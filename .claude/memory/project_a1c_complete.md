---
name: a1c-complete
description: "A.1.c asset handling slice — implementation complete, all 6 user-verification steps green; 5 dotfiles + 6 site-repo files staged, awaiting author commit. Next: A.1.d (unpublish + integration)."
metadata: 
  node_type: memory
  type: project
  originSessionId: 7ef3bb18-9acf-451e-8f17-f5a28329110c
---

**State (2026-05-23/24):** A.1.c (asset handling + 24th linter pair + HTML-escape helper retrofit) **implementation-complete + verified**. 5 files staged in `~/dotfiles` + 6 files staged in site repo. Author commits between sessions per session policy. Suggested commit messages drafted in session transcript.

## What shipped

26 plan tasks executed via `superpowers:subagent-driven-development`. Test count progression: 109 (A.1.b end) → **175 ert** + **11 Python sibling** + **4 Python integration**. All passing. Linter passes on live site (24 bundles).

Per-stage summary:

| Stage | Tasks | What |
|---|---|---|
| 1 (escape retrofit) | 1-4 | `a3madkour-pub--html-escape` helper + retrofit 3 existing emit points (id-link / typed-link via inheritance / external) |
| 2 (asset core) | 5-9 | assets.el skeleton + defcustoms + path resolution + cross-namespace + bundle-dest + image-classification + emit-html + inert |
| 3 (auto-remediation) | 10-13 | SHA-1 content hash + dest+collision pure logic + do-move (git-mv-vs-mv-vs-dry-run) + org-source link rewrite |
| 4 (integration) | 14-19 | rewrite-asset-link dispatcher + auto-remediate integration + extract-asset-refs + cleanup-stale + asset-validate-and-copy + wire into rewrite-link (replace :pending-asset) |
| 5 (Python + CI) | 20-23 | check_org_assets.py + sibling test + CI registration + test_publish_integration.py (§11 placeholder finally lands) |
| Final | 24-26 | user-verification checkpoint + CLAUDE.md update + stage for author commit |

## Bug caught by user-verification (already fixed)

Plan Task 24 Step 5 spot-check surfaced that `a3-pub.sh` didn't `-l a3madkour-publish-assets`. The first spot-check call (`rewrite-asset-link`) worked via the autoload declaration in `a3madkour-publish-rewrite.el`, but `asset-validate-and-copy` had no autoload — emacs errored silently under `--batch`, bundle stayed empty.

Fix: added `-l a3madkour-publish-assets` to wrapper between existing `-l a3madkour-publish-rewrite` and the readiness `--eval`. Re-ran spot-check, asset now copies correctly. Wrapper change is in the staged dotfiles set.

**Lesson** (worth memorizing for future plans): when a slice adds a new top-level elisp module, the plan should include "update `a3-pub.sh` load chain" as an explicit step. The A.1.c plan didn't, but `run-tests.sh` happened to use auto-discovery so that side worked. Catch this in A.1.d brainstorm. See [[feedback-plan-wrapper-script-updates]].

## Intentional scope expansions (documented)

1. **`a3madkour-pub--asset-normalize-link-path`** (helper inside `asset-validate-and-copy`): treats `./assets/...` as a canonical-root alias rather than literal source-dir-relative. Improves nested-note layouts. Unit tests deferred to A.1.d.
2. **`check_org_assets.py` extraction scope**: beyond plan's `<img src>` + `<a href>` + markdown `![alt](src)`, also extracts Hugo shortcode `src/figure/image/href` attributes + frontmatter `hero:/image:/cover:` fields. Necessary to pass on the 24 existing live-site bundles.

## Final code-review findings (all addressed inline before staging)

- ✅ Important 1: `asset-validate-and-copy` docstring documents `"from-validate"` source-id caller contract.
- ✅ Important 2: `rewrite-asset-link` docstring lists the dry-run third return variant.
- ✅ Minor 2: Remediation test has a comment explaining canonical-asset-root tmpdir vs production.
- ⏭ Minor 1 (defer to A.1.d): No dedicated `--asset-normalize-link-path` unit tests.
- ⏭ Minor 3 (defer): CLAUDE.md CI step count off-by-2 (pre-existing).

## User-verification all green (2026-05-24 local)

| Step | Result |
|---|---|
| 1. `run-tests.sh` | 175/175 ✅ |
| 2. `test_check_org_assets.py` | 11/11 ✅ |
| 3. `test_publish_integration.py` | 4/4 ✅ |
| 4. `check_org_assets.py` live | 24 bundles OK ✅ |
| 5. Spot-check via `a3-pub.sh` | Asset copies into bundle ✅ (after wrapper fix) |
| 6. `hugo --minify` | 109 pages / 1.16s ✅ |

## Open items (carried forward to A.1.d)

1. **`--asset-normalize-link-path` unit tests.**
2. **Slug-shift asset directory rename.** Note slug `foo` → `foo-v2` should trigger `assets/page/foo/` → `assets/page/foo-v2/` rename + link rewrite in all source files. Hook into URL-history slug-change events.
3. **Shared-asset conflict resolution.** First-publish wins on out-of-root remediation; later notes that linked the same file get WARN. Could auto-suggest `assets/shared/` placement.
4. **`--strict` flag plumbing.** Still A.2 per parent spec §6 — confirm deferral at A.1.d brainstorm.

## What's next (per CLAUDE.md sequencing)

**A.1.d — unpublish flow + integration test expansion.** Walks all org files, diffs against URL-history's live/draft set, deletes removed-note bundles + records `reason: removed`, re-checks live notes' outgoing links (inert + WARN for links into removed-this-publish targets), ships `--check-orphans` preview flag. Plus the 4 A.1.c carry-forwards above.

After A.1.d: sub-project A complete. Then move to sub-project B (publisher + templates), then F (citations), C (validators), D (unified markup), E (explorables).

## Cross-references

- [[a1b-complete]] — A.1.b context
- [[next-slice]] — A.1.d entry pointer + agent-environment carry-forwards
- [[phase-3-decomposition]] — sub-project A→F mapping
- [[org-roam-id-find-returns-cons]] — API gotcha from A.1.b session
- [[phase-3-two-publish-commands]] — relevant when sub-project B starts
- [[phase-3-library-tag-shelves]] — B's library publisher round-trip rule
