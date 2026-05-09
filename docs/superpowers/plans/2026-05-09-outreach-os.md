# Outreach OS Implementation Plan

> **For agentic workers:** REQUIRED: Use `superpowers:subagent-driven-development` (if subagents available) or `superpowers:executing-plans` to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/superpowers/specs/2026-05-09-outreach-os-design.md`

**Goal:** Build a Claude-Code-native daily client-acquisition control plane that orchestrates three existing Reddit pipelines plus a LinkedIn 20/day queue, writes a Daily Brief and Dashboard to Obsidian, and tracks outcomes via a tickbox-flush flow.

**Architecture:** Slash commands as user entry points; pure-Python helpers under `agents/outreach_os/` for the orchestration logic; per-pipeline `last_run.json` markers written by the orchestrator on clean exit; the only outbound API is the Anthropic API (Haiku for openers, Opus for orchestration).

**Tech Stack:** Python 3.11 (`C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe`), pytest, openpyxl, anthropic SDK, PyYAML, sqlite3 (stdlib). No new infra. No web framework. No SMTP.

---

## Hard rules (apply to every task)

1. **Voice:** No em-dashes, no emoji, no guru cadence in any user-facing string (Daily Brief copy, Dashboard verdicts, LinkedIn openers, slash-command output). Use periods, commas, "and".
2. **Send guardrails (spec section "Send guardrails"):**
   - No code path may call SMTP, sender SDKs (Smartlead, Instantly, Apollo, Lemlist, Outreach, Mailgun, SendGrid, yagmail, smtplib, aiosmtplib), or platform send APIs (LinkedIn, Reddit) anywhere in this MVP.
   - The MVP only calls the Anthropic API outbound. Reddit/LinkedIn read-only lookup APIs are fine if needed.
   - The plan's final task adds a regression test that fails if any module imports both a sender SDK and the Uncharted dataset reader.
3. **TDD:** Failing test first, then minimal implementation. Run test to confirm RED, write impl, run test to confirm GREEN.
4. **Atomic commits:** One commit per task (after Step 5). Use `git add <specific paths>`, never `git add -A` or `git add .`.
5. **Python invocation:** Always use the Windows path `C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe`. In tests, use `sys.executable` instead.
6. **Existing pipelines stay untouched.** No edits to `agents/revops_intel/`, `agents/pe_intel/`, or `agents/reddit_mine/` source code. Only additions in `agents/outreach_os/` and a new `agents/reddit_mine/outcomes.py` module that is purely additive.

---

## File structure (everything new)

```
agents/outreach_os/
  __init__.py              (Chunk 0)
  config.json              (Chunk 0 — tier thresholds, daily caps)
  state.json               (Chunk 4 — created by linkedin_rotator on first run)
  tier.py                  (Chunk 1 — tier derivation rules)
  last_run.py              (Chunk 1 — read/write per-pipeline markers)
  frontmatter.py           (Chunk 2 — YAML frontmatter parser)
  queue_scanner.py         (Chunk 2 — glob + parse queue files)
  pending_outcomes.py      (Chunk 2 — read pending leads from DB or json)
  brief.py                 (Chunk 2 — render Daily Brief MD)
  aggregate.py             (Chunk 2 — CLI entry: builds Daily Brief)
  outcome_counts.py        (Chunk 3 — count outcomes from all sources)
  win_rate.py              (Chunk 3 — compute win rates)
  verdicts.py              (Chunk 3 — auto-generate "What's working/not")
  run_history.py           (Chunk 3 — read last 7 days of brief frontmatter)
  dashboard.py             (Chunk 3 — CLI entry: builds Dashboard)
  xlsx_loader.py           (Chunk 4 — read B2B AI Agents.xlsx)
  icp_bump.py              (Chunk 4 — ICP-priority sort)
  rotation.py              (Chunk 4 — sequential pointer + state.json)
  opener.py                (Chunk 4 — Haiku call for one opener)
  linkedin_rotator.py      (Chunk 4 — CLI entry: writes today's LinkedIn 20)
  tickbox.py               (Chunk 5 — parse outcome checkboxes from brief)
  outcome_dispatcher.py    (Chunk 5 — write outcomes to right destination)
  flush_outcomes.py        (Chunk 5 — CLI entry: full flush pipeline)

agents/reddit_mine/
  outcomes.py              (Chunk 5 — read/write outcomes.json)

.claude/commands/
  outreach-os.md           (Chunk 6)
  outreach-status.md       (Chunk 6)
  outreach-flush-outcomes.md (Chunk 6)
  reddit-mine-outcome.md   (Chunk 6)

tests/
  conftest.py              (Chunk 0)
  outreach_os/
    test_tier.py
    test_last_run.py
    test_frontmatter.py
    test_queue_scanner.py
    test_pending_outcomes.py
    test_brief.py
    test_aggregate.py
    test_outcome_counts.py
    test_win_rate.py
    test_verdicts.py
    test_run_history.py
    test_dashboard.py
    test_xlsx_loader.py
    test_icp_bump.py
    test_rotation.py
    test_opener.py
    test_linkedin_rotator.py
    test_tickbox.py
    test_outcome_dispatcher.py
    test_flush_outcomes.py
    test_smoke_outreach_os.py
    test_smoke_skip_if_run_today.py
    test_guardrails.py
  reddit_mine/
    test_outcomes.py
  fixtures/
    revops_queue/2026-05-09_alice_post1.md
    revops_queue/2026-05-09_bob_post2.md
    pe_queue/2026-05-09_carol_post3.md
    reddit_mine_queue/2026-05-09_dave_post4.md
    b2b_leads_10.xlsx
    revops_processed_leads.db (built per-test)

pytest.ini                 (Chunk 0 — at project root)

outreach-os/                (created at runtime by aggregate.py + dashboard.py)
  daily/YYYY-MM-DD.md
  dashboard.md
```

---

## Chunk 0: Bootstrap

### Task 0.1: Install Python deps

**Files:**
- (no new files)

- [ ] **Step 1: Install dependencies**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pip install pytest pytest-mock pyyaml openpyxl anthropic
```

Expected: all packages install cleanly.

- [ ] **Step 2: Verify versions**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "import pytest, yaml, openpyxl, anthropic; print(pytest.__version__, yaml.__version__, openpyxl.__version__, anthropic.__version__)"
```

Expected: four version strings printed, no ImportError.

(No commit — environment-only step.)

---

### Task 0.2: Create pytest config + tests skeleton

**Files:**
- Create: `pytest.ini`
- Create: `tests/conftest.py`
- Create: `tests/__init__.py`
- Create: `tests/outreach_os/__init__.py`
- Create: `tests/reddit_mine/__init__.py`
- Create: `tests/fixtures/.gitkeep`

- [ ] **Step 1: Write `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -ra --strict-markers
markers =
    smoke: end-to-end smoke tests that read/write real files
```

- [ ] **Step 2: Write `tests/conftest.py`**

```python
"""Shared pytest fixtures for the Outreach OS test suite."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture()
def tmp_repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A throwaway repo root with the directory layout aggregate.py expects."""
    for sub in [
        "agents/revops_intel/queue",
        "agents/pe_intel/queue",
        "agents/reddit_mine/queue",
        "agents/outreach_os/linkedin",
        "outreach-os/daily",
        "linkedin-content",
    ]:
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    yield tmp_path


@pytest.fixture()
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
```

- [ ] **Step 3: Create empty package init files**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "
import pathlib
for p in ['tests/__init__.py', 'tests/outreach_os/__init__.py', 'tests/reddit_mine/__init__.py']:
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(p).touch()
pathlib.Path('tests/fixtures/.gitkeep').touch()
"
```

- [ ] **Step 4: Verify pytest discovers nothing yet (smoke check)**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest --collect-only
```

Expected: `0 tests collected` (no failures, just empty).

- [ ] **Step 5: Commit**

```bash
git add pytest.ini tests/__init__.py tests/conftest.py tests/outreach_os/__init__.py tests/reddit_mine/__init__.py tests/fixtures/.gitkeep
git commit -m "test(outreach-os): pytest config and tests/ skeleton"
```

---

### Task 0.3: Create `agents/outreach_os/` package + config

**Files:**
- Create: `agents/outreach_os/__init__.py`
- Create: `agents/outreach_os/config.json`

- [ ] **Step 1: Write `agents/outreach_os/__init__.py`**

```python
"""Outreach OS — daily client-acquisition control plane.

See docs/superpowers/specs/2026-05-09-outreach-os-design.md for the design.
This package contains pure-Python helpers invoked by the slash commands in
.claude/commands/outreach-os.md and friends. No SMTP, no sender SDKs.
"""
PIPELINES = ("revops", "pe", "reddit_mine")
LINKEDIN_DAILY_CAP = 20
TIER_HOT = "HOT"
TIER_WARM = "WARM"
TIER_AUTHORITY = "AUTHORITY"
```

- [ ] **Step 2: Write `agents/outreach_os/config.json`**

```json
{
  "tier_thresholds": {
    "hot_min_score": 80,
    "warm_min_score": 60,
    "authority_min_score": 40
  },
  "daily_caps": {
    "revops": 5,
    "pe": 5,
    "reddit_mine": 5,
    "linkedin": 20
  },
  "outcome_stale_days": 7,
  "schedule_time": "07:30",
  "icp_title_keywords": [
    "vp revops",
    "head of sales ops",
    "head of revenue operations",
    "director of revenue operations",
    "director of sales operations",
    "sales operations manager",
    "revenue operations",
    "revops"
  ]
}
```

- [ ] **Step 3: Verify importable**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "from agents.outreach_os import PIPELINES, LINKEDIN_DAILY_CAP; print(PIPELINES, LINKEDIN_DAILY_CAP)"
```

Expected: `('revops', 'pe', 'reddit_mine') 20`

- [ ] **Step 4: Commit**

```bash
git add agents/outreach_os/__init__.py agents/outreach_os/config.json
git commit -m "feat(outreach-os): package skeleton and config.json"
```

---

## Chunk 1: Foundation modules (tier, last_run)

### Task 1.1: `tier.py` — tier derivation

**Files:**
- Create: `agents/outreach_os/tier.py`
- Test: `tests/outreach_os/test_tier.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/outreach_os/test_tier.py
"""Unit tests for tier derivation per spec section 'Tier derivation rules'."""
import pytest

from agents.outreach_os import tier


@pytest.mark.parametrize("score,expected", [
    (95, "HOT"),
    (80, "HOT"),
    (79, "WARM"),
    (60, "WARM"),
    (59, "AUTHORITY"),
    (40, "AUTHORITY"),
    (39, None),
    (0, None),
])
def test_score_to_tier_default_thresholds(score, expected):
    assert tier.score_to_tier(score) == expected


def test_reddit_mine_tier_passthrough():
    # reddit_mine queue files already carry tier — pass through.
    assert tier.derive("reddit_mine", {"tier": "HOT"}) == "HOT"
    assert tier.derive("reddit_mine", {"tier": "WARM"}) == "WARM"
    assert tier.derive("reddit_mine", {"tier": "AUTHORITY"}) == "AUTHORITY"


def test_revops_tier_from_score():
    assert tier.derive("revops", {"score": 92}) == "HOT"
    assert tier.derive("revops", {"score": 70}) == "WARM"
    assert tier.derive("revops", {"score": 45}) == "AUTHORITY"
    assert tier.derive("revops", {"score": 30}) is None


def test_pe_tier_from_score():
    assert tier.derive("pe", {"score": 85}) == "HOT"
    assert tier.derive("pe", {"score": 50}) == "AUTHORITY"


def test_unknown_source_raises():
    with pytest.raises(ValueError, match="unknown source"):
        tier.derive("twitter", {"score": 99})


def test_thresholds_overridable():
    custom = {"hot_min_score": 90, "warm_min_score": 70, "authority_min_score": 50}
    assert tier.score_to_tier(85, thresholds=custom) == "WARM"
    assert tier.score_to_tier(60, thresholds=custom) == "AUTHORITY"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_tier.py -v
```

Expected: ImportError or collection error (`tier` module doesn't exist).

- [ ] **Step 3: Write `agents/outreach_os/tier.py`**

```python
"""Tier derivation per spec section 'Tier derivation rules'."""
from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "config.json"
_DEFAULT_THRESHOLDS = json.loads(_CONFIG_PATH.read_text())["tier_thresholds"]


def score_to_tier(score: int, thresholds: dict | None = None) -> str | None:
    """Map a numeric score to HOT / WARM / AUTHORITY / None."""
    t = thresholds or _DEFAULT_THRESHOLDS
    if score >= t["hot_min_score"]:
        return "HOT"
    if score >= t["warm_min_score"]:
        return "WARM"
    if score >= t["authority_min_score"]:
        return "AUTHORITY"
    return None


def derive(source: str, frontmatter: dict, thresholds: dict | None = None) -> str | None:
    """Derive the unified tier for a queue file based on its source."""
    if source == "reddit_mine":
        return frontmatter.get("tier")
    if source in {"revops", "pe"}:
        return score_to_tier(int(frontmatter.get("score", 0)), thresholds)
    raise ValueError(f"unknown source: {source}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_tier.py -v
```

Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/tier.py tests/outreach_os/test_tier.py
git commit -m "feat(outreach-os): tier derivation module"
```

---

### Task 1.2: `last_run.py` — per-pipeline run markers

**Files:**
- Create: `agents/outreach_os/last_run.py`
- Test: `tests/outreach_os/test_last_run.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/outreach_os/test_last_run.py
"""last_run marker read/write."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agents.outreach_os import last_run


def test_marker_path(tmp_repo_root: Path):
    assert last_run.marker_path("revops") == Path("agents/revops_intel/last_run.json")
    assert last_run.marker_path("pe") == Path("agents/pe_intel/last_run.json")
    assert last_run.marker_path("reddit_mine") == Path("agents/reddit_mine/last_run.json")


def test_unknown_pipeline_raises():
    with pytest.raises(ValueError, match="unknown pipeline"):
        last_run.marker_path("twitter")


def test_write_then_read(tmp_repo_root: Path):
    last_run.write("revops", new_leads=4, errors=0)
    data = last_run.read("revops")
    assert data["date"] == date.today().isoformat()
    assert data["new_leads"] == 4
    assert data["errors"] == 0
    assert "finished_at" in data


def test_read_missing_returns_none(tmp_repo_root: Path):
    assert last_run.read("revops") is None


def test_ran_today_true_when_marker_is_today(tmp_repo_root: Path):
    last_run.write("pe", new_leads=0, errors=0)
    assert last_run.ran_today("pe") is True


def test_ran_today_false_when_no_marker(tmp_repo_root: Path):
    assert last_run.ran_today("pe") is False


def test_ran_today_false_when_marker_is_old(tmp_repo_root: Path):
    marker = last_run.marker_path("revops")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"date": "2020-01-01", "finished_at": "2020-01-01T00:00:00", "new_leads": 0, "errors": 0}')
    assert last_run.ran_today("revops") is False
```

- [ ] **Step 2: Run test, verify it fails**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_last_run.py -v
```

Expected: ImportError on `agents.outreach_os.last_run`.

- [ ] **Step 3: Write `agents/outreach_os/last_run.py`**

```python
"""Per-pipeline last_run.json markers.

Written by /outreach-os AFTER a sub-pipeline completes cleanly.
Crashed runs leave no marker, so the next morning re-runs them.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

_PIPELINE_DIRS = {
    "revops": Path("agents/revops_intel"),
    "pe": Path("agents/pe_intel"),
    "reddit_mine": Path("agents/reddit_mine"),
}


def marker_path(pipeline: str) -> Path:
    if pipeline not in _PIPELINE_DIRS:
        raise ValueError(f"unknown pipeline: {pipeline}")
    return _PIPELINE_DIRS[pipeline] / "last_run.json"


def write(pipeline: str, *, new_leads: int, errors: int) -> Path:
    p = marker_path(pipeline)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": date.today().isoformat(),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "new_leads": int(new_leads),
        "errors": int(errors),
    }
    p.write_text(json.dumps(payload, indent=2))
    return p


def read(pipeline: str) -> dict | None:
    p = marker_path(pipeline)
    if not p.exists():
        return None
    return json.loads(p.read_text())


def ran_today(pipeline: str) -> bool:
    data = read(pipeline)
    return bool(data and data.get("date") == date.today().isoformat())
```

- [ ] **Step 4: Run tests, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_last_run.py -v
```

Expected: 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/last_run.py tests/outreach_os/test_last_run.py
git commit -m "feat(outreach-os): per-pipeline last_run markers"
```

---

## Chunk 2: Aggregate + Daily Brief

### Task 2.1: `frontmatter.py` — YAML frontmatter parser

**Files:**
- Create: `agents/outreach_os/frontmatter.py`
- Test: `tests/outreach_os/test_frontmatter.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/outreach_os/test_frontmatter.py
import pytest

from agents.outreach_os import frontmatter


def test_parse_basic():
    text = """---
post_id: abc123
score: 92
tier: HOT
---

## Body
Some content here.
"""
    fm, body = frontmatter.parse(text)
    assert fm["post_id"] == "abc123"
    assert fm["score"] == 92
    assert fm["tier"] == "HOT"
    assert "Body" in body


def test_parse_no_frontmatter_returns_empty_dict_and_full_body():
    text = "## Just a heading\nbody content"
    fm, body = frontmatter.parse(text)
    assert fm == {}
    assert body == text


def test_parse_malformed_frontmatter_returns_empty_dict():
    text = "---\nnot: valid: yaml: here:\n---\nbody"
    fm, body = frontmatter.parse(text)
    assert fm == {}


def test_parse_handles_lists_and_nested():
    text = """---
reasons: [low_reply_rate, hiring_freeze]
totals:
  hot: 3
  warm: 5
---
"""
    fm, _ = frontmatter.parse(text)
    assert fm["reasons"] == ["low_reply_rate", "hiring_freeze"]
    assert fm["totals"] == {"hot": 3, "warm": 5}
```

- [ ] **Step 2: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_frontmatter.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write impl**

```python
# agents/outreach_os/frontmatter.py
"""Parse YAML frontmatter from a markdown string."""
from __future__ import annotations

import re

import yaml

_FM_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


def parse(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_str). Empty dict if no/invalid frontmatter."""
    m = _FM_RE.match(text)
    if m is None:
        return {}, text
    raw_yaml, body = m.group(1), m.group(2)
    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError:
        return {}, text
    if not isinstance(data, dict):
        return {}, text
    return data, body
```

- [ ] **Step 4: Run, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_frontmatter.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/frontmatter.py tests/outreach_os/test_frontmatter.py
git commit -m "feat(outreach-os): YAML frontmatter parser"
```

---

### Task 2.2: Fixture queue files for downstream tests

**Files:**
- Create: `tests/fixtures/revops_queue/2026-05-09_alice_post1.md`
- Create: `tests/fixtures/revops_queue/2026-05-09_bob_post2.md`
- Create: `tests/fixtures/pe_queue/2026-05-09_carol_post3.md`
- Create: `tests/fixtures/reddit_mine_queue/2026-05-09_dave_post4.md`

- [ ] **Step 1: Write fixture files (verbatim)**

`tests/fixtures/revops_queue/2026-05-09_alice_post1.md`:
```markdown
---
post_id: post1
author: u/alice
subreddit: sales
url: https://reddit.com/r/sales/comments/post1
score: 92
reasons: [low_reply_rate, hiring_freeze]
problem_category: cold_email_failing
firm_size_signal: smb
offer_match: outbound_engine
generated_at: 2026-05-09T07:00:00
---

## Original post
**My cold email reply rate is 0.4%**
> agency wants 8k more

## Suggested REDDIT COMMENT
> hello world
```

`tests/fixtures/revops_queue/2026-05-09_bob_post2.md`:
```markdown
---
post_id: post2
author: u/bob
subreddit: sales
url: https://reddit.com/r/sales/comments/post2
score: 72
reasons: [needs_help]
problem_category: hubspot_chaos
firm_size_signal: midmarket
offer_match: outbound_engine
generated_at: 2026-05-09T07:00:00
---

## Original post
hubspot is a mess
```

`tests/fixtures/pe_queue/2026-05-09_carol_post3.md`:
```markdown
---
post_id: post3
author: u/carol
subreddit: privateequity
url: https://reddit.com/r/privateequity/comments/post3
score: 85
reasons: [acquisition_pain]
problem_category: portfolio_ops
firm_size_signal: portco
offer_match: outbound_engine
generated_at: 2026-05-09T07:00:00
---
```

`tests/fixtures/reddit_mine_queue/2026-05-09_dave_post4.md`:
```markdown
---
post_id: post4
author: u/dave
subreddit: n8n
url: https://reddit.com/r/n8n/comments/post4
created_iso: 2026-05-08T10:00:00
tier: HOT
urgency: 9
icp_segment: agency
help_angle: claude_automation
generated_at: 2026-05-09T07:00:00
---

## Original problem
> stuck on n8n loop logic
```

- [ ] **Step 2: Verify YAML parses cleanly**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "
import yaml, pathlib
for p in pathlib.Path('tests/fixtures').rglob('*.md'):
    text = p.read_text()
    parts = text.split('---', 2)
    yaml.safe_load(parts[1])
    print('OK', p)
"
```

Expected: 4 lines `OK <path>`.

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/revops_queue tests/fixtures/pe_queue tests/fixtures/reddit_mine_queue
git commit -m "test(outreach-os): fixture queue files for aggregator tests"
```

---

### Task 2.3: `queue_scanner.py` — read all queue files for today

**Files:**
- Create: `agents/outreach_os/queue_scanner.py`
- Test: `tests/outreach_os/test_queue_scanner.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/outreach_os/test_queue_scanner.py
import shutil
from datetime import date
from pathlib import Path

from agents.outreach_os import queue_scanner


def _seed_fixtures(repo: Path, fixtures: Path) -> None:
    mapping = {
        "revops_queue": "agents/revops_intel/queue",
        "pe_queue": "agents/pe_intel/queue",
        "reddit_mine_queue": "agents/reddit_mine/queue",
    }
    for src_name, dst in mapping.items():
        for p in (fixtures / src_name).iterdir():
            (repo / dst).mkdir(parents=True, exist_ok=True)
            shutil.copy(p, repo / dst / p.name)


def test_scan_returns_one_lead_per_queue_file(tmp_repo_root, fixtures_dir):
    _seed_fixtures(tmp_repo_root, fixtures_dir)

    leads = queue_scanner.scan_today_all(today=date(2026, 5, 9))

    assert len(leads) == 4
    sources = {l["source"] for l in leads}
    assert sources == {"revops", "pe", "reddit_mine"}


def test_scan_skips_files_not_generated_today(tmp_repo_root, fixtures_dir):
    _seed_fixtures(tmp_repo_root, fixtures_dir)
    leads = queue_scanner.scan_today_all(today=date(2026, 5, 10))
    assert leads == []


def test_scan_attaches_source_and_path(tmp_repo_root, fixtures_dir):
    _seed_fixtures(tmp_repo_root, fixtures_dir)
    leads = queue_scanner.scan_today_all(today=date(2026, 5, 9))
    one = leads[0]
    assert "source" in one
    assert "path" in one
    assert "frontmatter" in one


def test_scan_returns_empty_when_dirs_missing(tmp_repo_root):
    # tmp_repo_root has dirs but they're empty
    leads = queue_scanner.scan_today_all(today=date(2026, 5, 9))
    assert leads == []
```

- [ ] **Step 2: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_queue_scanner.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write impl**

```python
# agents/outreach_os/queue_scanner.py
"""Scan agents/<pipeline>/queue/*.md for files generated today."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from . import frontmatter

_SOURCES = {
    "revops": Path("agents/revops_intel/queue"),
    "pe": Path("agents/pe_intel/queue"),
    "reddit_mine": Path("agents/reddit_mine/queue"),
}


def _is_today(fm: dict, today: date) -> bool:
    raw = str(fm.get("generated_at", ""))
    return raw.startswith(today.isoformat())


def scan_today_all(today: date) -> list[dict]:
    out: list[dict] = []
    for source, qdir in _SOURCES.items():
        if not qdir.exists():
            continue
        for path in sorted(qdir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            fm, _body = frontmatter.parse(text)
            if not fm:
                continue
            if not _is_today(fm, today):
                continue
            out.append({"source": source, "path": str(path), "frontmatter": fm})
    return out
```

- [ ] **Step 4: Run, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_queue_scanner.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/queue_scanner.py tests/outreach_os/test_queue_scanner.py
git commit -m "feat(outreach-os): queue scanner for today's leads across pipelines"
```

---

### Task 2.4: `pending_outcomes.py` — read pending leads from each source

**Files:**
- Create: `agents/outreach_os/pending_outcomes.py`
- Test: `tests/outreach_os/test_pending_outcomes.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/outreach_os/test_pending_outcomes.py
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from agents.outreach_os import pending_outcomes


def _bootstrap_revops_db(repo: Path) -> Path:
    db_path = repo / "agents/revops_intel/revops_intel.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE processed_leads (
            post_id TEXT PRIMARY KEY,
            queue_file TEXT NOT NULL,
            processed_at INTEGER NOT NULL,
            posted_at INTEGER,
            outcome TEXT,
            offer_match TEXT
        );
    """)
    eight_days_ago = int((datetime.now() - timedelta(days=8)).timestamp())
    conn.execute(
        "INSERT INTO processed_leads VALUES (?, ?, ?, ?, NULL, ?)",
        ("stale1", "queue/x.md", eight_days_ago, eight_days_ago, "outbound_engine"),
    )
    one_day_ago = int((datetime.now() - timedelta(days=1)).timestamp())
    conn.execute(
        "INSERT INTO processed_leads VALUES (?, ?, ?, ?, NULL, ?)",
        ("fresh1", "queue/y.md", one_day_ago, one_day_ago, "outbound_engine"),
    )
    conn.execute(
        "INSERT INTO processed_leads VALUES (?, ?, ?, ?, ?, ?)",
        ("done1", "queue/z.md", eight_days_ago, eight_days_ago, "responded", "outbound_engine"),
    )
    conn.commit()
    conn.close()
    return db_path


def test_revops_returns_only_stale_pending(tmp_repo_root):
    _bootstrap_revops_db(tmp_repo_root)
    pending = pending_outcomes.fetch_revops(stale_days=7)
    ids = {p["post_id"] for p in pending}
    assert ids == {"stale1"}


def test_revops_returns_empty_when_db_missing(tmp_repo_root):
    pending = pending_outcomes.fetch_revops(stale_days=7)
    assert pending == []


def test_reddit_mine_returns_pending_from_outcomes_json(tmp_repo_root):
    out_path = tmp_repo_root / "agents/reddit_mine/outcomes.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    eight_days_ago = (datetime.now() - timedelta(days=8)).isoformat()
    one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()
    out_path.write_text(f'''{{
        "stalePost": {{"posted_at": "{eight_days_ago}", "outcome": null}},
        "freshPost": {{"posted_at": "{one_day_ago}", "outcome": null}},
        "donePost": {{"posted_at": "{eight_days_ago}", "outcome": "client"}}
    }}''')
    pending = pending_outcomes.fetch_reddit_mine(stale_days=7)
    ids = {p["post_id"] for p in pending}
    assert ids == {"stalePost"}


def test_reddit_mine_returns_empty_when_outcomes_missing(tmp_repo_root):
    pending = pending_outcomes.fetch_reddit_mine(stale_days=7)
    assert pending == []
```

- [ ] **Step 2: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_pending_outcomes.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write impl**

```python
# agents/outreach_os/pending_outcomes.py
"""Read pending-outcome lists from each pipeline's storage.

revops + pe → SQLite processed_leads (outcome IS NULL, posted_at older than threshold)
reddit_mine → agents/reddit_mine/outcomes.json
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

_DB_PATHS = {
    "revops": Path("agents/revops_intel/revops_intel.db"),
    "pe": Path("agents/pe_intel/pe_intel.db"),
}
_REDDIT_OUTCOMES = Path("agents/reddit_mine/outcomes.json")


def _fetch_db(source: str, stale_days: int) -> list[dict]:
    db_path = _DB_PATHS[source]
    if not db_path.exists():
        return []
    cutoff = int((datetime.now() - timedelta(days=stale_days)).timestamp())
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT post_id, queue_file, posted_at, processed_at, offer_match
        FROM processed_leads
        WHERE outcome IS NULL
          AND COALESCE(posted_at, processed_at) <= ?
        """,
        (cutoff,),
    ).fetchall()
    conn.close()
    return [
        {
            "source": source,
            "post_id": r["post_id"],
            "queue_file": r["queue_file"],
            "posted_at": datetime.fromtimestamp(r["posted_at"] or r["processed_at"]).isoformat(timespec="seconds"),
        }
        for r in rows
    ]


def fetch_revops(stale_days: int = 7) -> list[dict]:
    return _fetch_db("revops", stale_days)


def fetch_pe(stale_days: int = 7) -> list[dict]:
    return _fetch_db("pe", stale_days)


def fetch_reddit_mine(stale_days: int = 7) -> list[dict]:
    if not _REDDIT_OUTCOMES.exists():
        return []
    data = json.loads(_REDDIT_OUTCOMES.read_text())
    cutoff = datetime.now() - timedelta(days=stale_days)
    out: list[dict] = []
    for post_id, entry in data.items():
        if entry.get("outcome"):
            continue
        posted_at_raw = entry.get("posted_at")
        if not posted_at_raw:
            continue
        if datetime.fromisoformat(posted_at_raw) > cutoff:
            continue
        out.append({"source": "reddit_mine", "post_id": post_id, "posted_at": posted_at_raw})
    return out


def fetch_all(stale_days: int = 7) -> list[dict]:
    return fetch_revops(stale_days) + fetch_pe(stale_days) + fetch_reddit_mine(stale_days)
```

- [ ] **Step 4: Run, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_pending_outcomes.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/pending_outcomes.py tests/outreach_os/test_pending_outcomes.py
git commit -m "feat(outreach-os): pending-outcome reader for revops/pe/reddit_mine"
```

---

### Task 2.5: `brief.py` — render Daily Brief markdown

**Files:**
- Create: `agents/outreach_os/brief.py`
- Test: `tests/outreach_os/test_brief.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/outreach_os/test_brief.py
from datetime import date

import pytest

from agents.outreach_os import brief


def _lead(source, fm):
    return {"source": source, "path": "queue/x.md", "frontmatter": fm}


def test_render_includes_header_and_date():
    md = brief.render(
        today=date(2026, 5, 9),
        leads=[],
        linkedin=[],
        pending=[],
        pipelines_run=[],
        pipelines_skipped=[],
        pipelines_failed=[],
    )
    assert "# Outreach OS - 2026-05-09" in md
    assert "date: 2026-05-09" in md


def test_render_sorts_by_tier_priority():
    leads = [
        _lead("revops", {"post_id": "warm1", "score": 70, "author": "u/w", "subreddit": "sales"}),
        _lead("revops", {"post_id": "hot1", "score": 92, "author": "u/h", "subreddit": "sales"}),
        _lead("reddit_mine", {"post_id": "auth1", "tier": "AUTHORITY", "author": "u/a", "subreddit": "n8n"}),
    ]
    md = brief.render(
        today=date(2026, 5, 9), leads=leads, linkedin=[], pending=[],
        pipelines_run=["revops", "reddit_mine"], pipelines_skipped=[], pipelines_failed=[],
    )
    hot_idx = md.index("hot1")
    warm_idx = md.index("warm1")
    auth_idx = md.index("auth1")
    assert hot_idx < warm_idx < auth_idx


def test_render_includes_pending_outcome_checkboxes():
    pending = [{"source": "revops", "post_id": "p1", "posted_at": "2026-05-01T12:00:00"}]
    md = brief.render(
        today=date(2026, 5, 9), leads=[], linkedin=[], pending=pending,
        pipelines_run=[], pipelines_skipped=[], pipelines_failed=[],
    )
    assert "Pending outcomes" in md
    assert "p1" in md
    assert "[ ] responded" in md
    assert "[ ] dmd_back" in md
    assert "[ ] ghosted" in md
    assert "[ ] client" in md
    assert "[ ] unsub" in md


def test_render_zero_state_is_explicit():
    md = brief.render(
        today=date(2026, 5, 9), leads=[], linkedin=[], pending=[],
        pipelines_run=[], pipelines_skipped=[], pipelines_failed=[],
    )
    assert "No new leads today" in md


def test_render_includes_linkedin_section():
    linkedin = [
        {"name": "Sarah Chen", "title": "VP RevOps", "company": "Acme", "opener": "Saw your post."},
    ]
    md = brief.render(
        today=date(2026, 5, 9), leads=[], linkedin=linkedin, pending=[],
        pipelines_run=["linkedin"], pipelines_skipped=[], pipelines_failed=[],
    )
    assert "LinkedIn 20" in md
    assert "Sarah Chen" in md
    assert "VP RevOps" in md
    assert "Saw your post." in md


def test_no_em_dashes_in_rendered_brief():
    md = brief.render(
        today=date(2026, 5, 9), leads=[], linkedin=[], pending=[],
        pipelines_run=[], pipelines_skipped=[], pipelines_failed=[],
    )
    assert "—" not in md, "voice rule violation: em-dash in brief"
```

- [ ] **Step 2: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_brief.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write impl**

```python
# agents/outreach_os/brief.py
"""Render the Daily Brief markdown."""
from __future__ import annotations

from datetime import date, datetime
from textwrap import dedent

from . import tier as tier_mod

_TIER_RANK = {"HOT": 0, "WARM": 1, "AUTHORITY": 2}


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
        ### {idx}. {author} - r/{sub} ({lead['source']} - id {pid})
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
        name = item.get("name", "")
        title = item.get("title", "")
        company = item.get("company", "")
        opener = item.get("opener", "")
        lines.append(f"- [ ] **{name}** . {title} @ {company} . \"{opener}\"")
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
```

- [ ] **Step 4: Run, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_brief.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/brief.py tests/outreach_os/test_brief.py
git commit -m "feat(outreach-os): Daily Brief renderer"
```

---

### Task 2.6: `aggregate.py` — CLI entry point

**Files:**
- Create: `agents/outreach_os/aggregate.py`
- Test: `tests/outreach_os/test_aggregate.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/outreach_os/test_aggregate.py
import shutil
from datetime import date
from pathlib import Path

from agents.outreach_os import aggregate


def _seed(repo, fixtures):
    mapping = {
        "revops_queue": "agents/revops_intel/queue",
        "pe_queue": "agents/pe_intel/queue",
        "reddit_mine_queue": "agents/reddit_mine/queue",
    }
    for src, dst in mapping.items():
        for p in (fixtures / src).iterdir():
            (repo / dst).mkdir(parents=True, exist_ok=True)
            shutil.copy(p, repo / dst / p.name)


def test_writes_brief_to_expected_path(tmp_repo_root, fixtures_dir):
    _seed(tmp_repo_root, fixtures_dir)
    out = aggregate.run(today=date(2026, 5, 9))
    assert out == Path("outreach-os/daily/2026-05-09.md")
    assert out.exists()


def test_brief_contains_all_4_leads(tmp_repo_root, fixtures_dir):
    _seed(tmp_repo_root, fixtures_dir)
    aggregate.run(today=date(2026, 5, 9))
    md = (tmp_repo_root / "outreach-os/daily/2026-05-09.md").read_text()
    for pid in ("post1", "post2", "post3", "post4"):
        assert pid in md
```

- [ ] **Step 2: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_aggregate.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write impl**

```python
# agents/outreach_os/aggregate.py
"""CLI entry: build today's Daily Brief.

Usage:
    python -m agents.outreach_os.aggregate
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import brief as brief_mod
from . import pending_outcomes, queue_scanner


def _read_linkedin(today: date) -> list[dict]:
    p = Path(f"agents/outreach_os/linkedin/{today.isoformat()}.md")
    if not p.exists():
        return []
    import json as _json
    import re
    items: list[dict] = []
    for m in re.finditer(r"<!--LEAD\n(.*?)\n-->", p.read_text(), re.DOTALL):
        items.append(_json.loads(m.group(1)))
    return items


def run(*, today: date | None = None) -> Path:
    today = today or date.today()
    leads = queue_scanner.scan_today_all(today=today)
    linkedin = _read_linkedin(today)
    pending = pending_outcomes.fetch_all(stale_days=7)

    md = brief_mod.render(
        today=today,
        leads=leads,
        linkedin=linkedin,
        pending=pending,
        pipelines_run=[],
        pipelines_skipped=[],
        pipelines_failed=[],
    )

    out = Path(f"outreach-os/daily/{today.isoformat()}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    return out


def _cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="ISO date (default: today)")
    args = parser.parse_args()
    today = date.fromisoformat(args.date) if args.date else None
    out = run(today=today)
    print(out)


if __name__ == "__main__":
    _cli()
```

- [ ] **Step 4: Run, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_aggregate.py -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/aggregate.py tests/outreach_os/test_aggregate.py
git commit -m "feat(outreach-os): aggregate CLI builds Daily Brief"
```

---

## Chunk 3: Dashboard

### Task 3.1: `outcome_counts.py` — count outcomes per source over a window

**Files:**
- Create: `agents/outreach_os/outcome_counts.py`
- Test: `tests/outreach_os/test_outcome_counts.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/outreach_os/test_outcome_counts.py
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from agents.outreach_os import outcome_counts


def _db_with(repo: Path, source: str, rows: list[tuple]) -> Path:
    db_path = repo / f"agents/{source}_intel/{source}_intel.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE processed_leads (
            post_id TEXT PRIMARY KEY,
            queue_file TEXT,
            processed_at INTEGER,
            posted_at INTEGER,
            outcome TEXT,
            offer_match TEXT
        );
    """)
    conn.executemany("INSERT INTO processed_leads VALUES (?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    return db_path


def test_count_revops(tmp_repo_root):
    now = int(datetime.now().timestamp())
    rows = [
        ("p1", "q.md", now, now, "responded", "outbound_engine"),
        ("p2", "q.md", now, now, "ghosted", "outbound_engine"),
        ("p3", "q.md", now, now, "client", "outbound_engine"),
        ("p4", "q.md", now, now, "dmd_back", "outbound_engine"),
        ("p5", "q.md", now, now, None, "outbound_engine"),
    ]
    _db_with(tmp_repo_root, "revops", rows)
    counts = outcome_counts.count("revops", window_days=30)
    assert counts == {"sent": 5, "responded": 1, "dmd_back": 1, "ghosted": 1, "client": 1, "unsubscribed": 0}


def test_count_excludes_outside_window(tmp_repo_root):
    forty_days_ago = int((datetime.now() - timedelta(days=40)).timestamp())
    now = int(datetime.now().timestamp())
    rows = [
        ("old", "q.md", forty_days_ago, forty_days_ago, "client", "x"),
        ("new", "q.md", now, now, "client", "x"),
    ]
    _db_with(tmp_repo_root, "pe", rows)
    counts = outcome_counts.count("pe", window_days=30)
    assert counts["sent"] == 1
    assert counts["client"] == 1


def test_count_zero_when_db_missing(tmp_repo_root):
    counts = outcome_counts.count("revops", window_days=30)
    assert counts == {"sent": 0, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 0, "unsubscribed": 0}


def test_count_reddit_mine_from_outcomes_json(tmp_repo_root):
    now = datetime.now().isoformat()
    out = tmp_repo_root / "agents/reddit_mine/outcomes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f'{{"a": {{"posted_at": "{now}", "outcome": "responded"}}, "b": {{"posted_at": "{now}", "outcome": "client"}}}}')
    counts = outcome_counts.count("reddit_mine", window_days=30)
    assert counts["sent"] == 2
    assert counts["responded"] == 1
    assert counts["client"] == 1
```

- [ ] **Step 2: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_outcome_counts.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write impl**

```python
# agents/outreach_os/outcome_counts.py
"""Count outcomes per source over a rolling window."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

OUTCOMES = ("responded", "dmd_back", "ghosted", "client", "unsubscribed")

_DB_PATHS = {
    "revops": Path("agents/revops_intel/revops_intel.db"),
    "pe": Path("agents/pe_intel/pe_intel.db"),
}
_REDDIT_JSON = Path("agents/reddit_mine/outcomes.json")


def _zeros() -> dict[str, int]:
    return {"sent": 0, **{k: 0 for k in OUTCOMES}}


def _count_db(source: str, window_days: int) -> dict[str, int]:
    counts = _zeros()
    db_path = _DB_PATHS[source]
    if not db_path.exists():
        return counts
    cutoff = int((datetime.now() - timedelta(days=window_days)).timestamp())
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """
        SELECT outcome
        FROM processed_leads
        WHERE COALESCE(posted_at, processed_at) >= ?
        """,
        (cutoff,),
    ).fetchall()
    conn.close()
    counts["sent"] = len(rows)
    for (outcome,) in rows:
        if outcome in OUTCOMES:
            counts[outcome] += 1
    return counts


def _count_reddit(window_days: int) -> dict[str, int]:
    counts = _zeros()
    if not _REDDIT_JSON.exists():
        return counts
    cutoff = datetime.now() - timedelta(days=window_days)
    data = json.loads(_REDDIT_JSON.read_text())
    for entry in data.values():
        posted = entry.get("posted_at")
        if not posted:
            continue
        if datetime.fromisoformat(posted) < cutoff:
            continue
        counts["sent"] += 1
        oc = entry.get("outcome")
        if oc in OUTCOMES:
            counts[oc] += 1
    return counts


def count(source: str, *, window_days: int = 30) -> dict[str, int]:
    if source in _DB_PATHS:
        return _count_db(source, window_days)
    if source == "reddit_mine":
        return _count_reddit(window_days)
    raise ValueError(f"unknown source: {source}")
```

- [ ] **Step 4: Run, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_outcome_counts.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/outcome_counts.py tests/outreach_os/test_outcome_counts.py
git commit -m "feat(outreach-os): outcome counter per source"
```

---

### Task 3.2: `win_rate.py` + `verdicts.py` (combined small modules)

**Files:**
- Create: `agents/outreach_os/win_rate.py`
- Create: `agents/outreach_os/verdicts.py`
- Test: `tests/outreach_os/test_win_rate.py`
- Test: `tests/outreach_os/test_verdicts.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/outreach_os/test_win_rate.py
from agents.outreach_os import win_rate


def test_zero_sent_returns_none():
    counts = {"sent": 0, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 0, "unsubscribed": 0}
    assert win_rate.compute(counts) is None


def test_basic_ratio():
    counts = {"sent": 100, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 2, "unsubscribed": 0}
    assert win_rate.compute(counts) == 0.02
```

```python
# tests/outreach_os/test_verdicts.py
from agents.outreach_os import verdicts


def test_picks_best_and_worst():
    rates = {"revops": 0.025, "pe": 0.0, "reddit_mine": 0.03, "linkedin": 0.005}
    v = verdicts.generate(rates)
    assert "reddit_mine" in v["working"][0] or "revops" in v["working"][0]
    assert "pe" in v["not_working"][0] or "linkedin" in v["not_working"][0]


def test_skips_none_values():
    rates = {"revops": None, "pe": 0.01, "reddit_mine": 0.02, "linkedin": 0.005}
    v = verdicts.generate(rates)
    flat = "\n".join(v["working"] + v["not_working"])
    assert "revops" not in flat
```

- [ ] **Step 2: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_win_rate.py tests/outreach_os/test_verdicts.py -v
```

Expected: ImportErrors.

- [ ] **Step 3: Write impls**

```python
# agents/outreach_os/win_rate.py
"""Compute win rate (clients / sent) per source."""
from __future__ import annotations


def compute(counts: dict[str, int]) -> float | None:
    sent = counts.get("sent", 0)
    if sent == 0:
        return None
    return counts.get("client", 0) / sent
```

```python
# agents/outreach_os/verdicts.py
"""Auto-generate 'What's working / What's not' verdicts."""
from __future__ import annotations


def generate(rates: dict[str, float | None]) -> dict[str, list[str]]:
    valid = [(s, r) for s, r in rates.items() if r is not None]
    if not valid:
        return {"working": ["No data yet."], "not_working": []}
    valid.sort(key=lambda x: x[1], reverse=True)
    best_source, best_rate = valid[0]
    worst_source, worst_rate = valid[-1]
    working = [f"{best_source} leads with a {best_rate * 100:.1f}% win rate. Lean into it."]
    not_working = []
    if worst_rate < 0.005 and worst_source != best_source:
        not_working.append(f"{worst_source} is at {worst_rate * 100:.1f}%. Kill or rework after day 30.")
    return {"working": working, "not_working": not_working or ["Nothing flagged for cuts yet."]}
```

- [ ] **Step 4: Run, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_win_rate.py tests/outreach_os/test_verdicts.py -v
```

Expected: 4 tests pass total.

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/win_rate.py agents/outreach_os/verdicts.py tests/outreach_os/test_win_rate.py tests/outreach_os/test_verdicts.py
git commit -m "feat(outreach-os): win rate calculator and auto-verdicts"
```

---

### Task 3.3: `run_history.py` — read last 7 days of brief frontmatter

**Files:**
- Create: `agents/outreach_os/run_history.py`
- Test: `tests/outreach_os/test_run_history.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/outreach_os/test_run_history.py
from datetime import date, timedelta
from pathlib import Path

from agents.outreach_os import run_history


def _write_brief(repo: Path, on_date: date, totals_total: int, pipelines_run: list[str]) -> None:
    p = repo / f"outreach-os/daily/{on_date.isoformat()}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\n"
        f"date: {on_date.isoformat()}\n"
        f"generated_at: {on_date.isoformat()}T07:30:00\n"
        f"totals: {{hot: 0, warm: 0, authority: 0, linkedin: 0, total: {totals_total}}}\n"
        f"pipelines_run: {pipelines_run}\n"
        f"pipelines_skipped: []\n"
        f"pipelines_failed: []\n"
        f"---\nbody"
    )


def test_returns_last_n_days(tmp_repo_root):
    today = date(2026, 5, 9)
    for i in range(8):
        _write_brief(tmp_repo_root, today - timedelta(days=i), i, ["revops"])
    history = run_history.read(today=today, days=7)
    assert len(history) == 7
    assert history[0]["date"] == today.isoformat()


def test_handles_missing_days(tmp_repo_root):
    today = date(2026, 5, 9)
    _write_brief(tmp_repo_root, today, 5, ["revops"])
    history = run_history.read(today=today, days=7)
    assert len(history) == 1
```

- [ ] **Step 2: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_run_history.py -v
```

- [ ] **Step 3: Write impl**

```python
# agents/outreach_os/run_history.py
"""Read the last N days of Daily Brief frontmatter for the dashboard."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from . import frontmatter


def read(*, today: date, days: int = 7) -> list[dict]:
    out: list[dict] = []
    for i in range(days):
        d = today - timedelta(days=i)
        p = Path(f"outreach-os/daily/{d.isoformat()}.md")
        if not p.exists():
            continue
        fm, _ = frontmatter.parse(p.read_text(encoding="utf-8"))
        if not fm:
            continue
        out.append(fm)
    return out
```

- [ ] **Step 4: Run, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_run_history.py -v
```

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/run_history.py tests/outreach_os/test_run_history.py
git commit -m "feat(outreach-os): 7-day brief history reader"
```

---

### Task 3.4: `dashboard.py` — CLI entry

**Files:**
- Create: `agents/outreach_os/dashboard.py`
- Test: `tests/outreach_os/test_dashboard.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/outreach_os/test_dashboard.py
from datetime import date
from pathlib import Path

from agents.outreach_os import dashboard


def test_writes_dashboard_file(tmp_repo_root):
    out = dashboard.run(today=date(2026, 5, 9))
    assert out == Path("outreach-os/dashboard.md")
    assert out.exists()
    text = out.read_text()
    assert "Outreach OS - Dashboard" in text
    assert "30-day stats" in text
    assert "no em-dash check" not in text  # placeholder safety
    assert "—" not in text  # voice rule
```

- [ ] **Step 2: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_dashboard.py -v
```

- [ ] **Step 3: Write impl**

```python
# agents/outreach_os/dashboard.py
"""CLI entry: refresh the dashboard.

Usage:
    python -m agents.outreach_os.dashboard
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from . import outcome_counts, pending_outcomes, run_history, verdicts, win_rate

SOURCES = ("revops", "pe", "reddit_mine", "linkedin")


def _table_row(source: str, c: dict[str, int], rate: float | None) -> str:
    rate_str = f"{rate * 100:.1f}%" if rate is not None else "N/A"
    return (
        f"| {source:<8} | {c['sent']:>4} | {c['responded']:>9} | "
        f"{c['dmd_back']:>9} | {c['client']:>6} | {rate_str:>8} |"
    )


def _stats_table(today: date) -> tuple[str, dict[str, float | None]]:
    rows = ["| Source   | Sent | Responded | DM'd back | Booked | Win rate |",
            "|----------|------|-----------|-----------|--------|----------|"]
    rates: dict[str, float | None] = {}
    totals = {"sent": 0, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 0, "unsubscribed": 0}
    for source in ("revops", "pe", "reddit_mine"):
        c = outcome_counts.count(source, window_days=30)
        for k in totals:
            totals[k] += c[k]
        rates[source] = win_rate.compute(c)
        rows.append(_table_row(source, c, rates[source]))
    # linkedin: there is no DB; we rely on a future linkedin outcomes file. For MVP, zeros.
    linkedin_zero = {"sent": 0, "responded": 0, "dmd_back": 0, "ghosted": 0, "client": 0, "unsubscribed": 0}
    rates["linkedin"] = None
    rows.append(_table_row("linkedin", linkedin_zero, None))
    rows.append(_table_row("Total", totals, win_rate.compute(totals)))
    return "\n".join(rows), rates


def _history_table(today: date) -> str:
    rows = ["| Date | Pipelines run | New leads | Outcomes logged |",
            "|------|---------------|-----------|-----------------|"]
    for fm in run_history.read(today=today, days=7):
        d = fm.get("date", "")
        prun = fm.get("pipelines_run", [])
        total = (fm.get("totals") or {}).get("total", 0)
        rows.append(f"| {d} | {prun} | {total} | (n/a in MVP) |")
    return "\n".join(rows)


def run(*, today: date | None = None) -> Path:
    today = today or date.today()
    stats_md, rates = _stats_table(today)
    pending = pending_outcomes.fetch_all(stale_days=7)
    pending_md = "\n".join(f"- `{p['post_id']}` ({p['source']}) posted {p['posted_at']}" for p in pending) or "(none)"
    v = verdicts.generate(rates)
    history_md = _history_table(today)

    md = (
        "---\n"
        f"last_updated: {datetime.now().isoformat(timespec='seconds')}\n"
        "---\n\n"
        "# Outreach OS - Dashboard\n\n"
        "## 30-day stats\n"
        f"{stats_md}\n\n"
        f"## Outcomes pending >7 days ({len(pending)} leads)\n"
        f"{pending_md}\n\n"
        "## What's working\n"
        + "".join(f"- {line}\n" for line in v["working"])
        + "\n## What's not\n"
        + "".join(f"- {line}\n" for line in v["not_working"])
        + "\n## Last 7 days run history\n"
        f"{history_md}\n"
    )

    out = Path("outreach-os/dashboard.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    return out


def _cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args()
    today = date.fromisoformat(args.date) if args.date else None
    print(run(today=today))


if __name__ == "__main__":
    _cli()
```

- [ ] **Step 4: Run, verify pass**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_dashboard.py -v
```

- [ ] **Step 5: Commit**

```bash
git add agents/outreach_os/dashboard.py tests/outreach_os/test_dashboard.py
git commit -m "feat(outreach-os): dashboard CLI"
```

---

## Chunk 4: LinkedIn rotator

### Task 4.1: Fixture xlsx + `xlsx_loader.py`

**Files:**
- Create: `tests/fixtures/b2b_leads_10.xlsx` (built by a one-shot script in Step 1)
- Create: `agents/outreach_os/xlsx_loader.py`
- Test: `tests/outreach_os/test_xlsx_loader.py`

- [ ] **Step 1: Build the fixture xlsx**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "
from openpyxl import Workbook
wb = Workbook()
ws = wb.active
ws.append(['Name', 'Title', 'Company', 'LinkedIn URL'])
samples = [
    ('Sarah Chen', 'VP RevOps', 'Acme', 'https://linkedin.com/in/sarah'),
    ('Michael Torres', 'Head of Sales Ops', 'Beta', 'https://linkedin.com/in/michael'),
    ('Priya Patel', 'Marketing Lead', 'Gamma', 'https://linkedin.com/in/priya'),
    ('John Smith', 'Director of Revenue Operations', 'Delta', 'https://linkedin.com/in/john'),
    ('Aisha Khan', 'Customer Success Manager', 'Epsilon', 'https://linkedin.com/in/aisha'),
    ('Carlos Rivera', 'Sales Operations Manager', 'Zeta', 'https://linkedin.com/in/carlos'),
    ('Liu Yang', 'Engineering Manager', 'Eta', 'https://linkedin.com/in/liu'),
    ('Maya Brown', 'CFO', 'Theta', 'https://linkedin.com/in/maya'),
    ('Tom Becker', 'RevOps Analyst', 'Iota', 'https://linkedin.com/in/tom'),
    ('Sven Johansson', 'Account Executive', 'Kappa', 'https://linkedin.com/in/sven'),
]
for row in samples:
    ws.append(row)
wb.save('tests/fixtures/b2b_leads_10.xlsx')
print('wrote tests/fixtures/b2b_leads_10.xlsx with 10 rows')
"
```

- [ ] **Step 2: Write failing tests**

```python
# tests/outreach_os/test_xlsx_loader.py
from agents.outreach_os import xlsx_loader


def test_loads_all_rows(fixtures_dir):
    rows = xlsx_loader.load(fixtures_dir / "b2b_leads_10.xlsx")
    assert len(rows) == 10
    assert rows[0]["name"] == "Sarah Chen"
    assert rows[0]["title"] == "VP RevOps"
    assert rows[0]["company"] == "Acme"


def test_columns_lowercased(fixtures_dir):
    rows = xlsx_loader.load(fixtures_dir / "b2b_leads_10.xlsx")
    assert "linkedin_url" in rows[0]
```

- [ ] **Step 3: Run, verify fail**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_xlsx_loader.py -v
```

- [ ] **Step 4: Write impl**

```python
# agents/outreach_os/xlsx_loader.py
"""Load LinkedIn leads from an xlsx file (header row required)."""
from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook


def load(path: Path | str) -> list[dict]:
    wb = load_workbook(filename=str(path), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).strip().lower().replace(" ", "_") for h in rows[0]]
    out = []
    for r in rows[1:]:
        if all(c is None for c in r):
            continue
        out.append({h: (str(v).strip() if v is not None else "") for h, v in zip(headers, r)})
    return out
```

- [ ] **Step 5: Run, verify pass + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_xlsx_loader.py -v
git add tests/fixtures/b2b_leads_10.xlsx agents/outreach_os/xlsx_loader.py tests/outreach_os/test_xlsx_loader.py
git commit -m "feat(outreach-os): xlsx loader for B2B leads"
```

---

### Task 4.2: `icp_bump.py` — sort ICP titles to the front

**Files:**
- Create: `agents/outreach_os/icp_bump.py`
- Test: `tests/outreach_os/test_icp_bump.py`

- [ ] **Step 1: Failing tests**

```python
# tests/outreach_os/test_icp_bump.py
from agents.outreach_os import icp_bump


def test_bumps_revops_title_to_front():
    rows = [
        {"name": "A", "title": "Marketing Lead"},
        {"name": "B", "title": "VP RevOps"},
        {"name": "C", "title": "Engineering Manager"},
        {"name": "D", "title": "Head of Sales Ops"},
    ]
    out = icp_bump.bump(rows)
    assert [r["name"] for r in out[:2]] == ["B", "D"]


def test_preserves_order_within_groups():
    rows = [
        {"name": "A", "title": "Marketing Lead"},
        {"name": "B", "title": "Engineering Manager"},
        {"name": "C", "title": "VP RevOps"},
    ]
    out = icp_bump.bump(rows)
    assert [r["name"] for r in out] == ["C", "A", "B"]


def test_case_insensitive():
    rows = [{"name": "X", "title": "vp REVOPS"}]
    assert icp_bump.bump(rows)[0]["name"] == "X"
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Impl**

```python
# agents/outreach_os/icp_bump.py
"""Sort ICP-matching titles to the front of the rotation."""
from __future__ import annotations

import json
from pathlib import Path

_KEYWORDS = json.loads((Path(__file__).parent / "config.json").read_text())["icp_title_keywords"]


def is_icp(title: str) -> bool:
    t = (title or "").lower()
    return any(kw in t for kw in _KEYWORDS)


def bump(rows: list[dict]) -> list[dict]:
    icp = [r for r in rows if is_icp(r.get("title", ""))]
    rest = [r for r in rows if not is_icp(r.get("title", ""))]
    return icp + rest
```

- [ ] **Step 4: Pass + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_icp_bump.py -v
git add agents/outreach_os/icp_bump.py tests/outreach_os/test_icp_bump.py
git commit -m "feat(outreach-os): ICP-bump sorter for LinkedIn rotation"
```

---

### Task 4.3: `rotation.py` — sequential pointer + state.json

**Files:**
- Create: `agents/outreach_os/rotation.py`
- Test: `tests/outreach_os/test_rotation.py`

- [ ] **Step 1: Failing tests**

```python
# tests/outreach_os/test_rotation.py
from datetime import date
from pathlib import Path

from agents.outreach_os import rotation


def test_first_run_picks_first_n(tmp_repo_root):
    rows = [{"name": str(i), "title": "X", "linkedin_url": f"u{i}"} for i in range(50)]
    picked = rotation.pick(rows, n=20, today=date(2026, 5, 9))
    assert len(picked) == 20
    assert picked[0]["name"] == "0"


def test_second_run_advances_pointer(tmp_repo_root):
    rows = [{"name": str(i), "title": "X", "linkedin_url": f"u{i}"} for i in range(50)]
    rotation.pick(rows, n=20, today=date(2026, 5, 9))
    picked = rotation.pick(rows, n=20, today=date(2026, 5, 10))
    names = {r["name"] for r in picked}
    assert "20" in names
    assert "0" not in names


def test_wrap_around(tmp_repo_root):
    rows = [{"name": str(i), "title": "X", "linkedin_url": f"u{i}"} for i in range(10)]
    rotation.pick(rows, n=8, today=date(2026, 5, 9))
    picked = rotation.pick(rows, n=8, today=date(2026, 5, 10))
    assert len(picked) == 8


def test_state_file_persists(tmp_repo_root):
    rows = [{"name": str(i), "title": "X", "linkedin_url": f"u{i}"} for i in range(50)]
    rotation.pick(rows, n=20, today=date(2026, 5, 9))
    state_path = Path("agents/outreach_os/state.json")
    assert state_path.exists()
    import json
    state = json.loads(state_path.read_text())
    assert state["last_index"] == 20
    assert state["last_run_date"] == "2026-05-09"
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Impl**

```python
# agents/outreach_os/rotation.py
"""Sequential rotation through a static lead list with state persistence."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

_STATE = Path("agents/outreach_os/state.json")


def _load() -> dict:
    if not _STATE.exists():
        return {"last_index": 0, "total_rows": 0, "last_run_date": None, "openers_generated_count": 0}
    return json.loads(_STATE.read_text())


def _save(state: dict) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    _STATE.write_text(json.dumps(state, indent=2))


def pick(rows: list[dict], *, n: int, today: date) -> list[dict]:
    """Pick the next n rows in sequence. Wraps around end of list."""
    state = _load()
    start = state["last_index"]
    total = len(rows)
    state["total_rows"] = total
    if total == 0:
        return []
    end = start + n
    if end <= total:
        picked = rows[start:end]
        new_index = end % total
    else:
        picked = rows[start:total] + rows[: end - total]
        new_index = (end - total) % total
    state["last_index"] = new_index
    state["last_run_date"] = today.isoformat()
    state["openers_generated_count"] += len(picked)
    _save(state)
    return picked
```

- [ ] **Step 4: Pass + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_rotation.py -v
git add agents/outreach_os/rotation.py tests/outreach_os/test_rotation.py
git commit -m "feat(outreach-os): rotation pointer with state.json"
```

---

### Task 4.4: `opener.py` — Haiku call for one personalized opener

**Files:**
- Create: `agents/outreach_os/opener.py`
- Test: `tests/outreach_os/test_opener.py`

- [ ] **Step 1: Failing tests**

```python
# tests/outreach_os/test_opener.py
from unittest.mock import MagicMock

import pytest

from agents.outreach_os import opener


def test_calls_haiku_and_returns_stripped_text(monkeypatch):
    fake_message = MagicMock()
    fake_message.content = [MagicMock(text="Saw your post about Salesforce reporting hell.")]
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_message

    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert out == "Saw your post about Salesforce reporting hell."
    assert fake_client.messages.create.called
    kwargs = fake_client.messages.create.call_args.kwargs
    assert "haiku" in kwargs["model"]


def test_strips_em_dashes_from_response(monkeypatch):
    fake_message = MagicMock()
    fake_message.content = [MagicMock(text="Hey Sarah — thought this might help.")]
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_message

    monkeypatch.setattr(opener, "_client", lambda: fake_client)
    out = opener.generate({"name": "Sarah", "title": "VP RevOps", "company": "Acme"})
    assert "—" not in out
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Impl**

```python
# agents/outreach_os/opener.py
"""Generate one LinkedIn opener via Haiku 4.5."""
from __future__ import annotations

import os

import anthropic

_MODEL = "claude-haiku-4-5-20251001"
_SYSTEM = (
    "You write one-line LinkedIn DM openers that sound like a peer, not a guru. "
    "Hard rules: no em-dashes, no emoji, no compliments, no hyperbole. "
    "Reference the person's role specifically. Output exactly one sentence under 25 words."
)


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def generate(lead: dict) -> str:
    user_msg = (
        f"Name: {lead.get('name', '')}\n"
        f"Title: {lead.get('title', '')}\n"
        f"Company: {lead.get('company', '')}\n\n"
        "Write the opener."
    )
    resp = _client().messages.create(
        model=_MODEL,
        max_tokens=80,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()
    return text.replace("—", ",").replace("--", ",")
```

- [ ] **Step 4: Pass + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_opener.py -v
git add agents/outreach_os/opener.py tests/outreach_os/test_opener.py
git commit -m "feat(outreach-os): Haiku opener generator"
```

---

### Task 4.5: `linkedin_rotator.py` — CLI entry, ties xlsx + bump + rotation + opener

**Files:**
- Create: `agents/outreach_os/linkedin_rotator.py`
- Test: `tests/outreach_os/test_linkedin_rotator.py`

- [ ] **Step 1: Failing tests**

```python
# tests/outreach_os/test_linkedin_rotator.py
import shutil
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from agents.outreach_os import linkedin_rotator


def _seed_xlsx(repo: Path, fixtures: Path) -> None:
    dst = repo / "linkedin-content/B2B AI Agents.xlsx"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixtures / "b2b_leads_10.xlsx", dst)


def test_writes_md_with_n_leads(tmp_repo_root, fixtures_dir, monkeypatch):
    _seed_xlsx(tmp_repo_root, fixtures_dir)
    fake_open = MagicMock(side_effect=lambda lead: f"opener-for-{lead['name']}")
    monkeypatch.setattr(linkedin_rotator, "_generate_opener", fake_open)

    out = linkedin_rotator.run(today=date(2026, 5, 9), n=5)

    assert out == Path(f"agents/outreach_os/linkedin/2026-05-09.md")
    assert out.exists()
    text = out.read_text()
    assert text.count("<!--LEAD") == 5


def test_failed_opener_does_not_block_others(tmp_repo_root, fixtures_dir, monkeypatch):
    _seed_xlsx(tmp_repo_root, fixtures_dir)
    counter = {"n": 0}

    def flaky(lead):
        counter["n"] += 1
        if counter["n"] == 2:
            raise RuntimeError("boom")
        return "ok"

    monkeypatch.setattr(linkedin_rotator, "_generate_opener", flaky)
    out = linkedin_rotator.run(today=date(2026, 5, 9), n=5)
    text = out.read_text()
    assert text.count("<!--LEAD") == 5
    assert "<ERROR" in text
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Impl**

```python
# agents/outreach_os/linkedin_rotator.py
"""CLI entry: build today's LinkedIn 20.

Usage:
    python -m agents.outreach_os.linkedin_rotator
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from . import LINKEDIN_DAILY_CAP, icp_bump, opener, rotation, xlsx_loader

_XLSX = Path("linkedin-content/B2B AI Agents.xlsx")


def _generate_opener(lead: dict) -> str:
    return opener.generate(lead)


def _render(picks: list[dict]) -> str:
    parts = ["# LinkedIn queue\n"]
    for p in picks:
        parts.append(f"<!--LEAD\n{json.dumps(p)}\n-->\n")
        parts.append(f"- **{p.get('name')}** . {p.get('title')} @ {p.get('company')} . \"{p.get('opener')}\"\n")
    return "\n".join(parts)


def run(*, today: date | None = None, n: int = LINKEDIN_DAILY_CAP) -> Path:
    today = today or date.today()
    rows = xlsx_loader.load(_XLSX)
    if not rows:
        out = Path(f"agents/outreach_os/linkedin/{today.isoformat()}.md")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("# LinkedIn queue\n\n(No leads available.)\n", encoding="utf-8")
        return out

    bumped = icp_bump.bump(rows)
    picks = rotation.pick(bumped, n=n, today=today)

    enriched: list[dict] = []
    for lead in picks:
        try:
            opener_text = _generate_opener(lead)
        except Exception as e:
            opener_text = f"<ERROR: {e}>"
        enriched.append({**lead, "opener": opener_text})

    out = Path(f"agents/outreach_os/linkedin/{today.isoformat()}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_render(enriched), encoding="utf-8")
    return out


def _cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--n", type=int, default=LINKEDIN_DAILY_CAP)
    args = parser.parse_args()
    today = date.fromisoformat(args.date) if args.date else None
    print(run(today=today, n=args.n))


if __name__ == "__main__":
    _cli()
```

- [ ] **Step 4: Pass + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_linkedin_rotator.py -v
git add agents/outreach_os/linkedin_rotator.py tests/outreach_os/test_linkedin_rotator.py
git commit -m "feat(outreach-os): LinkedIn rotator CLI"
```

---

## Chunk 5: Outcome flush + reddit_mine outcomes

### Task 5.1: `agents/reddit_mine/outcomes.py`

**Files:**
- Create: `agents/reddit_mine/outcomes.py`
- Test: `tests/reddit_mine/test_outcomes.py`

- [ ] **Step 1: Failing tests**

```python
# tests/reddit_mine/test_outcomes.py
import json
from datetime import datetime
from pathlib import Path

import pytest

from agents.reddit_mine import outcomes


def test_record_creates_file(tmp_repo_root):
    outcomes.record("post1", "responded")
    p = Path("agents/reddit_mine/outcomes.json")
    data = json.loads(p.read_text())
    assert data["post1"]["outcome"] == "responded"
    assert data["post1"]["outcome_logged_at"]


def test_record_initializes_posted_at_if_missing(tmp_repo_root):
    outcomes.record("post1", "responded")
    p = Path("agents/reddit_mine/outcomes.json")
    data = json.loads(p.read_text())
    assert data["post1"]["posted_at"] is not None


def test_record_idempotent_on_same_outcome(tmp_repo_root):
    outcomes.record("post1", "responded")
    p = Path("agents/reddit_mine/outcomes.json")
    first = json.loads(p.read_text())
    outcomes.record("post1", "responded")
    second = json.loads(p.read_text())
    assert first["post1"]["posted_at"] == second["post1"]["posted_at"]


def test_record_invalid_outcome_raises(tmp_repo_root):
    with pytest.raises(ValueError, match="invalid outcome"):
        outcomes.record("post1", "maybe")
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Impl**

```python
# agents/reddit_mine/outcomes.py
"""Outcome state for the reddit_mine pipeline.

Stored at agents/reddit_mine/outcomes.json. One key per post_id.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

VALID_OUTCOMES = {"responded", "dmd_back", "ghosted", "client", "unsubscribed"}
_PATH = Path("agents/reddit_mine/outcomes.json")


def _load() -> dict:
    if not _PATH.exists():
        return {}
    return json.loads(_PATH.read_text())


def _save(data: dict) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(data, indent=2))


def record(post_id: str, outcome: str) -> None:
    if outcome not in VALID_OUTCOMES:
        raise ValueError(f"invalid outcome: {outcome}. allowed: {sorted(VALID_OUTCOMES)}")
    data = _load()
    now = datetime.now().isoformat(timespec="seconds")
    if post_id not in data:
        data[post_id] = {"posted_at": now, "outcome": outcome, "outcome_logged_at": now}
    else:
        if data[post_id].get("outcome") == outcome:
            return  # idempotent
        data[post_id]["outcome"] = outcome
        data[post_id]["outcome_logged_at"] = now
        if not data[post_id].get("posted_at"):
            data[post_id]["posted_at"] = now
    _save(data)
```

- [ ] **Step 4: Pass + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/reddit_mine/test_outcomes.py -v
git add agents/reddit_mine/outcomes.py tests/reddit_mine/test_outcomes.py
git commit -m "feat(reddit_mine): outcomes.json store for /reddit-mine-outcome"
```

---

### Task 5.2: `tickbox.py` — parse outcome checkboxes from a Daily Brief

**Files:**
- Create: `agents/outreach_os/tickbox.py`
- Test: `tests/outreach_os/test_tickbox.py`

- [ ] **Step 1: Failing tests**

```python
# tests/outreach_os/test_tickbox.py
from agents.outreach_os import tickbox


_BRIEF = """
## Pending outcomes (>7 days old)
- [ ] `post1` (revops) posted 2026-05-01T12:00:00
  - [x] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub
- [ ] `post2` (pe) posted 2026-05-01T12:00:00
  - [ ] responded   [ ] dmd_back   [x] ghosted   [ ] client   [ ] unsub
- [ ] `post3` (reddit_mine) posted 2026-05-01T12:00:00
  - [ ] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub
- [ ] `post4` (revops) posted 2026-05-01T12:00:00
  - [x] responded   [x] ghosted   [ ] dmd_back   [ ] client   [ ] unsub

## HOT
nothing here
"""


def test_extracts_ticked_outcomes():
    items = tickbox.parse(_BRIEF)
    by_id = {i["post_id"]: i for i in items}
    assert by_id["post1"]["source"] == "revops"
    assert by_id["post1"]["outcome"] == "responded"
    assert by_id["post2"]["outcome"] == "ghosted"


def test_skips_untagged():
    items = tickbox.parse(_BRIEF)
    ids = {i["post_id"] for i in items}
    assert "post3" not in ids


def test_flags_conflicts():
    items = tickbox.parse(_BRIEF)
    by_id = {i["post_id"]: i for i in items}
    assert by_id["post4"]["conflict"] is True


def test_ignores_unrelated_checkboxes():
    text = """
## HOT
- [ ] Post comment + send DM. Queue file: `q.md`
"""
    items = tickbox.parse(text)
    assert items == []
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Impl**

```python
# agents/outreach_os/tickbox.py
"""Parse outcome tickboxes from a Daily Brief markdown."""
from __future__ import annotations

import re

_LEAD_RE = re.compile(
    r"- \[ \] `(?P<post_id>[^`]+)` \((?P<source>revops|pe|reddit_mine)\) posted [^\n]+\n"
    r"\s+(?P<options>.*)"
)
_OUTCOME_RE = re.compile(r"\[(?P<mark>[ x])\]\s*(?P<name>responded|dmd_back|ghosted|client|unsub)")


def parse(brief_md: str) -> list[dict]:
    out: list[dict] = []
    for m in _LEAD_RE.finditer(brief_md):
        ticked = []
        for om in _OUTCOME_RE.finditer(m.group("options")):
            if om.group("mark") == "x":
                ticked.append(om.group("name"))
        if not ticked:
            continue
        out.append({
            "post_id": m.group("post_id"),
            "source": m.group("source"),
            "outcome": ticked[0],
            "conflict": len(ticked) > 1,
        })
    return out
```

- [ ] **Step 4: Pass + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_tickbox.py -v
git add agents/outreach_os/tickbox.py tests/outreach_os/test_tickbox.py
git commit -m "feat(outreach-os): tickbox parser for Daily Brief outcomes"
```

---

### Task 5.3: `outcome_dispatcher.py` — write outcomes to the right destination

**Files:**
- Create: `agents/outreach_os/outcome_dispatcher.py`
- Test: `tests/outreach_os/test_outcome_dispatcher.py`

- [ ] **Step 1: Failing tests**

```python
# tests/outreach_os/test_outcome_dispatcher.py
import json
import sqlite3
from pathlib import Path

from agents.outreach_os import outcome_dispatcher


def _make_revops_db(repo: Path) -> None:
    p = repo / "agents/revops_intel/revops_intel.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.executescript("""
        CREATE TABLE processed_leads (
            post_id TEXT PRIMARY KEY,
            queue_file TEXT, processed_at INTEGER, posted_at INTEGER, outcome TEXT, offer_match TEXT
        );
    """)
    conn.execute("INSERT INTO processed_leads VALUES ('p1', 'q.md', 0, 0, NULL, 'x')")
    conn.commit(); conn.close()


def test_dispatch_revops_writes_db(tmp_repo_root):
    _make_revops_db(tmp_repo_root)
    outcome_dispatcher.dispatch({"source": "revops", "post_id": "p1", "outcome": "responded", "conflict": False})
    conn = sqlite3.connect("agents/revops_intel/revops_intel.db")
    row = conn.execute("SELECT outcome FROM processed_leads WHERE post_id='p1'").fetchone()
    conn.close()
    assert row[0] == "responded"


def test_dispatch_reddit_mine_writes_json(tmp_repo_root):
    outcome_dispatcher.dispatch({"source": "reddit_mine", "post_id": "p2", "outcome": "client", "conflict": False})
    data = json.loads(Path("agents/reddit_mine/outcomes.json").read_text())
    assert data["p2"]["outcome"] == "client"


def test_dispatch_skips_conflict(tmp_repo_root, capsys):
    out = outcome_dispatcher.dispatch({"source": "revops", "post_id": "p1", "outcome": "responded", "conflict": True})
    assert out is False
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Impl**

```python
# agents/outreach_os/outcome_dispatcher.py
"""Dispatch one parsed tickbox entry to the right outcome store."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from agents.reddit_mine import outcomes as reddit_outcomes

# Tickbox uses "unsub" for brevity. Map to the canonical /revops-outcome vocabulary.
_OUTCOME_MAP = {
    "responded": "responded",
    "dmd_back": "dmd_back",
    "ghosted": "ghosted",
    "client": "client",
    "unsub": "unsubscribed",
}


def _dispatch_db(source: str, post_id: str, outcome: str) -> None:
    db_paths = {
        "revops": Path("agents/revops_intel/revops_intel.db"),
        "pe": Path("agents/pe_intel/pe_intel.db"),
    }
    db_path = db_paths[source]
    if not db_path.exists():
        return
    conn = sqlite3.connect(db_path)
    now = int(time.time())
    conn.execute(
        "UPDATE processed_leads SET outcome = ?, posted_at = COALESCE(posted_at, ?) WHERE post_id = ?",
        (outcome, now, post_id),
    )
    conn.commit()
    conn.close()


def dispatch(entry: dict) -> bool:
    """Write one outcome. Returns True if dispatched, False if skipped."""
    if entry.get("conflict"):
        return False
    canonical = _OUTCOME_MAP.get(entry["outcome"])
    if canonical is None:
        return False
    if entry["source"] in {"revops", "pe"}:
        _dispatch_db(entry["source"], entry["post_id"], canonical)
        return True
    if entry["source"] == "reddit_mine":
        reddit_outcomes.record(entry["post_id"], canonical)
        return True
    return False
```

- [ ] **Step 4: Pass + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_outcome_dispatcher.py -v
git add agents/outreach_os/outcome_dispatcher.py tests/outreach_os/test_outcome_dispatcher.py
git commit -m "feat(outreach-os): outcome dispatcher routes to revops/pe/reddit_mine"
```

---

### Task 5.4: `flush_outcomes.py` — CLI entry

**Files:**
- Create: `agents/outreach_os/flush_outcomes.py`
- Test: `tests/outreach_os/test_flush_outcomes.py`

- [ ] **Step 1: Failing tests**

```python
# tests/outreach_os/test_flush_outcomes.py
import json
import sqlite3
from datetime import date
from pathlib import Path

from agents.outreach_os import flush_outcomes


def _seed(repo: Path):
    db = repo / "agents/revops_intel/revops_intel.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript("CREATE TABLE processed_leads (post_id TEXT PRIMARY KEY, queue_file TEXT, processed_at INTEGER, posted_at INTEGER, outcome TEXT, offer_match TEXT);")
    conn.execute("INSERT INTO processed_leads VALUES ('p1', 'q.md', 0, 0, NULL, 'x')")
    conn.commit(); conn.close()
    brief = repo / f"outreach-os/daily/{date.today().isoformat()}.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text(
        "## Pending outcomes (>7 days old)\n"
        "- [ ] `p1` (revops) posted 2026-05-01T12:00:00\n"
        "  - [x] responded   [ ] dmd_back   [ ] ghosted   [ ] client   [ ] unsub\n"
        "- [ ] `p2` (reddit_mine) posted 2026-05-01T12:00:00\n"
        "  - [x] client   [ ] responded   [ ] dmd_back   [ ] ghosted   [ ] unsub\n"
    )


def test_flush_updates_db_and_json(tmp_repo_root):
    _seed(tmp_repo_root)
    summary = flush_outcomes.run(brief_path=Path(f"outreach-os/daily/{date.today().isoformat()}.md"))
    assert summary["updated"] == 2
    assert summary["unchanged"] == 0
    conn = sqlite3.connect("agents/revops_intel/revops_intel.db")
    assert conn.execute("SELECT outcome FROM processed_leads WHERE post_id='p1'").fetchone()[0] == "responded"
    data = json.loads(Path("agents/reddit_mine/outcomes.json").read_text())
    assert data["p2"]["outcome"] == "client"
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Impl**

```python
# agents/outreach_os/flush_outcomes.py
"""CLI entry: flush outcomes ticked in today's Daily Brief."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import outcome_dispatcher, tickbox


def run(*, brief_path: Path | None = None) -> dict:
    brief_path = brief_path or Path(f"outreach-os/daily/{date.today().isoformat()}.md")
    if not brief_path.exists():
        return {"updated": 0, "unchanged": 0, "conflicts": 0}
    text = brief_path.read_text(encoding="utf-8")
    parsed = tickbox.parse(text)
    updated = 0
    conflicts = 0
    for entry in parsed:
        if entry.get("conflict"):
            conflicts += 1
            continue
        if outcome_dispatcher.dispatch(entry):
            updated += 1
    return {"updated": updated, "unchanged": 0, "conflicts": conflicts}


def _cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief")
    args = parser.parse_args()
    bp = Path(args.brief) if args.brief else None
    summary = run(brief_path=bp)
    print(f"updated: {summary['updated']}, conflicts: {summary['conflicts']}")


if __name__ == "__main__":
    _cli()
```

- [ ] **Step 4: Pass + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_flush_outcomes.py -v
git add agents/outreach_os/flush_outcomes.py tests/outreach_os/test_flush_outcomes.py
git commit -m "feat(outreach-os): flush_outcomes CLI"
```

---

## Chunk 6: Slash commands

Slash commands are Claude Code instructions in `.claude/commands/<name>.md`. They are not unit-testable; they get verified by E2E smokes in Chunk 7 plus manual usage.

### Task 6.1: `/outreach-os`

**Files:**
- Create: `.claude/commands/outreach-os.md`

- [ ] **Step 1: Write the command**

```markdown
---
description: Run the daily client-acquisition stack — invokes /revops-process, /pe-process, /reddit-mine (skipping any that ran today), generates the LinkedIn 20, builds the Daily Brief, and refreshes the Dashboard.
---

You are running `/outreach-os` — the morning entry point for the daily client-acquisition routine.

## Send guardrails (hard rules — read first)
- The MVP only calls the Anthropic API outbound. Never call SMTP, sender SDKs (Smartlead, Instantly, Apollo, Lemlist, Outreach, Mailgun, SendGrid, yagmail, smtplib, aiosmtplib), or platform send APIs (LinkedIn send, Reddit post).
- Uncharted/PitchBook database is not read or referenced anywhere in this command.

## Steps (in order)

### 1. Skip-or-run each upstream pipeline
For each pipeline in this order: `revops`, `pe`, `reddit_mine`:

1. Check the marker:
   ```bash
   "C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "from agents.outreach_os import last_run; import json, sys; print(json.dumps({'ran_today': last_run.ran_today('PIPELINE')}))"
   ```
   (substitute `PIPELINE` with revops / pe / reddit_mine)

2. If `ran_today == true`, log to a running list as `pipelines_skipped` and continue.

3. Else, invoke the corresponding sub-slash-command:
   - revops → `/revops-process`
   - pe → `/pe-process`
   - reddit_mine → `/reddit-mine`

   Use the Task tool. Wait for completion. Capture stderr.

4. On clean completion, write the marker:
   ```bash
   "C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -c "from agents.outreach_os import last_run; last_run.write('PIPELINE', new_leads=N, errors=0)"
   ```
   (substitute N with the lead count from the sub-command's summary).

5. On failure, log to a running list as `pipelines_failed`. Do NOT write a marker. Continue to the next pipeline.

### 2. Generate today's LinkedIn 20

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.linkedin_rotator
```

If this errors, log as `pipelines_failed: linkedin` and continue.

### 3. Aggregate Daily Brief

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.aggregate
```

### 4. Refresh Dashboard

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.dashboard
```

### 5. Print summary

A single table: `pipelines_run`, `pipelines_skipped`, `pipelines_failed`, `total_leads_today`, `pending_outcome_count`. Then point the user to `outreach-os/daily/YYYY-MM-DD.md`.

## Voice rules (hard)
- No em-dashes, no emoji, no guru cadence in any text you generate.

## Guardrails
- Do NOT post anything to Reddit or LinkedIn. The queues are review-only.
- Do NOT send any email.
- Do NOT modify the existing pipelines' source code; only invoke them.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/outreach-os.md
git commit -m "feat(outreach-os): /outreach-os slash command"
```

---

### Task 6.2: `/outreach-status`, `/outreach-flush-outcomes`, `/reddit-mine-outcome`

**Files:**
- Create: `.claude/commands/outreach-status.md`
- Create: `.claude/commands/outreach-flush-outcomes.md`
- Create: `.claude/commands/reddit-mine-outcome.md`

- [ ] **Step 1: Write `outreach-status.md`**

```markdown
---
description: Mid-day cheap visibility check — re-runs aggregate.py and dashboard.py only. No upstream pipelines, no LLM calls.
---

You are running `/outreach-status`.

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.aggregate
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.dashboard
```

Print a one-line summary: total leads in today's brief, pending-outcome count, last-updated timestamp on the dashboard.
```

- [ ] **Step 2: Write `outreach-flush-outcomes.md`**

```markdown
---
description: End-of-day batch outcome update — scans today's Daily Brief for ticked outcome checkboxes and writes them to the right outcome store.
---

You are running `/outreach-flush-outcomes`.

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m agents.outreach_os.flush_outcomes
```

Print the returned summary: `updated: N, conflicts: M`.

If conflicts > 0, list the post_ids that had multiple outcome boxes ticked and ask the user to fix the brief and re-run.
```

- [ ] **Step 3: Write `reddit-mine-outcome.md`**

```markdown
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

(Substitute `__POST_ID__` and `__OUTCOME__` with the actual values from `$ARGUMENTS` — do not run verbatim.)
```

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/outreach-status.md .claude/commands/outreach-flush-outcomes.md .claude/commands/reddit-mine-outcome.md
git commit -m "feat(outreach-os): /outreach-status, /outreach-flush-outcomes, /reddit-mine-outcome slash commands"
```

---

### Task 6.3: Schedule the daily run

**Files:**
- (no new files; uses Claude Code `/schedule` skill)

- [ ] **Step 1: User runs `/schedule` to wire it up**

This step is performed by the user, since the `/schedule` skill is interactive. Document in the project README:

```
After completing the implementation, the user runs:
  /schedule create --cron "30 7 * * *" --command "/outreach-os"

This fires /outreach-os every weekday morning at 7:30 AM local time. The user can edit/disable via /schedule list.
```

- [ ] **Step 2: Commit a project doc**

```bash
git add docs/superpowers/specs/2026-05-09-outreach-os-design.md  # already committed; this is just the docs note
```

(No new commit — the schedule wiring is an operational step, not a code change.)

---

## Chunk 7: E2E smokes + Send guardrail regression test

### Task 7.1: Skip-if-run-today smoke

**Files:**
- Test: `tests/outreach_os/test_smoke_skip_if_run_today.py`

- [ ] **Step 1: Write the smoke**

```python
# tests/outreach_os/test_smoke_skip_if_run_today.py
import pytest
from agents.outreach_os import last_run


@pytest.mark.smoke
def test_marker_round_trip(tmp_repo_root):
    last_run.write("revops", new_leads=3, errors=0)
    assert last_run.ran_today("revops") is True

    # Stale marker
    marker = last_run.marker_path("pe")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"date": "2020-01-01", "finished_at": "2020-01-01T00:00:00", "new_leads": 0, "errors": 0}')
    assert last_run.ran_today("pe") is False
```

- [ ] **Step 2: Run + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_smoke_skip_if_run_today.py -v -m smoke
git add tests/outreach_os/test_smoke_skip_if_run_today.py
git commit -m "test(outreach-os): skip-if-run-today smoke"
```

---

### Task 7.2: Full pipeline smoke

**Files:**
- Test: `tests/outreach_os/test_smoke_outreach_os.py`

- [ ] **Step 1: Write the smoke**

```python
# tests/outreach_os/test_smoke_outreach_os.py
import shutil
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agents.outreach_os import aggregate, dashboard, linkedin_rotator


def _seed(repo: Path, fixtures: Path) -> None:
    mapping = {
        "revops_queue": "agents/revops_intel/queue",
        "pe_queue": "agents/pe_intel/queue",
        "reddit_mine_queue": "agents/reddit_mine/queue",
    }
    for src, dst in mapping.items():
        for p in (fixtures / src).iterdir():
            (repo / dst).mkdir(parents=True, exist_ok=True)
            shutil.copy(p, repo / dst / p.name)
    shutil.copy(fixtures / "b2b_leads_10.xlsx", repo / "linkedin-content/B2B AI Agents.xlsx")


@pytest.mark.smoke
def test_full_run_writes_brief_and_dashboard(tmp_repo_root, fixtures_dir, monkeypatch):
    _seed(tmp_repo_root, fixtures_dir)
    monkeypatch.setattr(linkedin_rotator, "_generate_opener", lambda lead: f"opener-for-{lead['name']}")

    linkedin_rotator.run(today=date(2026, 5, 9), n=5)
    aggregate.run(today=date(2026, 5, 9))
    dashboard.run(today=date(2026, 5, 9))

    brief = Path("outreach-os/daily/2026-05-09.md")
    dash = Path("outreach-os/dashboard.md")
    assert brief.exists()
    assert dash.exists()
    bt = brief.read_text()
    for pid in ("post1", "post2", "post3", "post4"):
        assert pid in bt
    assert "Sarah Chen" in bt or "VP RevOps" in bt
    assert "—" not in bt
    assert "—" not in dash.read_text()
```

- [ ] **Step 2: Run + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_smoke_outreach_os.py -v -m smoke
git add tests/outreach_os/test_smoke_outreach_os.py
git commit -m "test(outreach-os): full pipeline smoke"
```

---

### Task 7.3: Send-guardrail regression test (HARD RULE per spec)

**Files:**
- Test: `tests/outreach_os/test_guardrails.py`

- [ ] **Step 1: Write the regression test**

```python
# tests/outreach_os/test_guardrails.py
"""Send-guardrail regression test (spec section 'Send guardrails', rule #6).

This test fails if any module under agents/outreach_os/ or agents/reddit_mine/
imports a sender SDK while also importing the Uncharted dataset reader.

It also asserts that NO module under those packages currently imports any
sender SDK at all (since Phase 1 doesn't need them).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

SENDER_MODULES = {
    "smtplib", "aiosmtplib", "yagmail",
    "smartlead", "instantly", "apollo", "lemlist",
    "mailgun", "sendgrid", "outreach_io",
}
UNCHARTED_HINTS = {"uncharted", "uncharted_dashboard", "pitchbook"}

SCAN_DIRS = (Path("agents/outreach_os"), Path("agents/reddit_mine"))


def _imports_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module.split(".")[0])
    return out


def _all_py_files() -> list[Path]:
    files: list[Path] = []
    for d in SCAN_DIRS:
        files.extend(d.rglob("*.py"))
    return files


def test_no_sender_sdk_imported_in_phase1():
    offenders: list[tuple[Path, set[str]]] = []
    for f in _all_py_files():
        imports = _imports_in(f)
        bad = imports & SENDER_MODULES
        if bad:
            offenders.append((f, bad))
    assert not offenders, f"Phase 1 must not import sender SDKs. Offenders: {offenders}"


def test_no_module_couples_sender_with_uncharted():
    """Belt-and-braces: even if a sender appears later, it must never co-exist
    with an Uncharted reader in the same module."""
    offenders: list[tuple[Path, set[str], set[str]]] = []
    for f in _all_py_files():
        imports = _imports_in(f)
        senders = imports & SENDER_MODULES
        unchart = {n for n in imports if any(h in n.lower() for h in UNCHARTED_HINTS)}
        if senders and unchart:
            offenders.append((f, senders, unchart))
    assert not offenders, f"Sender SDK + Uncharted reader in same module: {offenders}"
```

- [ ] **Step 2: Run + commit**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_guardrails.py -v
git add tests/outreach_os/test_guardrails.py
git commit -m "test(outreach-os): send-guardrail regression test (spec rule #6)"
```

---

### Task 7.4: Final full-suite run

- [ ] **Step 1: Run everything green-end-to-end**

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest -v
```

Expected: all tests pass. Smoke tests included via the `smoke` marker.

- [ ] **Step 2: If anything failed, fix forward (no destructive resets)**

For each failing test, the fix lives in the module under test. Re-run the failing test only first:

```bash
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe" -m pytest tests/outreach_os/test_<failing>.py -v
```

Commit each fix as its own atomic commit.

- [ ] **Step 3: User runs `/outreach-os` end-to-end manually**

This is the final acceptance test:
1. `/outreach-os` runs from a cold start
2. Brief appears at `outreach-os/daily/<today>.md`
3. Dashboard appears at `outreach-os/dashboard.md`
4. LinkedIn queue MD appears at `agents/outreach_os/linkedin/<today>.md`
5. Tick a couple of outcome boxes in the brief, run `/outreach-flush-outcomes`, verify the dashboard's win-rate row updates after a fresh `/outreach-status`
6. Run `/outreach-os` again the same day; verify each pipeline reports `skipped`

---

## Open dependencies (resolve during execution)

These were flagged in the spec's "Open dependencies" section. Confirm each before/during the relevant task:

1. **`/schedule` skill supports daily slash-command firing.** Verified by user during Task 6.3.
2. **`B2B AI Agents.xlsx` lives at `linkedin-content/B2B AI Agents.xlsx`.** Verified by Glob during plan-writing — confirmed.
3. **`db.update_outcome` is idempotent on second-write.** Verified by reading `agents/revops_intel/db.py:248-258` — it's a plain UPDATE, second-write of the same value is a no-op. Confirmed.
4. **The orchestrator slash command can invoke other slash commands via the Task tool.** This is standard Claude Code behavior. If it turns out it cannot (e.g., harness restriction), fall back: `/outreach-os` prints a numbered list of slash commands for the user to run sequentially, then runs the Python steps that don't depend on sub-slash-commands. The brief will still write with `pipelines_run: []` and the dashboard still updates. Document the fallback in `outreach-os.md` if encountered.

---

## Acceptance criteria (per spec)

- 14 days post-launch: `/outreach-os` runs every weekday morning without manual intervention
- 30 days post-launch: dashboard shows real win rates per source (no `N/A` cells), proving outcome flush is being used
- 60 days post-launch: at least one win-rate-based daily-cap adjustment has been made (concrete proof the dashboard drove a decision)
- 90 days post-launch: at least one new client cited "outreach via [Reddit/LinkedIn] from Outreach OS" as the source

These are not test assertions — they are behavioral milestones tracked separately.
