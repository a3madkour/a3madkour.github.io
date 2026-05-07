# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Personal website for Abdelrahman Madkour, built as a Hugo static site with hand-rolled CSS and deployed to GitHub Pages. Long-form essays are the centerpiece, supported by a Zettelkasten-style knowledge garden, research surface, and creative output (games / music / poetry). All content authored in org-mode + org-roam, exported via ox-hugo.

## Commands

- `hugo server --buildDrafts` — dev server with drafts visible
- `hugo --minify` — production build to `public/`
- `python3 tools/check-contrast.py` — WCAG 2.1 contrast verifier (CI gate)
- `python3 tools/check_fixtures.py` — essay fixture frontmatter linter (CI gate)
- `python3 -m unittest tools/test_check_fixtures.py -v` — essay linter unit tests (CI gate)
- `python3 tools/check_garden_fixtures.py` — garden fixture frontmatter linter (CI gate)
- `python3 -m unittest tools/test_check_garden_fixtures.py -v` — garden linter unit tests (CI gate)

There is no npm step. The Python tooling (linter + contrast) is stdlib-only.

Hugo **extended** (≥ 0.148.0) is required — the GitHub Actions workflow pins `HUGO_VERSION=0.148.0`.

## Architecture

### CSS pipeline — hand-rolled, processed by Hugo

`assets/css/main.css` is a single hand-rolled stylesheet, organized into numbered sections (1 reset → 2 tokens → 3 typography → 4 layout primitives → 5 site header → 6 site footer → 7 hero/role → 8 reduced-motion → 9 page lists/meta + TOC active → 10 essay meta → 11 essay grid + cards → 12 sidenotes → 13 citations + references → 14 figures → 15 essay three-zone layout → 16 filter chips (multi-dim, shared by essays + garden) → 17 series nav → 18 homepage essays strip → 19 garden index (topic sections + tiles + single-note page elements) → 20 garden note header strip + status pill → 21 garden note tile → 22 spoiler runtime → 23 garden empty-state placeholder). Consumed by `layouts/partials/head.html` via `resources.Get` + (production) `minify | fingerprint` with SRI integrity.

- **Tokens** are CSS custom properties on `:root` (light) and `:root[data-theme="dark"]` (dark). System dark is handled by `@media (prefers-color-scheme: dark) :root:not([data-theme])`. The `:root[data-theme="dark"]` block and the media-query block carry duplicate values — both must be updated together when the palette changes.
- **WCAG contrast**: `tools/check-contrast.py` parses the `:root` blocks and verifies four documented pairings (ink/stone AAA, ink-soft/stone AA, burgundy/stone AA, steel/stone AA) in both modes. Failure blocks deploy. Additional tokens `--color-green` (evergreen stage glyph + finished status pill) and `--color-warn` (queued status pill) ride along but aren't checked.
- **No Tailwind, no PostCSS, no Node.** Class names are semantic.

### JS pipeline

`assets/js/index.js` is bundled by Hugo's `js.Build` (esbuild) into `js/bundle.<hash>.js`, minified, fingerprinted, and loaded with `defer`. Entry imports `toggle-theme.js`, `nav.js` (TOC scroll-spy via `IntersectionObserver`), `essay.js`, and `garden.js`. Both `essay.js` and `garden.js` import the shared `filter-chips.js` module (multi-dim AND filter behavior). Each page-level module guards on its own selector (`.essay-body || .essay-grid` / `.garden-grid || .garden-note`) and bails on irrelevant pages.

### Theme toggle

Three-state cycle: **system → light → dark → system**.

- Storage key: `theme-pref` in `localStorage` (absent = system mode).
- The CSS responds to a `data-theme` attribute on `<html>` (not a class).
- An inline `<script>` at the very top of `<head>` (in `head.html`) reads `theme-pref` synchronously during HTML parse and applies `data-theme` before any rendering — prevents FOUC for users with a stored preference. Storage access is wrapped in `try/catch` so restricted contexts (private browsing strict, sandboxed iframes) degrade gracefully.
- The bundled `toggle-theme.js` handles the click cycle, button label updates, and an idempotent re-apply.

### Content & layouts

- **Content sections** (in `content/`): `_index.html` (homepage with role line + essays strip), `about/`, `blog/` (legacy), `essays/` (six fixture posts with filler bodies — see Project status below), `garden/` (14 fixture notes — see Project status), and stubs for `research/`, `works/` (each with a placeholder `_index.md`).
- **Layouts**:
  - `layouts/_default/{baseof,single,list}.html` — base templates.
  - `layouts/home.html` — homepage; renders `.Content` (role line) + the essays strip (1 featured + 3 recents).
  - `layouts/essays/{list,single,rss.xml}.html` — essays index (variable-tile Bento grid + filter chips), essay post (three-zone layout: TOC | body | sidenote rail), per-section RSS feed.
  - `layouts/garden/{list,single,rss.xml}.html` — garden index (topic-map sections + Other notes + multi-dim filter strip), single note page (single template, flavor-routed metadata strip), per-section RSS feed.
  - `layouts/blog/{list,single}.html` — legacy.
  - `layouts/404.html`.
  - `baseof.html` is a thin semantic wrapper (`.page` div around header/main/footer); per-section layouts override `{{ block "main" }}`.
- **Partials**:
  - `head.html` (inline FOUC script + Google Fonts + main.css link)
  - `header.html` (brand + 5-item top nav + RSS button — switches between site-wide and per-section feed by URL prefix for `/essays/` and `/garden/` — + theme toggle)
  - `footer.html` (colophon + social row)
  - `scripts.html` (JS bundle)
  - `filter-chips.html` (shared by essays + garden index — renders chip strip from a `dimensions` parameter; suppresses dims with <2 distinct values)
  - `essay-meta.html` (date · reading-time · tags · series pill — used in cards + post header)
  - `essay-card.html` / `essay-card-featured.html` (grid tiles, reused by `/essays/` index, homepage strip, series nav)
  - `essay-toc.html` (server-rendered TOC from Hugo's `.TableOfContents`; `nav.js` adds active-link highlighting)
  - `essay-references.html` (citations list at end of post; reads page scratch populated by the cite shortcode)
  - `essay-series-nav.html` (prev/next + "Part N of M")
  - `garden/note-header.html` (flavor-routed metadata strip — stage glyph + tended date + media-flavor status pill / dates / spoiler-level / reference-flavor type label)
  - `garden/stage-glyph.html` (hand-authored SVG sprout/two-leaf/tree by stage; `currentColor` stroke; size lg/sm/xs)
  - `garden/note-tile.html` (single tile card; `data-tags`/`data-flavor`/`data-stage` attributes drive the filter JS)
  - `garden/topic-section.html` (H2 + framing italic + tile grid resolved from a topic-map note's ordered slug list)
  - `garden/relative-date.html` (helper — formats a YAML date string as "Nd ago" / "Nmo ago" / "today" etc.; coerces string inputs via `time.AsTime`)
- **Shortcodes**:
  - `cite.html` — looks up `site.Data.citations.citations[key]`, emits `<cite class="citation" data-cite-key>`, errors if key missing
  - `sidenote.html` — auto-numbered marker + aside via page scratch
  - `figure.html` — overrides Hugo default; semantic `<figure><img><figcaption>`; supports `class="wide"` breakout
  - `spoiler.html` — `<details>`-based click-to-reveal; takes `summary` + `level` (`light`/`heavy`); native semantics, no JS, reduced-motion respected
  - `math.html` / `video-sync.html` / `widget.html` — **deferred-feature stubs**: emit a container with a `data-*` hook so fixtures can exercise them; later slices will replace the stub bodies with real renderers (KaTeX, IntersectionObserver, per-page widgets).
- **Top nav** (locked): Essays / Garden / Research / Works / About. Active item gets `aria-current="page"` via `hasPrefix` match.

### Frontmatter contract for essays

Each `content/essays/<slug>/index.md` declares 17 required frontmatter fields enforced by `tools/check_fixtures.py`: `title, date, lastmod, draft, summary, tags, series, series_order, toc, has_sidenotes, has_citations, has_footnotes, has_math, has_widgets, has_video_sync` plus optional `tile_size, featured, hero`. The contract mirrors spec §10 (ox-hugo output shape) so when Phase 3's elisp pipeline arrives, the exporter overwrites fixtures without template changes.

`data/citations.yaml` is a fixture file in the same shape ox-hugo will eventually produce.

### Frontmatter contract for garden notes

Each `content/garden/<slug>/index.md` declares fields enforced by `tools/check_garden_fixtures.py`. **Always required** (all flavors): `title, draft, last_modified, growth_stage`. Flavor is derived from `media_type`:

- **Concept** (no `media_type`) — only the always-required + optional `tags, summary, topic_map, roam_refs, year, weight`.
- **Media** (`media_type ∈ {book, album, track, game, film, series}`) — also required: `status, creator`. Optional: `started, finished, spoiler_level, original_url`, plus the concept-flavor optionals.
- **Reference** (`media_type ∈ {paper, video, article, talk}`) — also required: `creator`. Optional: `original_url`, plus the concept-flavor optionals. `status, started, finished, spoiler_level` are forbidden.

Topic maps are an optional facet on any note: `topic_map: [slug-1, slug-2, ...]` declares an ordered list of other note slugs. The note's own page renders the prose body followed by a curated tile grid; the `/garden/` index surfaces one section per topic-map note. Linter validates that every entry resolves to an existing non-draft note. The shared parser (`parse_frontmatter`) is imported from `tools/check_fixtures.py` — both linters use one parser.

`last_modified` is parsed by Hugo as a string (YAML 1.2 doesn't auto-coerce to `time.Time` for custom keys); template helpers (`garden/relative-date.html`, `garden/rss.xml`) coerce via `time.AsTime` when a string is detected.

### Bento variable-tile grid (essays index + homepage strip)

Cards carry `data-tile-size` and `data-span` attributes resolved per priority order in `layouts/partials/essay-card.html`:
- Tile size: explicit `tile_size` > `featured: true` (large) > in-series (medium) > medium (default)
- Span: `featured: true` → 2 cols; `hero` declared → 2 rows. Combined: `2x1 / 1x2 / 2x2 / 1x1`.

CSS reads `data-span` and applies `grid-column: span N` / `grid-row: span N`.

### Filter chips

`/essays/` and `/garden/` both render filter chip strips via the shared `partials/filter-chips.html` partial (essays: tag / series / year; garden: tag / flavor / stage). **Suppression rule:** dimensions with <2 distinct values don't render. **Active-state:** per-dimension and AND-composed across dimensions — selecting "Budding" while "memory" tag is active narrows to the intersection (notes that are *both*). The shared logic lives in `assets/js/filter-chips.js`; `essay.js` and `garden.js` each call `setupFilterChips({ containerSelector, cardSelector, sectionSelector?, emptyStateSelector? })` with their own selectors. Garden's empty-intersection state: section wrappers with no visible tiles get `hidden`; a `.garden-empty` element shows when zero tiles globally pass.

Taxonomies are declared in `hugo.yaml` (`tag: tags`, `series: series`). Garden tags do not currently round-trip through the `/tags/` taxonomy pages — they're chip-filter-only for now.

### Typography

Three Google Fonts loaded in a single `<link>`: **Petrona** (body, italic + upright at 400/600/700), **Inter** (UI labels), **JetBrains Mono** (code). Display = swap. Token names: `--font-body`, `--font-ui`, `--font-mono`.

### Deployment

`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `master`. The build job runs: Install Hugo CLI → Checkout → Setup Pages → **Verify CSS contrast (WCAG)** → **Verify essay fixtures** → **Run essay linter unit tests** → **Verify garden fixtures** → **Run garden linter unit tests** → Build with Hugo → Upload artifact → Deploy. All five Python checks must pass before the Hugo build.

## Reference docs

- **Design spec** (visual identity, content architecture, per-page layouts, org-mode contract, build pipeline): `docs/superpowers/specs/2026-05-03-personal-site-design.md`
- **Phase 0+1 implementation plan**: `docs/superpowers/plans/2026-05-04-foundation-and-visual-identity.md`
- **Phase 2 essays slice spec**: `docs/superpowers/specs/2026-05-05-essays-section-design.md`
- **Phase 2 essays slice plan**: `docs/superpowers/plans/2026-05-05-essays-section.md`
- **Phase 2 garden slice spec**: `docs/superpowers/specs/2026-05-07-garden-notes-design.md` (amends parent §4.9 — topic maps are a note facet, not a separate URL)
- **Phase 2 garden slice plan**: `docs/superpowers/plans/2026-05-07-garden-notes.md`
- The site spec's §14 is the master phase list.

## Project status (2026-05-07)

**Phase 0+1 complete.** Foundation cleanup (dropped Tailwind/Node) and visual identity scaffold.

**Phase 2 — essays slice complete.** Variable-tile grid index with filter chips, full essay post layout (TOC + sidenotes + citations placeholder + figures + footnotes + tags + hero illustrations + series nav + reading time), per-section RSS, homepage essays strip, fixture frontmatter linter wired into CI. Six fixture essays under `content/essays/<slug>/` exercise all in-scope and deferred capabilities — see the slice spec for the table. **All fixture bodies are obvious filler text (lorem ipsum / "Example N") — never authored prose.** When the elisp/ox-hugo pipeline arrives, fixtures get overwritten in place without template changes.

**Phase 2 — garden slice complete.** Single note template for concept/media/reference flavors with metadata-routed header strip (status pill + dates + spoiler-level + creator + "→ original"); `topic_map:` frontmatter facet (any concept note can declare an ordered slug list and renders a curated tile grid below the body — supersedes parent spec §4.9, no `/garden/topics/` URL); garden index with topic-map sections + "Other notes" catch-all + multi-dimension AND filter chips (tag / flavor / stage); hand-authored SVG growth-stage glyphs (seedling sprout / budding two-leaf / evergreen tree) in `partials/garden/stage-glyph.html`; native `<details>` spoiler runtime (replaces the no-op stub from the essays slice); per-section RSS at `/garden/index.xml`; 14-fixture set covering every status (reading/finished/abandoned/queued), every spoiler-level (none/light/heavy), and every growth stage. **Filter chips refactored:** shared `assets/js/filter-chips.js` module powers both `/essays/` and `/garden/`; both pages migrated to AND-composition (clicking a tag chip + a series chip narrows to intersection — was previously single-active on essays).

**Phase 2 — remaining slices (not started).** Spec §14's Phase 2 also called for About; that's still pending. Beyond Phase 2:
- About page rewrite (real bio, Now widget, affiliations, connect block, full colophon) — Phase 3-dependent for the Now widget.
- Garden interaction model — stacked-columns retrieval, path log with consent, backlinks computation, garden graph view, reduced from this slice — Phase 4.
- Research theme cards + question hubs + research graph — Phase 5.
- Works (games + music + poetry) — Phase 6.
- Library (reading / listening / playing) — data-driven from `data/*.yaml`, Phase 7.
- Homepage v3 final assembly (Currently strip + Studio strip + Garden+Studio columns) — Phase 7. The current homepage has the role line and the essays strip; the rest of v3 is pending.
- Phase 3: org-mode pipeline (elisp helpers + ox-hugo) — wires real content into the fixture-shaped data files.
- Phase 8: Pagefind search + Lighthouse CI + final QA pass.

To pick up the next slice in a future session: read this file + the parent spec §14, pick a slice (About page is one option but blocks on Phase 3's Now widget; Phase 4 garden interactions is the next natural extension of Garden), run `superpowers:brainstorming` then `superpowers:writing-plans`. Most remaining work depends on the org-mode export pipeline; confirm with the user whether to coordinate with their elisp helpers or build with placeholder data first.

### Deferred features still in plan

These capabilities ship as no-op stubs (or are deliberately omitted from rendering) so fixtures exercise them already; when the renderer lands, swap in the real implementation and the existing fixture content verifies it:

| Capability | Target | Fixture seeded |
|---|---|---|
| KaTeX math rendering | Later, gated on author need | essay fixture #2 |
| Scroll-synced video runtime | Later, gated on author need | essay fixture #4 |
| Per-page interactive widgets + per-page JS bundle convention | Later, design when first widget exists | essay fixture #5 |
| Citation hover-card runtime | Phase 3 | `data-cite-key` hooks present in all essay citation fixtures + garden `roam_refs` field on media/reference notes |
| Figure lightbox | Polish phase | n/a |
| Code highlighting palette swap from Dracula | Post-Phase-2 | n/a (Dracula stays placeholder) |
| Print stylesheet | Phase 8 polish | n/a |
| Garden outgoing-link section on note pages | Phase 4 | body internal links use `[text](/garden/<slug>/)` form (e.g., `surprise-budget` → `salience-and-memory`) |
| Garden backlinks section | Phase 4 | computed at build time from outgoing links — `salience-and-memory` is referenced from `surprise-budget`'s body |
| Garden stacked-columns retrieval + path log | Phase 4 | (no fixture hook — pure UX layer) |
| Garden graph view | Phase 4 | (`data/notes.json` arrives in Phase 3) |
| Library cross-linking from media garden notes | Phase 7 | media-flavor garden notes are the canonical source; library will be a filtered view |
| `single` mode in shared filter-chips JS | Removed once both essays + garden have shipped on `and` mode (this slice) | follow-up — no fixture hook |

## Hard constraints (from spec §1)

- **No AI-generated text** anywhere on the site. AI is permitted only for site/app code and code for interactive explorables.
- **No AI-generated illustrations.** SVG icons are hand-authored under `assets/images/icons/`. Hero/figure SVGs in essays page bundles are hand-authored placeholders.
- **Privacy by org-export boundary**: content not exported never reaches the site.
- **Accessibility**: WCAG 2.1 AAA for body text, AA for accents; CB-safe palette; never color-only meaning.
- **Fixture content is obviously dummy** (lorem ipsum / "Example N") — never authored prose, even for layout testing. Real content lands via the elisp pipeline.
