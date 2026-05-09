# Garden interactions — slice design

**Status:** drafted · **Date:** 2026-05-08 · **Slice:** Phase 4 — Garden interaction model
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §4.5–§4.9, §5.6, §5.7, §14
**Predecessor slices:**
- `docs/superpowers/specs/2026-05-07-garden-notes-design.md` (garden — established the single-note template, topic-map facet, fixture set this slice extends with link data)
- `docs/superpowers/specs/2026-05-08-garden-tag-search-design.md` (filter-chips — shared partial unaffected by this slice)

---

## 0. Context for future Claude sessions

This slice ships the four interaction features parent §14 lists for Phase 4: **Matuschak-style stacked-column retrieval**, **path log with consent banner**, **outgoing-links + backlinks sections** on note pages, and a **force-directed graph view**. The fifth Phase 4 item in parent §14 — the spoiler shortcode — already shipped in the prior garden slice (native `<details>` runtime).

The slice is intentionally decoupled from the Phase 3 org-mode pipeline. Parent §10.6 has the graph fed by `data/notes.json` (an elisp output); this slice synthesizes the same JSON shape at Hugo build time from existing fixture frontmatter + body link extraction. When Phase 3 lands, the build-time partial gets retired and the JSON comes from `site.Data.notes` instead — JS does not change. Backlinks computation also lives in the same partial. No new external dependencies (d3-force is the only library, and it lazy-loads on first graph open).

Fixtures gain ~26 additional internal `/garden/<slug>/` references (inserted into existing lorem-ipsum bodies — filler-only per CLAUDE.md hard constraint) so the graph has visible structure: two clusters matching the topic-map groupings, ~5 cross-topic bridges, one deliberate orphan to keep the lonely-node rendering exercised. A new CI gate validates that every internal garden reference resolves to a non-draft fixture.

**Decisions made during brainstorm** (expanded in §2):
- Graph data derived at Hugo build time from page params + body regex (no `data/notes.json` dependency)
- Stacked-column content fetched as full HTML with `<article>` extracted via DOMParser
- Eager Matuschak activation: every garden note page is column 1 of a stack from load; path log always present; URL syncs `?stack=...`
- Graph as side panel on desktop (slide-in from right, ~280px); separate `/garden/graph/` route as the mobile fallback and a deep-linkable URL on every viewport
- Local-graph mode shipped in full (all / 1-hop / 2-hop) per parent spec
- Re-focus existing column on duplicate click; clear / Esc collapse to URL note (column 1) and strip `?stack=`
- Outgoing-links section limited to `/garden/` targets; v1 backlinks list is titles only (no snippet preview)
- d3-force lazy-imported on first graph open

---

## 1. Slice scope

### In scope
1. Stacked-column runtime (`assets/js/garden-stack.js`) — eager activation, click interception, fetch + DOMParser, append/refocus, scroll-snap, URL sync via `history.replaceState`, clear/Esc handlers
2. Path log partial (`layouts/partials/garden/path-log.html`) — sticky breadcrumb at top of stack container, "N in stack · clear · ⊞ Graph" right side, ARIA `<nav aria-label="Reading path">`
3. Consent banner — rendered on first 1→2 stack expansion when `path-log-consent` is unset; choice stored as `yes` | `session` | `no`; reading-path slugs stored under `garden-path-log` in localStorage (`yes`) or sessionStorage (`session`)
4. Outgoing-links + backlinks section partial (`layouts/partials/garden/links-section.html`) at bottom of every column; computed at build time from a single shared partial
5. Build-time graph data partial (`layouts/partials/garden/graph-data.html`, `partialCached`) — walks all garden pages, extracts outgoing slugs via `findRE` on `.RawContent`, classifies edges as same-topic / cross-topic, emits inline JSON `<script type="application/json" id="garden-graph-data">` on every garden page
6. Graph runtime (`assets/js/garden-graph.js`) — d3-force simulation, side-panel toggle, tag/stage chip filters, all/1-hop/2-hop local-graph mode (note pages only), bold-stroke "in stack" markers driven by `garden:stack-changed` events, panel state persisted in `sessionStorage["garden-graph-open"]`
7. Graph panel partial (`layouts/partials/garden/graph-panel.html`) — slide-in from right, 280px, `role="region" aria-label="Garden graph"`, close button, filter-chips inside
8. Graph page (`layouts/garden/graph.html`) at `/garden/graph/` — separate-page rendering for mobile fallback and deep linking; uses the same JSON, same `garden-graph.js` module
9. Fixture extension — ~26 additional internal `/garden/<slug>/` references inserted across 13 of 14 fixtures (one note kept deliberately orphan); insertion is into existing lorem-ipsum bodies only (no authored prose)
10. New CI gate — `tools/check_garden_links.py` + `tools/test_check_garden_links.py` (stdlib only); validates every internal `/garden/<slug>/` reference resolves to a non-draft fixture; wired between garden-fixtures and filter-chips checks in `.github/workflows/hugo.yaml`
11. CSS additions to `assets/css/main.css` — sections 24 (path log + consent banner), 25 (stacked columns + scroll-snap + mobile collapse), 26 (links section), 27 (graph panel slide-in), 28 (graph page)
12. CLAUDE.md update — new commands, new architecture sections, project-status update

### Deferred (kept as visible/round-trippable hooks)
- Backlink snippet previews ("…flagged by salience-and-memory") — easy to add later by extending the build-time partial; the v1 list reads fine without
- Citation hover-card runtime — Phase 3 (fixtures already carry `data-cite-key` / `roam_refs`)
- Library cross-linking from media notes — Phase 7
- `data/notes.json` from ox-hugo — Phase 3 (drop-in replacement for the build-time partial; JS unchanged)

### Out of slice (explicit)
- Cross-section link tracking (essays linking into garden, garden linking into research) — outgoing-links section is `/garden/` only; cross-section discovery happens via Pagefind in Phase 8
- Research graph — separate slice (Phase 5)
- Pagefind indexing of stacked content — Phase 8
- Browser-test runner / Playwright / etc. — JS too small to justify; introduce when JS surface grows
- Tag count badges on graph nodes — out of scope; tags signal via color + filter chips
- Outgoing-links scope grouping ("Garden notes (3) · Essays (1)") — rejected as overkill for v1

---

## 2. Decisions captured during brainstorm

| Decision | Reasoning | Where it lives |
|---|---|---|
| Build-time-derived graph data over hand-authored `data/notes.json` stub | Keeps the org-mode pipeline at zero touch; nothing fake to maintain; same JSON shape ox-hugo will eventually emit so JS doesn't change in Phase 3 | `layouts/partials/garden/graph-data.html` |
| Stack activation: eager Matuschak (every note page = column 1 from load) | Matches the parent spec's wording faithfully ("opens as a new column to the right of any existing columns" implies stack already exists). Path log always discoverable. URL is shareable and deep-linkable. | `garden-stack.js` + `single.html` |
| Graph view: side panel (slide-in right) on desktop; separate `/garden/graph/` page as mobile fallback and direct route | The panel's "you are here" markers (bold-stroke nodes for in-stack notes) are the genuine design win that a separate page can't replicate; the separate page is honest about mobile and useful as a deep link on any viewport | `graph-panel.html`, `graph.html`, `garden-graph.js` |
| Stacked-column content via fetch + DOMParser extraction of `<article>` | No Hugo plumbing needed; gracefully degrades (links work without JS); ~30 lines of JS | `garden-stack.js` |
| Local-graph mode shipped in full (all / 1-hop / 2-hop) | Per parent §4.6; tested via fixture cluster structure during dev | `garden-graph.js` |
| Re-focus existing column on duplicate click (no append) | Matches reader's mental model ("I already opened that one") and keeps URL clean | `garden-stack.js` |
| Clear / Esc → collapse to URL note (column 1), strip `?stack=` | One concept, two affordances; preserves entry point as the "home base" of the stack | `garden-stack.js` |
| Outgoing-links section: `/garden/` targets only | The links section is about garden interconnection; cross-section links remain inline in the body and discoverable through Pagefind later | `links-section.html` |
| Backlinks v1: titles only, no snippet preview | Snippets need extra extraction logic and the list reads fine without; explicitly deferred so it's easy to add later | `links-section.html` |
| Inline JSON on every garden page (not a separate `data/garden-graph.json` artifact) | Same data on every page, no fetch round-trip; the JSON is small (~3-5 KB for current fixtures) | `graph-data.html` |
| d3-force loaded via dynamic `import()` on first panel open | Note pages that never open the graph don't pay the ~30 KB cost | `garden-graph.js` |
| Graph panel is non-modal (no focus trap) | Users want to peek at the graph while reading — a focus trap fights that intent. Esc-to-close is the keyboard exit. | `graph-panel.html` + `garden-graph.js` |
| Esc disambiguation: panel-focused → close panel; otherwise (panel closed, stack ≥ 2) → clear stack | Two-tier Esc semantics are unambiguous when one is "active surface" (panel) and the other is "ambient" (stack) | `garden-stack.js`, `garden-graph.js` |
| Reduced-motion: graph runs 300 ticks then `simulation.stop()`; column scroll-snap uses `scroll-behavior: auto` when reduced | Static layout still readable; aligns with site-wide reduced-motion convention | `garden-graph.js`, CSS §25 |
| Consent banner is a `<aside role="dialog">` rendered on first 1→2 expansion only | Only ask when the act of recording would actually happen; "yes" / "session" / "no" stored under `path-log-consent` | `garden-stack.js` |
| Single `nguyen-2020-games-as-art` fixture left as deliberate orphan (no in/out garden links) | Reference-flavor academic papers being isolated is honest about the org-roam workflow; tests the lonely-node rendering | Fixture set |
| Mini-hubs at salience-and-memory (deg 7), memory-in-play and recall-vs-replay (deg 5) | Exercises size-by-degree node sizing; matches realistic graph topology for a small note set | Fixture set |
| Filler-only insertion discipline (CLAUDE.md hard constraint) | Phase 3's elisp pipeline overwrites bodies wholesale; the test surface (which slugs link to which) survives because the linter validates the resolved set, not specific text positions | Fixtures |

---

## 3. Architecture

### 3.1 Data flow

1. **Build time (Hugo, single pass):**
   - `partials/garden/graph-data.html` (called via `partialCached "garden/graph-data" .Site` so it computes once per build)
   - Walks `where .Site.RegularPages "Section" "garden"`
   - For each page: extracts outgoing slugs via `findRE \`\\(/garden/[a-z0-9-]+/\\)\` .RawContent`, dedupes
   - Builds `byOut` (slug → []targets) and inverts to `byIn` (slug → []sources, which is the backlinks relation)
   - Builds `byTopic` from `topic_map:` frontmatter
   - For each edge `(src, tgt)`: classifies `crossTopic` = true unless src and tgt share at least one topic-map ownership
   - Builds nodes with `{slug, title, tag (first tag — primary), stage, flavor, degree (in+out)}`
   - Returns a JSON-encoded string ready for inlining

2. **Page render (Hugo):**
   - `layouts/garden/single.html` and `layouts/garden/graph.html` and `layouts/garden/list.html` each include the inline JSON via `<script type="application/json" id="garden-graph-data">{{ partialCached "garden/graph-data" .Site }}</script>`
   - Note pages also include the path log partial, links-section partial (computed from same data), and the graph panel partial
   - Index page includes the "⊞ Graph" toggle in the filter strip and the graph panel partial

3. **Page load (browser):**
   - `garden-stack.js` runs on any page where `.garden-stack` exists; reads `?stack=` from URL; if present, fetches notes 2..N in parallel (`Promise.all([fetch(...), ...])`), extracts each page's `.garden-note article`, appends to `.garden-stack` container
   - `garden-graph.js` runs on any page where `#garden-graph-data` is present; parses JSON; mounts panel if `.garden-graph-panel` exists; mounts page renderer if `.garden-graph-page` exists; restores panel-open state from `sessionStorage["garden-graph-open"]`

4. **User interaction:**
   - Click on `<a href="/garden/<slug>/">`: `garden-stack.js` intercepts via delegated `click` listener on `.garden-stack`. If slug already in stack → `scrollIntoView({behavior: motionPref(), inline: 'start'})`. Else → fetch + parse + append + URL update + dispatch `garden:stack-changed` event
   - Click on path-log "clear" or Esc (panel closed, stack ≥ 2): drop columns 2..N from DOM, strip `?stack=`, dispatch event, focus column 1 heading
   - Click on path-log "⊞ Graph" or index toolbar "Graph view": toggle panel `.garden-graph-panel[aria-hidden]`; first open dynamic-imports `d3-force`, builds simulation, renders SVG
   - Click on chip in graph panel: filter nodes/edges; re-init simulation
   - Click on local-mode chip (note pages only): BFS from URL slug; restrict to N-hop neighborhood; re-init simulation
   - Click on graph node: `location.assign('/garden/<slug>/')` — full page nav, browser handles
   - First time `garden-stack.js` would write to localStorage (i.e., first 1→2 expansion AND `path-log-consent` is unset): render consent banner above path log; on choice, store `path-log-consent` and (if `yes` or `session`) start writing visited slugs

### 3.2 Components & boundaries

| Component | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `partials/garden/graph-data.html` | Walks all garden pages once; produces full graph JSON; cached per build | `.Site.RegularPages` filtered to `Section == "garden"` | JSON string |
| `partials/garden/path-log.html` | Renders sticky breadcrumb row at top of stack container | Current page, current stack from URL | Static HTML |
| `partials/garden/links-section.html` | Renders outgoing-links + backlinks at column bottom | Current page slug, graph-data partial output | Static HTML |
| `partials/garden/graph-panel.html` | Renders the side-panel scaffolding (filters, SVG container, close button); empty until JS mounts | — | Static HTML |
| `layouts/garden/graph.html` | Standalone page at `/garden/graph/`; full-viewport SVG host; mobile fallback | Same JSON | Page |
| `layouts/garden/single.html` (modified) | Wraps article in stack container; renders path log; renders links section; mounts graph panel | Page params + graph-data | Page |
| `layouts/garden/list.html` (modified) | Adds graph toggle to filter strip; mounts graph panel | Existing + graph-data | Page |
| `assets/js/garden-stack.js` | Stack runtime: click interception, fetch+append, URL sync, clear/Esc, consent banner | DOM, URL, localStorage / sessionStorage | DOM mutations + custom events |
| `assets/js/garden-graph.js` | Graph runtime: d3-force, panel toggle, filters, local mode, in-stack markers | Inline JSON, custom events from stack | SVG, panel DOM, sessionStorage |
| `tools/check_garden_links.py` | Validates every `/garden/<slug>/` reference in fixture bodies resolves | Fixture filesystem | exit 0 / exit 1 + errors |
| `tools/test_check_garden_links.py` | Unit tests for the linter | — | Test results |

### 3.3 HTML contract — note page (`single.html`)

```html
<article class="garden-note garden-stack" data-stack-root="true">
  <nav class="garden-path-log" aria-label="Reading path">
    <span class="path-log-label">Path:</span>
    <a class="path-log-crumb" href="/garden/">Garden</a>
    <span class="path-log-sep">›</span>
    <a class="path-log-crumb" aria-current="page" href="/garden/salience-and-memory/">Salience &amp; memory</a>
    <span class="path-log-actions">
      <span class="path-log-count">1 in stack</span>
      <button type="button" class="path-log-clear">clear</button>
      <button type="button" class="garden-graph-toggle" aria-expanded="false">⊞ Graph</button>
    </span>
  </nav>

  <div class="garden-stack-columns">
    <article class="garden-column is-active" data-slug="salience-and-memory">
      <!-- existing note-header partial -->
      <h1 class="garden-note-title" tabindex="-1">Salience &amp; memory</h1>
      <div class="garden-note-body essay-body">
        {{ .Content }}
      </div>
      <!-- topic-map tile grid (if any) -->
      <!-- new: links section -->
      <section class="garden-links">
        <h2>Links from this note</h2>
        <ul>
          <li><a href="/garden/surprise-budget/">Surprise budget</a></li>
        </ul>
        <h2>Backlinks (2)</h2>
        <ul>
          <li><a href="/garden/surprise-budget/">Surprise budget</a></li>
          <li><a href="/garden/memory-in-play/">Memory in play</a></li>
        </ul>
      </section>
    </article>
    <!-- additional columns appended by JS when ?stack= present -->
  </div>

  <aside class="garden-graph-panel" aria-hidden="true" aria-label="Garden graph" role="region">
    <!-- mounted by garden-graph.js on first open -->
  </aside>

  <script type="application/json" id="garden-graph-data">
    {"nodes":[…],"edges":[…],"topics":{…}}
  </script>
</article>
```

### 3.4 HTML contract — graph page (`graph.html`)

```html
<section class="reading-column garden-graph-page">
  <p class="crumb"><a href="/garden/">Garden</a> ›</p>
  <h1>Graph</h1>
  <p class="garden-graph-summary">14 notes · 28 links. Click a node to open it in a stack.</p>

  <nav class="garden-graph-toolbar" aria-label="Graph filters">
    <!-- tag chips, stage chips — same shape as filter-chips.html -->
  </nav>

  <div class="garden-graph-canvas" role="img" aria-label="Force-directed graph of 14 garden notes">
    <!-- SVG mounted by garden-graph.js -->
    <desc>Two clusters connected by cross-topic links; one isolated node.</desc>
  </div>

  <ul class="garden-graph-legend">
    <li><span class="swatch" style="background: #993333"></span> narrative</li>
    <li><span class="swatch" style="background: #3a5a40"></span> memory</li>
    <li>node size = link count · solid = same topic-map · dashed = cross-topic</li>
  </ul>

  <script type="application/json" id="garden-graph-data">{…}</script>
</section>
```

### 3.5 JSON shape

```jsonc
{
  "nodes": [
    {
      "slug": "salience-and-memory",
      "title": "Salience & memory",
      "tag": "narrative",          // first tag — primary, used for color
      "stage": "budding",          // seedling | budding | evergreen
      "flavor": "concept",         // concept | media | reference
      "degree": 7                  // in + out
    }
    // …
  ],
  "edges": [
    {"source": "surprise-budget", "target": "salience-and-memory", "crossTopic": false},
    {"source": "salience-and-memory", "target": "memory-in-play", "crossTopic": true}
    // …
  ],
  "topics": {
    "procedural-narrative": ["surprise-budget", "salience-and-memory", "emergence-vs-design", "story-atoms"],
    "memory-in-play": ["sleep-and-consolidation", "recall-vs-replay", "the-save-game"]
  }
}
```

When Phase 3 ships ox-hugo, the same shape comes from `site.Data.notes` — JS unchanged.

### 3.6 State shape (JavaScript)

```js
// garden-stack.js
const stack = {
  slugs: [],            // ordered list, slugs[0] is the URL note
  consent: 'unset',     // 'unset' | 'yes' | 'session' | 'no'
  visited: [],          // slugs visited across stack expansions; mirrored to storage if consent ≠ 'no'
};

// garden-graph.js
const graph = {
  data: null,           // parsed JSON
  simulation: null,     // d3 forceSimulation; null until first open
  panelOpen: false,
  filters: { tag: 'all', stage: 'all', local: 'all' /* all | 1-hop | 2-hop */ },
  inStack: new Set(),   // slugs currently in stack; updated via 'garden:stack-changed' event
};
```

### 3.7 Custom events

- `garden:stack-changed` — dispatched by `garden-stack.js` on every stack mutation; `event.detail = { slugs: [...] }`. Listened by `garden-graph.js` to update bold-stroke node markers.
- `garden:graph-toggled` — dispatched by `garden-graph.js`; `event.detail = { open: true | false }`. Reserved for future surfaces; not consumed in this slice.

### 3.8 CSS additions to `main.css`

| Section | Contents |
|---|---|
| **§24 Path log + consent banner** | Sticky header positioning (`position: sticky; top: 0`), background, dashed underline on crumbs, action buttons, consent banner row above |
| **§25 Stacked columns** | `display: grid; grid-auto-flow: column; grid-auto-columns: 430px; overflow-x: auto; scroll-snap-type: x mandatory; scroll-behavior: smooth (or auto when reduced)`. Active column highlight via `.is-active`. Mobile (`@media (max-width: 720px)`): collapse to single-column — `grid-auto-columns: 1fr`, no horizontal scroll, all stack JS no-ops |
| **§26 Links section** | `border-top: 1px dashed var(--ink-soft); padding-top: var(--space-3); h2` styled like a small label; tight `<ul>` |
| **§27 Graph panel** | `position: fixed; right: 0; top: 0; bottom: 0; width: 280px; transform: translateX(100%)` on hidden state; `transform: translateX(0)` open; `transition: transform 200ms ease-out` (no transition under reduced-motion). Filters row inside; SVG fills remaining height |
| **§28 Graph page** | Full-viewport SVG container (`min-height: 70vh`); toolbar + legend rows; same color tokens as panel |

No new color tokens; contrast checker stays green.

---

## 4. Linter contract

`tools/check_garden_links.py`:

1. Walk `content/garden/*/index.md`, parsing frontmatter + body via the shared `parse_frontmatter` helper imported from `tools/check_fixtures.py`.
2. For each fixture, extract every `/garden/<target-slug>/` reference from the raw body using the same regex pattern Hugo's `findRE` uses (`r'/garden/([a-z0-9-]+)/'`).
3. For each target slug: verify `content/garden/<target-slug>/index.md` exists AND its frontmatter `draft` is `false` (or absent).
4. Self-references (slug == target) emit a **warning** to stderr but do not fail the linter — these are usually typos, but not strictly broken.
5. Targets that resolve outside `content/garden/` are not the linter's concern (no error, no warning) — the regex is anchored to `/garden/`.
6. Exit code 0 on success; exit code 1 on any unresolved or draft target with a line-numbered error message printed to stderr.

`tools/test_check_garden_links.py`: covers resolved link, missing target, draft target, self-reference (warning), multiple references in one file, no-references file, malformed slug ignored.

Wired into `.github/workflows/hugo.yaml`:

```
… Verify garden fixtures
… Run garden linter unit tests
+ Verify garden links               (new)
+ Run garden links linter unit tests (new)
… Verify filter-chips config
```

---

## 5. Stack interaction model

### 5.1 Activation (eager Matuschak)

On every `/garden/<slug>/` page:
- Server renders `<article class="garden-note garden-stack">` with one `<article class="garden-column>` inside (the URL note)
- Path log renders inline above the columns container with a single crumb (`Garden › <Title>`) and `1 in stack`
- `garden-stack.js` initializes from URL `?stack=` parameter:
  - **Normalization rule:** `stack.slugs` always starts with the URL slug (column 0). The `?stack=` parameter is treated as additional columns appended after column 0, in declaration order. Any occurrence of the URL slug in `?stack=` is dropped (deduped). So `/garden/d/?stack=a,b,c` → `[d, a, b, c]`; `/garden/d/?stack=a,d,c` → `[d, a, c]`; `/garden/d/?stack=d` → `[d]`.
  - For each slug at index ≥ 1 → fetch in parallel (`Promise.all`), extract the column fragment, append, then dispatch `garden:stack-changed` once
  - If a slug in `?stack=` doesn't resolve (404 fetch) → drop it silently; remaining slugs still render
  - URL is rewritten via `history.replaceState` after init if normalization changed the stack (e.g., a duplicate or invalid slug was dropped)

### 5.2 Click interception

Delegated `click` listener on `.garden-stack`:
- Match anchor whose `href` resolves to `/garden/<slug>/` (`new URL(a.href, location.href)` to handle relative links)
- `event.preventDefault()`
- If slug already in `stack.slugs`:
  - Find the existing column (`[data-slug="<slug>"]`); `scrollIntoView({behavior: motionPref(), inline: 'start'})`
  - Mark that column `.is-active`; remove `.is-active` from others
  - No URL change; no event dispatch
- Else:
  - `fetch('/garden/<slug>/')`, `DOMParser` parse, extract `.garden-note .garden-column[data-slug="<slug>"]`. If selector misses (e.g., redirect), fall back to whole `.garden-note article`
  - Remove path log + nested stack container from the extracted fragment (only the column body is wanted)
  - `appendChild` to `.garden-stack-columns`; `.is-active` migrates to new column
  - `scrollIntoView({behavior: motionPref(), inline: 'start'})`
  - Append slug to `stack.slugs`; rewrite URL with `history.replaceState(null, '', '?stack=' + stack.slugs.join(','))`
  - Dispatch `garden:stack-changed`
  - On first 1→2 expansion AND `path-log-consent === 'unset'` → render consent banner

### 5.3 Path-log clear / Esc

Both behave identically:
- Drop columns where `data-slug !== slugs[0]` from DOM
- `stack.slugs = [stack.slugs[0]]`
- `history.replaceState(null, '', location.pathname)` (strip query)
- Dispatch `garden:stack-changed`
- Move focus to column 1's `<h1>` (`tabindex="-1"` + `focus()`)

Esc disambiguation:
- If graph panel is open AND active element is inside it → close panel, return focus to toggle button
- Else if `stack.slugs.length >= 2` → execute clear-stack as above
- Else → no-op

### 5.4 Consent banner

Rendered as `<aside role="dialog" aria-label="Track reading path">` directly above the path log when:
1. Stack count transitions from 1 to 2 for the first time within this session, AND
2. `localStorage.getItem('path-log-consent')` is null

Three buttons (`Yes, persist`, `Just this session`, `No, never`):
- **Yes, persist** → `localStorage.setItem('path-log-consent', 'yes')`; `consent = 'yes'`. From now on, every stack mutation appends to `localStorage["garden-path-log"]` (capped at 100 entries, FIFO eviction)
- **Just this session** → `localStorage.setItem('path-log-consent', 'session')`; `consent = 'session'`. Same write behavior but to `sessionStorage` instead
- **No, never** → `localStorage.setItem('path-log-consent', 'no')`; `consent = 'no'`. No path-log writes happen at any time
- After any choice, banner is removed from DOM

The banner does not re-render on subsequent visits — the choice is persistent.

### 5.5 Mobile concession

Below 720px viewport width:
- CSS §25 collapses the columns container to single-column rendering (`grid-auto-columns: 1fr; overflow-x: visible`)
- `garden-stack.js` checks `matchMedia('(max-width: 720px)').matches` on init; if mobile:
  - Click interceptor not installed — links navigate normally
  - `?stack=` parameter is ignored (URL stays as-is, but only column 1 renders)
  - Path log still renders with current crumb (no `clear` button — nothing to clear)
- `/garden/graph/` page is the entry point on mobile; toggling the panel from the path log button takes the user to that page instead of opening a panel (the toggle is a real `<a href="/garden/graph/">` on mobile)

---

## 6. Graph view

### 6.1 Surfaces

The same `garden-graph.js` mounts on three surfaces:
1. **Side panel** — slid in from right on desktop garden index + note pages; toggled by `⊞ Graph` button
2. **Mobile** — same `<button class="garden-graph-toggle">` element in the rendered HTML, but the JS checks `matchMedia('(max-width: 720px)').matches` on click and navigates to `/garden/graph/` instead of toggling the panel. The toggle is therefore not viewport-conditionally rendered server-side; behavior switching lives entirely in JS.
3. **`/garden/graph/` page** — full-viewport rendering, accessible directly on any viewport as a deep-linkable URL. On this surface, the page itself IS the graph; no panel scaffolding rendered.

### 6.2 Filter dimensions

- **Tag** chips (multi-select, AND, matches the filter-chips slice convention) — first tag of each node is its primary; node visibility = primary tag is in selected set OR set is empty
- **Stage** chips (single-active among seedling / budding / evergreen / All)
- **Local mode** (note pages only — disabled on index, where there's no focus): all / 1-hop / 2-hop. BFS from the URL slug; restrict nodes to `dist <= N`; restrict edges to those with both endpoints in the restricted set
- "All" chips clear their dimension

Filter changes re-init the simulation rather than just hiding nodes — d3-force layouts assume the node set is stable. Reduced-motion: re-init still runs 300 ticks, just no animation.

### 6.3 Visual encoding

- Node fill = primary tag color (mapping derived from a small `tagColors` object in `garden-graph.js`; orphan nodes / tags not in the map use the `--ink-soft` token)
- Node radius = `5 + degree * 1.5` (clamped 5..16); orphans get the minimum
- Node stroke = bold (`var(--ink)`, 2.5px) when slug is in `inStack`; thin (1px) otherwise
- Edge stroke = `--ink-soft`; same-topic edges solid; cross-topic edges `stroke-dasharray: 4 3`
- SVG `viewBox` set to fit the simulation's bounding box on freeze; resizes on window resize (re-fit, no re-simulate)

### 6.4 Reduced motion

- `matchMedia('(prefers-reduced-motion: reduce)').matches` → `simulation.tick()` 300 times then `simulation.stop()`; no rAF loop
- Panel slide animation: under reduced-motion, CSS `transition: none`; transform jumps to open/closed state

### 6.5 Keyboard accessibility

- Panel toggle button: standard `<button>` semantics; `aria-expanded` reflects state; Esc when focus is inside panel closes panel
- SVG nodes: each `<g class="graph-node" tabindex="0" role="link" aria-label="Open '<title>' in stack">`. Enter / Space activates (full nav to that note's URL)
- Tab order: enter panel → close button → filter chips → first node → second node … → exit panel
- On `/garden/graph/` page: same node interaction; toolbar precedes canvas in tab order

---

## 7. Fixture extension

### 7.1 Edge plan (~28 edges across 14 nodes)

**Procedural-narrative cluster (within-topic, solid edges):**
- salience-and-memory ↔ surprise-budget *(surprise-budget→salience already exists; add reverse + others)*
- surprise-budget → story-atoms
- story-atoms → emergence-vs-design
- emergence-vs-design → procedural-narrative *(owner)*
- salience-and-memory → emergence-vs-design
- emergence-vs-design → surprise-budget
- story-atoms → salience-and-memory
- procedural-narrative → salience-and-memory *(already exists)*

**Memory-and-recall cluster (within-topic, solid edges):**
- recall-vs-replay ↔ sleep-and-consolidation
- sleep-and-consolidation → memory-in-play *(owner)*
- memory-in-play → recall-vs-replay
- the-save-game → recall-vs-replay
- memory-in-play → the-save-game

**Cross-topic edges (dashed):**
- salience-and-memory ↔ memory-in-play
- recall-vs-replay → salience-and-memory
- surprise-budget → recall-vs-replay
- outer-wilds → salience-and-memory
- outer-wilds → recall-vs-replay
- severance-s2 → memory-in-play
- severance-s2 → recall-vs-replay
- invisible-cities ↔ story-atoms
- invisible-cities → emergence-vs-design
- koyaanisqatsi-soundtrack → emergence-vs-design
- story-atoms → koyaanisqatsi-soundtrack

**Deliberate orphan (no in/out garden links):** `nguyen-2020-games-as-art`

Resulting degree distribution: salience-and-memory deg 7 (hub), memory-in-play deg 5, recall-vs-replay deg 5, story-atoms deg 5, emergence-vs-design deg 5, surprise-budget deg 4, others deg 1–3, nguyen deg 0.

### 7.2 Insertion discipline

Each link is inserted into an existing lorem-ipsum sentence as a markdown link. No authored prose, no sentence rephrasing beyond what's needed to attach the link. Example:

```diff
- Lorem ipsum dolor sit amet, consectetur adipiscing elit.
+ Lorem ipsum dolor sit amet — see also [salience and memory](/garden/salience-and-memory/) — consectetur adipiscing elit.
```

When Phase 3's elisp pipeline overwrites bodies wholesale, the test surface (which slugs link to which) is preserved by the linter's resolved-set check, not by specific text positions.

---

## 8. Performance budget (advisory, per parent §8)

- **`d3-force` minified** ≈ 30 KB · loaded via dynamic `import()` on first panel open · note pages without panel toggle don't pay the cost
- **`garden-stack.js` + `garden-graph.js` source** ≈ 7 KB combined uncompressed
- **Inline graph JSON** ≈ 3–5 KB for 14 nodes / 28 edges
- **Total Phase 4 weight on a note page that doesn't open the graph**: < 8 KB
- **With graph open**: ≈ 38 KB

---

## 9. Accessibility

- Path log: `<nav aria-label="Reading path">`; crumbs are `<a>` elements with `aria-current="page"` on the rightmost (active) crumb
- Stack column append: focus moved to new column's `<h1 tabindex="-1">` so screen readers announce the change
- Each column wrapped in `<article aria-labelledby="col-heading-N">`
- Graph panel: `role="region" aria-label="Garden graph"`; close button `aria-label="Close graph panel"`; `aria-hidden` reflects state; not modal (no focus trap)
- Graph SVG: `role="img" aria-label="Force-directed graph of N notes…"` + hidden `<desc>` summarizing cluster structure
- Graph nodes: `role="link" tabindex="0" aria-label="Open <title> in stack"`; Enter / Space activate
- Color is augmented by labels and edge style — never the only signal (CLAUDE.md hard constraint)
- Reduced motion: graph simulation freezes after 300 ticks; column scroll-snap uses `scroll-behavior: auto`; panel transition disabled
- Consent banner: `<aside role="dialog" aria-label="Track reading path">`; explicit choice required to write storage

---

## 10. Implementation order

1. **Fixture extension + new linter** — add link references to fixtures; write `check_garden_links.py` + tests; verify linter catches a deliberately-broken case before fixing it
2. **Build-time graph data partial** — implement `partials/garden/graph-data.html`; verify JSON shape with `hugo --renderToMemory` + browser inspect
3. **Links section partial** — implement `links-section.html`; render outgoing + backlinks at column bottom; visual check
4. **Path log partial + CSS §24 + §25** — render path log (server-side single-column); add stack columns CSS; verify mobile collapse below 720px
5. **`garden-stack.js`** — eager init, click interception, fetch+append, URL sync, clear/Esc, mobile no-op; manual browser walkthrough
6. **Consent banner** — wire into stack runtime; verify storage shape; test all three choices
7. **Graph panel partial + CSS §27** — empty panel scaffold; toggle button; verify slide-in transform on desktop, link-to-page on mobile
8. **`garden-graph.js`** — d3-force render, panel mount, filter chips, in-stack markers via custom event
9. **Local-graph mode** — BFS subgraph; chip group integration
10. **Graph page (`graph.html`) + CSS §28** — separate-page rendering reusing same JSON + module
11. **CI workflow update** — insert two new steps; verify green build
12. **Documentation** — CLAUDE.md commands + architecture + project status

Each step ends with a `hugo server` walkthrough confirming no regression in the prior step's surfaces.

---

## 11. Open questions

These are residual; none block implementation but are flagged so the plan can resolve them with the user when relevant:

1. **Backlink ordering** — alphabetical by source title or by source `last_modified` desc? Recommend: by `last_modified` desc (most recently tended back-references first), matches the "recent activity" intuition.
2. **Same-page anchors in fetched columns** — when extracting `<article>` from a fetched note, in-body anchor links (`<a href="#section">`) should resolve to that column's anchors, not the page-level ones. Plan: rewrite anchor `href`s during DOM extraction by prefixing with `?stack=…#col-<slug>-<id>`. Decide during step 5; flag if it gets hairy.
3. **Path-log overflow on long stacks** — at ≥ 6 columns the path log might wrap or overflow on narrow desktop. Easy: ellipsize middle entries with a "…" expander. Defer the polish; flag when first observed in dev.
4. **Persistent panel state across pages** — `sessionStorage["garden-graph-open"]` is per-tab. If user opens the panel on `/garden/foo/` then navigates to `/garden/bar/`, the panel re-opens. Confirm this is desired (it matches "the graph is a tool I'm using right now" intuition) — recommend keep as-is.
5. **Graph node click vs scroll** — on touch devices, momentum scroll over an SVG can fire unintended click. Implement with a small `touch-move` threshold; flag in step 8 if regressions surface.

---

## 12. Cross-references to other slices

- **Phase 3 (org-mode pipeline)** drops in `data/notes.json` produced by ox-hugo; the `partials/garden/graph-data.html` partial is retired and replaced with `{{ site.Data.notes | jsonify }}`. JS contract unchanged.
- **Phase 5 (research)** will likely build on the same `garden-graph.js` simulation primitives. Plan for that slice should consider extracting a generic `assets/js/force-graph.js` then; this slice does not pre-extract.
- **Phase 7 (library)** cross-links from media-flavor garden notes will reuse the same outgoing-link extraction; the linter may need to allow `/library/` targets as a side-effect.
- **Phase 8 (Pagefind)** indexing must skip the duplicated content inside appended stacked columns (otherwise a single search hit could match all visible columns). Tag the appended columns with `data-pagefind-ignore` when JS appends — flagged for the Pagefind slice.

---

*End of spec.*
