"""CLI entry: flush outcomes ticked in today's Daily Brief."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import outcome_dispatcher, tickbox


def run(*, brief_path: Path | None = None) -> dict:
    brief_path = brief_path or Path(f"outreach-os/daily/{date.today().isoformat()}.md")
    if not brief_path.exists():
        return {"updated": 0, "unchanged": 0, "conflicts": 0}
    text = brief_path.read_text(encoding="utf-8")
    parsed = tickbox.parse(text)
    updated = 0
    conflicts = 0
    for entry in parsed:
        if entry.get("conflict"):
            conflicts += 1
            continue
        if outcome_dispatcher.dispatch(entry):
            updated += 1
    return {"updated": updated, "unchanged": 0, "conflicts": conflicts}


def _cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief")
    args = parser.parse_args()
    bp = Path(args.brief) if args.brief else None
    summary = run(brief_path=bp)
    print(f"updated: {summary['updated']}, conflicts: {summary['conflicts']}")


if __name__ == "__main__":
    _cli()
