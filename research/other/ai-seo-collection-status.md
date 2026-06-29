# AI SEO Collection Status

Date: 2026-06-29

## Completed

- Ranked 10 AI-powered SEO content-production experts from strong to weak in `research/sources.md`.
- Added verification CSV at `research/ai-seo-expert-verification.csv`.
- Added a free-method YouTube collector script: `scrape_ai_seo_youtube_transcripts.py`.
- Collected/copied YouTube transcript files where captions or local transcripts were available.
- Created YouTube manifests:
  - `research/other/ai-seo-youtube-videos-manifest.csv`
  - `research/other/ai-seo-youtube-channel-inventory.csv`
- Created per-author YouTube summary files under `research/youtube-transcripts/<author>/videos.md`.

## YouTube Collection Notes

Collected transcript files are available for:
- Tim Soulo / Ahrefs: 5 recent transcripts.
- Gael Breton / Authority Hacker: 5 recent transcripts.
- Tibo Maker / Outrank: 1 local Starter Story transcript.
- John Rush / SEObot: 1 local Starter Story transcript.
- Bhanu Teja P / SiteGPT: 1 local Starter Story transcript.

Recent YouTube URLs were collected, but free transcript extraction found no English captions for:
- Samanyou Garg / Writesonic.
- Bernard Huang / Clearscope.
- Ross Hudgens / Siege Media.
- Ross Simmonds / Foundation.
- Jacky Chou / Indexsy.

## LinkedIn Collection Blocker

Full LinkedIn post scraping was not completed in this run.

Reason:
- No `APIFY_TOKEN` or `APIFY_API_TOKEN` was available in the shell environment.
- Kimi WebBridge was checked for authenticated browser scraping, but the expected command was not installed at `C:\Users\Admin\.kimi-webbridge\bin\kimi-webbridge`.
- Without an authenticated scraper or browser session, collecting full recent LinkedIn post text would be unreliable and likely incomplete.

What is in the repo:
- Per-author LinkedIn placeholder/status files under `research/linkedin-posts/<author>/posts.md`.
- A LinkedIn manifest at `research/linkedin-posts/ai-seo-linkedin-manifest.csv`.

Next collection step:
- Run `codex mcp login apify` or provide an authenticated LinkedIn scraping route, then collect 10-15 recent posts per author into the existing per-author folders.

