"""Unit tests for llm_client.

The Groq SDK is mocked via pytest-mock — no real API calls. Tests cover:
- API key loading from .env
- LLMError raised when key missing
- GURU_REPLACEMENTS lookup table shape
"""
from __future__ import annotations

import pytest

from agents.revops_intel import llm_client


def test_llm_error_is_exception():
    assert issubclass(llm_client.LLMError, Exception)


def test_guru_replacements_has_expected_keys():
    table = llm_client.GURU_REPLACEMENTS
    expected = {
        "game changer", "game-changer", "10x", "level up",
        "crushing it", "move the needle", "deep dive",
        "low-hanging fruit", "synergy",
    }
    assert expected <= set(table.keys())
    assert all(isinstance(v, str) for v in table.values())
    assert "leverage" not in table  # intentionally excluded (verb/noun ambiguity)


def test_load_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(llm_client, "_DOTENV_PATH", "/nonexistent/.env")
    with pytest.raises(llm_client.LLMError, match="GROQ_API_KEY"):
        llm_client._load_api_key()


def test_load_api_key_returns_env_value(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")
    assert llm_client._load_api_key() == "test-key-123"
