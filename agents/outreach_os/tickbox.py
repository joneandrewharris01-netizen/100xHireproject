"""Parse outcome tickboxes from a Daily Brief markdown."""
from __future__ import annotations

import re

_LEAD_RE = re.compile(
    r"- \[ \] `(?P<post_id>[^`]+)` \((?P<source>revops|pe|reddit_mine)\) posted [^\n]+\n"
    r"\s+(?P<options>.*)"
)
_OUTCOME_RE = re.compile(r"\[(?P<mark>[ x])\]\s*(?P<name>responded|dmd_back|ghosted|client|unsub)")


def parse(brief_md: str) -> list[dict]:
    out: list[dict] = []
    for m in _LEAD_RE.finditer(brief_md):
        ticked = []
        for om in _OUTCOME_RE.finditer(m.group("options")):
            if om.group("mark") == "x":
                ticked.append(om.group("name"))
        if not ticked:
            continue
        out.append({
            "post_id": m.group("post_id"),
            "source": m.group("source"),
            "outcome": ticked[0],
            "conflict": len(ticked) > 1,
        })
    return out
