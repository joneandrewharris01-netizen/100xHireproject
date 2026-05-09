"""Generate one LinkedIn opener via Haiku 4.5."""
from __future__ import annotations

import os

import anthropic

_MODEL = "claude-haiku-4-5-20251001"
_SYSTEM = (
    "You write one-line LinkedIn DM openers that sound like a peer, not a guru. "
    "Hard rules: no em-dashes, no emoji, no compliments, no hyperbole. "
    "Reference the person's role specifically. Output exactly one sentence under 25 words."
)


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def generate(lead: dict) -> str:
    user_msg = (
        f"Name: {lead.get('name', '')}\n"
        f"Title: {lead.get('title', '')}\n"
        f"Company: {lead.get('company', '')}\n\n"
        "Write the opener."
    )
    resp = _client().messages.create(
        model=_MODEL,
        max_tokens=80,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()
    return text.replace("—", ",").replace("--", ",")
