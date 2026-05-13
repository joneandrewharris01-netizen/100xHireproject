"""Tests for kb_backups module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import kb_backups


@pytest.fixture
def tmp_kb(tmp_path, monkeypatch):
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()
    for name in ("tools", "pains", "personas", "jargon"):
        (kb_dir / f"{name}.json").write_text('{"v": 1}', encoding="utf-8")
    monkeypatch.setattr(kb_backups, "_KB_DIR", kb_dir)
    monkeypatch.setattr(kb_backups, "_BACKUP_DIR", kb_dir / ".backups")
    return kb_dir


def test_snapshot_creates_backup_files(tmp_kb):
    kb_backups.snapshot()
    backups = list((tmp_kb / ".backups").glob("*.bak"))
    assert len(backups) == 4
    assert all(b.stat().st_size > 0 for b in backups)


def test_snapshot_prunes_to_7_per_file(tmp_kb, monkeypatch):
    for i in range(10):
        monkeypatch.setattr(
            kb_backups, "_TIMESTAMP_FN",
            lambda i=i: f"2026-05-13T00-00-{i:02d}",
        )
        kb_backups.snapshot()

    for name in ("tools", "pains", "personas", "jargon"):
        backups = sorted((tmp_kb / ".backups").glob(f"*_{name}.json.bak"))
        assert len(backups) == 7, f"{name} has {len(backups)} backups, expected 7"
        assert backups[0].name.startswith("2026-05-13T00-00-03_")
        assert backups[-1].name.startswith("2026-05-13T00-00-09_")


def test_restore_latest_returns_most_recent(tmp_kb, monkeypatch):
    monkeypatch.setattr(kb_backups, "_TIMESTAMP_FN", lambda: "2026-05-13T00-00-01")
    kb_backups.snapshot()
    monkeypatch.setattr(kb_backups, "_TIMESTAMP_FN", lambda: "2026-05-13T00-00-02")
    (tmp_kb / "tools.json").write_text('{"v": 2}', encoding="utf-8")
    kb_backups.snapshot()

    restored = kb_backups.restore_latest("tools")
    assert json.loads(restored) == {"v": 2}
