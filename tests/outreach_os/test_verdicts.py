from agents.outreach_os import verdicts


def test_picks_best_and_worst():
    rates = {"revops": 0.025, "pe": 0.0, "reddit_mine": 0.03, "linkedin": 0.005}
    v = verdicts.generate(rates)
    assert "reddit_mine" in v["working"][0] or "revops" in v["working"][0]
    assert "pe" in v["not_working"][0] or "linkedin" in v["not_working"][0]


def test_skips_none_values():
    rates = {"revops": None, "pe": 0.01, "reddit_mine": 0.02, "linkedin": 0.005}
    v = verdicts.generate(rates)
    flat = "\n".join(v["working"] + v["not_working"])
    assert "revops" not in flat
