# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Personal website for Abdelrahman Madkour, built as a Hugo static site with hand-rolled CSS and deployed to GitHub Pages. Long-form essays are the centerpiece, supported by a Zettelkasten-style knowledge garden, research surface, and creative output (games / music / poetry). All content authored in org-mode + org-roam, exported via ox-hugo.

## Commands

- `hugo server --buildDrafts` — dev server with drafts visible.
- `hugo --minify` — production build to `public/`. **Do not run with a dev server alive**; it poisons the dev-server CSS via a MIME mismatch.
- `python3 tools/check-contrast.py` — WCAG 2.1 contrast verifier (CI gate).
- Nine linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, works fixtures, works links.

No npm. Python tooling is stdlib-only. Hugo **extended** (≥ 0.148.0) is required — `.github/workflows/hugo.yaml` pins `HUGO_VERSION=0.148.0`.

## Architecture

### CSS pipeline — hand-rolled, processed by Hugo

`assets/css/main.css` is a single hand-rolled stylesheet, organized into numbered sections §1–§36 (see the file's top-of-file index for the list). Consumed by `layouts/partials/head.html` via `resources.Get` + (production) `minify | fingerprint` with SRI integrity.

- **Tokens** are CSS custom properties on `:root` (light) and `:root[data-theme="dark"]` (dark). System dark via `@media (prefers-color-scheme: dark) :root:not([data-theme])`. The `[data-theme="dark"]` block and the media-query block carry **duplicate values** — both must be updated together when the palette changes.
- **WCAG contrast**: `tools/check-contrast.py` parses the `:root` blocks and verifies four pairings (ink/stone AAA, ink-soft/stone AA, burgundy/stone AA, steel/stone AA) in both modes. Failure blocks deploy. Tokens `--color-green` (evergreen / finished pill) and `--color-warn` (queued pill) ride along but aren't checked.
- **No Tailwind, no PostCSS, no Node.** Class names are semantic.

### JS pipeline — multi-entry bundling

`layouts/partials/scripts.html` runs Hugo's `js.Build` (esbuild) five times — minified + fingerprinted, classic-script with SRI:

| Entry | Output | Loaded on | Notes |
|---|---|---|---|
| `js/index.js` | `core.<hash>.js` (~1.4 KB) | every page | `toggle-theme.js` + `nav.js` |
| `js/entry-essay.js` | `essay.<hash>.js` (~4.8 KB) | `.Section == "essays"` | imports `filter-chips.js` + `citation-card.js` |
| `js/entry-garden.js` | `garden.<hash>.js` (~117 KB) | `.Section == "garden"` | `garden.js` + `garden-stack.js` + `garden-graph.js` + ~95 KB vendored d3 modules |
| `js/entry-research.js` | `research.<hash>.js` (~107 KB) | `/research/` and `/research/graph/` only | `research-graph.js` (copy + trim of `garden-graph.js`); page-narrow predicate over section-wide |
| `js/entry-works.js` | `works.<hash>.js` (~4 KB) | `.Section == "works"` AND NOT `/works/`-or-`/works/graph/` | imports `filter-chips.js`; per-item pages only |
| `js/entry-works-umbrella.js` | `works-umbrella.<hash>.js` (~112 KB) | `/works/` and `/works/graph/` only | `works.js` + `works-graph.js` (copy + trim of `research-graph.js`) + vendored d3 modules |

**Why multi-entry, not `splitting: true`?** esbuild requires `outdir` for code splitting, but Hugo's `js.Build` is `outfile`-only. `splitting: true` on a single entry silently inlines dynamic imports rather than emitting chunks. Confirmed with a minimal repro. `filter-chips.js` is duplicated into essay/garden/works bundles (~8 KB).

d3-force / d3-zoom / d3-drag / d3-selection are **vendored** under `assets/js/vendor/` (no npm). `garden-graph.js` dynamically imports all four — they inline into the garden bundle. `research-graph.js` is an independent copy + trim (drops stack-coordination + N-hop local mode); the two graphs share CSS scaffolding (§27) but not JS code. Each page module guards on its own selector and bails on irrelevant pages.

### Theme toggle

Three-state cycle: **system → light → dark → system**.

- Storage key: `theme-pref` in `localStorage` (absent = system mode).
- CSS responds to a `data-theme` attribute on `<html>`.
- An inline `<script>` at the top of `<head>` reads `theme-pref` synchronously during HTML parse and applies `data-theme` before any rendering — prevents FOUC. Storage access is wrapped in `try/catch` so restricted contexts (private browsing strict, sandboxed iframes) degrade gracefully.
- Bundled `toggle-theme.js` handles the click cycle, button label updates, and idempotent re-apply.

### Content & layouts

- **Content sections** in `content/`: `_index.html`, `about/`, `blog/` (legacy), `essays/`, `garden/`, `research/`, `works/`.
- **Layouts** under `layouts/`: base templates in `_default/`; per-section `{list,single}.html` plus `rss.xml` for essays + garden and standalone `graph.html` pages for garden + research + works. Works splits into `works/`, `works-games/`, `works-music/`, `works-poetry/`. Research splits into `research/`, `research-theme/`, `research-question/` with type discrimination via `cascade: { type: research-theme|research-question }` on `content/research/{themes,questions}/_index.md` (bare section URLs hidden via `build: render: never`). `baseof.html` is a thin semantic wrapper; per-section layouts override `{{ block "main" }}`.
- **Partials** under `layouts/partials/`: site chrome (`head`, `header`, `footer`, `scripts`); essays (`essay-card{,-featured}`, `essay-meta`, `essay-toc`, `essay-references`, `essay-series-nav`); shared `filter-chips.html`; `garden/` subfolder (`note-header`, `stage-glyph`, `note-tile`, `topic-section`, `relative-date`, `path-log`, `links-section`, `graph-{data,script,panel}`); `research/` subfolder (`status-pill`, `output-item`, `theme-card`, `backlinks-data`, `graph-{data,script,panel}`); `works/` subfolder (`tile`, `glyph-sprite`, `game-card`, `music-row`, `poem-row`, `status-pill`, `audio-pill`, `audio-link`, `connections`, `graph-{data,data-inner,script,panel}`).
- **Shortcodes** under `layouts/shortcodes/`: `cite` (looks up `site.Data.citations.citations[key]`, errors if missing), `sidenote` (auto-numbered marker + aside via page scratch), `figure` (semantic, supports `class="wide"`), `spoiler` (`<details>`-based, no JS). Deferred-feature stubs: `math`, `video-sync`, `widget`, `lyrics` — each emits a `data-pending` container so fixtures exercise the shape.
- **Top nav** (locked): Essays / Garden / Research / Works / About. Active item gets `aria-current="page"` via `hasPrefix` match.

### Frontmatter contracts

**Essays** (`content/essays/<slug>/index.md`) — enforced by `tools/check_fixtures.py`. Required: `title, date, lastmod, draft, summary, tags, series, series_order, toc, has_sidenotes, has_citations, has_footnotes, has_math, has_widgets, has_video_sync`. Optional: `tile_size, featured, hero`. Mirrors spec §10 (ox-hugo output shape).

**Garden** (`content/garden/<slug>/index.md`) — enforced by `tools/check_garden_fixtures.py`. Always required: `title, draft, last_modified, growth_stage`. Flavor derived from `media_type`:
- **Concept** (no `media_type`) — only the always-required + optional `tags, summary, topic_map, roam_refs, year, weight`.
- **Media** (`media_type ∈ {book, album, track, game, film, series}`) — also `status, creator`; optional `started, finished, spoiler_level, original_url`.
- **Reference** (`media_type ∈ {paper, video, article, talk}`) — also `creator`; optional `original_url`. `status, started, finished, spoiler_level` are forbidden.

`topic_map: [slug-1, ...]` is an optional facet on any concept note: declares an ordered slug list; the note renders a curated tile grid below its body, and `/garden/` surfaces one section per topic-map note.

**`last_modified` is parsed by Hugo as a string** (YAML 1.2 doesn't auto-coerce to `time.Time` for custom keys); template helpers coerce via `time.AsTime` when needed.

**Research** (`content/research/{themes,questions}/<slug>/index.md`) — `tools/check_research_fixtures.py` enforces per-type contract (incl. `validate_unique_theme_weights()` to keep the graph palette deterministic); `tools/check_research_links.py` resolves `garden_topic_ref` / `theme` / `parent_question` / `supporting_notes` / `related_essays`.

**Works** — per-type contracts in `tools/check_works_fixtures.py`. **Games' "kind" field is named `game_kind`** (Hugo reserves both `type` and `kind` as built-in page attributes — avoid these names on per-fixture frontmatter). `tools/check_works_links.py` enforces round-trip `lyrics_poem ↔ set_to_music` symmetry between music and poetry.

**Citations**: `data/citations.yaml` is the canonical citation store (fixture-shaped — ox-hugo will produce it later). `tools/check_citations.py` validates shape and resolves `notes_ref` against the garden tree.

### Bento variable-tile grid (essays index + homepage strip)

Cards in `layouts/partials/essay-card.html` carry `data-tile-size` and `data-span` attributes resolved per priority:
- Tile size: explicit `tile_size` > `featured: true` (large) > in-series (medium) > medium (default).
- Span: `featured: true` → 2 cols; `hero` declared → 2 rows. Combined: `2x1 / 1x2 / 2x2 / 1x1`.

CSS reads `data-span` and applies `grid-column / grid-row: span N`.

### Filter chips

`/essays/`, `/garden/`, and all three `/works/` sub-indexes render filter chip strips via the shared `partials/filter-chips.html`. Dimensions:
- Essays: tag / series / year. Garden: tag / flavor / stage. Games: status / kind / tag. Music: format / tag. Poetry: collection / tag.
- **Suppression**: dimensions with <2 distinct values don't render.
- **Tag dim is two-tier**: primary chips inline; secondary chips inside a native `<details>` disclosure with a search input. Primary set from `data/filter-chips.yaml` `<section>.primary_tags` (manual, ordered) or top-K by note count (default K=10, override per section via `primary_top_k`). `tools/check_filter_chips_config.py` validates curated tags against the live taxonomy and includes section-path overrides for `content/works/<sub>/`.
- **Read the data file via `index site.Data "filter-chips"`** — Hugo exposes hyphenated filenames literally, not dot syntax.

**Active-state model**: per-dimension AND across dimensions. Multi-select within tag dim only (mutually-exclusive dims stay single-active). Clicking an active tag chip deselects it; "All" clears the tag selection. Disclosure summary surfaces active secondary tags when collapsed.

**Optional `labels` map per dim** (`partials/filter-chips.html`): when present, the chip displays `labels[value]` while `data-key` stays the raw value. Used on the works umbrella to render display labels "Games / Music / Poetry" while keeping singular keys ("game" / "music" / "poetry") that match tile `data-medium`.

Search inside the disclosure: case-insensitive substring on `data-key`, live-filters chips. Keyboard: Arrow Down → first visible chip, Arrow Left/Right between visible chips (no wraparound), Arrow Up returns to input, Enter toggles, Esc clears.

Shared module: `assets/js/filter-chips.js`. Each page entry calls `setupFilterChips({ containerSelector, cardSelector, sectionSelector?, emptyStateSelector? })`. The `data-tags` attribute on tile elements is split on **whitespace** (`/\s+/`) — every tile template must emit space-delimited tags via `delimit $tags " "`. Comma silently zeros all chip matches.

**`[hidden]` cascade gotcha**: any element with author-side `display: <X>` overrides the UA `[hidden] { display: none }` rule. When JS toggles the `hidden` attribute on a chip/tile, add an explicit `.<class>[hidden] { display: none; }` rule (already in place for `.filter-chip`, `.garden-tile`, `.garden-topic`).

**No in-strip no-JS fallback.** With JS off, the disclosure still opens (native `<details>`) but chips and search are inert. Taxonomy pages at `/tags/<slug>/` and `/series/<slug>/` are the fallback. Taxonomies declared in `hugo.yaml` (`tag: tags`, `series: series`).

### Build-time graph data

`partials/garden/graph-data.html` (run once via `partialCached`) walks all garden pages and extracts internal `/garden/<slug>/` references from `.RawContent` via `findRE`. Edges classified by topic-map membership: same-topic (solid) vs cross-topic (dashed). Output JSON `{nodes, edges, topics}` matches what ox-hugo's `data/notes.json` will produce — `garden-graph.js` won't change when Phase 3 lands. `tools/check_garden_links.py` validates every internal reference resolves to a non-draft fixture.

`partials/research/graph-data.html` mirrors this for research themes + questions: parent-child edges from `theme` + `parent_question` (solid), cross-theme edges from shared `supporting_notes` (dashed). Shared cache key `"research-graph"` so multi-page callers share one cache entry.

`partials/works/graph-data.html` does the same for works umbrella + standalone graph: nodes are all 12 fixtures (games + music + poetry merged); tag-share edges (solid) for any pair sharing ≥1 tag; cross-medium edges (dashed) for `lyrics_poem` / `set_to_music` pairs. Pattern: outer wrapper returns a Hugo dict via `partialCached`; the `graph-script.html` caller does `jsonify | safeJS` at the embed point. **Don't `jsonify` inside the data partial** — the production minifier chokes on HTML-escaped quotes inside `<script type="application/json">`.

### Typography

Three Google Fonts in a single `<link>`: **Petrona** (body, italic + upright at 400/600/700), **Inter** (UI labels), **JetBrains Mono** (code). Display = swap. Token names: `--font-body`, `--font-ui`, `--font-mono`.

### Deployment

`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `master`. CI runs all Python checks (contrast + 9 linter pairs = 19 verification steps) before the Hugo build; any failure blocks deploy.

## Reference docs

- **Design spec (canonical)**: `docs/superpowers/specs/2026-05-03-personal-site-design.md`. §14 is the master phase list.
- Per-slice plans and specs under `docs/superpowers/{plans,specs}/`, dated by slice.
- **Phase 6 umbrella polish spec**: `docs/superpowers/specs/2026-05-12-works-umbrella-polish-design.md`. Phase 6 Slice 0.

## Project status (as of 2026-05-12)

**Shipped — Phases 0–6 plus targeted polish:**

- **Site chrome + visual identity** (Phase 0+1): tokens, typography, three-state theme toggle, header/footer, contrast-gated CSS.
- **Essays** (Phase 2): variable-tile Bento index, three-zone post layout (TOC + body + sidenote rail), citation hover-card runtime, figures, footnotes, hero illustrations, series nav, per-section RSS, homepage essays strip.
- **Garden** (Phase 2 + 4): concept/media/reference single-note template, `topic_map` facet, multi-dim AND filter chips with two-tier tag disclosure, stacked-column retrieval (`?stack=` URL sync, sticky path log, consent banner), force-directed graph with zoom/pan/drag-to-reposition, side panel on desktop + standalone `/garden/graph/` on mobile, per-section RSS.
- **Research** (Phase 5): `/research/` index, theme + question hubs, status pills, output icons, backlinks, force-directed research graph (slide-in panel + standalone `/research/graph/`).
- **Works** (Phase 6): polished umbrella (Bento variable-tile grid + tag-cloud filter + ⊞ Graph view toggle with d3-force constellation; three hand-authored medium glyphs: gamepad/eighth-note/quill); games / music / poetry indexes + per-item pages. Runtime-heavy pieces deferred — see table below.
- **About** (Phase 2 bio half): Hero / Bio / Where / Connect / Colophon. Now widget deferred (Phase 3-blocked).

**Not started, in phase order:**

- **About Now widget** — Phase 3-blocked (needs elisp pipeline).
- **Phase 3 — org-mode pipeline**: elisp helpers + ox-hugo that wire real content into the fixture-shaped data files. All site fixtures exist to round-trip when this lands.
- **Phase 7 — Library** (reading / listening / playing): data-driven view filtered from media-flavor garden notes + `data/*.yaml`.
- **Phase 7 — Homepage v3**: Currently strip + Studio strip + Garden+Studio columns. The current homepage has only the role line + essays strip.
- **Phase 8 — Pagefind search + Lighthouse CI + final QA.**

To pick up a slice: read this file + parent spec §14, run `superpowers:brainstorming` then `superpowers:writing-plans`. Confirm with the user whether the slice depends on the elisp pipeline (most do) or can build on placeholder data.

**Fixture content is always obvious filler** (lorem ipsum / "Example N") — never authored prose, even for layout testing. Real content lands via the elisp pipeline.

### Deferred features (fixtures exercise the shape; stubs carry `data-pending` for future swap-in)

| Capability | Target | Fixture seed |
|---|---|---|
| KaTeX math rendering | Gated on author need | essay fixture #2 (`has_math`) |
| Scroll-synced video runtime | Gated on author need | essay fixture #4 (`has_video_sync`) |
| Per-page interactive widgets + per-page JS bundle convention | Design when first real widget exists | essay fixture #5 (`has_widgets`) |
| Game iframe embed (itch / Bitsy / WebGL) | Future works runtime slice | game fixture #1 `embed_url`; `works-embed-stub` anchor |
| Music platform iframe (Bandcamp / SoundCloud / YouTube) | Future works runtime slice | music fixtures #1 / #2 / #4; `works-audio-link` text link only |
| Custom audio player | Future works runtime slice | `works-player-stub` block |
| Synced-lyrics runtime + two-column lyrics layout | Future works runtime slice | music fixture #2 ↔ poem fixture #1; `synced-lyrics-stub`, `lyrics` shortcode is a no-op |
| Audio-pill pulse animation | Future works runtime slice | poem-page audio pill renders without animation |
| Gif-vs-hero toggle on game cards | When real gif assets land | n/a |
| Figure lightbox | Polish phase | n/a |
| Code highlighting palette swap from Dracula | Post-Phase-2 polish | n/a |
| Print stylesheet | Phase 8 polish | n/a |
| Library cross-linking | Phase 7 | media-flavor garden notes are the canonical source |
| About Now widget | Phase 3 (org-mode) | About template has a placeholder slot |

## Hard constraints (from spec §1)

- **No AI-generated text** anywhere on the site. AI is permitted only for site/app code and code for interactive explorables.
- **No AI-generated illustrations.** SVG icons are hand-authored under `assets/images/icons/`. Hero/figure SVGs in essay page bundles are hand-authored placeholders.
- **Privacy by org-export boundary**: content not exported never reaches the site.
- **Accessibility**: WCAG 2.1 AAA for body text, AA for accents; CB-safe palette; never color-only meaning.
- **Fixture content is obviously dummy** (lorem ipsum / "Example N") — never authored prose. Real content lands via the elisp pipeline.
