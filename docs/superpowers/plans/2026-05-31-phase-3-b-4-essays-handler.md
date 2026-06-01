# Phase 3 B.4 — essays handler implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the essays handler — first `publish-deliberate` slice. Per-essay org sources at `~/org/essays/<slug>.org` become Hugo bundles at `content/essays/<slug>/index.md` via `M-x a3-publish-deliberate <file>` / `a3-pub.sh --publish-deliberate <path>`. Includes the B.0 `finish-publish :scope` contract amend so deliberate runs don't catastrophically unpublish other bundles.

**Architecture:** New `a3madkour-publish-essays.el` module mirrors B.3's per-page-bundle pattern (rewrite-to-tmp-file → export → normalize → asset-copy → write-if-different → record-publish). New essays dispatch arm in `a3madkour-publish-frontmatter.el` handles 14 required + 4 optional frontmatter keys, including 6 `has_*` flags derived from post-export markdown body scan with `#+HUGO_HAS_<X>:` keyword override. `finish-publish` gains a `:scope` keyword (`'living` default; `'deliberate` skips Step A + C and narrows Step B to the single touched id).

**Tech Stack:** Emacs Lisp (ert tests), ox-hugo, Python 3 stdlib (integration tests via `unittest`).

**Spec:** `docs/superpowers/specs/2026-05-31-phase-3-b-4-essays-handler-design.md`

**Working directories:**
- Dotfiles: `/Users/a3madkour/dotfiles/`
- Site: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`
- Author org sources: `~/org/essays/` (created by Task 16)

**Test commands (used throughout):**
- ert: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -20`
- integration: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration -v 2>&1 | tail -30`

---

## Task 1 — `essays-dir` defvar

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` (add defvar near existing `a3madkour-pub/org-notes-dir`)
- Test: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el` (add assertion)

- [ ] **Step 1: Locate the existing org-notes-dir defvar**

Run: `grep -n "org-notes-dir" /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
Note the line number; the new defvar lands immediately below it.

- [ ] **Step 2: Write failing test**

Append to `a3madkour-publish-test.el` before its `(provide ...)`:

```elisp
(ert-deftest a3madkour-pub-test/essays-dir-defvar-exists ()
  "B.4 Task 1: `a3madkour-pub/essays-dir' must be a defcustom or defvar,
non-empty string, defaulting to a path under ~/org/."
  (should (boundp 'a3madkour-pub/essays-dir))
  (should (stringp a3madkour-pub/essays-dir))
  (should (not (string-empty-p a3madkour-pub/essays-dir)))
  (should (string-match-p "/org/essays" a3madkour-pub/essays-dir)))
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "essays-dir-defvar|FAIL|Ran" | head -5`
Expected: `FAIL` (symbol-not-bound for `a3madkour-pub/essays-dir`).

- [ ] **Step 4: Add the defvar**

Add to `a3madkour-publish.el` immediately after the `a3madkour-pub/org-notes-dir` block:

```elisp
(defcustom a3madkour-pub/essays-dir (expand-file-name "~/org/essays/")
  "Directory holding essay source `.org' files for B.4 essays handler.

Essays are NOT roam-indexed and do NOT live under
`a3madkour-pub/org-notes-dir'.  The handler walks this directory only
under `publish-deliberate'; `publish-living' does not touch essays."
  :type 'directory
  :group 'a3madkour-pub)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "essays-dir-defvar|Ran [0-9]+ tests"`
Expected: `passed N/N a3madkour-pub-test/essays-dir-defvar-exists` and `Ran <count> tests, <count> results as expected, 0 unexpected`.

- [ ] **Step 6: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish.el emacs-configs/custom/lisp/a3madkour-publish-test.el
git commit -m "$(cat <<'EOF'
feat(b-4): a3madkour-pub/essays-dir defcustom (Task 1)

New defcustom defaults to ~/org/essays/.  Parallel to org-notes-dir
but scoped to B.4 essays handler — essays are not roam-indexed and
publish-living does not touch them.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2 — `finish-publish :scope` kwarg (B.0 contract amend)

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el:196` (`a3madkour-pub/finish-publish` signature + Step A/B/C conditionals)
- Test: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el`

- [ ] **Step 1: Write 4 failing tests**

Append to `a3madkour-publish-unpublish-test.el` before its `(provide ...)`:

```elisp
;; -- B.4 Task 2: finish-publish :scope keyword --

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-deliberate-skips-step-a ()
  "B.4: :scope 'deliberate does NOT delete bundles for ids missing from
the accumulator.  Seed manifest with 3 live ids; accumulator has only
id-a; assert no `record-publish' with state `removed' fired."
  (let ((tmp-data-dir (make-temp-file "a3-pub-data-" t))
        (tmp-content (make-temp-file "a3-pub-content-" t))
        removed-ids)
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir (file-name-as-directory tmp-data-dir))
              (a3madkour-pub--manifest-snapshot
               '((notes . [((id . "id-a") (current_url . "/garden/a/") (state . "live"))
                           ((id . "id-b") (current_url . "/garden/b/") (state . "live"))
                           ((id . "id-c") (current_url . "/garden/c/") (state . "live"))]))))
          (clrhash a3madkour-pub--publish-run-accumulator)
          (puthash "id-a" (cons "/garden/a/" 'live) a3madkour-pub--publish-run-accumulator)
          (cl-letf (((symbol-function 'a3madkour-pub--unpublish-delete-bundle)
                     (lambda (&rest _) (error "delete-bundle should not be called")))
                    ((symbol-function 'a3madkour-pub-history/record-publish)
                     (lambda (id _url state)
                       (when (eq state 'removed) (push id removed-ids)))))
            (a3madkour-pub/finish-publish :scope 'deliberate))
          (should-not removed-ids))
      (delete-directory tmp-data-dir t)
      (delete-directory tmp-content t))))

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-deliberate-step-b-narrows ()
  "B.4: :scope 'deliberate runs Step B only for the touched id.
Manifest has id-a at /garden/a/; accumulator has id-a at /garden/a-renamed/
AND manifest has id-b at /garden/b-old/ that's NOT in accumulator.
Step B fires for id-a only."
  (let ((tmp-data-dir (make-temp-file "a3-pub-data-" t))
        renamed-pairs)
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir (file-name-as-directory tmp-data-dir))
              (a3madkour-pub--manifest-snapshot
               '((notes . [((id . "id-a") (current_url . "/garden/a/") (state . "live"))
                           ((id . "id-b") (current_url . "/garden/b-old/") (state . "live"))]))))
          (clrhash a3madkour-pub--publish-run-accumulator)
          (puthash "id-a" (cons "/garden/a-renamed/" 'live)
                   a3madkour-pub--publish-run-accumulator)
          (cl-letf (((symbol-function 'a3madkour-pub--unpublish-rename-asset-dir)
                     (lambda (old new &rest _) (push (cons old new) renamed-pairs)))
                    ((symbol-function 'a3madkour-pub--unpublish-bulk-rewrite-source-links)
                     (lambda (&rest _) nil))
                    ((symbol-function 'a3madkour-pub--unpublish-delete-bundle)
                     (lambda (&rest _) nil))
                    ((symbol-function 'a3madkour-pub-history/record-publish)
                     (lambda (&rest _) nil)))
            (a3madkour-pub/finish-publish :scope 'deliberate))
          (should (equal renamed-pairs '(("a" . "a-renamed")))))
      (delete-directory tmp-data-dir t))))

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-deliberate-step-c-skipped ()
  "B.4: :scope 'deliberate returns :orphan-warnings nil (Step C never ran)."
  (let ((tmp-data-dir (make-temp-file "a3-pub-data-" t)))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir (file-name-as-directory tmp-data-dir))
              (a3madkour-pub--manifest-snapshot
               '((notes . [((id . "id-a") (current_url . "/garden/a/") (state . "live"))]))))
          (clrhash a3madkour-pub--publish-run-accumulator)
          (puthash "id-a" (cons "/garden/a/" 'live) a3madkour-pub--publish-run-accumulator)
          (cl-letf (((symbol-function 'a3madkour-pub--unpublish-recheck-live-note-links)
                     (lambda (&rest _) (error "recheck should not be called"))))
            (let ((result (a3madkour-pub/finish-publish :scope 'deliberate)))
              (should-not (plist-get result :orphan-warnings)))))
      (delete-directory tmp-data-dir t))))

(ert-deftest a3madkour-pub-unpublish-test/finish-publish-living-default-unchanged ()
  "B.4: :scope defaults to 'living; called with no kwargs runs full
Step A + B + C (existing behavior).  Sanity check that the kwarg
addition didn't regress the default path."
  (let ((tmp-data-dir (make-temp-file "a3-pub-data-" t))
        deleted-bundles)
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir (file-name-as-directory tmp-data-dir))
              (a3madkour-pub--manifest-snapshot
               '((notes . [((id . "id-a") (current_url . "/garden/a/") (state . "live"))
                           ((id . "id-b") (current_url . "/garden/b/") (state . "live"))]))))
          (clrhash a3madkour-pub--publish-run-accumulator)
          (puthash "id-a" (cons "/garden/a/" 'live) a3madkour-pub--publish-run-accumulator)
          (cl-letf (((symbol-function 'a3madkour-pub--unpublish-delete-bundle)
                     (lambda (section slug &rest _) (push (cons section slug) deleted-bundles)))
                    ((symbol-function 'a3madkour-pub-history/record-publish) (lambda (&rest _) nil))
                    ((symbol-function 'a3madkour-pub--unpublish-recheck-live-note-links)
                     (lambda (&rest _) nil)))
            (a3madkour-pub/finish-publish))
          ;; Living scope: id-b is "removed" (not in accumulator), bundle deleted.
          (should (member '("garden" . "b") deleted-bundles)))
      (delete-directory tmp-data-dir t))))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "deliberate-skips|deliberate-step|living-default-unchanged|FAIL" | head -10`
Expected: 3 deliberate tests FAIL (scope kwarg not recognized → step A still runs → removed-ids populated). `living-default-unchanged` may pass or fail depending on existing finish-publish semantics; check the output.

- [ ] **Step 3: Modify `finish-publish` signature + Step A/B/C conditionals**

In `a3madkour-publish-unpublish.el`, replace the existing `cl-defun a3madkour-pub/finish-publish` block (currently lines ~196-272) with:

```elisp
(cl-defun a3madkour-pub/finish-publish (&key dry-run (scope 'living))
  "Orchestrate the unpublish flow.  Returns a plist.

When DRY-RUN is non-nil: no FS writes, no manifest mutation.

SCOPE is `'living' (default) or `'deliberate'.  `'living' runs the
full Step A unpublish-sweep + Step B slug-shift + Step C re-link-check
against the diff of new-set vs manifest.  `'deliberate' skips Step A
and Step C entirely (the accumulator carries only the touched files,
so `\"missing from accumulator\"' has no meaning) and narrows Step B
to the single accumulator entry's slug-shift if its URL differs from
the manifest.

Sub-steps (in fixed order):
  Step A — unpublish sweep: diff new live-set vs manifest live+draft;
           for each :removed, delete `content/<section>/<slug>/' bundle +
           call `record-publish' with state `removed' to mutate manifest.
           SKIPPED under `'deliberate'.
  Step B — slug-shift sync: rename `<asset-root>/page/<old-slug>/' →
           `<new-slug>/' and bulk-rewrite source .org link references.
           Under `'deliberate', narrowed to the single accumulator entry.
  Step C — re-link-check: scan live notes' outgoing [[id:...]] links;
           WARN for any link resolving into removed-this-publish-set.
           SKIPPED under `'deliberate'.

New-set is read from `a3madkour-pub--publish-run-accumulator' (B-coupled
mode); if empty, falls back to `walk-published-source-set' (standalone
mode — used today before B ships).

Returns:
  (:added          (id ...)
   :stayed         (id ...)
   :removed        (id ...)
   :slug-shifted   ((old-slug . new-slug) ...)
   :orphan-warnings (\"WARN: ...\" ...))"
  (let* ((new-set (if (zerop (hash-table-count a3madkour-pub--publish-run-accumulator))
                      (a3madkour-pub/walk-published-source-set)
                    (copy-hash-table a3madkour-pub--publish-run-accumulator)))
         (diff (a3madkour-pub/diff-published-set new-set))
         (removed (plist-get diff :removed))
         (shifts (plist-get diff :slug-shifted))
         (manifest (a3madkour-pub-history/read-manifest))
         (notes (alist-get 'notes manifest))
         (removed-set (make-hash-table :test 'equal))
         slug-shifted-result orphan-warnings)
    ;; Step A: sweep.  Skipped under 'deliberate.
    (unless (eq scope 'deliberate)
      (dolist (id removed)
        (puthash id t removed-set)
        (let* ((idx (a3madkour-pub-history--find-note-by-id notes id))
               (entry (when idx (aref notes idx)))
               (url (when entry (alist-get 'current_url entry)))
               (parts (when url (a3madkour-pub--unpublish-url-to-section-slug url))))
          (when (and parts (not dry-run))
            (a3madkour-pub--unpublish-delete-bundle (car parts) (cdr parts))
            (a3madkour-pub-history/record-publish id nil 'removed)))))
    ;; Step B: slug-shift sync.  Under 'deliberate, narrow to touched ids.
    (let ((deliberate-ids
           (when (eq scope 'deliberate)
             (let ((ids nil))
               (maphash (lambda (k _v) (push k ids))
                        a3madkour-pub--publish-run-accumulator)
               ids))))
      (dolist (shift shifts)
        (when (or (not (eq scope 'deliberate))
                  (member (car shift) deliberate-ids))
          (let* ((old-url (nth 1 shift))
                 (new-url (nth 2 shift))
                 (old-parts (a3madkour-pub--unpublish-url-to-section-slug old-url))
                 (new-parts (a3madkour-pub--unpublish-url-to-section-slug new-url)))
            (when (and old-parts new-parts)
              (let ((old-slug (cdr old-parts))
                    (new-slug (cdr new-parts)))
                (unless dry-run
                  (a3madkour-pub--unpublish-rename-asset-dir old-slug new-slug)
                  (a3madkour-pub--unpublish-bulk-rewrite-source-links old-slug new-slug)
                  (a3madkour-pub--unpublish-delete-bundle
                   (car old-parts) (cdr old-parts)))
                (push (cons old-slug new-slug) slug-shifted-result)))))))
    ;; Step C: re-link-check (read-only; runs in dry-run too).  Skipped under 'deliberate.
    (when (and (not (eq scope 'deliberate))
               (> (hash-table-count removed-set) 0))
      (setq orphan-warnings
            (a3madkour-pub--unpublish-recheck-live-note-links removed-set)))
    ;; Clear manifest snapshot now that the publish run is over.
    (setq a3madkour-pub--manifest-snapshot nil)
    (list :added (plist-get diff :added)
          :stayed (plist-get diff :stayed)
          :removed (if (eq scope 'deliberate) nil removed)
          :slug-shifted (nreverse slug-shifted-result)
          :orphan-warnings orphan-warnings)))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -15`
Expected: 4 new tests PASS; all existing tests still PASS; final line `Ran <N> tests, <N> results as expected, 0 unexpected`.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el
git commit -m "$(cat <<'EOF'
feat(b-4): finish-publish :scope kwarg (B.0 contract amend, Task 2)

`:scope 'deliberate' skips Step A unpublish-sweep + Step C re-link-check
(accumulator-as-new-set carries no "removed" meaning under deliberate);
Step B narrows to the touched-id slug-shift only.  Default `'living'
keeps existing behavior.  Closes the B.0 gap that would have
catastrophically unpublished other bundles on first deliberate run.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3 — Essays normalizer dispatch arm (skeleton + required keys)

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` (add `'essays` arm to dispatch + new helper `--normalize-essays`)
- Test: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests**

Append to `a3madkour-publish-frontmatter-test.el` before its `(provide ...)`:

```elisp
;; -- B.4 Task 3: essays normalizer skeleton --

(ert-deftest a3madkour-pub-frontmatter-test/essays-known-section ()
  "B.4 Task 3: dispatch accepts 'essays without erroring."
  (let ((tmp (make-temp-file "essays-norm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let ((result (a3madkour-pub-frontmatter/normalize
                         'essays
                         '((title . "x") (date . "2026-04-12"))
                         tmp)))
            (should (listp result))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-frontmatter-test/essays-required-keys-present ()
  "B.4 Task 3: normalize emits all 14 required essay frontmatter keys."
  (let ((tmp (make-temp-file "essays-norm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let* ((raw '((title . "Test") (date . "2026-04-12") (summary . "S")
                        (tags . ("a"))))
                 (out (a3madkour-pub-frontmatter/normalize 'essays raw tmp))
                 (required '(title date lastmod draft summary tags series series_order
                             toc has_sidenotes has_citations has_footnotes has_math
                             has_widgets has_video_sync)))
            (dolist (k required)
              (should (assq k out)))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-frontmatter-test/essays-draft-defaults-false ()
  "B.4 Task 3: absent draft → false."
  (let ((tmp (make-temp-file "essays-norm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let ((out (a3madkour-pub-frontmatter/normalize
                      'essays '((title . "x") (date . "2026-04-12")) tmp)))
            (should (eq (alist-get 'draft out) nil))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-frontmatter-test/essays-toc-defaults-true ()
  "B.4 Task 3: absent toc → true."
  (let ((tmp (make-temp-file "essays-norm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let ((out (a3madkour-pub-frontmatter/normalize
                      'essays '((title . "x") (date . "2026-04-12")) tmp)))
            (should (eq (alist-get 'toc out) t))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-frontmatter-test/essays-noise-keys-dropped ()
  "B.4 Task 3: ox-hugo noise keys NOT in the essay contract are dropped."
  (let ((tmp (make-temp-file "essays-norm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let* ((raw '((title . "x") (date . "2026-04-12") (author . "noise")
                        (slug . "noise")))
                 (out (a3madkour-pub-frontmatter/normalize 'essays raw tmp)))
            (should-not (assq 'author out))
            (should-not (assq 'slug out))))
      (delete-file tmp))))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "essays-known-section|essays-required-keys|essays-draft-defaults|essays-toc-defaults|essays-noise|FAIL" | head -15`
Expected: `essays-known-section` fails with `unknown section 'essays'`; the other 4 fail because dispatch errors before computing anything.

- [ ] **Step 3: Add `'essays` to known sections + dispatch arm**

In `a3madkour-publish-frontmatter.el`:

(a) Update the `a3madkour-pub-frontmatter--known-sections` defconst to include `essays`. Find and replace:

```elisp
(defconst a3madkour-pub-frontmatter--known-sections
  '(garden essay library research-themes research-questions
           works streams about
           library-reading library-listening library-playing library-watching)
  "Closed set of section symbols `normalize' accepts.  Updated as new
sections are added (none planned beyond this set).")
```

with:

```elisp
(defconst a3madkour-pub-frontmatter--known-sections
  '(garden essay essays library research-themes research-questions
           works streams about
           library-reading library-listening library-playing library-watching)
  "Closed set of section symbols `normalize' accepts.  Updated as new
sections are added (none planned beyond this set).

B.4 adds `essays' (plural).  `essay' (singular) is kept reserved per
parent spec but the live dispatch uses `essays'.")
```

(b) In the `cond` of `a3madkour-pub-frontmatter/normalize`, add the new arm BEFORE the `(t ...)` pass-through:

```elisp
   ((eq section 'essays)
    (a3madkour-pub-frontmatter--normalize-essays raw-alist source-file))
```

(c) Add the skeleton normalizer immediately before the existing `--normalize-garden`:

```elisp
(defconst a3madkour-pub-frontmatter--essay-required-keys
  '(title date lastmod draft summary tags series series_order toc
          has_sidenotes has_citations has_footnotes has_math
          has_widgets has_video_sync)
  "14 required frontmatter keys per check_fixtures.py essay contract.")

(defconst a3madkour-pub-frontmatter--essay-optional-keys
  '(tile_size featured hero source_stream)
  "4 optional frontmatter keys per CLAUDE.md essay contract.")

(defun a3madkour-pub-frontmatter--normalize-essays (raw-alist source-file)
  "B.4: essays frontmatter normalizer.

Pipeline:
  1. Drop ox-hugo noise keys (anything not in required ∪ optional).
  2. Coerce draft to bool (default false), toc to bool (default true).
  3. Default series=\"\", series_order=0 (always emitted for linter parity).
  4. Resolve lastmod via last-modified-cascade (drawer → keyword → git → fs → today).
  5. Default all 6 has_* flags to nil; Tasks 4-5 add real scan + override merge.
Returns the normalized alist."
  (let* ((allowed (append a3madkour-pub-frontmatter--essay-required-keys
                          a3madkour-pub-frontmatter--essay-optional-keys))
         (out (cl-remove-if-not (lambda (cell) (memq (car cell) allowed))
                                (copy-alist raw-alist))))
    ;; draft default false
    (unless (assq 'draft out)
      (push (cons 'draft nil) out))
    (when (assq 'draft out)
      (let ((v (alist-get 'draft out)))
        (setf (alist-get 'draft out) (and v (not (eq v nil)) t))))
    ;; toc default true
    (unless (assq 'toc out)
      (push (cons 'toc t) out))
    (when (assq 'toc out)
      (let ((v (alist-get 'toc out)))
        (setf (alist-get 'toc out) (if (memq v '(nil :nil)) nil t))))
    ;; series defaults
    (unless (assq 'series out)
      (push (cons 'series "") out))
    (unless (assq 'series_order out)
      (push (cons 'series_order 0) out))
    (when-let ((so (alist-get 'series_order out)))
      (when (stringp so)
        (setf (alist-get 'series_order out) (string-to-number so))))
    ;; lastmod cascade
    (let* ((drawer-lm (alist-get 'last_modified raw-alist))
           (kw-lm     (alist-get 'lastmod raw-alist))
           (kw-trim   (when (and (stringp kw-lm) (>= (length kw-lm) 10))
                        (substring kw-lm 0 10))))
      (setq out (assq-delete-all 'lastmod out))
      (setq out (assq-delete-all 'last_modified out))
      (setf (alist-get 'lastmod out)
            (a3madkour-pub-frontmatter/last-modified-cascade
             source-file
             :drawer  drawer-lm
             :keyword kw-trim)))
    ;; Defaults for required has_* flags (Task 4-5 add real wiring).
    (dolist (k '(has_sidenotes has_citations has_footnotes has_math
                                has_widgets has_video_sync))
      (unless (assq k out)
        (push (cons k nil) out)))
    out))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -10`
Expected: 5 new essays normalizer tests PASS; total test count grows by 5; final line shows `0 unexpected`.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "$(cat <<'EOF'
feat(b-4): essays normalizer dispatch arm + skeleton (Task 3)

Adds `'essays' to known-sections + dispatch arm.  Skeleton normalizer
emits all 14 required keys (defaults: draft=false, toc=true,
series=\"\", series_order=0, has_*=nil); lastmod cascade wired;
ox-hugo noise keys dropped.  Tasks 4-5 add has_* scan + override merge.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4 — `has_*` body scanner helper

**Files:**
- Create: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays.el` (new module — first contents)
- Create: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays-test.el` (new test module)

- [ ] **Step 1: Write 12 failing tests in new test file**

Create `a3madkour-publish-essays-test.el`:

```elisp
;;; a3madkour-publish-essays-test.el --- ert tests for B.4 essays handler -*- lexical-binding: t; -*-

;;; Code:

(require 'ert)
(require 'cl-lib)
(require 'a3madkour-publish-essays)

;; -- B.4 Task 4: has_* body scanner --

(ert-deftest a3madkour-pub-essays-test/scan-sidenotes-positive ()
  (should (eq t (plist-get
                 (a3madkour-pub-essays--scan-has-flags
                  "lorem {{< sidenote >}}x{{< /sidenote >}} ipsum")
                 :has_sidenotes))))

(ert-deftest a3madkour-pub-essays-test/scan-sidenotes-negative ()
  (should-not (plist-get
               (a3madkour-pub-essays--scan-has-flags "plain text only")
               :has_sidenotes)))

(ert-deftest a3madkour-pub-essays-test/scan-citations-positive ()
  (should (eq t (plist-get
                 (a3madkour-pub-essays--scan-has-flags "see {{< cite \"k\" >}} here")
                 :has_citations))))

(ert-deftest a3madkour-pub-essays-test/scan-citations-negative ()
  (should-not (plist-get
               (a3madkour-pub-essays--scan-has-flags "plain text only")
               :has_citations)))

(ert-deftest a3madkour-pub-essays-test/scan-footnotes-positive ()
  (should (eq t (plist-get
                 (a3madkour-pub-essays--scan-has-flags "lorem[^1] ipsum\n\n[^1]: note")
                 :has_footnotes))))

(ert-deftest a3madkour-pub-essays-test/scan-footnotes-negative ()
  (should-not (plist-get
               (a3madkour-pub-essays--scan-has-flags "plain text only no refs")
               :has_footnotes)))

(ert-deftest a3madkour-pub-essays-test/scan-math-shortcode ()
  (should (eq t (plist-get
                 (a3madkour-pub-essays--scan-has-flags
                  "see {{< math >}}\\alpha{{< /math >}}")
                 :has_math))))

(ert-deftest a3madkour-pub-essays-test/scan-math-inline-delim ()
  (should (eq t (plist-get
                 (a3madkour-pub-essays--scan-has-flags "see \\(\\alpha\\) here")
                 :has_math))))

(ert-deftest a3madkour-pub-essays-test/scan-math-display-delim ()
  (should (eq t (plist-get
                 (a3madkour-pub-essays--scan-has-flags "see \\[\\alpha\\] here")
                 :has_math))))

(ert-deftest a3madkour-pub-essays-test/scan-math-negative ()
  (should-not (plist-get
               (a3madkour-pub-essays--scan-has-flags "plain text only")
               :has_math)))

(ert-deftest a3madkour-pub-essays-test/scan-widgets-positive ()
  (should (eq t (plist-get
                 (a3madkour-pub-essays--scan-has-flags "see {{< widget \"x\" >}}")
                 :has_widgets))))

(ert-deftest a3madkour-pub-essays-test/scan-widgets-negative ()
  (should-not (plist-get
               (a3madkour-pub-essays--scan-has-flags "plain text only")
               :has_widgets)))

(ert-deftest a3madkour-pub-essays-test/scan-video-sync-positive ()
  (should (eq t (plist-get
                 (a3madkour-pub-essays--scan-has-flags "see {{< video-sync \"x\" >}}")
                 :has_video_sync))))

(ert-deftest a3madkour-pub-essays-test/scan-video-sync-negative ()
  (should-not (plist-get
               (a3madkour-pub-essays--scan-has-flags "plain text only")
               :has_video_sync)))

(provide 'a3madkour-publish-essays-test)

;;; a3madkour-publish-essays-test.el ends here
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "Cannot open load file|FAIL" | head -5`
Expected: `Cannot open load file: a3madkour-publish-essays` — module doesn't exist yet.

- [ ] **Step 3: Create the module with the scanner**

Create `a3madkour-publish-essays.el`:

```elisp
;;; a3madkour-publish-essays.el --- B.4 essays per-file publish handler  -*- lexical-binding: t; -*-

;;; Commentary:

;; B.4: essays per-file publish handler (first publish-deliberate slice).
;; Pipeline mirrors B.1/B.3 (pre-export-rewrite → export → normalize →
;; asset-copy → write-if-different → record-publish), with a novel
;; post-export markdown body scan for the 6 `has_*' frontmatter flags.
;;
;; Registered into `a3madkour-pub-deliberate--handlers' (see Task 9) as
;;   (essays . a3madkour-pub-essays/publish-essay-file)

;;; Code:

(require 'a3madkour-publish)
(require 'a3madkour-publish-export)
(require 'a3madkour-publish-frontmatter)
(require 'a3madkour-publish-rewrite)
(require 'a3madkour-publish-assets)
(require 'a3madkour-publish-history)

;; Task 4: has_* body scanner.

(defun a3madkour-pub-essays--scan-has-flags (body)
  "Return a plist of 6 has_* booleans derived from substring scan of BODY
(post-export markdown).

Patterns (all case-sensitive; shortcodes match the trailing space):
  :has_sidenotes  ← `{{< sidenote '
  :has_citations  ← `{{< cite '
  :has_footnotes  ← `[^N]' markdown footnote reference
  :has_math       ← `{{< math ' OR raw KaTeX delim `\\(` OR `\\['
  :has_widgets    ← `{{< widget '
  :has_video_sync ← `{{< video-sync '

Each value is `t' on a positive match or `nil' on no match.  Callers
merge with per-keyword `#+HUGO_HAS_<X>:' overrides (see Task 5)."
  (list :has_sidenotes  (and (string-match-p "{{< sidenote " body) t)
        :has_citations  (and (string-match-p "{{< cite "     body) t)
        :has_footnotes  (and (string-match-p "\\[\\^[^]]+\\]" body) t)
        :has_math       (and (or (string-match-p "{{< math "  body)
                                 (string-match-p "\\\\("      body)
                                 (string-match-p "\\\\\\["    body)) t)
        :has_widgets    (and (string-match-p "{{< widget "    body) t)
        :has_video_sync (and (string-match-p "{{< video-sync " body) t)))

(provide 'a3madkour-publish-essays)

;;; a3madkour-publish-essays.el ends here
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "essays-test/scan|Ran [0-9]+ tests" | tail -20`
Expected: All 14 scan-* tests pass; `Ran <N> tests, <N> results as expected, 0 unexpected`.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-essays.el emacs-configs/custom/lisp/a3madkour-publish-essays-test.el
git commit -m "$(cat <<'EOF'
feat(b-4): essays module + has_* body scanner (Task 4)

New `a3madkour-publish-essays.el` module with `--scan-has-flags' —
post-export markdown body scan for 6 has_* flags (sidenotes / citations
/ footnotes / math / widgets / video-sync).  Math detects shortcode OR
raw KaTeX inline + display delim.  14 ert tests cover positive +
negative for each flag (math counts triple).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5 — `has_*` override merge into essays normalizer

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays.el` (add merge helper + a metadata reader)
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` (consume merge result)
- Test: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays-test.el`

- [ ] **Step 1: Write failing tests**

Append to `a3madkour-publish-essays-test.el` before its `(provide ...)`:

```elisp
;; -- B.4 Task 5: has_* override merge --

(ert-deftest a3madkour-pub-essays-test/merge-keyword-override-wins-false ()
  "Body has sidenote shortcode AND #+HUGO_HAS_SIDENOTES: nil → false."
  (let ((tmp (make-temp-file "essays-merge-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp
            (insert "#+HUGO_HAS_SIDENOTES: nil\n"))
          (let* ((scan '(:has_sidenotes t :has_citations nil
                         :has_footnotes nil :has_math nil
                         :has_widgets nil :has_video_sync nil))
                 (merged (a3madkour-pub-essays--merge-has-flags scan tmp)))
            (should (eq (plist-get merged :has_sidenotes) nil))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-essays-test/merge-keyword-override-wins-true ()
  "No body shortcode but #+HUGO_HAS_WIDGETS: t → true."
  (let ((tmp (make-temp-file "essays-merge-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp
            (insert "#+HUGO_HAS_WIDGETS: t\n"))
          (let* ((scan '(:has_sidenotes nil :has_citations nil
                         :has_footnotes nil :has_math nil
                         :has_widgets nil :has_video_sync nil))
                 (merged (a3madkour-pub-essays--merge-has-flags scan tmp)))
            (should (eq (plist-get merged :has_widgets) t))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-essays-test/merge-absent-keyword-uses-scan ()
  "No #+HUGO_HAS_* keywords → scan result wins."
  (let ((tmp (make-temp-file "essays-merge-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp
            (insert "#+title: x\n"))
          (let* ((scan '(:has_sidenotes t :has_citations nil
                         :has_footnotes t :has_math nil
                         :has_widgets nil :has_video_sync nil))
                 (merged (a3madkour-pub-essays--merge-has-flags scan tmp)))
            (should (eq (plist-get merged :has_sidenotes) t))
            (should (eq (plist-get merged :has_citations) nil))
            (should (eq (plist-get merged :has_footnotes) t))))
      (delete-file tmp))))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "merge-keyword|merge-absent|symbol's function definition|FAIL" | head -10`
Expected: 3 tests FAIL (`a3madkour-pub-essays--merge-has-flags` not defined).

- [ ] **Step 3: Add the merge helper to the essays module**

Append to `a3madkour-publish-essays.el` BEFORE `(provide ...)`:

```elisp
;; Task 5: has_* override merge.

(defconst a3madkour-pub-essays--has-flag-keywords
  '((:has_sidenotes  . "HUGO_HAS_SIDENOTES")
    (:has_citations  . "HUGO_HAS_CITATIONS")
    (:has_footnotes  . "HUGO_HAS_FOOTNOTES")
    (:has_math       . "HUGO_HAS_MATH")
    (:has_widgets    . "HUGO_HAS_WIDGETS")
    (:has_video_sync . "HUGO_HAS_VIDEO_SYNC"))
  "Alist mapping each has_* plist key to its `#+HUGO_HAS_<X>:' keyword.")

(defun a3madkour-pub-essays--read-has-override (file plist-key)
  "Read `#+HUGO_<KEYWORD>:' from FILE for PLIST-KEY.
Returns a 3-state value: t (\"t\"/\"true\"/\"1\" → t), nil (\"nil\"/\"false\"/\"0\" → nil),
or `:unset' if the keyword is absent or value is empty."
  (let* ((kw (cdr (assq plist-key a3madkour-pub-essays--has-flag-keywords)))
         (raw (a3madkour-pub-frontmatter--read-org-keyword file kw)))
    (cond
     ((null raw) :unset)
     ((member (downcase raw) '("t" "true" "1" "yes")) t)
     ((member (downcase raw) '("nil" "false" "0" "no")) nil)
     (t :unset))))

(defun a3madkour-pub-essays--merge-has-flags (scan-plist file)
  "Merge keyword override on top of SCAN-PLIST for FILE.
For each has_* key: if `#+HUGO_HAS_<X>:' is set in FILE, its value wins;
else SCAN-PLIST's value passes through.  Returns a new plist."
  (let ((out (copy-sequence scan-plist)))
    (dolist (cell a3madkour-pub-essays--has-flag-keywords)
      (let* ((k (car cell))
             (override (a3madkour-pub-essays--read-has-override file k)))
        (unless (eq override :unset)
          (setq out (plist-put out k override)))))
    out))
```

- [ ] **Step 4: Wire the merge into the essays normalizer**

In `a3madkour-publish-frontmatter.el`, replace the `--normalize-essays` defun's tail section (the loop that defaults has_* flags) so the function reads:

Find:
```elisp
    ;; Defaults for required has_* flags (Task 4-5 add real wiring).
    (dolist (k '(has_sidenotes has_citations has_footnotes has_math
                                has_widgets has_video_sync))
      (unless (assq k out)
        (push (cons k nil) out)))
    out))
```

Replace with:

```elisp
    ;; Task 5: has_* flags.  Caller (publish-essay-file) injects a `:scan-plist'
    ;; key into raw-alist BEFORE calling normalize.  Merge with #+HUGO_HAS_<X>:
    ;; keyword overrides via the essays module helper.  When :scan-plist is
    ;; absent (e.g. unit tests of the normalizer alone), default all flags to nil.
    (require 'a3madkour-publish-essays)
    (let* ((scan-pl (alist-get :scan-plist raw-alist))
           (merged (if scan-pl
                       (a3madkour-pub-essays--merge-has-flags scan-pl source-file)
                     '(:has_sidenotes nil :has_citations nil :has_footnotes nil
                       :has_math nil :has_widgets nil :has_video_sync nil))))
      (setq out (assq-delete-all :scan-plist out))
      (dolist (cell a3madkour-pub-essays--has-flag-keywords)
        (let ((k (intern (substring (symbol-name (car cell)) 1))))  ; :has_x → has_x
          (setf (alist-get k out) (and (plist-get merged (car cell)) t)))))
    out))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -10`
Expected: 3 new merge-* tests PASS; Task 3 tests still pass; final line shows `0 unexpected`.

- [ ] **Step 6: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-essays.el emacs-configs/custom/lisp/a3madkour-publish-essays-test.el emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el
git commit -m "$(cat <<'EOF'
feat(b-4): has_* keyword override merge (Task 5)

#+HUGO_HAS_<X>: keyword (t/true/1/yes or nil/false/0/no, case-insensitive)
wins absolutely when set; else body-scan result determines.  Wired into
the essays normalizer via a :scan-plist key the handler injects pre-call.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6 — lastmod cascade integration check

(The 5-step cascade is already implemented in `a3madkour-pub-frontmatter/last-modified-cascade`. Task 3 wired it into the essays normalizer. This task adds explicit coverage tests; no production code changes.)

**Files:**
- Test: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests**

Append to `a3madkour-publish-frontmatter-test.el` before its `(provide ...)`:

```elisp
;; -- B.4 Task 6: lastmod cascade in essays normalizer --

(ert-deftest a3madkour-pub-frontmatter-test/essays-lastmod-from-drawer ()
  "Tier 1: :LAST_MODIFIED: drawer wins."
  (let ((tmp (make-temp-file "essays-lm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let ((out (a3madkour-pub-frontmatter/normalize
                      'essays
                      '((title . "x") (date . "2026-04-12")
                        (last_modified . "2025-01-15"))
                      tmp)))
            (should (equal (alist-get 'lastmod out) "2025-01-15"))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-frontmatter-test/essays-lastmod-from-keyword ()
  "Tier 2: HUGO_LASTMOD keyword (ISO datetime trimmed to date)."
  (let ((tmp (make-temp-file "essays-lm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let ((out (a3madkour-pub-frontmatter/normalize
                      'essays
                      '((title . "x") (date . "2026-04-12")
                        (lastmod . "2025-03-22T18:00:00+00:00"))
                      tmp)))
            (should (equal (alist-get 'lastmod out) "2025-03-22"))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-frontmatter-test/essays-lastmod-from-fs-mtime ()
  "Tier 4: drawer + keyword absent + not a git repo → fs-mtime."
  (let ((tmp (make-temp-file "essays-lm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let ((out (a3madkour-pub-frontmatter/normalize
                      'essays
                      '((title . "x") (date . "2026-04-12"))
                      tmp)))
            ;; fs-mtime is today (we just created the temp file).
            (should (string-match-p "^[0-9]\\{4\\}-[0-9]\\{2\\}-[0-9]\\{2\\}$"
                                    (alist-get 'lastmod out)))))
      (delete-file tmp))))
```

- [ ] **Step 2: Run tests to verify they pass (no code change required)**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep "essays-lastmod" | head -5`
Expected: 3 tests PASS — the cascade was wired by Task 3 already.

- [ ] **Step 3: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "$(cat <<'EOF'
test(b-4): essays lastmod cascade coverage (Task 6)

3 new tests prove the 5-step cascade fires correctly in the essays
normalizer (drawer / keyword / fs-mtime tiers).  Git-mtime + today
tiers are exercised indirectly via the underlying cascade helper's
own tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7 — Series defaults coercion tests

(Series defaults are already implemented in Task 3's normalizer skeleton — `series=""` and `series_order=0` when absent. This task locks them in with explicit tests + handles the int-coercion edge case.)

**Files:**
- Test: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests**

Append to `a3madkour-publish-frontmatter-test.el` before its `(provide ...)`:

```elisp
;; -- B.4 Task 7: series defaults --

(ert-deftest a3madkour-pub-frontmatter-test/essays-series-defaults ()
  "Absent series → empty string; absent series_order → 0."
  (let ((tmp (make-temp-file "essays-ser-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let ((out (a3madkour-pub-frontmatter/normalize
                      'essays '((title . "x") (date . "2026-04-12")) tmp)))
            (should (equal (alist-get 'series out) ""))
            (should (equal (alist-get 'series_order out) 0))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-frontmatter-test/essays-series-order-string-coerced ()
  "series_order from ox-hugo arrives as string '2' → coerce to int 2."
  (let ((tmp (make-temp-file "essays-ser-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
          (let ((out (a3madkour-pub-frontmatter/normalize
                      'essays
                      '((title . "x") (date . "2026-04-12")
                        (series . "example-series") (series_order . "2"))
                      tmp)))
            (should (equal (alist-get 'series out) "example-series"))
            (should (eq (alist-get 'series_order out) 2))))
      (delete-file tmp))))
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep "essays-series" | head -5`
Expected: 2 tests PASS.

- [ ] **Step 3: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "$(cat <<'EOF'
test(b-4): essays series defaults + int coercion (Task 7)

Locks in series='' / series_order=0 defaults and the
string-to-int coercion ox-hugo's #+HUGO_SERIES_ORDER: line round-trips
through.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8 — `publish-essay-file` pipeline

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays.el` (add the pipeline entry + render helpers)
- Test: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays-test.el`

- [ ] **Step 1: Write failing tests**

Append to `a3madkour-publish-essays-test.el` before its `(provide ...)`:

```elisp
;; -- B.4 Task 8: publish-essay-file end-to-end (stubbed) --

(ert-deftest a3madkour-pub-essays-test/publish-essay-file-writes-bundle-and-records ()
  "End-to-end stubbed: handler exports stub body, writes content/essays/<slug>/index.md,
calls record-publish with the correct URL."
  (let ((tmp-essays-dir (make-temp-file "essays-pub-src-" t))
        (tmp-site-data (make-temp-file "essays-pub-site-" t))
        (tmp-site-content (make-temp-file "essays-pub-content-" t))
        recorded)
    (unwind-protect
        (let* ((src (expand-file-name "example-one.org" tmp-essays-dir))
               (site-root (file-name-as-directory
                           (directory-file-name
                            (file-name-directory
                             (file-name-as-directory tmp-site-data)))))
               (a3madkour-pub/site-data-dir (file-name-as-directory tmp-site-data)))
          (with-temp-file src
            (insert ":PROPERTIES:\n:ID: essay-one-uuid\n:END:\n"
                    "#+title: Example essay one\n"
                    "#+date: 2026-04-12\n"
                    "#+HUGO_PUBLISH: t\n"
                    "#+HUGO_SECTION: essays\n"
                    "#+HUGO_SUMMARY: Lorem ipsum.\n"))
          (cl-letf (((symbol-function 'a3madkour-pub/note-metadata)
                     (lambda (_) (list :id "essay-one-uuid" :slug "example-one" :section "essays")))
                    ((symbol-function 'a3madkour-pub/note-slug)
                     (lambda (_) "example-one"))
                    ((symbol-function 'a3madkour-pub/note-url)
                     (lambda (_) "/essays/example-one/"))
                    ((symbol-function 'a3madkour-pub-export/export-file)
                     (lambda (_) (list :frontmatter '((title . "Example essay one")
                                                     (date . "2026-04-12")
                                                     (summary . "Lorem ipsum."))
                                       :body "Lorem ipsum body.")))
                    ((symbol-function 'a3madkour-pub/asset-validate-and-copy)
                     (lambda (&rest _) nil))
                    ((symbol-function 'a3madkour-pub-history/record-publish)
                     (lambda (id url state)
                       (setq recorded (list id url state))))
                    ((symbol-function 'a3madkour-pub-essays--site-root)
                     (lambda () site-root)))
            (a3madkour-pub-essays/publish-essay-file src))
          ;; Bundle exists.
          (should (file-exists-p (expand-file-name
                                  "content/essays/example-one/index.md" site-root)))
          ;; record-publish called with correct URL + state.
          (should (equal recorded '("essay-one-uuid" "/essays/example-one/" live)))
          ;; Body present in output.
          (let ((written (with-temp-buffer
                           (insert-file-contents
                            (expand-file-name "content/essays/example-one/index.md" site-root))
                           (buffer-string))))
            (should (string-match-p "Lorem ipsum body\\." written))
            ;; Frontmatter has all 14 required keys.
            (dolist (k '("title" "date" "lastmod" "draft" "summary" "tags"
                         "series" "series_order" "toc"
                         "has_sidenotes" "has_citations" "has_footnotes"
                         "has_math" "has_widgets" "has_video_sync"))
              (should (string-match-p (format "^%s:" k) written)))))
      (when (file-exists-p tmp-essays-dir) (delete-directory tmp-essays-dir t))
      (when (file-exists-p tmp-site-data) (delete-directory tmp-site-data t))
      (when (file-exists-p tmp-site-content) (delete-directory tmp-site-content t)))))

(ert-deftest a3madkour-pub-essays-test/publish-essay-file-injects-scan-plist ()
  "Handler scans body and threads the result into normalize via :scan-plist."
  (let ((tmp-essays-dir (make-temp-file "essays-pub-src-" t))
        (tmp-site-data (make-temp-file "essays-pub-site-" t))
        injected-raw)
    (unwind-protect
        (let* ((src (expand-file-name "example-x.org" tmp-essays-dir))
               (site-root (file-name-as-directory
                           (directory-file-name
                            (file-name-directory
                             (file-name-as-directory tmp-site-data)))))
               (a3madkour-pub/site-data-dir (file-name-as-directory tmp-site-data)))
          (with-temp-file src (insert ":PROPERTIES:\n:ID: x\n:END:\n#+title: x\n"))
          (cl-letf (((symbol-function 'a3madkour-pub/note-metadata)
                     (lambda (_) (list :id "x" :slug "x" :section "essays")))
                    ((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "x"))
                    ((symbol-function 'a3madkour-pub/note-url) (lambda (_) "/essays/x/"))
                    ((symbol-function 'a3madkour-pub-export/export-file)
                     (lambda (_) (list :frontmatter nil
                                       :body "lorem {{< sidenote >}}n{{< /sidenote >}} ipsum")))
                    ((symbol-function 'a3madkour-pub/asset-validate-and-copy) (lambda (&rest _) nil))
                    ((symbol-function 'a3madkour-pub-history/record-publish) (lambda (&rest _) nil))
                    ((symbol-function 'a3madkour-pub-frontmatter/normalize)
                     (lambda (section raw _)
                       (when (eq section 'essays) (setq injected-raw raw))
                       (or raw '())))
                    ((symbol-function 'a3madkour-pub-essays--site-root)
                     (lambda () site-root)))
            (a3madkour-pub-essays/publish-essay-file src))
          (should (assq :scan-plist injected-raw))
          (should (eq (plist-get (alist-get :scan-plist injected-raw) :has_sidenotes) t)))
      (when (file-exists-p tmp-essays-dir) (delete-directory tmp-essays-dir t))
      (when (file-exists-p tmp-site-data) (delete-directory tmp-site-data t)))))

(ert-deftest a3madkour-pub-essays-test/publish-essay-file-no-hero-still-runs-asset-copy ()
  "asset-validate-and-copy is always called (it handles per-bundle assets
generally); absence of #+HUGO_HERO does not skip it."
  (let ((tmp-essays-dir (make-temp-file "essays-pub-src-" t))
        (tmp-site-data (make-temp-file "essays-pub-site-" t))
        asset-call-count)
    (setq asset-call-count 0)
    (unwind-protect
        (let* ((src (expand-file-name "example-x.org" tmp-essays-dir))
               (site-root (file-name-as-directory
                           (directory-file-name
                            (file-name-directory
                             (file-name-as-directory tmp-site-data)))))
               (a3madkour-pub/site-data-dir (file-name-as-directory tmp-site-data)))
          (with-temp-file src (insert ":PROPERTIES:\n:ID: x\n:END:\n#+title: x\n"))
          (cl-letf (((symbol-function 'a3madkour-pub/note-metadata)
                     (lambda (_) (list :id "x" :slug "x" :section "essays")))
                    ((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "x"))
                    ((symbol-function 'a3madkour-pub/note-url) (lambda (_) "/essays/x/"))
                    ((symbol-function 'a3madkour-pub-export/export-file)
                     (lambda (_) (list :frontmatter nil :body "body")))
                    ((symbol-function 'a3madkour-pub/asset-validate-and-copy)
                     (lambda (&rest _) (cl-incf asset-call-count)))
                    ((symbol-function 'a3madkour-pub-history/record-publish) (lambda (&rest _) nil))
                    ((symbol-function 'a3madkour-pub-essays--site-root)
                     (lambda () site-root)))
            (a3madkour-pub-essays/publish-essay-file src))
          (should (= asset-call-count 1)))
      (when (file-exists-p tmp-essays-dir) (delete-directory tmp-essays-dir t))
      (when (file-exists-p tmp-site-data) (delete-directory tmp-site-data t)))))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "publish-essay-file|symbol's function|FAIL" | head -5`
Expected: 3 tests FAIL (`a3madkour-pub-essays/publish-essay-file` not defined).

- [ ] **Step 3: Add the pipeline entry + render helpers**

Append to `a3madkour-publish-essays.el` BEFORE the `(provide ...)` line:

```elisp
;; Task 8: rendering helpers (mirror garden's; future shared extraction
;; tracked as B.4 follow-up #3).

(defcustom a3madkour-pub-essays/section-dir-name "essays"
  "Hugo content section directory name for essays (relative to site root)."
  :type 'string
  :group 'a3madkour-pub)

(defun a3madkour-pub-essays--site-root ()
  "Derive the Hugo site root from `a3madkour-pub/site-data-dir'."
  (file-name-as-directory
   (directory-file-name
    (file-name-directory
     (directory-file-name
      (file-name-as-directory a3madkour-pub/site-data-dir))))))

(defun a3madkour-pub-essays--write-if-different (path content)
  "Write CONTENT to PATH only if it differs from existing on-disk content.
Returns t if a write happened, nil if no-op."
  (let ((existing (when (file-exists-p path)
                    (with-temp-buffer
                      (insert-file-contents path)
                      (buffer-string)))))
    (unless (string= existing content)
      (make-directory (file-name-directory path) t)
      (with-temp-file path (insert content))
      t)))

(defconst a3madkour-pub-essays--date-re
  "^[0-9]\\{4\\}-[0-9]\\{2\\}-[0-9]\\{2\\}$"
  "Regex for bare YYYY-MM-DD date strings (emitted unquoted in YAML).")

(defun a3madkour-pub-essays--render-yaml-value (v)
  "Render V as a YAML scalar/list value.  Same contract as garden's
helper: strings quoted; YYYY-MM-DD dates unquoted; numbers as-is;
t/nil → true/false; lists of strings → JSON-style array.

NOTE: nil is also a list in Emacs Lisp — test null BEFORE listp."
  (cond
   ((null v)    "false")
   ((eq v t)    "true")
   ((and (stringp v)
         (string-match-p a3madkour-pub-essays--date-re v))
    v)
   ((stringp v) (format "\"%s\"" v))
   ((numberp v) (format "%s" v))
   ((listp v)
    (format "[%s]"
            (mapconcat (lambda (s) (format "\"%s\"" s)) v ", ")))))

(defun a3madkour-pub-essays--render-frontmatter (alist)
  "Render ALIST as YAML frontmatter (alphabetical key order; deterministic).
Returns a string with leading/trailing `---' delimiters."
  (let ((sorted (sort (copy-sequence alist)
                      (lambda (a b)
                        (string< (symbol-name (car a)) (symbol-name (car b)))))))
    (concat "---\n"
            (mapconcat
             (lambda (cell)
               (format "%s: %s"
                       (symbol-name (car cell))
                       (a3madkour-pub-essays--render-yaml-value (cdr cell))))
             sorted "\n")
            "\n---\n")))

;; Task 8: pipeline entry.

(defun a3madkour-pub-essays/publish-essay-file (file)
  "Publish a single essay FILE to content/essays/<slug>/index.md.

Pipeline:
  1. resolve metadata (id / slug)
  2. pre-export rewrite via shared rewrite-to-tmp-file (B.4 cleanup commit)
  3. ox-hugo export
  4. scan post-export body for has_* shortcodes
  5. inject :scan-plist into raw fm; normalize via 'essays dispatch arm
  6. asset-validate-and-copy (hero.svg etc.)
  7. render frontmatter + body; write if different
  8. record-publish"
  (let* ((md         (a3madkour-pub/note-metadata file))
         (id         (plist-get md :id))
         (slug       (plist-get md :slug))
         (new-url    (a3madkour-pub/note-url file))
         (site-root  (a3madkour-pub-essays--site-root))
         (bundle-dir (expand-file-name
                      (format "content/%s/%s/"
                              a3madkour-pub-essays/section-dir-name slug)
                      site-root))
         (out-path   (expand-file-name "index.md" bundle-dir))
         (tmp-src    (a3madkour-pub-rewrite/rewrite-to-tmp-file
                      file id "a3-pub-essays"))
         (exported   (unwind-protect
                         (a3madkour-pub-export/export-file tmp-src)
                       (when (file-exists-p tmp-src)
                         (delete-file tmp-src))))
         (body       (plist-get exported :body))
         (scan-pl    (a3madkour-pub-essays--scan-has-flags (or body "")))
         (raw-fm     (cons (cons :scan-plist scan-pl)
                           (or (plist-get exported :frontmatter) '())))
         (normalized (a3madkour-pub-frontmatter/normalize 'essays raw-fm file)))
    (a3madkour-pub/asset-validate-and-copy file bundle-dir)
    (a3madkour-pub-essays--write-if-different
     out-path
     (concat (a3madkour-pub-essays--render-frontmatter normalized) (or body "")))
    (a3madkour-pub-history/record-publish id new-url 'live)))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -10`
Expected: 3 new pipeline tests PASS; all earlier tests still PASS.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-essays.el emacs-configs/custom/lisp/a3madkour-publish-essays-test.el
git commit -m "$(cat <<'EOF'
feat(b-4): publish-essay-file pipeline (Task 8)

Per-essay handler wires shared rewrite-to-tmp-file → ox-hugo export →
post-export has_* body scan → essays normalizer (with scan-plist
injected via :scan-plist key) → asset-validate-and-copy →
write-if-different → record-publish.  YAML render helpers copied from
garden; shared extraction tracked as B.4 follow-up #3.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9 — Register `'essays` handler in deliberate alist

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate.el` (require + populate handler alist)
- Test: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate-test.el`

- [ ] **Step 1: Write failing test**

Append to `a3madkour-publish-deliberate-test.el` before its `(provide ...)`:

```elisp
(ert-deftest a3madkour-pub-deliberate-test/essays-handler-registered ()
  "B.4 Task 9: 'essays is registered in the deliberate handler alist."
  (require 'a3madkour-publish-deliberate)
  (should (eq (cdr (assq 'essays a3madkour-pub-deliberate--handlers))
              'a3madkour-pub-essays/publish-essay-file)))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep "essays-handler-registered" | head -3`
Expected: FAIL (alist entry missing).

- [ ] **Step 3: Wire the require + populate the alist**

In `a3madkour-publish-deliberate.el`:

(a) After the existing `(require 'a3madkour-publish-unpublish)` line, add:

```elisp
(require 'a3madkour-publish-essays)
```

(b) Replace the `(defvar a3madkour-pub-deliberate--handlers nil ...)` block with:

```elisp
(defvar a3madkour-pub-deliberate--handlers
  '((essays . a3madkour-pub-essays/publish-essay-file))
  "Alist of (SECTION-SYMBOL . HANDLER-FUNCTION) for deliberate sections.

HANDLER-FUNCTION takes one argument (a source file path) and emits the
corresponding Hugo content + calls `record-publish'.

Same shape as `a3madkour-pub-living--handlers' but a separate registry
because some sections might exist in both (uncommon but possible).
B.4 registers `essays'; B.5 (works), B.6 (streams), B.7 (about) each
add their own entry.")
```

(c) Update the `a3-publish-deliberate` defun to call `finish-publish` with the new scope kwarg:

Find:
```elisp
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
```

Replace with:
```elisp
  (a3madkour-pub/begin-publish)
  (unwind-protect
      (let* ((file (a3madkour-pub--resolve-file-or-id file-or-id))
             (section (a3madkour-pub/note-section file))
             (handler (cdr (assq section a3madkour-pub-deliberate--handlers))))
        (unless handler
          (error "a3madkour-pub-deliberate: no handler registered for section %S (file: %s)"
                 section file))
        (funcall handler file))
    (a3madkour-pub/finish-publish :scope 'deliberate)))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -10`
Expected: new test passes; existing tests still pass.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-deliberate.el emacs-configs/custom/lisp/a3madkour-publish-deliberate-test.el
git commit -m "$(cat <<'EOF'
feat(b-4): register essays handler in deliberate alist (Task 9)

Wires 'essays → a3madkour-pub-essays/publish-essay-file.  Also threads
:scope 'deliberate through to finish-publish so the first deliberate
run doesn't catastrophically unpublish other bundles.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10 — `a3-pub.sh` `-l a3madkour-publish-essays` wire-up

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` (two exec blocks: `--publish-deliberate` and the default exec — both load handler libs)

- [ ] **Step 1: Add `-l a3madkour-publish-essays` to the --publish-deliberate exec**

In `a3-pub.sh`, find the `--publish-deliberate` exec block (around lines 144-169) and add `-l a3madkour-publish-essays` after the existing `-l a3madkour-publish-research \`:

```bash
    -l a3madkour-publish-garden \
    -l a3madkour-publish-library \
    -l a3madkour-publish-research \
    -l a3madkour-publish-essays \
    --eval "(setq a3madkour-pub/site-data-dir \"$SITE_DATA_DIR\")" \
```

- [ ] **Step 2: Add `-l a3madkour-publish-essays` to the default exec**

In `a3-pub.sh`, find the default exec block at the very end (around lines 178-198) and add `-l a3madkour-publish-essays` after `-l a3madkour-publish-research \`:

```bash
  -l a3madkour-publish-garden \
  -l a3madkour-publish-library \
  -l a3madkour-publish-research \
  -l a3madkour-publish-essays \
  --eval "(message \"[a3-pub] ready (v%s)\" a3madkour-pub/version)" \
```

(Do NOT add it to the `--publish-living` block — essays are deliberate-only.)

- [ ] **Step 3: Smoke-test the wrapper**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --eval "(message \"%s\" (boundp 'a3madkour-pub-essays/publish-essay-file))" 2>&1 | tail -5`
Expected: prints `t` (or at minimum prints `[a3-pub] ready (vN)` without errors).

- [ ] **Step 4: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3-pub.sh
git commit -m "$(cat <<'EOF'
feat(b-4): a3-pub.sh wires the essays handler module (Task 10)

Adds -l a3madkour-publish-essays to --publish-deliberate and default
exec blocks.  Skips --publish-living per spec §3.6 (essays are
deliberate-only).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11 — Integration: publish-once

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Inspect the existing TestResearchPublishLiving pattern**

Run: `grep -n "class TestResearchPublishLiving\|def test_research_theme_publish_once\|def _run_publish\|_seed_site_root\|_seed_research_theme_file" /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py | head -20`
Note line numbers — Task 11 mirrors this pattern for essays.

- [ ] **Step 2: Append the new TestEssaysPublishDeliberate scaffold + test_essay_publish_once**

Append before `if __name__ == "__main__":` (or at the end if the file lacks that block):

```python
class TestEssaysPublishDeliberate(unittest.TestCase):
    """B.4 integration tests: publish-deliberate for essays."""

    def setUp(self) -> None:
        self.tmp_root = tempfile.mkdtemp(prefix="a3-pub-essays-int-")
        self.essays_dir = os.path.join(self.tmp_root, "org", "essays")
        os.makedirs(self.essays_dir, exist_ok=True)
        self.site_root = os.path.join(self.tmp_root, "site")
        os.makedirs(os.path.join(self.site_root, "data"), exist_ok=True)
        os.makedirs(os.path.join(self.site_root, "content", "essays"), exist_ok=True)
        # Seed empty manifest so begin-publish reads cleanly.
        with open(os.path.join(self.site_root, "data", "url-history.yaml"), "w") as f:
            f.write("manifest_version: 1\nnotes: []\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _seed_essay(self, slug: str, body: str, extra_keywords: str = "") -> str:
        path = os.path.join(self.essays_dir, f"{slug}.org")
        content = (
            ":PROPERTIES:\n"
            f":ID:       {slug}-uuid\n"
            ":END:\n"
            f"#+title: {slug.replace('-', ' ').title()}\n"
            "#+date: 2026-04-12\n"
            "#+HUGO_PUBLISH: t\n"
            "#+HUGO_SECTION: essays\n"
            f"{extra_keywords}"
            "\n"
            f"{body}\n"
        )
        with open(path, "w") as f:
            f.write(content)
        return path

    def _run_publish_deliberate(self, path: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["A3_PUB_SITE_DATA_DIR"] = os.path.join(self.site_root, "data")
        wrapper = os.path.expanduser(
            "~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh")
        return subprocess.run(
            [wrapper, "--publish-deliberate", path],
            env=env, capture_output=True, text=True, timeout=120)

    def test_essay_publish_once(self) -> None:
        """B.4 Task 11: one source → bundle written + manifest updated."""
        src = self._seed_essay("example-one", "Lorem ipsum body.")
        result = self._run_publish_deliberate(src)
        self.assertEqual(result.returncode, 0,
                         f"stderr: {result.stderr}\nstdout: {result.stdout}")
        bundle = os.path.join(self.site_root, "content", "essays", "example-one",
                              "index.md")
        self.assertTrue(os.path.exists(bundle), f"bundle missing: {bundle}")
        with open(bundle) as f:
            content = f.read()
        for required in ("title:", "date:", "lastmod:", "draft:",
                         "series:", "series_order:", "toc:",
                         "has_sidenotes:", "has_citations:",
                         "has_footnotes:", "has_math:",
                         "has_widgets:", "has_video_sync:"):
            self.assertIn(required, content,
                          f"required key missing: {required}")
        self.assertIn("Lorem ipsum body.", content)
        # Manifest entry exists.
        with open(os.path.join(self.site_root, "data", "url-history.yaml")) as f:
            manifest_text = f.read()
        self.assertIn("/essays/example-one/", manifest_text)
```

The test file already imports `os`, `shutil`, `subprocess`, `tempfile`, `unittest` at the top — verify with the grep step. If `unittest` is not imported, also add `import unittest`.

- [ ] **Step 3: Run the test to verify it fails (no handler yet wired up via wrapper)**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration.TestEssaysPublishDeliberate.test_essay_publish_once -v 2>&1 | tail -20`

Expected at this point: PASS (tasks 1-10 are complete, so the wrapper is wired). If FAIL, debug per `result.stderr` printed by the test.

- [ ] **Step 4: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
git commit -m "$(cat <<'EOF'
test(b-4): integration — essays publish-once (Task 11)

TestEssaysPublishDeliberate scaffold + first test.  Seeds tmp
~/org/essays/-shaped corpus, invokes publish-deliberate via the
emacs --batch wrapper, asserts bundle landed at correct path and
all 14 required frontmatter keys present.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12 — Integration: idempotency

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Append the test**

Append to the `TestEssaysPublishDeliberate` class:

```python
    def test_essay_publish_idempotent(self) -> None:
        """B.4 Task 12: second publish on unchanged source → zero file diff."""
        src = self._seed_essay("example-one", "Lorem ipsum body.")
        first = self._run_publish_deliberate(src)
        self.assertEqual(first.returncode, 0, first.stderr)
        bundle = os.path.join(self.site_root, "content", "essays",
                              "example-one", "index.md")
        with open(bundle) as f:
            first_content = f.read()
        first_mtime = os.path.getmtime(bundle)
        # Sleep briefly so mtime would tick if a write happened.
        import time
        time.sleep(1.1)
        second = self._run_publish_deliberate(src)
        self.assertEqual(second.returncode, 0, second.stderr)
        with open(bundle) as f:
            second_content = f.read()
        self.assertEqual(first_content, second_content,
                         "second publish produced a different file")
        self.assertEqual(first_mtime, os.path.getmtime(bundle),
                         "second publish bumped mtime — write-if-different broke")
```

- [ ] **Step 2: Run the test**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration.TestEssaysPublishDeliberate.test_essay_publish_idempotent -v 2>&1 | tail -10`
Expected: PASS.

- [ ] **Step 3: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
git commit -m "$(cat <<'EOF'
test(b-4): integration — essays publish idempotent (Task 12)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13 — Integration: slug-shift (deliberate-scoped Step B)

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Append the test**

Append to the `TestEssaysPublishDeliberate` class:

```python
    def test_essay_slug_shift(self) -> None:
        """B.4 Task 13: title change → finish-publish Step B (deliberate-scoped)
        renames asset dir + rewrites referring source links + deletes old bundle."""
        src = self._seed_essay("example-one", "Lorem ipsum body.")
        first = self._run_publish_deliberate(src)
        self.assertEqual(first.returncode, 0, first.stderr)
        old_bundle = os.path.join(self.site_root, "content", "essays",
                                  "example-one", "index.md")
        self.assertTrue(os.path.exists(old_bundle))
        # Edit the source: change the title (changes the slug).
        with open(src) as f:
            content = f.read()
        new_content = content.replace("#+title: Example One",
                                      "#+title: Example One Renamed")
        with open(src, "w") as f:
            f.write(new_content)
        second = self._run_publish_deliberate(src)
        self.assertEqual(second.returncode, 0, second.stderr)
        new_bundle = os.path.join(self.site_root, "content", "essays",
                                  "example-one-renamed", "index.md")
        self.assertTrue(os.path.exists(new_bundle),
                        f"new bundle missing: {new_bundle}")
        self.assertFalse(os.path.exists(old_bundle),
                         f"old bundle still exists: {old_bundle}")
```

- [ ] **Step 2: Run the test**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration.TestEssaysPublishDeliberate.test_essay_slug_shift -v 2>&1 | tail -15`
Expected: PASS.

- [ ] **Step 3: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
git commit -m "$(cat <<'EOF'
test(b-4): integration — essays slug-shift (Task 13)

Title change triggers finish-publish :scope 'deliberate Step B —
asset dir rename + old bundle delete.  Validates the deliberate
scope narrows to the touched id without affecting other sections.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14 — Integration: deliberate-doesn't-touch-other-sections

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Append the test**

Append to the `TestEssaysPublishDeliberate` class:

```python
    def test_essay_deliberate_does_not_touch_other_sections(self) -> None:
        """B.4 Task 14: seed manifest with garden + essay entries; publish-deliberate
        the essay; assert garden bundle untouched and no 'removed state changes."""
        # Seed manifest with a pre-existing garden entry.
        manifest_path = os.path.join(self.site_root, "data", "url-history.yaml")
        with open(manifest_path, "w") as f:
            f.write(
                "manifest_version: 1\n"
                "notes:\n"
                "  - id: garden-a-uuid\n"
                "    current_url: /garden/note-a/\n"
                "    state: live\n"
                "    aliases: []\n"
            )
        # Seed a fake garden bundle on disk.
        garden_bundle_dir = os.path.join(self.site_root, "content", "garden", "note-a")
        os.makedirs(garden_bundle_dir, exist_ok=True)
        garden_bundle = os.path.join(garden_bundle_dir, "index.md")
        with open(garden_bundle, "w") as f:
            f.write("---\ntitle: note-a\n---\nbody\n")
        # Publish a fresh essay.
        src = self._seed_essay("example-one", "Lorem ipsum body.")
        result = self._run_publish_deliberate(src)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Garden bundle still exists.
        self.assertTrue(os.path.exists(garden_bundle),
                        "deliberate publish wrongly deleted unrelated garden bundle")
        # Manifest still has the garden entry as live.
        with open(manifest_path) as f:
            manifest_text = f.read()
        self.assertIn("garden-a-uuid", manifest_text)
        self.assertIn("/garden/note-a/", manifest_text)
        # And the essay entry was added.
        self.assertIn("/essays/example-one/", manifest_text)
```

- [ ] **Step 2: Run the test**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration.TestEssaysPublishDeliberate.test_essay_deliberate_does_not_touch_other_sections -v 2>&1 | tail -15`
Expected: PASS.

- [ ] **Step 3: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
git commit -m "$(cat <<'EOF'
test(b-4): integration — deliberate skips foreign sections (Task 14)

Proves :scope 'deliberate Step A skip works end-to-end: a pre-seeded
garden bundle survives a deliberate essay publish unchanged.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15 — Integration: has_* scan + override + linter parity

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Append three tests**

Append to the `TestEssaysPublishDeliberate` class:

```python
    def test_essay_has_flags_scan_detects_each_shortcode(self) -> None:
        """B.4 Task 15a: each has_* shortcode pattern → flag emitted true."""
        patterns = [
            ("sidenotes",  "{{< sidenote >}}n{{< /sidenote >}}", "has_sidenotes"),
            ("citations",  "{{< cite \"k\" >}}",                  "has_citations"),
            ("footnotes",  "lorem[^1] ipsum\n\n[^1]: note",       "has_footnotes"),
            ("math",       "{{< math >}}\\alpha{{< /math >}}",    "has_math"),
            ("widgets",    "{{< widget src=\"x\" >}}",            "has_widgets"),
            ("video-sync", "{{< video-sync src=\"x.mp4\" >}}",    "has_video_sync"),
        ]
        for slug, body, flag in patterns:
            with self.subTest(flag=flag):
                src = self._seed_essay(f"example-{slug}", body)
                result = self._run_publish_deliberate(src)
                self.assertEqual(result.returncode, 0,
                                 f"{slug}: {result.stderr}")
                bundle = os.path.join(self.site_root, "content", "essays",
                                      f"example-{slug}", "index.md")
                with open(bundle) as f:
                    content = f.read()
                self.assertIn(f"{flag}: true", content,
                              f"expected {flag}: true for {slug}\n{content}")

    def test_essay_has_keyword_override_wins(self) -> None:
        """B.4 Task 15b: #+HUGO_HAS_SIDENOTES: nil beats positive scan."""
        src = self._seed_essay(
            "example-override",
            "{{< sidenote >}}n{{< /sidenote >}}",
            extra_keywords="#+HUGO_HAS_SIDENOTES: nil\n")
        result = self._run_publish_deliberate(src)
        self.assertEqual(result.returncode, 0, result.stderr)
        bundle = os.path.join(self.site_root, "content", "essays",
                              "example-override", "index.md")
        with open(bundle) as f:
            content = f.read()
        self.assertIn("has_sidenotes: false", content)

    def test_essay_yaml_passes_site_linter(self) -> None:
        """B.4 Task 15c: B-emitted bundle passes tools/check_fixtures.py."""
        src = self._seed_essay("example-linter",
                               "Lorem ipsum.",
                               extra_keywords="#+HUGO_SUMMARY: S\n")
        result = self._run_publish_deliberate(src)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Point check_fixtures.py at our tmp site root.
        env = os.environ.copy()
        env["CONTENT_DIR"] = os.path.join(self.site_root, "content")
        linter = subprocess.run(
            ["python3",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "check_fixtures.py"),
             os.path.join(self.site_root, "content", "essays")],
            env=env, capture_output=True, text=True)
        self.assertEqual(linter.returncode, 0,
                         f"linter failed:\nstdout: {linter.stdout}\n"
                         f"stderr: {linter.stderr}")
```

(If `check_fixtures.py` does not accept a positional content-dir argument, replace the linter invocation with: `subprocess.run(["python3", "tools/check_fixtures.py"], cwd=self.site_root, ...)`. Inspect `tools/check_fixtures.py:1-30` first to confirm its invocation contract.)

- [ ] **Step 2: Inspect check_fixtures.py to confirm invocation**

Run: `head -40 /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/check_fixtures.py`
If the script uses `argparse` with a directory arg → keep Step 1's invocation. If it reads relative paths from CWD → switch to the `cwd=` form per the note above.

- [ ] **Step 3: Run the 3 tests**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration.TestEssaysPublishDeliberate.test_essay_has_flags_scan_detects_each_shortcode tools.test_publish_integration.TestEssaysPublishDeliberate.test_essay_has_keyword_override_wins tools.test_publish_integration.TestEssaysPublishDeliberate.test_essay_yaml_passes_site_linter -v 2>&1 | tail -25`
Expected: all 3 PASS.

- [ ] **Step 4: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
git commit -m "$(cat <<'EOF'
test(b-4): integration — has_* scan + override + linter parity (Task 15)

Three integration tests: (1) each of 6 has_* shortcode patterns
flips its frontmatter flag to true; (2) #+HUGO_HAS_SIDENOTES: nil
beats positive scan; (3) B-emitted bundle passes the site's
check_fixtures.py contract.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 16 — Real-corpus spot-check (manual)

This task does not produce code; it produces author confidence and may surface fix-up commits.

**Files:**
- Create: `~/org/essays/example-one.org` (kitchen-sink stub — see spec §6.3 template)
- Create: `~/org/essays/example-two.org` (series part 2 of "example-series")
- Create: `~/org/essays/example-three.org` (minimal)
- Create: `~/org/essays/example-four.org` (has_* override demo)
- Create: `~/org/essays/assets/<example-one-uuid>/hero.svg` (hand-drawn SVG; placeholder OK)

- [ ] **Step 1: Author creates the 4 stub `.org` files**

The reference template for `example-one.org` is in `docs/superpowers/specs/2026-05-31-phase-3-b-4-essays-handler-design.md` §6.3.

`example-two.org` is the same shape minus hero/featured/code blocks and with:
```
#+HUGO_SERIES: example-series
#+HUGO_SERIES_ORDER: 2
```

`example-three.org` is bare: just title, date, HUGO_PUBLISH, HUGO_SECTION, HUGO_SUMMARY, and a body of `Lorem ipsum.`

`example-four.org` has a body with `{{< sidenote >}}…{{< /sidenote >}}` AND the header line `#+HUGO_HAS_SIDENOTES: nil`.

- [ ] **Step 2: Run publish-deliberate on each stub**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate ~/org/essays/example-one.org
/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate ~/org/essays/example-two.org
/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate ~/org/essays/example-three.org
/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate ~/org/essays/example-four.org
```

- [ ] **Step 3: Run the linter**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_fixtures.py`
Expected: exit 0 (no fixture-shape errors on any of the 4 new bundles).

- [ ] **Step 4: Verify on the dev server**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
hugo server --buildDrafts
```

Open these in a browser and confirm:
- `/essays/` shows the 4 new bundles in the bento grid.
- `/essays/example-one/` renders with hero.svg, TOC (level-4 nesting), sidenotes, citations, footnotes, figures, code blocks, math placeholder, widget placeholder, video-sync placeholder.
- `/essays/example-two/` renders and shows series-nav "Part 2 of 2 of example-series" with prev link to example-one.
- `/essays/example-three/` renders bare.
- `/essays/example-four/` renders WITH the sidenote shortcode visible (since the partial is unconditional) but frontmatter shows `has_sidenotes: false` (curl the page source to verify).

- [ ] **Step 5: Verify idempotency + scope**

Run each `--publish-deliberate` invocation a second time; `git status` should show only the new manifest entries and the 4 new bundles, no rogue changes.

- [ ] **Step 6: File any fix-up commits as needed**

If the spot-check surfaces issues (R1 / R2 from the spec — widget/video-sync pass-through OR layout regression), land fix-up commits with `fix(b-4): <one-line>` and re-run Steps 2-5.

- [ ] **Step 7: Stop the dev server before the next task**

Kill the `hugo server` process per [[reference_hugo_dev_server_gotcha]] — the production build coming in CI will fail with an active dev server.

---

## Task 17 — Fixture retirement + final commit

**Files:**
- Delete: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-essay-one/` (whole dir)
- Delete: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-essay-two/`
- Delete: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-essay-three/`
- Delete: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-figures-essay/`
- Delete: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-series-part-1/`
- Delete: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-series-part-2/`
- Delete: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-deep-toc-essay/`

- [ ] **Step 1: Run `tools/ci-local.sh` BEFORE deleting fixtures**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && tools/ci-local.sh 2>&1 | tail -20`
Expected: PASS. This baselines the state with both old fixtures + new B-emitted bundles present.

- [ ] **Step 2: Delete the 7 hand-authored fixture bundles**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
rm -rf content/essays/example-essay-one \
       content/essays/example-essay-two \
       content/essays/example-essay-three \
       content/essays/example-figures-essay \
       content/essays/example-series-part-1 \
       content/essays/example-series-part-2 \
       content/essays/example-deep-toc-essay
```

- [ ] **Step 3: Run `tools/ci-local.sh` after deletion**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && tools/ci-local.sh 2>&1 | tail -20`
Expected: PASS — the 4 B-emitted bundles satisfy all 50 linter steps, the Hugo build, and LHCI.

If any step fails, this is the spot to fix the underlying B emission (NOT to add a special-case linter exclusion). Iterate on the handler / normalizer / scanner until ci-local goes green.

- [ ] **Step 4: Stage + commit the fixture retirement + the spot-check spot-check artifacts**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add -A content/essays/
git commit -m "$(cat <<'EOF'
feat(b-4): essays publisher ships — fixture handover (Task 17)

7 hand-authored essay fixtures retired (example-essay-{one,two,three},
example-figures-essay, example-series-part-{1,2}, example-deep-toc-essay).
Replaced by 4 B-emitted bundles from ~/org/essays/example-{one,two,three,four}.org.
example-one is the kitchen sink (every has_* shortcode + hero +
featured + series + level-4 TOC + figures + code); example-two pairs
the series; example-three is the minimal negative case; example-four
demos the #+HUGO_HAS_<X>: keyword override.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Run ert + integration test totals**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -3`
Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration 2>&1 | tail -5`

Expected end state: `Ran 393 tests, 393 results as expected, 0 unexpected` (ert) and `Ran 33 tests in <Ns>` `OK` (integration).

(The exact counts may differ by a handful if you added incidental tests during fix-ups — the important properties are all-green and the +37 ert / +7 integration deltas.)

---

## Spec coverage check

Mapping each spec requirement to a task:

| Spec section | Coverage |
|---|---|
| §1 — Goals & non-goals | Tasks 1-17 collectively |
| §2 — Module structure (new + modified files) | Tasks 1, 3, 4, 5, 8, 9, 10 |
| §3 — Source-side contract (location, asymmetric refs, frontmatter mapping) | Tasks 1, 3, 5, 6, 7, 8, 16 |
| §4 — finish-publish `:scope` kwarg | Task 2 |
| §5 — Essays handler module + has_* scanner + normalizer + ert tests | Tasks 3-8 |
| §6 — Integration tests + stub source files + fixture retirement | Tasks 11-17 |
| §7 — Task ordering + spot-check checklist | Plan order + Task 16 |
| §8 — Open questions + follow-ups (R1-R3 risks) | Task 16 catches R1 + R2; Task 2's living-default test gates R3 |
