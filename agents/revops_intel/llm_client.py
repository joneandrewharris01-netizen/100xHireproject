"""Groq SDK wrapper for the RevOps Intel standalone pipeline.

This is the single file that knows Groq exists. All other modules call
`complete(prompt)` and get voice-clean text or LLMError.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


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


import re


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
