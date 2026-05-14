# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Personal website for Abdelrahman Madkour, built as a Hugo static site with hand-rolled CSS and deployed to GitHub Pages. Long-form essays are the centerpiece, supported by a Zettelkasten-style knowledge garden, research surface, and creative output (games / music / poetry). All content authored in org-mode + org-roam, exported via ox-hugo.

## Commands

- `hugo server --buildDrafts` — dev server with drafts visible.
- `hugo --minify` — production build to `public/`. **Do not run with a dev server alive**; it poisons the dev-server CSS via a MIME mismatch.
- `python3 tools/check-contrast.py` — WCAG 2.1 contrast verifier (CI gate).
- Seventeen linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, works fixtures, works links, library fixtures, library links, library covers, RSS XSL, garden history, pagefind metadata, cite metadata, page weights. `tools/check_smoke.py` is a sibling-less linter (no paired test file — spec §3.1: logic is too thin to warrant pairing).

No npm. Python tooling is stdlib-only. Hugo **extended** (≥ 0.148.0) is required — `.github/workflows/hugo.yaml` pins `HUGO_VERSION=0.148.0`.

## Architecture

### CSS pipeline — hand-rolled, processed by Hugo

`assets/css/main.css` is a single hand-rolled stylesheet, organized into numbered sections §1–§43 (see the file's top-of-file index for the list; §32–§36 are reserved for past works-section additions that landed without numbered headers; §38–§40 cover the homepage hero, Currently widget, and homepage strips; §41 covers the cross-template page sidebar; §42 covers the search modal; §43 covers citation export). Consumed by `layouts/partials/head.html` via `resources.Get` + (production) `minify | fingerprint` with SRI integrity.

- **Tokens** are CSS custom properties on `:root` (light) and `:root[data-theme="dark"]` (dark). System dark via `@media (prefers-color-scheme: dark) :root:not([data-theme])`. The `[data-theme="dark"]` block and the media-query block carry **duplicate values** — both must be updated together when the palette changes.
- **WCAG contrast**: `tools/check-contrast.py` parses the `:root` blocks and verifies four pairings (ink/stone AAA, ink-soft/stone AA, burgundy/stone AA, steel/stone AA) in both modes. Failure blocks deploy. Tokens `--color-green` (evergreen / finished pill), `--color-warn` (queued pill), and `--color-paper` (floating panel surface — search modal; light `#fdfcf8`, dark `#2a2a2a`; semantically distinct from `--color-tile` which is the grid-item surface) ride along but aren't checked.
- **No Tailwind, no PostCSS, no Node.** Class names are semantic.

### JS pipeline — multi-entry bundling

`layouts/partials/scripts.html` runs Hugo's `js.Build` (esbuild) nine times — minified + fingerprinted, classic-script with SRI:

| Entry | Output | Loaded on | Notes |
|---|---|---|---|
| `js/index.js` | `core.<hash>.js` (~1.4 KB) | every page | `toggle-theme.js` + `nav.js` |
| `js/entry-essay.js` | `essay.<hash>.js` (~4.8 KB) | `.Section == "essays"` | imports `filter-chips.js` + `citation-card.js` |
| `js/entry-garden.js` | `garden.<hash>.js` (~117 KB) | `.Section == "garden"` | `garden.js` + `garden-stack.js` + `garden-graph.js` + ~95 KB vendored d3 modules |
| `js/entry-research.js` | `research.<hash>.js` (~107 KB) | `/research/` and `/research/graph/` only | `research-graph.js` (copy + trim of `garden-graph.js`); page-narrow predicate over section-wide |
| `js/entry-works.js` | `works.<hash>.js` (~4 KB) | `.Section == "works"` AND NOT `/works/`-or-`/works/graph/` | imports `filter-chips.js`; per-item pages only |
| `js/entry-works-umbrella.js` | `works-umbrella.<hash>.js` (~112 KB) | `/works/` and `/works/graph/` only | `works.js` + `works-graph.js` (copy + trim of `research-graph.js`) + vendored d3 modules |
| `js/entry-library.js` | `library.<hash>.js` (~5 KB) | `.Section == "library"` AND NOT `/library/` | imports `filter-chips.js`; per-leaf pages only (no graph) |
| `js/entry-search.js` | `search.<hash>.js` (~4 KB) | every page | search modal open/close logic; lazy-loads `/pagefind/pagefind.js` on first open |
| `js/entry-cite.js` | `cite.<hash>.js` (~2.5 KB) | `.Section in {essays, garden, research, works}` AND `.Kind == "page"` | `cite.js` — citation modal runtime (parse #cite-data blob, open `<dialog>`, tab/copy/download, Half B inline copy) |

**Why multi-entry, not `splitting: true`?** esbuild requires `outdir` for code splitting, but Hugo's `js.Build` is `outfile`-only. `splitting: true` on a single entry silently inlines dynamic imports rather than emitting chunks. Confirmed with a minimal repro. `filter-chips.js` is duplicated into essay/garden/works bundles (~8 KB).

d3-force / d3-zoom / d3-drag / d3-selection are **vendored** under `assets/js/vendor/` (no npm). `garden-graph.js` dynamically imports all four — they inline into the garden bundle. `research-graph.js` is an independent copy + trim (drops stack-coordination + N-hop local mode); the two graphs share CSS scaffolding (§27) but not JS code. Each page module guards on its own selector and bails on irrelevant pages.

### Theme toggle

Three-state cycle: **system → light → dark → system**.

- Storage key: `theme-pref` in `localStorage` (absent = system mode).
- CSS responds to a `data-theme` attribute on `<html>`.
- An inline `<script>` at the top of `<head>` reads `theme-pref` synchronously during HTML parse and applies `data-theme` before any rendering — prevents FOUC. Storage access is wrapped in `try/catch` so restricted contexts (private browsing strict, sandboxed iframes) degrade gracefully.
- Bundled `toggle-theme.js` handles the click cycle, button label updates, and idempotent re-apply.

### Search modal

`layouts/partials/search-modal.html` is included once from `baseof.html`. It renders a `<dialog>` element that opens via the header magnifier button or the `/` key. On first open, `entry-search.js` lazy-loads `/pagefind/pagefind.js` from the CI-built Pagefind index (never bundled; always served from `public/pagefind/`). Section filter chips (All / Essays / Garden / Research / Works / Library) map to `data-pagefind-filter="section:<name>"` values emitted by per-layout templates.

**Pagefind 1.x gotchas** (non-obvious from the code; essential for maintaining or extending search):

- `data-pagefind-meta` is **one key per element**. Multiple meta keys require multiple hidden `<span>` elements — comma-separated multi-key syntax on one element is not supported in Pagefind 1.x. All per-layout meta emissions follow this pattern.
- `data-pagefind-filter` is **separate from** `data-pagefind-meta`. Filter chips need their own explicit `data-pagefind-filter="section:<name>"` element in addition to the meta span.
- Calling `pagefindInstance.search(query, { filters: {} })` with an **empty filters object filters out everything** — zero results. When no filter is active, omit the second argument entirely (or don't pass a `filters` key).
- `data.title` is **not at the top level** of a Pagefind result data object; it lives at `data.meta.title`.

**Per-layout meta keys emitted:**

| Layout family | `section` | Additional keys |
|---|---|---|
| Essays | `essays` | `date` |
| Garden | `garden` | `growth_stage`, `flavor` (concept\|media\|reference, derived from `media_type`) |
| Research theme | `research` | `subtype:theme`, `status` |
| Research question | `research` | `subtype:question`, `status` |
| Works (game/music/poem) | `works` | `medium` |
| Library leaves | `library` | `medium`, `status` (leaf name: reading\|listening\|playing\|watching) |
| About / Home / Blog (legacy) | section name only | — |

**Indexing controls**: `<main data-pagefind-body>` in `baseof.html` scopes the indexed body. `data-pagefind-ignore` on `.spoiler-body` (in `spoiler` shortcode) excludes spoiler content from the index.

### Content & layouts

- **Content sections** in `content/`: `_index.html`, `about/`, `blog/` (legacy), `essays/`, `garden/`, `research/`, `works/`.
- **Layouts** under `layouts/`: base templates in `_default/`; per-section `{list,single}.html` plus `rss.xml` for essays + garden and standalone `graph.html` pages for garden + research + works. Works splits into `works/`, `works-games/`, `works-music/`, `works-poetry/`. Research splits into `research/`, `research-theme/`, `research-question/` with type discrimination via `cascade: { type: research-theme|research-question }` on `content/research/{themes,questions}/_index.md` (bare section URLs hidden via `build: render: never`). `baseof.html` is a thin semantic wrapper; per-section layouts override `{{ block "main" }}`.
- **Partials** under `layouts/partials/`: site chrome (`head`, `header`, `footer`, `scripts`); essays (`essay-card{,-featured}`, `essay-meta`, `essay-toc`, `essay-references`, `essay-series-nav`); shared `filter-chips.html`, `page-sidebar.html` (cross-template rotated-labels rail + mobile dots strip), `search-modal.html` (included once in `baseof.html`); `home/` subfolder (`hero`, `currently`, `research-strip`, `garden-strip`, `studio-strip` — homepage v3 sections); `garden/` subfolder (`note-header`, `stage-glyph`, `note-tile`, `topic-section`, `relative-date`, `path-log`, `links-section`, `graph-{data,script,panel}`); `research/` subfolder (`status-pill`, `output-item`, `theme-card`, `backlinks-data`, `graph-{data,script,panel}`); `works/` subfolder (`tile`, `glyph-sprite`, `game-card`, `music-row`, `poem-row`, `status-pill`, `audio-pill`, `audio-link`, `connections`, `graph-{data,data-inner,script,panel}`).
- **Shortcodes** under `layouts/shortcodes/`: `cite` (looks up `site.Data.citations.citations[key]`, errors if missing), `sidenote` (auto-numbered marker + aside via page scratch), `figure` (semantic, supports `class="wide"`), `spoiler` (`<details>`-based, no JS). Deferred-feature stubs: `math`, `video-sync`, `widget`, `lyrics` — each emits a `data-pending` container so fixtures exercise the shape.
- **Top nav** (locked): Essays / Garden / Research / Works / Library / About. Active item gets `aria-current="page"` via `hasPrefix` match.

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

`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `master`. CI step order: pre-build linters (contrast + 14 linter pairs = 29 steps) → `hugo --minify` → pagefind metadata linter unit tests → verify pagefind metadata on built pages → cite metadata linter unit tests → verify cite metadata on built pages → install Pagefind 1.5.2 binary → build Pagefind index into `public/pagefind/` → smoke test → page-weight linter + unit tests → Lighthouse CI desktop (2 steps: `lighthouserc.json`) → Lighthouse CI mobile (`lighthouserc.mobile.json`) → upload artifact → deploy. Total: 46 named steps. Any failure blocks deploy. `public/pagefind/` is gitignored and CI-regenerated each run. Two separate LHCI config files (`lighthouserc.json` for desktop, `lighthouserc.mobile.json` for mobile) — simpler than an env-override approach.

## Reference docs

- **Design spec (canonical)**: `docs/superpowers/specs/2026-05-03-personal-site-design.md`. §14 is the master phase list.
- Per-slice plans and specs under `docs/superpowers/{plans,specs}/`, dated by slice.
- **Phase 6 umbrella polish spec**: `docs/superpowers/specs/2026-05-12-works-umbrella-polish-design.md`. Phase 6 Slice 0.
- **Library spec**: `docs/superpowers/specs/2026-05-12-library-section-design.md`. Phase 7 first slice.
- **Library cover-fetch spec**: `docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md`. Phase 7 Slice 1 (infra shipped; live IGDB + TMDB paths deferred to a future slice).
- **Homepage v3 spec**: `docs/superpowers/specs/2026-05-13-homepage-v3-design.md`. Phase 7 Slice 2 (closes Phase 7).
- **Page sidebar spec**: `docs/superpowers/specs/2026-05-13-page-sidebar-design.md`. Phase 7 polish slice (rotated-labels rail across 5 layout families).
- **Phase 8 spec**: `docs/superpowers/specs/2026-05-13-phase-8-design.md`. Pagefind search runtime (Slice 1 shipped), Lighthouse CI, final QA.
- **Citation export spec**: `docs/superpowers/specs/2026-05-13-citation-export-design.md` + plan `docs/superpowers/plans/2026-05-13-citation-export.md`. Post-Phase-8 polish slice (designed, plan drafted, implementation queued).
- **Time-synced poetry spec**: `docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md`. Independent works/poetry runtime slice (designed, implementation queued).
- **Streams section spec**: `docs/superpowers/specs/2026-05-13-streams-section-design.md`. New top-level `/streams/` section + live-state polling via GitHub Action; designed, soft dependency on Citation export.
- **Multi-target export spec**: `docs/superpowers/specs/2026-05-13-multi-target-export-design.md`. Phase 3 Slice 3 — literate org → web essay + PDF + Word via one Emacs command; depends on Phase 3 Slices 1+2.

## Project status (as of 2026-05-13)

**Shipped — Phases 0–6 plus targeted polish:**

- **Site chrome + visual identity** (Phase 0+1): tokens, typography, three-state theme toggle, header/footer, contrast-gated CSS.
- **Essays** (Phase 2): variable-tile Bento index, three-zone post layout (TOC + body + sidenote rail), citation hover-card runtime, figures, footnotes, hero illustrations, series nav, per-section RSS, homepage essays strip.
- **Garden** (Phase 2 + 4): concept/media/reference single-note template, `topic_map` facet, multi-dim AND filter chips with two-tier tag disclosure, stacked-column retrieval (`?stack=` URL sync, sticky path log, consent banner), force-directed graph with zoom/pan/drag-to-reposition, side panel on desktop + standalone `/garden/graph/` on mobile, per-section RSS.
- **Research** (Phase 5): `/research/` index, theme + question hubs, status pills, output icons, backlinks, force-directed research graph (slide-in panel + standalone `/research/graph/`).
- **Works** (Phase 6): polished umbrella (Bento variable-tile grid + tag-cloud filter + ⊞ Graph view toggle with d3-force constellation; three hand-authored medium glyphs: gamepad/eighth-note/quill); games / music / poetry indexes + per-item pages. Runtime-heavy pieces deferred — see table below.
- **About** (Phase 2 bio half): Hero / Bio / Where / Connect / Colophon. Now widget deferred (Phase 3-blocked).
- **Library** (Phase 7 first slice): umbrella + 4 list pages (`/library/{reading,listening,playing,watching}/`); fixture-shaped `data/*.yaml` per spec §10.4; 2 new hand-authored glyphs (book + clapper); shape+color status badges (✓ ▶ ↑ ✗ ★); per-page filter chips with status / format-or-platform / tag dims; nav adds Library as 6th item.
- **Library cover-fetch** (Phase 7 Slice 1): cover infra (data shape via `extras.cover_url`/`isbn`/`mbid`/`igdb_id`/`tmdb_id`/`cover_file`; Hugo `<img>` template with glyph fallback; per-section aspect — listening square, others portrait; `tools/fetch_library_covers.py` with 4 live source paths + IGDB/TMDB `NotImplementedError` stubs; 12th linter pair gating schema + cache + audit consistency + freshness; sha256 audit log at `tools/.cover-cache.json`). 8 PD/fair-use cover thumbnails seeded via Wikimedia thumb URLs (~588 KB total). Live IGDB + TMDB API paths defer to a future slice that pairs with real items + API keys.
- **Homepage v3** (Phase 7 Slice 2): closes Phase 7. New hero (2-col grid, `home_lede` frontmatter split from `description`, hand-authored burgundy mark SVG) + Currently widget (4 rows reading/listening/playing/watching, max-`last_modified` timestamp, spoiler tag only when `spoiler_level == heavy` AND `note_slug` present, empty-row + empty-widget hiding) + Research strip (top 3 active questions, theme-name lookup via `site.GetPage`) + 2-col Research section combining research questions + top-10 garden tiles under one sidebar anchor (each side keeps its own "What I'm chasing" / "From the Garden" sub-header) + standalone full-width Works section (renamed from "Lately, in the studio"; one per medium + most-recent remaining = 4 rows; reuses `works/glyph-sprite.html` rendered once guarded). CSS §38–§40 + responsive breakpoint. Studio type-badge glyphs use `var(--color-stone)` (theme-flipping) for dark-mode contrast on the burgundy/steel `color-mix` gradients.
- **Page sidebar** (Phase 7 polish): shared `partials/page-sidebar.html` taking a `sections` slice of `(id, label)` dicts — emits a fixed-position vertical rotated-labels rail (writing-mode: vertical-rl) on the left margin at viewport ≥1220px AND a sticky horizontal dots strip below 1220px. `assets/js/nav.js` carries a scrollspy that toggles `.is-active` by `href` (so both rail label + strip dot flip together); active = last section whose top has crossed the upper-10% trigger line, with a "force last section active when scrollY + viewportHeight ≥ docHeight" fallback so short final sections still highlight at the page bottom. Integrated across 5 layout families: home, about, research themes, research questions, four library leaves. Each layout owns its anchor list; conditional sections (theme without `garden_topic_ref`, library leaves without queue) filter the slice before passing. <2 entries → partial emits nothing. CSS §41. Label font-size is fluid: `clamp(0.9rem, 0.7rem + 0.35vw, 1.2rem)`.
- **Pagefind search** (Phase 8 Slice 1): full-text site search via Pagefind 1.5.2 (pinned in workflow env). `<dialog>`-based search modal in `layouts/partials/search-modal.html` included once from `baseof.html`; triggered by header magnifier button or `/` key; lazy-loads `/pagefind/pagefind.js` on first open. `entry-search.js` → `search.<hash>.js` (~4 KB) loads on every page. Pagefind index built in CI post-`hugo --minify` into `public/pagefind/` (gitignored, CI-regenerated). Per-layout `data-pagefind-meta` + `data-pagefind-filter` spans emitted as separate hidden elements (one key per element — see Pagefind 1.x gotchas below). Spoiler bodies excluded via `data-pagefind-ignore` on `.spoiler-body`. 13th linter pair (`tools/check_pagefind_meta.py` + `test_check_pagefind_meta.py`) runs post-build to assert every indexable page has `<main data-pagefind-body>`, a `section` meta span, and a `section` filter span. Section filter chips in modal: All / Essays / Garden / Research / Works / Library. CSS §42 + new `--color-paper` token. New `search.svg` hand-authored icon.
- **CI gates trio** (Phase 8 Slice 2): Build smoke test (`tools/check_smoke.py` — 7 top-level URLs rendered via stdlib HTMLParser; sibling-less linter per spec §3.1), page-weight gate (per-page §8 budget — 100/500/600 KB tiers; classifier prefix-keyed; 24-test sibling pins the logic; classifier widened beyond spec §8 to cover `/library/` at 500 KB for cover images + `/research/` at 600 KB for inline graph JS), Lighthouse CI (4 categories ≥0.9 across 12 stable fixture URLs; mobile + desktop runs via two separate config files: `lighthouserc.json` + `lighthouserc.mobile.json`). Workflow grew by 6 steps. CI run time on master adds ~6–10 min for the two LHCI runs.
- **Final QA — partial pass** (Phase 8 Slice 3): QA checklist drafted + committed at `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md`. First-session walkthrough surfaced three deferrable items captured with their own spec stubs. **All three are now resolved or shipped:** the mobile page-sidebar strip pinning bug (resolved 2026-05-13, commit `bab359d` — root cause `.site-nav` lacking `flex-wrap` forced horizontal document overflow and broke Firefox's `position: sticky` paint math; fixed via `flex-wrap: wrap` on `.site-nav` + `html { overflow-x: clip }`, clip-not-hidden because clip does not create a scroll container so sticky descendants keep working); RSS link UX (shipped via the RSS XSL pretty-render slice — see entry below); garden path-log retrieval (shipped via the garden path-log retrieval slice — see entry below).
- **a11y close-out** (Phase 8 follow-up, commit `7ac2539`, 2026-05-13, pushed to origin): static-scan-driven sweep covering every QA checklist item findable from code without a human walkthrough. Approach: 4 parallel agents scanned keyboard nav / SR semantics / colour-blindness redundancy / mobile + perf; 5 BLOCKERs + 16 WARNs + 11 NITs surfaced. Shipped: all 5 blockers + 10 of the 16 warns + a heading-hierarchy sweep across every layout family. *Blockers:* primary filter-chip arrow nav, nested `<main>` cleanup across 9 layouts, research-theme h1→h3 skip (added h2 "Questions" wrapper), sidenote marker `<span role="button">` → `<sup><a>`, search-modal `<mark>` font-weight 600. *Warns:* skip-past-graph link on 3 standalone graph pages, library status-badge `role="img"` + aria-hidden glyph, garden+research graph legends start hidden, citation underline restored, `.essay-references li:target` 3px border-left, `--color-warn` added to contrast linter (works in-progress pill text now inherits stone for 5+:1), garden+research graph SVG min-height 480px, library cover img width/height/decoding=async, QA checklist 1.7 reworded (kbd-hints intentionally non-focusable). *Heading sweep:* essay/works/library card titles promoted to h2, library section dividers `<header>`→`<h2>`, homepage studio-strip h5→h3 — every layout now renders a clean h1→h2→h3 tree. WARNs intentionally NOT shipped: per-node graph SVG tabindex retained (addressed via skip-link instead); sidenote desktop no-reveal addressed indirectly by the blocker fix.
- **RSS XSL pretty-render** (post-Phase-8 polish, 2026-05-13): essays feed (`/essays/index.xml`) now opens in browsers as a styled HTML page via `assets/feed/feed.xsl` referenced by an `<?xml-stylesheet ?>` PI on `layouts/essays/rss.xml`. Inline `<style>` block clones four `:root` tokens from `main.css` (stone / ink / ink-soft / burgundy) and respects `prefers-color-scheme` for dark mode. Two named XSL templates parse the RFC-822 pubDate into ISO-8601 + display form via positional `substring()` slicing on the fixed Hugo format string. Garden + site-wide feed files still emit but stay raw XML (scope guard enforced by linter). **Header chrome collapsed**: `layouts/partials/header.html` previously switched the RSS icon's `href` per-section (essays → essays feed, garden → garden feed, else → home feed); now it always links to `/essays/index.xml`. New linter pair (`tools/check_rss_xsl.py` + sibling) enforces: XSL exists + parses + has stylesheet root + has `template match="/"` + has inline `<style>` sentinel, essays template has PI before `<rss>`, garden template has no PI. CI workflow grows by 2 named steps (40 → 42).
- **Citation export** (post-Phase-8 polish, 2026-05-14, merge `4b2a75e`, pushed to origin): page-level cite metadata + per-reference cite affordances on every citable single page (essays / garden / research themes & questions / works games & music & poetry), plus per-row affordances on library leaves. Highwire `<meta>` tags emit in `<head>` for Zotero auto-detect.

    **Primary CTA**: a sticky burgundy block reading "Cite this _kind_" — contextual per section (`essay` / `note` / `entry` / `reference` / `theme` / `question` / `game` / `release` / `poem`; library rows go a tier deeper to `book` / `album` / `track` / `game` / `movie` / `series`). On essays the CTA + the existing TOC live in a single `.essay-toc-zone` that's `position: fixed` at the viewport left edge (left: 1.5rem) so the sidebar hugs the edge regardless of viewport width; the essay reading column was widened 720 → 900px with `margin-left: max(240px, calc((100% - var(--reading-column)) / 2))` so it re-centers on wide screens but holds a min-runway that never overlaps the fixed sidebar. Garden / research / works place the CTA inline below the title block.

    **Modal**: a singleton `<dialog>` rendered once via `baseof.html`. h2 reads the contextual cite label; subtitle reads the page (or ref / item) title. Five tabs (BibTeX / APA / Chicago / MLA / RIS). Action row splits into `cite-modal-nav-group` (Source steel · Related note green) on the left + `cite-modal-action-group` (Copy burgundy · Download `<ext>` burgundy) on the right. Source/Related note pills hide cleanly when the active source lacks them (self-cite has neither; refs show whichever the entry has). `dialog.close()` (NOT `removeAttribute('open')`) is the only thing that unwinds the modal's inert state — using attribute removal first leaves the rest of the page unclickable.

    **Direction-1 button vocabulary** (color-as-semantic, applied consistently across reference rows + modal + library rows):
    - Burgundy fill → primary cite CTA (`.cite-cta`).
    - Burgundy outline pill → cite action (`.ref-cite-full`, `.cite-modal-copy`, `.cite-modal-download`).
    - Stone outline chip (smaller) → micro copy action (`.ref-cite-copy` for BibTeX / APA / .ris quick-copies).
    - Steel outline pill → external nav (`.ref-cite-source`, `.cite-modal-source`, `.library-row-original` — same `--color-steel` token; one external-link color across the slice).
    - Green outline pill → internal nav (`.ref-cite-note`, `.cite-modal-note`, `.library-row-note` — same `--color-green`).

    Each essay's References list also gets a **"Download all as .bib" bulk button** at the head of the section — concatenates every refs.<key>.formats.bibtex from the scoped cite-data blob.

    **Per-row library cite-data**: every library row + currently-active card emits its own `<script class="cite-data">` inline. `cite.js` scopes lookup to `closest('article')`, so a button in row N reads row N's data. **Class, not id** — multiple `id="cite-data"` would collide in DOM (e.g. stacked garden columns each carry their own blob); switched to `class="cite-data"` early in the slice walkthrough.

    **Build-time pipeline** under `layouts/partials/cite/`: `normalize-{page,ref,library-item}.html` produce a citation dict; `fmt-{bibtex,apa,chicago,mla,ris}.html` consume it; `data-blob.html` emits the JSON blob with `self` + `refs` (one entry per `Page.Scratch.cite-keys` slug the cite shortcode populates; `url` + `notes_ref` forwarded per ref so the modal can render Source/Related note pills). **`jsonify | safeJS`** at the embed point — without `safeJS` Hugo's HTML-context auto-escape double-encodes the result and the runtime parses a string instead of a dict (same trap flagged for graph-data above). `meta-tags.html` emits the five Highwire `citation_*` tags. `cite-cta` is a `<button>`, **not** an `<a href="#cite-this">` — stacked garden columns each have an `id="cite-this"` static-fallback section, so anchor navigation would race-process focus to the FIRST one (always the root) before `preventDefault` could land.

    **Bundle**: `entry-cite.js` → `cite.<hash>.js` (~2.5 KB) loaded on citable single pages + library leaves only.

    **Linter (17th pair)** `tools/check_cite_meta.py` + sibling (16 tests) post-build asserts every citable page has all 5 `citation_*` meta tags, a valid `<script class="cite-data">` blob with `self.citekey` matching `madkour-<year>-<slug>`, all 5 format keys non-empty in self.formats, every refs key existing in `data/citations.yaml`, and a `<section id="cite-this">` static fallback. Library leaves stay non-citable (the page is an index, not the source); the modal still loads there because per-row blobs are independent. `tools/check_citations.py` extended to whitelist `doi / publisher / volume / issue / pages / isbn / type` — required-set unchanged. CI workflow grows by 2 named steps (44 → 46).

    **Side-effects shipped in the same slice**: (1) **RSS scope tightened** — only `/essays/index.xml` emits now. `hugo.yaml` `outputs` config strips RSS from home/section/taxonomy/term; `content/essays/_index.md` opts back into RSS via frontmatter; `layouts/garden/rss.xml` deleted; `about/single.html` + `footer.html` now both link to `/essays/index.xml`. (2) **Slice stubs filed** at `docs/superpowers/specs/2026-05-14-{library-redesign,graph-view-consistency}-design.md` for the next two queued brainstorming sessions.
- **Garden path-log retrieval** (post-Phase-8 polish, 2026-05-13): the persisted visited-notes list now has 3 consumer surfaces. `localStorage['garden-path-log']` schema migrated from v1 (flat slug array) to v2 (`{version:2, sessions:[{root, slugs, at}]}`); one-shot migration on first read wraps any v1 data as one synthetic session. **Three new surfaces:** (1) "Recent paths" widget at the top of `/garden/` showing up to 5 dedup'd most-recent paths — each row is one `<a>` so a click anywhere on the path loads the full `?stack=…`; (2) popover off the path-log "N in stack" count on note pages (desktop only) showing up to 4 dedup'd paths excluding the current session — `role=dialog` with focus trap + Esc-stops-propagation; (3) dedicated `/garden/history/` page with full list (up to 20 sessions), three empty-state variants per consent state, and a "Re-enable tracking" button for the `consent === 'no'` branch. Three new JS modules (`garden-history.js` shared core + 2 thin mount scripts; garden bundle grows ~5–7 KB). `garden-stack.js` swaps `persistVisited(slug)` for `startSession()` (at `init()`) + `extendSession(slug)` (in `appendColumn`); `clearStack` does NOT end the session (matches "start over from here" intent). New linter pair (`tools/check_garden_history.py` + sibling) — 10 source-side assertions including the literal `"version": 2` schema sentinel in `garden-stack.js`. **Also fixed**: `tools/check_garden_fixtures.py` now skips Hugo section directories (those with `_index.md` but no `index.md`) so the new `/garden/history/` section doesn't false-fail the note linter. CI workflow grows by 2 named steps (42 → 44). Closes the last Phase 8 deferral.

**Not started, in phase order:**

- **About Now widget** — Phase 3-blocked (needs elisp pipeline).
- **Phase 3 — org-mode pipeline**: elisp helpers + ox-hugo that wire real content into the fixture-shaped data files. All site fixtures exist to round-trip when this lands. **Two separate publishing commands** required (per spec §14 Phase 3): a Garden/Library/Research publish that runs frequently and idempotently (the "living" surfaces — meant for daily/hourly cadence with no diff when nothing changed), and an Essay publish that's per-post and deliberate (treated as a publishing event with hero/figures/sidenotes/citations rolled in; output reviewed before commit).
- **Phase 8 follow-up: interactive QA walkthrough.** Static-findable issues are resolved (a11y close-out, commit `7ac2539`). Remaining checklist items in `docs/superpowers/qa-checklists/2026-05-13-phase-8-final-qa.md` are all things that need a human at a keyboard / screen-reader / DevTools deficiency emulation / mobile device: §1.1–1.5 and §1.7–1.9 keyboard nav verification, §2 SR walkthrough, §3 colour-blindness simulation, §4 mobile audit at the documented breakpoints (360 / 414 / 768 / 960 / 1220), §5 perf manual cross-check. No outstanding deferrals — both queued Phase 8 deferrals shipped (RSS XSL pretty-render + garden path-log retrieval).

**Designed but not yet implemented** (specs committed 2026-05-13; pick up via `superpowers:executing-plans` when scheduled):

| Feature | Spec | Plan | Phase fit | Notes |
|---|---|---|---|---|
| Time-synced poetry | `2026-05-13-time-synced-poetry-design.md` | not yet drafted | Independent works/poetry runtime slice | Auto-detected `[mm:ss]` markers in poem bodies → audio-driven or animation-driven reveal + player. New linter pair. Foundation for the deferred lyrics runtime. |
| Streams section | `2026-05-13-streams-section-design.md` | not yet drafted | Independent (β parallel with Phase 3 or γ after) | New 7th top-level `/streams/` section. Cron GitHub Action polls Twitch + YouTube every 5 min → writes `data/streams-*.yaml` + auto-stubs draft stream pages. Header LIVE pill. Bidirectional cross-refs to essays/garden/research/works (2 new linter pairs). (Soft dependency on Citation export — now satisfied, shipped 2026-05-14.) |
| Multi-target export pipeline | `2026-05-13-multi-target-export-design.md` | not yet drafted | **Phase 3 Slice 3** | One Emacs interactive command publishes a literate org doc to Hugo essay + PDF + Word. Per-target subtree visibility tags. Elisp + LaTeX classes + Word reference template versioned in `tools/elisp/` and `tools/templates/`. Hard dependency on Phase 3 Slices 1+2 (garden/research publish + standard essay publish). |
| Library page redesign | `2026-05-14-library-redesign-design.md` (stub) | not yet drafted | Independent polish slice | User feedback: `/library/` umbrella feels bland (uniform glyph+stats+top-3 cards, no visual hierarchy, no covers). Stub captures motivation + open dimensions. Brainstorm pending — invoke `superpowers:brainstorming` when scheduled. |
| Graph-view consistency | `2026-05-14-graph-view-consistency-design.md` (stub) | not yet drafted | Independent polish slice | Garden / research / works graphs were implemented as copy-trim siblings; visual style has drifted. Stub lists the divergent dimensions (nodes, edges, legend, panel chrome, palette). Brainstorm pending. Likely shares CSS §27 rewrite + possibly a shared graph-core.js module. |

Recommended sequencing across remaining queued work: **Time-synced poetry (next up — spec drafted, plan still needed)** → Phase 3 Slice 1 (garden publish) → Phase 3 Slice 2 (essay publish) → Multi-target export → Streams section. Library-redesign + graph-view-consistency are polish slices with stub specs only; pick up whenever appetite shows up.

To pick up a slice: read this file + parent spec §14, run `superpowers:brainstorming` then `superpowers:writing-plans` first (none of the remaining queued slices have a drafted plan yet). Confirm with the user whether the slice depends on the elisp pipeline (Multi-target export does; the rest don't).

**Fixture content is always obvious filler** (lorem ipsum / "Example N") — never authored prose, even for layout testing. Real content lands via the elisp pipeline.

### Deferred features (fixtures exercise the shape; stubs carry `data-pending` for future swap-in)

| Capability | Target | Fixture seed |
|---|---|---|
| KaTeX math rendering | Gated on author need | essay fixture #2 (`has_math`) |
| Scroll-synced video runtime | Gated on author need | essay fixture #4 (`has_video_sync`) |
| Per-page interactive widgets + per-page JS bundle convention | Explorable explainables — own future spec (referenced from §7 of multi-target export spec) | essay fixture #5 (`has_widgets`); `widget` shortcode stub emits `data-pending` |
| Game iframe embed (itch / Bitsy / WebGL) | Future works runtime slice | game fixture #1 `embed_url`; `works-embed-stub` anchor |
| Music platform iframe (Bandcamp / SoundCloud / YouTube) | Future works runtime slice | music fixtures #1 / #2 / #4; `works-audio-link` text link only |
| Custom audio player | Future works runtime slice | `works-player-stub` block |
| Synced-lyrics runtime + two-column lyrics layout | Future works runtime slice | music fixture #2 ↔ poem fixture #1; `synced-lyrics-stub`, `lyrics` shortcode is a no-op. Parser foundation (`partials/works/synced-text-parser.html`) is designed in the time-synced poetry spec — lyrics slice reuses it. |
| Audio-pill pulse animation | Future works runtime slice | poem-page audio pill renders without animation |
| Gif-vs-hero toggle on game cards | When real gif assets land | n/a |
| Figure lightbox | Polish phase | n/a |
| Code highlighting palette swap from Dracula | Post-Phase-2 polish | n/a |
| Print stylesheet | Phase 8 polish | n/a |
| Library cover thumbnails (book / album / game / film / series) | Infra shipped 2026-05-12; live IGDB + TMDB paths land with elisp or real items | yaml `extras` accepts `isbn` / `mbid` / `igdb_id` / `tmdb_id` / `cover_url` / `cover_file`; 8 thumbnails seeded via Wikimedia thumb URLs |
| Last.fm scrobble counts on `/library/listening/` | Gated on author need | listening yaml `extras` already accepts (none defined yet); spec §4.23 documents deferral |
| Library RSS feeds | Phase 7 polish or later | essays + garden have RSS; works + library do not |
| `/library/graph/` constellation | Future library polish slice | parent spec did not request a graph view; defer unless appetite shows up |
| About Now widget | Phase 3 (org-mode) | About template has a placeholder slot |
| ORCID `citation_author_orcid` meta | Add when an ORCID exists | partial scaffolds the slot |
| Library item cite export | Reader appetite; library items already have ISBN/MBID/IGDB/TMDB external metadata | n/a |
| DOI / CrossRef integration | When a DOI registrar is in scope | `data/citations.yaml` already accepts a `doi:` field |
| Bulk export (single .bib for all refs on a page) | Reader feedback if requested | n/a |
| Bilingual / Arabic-aware citation formats | Gated on real Arabic content (Phase 3 follow-up) | n/a |

## Hard constraints (from spec §1)

- **No AI-generated text** anywhere on the site. AI is permitted only for site/app code and code for interactive explorables.
- **No AI-generated illustrations.** SVG icons are hand-authored under `assets/images/icons/`. Hero/figure SVGs in essay page bundles are hand-authored placeholders.
- **Privacy by org-export boundary**: content not exported never reaches the site.
- **Accessibility**: WCAG 2.1 AAA for body text, AA for accents; CB-safe palette; never color-only meaning.
- **Fixture content is obviously dummy** (lorem ipsum / "Example N") — never authored prose. Real content lands via the elisp pipeline.
