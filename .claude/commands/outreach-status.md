---
description: Mid-day cheap visibility check. Re-runs aggregate.py and dashboard.py only. No upstream pipelines, no LLM calls.
---

You are running `/outreach-status`.

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.aggregate
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.dashboard
```

Print a one-line summary: total leads in today's brief, pending-outcome count, last-updated timestamp on the dashboard.
