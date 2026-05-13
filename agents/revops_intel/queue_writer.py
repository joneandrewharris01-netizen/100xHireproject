"""Write queue files in the format /revops-process produces."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


_QUEUE_DIR = Path(__file__).parent / "queue"


def _blockquote(text: str) -> str:
    """Prepend '> ' to every line so multi-line LLM output renders as a single
    Markdown blockquote instead of breaking out of the section after the first
    newline."""
    if not text:
        return "> "
    return "\n".join(f"> {line}" if line else ">" for line in text.split("\n"))


def _sanitize(author: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", author or "anon")[:32]


def _kb_summary(kb_diff: dict) -> str:
    lines = []
    for tool in (kb_diff.get("tools") or {}):
        lines.append(f"- Added tool: \"{tool}\"")
    for pain in (kb_diff.get("pains") or {}):
        lines.append(f"- Added pain: \"{pain}\"")
    for persona in (kb_diff.get("personas") or {}):
        lines.append(f"- Updated persona: \"{persona}\"")
    for term in (kb_diff.get("jargon") or {}):
        lines.append(f"- Added jargon: \"{term}\"")
    return "\n".join(lines) if lines else "- (no KB updates this lead)"


def _format_comments_section(comments: list[dict]) -> str:
    if not comments:
        return "- (no top comments)"
    out = []
    for c in comments[:5]:
        snippet = (c.get("body") or "").strip().replace("\n", " ")[:300]
        out.append(f'- u/{c.get("author","?")} ({c.get("score",0)} upvotes): "{snippet}"')
    return "\n".join(out)


def write(lead: dict, comments: list[dict], comment_text: str, dm_text: str,
          kb_diff: dict, *, flagged: bool) -> str:
    _QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    author = _sanitize(lead.get("author", ""))
    prefix = "_FLAGGED_" if flagged else ""
    name = f"{date}_{prefix}{author}_{lead['post_id']}.md"
    path = _QUEUE_DIR / name

    body = f"""---
post_id: {lead['post_id']}
author: u/{lead.get('author', '')}
subreddit: {lead.get('subreddit', '')}
url: {lead.get('url', '')}
score: {lead.get('score', 0)}
reasons: {json.dumps(lead.get('reasons', []))}
problem_category: {lead.get('problem_category', '')}
firm_size_signal: {lead.get('firm_size_signal', '')}
offer_match: {lead.get('offer_match', '')}
generated_at: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
{"flagged: true" if flagged else "flagged: false"}
---

## Original post
**{lead.get('title', '')}**
{_blockquote((lead.get('selftext') or '').strip())}

## Why this lead is hot
- Score {lead.get('score', 0)} on revops_intel scorer
- Reasons: {", ".join(lead.get('reasons', []))}

## Top relevant comments (insider context)
{_format_comments_section(comments)}

## Suggested REDDIT COMMENT
{_blockquote(comment_text)}

## Suggested REDDIT DM
{_blockquote(dm_text)}

## Knowledge updates from this thread
{_kb_summary(kb_diff)}
"""
    path.write_text(body, encoding="utf-8")
    return str(path)
