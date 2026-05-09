"""Sequential rotation through a static lead list with state persistence."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

_STATE = Path("agents/outreach_os/state.json")


def _load() -> dict:
    if not _STATE.exists():
        return {"last_index": 0, "total_rows": 0, "last_run_date": None, "openers_generated_count": 0}
    return json.loads(_STATE.read_text())


def _save(state: dict) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    _STATE.write_text(json.dumps(state, indent=2))


def pick(rows: list[dict], *, n: int, today: date) -> list[dict]:
    """Pick the next n rows in sequence. Wraps around end of list."""
    state = _load()
    start = state["last_index"]
    total = len(rows)
    state["total_rows"] = total
    if total == 0:
        return []
    end = start + n
    if end <= total:
        picked = rows[start:end]
        new_index = end % total
    else:
        picked = rows[start:total] + rows[: end - total]
        new_index = (end - total) % total
    state["last_index"] = new_index
    state["last_run_date"] = today.isoformat()
    state["openers_generated_count"] += len(picked)
    _save(state)
    return picked
