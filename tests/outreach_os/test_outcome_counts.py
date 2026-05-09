import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from agents.outreach_os import outcome_counts


def _db_with(repo: Path, source: str, rows: list[tuple]) -> Path:
    db_path = repo / f"agents/{source}_intel/{source}_intel.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE processed_leads (
            post_id TEXT PRIMARY KEY,
            queue_file TEXT,
            processed_at INTEGER,
            posted_at INTEGER,
            outcome TEXT,
            offer_match TEXT
        );
    """)
    conn.executemany("INSERT INTO processed_leads VALUES (?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    return db_path


def test_count_revops(tmp_repo_root):
    now = int(datetime.now().timestamp())
    rows = [
        ("p1", "q.md", now, now, "responded", "outbound_engine"),
        ("p2", "q.md", now, now, "ghosted", "outbound_engine"),
        ("p3", "q.md", now, now, "client", "outbound_engine"),
        ("p4", "q.md", now, now, "dmd_back", "outbound_engine"),
        ("p5", "q.md", now, now, None, "outbound_engine"),
    ]
    _db_with(tmp_repo_root, "revops", rows)
    counts = outcome_counts.count("revops", window_days=30)
    assert counts == {"sent": 5, "responded": 1, "dmd_back": 1, "ghosted": 1, "client": 1, "unsubscribed": 0}


def test_count_excludes_outside_window(tmp_repo_root):
    forty_days_ago = int((datetime.now() - timedelta(days=40)).timestamp())
    now = int(datetime.now().timestamp())
    rows = [
        ("old", "q.md", forty_days_ago, forty_days_ago, "client", "x"),
        ("new", "q.md", now, now, "client", "x"),
    ]
    _db_with(tmp_repo_root, "pe", rows)
    counts = outcome_counts.count("pe", window_days=30)
    assert counts["sent"] == 1
    assert counts["client"] == 1


def test_count_zero_when_db_missing(tmp_repo_root):
    counts = outcome_counts.count("revops", window_days=30)
    assert counts == {"sent": 0, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 0, "unsubscribed": 0}


def test_count_reddit_mine_from_outcomes_json(tmp_repo_root):
    now = datetime.now().isoformat()
    out = tmp_repo_root / "agents/reddit_mine/outcomes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f'{{"a": {{"posted_at": "{now}", "outcome": "responded"}}, "b": {{"posted_at": "{now}", "outcome": "client"}}}}')
    counts = outcome_counts.count("reddit_mine", window_days=30)
    assert counts["sent"] == 2
    assert counts["responded"] == 1
    assert counts["client"] == 1
