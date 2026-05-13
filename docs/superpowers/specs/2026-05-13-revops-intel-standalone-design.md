# RevOps Intel — Standalone Free-LLM Pipeline (Design Spec)

**Date:** 2026-05-13
**Owner:** Jone Andrew Harris
**Status:** Approved for implementation
**Related:** `agents/revops_intel/`, `.claude/commands/revops-process.md`, `docs/superpowers/specs/2026-04-28-pe-intel-agent-design.md`

---

## Problem

The RevOps Intel pipeline (`/revops-process`) currently requires an interactive Claude Code session to do the LLM work: knowledge base extraction, Reddit comment drafting, and DM drafting. That coupling means:

1. **It cannot run unattended.** No cron job, no background process, no headless server.
2. **It burns the user's Claude Code Max-plan session time** for repetitive output that is largely templated against a knowledge base.
3. **It blocks parallel work.** While `/revops-process` runs, the same session cannot do anything else.
4. **It is not portable.** New niches (pe_intel, reddit_mine, future verticals) each require their own slash command and human attention.

The Python layer below the slash command (`scrape.py`, `score.py`, `route.py`, `db.py`, `classify.py`) is already pure Python with zero LLM calls — it does Reddit scraping, heuristic scoring, and DB routing. The only LLM-dependent steps are the per-lead KB extraction and outreach drafting.

## Goal

Replicate the full `/revops-process` end-to-end as a standalone Python pipeline that uses a **free** LLM provider (Groq, Llama 3.3 70B) instead of Claude Code. One command runs scrape → score → route → loop hot leads → extract KB → draft comment + DM → save queue file → mark processed. Output is byte-for-byte compatible with what `/revops-process` produces today.

## Non-Goals

- **No auto-posting.** Reddit's spam detection is brutal; queue is review-only. Same rule as the slash command.
- **No replacement of the slash command itself.** `/revops-process` continues to exist for high-stakes one-offs where Opus quality matters. The standalone pipeline is the daily default.
- **No multi-provider abstraction.** Single provider (Groq) in v1. Provider swap is a one-file edit to `llm_client.py`.
- **No new scraping logic.** Reuse `scrape.py`, `score.py`, `route.py`, `classify.py` unchanged. `db.py` gets one new helper (`fetch_top_comments`) — see Architecture section.
- **No new DB schema.** Same `revops_intel.db`, same `mark_processed` writes.
- **No port to pe_intel or reddit_mine in v1.** Prove the pattern on revops_intel first; port later when the shape stabilizes.
- **No paid API spend.** Groq free tier is the whole budget. If we exceed it, we slow down — we do not upgrade.

## Architecture

### File layout

```
agents/revops_intel/
├── scrape.py                  (unchanged) Reddit → SQLite
├── score.py                   (unchanged) heuristic scoring
├── route.py                   (unchanged) DB routing
├── db.py                      MODIFIED   adds fetch_top_comments(conn, post_id, limit) helper
├── classify.py                (unchanged) keyword classification
├── knowledge_base/            (unchanged) tools/pains/personas/jargon/offers/playbook
├── queue/                     (unchanged) generated outreach drafts
├── logs/                      (unchanged + new files below)
│   ├── failed_leads.jsonl     NEW  per-lead failures with stack + retry count
│   └── voice_violations.jsonl NEW  every regex substitution applied
├── llm_client.py              NEW  Groq SDK wrapper, retry, voice cleanup
├── llm_extract.py             NEW  KB extraction step
├── llm_generate.py            NEW  comment + DM drafting step
├── run.py                     NEW  chain runner (~80 LOC)
├── run.bat                    NEW  one-click launcher
├── .env                       NEW  GROQ_API_KEY=... (gitignored)
├── .env.example               NEW  template (committed)
├── prompts/                   NEW
│   ├── kb_extract.txt
│   ├── reddit_comment.txt
│   └── reddit_dm.txt
├── fixtures/                  NEW
│   └── sample_lead.json       lead dict shaped like db.fetch_hot_unprocessed returns
└── tests/
    ├── test_llm_client.py     NEW  voice regex, retry behavior (Groq mocked)
    ├── test_llm_extract.py    NEW  KB merge logic against fixture thread
    └── test_llm_generate.py   NEW  voice rule compliance on generated text
```

### Data flow

```
                ┌──────────────────────────────────────┐
                │  python -m agents.revops_intel.run   │
                └──────────────────┬───────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
       scrape.py              score.py               route.py
       (subprocess)          (subprocess)           (subprocess)
            │                      │                      │
            └────────► revops_intel.db (posts/comments/scores) ◄────
                                   │
                                   ▼
                  db.fetch_hot_unprocessed(limit=20)
                                   │
              ┌────────────────────┴───────────────────┐
              │  for each hot lead, in score order:   │
              └────────────────────┬───────────────────┘
                                   ▼
                       ┌───────────────────────┐
                       │   llm_extract.py      │
                       │   - read 4 KB JSON    │
                       │   - Groq call         │
                       │   - merge + write JSON│
                       └───────────┬───────────┘
                                   ▼
                       ┌───────────────────────┐
                       │   llm_generate.py     │
                       │   - read offers.json  │
                       │   - Groq call (cmt)   │
                       │   - Groq call (DM)    │
                       └───────────┬───────────┘
                                   ▼
                       ┌───────────────────────┐
                       │   write queue/*.md    │
                       │   db.mark_processed() │
                       │   sleep 2.1s          │
                       └───────────────────────┘
```

### Component contracts

#### `db.py` (modification)

Add one helper. The current `/revops-process` slash command uses inline `SELECT` for top comments (lines 36-44 of `revops-process.md`); we lift it into a real helper to keep the "no raw SQL outside db.py" rule intact for both the slash command and this pipeline.

```python
def fetch_top_comments(conn, post_id: str, limit: int = 10) -> list[dict]:
    """Returns top comments for a post, ordered by score desc.
    Each row: {author, body, score, depth}."""
```

#### `llm_client.py`

```python
class LLMError(Exception): pass

def complete(
    prompt: str,
    *,
    max_tokens: int = 800,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
) -> str:
    """Single Groq call with retry + voice cleanup. Raises LLMError on unrecoverable failure."""
```

- Reads `GROQ_API_KEY` from `agents/revops_intel/.env` (loaded via `python-dotenv`)
- Retries: 3x exponential backoff on 429 (1s, 4s, 16s); 2x on 5xx (1s, 4s)
- Total max wait per call: ~25s
- After response: runs `_enforce_voice(text)` (see below) and returns cleaned text
- Logs every call (model, tokens_in, tokens_out, latency_ms, retries) to `logs/llm_calls.jsonl`

#### `_enforce_voice(text: str) -> str` (private)

Hard rules from project memory ([feedback_writing_style](memory/feedback_writing_style.md)). All rules run case-insensitive (`re.IGNORECASE`).

| Violation | Action |
|---|---|
| Em-dash (`—`, `–`) | Deterministic rule: if the next non-whitespace char is uppercase OR end-of-string, replace with `. `; otherwise replace with `, `. (Covers "did X — Then Y" → ". Then Y" and "did X — and Y" → ", and Y".) |
| Emoji | Strip via combined regex covering `\U0001F000-\U0001FFFF` plus `\U00002600-\U000027BF` plus skin tones `\U0001F3FB-\U0001F3FF` plus ZWJ `‍`. Also strip typographic noise: `…` → `...`, `→` → ` to `, `•` → `-`, smart quotes (`"" ''`) → straight quotes. |
| Trailing CTA boilerplate | If the last sentence matches any of: "DM me", "Hit me up", "Feel free to reach out", "Reach out anytime", "Shoot me a message" → strip that sentence. |
| Guru phrases (case-insensitive) | Lookup table (committed in `llm_client.py` as `GURU_REPLACEMENTS`): `"game changer"` → `"big shift"`, `"game-changer"` → `"big shift"`, `"10x"` → `"a lot more"`, `"level up"` → `"improve"`, `"crushing it"` → `"doing well"`, `"move the needle"` → `"matter"`, `"deep dive"` → `"look at"`, `"low-hanging fruit"` → `"quick win"`, `"synergy"` → `""` (strip), `"leverage"` (as verb) → `"use"`. |

Every substitution gets appended to `logs/voice_violations.jsonl` with `{ts, lead_id, rule, before, after}` so prompt drift is visible over time.

**Ordering rule:** `_enforce_voice` runs once at `llm_client.complete()` exit. The length check in `llm_generate` runs on cleaned text. Voice-rule violations alone never trigger a regeneration retry — the regex has already fixed them. Only length-out-of-range and quality-sanity violations (see below) trigger retries.

#### `llm_extract.py`

```python
def extract(lead: dict, top_comments: list[dict]) -> dict:
    """Returns a diff dict: {tools: {...}, pains: {...}, personas: {...}, jargon: {...}}.
    Caller is responsible for merging into the real KB JSON files."""
```

- Reads `prompts/kb_extract.txt`, fills in `{lead}` and `{comments}` placeholders
- Single `llm_client.complete()` call, max_tokens=1500, temp=0.2 (extraction is low-creativity)
- Parses the response as JSON. If JSON parse fails, retries the call once with a stricter "JSON ONLY" suffix. After 2 fails, returns empty dict and logs to `failed_leads.jsonl`
- Strips any `<think>...</think>` reasoning blocks before JSON parsing (Llama 3.3 occasionally emits these depending on prompt phrasing)
- Caller (`run.py`) immediately merges into the 4 KB JSON files using the read-fresh-mutate-write-back protocol from the slash command (one file at a time, no in-memory batching)

**KB diff schema returned by `extract`** (pinned here for implementation compatibility with `/revops-process` output — mirrors `revops-process.md` lines 69-74):

```json
{
  "tools": {
    "<tool_name>": {
      "category": "...", "first_seen": "<iso>", "mention_count": 1,
      "sentiment_summary": "...", "common_complaints": ["..."],
      "common_praise": ["..."], "example_quotes": ["..."]
    }
  },
  "pains": {
    "<pain_slug>": {
      "frequency": 1, "personas_affected": ["..."],
      "current_workarounds": ["..."], "automation_opportunity": "...",
      "example_quotes": ["..."]
    }
  },
  "personas": {
    "<persona_slug>": {
      "title_variants": ["..."], "firm_size_signals": ["..."],
      "buying_authority": "...", "language_markers": ["..."],
      "common_pains": ["..."]
    }
  },
  "jargon": {
    "<term>": { "def": "...", "use_in_outreach": true }
  }
}
```

Each top-level key is optional — empty dict `{}` for a missing category is valid.

#### `llm_generate.py`

```python
def generate(lead: dict, top_comments: list[dict], offer_pitch: dict) -> tuple[str, str]:
    """Returns (reddit_comment, reddit_dm). Each is voice-clean plain text."""
```

- `offer_pitch` is loaded by caller from `knowledge_base/offers.json` based on `lead["offer_match"]`
- Two separate `llm_client.complete()` calls: one with `prompts/reddit_comment.txt`, one with `prompts/reddit_dm.txt`
- Each prompt includes: lead body, top 3 comments, KB excerpts (top mentioned tools + pains relevant to this post's `problem_category`), offer pitch
- Post-generation sanity checks (run in order, retry once on any failure, after 2 fails raise `QualityFlag`):
  1. **Prompt-leak check** — reject if output contains literal `"HARD RULES"`, `"AS AN AI"`, or any prompt-template marker (`{`, `}` placeholder syntax that survived templating)
  2. **Truncation check** — reject if output does not end in a sentence-terminating punctuation (`.`, `!`, `?`) — likely token-limit truncation
  3. **Length check** — comment 60-250 words, DM 60-180 words
- On `QualityFlag`: the queue file is still written but renamed `_FLAGGED_<id>.md` so user sees it needs manual fix. The exception carries the last attempt's content via `.comment`, `.dm`, `.reason` attributes.

```python
class QualityFlag(Exception):
    def __init__(self, comment: str, dm: str, reason: str):
        self.comment, self.dm, self.reason = comment, dm, reason
        super().__init__(reason)
```

#### `run.py`

Pseudocode (~80 LOC target):

```python
def main(limit: int = 20, dry_run: bool = False):
    # 0. Snapshot KB JSON files for rollback
    snapshot_kb_backups()    # writes timestamped .bak in knowledge_base/.backups/

    # 1. Refresh data — fail-fast if scrape errors >5%
    subprocess.run([PY, "-m", "agents.revops_intel.scrape"], check=True)
    subprocess.run([PY, "-m", "agents.revops_intel.score"], check=True)
    subprocess.run([PY, "-m", "agents.revops_intel.route"], check=True)

    # 2. Pull hot leads
    conn = db.connect()
    hot = db.fetch_hot_unprocessed(conn, limit=limit)

    if not hot:
        print(f"[INFO] no hot leads in queue; last successful run had N. Exiting cleanly.")
        log_zero_lead_run()    # tracks 3-day streak for louder warning
        return 0

    # 3. Load offer playbook (used for prompt context)
    offers = json.load(open("knowledge_base/offers.json"))
    DEFAULT_OFFER_KEY = "general_automation"   # NOT "general" — verified against offers.json

    # 4. Loop
    stats = {"processed": 0, "flagged": 0, "failed": 0, "kb_diffs": Counter()}
    for lead in hot:
        kb_diff: dict = {}       # initialized BEFORE try so except branch can reference it
        comments: list = []
        retry_stall_sec = 0.0    # tracks backoff time for inter-lead sleep adjustment
        try:
            comments = db.fetch_top_comments(conn, lead["post_id"], limit=10)
            kb_diff = llm_extract.extract(lead, comments)
            if not dry_run:
                merge_kb_atomic(kb_diff, stats["kb_diffs"])
            offer_pitch = offers.get(lead["offer_match"], offers[DEFAULT_OFFER_KEY])
            comment, dm = llm_generate.generate(lead, comments, offer_pitch)
            if not dry_run:
                queue_file = write_queue(lead, comments, comment, dm, kb_diff, flagged=False)
                db.mark_processed(conn, lead["post_id"], queue_file, lead["offer_match"])
            stats["processed"] += 1
        except QualityFlag as e:
            if not dry_run:
                queue_file = write_queue(lead, comments, e.comment, e.dm, kb_diff, flagged=True)
                db.mark_processed(conn, lead["post_id"], queue_file, lead["offer_match"])
            stats["flagged"] += 1
        except LLMError as e:
            log_failure(lead, e)
            stats["failed"] += 1
        except Exception as e:    # truly unexpected — log full traceback
            log_failure(lead, e, traceback=True)
            stats["failed"] += 1

        # Inter-lead sleep: skip if backoff already burned the budget
        sleep_for = max(0, 2.1 - retry_stall_sec)
        time.sleep(sleep_for)

    # 5. Print summary table (playbook.md append is skipped in v1 — see Open Questions)
    print_summary(stats)
    return 0
```

**CLI flags:** `--limit N` (default 20), `--dry-run` (call Groq but no DB/KB writes).

### Prompt design

Each `prompts/*.txt` file is a string template with named placeholders. They are NOT Python f-strings — they use `{placeholder}` and are filled via `template.format(**kwargs)`. This lets the user edit them without restarting the pipeline or touching Python.

Each prompt ends with the hard voice rules block:

```
HARD RULES — violations will be regex-stripped automatically:
- No em-dashes (—, –). Use periods, commas, or "and".
- No emoji. None.
- No "DM me", "Hit me up", "Feel free to reach out". End naturally.
- No guru cadence ("game changer", "10x", "level up", "crushing it").
- Sound like a peer who has built this. Plain prose.
```

## Rate limit math

Groq free-tier limits change occasionally — **verify against https://console.groq.com/docs/rate-limits at implementation time**. Current published values for `llama-3.3-70b-versatile` free tier (as of 2026-05):

| Resource | Groq free tier (`llama-3.3-70b-versatile`) | Pipeline usage per run (20 leads × 3 calls = 60 calls) |
|---|---|---|
| Requests/min (RPM) | 30 | ~28.5 (with 2.1s inter-lead sleep, 3 calls grouped per lead) |
| Tokens/min (TPM) | 12,000 | ~8,000 peak (KB extract + 2 generate, ~2.7k tokens/lead) |
| Requests/day (RPD) | 1,000 | ~60 (well under) |
| Tokens/day (TPD) | 100,000 | ~24,000 (well under) |

The 30 RPM and 12,000 TPM ceilings are the real constraints. A single bad-actor lead that burns 3 retries × 3 calls = 9 calls in <60s can briefly exceed RPM; the exponential backoff inside `llm_client.complete()` absorbs this. If Groq changes their free tier, update this table — do not assume the old numbers.

## Voice rules and quality gates

| Gate | When | Action |
|---|---|---|
| JSON parse (KB) | After `llm_extract` returns | Retry once with stricter suffix; after 2 fails, skip KB for this lead, log to `failed_leads.jsonl` |
| Length check (comment) | After `llm_generate` returns | 60-250 words. Retry once. After 2 fails, mark `_FLAGGED_` |
| Length check (DM) | After `llm_generate` returns | 60-180 words. Retry once. After 2 fails, mark `_FLAGGED_` |
| Voice regex | Inside `llm_client.complete()` | Always runs. Logs every substitution. |
| KB write race | Between leads | Atomic per-file write (read fresh, mutate, write back, fsync). One lead at a time — no concurrency. |

## Failure modes

| Failure | Behavior |
|---|---|
| Groq API key missing | Hard fail at startup with clear message |
| Groq rate limit | Retry with exponential backoff (built into `llm_client`) |
| Groq 5xx | Retry once after 4s; if still failing, log to `failed_leads.jsonl` and continue |
| KB JSON corrupt on read | Log to `failed_leads.jsonl`, restore from latest `.bak` (see KB backup protocol below), continue |
| Network timeout | Retry once; on second failure, log and continue |
| Subprocess (scrape/score/route) failure | Hard fail — that data layer is upstream of everything else |
| Output quality (length/sanity) | Retry once with stricter prompt; on second failure, save to `queue/_FLAGGED_*.md` and continue |
| Zero hot leads returned | Log `[INFO] no hot leads`, increment streak counter in `logs/zero_lead_streak.txt`, exit 0 without calling Groq. If streak reaches 3 consecutive days, also print a louder warning. |
| Groq returns 200 with malformed text | Prompt-leak check + truncation check + `<think>...</think>` strip inside `llm_generate`. Trigger retry, then `QualityFlag`. |

All failures continue to the next lead. A single bad lead never crashes the run.

### KB backup protocol

At the start of every `run.py` execution (the `snapshot_kb_backups()` call in step 0):

1. Copy `knowledge_base/{tools,pains,personas,jargon}.json` to `knowledge_base/.backups/YYYY-MM-DDTHH-MM-SS_<file>.json.bak`
2. After write, prune `.backups/` to keep the most recent 7 snapshots per file (one week of rollback room)
3. On KB-JSON-corrupt-on-read failure: restore from the most recent `.bak` of that file, log the restoration, retry the read once. If still corrupt after restore: hard fail with clear error (something deeper is broken)
4. `.backups/` is gitignored (add to `.gitignore` during implementation)

## Testing strategy

Unit tests cover the LLM-touching modules with the Groq client mocked:

- `test_llm_client.py`
  - Voice regex strips em-dashes, emoji, "DM me" trailers, guru phrases
  - Retry on 429 sleeps then retries; gives up after 3 attempts
  - Retry on 5xx; gives up after 2 attempts
  - Voice substitutions appended to `voice_violations.jsonl`
- `test_llm_extract.py`
  - Given a fixture lead (`agents/revops_intel/fixtures/sample_lead.json` — shape matches `db.fetch_hot_unprocessed` row, NOT a raw Reddit Listing), returns the KB diff schema pinned in this spec
  - JSON parse failure → retries with stricter suffix
  - Two failures → returns empty dict, logs to `failed_leads.jsonl`
  - `<think>...</think>` blocks stripped before JSON parse
- `test_llm_generate.py`
  - Output passes voice rule check (no em-dashes, no emoji, no banned phrases)
  - Out-of-range length triggers retry
  - Two length failures → returned with quality flag

Integration smoke test (manual, documented in SOPs):
1. Drop one known-good fixture lead into `revops_intel.db`
2. Run `python -m agents.revops_intel.run`
3. Verify queue file generated, KB diffs applied, mark_processed called

No mock-vs-prod divergence concern — tests mock only the Groq SDK boundary; DB writes go through the same `db.py` real code path against a temp SQLite file.

## SOP touchpoints (mandatory updates during implementation)

The implementation is not complete until all of these are updated. The pipeline that ships without SOP updates is the pipeline that gets lost in a month.

1. **`SOPs/AGENT/02-AGENT-REGISTRY.md`** — add new entry:
   ```
   ### revops_intel/run.py
   - **Purpose:** Standalone Reddit lead pipeline for B2B SaaS RevOps niche. Replicates /revops-process without a Claude Code session.
   - **Stack:** PRAW + SQLite + Groq Llama 3.3 70B
   - **Usage:** `python -m agents.revops_intel.run` or `agents/revops_intel/run.bat`
   - **Output:** `agents/revops_intel/queue/*.md`, KB JSON updates, processed_leads DB writes
   - **Health:** [STATUS as of <date>]
   - **Known issues:** [TBD on first run]
   ```
2. **`SOPs/AGENT/registry.json`** — add this exact JSON object under `agents`:
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
3. **`SOPs/AGENT/09-LLM-PROVIDER-POLICY.md`** — append section: "Groq Llama 3.3 70B is the default free-tier provider for content extraction and outreach drafting pipelines (revops_intel, future ports). Claude Code via slash commands remains the option for high-stakes one-offs where Opus-grade output matters."
4. **`SOPs/HUMAN/03-LEAD-SYSTEMS.md`** — add user-facing section explaining: how to run, where outputs land, how to recover from rate-limit, when to use `/revops-process` instead
5. **`SOPs/HUMAN/07-DAILY-ROUTINES.md`** — insert under the morning routine section, exact lines:
   ```
   ### RevOps lead pipeline (daily, free-LLM)
   - Run `agents/revops_intel/run.bat` (or `python -m agents.revops_intel.run`)
   - Review queue files in `agents/revops_intel/queue/` written today
   - Post HOT comments + send WARM DMs manually (queue is review-only)
   - Investigate any `_FLAGGED_*.md` files before posting them
   - Weekly (Sunday): run `/revops-process` for Opus-grade pass on the same week's hot leads — compare to standalone output, note any quality drift in mistakes.json
   ```
6. **`SOPs/HUMAN/09-TROUBLESHOOTING.md`** — add four exact entries (one per scenario):
   ```
   ## RevOps Intel Standalone Pipeline

   ### "GROQ_API_KEY not set"
   - Symptom: pipeline exits immediately with `LLMError: GROQ_API_KEY not set`
   - Fix: create `agents/revops_intel/.env` from `.env.example`, paste your free Groq key from https://console.groq.com/keys
   - Verify: `python -c "from agents.revops_intel import llm_client; print(llm_client.complete('say hi'))"` should print a short reply

   ### "Rate limit hit on every call"
   - Symptom: all leads logged to `logs/failed_leads.jsonl` with 429 errors
   - Likely cause: you ran the pipeline twice within 60 seconds, or another script is sharing the Groq key
   - Fix: wait 60s, run again. If still failing after 5 min, check Groq dashboard for daily-cap exhaustion. Worst case: switch model in `llm_client.py` to `llama-3.1-8b-instant` (lower quality but higher free-tier limits)

   ### "KB JSON corrupted — pipeline restored from backup"
   - Symptom: log entry mentions `.bak` restoration for one of the four KB files
   - Cause: previous run was killed mid-write, or two scripts touched the KB concurrently
   - Fix: confirm the restored KB file is valid (`python -c "import json; json.load(open('agents/revops_intel/knowledge_base/tools.json'))"`). If still bad, manually pick a recent `.bak` from `knowledge_base/.backups/`

   ### "_FLAGGED_*.md files in queue/"
   - Meaning: the LLM produced output that failed quality checks (length, prompt leak, truncation) twice in a row
   - Fix: open the file, edit the comment/DM by hand, rename without `_FLAGGED_` prefix before posting
   - If you see flagged files frequently (>10% of run): prompt drift — open `prompts/*.txt` and tighten
   ```
7. **`SOPs/AGENT/mistakes.json`** — pre-seed three known footguns:
   - "em-dash leakage from Llama 3.3" (mitigation: regex post-cleanup is mandatory)
   - "KB write race if leads run concurrently" (mitigation: serial only, never thread)
   - "prompt drift over time degrades voice" (mitigation: weekly review of `voice_violations.jsonl`)
8. **`SOPs/AGENT/dos_donts.json`** — add: "DO read fresh KB JSON for every lead; DON'T batch KB mutations in memory"
9. **`SOPs/sync.py` run** — final step, mirrors all SOP edits to C: and E: drives. Command: `python D:/Projects/my-project/SOPs/sync.py`
10. **Root `.gitignore`** — verify or add: `agents/*/.env` and `agents/*/knowledge_base/.backups/`

## Resolved decisions (previously open questions)

1. **`--limit N` flag:** YES — implemented. Default 20.
2. **KB backup location and retention:** `knowledge_base/.backups/`, keep last 7 snapshots per file (one week). See "KB backup protocol" above.
3. **`--dry-run` flag:** YES — implemented. Calls Groq for prompt-tuning visibility but skips all DB and KB writes.
4. **`playbook.md` append:** SKIPPED in v1. LLM-generated meta-commentary is the weakest output of free models. User does weekly playbook updates manually after the weekly `/revops-process` Opus-grade pass.

## Success criteria

The pipeline is considered done when:

1. `python -m agents.revops_intel.run` completes a full cycle on real Reddit data without crashing
2. Output queue files are visually indistinguishable from current `/revops-process` queue files (same frontmatter, same sections, same length range)
3. Voice rules hold: zero em-dashes, zero emoji, zero "DM me" trailers, zero un-substituted guru phrases from the `GURU_REPLACEMENTS` lookup table across 20 generated outputs
4. KB JSON files remain valid JSON after a full run; no schema regressions
5. All 10 SOP touchpoints are updated and `sync.py` has mirrored them
6. All tests pass
7. A manual side-by-side comparison of 5 leads (standalone output vs. `/revops-process` output on the same lead) shows the standalone output is "good enough to lightly edit and ship" (user's call, documented in commit message)
