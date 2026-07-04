#!/usr/bin/env python3
"""Dark-mode token equality linter (R2.2).

The palette's dark values live in TWO hand-duplicated blocks of
`assets/css/main.css` that must stay byte-identical:

  1. `:root[data-theme="dark"]`            — explicit attribute override
  2. `:root:not([data-theme])` inside a    — system `prefers-color-scheme`
     `@media (prefers-color-scheme: dark)`

`tools/check-contrast.py` verifies contrast *ratios* but never that these two
blocks *match each other*, so a palette edit touching only one ships a
light/dark inconsistency that passes CI. This linter closes that gap: it
extracts both blocks and asserts identical `--token: value` maps.

Stdlib only. Exits 0 on match, 1 on any drift.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ATTR_SELECTOR = r':root\[data-theme="dark"\]'
MEDIA_SELECTOR = r':root:not\(\[data-theme\]\)'
DECL_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")


def _extract_block(css: str, selector_re: str) -> dict[str, str] | None:
    """Return the `--token: value` map for the first `<selector> { ... }` block,
    or None if the selector isn't present. Blocks are flat (no nested braces)."""
    m = re.search(selector_re + r"\s*\{([^}]*)\}", css)
    if not m:
        return None
    return {k: v.strip() for k, v in DECL_RE.findall(m.group(1))}


def run(repo_root: Path) -> tuple[int, list[str]]:
    css_path = repo_root / "assets" / "css" / "main.css"
    if not css_path.exists():
        return (1, [f"main.css not found at {css_path}"])
    css = css_path.read_text(encoding="utf-8")

    attr = _extract_block(css, ATTR_SELECTOR)
    media = _extract_block(css, MEDIA_SELECTOR)
    errors: list[str] = []
    if attr is None:
        errors.append('missing `:root[data-theme="dark"]` block')
    if media is None:
        errors.append('missing `:root:not([data-theme])` block inside @media (prefers-color-scheme: dark)')
    if errors:
        return (1, errors)

    for token in sorted(set(attr) | set(media)):
        a = attr.get(token)
        b = media.get(token)
        if a is None:
            errors.append(f"{token}: present in @media block but absent from [data-theme=dark]")
        elif b is None:
            errors.append(f"{token}: present in [data-theme=dark] but absent from @media block")
        elif a != b:
            errors.append(f"{token}: [data-theme=dark]={a!r} != @media={b!r}")
    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} dark-token drift issue(s) between the two dark blocks.", file=sys.stderr)
        return rc
    print("OK — dark-mode token blocks are in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
