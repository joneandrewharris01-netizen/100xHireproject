"""Compute win rate (clients / sent) per source."""
from __future__ import annotations


def compute(counts: dict[str, int]) -> float | None:
    sent = counts.get("sent", 0)
    if sent == 0:
        return None
    return counts.get("client", 0) / sent
