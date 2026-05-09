"""Outreach OS - daily client-acquisition control plane.

See docs/superpowers/specs/2026-05-09-outreach-os-design.md for the design.
This package contains pure-Python helpers invoked by the slash commands in
.claude/commands/outreach-os.md and friends. No SMTP, no sender SDKs.
"""
PIPELINES = ("revops", "pe", "reddit_mine")
LINKEDIN_DAILY_CAP = 20
TIER_HOT = "HOT"
TIER_WARM = "WARM"
TIER_AUTHORITY = "AUTHORITY"
