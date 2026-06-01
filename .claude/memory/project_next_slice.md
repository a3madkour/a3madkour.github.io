---
name: next-slice
description: "Session-start pointer — next slice is Phase 3 sub-project C (pre-publish validators). F shipped 2026-06-01 end-to-end with Task 18 spot-check passing on real corpus (notes_ref auto-detect now produces 'Related note' links next to bib refs). Per spec sequencing: A → B → F → **C** → D → E."
metadata:
  node_type: memory
  type: project
---

**Next slice = Phase 3 sub-project C — pre-publish validators.** F shipped 2026-06-01; see [[f-complete]].

Per the parent decomposition ([[phase-3-decomposition]]) + CLAUDE.md sequencing: A → B → F → **C (next)** → D → E.

## What C is

From CLAUDE.md "C. Pre-publish validators":

> Python `check_*` pattern.  Math-rendering lint (KaTeX/MathJax compatibility, balanced delimiters, macro availability).  Citation validation was moved to F.

So C is the **math validator**, paralleling the existing site-side `check_*` Python linters (essay-fixtures, garden-links, etc.). New pair: `tools/check_math.py` + `tools/test_check_math.py`.

Scope candidates (to confirm in C's brainstorm):
- Balanced `\(...\)`, `\[...\]`, `$...$`, `$$...$$` delimiters across all `has_math: true` essay bodies.
- KaTeX-supported macro vocabulary (or MathJax, depending on which the site bundles — currently neither is shipped; math is a deferred feature exercised by essay fixture #2's `has_math` flag).
- LaTeX-specific commands that won't render in the chosen JS engine.
- Inline vs display math context sanity.

## Pre-C prep

Per [[design-batch-no-plan-until-implement]] — design batch only; spec C first, plan when implementation slot opens.

Required reads when C kicks off:
1. CLAUDE.md "Phase 3" section + the deferred features table (math is on it).
2. [[phase-3-decomposition]] for the 6-sub-project frame.
3. The 24 existing `tools/check_*.py` linter pairs as the Python style precedent (look at `check_citations.py` for the closest analog since math is also a content-shape check).
4. F spec + plan for how the citation linter pair was scoped (F kept the existing schema, just loosened a regex — C builds a new linter from scratch).

## State of the world at session start

**Site (`~/Sync/Workspace/a3madkour.github.io/`):**
- master = post-F merge (`--no-ff` of `worktree-f-citation-pipeline`). Pre-existing unpushed commits from before F (spec/plan/LHCI stub) + 4 F commits + the merge. Push pending — author held it for the next session.
- Worktree at `.claude/worktrees/f-citation-pipeline` still exists; clean up when push happens.
- `data/citations.yaml` now contains the 3 fixture entries + the author's first real cite (`meiRWoMRetrievalaugmentedWorld2026`) — proof F works end-to-end.
- New garden bundle `content/garden/mei-r-wom-2026/` from the spot-check (a ref-note promoted to garden via `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden`).
- 478 ert + 36 integration tests passing.

**Dotfiles (`~/dotfiles/`):**
- main = `116950b` (Task 18 follow-ups). Unpushed.
- 5 pre-existing dirty tracked files (`.gitignore`, `.zshrc`, `bookmarks`, `early-init.el`, `init.el`) — author's in-progress local work, NEVER commit them.

**Personal notes (`~/org/`):**
- `org/essays/example-one.org` carries the author's first `[cite:@meiRWoMRetrievalaugmentedWorld2026]` — kept for the spot-check.
- `org/notes/ref-notes/meiRWoMRetrievalaugmentedWorld2026.org` was promoted to garden via flags; if you decide to roll back the spot-check, edit the flags back out (or leave it — it's working content now).

## Pending follow-ups (NOT C-scope)

Logged in [[f-complete]]:
- **B.4 orphan-sweep over-deletion** — `--publish-deliberate` of one essay deletes other essay bundles. NOT an F issue; file under B.4.x.
- F.2 — style-override / prefix-suffix org-cite syntax.
- F.3 — `#+print_bibliography:` positional rendering.
- F.x — title quality on ref-notes promoted to garden (full bibliographic header makes a clunky tile title).
- F.x — promote `TestSyncPurges` + `TestHugoRendersCitedEssay` from `@unittest.skip` to runnable (needs roam-indexed fixture harness OR a self-contained live-tree workspace).
- Performance regression test against 15.6k-entry library.bib if publish slowdown surfaces.

## Recommended session start

1. Author pushes the queued site + dotfiles commits (held from F's session).
2. Read CLAUDE.md + [[phase-3-decomposition]] + this file.
3. `superpowers:brainstorming` for C — open design questions: which math engine (KaTeX vs MathJax, both deferred); whether to validate against a vocabulary list or just delimiter balance; whether per-essay `has_math: true` triggers the check.
4. Spec C, queue the plan, ship.
