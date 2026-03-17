# AdNerve

## What This Is

AdNerve is a $29/mo SaaS that lets marketers upload CSV exports from their ad platforms (Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads, Microsoft Ads) and receive an AI-powered audit report with a 0-100 health score, severity-graded checks, and prioritized recommendations. No OAuth required — users export data from their ad dashboard, upload it, and get results in under 60 seconds.

## Core Value

Users can upload ad platform CSV exports and instantly receive a scored, actionable audit report that identifies wasted spend and prioritizes fixes by revenue impact.

## Requirements

### Validated

- ✓ Landing page with brand, copy, pricing, waitlist form — existing
- ✓ Waitlist API with email collection — existing
- ✓ Dark theme design with GSAP/Lenis animations — existing
- ✓ Vercel deployment config — existing

### Active

- [ ] CSV upload for Google Ads exports
- [ ] CSV upload for Meta Ads exports
- [ ] CSV upload for LinkedIn, TikTok, Microsoft Ads exports
- [ ] AI-powered audit engine using Claude API (190+ checks)
- [ ] Health score calculation (0-100, weighted across categories)
- [ ] Severity-graded check results (critical/high/medium/low)
- [ ] Prioritized recommendations with estimated revenue impact
- [ ] Interactive web dashboard showing audit results
- [ ] PDF report export for clients/stakeholders
- [ ] User authentication (email + password)
- [ ] Razorpay subscription ($29/mo recurring)
- [ ] "How to export" guides for each platform (screenshots/instructions)
- [ ] Multi-platform audit (upload CSVs from multiple platforms in one session)

### Out of Scope

- OAuth/API connectors to ad platforms — Phase 0 is CSV-only, OAuth is future
- Real-time monitoring/alerts — CSV is point-in-time, not live
- AI competitor intelligence — requires ad library scraping, defer to v2
- Agency multi-account management — single business per subscription for v1
- Mobile app — web-first, responsive design sufficient
- LinkedIn Ads API / TikTok API integration — skip for v1, CSV handles this

## Context

**Market gap:** No paid tool between $0 and $149/mo does multi-platform ad audits. Advirtis (free, Google-only ChatGPT wrapper) and Optmyzr ($249+, OAuth-required) bracket a massive gap. Adalysis users said they want $25-30/mo pricing.

**CSV approach advantage:** No OAuth approval delays (Google has months-long backlog), no business verification (Meta requires registered entity), no API rate limits. Users feel safer uploading exports than giving account access to unknown tools.

**Existing assets:**
- Landing page: Next.js 16 + Tailwind v4 + GSAP + Lenis (fully built, production-ready)
- claude-ads: 186 checks across 6 platforms with weighted scoring (open source reference)
- Waitlist: JSON-based email collection already working

**Competitors:**
| Tool | Price | Platforms | Approach |
|------|-------|-----------|----------|
| Advirtis | Free | Google only | ChatGPT wrapper, lead gen |
| PPC Rocket | ~$20/mo | Google only | OAuth API |
| Opteo | $97-129/mo | Google only | OAuth API |
| Adalysis | $149+/mo | Google, Microsoft | OAuth API |
| Optmyzr | $249+/mo | Google, Microsoft | OAuth API |

**AdNerve positioning:** $29/mo, 5 platforms, CSV upload, AI-powered, modern UX.

## Constraints

- **AI Cost**: Claude API costs per audit — need to optimize prompt size and cache common patterns
- **Tech Stack**: Next.js 16 + Tailwind v4 (existing), TypeScript strict mode
- **Deployment**: Vercel (free tier for MVP, existing config)
- **Payment**: Razorpay (user preference, Indian payment gateway)
- **Auth**: Email + password via NextAuth or Clerk
- **CSV Parsing**: Must handle exports from 5 different platforms with different schemas/column names
- **Solo dev**: Ship fast, minimize complexity, avoid over-engineering

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CSV upload over OAuth | No API approval delays, ships in weeks not months, users feel safer | — Pending |
| Claude API for analysis | Already have 186-check reference library, produces natural language insights | — Pending |
| $29/mo subscription | Fills gap between free and $149+, matches what Adalysis users said they'd pay | — Pending |
| Razorpay over Stripe | User's preferred payment gateway | — Pending |
| Vercel deployment | Already configured, free tier sufficient for MVP | — Pending |
| Web dashboard + PDF | Interactive results for users, PDF for sharing with clients/stakeholders | — Pending |

---
*Last updated: 2026-03-17 after initialization*
