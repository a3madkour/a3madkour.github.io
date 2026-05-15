# Library redesign + icon-provenance close-out — design

**Status:** Spec — brainstorm complete. Plan to follow.
**Slice scope:** two layers in one slice.

## 1. Motivation

Two unrelated problems converged during the citation-export slice and are merged here for delivery economy:

1. **`/library/` umbrella feels bland.** User feedback (2026-05-14): "the current card setup is a bit too bland." Four equal-weight summary cards (Reading / Listening / Playing / Watching), each showing a glyph + stats + top-3 list. Uniform, no editorial hierarchy, no cover art surface, no extensibility beyond the four hardcoded mediums.

2. **Icon-provenance violation.** Mid-brainstorm audit (2026-05-14) revealed 11 SVG icons under `assets/images/icons/` committed as "hand-authored" are AI-drafted. Spec §1 hard-constraint says **no AI-generated illustrations**, including SVGs.

Both touch the same surfaces (the library umbrella uses 4 of the 11 icons) and benefit from one combined linter pair, one `/credits/` page, one PR. The work splits cleanly into two layers.

## 2. Scope

### Layer 1 — Library umbrella redesign

- New `/library/` umbrella page shape: hero + themed cross-medium shelves + bottom catalogue block.
- Two new yaml data files: `data/library-shelves.yaml` + `data/library-media.yaml`.
- New Hugo section for shelves > 12 items at `/library/shelves/<slug>/`.
- New tile partial (umbrella-only); reuses existing leaf row partial elsewhere.
- New CSS section §44.
- New linter pair: `tools/check_library_shelves.py` (#18).

### Layer 2 — Icon-provenance close-out

- Replace 11 icons under `assets/images/icons/` with [Lucide](https://lucide.dev) (ISC).
- New `/credits/` page (third-party attribution).
- New `THIRD_PARTY.md` at repo root.
- Per-SVG header comment with provenance + license.
- Delete `monogram-am.svg`; replace with text-only "AM" in About hero.
- New linter pair: `tools/check_icon_attribution.py` (#19).

### Out of scope

- Leaf pages `/library/{reading,listening,playing,watching}/` — already polished in the cover-fetch slice; redesign **does not touch** them.
- Library YAML schema changes (no new per-item fields).
- IGDB / TMDB live cover fetching (still deferred from cover-fetch slice).
- Library RSS feeds (deferred; essays-only RSS scope holds).
- `/library/graph/` (out of scope per parent spec).

## 3. Architecture

### 3.1 Content + layouts

- `content/library/_index.md` — unchanged frontmatter contract; the umbrella body content stays as the lede.
- `content/library/shelves/<slug>/_index.md` — **new**, one per long-shelf (>12 items). Author-written stub.
- `layouts/library/list.html` — **rewritten** for the new shape (was the bland 4-card umbrella).
- `layouts/library-shelf/list.html` — **new** section template for `/library/shelves/<slug>/`.

### 3.2 Partials

Under `layouts/partials/library/`:

- `umbrella-hero.html` — **new**. Renders the single hero block. Reads first matching item per `hero:` key or max-`last_modified` fallback.
- `umbrella-shelf.html` — **new**. Takes a resolved shelf dict; emits `<h2>` + intro + horizontal-scroll strip of up to N tiles + "See all" link.
- `umbrella-tile.html` — **new**. Per-tile markup (cover + title + meta + action row). Distinct from `library/row.html` which is the leaf list-row partial.
- `umbrella-catalogue.html` — **new**. Renders the 4-card (or N-card per media registry) "Browse the catalogue" block.
- `medium-rail.html` — **new**. Top pill rail with one chip per medium from the registry.
- `umbrella-card.html` — **deleted** (was the four-section card; superseded).
- `glyph-block.html` — **kept**. Used as no-cover fallback on tiles + hero. Per-medium tinted block remains as decorative-only treatment (the **semantic** medium identity is carried by the neutral disc badge that overlays — see §4.3).

### 3.3 Data contracts

#### `data/library-media.yaml` — media registry (new, required)

Top-level: `media:` list. Order = display order in the top rail and bottom catalogue.

```yaml
media:
  - key: reading
    label: "Reading"
    glyph: book-open          # Lucide icon name (must exist in assets/images/icons/)
    cover_aspect: portrait    # portrait | square
  - key: listening
    label: "Listening"
    glyph: music
    cover_aspect: square
  - key: playing
    label: "Playing"
    glyph: gamepad-2
    cover_aspect: portrait
  - key: watching
    label: "Watching"
    glyph: clapperboard
    cover_aspect: portrait
```

Required fields per entry: `key`, `label`, `glyph`, `cover_aspect`. `key` must match the existing `data/<key>.yaml` filename + `/library/<key>/` URL.

#### `data/library-shelves.yaml` — curation (new, optional)

Two top-level keys: `hero:` (optional, single slug) and `shelves:` (list).

```yaml
hero: essence-of-decision    # any slug from any data/<medium>.yaml

shelves:
  # Tag-driven shelf — items resolve by tag intersection across all media
  - title: "Recently finished"
    intro: "Things I closed the cover on this season."
    tag: finished              # single tag string (not a list)

  # Hand-curated slug-list shelf
  - title: "From the field of game design"
    intro: "Books and papers that shaped how I think about games."
    items:
      - essence-of-decision
      - a-pattern-language
      - homo-ludens
      # … any cross-media mix; up to 12 fit on umbrella
```

Each shelf MUST have exactly one of `tag:` or `items:` (linter rejects both / neither). `title:` + `intro:` required. `tag:` is a single string referencing a tag that appears in at least one item's `tags:` array across the four medium yamls; resolved items are the union of all items carrying that tag (cross-medium). `items:` is an ordered slug list — slugs reference any item across `data/reading.yaml` / `listening.yaml` / `playing.yaml` / `watching.yaml`.

### 3.4 Per-shelf detail-page pattern

Shelves with >12 items render only 12 tiles on the umbrella + a "See all →" link. Routing:

| Shelf type | See-all target | Generation path |
|---|---|---|
| Tag-driven | `/tags/<tag>/` | Existing Hugo taxonomy — no new page generated |
| Hand-curated, ≤12 items | None (no link) | All items shown on umbrella |
| Hand-curated, >12 items | `/library/shelves/<slug>/` | **Author-written stub** (see below) |

For long hand-curated shelves, author creates `content/library/shelves/<slug>/_index.md`:

```yaml
---
title: "From the field of game design"
shelf: field-of-game-design       # slug must match a shelf in library-shelves.yaml
type: library-shelf
summary: "Books and papers that shaped how I think about games."
---

Optional markdown body — renders below the page title, above the tile grid.
```

Linter (`check_library_shelves.py`) enforces stub↔yaml sync:

- Every shelf in yaml with `items:` count > 12 MUST have a corresponding stub.
- Every stub MUST reference a shelf in yaml (no orphan stubs).
- Stub `shelf:` value MUST match the slugified shelf title.

### 3.5 Empty-state matrix

| Condition | Behaviour |
|---|---|
| `data/library-media.yaml` missing | **Build fails.** Registry required; linter asserts. |
| `data/library-shelves.yaml` missing | Soft fall-back: render H1 + lede + rail + catalogue. No hero, no shelves. |
| Shelves yaml exists, both `hero:` and `shelves:` absent / empty | Hero auto-falls-back to max-`last_modified`; no shelves; catalogue still renders. |
| Shelves yaml exists, `hero:` set, `shelves:` empty | Hero renders from explicit slug; no shelves; catalogue still renders. |
| Shelf resolves to zero items (bad tag or empty slug-list resolution) | Shelf hidden silently. Linter catches all-404 slug list at build; tag-driven empty shelves emit a build warning. |
| `hero:` slug doesn't resolve | Fall back to max-`last_modified` across all media. Build warning emitted. |
| Hero auto-fallback finds no items at all | Hero block hidden. Page renders H1 + lede + rail + catalogue only. |

### 3.6 Soft cap on shelf count

Spec guideline: **~6 shelves max** on the umbrella. Not linter-enforced; author judgment. Page-weight CI gate (§4.5) is the hard backstop.

## 4. Visual design — Layer 1

### 4.1 Page shape (Section A · variant A)

Top-to-bottom flow:

1. **Header** — `<h1>Library</h1>` + italic lede from `content/library/_index.md`.
2. **Medium pill rail** — one pill per `library-media.yaml` entry + an "All" pill (default active). Pills link to the corresponding `/library/<key>/` leaf page.
3. **Hero block** — single `<article class="library-hero">`; oversized cover (140×190 portrait or 140×140 square per `cover_aspect`), eyebrow text `★ Featured · <Label>`, h2 title, creator · year meta, italic preview, full Direction-1 action row. No corner badge overlay (medium is carried by the eyebrow + cover ratio).
4. **Shelves** — each `<section>` with h2 + intro + horizontal-scroll tile strip (up to 12 tiles, fixed 140px wide) + "See all →" link in the shelf header (right-aligned).
5. **Browse the catalogue** — `<section>` with h2 "Browse the catalogue" + N cards (one per medium). Card = neutral ink disc + Lucide glyph + medium label + total count.
6. **Page sidebar** — partial `layouts/partials/page-sidebar.html` with anchors `#hero`, one per shelf `#shelf-<slug>`, `#catalogue`. Suppressed when <2 anchors (consistent with the cross-template rail behaviour).

### 4.2 Tile (Section C · always-visible action row)

`<article data-medium="<key>" class="library-tile">`:

```
<a class="library-tile-link" href="/library/<medium>/#<slug>">
  <div class="library-cover-wrap">
    <img ... loading="lazy"> | <div class="library-glyph-block <medium>">…</div>
    <span class="library-badge"> [Lucide glyph] </span>
  </div>
  <h4 class="library-tile-title">…</h4>
  <p class="library-tile-meta">creator · year</p>
</a>
<script class="cite-data">{…}</script>
<div class="library-tile-actions">
  <button class="cite-cta">Cite this <kind></button>
  <a class="ref-cite-note" href="/garden/<note>/">Note</a>
  <a class="ref-cite-source" href="<canonical_url>">Original</a>
</div>
```

Action row siblings OUTSIDE the wrapping `<a>` (no nested anchors). Tile height grows ~28px to fit the row. Same pattern as `library/row.html`.

### 4.3 Medium badge — neutral disc, semantic colour discipline

Every tile + the catalogue cards carry a corner / centered badge:

- **Background:** `--color-ink` disc.
- **Glyph:** `--color-stone` Lucide icon at 12px (22px disc on tile corner) / 14px (28px disc on catalogue card) / 22px (44px disc on hero overlay if used) / 44px (88px disc as no-cover fallback).
- **Shape carries medium** (different glyph per medium); **colour stays semantic** (the green / burgundy / steel tokens retain their other meanings on the site).

Rationale: per-medium tinted badges would double-book `--color-green` (finished status + Related-note pill), `--color-burgundy` (primary CTA), `--color-steel` (external nav). See `feedback_semantic_consistency_site_wide` memory.

### 4.4 No-cover fallback (Section C Q1 = B)

Existing `.library-glyph-block.book/.music/.game/.watching` per-medium tinted blocks **stay** as the no-cover fallback. The block fills the cover slot with a tinted background (book = burgundy, music = steel, game = green, watching = violet) and an oversized stone glyph.

**Critical:** this tinted block is **decorative-only**, not semantic. The neutral disc badge that overlays on top carries the semantic medium identity. The deviation from "color stays semantic" is documented here per `feedback_semantic_consistency_site_wide`:

> The tinted block uses the same colour tokens as the semantic palette (green / burgundy / steel / violet) for visual interest, NOT for semantic mapping. Readers must not infer "green-tinted block = finished" or "burgundy-tinted block = primary." The semantic medium signal is the neutral disc badge in the corner, which is identical across all media (shape differs, colour does not).

This trade-off was chosen against the "go fully neutral" alternative (Section C Q1 = A) because tinted blocks fight the "too bland" feedback that motivated the redesign. Most items in practice will have real covers (cover-fetch slice seeded 8 thumbnails); the fallback is uncommon.

### 4.5 Hero block (Section C Q2 = A · article element)

`<article class="library-hero">` — `article` element, not `section`. This makes `cite.js`'s existing `closest('article')` selector find the hero's `<script class="cite-data">` blob without any JS change.

Layout: 2-column grid (cover left, body right). Cover at 140×190 (portrait) or 140×140 (square) per the featured item's `media_type`. Body: eyebrow + h2 + creator/year/started/finished line + italic preview + full action row (`Cite this <kind>` burgundy fill · `Note` green outline · `Original` steel outline). All three action affordances render whether or not the underlying item has a note or original — hidden conditionally via inline `style="display:none"` when the data is absent, consistent with how leaf rows already render them.

### 4.6 Scroll-row behaviour (Section D Q1 = A · plain scroll)

Shelf tile strip: `overflow-x: auto`, no `scroll-snap`. Touch swipe natural; trackpad / mouse-wheel scroll natural. No gradient masks, no snap-stop, no scroll-indicator chrome.

### 4.7 Keyboard navigation (Section D Q2 = A · arrow within)

Tab order:

1. `Tab` to first tile of shelf 1
2. `→` / `←` arrows traverse within shelf 1
3. `Tab` exits to first tile of shelf 2 (skips remaining tiles in shelf 1)
4. Repeat per shelf
5. `Tab` past last shelf → first catalogue card

Pattern mirrors the post-a11y close-out filter-chip primary-tier nav. Action-row pills on a focused tile are reachable by a nested `Tab` into the tile (since they're rendered outside the `<a>` but inside the tile `<article>`).

Implementation: each tile is a real focusable `<a>`. Per-shelf strip carries a `keydown` handler scoped to that strip; tiles after the first get `tabindex="-1"` so native `Tab` skips them; arrow keys call `.focus()` on the next sibling tile, capped at the strip boundaries (no wraparound).

### 4.8 CSS section §44

New top-of-file index entry. Layout:

- `.library-umbrella` page-level grid (max-width: 900px, padded gutters).
- `.medium-rail` flex row, 12px gap, `flex-wrap: wrap`.
- `.medium-pill` (chip styling consistent with filter-chips: `border-radius: 999px`, `border: 1px solid currentColor`, `padding: 4px 12px`).
- `.library-hero` 2-column grid (cover + body), responsive collapse to 1-col below 720px.
- `.library-shelf` block layout; `.library-shelf-strip` flex row with `overflow-x: auto`; `.library-tile` fixed 140px width.
- `.library-tile-actions` row of three action pills.
- `.library-catalogue` flex/grid responsive: 4 cols ≥960px, 2 cols 720-960, 1 col <720.

### 4.9 Page weight (Section D Q3 = A · 500 KB + lazy-load)

Classifier in `tools/check_page_weights.py` for `/library/` stays at **500 KB**. Add lazy-loading:

- Hero `<img>` carries `loading="eager"` (above-the-fold) + `fetchpriority="high"`.
- All shelf tile `<img>` elements carry `loading="lazy"` + `decoding="async"`.
- Catalogue card discs are inline SVG (no image fetch).

Initial-paint weight stays under 500 KB; below-fold covers fetch only on scroll-near.

## 5. Visual design — Layer 2 (icon provenance)

### 5.1 Icon canon

All 11 SVG icons under `assets/images/icons/` get replaced with [Lucide v1.16.0](https://lucide.dev) (ISC license). One-to-one mapping:

| Current file | Lucide replacement | Used on |
|---|---|---|
| `book.svg` | `book-open.svg` | Library (reading leaf, umbrella catalogue) |
| `music.svg` | `music.svg` | Library (listening), Works (music) |
| `gamepad.svg` | `gamepad-2.svg` | Library (playing), Works (games) |
| `clapper.svg` | `clapperboard.svg` | Library (watching) |
| `quill.svg` | `feather.svg` | Works (poetry) |
| `search.svg` | `search.svg` | Header search trigger |
| `rss.svg` | `rss.svg` | Header RSS link |
| `theme-sun.svg` | `sun.svg` | Theme toggle |
| `code.svg` | `code.svg` | (audit usage — possibly remove if unused) |
| `note.svg` | `file-text.svg` | (audit usage) |
| `talk.svg` | `presentation.svg` | (audit usage) |

Audit usage during implementation: any of the last three not referenced anywhere → delete the file (instead of fetching a replacement).

### 5.2 Ship parameters (Final-thread Q1 = A)

- All 11 fetched at default Lucide stroke-width=2.
- Single SVG file per icon rendered at all 4 sizes (22 / 28 / 44 / 88 px) via CSS-driven width/height — no per-size variants up front.
- QA pass: visually inspect 22px-badge legibility per icon; for any that read poorly (likely candidates: `gamepad-2`'s dense controls), commission a per-icon stroke-width override or use a Lucide-icons-lab variant. Defer; only fix if a real problem shows up.

### 5.3 Per-SVG header comment

Every fetched SVG gets a header comment **before** the `<svg>` element:

```xml
<!-- Lucide v1.16.0 — book-open · ISC License · see /THIRD_PARTY.md -->
<svg ...>
```

Linter (`check_icon_attribution.py`) asserts every file under `assets/images/icons/` carries this header pattern OR appears in `tools/.icon-attribution-exceptions.yaml` (for legitimate user-drawn icons added later).

### 5.4 `/credits/` page (new)

`content/credits/_index.md` — single page at `/credits/`. Renders:

- ISC license full text for Lucide.
- Acknowledgment line: "Site icons sourced from Lucide (lucide.dev) v1.16.0."
- Acknowledgment for any other third-party assets that get added.
- Cross-link target for `about/single.html` Colophon section.

`layouts/credits/single.html` — minimal layout (h1 + body + page-sidebar partial). Reuses essay-like prose layout.

### 5.5 `THIRD_PARTY.md` (new)

Repo root. Plain markdown. Format:

```markdown
# Third-party assets

## Icons

**Lucide** — https://lucide.dev — ISC License — see `LICENSES/lucide-ISC.txt`
- book-open · music · gamepad-2 · clapperboard · feather · search · rss · sun · (etc.)

## Fonts

(existing entries for Petrona / Inter / JetBrains Mono if any)
```

Linter (`check_icon_attribution.py`) asserts the file exists, parses as markdown, and contains a `## Icons` section listing Lucide.

### 5.6 Monogram-AM replacement (Final-thread Q2 = B)

`assets/images/icons/monogram-am.svg` deleted. About-hero CSS renders "AM" as a white-on-ink disc:

```css
.about-monogram {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: var(--color-ink);
  color: var(--color-stone);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-body);  /* Petrona */
  font-weight: 600;
  font-size: 2.4rem;
  letter-spacing: -0.02em;
  line-height: 1;
}
```

`layouts/about/single.html` swaps `<img src="…/monogram-am.svg">` for `<div class="about-monogram" aria-label="A.M. — Abdelrahman Madkour">AM</div>`. The `aria-label` covers SR users; the `<div>` content stays bare "AM" for visual rendering.

## 6. Hugo partial signatures

### 6.1 `partials/library/umbrella-hero.html`

```text
Input (dict):
  hero_slug:   string | nil  (from library-shelves.yaml `hero:`)
  fallback:    bool          (true when hero_slug is nil or doesn't resolve)
Output: <article class="library-hero"> block
Side effect: appends one cite-keys entry to Page.Scratch for the cite linter
```

### 6.2 `partials/library/umbrella-shelf.html`

```text
Input (dict):
  shelf:    map  (one entry from library-shelves.yaml shelves[] — title, intro, tag|items)
Output: <section class="library-shelf"> block with up to 12 tiles + See-all link if applicable
Side effect: per-tile cite-keys entries appended to Page.Scratch
```

The 12-item cap is a hardcoded constant in the partial. Change it by editing the partial; no yaml override.

### 6.3 `partials/library/umbrella-tile.html`

```text
Input (dict):
  item:     map  (one library item from data/<medium>.yaml + medium key joined in)
Output: <article class="library-tile"> block with cover + title + meta + action row
```

### 6.4 `partials/library/umbrella-catalogue.html`

```text
Input: nothing (reads site.Data.library-media + site.Data.<medium> directly)
Output: <section class="library-catalogue"> block with N <article class="library-cat-card">
```

### 6.5 `partials/library/medium-rail.html`

```text
Input: nothing (reads site.Data.library-media)
Output: <nav class="medium-rail"> with N+1 <a class="medium-pill"> (N media + "All")
```

## 7. Linters

### 7.1 `tools/check_library_shelves.py` (#18)

Asserts:

- `data/library-media.yaml` exists, parses, has `media:` list with ≥1 entry; each entry has `key` / `label` / `glyph` / `cover_aspect`.
- Each `media[].key` has a corresponding `data/<key>.yaml` AND `/library/<key>/` layout target.
- Each `media[].glyph` references a file under `assets/images/icons/<glyph>.svg`.
- `data/library-shelves.yaml` either does not exist OR parses cleanly with valid shape.
- For each shelf: exactly one of `tag:` or `items:` present.
- Tag-driven shelves: tag exists in at least one item's `tags:` across the four media yamls (warns if not, fails if shelf resolves to zero items at build).
- Slug-list shelves: every slug resolves to an item in one of the four media yamls.
- `hero:` slug (if present) resolves to a real item.
- Stub↔yaml sync: every shelf with `items:` count > 12 has `content/library/shelves/<slug>/_index.md`; every stub references a shelf in yaml.

`tools/test_check_library_shelves.py` — sibling test file. Test fixtures for: missing media yaml (fails), missing shelves yaml (passes — soft), shelf with both tag+items (fails), unresolved hero slug (warns), orphan stub (fails), missing stub for long shelf (fails).

### 7.2 `tools/check_icon_attribution.py` (#19)

Asserts:

- `THIRD_PARTY.md` exists at repo root, parses as markdown, contains `## Icons` section.
- `## Icons` section names Lucide (case-insensitive substring `lucide`).
- For every file under `assets/images/icons/*.svg`:
  - Either: file begins with the canonical header comment `<!-- Lucide v<version> — <name> · ISC License · see /THIRD_PARTY.md -->`.
  - Or: file basename appears in `tools/.icon-attribution-exceptions.yaml` (a manifest of legitimate exceptions with their own provenance documented).

`tools/test_check_icon_attribution.py` — sibling test file. Fixtures: SVG with valid header (passes), SVG without header (fails), SVG in exceptions list (passes), missing THIRD_PARTY.md (fails), THIRD_PARTY.md without Lucide mention (fails).

## 8. JS

No new JS modules. Existing `cite.js` (assets/js/cite.js) handles hero + tile cite actions via `closest('article')` — both hero and tiles use `<article>` elements, so the existing selector works unchanged.

Existing `entry-library.js` loads on `/library/<leaf>/` only today (per CLAUDE.md: `.Section == "library" AND NOT /library/`; leaves get the filter-chip handler, umbrella is JS-free). **New scope predicate** in `partials/scripts.html`: load `entry-library.js` everywhere under `.Section == "library"` — drop the `AND NOT /library/` clause. The umbrella now needs the keyboard-nav handler for shelf strips.

Add new module `assets/js/library-shelf-nav.js` imported by `entry-library.js`. ~30 LOC. Mounts a `keydown` listener per `.library-shelf-strip`; on `ArrowLeft` / `ArrowRight` focuses prev/next tile within the strip; no wraparound; no-op outside `.library-tile-link` focus.

## 9. Test plan

### 9.1 Fixtures

- `data/library-media.yaml` — 4 media (matches existing reading/listening/playing/watching).
- `data/library-shelves.yaml` — 3 example shelves: one tag-driven, one short slug-list (5 items), one long slug-list (14 items, triggers stub requirement).
- `content/library/shelves/long-example/_index.md` — corresponding stub for the long shelf.

### 9.2 CI sequence

Add 2 named workflow steps to `.github/workflows/hugo.yaml`:

- `check_library_shelves.py` + sibling test → between existing `check_library_covers.py` and `check_pagefind_meta.py`.
- `check_icon_attribution.py` + sibling test → between `check_library_shelves` and `check_pagefind_meta`.

Workflow grows: 46 → 48 named steps.

### 9.3 Smoke

`tools/check_smoke.py` already covers `/library/`. Add `/credits/` to its URL list.

### 9.4 Page-weight

`tools/check_page_weights.py` classifier:

- `/library/` stays at 500 KB.
- `/library/shelves/<slug>/` added at 500 KB (same as umbrella).
- `/credits/` added at 100 KB (minimal page).

### 9.5 Pagefind

`/credits/` page must be Pagefind-indexed. `partials/library/umbrella-catalogue.html` and `umbrella-shelf.html` ensure tile elements participate in the existing `data-pagefind-body` scope.

## 10. Spec-§1 hard-constraint compliance

This slice closes a hard-constraint violation (icon provenance). Compliance going forward:

- All SVGs under `assets/images/icons/` carry attribution headers + appear in `THIRD_PARTY.md`.
- Linter gates new commits.
- Any future user-drawn icon goes through the exceptions manifest with a one-line provenance note.
- AI MAY NOT draft new SVG path data (memory `feedback_no_ai_visuals_in_mockups` + `feedback_icon_provenance_required`).
- AI MAY commit assets directly fetched from documented OSS sets.

## 11. Memory entries referenced

- `feedback_semantic_consistency_site_wide` — drives the neutral-disc-badge decision, documents the no-cover tinted-block deviation.
- `feedback_no_ai_visuals_in_mockups` — kept this brainstorm's mockups Lucide-only.
- `feedback_icon_provenance_required` — direct motivation for Layer 2.
- `feedback_visual_companion_for_visual_designs` — drove the browser-mockup-first walkthrough.
- `reference_duplicate_id_anchor_race` — informs the cite-cta button-vs-anchor choice; carries forward unchanged.

## 12. Deferred from this slice

- **Per-icon stroke-width tuning** at 22px badges — defer to QA pass; only fix specific icons that fail in production.
- **Pre-commissioned per-size SVG variants** — defer indefinitely; revisit only if multiple icons fail QA.
- **Audit + delete of unused icons** (`code.svg` / `note.svg` / `talk.svg` if no references) — handle during implementation, not deferred.
- **`/credits/` markdown body content** — minimal version ships in this slice; expand as the third-party asset list grows.

## 13. Done criteria

- All 11 icons under `assets/images/icons/` have Lucide replacements + header attribution comments.
- `THIRD_PARTY.md` exists and links Lucide.
- `/credits/` page renders.
- `monogram-am.svg` deleted; About hero renders CSS "AM" in disc.
- `data/library-media.yaml` + `data/library-shelves.yaml` exist with example shelves.
- `/library/` renders the new shape (hero + ≥1 shelf + catalogue).
- `/library/shelves/long-example/` renders the long-shelf detail page.
- `check_library_shelves.py` + sibling test pass on the fixtures.
- `check_icon_attribution.py` + sibling test pass on every SVG.
- All existing linters pass.
- Contrast linter passes (no new tokens added).
- Lighthouse CI mobile + desktop pass with `/library/` (500 KB ceiling holds).
- Smoke test passes on all top-level URLs including `/credits/`.
- Manual eyeball at half-screen-1080p (~960px) and ~720px breakpoint per `feedback_test_at_half_screen_1080p`.
