---
name: garden-path-log-retrieval-slice
description: Phase 8 deferral — 3 consumer surfaces for the garden visited-list (widget + popover + /history/ page) + v1→v2 schema upgrade; shipped 2026-05-13. Closes the last Phase 8 deferral.
metadata: 
  node_type: memory
  type: project
  originSessionId: db0fe890-9229-4849-89d1-9d213bd28e0d
---

Phase 8 deferral cleared. Shipped 2026-05-13 (pushed `5d56dbd..4e3f576` to origin/master).

**Three new surfaces consume the persisted visited-list:**
- Widget at top of `/garden/` — up to 5 dedup'd recent paths as chip+arrow chains with relative timestamps. Whole row is one `<a>` so a click anywhere loads the full path via `?stack=…`.
- Popover off the path-log "N in stack" count on note pages (desktop only). `role="dialog"`, focus trap, Esc with `stopImmediatePropagation` so it doesn't fire garden-stack's stack-clear handler.
- Dedicated `/garden/history/` page with full list (cap 20 sessions), three empty-state branches per consent state, "Re-enable tracking" button for the `consent === 'no'` branch.

**Schema upgrade (v1 → v2):** `localStorage['garden-path-log']` changed from `Array<string>` (flat slug list) to `{version:2, sessions:[{root, slugs, at}]}`. One-shot migration on first read wraps v1 data as one synthetic session with `at: 0`. `garden-stack.js` swaps `persistVisited(slug)` for `startSession()` (at `init()` end) + `extendSession(slug)` (in `appendColumn`). `clearStack` does NOT end the session — matches "start over from here" intent.

**Files added:**
- `assets/js/garden-history.js` — shared core (storage + migration + dedupe + formatRelativeTime + renderPath + clearHistory + setConsent).
- `assets/js/garden-recent-paths.js` — mount module covering BOTH `.garden-recent-paths` (widget) AND `.garden-history` (page).
- `assets/js/garden-pathlog-popover.js` — popover mount (desktop only).
- `layouts/partials/garden/recent-paths.html` — widget shell.
- `layouts/garden/history.html` — history page layout (server shell, JS hydrates).
- `content/garden/history/_index.md` — selects `layout: history`.
- `tools/check_garden_history.py` + `tools/test_check_garden_history.py` — new linter pair (10 source-side assertions including `"version": 2` literal sentinel in `garden-stack.js`).

**Files modified:**
- `assets/js/garden-stack.js` — v2 migration (drop persistVisited, add startSession/extendSession, import readHistory/writeHistory from shared core).
- `assets/js/entry-garden.js` — +2 imports for new mount scripts.
- `layouts/garden/list.html` — include the recent-paths partial after garden-hero.
- `layouts/partials/garden/path-log.html` — add `<a class="path-log-history" href="/garden/history/">history</a>` to the chrome strip.
- `assets/css/main.css` — new §43 (~170 lines: widget + popover + history page + shared `.path-row`/`.path-chip`/`.path-arrow`/`.path-time` primitives).
- `tools/check_garden_fixtures.py` — incidental fix: skip Hugo section dirs (those with `_index.md` but no `index.md`) so `/garden/history/` doesn't false-fail the note linter.
- `.github/workflows/hugo.yaml` — 42 → 44 named steps.
- `CLAUDE.md` — shipped entry; Final QA + Phase 8 follow-up entries updated to mark all deferrals closed.

**Specs / plans committed:**
- `docs/superpowers/specs/2026-05-13-garden-path-log-retrieval-design.md` (commit `0aa73e4`).
- `docs/superpowers/plans/2026-05-13-garden-path-log-retrieval.md` (commit `d1d4697`).

**Process notes (subagent-driven execution, 13 plan tasks):**
- Tasks 1–4 (linter scaffold + impl + shared core + garden-stack migration) shipped with full spec + code-quality reviews; all GREEN.
- Tasks 5–7 (widget + page + popover) similar pattern.
- Task 8 (wire imports) trivial; skipped code-quality review since it was a 4-line wire-up.
- Task 9 scripted verification surfaced a `check_garden_fixtures.py` regression: the linter iterated every dir under `content/garden/` expecting `index.md`, but the new `/history/` is a Hugo section with `_index.md`. Fixed with a 5-line skip rule (commit `862aeb1`); didn't update the sibling test since the skip rule is trivially correct.
- Task 10 browser walkthrough surfaced two issues fixed in commit `4a34372`:
  1. Only the leftmost chip in a path row carried `?stack=…`; other chips jumped to single notes. Refactored `renderPath()` so the WHOLE row is one `<a>` wrapping decorative `<span>` chips — any click loads the full path.
  2. Removed all trailing `→` arrows from link labels (widget "Reading history →", popover "full history →", path-log chrome "history →"). User explicitly asked to strengthen [[no-arrow-prefix-on-links]] to disallow `→` in chrome too, not just content. Memory updated accordingly.

**Phase 8 status:** Functionally closed. Only the interactive QA walkthrough items remain (keyboard nav verification, SR walkthrough, colour-blindness simulation, mobile audit at breakpoints, perf manual cross-check) — all need a human at hardware, not codeable work.

See also: [[rss-xsl-pretty-render-slice]], [[phase-8-slice-3-final-qa]], [[phase-8-a11y-close-out]], [[no-arrow-prefix-on-links]], [[chrome-routing-follows-scope]].
