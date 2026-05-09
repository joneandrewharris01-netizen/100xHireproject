"""Read pending-outcome lists from each pipeline's storage.

revops + pe -> SQLite processed_leads (outcome IS NULL, posted_at older than threshold)
reddit_mine -> agents/reddit_mine/outcomes.json
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

_DB_PATHS = {
    "revops": Path("agents/revops_intel/revops_intel.db"),
    "pe": Path("agents/pe_intel/pe_intel.db"),
}
_REDDIT_OUTCOMES = Path("agents/reddit_mine/outcomes.json")


def _fetch_db(source: str, stale_days: int) -> list[dict]:
    db_path = _DB_PATHS[source]
    if not db_path.exists():
        return []
    cutoff = int((datetime.now() - timedelta(days=stale_days)).timestamp())
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT post_id, queue_file, posted_at, processed_at
        FROM processed_leads
        WHERE outcome IS NULL
          AND COALESCE(posted_at, processed_at) <= ?
        """,
        (cutoff,),
    ).fetchall()
    conn.close()
    return [
        {
            "source": source,
            "post_id": r["post_id"],
            "queue_file": r["queue_file"],
            "posted_at": datetime.fromtimestamp(r["posted_at"] or r["processed_at"]).isoformat(timespec="seconds"),
        }
        for r in rows
    ]


def fetch_revops(stale_days: int = 7) -> list[dict]:
    return _fetch_db("revops", stale_days)


def fetch_pe(stale_days: int = 7) -> list[dict]:
    return _fetch_db("pe", stale_days)


def fetch_reddit_mine(stale_days: int = 7) -> list[dict]:
    if not _REDDIT_OUTCOMES.exists():
        return []
    data = json.loads(_REDDIT_OUTCOMES.read_text())
    cutoff = datetime.now() - timedelta(days=stale_days)
    out: list[dict] = []
    for post_id, entry in data.items():
        if entry.get("outcome"):
            continue
        posted_at_raw = entry.get("posted_at")
        if not posted_at_raw:
            continue
        if datetime.fromisoformat(posted_at_raw) > cutoff:
            continue
        out.append({"source": "reddit_mine", "post_id": post_id, "posted_at": posted_at_raw})
    return out


def fetch_all(stale_days: int = 7) -> list[dict]:
    return fetch_revops(stale_days) + fetch_pe(stale_days) + fetch_reddit_mine(stale_days)
