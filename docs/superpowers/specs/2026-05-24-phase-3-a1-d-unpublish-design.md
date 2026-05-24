# Phase 3 sub-project A.1.d: unpublish flow + integration — design

**Date:** 2026-05-24
**Status:** brainstormed; plan pending
**Phase fit:** Phase 3, sub-project **A**, slice **A.1.d** (fifth and final of A.1 sequence: A.1.0 bootstrap → A.1.a foundations → A.1.b link rewriter → A.1.c asset handling → **A.1.d unpublish + integration**).
**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §8 (URL-history manifest) + §9 (unpublish flow) + §10 (A → B interface) + §11 (testing strategy) + §12 (A.1 vs A.2 scope split, item #7).
**Session policy:** no commits between sessions — author reviews + commits manually.

## 1 — Goals

Close parent spec §12 A.1 item #7 ("Unpublish flow + `--check-orphans` preview flag") by shipping the orchestrator that runs after a publish to:

1. **Diff** the new published-set against the URL-history manifest's current `live + draft` entries.
2. **Delete** Hugo page bundles for notes no longer published; mutate manifest with `state: removed` + `reason: removed` event.
3. **Sync slug shifts** — for `title_change`/`slug_override` events recorded during this publish, rename `~/org/notes/assets/page/<old-slug>/` → `<new-slug>/` and bulk-rewrite source `.org` link references (carry-forward #2 from A.1.c).
4. **Re-link-check** — for each currently-live note, scan outgoing org links; WARN for any link resolving into the removed-this-publish set.
5. Expose a `--check-orphans` dry-run flag on `a3-pub.sh` that runs steps 1–4 read-only.

This slice closes sub-project A.1. The next slice is sub-project **B** (per-content-type publisher + templates).

Also folds three additional carry-forwards from A.1.c:
- **#1**: `--asset-normalize-link-path` dedicated unit tests (3 ert tests).
- **#5**: CLAUDE.md CI step count off-by-2 (1-line edit).
- **Manifest schema bump**: add `republished` to the reason enum (parent spec §8 amendment).

## 2 — Non-goals (deferred or out of scope)

- **Sub-project B's per-content-type publisher.** A.1.d's `finish-publish` is callable by B but does not implement B. Until B ships, `finish-publish` runs in standalone mode (walks the source tree to compute the live-set).
- **Shared-asset conflict resolution** (carry-forward #3 from A.1.c) — needs its own design pass; today's "first publish wins" behavior is acceptable until friction surfaces.
- **`--strict` flag** (carry-forward #4 from A.1.c) — re-confirmed deferred to A.2 per parent spec §12.
- **Typed-backlinks** (A.2 item #1), **`:noexport:` subtree handling** (A.2 item #2), **`--gc-shared`** (A.2 item #4).
- **Heading-anchor URL history** — known caveat in parent spec §13 item #1; out of scope for A.1 entirely.
- **`removed-this-publish` persistence** — per-`finish-publish`-call value, not written anywhere. Next run computes fresh from diff.

## 3 — Carry-forward context

- **A.1.c shipped 2026-05-23/24** with 175 ert tests + 11 Python sibling tests + 4 Python integration fixtures. Wrapper `a3-pub.sh` loads `a3madkour-publish` + `a3madkour-publish-rewrite` + `a3madkour-publish-assets`. Live-site linter passes (`24 bundle(s)` verified).
- **URL-history manifest** today contains `notes: []` (empty seed from A.1.a). A.1.d's tests exercise it via fixtures; live-site behavior is steady-state (no published notes yet — that arrives with B).
- **`pub-history/record-publish`** already handles the 4-reason enum (`title_change | slug_override | section_change | removed`). A.1.d extends to 5 (adds `republished`) and adds the `state` flip-flop case (removed → live).
- **Wrapper-script lesson from A.1.c**: when a new top-level module is introduced, the plan must include "update `a3-pub.sh` load chain" as an explicit step within the introducing task. A.1.d's new module (`a3madkour-publish-unpublish.el`) follows this rule.

## 4 — `finish-publish` orchestrator overview

Single public entry point. Three sub-steps in fixed order. All sub-steps support dry-run mode (returns the would-do list without FS or manifest mutation).

```
(a3madkour-pub/finish-publish &key dry-run)
  ;; → (:removed (id ...)
  ;;    :slug-shifted ((old-slug . new-slug) ...)
  ;;    :orphan-warnings ("WARN: ..." ...))
```

**Step A** — Unpublish sweep: delete bundles, mutate manifest entries to `state: removed`, build `removed-this-publish-set`.
**Step B** — Slug-shift sync: rename asset dirs, bulk-rewrite source links.
**Step C** — Re-link-check: scan live notes' outgoing links against `removed-this-publish-set`, emit WARN list.

### Live-set computation: B-coupled accumulator + standalone fallback

`finish-publish` needs the "new live + draft set" to diff against. Two paths:

- **B-coupled**: B calls `record-publish` for each note it publishes. `record-publish` writes to manifest AND appends to an in-publish-run accumulator (`a3madkour-pub--publish-run-accumulator`, hash table id → (url . state)). `finish-publish` reads this accumulator first.
- **Standalone** (today, until B ships): `finish-publish` detects the accumulator is empty (no `record-publish` calls happened this run) and falls back to `walk-published-source-set` — walks `org-notes-dir`, parses each `.org` for `HUGO_PUBLISH:`/`HUGO_SECTION:`/`HUGO_DRAFT:` + derives URL via existing slug-derivation, returns the set.

`begin-publish` (existing) gets an extension: it resets the accumulator alongside the metadata cache.

## 5 — Step A: Unpublish sweep algorithm

```
1. new-set ← (or accumulator   ; B-coupled
                 walk-published-source-set)   ; standalone
2. manifest ← read-manifest
3. current-live-or-draft ← {id | id ∈ manifest, state ∈ {live, draft}}
4. diff ← diff-published-set new-set
       ;; → (:added :removed :stayed :slug-shifted)
       ;;    where :removed = current-live-or-draft \ keys(new-set)
       ;;    and :slug-shifted = {(id, old-url, new-url) | id ∈ stayed AND old-url ≠ new-url}
5. for each id in diff.removed:
     entry ← manifest-lookup id
     unless dry-run:
       (section, slug) ← parse-url-into-section-slug entry.current_url
       bundle-dir ← site-content-dir / section / slug /
       delete-directory bundle-dir (recursive) if exists
                          ;; missing dir = info log; not an error
       record-publish id nil 'removed
         ;; appends (url: prior, replaced_at: now, reason: removed)
         ;; sets state: removed, current_url: nil
6. removed-this-publish-set ← {id | id ∈ diff.removed}
7. return removed-this-publish-set
```

**Error cases:**

| Case | Behavior |
|---|---|
| Bundle dir doesn't exist (stale manifest) | Info log; mutate manifest anyway; not an error |
| `delete-directory` raises (permissions, file lock) | Propagate error; manifest NOT mutated for that id; aggregate into partial-failure WARN summary at orchestrator end |
| Two ids in manifest derive to the same `current_url` | Error, abort Step A. Pre-A.1.b invariant violation; should not happen but defensive |
| `current_url` nil for an id in `current-live-or-draft` | Error, abort. State inconsistency |

## 6 — Step B: Slug-shift sync algorithm

```
1. shifts ← diff.slug-shifted from Step A
       ;; format: ((id old-url new-url) ...)
2. for each (id, old-url, new-url):
     old-slug ← path-last-segment old-url
     new-slug ← path-last-segment new-url
     old-asset-dir ← ~/org/notes/assets/page/<old-slug>/
     new-asset-dir ← ~/org/notes/assets/page/<new-slug>/
     unless dry-run:
       if old-asset-dir exists:
         if new-asset-dir exists:
           error: "target dir conflict for slug shift <old-slug>→<new-slug>; skipping"
           continue   ; aggregate WARN, don't abort
         if git-tracked old-asset-dir:
           git mv old-asset-dir new-asset-dir
         else:
           rename-file old-asset-dir new-asset-dir
       bulk-rewrite-source-links old-slug new-slug
         ;; walks all .org under org-notes-dir; substitutes
         ;; in-text:
         ;;   ./assets/page/<old-slug>/...    →  ./assets/page/<new-slug>/...
         ;;   ~/org/notes/assets/page/<old-slug>/...   →  ...<new-slug>/...
         ;;   (and the expanded-home absolute form)
         ;; idempotent: re-running after partial completion is safe
3. return ((old-slug . new-slug) ...)
```

**Error cases:**

| Case | Behavior |
|---|---|
| `new-asset-dir` already exists | WARN, skip this shift; continue to next |
| Source `.org` file unwritable during bulk rewrite | WARN naming the file; continue with other files |
| `old-asset-dir` doesn't exist | Silent skip (note had no per-page assets) |
| `git mv` fails (not a git repo, or `git` not on PATH) | Fall back to `rename-file`; emit info log |

**Crash window:** if Step B aborts mid-rename (e.g., `git mv` succeeds for assets but `.org` rewrite crashes), the source tree is mid-migration. The bulk rewrite is idempotent (re-runs are no-ops once paths are migrated), so re-running `finish-publish` recovers.

**Coupling to Step A:** Step B reads `diff.slug-shifted` computed by Step A. Independent fallback (history-event scan with `replaced_at >= publish-start-time`) is NOT implemented in A.1.d — adds complexity without coverage benefit.

## 7 — Step C: Re-link-check algorithm

```
1. live-ids ← {id | id ∈ manifest (post Step A), state = 'live}
2. warnings ← ()
3. for each id in live-ids:
     source-file ← org-roam-id-find id
     unless source-file readable:
       push WARN "live note <id> source file unreadable"; continue
     for each org-link in parse-outgoing-links(source-file):
       target-id ← resolve-link org-link
                       ;; id: scheme → direct
                       ;; file: scheme → org-roam lookup
       if target-id ∈ removed-this-publish-set:
         old-url ← (manifest-lookup target-id).current_url  ;; nil after Step A
                   OR previous current_url from history     ;; preferred for the message
         push WARN format:
           "live note %s (%s) outgoing link to %s (was %s) — republish recommended"
           id (manifest-lookup id).current_url target-id old-url
4. return warnings
```

**Error cases:**

| Case | Behavior |
|---|---|
| Source `.org` unparseable | WARN naming the file; continue |
| org-roam ID resolution returns nil for a file-link target | Skip (no inert WARN here — rewrite-link's `:inert` path handles render time) |
| `removed-this-publish-set` is empty | Step C returns empty WARN list (common steady-state case) |

**Performance**: live site worst-case ~200 notes, each with up to ~10 outgoing links → ~2000 hash lookups + 200 file reads. Acceptable. No caching for A.1.d.

**Important note on semantics:** Step C only WARNs. It does NOT re-rewrite the published HTML files. Those still reflect the last publish output. Re-running `finish-publish` produces no new state until the author either:

- Migrates the source link AND republishes the live note via B, OR
- Re-adds the removed target to the published-set.

The WARN exists so the author knows republish is needed; it's not a self-healing mechanism.

## 8 — API surface (new + amended)

**New public functions** (in `a3madkour-publish-unpublish.el`):

```elisp
(a3madkour-pub/finish-publish &key dry-run)
  ;; Orchestrator. Returns plist:
  ;;   :removed         (id ...)
  ;;   :slug-shifted    ((old-slug . new-slug) ...)
  ;;   :orphan-warnings ("WARN: ..." ...)
  ;;   :partial-failures ("ERR: ..." ...)  ;; when present

(a3madkour-pub/check-orphans)
  ;; Thin alias for (finish-publish :dry-run t).
  ;; Exists because parent spec §10 named it.

(a3madkour-pub/diff-published-set new-set)
  ;; Pure. NEW-SET is a hash table id → (url . state).
  ;; Returns plist:
  ;;   :added         (id ...)
  ;;   :removed       (id ...)
  ;;   :stayed        (id ...)
  ;;   :slug-shifted  ((id old-url new-url) ...)

(a3madkour-pub/walk-published-source-set)
  ;; Walks `a3madkour-pub/org-notes-dir`, parses each .org for keywords,
  ;; derives slug + URL, returns hash table id → (url . state).
  ;; Used by finish-publish in standalone mode.
```

**New internal helpers** (in `a3madkour-publish-unpublish.el`):

```elisp
(a3madkour-pub--unpublish-delete-bundle section slug)
(a3madkour-pub--unpublish-rename-asset-dir old-slug new-slug)
(a3madkour-pub--unpublish-bulk-rewrite-source-links old-slug new-slug)
(a3madkour-pub--unpublish-recheck-live-note-links removed-this-publish-set)
```

**Amended existing** (extends shipped code):

```elisp
;; a3madkour-publish.el
(a3madkour-pub/begin-publish)
  ;; Existing: resets metadata cache + syncs org-roam DB.
  ;; A.1.d adds: resets a3madkour-pub--publish-run-accumulator.

(defvar a3madkour-pub--publish-run-accumulator)
  ;; New. Hash table id → (url . state). Populated by record-publish.

;; a3madkour-publish-history.el
(a3madkour-pub-history/record-publish id new-url state &key had-slug-override-p)
  ;; Existing: writes manifest, derives reason from 4-value enum.
  ;; A.1.d extends:
  ;;   - 5th reason value: 'republished
  ;;   - removed → live transition: appends republished event, flips state
  ;;   - all calls: append to a3madkour-pub--publish-run-accumulator
```

## 9 — Manifest schema delta

`data/url-history.yaml` reason enum extends from 4 → 5 values:

```yaml
# Before (parent spec §8):
reason: title_change | slug_override | section_change | removed

# After (A.1.d):
reason: title_change | slug_override | section_change | removed | republished
```

The leading comment block in `data/url-history.yaml` gets the new value listed. The seed file (`notes: []`) is unchanged.

**Parent spec §8 amendment:** A.1.d's plan includes a final task to amend the parent spec (`docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md`) §8's reason enum from 4 → 5 values. Same commit cadence as the A.1.b carry-forward resolutions (separate `docs(phase-3)` commit ahead of the implementation commit).

**No other manifest shape changes.** The `state: live | draft | removed` enum is unchanged (no `republished` state — that's an event, not a state).

## 10 — CLI surface: `--check-orphans` flag

`a3-pub.sh` intercepts `--check-orphans` BEFORE `exec emacs`:

```bash
# Pseudo-shell logic (refined at plan time):
if [[ "${1:-}" == "--check-orphans" ]]; then
  shift
  exec emacs --batch \
    [existing straight bootstrap + -l flags] \
    --eval '(progn
              (a3madkour-pub/begin-publish)
              (let ((result (a3madkour-pub/check-orphans)))
                (princ (format "removed: %S\n" (plist-get result :removed)))
                (princ (format "slug-shifted: %S\n" (plist-get result :slug-shifted)))
                (princ (format "orphan-warnings:\n"))
                (dolist (w (plist-get result :orphan-warnings))
                  (princ (format "  %s\n" w)))))' \
    "$@"
fi
```

**Exit code:** 0 always. `--check-orphans` is an info command; non-zero would conflate with a publish failure.

**Output format:** stderr-text (no structured JSON/yaml in A.1.d). Author reads visually; downstream tooling can be added later if needed.

**Usage:**
```
./a3-pub.sh --check-orphans
# → removed: (uuid1 uuid2)
#   slug-shifted: ((old-foo . new-foo))
#   orphan-warnings:
#     WARN: live note uuid3 (/garden/x/) outgoing link to uuid1 (was /garden/y/) — republish recommended
```

## 11 — Testing strategy

### Layer 1 — Elisp ert unit tests

New file `a3madkour-publish-unpublish-test.el` + extensions to existing test files. Approximate counts:

| Target | Tests |
|---|---|
| `diff-published-set` (pure) | 6 |
| `walk-published-source-set` | 4 |
| `unpublish--delete-bundle` | 3 |
| `unpublish--rename-asset-dir` | 4 |
| `unpublish--bulk-rewrite-source-links` | 5 |
| `unpublish--recheck-live-note-links` | 4 |
| `finish-publish` orchestrator | 6 |
| `check-orphans` thin alias | 1 |
| `pub-history/record-publish` republished path (extension) | 3 |
| `--asset-normalize-link-path` (carry-forward #1, extension to publish-assets-test.el) | 3 |
| **Subtotal** | **~39 new** |

Brings total from 175 → ~214.

### Layer 2 — Python integration fixtures

Extensions to `tools/test_publish_integration.py` (A.1.c shipped 4 fixtures). A.1.d adds 4:

| Fixture | Verifies |
|---|---|
| `unpublish_removed_note` | publish → remove `HUGO_PUBLISH:` from one note → re-publish → bundle deleted, manifest entry has `state: removed` + `reason: removed` event |
| `slug_shift_renames_assets` | publish note with `assets/page/foo/x.png` → add `#+HUGO_SLUG: foo-v2` → re-publish → `assets/page/foo-v2/x.png` exists, source `.org` link rewritten, history has `slug_override` event |
| `republish_after_removal` | publish → unpublish → republish → history shows `removed` then `republished` events; aliases include the prior URL |
| `link_into_removed_target_warns` | publish two notes A→B → unpublish B → re-publish → captured WARN cites A's outgoing link into B |

Brings total from 4 → 8 fixtures.

### Layer 3 — Python linter sibling

No new linter pair in A.1.d. The 24th (`check_org_assets.py`) shipped in A.1.c; A.1.d does not introduce a 25th. CI step count stays at the post-A.1.c value.

### Layer 4 — Manual verification checkpoints

Per parent spec §11 cadence: each plan stage gets a labeled checkpoint with seed-corpus + expected diff. Same pattern as A.1.b/A.1.c. Final 6-step user-verification at slice end (re-runnable from the plan).

### Live-site smoke test at slice end

```bash
./a3-pub.sh --check-orphans
# Expect steady state:
#   removed: nil
#   slug-shifted: nil
#   orphan-warnings: nil
```

Because the live site's `url-history.yaml` is `notes: []`, the diff produces empty results — but the command must exit 0 cleanly.

## 12 — File inventory

**Dotfiles repo** (`~/dotfiles/emacs-configs/custom/lisp/`):

- NEW: `a3madkour-publish-unpublish.el` (~350-450 lines) — orchestrator + helpers
- NEW: `a3madkour-publish-unpublish-test.el` (~600-750 lines) — ert tests
- MODIFIED: `a3madkour-publish.el` — add `a3madkour-pub--publish-run-accumulator` defvar; extend `begin-publish` to reset it
- MODIFIED: `a3madkour-publish-test.el` — extend `begin-publish` test for accumulator reset
- MODIFIED: `a3madkour-publish-history.el` — extend `record-publish` to handle 5th reason + removed→live transition + accumulator append
- MODIFIED: `a3madkour-publish-history-test.el` — 3 new tests for republished path
- MODIFIED: `a3madkour-publish-assets-test.el` — 3 new tests for `--asset-normalize-link-path` (carry-forward #1)
- MODIFIED: `a3-pub.sh` — add `-l a3madkour-publish-unpublish`; add `--check-orphans` intercept

**Site repo:**

- MODIFIED: `tools/test_publish_integration.py` — 4 new integration fixtures
- MODIFIED: `data/url-history.yaml` — updated leading comment block listing 5-value reason enum (data unchanged)
- MODIFIED: `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` — amend §8 reason enum 4 → 5 (separate `docs(phase-3)` commit ahead of implementation)
- MODIFIED: `CLAUDE.md` — pre-existing CI step count off-by-2 fix (carry-forward #5)

No new linter pair. No `.github/workflows/hugo.yaml` changes. No `tools/ci-local.sh` changes.

## 13 — Commit layout (suggested; refined at writing-plans time)

1. **Site doc** — `docs(phase-3): A.1.d parent-spec amendments — republished reason enum`. Amends parent spec §8 reason enum from 4 → 5 values.
2. **Site doc** — `docs(phase-3): A.1.d design — unpublish flow + integration`. This file.
3. **Site doc** — `docs(phase-3): A.1.d implementation plan — unpublish flow`. Plan file.
4. **Dotfiles impl** — `A.1.d implementation` (one commit, like A.1.c). Contains all 8 dotfiles changes.
5. **Site impl** — `A.1.d implementation`. Contains 3 site changes: integration fixtures (`tools/test_publish_integration.py`), url-history reason-enum comment (`data/url-history.yaml`), and the CLAUDE.md CI-step fix (carry-forward #5). The parent-spec §8 amendment is already covered by commit #1.

Same cadence as A.1.c. Author commits each manually per the no-commit session policy.

## 14 — Open carry-forwards for A.2 / future

Items NOT closed by A.1.d that remain queued:

- **Carry-forward #3** (from A.1.c): Shared-asset conflict resolution. Today: first publish wins; subsequent notes get `(missing asset: …)` + WARN. Future design pass.
- **Carry-forward #4** (from A.1.c): `--strict` flag. Deferred to A.2.
- **A.2 item #1**: Typed-backlinks data computation.
- **A.2 item #2**: `:noexport:` subtree handling inside the link rewriter.
- **A.2 item #4**: `--gc-shared` flag for cleaning orphan shared assets.
- **Parent spec §13 item #1**: Heading-anchor URL history (renaming a heading = potential deep-link rot). Acknowledged caveat.
- **Slug-shift bundle URL rewrite in HTML**: A.1.d renames source assets + rewrites source `.org` links. It does NOT rewrite published HTML files referencing the old asset URL — those self-correct when B republishes the affected notes. Step C's WARN flags this for the author.

These move A → "complete" after A.1.d ships. A.2 stays queued; sub-project B is next per CLAUDE.md sequencing.

## 15 — Cross-references

- **Parent spec**: `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §§ 8, 9, 10, 11, 12.
- **A.1.a foundations**: `docs/superpowers/plans/2026-05-20-phase-3-a1-a-foundations.md` (history module + url-history.yaml seed).
- **A.1.b link rewriter**: `docs/superpowers/specs/2026-05-20-phase-3-a1-b-link-rewriter-design.md` + plan.
- **A.1.c asset handling**: `docs/superpowers/specs/2026-05-23-phase-3-a1-c-asset-handling-design.md` + plan (carry-forwards #1, #2, #3, #4, #5 originate here).
- **Memory entries** (project): `next-slice` (this is the slice it points at), `a1c-complete`, `a1b-complete`, `a1a-foundations-slice`, `phase-3-decomposition`.
- **Memory entries** (reference): `org-roam-id-find-returns-cons` (Step C uses `org-roam-id-find`; result unwrap required).
- **Memory entries** (feedback): `plan-wrapper-script-updates` (wrapper-script lesson applied in §3).

## Spec self-review checklist (per superpowers:brainstorming)

- [ ] **Placeholder scan** — no "TBD", "TODO", or vague-but-unfilled sections.
- [ ] **Internal consistency** — Step A's `removed-this-publish-set` is consumed by Step C; Step B's `slug-shifted` shape matches `diff-published-set`'s return; API names in §8 match references throughout.
- [ ] **Scope check** — single implementation plan; carry-forwards #1, #2, #5 explicitly folded in; #3, #4 explicitly deferred.
- [ ] **Ambiguity check** — `removed-this-publish-set` lifetime defined (per-call, not persisted); `--check-orphans` exit code defined (always 0); standalone vs B-coupled live-set computation explicit; Step C only WARNs (does not rewrite HTML).

To be run after writing — fix inline, no separate re-review.
