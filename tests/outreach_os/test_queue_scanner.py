import shutil
from datetime import date
from pathlib import Path

from agents.outreach_os import queue_scanner


def _seed_fixtures(repo: Path, fixtures: Path) -> None:
    mapping = {
        "revops_queue": "agents/revops_intel/queue",
        "pe_queue": "agents/pe_intel/queue",
        "reddit_mine_queue": "agents/reddit_mine/queue",
    }
    for src_name, dst in mapping.items():
        for p in (fixtures / src_name).iterdir():
            (repo / dst).mkdir(parents=True, exist_ok=True)
            shutil.copy(p, repo / dst / p.name)


def test_scan_returns_one_lead_per_queue_file(tmp_repo_root, fixtures_dir):
    _seed_fixtures(tmp_repo_root, fixtures_dir)
    leads = queue_scanner.scan_today_all(today=date(2026, 5, 9))
    assert len(leads) == 4
    sources = {l["source"] for l in leads}
    assert sources == {"revops", "pe", "reddit_mine"}


def test_scan_skips_files_not_generated_today(tmp_repo_root, fixtures_dir):
    _seed_fixtures(tmp_repo_root, fixtures_dir)
    leads = queue_scanner.scan_today_all(today=date(2026, 5, 10))
    assert leads == []


def test_scan_attaches_source_and_path(tmp_repo_root, fixtures_dir):
    _seed_fixtures(tmp_repo_root, fixtures_dir)
    leads = queue_scanner.scan_today_all(today=date(2026, 5, 9))
    one = leads[0]
    assert "source" in one
    assert "path" in one
    assert "frontmatter" in one


def test_scan_returns_empty_when_dirs_missing(tmp_repo_root):
    leads = queue_scanner.scan_today_all(today=date(2026, 5, 9))
    assert leads == []
