---
name: project-phase-8-a11y-close-out
description: "a11y sweep (5 BLOCKERs + 10 WARNs + heading hierarchy fix) shipped 2026-05-13 (commit 7ac2539, pushed to origin); functionally closes Phase 8 Slice 3 except for interactive walkthrough items"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0ca45fc5-2a99-438c-bd84-6dc5e4765696
---

Phase 8 a11y close-out — shipped to master 2026-05-13 (commit `7ac2539`, pushed to origin). 34 files, +189 / -97. No new merge — direct commit on master since the changes weren't on a slice branch.

**Why:** Phase 8 Slice 3 ([[project-phase-8-slice-3-final-qa]]) left §1.1–1.5 + 1.7–1.9 keyboard nav, §2 SR, §3 CB sim, §4 mobile, §5 perf items unwalked. Approach this session: 4 parallel agents did a STATIC code pre-scan covering all 5 categories; surfaced 5 BLOCKERs + 16 WARNs + 11 NITs findable from code alone. User authorized "B1–B5 + W11 + W12" first round, then "fix the WARNs too" — all blockers + 10 of the warns shipped, the rest (3) intentionally deferred or NITs.

**How to apply:**
- **Phase 8 is functionally closed for code work.** Only the interactive walkthrough items remain — those require the user to actually run keyboard nav / SR / DevTools deficiency emulation in a browser. The pre-scan + fix sweep handled every issue findable without a human at a keyboard.
- **Next session priority:** Citation export slice (`docs/superpowers/specs/2026-05-13-citation-export-design.md` + plan `docs/superpowers/plans/2026-05-13-citation-export.md`, 24 tasks). No `slice/citation-export` branch exists yet — create from master. Per documented sequence: Citation export → Time-synced poetry → Phase 3 Slice 1 (garden publish).
- **Don't redo the static scan** — the agents covered every checklist item; if a future SR walkthrough surfaces new issues, those should be specific live-AT findings (e.g. "VoiceOver mispronounces X"), not things a static scan would have caught.

**What this commit landed:**

*Blockers (5):*
- `assets/js/filter-chips.js` — added ArrowLeft/Right handler to PRIMARY chip strip (was secondary-only inside `<details>`)
- 9 layouts swapped inner `<main>` → `<article>` (baseof already provides `<main>` — nested mains were invalid landmarks)
- `layouts/research-theme/single.html` — h1→h3 skip fixed by wrapping the 3-col questions block in `<section id="questions"><h2>Questions</h2><div class="three-col-questions">…</div></section>`
- `layouts/shortcodes/sidenote.html` — `<span role="button">` → `<sup><a href="#sn-N">` standard footnote pattern; essay.js updated to listen on inner `<a>` and read href instead of aria-controls
- `assets/css/main.css` — `.search-modal-result-snippet mark` adds `font-weight: 600` (was colour-only highlight)

*Warns (10 shipped):*
- All 3 standalone graph pages get a focus-visible "Skip past graph" link + tabindex=-1 anchor target after SVG
- `layouts/partials/library/status-badge.html` — `role="img"` + `aria-hidden` glyph span (was glyph-only text node — SR could announce "check mark" instead of "finished")
- `layouts/garden/graph.html` + `layouts/research/graph.html` — empty `<ul>` legends start `[hidden]`; `buildLegend()` removes attr when populating
- `assets/css/main.css` — citation links keep underline at rest; `.essay-references li:target` gets 3px burgundy `border-left` (shape redundancy under achromatopsia)
- `tools/check-contrast.py` — `--color-warn` added to pairings (warn/stone + stone/warn); the `.works-status-pill[data-status="in-progress"]` color override removed so text inherits stone (5+:1 contrast)
- Garden + research standalone graph SVG: `min-height: 480px` (matches works pattern; prevents shrink-to-252px on landscape phones)
- `layouts/partials/library/type-glyph.html` — library cover `<img>` gets `width`/`height`/`decoding="async"` attrs (prevents CLS)
- QA checklist 1.7 reworded — `<kbd>` hints intentionally non-focusable (deviation from "Tab cycle includes kbd-hints" was the wrong demand — `<kbd>` should not be interactive)

*Heading hierarchy sweep (caught during verification, NOT in original agent findings):*
- essay-card{,-featured}: h3 → h2 (cards directly under h1 with no h2 wrapper)
- works tile / game-card / music-row / poem-row: h3 → h2 (same pattern)
- homepage studio-strip work title: h5 → h3 (was an h2 → h5 skip)
- library row-title: h4 → h3
- library currently-active / year-section / up-next: `<header class="library-…-rule">` → `<h2>` (were styled divs, not headings)
- Result: every layout family now renders a clean h1→h2→h3 tree

**WARNs intentionally NOT fixed (judgement calls deferred to live walkthrough):**
- W1 graph SVG tab-flood per-node tabindex=0 — addressed via skip-link instead. Per-node focus retained for keyboard activation.
- W2 kbd-hints non-focusable — documented as deviation from spec checklist 1.7.
- W3 sidenote desktop-no-reveal — addressed indirectly by B4 (marker is now a real link that jumps to aside).

**Linter footprint:**
- `tools/check-contrast.py` grew from 4 pairings to 6 (added warn/stone + stone/warn). Now 6 pairings × 2 modes = 12 checked combinations.
- No new linter pair added (the changes touched existing layouts/JS, not a new domain).

**Related memory:**
- [[project-phase-8-slice-3-final-qa]] — original partial QA pass; this commit closes most of what was left
- [[project-phase-8-slice-1-pagefind-runtime]]
- [[project-phase-8-slice-2-ci-gates]]
- [[feedback-verify-contrast-ratios]] — relevant when adding new contrast pairings
