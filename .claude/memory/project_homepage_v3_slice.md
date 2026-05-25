---
name: project-homepage-v3-slice
description: Homepage v3 slice merged 2026-05-13 — closes Phase 7 (only Phase 3 elisp + Phase 8 polish remain)
metadata: 
  node_type: memory
  type: project
  originSessionId: d27b9186-f371-40e9-ac80-f9b1a00cfcff
---

Homepage v3 slice — Phase 7 Slice 2 — merged 2026-05-13 (merge `020ca4a`, pushed to origin). Closes Phase 7.

Five new partials under `layouts/partials/home/`: hero, currently, research-strip, garden-strip, studio-strip. CSS §38–§40 (hero, Currently widget, strips) appended to `assets/css/main.css` with a single 800px responsive breakpoint. New `home_lede:` frontmatter field on `content/_index.html` separates the visible hero lede from the `<meta name="description">` value. Studio strip reuses the existing `works/glyph-sprite.html` rendered once near the top of `layouts/home.html`, guarded by "studio strip will produce ≥1 row".

**Why:** the user's request was to close Phase 7 by assembling the remaining v3 mockup blocks. The mockup at `.superpowers/brainstorm/1178775-1777859433/content/homepage-v3.html` was the visual target. 4 Currently rows (reading/listening/playing/watching) reflects the Library section's 4 leaves, not the spec's literal "3 lines" — the spec predates the watching addition.

**How to apply:** when working on the homepage, the orchestrator is `layouts/home.html` and each section is its own partial under `home/`. Type-badge glyphs use `var(--color-stone)` (theme-flipping) for dark-mode contrast on the burgundy/steel `color-mix` gradients — a critical-contrast fix landed as a follow-up commit `1088da3`. Studio selection algorithm: 1 newest per medium + 1 newest remaining = 4 rows max, sorted by `last_modified` desc for display. See also: [[project-library-cover-fetch-slice]].

Next slice under discussion: homepage **section sidebar** (sticky in-page TOC rail) — brainstorm/spec pending. Remaining roadmap items: Phase 3 (elisp pipeline, user-driven), Phase 8 (Pagefind + Lighthouse + final QA).
