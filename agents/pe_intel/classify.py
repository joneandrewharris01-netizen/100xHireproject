"""Heuristic lead classifier.

Pure function. classify(post) -> dict with:
  - problem_category: one of CATEGORIES
  - firm_size_signal: one of FIRM_SIZES
  - fit_for_jone: 'high' | 'med' | 'low'

Used by route.py to decide which tier (Jone delivers / broker / affiliate).
"""
from __future__ import annotations

import re

CATEGORIES = [
    "gtm",                 # outbound, lead gen, SDR, cold email, pipeline
    "automation",          # n8n, Make, Zapier, workflow automation
    "portfolio_reporting", # Chronograph, 73 Strings, fund admin, LP reporting
    "ai_infra",            # Claude, LLM, AI-first infrastructure, RAG
    "crm",                 # HubSpot, GoHighLevel, Salesforce migrations
    "hiring",              # VAs, offshore staffing, recruiting
    "capital",             # family office, LPs, fundraising, raise capital
    "other",
]

FIRM_SIZES = ["solo", "smb", "mid", "enterprise", "unknown"]

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "gtm": [
        "outbound", "lead gen", "lead generation", "sdr", "cold email",
        "cold call", "pipeline", "prospecting", "appointment setting",
        "demand gen", "go-to-market", "go to market", "gtm",
    ],
    "automation": [
        "n8n", "make.com", "zapier", "automation", "automate",
        "automating", "automated", "workflow", "no-code", "low-code",
    ],
    "portfolio_reporting": [
        # Strong signals: specific products + explicit reporting language
        "chronograph", "73 strings", "carta", "allvue", "juniper square",
        "portfolio reporting", "fund admin", "lp reporting",
        # Weak signals (peer fund, performance data) intentionally excluded —
        # they're context, not buy signals. A research analyst frustrated with
        # manual LP doc extraction is automation, not portfolio_reporting.
    ],
    "ai_infra": [
        "claude", "openai api", "llm", "rag", "ai-first", "ai first",
        "ai infrastructure", "ai infra", "anthropic", "gpt-4 api",
        "vector database", "embeddings",
    ],
    "crm": [
        "hubspot", "gohighlevel", "ghl", "salesforce migration",
        "salesforce setup", "pipedrive", "zoho crm", "crm setup",
        "crm migration",
    ],
    "hiring": [
        "virtual assistant", " va ", "offshore staffing", "hire",
        "recruiter", "recruiting", "headhunter", "staffing",
    ],
    "capital": [
        "family office", "single family office", "multi family office",
        "sfo", "mfo", "fundraise", "raise capital", "lp introduction",
        "lp intros", "limited partner", "anchor investor",
    ],
}

FIRM_SIZE_PATTERNS: dict[str, list[str]] = {
    "solo": [
        "solo founder", "one-person", "one person", "freelance",
        "indie hacker", "solopreneur", "just me",
    ],
    "smb": [
        "small business", "smb", "lower middle market", "lmm",
        "small firm", "small fund", "small pe", "small private equity",
        "boutique", "early stage", "startup",
    ],
    "mid": [
        "mid-market", "mid market", "$1b aum", "$2b aum", "$3b aum",
        "$3-5b", "$5b aum", "$5-10b", "100 employees", "200 employees",
        "growing firm",
    ],
    "enterprise": [
        "fortune 500", "f500", "fortune 100", "f100", "$10b",
        "$50b", "fortune 1000", "global firm", "multinational",
    ],
}

# Compile regexes once
_CATEGORY_RX = {
    cat: re.compile(r"|".join(re.escape(kw) for kw in kws), re.I)
    for cat, kws in CATEGORY_KEYWORDS.items()
}
_FIRM_RX = {
    size: re.compile(r"|".join(re.escape(p) for p in patterns), re.I)
    for size, patterns in FIRM_SIZE_PATTERNS.items()
}


def classify(post: dict) -> dict:
    """post needs at least 'title' and 'selftext' keys (selftext can be empty)."""
    blob = f"{post.get('title') or ''}\n{post.get('selftext') or ''}"

    # Score each category by match count, pick highest
    cat_scores: dict[str, int] = {}
    for cat, rx in _CATEGORY_RX.items():
        n = len(rx.findall(blob))
        if n:
            cat_scores[cat] = n
    problem_category = max(cat_scores, key=cat_scores.get) if cat_scores else "other"

    # Firm size: highest specificity wins (enterprise > mid > smb > solo)
    firm_size = "unknown"
    for size in ("enterprise", "mid", "smb", "solo"):
        if _FIRM_RX[size].search(blob):
            firm_size = size
            break

    fit = _fit_for_jone(problem_category, firm_size)

    return {
        "problem_category": problem_category,
        "firm_size_signal": firm_size,
        "fit_for_jone": fit,
    }


def _fit_for_jone(category: str, firm_size: str) -> str:
    """Jone is most credible at SMB and lower-mid-market for automation/GTM/CRM.

    high: smb + (automation OR gtm OR crm OR ai_infra)
    med:  solo + (any tech category) | smb + other tech | unknown size + tech
    low:  enterprise + anything (broker via Tier 2)
    low:  capital/hiring/portfolio_reporting (Tier 3 territory)
    """
    if category in ("capital", "hiring", "portfolio_reporting"):
        return "low"  # not Jone's wheelhouse — affiliate/refer

    if firm_size == "enterprise":
        return "low"  # too big for Jone alone — broker

    if firm_size == "mid" and category in ("automation", "gtm", "crm", "ai_infra"):
        return "med"  # borderline — may need a partner front

    if firm_size == "smb" and category in ("automation", "gtm", "crm", "ai_infra"):
        return "high"

    if firm_size == "solo" and category in ("automation", "gtm", "crm", "ai_infra"):
        return "med"

    if category in ("automation", "gtm", "crm", "ai_infra"):
        return "med"  # unknown size + tech category

    return "low"  # other / weak signal
