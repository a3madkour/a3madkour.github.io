# TOC collapsible subsections — stub spec

**Status:** STUB. Brainstorm pending. File via `superpowers:brainstorming` when scheduled.

**Date:** 2026-05-14

## Motivation

The essay TOC currently lists every heading (h2–h6) flat. On a long essay this is noisy. Sub-headings (h3 nested under an h2 section) are useful when you're reading that section but clutter when you're elsewhere on the page.

The scrollspy already tracks the currently-active heading (fixed in the library-redesign slice via the "last heading whose top crossed the 10% trigger line" algorithm in `assets/js/nav.js`). The TOC should use that signal to **collapse subsections that don't belong to the active top-level section**, and **expand subsections under the active top-level section**.

## Open questions for the brainstorm

- **Definition of "top-level section":** h2 only? Or whatever the highest heading the essay actually uses (some essays might lead with h3)?
- **Reveal mechanic:** instant show/hide vs. animated collapse (CSS `details` + `height` transition)? Respect `prefers-reduced-motion`.
- **Multi-level nesting:** essays can go h2 > h3 > h4. Do we expand the *full* subtree under an active h2, or only one level (h3) and require manual expand for h4+?
- **Manual override:** if the reader manually expands a different section's subtree (clicks a chevron, hovers, etc.), does the scrollspy stop auto-collapsing, or always win?
- **Fixture:** none of the current essay fixtures have a deep TOC (≥3 levels). The brainstorm should commission a fixture (essay 4 or 5) with a 3+ level heading tree to make the behavior visible and testable.
- **a11y:** make sure collapsed subsections are reachable by keyboard (Tab into the parent expands? `aria-expanded` state on the parent? sub-list `hidden` vs CSS `display: none`?). Don't trap focus or hide content from search/index.
- **Scope creep:** does this also apply to the page-sidebar (`partials/page-sidebar.html` — used on about/home/research-theme/research-question/library leaves)? That uses a flat anchor list. Probably out of scope for v1 — sidebar entries are intentionally shallow.

## What already exists

- `nav.js` lines 5–43 — TOC scrollspy. Already exposes the active heading id via `.is-active` on `#TableOfContents a`. The collapse logic can hang off this same machinery.
- `essay.js` `setupTocSmoothScroll()` — smooth-scroll on TOC click. Don't break it when adding collapse behavior.
- Hugo `.TableOfContents` emits a nested `<ul>` tree. The CSS hook is each anchor's `href` matches a heading id.

## Out of scope

- Anything beyond the essay TOC. Library / garden / research / works do not use `.TableOfContents`.
- Server-side rendering of collapse state — pure progressive enhancement (works without JS by showing the full tree).

## Done criteria (provisional — to be confirmed in brainstorm)

- A new essay fixture with ≥3 heading levels exists and renders.
- On that fixture, only the active section's subsection list is visible; other sections show their h2 entry only.
- Scrollspy still updates the active entry continuously as you scroll.
- No keyboard nav regression.
- Linter (`tools/check_essay_fixtures.py` or a new sibling) — TBD whether anything new needs gating.
