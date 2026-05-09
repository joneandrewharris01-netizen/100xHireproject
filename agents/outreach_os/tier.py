"""Tier derivation per spec section 'Tier derivation rules'."""
from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "config.json"
_DEFAULT_THRESHOLDS = json.loads(_CONFIG_PATH.read_text())["tier_thresholds"]


def score_to_tier(score: int, thresholds: dict | None = None) -> str | None:
    """Map a numeric score to HOT / WARM / AUTHORITY / None."""
    t = thresholds or _DEFAULT_THRESHOLDS
    if score >= t["hot_min_score"]:
        return "HOT"
    if score >= t["warm_min_score"]:
        return "WARM"
    if score >= t["authority_min_score"]:
        return "AUTHORITY"
    return None


def derive(source: str, frontmatter: dict, thresholds: dict | None = None) -> str | None:
    """Derive the unified tier for a queue file based on its source."""
    # Pipelines that already classify in their queue frontmatter use it directly.
    if source in {"reddit_mine", "vc_pain_analysis"}:
        return frontmatter.get("tier")
    # DB-scored pipelines (revops, pe) provide a numeric score; map to tier.
    if source in {"revops", "pe"}:
        return score_to_tier(int(frontmatter.get("score", 0)), thresholds)
    raise ValueError(f"unknown source: {source}")
