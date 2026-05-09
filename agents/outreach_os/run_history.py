"""Read the last N days of Daily Brief frontmatter for the dashboard."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from . import frontmatter


def read(*, today: date, days: int = 7) -> list[dict]:
    out: list[dict] = []
    for i in range(days):
        d = today - timedelta(days=i)
        p = Path(f"outreach-os/daily/{d.isoformat()}.md")
        if not p.exists():
            continue
        fm, _ = frontmatter.parse(p.read_text(encoding="utf-8"))
        if not fm:
            continue
        out.append(fm)
    return out
