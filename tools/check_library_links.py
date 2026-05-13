#!/usr/bin/env python3
"""Library cross-reference linter.

Resolves cross-references on `data/{reading,listening,playing,watching}.yaml`:
  - note_slug → content/garden/<slug>/index.md (non-draft)
  - cite_key  → data/citations.yaml entry
  - canonical_url → must be HTTPS or null

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402
from check_citations import parse_citations_yaml  # noqa: E402
from check_library_fixtures import parse_library_yaml  # noqa: E402


LIBRARY_FILES = ["reading.yaml", "listening.yaml", "playing.yaml", "watching.yaml"]


def _garden_slugs(garden_dir: Path) -> set[str]:
    """Return slugs of non-draft garden notes."""
    out: set[str] = set()
    if not garden_dir.is_dir():
        return out
    for d in sorted(garden_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        md = d / "index.md"
        if not md.exists():
            continue
        fm = parse_frontmatter(md.read_text()) or {}
        if bool(fm.get("draft", False)):
            continue
        out.add(d.name)
    return out


def _citation_keys(citations_yaml: Path) -> set[str]:
    if not citations_yaml.exists():
        return set()
    return set(parse_citations_yaml(citations_yaml.read_text()).keys())


def lint_links(repo_root: Path) -> list[str]:
    errors: list[str] = []
    garden_dir = repo_root / "content" / "garden"
    citations = repo_root / "data" / "citations.yaml"
    data_dir = repo_root / "data"

    slugs = _garden_slugs(garden_dir)
    keys = _citation_keys(citations)

    for fname in LIBRARY_FILES:
        path = data_dir / fname
        if not path.exists():
            continue
        items = parse_library_yaml(path.read_text())
        for idx, item in enumerate(items):
            prefix = f"{fname}[{idx}]"
            ns = item.get("note_slug")
            if isinstance(ns, str) and ns and ns not in slugs:
                errors.append(f"{prefix}: note_slug '{ns}' does not resolve to a non-draft garden note")
            ck = item.get("cite_key")
            if isinstance(ck, str) and ck and ck not in keys:
                errors.append(f"{prefix}: cite_key '{ck}' missing from data/citations.yaml")
            url = item.get("canonical_url")
            if url is not None and not (isinstance(url, str) and url.startswith("https://")):
                errors.append(f"{prefix}: canonical_url must be https:// or null, got {url!r}")
    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    errs = lint_links(repo_root)
    return (1 if errs else 0), errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_library_links: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
