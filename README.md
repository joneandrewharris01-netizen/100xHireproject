# 100x Hire Project

This repository is part of my assignment for 100x, a step toward getting hired as a junior marketing specialist.

## Setup Notes

What I did:
- Installed Cursor as the development environment.
- Added Codex and Claude Code extensions, then connected both extensions to Cursor.
- Connected GitHub so this repository can be updated directly.
- Created and maintained this README as the project evolves.

Challenge faced:
- Cursor's interface had changed since the last time I used it, especially around opening and installing extensions. I solved it by watching an updated tutorial for the current Cursor UI.

## AI-Powered SEO Content Production Research Project

This repository now contains a source-backed research project for building a future AI-powered SEO content production playbook for B2B SaaS.

Topic: AI-powered SEO content production for B2B SaaS, including AI search visibility, AEO/GEO, programmatic SEO, AI-assisted content workflows, free-tools SEO, and content distribution for Google and AI answer engines.

What was collected:
- 10 practitioner-experts ranked from strong to weak fit.
- Verification CSV with proof strength and source URLs.
- Recent YouTube video inventory for AI SEO/GEO/content operators.
- 13 YouTube transcript files where captions or local Starter Story transcripts were available.
- Recent YouTube URLs for additional strong operators where free transcript extraction found no English captions.
- Per-author LinkedIn collection files and manifest, with the authenticated-scrape blocker documented.

Research structure:
- `research/sources.md` - expert list, source links, dates, annotations, and why each person was selected.
- `research/linkedin-posts/` - per-author LinkedIn collection folders and current scrape status.
- `research/youtube-transcripts/` - transcripts and per-author video summaries organized by expert.
- `research/other/` - collection status, YouTube manifests, channel inventory, and supporting notes.
- `research/ai-seo-expert-verification.csv` - proof-strength table for selected, backup, and rejected candidates.

Chosen experts, strong to weak:
1. Tibo Maker
2. John Rush
3. Samanyou Garg
4. Jacky Chou
5. Ross Hudgens
6. Ross Simmonds
7. Bernard Huang
8. Tim Soulo
9. Gael Breton
10. Bhanu Teja P

Quality control:
- Removed weak or unverified candidates instead of forcing the list: Eugene Zolotarenko, Tanya Van Gastel, and Elston Baretto remain dropped/pending.
- Prioritized people with real products, agencies, or SaaS growth systems, not generic AI or SEO commentators.
- Marked LinkedIn scraping as pending because no Apify token or authenticated browser bridge was available in this environment.
- Kept failed YouTube transcript attempts in the manifest so source coverage and gaps are visible.

Key manifests:
- `research/other/ai-seo-youtube-videos-manifest.csv`
- `research/other/ai-seo-youtube-channel-inventory.csv`
- `research/linkedin-posts/ai-seo-linkedin-manifest.csv`
- `research/other/ai-seo-collection-status.md`
