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
