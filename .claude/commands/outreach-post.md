---
description: Interactive Reddit posting helper. Opens each lead URL in your default browser, copies comment to clipboard, waits for you to post manually before moving to the next. Reddit-ToS safe — keeps a human in the loop.
argument-hint: [--tier HOT|WARM|AUTHORITY] [--dms]
---

You are running `/outreach-post $ARGUMENTS`.

This is the SAFE alternative to auto-posting. The user posts each comment manually (Reddit ToS prohibits automated posting; mods detect batch patterns). The helper just removes friction: opens URLs, copies comments to clipboard, paces the work.

Run:

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.post_helper $ARGUMENTS
```

If the user types just `/outreach-post`, no flags. If they pass `--tier HOT` it runs only HOT-tier leads. `--dms` surfaces DM angles too.

Print the user-facing output verbatim. Do NOT post anything yourself. Do NOT call any send API. The script does all the lead-by-lead pacing.
