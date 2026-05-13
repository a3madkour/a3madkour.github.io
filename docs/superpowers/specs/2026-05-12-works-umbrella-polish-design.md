# Works umbrella polish — design spec

**Date**: 2026-05-12
**Phase**: 6 (works section, post-merge polish — "Slice 0" of the next Phase-6 slice)
**Status**: design approved, plan pending
**Amends**: parent spec §4.13 (works umbrella)
**Inherits constraints from**: parent spec §1 (no AI art, no AI text, accessibility, fixture-only content)

---

## 1. Motivation

After merging the first works slice (2026-05-12), the `/works/` umbrella shipped as parent spec §4.13 originally specified — three bordered overview cards (title + item count + 3 recent titles + "All X →"). The author reviewed it on the dev server and called it "pretty bland." The spec was lightly specced; the implementation matched.

The umbrella is the creative-self landing — visitors arrive here to see what kind of maker the author is across three mediums. The shipped version reads as a list-of-lists; the wireframe energy needs to be a small landing surface with personality.

Three side-quests motivate the redesign:

1. **Type-glyph SVGs** (parent §3) — gamepad / eighth-note / quill — are spec'd but not yet hand-authored. They'll also feed the future Phase 7 homepage Studio strip; this slice authors them once for double-duty.
2. **Cross-medium connections** (`lyrics_poem ↔ set_to_music` round-trips, etc.) already live in fixtures but go visually unused on the umbrella. The umbrella is the natural place to make them visible.
3. **Existing infrastructure** (filter-chips partial, essays-Bento variable-tile grid, §27 shared graph CSS, research-graph copy-trim pattern) supports a richer landing without inventing new primitives.

## 2. Scope

**In scope (this slice):**

- Hand-author three SVG type-glyphs (`glyph-game.svg`, `glyph-music.svg`, `glyph-poetry.svg`) in `assets/images/icons/`.
- Rewrite `layouts/works/list.html` and replace `partials/works/section-card.html` (deleted) with a new Bento variable-tile grid + tag-cloud filter + medium chips + ⊞ Graph view toggle.
- Add a force-directed constellation panel for the umbrella, copied + trimmed from `research-graph.js`.
- Add a standalone `/works/graph/` page as the mobile fallback (≤720px) and deep-link target.
- Surface cross-medium references (existing fixture data) as "↔" annotations on Bento tiles.
- Extend `assets/css/main.css` §33 (works umbrella + games) — replace the current umbrella block in place; add a new §36 for the works graph (mirrors §31 research-graph).
- Extend `data/filter-chips.yaml` with a `works` key for the umbrella.
- Split the works JS bundle: page-narrow predicate `/works/` and `/works/graph/` get the graph-enabled bundle; per-item works pages stay on the existing 6 KB bundle.

**Out of scope (deferred to later slices):**

- `/works/games/`, `/works/music/`, `/works/poetry/` sub-indexes — unchanged. They keep their per-section filter chips (status/kind/tag for games; format/tag for music; collection/tag for poetry).
- Per-item page templates — unchanged.
- Runtime deferrals (game iframe embed, music platform iframe, custom audio player, synced-lyrics runtime, audio-pill pulse, gif-vs-hero toggle) — still deferred; CLAUDE.md "Deferred features" table is unchanged.
- New fixtures or fixture rewrites. The 12 existing fixtures stay; the slice adds optional `tile_size`/`featured`/`hero` to 4–5 of them so the Bento has visible variation.
- The future homepage Studio strip (Phase 7). The three SVG glyphs ship here; the homepage strip that consumes them comes later. Authored once, used twice.
- Per-medium taglines on the umbrella. The umbrella has no medium headers in the Bento — taglines are unnecessary.

## 3. Visual design

### 3.1 Page header

```
Works
Games, music, and poetry. Pick a thread, scan the whole sprawl, or open the constellation.
```

H1 in body type (Petrona, 1.8rem, weight 600); intro line italic, `--color-ink-soft`. No hero illustration.

### 3.2 Filter strip

Two-row strip rendered by the existing `partials/filter-chips.html`:

- **Row 1 — Tag dim** (multi-select, AND): two-tier rendering. Primary chips inline from `data/filter-chips.yaml` works.primary_tags (manual curation), secondary chips in the native `<details>` disclosure with search input. Suppressed if <2 tag values across all works.
- **Row 2 — Medium dim** (single-active, mutually exclusive): chips for `All` / `Games` / `Music` / `Poetry`. Counts appear in `<span class="n">N</span>` per chip.
- **Sort dropdown** (right-aligned): featured · chronological · random. Default = featured.
- **⊞ Graph view toggle** (right-aligned, after sort): burgundy outline button. Click reveals the constellation panel.

Active-state model is unchanged from the existing partial — per-dimension AND across dimensions; multi-select within tag dim only.

### 3.3 Bento grid (default view)

Variable-tile grid mirroring the essays-index pattern. Cards carry `data-tile-size` and `data-span` resolved per priority in a new `partials/works/tile.html`:

- **Tile size**: explicit `tile_size: large|medium|small` > `featured: true` (large) > medium (default).
- **Span**: `featured: true` → 2 cols; `hero: true` → 2 rows. Combined: `2×1 / 1×2 / 2×2 / 1×1`.

CSS reads `data-span` on each tile and applies `grid-column: span N` / `grid-row: span N`. Grid: `repeat(auto-fit, minmax(220px, 1fr))` desktop; 2 cols at ≤720px; 1 col at ≤480px.

Tile content (each medium uses the same template; glyph fill color is the only per-medium difference):

- Glyph (top-left, 22px regular / 30px on `2×2`), colored per medium: games burgundy, music steel, poetry green.
- Title (Petrona, 1rem regular / 1.15rem on `2×1` / 1.4rem on `2×2`).
- Meta line (Inter, 0.7rem, `--color-ink-soft`): `<type> · <year>`. For games: `<game_kind> · <year>`. For music: `<format> · <year>`. For poetry: `<collection> · <year>` (omits when no collection).
- Pull quote (only on `2×2` featured tiles, italic, `--color-ink-soft`): pulled from `summary` frontmatter if present. When `summary` is absent or empty, the pull quote is omitted and the tile compresses vertically — no placeholder text.
- Tags (bottom, Inter 0.62rem, capsule chips, `--color-ink-soft`): up to 3, with the active filter tag highlighted (`.t.match` — inverted: `--color-ink` background, `--color-stone` text).
- Cross-ref annotation (when present): single line, Inter 0.62rem, `--color-burgundy`, e.g. `↔ poem · After the Bell`. Computed from frontmatter (`lyrics_poem`, `set_to_music`, `embed_url` is not a cross-ref, only inter-fixture refs count).

Empty-state: `<p class="works-empty">No works match the current filter.</p>` rendered after the grid; shown by JS when zero tiles pass.

### 3.4 Graph view (slide-in panel on desktop)

Click `⊞ Graph view` → constellation panel slides in from the right (320–480px wide, resizable handle on the left edge — same pattern as garden + research panels). The Bento behind stays visible; the panel has its own toolbar:

- Medium filter (4 chips: All / Games / Music / Poetry — same single-active dim as the strip, but operates only on graph nodes).
- `Reset view` button.
- `Reset positions` button.

Canvas: SVG, force-directed via the vendored d3-force / d3-zoom / d3-drag / d3-selection (already vendored under `assets/js/vendor/`). Zoom (0.3×–4× toward cursor), drag-pan on empty SVG, drag-to-reposition for any node with stay-put release. Position state persists per filter+viewport in localStorage under the existing `{nodes, view}` cache shape (same code path as garden + research).

**Nodes**: Each node is an inline `<svg viewBox="0 0 24 24"><use href="#g-game|g-music|g-poetry"/></svg>` referencing one of three shared `<symbol>` definitions emitted by a new `partials/works/glyph-sprite.html` at the top of the umbrella + standalone graph page. Node size: 28px regular, 40px for `featured: true` works. Wrapped in a 52×52 rounded badge with the same gradient as Bento tile badges (`linear-gradient(135deg, rgba(122,45,42,0.10), rgba(47,91,117,0.08))`).

**Edges**:

- **Solid** = tag-share — if two works share ≥1 tag, emit an edge with `weight = count_of_shared_tags`. Force-link distance shorter for higher weight.
- **Dashed** = explicit cross-medium ref — derived from `lyrics_poem` / `set_to_music` / etc. frontmatter cross-refs. Always emitted regardless of tag overlap.

**Legend** (bottom of panel): `— tag-share · · · cross-medium ref`.

### 3.5 Standalone `/works/graph/` (mobile fallback + deep link)

Mirrors `/garden/graph/` and `/research/graph/`:

- Breadcrumb (`Works › Constellation`).
- Summary line (`N works · M edges`).
- Full-width canvas (same JS, mounts on full-page element instead of panel).
- Toolbar + legend at the bottom.

At ≤720px the ⊞ button on the umbrella becomes a link to this page rather than a panel toggle.

## 4. Data contracts

### 4.1 Frontmatter additions (optional, all per-work)

| Field | Type | Default | Effect |
|---|---|---|---|
| `tile_size` | enum: `small`/`medium`/`large` | `medium` | Bento tile size. Highest priority. |
| `featured` | bool | `false` | If `tile_size` unset → tile becomes `large`. Also: graph node uses the 40px (featured) badge size. Spans 2 cols. |
| `hero` | bool | `false` | Spans 2 rows in Bento. Pairs with `featured: true` to make `2×2` tiles. |

All three fields are already validated as optional by `tools/check_works_fixtures.py` — the linter's optional-field allowlist needs to accept them per type. (Today only `essay` knows these fields.)

To exercise the Bento in dev, this slice will set `featured: true` on 1–2 fixtures across the three sub-sections (e.g., `example-playable-full-release` for games, `example-album-with-tracks` for music). No fixture text changes.

### 4.2 `data/filter-chips.yaml` — new `works` section

```yaml
works:
  primary_tags: [example, ambient, lyric]   # curated; aggregate across games + music + poetry
  primary_top_k: 10
```

`tools/check_filter_chips_config.py` must learn that the `works` key resolves its tag pool by aggregating tags from `content/works/games/`, `content/works/music/`, `content/works/poetry/` (drafts excluded). Today the linter has section-path overrides for the three sub-sections; this slice adds one more for the umbrella aggregation.

### 4.3 Filter-chips partial — small additive extension

`partials/filter-chips.html` currently treats `dimensions` as the source of truth. No template change needed — the **caller** (`layouts/works/list.html`) computes tag + medium dimensions from the aggregated pages and passes them in. No new partial parameter.

### 4.4 Graph data partial

New: `partials/works/graph-data.html` (run once via `partialCached`). Walks `(site.GetPage "/works/games").Pages`, music, poetry; emits:

```json
{
  "nodes": [
    {"slug": "forest-of-forking-memories", "medium": "game", "title": "...", "url": "...", "tags": ["memory","narrative"], "featured": true, "year": 2026},
    ...
  ],
  "edges": [
    {"source": "forest-of-forking-memories", "target": "after-the-bell-ep", "kind": "tag-share", "weight": 2, "shared": ["memory","loops"]},
    {"source": "after-the-bell-ep", "target": "after-the-bell", "kind": "cross-ref", "via": "set_to_music"}
  ]
}
```

Edge generation: tag-share edges emitted for every pair with ≥1 shared tag (weight = count of shared tags). Cross-ref edges always emitted regardless of tag overlap (deduped if the same pair also tag-shares — the dashed cross-ref edge wins; tag overlap recorded in its `shared` field for tooltip use later). No `mediumPaletteOrder` field — the three mediums are a fixed enum; palette mapping (`game→burgundy`, `music→steel`, `poetry→green`) is hardcoded in `works-graph.js`. If fixture growth pushes edge count past ~200 and render perf suffers, gate tag-share emission on a `min_shared` threshold; not in scope at 12 fixtures.

Wrapper: new `partials/works/graph-script.html` emits `<script type="application/json" id="works-graph-data">` via `safeJS`. Cache key for `partialCached`: the fixed string `"works-graph"` so the umbrella + standalone page share one cache entry (same trick as research).

### 4.5 Glyph sprite

New: `partials/works/glyph-sprite.html` emits a hidden `<svg width="0" height="0" aria-hidden="true">` containing three `<symbol>` definitions: `g-game`, `g-music`, `g-poetry`. Each symbol has `viewBox="0 0 24 24"` and a `<g>` of paths with `stroke="currentColor"`, `stroke-width="1.5"`, `stroke-linecap="round"`, `stroke-linejoin="round"`. Embedded in the umbrella layout once, and in `/works/graph/` once. Both Bento tiles and graph nodes reference symbols via `<svg viewBox="0 0 24 24"><use href="#g-<medium>"/></svg>`.

The three source SVGs also exist as standalone files in `assets/images/icons/glyph-{game,music,poetry}.svg` so the future homepage Studio strip can `<img src=...>` or inline-copy them. **Single visual source: the standalone SVG file. The sprite partial inlines the same `<g>` contents.** Manual sync — small enough (3 files, 24×24 viewBox) that drift risk is low. No automated build step.

## 5. Component map

| File | Status | Role |
|---|---|---|
| `assets/images/icons/glyph-game.svg` | NEW | Gamepad. Hand-authored, hybrid style (clean strokes + organic shape). `currentColor`. |
| `assets/images/icons/glyph-music.svg` | NEW | Eighth-note. Same art direction. |
| `assets/images/icons/glyph-poetry.svg` | NEW | Quill. Same art direction. |
| `layouts/works/list.html` | REWRITE | Renders header, glyph sprite, filter strip, Bento grid, graph panel scaffolding. |
| `layouts/works/graph.html` | NEW | Standalone `/works/graph/` page. |
| `partials/works/section-card.html` | DELETE | Replaced by tile + new umbrella layout. |
| `partials/works/tile.html` | NEW | One Bento tile (resolves `data-tile-size`/`data-span`, renders glyph + title + meta + tags + cross-ref annotation). |
| `partials/works/glyph-sprite.html` | NEW | Inlined `<symbol>` definitions for the three mediums. |
| `partials/works/graph-data.html` | NEW | Build-time `partialCached` data partial. |
| `partials/works/graph-script.html` | NEW | JSON `<script>` wrapper via `safeJS`. |
| `partials/works/graph-panel.html` | NEW | Side-panel scaffolding (`<aside id="works-graph-panel" class="graph-panel" hidden>`). |
| `assets/css/main.css` §33 | REPLACE umbrella block | Lines ~2188–2235 replaced with new Bento + filter-strip umbrella rules. §33's games block stays. |
| `assets/css/main.css` §36 | NEW | "Works graph" — palette per medium via `data-medium` attribute, dashed cross-ref edges, standalone-page chrome. Mirrors §31 research-graph. |
| `assets/js/works-graph.js` | NEW | Copy + trim of `research-graph.js`. Selector-guarded on `#works-graph-data`. ~107 KB minified. |
| `assets/js/entry-works-umbrella.js` | NEW | Imports `works.js` (existing — filter chips wiring) + `works-graph.js`. |
| `assets/js/entry-works.js` | UNCHANGED | Still loaded on per-item works pages. ~6 KB. |
| `layouts/partials/scripts.html` | EDIT | Add the 6th `js.Build` call for `entry-works-umbrella.js` with predicate `eq .RelPermalink "/works/"` or `eq .RelPermalink "/works/graph/"`. |
| `data/filter-chips.yaml` | EDIT | Add `works` section. |
| `tools/check_filter_chips_config.py` | EDIT | Aggregate `content/works/{games,music,poetry}/` for the `works` key. |
| `tools/check_works_fixtures.py` | EDIT | Accept `tile_size`, `featured`, `hero` as optional fields per type. |

## 6. JS bundle strategy

`works.<hash>.js` (~6 KB) currently loads on every `.Section == "works"` page (umbrella + 12 per-item). Inlining d3 into that bundle would push every per-item works page from ~6 KB to ~110 KB — wasteful, since per-item pages don't use the graph.

This slice splits the bundle into two predicates that **never overlap**:

- `entry-works.js` → `works.<hash>.js` (~6 KB) — predicate narrowed from `.Section == "works"` to `.Section == "works" AND NOT (.RelPermalink in {"/works/", "/works/graph/"})`. Loads on per-item works pages only (the 12 fixtures × 3 sub-sections + the 3 sub-section indexes). Selector guards inside `works.js` already no-op on irrelevant pages, but the predicate prevents the bundle from shipping where the umbrella bundle is also loading.
- `entry-works-umbrella.js` → `works-umbrella.<hash>.js` (~110 KB) — page-narrow predicate: `.RelPermalink in {"/works/", "/works/graph/"}`. Imports `works.js` (filter chips) + `works-graph.js`. Loads on the umbrella + standalone graph page only.

This mirrors the research bundle precedent (research bundle loads on `/research/` + `/research/graph/` only; theme + question pages stay on core). Filter-chips logic ships once per page; no duplication.

## 7. Reuse map (what's NOT new)

| Capability | Source |
|---|---|
| Filter-chip rendering (tag two-tier, medium single-active, suppression) | `partials/filter-chips.html` — unchanged |
| Filter-chip JS (active state, AND composition, search disclosure, keyboard nav) | `assets/js/filter-chips.js` — unchanged |
| Variable-tile Bento CSS pattern (`data-span` reading) | Lifted from `assets/css/main.css` §11 (essay grid) — adapt selectors only |
| Graph CSS scaffolding (toggle, panel chrome, toolbar, canvas, legend, resize handle) | `assets/css/main.css` §27 — already shared |
| Graph JS architecture (force sim, zoom/pan/drag, position cache, reduced-motion freeze) | `assets/js/research-graph.js` — copy + trim |
| Standalone graph page pattern | `layouts/research/graph.html` — mirror |
| Cross-medium-ref data | Already in fixtures, validated by `check_works_links.py` |

## 8. Accessibility

- Glyphs in tiles: `<svg role="img" aria-label="game">` (or music / poetry). Decorative on graph nodes inside the panel (`aria-hidden="true"`) since the title is the accessible label.
- Filter chips: existing partial already handles `aria-pressed`, `aria-controls`, keyboard nav. No change.
- Graph toggle button: `aria-expanded="<bool>"`, `aria-controls="works-graph-panel"`. Existing pattern.
- Color is never the only cue: medium is also communicated by glyph shape (not just fill color), satisfying CB-safe palette + spec §1.
- Reduced motion: same as research/garden — sim runs 300 ticks then freezes; no slide-in animation on the panel (instant show).
- WCAG: glyph fills are burgundy / steel / green on stone — all already AA-validated by `tools/check-contrast.py`. No new contrast pairings.

## 9. Tradeoffs considered

- **Bento vs editorial rows vs quiet columns vs merged stream**: the author picked the Bento+graph mashup over four alternatives (Three cards, Editorial rows, Quiet columns, Merged stream, Constellation-only, Bento-only, Tag-facet, Studio-diary). The combination preserves "buckets foreground identity" (medium chips up top, glyph on every tile) AND "freeform exploration" (tag cloud, sort, graph view) without compromising either.
- **Graph panel vs full-page swap**: panel mirrors garden + research. Standalone page for mobile + deep-linking. Established pattern; no novelty cost.
- **Tag dim curated vs auto-top-K**: curated default in `data/filter-chips.yaml` so the author controls primary-strip composition. Auto-top-K is fallback (the existing partial behavior).
- **Sort default**: "featured" rather than "chronological" because the Bento's variable-tile sizes ARE the visual hierarchy — chronological default would shuffle featured pieces around the grid, fighting the layout.
- **Edges by tag-share vs essay-style explicit links**: tag-share gives a denser, more interesting graph from fixture data the author already curates. Cross-medium refs add a sparse but high-signal layer on top.
- **Single sprite vs three inline copies per tile**: sprite emitted once per page, `<use>` referenced by every tile and graph node. Per-page footprint stays small; SVG paths defined once.

## 10. Risks

- **Bundle size on the umbrella jumps from ~6 KB to ~110 KB on first visit.** Acceptable — the umbrella is the landing page, performance budget is OK for one heavy page. Per-item pages are unaffected.
- **Tag aggregation across sub-sections is new.** The filter-chips partial accepts pre-computed `dimensions`, so the caller does the aggregation — no partial changes. The linter needs to learn the aggregation. Small change, additive.
- **Drift between standalone SVG files and sprite partial.** Three files, 24×24 each, hand-authored. Sync manually; the risk is small. If it grows, add a build step or a linter; not in scope here.
- **Featured tiles need fixture frontmatter.** Adding `featured: true` to 1–2 fixtures per medium changes fixture frontmatter — but `featured` is an optional field, not an authored prose change. Fixture content stays filler-only per spec §1.
- **Empty graph at low fixture count.** With 12 fixtures and limited tag overlap, the graph may look sparse at first. Acceptable — it grows organically as real content lands via the elisp pipeline. The infrastructure is the deliverable, not the density.

## 11. Acceptance

The slice ships when:

1. `/works/` renders the new Bento grid with the three glyphs visibly anchoring each tile in the correct color.
2. Tag-cloud filter narrows the grid (multi-select tag dim, single-active medium dim, AND across dimensions).
3. ⊞ Graph view toggles a panel containing the d3-force constellation; nodes use the medium glyphs; solid edges (tag-share) and dashed edges (cross-medium refs) both render.
4. `/works/graph/` renders the standalone page with the same data.
5. At ≤720px the ⊞ button navigates to `/works/graph/` instead of toggling a panel.
6. All 19 existing CI gates pass; `check_works_fixtures.py` accepts the new optional fields; `check_filter_chips_config.py` validates the new `works` key.
7. `python3 -m unittest tools/test_check_works_fixtures.py -v` and `python3 -m unittest tools/test_check_filter_chips_config.py -v` pass with new unit tests added for the new behavior.
8. WCAG contrast verifier passes with no changes (palette unchanged).
9. No new CSS tokens, no new fonts, no npm.

## 12. Out-of-band notes

- This slice is "Slice 0" of the next Phase-6 work — labelled as polish but it's the first time the umbrella becomes the creative-self landing rather than a directory listing. The author may want to revisit and add a homepage v3 Studio strip that links to `/works/` (Phase 7) once this lands; the three glyphs ship here precisely so that strip is unblocked.
- Cross-ref to memory: `project_works_umbrella_polish_pending.md`. Update or remove that memory entry when this slice merges.
- After this slice, the CLAUDE.md "Project status" section gains a note: "Works umbrella polished — Bento grid + constellation panel + 3 hand-authored type-glyphs."
