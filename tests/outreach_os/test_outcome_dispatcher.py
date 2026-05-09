import json
import sqlite3
from pathlib import Path

from agents.outreach_os import outcome_dispatcher


def _make_revops_db(repo: Path) -> None:
    p = repo / "agents/revops_intel/revops_intel.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.executescript("""
        CREATE TABLE processed_leads (
            post_id TEXT PRIMARY KEY,
            queue_file TEXT, processed_at INTEGER, posted_at INTEGER, outcome TEXT, offer_match TEXT
        );
    """)
    conn.execute("INSERT INTO processed_leads VALUES ('p1', 'q.md', 0, 0, NULL, 'x')")
    conn.commit(); conn.close()


def test_dispatch_revops_writes_db(tmp_repo_root):
    _make_revops_db(tmp_repo_root)
    outcome_dispatcher.dispatch({"source": "revops", "post_id": "p1", "outcome": "responded", "conflict": False})
    conn = sqlite3.connect("agents/revops_intel/revops_intel.db")
    row = conn.execute("SELECT outcome FROM processed_leads WHERE post_id='p1'").fetchone()
    conn.close()
    assert row[0] == "responded"


def test_dispatch_reddit_mine_writes_json(tmp_repo_root):
    outcome_dispatcher.dispatch({"source": "reddit_mine", "post_id": "p2", "outcome": "client", "conflict": False})
    data = json.loads(Path("agents/reddit_mine/outcomes.json").read_text())
    assert data["p2"]["outcome"] == "client"


def test_dispatch_skips_conflict(tmp_repo_root):
    out = outcome_dispatcher.dispatch({"source": "revops", "post_id": "p1", "outcome": "responded", "conflict": True})
    assert out is False
