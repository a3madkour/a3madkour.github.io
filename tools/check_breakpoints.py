#!/usr/bin/env python3
"""Breakpoint discipline linter (R6.2).

Desktop breakpoints were one-off values with no shared vocabulary, and JS
mirrored two of them (`RAIL_BREAKPOINT=1100`, `MOBILE_BREAKPOINT=720`) as magic
numbers that hand-synced with CSS by luck. CSS `@media` can't read `var()`, so
there are no runtime breakpoint tokens; instead this linter enforces a
documented canonical scale and fails CI on CSS↔JS drift.

Scope: only width features INSIDE `@media` preludes are breakpoints — element
`min-width`/`max-width` declarations are ignored. JS `*_BREAKPOINT` constants and
`matchMedia` width literals must be canonical (JS must not reference the CSS-only
per-component allowlist values).

By design the CSS scan matches only `min-width`/`max-width` in `px`; exact
`(width: Npx)`, MQ4 range syntax (`width >= Npx`), and non-px units are outside
scope (none exist in this codebase). Extend the regex if that changes.

Stdlib only. Exits 0 when every breakpoint is canonical / allowlisted / a seam,
1 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# The documented canonical breakpoint scale (px).
CANONICAL: set[int] = {480, 600, 720, 960, 1100, 1280}

# CSS-only per-component exceptions, kept literal. New additions need a reason.
CSS_ALLOWLIST: dict[int, str] = {
    800: ".home-hero reflow",
    900: ".essay-grid bento reflow",
    1140: ".essay-figure.wide constrain",
    1219: ".page-sidebar rail hide",
}

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
# @media prelude text up to the opening brace.
MEDIA_PRELUDE_RE = re.compile(r"@media([^{]*)\{")
# A width feature within a prelude.
WIDTH_FEATURE_RE = re.compile(r"(min-width|max-width)\s*:\s*(\d+)px")
# JS: `NAME_BREAKPOINT = <int>` and matchMedia `(min|max-width: <int>px)`.
JS_BREAKPOINT_CONST_RE = re.compile(r"\b[A-Z][A-Z0-9_]*BREAKPOINT\b\s*=\s*(\d+)")
JS_MATCHMEDIA_WIDTH_RE = re.compile(r"\((?:min|max)-width:\s*(\d+)px\)")


def _css_valid(feature: str, value: int) -> bool:
    if value in CANONICAL or value in CSS_ALLOWLIST:
        return True
    if feature == "max-width" and (value + 1) in CANONICAL:
        return True  # seam partner (max = min - 1)
    return False


def check_css(css: str) -> list[str]:
    """Flag @media width features outside canonical / allowlist / seam. Element
    min/max-width declarations are ignored (only @media preludes are scanned)."""
    css = BLOCK_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), css)
    errors: list[str] = []
    for pm in MEDIA_PRELUDE_RE.finditer(css):
        prelude, base = pm.group(1), pm.start(1)
        for wm in WIDTH_FEATURE_RE.finditer(prelude):
            feature, value = wm.group(1), int(wm.group(2))
            if not _css_valid(feature, value):
                lineno = css.count("\n", 0, base + wm.start()) + 1
                errors.append(
                    f"main.css:{lineno}: non-canonical @media breakpoint "
                    f"{feature}: {value}px — use the canonical scale "
                    f"(480/600/720/960/1100/1280) or add a documented allowlist entry"
                )
    return errors


def _strip_js_comments(js: str) -> str:
    js = BLOCK_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), js)
    return LINE_COMMENT_RE.sub("", js)


def check_js_text(rel: str, js: str) -> list[str]:
    """Flag JS *_BREAKPOINT constants and matchMedia width literals that aren't
    canonical. Comments are stripped so commented/cross-ref lines don't match."""
    js = _strip_js_comments(js)
    errors: list[str] = []
    for m in JS_BREAKPOINT_CONST_RE.finditer(js):
        value = int(m.group(1))
        if value not in CANONICAL:
            lineno = js.count("\n", 0, m.start()) + 1
            errors.append(
                f"{rel}:{lineno}: *_BREAKPOINT = {value} is not a canonical "
                f"breakpoint (480/600/720/960/1100/1280)"
            )
    for m in JS_MATCHMEDIA_WIDTH_RE.finditer(js):
        value = int(m.group(1))
        if value not in CANONICAL:
            lineno = js.count("\n", 0, m.start()) + 1
            errors.append(
                f"{rel}:{lineno}: matchMedia width {value}px is not a canonical "
                f"breakpoint (480/600/720/960/1100/1280)"
            )
    return errors


def run(repo_root: Path) -> tuple[int, list[str]]:
    css_path = repo_root / "assets" / "css" / "main.css"
    if not css_path.exists():
        return (1, [f"main.css not found at {css_path}"])
    errors = check_css(css_path.read_text(encoding="utf-8"))
    js_dir = repo_root / "assets" / "js"
    if js_dir.exists():
        for js_path in sorted(js_dir.rglob("*.js")):
            if "vendor" in js_path.parts:
                continue
            rel = js_path.relative_to(repo_root).as_posix()
            errors += check_js_text(rel, js_path.read_text(encoding="utf-8"))
    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} non-canonical breakpoint(s).", file=sys.stderr)
        return rc
    print("OK — every @media + JS breakpoint is canonical, allowlisted, or a seam.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
