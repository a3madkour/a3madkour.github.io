# Research Graph (Slice 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the deferred force-directed research graph on `/research/` — toggle button + slide-in panel on desktop, standalone `/research/graph/` page on mobile — with theme-colored squares for themes, circles for questions, solid parent-child edges, and dashed cross-theme edges derived from shared `supporting_notes`.

**Architecture:** Build-time data partial emits `{themes, questions, edges, themePaletteOrder}` as JSON (mirrors `partials/garden/graph-data.html`). A new `assets/js/research-graph.js` is a copy + trim of `garden-graph.js` (removes stack-coordination and local-graph N-hop mode; adapts mount selectors, node renderer, edge classifier, filter chips, and click-to-navigate). A new `entry-research.js` + third `js.Build` call in `partials/scripts.html` loads it only on `/research/` (index) and `/research/graph/` (standalone). Shared scaffolding (toggle button, panel chrome, toolbar, canvas, legend) hoists from `.garden-graph-*` to neutral `.graph-*` so both surfaces share CSS §27 (renamed "Graph (shared)"); a new CSS §31 "Research graph" adds only the research-specific overrides (theme palette fills via `data-theme-color`, square-vs-circle shape distinction, cross-theme edge dasharray).

**Tech Stack:** Hugo extended ≥ 0.148.0 · vanilla ES modules built by Hugo's `js.Build` (esbuild) · d3-force / d3-zoom / d3-drag / d3-selection v3 (already vendored under `assets/js/vendor/`) · Python stdlib for linter extension · CSS hand-rolled in `assets/css/main.css`.

**Spec:** `docs/superpowers/specs/2026-05-11-research-graph-design.md` (commit `c78afad`)

**Predecessor working state:** master @ commit `c78afad` (spec landed). Research surface Slice 1 shipped + merged in `0ac950c`; 3 themes + 6 questions fixture set under `content/research/`; `tools/check_research_fixtures.py` and `tools/check_research_links.py` are the active CI gates; CSS §30 is the research surface section.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `layouts/partials/research/graph-data.html` | NEW | `partialCached` data partial: walks themes + questions, builds parent-child + cross-theme edges, emits JSON dict |
| `layouts/partials/research/graph-script.html` | NEW | Wraps the JSON in `<script type="application/json" id="research-graph-data">` via `safeJS` |
| `layouts/partials/research/graph-panel.html` | NEW | Side-panel scaffolding `<aside id="research-graph-panel" class="graph-panel" hidden>` |
| `layouts/research/graph.html` | NEW | Standalone `/research/graph/` page template |
| `content/research/graph.md` | NEW | Frontmatter file declaring `layout: graph`, `build.list: never` |
| `assets/js/research-graph.js` | NEW | Copy + trim of `garden-graph.js`; adapted for research node/edge taxonomy |
| `assets/js/entry-research.js` | NEW | Thin entry: `import './research-graph.js'` |
| `layouts/research/list.html` | MODIFY | Append toggle button + mount panel partial + mount script partial |
| `layouts/partials/scripts.html` | MODIFY | Add third `js.Build` for research bundle with page-narrow predicate |
| `assets/css/main.css` | MODIFY | §27 hoist (rename `.garden-graph-*` → `.graph-*`); append §31 "Research graph" |
| `layouts/partials/garden/graph-panel.html` | MODIFY | Class renames in lockstep with §27 hoist |
| `layouts/garden/list.html` | MODIFY | Toggle button class rename in lockstep with §27 hoist |
| `assets/js/garden-graph.js` | MODIFY | `querySelector` string updates in lockstep with §27 hoist |
| `tools/check_research_fixtures.py` | MODIFY | Add unique-`weight` assertion across themes |
| `tools/test_check_research_fixtures.py` | MODIFY | One new unit test for the unique-weight check |
| `CLAUDE.md` | MODIFY | §CSS pipeline (§27 rename + §31 add); §Layouts; §Partials; §JS pipeline; §Project status |

---

## Review checkpoints

The user wants review at logical milestones. Tasks below are grouped into six checkpoints:

1. **After Task 1** — CSS hoist regression: garden surfaces still work after class rename.
2. **After Task 2** — Linter extension: CI gate update lands isolated.
3. **After Task 3** — Data partial: JSON shape verified in HTML view-source.
4. **After Task 6** — Integration scaffolding: route + panel + toggle visible, no graph yet.
5. **After Task 8** — JS module + CSS: graph renders with all interactions.
6. **After Task 9** — Dev-server spot-check + CLAUDE.md: slice closure.

---

## Task 1: CSS hoist refactor (`.garden-graph-*` → `.graph-*`)

This task is pure refactor — no new functionality. Touches the live garden module, so verify nothing regresses before continuing.

**Files:**
- Modify: `assets/css/main.css` (§27, lines ~1080–1450)
- Modify: `layouts/partials/garden/graph-panel.html`
- Modify: `layouts/garden/list.html` (the toggle button on line 59)
- Modify: `assets/js/garden-graph.js` (`querySelector` strings)

- [ ] **Step 1: Rename selectors in `assets/css/main.css` §27**

Apply these renames (use `sed -i` or your editor's project-wide rename, then visually verify):

| Old selector | New selector |
|---|---|
| `.garden-graph-toggle` | `.graph-toggle` |
| `.garden-graph-panel` | `.graph-panel` |
| `.garden-graph-panel-header` | `.graph-panel-header` |
| `.garden-graph-panel-toolbar` | `.graph-panel-toolbar` |
| `.garden-graph-panel-canvas` | `.graph-panel-canvas` |
| `.garden-graph-panel-close` | `.graph-panel-close` |
| `.garden-graph-panel-resize` | `.graph-panel-resize` |
| `.garden-graph-panel-legend` | `.graph-panel-legend` |

State variants ride along automatically (`[aria-expanded="true"]`, `.is-animating`, `.is-panning`, `.is-resizing`).

Also rename the §27 section header comment:
- Old: `/* 27. Garden graph panel ... */`
- New: `/* 27. Graph (shared) — toggle, panel chrome, toolbar, canvas, legend, resize handle ... */`

Bash one-liner to do the global rename (review the diff before committing):

```bash
sed -i 's/\.garden-graph-toggle/.graph-toggle/g; s/\.garden-graph-panel/.graph-panel/g' assets/css/main.css
```

Note: this leaves the §28 `.garden-graph-page` page-specific rules intact (those are garden-scoped on purpose — they apply only to `/garden/graph/`).

- [ ] **Step 2: Rename classes in `layouts/partials/garden/graph-panel.html`**

Open the file, search-replace within it:
- `garden-graph-panel` → `graph-panel` (in class attributes)
- `garden-graph-panel-header` → `graph-panel-header`
- `garden-graph-panel-toolbar` → `graph-panel-toolbar`
- `garden-graph-panel-canvas` → `graph-panel-canvas`
- `garden-graph-panel-close` → `graph-panel-close`
- `garden-graph-panel-resize` → `graph-panel-resize`
- `garden-graph-panel-legend` → `graph-panel-legend`

**Keep** the `id="garden-graph-panel"` attribute — id stays namespaced per surface so both panels can coexist in theory (and the garden toggle's `aria-controls` references it).

- [ ] **Step 3: Rename the toggle class in `layouts/garden/list.html:59`**

Change:
```html
<button type="button" class="garden-graph-toggle" aria-expanded="false" aria-controls="garden-graph-panel">⊞ Graph</button>
```

To:
```html
<button type="button" class="graph-toggle" aria-expanded="false" aria-controls="garden-graph-panel">⊞ Graph</button>
```

`aria-controls` stays pointing at `garden-graph-panel` (id unchanged).

- [ ] **Step 4: Update `querySelector` strings in `assets/js/garden-graph.js`**

Run this to find every selector that needs updating:

```bash
grep -n "garden-graph-toggle\|garden-graph-panel" assets/js/garden-graph.js
```

For each match, decide:
- **Class selector** (e.g., `.garden-graph-panel-toolbar`, `.garden-graph-toggle`) → rename to neutral `.graph-*`.
- **Id selector** (e.g., `#garden-graph-panel`) → leave as-is (id stays surface-namespaced).

Apply edits. After the edits, this grep should still return id-only matches:

```bash
grep -n "garden-graph-toggle\|garden-graph-panel" assets/js/garden-graph.js
```

Expected: only matches against `#garden-graph-panel` (the id, used in `document.getElementById` or `querySelector('#garden-graph-panel')`).

- [ ] **Step 5: Start dev server and regression-test garden surfaces**

```bash
hugo server --buildDrafts
```

Open `http://localhost:1313/garden/` in a browser. Verify:

1. ⊞ Graph button is visible in the filter strip (same as before).
2. Click the button → panel slides in from the right.
3. Inside the panel: tag chips render, stage chips render, [Reset view] + [Reset positions] buttons render, canvas shows the graph.
4. Drag a node → it stays put on release.
5. Wheel-zoom + drag-pan work.
6. Click ✕ in the panel header → panel closes.

Open `http://localhost:1313/garden/the-save-game/` (any note page). Verify:

7. ⊞ Graph button is visible in the path log at the top.
8. Click → panel slides in, "in-stack" markers (thicker stroke) appear on visited nodes.
9. Click an outgoing link in column 1 → column 2 appends, panel updates with new in-stack marker.

Open `http://localhost:1313/garden/graph/`. Verify:

10. Standalone page renders the full-viewport graph (this uses `.garden-graph-page` which we left alone).
11. Toolbar at the top works.

If any of these regress, fix in lockstep before continuing.

- [ ] **Step 6: Commit**

```bash
git add assets/css/main.css \
        layouts/partials/garden/graph-panel.html \
        layouts/garden/list.html \
        assets/js/garden-graph.js
git commit -m "$(cat <<'EOF'
CSS §27: hoist .garden-graph-* → .graph-* for shared scaffolding

Renames the toggle, panel, panel-header, panel-toolbar, panel-canvas,
panel-close, panel-resize, panel-legend classes to the neutral .graph-*
form. Garden HTML + JS updated in lockstep; ids stay surface-namespaced
(#garden-graph-panel). Prep for the research graph in Slice 2, which
will share §27 and add only research-specific overrides in §31.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

**🔍 REVIEW CHECKPOINT 1** — Garden surfaces verified non-regressed. Halt for review before Task 2.

---

## Task 2: Linter extension — unique theme weights (TDD)

Pure Python, isolated from the rest of the slice. TDD-friendly.

**Files:**
- Modify: `tools/check_research_fixtures.py`
- Modify: `tools/test_check_research_fixtures.py`

- [ ] **Step 1: Read the existing linter to find the integration point**

```bash
grep -n "def validate\|def check\|themes\|weight" tools/check_research_fixtures.py | head -30
```

Locate the function that iterates themes (likely a `for theme in themes:` loop or a per-theme validator). The new check should run once per theme set, not per-theme — find or add a `validate_themes(themes)` collection-level function.

- [ ] **Step 2: Write the failing unit test**

Open `tools/test_check_research_fixtures.py` and add a new test method. The existing test file uses Python's `unittest` (matches `tools/test_check_fixtures.py` style). Add:

```python
def test_unique_theme_weights_detects_duplicate(self):
    """Two themes with the same weight should produce a linter error."""
    themes = [
        {'slug': 'theme-a', 'weight': 10, 'title': 'A', 'status': 'active', 'last_modified': '2026-05-11'},
        {'slug': 'theme-b', 'weight': 10, 'title': 'B', 'status': 'active', 'last_modified': '2026-05-11'},
    ]
    errors = validate_unique_theme_weights(themes)
    self.assertEqual(len(errors), 1)
    self.assertIn('weight 10 duplicated', errors[0])
    self.assertIn('theme-a', errors[0])
    self.assertIn('theme-b', errors[0])

def test_unique_theme_weights_accepts_distinct(self):
    """Distinct weights produce no errors."""
    themes = [
        {'slug': 'theme-a', 'weight': 10},
        {'slug': 'theme-b', 'weight': 20},
        {'slug': 'theme-c', 'weight': 30},
    ]
    errors = validate_unique_theme_weights(themes)
    self.assertEqual(errors, [])

def test_unique_theme_weights_skips_missing(self):
    """Themes without a weight field shouldn't crash the check (weight is required elsewhere)."""
    themes = [
        {'slug': 'theme-a'},
        {'slug': 'theme-b', 'weight': 20},
    ]
    errors = validate_unique_theme_weights(themes)
    self.assertEqual(errors, [])
```

The import of `validate_unique_theme_weights` from `check_research_fixtures` should also be added at the top of the test file alongside existing imports.

- [ ] **Step 3: Run the test and verify it fails**

```bash
python3 -m unittest tools.test_check_research_fixtures.TestCheckResearchFixtures.test_unique_theme_weights_detects_duplicate -v
```

Expected:
```
ImportError: cannot import name 'validate_unique_theme_weights' from 'tools.check_research_fixtures'
```
…or an `AttributeError` of similar shape.

- [ ] **Step 4: Implement the validator function**

Add to `tools/check_research_fixtures.py`:

```python
def validate_unique_theme_weights(themes):
    """Theme weights must be unique so themePaletteOrder is deterministic.

    Returns a list of error strings (empty if all weights are distinct or absent).
    """
    seen = {}
    errors = []
    for theme in themes:
        w = theme.get('weight')
        if w is None:
            continue
        if w in seen:
            errors.append(
                f"theme weight {w} duplicated: {seen[w]} and {theme['slug']}"
            )
        else:
            seen[w] = theme['slug']
    return errors
```

Then wire it into the main `check()` flow — find where the linter aggregates errors across themes and add a call:

```python
errors.extend(validate_unique_theme_weights(themes))
```

(The exact aggregation line depends on the existing linter's structure — look for where other collection-level checks are called, or where the per-theme loop closes and aggregate-level checks run.)

- [ ] **Step 5: Run the unit tests and verify they pass**

```bash
python3 -m unittest tools.test_check_research_fixtures -v
```

Expected: all tests pass, including the three new ones.

- [ ] **Step 6: Run the linter against the live fixtures**

```bash
python3 tools/check_research_fixtures.py
```

Expected: exit code 0. (Current fixture weights are 10/20/30 — all distinct, so the new check passes.)

- [ ] **Step 7: Sanity-check failure mode by temporarily breaking a fixture**

```bash
# Make a theme weight collide temporarily
sed -i 's/^weight: 20$/weight: 10/' content/research/themes/procedural-narrative/index.md
python3 tools/check_research_fixtures.py
```

Expected: exits non-zero with an error message mentioning `weight 10 duplicated`.

Then revert:

```bash
sed -i 's/^weight: 10$/weight: 20/' content/research/themes/procedural-narrative/index.md
python3 tools/check_research_fixtures.py  # back to exit 0
```

- [ ] **Step 8: Commit**

```bash
git add tools/check_research_fixtures.py tools/test_check_research_fixtures.py
git commit -m "$(cat <<'EOF'
CI: research fixtures linter — assert unique theme weights

Slice 2's themePaletteOrder array is built from theme.weight ordering, so
duplicate weights would make palette assignment non-deterministic. Adds
validate_unique_theme_weights() to check_research_fixtures.py and three
unit tests. No new CI gate; extends the existing one.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

**🔍 REVIEW CHECKPOINT 2** — Linter extension lands isolated. Halt for review before Task 3.

---

## Task 3: Build-time data partial + script partial

These two partials are pure-additive — they don't appear anywhere until Task 5 wires the script partial into `layouts/research/list.html`. Verify the JSON shape at the end of Task 5; here we just create the files.

**Files:**
- Create: `layouts/partials/research/graph-data.html`
- Create: `layouts/partials/research/graph-script.html`

- [ ] **Step 1: Inspect garden's equivalents as a reference**

```bash
cat layouts/partials/garden/graph-data.html
cat layouts/partials/garden/graph-script.html
```

The research versions mirror the same shape: a `partialCached` data partial that returns a JSON-serializable dict, plus a tiny script partial that wraps it in a `<script>` tag.

- [ ] **Step 2: Create `layouts/partials/research/graph-data.html`**

```go-html-template
{{- /*
  Research graph data — emitted once per build, consumed by research-graph.js.

  Shape:
    {
      themes: [ {slug, title, status, tags, weight} ],
      questions: [ {slug, title, theme, status, tags, degree} ],
      edges: [ {source, target, kind, via?} ],
      themePaletteOrder: [slug, ...]   // sorted by weight asc, then slug
    }

  Edges:
    - parent-child (solid): theme→question (from question.theme), question→sub-question (from question.parent_question)
    - cross-theme (dashed): two questions in different themes citing the same garden slug in supporting_notes
*/ -}}

{{- $themesIn := where site.RegularPages "Type" "research-theme" -}}
{{- $questionsIn := where site.RegularPages "Type" "research-question" -}}

{{- /* ---------- themes ---------- */ -}}
{{- $themes := slice -}}
{{- range $themesIn -}}
  {{- $slug := path.Base .File.Dir -}}
  {{- $themes = $themes | append (dict
      "slug" $slug
      "title" .Title
      "status" .Params.status
      "tags" (default (slice) .Params.tags)
      "weight" (default 0 .Params.weight)
    ) -}}
{{- end -}}

{{- /* themePaletteOrder: sort by weight asc, slug for ties */ -}}
{{- $themesSorted := sort $themes "weight" "asc" -}}
{{- $themePaletteOrder := slice -}}
{{- range $themesSorted -}}
  {{- $themePaletteOrder = $themePaletteOrder | append .slug -}}
{{- end -}}

{{- /* ---------- questions + supporting-notes index ---------- */ -}}
{{- $questions := slice -}}
{{- $supportingIndex := dict -}}
{{- range $questionsIn -}}
  {{- $slug := path.Base .File.Dir -}}
  {{- $q := dict
      "slug" $slug
      "title" .Title
      "theme" .Params.theme
      "parent" (default "" .Params.parent_question)
      "status" .Params.status
      "tags" (default (slice) .Params.tags)
  -}}
  {{- $questions = $questions | append $q -}}
  {{- range (default (slice) .Params.supporting_notes) -}}
    {{- $note := . -}}
    {{- $existing := index $supportingIndex $note -}}
    {{- if $existing -}}
      {{- $supportingIndex = merge $supportingIndex (dict $note ($existing | append $slug)) -}}
    {{- else -}}
      {{- $supportingIndex = merge $supportingIndex (dict $note (slice $slug)) -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- /* question slug → theme slug, for cross-theme detection */ -}}
{{- $qTheme := dict -}}
{{- range $questions -}}
  {{- $qTheme = merge $qTheme (dict .slug .theme) -}}
{{- end -}}

{{- /* ---------- edges ---------- */ -}}
{{- $edges := slice -}}

{{- /* parent-child: theme → its questions */ -}}
{{- range $q := $questions -}}
  {{- if $q.theme -}}
    {{- $edges = $edges | append (dict "source" $q.theme "target" $q.slug "kind" "parent-child") -}}
  {{- end -}}
{{- end -}}

{{- /* parent-child: question → sub-question */ -}}
{{- range $q := $questions -}}
  {{- if $q.parent -}}
    {{- $edges = $edges | append (dict "source" $q.parent "target" $q.slug "kind" "parent-child") -}}
  {{- end -}}
{{- end -}}

{{- /* cross-theme: per garden slug, all distinct cross-theme pairs */ -}}
{{- $seenPairs := dict -}}
{{- range $note, $qs := $supportingIndex -}}
  {{- if ge (len $qs) 2 -}}
    {{- range $i, $a := $qs -}}
      {{- range $j, $b := $qs -}}
        {{- if gt $j $i -}}
          {{- $themeA := index $qTheme $a -}}
          {{- $themeB := index $qTheme $b -}}
          {{- if ne $themeA $themeB -}}
            {{- $pairKey := printf "%s|%s" $a $b -}}
            {{- if not (isset $seenPairs $pairKey) -}}
              {{- $seenPairs = merge $seenPairs (dict $pairKey true) -}}
              {{- $edges = $edges | append (dict "source" $a "target" $b "kind" "cross-theme" "via" $note) -}}
            {{- end -}}
          {{- end -}}
        {{- end -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{- /* ---------- degree per node ---------- */ -}}
{{- $degree := dict -}}
{{- range $e := $edges -}}
  {{- $sCur := default 0 (index $degree $e.source) -}}
  {{- $tCur := default 0 (index $degree $e.target) -}}
  {{- $degree = merge $degree (dict $e.source (add $sCur 1)) -}}
  {{- $degree = merge $degree (dict $e.target (add $tCur 1)) -}}
{{- end -}}

{{- /* fold degree back into questions (themes don't need it surfaced in JSON since size also uses degree later but reading from a flat map is fine) */ -}}
{{- $questionsOut := slice -}}
{{- range $q := $questions -}}
  {{- $deg := default 0 (index $degree $q.slug) -}}
  {{- $questionsOut = $questionsOut | append (dict
      "slug" $q.slug
      "title" $q.title
      "theme" $q.theme
      "status" $q.status
      "tags" $q.tags
      "degree" $deg
    ) -}}
{{- end -}}

{{- $themesOut := slice -}}
{{- range $t := $themes -}}
  {{- $deg := default 0 (index $degree $t.slug) -}}
  {{- $themesOut = $themesOut | append (dict
      "slug" $t.slug
      "title" $t.title
      "status" $t.status
      "tags" $t.tags
      "weight" $t.weight
      "degree" $deg
    ) -}}
{{- end -}}

{{- $payload := dict
    "themes" $themesOut
    "questions" $questionsOut
    "edges" $edges
    "themePaletteOrder" $themePaletteOrder
-}}

{{- return $payload -}}
```

- [ ] **Step 3: Create `layouts/partials/research/graph-script.html`**

```go-html-template
{{- $data := partialCached "research/graph-data.html" . -}}
<script type="application/json" id="research-graph-data">
{{- $data | jsonify | safeJS -}}
</script>
```

The `safeJS` cast prevents Hugo from HTML-escaping the JSON. Mirrors `partials/garden/graph-script.html`.

- [ ] **Step 4: Static check — Hugo doesn't error on the partials**

Even without wiring them into a layout yet, Hugo will still parse them during the next build. Run:

```bash
hugo --gc 2>&1 | grep -E "ERROR|partials/research/graph"
```

Expected: no error output. (The partials are present but not yet called from any layout, so they don't render anywhere — but they shouldn't break the build.)

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/research/graph-data.html \
        layouts/partials/research/graph-script.html
git commit -m "$(cat <<'EOF'
Research graph: build-time data + script partials

graph-data.html walks themes + questions, emits {themes, questions, edges,
themePaletteOrder}. Edge classification: theme→question and question→
sub-question are parent-child (solid); shared supporting_notes across
themes produce cross-theme (dashed) edges with via:<garden-slug>.

graph-script.html wraps the JSON in <script type="application/json"
id="research-graph-data"> via safeJS. Not yet wired into list.html
(Task 5).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

**🔍 REVIEW CHECKPOINT 3** — Data partial committed; will verify shape in view-source after Task 5.

---

## Task 4: Standalone page (`/research/graph/`)

Create the content file and minimal layout. After this task, `/research/graph/` returns 200 with an (empty) page. No JS yet.

**Files:**
- Create: `content/research/graph.md`
- Create: `layouts/research/graph.html`

- [ ] **Step 1: Inspect garden's standalone page as a reference**

```bash
cat content/garden/graph.md 2>/dev/null || ls content/garden/ | grep graph
cat layouts/garden/graph.html
```

Replicate the same shape for research.

- [ ] **Step 2: Create `content/research/graph.md`**

```markdown
---
title: "Research graph"
layout: graph
build:
  list: never
---
```

`build.list: never` excludes this from the `/research/` index iteration (so it doesn't appear as a stray theme/question entry).

- [ ] **Step 3: Create `layouts/research/graph.html`**

Minimal full-viewport canvas. Mirror garden's structure:

```go-html-template
{{ define "main" }}
<main class="research-graph-page">
  <div class="graph-panel-canvas"></div>
</main>
{{ partial "research/graph-script.html" .Site }}
{{ end }}
```

The `.graph-panel-canvas` class picks up sizing rules from §27 (post-hoist). The script partial mounts the JSON blob even on this page, so the standalone graph reads the same data shape.

- [ ] **Step 4: Verify the route renders**

```bash
hugo server --buildDrafts
```

Visit `http://localhost:1313/research/graph/`. Expected:
- HTTP 200, page renders with the site header + footer chrome.
- View source: `<main class="research-graph-page">` is present, plus the `<script type="application/json" id="research-graph-data">…</script>` blob with the JSON payload.
- Canvas is empty (no JS yet).

Also verify the index doesn't list this as a stray:

Visit `http://localhost:1313/research/`. Expected: 3 theme cards only — no stray "Research graph" entry.

- [ ] **Step 5: Commit**

```bash
git add content/research/graph.md layouts/research/graph.html
git commit -m "$(cat <<'EOF'
Research graph: standalone /research/graph/ page

content/research/graph.md declares layout=graph and build.list=never so
it doesn't appear in the index iteration. layouts/research/graph.html is
a minimal canvas wrapper; relies on .graph-panel-canvas from §27 post-
hoist for sizing. Mounts the script partial so the data blob is in scope.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Panel partial + toggle button on /research/

Wires the panel scaffolding + toggle + data script into `layouts/research/list.html`. After this task, the toggle button is visible, the panel `<aside>` is in the DOM (hidden), and the JSON blob is in page source. No JS yet, so clicking the toggle does nothing.

**Files:**
- Create: `layouts/partials/research/graph-panel.html`
- Modify: `layouts/research/list.html`

- [ ] **Step 1: Inspect garden's panel partial**

```bash
cat layouts/partials/garden/graph-panel.html
```

The research version mirrors it; only the wrapping `id` differs.

- [ ] **Step 2: Create `layouts/partials/research/graph-panel.html`**

```go-html-template
<aside id="research-graph-panel" class="graph-panel" hidden aria-hidden="true">
  <header class="graph-panel-header">
    <h2>Research graph</h2>
    <button type="button" class="graph-panel-close" aria-label="Close graph">×</button>
  </header>
  <div class="graph-panel-toolbar"></div>
  <div class="graph-panel-canvas"></div>
  <div class="graph-panel-legend"></div>
  <div class="graph-panel-resize" aria-hidden="true"></div>
</aside>
```

All children are populated by `research-graph.js` on first mount.

- [ ] **Step 3: Edit `layouts/research/list.html`**

Three additions. The current file structure (verified pre-task at `layouts/research/list.html:1-37`):
- Line 24 ends with `{{ partial "filter-chips.html" ... }}`
- Line 33 closes the `.research-grid` div
- Line 35 closes `</main>`

Add a toggle button after the filter-chips partial (line 24), then mount the panel partial after the grid, then mount the script partial inside `main`. Full replacement of lines 13–35:

```go-html-template
  {{- /* Filter chips: tag dim only for v1 */ -}}
  {{- $tags := slice -}}
  {{- range $themes -}}
    {{- range .Params.tags -}}
      {{- if not (in $tags .) -}}{{- $tags = $tags | append . -}}{{- end -}}
    {{- end -}}
  {{- end -}}
  {{- $dims := slice -}}
  {{- if ge (len $tags) 2 -}}
    {{- $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" (sort $tags)) -}}
  {{- end -}}
  {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "research") }}
  <button type="button" class="graph-toggle" aria-expanded="false" aria-controls="research-graph-panel">⊞ Graph</button>

  <div class="research-grid">
    {{- range $themes.ByWeight -}}
      {{- $thisTheme := . -}}
      {{- $thisSlug := path.Base $thisTheme.File.Dir -}}
      {{- $themeQs := where $questions "Params.theme" $thisSlug -}}
      {{ partial "research/theme-card.html" (dict "theme" $thisTheme "questions" $themeQs) }}
    {{- end -}}
  </div>

  {{ partial "research/graph-panel.html" . }}
  {{ partial "research/graph-script.html" .Site }}

</main>
{{ end }}
```

- [ ] **Step 4: Verify in the browser**

```bash
hugo server --buildDrafts  # if not still running
```

Visit `http://localhost:1313/research/`. Expected:
- The ⊞ Graph button appears just after the filter chip strip.
- Its `.graph-toggle` styling matches garden's button (after §27 hoist).
- View source: `<aside id="research-graph-panel" class="graph-panel" hidden>` is present after the grid.
- View source: `<script type="application/json" id="research-graph-data">` is present, JSON inside.
- Inspect the JSON: should contain 3 themes + 6 questions + 8 edges (6 theme→question parent-child + 1 question→sub-question parent-child + 1 cross-theme).
- Clicking the button does nothing (no JS handler yet). The button's `aria-expanded` stays `false`.

Specifically eyeball the JSON for:
- `themePaletteOrder: ["memory-and-play", "procedural-narrative", "save-game-as-form"]` (sorted by weight 10, 20, 30).
- One edge with `"kind": "cross-theme", "via": "story-atoms"` connecting `how-do-readers-form-narrative-from-shuffle` and `what-is-a-narrative-atom`.
- `degree` field populated on each question.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/research/graph-panel.html layouts/research/list.html
git commit -m "$(cat <<'EOF'
Research graph: panel scaffolding + toggle button on /research/

Adds the ⊞ Graph button after the filter chip strip, mounts the panel
aside (hidden by default), and emits the JSON data blob via the script
partial. No JS yet — clicking the toggle is a no-op until Task 7.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: JS entry + bundling

Create the entry file, copy garden-graph.js as a starting point, wire the bundle into `scripts.html`. After this task, `js/research.<hash>.js` is served on `/research/` and `/research/graph/` (and NOT on theme/question pages), but it's just a copy of garden-graph that won't find its mount selectors. Toggle still doesn't open anything yet.

**Files:**
- Create: `assets/js/entry-research.js`
- Create: `assets/js/research-graph.js`
- Modify: `layouts/partials/scripts.html`

- [ ] **Step 1: Create `assets/js/entry-research.js`**

```js
import './research-graph.js';
```

- [ ] **Step 2: Copy `garden-graph.js` to `research-graph.js`**

```bash
cp assets/js/garden-graph.js assets/js/research-graph.js
```

This is a literal copy — adaptation happens in Task 7. Keeping it as-is for this task lets us verify the bundle pipeline before the JS surgery.

- [ ] **Step 3: Inspect `layouts/partials/scripts.html` for the existing pattern**

```bash
cat layouts/partials/scripts.html
```

Locate the essay and garden `js.Build` blocks. The research block goes after them, before the closing `</body>` or whatever the page-bottom is.

- [ ] **Step 4: Add the third `js.Build` call**

Add this block after the garden block in `layouts/partials/scripts.html`. The exact Go template syntax depends on how the existing blocks are written; here's the canonical form (mirror the garden block's surrounding boilerplate):

```go-html-template
{{- $loadResearch := or
     (and (eq .Section "research") (eq .Kind "section"))
     (and (eq .Section "research") (eq .Layout "graph")) -}}
{{- if $loadResearch -}}
  {{- $researchEntry := resources.Get "js/entry-research.js" -}}
  {{- $research := $researchEntry | js.Build $opts -}}
  {{- if hugo.IsProduction -}}
    {{- $research = $research | minify | fingerprint -}}
    <script src="{{ $research.RelPermalink }}" integrity="{{ $research.Data.Integrity }}"></script>
  {{- else -}}
    <script src="{{ $research.RelPermalink }}"></script>
  {{- end -}}
{{- end -}}
```

`$opts` is the shared `js.Build` options object defined earlier in the file. If it's named differently in the existing code, match that name.

- [ ] **Step 5: Verify the bundle loads on the right pages and not the wrong ones**

```bash
hugo server --buildDrafts
```

Visit and view-source on each page; check the `<script src="…">` tags at the bottom:

| URL | Should load `research.<hash>.js`? |
|---|---|
| `/research/` | YES |
| `/research/graph/` | YES |
| `/research/themes/memory-and-play/` | NO |
| `/research/questions/how-do-readers-form-narrative-from-shuffle/` | NO |
| `/garden/` | NO |
| `/garden/graph/` | NO (this is garden's standalone) |
| `/` (homepage) | NO |

Garden's bundle (`garden.<hash>.js`) should still load only on garden pages. Essay bundle still essay-only. Core bundle on everything. No leakage.

- [ ] **Step 6: Verify JS console — research-graph.js loads and bails on theme/question pages**

The copied script will run on `/research/` and `/research/graph/`. Because it's still the unmodified garden code, it queries selectors like `.garden-graph-toggle` (which don't exist on research pages — the toggle there is `.graph-toggle`) and probably does an early return. Open the browser console at `/research/`. Expected:
- No JS errors.
- No graph activity (script bails because selectors don't match).

If you see errors, that's fine for this task — they'll be resolved by Task 7's adaptation. Note them but don't fix here.

- [ ] **Step 7: Commit**

```bash
git add assets/js/entry-research.js assets/js/research-graph.js layouts/partials/scripts.html
git commit -m "$(cat <<'EOF'
Research graph: JS entry + multi-entry bundling

assets/js/entry-research.js imports research-graph.js (a literal copy of
garden-graph.js for now — Task 7 trims and adapts).

partials/scripts.html gains a third js.Build call. Page-narrow predicate
loads the research bundle only on /research/ (index) and /research/graph/
(standalone) — theme + question pages stay on the core bundle.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

**🔍 REVIEW CHECKPOINT 4** — Integration scaffolding done. Toggle visible, bundle wired, JSON in source. Halt for review before Task 7.

---

## Task 7: Adapt `research-graph.js` (trim + research-specific bits)

The meaty task. Sub-divided into named edits, each one a small focused diff. Each sub-step ends in a commit so the history is reviewable.

**Files:**
- Modify: `assets/js/research-graph.js`

- [ ] **Step 1: Update the DOM mount selectors**

Open `assets/js/research-graph.js`. Find every selector reference to garden's mount points and update:

| Replace | With |
|---|---|
| `'#garden-graph-panel'` | `'#research-graph-panel'` |
| `'.garden-graph-page'` | `'.research-graph-page'` |
| `'.garden-graph-toggle'` (if still present after Task 1 hoist) | `'.graph-toggle'` |
| `'#garden-graph-data'` | `'#research-graph-data'` |

Run this to find every relevant selector:

```bash
grep -n "garden-graph\|garden:" assets/js/research-graph.js
```

The grep output drives the rename pass. Most should be selectors; a few may be event names (see Step 2).

After this step the script should at minimum bind to the right elements on `/research/` — the toggle click will mount something, even if data parsing fails.

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: update mount selectors to research IDs

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 2: Remove the `garden:stack-changed` event listener and in-stack rendering**

Search for `garden:stack-changed`:

```bash
grep -n "stack-changed\|in-stack\|inStack" assets/js/research-graph.js
```

Three classes of removal:
1. The `window.addEventListener('garden:stack-changed', …)` handler.
2. The `.in-stack` CSS-class-toggle logic on nodes.
3. The `state.stack` reads (no stack on research; nodes have no concept of "currently in stack").

Replace each with a deletion (not a no-op). The function bodies that handled stack state should be removed entirely.

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: drop garden stack-coordination

No stack model on research — remove the garden:stack-changed listener,
.in-stack class toggles, and state.stack reads.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 3: Remove the local-graph N-hop mode**

Search for the local-mode UI + filter logic:

```bash
grep -n "local\|1-hop\|2-hop\|nHop" assets/js/research-graph.js
```

Remove:
- The `local` state variable + its read/write sites.
- The `1-hop` / `2-hop` / `all` toolbar buttons in the `buildToolbar()` function.
- The graph-filtering logic that prunes nodes by hop distance from a focused node.
- The mount-time detection of "am I on a note page → enable local mode by default".

All research graphs render all nodes; there's no per-page focus.

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: drop local-graph N-hop mode

No graph runtime on theme/question pages in Slice 2 — drop the all/1-hop/
2-hop toolbar and its filter logic.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 4: Adapt the data parse — read research JSON shape**

Find where garden parses its `#garden-graph-data` blob. The shape difference:

| Garden | Research |
|---|---|
| `{nodes: [...], edges: [...], topics: {...}}` | `{themes: [...], questions: [...], edges: [...], themePaletteOrder: [...]}` |
| Nodes uniform: `{slug, title, tag, stage, flavor, degree}` | Two kinds: themes have `weight`, questions have `theme` |
| Edges: `{source, target, crossTopic}` (boolean) | Edges: `{source, target, kind, via?}` (`kind` is "parent-child" or "cross-theme") |

Replace the garden parse with:

```js
const raw = JSON.parse(document.getElementById('research-graph-data').textContent);
const themePaletteOrder = raw.themePaletteOrder;
const themePaletteIndex = (slug) => themePaletteOrder.indexOf(slug);

const nodes = [
  ...raw.themes.map(t => ({
    slug: t.slug,
    title: t.title,
    kind: 'theme',
    status: t.status,
    tags: t.tags,
    themeColorIdx: themePaletteIndex(t.slug),
    degree: t.degree,
  })),
  ...raw.questions.map(q => ({
    slug: q.slug,
    title: q.title,
    kind: 'question',
    theme: q.theme,
    status: q.status,
    tags: q.tags,
    themeColorIdx: themePaletteIndex(q.theme),
    degree: q.degree,
  })),
];

const links = raw.edges.map(e => ({
  source: e.source,
  target: e.target,
  kind: e.kind,
  via: e.via || null,
}));
```

The d3-force setup that follows (`forceLink`, `forceManyBody`, `forceCenter`, etc.) reads from `nodes` and `links` — those names match the garden script, so the simulation initialization shouldn't need other changes here.

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: parse research JSON shape

Flattens themes + questions into a unified nodes array with kind=theme/
question. Maps themePaletteOrder index onto each node (theme uses its own
slug; question uses its theme's slug).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 5: Adapt the node renderer — shape + color**

Find the d3 enter-selection that creates per-node SVG groups (likely a `.join('g').classed(...)` chain or similar). Garden renders a `<circle>` per node. Research renders `<rect>` for themes and `<circle>` for questions, with `data-theme-color` for fill.

Replace the node element creation with kind-aware code:

```js
const nodeG = svg.append('g').attr('class', 'graph-nodes')
  .selectAll('g.graph-node')
  .data(nodes, d => d.slug)
  .join('g')
    .attr('class', d => `graph-node graph-node-${d.kind}`)
    .attr('data-theme-color', d => d.themeColorIdx)
    .attr('data-status', d => d.status);

// per-kind shape
nodeG.each(function (d) {
  const sel = d3.select(this);
  const size = sizeFromDegree(d.degree);   // existing helper or inline: Math.max(4, Math.min(12, 4 + d.degree));
  if (d.kind === 'theme') {
    sel.append('rect')
      .attr('width',  size * 1.6)
      .attr('height', size * 1.6)
      .attr('x', -size * 0.8)
      .attr('y', -size * 0.8);
  } else {
    sel.append('circle')
      .attr('r', size);
  }
});

nodeG.append('title').text(d => d.title);  // browser-native tooltip
```

(`sizeFromDegree` is a helper you'll either find in garden's existing code or define inline as `Math.max(4, Math.min(12, 4 + (d.degree || 0)))`.)

CSS in §31 (Task 8) reads `data-theme-color` for fill.

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: shape + color per node kind

Themes render as squares (rect), questions as circles. data-theme-color
attribute drives fill via CSS §31. data-status surfaces for the filter
dim.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 6: Adapt the edge renderer — classification**

Find the link-rendering enter selection. Garden uses `crossTopic` boolean → CSS class `.cross-topic`. Research uses `kind: 'parent-child' | 'cross-theme'` → CSS class `.graph-edge-cross-theme` when kind is `cross-theme`.

Replace the edge element creation:

```js
const linkG = svg.append('g').attr('class', 'graph-edges')
  .selectAll('line.graph-edge')
  .data(links)
  .join('line')
    .attr('class', d => d.kind === 'cross-theme' ? 'graph-edge graph-edge-cross-theme' : 'graph-edge');
```

The `tick` handler that updates `x1, y1, x2, y2` doesn't need changes.

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: edge classification (parent-child vs cross-theme)

Cross-theme edges get .graph-edge-cross-theme class for CSS §31's dashed
stroke override. Parent-child edges stay on the default .graph-edge style.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 7: Adapt the filter chips — tag + status (replacing tag + stage)**

Find `buildToolbar()` or wherever garden constructs the in-panel chip strip. Two changes:
1. Replace the `stage` dimension with `status`.
2. Update the chip values: garden's stages were `seedling / budding / evergreen`; research statuses are `active / dormant / answered`.

Status filter behavior:
- Single-select (clicking switches to that status; clicking again clears).
- Affects questions only — theme nodes ignore the filter (never dim).

In the filter application logic (where garden dims nodes based on tag+stage match), update:

```js
function isNodeVisible(node, filter) {
  // Themes always visible (status filter applies to questions only).
  if (node.kind === 'theme') {
    // Tag filter still applies to themes if they have matching tags
    if (filter.tags.size > 0) {
      return [...filter.tags].every(t => (node.tags || []).includes(t));
    }
    return true;
  }
  // Questions: AND of tag filter (multi-select) + status filter (single).
  if (filter.tags.size > 0) {
    if (![...filter.tags].every(t => (node.tags || []).includes(t))) return false;
  }
  if (filter.status && node.status !== filter.status) return false;
  return true;
}
```

(Adapt to the existing filter state shape — garden likely already has `filter.tags: Set` and `filter.stage: string|null`. Rename `stage` → `status`.)

The chip rendering itself reuses garden's chip-element structure; only the dimension data changes.

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: filter dims = tag + status (replacing tag + stage)

Tag chips stay multi-select AND. Status chips (active/dormant/answered)
are single-select and apply to questions only — theme nodes never dim by
status.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 8: Adapt click-to-navigate**

Find where garden binds `click` on a node group to navigate to `/garden/<slug>/`. Update to dispatch by kind:

```js
nodeG.on('click', (event, d) => {
  if (event.defaultPrevented) return;  // drag suppresses click
  const url = d.kind === 'theme'
    ? `/research/themes/${d.slug}/`
    : `/research/questions/${d.slug}/`;
  window.location.href = url;
});
```

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: click-to-navigate by node kind

Theme nodes navigate to /research/themes/<slug>/; question nodes to
/research/questions/<slug>/.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 9: Adapt the persistence cache key prefix**

Find where garden writes/reads positions in `localStorage`. The key likely starts with `garden-graph-positions:` — change to `research-graph-positions:`. This prevents the two graphs from colliding in storage.

```bash
grep -n "garden-graph-positions\|localStorage" assets/js/research-graph.js
```

Replace the prefix in every read/write callsite.

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: namespace positions cache as research-graph-positions:

Avoids localStorage key collision with garden's cache.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 10: Mobile fallback — toggle navigates instead of mounting**

On viewports ≤720px, the toggle button on `/research/` should navigate to `/research/graph/` rather than open the panel. Mirror garden's pattern. Find garden's mobile detection (likely a `window.matchMedia('(max-width: 720px)')` check) and replicate the navigation target.

```js
toggle.addEventListener('click', (event) => {
  if (window.matchMedia('(max-width: 720px)').matches) {
    event.preventDefault();
    window.location.href = '/research/graph/';
    return;
  }
  // … existing desktop panel-mount logic
});
```

**Commit:**

```bash
git add assets/js/research-graph.js
git commit -m "research-graph.js: mobile toggle navigates to /research/graph/

≤720px viewports get the standalone page instead of the cramped panel.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 11: Smoke test in the browser**

```bash
hugo server --buildDrafts
```

Visit `http://localhost:1313/research/` and click ⊞ Graph. Expected:
- Panel slides in from right.
- 9 nodes appear: 3 squares (themes) + 6 circles (questions).
- 8 edges visible: 7 solid (parent-child) + 1 dashed (the story-atoms cross-theme link).
- Drag a node → stays put on release.
- Wheel-zoom + drag-pan work.
- Tag chips render at the top of the panel; clicking `memory` dims non-matching nodes.
- Status chips render; clicking `dormant` dims active/answered questions but leaves themes opaque.
- Click a node → browser navigates to the right URL.
- ✕ closes the panel.

Without §31 styling yet, nodes will look unstyled (no fill color, no shape distinction beyond what's intrinsic to rect vs circle). The dashed cross-theme edge won't have its dasharray yet (that's CSS in §31). The next task fixes those.

Visit `http://localhost:1313/research/graph/`. Expected: full-page graph, same nodes + edges, no panel chrome.

Resize browser to ≤720px on `/research/`. Click ⊞ Graph. Expected: navigates to `/research/graph/`.

Garden side regression check:
- `/garden/` panel still works.
- `/garden/the-save-game/` panel still works (in-stack markers — wait, in-stack is garden-only, that's expected).
- `/garden/graph/` standalone still works.

---

## Task 8: CSS §31 — research-specific overrides

After Task 7, the graph functions but is unstyled. This task adds the theme palette fills, shape distinction, and cross-theme dashed edges.

**Files:**
- Modify: `assets/css/main.css` (append §31 after §30)

- [ ] **Step 1: Locate the end of §30 in `assets/css/main.css`**

```bash
grep -n "^/\* 30\.\|^/\* 31\." assets/css/main.css
```

Confirm §30 is the last numbered section. §31 appends below.

- [ ] **Step 2: Append §31**

```css
/* 31. Research graph
   ───────────────────────────────────────────────────────── */

/* Theme palette — deterministic by themePaletteOrder index from the data blob.
   Theme slugs sort ascending by `weight`; index drives fill color. */
.graph-node[data-theme-color="0"] rect,
.graph-node[data-theme-color="0"] circle { fill: var(--color-burgundy); }
.graph-node[data-theme-color="1"] rect,
.graph-node[data-theme-color="1"] circle { fill: var(--color-steel); }
.graph-node[data-theme-color="2"] rect,
.graph-node[data-theme-color="2"] circle { fill: var(--color-green); }

/* Shape variants. Themes get a thin ink stroke to lift them from question circles. */
.graph-node-theme rect {
  stroke: var(--color-ink);
  stroke-width: 1.5;
}
.graph-node-question circle {
  /* fill-only, no stroke */
}

/* Hover + focus. */
.graph-node:hover { opacity: 0.85; cursor: pointer; }
.graph-node:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}

/* Edges — defaults inherited from .graph-edge (added in §27 hoist if not present;
   otherwise specified here). */
.graph-edge {
  stroke: var(--color-ink-soft);
  stroke-width: 1;
  fill: none;
}
.graph-edge-cross-theme {
  stroke-dasharray: 4 3;
  opacity: 0.6;
}
```

- [ ] **Step 3: Verify `--color-green` and `--color-steel` exist as tokens**

```bash
grep -n "color-green\|color-steel\|color-burgundy" assets/css/main.css | head -10
```

Expected: all three defined on `:root` and `:root[data-theme="dark"]` (and in the prefers-color-scheme media block). If any is missing, fix the token block before continuing — this is a hard contract for §31 to work.

- [ ] **Step 4: Browser verification**

Visit `http://localhost:1313/research/`. Click ⊞ Graph. Expected:
- Theme squares: 3 of them, one burgundy, one steel, one green (palette indices 0/1/2).
- Question circles: each one matches its theme's color (memory-and-play questions are burgundy, etc.).
- The cross-theme edge is dashed; parent-child edges are solid.
- Hover on a node: opacity dips slightly; cursor is pointer.
- Tab through nodes (keyboard): focused node gets the ink outline.

Toggle dark mode (theme button in the header). Expected: colors swap to the dark palette versions of burgundy/steel/green; contrast still readable.

- [ ] **Step 5: Run the contrast check**

```bash
python3 tools/check-contrast.py
```

Expected: exit 0. (The four documented WCAG pairings aren't changed; the new color usages are decorative.)

- [ ] **Step 6: Commit**

```bash
git add assets/css/main.css
git commit -m "$(cat <<'EOF'
CSS §31: research graph styling

Theme palette via data-theme-color attribute (0=burgundy, 1=steel, 2=green
— index from themePaletteOrder in the data blob). Themes render as
stroked rects, questions as fill-only circles. Cross-theme edges get
stroke-dasharray; parent-child stay solid. Hover + focus-visible
indicators added.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

**🔍 REVIEW CHECKPOINT 5** — Graph renders fully styled. Halt for review before Task 9.

---

## Task 9: Dev-server spot-check + CLAUDE.md update + bundle size capture

Slice closure. Run through the spec §8 checklist, record bundle sizes, update project memory.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Run the full CI gate locally**

```bash
python3 tools/check-contrast.py
python3 tools/check_fixtures.py
python3 -m unittest tools.test_check_fixtures -v
python3 tools/check_garden_fixtures.py
python3 -m unittest tools.test_check_garden_fixtures -v
python3 tools/check_garden_links.py
python3 -m unittest tools.test_check_garden_links -v
python3 tools/check_filter_chips_config.py
python3 -m unittest tools.test_check_filter_chips_config -v
python3 tools/check_research_fixtures.py
python3 -m unittest tools.test_check_research_fixtures -v
python3 tools/check_research_links.py
python3 -m unittest tools.test_check_research_links -v
```

Expected: all 13 gates pass, all unit tests pass (including the three new tests from Task 2).

- [ ] **Step 2: Produce a production build to capture bundle sizes**

If you have a dev server running, **kill it first** (production build poisons the dev-server output with a MIME mismatch on CSS — documented gotcha). Then:

```bash
pkill -f 'hugo server' 2>/dev/null
rm -rf public/
hugo --minify
```

Expected: clean build, no errors. Capture bundle sizes:

```bash
ls -lh public/js/*.js
```

Record the sizes — they go into CLAUDE.md. Expected shape:

| Bundle | Size |
|---|---|
| `core.<hash>.js` | ~1.4 KB (unchanged) |
| `essay.<hash>.js` | ~5 KB (unchanged) |
| `garden.<hash>.js` | ~119 KB (unchanged) |
| `research.<hash>.js` | ~110–120 KB (similar to garden; copy + trim of garden-graph.js minus stack/local features) |

If the research bundle is substantially smaller or larger than ~110–120 KB, eyeball the trim — likely a feature wasn't fully removed or vendor modules aren't loading the same way.

- [ ] **Step 3: Run the spec §8 dev-server spot-check**

Restart the dev server:

```bash
hugo server --buildDrafts
```

Run through every item in `docs/superpowers/specs/2026-05-11-research-graph-design.md` §8 (dev-server spot-check). Each item should pass. List any deltas — they're the closure list.

- [ ] **Step 4: Update `CLAUDE.md` — §"CSS pipeline"**

Find the line that lists §27 in the "organized into numbered sections" enumeration. Update:

- §27 description: change from "garden graph panel" to "graph (shared) — toggle, panel chrome, toolbar, canvas, legend, resize"
- Append §31 to the list: "31 research graph"

- [ ] **Step 5: Update `CLAUDE.md` — §"Layouts"**

Add `layouts/research/graph.html` to the research layouts subsection:

> - `layouts/research/graph.html` — standalone `/research/graph/` page (mobile fallback + deep link). Mirrors `layouts/garden/graph.html`.

- [ ] **Step 6: Update `CLAUDE.md` — §"Partials"**

Add four new entries under the research/* group:

> - `research/graph-data.html` (build-time `partialCached` data partial — walks themes + questions, emits `{themes, questions, edges, themePaletteOrder}` JSON; parent-child edges from `theme` + `parent_question`, cross-theme edges derived from shared `supporting_notes`)
> - `research/graph-script.html` (wraps the JSON in `<script type="application/json" id="research-graph-data">` via `safeJS`)
> - `research/graph-panel.html` (side-panel scaffolding `<aside id="research-graph-panel" class="graph-panel">`; populated by `research-graph.js`)

Plus on the toggle button class, mention in passing in the existing `layouts/research/list.html` description.

- [ ] **Step 7: Update `CLAUDE.md` — §"JS pipeline"**

Find the "Multi-entry bundling" paragraph. Add a fourth bundle entry:

> - `js/entry-research.js` → `js/research.<hash>.js` (~<size> KB) — `research-graph.js` (which dynamically imports the same vendored d3 modules as garden); loaded only on `/research/` (index) and `/research/graph/` (standalone). Theme + question pages stay on the core bundle. Page-narrow predicate over section-wide.

Replace `<size>` with the actual size from Step 2.

Mention `research-graph.js` in the "Module roles" paragraph alongside `garden-graph.js`, noting that both share scaffolding CSS classes (`.graph-*`) but their JS modules are independent copies (per the spec's reuse decision).

- [ ] **Step 8: Update `CLAUDE.md` — §"Project status"**

Add a new "Phase 5 — research surface (Slice 2) complete" paragraph after the existing Slice 1 entry. Sample:

> **Phase 5 — research surface (Slice 2) complete (2026-05-11).** Force-directed research graph on `/research/` — `⊞ Graph` toggle next to the filter chips reveals a slide-in side panel; mobile (≤720px) navigates to a standalone `/research/graph/` page. Build-time data partial (`partials/research/graph-data.html`) emits `{themes, questions, edges, themePaletteOrder}`; parent-child edges from `theme` + `parent_question` (solid), cross-theme edges derived from shared `supporting_notes` (dashed, annotated with `via:<garden-slug>`). Theme nodes render as squares, question nodes as circles; fill follows the theme palette (`burgundy / steel / green`, deterministic by `theme.weight`). Filter chips inside the panel: tag (multi-select AND) + status (single-select, questions only). New JS module `assets/js/research-graph.js` is a copy + trim of `garden-graph.js` (drops stack-coordination + local-graph N-hop mode). Multi-entry bundle gains `entry-research.js` → `js/research.<size>.js`, loaded page-narrow on `/research/` and `/research/graph/` only. CSS hoist refactor renames `.garden-graph-*` → `.graph-*` for shared scaffolding (§27 → "Graph (shared)"); new §31 "Research graph" adds the theme palette + shape + edge-class overrides. Linter extension: `tools/check_research_fixtures.py` gains a `validate_unique_theme_weights()` assertion so `themePaletteOrder` stays deterministic — three new unit tests. No new CI gates; no fixture changes (Slice 1's set exercises every variant — 9 nodes, 7 parent-child edges, 1 cross-theme edge).

- [ ] **Step 9: Update `CLAUDE.md` — §"Project status" remaining-slices list**

Remove the "research graph runtime deferred to Slice 2" line from the Slice 1 entry (no longer deferred) or mark it as shipped. Update the "Phase 2 — remaining slices" section accordingly — the bullet "Research theme cards + question hubs + research graph — Phase 5." can be marked complete, since Phase 5 is now done with both slices.

- [ ] **Step 10: Run hugo build one more time, post-CLAUDE.md edits**

```bash
hugo --minify
```

Expected: clean build (the README-style edits don't affect Hugo output, but a final sanity check is cheap).

- [ ] **Step 11: Final commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
CLAUDE.md: document research graph (Slice 2) shipment

§CSS pipeline: §27 renamed to "Graph (shared)"; §31 "Research graph"
added. §Layouts: research/graph.html. §Partials: four new research/*
graph partials. §JS pipeline: research bundle added to the multi-entry
list; page-narrow load. §Project status: Slice 2 complete entry.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

**🔍 REVIEW CHECKPOINT 6** — Slice closed. Ready for the user's standard pre-merge dev-server eyeball + merge.

---

## Self-review summary

Spec coverage check: every numbered section in the spec maps to one or more tasks:

| Spec section | Plan task(s) |
|---|---|
| §5.1 Data partial | Task 3 |
| §5.2 Script partial | Task 3 |
| §5.3 Panel partial | Task 5 |
| §5.4 Standalone page | Task 4 |
| §5.5 Index edits | Task 5 |
| §5.6 JS module | Task 6 (skeleton) + Task 7 (adapt) |
| §5.7 Entry + bundling | Task 6 |
| §5.8 CSS hoist | Task 1 |
| §5.8 CSS §31 | Task 8 |
| §5.9 Linter extension | Task 2 |
| §6 Files touched | All tasks combined |
| §7 Fixture coverage | No task (no fixture changes) |
| §8 Build + verification | Task 9 |
| §9 Slice closure | Task 9 |
