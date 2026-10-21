---
name: project_section_registry_design
description: "Section registry (data/sections.json + elisp registry + contract-driven a3-publish-mark) — MERGED to local main in both repos 2026-10-21, NOT pushed; push together at end of S1; S1 research dogfood resumes on it"
metadata:
  node_type: memory
  type: project
  originSessionId: 5c2a5d02-07e8-4ea9-b946-2d0cb3a41302
  modified: 2026-10-21T16:17:10.085Z
---

Section-registry project. Spec `docs/superpowers/specs/2026-10-20-section-registry-design.md`. Plans `docs/superpowers/plans/2026-10-20-section-registry-{site,dotfiles}.md`. It was triggered by S1 friction row 15: `a3-publish-mark` left the section fields for the author to type by hand.

**State (2026-10-21):** built via SDD, every task + opus final reviews clean; fast-forward MERGED into local `main` in both repos (site `54b85fa`, then log commit `4ca61e6`; dotfiles `a3b2293`), branches deleted, SDD workspaces deleted. NOT pushed. Dotfiles is also 2 behind origin (user i3 commits, no overlap) — integrate before push.
- **The two branches must land together.** The site deletes `data/works-vocab.json`, which old dotfiles main reads, and the new dotfiles fails closed without `data/sections.json`.
- Evidence:
  - ERT 1007/1007.
  - Every site linter test passes.
  - LHCI desktop and mobile both asserted 28 URLs and passed.
  - A real `a3-pub.sh --publish-living` over ~/org dispatched 15 notes and produced zero content diff.

**What was built:**
- Site:
  - `data/sections.json` covers 14 sections. Each field carries type/required/values/to/from/ask/fill/default, and garden and library extras use variants.
  - `tools/sections.py` is a fail-closed reader plus `check_fields`.
  - All 7 fixture linters were migrated to it.
  - `works-vocab.json` was deleted.
- Dotfiles:
  - `a3madkour-sections.el` is the JSON reader.
  - `a3madkour-publish-registry.el` is one section table plus the only slash↔hyphen conversion.
  - Dispatch and the old section lists now derive from the registry. An unloaded handler is now a loud per-file error.
  - The normalizers and works-lint read the contract.
  - The library emitter quotes number-looking text by contract type.
  - `a3-publish-mark` prompts for exactly the missing contract fields (gather-then-write, idempotent). refs are written as a space list in one quoted string; drafts are excluded from ref targets.

**Known pre-existing (not this branch):**
- `test_check_pagefind_meta` (error).
- `test_fetch_library_covers` (1 failure).
- Integration library lint-clean (2- vs 3-tuple) and poetry relative-audio (Emacs 31 native-comp).
- ERT `multi-pdf/compile-chain-runs-four-passes` is flaky.
- The parallel Playwright flake (row 14).

**Queued follow-ups:**
- C: shared publish template.
- D: org helpers dedup.
- E: `a3-pub.sh` bootstrap.
- F: site Python dedup. Includes the draft predicate written 5 ways (likely bug), and `check_library_covers` duplicating cover keys.
- G: layouts read `site.Data.sections`.
- Mark gaps from the final review:
  - A section change keeps values that are invalid in the new section.
  - `next-weight` sees only published bundles, so two themes marked before one publish both get the same weight and CI fails.
  - A valueless cfm key counts as present.
  - `/enum` on a case-only field returns the first case only.
  - Library digit tags are left unquoted.

**Open work, next session:**
1. Push both repos together at the end of S1 (user decision). Dotfiles: integrate origin i3 commits first.
2. Friction rows 15 (resolved) + 16 (citations.yaml leakage) LOGGED in `4ca61e6`.
3. Resume S1 research: the user runs `a3-publish-mark` on their plain org-roam node (theme "Bayesian reasoning for procedural generation"), then publish, then the research linters/build/visual. After that: library, essay, poetry, games+music, then close-out.
4. User actions:
   - delete `citations.yaml` in both repos;
   - drop `stash@{0}` (site);
   - set `ORG_MATH_LINT_CONFIG` in the shell profile;
   - restart Emacs, or `M-:` require `a3madkour-publish-registry` and `a3madkour-sections`, since `config.org` changed.
5. SDD workspaces deleted after merge; rulings were reported to the user in-session.

Related: [[project_authoring_infra_roadmap]], [[feedback_mutation_test_every_guard]], [[reference_lhci_assertmatrix_exclusive]].
