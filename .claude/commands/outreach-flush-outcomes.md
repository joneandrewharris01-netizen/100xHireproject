---
description: End-of-day batch outcome update. Scans today's Daily Brief for ticked outcome checkboxes and writes them to the right outcome store.
---

You are running `/outreach-flush-outcomes`.

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.flush_outcomes
```

Print the returned summary: `updated: N, conflicts: M`.

If `conflicts > 0`, list the post_ids that had multiple outcome boxes ticked and ask the user to fix the brief and re-run.
