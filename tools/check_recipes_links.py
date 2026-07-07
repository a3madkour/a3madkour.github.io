#!/usr/bin/env python3
"""Recipe source-URL + video-id well-formedness linter. Stdlib only."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

URL_RE = re.compile(r"^https?://\S+$")
VIDEO_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def lint_file(md: Path) -> list[str]:
    errs: list[str] = []
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return []
    sources = fm.get("sources")
    if isinstance(sources, list):
        for i, s in enumerate(sources):
            if isinstance(s, dict) and s.get("url"):
                if not URL_RE.match(str(s["url"])):
                    errs.append(f"{md}: sources[{i}] url is not a well-formed http(s) URL")
    vid = fm.get("video")
    if vid:
        if not VIDEO_RE.match(str(vid)):
            errs.append(f"{md}: video '{vid}' is not an 11-char YouTube id")
    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    root = repo_root / "content" / "recipes"
    if root.exists():
        for child in sorted(root.iterdir()):
            md = child / "index.md"
            if child.is_dir() and md.exists():
                all_errs.extend(lint_file(md))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    rc, errs = run(Path(__file__).resolve().parent.parent)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_recipes_links: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
