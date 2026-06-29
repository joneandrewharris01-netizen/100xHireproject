# AI SEO Collection Status

Date: 2026-06-29

## Completed

- Ranked 10 AI-powered SEO content-production experts from strong to weak in `research/sources.md`.
- Added verification CSV at `research/ai-seo-expert-verification.csv`.
- Added a free-method YouTube collector script: `scrape_ai_seo_youtube_transcripts.py`.
- Collected/copied YouTube transcript files where captions, local transcripts, or local ASR were available.
- Created YouTube manifests:
  - `research/other/ai-seo-youtube-videos-manifest.csv`
  - `research/other/ai-seo-youtube-channel-inventory.csv`
  - `research/other/ai-seo-youtube-complete-inventory.csv`
  - `research/other/ai-seo-youtube-complete-transcript-manifest.csv`
- Created per-author YouTube summary files under `research/youtube-transcripts/<author>/videos.md`.
- Collected visible recent LinkedIn posts for all 10 experts under `research/linkedin-posts/<author>/posts.md`.
- Updated `research/linkedin-posts/ai-seo-linkedin-manifest.csv` with profile URLs and post counts.

## YouTube Collection Notes

The complete inventory tracks 70 recent videos total, 7 per expert.

Available transcript files are reconciled for 26 videos:
- Tibo Maker / Outrank: 7 transcripts.
- John Rush / SEObot: 7 transcripts.
- Tim Soulo / Ahrefs: 5 transcripts.
- Gael Breton / Authority Hacker: 5 transcripts.
- Samanyou Garg / Writesonic: 1 transcript.
- Bhanu Teja P / SiteGPT: 1 transcript.

The manifest keeps 44 recent videos as pending. Those videos did not have a local transcript file available in this run; completing them requires either a transcript API with access to those videos or a longer local ASR batch.

## LinkedIn Collection

Visible LinkedIn posts were collected from the authenticated browser session:

- Tibo Maker: 15 posts.
- John Rush: 15 posts.
- Samanyou Garg: 15 posts.
- Jacky Chou: 5 posts.
- Ross Hudgens: 5 posts.
- Ross Simmonds: 5 posts.
- Bernard Huang: 5 posts.
- Tim Soulo: 5 posts.
- Gael Breton: 5 posts.
- Bhanu Teja P: 5 posts.

What is in the repo:
- Per-author LinkedIn post files under `research/linkedin-posts/<author>/posts.md`.
- A LinkedIn manifest at `research/linkedin-posts/ai-seo-linkedin-manifest.csv`.

Apify actor note:
- The requested actor is `curious_coder/linkedin-post-search-scraper` / `kfiWbq3boy3dWKbiL`.
- Its input schema requires LinkedIn cookies and `userAgent`, plus `urls`, `limitPerSource`, optional `scrapeUntilDate`, `deepScrape`, and proxy settings.
- The Apify console opened to sign-up in the browser profile, and no `APIFY_TOKEN` or `APIFY_API_TOKEN` was available in the shell.
- A safe input template without secrets is saved at `research/other/apify-linkedin-post-scraper-input-template.json`.
