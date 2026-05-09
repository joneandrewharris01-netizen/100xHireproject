"""Scan agents/<pipeline>/queue/*.md for files generated today."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from . import frontmatter

_SOURCES = {
    "revops": Path("agents/revops_intel/queue"),
    "pe": Path("agents/pe_intel/queue"),
    "reddit_mine": Path("agents/reddit_mine/queue"),
    "vc_pain_analysis": Path("agents/vc_pain_analysis/queue"),
}


def _is_today(fm: dict, today: date) -> bool:
    raw = str(fm.get("generated_at", ""))
    return raw.startswith(today.isoformat())


def scan_today_all(today: date) -> list[dict]:
    out: list[dict] = []
    for source, qdir in _SOURCES.items():
        if not qdir.exists():
            continue
        for path in sorted(qdir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            fm, _body = frontmatter.parse(text)
            if not fm:
                continue
            if not _is_today(fm, today):
                continue
            # Filter SKIPPED queue files (they're audit trail, not action items).
            # status: SKIPPED is the explicit signal; some pipelines also use a
            # filename prefix convention (e.g. revops_intel/queue/*_SKIPPED_*.md).
            status = str(fm.get("status", "")).strip().upper()
            if status == "SKIPPED" or "_SKIPPED_" in path.name.upper():
                continue
            out.append({"source": source, "path": str(path), "frontmatter": fm})
    return out
