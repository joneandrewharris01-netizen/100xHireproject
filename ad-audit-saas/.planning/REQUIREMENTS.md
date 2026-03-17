# Requirements: AdNerve

**Defined:** 2026-03-17
**Core Value:** Users can upload ad platform CSV exports and instantly receive a scored, actionable audit report that identifies wasted spend and prioritizes fixes by revenue impact.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Upload & Parsing

- [ ] **UPLD-01**: User can upload a Google Ads CSV export and have it parsed correctly
- [ ] **UPLD-02**: User can upload a Meta Ads CSV export and have it parsed correctly
- [ ] **UPLD-03**: User can upload a LinkedIn Ads CSV export and have it parsed correctly
- [ ] **UPLD-04**: User can upload a TikTok Ads CSV export and have it parsed correctly
- [ ] **UPLD-05**: User can upload a Microsoft Ads CSV export and have it parsed correctly
- [ ] **UPLD-06**: User sees clear "how to export" guides with screenshots for each platform
- [ ] **UPLD-07**: System handles CSV column name variance across locales and export types via fuzzy matching
- [ ] **UPLD-08**: System rejects invalid/corrupt files with helpful error messages

### Audit Engine

- [ ] **AUDT-01**: System runs 74 automated checks on Google Ads data
- [ ] **AUDT-02**: System runs 46 automated checks on Meta Ads data
- [ ] **AUDT-03**: System runs 25 automated checks on LinkedIn Ads data
- [ ] **AUDT-04**: System runs 25 automated checks on TikTok Ads data
- [ ] **AUDT-05**: System runs 20 automated checks on Microsoft Ads data
- [ ] **AUDT-06**: System calculates a weighted 0-100 health score across all uploaded platforms
- [ ] **AUDT-07**: Each check is graded by severity (critical/high/medium/low)
- [ ] **AUDT-08**: System generates a "Quick Wins" section — top 5-6 fixes under 15 min with estimated impact
- [ ] **AUDT-09**: Claude API generates a 2-3 paragraph AI narrative summary of findings
- [ ] **AUDT-10**: Checks run deterministically in TypeScript first, then Claude analyzes aggregated results (not raw CSV)

### Dashboard & Output

- [ ] **DASH-01**: User sees an interactive web dashboard with health score, check results, and recommendations
- [ ] **DASH-02**: Dashboard shows results grouped by category (conversion tracking, budget, targeting, creative, etc.)
- [ ] **DASH-03**: User can download a PDF report of audit results for sharing with clients/stakeholders
- [ ] **DASH-04**: User can view audit history and see score changes over time
- [ ] **DASH-05**: Dashboard design matches the existing landing page aesthetic (dark theme, GSAP animations)

### Authentication

- [ ] **AUTH-01**: User can create an account with email and password
- [ ] **AUTH-02**: User session persists across browser refresh
- [ ] **AUTH-03**: User can log out from any page
- [ ] **AUTH-04**: Every API route independently verifies session (not just middleware)

### Payments

- [ ] **PAY-01**: User can subscribe at $29/mo via Razorpay
- [ ] **PAY-02**: User gets one free audit without payment (conversion hook)
- [ ] **PAY-03**: After free audit, user must subscribe to run additional audits
- [ ] **PAY-04**: User can cancel subscription from dashboard
- [ ] **PAY-05**: Razorpay webhooks handled idempotently with retry support

### Notifications

- [ ] **NOTF-01**: User receives audit results via email after completion

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### OAuth API Connectors

- **OAUT-01**: User can connect Google Ads account via OAuth for automated audits
- **OAUT-02**: User can connect Meta Ads account via OAuth
- **OAUT-03**: Real-time budget monitoring and spend alerts

### Advanced Features

- **ADVN-01**: AI competitor intelligence using Meta Ad Library / Google Transparency
- **ADVN-02**: Share link for public audit reports (no login required)
- **ADVN-03**: Agency multi-account management
- **ADVN-04**: Weekly automated re-audit with score delta notifications
- **ADVN-05**: Landing page audit paired with ad audit

## Out of Scope

| Feature | Reason |
|---------|--------|
| OAuth/API connectors | Phase 0 is CSV-only; OAuth requires weeks of API approvals |
| Real-time monitoring | CSV is point-in-time audit, not live monitoring |
| Bid management / campaign changes | Read-only tool, never modifies campaigns |
| Custom rule builder | Over-engineering for v1; 190+ checks are sufficient |
| Mobile app | Web responsive is sufficient |
| Multi-language support | English-first, localize later |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| UPLD-01 | Phase 2 | Pending |
| UPLD-02 | Phase 2 | Pending |
| UPLD-03 | Phase 2 | Pending |
| UPLD-04 | Phase 2 | Pending |
| UPLD-05 | Phase 2 | Pending |
| UPLD-06 | Phase 2 | Pending |
| UPLD-07 | Phase 2 | Pending |
| UPLD-08 | Phase 2 | Pending |
| AUDT-01 | Phase 2 | Pending |
| AUDT-02 | Phase 2 | Pending |
| AUDT-03 | Phase 2 | Pending |
| AUDT-04 | Phase 2 | Pending |
| AUDT-05 | Phase 2 | Pending |
| AUDT-06 | Phase 2 | Pending |
| AUDT-07 | Phase 2 | Pending |
| AUDT-08 | Phase 2 | Pending |
| AUDT-09 | Phase 2 | Pending |
| AUDT-10 | Phase 2 | Pending |
| DASH-01 | Phase 3 | Pending |
| DASH-02 | Phase 3 | Pending |
| DASH-03 | Phase 3 | Pending |
| DASH-04 | Phase 3 | Pending |
| DASH-05 | Phase 3 | Pending |
| PAY-01 | Phase 4 | Pending |
| PAY-02 | Phase 4 | Pending |
| PAY-03 | Phase 4 | Pending |
| PAY-04 | Phase 4 | Pending |
| PAY-05 | Phase 4 | Pending |
| NOTF-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 33 total
- Mapped to phases: 33
- Unmapped: 0

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-17 — traceability mapped after roadmap creation*
