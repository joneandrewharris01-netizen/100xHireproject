"""Collect recent LinkedIn posts for AI SEO experts through Kimi WebBridge.

This script uses the local Kimi daemon at http://127.0.0.1:10086. It does not
handle login; it expects the user's browser session to already be logged in to
LinkedIn and the Kimi extension to be connected.
"""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUT_ROOT = ROOT / "research" / "linkedin-posts"
MANIFEST = OUT_ROOT / "ai-seo-linkedin-manifest.csv"
SESSION = "ai-seo-linkedin-collector"
KIMI_URL = "http://127.0.0.1:10086/command"


EXPERTS = [
    {
        "rank": 1,
        "expert": "Tibo Maker",
        "slug": "tibo-maker-outrank",
        "company": "Outrank / Revid AI / Feather",
        "search": "Tibo Louis Lucas Outrank",
    },
    {
        "rank": 2,
        "expert": "John Rush",
        "slug": "john-rush-seobot",
        "company": "SEObot / ListingBott / Unicorn Platform",
        "search": "John Rush SEObot",
        "profile_url": "https://www.linkedin.com/in/johnrushx/",
    },
    {
        "rank": 3,
        "expert": "Samanyou Garg",
        "slug": "samanyou-garg-writesonic",
        "company": "Writesonic",
        "search": "Samanyou Garg Writesonic",
        "profile_url": "https://www.linkedin.com/in/samanyougarg/",
    },
    {
        "rank": 4,
        "expert": "Jacky Chou",
        "slug": "jacky-chou-indexsy",
        "company": "Indexsy / Trackings / LocalRank",
        "search": "Jacky Chou Indexsy",
        "profile_url": "https://www.linkedin.com/in/jacky-chou/",
    },
    {
        "rank": 5,
        "expert": "Ross Hudgens",
        "slug": "ross-hudgens-siege-media",
        "company": "Siege Media",
        "search": "Ross Hudgens Siege Media",
        "profile_url": "https://www.linkedin.com/in/rosshudgens/",
    },
    {
        "rank": 6,
        "expert": "Ross Simmonds",
        "slug": "ross-simmonds-foundation",
        "company": "Foundation Marketing",
        "search": "Ross Simmonds Foundation Marketing",
        "profile_url": "https://www.linkedin.com/in/rosssimmonds/",
    },
    {
        "rank": 7,
        "expert": "Bernard Huang",
        "slug": "bernard-huang-clearscope",
        "company": "Clearscope",
        "search": "Bernard Huang Clearscope",
        "profile_url": "https://www.linkedin.com/in/bernardjhuang/",
    },
    {
        "rank": 8,
        "expert": "Tim Soulo",
        "slug": "tim-soulo-ahrefs",
        "company": "Ahrefs",
        "search": "Tim Soulo Ahrefs",
        "profile_url": "https://www.linkedin.com/in/timsoulo/",
    },
    {
        "rank": 9,
        "expert": "Gael Breton",
        "slug": "gael-breton-authority-hacker",
        "company": "Authority Hacker",
        "search": "Gael Breton Authority Hacker",
        "profile_url": "https://www.linkedin.com/in/gael-breton/",
    },
    {
        "rank": 10,
        "expert": "Bhanu Teja P",
        "slug": "bhanu-teja-sitegpt",
        "company": "SiteGPT / Feather",
        "search": "Bhanu Teja P SiteGPT",
        "profile_url": "https://www.linkedin.com/in/pbteja1998/",
    },
]


def kimi(action: str, args: dict[str, Any] | None = None, session: str = SESSION, timeout: int = 90) -> dict[str, Any]:
    payload = json.dumps({"action": action, "args": args or {}, "session": session}).encode("utf-8")
    request = urllib.request.Request(KIMI_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    if not data.get("ok"):
        raise RuntimeError(data.get("error", {}).get("message", raw))
    return data.get("data", {})


def safe_kimi(action: str, args: dict[str, Any] | None = None, session: str = SESSION, timeout: int = 90) -> dict[str, Any] | None:
    try:
        return kimi(action, args, session=session, timeout=timeout)
    except Exception:
        return None


def js_json(code: str, timeout: int = 90) -> Any:
    try:
        result = kimi("evaluate", {"code": code}, timeout=timeout)
    except Exception:
        claim_current_linkedin()
        result = kimi("evaluate", {"code": code}, timeout=timeout)
    value = result.get("value")
    if isinstance(value, str):
        return json.loads(value)
    return value


def claim_current_linkedin() -> None:
    safe_kimi("find_tab", {"url": "https://www.linkedin.com", "active": True}, timeout=15)


def navigate(url: str, sleep_seconds: float = 4.0) -> None:
    try:
        kimi("navigate", {"url": url, "newTab": False, "group_title": "AI SEO LinkedIn"}, timeout=45)
    except Exception:
        claim_current_linkedin()
        safe_kimi("navigate", {"url": url, "newTab": False, "group_title": "AI SEO LinkedIn"}, timeout=45)
    time.sleep(sleep_seconds)
    safe_kimi("find_tab", {"url": url.split("?")[0], "active": True}, timeout=15)


def resolve_profile(expert: dict[str, Any]) -> tuple[str, str, list[dict[str, str]]]:
    if expert.get("profile_url"):
        return str(expert["profile_url"]), "profile_seeded", []
    query = urllib.parse.quote(expert["search"])
    url = f"https://www.linkedin.com/search/results/people/?keywords={query}&origin=GLOBAL_SEARCH_HEADER"
    navigate(url)
    code = r"""
(() => JSON.stringify({
  url: location.href,
  title: document.title,
  text: document.body.innerText.slice(0, 2000),
  links: [...document.querySelectorAll('a[href*="/in/"]')]
    .map(a => ({ text: a.innerText.trim().replace(/\s+/g, ' '), href: a.href.split('?')[0] }))
    .filter(x => x.text && x.href.includes('/in/'))
    .slice(0, 20)
}))()
"""
    data = js_json(code)
    links = data.get("links", [])
    expert_tokens = [t.lower() for t in re.findall(r"[A-Za-z]+", expert["expert"]) if len(t) > 1]
    company_tokens = [t.lower() for t in re.findall(r"[A-Za-z]+", expert["company"]) if len(t) > 2]

    def score(link: dict[str, str]) -> int:
        text = (link.get("text") or "").lower()
        href = (link.get("href") or "").lower()
        value = 0
        value += sum(5 for token in expert_tokens if token in text or token in href)
        value += sum(2 for token in company_tokens if token in text)
        return value

    best = max(links, key=score, default={})
    if not best or score(best) < max(5, len(expert_tokens) * 3):
        return "", "profile_not_resolved", links
    href = best["href"].rstrip("/") + "/"
    return href, "profile_resolved", links


def collect_posts(profile_url: str, max_posts: int = 15) -> tuple[list[dict[str, str]], str]:
    activity_url = profile_url.rstrip("/") + "/recent-activity/all/"
    navigate(activity_url, sleep_seconds=5)
    harvest_code = r"""
(() => {
  const posts = [];
  const selectors = ['[data-urn*="activity"]','[data-id*="activity"]','div.feed-shared-update-v2','div.occludable-update'];
  for (const selector of selectors) {
    for (const node of document.querySelectorAll(selector)) {
      const raw = (node.innerText || '').replace(/\u00a0/g, ' ').replace(/[ \t]+\n/g, '\n').trim();
      if (raw.length < 80) continue;
      const urlNode = node.querySelector('a[href*="/posts/"], a[href*="activity-"], a[href*="/feed/update/"]');
      const postUrl = urlNode ? urlNode.href.split('?')[0] : '';
      const urn = node.getAttribute('data-urn') || node.getAttribute('data-id') || '';
      const lines = raw.split('\n').map(x => x.trim()).filter(Boolean);
      const timeLine = lines.find(x => /\b(now|m|h|d|w|mo|yr|ago|edited)\b/i.test(x) && x.length < 120) || '';
      const author = lines[0] || '';
      const text = lines
        .filter(line => !/^(like|comment|repost|send|follow|connect|message)$/i.test(line))
        .join('\n')
        .slice(0, 7000);
      posts.push({ author, relative_date: timeLine, post_url: postUrl, urn, text });
    }
  }
  return JSON.stringify({ url: location.href, title: document.title, posts });
})()
"""
    scroll_code = r"""
(() => {
  [...document.querySelectorAll('button')].forEach(button => {
    const label = (button.innerText || button.getAttribute('aria-label') || '').trim().toLowerCase();
    if (label === 'see more' || label.includes('see more')) {
      try { button.click(); } catch (_) {}
    }
  });
  window.scrollBy(0, Math.max(900, Math.floor(window.innerHeight * 0.85)));
  return JSON.stringify({ y: window.scrollY, h: document.body.scrollHeight, title: document.title, url: location.href });
})()
"""
    posts: list[dict[str, str]] = []
    seen: set[str] = set()
    for _ in range(22):
        try:
            data = js_json(harvest_code, timeout=30)
        except Exception:
            claim_current_linkedin()
            data = {"posts": []}
        for post in data.get("posts", []):
            key = post.get("post_url") or post.get("urn") or post.get("text", "")[:180]
            if not key or key in seen:
                continue
            seen.add(key)
            posts.append(post)
            if len(posts) >= max_posts:
                break
        if len(posts) >= max_posts:
            break
        safe_kimi("evaluate", {"code": scroll_code}, timeout=20)
        time.sleep(1.3)
    status = "collected" if posts else "no_posts_visible"
    return posts[:max_posts], status


def write_posts_file(expert: dict[str, Any], profile_url: str, posts: list[dict[str, str]], status: str, candidates: list[dict[str, str]]) -> None:
    folder = OUT_ROOT / expert["slug"]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "posts.md"
    lines = [
        f"# LinkedIn Posts: {expert['expert']}",
        "",
        f"Company/source: {expert['company']}",
        f"Profile URL: {profile_url or 'not resolved'}",
        f"Collection status: {status}",
        f"Collection date: 2026-06-29",
        "",
    ]
    if posts:
        for index, post in enumerate(posts, start=1):
            lines.extend(
                [
                    f"## Post {index}",
                    "",
                    f"- Relative date: {post.get('relative_date') or 'not visible'}",
                    f"- URL: {post.get('post_url') or 'not visible'}",
                    "",
                    "```text",
                    (post.get("text") or "").strip(),
                    "```",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "No recent posts were visible through the authenticated browser scrape.",
                "",
                "Candidate profile links from LinkedIn search:",
                "",
            ]
        )
        for link in candidates[:10]:
            lines.append(f"- {link.get('text', '').strip()} - {link.get('href', '').strip()}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_manifest(rows: list[dict[str, Any]]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    fields = [
        "rank",
        "expert",
        "slug",
        "company",
        "profile_url",
        "collection_status",
        "posts_collected",
        "reason",
        "next_step",
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def count_posts_file(slug: str) -> int:
    path = OUT_ROOT / slug / "posts.md"
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.startswith("## Post "))


def read_manifest_rows() -> dict[str, dict[str, str]]:
    if not MANIFEST.exists():
        return {}
    with MANIFEST.open("r", newline="", encoding="utf-8") as handle:
        return {row["slug"]: row for row in csv.DictReader(handle)}


def main() -> None:
    rows: list[dict[str, Any]] = []
    existing_rows = read_manifest_rows()
    claim_current_linkedin()
    for expert in EXPERTS:
        existing_count = count_posts_file(expert["slug"])
        existing_row = existing_rows.get(expert["slug"])
        if existing_count >= 10 and existing_row:
            print(f"Skipping {expert['expert']} ({existing_count} posts already collected)...", flush=True)
            rows.append(existing_row)
            write_manifest(rows)
            continue
        print(f"Collecting {expert['expert']}...", flush=True)
        profile_url, profile_status, candidates = resolve_profile(expert)
        posts: list[dict[str, str]] = []
        status = profile_status
        reason = ""
        if profile_url:
            try:
                posts, status = collect_posts(profile_url)
                reason = f"{len(posts)} recent posts visible from LinkedIn activity page."
            except Exception as exc:
                status = "post_collection_failed"
                reason = str(exc)[:240]
        else:
            reason = "LinkedIn profile could not be resolved from authenticated people search."
        write_posts_file(expert, profile_url, posts, status, candidates)
        rows.append(
            {
                "rank": expert["rank"],
                "expert": expert["expert"],
                "slug": expert["slug"],
                "company": expert["company"],
                "profile_url": profile_url,
                "collection_status": status,
                "posts_collected": len(posts),
                "reason": reason,
                "next_step": "Use Apify/manual profile URL if fewer than 10 posts are visible."
                if len(posts) < 10
                else "Ready for playbook analysis.",
            }
        )
        write_manifest(rows)

    safe_kimi("close_session", {}, timeout=15)


if __name__ == "__main__":
    main()
