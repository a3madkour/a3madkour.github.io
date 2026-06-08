# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Personal website for Abdelrahman Madkour, built as a Hugo static site with hand-rolled CSS and deployed to GitHub Pages. Long-form essays are the centerpiece, supported by a Zettelkasten-style knowledge garden, research surface, and creative output (games / music / poetry). All content authored in org-mode + org-roam, exported via ox-hugo.

## Commands

- `hugo server --buildDrafts` — dev server with drafts visible.
- `hugo --minify` — production build to `public/`. **Do not run with a dev server alive**; it poisons the dev-server CSS via a MIME mismatch.
- `python3 tools/check-contrast.py` — WCAG 2.1 contrast verifier (CI gate).
- Twenty-six linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, essay TOC depth, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, math frontmatter coupling, works fixtures, works links, synced poetry, library fixtures, library links, library covers, library shelves, icon attribution, RSS XSL, garden history, streams fixtures, streams links, pagefind metadata, cite metadata, page weights, LHCI URL resolution, org-asset references. `tools/check_smoke.py` and `tools/check_graph_chrome.py` are sibling-less linters (no paired test file — spec §3.1: logic is too thin to warrant pairing).

No npm. Python tooling is stdlib-only. Hugo **extended** (≥ 0.162.1) is required — `.github/workflows/hugo.yaml` pins `HUGO_VERSION=0.162.1`. (Hugo 0.162+ tightened the default `security.allowContent` policy to deny `text/html` source files; this site avoids the issue by using `_index.md` rather than `_index.html` for the homepage.)

## Architecture

### CSS pipeline — hand-rolled, processed by Hugo

`assets/css/main.css` is a single hand-rolled stylesheet, organized into numbered sections §1–§46 (see the file's top-of-file index for the list; §32–§36 are reserved for past works-section additions that landed without numbered headers; §38–§40 cover the homepage hero, Currently widget, and homepage strips; §41 covers the cross-template page sidebar; §42 covers the search modal; §43 covers citation export; §44 covers the library umbrella redesign — hero + themed shelves + bottom catalogue; §45 covers the synced-poetry runtime (reveal opacity/flourish + JS-built player chrome); §46 covers the streams section — header live-pill, click-to-load YouTube embed, archive grid, upcoming strip, cross-section from-stream attribution, category pill palette). Consumed by `layouts/partials/head.html` via `resources.Get` + (production) `minify | fingerprint` with SRI integrity.

- **Tokens** are CSS custom properties on `:root` (light) and `:root[data-theme="dark"]` (dark). System dark via `@media (prefers-color-scheme: dark) :root:not([data-theme])`. The `[data-theme="dark"]` block and the media-query block carry **duplicate values** — both must be updated together when the palette changes.
- **WCAG contrast**: `tools/check-contrast.py` parses the `:root` blocks and verifies nine pairings in both modes — ink/stone AAA; ink-soft/stone, burgundy/stone, steel/stone, green/stone, green-mid/stone, green-soft/stone, warn/stone (and the inverse stone/warn for the queued pill background) all AA. Failure blocks deploy. The three green stops are the garden stage-glyph ramp (evergreen / budding / seedling). Token `--color-paper` (floating panel surface — search modal; light `#fdfcf8`, dark `#2a2a2a`; semantically distinct from `--color-tile` which is the grid-item surface) rides along but isn't checked.
- **No Tailwind, no PostCSS, no Node.** Class names are semantic.

### JS pipeline — multi-entry bundling

`layouts/partials/scripts.html` runs Hugo's `js.Build` (esbuild) eleven times — minified + fingerprinted, classic-script with SRI:

| Entry | Output | Loaded on | Notes |
|---|---|---|---|
| `js/index.js` | `core.<hash>.js` (~1.4 KB) | every page | `toggle-theme.js` + `nav.js` |
| `js/entry-essay.js` | `essay.<hash>.js` (~4.8 KB) | `.Section == "essays"` | imports `filter-chips.js` + `citation-card.js` |
| `js/entry-garden.js` | `garden.<hash>.js` (~117 KB) | `.Section == "garden"` | `garden.js` + `garden-stack.js` + `garden-graph.js` + ~95 KB vendored d3 modules |
| `js/entry-research.js` | `research.<hash>.js` (~107 KB) | `/research/` and `/research/graph/` only | `research-graph.js` (copy + trim of `garden-graph.js`); page-narrow predicate over section-wide |
| `js/entry-works.js` | `works.<hash>.js` (~4 KB) | `.Section == "works"` AND NOT `/works/`-or-`/works/graph/` | imports `filter-chips.js`; per-item pages only |
| `js/entry-works-umbrella.js` | `works-umbrella.<hash>.js` (~112 KB) | `/works/` and `/works/graph/` only | `works.js` + `works-graph.js` (copy + trim of `research-graph.js`) + vendored d3 modules |
| `js/entry-library.js` | `library.<hash>.js` (~5 KB) | `.Section == "library"` | imports `filter-chips.js` + `library-shelf-nav.js`; per-leaf pages AND umbrella |
| `js/entry-search.js` | `search.<hash>.js` (~4 KB) | every page | search modal open/close logic; lazy-loads `/pagefind/pagefind.js` on first open |
| `js/entry-cite.js` | `cite.<hash>.js` (~2.5 KB) | `.Section in {essays, garden, research, works}` AND `.Kind == "page"` | `cite.js` — citation modal runtime (parse #cite-data blob, open `<dialog>`, tab/copy/download, Half B inline copy) |
| `js/entry-poetry.js` | `poetry.<hash>.js` (~4 KB) | `.Section == "works"` AND `.Kind == "page"` AND `.Type == "works-poetry"` | `poem-synced.js` — synced-reveal runtime; JS-built player |
| `js/entry-streams.js` | `streams.<hash>.js` (~1 KB) | `.Section == "streams"` | `streams.js` — click-to-load YouTube embed + filter-chip setup on the /streams/ section index |

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
| Streams | `streams` | `category`, `archive_status` |
| About / Home / Blog (legacy) | section name only | — |

**Indexing controls**: `<main data-pagefind-body>` in `baseof.html` scopes the indexed body. `data-pagefind-ignore` on `.spoiler-body` (in `spoiler` shortcode) excludes spoiler content from the index.

### Math pipeline

Math content is authored in org-mode and validated **before publish**, not after.

1. **`org-math-lint` (pre-publish, dotfiles)** — runs against org source files; tokenizes, applies a 10-rule registry (delimiters, fragmented math, unicode → LaTeX, unknown commands), verifies each fragment by parsing it with vendored KaTeX in V8 via `py-mini-racer`. Source: `~/org/notes/tools/org-math-lint/` (not in this repo). Invoked by `a3-pub.sh` (default on; opt out via `--skip-math-check`).
2. **B.4 essays handler `has_math` scanner (dotfiles)** — buffer scan for math markers (`{{< math >}}` stub, `\(`, `\[`, `\begin{…}`) excluding fenced code blocks; sets emitted `has_math` frontmatter. `#+HUGO_HAS_MATH:` keyword acts as manual override when present.
3. **`tools/check_math.py` (site CI, 25th linter pair)** — coupling-only: every essay's `has_math` value must match whether the body actually contains math markers. Catches publish bugs the source-side validator can't see.
4. **KaTeX runtime — deferred.** No math engine ships on the site yet. When it lands, it will parse the canonical `\(...\)` / `\[...\]` forms `org-math-lint` produces.

### Content & layouts

- **Content sections** in `content/`: `_index.html`, `about/`, `blog/` (legacy), `essays/`, `garden/`, `research/`, `works/`.
- **Layouts** under `layouts/`: base templates in `_default/`; per-section `{list,single}.html` plus `rss.xml` for essays + garden and standalone `graph.html` pages for garden + research + works. Works splits into `works/`, `works-games/`, `works-music/`, `works-poetry/`. Research splits into `research/`, `research-theme/`, `research-question/` with type discrimination via `cascade: { type: research-theme|research-question }` on `content/research/{themes,questions}/_index.md` (bare section URLs hidden via `build: render: never`). `baseof.html` is a thin semantic wrapper; per-section layouts override `{{ block "main" }}`.
- **Partials** under `layouts/partials/`: site chrome (`head`, `header`, `footer`, `scripts`); essays (`essay-card{,-featured}`, `essay-meta`, `essay-toc`, `essay-references`, `essay-series-nav`); shared `filter-chips.html`, `page-sidebar.html` (cross-template rotated-labels rail + mobile dots strip), `search-modal.html` (included once in `baseof.html`); `home/` subfolder (`hero`, `currently`, `research-strip`, `garden-strip`, `studio-strip` — homepage v3 sections); `garden/` subfolder (`note-header`, `stage-glyph`, `note-tile`, `topic-section`, `relative-date`, `path-log`, `links-section`, `graph-{data,script,panel}`); `research/` subfolder (`status-pill`, `output-item`, `theme-card`, `backlinks-data`, `graph-{data,script,panel}`); `works/` subfolder (`tile`, `glyph-sprite`, `game-card`, `music-row`, `poem-row`, `status-pill`, `audio-pill`, `audio-link`, `connections`, `graph-{data,data-inner,script,panel}`, `synced-marker-seconds`, `synced-text-parser`, `poem-synced`).
- **Shortcodes** under `layouts/shortcodes/`: `cite` (looks up `site.Data.citations.citations[key]`, errors if missing), `sidenote` (auto-numbered marker + aside via page scratch), `figure` (semantic, supports `class="wide"`), `spoiler` (`<details>`-based, no JS). Deferred-feature stubs: `math`, `video-sync`, `widget`, `lyrics` — each emits a `data-pending` container so fixtures exercise the shape.
- **Top nav** (locked): Essays / Garden / Research / Works / Library / Streams / About. Active item gets `aria-current="page"` via `hasPrefix` match. (Streams added 2026-05-19; was previously 6 items.)

### Semantic blocks (AMS-style)

Essays can use 12 AMS-style block shortcodes for rigorous prose: `theorem`, `lemma`, `corollary`, `proposition`, `definition`, `proof`, `remark`, `example`, `note`, `claim`, `conjecture`, `axiom`. Each is a Hugo shortcode in `layouts/shortcodes/` with per-page auto-numbering via `$page.Scratch`.

Authors write `#+begin_theorem` blocks in org, with optional `#+attr_shortcode: :title <name> :id <slug>` header line for title and cross-reference ID. ox-hugo's `org-hugo-paired-shortcodes` config (in `a3madkour-publish-export.el`) emits the matching `{{< theorem title="…" id="…" >}}…{{< /theorem >}}` markdown.

**Numbering follows AMS conventions:** theorem/lemma/corollary/proposition share one counter (`theorem-family`); definition/remark/example/note/claim/conjecture/axiom each have independent counters; proof is unnumbered (auto-appends ∎ tombstone).

**Cross-references** use the block's `#+attr_shortcode: :id <slug>` + org's `[[#id][text]]` link syntax. Visible reference text is author-managed (renumber-induced drift is a documented limitation; auto-formatting is a D.x follow-up). `:CUSTOM_ID:` property drawers continue to work for headings (B.1.1 unchanged) but are silently dropped by ox-hugo on special blocks.

**CSS §47** styles three visual tiers (strong / soft / chrome-less) using existing color tokens. No new `has_*` frontmatter flag — the CSS loads on every essay page.

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

**Streams** (`content/streams/<YYYY-MM-DD>-<slug>/index.md`) — enforced by `tools/check_streams_fixtures.py`. Required: `title, date, platforms, category, archive_status, draft`. Optional: `duration, vod_url, twitch_archive_url, archive_url, tags, summary, related_essays, related_garden, related_research, related_works`. `platforms` ⊆ `{twitch, youtube}`. `category` ∈ `{game-dev, research, coding, creative}`. `archive_status` ∈ `{live, archived, removed, private}`. Cross-val: `archive_status == archived` ⇒ `vod_url` non-empty. Bidirectional symmetry `related_* ↔ source_stream` enforced by `tools/check_streams_links.py` (the 23rd linter pair). Live state + schedule cache: `data/streams-live.yaml` / `data/streams-schedule.yaml` / `data/streams-twitch-cache.yaml` — shape-validated by the same fixtures linter.

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
- Same gotcha for `data/streams-*.yaml`: `site.Data.streams-live` etc. would silently break. Read via `index site.Data "streams-live"` / `"streams-schedule"` / `"streams-twitch-cache"`.

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

Three **self-hosted** fonts loaded via `@font-face` in `assets/css/main.css` §3: **Petrona** (body, italic + upright at 400/600/700), **Inter** (UI labels, 400/500/600), **JetBrains Mono** (code, 400). Display = swap. Token names: `--font-body`, `--font-ui`, `--font-mono`.

woff2 files live in `static/fonts/` (latin + latin-ext subsets only; browsers download per-subset based on unicode-range matching). 16 woff2 files total, ~595 KB on disk; over-the-wire downloads are subset-gated by the browser so a Latin-only page typically pulls 4–6 files. **Don't reintroduce the `fonts.googleapis.com` `<link>`** — CI's TTFB to it caused LHCI desktop perf to flake below 0.9 (see [[reference_lhci_google_fonts_flakiness]] / commit history near 2026-05-30).

### Deployment

`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `master`. CI step order: pre-build linters (contrast + 25 linter pairs + 1 sibling-less = 52 steps) → `hugo --minify` → pagefind metadata linter unit tests → verify pagefind metadata on built pages → cite metadata linter unit tests → verify cite metadata on built pages → install Pagefind 1.5.2 binary → build Pagefind index into `public/pagefind/` → smoke test → LHCI URL check → page-weight linter + unit tests → Lighthouse CI desktop (2 steps: `lighthouserc.json`) → Lighthouse CI mobile (`lighthouserc.mobile.json`) → upload artifact → deploy. Total: 65 named steps. (A separate cron workflow `.github/workflows/streams-poll.yaml` runs every 5 minutes — outside this build/deploy pipeline.) Any failure blocks deploy. `public/pagefind/` is gitignored and CI-regenerated each run. Two separate LHCI config files (`lighthouserc.json` for desktop, `lighthouserc.mobile.json` for mobile) — simpler than an env-override approach.

### Anchor-link affordance

Every `id`-bearing reading-flow element inside `<main>` (headings `<h2>`–`<h6>` plus elements whose class list contains a `block-` token — i.e., D.1 semantic blocks) carries a trailing `§` glyph that copies the absolute URL to the clipboard on click and surfaces a top-of-viewport status banner ("Link to *X* copied"). Source of truth is one partial — `layouts/partials/anchor-link.html` — called by the Goldmark heading render hook (`layouts/_default/_markup/render-heading.html`), the 12 D.1 semantic-block shortcodes, and 7 chrome partials (References, Recent paths, From this stream, Upcoming, library shelf headings, catalogue, Cite static fallback). Behavior in `assets/js/anchor-link.js` (~1 KB; site-wide entry; delegated `click` listener on `<main>`; Escape skipped when a `<dialog>` is open so the cite modal's native cancel wins). CSS §48. Per-element opt-out via `data-no-anchor-link` (applied to the Cite modal `<h2>`). 27th linter pair (`check_anchor_link.py`) gates the partial-emission invariant; smoke test asserts at least one `.anchor-link` on `/essays/example-five/`.

## Reference docs

- **Design spec (canonical)**: `docs/superpowers/specs/2026-05-03-personal-site-design.md`. §14 is the master phase list.
- **Per-slice specs and plans** under `docs/superpowers/{specs,plans}/`, dated by slice. Memory has shipped-slice details (`project_*.md`); the queued-work entries below cover what's still ahead.
- **Time-synced poetry**: `docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md` (designed) + `docs/superpowers/plans/2026-05-18-time-synced-poetry.md` (plan). Shipped — see memory `project_time_synced_poetry_slice.md`.
- **Org → synced-poetry export**: `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md` (stub, no plan). Phase 3 — elisp/ox-hugo emits the shipped synced-poetry markup contract from real org content.
- **Streams section**: `docs/superpowers/specs/2026-05-13-streams-section-design.md`. New `/streams/` top-level; cron-polled live state.
- **Multi-target export**: `docs/superpowers/specs/2026-05-13-multi-target-export-design.md`. Phase 3 Slice 3 — literate org → Hugo + PDF + Word.
- **TOC collapsible subsections**: `docs/superpowers/specs/2026-05-14-toc-collapsible-subsections-design.md` (designed) + `docs/superpowers/plans/2026-05-18-toc-collapsible-subsections.md` (plan). Shipped — see memory `project_toc_collapsible_subsections_slice.md`.

## Project status (as of 2026-06-07)

**Shipped**: Phases 0–8 (modulo interactive QA walkthrough) plus Citation export + Library redesign + Graph-view chrome-consistency + Persistent-graph-access + TOC collapsible subsections + Time-synced poetry + Streams section slices. Phase 3 org-mode pipeline: sub-projects **A** (5 plans), **B** (B.0–B.4), **F** (citations), **C** (math validator), **D** (D.1 semantic blocks + D.2 multi-target export) all shipped. Per-slice merge details live in memory under `project_*.md`.

**Active queue is now polish-and-bugfix-first.** Sub-project E (explorables — the last Phase 3 piece) was pushed to Tier 8 in the 2026-06-07 reorder. Two durable specs hold the canonical queue:

- **`docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`** — 8 tiers, ordering, entry checklists. **Tier 1 fully closed 2026-06-07 (10/10); Tier 2 (UX polish) is next.** 2.1 (anchor affordance) brainstormed 2026-06-07 → [`2026-06-07-anchor-affordance-design.md`](docs/superpowers/specs/2026-06-07-anchor-affordance-design.md); plan + impl pending.
- **`docs/superpowers/specs/2026-06-07-deferred-features-registry.md`** — long-horizon trigger-gated capabilities (Tier 9).

Both specs are the source of truth — they survive independently of this file. The CLAUDE.md "Deferred features" table that lived here previously is now in the registry spec.

To pick up the next session: read the roadmap top-to-bottom, start at the highest-numbered open item in the next-up tier (today, Tier 2.1 — its design spec is committed; the next session opens `superpowers:writing-plans` against that spec). For sub-project E specifically (when its time comes), also read `memory/project_phase_3_decomposition.md` + parent spec §14.

## Hard constraints (from spec §1)

- **No AI-generated text** anywhere on the site. AI is permitted only for site/app code and code for interactive explorables.
- **No AI-generated illustrations.** SVG icons are hand-authored under `assets/images/icons/`. Hero/figure SVGs in essay page bundles are hand-authored placeholders.
- **Privacy by org-export boundary**: content not exported never reaches the site.
- **Accessibility**: WCAG 2.1 AAA for body text, AA for accents; CB-safe palette; never color-only meaning.
- **Fixture content is obviously dummy** (lorem ipsum / "Example N") — never authored prose. Real content lands via the elisp pipeline.
