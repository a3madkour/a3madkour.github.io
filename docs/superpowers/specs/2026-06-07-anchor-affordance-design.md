# Anchor affordance — site-wide deep-link UI for [id] elements

**Status:** design (brainstormed 2026-06-07)
**Parent roadmap:** [`2026-06-07-polish-and-bugfix-roadmap.md`](2026-06-07-polish-and-bugfix-roadmap.md) Tier 2.1
**Prior slice memories:** [[d1-complete]] (D.1 semantic blocks shipped 2026-06-01 — placeholder `[id]:hover::after { content: " #"; }` rule lived in CSS §47 briefly and has since been removed), [[anchor-affordance-followup]] (problem framing + queued-brainstorm pointer).

---

## 1 — Goals & non-goals

### Goals

Give readers a real, clickable, touch-and-keyboard-accessible way to **(a) discover** that an on-page element has a stable URL fragment and **(b) grab** the absolute URL in one cheap action. Cover every `id`-bearing element inside the page's main reading flow — Goldmark-auto-IDed headings, author-opted-in `:CUSTOM_ID:` headings, D.1 semantic blocks with `:id`, and chrome headings (References, Recent paths, shelf names, etc.) that sit inside `<main>`.

The shipped artifact is a small site-wide affordance: a `§` glyph trailing every qualifying element, server-rendered by Hugo, with a tiny JS module that upgrades click to clipboard-copy plus a top-of-viewport status banner.

### In scope

- **One shared Hugo partial** — `layouts/partials/anchor-link.html` — emits the canonical `<a class="anchor-link">§</a>` markup. Called by every other touchpoint so there is exactly one source of truth.
- **One heading render hook** — `layouts/_default/_markup/render-heading.html` — collapses every Goldmark-rendered heading on every page into one touchpoint.
- **Per-shortcode injection** in all 12 D.1 semantic-block shortcodes (`theorem` / `lemma` / `corollary` / `proposition` / `definition` / `proof` / `remark` / `example` / `note` / `claim` / `conjecture` / `axiom`) after the `.block-header`, gated on `:id` being set.
- **Per-partial injection** in the 7 chrome partials that emit hand-templated `<h2 id="…">` inside `<main>`: `essay-references.html`, `streams/cross-refs.html`, `streams/upcoming.html`, `garden/recent-paths.html`, `library/umbrella-shelf.html`, `library/umbrella-catalogue.html`, `cite/static-fallback.html`.
- **One JS module** — `assets/js/anchor-link.js` — single delegated `click` listener on `<main>`. On click of `.anchor-link`: prevent default → `navigator.clipboard.writeText(absoluteUrl)` → show banner. Keyboard-accessible for free (native `<a>` Enter activation). New entry `js/entry-anchor-link.js`, registered in `layouts/partials/scripts.html`, loaded site-wide.
- **One CSS section** — `§48 Anchor-link affordance` in `assets/css/main.css` — glyph + banner styles using existing tokens only (no new contrast pairings).
- **One opt-out hook** — `data-no-anchor-link` on an element suppresses the §. Applied to the Cite-modal `<h2 id="cite-modal-title">` (sits inside `<dialog>`, not the reading flow). Reserved for future cases.
- **One new linter pair** — `tools/check_anchor_link.py` + `tools/test_check_anchor_link.py` (27th pair; current count is 26 paired + 2 sibling-less = 28 total `check_*.py` files). Walks `public/**/*.html` under `<main>`, asserts every `[id]` (except `[data-no-anchor-link]`) has an immediately-following `<a class="anchor-link">` sibling.
- **`tools/check_smoke.py` extension** — assert at least one `.anchor-link` exists on `/essays/example-five/` (the D.1 kitchen sink).
- **CLAUDE.md update** — new short paragraph under "Architecture" describing the affordance, the partial, and the opt-out hook.

### Non-goals

- **Tile/card IDs.** Essay cards, garden tiles, works tiles, library catalogue rows, research theme cards, library shelf entries, etc. currently have **no `id` attribute**. The "all elements with `id`" rule passes over them by construction. Adding IDs to tiles is its own design (what value? rendered where? how does it compose with the tile already being a link to its destination page?). Deferred — filed in the deferred-features registry.
- **Heading-level discrimination.** Every `<h2>` / `<h3>` / `<h4>` rendered by Goldmark with an ID gets a §. If §s on H4s turn out to be too dense in real essays, that's a fast-follow tuning step — filed as a Tier 2 fast-follow stub.
- **Banner queueing for rapid clicks.** Design is "reset timer + update text" if a second § is clicked within the 2.2s window. Multi-banner stacking is not warranted by human-pace usage.
- **Server-rendered banner.** Banner is owned and injected by the JS module; a JS-off browser sees zero banner (and degrades to native anchor navigation — see §6).
- **Page-anchor scroll-spy** that rewrites `location.hash` as the reader passes anchored elements. Conceptually adjacent but unrelated UX.
- **Tile/card cite-button-equivalent for IDs.** No "copy link" button surface; only the inline §.
- **Glyph customization per surface.** All anchored elements get the same `§`. No "blocks get §, headings get #" mixed vocabulary.

---

## 2 — Decisions

Each row is a settled trade-off; the brainstorm transcript drove all seven.

| # | Decision | Rationale |
|---|---|---|
| D1 | **Scope = all `id`-bearing elements inside `<main>`**, both auto-generated (Goldmark autoHeadingID) and explicit (`:CUSTOM_ID:`, `:id`). | Maximizes discoverability. Author opt-out via `data-no-anchor-link` is cheap; per-element author opt-in would mean every essay heading needs an explicit ID before the affordance fires, which defeats the discoverability goal. Author prioritized clarity over visual minimalism. |
| D2 | **Progressive enhancement**: real `<a href="#id">` anchor + JS click handler that upgrades to clipboard + banner. | No-JS readers still get a one-click "navigate to fragment → URL bar updates" path. JS-on readers get the one-action grab. Either degradation is functional. |
| D3 | **Always-visible inline `§` glyph** (Q3 option C), placed immediately after the anchored element's heading text / block header. | Hover-only is invisible on touch (the original D.1 problem). Always-visible solves discovery for everyone. `§` reads as a section mark (academic register) rather than `#` (chat / dev register), and matches the site's serif aesthetic better. |
| D4 | **Top-of-viewport status banner** ("Link to *Section one* copied", ~2.2s, viewport-fixed) as copy feedback (Q4 option D). | Author chose clarity over visual subtlety. Banner is the most descriptive of the four feedback options; visible regardless of scroll position; carries the readable title so the reader knows *which* link was copied. |
| D5 | **Absolute URL** form on clipboard (`https://a3madkour.github.io/essays/x/#thm-ivt`). | Pastes correctly into Slack / email / notes / other sites. Matches the clarity-over-aesthetics signal. |
| D6 | **SSR via Hugo + JS for behavior only.** Glyph emitted by templates / render hook / shared partial; JS module handles click-to-copy + banner. | No FOUC (glyph present in first paint). View-source legibility. Crawlers / RSS readers see the markup. JS module is tiny because it doesn't have to inject DOM, only respond to clicks. |
| D7 | **One shared `anchor-link.html` partial** consumed by render hook + 12 shortcodes + 7 chrome partials. | One source of truth for the markup. Future tweaks (rename class, swap glyph, change `aria-label` format) land in one file. |

---

## 3 — Architecture

### 3.1 DOM contract

The shared partial emits exactly this markup for every qualifying element:

```html
<a class="anchor-link" href="#thm-ivt"
   aria-label="Copy link to Intermediate Value"
   data-anchor-title="Intermediate Value">§</a>
```

Three deliberate properties:

1. **Real `<a href="#fragment">`.** No-JS click follows the anchor; browser updates address bar with the fragment.
2. **`aria-label` is human-readable** — built from the readable title of the parent element. Avoids the unhelpful screen-reader announcement "anchor link section-dash-one".
3. **`data-anchor-title` carries the same readable title** for the JS banner. Kept separate from `aria-label` so the visible banner can be richer than the screen-reader announcement if we ever want to diverge.

### 3.2 Title derivation by surface

| Surface | Readable title used in `aria-label` + `data-anchor-title` |
|---|---|
| Heading (`<h2>`–`<h6>`) | The heading's plain text (`.Text \| plainify`). |
| D.1 strong/soft block with `:title` set | `"<Kind> <N> (<Title>)"` — e.g., `"Theorem 1 (Intermediate Value)"`. |
| D.1 strong/soft block without `:title` | `"<Kind> <N>"` — e.g., `"Lemma 3"`. |
| D.1 proof with `:of` set | `"Proof of <Of>"` — e.g., `"Proof of Intermediate Value"`. |
| D.1 proof without `:of` | `"Proof"`. |
| Chrome partial | Hard-coded per partial — `"References"`, `"Recent paths"`, `"Cite"`, `"From this stream"`, `"Upcoming"`, `"Browse the catalogue"`, `"<Shelf-Title>"`. |
| Fallback (no title derivable) | The literal string `"this section"`. |

### 3.3 Hugo touchpoints

**Shared partial** — `layouts/partials/anchor-link.html`:

```go-html-template
{{- /* anchor-link.html — emit the §-glyph deep-link affordance.
       Inputs: .id (required), .title (required, used for aria-label + banner). */ -}}
{{- $id := .id -}}
{{- $title := .title | default "this section" -}}
<a class="anchor-link" href="#{{ $id }}"
   aria-label="Copy link to {{ $title }}"
   data-anchor-title="{{ $title }}">§</a>
```

**Heading render hook** — `layouts/_default/_markup/render-heading.html`:

```go-html-template
{{- $id := .Anchor -}}
{{- $text := .Text -}}
<h{{ .Level }}{{ with $id }} id="{{ . }}"{{ end }}>
  {{ $text | safeHTML }}
  {{- with $id -}}
    {{ partial "anchor-link.html" (dict "id" . "title" ($text | plainify)) }}
  {{- end -}}
</h{{ .Level }}>
```

Single file covers every essay/garden/research/works/library body heading.

**D.1 shortcode injection** — 12 files, one-liner each. Each shortcode currently builds a `$blockTitle` string (already implied by the existing `Kind N (Title)` rendering in `.block-header`); we just call the partial after the header:

```go-html-template
<div class="block-theorem block-strong"{{ with $id }} id="{{ . }}"{{ end }}>
  <h4 class="block-header">
    Theorem {{ $n }}{{ with $title }} (<span class="block-title">{{ . }}</span>){{ end }}.
  </h4>
  {{- with $id -}}
    {{ $aria := printf "Theorem %d" $n -}}
    {{- with $title -}}{{ $aria = printf "Theorem %d (%s)" $n . -}}{{- end -}}
    {{ partial "anchor-link.html" (dict "id" $id "title" $aria) }}
  {{- end -}}
  <div class="block-body">{{ .Inner | markdownify }}</div>
</div>
```

Same pattern repeats across all 12 shortcodes with the kind name and counter variable swapped.

**Chrome partials** — 7 hand edits, one line each. After each `<h2 id="…">…</h2>` close-tag, append the partial call with the partial's hard-coded title.

**Cite-modal opt-out** — `layouts/partials/cite/modal.html` adds `data-no-anchor-link` to the `<h2 id="cite-modal-title">` element so the linter skips it and the render-hook gate naturally excludes it (it isn't in `<main>` either, but explicit is better here).

### 3.4 JS module

`assets/js/anchor-link.js` (~50 LoC, no dependencies):

```js
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

Loaded on every page via a new entry `assets/js/entry-anchor-link.js` registered in `scripts.html` alongside `core`. Bundle size ~1 KB minified.

### 3.5 CSS

New section in `assets/css/main.css` (next available number is **§48**):

```css
/* §48 Anchor-link affordance — deep-link glyph for [id] elements
   Always-visible inline § next to headings, semantic blocks, and chrome
   anchors. Wired by anchor-link.html partial; behavior in anchor-link.js. */

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

/* Banner — singleton, top of viewport */
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
  /* Override UA `[hidden] { display: none }` so the banner can fade. */
  display: block;
  opacity: 0;
  pointer-events: none;
}

@media (prefers-reduced-motion: reduce) {
  #anchor-link-banner { transition: none; }
}
```

**Token reuse, no new contrast pairings**:
- `--color-ink-soft` for idle glyph → same as `.block-title`, stub anchors. AAA against stone (already verified by §1 contrast checker).
- `--color-burgundy` for hover/focus → same as `.essay-card:hover` border, `.site-brand:hover`. AA verified.
- `--color-green` + `--color-stone` for banner → already in the 9 pairings checked by `tools/check-contrast.py` (garden stage-glyph "evergreen" stop). AA verified.

**`[hidden]` override caveat** matches the existing pattern documented in CLAUDE.md's filter-chips "`[hidden]` cascade gotcha" note: when JS toggles the `hidden` attribute for animation, the UA rule `[hidden] { display: none }` blocks any transition. The fix is to override `display` and rely on `opacity: 0` + `pointer-events: none` for the visually-hidden state.

---

## 4 — Testing

### 4.1 New site linter pair (27th)

- **`tools/check_anchor_link.py`** — given `public/`, walks every `*.html`, parses with `html.parser`, narrows to elements inside `<main>`. For each element with an `id` attribute and *without* `data-no-anchor-link`, asserts the immediately-following sibling element is an `<a class="anchor-link">` with `href="#<the-id>"`. Reports missing pairings with file path + element + id.
- **`tools/test_check_anchor_link.py`** — fixtures covering: (a) present-and-correct, (b) missing `<a>`, (c) wrong href, (d) opt-out via `data-no-anchor-link`, (e) ID outside `<main>` (ignored), (f) nested-`<main>` edge case (extremely unlikely but parser-defensive). Same structure as the other 26 linter pairs.
- CI step count: **65 → 67** (linter + sibling test).

### 4.2 Smoke extension

`tools/check_smoke.py` gains one assertion: at least one `.anchor-link` element exists on `/essays/example-five/index.html`. Cheap; catches the catastrophic-omission case before the full linter runs.

### 4.3 No new ert tests in dotfiles

This slice is site-side only. The org-publish pipeline already emits `id` attributes (D.1's `:id`, B.1.1's `:CUSTOM_ID:` round-trip). Nothing in elisp-land changes.

### 4.4 Manual dev-server spot-check

Per [[feedback-verify-before-merge]]:

- `/essays/example-five/` — D.1 kitchen sink; verify § on every block kind + every body H2/H3.
- `/garden/example-map/` — topic-map garden note; verify § on body headings.
- `/library/reading/` — chrome shelf headings; verify § on `<h2 id="shelf-*-heading">`.
- `/essays/` index page — verify chrome heading on `essay-references.html`-emitting page or equivalent.
- Half-screen 1080p (~960px) per [[feedback-test-at-half-screen-1080p]] — verify glyph placement at narrow widths doesn't break heading wrapping.
- Keyboard: Tab to §, Enter; verify banner appears + URL on clipboard.
- Touch (mobile emulator or real device): tap §; verify banner appears.
- JS-disabled: open browser with JS off, click §; verify URL fragment lands in address bar (no banner, but functional).
- Cite modal: open `<dialog>`; verify the modal `<h2>` does *not* render a §.

---

## 5 — Rollout

- **Single commit chain on `master`.** No feature flag. The change is additive — new partial, new render hook, new shortcode/partial calls, new JS module, new CSS section, new linter pair. Existing surface (CSS, JS, templates) is unchanged except for the 7 chrome partials gaining one line each and the 12 D.1 shortcodes gaining one-liner block.
- **Cite-modal `data-no-anchor-link` lands in the same commit** as the linter, so the first CI run doesn't fail on the modal `<h2>`.
- **Roadmap update.** Mark Tier 2.1 ✓ when shipped, with a link to the `project_anchor_affordance_complete.md` memory file.
- **No CLAUDE.md "Architecture" rewrite.** A short paragraph addition (one section, ~80 words) under the existing "Architecture" superhead describes the partial and the `data-no-anchor-link` opt-out hook. Does not warrant its own subsection.

---

## 6 — No-JS degradation

Explicit graceful-degradation story (the JS module is the only piece that becomes inert):

| With JS | Without JS |
|---|---|
| Click § → clipboard receives absolute URL → top banner says "Link to *X* copied" for 2.2s. | Click § → browser follows the anchor → URL bar updates to `#fragment` → reader copies from address bar. |
| Banner dismissible via Escape. | No banner; nothing to dismiss. |
| Keyboard activation (Enter on focused §) triggers same flow. | Keyboard activation triggers native anchor follow. |

Both paths are functional. The JS-on path is more convenient; the JS-off path is the same path the reader would use without any affordance at all, with the bonus that the § makes the addressability discoverable.

---

## 7 — Open questions

None. All seven brainstorm decisions are settled in §2. Glyph balance and heading-density tuning are explicit fast-follow stubs in the roadmap, not open spec questions.

---

## 8 — Deferred follow-ups (filed elsewhere; not part of this slice)

These were surfaced during the 2026-06-07 brainstorm and intentionally not folded into v1. Their canonical homes:

1. **Tile/card IDs + deep-link affordance.** Tiles (essay-card, garden-tile, works-tile, library catalogue rows, research theme cards, library shelf entries) currently have no `id` attribute and so naturally fall outside this slice's "all elements with `id`" rule. Adding IDs requires its own design (what ID? rendered where? composition with the tile-as-link?). **Filed in:** `2026-06-07-deferred-features-registry.md` under "Authoring / metadata extensions". No clear trigger.
2. **Heading-level tuning — skip H4 if §s feel too dense.** If real essays show §s on H4s as visually noisy, a one-line render-hook gate skips them. **Filed in:** `2026-06-07-polish-and-bugfix-roadmap.md` Tier 2 as a fast-follow stub. Trigger: first essay author finds H4 §s noisy.
