"""Outcome state for the reddit_mine pipeline.

Stored at agents/reddit_mine/outcomes.json. One key per post_id.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

VALID_OUTCOMES = {"responded", "dmd_back", "ghosted", "client", "unsubscribed"}
_PATH = Path("agents/reddit_mine/outcomes.json")


def _load() -> dict:
    if not _PATH.exists():
        return {}
    return json.loads(_PATH.read_text())


def _save(data: dict) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(data, indent=2))


def record(post_id: str, outcome: str) -> None:
    if outcome not in VALID_OUTCOMES:
        raise ValueError(f"invalid outcome: {outcome}. allowed: {sorted(VALID_OUTCOMES)}")
    data = _load()
    now = datetime.now().isoformat(timespec="seconds")
    if post_id not in data:
        data[post_id] = {"posted_at": now, "outcome": outcome, "outcome_logged_at": now}
    else:
        if data[post_id].get("outcome") == outcome:
            return  # idempotent
        data[post_id]["outcome"] = outcome
        data[post_id]["outcome_logged_at"] = now
        if not data[post_id].get("posted_at"):
            data[post_id]["posted_at"] = now
    _save(data)
