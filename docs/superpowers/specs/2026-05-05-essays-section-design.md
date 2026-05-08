# Essays section — design spec

**Date:** 2026-05-05
**Status:** Spec drafted; ready for implementation plan
**Slice of:** Phase 2 of the personal-site rebuild (`docs/superpowers/specs/2026-05-03-personal-site-design.md`)
**Predecessor:** `docs/superpowers/plans/2026-05-04-foundation-and-visual-identity.md` (Phase 0+1, complete)
**Successor:** This spec → implementation plan via `superpowers:writing-plans` → next slice (Garden notes, About, or homepage v3)

---

## 0. Context for future Claude sessions

If you are picking up this work, read in order:

1. Repo root `CLAUDE.md` — current architecture (post-rebuild).
2. The site design spec at `docs/superpowers/specs/2026-05-03-personal-site-design.md`, in particular §4.3, §4.4 (essay index + post), §5 (cross-cutting features), §10 (org-mode contract), §14 (phases).
3. This spec — narrows the §4.3/§4.4 surface to a buildable slice.
4. The implementation plan that follows this spec (will live at `docs/superpowers/plans/2026-05-05-essays-section.md`).

The brainstorm transcripts and visual mockups for this design are persisted under `.superpowers/brainstorm/` and gitignored. They will not be there in a fresh checkout.

---

## 1. Slice scope

This slice ships **the essays section**:

- `/essays/` index page with the variable-tile (Bento) grid + filter chips.
- `/essays/<slug>/` post layout with TOC, sidenotes, citations placeholder, code highlighting, footnotes, figures, tags, hero illustrations, series navigation, reading-time.
- Per-section RSS feed at `/essays/index.xml` and a header RSS button that targets the section feed when on `/essays/`.
- A homepage Essays strip (featured card + 3-column recent grid + "All essays →" link) that surfaces essays from the front page. Final homepage v3 wiring (Currently / Studio strips) stays in spec Phase 7; this slice contributes only the essays strip.
- Six fixture essays under `content/essays/<slug>/` with **filler bodies only** (lorem ipsum / "Example N"). No authored prose.
- A `data/citations.yaml` fixture file matching the eventual ox-hugo output shape (spec §10).
- One new automated CI gate: `tools/check-fixtures.py` that lints essay frontmatter + verifies cite keys.

This slice does **not** ship: Garden, Research, Works, About rewrite, Library, Pagefind search, Lighthouse CI, the homepage v3 final assembly, KaTeX, interactive widgets, scroll-synced video, spoiler-block runtime, citation hover-card, figure lightbox. Each is documented in §9 below with target phase.

## 2. Decisions captured during brainstorm

| # | Decision | Choice |
|---|---|---|
| 1 | Phase-2 slice scope | **A** — essays only (defer Garden + About) |
| 2 | Content strategy | **A** — committed fixture essays under `content/essays/` with explicit filler text |
| 3 | Capability scope (beyond spec-locked TOC/sidenotes/citations/code) | TOC, sidenotes, citations placeholder, code highlighting (locked) + **footnotes, figures (no lightbox), tags, hero illustrations, series nav** |
| 4 | Homepage essays strip | **A** — include featured + recent grid in this slice; final homepage wiring (Currently / Studio strips) stays in Phase 7 |
| 5 | Fixture set | **C** — six fixtures: featured large-with-hero, medium with code, minimal small, two-part series, figure-heavy |
| 6 | Filter chips | **All three** — tag, series, year |
| 7 | Per-section RSS, reading time, tile-grid auto-promotion, code-highlighting palette | RSS in; reading time in; auto-promotion (featured 2× wide / hero spans 2 rows / active series stays larger) all implemented; **Dracula palette kept as placeholder, deferred for revisit** |
| 8 | JavaScript architecture | **B** — one shared `assets/js/essay.js` module added to the existing bundle; no per-page bundle convention introduced |

Carrying preferences from prior memory:
- Fixture content uses obvious filler only (lorem ipsum / "Example N"), never authored prose.
- Deferred features must stay visible in plans AND be exercised by fixtures so they round-trip when implemented.
- Don't defer cheap items — the bar for deferral is real implementation cost or unresolved design questions.

## 3. Architecture

### 3.1 New + modified files

```
layouts/
├── essays/
│   ├── list.html               [NEW] /essays/ — variable-tile grid + filter chips
│   ├── single.html             [NEW] essay post — TOC, body, sidenotes, references
│   └── rss.xml                 [NEW] /essays/index.xml — per-section feed
├── partials/
│   ├── essay-card.html         [NEW] grid tile (used in list.html and homepage strip)
│   ├── essay-card-featured.html[NEW] large featured card variant
│   ├── essay-toc.html          [NEW] left-rail TOC, server-rendered
│   ├── essay-meta.html         [NEW] date · reading-time · tags · series pill
│   ├── essay-references.html   [NEW] citations list at end of post
│   ├── essay-series-nav.html   [NEW] prev/next + "Part N of M"
│   └── header.html             [MOD] RSS button → section feed when on /essays/
├── shortcodes/
│   ├── sidenote.html           [NEW] {{< sidenote >}} → marker + aside
│   ├── cite.html               [NEW] {{< cite key >}} → <cite> with data-cite-key
│   ├── figure.html             [NEW] override Hugo default; supports class="wide"
│   ├── spoiler.html            [NEW deferred-stub] <span data-spoiler> wrapper
│   ├── math.html               [NEW deferred-stub] <code data-math> wrapper
│   ├── video-sync.html         [NEW deferred-stub] <div data-video-sync>
│   └── widget.html             [NEW deferred-stub] <div data-widget>
└── _default/                   [unchanged]

assets/
├── css/main.css                [MOD] new sections: .essay-grid, .essay-card,
│                                     .essay-body, .toc, .sidenote, .references
└── js/
    ├── index.js                [MOD] import './essay.js'
    └── essay.js                [NEW] guarded by .essay-body; TOC scroll-spy
                                       + sidenote/footnote popups + cite hook

content/
├── _index.html                 [MOD] add Essays strip (featured + 3-col recent)
└── essays/
    ├── _index.md               [MOD] real section frontmatter + framing copy
    ├── example-essay-one/        [NEW fixture] large+featured, full chrome
    │   ├── index.md
    │   └── hero.svg
    ├── example-essay-two/index.md  [NEW fixture] medium, code-heavy + math filler
    ├── example-essay-three/index.md[NEW fixture] small, minimal + spoiler filler
    ├── example-series-part-1/      [NEW fixture] series, hero + video filler
    │   ├── index.md
    │   └── hero.svg
    ├── example-series-part-2/index.md  [NEW fixture] series, code + widget filler
    └── example-figures-essay/      [NEW fixture] figure-heavy
        ├── index.md
        └── fig-{1,2,3}.svg

data/
└── citations.yaml              [NEW] fixture bib entries — feeds cite shortcode

tools/
└── check-fixtures.py           [NEW] CI gate: frontmatter linter + cite key checker

.github/workflows/hugo.yaml     [MOD] add "Verify essay fixtures" step
```

### 3.2 Top-level decisions baked into the layout

- **Dedicated `layouts/essays/` directory.** Hugo picks up `essays/list.html` for `/essays/` and `essays/single.html` for any page under `content/essays/`. Keeps essay markup off `_default/`.
- **Fine-grained partials.** `essay-card`, `essay-toc`, `essay-meta`, `essay-references`, `essay-series-nav` each do one thing. The homepage strip and the index page reuse the same `essay-card` partials, so visual consistency is structural — not duplicated CSS.
- **Deferred features ship as no-op shortcodes** (`spoiler`, `math`, `video-sync`, `widget`). Fixtures use them; output is harmless. When the real renderer arrives in a later slice, the shortcode body is the only thing that changes.
- **`data/citations.yaml` is committed** as a fixture matching spec §10. The `cite` shortcode reads from it. The real ox-hugo exporter will overwrite this file with the same shape.
- **One shared `essay.js` module**, imported into the existing bundle. No per-page bundle convention introduced (open question 3 in the parent spec stays open).

## 4. Components

### 4.1 `layouts/essays/list.html` — index template

**Job:** render the variable-tile grid + filter strip + framing.

**Inputs:** all pages under `content/essays/` (Hugo `.Pages`), sorted by `.Date` reverse.

**Output structure:**

```html
<article class="essays-index">
  <header class="essays-hero">
    <h1>Essays</h1>
    <p class="framing">{{ .Content }}</p>  {{/* from _index.md body */}}
  </header>

  <nav class="filter-strip" aria-label="Filter essays">
    <span class="label">Tags</span>      {{/* chips: all + each tag */}}
    <span class="label">Series</span>    {{/* chips: all + each series */}}
    <span class="label">Year</span>      {{/* chips: all + each year (suppressed if 1) */}}
  </nav>

  <ul class="essay-grid" data-filter-state="all">
    {{ range .Pages }}
      {{ partial "essay-card.html" . }}
    {{ end }}
  </ul>
</article>
```

### 4.2 Tile-size resolution (auto-promotion rules)

The card partial computes tile size + span using this priority order:

1. Explicit `tile_size: large|medium|small` in frontmatter wins.
2. Else `featured: true` → `large`.
3. Else page in active series (most recent post in that series, computed across all essays) → `medium`.
4. Else `medium`.

Then `tile_span`:

- `featured: true` → `data-span="2x1"` (2 cols × 1 row).
- `hero` present → adds row span: `data-span="2x2"` if also featured, `data-span="1x2"` otherwise.
- Default → `data-span="1x1"`.

CSS reads `data-span` and assigns `grid-column: span N` / `grid-row: span N`.

### 4.3 `partials/essay-card.html` and `essay-card-featured.html`

- **Card fields:** hero (if any), title, summary (frontmatter `summary` or auto), meta line (date · reading-time · series-pill · tag chips).
- **Featured variant:** adds eyebrow text ("Featured" or series name).
- **Reuse:** same partials called from `essays/list.html`, `_index.html` (homepage strip), and `essay-series-nav.html` (prev/next mini-cards). One source of truth.

### 4.4 Filter chips

> **Updated 2026-05-08 by the garden-notes slice** — chips render via the shared `partials/filter-chips.html` partial (button elements only, no anchor fallback). Active state is per-dimension and AND-combined across dimensions. The earlier no-JS fallback to taxonomy pages and the single-active-across-dimensions rule no longer apply. Tag and series taxonomy pages still exist at `/tags/<slug>/` and `/series/<slug>/` for direct entry. See `docs/superpowers/specs/2026-05-07-garden-notes-design.md` §4.7 + memory `feedback_filter_chips_compose` for rationale.

- Each chip is a `<button>` with `data-dim` and `data-key`. Cards carry `data-tags`, `data-series`, `data-year` (year computed from `.Date.Format "2006"` at render time, no frontmatter field required). The shared `assets/js/filter-chips.js` module hides cards that fail the AND of all non-`all` filters (`hidden` attribute, not `display: none`).
- **No-JS behavior:** chips render but are inert; tag and series taxonomy pages remain reachable at `/tags/<slug>/` and `/series/<slug>/` via direct entry. There is no in-strip anchor fallback.
- **Per-dimension active state, AND-composed:** selecting a chip in one dimension does not affect chips in other dimensions; visibility is the intersection.
- **Suppression:** if a dimension has fewer than 2 distinct values, that dimension's chip strip is not rendered (avoids the single-value cosmetic "2026 (6)" button while only one year of content exists).

### 4.5 `layouts/essays/single.html` — post template

```html
<article class="essay" data-toc="{{ if not (eq .Params.toc false) }}true{{ end }}">
  <header class="essay-header">
    {{ with .Params.hero }}<img class="hero" src="{{ . }}" alt="">{{ end }}
    {{ partial "essay-meta.html" . }}     {{/* date · reading-time · tags · series pill */}}
    <h1>{{ .Title }}</h1>
    {{ with .Params.summary }}<p class="lede">{{ . }}</p>{{ end }}
  </header>

  {{ if not (eq .Params.toc false) }}
    {{ partial "essay-toc.html" . }}      {{/* left rail; sticky on wide */}}
  {{ end }}

  <div class="essay-body">
    {{ .Content }}                        {{/* markdown body, shortcodes resolved */}}
  </div>

  {{ if .Params.has_citations }}
    {{ partial "essay-references.html" . }}
  {{ end }}

  {{ if .Params.series }}
    {{ partial "essay-series-nav.html" . }}
  {{ end }}
</article>
```

**Three-zone layout** (CSS): TOC rail (left, ~200px) | reading column (center, max ~720px) | sidenote rail (right, ~250px). Below 1024px viewport, TOC collapses to a "Contents" disclosure at the top of the post; sidenotes inline as numbered popups.

### 4.6 `partials/essay-toc.html`

Server-rendered from Hugo's `.TableOfContents` (`markup.tableOfContents.startLevel: 2, endLevel: 6` is already in `hugo.yaml`). Static HTML works without JS. `essay.js` attaches an `IntersectionObserver` on H2/H3 to mark the active section as you scroll. Clicks smooth-scroll. `aria-current="location"` on the active item.

### 4.7 Sidenote shortcode

`{{< sidenote >}}…{{< /sidenote >}}` renders to:

```html
<span class="sidenote-marker" tabindex="0" aria-controls="sn-3">3</span>
<aside class="sidenote" id="sn-3">3. (body)</aside>
```

- **Wide viewport:** aside floats into the right rail at marker height.
- **Narrow viewport:** aside hidden until marker is clicked/focused → opens popup card anchored to marker (handled by `essay.js`).
- Auto-numbering via Hugo `scratch`.
- Forbidden inside code blocks: shortcode calls `errorf` if rendered within a `<code>`/`<pre>` ancestor.

### 4.8 Cite shortcode + references partial

- `{{< cite "key" >}}` reads `site.Data.citations.citations[key]`, emits `<cite class="citation" data-cite-key="key">[Author 2020]</cite>` with anchor jump to the references list.
- `essay-references.html` walks the page's used keys (collected via Hugo scratch in the `cite` shortcode) and emits the references list at the end of the post.
- **Hover-card behavior is deferred.** The `data-cite-key` hook is in place so the Phase 3 hover-card can attach without changing markup.

### 4.9 Figure shortcode

`{{< figure src caption alt class >}}` overrides Hugo's default. Emits semantic `<figure><img><figcaption>`. Supports `class="wide"` for breakout figures that exceed the reading column (capped at 920px via `--reading-wide` token). No lightbox in this slice (deferred).

### 4.10 Deferred-feature shortcodes (no-op stubs)

- `{{< spoiler >}}…{{< /spoiler >}}` → `<span data-spoiler>(body)</span>`. CSS does nothing yet; later it'll become click-to-reveal.
- `{{< math >}}$\alpha + \beta${{< /math >}}` → `<code data-math>(body)</code>`. Renders raw TeX as inline code; KaTeX fills it in later.
- `{{< video-sync src >}}` → `<div data-video-sync data-src="…"></div>`. Empty container; later JS attaches.
- `{{< widget id >}}` → `<div data-widget data-widget-id="id"></div>`. Empty container; later per-page JS attaches.

Each stub is one-line Hugo template emitting its container with the data-attribute hook. Fixtures use them. Output renders as either invisible (empty divs) or harmless inline text.

### 4.11 `assets/js/essay.js`

Imported by `assets/js/index.js`. Guards: returns immediately if `document.querySelector('.essay-body')` is null. Then:

- **TOC scroll-spy:** `IntersectionObserver` watches `h2, h3` in `.essay-body`; marks the matching TOC link with `aria-current="location"`.
- **Sidenote & footnote popups:** on viewports below the rail breakpoint, click/focus on a marker opens a positioned popup card; click outside / `Esc` closes. Same component handles markdown footnote markers (Hugo emits them with predictable IDs).
- **Citation hook:** registers a hover/focus listener on `[data-cite-key]` elements that's currently a no-op (placeholder for Phase 3 hover-card).
- **Reduced motion:** respects `prefers-reduced-motion: reduce` — skips smooth-scroll, sets `scroll-behavior: auto`.

Estimated bundle delta: ~3–4 KB minified.

## 5. Data flow

### 5.1 Frontmatter contract

Mirrors spec §10 ox-hugo output. Fixture frontmatter follows this exact shape so when the real exporter arrives, layouts don't change.

```yaml
---
title: "Example essay one"
date: 2026-04-12
lastmod: 2026-04-20
draft: false
summary: "Lorem ipsum dolor sit amet…"
tags: ["example-tag-a", "example-tag-b"]
series: ""                         # "" or "example-series"
series_order: 0                    # 0 if not in a series

# Tile / promotion
tile_size: large                   # large | medium | small | (omit)
featured: true                     # true | (omit)
hero: hero.svg                     # filename in page bundle | (omit)

# Capability flags (each gates its component or shortcode)
toc: true                          # default true; set false to suppress
has_sidenotes: true                # advisory; rail renders only if used
has_citations: true                # gates the references partial
has_footnotes: true                # advisory
has_math: false                    # deferred — flag still recorded
has_widgets: false                 # deferred — flag still recorded
has_video_sync: false              # deferred — flag still recorded
---
```

The `tools/check-fixtures.py` linter enforces:
- Required fields present.
- `tile_size` ∈ allowed enum.
- `series_order > 0` when `series` is set.
- `hero` file exists in page bundle when declared.
- `lastmod >= date`.
- All cite keys referenced in body exist in `data/citations.yaml`.

### 5.2 `data/citations.yaml` shape

```yaml
citations:
  example-source-1:
    authors: ["Lastname, F.", "Othername, G."]
    year: 2020
    title: "Lorem ipsum dolor sit amet"
    venue: "Journal of Examples"
    url: "https://example.invalid/1"
    notes_ref: ""                  # slug of garden note if user has notes on it
  example-source-2:
    authors: ["Author, A."]
    year: 2024
    title: "Consectetur adipiscing elit"
    venue: "Proceedings of Things"
    url: "https://example.invalid/2"
    notes_ref: "example-note-slug"
```

Cite flow: `{{< cite "example-source-1" >}}` in fixture body → `cite.html` shortcode reads `site.Data.citations.citations.example-source-1` → emits inline `<cite>[Lastname & Othername 2020]</cite>` with `data-cite-key` and jump anchor → `essay-references.html` walks used keys (collected via scratch) and emits the references list at end-of-post.

### 5.3 Taxonomies

```
hugo.yaml taxonomies:
  tag: tags
  series: series
```

Tag and series are real Hugo taxonomies. Hugo auto-generates `/tags/<slug>/` and `/series/<slug>/` pages, which serve as the no-JS fallback for those filter chips.

**Year is NOT a taxonomy.** Year filter is computed at render time in `list.html` from each page's `.Date.Format "2006"`, written to the card as `data-year`, and filtered client-side via `essay.js`. Rationale: keeps frontmatter aligned with spec §10 (no extra `years:` field beyond what ox-hugo emits) and avoids needing a pre-build step to populate a synthetic taxonomy. Tradeoff: year filter has no no-JS URL fallback — see §4.4.

### 5.4 RSS section feed

`layouts/essays/rss.xml` is a section-scoped Hugo RSS template. `/essays/index.xml` is generated automatically. The header partial picks the section feed when `strings.HasPrefix .RelPermalink "/essays/"`, otherwise the site-wide feed. Same logic generalizes to Garden/Research/Works in later slices.

### 5.5 Homepage Essays strip

- **Featured essay:** first essay (most recent by date) where `featured: true`; falls back to most recent essay overall if none has the flag.
- **Recent grid:** the next three essays after the featured one, by date.
- Both reuse the same `essay-card` / `essay-card-featured` partials as the index.
- "All essays →" link goes to `/essays/`.

### 5.6 Phase 3 handoff (no layout changes when real content arrives)

- **Frontmatter:** ox-hugo emits the same fields. Fixtures get overwritten by the export; no template change.
- **Citations:** ox-hugo emits `data/citations.yaml` in the same shape. `cite` shortcode is unchanged.
- **Hero illustrations:** exporter places SVG in the page bundle next to `index.md`. Same path as fixtures.
- **Deferred shortcodes:** when KaTeX/widgets/video-sync land in later slices, only the shortcode body changes — fixture content and post markup are unchanged.

## 6. Error handling & edge cases

### 6.1 Build-time failures (must block deploy)

| # | Scenario | Handling |
|---|---|---|
| 1 | Required frontmatter missing | `tools/check-fixtures.py` fails CI |
| 2 | Citation key not in `citations.yaml` | `cite.html` calls `errorf`; Hugo build aborts |
| 3 | Hero file declared but absent | `single.html` uses `resources.Get` with nil-check; declared-but-missing → `errorf`, fail |
| 4 | Series declared but `series_order = 0` | linter flag |
| 5 | Sidenote inside a code block | `sidenote.html` calls `errorf` if `<code>`/`<pre>` ancestor detected |

### 6.2 Build-time tolerable warnings

| # | Scenario | Handling |
|---|---|---|
| 6 | Empty `/essays/` section | `list.html` renders hero + "No essays yet." block |
| 7 | Filter dimension with < 2 values | dimension's chip strip suppressed (year strip suppressed when only 2026 fixtures exist) |
| 8 | Tag with zero matches after filter | chip rendered with `(0)` count, disabled style |

### 6.3 Runtime / progressive enhancement

| # | Scenario | Handling |
|---|---|---|
| 9 | JS disabled | TOC clicks = anchor jumps; sidenotes inline below marker via CSS; footnote/cite jumps are anchors; tag + series chips link to taxonomy pages; year chips inert |
| 10 | `prefers-reduced-motion: reduce` | `essay.js` skips smooth-scroll; CSS suppresses scroll-snap and transitions |
| 11 | Theme switch mid-scroll | `IntersectionObserver` state unaffected; `data-theme` change does not reflow `.essay-body` |

### 6.4 Layout edge cases

| # | Scenario | Handling |
|---|---|---|
| 12 | Sidenote longer than rail height | CSS `max-height` + `overflow-y: auto`; pop-out-on-hover variant |
| 13 | Long card title (3+ lines) | CSS `line-clamp: 3` with ellipsis; full title in `title` attr |
| 14 | Series with one item | series-nav renders "Part 1 of 1" with no prev/next |
| 15 | Featured + hero on same post | resolved by span rules (`2x2`); exercised by fixture #1 |
| 16 | Wide figure exceeds reading column | `class="wide"` uses negative margin; capped at 920px via `--reading-wide` |
| 17 | Mobile horizontal overflow | reading column `max-width: calc(100vw - 2rem)`; sidenote rail becomes popups |

### 6.5 Out of error-handling scope

- Print stylesheet (deferred to polish phase).
- Citation hover-card runtime errors (no hover-card yet).
- Math / widget / video-sync runtime errors (renderers don't exist yet).
- Pagefind index errors (Phase 8).
- Lighthouse / smoke-test CI (Phase 8).

## 7. Testing & verification

### 7.1 Automated CI gates (must pass to deploy)

1. **`tools/check-contrast.py`** — existing. Palette unchanged but verify; new components reuse existing tokens.
2. **`tools/check-fixtures.py`** — NEW. Walks `content/essays/*/index.md`:
   - Required fields present.
   - `tile_size` ∈ allowed enum.
   - If `series` set, `series_order > 0`.
   - Hero file exists when declared.
   - `lastmod >= date`.
   - All cite keys used in body exist in `data/citations.yaml`.
3. **`hugo --minify`** — implicit. Shortcode `errorf` calls (missing cite key, sidenote-in-code, etc.) abort the build.

The new `check-fixtures.py` sits alongside `check-contrast.py` in `.github/workflows/hugo.yaml`, between "Setup Pages" and "Build with Hugo." Same shape: zero exit on success, nonzero with line-numbered error on failure.

### 7.2 Manual walkthrough checklist

The implementation plan's final step is a top-to-bottom walkthrough against `hugo server`. The plan will include the full checklist; abbreviated here:

- **Layout / visual:** all six fixtures render; Bento grid matches projected diagram; tile-size + hero promotion correct; three-zone layout > 1024px; single-column ≤ 1024px; long titles line-clamp.
- **Capabilities:** TOC scroll-spy + smooth-scroll; sidenote rail wide / popup narrow; footnote popup narrow; citation jumps + `data-cite-key` present; code highlighting renders for 3 languages; figure renders with caption + `wide` breakout; series prev/next; tag chip → `/tags/<slug>/`; reading time matches `.ReadingTime`.
- **Filter chips:** tag/series filter the grid; year chip strip suppressed (single value, while only 2026 fixtures exist); "All" resets; JS-off → tag and series chips link to taxonomy pages, year chips inert.
- **Themes & a11y:** light, dark, system; tab order logical; focus ring visible; `aria-current="page"` on top-nav; `aria-current="location"` on TOC; reduced-motion disables transitions; JS-off degrades as documented.
- **Homepage strip:** featured matches expected fixture; 3 recents in correct order; "All essays →" resolves.
- **RSS:** `/essays/index.xml` validates (W3C feed validator); header RSS button targets section feed when on `/essays/`.
- **Deferred-feature stubs:** `spoiler`, `math`, `video-sync`, `widget` shortcodes all render harmlessly; no JS errors in console.

### 7.3 Out of testing scope

- Lighthouse / Web Vitals CI (Phase 8).
- Pagefind index validation (Phase 8).
- Cross-browser matrix beyond Chrome + Firefox local (Phase 8 audit).
- Screen-reader recorded walkthrough (Phase 8 audit).

## 8. Fixture set

Six committed fixture posts. All bodies are lorem ipsum / "Example N" filler. Variety exercises the layout surface and seeds deferred features.

| # | Slug | Tile | Hero? | Capabilities exercised | Deferred-feature filler |
|---|---|---|---|---|---|
| 1 | `example-essay-one` | large + featured (2× wide, 2 rows) | yes | TOC (5 H2s), sidenotes (×3), citations placeholder (×2), footnotes (×2), figures (×2), tags (×3), reading-time | — |
| 2 | `example-essay-two` | medium | no | code highlighting (3 languages), footnotes, tags | KaTeX math expression (renders raw for now) |
| 3 | `example-essay-three` | small | no | plain prose only — minimal essay | spoiler block (renders as plain text wrapper) |
| 4 | `example-series-part-1` | medium (auto-promoted: active series) | yes | series nav, TOC, citations, tags | video-sync shortcode (renders as empty `<div>`) |
| 5 | `example-series-part-2` | medium (auto-promoted: active series) | no | series nav (back to part 1), code highlighting, footnotes | widget shortcode (renders as empty `<div>`) |
| 6 | `example-figures-essay` | medium with hero (1×2) | yes | figures (×3 incl. one `wide` breakout), captions, tags | — |

All fixtures have `draft: false` so they ship with the site. Titles are *"Example essay one"* / *"Example figures essay"* — never invented topic-flavored titles.

## 9. Deferred features (must stay in plan)

The following capabilities are explicitly out of this slice but kept visible:

| Capability | Target slice | Fixture seeded? |
|---|---|---|
| Spoiler block runtime (click-to-reveal CSS) | Phase 4 (Garden interaction model) — Garden uses spoilers more | Yes — fixture #3 |
| KaTeX math rendering | Later — gated on author-side need | Yes — fixture #2 |
| Scroll-synced video runtime | Later — gated on author-side need | Yes — fixture #4 |
| Per-page interactive widgets + per-page JS bundle convention (open Q3) | Later — design when first widget exists | Yes — fixture #5 |
| Figure lightbox | Polish phase | No — fixtures use figures but no lightbox filler |
| Citation hover-card runtime | Phase 3 (Org-mode pipeline) | Yes — `data-cite-key` hooks present in all citation fixtures |
| Code highlighting palette swap from Dracula | Post-Phase-2, before Phase 6 (Works/games) | N/A — keeps current Dracula |
| Multi-dimension filter combination (tag AND year) | Later — gated on whether user wants it | N/A — single-dimension v1 |
| Print stylesheet | Phase 8 polish | N/A |

Implementation plan must reproduce this table verbatim and confirm each row at the end of the slice.

## 10. Out of slice

Sections of the parent spec NOT touched by this slice:

- Garden notes, Garden index, topic maps, graph view, stacked-column retrieval (spec §4.5–4.9).
- Research themes, question hubs, research graph (§4.10–4.13).
- Works (games, music, poetry) (§4.14+).
- Library (reading / listening / playing).
- About page rewrite + Now widget.
- Homepage v3 final assembly (Currently strip, Studio strip, Garden+Studio columns) — only the Essays strip is added.
- Pagefind search.
- Lighthouse / Web Vitals CI gates.

## 11. Open questions inherited from parent spec

This slice does not resolve any of parent-spec §15's open questions. Specifically:

- **Open Q3 (per-page bundle JS convention)** stays open. Resolved when the first interactive widget arrives.
- **Open Q5 (inline spoiler markup convention)** stays open. The `{{< spoiler >}}` shortcode is the working markup; the org-side syntax (`~text~` vs org macro) will be settled in Phase 3 when ox-hugo emits the spoiler shortcode.

## 12. Pointers

- Parent spec: `docs/superpowers/specs/2026-05-03-personal-site-design.md`.
- Phase 0+1 plan: `docs/superpowers/plans/2026-05-04-foundation-and-visual-identity.md`.
- This spec: `docs/superpowers/specs/2026-05-05-essays-section-design.md`.
- Implementation plan (next): will live at `docs/superpowers/plans/2026-05-05-essays-section.md`.
- Repo `CLAUDE.md` for current architecture.
- Brainstorm artifacts (mockups, transcripts) under `.superpowers/brainstorm/` — gitignored, not in fresh checkouts.
