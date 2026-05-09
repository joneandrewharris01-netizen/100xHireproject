"""Per-pipeline last_run.json markers.

Written by /outreach-os AFTER a sub-pipeline completes cleanly.
Crashed runs leave no marker, so the next morning re-runs them.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

_PIPELINE_DIRS = {
    "revops": Path("agents/revops_intel"),
    "pe": Path("agents/pe_intel"),
    "reddit_mine": Path("agents/reddit_mine"),
    "vc_pain_analysis": Path("agents/vc_pain_analysis"),
}


def marker_path(pipeline: str) -> Path:
    if pipeline not in _PIPELINE_DIRS:
        raise ValueError(f"unknown pipeline: {pipeline}")
    return _PIPELINE_DIRS[pipeline] / "last_run.json"


def write(pipeline: str, *, new_leads: int, errors: int) -> Path:
    p = marker_path(pipeline)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": date.today().isoformat(),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "new_leads": int(new_leads),
        "errors": int(errors),
    }
    p.write_text(json.dumps(payload, indent=2))
    return p


def read(pipeline: str) -> dict | None:
    p = marker_path(pipeline)
    if not p.exists():
        return None
    return json.loads(p.read_text())


def ran_today(pipeline: str) -> bool:
    data = read(pipeline)
    return bool(data and data.get("date") == date.today().isoformat())
