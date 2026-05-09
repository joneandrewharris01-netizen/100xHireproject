"""Generate one LinkedIn opener via Groq Llama 3.3 70B.

Uses the free Groq API (~14k req/day on Llama 3.3 70B). Reads GROQ_API_KEY
from process env or the project root .env file. Switched from Gemini after
hitting Gemini's 20-req/day free-tier cap on a single LinkedIn rotator run.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

_MODEL = "llama-3.3-70b-versatile"
_SYSTEM = (
    "You write one-line LinkedIn DM openers that sound like a peer, not a guru. "
    "The sender is Jone Andrew Harris, an automation freelancer who builds outbound systems "
    "for B2B SaaS RevOps teams (Seed to Series B). "
    "Hard rules: no em-dashes, no emoji, no compliments, no hyperbole, no placeholders like "
    "[Name] or [Title] or [Company]. Use ONLY the data provided. If you don't know the "
    "person's role, write a brief connection-request opener that grounds itself in Jone's "
    "offer (helping B2B SaaS founders / RevOps teams ship outbound that actually replies) "
    "WITHOUT pretending to know their role. "
    "Output exactly one sentence under 25 words. Sound like a peer. "
    "Output ONLY the opener sentence, no preamble, no quotation marks, no labels."
)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")

_CACHED_CLIENT: Groq | None = None


def _client() -> Groq:
    global _CACHED_CLIENT
    if _CACHED_CLIENT is None:
        _CACHED_CLIENT = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    return _CACHED_CLIENT


def generate(lead: dict) -> str:
    """Generate an opener using whatever fields the lead has.

    Recognized keys (any subset): name, first_name, title, company, headline.
    Empty / missing fields are omitted from the prompt so the model never
    inserts placeholder tokens like [Title].
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
    resp = client.chat.completions.create(
        model=_MODEL,
        max_tokens=80,
        temperature=0.7,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )
    text = (resp.choices[0].message.content or "").strip()
    # Strip outer quotes if the model wrapped its answer
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    return text.replace("—", ",").replace("--", ",")
