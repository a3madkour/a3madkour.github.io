---
name: a1b-complete
description: "A.1.b link-rewriter slice — implementation complete + Task 19 spot-check verified; staged in dotfiles, awaiting author commit. Next: A.1.c (assets) per Phase 3 sequencing."
metadata: 
  node_type: memory
  type: project
  originSessionId: 7ef3bb18-9acf-451e-8f17-f5a28329110c
---

**State (2026-05-23):** A.1.b link-rewriter slice is **implementation-complete + verified**. 10 files staged in `~/dotfiles` (5 modified + 4 new + 1 wrapper-script fix), 1 working-tree change to the plan doc in the site repo. Author commits between sessions per session policy. Suggested commit messages in the session transcript + at plan doc lines 1879-1914.

## What shipped

20 plan tasks executed via subagent-driven-development. Test count progression: 45 (A.1.a baseline) → 109 (end of slice, including 11 review-driven regression-guard tests beyond the plan's 98 target).

Per-task summary (in execution order this session): Task 9 (file-or-id dispatch) + Task 10 (`:had-slug-override-p`) + Task 11 (skeleton) + Task 12 (heading-anchor, +4 from Hugo source-of-truth correction) + Task 13 (external) + Task 14 (id-links, +1 from heading-suffix happy path) + Task 15 (heading-anchor existence, +2 from case-sensitivity + decorations) + Task 16 (file-link auto-convert, +2 from subtree-leak + relative-path) + Task 17 (typed + class) + Task 18 (`:pending-asset`) + Task 19 (spot-check, +2 from org-roam-id-find cons fix).

## Bugs caught during Task 19 spot-check

1. **`a3-pub.sh` wrapper** missed loading `a3madkour-publish-rewrite` (only loaded the entry-point). Fixed: added `(straight-use-package 'org-roam)` + `-l a3madkour-publish-rewrite` to the batch invocation.
2. **`--id-to-file` cons-cell** — `org-roam-id-find` returns `(file . pos)`, not a string. cl-letf test stubs in Tasks 7-9 returned plain strings, masking this until real org-roam was exercised. Fix: wrapper now `cond`s on `nil`/`cons`/`stringp` with defensive error for unexpected types. 2 regression tests pin the cons-shape handling. See [[org-roam-id-find-returns-cons]].

## Spot-check parity verified

Heading-anchor algorithm matches **real Hugo byte-for-byte** across all 8 emitted `id="..."` values in `public/essays/example-deep-toc-essay/index.html` — including non-trivial Unicode (middle-dot `·` U+00B7 drop, em-dash `—` U+2014 space-flanked → `--` non-collapse, ASCII-only kept-set behavior). The Task 12 algorithm corrections (trim + drop `Nl`/`No` + empty→`"heading"` fallback) were essential — without them this round-trip would have diverged.

## Open items (carried forward to next slice)

1. **HTML escaping decision** (Task 13 review carry-forward): every `:html` branch uses `(format "<a href=\"%s\">%s</a>" path text)` without escaping. Safe for trusted-author content but needs explicit design — pre-escape-on-`text`-contract vs emit-time `--html-escape` helper. Fold into A.1.c plan brainstorm.
2. **Parent spec amendments** to `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §6: (a) Task 17 narrowing wording — "class always emitted regardless of target state" → "class on `:html` variants only" (defcustom docstring already updated inline); (b) Task 12 algorithm source-of-truth — cite Hugo's `sanitizeAnchorNameWithHook`, not bare Goldmark `auto_heading_id`.
3. **`org-roam-directory` default mismatch**: defaults to `~/org-roam/` but user's notes live in `~/org/notes/`. The publish wrapper or B's publisher needs to either set this in `a3-pub.sh` or surface a setup step.

## User-workspace findings (not bugs in publish code; for awareness)

- **No notes currently have `HUGO_PUBLISH:`** — couldn't exercise the "live target" half of Task 19 Step 2. Private/inert half ran successfully against a real `:ID:`-bearing note.
- **UUID collision** in user's workspace: `09049cd8-ba99-435d-a8f2-9c0cbf9322a4` exists in both `~/org/notes/bayesian_statistics.org` AND `~/org/notes/tools/org-math-lint/workspace/bayesian_statistics.org` (a test fixture from the user's org-math-lint subproject). Real org-roam DB lookup returned the latter. User-side data hygiene, not a publish concern.

## What's next (per CLAUDE.md sequencing)

**A.1.c — asset handling + 24th linter pair.** This is the next sub-project A slice. It replaces the `:pending-asset` stub with real canonical-root resolution + a Python linter pair for asset references. Before brainstorming A.1.c:
- Decide HTML-escaping contract (above).
- Apply parent-spec amendments (above).
- Author commits the A.1.b dotfiles staging + the A.1.b plan correction.

After A.1.c: A.1.d (unpublish + integration). Then move to sub-project B (publisher + templates), then F (citations), C (validators), D (unified markup), E (explorables). See [[phase-3-decomposition]].

## Cross-references

- [[a1a-foundations-slice]] — A.1.a context
- [[a1a-to-a1b-carryforward]] — 3 carry-forwards (all now resolved: `slug_override` via Task 10, `note-metadata` + memo via Tasks 3-4, redundant guards via Task 6)
- [[phase-3-decomposition]] — sub-project A→F mapping
- [[org-roam-id-find-returns-cons]] — API gotcha for future elisp tests
- [[phase-3-two-publish-commands]] — when B starts, design the two publish entry-points
- [[phase-3-library-tag-shelves]] — B's library publisher round-trip rule
