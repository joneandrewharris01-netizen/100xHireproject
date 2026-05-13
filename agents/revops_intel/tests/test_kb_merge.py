"""Tests for kb_merge.merge_atomic."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import kb_merge


@pytest.fixture
def tmp_kb(tmp_path, monkeypatch):
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()
    for name in ("tools", "pains", "personas", "jargon"):
        (kb_dir / f"{name}.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(kb_merge, "_KB_DIR", kb_dir)
    return kb_dir


def test_merge_adds_new_tool(tmp_kb):
    diff = {"tools": {"smartlead": {"category": "outbound", "mention_count": 1,
                                     "example_quotes": ["quote"]}}}
    kb_merge.merge_atomic(diff)

    data = json.loads((tmp_kb / "tools.json").read_text(encoding="utf-8"))
    assert "smartlead" in data
    assert data["smartlead"]["mention_count"] == 1


def test_merge_increments_existing_mention_count(tmp_kb):
    (tmp_kb / "tools.json").write_text(
        json.dumps({"smartlead": {"category": "outbound", "mention_count": 3,
                                    "example_quotes": ["old"]}}),
        encoding="utf-8",
    )
    diff = {"tools": {"smartlead": {"category": "outbound", "mention_count": 1,
                                     "example_quotes": ["new quote"]}}}
    kb_merge.merge_atomic(diff)

    data = json.loads((tmp_kb / "tools.json").read_text(encoding="utf-8"))
    assert data["smartlead"]["mention_count"] == 4
    assert "old" in data["smartlead"]["example_quotes"]
    assert "new quote" in data["smartlead"]["example_quotes"]


def test_merge_handles_empty_diff(tmp_kb):
    kb_merge.merge_atomic({})
    data = json.loads((tmp_kb / "tools.json").read_text(encoding="utf-8"))
    assert data == {}


def test_merge_ignores_unknown_top_level_keys(tmp_kb):
    diff = {"tools": {"x": {"mention_count": 1}}, "garbage": {"foo": "bar"}}
    kb_merge.merge_atomic(diff)
    assert (tmp_kb / "tools.json").exists()
    assert not (tmp_kb / "garbage.json").exists()


def test_merge_skips_non_dict_entry_values(tmp_kb):
    """If LLM returns a malformed entry (e.g., string instead of dict), skip not crash."""
    diff = {"tools": {"smartlead": "this should be a dict but isn't",
                       "apollo": {"category": "outbound", "mention_count": 1}}}
    kb_merge.merge_atomic(diff)

    data = json.loads((tmp_kb / "tools.json").read_text(encoding="utf-8"))
    assert "smartlead" not in data
    assert "apollo" in data
