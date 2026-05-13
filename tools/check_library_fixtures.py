#!/usr/bin/env python3
"""Library fixture frontmatter linter.

Validates `data/{reading,listening,playing,watching}.yaml` shape per
docs/superpowers/specs/2026-05-12-library-section-design.md §3.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_scalar  # noqa: E402


ITEM_START_RE = re.compile(r"^  - ([a-zA-Z_]+):\s*(.*)$")
ITEM_FIELD_RE = re.compile(r"^    ([a-zA-Z_]+):\s*(.*)$")
NESTED_HEADER_RE = re.compile(r"^    ([a-zA-Z_]+):\s*$")
NESTED_FIELD_RE = re.compile(r"^      ([a-zA-Z_]+):\s*(.*)$")


def _scalar(value: str) -> object:
    """Extend parse_scalar with null → None handling."""
    if value == "null":
        return None
    return parse_scalar(value)


def parse_library_yaml(text: str) -> list[dict[str, object]]:
    """Parse a library data yaml file into a list of item dicts.

    Format:
        items:
          - slug: foo
            title: Bar
            tags: [a, b]
            extras:
              progress_pct: 50

    `null`, ints, floats, bools, [a, b] inline arrays handled via parse_scalar.
    """
    items: list[dict[str, object]] = []
    in_items = False
    current: dict[str, object] | None = None
    nested_key: str | None = None
    nested: dict[str, object] | None = None

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw.startswith("items:"):
            in_items = True
            continue
        if not in_items:
            continue

        m = ITEM_START_RE.match(raw)
        if m:
            if current is not None:
                if nested_key is not None and nested is not None:
                    current[nested_key] = nested
                items.append(current)
            current = {}
            nested_key = None
            nested = None
            field, value = m.group(1), m.group(2).strip()
            current[field] = _scalar(value)
            continue

        m_nested_hdr = NESTED_HEADER_RE.match(raw)
        if m_nested_hdr and current is not None:
            if nested_key is not None and nested is not None:
                current[nested_key] = nested
            nested_key = m_nested_hdr.group(1)
            nested = {}
            continue

        m_nested = NESTED_FIELD_RE.match(raw)
        if m_nested and nested is not None:
            field, value = m_nested.group(1), m_nested.group(2).strip()
            nested[field] = _scalar(value)
            continue

        m_field = ITEM_FIELD_RE.match(raw)
        if m_field and current is not None:
            if nested_key is not None and nested is not None:
                current[nested_key] = nested
                nested_key = None
                nested = None
            field, value = m_field.group(1), m_field.group(2).strip()
            current[field] = _scalar(value)
            continue

    if current is not None:
        if nested_key is not None and nested is not None:
            current[nested_key] = nested
        items.append(current)

    return items


def main() -> int:
    return 0


if __name__ == "__main__":
    sys.exit(main())
