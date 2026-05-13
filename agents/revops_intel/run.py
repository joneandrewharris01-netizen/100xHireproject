"""Chain runner for the standalone RevOps Intel pipeline.

Refresh data, then loop hot leads through extract + generate, write queue
files, mark processed. No interactive Claude Code session required.

Usage:
    python -m agents.revops_intel.run [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from agents.revops_intel import db, kb_backups, kb_merge, llm_extract, llm_generate
from agents.revops_intel.llm_client import LLMError
from agents.revops_intel.llm_generate import QualityFlag
from agents.revops_intel import queue_writer


PY = sys.executable
_LOG_DIR = Path(__file__).parent / "logs"
_FAILED_LOG = _LOG_DIR / "failed_leads.jsonl"
_ZERO_STREAK = _LOG_DIR / "zero_lead_streak.txt"

_KB_PATH = Path(__file__).parent / "knowledge_base"
DEFAULT_OFFER_KEY = "general_automation"


def _log_failure(lead: dict, exc: Exception, tb: bool = False) -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lead_id": lead.get("post_id", "?"),
        "stage": "run",
        "error": str(exc)[:500],
    }
    if tb:
        entry["traceback"] = traceback.format_exc()[:2000]
    with _FAILED_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _bump_zero_streak() -> int:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    cur = 0
    if _ZERO_STREAK.exists():
        try:
            cur = int(_ZERO_STREAK.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            cur = 0
    cur += 1
    _ZERO_STREAK.write_text(str(cur), encoding="utf-8")
    return cur


def _reset_zero_streak() -> None:
    if _ZERO_STREAK.exists():
        _ZERO_STREAK.write_text("0", encoding="utf-8")


def main(limit: int = 20, dry_run: bool = False) -> int:
    print(f"[run] starting (limit={limit}, dry_run={dry_run})")

    print("[run] snapshotting KB backups")
    kb_backups.snapshot()

    print("[run] refreshing data (scrape -> score -> route)")
    for stage in ("scrape", "score", "route"):
        result = subprocess.run(
            [PY, "-m", f"agents.revops_intel.{stage}"],
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        if result.returncode != 0:
            print(f"[run] FATAL: {stage} exited with {result.returncode}")
            return 1

    conn = db.connect()
    try:
        db.init_schema(conn)  # idempotent — safe on first run with empty DB
        hot = db.fetch_hot_unprocessed(conn, limit=limit)

        if not hot:
            streak = _bump_zero_streak()
            print(f"[run] no hot leads (streak: {streak} days)")
            if streak >= 3:
                print(f"[run] WARNING: zero-lead streak hit {streak} days; check upstream scoring")
            return 0
        _reset_zero_streak()

        offers = json.loads((_KB_PATH / "offers.json").read_text(encoding="utf-8"))
        if DEFAULT_OFFER_KEY not in offers:
            print(f"[run] FATAL: offers.json missing required key '{DEFAULT_OFFER_KEY}'")
            return 1
        stats = {"processed": 0, "flagged": 0, "failed": 0,
                 "kb_diffs": Counter()}

        for i, lead in enumerate(hot, start=1):
            print(f"[run] {i}/{len(hot)} processing {lead['post_id']} ({lead.get('subreddit')})")
            kb_diff: dict = {}
            comments: list[dict] = []
            try:
                comments = db.fetch_top_comments(conn, lead["post_id"], limit=10)
                kb_diff = llm_extract.extract(lead, comments)
                if kb_diff and not dry_run:
                    kb_merge.merge_atomic(kb_diff)
                    for k in ("tools", "pains", "personas", "jargon"):
                        stats["kb_diffs"][k] += len(kb_diff.get(k) or {})

                offer_pitch = offers.get(
                    lead.get("offer_match"), offers[DEFAULT_OFFER_KEY],
                )
                comment, dm = llm_generate.generate(lead, comments, offer_pitch)

                if not dry_run:
                    queue_file = queue_writer.write(
                        lead, comments, comment, dm, kb_diff, flagged=False,
                    )
                    db.mark_processed(
                        conn, lead["post_id"], queue_file, lead.get("offer_match"),
                    )
                stats["processed"] += 1
            except QualityFlag as qf:
                if not dry_run:
                    queue_file = queue_writer.write(
                        lead, comments, qf.comment, qf.dm, kb_diff, flagged=True,
                    )
                    db.mark_processed(
                        conn, lead["post_id"], queue_file, lead.get("offer_match"),
                    )
                stats["flagged"] += 1
                print(f"[run]   FLAGGED: {qf.reason}")
            except LLMError as e:
                _log_failure(lead, e)
                stats["failed"] += 1
                print(f"[run]   FAILED (LLM): {e}")
            except Exception as e:
                _log_failure(lead, e, tb=True)
                stats["failed"] += 1
                print(f"[run]   FAILED (unexpected): {e}")

            time.sleep(2.1)

        print("\n[run] summary:")
        print(f"  processed: {stats['processed']}")
        print(f"  flagged:   {stats['flagged']}")
        print(f"  failed:    {stats['failed']}")
        print(f"  KB diffs:  {dict(stats['kb_diffs'])}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    sys.exit(main(limit=args.limit, dry_run=args.dry_run))
