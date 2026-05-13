"""Tests for llm_extract.extract.

llm_client.complete is mocked so we control the model's return value.
Fixture lead matches db.fetch_hot_unprocessed shape (per Task 1.4).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import llm_extract, llm_client


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def sample_lead():
    return json.loads((FIXTURE_DIR / "sample_lead.json").read_text(encoding="utf-8"))


@pytest.fixture
def sample_comments():
    return json.loads((FIXTURE_DIR / "sample_comments.json").read_text(encoding="utf-8"))


def test_extract_returns_parsed_json(monkeypatch, sample_lead, sample_comments):
    response_json = {
        "tools": {"smartlead": {"category": "outbound", "first_seen": sample_lead["post_id"],
                                "mention_count": 1, "sentiment_summary": "mixed",
                                "common_complaints": ["deliverability issues"],
                                "common_praise": [], "example_quotes": ["Smartlead"]}},
        "pains": {}, "personas": {}, "jargon": {},
    }
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: json.dumps(response_json))

    out = llm_extract.extract(sample_lead, sample_comments)

    assert out == response_json
    assert "smartlead" in out["tools"]


def test_extract_strips_think_blocks(monkeypatch, sample_lead, sample_comments):
    raw = '<think>analyzing the thread</think>\n{"tools": {}, "pains": {}, "personas": {}, "jargon": {}}'
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: raw)

    out = llm_extract.extract(sample_lead, sample_comments)
    assert out == {"tools": {}, "pains": {}, "personas": {}, "jargon": {}}


def test_extract_retries_once_on_json_parse_failure(monkeypatch, sample_lead, sample_comments):
    calls = []
    responses = ["this is not json", '{"tools": {}, "pains": {}, "personas": {}, "jargon": {}}']
    def fake(prompt, **kw):
        calls.append(prompt)
        return responses.pop(0)
    monkeypatch.setattr(llm_client, "complete", fake)

    out = llm_extract.extract(sample_lead, sample_comments)

    assert len(calls) == 2
    assert "RETURN ONLY VALID JSON" in calls[1]
    assert out == {"tools": {}, "pains": {}, "personas": {}, "jargon": {}}


def test_extract_returns_empty_dict_after_two_failures(monkeypatch, tmp_path,
                                                       sample_lead, sample_comments):
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: "still not json")
    monkeypatch.setattr(llm_extract, "_FAILED_LOG", str(tmp_path / "failed.jsonl"))

    out = llm_extract.extract(sample_lead, sample_comments)

    assert out == {}
    log = (tmp_path / "failed.jsonl").read_text(encoding="utf-8")
    assert sample_lead["post_id"] in log
    assert "json_parse" in log
