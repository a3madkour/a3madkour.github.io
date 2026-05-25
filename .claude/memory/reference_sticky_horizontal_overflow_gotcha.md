---
name: reference-sticky-horizontal-overflow-gotcha
description: "When position:sticky behaves like static (DOM API says pinned, user sees it scroll away), check documentElement horizontal overflow first — Firefox sticky paint math fails when html.scrollWidth > clientWidth"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 171c2d70-e589-4228-8a7e-9479c381df35
---

When `position: sticky` appears to fail (element scrolls with content despite `getBoundingClientRect().y` reporting `0`), Firefox's sticky paint math breaks if `document.documentElement.scrollWidth > clientWidth`. The layout engine still computes `y=0`, but the paint is drawn against the wider scroll context and scrolls out of view with the page.

**Diagnostic** (one-liner — run BEFORE pursuing compositor / display:contents / containing-block hypotheses):

```js
console.log('overflow?=' + (document.documentElement.scrollWidth > document.documentElement.clientWidth), 'docW=' + document.documentElement.scrollWidth, 'clientW=' + document.documentElement.clientWidth);
```

**Important caveats discovered on this project:**

- The bug is viewport-width-scoped. At wide enough viewports the over-wide element fits and sticky works. The first investigation session at the wrong viewport saw `getBoundingClientRect().y = 0` and assumed sticky was working — it was, just only at that width. Always probe at the viewport where the user reports the bug, not a convenient wider one.
- The over-wide culprit was the site header's `<nav>` (display:flex with no flex-wrap, ran past the viewport at narrow widths). Common culprits in general: nav links + icon buttons not wrapping, long unbreakable strings, fixed-width images, code blocks without `overflow-x: auto`.
- **Use `overflow-x: clip` on `html` (NOT `overflow-x: hidden`) as a defensive backstop.** `hidden` creates a scroll container which breaks `position: sticky` for descendants. `clip` does not. Both prevent horizontal overflow visually.
- `body { overflow-x: clip }` does NOT propagate to `html` reliably in Firefox; apply to `html` directly.

**Fixed on this project 2026-05-13** in commit `bab359d`. See `docs/superpowers/specs/2026-05-13-mobile-page-sidebar-strip-bug-design.md` for the full write-up.

Related: [[project-phase-8-slice-3-final-qa]], [[project-page-sidebar-slice]].
