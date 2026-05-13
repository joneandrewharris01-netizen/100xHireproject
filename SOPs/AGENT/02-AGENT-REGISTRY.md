---
name: Agent Registry
description: Every agent we have, what it does, when to use it, how it's been performing
audience: agent
---

# Agent Registry

All agents live in `D:/Projects/my-project/agents/`. Run via `python <agent>.py [args]` unless otherwise noted.

## Lead-generation agents

### lead_finder_agent.py
- **Purpose:** Reddit lead scraper across 22 subreddits
- **Stack:** PRAW + Groq scoring
- **Usage:** `python lead_finder_agent.py --hours 0.5`
- **Output:** `agents/leads/reddit_leads_<ts>.csv`
- **Health:** Working as of 2026-04-23. Scheduled every 4h via n8n.
- **Known issues:** Rate limiting if `--hours` > 2.

### linkedin_lead_finder.py
- **Purpose:** LinkedIn search via Google scraping
- **Stack:** requests + Groq scoring
- **Usage:** `python linkedin_lead_finder.py --hours 0.5`
- **Output:** `agents/leads/linkedin_leads_<ts>.csv`
- **Health:** BROKEN as of 2026-04-23 (Google blocking). Use WebSearch fallback instead.
- **Fix path:** Switch to Brave Search API or authenticated Playwright session.

### n8n_community_agent.py
- **Purpose:** Find leads on community.n8n.io
- **Usage:** `python n8n_community_agent.py --hours 0.5`
- **Output:** `agents/leads/n8n_community/*.csv`
- **Companion:** `n8n_community_helper.py` drafts answers (manual review required)

### hn_lead_finder.py
- **Purpose:** Hacker News opportunity finder
- **Usage:** `python hn_lead_finder.py`
- **Output:** `agents/leads/hn_*.csv`

### twitter_lead_finder.py
- **Purpose:** X.com (Twitter) keyword scraping
- **Usage:** `python twitter_lead_finder.py --query "<keyword>"`

### google_maps_scraper.py
- **Purpose:** Local business data
- **Usage:** `python google_maps_scraper.py --location "<area>" --niche "<type>"`

### free_domain_prospector.py
- **Purpose:** TLD-based prospect discovery
- **Usage:** `python free_domain_prospector.py`

### find_100_leads.py
- **Purpose:** Bulk run target (100-lead session)
- **Usage:** `python find_100_leads.py`

### seattle_local_lead_agent.py
- **Purpose:** Seattle-geo-targeted leads
- **Folder:** `agents/seattle_local/` has full module
- **Usage:** `python seattle_local_lead_agent.py`

### coach_scraper.py + coach_enricher.py
- **Purpose:** Life/business coach niche scrape + enrich
- **Workflow:** `coach_scraper.py` first, then `coach_enricher.py` on output

### web_intent_scraper.py
- **Purpose:** General web scraping for intent signals

### arcaero_partner_finder.py
- **Purpose:** One-off Arcaero deal sourcer
- **Status:** Reference only. Replaced by general-purpose `deal-sourcer/` Streamlit app.

### enrich_socials.py
- **Purpose:** Add LinkedIn / Twitter / website URLs to existing leads CSV

### consolidate_leads.py
- **Purpose:** Merge weekly lead CSVs, dedupe
- **Run:** `python consolidate_leads.py` weekly

### lead_qualifier.py
- **Purpose:** AI-score raw leads
- **Stack:** Groq, scoring rubric in code
- **Used by:** All lead_finder agents internally

### lead_claude_helper.py
- **Purpose:** Generate personalized DM for a specific lead
- **Run:** `python lead_claude_helper.py --lead <id_from_csv>`

### lead_memory.py
- **Purpose:** Local cache of seen lead URLs (avoid duplicates across runs)
- **Module:** Imported by all lead agents

### run_lead_orchestra.py
- **Purpose:** Run all lead sources in sequence
- **Run:** `python run_lead_orchestra.py`

### revops_intel/run.py
- **Purpose:** Standalone Reddit lead pipeline for B2B SaaS RevOps niche. Free-LLM replacement for `/revops-process`.
- **Stack:** PRAW + SQLite + Groq Llama 3.3 70B + python-dotenv
- **Usage:** `python -m agents.revops_intel.run [--limit N] [--dry-run]` or `agents\revops_intel\run.bat`
- **Output:** `agents/revops_intel/queue/*.md` + KB JSON updates + processed_leads DB writes
- **Health:** Unknown (newly built 2026-05-13; awaits first production run)
- **Known issues:** TBD on first month of runs

## Content-generation agents

### content_idea_agent.py
- **Purpose:** Generate content ideas (daily, batch, trend-based)
- **Modes:** `daily`, `batch`, `trend`, `list`, `top`, `stats`
- **DB:** `agents/idea_db/ideas.json`
- **Run:** `python content_idea_agent.py daily`

### linkedin_agent.py
- **Purpose:** Generate full LinkedIn deliverable (caption + carousel + PDF)
- **Run:** `python linkedin_agent.py "<topic>" --type full`
- **Outputs:** `agents/output/linkedin_output/<slug>_<ts>/`
- **Requires:** ANTHROPIC_API_KEY (NOT zero-cost)
- **Refactor opportunity:** Port to Claude Code subprocess pattern from `deal-sourcer/core/claude_client.py`

### linkedin_dm_agent.py
- **Purpose:** Draft LinkedIn DMs to leads
- **Run:** `python linkedin_dm_agent.py --lead <id>`

### instagram_agent.py
- **Purpose:** Reel scripts, hooks, content calendars
- **Run:** `python instagram_agent.py "<topic>"`

### generate_seo_llm_post.py
- **Purpose:** SEO-optimized blog/LinkedIn post

### torti_style_generator.py
- **Purpose:** Specific creator-voice generator

### scraper_agent.py
- **Purpose:** General scraper (YouTube, Reddit, web)

## Builder agents

### code_builder_agent.py
- **Purpose:** Generate MVPs, landing pages, n8n workflows, APIs
- **Run:** `python code_builder_agent.py "<task>"`

### research_agent.py
- **Purpose:** Market research, trend analysis, opportunity reports

### saas_validator_agent.py
- **Purpose:** BUILD / MAYBE / KILL verdict on SaaS ideas
- **Run:** `python saas_validator_agent.py "<idea>"`

### analysis_agent.py
- **Purpose:** Pattern recognition, scoring, data analysis (general)

### proposal_agent.py
- **Purpose:** Upwork proposals, cold emails, follow-ups

### build_resume_docx.py
- **Purpose:** Generate polished DOCX resume

## Reddit-specific

### reddit_karma_bot.py
- **Purpose:** Comment queue builder (NEVER auto-posts)
- **Workflow:** Reads pending comments, presents queue for manual review

### reddit_auth_setup.py
- **Purpose:** One-time PRAW credential setup

### scrape_comments.py / quick_reddit_scan.py / quick_coaches_scan.py
- **Purpose:** Various ad-hoc Reddit scans

## Reel review

### reel_reviewer/ folder
- `generate_vo_with_timings.py` - VO generation
- `reel_reviewer.py` - AI critique
- `build_review_video.py` - assembled review video

## Utility

### upload_to_drive.py
- **Purpose:** Upload outputs to Google Drive

### run_remotion_post.py
- **Purpose:** Trigger Remotion render via API

### automa_bridge.py
- **Purpose:** Bridge to Automa Chrome extension

### run_agent.py
- **Purpose:** Universal agent runner with `--list`, workflow modes
- **Run:** `python run_agent.py --list` to see all

## Master playbook

`D:/Projects/my-project/agents/PLAYBOOK.md` is the human-friendly version of this registry.

## How agents have been performing (status snapshot)

| Status | Agents |
|---|---|
| Healthy | reddit lead finder, n8n community, content idea, code builder |
| Broken | linkedin_lead_finder (Google blocking) |
| Reference only | arcaero_partner_finder (superseded by deal-sourcer Streamlit) |
| Needs API key (not zero-cost) | linkedin_agent, instagram_agent, research_agent |
| Stale | hn_lead_finder, twitter_lead_finder (no recent runs) |

## Choosing the right agent (decision flow)

```
What do you need?
  Find leads             -> 03-LEAD-SYSTEMS or run_lead_orchestra.py
  Make content           -> linkedin_agent / instagram_agent / content_idea_agent
  Score / qualify lead   -> lead_qualifier.py
  Build code / app       -> code_builder_agent.py
  Research a topic       -> research_agent.py
  Validate idea          -> saas_validator_agent.py
  Find partners for      -> deal-sourcer/ (Streamlit app)
  Reach out to a lead    -> lead_claude_helper.py
  Daily content          -> content_idea_agent.py daily
```

## When to create a new agent

1. Same task done 3+ times manually
2. Existing agent does < 50% of what you need
3. Output format / source is different enough to justify

## When NOT to create a new agent

1. Existing agent does 80%+ - just modify it
2. One-off task - just script it inline
3. Could be a Claude Code skill instead - prefer skills for behavioral changes
