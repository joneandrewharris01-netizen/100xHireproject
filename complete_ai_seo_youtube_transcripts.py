"""Complete AI SEO YouTube transcripts using captions first, then local ASR.

Reads:
  research/other/ai-seo-youtube-complete-inventory.csv

Writes:
  research/youtube-transcripts/<expert-slug>/*.txt
  research/youtube-transcripts/<expert-slug>/videos.md
  research/other/ai-seo-youtube-complete-transcript-manifest.csv

For videos without YouTube captions, this downloads audio and transcribes with
faster-whisper on CPU. The ASR transcript is marked in metadata.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
YTDEPS = ROOT / ".tmp_tools" / "ytdeps"
ASRDEPS = ROOT / ".tmp_tools" / "asrdeps"
for dep in (YTDEPS, ASRDEPS):
    if dep.exists():
        sys.path.insert(0, str(dep))

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi


INVENTORY = ROOT / "research" / "other" / "ai-seo-youtube-complete-inventory.csv"
MANIFEST = ROOT / "research" / "other" / "ai-seo-youtube-complete-transcript-manifest.csv"
OUT_ROOT = ROOT / "research" / "youtube-transcripts"
LANGS = ("en", "en-US", "en-GB")


def clean_filename(value: str, max_len: int = 90) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", value or "")
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


def out_path(row: dict[str, str]) -> Path:
    return OUT_ROOT / row["slug"] / f"{row['video_id']} - {clean_filename(row['title'])}.txt"


def fetch_youtube_transcript_api(video_id: str) -> tuple[str | None, str]:
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


def ydl_video() -> yt_dlp.YoutubeDL:
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


def fetch_ytdlp_caption(video_id: str) -> tuple[str | None, str, dict[str, Any]]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    with ydl_video() as ydl:
        info = ydl.extract_info(url, download=False) or {}
    for source_name, source in (("manual", info.get("subtitles") or {}), ("auto", info.get("automatic_captions") or {})):
        for lang in LANGS:
            for item in source.get(lang) or []:
                if item.get("ext") == "vtt" and item.get("url"):
                    request = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(request, timeout=45) as response:
                        raw = response.read().decode("utf-8", errors="replace")
                    text = clean_vtt(raw)
                    if len(text) >= 20:
                        return text, f"yt_dlp_{source_name}_{lang}", info
    return None, "no_english_subtitle_url", info


def download_audio(video_id: str, tmpdir: Path) -> Path:
    outtmpl = str(tmpdir / "%(id)s.%(ext)s")
    options = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "socket_timeout": 30,
        "retries": 3,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "64",
            }
        ],
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    wav = tmpdir / f"{video_id}.wav"
    if not wav.exists():
        found = list(tmpdir.glob("*.wav"))
        if not found:
            raise RuntimeError("audio download did not produce wav")
        return found[0]
    return wav


_model = None


def transcribe_asr(video_id: str) -> str:
    global _model
    from faster_whisper import WhisperModel

    if _model is None:
        model_name = os.environ.get("WHISPER_MODEL", "tiny")
        _model = WhisperModel(model_name, device="cpu", compute_type="int8")
    with tempfile.TemporaryDirectory(prefix="ai-seo-asr-") as raw_tmp:
        tmpdir = Path(raw_tmp)
        audio_path = download_audio(video_id, tmpdir)
        segments, _info = _model.transcribe(str(audio_path), beam_size=1, vad_filter=True)
        parts = [segment.text.strip() for segment in segments if segment.text and segment.text.strip()]
    text = re.sub(r"\s+", " ", " ".join(parts)).strip()
    if len(text) < 20:
        raise RuntimeError("ASR produced empty transcript")
    return text


def write_transcript(row: dict[str, str], text: str, source: str) -> Path:
    path = out_path(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {
        "topic": "AI-powered SEO content production for B2B SaaS",
        "expert": row["expert"],
        "company": row["company"],
        "video_id": row["video_id"],
        "title": row["title"],
        "url": row["url"],
        "channel": row.get("channel", ""),
        "source_type": row.get("source_type", ""),
        "transcript_source": source,
    }
    path.write_text(
        "Metadata:\n"
        + json.dumps(header, ensure_ascii=False, indent=2)
        + "\n\nTranscript:\n"
        + text.strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def existing_path(row: dict[str, str]) -> Path | None:
    folder = OUT_ROOT / row["slug"]
    if not folder.exists():
        return None
    matches = list(folder.glob(f"{row['video_id']} - *.txt"))
    if matches:
        return matches[0]
    return None


def md_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def write_author_summaries(manifest: list[dict[str, Any]]) -> None:
    by_slug: dict[str, list[dict[str, Any]]] = {}
    for row in manifest:
        by_slug.setdefault(row["slug"], []).append(row)
    for slug, rows in by_slug.items():
        folder = OUT_ROOT / slug
        folder.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# YouTube Transcripts: {rows[0]['expert']}",
            "",
            f"Company/source: {rows[0]['company']}",
            "",
            "| Status | Source | Title | URL | Transcript file |",
            "|---|---|---|---|---|",
        ]
        for row in rows:
            lines.append(
                f"| {md_cell(row['status'])} | {md_cell(row['transcript_source'])} | {md_cell(row['title'])} | {md_cell(row['url'])} | {md_cell(row['transcript_file'])} |"
            )
        lines.append("")
        (folder / "videos.md").write_text("\n".join(lines), encoding="utf-8")


def load_inventory() -> list[dict[str, str]]:
    with INVENTORY.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def process_row(row: dict[str, str], use_asr: bool, force: bool, no_fetch: bool) -> dict[str, Any]:
    existing = existing_path(row)
    if existing and not force:
        chars = len(existing.read_text(encoding="utf-8", errors="replace"))
        return result_row(row, "existing", "existing_file", chars, existing, "")
    if no_fetch:
        return result_row(row, "pending", "", 0, None, "no local transcript file found")

    print(f"{row['expert']}: {row['title']}", flush=True)
    text, source = fetch_youtube_transcript_api(row["video_id"])
    error = ""
    if not text:
        try:
            text, source, _info = fetch_ytdlp_caption(row["video_id"])
        except Exception as exc:
            error = str(exc)[:240]
            text = None
            source = "yt_dlp_caption_failed"
    if not text and use_asr:
        try:
            text = transcribe_asr(row["video_id"])
            source = "faster_whisper_asr"
        except Exception as exc:
            error = str(exc)[:240]
            text = None
            source = "asr_failed"
    if text:
        path = write_transcript(row, text, source)
        return result_row(row, "ok", source, len(text), path, "")
    return result_row(row, "no_transcript", source, 0, None, error or source)


def result_row(
    row: dict[str, str],
    status: str,
    transcript_source: str,
    chars: int,
    path: Path | None,
    error: str,
) -> dict[str, Any]:
    return {
        "rank": row["rank"],
        "expert": row["expert"],
        "slug": row["slug"],
        "company": row["company"],
        "source_type": row["source_type"],
        "video_id": row["video_id"],
        "title": row["title"],
        "url": row["url"],
        "channel": row.get("channel", ""),
        "status": status,
        "transcript_source": transcript_source,
        "transcript_chars": chars,
        "transcript_file": str(path.relative_to(ROOT)) if path else "",
        "error": error,
    }


def write_manifest(rows: list[dict[str, Any]]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
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
        "status",
        "transcript_source",
        "transcript_chars",
        "transcript_file",
        "error",
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asr", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-new", type=int, default=0)
    parser.add_argument("--expert", action="append", default=[])
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--no-fetch", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_inventory()
    if args.expert:
        wanted = {item.lower() for item in args.expert}
        rows = [row for row in rows if row["expert"].lower() in wanted or row["slug"].lower() in wanted]

    manifest: list[dict[str, Any]] = []
    new_count = 0
    for row in rows:
        before = existing_path(row)
        result = process_row(row, use_asr=args.asr, force=args.force, no_fetch=args.no_fetch)
        manifest.append(result)
        after = result.get("status") == "ok" and (args.force or before is None)
        if after:
            new_count += 1
        if args.max_new and new_count >= args.max_new:
            for remaining in rows[len(manifest):]:
                existing = existing_path(remaining)
                if existing:
                    chars = len(existing.read_text(encoding="utf-8", errors="replace"))
                    manifest.append(result_row(remaining, "existing", "existing_file", chars, existing, ""))
                else:
                    manifest.append(result_row(remaining, "pending", "", 0, None, "max_new limit reached"))
            break
        if args.sleep:
            time.sleep(args.sleep)

    write_manifest(manifest)
    write_author_summaries(manifest)
    print(f"wrote {len(manifest)} rows to {MANIFEST}")


if __name__ == "__main__":
    main()
