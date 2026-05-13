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
- **No new scraping logic.** Reuse `scrape.py`, `score.py`, `route.py`, `db.py`, `classify.py` unchanged.
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
├── db.py                      (unchanged) SQLite helpers
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

Hard rules from project memory ([feedback_writing_style](memory/feedback_writing_style.md)):

| Violation | Action |
|---|---|
| Em-dash (`—`, `–`) | Replace with `, ` if mid-clause, `. ` if sentence-ending |
| Emoji | Strip via regex `[\U0001F300-\U0001FAFF\U00002600-\U000027BF]` |
| Trailing "DM me" / "Hit me up" / "Feel free to reach out" | Strip last sentence if it matches |
| Guru phrases ("game changer", "10x", "level up", "crushing it") | Replace with neutral alternatives from a lookup table |

Every substitution gets appended to `logs/voice_violations.jsonl` with `{ts, lead_id, rule, before, after}` so prompt drift is visible over time.

#### `llm_extract.py`

```python
def extract(lead: dict, top_comments: list[dict]) -> dict:
    """Returns a diff dict: {tools: {...}, pains: {...}, personas: {...}, jargon: {...}}.
    Caller is responsible for merging into the real KB JSON files."""
```

- Reads `prompts/kb_extract.txt`, fills in `{lead}` and `{comments}` placeholders
- Single `llm_client.complete()` call, max_tokens=1500, temp=0.2 (extraction is low-creativity)
- Parses the response as JSON. If JSON parse fails, retries the call once with a stricter "JSON ONLY" suffix. After 2 fails, returns empty dict and logs to `failed_leads.jsonl`
- Caller (`run.py`) immediately merges into the 4 KB JSON files using the read-fresh-mutate-write-back protocol from the slash command (one file at a time, no in-memory batching)

#### `llm_generate.py`

```python
def generate(lead: dict, top_comments: list[dict], offer_pitch: dict) -> tuple[str, str]:
    """Returns (reddit_comment, reddit_dm). Each is voice-clean plain text."""
```

- `offer_pitch` is loaded by caller from `knowledge_base/offers.json` based on `lead["offer_match"]`
- Two separate `llm_client.complete()` calls: one with `prompts/reddit_comment.txt`, one with `prompts/reddit_dm.txt`
- Each prompt includes: lead body, top 3 comments, KB excerpts (top mentioned tools + pains relevant to this post's `problem_category`), offer pitch
- Post-generation length check: comment 60-250 words, DM 60-180 words. If out of range, retry once with stricter prompt. After 2 fails, output is saved but the queue file is renamed `_FLAGGED_<id>.md` so user sees it needs manual fix.

#### `run.py`

Pseudocode (~80 LOC target):

```python
def main():
    # 1. Refresh data — fail-fast if scrape errors >5%
    subprocess.run([PY, "-m", "agents.revops_intel.scrape"], check=True)
    subprocess.run([PY, "-m", "agents.revops_intel.score"], check=True)
    subprocess.run([PY, "-m", "agents.revops_intel.route"], check=True)

    # 2. Pull hot leads
    conn = db.connect()
    hot = db.fetch_hot_unprocessed(conn, limit=20)

    # 3. Load offer playbook + jargon (used for prompt context)
    offers = json.load(open("knowledge_base/offers.json"))

    # 4. Loop
    stats = {"processed": 0, "flagged": 0, "failed": 0, "kb_diffs": Counter()}
    for lead in hot:
        try:
            comments = db.fetch_top_comments(conn, lead["post_id"], limit=10)
            kb_diff = llm_extract.extract(lead, comments)
            merge_kb(kb_diff, stats["kb_diffs"])     # atomic per-file write
            offer_pitch = offers.get(lead["offer_match"], offers["general"])
            comment, dm = llm_generate.generate(lead, comments, offer_pitch)
            queue_file = write_queue(lead, comments, comment, dm, kb_diff, flagged=False)
            db.mark_processed(conn, lead["post_id"], queue_file, lead["offer_match"])
            stats["processed"] += 1
        except QualityFlag as e:
            queue_file = write_queue(lead, comments, e.comment, e.dm, kb_diff, flagged=True)
            db.mark_processed(conn, lead["post_id"], queue_file, lead["offer_match"])
            stats["flagged"] += 1
        except (LLMError, Exception) as e:
            log_failure(lead, e)
            stats["failed"] += 1
            continue
        time.sleep(2.1)  # Groq rate-limit cushion (28.5 req/min ceiling on 30 req/min limit)

    # 5. Append to playbook.md (dated section, prune if >5000 words)
    append_playbook(stats)

    # 6. Print summary table
    print_summary(stats)
```

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

| Resource | Groq free tier (Llama 3.3 70B) | Pipeline usage |
|---|---|---|
| Requests/min | 30 | 28.5 (with 2.1s sleep) |
| Tokens/min | 6,000 | ~4,000 (avg lead) |
| Requests/day | 14,400 | ~60 (20 leads × 3 calls) |
| Tokens/day | ~500,000 | ~24,000 |

Well within free tier. The 30 req/min limit is the only real ceiling. The 2.1s inter-lead sleep gives one full retry of headroom per lead.

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
| KB JSON corrupt on read | Log to `failed_leads.jsonl`, restore from `.bak` (created at start of run), continue |
| Network timeout | Retry once; on second failure, log and continue |
| Subprocess (scrape/score/route) failure | Hard fail — that data layer is upstream of everything else |
| Output quality (length/voice) | Retry once with stricter prompt; on second failure, save to `queue/_FLAGGED_*.md` and continue |

All failures continue to the next lead. A single bad lead never crashes the run.

## Testing strategy

Unit tests cover the LLM-touching modules with the Groq client mocked:

- `test_llm_client.py`
  - Voice regex strips em-dashes, emoji, "DM me" trailers, guru phrases
  - Retry on 429 sleeps then retries; gives up after 3 attempts
  - Retry on 5xx; gives up after 2 attempts
  - Voice substitutions appended to `voice_violations.jsonl`
- `test_llm_extract.py`
  - Given a fixture thread (already exists at `agents/pe_intel/fixtures/sample_thread.json`, adapt for revops), returns the expected JSON shape
  - JSON parse failure → retries with stricter suffix
  - Two failures → returns empty dict, logs to `failed_leads.jsonl`
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
2. **`SOPs/AGENT/registry.json`** — machine-readable mirror of the entry above
3. **`SOPs/AGENT/09-LLM-PROVIDER-POLICY.md`** — append section: "Groq Llama 3.3 70B is the default free-tier provider for content extraction and outreach drafting pipelines (revops_intel, future ports). Claude Code via slash commands remains the option for high-stakes one-offs where Opus-grade output matters."
4. **`SOPs/HUMAN/03-LEAD-SYSTEMS.md`** — add user-facing section explaining: how to run, where outputs land, how to recover from rate-limit, when to use `/revops-process` instead
5. **`SOPs/HUMAN/07-DAILY-ROUTINES.md`** — slot `agents/revops_intel/run.bat` into the daily routine (default daily run; `/revops-process` becomes the weekly deep-quality pass)
6. **`SOPs/HUMAN/09-TROUBLESHOOTING.md`** — add entries for: missing GROQ_API_KEY, rate limit symptoms, KB corruption recovery via `.bak` restore, what `_FLAGGED_*.md` means
7. **`SOPs/AGENT/mistakes.json`** — pre-seed three known footguns:
   - "em-dash leakage from Llama 3.3" (mitigation: regex post-cleanup is mandatory)
   - "KB write race if leads run concurrently" (mitigation: serial only, never thread)
   - "prompt drift over time degrades voice" (mitigation: weekly review of `voice_violations.jsonl`)
8. **`SOPs/AGENT/dos_donts.json`** — add: "DO read fresh KB JSON for every lead; DON'T batch KB mutations in memory"
9. **`SOPs/sync.py` run** — final step, mirrors all SOP edits to C: and E: drives

## Open questions for the planner

(Items the writing-plans skill should resolve before execution starts.)

1. Should `run.py` accept `--limit N` to process fewer leads (useful for first runs while validating prompt quality)?
2. Where should `.bak` files for KB JSON live, and how many revisions to retain? (Recommend: same dir, last 3 timestamped backups, cleaned weekly.)
3. Should we add a `--dry-run` flag that calls Groq but does not write to DB or KB? (Recommend yes — cheap to add, very useful for prompt tuning.)
4. The slash command currently appends to `playbook.md` after each run. Should the standalone pipeline do the same, or skip it (since LLM-generated meta-commentary is the weakest output of free models)? (Recommend skip in v1; user does the weekly playbook update manually.)

## Success criteria

The pipeline is considered done when:

1. `python -m agents.revops_intel.run` completes a full cycle on real Reddit data without crashing
2. Output queue files are visually indistinguishable from current `/revops-process` queue files (same frontmatter, same sections, same length range)
3. Voice rules hold: zero em-dashes, zero emoji, zero "DM me" trailers across 20 generated outputs
4. KB JSON files remain valid JSON after a full run; no schema regressions
5. All 9 SOP touchpoints are updated and `sync.py` has mirrored them
6. All tests pass
7. A manual side-by-side comparison of 5 leads (standalone output vs. `/revops-process` output on the same lead) shows the standalone output is "good enough to lightly edit and ship" (user's call, documented in commit message)
