# Domain Pitfalls

**Domain:** CSV-upload AI audit SaaS (AdNerve — ad platform auditing)
**Researched:** 2026-03-17
**Confidence:** HIGH (infrastructure limits from official Vercel/Razorpay docs), MEDIUM (CSV parsing, auth), LOW (some LLM cost projection specifics)

---

## Critical Pitfalls

Mistakes that cause rewrites, security incidents, or silent product failures.

---

### Pitfall 1: Vercel 4.5 MB Request Body Limit Kills Large CSV Uploads

**What goes wrong:** A user exports 12 months of Google Ads data — 8,000 rows across campaigns, ad groups, and keywords. The CSV is 6 MB. The Next.js API route receives the upload, Vercel rejects it with `413: FUNCTION_PAYLOAD_TOO_LARGE`, and the user sees a generic error or blank screen. The product appears broken on the most valuable use case (large accounts).

**Why it happens:** Vercel serverless functions enforce a hard 4.5 MB request body limit. CSV files from large ad accounts regularly exceed this — Google Ads Editor exports with many columns can hit 10+ MB. Piping the upload through a Next.js API route is the intuitive approach but fails silently or with cryptic errors.

**Consequences:** Largest and most valuable customers (enterprise advertisers with big accounts) are the ones most likely to hit this limit. Free-tier accounts with small campaigns will work fine; paid subscribers will see failures. This creates a perverse churn pattern where your best customers can't use the product.

**Prevention:** Never route file bytes through Vercel serverless functions. Use presigned URLs to upload directly from browser to object storage (Vercel Blob, AWS S3, Cloudflare R2), then pass only the storage URL to the API route for processing. The API function fetches and parses the file server-side without the upload passing through the function body.

```
Browser → presigned URL → Blob storage
Browser → API route (sends storage URL only, no file bytes)
API route → fetches file from storage → parses → sends to Claude
```

**Warning signs:** Any upload > 4 MB fails. Users with multiple-platform uploads (uploading 5 CSVs in one session) hit the limit even with small individual files if done as multipart.

**Detection:** Test with a real 30-day Google Ads export from an account with 500+ keywords before launch.

**Phase:** Must address in the CSV upload phase, before any other feature work on top of it.

---

### Pitfall 2: Claude API Costs Blow Up Without Per-Audit Budgets

**What goes wrong:** A user uploads a 5,000-row Google Ads export. The naive approach sends the entire CSV to Claude as context. At ~4 characters per token, 5,000 rows × 15 columns × 20 chars = 1.5M characters = ~375K tokens per audit. At Claude Sonnet pricing, this is $1.13 in input tokens alone — 4% of a monthly subscription per audit. A user who runs 30 audits/month costs $33.90 in API fees alone, at a loss.

**Why it happens:** CSV data is dense and wide. Each row has many numeric columns. It is tempting to dump the whole file into the prompt. The 186-check reference library in `claude-ads/` is comprehensive, which means the system prompt is also large — compounding cost.

**Consequences:** Gross margin goes negative on heavy users. At $29/mo subscription with even 10% API cost ceiling, each audit must cost under $0.29. Raw CSV dumps blow this budget on any real account.

**Prevention:**
- Never send raw CSV rows to Claude. Pre-aggregate to statistical summaries before sending: min, max, mean, p25, p50, p75, count of anomalies per metric column.
- Use Claude's prompt caching for the static system prompt (the 186 checks, scoring rules, output format). The system prompt is identical for every audit — cache it. Cached tokens cost 90% less on re-reads.
- Set a hard token budget per audit and enforce it server-side before sending to Claude.
- Parse the CSV yourself (in Node/Python), compute rule-based checks (CTR < 1%, CPC > industry average, Quality Score < 6), and only send flagged anomalies to Claude for natural language explanation — not the full dataset.

**Warning signs:** Audit latency > 30 seconds (sign you're sending too much data). Claude responses contain references to specific rows (sign you're not pre-aggregating).

**Detection:** Log input/output token counts for every Claude call from day one. Set a billing alert at $50/month on Anthropic console before launch.

**Phase:** AI analysis engine phase. Design the aggregation pipeline before wiring Claude — do not bolt it on afterward.

---

### Pitfall 3: Platform CSV Schemas Are Inconsistent and Change Without Notice

**What goes wrong:** You build the Meta Ads parser against the column headers from your own test export. Three months later, a user from a different region exports their data — Meta renders column headers in the user's account language (French, Spanish, Portuguese). Or Meta silently renames "Amount spent" to "Spend" in a UI update, and your parser returns null for all spend values, producing a meaningless audit with 0s everywhere.

**Why it happens:** Meta's own documentation explicitly notes that "field names and column names in the import/export spreadsheet aren't the same" as what you see in Ads Manager. Google Ads Editor column names differ from Google Ads web interface exports, which differ from Google Ads API report exports. TikTok Ads and LinkedIn Ads have even less stable export schemas. Platforms localise headers based on account locale settings.

**Consequences:** Silent data corruption — the audit runs and produces a score, but all the underlying data is wrong. Users trust the AI analysis without knowing the parser silently zeroed out key metrics.

**Prevention:**
- Parse columns by fuzzy matching, not exact string match. Use a canonical alias map: `{"amount spent": "spend", "cost": "spend", "spend (usd)": "spend"}` and normalize to internal names.
- Always log which columns were detected and which were expected but missing. Surface this to the user: "We detected 12 of 15 expected columns. Missing: Quality Score, Impression Share."
- Version your parser per platform and test against multiple real exports from different account types, date ranges, and regions before launch.
- Store the raw column headers from every uploaded file in your database for forensic debugging.
- Never fail silently on a missing column — return a partial audit with a clear notice about what data was missing.

**Warning signs:** Audit produces all-zero values for any metric. Health score is suspiciously round (e.g., exactly 50). Users report "the numbers don't match my dashboard."

**Detection:** Build a column detection confidence score into the parser output: "12/15 expected columns found (80% confidence)."

**Phase:** CSV parsing phase — per-platform parser must include fuzzy matching and column audit from day one.

---

### Pitfall 4: Middleware-Only Auth Leaves API Routes Unprotected (CVE-2025-29927)

**What goes wrong:** You protect the dashboard with Next.js middleware that checks for a valid session and redirects unauthenticated users to `/login`. The API routes at `/api/audit`, `/api/report` are assumed protected because middleware runs first. An attacker sends requests directly to the API routes with a crafted `x-middleware-subrequest` header, bypassing middleware entirely, and gets full audit results without a subscription.

**Why it happens:** CVE-2025-29927, disclosed March 2025, allows complete bypass of Next.js middleware by manipulating the `x-middleware-subrequest` header. This is a known, documented vulnerability. Any Next.js app relying solely on middleware for auth is vulnerable.

**Consequences:** Non-subscribers can query the AI audit endpoint for free. Data from other users' audits could be accessible if audit IDs are guessable (sequential integers). Free users can generate unlimited PDF reports.

**Prevention:**
- Verify the session at every API route handler, not just in middleware. Middleware is a redirect layer for UX — not a security boundary.
- Use Clerk's `auth()` server-side helper or NextAuth's `getServerSession()` in every API handler before processing any request.
- Use non-sequential, non-guessable IDs for audit records (UUIDs v4, not auto-increment integers).
- Check subscription status at the API handler level, not just on the frontend.

**Warning signs:** API routes return data without checking `Authorization` headers. Any `fetch('/api/audit')` from the browser console works without a login cookie.

**Detection:** Write an integration test that calls API routes with no session cookie and assert 401 responses before shipping.

**Phase:** Auth phase — verify this pattern is established before building any protected feature on top of it.

---

## Moderate Pitfalls

Mistakes that degrade user experience, inflate costs, or create debt that slows future development.

---

### Pitfall 5: Razorpay Webhooks Drop Subscription Status Updates

**What goes wrong:** A user subscribes, Razorpay charges them, but the webhook to your `/api/webhooks/razorpay` route times out (> 5 seconds) or returns a non-2xx because your PDF generation is running synchronously in the same process. Razorpay marks the delivery as failed. The user's subscription status in your database stays as "free" even though they paid. They can't access audit features. Support ticket follows.

**Why it happens:** Razorpay uses at-least-once delivery semantics with exponential backoff retry for 24 hours after the event. If your webhook handler does any heavy work synchronously (sending a welcome email, triggering an audit, writing to a slow DB), it may exceed the 5-second response window.

**Consequences:** Paid users are locked out. Churn from payment processing confusion. Potential double-subscription if user retries checkout.

**Prevention:**
- Webhook handler must do exactly three things: verify signature, write event to DB, return 200. All other logic runs asynchronously after.
- Validate webhook signature using raw request body — do NOT parse the body before signature verification (Next.js body parsers modify the raw bytes).
- Implement idempotency: store the Razorpay event ID and reject duplicate webhook deliveries.
- In `next.config.js`, set `api.bodyParser: false` for the webhook route and manually parse raw bytes.
- Handle the full subscription lifecycle: `subscription.activated`, `subscription.charged`, `subscription.halted`, `subscription.cancelled`, `subscription.completed`.

**Warning signs:** Users report paying but not getting access. Razorpay dashboard shows webhook delivery failures. Subscription status mismatches between Razorpay dashboard and your DB.

**Detection:** Use Razorpay's webhook testing tool in the dashboard to fire sample events at your endpoint before launch.

**Phase:** Payments phase — test the full webhook lifecycle end-to-end including failure/retry scenarios.

---

### Pitfall 6: PDF Generation Fails or OOMs on Vercel Serverless

**What goes wrong:** You use Puppeteer to generate the audit PDF report. Puppeteer requires spawning a full Chromium browser process. Vercel serverless functions have a 512 MB memory limit (default) and a 10-second execution timeout (on free tier). Puppeteer + Chromium easily uses 300-400 MB and takes 8-15 seconds to generate a multi-page PDF. The function times out or OOMs. Users click "Download Report" and get an error.

**Why it happens:** Puppeteer is standard for HTML-to-PDF in Node.js, but it's architected for long-running server processes, not serverless functions. Spinning up a new Chromium instance per request is prohibitively expensive in a serverless context.

**Consequences:** PDF export is broken for all users. This is a marquee feature (reports for clients) — its failure damages perceived product quality significantly.

**Prevention:**
- Use `@react-pdf/renderer` (pure JavaScript, no browser required, generates PDFs from React components). It runs fine in serverless with no external dependencies and produces deterministic output. The audit data is structured (scores, checks, recommendations) — react-pdf is well-suited to this shape.
- Alternatively, use an external PDF service (Browserless, Gotenberg) and treat PDF generation as an async job: queue it, poll for completion, provide a download link.
- Do not use Puppeteer in Vercel serverless functions.

**Warning signs:** PDF generation takes > 3 seconds locally. Any Chromium-related imports in the API route.

**Detection:** Measure PDF generation memory usage locally with `--max-old-space-size=512` Node flag before deploying.

**Phase:** Dashboard and reporting phase — pick the PDF library before building the report template.

---

### Pitfall 7: LLM Recommendations Contradict the Structured Check Results

**What goes wrong:** Your rule-based parser flags a campaign for "CTR below 1% — critical issue." Claude's natural language summary, generated from pre-aggregated stats, says "CTR performance is within acceptable range." The user sees conflicting signals: the check card says critical, the AI summary says it's fine. Trust evaporates. They don't know which to believe.

**Why it happens:** The pre-aggregated summary sent to Claude omits the raw CTR values or frames them differently. Claude uses different benchmarks than your hard-coded thresholds. Or the prompt instructs Claude to "identify the top 3 issues" and it picks different priorities than your severity-weighted algorithm.

**Consequences:** Users lose confidence in the product. If the AI contradicts the checks, either the checks are wrong or the AI is wrong — both interpretations are damaging.

**Prevention:**
- The Claude prompt must include the exact check results (what fired, at what severity) and instruct Claude to elaborate on those findings — not independently re-assess the data. Claude's role is explanation and actionability, not independent analysis.
- Pass severity-graded check names and trigger values explicitly: "The following checks fired: [CRITICAL] Average CPC $4.23 exceeds industry benchmark $1.80 for your category. Explain why this is a problem and give 3 specific fixes."
- Never let Claude contradict a structured check result — it should only amplify and contextualize them.

**Warning signs:** Claude response contains phrases like "overall the account looks healthy" when critical checks fired. Recommendations mention metrics not present in the check results.

**Detection:** During QA, run the same audit 3 times and compare Claude outputs for consistency. Any contradiction between check results and AI narrative is a prompt defect.

**Phase:** AI analysis engine phase — validate prompt alignment with check results before connecting the UI.

---

### Pitfall 8: Health Score Feels Arbitrary Without Visible Calculation Logic

**What goes wrong:** User gets a 67/100 health score. They have no idea why. They change one thing in their ad account, re-upload, get 65/100. They expected improvement but the score went down. They think the product is broken or random. They churn.

**Why it happens:** The health score is a weighted aggregate of many checks. Small changes in input data (date range, included campaigns) can shift the score significantly due to weighting. If the score calculation is invisible, users can't trust it or act on it.

**Consequences:** The health score is the headline feature. If users distrust the score, they distrust the entire product.

**Prevention:**
- Show score breakdown by category (e.g., "Quality Score: 18/25, Budget Efficiency: 22/25, Ad Creative: 14/25, Targeting: 13/25").
- Show which checks contributed most to point deductions. "You lost 8 points from 3 campaigns with Quality Score below 5."
- Explain what "67/100" means in plain language: "Average — you have critical issues that are likely wasting 20-30% of your ad budget."
- Document the scoring methodology in the UI (a "how we score" tooltip or page).

**Warning signs:** Users in support asking "why did my score change?" or "what does this score mean?" more than once.

**Detection:** User test the score display with 3 people who are NOT ad experts before launch. If they can't explain their score back to you, the UI needs work.

**Phase:** Dashboard phase — design score transparency into the UI spec before building.

---

## Minor Pitfalls

Issues that cause friction but are recoverable without a rewrite.

---

### Pitfall 9: "How to Export" Guides Go Stale as Platforms Update Their UIs

**What goes wrong:** You write step-by-step export instructions with screenshots for Meta Ads Manager. Meta does a UI redesign (they do this frequently). The menu is now under a different location. Users follow your screenshots and can't find the export button. They blame your product for being confusing.

**Prevention:** Write export instructions as text steps with minimal screenshot reliance. Focus on the navigation path ("Reports > Scheduled Reports > Export > CSV") rather than visual landmarks. Include a "last verified" date on each guide. Build the guides as MDX so they can be updated without a code deploy.

**Phase:** Onboarding/UX phase. Do not invest heavily in screenshoted guides — text-only is more maintainable.

---

### Pitfall 10: Encoding Issues Corrupt Non-ASCII Account and Ad Names

**What goes wrong:** A user manages Google Ads for a Japanese e-commerce brand. The campaign names contain Japanese characters. The CSV uses UTF-8 encoding, but your Node.js CSV parser defaults to latin-1. The campaign names display as garbled characters in the audit UI and PDF report. The user thinks the product corrupted their data.

**Prevention:** Always specify `encoding: 'utf-8'` explicitly in your CSV parser. Test with a CSV file containing emoji, Chinese characters, and accented Latin characters (é, ü, ñ) before launch. The `papaparse` library handles encoding well when configured correctly.

**Phase:** CSV parsing phase — add multi-encoding test to the parser validation suite.

---

### Pitfall 11: Sequential Audit IDs Enable Enumeration Attacks

**What goes wrong:** Audit results are stored at `/audit/1234`. A logged-in user (even on free tier) can increment the ID and view another user's audit results. Ad account data (spend, campaigns, CTR) is commercially sensitive.

**Prevention:** Use UUIDs (v4) for all audit record IDs. Never expose sequential database primary keys in URLs or API responses.

**Phase:** Data modeling phase — set this as a schema standard before writing any API routes.

---

### Pitfall 12: Multi-Platform Audit Session State Is Hard to Recover

**What goes wrong:** The user intends to upload CSVs from Google Ads, Meta, and LinkedIn in one session to get a combined multi-platform audit. They upload Google Ads successfully. While uploading Meta, their browser tab refreshes. The Google Ads upload is lost. They have to start over.

**Prevention:** Upload each CSV immediately on selection and persist it to the server/storage. Show a checklist UI with per-platform upload status (uploaded/pending/error). Users should be able to close and re-open the session without losing previously uploaded files. Tie uploads to a session ID stored in the database, not just browser memory.

**Phase:** Multi-platform audit phase — design the session state model before building the upload UI.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| CSV parsing setup | Silent schema mismatch on Meta/TikTok exports | Fuzzy column matching + column audit log from day one |
| File upload implementation | Vercel 4.5 MB body limit blocks large accounts | Presigned URL upload to Blob storage before building any parser |
| AI analysis engine | Claude costs blow budget on raw CSV input | Aggregate to stats first, cache system prompt, log token counts |
| AI analysis engine | Claude narrative contradicts structured check results | Prompt Claude to explain checks, not re-analyze independently |
| Payments integration | Webhook delivery failures lock out paid users | Async handler pattern, idempotency, raw body for signature |
| Auth implementation | Middleware bypass (CVE-2025-29927) exposes API routes | Server-side session check in every API handler |
| PDF report generation | Puppeteer OOM/timeout on Vercel serverless | Use react-pdf, avoid Chromium in serverless |
| Health score display | Score feels arbitrary, users can't act on it | Show category breakdown and per-check point deductions in UI |
| Multi-platform sessions | Upload state lost on browser refresh | Persist uploads to storage by session ID, not browser memory |

---

## Sources

- [Vercel Function Limitations (official)](https://vercel.com/docs/functions/limitations)
- [How to Bypass Vercel's 4.5MB Body Size Limit (Supabase)](https://medium.com/@jpnreddy25/how-to-bypass-vercels-4-5mb-body-size-limit-for-serverless-functions-using-supabase-09610d8ca387)
- [Razorpay Webhook Best Practices (official)](https://razorpay.com/docs/webhooks/best-practices/)
- [Razorpay Webhook FAQs (official)](https://razorpay.com/docs/webhooks/faqs/)
- [Meta Ads Manager: Differences between field names and CSV column names (official)](https://en-gb.facebook.com/business/help/1462433740708893)
- [Meta Ads Manager: Header Label Doesn't Match (official)](https://www.facebook.com/business/help/116845212334480)
- [CVE-2025-29927: Next.js Middleware Auth Bypass](https://clerk.com/articles/nextjs-session-management-solving-nextauth-persistence-issues)
- [Clerk Auth: Complete Authentication Guide for Next.js App Router 2025](https://clerk.com/articles/complete-authentication-guide-for-nextjs-app-router)
- [Claude API Pricing and Cost Optimization (official)](https://platform.claude.com/docs/en/about-claude/pricing)
- [Dromo: Common Data Import Errors](https://dromo.io/blog/common-data-import-errors-and-how-to-fix-them)
- [OneSchema: Best Practices for Building a CSV Uploader](https://www.oneschema.co/blog/building-a-csv-uploader)
- [How to Generate PDFs in 2025 — Node.js options comparison](https://dev.to/michal_szymanowski/how-to-generate-pdfs-in-2025-26gi)
- [Puppeteer PDF generation gotchas (Joyfill)](https://joyfill.io/blog/integrating-pdf-generation-into-node-js-backends-tips-gotchas)
- [LLM Hallucinations in Enterprise Applications (Glean)](https://www.glean.com/perspectives/when-llms-hallucinate-in-enterprise-contexts-and-how-contextual-grounding)
