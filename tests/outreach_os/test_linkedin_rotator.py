import shutil
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from agents.outreach_os import linkedin_rotator


def _seed_xlsx(repo: Path, fixtures: Path) -> None:
    dst = repo / "linkedin-content/B2B AI Agents.xlsx"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixtures / "b2b_leads_10.xlsx", dst)


def test_writes_md_with_n_leads(tmp_repo_root, fixtures_dir, monkeypatch):
    _seed_xlsx(tmp_repo_root, fixtures_dir)
    fake_open = MagicMock(side_effect=lambda lead: f"opener-for-{lead['name']}")
    monkeypatch.setattr(linkedin_rotator, "_generate_opener", fake_open)

    out = linkedin_rotator.run(today=date(2026, 5, 9), n=5)

    assert out == Path(f"agents/outreach_os/linkedin/2026-05-09.md")
    assert out.exists()
    text = out.read_text()
    assert text.count("<!--LEAD") == 5


def test_failed_opener_does_not_block_others(tmp_repo_root, fixtures_dir, monkeypatch):
    _seed_xlsx(tmp_repo_root, fixtures_dir)
    counter = {"n": 0}

    def flaky(lead):
        counter["n"] += 1
        if counter["n"] == 2:
            raise RuntimeError("boom")
        return "ok"

    monkeypatch.setattr(linkedin_rotator, "_generate_opener", flaky)
    out = linkedin_rotator.run(today=date(2026, 5, 9), n=5)
    text = out.read_text()
    assert text.count("<!--LEAD") == 5
    assert "<ERROR" in text
