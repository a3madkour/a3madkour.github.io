# Phase 3 A.1.b — Link Rewriter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Session policy default (mirrors A.1.a):** stage files with `git add` but do NOT git-commit autonomously. Final task surfaces suggested commit messages for the author. If the author signals "commit as you go" at session start, switch to per-task commits.

**Goal:** Implement A.1.b — the link rewriter (`rewrite-link`) covering id-links, file-link auto-convert, heading anchors, external pass-through, custom typed links — plus the org-roam ID dispatching layer so `published-p`/`note-url`/`note-section`/`note-slug` accept UUIDs, the `note-metadata` accessor + per-publish memoization, and the `slug_override` reason resolution. Asset-shaped links return a `:pending-asset` sentinel that A.1.c upgrades. All TDD.

**Architecture:** Two new files (`a3madkour-publish-rewrite.el` for the rewriter + anchor slugifier; `a3madkour-publish-id.el` for the org-roam ID→file lookup), plus modifications to the existing entry-point (`a3madkour-publish.el`) and history module (`a3madkour-publish-history.el`). Cache state lives in a defvar in the entry-point. The `org-roam` dep is isolated to `-id.el`; the rewriter unit-tests mock it out so per-link-type tests don't need a real DB.

**Tech Stack:** Emacs 30.2 + ert (built-in) + yaml.el (already installed in A.1.0) + **org-roam** (new dep, installed via straight.el) + bash test runner.

**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §6, §8, §10, §11 (snapshot-at-publish-start subsection).

**Design doc (this slice):** `docs/superpowers/specs/2026-05-20-phase-3-a1-b-link-rewriter-design.md`.

**Prior plan:** `docs/superpowers/plans/2026-05-20-phase-3-a1-a-foundations.md` (A.1.a foundations — must be complete + verified; 45 ert tests green).

**Carry-forward memory:** `memory/project_a1a_to_a1b_carryforward.md`.

---

## File Structure

**Created (dotfiles repo):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el` — `rewrite-link` + per-link-type dispatcher + heading-anchor slugifier + custom-typed-link defcustom
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id.el` — `--id-to-file` + org-roam dep boundary
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id-test.el`

**Modified (dotfiles repo):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` — introduces `note-metadata` + per-publish hash table `--metadata-cache`; the 4 public accessors become thin wrappers over `note-metadata` AND now accept `file-or-id` (dispatching via `--id-to-file` from `-id.el`); drops redundant empty-string guards in `note-section`/`note-slug`; new `(begin-publish)` entry-point resets the cache + invokes `org-roam-db-sync`.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el` — adds tests for `note-metadata`, cache discipline, `begin-publish`, file-or-id dispatch.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el` — `record-publish` gains `&key had-slug-override-p`; `--diff-reason` emits `slug_override` when the flag is `t`.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el` — adds tests for the new keyword arg branches.
- `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh` — adds `(straight-use-package 'org-roam)` to the bootstrap so the new dep is loadable in batch.

**Author-manual (not enforced by tests):**
- `~/dotfiles/emacs-configs/custom/config.org` — add `(straight-use-package 'org-roam) (require 'org-roam)` near the existing yaml install for permanence.

**Out of scope** (deferred to A.1.c / A.1.d / A.2):
- Asset link real handling + 24th linter pair (A.1.c)
- Unpublish flow + integration tests (A.1.d)
- `--strict` mode + `:noexport:` link rejection + typed-backlinks real data (A.2)

---

### Task 1: Install `org-roam` via straight.el

**Files:**
- None created/modified — emacs-side package install + verify.

- [ ] **Step 1: Check whether org-roam is already loadable**

Run:
```bash
emacs --batch --eval "(condition-case err (progn (require 'org-roam) (message \"org-roam ok: %s\" (org-roam-version))) (error (message \"org-roam missing: %s\" err)))"
```

If output begins with `org-roam ok:`, skip to Step 4 (already installed). If `org-roam missing:`, continue to Step 2.

- [ ] **Step 2: Install via straight.el in a one-shot batch invocation**

Find the bootstrap file (path may differ slightly per machine):
```bash
find ~/dotfiles/emacs-configs/custom/straight -name "bootstrap.el" -path "*/straight.el/*"
```

Then install (substituting the discovered path):
```bash
emacs --batch \
  -l <discovered-bootstrap-path> \
  --eval "(straight-use-package 'org-roam)" \
  --eval "(message \"installed: %s\" (locate-library \"org-roam\"))"
```

Expected: a long install log, then a final `installed: /home/.../straight/build/org-roam/org-roam.el`.

- [ ] **Step 3: Re-run the load check**

```bash
emacs --batch \
  -l <discovered-bootstrap-path> \
  --eval "(straight-use-package 'org-roam)" \
  --eval "(require 'org-roam)" \
  --eval "(message \"org-roam ok: %s\" (org-roam-version))"
```

Expected: `org-roam ok: <version-string>` (e.g., `org-roam ok: 2.2.2`).

- [ ] **Step 4: Note in config.org for permanence (author manual)**

Author opens `~/dotfiles/emacs-configs/custom/config.org`, finds the same `*** Exporting to website` heading where yaml was added in A.1.a, and adds inside the emacs-lisp block:

```elisp
(straight-use-package 'org-roam)
(require 'org-roam)
```

Then re-tangle (`C-c C-v t` from within config.org) so `config.el` carries the change. Skip if already present. Manual step; not enforced by tests.

---

### Task 2: Add `org-roam` to the test runner bootstrap

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`

- [ ] **Step 1: Locate the existing yaml bootstrap line**

Run:
```bash
grep -n "straight-use-package" ~/dotfiles/emacs-configs/custom/lisp/run-tests.sh
```

You should see a line invoking `straight-use-package` for `yaml` from A.1.0. The new `org-roam` line goes immediately after.

- [ ] **Step 2: Insert org-roam bootstrap**

Edit `run-tests.sh` to add an `--eval "(straight-use-package 'org-roam)"` line in the same emacs invocation that bootstraps yaml. Example (depending on existing format):

```bash
emacs --batch \
  -l <bootstrap-path> \
  --eval "(straight-use-package 'yaml)" \
  --eval "(straight-use-package 'org-roam)" \
  -L "$LISP_DIR" \
  $(find "$LISP_DIR" -name "*-test.el" -printf '-l %p ')\
  -f ert-run-tests-batch-and-exit
```

(If the existing structure differs, preserve it; just add the one `--eval` line for org-roam.)

- [ ] **Step 3: Run the existing test suite — all 45 still green**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`

Expected: `Ran 45 tests, 45 results as expected, 0 unexpected`. Bootstrap may print extra install lines on first run; that's fine — only the ert summary line matters.

---

### Task 3: Introduce `note-metadata` (single-pass accessor; no memoization yet)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-test.el` (before the `provide` form):

```elisp
;; -- note-metadata --

(ert-deftest a3madkour-pub-test/note-metadata-returns-plist ()
  "note-metadata returns a plist with :id :section :slug :state :file :title."
  (let ((file (make-temp-file "a3pub-meta-" nil ".org"
                              "#+title: My Note
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
:PROPERTIES:
:ID: 11111111-1111-1111-1111-111111111111
:END:
")))
    (unwind-protect
        (let ((md (a3madkour-pub/note-metadata file)))
          (should (equal (plist-get md :section) "garden"))
          (should (equal (plist-get md :slug) "my-note"))
          (should (equal (plist-get md :state) 'live))
          (should (equal (plist-get md :file) file))
          (should (equal (plist-get md :title) "My Note"))
          (should (equal (plist-get md :id) "11111111-1111-1111-1111-111111111111")))
      (delete-file file))))

(ert-deftest a3madkour-pub-test/note-metadata-returns-nil-for-unpublished ()
  "note-metadata returns nil when HUGO_PUBLISH is absent."
  (let ((file (make-temp-file "a3pub-meta-" nil ".org" "#+title: Plain note\n")))
    (unwind-protect
        (should-not (a3madkour-pub/note-metadata file))
      (delete-file file))))

(ert-deftest a3madkour-pub-test/note-metadata-draft-state ()
  "note-metadata returns :state 'draft when HUGO_DRAFT: t."
  (let ((file (make-temp-file "a3pub-meta-" nil ".org"
                              "#+title: Draft
#+HUGO_PUBLISH: t
#+HUGO_SECTION: essays
#+HUGO_DRAFT: t
")))
    (unwind-protect
        (should (equal (plist-get (a3madkour-pub/note-metadata file) :state) 'draft))
      (delete-file file))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failing tests with `Symbol's function definition is void: a3madkour-pub/note-metadata`.

- [ ] **Step 3: Implement `note-metadata`**

Open `a3madkour-publish.el`. Find the existing `--parse-file` private helper. Add `note-metadata` as a public function that just calls `--parse-file` and returns its result (no caching yet — that comes in Task 4). Position it just before the existing `published-p` defun.

```elisp
(defun a3madkour-pub/note-metadata (file)
  "Return a plist of publish-relevant metadata for FILE, or nil if unpublished.

Plist keys:
  :id       — the org-roam :ID: property (string), or nil if absent.
  :section  — `#+HUGO_SECTION:` value as string (validated against
              `a3madkour-pub/sections`), or nil.
  :slug     — title-derived slug, overridden by `#+HUGO_SLUG:' if set.
  :state    — `'live | 'draft`.
  :file     — absolute path to FILE.
  :title    — `#+title:` value.

Returns nil if `#+HUGO_PUBLISH:' is not `t`.

SNAPSHOT SEMANTICS: in A.1.b+, this function is cached per publish run
via `a3madkour-pub/begin-publish'; edits to FILE made after the cache
warms are NOT picked up until the next publish run."
  (a3madkour-pub--parse-file file))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 48 tests, 48 results as expected, 0 unexpected`.

---

### Task 4: Per-publish hash-table memoization

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-test.el`:

```elisp
(ert-deftest a3madkour-pub-test/note-metadata-cache-hit ()
  "A second call to note-metadata on the same FILE returns cached value
without re-parsing the file (verified by mutating the file between
calls and observing the original value still returned)."
  (let ((file (make-temp-file "a3pub-cache-" nil ".org"
                              "#+title: V1
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
")))
    (unwind-protect
        (progn
          (a3madkour-pub--reset-metadata-cache)  ; start clean
          (let ((md1 (a3madkour-pub/note-metadata file)))
            (should (equal (plist-get md1 :title) "V1"))
            ;; Mutate file under the cache's feet
            (with-temp-file file
              (insert "#+title: V2\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n"))
            (let ((md2 (a3madkour-pub/note-metadata file)))
              ;; Cache hit: still V1, not V2
              (should (equal (plist-get md2 :title) "V1")))))
      (delete-file file))))

(ert-deftest a3madkour-pub-test/note-metadata-cache-explicit-reset ()
  "After --reset-metadata-cache, the next note-metadata call re-parses."
  (let ((file (make-temp-file "a3pub-cache-" nil ".org"
                              "#+title: V1
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
")))
    (unwind-protect
        (progn
          (a3madkour-pub--reset-metadata-cache)
          (a3madkour-pub/note-metadata file)  ; populate
          (with-temp-file file
            (insert "#+title: V2\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n"))
          (a3madkour-pub--reset-metadata-cache)  ; reset
          (should (equal (plist-get (a3madkour-pub/note-metadata file) :title) "V2")))
      (delete-file file))))

(ert-deftest a3madkour-pub-test/note-metadata-cache-multiple-files ()
  "The cache distinguishes between multiple files keyed by abs path."
  (let ((f1 (make-temp-file "a3pub-multi-1-" nil ".org"
                            "#+title: One
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
"))
        (f2 (make-temp-file "a3pub-multi-2-" nil ".org"
                            "#+title: Two
#+HUGO_PUBLISH: t
#+HUGO_SECTION: essays
")))
    (unwind-protect
        (progn
          (a3madkour-pub--reset-metadata-cache)
          (should (equal (plist-get (a3madkour-pub/note-metadata f1) :title) "One"))
          (should (equal (plist-get (a3madkour-pub/note-metadata f2) :title) "Two"))
          (should (equal (plist-get (a3madkour-pub/note-metadata f1) :section) "garden"))
          (should (equal (plist-get (a3madkour-pub/note-metadata f2) :section) "essays")))
      (delete-file f1)
      (delete-file f2))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failing tests with `void function: a3madkour-pub--reset-metadata-cache` and/or cache-hit assertion failures.

- [ ] **Step 3: Implement the cache + reset helper**

In `a3madkour-publish.el`, add (before `note-metadata`):

```elisp
(defvar a3madkour-pub--metadata-cache
  (make-hash-table :test 'equal)
  "Per-publish-run cache of file path → metadata plist (see `a3madkour-pub/note-metadata`).
Reset explicitly via `a3madkour-pub--reset-metadata-cache` at the start of each
publish run (called from `a3madkour-pub/begin-publish`).")

(defun a3madkour-pub--reset-metadata-cache ()
  "Clear the per-publish metadata cache. Idempotent."
  (setq a3madkour-pub--metadata-cache (make-hash-table :test 'equal)))
```

Then update `note-metadata` to consult the cache, keyed by absolute path:

```elisp
(defun a3madkour-pub/note-metadata (file)
  "<docstring from Task 3 — unchanged>"
  (let* ((abs (expand-file-name file))
         (cached (gethash abs a3madkour-pub--metadata-cache 'a3-pub-miss)))
    (if (eq cached 'a3-pub-miss)
        (let ((md (a3madkour-pub--parse-file abs)))
          ;; Cache even nil results so unpublished files don't re-parse.
          (puthash abs md a3madkour-pub--metadata-cache)
          md)
      cached)))
```

(`'a3-pub-miss` is a sentinel symbol so `nil` cache hits — i.e., known-unpublished files — return `nil` without re-parsing.)

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 51 tests, 51 results as expected, 0 unexpected`.

---

### Task 5: `begin-publish` entry-point (cache reset + DB sync)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-test.el`:

```elisp
(ert-deftest a3madkour-pub-test/begin-publish-resets-cache ()
  "begin-publish clears the metadata cache."
  (puthash "/some/file" '(:title "stale") a3madkour-pub--metadata-cache)
  (cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil)))
    (a3madkour-pub/begin-publish))
  (should (zerop (hash-table-count a3madkour-pub--metadata-cache))))

(ert-deftest a3madkour-pub-test/begin-publish-invokes-org-roam-db-sync ()
  "begin-publish calls (org-roam-db-sync) to snapshot ID resolution state."
  (let ((called nil))
    (cl-letf (((symbol-function 'org-roam-db-sync) (lambda () (setq called t))))
      (a3madkour-pub/begin-publish))
    (should called)))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 2 failing tests with `void function: a3madkour-pub/begin-publish`.

- [ ] **Step 3: Implement `begin-publish`**

Add `(require 'cl-lib)` to the top of `a3madkour-publish.el` if not already present.

Append before `(provide 'a3madkour-publish)`:

```elisp
(defun a3madkour-pub/begin-publish ()
  "Take per-publish snapshots: reset metadata cache; sync org-roam DB.

Call this at the start of any publish run (shell or interactive).
Both A's accessors and the link rewriter rely on these snapshots being
fresh; edits made after this call are NOT picked up until the next
`begin-publish` call.

See parent spec §11 (snapshot-at-publish-start subsection)."
  (a3madkour-pub--reset-metadata-cache)
  (require 'org-roam)
  (org-roam-db-sync))
```

The `cl-letf` in the test injects a no-op `org-roam-db-sync`, so the real one isn't invoked during tests — important because the real one needs a working org-roam-directory + SQLite, and we don't want test runs to touch the author's actual DB.

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 53 tests, 53 results as expected, 0 unexpected`.

---

### Task 6: Refactor 4 public accessors to thin wrappers + drop redundant guards

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`

This task is a pure refactor — no new tests; the existing accessor tests must remain green.

- [ ] **Step 1: Snapshot current test count**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -3`
Note the count (expected `53` post-Task-5).

- [ ] **Step 2: Refactor `published-p`**

Locate the existing `published-p` defun in `a3madkour-publish.el`. Replace its body so it just queries `note-metadata`:

```elisp
(defun a3madkour-pub/published-p (file)
  "Return `'live`, `'draft`, or nil for FILE.
See `a3madkour-pub/note-metadata` for snapshot/caching behavior.
A.1.b note: FILE-or-ID dispatching lands in Task 9."
  (when-let ((md (a3madkour-pub/note-metadata file)))
    (plist-get md :state)))
```

- [ ] **Step 3: Refactor `note-section`, drop empty-string guard**

Replace:

```elisp
(defun a3madkour-pub/note-section (file)
  "Return the `#+HUGO_SECTION:' value for FILE as a string, or nil.
See `a3madkour-pub/note-metadata` for snapshot/caching behavior."
  (plist-get (a3madkour-pub/note-metadata file) :section))
```

Confirm the existing belt-and-suspenders `string-empty-p` check is gone — `--parse-file` already normalizes empty strings to nil at parse time.

- [ ] **Step 4: Refactor `note-slug`, drop empty-string guard**

```elisp
(defun a3madkour-pub/note-slug (file)
  "Return the derived slug for FILE (title-based, overridden by `#+HUGO_SLUG:`),
or nil if FILE is unpublished or has no parseable title.
See `a3madkour-pub/note-metadata` for snapshot/caching behavior."
  (plist-get (a3madkour-pub/note-metadata file) :slug))
```

- [ ] **Step 5: Refactor `note-url`**

```elisp
(defun a3madkour-pub/note-url (file)
  "Return `\"/<section>/<slug>/\"` for FILE, or nil if unpublished.
See `a3madkour-pub/note-metadata` for snapshot/caching behavior."
  (when-let* ((md (a3madkour-pub/note-metadata file))
              (section (plist-get md :section))
              (slug (plist-get md :slug)))
    (format "/%s/%s/" section slug)))
```

- [ ] **Step 6: Run, all tests still green**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 53 tests, 53 results as expected, 0 unexpected` (no new tests; existing ones unaffected).

If any test fails, the refactor broke something — most likely either the cache is returning stale data (because the test doesn't call `--reset-metadata-cache` and a prior test populated the cache), or an accessor relied on the dropped guard. Inspect the failing test's setup; if needed, add `(a3madkour-pub--reset-metadata-cache)` to its setup form. (A.1.a's existing tests SHOULD use unique temp filenames per test, so cache collisions across tests are unlikely.)

---

### Task 7: Create `a3madkour-publish-id.el` skeleton + test file

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id-test.el`

- [ ] **Step 1: Write the id library shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id.el`

Content:

```elisp
;;; a3madkour-publish-id.el --- org-roam ID → file lookup -*- lexical-binding: t; -*-

;;; Commentary:

;; Isolates the `org-roam' dep used to resolve `[[id:UUID]]` links to
;; concrete file paths.  All publish-side ID dispatching goes through
;; `a3madkour-pub--id-to-file` defined here.

;;; Code:

(require 'org-roam)

(provide 'a3madkour-publish-id)

;;; a3madkour-publish-id.el ends here
```

- [ ] **Step 2: Write the id test file shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id-test.el`

Content:

```elisp
;;; a3madkour-publish-id-test.el --- Tests for ID dispatching -*- lexical-binding: t; -*-

;;; Code:

(require 'ert)
(require 'cl-lib)
(require 'a3madkour-publish-id)

(provide 'a3madkour-publish-id-test)

;;; a3madkour-publish-id-test.el ends here
```

- [ ] **Step 3: Verify the runner picks up the new test file + still green**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 53 tests, 53 results as expected, 0 unexpected`.

---

### Task 8: Implement `--id-to-file` via `org-roam-id-find`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-id-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-id-test.el` (before the `provide`):

```elisp
(ert-deftest a3madkour-pub-id-test/id-to-file-resolves-known-uuid ()
  "--id-to-file returns the file path for a UUID known to org-roam."
  (cl-letf (((symbol-function 'org-roam-id-find)
             (lambda (id) (and (equal id "abc") "/tmp/known.org"))))
    (should (equal (a3madkour-pub--id-to-file "abc") "/tmp/known.org"))))

(ert-deftest a3madkour-pub-id-test/id-to-file-returns-nil-for-unknown ()
  "--id-to-file returns nil for an unknown UUID."
  (cl-letf (((symbol-function 'org-roam-id-find)
             (lambda (_id) nil)))
    (should-not (a3madkour-pub--id-to-file "not-a-real-uuid"))))

(ert-deftest a3madkour-pub-id-test/id-to-file-returns-nil-for-non-string ()
  "--id-to-file rejects non-string input gracefully."
  (should-not (a3madkour-pub--id-to-file nil))
  (should-not (a3madkour-pub--id-to-file 42)))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failing tests with `void function: a3madkour-pub--id-to-file`.

- [ ] **Step 3: Implement `--id-to-file`**

Append to `a3madkour-publish-id.el` (before `(provide ...)`):

```elisp
(defun a3madkour-pub--id-to-file (id)
  "Return the absolute file path containing org-roam node ID, or nil.

ID must be a string (a UUID).  Non-string input returns nil without error.

Wraps `org-roam-id-find', which performs a SQLite lookup against the
org-roam DB.  The DB is snapshotted at publish start (see
`a3madkour-pub/begin-publish'); IDs created mid-run are NOT visible
until the next snapshot."
  (when (stringp id)
    (org-roam-id-find id)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 56 tests, 56 results as expected, 0 unexpected`.

---

### Task 9: Extend 4 public accessors to accept `file-or-id`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-test.el`:

```elisp
;; -- file-or-id dispatch --

(ert-deftest a3madkour-pub-test/published-p-accepts-uuid ()
  "published-p resolves a UUID via --id-to-file, then dispatches to file path."
  (let ((file (make-temp-file "a3pub-uuid-" nil ".org"
                              "#+title: UUID note
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
")))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                   (lambda (id) (and (equal id "uuid-abc") file))))
          (a3madkour-pub--reset-metadata-cache)
          (should (equal (a3madkour-pub/published-p "uuid-abc") 'live)))
      (delete-file file))))

(ert-deftest a3madkour-pub-test/note-url-accepts-uuid ()
  "note-url resolves a UUID and returns the published URL."
  (let ((file (make-temp-file "a3pub-uuid-" nil ".org"
                              "#+title: UUID note
#+HUGO_PUBLISH: t
#+HUGO_SECTION: essays
")))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                   (lambda (id) (and (equal id "uuid-xyz") file))))
          (a3madkour-pub--reset-metadata-cache)
          (should (equal (a3madkour-pub/note-url "uuid-xyz")
                         "/essays/uuid-note/")))
      (delete-file file))))

(ert-deftest a3madkour-pub-test/note-section-accepts-uuid ()
  (let ((file (make-temp-file "a3pub-uuid-" nil ".org"
                              "#+title: U
#+HUGO_PUBLISH: t
#+HUGO_SECTION: works/games
")))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                   (lambda (id) (and (equal id "uuid-game") file))))
          (a3madkour-pub--reset-metadata-cache)
          (should (equal (a3madkour-pub/note-section "uuid-game") "works/games")))
      (delete-file file))))

(ert-deftest a3madkour-pub-test/note-slug-accepts-uuid ()
  (let ((file (make-temp-file "a3pub-uuid-" nil ".org"
                              "#+title: Sluggable Title
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
")))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                   (lambda (id) (and (equal id "uuid-slug") file))))
          (a3madkour-pub--reset-metadata-cache)
          (should (equal (a3madkour-pub/note-slug "uuid-slug") "sluggable-title")))
      (delete-file file))))

(ert-deftest a3madkour-pub-test/accessors-return-nil-for-unknown-uuid ()
  "Accessors return nil cleanly when --id-to-file returns nil."
  (cl-letf (((symbol-function 'a3madkour-pub--id-to-file) (lambda (_) nil)))
    (a3madkour-pub--reset-metadata-cache)
    (should-not (a3madkour-pub/published-p  "unknown-uuid"))
    (should-not (a3madkour-pub/note-url     "unknown-uuid"))
    (should-not (a3madkour-pub/note-section "unknown-uuid"))
    (should-not (a3madkour-pub/note-slug    "unknown-uuid"))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 5 failures — either `void function: a3madkour-pub--id-to-file` (if `-id.el` isn't required from `-publish.el`) or assertion failures because UUIDs are passed straight through to `note-metadata` which tries to parse them as file paths.

- [ ] **Step 3: Wire `-id.el` into the entry point**

Near the top of `a3madkour-publish.el`, add (or extend) the requires block:

```elisp
(require 'a3madkour-publish-id)
```

- [ ] **Step 4: Add `file-or-id` dispatch helper**

In `a3madkour-publish.el`, just before `note-metadata`, add:

```elisp
(defun a3madkour-pub--resolve-file-or-id (file-or-id)
  "If FILE-OR-ID is a UUID (looks like an org-roam ID), resolve via
`a3madkour-pub--id-to-file' and return the file path.  Otherwise return
FILE-OR-ID unchanged.  The heuristic is: input is a UUID if it matches
the RFC 4122 pattern; everything else is treated as a file path."
  (cond
   ((null file-or-id) nil)
   ((and (stringp file-or-id)
         (string-match-p
          "\\`[[:xdigit:]]\\{8\\}-[[:xdigit:]]\\{4\\}-[[:xdigit:]]\\{4\\}-[[:xdigit:]]\\{4\\}-[[:xdigit:]]\\{12\\}\\'"
          file-or-id))
    (a3madkour-pub--id-to-file file-or-id))
   (t file-or-id)))
```

- [ ] **Step 5: Update the 4 accessors to dispatch**

For each of `published-p`, `note-section`, `note-slug`, `note-url`, change the body to first dispatch:

```elisp
(defun a3madkour-pub/published-p (file-or-id)
  "Return `'live`, `'draft`, or nil for FILE-OR-ID.
FILE-OR-ID may be either a file path (string) or a UUID string;
UUIDs are resolved via `a3madkour-pub--id-to-file'."
  (when-let* ((file (a3madkour-pub--resolve-file-or-id file-or-id))
              (md (a3madkour-pub/note-metadata file)))
    (plist-get md :state)))

(defun a3madkour-pub/note-section (file-or-id)
  "Return the section for FILE-OR-ID (file path OR UUID)."
  (when-let ((file (a3madkour-pub--resolve-file-or-id file-or-id)))
    (plist-get (a3madkour-pub/note-metadata file) :section)))

(defun a3madkour-pub/note-slug (file-or-id)
  "Return the slug for FILE-OR-ID (file path OR UUID)."
  (when-let ((file (a3madkour-pub--resolve-file-or-id file-or-id)))
    (plist-get (a3madkour-pub/note-metadata file) :slug)))

(defun a3madkour-pub/note-url (file-or-id)
  "Return `\"/<section>/<slug>/\"` for FILE-OR-ID (file path OR UUID)."
  (when-let* ((file (a3madkour-pub--resolve-file-or-id file-or-id))
              (md (a3madkour-pub/note-metadata file))
              (section (plist-get md :section))
              (slug (plist-get md :slug)))
    (format "/%s/%s/" section slug)))
```

- [ ] **Step 6: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 61 tests, 61 results as expected, 0 unexpected`.

---

### Task 10: `record-publish` keyword arg + `--diff-reason` upgrade

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-history-test.el` (before `(provide ...)`):

```elisp
;; -- :had-slug-override-p resolution --

(ert-deftest a3madkour-pub-history-test/record-publish-slug-override-reason ()
  "record-publish with :had-slug-override-p t emits reason=slug_override
when the URL changes."
  (let ((data-dir (make-temp-file "a3pub-history-" t)))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir data-dir))
          (a3madkour-pub-history/record-publish "id-1" "/garden/v1/" 'live)
          (a3madkour-pub-history/record-publish
           "id-1" "/garden/v2/" 'live :had-slug-override-p t)
          (let* ((entry (car (a3madkour-pub-history/read-manifest)))
                 (history (alist-get 'history entry))
                 (last-evt (aref history (1- (length history)))))
            (should (equal (alist-get 'reason last-evt) "slug_override"))))
      (delete-directory data-dir t))))

(ert-deftest a3madkour-pub-history-test/record-publish-title-change-reason ()
  "record-publish without :had-slug-override-p (or :had-slug-override-p nil)
emits reason=title_change when the URL changes."
  (let ((data-dir (make-temp-file "a3pub-history-" t)))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir data-dir))
          (a3madkour-pub-history/record-publish "id-2" "/garden/old/" 'live)
          (a3madkour-pub-history/record-publish "id-2" "/garden/new/" 'live)
          (let* ((entry (car (a3madkour-pub-history/read-manifest)))
                 (history (alist-get 'history entry))
                 (last-evt (aref history (1- (length history)))))
            (should (equal (alist-get 'reason last-evt) "title_change"))))
      (delete-directory data-dir t))))

(ert-deftest a3madkour-pub-history-test/record-publish-section-change-wins ()
  "Section change takes precedence over slug_override flag in --diff-reason."
  (let ((data-dir (make-temp-file "a3pub-history-" t)))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir data-dir))
          (a3madkour-pub-history/record-publish "id-3" "/garden/foo/" 'live)
          (a3madkour-pub-history/record-publish
           "id-3" "/essays/foo/" 'live :had-slug-override-p t)
          (let* ((entry (car (a3madkour-pub-history/read-manifest)))
                 (history (alist-get 'history entry))
                 (last-evt (aref history (1- (length history)))))
            (should (equal (alist-get 'reason last-evt) "section_change"))))
      (delete-directory data-dir t))))
```

(Note: the precise assertion path through the parsed yaml depends on yaml.el's keyword-args choices — see how A.1.a's `record-publish` tests assert the same structure and mirror it. If A.1.a's existing tests use a different shape — e.g., `(alist-get :reason ...)` instead of `(alist-get 'reason ...)` — adjust to match.)

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures — most likely "Wrong number of arguments" on `record-publish` (because the existing signature doesn't accept the keyword) or assertion failures on `reason`.

- [ ] **Step 3: Update `record-publish` signature**

Open `a3madkour-publish-history.el`. Locate the existing `record-publish` defun. Change its signature to accept `&key had-slug-override-p`:

```elisp
(cl-defun a3madkour-pub-history/record-publish (id new-url state &key had-slug-override-p)
  "Record a publish event for ID with NEW-URL and STATE in `data/url-history.yaml`.

STATE is one of `'live`, `'draft`, `'removed`.

When HAD-SLUG-OVERRIDE-P is non-nil and the URL changed for a reason
other than section change, `--diff-reason` emits `slug_override`
instead of `title_change`. The caller (B's publisher) is responsible
for setting this based on whether the source file has `#+HUGO_SLUG:`.

See parent spec §8 for the URL-history schema."
  ; <body — see Step 4>
  )
```

If `record-publish` was a `defun` (positional args), it needs to become `cl-defun` to support `&key`. Ensure `(require 'cl-lib)` is at the top of the file.

- [ ] **Step 4: Thread `had-slug-override-p` into `--diff-reason`**

Locate the existing `--diff-reason` helper (or wherever the reason is computed in `record-publish`). Pass `had-slug-override-p` in, and update the helper to emit `slug_override` when the flag is set AND the change isn't a section change:

```elisp
(defun a3madkour-pub-history--diff-reason (old-url new-url &optional had-slug-override-p)
  "Classify the kind of URL change for the URL-history `reason` field.

Returns one of `\"title_change\"`, `\"slug_override\"`, `\"section_change\"`,
`\"removed\"`."
  (cond
   ((null new-url) "removed")
   ((null old-url) nil)  ; new note — no `reason` for the first publish
   ((not (equal (a3madkour-pub-history--url-section old-url)
                (a3madkour-pub-history--url-section new-url)))
    "section_change")
   (had-slug-override-p "slug_override")
   (t "title_change")))
```

(`--url-section` is whatever helper A.1.a uses to extract the section segment from a URL; reuse the same one. If A.1.a inlined section parsing in `--diff-reason`, factor it out here.)

Inside `record-publish`, where `--diff-reason` is called, pass the flag through:

```elisp
(let ((reason (a3madkour-pub-history--diff-reason old-url new-url had-slug-override-p)))
  ; ...
  )
```

- [ ] **Step 5: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 64 tests, 64 results as expected, 0 unexpected`.

---

### Task 11: Create `a3madkour-publish-rewrite.el` skeleton + defcustom

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write the rewriter library shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`

Content:

```elisp
;;; a3madkour-publish-rewrite.el --- Link rewriting for org-mode publish -*- lexical-binding: t; -*-

;;; Commentary:

;; Implements parent-spec §6 link rewriting contract for A.1.b.
;; - `a3madkour-pub/rewrite-link' — per-link-type dispatcher.
;; - `a3madkour-pub--heading-anchor' — Goldmark `github` autolink-headings slug.
;; - `a3madkour-pub-typed-link-types' — defcustom listing recognized custom
;;   typed-link types (e.g., `supports`, `contradicts`).
;;
;; Asset-shaped links return `:pending-asset` in A.1.b; A.1.c upgrades
;; to real handling.

;;; Code:

(require 'cl-lib)
(require 'a3madkour-publish)
(require 'a3madkour-publish-id)

(defgroup a3madkour-pub-rewrite nil
  "Link rewriter for the a3madkour-publish library."
  :group 'a3madkour-pub)

(defcustom a3madkour-pub-typed-link-types
  '("supports" "contradicts" "extends" "example-of" "causes")
  "List of recognized custom typed-link types.

For any org link of the form `[[<type>:UUID][text]]` where `<type>` is
a member of this list, `a3madkour-pub/rewrite-link' treats it as an
id-link AND emits `class=\"link-<type>\"` on the rendered anchor.
Class is emitted regardless of target state (live/draft/inert) so CSS
styling is consistent for all variants.

See parent spec §6 (custom typed-link CSS class emission)."
  :type '(repeat string)
  :group 'a3madkour-pub-rewrite)

(provide 'a3madkour-publish-rewrite)

;;; a3madkour-publish-rewrite.el ends here
```

- [ ] **Step 2: Write the rewriter test file shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

Content:

```elisp
;;; a3madkour-publish-rewrite-test.el --- Tests for link rewriting -*- lexical-binding: t; -*-

;;; Code:

(require 'ert)
(require 'cl-lib)
(require 'a3madkour-publish-rewrite)

(provide 'a3madkour-publish-rewrite-test)

;;; a3madkour-publish-rewrite-test.el ends here
```

- [ ] **Step 3: Verify runner picks up new test file + still green**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 64 tests, 64 results as expected, 0 unexpected`.

---

### Task 12: Heading-anchor slugifier (Goldmark `github` algorithm)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

Reference: Hugo uses its **own** `github`-style ID generator at `gohugoio/hugo` `markup/goldmark/autoid.go` (function `sanitizeAnchorNameWithHook`), NOT Goldmark's bare `parser.IDs.Generate` — the two algorithms differ. Hugo registers its generator via Goldmark's `AddOption(html.WithIDRenderer(...))` hook. Hugo's algorithm:

1. **Trim leading/trailing whitespace.**
2. For each rune in the trimmed text:
   - Keep if `unicode.IsLetter(r)` OR `unicode.IsDigit(r)` OR `r == '_'`. Lowercase and append.
   - Keep `' '` and `'-'` — both append as `'-'`.
   - Drop everything else.
3. **If the resulting buffer is empty, fall back to `"heading"`** (only fires for Heading kind; not the parent-spec's concern).

(Consecutive spaces produce consecutive hyphens — no collapse. `unicode.IsDigit` is **strictly `Nd`** — `Nl` (Roman numerals like `Ⅳ`) and `No` (`½`, `²`) are dropped. Unicode letters preserved — `café` stays `café`.)

**In-flight correction (2026-05-23 session):** The original plan text here cited Goldmark's `auto_heading_id` and omitted the trim + heading-fallback + Nd-only details. Task 12's code reviewer caught the divergence against real Hugo (the algorithm above replaces the buggy original). Tests + function updated; 4 additional tests added (`anchor-punctuation-only-fallback`, `anchor-hyphens-preserved`, `anchor-drops-letter-numbers`, `anchor-uppercase-underscore`). Test-count target adjusted: 75 → **79** at end of Task 12.

- [ ] **Step 1: Write the failing tests (gotcha suite)**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- heading-anchor (Goldmark `github` autolink-headings) --

(ert-deftest a3madkour-pub-rewrite-test/anchor-basic-ascii ()
  (should (equal (a3madkour-pub--heading-anchor "Hello World") "hello-world")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-lowercase ()
  (should (equal (a3madkour-pub--heading-anchor "FOO BAR") "foo-bar")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-preserves-accents ()
  "Goldmark preserves unicode letters — `café` stays `café`, not folded."
  (should (equal (a3madkour-pub--heading-anchor "Café") "café")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-preserves-cjk ()
  (should (equal (a3madkour-pub--heading-anchor "日本語タイトル") "日本語タイトル")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-strips-punctuation ()
  (should (equal (a3madkour-pub--heading-anchor "Hello, World!") "hello-world")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-strips-parens ()
  (should (equal (a3madkour-pub--heading-anchor "Foo (Bar)") "foo-bar")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-keeps-hyphen-and-underscore ()
  (should (equal (a3madkour-pub--heading-anchor "foo-bar_baz") "foo-bar_baz")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-keeps-digits ()
  (should (equal (a3madkour-pub--heading-anchor "Section 2.3") "section-23")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-contiguous-spaces ()
  "Multiple spaces become multiple hyphens (Goldmark does not collapse)."
  (should (equal (a3madkour-pub--heading-anchor "a  b") "a--b")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-leading-trailing-spaces ()
  "Goldmark does not trim — leading/trailing spaces become hyphens."
  (should (equal (a3madkour-pub--heading-anchor " hi ") "-hi-")))

(ert-deftest a3madkour-pub-rewrite-test/anchor-empty ()
  (should (equal (a3madkour-pub--heading-anchor "") "")))
```

(If any of these edge-case expectations turn out to be wrong on real Hugo + Goldmark — the integration spot-check in Task 19 catches this — update the function AND the test to match Goldmark's actual output. Goldmark's source-of-truth: `github.com/yuin/goldmark/extension/auto_heading_id.go`.)

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 11 failures with `void function: a3madkour-pub--heading-anchor`.

- [ ] **Step 3: Implement the slugifier**

Append to `a3madkour-publish-rewrite.el` (before `(provide ...)`):

```elisp
(defun a3madkour-pub--heading-anchor (heading-text)
  "Compute the Hugo Goldmark `github`-style heading anchor for HEADING-TEXT.

Algorithm (from goldmark/extension/auto_heading_id.go):
  1. Keep only chars where `(or (string-match-p \"[[:alnum:]]\" s)
                                  (string-match-p \"[- _]\" s))`.
  2. Lowercase.
  3. Replace each ` ` with `-`.

Unicode letters/numbers are preserved (`café` stays `café`, not folded).
Consecutive spaces produce consecutive hyphens (no collapse).
Leading/trailing whitespace becomes hyphens (no trim)."
  (let* ((kept (apply #'string
                      (cl-loop for c across heading-text
                               when (or (= c ?\s) (= c ?-) (= c ?_)
                                        ;; alnum here means letters + numbers
                                        ;; using elisp's syntax-class check.
                                        (string-match-p
                                         "[[:alnum:]]"
                                         (char-to-string c)))
                               collect c)))
         (lowered (downcase kept))
         (hyphenated (replace-regexp-in-string " " "-" lowered)))
    hyphenated))
```

**Caveat:** elisp's `[[:alnum:]]` matches per the buffer's `char-syntax` table, which IS unicode-aware on modern Emacs (≥27). If a test on accented or CJK characters surprises you, debug with `(char-to-string ?\é)` and `(string-match-p "[[:alnum:]]" "é")` interactively — the docs claim unicode-awareness, but verify on your install.

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 75 tests, 75 results as expected, 0 unexpected`.

If any anchor test fails because elisp's `[[:alnum:]]` doesn't classify the way Goldmark does, switch to an explicit unicode-category check: `(memq (get-char-code-property c 'general-category) '(Lu Ll Lt Lm Lo Nd Nl No))` — letters + numbers.

---

### Task 13: Link rewriter — external pass-through

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- rewrite-link: external URL pass-through --

(ert-deftest a3madkour-pub-rewrite-test/external-https ()
  (let ((result (a3madkour-pub/rewrite-link
                 "[[https://example.com][Example]]" "src-id")))
    (should (equal (plist-get result :html)
                   "<a href=\"https://example.com\">Example</a>"))
    (should-not (plist-get result :warnings))))

(ert-deftest a3madkour-pub-rewrite-test/external-http ()
  (let ((result (a3madkour-pub/rewrite-link
                 "[[http://example.com][text]]" "src-id")))
    (should (equal (plist-get result :html)
                   "<a href=\"http://example.com\">text</a>"))))

(ert-deftest a3madkour-pub-rewrite-test/external-mailto ()
  (let ((result (a3madkour-pub/rewrite-link
                 "[[mailto:foo@example.com][Email me]]" "src-id")))
    (should (equal (plist-get result :html)
                   "<a href=\"mailto:foo@example.com\">Email me</a>"))))

(ert-deftest a3madkour-pub-rewrite-test/external-tel ()
  (let ((result (a3madkour-pub/rewrite-link
                 "[[tel:+15551234567][Call]]" "src-id")))
    (should (equal (plist-get result :html)
                   "<a href=\"tel:+15551234567\">Call</a>"))))

(ert-deftest a3madkour-pub-rewrite-test/external-other-scheme ()
  "Unrecognized URL schemes pass through unchanged."
  (let ((result (a3madkour-pub/rewrite-link
                 "[[ftp://files.example.com][download]]" "src-id")))
    (should (equal (plist-get result :html)
                   "<a href=\"ftp://files.example.com\">download</a>"))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 5 failures — `void function: a3madkour-pub/rewrite-link`.

- [ ] **Step 3: Implement `rewrite-link` skeleton + external branch**

Append to `a3madkour-publish-rewrite.el` (before `(provide ...)`):

```elisp
(defun a3madkour-pub--parse-org-link (org-link)
  "Parse an org link form `[[<path>][<text>]]` (or `[[<path>]]`) into a plist.

Returns (:path PATH :text TEXT-OR-PATH).  TEXT-OR-PATH is the display
text if present, else PATH (org's default rendering)."
  (cond
   ;; [[path][text]]
   ((string-match "\\`\\[\\[\\(.*?\\)\\]\\[\\(.*?\\)\\]\\]\\'" org-link)
    (list :path (match-string 1 org-link)
          :text (match-string 2 org-link)))
   ;; [[path]]
   ((string-match "\\`\\[\\[\\(.*?\\)\\]\\]\\'" org-link)
    (let ((path (match-string 1 org-link)))
      (list :path path :text path)))
   (t (error "Unparseable org link: %S" org-link))))

(defun a3madkour-pub--link-scheme (path)
  "Return the URL scheme of PATH as a string (e.g., \"https\"), or nil."
  (when (string-match "\\`\\([a-z][a-z0-9+.-]*\\):" path)
    (match-string 1 path)))

(defun a3madkour-pub--external-scheme-p (scheme)
  "Return non-nil if SCHEME is an external URL scheme (not id/file/custom-type)."
  (and scheme
       (not (equal scheme "id"))
       (not (equal scheme "file"))
       (not (member scheme a3madkour-pub-typed-link-types))))

(defun a3madkour-pub/rewrite-link (org-link source-note-id)
  "Rewrite ORG-LINK to web HTML, inert text, or asset placeholder.

ORG-LINK is the raw org bracket form, e.g., `\"[[id:UUID][text]]\"`.
SOURCE-NOTE-ID is the id of the org file containing ORG-LINK
(used to determine source state for the live→draft WARN).

Returns one of:
  (:html HTML-STRING :warnings (WARN ...))    ; rendered anchor
  (:inert TEXT-STRING :warnings (WARN ...))   ; link erased; text preserved
  (:pending-asset ORIG-LINK :warnings (...))  ; A.1.b stub; A.1.c upgrades

See parent spec §6 for the per-link-type rules."
  (let* ((parsed (a3madkour-pub--parse-org-link org-link))
         (path (plist-get parsed :path))
         (text (plist-get parsed :text))
         (scheme (a3madkour-pub--link-scheme path)))
    (cond
     ;; External URL scheme — pass through unchanged.
     ((a3madkour-pub--external-scheme-p scheme)
      (list :html (format "<a href=\"%s\">%s</a>" path text)
            :warnings nil))
     ;; Other branches added in Tasks 14–18.
     (t
      (error "rewrite-link: scheme %S not yet handled (this branch lands in a later task)"
             scheme)))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 80 tests, 80 results as expected, 0 unexpected`.

---

### Task 14: Link rewriter — id-links (live/draft/private/unknown)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- rewrite-link: id-links --

(defmacro a3madkour-pub-rewrite-test--with-stubbed (state-alist &rest body)
  "Run BODY with `note-metadata` stubbed to return entries from STATE-ALIST.
STATE-ALIST maps file-or-id strings to plist values."
  (declare (indent 1))
  `(cl-letf (((symbol-function 'a3madkour-pub/note-metadata)
              (lambda (file-or-id)
                (cdr (assoc file-or-id ',state-alist))))
             ((symbol-function 'a3madkour-pub--resolve-file-or-id)
              (lambda (foi) foi))  ; identity — let stub handle dispatch
             ((symbol-function 'a3madkour-pub/published-p)
              (lambda (foi)
                (plist-get (cdr (assoc foi ',state-alist)) :state)))
             ((symbol-function 'a3madkour-pub/note-url)
              (lambda (foi)
                (let ((md (cdr (assoc foi ',state-alist))))
                  (when md
                    (format "/%s/%s/"
                            (plist-get md :section)
                            (plist-get md :slug)))))))
     ,@body))

(ert-deftest a3madkour-pub-rewrite-test/id-link-live ()
  "Live target → <a href> with section/slug; no warnings."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("target-id" :state live :section "garden" :slug "foo")
    ("source-id" :state live :section "garden" :slug "bar"))
   (let ((result (a3madkour-pub/rewrite-link
                  "[[id:target-id][Hello]]" "source-id")))
     (should (equal (plist-get result :html)
                    "<a href=\"/garden/foo/\">Hello</a>"))
     (should-not (plist-get result :warnings)))))

(ert-deftest a3madkour-pub-rewrite-test/id-link-draft-from-live ()
  "Draft target, source is live → :html with WARN."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("target-id" :state draft :section "essays" :slug "draftpost")
    ("source-id" :state live  :section "garden" :slug "live"))
   (let ((result (a3madkour-pub/rewrite-link
                  "[[id:target-id][text]]" "source-id")))
     (should (equal (plist-get result :html)
                    "<a href=\"/essays/draftpost/\">text</a>"))
     (should (= 1 (length (plist-get result :warnings))))
     (should (string-match-p "draft" (car (plist-get result :warnings)))))))

(ert-deftest a3madkour-pub-rewrite-test/id-link-draft-from-draft ()
  "Draft target, source is also draft → :html, NO warning (both unship together)."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("target-id" :state draft :section "essays" :slug "tgt")
    ("source-id" :state draft :section "garden" :slug "src"))
   (let ((result (a3madkour-pub/rewrite-link
                  "[[id:target-id][text]]" "source-id")))
     (should (equal (plist-get result :html)
                    "<a href=\"/essays/tgt/\">text</a>"))
     (should-not (plist-get result :warnings)))))

(ert-deftest a3madkour-pub-rewrite-test/id-link-private ()
  "Target unpublished (private) → :inert with WARN."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("source-id" :state live :section "garden" :slug "src"))
   ;; No entry for "target-id" → published-p returns nil → private
   (let ((result (a3madkour-pub/rewrite-link
                  "[[id:target-id][Some text]]" "source-id")))
     (should (equal (plist-get result :inert) "Some text"))
     (should (= 1 (length (plist-get result :warnings))))
     (should (string-match-p "private\\|unpublished\\|unknown"
                             (car (plist-get result :warnings)))))))

(ert-deftest a3madkour-pub-rewrite-test/id-link-without-display-text ()
  "Link [[id:UUID]] (no text) uses the resolved URL as text (org's default behavior)."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("target-id" :state live :section "garden" :slug "foo")
    ("source-id" :state live :section "garden" :slug "src"))
   ;; When the parsed link has no [text], path doubles as text — but here
   ;; the path is `id:target-id`, which is meaningless to display. Pick a
   ;; sensible default: use the resolved URL as text.
   (let ((result (a3madkour-pub/rewrite-link "[[id:target-id]]" "source-id")))
     (should (equal (plist-get result :html)
                    "<a href=\"/garden/foo/\">/garden/foo/</a>")))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 5 failures — most likely "rewrite-link: scheme \"id\" not yet handled" errors.

- [ ] **Step 3: Implement the id-link branch**

In `a3madkour-publish-rewrite.el`, replace the `(error ...)` fallback in `rewrite-link` with branching on scheme. The id-link branch needs the target's metadata + source's state:

```elisp
(defun a3madkour-pub--rewrite-id-link (path text source-note-id)
  "Rewrite a `[[id:UUID...]]' link.  PATH is the part after `id:`, possibly
with `::*Section` heading suffix.  TEXT is the display text.
SOURCE-NOTE-ID determines whether to emit the live→draft warning."
  (let* ((parts (split-string path "::" t))     ; \"UUID\" or \"UUID\" \"*Heading\"
         (target-id (car parts))
         (heading-suffix (cadr parts))           ; nil or \"*Heading\"
         (target-state (a3madkour-pub/published-p target-id))
         (target-url (a3madkour-pub/note-url target-id))
         (source-state (a3madkour-pub/published-p source-note-id))
         (display (if (string-empty-p text) target-url text)))
    (cond
     ;; Unknown UUID or private → :inert + WARN
     ((null target-state)
      (list :inert (or display "")
            :warnings (list (format "link target id:%s is private or unknown" target-id))))
     ;; Live OR draft target → :html
     (t
      (let* ((href (if heading-suffix
                       (a3madkour-pub--id-link-href-with-anchor
                        target-url heading-suffix target-id)
                     target-url))
             (warnings
              (cond
               ((and (eq target-state 'draft) (eq source-state 'live))
                (list (format "live note links to draft target id:%s" target-id)))
               (t nil))))
        (list :html (format "<a href=\"%s\">%s</a>" href display)
              :warnings warnings))))))

(defun a3madkour-pub--id-link-href-with-anchor (target-url heading-suffix _target-id)
  "Return TARGET-URL with `#<goldmark-slug>` appended for HEADING-SUFFIX.
HEADING-SUFFIX is the org `*Heading Text` form (with leading `*`).
A.1.b: heading existence is NOT verified (Task 15 adds that nuance).
This function only computes the href; verification + WARN-on-missing
land in Task 15."
  (let* ((heading-text (string-trim (substring heading-suffix 1)))
         (anchor (a3madkour-pub--heading-anchor heading-text)))
    (format "%s#%s" target-url anchor)))
```

Then in the `cond` inside `rewrite-link`, add the id branch before the external branch:

```elisp
(cond
 ;; id-link
 ((equal scheme "id")
  (a3madkour-pub--rewrite-id-link
   (substring path 3)  ; drop "id:"
   text source-note-id))
 ;; External URL — pass through
 ((a3madkour-pub--external-scheme-p scheme)
  (list :html (format "<a href=\"%s\">%s</a>" path text)
        :warnings nil))
 (t
  (error "rewrite-link: scheme %S not yet handled" scheme)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 85 tests, 85 results as expected, 0 unexpected`.

---

### Task 15: Link rewriter — heading anchors (existence check + WARN)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

Task 14 already emits `#<anchor>` for `[[id:UUID::*Section]]`. This task adds the existence check: if the heading doesn't exist in the target file, emit the link anyway but with a WARN.

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- rewrite-link: heading anchors --

(ert-deftest a3madkour-pub-rewrite-test/anchor-link-live-heading-exists ()
  "Live target + heading exists in target file → :html with anchor; no WARN."
  (let ((tgt-file (make-temp-file "a3pub-tgt-" nil ".org"
                                  "#+title: Target
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
* Introduction
* Section Two
")))
    (unwind-protect
        (a3madkour-pub-rewrite-test--with-stubbed
         (("target-id" :state live :section "garden" :slug "target" :file ,tgt-file)
          ("source-id" :state live :section "garden" :slug "src"))
         (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                    (lambda (id) (and (equal id "target-id") tgt-file))))
           (let ((result (a3madkour-pub/rewrite-link
                          "[[id:target-id::*Section Two][Read more]]" "source-id")))
             (should (equal (plist-get result :html)
                            "<a href=\"/garden/target/#section-two\">Read more</a>"))
             (should-not (plist-get result :warnings)))))
      (delete-file tgt-file))))

(ert-deftest a3madkour-pub-rewrite-test/anchor-link-heading-missing ()
  "Live target + heading missing → :html with anchor + WARN."
  (let ((tgt-file (make-temp-file "a3pub-tgt-" nil ".org"
                                  "#+title: Target
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
* Only Section
")))
    (unwind-protect
        (a3madkour-pub-rewrite-test--with-stubbed
         (("target-id" :state live :section "garden" :slug "target" :file ,tgt-file)
          ("source-id" :state live :section "garden" :slug "src"))
         (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                    (lambda (id) (and (equal id "target-id") tgt-file))))
           (let ((result (a3madkour-pub/rewrite-link
                          "[[id:target-id::*Missing Heading][text]]" "source-id")))
             (should (equal (plist-get result :html)
                            "<a href=\"/garden/target/#missing-heading\">text</a>"))
             (should (= 1 (length (plist-get result :warnings))))
             (should (string-match-p "heading.*not found"
                                     (car (plist-get result :warnings)))))))
      (delete-file tgt-file))))

(ert-deftest a3madkour-pub-rewrite-test/anchor-link-private-target ()
  "Private target with heading suffix → :inert + WARN (anchor lost)."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("source-id" :state live :section "garden" :slug "src"))
   (let ((result (a3madkour-pub/rewrite-link
                  "[[id:no-such-target::*Section][text]]" "source-id")))
     (should (equal (plist-get result :inert) "text"))
     (should (= 1 (length (plist-get result :warnings)))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 1 failure — `anchor-link-heading-missing` doesn't emit the WARN yet (the other two should pass because Task 14 already emits the anchor and the private case was handled).

- [ ] **Step 3: Implement heading-existence check**

Add to `a3madkour-publish-rewrite.el`:

```elisp
(defun a3madkour-pub--target-has-heading-p (target-file heading-text)
  "Return non-nil iff TARGET-FILE contains an org heading matching HEADING-TEXT.
Matched case-sensitively against trimmed heading text (the org `* Title` form).
Returns nil if TARGET-FILE doesn't exist or can't be read."
  (when (and target-file (file-exists-p target-file))
    (with-temp-buffer
      (insert-file-contents target-file)
      (goto-char (point-min))
      (let ((heading-re (concat "^\\*+ +"
                                (regexp-quote (string-trim heading-text))
                                "[ \t]*$")))
        (re-search-forward heading-re nil t)))))
```

Then upgrade `--rewrite-id-link` to invoke the check when a heading-suffix is present:

```elisp
(defun a3madkour-pub--rewrite-id-link (path text source-note-id)
  "<docstring unchanged>"
  (let* ((parts (split-string path "::" t))
         (target-id (car parts))
         (heading-suffix (cadr parts))
         (target-state (a3madkour-pub/published-p target-id))
         (target-url (a3madkour-pub/note-url target-id))
         (target-file (and target-id (a3madkour-pub--id-to-file target-id)))
         (source-state (a3madkour-pub/published-p source-note-id))
         (display (if (string-empty-p text) target-url text)))
    (cond
     ((null target-state)
      (list :inert (or display "")
            :warnings (list (format "link target id:%s is private or unknown" target-id))))
     (t
      (let* ((heading-text (and heading-suffix
                                (string-trim (substring heading-suffix 1))))
             (href (if heading-suffix
                       (format "%s#%s"
                               target-url
                               (a3madkour-pub--heading-anchor heading-text))
                     target-url))
             (warnings
              (delq nil
                    (list
                     ;; live→draft warn
                     (when (and (eq target-state 'draft) (eq source-state 'live))
                       (format "live note links to draft target id:%s" target-id))
                     ;; heading-missing warn
                     (when (and heading-suffix target-file
                                (not (a3madkour-pub--target-has-heading-p
                                      target-file heading-text)))
                       (format "heading %S not found in target id:%s"
                               heading-text target-id)))))))
        (list :html (format "<a href=\"%s\">%s</a>" href display)
              :warnings warnings))))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 88 tests, 88 results as expected, 0 unexpected`.

---

### Task 16: Link rewriter — file-link auto-convert

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

`[[file:foo.org]]` — if the target file has an `:ID:` property at top level (or in any subtree's PROPERTIES drawer), resolve to id-link semantics. If not, emit inert + WARN.

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- rewrite-link: file-link auto-convert --

(ert-deftest a3madkour-pub-rewrite-test/file-link-with-id ()
  "file-link to a target with :ID: → resolves to id-link semantics."
  (let ((tgt (make-temp-file "a3pub-file-tgt-" nil ".org"
                             "#+title: Target
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
:PROPERTIES:
:ID: deadbeef-dead-beef-dead-beefdeadbeef
:END:
")))
    (unwind-protect
        (a3madkour-pub-rewrite-test--with-stubbed
         (("deadbeef-dead-beef-dead-beefdeadbeef"
           :state live :section "garden" :slug "target" :file ,tgt)
          ("source-id" :state live :section "garden" :slug "src"))
         (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                    (lambda (id)
                      (and (equal id "deadbeef-dead-beef-dead-beefdeadbeef") tgt)))
                   ((symbol-function 'a3madkour-pub--file-top-level-id)
                    (lambda (f)
                      (and (equal f tgt) "deadbeef-dead-beef-dead-beefdeadbeef"))))
           (let ((result (a3madkour-pub/rewrite-link
                          (format "[[file:%s][text]]" tgt) "source-id")))
             (should (equal (plist-get result :html)
                            "<a href=\"/garden/target/\">text</a>")))))
      (delete-file tgt))))

(ert-deftest a3madkour-pub-rewrite-test/file-link-without-id ()
  "file-link to target lacking :ID: → :inert + WARN."
  (let ((tgt (make-temp-file "a3pub-file-tgt-noid-" nil ".org"
                             "#+title: Plain target\n")))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub--file-top-level-id)
                   (lambda (f) (and (equal f tgt) nil))))
          (let ((result (a3madkour-pub/rewrite-link
                         (format "[[file:%s][text]]" tgt) "source-id")))
            (should (equal (plist-get result :inert) "text"))
            (should (string-match-p ":ID:" (car (plist-get result :warnings))))))
      (delete-file tgt))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 2 failures — `void function: a3madkour-pub--file-top-level-id` or "scheme \"file\" not yet handled".

- [ ] **Step 3: Implement file-link branch + id-extraction helper**

Add to `a3madkour-publish-rewrite.el`:

```elisp
(defun a3madkour-pub--file-top-level-id (file)
  "Return the value of the top-level :ID: property in FILE as a string, or nil.

\"Top level\" here means the file-level property drawer that ox-hugo /
org-roam puts at the very top. If FILE has no such drawer or no :ID:,
return nil. Subtree-level IDs are out of scope for file-link resolution
(authors should link to subtree IDs via `[[id:UUID]]` directly)."
  (when (and file (file-exists-p file))
    (with-temp-buffer
      (insert-file-contents file)
      (goto-char (point-min))
      (when (re-search-forward
             "^:ID: +\\([0-9a-f-]+\\)" nil t)
        (match-string 1)))))

(defun a3madkour-pub--rewrite-file-link (path text source-note-id)
  "Rewrite a `[[file:...]]' link by resolving target's `:ID:` and
recursing into id-link semantics, OR emit :inert + WARN if no :ID:."
  (let* ((target-file (expand-file-name path))
         (target-id (a3madkour-pub--file-top-level-id target-file)))
    (if target-id
        (a3madkour-pub--rewrite-id-link
         target-id text source-note-id)
      (list :inert text
            :warnings (list (format "file-link target %s lacks :ID:; cannot resolve"
                                    target-file))))))
```

Then add the file-link branch to `rewrite-link`'s `cond`, BEFORE the external branch:

```elisp
(cond
 ((equal scheme "id")
  (a3madkour-pub--rewrite-id-link (substring path 3) text source-note-id))
 ((equal scheme "file")
  (a3madkour-pub--rewrite-file-link (substring path 5) text source-note-id))
 ((a3madkour-pub--external-scheme-p scheme)
  (list :html (format "<a href=\"%s\">%s</a>" path text)
        :warnings nil))
 ...)
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 90 tests, 90 results as expected, 0 unexpected`.

---

### Task 17: Link rewriter — custom typed links + CSS class

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- rewrite-link: custom typed links --

(ert-deftest a3madkour-pub-rewrite-test/typed-link-supports-live-target ()
  "[[supports:UUID][text]] → <a class=\"link-supports\" href=\"...\">text</a>"
  (a3madkour-pub-rewrite-test--with-stubbed
   (("tgt" :state live :section "garden" :slug "ev")
    ("source-id" :state live :section "garden" :slug "src"))
   (let ((result (a3madkour-pub/rewrite-link
                  "[[supports:tgt][evidence]]" "source-id")))
     (should (equal (plist-get result :html)
                    "<a class=\"link-supports\" href=\"/garden/ev/\">evidence</a>")))))

(ert-deftest a3madkour-pub-rewrite-test/typed-link-contradicts ()
  (a3madkour-pub-rewrite-test--with-stubbed
   (("tgt" :state live :section "garden" :slug "x")
    ("source-id" :state live :section "garden" :slug "src"))
   (let ((result (a3madkour-pub/rewrite-link
                  "[[contradicts:tgt][counterexample]]" "source-id")))
     (should (equal (plist-get result :html)
                    "<a class=\"link-contradicts\" href=\"/garden/x/\">counterexample</a>")))))

(ert-deftest a3madkour-pub-rewrite-test/typed-link-class-on-inert ()
  "Class is emitted even when target is private/unknown (inert variant)."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("source-id" :state live :section "garden" :slug "src"))
   (let ((result (a3madkour-pub/rewrite-link
                  "[[supports:no-such-target][text]]" "source-id")))
     ;; A.1.b decision: inert variants render as plain text. The class
     ;; only matters when the anchor is present. Document this in the
     ;; spec — typed-class is emitted ONLY on :html (live/draft), not
     ;; on :inert; the spec sentence "Class always emitted regardless
     ;; of target state" refers to the *anchor's* class, which doesn't
     ;; exist for inert variants. Update spec wording in Task 19.
     (should (equal (plist-get result :inert) "text")))))

(ert-deftest a3madkour-pub-rewrite-test/typed-link-respects-defcustom ()
  "Adding a new type to the defcustom makes it recognized; otherwise pass-through."
  (let ((a3madkour-pub-typed-link-types
         '("supports" "contradicts" "extends" "example-of" "causes" "cites")))
    (a3madkour-pub-rewrite-test--with-stubbed
     (("tgt" :state live :section "garden" :slug "y")
      ("source-id" :state live :section "garden" :slug "src"))
     (let ((result (a3madkour-pub/rewrite-link
                    "[[cites:tgt][reference]]" "source-id")))
       (should (equal (plist-get result :html)
                      "<a class=\"link-cites\" href=\"/garden/y/\">reference</a>"))))))
```

(Re. test 3 — I'm narrowing the spec wording: classes are emitted ONLY on the rendered anchor; inert variants have no anchor, hence no class. This is a deliberate narrowing of "Class always emitted regardless of target state" from the spec — captured in Task 19 spec-amendment.)

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures — `rewrite-link: scheme "supports" not yet handled` etc.

- [ ] **Step 3: Implement typed-link branch**

Update `a3madkour-publish-rewrite.el`. Add a helper:

```elisp
(defun a3madkour-pub--rewrite-typed-link (typed-link-type path text source-note-id)
  "Rewrite `[[<type>:UUID][text]]' for TYPED-LINK-TYPE (e.g., \"supports\").
Resolves via id-link rules; on :html result, adds class=\"link-<type>\"."
  (let* ((id-result (a3madkour-pub--rewrite-id-link path text source-note-id))
         (html (plist-get id-result :html)))
    (if html
        (list :html
              (replace-regexp-in-string
               "\\`<a "
               (format "<a class=\"link-%s\" " typed-link-type)
               html)
              :warnings (plist-get id-result :warnings))
      id-result)))
```

Then in `rewrite-link`'s `cond`, add a branch BEFORE the external pass-through:

```elisp
((member scheme a3madkour-pub-typed-link-types)
 (a3madkour-pub--rewrite-typed-link
  scheme
  (substring path (1+ (length scheme)))  ; drop "<type>:"
  text source-note-id))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 94 tests, 94 results as expected, 0 unexpected`.

---

### Task 18: Link rewriter — `:pending-asset` for asset-shaped links

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- rewrite-link: asset-shaped link stubs --

(ert-deftest a3madkour-pub-rewrite-test/pending-asset-relative ()
  "[[./assets/page/foo/x.png]] → :pending-asset + WARN."
  (let ((result (a3madkour-pub/rewrite-link
                 "[[./assets/page/foo/diagram.png]]" "source-id")))
    (should (equal (plist-get result :pending-asset)
                   "[[./assets/page/foo/diagram.png]]"))
    (should (= 1 (length (plist-get result :warnings))))
    (should (string-match-p "asset" (car (plist-get result :warnings))))
    (should (string-match-p "A.1.c" (car (plist-get result :warnings))))))

(ert-deftest a3madkour-pub-rewrite-test/pending-asset-relative-shared ()
  (let ((result (a3madkour-pub/rewrite-link
                 "[[./assets/shared/common.svg]]" "source-id")))
    (should (plist-get result :pending-asset))))

(ert-deftest a3madkour-pub-rewrite-test/pending-asset-absolute ()
  "Absolute path outside canonical root also returns :pending-asset."
  (let ((result (a3madkour-pub/rewrite-link
                 "[[/home/user/some/path/screenshot.jpg]]" "source-id")))
    (should (plist-get result :pending-asset))))

(ert-deftest a3madkour-pub-rewrite-test/pending-asset-tilde ()
  "Tilde-paths to canonical root also detected."
  (let ((result (a3madkour-pub/rewrite-link
                 "[[~/org/notes/assets/page/foo/x.png]]" "source-id")))
    (should (plist-get result :pending-asset))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures with various forms of "scheme nil not yet handled" (none of these have a URL scheme; they're file paths).

- [ ] **Step 3: Implement asset-shaped detection**

Add to `a3madkour-publish-rewrite.el`:

```elisp
(defun a3madkour-pub--asset-shaped-link-p (path)
  "Return non-nil if PATH looks like an asset link (image / pdf / audio / etc.).

Heuristic: PATH has no URL scheme (or scheme is `file:` for an asset
file, not an org file) AND extension is not `.org`. Captures the
common forms:
  - relative: `./assets/page/foo/x.png`, `./assets/shared/diagram.svg`
  - absolute: `/home/.../foo.png`, `~/org/notes/assets/page/foo/x.png`
A.1.c will replace this with proper canonical-root resolution."
  (and (not (a3madkour-pub--link-scheme path))
       (let ((ext (file-name-extension path)))
         (and ext (not (member ext '("org")))))))
```

Then add a branch in `rewrite-link`'s `cond`, BEFORE the catch-all error:

```elisp
((a3madkour-pub--asset-shaped-link-p path)
 (list :pending-asset org-link
       :warnings (list (format "asset link %S; rewriting deferred to A.1.c"
                                org-link))))
```

(Note: `org-link` is the raw link form, not just `path` — we want to round-trip the full `[[...]]` form so A.1.c picks up exactly what the source had.)

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 98 tests, 98 results as expected, 0 unexpected`.

---

### Task 19: USER VERIFICATION CHECKPOINT

This is for the human author. Per spec §11, every implementation stage gets a manual checkpoint.

- [ ] **Step 1: Author runs the full test suite**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`
Expected: `Ran 98 tests, 98 results as expected, 0 unexpected`. Exit `0`.

- [ ] **Step 2: Author spot-checks a real id-link via `a3-pub.sh`**

Pick any TWO notes in `~/org/notes/` with `:ID:` properties, one published (has `#+HUGO_PUBLISH: t`) and one not. Then:

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh \
  --eval "(a3madkour-pub/begin-publish)" \
  --eval "(message \"%S\" (a3madkour-pub/rewrite-link \"[[id:<published-UUID>][text]]\" \"<some-source-UUID>\"))"
```

Expected: `(:html "<a href=\"/<section>/<slug>/\">text</a>" :warnings nil)`. Substitute `<published-UUID>` with a real id.

Repeat with the unpublished note's UUID; expected: `(:inert "text" :warnings ("link target id:... is private or unknown"))`.

- [ ] **Step 3: Author spot-checks the heading-anchor against real Hugo output**

Pick a published note with at least one second-level heading. In a one-off:

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh \
  --eval "(message \"anchor: %s\" (a3madkour-pub--heading-anchor \"<exact heading text>\"))"
```

Then in the site repo:
```bash
hugo --buildDrafts --renderToMemory 2>&1 | grep -i "<exact heading text>"
```

(Or build to disk + grep `public/` for the published page's HTML.) Confirm the elisp-computed anchor matches what Hugo emits as `id="..."` on the `<h2>` tag. If they diverge on a real heading (likely candidates: punctuation, parentheses, accented chars), update `a3madkour-pub--heading-anchor` + the failing test to match Hugo's actual behavior.

- [ ] **Step 4: Author spot-checks `:pending-asset` shape**

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh \
  --eval "(message \"%S\" (a3madkour-pub/rewrite-link \"[[./assets/page/some/x.png]]\" \"source-id\"))"
```

Expected: `(:pending-asset "[[./assets/page/some/x.png]]" :warnings ("asset link \"[[./assets/page/some/x.png]]\"; rewriting deferred to A.1.c"))`.

- [ ] **Step 5: Author confirms readiness for A.1.c**

Author affirms in the session that A.1.b is sound and the next plan (A.1.c — asset handling + 24th linter pair) can begin.

---

### Task 20: Stage files for author commit (default no-commit session policy)

Per session policy default (matching A.1.a), the agent stages but does NOT commit. Skip this task if the author signaled "commit as you go" at session start.

- [ ] **Step 1: Stage dotfiles changes**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish.el \
        emacs-configs/custom/lisp/a3madkour-publish-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-history.el \
        emacs-configs/custom/lisp/a3madkour-publish-history-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-rewrite.el \
        emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-id.el \
        emacs-configs/custom/lisp/a3madkour-publish-id-test.el \
        emacs-configs/custom/lisp/run-tests.sh
git status --short | grep -E "(^A |^M ) emacs-configs/custom/lisp"
```

Expected: 9 files listed (5 modified + 4 newly created, plus the run-tests.sh modification).

- [ ] **Step 2: Stage site-repo changes**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add docs/superpowers/plans/2026-05-20-phase-3-a1-b-link-rewriter.md
git status --short | grep a1-b
```

Expected: 1 file staged.

- [ ] **Step 3: Suggested commit messages (author runs)**

In dotfiles:

```bash
git commit -m "feat(publish): A.1.b link rewriter + ID dispatching + carry-forwards

Sub-project A.1.b of the Phase 3 org→Hugo publish pipeline.

- a3madkour-publish-rewrite.el: rewrite-link (id / file / heading / external
  / typed) + Goldmark github heading-anchor slugifier + asset-shaped link
  :pending-asset stub for A.1.c.
- a3madkour-publish-id.el: --id-to-file via org-roam-id-find (isolates the
  org-roam dep boundary).
- a3madkour-publish.el (entry): note-metadata accessor + per-publish hash
  table memoization; 4 public accessors become thin wrappers AND now
  accept file-or-id; begin-publish entry resets cache + invokes
  org-roam-db-sync; redundant empty-string guards dropped.
- a3madkour-publish-history.el: record-publish gains :had-slug-override-p
  keyword + --diff-reason emits slug_override correctly.
- run-tests.sh: adds (straight-use-package 'org-roam) to bootstrap.

98 ert tests; all passing.  Manual snapshot semantics: metadata cache
+ org-roam DB synced at begin-publish; edits mid-publish are NOT picked
up until the next snapshot.  Publish invokable from shell (a3-pub.sh)
or interactively (M-x)."
```

In site repo:

```bash
git commit -m "docs(phase-3): A.1.b link-rewriter plan

Plan doc for the A.1.b implementation slice (link rewriter + ID
dispatching + 3 carry-forward items from A.1.a)."
```

---

## Self-Review

**Spec coverage (parent + design doc):**
- ✅ Per-link-type table (parent §6) — Tasks 13 (external), 14 (id-links live/draft/private), 15 (heading anchors), 16 (file-link auto-convert), 17 (typed links), 18 (`:pending-asset` for assets).
- ✅ Custom typed-link CSS class emission (parent §6) — Task 17, with documented narrowing (class only on `:html` variants).
- ✅ ID dispatching (parent §10) — Tasks 7–9.
- ✅ `note-metadata` + memoization (carry-forward #2, design §3) — Tasks 3–5.
- ✅ Drop redundant guards (carry-forward #3) — Task 6.
- ✅ `:had-slug-override-p` keyword on `record-publish` (carry-forward #1) — Task 10.
- ✅ Goldmark heading-anchor algorithm (design §5 + parent §6 amendment) — Task 12.
- ✅ `:pending-asset` sentinel (design §2 + parent §6 amendment) — Task 18.
- ✅ Snapshot-at-publish-start semantics (design §3 + parent §11 amendment) — Tasks 4, 5, 9, and docstrings throughout.
- ✅ Testing strategy (design §8) — Tasks 3–18 each have ert tests; Task 19 = manual checkpoint.
- ✅ File organization (design §4) — 4 new files + 4 modified, matches.

**Placeholder scan:** no "TBD" / "TODO" in this plan; the Goldmark-algorithm caveat in Task 12 ("update if real Hugo output diverges") is a documented adjust-on-empirical-evidence note, not a placeholder for missing content.

**Type consistency:** `rewrite-link` returns `:html` / `:inert` / `:pending-asset` consistently across all tasks. `note-metadata` plist keys (`:id :section :slug :state :file :title`) match between Task 3 (introduction) and Tasks 6, 9, 15 (consumers). `record-publish` signature in Task 10 matches the carry-forward expectation. `--id-to-file` signature is `(id)` in Task 8 and `(id)` in Task 9.

**Test count integrity:** A.1.a left 45 green tests. Each task adds a documented count: +3 +3 +2 (Task 3+4+5) +0 (Task 6 refactor) +3 (Task 8) +5 (Task 9) +3 (Task 10) +11 (Task 12) +5 (Task 13) +5 (Task 14) +3 (Task 15) +2 (Task 16) +4 (Task 17) +4 (Task 18) = 53 new tests. Total target: 45 + 53 = 98. Task 19 step 1 asserts 98.
