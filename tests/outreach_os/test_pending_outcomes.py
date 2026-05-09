import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from agents.outreach_os import pending_outcomes


def _bootstrap_revops_db(repo: Path) -> Path:
    db_path = repo / "agents/revops_intel/revops_intel.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE processed_leads (
            post_id TEXT PRIMARY KEY,
            queue_file TEXT NOT NULL,
            processed_at INTEGER NOT NULL,
            posted_at INTEGER,
            outcome TEXT,
            offer_match TEXT
        );
    """)
    eight_days_ago = int((datetime.now() - timedelta(days=8)).timestamp())
    conn.execute(
        "INSERT INTO processed_leads VALUES (?, ?, ?, ?, NULL, ?)",
        ("stale1", "queue/x.md", eight_days_ago, eight_days_ago, "outbound_engine"),
    )
    one_day_ago = int((datetime.now() - timedelta(days=1)).timestamp())
    conn.execute(
        "INSERT INTO processed_leads VALUES (?, ?, ?, ?, NULL, ?)",
        ("fresh1", "queue/y.md", one_day_ago, one_day_ago, "outbound_engine"),
    )
    conn.execute(
        "INSERT INTO processed_leads VALUES (?, ?, ?, ?, ?, ?)",
        ("done1", "queue/z.md", eight_days_ago, eight_days_ago, "responded", "outbound_engine"),
    )
    conn.commit()
    conn.close()
    return db_path


def test_revops_returns_only_stale_pending(tmp_repo_root):
    _bootstrap_revops_db(tmp_repo_root)
    pending = pending_outcomes.fetch_revops(stale_days=7)
    ids = {p["post_id"] for p in pending}
    assert ids == {"stale1"}


def test_revops_returns_empty_when_db_missing(tmp_repo_root):
    pending = pending_outcomes.fetch_revops(stale_days=7)
    assert pending == []


def test_reddit_mine_returns_pending_from_outcomes_json(tmp_repo_root):
    out_path = tmp_repo_root / "agents/reddit_mine/outcomes.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    eight_days_ago = (datetime.now() - timedelta(days=8)).isoformat()
    one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()
    out_path.write_text(f'''{{
        "stalePost": {{"posted_at": "{eight_days_ago}", "outcome": null}},
        "freshPost": {{"posted_at": "{one_day_ago}", "outcome": null}},
        "donePost": {{"posted_at": "{eight_days_ago}", "outcome": "client"}}
    }}''')
    pending = pending_outcomes.fetch_reddit_mine(stale_days=7)
    ids = {p["post_id"] for p in pending}
    assert ids == {"stalePost"}


def test_reddit_mine_returns_empty_when_outcomes_missing(tmp_repo_root):
    pending = pending_outcomes.fetch_reddit_mine(stale_days=7)
    assert pending == []
