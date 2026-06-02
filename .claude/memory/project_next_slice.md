---
name: next-slice
description: "Session-start pointer — next slice is Phase 3 sub-project D (unified semantic markup: def / thm / figure / sidenotes / math in one source vocabulary rendering to Hugo + PDF + Word). C shipped 2026-06-01 (math validator, integration slice; see [[c-complete]]). Per spec sequencing: A → B → F → C → **D** → E."
metadata: 
  node_type: memory
  type: project
  originSessionId: 29127c6c-92db-4a63-8841-a53b487a6d52
---

**Next slice = Phase 3 sub-project D — unified semantic markup.** C shipped 2026-06-01; see [[c-complete]].

Per the parent decomposition ([[phase-3-decomposition]]) + CLAUDE.md sequencing: A → B → F → C → **D (next)** → E.

## What D is

From CLAUDE.md "D. Unified semantic markup":

> Definitions / theorems / proofs / sidenotes / figures / math in one source vocabulary that renders to Hugo + PDF + Word. **Subsumes** the prior Multi-target export spec (`docs/superpowers/specs/2026-05-13-multi-target-export-design.md`) — revisit inside D.

So D is the **largest** of the remaining sub-projects. It:

1. Defines a single source vocabulary for semantic blocks — `definition`, `theorem`, `proof`, `figure`, `sidenote`, plus math (which K just validated).
2. Renders that vocabulary to **three** targets: Hugo (web), PDF (LaTeX), Word (docx). Multi-target export folds into this.
3. Likely subsumes the existing fragmented stub-shortcodes (`sidenote`, `figure`, `spoiler`) that already exist on the Hugo side, AND the deferred ones (`widget`, `lyrics`, `video-sync`).
4. Has the biggest unresolved-design surface of any remaining slice. Brainstorm will be substantial.

## Pre-D prep

Per [[design-batch-no-plan-until-implement]] — when D's slot opens, brainstorm fresh; don't try to draft the plan from this stub. Required reads:

1. CLAUDE.md "Phase 3" section + the deferred features table.
2. [[phase-3-decomposition]] for the 6-sub-project frame.
3. The existing multi-target export spec: `docs/superpowers/specs/2026-05-13-multi-target-export-design.md` (will be revisited inside D).
4. The existing shortcode stubs in `layouts/shortcodes/` — `sidenote.html`, `figure.html`, `spoiler.html` are real; `widget.html`, `lyrics.html`, `video-sync.html` are deferred-feature placeholders (per CLAUDE.md "Deferred features" table).
5. [[c-complete]] for what math validation looks like post-C.
6. [[time-synced-poetry-slice]] + [[citation-export-slice]] for prior multi-target-ish work (poetry has audio+animation modes; citations have BibTeX/APA/Chicago/MLA/RIS exports).

## State of the world at session start

**Site (`~/Sync/Workspace/a3madkour.github.io/`):**
- master = post-C local tip `8808c74`. Pre-existing unpushed F commits (`9d333c4`, `930bcec`, `e3b9c6a`) + new C commits (`07ff27e`, `3448b13`, `0639291`, `9a4e4e3`, `bd70977`, `0ae3c73`, `5e0284b`, `8808c74`). **Not pushed** — held for author review of the C slice.
- Worktree `.claude/worktrees/f-citation-pipeline` still exists; clean to remove after push.
- 480 ert + 36 integration + 7 new check_math sibling tests passing.

**Dotfiles (`~/dotfiles/`):**
- main = `0284026` (C T9 wire). 5 local C commits (`81fae4d`, `89092f8`, `8049844`, `7b2db57`, `0284026`). **Not pushed**.
- 5 pre-existing dirty tracked files (`.gitignore`, `.zshrc`, `bookmarks`, `early-init.el`, `init.el`) — author's in-progress local work, NEVER commit them.
- `org-math-lint` venv at `~/org/notes/tools/org-math-lint/.venv/` is **broken** on this host (cross-platform mismatch); recreate before exercising the math gate. See [[reference-org-math-lint-venv-platform]].

**Personal notes (`~/org/`):**
- Unchanged since end of F.

## Pending follow-ups (NOT D-scope)

Logged in [[c-complete]]:
- **org-math-lint venv recreation** on this host (5-line shell incantation).
- **Helper exit-code conflation** in `a3-pub.sh` — distinguish "broken install" from "validation failure" via an `import org_math_lint` probe.
- **Interactive `M-x a3-publish-*` paths uncovered** by the math gate.
- **Garden / research / library math** not validated by `check_math.py` (essays-only V1).

Plus from [[f-complete]]: B.4 orphan-sweep over-deletion; F.2/F.3 cite-syntax extensions; F.x ref-note title quality.

## Recommended session start

1. Author pushes the queued site + dotfiles commits (10 local C commits held from this session).
2. Read CLAUDE.md + [[phase-3-decomposition]] + this file + [[c-complete]].
3. Decide whether D is in scope now or defer (D is large; E may be smaller).
4. If D: `superpowers:brainstorming`. Open questions: source vocabulary syntax (org `:custom-id:` blocks? `#+begin_definition`?); render-target architecture (one renderer per target? one IR?); how `definition` / `theorem` / `proof` interact with the existing org-mode export and ox-hugo.
