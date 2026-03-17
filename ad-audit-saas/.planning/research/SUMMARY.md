# Project Research Summary

**Project:** AdNerve — CSV-based multi-platform ad audit SaaS
**Domain:** AI-powered PPC audit tool ($29/mo subscription, CSV upload model)
**Researched:** 2026-03-17
**Confidence:** HIGH

## Executive Summary

AdNerve is a brownfield SaaS addition to an existing Next.js 16 + Tailwind v4 app. The product category is well-established — PPC audit tools like Adalysis, Opteo, Optmyzr, and PPC Rocket set clear user expectations — but all credible competitors live above $149/month or are free with shallow checks. The $29/month slot with multi-platform CSV coverage and 186 deterministic checks is a real market gap. The recommended build strategy is Google Ads first (largest market, most checks defined, fastest to validate unit economics), then layer in Meta, LinkedIn, TikTok, and Microsoft Ads as subsequent phases. The core architecture is a six-component pipeline: CSV upload, platform detection and normalization, deterministic check runner (pure TypeScript, no AI), Claude API narrative layer, Postgres persistence, and dashboard/PDF rendering. The single most important design decision is to run all 186 checks deterministically before invoking Claude — this keeps AI costs at $0.008–0.02 per audit rather than $1+ per audit, which is the difference between viable and bankrupt unit economics at $29/month.

The recommended stack adds six packages to the existing foundation: Drizzle ORM + Neon Postgres for lightweight serverless database access, Better Auth for email/password sessions with no vendor dependency, csv-parse for stream-native server-side CSV parsing, Anthropic SDK with Haiku as primary model and Sonnet only for narrative prose, @react-pdf/renderer for PDF generation without Chromium, and Razorpay for recurring subscriptions. Every choice was made with the Vercel free-tier-to-Pro upgrade path in mind. Note: the ARCHITECTURE.md references Supabase while STACK.md recommends Neon + Drizzle. The STACK.md recommendation (Neon + Drizzle) is the more current analysis and should be treated as authoritative — it avoids paying for Supabase's bundled auth and realtime features that this product replaces with better-suited tools.

The two existential risks are AI cost blowout (sending raw CSV rows to Claude instead of aggregated check results) and the Vercel 4.5 MB request body limit (which blocks large ad accounts and causes your best customers to churn). Both must be addressed in the first phase of development, before anything else is built on top of them. A third critical risk — CVE-2025-29927 Next.js middleware auth bypass — means every API route must perform its own session verification, not rely on middleware alone.

---

## Key Findings

### Recommended Stack

The existing Next.js 16 + Tailwind v4 + TypeScript foundation is kept unchanged. Six libraries are added, each chosen to minimize cold start latency and avoid paying for unused features. Drizzle ORM (7.4 KB) vs Prisma (40 KB) is a meaningful cold start difference on Vercel. Better Auth saves 40–80 hours over a production-quality NextAuth email/password setup. @react-pdf/renderer avoids the Puppeteer + Chromium dependency that causes OOM and timeouts in serverless functions.

**Core technologies:**
- Next.js 16 + App Router: existing framework — Server Actions and Route Handlers handle the full pipeline without a separate backend
- Neon Postgres + Drizzle ORM: serverless Postgres with auto-suspend (free tier viable), 7.4 KB ORM bundle avoids Prisma cold start penalty
- Better Auth: email/password + session management with zero vendor dependency, TypeScript-first, uses same DB via Drizzle adapter
- csv-parse 5.x: stream-native Node.js CSV parser, purpose-built for server-side, full TypeScript types
- Anthropic SDK (claude-haiku primary, claude-sonnet for narrative): Haiku handles all 186 structured checks; Sonnet only for final prose summary — cuts per-audit cost 70%+
- @react-pdf/renderer 4.3+: pure Node.js PDF, no Chromium, React JSX layout model, runs in Route Handlers
- Razorpay Node SDK 2.9+: native recurring subscription support via Plans + Subscriptions API; CommonJS, nodejs runtime only
- Resend: transactional email (audit ready, password reset), 3,000 emails/month free
- shadcn/ui + TanStack Table + Recharts: copy-paste component model, handles sortable/filterable check results table and score visualization

**Critical constraint:** Set `export const maxDuration = 60` and `export const runtime = 'nodejs'` on all audit and payment routes. Vercel Hobby plan's 10-second function timeout will cause intermittent Claude API timeouts — Vercel Pro plan is required for production.

### Expected Features

The 186-check reference library in `claude-ads/ads/references/` is the product's primary competitive advantage. It defines check coverage across 5 platforms that no competitor at this price point matches.

**Must have (table stakes):**
- CSV upload with platform auto-detection (Google, Meta, LinkedIn, TikTok, Microsoft schema detection by column signature, not filename)
- 0-100 weighted health score with A-F grade per platform
- Severity-graded findings list (Critical / High / Medium / Low) — users need to know what to fix first
- Prioritized recommendations with Quick Wins section (Critical/High severity + fix time under 15 minutes)
- Wasted spend identification — zero-conversion keywords, broad match + manual CPC, irrelevant search terms
- Conversion tracking checks (highest-weight category: 25% of Google score, equivalent weight on other platforms)
- PDF report export — professional, shareable; this is the deliverable users send to clients
- "How to export" guides per platform — users do not know which CSV to download
- Email/password auth with subscription gate ($29/mo via Razorpay)

**Should have (competitive differentiators):**
- Multi-platform audit in one session — no competitor below $149 does this; strongest pricing justification
- Cross-platform aggregate health score — budget-weighted composite across all uploaded platforms
- Estimated revenue impact per issue — converts "interesting" finding into "urgent" action
- AI-generated narrative (Claude) — explains why each issue matters in plain language, not just a checkbox
- Audit history (stored reports per user) — enables month-over-month score tracking
- Share link for audit report — freelancers/agencies want a URL to send clients, not just a PDF attachment
- Platform benchmark context in findings ("your CTR of 1.2% is below the 2.4% ecommerce average")

**Defer to v2+:**
- Before/after comparison view (requires audit history with 2+ stored audits)
- Revenue impact estimates (needs sufficient spend data; complex to implement reliably)
- White-label PDF for agency tier (logo upload, color palette — significant upsell but defers from MVP)
- Cross-platform aggregate score (needs all 5 platforms complete before meaningful)
- OAuth / API connectors (Google OAuth approval takes months; out of scope for CSV-first product)
- Real-time monitoring/alerts (incompatible with CSV point-in-time model)
- Custom check builder / rule engine (Adalysis power-user feature; 186 prebuilt checks are enough for v1)

### Architecture Approach

The architecture is a linear pipeline with clear component boundaries: Upload UI → /api/audit/upload (Route Handler) → CSV Parser → Audit Engine (pure TypeScript, no AI) → Claude API (narrative only) → Neon Postgres → Dashboard UI + /api/audit/[id]/pdf. Each component has one responsibility and communicates only with its immediate neighbors. The check runner is the most important component — it executes all 186 deterministic checks and scores them using the weighted formula from `scoring-system.md`, producing structured CheckResult[] that become the Claude prompt payload. Claude never sees raw CSV data.

**Major components:**
1. Platform Detector + Per-Platform Parser (`lib/parsers/`) — detects platform from column signature, normalizes to canonical NormalizedAdData schema with fuzzy column matching and confidence score
2. Audit Engine (`lib/engine/`) — runs all platform-specific checks as pure TypeScript functions, computes weighted score; no network calls; executes in under 200ms
3. AI Summarizer (`lib/ai/`) — sends check results (not raw CSV) to Claude with cached system prompt; parses JSON response into AuditInsights; prompt caching saves 90% on repeated system prompt tokens
4. Database Layer (`lib/db/`) — Drizzle ORM on Neon Postgres; three audit tables: `audits`, `audit_checks`, `audit_insights`; UUIDs for all record IDs
5. PDF Generator (`lib/pdf/`) — @react-pdf/renderer document component served from /api/audit/[id]/pdf Route Handler with Content-Disposition: attachment
6. Auth + Payments (`lib/auth/`, `lib/payments/`) — Better Auth session verification in every API handler; Razorpay webhook handler with raw body parsing and idempotency

### Critical Pitfalls

1. **Vercel 4.5 MB body limit blocks large CSV uploads** — Never route file bytes through serverless functions. Use presigned URLs to upload directly to Vercel Blob/S3; pass only the storage URL to the API route. Large accounts (the most valuable customers) hit this limit first. Must be the first thing built.

2. **Claude API costs blow unit economics without aggregation** — Never send raw CSV rows to Claude. Pre-aggregate to statistical summaries and pass only check results (~2–5 KB) from the deterministic engine. Cache the static system prompt. Without this, a single heavy user can cost more in API fees than their $29/month subscription.

3. **Platform CSV schemas change without notice; fuzzy matching is required** — Meta localizes column headers by account language; Google Ads has different headers across web UI, Editor, and API exports. Use alias maps for column detection. Log detected vs expected columns. Surface missing columns to the user rather than silently zeroing out metrics.

4. **CVE-2025-29927: Middleware-only auth leaves every API route exposed** — Next.js middleware can be bypassed via `x-middleware-subrequest` header manipulation. Verify session in every API route handler independently. Use UUID audit IDs (never sequential integers) to prevent enumeration.

5. **Claude narrative contradicts structured check results** — If Claude independently re-analyzes aggregated stats, it may reach different conclusions than the deterministic engine. Prompt Claude to explain and contextualize the specific check results that fired — not to independently assess the account. Claude's role is narration, not re-scoring.

---

## Implications for Roadmap

Based on research, the dependency graph drives a clear build order. The audit pipeline is the product core; auth and payments gate access but do not affect audit logic. Platform parsers have no dependencies on each other — Google alone is an MVP.

### Phase 1: Foundation — File Upload + Database + Auth
**Rationale:** Nothing else works without a user identity to attach audits to, and the Vercel body size limit pitfall must be solved before any feature is built on top of upload. Presigned URL upload pattern must be established first.
**Delivers:** Working auth (signup/login), database schema with UUID IDs, presigned URL upload to Vercel Blob, CSV received and stored server-side
**Addresses:** Auth requirement (table stakes), file upload requirement (table stakes)
**Avoids:** CVE-2025-29927 (session verification pattern established), Vercel 4.5 MB body limit (presigned URL pattern from day one), sequential ID enumeration (UUID schema standard set here)

### Phase 2: Google Ads Audit Engine (Core Product)
**Rationale:** The check runner is pure TypeScript with no external dependencies — most isolated, most testable phase. Google Ads has the most check coverage (74 checks, best-defined schema) and the largest market share. Ships the core product value without touching AI or payments.
**Delivers:** Google CSV detection + normalization, all 74 Google checks running, weighted score output (0-100, A-F grade), severity-graded CheckResult[] array, Quick Wins flagging
**Addresses:** Health score (table stakes), severity grading (table stakes), wasted spend identification (table stakes), conversion tracking checks (table stakes)
**Avoids:** Platform CSV schema pitfall (fuzzy column matching + confidence score built here), check runner cost (no AI cost in this phase — pure TypeScript)
**Research flag:** Standard patterns — Vercel/Next.js Route Handler patterns are well-documented; TypeScript check functions are straightforward implementation work

### Phase 3: AI Analysis Layer
**Rationale:** Requires check runner output as input. Must be designed with cost controls before connecting to any user-facing UI. Prompt caching and token budgeting must be validated against real check result payloads.
**Delivers:** Claude API integration, prompt builder (check results → structured prompt), response parser (JSON → AuditInsights), system prompt caching, Haiku for checks/Sonnet for narrative, per-audit token logging
**Addresses:** AI-generated narrative (differentiator), prioritized recommendations (table stakes)
**Avoids:** Claude cost blowout (aggregation pipeline designed before UI connection), Claude/check result contradiction (prompt instructs Claude to explain fired checks, not re-assess)
**Research flag:** Needs validation — prompt design for 186-check coverage is non-trivial; test prompt alignment between check results and AI narrative in QA before connecting dashboard

### Phase 4: Audit API Route + Persistence
**Rationale:** Integration point that wires all Phase 1–3 components. First time the full pipeline runs end-to-end. Test with real Google Ads CSV exports before proceeding to UI.
**Delivers:** /api/audit/upload (parse + check + AI + DB insert), /api/audit/[id] (fetch results), ownership verification, auditId returned to client
**Addresses:** Account structure (technical prerequisite for all features)
**Avoids:** Polling anti-pattern (server components fetch audit data once, immutable after completion)

### Phase 5: Dashboard UI + PDF Export
**Rationale:** Requires Phase 4 API routes returning real data. PDF can be built in parallel with dashboard components since both read from the same audit data shape.
**Delivers:** Upload UI with drag-and-drop + progress, results dashboard (score ring, check table, recommendations, quick wins), score category breakdown (transparency for Pitfall 8), PDF report generation via /api/audit/[id]/pdf
**Addresses:** PDF report export (table stakes), health score display with visible category breakdown, "how to export" onboarding guides
**Avoids:** PDF OOM/timeout (react-pdf chosen in Phase 1 stack decision; never Puppeteer), arbitrary-feeling health score (category breakdown and per-check deductions shown in UI)
**Research flag:** Standard patterns — shadcn/ui DataTable and @react-pdf/renderer are well-documented

### Phase 6: Payments + Subscription Gate
**Rationale:** Developed last to avoid blocking development iteration. Paywall middleware applied after all features are working and tested.
**Delivers:** Razorpay Plans + Subscriptions API integration, checkout flow, webhook handler (verify signature + idempotency + raw body), subscription status in DB, paywall on /dashboard
**Addresses:** Subscription billing (table stakes)
**Avoids:** Webhook delivery failures (async handler pattern: verify signature → write to DB → return 200 → async processing), Razorpay CommonJS in nodejs runtime only
**Research flag:** Needs care — webhook lifecycle (activated, charged, halted, cancelled, completed) must all be handled; use Razorpay's webhook testing tool before launch

### Phase 7: Multi-Platform Expansion (Meta → LinkedIn → TikTok → Microsoft)
**Rationale:** Google alone is a shippable MVP. Each additional platform adds market width and strengthens the multi-platform differentiator. Meta comes second (second-largest PPC market, 4 check categories defined). LinkedIn, TikTok, Microsoft follow.
**Delivers:** Per-platform parser + check files for each platform, platform-specific score display, multi-platform session state (upload checklist with per-platform status, persisted by session ID)
**Addresses:** Multi-platform in one session (key differentiator), cross-platform aggregate score (enabled when 2+ platforms complete)
**Avoids:** Multi-platform session state loss on browser refresh (uploads persisted to storage by session ID, not browser memory)
**Research flag:** Needs real CSV exports from each platform for parser testing; TikTok and Microsoft schemas are least documented — source test exports before building parsers

### Phase 8: Retention Features (Audit History + Share Links)
**Rationale:** Retention layer after core product is proven and paying subscribers exist.
**Delivers:** Stored audit list per user, score delta display (month-over-month improvement), shareable read-only audit URL
**Addresses:** Audit history (differentiator), share link (differentiator)

### Phase Ordering Rationale

- Foundation (Phase 1) must come first because auth establishes user identity for all audit records, and the presigned URL upload pattern must be established before any CSV processing is built on top of it.
- Audit Engine (Phase 2) before AI Layer (Phase 3) because Claude receives check results as input — the engine output defines the prompt schema.
- API Route (Phase 4) before Dashboard UI (Phase 5) because the UI requires real data from the pipeline to build against meaningfully.
- Payments (Phase 6) last because it gates the product but does not affect any of the product logic — developing it last avoids a paywall blocking development iteration.
- Platform Expansion (Phase 7) after a working Google-only MVP because each platform parser requires sourcing real CSV exports for testing, which is time-consuming and shouldn't delay the core product proving its value.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (AI Analysis):** Prompt engineering for 186-check context is non-trivial. Validate prompt structure and output schema with real check results before wiring to UI. Verify prompt caching behavior with the specific system prompt size.
- **Phase 6 (Payments):** Razorpay webhook edge cases (halted, cancelled, payment retry scenarios) need full mapping before launch. The raw body parsing requirement is easy to get wrong in Next.js App Router.
- **Phase 7 (Multi-Platform):** Each platform parser needs real CSV exports from multiple account types and regions for testing. TikTok and Microsoft are least documented — validate column schema assumptions before building.

Phases with standard patterns (research-phase not needed):
- **Phase 1 (Foundation):** Presigned URL upload, Better Auth setup, Drizzle schema — all well-documented patterns with official guides.
- **Phase 2 (Audit Engine):** Pure TypeScript check functions, no novel patterns. The check logic is already fully specified in `claude-ads/ads/references/`.
- **Phase 5 (Dashboard + PDF):** shadcn/ui DataTable and @react-pdf/renderer have clear documentation and examples.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core choices verified against official docs and 2026 community consensus. One inconsistency: ARCHITECTURE.md uses Supabase while STACK.md recommends Neon + Drizzle. STACK.md is authoritative — more current analysis with stronger rationale. |
| Features | HIGH | Grounded in existing 186-check claude-ads reference library and direct competitor feature analysis (Opteo, Adalysis, PPC Rocket, Optmyzr). Feature complexity estimates are MEDIUM — solo dev estimates that may encounter CSV schema edge cases. |
| Architecture | HIGH | Vercel limits verified against official docs. Pipeline design is sound and follows established Next.js App Router patterns. PDF approach (react-pdf) is MEDIUM — community-confirmed but less tested at scale than Puppeteer. |
| Pitfalls | HIGH | Infrastructure limits (Vercel 4.5 MB, function timeouts) from official Vercel docs. CVE-2025-29927 is publicly documented. CSV schema instability confirmed by Meta's own documentation. AI cost structure from official Claude pricing. |

**Overall confidence:** HIGH

### Gaps to Address

- **Stack conflict resolution:** ARCHITECTURE.md and STACK.md disagree on database (Supabase vs Neon). Resolve explicitly at project start by choosing Neon + Drizzle + Better Auth (STACK.md recommendation) — this decision affects schema, auth config, and DB client setup everywhere.
- **Real CSV exports for parser testing:** All platform parsers must be tested against real exports from multiple account types before shipping. This is not a research gap but an execution dependency — source 2–3 real CSV exports per platform before starting Phase 7.
- **Claude prompt token measurement:** The 186-check system prompt size in tokens needs to be measured before Phase 3 to confirm prompt caching applies (caching requires the cached content to be above a minimum token threshold) and to set accurate per-audit cost estimates.
- **Vercel plan requirement:** The architecture requires Vercel Pro plan (not Hobby) for the 60-second function timeout. This is a known hard requirement — budget for it before launch.
- **Revenue impact estimation:** The "estimated revenue impact per issue" differentiator is high-complexity and deferred to Phase 3+. The estimation methodology (spend data from CSV + benchmark wastage rates) needs design work before implementation.

---

## Sources

### Primary (HIGH confidence)
- `claude-ads/ads/references/` — 186-check reference library, scoring system, platform benchmarks (proprietary research, directly usable)
- Vercel Function Limitations (official): https://vercel.com/docs/functions/limitations
- Vercel body size limit KB (official): https://vercel.com/kb/guide/how-to-bypass-vercel-body-size-limit-serverless-functions
- Vercel maxDuration configuration (official): https://vercel.com/docs/functions/configuring-functions/duration
- Claude API prompt caching (official): https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Claude API pricing (official): https://platform.claude.com/docs/en/about-claude/pricing
- Razorpay webhook best practices (official): https://razorpay.com/docs/webhooks/best-practices/
- Meta CSV column name discrepancies (official): https://en-gb.facebook.com/business/help/1462433740708893
- Puppeteer on Vercel challenges (official Vercel KB): https://vercel.com/kb/guide/deploying-puppeteer-with-nextjs-on-vercel

### Secondary (MEDIUM confidence)
- Better Auth vs NextAuth vs Clerk (2026): https://supastarter.dev/blog/better-auth-vs-nextauth-vs-clerk
- Drizzle vs Prisma cold starts: https://dev.to/jsgurujobs/6-prisma-vs-drizzle-patterns-that-cut-serverless-cold-starts-by-700ms-5dl5
- Neon vs Supabase reliability (2025): https://dev.to/dataformathub/serverless-postgresql-2025-the-truth-about-supabase-neon-and-planetscale-7lf
- Razorpay Next.js App Router integration: https://www.akkhil.dev/blogs/razorpay-integration-with-nextjs
- @react-pdf/renderer App Router compatibility: https://github.com/diegomura/react-pdf/discussions/2402
- csv-parse vs PapaParse comparison: https://npm-compare.com/csv-parse,csv-parser,fast-csv,papaparse

### Tertiary (LOW confidence)
- Claude cost projections at scale — based on current API pricing; Anthropic has adjusted pricing multiple times; re-validate before setting subscription pricing
- Fluid Compute extended durations (Inngest blog): https://www.inngest.com/blog/how-to-solve-nextjs-timeouts — corroborated by Vercel docs but third-party source

---

*Research completed: 2026-03-17*
*Ready for roadmap: yes*
