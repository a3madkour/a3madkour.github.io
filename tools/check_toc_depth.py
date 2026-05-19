#!/usr/bin/env python3
"""Essay TOC-depth linter.

Guards the invariant that at least one non-draft essay fixture exercises a
deep (>=3 distinct heading levels) table of contents, so the collapsible-
subsection TOC behaviour stays exercised. If every essay flattens to <3
levels the collapse feature has nothing to act on and no test of it.

Counts ATX headings h2-h6 (Hugo markup.tableOfContents startLevel is 2, so
h1 / page title is irrelevant). Fenced code blocks are stripped first so a
`### ...` inside a ``` block is not miscounted.

Exits 0 on all-pass, 1 on violation. Stdlib only.
"""
from __future__ import annotations

import re
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
DRAFT_RE = re.compile(r"^draft:\s*(true|false)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^\s*```")   # CommonMark: closing fences may indent 0–3 spaces
HEADING_RE = re.compile(r"^(#{2,6})\s+\S")  # ATX headings must be at column 0
MIN_DISTINCT_LEVELS = 3


def strip_frontmatter(text: str) -> tuple[bool, str]:
    """Return (is_draft, body). Missing draft key counts as not-draft."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return (False, text)
    fm = m.group(1)
    dm = DRAFT_RE.search(fm)
    is_draft = bool(dm and dm.group(1) == "true")
    return (is_draft, text[m.end():])


def distinct_heading_levels(body: str) -> set[int]:
    """Distinct ATX heading levels h2-h6, ignoring fenced code blocks."""
    levels: set[int] = set()
    in_fence = False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        hm = HEADING_RE.match(line)
        if hm:
            levels.add(len(hm.group(1)))
    return levels


def run(repo_root: Path) -> tuple[int, list[str]]:
    essays_dir = repo_root / "content" / "essays"
    if not essays_dir.exists():
        return (0, [])

    non_draft_essays = 0
    deepest = 0
    for essay_dir in sorted(essays_dir.iterdir()):
        if not essay_dir.is_dir():
            continue
        md = essay_dir / "index.md"
        if not md.exists():
            continue
        is_draft, body = strip_frontmatter(md.read_text())
        if is_draft:
            continue
        non_draft_essays += 1
        deepest = max(deepest, len(distinct_heading_levels(body)))

    if non_draft_essays == 0:
        return (0, [])
    if deepest < MIN_DISTINCT_LEVELS:
        return (
            1,
            [
                "no non-draft essay reaches >=3 distinct heading levels "
                f"(deepest is {deepest}); the collapsible-subsection TOC "
                "needs a fixture with h2>h3>h4 to stay exercised"
            ],
        )
    return (0, [])


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("TOC-depth lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("TOC-depth linter passes (a deep-TOC essay fixture exists).")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
