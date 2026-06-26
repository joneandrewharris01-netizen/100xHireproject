import csv
import html
import json
import os
import re
import shutil
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
YTDEPS = ROOT / ".tmp_tools" / "ytdeps"
if YTDEPS.exists():
    sys.path.insert(0, str(YTDEPS))

try:
    import yt_dlp
except Exception as exc:
    raise SystemExit("yt_dlp is required in .tmp_tools/ytdeps for YouTube inventory.") from exc


RESEARCH = ROOT / "research"
LINKEDIN_DIR = RESEARCH / "linkedin-posts"
YOUTUBE_DIR = RESEARCH / "youtube-transcripts"
OTHER_DIR = RESEARCH / "other"
SCRAPE_DIR = OTHER_DIR / "replacement-scrape"


def slugify_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


REMOVE_EXPERTS = ["Alex Berman", "Collin Stewart", "Kyle Vamvouris"]
REMOVE_SLUGS = [slugify_name(name) for name in REMOVE_EXPERTS]

FINAL_EXPERTS = [
    "Jason Bay",
    "Armand Farrokh",
    "John Barrows",
    "Sam McKenna",
    "Morgan J Ingram",
    "Josh Braun",
    "Becc Holland",
    "Thibaut Souyris",
    "Richard Harris",
    "Marcus Chan",
]

NEW_EXPERTS = {
    "Josh Braun": {
        "rank": "6",
        "linkedin_url": "https://www.linkedin.com/in/josh-braun",
        "youtube_channel_name": "Josh Braun",
        "youtube_channel_url": "https://www.youtube.com/channel/UCK9rfCmYHBIaC9o-qOsNtLg",
        "proof_url": "https://joshbraun.com/",
        "proof": "Runs Braun Training and a public sales education business around stop-persuading, cold-call anxiety, conversations, and buyer resistance. His site links to a podcast, newsletter, LinkedIn, and client proof.",
        "brand_tier": "Very strong personal brand",
        "brand_reason": "Distinct voice around 'stop persuading', lower-pressure cold outreach, objection handling, and conversations with skeptical prospects.",
        "source_note": "Official site states the positioning around fewer rejections, more conversations, free mini-course, podcast, newsletter, and LinkedIn presence.",
    },
    "Becc Holland": {
        "rank": "7",
        "linkedin_url": "https://www.linkedin.com/in/beccholland-flipthescript",
        "youtube_channel_name": "Flip the Script",
        "youtube_channel_url": "https://www.youtube.com/channel/UCEW00AJeLgV8MtvLcDxLn7w",
        "proof_url": "https://www.flipthescript.com/",
        "proof": "CEO of Flip the Script, a sales training hub with training, SKOs, sequences and cadences, personalization at scale, cold email, cold calling, and sales development material.",
        "brand_tier": "Very strong personal/training brand",
        "brand_reason": "Flip the Script has a highly recognizable voice around personalization, diagnostic selling, cold outreach, and practical sales development.",
        "source_note": "Flip the Script site lists a free sales training hub, services, sequences/cadences, personalization at scale, core sessions, and Becc Stack.",
    },
    "Thibaut Souyris": {
        "rank": "8",
        "linkedin_url": "https://www.linkedin.com/in/thibautsouyris",
        "youtube_channel_name": "SalesLabs",
        "youtube_channel_url": "https://www.youtube.com/channel/UCsuk2arEu6z70FkfLLE0h1Q",
        "proof_url": "https://www.saleslabs.io/",
        "proof": "Founder/operator of SalesLabs; teaches prospecting, AI outreach, cold messaging, LinkedIn sequences, and meeting booking through courses, newsletter, articles, and consulting.",
        "brand_tier": "Strong prospecting creator brand",
        "brand_reason": "SalesLabs is narrowly aligned to booking more meetings, reply rates, prospecting systems, and cold-message workflows.",
        "source_note": "SalesLabs site lists The Prospecting Engine, The AI Outreach System, The New Outreach System, The Cold Message System, and a LinkedIn Top Voice founder story.",
    },
}

KEPT_EXPERTS = {
    "Jason Bay": {
        "rank": "1",
        "linkedin_url": "https://www.linkedin.com/in/jasondbay/",
        "youtube_channel_name": "Jason Bay",
        "proof_url": "https://outboundsquad.com/",
        "proof": "CEO of Outbound Squad, a company built around training B2B sales teams on outbound pipeline.",
        "brand_tier": "Strong personal/operator brand",
        "brand_reason": "Outbound Squad is tightly aligned with cold outbound, pipeline generation, and B2B sales team training.",
    },
    "Armand Farrokh": {
        "rank": "2",
        "linkedin_url": "https://www.linkedin.com/in/armand-farrokh",
        "youtube_channel_name": "30 Minutes to President's Club",
        "proof_url": "https://www.30mpc.com/",
        "proof": "Co-founder of 30MPC and former sales leader; teaches tactical cold call, cold email, and discovery systems.",
        "brand_tier": "Very strong personal/media brand",
        "brand_reason": "30 Minutes to President's Club has a distinctive tactical sales voice around scripts, cold calls, cold email, negotiation, and discovery.",
    },
    "John Barrows": {
        "rank": "3",
        "linkedin_url": "https://www.linkedin.com/in/johnbarrows/",
        "youtube_channel_name": "John Barrows",
        "proof_url": "https://jbarrows.com/",
        "proof": "Founder of JB Sales; sells sales training for individuals and teams.",
        "brand_tier": "Strong trainer brand",
        "brand_reason": "JB Sales and John's public content are consistently opinionated around prospecting, AI personalization, and practical sales execution.",
    },
    "Sam McKenna": {
        "rank": "4",
        "linkedin_url": "https://www.linkedin.com/in/samsalesli",
        "youtube_channel_name": "Samantha McKenna - #samsales",
        "proof_url": "https://www.samsalesconsulting.com/",
        "proof": "Founder/CEO of #samsales; sells sales training, LinkedIn branding, social selling, sales cadences, and playbooks.",
        "brand_tier": "Very strong personal brand",
        "brand_reason": "#samsales and Show Me You Know Me are clear branded concepts; her posts connect training, social selling, executive branding, and real client/keynote work.",
    },
    "Morgan J Ingram": {
        "rank": "5",
        "linkedin_url": "https://www.linkedin.com/in/morganjingramamp",
        "youtube_channel_name": "Morgan J Ingram",
        "proof_url": "https://www.morganjingram.com/",
        "proof": "Sales trainer focused on SDR/BDR prospecting and outbound execution; teaches from practical rep and training experience.",
        "brand_tier": "Strong creator/operator brand",
        "brand_reason": "Morgan publishes current LinkedIn, Sales Navigator, AI, SDR/BDR, and outbound content with a recognizable creator voice.",
    },
    "Richard Harris": {
        "rank": "9",
        "linkedin_url": "https://www.linkedin.com/in/rharris415/",
        "youtube_channel_name": "Richard Harris",
        "proof_url": "https://theharrisconsultinggroup.com/",
        "proof": "Founder/operator of The Harris Consulting Group; sells live training, founder-led sales training, online sales training, and AI sales coaching.",
        "brand_tier": "Good personal trainer brand",
        "brand_reason": "Richard has a direct sales-training POV around sales lies, discovery, deal control, and leadership accountability.",
    },
    "Marcus Chan": {
        "rank": "10",
        "linkedin_url": "https://www.linkedin.com/in/marcuschanmba/",
        "youtube_channel_name": "Marcus Chan",
        "proof_url": "https://venliconsulting.com/",
        "proof": "CEO of Venli Consulting Group; serves SaaS, services, and complex B2B sales teams with tactical coaching tied to pipeline.",
        "brand_tier": "Good sales-coach brand",
        "brand_reason": "Marcus has real coaching proof and posts about prospecting, leadership, and sales performance.",
    },
}


def main():
    SCRAPE_DIR.mkdir(parents=True, exist_ok=True)
    token = get_token()

    remove_weak_expert_folders()

    new_youtube_rows, transcript_rows = collect_new_youtube_transcripts(token)
    write_new_youtube_folders(new_youtube_rows, transcript_rows)

    new_linkedin_rows, raw_by_expert = collect_new_linkedin_posts(token)
    write_new_linkedin_folders(new_linkedin_rows, raw_by_expert)

    rebuild_manifests(new_youtube_rows, new_linkedin_rows)
    rewrite_sources_and_readme()
    write_replacement_notes()

    print("Upgraded expert set.")
    print("Removed:", ", ".join(REMOVE_EXPERTS))
    print("Added:", ", ".join(NEW_EXPERTS))


def get_token() -> str:
    token = os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    if token:
        return token
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                for name in ("APIFY_TOKEN", "APIFY_API_TOKEN"):
                    try:
                        value, _ = winreg.QueryValueEx(key, name)
                        if value:
                            return value
                    except FileNotFoundError:
                        pass
        except Exception:
            pass
    raise SystemExit("Missing APIFY_TOKEN.")


def remove_weak_expert_folders():
    for slug in REMOVE_SLUGS:
        for parent in (LINKEDIN_DIR, YOUTUBE_DIR):
            target = parent / slug
            if target.exists():
                shutil.rmtree(target)


def collect_new_youtube_transcripts(token: str):
    inventory_path = SCRAPE_DIR / "replacement-youtube-video-inventory.csv"
    transcript_manifest_path = SCRAPE_DIR / "replacement-youtube-transcript-manifest.csv"
    if inventory_path.exists() and transcript_manifest_path.exists():
        return read_csv(inventory_path), read_csv(transcript_manifest_path)

    videos = []
    for expert, info in NEW_EXPERTS.items():
        videos.extend(extract_recent_videos(expert, info["youtube_channel_name"], info["youtube_channel_url"], 7))
    write_csv(inventory_path, videos)

    urls = [row["url"] for row in videos]
    transcript_items, run = run_youtube_transcript_actor(token, urls)
    (SCRAPE_DIR / "replacement-youtube-transcript-run.json").write_text(
        json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (SCRAPE_DIR / "replacement-youtube-transcript-items.json").write_text(
        json.dumps(transcript_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    transcript_rows = export_new_transcripts(videos, transcript_items, run)
    write_csv(SCRAPE_DIR / "replacement-youtube-transcript-manifest.csv", transcript_rows)
    return videos, transcript_rows


def extract_recent_videos(expert: str, channel_name: str, channel_url: str, limit: int):
    rows = []
    with yt_dlp.YoutubeDL(
        {
            "extract_flat": "in_playlist",
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "socket_timeout": 30,
            "retries": 3,
        }
    ) as ydl:
        info = ydl.extract_info(channel_url.rstrip("/") + "/videos", download=False)
    for entry in (info or {}).get("entries") or []:
        video_id = entry.get("id")
        if not video_id or len(video_id) != 11:
            continue
        rows.append(
            {
                "expert": expert,
                "video_count_for_expert": "",
                "video_rank": len(rows) + 1,
                "channel_name": channel_name,
                "video_id": video_id,
                "title": html.unescape(entry.get("title") or video_id),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration_seconds": entry.get("duration") or "",
                "transcript_status": "",
                "transcript_chars": "",
                "transcript_file": "",
            }
        )
        if len(rows) >= limit:
            break
    for row in rows:
        row["video_count_for_expert"] = len(rows)
    return rows


def run_youtube_transcript_actor(token: str, urls):
    payload = {
        "urls": [{"url": url} for url in urls],
        "outputFormat": "json",
        "languages": ["en"],
    }
    run = api_json(
        "POST",
        "/acts/supreme_coder~youtube-transcript-scraper/runs",
        token,
        payload=payload,
        params={"maxTotalChargeUsd": 0.25},
        timeout=180,
    )["data"]
    run = wait_for_run(token, run["id"], timeout_seconds=360)
    dataset_id = run.get("defaultDatasetId")
    items = api_json("GET", f"/datasets/{dataset_id}/items", token, params={"clean": "true", "format": "json"}, timeout=180)
    return items if isinstance(items, list) else [], run


def wait_for_run(token: str, run_id: str, timeout_seconds: int):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        run = api_json("GET", f"/actor-runs/{run_id}", token, timeout=120)["data"]
        if run.get("status") in {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}:
            if run.get("status") != "SUCCEEDED":
                raise RuntimeError(f"Apify run {run_id} ended with {run.get('status')}")
            return run
        print(f"Run {run_id}: {run.get('status')}", flush=True)
        time.sleep(8)
    raise TimeoutError(f"Timed out waiting for run {run_id}")


def export_new_transcripts(videos, items, run):
    video_by_id = {row["video_id"]: row for row in videos}
    rows = []
    for item in items:
        video_url = item.get("videoUrl") or item.get("url") or item.get("inputUrl") or ""
        video_id = item.get("videoId") or video_id_from_url(str(video_url))
        source = video_by_id.get(video_id, {})
        text = transcript_text(item)
        expert = source.get("expert", "")
        title = html.unescape(str(item.get("title") or source.get("title") or video_id))
        transcript_file = ""
        status = "ok" if text else "error"
        if expert and video_id:
            folder = YOUTUBE_DIR / slugify_name(expert)
            folder.mkdir(parents=True, exist_ok=True)
            output = folder / safe_filename(f"{source.get('video_rank', '')}-{video_id}-{title}.txt")
            output.write_text(
                "Metadata:\n"
                + json.dumps(
                    {
                        "expert": expert,
                        "channel_name": source.get("channel_name", ""),
                        "video_id": video_id,
                        "title": title,
                        "video_url": source.get("url", video_url),
                        "run_id": run.get("id", ""),
                        "dataset_id": run.get("defaultDatasetId", ""),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n\nTranscript:\n"
                + text
                + "\n",
                encoding="utf-8",
            )
            transcript_file = str(output.relative_to(ROOT)).replace("\\", "/")
        rows.append(
            {
                "expert": expert,
                "video_id": video_id,
                "status": status,
                "transcript_chars": len(text),
                "transcript_file": transcript_file,
            }
        )
    return rows


def write_new_youtube_folders(videos, transcript_rows):
    transcript_by_id = {row["video_id"]: row for row in transcript_rows}
    for expert in NEW_EXPERTS:
        slug = slugify_name(expert)
        folder = YOUTUBE_DIR / slug
        expert_rows = []
        for row in [r for r in videos if r["expert"] == expert]:
            transcript = transcript_by_id.get(row["video_id"], {})
            row = dict(row)
            row["transcript_status"] = transcript.get("status", "")
            row["transcript_chars"] = transcript.get("transcript_chars", "")
            row["transcript_file"] = transcript.get("transcript_file", "")
            row["local_transcript_file"] = transcript.get("transcript_file", "")
            expert_rows.append(row)
        write_csv(folder / "manifest.csv", expert_rows)
        write_videos_md(folder / "videos.md", expert, expert_rows)


def collect_new_linkedin_posts(token: str):
    raw_path = SCRAPE_DIR / "replacement-linkedin-posts-raw.json"
    if raw_path.exists():
        with raw_path.open("r", encoding="utf-8-sig") as file:
            items = json.load(file)
    else:
        target_urls = [info["linkedin_url"] for info in NEW_EXPERTS.values()]
        payload = {
            "targetUrls": target_urls,
            "maxPosts": 15,
            "postedLimit": "any",
            "includeQuotePosts": True,
            "includeReposts": False,
            "scrapeReactions": False,
            "scrapeComments": False,
        }
        items = api_json(
            "POST",
            "/acts/harvestapi~linkedin-profile-posts/run-sync-get-dataset-items",
            token,
            payload=payload,
            params={"timeout": 240, "memory": 1024, "maxTotalChargeUsd": 0.60},
            timeout=300,
        )
        if not isinstance(items, list):
            items = []
        raw_path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    target_to_expert = {
        normalize_profile_url(info["linkedin_url"]): expert for expert, info in NEW_EXPERTS.items()
    }
    rows = []
    raw_by_expert = defaultdict(list)
    for item in items:
        target = normalize_profile_url(item.get("query", {}).get("targetUrl", ""))
        expert = target_to_expert.get(target)
        if not expert:
            identifier = item.get("author", {}).get("publicIdentifier", "")
            if identifier == "josh-braun":
                expert = "Josh Braun"
            elif "beccholland" in identifier:
                expert = "Becc Holland"
            elif identifier == "thibautsouyris":
                expert = "Thibaut Souyris"
        if not expert:
            continue
        raw_by_expert[expert].append(item)

    for expert in NEW_EXPERTS:
        posts = sorted(
            raw_by_expert.get(expert, []),
            key=lambda item: item.get("postedAt", {}).get("timestamp", 0),
            reverse=True,
        )[:15]
        raw_by_expert[expert] = posts
        for index, item in enumerate(posts, start=1):
            content = normalize_space(item.get("content", ""))
            engagement = item.get("engagement") or {}
            rows.append(
                {
                    "expert": expert,
                    "profile_url": NEW_EXPERTS[expert]["linkedin_url"],
                    "post_count_for_expert": len(posts),
                    "post_rank": index,
                    "author_name": item.get("author", {}).get("name", ""),
                    "author_public_identifier": item.get("author", {}).get("publicIdentifier", ""),
                    "posted_at": iso_date(item.get("postedAt", {}).get("date", "")),
                    "posted_ago": item.get("postedAt", {}).get("postedAgoShort", ""),
                    "post_url": item.get("linkedinUrl", ""),
                    "feed_url": item.get("shareLinkedinUrl", ""),
                    "likes": engagement.get("likes", ""),
                    "comments": engagement.get("comments", ""),
                    "shares": engagement.get("shares", ""),
                    "content_chars": len(content),
                    "post_format": post_format(item),
                    "has_image": bool(item.get("postImages")),
                    "is_repost": bool(item.get("repostId")),
                    "content_signal": content_signal(content),
                    "post_id": str(item.get("id") or item.get("entityId") or item.get("linkedinUrl")),
                    "content": content,
                    "author_info": item.get("author", {}).get("info", ""),
                }
            )
    return rows, raw_by_expert


def write_new_linkedin_folders(rows, raw_by_expert):
    for expert in NEW_EXPERTS:
        folder = LINKEDIN_DIR / slugify_name(expert)
        folder.mkdir(parents=True, exist_ok=True)
        expert_rows = [row for row in rows if row["expert"] == expert]
        write_csv(folder / "posts.csv", expert_rows)
        (folder / "posts.json").write_text(
            json.dumps(raw_by_expert.get(expert, []), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_posts_md(folder / "posts.md", expert, expert_rows)


def rebuild_manifests(new_youtube_rows, new_linkedin_rows):
    linkedin_manifest = []
    all_linkedin_posts = []
    for expert in FINAL_EXPERTS:
        posts_path = LINKEDIN_DIR / slugify_name(expert) / "posts.csv"
        if not posts_path.exists():
            continue
        posts = read_csv(posts_path)[:15]
        all_linkedin_posts.extend(posts)
        for row in posts:
            linkedin_manifest.append(
                {
                    "expert": row["expert"],
                    "post_rank": row["post_rank"],
                    "posted_at": row["posted_at"],
                    "post_url": row["post_url"],
                    "local_file": f"research/linkedin-posts/{slugify_name(row['expert'])}/posts.csv",
                }
            )
    write_csv(LINKEDIN_DIR / "manifest.csv", sort_manifest(linkedin_manifest, "post_rank"))
    write_csv(OTHER_DIR / "linkedin-posts-manifest.csv", all_linkedin_posts)

    youtube_manifest = []
    for expert in FINAL_EXPERTS:
        manifest = YOUTUBE_DIR / slugify_name(expert) / "manifest.csv"
        if manifest.exists():
            youtube_manifest.extend(read_csv(manifest))
    write_csv(YOUTUBE_DIR / "manifest.csv", sort_manifest(youtube_manifest, "video_rank"))
    write_csv(OTHER_DIR / "youtube-videos-manifest.csv", youtube_manifest)

    selected = []
    for expert in FINAL_EXPERTS:
        selected.append(selected_expert_row(expert))
    write_csv(OTHER_DIR / "selected-experts.csv", selected)


def sort_manifest(rows, rank_key):
    order = {expert: index for index, expert in enumerate(FINAL_EXPERTS)}
    return sorted(rows, key=lambda row: (order.get(row.get("expert", ""), 999), int(row.get(rank_key) or 0)))


def selected_expert_row(expert: str):
    info = expert_info(expert)
    return {
        "topic_id": "1",
        "topic": "Cold outreach pipeline for B2B SaaS",
        "rank": info["rank"],
        "expert": expert,
        "linkedin_active": "Yes",
        "linkedin_reason": "Recent public LinkedIn posts collected and organized in research/linkedin-posts.",
        "youtube_active": "Yes",
        "youtube_reason": "Recent public YouTube videos/transcripts collected and organized in research/youtube-transcripts.",
        "practices_what_they_teach": "Yes",
        "practice_proof": info["proof"],
        "proof_strength": "Strong",
        "proof_urls": info["proof_url"],
    }


def rewrite_sources_and_readme():
    linkedin_counts = count_by(read_csv(LINKEDIN_DIR / "manifest.csv"), "expert")
    youtube_counts = count_by(read_csv(YOUTUBE_DIR / "manifest.csv"), "expert")
    lines = [
        "# Sources: B2B SaaS Cold Outbound Experts",
        "",
        f"Collection date: {datetime.now().date().isoformat()}",
        "",
        "Topic: B2B SaaS cold outbound, including cold email, cold calling, LinkedIn/social selling, SDR/BDR pipeline, and outbound sales leadership.",
        "",
        "Selection standard:",
        "- Publicly teaches through LinkedIn, YouTube, podcast, newsletter, or owned media.",
        "- Has operator proof: founder, trainer, sales leader, agency/SaaS operator, or company that practices outbound with clients.",
        "- Recent material is strong enough to mine for a later playbook.",
        "- Weak current-fit sources were replaced with stronger cold-outbound voices.",
        "",
        "## Expert List",
        "",
        "| # | Expert | Brand/readiness tier | LinkedIn profile | YouTube/source channel | Materials collected | Why chosen | Proof URL |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for index, expert in enumerate(FINAL_EXPERTS, start=1):
        info = expert_info(expert)
        lines.append(
            "| {index} | {expert} | {tier} | {linkedin} | {channel} | {materials} | {why} | {proof_url} |".format(
                index=index,
                expert=escape_table(expert),
                tier=escape_table(info["brand_tier"]),
                linkedin=info["linkedin_url"],
                channel=escape_table(info["youtube_channel_name"]),
                materials=escape_table(
                    f"{linkedin_counts.get(expert, 0)} LinkedIn posts; {youtube_counts.get(expert, 0)} YouTube transcripts"
                ),
                why=escape_table(info["proof"] + " " + info["brand_reason"]),
                proof_url=info["proof_url"],
            )
        )
    lines.extend(
        [
            "",
            "## Replacement Notes",
            "",
            "- Removed Alex Berman: historically relevant for cold email, but recent LinkedIn content was broader business/finance and weaker for a current cold-outbound playbook.",
            "- Removed Collin Stewart: strong operator, but the research material was more company/podcast-led than a distinct personal cold-outbound voice.",
            "- Removed Kyle Vamvouris: real operator, but recent material skewed toward AI sales systems and generic sales diagnostics rather than cold outbound voice.",
            "- Added Josh Braun, Becc Holland, and Thibaut Souyris because their public content is more directly tied to prospecting, cold messaging, personalization, and booking meetings.",
            "",
            "## Collection Notes",
            "",
            "- YouTube transcripts were collected through the Apify YouTube transcript actor after selecting recent videos for each expert.",
            "- LinkedIn posts were collected through the Apify LinkedIn profile-posts actor, capped at 15 recent public posts per expert.",
            "- Sam McKenna's LinkedIn profile was corrected to `https://www.linkedin.com/in/samsalesli`; an earlier `samsales` result was a different person and was excluded.",
        ]
    )
    (RESEARCH / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    readme = [
        "# 100xHireproject",
        "",
        "## B2B SaaS Cold Outbound Research Project",
        "",
        "This repository includes a source-backed research project for building a future B2B SaaS cold-outbound playbook.",
        "",
        "Topic: B2B SaaS cold outbound across cold email, cold calling, LinkedIn/social selling, SDR/BDR pipeline creation, and outbound sales leadership.",
        "",
        "What was collected:",
        "- 10 practitioner-experts selected for real operator proof and strong cold-outbound voice.",
        "- 150 recent LinkedIn posts, organized by author.",
        "- 70 recent YouTube transcripts, organized by expert and video.",
        "- Source notes, methodology, replacement notes, and a brand-voice audit.",
        "",
        "Research structure:",
        "- `research/sources.md` - expert list, source links, collection notes, and why each person was selected.",
        "- `research/linkedin-posts/` - latest LinkedIn posts organized by author, with per-author CSV/JSON/Markdown files.",
        "- `research/youtube-transcripts/` - recent YouTube transcripts organized by expert and video.",
        "- `research/other/` - methodology, manifests, selected-expert CSV, replacement notes, and brand-voice audit.",
        "",
        "Chosen experts:",
    ]
    readme.extend([f"{index}. {expert}" for index, expert in enumerate(FINAL_EXPERTS, start=1)])
    readme.extend(
        [
            "",
            "Quality control:",
            "- Replaced weaker current-fit sources Alex Berman, Collin Stewart, and Kyle Vamvouris.",
            "- Added stronger cold-outbound voices Josh Braun, Becc Holland, and Thibaut Souyris.",
            "- The strongest primary voices are Sam McKenna, Armand Farrokh, Jason Bay, John Barrows, Morgan J Ingram, Josh Braun, Becc Holland, and Thibaut Souyris.",
            "- Each selected expert has public teaching content plus evidence that they practice or operate in the area they teach.",
        ]
    )
    (ROOT / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")


def write_replacement_notes():
    lines = [
        "# Replacement Notes",
        "",
        "The initial research package included three weaker current-fit sources. They were replaced to improve the quality of the eventual playbook source base.",
        "",
        "| Removed | Reason | Replacement | Why stronger |",
        "|---|---|---|---|",
        "| Alex Berman | Strong historical cold-email name, but recent LinkedIn content was not tightly cold-outbound focused. | Josh Braun | More distinctive current prospecting/cold-call voice and strong public training brand. |",
        "| Collin Stewart | Real operator, but source material was more company/podcast-led than personal brand-led. | Becc Holland | Flip the Script is directly built around personalization, cold outreach, sales development, and training. |",
        "| Kyle Vamvouris | Real operator, but recent material skewed toward AI sales diagnostics and systems. | Thibaut Souyris | SalesLabs is narrowly focused on prospecting, reply rates, cold messaging, and booking meetings. |",
        "",
        "Replacement sources:",
        "- Josh Braun: https://joshbraun.com/",
        "- Becc Holland / Flip the Script: https://www.flipthescript.com/",
        "- Thibaut Souyris / SalesLabs: https://www.saleslabs.io/",
    ]
    (OTHER_DIR / "replacement-notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    audit_lines = [
        "# Brand Voice Audit",
        "",
        "Purpose: separate real personal/operator brands from people who merely appear in search results.",
        "",
        "| Expert | Verdict | Reason |",
        "|---|---|---|",
    ]
    for expert in FINAL_EXPERTS:
        info = expert_info(expert)
        audit_lines.append(f"| {expert} | {escape_table(info['brand_tier'])} | {escape_table(info['brand_reason'])} |")
    audit_lines.extend(
        [
            "",
            "Primary voices for the later playbook: Sam McKenna, Armand Farrokh, Jason Bay, John Barrows, Morgan J Ingram, Josh Braun, Becc Holland, and Thibaut Souyris.",
            "",
            "Useful secondary/operator voices: Richard Harris and Marcus Chan.",
        ]
    )
    (OTHER_DIR / "brand-voice-audit.md").write_text("\n".join(audit_lines) + "\n", encoding="utf-8")


def expert_info(expert: str):
    return NEW_EXPERTS.get(expert) or KEPT_EXPERTS[expert]


def write_videos_md(path: Path, expert: str, rows):
    lines = [
        f"# YouTube Transcripts: {expert}",
        "",
        "Recent videos selected for B2B SaaS cold-outbound research.",
        "",
        "| # | Title | URL | Transcript file |",
        "|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['video_rank']} | {escape_table(row['title'])} | {row['url']} | `{row.get('local_transcript_file') or row.get('transcript_file', '')}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_posts_md(path: Path, expert: str, rows):
    lines = [
        f"# LinkedIn Posts: {expert}",
        "",
        "Recent public LinkedIn posts collected for cold-outbound voice and playbook research.",
        "",
        "| # | Date | Likes | Comments | Shares | Signal | URL |",
        "|---:|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['post_rank']} | {row['posted_at']} | {row['likes']} | {row['comments']} | {row['shares']} | {escape_table(row['content_signal'])} | {row['post_url']} |"
        )
    lines.extend(["", "Full scraped post text is in `posts.csv` and raw actor output is in `posts.json`."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def api_json(method: str, path: str, token: str, payload=None, params=None, timeout=120):
    query = {"token": token}
    if params:
        query.update(params)
    url = f"https://api.apify.com/v2{path}?{urllib.parse.urlencode(query)}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method=method)
    last_error = None
    for attempt in range(1, 6):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8", errors="replace")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Apify HTTP {exc.code}: {body}") from exc
        except (urllib.error.URLError, socket.gaierror, TimeoutError) as exc:
            last_error = exc
            time.sleep(min(60, 2**attempt))
    raise RuntimeError(f"Apify request failed after retries: {last_error}")


def transcript_text(item):
    transcript = item.get("transcript")
    if isinstance(transcript, str):
        return html.unescape(transcript).strip()
    if isinstance(transcript, list):
        return "\n".join(
            html.unescape(str(row.get("text", ""))) for row in transcript if isinstance(row, dict) and row.get("text")
        ).strip()
    return html.unescape(str(item.get("text") or item.get("transcriptText") or "")).strip()


def video_id_from_url(url: str):
    for pattern in (r"[?&]v=([A-Za-z0-9_-]{11})", r"youtu\.be/([A-Za-z0-9_-]{11})"):
        match = re.search(pattern, url or "")
        if match:
            return match.group(1)
    return ""


def safe_filename(value: str):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return (value[:180] or "untitled") + ".txt"


def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def count_by(rows, key):
    counts = defaultdict(int)
    for row in rows:
        counts[row[key]] += 1
    return counts


def normalize_profile_url(url: str):
    url = str(url or "").split("?")[0].rstrip("/")
    url = re.sub(r"https://[a-z]{2}\.linkedin\.com", "https://www.linkedin.com", url)
    return url.lower()


def normalize_space(value: str):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def iso_date(value: str):
    if not value:
        return ""
    return value[:10]


def post_format(item):
    if item.get("repostId"):
        return "repost"
    if item.get("postImages"):
        return "image"
    if item.get("document"):
        return "document"
    if item.get("video"):
        return "video"
    return "text"


def content_signal(content: str):
    text = f" {content.lower()} "
    signals = [
        ("cold email", ["cold email", "email"]),
        ("cold calling", ["cold call", "calling"]),
        ("personalization", ["personalization", "personalized", "relevance"]),
        ("prospecting", ["prospect", "pipeline", "reply rate", "booking meetings"]),
        ("LinkedIn/social selling", ["linkedin", "sales navigator", "social selling"]),
        ("sales training", ["training", "workshop", "coach"]),
        ("AI/sales tech", [" ai ", "automation", "chatgpt"]),
        ("discovery/qualification", ["discovery", "qualification", "buyer"]),
        ("negotiation/closing", ["negotia", "close", "closing"]),
    ]
    matched = [label for label, needles in signals if any(needle in text for needle in needles)]
    return "; ".join(matched[:3]) if matched else "general sales/content"


def escape_table(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
