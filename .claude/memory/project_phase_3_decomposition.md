---
name: phase-3-decomposition
description: "Phase 3 (org-mode pipeline) decomposed 2026-05-20 into 6 independently-spec'd sub-projects A→F; A in brainstorm now"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1a888769-aa2f-4b65-9f3e-7d198d0e6582
---

User brainstorm 2026-05-20 chose to **decompose Phase 3 into 6 sub-projects** rather than the prior 3-slice model. Triggered by the user layering 7 cross-cutting concerns (math lint, content-type templates, explorable explainable workflow, unified def/thm format, citation validation, link rewriting, access control) on top of the existing Phase 3 scope. Originally 5 sub-projects; mid-brainstorm the user split citation pipeline out of C into its own sub-project F. Each sub-project gets its own spec → plan → ship cycle.

**A. Access control + link semantics** — *first; foundational.* Which org notes get published; how `[[id:UUID]]` + `[[file:...]]` org-roam links rewrite to web URLs on export; what happens when a linked-to note isn't published (inert text? omit? warn?). Drives the "is this published?" oracle every other sub-project consumes. **Currently in brainstorm 2026-05-20.**

**B. Per-content-type publish + templates** — the publisher itself (elisp/ox-hugo). Per-destination templates: garden / essay / library / research / works. Carries [[project-phase-3-two-publish-commands]] (frequent/idempotent vs. per-post/deliberate) and [[project-phase-3-library-tag-shelves]] (library tags round-trip). Essay/poetry publish must emit the [[project-phase-3-org-synced-poetry-export]] contract (`[mm:ss]`+`audio_url`).

**F. Citation pipeline + bibliography integration** — split out of C at A's brainstorm (2026-05-20). `[cite:@key]` org marker parsing, lookup against `library.bib` via citar (already in user's emacs config), emission of `data/citations.yaml` entries, integration with the existing site `{{< cite >}}` shortcode runtime, cite-key validation step. Needs A's "is published?" predicate (only validate cite-keys in published files) and B's per-content-type template hooks (where shortcode emission plugs into each section's output).

**C. Pre-publish validators** — mirrors the Python `check_*` linter pattern that gates CI. Math-rendering lint only (KaTeX/MathJax compatibility, balanced delimiters, macro availability). Citation validation was moved to F.

**D. Unified semantic markup** — definitions / theorems / proofs / sidenotes / figures / math as one source vocabulary that renders to Hugo + PDF + Word. **Subsumes** the existing Multi-target export spec (`docs/superpowers/specs/2026-05-13-multi-target-export-design.md`) — revisit and possibly fold/replace inside D.

**E. Explorable explainable workflow** — per-page interactive widgets + per-page JS bundle convention. Was deferred from Phase 0 as "own future spec, referenced from §7 of multi-target export spec"; now in this batch.

**Why this decomposition + ordering:**
- **Why:** Single-spec attempt across 7 concerns would either drag for days or silently lose detail. User chose to keep A and B separate (vs. fuse them into "publisher with link rules baked in") so the "is this published?" oracle stays a stable interface other sub-projects consume.
- **How to apply:** Don't try to merge sub-projects. A's spec must define the published-set predicate + link-resolution contract clearly enough that B can call it as a function. At C's brainstorm, decide whether citation validation splits out as a 6th sub-project. At D's brainstorm, decide whether the existing Multi-target export spec is updated in place or replaced.

**Dependency order:** A → B → F → C → D → E.
- **A first:** foundational — every other sub-project queries "is this note published?" and "what URL does this link become?"
- **B second:** the publisher exists. Per-type templates land here.
- **F right after B:** citation export pipeline needs B's per-content-type template hooks (where the `{{< cite >}}` shortcode gets injected). Slots ahead of C because essays-without-citations is too weak a deliverable; F keeps academic-writing functional.
- **C runs before publish in CI but is built after F exists:** validators need real publish output to validate; can use existing fixtures to scaffold. C is now math-only (citation validation moved to F).
- **D needs B's renderer + a PDF/Word target.** Subsumes Multi-target export.
- **E depends on B** (per-page bundle convention) **and possibly D** (math/figures inside the widget).

**Existing scope that folds into the decomposition:**
- [[project-phase-3-two-publish-commands]] → **B**.
- [[project-phase-3-library-tag-shelves]] → **B**.
- [[project-phase-3-org-synced-poetry-export]] → **B** (Essay/poetry publish).
- Multi-target export spec (`2026-05-13-multi-target-export-design.md`) → **D**; revisit/possibly-supersede inside D.
- About Now widget → depends on **B** (essay/about publish).

**Source-side reality (relevant context from session-start mapping 2026-05-20):**
- `~/org/notes/` is org-roam (UUID `:ID:` properties, bare-slug filenames, ~174 files, flat structure — no garden/essays/research subdirs).
- **Opt-in publication subset already exists:** `~/org/notes/public-notes/` is used by an existing org-publish project (publishes to HTML at `~/Workspace/website/notes`, not Hugo). Plausible foundation for A's published-set predicate.
- **No content-type tags exist** (`:essay:` / `:garden:` etc.) — destination must be invented via per-file keyword, property, subdirectory convention, or tag vocabulary.
- ox-hugo installed but **zero config** — fresh canvas for B.
- ~15 files carry orphan `#+HUGO_LASTMOD:` — residue from a prior aborted ox-hugo attempt.
- Existing `:PROGRESS:` property pipeline (`none → highlighting → ref-notes → main-notes → done`) plausibly maps to garden `growth_stage` for free.
- Custom org link types defined: `supports` / `contradicts` / `extends` / `example-of` / `causes` (color-coded for roam graph) — A must decide how these rewrite (or don't) for the web.

**Session policy note (2026-05-20):** This session is no-commit — user reviews + pushes manually. Brainstorm/spec/plan edits will be made, and commit checkpoints flagged for user.
