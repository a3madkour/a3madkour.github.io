#!/usr/bin/env python3
"""Spacing-token discipline linter (R6.1).

`assets/css/main.css` uses a 12-step `--space-*` scale for layout rhythm. This
linter fails if any in-scope spacing declaration (`gap`/`row-gap`/`column-gap`/
`padding*`/`margin*`) carries a bare rem literal instead of a `var(--space-*)`
reference, so magic-number spacing can't re-accrete.

Allowlisted sub-0.25rem micro-nudges (hairline border/alignment tweaks, not
rhythm) may remain literal. Note 0.2rem / 0.3rem are NOT allowlisted — they snap
to --space-3xs.

Stdlib only. Exits 0 when every in-scope rem is tokenized or allowlisted, 1
otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Sub-0.25rem micro-nudges (hairline border/alignment tweaks, ≤ ~2.4px) that
# stay literal — the design's "leave micro-nudges alone" rule (see spec R6.1).
# 0.0625rem (1px) and 0.12rem (~1.9px) are the same class as 0.125rem.
ALLOWLIST: set[float] = {0.02, 0.05, 0.0625, 0.1, 0.12, 0.125, 0.15}

COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
# In-scope property at a declaration position: `<prop>:`. Covers the modern
# gap family + its legacy `grid-*` aliases (drift-prevention — none exist in the
# file today, but a future `grid-gap: 0.3rem` should still be flagged), and
# padding/margin incl. per-side + logical (block/inline start/end) forms.
# DELIBERATELY EXCLUDED (positioning, not layout rhythm — out of scope per spec):
# `scroll-margin*` / `scroll-padding*` / `inset` / `top`/`left`/etc. The `(?<![\w-])`
# lookbehind is what keeps `scroll-padding` from matching the `padding` alternative.
IN_SCOPE_PROP_RE = re.compile(
    r"(?<![\w-])"
    r"(gap|row-gap|column-gap|grid-gap|grid-row-gap|grid-column-gap|"
    r"padding(?:-(?:top|right|bottom|left|block|inline)(?:-(?:start|end))?)?|"
    r"margin(?:-(?:top|right|bottom|left|block|inline)(?:-(?:start|end))?)?)"
    r"\s*:\s*([^;{}]*)"
)
# A bare rem literal (optionally signed). `var(--space-…)` has no rem, so it
# never matches; `calc(-1 * var(--space-…))` likewise carries no bare rem.
REM_RE = re.compile(r"-?(\d*\.?\d+)rem\b")


def _allowlisted(num: str) -> bool:
    try:
        val = float(num)
    except ValueError:
        return False
    return any(abs(val - a) < 1e-6 for a in ALLOWLIST)


def find_violations(css: str) -> list[tuple[int, str, str]]:
    """Return (lineno, prop, raw_number) for every bare, non-allowlisted rem in
    an in-scope declaration. `raw_number` is the numeric text (no unit)."""
    css = COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), css)
    violations: list[tuple[int, str, str]] = []
    for m in IN_SCOPE_PROP_RE.finditer(css):
        prop, value = m.group(1), m.group(2)
        for rem in REM_RE.finditer(value):
            num = rem.group(1)
            if _allowlisted(num):
                continue
            lineno = css.count("\n", 0, m.start()) + 1
            violations.append((lineno, prop, num))
    return violations


def run(repo_root: Path) -> tuple[int, list[str]]:
    css_path = repo_root / "assets" / "css" / "main.css"
    if not css_path.exists():
        return (1, [f"main.css not found at {css_path}"])
    css = css_path.read_text(encoding="utf-8")
    errors = [
        f"{css_path}:{ln}: raw spacing '{num}rem' in `{prop}` — "
        f"use var(--space-*) or allowlist a micro-nudge"
        for ln, prop, num in find_violations(css)
    ]
    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} un-tokenized spacing value(s).", file=sys.stderr)
        return rc
    print("OK — every in-scope spacing value is tokenized or allowlisted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
