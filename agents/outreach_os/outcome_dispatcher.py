"""Dispatch one parsed tickbox entry to the right outcome store."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from agents.reddit_mine import outcomes as reddit_outcomes

# Tickbox uses "unsub" for brevity. Map to the canonical /revops-outcome vocabulary.
_OUTCOME_MAP = {
    "responded": "responded",
    "dmd_back": "dmd_back",
    "ghosted": "ghosted",
    "client": "client",
    "unsub": "unsubscribed",
}


def _dispatch_db(source: str, post_id: str, outcome: str) -> None:
    db_paths = {
        "revops": Path("agents/revops_intel/revops_intel.db"),
        "pe": Path("agents/pe_intel/pe_intel.db"),
    }
    db_path = db_paths[source]
    if not db_path.exists():
        return
    conn = sqlite3.connect(db_path)
    now = int(time.time())
    conn.execute(
        "UPDATE processed_leads SET outcome = ?, posted_at = COALESCE(posted_at, ?) WHERE post_id = ?",
        (outcome, now, post_id),
    )
    conn.commit()
    conn.close()


def dispatch(entry: dict) -> bool:
    """Write one outcome. Returns True if dispatched, False if skipped."""
    if entry.get("conflict"):
        return False
    canonical = _OUTCOME_MAP.get(entry["outcome"])
    if canonical is None:
        return False
    if entry["source"] in {"revops", "pe"}:
        _dispatch_db(entry["source"], entry["post_id"], canonical)
        return True
    if entry["source"] == "reddit_mine":
        reddit_outcomes.record(entry["post_id"], canonical)
        return True
    return False
