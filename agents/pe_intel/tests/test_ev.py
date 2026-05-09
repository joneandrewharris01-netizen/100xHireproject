import pytest

from agents.pe_intel import ev


def make_lead(category="automation", fit="high"):
    return {"problem_category": category, "fit_for_jone": fit}


def make_partner(category="automation", tier="T3", payout_max=500,
                 payout_min=100, status="approved"):
    return {
        "category": category,
        "tier": tier,
        "payout_max_usd": payout_max,
        "payout_min_usd": payout_min,
        "application_status": status,
    }


# --- Tier 1 ---

def test_t1_high_fit_returns_positive_ev():
    assert ev.ev_tier1(make_lead(fit="high")) > 0


def test_t1_low_fit_is_zero():
    """Don't pitch Jone when fit is low — let T2/T3 handle or skip."""
    assert ev.ev_tier1(make_lead(fit="low")) == 0


def test_t1_med_between_high_and_low():
    high = ev.ev_tier1(make_lead(fit="high"))
    med = ev.ev_tier1(make_lead(fit="med"))
    low = ev.ev_tier1(make_lead(fit="low"))
    assert low < med < high


# --- Tier 2 ---

def test_t2_returns_zero_when_no_partner():
    e, p = ev.ev_tier2(make_lead(category="automation", fit="low"), partners=[])
    assert e == 0 and p is None


def test_t2_returns_zero_for_high_fit_lead():
    """Don't broker a hot Jone fit — Tier 1 wins."""
    partners = [make_partner(tier="T2")]
    e, p = ev.ev_tier2(make_lead(fit="high"), partners)
    assert e == 0


def test_t2_returns_ev_for_low_fit_with_approved_partner():
    partners = [make_partner(category="automation", tier="T2", payout_max=1000)]
    e, p = ev.ev_tier2(make_lead(category="automation", fit="low"), partners)
    assert e == 400  # 1000 * 0.40
    assert p["category"] == "automation"


def test_t2_includes_unapproved_partners_at_discount():
    """Unapproved T2 partners count at 50% discount (DM-acceptance risk).
    Approved T2 partners count at full payout."""
    unapproved = [make_partner(tier="T2", payout_max=1000, status="not_applied")]
    approved = [make_partner(tier="T2", payout_max=1000, status="approved")]
    e_un, _ = ev.ev_tier2(make_lead(fit="low"), unapproved)
    e_ap, _ = ev.ev_tier2(make_lead(fit="low"), approved)
    assert e_un == 200   # 1000 * 0.5 * 0.40
    assert e_ap == 400   # 1000 * 0.40
    assert e_un < e_ap


def test_t2_skips_rejected_partners():
    partners = [make_partner(tier="T2", payout_max=1000, status="rejected")]
    e, p = ev.ev_tier2(make_lead(fit="low"), partners)
    assert e == 0


def test_t2_picks_highest_payout_when_multiple_partners():
    partners = [
        make_partner(category="automation", tier="T2", payout_max=200),
        make_partner(category="automation", tier="T2", payout_max=1000),
    ]
    e, p = ev.ev_tier2(make_lead(category="automation", fit="low"), partners)
    assert p["payout_max_usd"] == 1000


# --- Tier 3 ---

def test_t3_returns_zero_when_no_partner():
    e, p = ev.ev_tier3(make_lead(), partners=[])
    assert e == 0 and p is None


def test_t3_returns_ev_with_approved_partner():
    partners = [make_partner(category="hiring", tier="T3", payout_max=1000)]
    e, p = ev.ev_tier3(make_lead(category="hiring"), partners)
    assert e == 100  # 1000 * 0.10
    assert p["category"] == "hiring"


def test_t3_filters_by_category():
    partners = [make_partner(category="hiring", tier="T3", payout_max=1000)]
    e, p = ev.ev_tier3(make_lead(category="automation"), partners)
    assert e == 0  # category mismatch


# --- all_evs structure ---

def test_all_evs_returns_three_tiers():
    result = ev.all_evs(make_lead(), partners=[])
    assert set(result.keys()) == {"T1", "T2", "T3"}


def test_all_evs_each_value_is_tuple():
    result = ev.all_evs(make_lead(), partners=[])
    for tier, (e, p) in result.items():
        assert isinstance(e, int)
