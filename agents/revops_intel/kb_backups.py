"""KB JSON backup/restore for the standalone pipeline.

Snapshot all 4 KB files at run start. Keep last 7 per file. On corrupt
read, callers use restore_latest(name) to read the most recent valid copy.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path


_KB_DIR = Path(__file__).parent / "knowledge_base"
_BACKUP_DIR = _KB_DIR / ".backups"
_RETENTION = 7
_FILES = ("tools", "pains", "personas", "jargon", "offers")


def _TIMESTAMP_FN() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")


def snapshot() -> None:
    """Copy all 4 KB JSON files into .backups/ with a timestamp prefix."""
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = _TIMESTAMP_FN()
    for name in _FILES:
        src = _KB_DIR / f"{name}.json"
        if not src.exists():
            continue
        dst = _BACKUP_DIR / f"{ts}_{name}.json.bak"
        shutil.copy2(src, dst)
    _prune()


def _prune() -> None:
    for name in _FILES:
        backups = sorted(_BACKUP_DIR.glob(f"*_{name}.json.bak"))
        for old in backups[:-_RETENTION]:
            old.unlink(missing_ok=True)


def restore_latest(name: str) -> str:
    """Return the contents of the most recent backup of `name` as a string."""
    backups = sorted(_BACKUP_DIR.glob(f"*_{name}.json.bak"))
    if not backups:
        raise FileNotFoundError(f"no backups for {name}")
    return backups[-1].read_text(encoding="utf-8")
