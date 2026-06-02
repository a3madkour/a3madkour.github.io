---
name: next-slice
description: "Session-start pointer — next slice is Phase 3 sub-project D.2 (multi-target export: one org source → Hugo + PDF + Word). D.1 shipped 2026-06-01 (semantic blocks; see [[d1-complete]]). D.2 picks up the existing spec at `docs/superpowers/specs/2026-05-13-multi-target-export-design.md` (446 lines, designed but not implemented) and wires ox-latex + pandoc to emit the D.1 vocabulary into PDF + Word. Per spec sequencing: A → B → F → C → D.1 → **D.2** → E."
metadata:
  node_type: memory
  type: project
---

**Next slice = Phase 3 sub-project D.2 — multi-target export.** D.1 shipped 2026-06-01; see [[d1-complete]].

Per the parent decomposition ([[phase-3-decomposition]]) + CLAUDE.md sequencing + the brainstorm split during D: A → B → F → C → D.1 → **D.2 (next)** → E.

## What D.2 is

D.1 shipped the **authoring vocabulary** (12 AMS-style block kinds rendered to Hugo only). D.2 picks up the existing **multi-target export pipeline** spec at `docs/superpowers/specs/2026-05-13-multi-target-export-design.md` (446 lines, designed but not implemented) and wires the rendering targets:

1. **Hugo essay** — already shipped (D.1 + existing essay infrastructure).
2. **PDF technical report** — via ox-latex + pdflatex/xelatex + biber.
3. **Word document** — via pandoc + a `tools/templates/reference.docx` style reference.

Three artifacts from one org source. Opt-in via `#+multi_export: t` keyword. Per-target visibility tags (`:NOEXPORT_PDF:`, `:NOEXPORT_WEB:`, `:NOEXPORT_WORD:`). The D.1 vocabulary (theorem / lemma / etc.) must render correctly to all three targets — Hugo ✓ (D.1 shipped), PDF (new), Word (new).

## Pre-D.2 prep

Per [[design-batch-no-plan-until-implement]] — when D.2's slot opens, brainstorm fresh; the existing 446-line spec needs revisiting since it predates D.1. Specifically:

- The existing spec doesn't mention the D.1 vocabulary (definitions, theorems, proofs). D.2's brainstorm needs to add: how does ox-latex translate `#+begin_theorem` into a real LaTeX theorem environment (`\begin{theorem}`)? How does pandoc translate it into Word styles?
- The existing spec lays out the orchestrator architecture (one Emacs command runs all 3 backends). That part stands as-is.

Required reads when D.2 kicks off:

1. CLAUDE.md "Phase 3" section + the deferred features table.
2. [[phase-3-decomposition]] for the 6-sub-project frame.
3. The existing multi-target spec `docs/superpowers/specs/2026-05-13-multi-target-export-design.md`.
4. [[d1-complete]] for the D.1 shortcodes' output shape — D.2 needs to mirror this.
5. [[time-synced-poetry-slice]] (synced-poetry has audio+animation modes) and [[citation-export-slice]] (BibTeX/APA/Chicago/MLA/RIS exports) as prior multi-target-ish patterns.

## State of the world at session start

**Site (`~/Sync/Workspace/a3madkour.github.io/`):**
- master = local tip post-D.1 (`a2f32f7` for CLAUDE.md + earlier D.1 commits + the `c6dcbde` §11-comment fix-up). **Not pushed** — held for author review.
- Worktree directory empty (no worktrees needed for D.1).
- 481 ert tests + 7 site check_math tests passing.

**Dotfiles (`~/dotfiles/`):**
- main = `a6336f3` (D.1 T6 ox-hugo config). **Not pushed**.
- 5 pre-existing dirty tracked files (`.gitignore`, `.zshrc`, `bookmarks`, `early-init.el`, `init.el`) — author's in-progress local work, NEVER commit them.
- `org-math-lint` venv at `~/org/notes/tools/org-math-lint/.venv/` still broken (cross-platform mismatch). Pre-existing issue from C; recreate if math validation gate is needed. See [[reference-org-math-lint-venv-platform]].

**Personal notes (`~/org/`):**
- Unchanged since end of F.

## Pending follow-ups (NOT D.2-scope)

Logged in [[d1-complete]]:
- Cross-reference auto-formatting (`{{< ref-block >}}`).
- Section-prefixed numbering.
- Custom block kinds beyond the 12.
- Per-essay numbering reset point.
- Generalize `[id]:hover::after` deep-link affordance.
- Goldmark LaTeX-delimiter strategy (for when KaTeX ships).

Logged in [[c-complete]]:
- org-math-lint venv recreation on this host.
- Helper exit-code conflation (broken-install vs validation-failure) in a3-pub.sh.
- Interactive `M-x a3-publish-*` paths uncovered by math gate.
- Garden/research/library math not validated.

Logged in [[f-complete]]:
- B.4 orphan-sweep over-deletion.
- F.2/F.3 cite-syntax extensions.
- F.x ref-note title quality.

## Recommended session start

1. Author pushes the queued site + dotfiles commits (D.1 commits held from this session).
2. Read CLAUDE.md + [[phase-3-decomposition]] + this file + [[d1-complete]] + the existing multi-target spec.
3. Decide D.2 scope: full pickup of existing spec OR smaller carve-out (e.g., PDF target only, Word deferred).
4. `superpowers:brainstorming`. Open design questions:
   - Does the existing 446-line spec need revisiting in light of D.1's vocabulary, or just minor additions?
   - LaTeX target: which class file? `madkour-paper` per existing spec, OR pull from real essay frontmatter?
   - Word target: how to define `reference.docx` styles for the 12 block kinds?
   - Test surface: an integration test that publishes example-five to all 3 targets and validates each artifact?
