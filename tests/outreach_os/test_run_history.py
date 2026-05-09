from datetime import date, timedelta
from pathlib import Path

from agents.outreach_os import run_history


def _write_brief(repo: Path, on_date: date, totals_total: int, pipelines_run: list[str]) -> None:
    p = repo / f"outreach-os/daily/{on_date.isoformat()}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\n"
        f"date: {on_date.isoformat()}\n"
        f"generated_at: {on_date.isoformat()}T07:30:00\n"
        f"totals: {{hot: 0, warm: 0, authority: 0, linkedin: 0, total: {totals_total}}}\n"
        f"pipelines_run: {pipelines_run}\n"
        f"pipelines_skipped: []\n"
        f"pipelines_failed: []\n"
        f"---\nbody"
    )


def test_returns_last_n_days(tmp_repo_root):
    today = date(2026, 5, 9)
    for i in range(8):
        _write_brief(tmp_repo_root, today - timedelta(days=i), i, ["revops"])
    history = run_history.read(today=today, days=7)
    assert len(history) == 7
    # PyYAML parses ISO dates as date objects, not strings
    assert str(history[0]["date"]) == today.isoformat()


def test_handles_missing_days(tmp_repo_root):
    today = date(2026, 5, 9)
    _write_brief(tmp_repo_root, today, 5, ["revops"])
    history = run_history.read(today=today, days=7)
    assert len(history) == 1
