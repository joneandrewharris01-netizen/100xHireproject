from agents.outreach_os import icp_bump


def test_bumps_revops_title_to_front():
    rows = [
        {"name": "A", "title": "Marketing Lead"},
        {"name": "B", "title": "VP RevOps"},
        {"name": "C", "title": "Engineering Manager"},
        {"name": "D", "title": "Head of Sales Ops"},
    ]
    out = icp_bump.bump(rows)
    assert [r["name"] for r in out[:2]] == ["B", "D"]


def test_preserves_order_within_groups():
    rows = [
        {"name": "A", "title": "Marketing Lead"},
        {"name": "B", "title": "Engineering Manager"},
        {"name": "C", "title": "VP RevOps"},
    ]
    out = icp_bump.bump(rows)
    assert [r["name"] for r in out] == ["C", "A", "B"]


def test_case_insensitive():
    rows = [{"name": "X", "title": "vp REVOPS"}]
    assert icp_bump.bump(rows)[0]["name"] == "X"
