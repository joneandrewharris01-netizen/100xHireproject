import pytest

from agents.pe_intel import classify


def make(title="", body=""):
    return {"title": title, "selftext": body}


# --- problem_category ---

def test_classifies_ai_infra():
    r = classify.classify(make("Building AI infra at our PE firm",
                               "Using Claude Team plan for NDA review"))
    assert r["problem_category"] == "ai_infra"


def test_classifies_portfolio_reporting():
    r = classify.classify(make("Portfolio Reporting Solutions",
                               "evaluating Chronograph and 73 Strings"))
    assert r["problem_category"] == "portfolio_reporting"


def test_classifies_automation():
    r = classify.classify(make("Automating my outreach with n8n",
                               "I want to use n8n to automate workflow"))
    assert r["problem_category"] == "automation"


def test_classifies_capital():
    r = classify.classify(make("Family office introductions",
                               "Looking for SFO and MFO connections"))
    assert r["problem_category"] == "capital"


def test_classifies_gtm():
    r = classify.classify(make("Need help with cold email outbound",
                               "Setting up an SDR pipeline"))
    assert r["problem_category"] == "gtm"


def test_classifies_other():
    r = classify.classify(make("Best Minecraft server settings",
                               "Java + Bedrock no grief no reset"))
    assert r["problem_category"] == "other"


# --- firm_size_signal ---

def test_size_smb():
    r = classify.classify(make("question", "I'm at a small business doing X"))
    assert r["firm_size_signal"] == "smb"


def test_size_mid():
    r = classify.classify(make("Eval", "We are a $3-5B AUM fund"))
    assert r["firm_size_signal"] == "mid"


def test_size_enterprise():
    r = classify.classify(make("F500 question", "Working at a Fortune 500"))
    assert r["firm_size_signal"] == "enterprise"


def test_size_solo():
    r = classify.classify(make("solopreneur help",
                               "I'm a solo founder freelance"))
    assert r["firm_size_signal"] == "solo"


def test_size_unknown_fallback():
    r = classify.classify(make("anything", "no size signals here"))
    assert r["firm_size_signal"] == "unknown"


# --- fit_for_jone ---

def test_fit_high_smb_automation():
    r = classify.classify(make("automating my small business",
                               "small business needs n8n"))
    assert r["fit_for_jone"] == "high"


def test_fit_low_enterprise():
    r = classify.classify(make("F500 automation",
                               "Fortune 500 firm needs n8n setup"))
    assert r["fit_for_jone"] == "low"


def test_fit_low_capital_always():
    """Capital raise / family offices are always low fit (Tier 3 territory)."""
    r = classify.classify(make("Need LP introductions",
                               "Looking for family office connections"))
    assert r["fit_for_jone"] == "low"


def test_fit_low_portfolio_reporting():
    """Portfolio reporting (Chronograph et al) is Tier 3 — vendor refers."""
    r = classify.classify(make("Chronograph eval",
                               "evaluating Chronograph and 73 Strings"))
    assert r["fit_for_jone"] == "low"


def test_fit_med_mid_market_automation():
    r = classify.classify(make("automation help",
                               "We are a $3-5B AUM fund needing automation"))
    assert r["fit_for_jone"] == "med"


# --- structure ---

def test_returns_all_three_keys():
    r = classify.classify(make("anything", ""))
    assert set(r.keys()) == {"problem_category", "firm_size_signal", "fit_for_jone"}
