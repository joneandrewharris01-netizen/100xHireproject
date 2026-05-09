import pytest

from agents.pe_intel import db, route


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    db.init_schema(c)
    yield c
    c.close()


def make_lead(post_id="t1", title="Some title", body="Some body",
              category="automation", fit="high"):
    return {
        "post_id": post_id,
        "title": title,
        "selftext": body,
        "problem_category": category,
        "firm_size_signal": "smb",
        "fit_for_jone": fit,
    }


def test_route_high_fit_lead_goes_to_t1():
    """Hot Jone fit + no partners → T1 wins via positive EV."""
    decision = route.route_lead(make_lead(fit="high"), partners=[])
    assert decision["tier"] == "T1"
    assert decision["matched_partner"] is None
    assert decision["expected_value_usd"] > 0


def test_route_low_fit_no_partner_skips():
    decision = route.route_lead(make_lead(fit="low"), partners=[])
    assert decision["tier"] == "skip"
    assert decision["expected_value_usd"] == 0


def test_route_low_fit_with_t3_partner_routes_to_t3():
    partners = [{
        "name": "Deel",
        "category": "automation",
        "tier": "T3",
        "payout_max_usd": 1000,
        "payout_min_usd": 500,
        "application_status": "approved",
    }]
    decision = route.route_lead(make_lead(fit="low"), partners)
    assert decision["tier"] == "T3"
    assert decision["matched_partner"] == "Deel"


def test_route_high_fit_beats_t3_partner():
    """Hot Jone fit ($150 EV) should beat $100 T3 partner."""
    partners = [{
        "name": "SomeVendor",
        "category": "automation",
        "tier": "T3",
        "payout_max_usd": 1000,
        "payout_min_usd": 500,
        "application_status": "approved",
    }]
    decision = route.route_lead(make_lead(fit="high"), partners)
    assert decision["tier"] == "T1"


def test_classify_and_route_full_flow():
    lead = {"post_id": "x", "title": "Building automation at our small business",
            "selftext": "We're a small firm needing n8n setup"}
    decision = route.classify_and_route(lead, partners=[])
    assert decision["problem_category"] == "automation"
    assert decision["firm_size_signal"] == "smb"
    assert decision["fit_for_jone"] == "high"
    assert decision["tier"] == "T1"


def test_apply_to_db_skips_low_score_noise(conn):
    """Posts with lead_score below threshold are forced to skip even if their
    classified category would otherwise route them. Career-question posts
    that mention 'automation' in passing should not become routable leads."""
    db.upsert_post_metadata(conn, {
        "post_id": "noise",
        "subreddit": "test",
        "author": "u_n",
        "title": "Breaking into PE — should I learn automation?",
        "selftext": "Career question, would help to know n8n",
        "score": 0,
        "num_comments": 0,
        "created_utc": 1714000000,
        "permalink": "https://reddit.com/n",
    })
    # Lead scorer would have flagged this with career_question_penalty,
    # ending up well below 30. Simulate that here:
    db.upsert_lead_score(conn, "noise", score=10, reasons=["career_question_penalty"])

    counts = route.apply_to_db(conn, min_lead_score=30)
    assert counts["skip"] == 1
    assert counts["T1"] == 0

    row = conn.execute("SELECT tier FROM routing WHERE post_id='noise'").fetchone()
    assert row["tier"] == "skip"


def test_apply_to_db_routes_all_posts(conn):
    """End-to-end: insert posts, run apply_to_db, verify routing table populated."""
    db.upsert_post_metadata(conn, {
        "post_id": "p_smb",
        "subreddit": "test",
        "author": "u_a",
        "title": "Need automation help",
        "selftext": "I run a small business and need n8n",
        "score": 0,
        "num_comments": 0,
        "created_utc": 1714000000,
        "permalink": "https://reddit.com/p1",
    })
    db.upsert_post_metadata(conn, {
        "post_id": "p_enterprise",
        "subreddit": "test",
        "author": "u_b",
        "title": "F500 looking for AI infra advice",
        "selftext": "I'm at a Fortune 500 evaluating Claude",
        "score": 0,
        "num_comments": 0,
        "created_utc": 1714000000,
        "permalink": "https://reddit.com/p2",
    })

    # min_lead_score=0 — test posts don't have lead_scores; we only want
    # to verify routing logic here, not the noise gate
    counts = route.apply_to_db(conn, min_lead_score=0)
    assert counts["T1"] == 1  # smb automation
    assert counts["skip"] == 1  # enterprise + no partners

    rows = conn.execute("SELECT post_id, tier FROM routing").fetchall()
    by_id = {r["post_id"]: r["tier"] for r in rows}
    assert by_id["p_smb"] == "T1"
    assert by_id["p_enterprise"] == "skip"
