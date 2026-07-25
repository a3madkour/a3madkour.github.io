#!/usr/bin/env python3
"""Math linter — coupling + scope.

Two invariants, both mirroring what actually renders (Hugo's goldmark
passthrough extension captures the two canonical delimiter pairs, `\\(...\\)`
inline and `\\[...\\]` display; transform.ToMath renders them, and the
`{{< math >}}` shortcode wraps the same pairs):

1. COUPLING (essays) — every essay's `has_math` frontmatter value must match
   whether the body actually contains rendered math. Source-side syntactic
   validation is handled by `org-math-lint` (run pre-publish via a3-pub.sh);
   this site-side check catches deploy-time regressions where frontmatter and
   body fall out of sync (e.g. B.4's has_math auto-derive having a bug).

2. SCOPE (everything else) — math is an essays-only feature: the KaTeX
   stylesheet is loaded only on has_math pages, and only the essays schema
   carries that flag. But the passthrough extension is enabled site-wide, so
   math authored in any other section WOULD render (unstyled, no fonts) with no
   build error. This check fails CI if rendered-math markers appear outside
   content/essays/, so unstyled non-essay math can never ship. Extending math to
   another section = add has_math to that schema and drop it from SCOPE_SKIP.

Detection requires MATCHED delimiters (a `\\[` with a following `\\]`), so
unpaired look-alikes — e.g. the poems' `\\[00:99]` synced-lyric timestamps,
which have no closing `\\]` and so are never captured as math — do not trip it.

Stdlib only.
Exits 0 on all-pass, 1 on any violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


# Rendered-math markers — EXACTLY what the passthrough extension captures and
# transform.ToMath renders, so this stays in lockstep with real output. Matched
# delimiter pairs only (non-greedy, DOTALL for multi-line display blocks); the
# `{{< math >}}` / `{{% math %}}` shortcode wraps the same pairs.
MARKER_PATTERNS = [
    re.compile(r"\\\(.*?\\\)", re.DOTALL),   # inline  \( ... \)
    re.compile(r"\\\[.*?\\\]", re.DOTALL),   # display \[ ... \]
    re.compile(r"\{\{[<%]\s*math\b"),        # {{< math >}} shortcode
]

# Match ``` or ~~~ fences, including leading indentation (up to 3 spaces of
# Markdown indent, or the deeper indent used inside list items).
CODE_FENCE = re.compile(r"^[ \t]*(?:```|~~~)", re.MULTILINE)

# Content sections that carry has_math (and load KaTeX CSS). Anything else is
# scanned by the SCOPE check and must be math-free.
SCOPE_SKIP = {"essays"}


def _strip_code_fences(body: str) -> str:
    """Remove ```-fenced code blocks. Split on lines starting with ``` and keep
    only segments at even indices (text segments) — odd indices are inside fences."""
    segments = CODE_FENCE.split(body)
    return "\n".join(segments[::2])


def _extract_body(text: str) -> str:
    """Return the markdown body (frontmatter stripped)."""
    return text.split("---", 2)[-1] if text.startswith("---") else text


def _body_has_math(body: str) -> bool:
    stripped = _strip_code_fences(body)
    return any(pat.search(stripped) for pat in MARKER_PATTERNS)


def lint_coupling(essays_dir: Path) -> list[str]:
    """has_math ↔ body-math coupling for essays. Empty list = all good."""
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
        body_has = _body_has_math(_extract_body(text))
        rel = f"content/essays/{d.name}/index.md"
        if has_math and not body_has:
            errors.append(f"{rel}: has_math is true but no math markers found in body")
        elif not has_math and body_has:
            errors.append(f"{rel}: math markers found in body but has_math is false (or missing)")
    return errors


def lint_scope(content_dir: Path) -> list[str]:
    """Math is essays-only: flag rendered-math markers anywhere outside the
    sections in SCOPE_SKIP. Empty list = all good."""
    errors: list[str] = []
    if not content_dir.is_dir():
        return errors
    for md in sorted(content_dir.rglob("*.md")):
        rel_parts = md.relative_to(content_dir).parts
        section = rel_parts[0] if rel_parts else ""
        if section in SCOPE_SKIP:
            continue
        body = _extract_body(md.read_text(encoding="utf-8"))
        if _body_has_math(body):
            rel = md.relative_to(content_dir.parent)
            errors.append(
                f"{rel}: math markers found outside essays — math is an "
                f"essays-only feature (no KaTeX CSS loads elsewhere). Add "
                f"has_math to this section's schema to extend math to it."
            )
    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    content_dir = repo_root / "content"
    errors = lint_coupling(content_dir / "essays") + lint_scope(content_dir)
    return (1 if errors else 0, errors)


def main() -> int:
    rc, errors = run(Path(__file__).resolve().parent.parent)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} math issue(s).", file=sys.stderr)
    if rc == 0:
        print("OK — math frontmatter coupling + essays-only scope validate.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
