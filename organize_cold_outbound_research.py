import csv
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path


SOURCE_BASE = Path("cold-outreach-youtube-transcripts-2026/recent-7-per-prospect-apify")
RESEARCH = Path("research")
LINKEDIN_DIR = RESEARCH / "linkedin-posts"
YOUTUBE_DIR = RESEARCH / "youtube-transcripts"
OTHER_DIR = RESEARCH / "other"

SELECTED_PROSPECTS = Path("b2b-saas-cold-outreach-selected-10-prospects-2026.csv")
LINKEDIN_MANIFEST = SOURCE_BASE / "linkedin_recent_posts_manifest.csv"
LINKEDIN_RAW = SOURCE_BASE / "linkedin_recent_posts_raw.json"
LINKEDIN_SAM_RAW = SOURCE_BASE / "linkedin_recent_posts_sam_mckenna_corrected_raw.json"
YOUTUBE_MANIFEST = SOURCE_BASE / "youtube_recent_video_url_report.csv"
TRANSCRIPT_MANIFEST = SOURCE_BASE / "recent_transcript_manifest.csv"
PROFILE_TARGETS = SOURCE_BASE / "linkedin_profile_targets.csv"

EXPERT_ORDER = [
    "Jason Bay",
    "Armand Farrokh",
    "John Barrows",
    "Sam McKenna",
    "Morgan J Ingram",
    "Alex Berman",
    "Collin Stewart",
    "Kyle Vamvouris",
    "Richard Harris",
    "Marcus Chan",
]

AUTHOR_IDENTIFIER_TO_EXPERT = {
    "jasondbay": "Jason Bay",
    "armand-farrokh": "Armand Farrokh",
    "johnbarrows": "John Barrows",
    "samsalesli": "Sam McKenna",
    "morganjingramamp": "Morgan J Ingram",
    "alexanderberman": "Alex Berman",
    "collinstewart": "Collin Stewart",
    "kylevamvouris": "Kyle Vamvouris",
    "rharris415": "Richard Harris",
    "marcuschanmba": "Marcus Chan",
}

BRAND_TIERS = {
    "Jason Bay": ("Strong personal/operator brand", "Outbound Squad is tightly aligned with cold outbound, pipeline generation, and B2B sales team training."),
    "Armand Farrokh": ("Very strong personal/media brand", "30 Minutes to President's Club has a distinctive tactical sales voice around scripts, cold calls, cold email, negotiation, and discovery."),
    "John Barrows": ("Strong trainer brand", "JB Sales and John's public content are consistently opinionated around prospecting, AI personalization, and practical sales execution."),
    "Sam McKenna": ("Very strong personal brand", "#samsales and Show Me You Know Me are clear branded concepts; her posts connect training, social selling, executive branding, and real client/keynote work."),
    "Morgan J Ingram": ("Strong creator/operator brand", "Morgan publishes current LinkedIn, Sales Navigator, AI, SDR/BDR, and outbound content with a recognizable creator voice."),
    "Alex Berman": ("Historically strong, current-fit mixed", "Alex is a real cold-email/YouTube creator, but recent LinkedIn content is broader business and finance. Keep as a secondary source for cold-email history and YouTube material."),
    "Collin Stewart": ("Company-led operator brand", "Predictable Revenue is real outbound operating proof; Collin's voice is more tied to company/podcast content than a standalone personal brand."),
    "Kyle Vamvouris": ("Company-led operator brand", "Vouris is a real B2B sales consulting firm with video content; recent posts skew toward AI sales diagnostics and founder training."),
    "Richard Harris": ("Good personal trainer brand", "Richard has a direct sales-training POV around sales lies, discovery, deal control, and leadership accountability."),
    "Marcus Chan": ("Good sales-coach brand", "Marcus has real coaching proof and posts about prospecting, leadership, and sales performance, though broader than pure cold outbound."),
}


def main():
    ensure_dirs()
    prospects = load_csv_by_key(SELECTED_PROSPECTS, "expert")
    linkedin_profiles = load_csv_by_key(PROFILE_TARGETS, "expert")
    linkedin_rows = read_csv(LINKEDIN_MANIFEST)
    youtube_rows = read_csv(YOUTUBE_MANIFEST)
    transcript_rows = read_csv(TRANSCRIPT_MANIFEST)
    linkedin_raw_by_expert = load_linkedin_raw_by_expert()

    write_sources(prospects, linkedin_profiles, linkedin_rows, youtube_rows)
    write_linkedin_posts(linkedin_rows, linkedin_raw_by_expert)
    write_youtube_transcripts(youtube_rows, transcript_rows)
    write_other_materials(prospects, linkedin_rows, youtube_rows)
    write_readme()

    print("Organized research artifacts under research/")
    print(f"Experts: {len(EXPERT_ORDER)}")
    print(f"LinkedIn posts: {len(linkedin_rows)}")
    print(f"YouTube videos/transcripts: {len(youtube_rows)}")


def ensure_dirs():
    for directory in [RESEARCH, LINKEDIN_DIR, YOUTUBE_DIR, OTHER_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_csv_by_key(path, key):
    return {row[key]: row for row in read_csv(path)}


def load_json(path):
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def load_linkedin_raw_by_expert():
    raw_items = load_json(LINKEDIN_RAW)
    sam_items = load_json(LINKEDIN_SAM_RAW)
    filtered = [item for item in raw_items if item.get("author", {}).get("publicIdentifier") != "samsales"]
    filtered.extend(sam_items)

    by_expert = defaultdict(list)
    seen = set()
    for item in filtered:
        identifier = item.get("author", {}).get("publicIdentifier", "")
        expert = AUTHOR_IDENTIFIER_TO_EXPERT.get(identifier)
        if not expert:
            continue
        post_id = str(item.get("id") or item.get("entityId") or item.get("linkedinUrl"))
        if post_id in seen:
            continue
        seen.add(post_id)
        by_expert[expert].append(item)

    for expert, rows in by_expert.items():
        rows.sort(key=lambda item: item.get("postedAt", {}).get("timestamp", 0), reverse=True)
        by_expert[expert] = rows[:15]
    return by_expert


def write_sources(prospects, linkedin_profiles, linkedin_rows, youtube_rows):
    linkedin_counts = count_by(linkedin_rows, "expert")
    youtube_counts = count_by(youtube_rows, "expert")
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
        "",
        "## Expert List",
        "",
        "| # | Expert | Brand/readiness tier | LinkedIn profile | YouTube/source channel | Materials collected | Why chosen | Proof URL |",
        "|---:|---|---|---|---|---|---|---|",
    ]

    for index, expert in enumerate(EXPERT_ORDER, start=1):
        prospect = prospects[expert]
        profile = linkedin_profiles.get(expert, {}).get("linkedin_profile_url", "")
        channel_names = sorted({row["channel_name"] for row in youtube_rows if row["expert"] == expert})
        channel = ", ".join(channel_names)
        tier, tier_note = BRAND_TIERS[expert]
        materials = f"{linkedin_counts.get(expert, 0)} LinkedIn posts; {youtube_counts.get(expert, 0)} YouTube transcripts"
        why = f"{prospect['practice_proof']} {tier_note}"
        lines.append(
            "| {index} | {expert} | {tier} | {profile} | {channel} | {materials} | {why} | {proof} |".format(
                index=index,
                expert=escape_table(expert),
                tier=escape_table(tier),
                profile=profile,
                channel=escape_table(channel),
                materials=escape_table(materials),
                why=escape_table(why),
                proof=prospect["proof_urls"],
            )
        )

    lines.extend(
        [
            "",
            "## Collection Notes",
            "",
            "- YouTube transcripts were collected through the Apify YouTube transcript actor after selecting recent videos for each expert.",
            "- LinkedIn posts were collected through the Apify LinkedIn profile-posts actor, capped at 15 recent public posts per expert.",
            "- Sam McKenna's LinkedIn profile was corrected to `https://www.linkedin.com/in/samsalesli`; an earlier `samsales` result was a different person and was excluded.",
            "- Alex Berman is kept as a cold-email/YouTube source, but his recent LinkedIn content is a weaker cold-outbound fit than the top five experts.",
        ]
    )

    (RESEARCH / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_linkedin_posts(linkedin_rows, linkedin_raw_by_expert):
    manifest_rows = []
    for expert in EXPERT_ORDER:
        slug = slugify(expert)
        folder = LINKEDIN_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)

        rows = [row for row in linkedin_rows if row["expert"] == expert]
        raw_rows = linkedin_raw_by_expert.get(expert, [])
        raw_by_id = {str(item.get("id") or item.get("entityId") or item.get("linkedinUrl")): item for item in raw_rows}

        full_rows = []
        for row in rows:
            post_id = post_id_from_url(row["post_url"])
            raw = raw_by_id.get(post_id, {})
            content = normalize_space(raw.get("content", ""))
            full_row = {
                **row,
                "post_id": post_id,
                "content": content,
                "author_info": raw.get("author", {}).get("info", ""),
            }
            full_rows.append(full_row)
            manifest_rows.append(
                {
                    "expert": expert,
                    "post_rank": row["post_rank"],
                    "posted_at": row["posted_at"],
                    "post_url": row["post_url"],
                    "local_file": f"research/linkedin-posts/{slug}/posts.csv",
                }
            )

        write_csv(folder / "posts.csv", full_rows)
        (folder / "posts.json").write_text(json.dumps(raw_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_author_posts_md(folder / "posts.md", expert, full_rows)

    write_csv(LINKEDIN_DIR / "manifest.csv", manifest_rows)


def write_author_posts_md(path, expert, rows):
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
            "| {rank} | {date} | {likes} | {comments} | {shares} | {signal} | {url} |".format(
                rank=row["post_rank"],
                date=row["posted_at"],
                likes=row["likes"],
                comments=row["comments"],
                shares=row["shares"],
                signal=escape_table(row["content_signal"]),
                url=row["post_url"],
            )
        )
    lines.extend(["", "Full scraped post text is in `posts.csv` and raw actor output is in `posts.json`."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_youtube_transcripts(youtube_rows, transcript_rows):
    transcript_by_video = {row["video_id"]: row for row in transcript_rows}
    manifest_rows = []
    for expert in EXPERT_ORDER:
        slug = slugify(expert)
        folder = YOUTUBE_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)
        rows = [row for row in youtube_rows if row["expert"] == expert]
        author_manifest = []

        for row in rows:
            transcript = transcript_by_video.get(row["video_id"], {})
            source_file = Path(transcript.get("transcript_file", ""))
            local_name = safe_filename(f"{row['video_rank']}-{row['video_id']}-{row['title']}.txt")
            local_path = folder / local_name
            if source_file.exists():
                shutil.copy2(source_file, local_path)
            else:
                local_path.write_text("", encoding="utf-8")

            out_row = {
                "expert": expert,
                "video_rank": row["video_rank"],
                "channel_name": row["channel_name"],
                "video_id": row["video_id"],
                "title": row["title"],
                "url": row["url"],
                "duration_seconds": row["duration_seconds"],
                "transcript_status": row["transcript_status"],
                "transcript_chars": row["transcript_chars"],
                "local_transcript_file": str(local_path).replace("\\", "/"),
            }
            author_manifest.append(out_row)
            manifest_rows.append(out_row)

        write_csv(folder / "manifest.csv", author_manifest)
        write_author_videos_md(folder / "videos.md", expert, author_manifest)

    write_csv(YOUTUBE_DIR / "manifest.csv", manifest_rows)


def write_author_videos_md(path, expert, rows):
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
            "| {rank} | {title} | {url} | `{file}` |".format(
                rank=row["video_rank"],
                title=escape_table(row["title"]),
                url=row["url"],
                file=row["local_transcript_file"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_other_materials(prospects, linkedin_rows, youtube_rows):
    write_csv(OTHER_DIR / "selected-experts.csv", [prospects[expert] for expert in EXPERT_ORDER])
    write_csv(OTHER_DIR / "linkedin-posts-manifest.csv", linkedin_rows)
    write_csv(OTHER_DIR / "youtube-videos-manifest.csv", youtube_rows)

    lines = [
        "# Brand Voice Audit",
        "",
        "Purpose: separate real personal/operator brands from people who merely appear in search results.",
        "",
        "| Expert | Verdict | Reason |",
        "|---|---|---|",
    ]
    for expert in EXPERT_ORDER:
        tier, reason = BRAND_TIERS[expert]
        lines.append(f"| {expert} | {escape_table(tier)} | {escape_table(reason)} |")
    lines.extend(
        [
            "",
            "Best primary voices for a later cold-outbound playbook: Sam McKenna, Armand Farrokh, Jason Bay, John Barrows, and Morgan J Ingram.",
            "",
            "Useful secondary/operator sources: Richard Harris, Marcus Chan, Collin Stewart, Kyle Vamvouris, and Alex Berman.",
        ]
    )
    (OTHER_DIR / "brand-voice-audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    methodology = [
        "# Methodology",
        "",
        "1. Started with the topic: B2B SaaS cold outbound.",
        "2. Filtered for practitioners who teach publicly and have business/operator proof.",
        "3. Collected 7 recent YouTube videos/transcripts per expert.",
        "4. Collected 15 recent public LinkedIn posts per expert.",
        "5. Organized all source material by expert so a cold-outbound playbook can be built from patterns, not generic advice.",
        "",
        "API/tooling notes:",
        "- YouTube transcripts: Apify YouTube transcript actor.",
        "- LinkedIn posts: Apify LinkedIn profile-posts actor.",
        "- LinkedIn profile correction/search: Apify LinkedIn profile search actor.",
    ]
    (OTHER_DIR / "methodology.md").write_text("\n".join(methodology) + "\n", encoding="utf-8")


def write_readme():
    readme = [
        "# 100xHireproject",
        "",
        "## B2B SaaS Cold Outbound Research Project",
        "",
        "This repository now includes a source-backed research project for building a future B2B SaaS cold-outbound playbook.",
        "",
        "Topic: B2B SaaS cold outbound across cold email, cold calling, LinkedIn/social selling, SDR/BDR pipeline creation, and outbound sales leadership.",
        "",
        "What was collected:",
        "- 10 practitioner-experts selected for real operator proof, not just search visibility.",
        "- 150 recent LinkedIn posts, organized by author.",
        "- 70 recent YouTube transcripts, organized by expert and video.",
        "- Source notes, methodology, and a brand-voice audit.",
        "",
        "Research structure:",
        "- `research/sources.md` - expert list, source links, collection notes, and why each person was selected.",
        "- `research/linkedin-posts/` - latest LinkedIn posts organized by author, with per-author CSV/JSON/Markdown files.",
        "- `research/youtube-transcripts/` - recent YouTube transcripts organized by expert and video.",
        "- `research/other/` - methodology, manifests, selected-expert CSV, and brand-voice audit.",
        "",
        "Chosen experts:",
        "1. Jason Bay",
        "2. Armand Farrokh",
        "3. John Barrows",
        "4. Sam McKenna",
        "5. Morgan J Ingram",
        "6. Alex Berman",
        "7. Collin Stewart",
        "8. Kyle Vamvouris",
        "9. Richard Harris",
        "10. Marcus Chan",
        "",
        "Why these experts:",
        "- The strongest primary voices are Sam McKenna, Armand Farrokh, Jason Bay, John Barrows, and Morgan J Ingram because their recent content has a clear, repeatable point of view on cold outbound.",
        "- The secondary operator sources add useful material from sales training, outbound agencies, and B2B sales consulting firms.",
        "- Each selected expert has public teaching content plus evidence that they practice or operate in the area they teach.",
    ]
    Path("README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def count_by(rows, key):
    counts = defaultdict(int)
    for row in rows:
        counts[row[key]] += 1
    return counts


def post_id_from_url(url):
    match = re.search(r"activity-(\d+)", url or "")
    return match.group(1) if match else url


def normalize_space(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value):
    return (
        str(value)
        .lower()
        .replace("&", "and")
        .replace("#", "")
        .replace("'", "")
        .replace(".", "")
        .replace("/", "-")
        .replace("\\", "-")
        .replace(" ", "-")
    )


def safe_filename(value):
    value = re.sub(r'[<>:"/\\|?*]', "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:180]


def escape_table(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
