"""Routing layer.

Given a classified lead and the partners table, decide which tier to pursue
(T1: Jone delivers, T2: broker, T3: refer) and which partner to use.

Picks the max-EV path. Fallback: if all EVs are zero, route as T1 'skip'.
"""
from __future__ import annotations

from . import db, classify, ev


def route_lead(lead: dict, partners: list[dict]) -> dict:
    """Given an already-classified lead, return the routing decision.

    Lead must already have problem_category, firm_size_signal, fit_for_jone.
    Returns dict with: tier, expected_value_usd, matched_partner (or None).
    """
    evs = ev.all_evs(lead, partners)
    # evs = {"T1": (ev, None), "T2": (ev, partner_dict|None), "T3": (ev, partner_dict|None)}

    best_tier = max(evs, key=lambda t: evs[t][0])
    best_ev, best_partner = evs[best_tier]

    if best_ev == 0:
        # No path has positive EV — route as skip but record what we computed
        return {
            "tier": "skip",
            "expected_value_usd": 0,
            "matched_partner": None,
        }

    return {
        "tier": best_tier,
        "expected_value_usd": best_ev,
        "matched_partner": best_partner["name"] if best_partner else None,
    }


def classify_and_route(lead: dict, partners: list[dict]) -> dict:
    """Convenience: classify a raw lead, then route. Returns merged dict."""
    cls = classify.classify(lead)
    decision = route_lead({**lead, **cls}, partners)
    return {**cls, **decision}


MIN_LEAD_SCORE_FOR_ROUTING = 30


def apply_to_db(conn, min_lead_score: int = MIN_LEAD_SCORE_FOR_ROUTING) -> dict:
    """Classify + route every post in the DB. Upserts into routing table.

    Posts whose lead_score (heuristic relevance) is below `min_lead_score`
    are routed as 'skip' regardless of category — those are noise (career
    questions, off-topic, etc) that triggered keyword matches by accident.

    Returns counts by tier.
    """
    # Pull all partners once
    partner_rows = conn.execute("SELECT * FROM partners").fetchall()
    partners = [dict(r) for r in partner_rows]

    # Pull posts WITH lead_score so we can gate noise leads
    rows = conn.execute(
        """
        SELECT p.post_id, p.title, p.selftext,
               COALESCE(s.score, 0) AS lead_score
        FROM posts p
        LEFT JOIN lead_scores s ON s.post_id = p.post_id
        """
    ).fetchall()

    counts = {"T1": 0, "T2": 0, "T3": 0, "skip": 0}
    for r in rows:
        if r["lead_score"] < min_lead_score:
            # Noise lead — classify for the record but force skip
            cls = classify.classify(dict(r))
            db.upsert_routing(
                conn,
                post_id=r["post_id"],
                problem_category=cls["problem_category"],
                firm_size_signal=cls["firm_size_signal"],
                fit_for_jone=cls["fit_for_jone"],
                tier="skip",
                expected_value_usd=0,
                matched_partner=None,
            )
            counts["skip"] += 1
            continue

        decision = classify_and_route(dict(r), partners)
        db.upsert_routing(
            conn,
            post_id=r["post_id"],
            problem_category=decision["problem_category"],
            firm_size_signal=decision["firm_size_signal"],
            fit_for_jone=decision["fit_for_jone"],
            tier=decision["tier"],
            expected_value_usd=decision["expected_value_usd"],
            matched_partner=decision["matched_partner"],
        )
        counts[decision["tier"]] = counts.get(decision["tier"], 0) + 1
    return counts


def main() -> int:
    conn = db.connect()
    db.init_schema(conn)
    stats = apply_to_db(conn)
    print(f"DONE: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
