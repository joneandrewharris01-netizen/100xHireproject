# Technology Stack: AdNerve

**Project:** AdNerve — CSV-based multi-platform ad audit SaaS
**Researched:** 2026-03-17
**Confidence:** HIGH (most choices verified against current docs/community sources)

---

## Context

This is a brownfield addition to an existing Next.js 16 + Tailwind v4 app. Every choice
must integrate with what exists without forcing a rewrite. The project is solo-built,
MVP-first, deployed on Vercel free tier. Cost sensitivity is real: Claude API costs money
per audit, so prompt engineering is part of the stack decision.

---

## Recommended Stack

### Core Framework (Existing — Do Not Change)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Next.js | 16.x | Full-stack React framework | Already in place; App Router gives server actions for audit processing without a separate backend |
| Tailwind CSS | v4 | Styling | Already in place; v4's new engine is faster and has no config file |
| TypeScript | 5.x strict | Type safety | Already in place; strict mode catches CSV schema mismatches at compile time |

### Database

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Neon Postgres | Current | Primary datastore | Serverless Postgres with auto-suspend (free tier viable for MVP). Native Vercel integration — one click to provision. Auto-suspends after 5 min idle so free tier lasts. Neon beats Supabase here because we don't need Supabase's auth/storage/realtime extras (we handle auth ourselves). |
| Drizzle ORM | 0.39+ | Database access layer | Chosen over Prisma for two concrete reasons: (1) 7.4KB bundle vs Prisma's ~40KB — meaningful for Vercel cold starts; (2) TypeScript-first schema with instant type inference, no `prisma generate` step. SQL-adjacent API means queries are readable and debuggable. |

### Authentication

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Better Auth | 1.x | Email + password auth | The 2026 consensus pick for solo Next.js SaaS. Beats NextAuth v5 (Auth.js) because email/password + session management with Auth.js requires 40-80 hours of custom work for production-ready setup. Beats Clerk because Clerk's free tier is limited and adds vendor lock-in for a product this simple. Better Auth is TypeScript-first, self-hosted (your DB, your data), zero vendor dependency, and ships email/password + session handling out of the box with minimal boilerplate. |

### CSV Parsing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| csv-parse | 5.x | Server-side CSV parsing | Runs in Node.js route handlers (Server Actions / API routes). Stream-based — processes large files without loading everything into memory. Chosen over PapaParse because PapaParse is browser-first; its synchronous API works in serverless but is not stream-native. csv-parse is the purpose-built Node.js solution with full TypeScript types. |

**Critical constraint:** Vercel's 4.5MB hard limit on serverless function payloads applies to
API routes. Ad platform CSVs are typically 50KB–2MB, which is safe. For any CSV approaching
4MB, parse client-side first and send structured JSON (not raw file) to the server. Implement
a client-side file size check and reject anything over 4MB with a clear error before upload.

### File Upload

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Vercel Blob | Current | Temporary CSV storage | If files need to be stored before processing (e.g., for retry or async processing), Vercel Blob is the zero-config option already on the Vercel platform. For MVP, parse the CSV inline in the upload Server Action without persisting the raw file — reduces complexity and storage cost. |

### AI Analysis

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Anthropic SDK (`@anthropic-ai/sdk`) | 0.39+ | Claude API client | Official SDK. Use `claude-3-5-haiku-20241022` as the primary model — significantly cheaper than Sonnet/Opus while producing structured JSON outputs reliably for rule-based audit scoring. Reserve `claude-3-5-sonnet-20241022` only for the narrative recommendation section where prose quality matters. |

**Cost optimization strategy (HIGH importance — directly affects unit economics):**

1. **Prompt caching:** Cache the system prompt containing the 186-check rule library. Cache writes cost 1.25x but reads cost 0.1x. After the first request, every subsequent audit re-reading the same system prompt saves 90% on that token block. Add `cache_control: { type: "ephemeral" }` to the system message.
2. **Structured output:** Request JSON output directly. Parse the Claude response into your scoring schema server-side. Never send raw CSV text to Claude — pre-process it into a compact summary object (key metrics, flagged rows) before sending.
3. **Haiku-first:** Run all 186 checks through Haiku. Only invoke Sonnet for the final 2-3 paragraph "executive summary" narrative. This can cut per-audit cost by 70%+.

Estimated cost per audit with this strategy: ~$0.008–0.02 per audit at $29/mo subscription — viable margin.

### PDF Generation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `@react-pdf/renderer` | 4.3.x | PDF report export | Chosen over Puppeteer and jsPDF. Puppeteer spins up a full Chromium instance — too heavy for Vercel serverless (cold start, memory). jsPDF is browser-only (uses html2canvas, can't run in Node). `@react-pdf/renderer` runs server-side in a Route Handler, produces proper vector PDFs, and you define the layout in JSX — same mental model as the rest of the app. **Important:** Must be called from a Route Handler (`/api/report/[id]/pdf`), NOT a Server Component. Add `serverExternalPackages: ['@react-pdf/renderer']` to `next.config.ts` to prevent bundling issues. Return the PDF as a streamed response with `Content-Disposition: attachment`. |

### Payments

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `razorpay` (Node SDK) | 2.9+ | Subscription billing | User preference confirmed. Razorpay supports recurring subscriptions natively via Plans + Subscriptions API. Integration pattern: (1) Create Plan via Razorpay dashboard/API, (2) create Subscription server-side, (3) load Razorpay checkout.js client-side to collect payment method, (4) verify via webhook. |

**Webhook verification is mandatory.** Never trust the client-side callback as payment confirmation. Verify every `subscription.charged` webhook using HMAC-SHA256 against your Razorpay webhook secret. Store the `x-razorpay-event-id` header and skip duplicate events (Razorpay retries failed webhooks).

### UI Components

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| shadcn/ui | Latest (copy-paste model) | Dashboard components | The project already uses Tailwind v4. shadcn/ui components are copy-pasted into `/components/ui/` — no runtime dependency, full control over styling. DataTable (wraps TanStack Table v8) handles audit results with sorting/filtering. Use Card, Badge (severity grades), Progress (health score), and Tabs (per-platform breakdown). |
| TanStack Table | v8 | Data table for audit results | Ships inside shadcn/ui's DataTable. Handles sorting by severity, filtering by check category, pagination for 190+ checks. No additional installation beyond shadcn scaffolding. |
| Recharts | 3.x | Score visualization | Ships with shadcn chart components. Use for the 0-100 health score gauge and category breakdown radar chart. |

### Email

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Resend | Current | Transactional email | Send audit-ready notifications, password reset, subscription receipts. Free tier: 3,000 emails/month. The `resend` npm package integrates directly with Next.js Server Actions. Chosen over Nodemailer (manual SMTP config) and SendGrid (overkill for solo MVP). |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Auth | Better Auth | Clerk | Free tier limits; vendor lock-in; unnecessary managed overhead for email+password only |
| Auth | Better Auth | NextAuth v5 (Auth.js) | Email/password in Auth.js requires custom pages, DB adapter, session config — 40-80hr implementation vs Better Auth's 2hrs |
| Database | Neon + Drizzle | Supabase | Supabase bundles auth/realtime/storage we're not using; paying for features we replace with better-suited tools |
| Database | Drizzle | Prisma | Prisma's 40KB bundle bloat hits Vercel cold starts; `prisma generate` step adds friction in solo dev |
| PDF | @react-pdf/renderer | Puppeteer | Puppeteer needs Chromium — too heavy for serverless; memory limit issues on Vercel free tier |
| PDF | @react-pdf/renderer | jsPDF | jsPDF is browser-only, can't run in Route Handlers |
| CSV Parsing | csv-parse | PapaParse | PapaParse is browser-optimized; csv-parse is the purpose-built server-side choice |
| AI Model | Claude Haiku (primary) | Claude Sonnet (primary) | Sonnet is 5x more expensive per token; Haiku handles structured JSON scoring reliably |

---

## Installation

```bash
# Database + ORM
npm install drizzle-orm @neondatabase/serverless
npm install -D drizzle-kit

# Auth
npm install better-auth

# CSV parsing
npm install csv-parse

# AI
npm install @anthropic-ai/sdk

# PDF generation
npm install @react-pdf/renderer

# Payments
npm install razorpay

# Email
npm install resend

# UI (shadcn/ui is copy-paste, not npm install — use CLI)
npx shadcn@latest init
npx shadcn@latest add table card badge progress tabs chart
```

**next.config.ts addition required:**
```typescript
const nextConfig = {
  // existing config...
  serverExternalPackages: ['@react-pdf/renderer'],
};
```

---

## Key Version Constraints

- `@react-pdf/renderer` requires `>= 4.1.0` for React 19 support. Lock to `^4.3.2`.
- `csv-parse` v5+ uses ESM by default. Import as: `import { parse } from 'csv-parse/sync'` for simple cases or use streaming API for large files.
- Better Auth requires a database adapter. Use `drizzle` adapter — avoids running two separate DB libraries.
- Razorpay's Node SDK (`razorpay@2.9+`) is CommonJS. Import in Route Handlers only (not Edge Runtime). Set route config to `export const runtime = 'nodejs'`.

---

## Sources

- Better Auth vs NextAuth vs Clerk comparison (2026): https://supastarter.dev/blog/better-auth-vs-nextauth-vs-clerk
- Drizzle vs Prisma serverless cold starts: https://dev.to/jsgurujobs/6-prisma-vs-drizzle-patterns-that-cut-serverless-cold-starts-by-700ms-5dl5
- Neon vs Supabase for Vercel: https://hrekov.com/blog/vercel-vs-supabase-database-comparison
- @react-pdf/renderer Next.js App Router: https://github.com/diegomura/react-pdf/discussions/2402
- Vercel 4.5MB body size limit: https://vercel.com/kb/guide/how-to-bypass-vercel-body-size-limit-serverless-functions
- Razorpay Next.js App Router integration: https://www.akkhil.dev/blogs/razorpay-integration-with-nextjs
- Claude API prompt caching guide: https://www.aifreeapi.com/en/posts/claude-api-prompt-caching-guide
- csv-parse vs PapaParse comparison: https://npm-compare.com/csv-parse,csv-parser,fast-csv,papaparse
- shadcn/ui DataTable docs: https://ui.shadcn.com/docs/components/radix/data-table
- Better Auth Next.js docs: https://better-auth.com/docs/integrations/next
