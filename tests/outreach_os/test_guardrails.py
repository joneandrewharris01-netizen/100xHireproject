"""Send-guardrail regression test (spec section 'Send guardrails', rule #6).

Fails if any module under agents/outreach_os/ or agents/reddit_mine/ imports
a sender SDK while also importing the Uncharted dataset reader, OR if any
module under those packages currently imports any sender SDK at all (since
Phase 1 doesn't need them).
"""
from __future__ import annotations

import ast
from pathlib import Path

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
    offenders: list[tuple[Path, set[str], set[str]]] = []
    for f in _all_py_files():
        imports = _imports_in(f)
        senders = imports & SENDER_MODULES
        unchart = {n for n in imports if any(h in n.lower() for h in UNCHARTED_HINTS)}
        if senders and unchart:
            offenders.append((f, senders, unchart))
    assert not offenders, f"Sender SDK + Uncharted reader in same module: {offenders}"
