---
description: Run the daily client-acquisition stack. Invokes /revops-process, /pe-process, /reddit-mine (skipping any that ran today), generates the LinkedIn 20, builds the Daily Brief, and refreshes the Dashboard.
---

You are running `/outreach-os`, the morning entry point for the daily client-acquisition routine.

## Send guardrails (hard rules, read first)

- The MVP only calls the Anthropic API outbound. Never call SMTP, sender SDKs (Smartlead, Instantly, Apollo, Lemlist, Outreach, Mailgun, SendGrid, yagmail, smtplib, aiosmtplib), or platform send APIs (LinkedIn send, Reddit post).
- The Uncharted/PitchBook database is not read or referenced anywhere in this command.

## Steps (in order)

### 1. Skip-or-run each upstream pipeline

For each pipeline in this order: `revops`, `pe`, `reddit_mine`:

1. Check the marker:

   ```bash
   "C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "from agents.outreach_os import last_run; import json; print(json.dumps({'ran_today': last_run.ran_today('PIPELINE')}))"
   ```

   (Substitute `PIPELINE` with `revops` / `pe` / `reddit_mine`.)

2. If `ran_today` is true, log it as skipped and continue to the next pipeline.

3. Otherwise, invoke the corresponding sub-slash-command via the Task tool:
   - `revops` -> `/revops-process`
   - `pe` -> `/pe-process`
   - `reddit_mine` -> `/reddit-mine`

   Wait for completion. Capture stderr.

4. On clean completion, write the marker:

   ```bash
   "C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "from agents.outreach_os import last_run; last_run.write('PIPELINE', new_leads=N, errors=0)"
   ```

   Substitute `N` with the lead count from the sub-command's summary. If the count is unknown, use `0`.

5. On failure, log the pipeline as failed. Do NOT write the marker. Continue to the next pipeline.

### 2. Generate today's LinkedIn 20

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.linkedin_rotator
```

If this errors, log `linkedin` as failed and continue.

### 3. Aggregate the Daily Brief

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.aggregate
```

### 4. Refresh the Dashboard

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.dashboard
```

### 5. Print summary

A single table: `pipelines_run`, `pipelines_skipped`, `pipelines_failed`, `total_leads_today`, `pending_outcome_count`. Then point the user to `outreach-os/daily/YYYY-MM-DD.md`.

## Voice rules (hard)

- No em-dashes, no emoji, no guru cadence in any text you generate.

## Guardrails

- Do NOT post anything to Reddit or LinkedIn. The queues are review-only.
- Do NOT send any email.
- Do NOT modify the existing pipelines' source code; only invoke them.
