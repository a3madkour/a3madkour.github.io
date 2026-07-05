#!/usr/bin/env python3
"""Garden internal-link linter.

Walks `content/garden/<slug>/index.md` (skips `_index.md`), extracts every
`/garden/<target-slug>/` reference from the body, and verifies each target
exists and is non-draft.

Self-references are flagged as warnings (likely typos) but do not fail.

Exits 0 on success, 1 on any unresolved or draft target. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


GARDEN_LINK_RE = re.compile(r"/garden/([a-z0-9][a-z0-9-]*)/")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _is_draft(fm: dict[str, object] | None) -> bool:
    if fm is None:
        return False
    return bool(fm.get("draft", False))


def lint_garden_links(garden_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings).

    Errors fail the build; warnings are advisory.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # First pass: which slugs exist + draft state
    slug_state: dict[str, bool] = {}  # slug -> is_draft
    for d in sorted(garden_dir.iterdir()):
        if not d.is_dir():
            continue
        index = d / "index.md"
        if not index.exists():
            continue
        text = _read(index)
        fm = parse_frontmatter(text)
        slug_state[d.name] = _is_draft(fm)

    # Second pass: validate every reference
    for slug in sorted(slug_state):
        index = garden_dir / slug / "index.md"
        text = _read(index)
        # Strip frontmatter so we only scan the body
        m = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
        body = text[m.end():] if m else text

        seen: set[str] = set()
        for match in GARDEN_LINK_RE.finditer(body):
            target = match.group(1)
            if target in seen:
                continue
            seen.add(target)

            if target == slug:
                warnings.append(
                    f"{slug}/index.md: self-reference to /garden/{target}/ (likely a typo)"
                )
                continue

            if target not in slug_state:
                errors.append(
                    f"{slug}/index.md: link to /garden/{target}/ does not resolve"
                )
                continue

            if slug_state[target]:
                errors.append(
                    f"{slug}/index.md: link to /garden/{target}/ resolves to a draft note"
                )

    return errors, warnings


def run(repo_root: Path) -> tuple[int, list[str]]:
    garden_dir = repo_root / "content" / "garden"
    errors, warnings = lint_garden_links(garden_dir)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    garden_dir = repo_root / "content" / "garden"
    if not garden_dir.is_dir():
        print(f"error: {garden_dir} not found", file=sys.stderr)
        return 1
    rc, errors = run(repo_root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} broken link(s).", file=sys.stderr)
    if rc == 0:
        print(f"OK — verified {len([1 for d in garden_dir.iterdir() if d.is_dir()])} note(s).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
