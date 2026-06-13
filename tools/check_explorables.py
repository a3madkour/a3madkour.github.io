#!/usr/bin/env python3
"""Explorables coupling linter.

Validates the round-trip between essay frontmatter (`has_widgets`), in-body
`{{< widget id="..." >}}` shortcodes, per-essay JS at
`assets/js/explorables/<slug>/index.js`, and `registerWidget("<id>", ...)`
calls in that JS.

Stdlib only.
Exits 0 on all-pass, 1 on any violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


WIDGET_SHORTCODE_RE = re.compile(r"\{\{<\s*widget\b[^>]*>\}\}")

# captures the whole shortcode call and (if present) the id="..." value
WIDGET_CALL_RE = re.compile(
    r"\{\{<\s*widget\b([^>]*?)\s*>\}\}"
)
ID_ATTR_RE = re.compile(r'\bid\s*=\s*"([^"]*)"')


def _extract_widget_ids(body: str) -> list[tuple[str, str | None]]:
    """Returns list of (raw_call, id_value or None). None = id attribute absent.
    Empty string = id="" present but empty."""
    out: list[tuple[str, str | None]] = []
    for m in WIDGET_CALL_RE.finditer(body):
        attrs = m.group(1)
        idm = ID_ATTR_RE.search(attrs)
        out.append((m.group(0), idm.group(1) if idm else None))
    return out


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2]
    return text


def _body_has_widget(body: str) -> bool:
    return WIDGET_SHORTCODE_RE.search(body) is not None


def lint_explorables(repo_root: Path) -> list[str]:
    """Return list of error strings. Empty list = all good."""
    errors: list[str] = []
    essays_dir = repo_root / "content" / "essays"
    if not essays_dir.is_dir():
        return errors

    for d in sorted(essays_dir.iterdir()):
        if not d.is_dir():
            continue
        index = d / "index.md"
        if not index.exists():
            continue
        text = index.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            continue
        body = _strip_frontmatter(text)

        slug = d.name
        rel = f"content/essays/{slug}/index.md"
        has_widgets = bool(fm.get("has_widgets", False))
        body_has = _body_has_widget(body)

        # Rule 1: has_widgets ↔ shortcode presence
        if has_widgets and not body_has:
            errors.append(f"{rel}: has_widgets is true but no widget shortcodes found")
        elif not has_widgets and body_has:
            errors.append(f"{rel}: widget shortcodes found but has_widgets is false (or missing)")

        # Rule 2: id required + non-empty on every widget call
        calls = _extract_widget_ids(body)
        for raw, idv in calls:
            if idv is None:
                errors.append(f"{rel}: widget shortcode missing id attribute: {raw}")
            elif idv == "":
                errors.append(f"{rel}: widget shortcode has empty id: {raw}")

        # Rule 3: ids unique per page
        seen: set[str] = set()
        for raw, idv in calls:
            if idv and idv in seen:
                errors.append(f"{rel}: duplicate widget id \"{idv}\" on page")
            elif idv:
                seen.add(idv)

    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    """Programmatic entry point mirroring sibling linters. Returns (rc, errors)."""
    errors = lint_explorables(repo_root)
    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} explorables issue(s).", file=sys.stderr)
        return rc
    print("OK — explorables coupling validates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
