"""Tests for db.fetch_top_comments helper.

We construct a fresh in-memory SQLite DB with the real schema, insert a
post and three comments with varying scores, then verify the helper returns
them in descending score order, limited to N.
"""
from __future__ import annotations

import time

import pytest

from agents.revops_intel import db


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    db.init_schema(c)
    yield c
    c.close()


def _insert_post(conn, post_id: str = "abc"):
    db.upsert_post_metadata(
        conn,
        {
            "post_id": post_id,
            "subreddit": "sales",
            "author": "u1",
            "title": "test",
            "selftext": "",
            "flair": None,
            "score": 1,
            "num_comments": 0,
            "created_utc": int(time.time()),
            "permalink": "/r/sales/test",
        },
    )


def test_fetch_top_comments_orders_by_score_desc(conn):
    _insert_post(conn)
    now = int(time.time())
    for cid, score in [("c1", 5), ("c2", 50), ("c3", 12)]:
        db.insert_comment(
            conn,
            {
                "comment_id": cid,
                "post_id": "abc",
                "parent_id": None,
                "author": f"u_{cid}",
                "body": f"body {cid}",
                "score": score,
                "depth": 0,
                "created_utc": now,
            },
        )

    rows = db.fetch_top_comments(conn, "abc", limit=10)

    assert [r["author"] for r in rows] == ["u_c2", "u_c3", "u_c1"]
    assert [r["score"] for r in rows] == [50, 12, 5]
    assert all({"author", "body", "score", "depth"} <= set(r) for r in rows)


def test_fetch_top_comments_respects_limit(conn):
    _insert_post(conn)
    now = int(time.time())
    for i in range(15):
        db.insert_comment(
            conn,
            {
                "comment_id": f"c{i}",
                "post_id": "abc",
                "parent_id": None,
                "author": f"u{i}",
                "body": "b",
                "score": i,
                "depth": 0,
                "created_utc": now,
            },
        )

    rows = db.fetch_top_comments(conn, "abc", limit=5)
    assert len(rows) == 5
    assert [r["score"] for r in rows] == [14, 13, 12, 11, 10]


def test_fetch_top_comments_returns_empty_when_no_comments(conn):
    _insert_post(conn)
    rows = db.fetch_top_comments(conn, "abc", limit=10)
    assert rows == []
