from datetime import date
from pathlib import Path

from agents.outreach_os import dashboard


def test_writes_dashboard_file(tmp_repo_root):
    out = dashboard.run(today=date(2026, 5, 9))
    assert out == Path("outreach-os/dashboard.md")
    assert out.exists()
    text = out.read_text()
    assert "Outreach OS - Dashboard" in text
    assert "30-day stats" in text
    assert "—" not in text  # voice rule
