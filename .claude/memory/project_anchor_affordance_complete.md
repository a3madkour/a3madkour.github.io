---
name: anchor-affordance-complete
description: "Tier 2.1 anchor affordance — shipped 2026-06-07. Site-wide §-glyph deep-link UI on every [id]-bearing reading-flow element inside <main> (headings + D.1 block-class elements). SSR via one shared partial + heading render hook + 12 D.1 shortcodes + 7 chrome partials. JS module (~1 KB) handles click → clipboard → top-of-viewport status banner. CSS §48. 27th linter pair (narrowed to reading-flow targets) + smoke-test extension. CI 65 → 67 steps."
metadata:
  type: project
---

**Shipped 2026-06-07.** Tier 2.1 of the polish-and-bugfix roadmap per the brainstormed design spec `docs/superpowers/specs/2026-06-07-anchor-affordance-design.md` and plan `docs/superpowers/plans/2026-06-07-anchor-affordance.md`. Subagent-driven, 12 tasks.

## What ships

- **Shared partial** `layouts/partials/anchor-link.html` — canonical `<a class="anchor-link" href="#…" aria-label="Copy link to …" data-anchor-title="…">§</a>` markup. Single source of truth.
- **Heading render hook** `layouts/_default/_markup/render-heading.html` — emits the partial after every Goldmark-rendered `<hN id="…">`. Covers every essay/garden/research/works/library body heading site-wide.
- **D.1 shortcode injection** in all 12 semantic blocks (theorem/lemma/corollary/proposition/definition/proof/remark/example/note/claim/conjecture/axiom). Each gates on `:id` being set; aria-label derived from kind + counter (+ optional `:title` or `:of`).
- **Chrome partials** — 7 hand edits (`essay-references`, `streams/cross-refs`, `streams/upcoming`, `garden/recent-paths`, `library/umbrella-shelf`, `library/umbrella-catalogue`, `cite/static-fallback`). Each emits the partial after its `<h2 id>`.
- **Cite-modal opt-out** — `data-no-anchor-link` on `<h2 id="cite-modal-title">` (dialog-scoped, not reading flow).
- **JS module** `assets/js/anchor-link.js` (~1 KB minified). Single delegated `click` listener on `<main>`. `clipboard.writeText` → banner; graceful fallback to `location.hash` on clipboard-API failure. Escape skipped when a `<dialog>` is open so the cite modal's native cancel wins (added during code review).
- **CSS §48** — glyph + banner styles using existing tokens (`--color-ink-soft`, `--color-burgundy`, `--color-green`, `--color-stone`). No new contrast pairings.
- **27th linter pair** `tools/check_anchor_link.py` + `tools/test_check_anchor_link.py`. Narrowed scope after task 8 discovered structural-id false-positives (SVG `<symbol>`, graph-data `<script>`, sidenote `<aside>`, footnote `<sup>`/`<li>`, TOC `<nav>`, graph-panel `<aside>`). Linter now only enforces on headings `<h1>`-`<h6>` + elements with a `block-` class token. 11 unit tests cover sibling-form, nested-form (heading hook), block-container-form (D.1 shortcodes), structural ignored, and opt-out.
- **Smoke-test extension** — `tools/check_smoke.py` asserts ≥1 `.anchor-link` on `/essays/example-five/`.
- **CLAUDE.md** — new "Anchor-link affordance" subsection under Architecture.

## Numbers

- Site-side only; dotfiles untouched.
- 6 new files, 24 modified.
- 14 commits on `master` (12 plan tasks + 2 in-task fix commits: Escape `<dialog>` guard + linter scope narrowing).
- CI named-step count: 65 → 67.
- Linter pairs: 26 → 27.
- JS bundles loaded per page: gained `anchor-link.<hash>.js` (~1 KB).
- CSS: gained §48 (no new tokens; no new contrast pairings).
- No new ert tests in dotfiles (site-only slice).

## In-slice fix-ups (caught by code review)

1. **Task 3 — Escape handler `<dialog>` guard.** Original `handleEscape` would dismiss the banner even when a `<dialog>` was open, conflicting with the cite modal's native Escape cancel. Added `if (document.querySelector('dialog[open]')) return;` early-return. (Commit `dc2a1c5`.)
2. **Task 8 — linter scope narrowing.** Original linter treated every `[id]` inside `<main>` as a reading-flow target, spuriously flagging 257 structural elements (SVG sprite `<symbol>`, graph-data `<script>`, sidenote `<aside>`, footnote `<sup>`/`<li>`, TOC `<nav>`, graph-panel `<aside>`, reference-list `<li>`). Spec §1 defines reading-flow targets as exactly headings + elements with `block-*` class. Added `_is_reading_flow_target` predicate and 3 new unit-test cases (8 → 11). (Commit `09aca21`.)

## Spot-check (subagent-automated stand-in)

Build + presence checks confirm §s emitted on:
- `/essays/example-five/` — D.1 kitchen sink headings/blocks, ≥1 anchor-link
- `/garden/` — section index headings, ≥1 anchor-link
- `/library/` — umbrella catalogue + shelf headings, ≥2 anchor-links
- Smoke + linter + 11 unit tests all green.

**Manual dev-server walkthrough still pending** for the parts a subagent can't verify: keyboard Tab-to-§-then-Enter behavior, half-screen-1080p layout, JS-disabled URL-bar fallback. Surfaced as a follow-up below.

## Follow-ups (filed elsewhere)

1. **Tile/card stable IDs** → deferred-features registry (no clear trigger). Filed during brainstorm.
2. **H4 heading-density tuning** → roadmap Tier 2.4 fast-follow stub. Filed during brainstorm.
3. **Manual dev-server spot-check** — owner to do at next human session (per spec §4.4): keyboard Tab/Enter, touch tap, JS-disabled fragment-update, half-screen 1080px breakpoint, cite-modal `<h2>` should NOT show a §.
