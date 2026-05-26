---
name: b1-complete
description: "B.1 garden handler — code-complete 2026-05-25. 259 ert tests (+20 from B.0's 239 baseline) + 13 Python integration fixtures (was 8) all green. Pipeline emits real content/garden/<slug>/index.md from org sources via a3-pub.sh --publish-living. Task 17 (real-corpus handover) gated on author annotating ~/org/notes/ with HUGO_PUBLISH + HUGO_SECTION keywords. Next slice = B.2 library handler."
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

14 dotfiles commits total. Site repo has 1 commit (`6561504`) for the integration fixtures + pending commits for the plan file, CLAUDE.md update, and this memory snapshot.

## Architectural decisions worth recording

1. **Link rewriting is deferred to B.1.x.** A.1's `rewrite-link` operates on raw org `[[id:UUID]]` bracket syntax; ox-hugo already translates those during markdown export, so the post-export `:body` has no `[[...]]` patterns left. Resolution needs either pre-export buffer rewriting (new helper + tmp-buffer dance) or `org-link-set-parameters` hooks. Deferred — Task 17 spot-check will reveal what ox-hugo actually emits for internal links, then a follow-on lands the right approach.

2. **`flavor` is NOT emitted to YAML frontmatter** (contrary to the B parent spec §7). The linter derives it from media_type internally; CLAUDE.md's frontmatter contract confirms. B design spec at `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` §7 needs a one-line correction.

3. **YAML date rendering is unquoted** so PyYAML loads as `datetime.date` (matches hand-authored fixtures + linter's `isinstance(val, date)` check). `render-yaml-value` detects `^YYYY-MM-DD$` strings and emits them without quotes.

4. **`SITE_DATA_DIR` cascade** is env > git rev-parse > hard-error. Auto-detect from `$PWD` (`git rev-parse --show-toplevel`) is the normal-workflow path; env override for CI/test corpora; hard-error keeps surprising silent-misroutes from happening.

5. **`note-section` returns a string, dispatch keys by symbol.** B.0 had a latent `(eq 'garden "garden")` bug that would never match. Fixed in `walk-section` via `symbol-name` conversion (preserves the symbol-keyed alist registration pattern).

## Known issues / B.1.x follow-ups (must address before Task 17 fully ships)

1. **Link rewriting stub** (per Architectural Decision 1). The first real-corpus garden note with `[[id:UUID]]` internal links will show ox-hugo's default translation, which probably points at the wrong URL. Surface via spot-check, then ship the right fix.

2. **`last_modified` is file mtime, not git mtime.** Spec §7 + §12 open-Q-5 want git-mtime-of-HEAD-touching-file. File mtime is unstable across `touch` or editor saves with no content change. Acceptable for first-cut but needs replacing for true idempotency. Follow-up task should switch to `(shell-command-to-string "git log -1 --format=%cI -- <file>")` + Date parse.

3. **B design spec correction.** Drop the "flavor is emitted" sentence in §7.

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
