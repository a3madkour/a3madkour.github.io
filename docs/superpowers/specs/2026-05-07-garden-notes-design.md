# Garden notes — slice design

**Status:** approved · **Date:** 2026-05-07 · **Slice:** Phase 2 (continuation) — Garden notes
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §4.5–§4.9, §6.1–§6.6, §14
**Predecessor slice:** `docs/superpowers/specs/2026-05-05-essays-section-design.md` (essays — establishes patterns this slice extends)

---

## 0. Context for future Claude sessions

This slice ships the Garden section: note pages, the `/garden/` index, multi-dimension filter chips, and the spoiler shortcode runtime. It also refactors the essays filter chips to share one module with garden's. The org-mode pipeline (Phase 3) is **not** in this slice — fixtures are hand-authored placeholders in the same shape ox-hugo will eventually produce.

**The slice spec amends parent §4.9.** Topic maps are no longer their own URL at `/garden/topics/<slug>/`. They're an optional facet of any note: a note with `topic_map: [slug, ...]` in its frontmatter renders both its prose body and a curated tile grid of referenced notes. One canonical URL per idea. The parent spec should be read with this amendment in mind; revisit when authoring future slices that touch Garden.

**Decisions made during brainstorm** (referenced from §2 of this doc, but called out here for fast scanning):
- Single Hugo template for all garden notes; flavor (concept/media/reference) inferred from `media_type`
- Topic-map facet (`topic_map: [slug, ...]`) rather than separate topic-map URLs
- Garden index = topic-map sections + "Other notes" catch-all
- Multi-dimension filter chips compose with AND (per memory `feedback_filter_chips_compose`)
- Hand-authored SVG growth-stage glyphs (seedling sprout / budding two-leaf / evergreen tree)
- Spoiler runtime via native `<details>` (no JS), replacing the no-op stub from the essays slice
- 14-note fixture set covering all UI states (3 stages × 4 statuses × 3 spoiler-levels)

---

## 1. Slice scope

### In scope
1. Garden note page (`layouts/garden/single.html`) — single template; flavor routing in `partials/garden/note-header.html`
2. `topic_map:` frontmatter facet — ordered slug list; renders tile grid below body and drives index sections
3. Garden index (`layouts/garden/list.html`) — topic-map sections + "Other notes" catch-all
4. Multi-dimension AND filter chips (tag, flavor, stage); empty intersection → empty-state message; sections with zero visible notes collapse
5. Hand-authored SVG growth-stage glyphs in a single partial
6. `spoiler` shortcode — `<details>`-based click-to-reveal, replaces the no-op stub from essays slice
7. Per-section RSS feed at `/garden/index.xml`
8. **Refactor**: essays' inline `setupFilterChips` factored into `assets/js/filter-chips.js`; both essays and garden use it; essays migrate from single-active to multi-dimension AND
9. 14-note fixture set with linter (`tools/check_garden_fixtures.py` + unit tests)
10. CSS sections 19–23 added to `assets/css/main.css`; §16 (filter strip) generalized to multi-dim chips

### Deferred (kept as visible/round-trippable hooks)
- Outgoing-link section on note pages — Phase 4 (needs org-roam ID resolver)
- Backlinks section on note pages — Phase 4
- Graph view + stacked-columns retrieval + path log — Phase 4
- Citation hover-card runtime — Phase 3 (fixtures may carry `roam_refs` but currently no-op)
- Library cross-linking from media notes — Phase 7
- Media-type-specific embeds (audio player, game iframe) — Phase 6 / Phase 7

### Out of slice (explicit)
- About page rewrite + Now widget (Phase 3-dependent)
- Topic-map page at `/garden/topics/<slug>/` — replaced by `topic_map` facet on note pages; parent spec §4.9 amended
- Print stylesheet (Phase 8)
- Pagefind indexing (Phase 8)
- Multi-flavor visual differentiation beyond the metadata strip (concept/media/reference share the same body styling)

---

## 2. Decisions captured during brainstorm

| Decision | Reasoning | Where it lives |
|---|---|---|
| Topic maps are a note facet, not a separate URL | In org-roam, every topic map IS a note. Two URLs for the same idea creates duplication risk. One canonical URL per idea matches the org-roam grain. | §3, §4.2 |
| Garden index = topic sections + Other notes | Spec primary intent is curated browsing. Notes not yet in any topic map need a home; "Other notes" is honest about the gap. | §4.1 |
| Filter chips: multi-dimension AND | "If the user wants budding notes that are part of a given tag, they should be able to apply both." Single-active across dimensions makes intersections impossible. | §4.7, §4.9, memory |
| Iconography: hand-authored SVG sprout/two-leaf/tree | Reinforces "garden" feel; consistent with hard constraint (no AI-generated illustrations); colour-coded for CB-safe + label fallback. | §4.4, §5.4 |
| Spoiler runtime via `<details>` | Native semantics, no JS, accessible by default. Click-to-reveal matches spec §5.4. | §4.8 |
| Refactor essays to multi-dimension AND too | Long-term consistency; cost is small; the new pattern is the right pattern. (User: "I don't see any reason why we can't do the best strategy for the long term here.") | §4.7, §4.11 |
| Bump fixtures to 14 (from 12) | Round out coverage of `abandoned` status pill and `heavy` spoiler-level, since each is a distinct rendering path. (memory: deferred features stay visible.) | §8 |

---

## 3. Architecture

### 3.1 New + modified files

**New layouts:**
```
layouts/garden/list.html              — index page
layouts/garden/single.html            — note page (all flavors)
layouts/garden/rss.xml                — section RSS
layouts/partials/garden/note-header.html      — flavor-routed metadata strip
layouts/partials/garden/stage-glyph.html      — SVG glyph by stage + size
layouts/partials/garden/note-tile.html        — single tile card
layouts/partials/garden/topic-section.html    — H2 + framing + tile grid
layouts/partials/filter-chips.html            — shared filter strip (essays + garden)
layouts/shortcodes/spoiler.html               — replaces no-op stub
```

**New assets:**
```
assets/js/filter-chips.js   — shared multi-dimension AND module
assets/js/garden.js         — page-level guard + filter init for garden
```

**New tooling:**
```
tools/check_garden_fixtures.py
tools/test_check_garden_fixtures.py
```

**New fixture content** (14 page bundles under `content/garden/<slug>/index.md` — see §8 for full attribute coverage):
```
procedural-narrative/         memory-in-play/             surprise-budget/
salience-and-memory/          emergence-vs-design/        story-atoms/
sleep-and-consolidation/      recall-vs-replay/           the-save-game/
invisible-cities/             koyaanisqatsi-soundtrack/   outer-wilds/
severance-s2/                 nguyen-2020-games-as-art/
```

`content/garden/_index.md` rewritten — drop the "(Coming soon.)" placeholder, add a one-paragraph lede.

**Modified:**
```
assets/css/main.css                 — generalize §16 (filter strip) to multi-dim chip styles;
                                      append §19 Garden index, §20 Note header strip + status pill,
                                      §21 Note tile, §22 Spoiler runtime, §23 Empty-state placeholder
assets/js/index.js                  — import filter-chips.js + garden.js
assets/js/essay.js                  — drop inline setupFilterChips; import shared module in 'and' mode
layouts/essays/list.html            — chip strip → call shared partial
.github/workflows/hugo.yaml         — add check_garden_fixtures.py and unit tests as CI gates
```

**Untouched (declared explicitly):**
`data/citations.yaml`, all essay fixtures and `tools/check_fixtures.py`, header/footer/head partials, theme toggle, base templates, hero illustrations, homepage essays strip.

### 3.2 Top-level decisions baked into the layout

- All garden URLs are flat: `/garden/<slug>/`. There is no `/garden/topics/<slug>/`.
- Flavor is a derived property, not a frontmatter field. Single source of truth: presence/value of `media_type`.
- `topic_map: [slug-1, slug-2]` is the *only* way a note becomes a topic-map node. No separate `is_topic_map` flag.
- Tile rendering is uniform — no variable-tile / Bento sizing in Garden (unlike Essays). Stage glyph is the only visual differentiator on tiles.
- The same `partials/filter-chips.html` partial powers both `/essays/` and `/garden/` — chip dimensions are passed in as a parameter, suppression rule (<2 distinct values → don't render) carried over from essays slice.
- "Active state" is per-dimension. Resetting a single chip to `all` does not affect other dimensions.

---

## 4. Components

### 4.1 `layouts/garden/list.html` — index template

Top-down structure:
1. Page title (`Garden`) + lede from `_index.md` body
2. `partials/filter-chips.html` rendering tag + flavor + stage dimensions, suppressing dims with <2 distinct values
3. Topic-map sections — for each garden page where `.Params.topic_map` is set, in `weight` order then alphabetical:
   - Calls `partials/garden/topic-section.html` with `.context = page`
   - That partial renders: H2 link to the topic-map note, italic framing (first paragraph of body, plain-text), then a tile grid in the order specified by `topic_map`, resolving each entry via `where (where .Site.RegularPages "Section" "garden") "File.ContentBaseName" slug`
4. "Other notes" section — every garden page not referenced in any other note's `topic_map` array, in `last_modified` desc order
5. Empty-state placeholder div with `hidden` attribute by default; JS toggles visible when filter intersection is empty

The "is this note referenced anywhere" computation is a single template pass: build a set of all referenced slugs from all garden pages' `topic_map` arrays, then emit any page whose slug isn't in that set.

### 4.2 `layouts/garden/single.html` — note template

Layout (single column, max ~720px):
1. Crumb (`Garden ›`) — links to `/garden/`
2. `partials/garden/note-header.html` — branches on flavor (see §4.3)
3. Title (Petrona 700, ~1.6rem)
4. Creator line (Petrona italic) — only for media + reference flavors
5. Media-meta row (`→ original` + media-type meta) — only for media + reference flavors
6. `.Content` — body rendered through Hugo's standard markdown pipeline; supports `cite`, `sidenote`, `figure`, and the new `spoiler` shortcode
7. Topic-map tile section — only when `.Params.topic_map` is set; calls `partials/garden/topic-section.html` with `.heading = "Notes in this topic"` and `.framing = "Curated reading order, not chronological."`
8. Outgoing-links + backlinks sections **omitted entirely** in this slice (Phase 4 deferral)

### 4.3 `partials/garden/note-header.html`

Flavor-routed metadata strip. The strip is a flex row with the following slots, in order:
- Stage glyph + label (always — `partials/garden/stage-glyph.html` with size=lg)
- Tended date — `tended Nd ago` (computed from `.Params.last_modified`; uses Hugo's `time.Format` and a small relative-date helper)

Then, for media flavor only (`media_type ∈ {book, album, track, game, film, series}`):
- Status pill — CB-safe shape + colour. Shapes:
  - `reading` → filled circle, steel
  - `finished` → check, green (`#2d5a3d`)
  - `abandoned` → ×, burgundy
  - `queued` → arrow-up, warn (`#a05a1a`)
- Started date — only if `.Params.started` present
- Spoiler-level warning — only if `.Params.spoiler_level` is `light` or `heavy`; renders as `⚠ light spoilers` or `⚠ heavy spoilers` in burgundy plain text

For reference flavor only (`media_type ∈ {paper, video, article, talk}`):
- Uppercase media-type label (e.g., `PAPER`, `TALK`) in `--color-ink-fade`

### 4.4 `partials/garden/stage-glyph.html`

Inputs: `stage` (one of `seedling | budding | evergreen`), `size` (`lg | sm | xs`, default `sm`).

Hugo template branches on `stage`, returning inline SVG with `currentColor` stroke. Stroke widths and viewbox scaled per `size`:
- `lg` → 20px, stroke-width 1.6
- `sm` → 14px, stroke-width 1.6
- `xs` → 11px, stroke-width 1.8 (heavier weight at small size for legibility)

The three SVG paths (final, with viewBox 0 0 24 24):

**Seedling** — single sprout above soil baseline:
```
M12 21 V13
M12 15 C9 14 7 11 7 8 C10 8 12 11 12 14
M3 21 H21
```

**Budding** — stem with two opposed leaves:
```
M12 21 V11
M12 14 C8 13 6 10 6 7 C9 7 11 9 12 12
M12 13 C15 12 17 9 17 6 C14 6 12 8 12 11
```

**Evergreen** — triangular tree silhouette with trunk:
```
M12 4 L7 12 H10 L7 18 H17 L14 12 H17 Z
M12 18 V21
```

Stroke colour assigned by consumer CSS class:
- `.stage-seedling` → `--color-burgundy`
- `.stage-budding` → `--color-steel`
- `.stage-evergreen` → `#2d5a3d` (added as `--color-green` token in §20)

### 4.5 `partials/garden/note-tile.html`

Inputs: `.page` (target Hugo page), optional `.size` (default `md`).

Renders:
```html
<a class="garden-tile" href="{{ .page.RelPermalink }}"
   data-tags="{{ delimit .page.Params.tags " " }}"
   data-flavor="{{ derive flavor }}"
   data-stage="{{ .page.Params.growth_stage }}">
  <div class="tile-stage">
    {{ partial "garden/stage-glyph.html" (dict "stage" .page.Params.growth_stage "size" "sm") }}
    <span class="tile-stage-label">{{ title .page.Params.growth_stage }}</span>
  </div>
  <p class="tile-title">{{ .page.Title }}</p>
  <div class="tile-meta">tended {{ relativeDate .page.Params.last_modified }}</div>
</a>
```

The `data-*` attributes drive the filter JS. Flavor is derived inline (concept / media / reference based on `media_type`).

### 4.6 `partials/garden/topic-section.html`

Inputs: `.context` (page that owns the topic_map), optional `.heading` (default = page title), optional `.framing` (default = first paragraph of `.context.Content`).

Renders an H2 link, italic framing, and a tile grid resolved by iterating `.context.Params.topic_map` and looking up each slug.

### 4.7 `partials/filter-chips.html` (shared)

Replaces the inline chip strip in `layouts/essays/list.html`. Inputs:
- `dimensions` — list of dimension specs, each `{key, label, values}`
- `mode` — `single` (legacy essays behavior, kept for compat) or `and` (new default)

Renders the strip; each dimension only renders if `len(values) >= 2` (suppression rule). Each chip carries `data-dim` and `data-key`. Container has `data-filter-mode={mode}`.

Note: the `mode: single` branch is a transitional accommodation. **All callers will use `and` after this slice.** The branch exists so the partial can be introduced without breaking essays during incremental development; once both pages migrate, the `single` branch should be removed in a follow-up — tracked in §11.

### 4.8 `layouts/shortcodes/spoiler.html`

Replaces the no-op stub from the essays slice. Body:
```html
<details class="spoiler" data-spoiler-level="{{ .Get "level" | default "light" }}">
  <summary>{{ .Get "summary" | default "spoiler" }}</summary>
  <div class="spoiler-body">{{ .Inner | markdownify }}</div>
</details>
```

Authoring form: `{{< spoiler summary="chapter ending" level="light" >}}…{{< /spoiler >}}`. Click-to-reveal is `<details>` native; no JS needed. Reduced-motion respected by default (no animation; CSS only sets the open/closed arrow).

### 4.9 `assets/js/filter-chips.js` (shared module)

Exports `setupFilterChips(container)`. Reads `data-filter-mode` from container. Two modes:

**`and` mode (garden + post-refactor essays):**
- State: `{[dim]: activeKey}` map, all initialized to `"all"`
- Click handler: set `state[dim] = clickedKey`; re-render chip active states; re-evaluate every card
- Card visibility: a card is visible iff for every dimension where state is not `"all"`, the card's `data-{dim}` value contains the active key
- After update, scan section wrappers (`[data-section]`) and toggle `hidden` based on whether they contain any visible cards
- After update, toggle the empty-state element based on global card visibility count

**`single` mode (transitional):** carried over from current essays behavior, single chip active across all dimensions. Removed after follow-up.

**Tag matching:** `data-tags` is a space-separated list. Active key matched as a whole-word substring (so "memory" matches `data-tags="memory narrative"` but not `data-tags="working-memory"`).

### 4.10 `assets/js/garden.js`

Page-level entry. Guard: `document.querySelector('.garden-grid, .garden-note')` — bail on non-garden pages. If on a garden index, find `.filter-chips[data-filter-mode]` and call `setupFilterChips`. (No per-note-page JS in this slice — spoilers are CSS+native, citations are deferred.)

### 4.11 Essay refactor (consequence of choosing approach C)

`assets/js/essay.js` deletes its inline `setupFilterChips` function and imports from `filter-chips.js`. The call site changes from single-active to AND mode. `layouts/essays/list.html` swaps its inline `<div class="filter-strip">…</div>` for a `{{ partial "filter-chips.html" (dict "dimensions" essayDims "mode" "and") }}` call.

User-visible behavior change: combining a tag chip with a series chip now narrows to the intersection (previously the second click cleared the first). This is intentional — it's a strict improvement and aligns with the new feedback memory.

---

## 5. Data flow

### 5.1 Frontmatter contract

`content/garden/<slug>/index.md`:

```yaml
---
# Always required
title:           string
draft:           bool
last_modified:   YYYY-MM-DD
growth_stage:    seedling | budding | evergreen

# Required for media notes
media_type:      book | album | track | game | film | series
status:          reading | finished | abandoned | queued
creator:         string

# Required for reference notes
media_type:      paper | video | article | talk
creator:         string

# Optional (any flavor)
tags:            [string]
summary:         string             # framing italic on topic-map tile section if topic_map set
topic_map:       [slug]             # ordered; turns this note into a topic-map node
roam_refs:       string             # bib key — Phase 3 hook, not used in this slice
year:            int

# Optional (media + reference)
original_url:    string

# Optional (media only)
started:         YYYY-MM-DD
finished:        YYYY-MM-DD
spoiler_level:   none | light | heavy   # default none
---
```

**Resolution rules** (linter-enforced):
- `media_type` absent → flavor=concept; `status`/`started`/`finished`/`spoiler_level`/`original_url`/`creator`/`year` rejected
- `media_type ∈ {book, album, track, game, film, series}` → flavor=media; `status` + `creator` required, others optional per above
- `media_type ∈ {paper, video, article, talk}` → flavor=reference; `creator` required; `status`/`started`/`finished`/`spoiler_level` rejected
- `topic_map` entries must each resolve to an existing `content/garden/<slug>/index.md`; entry pointing to a draft note fails the linter
- `last_modified` ≤ today
- `growth_stage`, `status`, `spoiler_level` values must be one of their enum sets
- A note may carry `topic_map` regardless of flavor (concept notes are the natural case, but media/reference notes can also act as topic maps if useful)

### 5.2 Topic-map resolution

At template time, for a note with `topic_map: [a, b, c]`:
```go
{{ range .Params.topic_map }}
  {{ with where (where $.Site.RegularPages "Section" "garden") "File.ContentBaseName" . }}
    {{ partial "garden/note-tile.html" (dict "page" (index . 0)) }}
  {{ else }}
    {{ errorf "topic_map entry %q on %q does not resolve" . $.RelPermalink }}
  {{ end }}
{{ end }}
```

The linter catches unresolvable entries before Hugo runs; the `errorf` is a defense-in-depth guard.

### 5.3 Garden index aggregation

Two passes over `where .Site.RegularPages "Section" "garden"`:

**Pass 1 (build referenced-slug set):**
```
referenced = set()
for page in garden_pages:
    for slug in page.Params.topic_map (default []):
        referenced.add(slug)
```

**Pass 2 (render):**
```
for page in garden_pages where page.Params.topic_map:
    render topic-section for that page
for page in garden_pages where slug not in referenced and not page.Params.topic_map:
    add to "Other notes" tile list
render "Other notes" section (sorted by last_modified desc) if non-empty
```

A topic-map note is itself NOT added to "Other notes" even though it isn't referenced by anything — its presence is implied by its own section heading.

### 5.4 Filter chip state model

`window.Garden.filterState = {tag: "all", flavor: "all", stage: "all"}` after init. Click handler reads `dim` and `key` from data attributes, updates state, re-renders. `data-tags="memory narrative"` allows multi-tag membership.

Section collapsing: each `<section data-garden-section>` wrapper is hidden when none of its children pass the filter. The empty-state element (a `<div class="garden-empty" hidden>`) is toggled when no cards globally pass.

### 5.5 RSS section feed

`layouts/garden/rss.xml` — Hugo's built-in RSS template, customized to:
- Use `last_modified` rather than `date` for `<pubDate>`
- Title format: `Garden — Abdelrahman Madkour`
- Description: from `summary` if present, else first paragraph of body
- Enclose only published (non-draft) notes

Header partial's RSS button switches feed URL when on `/garden/...` paths (existing per-section logic from essays slice).

### 5.6 Phase 3 handoff (no layout changes when real content arrives)

When the elisp / ox-hugo pipeline replaces fixtures:
- Frontmatter shape is identical; ox-hugo writes the same fields
- `topic_map` becomes a derived field — exporter walks `[[id:UUID]]` ordered list in the org topic-map note's body and converts to slug list
- `roam_refs` populated from `:ROAM_REFS:`; cite shortcode (Phase 3) renders the hover-card
- Fixture deletion is a separate commit; layouts/partials/JS unchanged

---

## 6. Error handling & edge cases

### 6.1 Build-time failures (must block deploy)

| Case | Message |
|---|---|
| Required field missing for flavor | `<file>: <field> is required for <flavor> notes` |
| Forbidden field present | `<file>: <field> not permitted on <flavor> notes` |
| Invalid enum value | `<file>: <field>=<value> not in {…}` |
| `topic_map` entry doesn't resolve | `<file>: topic_map[<i>]=<slug> does not resolve to an existing note` |
| `topic_map` references draft note | `<file>: topic_map[<i>]=<slug> is a draft; drafts cannot be in published topic maps` |
| `last_modified` in future | `<file>: last_modified <date> is in the future` |
| Malformed date | `<file>: <field>=<value> is not a valid YYYY-MM-DD date` |
| `original_url` not http/https | `<file>: original_url must be http(s)` |

### 6.2 Build-time tolerable warnings (don't block)

- Unrecognized tag (no controlled vocabulary check — tags are free-form, per parent §6.6) — warned with file path, no block
- Duplicate slug in `topic_map` — warned (slot dedupes), no block

### 6.3 Runtime / progressive enhancement

- JS disabled: filter chips are inert visually but don't break layout (chips render statically; nothing is hidden by default). Fallback: tag-chip text labels still link to `/tags/<slug>/` taxonomy pages (Hugo built-in, unchanged from essays slice).
- `localStorage` denied (private browsing strict): no impact on garden — no filter state is persisted, every page load starts fresh
- `prefers-reduced-motion`: spoiler `<details>` open/close has no animation (no transitions defined); already fine

### 6.4 Layout edge cases

| Case | Behavior |
|---|---|
| Note has `topic_map` but no body | Empty framing italic, tile grid below; valid |
| Empty `topic_map: []` (zero entries) | Renders the H3 heading + framing + an empty grid; arguably should error — linter flags as warning |
| Note referenced in multiple `topic_map` arrays | Tile renders in each; not deduped (intentional — same note can belong to multiple curated reading orders) |
| Garden has zero notes | Index shows lede + empty-state placeholder ("No notes yet — check back soon") |
| Garden has notes but all are drafts | Same as zero notes (drafts excluded from production builds) |
| All notes in one topic map (no orphans) | "Other notes" section omitted entirely |
| All notes orphaned (no topic maps) | Only "Other notes" section renders |
| Filter combo has zero matches | All sections collapsed; empty-state message visible |

### 6.5 Out of error-handling scope

- Network failures (no fetch in this slice)
- Race conditions in filter init (filter init runs after DOMContentLoaded; chips inert until then but visible)
- Image/SVG load failures (SVG is inline; can't fail to load)

---

## 7. Testing & verification

### 7.1 Automated CI gates (must pass to deploy)

Added to `.github/workflows/hugo.yaml` after the existing essay linter step:
1. `python3 tools/check_garden_fixtures.py`
2. `python3 -m unittest tools/test_check_garden_fixtures.py -v`

Existing CI gates that must continue to pass:
- `python3 tools/check-contrast.py`
- `python3 tools/check_fixtures.py` + `python3 -m unittest tools/test_check_fixtures.py -v`
- `hugo --minify` exits clean (no warnings)

### 7.2 Manual walkthrough checklist

- Click each filter dimension's chips in isolation — only that dimension's active state changes
- Click chips across two dimensions — AND intersection holds
- Click chips creating an empty intersection — empty-state message shows; sections collapse
- Reset all chips to `all` — every card visible, all sections shown
- Open and close every spoiler block on `invisible-cities` (1 block) and `severance-s2` (multiple blocks)
- Cycle theme system → light → dark → system on each page (`/garden/`, a topic-map note, a media note, a reference note) — colours render correctly in both modes
- Resize to 480px / 768px / 1200px — strip, tiles, and grid reflow gracefully; chips wrap; status pill stays inline
- Keyboard: Tab through chips and tiles; Enter activates; focus rings visible; spoiler details element keyboard-toggleable
- Screen reader (VoiceOver / NVDA): chip dimension labels announced before chip values; stage glyph carries an `aria-label` of the stage name; empty-state message announced when revealed

### 7.3 Essay regression check

- `/essays/` index loads; chip filtering still works (now multi-dimension AND — visible improvement, not regression)
- Existing essay fixture frontmatter linter passes
- An essay tag + series chip combination narrows to intersection (was previously single-active behavior)

---

## 8. Fixture set

14 notes covering all UI states: every growth stage, every media-status pill, every spoiler-level, both topic-map shapes (4 children, 3 children), and a non-empty "Other notes" group. Every body uses lorem ipsum or "Example sentence N" — never authored prose.

| # | Slug | Flavor | Stage | Status | Spoiler | Topic-map role | Tags | Body exercises |
|---|---|---|---|---|---|---|---|---|
| 1 | `procedural-narrative` | concept | budding | — | — | self: 4 children (3, 4, 5, 6) | narrative, games | prose + internal link |
| 2 | `memory-in-play` | concept | budding | — | — | self: 3 children (7, 8, 9) | memory, play | plain prose |
| 3 | `surprise-budget` | concept | budding | — | — | in PN | narrative | `sidenote` shortcode |
| 4 | `salience-and-memory` | concept | seedling | — | — | in PN | memory, narrative | back-target for #3 |
| 5 | `emergence-vs-design` | concept | evergreen | — | — | in PN | narrative | plain prose |
| 6 | `story-atoms` | concept | budding | — | — | in PN | narrative | `figure` shortcode |
| 7 | `sleep-and-consolidation` | concept | seedling | — | — | in MIP | memory | plain prose |
| 8 | `recall-vs-replay` | concept | budding | — | — | in MIP | memory, play | plain prose |
| 9 | `the-save-game` | concept | evergreen | — | — | in MIP | memory, games | plain prose |
| 10 | `invisible-cities` | media (book) | budding | reading | light | Other notes | reading, calvino | 1 `spoiler` block + `roam_refs` hook |
| 11 | `koyaanisqatsi-soundtrack` | media (album) | evergreen | finished | none | Other notes | listening, glass | plain prose |
| 12 | `severance-s2` | media (series) | budding | abandoned | heavy | Other notes | series, mystery | 3 `spoiler` blocks |
| 13 | `outer-wilds` | media (game) | seedling | queued | none | Other notes | playing, games | plain prose |
| 14 | `nguyen-2020-games-as-art` | reference (paper) | evergreen | — | — | Other notes | games, aesthetics | `roam_refs` hook |

**Coverage matrix:**
- Stages — seedling: 3, budding: 7, evergreen: 4 (all three present)
- Statuses (media only) — reading: 1, finished: 1, abandoned: 1, queued: 1 (all four present)
- Spoiler-levels (media only) — none: 2, light: 1, heavy: 1 (all three present)
- Flavors — concept: 9 (incl. 2 topic-map), media: 4, reference: 1
- Topic-map sections on `/garden/`: 2 (PN with 4 tiles, MIP with 3 tiles); Other notes: 5 tiles (#10–#14)

---

## 9. Deferred features (must stay in plan)

This slice ships these as round-trippable hooks. When the dependent slice lands, the fixture content immediately verifies the new runtime:

| Feature | Phase | Round-trip hook |
|---|---|---|
| Outgoing-link section on note pages | 4 | Body internal links use `[text](/garden/<slug>/)` form |
| Backlinks section | 4 | Computed at build time from outgoing links — fixture #4 (`salience-and-memory`) is referenced from #3 (`surprise-budget`) body |
| Stacked-columns retrieval + path log | 4 | (No fixture hook — pure UX layer) |
| Garden graph view | 4 | (Pure UX — `data/notes.json` arrives in Phase 3) |
| Citation hover-card runtime | 3 | `roam_refs` field accepted by linter on media + reference flavors; at least one fixture (#10, #14) carries one |
| Library cross-linking | 7 | media-flavor notes are the canonical source; library will be a filtered view |

---

## 10. Open questions inherited from parent spec

These don't block this slice but should be revisited when the next slice depending on Garden lands:

1. **Spec §4.9 amendment.** This spec amends parent §4.9 (no separate `/garden/topics/<slug>/` URL). When the parent spec is next touched, fold this amendment into §4.9 inline.
2. **`single` mode in `filter-chips.js`.** Transitional shim; remove in a follow-up after both essays + garden have shipped on `and` mode.
3. **Topic-map ordering.** Currently topic-map sections on the index render in `weight` then alphabetical order. Future: a configurable order field on each topic-map note's frontmatter.
4. **Tag normalization.** Tags are free-form per spec §6.6. Slug-normalize on render, but no controlled vocabulary check yet — revisit when Garden starts to feel cluttered.
5. **Empty-state copy.** "No notes yet — check back soon" / "No notes match these filters yet." — revisit when real content lands; placeholder until then.

---

## 11. Pointers

- **This spec:** `docs/superpowers/specs/2026-05-07-garden-notes-design.md`
- **Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §4.5–§4.9
- **Predecessor slice:** `docs/superpowers/specs/2026-05-05-essays-section-design.md`
- **Implementation plan (next):** `docs/superpowers/plans/2026-05-07-garden-notes.md` — produced via `superpowers:writing-plans`
- **Visual mockups (transient, gitignored):** `.superpowers/brainstorm/<session>/content/*.html` — these capture index options, topic-vs-note distinction, note variants, iconography, components walkthrough

*End of slice spec.*
