# PE Intel Agent Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Reddit scraper + heuristic lead scorer + Claude-driven analysis pipeline that turns r/privateequity (and adjacent finance subs) into a daily queue of insider-language comment + DM drafts for manual posting.

**Architecture:** A pipeline of small Python scripts owned by the `agents/pe_intel/` package. `scrape.py` pulls posts and full nested comment threads into SQLite. `score.py` applies cheap heuristic rules to flag hot leads. Two slash commands (`/pe-process`, `/pe-outcome`) drive Claude (Opus 4.7, via Claude Code) to read the hot leads, update a JSON knowledge base, and write comment + DM markdown files to a review queue. Zero external API spend — all LLM work runs inside the user's Claude Max subscription.

**Tech Stack:** Python 3.11, SQLite (stdlib `sqlite3`), `urllib.request` for unauth Reddit JSON API, optional `praw` fallback, `pytest` for tests, JSON files for the knowledge base, markdown files for slash commands.

**Spec:** `docs/superpowers/specs/2026-04-28-pe-intel-agent-design.md`

---

## File Structure

```
agents/pe_intel/
├── __init__.py
├── db.py                  # SQLite schema + helpers (~150 lines)
├── fetchers.py            # RedditFetcher interface + UrllibFetcher + PrawFetcher (~120 lines)
├── scrape.py              # Orchestrates fetch → walk → store (~150 lines)
├── score.py               # Heuristic scoring rules + apply (~120 lines)
├── pe_intel.db            # SQLite (generated, gitignored)
├── knowledge_base/
│   ├── tools.json         # {} on init
│   ├── pains.json         # {} on init
│   ├── personas.json      # {} on init
│   ├── jargon.json        # {} on init
│   └── playbook.md        # empty on init
├── queue/                 # generated markdown files (gitignored)
├── logs/                  # daily scrape logs (gitignored)
└── fixtures/
    └── sample_thread.json # captured real thread for tests

agents/pe_intel/tests/
├── __init__.py
├── conftest.py
├── test_db.py
├── test_fetchers.py       # uses fixture, no network
├── test_scrape.py         # uses fixture, no network
└── test_score.py          # pure unit tests on scoring rules

.claude/commands/
├── pe-process.md          # /pe-process slash command
└── pe-outcome.md          # /pe-outcome <post_id> <result>
```

**Boundary contracts:**
- `db.py` owns SQLite. Nothing else opens the DB file directly.
- `fetchers.py` owns Reddit I/O. Nothing else makes network calls.
- `scrape.py` glues fetcher + db together; pure orchestration, no domain logic.
- `score.py` is a pure function from a post dict to a `(score, reasons)` tuple, plus a small driver that applies it across all rows in `posts`.
- KB JSON files are written **only** by `/pe-process`. The Python scripts never touch them.

---

## Chunk 1: Project scaffold + db.py

### Task 1: Scaffold directories and gitignore

**Files:**
- Create: `agents/pe_intel/__init__.py` (empty)
- Create: `agents/pe_intel/tests/__init__.py` (empty)
- Create: `agents/pe_intel/knowledge_base/tools.json` with `{}`
- Create: `agents/pe_intel/knowledge_base/pains.json` with `{}`
- Create: `agents/pe_intel/knowledge_base/personas.json` with `{}`
- Create: `agents/pe_intel/knowledge_base/jargon.json` with `{}`
- Create: `agents/pe_intel/knowledge_base/playbook.md` (empty)
- Modify: `.gitignore` (add three lines)

- [ ] **Step 1.1: Create the directory tree**

```bash
mkdir -p agents/pe_intel/knowledge_base
mkdir -p agents/pe_intel/queue
mkdir -p agents/pe_intel/logs
mkdir -p agents/pe_intel/tests
mkdir -p agents/pe_intel/fixtures
```

- [ ] **Step 1.2: Create empty package + KB seed files**

`agents/pe_intel/__init__.py`:
```python
```

`agents/pe_intel/tests/__init__.py`:
```python
```

`agents/pe_intel/knowledge_base/tools.json`:
```json
{}
```

`agents/pe_intel/knowledge_base/pains.json`:
```json
{}
```

`agents/pe_intel/knowledge_base/personas.json`:
```json
{}
```

`agents/pe_intel/knowledge_base/jargon.json`:
```json
{}
```

`agents/pe_intel/knowledge_base/playbook.md`:
```markdown
# PE Outreach Playbook

(Empty — Claude appends learnings via `/pe-process` runs.)
```

- [ ] **Step 1.3: Add gitignore entries**

Append to `.gitignore`:
```
agents/pe_intel/pe_intel.db
agents/pe_intel/queue/
agents/pe_intel/logs/
```

- [ ] **Step 1.4: Commit scaffold**

```bash
git add agents/pe_intel/ .gitignore
git commit -m "feat(pe-intel): scaffold directory structure and KB seeds"
```

---

### Task 2: db.py — schema creation

**Files:**
- Create: `agents/pe_intel/db.py`
- Test: `agents/pe_intel/tests/test_db.py`

- [ ] **Step 2.1: Write the failing test for schema creation**

`agents/pe_intel/tests/test_db.py`:
```python
import sqlite3
from pathlib import Path

import pytest

from agents.pe_intel import db


@pytest.fixture
def conn(tmp_path):
    """Fresh in-memory-ish SQLite for each test."""
    db_path = tmp_path / "test.db"
    c = db.connect(db_path)
    db.init_schema(c)
    yield c
    c.close()


def test_init_schema_creates_all_tables(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = {r[0] for r in rows}
    assert table_names == {"posts", "comments", "lead_scores", "processed_leads"}


def test_init_schema_is_idempotent(conn):
    db.init_schema(conn)  # second call should not raise
    db.init_schema(conn)
```

- [ ] **Step 2.2: Run test to confirm failure**

```bash
cd D:/Projects/my-project
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_db.py -v
```
Expected: `ImportError` or `AttributeError` (db module / function missing).

- [ ] **Step 2.3: Implement minimal db.py**

`agents/pe_intel/db.py`:
```python
"""SQLite layer for PE Intel agent.

All DB I/O lives here. No other module opens pe_intel.db directly.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).parent / "pe_intel.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    post_id        TEXT PRIMARY KEY,
    subreddit      TEXT NOT NULL,
    author         TEXT,
    title          TEXT NOT NULL,
    selftext       TEXT,
    flair          TEXT,
    score          INTEGER,
    num_comments   INTEGER,
    created_utc    INTEGER NOT NULL,
    permalink      TEXT NOT NULL,
    scraped_at     INTEGER NOT NULL,
    last_updated   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_posts_created   ON posts(created_utc);
CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);

CREATE TABLE IF NOT EXISTS comments (
    comment_id   TEXT PRIMARY KEY,
    post_id      TEXT NOT NULL REFERENCES posts(post_id),
    parent_id    TEXT,
    author       TEXT,
    body         TEXT NOT NULL,
    score        INTEGER,
    depth        INTEGER NOT NULL,
    created_utc  INTEGER NOT NULL,
    scraped_at   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_comments_post   ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_author ON comments(author);

CREATE TABLE IF NOT EXISTS lead_scores (
    post_id       TEXT PRIMARY KEY REFERENCES posts(post_id),
    score         INTEGER NOT NULL,
    score_reasons TEXT NOT NULL,
    is_hot        INTEGER NOT NULL,
    scored_at     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scores_hot ON lead_scores(is_hot, score DESC);

CREATE TABLE IF NOT EXISTS processed_leads (
    post_id      TEXT PRIMARY KEY REFERENCES posts(post_id),
    queue_file   TEXT NOT NULL,
    processed_at INTEGER NOT NULL,
    posted_at    INTEGER,
    outcome      TEXT
);
"""


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
```

- [ ] **Step 2.4: Run tests to confirm pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_db.py -v
```
Expected: 2 passed.

- [ ] **Step 2.5: Commit**

```bash
git add agents/pe_intel/db.py agents/pe_intel/tests/test_db.py
git commit -m "feat(pe-intel): db schema + init"
```

---

### Task 3: db.py — post upsert + dedup query

**Files:**
- Modify: `agents/pe_intel/db.py` (add `upsert_post` + `post_needs_rescrape`)
- Modify: `agents/pe_intel/tests/test_db.py` (add tests)

- [ ] **Step 3.1: Add failing tests**

Note the **critical semantic split:** `upsert_post_metadata` only writes the listing-level row (does NOT bump `last_updated`). `mark_post_rescraped` is called AFTER a successful comment-tree fetch and bumps `last_updated`. This is what makes the re-scrape policy actually work — `last_updated` means "last time we got the comments," not "last time we touched the row."

Append to `agents/pe_intel/tests/test_db.py`:
```python
import time


SAMPLE_POST = {
    "post_id": "1abcde",
    "subreddit": "privateequity",
    "author": "u_test",
    "title": "Sample post",
    "selftext": "Body text",
    "flair": None,
    "score": 5,
    "num_comments": 3,
    "created_utc": 1714000000,
    "permalink": "https://reddit.com/r/privateequity/comments/1abcde/sample/",
}


def test_upsert_post_metadata_inserts_new(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    rows = conn.execute("SELECT post_id, title FROM posts").fetchall()
    assert len(rows) == 1
    assert rows[0]["post_id"] == "1abcde"


def test_upsert_post_metadata_updates_existing(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    updated = dict(SAMPLE_POST, score=99, num_comments=50)
    db.upsert_post_metadata(conn, updated)
    rows = conn.execute("SELECT score, num_comments FROM posts").fetchall()
    assert len(rows) == 1
    assert rows[0]["score"] == 99
    assert rows[0]["num_comments"] == 50


def test_upsert_post_metadata_does_not_bump_last_updated(conn):
    """CRITICAL: metadata-only upsert preserves prior last_updated value.
    Otherwise the re-scrape policy is broken — every metadata refresh would
    look like a fresh comments scrape."""
    db.upsert_post_metadata(conn, SAMPLE_POST)
    # Simulate "we did a comments scrape 30h ago"
    long_ago = int(time.time()) - 60 * 60 * 30
    conn.execute(
        "UPDATE posts SET last_updated = ? WHERE post_id = ?",
        (long_ago, "1abcde"),
    )
    conn.commit()
    # Now do another metadata upsert (e.g. listing was re-fetched)
    db.upsert_post_metadata(conn, dict(SAMPLE_POST, score=99))
    row = conn.execute(
        "SELECT last_updated FROM posts WHERE post_id = ?", ("1abcde",)
    ).fetchone()
    assert row["last_updated"] == long_ago  # NOT bumped


def test_mark_post_rescraped_bumps_last_updated(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    long_ago = int(time.time()) - 60 * 60 * 30
    conn.execute(
        "UPDATE posts SET last_updated = ? WHERE post_id = ?",
        (long_ago, "1abcde"),
    )
    conn.commit()
    db.mark_post_rescraped(conn, "1abcde")
    row = conn.execute(
        "SELECT last_updated FROM posts WHERE post_id = ?", ("1abcde",)
    ).fetchone()
    assert row["last_updated"] > long_ago  # bumped to ~now


def test_post_needs_rescrape_new_post(conn):
    assert db.post_needs_rescrape(conn, "neverseen") is True


def test_post_needs_rescrape_recent_active_post(conn):
    """Post <7d old, last comments-scraped >24h ago → needs rescrape."""
    db.upsert_post_metadata(conn, SAMPLE_POST)
    long_ago = int(time.time()) - 60 * 60 * 30
    conn.execute(
        "UPDATE posts SET created_utc = ?, last_updated = ? WHERE post_id = ?",
        (int(time.time()) - 86400 * 3, long_ago, "1abcde"),
    )
    conn.commit()
    assert db.post_needs_rescrape(conn, "1abcde") is True


def test_post_needs_rescrape_recent_active_post_just_scraped(conn):
    """Post <7d old, last comments-scraped <24h ago → skip."""
    db.upsert_post_metadata(conn, SAMPLE_POST)
    just_now = int(time.time()) - 60 * 60
    conn.execute(
        "UPDATE posts SET created_utc = ?, last_updated = ? WHERE post_id = ?",
        (int(time.time()) - 86400 * 3, just_now, "1abcde"),
    )
    conn.commit()
    assert db.post_needs_rescrape(conn, "1abcde") is False


def test_post_needs_rescrape_old_post_frozen(conn):
    """Post >30d old → never rescrape."""
    db.upsert_post_metadata(conn, SAMPLE_POST)
    old = int(time.time()) - 86400 * 45
    conn.execute(
        "UPDATE posts SET created_utc = ?, last_updated = ? WHERE post_id = ?",
        (old, old, "1abcde"),
    )
    conn.commit()
    assert db.post_needs_rescrape(conn, "1abcde") is False
```

- [ ] **Step 3.2: Run to confirm failure**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_db.py -v
```
Expected: tests fail with `AttributeError: module 'agents.pe_intel.db' has no attribute 'upsert_post'`.

- [ ] **Step 3.3: Implement upsert_post_metadata + mark_post_rescraped + post_needs_rescrape**

Append to `agents/pe_intel/db.py`:
```python
import time as _time


def upsert_post_metadata(conn: sqlite3.Connection, post: dict) -> None:
    """Insert or refresh listing-level fields. Does NOT touch last_updated.

    last_updated is reserved for "last successful comment-tree fetch" so the
    re-scrape policy works correctly. On INSERT, last_updated starts at 0
    (never scraped comments yet).
    """
    now = int(_time.time())
    conn.execute(
        """
        INSERT INTO posts (
            post_id, subreddit, author, title, selftext, flair,
            score, num_comments, created_utc, permalink,
            scraped_at, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ON CONFLICT(post_id) DO UPDATE SET
            score = excluded.score,
            num_comments = excluded.num_comments,
            selftext = excluded.selftext,
            scraped_at = excluded.scraped_at
            -- last_updated intentionally NOT updated here
        """,
        (
            post["post_id"], post["subreddit"], post.get("author"),
            post["title"], post.get("selftext"), post.get("flair"),
            post.get("score", 0), post.get("num_comments", 0),
            post["created_utc"], post["permalink"],
            now,
        ),
    )
    conn.commit()


def mark_post_rescraped(conn: sqlite3.Connection, post_id: str) -> None:
    """Call AFTER a successful comment-tree fetch. Bumps last_updated."""
    now = int(_time.time())
    conn.execute(
        "UPDATE posts SET last_updated = ? WHERE post_id = ?",
        (now, post_id),
    )
    conn.commit()


def post_needs_rescrape(conn: sqlite3.Connection, post_id: str) -> bool:
    """Re-scrape policy (last_updated = last successful comments fetch):
    - Never seen, or last_updated == 0 → True (never fetched comments yet)
    - Post <7 days old AND last_updated <24h ago → False
    - Post <7 days old AND last_updated >=24h ago → True
    - Post 7-30 days old AND last_updated <7d ago → False
    - Post 7-30 days old AND last_updated >=7d ago → True
    - Post >30 days old → False (frozen)
    """
    row = conn.execute(
        "SELECT created_utc, last_updated FROM posts WHERE post_id = ?",
        (post_id,),
    ).fetchone()
    if row is None or row["last_updated"] == 0:
        return True
    now = int(_time.time())
    age_days = (now - row["created_utc"]) / 86400
    since_update_h = (now - row["last_updated"]) / 3600
    if age_days > 30:
        return False
    if age_days < 7:
        return since_update_h >= 24
    return since_update_h >= 24 * 7
```

- [ ] **Step 3.4: Run tests**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_db.py -v
```
Expected: 9 passed (2 init + 7 post-related).

- [ ] **Step 3.5: Commit**

```bash
git add agents/pe_intel/db.py agents/pe_intel/tests/test_db.py
git commit -m "feat(pe-intel): post metadata upsert + mark-rescraped + re-scrape policy"
```

---

### Task 4: db.py — comment insert + hot lead query + processed_leads helpers

**Files:**
- Modify: `agents/pe_intel/db.py`
- Modify: `agents/pe_intel/tests/test_db.py`

- [ ] **Step 4.1: Add failing tests**

Append to `agents/pe_intel/tests/test_db.py`:
```python
SAMPLE_COMMENT = {
    "comment_id": "c_aaa",
    "post_id": "1abcde",
    "parent_id": "t3_1abcde",
    "author": "u_alice",
    "body": "This is a real comment, definitely longer than thirty characters.",
    "score": 4,
    "depth": 0,
    "created_utc": 1714000100,
}


def test_insert_comment(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.insert_comment(conn, SAMPLE_COMMENT)
    rows = conn.execute("SELECT body FROM comments WHERE comment_id = 'c_aaa'").fetchall()
    assert len(rows) == 1
    assert "real comment" in rows[0]["body"]


def test_insert_comment_idempotent(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.insert_comment(conn, SAMPLE_COMMENT)
    db.insert_comment(conn, SAMPLE_COMMENT)  # second call no-op
    count = conn.execute("SELECT COUNT(*) AS n FROM comments").fetchone()["n"]
    assert count == 1


def test_upsert_lead_score_and_hot_query(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.upsert_lead_score(conn, "1abcde", score=85, reasons=["pain_point", "automation_relevant"])
    hot = db.fetch_hot_unprocessed(conn)
    assert len(hot) == 1
    assert hot[0]["post_id"] == "1abcde"
    assert hot[0]["score"] == 85


def test_upsert_lead_score_excludes_processed(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.upsert_lead_score(conn, "1abcde", score=85, reasons=["pain_point"])
    db.mark_processed(conn, "1abcde", "queue/2026-04-28_test.md")
    hot = db.fetch_hot_unprocessed(conn)
    assert hot == []


def test_upsert_lead_score_excludes_cold(conn):
    db.upsert_post_metadata(conn, SAMPLE_POST)
    db.upsert_lead_score(conn, "1abcde", score=40, reasons=["pain_point"])
    hot = db.fetch_hot_unprocessed(conn)
    assert hot == []
```

- [ ] **Step 4.2: Run to confirm failure**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_db.py -v
```
Expected: new tests fail with AttributeError.

- [ ] **Step 4.3: Implement helpers**

Append to `agents/pe_intel/db.py`:
```python
import json as _json

HOT_THRESHOLD = 70


def insert_comment(conn: sqlite3.Connection, c: dict) -> None:
    """Insert a comment; no-op on conflict (idempotent re-scrape)."""
    now = int(_time.time())
    conn.execute(
        """
        INSERT OR IGNORE INTO comments (
            comment_id, post_id, parent_id, author, body, score,
            depth, created_utc, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            c["comment_id"], c["post_id"], c.get("parent_id"),
            c.get("author"), c["body"], c.get("score", 0),
            c["depth"], c["created_utc"], now,
        ),
    )
    conn.commit()


def upsert_lead_score(
    conn: sqlite3.Connection, post_id: str, score: int, reasons: list[str]
) -> None:
    now = int(_time.time())
    is_hot = 1 if score >= HOT_THRESHOLD else 0
    conn.execute(
        """
        INSERT INTO lead_scores (post_id, score, score_reasons, is_hot, scored_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            score = excluded.score,
            score_reasons = excluded.score_reasons,
            is_hot = excluded.is_hot,
            scored_at = excluded.scored_at
        """,
        (post_id, score, _json.dumps(reasons), is_hot, now),
    )
    conn.commit()


def fetch_hot_unprocessed(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    """Hot leads (is_hot=1) that have not been processed yet, highest score first."""
    rows = conn.execute(
        """
        SELECT p.post_id, p.subreddit, p.author, p.title, p.selftext,
               p.score AS reddit_score, p.num_comments, p.permalink,
               p.created_utc,
               s.score, s.score_reasons
        FROM lead_scores s
        JOIN posts p ON p.post_id = s.post_id
        LEFT JOIN processed_leads pl ON pl.post_id = s.post_id
        WHERE s.is_hot = 1 AND pl.post_id IS NULL
        ORDER BY s.score DESC, p.created_utc DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def mark_processed(conn: sqlite3.Connection, post_id: str, queue_file: str) -> None:
    now = int(_time.time())
    conn.execute(
        """
        INSERT INTO processed_leads (post_id, queue_file, processed_at)
        VALUES (?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            queue_file = excluded.queue_file,
            processed_at = excluded.processed_at
        """,
        (post_id, queue_file, now),
    )
    conn.commit()


def update_outcome(conn: sqlite3.Connection, post_id: str, outcome: str) -> None:
    now = int(_time.time())
    conn.execute(
        """
        UPDATE processed_leads
        SET outcome = ?, posted_at = COALESCE(posted_at, ?)
        WHERE post_id = ?
        """,
        (outcome, now, post_id),
    )
    conn.commit()
```

- [ ] **Step 4.4: Run all db tests**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_db.py -v
```
Expected: 12 passed.

- [ ] **Step 4.5: Commit**

```bash
git add agents/pe_intel/db.py agents/pe_intel/tests/test_db.py
git commit -m "feat(pe-intel): comment insert + hot-lead query + processed_leads helpers"
```

---

## Chunk 2: Reddit fetcher + scrape.py

### Task 5: Test fixtures (hand-crafted minimal + optional real capture)

**Files:**
- Create: `agents/pe_intel/fixtures/minimal_thread.json` (hand-crafted, always works)
- Create: `agents/pe_intel/fixtures/sample_thread.json` (optional, real capture)

The minimal fixture is the fixture all tests reference. It's deterministic, committed to the repo, and never depends on Reddit being friendly. The "real" fixture is a nice-to-have for richer manual exploration but is not required for tests to pass.

- [ ] **Step 5.1: Write the hand-crafted minimal fixture**

`agents/pe_intel/fixtures/minimal_thread.json`:
```json
[
  {
    "kind": "Listing",
    "data": {
      "children": [
        {
          "kind": "t3",
          "data": {
            "id": "test001",
            "subreddit": "private_equity",
            "author": "u_alice",
            "title": "Building AI-first infra at our PE firm",
            "selftext": "I'm a director at our firm. Looking for vendor recommendations.",
            "link_flair_text": "",
            "score": 25,
            "num_comments": 3,
            "created_utc": 1714000000,
            "permalink": "/r/private_equity/comments/test001/building_ai_first_infra/"
          }
        }
      ],
      "after": null
    }
  },
  {
    "kind": "Listing",
    "data": {
      "children": [
        {
          "kind": "t1",
          "data": {
            "id": "c001",
            "parent_id": "t3_test001",
            "author": "u_bob",
            "body": "We tried Chronograph last year — onboarding was fast but waterfall modeling was weak.",
            "score": 8,
            "created_utc": 1714000100,
            "replies": {
              "kind": "Listing",
              "data": {
                "children": [
                  {
                    "kind": "t1",
                    "data": {
                      "id": "c002",
                      "parent_id": "t1_c001",
                      "author": "u_carol",
                      "body": "Same here. Ended up wiring n8n + Claude on top to fill the gaps.",
                      "score": 5,
                      "created_utc": 1714000200,
                      "replies": ""
                    }
                  }
                ]
              }
            }
          }
        },
        {
          "kind": "t1",
          "data": {
            "id": "c003",
            "parent_id": "t3_test001",
            "author": "AutoModerator",
            "body": "Reminder to follow the sub rules. This comment must be skipped by the walker.",
            "score": 1,
            "created_utc": 1714000050,
            "replies": ""
          }
        },
        {
          "kind": "t1",
          "data": {
            "id": "c004",
            "parent_id": "t3_test001",
            "author": "[deleted]",
            "body": "[removed]",
            "score": 0,
            "created_utc": 1714000060,
            "replies": ""
          }
        },
        {
          "kind": "t1",
          "data": {
            "id": "c005",
            "parent_id": "t3_test001",
            "author": "u_dave",
            "body": "short",
            "score": 1,
            "created_utc": 1714000070,
            "replies": ""
          }
        }
      ]
    }
  }
]
```

This fixture exercises every walker code path: a valid top-level comment, a nested reply, an AutoModerator skip, a `[deleted]` skip, and a too-short body skip. Walker should yield exactly 2 comments (`c001` and `c002`).

- [ ] **Step 5.2: (Optional) Capture a real thread for richer manual checks**

If Reddit is reachable, also capture a real fixture:
```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -X utf8 -c "
import urllib.request, json, sys
url = 'https://www.reddit.com/r/private_equity/comments/1rzqon1/.json?limit=500'
req = urllib.request.Request(url, headers={'User-Agent': 'pe-intel-test/1.0'})
try:
    data = json.loads(urllib.request.urlopen(req, timeout=20).read())
    with open('agents/pe_intel/fixtures/sample_thread.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print('saved')
except Exception as e:
    print(f'skip: {e}')
"
```

If this fails or Reddit rate-limits, skip — tests don't depend on this fixture.

- [ ] **Step 5.3: Commit fixtures**

```bash
git add agents/pe_intel/fixtures/
git commit -m "test(pe-intel): minimal hand-crafted thread fixture (deterministic)"
```

---

### Task 6: fetchers.py — RedditFetcher interface + UrllibFetcher

**Files:**
- Create: `agents/pe_intel/fetchers.py`
- Test: `agents/pe_intel/tests/test_fetchers.py`

- [ ] **Step 6.1: Write the failing test**

`agents/pe_intel/tests/test_fetchers.py`:
```python
"""Fetcher tests use the hand-crafted minimal fixture — no live network."""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agents.pe_intel import fetchers


FIXTURE = Path(__file__).parent.parent / "fixtures" / "minimal_thread.json"


@pytest.fixture
def fixture_bytes():
    return FIXTURE.read_bytes()


@pytest.fixture
def fixture_json():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_urllib_fetcher_get_returns_parsed_json(fixture_bytes):
    """fetch_listing should return whatever JSON the URL returns, parsed."""
    f = fetchers.UrllibFetcher(user_agent="pe-intel-test/1.0", sleep_s=0)
    fake_response = MagicMock()
    fake_response.read.return_value = fixture_bytes
    fake_response.__enter__ = lambda s: fake_response
    fake_response.__exit__ = lambda *a: None
    with patch("urllib.request.urlopen", return_value=fake_response):
        result = f.fetch_listing("private_equity", "new", limit=100)
    # Result should be the parsed top-level JSON (a list, since our fixture is a thread JSON)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["kind"] == "Listing"


def test_urllib_fetcher_fetch_post_with_comments_returns_post_and_walked(fixture_bytes):
    f = fetchers.UrllibFetcher(user_agent="pe-intel-test/1.0", sleep_s=0)
    fake_response = MagicMock()
    fake_response.read.return_value = fixture_bytes
    fake_response.__enter__ = lambda s: fake_response
    fake_response.__exit__ = lambda *a: None
    with patch("urllib.request.urlopen", return_value=fake_response):
        post, comments = f.fetch_post_with_comments("test001", "private_equity")
    assert post["id"] == "test001"
    assert post["title"] == "Building AI-first infra at our PE firm"
    # Walker should yield exactly 2 valid comments (c001, c002); skips c003/c004/c005
    assert len(comments) == 2
    ids = {c["comment_id"] for c in comments}
    assert "t1_c001" in ids
    assert "t1_c002" in ids


def test_walk_comments_yields_required_fields(fixture_json):
    comments = list(fetchers.walk_comments(fixture_json[1], post_id="test001"))
    assert len(comments) == 2
    for c in comments:
        assert c["comment_id"].startswith("t1_")
        assert c["post_id"] == "test001"
        assert "body" in c
        assert "depth" in c
        assert c["author"] not in (None, "[deleted]", "AutoModerator")
        assert len(c["body"]) >= 30


def test_walk_comments_records_depth_correctly(fixture_json):
    """Top-level comment depth=0; nested reply depth=1."""
    comments = list(fetchers.walk_comments(fixture_json[1], post_id="test001"))
    by_id = {c["comment_id"]: c for c in comments}
    assert by_id["t1_c001"]["depth"] == 0
    assert by_id["t1_c002"]["depth"] == 1


def test_walk_comments_skips_automod_deleted_and_short(fixture_json):
    """Must skip c003 (AutoMod), c004 (deleted), c005 (too short)."""
    comments = list(fetchers.walk_comments(fixture_json[1], post_id="test001"))
    ids = {c["comment_id"] for c in comments}
    for skipped in ["t1_c003", "t1_c004", "t1_c005"]:
        assert skipped not in ids
```

- [ ] **Step 6.2: Run to confirm failure**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_fetchers.py -v
```
Expected: ImportError on `fetchers`.

- [ ] **Step 6.3: Implement fetchers.py**

`agents/pe_intel/fetchers.py`:
```python
"""Reddit fetchers + comment-tree walker.

Two implementations: UrllibFetcher (default, unauthenticated, cheap)
and PrawFetcher (fallback when rate-limited).
"""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Iterator, Protocol

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) jone-pe-intel/1.0"
MIN_COMMENT_LEN = 30
SKIP_AUTHORS = {None, "[deleted]", "[removed]", "AutoModerator"}


class RedditFetcher(Protocol):
    def fetch_listing(self, subreddit: str, listing: str,
                      limit: int = 100, t: str | None = None,
                      after: str | None = None) -> dict: ...

    def fetch_post_with_comments(self, post_id: str,
                                 subreddit: str) -> tuple[dict, list[dict]]: ...


class UrllibFetcher:
    def __init__(self, user_agent: str = USER_AGENT, sleep_s: float = 2.0):
        self.user_agent = user_agent
        self.sleep_s = sleep_s

    def _get(self, url: str) -> dict | list:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        time.sleep(self.sleep_s)
        return json.loads(data)

    def fetch_listing(self, subreddit, listing, limit=100, t=None, after=None):
        url = f"https://www.reddit.com/r/{subreddit}/{listing}.json?limit={limit}"
        if t:
            url += f"&t={t}"
        if after:
            url += f"&after={after}"
        return self._get(url)

    def fetch_post_with_comments(self, post_id, subreddit):
        url = (
            f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
            f"?limit=500&depth=10"
        )
        raw = self._get(url)
        post_data = raw[0]["data"]["children"][0]["data"]
        comments = list(walk_comments(raw[1], post_id=post_id))
        return post_data, comments


def walk_comments(comments_listing: dict, post_id: str,
                  parent_id: str | None = None, depth: int = 0
                  ) -> Iterator[dict]:
    """Recursively yield comment dicts ready for db.insert_comment."""
    children = comments_listing.get("data", {}).get("children", [])
    for child in children:
        kind = child.get("kind")
        if kind != "t1":  # skip "more" placeholders
            continue
        d = child.get("data", {})
        author = d.get("author")
        body = (d.get("body") or "").strip()
        if author in SKIP_AUTHORS or len(body) < MIN_COMMENT_LEN:
            # still recurse into replies — children may be valid
            replies = d.get("replies")
            if isinstance(replies, dict):
                yield from walk_comments(replies, post_id,
                                          parent_id=f"t1_{d.get('id')}",
                                          depth=depth + 1)
            continue
        yield {
            "comment_id": f"t1_{d.get('id')}",
            "post_id": post_id,
            "parent_id": parent_id or d.get("parent_id"),
            "author": author,
            "body": body,
            "score": d.get("score", 0),
            "depth": depth,
            "created_utc": int(d.get("created_utc", 0)),
        }
        replies = d.get("replies")
        if isinstance(replies, dict):
            yield from walk_comments(replies, post_id,
                                      parent_id=f"t1_{d.get('id')}",
                                      depth=depth + 1)


# PrawFetcher stub — wired in but not required for v1 unit tests.
class PrawFetcher:
    """Authenticated fallback for when unauth requests get blocked.

    Lazy-imports praw so the default install doesn't need it.
    """
    def __init__(self, env_path: str = "agents/reddit_bot.env"):
        import os
        from pathlib import Path
        if Path(env_path).exists():
            for line in Path(env_path).read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
        import praw  # type: ignore
        self.reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent=os.environ.get("REDDIT_USER_AGENT", USER_AGENT),
        )

    def fetch_listing(self, subreddit, listing, limit=100, t=None, after=None):
        raise NotImplementedError("PrawFetcher v1: add when unauth blocks happen")

    def fetch_post_with_comments(self, post_id, subreddit):
        raise NotImplementedError("PrawFetcher v1: add when unauth blocks happen")
```

- [ ] **Step 6.4: Run tests**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_fetchers.py -v
```
Expected: 5 passed.

- [ ] **Step 6.5: Commit**

```bash
git add agents/pe_intel/fetchers.py agents/pe_intel/tests/test_fetchers.py
git commit -m "feat(pe-intel): RedditFetcher interface + UrllibFetcher + comment-tree walker"
```

---

### Task 7: scrape.py — single-subreddit orchestration

**Files:**
- Create: `agents/pe_intel/scrape.py`
- Test: `agents/pe_intel/tests/test_scrape.py`

- [ ] **Step 7.1: Write the failing test**

`agents/pe_intel/tests/test_scrape.py`:
```python
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agents.pe_intel import db, scrape


FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample_thread.json"


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    db.init_schema(c)
    yield c
    c.close()


@pytest.fixture
def mock_fetcher():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    post_data = raw[0]["data"]["children"][0]["data"]

    f = MagicMock()
    # /new returns a listing with 1 child (the sample post)
    f.fetch_listing.return_value = {
        "data": {
            "children": [{"data": post_data}],
            "after": None,
        }
    }
    # /comments returns the post + walked comments
    from agents.pe_intel import fetchers
    walked = list(fetchers.walk_comments(raw[1], post_id=post_data["id"]))
    f.fetch_post_with_comments.return_value = (post_data, walked)
    return f


def test_scrape_subreddit_inserts_post_and_comments(conn, mock_fetcher):
    scrape.scrape_subreddit(conn, "private_equity", mock_fetcher,
                             listings=[("new", None)])
    posts = conn.execute("SELECT post_id FROM posts").fetchall()
    comments = conn.execute("SELECT comment_id FROM comments").fetchall()
    assert len(posts) == 1
    assert len(comments) > 0


def test_scrape_subreddit_skips_recently_scraped(conn, mock_fetcher):
    scrape.scrape_subreddit(conn, "private_equity", mock_fetcher,
                             listings=[("new", None)])
    initial_calls = mock_fetcher.fetch_post_with_comments.call_count
    # Run again immediately
    scrape.scrape_subreddit(conn, "private_equity", mock_fetcher,
                             listings=[("new", None)])
    # Listing fetch happens again (always); but comments fetch should NOT
    assert mock_fetcher.fetch_post_with_comments.call_count == initial_calls
```

- [ ] **Step 7.2: Run to confirm failure**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_scrape.py -v
```
Expected: ImportError on `scrape`.

- [ ] **Step 7.3: Implement scrape.py**

`agents/pe_intel/scrape.py`:
```python
"""Scrape orchestrator. Pure glue: fetcher → walker → db.

No domain logic. No LLM calls. Idempotent — re-runs are cheap and safe.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path

from . import db, fetchers

SUBREDDITS = [
    "privateequity",
    "private_equity",
    "investmentbanking",
    "FinancialCareers",
    "SecurityAnalysis",
]

DEFAULT_LISTINGS: list[tuple[str, str | None]] = [
    ("new", None),
    ("top", "month"),
]

LOG_DIR = Path(__file__).parent / "logs"


def _setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"scrape_{datetime.now():%Y-%m-%d}.log"
    logger = logging.getLogger("pe_intel.scrape")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        h = logging.FileHandler(log_file, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(h)
    return logger


def scrape_subreddit(
    conn,
    subreddit: str,
    fetcher: fetchers.RedditFetcher,
    listings: list[tuple[str, str | None]] = DEFAULT_LISTINGS,
    max_posts_per_listing: int = 100,
) -> dict:
    """Scrape one subreddit. Returns {posts_seen, posts_fetched, comments_added}."""
    log = _setup_logging()
    stats = {"posts_seen": 0, "posts_fetched": 0, "comments_added": 0, "errors": 0}

    for listing, t in listings:
        try:
            data = fetcher.fetch_listing(subreddit, listing,
                                          limit=max_posts_per_listing, t=t)
        except Exception as e:
            log.error(f"listing fetch failed r/{subreddit} {listing}: {e}")
            stats["errors"] += 1
            continue

        children = data.get("data", {}).get("children", [])
        for child in children:
            d = child.get("data", {})
            post_id = d.get("id")
            if not post_id:
                continue
            stats["posts_seen"] += 1

            # Refresh listing-level metadata (does NOT bump last_updated)
            db.upsert_post_metadata(conn, {
                "post_id": post_id,
                "subreddit": d.get("subreddit", subreddit),
                "author": d.get("author"),
                "title": (d.get("title") or "").strip(),
                "selftext": (d.get("selftext") or "").strip(),
                "flair": d.get("link_flair_text") or "",
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "created_utc": int(d.get("created_utc", 0)),
                "permalink": f"https://reddit.com{d.get('permalink', '')}",
            })

            if not db.post_needs_rescrape(conn, post_id):
                continue

            # Pull full comment tree (the expensive call)
            try:
                _, comments = fetcher.fetch_post_with_comments(post_id, subreddit)
            except Exception as e:
                log.error(f"comments fetch failed {post_id}: {e}")
                stats["errors"] += 1
                continue

            for c in comments:
                db.insert_comment(conn, c)
                stats["comments_added"] += 1
            # Only NOW bump last_updated — comments fetch succeeded
            db.mark_post_rescraped(conn, post_id)
            stats["posts_fetched"] += 1

    log.info(f"r/{subreddit} stats={stats}")
    return stats


def main() -> int:
    """CLI entry: scrape all configured subreddits."""
    conn = db.connect()
    db.init_schema(conn)
    fetcher = fetchers.UrllibFetcher()
    totals = {"posts_seen": 0, "posts_fetched": 0, "comments_added": 0, "errors": 0}
    for sub in SUBREDDITS:
        s = scrape_subreddit(conn, sub, fetcher)
        for k in totals:
            totals[k] += s[k]
    print(f"DONE: {totals}")
    error_rate = totals["errors"] / max(totals["posts_seen"], 1)
    if error_rate > 0.05:
        print(f"WARN: error rate {error_rate:.1%} > 5% — check logs")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 7.4: Run tests**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_scrape.py -v
```
Expected: 2 passed.

- [ ] **Step 7.5: Commit**

```bash
git add agents/pe_intel/scrape.py agents/pe_intel/tests/test_scrape.py
git commit -m "feat(pe-intel): scrape orchestrator with re-scrape policy"
```

---

## Chunk 3: Scoring

### Task 8: score.py — heuristic rules + apply

**Files:**
- Create: `agents/pe_intel/score.py`
- Test: `agents/pe_intel/tests/test_score.py`

- [ ] **Step 8.1: Write the failing test**

`agents/pe_intel/tests/test_score.py`:
```python
import pytest

from agents.pe_intel import db, score


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    db.init_schema(c)
    yield c
    c.close()


def make_post(**overrides):
    base = {
        "post_id": "test1", "subreddit": "private_equity", "author": "u_x",
        "title": "Generic title", "selftext": "Generic body.",
        "flair": "", "score": 1, "num_comments": 0,
        "created_utc": 1714000000,
        "permalink": "https://reddit.com/test",
    }
    base.update(overrides)
    return base


# --- Rule-by-rule unit tests on score_post() ---

def test_vendor_evaluation_signal():
    post = make_post(title="Looking for alternatives to Pitchbook")
    s, reasons = score.score_post(post)
    assert "vendor_evaluation" in reasons
    assert s >= 25


def test_active_build_signal():
    post = make_post(title="Building AI-first infrastructure at our PE firm")
    s, reasons = score.score_post(post)
    assert "active_build" in reasons


def test_decision_maker_signal():
    post = make_post(selftext="I'm a director at a small fund and need help.")
    _, reasons = score.score_post(post)
    assert "decision_maker_signal" in reasons


def test_career_question_penalty():
    post = make_post(title="Breaking into PE from consulting", selftext="career advice please")
    s, _ = score.score_post(post)
    assert s < 30


def test_career_penalty_catches_mba_and_into_pe_with_punctuation():
    """Word-boundary regex must catch MBA and 'into PE' regardless of punctuation."""
    for title in ["MBA holder pivoting to PE", "How to pivot into PE?",
                  "Into PE from consulting"]:
        s, reasons = score.score_post(make_post(title=title))
        assert "career_question_penalty" in reasons, f"missed: {title}"


def test_score_is_always_0_to_100():
    """No matter what we throw at it, score stays in [0, 100]."""
    extreme = make_post(
        title="Building automation infra rolling out — vendor recommendations vs alternatives",
        selftext="I'm a director at our firm. We're a fund using Claude. Manual process automating workflow.",
        num_comments=200, score=500,
    )
    s, _ = score.score_post(extreme)
    assert 0 <= s <= 100

    negative = make_post(title="Breaking into PE — career advice MBA into PE")
    s, _ = score.score_post(negative)
    assert 0 <= s <= 100


def test_high_signal_post_is_hot():
    post = make_post(
        title="Building AI infra at our PE firm — vendor recommendations?",
        selftext="I'm an operating director at a $1B fund. Currently evaluating "
                 "alternatives to Pitchbook. Our firm uses Claude already.",
        score=20, num_comments=30,
    )
    s, reasons = score.score_post(post)
    assert s >= 70  # is hot
    assert "vendor_evaluation" in reasons
    assert "active_build" in reasons
    assert "decision_maker_signal" in reasons
    assert "speaks_for_firm" in reasons
    assert "automation_relevant" in reasons
    assert "hot_thread" in reasons


# --- Integration test: apply_to_db ---

def test_apply_scoring_writes_lead_scores(conn):
    # Insert 3 posts
    for i, p in enumerate([
        make_post(post_id="hot1",
                  title="Building AI-first infra — alternatives to Pitchbook?",
                  selftext="I'm a partner at our firm. Using Claude.",
                  num_comments=30, score=10),
        make_post(post_id="cold1", title="Career advice: breaking into PE"),
        make_post(post_id="mid1", title="Anyone using Chronograph?"),
    ]):
        db.upsert_post(conn, p)
    score.apply_to_db(conn)
    rows = conn.execute(
        "SELECT post_id, score, is_hot FROM lead_scores ORDER BY score DESC"
    ).fetchall()
    by_id = {r["post_id"]: r for r in rows}
    assert by_id["hot1"]["is_hot"] == 1
    assert by_id["cold1"]["is_hot"] == 0
    assert by_id["cold1"]["score"] < 30
```

- [ ] **Step 8.2: Run to confirm failure**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_score.py -v
```
Expected: ImportError on `score`.

- [ ] **Step 8.3: Implement score.py**

`agents/pe_intel/score.py`:
```python
"""Heuristic lead scoring.

Pure: score_post(dict) -> (int, list[str]). Driver: apply_to_db rescores
every post in the DB. Cheap, runs in milliseconds for thousands of posts.

Keyword lists are checked via word-boundary regexes (not substring) so
"into PE" matches "...transition into PE." but not "intoxicated person".
"""
from __future__ import annotations

import re

from . import db


# Substring-OK keywords (multi-word phrases — substring is fine)
VENDOR_PHRASES = [
    "evaluating", "looking for", "alternatives to", "anyone using",
    "experiences with", "vendor", "better than", "recommendations",
]
PAIN_PHRASES = [
    "manual process", "automate", "automating", "struggling with",
    "headache", "wasting time", "scaling",
]
BUILD_PHRASES = [
    "rolling out", "implementing", "ai-first",
    "infrastructure", "set up", "setting up",
]
AUTOMATION_PHRASES = [
    "claude", "chatgpt", "openai", "automation", "workflow",
    "n8n", "make.com", "zapier", "copilot", "pitchbook",
    "chronograph", "preqin", "73 strings",
]
CAREER_PHRASES = [
    "breaking into", "career advice", "internship", "interview prep",
    "resume", "cv review", "what college", "career in",
    "looking for material", "transition into pe", "transition to pe",
]

# Word-boundary regexes (where substring would be wrong)
BUILDING_RX = re.compile(r"\bbuilding\b", re.I)
MANUAL_RX = re.compile(r"\bmanual\b", re.I)
AI_RX = re.compile(r"\bai\b", re.I)  # avoid "main", "available", etc
VS_RX = re.compile(r"\bvs\b\.?", re.I)
MBA_RX = re.compile(r"\bmba\b", re.I)
INTO_PE_RX = re.compile(r"\binto pe\b", re.I)

DECISION_RX = re.compile(
    r"\bi'?m\s+an?\s+(operating|partner|principal|vp|director|cfo|"
    r"head of|founder|managing|senior)",
    re.I,
)
FIRM_RX = re.compile(r"\bour firm\b|\bwe'?re a\b|\bat our fund\b", re.I)


def _has_phrase(text: str, phrases: list[str]) -> bool:
    return any(p in text for p in phrases)


def score_post(post: dict) -> tuple[int, list[str]]:
    title = (post.get("title") or "").lower()
    body = (post.get("selftext") or "").lower()
    blob = f"{title}\n{body}"

    points = 0
    reasons: list[str] = []

    if _has_phrase(blob, VENDOR_PHRASES) or VS_RX.search(blob):
        points += 25
        reasons.append("vendor_evaluation")
    if _has_phrase(blob, PAIN_PHRASES) or MANUAL_RX.search(blob):
        points += 20
        reasons.append("pain_point")
    if _has_phrase(blob, BUILD_PHRASES) or BUILDING_RX.search(blob):
        points += 25
        reasons.append("active_build")
    if DECISION_RX.search(post.get("selftext") or ""):
        points += 20
        reasons.append("decision_maker_signal")
    if FIRM_RX.search(post.get("selftext") or ""):
        points += 10
        reasons.append("speaks_for_firm")
    if _has_phrase(blob, AUTOMATION_PHRASES) or AI_RX.search(blob):
        points += 15
        reasons.append("automation_relevant")

    nc = post.get("num_comments", 0) or 0
    rs = post.get("score", 0) or 0
    if nc >= 10 and rs >= 5:
        points += 10
        reasons.append("active_thread")
    if nc >= 25:
        points += 5
        reasons.append("hot_thread")

    if (_has_phrase(title, CAREER_PHRASES) or
            MBA_RX.search(title) or INTO_PE_RX.search(title)):
        points -= 40
        reasons.append("career_question_penalty")

    points = max(0, min(100, points))
    return points, reasons


def apply_to_db(conn) -> dict:
    """Re-score every post in the DB. Returns {scored, hot}."""
    rows = conn.execute(
        "SELECT post_id, title, selftext, score, num_comments FROM posts"
    ).fetchall()
    hot = 0
    for r in rows:
        pts, reasons = score_post(dict(r))
        db.upsert_lead_score(conn, r["post_id"], pts, reasons)
        if pts >= db.HOT_THRESHOLD:
            hot += 1
    return {"scored": len(rows), "hot": hot}


def main() -> int:
    conn = db.connect()
    db.init_schema(conn)
    stats = apply_to_db(conn)
    print(f"DONE: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 8.4: Run tests**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest agents/pe_intel/tests/test_score.py -v
```
Expected: 9 passed.

- [ ] **Step 8.5: Commit**

```bash
git add agents/pe_intel/score.py agents/pe_intel/tests/test_score.py
git commit -m "feat(pe-intel): heuristic lead scoring with rule-by-rule tests"
```

---

## Chunk 4: Slash commands + smoke run

### Task 9: /pe-process slash command

**Files:**
- Create: `.claude/commands/pe-process.md`

The slash command is a markdown instruction file that Claude Code reads when the user types `/pe-process`. It tells Claude what to do, in what order, with what guardrails.

- [ ] **Step 9.1: Write `.claude/commands/pe-process.md`**

```markdown
---
description: Run the PE Intel pipeline — scrape, score, then read hot leads, update KB, and write comment+DM markdown to the queue.
---

You are running the PE Intel agent. The user has invoked `/pe-process`.

## Steps (in order)

### 1. Refresh data
Run from project root:
```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.pe_intel.scrape
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.pe_intel.score
```

If scrape exits 1 (>5% errors), STOP and report to user.

### 2. Pull hot leads (use the Python helpers — never raw SQL)

Run via Bash to get the hot leads as JSON:
```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "
import json
from agents.pe_intel import db
conn = db.connect()
print(json.dumps(db.fetch_hot_unprocessed(conn, limit=20), indent=2))
"
```

For each hot lead's top comments, run:
```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "
import json
from agents.pe_intel import db
conn = db.connect()
rows = conn.execute('SELECT author, body, score, depth FROM comments WHERE post_id = ? ORDER BY score DESC LIMIT 10', ('<post_id>',)).fetchall()
print(json.dumps([dict(r) for r in rows], indent=2))
"
```

Use `db.mark_processed(conn, post_id, queue_file)` for writes — never construct INSERT SQL inline.

### 3. Load knowledge base
Read these files into memory:
- `agents/pe_intel/knowledge_base/tools.json`
- `agents/pe_intel/knowledge_base/pains.json`
- `agents/pe_intel/knowledge_base/personas.json`
- `agents/pe_intel/knowledge_base/jargon.json`
- `agents/pe_intel/knowledge_base/playbook.md`

### 4. For each hot lead, in score order:

#### 4a. EXTRACT — what new knowledge does this thread teach?
Scan post + top comments for:
- **New tools mentioned** (Pitchbook, Chronograph, 73 Strings, Claude, n8n, etc.) — if not in `tools.json`, add. If present, increment `mention_count` (only +1 per post_id) and append a quote to `example_quotes`.
- **New pain patterns** — if a recurring complaint pattern emerges, add to `pains.json` with persona + workaround + automation_opportunity. Use snake_case slug.
- **New personas** — if the post author or top commenters use unfamiliar titles/firm-size language, add or refine entries in `personas.json`.
- **New jargon** — terms like "EBITDA bridge", "target primer", "secondaries". Set `use_in_outreach=true` only if it's a natural identifier (not a try-hard term like MOIC or carry).

Write updates back to the JSON files.

#### 4b. GENERATE — write outreach
Match the post to a persona slug + pain slug from the KB.

Write the **Reddit comment**: value-first, no pitch, references specific tools or experiences from the KB if relevant. Plain prose, ~80–200 words. Avoid emoji and consultant-speak. Sound like a peer who's actually built this stuff (Jone has — accounting, real estate, fintech, events, trades).

Write the **Reddit DM**: warmer, references the user's specific situation, leads with a concrete proof point ("I've built this exact stack twice" / "saved another firm $250K mis-decision"), offers free 30-min audit. ~80–150 words. Sign as Jone.

#### 4c. SAVE — write queue file
Path: `agents/pe_intel/queue/YYYY-MM-DD_<author_sanitized>_<post_id>.md`

Format:
```markdown
---
post_id: <id>
author: u/<name>
url: <permalink>
score: <0-100>
reasons: [<tag>, ...]
persona_match: <persona_slug>
pain_match: <pain_slug>
generated_at: <iso8601>
---

## Original post
**<title>**
> <body>

## Why this lead is hot
- <bullet>
- <bullet>

## Top relevant comments (insider context)
- u/<name> (<N> upvotes): "<snippet>"
- u/<name> (<N> upvotes): "<snippet>"

## Suggested REDDIT COMMENT
> <comment>

## Suggested REDDIT DM
> <dm>

## Knowledge updates from this thread
- Added tool: "<name>"
- Added pain: "<slug>"
- Added jargon: "<term>"
```

#### 4d. MARK PROCESSED
Use the Python helper:
```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "
from agents.pe_intel import db
conn = db.connect()
db.mark_processed(conn, '<post_id>', '<queue_file_path>')
"
```

### 5. APPEND to playbook.md
At the bottom, add a dated section with what you learned today: which post types are showing up most, any new tool/pain patterns, any DM angles you tried. Free-form. Future runs read this for context.

### 6. Print summary
| post_id | author | score | reasons | queue_file |
|---|---|---|---|---|

Plus: KB diff stats (N tools added, N pains added, N personas updated, N jargon added).

## Guardrails
- Do NOT post anything to Reddit. The queue is review-only.
- DB writes go through `db.mark_processed` only. Never modify `posts`, `comments`, or `lead_scores` from this slash command — those are owned by `scrape.py` and `score.py`.
- Do NOT regenerate queue files for posts already in `processed_leads` (`fetch_hot_unprocessed` filters them out for you).
- KB JSON files (`tools.json`, `pains.json`, `personas.json`, `jargon.json`) are written ONLY by this slash command. The Python scripts never touch them. This invariant is enforced by convention.
- If a post body contains PII (real names, emails, phone numbers) of someone other than the author, redact it in the queue file.
```

- [ ] **Step 9.2: Commit**

```bash
git add .claude/commands/pe-process.md
git commit -m "feat(pe-intel): /pe-process slash command"
```

---

### Task 10: /pe-outcome slash command

**Files:**
- Create: `.claude/commands/pe-outcome.md`

- [ ] **Step 10.1: Write `.claude/commands/pe-outcome.md`**

```markdown
---
description: Track the outcome of a posted PE Intel lead — updates processed_leads.outcome.
argument-hint: <post_id> <outcome>
---

User invoked: `/pe-outcome $ARGUMENTS`

Parse `$ARGUMENTS` as `<post_id> <outcome>` where outcome is one of:
- `responded` — they replied to the comment
- `dmd_back` — they replied to the DM
- `ghosted` — no response after 7+ days
- `client` — converted to a paying client
- `unsubscribed` — asked you to stop

If outcome is not in this list, print the list and stop.

Run:
```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "
from agents.pe_intel import db
conn = db.connect()
db.update_outcome(conn, '<post_id>', '<outcome>')
print('updated')
"
```

After updating, query and print the lead's queue file path so the user can re-read what was sent:
```sql
SELECT queue_file FROM processed_leads WHERE post_id = ?;
```
```

- [ ] **Step 10.2: Commit**

```bash
git add .claude/commands/pe-outcome.md
git commit -m "feat(pe-intel): /pe-outcome slash command for outcome tracking"
```

---

### Task 11: Smoke test on real data

- [ ] **Step 11.1: Run scrape against r/private_equity**

```bash
cd D:/Projects/my-project
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.pe_intel.scrape
```

Expected output: `DONE: {'posts_seen': N, 'posts_fetched': M, 'comments_added': K, 'errors': 0}`. N should be ≥50 across all 5 subs.

If errors > 5%, check `agents/pe_intel/logs/scrape_*.log`.

- [ ] **Step 11.2: Run scoring**

```bash
cd D:/Projects/my-project
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.pe_intel.score
```

Expected: `DONE: {'scored': N, 'hot': M}` where M is roughly 5-15% of N.

- [ ] **Step 11.3: Sanity-check the hot leads**

```bash
cd D:/Projects/my-project
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "
from agents.pe_intel import db
conn = db.connect()
rows = db.fetch_hot_unprocessed(conn)
for r in rows[:10]:
    print(f\"[{r['score']:>3}] {r['title'][:80]} | {r['score_reasons']}\")"
```

Manual check: do these 10 posts look like genuine buying signals? If career-question posts are surfacing, tighten `CAREER_KW` in `score.py` and re-run.

- [ ] **Step 11.4: Test `/pe-process` end-to-end**

In Claude Code, type `/pe-process`. Verify:
- Scrape + score actually runs
- Queue files appear in `agents/pe_intel/queue/`
- KB JSON files have new entries
- `processed_leads` table has new rows

- [ ] **Step 11.5: Memory update**

(`pe_intel.db` is gitignored — no commit needed for the data file. Only commit any code tweaks discovered during the smoke test.)

Write `C:/Users/Admin/.claude/projects/D--Projects-my-project/memory/pe_intel_agent.md` with:
- Location: `agents/pe_intel/`
- Daily scrape: `python -m agents.pe_intel.scrape && python -m agents.pe_intel.score`
- Slash commands: `/pe-process` (generate queue), `/pe-outcome <post_id> <result>` (track outcome)
- KB structure: 4 JSON files in `knowledge_base/` + `playbook.md`
- Output: markdown queue files in `queue/`

Then add a one-line index entry to `MEMORY.md`:
```
- [PE Intel Agent](pe_intel_agent.md) — Reddit PE-niche lead pipeline; daily scrape + /pe-process for outreach drafts
```

Commit:
```bash
git add C:/Users/Admin/.claude/projects/D--Projects-my-project/memory/
git commit -m "docs(memory): add PE Intel agent reference"
```

---

## Done criteria

- [ ] All Python tests pass: `pytest agents/pe_intel/tests/ -v` → 25 passed (9 db + 5 fetchers + 2 scrape + 9 score).
- [ ] `python -m agents.pe_intel.scrape` runs clean against live Reddit (or with rate-limit fallback noted).
- [ ] `python -m agents.pe_intel.score` produces a sensible hot-lead list (5-15% hot rate).
- [ ] `/pe-process` invoked manually generates ≥3 queue files with comment + DM in the format above.
- [ ] KB JSON files have non-empty entries after first `/pe-process` run.
- [ ] Memory doc + MEMORY.md index entry created so future Claude sessions know about the system.
