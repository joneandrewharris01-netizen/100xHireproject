---
title: Outreach OS — Design Spec
date: 2026-05-09
status: draft
owner: Jone Andrew Harris
tags: [outreach, automation, claude-code, agentic-os, design-spec]
---

# Outreach OS — Design Spec

## Goal

A Claude-Code-native control plane that runs the daily client-acquisition stack, eliminates the four friction points that are killing outbound consistency today, and keeps a single dashboard alive past month 6.

The OS exists to serve one priority: **get B2B SaaS RevOps clients toward the locked $5K MRR by day 90-120 target.**

## Primary job

Run the daily revenue routine without:
1. Forgetting to run agents
2. Context-switching across 4+ folders
3. Manually copy-pasting between agent outputs and the next stage
4. Losing track of which leads converted vs. ghosted

## Scope

### In scope (MVP)
- Orchestration of three existing Reddit pipelines: `revops_intel`, `pe_intel`, `reddit_mine`
- LinkedIn 20/day queue generation from `B2B AI Agents.xlsx` (352 rows)
- Daily Brief MD aggregating all queued items
- Dashboard MD with 30-day stats by source
- Outcome flush mechanism (Option C from brainstorm)
- Scheduled daily execution via Claude Code `/schedule`

### Out of scope
- Uncharted 173-rig automation (deferred per user — handled manually wks 1-3)
- Automated LinkedIn DM/connect sending (LinkedIn ToS violation; queue is review-only)
- Web dashboard / SaaS productization (deferred to >day 180)
- New Reddit pipelines beyond the three named above
- Replacing or modifying any existing slash command (`/revops-process`, `/reddit-mine`, `/pe-process`, `/revops-outcome`, `/pe-outcome`)

## Architecture

```
/outreach-os  (single morning entry point)
  │
  ├─ 1. Run upstream pipelines (skip if already run today)
  │     /revops-process  →  agents/revops_intel/queue/*.md
  │     /pe-process      →  agents/pe_intel/queue/*.md
  │     /reddit-mine     →  agents/reddit_mine/queue/*.md
  │
  ├─ 2. Generate today's LinkedIn 20
  │     agents/outreach_os/linkedin_rotator.py
  │       reads B2B AI Agents.xlsx + state.json (last_index)
  │       generates personalized openers via Haiku 4.5
  │       writes agents/outreach_os/linkedin/YYYY-MM-DD.md
  │
  ├─ 3. Aggregate into Daily Brief
  │     agents/outreach_os/aggregate.py
  │       scans queue/*.md frontmatter across 3 pipelines
  │       reads today's LinkedIn MD
  │       reads pending-outcome list from each pipeline (DB or insights.md)
  │       writes outreach-os/daily/YYYY-MM-DD.md
  │
  ├─ 4. Refresh Dashboard
  │     agents/outreach_os/dashboard.py
  │       reads outcomes from each pipeline source
  │       computes 30-day win rates by source
  │       writes outreach-os/dashboard.md
  │
  └─ 5. Print summary table to terminal

/outreach-flush-outcomes  (end-of-day companion)
  └─ Scans today's Daily Brief for ticked outcome checkboxes
     For each ticked box, runs the appropriate `/revops-outcome` or
     `/pe-outcome` slash command. Reports which leads were updated.

/outreach-status  (mid-day cheap check)
  └─ Re-runs aggregate.py + dashboard.py only (no scrape, no LLM calls).
     Surfaces "what's queued / what's pending" without burning tokens.
```

## Component contracts

### `/outreach-os` (slash command)
- **Input:** none (today's date implicit)
- **Output:** Daily Brief MD + refreshed Dashboard + summary table
- **Side effects:** runs three existing slash commands; writes to `outreach-os/` and `agents/outreach_os/`
- **Skip-if-run-today:** for each upstream pipeline, check most recent queue file's `generated_at` frontmatter. If today, skip the scrape/score, just re-aggregate.
- **Failure mode:** any pipeline failure logged to brief frontmatter as `pipelines_failed: [...]`; remaining pipelines continue. Brief always writes.

### `agents/outreach_os/linkedin_rotator.py`
- **Input:** `B2B AI Agents.xlsx`, `agents/outreach_os/state.json`
- **Output:** `agents/outreach_os/linkedin/YYYY-MM-DD.md` (20 leads + openers)
- **Logic:**
  1. Load all 352 rows
  2. Filter to rows not yet contacted (tracked via state.json)
  3. Bump RevOps-ICP rows (job titles matching: VP RevOps, Head of Sales Ops, Director of Revenue Operations, Sales Operations Manager, etc.) to the front
  4. Take first 20
  5. For each, call Haiku 4.5 with `(name, title, company, recent_post_or_signal_if_available)` → 1-line opener
  6. Write MD file with leads + openers
  7. Update state.json: `last_index`, `last_run_date`, `openers_generated_count`
- **Failure mode:** per-row try/except on opener generation. Failed rows get `opener: <ERROR: reason>`; rotation pointer still advances.
- **Cost:** ~20 Haiku calls/day × ~200 tokens each ≈ $0.05/day = $1.50/mo

### `agents/outreach_os/aggregate.py`
- **Input:** all `agents/{revops_intel,pe_intel,reddit_mine}/queue/*.md`, today's LinkedIn MD, per-pipeline pending-outcome lists
- **Output:** `outreach-os/daily/YYYY-MM-DD.md`
- **Logic:** Pure read + filter + format. No LLM calls.
  1. Glob queue files across 3 pipelines, parse YAML frontmatter
  2. Filter to today's run (frontmatter `generated_at` matches today)
  3. Sort by tier: HOT > WARM > AUTHORITY > LinkedIn
  4. Pull pending-outcome list from `processed_leads` table (revops, pe) and `insights.md` outcome state (reddit_mine)
  5. Render as Daily Brief MD per the format defined below
- **Failure mode:** if a pipeline's queue dir is missing, skip with a warning; brief still writes for the others.

### `agents/outreach_os/dashboard.py`
- **Input:** per-pipeline outcome state (DB rows for revops/pe; YAML in queue files for reddit_mine), Daily Brief frontmatter from last 7 days
- **Output:** `outreach-os/dashboard.md` (full rewrite)
- **Logic:** Pure read + aggregation. No LLM calls.
  1. Query last 30 days of outcomes per pipeline source
  2. Compute Sent / Responded / DM'd back / Booked / Win rate
  3. Auto-generate "What's working / not working" verdicts based on win rate (per user approval in Section 3 of brainstorm: auto, not manual)
  4. Build last-7-days run history from Daily Brief frontmatter
  5. Render as Dashboard MD
- **Failure mode:** if any pipeline's outcome source is missing, that row shows `N/A`; dashboard still writes.

### `/outreach-flush-outcomes` (slash command)
- **Input:** today's Daily Brief path
- **Output:** terminal report of which leads were updated and which weren't
- **Logic:**
  1. Read today's Daily Brief
  2. Parse the "Pending outcomes" section
  3. For each lead with a ticked outcome checkbox, identify the pipeline (`revops` / `pe`) and run the appropriate outcome slash command
  4. Print summary: `N updated, M unchanged`
- **Idempotency:** if a lead has already been marked, the underlying outcome command is a no-op (existing behavior of `/revops-outcome` and `/pe-outcome`)

### `/outreach-status` (slash command)
- **Input:** none
- **Output:** refreshed Dashboard + brief terminal summary
- **Logic:** runs `aggregate.py` + `dashboard.py` only. Skips upstream pipelines entirely.
- **Cost:** zero LLM tokens. Pure filesystem + DB reads.

## Data shapes

### Daily Brief — `outreach-os/daily/YYYY-MM-DD.md`

```markdown
---
date: 2026-05-09
generated_at: 2026-05-09T07:30:00
totals: {hot: 3, warm: 8, authority: 4, linkedin: 20, total: 35}
pipelines_run: [revops, pe, reddit_mine, linkedin]
pipelines_skipped: []
pipelines_failed: []
---

# Outreach OS — 2026-05-09

## Pending outcomes (3 leads stale >7 days)
- [ ] `1srvohy` u/Rathavara · revops · DM'd 2026-05-01 (8 days ago)
  - [ ] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub
- [ ] `1t6gaul` u/FunnyGuilty9745 · revops · DM'd 2026-05-02 (7 days ago)
  - [ ] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub
- [ ] `1t73gb4` u/Bubbly-Chee-685 · reddit_mine · DM'd 2026-05-02 (7 days ago)
  - [ ] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub

(Tick a box per lead, then run `/outreach-flush-outcomes` at end of day.)

## HOT (do these first, ~30 min)
### 1. u/FunnyGuilty9745 — r/sales (RevOps · score 92 · outbound_engine)
> "We're hitting 0.4% reply rate on cold email and the agency wants $8K/mo more"
- [ ] Post comment + send DM → [queue file](agents/revops_intel/queue/2026-05-08_FunnyGuilty9745_1t6gaul.md)
- After posting, this lead will appear in tomorrow's "Pending outcomes" section

### 2. ... (next HOT lead)

## WARM (~60 min)
### 1. u/<author> — r/<sub> ...

## AUTHORITY plays (public replies, no pitch — ~30 min)
### 1. ...

## LinkedIn 20 (~60 min)
- [ ] **Sarah Chen** · VP RevOps @ Acme · "Saw your post on Salesforce reporting hell..."
- [ ] **Michael Torres** · Head of Sales Ops @ Beta · "..."
- (...18 more)

## Today's plan
Total: ~3 hours of active work. Start with HOT, then LinkedIn (energy drops fast on those), then WARM, AUTHORITY last.
```

### Dashboard — `outreach-os/dashboard.md`

```markdown
---
last_updated: 2026-05-09T07:30:00
last_run_per_pipeline:
  revops: 2026-05-09T07:30
  pe: 2026-05-09T07:30
  reddit_mine: 2026-05-09T07:30
  linkedin: 2026-05-09T07:30
---

# Outreach OS — Dashboard

## 30-day stats
| Source   | Sent | Responded | DM'd back | Booked | Win rate |
|----------|------|-----------|-----------|--------|----------|
| RevOps   |  47  |    8      |    3      |   1    |  2.1%    |
| PE       |  22  |    4      |    1      |   0    |  0%      |
| Reddit   |  35  |   12      |    5      |   1    |  2.8%    |
| LinkedIn | 280  |   18      |   12      |   2    |  0.7%    |
| Total    | 384  |   42      |   21      |   4    |  1.0%    |

## Outcomes pending >7 days (10 leads)
(list mirrored from Daily Brief)

## What's working
- RevOps + Reddit are 3-4× LinkedIn's win rate. Recommend tilting daily cap.
- Top-converting offer_match: outbound_engine (3 of 4 booked)

## What's not
- PE: 22 sent, 0 booked. Kill or rework after day 30.

## Last 7 days run history
| Date | Pipelines run | New leads | Outcomes logged |
|------|---------------|-----------|-----------------|
| 2026-05-09 | all 4 | 35 | 0 |
| 2026-05-08 | all 4 | 33 | 2 |
```

### LinkedIn rotator state — `agents/outreach_os/state.json`

```json
{
  "last_index": 47,
  "total_rows": 352,
  "icp_bumped_indices": [12, 33, 67],
  "last_run_date": "2026-05-09",
  "openers_generated_count": 940,
  "contacted_indices": [0, 1, 2, "..."]
}
```

## Recommended configuration (locked)

| Setting | Value | Reason |
|---|---|---|
| Schedule time | 7:30 AM local, daily | Lead-gen volume highest before noon; brief ready before work starts |
| Daily action cap | 5 RevOps + 5 PE + 5 Reddit + 20 LinkedIn = 35 | Below this starves outcomes; above this burns out by week 2 |
| Sort order in brief | Pending outcomes → HOT → WARM → AUTHORITY → LinkedIn → Plan | Top of brief = first thing done when energy is highest |
| Model for openers | Haiku 4.5 | ~10× cheaper than Opus, indistinguishable for 1-line opener |
| Model for orchestrator | Opus 4.7 | Per locked feedback: complex routing decisions stay on Opus |
| Skip-if-run-today | Check most recent queue file's `generated_at` | Avoids re-running scrape mid-day |
| LinkedIn rotation | Sequential through 352, ICP-bumped | Each contact touched once before any twice; ICP filter for quality |
| Outcome stale threshold | 7 days | Triggers visibility in brief |
| Dashboard win-rate window | Last 30 days, by source | After 30 days you can kill worst, double best |
| Outcome flush | Tickbox in brief + `/outreach-flush-outcomes` end-of-day | Reduces friction from per-lead command to per-day batch |

## Error handling

- Each pipeline call wrapped: 10-min timeout, capture stderr, mark as `failed` in brief frontmatter, **continue** to next step
- If `aggregate.py` fails on filesystem error, brief writes a stub with error trace; dashboard still updates
- LinkedIn opener generation: per-row try/except. If 1 row fails, leave `opener: <ERROR>` and continue the other 19
- Daily Brief always writes, even with zero leads. Header in that case: "No new leads today, here's what's pending"
- Pipeline failures appear in dashboard's "Last 7 days run history" so a broken pipeline is spotted within 24h

## Testing

- **Unit tests** for `aggregate.py` (queue file fixtures → expected brief sections)
- **Unit tests** for `dashboard.py` (DB row fixtures → expected markdown table)
- **Unit tests** for `linkedin_rotator.py`: mock Anthropic API, fixture xlsx of 10 rows, assert rotation + ICP-bump logic
- **E2E smoke test:** run `/outreach-os` once on a copy of today's data, assert brief + dashboard files exist + parse cleanly
- **E2E smoke test:** run `/outreach-flush-outcomes` against a brief with hand-ticked checkboxes, assert outcomes update in DB
- **No tests for slash commands themselves** — they're tested by their own usage

## Phasing

Phase 1 (MVP, the body of this spec) ships everything above. No phased rollout within MVP.

Phase 2 candidates (deferred, not part of this spec):
- Uncharted 173-rig integration (when wks 1-3 of 90-day plan rotate to wk 4+)
- Auto-detection of LinkedIn replies via LinkedIn export (still no automated sending)
- Streak / consistency tracking ("you've run /outreach-os 14 days in a row")
- Per-channel daily-cap auto-tuning based on win rate

## Open dependencies

- `B2B AI Agents.xlsx` must exist at `D:/Projects/my-project/linkedin-content/B2B AI Agents.xlsx` (per MEMORY.md). Verify path during plan phase.
- `/schedule` skill must support firing slash commands daily at fixed local time. Verify during plan phase.
- The `Task` tool inside `/outreach-os` must be able to invoke other slash commands. If not directly possible, the orchestrator falls back to writing a "run these commands in order" prompt for the user. Verify during plan phase.

## Voice + style requirements (hard rules)

These apply to any text the OS generates (LinkedIn openers, brief copy, dashboard verdicts):
- No em-dashes anywhere. Use periods, commas, or "and"
- No emoji
- No guru cadence — peer voice only
- "Jone Andrew Harris" on outbound, never placeholder handles
- Per existing pipeline rules, no PII of third parties leaks into queue files

## Success criteria

- 14-day post-launch: `/outreach-os` runs every weekday morning without manual intervention
- 30-day post-launch: dashboard shows real win rates per source (no `N/A` cells), proving outcome flush is being used
- 60-day post-launch: at least one win-rate-based daily-cap adjustment has been made (concrete proof the dashboard drove a decision)
- 90-day post-launch: at least one new client cited "outreach via [Reddit/LinkedIn] from Outreach OS" as the source

## Non-goals (explicit)

- Becoming a SaaS
- Replacing existing slash commands
- Automating any platform's terms-violating actions (LinkedIn auto-DM, Reddit auto-post)
- Generic "agentic OS" features beyond what serves the daily revenue routine
