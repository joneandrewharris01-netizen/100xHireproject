---
name: LLM Provider Policy
description: Which model / provider to use for what
audience: agent
---

# LLM Provider Policy

Default to free / subscription. Paid only when explicitly authorized.

## Provider tiers

### Tier 1: Free / subscription (default)

| Provider | How | Cost | Best for |
|---|---|---|---|
| Claude Code subprocess | `claude -p ...` from Python or shell | $0 (subscription) | Default LLM for any task |
| Groq | Free API tier | $0 (rate limited) | Bulk / cheap classification |
| Gemini Flash free | Google AI Studio API | $0 (rate limited) | Vision tasks, second opinion |
| OpenRouter free models | OpenRouter API | $0 (slow / limited models) | Variety, cheap fallback |

### Tier 2: Paid (only with authorization)

| Provider | When to use |
|---|---|
| Anthropic API direct | NEVER unless user explicitly authorized for this specific task |
| OpenAI API | NEVER unless user explicitly authorized |
| GLM 5.2 (paid plan) | Bulk agents per memory's LLM provider policy |

## Model choice within Claude Code

| Model | When | Cost on subscription |
|---|---|---|
| Sonnet (default) | Most tasks | Generous quota |
| Opus | Quality-critical: contracts, sales letters, final client output | Limited Opus quota; use sparingly |
| Haiku | Tiny tasks: format conversion, classification | Smallest footprint |

Set via `--model sonnet` / `--model opus` / `--model haiku` flag.

## When to use what

### Default for any new agent
```python
# Use the deal-sourcer pattern - zero cost, subscription-based
from deal_sourcer.core.claude_client import call_claude
response = call_claude(system_prompt, user_message, use_web_search=False)
```

### Quality-critical (final client output)
- Use Claude Code with `--model opus`
- Or use the QA-style pattern: cheap model first, Opus review pass

### Bulk classification (1000+ items)
- Groq llama-3.3-70b-versatile (used in lead_qualifier.py)
- Free, fast, accurate enough for scoring

### Vision tasks
- Gemini Flash free tier (multimodal, free)
- OR Claude Code (Sonnet supports vision)

### Web search needed
- Claude Code with `--tools WebSearch` (built-in, free)
- See deal-sourcer/agents/candidate_finder.py for pattern

## Fallback rule (memory: feedback_use_claude_api.md)

If ANY external API fails (Anthropic, Groq, Gemini, OpenAI), fall back to Claude Code subprocess. Don't block on API issues.

```python
try:
    response = groq_client.chat(...)
except (RateLimitError, APIError):
    response = call_claude(...)  # Claude Code fallback
```

## Cost tracking

For zero-cost subscription work, no tracking needed. For any paid API call:
- Log to `agents/cost_log.jsonl` with `{provider, tokens_in, tokens_out, cost_usd, ts}`
- Surface to user weekly via review template

## Rate limit behavior

### Groq
- 30 req/min default
- Backoff: 5s -> 15s -> 30s -> fall back to Claude Code
- Track 429 errors, after 3 in a row switch fallback

### Claude Code
- Subscription has weekly quotas
- If hit Opus limit, fall back to Sonnet
- If hit Sonnet limit, wait until reset (next Sunday) or use Groq for non-critical

### Gemini Flash
- Free quota: 1500 req/day (varies)
- Backoff similar to Groq

## Anti-patterns

- Calling paid Anthropic API "just to test" without authorization
- Using Opus for trivial tasks (format conversion, lookups)
- Looping over a paid API in a tight loop without a budget check
- Using a paid API when Groq could do it (for non-quality-critical bulk work)

## Cross-reference

- Detailed policy in memory: `feedback_llm_provider_policy.md`
- Fallback rule in memory: `feedback_use_claude_api.md`
- Free AI stack: `free_ai_stack_2026.md`

## When to update this policy

If any of these change:
- New model becomes available on subscription
- Free tier of a provider expires or changes
- Task type comes up that doesn't fit current matrix
- Cost / quota numbers shift

Edit this doc, log change in `06-PARTNERSHIPS.md`-style memory note if it affects ongoing work.

## Free-tier provider default (added 2026-05-13)

**Groq Llama 3.3 70B** is the default free-tier provider for content extraction and outreach drafting pipelines (revops_intel/run.py, future ports to pe_intel/reddit_mine).

Claude Code via slash commands (`/revops-process`, `/pe-process`) remains the option for high-stakes one-offs where Opus-grade quality matters. Use the standalone pipeline daily; use Claude Code on the weekly Opus pass for quality benchmarking and prompt drift detection.

Rationale: Groq is fast (200+ tok/s), free up to 1k requests/day on 70B-versatile, and good enough for templated KB extraction + outreach drafting. Claude Code is preserved for judgement-heavy work where the cost is justified.
