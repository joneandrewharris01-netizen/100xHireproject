"""CLI entry: build today's Daily Brief.

Usage:
    python -m agents.outreach_os.aggregate
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import PIPELINES, brief as brief_mod
from . import last_run, pending_outcomes, queue_scanner


def _read_linkedin(today: date) -> list[dict]:
    p = Path(f"agents/outreach_os/linkedin/{today.isoformat()}.md")
    if not p.exists():
        return []
    import json as _json
    import re
    items: list[dict] = []
    for m in re.finditer(r"<!--LEAD\n(.*?)\n-->", p.read_text(encoding="utf-8"), re.DOTALL):
        item = _json.loads(m.group(1))
        # Normalize Phantombuster-style keys so brief renderer can use plain `name`.
        if "name" not in item:
            item["name"] = item.get("author/name") or item.get("author/firstname") or ""
        items.append(item)
    return items


def _infer_pipeline_status() -> tuple[list[str], list[str]]:
    """Return (pipelines_run_today, pipelines_not_run_today) based on last_run markers."""
    run_today: list[str] = []
    not_run: list[str] = []
    for p in PIPELINES:
        if last_run.ran_today(p):
            run_today.append(p)
        else:
            not_run.append(p)
    return run_today, not_run


def run(*, today: date | None = None) -> Path:
    today = today or date.today()
    leads = queue_scanner.scan_today_all(today=today)
    linkedin = _read_linkedin(today)
    pending = pending_outcomes.fetch_all(stale_days=7)
    pipelines_run, pipelines_not_run = _infer_pipeline_status()
    if Path(f"agents/outreach_os/linkedin/{today.isoformat()}.md").exists():
        pipelines_run.append("linkedin")

    md = brief_mod.render(
        today=today,
        leads=leads,
        linkedin=linkedin,
        pending=pending,
        pipelines_run=pipelines_run,
        pipelines_skipped=[],
        pipelines_failed=pipelines_not_run,
    )

    out = Path(f"outreach-os/daily/{today.isoformat()}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    return out


def _cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="ISO date (default: today)")
    args = parser.parse_args()
    today = date.fromisoformat(args.date) if args.date else None
    out = run(today=today)
    print(out)


if __name__ == "__main__":
    _cli()
