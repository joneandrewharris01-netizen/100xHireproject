"""Groq SDK wrapper for the RevOps Intel standalone pipeline.

This is the single file that knows Groq exists. All other modules call
`complete(prompt)` and get voice-clean text or LLMError.
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq, APIStatusError, APIConnectionError, RateLimitError


_DOTENV_PATH = str(Path(__file__).parent / ".env")


class LLMError(Exception):
    """Raised for any unrecoverable LLM-side failure (auth, network, bad response)."""


GURU_REPLACEMENTS: dict[str, str] = {
    "game changer": "big shift",
    "game-changer": "big shift",
    "10x": "a lot more",
    "level up": "improve",
    "crushing it": "doing well",
    "move the needle": "matter",
    "deep dive": "look at",
    "low-hanging fruit": "quick win",
    "synergy": "",
}


def _load_api_key() -> str:
    """Load GROQ_API_KEY from environment or agents/revops_intel/.env."""
    load_dotenv(_DOTENV_PATH, override=False)
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise LLMError(
            "GROQ_API_KEY not set. Copy .env.example to .env and add your key "
            "from https://console.groq.com/keys"
        )
    return key


# Em-dash + en-dash. Heuristic: if next non-space char is uppercase OR end-of-string,
# replace with ". "; otherwise replace with ", ".
_EM_DASH_RE = re.compile(r"\s*[—–]\s*")

# Emoji + symbol blocks Llama 3.3 is known to emit.
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FFFF\U00002600-\U000027BF\U0001F3FB-\U0001F3FF‍]"
)

_TYPOGRAPHIC = [
    ("…", "..."),
    ("→", " to "),
    ("•", "-"),
    ("“", '"'),  # left double quote
    ("”", '"'),  # right double quote
    ("‘", "'"),  # left single quote
    ("’", "'"),  # right single quote
]

_CTA_TRAILERS = [
    r"\bDM me\b[^.!?]*[.!?]?\s*$",
    r"\bHit me up\b[^.!?]*[.!?]?\s*$",
    r"\bFeel free to reach out\b[^.!?]*[.!?]?\s*$",
    r"\bReach out anytime\b[^.!?]*[.!?]?\s*$",
    r"\bShoot me a message\b[^.!?]*[.!?]?\s*$",
]
_CTA_RE = re.compile("|".join(_CTA_TRAILERS), re.IGNORECASE)


def _replace_em_dash(match: re.Match) -> str:
    end = match.end()
    src = match.string
    nxt = ""
    i = end
    while i < len(src) and src[i].isspace():
        i += 1
    if i < len(src):
        nxt = src[i]
    if nxt == "" or nxt.isupper():
        return ". "
    return ", "


def _enforce_voice(text: str) -> tuple[str, list[dict]]:
    """Apply voice cleanup. Returns (cleaned_text, violations).

    violations is a list of {rule, before, after} dicts for logging.
    """
    violations: list[dict] = []

    new_text, n = _EM_DASH_RE.subn(_replace_em_dash, text)
    if n:
        violations.append({"rule": "em_dash", "before": text, "after": new_text})
    text = new_text

    new_text, n = _EMOJI_RE.subn("", text)
    if n:
        violations.append({"rule": "emoji", "before": text, "after": new_text})
    text = new_text

    for raw, replacement in _TYPOGRAPHIC:
        if raw in text:
            new_text = text.replace(raw, replacement)
            violations.append({"rule": "typographic", "before": text, "after": new_text})
            text = new_text

    new_text, n = _CTA_RE.subn("", text)
    if n:
        cleaned = new_text.rstrip()
        # After stripping a trailing CTA sentence, ensure terminal punctuation
        # remains so downstream truncation checks don't false-positive.
        if cleaned and cleaned[-1] not in ".!?":
            cleaned += "."
        violations.append({"rule": "cta_trailer", "before": text, "after": cleaned})
        text = cleaned

    for phrase, replacement in GURU_REPLACEMENTS.items():
        # Word boundaries prevent "10x" from mangling "210x growth" or "100x".
        pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
        new_text, n = pattern.subn(replacement, text)
        if n:
            violations.append({"rule": "guru", "before": text, "after": new_text})
            text = new_text

    # Collapse double-spaces created by substitutions
    text = re.sub(r"  +", " ", text).strip()
    return text, violations


# Retry sleeps: between 3 attempts, we wait 1s then 4s (5s total wait budget).
# Spec mentioned "(1s, 4s, 16s)" — that was the earlier 4-attempt design.
# We ship 3 attempts because Groq RPM is generous enough that a 3rd retry
# rarely helps; cleaner to give up and log to failed_leads.jsonl.
_BACKOFF_BASE = 1.0  # seconds. Tests patch this to 0.01.
_MAX_RETRIES = 3     # 429: 3 attempts total; 5xx: 2 attempts total
_VIOLATIONS_LOG = str(
    Path(__file__).parent / "logs" / "voice_violations.jsonl"
)
_CALLS_LOG = str(
    Path(__file__).parent / "logs" / "llm_calls.jsonl"
)


_CLIENT: Groq | None = None


def _get_client() -> Groq:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = Groq(api_key=_load_api_key())
    return _CLIENT


def _log_violations(violations: list[dict], lead_id: str | None) -> None:
    if not violations:
        return
    log_path = Path(_VIOLATIONS_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        for v in violations:
            entry = {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "lead_id": lead_id,
                **v,
            }
            f.write(json.dumps(entry) + "\n")


def _log_call(
    model: str, prompt_chars: int, output_chars: int,
    attempts: int, latency_ms: int,
) -> None:
    log_path = Path(_CALLS_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": model, "prompt_chars": prompt_chars,
        "output_chars": output_chars, "attempts": attempts,
        "latency_ms": latency_ms,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def complete(
    prompt: str,
    *,
    max_tokens: int = 800,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
    lead_id: str | None = None,
) -> str:
    """Single Groq call with retry, voice cleanup, and logging.

    Raises LLMError on unrecoverable failure (auth, 3x 429, 2x 5xx, network).
    Returns voice-clean text.
    """
    client = _get_client()
    attempts = 0
    last_exc: Exception | None = None
    started = time.time()

    while attempts < _MAX_RETRIES:
        attempts += 1
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if not resp.choices:
                raise LLMError("Groq returned response with empty choices list")
            raw = (resp.choices[0].message.content or "")
            cleaned, violations = _enforce_voice(raw)
            _log_violations(violations, lead_id)
            _log_call(
                model, len(prompt), len(cleaned),
                attempts, int((time.time() - started) * 1000),
            )
            return cleaned
        except RateLimitError as e:
            last_exc = e
            if attempts >= _MAX_RETRIES:
                break
            time.sleep(_BACKOFF_BASE * (4 ** (attempts - 1)))
        except APIStatusError as e:
            last_exc = e
            status = getattr(e, "status_code", 0)
            if 500 <= status < 600 and attempts < 2:
                time.sleep(_BACKOFF_BASE * 4)
                continue
            raise LLMError(f"Groq API status error {status}: {e}") from e
        except APIConnectionError as e:
            last_exc = e
            if attempts < 2:
                time.sleep(_BACKOFF_BASE * 4)
                continue
            raise LLMError(f"Groq connection error: {e}") from e

    raise LLMError(
        f"Groq rate limit not recoverable after {attempts} attempts: {last_exc}"
    ) from last_exc
