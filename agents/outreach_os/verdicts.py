"""Auto-generate 'What's working / What's not' verdicts."""
from __future__ import annotations


def generate(rates: dict[str, float | None]) -> dict[str, list[str]]:
    valid = [(s, r) for s, r in rates.items() if r is not None]
    if not valid:
        return {"working": ["No data yet."], "not_working": []}
    valid.sort(key=lambda x: x[1], reverse=True)
    best_source, best_rate = valid[0]
    worst_source, worst_rate = valid[-1]
    working = [f"{best_source} leads with a {best_rate * 100:.1f}% win rate. Lean into it."]
    not_working: list[str] = []
    if worst_rate < 0.005 and worst_source != best_source:
        not_working.append(f"{worst_source} is at {worst_rate * 100:.1f}%. Kill or rework after day 30.")
    return {"working": working, "not_working": not_working or ["Nothing flagged for cuts yet."]}
