"""SQLite layer for PE Intel agent.

All DB I/O lives here. No other module opens pe_intel.db directly.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).parent / "pe_intel.db"

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
    outcome      TEXT
);

CREATE TABLE IF NOT EXISTS routing (
    post_id            TEXT PRIMARY KEY REFERENCES posts(post_id),
    problem_category   TEXT NOT NULL,
    firm_size_signal   TEXT NOT NULL,
    fit_for_jone       TEXT NOT NULL,
    tier               TEXT NOT NULL,
    expected_value_usd INTEGER NOT NULL,
    matched_partner    TEXT,
    routed_at          INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_routing_tier ON routing(tier, expected_value_usd DESC);
CREATE INDEX IF NOT EXISTS idx_routing_category ON routing(problem_category);

CREATE TABLE IF NOT EXISTS partners (
    name                TEXT PRIMARY KEY,
    category            TEXT NOT NULL,
    tier                TEXT NOT NULL,
    payout_model        TEXT NOT NULL,
    payout_min_usd      INTEGER,
    payout_max_usd      INTEGER,
    apply_url           TEXT,
    application_status  TEXT NOT NULL DEFAULT 'not_applied',
    notes               TEXT,
    added_at            INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_partners_category ON partners(category, tier);
CREATE INDEX IF NOT EXISTS idx_partners_status ON partners(application_status);

CREATE TABLE IF NOT EXISTS revenue_outcomes (
    rowid_       INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id      TEXT NOT NULL REFERENCES posts(post_id),
    partner      TEXT,
    tier         TEXT NOT NULL,
    sent_at      INTEGER NOT NULL,
    status       TEXT NOT NULL,
    revenue_usd  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_revenue_post ON revenue_outcomes(post_id);
CREATE INDEX IF NOT EXISTS idx_revenue_status ON revenue_outcomes(status);
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


def upsert_post_metadata(conn: sqlite3.Connection, post: dict) -> None:
    """Insert or refresh listing-level fields. Does NOT touch last_updated.

    last_updated is reserved for "last successful comment-tree fetch" so the
    re-scrape policy works correctly. On INSERT, last_updated starts at 0
    (never scraped comments yet).
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
            -- last_updated intentionally NOT updated here
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
    """Re-scrape policy (last_updated = last successful comments fetch):
    - Never seen, or last_updated == 0 → True (never fetched comments yet)
    - Post <7 days old AND last_updated <24h ago → False
    - Post <7 days old AND last_updated >=24h ago → True
    - Post 7-30 days old AND last_updated <7d ago → False
    - Post 7-30 days old AND last_updated >=7d ago → True
    - Post >30 days old → False (frozen)
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


import json as _json

HOT_THRESHOLD = 70


def insert_comment(conn: sqlite3.Connection, c: dict) -> None:
    """Insert a comment; no-op on conflict (idempotent re-scrape)."""
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
    """Hot leads (is_hot=1) that have not been processed yet, highest score first.

    Returns dicts with `permalink` aliased to `url` and `score_reasons`
    pre-deserialized to a Python list, matching the queue-file frontmatter
    convention so the slash command doesn't have to remap fields.
    """
    rows = conn.execute(
        """
        SELECT p.post_id, p.subreddit, p.author, p.title, p.selftext,
               p.score AS reddit_score, p.num_comments,
               p.permalink AS url,
               p.created_utc,
               s.score, s.score_reasons
        FROM lead_scores s
        JOIN posts p ON p.post_id = s.post_id
        LEFT JOIN processed_leads pl ON pl.post_id = s.post_id
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


def mark_processed(conn: sqlite3.Connection, post_id: str, queue_file: str) -> None:
    now = int(_time.time())
    conn.execute(
        """
        INSERT INTO processed_leads (post_id, queue_file, processed_at)
        VALUES (?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            queue_file = excluded.queue_file,
            processed_at = excluded.processed_at
        """,
        (post_id, queue_file, now),
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


# --- Routing layer (Tier 1/2/3 money-maximizing system) ---

def upsert_routing(
    conn: sqlite3.Connection,
    post_id: str,
    problem_category: str,
    firm_size_signal: str,
    fit_for_jone: str,
    tier: str,
    expected_value_usd: int,
    matched_partner: str | None = None,
) -> None:
    now = int(_time.time())
    conn.execute(
        """
        INSERT INTO routing (
            post_id, problem_category, firm_size_signal, fit_for_jone,
            tier, expected_value_usd, matched_partner, routed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            problem_category = excluded.problem_category,
            firm_size_signal = excluded.firm_size_signal,
            fit_for_jone = excluded.fit_for_jone,
            tier = excluded.tier,
            expected_value_usd = excluded.expected_value_usd,
            matched_partner = excluded.matched_partner,
            routed_at = excluded.routed_at
        """,
        (post_id, problem_category, firm_size_signal, fit_for_jone,
         tier, expected_value_usd, matched_partner, now),
    )
    conn.commit()


def fetch_routed_by_tier(
    conn: sqlite3.Connection, tier: str, limit: int = 50
) -> list[dict]:
    """Top routed leads in a given tier, ordered by expected value."""
    rows = conn.execute(
        """
        SELECT p.post_id, p.title, p.selftext, p.author, p.subreddit,
               p.permalink AS url,
               r.problem_category, r.firm_size_signal, r.fit_for_jone,
               r.tier, r.expected_value_usd, r.matched_partner,
               s.score AS lead_score
        FROM routing r
        JOIN posts p ON p.post_id = r.post_id
        LEFT JOIN lead_scores s ON s.post_id = r.post_id
        WHERE r.tier = ?
        ORDER BY r.expected_value_usd DESC
        LIMIT ?
        """,
        (tier, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_partner(
    conn: sqlite3.Connection,
    name: str,
    category: str,
    tier: str,
    payout_model: str,
    payout_min_usd: int | None = None,
    payout_max_usd: int | None = None,
    apply_url: str | None = None,
    notes: str | None = None,
) -> None:
    now = int(_time.time())
    conn.execute(
        """
        INSERT INTO partners (
            name, category, tier, payout_model, payout_min_usd,
            payout_max_usd, apply_url, notes, added_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            category = excluded.category,
            tier = excluded.tier,
            payout_model = excluded.payout_model,
            payout_min_usd = excluded.payout_min_usd,
            payout_max_usd = excluded.payout_max_usd,
            apply_url = excluded.apply_url,
            notes = excluded.notes
        """,
        (name, category, tier, payout_model, payout_min_usd,
         payout_max_usd, apply_url, notes, now),
    )
    conn.commit()


def fetch_partners_for_category(
    conn: sqlite3.Connection, category: str, tier: str | None = None
) -> list[dict]:
    """Return partners that handle this category, optionally filtered by tier."""
    if tier:
        rows = conn.execute(
            """
            SELECT * FROM partners
            WHERE category = ? AND tier = ?
            ORDER BY payout_max_usd DESC
            """,
            (category, tier),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM partners WHERE category = ? ORDER BY payout_max_usd DESC",
            (category,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_partner_application_status(
    conn: sqlite3.Connection, name: str, status: str
) -> None:
    """status in {not_applied, applied, approved, rejected}"""
    conn.execute(
        "UPDATE partners SET application_status = ? WHERE name = ?",
        (status, name),
    )
    conn.commit()


def record_revenue_outcome(
    conn: sqlite3.Connection,
    post_id: str,
    tier: str,
    status: str,
    partner: str | None = None,
    revenue_usd: int = 0,
) -> None:
    """Append-only event log for outreach outcomes per (lead, partner)."""
    now = int(_time.time())
    conn.execute(
        """
        INSERT INTO revenue_outcomes (post_id, partner, tier, sent_at, status, revenue_usd)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (post_id, partner, tier, now, status, revenue_usd),
    )
    conn.commit()
