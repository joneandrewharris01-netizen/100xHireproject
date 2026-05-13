"""Comment + DM drafting for the standalone RevOps Intel pipeline.

Two LLM calls per lead. Output passes prompt-leak, truncation, and length
checks. Retries once on failure; second failure raises QualityFlag carrying
the last attempts so the caller can save a _FLAGGED_*.md queue file.
"""
from __future__ import annotations

from pathlib import Path

from agents.revops_intel import llm_client


_PROMPTS_DIR = Path(__file__).parent / "prompts"

COMMENT_MIN = 60
COMMENT_MAX = 250
DM_MIN = 60
DM_MAX = 180

_PROMPT_LEAK_MARKERS = ("HARD RULES", "AS AN AI", "As an AI", "{lead_title}",
                       "{lead_body}", "{comments_block}", "{kb_anchors}")


class QualityFlag(Exception):
    """Raised when generation fails quality checks twice in a row."""
    def __init__(self, comment: str, dm: str, reason: str):
        self.comment, self.dm, self.reason = comment, dm, reason
        super().__init__(reason)


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def _format_comments(comments: list[dict]) -> str:
    if not comments:
        return "(no comments)"
    return "\n".join(
        f"- u/{c.get('author', '?')} ({c.get('score', 0)} pts): {(c.get('body') or '').strip()[:400]}"
        for c in comments[:3]
    )


def _kb_anchors(lead: dict) -> str:
    cat = lead.get("problem_category", "")
    return f"(problem_category: {cat})" if cat else "(no anchors)"


def _offer_summary(pitch: dict) -> str:
    return f"{pitch.get('name', 'general automation')}. Ideal buyer: {pitch.get('ideal_buyer', '')[:200]}"


def _offer_proof(pitch: dict) -> str:
    points = pitch.get("proof_points_jone_can_use", [])
    return "\n".join(f"- {p}" for p in points[:6])


def _check_quality(text: str, min_words: int, max_words: int, kind: str) -> str | None:
    """Return None if OK, else a reason string."""
    stripped = text.strip()
    if any(marker in stripped for marker in _PROMPT_LEAK_MARKERS):
        return f"prompt_leak detected in {kind}"
    if not stripped:
        return f"{kind} is empty"
    if stripped[-1] not in ".!?":
        return f"{kind} appears truncated (no terminal punctuation)"
    n = len(stripped.split())
    if n < min_words or n > max_words:
        return f"{kind} length out of range ({n} words, want {min_words}-{max_words})"
    return None


def _generate_one(prompt: str, min_words: int, max_words: int, kind: str,
                  lead_id: str | None) -> tuple[str, str | None]:
    """Two attempts. Returns (text, last_reason). last_reason is None on success."""
    last_text = ""
    last_reason: str | None = None
    for attempt in (1, 2):
        active_prompt = prompt
        if attempt == 2:
            active_prompt += (
                f"\n\nPREVIOUS ATTEMPT FAILED: {last_reason}\n"
                "Try again. Stay strictly within length range. End with a complete sentence."
            )
        text = llm_client.complete(
            active_prompt, max_tokens=600, temperature=0.7, lead_id=lead_id,
        )
        last_text = text
        reason = _check_quality(text, min_words, max_words, kind)
        if reason is None:
            return text, None
        last_reason = reason
    return last_text, last_reason


def generate(lead: dict, top_comments: list[dict], offer_pitch: dict) -> tuple[str, str]:
    """Returns (reddit_comment, reddit_dm). Raises QualityFlag if checks fail twice."""
    lead_id = lead.get("post_id")
    common = {
        "subreddit": lead.get("subreddit", ""),
        "lead_title": lead.get("title", ""),
        "lead_body": (lead.get("selftext") or "")[:2000],
        "comments_block": _format_comments(top_comments),
        "kb_anchors": _kb_anchors(lead),
        "offer_summary": _offer_summary(offer_pitch),
        "offer_proof_points": _offer_proof(offer_pitch),
    }

    comment_prompt = _load_prompt("reddit_comment.txt").format(**common)
    comment, c_reason = _generate_one(
        comment_prompt, COMMENT_MIN, COMMENT_MAX, "comment", lead_id,
    )

    dm_prompt = _load_prompt("reddit_dm.txt").format(**common)
    dm, d_reason = _generate_one(
        dm_prompt, DM_MIN, DM_MAX, "dm", lead_id,
    )

    if c_reason or d_reason:
        raise QualityFlag(
            comment=comment, dm=dm,
            reason=f"comment: {c_reason or 'ok'} | dm: {d_reason or 'ok'}",
        )

    return comment, dm
