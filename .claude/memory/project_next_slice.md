---
name: next-slice
description: "Session-start pointer — next slice is B.3 (research handler). B.2 shipped 2026-05-29/30: per-medium YAML row publisher + retroactive --git-mtime-of-file + --filter-editorial-tags helpers (closed B.1.x #2 + #6) + dispatch alist refactor to string-keyed slash-form section paths. 309 ert + 19 Python integration tests. Per spec §12 sequencing: B.3 → B.4 (essays) → B.5 (works) → B.6 (streams) → B.7 (about) → F (citations) → C (math validators) → D (unified markup) → E (explorables)."
metadata:
  node_type: memory
  type: project
---

**Next slice = B.3 — research handler.** B.2 shipped 2026-05-29/30; see [[b2-complete]].

Per design spec §12 slice ordering: A → B.0 → B.1 → B.1.1 → B.2 → **B.3 (next)** → B.4 → B.5 → B.6 → B.7 → F → C → D → E.

## What B.3 must do

Research has **two cascade types** sharing one section path tree: `research/themes` and `research/questions`. Each is a per-page Hugo bundle (`content/research/{themes,questions}/<slug>/index.md`), like garden — not like library's YAML rows. So B.3 reuses much of B.1's shape (ox-hugo invocation, bundle emit, link rewriter, asset copier), and registers **two handlers in the dispatch alist pointing at the same `publish-research-file`** (same pattern B.2 used for the 4 library mediums).

Required frontmatter contracts (see CLAUDE.md "Research"):
- **theme** (cascade `type: research-theme`): theme-specific fields including `weight` (deterministic graph palette — `validate_unique_theme_weights()` in the linter).
- **question** (cascade `type: research-question`): question-specific fields including `theme` parent reference + `parent_question` (optional) + `supporting_notes` (list of garden slugs).

Cross-linking validators (in `tools/check_research_links.py`):
- `garden_topic_ref` → must resolve to a garden bundle.
- `theme` → must resolve to a theme bundle.
- `parent_question` → must resolve to a question bundle.
- `supporting_notes` → each must resolve to a garden bundle.
- `related_essays` → each must resolve to an essay bundle.

## Special considerations carried forward

- **Slash-form section paths are canonical** ([[b2-complete]] Architectural Decision 1): register `"research/themes"` and `"research/questions"` as two separate alist entries pointing at the same handler function.
- **Hugo `unsafe: true` is sitewide** ([[goldmark-unsafe-for-ox-hugo-html]]): research bodies will exercise the `@@html:` flow if they contain id-links (likely — research notes cite garden notes a lot).
- **Garden's normalizer is already cleaner**: `--filter-editorial-tags` + `--git-mtime-of-file` shipped in B.2. B.3's research normalizer should use both from the start.
- **Two publish commands** ([[phase-3-two-publish-commands]]): research is in the "frequent + idempotent" set with garden + library. Register in `publish-living`'s walker, not a deliberate per-post command.
- **`finish-publish`'s no-retry on `delete-bundle` 'failed**: still open. Research will exercise this path (themes + questions are deletable bundles). Worth fixing in or alongside B.3 rather than carrying the gap further.

## State of the world at session start

**Site repo (`/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`):**
- master is **at origin/master**: `master = 6e5a746`. All B.2 work pushed (last push `4fe4870..6e5a746`).
- Real B-emitted garden bundles: 4 (`bayesian-statistics`, `bias-vs-variance`, `cellular-automata-are-visual-rule-based-systems`, `maximum-a-posteriori-map`).
- `data/{reading,listening,playing,watching}.yaml` — still fixture rows (B.2 Task 17 spot-check not yet performed).
- `hugo.yaml` — `markup.goldmark.renderer.unsafe: true` (from B.1.1) + Hugo 0.162.1 pin + `_index.md` homepage.
- 19 Python integration fixtures passing.
- Working tree clean (modulo `node_modules/`, pre-existing untracked).

**Dotfiles (`~/dotfiles/`):**
- main is at `23fc5d7`; pushed.
- 309 ert tests passing.

**Personal notes (`~/org/notes/`):**
- 4 garden notes annotated with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden`.
- **No `library-*.org` annotations yet** — B.2 Task 17 still pending.
- **No research notes annotated yet** — B.3 spot-check will need a few.

## Recommended session start

1. Read site CLAUDE.md + [[b2-complete]] + [[b1-complete]] (for the per-bundle handler precedent) + [[phase-3-decomposition]].
2. Read parent B spec `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` §9 (research pipeline shape).
3. `superpowers:brainstorming` for B.3 — the themes/questions split + cross-linking surface (theme ↔ question + supporting_notes + related_essays) is novel enough to warrant a design pass before writing the plan.
4. Then `superpowers:writing-plans` for the implementation.

## Pending non-B.3 follow-ups

If the author wants to pause B and clean up first:
- **B.2 Task 17 real-corpus spot-check**: seed real `~/org/notes/library-*.org` annotations and run publish-living against the real site. Same shape as B.1's Task 17 (which produced the 4 garden bundles).
- **B.2.x follow-ups** (from [[b2-complete]] Known issues): `check_library_covers.run(root)` API gap, `--render-scalar` fallback `%S` hardening, `:group` defcustom rename, works sidebar overflow (pre-existing spec §13 item).
- **Open B.1.x #5**: `finish-publish` no-retry on `delete-bundle` 'failed. Worth fixing before B.3 starts since research will heavily exercise the delete-bundle path.
