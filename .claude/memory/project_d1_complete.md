---
name: d1-complete
description: "D.1 semantic blocks — shipped 2026-06-01. 12 AMS-style Hugo shortcodes (theorem family + definition strong-tier; 6 soft-tier; proof chrome-less with ∎). CSS §47 three-tier visual treatment using existing tokens. ox-hugo `org-hugo-paired-shortcodes` config drives `#+begin_<kind>' → `{{< <kind> >}}'. example-five fixture exercises all 12 kinds + cross-ref. +1 ert (480 → 481). No new linter pair; no CI step bump. Subagent-driven, 7 tasks, ~7 commits across 2 repos."
metadata:
  node_type: memory
  type: project
---

**Shipped (code-complete 2026-06-01):** D.1 — semantic blocks per `docs/superpowers/specs/2026-06-01-phase-3-d1-semantic-blocks-design.md` + `docs/superpowers/plans/2026-06-01-phase-3-d1-semantic-blocks.md`. 7 tasks, subagent-driven.

## What ships in D.1

### Site (`~/Sync/Workspace/a3madkour.github.io/`; baseline `e3369dd` → tip `a2f32f7`)

- **12 new shortcodes** in `layouts/shortcodes/` — theorem / lemma / corollary / proposition / definition / proof / remark / example / note / claim / conjecture / axiom. Each ~10 LoC; follows the `sidenote.html` `$page.Scratch` counter pattern.
- **CSS §47** (~80 LoC) — three-tier styling using `--color-burgundy` / `--color-stone` / `--color-ink-soft`. Anchored blocks (`[id]:hover::after`) get a `" #"` deep-link affordance (new pattern in this codebase; generalize later if headings or garden notes want it).
- **`content/essays/example-five/index.md`** — kitchen-sink fixture demonstrating all 12 kinds + a `[#thm-ivt]` cross-ref. Two-stage commit (T1 frontmatter stub + T4 body) intentionally leaves `check_math.py` failing between T1 and T4; intermediate state documented in the T1 commit body.
- **`CLAUDE.md`** — new "Semantic blocks (AMS-style)" subsection under Architecture, sibling to C's "Math pipeline".

### Dotfiles (`~/dotfiles/`; baseline `0284026` → tip `a6336f3`)

- **`a3madkour-publish-export.el`** — two new `setq` blocks after `(require 'ox-hugo)`:
  - `org-hugo-paired-shortcodes` set to the 12-kind space-separated list.
  - `org-hugo-special-block-type-properties` alist with `:trim-pre t :trim-post t` for each kind (keeps emitted markdown tidy).
- **`a3madkour-publish-essays-test.el`** — +1 ert (`special-block-round-trip`) verifying `#+attr_shortcode: :title Foo :id thm-foo` + `#+begin_theorem` round-trips to `{{< theorem title="Foo" id="thm-foo" >}}...{{< /theorem >}}`.
- ert: 480 → 481.

## In-slice fix-ups

One small carry-forward during T3 (CSS §47):

- **`c6dcbde`** — fixed misleading "§11 heading anchor" comment in `.block-strong[id]:hover::after` rule. The original plan text claimed to mirror "headings in §11" but §11 is actually the Essay grid section, not headings, and the hover affordance is a new pattern in this codebase. Code-quality reviewer caught it; one-line comment rewrite landed as a follow-up commit.

## Why this slice mattered

The site has had the existing semantic primitives (sidenote, figure, spoiler) since Phase 1, but had no vocabulary for the rigorous-prose constructs that an academic essay needs — theorems, definitions, proofs, lemmas. D.1 closes that gap with 12 AMS-style shortcodes wired into the ox-hugo pipeline.

The brainstorm split D into two sub-projects (D.1 vocab, D.2 multi-target export). D.1 ships value first (rigorous essays writable); D.2 picks up the existing `2026-05-13-multi-target-export-design.md` and adds PDF + Word render targets to the same vocabulary.

## Known follow-ups (D.x)

1. **Cross-reference auto-formatting.** `{{< ref-block "thm-foo" >}}` → "Theorem 1" via a two-pass scratch lookup. Trigger: the first real essay that hits renumber-induced drift on a manually-typed reference.
2. **Section-prefixed numbering** ("Theorem 3.2"). Trigger: a long essay where bare integers become hard to navigate.
3. **Custom block kinds beyond the 12** (e.g., `principle`, `metatheorem`, `observation`). Trigger: spec request from real essay usage.
4. **Per-essay numbering reset point** ("reset theorem-family at this H2"). Trigger: long essays where two unrelated arguments share theorem numbering.
5. **D.2 multi-target export.** Picks up the existing multi-target spec; wires the same 12-kind vocabulary into PDF (ox-latex) + Word (pandoc) renderers.
6. **Generalize the `[id]:hover::after` deep-link affordance** to headings and garden notes when the appetite shows up. Currently the pattern is only on `.block-strong[id]` / `.block-soft[id]` / `.block-proof[id]`.
7. **Goldmark LaTeX-delimiter strategy for KaTeX integration.** D.1 doesn't surface this since KaTeX is deferred, but the dev-server spot-check noticed that Goldmark strips `\(...\)` backslashes by default (renders `\(x_0\)` as `(x_0)`). Future KaTeX shortcode-or-Goldmark-extension work will need to handle this. C's `tools/check_math.py` was correctly catching the markdown-level markers — the issue is render-time only.

## End-of-slice test inventory

- ert (dotfiles): 480 → 481 (+1 round-trip integration).
- Site Python unit tests: unchanged.
- Linter pairs: 25 (unchanged).
- CI step count: 63 (unchanged).
- Hugo shortcode count: 8 → 20 (existing cite/sidenote/figure/spoiler + 4 deferred stubs unchanged + 12 new semantic blocks).

## State at end of session

- All site commits LOCAL on `master` (8 commits including T0 spec + T0a spec amendment + T0 plan + 7 implementation tasks + the §11-comment fix-up).
- All dotfiles commits LOCAL on `main` (1 commit: `a6336f3` from T6).
- Site working tree: clean.
- Dotfiles working tree: pre-existing 5 dirty tracked files unchanged (author's in-progress; never staged).
- All gates green: site CI (`check_fixtures.py`, `check_math.py`, `check_smoke.py` all pass), dotfiles ert 481/481 with 0 unexpected, Hugo `--minify` build clean.
- Negative-path verification confirmed `check_math.py` errors correctly when `has_math: true` is flipped to `false` while math markers persist in the body.
