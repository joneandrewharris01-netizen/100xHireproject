"""CLI entry: build today's LinkedIn 20.

Usage:
    python -m agents.outreach_os.linkedin_rotator
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from . import LINKEDIN_DAILY_CAP, icp_bump, opener, rotation, xlsx_loader

_XLSX = Path("linkedin-content/B2B AI Agents.xlsx")


def _generate_opener(lead: dict) -> str:
    return opener.generate(lead)


def _render(picks: list[dict]) -> str:
    parts = ["# LinkedIn queue\n"]
    for p in picks:
        parts.append(f"<!--LEAD\n{json.dumps(p)}\n-->\n")
        parts.append(f'- **{p.get("name")}** . {p.get("title")} @ {p.get("company")} . "{p.get("opener")}"\n')
    return "\n".join(parts)


def run(*, today: date | None = None, n: int = LINKEDIN_DAILY_CAP) -> Path:
    today = today or date.today()
    rows = xlsx_loader.load(_XLSX)
    if not rows:
        out = Path(f"agents/outreach_os/linkedin/{today.isoformat()}.md")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("# LinkedIn queue\n\n(No leads available.)\n", encoding="utf-8")
        return out

    bumped = icp_bump.bump(rows)
    picks = rotation.pick(bumped, n=n, today=today)

    enriched: list[dict] = []
    for lead in picks:
        try:
            opener_text = _generate_opener(lead)
        except Exception as e:
            opener_text = f"<ERROR: {e}>"
        enriched.append({**lead, "opener": opener_text})

    out = Path(f"agents/outreach_os/linkedin/{today.isoformat()}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_render(enriched), encoding="utf-8")
    return out


def _cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--n", type=int, default=LINKEDIN_DAILY_CAP)
    args = parser.parse_args()
    today = date.fromisoformat(args.date) if args.date else None
    print(run(today=today, n=args.n))


if __name__ == "__main__":
    _cli()
