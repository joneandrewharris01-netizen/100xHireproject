"""Tests for queue_writer.write."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import queue_writer


@pytest.fixture
def sample_lead():
    return json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "sample_lead.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def sample_comments():
    return json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "sample_comments.json").read_text(encoding="utf-8")
    )


def test_write_creates_file_with_frontmatter(tmp_path, monkeypatch, sample_lead, sample_comments):
    monkeypatch.setattr(queue_writer, "_QUEUE_DIR", tmp_path)
    out_path = queue_writer.write(
        sample_lead, sample_comments, "the comment", "the dm",
        kb_diff={"tools": {"smartlead": {"mention_count": 1}}},
        flagged=False,
    )
    text = Path(out_path).read_text(encoding="utf-8")
    assert text.startswith("---")
    assert f"post_id: {sample_lead['post_id']}" in text
    assert "the comment" in text
    assert "the dm" in text
    assert "Added tool" in text
    assert "_FLAGGED_" not in out_path


def test_write_flagged_prefix(tmp_path, monkeypatch, sample_lead, sample_comments):
    monkeypatch.setattr(queue_writer, "_QUEUE_DIR", tmp_path)
    out_path = queue_writer.write(
        sample_lead, sample_comments, "c", "d", kb_diff={}, flagged=True,
    )
    assert "_FLAGGED_" in Path(out_path).name
