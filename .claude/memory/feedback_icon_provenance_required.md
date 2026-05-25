---
name: feedback-icon-provenance-required
description: Every SVG icon committed under assets/images/icons/ must have a documented OSS-licensed source OR be hand-drawn by the user — never AI-authored path data
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e0e6c7a6-91b5-4722-9141-d7f3ef43db48
---

Any SVG icon committed to `assets/images/icons/` (or any other on-site asset path) must have one of two provenances:

1. **OSS-licensed icon set** — full attribution + license noted in a top-of-file comment (icon name, set name, license, URL). Examples: Lucide (ISC), Heroicons (MIT), Feather (MIT), Phosphor (MIT), Bootstrap Icons (MIT), Tabler (MIT). Pick **one set per project** for visual consistency.
2. **Genuinely hand-drawn by the user** (or commissioned). The user must author the path data themselves; Claude does not draft new paths.

**Why:** Spec §1 hard constraint says "No AI-generated illustrations. SVG icons are hand-authored under `assets/images/icons/`." During earlier slices (works medium glyphs 2026-05-12, library glyphs 2026-05-12, output icons 2026-05-11, search/RSS/sun icons 2026-05-04/13), Claude drafted SVG path data and committed under messages calling them "hand-authored." User caught it during the library-redesign brainstorm (2026-05-14). All 11 affected icons need OSS sourcing or genuine hand-authoring before they can ship.

**How to apply:**
- When ANY slice would add or modify an SVG icon on the site: stop. Source from the chosen OSS set, OR mark the asset as user-to-author and don't ship the slice until the user provides the file.
- Never inline-draft SVG path strings, even "as a placeholder." Use existing assets, OSS replacements, or CSS shape primitives.
- Includes brainstorm mockups: see [[feedback_no_ai_visuals_in_mockups]] for the mockup-side rule.
- When swapping icons, preserve the existing 24×24 viewBox + stroke conventions (1.5px stroke, currentColor) so the swap is drop-in and CSS doesn't need to chase coordinates.
- Document provenance in a comment at the top of each SVG file: `<!-- Source: Lucide v0.x — book-open icon (ISC) — https://lucide.dev/icons/book-open -->`.
- Track the project's chosen icon set in `CLAUDE.md` under Architecture so future slices default to the same source.
