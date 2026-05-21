# Phase 3 A.1.a — Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Session policy:** the controlling author has set a no-commit-this-session policy. Stage files with `git add` but do NOT git-commit autonomously. Final task surfaces suggested commit messages for the author.

**Goal:** Implement the foundational A.1 surface: per-file org keyword parsing (`HUGO_PUBLISH` / `HUGO_SECTION` / `HUGO_DRAFT` / `HUGO_SLUG` / `HUGO_ALIASES`), section enum validation, slug derivation (title-derived + override), public API (`published-p` / `note-url` / `note-section`), and the URL-history manifest (`data/url-history.yaml`) with record-publish + aliases-for. All TDD.

**Architecture:** The library splits across four `.el` files under `~/dotfiles/emacs-configs/custom/lisp/`, each with a sibling `-test.el`. `a3madkour-publish.el` is the public entry point; `-keywords.el`, `-slug.el`, `-history.el` are focused subsystems consumed by the entry point. `yaml.el` (zkry's pure-elisp YAML parser) is added via straight.el for manifest I/O. A new state file `data/url-history.yaml` lands in the site repo.

**Tech Stack:** Emacs 30.2 + ert (built-in) + yaml.el (straight.el-installed) + bash (the existing `run-tests.sh` wrapper auto-discovers new `-test.el` files).

**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §4, §5, §8, §10.

**Prior plan:** `docs/superpowers/plans/2026-05-20-phase-3-a1-0-bootstrap.md` (A.1.0 bootstrap — must be complete + verified before starting).

---

## File Structure

**Modified (dotfiles repo):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` — adds: section enum constant, `published-p`, `note-url`, `note-section`, two defcustoms (`org-notes-dir`, `site-data-dir`), requires the three new sibling files
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el` — adds: tests for the public API

**Created (dotfiles repo):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords.el` — keyword extraction helpers
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords-test.el`
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-slug.el` — slug derivation
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-slug-test.el`
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el` — URL-history manifest
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

**Created (site repo):**
- `data/url-history.yaml` — initial empty manifest (`{notes: []}`)

**Out of scope** (deferred to A.1.b/c/d):
- Link rewriting (A.1.b)
- Asset handling (A.1.c)
- Unpublish flow (A.1.d)
- File-vs-ID dispatching for `published-p` etc. — A.1.a takes file paths only; A.1.b adds the ID→file lookup layer using `org-roam-id-find`

---

### Task 1: Install `yaml.el` via straight.el

**Files:**
- None created/modified — this is an emacs-side package install + verify.

- [ ] **Step 1: Check whether yaml.el is already loadable**

Run:
```bash
emacs --batch --eval "(condition-case err (progn (require 'yaml) (message \"yaml ok: %s\" (yaml-parse-string \"foo: 1\"))) (error (message \"yaml missing: %s\" err)))"
```

If output begins with `yaml ok:`, skip to Step 4 (already installed). If output begins with `yaml missing:`, continue to Step 2.

- [ ] **Step 2: Install via straight.el in a one-shot batch invocation**

Run:
```bash
emacs --batch \
  -l ~/dotfiles/emacs-configs/custom/straight/repos/straight.el/bootstrap.el \
  --eval "(straight-use-package 'yaml)" \
  --eval "(message \"installed: %s\" (locate-library \"yaml\"))"
```

Expected: a long install log, then a final line like `installed: /home/a3madkour/dotfiles/emacs-configs/custom/straight/build/yaml/yaml.el`.

If the bootstrap path doesn't exist, find it with: `find ~/dotfiles/emacs-configs/custom/straight -name "bootstrap.el" -path "*/straight.el/*"` and use the discovered path.

- [ ] **Step 3: Re-run the load check**

Run:
```bash
emacs --batch --eval "(progn (require 'yaml) (message \"yaml ok: %s\" (yaml-parse-string \"foo: 1\")))"
```

Expected: `yaml ok: #s(hash-table ...)` (yaml returns a hash table by default).

- [ ] **Step 4: Note in config.org for permanence**

The straight install above lives in the straight cache. For the dependency to be picked up on the author's next emacs start, add a one-liner to the author's config.org under the "Exporting to website" section.

**Author action (manual; not for agent to commit):** open `~/dotfiles/emacs-configs/custom/config.org`, find the `*** Exporting to website` heading (around line 2962 per the Explore agent's earlier mapping), and ensure an emacs-lisp block under it contains:

```elisp
(straight-use-package 'yaml)
(require 'yaml)
```

Then re-tangle (`C-c C-v t` from within config.org) so `config.el` carries the change. Skip if already present.

This is a manual step because we don't want the agent rewriting the author's literate config without explicit approval. Tracked here as part of the plan; not enforced by tests.

---

### Task 2: Define the section taxonomy enum + validator

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

- [ ] **Step 1: Write the failing test**

Open `a3madkour-publish-test.el` and append:

```elisp
;; -- Section enum --

(ert-deftest a3madkour-pub-test/sections-includes-known-values ()
  "The section enum includes every section documented in the design spec."
  (dolist (s '("essays" "garden"
               "research/themes" "research/questions"
               "works/games" "works/music" "works/poetry"
               "library/reading" "library/listening" "library/playing" "library/watching"
               "streams" "about"))
    (should (a3madkour-pub/valid-section-p s))))

(ert-deftest a3madkour-pub-test/sections-rejects-unknown-values ()
  "The section enum rejects typos and unknown values."
  (should-not (a3madkour-pub/valid-section-p "esays"))
  (should-not (a3madkour-pub/valid-section-p "garden/topic"))
  (should-not (a3madkour-pub/valid-section-p ""))
  (should-not (a3madkour-pub/valid-section-p nil)))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -20`
Expected: failures for `sections-includes-known-values` and `sections-rejects-unknown-values` with "Symbol's function definition is void: a3madkour-pub/valid-section-p" or similar.

- [ ] **Step 3: Implement**

Open `a3madkour-publish.el`. After the existing `defconst a3madkour-pub/version` line and before `(provide 'a3madkour-publish)`, insert:

```elisp
(defconst a3madkour-pub/sections
  '("essays"
    "garden"
    "research/themes" "research/questions"
    "works/games" "works/music" "works/poetry"
    "library/reading" "library/listening" "library/playing" "library/watching"
    "streams"
    "about")
  "Permitted values for the org-side `#+HUGO_SECTION:' keyword.
See docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md §4.")

(defun a3madkour-pub/valid-section-p (s)
  "Return non-nil iff S is a string matching one of `a3madkour-pub/sections'."
  (and (stringp s)
       (member s a3madkour-pub/sections)
       t))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 3 tests, 3 results as expected, 0 unexpected`.

---

### Task 3: Create `a3madkour-publish-keywords.el` skeleton + test file

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords-test.el`

- [ ] **Step 1: Write the keywords library shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords.el`

Content:

```elisp
;;; a3madkour-publish-keywords.el --- Keyword extraction helpers -*- lexical-binding: t; -*-

;;; Commentary:

;; Extract `#+KEYWORD: value' lines from an org buffer / file.  Used by the
;; main `a3madkour-publish' library.  Pure functions — no side effects.

;;; Code:

(provide 'a3madkour-publish-keywords)

;;; a3madkour-publish-keywords.el ends here
```

- [ ] **Step 2: Write the keywords test file shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords-test.el`

Content:

```elisp
;;; a3madkour-publish-keywords-test.el --- Tests for keyword extraction -*- lexical-binding: t; -*-

;;; Code:

(require 'ert)
(require 'a3madkour-publish-keywords)

(provide 'a3madkour-publish-keywords-test)

;;; a3madkour-publish-keywords-test.el ends here
```

- [ ] **Step 3: Verify wrapper picks up new test file + still green**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 3 tests, 3 results as expected, 0 unexpected` (no new tests yet; existing ones still pass).

---

### Task 4: Implement generic keyword extraction

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords-test.el`

- [ ] **Step 1: Write the failing tests**

Open `a3madkour-publish-keywords-test.el` and append (before the `provide` form):

```elisp
(ert-deftest a3madkour-pub-keywords-test/extract-finds-keyword-value ()
  "extract-keyword returns the value string for a present keyword."
  (with-temp-buffer
    (insert "#+title: My Note\n#+HUGO_PUBLISH: t\n* Body\n")
    (should (equal "My Note"
                   (a3madkour-pub-keywords/extract "title")))
    (should (equal "t"
                   (a3madkour-pub-keywords/extract "HUGO_PUBLISH")))))

(ert-deftest a3madkour-pub-keywords-test/extract-returns-nil-when-absent ()
  "extract-keyword returns nil if the keyword line is missing."
  (with-temp-buffer
    (insert "#+title: My Note\n* Body\n")
    (should (null (a3madkour-pub-keywords/extract "HUGO_PUBLISH")))))

(ert-deftest a3madkour-pub-keywords-test/extract-is-case-insensitive-on-key ()
  "Org keywords are case-insensitive; the helper matches both `HUGO_PUBLISH' and `hugo_publish'."
  (with-temp-buffer
    (insert "#+hugo_publish: t\n* Body\n")
    (should (equal "t" (a3madkour-pub-keywords/extract "HUGO_PUBLISH")))))

(ert-deftest a3madkour-pub-keywords-test/extract-trims-trailing-whitespace ()
  "Values are trimmed of leading/trailing whitespace."
  (with-temp-buffer
    (insert "#+HUGO_SECTION:  garden   \n* Body\n")
    (should (equal "garden"
                   (a3madkour-pub-keywords/extract "HUGO_SECTION")))))

(ert-deftest a3madkour-pub-keywords-test/extract-returns-empty-string-for-bare-keyword ()
  "Keyword with no value returns empty string, not nil."
  (with-temp-buffer
    (insert "#+HUGO_DRAFT:\n* Body\n")
    (should (equal "" (a3madkour-pub-keywords/extract "HUGO_DRAFT")))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -20`
Expected: 5 new failures, all "Symbol's function definition is void: a3madkour-pub-keywords/extract".

- [ ] **Step 3: Implement**

Open `a3madkour-publish-keywords.el`. Before the `provide` form, insert:

```elisp
(defun a3madkour-pub-keywords/extract (key)
  "Return the value of org keyword KEY in the current buffer, or nil if absent.

Matches `#+KEY: value' lines case-insensitively on the key.  The value is
trimmed of surrounding whitespace.  A keyword present with no value returns
an empty string \"\" (distinguishable from absent → nil)."
  (save-excursion
    (save-restriction
      (widen)
      (goto-char (point-min))
      (let ((case-fold-search t)
            (re (format "^#\\+%s:\\(.*\\)$" (regexp-quote key))))
        (when (re-search-forward re nil t)
          (string-trim (match-string 1)))))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 8 tests, 8 results as expected, 0 unexpected`.

---

### Task 5: Boolean keyword parsing

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-keywords-test.el` before the `provide` form:

```elisp
(ert-deftest a3madkour-pub-keywords-test/boolean-true ()
  "`t' (case-insensitive) is the only truthy value."
  (should (a3madkour-pub-keywords/boolean-p "t"))
  (should (a3madkour-pub-keywords/boolean-p "T"))
  (should-not (a3madkour-pub-keywords/boolean-p "true"))
  (should-not (a3madkour-pub-keywords/boolean-p "yes"))
  (should-not (a3madkour-pub-keywords/boolean-p "1"))
  (should-not (a3madkour-pub-keywords/boolean-p ""))
  (should-not (a3madkour-pub-keywords/boolean-p nil)))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 1 new failure for `boolean-true`.

- [ ] **Step 3: Implement**

In `a3madkour-publish-keywords.el`, before the `provide`, insert:

```elisp
(defun a3madkour-pub-keywords/boolean-p (v)
  "Return non-nil iff V is the string \"t\" (case-insensitive).
Used for `#+HUGO_PUBLISH:' and `#+HUGO_DRAFT:' parsing.  The contract is
deliberately strict — \"true\"/\"yes\"/\"1\" do NOT count, only \"t\"."
  (and (stringp v)
       (string-match-p "\\`[Tt]\\'" v)
       t))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 9 tests, 9 results as expected, 0 unexpected`.

---

### Task 6: HUGO_ALIASES list parsing

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-keywords-test.el`

- [ ] **Step 1: Write the failing tests**

Append:

```elisp
(ert-deftest a3madkour-pub-keywords-test/aliases-splits-whitespace ()
  "HUGO_ALIASES values are whitespace-separated."
  (should (equal '("/garden/old/" "/garden/older/")
                 (a3madkour-pub-keywords/parse-aliases "/garden/old/ /garden/older/"))))

(ert-deftest a3madkour-pub-keywords-test/aliases-splits-commas-too ()
  "Commas are accepted as separators in addition to whitespace (forgiving)."
  (should (equal '("/garden/old/" "/garden/older/")
                 (a3madkour-pub-keywords/parse-aliases "/garden/old/, /garden/older/"))))

(ert-deftest a3madkour-pub-keywords-test/aliases-empty-input-nil ()
  (should (null (a3madkour-pub-keywords/parse-aliases nil)))
  (should (null (a3madkour-pub-keywords/parse-aliases "")))
  (should (null (a3madkour-pub-keywords/parse-aliases "   "))))

(ert-deftest a3madkour-pub-keywords-test/aliases-trims-empties ()
  (should (equal '("/garden/x/")
                 (a3madkour-pub-keywords/parse-aliases "  /garden/x/  ,  "))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: 4 new failures for `parse-aliases`.

- [ ] **Step 3: Implement**

In `a3madkour-publish-keywords.el`, before the `provide`, insert:

```elisp
(defun a3madkour-pub-keywords/parse-aliases (v)
  "Parse HUGO_ALIASES value V (a string or nil) into a list of URL strings.
Accepts whitespace and commas as separators.  Drops empty tokens.  Returns
nil for nil / empty / whitespace-only input."
  (when (and (stringp v) (not (string-blank-p v)))
    (let ((parts (split-string v "[ \t\n,]+" t "[ \t\n]+")))
      (and parts (delq nil parts)))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 13 tests, 13 results as expected, 0 unexpected`.

---

### Task 7: Create `a3madkour-publish-slug.el` skeleton + test file

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-slug.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-slug-test.el`

- [ ] **Step 1: Write the slug library shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-slug.el`

Content:

```elisp
;;; a3madkour-publish-slug.el --- Slug derivation -*- lexical-binding: t; -*-

;;; Commentary:

;; Convert a title string to a URL slug.  Lowercase, ASCII-fold (Unicode
;; normalization), spaces → hyphens, strip punctuation.

;;; Code:

(provide 'a3madkour-publish-slug)

;;; a3madkour-publish-slug.el ends here
```

- [ ] **Step 2: Write the slug test file shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-slug-test.el`

Content:

```elisp
;;; a3madkour-publish-slug-test.el --- Tests for slug derivation -*- lexical-binding: t; -*-

;;; Code:

(require 'ert)
(require 'a3madkour-publish-slug)

(provide 'a3madkour-publish-slug-test)

;;; a3madkour-publish-slug-test.el ends here
```

- [ ] **Step 3: Verify wrapper still green**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 13 tests, 13 results as expected, 0 unexpected`.

---

### Task 8: Slugify function

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-slug.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-slug-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-slug-test.el` before the `provide`:

```elisp
(ert-deftest a3madkour-pub-slug-test/basic-ascii ()
  (should (equal "bayesian-statistics" (a3madkour-pub-slug/slugify "Bayesian Statistics"))))

(ert-deftest a3madkour-pub-slug-test/lowercase-and-hyphens ()
  (should (equal "my-note-title" (a3madkour-pub-slug/slugify "My Note Title"))))

(ert-deftest a3madkour-pub-slug-test/strip-punctuation ()
  (should (equal "whats-going-on" (a3madkour-pub-slug/slugify "What's going on?!")))
  (should (equal "foo-bar" (a3madkour-pub-slug/slugify "foo / bar")))
  (should (equal "x-y-z" (a3madkour-pub-slug/slugify "x_y_z"))))

(ert-deftest a3madkour-pub-slug-test/collapse-runs ()
  "Runs of hyphens collapse to one."
  (should (equal "a-b" (a3madkour-pub-slug/slugify "a   b")))
  (should (equal "a-b" (a3madkour-pub-slug/slugify "a---b")))
  (should (equal "a-b" (a3madkour-pub-slug/slugify "a..b"))))

(ert-deftest a3madkour-pub-slug-test/strip-leading-trailing-hyphens ()
  (should (equal "foo" (a3madkour-pub-slug/slugify "  foo  ")))
  (should (equal "foo" (a3madkour-pub-slug/slugify "-foo-")))
  (should (equal "foo" (a3madkour-pub-slug/slugify "...foo..."))))

(ert-deftest a3madkour-pub-slug-test/unicode-ascii-fold ()
  "Non-ASCII letters are folded to ASCII where possible (NFKD)."
  (should (equal "cafe" (a3madkour-pub-slug/slugify "Café")))
  (should (equal "naive" (a3madkour-pub-slug/slugify "naïve"))))

(ert-deftest a3madkour-pub-slug-test/non-ascii-unfoldable-drops ()
  "Non-foldable characters (e.g., Arabic, CJK) drop entirely; author should set HUGO_SLUG."
  (should (equal "" (a3madkour-pub-slug/slugify "بسم الله")))
  (should (equal "" (a3madkour-pub-slug/slugify "私"))))

(ert-deftest a3madkour-pub-slug-test/empty-or-nil ()
  (should (equal "" (a3madkour-pub-slug/slugify "")))
  (should (equal "" (a3madkour-pub-slug/slugify "   ")))
  (should (equal "" (a3madkour-pub-slug/slugify nil))))

(ert-deftest a3madkour-pub-slug-test/camel-case-not-split ()
  "camelCase is NOT split — author uses HUGO_SLUG for camelCase filenames.
This test documents the deliberate behavior so a future contributor doesn't
add a `camel→kebab' transform without considering existing notes."
  (should (equal "darwichetractablebooleanarithmetic2022"
                 (a3madkour-pub-slug/slugify "darwicheTractableBooleanArithmetic2022"))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -20`
Expected: 9 new failures for `slugify`.

- [ ] **Step 3: Implement**

In `a3madkour-publish-slug.el`, before the `provide`, insert:

```elisp
(defun a3madkour-pub-slug--ascii-fold (s)
  "Decompose S to NFKD and drop combining marks, leaving ASCII where possible."
  (let* ((decomposed (ucs-normalize-NFKD-string s)))
    (replace-regexp-in-string "\\cM" "" decomposed)))

(defun a3madkour-pub-slug/slugify (title)
  "Convert TITLE (string or nil) to a URL slug.

Rules (in order):
  1. nil / empty → \"\".
  2. NFKD-normalize, drop combining marks → ASCII-fold accented letters.
  3. Drop any character that isn't [a-zA-Z0-9 -] after fold.
  4. Lowercase.
  5. Replace any whitespace run with a single hyphen.
  6. Collapse runs of hyphens.
  7. Strip leading/trailing hyphens.

camelCase is NOT split — set `#+HUGO_SLUG:' for camelCase source filenames."
  (if (or (null title) (string-blank-p title))
      ""
    (let* ((folded (a3madkour-pub-slug--ascii-fold title))
           (clean (replace-regexp-in-string "[^a-zA-Z0-9 -]" "" folded))
           (lower (downcase clean))
           (hyphenated (replace-regexp-in-string "[ \t]+" "-" lower))
           (collapsed (replace-regexp-in-string "-+" "-" hyphenated))
           (trimmed (replace-regexp-in-string "\\`-+\\|-+\\'" "" collapsed)))
      trimmed)))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 22 tests, 22 results as expected, 0 unexpected`.

---

### Task 9: Wire up keywords + slug + section into `a3madkour-publish.el` (public API)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

- [ ] **Step 1: Write the failing tests for `published-p` happy path**

Append to `a3madkour-publish-test.el` (before its `provide`):

```elisp
;; -- published-p --

(defun a3madkour-pub-test--with-org-file (content thunk)
  "Write CONTENT to a tmp .org file and call THUNK with the file path.
Cleans up the tmp file afterwards."
  (let ((tmp (make-temp-file "a3-pub-test-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp (insert content))
          (funcall thunk tmp))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-test/published-p-live ()
  "File with HUGO_PUBLISH: t + valid HUGO_SECTION + no HUGO_DRAFT → 'live."
  (a3madkour-pub-test--with-org-file
   "#+title: Foo\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n* Body\n"
   (lambda (f) (should (eq 'live (a3madkour-pub/published-p f))))))

(ert-deftest a3madkour-pub-test/published-p-draft ()
  "Add HUGO_DRAFT: t → 'draft."
  (a3madkour-pub-test--with-org-file
   "#+title: Foo\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n#+HUGO_DRAFT: t\n* Body\n"
   (lambda (f) (should (eq 'draft (a3madkour-pub/published-p f))))))

(ert-deftest a3madkour-pub-test/published-p-private-missing-publish ()
  "No HUGO_PUBLISH → nil."
  (a3madkour-pub-test--with-org-file
   "#+title: Foo\n#+HUGO_SECTION: garden\n* Body\n"
   (lambda (f) (should (null (a3madkour-pub/published-p f))))))

(ert-deftest a3madkour-pub-test/published-p-publish-without-section-errors ()
  "HUGO_PUBLISH without HUGO_SECTION → user-error.
Default-deny means both keywords are required; setting just one is a likely
typo that should not silently succeed nor silently fail-private."
  (a3madkour-pub-test--with-org-file
   "#+title: Foo\n#+HUGO_PUBLISH: t\n* Body\n"
   (lambda (f) (should-error (a3madkour-pub/published-p f) :type 'user-error))))

(ert-deftest a3madkour-pub-test/published-p-unknown-section-errors ()
  "Unknown section value → user-error."
  (a3madkour-pub-test--with-org-file
   "#+title: Foo\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: gardn\n* Body\n"
   (lambda (f) (should-error (a3madkour-pub/published-p f) :type 'user-error))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -20`
Expected: 5 new failures for `published-p`.

- [ ] **Step 3: Implement**

In `a3madkour-publish.el`:

First, after the `defgroup` block (before the existing `defconst a3madkour-pub/version`), add:

```elisp
(require 'a3madkour-publish-keywords)
(require 'a3madkour-publish-slug)
```

Then, after the `valid-section-p` function (from Task 2) and before `(provide 'a3madkour-publish)`, insert:

```elisp
(defun a3madkour-pub--parse-file (file)
  "Open FILE and return a plist of parsed publish-relevant keywords.

Plist keys: :title :publish-p :section :draft-p :slug :aliases.
Errors with `user-error' if FILE is missing.  Does not validate the
keyword combination — that is `published-p''s job."
  (unless (file-readable-p file)
    (user-error "a3madkour-pub: cannot read file: %s" file))
  (with-temp-buffer
    (insert-file-contents file)
    (org-mode)
    (list :title     (a3madkour-pub-keywords/extract "title")
          :publish-p (a3madkour-pub-keywords/boolean-p
                      (a3madkour-pub-keywords/extract "HUGO_PUBLISH"))
          :section   (a3madkour-pub-keywords/extract "HUGO_SECTION")
          :draft-p   (a3madkour-pub-keywords/boolean-p
                      (a3madkour-pub-keywords/extract "HUGO_DRAFT"))
          :slug      (a3madkour-pub-keywords/extract "HUGO_SLUG")
          :aliases   (a3madkour-pub-keywords/parse-aliases
                      (a3madkour-pub-keywords/extract "HUGO_ALIASES")))))

(defun a3madkour-pub/published-p (file)
  "Return the publish-state of FILE: `live', `draft', or nil.

Signals `user-error' for invalid combinations:
  - `#+HUGO_PUBLISH: t' without `#+HUGO_SECTION:'
  - `#+HUGO_SECTION:' with an unknown value (typo guard)

File path input only.  A.1.b will add an org-roam ID dispatching layer."
  (let* ((parsed (a3madkour-pub--parse-file file))
         (publish-p (plist-get parsed :publish-p))
         (section (plist-get parsed :section))
         (draft-p (plist-get parsed :draft-p)))
    (cond
     ;; Not opted-in → private (most common case).
     ((not publish-p) nil)
     ;; Opted-in but no section → likely typo / incomplete config.
     ((null section)
      (user-error "a3madkour-pub: %s has #+HUGO_PUBLISH but no #+HUGO_SECTION" file))
     ;; Unknown section value → likely typo.
     ((not (a3madkour-pub/valid-section-p section))
      (user-error "a3madkour-pub: %s has unknown #+HUGO_SECTION value %S"
                  file section))
     ;; All good.
     (draft-p 'draft)
     (t 'live))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 27 tests, 27 results as expected, 0 unexpected`.

---

### Task 10: `note-slug`, `note-section`, `note-url`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-test.el` (before its `provide`):

```elisp
;; -- note-slug / note-section / note-url --

(ert-deftest a3madkour-pub-test/note-slug-uses-title-by-default ()
  (a3madkour-pub-test--with-org-file
   "#+title: Bayesian Statistics\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n* Body\n"
   (lambda (f)
     (should (equal "bayesian-statistics" (a3madkour-pub/note-slug f))))))

(ert-deftest a3madkour-pub-test/note-slug-honors-override ()
  (a3madkour-pub-test--with-org-file
   "#+title: Tractable Boolean Arithmetic\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n#+HUGO_SLUG: tba-2022\n* Body\n"
   (lambda (f)
     (should (equal "tba-2022" (a3madkour-pub/note-slug f))))))

(ert-deftest a3madkour-pub-test/note-section-returns-string-or-nil ()
  (a3madkour-pub-test--with-org-file
   "#+title: Foo\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n* Body\n"
   (lambda (f) (should (equal "garden" (a3madkour-pub/note-section f)))))
  (a3madkour-pub-test--with-org-file
   "#+title: Foo\n* Body\n"
   (lambda (f) (should (null (a3madkour-pub/note-section f))))))

(ert-deftest a3madkour-pub-test/note-url-shape ()
  (a3madkour-pub-test--with-org-file
   "#+title: Bayesian Statistics\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n* Body\n"
   (lambda (f)
     (should (equal "/garden/bayesian-statistics/" (a3madkour-pub/note-url f))))))

(ert-deftest a3madkour-pub-test/note-url-with-nested-section ()
  (a3madkour-pub-test--with-org-file
   "#+title: Q One\n#+HUGO_PUBLISH: t\n#+HUGO_SECTION: research/questions\n* Body\n"
   (lambda (f)
     (should (equal "/research/questions/q-one/" (a3madkour-pub/note-url f))))))

(ert-deftest a3madkour-pub-test/note-url-nil-for-private ()
  (a3madkour-pub-test--with-org-file
   "#+title: Foo\n* Body\n"
   (lambda (f) (should (null (a3madkour-pub/note-url f))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -20`
Expected: 6 new failures for `note-slug`/`note-section`/`note-url`.

- [ ] **Step 3: Implement**

In `a3madkour-publish.el`, before `(provide 'a3madkour-publish)`, insert:

```elisp
(defun a3madkour-pub/note-section (file)
  "Return the `#+HUGO_SECTION:' string value of FILE, or nil if absent."
  (let ((s (plist-get (a3madkour-pub--parse-file file) :section)))
    (and s (not (string-empty-p s)) s)))

(defun a3madkour-pub/note-slug (file)
  "Return the slug for FILE: `#+HUGO_SLUG:' if set, else slugified `#+title:'.
Returns nil if neither yields a non-empty result."
  (let* ((parsed (a3madkour-pub--parse-file file))
         (override (plist-get parsed :slug))
         (title (plist-get parsed :title)))
    (cond
     ((and override (not (string-empty-p override))) override)
     (title (let ((s (a3madkour-pub-slug/slugify title)))
              (and s (not (string-empty-p s)) s)))
     (t nil))))

(defun a3madkour-pub/note-url (file)
  "Return the URL path for FILE: `/<section>/<slug>/', or nil if FILE is not published.
Does NOT validate the publish state (use `published-p' for that) — it just
returns nil if the necessary pieces are missing."
  (let ((section (a3madkour-pub/note-section file))
        (slug (a3madkour-pub/note-slug file)))
    (when (and section slug)
      (format "/%s/%s/" section slug))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 33 tests, 33 results as expected, 0 unexpected`.

---

### Task 11: Create `a3madkour-publish-history.el` skeleton + defcustoms

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` (add `(require 'a3madkour-publish-history)`)

- [ ] **Step 1: Write the history library shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`

Content:

```elisp
;;; a3madkour-publish-history.el --- URL-history manifest -*- lexical-binding: t; -*-

;;; Commentary:

;; Reads, writes, and updates `data/url-history.yaml' (path computed from
;; `a3madkour-pub/site-data-dir').  Tracks every published note's current
;; URL plus the URLs it has had in the past, so that `aliases:' frontmatter
;; can be emitted on the next publish.

;;; Code:

(require 'yaml)
(require 'a3madkour-publish-slug)

(defgroup a3madkour-pub-history nil
  "URL-history manifest for the publish pipeline."
  :group 'a3madkour-pub
  :prefix "a3madkour-pub/")

(defcustom a3madkour-pub/org-notes-dir
  (expand-file-name "~/org/notes/")
  "Root directory of the org-roam notes corpus."
  :type 'directory
  :group 'a3madkour-pub-history)

(defcustom a3madkour-pub/site-data-dir
  nil
  "Path to the Hugo site repo's `data/' directory.

Required for URL-history manifest I/O.  Errors clearly when nil and
manifest reads/writes are attempted.  Set in your emacs config:

  (setq a3madkour-pub/site-data-dir
        \"~/Workspace/a3madkour.github.io/data/\")"
  :type '(choice (const :tag "Not set" nil) directory)
  :group 'a3madkour-pub-history)

(defun a3madkour-pub-history--manifest-path ()
  "Return the absolute path to `url-history.yaml', or signal user-error."
  (unless a3madkour-pub/site-data-dir
    (user-error "a3madkour-pub: set `a3madkour-pub/site-data-dir' first"))
  (expand-file-name "url-history.yaml" a3madkour-pub/site-data-dir))

(provide 'a3madkour-publish-history)

;;; a3madkour-publish-history.el ends here
```

- [ ] **Step 2: Write the history test file shell**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

Content:

```elisp
;;; a3madkour-publish-history-test.el --- Tests for URL-history manifest -*- lexical-binding: t; -*-

;;; Code:

(require 'ert)
(require 'a3madkour-publish-history)

(defun a3madkour-pub-history-test--with-tmp-data-dir (thunk)
  "Create a tmp dir; let-bind `a3madkour-pub/site-data-dir' to it; call THUNK."
  (let ((tmp-dir (file-name-as-directory (make-temp-file "a3-pub-data-" t))))
    (unwind-protect
        (let ((a3madkour-pub/site-data-dir tmp-dir))
          (funcall thunk tmp-dir))
      (delete-directory tmp-dir t))))

(ert-deftest a3madkour-pub-history-test/site-data-dir-required ()
  "Manifest path requires `a3madkour-pub/site-data-dir' to be set."
  (let ((a3madkour-pub/site-data-dir nil))
    (should-error (a3madkour-pub-history--manifest-path) :type 'user-error)))

(ert-deftest a3madkour-pub-history-test/manifest-path-resolves ()
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (tmp-dir)
     (should (equal (expand-file-name "url-history.yaml" tmp-dir)
                    (a3madkour-pub-history--manifest-path))))))

(provide 'a3madkour-publish-history-test)

;;; a3madkour-publish-history-test.el ends here
```

- [ ] **Step 3: Wire history.el into the entry-point library**

In `a3madkour-publish.el`, in the `(require ...)` block near the top (alongside the keywords + slug requires from Task 9), add:

```elisp
(require 'a3madkour-publish-history)
```

- [ ] **Step 4: Run, verify the new history tests pass + everything else still passes**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 35 tests, 35 results as expected, 0 unexpected`.

---

### Task 12: YAML read/write of the manifest

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-history-test.el` (before its `provide`):

```elisp
(ert-deftest a3madkour-pub-history-test/read-empty-manifest ()
  "Reading a missing-or-empty manifest returns the empty shape `((notes . []))'."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (_)
     (let ((m (a3madkour-pub-history/read-manifest)))
       (should (vectorp (alist-get 'notes m)))
       (should (= 0 (length (alist-get 'notes m))))))))

(ert-deftest a3madkour-pub-history-test/write-then-read-round-trip ()
  "Round-trip: write a manifest with one note → read back → matches."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (_)
     (let ((manifest
            '((notes . [((id . "abc-123")
                         (current_url . "/garden/foo/")
                         (history . [])
                         (state . "live"))]))))
       (a3madkour-pub-history/write-manifest manifest)
       (let* ((readback (a3madkour-pub-history/read-manifest))
              (notes (alist-get 'notes readback))
              (note (aref notes 0)))
         (should (= 1 (length notes)))
         (should (equal "abc-123" (alist-get 'id note)))
         (should (equal "/garden/foo/" (alist-get 'current_url note)))
         (should (equal "live" (alist-get 'state note))))))))

(ert-deftest a3madkour-pub-history-test/read-returns-empty-when-file-missing ()
  "If url-history.yaml doesn't exist yet, read returns the empty shape — no error."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (tmp-dir)
     (should-not (file-exists-p (expand-file-name "url-history.yaml" tmp-dir)))
     (let ((m (a3madkour-pub-history/read-manifest)))
       (should (= 0 (length (alist-get 'notes m))))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -20`
Expected: 3 new failures for `read-manifest` / `write-manifest`.

- [ ] **Step 3: Implement**

In `a3madkour-publish-history.el`, before the `provide`, insert:

```elisp
(defconst a3madkour-pub-history--empty-manifest
  '((notes . []))
  "Initial manifest shape: an empty vector under `notes'.")

(defun a3madkour-pub-history/read-manifest ()
  "Return the manifest as an alist parsed from `url-history.yaml'.
If the file is missing or empty, returns the empty shape `((notes . []))'."
  (let ((path (a3madkour-pub-history--manifest-path)))
    (if (and (file-readable-p path)
             (> (file-attribute-size (file-attributes path)) 0))
        (with-temp-buffer
          (insert-file-contents path)
          (let ((yaml-parsing-object-type 'alist)
                (yaml-parsing-sequence-type 'array)
                (yaml-parsing-null-object nil)
                (yaml-parsing-false-object nil))
            (yaml-parse-string (buffer-string))))
      (copy-tree a3madkour-pub-history--empty-manifest))))

(defun a3madkour-pub-history/write-manifest (manifest)
  "Serialize MANIFEST (an alist) to `url-history.yaml' as block-style YAML.
Creates the data dir if missing."
  (let ((path (a3madkour-pub-history--manifest-path)))
    (make-directory (file-name-directory path) t)
    (with-temp-file path
      (insert (yaml-encode manifest))
      (unless (eq ?\n (char-before)) (insert "\n")))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 38 tests, 38 results as expected, 0 unexpected`.

If the round-trip test fails on the *order* of alist keys (yaml-encode is not order-preserving in all builds), accept either ordering by reading specific keys (the test already does this).

---

### Task 13: `record-publish` — new note path

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

- [ ] **Step 1: Write the failing test**

Append:

```elisp
(ert-deftest a3madkour-pub-history-test/record-new-note ()
  "Recording a publish for a not-yet-seen ID creates an entry with empty history."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (_)
     (a3madkour-pub-history/record-publish "abc-123" "/garden/foo/" 'live)
     (let* ((m (a3madkour-pub-history/read-manifest))
            (notes (alist-get 'notes m))
            (note (aref notes 0)))
       (should (= 1 (length notes)))
       (should (equal "abc-123" (alist-get 'id note)))
       (should (equal "/garden/foo/" (alist-get 'current_url note)))
       (should (equal "live" (alist-get 'state note)))
       (let ((hist (alist-get 'history note)))
         (should (or (null hist) (= 0 (length hist)))))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -20`
Expected: 1 new failure for `record-publish`.

- [ ] **Step 3: Implement (new-note path only; URL-change path comes in Task 14)**

In `a3madkour-publish-history.el`, before the `provide`, insert:

```elisp
(defun a3madkour-pub-history--find-note-by-id (notes-vec id)
  "Return the index of the note with given ID in NOTES-VEC, or nil if absent."
  (cl-loop for i from 0 below (length notes-vec)
           when (equal id (alist-get 'id (aref notes-vec i)))
           return i))

(defun a3madkour-pub-history--state-to-string (state)
  "Coerce STATE (symbol or string) to its canonical string form."
  (cond
   ((stringp state) state)
   ((symbolp state) (symbol-name state))
   (t (error "a3madkour-pub: invalid state %S" state))))

(defun a3madkour-pub-history/record-publish (id new-url state)
  "Update the manifest entry for ID.

Cases:
  - ID not in manifest → insert a new entry with empty history.
  - ID present, current_url == NEW-URL → no-op (writes nothing).
  - ID present, current_url differs → append prior URL to history and update
    current_url.  (Reason detection lives in Task 14.)

STATE is `live', `draft', or `removed' (string or symbol accepted)."
  (require 'cl-lib)
  (let* ((manifest (a3madkour-pub-history/read-manifest))
         (notes (alist-get 'notes manifest))
         (idx (a3madkour-pub-history--find-note-by-id notes id))
         (state-str (a3madkour-pub-history--state-to-string state)))
    (cond
     ;; New note → append entry.
     ((null idx)
      (let* ((new-note `((id . ,id)
                         (current_url . ,new-url)
                         (history . [])
                         (state . ,state-str)))
             (new-notes (vconcat notes (vector new-note))))
        (setf (alist-get 'notes manifest) new-notes)
        (a3madkour-pub-history/write-manifest manifest)))
     ;; Existing note, same URL, same state → no-op.
     ((and (equal new-url (alist-get 'current_url (aref notes idx)))
           (equal state-str (alist-get 'state (aref notes idx))))
      nil)
     ;; URL or state differs → updated in Task 14.
     (t
      (error "a3madkour-pub: URL-change path not implemented yet (Task 14)")))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 39 tests, 39 results as expected, 0 unexpected`.

---

### Task 14: `record-publish` — URL change path + reason detection

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

- [ ] **Step 1: Write the failing tests**

Append:

```elisp
(ert-deftest a3madkour-pub-history-test/record-url-change-appends-history ()
  "Recording with a different URL appends the prior URL to history."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (_)
     (a3madkour-pub-history/record-publish "abc-123" "/garden/foo/" 'live)
     (a3madkour-pub-history/record-publish "abc-123" "/garden/foo-renamed/" 'live)
     (let* ((m (a3madkour-pub-history/read-manifest))
            (note (aref (alist-get 'notes m) 0))
            (hist (alist-get 'history note)))
       (should (equal "/garden/foo-renamed/" (alist-get 'current_url note)))
       (should (= 1 (length hist)))
       (let ((entry (aref hist 0)))
         (should (equal "/garden/foo/" (alist-get 'url entry)))
         (should (stringp (alist-get 'replaced_at entry)))
         (should (member (alist-get 'reason entry)
                         '("title_change" "slug_override" "section_change"))))))))

(ert-deftest a3madkour-pub-history-test/record-no-change-no-op ()
  "Recording the same URL/state twice does not append history."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (_)
     (a3madkour-pub-history/record-publish "abc-123" "/garden/foo/" 'live)
     (a3madkour-pub-history/record-publish "abc-123" "/garden/foo/" 'live)
     (let* ((note (aref (alist-get 'notes (a3madkour-pub-history/read-manifest)) 0))
            (hist (alist-get 'history note)))
       (should (or (null hist) (= 0 (length hist))))))))

(ert-deftest a3madkour-pub-history-test/record-section-change ()
  "Section change → reason='section_change'."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (_)
     (a3madkour-pub-history/record-publish "abc-123" "/garden/foo/" 'live)
     (a3madkour-pub-history/record-publish "abc-123" "/essays/foo/" 'live)
     (let* ((note (aref (alist-get 'notes (a3madkour-pub-history/read-manifest)) 0))
            (entry (aref (alist-get 'history note) 0)))
       (should (equal "section_change" (alist-get 'reason entry)))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -20`
Expected: failures for the URL-change tests (they currently hit the "not implemented yet" error).

- [ ] **Step 3: Implement (replace the placeholder in Task 13)**

In `a3madkour-publish-history.el`, REPLACE the `record-publish` function body's `(t (error ...))` clause and add a reason-detection helper.

Insert above `record-publish`:

```elisp
(defun a3madkour-pub-history--diff-reason (old-url new-url)
  "Classify the URL change between OLD-URL and NEW-URL.
Returns one of \"section_change\", \"slug_change\" (the catch-all for either
title_change or slug_override — we don't track which in the manifest itself
because we'd need extra context from the source file).

A.1.b can add finer-grained reason detection if useful; the spec lists
`title_change' / `slug_override' / `section_change' / `removed' as the canonical
vocabulary.  This stub picks the safest classification."
  (let* ((old-section (a3madkour-pub-history--section-of-url old-url))
         (new-section (a3madkour-pub-history--section-of-url new-url)))
    (cond
     ((not (equal old-section new-section)) "section_change")
     ;; Same section, different slug → can't distinguish title-vs-override here.
     ;; A.1.b/F will pass an extra :had-slug-override-p hint to refine this.
     (t "title_change"))))

(defun a3madkour-pub-history--section-of-url (url)
  "Extract the section component from URL of shape `/<section>/<slug>/'.
For nested sections like `/research/questions/q/' returns `research/questions'."
  (when (and (stringp url) (string-prefix-p "/" url))
    (let* ((trimmed (replace-regexp-in-string "\\`/+\\|/+\\'" "" url))
           (parts (split-string trimmed "/")))
      ;; All but the last segment is the section.
      (when (>= (length parts) 2)
        (mapconcat #'identity (butlast parts) "/")))))

(defun a3madkour-pub-history--now-iso ()
  "Return current time as an ISO-8601 UTC string."
  (format-time-string "%FT%TZ" nil t))
```

Then REPLACE the `record-publish` function entirely with:

```elisp
(defun a3madkour-pub-history/record-publish (id new-url state)
  "Update the manifest entry for ID.

Cases:
  - ID not in manifest → insert a new entry with empty history.
  - ID present, current_url == NEW-URL and state == STATE → no-op.
  - ID present, current_url differs → append `{url, replaced_at, reason}'
    to history and update current_url.
  - state differs (e.g. live → removed) → update state; if current_url also
    differs, append history with reason=\"removed\" when new-url is nil,
    otherwise per `--diff-reason'.

STATE is `live', `draft', or `removed' (string or symbol accepted)."
  (require 'cl-lib)
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
                          (url-changed-p (a3madkour-pub-history--diff-reason
                                          old-url new-url))
                          (t nil)))  ; state-only change
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
            (a3madkour-pub-history/write-manifest manifest))))))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 42 tests, 42 results as expected, 0 unexpected`.

---

### Task 15: `aliases-for`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

- [ ] **Step 1: Write the failing tests**

Append:

```elisp
(ert-deftest a3madkour-pub-history-test/aliases-for-empty ()
  "New note → no aliases."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (_)
     (a3madkour-pub-history/record-publish "abc-123" "/garden/foo/" 'live)
     (should (null (a3madkour-pub-history/aliases-for "abc-123"))))))

(ert-deftest a3madkour-pub-history-test/aliases-for-after-rename ()
  "After a URL change → the prior URL is in aliases-for."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (_)
     (a3madkour-pub-history/record-publish "abc-123" "/garden/foo/" 'live)
     (a3madkour-pub-history/record-publish "abc-123" "/garden/foo-v2/" 'live)
     (should (equal '("/garden/foo/")
                    (a3madkour-pub-history/aliases-for "abc-123"))))))

(ert-deftest a3madkour-pub-history-test/aliases-for-unknown-id ()
  "Unknown ID returns nil, not an error."
  (a3madkour-pub-history-test--with-tmp-data-dir
   (lambda (_)
     (should (null (a3madkour-pub-history/aliases-for "no-such-id"))))))
```

- [ ] **Step 2: Run, verify failure**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -20`
Expected: 3 new failures.

- [ ] **Step 3: Implement**

In `a3madkour-publish-history.el`, before the `provide`, insert:

```elisp
(defun a3madkour-pub-history/aliases-for (id)
  "Return all prior URLs recorded for ID, oldest-first.  Nil if ID unknown.
Drops `nil' entries (notes that have only ever had a single URL or are removed)."
  (let* ((manifest (a3madkour-pub-history/read-manifest))
         (notes (alist-get 'notes manifest))
         (idx (a3madkour-pub-history--find-note-by-id notes id)))
    (when idx
      (let ((hist (alist-get 'history (aref notes idx))))
        (when (and hist (> (length hist) 0))
          (cl-loop for i from 0 below (length hist)
                   for entry = (aref hist i)
                   for url = (alist-get 'url entry)
                   when url collect url))))))
```

- [ ] **Step 4: Run, verify pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -10`
Expected: `Ran 45 tests, 45 results as expected, 0 unexpected`.

---

### Task 16: Seed the empty manifest in the site repo

**Files:**
- Create: `data/url-history.yaml` (site repo)

- [ ] **Step 1: Write the initial empty manifest**

Path: `/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/data/url-history.yaml`

Content:

```yaml
# URL-history manifest for the org→Hugo publish pipeline.
# Managed by a3madkour-publish-history.el (sub-project A.1.a).
# See docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md §8.
#
# Schema (per-note entry):
#   id:           org-roam :ID: (UUID v4)
#   current_url:  /<section>/<slug>/  (or null if state=removed)
#   history:      list of {url, replaced_at, reason} entries; oldest-first
#   state:        live | draft | removed
#
# DO NOT edit by hand — re-publish will rewrite.

notes: []
```

- [ ] **Step 2: Verify the file is YAML-parseable**

Run (from anywhere):

```bash
emacs --batch --eval "(progn (require 'yaml) (let ((m (yaml-parse-string (with-temp-buffer (insert-file-contents \"/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/data/url-history.yaml\") (buffer-string))))) (message \"parsed: %s\" m)))"
```

Expected output: `parsed: ((notes . []))` or similar (an alist with `notes` key).

---

### Task 17: USER VERIFICATION CHECKPOINT

This is for the human author. Per spec §11, every stage of A.1 has an explicit manual-verification step.

- [ ] **Step 1: Author runs the full test suite**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`
Expected: `Ran 45 tests, 45 results as expected, 0 unexpected`. Exit `0`.

- [ ] **Step 2: Author spot-checks `published-p` on a real note**

Pick any note in `~/org/notes/` that is currently *unpublished* (no `#+HUGO_PUBLISH:`). Then in an interactive emacs session (or via batch):

```bash
emacs --batch \
  -L ~/dotfiles/emacs-configs/custom/lisp \
  -l a3madkour-publish \
  --eval "(message \"%s\" (a3madkour-pub/published-p \"~/org/notes/<some-real-note>.org\"))"
```

Replace `<some-real-note>` with an actual file. Expected: `nil` printed.

Then add `#+HUGO_PUBLISH: t` and `#+HUGO_SECTION: garden` to the *top* of a SCRATCH copy of the file (don't modify the real one), repeat: expected `live`.

- [ ] **Step 3: Author spot-checks `note-url`**

```bash
emacs --batch \
  -L ~/dotfiles/emacs-configs/custom/lisp \
  -l a3madkour-publish \
  --eval "(message \"%s\" (a3madkour-pub/note-url \"/tmp/scratch.org\"))"
```

With the scratch file containing `#+title: My Test`, `#+HUGO_PUBLISH: t`, `#+HUGO_SECTION: garden`. Expected: `/garden/my-test/`.

- [ ] **Step 4: Author spot-checks the URL-history round trip**

```bash
emacs --batch \
  -L ~/dotfiles/emacs-configs/custom/lisp \
  -l a3madkour-publish \
  --eval "(setq a3madkour-pub/site-data-dir \"/tmp/a3-pub-test-data/\")" \
  --eval "(a3madkour-pub-history/record-publish \"test-id\" \"/garden/foo/\" 'live)" \
  --eval "(a3madkour-pub-history/record-publish \"test-id\" \"/garden/foo-v2/\" 'live)" \
  --eval "(message \"aliases: %S\" (a3madkour-pub-history/aliases-for \"test-id\"))"
```

Expected output: `aliases: ("/garden/foo/")`. Inspect `/tmp/a3-pub-test-data/url-history.yaml` — should show one note with one history entry, state=live, current_url=/garden/foo-v2/.

Clean up: `rm -rf /tmp/a3-pub-test-data/`.

- [ ] **Step 5: Author confirms readiness for A.1.b**

Author affirms in the session that A.1.a is sound and the next plan (A.1.b — link rewriter) can begin.

---

### Task 18: Stage files for author commit

Per session policy, the agent stages but does NOT commit.

- [ ] **Step 1: Stage dotfiles changes**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish.el \
        emacs-configs/custom/lisp/a3madkour-publish-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-keywords.el \
        emacs-configs/custom/lisp/a3madkour-publish-keywords-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-slug.el \
        emacs-configs/custom/lisp/a3madkour-publish-slug-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-history.el \
        emacs-configs/custom/lisp/a3madkour-publish-history-test.el
git status --short | grep -E "(^A |^M ) emacs-configs/custom/lisp"
```

Expected: 8 files listed under "Changes to be committed".

- [ ] **Step 2: Stage site-repo changes**

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git add data/url-history.yaml docs/superpowers/plans/2026-05-20-phase-3-a1-a-foundations.md
git status --short | grep -E "(url-history|a1-a)"
```

Expected: 2 files staged.

- [ ] **Step 3: Suggested commit messages (author runs)**

In dotfiles:

```bash
git commit -m "feat(publish): A.1.a foundations — keywords, slug, published-p, URL-history

Sub-project A.1.a of the Phase 3 org→Hugo publish pipeline.
- a3madkour-publish-keywords.el: extract / boolean-p / parse-aliases
- a3madkour-publish-slug.el: slugify (NFKD ASCII-fold, lowercase, hyphens)
- a3madkour-publish-history.el: read/write/record-publish/aliases-for
  with auto-history tracking and reason classification
- a3madkour-publish.el (entry): section enum + valid-section-p +
  published-p / note-url / note-section / note-slug

45 ert tests; all passing.  Site repo path via two defcustoms
(a3madkour-pub/org-notes-dir, a3madkour-pub/site-data-dir)."
```

In site repo:

```bash
git commit -m "feat(data, plan): A.1.a foundations — url-history.yaml + plan

Seeds the URL-history manifest (data/url-history.yaml; empty initial state)
that the elisp publish library reads/writes on each publish.  Adds the
A.1.a plan doc."
```

---

## Self-Review

**Spec coverage:**
- §4 source-side keywords + section enum → Tasks 2, 4, 5, 6, 9.
- §4 default-deny (private when missing keywords) → Task 9 Step 3 (returns nil for `(not publish-p)`).
- §4 validation errors (missing pair, unknown section) → Task 9 Step 3 + tests.
- §5 slug derivation (title-default + override + Unicode handling) → Tasks 8, 10.
- §5 URL composition `/<section>/<slug>/` → Task 10.
- §5 URL stability via auto-aliases (the manifest part) → Tasks 11–15.
- §8 URL-history manifest schema → Task 16 (initial file) + Tasks 12–15 (logic).
- §10 elisp API surface: `published-p` / `note-url` / `note-section` / `record-publish` / `aliases-for` → Tasks 9, 10, 13, 14, 15.
- §10 site-repo coupling via `a3madkour-pub/site-data-dir` defcustom → Task 11.
- §11 testing strategy: ert unit tests per function (45 total) + per-stage manual-verification checkpoint → Task 17.

**Out of A.1.a scope (correctly deferred):**
- `(a3madkour-pub/rewrite-link …)` → A.1.b
- Asset validation / copy / auto-remediation → A.1.c
- Unpublish-flow `diff-published-set` + `check-orphans` → A.1.d
- File-vs-ID dispatching for `published-p` etc. → A.1.b (uses `org-roam-id-find`)
- Granular reason detection (title_change vs slug_override) — A.1.a uses "title_change" as catch-all for non-section-change; refinement noted in Task 14's helper docstring.

**Placeholder scan:** None. Every step has concrete commands and complete code.

**Type consistency:**
- All public functions use `a3madkour-pub/` prefix; internal helpers use `a3madkour-pub-<file>--` (double-hyphen private convention).
- Manifest shape is consistent: alists with `notes` → vector of alists with `id` / `current_url` / `history` / `state` keys.
- `state` values are strings (`"live"`/`"draft"`/`"removed"`) in the manifest; the API accepts symbols and coerces via `--state-to-string`.

**Scope check:** 18 tasks across 4 elisp files + 1 site-data file. Each task ≤ 5 minutes when nothing surprises. The plan's biggest risks are:
- yaml.el install (Task 1) — if straight.el bootstrap path differs, fallback diagnostic given.
- yaml-encode ordering (Task 12) — tests already accept either ordering.
