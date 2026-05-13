"""KB extraction step for the standalone RevOps Intel pipeline.

Given a hot lead + its top comments, returns a KB diff dict with up to
4 top-level keys (tools, pains, personas, jargon). Caller is responsible
for merging into the real KB JSON files atomically.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from agents.revops_intel import llm_client


_PROMPTS_DIR = Path(__file__).parent / "prompts"
_FAILED_LOG = str(Path(__file__).parent / "logs" / "failed_leads.jsonl")
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _load_prompt() -> str:
    return (_PROMPTS_DIR / "kb_extract.txt").read_text(encoding="utf-8")


def _format_comments(comments: list[dict]) -> str:
    if not comments:
        return "(no comments)"
    lines = []
    for c in comments[:5]:
        body = c.get("body", "").strip().replace("\n", " ")
        lines.append(f"- u/{c.get('author', '?')} ({c.get('score', 0)} pts): {body[:500]}")
    return "\n".join(lines)


def _log_failure(lead_id: str, kind: str, detail: str) -> None:
    log_path = Path(_FAILED_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lead_id": lead_id, "stage": "extract", "kind": kind, "detail": detail[:500],
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _try_parse(raw: str) -> dict | None:
    stripped = _THINK_RE.sub("", raw).strip()
    # Strip markdown fences if model wrapped JSON in them
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```\s*$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def extract(lead: dict, top_comments: list[dict]) -> dict:
    """Run KB extraction on a hot lead. Returns parsed diff dict or {} on failure."""
    template = _load_prompt()
    prompt = template.format(
        lead_title=lead.get("title", ""),
        lead_body=lead.get("selftext", "")[:3000],
        comments_block=_format_comments(top_comments),
    )

    raw = llm_client.complete(
        prompt, max_tokens=1500, temperature=0.2,
        lead_id=lead.get("post_id"),
    )
    parsed = _try_parse(raw)
    if parsed is not None:
        return parsed

    # Retry once with stricter instruction appended
    strict_prompt = prompt + "\n\nRETURN ONLY VALID JSON. NO PROSE. NO MARKDOWN."
    raw2 = llm_client.complete(
        strict_prompt, max_tokens=1500, temperature=0.1,
        lead_id=lead.get("post_id"),
    )
    parsed = _try_parse(raw2)
    if parsed is not None:
        return parsed

    _log_failure(lead.get("post_id", "?"), "json_parse",
                 f"raw1={raw[:200]} raw2={raw2[:200]}")
    return {}
