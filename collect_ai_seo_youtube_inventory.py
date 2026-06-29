"""Build complete recent YouTube inventory for AI SEO experts.

This is the inventory pass only. It collects recent channel videos where a
credible official/company channel exists, and fills gaps with YouTube search
appearances for experts without a clean channel feed.
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
YTDEPS = ROOT / ".tmp_tools" / "ytdeps"
if YTDEPS.exists():
    sys.path.insert(0, str(YTDEPS))

import yt_dlp


OUT = ROOT / "research" / "other" / "ai-seo-youtube-complete-inventory.csv"
LIMIT = 7


@dataclass
class Expert:
    rank: int
    expert: str
    slug: str
    company: str
    channel_url: str
    search_queries: list[str]


EXPERTS = [
    Expert(1, "Tibo Maker", "tibo-maker-outrank", "Outrank / Revid AI / Feather", "", ["Tibo Maker Outrank", "Tibo Maker SEO SaaS"]),
    Expert(2, "John Rush", "john-rush-seobot", "SEObot / ListingBott / Unicorn Platform", "", ["John Rush SEObot", "John Rush SEO Bot"]),
    Expert(3, "Samanyou Garg", "samanyou-garg-writesonic", "Writesonic", "https://www.youtube.com/channel/UCrE83mimEwjAELfoby63ScQ/videos", ["Samanyou Garg Writesonic AI search"]),
    Expert(4, "Jacky Chou", "jacky-chou-indexsy", "Indexsy / Trackings / LocalRank", "https://www.youtube.com/@Indexsy/videos", ["Jacky Chou AI SEO", "Jacky Chou Indexsy SEO"]),
    Expert(5, "Ross Hudgens", "ross-hudgens-siege-media", "Siege Media", "https://www.youtube.com/@SiegeMedia/videos", ["Ross Hudgens Siege Media GEO"]),
    Expert(6, "Ross Simmonds", "ross-simmonds-foundation", "Foundation Marketing", "", ["Ross Simmonds AI SEO", "Ross Simmonds Foundation Marketing GEO", "Ross Simmonds content distribution AI"]),
    Expert(7, "Bernard Huang", "bernard-huang-clearscope", "Clearscope", "https://www.youtube.com/@Clearscope/videos", ["Bernard Huang Clearscope AEO"]),
    Expert(8, "Tim Soulo", "tim-soulo-ahrefs", "Ahrefs", "https://www.youtube.com/@AhrefsCom/videos", ["Tim Soulo Ahrefs AI SEO"]),
    Expert(9, "Gael Breton", "gael-breton-authority-hacker", "Authority Hacker", "https://www.youtube.com/channel/UCTvgSAxisCh58hjzlMdED0A/videos", ["Gael Breton Authority Hacker AI SEO"]),
    Expert(10, "Bhanu Teja P", "bhanu-teja-sitegpt", "SiteGPT / Feather", "", ["Bhanu Teja SiteGPT", "Bhanu Teja free tools SEO"]),
]


def clean_text(value: Any) -> str:
    value = str(value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def ydl() -> yt_dlp.YoutubeDL:
    return yt_dlp.YoutubeDL(
        {
            "extract_flat": "in_playlist",
            "playlistend": LIMIT,
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "socket_timeout": 30,
            "retries": 3,
        }
    )


def rows_from_url(expert: Expert, url: str, source_type: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with ydl() as y:
        info = y.extract_info(url, download=False) or {}
    for entry in info.get("entries") or []:
        if not entry:
            continue
        video_id = entry.get("id")
        if not video_id or len(video_id) != 11:
            continue
        rows.append(
            {
                "rank": expert.rank,
                "expert": expert.expert,
                "slug": expert.slug,
                "company": expert.company,
                "source_type": source_type,
                "video_id": video_id,
                "title": clean_text(entry.get("title") or video_id),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "channel": clean_text(entry.get("channel") or ""),
                "channel_url": clean_text(entry.get("channel_url") or ""),
                "duration": entry.get("duration") or "",
                "upload_date": entry.get("upload_date") or "",
            }
        )
    return rows


def collect() -> list[dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
    for expert in EXPERTS:
        seen: set[str] = set()
        if expert.channel_url:
            try:
                for row in rows_from_url(expert, expert.channel_url, "official_or_company_channel"):
                    if row["video_id"] not in seen:
                        all_rows.append(row)
                        seen.add(row["video_id"])
                    if len(seen) >= LIMIT:
                        break
            except Exception as exc:
                print(f"channel failed: {expert.expert}: {exc}", flush=True)
        for query in expert.search_queries:
            if len(seen) >= LIMIT:
                break
            try:
                for row in rows_from_url(expert, f"ytsearch{LIMIT}:{query}", "youtube_search_appearance"):
                    if row["video_id"] not in seen:
                        all_rows.append(row)
                        seen.add(row["video_id"])
                    if len(seen) >= LIMIT:
                        break
            except Exception as exc:
                print(f"search failed: {expert.expert}: {query}: {exc}", flush=True)
    return all_rows


def main() -> None:
    rows = collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "rank",
        "expert",
        "slug",
        "company",
        "source_type",
        "video_id",
        "title",
        "url",
        "channel",
        "channel_url",
        "duration",
        "upload_date",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
