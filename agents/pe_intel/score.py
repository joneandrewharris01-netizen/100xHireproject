"""Heuristic lead scoring.

Pure: score_post(dict) -> (int, list[str]). Driver: apply_to_db rescores
every post in the DB. Cheap, runs in milliseconds for thousands of posts.

Keyword lists are checked via word-boundary regexes (not substring) so
"into PE" matches "...transition into PE." but not "intoxicated person".
"""
from __future__ import annotations

import re

from . import db


# Substring-OK keywords (multi-word phrases — substring is fine)
VENDOR_PHRASES = [
    "evaluating", "looking for", "alternatives to", "anyone using",
    "experiences with", "vendor", "better than", "recommendations",
]
PAIN_PHRASES = [
    "manual process", "automate", "automating", "struggling with",
    "headache", "wasting time", "scaling",
]
BUILD_PHRASES = [
    "rolling out", "implementing", "ai-first",
    "infrastructure", "set up", "setting up",
]
AUTOMATION_PHRASES = [
    "claude", "chatgpt", "openai", "automation", "workflow",
    "n8n", "make.com", "zapier", "copilot", "pitchbook",
    "chronograph", "preqin", "73 strings",
]
CAREER_PHRASES = [
    "breaking into", "career advice", "internship", "interview prep",
    "resume", "cv review", "what college", "career in",
    "looking for material", "transition into pe", "transition to pe",
]

# Word-boundary regexes (where substring would be wrong)
BUILDING_RX = re.compile(r"\bbuilding\b", re.I)
MANUAL_RX = re.compile(r"\bmanual\b", re.I)
AI_RX = re.compile(r"\bai\b", re.I)  # avoid "main", "available", etc
VS_RX = re.compile(r"\bvs\b\.?", re.I)
MBA_RX = re.compile(r"\bmba\b", re.I)
INTO_PE_RX = re.compile(r"\binto pe\b", re.I)

DECISION_RX = re.compile(
    r"\bi'?m\s+an?\s+(operating|partner|principal|vp|director|cfo|"
    r"head of|founder|managing|senior)",
    re.I,
)
FIRM_RX = re.compile(r"\bour firm\b|\bwe'?re a\b|\bat our fund\b", re.I)


def _has_phrase(text: str, phrases: list[str]) -> bool:
    return any(p in text for p in phrases)


def score_post(post: dict) -> tuple[int, list[str]]:
    title = (post.get("title") or "").lower()
    body = (post.get("selftext") or "").lower()
    blob = f"{title}\n{body}"

    points = 0
    reasons: list[str] = []

    if _has_phrase(blob, VENDOR_PHRASES) or VS_RX.search(blob):
        points += 25
        reasons.append("vendor_evaluation")
    if _has_phrase(blob, PAIN_PHRASES) or MANUAL_RX.search(blob):
        points += 20
        reasons.append("pain_point")
    if _has_phrase(blob, BUILD_PHRASES) or BUILDING_RX.search(blob):
        points += 25
        reasons.append("active_build")
    if DECISION_RX.search(post.get("selftext") or ""):
        points += 20
        reasons.append("decision_maker_signal")
    if FIRM_RX.search(post.get("selftext") or ""):
        points += 10
        reasons.append("speaks_for_firm")
    if _has_phrase(blob, AUTOMATION_PHRASES) or AI_RX.search(blob):
        points += 15
        reasons.append("automation_relevant")

    nc = post.get("num_comments", 0) or 0
    rs = post.get("score", 0) or 0
    if nc >= 10 and rs >= 5:
        points += 10
        reasons.append("active_thread")
    if nc >= 25:
        points += 5
        reasons.append("hot_thread")

    if (_has_phrase(title, CAREER_PHRASES) or
            MBA_RX.search(title) or INTO_PE_RX.search(title)):
        points -= 40
        reasons.append("career_question_penalty")

    points = max(0, min(100, points))
    return points, reasons


def apply_to_db(conn) -> dict:
    """Re-score every post in the DB. Returns {scored, hot}."""
    rows = conn.execute(
        "SELECT post_id, title, selftext, score, num_comments FROM posts"
    ).fetchall()
    hot = 0
    for r in rows:
        pts, reasons = score_post(dict(r))
        db.upsert_lead_score(conn, r["post_id"], pts, reasons)
        if pts >= db.HOT_THRESHOLD:
            hot += 1
    return {"scored": len(rows), "hot": hot}


def main() -> int:
    conn = db.connect()
    db.init_schema(conn)
    stats = apply_to_db(conn)
    print(f"DONE: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
