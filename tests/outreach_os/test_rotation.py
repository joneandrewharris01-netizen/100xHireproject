import json
from datetime import date
from pathlib import Path

from agents.outreach_os import rotation


def test_first_run_picks_first_n(tmp_repo_root):
    rows = [{"name": str(i), "title": "X", "linkedin_url": f"u{i}"} for i in range(50)]
    picked = rotation.pick(rows, n=20, today=date(2026, 5, 9))
    assert len(picked) == 20
    assert picked[0]["name"] == "0"


def test_second_run_advances_pointer(tmp_repo_root):
    rows = [{"name": str(i), "title": "X", "linkedin_url": f"u{i}"} for i in range(50)]
    rotation.pick(rows, n=20, today=date(2026, 5, 9))
    picked = rotation.pick(rows, n=20, today=date(2026, 5, 10))
    names = {r["name"] for r in picked}
    assert "20" in names
    assert "0" not in names


def test_wrap_around(tmp_repo_root):
    rows = [{"name": str(i), "title": "X", "linkedin_url": f"u{i}"} for i in range(10)]
    rotation.pick(rows, n=8, today=date(2026, 5, 9))
    picked = rotation.pick(rows, n=8, today=date(2026, 5, 10))
    assert len(picked) == 8


def test_state_file_persists(tmp_repo_root):
    rows = [{"name": str(i), "title": "X", "linkedin_url": f"u{i}"} for i in range(50)]
    rotation.pick(rows, n=20, today=date(2026, 5, 9))
    state_path = Path("agents/outreach_os/state.json")
    assert state_path.exists()
    state = json.loads(state_path.read_text())
    assert state["last_index"] == 20
    assert state["last_run_date"] == "2026-05-09"
