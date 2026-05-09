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


def _normalize(row: dict) -> dict:
    """Translate raw xlsx columns into the canonical keys opener.py expects.

    The B2B AI Agents.xlsx uses Phantombuster-style columns
    (author/firstName, author/name, author/profileUrl). Other lists may use
    plain Name / Title / Company. Map both shapes onto a common key set.
    """
    name = row.get("name") or row.get("author/name") or row.get("full_name") or ""
    first = row.get("first_name") or row.get("author/firstname") or row.get("author/firstName") or ""
    title = row.get("title") or row.get("author/headline") or row.get("headline") or ""
    company = row.get("company") or row.get("organization") or row.get("author/company") or ""
    url = row.get("linkedin_url") or row.get("author/profileurl") or row.get("author/profileUrl") or row.get("profile_url") or ""
    return {
        "name": name.strip(),
        "first_name": first.strip(),
        "title": title.strip(),
        "company": company.strip(),
        "profile_url": url.strip(),
    }


def _generate_opener(lead: dict) -> str:
    return opener.generate(_normalize(lead))


def _render(picks: list[dict]) -> str:
    parts = ["# LinkedIn queue\n"]
    for p in picks:
        parts.append(f"<!--LEAD\n{json.dumps(p)}\n-->\n")
        n = _normalize(p)
        title_company = " . ".join(filter(None, [n["title"], (f"@ {n['company']}" if n["company"] else "")]))
        parts.append(f'- **{n["name"] or n["first_name"]}** . {title_company or "(role unknown)"} . [profile]({n["profile_url"]}) . "{p.get("opener")}"\n')
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
