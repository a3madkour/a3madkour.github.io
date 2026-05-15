#!/usr/bin/env python3
"""Icon attribution linter.

Asserts that every SVG under `assets/images/icons/` either carries the
canonical Lucide attribution header comment OR is listed in the exceptions
manifest. Also asserts THIRD_PARTY.md exists and mentions Lucide.

Exits 0 on success, 1 on any error. Stdlib only. Paired with
tools/test_check_icon_attribution.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HEADER_PATTERN = re.compile(
    r"<!--\s*Lucide\s+v[\d.]+\s+—\s+[\w-]+\s+·\s+ISC License\s+·\s+see\s+/THIRD_PARTY\.md\s*-->",
    re.IGNORECASE,
)


def _parse_exceptions(yaml_path: Path) -> set[str]:
    """Tiny YAML reader — we only need a flat list of `file:` keys."""
    if not yaml_path.exists():
        return set()
    files: set[str] = set()
    in_list = False
    for raw in yaml_path.read_text().splitlines():
        line = raw.rstrip()
        if line.strip().startswith("#") or not line.strip():
            continue
        if line.strip() == "exceptions:" or line.strip().startswith("exceptions:"):
            in_list = True
            continue
        if not in_list:
            continue
        m = re.match(r"\s*-\s*file:\s*(.+?)\s*$", line)
        if m:
            files.add(m.group(1).strip().strip('"').strip("'"))
    return files


def lint_icon_attribution(project_root: Path) -> list[str]:
    errors: list[str] = []

    # 1. THIRD_PARTY.md must exist and mention Lucide
    tp = project_root / "THIRD_PARTY.md"
    if not tp.exists():
        errors.append("THIRD_PARTY.md is missing at repo root")
    else:
        body = tp.read_text()
        if "lucide" not in body.lower():
            errors.append("THIRD_PARTY.md exists but does not mention Lucide")

    # 2. Every SVG under assets/images/icons/ must carry the header OR be in exceptions
    icons_dir = project_root / "assets" / "images" / "icons"
    if not icons_dir.exists():
        errors.append("assets/images/icons/ directory is missing")
        return errors

    exceptions = _parse_exceptions(project_root / "tools" / ".icon-attribution-exceptions.yaml")

    for svg in sorted(icons_dir.rglob("*.svg")):
        rel = svg.relative_to(icons_dir).as_posix()
        if rel in exceptions or svg.name in exceptions:
            continue
        head = svg.read_text()[:512]
        if not HEADER_PATTERN.search(head):
            errors.append(f"{svg.relative_to(project_root)}: missing Lucide attribution header (first 512 bytes)")

    return errors


if __name__ == "__main__":
    errors = lint_icon_attribution(Path(__file__).resolve().parent.parent)
    for e in errors:
        print(e)
    sys.exit(1 if errors else 0)
