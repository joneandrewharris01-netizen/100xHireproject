# Lead Systems

Multiple sources feeding one funnel. Goal: 5+ qualified leads / day, 1+ booked call / week.

## The funnel

```
Source agents -> Raw CSV -> AI score (Groq) -> Hot/Warm/Cold split
       -> Outreach (LinkedIn/Email/DM) -> Reply -> Free Audit -> Sale
```

## Active sources

### Reddit Lead System
- **Run:** `python agents/lead_finder_agent.py --hours 0.5`
- **Output:** `agents/leads/reddit_leads_<timestamp>.csv`
- **Subreddits monitored:** 22 (r/automation, r/n8n, r/smallbusiness, etc.)
- **Karma bot:** `python agents/reddit_karma_bot.py` -> comment queue for review
- **Scheduled:** every 4hrs via `n8n-docker/reddit-opportunity-scanner.json`
- **CRITICAL:** never auto-post comments, always review queue first

### LinkedIn Lead Finder
- **Run:** `python agents/linkedin_lead_finder.py --hours 0.5`
- **Output:** `agents/leads/linkedin_leads_<timestamp>.csv`
- **Method:** Google `site:linkedin.com` search, Groq AI scoring
- **STATUS WARNING:** Last 2 automated runs returned 0 leads (Google blocking). Use WebSearch via Claude Code as fallback.

### n8n Community Bot
- **Run:** `python agents/n8n_community_agent.py --hours 0.5`
- **Output:** `agents/leads/n8n_community/*.csv`
- **Answer drafter:** `python agents/n8n_community_helper.py --max 10`
- **Answer & Earn:** EUR 500/month for top contributor. 3-5 quality answers/day = top 10.
- **CRITICAL:** AI answers banned on the platform. Always review/edit before posting manually.

### Other source agents
- `agents/hn_lead_finder.py` - Hacker News
- `agents/twitter_lead_finder.py` - X.com
- `agents/google_maps_scraper.py` - local businesses
- `agents/free_domain_prospector.py` - TLD prospecting
- `agents/find_100_leads.py` - bulk run target
- `agents/seattle_local_lead_agent.py` - Seattle geo lead
- `agents/coach_scraper.py` - life/biz coaches niche

### Lead Orchestra (run all)
- **Run:** `python agents/run_lead_orchestra.py`
- **What:** Orchestrates multiple lead sources in sequence, deduplicates, scores
- **Output:** Consolidated CSV in `agents/leads/`

## Scoring system (Groq AI)

Every lead is scored 0-100 by `lead_qualifier.py`:
- **80-100 HOT** - urgent need, budget signals, specific tool mention
- **60-79 GOOD** - clear need, small business, worth reaching out
- **31-59 MAYBE** - vague signal, awareness opportunity
- **0-30 NOT** - irrelevant or already solved

Hot leads go to top of outreach queue. Cold get filtered to nurture content list.

## Outreach flow

1. **Hot lead identified** -> generate personalized DM via `lead_claude_helper.py`
2. **Send DM** manually on LinkedIn / Reddit comment / cold email
3. **Log interaction** to brain DB:
   ```sql
   INSERT INTO interactions (lead_id, channel, direction, summary)
   VALUES (?, 'linkedin', 'outbound', '<one sentence>');
   ```
4. **Follow up** at day 3, 7, 14 if no reply
5. **Convert lead -> client** when they accept Free Audit:
   ```sql
   UPDATE leads SET converted_to_client_id = <new client id>;
   INSERT INTO clients (...);
   ```

## Offers

| Tier | Price | Delivery | Use when |
|---|---|---|---|
| Free Audit | $0 | 30-min call + 1-page report | Any inbound lead |
| Custom Build | $497 | One-shot automation, 7-14 days | Validated need, willing to pay one-time |
| Retainer | $1,497/mo | Hosting + monitoring + monthly improvement | Ongoing relationship |

## Storage

- Raw leads: `agents/leads/*.csv`
- Persistent: `leads` table in brain DB
- Memory file: `C:\Users\Admin\.claude\...\memory\reddit_lead_system.md`, `n8n_community_bot.md`

## When a system breaks

- Google blocking scraper -> switch to WebSearch tool via Claude Code subprocess
- Groq rate limit -> fall back to Gemini Flash (free) or Claude Code direct
- LinkedIn captcha -> stop automation, do manual review for 48hr
- See `09-TROUBLESHOOTING.md` for full list

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
- `agents/revops_intel/queue/*.md` - draft comments and DMs to review and post manually
- `agents/revops_intel/knowledge_base/*.json` - KB JSON files updated with new tool/pain/persona/jargon entries
- `agents/revops_intel/logs/*.jsonl` - call logs, voice violations, failed leads

**Recovery from rate limits:**
- If a run logs many 429 errors, wait 60s and re-run. Worst case: switch model in `llm_client.py` to `llama-3.1-8b-instant` (lower quality but higher free-tier limits).

**When to use `/revops-process` instead:**
- Weekly Opus-grade pass on the same hot leads for quality benchmarking
- Any one-off where you need Claude's judgment over Groq's speed (high-value lead, edge case persona, unusual offer match)
