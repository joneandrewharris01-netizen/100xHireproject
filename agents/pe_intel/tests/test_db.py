import sqlite3
from pathlib import Path

import pytest

from agents.pe_intel import db


@pytest.fixture
def conn(tmp_path):
    """Fresh in-memory-ish SQLite for each test."""
    db_path = tmp_path / "test.db"
    c = db.connect(db_path)
    db.init_schema(c)
    yield c
    c.close()


def test_init_schema_creates_all_tables(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = {r[0] for r in rows}
    expected = {
        "posts", "comments", "lead_scores", "processed_leads",
        "routing", "partners", "revenue_outcomes",
    }
    # sqlite_sequence may or may not exist depending on AUTOINCREMENT use
    table_names.discard("sqlite_sequence")
    assert table_names == expected


def test_init_schema_is_idempotent(conn):
    db.init_schema(conn)  # second call should not raise
    db.init_schema(conn)


import time


SAMPLE_POST = {
    "post_id": "1abcde",
    "subreddit": "privateequity",
    "author": "u_test",
    "title": "Sample post",
    "selftext": "Body text",
    "flair": None,
    "score": 5,
    "num_comments": 3,
    "created_utc": 1714000000,
    "permalink": "https://reddit.com/r/privateequity/comments/1abcde/sample/",
}


def test_upsert_post_metadata_inserts_new(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    rows = conn.execute("SELECT post_id, title FROM posts").fetchall()
    assert len(rows) == 1
    assert rows[0]["post_id"] == "1abcde"


def test_upsert_post_metadata_updates_existing(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    updated = dict(SAMPLE_POST, score=99, num_comments=50)
    db.upsert_post_metadata(conn, updated)
    rows = conn.execute("SELECT score, num_comments FROM posts").fetchall()
    assert len(rows) == 1
    assert rows[0]["score"] == 99
    assert rows[0]["num_comments"] == 50


def test_upsert_post_metadata_does_not_bump_last_updated(conn):
    """CRITICAL: metadata-only upsert preserves prior last_updated value.
    Otherwise the re-scrape policy is broken — every metadata refresh would
    look like a fresh comments scrape."""
    db.upsert_post_metadata(conn, SAMPLE_POST)
    long_ago = int(time.time()) - 60 * 60 * 30
    conn.execute(
        "UPDATE posts SET last_updated = ? WHERE post_id = ?",
        (long_ago, "1abcde"),
    )
    conn.commit()
    db.upsert_post_metadata(conn, dict(SAMPLE_POST, score=99))
    row = conn.execute(
        "SELECT last_updated FROM posts WHERE post_id = ?", ("1abcde",)
    ).fetchone()
    assert row["last_updated"] == long_ago


def test_mark_post_rescraped_bumps_last_updated(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    long_ago = int(time.time()) - 60 * 60 * 30
    conn.execute(
        "UPDATE posts SET last_updated = ? WHERE post_id = ?",
        (long_ago, "1abcde"),
    )
    conn.commit()
    db.mark_post_rescraped(conn, "1abcde")
    row = conn.execute(
        "SELECT last_updated FROM posts WHERE post_id = ?", ("1abcde",)
    ).fetchone()
    assert row["last_updated"] > long_ago


def test_post_needs_rescrape_new_post(conn):
    assert db.post_needs_rescrape(conn, "neverseen") is True


def test_post_needs_rescrape_recent_active_post(conn):
    """Post <7d old, last comments-scraped >24h ago → needs rescrape."""
    db.upsert_post_metadata(conn, SAMPLE_POST)
    long_ago = int(time.time()) - 60 * 60 * 30
    conn.execute(
        "UPDATE posts SET created_utc = ?, last_updated = ? WHERE post_id = ?",
        (int(time.time()) - 86400 * 3, long_ago, "1abcde"),
    )
    conn.commit()
    assert db.post_needs_rescrape(conn, "1abcde") is True


def test_post_needs_rescrape_recent_active_post_just_scraped(conn):
    """Post <7d old, last comments-scraped <24h ago → skip."""
    db.upsert_post_metadata(conn, SAMPLE_POST)
    just_now = int(time.time()) - 60 * 60
    conn.execute(
        "UPDATE posts SET created_utc = ?, last_updated = ? WHERE post_id = ?",
        (int(time.time()) - 86400 * 3, just_now, "1abcde"),
    )
    conn.commit()
    assert db.post_needs_rescrape(conn, "1abcde") is False


def test_post_needs_rescrape_old_post_frozen(conn):
    """Post >30d old → never rescrape."""
    db.upsert_post_metadata(conn, SAMPLE_POST)
    old = int(time.time()) - 86400 * 45
    conn.execute(
        "UPDATE posts SET created_utc = ?, last_updated = ? WHERE post_id = ?",
        (old, old, "1abcde"),
    )
    conn.commit()
    assert db.post_needs_rescrape(conn, "1abcde") is False


SAMPLE_COMMENT = {
    "comment_id": "c_aaa",
    "post_id": "1abcde",
    "parent_id": "t3_1abcde",
    "author": "u_alice",
    "body": "This is a real comment, definitely longer than thirty characters.",
    "score": 4,
    "depth": 0,
    "created_utc": 1714000100,
}


def test_insert_comment(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.insert_comment(conn, SAMPLE_COMMENT)
    rows = conn.execute("SELECT body FROM comments WHERE comment_id = 'c_aaa'").fetchall()
    assert len(rows) == 1
    assert "real comment" in rows[0]["body"]


def test_insert_comment_idempotent(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.insert_comment(conn, SAMPLE_COMMENT)
    db.insert_comment(conn, SAMPLE_COMMENT)  # second call no-op
    count = conn.execute("SELECT COUNT(*) AS n FROM comments").fetchone()["n"]
    assert count == 1


def test_upsert_lead_score_and_hot_query(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.upsert_lead_score(conn, "1abcde", score=85, reasons=["pain_point", "automation_relevant"])
    hot = db.fetch_hot_unprocessed(conn)
    assert len(hot) == 1
    assert hot[0]["post_id"] == "1abcde"
    assert hot[0]["score"] == 85


def test_fetch_hot_returns_url_alias_and_deserialized_reasons(conn):
    """Slash command consumes hot leads as queue-file frontmatter — verify field shape."""
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.upsert_lead_score(conn, "1abcde", score=85,
                          reasons=["pain_point", "automation_relevant"])
    hot = db.fetch_hot_unprocessed(conn)
    row = hot[0]
    # permalink aliased to url
    assert "url" in row
    assert "permalink" not in row
    assert row["url"].startswith("https://reddit.com/")
    # reasons is a list, not a JSON string
    assert isinstance(row["reasons"], list)
    assert row["reasons"] == ["pain_point", "automation_relevant"]
    assert "score_reasons" not in row


def test_upsert_lead_score_excludes_processed(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.upsert_lead_score(conn, "1abcde", score=85, reasons=["pain_point"])
    db.mark_processed(conn, "1abcde", "queue/2026-04-28_test.md")
    hot = db.fetch_hot_unprocessed(conn)
    assert hot == []


def test_upsert_lead_score_excludes_cold(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.upsert_lead_score(conn, "1abcde", score=40, reasons=["pain_point"])
    hot = db.fetch_hot_unprocessed(conn)
    assert hot == []
