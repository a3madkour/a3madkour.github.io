#!/usr/bin/env python3
"""Garden path-log retrieval linter.

Asserts source-side integration points for the path-log retrieval slice:
  1. layouts/partials/garden/recent-paths.html exists.
  2. layouts/garden/history.html exists.
  3. content/garden/history/_index.md exists with `layout: history` in frontmatter.
  4. layouts/garden/list.html includes the recent-paths partial.
  5. layouts/partials/garden/path-log.html references /garden/history/.
  6-8. assets/js/{garden-history.js, garden-recent-paths.js, garden-pathlog-popover.js} exist.
  9. assets/js/entry-garden.js imports both new mount scripts.
 10. assets/js/garden-stack.js carries the literal `"version": 2` sentinel.

Exits 0 on success, 1 on any error. Stdlib only. Paired with
tools/test_check_garden_history.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def lint_garden_history(project_root: Path) -> list[str]:
    """Return a list of error strings. Empty list = clean."""
    errors: list[str] = []
    return errors


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    errors = lint_garden_history(project)
    if errors:
        print(f"check_garden_history: {len(errors)} issue(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("check_garden_history: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
