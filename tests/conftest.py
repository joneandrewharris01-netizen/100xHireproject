"""Shared pytest fixtures for the Outreach OS test suite."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture()
def tmp_repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A throwaway repo root with the directory layout aggregate.py expects."""
    for sub in [
        "agents/revops_intel/queue",
        "agents/pe_intel/queue",
        "agents/reddit_mine/queue",
        "agents/outreach_os/linkedin",
        "outreach-os/daily",
        "linkedin-content",
    ]:
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    yield tmp_path


@pytest.fixture()
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
