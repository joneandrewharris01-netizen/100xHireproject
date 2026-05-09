from unittest.mock import MagicMock

from agents.outreach_os import opener


def test_calls_haiku_and_returns_stripped_text(monkeypatch):
    fake_message = MagicMock()
    fake_message.content = [MagicMock(text="Saw your post about Salesforce reporting hell.")]
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_message

    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert out == "Saw your post about Salesforce reporting hell."
    assert fake_client.messages.create.called
    kwargs = fake_client.messages.create.call_args.kwargs
    assert "haiku" in kwargs["model"]


def test_strips_em_dashes_from_response(monkeypatch):
    fake_message = MagicMock()
    fake_message.content = [MagicMock(text="Hey Sarah - thought this might help.")]
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_message

    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert "—" not in out
