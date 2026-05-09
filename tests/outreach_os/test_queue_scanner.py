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


def test_scan_skips_files_with_status_skipped(tmp_repo_root, fixtures_dir):
    _seed_fixtures(tmp_repo_root, fixtures_dir)
    skip_path = tmp_repo_root / "agents/revops_intel/queue/2026-05-09_SKIPPED_jobseeker.md"
    skip_path.write_text(
        "---\n"
        "post_id: skip1\n"
        "author: u/seeker\n"
        "subreddit: sales\n"
        "score: 75\n"
        "generated_at: 2026-05-09T07:00:00\n"
        "status: SKIPPED\n"
        "skip_reason: not a buyer\n"
        "---\nbody"
    )
    leads = queue_scanner.scan_today_all(today=date(2026, 5, 9))
    ids = {l["frontmatter"].get("post_id") for l in leads}
    assert "skip1" not in ids


def test_scan_skips_files_with_skipped_in_filename(tmp_repo_root, fixtures_dir):
    _seed_fixtures(tmp_repo_root, fixtures_dir)
    # Filename convention: ..._SKIPPED_*.md (legacy queue pattern, no frontmatter status)
    skip_path = tmp_repo_root / "agents/revops_intel/queue/2026-05-09_SKIPPED_legacy.md"
    skip_path.write_text(
        "---\n"
        "post_id: legacy_skip\n"
        "author: u/whatever\n"
        "subreddit: sales\n"
        "score: 75\n"
        "generated_at: 2026-05-09T07:00:00\n"
        "---\nbody"
    )
    leads = queue_scanner.scan_today_all(today=date(2026, 5, 9))
    ids = {l["frontmatter"].get("post_id") for l in leads}
    assert "legacy_skip" not in ids
