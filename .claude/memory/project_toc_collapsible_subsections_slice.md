---
name: project-toc-collapsible-subsections-slice
description: TOC collapsible subsections slice — shipped 2026-05-18; scrollspy-driven essay-TOC collapse + check_toc_depth linter (20th)
metadata: 
  node_type: memory
  type: project
  originSessionId: ab1b4ba4-4d0d-4c3a-80de-4f92efacc860
---

TOC collapsible subsections slice — independent essay-polish slice, executed via subagent-driven-development on branch `feature/toc-collapsible-subsections`.

**Spec:** `docs/superpowers/specs/2026-05-14-toc-collapsible-subsections-design.md` (stub replaced with the resolved design). **Plan:** `docs/superpowers/plans/2026-05-18-toc-collapsible-subsections.md`.

**Four locked design decisions:** (1) top-level section = the outermost `#TableOfContents > ul > li`, level-agnostic; (2) the active section expands its FULL subtree (all descendant levels); (3) manual chevrons — clicking is an additive "peek" that does not collapse the active section, and the next scroll re-asserts scrollspy (exactly the active section expanded, all others collapsed); (4) manual toggles animate via the `grid-template-rows: 0fr↔1fr` trick, scrollspy-driven collapse is instant (`.is-instant` + forced reflow), `prefers-reduced-motion` handled globally by the §8 universal rule (no local `@media` block — deliberate, documented inline).

**Approach A** — client-side enhancement folded into the existing TOC scrollspy in `assets/js/nav.js` (every-page core bundle; early-returns when no `#TableOfContents`). Hugo's `.TableOfContents` HTML unchanged → no-JS shows the full tree (progressive-enhancement floor). JS injects `<button class="toc-toggle" aria-expanded aria-controls aria-label>`, wraps each section's child `<ul>` in `<div class="toc-disclosure" id="toc-sub-N">`, `inert` on collapsed disclosures for a11y.

**Files:** new `content/essays/example-deep-toc-essay/index.md` (h2›h3›h4 dummy fixture, only essay exercising collapse); new linter pair `tools/check_toc_depth.py` + `tools/test_check_toc_depth.py` (20th pair — asserts ≥1 non-draft essay has ≥3 distinct heading levels; strips fenced code; drafts/empty vacuously pass); CI wiring (`.github/workflows/hugo.yaml` +2 named steps after the essay pair → 36 pre-build steps / 53 total; `tools/ci-local.sh`); CSS in `assets/css/main.css` (`.toc-toggle` border-triangle chevron, `.toc-disclosure`, no new numbered §); comment-only fix to the stale `layouts/partials/essay-toc.html` top comment; `CLAUDE.md` registration.

**Review-loop catches** (subagent two-stage review): Task 2 — two linter tests asserted only on `rc` not `errors` (added `assertTrue(any("3 distinct heading levels" ...))` for sibling-pattern parity); Task 3 — CI step name broke the `Run <subject> linter unit tests` convention (renamed to `Run essay TOC depth linter unit tests`); Task 4 — local `@media (prefers-reduced-motion)` block was redundant with global §8 (`*,*::before,*::after { transition-duration: 0.01ms !important }`), removed; Task 5 — dead write-only `peeked` field removed (behavior produced by `applyActive`'s `m === activeMeta` + click handler not touching the active section, independent of the field), stale `essay-toc.html` IntersectionObserver comment corrected; Task 6 — leftover double blank line from the deleted queue-table row.

**Spot-check (human gate) findings, fixed before merge:** (1) scrollspy skipped "Section two" — fixture too short, the pre-existing `atBottom` rule forced the last section; fixed by deepening the dummy content so each top-level section is individually dwellable (`bed878b`); (2) clicking a TOC link churned the highlight/collapse through every intervening section during `essay.js`'s smooth-scroll; fixed by a `scrollLock` in nav.js — on anchor click, snap state to the clicked target and freeze `updateActive` until `scrollend` / 1s backstop / user `wheel`|`touchmove` (`b10f5a4`). Also note an earlier final-review catch: spec decision 3's "manual click must not collapse the active section" was unenforced → added the active-section guard (`ad17282`).

**Merged + pushed:** to `master` 2026-05-18 as `--no-ff` merge commit `2bb9220` (11 slice commits); pushed `2642d69..2bb9220` (origin 0/0), triggering the GitHub Pages deploy workflow. Feature branch deleted. Full isolated `ci-local.sh` was re-run on merged master before the push: every gate green EXCEPT the documented pre-existing `/garden/` mobile-LHCI local-variance (0.84 vs 0.90, CPU-sensitive, unrelated to this slice — essay pages 0.92, desktop all-green); GitHub's consistent-hardware runners pass `/garden/` (graph-chrome precedent). No new regression from the slice. See [[reference_ci_local_lhci_deps]], [[feedback_verify_before_merge]], [[feedback_test_at_half_screen_1080p]].
