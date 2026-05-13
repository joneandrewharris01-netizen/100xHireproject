"""Atomic KB merge for the standalone pipeline.

For each top-level key in the diff (tools/pains/personas/jargon):
1. Read the corresponding JSON file fresh from disk
2. Merge the diff into it (per-entry rules below)
3. Write atomically: write to .tmp, fsync, rename over the original

Per-entry merge rules:
- mention_count / frequency: sum
- example_quotes / common_complaints / common_praise / etc.: extend, dedupe
- All other scalar fields: diff wins (newer data is more accurate)
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


_KB_DIR = Path(__file__).parent / "knowledge_base"
_ALLOWED = ("tools", "pains", "personas", "jargon")

_COUNT_KEYS = {"mention_count", "frequency"}
_LIST_KEYS = {
    "example_quotes", "common_complaints", "common_praise",
    "title_variants", "firm_size_signals", "language_markers",
    "common_pains", "personas_affected", "current_workarounds",
}


def _merge_entry(existing: dict, new: dict) -> dict:
    out = dict(existing)
    for k, v in new.items():
        if k in _COUNT_KEYS:
            out[k] = int(existing.get(k, 0)) + int(v)
        elif k in _LIST_KEYS:
            merged = list(existing.get(k, []))
            for item in v:
                if item not in merged:
                    merged.append(item)
            out[k] = merged
        else:
            out[k] = v
    return out


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def merge_atomic(diff: dict) -> None:
    """Apply the KB diff to the four KB JSON files. One file at a time."""
    for key in _ALLOWED:
        section = diff.get(key)
        if not section:
            continue
        path = _KB_DIR / f"{key}.json"
        current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        for entry_key, entry_diff in section.items():
            current[entry_key] = _merge_entry(current.get(entry_key, {}), entry_diff)
        _atomic_write(path, current)
