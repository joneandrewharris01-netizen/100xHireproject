"""Count outcomes per source over a rolling window."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

OUTCOMES = ("responded", "dmd_back", "ghosted", "client", "unsubscribed")

_DB_PATHS = {
    "revops": Path("agents/revops_intel/revops_intel.db"),
    "pe": Path("agents/pe_intel/pe_intel.db"),
}
_REDDIT_JSON = Path("agents/reddit_mine/outcomes.json")


def _zeros() -> dict[str, int]:
    return {"sent": 0, **{k: 0 for k in OUTCOMES}}


def _count_db(source: str, window_days: int) -> dict[str, int]:
    counts = _zeros()
    db_path = _DB_PATHS[source]
    if not db_path.exists():
        return counts
    cutoff = int((datetime.now() - timedelta(days=window_days)).timestamp())
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """
        SELECT outcome
        FROM processed_leads
        WHERE COALESCE(posted_at, processed_at) >= ?
        """,
        (cutoff,),
    ).fetchall()
    conn.close()
    counts["sent"] = len(rows)
    for (outcome,) in rows:
        if outcome in OUTCOMES:
            counts[outcome] += 1
    return counts


def _count_reddit(window_days: int) -> dict[str, int]:
    counts = _zeros()
    if not _REDDIT_JSON.exists():
        return counts
    cutoff = datetime.now() - timedelta(days=window_days)
    data = json.loads(_REDDIT_JSON.read_text())
    for entry in data.values():
        posted = entry.get("posted_at")
        if not posted:
            continue
        if datetime.fromisoformat(posted) < cutoff:
            continue
        counts["sent"] += 1
        oc = entry.get("outcome")
        if oc in OUTCOMES:
            counts[oc] += 1
    return counts


def count(source: str, *, window_days: int = 30) -> dict[str, int]:
    if source in _DB_PATHS:
        return _count_db(source, window_days)
    if source == "reddit_mine":
        return _count_reddit(window_days)
    raise ValueError(f"unknown source: {source}")
