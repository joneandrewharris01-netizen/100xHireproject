"""Sort ICP-matching titles to the front of the rotation."""
from __future__ import annotations

import json
from pathlib import Path

_KEYWORDS = json.loads((Path(__file__).parent / "config.json").read_text())["icp_title_keywords"]


def is_icp(title: str) -> bool:
    t = (title or "").lower()
    return any(kw in t for kw in _KEYWORDS)


def bump(rows: list[dict]) -> list[dict]:
    icp = [r for r in rows if is_icp(r.get("title", ""))]
    rest = [r for r in rows if not is_icp(r.get("title", ""))]
    return icp + rest
