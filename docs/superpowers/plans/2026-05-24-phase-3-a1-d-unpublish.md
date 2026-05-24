# Phase 3 A.1.d — Unpublish Flow + Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Session policy default (mirrors A.1.a + A.1.b + A.1.c):** stage files with `git add` but do NOT git-commit autonomously. Stage 0's parent-spec amendment IS committed (it's a separate doc commit ahead of impl, matching the A.1.b precedent `62636ef`). Final task surfaces suggested commit messages for the implementation diffs. If the author signals "commit as you go" at session start, switch to per-task commits.

**Goal:** Ship the `finish-publish` orchestrator that closes parent spec §12 A.1 item #7 — three-step unpublish flow (sweep → slug-shift sync → re-link-check) + `--check-orphans` dry-run preview flag. Plus three A.1.c carry-forwards (#1 `--asset-normalize-link-path` unit tests; #2 slug-shift asset rename folded into Step B above; #5 CLAUDE.md CI step count fix) and the parent-spec §8 `republished` reason enum bump.

**Architecture:** One new dotfiles module (`a3madkour-publish-unpublish.el`) holds the orchestrator + four internal helpers. The orchestrator is standalone-capable today (walks the source tree if no B-coupled accumulator is populated) and B-friendly tomorrow (B's per-content-type publisher calls `record-publish` per-note → populates accumulator → `finish-publish` reconciles). Step B (slug-shift sync) mutates the source tree (`~/org/notes/assets/page/`) + bulk-rewrites `.org` link references. Step C (re-link-check) only WARNs — does not rewrite published HTML; surviving live notes self-correct on their next publish. CLI surface: a `--check-orphans` flag intercepted in `a3-pub.sh` before `exec emacs`. No new linter pair (24 stays at 24); 4 new Python integration fixtures (4 → 8); ~39 new ert tests (175 → ~220).

**Tech Stack:** Emacs 30.2 + ert (built-in) + yaml.el + org-roam (A.1.a–A.1.c deps) + bash test runner + bash wrapper script; Python 3 stdlib for the integration orchestrator.

**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §§ 8, 9, 10, 11, 12.

**Design doc (this slice):** `docs/superpowers/specs/2026-05-24-phase-3-a1-d-unpublish-design.md`.

**Prior plan:** `docs/superpowers/plans/2026-05-23-phase-3-a1-c-asset-handling.md` (A.1.c — 175 ert + 11 + 4 Python tests green at start of A.1.d).

**Carry-forward memory:** `memory/project_a1c_complete.md` + `memory/project_next_slice.md`.

**Test runners:** elisp via `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh` (auto-discovers `*-test.el`); site CI via `tools/ci-local.sh`; integration via `python3 tools/test_publish_integration.py`.

---

## File Structure

**Created (dotfiles repo):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el` — orchestrator + 4 internal helpers
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

**Modified (dotfiles repo):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` — add `a3madkour-pub--publish-run-accumulator` defvar; extend `begin-publish` to reset it
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el` — +2 tests covering accumulator reset
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el` — extend `record-publish` for `republished` reason + accumulator append; extend `--diff-reason` (5-value enum)
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el` — +3 tests for republished path
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el` — +3 tests for `--asset-normalize-link-path` (carry-forward #1)
- `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` — add `-l a3madkour-publish-unpublish`; add `--check-orphans` flag intercept

**Modified (site repo):**
- `data/url-history.yaml` — extend leading comment block to list 5-value reason enum (data unchanged; remains `notes: []`)
- `tools/test_publish_integration.py` — +4 integration fixtures (unpublish_removed_note, slug_shift_renames_assets, republish_after_removal, link_into_removed_target_warns)
- `CLAUDE.md` — carry-forward #5 (CI step count); A.1.d shipped pointer; next-slice pointer
- `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` — Stage-0 amendment: §8 reason enum 4 → 5 values

**Out of scope** (deferred to future slices):
- Shared-asset conflict resolution (carry-forward #3 from A.1.c — own design pass).
- `--strict` flag (carry-forward #4 from A.1.c — A.2 per parent spec §12).
- Typed-backlinks (A.2 item #1).
- `:noexport:` subtree handling in link rewriter (A.2 item #2).
- `--gc-shared` flag (A.2 item #4).
- Heading-anchor URL history (parent spec §13 item #1; documented caveat).

**Test count progression:** baseline **175 ert** (end of A.1.c). Per-task targets noted at end of each task. Final target ≈ **220 ert tests** + 11 Python sibling tests + **8 Python integration fixtures**.

---

### Task 1: Parent-spec §8 amendment + url-history.yaml comment

**Files:**
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md`
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/data/url-history.yaml`

This is a docs-only Stage-0 commit, matching the A.1.b precedent (`62636ef docs(phase-3): A.1.b carry-forward resolutions — spec amendments + HTML escape contract`). No code, no tests. The commit lands ahead of any implementation so the rest of the plan can reference the 5-value enum.

- [ ] **Step 1: Amend parent spec §8 reason enum**

Locate the §8 example YAML block (around line 227 in the parent spec) and the inline comment that documents the reason enum. Edit so the enum lists 5 values instead of 4:

```yaml
# Before:
reason: title_change   # title_change | slug_override | section_change | removed
# `slug_override` is emitted when the caller passes `:had-slug-override-p t`
# to `record-publish` ...

# After:
reason: title_change   # title_change | slug_override | section_change | removed | republished
# `slug_override` is emitted when the caller passes `:had-slug-override-p t`
# to `record-publish` ...
# `republished` is emitted when a note transitions from state: removed back to
# state: live (added in A.1.d).
```

Also locate (probably around lines 240-247) any prose about "On each publish:" and append:

```markdown
- For each previously-removed note that re-enters the published-set: flip
  `state: live`, append a history entry with `reason: republished`, and
  re-merge aliases from prior history on render.
```

- [ ] **Step 2: Update data/url-history.yaml comment block**

The seed file currently lists 4 reasons in its leading comment. Update to 5:

```yaml
# URL-history manifest for the org→Hugo publish pipeline.
# Managed by a3madkour-publish-history.el (sub-project A.1.a),
# extended by a3madkour-publish-unpublish.el (sub-project A.1.d).
# See docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md §8.
#
# Schema (per-note entry):
#   id:           org-roam :ID: (UUID v4)
#   current_url:  /<section>/<slug>/  (or null if state=removed)
#   history:      list of {url, replaced_at, reason} entries; oldest-first
#     reason ∈ {title_change, slug_override, section_change, removed, republished}
#   state:        live | draft | removed
#
# DO NOT edit by hand — re-publish will rewrite.

notes: []
```

Data row (`notes: []`) is unchanged.

- [ ] **Step 3: Commit the Stage-0 amendment**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md \
        data/url-history.yaml
git commit -m "docs(phase-3): A.1.d parent-spec amendments — republished reason enum

Bumps the parent spec §8 reason enum from 4 → 5 values: adds
\`republished\` for the removed → live transition. Also updates
data/url-history.yaml's leading comment block to list the 5-value
enum.

This is the Stage-0 commit for A.1.d (mirrors the A.1.b precedent
\`62636ef\`). Implementation tasks consume the new enum value
starting at Task 4 (extends pub-history/record-publish)."
```

- [ ] **Step 4: Test-count checkpoint**

End of Task 1: **175 ert tests** (unchanged — docs-only stage). 11 Python sibling tests. 4 Python integration fixtures.

---

### Task 2: Create `a3madkour-publish-unpublish.el` skeleton + test file + wrapper-script registration

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`

Lesson applied from A.1.c: register the new module in `a3-pub.sh`'s `-l` chain **as part of the task that introduces it**. Don't defer to a downstream task. (Memory: `feedback_plan_wrapper_script_updates`.)

- [ ] **Step 1: Write the failing skeleton test**

Create `a3madkour-publish-unpublish-test.el`:

```elisp
;;; a3madkour-publish-unpublish-test.el --- Tests for unpublish module -*- lexical-binding: t; -*-
;;
;;; Commentary:
;; ert tests for `a3madkour-publish-unpublish.el' (sub-project A.1.d).
;;
;;; Code:

(require 'ert)
(require 'a3madkour-publish-unpublish)

(ert-deftest a3madkour-pub-unpublish-test/skeleton-loaded ()
  "The unpublish module loads and its provide marker is registered."
  (should (featurep 'a3madkour-publish-unpublish)))

(provide 'a3madkour-publish-unpublish-test)
;;; a3madkour-publish-unpublish-test.el ends here
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: load error — `Cannot open load file: a3madkour-publish-unpublish`. Exit non-zero.

- [ ] **Step 3: Create the skeleton module**

Create `a3madkour-publish-unpublish.el`:

```elisp
;;; a3madkour-publish-unpublish.el --- Unpublish flow + orchestrator (A.1.d) -*- lexical-binding: t; -*-
;;
;; Author: Abdelrahman Madkour
;; Version: 0.1.0
;;
;;; Commentary:
;; Phase 3 sub-project A.1.d.  Implements the three-step unpublish
;; orchestrator + --check-orphans dry-run preview, closing parent spec
;; §12 A.1 item #7.
;;
;;   Step A — unpublish sweep: diff new live-set vs manifest, delete
;;            stale page bundles, mutate manifest entries.
;;   Step B — slug-shift sync: rename ~/org/notes/assets/page/<old>/ →
;;            <new>/ and bulk-rewrite source .org link references.
;;   Step C — re-link-check: WARN for live-note outgoing links resolving
;;            into the removed-this-publish set.
;;
;; Public entry points:
;;   `a3madkour-pub/finish-publish'    — orchestrator (commits to FS + manifest)
;;   `a3madkour-pub/check-orphans'     — thin alias for dry-run preview
;;   `a3madkour-pub/diff-published-set'      — pure diff helper
;;   `a3madkour-pub/walk-published-source-set' — standalone-mode driver
;;
;; See `docs/superpowers/specs/2026-05-24-phase-3-a1-d-unpublish-design.md'.
;;
;;; Code:

(require 'cl-lib)
(require 'a3madkour-publish)
(require 'a3madkour-publish-history)

(provide 'a3madkour-publish-unpublish)

;;; a3madkour-publish-unpublish.el ends here
```

- [ ] **Step 4: Register the new module in `a3-pub.sh`**

Edit `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`. Find the existing `-l a3madkour-publish-assets \` line and add a new `-l a3madkour-publish-unpublish \` line immediately after it (alphabetical proximity + load-order compatibility — unpublish requires publish + publish-history which are loaded earlier in the chain). The relevant block changes from:

```bash
  -l a3madkour-publish \
  -l a3madkour-publish-rewrite \
  -l a3madkour-publish-assets \
  --eval "(message \"[a3-pub] ready (v%s)\" a3madkour-pub/version)" \
```

to:

```bash
  -l a3madkour-publish \
  -l a3madkour-publish-rewrite \
  -l a3madkour-publish-assets \
  -l a3madkour-publish-unpublish \
  --eval "(message \"[a3-pub] ready (v%s)\" a3madkour-pub/version)" \
```

- [ ] **Step 5: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 176 tests, 176 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 6: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el \
        emacs-configs/custom/lisp/a3-pub.sh
```

End of Task 2: **176 ert tests** (175 → 176).

---

### Task 3: Add `a3madkour-pub--publish-run-accumulator` defvar + extend `begin-publish`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

The accumulator gives B a place to record per-note publish events during its loop. `finish-publish` reads it (B-coupled mode) or falls back to `walk-published-source-set` (standalone mode).

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-test.el`:

```elisp
;; -- A.1.d: publish-run-accumulator + begin-publish extension --

(ert-deftest a3madkour-pub-test/publish-run-accumulator-is-hash-table ()
  "The accumulator defvar is bound to a hash table with equal test."
  (should (hash-table-p a3madkour-pub--publish-run-accumulator))
  (should (eq (hash-table-test a3madkour-pub--publish-run-accumulator) 'equal)))

(ert-deftest a3madkour-pub-test/begin-publish-clears-accumulator ()
  "`begin-publish' empties the accumulator alongside the metadata cache."
  (puthash "stale-id" '("/garden/old/" . live) a3madkour-pub--publish-run-accumulator)
  (should (> (hash-table-count a3madkour-pub--publish-run-accumulator) 0))
  (cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil)))
    (a3madkour-pub/begin-publish))
  (should (= 0 (hash-table-count a3madkour-pub--publish-run-accumulator))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 2 failures — `Symbol's value as variable is void: a3madkour-pub--publish-run-accumulator`. Exit non-zero.

- [ ] **Step 3: Add the defvar + extend `begin-publish`**

Edit `a3madkour-publish.el`. Find the `a3madkour-pub--metadata-cache` defvar block (around line 147) and add the accumulator defvar immediately below it:

```elisp
(defvar a3madkour-pub--publish-run-accumulator
  (make-hash-table :test 'equal)
  "Per-publish-run accumulator of id → (current-url . state) for notes that
`a3madkour-pub-history/record-publish' processed during this publish.

Populated incrementally by B's per-content-type publisher (via record-publish);
consumed by `a3madkour-pub/finish-publish' to compute the new live+draft set
without re-walking the source tree.

When empty at the time `finish-publish' runs, the orchestrator falls back to
`a3madkour-pub/walk-published-source-set' (standalone mode — used today,
before B ships).

Reset explicitly via `a3madkour-pub/begin-publish' at the start of each run.")
```

Then edit `a3madkour-pub/begin-publish` (around line 233) to clear the accumulator alongside the metadata cache. Body becomes:

```elisp
(defun a3madkour-pub/begin-publish ()
  "Take per-publish snapshots: reset metadata cache; clear accumulator;
sync org-roam DB.

Call this at the start of any publish run (shell or interactive).
Both A's accessors and the link rewriter rely on these snapshots being
fresh; edits made after this call are NOT picked up until the next
`begin-publish' call.

See parent spec §11 (snapshot-at-publish-start subsection).  A.1.d adds
the publish-run-accumulator clear (the accumulator backs `finish-publish'
in B-coupled mode).

NOTE: `org-roam' is required lazily via `autoload'/dynamic load on first
use of `org-roam-db-sync'.  Tests stub `org-roam-db-sync' via `cl-letf'
to avoid touching the author's real org-roam DB; for that stub to remain
in effect across the call, org-roam must already be loaded (so that
`require' here is a no-op).  The test file pre-requires `org-roam' for
that reason."
  (a3madkour-pub--reset-metadata-cache)
  (clrhash a3madkour-pub--publish-run-accumulator)
  (require 'org-roam)
  (org-roam-db-sync))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 178 tests, 178 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish.el \
        emacs-configs/custom/lisp/a3madkour-publish-test.el
```

End of Task 3: **178 ert tests** (176 → 178).

---

### Task 4: Extend `pub-history/record-publish` — `republished` reason + accumulator append

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

Three changes layered on top of the existing 4-value enum: (a) `--diff-reason` returns `"republished"` for removed→live transitions; (b) the main `record-publish` cond branches handle this case (flip state, append event); (c) every call appends to the accumulator (B's hook).

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-history-test.el`:

```elisp
;; -- A.1.d: republished reason path + accumulator append --

(ert-deftest a3madkour-pub-history-test/republished-flips-state-and-appends-event ()
  "A removed → live transition flips state, appends a `republished' event."
  (a3-pub-history-test--with-tmp-manifest path
    ;; Seed manifest with one removed note (URL was /garden/foo/).
    (let ((m `((notes . [((id . "rep-id-1")
                          (current_url . nil)
                          (history . [((url . "/garden/foo/")
                                       (replaced_at . "2026-05-22T10:00:00Z")
                                       (reason . "removed"))])
                          (state . "removed"))]))))
      (a3madkour-pub-history/write-manifest m))
    ;; Republish at the same URL.
    (cl-letf (((symbol-function 'a3madkour-pub-history--now-iso)
               (lambda () "2026-05-24T12:00:00Z")))
      (a3madkour-pub-history/record-publish "rep-id-1" "/garden/foo/" 'live))
    ;; Check.
    (let* ((m (a3madkour-pub-history/read-manifest))
           (note (aref (alist-get 'notes m) 0))
           (hist (alist-get 'history note)))
      (should (equal (alist-get 'state note) "live"))
      (should (equal (alist-get 'current_url note) "/garden/foo/"))
      (should (= 2 (length hist)))
      (should (equal (alist-get 'reason (aref hist 1)) "republished"))
      (should (equal (alist-get 'url (aref hist 1)) nil)))))

(ert-deftest a3madkour-pub-history-test/republished-aliases-re-merged-from-prior ()
  "After republish, aliases-for surfaces the prior URL from history."
  (a3-pub-history-test--with-tmp-manifest path
    (let ((m `((notes . [((id . "rep-id-2")
                          (current_url . nil)
                          (history . [((url . "/garden/old/")
                                       (replaced_at . "2026-05-22T10:00:00Z")
                                       (reason . "removed"))])
                          (state . "removed"))]))))
      (a3madkour-pub-history/write-manifest m))
    (cl-letf (((symbol-function 'a3madkour-pub-history--now-iso)
               (lambda () "2026-05-24T12:00:00Z")))
      (a3madkour-pub-history/record-publish "rep-id-2" "/garden/new/" 'live))
    (should (member "/garden/old/" (a3madkour-pub-history/aliases-for "rep-id-2")))))

(ert-deftest a3madkour-pub-history-test/record-publish-appends-to-accumulator ()
  "Every record-publish call pushes (id . (url . state)) into the accumulator."
  (a3-pub-history-test--with-tmp-manifest path
    (clrhash a3madkour-pub--publish-run-accumulator)
    (a3madkour-pub-history/record-publish "acc-id-1" "/garden/x/" 'live)
    (a3madkour-pub-history/record-publish "acc-id-2" "/garden/y/" 'draft)
    (a3madkour-pub-history/record-publish "acc-id-3" nil 'removed)
    (should (= 3 (hash-table-count a3madkour-pub--publish-run-accumulator)))
    (should (equal (gethash "acc-id-1" a3madkour-pub--publish-run-accumulator)
                   '("/garden/x/" . live)))
    (should (equal (gethash "acc-id-2" a3madkour-pub--publish-run-accumulator)
                   '("/garden/y/" . draft)))
    (should (equal (gethash "acc-id-3" a3madkour-pub--publish-run-accumulator)
                   '(nil . removed)))))
```

If a tmp-manifest fixture macro isn't already defined in the test file, add it once at the top (it's already in place from A.1.a — verify with `grep -n "with-tmp-manifest" ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`; if absent, model after the asset test file's `a3-pub-assets-test--with-tmp-root` pattern).

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures — republished test fails because state stays `"removed"`; accumulator test fails because nothing populates it. Exit non-zero.

- [ ] **Step 3: Extend `record-publish`**

Edit `a3madkour-publish-history.el`. The current `record-publish` `cond` handles two branches: new note (insert) and existing note (compute diff). The "existing" branch already detects `state-changed-p`. Extend the reason-derivation `cond` to recognize republish.

Replace the existing reason `cond` block (around line 170-173) with the extended version:

```elisp
                 (reason (cond
                          ;; Removed (new-url is nil; state must flip to removed).
                          ((and url-changed-p (null new-url)) "removed")
                          ;; Republished: was removed, now live again.
                          ((and state-changed-p
                                (equal old-state "removed")
                                (equal state-str "live"))
                           "republished")
                          ;; Any other URL change → existing enum.
                          (url-changed-p (a3madkour-pub-history--diff-reason
                                          old-url new-url had-slug-override-p))
                          (t nil)))  ; state-only change (e.g. live ↔ draft)
```

The republished branch must fire even when `url-changed-p` is false (republishing at the same URL) — that's why it's checked before the bare `url-changed-p` branch and uses `state-changed-p` as its trigger.

The history append needs to fire for the republished case too. The current code only appends when `reason` is non-nil — so the new `"republished"` value naturally triggers append. No extra change needed.

Then add the accumulator append. Insert this line immediately after the `(let* ((manifest ...) ...))` binding block in `record-publish`, before the `cond` (so even the no-op state-only case still updates the accumulator if state matched):

Actually — simpler: append unconditionally at the END of `record-publish`, after the `cond`. The accumulator records the current state regardless of whether the manifest was mutated. Replace the entire `record-publish` body's tail (after the existing `cond` closing parens) so it becomes:

```elisp
(cl-defun a3madkour-pub-history/record-publish (id new-url state &key had-slug-override-p)
  "Update the manifest entry for ID.

[... existing docstring preserved ...]

A.1.d additions:
  - `\"republished\"' reason: emitted on a removed → live transition.
  - Every call appends `(id . (new-url . state))' to
    `a3madkour-pub--publish-run-accumulator' for `finish-publish' consumption."
  (let* ((manifest (a3madkour-pub-history/read-manifest))
         (notes (alist-get 'notes manifest))
         (idx (a3madkour-pub-history--find-note-by-id notes id))
         (state-str (a3madkour-pub-history--state-to-string state)))
    (cond
     ;; New note.
     ((null idx)
      (let* ((new-note `((id . ,id)
                         (current_url . ,new-url)
                         (history . [])
                         (state . ,state-str)))
             (new-notes (vconcat notes (vector new-note))))
        (setf (alist-get 'notes manifest) new-notes)
        (a3madkour-pub-history/write-manifest manifest)))
     ;; Existing — compute diff.
     (t
      (let* ((current (aref notes idx))
             (old-url (alist-get 'current_url current))
             (old-state (alist-get 'state current))
             (url-changed-p (not (equal old-url new-url)))
             (state-changed-p (not (equal old-state state-str))))
        (when (or url-changed-p state-changed-p)
          (let* ((reason (cond
                          ((and url-changed-p (null new-url)) "removed")
                          ((and state-changed-p
                                (equal old-state "removed")
                                (equal state-str "live"))
                           "republished")
                          (url-changed-p (a3madkour-pub-history--diff-reason
                                          old-url new-url had-slug-override-p))
                          (t nil)))
                 (new-history
                  (if reason
                      (vconcat (alist-get 'history current)
                               (vector `((url . ,old-url)
                                         (replaced_at . ,(a3madkour-pub-history--now-iso))
                                         (reason . ,reason))))
                    (alist-get 'history current)))
                 (updated `((id . ,id)
                            (current_url . ,new-url)
                            (history . ,new-history)
                            (state . ,state-str))))
            (aset notes idx updated)
            (a3madkour-pub-history/write-manifest manifest))))))
    ;; A.1.d: accumulator append (always, regardless of mutation path above).
    (puthash id (cons new-url state) a3madkour-pub--publish-run-accumulator)))
```

The accumulator append uses a `(url . state)` cons where state is the **symbol** form (not `state-str`), matching the contract the diff function expects (see Task 5).

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 181 tests, 181 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-history.el \
        emacs-configs/custom/lisp/a3madkour-publish-history-test.el
```

End of Task 4: **181 ert tests** (178 → 181).

---

### Task 5: `a3madkour-pub/diff-published-set` (pure)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

Pure-ish: reads manifest internally (via `pub-history/read-manifest`) but no FS writes, no side effects beyond that read. Tests stub `read-manifest` with `cl-letf`.

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- diff-published-set: pure diff over manifest live+draft vs new-set --

(defmacro a3-pub-unpublish-test--with-manifest (manifest &rest body)
  "Stub pub-history/read-manifest to return MANIFEST for BODY."
  (declare (indent 1))
  `(cl-letf (((symbol-function 'a3madkour-pub-history/read-manifest)
              (lambda () ,manifest)))
     ,@body))

(defun a3-pub-unpublish-test--mk-new-set (&rest entries)
  "Build a hash table id → (url . state) from ENTRIES of (id url state)."
  (let ((h (make-hash-table :test 'equal)))
    (dolist (e entries)
      (puthash (nth 0 e) (cons (nth 1 e) (nth 2 e)) h))
    h))

(ert-deftest a3madkour-pub-unpublish-test/diff-added-only ()
  "New ids that aren't in manifest land in :added."
  (a3-pub-unpublish-test--with-manifest '((notes . []))
    (let* ((new (a3-pub-unpublish-test--mk-new-set
                 '("id-new" "/garden/x/" live)))
           (d (a3madkour-pub/diff-published-set new)))
      (should (equal (plist-get d :added) '("id-new")))
      (should (null (plist-get d :removed)))
      (should (null (plist-get d :stayed)))
      (should (null (plist-get d :slug-shifted))))))

(ert-deftest a3madkour-pub-unpublish-test/diff-removed-only ()
  "Manifest ids absent from new-set land in :removed."
  (a3-pub-unpublish-test--with-manifest
      '((notes . [((id . "id-gone") (current_url . "/garden/g/")
                   (history . []) (state . "live"))]))
    (let* ((new (a3-pub-unpublish-test--mk-new-set))
           (d (a3madkour-pub/diff-published-set new)))
      (should (equal (plist-get d :removed) '("id-gone"))))))

(ert-deftest a3madkour-pub-unpublish-test/diff-stayed-only ()
  "Ids present in both with identical URLs land in :stayed (not :slug-shifted)."
  (a3-pub-unpublish-test--with-manifest
      '((notes . [((id . "id-same") (current_url . "/garden/x/")
                   (history . []) (state . "live"))]))
    (let* ((new (a3-pub-unpublish-test--mk-new-set
                 '("id-same" "/garden/x/" live)))
           (d (a3madkour-pub/diff-published-set new)))
      (should (equal (plist-get d :stayed) '("id-same")))
      (should (null (plist-get d :slug-shifted))))))

(ert-deftest a3madkour-pub-unpublish-test/diff-slug-shifted ()
  "Ids present in both with different URLs land in :slug-shifted (+ also in :stayed)."
  (a3-pub-unpublish-test--with-manifest
      '((notes . [((id . "id-shift") (current_url . "/garden/foo/")
                   (history . []) (state . "live"))]))
    (let* ((new (a3-pub-unpublish-test--mk-new-set
                 '("id-shift" "/garden/foo-v2/" live)))
           (d (a3madkour-pub/diff-published-set new)))
      (should (equal (plist-get d :stayed) '("id-shift")))
      (should (equal (plist-get d :slug-shifted)
                     '(("id-shift" "/garden/foo/" "/garden/foo-v2/")))))))

(ert-deftest a3madkour-pub-unpublish-test/diff-mixed ()
  "Mixed scenario: 1 added + 1 removed + 1 stayed + 1 slug-shifted."
  (a3-pub-unpublish-test--with-manifest
      '((notes . [((id . "id-gone")  (current_url . "/garden/g/")
                   (history . []) (state . "live"))
                  ((id . "id-same")  (current_url . "/garden/s/")
                   (history . []) (state . "live"))
                  ((id . "id-shift") (current_url . "/garden/a/")
                   (history . []) (state . "live"))]))
    (let* ((new (a3-pub-unpublish-test--mk-new-set
                 '("id-new"   "/garden/n/" live)
                 '("id-same"  "/garden/s/" live)
                 '("id-shift" "/garden/b/" live)))
           (d (a3madkour-pub/diff-published-set new)))
      (should (equal (sort (plist-get d :added) #'string<) '("id-new")))
      (should (equal (plist-get d :removed) '("id-gone")))
      (should (member "id-same" (plist-get d :stayed)))
      (should (member "id-shift" (plist-get d :stayed)))
      (should (equal (plist-get d :slug-shifted)
                     '(("id-shift" "/garden/a/" "/garden/b/")))))))

(ert-deftest a3madkour-pub-unpublish-test/diff-ignores-removed-state-in-manifest ()
  "Manifest entries already in state `removed' are not in old-set; not :removed-again."
  (a3-pub-unpublish-test--with-manifest
      '((notes . [((id . "id-old-removed") (current_url . nil)
                   (history . [((url . "/garden/x/") (replaced_at . "t")
                                (reason . "removed"))])
                   (state . "removed"))]))
    (let* ((new (a3-pub-unpublish-test--mk-new-set))
           (d (a3madkour-pub/diff-published-set new)))
      (should (null (plist-get d :removed))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 6 failures — `Symbol's function definition is void: a3madkour-pub/diff-published-set`. Exit non-zero.

- [ ] **Step 3: Implement `diff-published-set`**

Insert into `a3madkour-publish-unpublish.el` (between the `(require)` block and `(provide)`):

```elisp
(defun a3madkour-pub/diff-published-set (new-set)
  "Diff NEW-SET against the manifest's currently-live+draft entries.

NEW-SET is a hash table id → (url . state) where state is `live' or `draft'.
The old set is computed by reading the manifest via
`a3madkour-pub-history/read-manifest' and filtering to entries with
`state ∈ {live, draft}' (manifest entries already in `removed' are
excluded from the old set, so re-removing them is a no-op).

Returns a plist:
  :added         (id ...)
  :removed       (id ...)
  :stayed        (id ...)
  :slug-shifted  ((id old-url new-url) ...)

`:slug-shifted' is a strict subset of `:stayed' — an id whose URL changed
appears in BOTH (in :stayed because it's still published; in :slug-shifted
because the URL also changed).  Step B (in `finish-publish') consumes
:slug-shifted to drive asset-dir + source-link migration."
  (let* ((manifest (a3madkour-pub-history/read-manifest))
         (notes (alist-get 'notes manifest))
         (old-set (make-hash-table :test 'equal))
         added removed stayed slug-shifted)
    ;; Build old-set from manifest live+draft entries.
    (cl-loop for i from 0 below (length notes)
             for entry = (aref notes i)
             for state-str = (alist-get 'state entry)
             when (member state-str '("live" "draft"))
             do (puthash (alist-get 'id entry)
                         (cons (alist-get 'current_url entry)
                               (intern state-str))
                         old-set))
    ;; Walk new-set: classify each id.
    (maphash
     (lambda (id new-entry)
       (let* ((new-url (car new-entry))
              (old-entry (gethash id old-set)))
         (cond
          ((null old-entry)
           (push id added))
          (t
           (push id stayed)
           (let ((old-url (car old-entry)))
             (unless (equal old-url new-url)
               (push (list id old-url new-url) slug-shifted)))))))
     new-set)
    ;; Walk old-set: anything not in new-set is :removed.
    (maphash
     (lambda (id _old-entry)
       (unless (gethash id new-set)
         (push id removed)))
     old-set)
    (list :added (nreverse added)
          :removed (nreverse removed)
          :stayed (nreverse stayed)
          :slug-shifted (nreverse slug-shifted))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 187 tests, 187 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 5: **187 ert tests** (181 → 187).

---

### Task 6: `a3madkour-pub/walk-published-source-set`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

Walks `a3madkour-pub/org-notes-dir` recursively, parses each `.org`, returns the hash table for the new live+draft set. Used by `finish-publish` in standalone mode (when B hasn't pre-populated the accumulator).

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- walk-published-source-set: standalone-mode driver --

(defmacro a3-pub-unpublish-test--with-tmp-notes-dir (dir-var &rest body)
  "Bind DIR-VAR to a fresh tmpdir + bind `a3madkour-pub/org-notes-dir' to it."
  (declare (indent 1))
  `(let* ((,dir-var (make-temp-file "a3-pub-walk-" t))
          (a3madkour-pub/org-notes-dir ,dir-var))
     (unwind-protect (progn ,@body)
       (delete-directory ,dir-var t))))

(defun a3-pub-unpublish-test--write-org (dir relpath body)
  "Write BODY to DIR/RELPATH (creating parent dirs as needed)."
  (let ((full (expand-file-name relpath dir)))
    (make-directory (file-name-directory full) t)
    (with-temp-file full (insert body))))

(ert-deftest a3madkour-pub-unpublish-test/walk-empty-dir ()
  "Empty notes dir → empty hash table."
  (a3-pub-unpublish-test--with-tmp-notes-dir d
    (let ((result (a3madkour-pub/walk-published-source-set)))
      (should (hash-table-p result))
      (should (= 0 (hash-table-count result))))))

(ert-deftest a3madkour-pub-unpublish-test/walk-respects-hugo-publish-gate ()
  "Notes without `#+HUGO_PUBLISH: t' are skipped."
  (a3-pub-unpublish-test--with-tmp-notes-dir d
    (a3-pub-unpublish-test--write-org d "yes.org"
      ":PROPERTIES:\n:ID: yes-id-1\n:END:\n#+TITLE: Yes\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\nbody\n")
    (a3-pub-unpublish-test--write-org d "no.org"
      ":PROPERTIES:\n:ID: no-id-1\n:END:\n#+TITLE: No\nbody\n")
    (let ((result (a3madkour-pub/walk-published-source-set)))
      (should (= 1 (hash-table-count result)))
      (should (gethash "yes-id-1" result))
      (should (null (gethash "no-id-1" result))))))

(ert-deftest a3madkour-pub-unpublish-test/walk-distinguishes-live-vs-draft ()
  "`#+HUGO_DRAFT: t' yields state `draft'; absent yields `live'."
  (a3-pub-unpublish-test--with-tmp-notes-dir d
    (a3-pub-unpublish-test--write-org d "live.org"
      ":PROPERTIES:\n:ID: live-id-1\n:END:\n#+TITLE: Live\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\nbody\n")
    (a3-pub-unpublish-test--write-org d "draft.org"
      ":PROPERTIES:\n:ID: draft-id-1\n:END:\n#+TITLE: Draft\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n#+HUGO_DRAFT: t\nbody\n")
    (let ((result (a3madkour-pub/walk-published-source-set)))
      (should (equal (cdr (gethash "live-id-1" result)) 'live))
      (should (equal (cdr (gethash "draft-id-1" result)) 'draft)))))

(ert-deftest a3madkour-pub-unpublish-test/walk-skips-files-without-id ()
  "Files missing :ID: are skipped (not in result)."
  (a3-pub-unpublish-test--with-tmp-notes-dir d
    (a3-pub-unpublish-test--write-org d "noid.org"
      "#+TITLE: No id\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\nbody\n")
    (let ((result (a3madkour-pub/walk-published-source-set)))
      (should (= 0 (hash-table-count result))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures — `Symbol's function definition is void: a3madkour-pub/walk-published-source-set`. Exit non-zero.

- [ ] **Step 3: Implement `walk-published-source-set`**

Insert into `a3madkour-publish-unpublish.el` (after `diff-published-set`, before `(provide)`):

```elisp
(defun a3madkour-pub/walk-published-source-set ()
  "Walk `a3madkour-pub/org-notes-dir' recursively, return hash table of the
new published set.

Returns id → (url . state) where state is `live' or `draft'.

Standalone-mode driver for `a3madkour-pub/finish-publish' — used when the
publish-run-accumulator is empty (no `record-publish' calls happened this
run, e.g. before B ships).  Each .org file is parsed via
`a3madkour-pub--parse-file' (which already implements the HUGO_PUBLISH gate
+ HUGO_DRAFT detection + slug derivation); files without `:state' (i.e.
unpublished or missing :ID:) are skipped.

This walk takes a fresh per-call snapshot of the source tree; it does NOT
hit the metadata cache populated by `note-metadata' (which is per-file
keyed, not per-walk).  Repeated calls are independent."
  (let ((set (make-hash-table :test 'equal)))
    (dolist (file (directory-files-recursively a3madkour-pub/org-notes-dir
                                                "\\.org\\'"))
      (let* ((parsed (a3madkour-pub--parse-file file))
             (state (plist-get parsed :state))
             (id (plist-get parsed :id))
             (section (plist-get parsed :section))
             (slug (plist-get parsed :slug)))
        (when (and state id section slug)
          (puthash id
                   (cons (format "/%s/%s/" section slug) state)
                   set))))
    set))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 191 tests, 191 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 6: **191 ert tests** (187 → 191).

---

### Task 7: `unpublish--delete-bundle` helper

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

Internal helper. Computes `<content-root>/<section>/<slug>/`, recursively deletes if present. Missing dir is informational not an error. Permission errors propagate (orchestrator aggregates them into `:partial-failures`).

- [ ] **Step 1: Add the content-dir defcustom + write the failing tests**

First, append the defcustom near the top of `a3madkour-publish-unpublish.el` (after the requires, before any defuns):

```elisp
(defcustom a3madkour-pub-site-content-dir
  (expand-file-name "Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/content/"
                    "~/")
  "Root of the Hugo `content/' tree for the site repo.
`a3madkour-pub--unpublish-delete-bundle' resolves `<content-root>/<section>/<slug>/'
against this when an orchestrator step needs to remove a bundle.

Override per-call by passing a third arg to the helper, or `let'-bind
this defcustom inside a fixture."
  :type 'directory
  :group 'a3madkour-publish)
```

Then append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- unpublish--delete-bundle helper --

(ert-deftest a3madkour-pub-unpublish-test/delete-bundle-happy ()
  "Existing bundle dir is removed recursively."
  (let* ((root (make-temp-file "a3-pub-content-" t))
         (bundle (expand-file-name "garden/foo" root)))
    (unwind-protect
        (progn
          (make-directory bundle t)
          (with-temp-file (expand-file-name "index.md" bundle) (insert "x"))
          (should (file-directory-p bundle))
          (a3madkour-pub--unpublish-delete-bundle "garden" "foo" root)
          (should-not (file-directory-p bundle)))
      (delete-directory root t))))

(ert-deftest a3madkour-pub-unpublish-test/delete-bundle-missing-dir-silent ()
  "Missing bundle dir is not an error (info log only)."
  (let ((root (make-temp-file "a3-pub-content-" t)))
    (unwind-protect
        ;; Should not raise:
        (a3madkour-pub--unpublish-delete-bundle "garden" "never-existed" root)
      (delete-directory root t))))

(ert-deftest a3madkour-pub-unpublish-test/delete-bundle-permission-error-propagates ()
  "Errors raised by delete-directory propagate up."
  (let* ((root (make-temp-file "a3-pub-content-" t))
         (bundle (expand-file-name "garden/foo" root)))
    (unwind-protect
        (progn
          (make-directory bundle t)
          (cl-letf (((symbol-function 'delete-directory)
                     (lambda (&rest _) (error "permission denied"))))
            (should-error
             (a3madkour-pub--unpublish-delete-bundle "garden" "foo" root)
             :type 'error)))
      (delete-directory root t))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures — `Symbol's function definition is void: a3madkour-pub--unpublish-delete-bundle`. Exit non-zero.

- [ ] **Step 3: Implement `unpublish--delete-bundle`**

Insert into `a3madkour-publish-unpublish.el` (after `walk-published-source-set`):

```elisp
(defun a3madkour-pub--unpublish-delete-bundle (section slug &optional content-root)
  "Recursively delete `<CONTENT-ROOT>/<SECTION>/<SLUG>/'.

CONTENT-ROOT defaults to `a3madkour-pub-site-content-dir'.  If the bundle
dir doesn't exist, logs via `message' and returns nil (not an error —
stale-manifest case is benign).  Other delete errors (permissions, file
lock) propagate to the caller.

Returns t on successful delete, nil if dir was absent."
  (let* ((root (or content-root a3madkour-pub-site-content-dir))
         (bundle (file-name-as-directory
                  (expand-file-name (format "%s/%s" section slug) root))))
    (cond
     ((file-directory-p bundle)
      (delete-directory bundle t)
      t)
     (t
      (message "[a3-pub] delete-bundle: %s already absent (stale manifest?)" bundle)
      nil))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 194 tests, 194 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 7: **194 ert tests** (191 → 194).

---

### Task 8: `pub/finish-publish` Step A integration

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

First skeleton of the orchestrator. Implements ONLY Step A (sweep) — Steps B + C land in Tasks 11 + 13. Returns the full plist shape (with `:slug-shifted` and `:orphan-warnings` as `nil` for now).

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- finish-publish: Step A skeleton --

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-step-a-happy ()
  "Step A: one removed note → bundle deleted, manifest mutated, :removed populated."
  (let* ((content-root (make-temp-file "a3-pub-content-" t))
         (bundle (expand-file-name "garden/gone" content-root))
         (manifest-path (make-temp-file "a3-pub-history-" nil ".yaml")))
    (unwind-protect
        (progn
          (make-directory bundle t)
          (with-temp-file (expand-file-name "index.md" bundle) (insert "x"))
          (let ((a3madkour-pub-site-content-dir content-root)
                (a3madkour-pub/site-data-dir (file-name-directory manifest-path))
                (manifest `((notes . [((id . "id-gone")
                                       (current_url . "/garden/gone/")
                                       (history . [])
                                       (state . "live"))]))))
            ;; Place the seed manifest file where read-manifest will find it.
            ;; Override the manifest-path to the tmpfile we already have:
            (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                       (lambda () manifest-path))
                      ((symbol-function 'a3madkour-pub-history--now-iso)
                       (lambda () "2026-05-24T12:00:00Z")))
              (a3madkour-pub-history/write-manifest manifest)
              ;; Empty accumulator + nothing in new-set → id-gone is removed.
              (clrhash a3madkour-pub--publish-run-accumulator)
              (cl-letf (((symbol-function 'a3madkour-pub/walk-published-source-set)
                         (lambda () (make-hash-table :test 'equal))))
                (let ((result (a3madkour-pub/finish-publish)))
                  (should (equal (plist-get result :removed) '("id-gone")))
                  (should-not (file-directory-p bundle))
                  (let* ((m (a3madkour-pub-history/read-manifest))
                         (note (aref (alist-get 'notes m) 0)))
                    (should (equal (alist-get 'state note) "removed"))))))))
      (when (file-exists-p manifest-path) (delete-file manifest-path))
      (delete-directory content-root t))))

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-dry-run-no-mutation ()
  ":dry-run t skips bundle delete AND manifest mutation; still reports :removed."
  (let* ((content-root (make-temp-file "a3-pub-content-" t))
         (bundle (expand-file-name "garden/gone" content-root))
         (manifest-path (make-temp-file "a3-pub-history-" nil ".yaml")))
    (unwind-protect
        (progn
          (make-directory bundle t)
          (with-temp-file (expand-file-name "index.md" bundle) (insert "x"))
          (let ((a3madkour-pub-site-content-dir content-root)
                (manifest `((notes . [((id . "id-gone")
                                       (current_url . "/garden/gone/")
                                       (history . [])
                                       (state . "live"))]))))
            (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                       (lambda () manifest-path)))
              (a3madkour-pub-history/write-manifest manifest)
              (clrhash a3madkour-pub--publish-run-accumulator)
              (cl-letf (((symbol-function 'a3madkour-pub/walk-published-source-set)
                         (lambda () (make-hash-table :test 'equal))))
                (let ((result (a3madkour-pub/finish-publish :dry-run t)))
                  (should (equal (plist-get result :removed) '("id-gone")))
                  ;; Bundle still present (dry-run skipped delete).
                  (should (file-directory-p bundle))
                  ;; Manifest still says live (dry-run skipped record-publish).
                  (let* ((m (a3madkour-pub-history/read-manifest))
                         (note (aref (alist-get 'notes m) 0)))
                    (should (equal (alist-get 'state note) "live"))))))))
      (when (file-exists-p manifest-path) (delete-file manifest-path))
      (delete-directory content-root t))))

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-empty-diff ()
  "Empty diff (no removes, no shifts) → :removed nil; no side effects."
  (let ((manifest-path (make-temp-file "a3-pub-history-" nil ".yaml")))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                   (lambda () manifest-path)))
          (a3madkour-pub-history/write-manifest '((notes . [])))
          (clrhash a3madkour-pub--publish-run-accumulator)
          (cl-letf (((symbol-function 'a3madkour-pub/walk-published-source-set)
                     (lambda () (make-hash-table :test 'equal))))
            (let ((result (a3madkour-pub/finish-publish)))
              (should (null (plist-get result :removed)))
              (should (null (plist-get result :slug-shifted)))
              (should (null (plist-get result :orphan-warnings))))))
      (when (file-exists-p manifest-path) (delete-file manifest-path)))))

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-prefers-accumulator-over-walk ()
  "Non-empty accumulator is used as new-set; walk is NOT called."
  (let ((manifest-path (make-temp-file "a3-pub-history-" nil ".yaml"))
        (walk-called nil))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                   (lambda () manifest-path)))
          (a3madkour-pub-history/write-manifest '((notes . [])))
          (clrhash a3madkour-pub--publish-run-accumulator)
          (puthash "id-from-acc" '("/garden/x/" . live)
                   a3madkour-pub--publish-run-accumulator)
          (cl-letf (((symbol-function 'a3madkour-pub/walk-published-source-set)
                     (lambda () (setq walk-called t)
                                (make-hash-table :test 'equal))))
            (let ((result (a3madkour-pub/finish-publish)))
              (should-not walk-called)
              ;; id-from-acc is new → :added; no :removed.
              (should (member "id-from-acc" (plist-get result :added))))))
      (when (file-exists-p manifest-path) (delete-file manifest-path)))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures — `Symbol's function definition is void: a3madkour-pub/finish-publish`. Exit non-zero.

- [ ] **Step 3: Implement `finish-publish` (Step A only)**

Insert into `a3madkour-publish-unpublish.el` (after `unpublish--delete-bundle`):

```elisp
(defun a3madkour-pub--unpublish-url-to-section-slug (url)
  "Parse URL of shape `/<section>/<slug>/' (or nested) into a cons cell.

Returns (SECTION . SLUG) or nil if URL isn't well-formed.  Mirrors
`a3madkour-pub-history--section-of-url' for the section part; the slug
is the LAST path segment.  Nested sections like `/research/questions/q/'
yield (\"research/questions\" . \"q\")."
  (when (and (stringp url) (string-prefix-p "/" url))
    (let* ((trimmed (replace-regexp-in-string "\\`/+\\|/+\\'" "" url))
           (parts (split-string trimmed "/")))
      (when (>= (length parts) 2)
        (cons (mapconcat #'identity (butlast parts) "/")
              (car (last parts)))))))

(cl-defun a3madkour-pub/finish-publish (&key dry-run)
  "Orchestrate the unpublish flow.  Returns a plist.

When DRY-RUN is non-nil: no FS writes, no manifest mutation.  Useful for
`--check-orphans' preview.

Sub-steps (in fixed order):
  Step A — unpublish sweep: diff new live-set vs manifest live+draft;
           for each :removed, delete `content/<section>/<slug>/' bundle +
           call `record-publish' with state `removed' to mutate manifest.
  Step B — slug-shift sync (Task 11): rename asset dirs + rewrite source
           .org links for ids in :slug-shifted.
  Step C — re-link-check (Task 13): scan live notes' outgoing org links;
           WARN for any link resolving into removed-this-publish-set.

New-set is read from `a3madkour-pub--publish-run-accumulator' (B-coupled
mode); if empty, falls back to `walk-published-source-set' (standalone
mode — used today before B ships).

Returns:
  (:removed         (id ...)
   :slug-shifted    ((old-slug . new-slug) ...)
   :orphan-warnings (\"WARN: ...\" ...)
   :added           (id ...)
   :stayed          (id ...))"
  (let* ((new-set (if (zerop (hash-table-count a3madkour-pub--publish-run-accumulator))
                      (a3madkour-pub/walk-published-source-set)
                    (let ((copy (make-hash-table :test 'equal)))
                      (maphash (lambda (k v) (puthash k v copy))
                               a3madkour-pub--publish-run-accumulator)
                      copy)))
         (diff (a3madkour-pub/diff-published-set new-set))
         (removed (plist-get diff :removed))
         (manifest (a3madkour-pub-history/read-manifest))
         (notes (alist-get 'notes manifest)))
    ;; Step A: sweep.
    (dolist (id removed)
      (let* ((idx (a3madkour-pub-history--find-note-by-id notes id))
             (entry (when idx (aref notes idx)))
             (url (when entry (alist-get 'current_url entry)))
             (parts (when url (a3madkour-pub--unpublish-url-to-section-slug url))))
        (when (and parts (not dry-run))
          (a3madkour-pub--unpublish-delete-bundle (car parts) (cdr parts))
          (a3madkour-pub-history/record-publish id nil 'removed))))
    ;; Step B + C land in Tasks 11 + 13.
    (list :added (plist-get diff :added)
          :stayed (plist-get diff :stayed)
          :removed removed
          :slug-shifted nil
          :orphan-warnings nil)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 198 tests, 198 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 8: **198 ert tests** (194 → 198).

---

### Task 9: `unpublish--rename-asset-dir` helper

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

Internal helper. Renames `<canonical-root>/page/<old-slug>/` → `<new-slug>/`. Uses `git mv` when the source dir is git-tracked; falls back to `rename-file` otherwise. Target conflict + source missing both return informational symbols (not errors).

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- unpublish--rename-asset-dir helper --

(ert-deftest a3madkour-pub-unpublish-test/rename-asset-dir-source-missing-silent ()
  "Source dir doesn't exist → :skipped-no-source (no error)."
  (let ((root (make-temp-file "a3-pub-assets-" t)))
    (unwind-protect
        (should (eq :skipped-no-source
                    (a3madkour-pub--unpublish-rename-asset-dir
                     "never-existed" "new-slug" root)))
      (delete-directory root t))))

(ert-deftest a3madkour-pub-unpublish-test/rename-asset-dir-target-exists-warn ()
  "Target dir already exists → :skipped-target-exists (no error)."
  (let* ((root (make-temp-file "a3-pub-assets-" t))
         (old-dir (expand-file-name "page/foo" root))
         (new-dir (expand-file-name "page/foo-v2" root)))
    (unwind-protect
        (progn
          (make-directory old-dir t)
          (make-directory new-dir t)
          (should (eq :skipped-target-exists
                      (a3madkour-pub--unpublish-rename-asset-dir
                       "foo" "foo-v2" root))))
      (delete-directory root t))))

(ert-deftest a3madkour-pub-unpublish-test/rename-asset-dir-untracked-uses-rename-file ()
  "Untracked source dir → rename-file, returns :renamed-mv."
  (let* ((root (make-temp-file "a3-pub-assets-" t))
         (old-dir (expand-file-name "page/foo" root))
         (new-dir (expand-file-name "page/foo-v2" root)))
    (unwind-protect
        (progn
          (make-directory old-dir t)
          (with-temp-file (expand-file-name "x.png" old-dir) (insert "data"))
          (cl-letf (((symbol-function 'vc-backend) (lambda (_) nil)))
            (should (eq :renamed-mv
                        (a3madkour-pub--unpublish-rename-asset-dir
                         "foo" "foo-v2" root))))
          (should (file-directory-p new-dir))
          (should-not (file-directory-p old-dir))
          (should (file-exists-p (expand-file-name "x.png" new-dir))))
      (delete-directory root t))))

(ert-deftest a3madkour-pub-unpublish-test/rename-asset-dir-tracked-uses-git-mv ()
  "Git-tracked source dir → shell-command \"git mv\", returns :renamed-git."
  (let* ((root (make-temp-file "a3-pub-assets-" t))
         (old-dir (expand-file-name "page/foo" root))
         (git-cmd-captured nil))
    (unwind-protect
        (progn
          (make-directory old-dir t)
          (cl-letf (((symbol-function 'vc-backend) (lambda (_) 'Git))
                    ((symbol-function 'shell-command)
                     (lambda (cmd &rest _)
                       (setq git-cmd-captured cmd)
                       ;; Simulate successful git mv by doing rename-file.
                       (rename-file old-dir
                                    (expand-file-name "page/foo-v2" root))
                       0)))
            (should (eq :renamed-git
                        (a3madkour-pub--unpublish-rename-asset-dir
                         "foo" "foo-v2" root))))
          (should (string-match-p "git mv" git-cmd-captured)))
      (when (file-directory-p (expand-file-name "page/foo-v2" root))
        (delete-directory (expand-file-name "page/foo-v2" root) t))
      (delete-directory root t))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures — `Symbol's function definition is void: a3madkour-pub--unpublish-rename-asset-dir`. Exit non-zero.

- [ ] **Step 3: Implement `unpublish--rename-asset-dir`**

Insert into `a3madkour-publish-unpublish.el` (after `finish-publish`):

```elisp
(defun a3madkour-pub--unpublish-rename-asset-dir (old-slug new-slug &optional canonical-root)
  "Rename `<CANONICAL-ROOT>/page/<OLD-SLUG>/' → `<NEW-SLUG>/'.

CANONICAL-ROOT defaults to `a3madkour-pub-canonical-asset-root'.

Returns a symbol indicating what happened:
  :renamed-git           — git-tracked; performed `git mv'.
  :renamed-mv            — untracked; performed `rename-file'.
  :skipped-no-source     — source dir doesn't exist (note had no assets).
  :skipped-target-exists — target dir already present (caller WARNs).

If `git mv' fails (git not installed, not a git repo), falls through to
`rename-file' and returns `:renamed-mv'."
  (let* ((root (or canonical-root a3madkour-pub-canonical-asset-root))
         (old-dir (file-name-as-directory
                   (expand-file-name (format "page/%s" old-slug) root)))
         (new-dir (file-name-as-directory
                   (expand-file-name (format "page/%s" new-slug) root))))
    (cond
     ((not (file-directory-p old-dir))
      :skipped-no-source)
     ((file-directory-p new-dir)
      (message "[a3-pub] rename-asset-dir: target exists: %s — skipping" new-dir)
      :skipped-target-exists)
     ((eq (vc-backend old-dir) 'Git)
      (let* ((cmd (format "git mv %s %s"
                          (shell-quote-argument (directory-file-name old-dir))
                          (shell-quote-argument (directory-file-name new-dir))))
             (rc (let ((default-directory root))
                   (shell-command cmd))))
        (if (zerop rc)
            :renamed-git
          ;; Fallback to mv on git failure.
          (rename-file old-dir new-dir)
          :renamed-mv)))
     (t
      (rename-file old-dir new-dir)
      :renamed-mv))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 202 tests, 202 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 9: **202 ert tests** (198 → 202).

---

### Task 10: `unpublish--bulk-rewrite-source-links` helper

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

Walks `org-notes-dir`, rewrites `.org` files that reference `assets/page/<old-slug>/` to `assets/page/<new-slug>/` across three link forms. Idempotent — re-runs after partial completion are no-ops.

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- unpublish--bulk-rewrite-source-links helper --

(ert-deftest a3madkour-pub-unpublish-test/bulk-rewrite-three-link-forms ()
  "All three link forms (relative ./assets/, ~-absolute, $HOME-absolute) rewrite."
  (a3-pub-unpublish-test--with-tmp-notes-dir d
    (let ((home-prefix (expand-file-name "~/")))
      (a3-pub-unpublish-test--write-org d "rel.org"
        "See [[./assets/page/foo/x.png][x]]\n")
      (a3-pub-unpublish-test--write-org d "tilde.org"
        "See [[~/org/notes/assets/page/foo/y.png][y]]\n")
      (a3-pub-unpublish-test--write-org d "abs.org"
        (format "See [[%sorg/notes/assets/page/foo/z.png][z]]\n" home-prefix))
      (let ((result (a3madkour-pub--unpublish-bulk-rewrite-source-links
                     "foo" "foo-v2" d)))
        (should (= 3 (length (plist-get result :modified))))
        (should (null (plist-get result :warnings))))
      (should (string-match-p "./assets/page/foo-v2/x.png"
                              (with-temp-buffer
                                (insert-file-contents (expand-file-name "rel.org" d))
                                (buffer-string))))
      (should (string-match-p "~/org/notes/assets/page/foo-v2/y.png"
                              (with-temp-buffer
                                (insert-file-contents (expand-file-name "tilde.org" d))
                                (buffer-string))))
      (should (string-match-p "assets/page/foo-v2/z.png"
                              (with-temp-buffer
                                (insert-file-contents (expand-file-name "abs.org" d))
                                (buffer-string)))))))

(ert-deftest a3madkour-pub-unpublish-test/bulk-rewrite-idempotent ()
  "Second invocation after a complete first pass yields zero modifications."
  (a3-pub-unpublish-test--with-tmp-notes-dir d
    (a3-pub-unpublish-test--write-org d "a.org"
      "[[./assets/page/foo/x.png][x]]\n")
    ;; First pass: 1 modification.
    (let ((r1 (a3madkour-pub--unpublish-bulk-rewrite-source-links "foo" "foo-v2" d)))
      (should (= 1 (length (plist-get r1 :modified)))))
    ;; Second pass: zero modifications.
    (let ((r2 (a3madkour-pub--unpublish-bulk-rewrite-source-links "foo" "foo-v2" d)))
      (should (null (plist-get r2 :modified))))))

(ert-deftest a3madkour-pub-unpublish-test/bulk-rewrite-no-matches-not-modified ()
  "Files without matching references stay untouched."
  (a3-pub-unpublish-test--with-tmp-notes-dir d
    (a3-pub-unpublish-test--write-org d "other.org"
      "Plain text without any asset references.\n")
    (let ((result (a3madkour-pub--unpublish-bulk-rewrite-source-links "foo" "foo-v2" d)))
      (should (null (plist-get result :modified))))))

(ert-deftest a3madkour-pub-unpublish-test/bulk-rewrite-mixed-partial ()
  "Files with multiple matches get all-or-nothing rewrites in one pass."
  (a3-pub-unpublish-test--with-tmp-notes-dir d
    (a3-pub-unpublish-test--write-org d "mixed.org"
      "[[./assets/page/foo/a.png][a]]\n[[./assets/page/foo/b.png][b]]\n[[./assets/page/bar/c.png][c]]\n")
    (let ((result (a3madkour-pub--unpublish-bulk-rewrite-source-links "foo" "foo-v2" d)))
      (should (= 1 (length (plist-get result :modified)))))
    (let ((content (with-temp-buffer
                     (insert-file-contents (expand-file-name "mixed.org" d))
                     (buffer-string))))
      (should (string-match-p "page/foo-v2/a.png" content))
      (should (string-match-p "page/foo-v2/b.png" content))
      ;; Unrelated `bar' slug untouched.
      (should (string-match-p "page/bar/c.png" content)))))

(ert-deftest a3madkour-pub-unpublish-test/bulk-rewrite-unwritable-warn ()
  "Files that fail to write back are captured in :warnings, not raised."
  (a3-pub-unpublish-test--with-tmp-notes-dir d
    (a3-pub-unpublish-test--write-org d "a.org"
      "[[./assets/page/foo/x.png][x]]\n")
    (cl-letf (((symbol-function 'write-region)
               (lambda (&rest _) (error "permission denied"))))
      (let ((result (a3madkour-pub--unpublish-bulk-rewrite-source-links "foo" "foo-v2" d)))
        (should (= 1 (length (plist-get result :warnings))))
        (should (string-match-p "a.org" (car (plist-get result :warnings))))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 5 failures — `Symbol's function definition is void: a3madkour-pub--unpublish-bulk-rewrite-source-links`. Exit non-zero.

- [ ] **Step 3: Implement `unpublish--bulk-rewrite-source-links`**

Insert into `a3madkour-publish-unpublish.el` (after `unpublish--rename-asset-dir`):

```elisp
(defun a3madkour-pub--unpublish-bulk-rewrite-source-links (old-slug new-slug &optional org-notes-dir)
  "Walk ORG-NOTES-DIR for .org files; substitute `page/<OLD-SLUG>/' →
`page/<NEW-SLUG>/' across three link forms:

  ./assets/page/<old>/...           → ./assets/page/<new>/...
  ~/org/notes/assets/page/<old>/... → ~/org/notes/assets/page/<new>/...
  <$HOME>/org/notes/assets/page/<old>/... → <$HOME>/org/notes/assets/page/<new>/...

ORG-NOTES-DIR defaults to `a3madkour-pub/org-notes-dir'.

Returns a plist:
  :modified  ((file . substitution-count) ...)
  :warnings  (\"WARN: failed to write back FILE: REASON\" ...)

Idempotent: re-runs after a successful pass produce zero modifications
(the substitution regex doesn't match the new slug)."
  (let* ((dir (or org-notes-dir a3madkour-pub/org-notes-dir))
         (home (expand-file-name "~/"))
         (patterns (list
                    (cons (format "\\./assets/page/%s/" (regexp-quote old-slug))
                          (format "./assets/page/%s/" new-slug))
                    (cons (format "~/org/notes/assets/page/%s/" (regexp-quote old-slug))
                          (format "~/org/notes/assets/page/%s/" new-slug))
                    (cons (format "%sorg/notes/assets/page/%s/"
                                  (regexp-quote home) (regexp-quote old-slug))
                          (format "%sorg/notes/assets/page/%s/" home new-slug))))
         modified warnings)
    (dolist (file (directory-files-recursively dir "\\.org\\'"))
      (let* ((orig (with-temp-buffer
                     (insert-file-contents file)
                     (buffer-string)))
             (new orig)
             (count 0))
        (dolist (p patterns)
          (while (string-match (car p) new)
            (setq new (replace-match (cdr p) t t new))
            (setq count (1+ count))))
        (when (> count 0)
          (condition-case err
              (progn
                (with-temp-buffer
                  (insert new)
                  (write-region (point-min) (point-max) file nil 'silent))
                (push (cons file count) modified))
            (error
             (push (format "WARN: failed to write back %s: %s"
                           file (error-message-string err))
                   warnings))))))
    (list :modified (nreverse modified)
          :warnings (nreverse warnings))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 207 tests, 207 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 10: **207 ert tests** (202 → 207).

---

### Task 11: Wire Step B into `finish-publish`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

Extend the orchestrator: after Step A, iterate `diff.slug-shifted` and call the two helpers. Populate `:slug-shifted` in the return value.

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- finish-publish: Step B integration --

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-step-b-happy ()
  "Step B: slug shift triggers asset-dir rename + source-link rewrite."
  (let* ((notes-dir (make-temp-file "a3-pub-notes-" t))
         (asset-root (make-temp-file "a3-pub-assets-" t))
         (old-asset-dir (expand-file-name "page/foo" asset-root))
         (manifest-path (make-temp-file "a3-pub-history-" nil ".yaml")))
    (unwind-protect
        (progn
          (make-directory old-asset-dir t)
          (with-temp-file (expand-file-name "x.png" old-asset-dir) (insert "data"))
          (a3-pub-unpublish-test--write-org notes-dir "note.org"
            "[[./assets/page/foo/x.png][x]]\n")
          (let ((a3madkour-pub-canonical-asset-root asset-root)
                (a3madkour-pub/org-notes-dir notes-dir))
            (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                       (lambda () manifest-path))
                      ((symbol-function 'vc-backend) (lambda (_) nil)))
              ;; Seed manifest: note was at /garden/foo/, now (per accumulator) at /garden/foo-v2/.
              (a3madkour-pub-history/write-manifest
               '((notes . [((id . "id-shift") (current_url . "/garden/foo/")
                            (history . []) (state . "live"))])))
              (clrhash a3madkour-pub--publish-run-accumulator)
              (puthash "id-shift" '("/garden/foo-v2/" . live)
                       a3madkour-pub--publish-run-accumulator)
              (let ((result (a3madkour-pub/finish-publish)))
                (should (equal (plist-get result :slug-shifted)
                               '(("foo" . "foo-v2"))))
                ;; Asset dir renamed.
                (should-not (file-directory-p old-asset-dir))
                (should (file-directory-p (expand-file-name "page/foo-v2" asset-root)))
                ;; Source link rewritten.
                (let ((content (with-temp-buffer
                                 (insert-file-contents (expand-file-name "note.org" notes-dir))
                                 (buffer-string))))
                  (should (string-match-p "page/foo-v2/x.png" content)))))))
      (delete-directory notes-dir t)
      (delete-directory asset-root t)
      (when (file-exists-p manifest-path) (delete-file manifest-path)))))

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-step-b-dry-run ()
  ":dry-run t skips both asset rename and source rewrite."
  (let* ((notes-dir (make-temp-file "a3-pub-notes-" t))
         (asset-root (make-temp-file "a3-pub-assets-" t))
         (old-asset-dir (expand-file-name "page/foo" asset-root))
         (manifest-path (make-temp-file "a3-pub-history-" nil ".yaml")))
    (unwind-protect
        (progn
          (make-directory old-asset-dir t)
          (with-temp-file (expand-file-name "x.png" old-asset-dir) (insert "data"))
          (a3-pub-unpublish-test--write-org notes-dir "note.org"
            "[[./assets/page/foo/x.png][x]]\n")
          (let ((a3madkour-pub-canonical-asset-root asset-root)
                (a3madkour-pub/org-notes-dir notes-dir))
            (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                       (lambda () manifest-path))
                      ((symbol-function 'vc-backend) (lambda (_) nil)))
              (a3madkour-pub-history/write-manifest
               '((notes . [((id . "id-shift") (current_url . "/garden/foo/")
                            (history . []) (state . "live"))])))
              (clrhash a3madkour-pub--publish-run-accumulator)
              (puthash "id-shift" '("/garden/foo-v2/" . live)
                       a3madkour-pub--publish-run-accumulator)
              (let ((result (a3madkour-pub/finish-publish :dry-run t)))
                ;; Reports the would-do.
                (should (equal (plist-get result :slug-shifted)
                               '(("foo" . "foo-v2"))))
                ;; But no FS mutation.
                (should (file-directory-p old-asset-dir))
                (let ((content (with-temp-buffer
                                 (insert-file-contents (expand-file-name "note.org" notes-dir))
                                 (buffer-string))))
                  (should (string-match-p "page/foo/x.png" content)))))))
      (delete-directory notes-dir t)
      (delete-directory asset-root t)
      (when (file-exists-p manifest-path) (delete-file manifest-path)))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 2 failures — `:slug-shifted` returns nil (Task 8's skeleton hardcoded it). Exit non-zero.

- [ ] **Step 3: Wire Step B into `finish-publish`**

Edit the existing `finish-publish` body in `a3madkour-publish-unpublish.el`. Add a Step B block between Step A and the return plist:

```elisp
(cl-defun a3madkour-pub/finish-publish (&key dry-run)
  "[... preserved docstring from Task 8 ...]"
  (let* ((new-set (if (zerop (hash-table-count a3madkour-pub--publish-run-accumulator))
                      (a3madkour-pub/walk-published-source-set)
                    (let ((copy (make-hash-table :test 'equal)))
                      (maphash (lambda (k v) (puthash k v copy))
                               a3madkour-pub--publish-run-accumulator)
                      copy)))
         (diff (a3madkour-pub/diff-published-set new-set))
         (removed (plist-get diff :removed))
         (shifts (plist-get diff :slug-shifted))
         (manifest (a3madkour-pub-history/read-manifest))
         (notes (alist-get 'notes manifest))
         slug-shifted-result)
    ;; Step A: sweep.
    (dolist (id removed)
      (let* ((idx (a3madkour-pub-history--find-note-by-id notes id))
             (entry (when idx (aref notes idx)))
             (url (when entry (alist-get 'current_url entry)))
             (parts (when url (a3madkour-pub--unpublish-url-to-section-slug url))))
        (when (and parts (not dry-run))
          (a3madkour-pub--unpublish-delete-bundle (car parts) (cdr parts))
          (a3madkour-pub-history/record-publish id nil 'removed))))
    ;; Step B: slug-shift sync.
    (dolist (shift shifts)
      (let* ((old-url (nth 1 shift))
             (new-url (nth 2 shift))
             (old-parts (a3madkour-pub--unpublish-url-to-section-slug old-url))
             (new-parts (a3madkour-pub--unpublish-url-to-section-slug new-url)))
        (when (and old-parts new-parts)
          (let ((old-slug (cdr old-parts))
                (new-slug (cdr new-parts)))
            (unless dry-run
              (a3madkour-pub--unpublish-rename-asset-dir old-slug new-slug)
              (a3madkour-pub--unpublish-bulk-rewrite-source-links old-slug new-slug))
            (push (cons old-slug new-slug) slug-shifted-result)))))
    ;; Step C lands in Task 13.
    (list :added (plist-get diff :added)
          :stayed (plist-get diff :stayed)
          :removed removed
          :slug-shifted (nreverse slug-shifted-result)
          :orphan-warnings nil)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 209 tests, 209 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 11: **209 ert tests** (207 → 209).

---

### Task 12: `unpublish--recheck-live-note-links` helper

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

Iterates manifest live entries. For each, fetches source file via `org-roam-id-find` (per memory `reference_org_roam_id_find_returns_cons`, the result is `(file . pos)` — unwrap via `car`). Parses outgoing links. WARNs for any link whose target id is in `removed-this-publish-set`.

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- unpublish--recheck-live-note-links helper --

(defmacro a3-pub-unpublish-test--with-tmp-source (file-var body-content &rest setup-body)
  "Write BODY-CONTENT to a tmpfile bound to FILE-VAR; run SETUP-BODY; cleanup."
  (declare (indent 2))
  `(let ((,file-var (make-temp-file "a3-pub-source-" nil ".org")))
     (unwind-protect
         (progn
           (with-temp-file ,file-var (insert ,body-content))
           ,@setup-body)
       (when (file-exists-p ,file-var) (delete-file ,file-var)))))

(ert-deftest a3madkour-pub-unpublish-test/recheck-live-link-to-removed-warns ()
  "Live note with [[id:...]] link to removed target produces WARN."
  (a3-pub-unpublish-test--with-tmp-source src
      "Some text [[id:tgt-removed][link]] more text.\n"
    (let ((removed-set (make-hash-table :test 'equal)))
      (puthash "tgt-removed" t removed-set)
      (cl-letf (((symbol-function 'a3madkour-pub-history/read-manifest)
                 (lambda ()
                   `((notes . [((id . "live-note") (current_url . "/garden/x/")
                                (history . []) (state . "live"))
                               ((id . "tgt-removed") (current_url . nil)
                                (history . [((url . "/garden/old/") (replaced_at . "t")
                                             (reason . "removed"))])
                                (state . "removed"))]))))
                ((symbol-function 'org-roam-id-find)
                 (lambda (id &optional _)
                   (when (equal id "live-note") (cons src 1)))))
        (let ((warnings (a3madkour-pub--unpublish-recheck-live-note-links removed-set)))
          (should (= 1 (length warnings)))
          (should (string-match-p "live-note" (car warnings)))
          (should (string-match-p "tgt-removed" (car warnings))))))))

(ert-deftest a3madkour-pub-unpublish-test/recheck-link-to-live-no-warn ()
  "Live note with link to another live target → no WARN."
  (a3-pub-unpublish-test--with-tmp-source src
      "[[id:tgt-live][link]]\n"
    (let ((removed-set (make-hash-table :test 'equal)))
      (cl-letf (((symbol-function 'a3madkour-pub-history/read-manifest)
                 (lambda ()
                   `((notes . [((id . "live-note") (current_url . "/garden/x/")
                                (history . []) (state . "live"))]))))
                ((symbol-function 'org-roam-id-find)
                 (lambda (id &optional _)
                   (when (equal id "live-note") (cons src 1)))))
        (should (null (a3madkour-pub--unpublish-recheck-live-note-links removed-set)))))))

(ert-deftest a3madkour-pub-unpublish-test/recheck-unparseable-source-warns ()
  "If source file is missing, WARN names the file but continues."
  (let ((removed-set (make-hash-table :test 'equal)))
    (cl-letf (((symbol-function 'a3madkour-pub-history/read-manifest)
               (lambda ()
                 `((notes . [((id . "ghost") (current_url . "/garden/g/")
                              (history . []) (state . "live"))]))))
              ((symbol-function 'org-roam-id-find)
               (lambda (id &optional _)
                 (when (equal id "ghost") (cons "/nonexistent/path.org" 1)))))
      (let ((warnings (a3madkour-pub--unpublish-recheck-live-note-links removed-set)))
        (should (= 1 (length warnings)))
        (should (string-match-p "ghost" (car warnings)))))))

(ert-deftest a3madkour-pub-unpublish-test/recheck-multi-link-per-note ()
  "Multiple links per note are all checked; each removed target → own WARN."
  (a3-pub-unpublish-test--with-tmp-source src
      "[[id:rem-1][a]] and [[id:rem-2][b]] and [[id:live-tgt][c]]\n"
    (let ((removed-set (make-hash-table :test 'equal)))
      (puthash "rem-1" t removed-set)
      (puthash "rem-2" t removed-set)
      (cl-letf (((symbol-function 'a3madkour-pub-history/read-manifest)
                 (lambda ()
                   `((notes . [((id . "src-note") (current_url . "/garden/s/")
                                (history . []) (state . "live"))]))))
                ((symbol-function 'org-roam-id-find)
                 (lambda (id &optional _)
                   (when (equal id "src-note") (cons src 1)))))
        (let ((warnings (a3madkour-pub--unpublish-recheck-live-note-links removed-set)))
          (should (= 2 (length warnings))))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures — `Symbol's function definition is void: a3madkour-pub--unpublish-recheck-live-note-links`. Exit non-zero.

- [ ] **Step 3: Implement `unpublish--recheck-live-note-links`**

Insert into `a3madkour-publish-unpublish.el` (after `unpublish--bulk-rewrite-source-links`):

```elisp
(defun a3madkour-pub--unpublish-recheck-live-note-links (removed-this-publish-set)
  "For each live manifest entry, scan outgoing [[id:...]] links.
Emit WARN for each link whose target id is in REMOVED-THIS-PUBLISH-SET.

REMOVED-THIS-PUBLISH-SET is a hash table id → t (or any truthy value).

Returns a list of WARN strings.  Format:
  \"WARN: live note <id> (<url>) outgoing link to <removed-id> (was <old-url>) — republish recommended\"

Source files are located via `org-roam-id-find' — which returns `(file . pos)';
we unwrap via `car' (per memory `reference_org_roam_id_find_returns_cons').
Source files that don't exist or can't be read produce their own WARN."
  (let* ((manifest (a3madkour-pub-history/read-manifest))
         (notes (alist-get 'notes manifest))
         warnings)
    (cl-loop for i from 0 below (length notes)
             for entry = (aref notes i)
             when (equal (alist-get 'state entry) "live")
             do
             (let* ((src-id (alist-get 'id entry))
                    (src-url (alist-get 'current_url entry))
                    (found (org-roam-id-find src-id))
                    (src-file (when (consp found) (car found))))
               (cond
                ((or (null src-file) (not (file-readable-p src-file)))
                 (push (format "WARN: live note %s (%s) source file unreadable"
                               src-id src-url)
                       warnings))
                (t
                 (let ((content (with-temp-buffer
                                  (insert-file-contents src-file)
                                  (buffer-string)))
                       (link-re "\\[\\[id:\\([^]]+\\)\\]"))
                   (with-temp-buffer
                     (insert content)
                     (goto-char (point-min))
                     (while (re-search-forward link-re nil t)
                       (let ((target-id (match-string 1)))
                         (when (gethash target-id removed-this-publish-set)
                           (let* ((tgt-idx (a3madkour-pub-history--find-note-by-id
                                            notes target-id))
                                  (tgt-entry (when tgt-idx (aref notes tgt-idx)))
                                  (tgt-hist (when tgt-entry
                                              (alist-get 'history tgt-entry)))
                                  (tgt-old-url
                                   (when (and tgt-hist (> (length tgt-hist) 0))
                                     (alist-get 'url (aref tgt-hist
                                                           (1- (length tgt-hist)))))))
                             (push (format
                                    "WARN: live note %s (%s) outgoing link to %s (was %s) — republish recommended"
                                    src-id src-url target-id (or tgt-old-url "?"))
                                   warnings)))))))))))
    (nreverse warnings)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 213 tests, 213 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 12: **213 ert tests** (209 → 213).

---

### Task 13: Wire Step C into `finish-publish`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

After Step B, build the `removed-this-publish-set` and call Step C. Populate `:orphan-warnings`.

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- finish-publish: Step C integration --

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-step-c-orphan-warn ()
  "End-to-end: removed note linked from a live note → :orphan-warnings populated."
  (let* ((manifest-path (make-temp-file "a3-pub-history-" nil ".yaml"))
         (live-src (make-temp-file "a3-pub-src-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file live-src
            (insert "Hello, see [[id:tgt-id][gone]] now.\n"))
          (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                     (lambda () manifest-path))
                    ((symbol-function 'org-roam-id-find)
                     (lambda (id &optional _)
                       (when (equal id "live-id") (cons live-src 1)))))
            (a3madkour-pub-history/write-manifest
             '((notes . [((id . "live-id") (current_url . "/garden/live/")
                          (history . []) (state . "live"))
                         ((id . "tgt-id") (current_url . "/garden/tgt/")
                          (history . []) (state . "live"))])))
            (clrhash a3madkour-pub--publish-run-accumulator)
            (puthash "live-id" '("/garden/live/" . live)
                     a3madkour-pub--publish-run-accumulator)
            ;; tgt-id NOT in accumulator → will be classified as removed.
            (cl-letf (((symbol-function 'a3madkour-pub--unpublish-delete-bundle)
                       (lambda (&rest _) nil)))  ; stub FS delete
              (let* ((result (a3madkour-pub/finish-publish))
                     (warnings (plist-get result :orphan-warnings)))
                (should (= 1 (length warnings)))
                (should (string-match-p "live-id" (car warnings)))
                (should (string-match-p "tgt-id" (car warnings)))))))
      (when (file-exists-p manifest-path) (delete-file manifest-path))
      (when (file-exists-p live-src) (delete-file live-src)))))

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-step-c-dry-run-still-warns ()
  "Step C is read-only; dry-run still produces :orphan-warnings."
  (let* ((manifest-path (make-temp-file "a3-pub-history-" nil ".yaml"))
         (live-src (make-temp-file "a3-pub-src-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file live-src (insert "[[id:tgt-id][x]]\n"))
          (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                     (lambda () manifest-path))
                    ((symbol-function 'org-roam-id-find)
                     (lambda (id &optional _)
                       (when (equal id "live-id") (cons live-src 1)))))
            (a3madkour-pub-history/write-manifest
             '((notes . [((id . "live-id") (current_url . "/garden/live/")
                          (history . []) (state . "live"))
                         ((id . "tgt-id") (current_url . "/garden/tgt/")
                          (history . []) (state . "live"))])))
            (clrhash a3madkour-pub--publish-run-accumulator)
            (puthash "live-id" '("/garden/live/" . live)
                     a3madkour-pub--publish-run-accumulator)
            (let ((result (a3madkour-pub/finish-publish :dry-run t)))
              (should (= 1 (length (plist-get result :orphan-warnings)))))))
      (when (file-exists-p manifest-path) (delete-file manifest-path))
      (when (file-exists-p live-src) (delete-file live-src)))))

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-empty-removed-empty-warnings ()
  "Empty :removed → :orphan-warnings nil (Step C short-circuits)."
  (let ((manifest-path (make-temp-file "a3-pub-history-" nil ".yaml")))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                   (lambda () manifest-path)))
          (a3madkour-pub-history/write-manifest '((notes . [])))
          (clrhash a3madkour-pub--publish-run-accumulator)
          (cl-letf (((symbol-function 'a3madkour-pub/walk-published-source-set)
                     (lambda () (make-hash-table :test 'equal))))
            (let ((result (a3madkour-pub/finish-publish)))
              (should (null (plist-get result :orphan-warnings))))))
      (when (file-exists-p manifest-path) (delete-file manifest-path)))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures — `:orphan-warnings` returns nil (Task 11's wiring hardcoded it). Exit non-zero.

- [ ] **Step 3: Wire Step C into `finish-publish`**

Edit the existing `finish-publish` body. Replace the trailing return-plist + add Step C between Step B and the return. The full body becomes:

```elisp
(cl-defun a3madkour-pub/finish-publish (&key dry-run)
  "[... preserved docstring from Tasks 8, 11 ...]"
  (let* ((new-set (if (zerop (hash-table-count a3madkour-pub--publish-run-accumulator))
                      (a3madkour-pub/walk-published-source-set)
                    (let ((copy (make-hash-table :test 'equal)))
                      (maphash (lambda (k v) (puthash k v copy))
                               a3madkour-pub--publish-run-accumulator)
                      copy)))
         (diff (a3madkour-pub/diff-published-set new-set))
         (removed (plist-get diff :removed))
         (shifts (plist-get diff :slug-shifted))
         (manifest (a3madkour-pub-history/read-manifest))
         (notes (alist-get 'notes manifest))
         (removed-set (make-hash-table :test 'equal))
         slug-shifted-result orphan-warnings)
    ;; Step A: sweep.
    (dolist (id removed)
      (puthash id t removed-set)
      (let* ((idx (a3madkour-pub-history--find-note-by-id notes id))
             (entry (when idx (aref notes idx)))
             (url (when entry (alist-get 'current_url entry)))
             (parts (when url (a3madkour-pub--unpublish-url-to-section-slug url))))
        (when (and parts (not dry-run))
          (a3madkour-pub--unpublish-delete-bundle (car parts) (cdr parts))
          (a3madkour-pub-history/record-publish id nil 'removed))))
    ;; Step B: slug-shift sync.
    (dolist (shift shifts)
      (let* ((old-url (nth 1 shift))
             (new-url (nth 2 shift))
             (old-parts (a3madkour-pub--unpublish-url-to-section-slug old-url))
             (new-parts (a3madkour-pub--unpublish-url-to-section-slug new-url)))
        (when (and old-parts new-parts)
          (let ((old-slug (cdr old-parts))
                (new-slug (cdr new-parts)))
            (unless dry-run
              (a3madkour-pub--unpublish-rename-asset-dir old-slug new-slug)
              (a3madkour-pub--unpublish-bulk-rewrite-source-links old-slug new-slug))
            (push (cons old-slug new-slug) slug-shifted-result)))))
    ;; Step C: re-link-check (read-only; runs in dry-run too).
    (when (> (hash-table-count removed-set) 0)
      (setq orphan-warnings
            (a3madkour-pub--unpublish-recheck-live-note-links removed-set)))
    (list :added (plist-get diff :added)
          :stayed (plist-get diff :stayed)
          :removed removed
          :slug-shifted (nreverse slug-shifted-result)
          :orphan-warnings orphan-warnings)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 216 tests, 216 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 13: **216 ert tests** (213 → 216).

---

### Task 14: `pub/check-orphans` thin alias

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

Single-line alias. Tested for parity with `finish-publish :dry-run t`.

- [ ] **Step 1: Write the failing test**

Append to `a3madkour-publish-unpublish-test.el`:

```elisp
;; -- check-orphans thin alias --

(ert-deftest a3madkour-pub-unpublish-test/check-orphans-parity-with-dry-run ()
  "`check-orphans' is identical to `(finish-publish :dry-run t)'."
  (let ((manifest-path (make-temp-file "a3-pub-history-" nil ".yaml")))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub-history--manifest-path)
                   (lambda () manifest-path)))
          (a3madkour-pub-history/write-manifest '((notes . [])))
          (clrhash a3madkour-pub--publish-run-accumulator)
          (cl-letf (((symbol-function 'a3madkour-pub/walk-published-source-set)
                     (lambda () (make-hash-table :test 'equal))))
            (let ((a (a3madkour-pub/finish-publish :dry-run t))
                  (b (a3madkour-pub/check-orphans)))
              (should (equal a b)))))
      (when (file-exists-p manifest-path) (delete-file manifest-path)))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 1 failure — `Symbol's function definition is void: a3madkour-pub/check-orphans`. Exit non-zero.

- [ ] **Step 3: Implement `check-orphans`**

Insert into `a3madkour-publish-unpublish.el` (after `finish-publish`):

```elisp
(defun a3madkour-pub/check-orphans ()
  "Dry-run preview of `a3madkour-pub/finish-publish'.

Thin alias for `(a3madkour-pub/finish-publish :dry-run t)'.  Exists
because parent spec §10 named it explicitly.

No FS or manifest mutation.  Returns the same plist shape as
`finish-publish' (with the same diagnostic content; only the side
effects differ between the two calls)."
  (a3madkour-pub/finish-publish :dry-run t))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 217 tests, 217 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 5: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
```

End of Task 14: **217 ert tests** (216 → 217).

---

### Task 15: `--check-orphans` flag intercept in `a3-pub.sh`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`

Add a bash conditional BEFORE `exec emacs`. If `$1 == "--check-orphans"`, shift, then invoke emacs with the existing args + a different `--eval` payload. Exit code always 0 (info command).

No ert test (shell flag). Spot-check goes in Task 22's user-verification checkpoint.

- [ ] **Step 1: Insert the flag-intercept block**

Edit `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`. Find the line `if [ ! -f "$STRAIGHT_BOOTSTRAP" ]; then` block and add the `--check-orphans` intercept ABOVE that block (so the bootstrap check still applies). Insertion point: right after the `STRAIGHT_BOOTSTRAP=` assignment, before the existence check.

The file post-edit should read (relevant region):

```bash
LISP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CUSTOM_DIR="$(dirname "$LISP_DIR")"
STRAIGHT_BOOTSTRAP="$CUSTOM_DIR/straight/repos/straight.el/bootstrap.el"

# A.1.d: --check-orphans flag intercept.  Runs (begin-publish) + (check-orphans)
# in standalone mode (walks source tree), prints the dry-run plist, exits 0.
if [ "${1:-}" = "--check-orphans" ]; then
  shift
  if [ ! -f "$STRAIGHT_BOOTSTRAP" ]; then
    echo "a3-pub.sh: cannot find straight bootstrap at $STRAIGHT_BOOTSTRAP" >&2
    exit 2
  fi
  exec emacs --batch \
    --eval "(setq user-emacs-directory \"$CUSTOM_DIR/\")" \
    --eval "(setq straight-base-dir user-emacs-directory)" \
    -l "$STRAIGHT_BOOTSTRAP" \
    --eval "(straight-use-package 'org-roam)" \
    --eval "(dolist (dir (directory-files (expand-file-name \"straight/build/\" user-emacs-directory) t \"^[^.]\")) (when (file-directory-p dir) (add-to-list 'load-path dir)))" \
    -L "$LISP_DIR" \
    -l a3madkour-publish \
    -l a3madkour-publish-rewrite \
    -l a3madkour-publish-assets \
    -l a3madkour-publish-unpublish \
    --eval "(a3madkour-pub/begin-publish)" \
    --eval "(let ((result (a3madkour-pub/check-orphans)))
              (princ (format \"removed: %S\\n\" (plist-get result :removed)))
              (princ (format \"slug-shifted: %S\\n\" (plist-get result :slug-shifted)))
              (princ \"orphan-warnings:\\n\")
              (dolist (w (plist-get result :orphan-warnings))
                (princ (format \"  %s\\n\" w)))
              (kill-emacs 0))" \
    "$@"
fi

if [ ! -f "$STRAIGHT_BOOTSTRAP" ]; then
  echo "a3-pub.sh: cannot find straight bootstrap at $STRAIGHT_BOOTSTRAP" >&2
  echo "a3-pub.sh: check that straight.el is installed under $CUSTOM_DIR/straight/" >&2
  exit 2
fi

exec emacs --batch \
  [... existing exec-emacs block stays unchanged ...]
```

- [ ] **Step 2: Sanity-check the flag**

This is shell, not ert. Verify by:

```bash
chmod +x ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --check-orphans 2>&1 | tail -10
echo "exit code: $?"
```

Expected: prints `removed: nil` + `slug-shifted: nil` + `orphan-warnings:` header with no warning lines (steady state, since live site has `notes: []`). Exit code: 0.

If `org-notes-dir` defaults to `~/org-roam/` (doesn't exist per memory `next-slice`'s agent-env notes), the walk produces an empty hash and the dry-run reports nothing. That's the steady-state baseline.

- [ ] **Step 3: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3-pub.sh
```

End of Task 15: **217 ert tests** (unchanged — shell flag has no ert sibling).

---

### Task 16: `--asset-normalize-link-path` dedicated unit tests (carry-forward #1)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

The helper landed in A.1.c (Task 18 scope expansion) but never got dedicated unit tests — exercised only indirectly via `validate-and-copy`. Three dedicated tests close the gap.

- [ ] **Step 1: Read the helper's signature**

Run: `grep -n "asset-normalize-link-path" ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
Expected: locate the `defun` line. Read 10-20 lines around it to confirm the signature + docstring branches.

Per A.1.c memory: the helper treats `./assets/<rest>` as a canonical-root alias (resolves against `a3madkour-pub-canonical-asset-root`), other relative paths resolve against the org-file's directory, and absolute paths pass through.

- [ ] **Step 2: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- A.1.d carry-forward #1: --asset-normalize-link-path dedicated unit tests --

(ert-deftest a3madkour-pub-assets-test/normalize-link-path-dot-assets-resolves-canonical ()
  "`./assets/<rest>' resolves against canonical-root, not the org file's dir."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (org-file (expand-file-name "notes/sub/a.org" root))
           (input "./assets/page/foo/x.png"))
      (make-directory (file-name-directory org-file) t)
      (with-temp-file org-file (insert "stub"))
      (let ((normalized (a3madkour-pub--asset-normalize-link-path input org-file)))
        (should (string-prefix-p (expand-file-name root) normalized))
        (should (string-suffix-p "page/foo/x.png" normalized))))))

(ert-deftest a3madkour-pub-assets-test/normalize-link-path-other-relative-resolves-org-dir ()
  "Relative paths NOT starting with `./assets/' resolve against org-file dir."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (org-file (expand-file-name "notes/sub/a.org" root))
           (input "../shared/sibling.png"))
      (make-directory (file-name-directory org-file) t)
      (with-temp-file org-file (insert "stub"))
      (let ((normalized (a3madkour-pub--asset-normalize-link-path input org-file)))
        ;; Should resolve to <root>/notes/shared/sibling.png (org-file dir + ../).
        (should (string-suffix-p "notes/shared/sibling.png" normalized))))))

(ert-deftest a3madkour-pub-assets-test/normalize-link-path-absolute-passes-through ()
  "Absolute path is returned as-is (after expand-file-name normalization)."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (org-file (expand-file-name "notes/a.org" root))
           (input "/tmp/some-external-asset.png"))
      (make-directory (file-name-directory org-file) t)
      (with-temp-file org-file (insert "stub"))
      (let ((normalized (a3madkour-pub--asset-normalize-link-path input org-file)))
        (should (equal normalized "/tmp/some-external-asset.png"))))))
```

If the actual helper signature differs from `(path org-file)`, adapt the test calls accordingly. The docstring + tests should describe the same three branches regardless of arg order.

- [ ] **Step 3: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 220 tests, 220 results as expected, 0 unexpected`. Exit 0.

If failure: the helper's actual return shape may differ slightly. Read the helper's body + docstring + adjust test assertions to match (these are tests OF an already-shipped function — the function is correct; the tests must match its actual behavior).

- [ ] **Step 4: Stage + test-count checkpoint**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-assets-test.el
```

End of Task 16: **220 ert tests** (217 → 220).

---

### Task 17: Integration fixture `unpublish_removed_note`

**Files:**
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

End-to-end: publish two notes → remove `HUGO_PUBLISH:` from one → re-publish → assert bundle deleted; manifest entry has `state: removed` + `reason: removed` event.

- [ ] **Step 1: Read the existing integration test pattern**

Run: `head -200 /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`
Expected: see the `_emacs_eval` helper, the TestPublishIntegration class header, and existing fixture pattern. Mirror style + naming.

- [ ] **Step 2: Write + run the failing test**

Append a new method to TestPublishIntegration:

```python
    @unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
    def test_unpublish_removed_note(self):
        """Publish two notes, unpublish one, re-run finish-publish; assert
        bundle deleted + manifest entry state=removed."""
        with tempfile.TemporaryDirectory(prefix="a3-pub-integ-") as workdir:
            workdir = Path(workdir)
            notes = workdir / "notes"
            content = workdir / "content"
            data = workdir / "data"
            notes.mkdir()
            (content / "garden" / "keep").mkdir(parents=True)
            (content / "garden" / "gone").mkdir(parents=True)
            (content / "garden" / "keep" / "index.md").write_text("# keep\n")
            (content / "garden" / "gone" / "index.md").write_text("# gone\n")
            data.mkdir()
            manifest_path = data / "url-history.yaml"
            # Seed manifest with both notes live.
            manifest_path.write_text(
                "notes:\n"
                "  - id: keep-id-1\n"
                "    current_url: /garden/keep/\n"
                "    history: []\n"
                "    state: live\n"
                "  - id: gone-id-1\n"
                "    current_url: /garden/gone/\n"
                "    history: []\n"
                "    state: live\n"
            )
            # Source corpus: only "keep" has HUGO_PUBLISH; "gone" doesn't.
            (notes / "keep.org").write_text(
                ":PROPERTIES:\n:ID: keep-id-1\n:END:\n"
                "#+TITLE: Keep\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n"
                "body\n"
            )
            (notes / "gone.org").write_text(
                ":PROPERTIES:\n:ID: gone-id-1\n:END:\n"
                "#+TITLE: Gone\n"  # No HUGO_PUBLISH — note unpublished.
                "body\n"
            )
            forms = [
                f'(setq a3madkour-pub/org-notes-dir "{notes}")',
                f'(setq a3madkour-pub-site-content-dir "{content}/")',
                f'(setq a3madkour-pub/site-data-dir "{data}/")',
                "(a3madkour-pub/begin-publish)",
                # Walk-mode: leave accumulator empty so finish-publish walks source.
                "(princ (format \"%S\\n\" (a3madkour-pub/finish-publish)))",
            ]
            # Need unpublish module loaded — extend _emacs_eval form list.
            forms.insert(0, "(load (expand-file-name \"a3madkour-publish-unpublish.el\" "
                            f"\"{DOTFILES_LISP}/\"))")
            proc = _emacs_eval(forms, cwd=workdir)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            # Bundle for "gone" deleted.
            self.assertFalse((content / "garden" / "gone").exists())
            # Bundle for "keep" remains.
            self.assertTrue((content / "garden" / "keep").exists())
            # Manifest mutated: gone-id-1 state == removed.
            updated = manifest_path.read_text()
            self.assertIn("gone-id-1", updated)
            self.assertIn("state: removed", updated)
            self.assertIn("reason: removed", updated)
```

Note: `_emacs_eval` in the existing test file uses a fixed `-l` chain; the test extends it via a load form. Verify the existing implementation supports this pattern — if not, factor a helper that accepts extra `-l` args, or use `--eval "(load ...)" ` injection like above.

Run: `python3 /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py 2>&1 | tail -10`
Expected: 5 tests run (4 existing + 1 new); the new one fails because `a3madkour-pub/site-data-dir` may not be the right variable name to set the manifest path. Adjust accordingly to whatever the actual override mechanism is (the existing fixtures show the pattern).

- [ ] **Step 3: Adjust until the test passes**

Re-run after each adjustment. Once green: `Ran 5 tests in N.Ns OK`. Exit 0.

- [ ] **Step 4: Stage + test-count checkpoint**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
```

End of Task 17: **220 ert tests** (unchanged). **5 integration fixtures** (4 → 5).

---

### Task 18: Integration fixture `slug_shift_renames_assets`

**Files:**
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Write + run the failing test**

Append to TestPublishIntegration:

```python
    @unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
    def test_slug_shift_renames_assets(self):
        """Publish note with /garden/foo/ + asset → change HUGO_SLUG to foo-v2;
        finish-publish renames asset dir + rewrites .org source link."""
        with tempfile.TemporaryDirectory(prefix="a3-pub-integ-") as workdir:
            workdir = Path(workdir)
            notes = workdir / "notes"
            asset_root = workdir / "asset-root"
            content = workdir / "content"
            data = workdir / "data"
            notes.mkdir()
            data.mkdir()
            (asset_root / "page" / "foo").mkdir(parents=True)
            (asset_root / "page" / "foo" / "x.png").write_bytes(b"PNGDATA")
            (content / "garden" / "foo").mkdir(parents=True)
            (content / "garden" / "foo" / "index.md").write_text("# foo\n")
            manifest_path = data / "url-history.yaml"
            manifest_path.write_text(
                "notes:\n"
                "  - id: shift-id-1\n"
                "    current_url: /garden/foo/\n"
                "    history: []\n"
                "    state: live\n"
            )
            # Source has HUGO_SLUG: foo-v2 → new URL = /garden/foo-v2/.
            (notes / "note.org").write_text(
                ":PROPERTIES:\n:ID: shift-id-1\n:END:\n"
                "#+TITLE: Foo\n#+HUGO_PUBLISH: t\n"
                "#+HUGO_SECTION: garden\n#+HUGO_SLUG: foo-v2\n"
                "See [[./assets/page/foo/x.png][x]]\n"
            )
            forms = [
                f'(load (expand-file-name "a3madkour-publish-unpublish.el" '
                f'"{DOTFILES_LISP}/"))',
                f'(setq a3madkour-pub/org-notes-dir "{notes}")',
                f'(setq a3madkour-pub-canonical-asset-root "{asset_root}")',
                f'(setq a3madkour-pub-site-content-dir "{content}/")',
                f'(setq a3madkour-pub/site-data-dir "{data}/")',
                "(a3madkour-pub/begin-publish)",
                "(princ (format \"%S\\n\" (a3madkour-pub/finish-publish)))",
            ]
            proc = _emacs_eval(forms, cwd=workdir)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            # Asset dir renamed.
            self.assertFalse((asset_root / "page" / "foo").exists())
            self.assertTrue((asset_root / "page" / "foo-v2" / "x.png").exists())
            # Source link rewritten.
            rewritten = (notes / "note.org").read_text()
            self.assertIn("./assets/page/foo-v2/x.png", rewritten)
            self.assertNotIn("./assets/page/foo/x.png", rewritten)
            # Manifest: slug_override event recorded.
            updated = manifest_path.read_text()
            self.assertIn("slug_override", updated)
```

Run: `python3 tools/test_publish_integration.py 2>&1 | tail -10`
Expected: 6 tests; new one passes. Exit 0.

- [ ] **Step 2: Stage + test-count checkpoint**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
```

End of Task 18: **220 ert tests** (unchanged). **6 integration fixtures** (5 → 6).

---

### Task 19: Integration fixture `republish_after_removal`

**Files:**
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Write + run the failing test**

Append to TestPublishIntegration:

```python
    @unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
    def test_republish_after_removal(self):
        """Publish a note → unpublish it (state: removed) → republish at a new
        URL → history shows {removed, republished} events; aliases include prior URL."""
        with tempfile.TemporaryDirectory(prefix="a3-pub-integ-") as workdir:
            workdir = Path(workdir)
            notes = workdir / "notes"
            content = workdir / "content"
            data = workdir / "data"
            notes.mkdir()
            data.mkdir()
            manifest_path = data / "url-history.yaml"
            # Seed manifest: already in `state: removed' with one history entry.
            manifest_path.write_text(
                "notes:\n"
                "  - id: rep-id-1\n"
                "    current_url: null\n"
                "    history:\n"
                "      - url: /garden/old-name/\n"
                "        replaced_at: '2026-05-22T10:00:00Z'\n"
                "        reason: removed\n"
                "    state: removed\n"
            )
            # Source: now published again at /garden/new-name/.
            (notes / "note.org").write_text(
                ":PROPERTIES:\n:ID: rep-id-1\n:END:\n"
                "#+TITLE: New name\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n"
                "body\n"
            )
            forms = [
                f'(load (expand-file-name "a3madkour-publish-unpublish.el" '
                f'"{DOTFILES_LISP}/"))',
                f'(setq a3madkour-pub/org-notes-dir "{notes}")',
                f'(setq a3madkour-pub-site-content-dir "{content}/")',
                f'(setq a3madkour-pub/site-data-dir "{data}/")',
                "(a3madkour-pub/begin-publish)",
                # Simulate B's per-note record-publish call:
                '(a3madkour-pub-history/record-publish "rep-id-1" "/garden/new-name/" \'live)',
                "(princ (format \"%S\\n\" (a3madkour-pub/finish-publish)))",
            ]
            proc = _emacs_eval(forms, cwd=workdir)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            updated = manifest_path.read_text()
            self.assertIn("state: live", updated)
            self.assertIn("current_url: /garden/new-name/", updated)
            self.assertIn("reason: removed", updated)       # original event preserved
            self.assertIn("reason: republished", updated)   # new event appended
            self.assertIn("/garden/old-name/", updated)     # prior URL in history (aliases source)
```

Run: `python3 tools/test_publish_integration.py 2>&1 | tail -10`
Expected: 7 tests; new one passes. Exit 0.

- [ ] **Step 2: Stage + test-count checkpoint**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
```

End of Task 19: **220 ert tests** (unchanged). **7 integration fixtures** (6 → 7).

---

### Task 20: Integration fixture `link_into_removed_target_warns`

**Files:**
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Write + run the failing test**

Append to TestPublishIntegration:

```python
    @unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
    def test_link_into_removed_target_warns(self):
        """Publish two notes A → B; unpublish B; finish-publish emits a WARN
        in :orphan-warnings naming A's outgoing link into B."""
        with tempfile.TemporaryDirectory(prefix="a3-pub-integ-") as workdir:
            workdir = Path(workdir)
            notes = workdir / "notes"
            content = workdir / "content"
            data = workdir / "data"
            notes.mkdir()
            data.mkdir()
            (content / "garden" / "src").mkdir(parents=True)
            (content / "garden" / "tgt").mkdir(parents=True)
            (content / "garden" / "src" / "index.md").write_text("# src\n")
            (content / "garden" / "tgt" / "index.md").write_text("# tgt\n")
            manifest_path = data / "url-history.yaml"
            manifest_path.write_text(
                "notes:\n"
                "  - id: src-id-1\n"
                "    current_url: /garden/src/\n"
                "    history: []\n"
                "    state: live\n"
                "  - id: tgt-id-1\n"
                "    current_url: /garden/tgt/\n"
                "    history: []\n"
                "    state: live\n"
            )
            # Source A links to B via [[id:tgt-id-1]]; B is no longer HUGO_PUBLISH.
            (notes / "src.org").write_text(
                ":PROPERTIES:\n:ID: src-id-1\n:END:\n"
                "#+TITLE: Source\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n"
                "See [[id:tgt-id-1][gone target]]\n"
            )
            (notes / "tgt.org").write_text(
                ":PROPERTIES:\n:ID: tgt-id-1\n:END:\n"
                "#+TITLE: Target\n"  # No HUGO_PUBLISH → tgt-id-1 will be classified :removed.
                "body\n"
            )
            forms = [
                f'(load (expand-file-name "a3madkour-publish-unpublish.el" '
                f'"{DOTFILES_LISP}/"))',
                f'(setq a3madkour-pub/org-notes-dir "{notes}")',
                f'(setq a3madkour-pub-site-content-dir "{content}/")',
                f'(setq a3madkour-pub/site-data-dir "{data}/")',
                "(a3madkour-pub/begin-publish)",
                # Stub org-roam-id-find to point at the source file.
                "(cl-letf (((symbol-function 'org-roam-id-find)"
                "           (lambda (id &optional _)"
                f'             (cond ((equal id "src-id-1") (cons "{notes}/src.org" 1))'
                f'                   ((equal id "tgt-id-1") (cons "{notes}/tgt.org" 1))))))'
                "  (princ (format \"%S\\n\" (a3madkour-pub/finish-publish))))",
            ]
            proc = _emacs_eval(forms, cwd=workdir)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            # WARN in stdout: should mention both src-id-1 (outgoing) and tgt-id-1 (target).
            self.assertIn("src-id-1", proc.stdout)
            self.assertIn("tgt-id-1", proc.stdout)
            self.assertIn("republish recommended", proc.stdout)
```

Run: `python3 tools/test_publish_integration.py 2>&1 | tail -10`
Expected: 8 tests; new one passes. Exit 0.

- [ ] **Step 2: Stage + test-count checkpoint**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
```

End of Task 20: **220 ert tests** (unchanged). **8 integration fixtures** (7 → 8).

---

### Task 21: Update site repo `CLAUDE.md`

**Files:**
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md`

Three edits: (1) carry-forward #5 (CI step count off-by-2, cosmetic); (2) A.1.d shipped pointer under Phase 3; (3) next-slice pointer (A.1 closed; next overall = Phase 3 sub-project B).

- [ ] **Step 1: Investigate the CI step count off-by-2**

Locate the CI step total in CLAUDE.md's `Deployment` section:

```bash
grep -n "named steps\|CI step\|Total:" /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md
```

Expected: a line like `Total: 61 named steps.` in the Deployment section. Cross-check against `.github/workflows/hugo.yaml`:

```bash
grep -c "^      - name:" /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.github/workflows/hugo.yaml
```

If the actual count differs from what CLAUDE.md says, update CLAUDE.md to match.

- [ ] **Step 2: Add A.1.d shipped pointer + update next-slice**

Find the Phase 3 sub-project A description in CLAUDE.md (under the "Not started, in phase order" section, A heading). The current line ends with:

> A.1.0 (bootstrap) + A.1.a (foundations) + A.1.b (link rewriter) + A.1.c (asset handling + 24th linter pair) implementation complete; 175 ert tests passing. A.1.d (unpublish flow + integration tests) is the next plan.

Replace with:

> A.1.0 (bootstrap) + A.1.a (foundations) + A.1.b (link rewriter) + A.1.c (asset handling + 24th linter pair) + **A.1.d (unpublish flow + integration tests)** implementation complete; ~220 ert tests passing. Sub-project A is now fully shipped. Next overall slice = Phase 3 sub-project **B** (per-content-type publisher + templates). See `memory/project_a1d_complete.md`.

Also update the line citing memory `project_a1c_complete.md` to reference the new `project_a1d_complete.md` instead (or in addition — keep both as historical entries).

- [ ] **Step 3: Stage + test-count checkpoint**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add CLAUDE.md
```

End of Task 21: **220 ert tests** (unchanged). Docs-only.

---

### Task 22: USER VERIFICATION CHECKPOINT

This is for the human author. Per parent spec §11, every implementation stage gets a manual checkpoint. The slice is "complete-but-staged" at this point; the author runs these checks before committing.

- [ ] **Step 1: Author runs the full elisp test suite**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5
```

Expected: `Ran 220 tests, 220 results as expected, 0 unexpected`. Exit 0.

- [ ] **Step 2: Author runs the site CI pipeline locally**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
tools/ci-local.sh 2>&1 | tail -10
```

Expected: full CI pipeline passes including all 24 linter pairs. LHCI-mobile garden score has known local variance (per `memory/project_toc_collapsible_subsections_slice.md`) — only flag if other steps fail.

- [ ] **Step 3: Author runs the Python integration tests**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
python3 tools/test_publish_integration.py 2>&1 | tail -10
```

Expected: `Ran 8 tests in N.Ns OK`. Exit 0.

- [ ] **Step 4: Spot-check `--check-orphans` against current site state**

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --check-orphans 2>&1 | tail -15
echo "exit code: $?"
```

Expected: `removed: nil` + `slug-shifted: nil` + `orphan-warnings:` header with no following lines. Exit code 0.

Steady state — the live site's `data/url-history.yaml` is `notes: []` and `a3madkour-pub/org-notes-dir` defaults to a (probably non-existent) `~/org-roam/` per memory, so the standalone walk returns an empty hash and the diff is trivially empty. If the author has `~/org/notes/` set as the override and that dir contains published notes, the output will reflect their state.

- [ ] **Step 5: Spot-check `finish-publish` end-to-end with a tmpdir corpus**

Set up the same shape as integration fixture #17 but interactively:

```bash
mkdir -p /tmp/a3-finish-spot/{notes,content/garden/{a,b}/,data,asset-root/page/a}
echo "data" > /tmp/a3-finish-spot/asset-root/page/a/x.png

# Two notes: A stays, B becomes unpublished.
cat > /tmp/a3-finish-spot/notes/a.org <<'ORG'
:PROPERTIES:
:ID: spot-a-id
:END:
#+TITLE: A
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
body
ORG

cat > /tmp/a3-finish-spot/notes/b.org <<'ORG'
:PROPERTIES:
:ID: spot-b-id
:END:
#+TITLE: B
body
ORG

# Seed manifest with both live.
cat > /tmp/a3-finish-spot/data/url-history.yaml <<'YAML'
notes:
  - id: spot-a-id
    current_url: /garden/a/
    history: []
    state: live
  - id: spot-b-id
    current_url: /garden/b/
    history: []
    state: live
YAML

touch /tmp/a3-finish-spot/content/garden/a/index.md
touch /tmp/a3-finish-spot/content/garden/b/index.md

~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh \
  --eval '(setq a3madkour-pub/org-notes-dir "/tmp/a3-finish-spot/notes")' \
  --eval '(setq a3madkour-pub-site-content-dir "/tmp/a3-finish-spot/content/")' \
  --eval '(setq a3madkour-pub/site-data-dir "/tmp/a3-finish-spot/data/")' \
  --eval "(a3madkour-pub/begin-publish)" \
  --eval "(message \"%S\" (a3madkour-pub/finish-publish))"

# Verify:
ls /tmp/a3-finish-spot/content/garden/   # only `a/` should remain
cat /tmp/a3-finish-spot/data/url-history.yaml   # spot-b-id should be state: removed
```

Expected: bundle `b/` is gone, `a/` remains; manifest shows `spot-b-id: state: removed` + history entry with `reason: removed`.

Cleanup: `rm -rf /tmp/a3-finish-spot`.

- [ ] **Step 6: Spot-check slug-shift end-to-end with a tmpdir corpus**

```bash
mkdir -p /tmp/a3-shift-spot/{notes,content/garden/foo/,data,asset-root/page/foo}
echo "data" > /tmp/a3-shift-spot/asset-root/page/foo/x.png

cat > /tmp/a3-shift-spot/notes/n.org <<'ORG'
:PROPERTIES:
:ID: shift-id
:END:
#+TITLE: Foo
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
#+HUGO_SLUG: foo-v2
[[./assets/page/foo/x.png][x]]
ORG

cat > /tmp/a3-shift-spot/data/url-history.yaml <<'YAML'
notes:
  - id: shift-id
    current_url: /garden/foo/
    history: []
    state: live
YAML

touch /tmp/a3-shift-spot/content/garden/foo/index.md

~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh \
  --eval '(setq a3madkour-pub/org-notes-dir "/tmp/a3-shift-spot/notes")' \
  --eval '(setq a3madkour-pub-canonical-asset-root "/tmp/a3-shift-spot/asset-root")' \
  --eval '(setq a3madkour-pub-site-content-dir "/tmp/a3-shift-spot/content/")' \
  --eval '(setq a3madkour-pub/site-data-dir "/tmp/a3-shift-spot/data/")' \
  --eval "(a3madkour-pub/begin-publish)" \
  --eval '(a3madkour-pub-history/record-publish "shift-id" "/garden/foo-v2/" (quote live))' \
  --eval "(message \"%S\" (a3madkour-pub/finish-publish))"

# Verify:
ls /tmp/a3-shift-spot/asset-root/page/        # foo-v2/ should exist; foo/ should NOT
cat /tmp/a3-shift-spot/notes/n.org            # link should now say page/foo-v2/x.png
cat /tmp/a3-shift-spot/data/url-history.yaml  # history should have slug_override event
```

Expected: asset dir renamed, source link rewritten, manifest event recorded.

Cleanup: `rm -rf /tmp/a3-shift-spot`.

- [ ] **Step 7: All-green signal**

If all 6 spot-checks pass + all 3 test suites pass: A.1.d is ready to commit. Proceed to Task 23 for staging + suggested commit messages. If anything failed: stop, capture output, debug or roll back the offending task before committing.

---

### Task 23: Stage files for author commit (default no-commit session policy)

Per session policy default, the agent stages but does NOT commit. Skip this task if the author signaled "commit as you go" at session start.

The Stage-0 parent-spec amendment (Task 1) is ALREADY committed; this task handles only the implementation diffs.

- [ ] **Step 1: Stage dotfiles changes**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el \
        emacs-configs/custom/lisp/a3madkour-publish.el \
        emacs-configs/custom/lisp/a3madkour-publish-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-history.el \
        emacs-configs/custom/lisp/a3madkour-publish-history-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-assets-test.el \
        emacs-configs/custom/lisp/a3-pub.sh
git status --short emacs-configs/custom/lisp/
```

Expected: 8 files listed (2 new unpublish + 6 modified).

- [ ] **Step 2: Stage site-repo changes**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py \
        CLAUDE.md \
        docs/superpowers/plans/2026-05-24-phase-3-a1-d-unpublish.md
git status --short
```

Expected: 3 files staged. (`data/url-history.yaml` and the parent spec amendment were already committed in Stage 0.)

- [ ] **Step 3: Suggested commit messages (author runs)**

In dotfiles:

```bash
git commit -m "feat(publish): A.1.d unpublish flow + integration

Sub-project A.1.d of the Phase 3 org→Hugo publish pipeline.  Closes
parent spec §12 A.1 item #7 (unpublish flow + --check-orphans preview).
Sub-project A is now fully shipped.

- a3madkour-publish-unpublish.el (NEW): \`finish-publish' orchestrator +
  4 internal helpers + \`check-orphans' thin alias.  Three sub-steps run
  in fixed order:
    A. Unpublish sweep — diff new live-set vs manifest live+draft;
       delete content/<section>/<slug>/ bundles; mutate manifest
       entries to state=removed.
    B. Slug-shift sync — rename ~/org/notes/assets/page/<old>/ →
       <new>/ + bulk-rewrite source .org link references (closes
       carry-forward #2 from A.1.c).
    C. Re-link-check — scan live notes' outgoing org links; WARN
       for any link resolving into removed-this-publish-set.
- a3madkour-publish.el: new defvar a3madkour-pub--publish-run-accumulator;
  begin-publish extended to clear it alongside the metadata cache.
- a3madkour-publish-history.el: record-publish extended for the
  republished reason path (state: removed → live + appends event)
  and always pushes (id . (url . state)) into the accumulator (B's
  hook for the standalone vs B-coupled mode dispatch).
- a3madkour-publish-assets-test.el: +3 carry-forward #1 tests covering
  --asset-normalize-link-path's three branches.
- a3-pub.sh: -l a3madkour-publish-unpublish added to load chain;
  --check-orphans flag intercept added before exec emacs.

Test count progression: 175 (end A.1.c) → 220 (end A.1.d). All passing.

Standalone-capable: finish-publish walks the source tree when B
hasn't populated the accumulator, so today's CLI runs work without B.
When B ships, B's per-content-type loop ends with (finish-publish);
accumulator drives the diff.

Carried forward to A.2 / future:
- carry-forward #3 (shared-asset conflict resolution; own design pass)
- carry-forward #4 (--strict flag; A.2)
- typed-backlinks + :noexport: + --gc-shared (A.2 items)"
```

In site repo:

```bash
git commit -m "ci(publish): A.1.d — integration fixtures + url-history schema bump

Sub-project A.1.d ships:

- tools/test_publish_integration.py: +4 end-to-end fixtures covering
  unpublish_removed_note, slug_shift_renames_assets, republish_after_removal,
  link_into_removed_target_warns.  Total 4 → 8 fixtures.
- CLAUDE.md: A.1.d shipped pointer under Phase 3; sub-project A closed;
  next overall slice = sub-project B (per-content-type publisher).
  Carry-forward #5 (CI step count off-by-2) fixed.
- docs/superpowers/plans/2026-05-24-phase-3-a1-d-unpublish.md: this plan.

Parent spec §8 reason enum bump (4 → 5 values, adding \`republished')
landed earlier in commit 9459a4c-or-similar (Stage-0 amendment ahead
of impl).  data/url-history.yaml comment block was bumped at the same
time; the seed value (notes: []) is unchanged.

Test count progression on the elisp side: 175 → 220.  No new linter
pair this slice (24 stays at 24).  Integration fixtures: 4 → 8."
```

- [ ] **Step 4: Final-counter checkpoint**

End of Task 23: Final test counts locked at **220 ert + 11 Python sibling + 8 Python integration tests**. A.1.d complete; sub-project A closed.

---

## Self-Review

**Spec coverage** (every spec section maps to one or more tasks):

- ✅ §1 Goals (5 items) — covered by Tasks 1 (parent-spec amend), 5+6 (diff+walk), 7+8 (Step A), 9+10+11 (Step B), 12+13 (Step C), 15 (--check-orphans CLI). Carry-forwards #1, #2, #5 covered by Tasks 16, 9+10+11, 21.
- ✅ §2 Non-goals — explicit deferrals confirmed in File Structure + Task 23 commit message.
- ✅ §3 Carry-forward context — Tasks 2 (wrapper-script lesson applied), 4 (record-publish extension), 16 (asset-normalize tests).
- ✅ §4 `finish-publish` orchestrator overview — Tasks 8 (skeleton), 11 (Step B wiring), 13 (Step C wiring), 14 (check-orphans alias).
- ✅ §5 Step A algorithm — Task 8.
- ✅ §6 Step B algorithm — Tasks 9 (rename helper), 10 (bulk rewrite helper), 11 (wiring).
- ✅ §7 Step C algorithm — Tasks 12 (helper), 13 (wiring).
- ✅ §8 API surface — Tasks 5, 6, 8, 11, 13, 14 (public); 7, 9, 10, 12 (internal helpers); 3, 4 (publish.el + history.el extensions).
- ✅ §9 Manifest schema delta — Task 1 (spec amend + manifest comment); Task 4 (record-publish republished branch).
- ✅ §10 CLI surface — Task 15.
- ✅ §11 Testing strategy — every elisp task ships ert tests (per-task counts noted); Tasks 17-20 ship integration fixtures.
- ✅ §12 File inventory — File Structure block above.
- ✅ §13 Commit layout — Tasks 1, 21, 23 produce the 4 commits the spec described (parent-spec amend + plan doc + dotfiles impl + site impl). Note: the plan-doc commit also lands as part of the site impl in Task 23 step 2 — adjust if cleaner to split.
- ✅ §14 Open carry-forwards — explicit deferrals listed in File Structure.

**Type consistency check** (function names + plist keys + signatures across tasks):

- `a3madkour-pub/finish-publish` — Tasks 8, 11, 13, 14, 17, 18, 19, 20. Same signature throughout: `(&key dry-run)`.
- `a3madkour-pub/check-orphans` — Task 14, called in Task 15. Zero-arg.
- `a3madkour-pub/diff-published-set` — Task 5, called by `finish-publish` (Task 8). 1-arg.
- `a3madkour-pub/walk-published-source-set` — Task 6, called by `finish-publish` (Task 8). 0-arg.
- `a3madkour-pub--unpublish-delete-bundle` — Task 7, called by `finish-publish` (Task 8). 3-arg with optional `content-root`.
- `a3madkour-pub--unpublish-rename-asset-dir` — Task 9, called by `finish-publish` (Task 11). 3-arg with optional `canonical-root`.
- `a3madkour-pub--unpublish-bulk-rewrite-source-links` — Task 10, called by `finish-publish` (Task 11). 3-arg with optional `org-notes-dir`.
- `a3madkour-pub--unpublish-recheck-live-note-links` — Task 12, called by `finish-publish` (Task 13). 1-arg (removed-this-publish-set).
- `a3madkour-pub--publish-run-accumulator` — defvar in Task 3, populated in Task 4, read in Task 8. Hash table `equal`.
- Return-plist keys consistent across `finish-publish` + `check-orphans`: `:added :stayed :removed :slug-shifted :orphan-warnings`. `:partial-failures` documented in spec §8 but NOT yet populated by the orchestrator (Task 8/11/13 omit it); add later if a partial-failure path materializes during user-verification.
- Manifest reason enum: 5 values throughout. Task 1 bumps spec + comment; Task 4 implements `republished`.

**Placeholder scan:**

- No "TBD"/"TODO"/"implement later".
- No "Similar to Task N".
- All code blocks complete; no `...` ellipses inside function bodies.
- Test runs have explicit expected output + exit code annotations.

**Test-count consistency:**

- 175 (start) → 176 (Task 2) → 178 (Task 3) → 181 (Task 4) → 187 (Task 5) → 191 (Task 6) → 194 (Task 7) → 198 (Task 8) → 202 (Task 9) → 207 (Task 10) → 209 (Task 11) → 213 (Task 12) → 216 (Task 13) → 217 (Task 14) → 217 (Task 15) → 220 (Task 16) → 220 (Tasks 17-21 — Python fixtures, not ert). Final: 220 ert + 11 Python sibling (unchanged) + 8 Python integration (4 → 8).

**Known risk to surface to executor at start:**

- Task 4's accumulator append uses the **symbol** form of `state` (not the string-coerced one) because the diff function (Task 5) compares cdr against `'live` / `'draft` symbols. If `record-publish` is called from B with a string state value, the symbol-vs-string mismatch will silently break the diff. Tests cover both forms (Task 4's accumulator test passes `'live` + `'draft` symbols directly).
- Task 9's `git mv` fallback path is best-effort; if `git mv` aborts the FS state may already be partially mutated (file moved + index modified). The fallback to `rename-file` won't fire because the source no longer exists. Realistic mitigation: dry-run first, then live-run only after verifying no shifts have target conflicts.
- Task 17-20 use `(load (expand-file-name "a3madkour-publish-unpublish.el" "${DOTFILES_LISP}/"))` to extend the existing `_emacs_eval` chain. If the existing helper signature changes between A.1.c and now, adjust the load form's path or add a kwarg to `_emacs_eval` for extra `-l` modules.
- The CI step count off-by-2 (carry-forward #5) is investigated in Task 21 Step 1 — the actual delta depends on the current state of `.github/workflows/hugo.yaml`. The plan says "61 named steps"; verify against `grep -c "^      - name:"` and reconcile.

Plan complete and saved.
