from unittest.mock import MagicMock

from agents.outreach_os import opener


def test_calls_gemini_and_returns_stripped_text(monkeypatch):
    fake_response = MagicMock()
    fake_response.text = "Saw your post about Salesforce reporting hell."
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert out == "Saw your post about Salesforce reporting hell."
    assert fake_client.models.generate_content.called
    kwargs = fake_client.models.generate_content.call_args.kwargs
    assert "gemini" in kwargs["model"]


def test_strips_em_dashes_from_response(monkeypatch):
    fake_response = MagicMock()
    fake_response.text = "Hey Sarah — thought this might help."
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert "—" not in out


def test_handles_empty_response(monkeypatch):
    fake_response = MagicMock()
    fake_response.text = None
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert out == ""
