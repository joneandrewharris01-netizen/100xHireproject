from agents.outreach_os import frontmatter


def test_parse_basic():
    text = """---
post_id: abc123
score: 92
tier: HOT
---

## Body
Some content here.
"""
    fm, body = frontmatter.parse(text)
    assert fm["post_id"] == "abc123"
    assert fm["score"] == 92
    assert fm["tier"] == "HOT"
    assert "Body" in body


def test_parse_no_frontmatter_returns_empty_dict_and_full_body():
    text = "## Just a heading\nbody content"
    fm, body = frontmatter.parse(text)
    assert fm == {}
    assert body == text


def test_parse_malformed_frontmatter_returns_empty_dict():
    text = "---\nnot: valid: yaml: here:\n---\nbody"
    fm, body = frontmatter.parse(text)
    assert fm == {}


def test_parse_handles_lists_and_nested():
    text = """---
reasons: [low_reply_rate, hiring_freeze]
totals:
  hot: 3
  warm: 5
---
"""
    fm, _ = frontmatter.parse(text)
    assert fm["reasons"] == ["low_reply_rate", "hiring_freeze"]
    assert fm["totals"] == {"hot": 3, "warm": 5}
