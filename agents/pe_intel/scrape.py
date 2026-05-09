"""Scrape orchestrator. Pure glue: fetcher → walker → db.

No domain logic. No LLM calls. Idempotent — re-runs are cheap and safe.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path

from . import db, fetchers

SUBREDDITS = [
    "privateequity",
    "private_equity",
    "investmentbanking",
    "FinancialCareers",
    "SecurityAnalysis",
]

DEFAULT_LISTINGS: list[tuple[str, str | None]] = [
    ("new", None),
    ("top", "month"),
]

LOG_DIR = Path(__file__).parent / "logs"


def _setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"scrape_{datetime.now():%Y-%m-%d}.log"
    logger = logging.getLogger("pe_intel.scrape")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        h = logging.FileHandler(log_file, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(h)
    return logger


def scrape_subreddit(
    conn,
    subreddit: str,
    fetcher: fetchers.RedditFetcher,
    listings: list[tuple[str, str | None]] = DEFAULT_LISTINGS,
    max_posts_per_listing: int = 100,
) -> dict:
    """Scrape one subreddit. Returns {posts_seen, posts_fetched, comments_added}."""
    log = _setup_logging()
    stats = {"posts_seen": 0, "posts_fetched": 0, "comments_added": 0, "errors": 0}

    for listing, t in listings:
        try:
            data = fetcher.fetch_listing(subreddit, listing,
                                          limit=max_posts_per_listing, t=t)
        except Exception as e:
            log.error(f"listing fetch failed r/{subreddit} {listing}: {e}")
            stats["errors"] += 1
            continue

        children = data.get("data", {}).get("children", [])
        for child in children:
            d = child.get("data", {})
            post_id = d.get("id")
            if not post_id:
                continue
            stats["posts_seen"] += 1

            # Refresh listing-level metadata (does NOT bump last_updated)
            db.upsert_post_metadata(conn, {
                "post_id": post_id,
                "subreddit": d.get("subreddit", subreddit),
                "author": d.get("author"),
                "title": (d.get("title") or "").strip(),
                "selftext": (d.get("selftext") or "").strip(),
                "flair": d.get("link_flair_text") or "",
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "created_utc": int(d.get("created_utc", 0)),
                "permalink": f"https://reddit.com{d.get('permalink', '')}",
            })

            if not db.post_needs_rescrape(conn, post_id):
                continue

            # Pull full comment tree (the expensive call)
            try:
                _, comments = fetcher.fetch_post_with_comments(post_id, subreddit)
            except Exception as e:
                log.error(f"comments fetch failed {post_id}: {e}")
                stats["errors"] += 1
                continue

            for c in comments:
                db.insert_comment(conn, c)
                stats["comments_added"] += 1
            # Only NOW bump last_updated — comments fetch succeeded
            db.mark_post_rescraped(conn, post_id)
            stats["posts_fetched"] += 1

    log.info(f"r/{subreddit} stats={stats}")
    return stats


def main() -> int:
    """CLI entry: scrape all configured subreddits."""
    conn = db.connect()
    db.init_schema(conn)
    fetcher = fetchers.UrllibFetcher()
    totals = {"posts_seen": 0, "posts_fetched": 0, "comments_added": 0, "errors": 0}
    for sub in SUBREDDITS:
        s = scrape_subreddit(conn, sub, fetcher)
        for k in totals:
            totals[k] += s[k]
    print(f"DONE: {totals}")
    error_rate = totals["errors"] / max(totals["posts_seen"], 1)
    if error_rate > 0.05:
        print(f"WARN: error rate {error_rate:.1%} > 5% — check logs")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
