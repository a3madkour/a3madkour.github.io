---
name: project-page-sidebar-slice
description: Page sidebar slice merged 2026-05-13 — cross-template rotated-labels rail with scrollspy; also refactored homepage Research section
metadata: 
  node_type: memory
  type: project
  originSessionId: d27b9186-f371-40e9-ac80-f9b1a00cfcff
---

Page sidebar slice — Phase 7 polish — merged 2026-05-13 (merge `10f64a5`, pushed to origin).

Shared `layouts/partials/page-sidebar.html` takes a `(id, label)` slice and emits a desktop rotated-labels rail (`writing-mode: vertical-rl` + `transform: rotate(180deg)`) on the left margin AND a sticky horizontal dots strip for narrower viewports. Breakpoint flips rail→strip at **1220px** (not 800px) because the rail at `left: 1.25rem` collides with the content column (`max-width: 1080px`) on anything narrower. Integrated across 5 layout families: home / about / research themes / research questions / four library leaves. Each layout owns its anchor list with conditional filtering for sections that may not render. Suppressed entirely when `<2` anchors.

JS scrollspy in `assets/js/nav.js`:
- Active = last section whose top has crossed `scrollY + viewportHeight*0.1` (top 10% trigger line). NOT IntersectionObserver — explicit bookkeeping handles tall sections that "span the band" cleanly.
- Footer-bottom fallback: when `scrollY + viewportHeight >= docHeight - 2`, force the LAST sidebar link active. Without this, a short last section can't get highlighted because its top never reaches the trigger before the page bottoms out.
- Toggle by `href` not element identity: the partial emits both rail anchors AND strip anchors with matching `href`s, so the toggle flips both simultaneously and whichever DOM is visible at the current breakpoint inherits the highlight.

**Why these specific choices:**
- **IntersectionObserver tried first** — abandoned because "any section intersecting the band" picks the wrong section when a long earlier section still spans the band while a short later section sits below. Scrollspy with explicit "last section whose top has crossed" is cleaner.
- **Breakpoint at 1220px** — content max-width (1080px) + ~70px rail safe-zone per side = 1220px. Below that, the rail's labels overlap headline characters.
- **Bottom-to-top book-spine direction was the original spec** — user reversed to top-to-bottom (column order matches DOM order) after seeing it live. Both directions ship via the `transform: rotate(180deg)` + `flex-direction` knobs in CSS.
- **Font-size is fluid `clamp(0.9rem, 0.7rem + 0.35vw, 1.2rem)`** because the user noted fixed sizes felt small at desktop. Tracking letter-spacing eased from 0.18em to 0.14em because wide tracking only earns its keep at tiny sizes.

**Homepage layout refactored as part of this slice:**
- Research + Garden are now in ONE 2-col `<section id="research" class="home-research-section">` (research questions left, top-10 garden tiles right) under one sidebar anchor "Research". Each side keeps its own visible sub-heading ("What I'm chasing" / "From the Garden").
- Studio renamed "Works", standalone full-width section after Research with its own `padding: 3rem 0 2.5rem`.
- Research strip bumped from 2 → 3 active questions; garden strip from 6 → 10 tiles; tile size scoping loosened. Section padding 3rem → 4rem to give breathing room without going empty.

**Caveats for next session:**
- The `<aside class="page-sidebar">` uses `display: contents` at the mobile breakpoint to dissolve the aside box so the strip's sticky containing block is `<main>` (full doc height). Sticky doesn't work otherwise — the strip's natural parent would be the aside itself, which has zero scroll travel. Some older screen readers may not announce `<aside>` regions when `display: contents` is set; current behavior accepts the tradeoff.
- The dev-server visual spot-check task surfaced ~10 polish commits beyond the original 6-task plan. That's normal for visual-design slices; expect similar iteration on future ones.
- Scrollspy is on a `scroll` listener (passive). On pages with hundreds of sections this would be slow; current pages have ≤8 anchors so it's fine.

Related: [[project-homepage-v3-slice]] (the Phase 7 Slice 2 that this polish slice extends).
