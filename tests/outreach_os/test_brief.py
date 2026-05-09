from datetime import date

from agents.outreach_os import brief


def _lead(source, fm):
    return {"source": source, "path": "queue/x.md", "frontmatter": fm}


def test_render_includes_header_and_date():
    md = brief.render(
        today=date(2026, 5, 9),
        leads=[],
        linkedin=[],
        pending=[],
        pipelines_run=[],
        pipelines_skipped=[],
        pipelines_failed=[],
    )
    assert "# Outreach OS - 2026-05-09" in md
    assert "date: 2026-05-09" in md


def test_render_sorts_by_tier_priority():
    leads = [
        _lead("revops", {"post_id": "warm1", "score": 70, "author": "u/w", "subreddit": "sales"}),
        _lead("revops", {"post_id": "hot1", "score": 92, "author": "u/h", "subreddit": "sales"}),
        _lead("reddit_mine", {"post_id": "auth1", "tier": "AUTHORITY", "author": "u/a", "subreddit": "n8n"}),
    ]
    md = brief.render(
        today=date(2026, 5, 9), leads=leads, linkedin=[], pending=[],
        pipelines_run=["revops", "reddit_mine"], pipelines_skipped=[], pipelines_failed=[],
    )
    hot_idx = md.index("hot1")
    warm_idx = md.index("warm1")
    auth_idx = md.index("auth1")
    assert hot_idx < warm_idx < auth_idx


def test_render_includes_pending_outcome_checkboxes():
    pending = [{"source": "revops", "post_id": "p1", "posted_at": "2026-05-01T12:00:00"}]
    md = brief.render(
        today=date(2026, 5, 9), leads=[], linkedin=[], pending=pending,
        pipelines_run=[], pipelines_skipped=[], pipelines_failed=[],
    )
    assert "Pending outcomes" in md
    assert "p1" in md
    assert "[ ] responded" in md
    assert "[ ] dmd_back" in md
    assert "[ ] ghosted" in md
    assert "[ ] client" in md
    assert "[ ] unsub" in md


def test_render_zero_state_is_explicit():
    md = brief.render(
        today=date(2026, 5, 9), leads=[], linkedin=[], pending=[],
        pipelines_run=[], pipelines_skipped=[], pipelines_failed=[],
    )
    assert "No new leads today" in md


def test_render_includes_linkedin_section():
    linkedin = [
        {"name": "Sarah Chen", "title": "VP RevOps", "company": "Acme", "opener": "Saw your post."},
    ]
    md = brief.render(
        today=date(2026, 5, 9), leads=[], linkedin=linkedin, pending=[],
        pipelines_run=["linkedin"], pipelines_skipped=[], pipelines_failed=[],
    )
    assert "LinkedIn" in md
    assert "Sarah Chen" in md
    assert "VP RevOps" in md
    assert "Saw your post." in md


def test_no_em_dashes_in_rendered_brief():
    md = brief.render(
        today=date(2026, 5, 9), leads=[], linkedin=[], pending=[],
        pipelines_run=[], pipelines_skipped=[], pipelines_failed=[],
    )
    assert "—" not in md, "voice rule violation: em-dash in brief"
