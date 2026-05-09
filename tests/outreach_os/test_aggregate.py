import shutil
from datetime import date
from pathlib import Path

from agents.outreach_os import aggregate, last_run


def _seed(repo, fixtures):
    mapping = {
        "revops_queue": "agents/revops_intel/queue",
        "pe_queue": "agents/pe_intel/queue",
        "reddit_mine_queue": "agents/reddit_mine/queue",
    }
    for src, dst in mapping.items():
        for p in (fixtures / src).iterdir():
            (repo / dst).mkdir(parents=True, exist_ok=True)
            shutil.copy(p, repo / dst / p.name)


def test_writes_brief_to_expected_path(tmp_repo_root, fixtures_dir):
    _seed(tmp_repo_root, fixtures_dir)
    out = aggregate.run(today=date(2026, 5, 9))
    assert out == Path("outreach-os/daily/2026-05-09.md")
    assert out.exists()


def test_brief_contains_all_4_leads(tmp_repo_root, fixtures_dir):
    _seed(tmp_repo_root, fixtures_dir)
    aggregate.run(today=date(2026, 5, 9))
    md = (tmp_repo_root / "outreach-os/daily/2026-05-09.md").read_text()
    for pid in ("post1", "post2", "post3", "post4"):
        assert pid in md


def test_pipelines_run_inferred_from_last_run_markers(tmp_repo_root, fixtures_dir):
    _seed(tmp_repo_root, fixtures_dir)
    last_run.write("revops", new_leads=2, errors=0)
    last_run.write("reddit_mine", new_leads=1, errors=0)
    aggregate.run(today=date(2026, 5, 9))
    md = (tmp_repo_root / "outreach-os/daily/2026-05-09.md").read_text()
    fm_block = md.split("---")[1]
    assert "revops" in fm_block
    assert "reddit_mine" in fm_block
