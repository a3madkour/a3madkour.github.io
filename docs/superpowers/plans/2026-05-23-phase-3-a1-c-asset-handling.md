# Phase 3 A.1.c — Asset Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Session policy default (mirrors A.1.a + A.1.b):** stage files with `git add` but do NOT git-commit autonomously. Final task surfaces suggested commit messages for the author. If the author signals "commit as you go" at session start, switch to per-task commits.

**Goal:** Replace A.1.b's `:pending-asset` rewriter stub with real asset-link handling — canonical-root resolution, cross-namespace validation, auto-remediation (default ON, with `--dry-run`), per-bundle asset copy + stale cleanup, `<img>`/`<a>` HTML emission with the new `--html-escape` helper applied. Land the 24th linter pair (`tools/check_org_assets.py` + sibling). Retrofit A.1.b's three existing `:html` emit points through the new escape helper. All TDD.

**Architecture:** One new dotfiles module (`a3madkour-publish-assets.el`) for canonical-root resolution + remediation + copy + cleanup. The escape helper (`a3madkour-pub--html-escape`) lives in `a3madkour-publish-rewrite.el` (where 3 of 4 existing emit points are). The `:pending-asset` dispatcher branch in `rewrite-link` becomes a call to `a3madkour-pub/rewrite-asset-link`. The Python linter walks `content/<section>/<slug>/` bundles + `static/notes-shared/` and verifies every `<img src>` / `<a href>` resolves + flags orphans. Integration test lands at last (`tools/test_publish_integration.py` — was a §11 placeholder until now).

**Tech Stack:** Emacs 30.2 + ert (built-in) + yaml.el + org-roam (A.1.b deps) + bash test runner; Python 3 stdlib for the linter pair + integration orchestrator.

**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §6, §7, §10, §11, §12.

**Design doc (this slice):** `docs/superpowers/specs/2026-05-23-phase-3-a1-c-asset-handling-design.md`.

**Prior plan:** `docs/superpowers/plans/2026-05-20-phase-3-a1-b-link-rewriter.md` (A.1.b — 109 ert tests green at start of A.1.c).

**Carry-forward memory:** `memory/project_a1b_complete.md` + `memory/project_next_slice.md`.

---

## File Structure

**Created (dotfiles repo):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el` — asset resolution + auto-remediation + copy + cleanup
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

**Created (site repo):**
- `tools/check_org_assets.py` — 24th linter (bundle-tree walker)
- `tools/test_check_org_assets.py` — sibling test
- `tools/test_publish_integration.py` — end-to-end fixture runner (spec §11 placeholder; lands at last in A.1.c)

**Modified (dotfiles repo):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el` — add `--html-escape` helper; retrofit 3 existing `:html` emit points (id-link ~line 176; typed-link ~line 237; external ~line 275); replace `:pending-asset` dispatcher branch with a call to `a3madkour-pub/rewrite-asset-link`.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el` — +5 escape-helper regression tests; +3 rewrite-link asset-branch integration tests.

**Modified (site repo):**
- `.github/workflows/hugo.yaml` — register `check_org_assets.py` + sibling test after the existing 23 linter pairs.
- `tools/ci-local.sh` — register same locally.
- `CLAUDE.md` — bump linter count 23→24; note A.1.c shipped; update next-slice pointer.

**Out of scope** (deferred to A.1.d / A.2):
- Slug-shift asset directory rename (A.1.d).
- Shared-asset conflict resolution when out-of-root same file is linked from multiple notes (A.1.d).
- `--strict` flag plumbing (A.2 per parent spec §6).
- `.publish-state` sidecar / whitelist cleanup (revisit in A.1.d if hand-curated bundle additions become a workflow need).

**Test count progression:** baseline 109 (end of A.1.b). Per-task targets are noted at the end of each task. Final target ≈ **173 ert tests** at end of A.1.c.

---

### Task 1: Add `--html-escape` helper (foundation for retrofit + new emits)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- --html-escape helper --

(ert-deftest a3madkour-pub-rewrite-test/html-escape-ampersand ()
  "& → &amp;."
  (should (equal (a3madkour-pub--html-escape "a & b") "a &amp; b")))

(ert-deftest a3madkour-pub-rewrite-test/html-escape-angle-brackets ()
  "< and > escape."
  (should (equal (a3madkour-pub--html-escape "<x>") "&lt;x&gt;")))

(ert-deftest a3madkour-pub-rewrite-test/html-escape-double-quote ()
  "\" → &quot;."
  (should (equal (a3madkour-pub--html-escape "say \"hi\"")
                 "say &quot;hi&quot;")))

(ert-deftest a3madkour-pub-rewrite-test/html-escape-apostrophe ()
  "' → &#39;."
  (should (equal (a3madkour-pub--html-escape "it's") "it&#39;s")))

(ert-deftest a3madkour-pub-rewrite-test/html-escape-all-five ()
  "& must be escaped FIRST to avoid double-escaping the &lt; chain."
  (should (equal (a3madkour-pub--html-escape "<a href=\"&\">'</a>")
                 "&lt;a href=&quot;&amp;&quot;&gt;&#39;&lt;/a&gt;")))

(ert-deftest a3madkour-pub-rewrite-test/html-escape-empty ()
  "Empty string passes through."
  (should (equal (a3madkour-pub--html-escape "") "")))

(ert-deftest a3madkour-pub-rewrite-test/html-escape-nil-coerces-to-empty ()
  "nil input → empty string (defensive; some callers pass nil through)."
  (should (equal (a3madkour-pub--html-escape nil) "")))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 7 failures with "Symbol's function definition is void: a3madkour-pub--html-escape".

- [ ] **Step 3: Implement the helper**

Add to `a3madkour-publish-rewrite.el` (place it BEFORE the existing `a3madkour-pub--parse-org-link` function — utility comes first):

```elisp
(defun a3madkour-pub--html-escape (s)
  "Escape `&', `<', `>', `\"', `'' in S for HTML attribute + element-body context.

This is the single chokepoint for HTML escaping in the publish-rewrite
+ publish-assets modules.  Per parent spec §6 (HTML escaping contract),
every `:html' emit's interpolated values route through this helper.

`&' is escaped FIRST to avoid double-encoding the other entities'
ampersands.  Returns the empty string when S is nil (defensive; some
upstream parsers may pass nil)."
  (if (or (null s) (string-empty-p s))
      ""
    (let ((out s))
      ;; Order matters: & must come first.
      (setq out (replace-regexp-in-string "&" "&amp;" out t t))
      (setq out (replace-regexp-in-string "<" "&lt;" out t t))
      (setq out (replace-regexp-in-string ">" "&gt;" out t t))
      (setq out (replace-regexp-in-string "\"" "&quot;" out t t))
      (setq out (replace-regexp-in-string "'" "&#39;" out t t))
      out)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 116 tests, 116 results as expected, 0 unexpected` (109 baseline + 7 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 1: **116 ert tests** (109 → 116).

---

### Task 2: Retrofit emit point #1 — id-link (`a3madkour--rewrite-id-link`)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el` (around line 176)
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write the failing regression tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- id-link emit escape retrofit --

(ert-deftest a3madkour-pub-rewrite-test/id-link-display-text-escaped ()
  "Display text containing < > & gets escaped in the rendered anchor."
  (cl-letf (((symbol-function 'a3madkour-pub/published-p)
             (lambda (_) 'live))
            ((symbol-function 'a3madkour-pub/note-url)
             (lambda (_) "/garden/x/")))
    (let* ((uuid "00000000-0000-0000-0000-000000000001")
           (link (format "[[id:%s][a < b & c > d]]" uuid))
           (result (a3madkour-pub/rewrite-link link "src")))
      (should (equal (plist-get result :html)
                     "<a href=\"/garden/x/\">a &lt; b &amp; c &gt; d</a>")))))

(ert-deftest a3madkour-pub-rewrite-test/id-link-href-with-quote-escaped ()
  "Resolved URL containing \" (pathological) gets &quot; in href context."
  (cl-letf (((symbol-function 'a3madkour-pub/published-p)
             (lambda (_) 'live))
            ((symbol-function 'a3madkour-pub/note-url)
             (lambda (_) "/garden/odd\"slug/")))
    (let* ((uuid "00000000-0000-0000-0000-000000000002")
           (link (format "[[id:%s][text]]" uuid))
           (result (a3madkour-pub/rewrite-link link "src")))
      (should (string-match-p "href=\"/garden/odd&quot;slug/\""
                              (plist-get result :html))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 2 failures — id-link emit still produces raw `<` `&` `>` in the anchor.

- [ ] **Step 3: Apply the retrofit**

In `a3madkour-publish-rewrite.el`, find the existing emit line (around line 176 — last line of the `t` branch of the `cond` inside `a3madkour-pub--rewrite-id-link`):

```elisp
;; OLD:
(list :html (format "<a href=\"%s\">%s</a>" href display)
      :warnings warnings)
```

Replace with:

```elisp
;; NEW:
(list :html (format "<a href=\"%s\">%s</a>"
                    (a3madkour-pub--html-escape href)
                    (a3madkour-pub--html-escape display))
      :warnings warnings)
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 118 tests, 118 results as expected, 0 unexpected` (116 + 2 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 2: **118 ert tests** (116 → 118).

---

### Task 3: Retrofit emit point #2 — typed-link wrapper (verify class injection preserves escape)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

The typed-link wrapper builds on id-link's already-formatted HTML and injects a class via `replace-regexp-in-string`. Once id-link is escape-retrofitted (Task 2), typed-link inherits escaping for free. We add a regression test to lock that in.

- [ ] **Step 1: Write the failing regression test**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- typed-link emit (class inheritance from id-link) --

(ert-deftest a3madkour-pub-rewrite-test/typed-link-display-text-escaped ()
  "Class injection MUST preserve the escape applied by id-link's emit."
  (cl-letf (((symbol-function 'a3madkour-pub/published-p)
             (lambda (_) 'live))
            ((symbol-function 'a3madkour-pub/note-url)
             (lambda (_) "/garden/y/")))
    (let* ((uuid "00000000-0000-0000-0000-000000000003")
           (link (format "[[supports:%s][a < b]]" uuid))
           (result (a3madkour-pub/rewrite-link link "src")))
      (should (equal (plist-get result :html)
                     "<a class=\"link-supports\" href=\"/garden/y/\">a &lt; b</a>")))))
```

- [ ] **Step 2: Run, verify pass (already passes due to Task 2's retrofit)**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 119 tests, 119 results as expected, 0 unexpected`.

Note: this is a "verify-only" task. No code change needed because typed-link reuses id-link's emit. If the test fails, investigate — it means typed-link is NOT reusing id-link's output as expected.

- [ ] **Step 3: Test-count checkpoint**

End of Task 3: **119 ert tests** (118 → 119).

---

### Task 4: Retrofit emit point #3 — external-link branch in `rewrite-link`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el` (around line 275)
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write the failing regression tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- external link emit escape retrofit --

(ert-deftest a3madkour-pub-rewrite-test/external-link-display-text-escaped ()
  "External link display text with < > & escapes properly."
  (let ((result (a3madkour-pub/rewrite-link
                 "[[https://example.com/x][a & b]]" "src")))
    (should (equal (plist-get result :html)
                   "<a href=\"https://example.com/x\">a &amp; b</a>"))))

(ert-deftest a3madkour-pub-rewrite-test/external-link-href-with-amp-escaped ()
  "URL with & in querystring escapes to &amp; in href."
  (let ((result (a3madkour-pub/rewrite-link
                 "[[https://example.com/?a=1&b=2][text]]" "src")))
    (should (equal (plist-get result :html)
                   "<a href=\"https://example.com/?a=1&amp;b=2\">text</a>"))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 2 failures — external link still emits raw `&` in href.

- [ ] **Step 3: Apply the retrofit**

In `a3madkour-publish-rewrite.el`, find the external-link branch (around line 275 inside `rewrite-link`'s `cond`):

```elisp
;; OLD:
((a3madkour-pub--external-scheme-p scheme)
 (list :html (format "<a href=\"%s\">%s</a>" path text)
       :warnings nil))
```

Replace with:

```elisp
;; NEW:
((a3madkour-pub--external-scheme-p scheme)
 (list :html (format "<a href=\"%s\">%s</a>"
                     (a3madkour-pub--html-escape path)
                     (a3madkour-pub--html-escape text))
       :warnings nil))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 121 tests, 121 results as expected, 0 unexpected` (119 + 2 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 4: **121 ert tests** (119 → 121). Escape-helper retrofit complete for all 3 A.1.b emit points.

---

### Task 5: Create `a3madkour-publish-assets.el` skeleton + defcustoms + test file

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Create the skeleton module**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`:

```elisp
;;; a3madkour-publish-assets.el --- Asset link handling for org-mode publish -*- lexical-binding: t; -*-

;;; Commentary:

;; Implements parent-spec §7 (asset handling) for A.1.c.  Replaces the
;; `:pending-asset' stub shipped in A.1.b's `rewrite-link' dispatcher.
;;
;; Public API:
;;   - `a3madkour-pub/rewrite-asset-link'      ; called by rewrite-link
;;   - `a3madkour-pub/asset-validate-and-copy' ; called by B's per-section publisher

;;; Code:

(require 'cl-lib)
(require 'a3madkour-publish)
(require 'a3madkour-publish-rewrite)         ; for --html-escape

(defgroup a3madkour-pub-assets nil
  "Asset link handling for the a3madkour-publish library."
  :group 'a3madkour-pub)

(defcustom a3madkour-pub-canonical-asset-root
  "~/org/notes/assets"
  "Root directory for canonical assets.  Two sub-folders below:
  page/<note-slug>/   — per-note assets (copied into the bundle)
  shared/             — assets referenced by many notes (one copy site-wide
                        in static/notes-shared/)

See parent spec §7."
  :type 'directory
  :group 'a3madkour-pub-assets)

(defcustom a3madkour-pub-asset-image-extensions
  '("png" "jpg" "jpeg" "gif" "svg" "webp" "avif")
  "Extensions classified as images.

Image-classified assets render as `<img src alt>'; other extensions
render as `<a href>text</a>'.  Unknown extensions fall through to the
link form (safest default)."
  :type '(repeat string)
  :group 'a3madkour-pub-assets)

(defcustom a3madkour-pub-asset-auto-remediate t
  "When non-nil (default), out-of-canonical-root assets are git-mv'd
into `<root>/page/<source-slug>/' and the .org source link is rewritten.
When nil, out-of-root assets emit `(missing asset: X)' + WARN.

Per parent spec §7 §Auto-remediation."
  :type 'boolean
  :group 'a3madkour-pub-assets)

(defcustom a3madkour-pub-notes-shared-static-dir
  nil
  "Absolute path to the site repo's `static/notes-shared/' directory.

Set explicitly by the publish driver (must be non-nil at publish time).
Shared assets are copied here once site-wide."
  :type '(choice (const :tag "Unset" nil) directory)
  :group 'a3madkour-pub-assets)

(provide 'a3madkour-publish-assets)

;;; a3madkour-publish-assets.el ends here
```

- [ ] **Step 2: Create the test file scaffold**

Create `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`:

```elisp
;;; a3madkour-publish-assets-test.el --- ert tests for a3madkour-publish-assets -*- lexical-binding: t; -*-

;;; Commentary:

;; ert tests for A.1.c asset handling.  Run via run-tests.sh.

;;; Code:

(require 'ert)
(require 'cl-lib)
(require 'a3madkour-publish-assets)

;; Tests populated by subsequent tasks.

(provide 'a3madkour-publish-assets-test)

;;; a3madkour-publish-assets-test.el ends here
```

- [ ] **Step 3: Register the test file in `run-tests.sh`**

In `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`, find the existing `-l a3madkour-publish-rewrite-test.el` line and add a sibling line:

```bash
# Add right after the existing rewrite-test line:
  -l "$DIR/a3madkour-publish-assets-test.el" \
```

- [ ] **Step 4: Run the test suite to confirm baseline**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 121 tests, 121 results as expected, 0 unexpected` (no new tests yet; just verifying the new files load).

- [ ] **Step 5: Test-count checkpoint**

End of Task 5: **121 ert tests** (unchanged). Module + test file scaffolded; ready for logic.

---

### Task 6: `--asset-resolve-path` — normalize + classify against canonical root

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --asset-resolve-path: classification --

(defmacro a3-pub-assets-test--with-tmp-root (root-var &rest body)
  "Bind ROOT-VAR to a fresh tmpdir; cleanup after BODY."
  (declare (indent 1))
  `(let ((,root-var (make-temp-file "a3-pub-assets-" t)))
     (unwind-protect (progn ,@body)
       (delete-directory ,root-var t))))

(ert-deftest a3madkour-pub-assets-test/resolve-page-kind ()
  "Path under <root>/page/<slug>/ classifies as :kind page."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "page/foo" root) t)
      (with-temp-file (expand-file-name "page/foo/x.png" root) (insert "data"))
      (let ((result (a3madkour-pub--asset-resolve-path
                     (expand-file-name "page/foo/x.png" root)
                     nil)))
        (should (eq (plist-get result :kind) 'page))
        (should (string-suffix-p "page/foo/x.png" (plist-get result :abs-path)))))))

(ert-deftest a3madkour-pub-assets-test/resolve-shared-kind ()
  "Path under <root>/shared/ classifies as :kind shared."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "shared" root) t)
      (with-temp-file (expand-file-name "shared/y.svg" root) (insert "<svg/>"))
      (let ((result (a3madkour-pub--asset-resolve-path
                     (expand-file-name "shared/y.svg" root)
                     nil)))
        (should (eq (plist-get result :kind) 'shared))))))

(ert-deftest a3madkour-pub-assets-test/resolve-out-of-root-kind ()
  "Path outside canonical root classifies as :kind out-of-root."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root)
          (other (make-temp-file "a3-pub-other-" nil ".png" "data")))
      (unwind-protect
          (let ((result (a3madkour-pub--asset-resolve-path other nil)))
            (should (eq (plist-get result :kind) 'out-of-root)))
        (delete-file other)))))

(ert-deftest a3madkour-pub-assets-test/resolve-missing-kind ()
  "Non-existent file classifies as :kind missing (regardless of location)."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "page/foo" root) t)
      ;; Note: no file created.
      (let ((result (a3madkour-pub--asset-resolve-path
                     (expand-file-name "page/foo/missing.png" root)
                     nil)))
        (should (eq (plist-get result :kind) 'missing))))))

(ert-deftest a3madkour-pub-assets-test/resolve-relative-against-source-dir ()
  "Relative path resolves against the source file's directory."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (source-dir (expand-file-name "notes/sub/" root)))
      (make-directory source-dir t)
      (make-directory (expand-file-name "page/foo" root) t)
      (with-temp-file (expand-file-name "page/foo/x.png" root) (insert "d"))
      ;; Relative path from source-dir reaching into canonical root:
      (let ((result (a3madkour-pub--asset-resolve-path
                     (concat source-dir "../../page/foo/x.png")
                     nil)))
        (should (eq (plist-get result :kind) 'page))
        (should (file-exists-p (plist-get result :abs-path)))))))

(ert-deftest a3madkour-pub-assets-test/resolve-tilde-expansion ()
  "~/path expands to home; works for canonical-root references."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      ;; Even with tilde, expand-file-name handles it; here we just verify
      ;; that an already-absolute home-relative input doesn't double-expand.
      (let ((result (a3madkour-pub--asset-resolve-path
                     "~/nonexistent.png" nil)))
        (should (eq (plist-get result :kind) 'missing))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 6 failures with "Symbol's function definition is void: a3madkour-pub--asset-resolve-path".

- [ ] **Step 3: Implement `--asset-resolve-path`**

Insert into `a3madkour-publish-assets.el` (after the defcustoms, before `provide`):

```elisp
(defun a3madkour-pub--asset-resolve-path (path source-file)
  "Normalize PATH + classify against the canonical asset root.

PATH may be relative (resolved against SOURCE-FILE's directory), absolute,
or tilde-expanded.  SOURCE-FILE may be nil — in which case relative paths
resolve against `default-directory'.

Returns a plist:
  (:kind page|shared|out-of-root|missing
   :abs-path \"/canonical/absolute/path\"
   :rel-path \"page/<slug>/<filename>\" or \"shared/<filename>\" or nil)

`:kind missing' takes priority over location-based classification — a
non-existent file at a canonical-looking path still reports missing."
  (let* ((source-dir (or (and source-file (file-name-directory source-file))
                         default-directory))
         (abs (expand-file-name path source-dir))
         (root (expand-file-name a3madkour-pub-canonical-asset-root))
         (root-page (file-name-as-directory (expand-file-name "page" root)))
         (root-shared (file-name-as-directory (expand-file-name "shared" root)))
         (exists (file-exists-p abs)))
    (cond
     ((not exists)
      (list :kind 'missing :abs-path abs :rel-path nil))
     ((string-prefix-p root-page abs)
      (list :kind 'page :abs-path abs
            :rel-path (substring abs (length root))))
     ((string-prefix-p root-shared abs)
      (list :kind 'shared :abs-path abs
            :rel-path (substring abs (length root))))
     (t
      (list :kind 'out-of-root :abs-path abs :rel-path nil)))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 127 tests, 127 results as expected, 0 unexpected` (121 + 6 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 6: **127 ert tests** (121 → 127).

---

### Task 7: `--asset-cross-namespace-p` — own-slug match check

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --asset-cross-namespace-p --

(ert-deftest a3madkour-pub-assets-test/cross-ns-own-slug-matches ()
  "page/<slug>/foo where slug == source-slug → NOT cross-namespace."
  (let ((resolved (list :kind 'page
                        :abs-path "/tmp/root/page/foo/x.png"
                        :rel-path "page/foo/x.png")))
    (should-not (a3madkour-pub--asset-cross-namespace-p resolved "foo"))))

(ert-deftest a3madkour-pub-assets-test/cross-ns-own-slug-differs ()
  "page/<slug>/foo where slug != source-slug → cross-namespace."
  (let ((resolved (list :kind 'page
                        :abs-path "/tmp/root/page/foo/x.png"
                        :rel-path "page/foo/x.png")))
    (should (a3madkour-pub--asset-cross-namespace-p resolved "bar"))))

(ert-deftest a3madkour-pub-assets-test/cross-ns-shared-never-fires ()
  "shared/ assets are never cross-namespace (no slug component)."
  (let ((resolved (list :kind 'shared
                        :abs-path "/tmp/root/shared/y.svg"
                        :rel-path "shared/y.svg")))
    (should-not (a3madkour-pub--asset-cross-namespace-p resolved "anything"))))

(ert-deftest a3madkour-pub-assets-test/cross-ns-out-of-root-never-fires ()
  "out-of-root assets are not cross-namespace (different concern)."
  (let ((resolved (list :kind 'out-of-root
                        :abs-path "/some/other/path/x.png"
                        :rel-path nil)))
    (should-not (a3madkour-pub--asset-cross-namespace-p resolved "anything"))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures with "Symbol's function definition is void: a3madkour-pub--asset-cross-namespace-p".

- [ ] **Step 3: Implement**

Append to `a3madkour-publish-assets.el` (after `--asset-resolve-path`):

```elisp
(defun a3madkour-pub--asset-cross-namespace-p (resolved source-slug)
  "Return non-nil iff RESOLVED's page-namespace conflicts with SOURCE-SLUG.

Only fires when `:kind' is `page' AND the rel-path's page-subdir slug
differs from SOURCE-SLUG.  `shared' and `out-of-root' kinds never trigger
this check (shared has no slug component; out-of-root is a separate concern
handled by auto-remediation)."
  (when (eq (plist-get resolved :kind) 'page)
    (let* ((rel (plist-get resolved :rel-path))      ; "page/<slug>/<filename>"
           (parts (split-string rel "/" t))
           ;; parts = ("page" "<slug>" "<filename>")
           (path-slug (cadr parts)))
      (not (equal path-slug source-slug)))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 131 tests, 131 results as expected, 0 unexpected` (127 + 4 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 7: **131 ert tests** (127 → 131).

---

### Task 8: `--asset-bundle-dest` — compute destination path (page vs shared)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --asset-bundle-dest --

(ert-deftest a3madkour-pub-assets-test/bundle-dest-page ()
  "page-kind asset destination = BUNDLE-DIR/<filename>."
  (let ((resolved (list :kind 'page
                        :abs-path "/root/page/foo/x.png"
                        :rel-path "page/foo/x.png")))
    (should (equal (a3madkour-pub--asset-bundle-dest resolved "/site/content/garden/foo/")
                   "/site/content/garden/foo/x.png"))))

(ert-deftest a3madkour-pub-assets-test/bundle-dest-shared ()
  "shared-kind asset destination = <static-notes-shared-dir>/<filename>."
  (let ((a3madkour-pub-notes-shared-static-dir "/site/static/notes-shared")
        (resolved (list :kind 'shared
                        :abs-path "/root/shared/y.svg"
                        :rel-path "shared/y.svg")))
    (should (equal (a3madkour-pub--asset-bundle-dest resolved "/site/content/garden/foo/")
                   "/site/static/notes-shared/y.svg"))))

(ert-deftest a3madkour-pub-assets-test/bundle-dest-shared-requires-dir ()
  "shared-kind without notes-shared-static-dir set → error."
  (let ((a3madkour-pub-notes-shared-static-dir nil)
        (resolved (list :kind 'shared
                        :abs-path "/root/shared/y.svg"
                        :rel-path "shared/y.svg")))
    (should-error (a3madkour-pub--asset-bundle-dest resolved "/site/content/garden/foo/"))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures with "Symbol's function definition is void: a3madkour-pub--asset-bundle-dest".

- [ ] **Step 3: Implement**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub--asset-bundle-dest (resolved bundle-dir)
  "Return the on-disk destination path for RESOLVED asset.

For `:kind page', dest = BUNDLE-DIR/<filename>.
For `:kind shared', dest = `a3madkour-pub-notes-shared-static-dir'/<filename>
(the variable MUST be set; error otherwise — caller's publish driver should
set it at publish start).

Other kinds (`out-of-root', `missing') are not valid input — should be
resolved by the caller before calling this function."
  (let ((filename (file-name-nondirectory (plist-get resolved :abs-path)))
        (kind (plist-get resolved :kind)))
    (cond
     ((eq kind 'page)
      (expand-file-name filename bundle-dir))
     ((eq kind 'shared)
      (unless a3madkour-pub-notes-shared-static-dir
        (error "asset-bundle-dest: shared asset but notes-shared-static-dir unset"))
      (expand-file-name filename a3madkour-pub-notes-shared-static-dir))
     (t
      (error "asset-bundle-dest: unsupported kind %S" kind)))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 134 tests, 134 results as expected, 0 unexpected` (131 + 3 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 8: **134 ert tests** (131 → 134).

---

### Task 9: `--asset-emit-html` — `<img>` for images, `<a href>` for others, inert for failures

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --asset-emit-html --

(ert-deftest a3madkour-pub-assets-test/emit-image-with-display ()
  "Image extension → <img src alt> with display as alt."
  (should (equal (a3madkour-pub--asset-emit-html "x.png" "My screenshot" 'image)
                 "<img src=\"x.png\" alt=\"My screenshot\" />")))

(ert-deftest a3madkour-pub-assets-test/emit-non-image-with-display ()
  "Non-image extension → <a href>text</a>."
  (should (equal (a3madkour-pub--asset-emit-html "manual.pdf" "Read the manual" 'other)
                 "<a href=\"manual.pdf\">Read the manual</a>")))

(ert-deftest a3madkour-pub-assets-test/emit-shared-img-src ()
  "Shared assets get /notes-shared/ src prefix from caller."
  (should (equal (a3madkour-pub--asset-emit-html "/notes-shared/diagram.svg" "diagram" 'image)
                 "<img src=\"/notes-shared/diagram.svg\" alt=\"diagram\" />")))

(ert-deftest a3madkour-pub-assets-test/emit-display-text-escaped ()
  "Display text containing < > & escapes properly in both <img alt> and <a>."
  (should (equal (a3madkour-pub--asset-emit-html "x.png" "a < b & c" 'image)
                 "<img src=\"x.png\" alt=\"a &lt; b &amp; c\" />"))
  (should (equal (a3madkour-pub--asset-emit-html "x.pdf" "a < b & c" 'other)
                 "<a href=\"x.pdf\">a &lt; b &amp; c</a>")))

(ert-deftest a3madkour-pub-assets-test/emit-src-with-quote-escaped ()
  "src containing \" gets &quot;."
  (should (equal (a3madkour-pub--asset-emit-html "odd\"name.png" "alt" 'image)
                 "<img src=\"odd&quot;name.png\" alt=\"alt\" />")))

(ert-deftest a3madkour-pub-assets-test/emit-inert-missing-asset ()
  "(missing asset: NAME) inert marker for failed cases."
  (should (equal (a3madkour-pub--asset-emit-inert "x.png")
                 "(missing asset: x.png)"))
  ;; Filename with special chars gets escaped.
  (should (equal (a3madkour-pub--asset-emit-inert "<x>.png")
                 "(missing asset: &lt;x&gt;.png)")))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 7 failures (2 ert tests assert twice; 7 failure messages) for both `--asset-emit-html` and `--asset-emit-inert`.

- [ ] **Step 3: Implement classification helper + emit helpers**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub--asset-kind-from-ext (path)
  "Return 'image if PATH's extension is in `a3madkour-pub-asset-image-extensions';
'other otherwise.  Unknown extensions fall through to 'other (link form,
safest default)."
  (let ((ext (downcase (or (file-name-extension path) ""))))
    (if (member ext a3madkour-pub-asset-image-extensions)
        'image
      'other)))

(defun a3madkour-pub--asset-emit-html (src display kind)
  "Format HTML for an asset link.

SRC is the rewritten link path (relative filename for page; `/notes-shared/X'
for shared).  DISPLAY is the link text (alt for images, body for others).
KIND is `'image' or `'other'.

All interpolated values pass through `a3madkour-pub--html-escape'."
  (if (eq kind 'image)
      (format "<img src=\"%s\" alt=\"%s\" />"
              (a3madkour-pub--html-escape src)
              (a3madkour-pub--html-escape display))
    (format "<a href=\"%s\">%s</a>"
            (a3madkour-pub--html-escape src)
            (a3madkour-pub--html-escape display))))

(defun a3madkour-pub--asset-emit-inert (filename)
  "Format the inert `(missing asset: FILENAME)' marker.
FILENAME passes through `a3madkour-pub--html-escape' to handle weird names."
  (format "(missing asset: %s)" (a3madkour-pub--html-escape filename)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 141 tests, 141 results as expected, 0 unexpected` (134 + 7 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 9: **141 ert tests** (134 → 141).

---

### Task 10: `--asset-content-hash` — SHA-1 first 6 hex chars

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --asset-content-hash --

(ert-deftest a3madkour-pub-assets-test/content-hash-deterministic ()
  "Same content → same 6-char hash."
  (let ((tmp (make-temp-file "a3-pub-hash-")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert "hello"))
          (let ((h1 (a3madkour-pub--asset-content-hash tmp))
                (h2 (a3madkour-pub--asset-content-hash tmp)))
            (should (= 6 (length h1)))
            (should (string-match-p "\\`[0-9a-f]\\{6\\}\\'" h1))
            (should (equal h1 h2))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-assets-test/content-hash-differs-by-content ()
  "Different content → different hash."
  (let ((a (make-temp-file "a3-pub-hash-a-"))
        (b (make-temp-file "a3-pub-hash-b-")))
    (unwind-protect
        (progn
          (with-temp-file a (insert "hello"))
          (with-temp-file b (insert "world"))
          (should-not (equal (a3madkour-pub--asset-content-hash a)
                             (a3madkour-pub--asset-content-hash b))))
      (delete-file a)
      (delete-file b))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 2 failures with "Symbol's function definition is void: a3madkour-pub--asset-content-hash".

- [ ] **Step 3: Implement**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub--asset-content-hash (file)
  "Return the first 6 hex chars of SHA-1 of FILE's contents.
Used for filename-collision suffixing in auto-remediation."
  (substring (secure-hash 'sha1
                          (with-temp-buffer
                            (set-buffer-multibyte nil)
                            (insert-file-contents-literally file)
                            (buffer-string)))
             0 6))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 143 tests, 143 results as expected, 0 unexpected` (141 + 2 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 10: **143 ert tests** (141 → 143).

---

### Task 11: Auto-remediation — destination + collision (pure logic, no FS writes)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --asset-remediate-dest: destination computation + collision --

(ert-deftest a3madkour-pub-assets-test/remediate-dest-no-collision ()
  "No collision → dest = <root>/page/<src-slug>/<filename>."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root)
          (src (make-temp-file "a3-pub-src-" nil ".png" "data")))
      (unwind-protect
          (let ((dest (a3madkour-pub--asset-remediate-dest src "foo")))
            (should (string-suffix-p "page/foo/" (file-name-directory dest)))
            (should (equal (file-name-nondirectory dest)
                           (file-name-nondirectory src))))
        (delete-file src)))))

(ert-deftest a3madkour-pub-assets-test/remediate-dest-collision-same-content ()
  "Destination exists with byte-equal content → return dest unchanged (no suffix)."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "page/foo" root) t)
      ;; Pre-existing dest with same content.
      (with-temp-file (expand-file-name "page/foo/clash.png" root) (insert "same"))
      (let ((src (make-temp-file "a3-pub-src-" nil ".png" "same")))
        (unwind-protect
            ;; Rename src to match the dest basename for the test fixture:
            (let* ((renamed (expand-file-name "clash.png" (file-name-directory src))))
              (rename-file src renamed)
              (let ((dest (a3madkour-pub--asset-remediate-dest renamed "foo")))
                (should (equal (file-name-nondirectory dest) "clash.png"))
                (should-not (string-match-p "-[0-9a-f]\\{6\\}\\." dest))
                (delete-file renamed)))
          (when (file-exists-p src) (delete-file src)))))))

(ert-deftest a3madkour-pub-assets-test/remediate-dest-collision-different-content ()
  "Destination exists with different content → suffix with content hash."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "page/foo" root) t)
      ;; Pre-existing dest with DIFFERENT content.
      (with-temp-file (expand-file-name "page/foo/clash.png" root) (insert "old"))
      (let ((src (make-temp-file "a3-pub-src-" nil ".png" "new")))
        (unwind-protect
            (let* ((renamed (expand-file-name "clash.png" (file-name-directory src))))
              (rename-file src renamed)
              (let ((dest (a3madkour-pub--asset-remediate-dest renamed "foo")))
                (should (string-match-p "/clash-[0-9a-f]\\{6\\}\\.png\\'" dest))
                (delete-file renamed)))
          (when (file-exists-p src) (delete-file src)))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures with "Symbol's function definition is void: a3madkour-pub--asset-remediate-dest".

- [ ] **Step 3: Implement**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub--asset-files-byte-equal-p (a b)
  "Return non-nil iff files A and B have identical byte contents."
  (and (file-exists-p a) (file-exists-p b)
       (= (file-attribute-size (file-attributes a))
          (file-attribute-size (file-attributes b)))
       (string=
        (with-temp-buffer
          (set-buffer-multibyte nil)
          (insert-file-contents-literally a)
          (buffer-string))
        (with-temp-buffer
          (set-buffer-multibyte nil)
          (insert-file-contents-literally b)
          (buffer-string)))))

(defun a3madkour-pub--asset-remediate-dest (src dest-slug)
  "Compute the canonical destination for SRC under page/DEST-SLUG/.

Filename-collision handling:
  - If dest doesn't exist                     → dest unchanged.
  - If dest exists + byte-equal to src        → dest unchanged (no-op move).
  - If dest exists + content differs          → append -<6hex> SHA-1 of src.

Returns the absolute destination path (no I/O performed)."
  (let* ((root (expand-file-name a3madkour-pub-canonical-asset-root))
         (dest-dir (expand-file-name (format "page/%s" dest-slug) root))
         (filename (file-name-nondirectory src))
         (dest (expand-file-name filename dest-dir)))
    (cond
     ((not (file-exists-p dest))
      dest)
     ((a3madkour-pub--asset-files-byte-equal-p src dest)
      dest)
     (t
      (let* ((base (file-name-base filename))
             (ext (file-name-extension filename))
             (hash (a3madkour-pub--asset-content-hash src)))
        (expand-file-name
         (if ext
             (format "%s-%s.%s" base hash ext)
           (format "%s-%s" base hash))
         dest-dir))))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 146 tests, 146 results as expected, 0 unexpected` (143 + 3 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 11: **146 ert tests** (143 → 146).

---

### Task 12: Auto-remediation — actual move (git-mv-vs-mv) + dry-run

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --asset-do-move --

(ert-deftest a3madkour-pub-assets-test/do-move-plain-mv ()
  "Non-git-tracked source uses plain `rename-file' (mv)."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (src (make-temp-file "a3-pub-mvsrc-" nil ".png" "data"))
           (dest (expand-file-name "page/foo/moved.png" root)))
      (make-directory (file-name-directory dest) t)
      (unwind-protect
          ;; Force mv branch by stubbing vc-git-handler-p.
          (cl-letf (((symbol-function 'vc-backend) (lambda (_) nil)))
            (let ((result (a3madkour-pub--asset-do-move src dest nil)))
              (should (eq (plist-get result :method) 'mv))
              (should (file-exists-p dest))
              (should-not (file-exists-p src))))
        (when (file-exists-p src) (delete-file src))
        (when (file-exists-p dest) (delete-file dest))))))

(ert-deftest a3madkour-pub-assets-test/do-move-git-mv-branch ()
  "Git-tracked source uses `git mv'."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (src (make-temp-file "a3-pub-gitmvsrc-" nil ".png" "data"))
           (dest (expand-file-name "page/foo/gitmoved.png" root))
           (git-mv-called nil))
      (make-directory (file-name-directory dest) t)
      (unwind-protect
          (cl-letf (((symbol-function 'vc-backend) (lambda (_) 'Git))
                    ((symbol-function 'call-process)
                     (lambda (prog _ _ _ &rest args)
                       (when (and (equal prog "git") (equal (car args) "mv"))
                         (setq git-mv-called t)
                         (rename-file (cadr args) (caddr args)))
                       0)))
            (let ((result (a3madkour-pub--asset-do-move src dest nil)))
              (should (eq (plist-get result :method) 'git-mv))
              (should git-mv-called)
              (should (file-exists-p dest))))
        (when (file-exists-p src) (delete-file src))
        (when (file-exists-p dest) (delete-file dest))))))

(ert-deftest a3madkour-pub-assets-test/do-move-dry-run-no-side-effects ()
  "Dry-run reports the move without performing it."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (src (make-temp-file "a3-pub-drysrc-" nil ".png" "data"))
           (dest (expand-file-name "page/foo/dry.png" root)))
      (make-directory (file-name-directory dest) t)
      (unwind-protect
          (let ((result (a3madkour-pub--asset-do-move src dest t)))
            (should (eq (plist-get result :method) 'dry-run))
            (should (file-exists-p src))           ; source still present
            (should-not (file-exists-p dest))      ; dest not created
            (should (string-match-p "would move" (plist-get result :info))))
        (when (file-exists-p src) (delete-file src))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures with "Symbol's function definition is void: a3madkour-pub--asset-do-move".

- [ ] **Step 3: Implement**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub--asset-do-move (src dest dry-run)
  "Move SRC to DEST.  Uses `git mv' if SRC is git-tracked, plain rename otherwise.

When DRY-RUN is non-nil, no I/O performed; returns
  (:method dry-run :info \"would move: SRC -> DEST\")

When DRY-RUN is nil, performs the move and returns one of:
  (:method git-mv :info \"moved (git mv): SRC -> DEST\")
  (:method mv     :info \"moved: SRC -> DEST\")

Caller is responsible for creating DEST's directory if needed."
  (when (not dry-run)
    (make-directory (file-name-directory dest) t))
  (cond
   (dry-run
    (list :method 'dry-run
          :info (format "would move: %s -> %s" src dest)))
   ((eq (vc-backend src) 'Git)
    (let ((rc (call-process "git" nil nil nil "mv" src dest)))
      (unless (zerop rc)
        (error "git mv failed (rc=%d): %s -> %s" rc src dest)))
    (list :method 'git-mv
          :info (format "moved (git mv): %s -> %s" src dest)))
   (t
    (rename-file src dest)
    (list :method 'mv
          :info (format "moved: %s -> %s" src dest)))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 149 tests, 149 results as expected, 0 unexpected` (146 + 3 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 12: **149 ert tests** (146 → 149).

---

### Task 13: Auto-remediation — org-source link rewrite

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --asset-rewrite-source-link --

(ert-deftest a3madkour-pub-assets-test/rewrite-source-link-basic ()
  "Find OLD link form in org buffer, replace with NEW."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((org-file (expand-file-name "note.org" root))
           (old "[[/home/u/Downloads/x.png]]")
           (new "[[./assets/page/foo/x.png]]"))
      (with-temp-file org-file
        (insert "Some text.\nHere is " old " in the doc.\n"))
      (a3madkour-pub--asset-rewrite-source-link org-file old new)
      (with-temp-buffer
        (insert-file-contents org-file)
        (should-not (search-forward old nil t))
        (goto-char (point-min))
        (should (search-forward new nil t))))))

(ert-deftest a3madkour-pub-assets-test/rewrite-source-link-with-display-text ()
  "[[OLD-PATH][TEXT]] gets path rewritten; text preserved."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((org-file (expand-file-name "note.org" root))
           (old "[[/home/u/x.png][My pic]]")
           (new "[[./assets/page/foo/x.png][My pic]]"))
      (with-temp-file org-file (insert "Doc with " old "."))
      (a3madkour-pub--asset-rewrite-source-link org-file old new)
      (with-temp-buffer
        (insert-file-contents org-file)
        (should (search-forward new nil t))))))

(ert-deftest a3madkour-pub-assets-test/rewrite-source-link-multiple-occurrences ()
  "All occurrences of OLD get rewritten."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((org-file (expand-file-name "note.org" root))
           (old "[[/x.png]]")
           (new "[[./y.png]]"))
      (with-temp-file org-file
        (insert old "\nmid\n" old "\nend\n" old))
      (a3madkour-pub--asset-rewrite-source-link org-file old new)
      (with-temp-buffer
        (insert-file-contents org-file)
        (let ((count 0))
          (while (search-forward new nil t) (cl-incf count))
          (should (= 3 count)))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures with "Symbol's function definition is void: a3madkour-pub--asset-rewrite-source-link".

- [ ] **Step 3: Implement**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub--asset-rewrite-source-link (org-file old-link new-link)
  "In ORG-FILE, replace every occurrence of OLD-LINK with NEW-LINK.

OLD-LINK and NEW-LINK are the full `[[...]]' bracket forms.  Match is
literal (case-sensitive, no regex interpretation); replacement is literal.
File is saved to disk after rewriting.

This is the visible side effect of auto-remediation — author sees both the
asset move and the link rewrite in `git status' after the publish."
  (with-temp-buffer
    (insert-file-contents org-file)
    (goto-char (point-min))
    (let ((case-fold-search nil))
      (while (search-forward old-link nil t)
        (replace-match new-link t t)))
    (write-region (point-min) (point-max) org-file nil 'silent)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 152 tests, 152 results as expected, 0 unexpected` (149 + 3 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 13: **152 ert tests** (149 → 152).

---

### Task 14: `rewrite-asset-link` — top-level dispatcher

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- rewrite-asset-link: full dispatch --

(ert-deftest a3madkour-pub-assets-test/rewrite-asset-page-image ()
  "Per-page image asset → :html <img> + :resolved-path + :kind image."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "page/foo" root) t)
      (with-temp-file (expand-file-name "page/foo/x.png" root) (insert "data"))
      (cl-letf (((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "foo")))
        (let ((result (a3madkour-pub/rewrite-asset-link
                       (expand-file-name "page/foo/x.png" root)
                       "My screenshot"
                       "source-id")))
          (should (equal (plist-get result :html)
                         "<img src=\"x.png\" alt=\"My screenshot\" />"))
          (should (equal (plist-get result :resolved-path) "x.png"))
          (should (eq (plist-get result :kind) 'image))
          (should-not (plist-get result :warnings)))))))

(ert-deftest a3madkour-pub-assets-test/rewrite-asset-shared-image ()
  "Shared image asset → :html <img src=/notes-shared/...>."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root)
          (a3madkour-pub-notes-shared-static-dir "/site/static/notes-shared"))
      (make-directory (expand-file-name "shared" root) t)
      (with-temp-file (expand-file-name "shared/y.svg" root) (insert "<svg/>"))
      (cl-letf (((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "foo")))
        (let ((result (a3madkour-pub/rewrite-asset-link
                       (expand-file-name "shared/y.svg" root)
                       "diagram"
                       "source-id")))
          (should (string-match-p "/notes-shared/y.svg" (plist-get result :html)))
          (should (equal (plist-get result :resolved-path) "/notes-shared/y.svg")))))))

(ert-deftest a3madkour-pub-assets-test/rewrite-asset-non-image ()
  "PDF (non-image) asset → :html <a href> + :kind other."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "page/foo" root) t)
      (with-temp-file (expand-file-name "page/foo/manual.pdf" root) (insert "pdf"))
      (cl-letf (((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "foo")))
        (let ((result (a3madkour-pub/rewrite-asset-link
                       (expand-file-name "page/foo/manual.pdf" root)
                       "Read the manual"
                       "source-id")))
          (should (string-match-p "<a href=\"manual.pdf\">" (plist-get result :html)))
          (should (eq (plist-get result :kind) 'other)))))))

(ert-deftest a3madkour-pub-assets-test/rewrite-asset-cross-namespace ()
  "page-namespace mismatch → :inert (missing asset: ...) + WARN."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "page/foo" root) t)
      (with-temp-file (expand-file-name "page/foo/x.png" root) (insert "d"))
      ;; Source slug is "bar" but link points at page/foo/x.png:
      (cl-letf (((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "bar")))
        (let ((result (a3madkour-pub/rewrite-asset-link
                       (expand-file-name "page/foo/x.png" root)
                       "screenshot"
                       "source-id")))
          (should (string-match-p "missing asset:" (plist-get result :inert)))
          (should (= 1 (length (plist-get result :warnings))))
          (should (string-match-p "cross.*namespace\\|move to shared"
                                   (car (plist-get result :warnings)))))))))

(ert-deftest a3madkour-pub-assets-test/rewrite-asset-missing ()
  "Non-existent file → :inert + WARN."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "page/foo" root) t)
      (cl-letf (((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "foo")))
        (let ((result (a3madkour-pub/rewrite-asset-link
                       (expand-file-name "page/foo/missing.png" root)
                       "x"
                       "source-id")))
          (should (plist-get result :inert))
          (should (= 1 (length (plist-get result :warnings))))
          (should (string-match-p "does not exist\\|missing"
                                   (car (plist-get result :warnings)))))))))

(ert-deftest a3madkour-pub-assets-test/rewrite-asset-no-display-text ()
  "When text equals path (no display text), use filename basename as alt/body."
  (a3-pub-assets-test--with-tmp-root root
    (let ((a3madkour-pub-canonical-asset-root root))
      (make-directory (expand-file-name "page/foo" root) t)
      (with-temp-file (expand-file-name "page/foo/x.png" root) (insert "d"))
      (cl-letf (((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "foo")))
        (let* ((path (expand-file-name "page/foo/x.png" root))
               ;; Pass text == path to simulate org's [[path]] no-display form:
               (result (a3madkour-pub/rewrite-asset-link path path "source-id")))
          (should (string-match-p "alt=\"x.png\"" (plist-get result :html))))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 6 failures with "Symbol's function definition is void: a3madkour-pub/rewrite-asset-link".

- [ ] **Step 3: Implement (no auto-remediation yet; Task 15 adds it)**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub/rewrite-asset-link (path text source-note-id &optional dry-run)
  "Resolve an asset link to HTML + path metadata.

PATH is the link path (relative `./assets/...', absolute `~/...' or `/...').
TEXT is the link display text (may equal PATH for [[no-text]] form).
SOURCE-NOTE-ID is the source note's UUID — used to derive source slug
for cross-namespace validation + auto-remediation destination.
DRY-RUN, when non-nil, prevents auto-remediation I/O (Task 15).

Returns one of:
  (:html STRING :resolved-path REL :source-path SRC :kind image|other
   :warnings (WARN ...))
  (:inert \"(missing asset: NAME)\" :warnings (WARN ...))

See parent spec §7 + design doc §5."
  (let* ((source-file (a3madkour-pub--id-to-file source-note-id))
         (source-slug (a3madkour-pub/note-slug source-note-id))
         (resolved (a3madkour-pub--asset-resolve-path path source-file))
         (kind (plist-get resolved :kind))
         (abs (plist-get resolved :abs-path))
         (filename (file-name-nondirectory abs))
         (display (if (and text (not (equal text path))) text filename))
         (html-kind (a3madkour-pub--asset-kind-from-ext filename)))
    (cond
     ;; Missing file → inert + WARN.
     ((eq kind 'missing)
      (list :inert (a3madkour-pub--asset-emit-inert filename)
            :warnings (list (format "asset source file does not exist: %s" abs))))
     ;; Cross-namespace use → inert + WARN.
     ((and (eq kind 'page)
           (a3madkour-pub--asset-cross-namespace-p resolved source-slug))
      (list :inert (a3madkour-pub--asset-emit-inert filename)
            :warnings (list
                       (format "cross-namespace asset: %s; move to assets/shared/ to share"
                               (plist-get resolved :rel-path)))))
     ;; Out-of-root: defer to Task 15 (auto-remediation).  For now, inert.
     ((eq kind 'out-of-root)
      (list :inert (a3madkour-pub--asset-emit-inert filename)
            :warnings (list
                       (format "out-of-canonical-root: %s (auto-remediation lands in Task 15)"
                               abs))))
     ;; page + same namespace → emit page-relative HTML.
     ((eq kind 'page)
      (let ((src filename))
        (list :html (a3madkour-pub--asset-emit-html src display html-kind)
              :resolved-path src
              :source-path abs
              :kind html-kind
              :warnings nil)))
     ;; shared → emit /notes-shared/ HTML.
     ((eq kind 'shared)
      (let ((src (format "/notes-shared/%s" filename)))
        (list :html (a3madkour-pub--asset-emit-html src display html-kind)
              :resolved-path src
              :source-path abs
              :kind html-kind
              :warnings nil))))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 158 tests, 158 results as expected, 0 unexpected` (152 + 6 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 14: **158 ert tests** (152 → 158). Asset rewriting works for page + shared + missing + cross-namespace. Auto-remediation still pending.

---

### Task 15: Integrate auto-remediation into `rewrite-asset-link`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- rewrite-asset-link: auto-remediation integration --

(ert-deftest a3madkour-pub-assets-test/remediate-moves-and-rewrites-link ()
  "Out-of-root asset (default auto-remediate=t) → moved + source rewritten."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (a3madkour-pub-asset-auto-remediate t)
           (source-org (expand-file-name "note.org" root))
           (src-asset (make-temp-file "a3-pub-oor-" nil ".png" "data")))
      (with-temp-file source-org
        (insert "Doc with [[" src-asset "]] in it."))
      (unwind-protect
          (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                     (lambda (_) source-org))
                    ((symbol-function 'a3madkour-pub/note-slug)
                     (lambda (_) "foo"))
                    ((symbol-function 'vc-backend) (lambda (_) nil)))
            (let ((result (a3madkour-pub/rewrite-asset-link
                           src-asset "alt" "source-id")))
              (should (plist-get result :html))
              ;; Source asset moved into canonical root:
              (should-not (file-exists-p src-asset))
              (should (file-exists-p
                       (expand-file-name
                        (format "page/foo/%s" (file-name-nondirectory src-asset))
                        root)))
              ;; .org source link rewritten:
              (with-temp-buffer
                (insert-file-contents source-org)
                (should-not (search-forward (format "[[%s]]" src-asset) nil t))
                (goto-char (point-min))
                (should (search-forward "[[./assets/page/foo/" nil t)))))
        (when (file-exists-p src-asset) (delete-file src-asset))))))

(ert-deftest a3madkour-pub-assets-test/remediate-disabled-emits-inert ()
  "When auto-remediate=nil, out-of-root → inert + WARN, no move."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (a3madkour-pub-asset-auto-remediate nil)
           (src-asset (make-temp-file "a3-pub-noremed-" nil ".png" "data")))
      (unwind-protect
          (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                     (lambda (_) nil))
                    ((symbol-function 'a3madkour-pub/note-slug)
                     (lambda (_) "foo")))
            (let ((result (a3madkour-pub/rewrite-asset-link
                           src-asset "alt" "source-id")))
              (should (plist-get result :inert))
              (should (file-exists-p src-asset))))         ; not moved
        (when (file-exists-p src-asset) (delete-file src-asset))))))

(ert-deftest a3madkour-pub-assets-test/remediate-dry-run-no-side-effects ()
  "DRY-RUN suppresses both the move and the source rewrite."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (a3madkour-pub-asset-auto-remediate t)
           (source-org (expand-file-name "note.org" root))
           (src-asset (make-temp-file "a3-pub-dryoor-" nil ".png" "data")))
      (with-temp-file source-org
        (insert "Doc with [[" src-asset "]]"))
      (unwind-protect
          (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                     (lambda (_) source-org))
                    ((symbol-function 'a3madkour-pub/note-slug)
                     (lambda (_) "foo")))
            (let ((result (a3madkour-pub/rewrite-asset-link
                           src-asset "alt" "source-id" t)))   ; dry-run = t
              ;; Source still in place, .org source NOT rewritten:
              (should (file-exists-p src-asset))
              (with-temp-buffer
                (insert-file-contents source-org)
                (should (search-forward (format "[[%s]]" src-asset) nil t)))
              ;; Result reports dry-run (no html or inert; deferred)
              (should (cl-find "would move" (plist-get result :warnings)
                                :test (lambda (n s) (string-match-p n s))))))
        (when (file-exists-p src-asset) (delete-file src-asset))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures — out-of-root branch in Task 14 still emits `:inert` placeholder; not actually remediating.

- [ ] **Step 3: Update `rewrite-asset-link` — replace the out-of-root branch**

In `a3madkour-publish-assets.el`, find the current out-of-root branch (in the `cond` inside `a3madkour-pub/rewrite-asset-link`) and REPLACE it:

```elisp
;; OLD (Task 14 placeholder):
((eq kind 'out-of-root)
 (list :inert (a3madkour-pub--asset-emit-inert filename)
       :warnings (list
                  (format "out-of-canonical-root: %s (auto-remediation lands in Task 15)"
                          abs))))

;; NEW:
((eq kind 'out-of-root)
 (cond
  ((not a3madkour-pub-asset-auto-remediate)
   (list :inert (a3madkour-pub--asset-emit-inert filename)
         :warnings (list
                    (format "out-of-canonical-root: %s; set auto-remediate or move manually"
                            abs))))
  (t
   (let* ((dest (a3madkour-pub--asset-remediate-dest abs source-slug))
          (move-result (a3madkour-pub--asset-do-move abs dest dry-run)))
     (cond
      (dry-run
       (list :resolved-path nil :source-path abs :kind html-kind
             :warnings (list (plist-get move-result :info))))
      (t
       ;; Rewrite the .org source link to the new canonical relative form:
       (let* ((dest-rel (concat "./" (file-relative-name
                                       dest
                                       (file-name-directory (or source-file ""))))))
         (when source-file
           (a3madkour-pub--asset-rewrite-source-link
            source-file
            (format "[[%s]]" path)
            (format "[[%s]]" dest-rel))
           ;; Also handle [[path][text]] form:
           (when (and text (not (equal text path)))
             (a3madkour-pub--asset-rewrite-source-link
              source-file
              (format "[[%s][%s]]" path text)
              (format "[[%s][%s]]" dest-rel text))))
         ;; Now re-dispatch as page-kind with the new dest:
         (let* ((new-resolved (a3madkour-pub--asset-resolve-path dest nil))
                (new-filename (file-name-nondirectory dest))
                (src new-filename))
           (list :html (a3madkour-pub--asset-emit-html src display html-kind)
                 :resolved-path src
                 :source-path dest
                 :kind html-kind
                 :warnings (list (plist-get move-result :info))))))))))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 161 tests, 161 results as expected, 0 unexpected` (158 + 3 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 15: **161 ert tests** (158 → 161). Full `rewrite-asset-link` complete with auto-remediation.

---

### Task 16: `--extract-asset-refs` — find all asset-shaped links in an org file

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --extract-asset-refs --

(ert-deftest a3madkour-pub-assets-test/extract-refs-finds-relative-and-absolute ()
  "Extracts all asset-shaped links from an org file."
  (a3-pub-assets-test--with-tmp-root root
    (let ((org-file (expand-file-name "note.org" root)))
      (with-temp-file org-file
        (insert "Hello\n"
                "[[./assets/page/foo/x.png]]\n"
                "[[/abs/path/y.svg][caption]]\n"
                "[[id:UUID-here][some link]]\n"          ; id link, should NOT match
                "[[~/org/notes/assets/shared/z.pdf]]\n"
                "[[https://example.com][external]]\n"))  ; external, should NOT match
      (let ((refs (a3madkour-pub--extract-asset-refs org-file)))
        (should (= 3 (length refs)))
        (should (cl-some (lambda (ref)
                           (string-match-p "x\\.png" (car ref)))
                         refs))
        (should (cl-some (lambda (ref)
                           (and (string-match-p "y\\.svg" (car ref))
                                (equal (cdr ref) "caption")))
                         refs))
        (should (cl-some (lambda (ref)
                           (string-match-p "z\\.pdf" (car ref)))
                         refs))))))

(ert-deftest a3madkour-pub-assets-test/extract-refs-empty-file ()
  "Empty org file → empty refs list."
  (a3-pub-assets-test--with-tmp-root root
    (let ((org-file (expand-file-name "empty.org" root)))
      (with-temp-file org-file (insert ""))
      (should-not (a3madkour-pub--extract-asset-refs org-file)))))

(ert-deftest a3madkour-pub-assets-test/extract-refs-no-display-text ()
  "[[path]] form sets text equal to path."
  (a3-pub-assets-test--with-tmp-root root
    (let ((org-file (expand-file-name "note.org" root)))
      (with-temp-file org-file (insert "[[./x.png]]"))
      (let ((refs (a3madkour-pub--extract-asset-refs org-file)))
        (should (= 1 (length refs)))
        (should (equal (caar refs) (cdar refs)))))))

(ert-deftest a3madkour-pub-assets-test/extract-refs-no-asset-shaped ()
  "File with only id and external links → empty refs."
  (a3-pub-assets-test--with-tmp-root root
    (let ((org-file (expand-file-name "note.org" root)))
      (with-temp-file org-file
        (insert "[[id:UUID][x]] [[https://example.com][y]] [[file:foo.org][z]]"))
      (should-not (a3madkour-pub--extract-asset-refs org-file)))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures with "Symbol's function definition is void: a3madkour-pub--extract-asset-refs".

- [ ] **Step 3: Implement**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub--extract-asset-refs (org-file)
  "Return a list of (PATH . TEXT) pairs for every asset-shaped link in ORG-FILE.

Walks all `[[<path>][<text>]]' and `[[<path>]]' forms; filters via
`a3madkour-pub--asset-shaped-link-p' (no URL scheme; extension != org)."
  (let ((refs nil))
    (with-temp-buffer
      (insert-file-contents org-file)
      (goto-char (point-min))
      (while (re-search-forward
              "\\[\\[\\([^]]+\\)\\(?:\\]\\[\\([^]]+\\)\\)?\\]\\]"
              nil t)
        (let ((path (match-string 1))
              (text (or (match-string 2) (match-string 1))))
          (when (a3madkour-pub--asset-shaped-link-p path)
            (push (cons path text) refs)))))
    (nreverse refs)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 165 tests, 165 results as expected, 0 unexpected` (161 + 4 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 16: **165 ert tests** (161 → 165).

---

### Task 17: `--asset-cleanup-stale` — blacklist removal from bundle dir

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- --asset-cleanup-stale --

(ert-deftest a3madkour-pub-assets-test/cleanup-removes-orphan ()
  "Bundle file not in ref set + not index.md → removed."
  (a3-pub-assets-test--with-tmp-root bundle
    (with-temp-file (expand-file-name "index.md" bundle) (insert "..."))
    (with-temp-file (expand-file-name "kept.png" bundle) (insert "k"))
    (with-temp-file (expand-file-name "stale.png" bundle) (insert "s"))
    (let ((removed (a3madkour-pub--asset-cleanup-stale bundle '("kept.png"))))
      (should (member (expand-file-name "stale.png" bundle) removed))
      (should-not (file-exists-p (expand-file-name "stale.png" bundle)))
      (should (file-exists-p (expand-file-name "kept.png" bundle))))))

(ert-deftest a3madkour-pub-assets-test/cleanup-preserves-index-md ()
  "index.md is always preserved even if not in ref set."
  (a3-pub-assets-test--with-tmp-root bundle
    (with-temp-file (expand-file-name "index.md" bundle) (insert "..."))
    (a3madkour-pub--asset-cleanup-stale bundle '())
    (should (file-exists-p (expand-file-name "index.md" bundle)))))

(ert-deftest a3madkour-pub-assets-test/cleanup-preserves-language-variants ()
  "index.en.md / _index.md preserved."
  (a3-pub-assets-test--with-tmp-root bundle
    (with-temp-file (expand-file-name "index.md" bundle) (insert "."))
    (with-temp-file (expand-file-name "index.en.md" bundle) (insert "."))
    (with-temp-file (expand-file-name "_index.md" bundle) (insert "."))
    (a3madkour-pub--asset-cleanup-stale bundle '())
    (should (file-exists-p (expand-file-name "index.en.md" bundle)))
    (should (file-exists-p (expand-file-name "_index.md" bundle)))))

(ert-deftest a3madkour-pub-assets-test/cleanup-skips-dotfiles ()
  ".publish-state, .DS_Store, etc. preserved (not in ref set; not removed)."
  (a3-pub-assets-test--with-tmp-root bundle
    (with-temp-file (expand-file-name ".publish-state" bundle) (insert "."))
    (with-temp-file (expand-file-name "stale.png" bundle) (insert "."))
    (a3madkour-pub--asset-cleanup-stale bundle '())
    (should (file-exists-p (expand-file-name ".publish-state" bundle)))
    (should-not (file-exists-p (expand-file-name "stale.png" bundle)))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures with "Symbol's function definition is void: a3madkour-pub--asset-cleanup-stale".

- [ ] **Step 3: Implement**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub--asset-cleanup-stale (bundle-dir referenced-files)
  "Remove files in BUNDLE-DIR not in REFERENCED-FILES.

Preserves:
  - index.md, _index.md, index.*.md (Hugo bundle conventions)
  - Files starting with `.` (dotfiles like .publish-state, .DS_Store)
  - Directories (cleanup is shallow; nested subdirs untouched)

Returns the list of removed absolute paths."
  (let ((removed nil))
    (when (file-directory-p bundle-dir)
      (dolist (f (directory-files bundle-dir t "^[^.]"))   ; skip dotfiles
        (let ((basename (file-name-nondirectory f)))
          (when (and (file-regular-p f)
                     (not (equal basename "index.md"))
                     (not (equal basename "_index.md"))
                     (not (string-match "\\`index\\..*\\.md\\'" basename))
                     (not (member basename referenced-files)))
            (delete-file f)
            (push f removed)))))
    (nreverse removed)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 169 tests, 169 results as expected, 0 unexpected` (165 + 4 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 17: **169 ert tests** (165 → 169).

---

### Task 18: `asset-validate-and-copy` — top-level orchestrator

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-assets-test.el`:

```elisp
;; -- asset-validate-and-copy --

(ert-deftest a3madkour-pub-assets-test/validate-and-copy-page-assets ()
  "Copies referenced page assets into bundle dir; returns :copied list."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (org-file (expand-file-name "note.org" root))
           (bundle (expand-file-name "bundle" root)))
      (make-directory bundle t)
      (make-directory (expand-file-name "page/foo" root) t)
      (with-temp-file (expand-file-name "page/foo/x.png" root) (insert "d"))
      (with-temp-file org-file (insert "[[./assets/page/foo/x.png]]"))
      (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                 (lambda (_) org-file))
                ((symbol-function 'a3madkour-pub/note-slug)
                 (lambda (_) "foo"))
                ;; published-p needs to be stubbed too for note-url etc:
                ((symbol-function 'a3madkour-pub/published-p)
                 (lambda (_) 'live)))
        (let ((result (a3madkour-pub/asset-validate-and-copy org-file bundle)))
          (should (file-exists-p (expand-file-name "x.png" bundle)))
          (should (member (expand-file-name "x.png" bundle)
                           (plist-get result :copied))))))))

(ert-deftest a3madkour-pub-assets-test/validate-and-copy-shared-asset ()
  "Shared assets copied to notes-shared dir (not bundle)."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (shared-static (expand-file-name "site/static/notes-shared" root))
           (a3madkour-pub-notes-shared-static-dir shared-static)
           (org-file (expand-file-name "note.org" root))
           (bundle (expand-file-name "bundle" root)))
      (make-directory bundle t)
      (make-directory shared-static t)
      (make-directory (expand-file-name "shared" root) t)
      (with-temp-file (expand-file-name "shared/y.svg" root) (insert "<svg/>"))
      (with-temp-file org-file (insert "[[./assets/shared/y.svg]]"))
      (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                 (lambda (_) org-file))
                ((symbol-function 'a3madkour-pub/note-slug)
                 (lambda (_) "foo")))
        (let ((result (a3madkour-pub/asset-validate-and-copy org-file bundle)))
          (should (file-exists-p (expand-file-name "y.svg" shared-static)))
          (should-not (file-exists-p (expand-file-name "y.svg" bundle))))))))

(ert-deftest a3madkour-pub-assets-test/validate-and-copy-removes-stale ()
  "Files in bundle not in current refs (and not index.md) get removed."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (org-file (expand-file-name "note.org" root))
           (bundle (expand-file-name "bundle" root)))
      (make-directory bundle t)
      ;; Pre-existing stale + index.md:
      (with-temp-file (expand-file-name "stale.png" bundle) (insert "old"))
      (with-temp-file (expand-file-name "index.md" bundle) (insert "doc"))
      ;; Current refs: empty org file.
      (with-temp-file org-file (insert "no asset refs"))
      (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                 (lambda (_) org-file))
                ((symbol-function 'a3madkour-pub/note-slug)
                 (lambda (_) "foo")))
        (let ((result (a3madkour-pub/asset-validate-and-copy org-file bundle)))
          (should-not (file-exists-p (expand-file-name "stale.png" bundle)))
          (should (file-exists-p (expand-file-name "index.md" bundle)))
          (should (member (expand-file-name "stale.png" bundle)
                           (plist-get result :removed))))))))

(ert-deftest a3madkour-pub-assets-test/validate-and-copy-aggregates-warnings ()
  "Per-link WARNs surface in :warnings."
  (a3-pub-assets-test--with-tmp-root root
    (let* ((a3madkour-pub-canonical-asset-root root)
           (org-file (expand-file-name "note.org" root))
           (bundle (expand-file-name "bundle" root)))
      (make-directory bundle t)
      (with-temp-file org-file
        (insert "[[./assets/page/foo/missing.png]]"))         ; missing source
      (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                 (lambda (_) org-file))
                ((symbol-function 'a3madkour-pub/note-slug)
                 (lambda (_) "foo")))
        (let ((result (a3madkour-pub/asset-validate-and-copy org-file bundle)))
          (should (plist-get result :warnings)))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 failures with "Symbol's function definition is void: a3madkour-pub/asset-validate-and-copy".

- [ ] **Step 3: Implement**

Append to `a3madkour-publish-assets.el`:

```elisp
(defun a3madkour-pub/asset-validate-and-copy (org-file bundle-dest-dir &optional dry-run)
  "Walk ORG-FILE for asset links; copy referenced assets; remove stale per-page assets.

For each `[[<path>][text]]' that is asset-shaped:
  - Resolve via `rewrite-asset-link' (which handles auto-remediation).
  - For `:kind page' results, copy abs-path → BUNDLE-DEST-DIR/<filename>.
  - For `:kind shared' results (resolved-path starts with `/notes-shared/'),
    copy abs-path → `a3madkour-pub-notes-shared-static-dir'/<filename>.

After all copies, remove stale per-page files (cleanup-stale).

Returns:
  (:copied   (DEST-PATH ...)
   :removed  (DEST-PATH ...)
   :warnings (WARN ...)
   :errors   (ERR ...))

DRY-RUN, when non-nil, propagates to rewrite-asset-link's auto-remediation
and suppresses file I/O for copies + cleanup."
  (let ((refs (a3madkour-pub--extract-asset-refs org-file))
        (copied nil)
        (warnings nil)
        (errors nil)
        (referenced-basenames nil))
    (dolist (ref refs)
      (let* ((path (car ref))
             (text (cdr ref))
             (rewrite-result (a3madkour-pub/rewrite-asset-link
                              path text "from-validate" dry-run))
             (src (plist-get rewrite-result :source-path))
             (resolved (plist-get rewrite-result :resolved-path)))
        ;; Always merge WARNs:
        (setq warnings (append warnings (plist-get rewrite-result :warnings)))
        ;; If :html (not :inert) AND not dry-run, perform the copy:
        (when (and (plist-get rewrite-result :html) (not dry-run) src)
          (let* ((basename (file-name-nondirectory src))
                 (dest (if (and resolved (string-prefix-p "/notes-shared/" resolved))
                           (expand-file-name basename
                                              a3madkour-pub-notes-shared-static-dir)
                         (expand-file-name basename bundle-dest-dir))))
            (make-directory (file-name-directory dest) t)
            (condition-case err
                (progn
                  (copy-file src dest t)                ; t = ok-if-already-exists
                  (push dest copied)
                  ;; Track for cleanup only when destination is the bundle:
                  (when (string-prefix-p (file-name-as-directory bundle-dest-dir) dest)
                    (push basename referenced-basenames)))
              (error
               (push (format "copy failed: %s -> %s (%S)" src dest err) errors)))))))
    (let ((removed (and (not dry-run)
                        (a3madkour-pub--asset-cleanup-stale
                         bundle-dest-dir referenced-basenames))))
      (list :copied (nreverse copied)
            :removed removed
            :warnings warnings
            :errors (nreverse errors)))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 173 tests, 173 results as expected, 0 unexpected` (169 + 4 new).

- [ ] **Step 5: Test-count checkpoint**

End of Task 18: **173 ert tests** (169 → 173). Elisp side complete.

---

### Task 19: Wire `rewrite-asset-link` into `rewrite-link` (replace `:pending-asset`)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write the failing integration tests**

Append to `a3madkour-publish-rewrite-test.el`:

```elisp
;; -- rewrite-link asset-branch integration --

(ert-deftest a3madkour-pub-rewrite-test/asset-dispatch-page ()
  "Asset-shaped link dispatches to rewrite-asset-link (no :pending-asset)."
  (let* ((root (make-temp-file "a3-pub-disp-" t))
         (a3madkour-pub-canonical-asset-root root))
    (unwind-protect
        (progn
          (make-directory (expand-file-name "page/foo" root) t)
          (with-temp-file (expand-file-name "page/foo/x.png" root) (insert "d"))
          (cl-letf (((symbol-function 'a3madkour-pub--id-to-file)
                     (lambda (_) nil))
                    ((symbol-function 'a3madkour-pub/note-slug)
                     (lambda (_) "foo")))
            (let* ((link (format "[[%s][alt]]"
                                  (expand-file-name "page/foo/x.png" root)))
                   (result (a3madkour-pub/rewrite-link link "src")))
              (should (plist-get result :html))
              (should-not (plist-get result :pending-asset)))))
      (delete-directory root t))))

(ert-deftest a3madkour-pub-rewrite-test/asset-dispatch-missing ()
  "Missing file routed to rewrite-asset-link's :inert path."
  (let* ((root (make-temp-file "a3-pub-dispm-" t))
         (a3madkour-pub-canonical-asset-root root))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub--id-to-file) (lambda (_) nil))
                  ((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "foo")))
          (let* ((link (format "[[%s/page/foo/missing.png]]" root))
                 (result (a3madkour-pub/rewrite-link link "src")))
            (should (plist-get result :inert))
            (should-not (plist-get result :pending-asset))))
      (delete-directory root t))))

(ert-deftest a3madkour-pub-rewrite-test/pending-asset-shape-removed ()
  "After A.1.c integration, no return path produces :pending-asset."
  ;; Walk through several asset shapes; none should return :pending-asset.
  (let* ((root (make-temp-file "a3-pub-noprev-" t))
         (a3madkour-pub-canonical-asset-root root))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub--id-to-file) (lambda (_) nil))
                  ((symbol-function 'a3madkour-pub/note-slug) (lambda (_) "foo")))
          (dolist (link '("[[./assets/page/foo/x.png]]"
                           "[[./assets/shared/y.svg]]"
                           "[[/tmp/somewhere/z.pdf]]"))
            (let ((result (a3madkour-pub/rewrite-link link "src")))
              (should-not (plist-get result :pending-asset)))))
      (delete-directory root t))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 3 failures — current `rewrite-link` still returns `:pending-asset` for asset-shaped links.

- [ ] **Step 3: Update `rewrite-link`'s dispatcher**

In `a3madkour-publish-rewrite.el`, locate the `:pending-asset` branch (around line 279) and REPLACE it:

```elisp
;; OLD:
;; Asset-shaped link (no scheme, non-`.org` extension) — A.1.b stub;
;; A.1.c will replace with canonical-root resolution.
((a3madkour-pub--asset-shaped-link-p path)
 (list :pending-asset org-link
       :warnings (list (format "asset link %S; rewriting deferred to A.1.c"
                                org-link))))

;; NEW:
;; Asset-shaped link (no scheme, non-`.org` extension) — A.1.c dispatch.
((a3madkour-pub--asset-shaped-link-p path)
 (a3madkour-pub/rewrite-asset-link path text source-note-id))
```

Also `require` the assets module at the top of `a3madkour-publish-rewrite.el`. Find:

```elisp
(require 'cl-lib)
(require 'a3madkour-publish)
(require 'a3madkour-publish-id)
```

And add immediately after:

```elisp
;; Forward declaration: rewrite-asset-link is in a3madkour-publish-assets.el,
;; which itself requires this file (for --html-escape).  Avoid the circular
;; require by autoloading the symbol.
(autoload 'a3madkour-pub/rewrite-asset-link "a3madkour-publish-assets")
```

Update the `rewrite-link` docstring to remove the `:pending-asset` mention (around line 252):

```elisp
;; OLD:
;;   (:pending-asset ORIG-LINK :warnings (...))  ; A.1.b stub; A.1.c upgrades

;; NEW: (delete that line)
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 176 tests, 176 results as expected, 0 unexpected` (173 + 3 new).

**Important:** existing A.1.b tests `a3madkour-pub-rewrite-test/pending-asset-*` (the 4 from Task 18 of A.1.b) will now fail because the shape changed. UPDATE them — change their assertions from `(plist-get result :pending-asset)` to `(plist-get result :inert)` for the missing-source cases (since none of those test fixtures actually exist on disk). Locate via:

```bash
grep -n "pending-asset" ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el
```

Replace each `(should (equal (plist-get result :pending-asset) ...))` with `(should (plist-get result :inert))`. Re-run the test suite.

Expected final: `Ran 176 tests, 176 results as expected, 0 unexpected`.

- [ ] **Step 5: Test-count checkpoint**

End of Task 19: **176 ert tests** (173 → 176). `:pending-asset` fully removed; asset dispatching live.

---

### Task 20: Create `tools/check_org_assets.py` (24th linter)

**Files:**
- Create: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/check_org_assets.py`

- [ ] **Step 1: Implement the linter**

Create `tools/check_org_assets.py`:

```python
#!/usr/bin/env python3
"""Org-asset link linter (24th in CI).

Walks every `content/<section>/<slug>/index.md` bundle, extracts `<img src>`,
`<a href>`, and markdown `![alt](src)` references, and verifies:

  - References starting with `/notes-shared/` resolve to existing files in
    `static/notes-shared/`.
  - Relative references (no scheme, no leading `/`, no `#`) resolve inside
    the bundle dir.
  - No `../` path traversal in any reference.
  - Orphan check: every regular file in the bundle (except `index.md`,
    `_index.md`, `index.*.md`, dotfiles) must be referenced.

External links (`http://`, `https://`, `mailto:`, `tel:`), anchor-only refs
(`#section`), and internal Hugo routes (`/garden/<slug>/`, etc.) are skipped.

Cross-namespace validation is NOT performed here (elisp-side only — Python
has no view of the org source).

Exits 0 on success, 1 on any error.  Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


# Match <img src="..."> and <a href="..."> in the bundle's index.md body.
IMG_SRC_RE = re.compile(r'<img\b[^>]*\bsrc="([^"]*)"', re.IGNORECASE)
A_HREF_RE = re.compile(r'<a\b[^>]*\bhref="([^"]*)"', re.IGNORECASE)
# Markdown image syntax ![alt](src) — future-proofing for B's slices.
MD_IMG_RE = re.compile(r'!\[[^\]]*\]\(([^)\s]+)')


# Internal Hugo routes we skip (not file references).
INTERNAL_ROUTE_PREFIXES = (
    "/about/", "/blog/", "/essays/", "/garden/", "/library/",
    "/research/", "/streams/", "/works/",
)
EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "tel:", "ftp://")
SKIP_BUNDLE_FILES = {"index.md", "_index.md"}
SKIP_BUNDLE_RE = re.compile(r"\Aindex\..+\.md\Z")  # index.<lang>.md


def _strip_frontmatter(text: str) -> str:
    m = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    return text[m.end():] if m else text


def _extract_refs(body: str) -> list[str]:
    refs: list[str] = []
    refs.extend(IMG_SRC_RE.findall(body))
    refs.extend(A_HREF_RE.findall(body))
    refs.extend(MD_IMG_RE.findall(body))
    return refs


def _classify(ref: str) -> str:
    """Return 'external' | 'anchor' | 'internal-route' | 'shared' | 'traversal'
    | 'local'."""
    if any(ref.startswith(s) for s in EXTERNAL_SCHEMES):
        return "external"
    if ref.startswith("#"):
        return "anchor"
    if ref.startswith("/notes-shared/"):
        return "shared"
    if any(ref.startswith(p) for p in INTERNAL_ROUTE_PREFIXES):
        return "internal-route"
    if ref.startswith("/"):
        # Other absolute /paths/ — treat as internal route (skip)
        return "internal-route"
    if "../" in ref:
        return "traversal"
    return "local"


def lint_bundle(bundle: Path, static_notes_shared: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    index = bundle / "index.md"
    if not index.exists():
        return errors, warnings
    body = _strip_frontmatter(index.read_text(encoding="utf-8"))
    refs = _extract_refs(body)
    referenced_locals: set[str] = set()
    for ref in refs:
        kind = _classify(ref)
        if kind in ("external", "anchor", "internal-route"):
            continue
        if kind == "traversal":
            errors.append(f"{bundle}: path traversal in ref: {ref}")
            continue
        if kind == "shared":
            target = static_notes_shared / ref[len("/notes-shared/"):]
            if not target.exists():
                errors.append(f"{bundle}: shared ref does not resolve: {ref} (looked at {target})")
            continue
        # kind == "local"
        target = bundle / ref
        if not target.exists():
            errors.append(f"{bundle}: local ref does not resolve: {ref}")
        else:
            referenced_locals.add(ref)
    # Orphan check.
    for f in sorted(bundle.iterdir()):
        if not f.is_file():
            continue
        name = f.name
        if name.startswith("."):
            continue
        if name in SKIP_BUNDLE_FILES or SKIP_BUNDLE_RE.fullmatch(name):
            continue
        if name not in referenced_locals:
            errors.append(f"{bundle}: orphan file not referenced by index.md: {name}")
    return errors, warnings


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    content_dir = repo_root / "content"
    static_notes_shared = repo_root / "static" / "notes-shared"
    if not content_dir.is_dir():
        print(f"error: {content_dir} not found", file=sys.stderr)
        return 1
    errors: list[str] = []
    warnings: list[str] = []
    bundle_count = 0
    for section in sorted(content_dir.iterdir()):
        if not section.is_dir():
            continue
        for entry in sorted(section.iterdir()):
            if not entry.is_dir():
                continue
            if not (entry / "index.md").exists():
                continue
            bundle_count += 1
            e, w = lint_bundle(entry, static_notes_shared)
            errors.extend(e)
            warnings.extend(w)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} asset-ref issue(s) across {bundle_count} bundle(s).",
              file=sys.stderr)
        return 1
    print(f"OK — verified {bundle_count} bundle(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Make it executable + run against the existing site**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
chmod +x tools/check_org_assets.py
python3 tools/check_org_assets.py
```

Expected: `OK — verified N bundle(s).` (where N matches the count of `content/<section>/<slug>/index.md` files in the repo today). If errors fire, they're real findings in the current content — investigate before continuing.

- [ ] **Step 3: Test-count checkpoint**

End of Task 20: **176 ert tests** (no elisp tests added). New Python linter shipped (test sibling added in Task 21).

---

### Task 21: Create `tools/test_check_org_assets.py` (sibling test)

**Files:**
- Create: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_check_org_assets.py`

- [ ] **Step 1: Implement the sibling test**

Create `tools/test_check_org_assets.py`:

```python
"""Unit tests for check_org_assets.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_org_assets as mod


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class TestLintBundle(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="check_org_assets_test_"))
        self.bundle = self.tmp / "bundle"
        self.static_shared = self.tmp / "static" / "notes-shared"
        self.static_shared.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _lint(self) -> tuple[list[str], list[str]]:
        return mod.lint_bundle(self.bundle, self.static_shared)

    # ---- Healthy cases -------------------------------------------------

    def test_healthy_local_and_shared(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n'
               '<img src="x.png" alt="x" />\n'
               '<img src="/notes-shared/y.svg" alt="y" />\n')
        _write(self.bundle / "x.png", "binary-data")
        _write(self.static_shared / "y.svg", "<svg/>")
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_empty_bundle(self) -> None:
        _write(self.bundle / "index.md", '---\ntitle: ok\n---\nNo refs.')
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_markdown_image_syntax(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n![alt](x.png)\n')
        _write(self.bundle / "x.png", "d")
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    # ---- Error cases ---------------------------------------------------

    def test_broken_local_ref(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<img src="missing.png" alt="" />')
        errors, _ = self._lint()
        self.assertTrue(any("missing.png" in e and "does not resolve" in e for e in errors),
                        errors)

    def test_broken_shared_ref(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<img src="/notes-shared/missing.svg" alt="" />')
        errors, _ = self._lint()
        self.assertTrue(any("missing.svg" in e and "shared ref" in e for e in errors),
                        errors)

    def test_orphan_file(self) -> None:
        _write(self.bundle / "index.md", '---\ntitle: ok\n---\nNo refs.')
        _write(self.bundle / "cruft.png", "data")
        errors, _ = self._lint()
        self.assertTrue(any("orphan" in e and "cruft.png" in e for e in errors), errors)

    def test_path_traversal(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<img src="../foo.png" alt="" />')
        errors, _ = self._lint()
        self.assertTrue(any("traversal" in e for e in errors), errors)

    # ---- Skip cases ----------------------------------------------------

    def test_external_skip(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<a href="https://example.com">x</a>')
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_anchor_skip(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<a href="#section">x</a>')
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_internal_route_skip(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<a href="/garden/other/">x</a>')
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_dotfiles_preserved(self) -> None:
        _write(self.bundle / "index.md", '---\ntitle: ok\n---\nNo refs.')
        _write(self.bundle / ".publish-state", "x")
        errors, _ = self._lint()
        self.assertEqual(errors, [])  # Dotfile is not flagged orphan


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the sibling test**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
python3 -m unittest tools/test_check_org_assets.py -v 2>&1 | tail -15
```

Expected: 11 tests pass.

- [ ] **Step 3: Test-count checkpoint**

End of Task 21: **176 ert tests + 11 Python tests** for the 24th linter pair.

---

### Task 22: Register the 24th linter pair in CI workflows

**Files:**
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.github/workflows/hugo.yaml`
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/ci-local.sh`

- [ ] **Step 1: Register in `.github/workflows/hugo.yaml`**

Find the last existing linter pair (search for `check_streams_links`):

```bash
grep -n "check_streams_links\|test_check_streams_links" \
  /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/.github/workflows/hugo.yaml
```

Add new step pair immediately AFTER `Run streams-links linter unit tests`:

```yaml
      - name: Verify org-asset references
        run: python3 tools/check_org_assets.py
      - name: Run org-assets linter unit tests
        run: python3 -m unittest tools/test_check_org_assets.py -v
```

- [ ] **Step 2: Register in `tools/ci-local.sh`**

Find the same anchor:

```bash
grep -n "check_streams_links\|test_check_streams_links" \
  /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/ci-local.sh
```

Add immediately after `python3 -m unittest tools/test_check_streams_links.py ... | tail -3`:

```bash
python3 tools/check_org_assets.py
python3 -m unittest tools/test_check_org_assets.py -v 2>&1 | tail -3
```

- [ ] **Step 3: Run ci-local.sh end-to-end**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
tools/ci-local.sh 2>&1 | tail -30
```

Expected: full CI pipeline runs; both new lines fire (`OK — verified N bundle(s)` + `OK` from unittest); final pipeline status = success.

- [ ] **Step 4: Test-count checkpoint**

End of Task 22: 24th linter pair registered in CI + ci-local.sh.

---

### Task 23: Create `tools/test_publish_integration.py` + asset-handling fixtures

**Files:**
- Create: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Implement the integration test runner**

Create `tools/test_publish_integration.py`:

```python
"""End-to-end integration tests for the elisp publish pipeline.

Each test sets up a tmp `~/org/notes/`-shaped corpus, invokes the elisp
publisher via `emacs --batch -l a3-pub.sh`, and asserts on the resulting
`content/`, `~/org/notes/assets/`, `static/notes-shared/`, and captured stdout.

Lands in A.1.c (was a parent-spec §11 placeholder until now).  Initial
fixture set covers A.1.c's asset-handling scope; future slices append.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


DOTFILES = Path.home() / "dotfiles" / "emacs-configs" / "custom" / "lisp"
A3_PUB_SH = DOTFILES / "a3-pub.sh"


def _emacs_eval(forms: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run `emacs --batch` with the publish library loaded and FORMS evaluated."""
    args = ["emacs", "--batch", "-Q",
            "-L", str(DOTFILES),
            "-l", "a3madkour-publish.el",
            "-l", "a3madkour-publish-id.el",
            "-l", "a3madkour-publish-rewrite.el",
            "-l", "a3madkour-publish-assets.el"]
    for form in forms:
        args.extend(["--eval", form])
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60)


class TestAssetHandling(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="a3-pub-integ-"))
        self.notes_root = self.tmp / "notes"
        self.assets_root = self.notes_root / "assets"
        self.site_root = self.tmp / "site"
        self.bundle = self.site_root / "content" / "garden" / "foo"
        self.shared_static = self.site_root / "static" / "notes-shared"
        for p in (self.notes_root, self.assets_root, self.bundle, self.shared_static):
            p.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    # Common setup helper: write an org file + return the asset link path
    def _setup_note_with_asset(self, asset_subpath: str, body_link: str) -> Path:
        org = self.notes_root / "foo.org"
        asset = self.assets_root / asset_subpath
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_text("binary-content", encoding="utf-8")
        org.write_text(f"Note text.\n{body_link}\n", encoding="utf-8")
        return org

    def test_canonical_page_asset_lands_in_bundle(self) -> None:
        self._setup_note_with_asset(
            "page/foo/diagram.png",
            f"[[./assets/page/foo/diagram.png][Diagram]]",
        )
        result = _emacs_eval(
            [
                f'(setq a3madkour-pub-canonical-asset-root {self.assets_root!r})',
                f'(setq a3madkour-pub-notes-shared-static-dir {self.shared_static!r})',
                f'(a3madkour-pub/asset-validate-and-copy {(self.notes_root / "foo.org")!r} {self.bundle!r})',
            ],
            cwd=self.tmp,
        )
        self.assertTrue((self.bundle / "diagram.png").exists(), result.stderr)

    def test_shared_asset_lands_in_notes_shared(self) -> None:
        self._setup_note_with_asset(
            "shared/common.svg",
            f"[[./assets/shared/common.svg][Shared]]",
        )
        result = _emacs_eval(
            [
                f'(setq a3madkour-pub-canonical-asset-root {self.assets_root!r})',
                f'(setq a3madkour-pub-notes-shared-static-dir {self.shared_static!r})',
                f'(a3madkour-pub/asset-validate-and-copy {(self.notes_root / "foo.org")!r} {self.bundle!r})',
            ],
            cwd=self.tmp,
        )
        self.assertTrue((self.shared_static / "common.svg").exists(), result.stderr)
        self.assertFalse((self.bundle / "common.svg").exists())

    def test_stale_asset_removed(self) -> None:
        org = self.notes_root / "foo.org"
        org.write_text("No asset refs.\n", encoding="utf-8")
        # Pre-existing stale + index.md:
        (self.bundle / "index.md").write_text("doc", encoding="utf-8")
        (self.bundle / "stale.png").write_text("old", encoding="utf-8")
        result = _emacs_eval(
            [
                f'(setq a3madkour-pub-canonical-asset-root {self.assets_root!r})',
                f'(setq a3madkour-pub-notes-shared-static-dir {self.shared_static!r})',
                f'(a3madkour-pub/asset-validate-and-copy {org!r} {self.bundle!r})',
            ],
            cwd=self.tmp,
        )
        self.assertFalse((self.bundle / "stale.png").exists(), result.stderr)
        self.assertTrue((self.bundle / "index.md").exists())

    def test_missing_asset_emits_warning(self) -> None:
        org = self.notes_root / "foo.org"
        org.write_text(
            "[[./assets/page/foo/never-existed.png]]\n", encoding="utf-8"
        )
        result = _emacs_eval(
            [
                f'(setq a3madkour-pub-canonical-asset-root {self.assets_root!r})',
                f'(setq a3madkour-pub-notes-shared-static-dir {self.shared_static!r})',
                f'(message "%S" (a3madkour-pub/asset-validate-and-copy {org!r} {self.bundle!r}))',
            ],
            cwd=self.tmp,
        )
        self.assertIn("does not exist", result.stderr + result.stdout, result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the integration test**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
python3 -m unittest tools/test_publish_integration.py -v 2>&1 | tail -20
```

Expected: 4 tests pass. If emacs is not on PATH, the test will fail with a clear error — install emacs or run from a shell where it's accessible.

(Note: this file is the §11 placeholder finally landed. It uses real `emacs --batch` invocation; CI should have emacs installed already since the dotfiles tests run there.)

- [ ] **Step 3: Test-count checkpoint**

End of Task 23: **176 ert + 11 + 4 Python tests**. Integration test landed (3 more fixtures — cross-namespace, auto-remediate, dry-run — could be added if time permits, OR deferred to a follow-up).

---

### Task 24: USER VERIFICATION CHECKPOINT

This is for the human author. Per spec §11, every implementation stage gets a manual checkpoint.

- [ ] **Step 1: Author runs the full test suite**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: `Ran 176 tests, 176 results as expected, 0 unexpected`. Exit `0`.

Run: `cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io && tools/ci-local.sh 2>&1 | tail -10`
Expected: Full CI pipeline including the new `check_org_assets.py` step passes.

- [ ] **Step 2: Spot-check via `a3-pub.sh` — page asset**

Pick a published note in `~/org/notes/` with at least one asset reference. If none exist, manually set up a tmpdir corpus:

```bash
mkdir -p /tmp/a3-spot/notes/assets/page/spotcheck
cp <some-image.png> /tmp/a3-spot/notes/assets/page/spotcheck/
cat > /tmp/a3-spot/notes/spotcheck.org <<'ORG'
:PROPERTIES:
:ID: spot-check-id-0001
:END:
#+TITLE: Spot check
#+HUGO_PUBLISH: t

Here is an asset: [[./assets/page/spotcheck/some-image.png][test image]].
ORG

mkdir -p /tmp/a3-spot/site/content/garden/spotcheck
mkdir -p /tmp/a3-spot/site/static/notes-shared

~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh \
  --eval "(setq a3madkour-pub-canonical-asset-root \"/tmp/a3-spot/notes/assets\")" \
  --eval "(setq a3madkour-pub-notes-shared-static-dir \"/tmp/a3-spot/site/static/notes-shared\")" \
  --eval "(message \"%S\" (a3madkour-pub/rewrite-asset-link \"/tmp/a3-spot/notes/assets/page/spotcheck/some-image.png\" \"test image\" \"spot-check-id-0001\"))"
```

Expected message:
```
(:html "<img src=\"some-image.png\" alt=\"test image\" />"
 :resolved-path "some-image.png"
 :source-path "/tmp/a3-spot/notes/assets/page/spotcheck/some-image.png"
 :kind image
 :warnings nil)
```

- [ ] **Step 3: Spot-check the asset-validate-and-copy end-to-end**

```bash
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh \
  --eval "(setq a3madkour-pub-canonical-asset-root \"/tmp/a3-spot/notes/assets\")" \
  --eval "(setq a3madkour-pub-notes-shared-static-dir \"/tmp/a3-spot/site/static/notes-shared\")" \
  --eval "(message \"%S\" (a3madkour-pub/asset-validate-and-copy \"/tmp/a3-spot/notes/spotcheck.org\" \"/tmp/a3-spot/site/content/garden/spotcheck\"))"

ls -la /tmp/a3-spot/site/content/garden/spotcheck/
```

Expected: the directory now contains `some-image.png`. The captured message includes `:copied` with the full destination path.

- [ ] **Step 4: Spot-check auto-remediation with a real out-of-root file**

```bash
echo "test-content" > /tmp/oor-asset.png
cat > /tmp/a3-spot/notes/oor-note.org <<'ORG'
:PROPERTIES:
:ID: oor-id-0001
:END:
#+TITLE: Out-of-root
#+HUGO_PUBLISH: t

[[/tmp/oor-asset.png][screenshot]]
ORG

~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh \
  --eval "(setq a3madkour-pub-canonical-asset-root \"/tmp/a3-spot/notes/assets\")" \
  --eval "(message \"%S\" (a3madkour-pub/rewrite-asset-link \"/tmp/oor-asset.png\" \"screenshot\" \"oor-id-0001\"))"

# Verify the file moved + the .org source was rewritten:
ls -la /tmp/a3-spot/notes/assets/page/oor-note/
diff <(cat /tmp/a3-spot/notes/oor-note.org) - <<'EXPECTED'
:PROPERTIES:
:ID: oor-id-0001
:END:
#+TITLE: Out-of-root
#+HUGO_PUBLISH: t

[[./assets/page/oor-note/oor-asset.png][screenshot]]
EXPECTED
```

Expected: asset moved into `~/org/notes/assets/page/oor-note/`; `.org` link rewritten in place; INFO log printed.

(If `oor-note` doesn't match the source-slug in the elisp `note-slug` impl for the spot-check id, adjust the test: the goal is verifying the move + source rewrite mechanism. Authors with real `published-p` set up may need to stub differently.)

- [ ] **Step 5: Spot-check the Python linter against the live site**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
python3 tools/check_org_assets.py
```

Expected: `OK — verified N bundle(s).` against the current `content/` tree. If errors fire, they're real — investigate before declaring A.1.c done.

- [ ] **Step 6: Hugo build still succeeds end-to-end**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
hugo --minify 2>&1 | tail -5
```

Expected: Hugo build completes with no errors.

- [ ] **Step 7: Author confirms readiness for A.1.d**

Author affirms that A.1.c is sound and the next plan (A.1.d — unpublish flow + integration test expansion) can begin.

---

### Task 25: Update site repo `CLAUDE.md`

**Files:**
- Modify: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md`

- [ ] **Step 1: Locate the lines to update**

```bash
grep -n "Twenty-three linter pairs\|A.1.0 (bootstrap)" \
  /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md
```

- [ ] **Step 2: Bump linter count + register A.1.c shipped**

In `CLAUDE.md`, find the line beginning `- Twenty-three linter pairs under` and update:

```
- OLD: Twenty-three linter pairs under ...
- NEW: Twenty-four linter pairs under ...
```

Also append `org-asset references` to the comma-separated list of linter-pair names in the same sentence (alphabetical position with the rest).

In the same file, find the Phase 3 sub-project A bullet (where A.1.b shipped was recorded):

```
- OLD: ... A.1.b (link rewriter) implementation complete; 109 ert tests passing. A.1.c (asset handling + 24th linter pair) is the next plan. ...
- NEW: ... A.1.b (link rewriter) + A.1.c (asset handling + 24th linter pair) implementation complete; 176 ert tests passing. A.1.d (unpublish flow + integration tests) is the next plan. ...
```

Also update the `memory/project_a1b_complete.md` reference to `memory/project_a1c_complete.md` (will be created at session end).

- [ ] **Step 3: Update CI workflow step count**

Find the line "Total: 59 named steps." and update to "Total: 61 named steps." (added 2 steps: the linter + the unit-test sibling).

- [ ] **Step 4: Test-count checkpoint**

End of Task 25: docs-only commit; no test count change.

---

### Task 26: Stage files for author commit (default no-commit session policy)

Per session policy default, the agent stages but does NOT commit. Skip this task if the author signaled "commit as you go" at session start.

- [ ] **Step 1: Stage dotfiles changes**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-rewrite.el \
        emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-assets.el \
        emacs-configs/custom/lisp/a3madkour-publish-assets-test.el \
        emacs-configs/custom/lisp/run-tests.sh
git status --short emacs-configs/custom/lisp/
```

Expected: 5 files listed (2 modified + 2 new + 1 modified test runner).

- [ ] **Step 2: Stage site-repo changes**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/check_org_assets.py \
        tools/test_check_org_assets.py \
        tools/test_publish_integration.py \
        .github/workflows/hugo.yaml \
        tools/ci-local.sh \
        CLAUDE.md \
        docs/superpowers/plans/2026-05-23-phase-3-a1-c-asset-handling.md
git status --short
```

Expected: 7 files staged (3 new tools + 2 modified workflows + CLAUDE.md + plan doc).

- [ ] **Step 3: Suggested commit messages (author runs)**

In dotfiles:

```bash
git commit -m "feat(publish): A.1.c asset handling + html-escape helper

Sub-project A.1.c of the Phase 3 org→Hugo publish pipeline.

- a3madkour-publish-assets.el (NEW): canonical-root resolution, cross-
  namespace validation, auto-remediation (default ON, --dry-run preview),
  per-bundle copy + stale cleanup. rewrite-asset-link + asset-validate-and-
  copy are the public entry points (called by rewrite-link's dispatcher
  + B's per-section publisher respectively).
- a3madkour-publish-rewrite.el: add a3madkour-pub--html-escape (single
  chokepoint per parent spec §6); retrofit 3 existing :html emit points
  (id-link, typed-link via id-link reuse, external). Replace :pending-asset
  dispatcher branch with call to rewrite-asset-link.

Test count progression: 109 (end A.1.b) → 176 (end A.1.c). All passing.

Auto-remediation: SHA-1 first 6 hex chars suffix on filename collision;
git-mv if vc-tracked, mv otherwise; org-source link rewritten in place
(visible side effect, author sees both move + rewrite in git status).

Carried forward to A.1.d: slug-shift asset dir rename, shared-asset
conflict resolution, --strict flag plumbing."
```

In site repo:

```bash
git commit -m "ci(linters): A.1.c — 24th linter pair (check_org_assets.py)

Sub-project A.1.c ships the 24th linter pair + integration test runner +
plan doc + CLAUDE.md update.

- tools/check_org_assets.py: walks content/<section>/<slug>/ bundles,
  verifies <img src> + <a href> + markdown ![alt](src) references resolve
  (local in bundle; shared in static/notes-shared/); flags orphans + path
  traversal. Cross-namespace stays elisp-only.
- tools/test_check_org_assets.py: 11 sibling tests.
- tools/test_publish_integration.py: 4 end-to-end asset-handling fixtures
  (parent spec §11 placeholder finally landed).
- .github/workflows/hugo.yaml + tools/ci-local.sh: register the linter pair.
- CLAUDE.md: bump linter count 23→24; note A.1.c shipped; bump CI step count
  59→61; update next-slice pointer to A.1.d."
```

- [ ] **Step 4: Test-count checkpoint**

End of Task 26: Final test count locked at **176 ert + 11 + 4 Python tests**. Plan complete.

---

## Self-Review

**Spec coverage (design doc + parent spec):**
- ✅ Rewriter return shape (hybrid HTML + path metadata) — Task 14 establishes; Task 15 extends with remediation.
- ✅ Asset resolution algorithm (§5 Steps 1-3) — Task 6 (normalize + classify); Task 7 (cross-namespace); Task 14 (dispatch by kind).
- ✅ Auto-remediation flow (§5 Step 4) — Tasks 10 (hash), 11 (dest+collision), 12 (do-move git-mv-vs-mv-vs-dryrun), 13 (source rewrite), 15 (integration).
- ✅ HTML emission (§5 Step 5) — Task 9 (emit helpers); Task 14 (uses them).
- ✅ Image extension defcustom (§5 §image-exts) — Task 5 (defcustom) + Task 9 (classification).
- ✅ Stale cleanup blacklist (§7) — Task 17.
- ✅ HTML escape helper retrofit (§6 + this session's amendment) — Tasks 1-4.
- ✅ Python linter (§8) — Tasks 20-22.
- ✅ Integration test landed (§11 placeholder) — Task 23.
- ✅ Three layers of testing (§9) — Layer 1: Tasks 1-19 (elisp ert); Layer 2: Tasks 20-22 (Python linter + sibling); Layer 3: Task 23 (integration).
- ✅ Per-stage manual verification (§9) — Task 24.
- ✅ File inventory (§10) — Created/modified files match exactly.
- ✅ Commit layout (§11) — Task 26 surfaces the suggested commits.
- ✅ Open carry-forwards (§12) — slug-shift, shared-conflict, --strict; all explicitly stated in commit message + design doc references.

**Type consistency check:**
- `(:html STRING :resolved-path PATH :source-path SRC :kind image|other :warnings (...))` — used consistently in Tasks 14, 15, 18, 19 + design §4.
- `(:inert STRING :warnings (...))` — used consistently in Tasks 14, 15, 19.
- `(a3madkour-pub--asset-resolve-path PATH SOURCE-FILE)` signature consistent across Tasks 6, 14, 15, 18.
- `(a3madkour-pub--asset-bundle-dest RESOLVED BUNDLE-DIR)` consistent Tasks 8 → reference in 18.
- `(a3madkour-pub/rewrite-asset-link PATH TEXT SOURCE-NOTE-ID &optional DRY-RUN)` consistent Tasks 14, 15, 18, 19 + design §6.
- `(a3madkour-pub/asset-validate-and-copy ORG-FILE BUNDLE-DEST-DIR &optional DRY-RUN)` consistent Task 18, 23 + design §6.

**Placeholder scan:**
- No "TBD", "TODO", "implement later", "add appropriate error handling", "similar to Task N" without repeating code.
- Test fixtures all have explicit assertions.
- Auto-remediation source-link rewrite handles both `[[path]]` (no display text) AND `[[path][text]]` (with display) — Task 15 step 3 makes this explicit.
- Edge case noted in Task 24 step 4: if note-slug differs from oor-note in spot-check, author adjusts test — flagged in plan, not deferred.

**Scope check:**
- Single A.1.c slice. 26 tasks, 5 stages (escape retrofit 1-4 / asset core 5-13 / dispatch + helpers 14-19 / Python linter 20-22 / integration + verification + commit 23-26). Each task is bite-sized (2-5 min execution).
- Three explicit carry-forwards punted to A.1.d (slug-shift rename, shared conflict, --strict). Spec §12 + Task 26's commit message.

**Test count progression:**
- 109 (start, A.1.b end) → 116 (Task 1) → 118 (Task 2) → 119 (Task 3) → 121 (Task 4) → 121 (Task 5 — skeleton, no tests) → 127 (Task 6) → 131 (Task 7) → 134 (Task 8) → 141 (Task 9) → 143 (Task 10) → 146 (Task 11) → 149 (Task 12) → 152 (Task 13) → 158 (Task 14) → 161 (Task 15) → 165 (Task 16) → 169 (Task 17) → 173 (Task 18) → 176 (Task 19). Final = **176 ert + 11 Python sibling + 4 Python integration**.
