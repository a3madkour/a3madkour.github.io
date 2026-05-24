# Phase 3 sub-project B.0 — shared publisher infrastructure: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the foundation pieces every B.x content-type slice will need: an ox-hugo export wrapper, a per-section frontmatter normalizer dispatch, two top-level command modules (`-living` / `-deliberate`) wired up to the begin/finish lifecycle, `a3-pub.sh` flag intercepts that mirror the existing `--check-orphans` precedent, and the manifest-snapshot fix that unblocks B's per-note `record-publish` calls without poisoning slug-shift detection.

**Architecture:** Five new elisp modules + sibling test files under `~/dotfiles/emacs-configs/custom/lisp/`. Three small edits to `a3madkour-publish.el` and `a3madkour-publish-history.el` for the snapshot fix. Two new flag intercepts in `a3-pub.sh`. One status update in the site repo's `CLAUDE.md`. Nothing user-visible at the Hugo content layer until B.1.

**Tech Stack:** Emacs Lisp + ert; bash; ox-hugo (loaded but only sanity-checked in this slice); the existing A.1 elisp library API (parent design spec §10).

---

## Reading list before starting

1. **`docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md`** — the parent design spec for sub-project B. §5 (modules), §6 (B-coupling fix), §10 (A → B interface usage), §11 (idempotency), §12 (slice ordering). This plan implements only what §12 calls the "B.0" slice.
2. **`docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md`** — A's parent design spec. §10 (A's API surface that B consumes), §11 (testing strategy, esp. snapshot-at-publish-start semantics).
3. **`~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`** — read `a3madkour-pub--publish-run-accumulator` (line 157), `a3madkour-pub/begin-publish` (line 248). The accumulator pattern is the model for the new manifest snapshot defvar.
4. **`~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`** — read `record-publish` (line 127). Confirms `record-publish` writes manifest eagerly; the snapshot fix changes ONLY `diff-published-set`'s read source.
5. **`~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`** — read `diff-published-set` (line 42), `walk-published-source-set` (line 99), `finish-publish` (line 163). `finish-publish` is where the snapshot must be cleared.
6. **`~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`** — current shell wrapper. Lines 22-50 are the existing `--check-orphans` intercept that the two new flag intercepts model after.

## Repository layout

This plan touches **two repos** on disk. Only the site repo gets pushed; the dotfiles repo stays local per the author's workflow.

- **Site repo** (`/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/`): houses this plan + the spec + the eventual CLAUDE.md status pointer update. Pushed to `origin/master`.
- **Dotfiles repo** (`~/dotfiles/`): houses all elisp work (new modules + edits to `-history.el` + edits to `a3-pub.sh`). Stays unpushed; the author syncs across machines manually.

## File structure

### Files to CREATE in the dotfiles repo

- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export.el` — ox-hugo wrapper skeleton (`export-file` returns a stub plist in B.0; B.1 wires real ox-hugo).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export-test.el` — ert sibling.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` — per-section normalizer dispatch (`normalize` returns input unchanged for any section in B.0; B.1+ fills per-section bodies).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el` — ert sibling.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el` — `(a3-publish-living)` top-level command; runs the begin/walk/finish lifecycle. Walks empty handler set in B.0 (handlers register in B.1+).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el` — ert sibling.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate.el` — `(a3-publish-deliberate file-or-id)` top-level command; resolves arg, reads `HUGO_SECTION`, signals `'no-handler-for-section` in B.0 (handlers register in B.1+).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate-test.el` — ert sibling.

### Files to MODIFY in the dotfiles repo

- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` — add the `a3madkour-pub--manifest-snapshot` defvar; populate it in `begin-publish`; clear it in tear-down hooked from `finish-publish` (clearing actually happens in the `-unpublish.el` finish-publish wrapper, but the defvar lives here next to the accumulator).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el` — read snapshot in `diff-published-set` (via a new helper `read-manifest-snapshot-or-disk`); leave `record-publish` unchanged.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el` — change `diff-published-set` call site (line 191) to use the new snapshot-aware reader; clear snapshot at end of `finish-publish` (after Step C).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el` — extend with snapshot-fix tests.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el` — extend with snapshot-clear-on-finish test + regression test ("record-publish mid-publish doesn't poison diff").
- `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` — add `--publish-living` and `--publish-deliberate <path>` flag intercepts mirroring the existing `--check-orphans` block; load all new modules (`-export`, `-frontmatter`, `-living`, `-deliberate`) under both intercept paths AND under the default exec at the bottom of the file (so ad-hoc `--eval` invocations also see them).

### Files to MODIFY in the site repo

- `CLAUDE.md` — bump the "Project status" pointer to note B.0 staged; add B.0 to the recent shipped slices line. Single short edit.

## Test-running command

All ert tests for the elisp library run via:

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5
```

Expected output at B.0 end: `Ran NNN tests, NNN results as expected, 0 unexpected` where NNN > 223 (the A.1.d baseline). Specifically, B.0 should add ≈15-20 new ert tests across the five new modules + snapshot-fix tests, landing total ≈240-245.

## Commit cadence

One commit per task (TDD pair = test + impl committed together). Commit messages follow A.1.d precedent:

```
feat(b-0): <one-liner>

<2-3 sentences explaining the change>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

The dotfiles repo accumulates B.0 commits locally; do NOT push it. The site repo gets one commit at the end (CLAUDE.md status update) that DOES get pushed.

---

## Stage 1 — Manifest snapshot fix (B-coupling)

This stage lands the §6 fix from the design spec. After it, `record-publish` can be called mid-publish without poisoning `diff-published-set`'s slug-shift detection. Three modules touched: `-publish.el` (new defvar), `-history.el` (helper that reads snapshot OR disk), `-unpublish.el` (`diff-published-set` callsite + `finish-publish` snapshot clear).

### Task 1: Add the manifest-snapshot defvar to `a3madkour-publish.el`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` (immediately after the existing `a3madkour-pub--publish-run-accumulator` defvar, ~line 170)

- [ ] **Step 1: Write the failing test**

Add to `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el` (append at end, before `(provide …)` if present, otherwise at file end):

```elisp
(ert-deftest a3madkour-pub-test/manifest-snapshot-defvar-exists ()
  "B.0 — `a3madkour-pub--manifest-snapshot' defvar is defined and starts nil."
  (should (boundp 'a3madkour-pub--manifest-snapshot))
  (should (null a3madkour-pub--manifest-snapshot)))
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-test/manifest-snapshot-defvar-exists' 2>&1 | tail -10
```

Expected: FAIL with `Symbol's value as variable is void: a3madkour-pub--manifest-snapshot` (or "0 tests run" if ert can't find the symbol; either is acceptable proof of red).

- [ ] **Step 3: Implement minimal code to make the test pass**

In `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`, immediately after the closing `)` of the existing `a3madkour-pub--publish-run-accumulator` defvar (around line 170), insert:

```elisp
(defvar a3madkour-pub--manifest-snapshot nil
  "Snapshot of the URL-history manifest taken at `begin-publish'.

`a3madkour-pub/diff-published-set' reads from this snapshot instead of
re-reading `data/url-history.yaml' off disk, so that `record-publish'
calls made mid-publish (by B's per-note publishers) do not poison the
slug-shift detection in `diff-published-set'.

nil means \"no snapshot active\" — `read-manifest-snapshot-or-disk' will
fall back to reading the manifest off disk.  Set at the top of
`begin-publish' (next to the metadata-cache reset); cleared at the bottom
of `finish-publish' (after Step C).

Lives in `a3madkour-publish.el' next to the publish-run-accumulator so the
two publish-run snapshots (accumulator, manifest) are colocated.

See parent design spec §6 (B-coupling fix); the design memo
`memory/project_a1d_complete.md` 'Architectural findings' section
documents why the snapshot approach was chosen over the alternatives.")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-test/manifest-snapshot-defvar-exists' 2>&1 | tail -5
```

Expected: `Ran 1 tests, 1 results as expected`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish.el emacs-configs/custom/lisp/a3madkour-publish-test.el
git commit -m "$(cat <<'EOF'
feat(b-0): add manifest-snapshot defvar (B-coupling fix prep)

Adds `a3madkour-pub--manifest-snapshot' next to the existing
publish-run-accumulator.  Will be populated by begin-publish in Task 2
and consumed by diff-published-set in Task 3.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Task 2: `begin-publish` reads manifest into snapshot

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` (the existing `a3madkour-pub/begin-publish` function, ~line 248)
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

- [ ] **Step 1: Write the failing test**

Append to `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`:

```elisp
(ert-deftest a3madkour-pub-test/begin-publish-populates-manifest-snapshot ()
  "B.0 — `begin-publish' reads url-history.yaml into the snapshot defvar.
Uses a temp data dir with a seeded manifest; stubs org-roam-db-sync."
  (let ((tmp-data (make-temp-file "b0-snapshot-" t))
        (a3madkour-pub--manifest-snapshot nil))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir tmp-data))
          ;; Seed a minimal manifest on disk.
          (with-temp-file (expand-file-name "url-history.yaml" tmp-data)
            (insert "notes:\n  - id: abc-123\n    current_url: /garden/foo/\n    history: []\n    state: live\n"))
          ;; Stub org-roam to avoid touching the user's real DB.
          (cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil)))
            (a3madkour-pub/begin-publish))
          ;; Snapshot should now hold the manifest alist.
          (should a3madkour-pub--manifest-snapshot)
          (let* ((notes (alist-get 'notes a3madkour-pub--manifest-snapshot)))
            (should (= 1 (length notes)))
            (should (equal "abc-123" (alist-get 'id (aref notes 0))))))
      (delete-directory tmp-data t))))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-test/begin-publish-populates-manifest-snapshot' 2>&1 | tail -10
```

Expected: FAIL — snapshot stays nil because `begin-publish` hasn't been edited yet.

- [ ] **Step 3: Implement**

In `a3madkour-publish.el`, edit the existing `a3madkour-pub/begin-publish` body (currently at line 248). The current body is:

```elisp
  (a3madkour-pub--reset-metadata-cache)
  (clrhash a3madkour-pub--publish-run-accumulator)
  (require 'org-roam)
  (org-roam-db-sync))
```

Change to:

```elisp
  (a3madkour-pub--reset-metadata-cache)
  (clrhash a3madkour-pub--publish-run-accumulator)
  ;; B.0: snapshot the URL-history manifest so diff-published-set reads
  ;; pre-publish state regardless of mid-publish record-publish calls.
  (setq a3madkour-pub--manifest-snapshot
        (a3madkour-pub-history/read-manifest))
  (require 'org-roam)
  (org-roam-db-sync))
```

Also update the docstring of `begin-publish` (just above the body) to add the snapshot to its enumerated responsibilities. Find this sentence in the current docstring:

```
Take per-publish snapshots: reset metadata cache; clear accumulator;
sync org-roam DB.
```

Replace with:

```
Take per-publish snapshots: reset metadata cache; clear accumulator;
read URL-history manifest into `a3madkour-pub--manifest-snapshot';
sync org-roam DB.
```

- [ ] **Step 4: Run test to verify it passes**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-test/begin-publish-populates-manifest-snapshot' 2>&1 | tail -5
```

Expected: `Ran 1 tests, 1 results as expected`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish.el emacs-configs/custom/lisp/a3madkour-publish-test.el
git commit -m "$(cat <<'EOF'
feat(b-0): begin-publish populates manifest snapshot

Adds the snapshot read inside begin-publish, right after the accumulator
clear.  Subsequent record-publish writes during the publish run hit disk
eagerly (unchanged) while diff-published-set will read from the snapshot
(Task 3).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Task 3: `diff-published-set` reads from snapshot when available

**Files:**
- Create helper: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el` (new fn `read-manifest-snapshot-or-disk`)
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el` (line 61 — change the `read-manifest` call inside `diff-published-set`)
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

- [ ] **Step 1: Write the failing test**

Append to `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`:

```elisp
(ert-deftest a3madkour-pub-hist-test/read-manifest-snapshot-or-disk-prefers-snapshot ()
  "B.0 — `read-manifest-snapshot-or-disk' returns the snapshot defvar
when non-nil, ignoring disk."
  (let ((tmp-data (make-temp-file "b0-snapshot-prefer-" t))
        (a3madkour-pub--manifest-snapshot
         '((notes . [((id . "snap-id") (current_url . "/garden/from-snap/")
                      (history . []) (state . "live"))]))))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir tmp-data))
          ;; Write a different manifest to disk to prove snapshot wins.
          (with-temp-file (expand-file-name "url-history.yaml" tmp-data)
            (insert "notes:\n  - id: disk-id\n    current_url: /garden/from-disk/\n    history: []\n    state: live\n"))
          (let* ((m (a3madkour-pub-history/read-manifest-snapshot-or-disk))
                 (notes (alist-get 'notes m)))
            (should (= 1 (length notes)))
            (should (equal "snap-id" (alist-get 'id (aref notes 0))))))
      (delete-directory tmp-data t))))

(ert-deftest a3madkour-pub-hist-test/read-manifest-snapshot-or-disk-falls-back ()
  "B.0 — `read-manifest-snapshot-or-disk' falls back to disk when snapshot is nil."
  (let ((tmp-data (make-temp-file "b0-snapshot-fallback-" t))
        (a3madkour-pub--manifest-snapshot nil))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir tmp-data))
          (with-temp-file (expand-file-name "url-history.yaml" tmp-data)
            (insert "notes:\n  - id: disk-only\n    current_url: /garden/disk-only/\n    history: []\n    state: live\n"))
          (let* ((m (a3madkour-pub-history/read-manifest-snapshot-or-disk))
                 (notes (alist-get 'notes m)))
            (should (= 1 (length notes)))
            (should (equal "disk-only" (alist-get 'id (aref notes 0))))))
      (delete-directory tmp-data t))))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-hist-test/read-manifest-snapshot-or-disk' 2>&1 | tail -10
```

Expected: FAIL — `Symbol's function definition is void: a3madkour-pub-history/read-manifest-snapshot-or-disk`.

- [ ] **Step 3: Implement the helper**

In `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`, immediately after the existing `a3madkour-pub-history/read-manifest` defun (line 51-68), add:

```elisp
(defun a3madkour-pub-history/read-manifest-snapshot-or-disk ()
  "Return `a3madkour-pub--manifest-snapshot' when non-nil; otherwise read disk.

Use this from any function that needs the URL-history manifest as it
existed AT THE START of the current publish run (as opposed to whatever
state `record-publish' has eagerly written to disk mid-run).  Currently
the sole caller is `a3madkour-pub/diff-published-set' (the slug-shift
detector); other A.1 readers continue to call `read-manifest' directly
because they don't care about run boundaries.

The snapshot defvar lives in `a3madkour-publish.el' (colocated with the
publish-run-accumulator); it is populated by `a3madkour-pub/begin-publish'
and cleared by `a3madkour-pub/finish-publish'.

See parent design spec §6 (B-coupling fix)."
  (if a3madkour-pub--manifest-snapshot
      a3madkour-pub--manifest-snapshot
    (a3madkour-pub-history/read-manifest)))
```

- [ ] **Step 4: Switch `diff-published-set` to the new helper**

In `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el`, line 61 currently reads:

```elisp
  (let* ((manifest (a3madkour-pub-history/read-manifest))
```

Change to:

```elisp
  (let* ((manifest (a3madkour-pub-history/read-manifest-snapshot-or-disk))
```

Also update the function's docstring (line 42-60). Find this sentence:

```
The old set is computed by reading the manifest via
`a3madkour-pub-history/read-manifest' and filtering to entries with
`state ∈ {live, draft}'
```

Replace with:

```
The old set is computed by reading the manifest via
`a3madkour-pub-history/read-manifest-snapshot-or-disk' (which prefers
`a3madkour-pub--manifest-snapshot' when set, i.e. during a B.0+ publish
run) and filtering to entries with `state ∈ {live, draft}'
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-hist-test/read-manifest-snapshot-or-disk' 2>&1 | tail -5
```

Expected: `Ran 2 tests, 2 results as expected`.

- [ ] **Step 6: Verify ALL existing tests still pass (no regression)**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5
```

Expected: `Ran NNN tests, NNN results as expected, 0 unexpected` where NNN is 223 + however many new tests have landed (≈226).

- [ ] **Step 7: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-history.el \
        emacs-configs/custom/lisp/a3madkour-publish-history-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish.el
git commit -m "$(cat <<'EOF'
feat(b-0): diff-published-set reads via snapshot-aware helper

Adds `read-manifest-snapshot-or-disk' (snapshot when set, disk
otherwise) and switches diff-published-set to it.  Other A.1 readers
continue to call read-manifest directly since they don't care about
publish-run boundaries.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Task 4: `finish-publish` clears the snapshot

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el` (end of `finish-publish` body, ~line 200-something after Step C)
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

- [ ] **Step 1: Locate the end of `finish-publish` body**

In `a3madkour-publish-unpublish.el`, the `finish-publish` defun starts at line 163. Find the closing `)` of its body — it's the line just before the `provide` form at the file end, OR just before the next top-level defun if there is one. Read the surrounding ~50 lines to identify the correct insertion point.

```bash
grep -n "finish-publish\|^(provide\|^(defun" ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el | head -20
```

Read enough of the file to see where Step C ends and what the final `)` for `cl-defun a3madkour-pub/finish-publish` looks like.

- [ ] **Step 2: Write the failing test**

Append to `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`:

```elisp
(ert-deftest a3madkour-pub-unpub-test/finish-publish-clears-manifest-snapshot ()
  "B.0 — `finish-publish' clears `a3madkour-pub--manifest-snapshot' at end.
Set up a tmp data dir, run begin-publish (which populates the snapshot),
then finish-publish, then assert snapshot is nil."
  (let ((tmp-data (make-temp-file "b0-snapshot-clear-" t)))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir tmp-data)
              (a3madkour-pub/org-notes-dir tmp-data))  ; harmless empty walk
          (with-temp-file (expand-file-name "url-history.yaml" tmp-data)
            (insert "notes: []\n"))
          (cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil)))
            (a3madkour-pub/begin-publish)
            (should a3madkour-pub--manifest-snapshot)
            (a3madkour-pub/finish-publish)
            (should-not a3madkour-pub--manifest-snapshot)))
      (delete-directory tmp-data t))))
```

- [ ] **Step 3: Run test to verify it fails**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-unpub-test/finish-publish-clears-manifest-snapshot' 2>&1 | tail -10
```

Expected: FAIL — snapshot stays populated after finish-publish.

- [ ] **Step 4: Implement the clear**

Inside the `a3madkour-pub/finish-publish` body, immediately before its closing `)` (after the Step C call, which is the last side-effect inside the function), insert:

```elisp
  ;; B.0: clear manifest snapshot now that the publish run is over.
  ;; Next publish run's begin-publish will populate it fresh.
  (setq a3madkour-pub--manifest-snapshot nil)
```

Make sure this is at the same indentation level as the existing Step C call (inside the `let*`/`cl-defun` body, at the `(let* …)`'s top level).

- [ ] **Step 5: Run test to verify it passes**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-unpub-test/finish-publish-clears-manifest-snapshot' 2>&1 | tail -5
```

Expected: `Ran 1 tests, 1 results as expected`.

- [ ] **Step 6: Run ALL tests; verify no regression**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5
```

Expected: zero unexpected failures.

- [ ] **Step 7: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el \
        emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
git commit -m "$(cat <<'EOF'
feat(b-0): finish-publish clears manifest snapshot

Adds the snapshot clear at the end of finish-publish (after Step C),
matching the lifecycle: begin-publish populates, finish-publish clears.
Next begin-publish reads fresh from disk.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Task 5: Regression test — `record-publish` mid-publish does not poison slug-shift detection

**Files:**
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

The behaviorial test that proves the entire snapshot fix works end-to-end.

- [ ] **Step 1: Write the regression test**

Append to `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`:

```elisp
(ert-deftest a3madkour-pub-unpub-test/snapshot-fix-preserves-slug-shift-detection ()
  "B.0 regression — calling record-publish mid-publish (B-coupled mode)
must NOT prevent diff-published-set from seeing the old URL.

Scenario:
  - Manifest has note ID 'shifter at /garden/old-name/.
  - During a publish run, we call record-publish to move it to /garden/new-name/.
  - Then we call diff-published-set with a new-set that still has 'shifter
    (because the source file still exists, just under a new slug).
  - Expectation: :slug-shifted contains ('shifter \"/garden/old-name/\" \"/garden/new-name/\").

Pre-fix: this would have reported the URL as unchanged because
diff-published-set re-read disk and saw the new URL already there."
  (let ((tmp-data (make-temp-file "b0-regression-" t)))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir tmp-data))
          ;; Seed manifest at the OLD url.
          (with-temp-file (expand-file-name "url-history.yaml" tmp-data)
            (insert "notes:\n  - id: shifter\n    current_url: /garden/old-name/\n    history: []\n    state: live\n"))
          (cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil)))
            (a3madkour-pub/begin-publish))
          ;; Mid-publish: record-publish writes the new URL to disk eagerly.
          (a3madkour-pub-history/record-publish "shifter" "/garden/new-name/" 'live)
          ;; Build new-set for diff-published-set (B handlers would do this
          ;; via the accumulator in real publish; here we construct one
          ;; directly for the test).
          (let* ((new-set (make-hash-table :test 'equal)))
            (puthash "shifter" (cons "/garden/new-name/" 'live) new-set)
            (let* ((diff (a3madkour-pub/diff-published-set new-set))
                   (shifted (plist-get diff :slug-shifted)))
              (should (= 1 (length shifted)))
              (should (equal '("shifter" "/garden/old-name/" "/garden/new-name/")
                             (car shifted)))))
          (a3madkour-pub/finish-publish))
      (delete-directory tmp-data t))))
```

- [ ] **Step 2: Run; verify it passes (the fix is already in place)**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-unpub-test/snapshot-fix-preserves-slug-shift-detection' 2>&1 | tail -10
```

Expected: `Ran 1 tests, 1 results as expected`. This proves Tasks 1-4 collectively closed the B-coupling bug.

- [ ] **Step 3: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
git commit -m "$(cat <<'EOF'
test(b-0): regression test for B-coupling slug-shift preservation

End-to-end test proving Tasks 1-4 closed the B-coupling bug:
record-publish writes the new URL to disk mid-publish, but
diff-published-set still sees the old URL via the snapshot, so
:slug-shifted correctly fires.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Stage 2 — `a3madkour-publish-export.el` skeleton

ox-hugo wrapper. B.0 ships the API surface + a stubbed return value. B.1 wires real ox-hugo invocation.

### Task 6: Create `-export.el` with `export-file` skeleton

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export-test.el`

- [ ] **Step 1: Write the failing test**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export-test.el`:

```elisp
;;; a3madkour-publish-export-test.el --- tests for -export.el  -*- lexical-binding: t; -*-
;;; Commentary:
;;; ert tests for the ox-hugo export wrapper.
;;; Code:

(require 'ert)
(require 'a3madkour-publish-export)

(ert-deftest a3madkour-pub-export-test/export-file-returns-plist-shape ()
  "B.0 — `export-file' returns a plist with :body, :frontmatter, :warnings keys.
B.0 ships a skeleton that returns empty values; B.1 wires real ox-hugo."
  (let ((tmp (make-temp-file "b0-export-" nil ".org")))
    (unwind-protect
        (let ((result (a3madkour-pub-export/export-file tmp nil)))
          (should (plistp result))
          (should (memq :body result))
          (should (memq :frontmatter result))
          (should (memq :warnings result))
          ;; B.0 skeleton: body is empty string, frontmatter is nil, warnings is nil.
          (should (stringp (plist-get result :body)))
          (should (null (plist-get result :frontmatter)))
          (should (null (plist-get result :warnings))))
      (delete-file tmp))))

(provide 'a3madkour-publish-export-test)
;;; a3madkour-publish-export-test.el ends here
```

- [ ] **Step 2: Run; verify fail**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-export-test/export-file-returns-plist-shape' 2>&1 | tail -10
```

Expected: FAIL with `Cannot open load file: No such file or directory, a3madkour-publish-export`.

- [ ] **Step 3: Create the module**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export.el`:

```elisp
;;; a3madkour-publish-export.el --- ox-hugo wrapper -*- lexical-binding: t; -*-

;;; Commentary:

;; Shared ox-hugo export wrapper for sub-project B's per-section
;; publishers.  Exposes a single entry point `export-file' that invokes
;; ox-hugo on a single source `.org' file and returns a structured plist:
;;
;;   (:body MARKDOWN-STRING :frontmatter ALIST :warnings (STRING ...))
;;
;; B.0 ships the API surface only — the body is empty, frontmatter and
;; warnings are nil.  B.1 (garden handler) is the first slice that wires
;; the real ox-hugo invocation.
;;
;; ox-hugo loading: ox-hugo is loaded lazily.  When B.0 is in effect
;; (skeleton stub), ox-hugo is not required.  B.1+ will add `(require
;; 'ox-hugo)' here once the real export plumbing lands.

;;; Code:

(defun a3madkour-pub-export/export-file (file dest-dir)
  "Export FILE (an absolute `.org' path) via ox-hugo.

DEST-DIR is the absolute path of the destination Hugo content section
(e.g. \"/Stuff/.../a3madkour.github.io/content/garden/\").  ox-hugo writes
the per-page bundle under DEST-DIR/<slug>/ ; the caller is responsible
for resolving the slug and matching the path.

Returns a plist:
  :body         MARKDOWN-STRING — the post-export markdown body (no frontmatter)
  :frontmatter  ALIST — keys are symbols (e.g. `title' `tags'), values are
                strings/lists/booleans as ox-hugo emits them
  :warnings     LIST OF STRINGS — non-fatal issues raised during export

B.0 skeleton: returns (:body \"\" :frontmatter nil :warnings nil) regardless
of input.  B.1 wires the real ox-hugo invocation; this docstring's contract
holds across both phases."
  ;; B.0 skeleton: no-op stub.  B.1 replaces the body with real ox-hugo
  ;; invocation that captures the export buffer + extracts frontmatter.
  (ignore file dest-dir)
  (list :body "" :frontmatter nil :warnings nil))

(provide 'a3madkour-publish-export)

;;; a3madkour-publish-export.el ends here
```

- [ ] **Step 4: Run test; verify pass**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-export-test/export-file-returns-plist-shape' 2>&1 | tail -5
```

Expected: `Ran 1 tests, 1 results as expected`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-export.el \
        emacs-configs/custom/lisp/a3madkour-publish-export-test.el
git commit -m "$(cat <<'EOF'
feat(b-0): a3madkour-publish-export skeleton

ox-hugo wrapper module with API surface and stub return.  B.0 returns
(:body \"\" :frontmatter nil :warnings nil); B.1 wires real ox-hugo
invocation.  No ox-hugo require yet — added when real plumbing lands.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Stage 3 — `a3madkour-publish-frontmatter.el` skeleton

Per-section frontmatter normalizer dispatch. B.0 ships the dispatch + a default branch; per-section bodies fill in B.1+.

### Task 7: Create `-frontmatter.el` with dispatch + B.0 default

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write the failing tests**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`:

```elisp
;;; a3madkour-publish-frontmatter-test.el --- tests for -frontmatter.el  -*- lexical-binding: t; -*-
;;; Commentary:
;;; ert tests for the per-section frontmatter normalizer dispatch.
;;; Code:

(require 'ert)
(require 'a3madkour-publish-frontmatter)

(ert-deftest a3madkour-pub-fm-test/normalize-returns-alist-with-section ()
  "B.0 — `normalize' returns the input alist annotated with section symbol.
Per-section transforms land in B.1+; B.0 ships pass-through behavior."
  (let* ((raw '((title . "Hello") (tags . ("a" "b"))))
         (result (a3madkour-pub-frontmatter/normalize 'garden raw "/tmp/foo.org")))
    (should (listp result))
    (should (equal "Hello" (alist-get 'title result)))
    (should (equal '("a" "b") (alist-get 'tags result)))))

(ert-deftest a3madkour-pub-fm-test/normalize-accepts-all-known-sections ()
  "B.0 — `normalize' dispatches without error for every section enum value."
  (dolist (section '(garden essays research-theme research-question
                     works-games works-music works-poetry
                     streams about
                     library-reading library-listening
                     library-playing library-watching))
    (should (a3madkour-pub-frontmatter/normalize section '((title . "X")) "/tmp/x.org"))))

(ert-deftest a3madkour-pub-fm-test/normalize-errors-on-unknown-section ()
  "B.0 — `normalize' signals an error for unknown section symbol."
  (should-error (a3madkour-pub-frontmatter/normalize 'made-up-section '() "/tmp/x.org")))

(provide 'a3madkour-publish-frontmatter-test)
;;; a3madkour-publish-frontmatter-test.el ends here
```

- [ ] **Step 2: Run; verify fail**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-fm-test/' 2>&1 | tail -10
```

Expected: FAIL with module load error.

- [ ] **Step 3: Create the module**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`:

```elisp
;;; a3madkour-publish-frontmatter.el --- per-section frontmatter normalizer dispatch  -*- lexical-binding: t; -*-

;;; Commentary:

;; Per-section frontmatter normalizer dispatch.  Each B.x content-type
;; slice registers its section's normalize logic by editing the dispatch
;; below.  B.0 ships dispatch infrastructure + pass-through behavior for
;; every known section.
;;
;; Contract (per design spec §7):
;;   (normalize SECTION RAW-ALIST SOURCE-FILE) -> NORMALIZED-ALIST
;;
;; SECTION is a symbol from the enum:
;;   garden | essays
;;   research-theme | research-question
;;   works-games | works-music | works-poetry
;;   streams | about
;;   library-reading | library-listening | library-playing | library-watching
;;
;; RAW-ALIST is what ox-hugo produces (keys are symbols).  SOURCE-FILE is
;; the absolute path of the source `.org' file (needed for git-mtime
;; lookups, has_* body scans, slug derivation cross-checks).
;;
;; Returns an alist with the same key shape, normalized per the section's
;; contract.  B.0 returns RAW-ALIST unchanged for any known section;
;; B.1+ replaces each per-section branch with real logic.

;;; Code:

(defconst a3madkour-pub-frontmatter--known-sections
  '(garden essays
    research-theme research-question
    works-games works-music works-poetry
    streams about
    library-reading library-listening library-playing library-watching)
  "Closed set of section symbols `normalize' accepts.  Updated as new
sections are added (none planned beyond this set).")

(defun a3madkour-pub-frontmatter/normalize (section raw-alist source-file)
  "Normalize RAW-ALIST for SECTION's frontmatter contract.

SECTION must be a symbol from `a3madkour-pub-frontmatter--known-sections';
signals `error' otherwise.

SOURCE-FILE is the absolute path of the source `.org' file (kept for
per-section normalizers that need git-mtime, body scans, etc.).

Returns a normalized alist.  B.0 returns RAW-ALIST unchanged for any
known section; per-section logic lands in B.1+ (garden), B.2 (library),
… see design spec §12 slice ordering."
  (unless (memq section a3madkour-pub-frontmatter--known-sections)
    (error "a3madkour-pub-frontmatter: unknown section %S (must be one of %S)"
           section a3madkour-pub-frontmatter--known-sections))
  (ignore source-file)  ; per-section bodies will consume this in B.1+
  ;; B.0 pass-through; B.1+ replaces this cond with per-section branches.
  (cond
   ((memq section a3madkour-pub-frontmatter--known-sections)
    raw-alist)))

(provide 'a3madkour-publish-frontmatter)

;;; a3madkour-publish-frontmatter.el ends here
```

- [ ] **Step 4: Run tests; verify pass**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-fm-test/' 2>&1 | tail -5
```

Expected: `Ran 3 tests, 3 results as expected`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el \
        emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "$(cat <<'EOF'
feat(b-0): a3madkour-publish-frontmatter skeleton + section dispatch

Per-section frontmatter normalizer dispatch with closed enum of section
symbols.  B.0 returns RAW-ALIST unchanged for any known section; B.1+
replaces per-section branches with real logic.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Stage 4 — `a3madkour-publish-living.el` skeleton

Top-level `(a3-publish-living)` command. Runs the begin/walk/finish lifecycle. In B.0 the walk yields zero notes (no per-section handlers are registered yet), so the lifecycle runs end-to-end with no content change.

### Task 8: Create `-living.el` with command skeleton

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el`

- [ ] **Step 1: Write the failing test**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el`:

```elisp
;;; a3madkour-publish-living-test.el --- tests for -living.el  -*- lexical-binding: t; -*-
;;; Commentary:
;;; ert tests for the publish-living top-level command.
;;; Code:

(require 'ert)
(require 'a3madkour-publish-living)

(ert-deftest a3madkour-pub-living-test/command-defined-and-interactive ()
  "B.0 — `a3-publish-living' is defined and interactive."
  (should (fboundp 'a3-publish-living))
  (should (commandp 'a3-publish-living)))

(ert-deftest a3madkour-pub-living-test/empty-handler-set-runs-lifecycle-clean ()
  "B.0 — with no per-section handlers registered, running publish-living
walks the (empty) handler set, calls begin/finish, and exits cleanly.
No commits to the manifest; snapshot is cleared at end."
  (let ((tmp-data (make-temp-file "b0-living-" t)))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir tmp-data)
              (a3madkour-pub/org-notes-dir tmp-data))
          (with-temp-file (expand-file-name "url-history.yaml" tmp-data)
            (insert "notes: []\n"))
          (cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil)))
            (a3-publish-living))
          ;; Snapshot cleared at end of finish-publish.
          (should-not a3madkour-pub--manifest-snapshot)
          ;; Accumulator empty (no record-publish calls happened).
          (should (zerop (hash-table-count a3madkour-pub--publish-run-accumulator))))
      (delete-directory tmp-data t))))

(provide 'a3madkour-publish-living-test)
;;; a3madkour-publish-living-test.el ends here
```

- [ ] **Step 2: Run; verify fail**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-living-test/' 2>&1 | tail -10
```

Expected: FAIL with module load error.

- [ ] **Step 3: Create the module**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el`:

```elisp
;;; a3madkour-publish-living.el --- publish-living top-level command  -*- lexical-binding: t; -*-

;;; Commentary:

;; Top-level command for sub-project B's living-surfaces publish.
;; Wraps the begin/walk/finish lifecycle around the union of per-section
;; handlers for living sections (garden, library-*, research-theme,
;; research-question).
;;
;; B.0 ships the lifecycle scaffold with an empty handler registry.
;; B.1 (garden) is the first slice to register a handler; B.2 (library)
;; and B.3 (research) fill in the rest.
;;
;; Idempotency contract (per design spec §11): running with no source
;; changes produces zero file diffs in content/ + data/.  The B.0 empty
;; handler set trivially satisfies this.

;;; Code:

(require 'a3madkour-publish)
(require 'a3madkour-publish-unpublish)

(defvar a3madkour-pub-living--handlers nil
  "Alist of (SECTION-SYMBOL . HANDLER-FUNCTION) for living sections.

HANDLER-FUNCTION takes one argument (a source file path) and emits the
corresponding Hugo content + calls `record-publish'.

B.0 ships this empty.  Each B.x slice that lands a living-section
handler will `setf' an entry here from its module's `provide' time
or init hook.  Example shape (filled in B.1+):

  ((garden . a3madkour-pub-garden/publish-garden-file)
   (library-reading . a3madkour-pub-library/publish-library-file)
   ...)")

;;;###autoload
(defun a3-publish-living ()
  "Publish all living-section source notes from `org-notes-dir'.

Runs the begin/walk/finish lifecycle.  For each registered living
handler in `a3madkour-pub-living--handlers', walks the section's source
set and invokes the handler per-file.

B.0: `a3madkour-pub-living--handlers' is empty, so the walk does nothing.
The lifecycle still runs (begin-publish populates snapshots;
finish-publish clears them) — this proves the wiring is correct without
emitting any Hugo content.

See parent design spec §4 (command surface) and §11 (idempotency)."
  (interactive)
  (a3madkour-pub/begin-publish)
  ;; Walk per-section handlers.  Empty in B.0.
  (dolist (entry a3madkour-pub-living--handlers)
    (let ((section (car entry))
          (handler (cdr entry)))
      (a3madkour-pub-living--walk-section section handler)))
  (a3madkour-pub/finish-publish))

(defun a3madkour-pub-living--walk-section (section handler)
  "Walk `org-notes-dir' for SECTION and invoke HANDLER per matching file.

A file matches SECTION when its `note-section' equals SECTION (which is
itself derived from `#+HUGO_SECTION:').  Non-matching and unpublished
files are skipped.

B.0: never called (handlers list is empty).  Tests exercise this via
direct invocation with a mock handler if desired."
  (dolist (file (directory-files-recursively
                 a3madkour-pub/org-notes-dir "\\.org\\'"))
    (when (eq section (a3madkour-pub/note-section file))
      (funcall handler file))))

(provide 'a3madkour-publish-living)

;;; a3madkour-publish-living.el ends here
```

- [ ] **Step 4: Run tests; verify pass**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-living-test/' 2>&1 | tail -5
```

Expected: `Ran 2 tests, 2 results as expected`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-living.el \
        emacs-configs/custom/lisp/a3madkour-publish-living-test.el
git commit -m "$(cat <<'EOF'
feat(b-0): a3-publish-living top-level command + handler registry

publish-living wraps begin/walk/finish around per-section handlers in
`a3madkour-pub-living--handlers' (empty in B.0; B.1+ fills in).  Empty
handler set means the lifecycle runs clean with no Hugo content change,
verifying wiring.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Stage 5 — `a3madkour-publish-deliberate.el` skeleton

Top-level `(a3-publish-deliberate file-or-id)` command. Resolves arg → file → reads HUGO_SECTION → dispatches to per-section handler. In B.0, dispatch lookup returns nil for every section, so the function signals `'no-handler-for-section` cleanly.

### Task 9: Create `-deliberate.el` with command skeleton

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate-test.el`

- [ ] **Step 1: Write the failing tests**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate-test.el`:

```elisp
;;; a3madkour-publish-deliberate-test.el --- tests for -deliberate.el  -*- lexical-binding: t; -*-
;;; Commentary:
;;; ert tests for the publish-deliberate top-level command.
;;; Code:

(require 'ert)
(require 'a3madkour-publish-deliberate)

(ert-deftest a3madkour-pub-delib-test/command-defined-and-interactive ()
  "B.0 — `a3-publish-deliberate' is defined and interactive."
  (should (fboundp 'a3-publish-deliberate))
  (should (commandp 'a3-publish-deliberate)))

(ert-deftest a3madkour-pub-delib-test/unknown-section-errors-clean ()
  "B.0 — given an org file with #+HUGO_SECTION: <known section>, but no
handler registered, signals `error' with a clear message identifying the
section.  This is B.0's expected behavior; B.1+ adds handlers."
  (let ((tmp (make-temp-file "b0-delib-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp
            (insert "#+title: Test\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n:PROPERTIES:\n:ID: test-id-001\n:END:\n\nbody\n"))
          (let ((err-data (should-error (a3-publish-deliberate tmp))))
            (should (string-match-p "garden" (cadr err-data)))))
      (delete-file tmp))))

(provide 'a3madkour-publish-deliberate-test)
;;; a3madkour-publish-deliberate-test.el ends here
```

- [ ] **Step 2: Run; verify fail**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-delib-test/' 2>&1 | tail -10
```

Expected: FAIL with module load error.

- [ ] **Step 3: Create the module**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate.el`:

```elisp
;;; a3madkour-publish-deliberate.el --- publish-deliberate top-level command  -*- lexical-binding: t; -*-

;;; Commentary:

;; Top-level command for sub-project B's deliberate-surfaces publish.
;; Wraps the begin/finish lifecycle around a SINGLE per-section handler
;; invocation, scoped to one source file (or org-roam ID resolved to a
;; file).  Intended for human-reviewed publishes (essays, works items,
;; streams items, about).
;;
;; B.0 ships the lifecycle scaffold with an empty handler registry.
;; B.4 (essays) is the first slice to register a handler.

;;; Code:

(require 'a3madkour-publish)
(require 'a3madkour-publish-unpublish)

(defvar a3madkour-pub-deliberate--handlers nil
  "Alist of (SECTION-SYMBOL . HANDLER-FUNCTION) for deliberate sections.

HANDLER-FUNCTION takes one argument (a source file path) and emits the
corresponding Hugo content + calls `record-publish'.

Same shape as `a3madkour-pub-living--handlers' but a separate registry
because some sections might exist in both (uncommon but possible).
B.0 ships this empty; B.4 (essays), B.5 (works), B.6 (streams), B.7
(about) each populate one entry.")

;;;###autoload
(defun a3-publish-deliberate (file-or-id)
  "Publish a single deliberate-section note identified by FILE-OR-ID.

FILE-OR-ID is either an absolute file path to a `.org' source file or an
org-roam UUID string.  Reads `#+HUGO_SECTION:' from the file; dispatches
to the handler registered in `a3madkour-pub-deliberate--handlers' for
that section.

B.0: every section's handler is unregistered, so this signals `error'
with a clear message naming the section that lacks a handler.  This is
expected; B.4+ adds handlers per section.

See parent design spec §4 (command surface)."
  (interactive "fOrg file or ID: ")
  (a3madkour-pub/begin-publish)
  (unwind-protect
      (let* ((file (a3madkour-pub--resolve-file-or-id file-or-id))
             (section (a3madkour-pub/note-section file))
             (handler (cdr (assq section a3madkour-pub-deliberate--handlers))))
        (unless handler
          (error "a3madkour-pub-deliberate: no handler registered for section %S (file: %s)"
                 section file))
        (funcall handler file))
    (a3madkour-pub/finish-publish)))

(provide 'a3madkour-publish-deliberate)

;;; a3madkour-publish-deliberate.el ends here
```

- [ ] **Step 4: Run tests; verify pass**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh -t 'a3madkour-pub-delib-test/' 2>&1 | tail -5
```

Expected: `Ran 2 tests, 2 results as expected`.

If the second test fails because `note-section` returns nil instead of `'garden` for an unsaved tmp file:
- `note-section` resolves through the metadata cache which is keyed on absolute path.  Verify the test file path is absolute (`make-temp-file` returns absolute by default).
- If still failing, the error matching may be against `nil` rather than the literal string `"garden"`; the error message format includes `%S` which prints `nil` as `nil`.  In that case, the test should match for `"no handler registered for section"` instead of `"garden"`.  Update the test's `string-match-p` argument to `"no handler registered"` and re-run.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-deliberate.el \
        emacs-configs/custom/lisp/a3madkour-publish-deliberate-test.el
git commit -m "$(cat <<'EOF'
feat(b-0): a3-publish-deliberate top-level command + handler registry

publish-deliberate resolves file-or-id, reads HUGO_SECTION, dispatches
to a registered handler.  B.0 errors cleanly when no handler is
registered for a section; B.4+ adds handlers (essays, works, streams,
about).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Stage 6 — `a3-pub.sh` flag intercepts

Mirror the existing `--check-orphans` block for `--publish-living` and `--publish-deliberate <path>`.  Also add `-l` lines for the four new modules under the existing exec at the bottom of the file (so ad-hoc `--eval` invocations see them too).

### Task 10: Add `-l` for new modules in the default exec block

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` (the default exec at the bottom, lines 58-70)

- [ ] **Step 1: Read current state of `a3-pub.sh`**

```bash
cat ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh
```

Confirm the file ends with an `exec emacs --batch …` block that loads `a3madkour-publish`, `-rewrite`, `-assets`, `-unpublish` and then runs `--eval "(message \"[a3-pub] ready (v%s)\" a3madkour-pub/version)"`.

- [ ] **Step 2: Add new module loads to the default exec**

In the default exec block (the one at the bottom of the file, starting around line 58), find these lines:

```bash
  -l a3madkour-publish \
  -l a3madkour-publish-rewrite \
  -l a3madkour-publish-assets \
  -l a3madkour-publish-unpublish \
```

Replace with:

```bash
  -l a3madkour-publish \
  -l a3madkour-publish-rewrite \
  -l a3madkour-publish-assets \
  -l a3madkour-publish-unpublish \
  -l a3madkour-publish-export \
  -l a3madkour-publish-frontmatter \
  -l a3madkour-publish-living \
  -l a3madkour-publish-deliberate \
```

- [ ] **Step 3: Verify the wrapper still loads cleanly**

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --eval '(message "[a3-pub] modules-loaded ok")' 2>&1 | tail -5
```

Expected: see `[a3-pub] modules-loaded ok` in the output (along with the `[a3-pub] ready (vX.X)` line). No load errors.

- [ ] **Step 4: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3-pub.sh
git commit -m "$(cat <<'EOF'
chore(b-0): load new B.0 modules in a3-pub.sh default exec

Adds -l flags for -export, -frontmatter, -living, -deliberate so
ad-hoc --eval invocations of the wrapper see them.  Flag intercepts
in Tasks 11 + 12 will load these same modules under their own paths.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Task 11: Add `--publish-living` flag intercept to `a3-pub.sh`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` (insert a new intercept block after the existing `--check-orphans` block, before the default exec)

- [ ] **Step 1: Identify the insertion point**

The existing `--check-orphans` intercept ends with `fi` on line 50. Insert the new intercept block immediately after that `fi` (before the `if [ ! -f "$STRAIGHT_BOOTSTRAP" ]` block on line 52).

- [ ] **Step 2: Insert the `--publish-living` block**

Insert (between lines 50 and 52):

```bash

# B.0: --publish-living flag intercept.  Runs (a3-publish-living) under
# the same straight bootstrap as the default exec.  Same as `M-x
# a3-publish-living' from inside emacs.
if [ "${1:-}" = "--publish-living" ]; then
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
    -l a3madkour-publish-export \
    -l a3madkour-publish-frontmatter \
    -l a3madkour-publish-living \
    -l a3madkour-publish-deliberate \
    --eval "(a3-publish-living)" \
    --eval "(kill-emacs 0)" \
    "$@"
fi
```

- [ ] **Step 3: Smoke test**

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living 2>&1 | tail -10
```

Expected: command completes with exit code 0; minimal output (B.0 handler set is empty so no Hugo content is emitted; just begin-publish + finish-publish run quietly).

If the command crashes with `wrong type argument` or similar, verify `(a3-publish-living)` returns cleanly when called from a fresh emacs invocation:

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --eval '(a3-publish-living)' 2>&1 | tail -10
```

This should also exit 0.

- [ ] **Step 4: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3-pub.sh
git commit -m "$(cat <<'EOF'
feat(b-0): a3-pub.sh --publish-living flag intercept

Mirrors --check-orphans pattern: bootstraps straight, loads all
publisher modules, calls (a3-publish-living), exits 0.  B.0 handler
set is empty so the run completes silently.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### Task 12: Add `--publish-deliberate <path>` flag intercept

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` (insert another intercept after `--publish-living`)

- [ ] **Step 1: Insert the `--publish-deliberate` block**

Immediately after the `--publish-living` block's closing `fi` (just added in Task 11), insert:

```bash

# B.0: --publish-deliberate <path> flag intercept.  Runs
# (a3-publish-deliberate <path>) under the same straight bootstrap.
# Same as `M-x a3-publish-deliberate' from inside emacs.
if [ "${1:-}" = "--publish-deliberate" ]; then
  shift
  if [ $# -lt 1 ]; then
    echo "a3-pub.sh --publish-deliberate: missing required <path> argument" >&2
    exit 2
  fi
  target_path="$1"
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
    -l a3madkour-publish-export \
    -l a3madkour-publish-frontmatter \
    -l a3madkour-publish-living \
    -l a3madkour-publish-deliberate \
    --eval "(condition-case err
              (a3-publish-deliberate \"$target_path\")
              (error (princ (format \"ERROR: %s\\n\" (error-message-string err)))
                     (kill-emacs 1)))" \
    --eval "(kill-emacs 0)" \
    "$@"
fi
```

- [ ] **Step 2: Smoke test the missing-arg branch**

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate 2>&1
echo "exit: $?"
```

Expected: error message `a3-pub.sh --publish-deliberate: missing required <path> argument`; exit 2.

- [ ] **Step 3: Smoke test with a temporary unhandled-section org file**

```bash
TMPORG=$(mktemp --suffix=.org)
cat > "$TMPORG" <<'EOF'
#+title: Test
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
:PROPERTIES:
:ID: smoke-test-001
:END:

body
EOF
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate "$TMPORG" 2>&1 | tail -10
echo "exit: $?"
rm "$TMPORG"
```

Expected: output contains `ERROR: a3madkour-pub-deliberate: no handler registered for section garden …`; exit 1.

This confirms the flag is wired and the B.0 expected-error path works.

- [ ] **Step 4: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3-pub.sh
git commit -m "$(cat <<'EOF'
feat(b-0): a3-pub.sh --publish-deliberate <path> flag intercept

Mirrors --check-orphans pattern: bootstraps straight, loads modules,
calls (a3-publish-deliberate <path>).  Missing-arg branch exits 2 with
clear message.  B.0 unhandled-section path exits 1 with the
no-handler-registered error.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Stage 7 — Wrap-up

### Task 13: Full test suite green; commit count audit

- [ ] **Step 1: Run the full ert suite**

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5
```

Expected: `Ran NNN tests, NNN results as expected, 0 unexpected` where NNN ≥ 240 (≈223 baseline + ≈15-20 new B.0 tests).

If any test fails unexpectedly, **stop and diagnose before continuing**. Common failure modes:
- A B.0 test depended on org-roam-db-sync being stubbed; check `cl-letf` usage in the test body.
- A test created tmp dirs but didn't bind `a3madkour-pub/site-data-dir` to them; the `--manifest-path` helper signals user-error when site-data-dir is nil.
- The snapshot fix introduced a regression in an A.1.d test that exercised `diff-published-set` mid-publish; check that the test still wraps in begin/finish if it expects snapshot semantics.

- [ ] **Step 2: Verify B.0 commit count**

```bash
cd ~/dotfiles
git log --oneline | head -15
```

Expected: top of log shows ≈9-12 commits with `(b-0)` in the message (one per task: Tasks 1-12; some tasks bundle test+impl into one commit per the task structure).

### Task 14: Update site repo CLAUDE.md status pointer

**Files:**
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md`

- [ ] **Step 1: Read the current "Project status" section**

```bash
grep -n "Project status\|Most recent\|sub-project A" /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md | head -10
```

Locate the lines that currently say "Sub-project A is now fully shipped" and "next overall slice = Phase 3 sub-project B".

- [ ] **Step 2: Edit the pointer**

In `CLAUDE.md`, find the line within the Phase 3 → sub-project A entry that reads (or contains a phrasing equivalent to):

```
**All five shipped: A.1.0 (bootstrap) + A.1.a (foundations) + A.1.b (link rewriter) + A.1.c (asset handling + 24th linter pair) + A.1.d (unpublish flow + integration tests) implementation complete; 223 ert tests passing + Python integration fixtures grown 4 → 8. Sub-project A is now fully shipped; next overall slice = Phase 3 sub-project B (per-content-type publisher + templates).**
```

Update to:

```
**All five shipped: A.1.0 (bootstrap) + A.1.a (foundations) + A.1.b (link rewriter) + A.1.c (asset handling + 24th linter pair) + A.1.d (unpublish flow + integration tests) implementation complete; 223 ert tests passing + Python integration fixtures grown 4 → 8. Sub-project A is now fully shipped. Sub-project B is in progress: B.0 (shared publisher infrastructure — export wrapper, frontmatter dispatch, living/deliberate command scaffolding, a3-pub.sh flags, manifest snapshot fix) staged 2026-05-24 in dotfiles. Next: B.1 (garden handler).**
```

- [ ] **Step 3: Verify the edit took**

```bash
grep -n "B.0\|sub-project B" /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md | head -5
```

Expected: the line you just edited appears in the grep output.

- [ ] **Step 4: Commit + push the site repo**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(phase-3): CLAUDE.md status — B.0 shared infra staged

B.0 (shared publisher infrastructure: export wrapper, frontmatter
dispatch, living/deliberate command scaffolding, a3-pub.sh flags,
manifest snapshot fix) staged in dotfiles.  Next: B.1 (garden handler).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin master
```

Expected: push succeeds.

### Task 15: Final verification + handoff memo

- [ ] **Step 1: Re-run the elisp test suite once more from a fresh shell**

(Catches any environment-state issues that only surface in a clean session.)

```bash
~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5
```

Expected: still green.

- [ ] **Step 2: Smoke-test both shell intercepts once more**

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "publish-living exit: $?"

TMPORG=$(mktemp --suffix=.org)
cat > "$TMPORG" <<'EOF'
#+title: Smoke
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
:PROPERTIES:
:ID: final-smoke-001
:END:
body
EOF
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate "$TMPORG"
echo "publish-deliberate exit: $?"
rm "$TMPORG"
```

Expected:
- `publish-living exit: 0`
- `publish-deliberate exit: 1` (with `ERROR: a3madkour-pub-deliberate: no handler registered for section garden …` message).

- [ ] **Step 3: Write a B.0 completion memory entry**

Create `/home/a3madkour/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_b0_complete.md`:

```markdown
---
name: b0-complete
description: "B.0 shared publisher infrastructure slice — landed: 4 new dotfiles modules + 4 sibling tests + a3-pub.sh flag intercepts + manifest snapshot fix. ~240 ert tests total. Site CLAUDE.md status updated + pushed. Next slice = B.1 garden handler."
metadata:
  node_type: memory
  type: project
---

**Shipped (2026-05-24)**: B.0 — shared publisher infrastructure per `docs/superpowers/plans/2026-05-24-phase-3-b-0-shared-infra.md` (15 tasks, 7 stages).

**Test counts at slice end:**
- ert: ≈240 total (223 A.1.d baseline + ≈17 B.0 new across 5 new modules + snapshot-fix tests).
- Python linter pairs: unchanged (24); B.0 emits no content.
- Python integration fixtures: unchanged (8); B.1 will start growing this.

**Dotfiles state:**
- 4 new modules + 4 sibling tests: `a3madkour-publish-{export,frontmatter,living,deliberate}.el` + `-test.el`.
- 3 modified A.1 modules: `-publish.el` (snapshot defvar + begin-publish populates), `-publish-history.el` (snapshot-aware reader), `-publish-unpublish.el` (diff-published-set switches to snapshot reader + finish-publish clears).
- Wrapper: `a3-pub.sh` extended with `--publish-living` + `--publish-deliberate <path>` intercepts; default exec loads new modules.

**Site state:**
- `CLAUDE.md` status pointer updated + pushed (commit `<hash>`).
- No content/data/template changes (B.0 emits nothing).

**Architectural artifact verified:**
- B-coupling regression test in `-unpublish-test.el` proves snapshot fix works end-to-end (record-publish mid-publish → diff-published-set still detects slug shift).

**Next slice: B.1 (garden handler).** Should:
- Create `a3madkour-publish-garden.el` + sibling test.
- Register `(garden . a3madkour-pub-garden/publish-garden-file)` in `a3madkour-pub-living--handlers`.
- Fill in `frontmatter/normalize` garden branch with growth_stage derivation + flavor inference + topic_map pass-through.
- Wire link-rewriter + asset-copy into the garden handler.
- Add 3-4 new integration fixtures under `tools/test_publish_integration.py`.
- First slice to emit real Hugo content; transition garden fixtures per design spec §11.

**Cross-references:**
- Parent spec: `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md`
- B.0 plan: `docs/superpowers/plans/2026-05-24-phase-3-b-0-shared-infra.md`
- Prior slice memory: [[a1d-complete]]
```

Then add the pointer to `MEMORY.md`:

```bash
# Edit /home/a3madkour/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/MEMORY.md
# Add this line at an appropriate spot (e.g., right after the a1d-complete line):
- [B.0 shared infra complete](project_b0_complete.md) — 4 new modules + snapshot fix; ~240 ert tests; CLAUDE.md status pushed; next = B.1 garden handler
```

- [ ] **Step 4: Update `memory/project_next_slice.md` pointer**

The existing `project_next_slice.md` says "Next slice = Phase 3 sub-project B". Update it to point at B.1 specifically:

Edit `/home/a3madkour/.claude/projects/-Stuff-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_next_slice.md` — change the first line to:

```
**Next slice = Phase 3 sub-project B.1 — garden handler.** B.0 (shared infra) shipped 2026-05-24; see [[b0-complete]].
```

And note that the architectural decisions are already settled in the parent B spec; B.1 is a plan-only slice (no new brainstorm needed) unless the garden growth_stage derivation surfaces surprises.

- [ ] **Step 5: Done. B.0 complete.**

Both repos are in a clean state:
- Site repo: clean, pushed, all 5 new spec/plan/status commits on origin/master.
- Dotfiles repo: clean, ≈12 new B.0 commits accumulated locally (per author preference, NOT pushed).

The author can pick up B.1 on any machine that has both repos synced.

---

## Self-review notes

**Spec coverage check:**

| Spec §/requirement | Plan task(s) |
|---|---|
| §5 module list — `-export.el` skeleton | Task 6 |
| §5 module list — `-frontmatter.el` skeleton + dispatch | Task 7 |
| §5 module list — `-living.el` + handler registry | Task 8 |
| §5 module list — `-deliberate.el` + handler registry | Task 9 |
| §6 B-coupling fix — snapshot defvar | Task 1 |
| §6 B-coupling fix — begin-publish populates | Task 2 |
| §6 B-coupling fix — diff-published-set reads snapshot | Task 3 |
| §6 B-coupling fix — finish-publish clears | Task 4 |
| §6 B-coupling fix — regression-proven | Task 5 |
| §4 command surface — M-x `a3-publish-living` | Task 8 |
| §4 command surface — M-x `a3-publish-deliberate` | Task 9 |
| §4 command surface — `a3-pub.sh --publish-living` | Task 11 |
| §4 command surface — `a3-pub.sh --publish-deliberate <path>` | Task 12 |
| `a3-pub.sh` default exec loads new modules | Task 10 |
| Site CLAUDE.md status pointer updated + pushed | Task 14 |

All B.0-scoped requirements have at least one task. Per-section handler bodies, per-section frontmatter content, and Hugo content emission are deferred to B.1-B.7 by design.

**Out-of-scope items reaffirmed:**
- No per-section handlers register in B.0 (registry list is empty).
- `export-file` returns a stub plist; no ox-hugo invocation.
- `normalize` returns input unchanged for every section.
- `publish-deliberate` errors cleanly on every section call.
- No Hugo content is emitted; no fixtures are cleared.

This keeps B.0 small and bounded; B.1+ does the user-visible work.
