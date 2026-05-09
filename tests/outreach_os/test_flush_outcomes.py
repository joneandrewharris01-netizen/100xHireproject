import json
import sqlite3
from datetime import date
from pathlib import Path

from agents.outreach_os import flush_outcomes


def _seed(repo: Path):
    db = repo / "agents/revops_intel/revops_intel.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript("CREATE TABLE processed_leads (post_id TEXT PRIMARY KEY, queue_file TEXT, processed_at INTEGER, posted_at INTEGER, outcome TEXT, offer_match TEXT);")
    conn.execute("INSERT INTO processed_leads VALUES ('p1', 'q.md', 0, 0, NULL, 'x')")
    conn.commit(); conn.close()
    brief = repo / f"outreach-os/daily/{date.today().isoformat()}.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text(
        "## Pending outcomes (>7 days old)\n"
        "- [ ] `p1` (revops) posted 2026-05-01T12:00:00\n"
        "  - [x] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub\n"
        "- [ ] `p2` (reddit_mine) posted 2026-05-01T12:00:00\n"
        "  - [x] client   [ ] responded   [ ] dmd_back   [ ] ghosted   [ ] unsub\n"
    )


def test_flush_updates_db_and_json(tmp_repo_root):
    _seed(tmp_repo_root)
    summary = flush_outcomes.run(brief_path=Path(f"outreach-os/daily/{date.today().isoformat()}.md"))
    assert summary["updated"] == 2
    assert summary["unchanged"] == 0
    conn = sqlite3.connect("agents/revops_intel/revops_intel.db")
    assert conn.execute("SELECT outcome FROM processed_leads WHERE post_id='p1'").fetchone()[0] == "responded"
    data = json.loads(Path("agents/reddit_mine/outcomes.json").read_text())
    assert data["p2"]["outcome"] == "client"
