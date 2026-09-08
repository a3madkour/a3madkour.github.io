# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Personal website for Abdelrahman Madkour, built as a Hugo static site with hand-rolled CSS and deployed to GitHub Pages. Long-form essays are the centerpiece, supported by a Zettelkasten-style knowledge garden, research surface, and creative output (games / music / poetry). All content authored in org-mode + org-roam, exported via ox-hugo.

## Commands

- `hugo server --buildDrafts` — dev server with drafts visible.
- `hugo --minify` — production build to `public/`. **Do not run with a dev server alive**; it poisons the dev-server CSS via a MIME mismatch.
- `python3 tools/check-contrast.py` — WCAG 2.1 contrast verifier (CI gate).
- Thirty-eight linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): dark-mode token equality, CSS class referential integrity, essay fixtures, essay TOC depth, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, math frontmatter coupling, works fixtures, works links, synced poetry, library fixtures, library links, library covers, library shelves, icon attribution, RSS XSL, garden history, streams fixtures, streams links, pagefind metadata, cite metadata, page weights, LHCI URL resolution, org-asset references, anchor-link affordance, html links, spacing tokens, breakpoints, explorables, recipe fixtures, recipe links, search sections, image ladder, meta description. `tools/check_smoke.py` and `tools/check_graph_chrome.py` are sibling-less linters (no paired test file — spec §3.1: logic is too thin to warrant pairing). `check_html_links.py` crawls the rendered `public/` for broken internal `<a href>` targets + fragment anchors (a post-build sibling of `check_smoke`/`check_anchor_link`), distinct from the frontmatter `check_*_links.py`. `check_image_ladder.py` pins `schema-recipe.html`'s three-branch `image` resolution to the identical branch keys in `check_recipes_links.py`: when the two drift, the linter certifies a value the template mangles into a broken JSON-LD URL that nothing else can see (`image` is never rendered as an `<img>`, so the built-HTML crawler never visits it). That drift shipped once and survived a first review. `check_meta_description.py` guards a surface that is invisible locally and public everywhere else: Hugo's `.Summary` is *rendered HTML* when a page declares no explicit summary, so without `plainify` the page's whole first section lands in `<meta name=description>` and `og:description` — which is what a search snippet or a social card then shows. 18 pages shipped that way. `check_search_sections.py` is a second post-build pair: it extracts every `section:<value>` the built HTML emits and asserts each appears in both `SECTION_ORDER` and `SECTION_LABEL` in `assets/js/search.js`. A section the site emits but the array omits is counted by the status line and then dropped from the results pane — invisible in the UI, and shipped twice before this guard existed (once for `recipes`, once for `tags`/`series`/`credits`/`blog`). The 5 test files that duplicated a full `TempRepo` class now share `tools/test_helpers.py` (`TempRepo`); the rest use lighter inline `setUp` tempdirs, left as-is (R5.4). Every linter exposes a uniform `run(...) -> (int, list[str])` seam + a thin `main()` — the param is `repo_root` for most (`check_anchor_link` / `check_html_links` / `check_lhci_urls` take `public`/config paths). `tools/test_test_helpers.py` is a self-test for the shared helper (not a linter pair — there is no corresponding `check_*.py`).
- `npx playwright test` — dev-only Playwright E2E smoke suite (10 spec files, 32 tests under `tests/e2e/`: `core` 3 — homepage brand + no-js + nav single-row below 960px; `theme` 1; `filter-chips` 1; `search` 2 — listbox keyboard + the recipes filter returning results; `cite` 1; `graph`/`research-graph`/`works-graph` 1 each; `math` 4; `recipes` 17 — render + scale, download target, index card count, group inheritance, `Serves` label focus, collapsed steps column, server render authoritative at rest, no write at load, no time chrome when times are absent, a focus ring on every scaler control, both scaler inputs honouring their own declared bounds, index heading order, the two-channel rescale signal, the live region present at load, the pluralised committed-yield announcement, the no-JS scaler fallback, and the optional kicker rendering only when cuisine or category is present). Runs in CI after the Pagefind index build; gates deploy. Mirrored in `tools/ci-local.sh` (loud-skips if Node is absent). The three graph-mount specs are the behavioral safety net for the R5.2 graph-core extraction.
- `node --no-experimental-detect-module --test tests/unit/*.test.mjs` — JS unit layer for pure client-side logic (currently covers `recipe-scale.js` quantity scaling). Lives under `tests/unit/`; does not require a running server. `package.json` declares `"type": "module"` (and `engines.node >= 20`); CI and `tools/ci-local.sh` both pass `--no-experimental-detect-module` so the Node-20 module semantics CI actually runs under are exercised regardless of the local runtime — without it a newer local Node auto-detects ESM and hides a resolution failure.

No npm **for the shipped site** — Python tooling is stdlib-only and nothing in `assets/` requires a Node build. The **sole exception is a dev-only Node test layer** (`package.json` devDependencies only, `node_modules/` gitignored): `npx playwright test` drives real Chromium over the built `public/` for the 32-test smoke suite under `tests/e2e/`; `node --no-experimental-detect-module --test tests/unit/*.test.mjs` runs the pure-JS unit layer (8 tests in 1 file, `tests/unit/recipe-scale.test.mjs`; no server required). It does not ship and adds zero bytes to any page. Hugo **extended** (≥ 0.162.1) is required — `.github/workflows/hugo.yaml` pins `HUGO_VERSION=0.162.1`. (Hugo 0.162+ tightened the default `security.allowContent` policy to deny `text/html` source files; this site avoids the issue by using `_index.md` rather than `_index.html` for the homepage.)

## Architecture

### CSS pipeline — hand-rolled, processed by Hugo

`assets/css/main.css` is a single hand-rolled stylesheet, organized into numbered sections §1–§51 (see the file's top-of-file index for the list; §32–§36 are reserved for past works-section additions that landed without numbered headers; §38–§40 cover the homepage hero, Currently widget, and homepage strips; §41 covers the cross-template page sidebar; §42 covers the search modal; §43 covers citation export; §44 covers the library umbrella redesign — hero + themed shelves + bottom catalogue; §45 covers the synced-poetry runtime (reveal opacity/flourish + JS-built player chrome); §46 covers the streams section — header live-pill, click-to-load YouTube embed, archive grid, upcoming strip, cross-section from-stream attribution, category pill palette; §49 covers the explorables runtime — slider cross-browser chrome, reactive-output, hand-rolled SVG chart, widget-fallback; §50 covers the math (KaTeX) overrides; §51 covers the recipes section — two-column reading layout (sticky ingredients rail + steps column, collapsing to one column at 720px), scaler chrome, and the index card grid; the stepper carries no `overflow`, so the `:focus-visible` ring on all four scaler controls paints unclipped). Consumed by `layouts/partials/head.html` via `resources.Get` + (production) `minify | fingerprint` with SRI integrity.

- **Tokens** are CSS custom properties on `:root` (light) and `:root[data-theme="dark"]` (dark). System dark via `@media (prefers-color-scheme: dark) :root:not([data-theme])`. The `[data-theme="dark"]` block and the media-query block carry **duplicate values** — both must be updated together when the palette changes. Spacing uses a 12-step `--space-*` scale (§2, `:root` only — mode-independent, not duplicated in the dark blocks); `tools/check_spacing_tokens.py` guards it. Breakpoints follow a documented canonical scale (`480/600/720/960/1100/1280`) — a top-of-file comment + `tools/check_breakpoints.py`, not runtime tokens (CSS `@media` can't read `var()`); JS breakpoint constants are enforced against the same scale.
- **WCAG contrast**: `tools/check-contrast.py` parses the `:root` blocks and verifies twenty-one pairings in both modes — ink/stone AAA and ink/tile AAA; everything else AA. Four background surfaces are gated, not one, because a token that clears the page background can still fail on a panel: **on `--color-stone`** (page) ink-soft, burgundy, steel, the three greens, warn, and ink-fade; **on `--color-tile`** (grid-item *and* recipe-rail surface) burgundy and ink-fade; **on `--color-paper`** (floating-panel surface) ink, ink-soft and burgundy; **on `--color-burgundy`** (accent used as a fill, not just as text) stone, tile and paper. The inverse pairs are gated deliberately: `stone/warn` for the queued pill, and `stone/burgundy` + `tile/burgundy` because burgundy carries text *on* it as often as it carries text *in* it — checking only one direction let a white-on-burgundy regression through. The three green stops are the garden stage-glyph ramp (evergreen / budding / seedling); `--color-ink-fade` is the de-emphasised meta / ingredient-qualifier stop, which is why it is gated against both surfaces. Failure blocks deploy. `--color-rss` and `--color-live` are gated at **3.0**, not 4.5, because both are graphical objects under SC 1.4.11 rather than text — the only sub-4.5 entries. Each clears its bar with headroom rather than sitting on it (RSS 4.12 light / 6.47 dark; live dot 5.74 / 3.69). The live dot is `aria-hidden` beside a visible LIVE label, so 1.4.11 does not strictly bind it; it is gated anyway because an indicator at 2.66:1 is one nobody can see, and because tokenizing it removed the last untokenized foreground literal in the stylesheet. Token `--color-paper` (floating panel surface — search modal, cite modal, path-log popover, recipe stepper field; light `#fdfcf8`, dark `#2a2a2a`; semantically distinct from `--color-tile`) is gated in its own right, not by value-coincidence: it happens to share `--color-tile`'s value today, and until 2026-09-07 that coincidence was the *only* reason its surfaces were covered — nudging either token would have dropped paper out of the gate with no failure anywhere. Gating it directly is what lets the two diverge safely.
- **No Tailwind, no PostCSS, no Node.** Class names are semantic. **One exception**: `assets/css/katex.css` is a second, vendored (not hand-rolled), conditionally-loaded stylesheet — self-hosted KaTeX CSS shipped alongside `static/fonts/katex/*.woff2`, loaded via a `<head>` link gated on `.Params.has_math` (essays only), separate from `main.css`'s single-bundle pipeline. See Math pipeline below.

### JS pipeline — multi-entry bundling

`layouts/partials/scripts.html` runs Hugo's `js.Build` (esbuild) thirteen fixed times + a dynamic per-essay loop — minified + fingerprinted, classic-script with SRI:

| Entry | Output | Loaded on | Notes |
|---|---|---|---|
| `js/index.js` | `core.<hash>.js` (~1.4 KB) | every page | `toggle-theme.js` + `nav.js` |
| `js/entry-anchor-link.js` | `anchor-link.<hash>.js` (~1 KB) | every page | `anchor-link.js` — click-to-clipboard §-glyph runtime; self-guards on `<main>` presence (shipped 2026-06-07 with Tier 2.1 anchor-affordance) |
| `js/entry-essay.js` | `essay.<hash>.js` (~4.8 KB) | `.Section == "essays"` | imports `filter-chips.js` + `citation-card.js` |
| `js/entry-garden.js` | `garden.<hash>.js` (~117 KB) | `.Section == "garden"` | `garden.js` + `garden-stack.js` + `garden-graph.js` (adapter over `graph-core.js`) + ~95 KB vendored d3 modules |
| `js/entry-research.js` | `research.<hash>.js` (~107 KB) | `/research/` and `/research/graph/` only | `research-graph.js` (adapter over `graph-core.js`); page-narrow predicate over section-wide |
| `js/entry-works.js` | `works.<hash>.js` (~4 KB) | `.Section == "works"` AND NOT `/works/`-or-`/works/graph/` | imports `filter-chips.js`; per-item pages only |
| `js/entry-works-umbrella.js` | `works-umbrella.<hash>.js` (~112 KB) | `/works/` and `/works/graph/` only | `works.js` + `works-graph.js` (adapter over `graph-core.js`) + vendored d3 modules |
| `js/entry-library.js` | `library.<hash>.js` (~5 KB) | `.Section == "library"` | imports `filter-chips.js` + `library-shelf-nav.js`; per-leaf pages AND umbrella |
| `js/entry-search.js` | `search.<hash>.js` (~4 KB) | every page | search modal open/close logic; lazy-loads `/pagefind/pagefind.js` on first open |
| `js/entry-cite.js` | `cite.<hash>.js` (~2.5 KB) | `.Section in {essays, garden, research, works}` AND `.Kind == "page"` | `cite.js` — citation modal runtime (parse #cite-data blob, open `<dialog>`, tab/copy/download, Half B inline copy) |
| `js/entry-poetry.js` | `poetry.<hash>.js` (~4 KB) | `.Section == "works"` AND `.Kind == "page"` AND `.Type == "works-poetry"` | `poem-synced.js` — synced-reveal runtime; JS-built player |
| `js/entry-streams.js` | `streams.<hash>.js` (~1 KB) | `.Section == "streams"` | `streams.js` — click-to-load YouTube embed + filter-chip setup on the /streams/ section index |
| `js/entry-recipes.js` | `recipes.<hash>.js` | `.Section == "recipes"` | `recipe-scale.js` (unit-aware quantity scaler) + `filter-chips.js`; handles both single-page rail binding and index filter chips. The server render is authoritative at rest: `initScaler` only binds listeners — it performs zero DOM writes at load, and the authored quantity strings are captured up-front so returning to ratio 1 restores them verbatim instead of round-tripping through the formatter. Both the `Serves` and multiplier inputs clamp through one `normalize()` against *both* controls' declared bounds, with the clamped value written back on `change` (not `input`, which would fight the caret). |
| `js/explorables/<slug>/index.js` (dynamic, per-essay) | `explorables-<slug>.<hash>.js` (~few KB) | `.Section == "essays"` AND `.Kind == "page"` AND `.Params.has_widgets` | per-essay; inlines runtime + lib kinds; spec at `docs/superpowers/specs/2026-06-12-sub-project-e-explorables-design.md` |

**Why multi-entry, not `splitting: true`?** esbuild requires `outdir` for code splitting, but Hugo's `js.Build` is `outfile`-only. `splitting: true` on a single entry silently inlines dynamic imports rather than emitting chunks. Confirmed with a minimal repro. `filter-chips.js` is duplicated into essay/garden/works bundles (~8 KB).

**Shared graph runtime (`assets/js/graph-core.js`, R5.2).** The three force-directed graphs share one core: `graph-core.js` exports `createGraph(adapter)` and owns all the infrastructure (cache/drag/zoom/settle loop/SVG scaffold/panel open-close on `inert`/panel-resize/chip primitives), parameterized by the adapter's `classPrefix`. `garden-graph.js` / `research-graph.js` / `works-graph.js` are thin adapters supplying the divergent surface — `parseData` / `applyFilters` / `filterCacheKey` / `nodeRadius` / `renderNode` / `edgeClass` / `svgAria` / `forceParams` / `onNodeClick` / `buildToolbar` plus optional `onSvgCreate` / `onRenderComplete` / `onOpenPanel` hooks. Garden-only features (stack-coordination, N-hop local mode, dynamic JS legend) live entirely in garden's adapter via those hooks; works was normalized to the garden/research conventions (JS-built toolbar, `inert` panel, `<div>` canvas). **`graph-core.js` must stay at `assets/js/` depth** — its `./vendor/d3-*` dynamic import is relative to the compiled bundle. The per-section node base class is emitted as `` `${classPrefix}-graph-node` `` (allowlisted in `tools/css-refs-allowlist.txt` since the static scan can't see the leading interpolation).

d3-force / d3-zoom / d3-drag / d3-selection are **vendored** under `assets/js/vendor/` (no npm). `graph-core.js` dynamically imports all four — they inline into each graph bundle (garden / research / works-umbrella); the core source is bundled into each entry (source-level share, like `filter-chips.js`). The three graphs share CSS scaffolding (§27). Each page module guards on its own selector and bails on irrelevant pages.

### Theme toggle

Three-state cycle: **system → light → dark → system**.

- Storage key: `theme-pref` in `localStorage` (absent = system mode).
- CSS responds to a `data-theme` attribute on `<html>`.
- An inline `<script>` at the top of `<head>` reads `theme-pref` synchronously during HTML parse and applies `data-theme` before any rendering — prevents FOUC. Storage access is wrapped in `try/catch` so restricted contexts (private browsing strict, sandboxed iframes) degrade gracefully.
- Bundled `toggle-theme.js` handles the click cycle, button label updates, and idempotent re-apply.

### Search modal

`layouts/partials/search-modal.html` is included once from `baseof.html`. It renders a `<dialog>` element that opens via the header magnifier button or the `/` key. On first open, `entry-search.js` lazy-loads `/pagefind/pagefind.js` from the CI-built Pagefind index (never bundled; always served from `public/pagefind/`). Section filter chips (All / Essays / Garden / Research / Works / Library / Recipes) map to `data-pagefind-filter="section:<name>"` values emitted by per-layout templates.

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
| Recipes | `recipes` | `cuisine`, `category` |
| About / Home / Blog (legacy) | section name only | — |

**Indexing controls**: `<main data-pagefind-body>` in `baseof.html` scopes the indexed body. `data-pagefind-ignore` on `.spoiler-body` (in `spoiler` shortcode) excludes spoiler content from the index.

### Math pipeline

Math content is authored in org-mode and validated **before publish**, not after.

1. **`org-math-lint` (pre-publish, dotfiles)** — runs against org source files; tokenizes, applies a 10-rule registry (delimiters, fragmented math, unicode → LaTeX, unknown commands), verifies each fragment by parsing it with vendored KaTeX in V8 via `py-mini-racer`. Source: `~/org/notes/tools/org-math-lint/` (not in this repo). Invoked by `a3-pub.sh` (default on; opt out via `--skip-math-check`).
2. **B.4 essays handler `has_math` scanner (dotfiles)** — buffer scan for math markers (`{{< math >}}`, `\(`, `\[`, `\begin{…}`) excluding fenced code blocks; sets emitted `has_math` frontmatter. `#+HUGO_HAS_MATH:` keyword acts as manual override when present. (Note: the site-side `check_math.py` deliberately recognizes a narrower, render-matched set — no bare `\begin{}` — so it can catch a `has_math` that B.4 set for content that won't actually render.)
3. **`tools/check_math.py` (site CI, 25th linter pair)** — two invariants, both mirroring what actually renders (detection requires **matched** delimiter pairs, so unpaired look-alikes like the poems' `\[00:99]` timestamps don't trip it): (a) **coupling** — every essay's `has_math` value must match whether the body contains rendered-math markers (`\(...\)`, `\[...\]`, `{{< math >}}`; `$$`/`$`/bare `\begin{}` are deliberately not markers — none are enabled passthrough delimiters); (b) **scope** — fails CI if any rendered-math marker appears outside `content/essays/` (`SCOPE_SKIP`), since the KaTeX CSS is essays-only and non-essay math would ship unstyled. Catches publish bugs the source-side validator can't see.
4. **KaTeX runtime — build-time, server-side.** Math renders during `hugo --minify` via Hugo's native `transform.ToMath` (embedded KaTeX). Body math: bare `\(...\)` / `\[...\]` anywhere in essay content is handled by the goldmark `passthrough` extension + `layouts/_default/_markup/render-passthrough.html`. Nested math: also bare — the 11 numbered AMS-block shortcodes (`ams-block.html`) and `proof.html` pipe their `.Inner` through `markdownify`, which re-runs goldmark (including passthrough) over the nested content, so `\(...\)` inside a `theorem`/`proof`/etc. block renders the same way with no wrapper needed. Both the render hook and `layouts/shortcodes/math.html` delegate to a shared `layouts/partials/render-math.html` (the single home of the `transform.ToMath` + `throwOnError` + error-reporting dance). `{{< math >}}` is an escape hatch for the rare shortcode that emits its `.Inner` raw (not markdownified) — not part of the normal authoring path; it `errorf`s if `.Inner` lacks a canonical delimiter pair. **Rendering is unconditional** (not gated on `has_math`): inside a `markdownify` pass the hook's `.Page`/`.PageInner` resolve to the home page, not the essay, so a `has_math` gate would wrongly suppress nested math — the essays-only invariant is enforced by `check_math.py`'s scope check instead. `throwOnError: true` fails the build on invalid LaTeX (the authoritative validity gate here; org-math-lint is a pre-publish authoring-pipeline guard, not site CI). Output is `htmlAndMathml` (visual + screen-reader MathML). Zero client JS. KaTeX CSS is vendored self-hosted (`assets/css/katex.css` + `static/fonts/katex/*.woff2`), loaded via a conditional `<head>` link gated on `.Params.has_math` (essays only). §50 in main.css holds the small hand-rolled overrides. Extending math to non-essay sections requires adding `has_math` to those schemas + dropping the section from `SCOPE_SKIP` (deferred).

### Content & layouts

- **Content sections** in `content/`: `_index.html`, `about/`, `blog/` (legacy), `essays/`, `garden/`, `research/`, `works/`, `recipes/`.
- **Layouts** under `layouts/`: base templates in `_default/`; per-section `{list,single}.html` plus `rss.xml` for essays + garden and standalone `graph.html` pages for garden + research + works. Works splits into `works/`, `works-games/`, `works-music/`, `works-poetry/`. Research splits into `research/`, `research-theme/`, `research-question/` with type discrimination via `cascade: { type: research-theme|research-question }` on `content/research/{themes,questions}/_index.md` (bare section URLs hidden via `build: render: never`). `baseof.html` is a thin semantic wrapper; per-section layouts override `{{ block "main" }}`. Recipes: `layouts/recipes/{list,single}.html` + `layouts/recipes/single.recipe.json` (the RECIPE custom output format — emits a schema.org/Recipe JSON file, shared with the `<head>` block for JSON-LD via `partials/recipes/schema-recipe.html`; first use of schema.org structured data on the site).
- **Partials** under `layouts/partials/`: site chrome (`head`, `header`, `footer`, `scripts`); essays (`essay-card{,-featured}`, `essay-meta`, `essay-toc`, `essay-references`, `essay-series-nav`); shared `filter-chips.html`, `page-sidebar.html` (cross-template rotated-labels rail + mobile dots strip), `search-modal.html` (included once in `baseof.html`); `home/` subfolder (`hero`, `currently`, `research-strip`, `garden-strip`, `studio-strip` — homepage v3 sections); `garden/` subfolder (`note-header`, `stage-glyph`, `note-tile`, `topic-section`, `relative-date`, `path-log`, `links-section`, `graph-{data,script,panel}`); `research/` subfolder (`status-pill`, `output-item`, `theme-card`, `backlinks-data`, `graph-{data,script,panel}`); `works/` subfolder (`tile`, `glyph-sprite`, `game-card`, `music-row`, `poem-row`, `status-pill`, `audio-pill`, `audio-link`, `connections`, `graph-{data,data-inner,script,panel}`, `synced-marker-seconds`, `synced-text-parser`, `poem-synced`); `recipes/` subfolder (`schema-recipe` — schema.org/Recipe JSON-LD + RECIPE output shared partial, `rail` — ingredient list + JS scaler mount, `sources` — source attribution block, `card` — recipe index card). The three per-section `graph-panel.html` files are thin wrappers (R5.3b) that delegate to a shared `layouts/partials/graph-panel.html` (dict params: `id`/`title`/`ariaLabel`/`section`); `graph-panel.html` is the only place a graph side-panel is constructed and always calls `graph-legend.html` — mirrors the already-shared `graph-legend.html` model.
- **Shortcodes** under `layouts/shortcodes/`: `cite` (looks up `site.Data.citations.citations[key]`, errors if missing), `sidenote` (auto-numbered marker + aside via page scratch), `figure` (semantic, supports `class="wide"`), `spoiler` (`<details>`-based, no JS). Deferred-feature stubs: `video-sync`, `lyrics` — each emits a `data-pending` container so fixtures exercise the shape. (`math` is no longer a stub — it's the live build-time KaTeX renderer, see the Math pipeline section. `widget` is also no longer a stub — it's the live explorables mount point, see the JS pipeline table.)
- **Top nav** (locked): Essays / Garden / Research / Works / Library / Streams / Recipes / About. Active item gets `aria-current="page"` via `hasPrefix` match. (Streams added 2026-05-19; Recipes added 2026-07-06; now 8 items.) Eight items plus three icon buttons no longer fit one row at every width, so `.site-nav` steps type and gap down one notch at `max-width: 1099px` — the documented seam for the canonical 1100 tier, so the nav steps in lockstep with the rail rather than a pixel early — keeping the header one row well below 960px. `core.spec.ts` asserts the single row.

### Semantic blocks (AMS-style)

Essays can use 12 AMS-style block shortcodes for rigorous prose: `theorem`, `lemma`, `corollary`, `proposition`, `definition`, `proof`, `remark`, `example`, `note`, `claim`, `conjecture`, `axiom`. Each is a Hugo shortcode in `layouts/shortcodes/` with per-page auto-numbering via `$page.Scratch`. The 11 numbered blocks (theorem-family + definition + the six soft blocks) now render through `layouts/partials/ams-block.html` (`dict` params: `ctx`/`kind`/`class`/`tier`/`counter`); each numbered shortcode is a one-line wrapper that also passes `"inner" .Inner` (a Hugo paired-shortcode parser hint so the closing tag is accepted; the partial reads `$ctx.Inner`). `proof.html` stays bespoke (unnumbered + ∎ tombstone).

Authors write `#+begin_theorem` blocks in org, with optional `#+attr_shortcode: :title <name> :id <slug>` header line for title and cross-reference ID. ox-hugo's `org-hugo-paired-shortcodes` config (in `a3madkour-publish-export.el`) emits the matching `{{< theorem title="…" id="…" >}}…{{< /theorem >}}` markdown.

**Numbering follows AMS conventions:** theorem/lemma/corollary/proposition share one counter (`theorem-family`); definition/remark/example/note/claim/conjecture/axiom each have independent counters; proof is unnumbered (auto-appends ∎ tombstone).

**Cross-references** use the block's `#+attr_shortcode: :id <slug>` + org's `[[#id][text]]` link syntax (manual form, drift-prone), OR the `ref-block` shortcode (`{{< ref-block "thm-foo" >}}` → `Theorem 1`) which auto-formats via a `$page.Scratch` lookup populated by each numbered block at render time. Roadmap row 2.2. Forward references (ref-block called before the target block renders) fall back to the bare id with a `.ref-block-unresolved` warning style — Hugo cannot do a second pass over shortcodes. `:CUSTOM_ID:` property drawers continue to work for headings (B.1.1 unchanged) but are silently dropped by ox-hugo on special blocks.

**Section-prefixed numbering** (roadmap row 2.3) is per-essay opt-in via frontmatter `block_numbering: "section-prefixed"`. When set, `baseof.html` emits `data-block-numbering="section-prefixed"` on `<main>` and `assets/js/block-renumber.js` (loaded via `entry-essay.js`) runs on `DOMContentLoaded` — walks H2s + `.block-*` containers in document order, rewrites every `.block-header` leading `Kind N` to `Kind M.N` (M = section index, N = per-section per-family counter), and updates matching `.ref-block` text. Hugo cannot do this server-side because shortcodes execute before Goldmark sees H2s. No-JS users see bare integers (the server render). Theorem-family (theorem / lemma / corollary / proposition) shares one per-section counter; each independent-counter kind keeps its own. Fixture: `content/essays/example-long-numbering/`.

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

**Recipes** (`content/recipes/<slug>/index.md`) — enforced by `tools/check_recipes_fixtures.py` (34th pair) + `tools/check_recipes_links.py` (35th pair). Required: `title, date, lastmod, draft, summary, servings, sources, ingredients, steps`. Optional: `tags, cuisine, category, yield_unit, prep_minutes, cook_minutes, total_minutes, image, video, outputs`. `ingredients` and `sources` are flow-style YAML objects; `qty` on an ingredient may be `null` (uncountable items) but never `0` or a non-decimal numeric string, and `servings` / `*_minutes` / `qty` must not be zero-padded (Hugo reads `010` as octal 8). A YAML null spelling (`~`/`null`/`Null`/`NULL`) standing in for a required ingredient `item` or source `name` is rejected — `parse_scalar` has no null handling, so those arrive as truthy strings. Optional fields are guarded at the template layer: a recipe with no times renders no time line and emits no `*Time` JSON-LD keys. `content/recipes/example-recipe-three/` is the minimal fixture — required fields only, no tags, no times, one url-less source, one `null` qty — and exists to keep every optional-field-absent path build-exercised; the index therefore shows 3 recipe cards. Spec: `docs/superpowers/specs/2026-07-06-recipe-slice-1-render-download-design.md`; remediation: `docs/superpowers/specs/2026-09-07-recipe-audit-remediation-design.md`.

**Recipe authoring (org → export), Slice 2 — dotfiles pipeline.** A recipe is authored as one `.org` file (`#+HUGO_SECTION: recipes`, `#+TITLE:`, `#+DATE:`, `#+FILETAGS:`, `#+HUGO_SUMMARY:`), with a `:PROPERTIES:` drawer (`:servings:` required; `:yield-unit:`, `:prep-time:`, `:cook-time:`, `:cuisine:`, `:category:`, `:video:`, `:image:` optional — key spellings aligned with org-chef, the prior-art Emacs recipe package, so a future import path stays trivial), a headnote (everything before the first `**` subheading = the exported page body), and three fixed level-2 subheadings: `** Ingredients` (a single `#+NAME: ingredients` org table, columns `qty | unit | item | group | note | alt`, parsed via `org-table-to-lisp` — empty `qty`/`unit` cells become `null`), `** Steps` (an ordered list, one item per step; a leading `[mm:ss]` marker is kept verbatim, reusing the synced-poetry timecode grammar — Slice 2 carries it as data only, no new site rendering), `** Sources` (a plain list, each item `[[url][name]] — note` or a bare name, optionally with a note after an em/en-dash). The handler `a3madkour-publish-recipes.el` (dotfiles, a garden/research-peer per-file handler registered in the `recipes` living-publish section) parses the drawer + three subtrees, strips them before ox-hugo export so only the headnote reaches the body, routes standard fields (title/date/lastmod/draft/summary/tags) through a new `recipes` branch in `a3madkour-publish-frontmatter.el`, and injects the recipe-specific keys (`servings`, `ingredients`, `steps`, `sources`, …) — emitting frontmatter byte-compatible with the Slice 1 contract above. `a3madkour-recipe-lint.el` is a pre-publish linter (org `file:line` errors: required subheadings/table columns/metadata, numeric-or-empty `qty`, timecode shape, bare YouTube-id `:video:`) invoked by `a3-pub.sh` before export, default-on, opt out via `--skip-recipe-check`. Design: `docs/superpowers/specs/2026-07-09-recipe-slice-2-org-authoring-design.md`; plan: `docs/superpowers/plans/2026-07-09-recipe-slice-2.md`.

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

`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `main`. CI step order: pre-build linters (contrast + dark-token equality + CSS-refs + the fixture/link linter pairs + 1 sibling-less) → `hugo --gc --minify` → pagefind + cite metadata linter tests + on-built-page checks → install Pagefind 1.5.2 binary (SHA256-verified) → build Pagefind index into `public/pagefind/` → Node setup + JS unit tests (`node --test`) + `npx playwright test` → smoke test → explorables → **regenerate LHCI URLs (`gen_lhci_urls.py`) → verify LHCI URLs resolve (`check_lhci_urls.py` — runs AFTER the regen so it validates the emitted list)** → page-weight linter + tests → Lighthouse CI desktop (`lighthouserc.json`) → mobile (`lighthouserc.mobile.json`) → upload artifact → deploy. **103 named steps** (recount with `grep -c '^\s*- name:'` after edits rather than trusting this number). The Hugo `.deb` + Pagefind tarball downloads are SHA256-checksum-verified; all `actions/*` + the third-party LHCI action are pinned to commit SHAs; both jobs carry `timeout-minutes`. LHCI runs `numberOfRuns: 3` (median cuts perf flake). (A separate cron workflow `.github/workflows/streams-poll.yaml` runs every 5 minutes — outside this build/deploy pipeline.) Any failure blocks deploy. `public/pagefind/` is gitignored and CI-regenerated each run. Two separate LHCI config files (`lighthouserc.json` for desktop, `lighthouserc.mobile.json` for mobile) — simpler than an env-override approach.

**LHCI URL list is CI-generated.** `tools/gen_lhci_urls.py` rewrites `lighthouserc.{json,mobile.json}` between `hugo --minify` and the LHCI steps, picking one representative URL per (kind, section, type) group alphabetically. Edit `tools/lhci-overrides.json` to change per-group assertion thresholds; don't hand-edit the lighthouserc files. `check_lhci_urls.py` (26th linter pair) stays as defense-in-depth.

### Multi-target export templates

`tools/templates/` hosts the assets the dotfiles D.2 orchestrator (`a3madkour-publish-multi-pdf.el`) copies into each PDF build dir. Layout:

```
tools/templates/
  <class-name>/                # one subdir per LaTeX class — switched by #+LATEX_CLASS:
    preamble.tex               # documentclass + usepackages + setup (becomes the org-latex-classes preamble)
    <class-assets>             # .cls, .sty, .bst, logos — copied verbatim next to the generated .tex
  reference.docx               # pandoc Word reference doc — flat, not per-class
  d2-blocks.lua                # pandoc filter for D.1 semantic blocks — flat
  test-fixtures/               # smoke .tex fixture
```

**Adding a new class** (e.g. an AAAI / ACM / IEEE submission template):

1. Create `tools/templates/<class-name>/` with the conference's `.sty` / `.cls` / `.bst` files alongside any required logos.
2. Write `preamble.tex` mirroring the conference's sample `.tex` preamble — everything from `\documentclass{...}` up to (but not including) `\begin{document}`. The orchestrator splices this as the second element of the `org-latex-classes` alist entry.
3. Add `#+LATEX_CLASS: <class-name>` to the source org file. Add `#+LATEX_HEADER:` lines per-essay for class-specific commands the orchestrator can't infer (e.g. AAAI's `\affiliations{...}`).
4. Fallback: when `#+LATEX_CLASS:` is missing, the orchestrator defaults to `madkour-paper`.

Currently installed: `madkour-paper/` (article + amsthm + biblatex/biber; ships with the site), `aaai24/` (AAAI 2024 anonymous submission — article + aaai24.sty + natbib/bibtex).

### Anchor-link affordance

Every `id`-bearing reading-flow element inside `<main>` (headings `<h2>`–`<h3>` plus elements whose class list contains a `block-` token — i.e., D.1 semantic blocks) carries a trailing `§` glyph that copies the absolute URL to the clipboard on click and surfaces a top-of-viewport status banner ("Link to *X* copied"). Source of truth is one partial — `layouts/partials/anchor-link.html` — called by the Goldmark heading render hook (`layouts/_default/_markup/render-heading.html`), the 12 D.1 semantic-block shortcodes, and 7 chrome partials (References, Recent paths, From this stream, Upcoming, library shelf headings, catalogue, Cite static fallback). Behavior in `assets/js/anchor-link.js` (~1 KB; site-wide entry; delegated `click` listener on `<main>`; Escape skipped when a `<dialog>` is open so the cite modal's native cancel wins). CSS §48. Per-element opt-out via `data-no-anchor-link` (applied to the Cite modal `<h2>`). Heading levels `<h4>`–`<h6>` intentionally omit the glyph to avoid visual density on deeply-nested subsections (roadmap row 2.4; render hook skips via `{{ if and $id (lt .Level 4) }}`; linter `_HEADING_TAGS` excludes `h4-h6`). 27th linter pair (`check_anchor_link.py`) gates the partial-emission invariant; smoke test asserts at least one `.anchor-link` on `/essays/example-five/`.

## Reference docs

- **Design spec (canonical)**: `docs/superpowers/specs/2026-05-03-personal-site-design.md`. §14 is the master phase list.
- **Per-slice specs and plans** under `docs/superpowers/{specs,plans}/`, dated by slice. Memory has shipped-slice details (`project_*.md`); the queued-work entries below cover what's still ahead.
- **Time-synced poetry**: `docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md` (designed) + `docs/superpowers/plans/2026-05-18-time-synced-poetry.md` (plan). Shipped — see memory `project_time_synced_poetry_slice.md`.
- **Org → synced-poetry export**: `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md` (stub, no plan). Phase 3 — elisp/ox-hugo emits the shipped synced-poetry markup contract from real org content.
- **Streams section**: `docs/superpowers/specs/2026-05-13-streams-section-design.md`. New `/streams/` top-level; cron-polled live state.
- **Multi-target export**: `docs/superpowers/specs/2026-05-13-multi-target-export-design.md`. Phase 3 Slice 3 — literate org → Hugo + PDF + Word.
- **TOC collapsible subsections**: `docs/superpowers/specs/2026-05-14-toc-collapsible-subsections-design.md` (designed) + `docs/superpowers/plans/2026-05-18-toc-collapsible-subsections.md` (plan). Shipped — see memory `project_toc_collapsible_subsections_slice.md`.

## Project status (as of 2026-07-06)

**Shipped**: Phases 0–8 plus all polish slices. Phase 3 org-mode pipeline complete — sub-projects **A**, **B** (B.0–B.4), **F** (citations), **C** (math validator), **D** (D.1 semantic blocks + D.2 multi-target export), and **E** (explorables) all shipped, plus org→synced-poetry export. Per-slice merge details live in memory under `project_*.md`.

**The polish-and-bugfix roadmap is fully closed.** `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` — Tiers 1–8 all closed or deferred as of 2026-06-12 (Tier 3 human-driven QA; Tier 6 closed-by-deferral; Tier 9 = the deferred-features registry). Nothing open there.

**Active queue: the post-audit remediation roadmap.** A six-lens codebase audit (2026-07-03) produced `docs/superpowers/specs/2026-07-03-audit-remediation-roadmap.md` (row IDs `R<tier>.<n>`). **Tiers R1 (correctness/security), R2 (guard linters + cheap fixes, incl. R4.3 dead-CSS), R3 (accessibility), and R4 (hygiene/doc-drift/config) are closed as of 2026-07-04.** The two systemic findings driving what remains: (1) "copy instead of abstract" — 3 graph runtimes ~70–80% shared, 12 near-identical AMS block shortcodes, duplicated Python test scaffolds; (2) no client-side test layer at all. **Next queue head: Tier R5** — structural de-duplication, gated on **R5.1 (a JS test harness)** landing first, then graph-core extraction (R5.2), AMS-block/graph-panel consolidation (R5.3, which subsumes R3.2's deferred structural piece), and Python tooling dedup (R5.4). R6 is optional design-scale polish.

- **`docs/superpowers/specs/2026-06-07-deferred-features-registry.md`** — long-horizon trigger-gated capabilities.

All three specs are the source of truth — they survive independently of this file. The CLAUDE.md "Deferred features" table that lived here previously is now in the registry spec.

The audit remediation roadmap is fully closed (R1–R6.3 all shipped). **Current active work: Recipes section** — Slice 1 (site render + download) is on branch `recipes`; Slice 2 (org authoring + lint + export) and Slice 3 (meal-prep planner) are queued stubs. See memory `project_recipe_section.md`.

## Hard constraints (from spec §1)

- **No AI-generated text** anywhere on the site. AI is permitted only for site/app code and code for interactive explorables.
- **No AI-generated illustrations.** SVG icons are hand-authored under `assets/images/icons/`. Hero/figure SVGs in essay page bundles are hand-authored placeholders.
- **Privacy by org-export boundary**: content not exported never reaches the site.
- **Accessibility**: WCAG 2.1 AAA for body text, AA for accents; CB-safe palette; never color-only meaning.
- **Fixture content is obviously dummy** (lorem ipsum / "Example N") — never authored prose. Real content lands via the elisp pipeline.
