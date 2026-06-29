"""Collect recent YouTube transcripts for AI SEO/content-production experts.

Outputs:
  research/youtube-transcripts/<expert-slug>/*.txt
  research/youtube-transcripts/<expert-slug>/videos.md
  research/other/ai-seo-youtube-videos-manifest.csv
  research/other/ai-seo-youtube-channel-inventory.csv

The script uses free methods: yt-dlp for channel/video metadata and
youtube-transcript-api or YouTube caption URLs for transcript text.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
YTDEPS = ROOT / ".tmp_tools" / "ytdeps"
if YTDEPS.exists():
    sys.path.insert(0, str(YTDEPS))

try:
    import yt_dlp
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "yt_dlp is required. Install with: python -m pip install --target .tmp_tools\\ytdeps yt-dlp"
    ) from exc

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except Exception:
    YouTubeTranscriptApi = None


OUT_ROOT = ROOT / "research" / "youtube-transcripts"
OTHER_DIR = ROOT / "research" / "other"
MANIFEST_CSV = OTHER_DIR / "ai-seo-youtube-videos-manifest.csv"
INVENTORY_CSV = OTHER_DIR / "ai-seo-youtube-channel-inventory.csv"
LANGS = ("en", "en-US", "en-GB")


CHANNELS = [
    {
        "expert": "Tim Soulo",
        "slug": "tim-soulo-ahrefs",
        "company": "Ahrefs",
        "channel_name": "Ahrefs",
        "channel_url": "https://www.youtube.com/@AhrefsCom/videos",
    },
    {
        "expert": "Gael Breton",
        "slug": "gael-breton-authority-hacker",
        "company": "Authority Hacker",
        "channel_name": "Authority Hacker Podcast",
        "channel_url": "https://www.youtube.com/channel/UCTvgSAxisCh58hjzlMdED0A/videos",
    },
    {
        "expert": "Samanyou Garg",
        "slug": "samanyou-garg-writesonic",
        "company": "Writesonic",
        "channel_name": "Writesonic",
        "channel_url": "https://www.youtube.com/channel/UCrE83mimEwjAELfoby63ScQ/videos",
    },
    {
        "expert": "Bernard Huang",
        "slug": "bernard-huang-clearscope",
        "company": "Clearscope",
        "channel_name": "Clearscope",
        "channel_url": "https://www.youtube.com/@Clearscope/videos",
    },
    {
        "expert": "Ross Hudgens",
        "slug": "ross-hudgens-siege-media",
        "company": "Siege Media",
        "channel_name": "Siege Media",
        "channel_url": "https://www.youtube.com/@SiegeMedia/videos",
    },
    {
        "expert": "Jacky Chou",
        "slug": "jacky-chou-indexsy",
        "company": "Indexsy / Trackings / LocalRank",
        "channel_name": "Indexsy",
        "channel_url": "https://www.youtube.com/@Indexsy/videos",
    },
]


EXTRA_YOUTUBE_VIDEOS = [
    {
        "expert": "Ross Simmonds",
        "slug": "ross-simmonds-foundation",
        "company": "Foundation Marketing",
        "channel_name": "Writesonic",
        "video_id": "du26Ywa-CtA",
        "title": "What Still Works? Content, Search, and Distribution in the AI Era",
        "url": "https://www.youtube.com/watch?v=du26Ywa-CtA",
        "source_type": "youtube_appearance",
    },
    {
        "expert": "Ross Simmonds",
        "slug": "ross-simmonds-foundation",
        "company": "Foundation Marketing",
        "channel_name": "Ross Simmonds",
        "video_id": "axTH6nKDUY4",
        "title": "Ross Simmonds keynote demo reel: Content, SEO and AI",
        "url": "https://www.youtube.com/watch?v=axTH6nKDUY4",
        "source_type": "youtube_appearance",
    },
    {
        "expert": "Ross Simmonds",
        "slug": "ross-simmonds-foundation",
        "company": "Foundation Marketing",
        "channel_name": "Clearscope",
        "video_id": "ZvZxuoLQr9U",
        "title": "Content Growth Framework by Ross Simmonds of Foundation Marketing",
        "url": "https://www.youtube.com/watch?v=ZvZxuoLQr9U",
        "source_type": "youtube_appearance",
    },
    {
        "expert": "Samanyou Garg",
        "slug": "samanyou-garg-writesonic",
        "company": "Writesonic",
        "channel_name": "Writesonic",
        "video_id": "du26Ywa-CtA",
        "title": "What Still Works? Content, Search, and Distribution in the AI Era",
        "url": "https://www.youtube.com/watch?v=du26Ywa-CtA",
        "source_type": "youtube_appearance",
    },
]


LOCAL_TRANSCRIPTS = [
    {
        "expert": "Tibo Maker",
        "slug": "tibo-maker-outrank",
        "company": "Outrank / Revid AI / Feather",
        "channel_name": "Starter Story",
        "video_id": "xeUhKuJbeWQ",
        "title": "Tibo Maker on Outrank and his SaaS portfolio",
        "url": "https://www.youtube.com/watch?v=xeUhKuJbeWQ",
        "source_path": ROOT / "app_ideas" / "research" / "transcripts" / "xeUhKuJbeWQ.txt",
    },
    {
        "expert": "John Rush",
        "slug": "john-rush-seobot",
        "company": "SEObot / ListingBott / Unicorn Platform",
        "channel_name": "Starter Story",
        "video_id": "En34iY-rQc0",
        "title": "John Rush on SEObot and his product portfolio",
        "url": "https://www.youtube.com/watch?v=En34iY-rQc0",
        "source_path": ROOT / "app_ideas" / "research" / "transcripts" / "En34iY-rQc0.txt",
    },
    {
        "expert": "Bhanu Teja P",
        "slug": "bhanu-teja-sitegpt",
        "company": "SiteGPT / Feather",
        "channel_name": "Starter Story",
        "video_id": "Adl5_lJfkEE",
        "title": "Bhanu Teja P on SiteGPT and free-tools SEO",
        "url": "https://www.youtube.com/watch?v=Adl5_lJfkEE",
        "source_path": ROOT / "app_ideas" / "research" / "transcripts" / "Adl5_lJfkEE.txt",
    },
]


@dataclass
class VideoRow:
    expert: str
    slug: str
    company: str
    channel_name: str
    channel_url: str
    video_id: str
    title: str
    url: str
    source_type: str = "channel_recent"
    duration: Any = ""
    upload_date: str = ""


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def clean_filename(value: str, max_len: int = 90) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return (value[:max_len].strip() or "untitled")


def clean_vtt(raw_text: str) -> str:
    lines: list[str] = []
    previous = ""
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if "-->" in line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line and line != previous:
            lines.append(line)
            previous = line
    return "\n".join(lines)


def ydl_for_flat(limit: int) -> yt_dlp.YoutubeDL:
    return yt_dlp.YoutubeDL(
        {
            "extract_flat": "in_playlist",
            "playlistend": limit,
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "socket_timeout": 30,
            "retries": 3,
        }
    )


def ydl_for_video() -> yt_dlp.YoutubeDL:
    return yt_dlp.YoutubeDL(
        {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "socket_timeout": 30,
            "retries": 3,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": list(LANGS),
            "subtitlesformat": "vtt",
        }
    )


def inventory_channels(limit_per_channel: int) -> list[VideoRow]:
    rows: list[VideoRow] = []
    seen: set[str] = set()
    for channel in CHANNELS:
        print(f"Inventory: {channel['expert']} -> {channel['channel_url']}", flush=True)
        try:
            with ydl_for_flat(limit_per_channel) as ydl:
                info = ydl.extract_info(channel["channel_url"], download=False) or {}
        except Exception as exc:
            print(f"  inventory failed: {exc}", flush=True)
            continue
        for entry in info.get("entries") or []:
            if not entry:
                continue
            video_id = entry.get("id")
            if not video_id or len(video_id) != 11 or video_id in seen:
                continue
            rows.append(
                VideoRow(
                    expert=channel["expert"],
                    slug=channel["slug"],
                    company=channel["company"],
                    channel_name=channel["channel_name"],
                    channel_url=channel["channel_url"],
                    video_id=video_id,
                    title=entry.get("title") or video_id,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    duration=entry.get("duration") or "",
                    upload_date=entry.get("upload_date") or "",
                )
            )
            seen.add(video_id)
    return rows


def extra_youtube_rows() -> list[VideoRow]:
    return [
        VideoRow(
            expert=row["expert"],
            slug=row["slug"],
            company=row["company"],
            channel_name=row["channel_name"],
            channel_url="",
            video_id=row["video_id"],
            title=row["title"],
            url=row["url"],
            source_type=row["source_type"],
        )
        for row in EXTRA_YOUTUBE_VIDEOS
    ]


def write_inventory(rows: list[VideoRow]) -> None:
    OTHER_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "expert",
        "slug",
        "company",
        "channel_name",
        "channel_url",
        "video_id",
        "title",
        "url",
        "source_type",
        "duration",
        "upload_date",
    ]
    with INVENTORY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def fetch_with_youtube_transcript_api(video_id: str) -> tuple[str | None, str]:
    if YouTubeTranscriptApi is None:
        return None, "youtube_transcript_api_not_installed"
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=list(LANGS))
        text = " ".join(snippet.text for snippet in transcript)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 20:
            return None, "empty_youtube_transcript_api"
        return text, "youtube_transcript_api"
    except Exception as exc:
        return None, f"youtube_transcript_api_failed: {str(exc)[:180]}"


def pick_subtitle_url(info: dict[str, Any]) -> tuple[str | None, str]:
    subtitles = info.get("subtitles") or {}
    auto_subtitles = info.get("automatic_captions") or {}
    for source_name, source in (("manual", subtitles), ("auto", auto_subtitles)):
        for lang in LANGS:
            formats = source.get(lang) or []
            for item in formats:
                if item.get("ext") == "vtt" and item.get("url"):
                    return item["url"], f"yt_dlp_{source_name}_{lang}"
    return None, "no_english_subtitle_url"


def fetch_with_ytdlp(video_id: str) -> tuple[str | None, str, dict[str, Any]]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    with ydl_for_video() as ydl:
        info = ydl.extract_info(url, download=False) or {}
    sub_url, source = pick_subtitle_url(info)
    if not sub_url:
        return None, source, info
    request = urllib.request.Request(sub_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read().decode("utf-8", errors="replace")
    text = clean_vtt(raw)
    if len(text) < 20:
        return None, "empty_yt_dlp_subtitle", info
    return text, source, info


def transcript_path_for(row: VideoRow) -> Path:
    folder = OUT_ROOT / row.slug
    title_part = clean_filename(row.title)
    return folder / f"{row.video_id} - {title_part}.txt"


def write_transcript_file(row: VideoRow, path: Path, text: str, caption_source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {
        "topic": "AI-powered SEO content production for B2B SaaS",
        "expert": row.expert,
        "company": row.company,
        "channel_name": row.channel_name,
        "video_id": row.video_id,
        "title": row.title,
        "url": row.url,
        "source_type": row.source_type,
        "upload_date": row.upload_date,
        "duration": row.duration,
        "caption_source": caption_source,
    }
    path.write_text(
        "Metadata:\n"
        + json.dumps(header, ensure_ascii=False, indent=2)
        + "\n\nTranscript:\n"
        + text.strip()
        + "\n",
        encoding="utf-8",
    )


def collect_youtube_row(row: VideoRow, force: bool) -> dict[str, Any]:
    output_path = transcript_path_for(row)
    if output_path.exists() and not force:
        text_len = len(output_path.read_text(encoding="utf-8", errors="replace"))
        return manifest_row(row, "existing", "existing_file", text_len, output_path, "")

    print(f"Transcript: {row.expert} | {row.title}", flush=True)
    text, caption_source = fetch_with_youtube_transcript_api(row.video_id)
    error = ""
    metadata: dict[str, Any] = {}
    if text is None:
        try:
            text, caption_source, metadata = fetch_with_ytdlp(row.video_id)
        except Exception as exc:
            error = str(exc)[:300]
            text = None
            if caption_source.startswith("youtube_transcript_api_failed"):
                error = f"{caption_source}; yt_dlp_failed: {error}"
            caption_source = "failed"

    if text:
        if metadata.get("title"):
            row.title = metadata["title"]
            output_path = transcript_path_for(row)
        row.upload_date = metadata.get("upload_date") or row.upload_date
        row.duration = metadata.get("duration") or row.duration
        write_transcript_file(row, output_path, text, caption_source)
        return manifest_row(row, "ok", caption_source, len(text), output_path, "")

    return manifest_row(row, "no_transcript", caption_source, 0, None, error or caption_source)


def collect_local_transcript(row: dict[str, Any], force: bool) -> dict[str, Any]:
    video = VideoRow(
        expert=row["expert"],
        slug=row["slug"],
        company=row["company"],
        channel_name=row["channel_name"],
        channel_url="",
        video_id=row["video_id"],
        title=row["title"],
        url=row["url"],
        source_type="local_starter_story_transcript",
    )
    output_path = transcript_path_for(video)
    source_path = row["source_path"]
    if output_path.exists() and not force:
        text_len = len(output_path.read_text(encoding="utf-8", errors="replace"))
        return manifest_row(video, "existing", "local_existing_file", text_len, output_path, "")
    if not source_path.exists():
        return manifest_row(video, "missing_local_source", "local_file", 0, None, str(source_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, output_path)
    text_len = len(output_path.read_text(encoding="utf-8", errors="replace"))
    return manifest_row(video, "ok", "local_starter_story_transcript", text_len, output_path, "")


def manifest_row(
    row: VideoRow,
    status: str,
    caption_source: str,
    transcript_chars: int,
    transcript_file: Path | None,
    error: str,
) -> dict[str, Any]:
    return {
        "expert": row.expert,
        "slug": row.slug,
        "company": row.company,
        "channel_name": row.channel_name,
        "video_id": row.video_id,
        "title": row.title,
        "url": row.url,
        "source_type": row.source_type,
        "status": status,
        "caption_source": caption_source,
        "transcript_chars": transcript_chars,
        "transcript_file": str(transcript_file.relative_to(ROOT)) if transcript_file else "",
        "upload_date": row.upload_date,
        "duration": row.duration,
        "error": error,
    }


def write_manifest(rows: list[dict[str, Any]]) -> None:
    OTHER_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "expert",
        "slug",
        "company",
        "channel_name",
        "video_id",
        "title",
        "url",
        "source_type",
        "status",
        "caption_source",
        "transcript_chars",
        "transcript_file",
        "upload_date",
        "duration",
        "error",
    ]
    with MANIFEST_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def md_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def write_author_summaries(rows: list[dict[str, Any]]) -> None:
    by_slug: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_slug.setdefault(row["slug"], []).append(row)
    for slug, slug_rows in by_slug.items():
        folder = OUT_ROOT / slug
        folder.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# YouTube Transcripts: {slug_rows[0]['expert']}",
            "",
            f"Company/source: {slug_rows[0]['company']}",
            "",
            "| Status | Title | URL | Transcript file |",
            "|---|---|---|---|",
        ]
        for row in slug_rows:
            lines.append(
                f"| {md_cell(row['status'])} | {md_cell(row['title'])} | {md_cell(row['url'])} | {md_cell(row['transcript_file'])} |"
            )
        lines.append("")
        (folder / "videos.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-per-channel", type=int, default=5)
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.35)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows = inventory_channels(args.limit_per_channel)
    rows.extend(extra_youtube_rows())
    write_inventory(rows)
    print(f"Inventory written: {INVENTORY_CSV} ({len(rows)} rows)", flush=True)
    if args.inventory_only:
        return

    manifest: list[dict[str, Any]] = []
    for row in rows:
        manifest.append(collect_youtube_row(row, force=args.force))
        if args.sleep:
            time.sleep(args.sleep)
    for row in LOCAL_TRANSCRIPTS:
        manifest.append(collect_local_transcript(row, force=args.force))
    write_manifest(manifest)
    write_author_summaries(manifest)
    print(f"Manifest written: {MANIFEST_CSV}", flush=True)


if __name__ == "__main__":
    main()
