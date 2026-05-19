# TOC collapsible subsections — design

**Status:** DESIGNED. Brainstorm complete; ready for `superpowers:writing-plans`.

**Filed:** 2026-05-14 (stub) · **Brainstormed:** 2026-05-18

**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` — independent essay-polish slice (not in the §14 phase list; queued in CLAUDE.md's "Designed but not yet implemented" table).

## Motivation

The essay TOC lists every heading h2–h6 flat (Hugo `markup.tableOfContents` `startLevel: 2`, `endLevel: 6`). On a long essay this is noisy. Sub-headings are useful while you're reading that section and clutter when you're elsewhere. The scrollspy already tracks the active heading (`assets/js/nav.js`, "last heading whose top crossed the 10% trigger line"). The TOC should reuse that signal to keep only the active top-level section's subtree visible and collapse the rest.

## Resolved decisions (from brainstorm)

1. **Top-level section = the outermost `#TableOfContents > ul > li`**, level-agnostic. Whatever heading level Hugo emits at the first tier (h2 normally, h3 if an essay leads with h3) is a "section." No hardcoded level.
2. **The active section expands its full subtree** — every descendant level (h3, h4, h5…), not just one level down. Inactive sections show only their top entry.
3. **Manual chevrons, scrollspy wins on next scroll.** Each section with a subtree gets a disclosure toggle. Clicking it is an additive "peek" (does not collapse the active section). The next scroll event re-asserts scrollspy: exactly the active section expanded, every other section collapsed, all manual "peek" flags cleared.
4. **Manual toggles animate; scrollspy-driven collapse is instant.** Manual open/close uses the `grid-template-rows: 0fr ↔ 1fr` CSS trick. Scrollspy-driven state changes are applied without transition (no scroll-jank). `prefers-reduced-motion: reduce` → instant for everyone.

## Approach (selected: A — client-side enhancement in `nav.js`)

Hugo's TOC rendering is unchanged. The TOC scrollspy block already in `nav.js` early-returns unless `#TableOfContents a[href^="#"]` exists, so all collapse work is a no-op off-essay. Rejected alternatives: **B** (server-rendered nested `<details>`) — large rewrite, makes no-JS = collapsed which contradicts the progressive-enhancement floor, scrollspy fights `<details open>` on every scroll; **C** (CSS-only disclosure + JS active class) — "expand the active section" is inherently scroll-derived so it can't be CSS-only; degrades to plain manual disclosures with no scrollspy tie-in when JS is off (B's downsides without its upside).

### Server side (unchanged)

`layouts/partials/essay-toc.html` still emits `{{ .TableOfContents }}` inside `<details open><summary>Contents</summary>`. No template rewrite. JS off → full flat tree, every link reachable. This is the progressive-enhancement floor and is mandated, not optional.

### One-time DOM transform (`DOMContentLoaded`, after scrollspy maps its sections)

- Walk `#TableOfContents > ul > li` — the level-agnostic sections.
- For each section `<li>` containing a nested `<ul>` (has a subtree):
  - Give the nested `<ul>` an id (`toc-sub-<n>`), wrap it in `<div class="toc-disclosure">` (the grid-rows animation container).
  - Inject `<button type="button" class="toc-toggle" aria-expanded="false" aria-controls="toc-sub-<n>">` as the first child of the `<li>`, before the anchor.
  - Add class `toc-section` to the `<li>`; start collapsed (`aria-expanded="false"`, container `grid-template-rows: 0fr`, `inert` on the disclosure).
- Section `<li>`s with no subtree get no button and no class — nothing to toggle.

### State model

Each `toc-section` carries a JS-tracked `peeked` flag (default `false`). Two drivers:

1. **Scrollspy driver (instant)** — inside the *existing* `updateActive()` scroll/resize handler, after `activeHref` is computed: find the top-level section containing the anchor whose `href === activeHref` (walk that anchor up to its `#TableOfContents > ul > li`). Set that section expanded; set every other section collapsed; clear all `peeked` flags. The disclosure transition is suppressed for this frame (`.is-instant`). This is the "scrollspy wins on next scroll" rule.
2. **Manual driver (animated)** — clicking a `.toc-toggle` flips that one section's `aria-expanded` + `inert`, sets `peeked = true`, and animates via the grid-rows transition. It does *not* collapse the active section (additive peek). The next scroll event's scrollspy driver wipes `peeked` and re-collapses everything but the active section.

**Initial render:** the existing `nav.js` TOC scrollspy calls `updateActive()` once at setup end (`nav.js:38`). The folded-in scrollspy driver therefore runs on load, so the correct section (the one matching `scrollY` at load — normally the first section) is expanded immediately, instantly (`.is-instant`), with no flash of the full tree beyond the brief pre-JS server state.

### Smooth-scroll coexistence

`assets/js/essay.js setupTocSmoothScroll()` binds clicks on `.essay-toc a` (anchors). The chevron is a `<button>`, not an anchor — the two handlers never collide (deliberate, per the duplicate-id/anchor-race lesson: click-driven actions use `<button type="button">`, not anchors). Clicking a collapsed section's anchor still smooth-scrolls there; the scrollspy driver expands it on arrival.

## CSS

A new block extending the existing `.essay-toc` rules near `assets/css/main.css:655–691`. No new numbered `§` header — it lives in the existing essay-TOC region (same precedent as the un-numbered §32–§36 works additions).

```css
.toc-toggle {
  /* bare button: chevron glyph, no border/background, inherits TOC font;
     rotates on [aria-expanded="true"] */
}
.toc-disclosure {
  display: grid;
  grid-template-rows: 0fr;
  overflow: hidden;
  transition: grid-template-rows 180ms ease;
}
.toc-disclosure > ul { min-height: 0; }            /* required for 0fr clip */
.toc-section[aria-expanded-section] .toc-disclosure { grid-template-rows: 1fr; }
.toc-disclosure.is-instant { transition: none; }   /* scrollspy-driven frame */
@media (prefers-reduced-motion: reduce) {
  .toc-disclosure { transition: none; }
}
```

(The exact "expanded" selector — attribute on the `<li>` vs a class — is an implementation nicety for the plan; the behavior is fixed.)

- **Animation mechanic:** `grid-template-rows: 0fr → 1fr` — no JS height measurement, no `max-height` magic number. Manual toggles transition; the scrollspy driver adds `.is-instant` for that frame so scroll-driven collapse never animates. `prefers-reduced-motion` removes the transition globally.
- **Chevron glyph:** a CSS border-triangle (zero new assets, rotates on `[aria-expanded="true"]`). No AI-drawn SVG path; if an SVG is preferred it must come from the documented Lucide icon canon. Final glyph choice confirmed at implementation.
- `#TableOfContents .is-active` (burgundy / weight 600, `main.css:306`) is untouched — highlight and collapse are orthogonal.

## Accessibility

- Toggle is a real `<button type="button">` with `aria-expanded` (state) and `aria-controls` (the wrapped `<ul>` id) — standard disclosure pattern, Enter/Space for free.
- Collapsed subtree must leave the tab order and a11y tree **but stay animatable**, so `hidden`/`display:none` are unusable (they kill the grid-rows transition). Use **`inert`** on `.toc-disclosure` when collapsed: not focusable, removed from the a11y tree, still rendered/animatable. Remove `inert` on expand, set it on collapse. (`inert` is applied deliberately here — the persistent-graph-access review caught an `inert` a11y regression; this design front-loads it.)
- The `[hidden]` cascade gotcha does not apply (no `hidden` attribute used; collapse is `inert` + grid-rows). No `[hidden]{display:none}` rule needed.
- No-JS: no buttons, no `inert`, full tree visible and reachable; nothing removed server-side, so search/index is unaffected.
- Keyboard reach to an inactive section's subsection: Tab to that section's anchor (a normal link) → activate → smooth-scroll → scrollspy expands on arrival; or Tab to its chevron → Space to peek. Nothing is permanently unreachable.

## Fixture

`content/essays/example-deep-toc-essay/index.md` — a **new** fixture (not a mutation of an existing one; mutating `example-essay-one`'s heading tree would perturb slices that rely on its shape, and a dedicated deep-TOC fixture is self-documenting).

- Frontmatter: full essay contract (`check_fixtures.py` `REQUIRED_FIELDS`), `toc: true`, `series: ""`, all `has_*: false`, `draft: false`, not featured.
- Body: obviously-dummy filler (lorem ipsum / "Example section N" — never authored prose), structured **h2 › h3 › h4** with ≥3 top-level h2 sections, one nesting h3s, one of those h3s nesting h4s. Enough to exercise: level-agnostic top-level, full-subtree expand, multiple sections collapsing, manual peek.
- No new `has_*` flag — TOC depth is structural, not a frontmatter feature; the frontmatter contract and `check_fixtures.py` are unchanged.

## Linter / CI gate

New sibling pair `tools/check_toc_depth.py` + `tools/test_check_toc_depth.py` (per CLAUDE.md linter-pair discipline; the logic — parse `content/essays/*/index.md`, count distinct ATX heading levels — is thick enough to warrant a paired test, unlike sibling-less `check_smoke.py`).

- Assertion: **at least one non-draft essay fixture reaches ≥3 distinct heading levels.** A future edit that flattens the fixture fails CI instead of silently killing the only thing exercising this feature.
- Wiring: `.github/workflows/hugo.yaml` as the 20th linter pair (2 new CI steps); `tools/ci-local.sh`; CLAUDE.md linter inventory + CI step count updated.

This is a thin guard and an explicit judgment call — included because it is cheap, matches project discipline, and prevents silent regression. (Reversible: if the user prefers, drop the linter and rely on the fixture + manual QA; the rest of the design is unaffected.)

## Scope / non-goals

- **Essay TOC only.** `layouts/partials/page-sidebar.html` (about / home / research-theme / research-question / library leaves) is a flat, intentionally-shallow anchor list — not a `.TableOfContents` tree. Out of scope. No chrome/scope contradiction: the feature is cleanly bounded to `.essay-toc`.
- **No server-side collapse state.** Pure progressive enhancement; no-JS = full tree.
- No change to scrollspy highlight behavior, smooth-scroll, or the Hugo TOC config.

## Bundle placement

The collapse code lives in `nav.js` (core bundle, every page) with the existing TOC scrollspy, not in the essay entry. Rationale: the active-anchor computation is already there; splitting it across two bundles would mean two scroll listeners racing to drive collapse. The incremental code is small and behind the existing `#TableOfContents` early-return guard — a ~sub-KB every-page cost is outweighed by a single race-free source of truth. (Noted as a deliberate tradeoff, not an oversight.)

## Testing / verification

- `test_check_toc_depth.py`: pass/fail cases for the depth assertion.
- Full `tools/ci-local.sh` before any push (one command, mirrors CI step-for-step).
- Dev-server spot-check on the new fixture at desktop **and ~960px half-screen**. Note the fixed left rail engages only ≥1100px; below that the TOC is the inline `<details>` — the collapse behavior applies in both layouts. Eyeball checklist: scroll-driven expand/collapse, manual chevron peek + scroll re-asserts, `prefers-reduced-motion` (instant), keyboard (Tab/Space on chevron, Enter on link), no-JS full tree.

## Done criteria

1. `example-deep-toc-essay` exists, renders, has ≥3 distinct heading levels.
2. On it: only the active top-level section's subtree visible; others show their top entry only; scrollspy updates continuously while scrolling.
3. Manual chevron peeks an inactive section; the next scroll re-collapses it.
4. Manual toggle animates; scrollspy-driven collapse and `prefers-reduced-motion` are instant.
5. No keyboard navigation regression; no-JS shows the full reachable tree.
6. `check_toc_depth.py` + `test_check_toc_depth.py` green; full local CI green.
