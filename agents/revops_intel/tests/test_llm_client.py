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


# --- complete() tests (Groq SDK mocked) ---


class _FakeGroqResponse:
    def __init__(self, content: str):
        self.choices = [type("C", (), {"message": type("M", (), {"content": content})()})()]


@pytest.fixture
def mock_groq(monkeypatch):
    """Patch llm_client._get_client() to return a controllable mock."""
    calls = []
    responses: list = []

    class _MockClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    calls.append(kwargs)
                    r = responses.pop(0)
                    if isinstance(r, Exception):
                        raise r
                    return r

    monkeypatch.setattr(llm_client, "_get_client", lambda: _MockClient())
    monkeypatch.setattr(llm_client, "_CLIENT", None)  # belt-and-suspenders isolation
    return calls, responses


def test_complete_returns_voice_clean_text(mock_groq, tmp_path, monkeypatch):
    calls, responses = mock_groq
    responses.append(_FakeGroqResponse("This is a game changer — really."))
    monkeypatch.setattr(llm_client, "_VIOLATIONS_LOG", str(tmp_path / "voice.jsonl"))

    out = llm_client.complete("hello")

    assert "game changer" not in out.lower()
    assert "—" not in out
    assert len(calls) == 1


def test_complete_retries_on_429(mock_groq, tmp_path, monkeypatch):
    from groq import RateLimitError

    calls, responses = mock_groq

    fake_err = RateLimitError(
        message="rate limited",
        response=type("R", (), {"status_code": 429, "headers": {}, "request": None})(),
        body=None,
    )
    responses.append(fake_err)
    responses.append(_FakeGroqResponse("recovered"))
    monkeypatch.setattr(llm_client, "_VIOLATIONS_LOG", str(tmp_path / "voice.jsonl"))
    monkeypatch.setattr(llm_client, "_BACKOFF_BASE", 0.01)  # speed up test

    out = llm_client.complete("hello")
    assert out == "recovered"
    assert len(calls) == 2


def test_complete_raises_llm_error_after_max_retries(mock_groq, tmp_path, monkeypatch):
    from groq import RateLimitError

    calls, responses = mock_groq
    fake_err = RateLimitError(
        message="rate limited",
        response=type("R", (), {"status_code": 429, "headers": {}, "request": None})(),
        body=None,
    )
    for _ in range(4):
        responses.append(fake_err)
    monkeypatch.setattr(llm_client, "_VIOLATIONS_LOG", str(tmp_path / "voice.jsonl"))
    monkeypatch.setattr(llm_client, "_BACKOFF_BASE", 0.01)

    with pytest.raises(llm_client.LLMError, match="rate limit"):
        llm_client.complete("hello")
    assert len(calls) == 3  # 3 attempts, then give up


def test_complete_writes_violations_to_log(mock_groq, tmp_path, monkeypatch):
    import json

    calls, responses = mock_groq
    responses.append(_FakeGroqResponse("Total synergy across teams."))
    log_path = tmp_path / "voice.jsonl"
    monkeypatch.setattr(llm_client, "_VIOLATIONS_LOG", str(log_path))

    llm_client.complete("hello", lead_id="post_xyz")

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert any("post_xyz" in line and "guru" in line for line in lines)
    # Each line is valid JSON
    for line in lines:
        json.loads(line)


def test_complete_raises_llm_error_on_empty_choices(mock_groq, tmp_path, monkeypatch):
    calls, responses = mock_groq
    empty_resp = type("R", (), {"choices": []})()
    responses.append(empty_resp)
    monkeypatch.setattr(llm_client, "_VIOLATIONS_LOG", str(tmp_path / "v.jsonl"))
    with pytest.raises(llm_client.LLMError, match="empty choices"):
        llm_client.complete("hello")


def test_complete_retries_on_5xx(mock_groq, tmp_path, monkeypatch):
    from groq import APIStatusError

    calls, responses = mock_groq
    # Build a faux 503 — APIStatusError needs (message, response, body)
    fake_resp = type("R", (), {"status_code": 503, "headers": {}, "request": None})()
    fake_err = APIStatusError(message="upstream 503", response=fake_resp, body=None)
    responses.append(fake_err)
    responses.append(_FakeGroqResponse("recovered after 503"))
    monkeypatch.setattr(llm_client, "_VIOLATIONS_LOG", str(tmp_path / "v.jsonl"))
    monkeypatch.setattr(llm_client, "_BACKOFF_BASE", 0.01)

    out = llm_client.complete("hello")
    assert out == "recovered after 503"
    assert len(calls) == 2


def test_complete_raises_on_4xx_without_retry(mock_groq, tmp_path, monkeypatch):
    from groq import APIStatusError

    calls, responses = mock_groq
    fake_resp = type("R", (), {"status_code": 400, "headers": {}, "request": None})()
    fake_err = APIStatusError(message="bad request", response=fake_resp, body=None)
    responses.append(fake_err)
    monkeypatch.setattr(llm_client, "_VIOLATIONS_LOG", str(tmp_path / "v.jsonl"))

    with pytest.raises(llm_client.LLMError, match="400"):
        llm_client.complete("hello")
    assert len(calls) == 1  # no retry on 4xx


def test_complete_retries_on_connection_error(mock_groq, tmp_path, monkeypatch):
    from groq import APIConnectionError

    calls, responses = mock_groq
    # APIConnectionError signature varies by SDK version. Try the common form.
    try:
        fake_err = APIConnectionError(request=type("Req", (), {})())
    except TypeError:
        fake_err = APIConnectionError(message="network")
    responses.append(fake_err)
    responses.append(_FakeGroqResponse("recovered after network blip"))
    monkeypatch.setattr(llm_client, "_VIOLATIONS_LOG", str(tmp_path / "v.jsonl"))
    monkeypatch.setattr(llm_client, "_BACKOFF_BASE", 0.01)

    out = llm_client.complete("hello")
    assert out == "recovered after network blip"
    assert len(calls) == 2
