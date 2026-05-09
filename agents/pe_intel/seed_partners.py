"""Seed the partners table from the 2026-04-28 research shortlist.

Run once after schema migration. Idempotent (uses upsert).
Application status defaults to 'not_applied'; mark approved as Jone gets in.
"""
from . import db


PARTNERS = [
    # ============================================================
    # TIER 3 — Formal affiliate / referral programs (apply, get cookie)
    # ============================================================
    # name, category, tier, payout_model, payout_min, payout_max, apply_url, notes
    ("Deel", "hiring", "T3", "per_meeting+per_close", 500, 1500,
     "https://deel.com/partner-program/",
     "$500/SQL + $1,000/close. 90-day cookie. Open to solos."),
    ("HighLevel", "crm", "T3", "per_close_recurring", 38, 198,
     "https://affiliates.gohighlevel.com",
     "40% MRR for life. Jone already uses GHL."),
    ("HubSpot Solutions Partner", "crm", "T3", "per_close_recurring", 100, 500,
     "https://hubspot.com/partners/solutions",
     "20% MRR 12 mo (Provider tier). APPLY BEFORE 2026-07-15."),
    ("Make.com", "automation", "T3", "per_close_recurring", 30, 200,
     "https://make.com/en/affiliate", "35% MRR for 12 months."),
    ("n8n Affiliate", "automation", "T3", "per_close_recurring", 20, 150,
     "https://n8n.io/affiliates/", "30% for 12 months."),
    ("Pipedrive", "crm", "T3", "per_close_recurring", 30, 150,
     "https://pipedrive.com/en/affiliate-partnership", "20% MRR 12 mo (Tier 3)."),
    ("Close CRM", "crm", "T3", "per_close_recurring", 30, 200,
     "https://close.com/partners", "30% MRR for 12 months."),
    ("Notion", "automation", "T3", "per_close_recurring", 50, 300,
     "https://notion.so (via PartnerStack)", "50% for 12 months. 180-day cookie."),
    ("ClickUp", "automation", "T3", "per_close", 20, 100,
     "https://clickup.com/partners/affiliates", "Per-signup commission."),
    ("Oyster HR", "hiring", "T3", "per_close_bonus", 250, 1000,
     "https://oysterhr.com/affiliates", "~10% first-year + $250 bonus."),
    ("Anthropic Claude Enterprise Referral", "ai_infra", "T3", "per_close_one_time", 500, 5000,
     "https://anthropic.com/referral", "Lower bar than Partner Network."),
    ("PartnerStack Marketplace", "automation", "T3", "varies", 50, 1000,
     "https://partnerstack.com", "Aggregator: 250+ programs."),
    ("Reditus", "automation", "T3", "varies", 50, 800,
     "https://getreditus.com", "PartnerStack alternative."),
    ("Zapier Solution Partner", "automation", "T3", "per_close", 50, 500,
     "https://zapier.com/l/solution-partner", "Apply for SOLUTION tier."),
    ("CommissionCrowd", "gtm", "T3", "per_close", 200, 2000,
     "https://commissioncrowd.com",
     "Marketplace of cos seeking commission sellers (T3 not T2 — formal)."),
    ("Synthflow", "ai_infra", "T3", "reseller_margin", 100, 500,
     "https://docs.synthflow.ai/synthflow-ai-agency-partner-program",
     "Voice AI agency partner."),

    # ============================================================
    # TIER 2 — Big B2B competitor firms (cold-DM, informal SDR brokerage)
    # Pay-per-qualified-meeting. NO public partner program. DM the BD/founder.
    # ============================================================

    # automation
    ("Bitovi", "automation", "T2", "per_meeting", 500, 1000,
     "https://linkedin.com/company/bitovi",
     "DM Justin Meyer. n8n service partner, 80 employees, founded 2010."),
    ("TrueHorizon AI", "automation", "T2", "per_meeting", 500, 1500,
     "https://linkedin.com/in/nateherkelman",
     "Nate Herkelman. Public n8n personality. $500K+ ARR cos with AI agents."),
    ("Spector", "automation", "T2", "per_meeting", 1000, 2000,
     "https://workato.com/partners",
     "Workato Gold partner. Enterprise iPaaS, $200K+ deals."),
    ("Codimite", "automation", "T2", "per_meeting", 400, 800,
     "https://codimite.ai/n8n",
     "Enterprise self-hosted n8n. ~100 employees."),
    ("Virtuoso Partners", "automation", "T2", "per_meeting", 1000, 2000,
     "https://linkedin.com/company/virtuosopartners",
     "Workato Partner of Year 2025. UK + global mid-market."),
    ("AOE", "automation", "T2", "per_meeting", 500, 1500,
     "https://aoe.com",
     "Germany. Mid-market+ digital transformation w/ n8n. Edge size."),
    ("NextAutomation", "automation", "T2", "per_meeting", 300, 600,
     "https://linkedin.com/company/nextautomation",
     "Real estate + AI ops backbone."),
    ("2V Automation", "automation", "T2", "per_meeting", 400, 800,
     "https://2vautomation.com",
     "US-based, $3M+ revenue overhauls."),
    ("Mpire Solutions", "automation", "T2", "per_meeting", 300, 500,
     "https://linkedin.com/company/mpire-solutions",
     "Mid-sized businesses, rapid n8n implementation."),
    ("Flowmondo", "automation", "T2", "per_meeting", 300, 600,
     "https://flowmondo.com", "UK. UK/EU clients with deep n8n need."),

    # gtm
    ("LevelUp Leads", "gtm", "T2", "per_meeting", 300, 500,
     "https://linkedin.com/in/johnkarsant",
     "John Karsant. SMB-mid B2B, $4-8K/mo retainers. STRONG FIT."),
    ("SalesBread", "gtm", "T2", "per_meeting", 200, 400,
     "https://linkedin.com/in/jackreamer",
     "Jack Reamer. Founder-led, LinkedIn personality. STRONG FIT."),
    ("Belkins", "gtm", "T2", "per_meeting", 300, 500,
     "https://linkedin.com/in/vladgoloshchuk",
     "Vlad Goloshchuk. ~400 employees, founded 2017. Edge size."),
    ("Martal Group", "gtm", "T2", "per_meeting", 300, 500,
     "https://linkedin.com/in/vito-vishnepolsky",
     "Vito Vishnepolsky. ~150-200 employees, founded 2009."),
    ("EBQ", "gtm", "T2", "per_meeting", 400, 700,
     "https://linkedin.com/company/ebq",
     "Austin TX. Mid-market + enterprise B2B."),
    ("SalesRoads", "gtm", "T2", "per_meeting", 300, 500,
     "https://linkedin.com/in/davidkreiger",
     "David Kreiger. Coral Springs FL. US B2B mid-market."),
    ("Cleverly", "gtm", "T2", "per_meeting", 250, 450,
     "https://linkedin.com/company/cleverlyco",
     "B2B SaaS, founder-led companies, LinkedIn outreach."),
    ("Pearl Lemon Leads", "gtm", "T2", "per_meeting", 200, 400,
     "https://linkedin.com/in/deepakshukla",
     "Deepak Shukla, very public. London. UK-EU SMB."),
    ("SalesHive", "gtm", "T2", "per_meeting", 250, 400,
     "https://saleshive.com",
     "200-400 SDRs. B2B SaaS needing SDR teams."),

    # ai_infra
    ("Tribe AI", "ai_infra", "T2", "per_meeting", 1000, 2000,
     "https://linkedin.com/in/jaclynricenelson",
     "Jaclyn Rice Nelson. F1000, PE, $50M+ ARR. Anthropic Partner. TOP PICK."),
    ("Forgd", "ai_infra", "T2", "per_meeting", 1000, 2000,
     "https://linkedin.com/company/forgd",
     "Claude Code specialist. Anthropic Partner. Small team, founder reachable."),
    ("AE Studio", "ai_infra", "T2", "per_meeting", 1000, 1500,
     "https://linkedin.com/company/ae-studio",
     "150-250 employees. Enterprise ML + custom AI products."),
    ("AI Squared", "ai_infra", "T2", "per_meeting", 800, 1500,
     "https://linkedin.com/company/aisquared",
     "Dr. Benjamin Harvey. Financial services + enterprise."),
    ("Lumetric", "ai_infra", "T2", "per_meeting", 1000, 2000,
     "https://lumetric.ai", "IB / PE / CRE / consulting AI coworkers."),
    ("T3 Consultants", "ai_infra", "T2", "per_meeting", 800, 1500,
     "https://t3-consultants.com",
     "Mid-market Claude enterprise implementation."),
    ("Pareto Technologies", "ai_infra", "T2", "per_meeting", 1000, 2000,
     "https://paretotechnologies.com",
     "Enterprise AI strategy + implementation."),
    ("DataNorth.ai", "ai_infra", "T2", "per_meeting", 500, 1000,
     "https://datanorth.ai", "NL-based. EU mid-market Claude."),

    # crm
    ("Aptitude 8", "crm", "T2", "per_meeting", 500, 1500,
     "https://linkedin.com/in/connor-jeffers",
     "Connor Jeffers. HubSpot Elite. LinkedIn-active. TOP PICK."),
    ("Bluleadz", "crm", "T2", "per_meeting", 500, 1000,
     "https://linkedin.com/in/ericbaumbz",
     "Eric Baum. HubSpot Elite. Stage 2 Capital LP — knows the model."),
    ("Carabiner Group", "crm", "T2", "per_meeting", 500, 1000,
     "https://linkedin.com/company/the-carabiner-group-consultants",
     "RevOps-as-a-service across 150+ tools. Part of SBI Growth."),
    ("New Breed", "crm", "T2", "per_meeting", 500, 1000,
     "https://linkedin.com/company/new-breed-marketing-llc",
     "Burlington VT. Mid-market HubSpot RevOps."),
    ("Six & Flow", "crm", "T2", "per_meeting", 400, 800,
     "https://linkedin.com/in/richwoodtech",
     "Rich Wood. Manchester UK. UK/EU mid-market HubSpot Elite."),
    ("BabelQuest", "crm", "T2", "per_meeting", 400, 800,
     "https://linkedin.com/in/gemrugggunn-hubspot",
     "Gem Rugg-Gunn. Oxford UK. HubSpot Elite."),
    ("Plative", "crm", "T2", "per_meeting", 700, 1500,
     "https://linkedin.com/company/plative",
     "Mid-market RevOps + Salesforce."),
    ("CloudMasonry", "crm", "T2", "per_meeting", 700, 1500,
     "https://linkedin.com/company/cloudmasonry",
     "Mid-market Salesforce CPQ in financial/media/energy."),
    ("Impulse Creative", "crm", "T2", "per_meeting", 400, 800,
     "https://linkedin.com/company/impulse-creative",
     "FL. SMB-mid HubSpot Diamond AI marketing."),
    ("Extendly", "crm", "T2", "per_meeting", 200, 400,
     "https://linkedin.com/company/extendly",
     "Beant Singh + Robb Bailey. GHL agency white-label."),

    # portfolio_reporting
    ("Alpha Alternatives", "portfolio_reporting", "T2", "per_meeting", 1500, 3000,
     "https://linkedin.com/in/jonathanbalkin",
     "Jonathan Balkin. PE/VC GPs. Carta+Allvue+Chronograph integration. HIGHEST PAYOUT."),
    ("SteelBridge Consulting", "portfolio_reporting", "T2", "per_meeting", 1000, 2500,
     "https://linkedin.com/in/jameshaluszczak",
     "James Haluszczak. PE/VC fund admin + tech. Founded 2008."),
    ("Drawbridge", "portfolio_reporting", "T2", "per_meeting", 800, 1500,
     "https://linkedin.com/in/jasonelmer",
     "Jason Elmer. Hedge fund + PE managers. Cybersec angle."),
    ("Mirador (iCapital)", "portfolio_reporting", "T2", "per_meeting", 1000, 2000,
     "https://linkedin.com/company/icapital",
     "Family offices, wealth managers, PE."),
]


def seed(conn):
    for (name, category, tier, model, pmin, pmax, url, notes) in PARTNERS:
        db.upsert_partner(
            conn, name=name, category=category, tier=tier,
            payout_model=model, payout_min_usd=pmin, payout_max_usd=pmax,
            apply_url=url, notes=notes,
        )
    return len(PARTNERS)


def main():
    conn = db.connect()
    db.init_schema(conn)
    n = seed(conn)
    print(f"Seeded {n} partners.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
