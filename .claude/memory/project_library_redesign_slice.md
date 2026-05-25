---
name: project-library-redesign-slice
description: "Library umbrella redesign + icon-provenance close-out — shipped 2026-05-14, merge 3330559, pushed to origin/master"
metadata: 
  node_type: memory
  type: project
  originSessionId: e54ad22c-8c11-4afb-8360-ad0b334d6968
---

Two-layer slice merged 2026-05-14 to master (merge `3330559`, pushed to origin).

**Layer 1 — Library umbrella redesign:**
- New umbrella shape: hero (featured item with cover + Cite/Note/Original action row) → "Browse the catalogue" 4-card grid → themed shelves (tag-driven OR hand-curated, see [[project-phase-3-library-tag-shelves]] for the Phase 3 round-trip plan).
- New data shape: `data/library-media.yaml` (medium registry) + `data/library-shelves.yaml` (hand-authored curation; tag-driven OR slug-list shelves; optional hero pin). Items in `data/<medium>.yaml` carry tags that drive shelf membership.
- New layouts: `layouts/library/list.html` rewritten; `layouts/library-shelf/list.html` for `/library/shelves/<slug>/` detail pages.
- New partials under `layouts/partials/library/`: `umbrella-hero`, `umbrella-shelf`, `umbrella-tile`, `umbrella-catalogue`.
- CSS §44 covers the entire umbrella + shelf-detail surface. `min(2400px, 95vw)` max-width so it breathes on 4K (was 900px inherited from prose column).
- 18th linter pair: `tools/check_library_shelves.py` + sibling — gates shelves-yaml schema, slug resolution against media yamls, tag resolution (zero-resolved-items fails), hero pin sanity.
- Tile invariants (per design + iteration):
    - Fixed `height: 340px` so all tiles in a shelf row are identical regardless of content variance — extra space absorbed via `.library-tile-meta { margin-bottom: auto }` (action row pins to tile bottom).
    - Cover `object-fit: cover` on `.library-cover-wrap .library-cover` so landscape thumbnails crop to fill the portrait frame (no white space).
    - Title `-webkit-line-clamp: 2` with `min-height: 2.4em` so 1-line and 2-line titles reserve the same slot.
    - Tile cite button shortened to "Cite" (full label preserved as `aria-label`) so the 3-button row doesn't wrap to 2 lines.
    - No wrapping anchor on the tile — actions handle navigation; keyboard nav (`library-shelf-nav.js`) traverses `.cite-cta` buttons within each shelf strip.
    - Glyph fallback (no-cover) uses `width: 100%; height: 100%` in normal flow (NOT absolute positioning — collapsed the wrap height in that variant). Scoped to `.library-cover-wrap .library-glyph-block` + `.library-hero-cover-wrap .library-glyph-block` so the older §37 leaf-row glyph (small inline-flex `height: 3.5rem`) keeps working unchanged on leaves.
- Hero action row harmonized: Cite is rectangular burgundy fill (primary); Note + Original are circular pill outlines (secondary) — all three baseline-aligned, same padding/weight, all lift on hover. Tile action row separately normalized so Cite drops its primary box-shadow and matches the pill aesthetic.
- Wikimedia 240px thumbnail URLs in all four `data/<medium>.yaml` files returned HTTP 400 — Wikimedia only allows specific thumbnail sizes (120/250/300/...). Bulk-replaced 240→250 across 8 cover URLs.

**Layer 2 — Icon-provenance close-out:**
- 11 hand-authored SVGs replaced with Lucide-sourced equivalents under `assets/images/icons/` — each carries an attribution header comment.
- `THIRD_PARTY.md` documents Lucide ISC + Google Fonts provenance; `LICENSES/lucide-ISC.txt` vendored.
- `/credits/` page added; linked from footer colophon + about-page Colophon section; registered in pagefind URL-prefix map.
- 19th linter pair: `tools/check_icon_attribution.py` + sibling — gates every SVG under `assets/images/icons/` having an attribution comment OR being listed in `tools/.icon-attribution-exceptions.yaml`.
- About-page hero `monogram-am.svg` removed; replaced with CSS "AM" disc (no SVG needed).

**CI growth:** workflow grew 46 → 50 named steps (icon-attribution linter +2, library-shelves linter +2). `tools/ci-local.sh` mirrors.

**Page-weight budget adjustments:** `/about/`, `/credits/`, `/blog/` bumped to 150K explicit budgets — site-wide CSS bundle grew past the 100K default for thin pages.

**TOC scrollspy fix (drive-by):** `nav.js` TOC active-link highlighter rewritten — was IntersectionObserver watching heading viewport-edge crossings, which never updated when scrolling within a long section. Now uses the same "last heading whose top crossed the 10%-from-top trigger" algorithm as the page-sidebar scrollspy already had.

**Essay reading-column widened:** `--reading-column` 900 → 1100px (was inherited from the citation-export slice's TOC-sidebar accommodation). `.essay-figure.wide` breakout updated 920 → 1140px to maintain its ~20px outset.

**Plan + spec:** `docs/superpowers/{specs,plans}/2026-05-14-library-redesign.md` (spec includes §11.5 forward-looking note re: Phase 3 tag round-trip).

Closes the queued library-redesign stub. Graph-view consistency remains the only stub-spec queue entry.
