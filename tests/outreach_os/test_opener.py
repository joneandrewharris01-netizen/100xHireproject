from unittest.mock import MagicMock

from agents.outreach_os import opener


def _fake_groq_response(text: str) -> MagicMock:
    fake = MagicMock()
    fake.choices = [MagicMock()]
    fake.choices[0].message.content = text
    return fake


def test_calls_groq_and_returns_text(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_groq_response(
        "Saw your post about Salesforce reporting hell."
    )
    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert out == "Saw your post about Salesforce reporting hell."
    kwargs = fake_client.chat.completions.create.call_args.kwargs
    assert "llama" in kwargs["model"].lower()


def test_strips_em_dashes_from_response(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_groq_response(
        "Hey Sarah — thought this might help."
    )
    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert "—" not in out


def test_strips_outer_quotes(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_groq_response(
        '"Hey Sarah, building outbound for B2B SaaS is my focus."'
    )
    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah"})
    assert not out.startswith('"')
    assert not out.endswith('"')


def test_handles_empty_response(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = _fake_groq_response(None)
    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert out == ""
