#!/usr/bin/env python3
"""WCAG 2.1 contrast verifier for the site palette.

Parses CSS custom properties from `assets/css/main.css` and asserts the
documented pairings (spec §2) hit their thresholds.

Exits 0 on all-pass, 1 on any violation. No third-party deps.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = REPO_ROOT / "assets" / "css" / "main.css"

# (foreground_token, background_token, min_ratio, role)
# WCAG 2.1: AAA body text = 7.0; AA body / AAA large = 4.5.
PAIRINGS = [
    ("color-ink",      "color-stone", 7.0, "body text on background"),
    ("color-ink-soft", "color-stone", 4.5, "secondary text on background"),
    ("color-burgundy", "color-stone", 4.5, "accent on background"),
    ("color-steel",    "color-stone", 4.5, "accent on background"),
]


def parse_palette(css: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return (light_tokens, dark_tokens) as name -> '#rrggbb'."""
    light_match = re.search(r":root\s*\{([^}]*)\}", css, re.DOTALL)
    dark_match = re.search(
        r':root\[data-theme="dark"\]\s*\{([^}]*)\}', css, re.DOTALL
    )
    if not light_match:
        sys.exit("ERROR: could not find ':root { ... }' block in main.css")
    if not dark_match:
        sys.exit(
            'ERROR: could not find \':root[data-theme="dark"] { ... }\' block in main.css'
        )

    def extract(block: str) -> dict[str, str]:
        return {
            name: value.lower()
            for name, value in re.findall(
                r"--([a-z0-9\-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\s*;", block
            )
        }

    return extract(light_match.group(1)), extract(dark_match.group(1))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    s = value.lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        sys.exit(f"ERROR: unsupported hex color '{value}'")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    l1 = relative_luminance(hex_to_rgb(fg))
    l2 = relative_luminance(hex_to_rgb(bg))
    light, dark = max(l1, l2), min(l1, l2)
    return (light + 0.05) / (dark + 0.05)


def check(palette_name: str, palette: dict[str, str]) -> list[str]:
    failures: list[str] = []
    print(f"\n{palette_name}:")
    for fg_name, bg_name, min_ratio, role in PAIRINGS:
        fg = palette.get(fg_name)
        bg = palette.get(bg_name)
        if fg is None or bg is None:
            failures.append(
                f"  MISSING tokens for {fg_name} or {bg_name} in {palette_name}"
            )
            print(f"  MISSING {fg_name} / {bg_name}")
            continue
        ratio = contrast_ratio(fg, bg)
        status = "PASS" if ratio >= min_ratio else "FAIL"
        if status == "FAIL":
            failures.append(
                f"  FAIL {fg_name} ({fg}) on {bg_name} ({bg}): "
                f"{ratio:.2f}:1 < {min_ratio:.1f}:1 ({role})"
            )
        print(
            f"  {status} {fg_name:16s} on {bg_name:14s} "
            f"{ratio:5.2f}:1  (min {min_ratio}, {role})"
        )
    return failures


def main() -> int:
    if not CSS_PATH.exists():
        sys.exit(f"ERROR: {CSS_PATH} not found")
    css = CSS_PATH.read_text()
    light, dark = parse_palette(css)
    failures = check("Light mode (:root)", light)
    failures += check('Dark mode (:root[data-theme="dark"])', dark)
    if failures:
        print("\nFAILURES:")
        for line in failures:
            print(line)
        return 1
    print("\nAll contrast pairings pass WCAG thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
