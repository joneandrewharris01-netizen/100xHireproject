# Architecture Patterns: AdNerve CSV Audit SaaS

**Domain:** AI-powered CSV upload + analysis SaaS (brownfield Next.js 16)
**Researched:** 2026-03-17
**Overall confidence:** HIGH (Vercel constraints verified via official docs; PDF approach MEDIUM)

---

## Recommended Architecture

AdNerve maps cleanly to six components. Each has a single responsibility and communicates only with its immediate neighbors. The audit pipeline is the critical path — everything else supports it.

```
Browser
  │
  ├── Upload UI (client component) ──► /api/audit/upload   (Route Handler)
  │                                         │
  │                                         ▼
  │                                   CSV Parser Layer
  │                                   (per-platform normalizer)
  │                                         │
  │                                         ▼
  │                                   Audit Engine
  │                                   (check runner + scorer)
  │                                         │
  │                                         ▼
  │                                   Claude API
  │                                   (narrative + recommendations)
  │                                         │
  │                                         ▼
  │                                   Supabase (Postgres)
  │                                   (audit results + user data)
  │                                         │
  ├── Dashboard UI ◄─────────────────── /api/audit/[id]
  │
  └── PDF Export ◄──────────────────── /api/audit/[id]/pdf
```

---

## Component Boundaries

| Component | Responsibility | Input | Output | Communicates With |
|-----------|---------------|-------|--------|-------------------|
| Upload UI | File selection, validation, progress display | User file selection | FormData POST | /api/audit/upload |
| /api/audit/upload | Receive file, parse CSV, run checks, call Claude, persist | multipart/form-data | auditId (JSON) | CSV Parser, Audit Engine, Claude API, Supabase |
| CSV Parser | Detect platform from headers, normalize to canonical schema | Raw CSV string | NormalizedAdData[] | Audit Engine |
| Audit Engine | Run 190+ deterministic checks, calculate weighted score | NormalizedAdData[] | CheckResult[], score | Claude API (sends check summary) |
| Claude API | Generate narrative insights, revenue-impact estimates | Check results + raw metrics | AuditInsights (JSON) | /api/audit/upload |
| Supabase | Persist users, audits, results, subscriptions | Typed inserts | Typed queries | All API routes |
| Dashboard UI | Render score, checks, recommendations, quick wins | auditId | — | /api/audit/[id] |
| /api/audit/[id]/pdf | Fetch audit from DB, generate PDF buffer | auditId | PDF binary | Supabase, @react-pdf/renderer |
| Auth middleware | Gate routes behind valid session | JWT cookie | 401 or pass-through | All /api/audit/* routes |
| /api/payments/* | Create Razorpay subscription, verify webhook signature | Plan selection / webhook payload | subscription status | Supabase (update user tier) |

---

## Data Flow: CSV Upload to PDF

### Step 1 — Client Upload

```
User selects file
  → client validates: file type (text/csv), size < 4MB (Vercel hard limit)
  → FormData POST to /api/audit/upload
  → optimistic UI shows progress bar
```

**Vercel constraint:** Request body hard limit is 4.5 MB on all plans. Ad platform CSV exports for a typical account (90 days, campaign level) are 50–500 KB. This is not a real-world problem. If a user hits the limit, reject with a clear message: "Export a shorter date range or campaign subset."

### Step 2 — Platform Detection + Normalization

```
/api/audit/upload receives file
  → read raw text via request.formData()
  → PlatformDetector.detect(headers[]) → 'google' | 'meta' | 'linkedin' | 'tiktok' | 'microsoft'
  → PlatformParser[platform].parse(rawCsv) → NormalizedAdData
```

Detection strategy: Each platform has unique column signatures. Google has "Campaign", "Ad group", "Keyword", "Quality score". Meta has "Ad Set Name", "Frequency", "CPM". Match by required column presence, not filename. This is deterministic and needs zero AI.

Canonical schema (NormalizedAdData):
```typescript
type NormalizedAdData = {
  platform: Platform
  dateRange: { start: string; end: string }
  campaigns: Campaign[]
  adGroups?: AdGroup[]
  ads: Ad[]
  keywords?: Keyword[]
  metrics: PlatformMetrics
  rawHeaders: string[]   // preserved for "unknown column" warnings
}
```

### Step 3 — Deterministic Check Runner

```
AuditEngine.run(normalizedData) → CheckResult[]

Each check:
  - id: 'G42' | 'M01' | etc.
  - status: 'pass' | 'warning' | 'fail' | 'na'
  - severity: 'critical' | 'high' | 'medium' | 'low'
  - evidence: string   // e.g., "3 campaigns have no conversion action"
  - quickWin: boolean
```

Scoring runs inline using the weighted formula from scoring-system.md:
```
score = Σ(C_pass × W_sev × W_cat) / Σ(C_total × W_sev × W_cat) × 100
```

This is pure TypeScript — no AI, no network call. It runs in < 200ms. The check results are the Claude prompt payload.

### Step 4 — Claude API Call

```
AuditSummarizer.buildPrompt(checkResults, normalizedData.metrics)
  → send to Claude API (claude-sonnet-4-5 or haiku-3-5 for cost)
  → parse JSON response: { insights[], recommendations[], quickWins[], estimatedImpact }
```

**Cost optimization via prompt caching:** The system prompt (check definitions, scoring context, output format) is large and static. Cache it with `cache_control: { type: "ephemeral" }`. Only the check results (dynamic, ~2–5 KB per audit) go in the uncached user message. Cache hits cost 10% of normal input price — saves ~90% on the largest cost driver.

**Prompt design:** Send check results, not raw CSV rows. Claude does not need to re-derive what the engine already computed. Keep the prompt under 8K tokens:

```
System (cached): You are an ad audit expert. Given check results in JSON, produce...
                 [check ID definitions, severity scales, output schema]

User (uncached): Platform: Google Ads
                 Score: 61/100 (Grade C)
                 Failed checks: [G42 Critical, G13 High, ...]
                 Metrics summary: {spend: $12,400, conversions: 84, ...}

                 Return JSON: { summary, topIssues[], recommendations[], quickWins[] }
```

**Timeout planning:** Claude API calls typically complete in 5–15 seconds. Vercel Hobby cap is 10 seconds — this will cause intermittent timeouts. Use Pro plan with `maxDuration = 60` set in the route, or use Vercel Fluid Compute. Do not ship on Hobby plan.

```typescript
// app/api/audit/upload/route.ts
export const maxDuration = 60
```

### Step 5 — Persistence

```
Supabase insert:
  audits table: { id, userId, platform, score, grade, createdAt }
  audit_checks table: { auditId, checkId, status, severity, evidence }
  audit_insights table: { auditId, summary, recommendations (JSON), quickWins (JSON) }
```

Return `{ auditId }` to client. Client redirects to `/dashboard/audit/[id]`.

### Step 6 — Dashboard Render

```
/dashboard/audit/[id]
  → server component fetches audit by ID from Supabase
  → verifies audit.userId === session.userId (ownership check)
  → renders score ring, check table, recommendation list, quick wins
  → PDF export button triggers /api/audit/[id]/pdf
```

### Step 7 — PDF Generation

```
/api/audit/[id]/pdf
  → fetch complete audit from Supabase
  → @react-pdf/renderer: build PDF from React components (runs server-side in Node.js)
  → stream PDF buffer as response with Content-Disposition: attachment
```

Use `@react-pdf/renderer` (not Puppeteer). It runs in pure Node.js with no Chromium dependency — works on Vercel serverless without extra configuration. Puppeteer on Vercel requires `@sparticuz/chromium-min` and is error-prone within function size limits. The tradeoff is that react-pdf layouts are less flexible than HTML/CSS, but that is acceptable for a structured report.

---

## Directory Structure

```
src/
  app/
    (auth)/
      login/page.tsx
      signup/page.tsx
    (app)/                         # gated by auth middleware
      dashboard/
        page.tsx                   # audit list
        audit/[id]/page.tsx        # audit results
        upload/page.tsx            # CSV upload UI
    api/
      audit/
        upload/route.ts            # POST: parse + analyze
        [id]/route.ts              # GET: fetch results
        [id]/pdf/route.ts          # GET: generate + stream PDF
      auth/[...nextauth]/route.ts  # NextAuth handlers
      payments/
        create/route.ts            # POST: create Razorpay subscription
        webhook/route.ts           # POST: handle Razorpay events
  lib/
    parsers/
      detect.ts                    # PlatformDetector
      google.ts                    # Google CSV → NormalizedAdData
      meta.ts
      linkedin.ts
      tiktok.ts
      microsoft.ts
      types.ts                     # NormalizedAdData, Platform, etc.
    engine/
      checks/
        google.ts                  # G01–G74 check functions
        meta.ts
        linkedin.ts
        tiktok.ts
        microsoft.ts
      scorer.ts                    # weighted scoring formula
      runner.ts                    # AuditEngine.run()
    ai/
      summarizer.ts                # buildPrompt(), parseResponse()
      client.ts                    # Anthropic SDK wrapper
    pdf/
      AuditReport.tsx              # react-pdf document component
      generator.ts                 # renders to buffer
    db/
      schema.ts                    # Supabase table types
      queries.ts                   # typed query helpers
    payments/
      razorpay.ts                  # client init, signature verify
    auth/
      config.ts                    # NextAuth configuration
  components/
    upload/
      DropZone.tsx
      ProgressIndicator.tsx
    dashboard/
      ScoreRing.tsx
      CheckTable.tsx
      QuickWins.tsx
      RecommendationList.tsx
```

---

## Suggested Build Order (Dependency Graph)

Build order is driven by what blocks what. The audit engine is the core product — auth and payments gate access to it but do not affect its logic.

```
Phase 1: Foundation
  Supabase setup (schema, auth tables) ──► NextAuth integration ──► Auth middleware
  (Nothing else works without a user identity to attach audits to)

Phase 2: Audit Core (the product)
  CSV parsers (Google first, most users) ──► Check runner ──► Scorer
  (This is pure TypeScript, no external dependencies, testable in isolation)

Phase 3: AI Layer
  Claude API integration ──► Prompt builder ──► Response parser
  (Requires check runner output as input; test with fixture check results)

Phase 4: API Route + Storage
  /api/audit/upload (wires parser + engine + Claude + Supabase) ──► /api/audit/[id]
  (Integration point; exercise with real CSV files)

Phase 5: Dashboard UI
  Upload UI ──► Results dashboard ──► Score ring + check table components
  (Requires Phase 4 API routes to return real data)

Phase 6: PDF Export
  react-pdf AuditReport component ──► /api/audit/[id]/pdf route
  (Independent of dashboard; can be built in parallel with Phase 5)

Phase 7: Payments
  Razorpay subscription flow ──► Webhook handler ──► Paywall middleware
  (Gate /dashboard behind active subscription; test last so it doesn't block development)

Phase 8: Remaining Platforms
  Add Meta, LinkedIn, TikTok, Microsoft parsers + check files
  (Google alone is an MVP; other platforms add market width)
```

---

## Vercel-Specific Constraints

| Constraint | Limit | Impact on AdNerve | Mitigation |
|------------|-------|-------------------|------------|
| Request body size | 4.5 MB hard | CSV exports are typically < 500 KB | Client-side size check before upload; show error if exceeded |
| Hobby function timeout | 10 seconds | Claude API call will timeout intermittently | Require Pro plan; set `maxDuration = 60` |
| Pro function timeout (configurable) | 300 seconds | Enough for full audit pipeline | Set `maxDuration = 60` (safe headroom) |
| Fluid Compute (Pro) | 14 min | Available if needed for batch audits | Not needed for single-file audit |
| Function memory | 1 GB default | CSV parsing + react-pdf can spike | Increase via `memory = 1024` in route config if PDF generation OOMs |
| Filesystem | Ephemeral, read-only in production | Cannot write temp files | Process everything in memory; stream PDF buffer directly |
| Environment variables | Managed per deployment | API keys (Anthropic, Razorpay, Supabase) | Set via Vercel dashboard, never hardcode |

```typescript
// app/api/audit/upload/route.ts — Vercel config
export const maxDuration = 60
export const runtime = 'nodejs'  // NOT edge; need Node.js APIs for CSV parsing
```

**Do not use Edge runtime** for any audit route. Edge runtime lacks Node.js stream APIs, buffer handling, and the `crypto` module needed for Razorpay signature verification.

---

## Architecture Decisions

### Why Supabase over Neon

Supabase includes auth (row-level security), storage, and typed client in one package. Solo dev context means fewer services to wire together. Neon experienced multiple outages in 2025 (including a 5.5-hour incident in May 2025). Supabase is the safer production choice. Free tier is sufficient for MVP (500 MB database, 50,000 monthly active users).

### Why NextAuth over Clerk

Clerk is faster to set up but adds a paid dependency as the user base grows. NextAuth + Supabase Auth Adapter is free, uses the same database already present, and keeps all user data in one place. For a solo dev shipping a $29/mo SaaS, avoiding per-user fees at scale matters. Initial setup is 2–3 hours, not 30 minutes, but it is a one-time cost.

### Why @react-pdf/renderer over Puppeteer

Puppeteer on Vercel requires `@sparticuz/chromium-min` (a 50 MB+ binary), complex configuration, and still hits timeout issues on the Hobby plan. `@react-pdf/renderer` is pure Node.js, zero binary dependencies, ships in the standard function bundle, and renders audit reports in under 2 seconds. The layout API is more constrained than HTML/CSS but is sufficient for a structured report (score, check table, recommendations list).

### Why Deterministic Checks Before Claude

Running 190 checks in TypeScript and passing only the results to Claude (not the raw CSV) keeps Claude prompt size under 8 KB per audit. This reduces Claude API costs by ~80% compared to passing full CSV rows. It also makes the scoring deterministic and auditable — users can see exactly which check fired and why, with the AI layer providing human-readable narrative on top.

### Why Single /api/audit/upload Route (Not Streaming)

The full pipeline (parse + checks + Claude + DB insert) runs in 10–30 seconds. A single route that returns when complete is simpler than a streaming/polling approach. The client shows a loading state. This is acceptable for a paid product where users expect the wait. If latency becomes a product issue, switch to: upload → return jobId → poll /api/audit/[jobId]/status → fetch results when complete. Do not pre-optimize this.

---

## Scalability Considerations

| Concern | At 10 users/day | At 100 users/day | At 1,000 users/day |
|---------|----------------|------------------|--------------------|
| Claude API cost | ~$0.50–2/day | ~$5–20/day | ~$50–200/day | Cache system prompt; use Haiku for simple checks |
| Supabase DB | Free tier fine | Free tier fine | Pro plan ($25/mo) |
| Vercel functions | Free tier exceeded (100 GB-hrs) | Pro plan needed ($20/mo) | Pro plan fine |
| CSV parsing time | Negligible | Negligible | Consider worker threads if > 5 MB files |

At MVP scale (< 100 users/day), the architecture above runs comfortably within Vercel Pro + Supabase free tier, total infra cost under $50/month.

---

## Anti-Patterns to Avoid

### Storing Raw CSV in the Database
**Why bad:** CSV files from 5 platforms with 90-day date ranges can be 200–500 KB each. At 100 audits/day, this is 15–25 MB/day of unstructured blobs, hitting Supabase free storage limits quickly.
**Instead:** Parse immediately on upload, store only normalized structured data. If CSV preservation is legally required, use Supabase Storage (object storage) with a reference pointer in the audit row.

### Calling Claude with Full CSV Rows
**Why bad:** A Google Ads CSV with 500 campaigns and 3,000 keywords can be 200+ KB. At $15/M input tokens, this costs $3+ per audit before prompt caching. Users churn when pricing has to rise to cover costs.
**Instead:** Run deterministic checks first, pass only check results (~2–5 KB) to Claude.

### Using Edge Runtime for Audit Routes
**Why bad:** Edge runtime lacks Node.js buffer APIs, `crypto` (needed for Razorpay signature verification), and stream handling. The audit pipeline needs all three.
**Instead:** Explicitly set `export const runtime = 'nodejs'` in every audit and payment API route.

### Building All 5 Platform Parsers Before Shipping
**Why bad:** Delays shipping by 2–3 weeks. Each parser requires sourcing real CSV exports for testing, which is time-consuming.
**Instead:** Ship Google Ads only. It covers the largest market segment and validates the full pipeline. Add platforms in Phase 8.

### Polling Supabase from the Dashboard on Every Re-render
**Why bad:** Burns free tier row reads quickly; adds latency.
**Instead:** Fetch audit data once in a server component, pass as props. No client-side polling needed — results are immutable once an audit completes.

---

## Sources

- Vercel function timeout limits: [Vercel Functions Limitations](https://vercel.com/docs/functions/limitations) — HIGH confidence (official docs)
- Vercel body size limit 4.5 MB: [Vercel KB: Bypass body size limit](https://vercel.com/kb/guide/how-to-bypass-vercel-body-size-limit-serverless-functions) — HIGH confidence (official KB)
- maxDuration configuration: [Configuring Maximum Duration](https://vercel.com/docs/functions/configuring-functions/duration) — HIGH confidence (official docs)
- Fluid Compute extended durations: [How to solve Next.js timeouts — Inngest](https://www.inngest.com/blog/how-to-solve-nextjs-timeouts) — MEDIUM confidence (third-party, corroborated by Vercel docs)
- @react-pdf/renderer Vercel compatibility: [react-pdf npm](https://www.npmjs.com/package/@react-pdf/renderer) + community confirmation — MEDIUM confidence
- Puppeteer on Vercel challenges: [Deploying Puppeteer with Next.js on Vercel](https://vercel.com/kb/guide/deploying-puppeteer-with-nextjs-on-vercel) — HIGH confidence (official KB)
- Claude prompt caching: [Prompt caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — HIGH confidence (official docs)
- Supabase vs Neon production reliability: [Serverless PostgreSQL 2025 — DEV Community](https://dev.to/dataformathub/serverless-postgresql-2025-the-truth-about-supabase-neon-and-planetscale-7lf) — MEDIUM confidence (verified by multiple sources)
- Razorpay webhook integration: [Integrate Razorpay with NextJS — akkhil.dev](https://www.akkhil.dev/blogs/razorpay-integration-with-nextjs) — MEDIUM confidence
- NextAuth vs Clerk: [better-auth vs NextAuth vs Clerk — supastarter](https://supastarter.dev/blog/better-auth-vs-nextauth-vs-clerk) — MEDIUM confidence
