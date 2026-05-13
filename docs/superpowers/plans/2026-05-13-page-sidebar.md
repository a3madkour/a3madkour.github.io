# Page Sidebar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a rotated-labels (book-spine direction) section sidebar to every multi-section page template; replace it with a sticky horizontal dots strip at mobile width.

**Architecture:** One shared partial `layouts/partials/page-sidebar.html` taking a `sections` slice. Each layout (home, about, research-theme, research-question, four library leaves) wraps its top-level section blocks with stable `id` attributes and passes a hardcoded slice of `(id, label)` pairs to the partial. A single IntersectionObserver added to `assets/js/nav.js` (core bundle, loaded everywhere) toggles `.is-active` on all sidebar anchors. CSS §41 renders the desktop rail (`writing-mode: vertical-rl; transform: rotate(180deg)`) and the mobile sticky dots strip.

**Tech Stack:** Hugo extended ≥ 0.148.0, hand-rolled CSS, vanilla JS in the core bundle (`assets/js/nav.js`), no npm, Python stdlib only for linters.

**Parent spec:** `docs/superpowers/specs/2026-05-13-page-sidebar-design.md`.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `layouts/partials/page-sidebar.html` | Create | Shared partial; takes `sections` slice; emits `.page-sidebar` with desktop rail + mobile strip DOMs. |
| `assets/js/nav.js` | Modify (append) | New IntersectionObserver + click-handler scoped to `.page-sidebar a[href^="#"]`. |
| `layouts/home.html` | Modify | Add `id="essays"` to inline `<section class="home-essays">`; call partial near the top of `<main>`. |
| `layouts/partials/home/currently.html` | Modify | Add `id="currently"` to outer `<section class="home-currently">`. |
| `layouts/partials/home/research-strip.html` | Modify | Add `id="research-strip"` to outer `<section class="home-research-strip">`. |
| `layouts/partials/home/garden-strip.html` | Modify | Add `id="garden-strip"` to outer `<section class="home-garden-strip">`. |
| `layouts/partials/home/studio-strip.html` | Modify | Add `id="studio-strip"` to outer `<section class="home-studio-strip">`. |
| `layouts/about/single.html` | Modify | Add 4 `id`s to existing `<section class="about-section">` wrappers; call partial. |
| `layouts/research-theme/single.html` | Modify | Add 4 `id`s to existing section wrappers; build conditional slice; call partial. |
| `layouts/research-question/single.html` | Modify | Add 7 `id`s to existing section wrappers; build conditional slice; call partial. |
| `layouts/partials/library/currently-active.html` | Modify | Add `id="currently-active"`. |
| `layouts/partials/library/year-section.html` | Modify | Add `id="{{ $year }}"`. |
| `layouts/library-reading/list.html` | Modify | Add `id="upnext"` to inline upnext section; build sections slice; call partial. |
| `layouts/library-listening/list.html` | Modify | Same pattern. |
| `layouts/library-playing/list.html` | Modify | Same pattern. |
| `layouts/library-watching/list.html` | Modify | Same pattern. |
| `assets/css/main.css` | Append | §41 — desktop rail + mobile strip + 800px responsive + focus-visible. |

---

## Working Directory & Branch

Work happens on a slice branch `slice/page-sidebar` off `master`. Before Task 1:

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git checkout -b slice/page-sidebar
```

All task commits land on this branch. Final merge happens via the existing slice-finishing flow after the dev-server spot-check in Task 7.

---

### Task 1: Shared partial + nav.js extension

**Files:**
- Create: `layouts/partials/page-sidebar.html`
- Modify: `assets/js/nav.js` (append at end)

- [ ] **Step 1: Create the shared partial**

Write `layouts/partials/page-sidebar.html`:

```html
{{- /* Inputs:
       .sections — slice of dicts {id, label}, in DOM order.
                   If <2 entries, the partial emits nothing.
   Emits both a desktop rotated-labels rail and a mobile sticky dots strip.
   CSS in §41 hides one per breakpoint; JS in assets/js/nav.js toggles
   .is-active on matching anchors as the user scrolls.
*/ -}}
{{- $sections := .sections | default slice -}}
{{- if ge (len $sections) 2 -}}
<aside class="page-sidebar" aria-label="Page sections">
  <nav class="page-sidebar--rail">
    {{- range $sections -}}
      <a href="#{{ .id }}" class="page-sidebar-label">{{ .label }}</a>
    {{- end -}}
  </nav>
  <nav class="page-sidebar--strip">
    {{- range $sections -}}
      <a href="#{{ .id }}" class="page-sidebar-dot" aria-label="{{ .label }}"></a>
    {{- end -}}
  </nav>
</aside>
{{- end -}}
```

- [ ] **Step 2: Read the end of `assets/js/nav.js`**

Run: `tail -5 assets/js/nav.js`
Expected: shows the existing IntersectionObserver block ending with the closing `});` of the `forEach` call (the existing essay-TOC observer).

- [ ] **Step 3: Append the page-sidebar observer + click handler to `assets/js/nav.js`**

Append at the end of the file (after the existing block, with one blank line of separation):

```js

// Page sidebar — section observer + click smooth-scroll.
// Activates on any page that calls partials/page-sidebar.html.
window.addEventListener('DOMContentLoaded', () => {
  const sidebarLinks = document.querySelectorAll('.page-sidebar a[href^="#"]');
  if (sidebarLinks.length === 0) return;

  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const id = entry.target.id;
      sidebarLinks.forEach((a) => {
        a.classList.toggle('is-active', a.getAttribute('href') === `#${id}`);
      });
    });
  }, { rootMargin: '-30% 0px -60% 0px' });

  sidebarLinks.forEach((a) => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) sectionObserver.observe(target);
  });

  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  sidebarLinks.forEach((a) => {
    a.addEventListener('click', (e) => {
      const href = a.getAttribute('href');
      const target = document.querySelector(href);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' });
      history.pushState(null, '', href);
    });
  });
});
```

- [ ] **Step 4: Verify the site builds**

Run: `hugo --buildDrafts --quiet`
Expected: exit 0, no template errors. (No template uses the partial yet; this confirms the new file parses and the JS file is still valid.)

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/page-sidebar.html assets/js/nav.js
git commit -m "$(cat <<'EOF'
sidebar: shared page-sidebar partial + nav.js observer

Adds layouts/partials/page-sidebar.html (takes sections slice, emits
desktop rail + mobile strip DOMs; suppresses when <2 entries).
Extends assets/js/nav.js with an IntersectionObserver scoped to
.page-sidebar a[href^="#"] that toggles .is-active on matching anchors
as the user scrolls past each section; click handler smooth-scrolls
to the target (auto if prefers-reduced-motion).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Homepage integration

**Files:**
- Modify: `layouts/partials/home/currently.html`
- Modify: `layouts/partials/home/research-strip.html`
- Modify: `layouts/partials/home/garden-strip.html`
- Modify: `layouts/partials/home/studio-strip.html`
- Modify: `layouts/home.html`

- [ ] **Step 1: Add `id="currently"` to `partials/home/currently.html`**

Find the line:
```html
<section class="home-currently" data-active-count="{{ len $rows }}">
```

Replace with:
```html
<section id="currently" class="home-currently" data-active-count="{{ len $rows }}">
```

- [ ] **Step 2: Add `id="research-strip"` to `partials/home/research-strip.html`**

Find the line:
```html
<section class="home-research-strip">
```

Replace with:
```html
<section id="research-strip" class="home-research-strip">
```

- [ ] **Step 3: Add `id="garden-strip"` to `partials/home/garden-strip.html`**

Find the line:
```html
<section class="home-garden-strip">
```

Replace with:
```html
<section id="garden-strip" class="home-garden-strip">
```

- [ ] **Step 4: Add `id="studio-strip"` to `partials/home/studio-strip.html`**

Find the line:
```html
<section class="home-studio-strip">
```

Replace with:
```html
<section id="studio-strip" class="home-studio-strip">
```

- [ ] **Step 5: Add `id="essays"` to `layouts/home.html` and call the sidebar partial**

In `layouts/home.html`, find:
```html
  <section class="home-essays">
```

Replace with:
```html
  <section id="essays" class="home-essays">
```

Then find the line `{{ partial "home/hero.html" . }}` (currently line 10). Insert the sidebar partial call **before** the hero call, on a new line. The relevant block changes from:

```html
  {{- if $hasWorks }}{{ partial "works/glyph-sprite.html" . }}{{ end -}}
  {{ partial "home/hero.html" . }}
```

to:

```html
  {{- if $hasWorks }}{{ partial "works/glyph-sprite.html" . }}{{ end -}}
  {{ partial "page-sidebar.html" (dict "sections" (slice
      (dict "id" "currently"      "label" "Currently")
      (dict "id" "essays"         "label" "Essays")
      (dict "id" "research-strip" "label" "Chasing")
      (dict "id" "garden-strip"   "label" "Garden")
      (dict "id" "studio-strip"   "label" "Studio")
    )) }}
  {{ partial "home/hero.html" . }}
```

- [ ] **Step 6: Verify the site builds**

Run: `hugo --buildDrafts --quiet`
Expected: exit 0, no template errors.

- [ ] **Step 7: Sanity-check the rendered homepage**

Run:
```bash
hugo --buildDrafts --destination /tmp/check2 && \
  echo "aside count: $(grep -c 'class="page-sidebar"' /tmp/check2/index.html)" && \
  echo "rail labels: $(grep -c 'class="page-sidebar-label"' /tmp/check2/index.html)" && \
  echo "strip dots: $(grep -c 'class="page-sidebar-dot"' /tmp/check2/index.html)" && \
  echo "section ids: $(grep -oE 'id="(currently|essays|research-strip|garden-strip|studio-strip)"' /tmp/check2/index.html | sort -u | wc -l)" && \
  rm -rf /tmp/check2
```
Expected: aside count `1`, rail labels `5`, strip dots `5`, section ids `5`.

- [ ] **Step 8: Commit**

```bash
git add layouts/home.html layouts/partials/home/
git commit -m "$(cat <<'EOF'
sidebar: homepage integration (5 anchors)

Adds id="…" to the four home/ partial wrappers + the inline
<section class="home-essays">. layouts/home.html calls
page-sidebar.html with the homepage's five-anchor list
(currently / essays / research-strip / garden-strip / studio-strip)
just above the hero call.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: About integration

**Files:**
- Modify: `layouts/about/single.html`

The current file has four `<section class="about-section">` wrappers (lines 15, 22, 40, 65). Each contains an `<h2>` with the section name. The Hero section (line 4 `<section class="about-hero">`) is the page-top anchor and **does not** appear in the sidebar.

Note: the spec §3.2 lists a `now` anchor, but the actual About template does not yet render a Now widget (Phase 3-blocked per CLAUDE.md). The v1 sidebar lists only the four sections present.

- [ ] **Step 1: Add `id="bio"` to the Bio section**

Find:
```html
  <section class="about-section">
    <h2>Bio</h2>
```

Replace with:
```html
  <section id="bio" class="about-section">
    <h2>Bio</h2>
```

- [ ] **Step 2: Add `id="where"` to the Where section**

Find:
```html
  <section class="about-section">
    <h2>Where</h2>
```

Replace with:
```html
  <section id="where" class="about-section">
    <h2>Where</h2>
```

- [ ] **Step 3: Add `id="connect"` to the Connect section**

Find:
```html
  <section class="about-section">
    <h2>Connect</h2>
```

Replace with:
```html
  <section id="connect" class="about-section">
    <h2>Connect</h2>
```

- [ ] **Step 4: Add `id="colophon"` to the Colophon section**

Find:
```html
  <section class="about-section">
    <h2>Colophon</h2>
```

Replace with:
```html
  <section id="colophon" class="about-section">
    <h2>Colophon</h2>
```

- [ ] **Step 5: Call the sidebar partial near the top of `<main>`**

Find the opening:
```html
<main class="reading-column about-page">

  <section class="about-hero">
```

Replace with:
```html
<main class="reading-column about-page">

  {{ partial "page-sidebar.html" (dict "sections" (slice
      (dict "id" "bio"      "label" "Bio")
      (dict "id" "where"    "label" "Where")
      (dict "id" "connect"  "label" "Connect")
      (dict "id" "colophon" "label" "Colophon")
    )) }}

  <section class="about-hero">
```

- [ ] **Step 6: Verify the site builds**

Run: `hugo --buildDrafts --quiet`
Expected: exit 0.

- [ ] **Step 7: Sanity-check `/about/`**

Run:
```bash
hugo --buildDrafts --destination /tmp/check3 && \
  echo "rail labels: $(grep -c 'class="page-sidebar-label"' /tmp/check3/about/index.html)" && \
  echo "section ids: $(grep -oE 'id="(bio|where|connect|colophon)"' /tmp/check3/about/index.html | sort -u | wc -l)" && \
  rm -rf /tmp/check3
```
Expected: rail labels `4`, section ids `4`.

- [ ] **Step 8: Commit**

```bash
git add layouts/about/single.html
git commit -m "$(cat <<'EOF'
sidebar: about-page integration (4 anchors)

Adds id="…" to four <section class="about-section"> wrappers
(bio/where/connect/colophon) and calls page-sidebar.html. Hero is
excluded; Now widget will join the slice when it lands (Phase 3).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Research theme + research question integration

**Files:**
- Modify: `layouts/research-theme/single.html`
- Modify: `layouts/research-question/single.html`

#### Part A — Research theme

The theme template has 4 conditional section wrappers. The sidebar slice is built dynamically before the partial call.

- [ ] **Step 1: Add `id="questions"` to `three-col-questions`**

Find:
```html
  <section class="three-col-questions">
```

Replace with:
```html
  <section id="questions" class="three-col-questions">
```

- [ ] **Step 2: Add `id="outputs"` to `research-outputs`**

Find:
```html
  {{ if $allOutputs }}
  <section class="research-outputs">
```

Replace with:
```html
  {{ if $allOutputs }}
  <section id="outputs" class="research-outputs">
```

- [ ] **Step 3: Add `id="garden-topic"` to `research-garden-embed`**

Find:
```html
    <section class="research-garden-embed">
```

Replace with:
```html
    <section id="garden-topic" class="research-garden-embed">
```

- [ ] **Step 4: Add `id="framing"` to `research-theme-body`**

Find:
```html
  {{ if .Content }}
  <section class="research-theme-body">
```

Replace with:
```html
  {{ if .Content }}
  <section id="framing" class="research-theme-body">
```

- [ ] **Step 5: Build the sections slice and call the partial**

Find the opening:
```html
<main class="reading-column research-theme-page">

  <nav class="research-breadcrumb" aria-label="Breadcrumb">
```

Replace with:
```html
<main class="reading-column research-theme-page">

  {{- $sections := slice -}}
  {{- if or $active $dormant $answered -}}
    {{- $sections = $sections | append (dict "id" "questions" "label" "Questions") -}}
  {{- end -}}
  {{- if $allOutputs -}}
    {{- $sections = $sections | append (dict "id" "outputs" "label" "Outputs") -}}
  {{- end -}}
  {{- if .Params.garden_topic_ref -}}
    {{- $sections = $sections | append (dict "id" "garden-topic" "label" "Topic") -}}
  {{- end -}}
  {{- if .Content -}}
    {{- $sections = $sections | append (dict "id" "framing" "label" "Framing") -}}
  {{- end -}}
  {{ partial "page-sidebar.html" (dict "sections" $sections) }}

  <nav class="research-breadcrumb" aria-label="Breadcrumb">
```

#### Part B — Research question

The question template has 7 section wrappers, several conditional. The sidebar slice is also dynamic.

- [ ] **Step 6: Add `id="thinking"` to `research-current-thinking`**

Find:
```html
  <section class="research-current-thinking">
```

Replace with:
```html
  <section id="thinking" class="research-current-thinking">
```

- [ ] **Step 7: Add `id="sub"` to `research-sub-questions`**

Find:
```html
  {{ if $subQs }}
  <section class="research-sub-questions">
```

Replace with:
```html
  {{ if $subQs }}
  <section id="sub" class="research-sub-questions">
```

- [ ] **Step 8: Add `id="siblings"` to `research-siblings`**

Find:
```html
  {{ if $siblings }}
  <section class="research-siblings">
```

Replace with:
```html
  {{ if $siblings }}
  <section id="siblings" class="research-siblings">
```

- [ ] **Step 9: Add `id="notes"` to `research-supporting-notes`**

Find:
```html
  {{ with .Params.supporting_notes }}
  <section class="research-supporting-notes">
```

Replace with:
```html
  {{ with .Params.supporting_notes }}
  <section id="notes" class="research-supporting-notes">
```

- [ ] **Step 10: Add `id="essays"` to `research-related-essays`**

Find:
```html
  {{ with .Params.related_essays }}
  <section class="research-related-essays">
```

Replace with:
```html
  {{ with .Params.related_essays }}
  <section id="essays" class="research-related-essays">
```

- [ ] **Step 11: Add `id="outputs"` to `research-outputs` (question template)**

Find:
```html
  {{ with .Params.outputs }}
  <section class="research-outputs">
```

Replace with:
```html
  {{ with .Params.outputs }}
  <section id="outputs" class="research-outputs">
```

- [ ] **Step 12: Add `id="backlinks"` to `research-backlinks`**

Find:
```html
  <section class="research-backlinks">
    <h2>Backlinks</h2>
```

Replace with:
```html
  <section id="backlinks" class="research-backlinks">
    <h2>Backlinks</h2>
```

- [ ] **Step 13: Build the sections slice and call the partial**

Find the opening:
```html
<main class="reading-column research-question-hub">

  <nav class="research-breadcrumb" aria-label="Breadcrumb">
```

Replace with:
```html
<main class="reading-column research-question-hub">

  {{- $sections := slice -}}
  {{- if .Content -}}
    {{- $sections = $sections | append (dict "id" "thinking"  "label" "Thinking") -}}
  {{- end -}}
  {{- if $subQs -}}
    {{- $sections = $sections | append (dict "id" "sub"       "label" "Sub-Qs") -}}
  {{- end -}}
  {{- if $siblings -}}
    {{- $sections = $sections | append (dict "id" "siblings"  "label" "Siblings") -}}
  {{- end -}}
  {{- if .Params.supporting_notes -}}
    {{- $sections = $sections | append (dict "id" "notes"     "label" "Notes") -}}
  {{- end -}}
  {{- if .Params.related_essays -}}
    {{- $sections = $sections | append (dict "id" "essays"    "label" "Essays") -}}
  {{- end -}}
  {{- if .Params.outputs -}}
    {{- $sections = $sections | append (dict "id" "outputs"   "label" "Outputs") -}}
  {{- end -}}
  {{- $sections = $sections | append (dict "id" "backlinks" "label" "Links") -}}
  {{ partial "page-sidebar.html" (dict "sections" $sections) }}

  <nav class="research-breadcrumb" aria-label="Breadcrumb">
```

- [ ] **Step 14: Verify the site builds**

Run: `hugo --buildDrafts --quiet`
Expected: exit 0.

- [ ] **Step 15: Sanity-check a research theme page**

Run:
```bash
hugo --buildDrafts --destination /tmp/check4 && \
  echo "theme rail labels: $(grep -c 'class="page-sidebar-label"' /tmp/check4/research/themes/procedural-narrative/index.html)" && \
  echo "question rail labels: $(grep -c 'class="page-sidebar-label"' /tmp/check4/research/questions/what-is-a-narrative-atom/index.html)" && \
  rm -rf /tmp/check4
```
Expected: theme rail labels ≥ 2 (depends on fixture), question rail labels ≥ 2.

- [ ] **Step 16: Commit**

```bash
git add layouts/research-theme/single.html layouts/research-question/single.html
git commit -m "$(cat <<'EOF'
sidebar: research theme + question integration

Theme template gains 4 conditional anchors (questions / outputs /
garden-topic / framing); the slice filter mirrors each section's
existing render condition. Question template gains 7 anchors
(thinking / sub / siblings / notes / essays / outputs / backlinks);
only backlinks is unconditional. The slice is assembled at template
top and passed to page-sidebar.html.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Library leaves integration

**Files:**
- Modify: `layouts/partials/library/currently-active.html`
- Modify: `layouts/partials/library/year-section.html`
- Modify: `layouts/library-reading/list.html`
- Modify: `layouts/library-listening/list.html`
- Modify: `layouts/library-playing/list.html`
- Modify: `layouts/library-watching/list.html`

- [ ] **Step 1: Add `id="currently-active"` to `partials/library/currently-active.html`**

Find:
```html
<section class="library-currently" data-active-count="{{ len $items }}">
```

Replace with:
```html
<section id="currently-active" class="library-currently" data-active-count="{{ len $items }}">
```

- [ ] **Step 2: Add `id="{{ $year }}"` to `partials/library/year-section.html`**

Find:
```html
<section class="library-year" data-year="{{ $year }}">
```

Replace with:
```html
<section id="{{ $year }}" class="library-year" data-year="{{ $year }}">
```

(The id will render as bare year strings like `id="2026"`. HTML5 accepts numeric-leading ids; `<a href="#2026">` resolves correctly.)

- [ ] **Step 3: Add `id="upnext"` + sidebar call to `layouts/library-reading/list.html`**

First, find:
```html
      <section class="library-upnext">
```

Replace with:
```html
      <section id="upnext" class="library-upnext">
```

Then find the opening of the main element:
```html
<main class="library-leaf-page" data-library-page="reading">
  <header class="library-page-header">
```

Replace with:
```html
<main class="library-leaf-page" data-library-page="reading">
  {{- $sections := slice -}}
  {{- if $active -}}
    {{- $sections = $sections | append (dict "id" "currently-active" "label" "Now") -}}
  {{- end -}}
  {{- range $years -}}
    {{- $sections = $sections | append (dict "id" . "label" .) -}}
  {{- end -}}
  {{- if $undated -}}
    {{- $sections = $sections | append (dict "id" "Undated" "label" "Undated") -}}
  {{- end -}}
  {{- if $queued -}}
    {{- $sections = $sections | append (dict "id" "upnext" "label" "Next") -}}
  {{- end -}}
  {{ partial "page-sidebar.html" (dict "sections" $sections) }}

  <header class="library-page-header">
```

(The "Undated" year section uses `id="Undated"` to match the year-section partial's output for that bucket — see the corresponding range over `$undated` in the list file.)

- [ ] **Step 4: Repeat Step 3 for `layouts/library-listening/list.html`**

Same change pattern. The `data-library-page` value is `"listening"`. The slice-building block is identical.

- [ ] **Step 5: Repeat Step 3 for `layouts/library-playing/list.html`**

Same change pattern. The `data-library-page` value is `"playing"`. The slice-building block is identical.

- [ ] **Step 6: Repeat Step 3 for `layouts/library-watching/list.html`**

Same change pattern. The `data-library-page` value is `"watching"`. The slice-building block is identical.

- [ ] **Step 7: Verify the site builds**

Run: `hugo --buildDrafts --quiet`
Expected: exit 0.

- [ ] **Step 8: Sanity-check each library leaf**

Run:
```bash
hugo --buildDrafts --destination /tmp/check5 && \
  for leaf in reading listening playing watching; do
    n=$(grep -c 'class="page-sidebar-label"' /tmp/check5/library/$leaf/index.html 2>/dev/null || echo 0)
    echo "library/$leaf rail labels: $n"
  done && \
  rm -rf /tmp/check5
```
Expected: each leaf prints ≥ 2 (depends on fixture data).

- [ ] **Step 9: Commit**

```bash
git add layouts/partials/library/ layouts/library-reading/list.html layouts/library-listening/list.html layouts/library-playing/list.html layouts/library-watching/list.html
git commit -m "$(cat <<'EOF'
sidebar: library leaves integration (data-driven section list)

Adds id="currently-active" to partials/library/currently-active.html,
id="{{ $year }}" to partials/library/year-section.html, and
id="upnext" to the inline upnext sections of the four list files.
Each list file builds its sections slice from the partitioned items
(active / years / undated / queued) and passes it to page-sidebar.html.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: CSS §41 — desktop rail + mobile strip + responsive

**Files:**
- Modify: `assets/css/main.css` (append at the end)

- [ ] **Step 1: Append §41 to `assets/css/main.css`**

Append at the END of the file:

```css
/* §41 Page sidebar — vertical rotated-labels rail (desktop) +
 * sticky horizontal dots strip (mobile).
 * Active state driven by IntersectionObserver in assets/js/nav.js.
 * ----------------------------------------------------------------- */

.page-sidebar { font-family: var(--font-ui); }

/* Desktop: rotated-label rail, fixed mid-viewport on the left margin */
.page-sidebar--rail {
  position: fixed;
  top: 50%;
  left: 1rem;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column-reverse;
  gap: 1.5rem;
  z-index: 5;
}
.page-sidebar-label {
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  font-size: 0.6rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  line-height: 1;
  color: var(--color-ink-soft);
  text-decoration: none;
  cursor: pointer;
}
.page-sidebar-label:hover {
  color: var(--color-burgundy);
  text-decoration: underline;
  text-underline-offset: 3px;
}
.page-sidebar-label.is-active {
  color: var(--color-burgundy);
  font-weight: 600;
}
.page-sidebar-label:focus-visible {
  outline: 1px solid var(--color-burgundy);
  outline-offset: 3px;
}

/* Mobile: horizontal dots strip, sticky just below the (non-sticky) header */
.page-sidebar--strip {
  display: none; /* hidden on desktop; shown in the @800 block */
}
.page-sidebar-dot {
  display: block;
  padding: 0.4rem;  /* hit-area expansion to ≥36×36 */
  text-decoration: none;
  position: relative;
}
.page-sidebar-dot::before {
  content: "";
  display: block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-rule);
  transition: background 0.15s, width 0.15s, height 0.15s;
}
.page-sidebar-dot.is-active::before {
  background: var(--color-burgundy);
  width: 8px;
  height: 8px;
}
.page-sidebar-dot:focus-visible {
  outline: 1px solid var(--color-burgundy);
  outline-offset: 2px;
  border-radius: 4px;
}

@media (max-width: 800px) {
  .page-sidebar--rail { display: none; }
  .page-sidebar--strip {
    display: flex;
    justify-content: center;
    gap: 0.85rem;
    padding: 0.5rem 0;
    position: sticky;
    top: 0;
    left: 0;
    right: 0;
    background: var(--color-stone);
    border-bottom: 1px solid var(--color-rule);
    z-index: 5;
  }
  /* Push scroll-into-view targets below the sticky strip (~24px). */
  main > section[id],
  main > article > section[id],
  main > .library-leaf-page section[id] { scroll-margin-top: 2.5rem; }
}
```

- [ ] **Step 2: Run the contrast verifier**

Run: `python3 tools/check-contrast.py`
Expected: exit 0. (No new tokens; only new consumers of existing burgundy/stone/rule/ink-soft pairings.)

- [ ] **Step 3: Run the linter pair tests**

Run: `pytest tools/test_check_*.py -q`
Expected: 189 passed (no content/data changes).

- [ ] **Step 4: Verify the site builds**

Run: `hugo --buildDrafts --quiet`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add assets/css/main.css
git commit -m "$(cat <<'EOF'
sidebar: css §41 — rail (vertical-rl) + mobile dots strip

Desktop: fixed mid-viewport on left margin; column-reverse so visual
order matches DOM order under bottom-to-top book-spine reading.
Mobile (≤800px): sticky horizontal dots strip below the (non-sticky)
header. scroll-margin-top on section[id] pushes scroll-into-view
targets clear of the sticky strip. Active state = color shift +
weight bump (rail) or color shift + size bump (dot) — not color
alone, per WCAG 1.4.1.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Dev-server visual spot-check (no commit unless fixes needed)

**Files:** none (verification only)

Per the session rule, do a visual spot-check before requesting merge. If you find issues, fix them as a new commit on `slice/page-sidebar` — never amend.

- [ ] **Step 1: Make sure no production build is running**

Run: `pgrep -af "hugo --minify"` — if anything matches, kill it. (Per the reference memory: production build and dev server conflict on the CSS MIME type.)

- [ ] **Step 2: Start the dev server**

Run in a separate terminal (or background): `hugo server --buildDrafts --bind 127.0.0.1 --port 1313`
Expected: listens on http://127.0.0.1:1313/.

- [ ] **Step 3: Walk the spot-check checklist for each of the 5 page templates**

Open each URL in light mode AND dark mode (toolbar toggle, 3-state):

1. **Homepage** (`/`) — rail shows 5 rotated labels (CURRENTLY / ESSAYS / CHASING / GARDEN / STUDIO) bottom-to-top on the left margin. Active label tracks scroll position. Click each label — page smooth-scrolls.
2. **About** (`/about/`) — rail shows 4 labels (BIO / WHERE / CONNECT / COLOPHON). Same active + click behavior.
3. **Research theme** (`/research/themes/procedural-narrative/`) — rail shows 1-4 labels depending on which conditional sections render for this theme fixture. Inspect the page: which sections are present? Confirm rail matches.
4. **Research question** (`/research/questions/what-is-a-narrative-atom/`) — rail shows up to 7 labels. Confirm only the unconditional `backlinks` always appears (BACKLINKS or "LINKS"). Conditional ones depend on fixture frontmatter.
5. **Library leaves** (`/library/reading/`, `/library/listening/`, `/library/playing/`, `/library/watching/`) — rail shows N labels: NOW (if active item) + each year + NEXT (if queued). Confirm year labels are bare year strings.

Then check **mobile** (DevTools responsive @ 400px) on each template:

6. Rail hides. Horizontal dots strip appears sticky below the page header.
7. Click a dot — page scrolls to the section, clear of the sticky strip (no overlap).
8. Active dot tracks scroll.

Also check:

9. **Reduced-motion mode** (DevTools → Rendering → Emulate CSS prefers-reduced-motion: reduce). Click rail label or strip dot — page jumps instantly, no smooth scroll.
10. **Dark-mode parity** on every page: rail labels and dots remain legible (`--color-ink-soft on --color-stone` AA pairing).
11. **Suppression**: if a fixture has only 1 active section (rare), the rail emits nothing on that page. Inspect HTML to confirm.

- [ ] **Step 4: If any check fails, fix and commit**

Add a new commit on `slice/page-sidebar` describing the fix. Re-run `hugo --buildDrafts --quiet` + `python3 tools/check-contrast.py` after fixing.

- [ ] **Step 5: Stop the dev server**

Kill the `hugo server` process. Site is ready for merge via the existing slice-finishing flow.

---

## Self-Review Notes

- **Spec coverage:**
  - §1 architecture → File Structure + Task 1.
  - §2 visual treatment → Task 6 (CSS §41).
  - §3 per-template integration → Tasks 2 (home), 3 (about), 4 (research theme + question), 5 (library leaves).
  - §4 accessibility → Task 1 (aria-label on partial), Task 6 (focus-visible CSS + prefers-reduced-motion handled in JS), Task 7 (verification).
  - §5 verification → Task 6 Steps 2–4 (contrast + linters + build), Task 7 (visual spot-check).
  - §6 out-of-scope → carried as deliberate non-tasks.
  - §7 commit shape → 6 commits across Tasks 1–6 (slightly more granular than the spec's 4-commit sketch — Task 4 covers two related templates and Task 5 covers four library leaves; both stay narrow per the "never amend" rule).
  - §8 risks → addressed inline: "section list drift" via co-located slice declarations (Tasks 2–5 put the slice right above the partial call); "sticky/fixed collisions" via column-reverse + fixed mid-viewport (Task 6 §41); "mobile strip scroll overlap" via `scroll-margin-top` (Task 6 §41 mobile block); "IntersectionObserver browser support" deferred to Phase 8 Lighthouse.

- **Spec-vs-layout reconciliation:** The about template does not currently have a Now section (Phase 3-blocked per CLAUDE.md). The plan drops `now` from the v1 sidebar slice; Step 5 of Task 3 lists only the four sections that actually exist. When the Now widget lands, a follow-up adds `id="now"` + a slice entry.

- **Placeholder scan:** every step contains literal code or commands; no "TODO" / "fill in" markers; commit messages are written verbatim.

- **Type consistency:** anchor `id`s, slice keys, and rendered hrefs all use the same kebab-case strings within each template. The shared partial's `{id, label}` dict shape is consistent across all five integration tasks. The CSS class names (`.page-sidebar`, `.page-sidebar--rail`, `.page-sidebar--strip`, `.page-sidebar-label`, `.page-sidebar-dot`) match between Task 1 (partial output), Task 1 Step 3 (JS selectors), and Task 6 (CSS rules).

---

*End of plan.*
