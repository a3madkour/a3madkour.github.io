# Mobile page-sidebar strip pin bug — investigation stub

**Phase:** Post-Phase-8 polish slice (standalone). Not blocking Phase 8 close.
**Parent spec:** `docs/superpowers/specs/2026-05-13-page-sidebar-design.md` (page-sidebar slice).
**Filed:** 2026-05-13, during Phase 8 Slice 3 QA walkthrough. Multiple attempted fixes in-session failed to resolve.

---

## Symptom

On viewports below the rail→strip flip point (≤ 1219 px CSS width), the homepage's mobile dots strip **scrolls away with page content instead of staying pinned at the top of the viewport.**

- Reproduces on real mobile devices (user confirmed it on phone with an earlier build).
- Reproduces on a narrow desktop window at ~525×599 (and other widths < 1220).
- Reproduces independently of Firefox Responsive Design Mode — happens with a real resized window.

## What the diagnostic ruled out

Run in the homepage's DevTools console while at the affected breakpoint, after various fixes:

1. **`getComputedStyle(aside).position` = `"fixed"`** when we set `position: fixed` (and `"sticky"` when we set `position: sticky`).
2. **`aside.offsetParent` = `null`** with `position: fixed` — spec-compliant for true viewport pinning.
3. **No ancestor has `transform`, `filter`, `backdrop-filter`, `perspective`, `contain`, or `will-change`** that would create a containing block for fixed positioning. We walked the ancestor chain explicitly.
4. **`getBoundingClientRect()` reports `y = 0` at every scroll position** (programmatic AND manual scrolls) — measured from scrollY=0 through scrollY=3802px, height ~38px, always at top of viewport.
5. **`document.elementsFromPoint(10, 10)` at scrollY=500 returns the strip as the TOP-MOST painted element**: `["NAV.page-sidebar--strip", "ASIDE.page-sidebar", "DIV.page", "BODY", "HTML"]`. Nothing is covering it.
6. **Computed style at the same scroll**: `opacity=1, visibility=visible, display=block, clip-path=none, transform=none`.
7. **A reduced reproduction** (`public/test-fixed.html` — a minimal page with a tomato bar `position: fixed; top: 0; left: 0; right: 0` and the same nested `<main>` structure) **WORKS CORRECTLY** — the bar stays pinned. So `position: fixed` works in the user's browser in isolation.

In short: every DOM-side and JS-side measurement says the strip IS pinned at viewport top throughout scrolling. The browser's own paint-stack API confirms the strip is the top-most painted element. **And yet** the user observes the strip vanishing from the screen entirely as soon as they scroll.

## What the diagnostic does NOT yet explain

The disconnect between the DOM/paint API readings and the actual rendered output. Hypotheses to investigate:

- **Compositing-layer bug**: Firefox (and Chromium's Skia path) sometimes drop or misplace fixed-positioned elements during accelerated scroll on certain layouts. Worth checking with `about:config` `layers.acceleration.disabled = true` (Firefox) and seeing if the bug persists.
- **Stacking context interaction we haven't found**: the diagnostic walked ancestors looking for containing-block-creating properties, but there may be a subtler interaction (e.g., a `position: relative` ancestor + a sibling that creates a stacking context, somehow displacing paint).
- **Nested `<main>` artifact**: the homepage has `<main data-pagefind-body>` from `baseof.html` wrapping `<main class="home">` from `home.html`. Two `<main>` elements is also an HTML validation defect (only one allowed per document). The reduced reproduction had the same nesting and worked — but it didn't have the full layout stack underneath.
- **An interaction with `min-height: 100dvh`** on `body` + `.page` and Firefox mobile's viewport-resize-on-scroll behaviour. `dvh` units are dynamic; their value changes when the URL bar hides/shows on mobile. Could `position: fixed` get re-anchored when `dvh` changes mid-scroll?
- **The site has nested scrollable contexts we haven't audited.** Could be `<main>` itself has overflow that creates a scroller in some browser path.

## What needs to happen in the dive-deeper slice

1. **Set up a clean repro environment**: a fresh checkout, no editor lock, no DevTools modifications. Trace one specific page from cold cache.
2. **Compare paint-on-screen vs DOM-on-paper.** Take a screen recording at the affected breakpoint. Confirm what's actually visible — different from what `getBoundingClientRect()` reports? Then there's a compositor/render-tree divergence.
3. **Bisect the layout stack**: starting from `public/test-fixed.html` (works) and incrementally adding the homepage's CSS + DOM, find the exact addition that breaks pinning. Suspect candidates to test in order:
   - Add the full `main.css` stylesheet.
   - Add `<main data-pagefind-body>` wrapping.
   - Add the `<div class="page">` flex column.
   - Add the homepage's hero + currently + research strip + garden strip + studio strip — one at a time.
4. **Test on multiple browsers and devices**: Firefox Linux, Firefox Android, Chromium Linux, Chromium Android, Safari iOS. The bug should be reproducible on any of them if it's a real layout defect.
5. **Once the breaking layer is identified, propose a structural fix** — likely a markup restructure (eliminate the nested `<main>`, move the page-sidebar outside `<main>` to be a direct child of `<body>` or `.page`, etc.) rather than another CSS tweak.

## Files relevant to the investigation

- CSS: `assets/css/main.css` §41 (page sidebar).
- Partial: `layouts/partials/page-sidebar.html`.
- Each layout that calls the partial: `layouts/home.html`, `layouts/about/single.html`, `layouts/research-theme/single.html`, `layouts/research-question/single.html`, the four `layouts/library-*/list.html`.
- Baseof: `layouts/_default/baseof.html` (where the outer `<main>` lives).
- Scrollspy + click handler: `assets/js/nav.js` (only manipulates `.is-active` class; doesn't touch positioning).
- The minimal repro that worked: replicate from in-session probe `public/test-fixed.html`.

## Failed attempts (don't repeat these — they were investigated and ruled out)

- `position: sticky` on the strip with `display: contents` on the aside → strip scrolls away
- `position: sticky` on the aside directly → same
- `position: fixed; top: 0; left: 0; right: 0` on the aside → DOM says pinned, user reports invisible
- Adding `!important` to the above → no change
- Different z-index values (5, 9999) → no change

## Pointers for whoever picks this up

- Memory: `feedback_test_at_half_screen_1080p.md` — half-screen 1080p (≈ 960 px wide) is the user's daily test viewport. At 960px the rail is the active rendering, NOT the strip; so the dots-strip bug only surfaces below the flip point (1220 px).
- Memory: `project_page_sidebar_slice.md` — Phase 7 polish that originally shipped this code (commit `10f64a5`).
- Session where this surfaced: Phase 8 Slice 3 QA walkthrough. Multiple back-and-forth fixes in the session got increasingly desperate and never resolved the actual rendering bug; controller's working context became polluted. Start fresh.

---

*End of stub. Brainstorm + plan when ready to dive in with a clean head.*
