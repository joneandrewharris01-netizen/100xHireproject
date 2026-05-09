"""Reddit fetchers + comment-tree walker.

Two implementations: UrllibFetcher (default, unauthenticated, cheap)
and PrawFetcher (fallback when rate-limited).
"""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Iterator, Protocol

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) jone-pe-intel/1.0"
MIN_COMMENT_LEN = 30
SKIP_AUTHORS = {None, "[deleted]", "[removed]", "AutoModerator"}


class RedditFetcher(Protocol):
    def fetch_listing(self, subreddit: str, listing: str,
                      limit: int = 100, t: str | None = None,
                      after: str | None = None) -> dict: ...

    def fetch_post_with_comments(self, post_id: str,
                                 subreddit: str) -> tuple[dict, list[dict]]: ...


class UrllibFetcher:
    def __init__(self, user_agent: str = USER_AGENT, sleep_s: float = 2.0):
        self.user_agent = user_agent
        self.sleep_s = sleep_s

    def _get(self, url: str) -> dict | list:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        time.sleep(self.sleep_s)
        return json.loads(data)

    def fetch_listing(self, subreddit, listing, limit=100, t=None, after=None):
        url = f"https://www.reddit.com/r/{subreddit}/{listing}.json?limit={limit}"
        if t:
            url += f"&t={t}"
        if after:
            url += f"&after={after}"
        return self._get(url)

    def fetch_post_with_comments(self, post_id, subreddit):
        url = (
            f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
            f"?limit=500&depth=10"
        )
        raw = self._get(url)
        post_data = raw[0]["data"]["children"][0]["data"]
        comments = list(walk_comments(raw[1], post_id=post_id))
        return post_data, comments


def walk_comments(comments_listing: dict, post_id: str,
                  parent_id: str | None = None, depth: int = 0
                  ) -> Iterator[dict]:
    """Recursively yield comment dicts ready for db.insert_comment.

    Skips AutoModerator, [deleted], and bodies <30 chars — but still recurses
    into the replies of skipped comments (children may be valid).
    Comment IDs are formatted as "t1_<id>" (Reddit's "fullname" convention).
    """
    children = comments_listing.get("data", {}).get("children", [])
    for child in children:
        kind = child.get("kind")
        if kind != "t1":  # skip "more" placeholders
            continue
        d = child.get("data", {})
        author = d.get("author")
        body = (d.get("body") or "").strip()
        if author in SKIP_AUTHORS or len(body) < MIN_COMMENT_LEN:
            # Skipped comments are never inserted. Don't point children at
            # them — pass through the current parent_id so children link to
            # a valid ancestor that exists in the DB. depth still increments
            # to reflect true tree position.
            replies = d.get("replies")
            if isinstance(replies, dict):
                yield from walk_comments(replies, post_id,
                                          parent_id=parent_id,
                                          depth=depth + 1)
            continue
        yield {
            "comment_id": f"t1_{d.get('id')}",
            "post_id": post_id,
            "parent_id": parent_id or d.get("parent_id"),
            "author": author,
            "body": body,
            "score": d.get("score", 0),
            "depth": depth,
            "created_utc": int(d.get("created_utc", 0)),
        }
        replies = d.get("replies")
        if isinstance(replies, dict):
            yield from walk_comments(replies, post_id,
                                      parent_id=f"t1_{d.get('id')}",
                                      depth=depth + 1)


# PrawFetcher stub — wired in but not required for v1 unit tests.
class PrawFetcher:
    """Authenticated fallback for when unauth requests get blocked.

    Lazy-imports praw so the default install doesn't need it.
    """
    def __init__(self, env_path: str = "agents/reddit_bot.env"):
        import os
        from pathlib import Path
        if Path(env_path).exists():
            for line in Path(env_path).read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
        import praw  # type: ignore
        self.reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent=os.environ.get("REDDIT_USER_AGENT", USER_AGENT),
        )

    def fetch_listing(self, subreddit, listing, limit=100, t=None, after=None):
        raise NotImplementedError("PrawFetcher v1: add when unauth blocks happen")

    def fetch_post_with_comments(self, post_id, subreddit):
        raise NotImplementedError("PrawFetcher v1: add when unauth blocks happen")
