"""Groq SDK wrapper for the RevOps Intel standalone pipeline.

This is the single file that knows Groq exists. All other modules call
`complete(prompt)` and get voice-clean text or LLMError.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


_DOTENV_PATH = str(Path(__file__).parent / ".env")


class LLMError(Exception):
    """Raised for any unrecoverable LLM-side failure (auth, network, bad response)."""


GURU_REPLACEMENTS: dict[str, str] = {
    "game changer": "big shift",
    "game-changer": "big shift",
    "10x": "a lot more",
    "level up": "improve",
    "crushing it": "doing well",
    "move the needle": "matter",
    "deep dive": "look at",
    "low-hanging fruit": "quick win",
    "synergy": "",
}


def _load_api_key() -> str:
    """Load GROQ_API_KEY from environment or agents/revops_intel/.env."""
    load_dotenv(_DOTENV_PATH, override=False)
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise LLMError(
            "GROQ_API_KEY not set. Copy .env.example to .env and add your key "
            "from https://console.groq.com/keys"
        )
    return key
