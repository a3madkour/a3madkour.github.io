# Phase 8 — search, CI gates, final QA — design

**Phase:** 8 (closes the site rebuild).
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §14.

Phase 8 ships three pieces the master spec gates the project on: a site-wide search modal powered by Pagefind, a CI gate set that protects deploy quality (Lighthouse a11y/perf/best-practices/SEO + smoke test + page-weight budget), and a final QA pass that surfaces and fixes residual keyboard / screen-reader / colour-blindness / mobile issues.

Implementation splits into **three slices** so each ships and reviews independently:

1. **Slice 1** — Pagefind runtime (modal + post-build step + spoiler-ignore + header icon)
2. **Slice 2** — CI gates trio (Lighthouse CI + smoke test + page-weight gate)
3. **Slice 3** — QA checklist + fix-on-find pass

---

## 1. Goals & non-goals

### Goal

Close Phase 8 by shipping (1) a working site-wide search modal, (2) a CI gate set that blocks deploys when accessibility / performance / best-practices / SEO / per-page payload size regresses, and (3) a final QA pass that walks the live site through keyboard nav, screen-reader read-through, colour-blindness simulation, and mobile breakpoints.

### Non-goals

- **Real-content authoring.** Pagefind indexes whatever lorem-ipsum and "Example N" fixtures are in `public/` today; search becomes useful as Phase 3 lands actual content. The runtime shipping now is what matters.
- **Phase 3 elisp pieces.** `:LAST_MODIFIED:` freshness gate and `:ROAM_REFS:` resolution from spec §11's required-data row belong to the elisp pipeline and stay deferred.
- **"Did you mean" / typo correction.** Spec §13 calls for enabling once content exists. Defer.
- **Sub-section search filters.** Modal filters across the 6 top-level sections only (all / essays / garden / research / works / library); no per-tag, per-status, or per-flavor sub-filters. That's spec §13's "Pagefind-based filters" follow-up.
- **Performance work beyond budget enforcement.** If a page exceeds budget, fix it; otherwise leave it alone. No speculative optimization.
- **Real-device mobile lab.** DevTools mobile mode plus the user's phone are enough for v1.

---

## 2. Slice 1 — Pagefind search runtime

### 2.1 Architecture

Pagefind ships as a Rust binary that, run against `public/` after `hugo --minify`, generates a static index under `public/pagefind/` (JSON shards + Wasm + JS loader). At runtime, the custom search modal lazy-loads `pagefind/pagefind.js`, calls its low-level API (`new PagefindInstance()` → `.search(query)`), and renders results into our custom modal markup.

The bundled `pagefind-ui.js` widget is **not** used. Spec §4.24 describes section filter chips, results grouped per section with headers, badges, and a spoiler-aware indicator — none of that is achievable through the bundled UI's flat-list defaults.

### 2.2 File layout

```
.github/workflows/hugo.yaml         # modify — install pagefind binary; post-build index step
.gitignore                          # modify — add public/pagefind/

assets/images/icons/search.svg      # new — hand-authored magnifier-glass (stroke-based, currentColor)

layouts/partials/
  header.html                       # modify — add search icon-button between RSS and theme toggle
  search-modal.html                 # new — modal markup, included once in baseof
  scripts.html                      # modify — add entry-search build entry

layouts/_default/baseof.html        # modify — include search-modal.html once per page

layouts/shortcodes/spoiler.html     # verify — must emit data-pagefind-ignore on .spoiler-body
layouts/_default/single.html        # modify — data-pagefind-body on <main>; metadata attrs
layouts/_default/list.html          # modify — same

assets/js/
  entry-search.js                   # new — bundle entry, imports search.js
  search.js                         # new — modal logic + Pagefind low-level integration

assets/css/main.css                 # append §42 search modal
```

### 2.3 CI install + post-build step

Mirrors how Hugo is installed. Workflow env adds `PAGEFIND_VERSION`. New steps inserted after the Hugo build:

```yaml
env:
  HUGO_VERSION: 0.148.0
  PAGEFIND_VERSION: 1.x.x          # pinned at plan-writing time
steps:
  # … existing Hugo install, lint runs, Hugo build …
  - name: Install Pagefind
    run: |
      wget -O ${{ runner.temp }}/pagefind.tar.gz \
        https://github.com/CloudCannon/pagefind/releases/download/v${PAGEFIND_VERSION}/pagefind-v${PAGEFIND_VERSION}-x86_64-unknown-linux-musl.tar.gz \
        && tar -xzf ${{ runner.temp }}/pagefind.tar.gz -C ${{ runner.temp }} \
        && sudo mv ${{ runner.temp }}/pagefind /usr/local/bin/
  - name: Build Pagefind index
    run: pagefind --site public/
  # … new CI gates (Slice 2) …
  # … upload-pages-artifact …
```

`public/pagefind/` is gitignored (regenerated in CI per spec §15.4).

### 2.4 Modal markup

`layouts/partials/search-modal.html`, included once in `layouts/_default/baseof.html` because the `/` keyboard shortcut works on every page:

```html
<dialog class="search-modal" aria-label="Search">
  <form class="search-modal-form" role="search">
    <span class="search-modal-icon" aria-hidden="true">
      {{ with resources.Get "images/icons/search.svg" }}{{ .Content | safeHTML }}{{ end }}
    </span>
    <input type="search" class="search-modal-input"
           placeholder="Search the site…"
           autocomplete="off" spellcheck="false" />
    <kbd class="search-modal-esc-hint">Esc</kbd>
  </form>
  <nav class="search-modal-filters" aria-label="Filter by section">
    <button type="button" class="search-modal-chip is-active" data-section="all">All</button>
    <button type="button" class="search-modal-chip" data-section="essays">Essays</button>
    <button type="button" class="search-modal-chip" data-section="garden">Garden</button>
    <button type="button" class="search-modal-chip" data-section="research">Research</button>
    <button type="button" class="search-modal-chip" data-section="works">Works</button>
    <button type="button" class="search-modal-chip" data-section="library">Library</button>
  </nav>
  <div class="search-modal-results" role="region" aria-live="polite">
    <!-- JS injects <section data-section="…"><h3>Essays</h3><ol>…</ol></section> per group -->
  </div>
  <footer class="search-modal-footer">
    <div class="search-modal-kbd-hints">
      <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
      <span><kbd>↵</kbd> open</span>
      <span><kbd>⌘</kbd><kbd>↵</kbd> new tab</span>
      <span><kbd>Esc</kbd> close</span>
    </div>
    <div class="search-modal-status" aria-live="polite"></div>
  </footer>
</dialog>
```

`<dialog>` is used for native modal semantics + automatic focus trap + Esc-to-close. Baseline browser support since 2022; no polyfill needed.

### 2.5 Indexing controls

- `<main>` element in every layout gets `data-pagefind-body` so Pagefind indexes only post bodies, not header / nav / footer / sidebar chrome.
- `spoiler` shortcode emits `data-pagefind-ignore` on `<div class="spoiler-body">` so plot text isn't indexed. This is spec line 628 and must be verified to already be in place during slice 1 implementation.
- Each indexed page emits structured metadata via `data-pagefind-meta` so the modal can render badges + group results:

  | Layout | Metadata attrs |
  |---|---|
  | essay | `section:essays`, `date:<RFC-3339>`, `series:<slug or "">` |
  | garden note | `section:garden`, `growth_stage:<seedling/budding/evergreen>`, `flavor:<concept/media/reference>` |
  | research theme | `section:research`, `subtype:theme`, `status:<active/dormant/concluded>` |
  | research question | `section:research`, `subtype:question`, `status:<active/dormant/concluded>` |
  | works (game/music/poem) | `section:works`, `medium:<game/music/poetry>` |
  | library (any leaf) | `section:library`, `medium:<book/album/game/film/series>`, `status:<reading/listening/playing/watching/done/queued>` |
  | about | `section:about` |
  | homepage | `section:home` |

  Metadata is set per-layout in a one-liner: `data-pagefind-meta="section:essays,date:{{ .Date.Format "2006-01-02" }}"` on the wrapper element below `<main>`.

- Spoiler-aware indicator: when a page contains any `<div class="spoiler-body">`, the page also emits `data-pagefind-meta="spoilers:<count>"`. Results render "N spoiler block(s) hidden from search" under their snippet if `spoilers > 0`.

### 2.6 Modal JS bundle

New bundle entry (sixth entry per spec §JS pipeline). Naming continues the established convention:

```
assets/js/entry-search.js → search.<hash>.js   # loaded on every page (predicate: always)
```

`scripts.html` adds the entry to the existing `js.Build` array and includes the resulting script on every page (no section predicate).

Module responsibilities (`assets/js/search.js`):

- Wire `/` keyboard shortcut: open modal if not currently in an `<input>` / `<textarea>` / `[contenteditable]`.
- Click handler on the header search icon: opens modal.
- On first open: dynamic `import('/pagefind/pagefind.js')` — lazy-loaded so cold pages don't pay the ~50KB cost. Cached after.
- Debounce input by ~150ms; call `instance.search(q, { filters: { section: [...] } })`.
- Filter chips: single-active across sections. Clicking "All" clears section filter. Clicking an active chip switches to "All". State syncs to next search.
- Render results into `<section data-section="…">` groups, ordered: essays → garden → research → works → library → other.
- Each result row: badge (section name), title with Pagefind's pre-highlighted excerpt, snippet with `<mark>` from Pagefind, optional spoiler indicator, optional growth-stage / status pill from metadata.
- Keyboard nav: ↑/↓ moves selection between result rows; Enter opens (window.location); ⌘/Ctrl+Enter opens in new tab (`window.open`); Esc closes via `<dialog>` native close.
- Focus management: `<dialog>` traps focus natively when opened with `showModal()`. On close, return focus to the trigger (header icon or whatever element had focus before `/`).
- Reduced-motion: modal fade-in only, no transform animation. CSS handles via `prefers-reduced-motion` media query.
- Status footer: "N results in Mms" line updates on each query.

Expected bundle size: ~3–5KB minified (no vendored dependencies; Pagefind itself is dynamically imported).

### 2.7 Header icon

`assets/images/icons/search.svg` — hand-authored magnifier-glass following the existing icon style (stroke-based, `currentColor`, ~16-20px viewBox; matches `rss.svg` + `sun.svg`).

`layouts/partials/header.html` gains a new `<button class="icon-button" data-search-toggle>` between the RSS link and the theme toggle button. Accessible label "Open search".

### 2.8 CSS — §42 search modal

New section in `assets/css/main.css`, token-driven:

- `dialog[open]` → centred, ~900px max-width, fade-in transition (skipped under `prefers-reduced-motion`), backdrop blur 8px.
- Modal background `var(--color-paper)`; input border `var(--color-ink-soft)`; chips inherit filter-chip palette.
- Result row hover/keyboard-active state mirrors filter-chip-active treatment.
- Badge colour per section pulls from existing section palette (essays burgundy, garden green, research steel, works ink, library stone).
- `<mark>` highlight uses `background: color-mix(in srgb, var(--color-burgundy) 20%, transparent)`.
- Mobile: `width: 95vw`, `max-height: 80vh`, results pane scrolls.
- Respects all four `[data-theme]` modes via existing tokens.

### 2.9 Out of scope for Slice 1

- The search modal needs no fallback for JS-disabled visitors (the search itself is JS-driven). Site navigation via the top nav + section indexes is the no-JS fallback.
- No keyboard shortcut for "next result page" — Pagefind returns paginated results but our modal scrolls; revisit if result counts grow.
- No analytics on search queries (the site is analytics-free per spec §8).

---

## 3. Slice 2 — CI gates trio

Three new gates inserted into `.github/workflows/hugo.yaml`, all running after `hugo --minify` and before `actions/upload-pages-artifact`. Order: smoke test → page-weight gate → Lighthouse CI. Cheap gates first so we fail fast.

### 3.1 Smoke test

**Spec §11 list:** `/`, `/essays/`, `/garden/`, `/research/`, `/works/`, `/about/`, `/library/`.

**Implementation:** `tools/check_smoke.py` (stdlib only). Walks `public/<path>/index.html` for each URL; asserts file exists, is non-empty, and parses as HTML via `html.parser.HTMLParser`. Fails CI with a clear message on any miss.

**House-style exception:** **no paired `tools/test_check_smoke.py`.** The logic is too thin to warrant a unit-test sibling — it would mostly re-test stdlib. The 12 existing linter pairs all have real parsing / validation logic that justifies test pairing; this one doesn't. This exception is the only place in the codebase that breaks the linter-pair pattern; documented here.

**Workflow step:**

```yaml
- name: Verify build smoke test
  run: python3 tools/check_smoke.py
```

### 3.2 Page-weight gate

**Budgets** (from spec §8):
- Default: <100 KB total per page
- Media-heavy: <500 KB — applies to `/`, `/works/music/<slug>/`, `/works/music/`
- Graph-bearing: <600 KB — applies to `/garden/`, `/garden/graph/`, `/research/graph/`, `/works/`, `/works/graph/`

**Classifier** (ordered prefix → budget; first match wins):

```python
BUDGETS = [
    ("/garden/graph/",   600_000),
    ("/research/graph/", 600_000),
    ("/works/graph/",    600_000),
    ("/works/",          600_000),   # works umbrella (Bento + ⊞ Graph data inline)
    ("/garden/",         600_000),   # garden index (filter chips data inline)
    ("/works/music/",    500_000),   # all music pages
    ("/",                500_000),   # homepage only (exact match before fallthrough)
    ("",                 100_000),   # everything else
]
```

`/` needs exact-match (not prefix) handling so it doesn't catch the entire site. Implementation detail in the script.

**Implementation:** `tools/check_page_weights.py` + `tools/test_check_page_weights.py`. Unit-test sibling is justified here — the budget-classification logic is real and worth pinning.

Script walks `public/`, parses each `index.html` for `<link rel="stylesheet" href="…">`, `<script src="…">`, `<img src="…">`. Sums the byte size of every referenced static asset that lives in `public/`. Inline `<style>` and `<script>` content counted via the HTML byte size itself. External resources (Google Fonts URLs) excluded — they're loaded from cdn, not our budget.

**Output on failure:** dump a table of offending pages with byte breakdown (HTML / CSS / JS / images) so the user sees exactly what blew the budget. Sample:

```
PAGE                              BUDGET    ACTUAL    HTML    CSS     JS      IMG
/works/graph/                     600_000   712_341   18_204  31_127  478_201 184_809
/essays/example-3/                100_000   142_018   42_018  31_127  4_829   64_044
2 page(s) over budget.
```

**Workflow steps:**

```yaml
- name: Verify page weights against §8 budgets
  run: python3 tools/check_page_weights.py
- name: Run page-weight linter unit tests
  run: python3 -m unittest tools/test_check_page_weights.py -v
```

### 3.3 Lighthouse CI

**Tool:** `treosh/lighthouse-ci-action@v12` (current stable major; pinned at plan-writing time).

**Form factors:** both mobile (LHCI default preset) and desktop (`settings.preset: desktop`). Two separate runs.

**Gated categories ≥90:** accessibility, performance, best-practices, SEO. Any sampled URL scoring <90 in any category fails the job.

**URL sample list (12 URLs):**

| URL | Reason |
|---|---|
| `/` | Homepage hero + Currently + strips |
| `/essays/` | Bento index |
| `/essays/<slug>/` | Essay post (TOC + sidenotes + figures + citations) |
| `/garden/` | Garden index (filter chips, heaviest non-graph index) |
| `/garden/<slug>/` | Garden note |
| `/garden/graph/` | Standalone graph (heaviest JS) |
| `/research/` | Research index |
| `/research/themes/<slug>/` | Theme page |
| `/research/questions/<slug>/` | Question hub |
| `/works/` | Works umbrella (Bento + graph data) |
| `/library/` | Library umbrella |
| `/about/` | About page |

12 URLs × 2 form factors = 24 runs. Each ~15-25s. Total ~6-10 minutes.

Slugs hardcoded into `lighthouserc.json`. We choose stable fixture slugs (the existing `example-1` family) and pin them. If a fixture is later renamed, the config file is the single point of update.

**Workflow step:**

```yaml
- name: Lighthouse CI
  uses: treosh/lighthouse-ci-action@v12
  with:
    configPath: lighthouserc.json
    uploadArtifacts: true
    temporaryPublicStorage: true
```

`lighthouserc.json` lives at repo root.

---

## 4. Slice 3 — Final QA pass

### 4.1 Deliverable

Markdown checklist at `docs/superpowers/qa-checklists/2026-05-DD-phase-8-final-qa.md`. Walked top-to-bottom; items marked ☑ / ☒ / ⚠ inline. Small fixes (CSS tweak, missing aria-label, alt-text fix) patched in-slice and re-tested. Anything requiring rethinking opens a follow-up spec.

Slice 3 is light on code work by intent. It audits what slices 1+2 ship.

### 4.2 Checklist categories

**1. Keyboard nav.**

- Tab order through homepage hero → Currently → Research strip → Garden strip → Works strip → footer is sane (no traps, no skipped interactive elements).
- Filter chip strips on `/essays/`, `/garden/`, `/works/games/`, `/works/music/`, `/works/poetry/`, `/library/reading/`, `/library/listening/`, `/library/playing/`, `/library/watching/` arrow-key navigable per spec.
- Filter-chip disclosure: arrow keys flow input → first chip → between visible chips (no wrap) → input again; Esc clears search.
- Garden stacked-columns: Tab moves through column headers and tile links predictably.
- Graph pages (`/garden/graph/`, `/research/graph/`, `/works/graph/`): keyboard users have a working sidebar/links fallback; graph itself is decoration.
- Theme toggle button + RSS link + search icon all reachable + activate via Space/Enter.
- Search modal: `/` opens (when not in `<input>` / `<textarea>` / `[contenteditable]`); modal traps focus; Tab cycles input → filter chips → results → kbd-hints footer → input; Esc closes; ↑/↓ navigate result rows; Enter opens.
- Page-sidebar rail + mobile dots strip: anchor links activate with Enter.

**2. Screen-reader walkthrough.**

- Targets: homepage, one essay post, one garden note, one research theme, one library leaf, one game page, search modal.
- SR of choice: Orca on Linux is the path. NVDA-on-Windows is acceptable if accessible; VoiceOver-on-iOS is the mobile audit.
- Each target verified for: landmark structure (header / nav / main / footer announced); H1/H2/H3 hierarchy reads in document order; alt text on icons (RSS, theme toggle, search) speaks meaningful labels; status pills + growth-stage glyphs have text content (not colour-only); citation hover-cards have keyboard-accessible alternative; sidenote markers announce as superscript references; graph pages announce "decorative" or have proper labels.

**3. Colour-blindness simulation.**

- Tool: Chrome DevTools → Rendering → Emulate vision deficiencies.
- Pages checked: homepage, research index (status pills), library leaves (status badges), garden index (growth-stage glyphs + tags), one essay post.
- Verify under each of {protanopia, deuteranopia, tritanopia, achromatopsia}: status pills distinguishable via shape + label (not colour); growth stages still legible; theme toggle / RSS icons keep contrast; filter-chip active state still clearly differentiated.

**4. Mobile audit.**

- Breakpoints to spot-check: 360px (small phone), 414px (large phone), 768px (tablet), 960px (half-screen 1080p workspace per memory `feedback_test_at_half_screen_1080p.md`), 1220px (sidebar rail → strip flip point).
- DevTools mobile mode + real device (the user's phone) for at least 1-2 pages.
- Items: homepage hero stacks; Currently widget rows wrap cleanly; Research strip readable; Garden strip readable; page sidebar collapses to mobile dots strip below 1220px; filter chip strips wrap without overflow; search modal sized correctly on phone (~95vw); graph pages downgrade to standalone full-screen view as designed.

**5. Performance budgets.**

- `check_page_weights.py` (slice 2) is the primary gate (automated).
- Manual cross-check: open DevTools Network panel on the homepage cold-load and verify total transfer matches the script's number.
- Spot any low-hanging perf wins (a font preload, `loading="lazy"` on an image, etc.) and patch in-slice.

---

## 5. Open questions for the implementation plan

These resolve at writing-plans time so the spec doesn't lock premature choices:

1. **Pagefind version pin.** Latest is v1.x. We pin a specific patch release in `PAGEFIND_VERSION`. Chosen at plan time after checking recent releases for regressions.
2. **Pre-warm Pagefind on idle vs strict lazy-load.** Strict lazy: first keystroke pays ~50KB. Pre-warm on `requestIdleCallback`: invisible to perf budgets, adds complexity. Default: strict lazy. Decision recorded in the plan if changed.
3. **`<dialog>` polyfill.** Baseline since 2022 in all major browsers (Safari 15.4+, Firefox 98+, Chrome/Edge 37+). No polyfill. Document in plan.
4. **LHCI Chrome cache strategy.** First LHCI run on a fresh CI agent installs Chrome (~100MB). The action handles caching but cache-key choice matters for hit rate. Settle in the plan.
5. **Fixture slug stability for LHCI URLs.** A `lighthouserc.json` with hardcoded slugs breaks if a fixture is renamed. Mitigation: pick fixture slugs we don't expect to move (`example-1` family) and pin them; comment the file explaining why.
6. **Page-weight per-page override map.** If a real page legitimately exceeds 100KB (heavy hero illustrations + sidenotes + citations), the classifier might need per-URL overrides. Defer the override map until `check_page_weights.py` actually fails on something we want to keep.
7. **Smoke test against running Hugo server vs static files.** We chose file-existence-only for simplicity. A running-server smoke would also catch broken templates rendering empty pages. Revisit if a broken-template regression slips through.

---

## 6. Risks + rollback

**Risk: Pagefind binary install flakes in CI.** Mitigation: pin version; cache binary; fail-fast with clear message if download breaks.

**Risk: LHCI scores below 90 on first run.** Likely outcome given inline-SVG-heavy pages, graph pages with ~110KB JS, and Google Fonts. First plan iteration is "make it pass" — reduce weight, add `loading=lazy`, tune font-display (already `swap`), or lower the floor for specific categories on specific URLs *with explicit justification in the spec*. We'd rather discover this than ship a vacuous gate.

**Risk: Modal markup breaks essay-page sidenotes or filter-chip JS.** Search modal lives at the bottom of every page; failure mode would be CSS bleed or JS scope leak. Mitigation: scoped CSS section (§42); JS isolated in `entry-search.js` bundle; tested on representative pages before merge.

**Rollback per slice:** each slice is its own PR; revert the merge commit if anything goes sideways. No DB / no external state. New CI steps can be temporarily commented out if they block deploys while a real fix is in flight (the contrast checker did this once during early Phase 1 — house pattern).

---

## 7. Total CI step delta

| Before Phase 8 | After Phase 8 |
|---|---|
| 25 verification steps | 29 verification steps |

New steps: smoke test, page-weight gate, page-weight unit tests, Lighthouse CI. Existing 25 steps unchanged.

---

## 8. Files touched (summary)

**Slice 1 — Pagefind runtime:**

- `.github/workflows/hugo.yaml` (modify)
- `.gitignore` (modify)
- `assets/images/icons/search.svg` (new)
- `layouts/partials/header.html` (modify)
- `layouts/partials/search-modal.html` (new)
- `layouts/partials/scripts.html` (modify)
- `layouts/_default/baseof.html` (modify)
- `layouts/_default/single.html` + `list.html` (modify)
- `layouts/shortcodes/spoiler.html` (verify; modify if needed)
- `assets/js/entry-search.js` + `search.js` (new)
- `assets/css/main.css` (append §42)
- Per-layout metadata one-liners on essay / garden / research / works / library / about / home templates

**Slice 2 — CI gates trio:**

- `tools/check_smoke.py` (new, no test sibling)
- `tools/check_page_weights.py` + `tools/test_check_page_weights.py` (new pair)
- `lighthouserc.json` (new)
- `.github/workflows/hugo.yaml` (modify — three new steps after Hugo build)

**Slice 3 — Final QA pass:**

- `docs/superpowers/qa-checklists/2026-05-DD-phase-8-final-qa.md` (new)
- Whatever code/CSS fixes the walkthrough surfaces (in-slice)

---

*End of spec.*
