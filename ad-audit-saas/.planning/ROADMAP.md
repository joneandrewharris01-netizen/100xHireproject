# Roadmap: AdNerve

## Overview

AdNerve ships in four phases. Phase 1 establishes the user identity and secure file upload infrastructure that everything depends on. Phase 2 builds the full audit pipeline — all five platform parsers, 190 deterministic checks, and the Claude AI narrative layer — starting with Google Ads and expanding outward. Phase 3 delivers the interactive dashboard and PDF report that turn audit data into a product users can see and share. Phase 4 closes the loop with Razorpay subscription billing and email delivery, making AdNerve a live commercial product.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Auth, database schema, and presigned CSV upload infrastructure
- [ ] **Phase 2: Audit Engine** - All five platform parsers, 190 deterministic checks, and AI narrative layer
- [ ] **Phase 3: Dashboard and PDF** - Interactive results UI, audit history, and downloadable PDF report
- [ ] **Phase 4: Payments and Launch** - Razorpay subscription billing, free trial gate, and audit email delivery

## Phase Details

### Phase 1: Foundation
**Goal**: Users can create accounts and securely upload ad CSV files to storage, with auth guarding every API route
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04
**Success Criteria** (what must be TRUE):
  1. User can create an account with email and password and log in immediately
  2. User session persists across browser refresh without re-authentication
  3. User can log out from any page and is fully unauthenticated afterward
  4. Any API route called without a valid session returns 401 (middleware bypass not possible)
  5. A CSV file uploaded by the user lands in Vercel Blob storage without passing through the serverless function body (presigned URL pattern)
**Plans**: TBD

Plans:
- [ ] 01-01: Better Auth setup — email/password, Drizzle adapter, session verification helper used by all routes
- [ ] 01-02: Database schema — audits, audit_checks, audit_insights tables with UUID IDs, Neon Postgres + Drizzle migrations
- [ ] 01-03: Presigned upload — Vercel Blob presigned URL endpoint, client-side upload widget, CSV stored to Blob and URL returned

### Phase 2: Audit Engine
**Goal**: Users can upload a CSV from any supported ad platform and receive a fully scored audit with deterministic check results and an AI narrative summary
**Depends on**: Phase 1
**Requirements**: UPLD-01, UPLD-02, UPLD-03, UPLD-04, UPLD-05, UPLD-06, UPLD-07, UPLD-08, AUDT-01, AUDT-02, AUDT-03, AUDT-04, AUDT-05, AUDT-06, AUDT-07, AUDT-08, AUDT-09, AUDT-10
**Success Criteria** (what must be TRUE):
  1. Uploading a Google Ads CSV produces a scored audit with all 74 checks evaluated and severity-graded
  2. Uploading a Meta, LinkedIn, TikTok, or Microsoft Ads CSV is detected by column signature and audited with the correct platform check set
  3. An invalid or corrupt file upload returns a clear error message explaining what went wrong
  4. The health score (0-100) and a 2-3 paragraph AI narrative summary are present in the completed audit record
  5. "How to export" guides are accessible from the upload screen for each of the five platforms
  6. Claude API receives only aggregated check results (never raw CSV rows) — confirmed by per-audit token log
**Plans**: TBD

Plans:
- [ ] 02-01: Platform parsers — Google Ads parser + normalizer with fuzzy column matching; establish NormalizedAdData schema; detection by column signature
- [ ] 02-02: Google Ads check runner — all 74 checks as pure TypeScript functions, weighted score computation, severity grading, Quick Wins flagging
- [ ] 02-03: Multi-platform parsers — Meta (46 checks), LinkedIn (25), TikTok (25), Microsoft (20) parsers and check runners following the Google pattern
- [ ] 02-04: AI narrative layer — Claude Haiku/Sonnet integration, prompt builder (check results only), response parser, system prompt caching, per-audit token logging
- [ ] 02-05: Audit API route — /api/audit/upload wires parser + engine + AI + DB insert; /api/audit/[id] fetches results; ownership verified; "how to export" guide content
- [ ] 02-06: Export guides — per-platform screenshot-illustrated "how to download your CSV" content, surfaced from upload UI

### Phase 3: Dashboard and PDF
**Goal**: Users can view their full audit results in an interactive dashboard and download a professional PDF report to share with clients
**Depends on**: Phase 2
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05
**Success Criteria** (what must be TRUE):
  1. After an audit completes, user sees a dashboard with health score, severity-graded check list, and prioritized recommendations
  2. Dashboard groups check results by category (conversion tracking, budget, targeting, creative) and matches the dark-theme aesthetic of the landing page
  3. User can download a PDF of the audit results that is formatted for sharing with a client or stakeholder
  4. User can view a list of past audits and see the health score for each
**Plans**: TBD

Plans:
- [ ] 03-01: Dashboard UI — score ring, check results table (sortable/filterable by severity and category), recommendations panel, Quick Wins section; GSAP/dark-theme aesthetic
- [ ] 03-02: PDF report — @react-pdf/renderer document served from /api/audit/[id]/pdf, professional layout matching dashboard content
- [ ] 03-03: Audit history — list view of past audits per user with health score, platform, and date; score delta display when 2+ audits exist

### Phase 4: Payments and Launch
**Goal**: Users must subscribe at $29/mo to run audits beyond the free trial, payments are handled reliably, and audit completion triggers an email notification
**Depends on**: Phase 3
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, PAY-05, NOTF-01
**Success Criteria** (what must be TRUE):
  1. A new user can complete one free audit without a payment method
  2. After the free audit, user is prompted to subscribe and can complete Razorpay checkout at $29/mo
  3. A subscribed user can cancel from the dashboard and loses audit access at the end of the billing period
  4. Razorpay webhook events (activated, charged, halted, cancelled) update subscription status correctly with no duplicate processing
  5. User receives an email when their audit is ready, with a link to the dashboard results
**Plans**: TBD

Plans:
- [ ] 04-01: Razorpay integration — Plans + Subscriptions API, checkout flow, subscription status in DB, paywall on audit creation
- [ ] 04-02: Webhook handler — raw body parsing, signature verification, idempotency check, full lifecycle handling (activated/charged/halted/cancelled/completed)
- [ ] 04-03: Email delivery — Resend integration, audit-ready email with result link, subscription event emails (confirmation, cancellation)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/3 | Not started | - |
| 2. Audit Engine | 0/6 | Not started | - |
| 3. Dashboard and PDF | 0/3 | Not started | - |
| 4. Payments and Launch | 0/3 | Not started | - |
