---
name: d2-spec-queued
description: "D.2 multi-target export — spec shipped 2026-06-02 at `docs/superpowers/specs/2026-06-02-phase-3-d2-multi-target-export-design.md` (commit c05b46c). Implementation plan QUEUED, not drafted. Picks up + supersedes the 2026-05-13 spec; reshaped around post-D.1 reality (stock org dispatcher does per-target iteration via hooks keyed on `#+multi_export: t`; existing `a3-publish-deliberate` auto-fires the full publish event). Plan drafted via `superpowers:writing-plans` when slice is actually scheduled."
metadata: 
  node_type: memory
  type: project
  originSessionId: 6e8aa45d-e277-4939-bd42-732f52c1c0ff
---

**D.2 spec shipped 2026-06-02; plan QUEUED.** Per [[design-batch-no-plan-until-implement]], plan drafting waits until implementation begins.

## Spec location

`docs/superpowers/specs/2026-06-02-phase-3-d2-multi-target-export-design.md` — committed in `c05b46c`. Supersedes the older 2026-05-13 multi-target spec (kept in repo for historical reference).

## Architecture decisions made during brainstorm (locked in spec)

The brainstorm question loop converged a single coherent design across 7 multi-choice questions:

| Decision | Choice |
|---|---|
| Scope | Full pickup (PDF + Word together in one slice) |
| Module home | Dotfiles (matches B.4/C/F convention); templates in site `tools/templates/` |
| Vocab parity | Full — same semantic treatment across Hugo + PDF + Word |
| LaTeX class scope | `madkour-paper.cls` only; conference classes deferred to real-submission trigger |
| Dispatcher integration | Hooks on standard backends, keyed by `#+multi_export: t`. Stock `C-c C-e l p` / `C-c C-e o` / `C-c C-e H` all "just work" on multi-export essays |
| Orchestrator UX | Auto: `a3-publish-deliberate` detects `#+multi_export` and runs the full pipeline (Hugo + PDF + Word + bundle placement + frontmatter patch) |
| Visibility tags | 5-tag scheme (3 per-target + 2 shorthand: `:WEB_ONLY:` / `:PAPER_ONLY:`) |
| Fixture | New B-emitted `essay-example-multi.org`; keep example-five as hand-authored D.1 demo |

## Why the existing 2026-05-13 spec needed superseding

The old spec predated:
- The dotfiles-publisher convention (B.4/C/F all live in `~/dotfiles/...`, not site `tools/elisp/` as the old spec proposed).
- D.1's semantic-block vocabulary (12 kinds; old spec had no story for how `#+begin_theorem` reaches LaTeX/Word).
- F.1's bibliography pipeline (`a3madkour-pub-bib-path` defcustom — reused, not duplicated).
- The realization that auto-triggering via `a3-publish-deliberate` is cleaner than a separate `M-x madkour/publish-literate-essay` command.

## Effort estimate (informal, revised)

~7 days focused work (old spec said 4–5d; didn't account for D.1 vocab parity which adds the Lua filter + amsthm declarations). Highest-novelty piece: pandoc Lua filter for stateful theorem-family numbering pass (~2d in own subagent task).

## Pre-implementation reads when slice kicks off

1. `docs/superpowers/specs/2026-06-02-phase-3-d2-multi-target-export-design.md` (the spec)
2. CLAUDE.md "Phase 3" section + the deferred features table
3. [[d1-complete]] for the D.1 shortcode output shape (LaTeX/Word must mirror this)
4. [[f-complete]] for the F.1 bib defcustom name (`a3madkour-pub-bib-path`) and `finish-publish` snapshot lifecycle
5. [[b4-complete]] for `a3-publish-deliberate` integration points + B.4's asset walker
6. [[reference-bbt-brace-protection]] in case the same brace-stripping bug surfaces in LaTeX/biblatex output

## Risks (flagged in spec §10)

- Pandoc Lua filter numbering pass (stateful tree-walk; theorem-family shared counter).
- amsthm + biblatex edge cases (proof env + footnote citations).
- `rsvg-convert` not on PATH on clean macOS install (degrades pipeline; defcustom override is mitigation).
- `reference.docx` style authoring tedious — iterate after first end-to-end run rather than perfecting up front.

## Out of scope (carries to D.x / future slices)

- Cross-reference auto-formatting → D.x
- Section-prefixed numbering → D.x
- `madkour-report.cls` (TOC variant) → gated on self-distribution trigger
- Conference LaTeX classes (`acmart`, `IEEEtran`) → gated on real submission
- Explorable explainables → sub-project E (next after D.2)
- CI-side LaTeX/pandoc builds → author-machine sufficient
- Pandoc docx → org round-trip
- Multi-language / Arabic PDF support
