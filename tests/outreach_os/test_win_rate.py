from agents.outreach_os import win_rate


def test_zero_sent_returns_none():
    counts = {"sent": 0, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 0, "unsubscribed": 0}
    assert win_rate.compute(counts) is None


def test_basic_ratio():
    counts = {"sent": 100, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 2, "unsubscribed": 0}
    assert win_rate.compute(counts) == 0.02
