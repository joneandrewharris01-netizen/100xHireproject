"""Interactive Reddit posting helper.

Opens each actionable lead's URL in your DEFAULT browser one at a time, copies
the prewritten comment to your clipboard, waits for you to hit ENTER after
you've posted manually. Then moves to the next lead.

Why interactive: Reddit's anti-spam flags batch automated posts; mods see
the patterns. Keeping a human in the loop preserves account safety AND lets
you edit each comment for thread context before sending.

Usage:
    python -m agents.outreach_os.post_helper            # all HOT + WARM
    python -m agents.outreach_os.post_helper --tier HOT # HOT only
    python -m agents.outreach_os.post_helper --dms      # surface DM angles too
"""
from __future__ import annotations

import argparse
import re
import webbrowser
from datetime import date
from pathlib import Path

try:
    import pyperclip
except ImportError:
    pyperclip = None  # graceful fallback; user can copy manually

from . import frontmatter, queue_scanner, tier as tier_mod

_TIER_RANK = {"HOT": 0, "WARM": 1, "AUTHORITY": 2}


def _extract_section(body: str, header: str) -> str:
    """Pull text under a `## <header>` block, stopping at the next `## ` heading."""
    pattern = rf"##\s+{re.escape(header)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    text = m.group(1).strip()
    # Strip a leading blockquote `>` if present (queue files often quote the comment)
    lines = [re.sub(r"^>\s?", "", ln) for ln in text.splitlines()]
    return "\n".join(lines).strip()


def _load_lead(lead: dict) -> dict:
    """Read the queue file body and pull out comment + DM."""
    text = Path(lead["path"]).read_text(encoding="utf-8")
    _, body = frontmatter.parse(text)
    comment = (
        _extract_section(body, "Suggested REDDIT COMMENT")
        or _extract_section(body, "REDDIT COMMENT")
        or _extract_section(body, "Suggested comment")
    )
    dm = (
        _extract_section(body, "Suggested REDDIT DM")
        or _extract_section(body, "Suggested DM angle (only if they engage)")
        or _extract_section(body, "Suggested DM angle")
        or _extract_section(body, "DM")
    )
    fm = lead["frontmatter"]
    derived = tier_mod.derive(lead["source"], fm)
    return {
        **lead,
        "comment": comment,
        "dm": dm,
        "tier": derived,
        "url": fm.get("url", ""),
        "author": fm.get("author", ""),
        "subreddit": fm.get("subreddit", ""),
        "urgency": int(fm.get("urgency", 0)) if fm.get("urgency") else 0,
        "post_id": fm.get("post_id", ""),
    }


def _sort_key(lead: dict) -> tuple[int, int]:
    """Sort by tier rank, then urgency descending."""
    rank = _TIER_RANK.get(lead.get("tier") or "", 99)
    return (rank, -lead.get("urgency", 0))


def _copy(text: str) -> bool:
    if pyperclip is None or not text:
        return False
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def _print_lead_card(idx: int, total: int, lead: dict) -> None:
    print()
    print("=" * 72)
    print(f"[{idx}/{total}]  {lead['tier']}  urgency {lead['urgency']}")
    print(f"  Author:    {lead['author']}")
    print(f"  Subreddit: r/{lead['subreddit']}")
    print(f"  Source:    {lead['source']}")
    print(f"  Post ID:   {lead['post_id']}")
    print(f"  Queue:     {lead['path']}")
    print(f"  URL:       {lead['url']}")
    print("=" * 72)
    if lead.get("comment"):
        preview = lead["comment"][:300].replace("\n", " ")
        print(f"\n  Comment preview: {preview}{'...' if len(lead['comment']) > 300 else ''}")


def run(*, tier_filter: list[str] | None = None, include_dms: bool = False) -> None:
    today = date.today()
    raw_leads = queue_scanner.scan_today_all(today=today)
    if not raw_leads:
        print("No actionable leads in today's queues. Nothing to post.")
        return

    leads = [_load_lead(l) for l in raw_leads]
    leads = [l for l in leads if l["tier"] is not None and l["url"]]
    if tier_filter:
        leads = [l for l in leads if l["tier"] in tier_filter]
    leads.sort(key=_sort_key)

    print(f"\n{len(leads)} actionable lead(s) loaded. Sorted: HOT first, then by urgency.\n")
    if pyperclip is None:
        print("(pyperclip not installed; comments will not auto-copy. `pip install pyperclip` to enable.)")

    for idx, lead in enumerate(leads, 1):
        _print_lead_card(idx, len(leads), lead)
        if not lead.get("comment"):
            print("\n  ! No comment text in queue file. Skipping (you'll need to write one).")
            input("  Press ENTER to continue: ")
            continue

        copied = _copy(lead["comment"])
        if copied:
            print("\n  ✓ Comment copied to clipboard.")
        else:
            print("\n  Copy this comment manually:")
            print("  " + "\n  ".join(lead["comment"].splitlines()))

        webbrowser.open(lead["url"])
        print(f"\n  Browser opened: {lead['url']}")
        ans = input("\n  Action: [ENTER] = posted, move to next  |  [s] skip  |  [q] quit: ").strip().lower()
        if ans == "q":
            print(f"\nStopped at {idx}/{len(leads)}. Re-run to resume from here (script is stateless).")
            return
        if ans == "s":
            continue

        if include_dms and lead.get("dm"):
            print("\n  --- DM angle (only if they engage in thread) ---")
            print("  " + "\n  ".join(lead["dm"].splitlines()))
            ans2 = input("\n  Copy DM to clipboard? [y/ENTER]: ").strip().lower()
            if ans2 == "y":
                if _copy(lead["dm"]):
                    print("  ✓ DM copied to clipboard.")

    print(f"\nAll {len(leads)} leads done. Tomorrow morning run /outreach-flush-outcomes after marking outcomes in the brief.")


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Interactive Reddit posting helper.")
    parser.add_argument(
        "--tier",
        choices=["HOT", "WARM", "AUTHORITY"],
        action="append",
        help="Filter to specific tier(s). Default: all.",
    )
    parser.add_argument("--dms", action="store_true", help="Surface DM angles after each comment.")
    args = parser.parse_args()
    run(tier_filter=args.tier, include_dms=args.dms)


if __name__ == "__main__":
    _cli()
