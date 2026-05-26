---
name: b1-complete
description: "B.1 garden handler — shipped 2026-05-25. 260 ert tests (+21 from B.0's 239 baseline) + 13 Python integration fixtures (was 8) all green. Pipeline emits real content/garden/<slug>/index.md from org sources via a3-pub.sh --publish-living. Task 17 spot-check shipped: 3 real notes annotated + bundles emitted + committed locally. lastmod-rename bug surfaced and fixed in same slice. Next slice = B.2 library handler."
metadata:
  node_type: memory
  type: project
---

**Shipped (code-complete 2026-05-25):** B.1 — garden per-content-type publisher per `docs/superpowers/plans/2026-05-25-phase-3-b-1-garden-handler.md`. Subagent-driven execution; controller absorbed two unplanned blockers (yaml-package + dispatch-symbol bugs) discovered during smoke tests.

## What ships in B.1

### Dotfiles (`~/dotfiles/emacs-configs/custom/lisp/`)

**New module:**
- `a3madkour-publish-garden.el` + `a3madkour-publish-garden-test.el` (7 tests) — `publish-garden-file` end-to-end handler. Pipeline: export-file → frontmatter/normalize 'garden → [link rewrite intentionally stubbed, see Known Issues] → asset-validate-and-copy → write-if-different → record-publish.

**Modified modules:**
- `a3-pub.sh` — `a3_pub_resolve_site_data_dir` cascade helper (env > git rev-parse > hard-error); env-branch existence check + trailing-slash normalize; `--check-orphans` block now plumbs `site-data-dir` through; `(straight-use-package 'yaml)` added everywhere `'org-roam` is registered; `-l a3madkour-publish-garden` wired into the three publish-side intercepts (NOT `--check-orphans`).
- `run-tests.sh` — `(straight-use-package 'yaml)` added.
- `a3madkour-publish-export.el` — real ox-hugo invocation (was B.0 skeleton). Buffer-emit via `org-hugo-export-as-md`, YAML frontmatter parsed via `yaml.el` into symbol-keyed alist, `unwind-protect` cleanup of both source + export buffers, `condition-case` around yaml-parse with filename context. `--frontmatter-string-to-alist` + `--split-frontmatter` helpers. Signature aligned to spec §10 (dropped `dest-dir`).
- `a3madkour-publish-frontmatter.el` — per-section dispatch refactor; full garden normalizer: growth_stage from `:PROGRESS:` (highlighting/ref-notes/main-notes/done/unset → seedling/budding/evergreen/evergreen/seedling); HUGO_GROWTH_STAGE override; media_type pass-through; topic_map string-or-list → list-of-slugs (or no-key when missing); year/weight string→int coerce; **strips `author` (ox-hugo adds it, linter rejects on concept notes)**; **derives `last_modified` from file mtime in YYYY-MM-DD when not provided** (git-mtime is the §7 §12 open-Q-5 target follow-up).
- `a3madkour-publish-living.el` — `with-eval-after-load 'a3madkour-publish-garden` registers `(garden . publish-garden-file)` in `--handlers`. `walk-section` now compares `(symbol-name section)` to `note-section`'s string return (fixed latent B.0 dispatch bug — would never have matched on bare `(eq ...)`).
- `a3madkour-publish-unpublish.el` — `finish-publish` Step B now calls `--unpublish-delete-bundle` for the OLD section/slug after the asset-dir rename (was leaving stale `content/<section>/<old-slug>/` bundles around when titles changed).

### Site repo

- `tools/test_publish_integration.py` — 5 new fixtures under `TestGardenPublishLiving`: `_publish_living`/`_write_garden_source`/`_import_linter` helpers; `test_garden_publish_once` / `test_garden_publish_idempotent` / `test_garden_slug_shift` / `test_garden_removed_note_unpublish` / `test_garden_emits_lint_clean_output`. The linter-parity fixture imports `check_garden_fixtures.run()` + `check_garden_links.run()` in-process and asserts rc == 0 against B-emitted output.
- `docs/superpowers/plans/2026-05-25-phase-3-b-1-garden-handler.md` — 17-task implementation plan.
- `CLAUDE.md` — Phase 3 sub-project bullet updated.

## Test counts at slice end

- **ert: 259 total** (B.0 baseline 239 + 20 new across export, frontmatter, garden, living, unpublish). All passing, 0 unexpected.
- **Python integration fixtures: 13 total** (A.1.d baseline 8 + 5 new B.1 fixtures). All passing.
- **Site linters (`check_garden_fixtures.py` + `check_garden_links.py`)**: green against current site (still fixture content); rc == 0 against B-emitted output in tmp dirs (via the linter-parity integration fixture).

## Commits

In dotfiles repo:
- `b8f76d4` SITE_DATA_DIR cascade + --check-orphans back-port
- `3c25911` straight-use-package 'yaml everywhere (B.0 packaging gap discovered)
- `a62ff0d` env-branch existence check + trailing-slash normalize
- `b5b19f2` align export-file signature with spec §10
- `1ac8bc0` real ox-hugo invocation in export-file
- `b2115c6` export-file resource hygiene + error context (unwind-protect, source-buffer cleanup, yaml-parse context)
- `740a013` per-section dispatch in frontmatter/normalize
- `f78d8f6` garden growth_stage derivation
- `11da3d5` garden media_type+flavor, topic_map, per-keyword pass-throughs (Tasks 6-8 batched)
- `6ad1e0d` scaffold a3madkour-publish-garden module + wrapper -l line
- `527795a` publish-garden-file end-to-end
- `6b1a834` register garden handler in living--handlers + fix dispatch symbol/string bug
- `21cc568` garden frontmatter hygiene (strip flavor/author + add last_modified)
- `a7e1100` finish-publish Step B deletes orphan content bundle on slug shift
- `8583feb` rename ox-hugo's `lastmod` → `last_modified` (Task 17 spot-check finding)

15 dotfiles commits total. Site repo has 3 commits: `6561504` integration fixtures + `2186366` plan/status/memory docs + a third with the Task 17 spot-check content (3 B-emitted bundles + manifest update + this memory update). Site commits are local only — not pushed pending author review.

## Architectural decisions worth recording

1. **Link rewriting is deferred to B.1.x.** A.1's `rewrite-link` operates on raw org `[[id:UUID]]` bracket syntax; ox-hugo already translates those during markdown export, so the post-export `:body` has no `[[...]]` patterns left. Resolution needs either pre-export buffer rewriting (new helper + tmp-buffer dance) or `org-link-set-parameters` hooks. Deferred — Task 17 spot-check will reveal what ox-hugo actually emits for internal links, then a follow-on lands the right approach.

2. **`flavor` is NOT emitted to YAML frontmatter** (contrary to the B parent spec §7). The linter derives it from media_type internally; CLAUDE.md's frontmatter contract confirms. B design spec at `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` §7 needs a one-line correction.

3. **YAML date rendering is unquoted** so PyYAML loads as `datetime.date` (matches hand-authored fixtures + linter's `isinstance(val, date)` check). `render-yaml-value` detects `^YYYY-MM-DD$` strings and emits them without quotes.

4. **`SITE_DATA_DIR` cascade** is env > git rev-parse > hard-error. Auto-detect from `$PWD` (`git rev-parse --show-toplevel`) is the normal-workflow path; env override for CI/test corpora; hard-error keeps surprising silent-misroutes from happening.

5. **`note-section` returns a string, dispatch keys by symbol.** B.0 had a latent `(eq 'garden "garden")` bug that would never match. Fixed in `walk-section` via `symbol-name` conversion (preserves the symbol-keyed alist registration pattern).

## Spot-check (Task 17) findings

Author annotated 3 small notes (`bayesian_statistics`, `bias_vs_variance`, `cellular_automata_are_visual_rule_based_systems`) with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden` and ran `a3-pub.sh --publish-living` against the real site repo. Outcomes:

- All 3 bundles emitted cleanly under `content/garden/*/index.md`.
- Both garden linters (`check_garden_fixtures.py` + `check_garden_links.py`) accepted B-emitted output (after the `lastmod` rename fix landed mid-spot-check).
- `hugo --minify` built 118 pages clean (+3 from baseline).
- Existing fixture bundles (`emergence-vs-design`, `invisible-cities`, etc.) were NOT swept — `finish-publish`'s orphan sweep operates on the manifest, not on disk-vs-source diff. Safer than the spec's "sync" wording suggests; author manually removes fixtures when ready.
- None of the 3 annotated notes have internal `[[id:UUID]]` links, so the deferred link-rewriting question was NOT exercised. Stays as B.1.x follow-up #1.

One bug surfaced + fixed in same slice (dotfiles `8583feb`): ox-hugo emits `#+HUGO_LASTMOD:` as `lastmod:` (its own key), but the linter only accepts `last_modified:`. The normalizer now renames `lastmod` → `last_modified` with ISO-datetime truncation. 3-case regression test pins it.

## Spot-check round 2: link rewriting exercised (2026-05-25)

Annotated `maximum_a_posteriori.org` which has TWO id-links:
- `[[id:09049cd8-...][Bayesian Statistics]]` — target is annotated/published.
- `[[id:32a9dc40-...][Inference Queries]]` (twice) — target exists at `inference_queries.org` but is NOT annotated.

ox-hugo translates BOTH forms identically: `[text]({{< relref "<filename>.md" >}})`. So Hugo sees:
- `[Bayesian Statistics]({{< relref "bayesian_statistics.md" >}})`
- `[Inference Queries]({{< relref "inference_queries.md" >}})`

`hugo --minify` errors with 3× `REF_NOT_FOUND` (one per link):
```
ERROR [en] REF_NOT_FOUND: Ref "bayesian_statistics.md":
  "/.../content/garden/maximum-a-posteriori-map/index.md:12:66": page not found
```

Two reasons Hugo can't resolve the relref:
1. ox-hugo uses **underscore filenames** (`bayesian_statistics.md`) but B-emits **hyphen slugs** (`bayesian-statistics`). The Hugo bundle path is `content/garden/bayesian-statistics/index.md`, not `content/<anywhere>/bayesian_statistics.md`.
2. Even if the filename matched, unpublished targets (`inference_queries`) have no Hugo content at all.

Concrete fix paths for B.1.x:
- **Pre-export buffer rewrite** (preferred): copy source to a tmp buffer/file, scan for `[[id:UUID]]` patterns, apply `a3madkour-pub/rewrite-link` to each (it returns `:html` for resolved, `:inert` for unresolved). Hand the rewritten content to ox-hugo. ox-hugo passes inline HTML through markdown untouched.
- **Post-export string substitution**: scan markdown for `{{< relref "X.md" >}}`, resolve X to a note ID via org-roam, substitute with `/garden/<slug>/` or plaintext.
- **`org-link-set-parameters` hook**: register a custom `:export` function for `id:` and `file:` schemes that calls A.1's rewriter directly. Avoids the relref shortcode entirely.

Recommended: pre-export buffer rewrite. Reuses A.1's `rewrite-link` exactly as designed. Needs a small new helper (`rewrite-buffer-links`) that scans + applies.

## Spot-check round 2: ALSO surfaced a `site-content-dir` defcustom bug

`a3madkour-pub-site-content-dir` (A.1.d defcustom) defaulted to a hardcoded `~/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/content/` — the OTHER machine's path. The wrapper plumbs `site-data-dir` but never sets `site-content-dir`, so `unpublish-delete-bundle` silently failed to delete the orphan bundle when MAP was rolled back. Fixed in dotfiles `0825853` — defcustom default is now nil; a new `--site-content-dir-effective` helper derives content/ as the sibling of data/.

**Secondary finding**: `finish-publish`'s Step A does NOT retry a failed delete-bundle. If the path computation is wrong (as the site-content-dir bug caused), the manifest correctly marks `state: removed` but the actual on-disk bundle stays. Subsequent publish-living runs see "manifest already says removed → no diff to act on" and the orphan persists. Worth documenting as an A.1.d gap: failed delete-bundle should at least WARN loudly, ideally reattempt OR reset manifest state for retry.

## Known issues / B.1.x follow-ups

1. **Link rewriting** (per Architectural Decision 1 + round-2 findings above). The architectural call is now made: **pre-export buffer rewrite via a new `rewrite-buffer-links` helper**. Land this as B.1.1 before any further user spot-checks against linked notes.

2. **`last_modified` falls back to file mtime when no `#+HUGO_LASTMOD:` exists.** Spec §7 + §12 open-Q-5 want git-mtime-of-HEAD-touching-file. File mtime is unstable across `touch` or editor saves with no content change. Follow-up should switch to `(shell-command-to-string "git log -1 --format=%cI -- <file>")` + Date parse.

3. **B design spec correction.** Drop the "flavor is emitted" sentence in §7.

4. **No fixture-sweep on first real run** (behavior, not a bug). Authors who want to remove fixture bundles need to do it manually before/after the first publish-living. Documenting this in CLAUDE.md or the spec is worth a small follow-up.

## Next slice: B.2 (library handler)

Per design spec §12 slice ordering: B.1 → **B.2 (library)**. Library is the structural outlier — per-medium YAML rows (not per-page Hugo bundles), parsed from top-level org headings in 4 source files (`library-reading.org`, `library-listening.org`, `library-playing.org`, `library-watching.org`). See B parent spec §8 for the full pipeline.

## How to start the next session

1. **First, address B.1.x follow-ups** (link rewriting + git-mtime), then start B.2.
2. **OR proceed with B.2** if the author wants to validate B.1 by getting more sections live first; the follow-ups can land after the slice ships.
3. **OR pause B and tackle the user-driven Task 17 first**: author annotates `~/org/notes/` with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden`, runs `a3-pub.sh --publish-living`, eyeballs result.

## Cross-references

- Parent spec: `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md`
- B.1 plan: `docs/superpowers/plans/2026-05-25-phase-3-b-1-garden-handler.md`
- Prior slice: [[b0-complete]]
- Decomposition: [[phase-3-decomposition]]
