# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Personal website for Abdelrahman Madkour, built as a Hugo static site with hand-rolled CSS and deployed to GitHub Pages. Long-form essays are the centerpiece, supported by a Zettelkasten-style knowledge garden, research surface, and creative output (games / music / poetry). All content authored in org-mode + org-roam, exported via ox-hugo.

## Commands

- `hugo server --buildDrafts` — dev server with drafts visible
- `hugo --minify` — production build to `public/`
- `python3 tools/check-contrast.py` — WCAG 2.1 contrast verifier (CI gate)
- `python3 tools/check_fixtures.py` — essay fixture frontmatter linter (CI gate)
- `python3 -m unittest tools/test_check_fixtures.py -v` — linter unit tests (CI gate)

There is no npm step. The Python tooling (linter + contrast) is stdlib-only.

Hugo **extended** (≥ 0.148.0) is required — the GitHub Actions workflow pins `HUGO_VERSION=0.148.0`.

## Architecture

### CSS pipeline — hand-rolled, processed by Hugo

`assets/css/main.css` is a single hand-rolled stylesheet, organized into numbered sections (1 reset → 2 tokens → 3 typography → 4 layout primitives → 5 site header → 6 site footer → 7 hero/role → 8 reduced-motion → 9 page lists/meta + TOC active → 10 essay meta → 11 essay grid + cards → 12 sidenotes → 13 citations + references → 14 figures → 15 essay three-zone layout → 16 filter strip → 17 series nav → 18 homepage essays strip). Consumed by `layouts/partials/head.html` via `resources.Get` + (production) `minify | fingerprint` with SRI integrity.

- **Tokens** are CSS custom properties on `:root` (light) and `:root[data-theme="dark"]` (dark). System dark is handled by `@media (prefers-color-scheme: dark) :root:not([data-theme])`. The `:root[data-theme="dark"]` block and the media-query block carry duplicate values — both must be updated together when the palette changes.
- **WCAG contrast**: `tools/check-contrast.py` parses the `:root` blocks and verifies four documented pairings (ink/stone AAA, ink-soft/stone AA, burgundy/stone AA, steel/stone AA) in both modes. Failure blocks deploy.
- **No Tailwind, no PostCSS, no Node.** Class names are semantic.

### JS pipeline

`assets/js/index.js` is bundled by Hugo's `js.Build` (esbuild) into `js/bundle.<hash>.js`, minified, fingerprinted, and loaded with `defer`. Entry imports `toggle-theme.js`, `nav.js` (TOC scroll-spy via `IntersectionObserver`), and `essay.js` (sidenote/footnote popups on narrow viewports + smooth-scroll on TOC clicks + citation hover-card hook). `essay.js` is guarded by `.essay-body || .essay-grid` presence, so it bails on non-essay pages.

### Theme toggle

Three-state cycle: **system → light → dark → system**.

- Storage key: `theme-pref` in `localStorage` (absent = system mode).
- The CSS responds to a `data-theme` attribute on `<html>` (not a class).
- An inline `<script>` at the very top of `<head>` (in `head.html`) reads `theme-pref` synchronously during HTML parse and applies `data-theme` before any rendering — prevents FOUC for users with a stored preference. Storage access is wrapped in `try/catch` so restricted contexts (private browsing strict, sandboxed iframes) degrade gracefully.
- The bundled `toggle-theme.js` handles the click cycle, button label updates, and an idempotent re-apply.

### Content & layouts

- **Content sections** (in `content/`): `_index.html` (homepage with role line + essays strip), `about/`, `blog/` (legacy), `essays/` (six fixture posts with filler bodies — see Project status below), and stubs for `garden/`, `research/`, `works/` (each with a placeholder `_index.md`).
- **Layouts**:
  - `layouts/_default/{baseof,single,list}.html` — base templates.
  - `layouts/home.html` — homepage; renders `.Content` (role line) + the essays strip (1 featured + 3 recents).
  - `layouts/essays/{list,single,rss.xml}.html` — essays index (variable-tile Bento grid + filter chips), essay post (three-zone layout: TOC | body | sidenote rail), per-section RSS feed.
  - `layouts/blog/{list,single}.html` — legacy.
  - `layouts/404.html`.
  - `baseof.html` is a thin semantic wrapper (`.page` div around header/main/footer); per-section layouts override `{{ block "main" }}`.
- **Partials**:
  - `head.html` (inline FOUC script + Google Fonts + main.css link)
  - `header.html` (brand + 5-item top nav + RSS button — switches between site-wide and per-section feed by URL prefix — + theme toggle)
  - `footer.html` (colophon + social row)
  - `scripts.html` (JS bundle)
  - `essay-meta.html` (date · reading-time · tags · series pill — used in cards + post header)
  - `essay-card.html` / `essay-card-featured.html` (grid tiles, reused by `/essays/` index, homepage strip, series nav)
  - `essay-toc.html` (server-rendered TOC from Hugo's `.TableOfContents`; `nav.js` adds active-link highlighting)
  - `essay-references.html` (citations list at end of post; reads page scratch populated by the cite shortcode)
  - `essay-series-nav.html` (prev/next + "Part N of M")
- **Shortcodes**:
  - `cite.html` — looks up `site.Data.citations.citations[key]`, emits `<cite class="citation" data-cite-key>`, errors if key missing
  - `sidenote.html` — auto-numbered marker + aside via page scratch
  - `figure.html` — overrides Hugo default; semantic `<figure><img><figcaption>`; supports `class="wide"` breakout
  - `spoiler.html` / `math.html` / `video-sync.html` / `widget.html` — **deferred-feature stubs**: emit a container with a `data-*` hook so fixtures can exercise them; later slices will replace the stub bodies with real renderers (KaTeX, click-to-reveal, IntersectionObserver, per-page widgets).
- **Top nav** (locked): Essays / Garden / Research / Works / About. Active item gets `aria-current="page"` via `hasPrefix` match.

### Frontmatter contract for essays

Each `content/essays/<slug>/index.md` declares 17 required frontmatter fields enforced by `tools/check_fixtures.py`: `title, date, lastmod, draft, summary, tags, series, series_order, toc, has_sidenotes, has_citations, has_footnotes, has_math, has_widgets, has_video_sync` plus optional `tile_size, featured, hero`. The contract mirrors spec §10 (ox-hugo output shape) so when Phase 3's elisp pipeline arrives, the exporter overwrites fixtures without template changes.

`data/citations.yaml` is a fixture file in the same shape ox-hugo will eventually produce.

### Bento variable-tile grid (essays index + homepage strip)

Cards carry `data-tile-size` and `data-span` attributes resolved per priority order in `layouts/partials/essay-card.html`:
- Tile size: explicit `tile_size` > `featured: true` (large) > in-series (medium) > medium (default)
- Span: `featured: true` → 2 cols; `hero` declared → 2 rows. Combined: `2x1 / 1x2 / 2x2 / 1x1`.

CSS reads `data-span` and applies `grid-column: span N` / `grid-row: span N`.

### Filter chips

`/essays/` filter strip renders chips for tag, series, year. **Suppression rule:** dimensions with <2 distinct values don't render their strip (e.g., year strip is hidden while only 2026 fixtures exist). Tag and series chips link to Hugo taxonomy pages (`/tags/<slug>/`, `/series/<slug>/`) as no-JS fallback. Year chips are inert spans (computed at render-time from `.Date`, no taxonomy backing). Active-state is single-chip-across-all-dimensions: selecting a chip clears the others. JS lives in `essay.js#setupFilterChips`.

Taxonomies are declared in `hugo.yaml` (`tag: tags`, `series: series`).

### Typography

Three Google Fonts loaded in a single `<link>`: **Petrona** (body, italic + upright at 400/600/700), **Inter** (UI labels), **JetBrains Mono** (code). Display = swap. Token names: `--font-body`, `--font-ui`, `--font-mono`.

### Deployment

`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `master`. The build job runs: Install Hugo CLI → Checkout → Setup Pages → **Verify CSS contrast (WCAG)** → **Verify essay fixtures** → **Run linter unit tests** → Build with Hugo → Upload artifact → Deploy. All three Python checks must pass before the Hugo build.

## Reference docs

- **Design spec** (visual identity, content architecture, per-page layouts, org-mode contract, build pipeline): `docs/superpowers/specs/2026-05-03-personal-site-design.md`
- **Phase 0+1 implementation plan**: `docs/superpowers/plans/2026-05-04-foundation-and-visual-identity.md`
- **Phase 2 essays slice spec**: `docs/superpowers/specs/2026-05-05-essays-section-design.md`
- **Phase 2 essays slice plan**: `docs/superpowers/plans/2026-05-05-essays-section.md`
- The site spec's §14 is the master phase list.

## Project status (2026-05-05)

**Phase 0+1 complete.** Foundation cleanup (dropped Tailwind/Node) and visual identity scaffold.

**Phase 2 — essays slice complete.** Variable-tile grid index with filter chips, full essay post layout (TOC + sidenotes + citations placeholder + figures + footnotes + tags + hero illustrations + series nav + reading time), per-section RSS, homepage essays strip, fixture frontmatter linter wired into CI. Six fixture essays under `content/essays/<slug>/` exercise all in-scope and deferred capabilities — see the slice spec for the table. **All fixture bodies are obvious filler text (lorem ipsum / "Example N") — never authored prose.** When the elisp/ox-hugo pipeline arrives, fixtures get overwritten in place without template changes.

**Phase 2 — remaining slices (not started).** Spec §14's Phase 2 also called for About + Garden notes; those are still pending. Beyond Phase 2:
- About page rewrite (real bio, Now widget, affiliations, connect block, full colophon) — Phase 3-dependent for the Now widget.
- Garden notes (single template + index + topic maps) — Phase 4 adds the graph view + stacked-column retrieval.
- Research theme cards + question hubs + research graph — Phase 5.
- Works (games + music + poetry) — Phase 6.
- Library (reading / listening / playing) — data-driven from `data/*.yaml`, Phase 7.
- Homepage v3 final assembly (Currently strip + Studio strip + Garden+Studio columns) — Phase 7. The current homepage has the role line and the essays strip; the rest of v3 is pending.
- Phase 3: org-mode pipeline (elisp helpers + ox-hugo) — wires real content into the fixture-shaped data files.
- Phase 8: Pagefind search + Lighthouse CI + final QA pass.

To pick up the next slice in a future session: read this file + the parent spec §14, pick a slice (Garden notes is the natural next; it shares the prose layout that's now proven), run `superpowers:brainstorming` then `superpowers:writing-plans`. Most remaining work depends on the org-mode export pipeline; confirm with the user whether to coordinate with their elisp helpers or build with placeholder data first.

### Deferred features still in plan

The essays slice ships these capabilities as no-op shortcode stubs that fixtures already exercise. When the renderer lands, swap the stub body and the existing fixture content immediately verifies it:

| Capability | Target | Fixture seeded |
|---|---|---|
| Spoiler block runtime (click-to-reveal CSS) | Phase 4 (Garden) | fixture #3 |
| KaTeX math rendering | Later, gated on author need | fixture #2 |
| Scroll-synced video runtime | Later, gated on author need | fixture #4 |
| Per-page interactive widgets + per-page JS bundle convention | Later, design when first widget exists | fixture #5 |
| Citation hover-card runtime | Phase 3 | `data-cite-key` hooks present in all citation fixtures |
| Figure lightbox | Polish phase | n/a |
| Code highlighting palette swap from Dracula | Post-Phase-2 | n/a (Dracula stays placeholder) |
| Multi-dimension filter combination (tag AND year) | Later, gated on whether wanted | n/a |
| Print stylesheet | Phase 8 polish | n/a |

## Hard constraints (from spec §1)

- **No AI-generated text** anywhere on the site. AI is permitted only for site/app code and code for interactive explorables.
- **No AI-generated illustrations.** SVG icons are hand-authored under `assets/images/icons/`. Hero/figure SVGs in essays page bundles are hand-authored placeholders.
- **Privacy by org-export boundary**: content not exported never reaches the site.
- **Accessibility**: WCAG 2.1 AAA for body text, AA for accents; CB-safe palette; never color-only meaning.
- **Fixture content is obviously dummy** (lorem ipsum / "Example N") — never authored prose, even for layout testing. Real content lands via the elisp pipeline.
