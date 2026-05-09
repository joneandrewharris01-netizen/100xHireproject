import shutil
from datetime import date
from pathlib import Path

import pytest

from agents.outreach_os import aggregate, dashboard, linkedin_rotator


def _seed(repo: Path, fixtures: Path) -> None:
    mapping = {
        "revops_queue": "agents/revops_intel/queue",
        "pe_queue": "agents/pe_intel/queue",
        "reddit_mine_queue": "agents/reddit_mine/queue",
    }
    for src, dst in mapping.items():
        for p in (fixtures / src).iterdir():
            (repo / dst).mkdir(parents=True, exist_ok=True)
            shutil.copy(p, repo / dst / p.name)
    shutil.copy(fixtures / "b2b_leads_10.xlsx", repo / "linkedin-content/B2B AI Agents.xlsx")


@pytest.mark.smoke
def test_full_run_writes_brief_and_dashboard(tmp_repo_root, fixtures_dir, monkeypatch):
    _seed(tmp_repo_root, fixtures_dir)
    monkeypatch.setattr(linkedin_rotator, "_generate_opener", lambda lead: f"opener-for-{lead['name']}")

    linkedin_rotator.run(today=date(2026, 5, 9), n=5)
    aggregate.run(today=date(2026, 5, 9))
    dashboard.run(today=date(2026, 5, 9))

    brief = Path("outreach-os/daily/2026-05-09.md")
    dash = Path("outreach-os/dashboard.md")
    assert brief.exists()
    assert dash.exists()
    bt = brief.read_text()
    for pid in ("post1", "post2", "post3", "post4"):
        assert pid in bt
    assert "Sarah Chen" in bt or "VP RevOps" in bt
    assert "—" not in bt
    assert "—" not in dash.read_text()
