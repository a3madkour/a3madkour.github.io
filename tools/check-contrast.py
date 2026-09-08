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
    ("color-green",      "color-stone", 4.5, "garden evergreen stage glyph on background"),
    ("color-green-mid",  "color-stone", 4.5, "garden budding stage glyph on background"),
    ("color-green-soft", "color-stone", 4.5, "garden seedling stage glyph on background"),
    ("color-warn",     "color-stone", 4.5, "warn pill text on background"),
    ("color-stone",    "color-warn",  4.5, "stone on warn pill background"),
    # Graphical object (the RSS icon strokes with currentColor), so the bar
    # is SC 1.4.11's 3:1 rather than 4.5 — but the chosen stops clear it with
    # headroom (4.12 light / 6.47 dark) rather than sitting on the line.
    ("color-rss",      "color-stone", 3.0, "RSS icon glyph on background"),
    ("color-live",     "color-stone", 3.0, "live-stream indicator dot on background"),
    ("color-ink",      "color-tile", 7.0, "body text on tile/rail surface"),
    ("color-burgundy", "color-tile", 4.5, "rescaled-quantity accent on rail surface"),
    ("color-ink-fade", "color-tile", 4.5, "ingredient qualifier text on rail surface"),
    ("color-stone",    "color-burgundy", 4.5, "stone on burgundy accent background"),
    ("color-ink-fade", "color-stone", 4.5, "de-emphasised meta text on background"),
    ("color-tile",     "color-burgundy", 4.5, "tile surface on burgundy accent background"),
    # --color-paper is the floating-panel surface (search modal, cite modal,
    # path-log popover, the recipe stepper field). It is a distinct token from
    # --color-tile that merely happens to share its value today; gating it in
    # its own right is what lets the two diverge without dropping out of the
    # gate. Both directions of the burgundy pairing render: burgundy text on a
    # paper control (.reenable-tracking, .recipe-stp button) and paper text on
    # a burgundy fill (.search-modal-chip.is-active, .download-link:hover).
    ("color-ink",      "color-paper", 7.0, "body text on floating panel surface"),
    ("color-ink-soft", "color-paper", 4.5, "secondary text on floating panel surface"),
    ("color-burgundy", "color-paper", 4.5, "accent control text on floating panel surface"),
    ("color-paper",    "color-burgundy", 4.5, "panel surface on burgundy accent background"),
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


# Margin below which a passing pairing is reported in the closing summary.
# Purely informational — it never fails the run. The point is that the palette's
# thinnest pairings should be visible to whoever is about to nudge a token,
# rather than recorded in a document they will not open.
#
# This sits deliberately *below* the margin the palette is tuned to (0.25 as of
# 2026-09-08, RF3.4). If the two were equal, pairings tuned to exactly the
# target would fall in or out of the report on a third-decimal rounding, and an
# empty report would mean "on the line" rather than "clear of it". The gap is
# the slack that makes an empty report a real statement.
TIGHT_MARGIN = 0.20


def check(
    palette_name: str, palette: dict[str, str]
) -> tuple[list[str], list[tuple[float, float, float, str, str, str]]]:
    """Print one palette's table. Returns (failures, rows) where each row is
    (margin, ratio, min_ratio, palette_name, fg_name, bg_name)."""
    failures: list[str] = []
    rows: list[tuple[float, float, float, str, str, str]] = []
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
        rows.append((ratio - min_ratio, ratio, min_ratio, palette_name, fg_name, bg_name))
        print(
            f"  {status} {fg_name:16s} on {bg_name:14s} "
            f"{ratio:5.2f}:1  ({ratio - min_ratio:+.2f} over {min_ratio}, {role})"
        )
    return failures, rows


def report_margins(rows: list[tuple[float, float, float, str, str, str]]) -> None:
    tight = sorted(r for r in rows if 0 <= r[0] < TIGHT_MARGIN)
    if not tight:
        return
    print(f"\nThinnest margins (passing, but within {TIGHT_MARGIN:.2f} of the bar):")
    for margin, ratio, min_ratio, palette_name, fg_name, bg_name in tight:
        mode = palette_name.split()[0].lower()
        print(
            f"  {margin:+.2f}  {ratio:5.2f}:1 vs {min_ratio:.1f}  "
            f"{mode:5s} {fg_name} on {bg_name}"
        )
    print("  These break first when the palette moves. Not a failure.")


def main() -> int:
    if not CSS_PATH.exists():
        sys.exit(f"ERROR: {CSS_PATH} not found")
    css = CSS_PATH.read_text()
    light, dark = parse_palette(css)
    failures, rows = check("Light mode (:root)", light)
    dark_failures, dark_rows = check('Dark mode (:root[data-theme="dark"])', dark)
    failures += dark_failures
    rows += dark_rows
    report_margins(rows)
    if failures:
        print("\nFAILURES:")
        for line in failures:
            print(line)
        return 1
    print("\nAll contrast pairings pass WCAG thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
