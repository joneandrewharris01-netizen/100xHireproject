import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agents.pe_intel import db, scrape


FIXTURE = Path(__file__).parent.parent / "fixtures" / "minimal_thread.json"


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    db.init_schema(c)
    yield c
    c.close()


@pytest.fixture
def mock_fetcher():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    post_data = raw[0]["data"]["children"][0]["data"]

    f = MagicMock()
    f.fetch_listing.return_value = {
        "data": {
            "children": [{"data": post_data}],
            "after": None,
        }
    }
    from agents.pe_intel import fetchers
    walked = list(fetchers.walk_comments(raw[1], post_id=post_data["id"]))
    f.fetch_post_with_comments.return_value = (post_data, walked)
    return f


def test_scrape_subreddit_inserts_post_and_comments(conn, mock_fetcher):
    scrape.scrape_subreddit(conn, "private_equity", mock_fetcher,
                             listings=[("new", None)])
    posts = conn.execute("SELECT post_id FROM posts").fetchall()
    comments = conn.execute("SELECT comment_id FROM comments").fetchall()
    assert len(posts) == 1
    assert len(comments) > 0


def test_scrape_subreddit_skips_recently_scraped(conn, mock_fetcher):
    scrape.scrape_subreddit(conn, "private_equity", mock_fetcher,
                             listings=[("new", None)])
    initial_calls = mock_fetcher.fetch_post_with_comments.call_count
    # Run again immediately
    scrape.scrape_subreddit(conn, "private_equity", mock_fetcher,
                             listings=[("new", None)])
    # Listing fetch happens again (always); but comments fetch should NOT
    assert mock_fetcher.fetch_post_with_comments.call_count == initial_calls
