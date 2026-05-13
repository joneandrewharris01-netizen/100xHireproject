"""SQLite layer for RevOps Intel agent.

All DB I/O lives here. No other module opens revops_intel.db directly.
Mirrors agents/pe_intel/db.py — same schema, separate database file so the
two niches can't cross-contaminate KB/queue/processed_leads.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).parent / "revops_intel.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    post_id        TEXT PRIMARY KEY,
    subreddit      TEXT NOT NULL,
    author         TEXT,
    title          TEXT NOT NULL,
    selftext       TEXT,
    flair          TEXT,
    score          INTEGER,
    num_comments   INTEGER,
    created_utc    INTEGER NOT NULL,
    permalink      TEXT NOT NULL,
    scraped_at     INTEGER NOT NULL,
    last_updated   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_posts_created   ON posts(created_utc);
CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);

CREATE TABLE IF NOT EXISTS comments (
    comment_id   TEXT PRIMARY KEY,
    post_id      TEXT NOT NULL REFERENCES posts(post_id),
    parent_id    TEXT,
    author       TEXT,
    body         TEXT NOT NULL,
    score        INTEGER,
    depth        INTEGER NOT NULL,
    created_utc  INTEGER NOT NULL,
    scraped_at   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_comments_post   ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_author ON comments(author);

CREATE TABLE IF NOT EXISTS lead_scores (
    post_id       TEXT PRIMARY KEY REFERENCES posts(post_id),
    score         INTEGER NOT NULL,
    score_reasons TEXT NOT NULL,
    is_hot        INTEGER NOT NULL,
    scored_at     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scores_hot ON lead_scores(is_hot, score DESC);

CREATE TABLE IF NOT EXISTS processed_leads (
    post_id      TEXT PRIMARY KEY REFERENCES posts(post_id),
    queue_file   TEXT NOT NULL,
    processed_at INTEGER NOT NULL,
    posted_at    INTEGER,
    outcome      TEXT,
    offer_match  TEXT
);

CREATE TABLE IF NOT EXISTS routing (
    post_id            TEXT PRIMARY KEY REFERENCES posts(post_id),
    problem_category   TEXT NOT NULL,
    firm_size_signal   TEXT NOT NULL,
    fit_for_jone       TEXT NOT NULL,
    offer_match        TEXT NOT NULL,
    tier               TEXT NOT NULL,
    expected_value_usd INTEGER NOT NULL,
    routed_at          INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_routing_tier ON routing(tier, expected_value_usd DESC);
CREATE INDEX IF NOT EXISTS idx_routing_offer ON routing(offer_match);
"""


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


import time as _time
import json as _json

HOT_THRESHOLD = 70


def upsert_post_metadata(conn: sqlite3.Connection, post: dict) -> None:
    """Insert or refresh listing-level fields. Does NOT touch last_updated.

    last_updated is reserved for "last successful comment-tree fetch" so the
    re-scrape policy works correctly. On INSERT, last_updated starts at 0.
    """
    now = int(_time.time())
    conn.execute(
        """
        INSERT INTO posts (
            post_id, subreddit, author, title, selftext, flair,
            score, num_comments, created_utc, permalink,
            scraped_at, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ON CONFLICT(post_id) DO UPDATE SET
            score = excluded.score,
            num_comments = excluded.num_comments,
            selftext = excluded.selftext,
            scraped_at = excluded.scraped_at
        """,
        (
            post["post_id"], post["subreddit"], post.get("author"),
            post["title"], post.get("selftext"), post.get("flair"),
            post.get("score", 0), post.get("num_comments", 0),
            post["created_utc"], post["permalink"],
            now,
        ),
    )
    conn.commit()


def mark_post_rescraped(conn: sqlite3.Connection, post_id: str) -> None:
    """Call AFTER a successful comment-tree fetch. Bumps last_updated."""
    now = int(_time.time())
    conn.execute(
        "UPDATE posts SET last_updated = ? WHERE post_id = ?",
        (now, post_id),
    )
    conn.commit()


def post_needs_rescrape(conn: sqlite3.Connection, post_id: str) -> bool:
    """Re-scrape policy:
    - Never seen / never fetched comments → True
    - Post <7 days old → re-fetch comments daily
    - Post 7-30 days old → re-fetch comments weekly
    - Post >30 days old → frozen
    """
    row = conn.execute(
        "SELECT created_utc, last_updated FROM posts WHERE post_id = ?",
        (post_id,),
    ).fetchone()
    if row is None or row["last_updated"] == 0:
        return True
    now = int(_time.time())
    age_days = (now - row["created_utc"]) / 86400
    since_update_h = (now - row["last_updated"]) / 3600
    if age_days > 30:
        return False
    if age_days < 7:
        return since_update_h >= 24
    return since_update_h >= 24 * 7


def insert_comment(conn: sqlite3.Connection, c: dict) -> None:
    now = int(_time.time())
    conn.execute(
        """
        INSERT OR IGNORE INTO comments (
            comment_id, post_id, parent_id, author, body, score,
            depth, created_utc, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            c["comment_id"], c["post_id"], c.get("parent_id"),
            c.get("author"), c["body"], c.get("score", 0),
            c["depth"], c["created_utc"], now,
        ),
    )
    conn.commit()


def upsert_lead_score(
    conn: sqlite3.Connection, post_id: str, score: int, reasons: list[str]
) -> None:
    now = int(_time.time())
    is_hot = 1 if score >= HOT_THRESHOLD else 0
    conn.execute(
        """
        INSERT INTO lead_scores (post_id, score, score_reasons, is_hot, scored_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            score = excluded.score,
            score_reasons = excluded.score_reasons,
            is_hot = excluded.is_hot,
            scored_at = excluded.scored_at
        """,
        (post_id, score, _json.dumps(reasons), is_hot, now),
    )
    conn.commit()


def fetch_hot_unprocessed(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        """
        SELECT p.post_id, p.subreddit, p.author, p.title, p.selftext,
               p.score AS reddit_score, p.num_comments,
               p.permalink AS url,
               p.created_utc,
               s.score, s.score_reasons,
               r.problem_category, r.firm_size_signal, r.fit_for_jone, r.offer_match
        FROM lead_scores s
        JOIN posts p ON p.post_id = s.post_id
        LEFT JOIN processed_leads pl ON pl.post_id = s.post_id
        LEFT JOIN routing r ON r.post_id = s.post_id
        WHERE s.is_hot = 1 AND pl.post_id IS NULL
        ORDER BY s.score DESC, p.created_utc DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["reasons"] = _json.loads(d.pop("score_reasons"))
        out.append(d)
    return out


def mark_processed(
    conn: sqlite3.Connection,
    post_id: str,
    queue_file: str,
    offer_match: str | None = None,
) -> None:
    now = int(_time.time())
    conn.execute(
        """
        INSERT INTO processed_leads (post_id, queue_file, processed_at, offer_match)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            queue_file = excluded.queue_file,
            processed_at = excluded.processed_at,
            offer_match = excluded.offer_match
        """,
        (post_id, queue_file, now, offer_match),
    )
    conn.commit()


def update_outcome(conn: sqlite3.Connection, post_id: str, outcome: str) -> None:
    now = int(_time.time())
    conn.execute(
        """
        UPDATE processed_leads
        SET outcome = ?, posted_at = COALESCE(posted_at, ?)
        WHERE post_id = ?
        """,
        (outcome, now, post_id),
    )
    conn.commit()


def upsert_routing(
    conn: sqlite3.Connection,
    post_id: str,
    problem_category: str,
    firm_size_signal: str,
    fit_for_jone: str,
    offer_match: str,
    tier: str,
    expected_value_usd: int,
) -> None:
    now = int(_time.time())
    conn.execute(
        """
        INSERT INTO routing (
            post_id, problem_category, firm_size_signal, fit_for_jone,
            offer_match, tier, expected_value_usd, routed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            problem_category = excluded.problem_category,
            firm_size_signal = excluded.firm_size_signal,
            fit_for_jone = excluded.fit_for_jone,
            offer_match = excluded.offer_match,
            tier = excluded.tier,
            expected_value_usd = excluded.expected_value_usd,
            routed_at = excluded.routed_at
        """,
        (post_id, problem_category, firm_size_signal, fit_for_jone,
         offer_match, tier, expected_value_usd, now),
    )
    conn.commit()


def fetch_top_comments(
    conn: sqlite3.Connection, post_id: str, limit: int = 10
) -> list[dict]:
    """Return top-scored comments for a post.

    Each row is a dict with keys: author, body, score, depth.
    Ordered by score DESC, with created_utc ASC as a deterministic
    tie-break so two runs on the same data always return the same order.
    """
    rows = conn.execute(
        """
        SELECT author, body, score, depth
        FROM comments
        WHERE post_id = ?
        ORDER BY score DESC, created_utc ASC
        LIMIT ?
        """,
        (post_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]
