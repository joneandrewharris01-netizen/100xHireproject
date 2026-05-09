"""Fetcher tests use the hand-crafted minimal fixture — no live network."""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agents.pe_intel import fetchers


FIXTURE = Path(__file__).parent.parent / "fixtures" / "minimal_thread.json"


@pytest.fixture
def fixture_bytes():
    return FIXTURE.read_bytes()


@pytest.fixture
def fixture_json():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_urllib_fetcher_get_returns_parsed_json(fixture_bytes):
    """fetch_listing should return whatever JSON the URL returns, parsed."""
    f = fetchers.UrllibFetcher(user_agent="pe-intel-test/1.0", sleep_s=0)
    fake_response = MagicMock()
    fake_response.read.return_value = fixture_bytes
    fake_response.__enter__ = lambda s: fake_response
    fake_response.__exit__ = lambda *a: None
    with patch("urllib.request.urlopen", return_value=fake_response):
        result = f.fetch_listing("private_equity", "new", limit=100)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["kind"] == "Listing"


def test_urllib_fetcher_fetch_post_with_comments_returns_post_and_walked(fixture_bytes):
    f = fetchers.UrllibFetcher(user_agent="pe-intel-test/1.0", sleep_s=0)
    fake_response = MagicMock()
    fake_response.read.return_value = fixture_bytes
    fake_response.__enter__ = lambda s: fake_response
    fake_response.__exit__ = lambda *a: None
    with patch("urllib.request.urlopen", return_value=fake_response):
        post, comments = f.fetch_post_with_comments("test001", "private_equity")
    assert post["id"] == "test001"
    assert post["title"] == "Building AI-first infra at our PE firm"
    # Walker should yield exactly 2 valid comments (c001, c002); skips c003/c004/c005
    assert len(comments) == 2
    ids = {c["comment_id"] for c in comments}
    assert "t1_c001" in ids
    assert "t1_c002" in ids


def test_walk_comments_yields_required_fields(fixture_json):
    comments = list(fetchers.walk_comments(fixture_json[1], post_id="test001"))
    assert len(comments) == 2
    for c in comments:
        assert c["comment_id"].startswith("t1_")
        assert c["post_id"] == "test001"
        assert "body" in c
        assert "depth" in c
        assert c["author"] not in (None, "[deleted]", "AutoModerator")
        assert len(c["body"]) >= 30


def test_walk_comments_records_depth_correctly(fixture_json):
    """Top-level comment depth=0; nested reply depth=1."""
    comments = list(fetchers.walk_comments(fixture_json[1], post_id="test001"))
    by_id = {c["comment_id"]: c for c in comments}
    assert by_id["t1_c001"]["depth"] == 0
    assert by_id["t1_c002"]["depth"] == 1


def test_walk_comments_skips_automod_deleted_and_short(fixture_json):
    """Must skip c003 (AutoMod), c004 (deleted), c005 (too short)."""
    comments = list(fetchers.walk_comments(fixture_json[1], post_id="test001"))
    ids = {c["comment_id"] for c in comments}
    for skipped in ["t1_c003", "t1_c004", "t1_c005"]:
        assert skipped not in ids
