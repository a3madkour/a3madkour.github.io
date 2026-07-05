#!/usr/bin/env python3
"""Math frontmatter coupling linter.

Validates that every essay's `has_math` frontmatter value matches whether
the rendered markdown body actually contains math markers. Source-side
syntactic validation is handled by `org-math-lint` (run pre-publish via
a3-pub.sh); this site-side check catches deploy-time regressions where
the frontmatter and the body fall out of sync (e.g., B.4's has_math
auto-derive having a bug).

Stdlib only.
Exits 0 on all-pass, 1 on any violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


# Math markers recognized:
#   \(   inline LaTeX
#   \[   display LaTeX
#   \begin{...}  environment-based math
#   $$   display dollar (defense-in-depth; org-math-lint canonicalizes away)
# Inline single-$ recognition is handled by a separate dollar-pair test to
# avoid false-positives on prose with money amounts ($5, $10/mo, $100).
MARKER_PATTERNS = [
    re.compile(r"\\\("),
    re.compile(r"\\\["),
    re.compile(r"\\begin\{[a-zA-Z]+\*?\}"),
    re.compile(r"\$\$"),
]

# Inline dollar: a $-delimited token where the inner content looks like math
# (one or more non-space chars without an intervening digit-only prose hit).
# Conservative: require non-space immediately after the opening $, and a
# closing $ on the same line. Skips bare "$5" / "$10/mo" because the regex
# requires a closing $ before end-of-line/whitespace.
INLINE_DOLLAR = re.compile(r"\$[^\s\d$][^$\n]*\$")

# Match ``` or ~~~ fences, including leading indentation (up to 3 spaces of
# Markdown indent, or the deeper indent used inside list items).
CODE_FENCE = re.compile(r"^[ \t]*(?:```|~~~)", re.MULTILINE)


def _strip_code_fences(body: str) -> str:
    """Remove ```-fenced code blocks. Split on lines starting with ``` and keep
    only segments at even indices (text segments) — odd indices are inside fences."""
    segments = CODE_FENCE.split(body)
    return "\n".join(segments[::2])


def _body_has_math(body: str) -> bool:
    stripped = _strip_code_fences(body)
    for pat in MARKER_PATTERNS:
        if pat.search(stripped):
            return True
    if INLINE_DOLLAR.search(stripped):
        return True
    return False


def lint_math(essays_dir: Path) -> list[str]:
    """Return list of error strings. Empty list = all good."""
    errors: list[str] = []
    if not essays_dir.is_dir():
        return errors  # nothing to lint
    for d in sorted(essays_dir.iterdir()):
        if not d.is_dir():
            continue
        index = d / "index.md"
        if not index.exists():
            continue
        text = index.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            continue  # no frontmatter to check against
        has_math = bool(fm.get("has_math", False))
        body = text.split("---", 2)[-1] if text.startswith("---") else text
        body_has = _body_has_math(body)
        rel = f"content/essays/{d.name}/index.md"
        if has_math and not body_has:
            errors.append(f"{rel}: has_math is true but no math markers found in body")
        elif not has_math and body_has:
            errors.append(f"{rel}: math markers found in body but has_math is false (or missing)")
    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    essays_dir = repo_root / "content" / "essays"
    errors = lint_math(essays_dir)
    return (1 if errors else 0, errors)


def main() -> int:
    rc, errors = run(Path(__file__).resolve().parent.parent)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} math coupling issue(s).", file=sys.stderr)
    if rc == 0:
        print("OK — math frontmatter coupling validates.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
