"""Unit tests for tier derivation per spec section 'Tier derivation rules'."""
import pytest

from agents.outreach_os import tier


@pytest.mark.parametrize("score,expected", [
    (95, "HOT"),
    (80, "HOT"),
    (79, "WARM"),
    (60, "WARM"),
    (59, "AUTHORITY"),
    (40, "AUTHORITY"),
    (39, None),
    (0, None),
])
def test_score_to_tier_default_thresholds(score, expected):
    assert tier.score_to_tier(score) == expected


def test_reddit_mine_tier_passthrough():
    assert tier.derive("reddit_mine", {"tier": "HOT"}) == "HOT"
    assert tier.derive("reddit_mine", {"tier": "WARM"}) == "WARM"
    assert tier.derive("reddit_mine", {"tier": "AUTHORITY"}) == "AUTHORITY"


def test_revops_tier_from_score():
    assert tier.derive("revops", {"score": 92}) == "HOT"
    assert tier.derive("revops", {"score": 70}) == "WARM"
    assert tier.derive("revops", {"score": 45}) == "AUTHORITY"
    assert tier.derive("revops", {"score": 30}) is None


def test_pe_tier_from_score():
    assert tier.derive("pe", {"score": 85}) == "HOT"
    assert tier.derive("pe", {"score": 50}) == "AUTHORITY"


def test_unknown_source_raises():
    with pytest.raises(ValueError, match="unknown source"):
        tier.derive("twitter", {"score": 99})


def test_thresholds_overridable():
    custom = {"hot_min_score": 90, "warm_min_score": 70, "authority_min_score": 50}
    assert tier.score_to_tier(85, thresholds=custom) == "WARM"
    assert tier.score_to_tier(60, thresholds=custom) == "AUTHORITY"
