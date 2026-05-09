# PE Outreach Playbook

(Empty — Claude appends learnings via `/pe-process` runs.)

---

## 2026-04-28 — first run

**3 hot leads surfaced from r/private_equity (the only sub that scraped before rate-limit).**

What worked:
- The 100/100 lead (Strong-Buy-6466) is a textbook buyer signal: "tasked with building" + Claude Team plan already + asking for dos/don'ts. Comment opens with credibility ("built this exact stack twice"), ends with a contrarian list (what to skip). DM keeps it short, free audit, no pitch deck.
- The 75/100 lead (Away-Lengthiness-831) is the strongest *quality* lead despite lower score. The post itself reads like a sales discovery call — they identified the chat-vs-API trap, named Preqin/Bloomberg as inadequate, admitted they're stuck. Comment leverages u/NecessaryPapaya51's deep reply (already validates the diagnosis) and adds the "workflow person not infrastructure" angle. DM offers $497 fixed MVP — a price anchor that makes the free audit feel reasonable.

What surfaced as false positive:
- atog2's VP Ops comp question scored 75 (active_build + vendor_evaluation + automation_relevant) because the role description mentions "implementing AI". This is the most common false-positive pattern: someone describing a job that touches automation, not someone buying automation. **Tune for v1.1**: if title contains "comp", "advice", "role", "offer", apply -20 penalty.

DM angle to try next run:
- Lead with a price anchor ($497 fixed) rather than just "free audit". Makes the free option feel like a no-brainer.
- For research analysts (lower buying authority), frame: "blueprint you can take to management" — gives them ammo internally.

Tools added this run: Claude Team, ChatGPT (chat vs API), Docling, Unstructured.io, AWS Textract, Preqin, Bloomberg, Perplexity (8 tools total — KB went from empty to viable foundation in one run).

Pains catalogued: ai_infrastructure_setup_no_playbook, manual_lp_doc_extraction, gpt_chat_vs_api_gap, in_house_data_pipeline_drift.

Personas: ai_lead_at_small_pe (high authority), research_analyst_at_small_pe (medium authority, high pain).

Scrape note: Reddit rate-limited after the first sub (~100 posts). Need to wire up PrawFetcher or add backoff before the next daily run, otherwise we're getting one sub of data per day.
