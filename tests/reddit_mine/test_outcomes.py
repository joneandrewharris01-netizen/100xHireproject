import json
from pathlib import Path

import pytest

from agents.reddit_mine import outcomes


def test_record_creates_file(tmp_repo_root):
    outcomes.record("post1", "responded")
    p = Path("agents/reddit_mine/outcomes.json")
    data = json.loads(p.read_text())
    assert data["post1"]["outcome"] == "responded"
    assert data["post1"]["outcome_logged_at"]


def test_record_initializes_posted_at_if_missing(tmp_repo_root):
    outcomes.record("post1", "responded")
    p = Path("agents/reddit_mine/outcomes.json")
    data = json.loads(p.read_text())
    assert data["post1"]["posted_at"] is not None


def test_record_idempotent_on_same_outcome(tmp_repo_root):
    outcomes.record("post1", "responded")
    p = Path("agents/reddit_mine/outcomes.json")
    first = json.loads(p.read_text())
    outcomes.record("post1", "responded")
    second = json.loads(p.read_text())
    assert first["post1"]["posted_at"] == second["post1"]["posted_at"]


def test_record_invalid_outcome_raises(tmp_repo_root):
    with pytest.raises(ValueError, match="invalid outcome"):
        outcomes.record("post1", "maybe")
