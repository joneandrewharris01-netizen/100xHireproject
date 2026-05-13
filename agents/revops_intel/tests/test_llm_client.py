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


# --- _enforce_voice tests ---


@pytest.mark.parametrize("raw,expected", [
    ("I did this — and it worked.", "I did this, and it worked."),
    ("I did this — Then it broke.", "I did this. Then it broke."),
    ("Step one – step two.", "Step one, step two."),
    ("Done — ", "Done."),
])
def test_enforce_voice_em_dash(raw, expected):
    out, _ = llm_client._enforce_voice(raw)
    assert out == expected


def test_enforce_voice_strips_emoji():
    raw = "Great work! 🚀🔥 Keep going."
    out, _ = llm_client._enforce_voice(raw)
    assert "🚀" not in out and "🔥" not in out
    assert "Great work!" in out


def test_enforce_voice_strips_smart_quotes_and_typographic():
    raw = 'He said "hello"… → next step • done'
    out, _ = llm_client._enforce_voice(raw)
    assert '"hello"' in out
    assert "..." in out
    assert " to " in out
    assert "- done" in out


def test_enforce_voice_strips_cta_trailer():
    raw = "Here is the answer. Reach out anytime if you want more."
    out, _ = llm_client._enforce_voice(raw)
    assert "Reach out anytime" not in out
    assert out.startswith("Here is the answer")


def test_enforce_voice_ensures_terminal_punct_after_cta_strip():
    """After stripping a trailing CTA, output must still end in . / ! / ?
    so downstream truncation checks don't false-positive."""
    raw = "Useful insight is here. DM me anytime"
    out, _ = llm_client._enforce_voice(raw)
    assert out.rstrip()[-1] in ".!?"


@pytest.mark.parametrize("raw,banned", [
    ("This is a game changer for sales.", "game changer"),
    ("Time to LEVEL UP your outbound.", "level up"),
    ("We saw 10x growth.", "10x"),
    ("Total synergy across teams.", "synergy"),
])
def test_enforce_voice_substitutes_guru_phrases(raw, banned):
    out, violations = llm_client._enforce_voice(raw)
    assert banned.lower() not in out.lower()
    assert any(v["rule"] == "guru" for v in violations)


def test_enforce_voice_preserves_numbers_containing_10x_substring():
    """'10x' substitution must not mangle '210x' or '100x growth'."""
    raw = "We hit 210x growth and 100x revenue."
    out, _ = llm_client._enforce_voice(raw)
    assert "210x" in out
    assert "100x" in out


def test_enforce_voice_returns_violations_for_logging():
    raw = "This is a game changer — really 10x."
    out, violations = llm_client._enforce_voice(raw)
    rules = [v["rule"] for v in violations]
    assert "guru" in rules
    assert "em_dash" in rules
    assert all("before" in v and "after" in v for v in violations)
