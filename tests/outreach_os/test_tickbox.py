from agents.outreach_os import tickbox


_BRIEF = """
## Pending outcomes (>7 days old)
- [ ] `post1` (revops) posted 2026-05-01T12:00:00
  - [x] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub
- [ ] `post2` (pe) posted 2026-05-01T12:00:00
  - [ ] responded   [ ] dmd_back   [x] ghosted   [ ] client   [ ] unsub
- [ ] `post3` (reddit_mine) posted 2026-05-01T12:00:00
  - [ ] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub
- [ ] `post4` (revops) posted 2026-05-01T12:00:00
  - [x] responded   [x] ghosted   [ ] dmd_back   [ ] client   [ ] unsub

## HOT
nothing here
"""


def test_extracts_ticked_outcomes():
    items = tickbox.parse(_BRIEF)
    by_id = {i["post_id"]: i for i in items}
    assert by_id["post1"]["source"] == "revops"
    assert by_id["post1"]["outcome"] == "responded"
    assert by_id["post2"]["outcome"] == "ghosted"


def test_skips_untagged():
    items = tickbox.parse(_BRIEF)
    ids = {i["post_id"] for i in items}
    assert "post3" not in ids


def test_flags_conflicts():
    items = tickbox.parse(_BRIEF)
    by_id = {i["post_id"]: i for i in items}
    assert by_id["post4"]["conflict"] is True


def test_ignores_unrelated_checkboxes():
    text = """
## HOT
- [ ] Post comment + send DM. Queue file: `q.md`
"""
    items = tickbox.parse(text)
    assert items == []
