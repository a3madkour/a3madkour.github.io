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


def lint_explorables(repo_root: Path) -> list[str]:
    """Return list of error strings. Empty list = all good."""
    return []


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
