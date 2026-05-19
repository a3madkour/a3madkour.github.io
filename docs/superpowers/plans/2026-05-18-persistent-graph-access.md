# Persistent Graph Access (research + works) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the graph a persistent, re-openable companion (with retained state) on every research and works item page, the way garden already does it, via one shared sticky launcher bar consistent across garden + research + works.

**Architecture:** `research-graph.js` / `works-graph.js` already carry garden's full panel-persistence machinery (sessionStorage open-state, un-animated restore on init, navigate-on-node-click, mobile→standalone fallback). This slice is mostly wiring: a new shared `graph-launcher-bar.html` partial (variant-switched: a `garden` branch that reproduces the existing path-log DOM verbatim, and a `generic` branch for research/works), included on the 5 item single layouts; bundle-predicate widening so the d3 graph bundle loads on those pages; an `is-here` current-node marker for research/works; and an extension of the `check_graph_chrome.py` gate to the new surfaces.

**Tech Stack:** Hugo (extended ≥ 0.148.0) templates/partials, hand-rolled CSS (`assets/css/main.css`, numbered sections), vanilla ES modules (no npm), Python stdlib linters, `tools/ci-local.sh` as the CI mirror.

---

## File Structure

**Create:**
- `layouts/partials/graph-launcher-bar.html` — the single shared sticky-bar + left-aligned `⊞ Graph` launcher. Variant `garden` reproduces today's path-log DOM (class `garden-path-log` + all `.path-log-*` children + `data-slug`, kept verbatim for `garden-stack.js` / `garden-pathlog-popover.js` / `check_garden_history.py`); variant `generic` renders a structured breadcrumb from a `crumbs` slice and emits `data-graph-current` for the `is-here` marker.

**Modify:**
- `layouts/partials/garden/path-log.html` — becomes a one-line delegator to the shared partial (keeps the existing `{{ partial "garden/path-log.html" . }}` call site in `garden/single.html` untouched).
- `layouts/research-theme/single.html` — render shared bar + research graph panel/script; drop the inline `.research-breadcrumb`.
- `layouts/research-question/single.html` — same.
- `layouts/works-games/single.html`, `layouts/works-music/single.html`, `layouts/works-poetry/single.html` — render shared bar + works graph panel/script (these gain a breadcrumb they lack today).
- `layouts/partials/scripts.html` — widen the research + works bundle predicates so the d3 graph bundle loads on item pages.
- `assets/css/main.css` — move the sticky-bar shell from `.garden-path-log` (§24) to a shared `.graph-launcher-bar` (§27); add launcher/crumb layout + `is-here` node emphasis.
- `assets/js/research-graph.js` — read `data-graph-current` into `state.page.currentSlug`; add `is-here` class in node render.
- `assets/js/works-graph.js` — same.
- `tools/check_graph_chrome.py` — extend the gate to the 5 new item-page surfaces.

---

## Task 1: Shared launcher-bar partial

**Files:**
- Create: `layouts/partials/graph-launcher-bar.html`

- [ ] **Step 1: Write the shared partial**

Create `layouts/partials/graph-launcher-bar.html` with exactly this content:

```html
{{- /* Shared sticky graph-launcher bar. One source of truth for the
       launcher chrome across garden + research + works.

       Params (dict):
         variant      — "garden" | "generic"
         panelId      — id of the <aside class="graph-panel"> this toggle controls
         page         — the Hugo Page (variant "garden" only)
         crumbs       — slice of dicts {label, url?} ; last entry = current
                         page (omit url) (variant "generic" only)
         currentSlug  — slug of the current page; emitted as data-graph-current
                         so <section>-graph.js can mark the "you are here" node
                         (variant "generic" only; garden has its own in-stack model)
         extraClass   — extra class(es) on the <nav> (variant "garden": the
                         literal "garden-path-log", preserved for garden JS +
                         the garden-history linter)

       The launcher is the FIRST child (left-aligned) so the fixed
       right-side .graph-panel (320px, user-resizable) never covers it.
       Sticky-bar shell CSS is .graph-launcher-bar (§27). */ -}}
{{- $variant := .variant -}}
{{- $panelId := .panelId -}}
{{- $extraClass := .extraClass | default "" -}}
<nav class="graph-launcher-bar{{ with $extraClass }} {{ . }}{{ end }}"
     aria-label="{{ if eq $variant "garden" }}Reading path{{ else }}Graph access{{ end }}"
     {{- if and (eq $variant "generic") .currentSlug }} data-graph-current="{{ .currentSlug }}"{{ end }}>
  <button type="button" class="graph-toggle" aria-expanded="false" aria-controls="{{ $panelId }}">⊞ Graph</button>
  {{- if eq $variant "garden" -}}
    {{- $p := .page -}}
    <span class="path-log-label">Path:</span>
    <a class="path-log-crumb" href="{{ "/garden/" | relURL }}">Garden</a>
    <span class="path-log-sep" aria-hidden="true">›</span>
    <a class="path-log-crumb is-active" aria-current="page" href="{{ $p.RelPermalink }}" data-slug="{{ path.Base $p.File.Dir }}">{{ $p.Title }}</a>
    <span class="path-log-actions">
      <span class="path-log-count" data-stack-count="1">1 in stack</span>
      <button type="button" class="path-log-clear" hidden>clear</button>
      <a class="path-log-history" href="{{ "/garden/history/" | relURL }}">history</a>
    </span>
  {{- else -}}
    <span class="graph-launcher-crumbs">
      {{- $n := len .crumbs -}}
      {{- range $i, $c := .crumbs -}}
        {{- if $c.url -}}
          <a class="graph-launcher-crumb" href="{{ $c.url | relURL }}">{{ $c.label }}</a>
        {{- else -}}
          <span class="graph-launcher-crumb is-active" aria-current="page">{{ $c.label }}</span>
        {{- end -}}
        {{- if lt (add $i 1) $n }}<span class="path-log-sep" aria-hidden="true">›</span>{{ end -}}
      {{- end -}}
    </span>
  {{- end -}}
</nav>
```

- [ ] **Step 2: Verify it parses (no call site yet — just template syntax)**

Run: `hugo --quiet --renderToMemory 2>&1 | head -20`
Expected: no `failed to parse` / `executeAsTemplate` error mentioning `graph-launcher-bar.html`. (An unused partial is not invoked, so this only catches syntax errors. It is wired up in Tasks 2–4.)

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/graph-launcher-bar.html
git commit -m "feat(graph): add shared graph-launcher-bar partial (variant-switched)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Garden path-log delegates to the shared partial (+ two regression fixes)

The garden branch of the shared partial reproduces the current `path-log.html` DOM (same `.garden-path-log` class via `extraClass`, same `.path-log-*` children, same `data-slug`), with one intended change: the `⊞ Graph` toggle moves from inside `.path-log-actions` to the first (left) child. **That relocation creates two regressions** (found in Task 1 code review, confirmed by reading the code), both fixed here in the same atomic task:

- **Fix A:** `assets/js/garden-stack.js` `updatePathLog()` (called at lines ~251/271/319 on every stack mutation) prunes every child of `.garden-path-log` that is not `.path-log-label`, `.path-log-actions`, or the `/garden/` anchor. The launcher used to survive because it lived *inside* `.path-log-actions`; as the nav's first child it would be **deleted on the first stack rebuild**, defeating the feature exactly during garden traversal. Add the launcher to the keep-set.
- **Fix B:** `tools/check_garden_history.py` assertion 5 asserts the literal `/garden/history/` lives in `layouts/partials/garden/path-log.html`. After delegation that string moves into `graph-launcher-bar.html`; the gate (and its paired `test_check_garden_history.py`, which hard-codes the path-log expectation at line ~141) would fail. Retarget assertion 5 + its paired test to the link's real new home — no fake reference comment in the delegator.

`garden-pathlog-popover.js` (selects `.path-log-count` / `.path-log-crumb.is-active[data-slug]`) and `garden-graph.js` (selects `.graph-toggle` globally) are genuinely unaffected — the preserved markup and the global toggle selector still work.

**Files:**
- Modify: `layouts/partials/garden/path-log.html` (full rewrite — 17 lines → delegator)
- Modify: `assets/js/garden-stack.js` (Fix A — `updatePathLog()` keep-set, ~line 144-150)
- Modify: `tools/check_garden_history.py` (Fix B — assertion 5 + docstring)
- Modify: `tools/test_check_garden_history.py` (Fix B — paired-test fixture + retargeted case)

- [ ] **Step 1: Replace path-log.html with the delegator**

Replace the entire contents of `layouts/partials/garden/path-log.html` with:

```html
{{- /* Inputs:
       . — Hugo Page (the note being rendered)
   Delegates to the shared graph-launcher-bar (variant "garden"), which
   reproduces this nav's DOM verbatim (class .garden-path-log + .path-log-*
   children + data-slug) so garden-stack.js / garden-pathlog-popover.js
   keep working. The only change vs. the old inline markup: the ⊞ Graph
   launcher is now the left-most child (was inside .path-log-actions),
   matching research + works. The /garden/history/ chrome link now lives
   in graph-launcher-bar.html (its garden branch); check_garden_history.py
   assertion 5 tracks it there. */ -}}
{{ partial "graph-launcher-bar.html" (dict
    "variant" "garden"
    "panelId" "garden-graph-panel"
    "extraClass" "garden-path-log"
    "page" .
) }}
```

- [ ] **Step 2: Fix A — preserve the launcher across stack rebuilds**

In `assets/js/garden-stack.js`, find (in `updatePathLog()`, ~line 142-150):

```js
  const label = log.querySelector('.path-log-label');
  const actions = log.querySelector('.path-log-actions');
  const gardenAnchor = log.querySelector('.path-log-crumb[href$="/garden/"]');

  // Clear everything between label and actions, except the static "Garden" anchor
  Array.from(log.children).forEach(child => {
    if (child !== label && child !== actions && child !== gardenAnchor) {
      log.removeChild(child);
    }
  });
```

Replace with:

```js
  const label = log.querySelector('.path-log-label');
  const actions = log.querySelector('.path-log-actions');
  const gardenAnchor = log.querySelector('.path-log-crumb[href$="/garden/"]');
  // The ⊞ Graph launcher is now the bar's first child (shared
  // graph-launcher-bar). It is persistent chrome — never prune it.
  const toggle = log.querySelector('.graph-toggle');

  // Clear everything between label and actions, except the static "Garden"
  // anchor and the persistent graph launcher.
  Array.from(log.children).forEach(child => {
    if (child !== label && child !== actions && child !== gardenAnchor && child !== toggle) {
      log.removeChild(child);
    }
  });
```

- [ ] **Step 3: Fix B — retarget the linter assertion**

In `tools/check_garden_history.py`, the module docstring line currently reads:

```
  5. layouts/partials/garden/path-log.html references /garden/history/.
```

Replace it with:

```
  5. layouts/partials/graph-launcher-bar.html references /garden/history/
     (the garden branch of the shared launcher bar; path-log.html delegates
     to it).
```

Then find assertion 5's code:

```python
    # 5: path-log.html links to /garden/history/
    pathlog = project_root / "layouts/partials/garden/path-log.html"
    if pathlog.is_file():
        text = pathlog.read_text(encoding="utf-8")
        if "/garden/history/" not in text:
            errors.append("layouts/partials/garden/path-log.html: missing chrome link to /garden/history/")
    else:
        errors.append("layouts/partials/garden/path-log.html: missing")
```

Replace with:

```python
    # 5: the shared launcher bar (garden branch) links to /garden/history/
    launcher = project_root / "layouts/partials/graph-launcher-bar.html"
    if launcher.is_file():
        text = launcher.read_text(encoding="utf-8")
        if "/garden/history/" not in text:
            errors.append("layouts/partials/graph-launcher-bar.html: missing chrome link to /garden/history/")
    else:
        errors.append("layouts/partials/graph-launcher-bar.html: missing")
```

- [ ] **Step 4: Fix B — update the paired test**

In `tools/test_check_garden_history.py`:

(a) After the `PATHLOG_PARTIAL = """..."""` block (~line 49), add a fixture for the shared bar:

```python
GRAPH_LAUNCHER_BAR_PARTIAL = """\
<nav class="graph-launcher-bar garden-path-log">
  <button type="button" class="graph-toggle">⊞ Graph</button>
  <a class="path-log-history" href="{{ "/garden/history/" | relURL }}">history</a>
</nav>
"""
```

(b) In `_layout_fixture`'s `files` dict, add the new file alongside the path-log entry:

```python
        "layouts/partials/garden/path-log.html": PATHLOG_PARTIAL,
        "layouts/partials/graph-launcher-bar.html": GRAPH_LAUNCHER_BAR_PARTIAL,
```

(c) Replace the whole `test_pathlog_missing_history_link` method with a retargeted case:

```python
    def test_launcher_bar_missing_history_link(self):
        bad = "<nav class=\"graph-launcher-bar garden-path-log\"></nav>\n"
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"layouts/partials/graph-launcher-bar.html": bad})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("graph-launcher-bar.html" in e and "/garden/history/" in e for e in errors),
                            f"expected 'graph-launcher-bar missing /garden/history/', got: {errors}")
```

- [ ] **Step 5: Build and confirm garden DOM is preserved**

Run:
```bash
hugo --quiet --destination /tmp/pga-build
grep -o 'class="graph-launcher-bar garden-path-log"' /tmp/pga-build/garden/*/index.html | head -1
grep -o 'class="path-log-crumb is-active"' /tmp/pga-build/garden/*/index.html | head -1
grep -o 'class="path-log-count" data-stack-count="1"' /tmp/pga-build/garden/*/index.html | head -1
grep -o 'class="path-log-history"' /tmp/pga-build/garden/*/index.html | head -1
grep -o '/garden/history/' layouts/partials/graph-launcher-bar.html | head -1
```
Expected: the first four `grep`s each print one match (garden DOM intact); the fifth confirms the history link now lives in the shared partial.

- [ ] **Step 6: Run the garden-history gate + paired test + a launcher-survives-prune check**

Run:
```bash
python3 tools/check_garden_history.py
python3 -m unittest tools/test_check_garden_history.py 2>&1 | tail -1
node -e '
const fs=require("fs");
const src=fs.readFileSync("assets/js/garden-stack.js","utf8");
if(!/const toggle = log\.querySelector\(.\.graph-toggle.\);/.test(src)) { console.error("FAIL: keep-set toggle lookup missing"); process.exit(1); }
if(!/child !== toggle/.test(src)) { console.error("FAIL: prune guard missing child !== toggle"); process.exit(1); }
console.log("OK: Fix A guard present");
' 2>/dev/null || grep -q "child !== toggle" assets/js/garden-stack.js && echo "OK: Fix A guard present"
```
Expected: `check_garden_history: OK`; unittest prints `OK`; `OK: Fix A guard present`. (The last line falls back to `grep` if `node` is unavailable — no npm in this repo; `node` may or may not be on PATH. Either path must print the OK line.)

- [ ] **Step 7: Commit**

```bash
git add layouts/partials/garden/path-log.html assets/js/garden-stack.js tools/check_garden_history.py tools/test_check_garden_history.py
git commit -m "refactor(graph): garden path-log delegates to shared launcher-bar

Fix A: garden-stack.js updatePathLog() keep-set guards the relocated
  ⊞ Graph launcher (now the bar's first child) from being pruned on
  stack rebuilds.
Fix B: check_garden_history.py assertion 5 + paired test track the
  /garden/history/ chrome link at its new home (graph-launcher-bar.html).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Sticky-bar shell + launcher/crumb + is-here CSS

Move the sticky-bar shell off `.garden-path-log` (§24) onto the shared `.graph-launcher-bar` (§27, where the canonical `.graph-toggle` already lives). Garden nodes now carry both classes (`graph-launcher-bar garden-path-log`), so garden keeps its shell via the shared rule; the garden-specific `.path-log-*` child rules stay in §24. Add `is-here` node emphasis (shape + color, never color-only — per spec §1 a11y).

**Files:**
- Modify: `assets/css/main.css` (§24 sticky block ~line 1157; §27 after `.graph-toggle` ~line 1399; research node rules ~§31 near line 2074; works node rules ~§36)

- [ ] **Step 1: Strip the shell from `.garden-path-log` in §24**

Find this block (currently ~line 1157):

```css
.garden-path-log {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem var(--page-gutter);
  border-bottom: 1px solid var(--color-rule);
  background: var(--color-tile);
  position: sticky;
  top: 0;
  z-index: 5;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  flex-wrap: wrap;
}
```

Replace it with (garden-only residue; the shell now comes from `.graph-launcher-bar`):

```css
/* .garden-path-log: garden-only residue. The sticky-bar shell now lives on
   the shared .graph-launcher-bar (§27); garden's nav carries both classes. */
.garden-path-log .path-log-label {
  /* (existing .path-log-* child rules below are unchanged) */
}
```

> Note: the block immediately following in the source is already
> `.garden-path-log .path-log-label { color: …; font-weight: 500; }`.
> To avoid an empty/duplicate selector, instead **delete** the
> `.garden-path-log { … }` rule entirely and leave the existing
> `.garden-path-log .path-log-label { … }` rule (next in the file) as the
> first garden-path-log rule. Net edit: remove the 13-line `.garden-path-log { … }` block; keep everything after it.

- [ ] **Step 2: Add the shared shell + crumb layout in §27**

In §27, immediately after the `.graph-toggle[aria-expanded="true"] { … }` rule (currently ends ~line 1399), insert:

```css
/* --- Shared sticky graph-launcher bar (garden + research + works).
       Shell migrated here from §24 .garden-path-log so all three sections
       share one source of truth. The launcher is the first child
       (left-aligned) so the fixed right-side .graph-panel never covers it. --- */
.graph-launcher-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem var(--page-gutter);
  border-bottom: 1px solid var(--color-rule);
  background: var(--color-tile);
  position: sticky;
  top: 0;
  z-index: 5;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  flex-wrap: wrap;
}
.graph-launcher-bar .graph-toggle {
  flex: 0 0 auto;
}
.graph-launcher-crumbs {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--color-ink-soft);
  min-width: 0;
}
.graph-launcher-crumb {
  color: var(--color-burgundy);
  text-decoration: none;
  border-bottom: 1px dotted var(--color-burgundy);
  padding-bottom: 1px;
}
.graph-launcher-crumb.is-active {
  color: var(--color-ink);
  font-weight: 600;
  border-bottom: none;
}
```

- [ ] **Step 3: Add `is-here` emphasis for research nodes**

Find the research node drag/state block (anchor: the selector `.research-graph-page .research-graph-canvas svg.is-dragging-node .research-graph-node` ~line 2074). Immediately **before** that anchor rule, insert:

```css
/* "You are here": the node for the current research item page. Shape
   (thicker stroke ring) + color, never color-only (spec §1 a11y). */
.research-graph-node.is-here circle,
.research-graph-node.is-here rect {
  stroke: var(--color-burgundy);
  stroke-width: 3px;
  paint-order: stroke;
}
.research-graph-node.is-here text {
  font-weight: 700;
}
```

- [ ] **Step 4: Add `is-here` emphasis for works nodes**

Find the works node badge selector `.works-graph-node-badge` in §36 (run `grep -n "works-graph-node-badge" assets/css/main.css | head -1` to locate the first definition). Immediately after that rule's closing brace, insert:

```css
/* "You are here": the node for the current works item page. Shape +
   color, never color-only (spec §1 a11y). */
.works-graph-node.is-here .works-graph-node-badge {
  stroke: var(--color-burgundy);
  stroke-width: 3px;
  paint-order: stroke;
}
.works-graph-node.is-here text {
  font-weight: 700;
}
```

- [ ] **Step 5: Build + contrast gate + verify CSS still fingerprints**

Run:
```bash
hugo --quiet --destination /tmp/pga-build
python3 tools/check-contrast.py
```
Expected: hugo build succeeds; `check-contrast` prints its PASS summary (the four checked pairings are untouched; `is-here` uses already-validated `--color-burgundy`).

- [ ] **Step 6: Commit**

```bash
git add assets/css/main.css
git commit -m "style(graph): shared .graph-launcher-bar shell + is-here node emphasis

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Research item layouts — bar + panel + script

`research-theme/single.html` and `research-question/single.html` already compute the slug/theme vars at the top of `{{ define "main" }}`. Render the shared bar **before** `<article>` (mirrors how `garden/single.html` renders path-log before `.garden-stack`), include the existing `research/graph-panel.html` + `research/graph-script.html` (the panel already pulls in the shared legend), and delete the now-redundant inline `.research-breadcrumb`.

**Files:**
- Modify: `layouts/research-theme/single.html`
- Modify: `layouts/research-question/single.html`

- [ ] **Step 1: research-theme — insert the bar before `<article>`**

In `layouts/research-theme/single.html`, the current line 16-17 is:

```html
{{- end -}}

<article class="reading-column research-theme-page">
```

Replace with:

```html
{{- end -}}

{{ partial "graph-launcher-bar.html" (dict
    "variant" "generic"
    "panelId" "research-graph-panel"
    "currentSlug" $thisSlug
    "crumbs" (slice
       (dict "label" "Research" "url" "/research/")
       (dict "label" .Title)
    )
) }}

<article class="reading-column research-theme-page">
```

- [ ] **Step 2: research-theme — delete the inline breadcrumb**

Delete this block (currently lines 38-41):

```html
  <nav class="research-breadcrumb" aria-label="Breadcrumb">
    <a href="/research/">Research</a> ›
    <span aria-current="page">{{ .Title }}</span>
  </nav>
```

- [ ] **Step 3: research-theme — add panel + script before `</article>`**

The file ends with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ end }}
```

Replace with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ partial "research/graph-panel.html" . }}
{{ partial "research/graph-script.html" .Site }}
{{ end }}
```

- [ ] **Step 4: research-question — insert the bar before `<article>`**

In `layouts/research-question/single.html`, line 36-37 is:

```html
{{- $myBacklinks := index $backlinksData $thisSlug | default slice -}}

<article class="reading-column research-question-hub">
```

Replace with:

```html
{{- $myBacklinks := index $backlinksData $thisSlug | default slice -}}

{{- $rqCrumbs := slice (dict "label" "Research" "url" "/research/") -}}
{{- if $themePage -}}
  {{- $rqCrumbs = $rqCrumbs | append (dict "label" $themePage.Title "url" $themePage.RelPermalink) -}}
{{- else -}}
  {{- $rqCrumbs = $rqCrumbs | append (dict "label" $themeSlug "url" "/research/") -}}
{{- end -}}
{{- $rqCrumbs = $rqCrumbs | append (dict "label" .Title) -}}
{{ partial "graph-launcher-bar.html" (dict
    "variant" "generic"
    "panelId" "research-graph-panel"
    "currentSlug" $thisSlug
    "crumbs" $rqCrumbs
) }}

<article class="reading-column research-question-hub">
```

- [ ] **Step 5: research-question — delete the inline breadcrumb**

Delete this block (currently lines 65-73):

```html
  <nav class="research-breadcrumb" aria-label="Breadcrumb">
    <a href="/research/">Research</a> ›
    {{ if $themePage }}
      <a href="{{ $themePage.RelPermalink }}">{{ $themePage.Title }}</a> ›
    {{ else }}
      <span>{{ $themeSlug }}</span> ›
    {{ end }}
    <span aria-current="page">{{ .Title }}</span>
  </nav>
```

- [ ] **Step 6: research-question — add panel + script before `</article>`**

The file ends with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ end }}
```

Replace with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ partial "research/graph-panel.html" . }}
{{ partial "research/graph-script.html" .Site }}
{{ end }}
```

- [ ] **Step 7: Build + research linters**

Run:
```bash
hugo --quiet --destination /tmp/pga-build
python3 tools/check_research_fixtures.py
python3 tools/check_research_links.py
grep -o 'class="graph-launcher-bar"' /tmp/pga-build/research/themes/*/index.html | head -1
grep -o 'data-graph-current="[^"]*"' /tmp/pga-build/research/themes/*/index.html | head -1
grep -o '⊞ Graph' /tmp/pga-build/research/questions/*/index.html | head -1
grep -c 'id="research-graph-panel"' /tmp/pga-build/research/questions/*/index.html | head -1
```
Expected: build succeeds; both linters print OK; the bar-class `grep` prints one match; the `data-graph-current` `grep` prints one match; the `⊞ Graph` `grep` prints one match; the panel `grep -c` prints `1`. (Greps test each attribute independently — Hugo renders the `<nav>`'s attributes across source lines, so a single combined-line grep would falsely fail even when correct.)

- [ ] **Step 8: Commit**

```bash
git add layouts/research-theme/single.html layouts/research-question/single.html
git commit -m "feat(graph): launcher bar + persistent panel on research item pages

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Works item layouts — bar + panel + script

Works game/music/poem single layouts have no breadcrumb today; they gain one. Pattern mirrors Task 4.

**Files:**
- Modify: `layouts/works-games/single.html`
- Modify: `layouts/works-music/single.html`
- Modify: `layouts/works-poetry/single.html`

- [ ] **Step 1: works-games — bar before `<article>`**

In `layouts/works-games/single.html`, line 1-2 is:

```html
{{ define "main" }}
<article class="page works-game-page">
```

Replace with:

```html
{{ define "main" }}
{{ partial "graph-launcher-bar.html" (dict
    "variant" "generic"
    "panelId" "works-graph-panel"
    "currentSlug" (path.Base .File.Dir)
    "crumbs" (slice
       (dict "label" "Works" "url" "/works/")
       (dict "label" "Games" "url" "/works/games/")
       (dict "label" .Title)
    )
) }}
<article class="page works-game-page">
```

- [ ] **Step 2: works-games — panel + script before `</article>`**

The file ends with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ end }}
```

Replace with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ partial "works/graph-panel.html" . }}
{{ partial "works/graph-script.html" . }}
{{ end }}
```

- [ ] **Step 3: works-music — bar before `<article>`**

In `layouts/works-music/single.html`, line 1-2 is:

```html
{{ define "main" }}
<article class="page works-music-page">
```

Replace with:

```html
{{ define "main" }}
{{ partial "graph-launcher-bar.html" (dict
    "variant" "generic"
    "panelId" "works-graph-panel"
    "currentSlug" (path.Base .File.Dir)
    "crumbs" (slice
       (dict "label" "Works" "url" "/works/")
       (dict "label" "Music" "url" "/works/music/")
       (dict "label" .Title)
    )
) }}
<article class="page works-music-page">
```

- [ ] **Step 4: works-music — panel + script before `</article>`**

The file ends with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ end }}
```

Replace with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ partial "works/graph-panel.html" . }}
{{ partial "works/graph-script.html" . }}
{{ end }}
```

- [ ] **Step 5: works-poetry — bar before `<article>`**

In `layouts/works-poetry/single.html`, line 1-2 is:

```html
{{ define "main" }}
<article class="page works-poem-page">
```

Replace with:

```html
{{ define "main" }}
{{ partial "graph-launcher-bar.html" (dict
    "variant" "generic"
    "panelId" "works-graph-panel"
    "currentSlug" (path.Base .File.Dir)
    "crumbs" (slice
       (dict "label" "Works" "url" "/works/")
       (dict "label" "Poetry" "url" "/works/poetry/")
       (dict "label" .Title)
    )
) }}
<article class="page works-poem-page">
```

- [ ] **Step 6: works-poetry — panel + script before `</article>`**

The file ends with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ end }}
```

Replace with:

```html
  {{ partial "cite/static-fallback.html" . }}
  {{ partial "cite/data-blob.html" . }}
</article>
{{ partial "works/graph-panel.html" . }}
{{ partial "works/graph-script.html" . }}
{{ end }}
```

- [ ] **Step 7: Build + works linters**

Run:
```bash
hugo --quiet --destination /tmp/pga-build
python3 tools/check_works_fixtures.py
python3 tools/check_works_links.py
grep -o 'data-graph-current="[^"]*"' /tmp/pga-build/works/games/*/index.html | head -1
grep -c 'id="works-graph-panel"' /tmp/pga-build/works/poetry/*/index.html | head -1
```
Expected: build succeeds; both linters print OK; `data-graph-current` `grep` prints one match; panel `grep -c` prints `1`.

- [ ] **Step 8: Commit**

```bash
git add layouts/works-games/single.html layouts/works-music/single.html layouts/works-poetry/single.html
git commit -m "feat(graph): launcher bar + persistent panel on works item pages

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Widen bundle predicates so d3 graph JS loads on item pages

The shared bar + panel are inert without `research-graph.js` / `works-graph.js`. Today `entry-research.js` loads only on `/research/` + `/research/graph/`; `entry-works-umbrella.js` only on `/works/` + `/works/graph/`. Widen both. Works single pages switch to the d3 umbrella bundle (they have no filter-chip strip, so they don't need `entry-works.js`); works sub-index list pages keep `entry-works.js`.

**Files:**
- Modify: `layouts/partials/scripts.html` (research predicate ~lines 30-37; works predicate ~lines 39-51)

- [ ] **Step 1: Widen the research predicate**

Find (currently lines 30-37):

```html
{{- $loadResearch := or
     (and (eq .Section "research") (eq .Kind "section"))
     (and (eq .Section "research") (eq .Layout "graph")) -}}
{{- if $loadResearch }}
{{- $researchOpts := dict "targetPath" "js/research.js" "minify" true -}}
{{- $research := resources.Get "js/entry-research.js" | js.Build $researchOpts | fingerprint }}
<script src="{{ $research.RelPermalink }}" integrity="{{ $research.Data.Integrity }}" defer></script>
{{- end }}
```

Replace the `$loadResearch` definition line(s) with a section-wide predicate (graph JS now lives on every research page — index, theme, question, standalone graph):

```html
{{- /* Graph JS on every research page: index + standalone graph (as before)
       AND theme/question item pages, so the panel survives node-click
       traversal (persistent-graph-access slice). */ -}}
{{- $loadResearch := eq .Section "research" -}}
{{- if $loadResearch }}
{{- $researchOpts := dict "targetPath" "js/research.js" "minify" true -}}
{{- $research := resources.Get "js/entry-research.js" | js.Build $researchOpts | fingerprint }}
<script src="{{ $research.RelPermalink }}" integrity="{{ $research.Data.Integrity }}" defer></script>
{{- end }}
```

- [ ] **Step 2: Widen the works predicate**

Find (currently lines 39-51):

```html
{{- /* Works split:
       umbrella + standalone graph → entry-works-umbrella.js (~110 KB w/ d3)
       per-item works pages       → entry-works.js (~6 KB, no d3) */ -}}
{{- $isUmbrella := or (eq .RelPermalink "/works/") (eq .RelPermalink "/works/graph/") -}}
{{- if $isUmbrella }}
{{- $worksUmbOpts := dict "targetPath" "js/works-umbrella.js" "minify" true -}}
{{- $worksUmb := resources.Get "js/entry-works-umbrella.js" | js.Build $worksUmbOpts | fingerprint }}
<script src="{{ $worksUmb.RelPermalink }}" integrity="{{ $worksUmb.Data.Integrity }}" defer></script>
{{- else if eq .Section "works" }}
{{- $worksOpts := dict "targetPath" "js/works.js" "minify" true -}}
{{- $works := resources.Get "js/entry-works.js" | js.Build $worksOpts | fingerprint }}
<script src="{{ $works.RelPermalink }}" integrity="{{ $works.Data.Integrity }}" defer></script>
{{- end }}
```

Replace with:

```html
{{- /* Works split:
       umbrella + standalone graph + per-item single pages
                                  → entry-works-umbrella.js (~112 KB w/ d3),
                                    so the graph panel survives node-click
                                    traversal (persistent-graph-access slice).
                                    Single pages have no filter-chip strip, so
                                    they don't need entry-works.js.
       works sub-index list pages → entry-works.js (~6 KB, no d3) */ -}}
{{- $isUmbrella := or (eq .RelPermalink "/works/") (eq .RelPermalink "/works/graph/") -}}
{{- $loadWorksUmb := or $isUmbrella (and (eq .Section "works") (eq .Kind "page")) -}}
{{- if $loadWorksUmb }}
{{- $worksUmbOpts := dict "targetPath" "js/works-umbrella.js" "minify" true -}}
{{- $worksUmb := resources.Get "js/entry-works-umbrella.js" | js.Build $worksUmbOpts | fingerprint }}
<script src="{{ $worksUmb.RelPermalink }}" integrity="{{ $worksUmb.Data.Integrity }}" defer></script>
{{- else if eq .Section "works" }}
{{- $worksOpts := dict "targetPath" "js/works.js" "minify" true -}}
{{- $works := resources.Get "js/entry-works.js" | js.Build $worksOpts | fingerprint }}
<script src="{{ $works.RelPermalink }}" integrity="{{ $works.Data.Integrity }}" defer></script>
{{- end }}
```

- [ ] **Step 3: Build + confirm the bundle is referenced on item pages**

Run:
```bash
hugo --minify --quiet --destination /tmp/pga-build
grep -o 'js/research\.[a-f0-9]*\.js' /tmp/pga-build/research/themes/*/index.html | head -1
grep -o 'js/works-umbrella\.[a-f0-9]*\.js' /tmp/pga-build/works/games/*/index.html | head -1
grep -L 'js/works-umbrella' /tmp/pga-build/works/games/index.html
```
Expected: first two `grep`s each print one fingerprinted filename (bundle now loads on a research theme + a works game page); the third (`grep -L` on the works **games index** list page) prints the filename, confirming the sub-index list page did **not** get the umbrella bundle (it still uses `entry-works.js`).

- [ ] **Step 4: Commit**

```bash
git add layouts/partials/scripts.html
git commit -m "build(graph): load d3 graph bundle on research+works item pages

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: `is-here` current-node marker in the graph JS

`research-graph.js` / `works-graph.js` already set `state.page.isMobile` in `init()` and build nodes with `g.dataset.slug = n.slug`. Read the bar's `data-graph-current` into `state.page.currentSlug`, then add the `is-here` class to the matching node.

**Files:**
- Modify: `assets/js/research-graph.js` (`init()` ~line 708; node class ~line 291)
- Modify: `assets/js/works-graph.js` (`init()` ~line 673; node class ~line 327)

- [ ] **Step 1: research-graph.js — capture the current slug in `init()`**

Find (currently ~line 708, inside `init()`):

```js
  state.panel = document.getElementById('research-graph-panel');
  state.page.isMobile = isMobile();
```

Replace with:

```js
  state.panel = document.getElementById('research-graph-panel');
  state.page.isMobile = isMobile();
  const hereBar = document.querySelector('.graph-launcher-bar[data-graph-current]');
  state.page.currentSlug = hereBar ? hereBar.dataset.graphCurrent : null;
```

- [ ] **Step 2: research-graph.js — mark the node**

Find (currently ~line 291, in the node-render `.map`):

```js
    const g = document.createElementNS(SVG_NS, 'g');
    g.setAttribute('class', `research-graph-node research-graph-node-${n.kind}`);
```

Replace with:

```js
    const g = document.createElementNS(SVG_NS, 'g');
    g.setAttribute('class', `research-graph-node research-graph-node-${n.kind}`
      + (state.page.currentSlug && n.slug === state.page.currentSlug ? ' is-here' : ''));
```

- [ ] **Step 3: works-graph.js — capture the current slug in `init()`**

Find (currently ~line 672, inside `init()`):

```js
  state.panel = document.getElementById('works-graph-panel');
  state.page.isMobile = isMobile();
```

Replace with:

```js
  state.panel = document.getElementById('works-graph-panel');
  state.page.isMobile = isMobile();
  const hereBar = document.querySelector('.graph-launcher-bar[data-graph-current]');
  state.page.currentSlug = hereBar ? hereBar.dataset.graphCurrent : null;
```

- [ ] **Step 4: works-graph.js — mark the node**

Find (currently ~line 327, in the node-render `.map`):

```js
    const g = document.createElementNS(SVG_NS, 'g');
    g.setAttribute('class', `works-graph-node${n.featured ? ' works-graph-node-featured' : ''}`);
```

Replace with:

```js
    const g = document.createElementNS(SVG_NS, 'g');
    g.setAttribute('class', `works-graph-node${n.featured ? ' works-graph-node-featured' : ''}`
      + (state.page.currentSlug && n.slug === state.page.currentSlug ? ' is-here' : ''));
```

- [ ] **Step 5: Build (esbuild via js.Build) and confirm no bundling error**

Run: `hugo --minify --quiet --destination /tmp/pga-build 2>&1 | tail -5`
Expected: no esbuild/`js.Build` error; build completes. (No JS unit harness exists in this repo — no npm; correctness is verified by the dev-server spot-check in Task 9.)

- [ ] **Step 6: Commit**

```bash
git add assets/js/research-graph.js assets/js/works-graph.js
git commit -m "feat(graph): mark the current page's node (is-here) on item pages

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Extend the chrome-consistency gate to the 5 new surfaces

`tools/check_graph_chrome.py` is sibling-less by design (spec §3.1 — substring/presence scans, no paired unit test). Extend it: the 5 item single layouts must each include the shared launcher-bar partial **and** their section's graph-panel + graph-script partials, so the canon stays enforced as surfaces grow.

**Files:**
- Modify: `tools/check_graph_chrome.py`

- [ ] **Step 1: Add the item-surface table + checks**

In `tools/check_graph_chrome.py`, after the `SURFACES = [ … ]` list and the `FORBIDDEN_MARKUP = [ … ]` list (i.e., just before `def main()`), add:

```python
# Item-page surfaces added by the persistent-graph-access slice
# (2026-05-16 spec). Each must include the shared launcher bar AND its
# section's graph panel + graph-data script, so the launcher/panel/legend
# canon stays enforced as surfaces grow.
LAUNCHER_BAR_CALL = 'partial "graph-launcher-bar.html"'
ITEM_SURFACES = {
    Path("layouts/research-theme/single.html"): "research",
    Path("layouts/research-question/single.html"): "research",
    Path("layouts/works-games/single.html"): "works",
    Path("layouts/works-music/single.html"): "works",
    Path("layouts/works-poetry/single.html"): "works",
}
```

- [ ] **Step 2: Wire the checks into `main()`**

In `main()`, find:

```python
    if errors:
        print(f"check_graph_chrome: {len(errors)} issue(s):", file=sys.stderr)
```

Immediately **before** that `if errors:` line, insert:

```python
    for surface, section in ITEM_SURFACES.items():
        if not surface.is_file():
            errors.append(f"missing item surface file: {surface}")
            continue
        text = surface.read_text(encoding="utf-8")
        if LAUNCHER_BAR_CALL not in text:
            errors.append(f"{surface}: does not include {LAUNCHER_BAR_CALL}")
        panel_call = f'partial "{section}/graph-panel.html"'
        script_call = f'partial "{section}/graph-script.html"'
        if panel_call not in text:
            errors.append(f"{surface}: does not include {panel_call}")
        if script_call not in text:
            errors.append(f"{surface}: does not include {script_call}")
```

- [ ] **Step 3: Update the success line to count item surfaces**

Find:

```python
    print(f"check_graph_chrome: OK ({len(SURFACES)} surfaces)")
```

Replace with:

```python
    print(
        f"check_graph_chrome: OK ({len(SURFACES)} graph surfaces, "
        f"{len(ITEM_SURFACES)} item surfaces)"
    )
```

- [ ] **Step 4: Run the gate — expect PASS**

Run: `python3 tools/check_graph_chrome.py`
Expected: `check_graph_chrome: OK (6 graph surfaces, 5 item surfaces)`

- [ ] **Step 5: Negative check — gate catches a regression**

Run:
```bash
cp layouts/works-poetry/single.html /tmp/wp.bak
python3 - <<'PY'
import re, pathlib
p = pathlib.Path("layouts/works-poetry/single.html")
p.write_text(p.read_text().replace('{{ partial "works/graph-panel.html" . }}\n', ''))
PY
python3 tools/check_graph_chrome.py; echo "exit=$?"
cp /tmp/wp.bak layouts/works-poetry/single.html
python3 tools/check_graph_chrome.py; echo "exit=$?"
```
Expected: first run prints an error mentioning `works-poetry/single.html: does not include partial "works/graph-panel.html"` and `exit=1`; after restore, second run prints OK and `exit=0`.

- [ ] **Step 6: Commit**

```bash
git add tools/check_graph_chrome.py
git commit -m "test(graph): extend check_graph_chrome to the 5 item surfaces

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Full CI mirror + page-weight/LHCI verification + visual spot-check

This task discharges the spec's "must verify, do not assume" risks (page-weight gate headroom; LHCI URLs), retires dead CSS the slice orphaned, and the user's standing preference for a dev-server spot-check with an eyeball checklist before merge.

**Files:** `assets/css/main.css` (Step 0 dead-CSS removal); otherwise verification only.

- [ ] **Step 0: Remove the orphaned `.research-breadcrumb` CSS (slice created the orphan)**

Task 4 deleted the only `.research-breadcrumb` markup (both research single layouts now route the breadcrumb through the shared launcher bar). The CSS rules are now fully dead — confirm and remove:

```bash
grep -rn 'research-breadcrumb' layouts/ assets/ content/
```
Expected: matches ONLY in `assets/css/main.css` (the rule block + its `/* Breadcrumb … */` comment, ~lines 1858-1866). If any `layouts/`/`content/` match exists, STOP — the orphan assumption is wrong; report it.

Delete the `.research-breadcrumb` rule block and its immediately-preceding comment line, e.g.:

```css
/* Breadcrumb … */
.research-breadcrumb {
  …
}
.research-breadcrumb a { color: var(--color-ink-soft); }
.research-breadcrumb [aria-current="page"] { color: var(--color-ink); }
```

(Match the exact current text via `grep -n 'research-breadcrumb' assets/css/main.css`; delete only those rules + the one comment line that introduces them. Touch nothing else.)

Then:
```bash
hugo --quiet --destination /tmp/pga-build
python3 tools/check-contrast.py
git add assets/css/main.css
git commit -m "style(graph): remove orphaned .research-breadcrumb CSS

Task 4 routed the research breadcrumb through the shared launcher bar
and deleted the inline .research-breadcrumb navs; these rules are now
dead. No remaining markup references them.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```
Expected: build clean; contrast gate green (the deleted rules used already-validated tokens; no checked pairing affected).

- [ ] **Step 0b: A11y remediation — `inert` on `research/graph-panel.html` (regression caught by Step 1's LHCI)**

The first CI-mirror run failed: LHCI `categories.accessibility` = **0.89 < 0.90** on the two LHCI-tested research item pages (`/research/themes/memory-and-play/`, `/research/questions/what-is-a-narrative-atom/`). Authoritative failing audits (`.lighthouseci/` LHR):
- `aria-hidden-focus`: `<aside id="research-graph-panel" … aria-hidden="true">` contains focusable descendants. **This is our regression** — Tasks 4 put this panel on the LHCI-tested research item pages. `layouts/partials/garden/graph-panel.html` ships `inert` (so `aria-hidden`+focusable is valid); `research/graph-panel.html` does **not**, yet `research-graph.js` already round-trips it (`removeAttribute('inert')` on open, `setAttribute('inert','')` on close) — the static partial is simply missing the initial attribute.
- `color-contrast` on `.tile-meta`: **pre-existing, not ours.** `note-tile.html` carried `.tile-meta` at branch-point `e036d0d`; research item pages have rendered supporting-notes/garden-topic tiles since before this slice (master is green only because pre-slice research items had no panel → no `aria-hidden-focus` → stayed ≥0.9 despite this). Out of scope for this slice; record as a discovered pre-existing bug for a separate ticket — do **not** fix here (it touches shared garden note-tile chrome).

Fix (research only — `works/graph-panel.html` uses `hidden`, an already-a11y-safe closed state that `works-graph.js` manages differently; do not touch it):

In `layouts/partials/research/graph-panel.html`, the opening tag:
```html
<aside id="research-graph-panel" class="graph-panel" aria-hidden="true"
      role="region" aria-label="Research graph">
```
becomes (add `inert`, matching `garden/graph-panel.html`):
```html
<aside id="research-graph-panel" class="graph-panel" aria-hidden="true"
      role="region" aria-label="Research graph" inert>
```

Then **empirically re-verify** (do not assume the score returns):
```bash
hugo --minify --quiet --destination ./public
npx --yes @lhci/cli@0.13.x autorun --config=lighthouserc.mobile.json 2>&1 | tail -20
python3 -m json.tool .lighthouseci/assertion-results.json
```
Expected: `.lighthouseci/assertion-results.json` is `[]` (or contains NO `accessibility` minScore failure for the two research item URLs); the two URLs now score accessibility ≥ 0.90. If still < 0.90, STOP and report — the tile-meta pre-existing issue may be load-bearing and needs escalation, not a silent budget change.

Commit:
```bash
git add layouts/partials/research/graph-panel.html
git commit -m "fix(a11y): inert on research graph-panel (LHCI aria-hidden-focus)

Tasks 4 put research/graph-panel.html on the LHCI-tested research item
pages; it lacked the `inert` that garden/graph-panel.html has, tripping
aria-hidden-focus and dropping accessibility to 0.89 < 0.90. research-graph.js
already round-trips inert (remove on open / restore on close); the static
partial was just missing the initial attribute. Works panel uses `hidden`
(already safe) and is intentionally untouched.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 1: Run the full CI mirror**

Run: `tools/ci-local.sh 2>&1 | tail -40`
Expected: the script runs to completion and exits 0 (it is `set -e`; a green run means CI will be green). It includes `check_graph_chrome.py`, `check_garden_history.py` + sibling test, the research/works linters, the build, the page-weight gate, and Lighthouse CI.

- [ ] **Step 2: Inspect the page-weight gate output for the new pages**

Run:
```bash
python3 tools/check_page_weights.py public 2>&1 | grep -E '/research/(themes|questions)/|/works/(games|music|poetry)/|BUDGET|FAIL' | head -30
```
(If `public/` is absent, run `hugo --minify` first, then build the Pagefind index per `tools/ci-local.sh`, or re-run Step 1 which produces `public/`.)
Expected: every research theme/question and works item page row shows `ACTUAL` < `BUDGET` (research/works prefixes are 600 KB; `/works/music/` 500 KB; ~110 KB of added d3 lands with large headroom). No `FAIL` rows. **If any row fails**, stop and report — the spec flagged this as a verify-not-assume risk; do not silently bump budgets.

- [ ] **Step 3: Confirm which URLs Lighthouse CI exercises**

Run: `grep -hoE '"http[^"]+"' lighthouserc.json lighthouserc.mobile.json | sort -u`
Expected: note whether any URL is a research/works **item** page (theme/question/game/music/poem). If yes, confirm Step 1's LHCI steps passed for it. If LHCI only hits umbrellas (which already ship d3), record that the item-page payload is bounded by the existing garden-item precedent. Either way, write the finding into the merge notes — do not assume.

- [ ] **Step 4: Dev-server visual spot-check (user preference: eyeball checklist before merge)**

Run (foreground; the user drives the browser): `hugo server --buildDrafts`
Then verify, at a normal window **and** at ~960px width (half-screen 1080p — the user runs a tiling WM):

1. **Research theme page** (e.g. `/research/themes/<slug>/`): the `⊞ Graph` bar is pinned to the top; click it → panel slides in from the right; the launcher stays fully visible and turns burgundy (it *is* the toggle); the node for this page has the `is-here` ring.
2. Click a node in the panel → navigates to another research page → **the panel is still open** (un-animated restore) and the new page's node now has the `is-here` ring.
3. **Research question page** and **works game/music/poem pages**: same launcher bar + breadcrumb (works pages now have a breadcrumb where they had none); same open → traverse → still-open behavior.
4. **Garden note page**: the bar still shows `Path: Garden › <note>` with stack count / clear / history on the right, but the `⊞ Graph` launcher is now **left-aligned** and no longer disappears behind the open panel. Stack still works (click a garden node → column appends; count increments).
5. **Mobile width (< 720px)**: the panel is hidden; clicking `⊞ Graph` navigates to the standalone `/research/graph/` · `/works/graph/`.
6. Light **and** dark theme: bar border/background and `is-here` ring read correctly in both.

Stop the dev server (Ctrl-C) when done. **Do not run `hugo --minify` while the dev server is alive** (MIME-poisons the dev CSS — project gotcha).

- [ ] **Step 5: Report findings and await merge authorization**

Summarize: CI-mirror result, the page-weight numbers for the new pages, the LHCI-URL finding, and the spot-check observations. Per project convention, **do not merge/push without explicit user authorization**. Integration (merge to master + push) is handled via the `superpowers:finishing-a-development-branch` skill after the user signs off.

---

## Self-Review

**1. Spec coverage:**
- Full in-page panel parity → Tasks 4–6 (panel partial + script + bundle widening); persistence machinery confirmed pre-existing in the spec/plan intro.
- Option D shared sticky bar, left-aligned launcher → Task 1 (partial) + Task 3 (`.graph-launcher-bar` shell, launcher as first child).
- Garden path-log refactored into the shared partial → Tasks 1 (garden branch) + 2 (delegator) + 3 (shell migration); DOM-preservation + linter coverage verified (Task 2 Steps 2-3).
- `is-here` on research/works only, garden excluded → Task 1 (attribute only on `generic` variant) + Task 3 (CSS) + Task 7 (JS); garden branch never emits `data-graph-current`.
- Stack *coordination* out of scope for research/works (they navigate, never stack) → Tasks 4-7 add no stacking. **Correction (Task 1 review):** the launcher relocation in Task 2 *does* require a defensive 2-line guard in `garden-stack.js` `updatePathLog()` (Fix A) so the stack renderer doesn't prune the relocated launcher — that is not stack coordination, just protecting persistent chrome. Garden stack behavior itself is unchanged; verified Task 6 (launcher-survives-prune) + Task 9 Step 4.4.
- Mobile fallback → pre-existing `isMobile()` branch; verified Task 9 Step 4.5.
- Gate extension → Task 8.
- Page-weight + LHCI verify-not-assume → Task 9 Steps 2-3 (explicit stop-and-report on failure).
- ci-local before push → Task 9 Step 1.

**2. Placeholder scan:** No TBD/TODO; every code step shows the exact old→new content; commands have expected output. The "~line N" annotations are search anchors with the literal text to find, not placeholders.

**3. Type/name consistency:** Partial name `graph-launcher-bar.html`, class `.graph-launcher-bar`, attribute `data-graph-current` (JS reads `.dataset.graphCurrent`), param names (`variant`, `panelId`, `crumbs`, `currentSlug`, `extraClass`), panel ids (`garden-graph-panel` / `research-graph-panel` / `works-graph-panel`), and `state.page.currentSlug` are used identically across Tasks 1, 4, 5, 7, 8. Garden retains `class="garden-path-log"` + all `.path-log-*` children (Task 1 garden branch ↔ Task 2 ↔ Task 3 §24 residue ↔ existing garden JS/linter). Consistent.
