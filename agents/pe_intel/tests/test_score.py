import pytest

from agents.pe_intel import db, score


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    db.init_schema(c)
    yield c
    c.close()


def make_post(**overrides):
    base = {
        "post_id": "test1", "subreddit": "private_equity", "author": "u_x",
        "title": "Generic title", "selftext": "Generic body.",
        "flair": "", "score": 1, "num_comments": 0,
        "created_utc": 1714000000,
        "permalink": "https://reddit.com/test",
    }
    base.update(overrides)
    return base


# --- Rule-by-rule unit tests on score_post() ---

def test_vendor_evaluation_signal():
    post = make_post(title="Looking for alternatives to Pitchbook")
    s, reasons = score.score_post(post)
    assert "vendor_evaluation" in reasons
    assert s >= 25


def test_active_build_signal():
    post = make_post(title="Building AI-first infrastructure at our PE firm")
    s, reasons = score.score_post(post)
    assert "active_build" in reasons


def test_decision_maker_signal():
    post = make_post(selftext="I'm a director at a small fund and need help.")
    _, reasons = score.score_post(post)
    assert "decision_maker_signal" in reasons


def test_career_question_penalty():
    post = make_post(title="Breaking into PE from consulting", selftext="career advice please")
    s, _ = score.score_post(post)
    assert s < 30


def test_career_penalty_catches_mba_and_into_pe_with_punctuation():
    """Word-boundary regex must catch MBA and 'into PE' regardless of punctuation."""
    for title in ["MBA holder pivoting to PE", "How to pivot into PE?",
                  "Into PE from consulting"]:
        s, reasons = score.score_post(make_post(title=title))
        assert "career_question_penalty" in reasons, f"missed: {title}"


def test_score_is_always_0_to_100():
    """No matter what we throw at it, score stays in [0, 100]."""
    extreme = make_post(
        title="Building automation infra rolling out — vendor recommendations vs alternatives",
        selftext="I'm a director at our firm. We're a fund using Claude. Manual process automating workflow.",
        num_comments=200, score=500,
    )
    s, _ = score.score_post(extreme)
    assert 0 <= s <= 100

    negative = make_post(title="Breaking into PE — career advice MBA into PE")
    s, _ = score.score_post(negative)
    assert 0 <= s <= 100


def test_high_signal_post_is_hot():
    post = make_post(
        title="Building AI infra at our PE firm — vendor recommendations?",
        selftext="I'm an operating director at a $1B fund. Currently evaluating "
                 "alternatives to Pitchbook. Our firm uses Claude already.",
        score=20, num_comments=30,
    )
    s, reasons = score.score_post(post)
    assert s >= 70  # is hot
    assert "vendor_evaluation" in reasons
    assert "active_build" in reasons
    assert "decision_maker_signal" in reasons
    assert "speaks_for_firm" in reasons
    assert "automation_relevant" in reasons
    assert "hot_thread" in reasons


# --- Integration test: apply_to_db ---

def test_apply_scoring_writes_lead_scores(conn):
    # Insert 3 posts
    for i, p in enumerate([
        make_post(post_id="hot1",
                  title="Building AI-first infra — alternatives to Pitchbook?",
                  selftext="I'm a partner at our firm. Using Claude.",
                  num_comments=30, score=10),
        make_post(post_id="cold1", title="Career advice: breaking into PE"),
        make_post(post_id="mid1", title="Anyone using Chronograph?"),
    ]):
        db.upsert_post_metadata(conn, p)
    score.apply_to_db(conn)
    rows = conn.execute(
        "SELECT post_id, score, is_hot FROM lead_scores ORDER BY score DESC"
    ).fetchall()
    by_id = {r["post_id"]: r for r in rows}
    assert by_id["hot1"]["is_hot"] == 1
    assert by_id["cold1"]["is_hot"] == 0
    assert by_id["cold1"]["score"] < 30
