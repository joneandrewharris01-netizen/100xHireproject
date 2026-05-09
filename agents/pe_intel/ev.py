"""Expected value calculation per tier.

Pure functions. Given a classified lead + a partners list, compute EV for
T1 (Jone delivers), T2 (broker meeting), T3 (vendor referral). The router
picks the max-EV path.

Numbers are heuristic v1. They calibrate as revenue_outcomes data accumulates.
"""
from __future__ import annotations

# --- Tier 1: Jone delivers ---

T1_AVG_DEAL_USD = 1500       # mix of $497 builds and $1,497 retainers
T1_FIT_CLOSE_RATES = {       # P(close from cold lead | fit_for_jone)
    "high": 0.10,
    "med": 0.05,
    "low": 0.00,             # Don't pitch Jone when fit is low — go T2/T3 or skip
}


def ev_tier1(lead: dict) -> int:
    """EV for Jone-delivers path. Zero if fit is low."""
    fit = lead.get("fit_for_jone", "low")
    rate = T1_FIT_CLOSE_RATES.get(fit, 0.0)
    return int(T1_AVG_DEAL_USD * rate)


# --- Tier 2: broker meeting to a credible bigger company ---

T2_QUALIFIED_RATE = 0.40     # P(meeting is "qualified" once we book it)


def ev_tier2(lead: dict, partners: list[dict]) -> tuple[int, dict | None]:
    """EV for broker-a-meeting path. Returns (ev, best_partner) or (0, None)
    if no T2 partner handles this category.

    T2 partners are big B2B competitors Jone can DM. They have no public
    program — Jone reaches out and negotiates. We include not_applied,
    applied, AND approved (everything except 'rejected') because the
    EV is "what's this lead worth if a T2 path opens up", not "what's
    guaranteed today". Rejected partners are filtered.
    """
    category = lead.get("problem_category", "other")
    fit = lead.get("fit_for_jone", "low")

    if fit == "high":
        return 0, None  # T1 wins; don't broker a hot Jone fit

    candidates = [p for p in partners
                  if p.get("tier") == "T2"
                  and p.get("category") == category
                  and p.get("application_status") != "rejected"]
    if not candidates:
        return 0, None

    best = max(candidates, key=lambda p: p.get("payout_max_usd") or 0)
    payout = (best.get("payout_max_usd") or best.get("payout_min_usd") or 0)
    # Discount unapproved partners by 50% (factor in DM acceptance rate)
    if best.get("application_status") != "approved":
        payout = int(payout * 0.5)
    ev = int(payout * T2_QUALIFIED_RATE)
    return ev, best


# --- Tier 3: vendor referral ---

T3_CLOSE_RATE = 0.10         # P(lead actually buys the vendor)


def ev_tier3(lead: dict, partners: list[dict]) -> tuple[int, dict | None]:
    """EV for vendor-referral path. Returns (ev, best_partner) or (0, None)."""
    category = lead.get("problem_category", "other")

    candidates = [p for p in partners
                  if p.get("tier") == "T3"
                  and p.get("category") == category
                  and p.get("application_status") == "approved"]
    if not candidates:
        return 0, None

    best = max(candidates, key=lambda p: p.get("payout_max_usd") or 0)
    payout = (best.get("payout_max_usd") or best.get("payout_min_usd") or 0)
    ev = int(payout * T3_CLOSE_RATE)
    return ev, best


def all_evs(lead: dict, partners: list[dict]) -> dict:
    """Compute all three EVs at once. Used by route.py to pick the max."""
    t2_ev, t2_partner = ev_tier2(lead, partners)
    t3_ev, t3_partner = ev_tier3(lead, partners)
    return {
        "T1": (ev_tier1(lead), None),
        "T2": (t2_ev, t2_partner),
        "T3": (t3_ev, t3_partner),
    }
