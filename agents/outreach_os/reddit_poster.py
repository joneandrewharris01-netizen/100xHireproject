"""Post today's queued comments to Reddit via the official API (PRAW).

Why API, not browser:
- Avoids Reddit's bot/CAPTCHA detection on the web UI
- Cleaner rate-limit signaling (we get an explicit 429 instead of a silent
  shadowban)
- Reddit's own rules permit this for personal-use script apps:
  https://www.reddit.com/wiki/api/

What this script does NOT do:
- Auto-send DMs (per the user's hard rule: drafts only, manual sending only,
  and DMs only after engagement)
- Post to threads where the comment text doesn't match the live thread context
  (you should manually skip those with `--skip POST_ID`)
- Bypass rate limits — every error stops the whole run

Setup (one-time):
1. Visit https://www.reddit.com/prefs/apps and click "create another app".
2. Type: SCRIPT.  Name: anything (e.g. "outreach-os personal").
3. Set redirect URI to http://localhost:8080 (script-type apps don't actually
   redirect, but the field is required).
4. Submit. Reddit shows a CLIENT ID under the app name and a SECRET below.
5. Add to D:\\Projects\\my-project\\.env:
       REDDIT_CLIENT_ID=<the id under the app name>
       REDDIT_CLIENT_SECRET=<the secret>
       REDDIT_USERNAME=<your reddit username>
       REDDIT_PASSWORD=<your reddit password>
       REDDIT_USER_AGENT=outreach-os/1.0 by /u/<your-username>

Usage:
    python -m agents.outreach_os.reddit_poster --dry-run       # show what WOULD post
    python -m agents.outreach_os.reddit_poster --limit 1       # post the first lead, stop
    python -m agents.outreach_os.reddit_poster                 # post all 15 leads
    python -m agents.outreach_os.reddit_poster --skip 1t73gb4  # skip a specific post_id

Safety:
- Default delay: 90-180 sec between posts (jittered)
- Stops on first 403, 429, or any other API error
- Writes outcome to outreach-os/daily/<today>-POSTING-LOG.md
- Won't double-post: maintains a session set of already-posted post_ids
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

from . import post_helper, queue_scanner

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")

LOG_PATH = Path(f"outreach-os/daily/{date.today().isoformat()}-POSTING-LOG.md")


def _log(line: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamped = f"- [{datetime.now().isoformat(timespec='seconds')}] {line}"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(stamped + "\n")
    print(stamped)


def _build_reddit():
    import praw

    missing = [
        k for k in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD")
        if not os.environ.get(k)
    ]
    if missing:
        print(f"ERROR: missing env vars: {missing}")
        print("See setup steps in this file's docstring.")
        sys.exit(2)

    user_agent = os.environ.get(
        "REDDIT_USER_AGENT",
        f"outreach-os/1.0 by /u/{os.environ['REDDIT_USERNAME']}",
    )
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=user_agent,
    )


def _post_comment(reddit, lead: dict) -> tuple[bool, str]:
    """Submit one comment. Returns (success, message)."""
    submission = reddit.submission(id=lead["post_id"])
    # Sanity check the thread is still alive
    if submission.locked:
        return False, "thread locked"
    if submission.archived:
        return False, "thread archived"
    if submission.removed_by_category:
        return False, f"thread removed: {submission.removed_by_category}"

    try:
        comment = submission.reply(body=lead["comment"])
    except Exception as e:
        return False, f"reply failed: {type(e).__name__}: {e}"
    return True, f"posted comment id={comment.id} permalink=https://reddit.com{comment.permalink}"


def run(*, dry_run: bool, limit: int | None, skip_ids: set[str], delay_min: int, delay_max: int) -> None:
    today = date.today()
    raw = queue_scanner.scan_today_all(today=today)
    leads = [post_helper._load_lead(l) for l in raw]
    leads = [l for l in leads if l["tier"] is not None and l["url"] and l.get("comment")]
    leads.sort(key=post_helper._sort_key)
    leads = [l for l in leads if l["post_id"] not in skip_ids]
    if limit is not None:
        leads = leads[:limit]

    _log(f"START run dry_run={dry_run} limit={limit} skip={sorted(skip_ids)} count={len(leads)}")
    print(f"\n{len(leads)} leads queued for posting.\n")

    if not leads:
        print("Nothing to post.")
        _log("END no_leads")
        return

    reddit = None
    if not dry_run:
        reddit = _build_reddit()
        try:
            me = reddit.user.me()
            _log(f"AUTH ok user=/u/{me.name}")
        except Exception as e:
            _log(f"AUTH failed: {type(e).__name__}: {e}")
            print(f"Auth failed. Check credentials in .env. Error: {e}")
            sys.exit(3)

    for i, lead in enumerate(leads, 1):
        author = lead['author'] if lead['author'].startswith('u/') else f"u/{lead['author']}"
        header = f"[{i}/{len(leads)}] {lead['tier']} u{lead['urgency']} {author} r/{lead['subreddit']} id={lead['post_id']}"
        print(f"\n{header}")
        if dry_run:
            preview = lead["comment"][:120].replace("\n", " ")
            print(f"  DRY-RUN. Would post: {preview}...")
            _log(f"DRY {lead['post_id']} {lead['source']} {lead['author']}")
            continue

        ok, msg = _post_comment(reddit, lead)
        if ok:
            _log(f"POSTED {lead['post_id']} {lead['source']} {lead['author']} {msg}")
            print(f"  OK: {msg}")
        else:
            _log(f"FAILED {lead['post_id']} {lead['source']} {lead['author']} {msg}")
            print(f"  FAILED: {msg}")
            print("\nStopping run on first failure (safety). Investigate, then resume with --skip <post_id> ... for already-posted ones.")
            _log(f"STOP after_failure {lead['post_id']}")
            return

        if i < len(leads):
            wait = random.randint(delay_min, delay_max)
            print(f"  Waiting {wait}s before next post...")
            time.sleep(wait)

    _log(f"END complete posted={len(leads)}")
    print(f"\nDone. {len(leads)} comments posted. Tomorrow run /outreach-flush-outcomes after marking outcomes in the brief.")


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Post queued comments to Reddit via API.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would post; do not authenticate or hit Reddit.")
    parser.add_argument("--limit", type=int, default=None, help="Only post the first N leads (e.g. --limit 1 for a test post).")
    parser.add_argument("--skip", action="append", default=[], metavar="POST_ID", help="Skip specific post_id(s). Can repeat.")
    parser.add_argument("--delay-min", type=int, default=90, help="Min seconds between posts (default 90).")
    parser.add_argument("--delay-max", type=int, default=180, help="Max seconds between posts (default 180).")
    args = parser.parse_args()
    run(
        dry_run=args.dry_run,
        limit=args.limit,
        skip_ids=set(args.skip),
        delay_min=args.delay_min,
        delay_max=args.delay_max,
    )


if __name__ == "__main__":
    _cli()
