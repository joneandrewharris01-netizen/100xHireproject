"""Tests for llm_generate.generate.

llm_client.complete is mocked. We verify length checks, prompt-leak
detection, truncation detection, and QualityFlag escalation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import llm_generate, llm_client


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def sample_lead():
    return json.loads((FIXTURE_DIR / "sample_lead.json").read_text(encoding="utf-8"))


@pytest.fixture
def sample_comments():
    return json.loads((FIXTURE_DIR / "sample_comments.json").read_text(encoding="utf-8"))


@pytest.fixture
def offer_pitch():
    return {
        "name": "Outbound Engine",
        "ideal_buyer": "B2B SaaS founder Series A-B",
        "scope": "domains, warmup, copy, list, sequence",
        "proof_points_jone_can_use": ["ran outbound playbook at Cause", "5% reply rate avg"],
    }


GOOD_COMMENT = ("Your domain warmup is the first place to look. If you spun up a fresh "
                "domain in the last 30 days and you have not configured DMARC, almost "
                "everything will go to spam regardless of copy quality. Run your sending "
                "address through seinheit.com to check inbox placement, then layer "
                "ICP-tight Clay enrichment so you are sending to people who match the "
                "buyer profile. Cutting your list by half almost always beats adding "
                "more contacts.")
GOOD_DM = ("Saw your post about Smartlead reply rates and the stalled outbound. "
           "I have built outbound for B2B SaaS at Series A-B and hit roughly 4 "
           "percent reply rate by tightening the ICP and rebuilding domain warmup "
           "before touching copy. Recent work included a domain warmup rebuild and "
           "a 3-step Smartlead sequence that cut the list by half and lifted reply "
           "rate. Happy to do a free 30-minute audit of your current setup, no "
           "obligation, just a second pair of eyes on the funnel. Signed, Jone.")


def test_generate_returns_clean_comment_and_dm(monkeypatch, sample_lead,
                                                sample_comments, offer_pitch):
    responses = iter([GOOD_COMMENT, GOOD_DM])
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: next(responses))

    comment, dm = llm_generate.generate(sample_lead, sample_comments, offer_pitch)

    assert 60 <= len(comment.split()) <= 250
    assert 60 <= len(dm.split()) <= 180
    assert comment.rstrip().endswith((".", "!", "?"))


def test_generate_retries_on_short_output(monkeypatch, sample_lead,
                                           sample_comments, offer_pitch):
    too_short = "Too brief."
    responses = iter([too_short, GOOD_COMMENT, GOOD_DM])
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: next(responses))

    comment, dm = llm_generate.generate(sample_lead, sample_comments, offer_pitch)
    assert 60 <= len(comment.split())


def test_generate_raises_quality_flag_on_two_short_outputs(monkeypatch, sample_lead,
                                                            sample_comments, offer_pitch):
    too_short = "Too brief."
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: too_short)

    with pytest.raises(llm_generate.QualityFlag) as exc:
        llm_generate.generate(sample_lead, sample_comments, offer_pitch)

    assert "length" in exc.value.reason.lower()
    assert exc.value.comment == too_short


def test_generate_raises_quality_flag_on_prompt_leak(monkeypatch, sample_lead,
                                                      sample_comments, offer_pitch):
    leaked = ("HARD RULES violations will be regex-stripped automatically. "
              "Here is my reply: " + GOOD_COMMENT)
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: leaked)

    with pytest.raises(llm_generate.QualityFlag) as exc:
        llm_generate.generate(sample_lead, sample_comments, offer_pitch)
    assert "prompt_leak" in exc.value.reason.lower() or "leak" in exc.value.reason.lower()


def test_generate_raises_quality_flag_on_truncation(monkeypatch, sample_lead,
                                                     sample_comments, offer_pitch):
    truncated = (GOOD_COMMENT.rstrip(".") + " and then the model just stopped writing "
                 "in the middle of a sentence without finishing the")
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: truncated)

    with pytest.raises(llm_generate.QualityFlag) as exc:
        llm_generate.generate(sample_lead, sample_comments, offer_pitch)
    assert "truncat" in exc.value.reason.lower()
