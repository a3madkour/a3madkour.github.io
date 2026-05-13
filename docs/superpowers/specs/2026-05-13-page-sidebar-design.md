# Page sidebar — design

**Phase:** 7 polish (extends Homepage v3, generalizes the pattern to four other long-scroll templates).
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §14.

A vertical, rotated-label rail in the left margin showing the page's section list. Active section is the one whose top edge has crossed the upper third of the viewport. Labels are clickable and smooth-scroll to their anchor. On narrow viewports the rail is replaced by a sticky horizontal dots strip just below the top nav.

The rail appears on **every multi-section page template** (≥2 sections): homepage, About, research themes, research questions, library leaves. Essay posts keep their existing `.essay-toc` partial — this rail does not replace it.

---

## 1. Architecture

### File layout

```
layouts/partials/
  page-sidebar.html              # new — shared, takes `sections` arg, emits both DOMs

layouts/
  home.html                      # modify — add id="…" to 5 section wrappers + call partial
  about/single.html              # modify — same
  research-theme/single.html     # modify — same
  research-question/single.html  # modify — same
  library-reading/list.html      # modify — same
  library-listening/list.html    # modify — same
  library-playing/list.html      # modify — same
  library-watching/list.html     # modify — same

assets/css/main.css              # append §41 page-sidebar (rail + strip + responsive)
assets/js/nav.js                 # extend — IntersectionObserver + click handler for `.page-sidebar`
```

### Partial signature

Mirrors `filter-chips.html` (the existing shared-partial-with-arg precedent):

```hugo
{{ partial "page-sidebar.html" (dict "sections" (slice
    (dict "id" "currently"      "label" "Currently")
    (dict "id" "essays"         "label" "Essays")
    (dict "id" "research-strip" "label" "Chasing")
    (dict "id" "garden-strip"   "label" "Garden")
    (dict "id" "studio-strip"   "label" "Studio")
  )) }}
```

### DOM output (per call)

```html
<aside class="page-sidebar" aria-label="Page sections">
  <nav class="page-sidebar--rail">
    <a href="#currently"      class="page-sidebar-label">Currently</a>
    <a href="#essays"         class="page-sidebar-label">Essays</a>
    <a href="#research-strip" class="page-sidebar-label">Chasing</a>
    <a href="#garden-strip"   class="page-sidebar-label">Garden</a>
    <a href="#studio-strip"   class="page-sidebar-label">Studio</a>
  </nav>
  <nav class="page-sidebar--strip">
    <a href="#currently"      class="page-sidebar-dot" aria-label="Currently"></a>
    <a href="#essays"         class="page-sidebar-dot" aria-label="Essays"></a>
    <a href="#research-strip" class="page-sidebar-dot" aria-label="Chasing"></a>
    <a href="#garden-strip"   class="page-sidebar-dot" aria-label="Garden"></a>
    <a href="#studio-strip"   class="page-sidebar-dot" aria-label="Studio"></a>
  </nav>
</aside>
```

CSS hides one nav per breakpoint. JS observer updates `.is-active` on whichever anchors share the active section's `href`.

### Section list source

Per-template hardcoded. Each layout assembles a `sections` slice immediately before its partial call. Pages with **conditional sections** (e.g., research theme without `garden_topic_ref`, library leaf with empty queue) filter the slice before passing it. If the assembled slice has **<2 entries** the partial emits nothing — matches the existing `filter-chips.html` ≥2-distinct-value suppression rule.

### Anchor strategy

- All wrapper elements use kebab-case `id` attributes unique within the page.
- The only structural change to existing templates is adding `id="…"` to wrapper `<section>` elements that already exist (or to top-level wrapper elements where none currently exists).
- No new partials introduced beyond `page-sidebar.html`.

### JS extension (`assets/js/nav.js`)

Added to the existing file, alongside the existing TOC-observer. Activated only when `.page-sidebar a[href^="#"]` exists on the page:

```js
const sidebarLinks = document.querySelectorAll('.page-sidebar a[href^="#"]');
if (sidebarLinks.length > 0) {
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
      const target = document.querySelector(a.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' });
      history.pushState(null, '', a.getAttribute('href'));
    });
  });
}
```

The rootMargin `-30% 0px -60% 0px` makes a section "active" once its top edge crosses the upper third of the viewport.

---

## 2. Visual treatment

### Desktop rail (`.page-sidebar--rail`)

- `position: fixed; top: 50%; left: 1rem; transform: translateY(-50%);` — vertically centered to the viewport. Stays mid-screen regardless of scroll position. Main content centers via `max-width: 1080px`, leaving the rail in the natural left margin without collision.
- `display: flex; flex-direction: column-reverse; gap: 1.5rem;` — `column-reverse` so the first section's label sits at the bottom of the stack, matching bottom-to-top book-spine reading order.
- Per-label (`.page-sidebar-label`):
  - `writing-mode: vertical-rl; transform: rotate(180deg);` — book-spine direction.
  - `font-family: var(--font-ui); font-size: 0.6rem; letter-spacing: 0.18em; text-transform: uppercase; line-height: 1;`.
  - Default `color: var(--color-ink-soft);`.
  - `:hover` → `color: var(--color-burgundy);` plus underline.
  - `.is-active` → `color: var(--color-burgundy); font-weight: 600;`. No underline — color and weight together signal active.
  - Anchor element; `text-decoration: none;`.

### Mobile dots strip (`.page-sidebar--strip`)

- `position: sticky; top: 0; left: 0; right: 0; z-index: 5;`. The site header is not sticky; it scrolls off, and the strip then pins flush to the viewport top.
- Horizontal flex, centered: `display: flex; justify-content: center; gap: 0.85rem; padding: 0.5rem 0;`.
- `background: var(--color-stone); border-bottom: 1px solid var(--color-rule);`.
- Per-dot (`.page-sidebar-dot`):
  - `width: 6px; height: 6px; border-radius: 50%;`.
  - Default `background: var(--color-rule);`.
  - `.is-active` → `background: var(--color-burgundy); width: 8px; height: 8px;`.
  - Anchor wrapper provides ≥36×36px tap target via `padding: 0.4rem;`.
  - `aria-label` carries the section name for screen readers.

### Active state model

The IntersectionObserver fires whenever a watched section enters the rootMargin band. The handler reassigns `.is-active` to the matching anchor in both rail and strip. If two sections briefly co-exist in the band during scroll, the later entry wins. Color flip is instantaneous — no transition.

### What it does NOT include

- No pulse / fade animations.
- No tooltip on rail hover (label already legible).
- No animated "moving rule" marker following the active label.
- No tooltip on mobile dot hover (sighted mobile users have position; screen readers have `aria-label`).

---

## 3. Per-template integration

Five layouts get the rail. Each owns its anchor list.

### 3.1 Homepage (`layouts/home.html`)

| anchor | label | source |
|---|---|---|
| `currently` | Currently | `partials/home/currently.html` wrapper gets `id` |
| `essays` | Essays | inline `<section class="home-essays">` in `home.html` gets `id` |
| `research-strip` | Chasing | `partials/home/research-strip.html` wrapper |
| `garden-strip` | Garden | inline `<section class="home-two-col">` in `home.html` — but the Garden anchor goes on the inner `partials/home/garden-strip.html` wrapper |
| `studio-strip` | Studio | `partials/home/studio-strip.html` wrapper |

Hero is the top of the page; it is not in the rail.

### 3.2 About (`layouts/about/single.html`)

| anchor | label |
|---|---|
| `bio` | Bio |
| `now` | Now |
| `where` | Where |
| `connect` | Connect |
| `colophon` | Colophon |

Each `<section class="about-…">` block gains a matching `id`.

### 3.3 Research theme (`layouts/research-theme/single.html`)

| anchor | label | conditional? |
|---|---|---|
| `framing` | Framing | always |
| `questions` | Questions | always |
| `outputs` | Outputs | always |
| `garden-topic` | Topic | only when `garden_topic_ref` is set |

The layout filters the `Topic` entry out of the slice when the theme has no `garden_topic_ref`.

### 3.4 Research question (`layouts/research-question/single.html`)

| anchor | label |
|---|---|
| `thinking` | Thinking |
| `sub` | Sub-Qs |
| `siblings` | Siblings |
| `notes` | Notes |
| `essays` | Essays |
| `outputs` | Outputs |
| `backlinks` | Links |

The longest list (7 labels). Single-word abbreviations keep the rail visually balanced.

### 3.5 Library leaves (`layouts/library-{reading,listening,playing,watching}/list.html`)

Partly data-driven. The base anchor set is:

| anchor | label | conditional? |
|---|---|---|
| `currently-active` | Now | when ≥1 active item exists |
| `<year>` | `<year>` (e.g., `2026`) | one per year section in the data |
| `upnext` | Next | when the queue (`status: queued`) is non-empty |

The layout builds the `sections` slice from the partitioned items before calling `page-sidebar.html`. Year labels render as the literal year string ("2026", "2025", …) — short enough for vertical text.

### Anchor uniqueness

- All anchors are kebab-case and unique within a page.
- The library leaf uses bare year strings as `id`s (`id="2026"`). Hugo + HTML5 accept numeric-leading ids; tested by build.

---

## 4. Accessibility

- Outer `<aside aria-label="Page sections">` declares the region.
- Each anchor is a real `<a href="#…">`. Keyboard users `Tab` through the rail labels (DOM order: top of `<main>`, before content) and press `Enter` to jump.
- Mobile dots carry `aria-label="<section name>"` for screen readers.
- `:focus-visible` shows a 1px burgundy outline on both rail labels and strip dots.
- `prefers-reduced-motion` flips smooth scroll to `behavior: 'auto'`.
- Active state uses color **and** weight (rail) / color **and** size (strip) — meets WCAG 1.4.1 ("use of color").
- Contrast: `--color-ink-soft on --color-stone` and `--color-burgundy on --color-stone` are both already gated at AA by `tools/check-contrast.py`. No new tokens.

---

## 5. Verification

No new linter pair. The anchor list is template-owned; if a layout emits a typo, the rail link 404s on the same page — a runtime visual check catches it.

Existing gates that re-run:
- `tools/check-contrast.py` — passes unchanged (no new tokens).
- 12 linter pairs — pass unchanged (no fixture or data shape changes).
- `hugo --minify` — fails CI if any template explodes.

Dev-server visual spot-check (mandatory per session rule):
- Rail renders on each of 5 page templates (`/`, `/about/`, `/research/themes/<slug>/`, `/research/questions/<slug>/`, `/library/{reading,listening,playing,watching}/`).
- Click each rail label — page scrolls smoothly to the matching section.
- Active state updates correctly as the page scrolls.
- Mobile (≤800px) on each: rail hides, dots strip appears sticky under the header.
- Dark mode: rail + strip both legible.
- Reduced-motion mode (DevTools): click → instant jump, no smooth scroll.
- Conditional sections (research theme without garden_topic_ref, library leaf with no queue) — verify the corresponding rail entry is absent.

---

## 6. Out of scope (deferred)

| Capability | Why |
|---|---|
| Animated active-state transition (slide / fade) | §27 motion budget — color flip only |
| Tooltip on rail label hover | Label is legible — tooltip duplicative |
| Per-essay use of this rail | Essays have their own `.essay-toc` partial |
| Linter for anchor ↔ section-id consistency | Build-time runtime resolves it; broken anchors visible immediately |
| Custom-icon labels (vs text) per template | Text labels suffice for v1 |
| Pulse dot on the active section | Static color flip — restrained per existing audio-pill / Currently-pulse posture |

---

## 7. Commit shape

Single slice branch `slice/page-sidebar`. Four logical commits:

1. **shared partial + nav.js extension** — `page-sidebar.html`, add the IntersectionObserver + click handler to `nav.js`. Site builds; no template uses the partial yet.
2. **homepage integration** — homepage section wrappers gain `id`s + the call to `page-sidebar.html`. Visible on `/`.
3. **other four templates** — About + research theme + research question + four library leaves gain `id`s + partial calls.
4. **css §41** — desktop rail + mobile strip + responsive breakpoint + focus state.

If any commit fails CI, the next commit is the fix — never amend.

---

## 8. Risk inventory

- **Section list drift**. If a template adds or removes a section without updating its `sections` slice, the rail goes silently out of sync. Mitigation: cluster the slice declaration in the same template/partial as the section markup. A short inline comment (`<!-- page-sidebar sections list defined below — keep in sync -->`) flags it.
- **Sticky/fixed positioning collisions**. `position: fixed; top: 50%; transform: translateY(-50%)` keeps the rail mid-viewport regardless of scroll. No collision with main content (left margin is empty on this site at every breakpoint above 800px).
- **Mobile sticky strip interfering with scroll-into-view**. When a sidebar anchor scrolls to a section, the sticky strip would normally overlap the section header. Mitigation: `scroll-margin-top: 2.5rem;` on the wrapper `<section>` elements pushes the scroll target below the ~24px sticky strip. The CSS rule is added inside the existing `@media (max-width: 800px)` block since the strip is only visible on mobile; on desktop the fixed rail doesn't sit at the top of the viewport and doesn't need a scroll offset.
- **IntersectionObserver browser support**. Universally supported in target browsers; Phase 8 Lighthouse / Pagefind work runs the canonical audit.

---

*End of spec.*
