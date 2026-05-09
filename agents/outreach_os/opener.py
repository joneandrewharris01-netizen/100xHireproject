"""Generate one LinkedIn opener via Gemini 2.0 Flash.

Uses the free Google AI Studio API. Reads GEMINI_API_KEY from process env or
the project root .env file. The previous Anthropic Haiku implementation was
swapped to Gemini because the user has no Anthropic API key.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

_MODEL = "gemini-2.5-flash-lite"
_SYSTEM = (
    "You write one-line LinkedIn DM openers that sound like a peer, not a guru. "
    "The sender is Jone Andrew Harris, an automation freelancer who builds outbound systems "
    "for B2B SaaS RevOps teams (Seed to Series B). "
    "Hard rules: no em-dashes, no emoji, no compliments, no hyperbole, no placeholders like "
    "[Name] or [Title] or [Company]. Use ONLY the data provided. If you don't know the "
    "person's role, write a brief connection-request opener that grounds itself in Jone's "
    "offer (helping B2B SaaS founders / RevOps teams ship outbound that actually replies) "
    "WITHOUT pretending to know their role. "
    "Output exactly one sentence under 25 words. Sound like a peer."
)

# Walk up from this file to find the project root .env (adjacent to pytest.ini /
# .git). Loading at import time is fine because dotenv is a no-op if no file
# exists, and tests monkeypatch _client() directly so this never blocks them.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")

_CACHED_CLIENT: genai.Client | None = None


def _client() -> genai.Client:
    """Cached Client. The genai SDK's internal httpx pool closes if the client
    instance is garbage-collected mid-request, so we hold a single reference."""
    global _CACHED_CLIENT
    if _CACHED_CLIENT is None:
        _CACHED_CLIENT = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    return _CACHED_CLIENT


def generate(lead: dict) -> str:
    """Generate an opener using whatever fields the lead has.

    Recognized keys (any subset): name, first_name, title, company, headline, profile_url.
    Empty / missing fields are omitted from the prompt so Gemini never inserts placeholders.
    """
    name = lead.get("name") or lead.get("first_name") or "the person"
    fields = [f"Name: {name}"]
    for key, label in (("title", "Title"), ("company", "Company"), ("headline", "Headline")):
        val = (lead.get(key) or "").strip()
        if val:
            fields.append(f"{label}: {val}")
    fields.append("Write the opener now using ONLY the fields above. Never include placeholder tokens.")
    user_msg = "\n".join(fields)

    client = _client()
    resp = client.models.generate_content(
        model=_MODEL,
        contents=user_msg,
        config={"system_instruction": _SYSTEM, "max_output_tokens": 80, "temperature": 0.7},
    )
    text = (resp.text or "").strip()
    return text.replace("—", ",").replace("--", ",")
