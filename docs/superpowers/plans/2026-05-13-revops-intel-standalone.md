# RevOps Intel Standalone Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replicate the `/revops-process` slash command as a standalone Python pipeline driven by free-tier Groq Llama 3.3 70B, producing byte-for-byte-compatible queue files without an interactive Claude Code session.

**Architecture:** Modular. `llm_client.py` is the only file that knows Groq exists (single provider boundary). `llm_extract.py` does KB extraction, `llm_generate.py` does comment+DM drafting. `run.py` is a ~120-line chain runner that wraps the existing Python scrape/score/route subprocesses and loops hot leads serially. Same SQLite DB, same KB JSON files, same queue file format.

**Tech Stack:** Python 3.11, `groq` SDK (free tier API), `python-dotenv`, existing `praw`+`sqlite3` stack, `pytest` + `pytest-mock`.

**Spec:** `docs/superpowers/specs/2026-05-13-revops-intel-standalone-design.md`

---

## Chunk 1: Foundations

Set up environment scaffolding, fixtures, and the one DB helper everything else depends on. After this chunk, `db.fetch_top_comments` works against the real schema with a real test, the fixture lead shape is locked, and the .env / .gitignore plumbing is in place.

**Prerequisites (verify before starting Chunk 1):**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest --version
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "import pytest_mock; print(pytest_mock.__version__)"
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "import dotenv; print(dotenv.__version__)"
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "import groq; print(groq.__version__)"
```

If any import fails: `pip install pytest pytest-mock python-dotenv groq`.

**Shell note:** All `pytest` invocations in this plan use `python -m pytest` from the project root `D:/Projects/my-project/` so that `from agents.revops_intel import ...` imports resolve. POSIX-style commands (`grep`, `test -f`, heredocs) should be run via the Bash tool; PowerShell commands are noted explicitly.

### Task 1.1: Add `.gitignore` entries for secrets and KB backups

**Files:**
- Modify: `D:/Projects/my-project/.gitignore` (append two new lines)

The existing `.gitignore` already covers `.env` broadly, but not the per-agent paths the pipeline uses. Just append the two lines unconditionally — git ignores duplicates.

- [ ] **Step 1: Append entries**

Use the Edit tool to add this block at the end of `D:/Projects/my-project/.gitignore`:

```
# RevOps Intel standalone pipeline
agents/*/.env
agents/*/knowledge_base/.backups/
```

- [ ] **Step 2: Verify entries are present**

Run via Bash tool: `grep -F "agents/*/.env" D:/Projects/my-project/.gitignore && grep -F "agents/*/knowledge_base/.backups/" D:/Projects/my-project/.gitignore`
Expected: both lines printed.

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore(revops_intel): ignore per-agent .env and KB backups"
```

---

### Task 1.2: Create `.env.example` template

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/.env.example`

- [ ] **Step 1: Write the template**

Content:

```
# RevOps Intel standalone pipeline credentials
# Copy this file to .env in the same directory and fill in your key.
# Get a free Groq API key at https://console.groq.com/keys
GROQ_API_KEY=
```

- [ ] **Step 2: Commit**

```bash
git add agents/revops_intel/.env.example
git commit -m "feat(revops_intel): add .env.example template"
```

---

### Task 1.3: Add `fetch_top_comments` helper to `db.py` (TDD)

**Files:**
- Modify: `D:/Projects/my-project/agents/revops_intel/db.py` (append a new function at the end)
- Create: `D:/Projects/my-project/agents/revops_intel/tests/__init__.py` (empty if not present)
- Create: `D:/Projects/my-project/agents/revops_intel/tests/conftest.py`
- Create: `D:/Projects/my-project/agents/revops_intel/tests/test_db.py`

- [ ] **Step 1: Write the failing test**

Create `agents/revops_intel/tests/test_db.py`:

```python
"""Tests for db.fetch_top_comments helper.

We construct a fresh in-memory SQLite DB with the real schema, insert a
post and three comments with varying scores, then verify the helper returns
them in descending score order, limited to N.
"""
from __future__ import annotations

import time

import pytest

from agents.revops_intel import db


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    db.init_schema(c)
    yield c
    c.close()


def _insert_post(conn, post_id: str = "abc"):
    db.upsert_post_metadata(
        conn,
        {
            "post_id": post_id,
            "subreddit": "sales",
            "author": "u1",
            "title": "test",
            "selftext": "",
            "flair": None,
            "score": 1,
            "num_comments": 0,
            "created_utc": int(time.time()),
            "permalink": "/r/sales/test",
        },
    )


def test_fetch_top_comments_orders_by_score_desc(conn):
    _insert_post(conn)
    now = int(time.time())
    for cid, score in [("c1", 5), ("c2", 50), ("c3", 12)]:
        db.insert_comment(
            conn,
            {
                "comment_id": cid,
                "post_id": "abc",
                "parent_id": None,
                "author": f"u_{cid}",
                "body": f"body {cid}",
                "score": score,
                "depth": 0,
                "created_utc": now,
            },
        )

    rows = db.fetch_top_comments(conn, "abc", limit=10)

    assert [r["author"] for r in rows] == ["u_c2", "u_c3", "u_c1"]
    assert [r["score"] for r in rows] == [50, 12, 5]
    assert all({"author", "body", "score", "depth"} <= set(r) for r in rows)


def test_fetch_top_comments_respects_limit(conn):
    _insert_post(conn)
    now = int(time.time())
    for i in range(15):
        db.insert_comment(
            conn,
            {
                "comment_id": f"c{i}",
                "post_id": "abc",
                "parent_id": None,
                "author": f"u{i}",
                "body": "b",
                "score": i,
                "depth": 0,
                "created_utc": now,
            },
        )

    rows = db.fetch_top_comments(conn, "abc", limit=5)
    assert len(rows) == 5
    assert [r["score"] for r in rows] == [14, 13, 12, 11, 10]


def test_fetch_top_comments_returns_empty_when_no_comments(conn):
    _insert_post(conn)
    rows = db.fetch_top_comments(conn, "abc", limit=10)
    assert rows == []
```

Also use the Write tool to create the package marker `D:/Projects/my-project/agents/revops_intel/tests/__init__.py` with content `""` (empty file).

And use the Write tool to create `D:/Projects/my-project/agents/revops_intel/tests/conftest.py` so pytest can import the `agents` package no matter where it's invoked from:

```python
"""Pytest fixtures and path setup for revops_intel tests."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/Projects/my-project && "C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_db.py -v`
Expected: 3 failures, all with `AttributeError: module 'agents.revops_intel.db' has no attribute 'fetch_top_comments'`

- [ ] **Step 3: Implement `fetch_top_comments`**

Append to `D:/Projects/my-project/agents/revops_intel/db.py`:

```python
def fetch_top_comments(
    conn: sqlite3.Connection, post_id: str, limit: int = 10
) -> list[dict]:
    """Return top-scored comments for a post.

    Each row is a dict with keys: author, body, score, depth.
    Ordered by score DESC, with created_utc ASC as a deterministic
    tie-break so two runs on the same data always return the same order.
    """
    rows = conn.execute(
        """
        SELECT author, body, score, depth
        FROM comments
        WHERE post_id = ?
        ORDER BY score DESC, created_utc ASC
        LIMIT ?
        """,
        (post_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_db.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agents/revops_intel/db.py agents/revops_intel/tests/__init__.py agents/revops_intel/tests/conftest.py agents/revops_intel/tests/test_db.py
git commit -m "feat(revops_intel): add db.fetch_top_comments helper

Lifts the inline SELECT used by /revops-process into a real helper so
both the slash command and the new standalone pipeline can use it
without breaking the 'no raw SQL outside db.py' rule. Adds conftest.py
to ensure pytest can resolve agents.revops_intel imports from any CWD."
```

---

### Task 1.4: Commit a sample lead fixture

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/fixtures/__init__.py` (empty)
- Create: `D:/Projects/my-project/agents/revops_intel/fixtures/sample_lead.json`
- Create: `D:/Projects/my-project/agents/revops_intel/fixtures/sample_comments.json`

The fixture's shape must match what `db.fetch_hot_unprocessed` returns. Tests in chunks 3-5 depend on this exact shape.

**Valid `offer_match` enum (per `knowledge_base/offers.json` keys):**
- `outbound_engine`
- `bookkeeper_command_center`
- `general_automation`

The slash command also uses `none` for "no DM, comment only" leads. The standalone pipeline treats `none` the same — `offers.get("none", offers[DEFAULT_OFFER_KEY])` falls back to `general_automation`.

- [ ] **Step 1: Create `sample_lead.json`**

```json
{
  "post_id": "fixture_001",
  "subreddit": "sales",
  "author": "burned_out_sdr",
  "title": "Outbound is dead, what's actually working in 2026?",
  "selftext": "Series B SaaS. Tried Apollo + Smartlead, reply rate is 0.3%. I'm the head of sales and I have no idea what to fix first. Domains, copy, lists? Considering hiring an agency but every one I've talked to feels like a content mill. Anyone running outbound that actually books meetings?",
  "reddit_score": 142,
  "num_comments": 38,
  "url": "/r/sales/comments/fixture_001/",
  "created_utc": 1731456000,
  "score": 87,
  "reasons": ["asking_for_recs", "explicit_pain", "budget_signal"],
  "problem_category": "outbound_broken",
  "firm_size_signal": "series_b",
  "fit_for_jone": "yes",
  "offer_match": "outbound_engine"
}
```

- [ ] **Step 2: Create `sample_comments.json`**

```json
[
  {"author": "outbound_pro", "body": "Your domain warmup is probably cooked. Apollo data is fine, but if you're sending from a 30-day-old domain without DMARC, everything goes to spam. Check seinheit.com for inbox placement before you blame the copy.", "score": 47, "depth": 0},
  {"author": "agencyhater", "body": "Every agency in our space charges $5k/mo and delivers 50 garbage meetings. Build it in-house with Clay + Instantly, you'll save the money and own the playbook.", "score": 23, "depth": 0},
  {"author": "founder_jane", "body": "We hit 4% reply rate last quarter using ICP-matched Clay enrichment + 3-step Smartlead sequence. The unlock was killing 60% of our list, not adding more.", "score": 18, "depth": 1}
]
```

- [ ] **Step 3: Verify JSON is valid**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "import json; json.load(open('agents/revops_intel/fixtures/sample_lead.json')); json.load(open('agents/revops_intel/fixtures/sample_comments.json')); print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add agents/revops_intel/fixtures/
git commit -m "feat(revops_intel): add sample lead + comments fixture

Shape matches db.fetch_hot_unprocessed return type. Used by
test_llm_extract and test_llm_generate."
```

---

### Chunk 1 done — review checkpoint

After all Chunk 1 tasks pass:

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/ -v
```
Expected: 3 passed

---

## Chunk 2: LLM client (Groq wrapper, retry, voice cleanup)

The single file that knows Groq exists. Every other module calls `llm_client.complete(prompt)` and gets back voice-clean text or an `LLMError`. Provider swap is a one-file edit here. Every line is heavily tested.

### Task 2.1: Define `LLMError`, `GURU_REPLACEMENTS`, and `_load_api_key` (TDD)

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/llm_client.py`
- Create: `D:/Projects/my-project/agents/revops_intel/tests/test_llm_client.py`

- [ ] **Step 1: Write the failing test**

Create `agents/revops_intel/tests/test_llm_client.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_client.py -v`
Expected: 4 errors with `ModuleNotFoundError: No module named 'agents.revops_intel.llm_client'`

- [ ] **Step 3: Write minimal implementation**

Create `agents/revops_intel/llm_client.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_client.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add agents/revops_intel/llm_client.py agents/revops_intel/tests/test_llm_client.py
git commit -m "feat(revops_intel): llm_client foundations (LLMError, GURU_REPLACEMENTS, _load_api_key)"
```

---

### Task 2.2: Add `_enforce_voice` (TDD)

The deterministic post-generation cleanup. All rules per spec: em-dash heuristic, emoji blocks, CTA trailer strip, guru lookup, typographic noise.

**Files:**
- Modify: `D:/Projects/my-project/agents/revops_intel/llm_client.py`
- Modify: `D:/Projects/my-project/agents/revops_intel/tests/test_llm_client.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_llm_client.py`:

```python
# --- _enforce_voice tests ---


@pytest.mark.parametrize("raw,expected", [
    ("I did this — and it worked.", "I did this, and it worked."),
    ("I did this — Then it broke.", "I did this. Then it broke."),
    ("Step one – step two.", "Step one, step two."),
    ("Done — ", "Done. "),
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_client.py -v -k enforce_voice`
Expected: all enforce_voice tests fail with `AttributeError: module ... has no attribute '_enforce_voice'`

- [ ] **Step 3: Implement `_enforce_voice`**

Append to `llm_client.py`:

```python
import re


# Em-dash + en-dash. Heuristic: if next non-space char is uppercase OR end-of-string,
# replace with ". "; otherwise replace with ", ".
_EM_DASH_RE = re.compile(r"\s*[—–]\s*")

# Emoji + symbol blocks Llama 3.3 is known to emit.
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FFFF\U00002600-\U000027BF\U0001F3FB-\U0001F3FF‍]"
)

_TYPOGRAPHIC = [
    ("…", "..."),
    ("→", " to "),
    ("•", "-"),
    ("“", '"'),  # left double quote
    ("”", '"'),  # right double quote
    ("‘", "'"),  # left single quote
    ("’", "'"),  # right single quote
]

_CTA_TRAILERS = [
    r"\bDM me\b[^.!?]*[.!?]?\s*$",
    r"\bHit me up\b[^.!?]*[.!?]?\s*$",
    r"\bFeel free to reach out\b[^.!?]*[.!?]?\s*$",
    r"\bReach out anytime\b[^.!?]*[.!?]?\s*$",
    r"\bShoot me a message\b[^.!?]*[.!?]?\s*$",
]
_CTA_RE = re.compile("|".join(_CTA_TRAILERS), re.IGNORECASE)


def _replace_em_dash(match: re.Match) -> str:
    end = match.end()
    src = match.string
    nxt = ""
    i = end
    while i < len(src) and src[i].isspace():
        i += 1
    if i < len(src):
        nxt = src[i]
    if nxt == "" or nxt.isupper():
        return ". "
    return ", "


def _enforce_voice(text: str) -> tuple[str, list[dict]]:
    """Apply voice cleanup. Returns (cleaned_text, violations).

    violations is a list of {rule, before, after} dicts for logging.
    """
    violations: list[dict] = []

    new_text, n = _EM_DASH_RE.subn(_replace_em_dash, text)
    if n:
        violations.append({"rule": "em_dash", "before": text, "after": new_text})
    text = new_text

    new_text, n = _EMOJI_RE.subn("", text)
    if n:
        violations.append({"rule": "emoji", "before": text, "after": new_text})
    text = new_text

    for raw, replacement in _TYPOGRAPHIC:
        if raw in text:
            new_text = text.replace(raw, replacement)
            violations.append({"rule": "typographic", "before": text, "after": new_text})
            text = new_text

    new_text, n = _CTA_RE.subn("", text)
    if n:
        violations.append({"rule": "cta_trailer", "before": text, "after": new_text.rstrip()})
        text = new_text.rstrip()

    for phrase, replacement in GURU_REPLACEMENTS.items():
        # Word boundaries prevent "10x" from mangling "210x growth" or "100x".
        pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
        new_text, n = pattern.subn(replacement, text)
        if n:
            violations.append({"rule": "guru", "before": text, "after": new_text})
            text = new_text

    # Collapse double-spaces created by substitutions
    text = re.sub(r"  +", " ", text).strip()
    return text, violations
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_client.py -v -k enforce_voice`
Expected: all enforce_voice tests pass

- [ ] **Step 5: Commit**

```bash
git add agents/revops_intel/llm_client.py agents/revops_intel/tests/test_llm_client.py
git commit -m "feat(revops_intel): _enforce_voice with em-dash heuristic, emoji strip, guru lookup"
```

---

### Task 2.3: Add `complete()` with retry and violation logging (TDD)

The public entry point. Calls Groq, retries on 429/5xx, applies voice cleanup, logs everything.

**Files:**
- Modify: `D:/Projects/my-project/agents/revops_intel/llm_client.py`
- Modify: `D:/Projects/my-project/agents/revops_intel/tests/test_llm_client.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_llm_client.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_client.py -v -k "complete"`
Expected: all `test_complete_*` tests fail (function doesn't exist yet)

- [ ] **Step 3: Implement `complete()` and helpers**

Append to `llm_client.py`:

```python
import json
import time
from datetime import datetime, timezone

from groq import Groq, APIStatusError, APIConnectionError, RateLimitError


# Retry sleeps: between 3 attempts, we wait 1s then 4s (5s total wait budget).
# Spec mentioned "(1s, 4s, 16s)" — that was the earlier 4-attempt design.
# We ship 3 attempts because Groq RPM is generous enough that a 3rd retry
# rarely helps; cleaner to give up and log to failed_leads.jsonl.
_BACKOFF_BASE = 1.0  # seconds. Tests patch this to 0.01.
_MAX_RETRIES = 3     # 429: 3 attempts total; 5xx: 2 attempts total
_VIOLATIONS_LOG = str(
    Path(__file__).parent / "logs" / "voice_violations.jsonl"
)
_CALLS_LOG = str(
    Path(__file__).parent / "logs" / "llm_calls.jsonl"
)


_CLIENT: Groq | None = None


def _get_client() -> Groq:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = Groq(api_key=_load_api_key())
    return _CLIENT


def _log_violations(violations: list[dict], lead_id: str | None) -> None:
    if not violations:
        return
    log_path = Path(_VIOLATIONS_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        for v in violations:
            entry = {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "lead_id": lead_id,
                **v,
            }
            f.write(json.dumps(entry) + "\n")


def _log_call(
    model: str, prompt_chars: int, output_chars: int,
    attempts: int, latency_ms: int,
) -> None:
    log_path = Path(_CALLS_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": model, "prompt_chars": prompt_chars,
        "output_chars": output_chars, "attempts": attempts,
        "latency_ms": latency_ms,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def complete(
    prompt: str,
    *,
    max_tokens: int = 800,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
    lead_id: str | None = None,
) -> str:
    """Single Groq call with retry, voice cleanup, and logging.

    Raises LLMError on unrecoverable failure (auth, 3x 429, 2x 5xx, network).
    Returns voice-clean text.
    """
    client = _get_client()
    attempts = 0
    last_exc: Exception | None = None
    started = time.time()

    while attempts < _MAX_RETRIES:
        attempts += 1
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            raw = resp.choices[0].message.content or ""
            cleaned, violations = _enforce_voice(raw)
            _log_violations(violations, lead_id)
            _log_call(
                model, len(prompt), len(cleaned),
                attempts, int((time.time() - started) * 1000),
            )
            return cleaned
        except RateLimitError as e:
            last_exc = e
            if attempts >= _MAX_RETRIES:
                break
            time.sleep(_BACKOFF_BASE * (4 ** (attempts - 1)))
        except APIStatusError as e:
            last_exc = e
            status = getattr(e, "status_code", 0)
            if 500 <= status < 600 and attempts < 2:
                time.sleep(_BACKOFF_BASE * 4)
                continue
            raise LLMError(f"Groq API status error {status}: {e}") from e
        except APIConnectionError as e:
            last_exc = e
            if attempts < 2:
                time.sleep(_BACKOFF_BASE * 4)
                continue
            raise LLMError(f"Groq connection error: {e}") from e

    raise LLMError(
        f"Groq rate limit not recoverable after {attempts} attempts: {last_exc}"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_client.py -v`
Expected: all tests pass (around 15 total)

- [ ] **Step 5: Commit**

```bash
git add agents/revops_intel/llm_client.py agents/revops_intel/tests/test_llm_client.py
git commit -m "feat(revops_intel): llm_client.complete with retry, logging, voice cleanup"
```

---

### Chunk 2 done — verification

Run all chunks 1+2 tests:

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/ -v
```
Expected: ~16 passed (3 db + ~13 llm_client)

---

## Chunk 3: KB extraction

`llm_extract.extract(lead, comments)` reads a hot lead + its top comments and returns a KB diff dict (tools/pains/personas/jargon). Strips `<think>` blocks. Retries on JSON parse failure. Pinned schema per spec.

### Task 3.1: Write the KB extraction prompt template

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/prompts/kb_extract.txt`

- [ ] **Step 1: Write the prompt**

Content (uses `{lead_title}`, `{lead_body}`, `{comments_block}` placeholders, filled by `template.format()`):

```
You are extracting knowledge-base updates from a Reddit thread about B2B SaaS RevOps, outbound sales, or bookkeeping/finance automation. Your output drives outreach generation for downstream tasks.

REDDIT POST
Title: {lead_title}

Body:
{lead_body}

TOP COMMENTS
{comments_block}

YOUR TASK
Extract structured knowledge from this thread. Return a SINGLE JSON object with up to 4 top-level keys: "tools", "pains", "personas", "jargon". Omit any key with no new entries. Be conservative — only add entries if the thread genuinely teaches something new.

SCHEMAS (match shapes exactly)
tools: { "<tool_name_lowercase>": { "category": "outbound|crm|automation|finance|other", "first_seen": "<post_id>", "mention_count": 1, "sentiment_summary": "...", "common_complaints": ["..."], "common_praise": ["..."], "example_quotes": ["..."] } }
pains: { "<pain_slug_snake_case>": { "frequency": 1, "personas_affected": ["..."], "current_workarounds": ["..."], "automation_opportunity": "...", "example_quotes": ["..."] } }
personas: { "<persona_slug>": { "title_variants": ["..."], "firm_size_signals": ["..."], "buying_authority": "...", "language_markers": ["..."], "common_pains": ["..."] } }
jargon: { "<term_lowercase>": { "def": "...", "use_in_outreach": true|false } }

RULES
- Return ONLY the JSON object. No prose before or after. No markdown fences.
- example_quotes must be verbatim from the thread, 1-2 short snippets.
- use_in_outreach=true only for natural identifiers (Apollo, Smartlead, ICP). false for consultant-speak.
- If nothing new, return {{}}.
```

- [ ] **Step 2: Commit**

```bash
git add agents/revops_intel/prompts/kb_extract.txt
git commit -m "feat(revops_intel): KB extraction prompt template"
```

---

### Task 3.2: Implement `llm_extract.extract` (TDD)

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/llm_extract.py`
- Create: `D:/Projects/my-project/agents/revops_intel/tests/test_llm_extract.py`

- [ ] **Step 1: Write the failing tests**

Create `agents/revops_intel/tests/test_llm_extract.py`:

```python
"""Tests for llm_extract.extract.

llm_client.complete is mocked so we control the model's return value.
Fixture lead matches db.fetch_hot_unprocessed shape (per Task 1.4).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import llm_extract, llm_client


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def sample_lead():
    return json.loads((FIXTURE_DIR / "sample_lead.json").read_text(encoding="utf-8"))


@pytest.fixture
def sample_comments():
    return json.loads((FIXTURE_DIR / "sample_comments.json").read_text(encoding="utf-8"))


def test_extract_returns_parsed_json(monkeypatch, sample_lead, sample_comments):
    response_json = {
        "tools": {"smartlead": {"category": "outbound", "first_seen": sample_lead["post_id"],
                                "mention_count": 1, "sentiment_summary": "mixed",
                                "common_complaints": ["deliverability issues"],
                                "common_praise": [], "example_quotes": ["Smartlead"]}},
        "pains": {}, "personas": {}, "jargon": {},
    }
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: json.dumps(response_json))

    out = llm_extract.extract(sample_lead, sample_comments)

    assert out == response_json
    assert "smartlead" in out["tools"]


def test_extract_strips_think_blocks(monkeypatch, sample_lead, sample_comments):
    raw = '<think>analyzing the thread</think>\n{"tools": {}, "pains": {}, "personas": {}, "jargon": {}}'
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: raw)

    out = llm_extract.extract(sample_lead, sample_comments)
    assert out == {"tools": {}, "pains": {}, "personas": {}, "jargon": {}}


def test_extract_retries_once_on_json_parse_failure(monkeypatch, sample_lead, sample_comments):
    calls = []
    responses = ["this is not json", '{"tools": {}, "pains": {}, "personas": {}, "jargon": {}}']
    def fake(prompt, **kw):
        calls.append(prompt)
        return responses.pop(0)
    monkeypatch.setattr(llm_client, "complete", fake)

    out = llm_extract.extract(sample_lead, sample_comments)

    assert len(calls) == 2
    assert "RETURN ONLY VALID JSON" in calls[1]
    assert out == {"tools": {}, "pains": {}, "personas": {}, "jargon": {}}


def test_extract_returns_empty_dict_after_two_failures(monkeypatch, tmp_path,
                                                       sample_lead, sample_comments):
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: "still not json")
    monkeypatch.setattr(llm_extract, "_FAILED_LOG", str(tmp_path / "failed.jsonl"))

    out = llm_extract.extract(sample_lead, sample_comments)

    assert out == {}
    log = (tmp_path / "failed.jsonl").read_text(encoding="utf-8")
    assert sample_lead["post_id"] in log
    assert "json_parse" in log
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_extract.py -v`
Expected: 4 errors with `ModuleNotFoundError: No module named 'agents.revops_intel.llm_extract'`

- [ ] **Step 3: Implement `llm_extract.py`**

Create `agents/revops_intel/llm_extract.py`:

```python
"""KB extraction step for the standalone RevOps Intel pipeline.

Given a hot lead + its top comments, returns a KB diff dict with up to
4 top-level keys (tools, pains, personas, jargon). Caller is responsible
for merging into the real KB JSON files atomically.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from agents.revops_intel import llm_client


_PROMPTS_DIR = Path(__file__).parent / "prompts"
_FAILED_LOG = str(Path(__file__).parent / "logs" / "failed_leads.jsonl")
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _load_prompt() -> str:
    return (_PROMPTS_DIR / "kb_extract.txt").read_text(encoding="utf-8")


def _format_comments(comments: list[dict]) -> str:
    if not comments:
        return "(no comments)"
    lines = []
    for c in comments[:5]:
        body = c.get("body", "").strip().replace("\n", " ")
        lines.append(f"- u/{c.get('author', '?')} ({c.get('score', 0)} pts): {body[:500]}")
    return "\n".join(lines)


def _log_failure(lead_id: str, kind: str, detail: str) -> None:
    log_path = Path(_FAILED_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lead_id": lead_id, "stage": "extract", "kind": kind, "detail": detail[:500],
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _try_parse(raw: str) -> dict | None:
    stripped = _THINK_RE.sub("", raw).strip()
    # Strip markdown fences if model wrapped JSON in them
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```\s*$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def extract(lead: dict, top_comments: list[dict]) -> dict:
    """Run KB extraction on a hot lead. Returns parsed diff dict or {} on failure."""
    template = _load_prompt()
    prompt = template.format(
        lead_title=lead.get("title", ""),
        lead_body=lead.get("selftext", "")[:3000],
        comments_block=_format_comments(top_comments),
    )

    raw = llm_client.complete(
        prompt, max_tokens=1500, temperature=0.2,
        lead_id=lead.get("post_id"),
    )
    parsed = _try_parse(raw)
    if parsed is not None:
        return parsed

    # Retry once with stricter instruction appended
    strict_prompt = prompt + "\n\nRETURN ONLY VALID JSON. NO PROSE. NO MARKDOWN."
    raw2 = llm_client.complete(
        strict_prompt, max_tokens=1500, temperature=0.1,
        lead_id=lead.get("post_id"),
    )
    parsed = _try_parse(raw2)
    if parsed is not None:
        return parsed

    _log_failure(lead.get("post_id", "?"), "json_parse",
                 f"raw1={raw[:200]} raw2={raw2[:200]}")
    return {}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_extract.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add agents/revops_intel/llm_extract.py agents/revops_intel/prompts/kb_extract.txt agents/revops_intel/tests/test_llm_extract.py
git commit -m "feat(revops_intel): llm_extract with JSON retry, think-block strip, failure logging"
```

---

## Chunk 4: Comment + DM generation

`llm_generate.generate(lead, comments, offer_pitch)` returns `(comment, dm)` or raises `QualityFlag` after two failed quality-check retries.

### Task 4.1: Write comment + DM prompt templates

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/prompts/reddit_comment.txt`
- Create: `D:/Projects/my-project/agents/revops_intel/prompts/reddit_dm.txt`

- [ ] **Step 1: Write `reddit_comment.txt`**

```
You are writing a Reddit comment in response to a B2B SaaS RevOps thread. You sound like a peer who has built outbound/finance automation, not a guru.

CONTEXT
Subreddit: r/{subreddit}
Title: {lead_title}

Body:
{lead_body}

Top comments:
{comments_block}

Knowledge-base anchors (use sparingly, only when relevant):
{kb_anchors}

Offer angle to lean toward (do NOT pitch, but match the pain shape): {offer_summary}

YOUR TASK
Write a single Reddit comment, 60-200 words, value-first, no pitch.
- Open with a specific observation about the OP's situation.
- Give one concrete tactic, tool, or framework they can apply this week.
- Reference a specific tool name or metric if the KB anchors are relevant.
- End naturally. No "DM me", no "happy to share", no CTA.

HARD RULES — violations will be regex-stripped automatically:
- No em-dashes (—, –). Use periods, commas, or "and".
- No emoji. None.
- No "DM me", "Hit me up", "Feel free to reach out", "Reach out anytime", "Shoot me a message".
- No guru cadence ("game changer", "10x", "level up", "crushing it", "synergy", "move the needle", "low-hanging fruit", "deep dive").
- Plain prose. Sound like a peer.

Return ONLY the comment text. No preamble, no quotes, no markdown.
```

- [ ] **Step 2: Write `reddit_dm.txt`**

```
You are writing a Reddit DM to follow up after the OP engages with a public comment. Warmer than the comment, references their specific situation, leads with proof.

CONTEXT
Subreddit: r/{subreddit}
Title: {lead_title}

Body:
{lead_body}

Offer pitch points (use one or two as proof, never list all):
{offer_proof_points}

Offer summary: {offer_summary}

YOUR TASK
Write a single Reddit DM, 60-150 words, signed "Jone".
- Reference one specific detail from their post (a tool they named, the metric they shared, the stuck point).
- Lead with one concrete proof point (a result you've delivered, what you've built).
- Offer a free 30-min audit / no obligation conversation.
- Plain prose.

HARD RULES — violations will be regex-stripped automatically:
- No em-dashes (—, –). Use periods, commas, or "and".
- No emoji.
- No guru cadence ("game changer", "10x", "level up", "crushing it", "synergy").
- Sound like a peer.

Return ONLY the DM text. No preamble, no quotes.
```

- [ ] **Step 3: Commit**

```bash
git add agents/revops_intel/prompts/reddit_comment.txt agents/revops_intel/prompts/reddit_dm.txt
git commit -m "feat(revops_intel): comment + DM prompt templates"
```

---

### Task 4.2: Implement `llm_generate.generate` with `QualityFlag` (TDD)

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/llm_generate.py`
- Create: `D:/Projects/my-project/agents/revops_intel/tests/test_llm_generate.py`

- [ ] **Step 1: Write the failing tests**

Create `agents/revops_intel/tests/test_llm_generate.py`:

```python
"""Tests for llm_generate.generate.

llm_client.complete is mocked. We verify length checks, prompt-leak
detection, truncation detection, and QualityFlag escalation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import llm_generate, llm_client


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def sample_lead():
    return json.loads((FIXTURE_DIR / "sample_lead.json").read_text(encoding="utf-8"))


@pytest.fixture
def sample_comments():
    return json.loads((FIXTURE_DIR / "sample_comments.json").read_text(encoding="utf-8"))


@pytest.fixture
def offer_pitch():
    return {
        "name": "Outbound Engine",
        "ideal_buyer": "B2B SaaS founder Series A-B",
        "scope": "domains, warmup, copy, list, sequence",
        "proof_points_jone_can_use": ["ran outbound playbook at Cause", "5% reply rate avg"],
    }


GOOD_COMMENT = ("Your domain warmup is the first place to look. If you spun up a fresh "
                "domain in the last 30 days and you have not configured DMARC, almost "
                "everything will go to spam regardless of copy quality. Run your sending "
                "address through seinheit.com to check inbox placement, then layer "
                "ICP-tight Clay enrichment so you are sending to people who match the "
                "buyer profile. Cutting your list by half almost always beats adding "
                "more contacts.")
GOOD_DM = ("Saw your post about Smartlead reply rates. I have built outbound for "
           "B2B SaaS at Series A-B, hit roughly 4 percent reply rate by tightening "
           "the ICP and rebuilding domain warmup before touching copy. Happy to do "
           "a free 30-minute audit of your current setup, no obligation. "
           "Jone")


def test_generate_returns_clean_comment_and_dm(monkeypatch, sample_lead,
                                                sample_comments, offer_pitch):
    responses = iter([GOOD_COMMENT, GOOD_DM])
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: next(responses))

    comment, dm = llm_generate.generate(sample_lead, sample_comments, offer_pitch)

    assert 60 <= len(comment.split()) <= 250
    assert 60 <= len(dm.split()) <= 180
    assert comment.rstrip().endswith((".", "!", "?"))


def test_generate_retries_on_short_output(monkeypatch, sample_lead,
                                           sample_comments, offer_pitch):
    too_short = "Too brief."
    responses = iter([too_short, GOOD_COMMENT, GOOD_DM])
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: next(responses))

    comment, dm = llm_generate.generate(sample_lead, sample_comments, offer_pitch)
    assert 60 <= len(comment.split())


def test_generate_raises_quality_flag_on_two_short_outputs(monkeypatch, sample_lead,
                                                            sample_comments, offer_pitch):
    too_short = "Too brief."
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: too_short)

    with pytest.raises(llm_generate.QualityFlag) as exc:
        llm_generate.generate(sample_lead, sample_comments, offer_pitch)

    assert "length" in exc.value.reason.lower()
    assert exc.value.comment == too_short


def test_generate_raises_quality_flag_on_prompt_leak(monkeypatch, sample_lead,
                                                      sample_comments, offer_pitch):
    leaked = ("HARD RULES violations will be regex-stripped automatically. "
              "Here is my reply: " + GOOD_COMMENT)
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: leaked)

    with pytest.raises(llm_generate.QualityFlag) as exc:
        llm_generate.generate(sample_lead, sample_comments, offer_pitch)
    assert "prompt_leak" in exc.value.reason.lower() or "leak" in exc.value.reason.lower()


def test_generate_raises_quality_flag_on_truncation(monkeypatch, sample_lead,
                                                     sample_comments, offer_pitch):
    truncated = (GOOD_COMMENT.rstrip(".") + " and then the model just stopped writing "
                 "in the middle of a sentence without finishing the")
    monkeypatch.setattr(llm_client, "complete", lambda *a, **k: truncated)

    with pytest.raises(llm_generate.QualityFlag) as exc:
        llm_generate.generate(sample_lead, sample_comments, offer_pitch)
    assert "truncat" in exc.value.reason.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_generate.py -v`
Expected: 5 errors with `ModuleNotFoundError`

- [ ] **Step 3: Implement `llm_generate.py`**

Create `agents/revops_intel/llm_generate.py`:

```python
"""Comment + DM drafting for the standalone RevOps Intel pipeline.

Two LLM calls per lead. Output passes prompt-leak, truncation, and length
checks. Retries once on failure; second failure raises QualityFlag carrying
the last attempts so the caller can save a _FLAGGED_*.md queue file.
"""
from __future__ import annotations

import re
from pathlib import Path

from agents.revops_intel import llm_client


_PROMPTS_DIR = Path(__file__).parent / "prompts"

COMMENT_MIN = 60
COMMENT_MAX = 250
DM_MIN = 60
DM_MAX = 180

_PROMPT_LEAK_MARKERS = ("HARD RULES", "AS AN AI", "As an AI", "{lead_title}",
                       "{lead_body}", "{comments_block}", "{kb_anchors}")


class QualityFlag(Exception):
    """Raised when generation fails quality checks twice in a row."""
    def __init__(self, comment: str, dm: str, reason: str):
        self.comment, self.dm, self.reason = comment, dm, reason
        super().__init__(reason)


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def _format_comments(comments: list[dict]) -> str:
    if not comments:
        return "(no comments)"
    return "\n".join(
        f"- u/{c.get('author', '?')} ({c.get('score', 0)} pts): {c.get('body', '').strip()[:400]}"
        for c in comments[:3]
    )


def _kb_anchors(lead: dict) -> str:
    cat = lead.get("problem_category", "")
    return f"(problem_category: {cat})" if cat else "(no anchors)"


def _offer_summary(pitch: dict) -> str:
    return f"{pitch.get('name', 'general automation')}. Ideal buyer: {pitch.get('ideal_buyer', '')[:200]}"


def _offer_proof(pitch: dict) -> str:
    points = pitch.get("proof_points_jone_can_use", [])
    return "\n".join(f"- {p}" for p in points[:6])


def _check_quality(text: str, min_words: int, max_words: int, kind: str) -> str | None:
    """Return None if OK, else a reason string."""
    stripped = text.strip()
    if any(marker in stripped for marker in _PROMPT_LEAK_MARKERS):
        return f"prompt_leak detected in {kind}"
    if not stripped:
        return f"{kind} is empty"
    if stripped[-1] not in ".!?":
        return f"{kind} appears truncated (no terminal punctuation)"
    n = len(stripped.split())
    if n < min_words or n > max_words:
        return f"{kind} length out of range ({n} words, want {min_words}-{max_words})"
    return None


def _generate_one(prompt: str, min_words: int, max_words: int, kind: str,
                  lead_id: str | None) -> tuple[str, str | None]:
    """Two attempts. Returns (text, last_reason). last_reason is None on success."""
    last_text = ""
    last_reason: str | None = None
    for attempt in (1, 2):
        active_prompt = prompt
        if attempt == 2:
            active_prompt += (
                f"\n\nPREVIOUS ATTEMPT FAILED: {last_reason}\n"
                "Try again. Stay strictly within length range. End with a complete sentence."
            )
        text = llm_client.complete(
            active_prompt, max_tokens=600, temperature=0.7, lead_id=lead_id,
        )
        last_text = text
        reason = _check_quality(text, min_words, max_words, kind)
        if reason is None:
            return text, None
        last_reason = reason
    return last_text, last_reason


def generate(lead: dict, top_comments: list[dict], offer_pitch: dict) -> tuple[str, str]:
    """Returns (reddit_comment, reddit_dm). Raises QualityFlag if checks fail twice."""
    lead_id = lead.get("post_id")
    common = {
        "subreddit": lead.get("subreddit", ""),
        "lead_title": lead.get("title", ""),
        "lead_body": (lead.get("selftext") or "")[:2000],
        "comments_block": _format_comments(top_comments),
        "kb_anchors": _kb_anchors(lead),
        "offer_summary": _offer_summary(offer_pitch),
        "offer_proof_points": _offer_proof(offer_pitch),
    }

    comment_prompt = _load_prompt("reddit_comment.txt").format(**common)
    comment, c_reason = _generate_one(
        comment_prompt, COMMENT_MIN, COMMENT_MAX, "comment", lead_id,
    )

    dm_prompt = _load_prompt("reddit_dm.txt").format(**common)
    dm, d_reason = _generate_one(
        dm_prompt, DM_MIN, DM_MAX, "dm", lead_id,
    )

    if c_reason or d_reason:
        raise QualityFlag(
            comment=comment, dm=dm,
            reason=f"comment: {c_reason or 'ok'} | dm: {d_reason or 'ok'}",
        )

    return comment, dm
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_llm_generate.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add agents/revops_intel/llm_generate.py agents/revops_intel/prompts/reddit_*.txt agents/revops_intel/tests/test_llm_generate.py
git commit -m "feat(revops_intel): llm_generate with prompt-leak/truncation/length checks + QualityFlag"
```

---

## Chunk 5: Chain runner

`run.py` is the entrypoint. Wraps existing scrape/score/route subprocesses, then loops hot leads serially through extract + generate, writes queue files in the existing format, marks processed, prints summary.

### Task 5.1: KB backup snapshot helper (TDD)

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/kb_backups.py`
- Create: `D:/Projects/my-project/agents/revops_intel/tests/test_kb_backups.py`

- [ ] **Step 1: Failing tests**

```python
"""Tests for kb_backups module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import kb_backups


@pytest.fixture
def tmp_kb(tmp_path, monkeypatch):
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()
    for name in ("tools", "pains", "personas", "jargon"):
        (kb_dir / f"{name}.json").write_text('{"v": 1}', encoding="utf-8")
    monkeypatch.setattr(kb_backups, "_KB_DIR", kb_dir)
    monkeypatch.setattr(kb_backups, "_BACKUP_DIR", kb_dir / ".backups")
    return kb_dir


def test_snapshot_creates_backup_files(tmp_kb):
    kb_backups.snapshot()
    backups = list((tmp_kb / ".backups").glob("*.bak"))
    assert len(backups) == 4
    assert all(b.stat().st_size > 0 for b in backups)


def test_snapshot_prunes_to_7_per_file(tmp_kb, monkeypatch):
    import time as t
    for i in range(10):
        kb_backups.snapshot()
        # Force unique timestamps in the filename
        t.sleep(0.01)
        monkeypatch.setattr(
            kb_backups, "_TIMESTAMP_FN",
            lambda i=i: f"2026-05-13T00-00-{i:02d}",
        )

    for name in ("tools", "pains", "personas", "jargon"):
        backups = list((tmp_kb / ".backups").glob(f"*_{name}.json.bak"))
        assert len(backups) <= 7, f"{name} has {len(backups)} backups"


def test_restore_latest_returns_most_recent(tmp_kb, monkeypatch):
    monkeypatch.setattr(kb_backups, "_TIMESTAMP_FN", lambda: "2026-05-13T00-00-01")
    kb_backups.snapshot()
    monkeypatch.setattr(kb_backups, "_TIMESTAMP_FN", lambda: "2026-05-13T00-00-02")
    (tmp_kb / "tools.json").write_text('{"v": 2}', encoding="utf-8")
    kb_backups.snapshot()

    restored = kb_backups.restore_latest("tools")
    assert json.loads(restored) == {"v": 2}
```

- [ ] **Step 2: Run to fail**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_kb_backups.py -v`
Expected: ModuleNotFoundError for `kb_backups`

- [ ] **Step 3: Implement `kb_backups.py`**

```python
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
_FILES = ("tools", "pains", "personas", "jargon")


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
```

- [ ] **Step 4: Run to pass**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/test_kb_backups.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agents/revops_intel/kb_backups.py agents/revops_intel/tests/test_kb_backups.py
git commit -m "feat(revops_intel): KB snapshot/restore with 7-day retention"
```

---

### Task 5.2: Atomic KB merge helper (TDD)

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/kb_merge.py`
- Create: `D:/Projects/my-project/agents/revops_intel/tests/test_kb_merge.py`

The merge protocol from the slash command: read fresh from disk per lead, merge diff, write atomically (write to .tmp then rename). One file at a time.

- [ ] **Step 1: Failing tests**

```python
"""Tests for kb_merge.merge_atomic."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import kb_merge


@pytest.fixture
def tmp_kb(tmp_path, monkeypatch):
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()
    for name in ("tools", "pains", "personas", "jargon"):
        (kb_dir / f"{name}.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(kb_merge, "_KB_DIR", kb_dir)
    return kb_dir


def test_merge_adds_new_tool(tmp_kb):
    diff = {"tools": {"smartlead": {"category": "outbound", "mention_count": 1,
                                     "example_quotes": ["quote"]}}}
    kb_merge.merge_atomic(diff)

    data = json.loads((tmp_kb / "tools.json").read_text(encoding="utf-8"))
    assert "smartlead" in data
    assert data["smartlead"]["mention_count"] == 1


def test_merge_increments_existing_mention_count(tmp_kb):
    (tmp_kb / "tools.json").write_text(
        json.dumps({"smartlead": {"category": "outbound", "mention_count": 3,
                                    "example_quotes": ["old"]}}),
        encoding="utf-8",
    )
    diff = {"tools": {"smartlead": {"category": "outbound", "mention_count": 1,
                                     "example_quotes": ["new quote"]}}}
    kb_merge.merge_atomic(diff)

    data = json.loads((tmp_kb / "tools.json").read_text(encoding="utf-8"))
    assert data["smartlead"]["mention_count"] == 4
    assert "old" in data["smartlead"]["example_quotes"]
    assert "new quote" in data["smartlead"]["example_quotes"]


def test_merge_handles_empty_diff(tmp_kb):
    kb_merge.merge_atomic({})
    data = json.loads((tmp_kb / "tools.json").read_text(encoding="utf-8"))
    assert data == {}


def test_merge_ignores_unknown_top_level_keys(tmp_kb):
    diff = {"tools": {"x": {"mention_count": 1}}, "garbage": {"foo": "bar"}}
    kb_merge.merge_atomic(diff)
    assert (tmp_kb / "tools.json").exists()
    assert not (tmp_kb / "garbage.json").exists()
```

- [ ] **Step 2: Run to fail** → ModuleNotFoundError

- [ ] **Step 3: Implement `kb_merge.py`**

```python
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
```

- [ ] **Step 4: Run to pass** → 4 passed

- [ ] **Step 5: Commit**

```bash
git add agents/revops_intel/kb_merge.py agents/revops_intel/tests/test_kb_merge.py
git commit -m "feat(revops_intel): atomic KB merge with per-key sum/dedupe/overwrite rules"
```

---

### Task 5.3: Queue file writer (TDD)

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/queue_writer.py`
- Create: `D:/Projects/my-project/agents/revops_intel/tests/test_queue_writer.py`

- [ ] **Step 1: Failing test**

```python
"""Tests for queue_writer.write."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.revops_intel import queue_writer


@pytest.fixture
def sample_lead():
    return json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "sample_lead.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def sample_comments():
    return json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "sample_comments.json").read_text(encoding="utf-8")
    )


def test_write_creates_file_with_frontmatter(tmp_path, monkeypatch, sample_lead, sample_comments):
    monkeypatch.setattr(queue_writer, "_QUEUE_DIR", tmp_path)
    out_path = queue_writer.write(
        sample_lead, sample_comments, "the comment", "the dm",
        kb_diff={"tools": {"smartlead": {"mention_count": 1}}},
        flagged=False,
    )
    text = Path(out_path).read_text(encoding="utf-8")
    assert text.startswith("---")
    assert f"post_id: {sample_lead['post_id']}" in text
    assert "the comment" in text
    assert "the dm" in text
    assert "Added tool" in text  # KB diff summary section
    assert "_FLAGGED_" not in out_path


def test_write_flagged_prefix(tmp_path, monkeypatch, sample_lead, sample_comments):
    monkeypatch.setattr(queue_writer, "_QUEUE_DIR", tmp_path)
    out_path = queue_writer.write(
        sample_lead, sample_comments, "c", "d", kb_diff={}, flagged=True,
    )
    assert "_FLAGGED_" in Path(out_path).name
```

- [ ] **Step 2: Run to fail**

- [ ] **Step 3: Implement `queue_writer.py`**

```python
"""Write queue files in the format /revops-process produces."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


_QUEUE_DIR = Path(__file__).parent / "queue"


def _sanitize(author: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", author or "anon")[:32]


def _kb_summary(kb_diff: dict) -> str:
    lines = []
    for tool in (kb_diff.get("tools") or {}):
        lines.append(f"- Added tool: \"{tool}\"")
    for pain in (kb_diff.get("pains") or {}):
        lines.append(f"- Added pain: \"{pain}\"")
    for persona in (kb_diff.get("personas") or {}):
        lines.append(f"- Updated persona: \"{persona}\"")
    for term in (kb_diff.get("jargon") or {}):
        lines.append(f"- Added jargon: \"{term}\"")
    return "\n".join(lines) if lines else "- (no KB updates this lead)"


def _format_comments_section(comments: list[dict]) -> str:
    if not comments:
        return "- (no top comments)"
    out = []
    for c in comments[:5]:
        snippet = (c.get("body") or "").strip().replace("\n", " ")[:300]
        out.append(f'- u/{c.get("author","?")} ({c.get("score",0)} upvotes): "{snippet}"')
    return "\n".join(out)


def write(lead: dict, comments: list[dict], comment_text: str, dm_text: str,
          kb_diff: dict, *, flagged: bool) -> str:
    _QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    author = _sanitize(lead.get("author", ""))
    prefix = "_FLAGGED_" if flagged else ""
    name = f"{date}_{prefix}{author}_{lead['post_id']}.md"
    path = _QUEUE_DIR / name

    body = f"""---
post_id: {lead['post_id']}
author: u/{lead.get('author', '')}
subreddit: {lead.get('subreddit', '')}
url: {lead.get('url', '')}
score: {lead.get('score', 0)}
reasons: {lead.get('reasons', [])}
problem_category: {lead.get('problem_category', '')}
firm_size_signal: {lead.get('firm_size_signal', '')}
offer_match: {lead.get('offer_match', '')}
generated_at: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
{"flagged: true" if flagged else "flagged: false"}
---

## Original post
**{lead.get('title', '')}**
> {(lead.get('selftext') or '').strip()}

## Why this lead is hot
- Score {lead.get('score', 0)} on revops_intel scorer
- Reasons: {", ".join(lead.get('reasons', []))}

## Top relevant comments (insider context)
{_format_comments_section(comments)}

## Suggested REDDIT COMMENT
> {comment_text}

## Suggested REDDIT DM
> {dm_text}

## Knowledge updates from this thread
{_kb_summary(kb_diff)}
"""
    path.write_text(body, encoding="utf-8")
    return str(path)
```

- [ ] **Step 4: Run to pass** → 2 passed

- [ ] **Step 5: Commit**

```bash
git add agents/revops_intel/queue_writer.py agents/revops_intel/tests/test_queue_writer.py
git commit -m "feat(revops_intel): queue file writer matching /revops-process format"
```

---

### Task 5.4: Chain runner `run.py` + `run.bat`

**Files:**
- Create: `D:/Projects/my-project/agents/revops_intel/run.py`
- Create: `D:/Projects/my-project/agents/revops_intel/run.bat`

This task does NOT have unit tests (it's a top-level orchestrator that calls subprocesses); we cover it via the integration smoke test in Task 5.5.

- [ ] **Step 1: Write `run.py`**

```python
"""Chain runner for the standalone RevOps Intel pipeline.

Refresh data, then loop hot leads through extract + generate, write queue
files, mark processed. No interactive Claude Code session required.

Usage:
    python -m agents.revops_intel.run [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from agents.revops_intel import db, kb_backups, kb_merge, llm_extract, llm_generate
from agents.revops_intel.llm_client import LLMError
from agents.revops_intel.llm_generate import QualityFlag
from agents.revops_intel import queue_writer


PY = sys.executable
_LOG_DIR = Path(__file__).parent / "logs"
_FAILED_LOG = _LOG_DIR / "failed_leads.jsonl"
_ZERO_STREAK = _LOG_DIR / "zero_lead_streak.txt"

_KB_PATH = Path(__file__).parent / "knowledge_base"
DEFAULT_OFFER_KEY = "general_automation"


def _log_failure(lead: dict, exc: Exception, tb: bool = False) -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lead_id": lead.get("post_id", "?"),
        "stage": "run",
        "error": str(exc)[:500],
    }
    if tb:
        entry["traceback"] = traceback.format_exc()[:2000]
    with _FAILED_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _bump_zero_streak() -> int:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    cur = 0
    if _ZERO_STREAK.exists():
        try:
            cur = int(_ZERO_STREAK.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            cur = 0
    cur += 1
    _ZERO_STREAK.write_text(str(cur), encoding="utf-8")
    return cur


def _reset_zero_streak() -> None:
    if _ZERO_STREAK.exists():
        _ZERO_STREAK.write_text("0", encoding="utf-8")


def main(limit: int = 20, dry_run: bool = False) -> int:
    print(f"[run] starting (limit={limit}, dry_run={dry_run})")

    print("[run] snapshotting KB backups")
    kb_backups.snapshot()

    print("[run] refreshing data (scrape -> score -> route)")
    for stage in ("scrape", "score", "route"):
        result = subprocess.run(
            [PY, "-m", f"agents.revops_intel.{stage}"],
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        if result.returncode != 0:
            print(f"[run] FATAL: {stage} exited with {result.returncode}")
            return 1

    conn = db.connect()
    hot = db.fetch_hot_unprocessed(conn, limit=limit)

    if not hot:
        streak = _bump_zero_streak()
        print(f"[run] no hot leads (streak: {streak} days)")
        if streak >= 3:
            print(f"[run] WARNING: zero-lead streak hit {streak} days; check upstream scoring")
        return 0
    _reset_zero_streak()

    offers = json.loads((_KB_PATH / "offers.json").read_text(encoding="utf-8"))
    stats = {"processed": 0, "flagged": 0, "failed": 0,
             "kb_diffs": Counter()}

    for i, lead in enumerate(hot, start=1):
        print(f"[run] {i}/{len(hot)} processing {lead['post_id']} ({lead.get('subreddit')})")
        kb_diff: dict = {}
        comments: list[dict] = []
        try:
            comments = db.fetch_top_comments(conn, lead["post_id"], limit=10)
            kb_diff = llm_extract.extract(lead, comments)
            if kb_diff and not dry_run:
                kb_merge.merge_atomic(kb_diff)
                for k in ("tools", "pains", "personas", "jargon"):
                    stats["kb_diffs"][k] += len(kb_diff.get(k) or {})

            offer_pitch = offers.get(
                lead.get("offer_match"), offers[DEFAULT_OFFER_KEY],
            )
            comment, dm = llm_generate.generate(lead, comments, offer_pitch)

            if not dry_run:
                queue_file = queue_writer.write(
                    lead, comments, comment, dm, kb_diff, flagged=False,
                )
                db.mark_processed(
                    conn, lead["post_id"], queue_file, lead.get("offer_match"),
                )
            stats["processed"] += 1
        except QualityFlag as qf:
            if not dry_run:
                queue_file = queue_writer.write(
                    lead, comments, qf.comment, qf.dm, kb_diff, flagged=True,
                )
                db.mark_processed(
                    conn, lead["post_id"], queue_file, lead.get("offer_match"),
                )
            stats["flagged"] += 1
            print(f"[run]   FLAGGED: {qf.reason}")
        except LLMError as e:
            _log_failure(lead, e)
            stats["failed"] += 1
            print(f"[run]   FAILED (LLM): {e}")
        except Exception as e:
            _log_failure(lead, e, tb=True)
            stats["failed"] += 1
            print(f"[run]   FAILED (unexpected): {e}")

        time.sleep(2.1)

    print("\n[run] summary:")
    print(f"  processed: {stats['processed']}")
    print(f"  flagged:   {stats['flagged']}")
    print(f"  failed:    {stats['failed']}")
    print(f"  KB diffs:  {dict(stats['kb_diffs'])}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    sys.exit(main(limit=args.limit, dry_run=args.dry_run))
```

- [ ] **Step 2: Write `run.bat`**

```
@echo off
REM Standalone RevOps Intel pipeline. Run from anywhere.
pushd D:\Projects\my-project
"C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe" -m agents.revops_intel.run %*
popd
```

- [ ] **Step 3: Commit**

```bash
git add agents/revops_intel/run.py agents/revops_intel/run.bat
git commit -m "feat(revops_intel): chain runner run.py + run.bat launcher"
```

---

### Task 5.5: Integration smoke test (manual, not in CI)

This task is a manual checklist, not new code. Document it once, run it at least once before declaring chunk 5 done.

- [ ] **Step 1: Dry-run with no real API call (validate prompts only)**

Set up `.env` with a real Groq key (free from https://console.groq.com/keys). Then:

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.revops_intel.run --limit 1 --dry-run
```

Expected output:
- "[run] starting (limit=1, dry_run=True)"
- Scrape/score/route run cleanly (or warn if no new data)
- One lead processed, one comment and DM generated
- No file written under `queue/`
- No row added to `processed_leads`

- [ ] **Step 2: Real run, single lead**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.revops_intel.run --limit 1
```

Verify:
- One file in `queue/` matching `YYYY-MM-DD_<author>_<post_id>.md`
- File frontmatter contains `post_id`, `subreddit`, `url`, `score`, `offer_match`
- Voice rules hold: zero `—`, no emoji, no "DM me"
- KB JSON files updated (or unchanged if model returned no new entries)
- `processed_leads` table has the row

- [ ] **Step 3: If all checks pass, commit a one-line audit note**

```bash
echo "First smoke test run: $(date) - 1 lead processed cleanly" >> agents/revops_intel/logs/audit.log
git add agents/revops_intel/logs/audit.log
git commit -m "chore(revops_intel): first smoke test pass logged"
```

---

## Chunk 6: SOP updates

These are documentation updates per the spec's "SOP touchpoints" section. No code, but treated as mandatory completion criteria. Skipping these means the pipeline gets lost in a month.

### Task 6.1: Update `SOPs/AGENT/02-AGENT-REGISTRY.md`

**Files:**
- Modify: `D:/Projects/my-project/SOPs/AGENT/02-AGENT-REGISTRY.md`

- [ ] **Step 1: Append entry under Lead-generation agents**

Find the section "## Lead-generation agents" and append (before the next `##` header):

```markdown
### revops_intel/run.py
- **Purpose:** Standalone Reddit lead pipeline for B2B SaaS RevOps niche. Free-LLM replacement for `/revops-process`.
- **Stack:** PRAW + SQLite + Groq Llama 3.3 70B + python-dotenv
- **Usage:** `python -m agents.revops_intel.run [--limit N] [--dry-run]` or `agents\revops_intel\run.bat`
- **Output:** `agents/revops_intel/queue/*.md` + KB JSON updates + processed_leads DB writes
- **Health:** [STATUS as of <date>]
- **Known issues:** [TBD on first month of runs]
```

- [ ] **Step 2: Commit**

```bash
git add SOPs/AGENT/02-AGENT-REGISTRY.md
git commit -m "docs(sops): register revops_intel/run.py in agent registry"
```

---

### Task 6.2: Update `SOPs/AGENT/registry.json`

**Files:**
- Modify: `D:/Projects/my-project/SOPs/AGENT/registry.json`

- [ ] **Step 1: Read the file**

Use the Read tool to see the current JSON structure (so the new object fits in cleanly).

- [ ] **Step 2: Insert object under `agents` key**

Use the Edit tool to add:

```json
"revops_intel_standalone": {
  "path": "agents/revops_intel/run.py",
  "purpose": "Standalone Reddit lead pipeline for B2B SaaS RevOps niche; free-LLM replacement for /revops-process",
  "stack": ["praw", "sqlite3", "groq", "python-dotenv"],
  "llm_provider": "groq",
  "llm_model": "llama-3.3-70b-versatile",
  "usage": "python -m agents.revops_intel.run [--limit N] [--dry-run]",
  "output_paths": ["agents/revops_intel/queue/*.md", "agents/revops_intel/knowledge_base/*.json"],
  "schedule_hint": "daily",
  "health": "unknown",
  "added": "<YYYY-MM-DD on implementation>"
}
```

- [ ] **Step 3: Validate JSON**

Run: `"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "import json; json.load(open('SOPs/AGENT/registry.json')); print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add SOPs/AGENT/registry.json
git commit -m "docs(sops): register revops_intel_standalone in registry.json"
```

---

### Task 6.3: Update LLM Provider Policy

**Files:**
- Modify: `D:/Projects/my-project/SOPs/AGENT/09-LLM-PROVIDER-POLICY.md`

- [ ] **Step 1: Append section**

Append at the end:

```markdown
## Free-tier provider default (added 2026-05-13)

**Groq Llama 3.3 70B** is the default free-tier provider for content extraction and outreach drafting pipelines (revops_intel/run.py, future ports to pe_intel/reddit_mine).

Claude Code via slash commands (`/revops-process`, `/pe-process`) remains the option for high-stakes one-offs where Opus-grade quality matters. Use the standalone pipeline daily; use Claude Code on the weekly Opus pass for quality benchmarking and prompt drift detection.

Rationale: Groq is fast (200+ tok/s), free up to 1k requests/day on 70B-versatile, and good enough for templated KB extraction + outreach drafting. Claude Code is preserved for judgement-heavy work where the cost is justified.
```

- [ ] **Step 2: Commit**

```bash
git add SOPs/AGENT/09-LLM-PROVIDER-POLICY.md
git commit -m "docs(sops): add Groq as default free-tier provider"
```

---

### Task 6.4: Update human-facing lead-systems doc

**Files:**
- Modify: `D:/Projects/my-project/SOPs/HUMAN/03-LEAD-SYSTEMS.md`

- [ ] **Step 1: Append section**

Append:

```markdown
## RevOps Intel Standalone Pipeline (2026-05-13)

**What it does:** Same as `/revops-process` but runs as a standalone Python script using free Groq Llama 3.3 70B instead of a Claude Code session.

**Run it:**
```
agents\revops_intel\run.bat
```
Or with limits / dry-run:
```
python -m agents.revops_intel.run --limit 5 --dry-run
```

**Where outputs land:**
- `agents/revops_intel/queue/*.md` — draft comments and DMs to review and post manually
- `agents/revops_intel/knowledge_base/*.json` — KB JSON files updated with new tool/pain/persona/jargon entries
- `agents/revops_intel/logs/*.jsonl` — call logs, voice violations, failed leads

**Recovery from rate limits:**
- If a run logs many 429 errors, wait 60s and re-run. Worst case: switch model in `llm_client.py` to `llama-3.1-8b-instant` (lower quality but higher free-tier limits).

**When to use `/revops-process` instead:**
- Weekly Opus-grade pass on the same hot leads for quality benchmarking
- Any one-off where you need Claude's judgment over Groq's speed (high-value lead, edge case persona, unusual offer match)
```

- [ ] **Step 2: Commit**

```bash
git add SOPs/HUMAN/03-LEAD-SYSTEMS.md
git commit -m "docs(sops): document standalone revops_intel pipeline usage"
```

---

### Task 6.5: Update daily routines

**Files:**
- Modify: `D:/Projects/my-project/SOPs/HUMAN/07-DAILY-ROUTINES.md`

- [ ] **Step 1: Insert under morning routine**

Find the morning routine section and add:

```markdown
### RevOps lead pipeline (daily, free-LLM)
- Run `agents\revops_intel\run.bat` (or `python -m agents.revops_intel.run`)
- Review queue files in `agents/revops_intel/queue/` written today
- Post HOT comments + send WARM DMs manually (queue is review-only)
- Investigate any `_FLAGGED_*.md` files before posting them
- Weekly (Sunday): run `/revops-process` for Opus-grade pass on the same week's hot leads — compare to standalone output, note any quality drift in mistakes.json
```

- [ ] **Step 2: Commit**

```bash
git add SOPs/HUMAN/07-DAILY-ROUTINES.md
git commit -m "docs(sops): slot revops_intel standalone into daily routine"
```

---

### Task 6.6: Update troubleshooting doc

**Files:**
- Modify: `D:/Projects/my-project/SOPs/HUMAN/09-TROUBLESHOOTING.md`

- [ ] **Step 1: Append 4 troubleshooting entries**

Use the exact entries from the spec's SOP touchpoint #6 (already drafted there — copy-paste). Append at end of file under a new `## RevOps Intel Standalone Pipeline` section.

- [ ] **Step 2: Commit**

```bash
git add SOPs/HUMAN/09-TROUBLESHOOTING.md
git commit -m "docs(sops): troubleshooting entries for revops_intel standalone"
```

---

### Task 6.7: Seed mistakes.json + dos_donts.json

**Files:**
- Modify: `D:/Projects/my-project/SOPs/AGENT/mistakes.json`
- Modify: `D:/Projects/my-project/SOPs/AGENT/dos_donts.json`

- [ ] **Step 1: Read mistakes.json**

Read current structure to know where to add entries.

- [ ] **Step 2: Add three entries to mistakes.json**

```json
{
  "id": "em_dash_leakage_llama_33",
  "system": "revops_intel_standalone",
  "discovered": "2026-05-13",
  "mistake": "Llama 3.3 70B emits em-dashes (—) in ~10% of outputs despite explicit prompt rules",
  "mitigation": "Regex post-cleanup in llm_client._enforce_voice is mandatory; do not rely on prompt alone",
  "files": ["agents/revops_intel/llm_client.py"]
},
{
  "id": "kb_write_race",
  "system": "revops_intel_standalone",
  "discovered": "2026-05-13",
  "mistake": "Concurrent KB JSON mutations clobber each other",
  "mitigation": "Always read fresh from disk per lead; never batch in memory; serial only, never thread",
  "files": ["agents/revops_intel/kb_merge.py", "agents/revops_intel/run.py"]
},
{
  "id": "prompt_drift_over_time",
  "system": "revops_intel_standalone",
  "discovered": "2026-05-13",
  "mistake": "Voice rules in prompts degrade as model versions drift; outputs slowly turn guru",
  "mitigation": "Weekly review of agents/revops_intel/logs/voice_violations.jsonl; tighten prompts if guru substitutions trend up",
  "files": ["agents/revops_intel/prompts/*.txt"]
}
```

- [ ] **Step 3: Add entries to dos_donts.json**

```json
{
  "do": "Read KB JSON files fresh from disk for each lead in revops_intel pipeline",
  "dont": "Batch KB mutations across leads in memory",
  "reason": "Lead-N's diff overwrites Lead-N-1's if both held in memory; atomic per-file write is the only safe pattern",
  "files": ["agents/revops_intel/kb_merge.py"]
}
```

- [ ] **Step 4: Validate JSON**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "import json; json.load(open('SOPs/AGENT/mistakes.json')); json.load(open('SOPs/AGENT/dos_donts.json')); print('ok')"
```
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add SOPs/AGENT/mistakes.json SOPs/AGENT/dos_donts.json
git commit -m "docs(sops): seed mistakes + dos_donts for revops_intel standalone"
```

---

### Task 6.8: Run sync.py to mirror SOPs to C: and E:

- [ ] **Step 1: Run sync**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" D:/Projects/my-project/SOPs/sync.py
```

Expected: prints sync summary for both drives. If errors, investigate before continuing.

- [ ] **Step 2: Verify**

Check timestamps on `C:/...SOPs/AGENT/02-AGENT-REGISTRY.md` and `E:/...SOPs/AGENT/02-AGENT-REGISTRY.md` are within the last minute (or whatever drives are configured in sync.py).

- [ ] **Step 3: No commit needed**

sync.py operates on external drives; the source-of-truth (D:) is already committed.

---

## Plan complete — final verification

After all chunks pass, run the full test suite and integration smoke once more:

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/revops_intel/tests/ -v
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.revops_intel.run --limit 3
```

Expected:
- ~30 tests pass
- 3 queue files written, 0 flagged (or 1 flagged — that's OK)
- KB JSON files updated
- No em-dashes, no emoji, no "DM me" in queue files

Then check spec's 7 success criteria are met. Tick them in the spec doc and commit.


