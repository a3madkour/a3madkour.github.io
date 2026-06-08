# Anchor Affordance — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a site-wide deep-link affordance — an always-visible inline `§` glyph next to every `id`-bearing element inside `<main>`, with a tiny JS module that copies the absolute URL to the clipboard on click and surfaces a top-of-viewport status banner.

**Architecture:** SSR everywhere — one shared Hugo partial emits the canonical `<a class="anchor-link">§</a>` markup. A heading render hook handles every Goldmark-emitted heading site-wide; per-shortcode injection handles the 12 D.1 semantic blocks; per-partial injection handles the 7 chrome partials. A single ~50-LoC JS module attaches one delegated click listener to `<main>`. CSS §48 styles glyph + banner using existing tokens only. A new linter pair (27th) gates the partial-emission invariant.

**Tech Stack:** Hugo (extended ≥0.162.1), hand-rolled CSS in `assets/css/main.css`, multi-entry esbuild via `js.Build`, stdlib-only Python for linters.

**Spec:** `docs/superpowers/specs/2026-06-07-anchor-affordance-design.md` (commit `b141327`).

---

## Per-task discipline

- **Commit per task.** Each task ends with a commit; the working tree should be green (`hugo --minify` builds + every test that exists at that point passes) before committing.
- **Stage by exact path.** Per session policy: pre-session bystanders live in the working tree; don't `git add .`. Each task's commit step lists exact paths.
- **No push.** Per session policy. Tasks 1-12 commit locally; the user pushes when satisfied.
- **No dotfiles work.** Site-only slice. The org-publish pipeline already emits the IDs we render against.

---

## Files touched (map)

**Created (new files):**
- `layouts/partials/anchor-link.html` — shared partial; canonical markup for `<a class="anchor-link">§</a>`.
- `layouts/_default/_markup/render-heading.html` — Hugo render hook for every Goldmark heading.
- `assets/js/anchor-link.js` — click-to-copy + banner module (~50 LoC).
- `assets/js/entry-anchor-link.js` — one-line entry that imports `anchor-link.js`.
- `tools/check_anchor_link.py` — linter that walks `public/**/*.html` and gates the partial-emission invariant inside `<main>`.
- `tools/test_check_anchor_link.py` — unit tests for the linter (paired sibling).

**Modified:**
- `assets/css/main.css` — append §48 (glyph + banner styles).
- `layouts/partials/scripts.html` — register the new entry alongside `core` + `search`.
- `layouts/shortcodes/{theorem,lemma,corollary,proposition,definition,proof,remark,example,note,claim,conjecture,axiom}.html` — 12 files, one-block injection each.
- `layouts/partials/essay-references.html` — append partial after `<h2 id="references-heading">`.
- `layouts/partials/streams/cross-refs.html` — append partial after `<h2 id="streams-cross-refs-heading">`.
- `layouts/partials/streams/upcoming.html` — append partial after `<h2 id="streams-upcoming-heading">`.
- `layouts/partials/garden/recent-paths.html` — append partial after `<h2 id="recent-paths-heading">`.
- `layouts/partials/library/umbrella-shelf.html` — append partial after `<h2 id="shelf-…-heading">`.
- `layouts/partials/library/umbrella-catalogue.html` — append partial after `<h2 id="catalogue-heading">`.
- `layouts/partials/cite/static-fallback.html` — append partial after `<h2 id="cite-this-heading">`.
- `layouts/partials/cite/modal.html` — add `data-no-anchor-link` attribute to `<h2 id="cite-modal-title">`.
- `tools/check_smoke.py` — extend the existing smoke test with one assertion against `/essays/example-five/`.
- `.github/workflows/hugo.yaml` — two new named steps (linter + sibling unit-test).
- `tools/ci-local.sh` — two new lines mirroring the CI additions.
- `CLAUDE.md` — append one short paragraph under "Architecture".

**Total:** 6 created, 24 modified.

---

## Task 1 — Shared `anchor-link.html` partial

**Files:**
- Create: `layouts/partials/anchor-link.html`

Adds the canonical markup source. Nothing calls it yet; this task just lands the partial so subsequent tasks can call it without producing an undefined-partial error.

- [ ] **Step 1: Create the partial**

Write the file exactly as specified in spec §3.3:

```go-html-template
{{- /* anchor-link.html — emit the §-glyph deep-link affordance.
       Inputs: .id (required), .title (required, used for aria-label + banner).
       Spec: docs/superpowers/specs/2026-06-07-anchor-affordance-design.md §3.3. */ -}}
{{- $id := .id -}}
{{- $title := .title | default "this section" -}}
<a class="anchor-link" href="#{{ $id }}"
   aria-label="Copy link to {{ $title }}"
   data-anchor-title="{{ $title }}">§</a>
```

- [ ] **Step 2: Verify Hugo build still succeeds**

```bash
hugo --minify
```

Expected: build succeeds; no warnings about the new partial. (The partial is unused so it won't be invoked yet.)

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/anchor-link.html
git commit -m "feat(anchor-link): add shared partial for §-glyph deep-link affordance

Task 1 of Tier 2.1 anchor-affordance plan. Lands the canonical markup
source; no callers yet. See docs/superpowers/plans/2026-06-07-anchor-
affordance.md.
"
```

---

## Task 2 — CSS §48

**Files:**
- Modify: `assets/css/main.css` (append at end-of-file, after the last existing section)

Adds the glyph + banner styles. Since no markup uses `.anchor-link` yet, the CSS is dormant — but landing it now means subsequent UI tasks render the right look on first paint.

- [ ] **Step 1: Append §48 to main.css**

Append exactly this block to `assets/css/main.css`:

```css

/* §48 Anchor-link affordance — deep-link glyph for [id] elements
   Always-visible inline § next to headings, semantic blocks, and chrome
   anchors. Wired by anchor-link.html partial; behavior in anchor-link.js.
   Spec: docs/superpowers/specs/2026-06-07-anchor-affordance-design.md §3.5. */

.anchor-link {
  margin-left: 0.4em;
  color: var(--color-ink-soft);
  font-family: var(--font-ui);
  font-size: 0.85em;
  font-weight: 400;
  text-decoration: none;
  vertical-align: baseline;
  cursor: pointer;
}

.anchor-link:hover,
.anchor-link:focus-visible {
  color: var(--color-burgundy);
}

.anchor-link:focus-visible {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
  border-radius: 2px;
}

/* Banner — singleton, top of viewport. Injected lazily by anchor-link.js. */
#anchor-link-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--color-green);
  color: var(--color-stone);
  font-family: var(--font-ui);
  font-size: 0.85rem;
  text-align: center;
  padding: 0.4rem 1rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
  transition: opacity 180ms ease-in-out;
}

#anchor-link-banner[hidden] {
  /* Override UA `[hidden] { display: none }` so the banner can fade.
     Documented pattern: see CLAUDE.md "filter-chips [hidden] cascade gotcha". */
  display: block;
  opacity: 0;
  pointer-events: none;
}

@media (prefers-reduced-motion: reduce) {
  #anchor-link-banner { transition: none; }
}
```

- [ ] **Step 2: Run contrast checker (sanity — no new token pairings, but the file changed)**

```bash
python3 tools/check-contrast.py
```

Expected: all 9 pairings PASS. The new section reuses existing tokens only; no new pairings introduced.

- [ ] **Step 3: Verify Hugo build still succeeds**

```bash
hugo --minify
```

Expected: build succeeds; CSS is bundled into the new fingerprinted main.<hash>.css.

- [ ] **Step 4: Commit**

```bash
git add assets/css/main.css
git commit -m "feat(anchor-link): add CSS §48 — glyph + banner styles

Task 2 of Tier 2.1 anchor-affordance plan. Token reuse only (no new
contrast pairings). Dormant until partial callers land.
"
```

---

## Task 3 — JS module + entry + scripts.html registration

**Files:**
- Create: `assets/js/anchor-link.js`
- Create: `assets/js/entry-anchor-link.js`
- Modify: `layouts/partials/scripts.html` (one new block, between `core` and `search`)

Lands the click-handler + banner runtime + bundles it on every page. No markup uses `.anchor-link` yet so the listener is dormant.

- [ ] **Step 1: Write the JS module**

Create `assets/js/anchor-link.js` exactly as specified in spec §3.4:

```js
// anchor-link.js — click-to-copy + banner for §-glyph deep-link affordance.
// Spec: docs/superpowers/specs/2026-06-07-anchor-affordance-design.md §3.4.

const BANNER_ID = 'anchor-link-banner';
const BANNER_TIMEOUT_MS = 2200;
let bannerEl = null;
let hideTimer = null;

function ensureBanner() {
  if (bannerEl) return bannerEl;
  bannerEl = document.createElement('div');
  bannerEl.id = BANNER_ID;
  bannerEl.setAttribute('role', 'status');
  bannerEl.setAttribute('aria-live', 'polite');
  bannerEl.hidden = true;
  const span = document.createElement('span');
  span.className = 'banner-text';
  bannerEl.appendChild(span);
  document.body.appendChild(bannerEl);
  return bannerEl;
}

function showBanner(text) {
  const el = ensureBanner();
  el.querySelector('.banner-text').textContent = text;
  el.hidden = false;
  if (hideTimer) clearTimeout(hideTimer);
  hideTimer = setTimeout(() => { el.hidden = true; }, BANNER_TIMEOUT_MS);
}

function handleClick(e) {
  const anchor = e.target.closest('a.anchor-link');
  if (!anchor) return;
  e.preventDefault();
  const absoluteUrl = new URL(anchor.getAttribute('href'), location.href).toString();
  const title = anchor.dataset.anchorTitle || 'this section';
  navigator.clipboard.writeText(absoluteUrl).then(
    () => showBanner(`Link to "${title}" copied`),
    () => {
      location.hash = anchor.getAttribute('href');
      showBanner('Link in address bar — copy from there');
    }
  );
}

function handleEscape(e) {
  if (e.key === 'Escape' && bannerEl && !bannerEl.hidden) {
    bannerEl.hidden = true;
    if (hideTimer) clearTimeout(hideTimer);
  }
}

const main = document.querySelector('main');
if (main) main.addEventListener('click', handleClick);
document.addEventListener('keydown', handleEscape);
```

- [ ] **Step 2: Write the entry stub**

Create `assets/js/entry-anchor-link.js` (mirrors `entry-search.js`):

```js
import './anchor-link.js';
```

- [ ] **Step 3: Register the entry in `scripts.html`**

In `layouts/partials/scripts.html`, after the `search` block (around line 16) and before the first `{{- if eq .Section "essays" }}` block (around line 18), insert this new block:

```go-html-template

{{- /* Anchor-link affordance: §-glyph copy-to-clipboard. Loaded on every
       page because [id] elements exist site-wide. JS self-guards on
       <main> presence; safely no-ops on pages without one. */ -}}
{{- $anchorOpts := dict "targetPath" "js/anchor-link.js" "minify" true -}}
{{- $anchor := resources.Get "js/entry-anchor-link.js" | js.Build $anchorOpts | fingerprint -}}
<script src="{{ $anchor.RelPermalink }}" integrity="{{ $anchor.Data.Integrity }}" defer></script>
```

- [ ] **Step 4: Build + verify the bundle exists**

```bash
hugo --minify
ls -la public/js/anchor-link.*.js
```

Expected: one file matching `anchor-link.<hash>.js`, size < 2 KB.

- [ ] **Step 5: Verify it's referenced on a few pages**

```bash
grep -l 'js/anchor-link\.' public/index.html public/essays/example-five/index.html public/garden/index.html
```

Expected: all three files contain a `<script src="…/js/anchor-link.<hash>.js"` tag.

- [ ] **Step 6: Commit**

```bash
git add assets/js/anchor-link.js assets/js/entry-anchor-link.js layouts/partials/scripts.html
git commit -m "feat(anchor-link): add JS module + entry + site-wide registration

Task 3 of Tier 2.1 anchor-affordance plan. ~1 KB minified bundle on
every page; delegated click listener on <main>; self-no-ops when no
.anchor-link elements exist. Dormant until templates emit the glyph.
"
```

---

## Task 4 — Heading render hook

**Files:**
- Create: `layouts/_default/_markup/render-heading.html`

Single file that turns every Goldmark-rendered heading on every page into a §-bearing element. First task with visible UI impact.

- [ ] **Step 1: Create the render hook directory**

```bash
mkdir -p layouts/_default/_markup
```

- [ ] **Step 2: Write the hook**

Create `layouts/_default/_markup/render-heading.html`:

```go-html-template
{{- /* render-heading.html — Goldmark heading render hook.
       Emits the standard <hN id="…"> element and appends a §-glyph
       anchor-link partial when an ID is present. Covers every essay,
       garden, research, works, library body heading site-wide.
       Spec: docs/superpowers/specs/2026-06-07-anchor-affordance-design.md §3.3. */ -}}
{{- $id := .Anchor -}}
{{- $text := .Text -}}
<h{{ .Level }}{{ with $id }} id="{{ . }}"{{ end }}>
  {{ $text | safeHTML }}
  {{- with $id -}}
    {{ partial "anchor-link.html" (dict "id" . "title" ($text | plainify)) }}
  {{- end -}}
</h{{ .Level }}>
```

- [ ] **Step 3: Build and inspect a rendered page**

```bash
hugo --minify
grep -A1 'class="anchor-link"' public/essays/example-five/index.html | head -10
```

Expected: multiple `<a class="anchor-link" href="#…" aria-label="Copy link to …">§</a>` lines, one per heading in the essay body.

- [ ] **Step 4: Manual check — start the dev server (kill any running first)**

```bash
pkill -f 'hugo server' 2>/dev/null; rm -rf public/  # clean per CLAUDE.md gotcha
hugo server --buildDrafts
```

Open `http://localhost:1313/essays/example-five/` in a browser. Expected: every body heading shows a faint § trailing the text. Click any §; URL bar fragment updates (JS click handler will refine this in later visual tests; for now navigate-and-update is enough since the JS module is loaded).

Stop the server (`Ctrl-C`) before moving on. Clean rebuild:

```bash
rm -rf public/
hugo --minify
```

- [ ] **Step 5: Commit**

```bash
git add layouts/_default/_markup/render-heading.html
git commit -m "feat(anchor-link): heading render hook — §s on every Goldmark heading

Task 4 of Tier 2.1 anchor-affordance plan. Single file covers every
essay/garden/research/works/library body heading. Visible everywhere
.Content is rendered.
"
```

---

## Task 5 — D.1 shortcode injection (12 files)

**Files:**
- Modify: `layouts/shortcodes/theorem.html`
- Modify: `layouts/shortcodes/lemma.html`
- Modify: `layouts/shortcodes/corollary.html`
- Modify: `layouts/shortcodes/proposition.html`
- Modify: `layouts/shortcodes/definition.html`
- Modify: `layouts/shortcodes/proof.html`
- Modify: `layouts/shortcodes/remark.html`
- Modify: `layouts/shortcodes/example.html`
- Modify: `layouts/shortcodes/note.html`
- Modify: `layouts/shortcodes/claim.html`
- Modify: `layouts/shortcodes/conjecture.html`
- Modify: `layouts/shortcodes/axiom.html`

Each gets a block that builds an `$aria` string from kind + counter (+ optional title or `of`) and calls the partial. The injection sits between `</h4>` (block-header close) and `<div class="block-body">`.

- [ ] **Step 1: Update `theorem.html` — the reference template**

Replace the full file contents with:

```go-html-template
{{- /* AMS-style block: theorem.
       Numbering shares counter "theorem-family" with lemma/corollary/proposition.
       Optional title + anchor id are both named args (ox-hugo limitation; see spec §3.2). */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "theorem-family" | default 0)) 1 -}}
{{- $page.Scratch.Set "theorem-family" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-theorem block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Theorem {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Theorem %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Theorem %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 2: Update `lemma.html`**

```go-html-template
{{- /* AMS-style block: lemma. Shares counter "theorem-family". */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "theorem-family" | default 0)) 1 -}}
{{- $page.Scratch.Set "theorem-family" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-lemma block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Lemma {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Lemma %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Lemma %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 3: Update `corollary.html`**

```go-html-template
{{- /* AMS-style block: corollary. Shares counter "theorem-family". */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "theorem-family" | default 0)) 1 -}}
{{- $page.Scratch.Set "theorem-family" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-corollary block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Corollary {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Corollary %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Corollary %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 4: Update `proposition.html`**

```go-html-template
{{- /* AMS-style block: proposition. Shares counter "theorem-family". */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "theorem-family" | default 0)) 1 -}}
{{- $page.Scratch.Set "theorem-family" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-proposition block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Proposition {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Proposition %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Proposition %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 5: Update `definition.html`**

```go-html-template
{{- /* AMS-style block: definition. Own counter; strong tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "definition-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "definition-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-definition block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Definition {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Definition %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Definition %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 6: Update `proof.html`** (different shape — no counter, uses `:of` not `:title`)

```go-html-template
{{- /* AMS-style block: proof. No counter. Optional :of <name> denotes target theorem.
       Auto-appends ∎ tombstone via .proof-tombstone span. */ -}}
{{- $page := .Page -}}
{{- $of := .Get "of" -}}
{{- $id := .Get "id" -}}
<div class="block-proof"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header"><em>Proof{{ with $of }} of <span class="block-title">{{ . }}</span>{{ end }}.</em></h4>
  {{- with $id -}}
    {{- $aria := "Proof" -}}
    {{- with $of -}}{{ $aria = printf "Proof of %s" . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}<span class="proof-tombstone" aria-hidden="true"> ∎</span></div>
</div>
```

- [ ] **Step 7: Update `remark.html`** (soft tier; own counter)

```go-html-template
{{- /* AMS-style block: remark. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "remark-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "remark-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-remark block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Remark {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Remark %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Remark %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 8: Update `example.html`** (soft; own counter)

```go-html-template
{{- /* AMS-style block: example. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "example-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "example-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-example block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Example {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Example %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Example %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 9: Update `note.html`** (soft; own counter)

```go-html-template
{{- /* AMS-style block: note. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "note-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "note-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-note block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Note {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Note %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Note %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 10: Update `claim.html`** (soft; own counter)

```go-html-template
{{- /* AMS-style block: claim. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "claim-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "claim-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-claim block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Claim {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Claim %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Claim %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 11: Update `conjecture.html`** (soft; own counter)

```go-html-template
{{- /* AMS-style block: conjecture. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "conjecture-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "conjecture-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-conjecture block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Conjecture {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Conjecture %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Conjecture %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 12: Update `axiom.html`** (soft; own counter)

```go-html-template
{{- /* AMS-style block: axiom. Own counter; soft tier. */ -}}
{{- $page := .Page -}}
{{- $n := add (int ($page.Scratch.Get "axiom-counter" | default 0)) 1 -}}
{{- $page.Scratch.Set "axiom-counter" $n -}}
{{- $title := .Get "title" -}}
{{- $id := .Get "id" -}}
<div class="block-axiom block-soft"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Axiom {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{- $aria := printf "Axiom %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Axiom %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

- [ ] **Step 13: Build + verify the IVT block now has a §**

```bash
hugo --minify
grep -A1 'id="thm-ivt"' public/essays/example-five/index.html | head -10
```

Expected: the `<div … id="thm-ivt" …>` block contains a `<a class="anchor-link" href="#thm-ivt" aria-label="Copy link to Theorem 2 (Intermediate Value)" data-anchor-title="Theorem 2 (Intermediate Value)">§</a>` somewhere after its `</h4>`.

(Note: the IVT block in `example-five` is the 2nd theorem-family entry because a `definition` precedes it. The aria-label correctly reflects the runtime counter.)

- [ ] **Step 14: Commit**

```bash
git add layouts/shortcodes/theorem.html layouts/shortcodes/lemma.html layouts/shortcodes/corollary.html layouts/shortcodes/proposition.html layouts/shortcodes/definition.html layouts/shortcodes/proof.html layouts/shortcodes/remark.html layouts/shortcodes/example.html layouts/shortcodes/note.html layouts/shortcodes/claim.html layouts/shortcodes/conjecture.html layouts/shortcodes/axiom.html
git commit -m "feat(anchor-link): wire § into all 12 D.1 semantic-block shortcodes

Task 5 of Tier 2.1 anchor-affordance plan. Each shortcode emits the
partial after .block-header when :id is set, with kind+counter (and
optional :title or :of) carried into aria-label + data-anchor-title.
"
```

---

## Task 6 — Chrome partials (7 files)

**Files:**
- Modify: `layouts/partials/essay-references.html`
- Modify: `layouts/partials/streams/cross-refs.html`
- Modify: `layouts/partials/streams/upcoming.html`
- Modify: `layouts/partials/garden/recent-paths.html`
- Modify: `layouts/partials/library/umbrella-shelf.html`
- Modify: `layouts/partials/library/umbrella-catalogue.html`
- Modify: `layouts/partials/cite/static-fallback.html`

Each one-line insertion: after the existing `<h2 id="…">…</h2>` close tag, call the partial with the partial's hard-coded title.

- [ ] **Step 1: `essay-references.html`** — replace the `<h2>` line:

Find:
```go-html-template
      <h2 id="references-heading">References</h2>
```

Replace with:
```go-html-template
      <h2 id="references-heading">References</h2>
      {{ partial "anchor-link.html" (dict "id" "references-heading" "title" "References") }}
```

- [ ] **Step 2: `streams/cross-refs.html`** — find the `<h2 id="streams-cross-refs-heading">` line and append the partial call on the next line:

```go-html-template
  <h2 id="streams-cross-refs-heading">From this stream</h2>
  {{ partial "anchor-link.html" (dict "id" "streams-cross-refs-heading" "title" "From this stream") }}
```

- [ ] **Step 3: `streams/upcoming.html`** — find the `<h2 id="streams-upcoming-heading">` line and append the partial call on the next line:

```go-html-template
  {{- if $heading -}}<h2 id="streams-upcoming-heading">{{ $heading }}</h2>{{- partial "anchor-link.html" (dict "id" "streams-upcoming-heading" "title" $heading) -}}{{- end -}}
```

(Single-line replacement; the `$heading` Hugo variable carries the actual heading text, and we mirror it into `title=` for the aria-label.)

- [ ] **Step 4: `garden/recent-paths.html`** — append after the `<h2>`:

```go-html-template
  <h2 id="recent-paths-heading">Recent paths</h2>
  {{ partial "anchor-link.html" (dict "id" "recent-paths-heading" "title" "Recent paths") }}
```

- [ ] **Step 5: `library/umbrella-shelf.html`** — the shelf-slug is dynamic; mirror it into the partial:

```go-html-template
    <h2 id="shelf-{{ $shelf_slug }}-heading">{{ $title }}</h2>
    {{ partial "anchor-link.html" (dict "id" (printf "shelf-%s-heading" $shelf_slug) "title" $title) }}
```

- [ ] **Step 6: `library/umbrella-catalogue.html`** — append after the `<h2>`:

```go-html-template
  <h2 id="catalogue-heading">Browse the catalogue</h2>
  {{ partial "anchor-link.html" (dict "id" "catalogue-heading" "title" "Browse the catalogue") }}
```

- [ ] **Step 7: `cite/static-fallback.html`** — append after the `<h2>`. The header label is dynamic (variable `$label`):

```go-html-template
  <h2 id="cite-this-heading">{{ $label }}</h2>
  {{ partial "anchor-link.html" (dict "id" "cite-this-heading" "title" $label) }}
```

- [ ] **Step 8: Build + verify**

```bash
hugo --minify
grep -A1 'id="references-heading"' public/essays/*/index.html 2>/dev/null | grep anchor-link | head -3
grep -A1 'id="catalogue-heading"' public/library/index.html | head -3
```

Expected: both surfaces emit the partial call's `<a class="anchor-link" …>§</a>` immediately after the `<h2>`.

- [ ] **Step 9: Commit**

```bash
git add layouts/partials/essay-references.html layouts/partials/streams/cross-refs.html layouts/partials/streams/upcoming.html layouts/partials/garden/recent-paths.html layouts/partials/library/umbrella-shelf.html layouts/partials/library/umbrella-catalogue.html layouts/partials/cite/static-fallback.html
git commit -m "feat(anchor-link): wire § into 7 chrome partials

Task 6 of Tier 2.1 anchor-affordance plan. Hand-templated <h2 id> in
chrome surfaces (References, Recent paths, From this stream, Upcoming,
shelf headings, catalogue, Cite static fallback) now emit the §-glyph
partial.
"
```

---

## Task 7 — Cite-modal opt-out

**Files:**
- Modify: `layouts/partials/cite/modal.html`

The cite modal's `<h2 id="cite-modal-title">` lives inside a `<dialog>`, not the reading flow. It would otherwise show a § that does nothing meaningful (and the linter in Task 8 would also flag it as missing the sibling partial). The `data-no-anchor-link` attribute opts it out cleanly.

- [ ] **Step 1: Add the opt-out attribute**

Find:
```go-html-template
      <h2 id="cite-modal-title">Cite</h2>
```

Replace with:
```go-html-template
      <h2 id="cite-modal-title" data-no-anchor-link>Cite</h2>
```

- [ ] **Step 2: Verify no § renders inside the modal**

```bash
hugo --minify
grep -A1 'id="cite-modal-title"' public/essays/example-five/index.html | head -5
```

Expected: no `<a class="anchor-link">` on the next line.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/cite/modal.html
git commit -m "feat(anchor-link): opt cite modal <h2> out of § affordance

Task 7 of Tier 2.1 anchor-affordance plan. The dialog-scoped modal
header isn't a reading-flow deep-link target; data-no-anchor-link
suppresses the §-glyph and exempts the element from the linter (Task 8).
"
```

---

## Task 8 — Linter pair (27th)

**Files:**
- Create: `tools/check_anchor_link.py`
- Create: `tools/test_check_anchor_link.py`

TDD: write the test fixtures first, watch them fail (linter doesn't exist yet), implement the linter, watch tests pass. Then run the linter against the real `public/` to confirm zero violations.

- [ ] **Step 1: Write the test file** (fixtures + assertions)

Create `tools/test_check_anchor_link.py`:

```python
"""Tests for check_anchor_link.py — run with: python3 -m unittest tools/test_check_anchor_link.py -v"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_anchor_link as lint  # noqa: E402  # pyright: ignore[reportMissingImports]


def page(body_inside_main: str) -> str:
    return (
        "<!doctype html><html><head><title>X</title></head><body>"
        "<header>chrome</header>"
        "<main>" + body_inside_main + "</main>"
        "<footer>chrome</footer>"
        "</body></html>"
    )


GOOD = page(
    '<h2 id="thm-ivt">Section</h2>'
    '<a class="anchor-link" href="#thm-ivt" aria-label="Copy link to Section"'
    ' data-anchor-title="Section">§</a>'
    "<p>body</p>"
)
# Nested form — what the heading render hook (Task 4) actually emits:
# the <a class="anchor-link"> sits INSIDE the <hN>, not after it.
NESTED_GOOD = page(
    '<h2 id="thm-ivt">Section'
    '<a class="anchor-link" href="#thm-ivt" aria-label="Copy link to Section"'
    ' data-anchor-title="Section">§</a></h2>'
    "<p>body</p>"
)
MISSING_ANCHOR = page('<h2 id="orphan">Section</h2><p>body</p>')
WRONG_HREF = page(
    '<h2 id="thm-ivt">Section</h2>'
    '<a class="anchor-link" href="#somewhere-else">§</a>'
    "<p>body</p>"
)
OPT_OUT = page('<h2 id="modal-title" data-no-anchor-link>Cite</h2><p>body</p>')
ID_OUTSIDE_MAIN = (
    "<!doctype html><html><body>"
    "<header><h1 id=\"site-title\">Site</h1></header>"
    "<main><p>no ids here</p></main>"
    "</body></html>"
)
NO_MAIN = "<!doctype html><html><body><h2 id=\"x\">No main wrapper</h2></body></html>"


class TempPublic:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.public = self.root / "public"
        self.public.mkdir()

    def write(self, rel: str, html: str) -> None:
        f = self.public / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html)

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class CheckAnchorLinkTest(unittest.TestCase):
    def setUp(self) -> None:
        self.t = TempPublic()

    def tearDown(self) -> None:
        self.t.cleanup()

    def test_good_passes(self) -> None:
        self.t.write("essays/x/index.html", GOOD)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")
        self.assertEqual(errors, [])

    def test_nested_good_passes(self) -> None:
        # Verifies the render-hook emission form (anchor INSIDE the <hN>).
        self.t.write("essays/x/index.html", NESTED_GOOD)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")
        self.assertEqual(errors, [])

    def test_missing_anchor_fails(self) -> None:
        self.t.write("essays/x/index.html", MISSING_ANCHOR)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 1)
        self.assertTrue(any("orphan" in e for e in errors))

    def test_wrong_href_fails(self) -> None:
        self.t.write("essays/x/index.html", WRONG_HREF)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 1)
        self.assertTrue(any("thm-ivt" in e for e in errors))

    def test_opt_out_is_skipped(self) -> None:
        self.t.write("essays/x/index.html", OPT_OUT)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")

    def test_id_outside_main_is_ignored(self) -> None:
        self.t.write("essays/x/index.html", ID_OUTSIDE_MAIN)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")

    def test_page_with_no_main_is_ignored(self) -> None:
        self.t.write("essays/x/index.html", NO_MAIN)
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0, msg=f"unexpected errors: {errors}")

    def test_empty_public_passes(self) -> None:
        rc, errors = lint.run(self.t.public)
        self.assertEqual(rc, 0)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests; expect failure ("module not found")**

```bash
python3 -m unittest tools/test_check_anchor_link.py -v
```

Expected: `ModuleNotFoundError: No module named 'check_anchor_link'`. Good — TDD requires red first.

- [ ] **Step 3: Write the linter**

Create `tools/check_anchor_link.py`:

```python
#!/usr/bin/env python3
"""Anchor-link affordance linter.

Walks public/**/*.html. For each [id]-bearing element inside <main>
(except those marked data-no-anchor-link), asserts that the immediately-
following sibling element is an <a class="anchor-link"> with the
matching href="#<id>".

Exits 0 on all-pass, 1 on violation. Stdlib only.

Spec: docs/superpowers/specs/2026-06-07-anchor-affordance-design.md §4.1.
"""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path


class _Linter(HTMLParser):
    """Tracks <main> scope and the most-recent [id]-bearing element.

    On every start-tag while inside <main>:
      - If the element has an id (and no data-no-anchor-link) and is NOT
        the anchor-link itself, remember the id as 'pending'. The next
        non-text, non-self-closing start-tag should be the matching
        <a class="anchor-link"> sibling.
      - If we have a 'pending' id and the next start-tag matches an
        anchor-link with the right href, clear the pending; otherwise
        record an error and clear pending (single chance per id).

    We treat the anchor-link as a sibling of the id-bearing element, not
    a child — Hugo's render hook emits it after the heading text but
    INSIDE the <hN>. To handle both cases (sibling and inside-heading),
    the matcher checks the NEXT start-tag regardless of nesting depth.
    """

    def __init__(self, file_path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.file_path = file_path
        self.errors: list[str] = []
        self._main_depth = 0
        self._pending_id: str | None = None
        self._pending_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: v for k, v in attrs}
        if tag == "main":
            self._main_depth += 1
            return
        if self._main_depth <= 0:
            return

        # If we just saw an id and this is its potential follower:
        if self._pending_id is not None:
            cls = (attr_map.get("class") or "").split()
            href = attr_map.get("href") or ""
            if tag == "a" and "anchor-link" in cls and href == f"#{self._pending_id}":
                # Match — clear pending.
                self._pending_id = None
                self._pending_tag = None
            else:
                # First following element is NOT the matching anchor-link.
                self.errors.append(
                    f"{self.file_path}: id='{self._pending_id}' on <{self._pending_tag}> "
                    f"is not immediately followed by <a class='anchor-link' "
                    f"href='#{self._pending_id}'>; got <{tag}> instead"
                )
                self._pending_id = None
                self._pending_tag = None
                # Fall through — this tag itself might have a new id to track.

        # Record a new pending id if this element has one and isn't opted out.
        # Skip the anchor-link itself (its href looks like an id-bearing
        # element if we don't filter it out).
        el_id = attr_map.get("id")
        if el_id is None:
            return
        if "data-no-anchor-link" in attr_map:
            return
        cls = (attr_map.get("class") or "").split()
        if tag == "a" and "anchor-link" in cls:
            return
        self._pending_id = el_id
        self._pending_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if tag == "main" and self._main_depth > 0:
            self._main_depth -= 1


def lint_file(path: Path) -> list[str]:
    html = path.read_text(encoding="utf-8", errors="replace")
    p = _Linter(path)
    try:
        p.feed(html)
    except Exception as e:
        return [f"{path}: HTML parse error: {e}"]
    # Any pending id at EOF means the id-bearing element had no follower at all.
    if p._pending_id is not None:
        p.errors.append(
            f"{path}: id='{p._pending_id}' on <{p._pending_tag}> "
            f"has no following element (anchor-link missing)"
        )
    return p.errors


def run(public: Path) -> tuple[int, list[str]]:
    if not public.is_dir():
        return (0, [])
    all_errors: list[str] = []
    for f in sorted(public.rglob("*.html")):
        all_errors.extend(lint_file(f))
    return (1 if all_errors else 0, all_errors)


def main() -> int:
    public = Path("public")
    if not public.is_dir():
        print(
            "check_anchor_link: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2
    rc, errors = run(public)
    if errors:
        print(f"check_anchor_link: {len(errors)} violation(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("check_anchor_link: OK (every [id] inside <main> has a matching <a class='anchor-link'>).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the unit tests; expect PASS**

```bash
python3 -m unittest tools/test_check_anchor_link.py -v
```

Expected: all 8 tests pass.

- [ ] **Step 5: Run the linter against the real built site**

```bash
hugo --minify
python3 tools/check_anchor_link.py
```

Expected: `check_anchor_link: OK …`. If it fails, walk the first error to find which template missed the partial call; fix in the appropriate task and re-run.

- [ ] **Step 6: Commit**

```bash
git add tools/check_anchor_link.py tools/test_check_anchor_link.py
git commit -m "feat(anchor-link): add 27th linter pair (check_anchor_link)

Task 8 of Tier 2.1 anchor-affordance plan. Walks public/**/*.html and
asserts every [id] inside <main> (except [data-no-anchor-link]) has an
immediately-following <a class='anchor-link' href='#<id>'>. Stdlib only;
8 unit-test cases cover both the sibling form (chrome partials, D.1
shortcodes) and the nested form (heading render hook).
"
```

---

## Task 9 — Smoke-test extension

**Files:**
- Modify: `tools/check_smoke.py`

Adds one assertion to `check_smoke.py`: `/essays/example-five/` must contain at least one `.anchor-link` element. Catches the catastrophic-omission case (e.g., partial silently no-ops) before the full per-element linter runs.

- [ ] **Step 1: Read current `check_smoke.py`** (already done above — it parses each URL's HTML).

- [ ] **Step 2: Extend the parser + per-URL check**

Modify `tools/check_smoke.py` — add an "anchor-link present" assertion for `/essays/example-five/` specifically. Replace the file with:

```python
"""Smoke test for the post-build site.

Asserts that the eight top-level URLs listed in spec §11 each resolve to a
non-empty, parseable HTML file in public/. Runs in CI after `hugo --minify`.
Also asserts that the D.1 kitchen-sink essay (/essays/example-five/) contains
at least one anchor-link element — catches catastrophic regressions of the
Tier 2.1 anchor-affordance pipeline before the full linter runs.

No paired unit-test sibling: the logic is too thin (it's mostly stdlib
HTMLParser + file-exists checks). Documented in spec §3.1.
"""

import sys
from html.parser import HTMLParser
from pathlib import Path


# Spec §11 list.
URLS = [
    "/",
    "/essays/",
    "/garden/",
    "/research/",
    "/works/",
    "/about/",
    "/library/",
    "/credits/",
]

# Tier 2.1 anchor-affordance smoke target.
ANCHOR_LINK_REQUIRED_URLS = ["/essays/example-five/"]


class _Parser(HTMLParser):
    """Tracks whether <html> + <body> were seen and counts .anchor-link tags."""

    def __init__(self) -> None:
        super().__init__()
        self.saw_html = False
        self.saw_body = False
        self.anchor_link_count = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "html":
            self.saw_html = True
        elif tag == "body":
            self.saw_body = True
        elif tag == "a":
            for k, v in attrs:
                if k == "class" and v and "anchor-link" in v.split():
                    self.anchor_link_count += 1
                    break


def file_for_url(public: Path, url: str) -> Path:
    rel = url.strip("/")
    if not rel:
        return public / "index.html"
    return public / rel / "index.html"


def check_url(public: Path, url: str) -> list:
    f = file_for_url(public, url)
    errors = []
    if not f.is_file():
        errors.append(f"{url}: file missing at {f.relative_to(public)}")
        return errors
    if f.stat().st_size == 0:
        errors.append(f"{url}: empty file at {f.relative_to(public)}")
        return errors
    html = f.read_text(encoding="utf-8", errors="replace")
    parser = _Parser()
    try:
        parser.feed(html)
    except Exception as e:
        errors.append(f"{url}: HTML parse error: {e}")
        return errors
    if not parser.saw_html:
        errors.append(f"{url}: no <html> tag")
    if not parser.saw_body:
        errors.append(f"{url}: no <body> tag")
    if url in ANCHOR_LINK_REQUIRED_URLS and parser.anchor_link_count == 0:
        errors.append(
            f"{url}: no <a class='anchor-link'> elements found — "
            "Tier 2.1 anchor-affordance pipeline broken"
        )
    return errors


def main() -> int:
    public = Path("public")
    if not public.is_dir():
        print(
            "check_smoke: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2

    all_errors = []
    for url in URLS + ANCHOR_LINK_REQUIRED_URLS:
        all_errors.extend(check_url(public, url))

    if all_errors:
        print(f"check_smoke: {len(all_errors)} issue(s):", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"check_smoke: OK ({len(URLS) + len(ANCHOR_LINK_REQUIRED_URLS)} URLs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run smoke against the built site**

```bash
hugo --minify
python3 tools/check_smoke.py
```

Expected: `check_smoke: OK (9 URLs)`.

- [ ] **Step 4: Commit**

```bash
git add tools/check_smoke.py
git commit -m "feat(anchor-link): smoke-test extension — anchor-link present on example-five

Task 9 of Tier 2.1 anchor-affordance plan. Catches the catastrophic-
omission case before the full linter runs. Adds /essays/example-five/
to the smoke URL set and asserts >=1 .anchor-link element.
"
```

---

## Task 10 — CI workflow + ci-local wire-up

**Files:**
- Modify: `.github/workflows/hugo.yaml`
- Modify: `tools/ci-local.sh`

Wires the new linter + sibling test into CI. Two new named steps per the project convention (linter on one line, unit-test on the next).

- [ ] **Step 1: Add the workflow steps**

In `.github/workflows/hugo.yaml`, find the existing `check_smoke.py` step (smoke runs AFTER `hugo --minify` since it needs `public/`). Insert two new steps RIGHT AFTER the smoke step, before "Verify LHCI URLs resolve to built pages":

```yaml
      - name: Verify anchor-link affordance present
        run: python3 tools/check_anchor_link.py
      - name: Run anchor-link linter unit tests
        run: python3 -m unittest tools/test_check_anchor_link.py -v
```

(Order: smoke first as a cheap early gate; full linter next; sibling unit-test last.)

- [ ] **Step 2: Mirror in `ci-local.sh`**

In `tools/ci-local.sh`, find the existing `python3 tools/check_smoke.py` line. Add these two lines RIGHT AFTER it:

```bash
python3 tools/check_anchor_link.py
python3 -m unittest tools/test_check_anchor_link.py -v 2>&1 | tail -3
```

- [ ] **Step 3: Run ci-local end-to-end to confirm everything's green**

```bash
bash tools/ci-local.sh
```

Expected: every step passes including the two new ones. (Per [[reference-ci-local-lhci-deps]], the LHCI step may show ±5-8 point mobile-perf variance vs CI; this is documented and not a regression.)

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "ci(anchor-link): wire 27th linter pair into CI + ci-local

Task 10 of Tier 2.1 anchor-affordance plan. Two new named steps after
check_smoke and before LHCI URL resolution. CI named-step count
65 -> 67. ci-local.sh mirrors verbatim.
"
```

---

## Task 11 — CLAUDE.md architecture note

**Files:**
- Modify: `CLAUDE.md`

Adds a short paragraph (~80 words) under "Architecture" describing the affordance + the opt-out hook + the partial as source-of-truth. Future maintainers shouldn't have to dig into the spec to know it exists.

- [ ] **Step 1: Find the right insertion point**

Scan `CLAUDE.md` "Architecture" superhead. Insert a new `### Anchor-link affordance` subsection at the end of the Architecture block, right before the `## Reference docs` superhead.

- [ ] **Step 2: Insert the paragraph**

Add this subsection (use Read then Edit to splice it in; preserves surrounding text):

```markdown
### Anchor-link affordance

Every `id`-bearing element inside `<main>` carries a trailing `§` glyph that
copies the absolute URL to the clipboard on click and surfaces a top-of-
viewport status banner ("Link to *X* copied"). Source of truth is one
partial — `layouts/partials/anchor-link.html` — called by the Goldmark
heading render hook (`layouts/_default/_markup/render-heading.html`), the 12
D.1 semantic-block shortcodes, and 7 chrome partials. Behavior in
`assets/js/anchor-link.js` (~1 KB; site-wide entry; delegated `click`
listener on `<main>`). CSS §48. Per-element opt-out via
`data-no-anchor-link` (applied to the Cite modal `<h2>`). 27th linter pair
(`check_anchor_link.py`) gates the partial-emission invariant.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude.md): add Anchor-link affordance subsection under Architecture

Task 11 of Tier 2.1 anchor-affordance plan. One-paragraph reference so
future maintainers see the affordance + opt-out hook without digging
into the spec.
"
```

---

## Task 12 — Manual spot-check + memory + roadmap mark + final commit

**Files:**
- Modify: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`
- Create: `.claude/memory/project_anchor_affordance_complete.md`

Verifies the slice works end-to-end in a real browser, files the project memory, marks Tier 2.1 ✓ in the roadmap.

- [ ] **Step 1: Start dev server (clean rebuild first)**

```bash
pkill -f 'hugo server' 2>/dev/null
rm -rf public/
hugo server --buildDrafts
```

Server should be at `http://localhost:1313`.

- [ ] **Step 2: Spot-check each surface per spec §4.4**

Walk through these URLs and verify the listed behaviors. Open each in a regular desktop browser at full width, then resize to ~960px (half-screen 1080p) per [[feedback-test-at-half-screen-1080p]].

- `/essays/example-five/`
  - Every body H2/H3 shows a trailing `§`.
  - Each D.1 block (theorem, lemma, …, axiom) with an `:id` (e.g., `thm-ivt`) shows a `§` after its `.block-header`.
  - Click any `§` → top of viewport shows green banner "Link to *<title>* copied" for ~2.2s.
  - Verify clipboard contains the absolute URL (e.g., `http://localhost:1313/essays/example-five/#thm-ivt`).
  - Press Escape during banner → it disappears immediately.
- `/garden/` and any garden note with body headings
  - Body headings show `§`.
  - Click works.
- `/library/reading/`
  - Shelf headings (e.g., "Currently reading", "Recently read") show `§`.
- `/essays/` index page
  - Page H1 (essay-list title) does NOT show a `§` (no `id`).
- Cite modal: open it (click any "Cite" button on the page); verify the modal `<h2 id="cite-modal-title">` does NOT show a `§`.
- Keyboard: Tab through the page; reach a `§`; press Enter; banner appears and clipboard updates.
- JS-disabled (DevTools → Settings → Debugger → Disable JavaScript, then refresh): click a `§`; address bar updates to `#fragment` (no banner; expected per spec §6).

- [ ] **Step 3: Stop the server**

```bash
pkill -f 'hugo server'
rm -rf public/
hugo --minify  # final production build sanity check
```

- [ ] **Step 4: Mark roadmap Tier 2.1 ✓**

In `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`, replace the Tier 2.1 row's `☐` with `✓` and add a shipped-pointer:

Find:
```
| 2.1 | ☐ **Anchor affordance.** D.1 shipped `[id]:hover::after { content: " #"; }` as a placeholder — but pseudo-element content isn't clickable, invisible on touch. → **design brainstormed 2026-06-07**: [`2026-06-07-anchor-affordance-design.md`](2026-06-07-anchor-affordance-design.md). Settled scope = all `id`-bearing elements inside `<main>` (Goldmark auto-IDs + explicit), always-visible `§` glyph, SSR + JS-for-behavior, absolute URL on clipboard, top-of-viewport status banner. Plan + impl pending. | Now (visible regression of intent) | Open the design spec → invoke `superpowers:writing-plans`. Plan should follow the 7-decision table in §2 + the 5 touchpoints in §3.3. |
```

Replace with:
```
| 2.1 | ✓ **Anchor affordance.** Shipped 2026-06-07. Site-wide §-glyph on every `id`-bearing element inside `<main>`; SSR via shared partial + heading render hook + 12 D.1 shortcodes + 7 chrome partials; JS module for click-to-clipboard + top-of-viewport banner; 27th linter pair gates the invariant. → [project-anchor-affordance-complete](../../../.claude/memory/project_anchor_affordance_complete.md) | n/a (shipped) | Spec: [`2026-06-07-anchor-affordance-design.md`](2026-06-07-anchor-affordance-design.md). |
```

- [ ] **Step 5: Write the project memory**

Create `.claude/memory/project_anchor_affordance_complete.md`:

```markdown
---
name: anchor-affordance-complete
description: "Tier 2.1 anchor affordance — shipped 2026-06-07. Site-wide §-glyph deep-link UI on every [id]-bearing element inside <main>. SSR via one shared partial + heading render hook + 12 D.1 shortcodes + 7 chrome partials. JS module (~1 KB) handles click → clipboard → top-of-viewport status banner. CSS §48. 27th linter pair + smoke-test extension. CI 65 → 67 steps."
metadata:
  type: project
---

**Shipped 2026-06-07.** Tier 2.1 of the polish-and-bugfix roadmap per the
brainstormed design spec `docs/superpowers/specs/2026-06-07-anchor-
affordance-design.md`. Plan: `docs/superpowers/plans/2026-06-07-anchor-
affordance.md`.

## What ships

- **Shared partial** `layouts/partials/anchor-link.html` — canonical
  `<a class="anchor-link" href="#…" aria-label="Copy link to …"
  data-anchor-title="…">§</a>` markup. Single source of truth.
- **Heading render hook** `layouts/_default/_markup/render-heading.html` —
  emits the partial after every Goldmark-rendered `<hN id="…">`. Covers
  every essay/garden/research/works/library body heading site-wide.
- **D.1 shortcode injection** in all 12 semantic blocks
  (theorem/lemma/corollary/proposition/definition/proof/remark/example/
  note/claim/conjecture/axiom). Each gates on `:id` being set; aria-label
  derived from kind + counter (+ optional `:title` or `:of`).
- **Chrome partials** — 7 hand edits (`essay-references`,
  `streams/cross-refs`, `streams/upcoming`, `garden/recent-paths`,
  `library/umbrella-shelf`, `library/umbrella-catalogue`,
  `cite/static-fallback`). Each emits the partial after its `<h2 id>`.
- **Cite-modal opt-out** — `data-no-anchor-link` on `<h2 id="cite-modal-title">`
  (dialog-scoped, not reading flow).
- **JS module** `assets/js/anchor-link.js` (~1 KB minified). Single
  delegated `click` listener on `<main>`. clipboard.writeText → banner;
  graceful fallback to `location.hash` on clipboard-API failure.
- **CSS §48** — glyph + banner styles using existing tokens
  (`--color-ink-soft`, `--color-burgundy`, `--color-green`, `--color-stone`).
  No new contrast pairings.
- **27th linter pair** `tools/check_anchor_link.py` +
  `tools/test_check_anchor_link.py`. CI gates the partial-emission
  invariant on every built page.
- **Smoke-test extension** — `tools/check_smoke.py` asserts ≥1
  `.anchor-link` on `/essays/example-five/` (catches catastrophic
  regressions early).
- **CLAUDE.md** — new "Anchor-link affordance" subsection under
  Architecture.

## Numbers

- Site-side only; dotfiles untouched.
- 6 new files, 24 modified.
- ~12 commits on `master` (one per task).
- CI named-step count: 65 → 67.
- Linter pairs: 26 → 27.
- JS bundles loaded per page: gained `anchor-link.<hash>.js` (~1 KB).
- CSS: gained §48 (no new tokens; no new contrast pairings).
- No new ert tests in dotfiles (site-only slice).

## Spot-check verified

Per spec §4.4 manual walkthrough on dev server: D.1 kitchen sink, garden
note headings, library shelf chrome, cite modal opt-out, keyboard
activation, JS-disabled fallback, half-screen 1080p layout. All green.

## Follow-ups (filed elsewhere)

1. **Tile/card stable IDs** → deferred-features registry (no clear
   trigger). Tiles have no `id` today; if author appetite arises to share
   specific tiles within a grid, the registry entry covers the gap.
2. **H4 heading-density tuning** → roadmap Tier 2.4 fast-follow stub.
   One-liner gate in `render-heading.html` if real essays show H4 §s as
   visually noisy.
```

- [ ] **Step 6: Final commit**

```bash
git add docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md .claude/memory/project_anchor_affordance_complete.md
git commit -m "docs(roadmap): Tier 2.1 ✓ anchor affordance shipped

Task 12 of Tier 2.1 anchor-affordance plan — closes the slice. Marks
roadmap row 2.1 ✓ with shipped-pointer to project memory. Manual
spot-check verified all spec §4.4 surfaces: D.1 kitchen sink, garden
headings, library chrome, cite-modal opt-out, keyboard, JS-disabled
fallback, half-screen 1080p.
"
```

- [ ] **Step 7: Final verification**

```bash
git log --oneline -15
git status -s docs/superpowers/specs/ layouts/ assets/ tools/ CLAUDE.md .claude/memory/
```

Expected: 12 new commits in `git log`; no staged or modified files matching the slice's paths in `git status`. Pre-session bystanders in other paths (e.g., `content/essays/example-multi/`, `.claude/memory/project_d2_*.md`) remain unchanged.

---

## Done

Slice is shipped locally on `master`. No push per session policy — author pushes when satisfied. Total: 12 task commits + the design spec commit (`b141327`) from the brainstorm session = 13 commits for the slice end-to-end.

If a future session triggers Tier 2.4 (H4 density tuning), the one-line edit goes in `layouts/_default/_markup/render-heading.html` — wrap the partial call in `{{ if lt .Level 4 }}…{{ end }}`.
