# PE Intel Agent — Design Spec

**Date:** 2026-04-28
**Owner:** Jone Andrew Harris
**Status:** Approved for implementation

---

## Problem

Cold outreach to private equity prospects on Reddit currently sounds generic. The replies are formulaic ("happy to share what's worked", "free 30-min audit") and lack the insider vocabulary, specific tool references, and pain-point framing that make a PE buyer trust the sender. We need an automation layer that learns the language and tooling landscape of the PE community on Reddit, then uses that knowledge to generate outreach that reads like it came from a peer.

## Goal

Build a Python + Claude Code pipeline that:
1. Continuously scrapes posts and full nested comment threads from a cluster of PE-adjacent subreddits.
2. Uses Claude (Opus 4.7, via interactive Claude Code sessions) to extract a structured knowledge base of tools, pain points, personas, and jargon used by PE practitioners.
3. Heuristically scores each new post for buyer intent, surfaces the top 10–20 hot leads per day.
4. Generates a Reddit comment + DM for each hot lead, written in PE-native language using the accumulated knowledge base.
5. Drops outputs in a review queue (markdown files) for manual posting — no auto-posting in v1.

## Non-Goals

- No automated Reddit posting (Reddit's spam detection on new accounts is brutal; manual review is mandatory).
- No vector database / semantic search (out of scope for v1; tag-based queries against SQLite are sufficient).
- No paid LLM API spend — agent uses Claude Code (the user's existing Max subscription), not the Anthropic API directly.
- No multi-platform expansion (LinkedIn, Twitter) in v1 — Reddit only.
- No CRM integration — outcome tracking lives in SQLite.

## Architecture

### File layout

```
agents/pe_intel/
├── scrape.py              # cron: pulls posts + nested comments → SQLite
├── db.py                  # SQLite schema + helpers
├── score.py               # heuristic lead scoring
├── pe_intel.db            # SQLite (posts, comments, lead_scores, processed_leads)
├── knowledge_base/
│   ├── tools.json         # {tool_name: {category, mentions, sentiment, quotes}}
│   ├── pains.json         # {pain_pattern: {frequency, personas, automation_opportunity}}
│   ├── personas.json      # {persona: {title_variants, firm_signals, pains}}
│   ├── jargon.json        # {term: {def, use_in_outreach}}
│   └── playbook.md        # accumulating notes on what converts in PE outreach
├── queue/
│   └── YYYY-MM-DD_<author>_<post_id>.md   # comment + DM for one hot lead
└── logs/
    └── scrape_YYYY-MM-DD.log

.claude/commands/
├── pe-process.md          # /pe-process — full analysis run
└── pe-outcome.md          # /pe-outcome <post_id> <result> — track outreach results
```

### Data flow

```
[ cron 6am ]                          [ user, when ready ]
     │                                       │
     ▼                                       ▼
 scrape.py                              Claude Code
     │                                       │
     ▼                                  /pe-process
 pe_intel.db                                 │
     │                                       ▼
     │                              read DB + KB
     ▼                                       │
 score.py                                    ▼
     │                            update KB with today's
     ▼                            new tools/pains/jargon
 hot leads flagged                           │
                                             ▼
                                  generate comment + DM
                                  for each hot lead
                                             │
                                             ▼
                                      queue/*.md files
                                             │
                                             ▼
                                  user reads & posts manually
                                             │
                                             ▼
                              /pe-outcome <post_id> <result>
                                             │
                                             ▼
                              processed_leads.outcome updated
```

### Stack

- **Language:** Python 3.11 (existing user setup at `C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe`)
- **Storage:** SQLite (single file, no server). JSON for knowledge base (human-readable, easy diff in git).
- **Scraping:** `urllib.request` + Reddit's public JSON API. No auth needed; UA string only. Falls back to `praw` with `agents/reddit_bot.env` creds if rate-limited.
- **Analysis:** Claude Code (Opus 4.7) interactive sessions via `/pe-process` slash command. No Anthropic API calls.
- **Scheduling:** Windows Task Scheduler or manual `.bat` runner for `scrape.py`. `/pe-process` is on-demand by the user.

## Components

### 1. `scrape.py`

**Purpose:** Pull new posts + full comment threads from PE cluster subreddits into SQLite. Pure I/O. No LLM calls. No outreach generation.

**Subreddits scraped:**
- r/privateequity
- r/private_equity
- r/investmentbanking
- r/FinancialCareers
- r/SecurityAnalysis

**Per subreddit, per run:**
1. Fetch `/new.json?limit=100` and `/top.json?t=month&limit=100`.
2. Dedupe against `posts` table; skip posts re-scraped within 24h unless they're <7 days old (active threads need more frequent re-fetch).
3. For each post needing fetch, request `/comments/<post_id>.json?limit=500&depth=10`.
4. Walk the comment tree recursively. Skip `[deleted]`, `[removed]`, AutoModerator, and comments under 30 chars.
5. Insert posts and comments into SQLite as one transaction.
6. Sleep 2s between Reddit requests.

**Re-scrape policy:**
- Posts <7 days old → re-fetch comments daily.
- Posts 7–30 days old → re-fetch weekly.
- Posts >30 days old → frozen, never re-fetch.

**Caps:**
- Max 100 posts/subreddit/run = 500 posts/day ceiling.
- Max 500 comments/post (Reddit's `MoreComments` collapses past that; v1 doesn't expand them).
- Initial backfill: paginate `/new.json` via the `after=` cursor and supplement with `/top.json?t=year` filtered to ≤90 days. Process oldest-first, stop at 90-day cutoff.

**Fetcher abstraction:** `scrape.py` defines a `RedditFetcher` interface with two implementations: `UrllibFetcher` (default, unauthenticated) and `PrawFetcher` (fallback when rate-limited, uses creds from `agents/reddit_bot.env`). The fallback is wired in from day one, not bolted on later.

**Errors:**
- Network error on a single post → log + continue.
- Malformed JSON → log + skip; alert if >5% of posts in one run fail.
- DB write fails → rollback whole run (no partial state).
- Logs go to `agents/pe_intel/logs/scrape_YYYY-MM-DD.log` (one file per day, append).

### 2. `db.py`

**Purpose:** Schema definition, connection helpers, common queries.

**Schema:**

```sql
CREATE TABLE posts (
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
CREATE INDEX idx_posts_created   ON posts(created_utc);
CREATE INDEX idx_posts_subreddit ON posts(subreddit);

CREATE TABLE comments (
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
CREATE INDEX idx_comments_post   ON comments(post_id);
CREATE INDEX idx_comments_author ON comments(author);

CREATE TABLE lead_scores (
    post_id       TEXT PRIMARY KEY REFERENCES posts(post_id),
    score         INTEGER NOT NULL,
    score_reasons TEXT NOT NULL,        -- JSON array
    is_hot        INTEGER NOT NULL,     -- 1 if score >= 70
    scored_at     INTEGER NOT NULL
);
CREATE INDEX idx_scores_hot ON lead_scores(is_hot, score DESC);

CREATE TABLE processed_leads (
    post_id      TEXT PRIMARY KEY REFERENCES posts(post_id),
    queue_file   TEXT NOT NULL,
    processed_at INTEGER NOT NULL,
    posted_at    INTEGER,
    outcome      TEXT
);
```

### 3. `score.py`

**Purpose:** Cheap heuristic scoring of every post in the DB. Filters 500/day → top 10–20 for Claude.

**Rules (additive, capped 0–100):**

| Signal | Pattern | Points | Reason tag |
|---|---|---|---|
| Vendor evaluation | "evaluating", "alternatives to", "anyone using", "vs", "vendor" | +25 | `vendor_evaluation` |
| Pain point | "manual process", "automate", "struggling with", "wasting time" | +20 | `pain_point` |
| Active build | "building", "rolling out", "implementing", "ai-first", "infrastructure" | +25 | `active_build` |
| Decision-maker self-id | regex `i'?m an? (operating\|partner\|principal\|vp\|director\|cfo\|head of\|founder)` | +20 | `decision_maker_signal` |
| Speaks for firm | regex `our firm\|we'?re a` | +10 | `speaks_for_firm` |
| Automation-relevant | mentions claude/chatgpt/ai/automation/workflow/n8n/make/zapier/copilot/pitchbook/chronograph | +15 | `automation_relevant` |
| Active thread | num_comments ≥10 AND reddit_score ≥5 | +10 | `active_thread` |
| Hot thread | num_comments ≥25 | +5 | `hot_thread` |
| Career-question penalty | "breaking into", "career advice", "internship", "interview prep", "resume", "cv review", "what college", "mba", "into pe" | -40 | `career_question_penalty` |

**Hot threshold:** score ≥ 70.

**Re-score:** Every post on first scrape, plus on every re-scrape (engagement signals can bump it). `lead_scores` rows are upserted by `post_id` — one row per post, always reflects the latest score.

**Why heuristic, not Claude:** runs in milliseconds for 500 posts; Claude is reserved for the deep read on the survivors. Tunable later as `processed_leads.outcome` data accumulates.

### 4. Knowledge base (JSON files)

Four files, all in `knowledge_base/`. Append-only growth — entries can be updated but never deleted.

**Write invariant:** KB JSON files are written **only** by `/pe-process`. `scrape.py` and `score.py` never touch them. This eliminates concurrency concerns between cron and interactive sessions.

**`mention_count` semantics:** increments only on first encounter per `post_id`. If the same tool is mentioned in 5 different comments on the same post, that's still +1. This makes `mention_count = 1` a reliable hallucination signal during monthly KB review.

**`tools.json`** — schema per entry:
```json
{
  "<tool_name>": {
    "category": "portfolio_reporting|crm|ai_assistant|data|other",
    "first_seen": "YYYY-MM-DD",
    "mention_count": 0,
    "sentiment_summary": "free-text from Claude",
    "common_complaints": ["..."],
    "common_praise": ["..."],
    "example_quotes": [{"author": "u/x", "post_id": "...", "snippet": "..."}]
  }
}
```

**`pains.json`** — schema per entry:
```json
{
  "<pain_slug>": {
    "frequency": 0,
    "personas_affected": ["..."],
    "current_workarounds": ["..."],
    "automation_opportunity": "free-text",
    "example_quotes": [...]
  }
}
```

**`personas.json`** — schema per entry:
```json
{
  "<persona_slug>": {
    "title_variants": ["..."],
    "firm_size_signals": ["..."],
    "buying_authority": "high|medium|low + free-text",
    "language_markers": ["..."],
    "common_pains": ["<pain_slug>"]
  }
}
```

**`jargon.json`** — schema per entry:
```json
{
  "<term>": {
    "def": "short definition",
    "use_in_outreach": true
  }
}
```

`use_in_outreach`: false for terms that sound try-hard (MOIC, carry); true for natural identifiers (LMM, portcos).

**`playbook.md`** — free-form markdown. Claude appends learnings each run: what kinds of posts convert, what DM openers get replies, what tone resonates.

### 5. `/pe-process` slash command

**Location:** `.claude/commands/pe-process.md`

**Steps Claude executes when invoked:**

1. Run `python agents/pe_intel/scrape.py` and `python agents/pe_intel/score.py` via Bash.
2. Query SQLite: hot leads scored today AND not in `processed_leads`.
3. Load all four KB JSON files + `playbook.md`.
4. For each hot lead:
   - Pull full post + all comments from SQLite.
   - **Extract phase:** identify new tools/pains/personas/jargon mentioned in this thread; update KB JSON files in place.
   - **Generate phase:** match thread to a persona + pain → write Reddit comment (value-first, no pitch) and DM (warmer, leads with specific offer/proof).
   - Save to `queue/YYYY-MM-DD_<author>_<post_id>.md` (see format below).
   - Insert into `processed_leads`.
5. Append to `playbook.md`: what was learned today.
6. Print summary table: N hot leads, queue file paths, KB diff stats.

**Idempotency:** posts already in `processed_leads` are skipped on re-run. Delete the row to regenerate.

### 6. Queue file format

```markdown
---
post_id: <id>
author: u/<name>
url: <permalink>
score: <0-100>
reasons: [tag, tag, ...]
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
- u/x (N upvotes): "<snippet>"
- u/y (N upvotes): "<snippet>"

## Suggested REDDIT COMMENT
> <Claude-generated comment>

## Suggested REDDIT DM
> <Claude-generated DM>

## Knowledge updates from this thread
- Added tool: "<name>" (<sentiment>)
- Added pain: "<slug>"
- Added jargon: "<term>"
```

### 7. `/pe-outcome` slash command

**Location:** `.claude/commands/pe-outcome.md`

**Usage:** `/pe-outcome <post_id> <outcome>` where outcome is one of `responded | dmd_back | ghosted | client | unsubscribed`.

**Action:** Updates `processed_leads.outcome` and `processed_leads.posted_at`. Over time, this data feeds back into `score.py` weight tuning.

## Testing strategy

- **`db.py`:** unit tests on schema creation + insert/query helpers (use in-memory SQLite).
- **`scrape.py`:** test the comment-tree walker against a saved JSON fixture (the existing `r_privateequity_20260427_2143.json` works as a real-world sample). Verify dedup logic against re-scrape.
- **`score.py`:** test with fixtures of known posts — career-question posts must score <30, the Strong-Buy-6466 post must score ≥90.
- **`/pe-process`:** manual end-to-end test — run on existing scraped data, verify queue files generate and KB updates make sense.

## Rollout

1. **v1 (this spec):** scrape → score → manual `/pe-process` → review queue. No auto-posting. Manual outcome tracking.
2. **v1.1:** Tune scoring weights based on first 30 days of outcome data.
3. **v1.2:** Add `/pe-process --backfill` mode that processes old hot leads in batches (rebuilds KB from history).
4. **v2 (out of scope here):** vector search for "find posts similar to this one"; LinkedIn cluster; auto-DM for highest-confidence leads.

## Risks

- **Reddit rate limits / blocks:** mitigated by 2s delay + UA string + `praw` fallback. If unauth gets blocked entirely, switch to authenticated PRAW (creds already in `agents/reddit_bot.env`).
- **Knowledge base drift:** Claude could hallucinate tool names or invent pain patterns. Mitigation: every KB entry tracks `example_quotes` with `post_id` so claims are auditable. Monthly review of `tools.json` for entries with mention_count = 1 (likely hallucinations).
- **Generated outreach feels formulaic:** mitigation is the `playbook.md` feedback loop — as outcomes accumulate, Claude updates the playbook, and the prompt instructions in `pe-process.md` reference it on every run.
- **Slash command discoverability:** user has dozens of slash commands; document `/pe-process` in `MEMORY.md` and `DAILY-REMINDERS.md`.
