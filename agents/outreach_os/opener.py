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
    "Hard rules: no em-dashes, no emoji, no compliments, no hyperbole. "
    "Reference the person's role specifically. Output exactly one sentence under 25 words."
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
    user_msg = (
        f"Name: {lead.get('name', '')}\n"
        f"Title: {lead.get('title', '')}\n"
        f"Company: {lead.get('company', '')}\n\n"
        "Write the opener."
    )
    client = _client()
    resp = client.models.generate_content(
        model=_MODEL,
        contents=user_msg,
        config={"system_instruction": _SYSTEM, "max_output_tokens": 80, "temperature": 0.7},
    )
    text = (resp.text or "").strip()
    return text.replace("—", ",").replace("--", ",")
