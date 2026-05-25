---
name: b0-complete
description: "B.0 shared publisher infrastructure slice — implementation complete. 4 new dotfiles modules + 4 sibling tests + a3-pub.sh 2 flag intercepts + manifest snapshot fix (5 tasks) + bonus Task 0 (org-roam-db-sync gate). 239 ert tests passing (+16 from A.1.d 223 baseline). Site CLAUDE.md status updated + pushed as `5ded581`. Next slice = B.1 garden handler."
metadata: 
  node_type: memory
  type: project
  originSessionId: 240f0465-31c7-4fcc-86e7-eaa6fa0a2727
---

**Shipped (2026-05-25)**: B.0 — shared publisher infrastructure per `docs/superpowers/plans/2026-05-24-phase-3-b-0-shared-infra.md` (15 tasks + 1 added "Task 0" for org-roam-db-sync gate). Subagent-driven execution; per-task implementer + spec reviewer + code-quality reviewer.

## Test counts at slice end

- **ert: 239 total** (223 A.1.d baseline + 16 B.0 new). All passing, 0 unexpected.
  - Task 0 (added): +2 (org-roam-db-sync gate skip + call paths).
  - Tasks 1-5 (Stage 1: manifest snapshot fix): +6 (defvar exists, begin-publish populates, helper prefers-snapshot, helper falls-back, finish-publish clears, regression slug-shift-detection).
  - Tasks 6-9 (Stages 2-5: new modules): +8 (export plist-shape, frontmatter returns-alist + accepts-all-13 + errors-unknown, living defined+interactive + empty-handler-lifecycle, deliberate defined+interactive + unknown-section-errors).
- **Python linter pairs**: unchanged (24); B.0 emits no content.
- **Python integration fixtures**: unchanged (8); B.1 will start growing this.

## Dotfiles state — staged + unstaged inventory

**STAGED (11 files)** — Tasks 4-12 work:
- `a3-pub.sh` — +87 lines (Tasks 10+11+12: 4 new module loads in default exec + 2 new flag intercepts with `SITE_DATA_DIR` env-default workaround)
- `a3madkour-publish-export.el` + sibling test (Task 6 — new)
- `a3madkour-publish-frontmatter.el` + sibling test (Task 7 — new)
- `a3madkour-publish-living.el` + sibling test (Task 8 — new)
- `a3madkour-publish-deliberate.el` + sibling test (Task 9 — new)
- `a3madkour-publish-unpublish.el` (Tasks 3-4: diff-published-set call switch + finish-publish snapshot clear)
- `a3madkour-publish-unpublish-test.el` (Tasks 4-5: 2 new B.0 tests)

**UNSTAGED — working tree modifications (4 files)** — Tasks 0-3 work the user unstaged mid-session:
- `a3madkour-publish.el` — Tasks 0+1+2 (org-roam-db-sync gate + manifest-snapshot defvar + begin-publish populates snapshot)
- `a3madkour-publish-test.el` — Tasks 0+1+2 (2 org-roam gate tests + defvar-exists test + snapshot-populates test + 3 stub mods to pre-existing tests)
- `a3madkour-publish-history.el` — Task 3 (forward-decl defvar + read-manifest-snapshot-or-disk helper)
- `a3madkour-publish-history-test.el` — Task 3 (2 helper tests)

**To commit all B.0 dotfiles work, author needs**:
```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/{a3madkour-publish.el,a3madkour-publish-test.el,a3madkour-publish-history.el,a3madkour-publish-history-test.el}
# (11 staged files already in index)
git commit -m "feat(b-0): shared publisher infrastructure"
```

## Site state

- `CLAUDE.md` status pointer updated + pushed (commit `5ded581`).
- No content/data/template changes (B.0 emits nothing).

## Architectural artifacts verified

- **B-coupling regression test** in `-unpublish-test.el` proves snapshot fix works end-to-end (record-publish mid-publish → diff-published-set still detects slug shift).
- **Lifecycle proof**: Task 4 implementer hit a real-world demonstration of the bug being fixed — without the snapshot clear, 10 unrelated tests poisoned each other via leaked snapshot. The 3-line clear resolved all 11 failures atomically.
- **Wrapper smoke tests green** (after Task 0's org-roam-db-sync gate):
  - `a3-pub.sh --eval` (default exec): exit 0
  - `a3-pub.sh --publish-living`: exit 0, silent (empty handler set)
  - `a3-pub.sh --publish-deliberate` (no arg): exit 2, missing-arg stderr
  - `a3-pub.sh --publish-deliberate <unhandled-section>`: exit 1, clean ERROR

## Known issues / B.1+ follow-ups

1. **`SITE_DATA_DIR` default path is wrong for this machine**: `--publish-living` and `--publish-deliberate` default `SITE_DATA_DIR="${A3_PUB_SITE_DATA_DIR:-$HOME/Workspace/a3madkour.github.io/data/}"`. Matches the defcustom docstring example but doesn't match this machine's real repo at `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/`. Smoke tests passed only because `read-manifest` returns empty manifest when file is missing (no crash, just no slug-shift detection). For B.1+ when real handlers run, either fix the default (e.g., git rev-parse from $PWD) or require `A3_PUB_SITE_DATA_DIR` to be set.

2. **Pre-existing latent bug in `--check-orphans`**: same `site-data-dir` defaulting gap as the two new intercepts had. The two B.0 intercepts now have the `SITE_DATA_DIR` workaround; `--check-orphans` does not. Worth back-porting the same pattern, or factoring out a shared helper.

3. **Cross-task staging conflation**: with stage-only policy + multiple tasks, each subagent reviewer sees the cumulative staged diff and may flag prior-task work as scope creep. Worked around by explicitly noting "Task N deltas only" in each reviewer prompt with file:line ranges. Future slices should consider per-task commits (then squash) instead, OR use snapshot SHAs for cleaner diffs.

4. **Deferred: stub-literal extraction**: `'((notes . []))` is duplicated as a `read-manifest` stub in ~4 test bodies. Quality reviewer suggested extracting `defconst a3madkour-pub-test--empty-manifest`. Defer to B.1+ as Stage 1 cleanup if more callers need it.

## Next slice: B.1 (garden handler)

Per design spec §12 slice ordering, B.1 should:
- Create `a3madkour-publish-garden.el` + sibling test.
- Register `(garden . a3madkour-pub-garden/publish-garden-file)` in `a3madkour-pub-living--handlers`.
- Fill in `frontmatter/normalize` garden branch with growth_stage derivation + flavor inference + topic_map pass-through.
- Wire link-rewriter + asset-copy into the garden handler.
- Add 3-4 new integration fixtures under `tools/test_publish_integration.py`.
- First slice to emit real Hugo content; transition garden fixtures per design spec §11.
- ALSO: address SITE_DATA_DIR default issue + back-port to --check-orphans (see Known Issues #1 + #2).

## Cross-references

- Parent spec: `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md`
- B.0 plan: `docs/superpowers/plans/2026-05-24-phase-3-b-0-shared-infra.md`
- Prior slice memory: [[a1d-complete]]
- Decomposition context: [[phase-3-decomposition]]
- Architectural finding referenced: [[a1d-complete]] "Architectural findings" (B-coupling fix rationale)
