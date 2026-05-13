# Daily, Weekly, Monthly Routines

Consistency beats intensity. Same things, every day.

## Daily (~90 min, mornings)

Set aside 9-10:30am. No exceptions unless paid client work.

### Morning (30 min)
- [ ] Open Claude Code, run `/gsd:progress` to see project state
- [ ] Check `DAILY-REMINDERS.md` for UNN8N + idea review reminders
- [ ] Check overnight lead CSVs in `agents/leads/`
- [ ] Skim warm-lead inboxes (LinkedIn, Reddit DM, email) - reply to anything < 24hr

### RevOps lead pipeline (daily, free-LLM)
- Run `agents\revops_intel\run.bat` (or `python -m agents.revops_intel.run`)
- Review queue files in `agents/revops_intel/queue/` written today
- Post HOT comments + send WARM DMs manually (queue is review-only)
- Investigate any `_FLAGGED_*.md` files before posting them
- Weekly (Sunday): run `/revops-process` for Opus-grade pass on the same week's hot leads - compare to standalone output, note any quality drift in mistakes.json

### Content (30 min)
- [ ] Run `python agents/content_idea_agent.py daily` - pick today's topic
- [ ] Run `python agents/linkedin_agent.py "<topic>" --type full` - generate 3 deliverables
- [ ] Post to LinkedIn between 9-11am IST
- [ ] DM yesterday's commenters with their PDF resource

### Outreach (30 min)
- [ ] Pick top 5 hot leads from `agents/leads/` CSVs
- [ ] Send 5 personalized DMs / Reddit comments / cold emails
- [ ] Log every send to brain DB `interactions` table
- [ ] Schedule day-3 follow-ups for any pending replies

## Daily reminders to never skip

These are baked into `DAILY-REMINDERS.md`:
- UNN8N personal n8n project - check daily, define scope, build
- Content ideas review - process new ideas
- Brain DB updates - log new interactions

## Weekly (~3 hours, Friday afternoons)

### Wins, gaps, plan (1 hour)

Use `10-WEEKLY-REVIEW-TEMPLATE.md`. Answer:
- Wins this week (what shipped, what got paid)
- Gaps (what stalled, why)
- Top 3 priorities next week (always tied to "get a paid client")

### Backups (30 min)
- [ ] Brain DB: `pg_dump -U jone brain > E:/Brain-Backups/brain_$(date +%F).sql`
- [ ] Critical project folders to E:/ via robocopy
- [ ] Push all local Git repos to GitHub

### System health (1 hour)
- [ ] `docker compose ps` - all services up?
- [ ] n8n workflow error rates - http://localhost:5678/workflows
- [ ] Free compute used vs quota (Colab + Kaggle)
- [ ] Stale agents running? `tasklist | grep python` - kill anything older than 7 days
- [ ] Disk space on D: - prune old build artifacts

### Lead consolidation (30 min)
- [ ] Run `python agents/consolidate_leads.py` - merge weekly CSVs
- [ ] Move any HOT leads to `interactions` table for tracking
- [ ] Archive old non-converted CSVs to `agents/leads/archive/`

## Monthly (~half day, first Friday)

### Strategic review
- [ ] Revenue MTD / forecast
- [ ] Active client count vs goal
- [ ] Lead source ROI: which sources are converting?
- [ ] Content engagement: top 3 posts, why?
- [ ] Project pipeline: what's stalling?

### Cleanup
- [ ] Archive completed projects in brain DB
- [ ] Update `MEMORY.md` index if anything stale
- [ ] Refresh `agents/PLAYBOOK.md` with new agents added
- [ ] Cancel any subscription you didn't use

### Goal-set next month
- [ ] One headline metric (clients won, revenue, content posted)
- [ ] One system to improve (pick from `09-TROUBLESHOOTING.md`)
- [ ] One new automation to build (from `idea_db/`)

## Quarterly

### Big stuff
- [ ] Tax / accounting review
- [ ] Renew domain / SaaS subscriptions
- [ ] Backup verification: actually restore a brain DB backup to confirm it works
- [ ] Hardware health: SMART check on D: and E: drives

## Never-skip rules

1. **Don't break the chain.** Daily LinkedIn post + 5 DMs is the minimum.
2. **Log everything.** If it isn't in the brain, it didn't happen.
3. **Friday review is sacred.** No "I'll do it tomorrow." Do it Friday.
4. **No new tools until current ones are running clean.** Tool sprawl is the silent killer.

## When discipline breaks down

Symptoms: skipped reviews, stale brain DB, no daily post for 3+ days.

Fix: don't try to "catch up." Reset. Log a brief note in brain explaining the gap, and start fresh tomorrow with just the morning routine. Discipline is restored by doing the small thing today, not by overcompensating.
