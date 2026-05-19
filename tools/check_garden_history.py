#!/usr/bin/env python3
"""Garden path-log retrieval linter.

Asserts source-side integration points for the path-log retrieval slice:
  1. layouts/partials/garden/recent-paths.html exists.
  2. layouts/garden/history.html exists.
  3. content/garden/history/_index.md exists with `layout: history` in frontmatter.
  4. layouts/garden/list.html includes the recent-paths partial.
  5. layouts/partials/graph-launcher-bar.html references /garden/history/
     (the garden branch of the shared launcher bar; path-log.html delegates
     to it).
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

    # 1-3: required new files
    must_exist = [
        ("layouts/partials/garden/recent-paths.html", "widget partial"),
        ("layouts/garden/history.html", "history page layout"),
        ("content/garden/history/_index.md", "history page content"),
    ]
    for rel, desc in must_exist:
        if not (project_root / rel).is_file():
            errors.append(f"{rel}: missing ({desc})")

    # Frontmatter check on _index.md
    idx = project_root / "content/garden/history/_index.md"
    if idx.is_file():
        text = idx.read_text(encoding="utf-8")
        if "layout: history" not in text:
            errors.append(f"content/garden/history/_index.md: missing 'layout: history' in frontmatter")

    # 4: list.html includes recent-paths partial
    list_html = project_root / "layouts/garden/list.html"
    if list_html.is_file():
        text = list_html.read_text(encoding="utf-8")
        if "garden/recent-paths" not in text:
            errors.append("layouts/garden/list.html: does not include partials/garden/recent-paths.html")
    else:
        errors.append("layouts/garden/list.html: missing")

    # 5: the shared launcher bar (garden branch) links to /garden/history/
    launcher = project_root / "layouts/partials/graph-launcher-bar.html"
    if launcher.is_file():
        text = launcher.read_text(encoding="utf-8")
        if "/garden/history/" not in text:
            errors.append("layouts/partials/graph-launcher-bar.html: missing chrome link to /garden/history/")
    else:
        errors.append("layouts/partials/graph-launcher-bar.html: missing")

    # 6-8: new JS modules
    for rel in (
        "assets/js/garden-history.js",
        "assets/js/garden-recent-paths.js",
        "assets/js/garden-pathlog-popover.js",
    ):
        if not (project_root / rel).is_file():
            errors.append(f"{rel}: missing")

    # 9: entry-garden.js imports both mount scripts
    entry = project_root / "assets/js/entry-garden.js"
    if entry.is_file():
        text = entry.read_text(encoding="utf-8")
        if not re.search(r"import\s+['\"]\.\/garden-recent-paths", text):
            errors.append("assets/js/entry-garden.js: missing import of './garden-recent-paths'")
        if not re.search(r"import\s+['\"]\.\/garden-pathlog-popover", text):
            errors.append("assets/js/entry-garden.js: missing import of './garden-pathlog-popover'")
    else:
        errors.append("assets/js/entry-garden.js: missing")

    # 10: garden-stack.js carries the v2 schema sentinel
    stack = project_root / "assets/js/garden-stack.js"
    if stack.is_file():
        text = stack.read_text(encoding="utf-8")
        if '"version": 2' not in text:
            errors.append('assets/js/garden-stack.js: missing v2 schema sentinel (expected literal \'"version": 2\')')
    else:
        errors.append("assets/js/garden-stack.js: missing")

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
