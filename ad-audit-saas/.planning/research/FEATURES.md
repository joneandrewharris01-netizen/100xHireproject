# Feature Landscape: Ad Audit SaaS (AdNerve)

**Domain:** Multi-platform PPC / paid advertising audit tool, CSV-upload, $29/mo SaaS
**Researched:** 2026-03-17
**Overall confidence:** HIGH — grounded in 186-check reference library (claude-ads), competitor analysis, and PPC audit industry research

---

## Table Stakes

Features users expect in any credible audit tool. Missing = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| CSV upload (any platform) | Core mechanism — no upload, no product | Low | Must handle Google, Meta, LinkedIn, TikTok, Microsoft schema variations |
| 0-100 health score per platform | Immediate answer to "how am I doing?" — Opteo, Adalysis, PPC Rocket all show this | Low | Weighted scoring already designed in `scoring-system.md` |
| Severity grading on checks | Users need to know what to fix first; critical vs low without this is noise | Low | 4-tier: Critical / High / Medium / Low — already in reference library |
| Prioritized recommendations list | The audit is useless without "what do I do now?" — competitors all lead with this | Medium | Ordered by severity x remediation time; Quick Wins flagged separately |
| Wasted spend identification | Primary reason users buy audit tools — "find the money leak" | Medium | Zero-conv keywords, broad match + manual CPC, irrelevant search terms |
| Conversion tracking checks | Foundation of all optimization; bad tracking = all other data is wrong | Medium | G42-G49 (11 checks) — highest weight category across all platforms |
| Account structure checks | Campaign/ad group organization is auditable from CSV data | Low | Naming conventions, brand/non-brand separation, budget allocation |
| PDF report export | Users share results with clients, managers, or team — report is the deliverable | Medium | Must be professional, not raw JSON; includes score, findings, recommendations |
| Platform-specific check categories | Google ≠ Meta ≠ LinkedIn — generic advice reads as irrelevant | Medium | Each platform has distinct weighted categories |
| "How to export" guides per platform | Users don't know which CSV to download from each platform | Low | Screenshot guides for Google, Meta, LinkedIn, TikTok, Microsoft |
| Authentication (login/account) | Users need to store audits and access their history | Low | Email + password; NextAuth or Clerk |
| Subscription billing | $29/mo recurring — users expect a proper paywall, not a one-time link | Low | Razorpay; free trial or freemium gate needed |

---

## Differentiators

Features that set AdNerve apart from the $0 (Advirtis) and $149+ (Adalysis/Optmyzr) bracket. Not expected, but converts and retains.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Multi-platform in one session | No competitor below $149 does this — unique to AdNerve at $29 | High | Upload CSVs from 2-5 platforms, get unified cross-platform health score |
| Cross-platform aggregate score | "Your overall ad portfolio scores 74/100 (Grade C)" — one number for executive summary | Medium | Budget-weighted aggregate: `Σ(Platform_Score × Platform_Budget_Share)` |
| Quick Wins section | Fixes that take <15 min and are Critical/High severity — immediate ROI | Low | Algorithm: `IF severity ∈ [Critical, High] AND fix_time < 15min THEN flag Quick Win` |
| Estimated revenue impact per issue | "Fixing this could recover ~$340/mo" — converts users from "interesting" to "urgent" | High | Requires spend data from CSV + benchmark wastage rates (10-25% typical) |
| AI-generated narrative (Claude) | Natural language explanation of why each issue matters — not just a checkbox | Medium | Claude API; already have 186-check prompts in claude-ads reference library |
| Audit history (stored reports) | Users can track improvement over time — re-run audit next month, compare score | Medium | Store JSON results per user; display score delta ("up 12 points since last audit") |
| "Before/After" comparison view | Run an audit, fix issues, re-upload, see score change — proves tool value | High | Requires audit history + diff rendering; defer to post-MVP |
| Share link for audit report | Freelancers/agencies want to send a link to clients, not attach a PDF | Low | Public shareable URL with read-only view of results |
| Platform benchmark context | "Your CTR of 1.2% is below the 2.4% industry average for ecommerce" | Medium | Use benchmarks from `benchmarks.md` in claude-ads reference library |
| White-label PDF | Agencies want branded reports — significant upsell surface for an agency plan | High | Logo upload, color palette, custom footer; defer to agency tier |
| Onboarding walkthrough | First-time PPC auditors need hand-holding through the upload + interpret flow | Low | Step-by-step UI; not complex but neglected by most tools |

---

## Anti-Features

Features to explicitly NOT build in Phase 1 (and likely Phase 2). Each has a clear reason.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| OAuth / API connectors to ad platforms | Google OAuth approval takes months; Meta requires registered business entity; kills shipping velocity | CSV-first forever for v1; add OAuth only if users explicitly demand it post-revenue |
| Real-time monitoring / alerts | CSV is a point-in-time snapshot; real-time requires API + webhooks + polling infra | Make it clear in UX that audit is a snapshot; encourage monthly re-uploads |
| AI-generated ad copy suggestions | Scope creep — users came for audit, not copy; adds Claude cost per session | Stay in audit/diagnosis lane; link to copy tools (Jasper, etc.) in recommendations |
| Bid management / auto-optimization | Requires OAuth access to push changes; out of scope for read-only CSV tool | Recommend what to change; never execute changes |
| Competitor ad intelligence | Requires ad library scraping (legal grey area, high maintenance) | Defer to v2 or a separate product; don't block on this |
| Agency multi-client dashboard | Multi-tenancy per client seat adds auth complexity; not day-one need | $29 plan is per-account; agency tier is a future pricing tier |
| Mobile app | Web-first is sufficient; CSV upload is desktop behavior by nature | Responsive web is enough; no native app |
| Custom check builder / rule engine | Adalysis has this; it's complex and used only by power users | Ship 186 prebuilt checks first; custom checks are a pro-tier upsell |
| Slack / email alert integrations | Real-time alerts need API connection; not compatible with CSV model | Consider email digest of "audit results ready" as a v1 notification |
| Annual trend analysis / benchmarking | Requires 6-12 months of stored CSV uploads; data-intensive | Audit history (monthly) is enough; deep trend analysis is v2 |

---

## Check Coverage: What the Audit Engine Must Run

This is the core product — these are the specific check categories users expect from a credible audit tool. Grounded in the existing 186-check claude-ads reference library.

### Google Ads (74 checks across 7 categories)

| Category | Weight | Check Count | Key Checks |
|----------|--------|-------------|------------|
| Conversion Tracking | 25% | 11 | Enhanced conversions, server-side, Consent Mode v2, duplicate counting, GA4 link |
| Wasted Spend / Negatives | 20% | 8 | Search term recency, negative keyword lists, broad match + manual CPC, zero-conv keywords |
| Account Structure | 15% | 12 | Brand/non-brand separation, naming conventions, network settings, geo targeting |
| Keywords & Quality Score | 15% | 8 | Avg QS ≥7, critical QS ≤3 share, zero-impression keywords, keyword-to-ad relevance |
| Ads & Assets | 15% | 12 | RSA count/strength, PMax asset density, ad freshness, CTR vs benchmark |
| Settings & Targeting | 10% | 12 | Extensions (sitelinks, callouts, structured snippets), audiences, placement exclusions |
| Performance Max | (within Ads) | 5 | Audience signals, brand cannibalization, search themes, negatives |

### Meta Ads (weighted by Pixel 30%, Creative 30%, Structure 20%, Audience 20%)

| Category | Key Checks |
|----------|------------|
| Pixel / CAPI Health | Pixel firing, Events API, EMQ score, standard events configured |
| Creative Diversity & Fatigue | Creative count, frequency score, format variety (image/video/carousel), refresh recency |
| Account Structure | Learning phase status, CBO vs ABO appropriateness, campaign consolidation |
| Audience & Targeting | Audience overlap, exclusions, Advantage+ Placements testing, audience size sufficiency |

### LinkedIn Ads (Technical 25%, Audience 25%, Creative 20%, Lead Gen 15%, Bidding 15%)

| Category | Key Checks |
|----------|------------|
| Technical Setup | Insight Tag firing, CAPI configuration, CRM integration |
| Audience Quality | Targeting specificity, audience size (300K-1M sweet spot), exclusions |
| Creative & Formats | TLA (Text + Lead + Video mix), format diversity, ad freshness |
| Lead Gen Forms | CVR vs 13% benchmark, CRM sync, form field count |

### TikTok Ads (Creative 30%, Technical 25%, Bidding 20%, Structure 15%, Performance 10%)

| Category | Key Checks |
|----------|------------|
| Creative Quality | Native-feel content, hook rate (first 3s), completion rate, format variety |
| Technical Setup | Pixel + Events API + ttclid passback |
| Bidding & Learning | 50 conv/week threshold, budget sufficiency, Smart+ campaigns |
| Performance | CTR, CPA, VCR benchmarks |

### Microsoft Ads (Technical 25%, Syndication 20%, Structure 20%, Creative 20%, Performance 15%)

| Category | Key Checks |
|----------|------------|
| Technical Setup | UET tag, enhanced conversions, GA4 import validation |
| Syndication & Bidding | Partner network control, Copilot placement, LinkedIn targeting |
| Creative & Extensions | Multimedia Ads, Action Extensions, Filter Link Extensions |

---

## Feature Dependencies

```
Authentication → Audit History (must be logged in to store reports)
CSV Upload → Audit Engine → Health Score → Recommendations (linear pipeline)
Health Score + Check Results → PDF Export (PDF is a rendering of the same data)
Audit History → Before/After Comparison (need ≥2 stored audits)
Multi-platform Upload → Cross-Platform Aggregate Score (needs ≥2 platform results)
Spend Data in CSV → Revenue Impact Estimates (can't estimate without spend figures)
```

---

## MVP Recommendation

Prioritize (Phase 1 — ship in ≤6 weeks):

1. **CSV upload + parsing** — Google Ads export first (largest market, most checks defined)
2. **Audit engine** — 74 Google checks against parsed CSV data using Claude API
3. **Health score output** — 0-100 weighted score with grade (A-F)
4. **Severity-graded findings** — Critical/High/Medium/Low list
5. **Quick Wins section** — top 3-5 fast fixes surfaced prominently
6. **PDF export** — professional report, not just on-screen display
7. **Auth + subscription** — email/password + Razorpay $29/mo gate

Add in Phase 2:

- Meta Ads CSV support (second-largest platform, 4 categories)
- Audit history (stored reports per user)
- Share links for reports
- Platform benchmark context in findings
- LinkedIn, TikTok, Microsoft Ads CSV support

Defer to Phase 3+:

- Cross-platform aggregate score (needs multi-platform complete)
- Revenue impact estimates per finding
- Audit comparison / before-after view
- White-label PDF for agency tier

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Check categories | HIGH | Sourced directly from claude-ads 186-check reference library (google-audit.md, meta-audit.md, etc.) |
| Table stakes | HIGH | Confirmed by Opteo, Adalysis, PPC Rocket, Optmyzr feature pages and user reviews |
| Differentiators | MEDIUM | Multi-platform CSV gap confirmed by market research; revenue impact UX is inference from user psychology, not direct competitor data |
| Anti-features | HIGH | OAuth delay is documented (Google months-long backlog); real-time constraint is inherent to CSV model |
| Feature complexity estimates | MEDIUM | Solo dev estimates — actual implementation may surface edge cases in CSV schema parsing |

---

## Sources

- claude-ads reference library: `claude-ads/ads/references/` (google-audit.md, meta-audit.md, scoring-system.md, benchmarks.md) — HIGH confidence, proprietary research
- Adalysis audit features: https://adalysis.com/how-to-audit-a-google-ads-account-the-ultimate-ppc-audit-checklist-2021/
- Optmyzr PPC audit tool overview: https://www.optmyzr.com/blog/ppc-auditing-tools/
- Opteo features (improvements, alerts, reports): https://opteo.com/features
- PPC Rocket audit checks: https://www.ppcrocket.com/google-ads-audit-tool/
- PPC audit checklist categories: https://www.uforocks.com/blog/ppc-audit-checklist/
- Meta Ads audit framework: https://madgicx.com/blog/meta-ads-audit
- White-label PDF for agencies (Octoboard, Marketing Auditor): https://www.marketingauditor.com/google-ads-audit
- Agency reporting tools overview: https://www.swydo.com/blog/ppc-audit/
- PROJECT.md constraints and competitor table: `ad-audit-saas/.planning/PROJECT.md`
