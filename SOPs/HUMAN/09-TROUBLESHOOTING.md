# Troubleshooting

Failure modes and fixes. Updated as new issues come up.

## Claude Code

### "Not logged in"
```bash
claude /login
```
Browser opens, log in with Claude subscription. Persists across sessions.

### `--bare` mode rejects auth
`--bare` requires `ANTHROPIC_API_KEY` env var. For subscription-based usage, drop `--bare`.

### Subprocess from Python fails with quoting errors on Windows
Use `claude.exe` directly (not `claude.cmd`):
```python
CLAUDE_BIN = r"C:\Users\Admin\AppData\Roaming\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe"
```
Pass system prompts via `--append-system-prompt-file <tmp>`, not `--append-system-prompt "<inline>"`.
See: `D:/Projects/my-project/deal-sourcer/core/claude_client.py`

## Lead Scrapers

### Google blocking LinkedIn scraper
Symptom: 0 results from every query in `linkedin_lead_finder.py`.

Fix:
1. Switch to WebSearch tool via Claude Code subprocess (free, no blocking)
2. OR add Brave Search API (free tier, 2k queries/month)
3. OR run `playwright` with logged-in LinkedIn session

### Reddit rate limited
Symptom: 429 errors from PRAW.

Fix: stop, wait 1 hour, reduce request rate in `lead_finder_agent.py`.

### n8n community AI answer banned
Symptom: account flagged for AI-generated answers.

Fix: ALWAYS review `answer_queue.json` and edit before posting. The agent only drafts, never posts.

## Brain DB

### Postgres not starting
```bash
cd D:/Projects/my-project/n8n-docker
docker compose down
docker compose up -d brain
docker compose logs brain | tail -20
```

If port 5432 is already taken (you have local Postgres), edit `docker-compose.yml` to map 5433:5432, and update `DATABASE_URL` in MCP config.

### Schema didn't auto-create
Schema only runs on FIRST boot when `brain_data/` is empty.
```bash
docker compose down -v   # wipes data, fresh start
docker compose up -d brain
```

### MCP server not finding DB
```bash
claude mcp list
# Should show postgres
```
If missing, re-run:
```bash
claude mcp add postgres --command python --args -m mcp_postgres \
  --env DATABASE_URL=postgresql://jone:brain2026@localhost:5432/brain
```
Restart Claude Code.

## Ralph Loop

### "Story too big" errors
Split the story. Rule: 2-3 sentences max.

### Build fails because dependency not in place
Reorder stories in `prd.json`: schema first, backend second, UI third.

### Type check fails silently
Always include "Typecheck passes" as final criterion in every story.

See full mistakes list: `memory/ralph_mistakes.md`

## Anthropic SDK

### Anthropic 0.39.0 breaks on modern httpx
Symptom: `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`

Fix: upgrade to anthropic >= 0.50.0:
```bash
pip install --upgrade anthropic
```

## Free GPU compute

### Colab T4 quota hit
Symptom: "You cannot currently connect to a GPU."

Fix:
- Switch to Kaggle (separate quota)
- Wait until weekly reset
- Use CPU mode for lighter workloads (MiroFish supports CPU)

## LinkedIn agent

### `ANTHROPIC_API_KEY` not set
The LinkedIn agent uses Anthropic API. For zero-cost output, refactor to Claude Code subprocess pattern (see deal-sourcer's `claude_client.py`).

## fpdf2 PDF generation

### "Not enough horizontal space to render a single character"
Cause: cursor stuck near right margin. Fix: explicit `pdf.set_x(pdf.l_margin)` before each `multi_cell`.

### Multi-resolution ICO only includes one size
Don't use `append_images` for ICO. Pass `sizes=[(w,h), ...]` to `save()` instead.
```python
img.save(out, format="ICO", sizes=[(16,16), (32,32), (64,64), (128,128), (256,256)])
```

## Windows path issues

### `cmd.exe /c start` drops first letter of filename
Symptom: `'laude-Code-Brain-Setup-Guide.pdf' is not recognized`

Fix: use PowerShell `Invoke-Item` instead:
```powershell
Invoke-Item "D:\path\to\file.pdf"
```

## When nothing works

Per the fallback rule (memory/feedback_use_claude_api.md):
- ANY external API failing -> use Claude Code itself
- Never block on API issues
- Never burn time debugging when there's a fallback path

## When you find a new failure mode

Add it here. Add it to `AGENT/05-MISTAKES-LOG.md`. Add it to project memory at `C:\Users\Admin\.claude\projects\...\memory\` if it's a recurring rule.

## RevOps Intel Standalone Pipeline

### "GROQ_API_KEY not set"
- Symptom: pipeline exits immediately with `LLMError: GROQ_API_KEY not set`
- Fix: create `agents/revops_intel/.env` from `.env.example`, paste your free Groq key from https://console.groq.com/keys
- Verify: `python -c "from agents.revops_intel import llm_client; print(llm_client.complete('say hi'))"` should print a short reply

### "Rate limit hit on every call"
- Symptom: all leads logged to `logs/failed_leads.jsonl` with 429 errors
- Likely cause: you ran the pipeline twice within 60 seconds, or another script is sharing the Groq key
- Fix: wait 60s, run again. If still failing after 5 min, check Groq dashboard for daily-cap exhaustion. Worst case: switch model in `llm_client.py` to `llama-3.1-8b-instant` (lower quality but higher free-tier limits)

### "KB JSON corrupted - pipeline restored from backup"
- Symptom: log entry mentions `.bak` restoration for one of the four KB files
- Cause: previous run was killed mid-write, or two scripts touched the KB concurrently
- Fix: confirm the restored KB file is valid (`python -c "import json; json.load(open('agents/revops_intel/knowledge_base/tools.json'))"`). If still bad, manually pick a recent `.bak` from `knowledge_base/.backups/`

### "_FLAGGED_*.md files in queue/"
- Meaning: the LLM produced output that failed quality checks (length, prompt leak, truncation) twice in a row
- Fix: open the file, edit the comment/DM by hand, rename without `_FLAGGED_` prefix before posting
- If you see flagged files frequently (>10% of run): prompt drift - open `prompts/*.txt` and tighten
