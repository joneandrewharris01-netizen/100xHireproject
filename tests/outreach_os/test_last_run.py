"""last_run marker read/write."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agents.outreach_os import last_run


def test_marker_path(tmp_repo_root: Path):
    assert last_run.marker_path("revops") == Path("agents/revops_intel/last_run.json")
    assert last_run.marker_path("pe") == Path("agents/pe_intel/last_run.json")
    assert last_run.marker_path("reddit_mine") == Path("agents/reddit_mine/last_run.json")


def test_unknown_pipeline_raises():
    with pytest.raises(ValueError, match="unknown pipeline"):
        last_run.marker_path("twitter")


def test_write_then_read(tmp_repo_root: Path):
    last_run.write("revops", new_leads=4, errors=0)
    data = last_run.read("revops")
    assert data["date"] == date.today().isoformat()
    assert data["new_leads"] == 4
    assert data["errors"] == 0
    assert "finished_at" in data


def test_read_missing_returns_none(tmp_repo_root: Path):
    assert last_run.read("revops") is None


def test_ran_today_true_when_marker_is_today(tmp_repo_root: Path):
    last_run.write("pe", new_leads=0, errors=0)
    assert last_run.ran_today("pe") is True


def test_ran_today_false_when_no_marker(tmp_repo_root: Path):
    assert last_run.ran_today("pe") is False


def test_ran_today_false_when_marker_is_old(tmp_repo_root: Path):
    marker = last_run.marker_path("revops")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"date": "2020-01-01", "finished_at": "2020-01-01T00:00:00", "new_leads": 0, "errors": 0}')
    assert last_run.ran_today("revops") is False
