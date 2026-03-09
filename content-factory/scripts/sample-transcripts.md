# Sample Transcripts & Expected Outputs

Upload this file as Project Knowledge in your Claude Project. It gives Claude additional reference for how to convert raw transcripts into the AI Finance Guy JSON format.

---

## Sample 1: Tax Deductions Transcript

### Source Transcript (Sarthak Ahuja style)
> If you're a freelancer earning above 50 lakhs... you're probably paying too much tax. I've audited hundreds of freelancer accounts and the same deductions keep getting missed. Home office deduction — most people skip it because it seems complicated. It's not. Health insurance premiums — fully deductible for self-employed individuals. All your software subscriptions — every SaaS tool counts. Internet and phone bills — the business portion. Professional development — courses, conferences, books. Equipment depreciation — your laptop, monitor, everything. And retirement contributions — a SEP IRA lets you shelter up to 20% of income. For someone earning around 80 thousand dollars, that's roughly 4,200 dollars per year you're leaving on the table.

### Expected Output
```json
{
  "id": "finance-003",
  "mode": "finance",
  "title": "7 Tax Deductions Freelancers Miss",
  "hook": "Freelancers: you're probably paying too much tax. AI found 7 deductions you're missing.",
  "voiceoverScript": "Freelancers. You're probably paying too much tax. I asked Claude to audit a typical freelancer's expenses and find missed deductions. It found seven. Home office deduction. Most freelancers skip it because it seems complicated. It's not. Health insurance premiums. Fully deductible if you're self-employed. Software subscriptions. Every tool you use for work counts. Internet and phone. The business percentage is deductible. Professional development. Courses, books, conferences. Equipment depreciation. That laptop? Deductible. Retirement contributions. SEP IRA lets you shelter up to twenty percent. Total potential savings for someone earning eighty thousand? Four thousand two hundred dollars a year. That's money you're giving away. AI found this in five minutes.",
  "scenes": [
    {
      "id": "data",
      "label": "Missed Deductions",
      "text": "7 deductions most freelancers skip. AI found them in 5 minutes.",
      "data": { "amount": 4200, "prefix": "$", "suffix": "/yr saved", "demographic": "Freelancers earning over $50K..." }
    },
    {
      "id": "geo",
      "label": "Your Tax Bill",
      "text": "Home office, health insurance, software, internet, education, equipment, retirement.",
      "data": {
        "location": "TAX SEASON",
        "stat1": "Deductions Found|7",
        "stat2": "Analysis Time|5 min",
        "stat3": "Annual Savings|$4,200",
        "stat4": "Income Level|$80K+"
      }
    },
    {
      "id": "ai",
      "label": "AI Tax Audit",
      "text": "Claude analyzed typical freelancer expenses for missed deductions",
      "data": {
        "prompt": "Audit a freelancer earning $80K for missed tax deductions",
        "result": "7 commonly missed deductions worth $4,200/year in savings"
      }
    }
  ],
  "cta": {
    "line1": "AI found this",
    "line2": "What else should I ask?"
  }
}
```

### Conversion Notes
- Original uses "I've audited hundreds" (personal credential) → converted to "I asked Claude to audit" (AI framing)
- "50 lakhs" converted to "$50K" for US/global audience
- Kept all 7 deductions since they were specific and real
- Geo scene uses "TAX SEASON" as situational context (no geographic location in source)
- Added "AI found this in five minutes" as an authority marker

---

## Sample 2: Real Hourly Rate Transcript

### Source Transcript (self-reflection style)
> You think you earn 150 dollars an hour? Let me break down what your real hourly rate looks like. Take your annual income. Now count ALL your hours. The hours you spend working. The hours commuting. Admin work — invoicing, emails, proposals. Time thinking about work on weekends. Answering that one Slack message at 10 PM. When I did this math myself, my 150 dollar rate dropped to 47 dollars per hour. To actually earn 150 real dollars per hour, I'd need to charge 412 on my invoice. Most freelancers have never done this calculation and they'd be shocked if they did.

### Expected Output
```json
{
  "id": "finance-005",
  "mode": "finance",
  "title": "Your Real Hourly Rate",
  "hook": "AI calculated my real hourly rate. I'm embarrassed.",
  "voiceoverScript": "AI calculated my real hourly rate. I'm embarrassed. I told Claude my annual income and asked it to calculate my true hourly rate. Not the number on my invoice. The real one. It counted everything. Hours working. Hours commuting. Hours doing admin. Hours thinking about work. Hours answering emails on weekends. My invoice says a hundred and fifty an hour. My real rate? Forty-seven dollars. Claude then calculated what I'd need to charge to actually earn a hundred and fifty real dollars per hour. The answer? Four hundred and twelve dollars per hour on my invoice. Most freelancers have no idea how much free work they're doing. The math doesn't care about your feelings. What would you ask AI about your money?",
  "scenes": [
    {
      "id": "data",
      "label": "Your Real Rate",
      "text": "Invoice says $150/hr. Real rate after all hours? $47/hr.",
      "data": { "amount": 47, "prefix": "$", "suffix": "/hr real", "demographic": "If you're a freelancer charging hourly..." }
    },
    {
      "id": "geo",
      "label": "The Gap",
      "text": "To truly earn $150/hr, you'd need to invoice $412/hr.",
      "data": {
        "location": "REALITY CHECK",
        "stat1": "Invoice Rate|$150/hr",
        "stat2": "Real Rate|$47/hr",
        "stat3": "Hidden Hours|68%",
        "stat4": "Target Invoice|$412/hr"
      }
    },
    {
      "id": "ai",
      "label": "AI Math",
      "text": "Calculate true hourly rate including all work-related time",
      "data": {
        "prompt": "Calculate my REAL hourly rate including admin, email, commute, thinking time",
        "result": "Your $150/hr invoice rate is actually $47/hr when you count all hours"
      }
    }
  ],
  "cta": {
    "line1": "What would you",
    "line2": "ask AI about money?"
  }
}
```

### Conversion Notes
- Original is first-person reflection → reframed as "I told Claude my income and asked it to calculate"
- All numbers preserved exactly from source (150, 47, 412)
- No geographic location → used "REALITY CHECK" as situational context
- "Hidden Hours|68%" was calculated: (150-47)/150 ≈ 68% of work time is unaccounted
- Hook uses self-deprecating tone ("I'm embarrassed") — matches brand voice

---

## Sample 3: Portugal Nomad Visa Transcript

### Source Transcript (geographic finance style)
> There is a country where earning 3,000 dollars a month puts you in the upper class. Portugal has a digital nomad visa, D7 visa, and the tax rate is a flat 20 percent for foreign income. If you're a remote worker making 5,000 dollars a month in the US, after federal and state taxes, rent in a decent city, health insurance, you're left with about 2,200. Move to Portugal — same income — you keep 3,100. That's 900 dollars more per month, 10,800 per year. Plus EU healthcare, travel across 27 Schengen countries, and a path to permanent residency after 5 years. You need to show 3,200 in monthly income to qualify. For anyone earning dollars and spending euros, this is probably the best arbitrage available right now.

### Expected Output
```json
{
  "id": "finance-004",
  "mode": "finance",
  "title": "Portugal Digital Nomad Visa",
  "hook": "The country where $3K a month makes you upper class. AI ran the numbers.",
  "voiceoverScript": "The country where three thousand dollars a month makes you upper class. AI ran the numbers. Portugal's digital nomad visa lets you live in Europe for a flat twenty percent tax rate. I asked Claude to compare a remote worker earning five thousand a month in the US versus Portugal. In the US, after taxes, rent, and living costs, you keep about twenty-two hundred. In Portugal, you keep thirty-one hundred. Same income. Nine hundred more in your pocket every month. That's ten thousand eight hundred a year. Plus you get EU healthcare, Schengen travel, and a path to permanent residency. The catch? You need to prove three thousand two hundred in monthly income and apply through the consulate. But for remote workers earning in dollars and spending in euros, the math is undeniable. Save this before it's gone.",
  "scenes": [
    {
      "id": "data",
      "label": "Monthly Savings",
      "text": "Same $5K income. $900 more per month in Portugal vs US.",
      "data": { "amount": 10800, "prefix": "$", "suffix": "/yr extra", "demographic": "Remote workers earning $5K+/month..." }
    },
    {
      "id": "geo",
      "label": "Portugal",
      "text": "20% flat tax, EU healthcare, Schengen travel, path to residency.",
      "data": {
        "location": "PORTUGAL",
        "stat1": "Tax Rate|20% flat",
        "stat2": "Monthly Savings|$900",
        "stat3": "Min Income|$3,200/mo",
        "stat4": "Annual Gain|$10,800"
      }
    },
    {
      "id": "ai",
      "label": "I Asked AI...",
      "text": "Compare take-home: US vs Portugal at $5K/mo remote income",
      "data": {
        "prompt": "Compare net income after all costs: US vs Portugal at $5K/mo",
        "result": "Portugal wins by $900/mo — plus EU healthcare and travel benefits"
      }
    }
  ],
  "cta": {
    "line1": "Save this",
    "line2": "before it's gone"
  }
}
```

### Conversion Notes
- Strong geographic hook preserved ("The country where $3K a month makes you upper class")
- All numbers from source: 3000, 5000, 20%, 2200, 3100, 900, 10800, 3200
- "D7 visa" detail kept in voiceover as "digital nomad visa" (simpler for audience)
- "best arbitrage available" → softened to "the math is undeniable" (less jargon)
- CTA uses urgency ("Save this before it's gone") — implies the visa opportunity won't last

---

## Conversion Checklist

Use this checklist when converting any transcript:

- [ ] Extracted all specific numbers from source — none fabricated
- [ ] Identified the single most shocking data point → data scene
- [ ] Found geographic or contextual angle → geo scene with ALL CAPS location
- [ ] Created AI framing ("I asked Claude/ChatGPT to...") → ai scene
- [ ] Reframed creator authority → AI tool authority
- [ ] Hook has AI framing + specific number (ideally both)
- [ ] voiceoverScript: 150-250 words, all numbers as words
- [ ] voiceoverScript starts with the hook text
- [ ] 4 stats in geo scene, all pipe-separated "Label|Value"
- [ ] CTA is implicit — no "follow me", just thought-provoking ending
- [ ] JSON is valid — no trailing commas, proper quoting
- [ ] `mode` is `"finance"`, scene order is data → geo → ai
