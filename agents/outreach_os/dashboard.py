"""CLI entry: refresh the dashboard.

Usage:
    python -m agents.outreach_os.dashboard
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from . import outcome_counts, pending_outcomes, run_history, verdicts, win_rate

SOURCES = ("revops", "pe", "reddit_mine", "linkedin")


def _table_row(source: str, c: dict[str, int], rate: float | None) -> str:
    rate_str = f"{rate * 100:.1f}%" if rate is not None else "N/A"
    return (
        f"| {source:<8} | {c['sent']:>4} | {c['responded']:>9} | "
        f"{c['dmd_back']:>9} | {c['client']:>6} | {rate_str:>8} |"
    )


def _stats_table(today: date) -> tuple[str, dict[str, float | None]]:
    rows = ["| Source   | Sent | Responded | DM'd back | Booked | Win rate |",
            "|----------|------|-----------|-----------|--------|----------|"]
    rates: dict[str, float | None] = {}
    totals = {"sent": 0, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 0, "unsubscribed": 0}
    for source in ("revops", "pe", "reddit_mine"):
        c = outcome_counts.count(source, window_days=30)
        for k in totals:
            totals[k] += c[k]
        rates[source] = win_rate.compute(c)
        rows.append(_table_row(source, c, rates[source]))
    linkedin_zero = {"sent": 0, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 0, "unsubscribed": 0}
    rates["linkedin"] = None
    rows.append(_table_row("linkedin", linkedin_zero, None))
    rows.append(_table_row("Total", totals, win_rate.compute(totals)))
    return "\n".join(rows), rates


def _history_table(today: date) -> str:
    rows = ["| Date | Pipelines run | New leads | Outcomes logged |",
            "|------|---------------|-----------|-----------------|"]
    for fm in run_history.read(today=today, days=7):
        d = fm.get("date", "")
        prun = fm.get("pipelines_run", [])
        total = (fm.get("totals") or {}).get("total", 0)
        rows.append(f"| {d} | {prun} | {total} | (n/a in MVP) |")
    return "\n".join(rows)


def run(*, today: date | None = None) -> Path:
    today = today or date.today()
    stats_md, rates = _stats_table(today)
    pending = pending_outcomes.fetch_all(stale_days=7)
    pending_md = "\n".join(f"- `{p['post_id']}` ({p['source']}) posted {p['posted_at']}" for p in pending) or "(none)"
    v = verdicts.generate(rates)
    history_md = _history_table(today)

    md = (
        "---\n"
        f"last_updated: {datetime.now().isoformat(timespec='seconds')}\n"
        "---\n\n"
        "# Outreach OS - Dashboard\n\n"
        "## 30-day stats\n"
        f"{stats_md}\n\n"
        f"## Outcomes pending >7 days ({len(pending)} leads)\n"
        f"{pending_md}\n\n"
        "## What's working\n"
        + "".join(f"- {line}\n" for line in v["working"])
        + "\n## What's not\n"
        + "".join(f"- {line}\n" for line in v["not_working"])
        + "\n## Last 7 days run history\n"
        f"{history_md}\n"
    )

    out = Path("outreach-os/dashboard.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    return out


def _cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args()
    today = date.fromisoformat(args.date) if args.date else None
    print(run(today=today))


if __name__ == "__main__":
    _cli()
