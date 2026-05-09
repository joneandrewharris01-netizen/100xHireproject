---
description: Track the outcome of a posted reddit_mine lead. Writes to agents/reddit_mine/outcomes.json.
argument-hint: <post_id> <outcome>
---

User invoked: `/reddit-mine-outcome $ARGUMENTS`

Parse `$ARGUMENTS` as `<post_id> <outcome>` where outcome is one of:

- `responded`
- `dmd_back`
- `ghosted`
- `client`
- `unsubscribed`

If the outcome is not in this list, print the list and stop.

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "
from agents.reddit_mine import outcomes
outcomes.record('__POST_ID__', '__OUTCOME__')
print('updated')
"
```

Substitute `__POST_ID__` and `__OUTCOME__` with the actual values from `$ARGUMENTS`. Do not run the snippet verbatim.
