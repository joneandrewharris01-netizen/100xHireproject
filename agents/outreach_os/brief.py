"""Render the Daily Brief markdown."""
from __future__ import annotations

from datetime import date, datetime
from textwrap import dedent

from . import tier as tier_mod


def _bucket(leads: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"HOT": [], "WARM": [], "AUTHORITY": []}
    for lead in leads:
        t = tier_mod.derive(lead["source"], lead["frontmatter"])
        if t in out:
            out[t].append(lead)
    return out


def _render_lead(lead: dict, idx: int) -> str:
    fm = lead["frontmatter"]
    pid = fm.get("post_id", "")
    author = fm.get("author", "")
    sub = fm.get("subreddit", "")
    return dedent(f"""
        ### {idx}. {author} . r/{sub} ({lead['source']} . id {pid})
        - [ ] Post comment + send DM. Queue file: `{lead['path']}`
        """).strip() + "\n"


def _render_pending(pending: list[dict]) -> str:
    if not pending:
        return ""
    lines = ["## Pending outcomes (>7 days old)"]
    for p in pending:
        lines.append(
            f"- [ ] `{p['post_id']}` ({p['source']}) posted {p['posted_at']}\n"
            f"  - [ ] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub"
        )
    lines.append("\nTick a box per lead, then run `/outreach-flush-outcomes` at end of day.\n")
    return "\n".join(lines) + "\n"


def _render_linkedin(items: list[dict]) -> str:
    if not items:
        return ""
    lines = [f"## LinkedIn {len(items)} (~60 min)"]
    for item in items:
        name = item.get("name") or item.get("author/name") or "(unknown)"
        title = (item.get("title") or "").strip()
        company = (item.get("company") or "").strip()
        opener = item.get("opener", "")
        # Build the role/company suffix only if data exists
        if title and company:
            role = f"{title} @ {company}"
        elif title:
            role = title
        elif company:
            role = f"@ {company}"
        else:
            role = "(role unknown, click profile to verify)"
        profile = item.get("author/profileurl") or item.get("author/profileUrl") or item.get("profile_url") or ""
        profile_md = f" [profile]({profile})" if profile else ""
        lines.append(f'- [ ] **{name}** . {role}{profile_md} . "{opener}"')
    return "\n".join(lines) + "\n"


def render(
    *,
    today: date,
    leads: list[dict],
    linkedin: list[dict],
    pending: list[dict],
    pipelines_run: list[str],
    pipelines_skipped: list[str],
    pipelines_failed: list[str],
) -> str:
    buckets = _bucket(leads)
    totals = {
        "hot": len(buckets["HOT"]),
        "warm": len(buckets["WARM"]),
        "authority": len(buckets["AUTHORITY"]),
        "linkedin": len(linkedin),
        "total": len(buckets["HOT"]) + len(buckets["WARM"]) + len(buckets["AUTHORITY"]) + len(linkedin),
    }

    fm_lines = [
        "---",
        f"date: {today.isoformat()}",
        f"generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"totals: {totals}",
        f"pipelines_run: {pipelines_run}",
        f"pipelines_skipped: {pipelines_skipped}",
        f"pipelines_failed: {pipelines_failed}",
        "---",
        "",
        f"# Outreach OS - {today.isoformat()}",
        "",
    ]

    body_parts = []
    body_parts.append(_render_pending(pending))

    if totals["total"] == 0:
        body_parts.append("No new leads today. See pending outcomes above and the dashboard for context.\n")
    else:
        if buckets["HOT"]:
            body_parts.append("## HOT (do these first, ~30 min)\n")
            for i, lead in enumerate(buckets["HOT"], 1):
                body_parts.append(_render_lead(lead, i))
        if buckets["WARM"]:
            body_parts.append("## WARM (~60 min)\n")
            for i, lead in enumerate(buckets["WARM"], 1):
                body_parts.append(_render_lead(lead, i))
        if buckets["AUTHORITY"]:
            body_parts.append("## AUTHORITY (public replies, no pitch, ~30 min)\n")
            for i, lead in enumerate(buckets["AUTHORITY"], 1):
                body_parts.append(_render_lead(lead, i))
        body_parts.append(_render_linkedin(linkedin))
        body_parts.append("## Today's plan\nTotal: ~3 hours. Start with HOT, then LinkedIn, then WARM, AUTHORITY last.\n")

    return "\n".join(fm_lines) + "\n".join(body_parts)
