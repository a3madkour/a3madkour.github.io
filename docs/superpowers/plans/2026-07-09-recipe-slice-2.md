# Recipe Slice 2 — Org Authoring + Lint + Export — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author a recipe in org-mode and publish it, through a new dotfiles handler + pre-publish linter, into exactly the Hugo bundle the shipped Slice 1 renders.

**Architecture:** A garden/research-peer per-file handler (`a3madkour-publish-recipes.el`) parses drawer metadata + three structured subtrees (`** Ingredients` org table, `** Steps` list, `** Sources` list), routes the standard fields (title/date/lastmod/draft/summary/tags) through a new `recipes` branch in the existing frontmatter normalizer, injects the recipe-specific keys, and renders flow-style YAML via the YAML module's `key-hook` mechanism (the exact pattern the research handler uses for `outputs`). A separate `a3madkour-recipe-lint.el` gates publish with org `file:line` errors.

**Tech Stack:** Emacs Lisp (`org-element`, `cl-lib`, ert), the existing `a3madkour-publish-*` modules, ox-hugo, `a3-pub.sh`. The site repo is touched only for the round-trip acceptance test + docs.

## Global Constraints

- **Two repos.** Handler + linter + their ert tests live in `~/dotfiles/emacs-configs/custom/lisp/`. The round-trip test + docs live in `~/Sync/Workspace/a3madkour.github.io/`. Commit to each repo separately; never cross-stage.
- **Emitted bundle must pass the shipped site linters** verbatim: `tools/check_recipes_fixtures.py` + `tools/check_recipes_links.py`. Contract: **REQUIRED** `title, date, lastmod, draft, summary, servings, sources, ingredients, steps`; **OPTIONAL** `tags, cuisine, category, yield_unit, prep_minutes, cook_minutes, total_minutes, image, video, outputs`. `servings` int > 0. Ingredient `qty` is number-or-null. Step timecode regex: `^\[(\d{1,2}):([0-5]\d)(?:\.\d{1,2})?\]`.
- **No new site rendering.** `video` + `[mm:ss]` are carried as data only (synced-video render is the deferred Slice 1c).
- **Follow the research handler.** `a3madkour-publish-research.el` is the structural template for table parse, subtree strip, and flow-style YAML emission — mirror it; do not invent new patterns.
- **YAML values: quote strings, `null` for nil, bare numbers.** Units like `no`/`l` MUST be quoted (unquoted `no` parses as boolean).
- **ert runner:** `emacs -Q --batch -L . -l <module>-test.el -f ert-run-tests-batch-and-exit` from the lisp dir (each task gives the exact command).
- **Fixtures stay obviously-dummy** on the site side (site rule); the round-trip recipe uses `Example`/lorem content.

## File map

**Dotfiles (`~/dotfiles/emacs-configs/custom/lisp/`):**
- Create: `a3madkour-recipe-lint.el` — pre-publish validator (pure; returns error strings).
- Create: `a3madkour-recipe-lint-test.el` — its ert suite.
- Create: `a3madkour-publish-recipes.el` — the handler.
- Create: `a3madkour-publish-recipes-test.el` — its ert suite.
- Modify: `a3madkour-publish-frontmatter.el` — add `recipes` to `--known-sections` + a `--normalize-recipes` branch.
- Modify: `a3madkour-publish-frontmatter-test.el` — normalize-recipes tests.
- Modify: `a3madkour-publish-living.el` — register the `"recipes"` handler.
- Modify: `a3-pub.sh` — load the two new modules (both invocations) + `--skip-recipe-check`.

**Site (`~/Sync/Workspace/a3madkour.github.io/`):**
- Modify: `CLAUDE.md` — recipe authoring subsection.
- Modify: `docs/superpowers/specs/2026-07-06-recipe-section-design.md` — mark Slice 2 shipped.

---

### Task 1: Module skeleton + registration + a3-pub.sh wiring

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-recipes.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el` (registration block near the other `with-eval-after-load` entries)
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` (both `-l` load lists, after `-l a3madkour-publish-research`)

**Interfaces:**
- Produces: `a3madkour-pub-recipes/publish-recipe-file (file run &key on-done)` (stub this task); `a3madkour-pub-recipes/planned-steps (file)`.

- [ ] **Step 1: Write the failing smoke test**

Create `a3madkour-publish-recipes-test.el`:
```elisp
;;; a3madkour-publish-recipes-test.el --- tests for recipes handler  -*- lexical-binding: t; -*-
(require 'ert)
(require 'a3madkour-publish-recipes)

(defun a3madkour-pub-recipes-test--parse (org-text)
  "Parse ORG-TEXT and return its element AST."
  (with-temp-buffer (insert org-text) (org-mode) (org-element-parse-buffer)))

(ert-deftest a3madkour-pub-recipes--module-loads ()
  "Smoke: module loadable and exposes the entry point."
  (should (fboundp 'a3madkour-pub-recipes/publish-recipe-file)))
```

- [ ] **Step 2: Run it, verify it fails** (module missing)

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-publish-recipes-test.el -f ert-run-tests-batch-and-exit`
Expected: FAIL — `Cannot open load file: a3madkour-publish-recipes`.

- [ ] **Step 3: Create the module skeleton**

Create `a3madkour-publish-recipes.el`:
```elisp
;;; a3madkour-publish-recipes.el --- recipes per-file publish handler  -*- lexical-binding: t; -*-

;;; Commentary:

;; Slice 2: recipes per-file publish handler.  Parses drawer metadata plus
;; the ** Ingredients (org table) / ** Steps / ** Sources subtrees, routes the
;; standard frontmatter fields through the `recipes' normalize branch, injects
;; the recipe-specific keys, and writes content/recipes/<slug>/index.md.
;; Structural peer of a3madkour-publish-research.el.

;;; Code:

(require 'cl-lib)
(require 'org-element)
(require 'a3madkour-publish)
(require 'a3madkour-publish-yaml)
(require 'a3madkour-publish-export)
(require 'a3madkour-publish-frontmatter)
(require 'a3madkour-publish-rewrite)
(require 'a3madkour-publish-assets)
(require 'a3madkour-publish-history)
(require 'a3madkour-recipe-lint)

(defcustom a3madkour-pub-recipes/section-dir-name "recipes"
  "Hugo content section directory name for recipes (relative to site root)."
  :type 'string :group 'a3madkour-pub)

(cl-defun a3madkour-pub-recipes/publish-recipe-file (file run &key on-done)
  "Publish a single recipe FILE to content/recipes/<slug>/index.md.
Stub — real pipeline lands in Task 11."
  (ignore file run)
  (error "a3madkour-pub-recipes: not implemented yet")
  (when on-done (funcall on-done 'err)))

(defun a3madkour-pub-recipes/planned-steps (_file)
  "Return rough step count for the recipes handler."
  3)

(provide 'a3madkour-publish-recipes)

;;; a3madkour-publish-recipes.el ends here
```

Create a matching one-line stub so the `require` resolves this task (the real linter lands in Task 9): create `a3madkour-recipe-lint.el` with only:
```elisp
;;; a3madkour-recipe-lint.el --- recipe pre-publish linter  -*- lexical-binding: t; -*-
;;; Code:
(defvar a3madkour-recipe-lint-enabled t
  "When nil, the recipes handler skips the lint gate (--skip-recipe-check).")
(defun a3madkour-recipe-lint/lint-file (_file)
  "Stub — real rules land in Task 9.  Returns nil (no errors)."
  nil)
(provide 'a3madkour-recipe-lint)
;;; a3madkour-recipe-lint.el ends here
```

- [ ] **Step 4: Run the smoke test, verify it passes**

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-publish-recipes-test.el -f ert-run-tests-batch-and-exit`
Expected: PASS (1 test).

- [ ] **Step 5: Register the handler in living + wire a3-pub.sh**

In `a3madkour-publish-living.el`, after the research registration block, add:
```elisp
;; Slice 2: recipes handler registration.
(with-eval-after-load 'a3madkour-publish-recipes
  (add-to-list 'a3madkour-pub-living--handlers
               '("recipes" . a3madkour-pub-recipes/publish-recipe-file)))
```

In `a3-pub.sh`, in **both** `-l` load lists, immediately after the `-l a3madkour-publish-research \` line, add:
```
    -l a3madkour-recipe-lint \
    -l a3madkour-publish-recipes \
```

- [ ] **Step 6: Commit** (dotfiles)

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-recipes.el \
  emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el \
  emacs-configs/custom/lisp/a3madkour-recipe-lint.el \
  emacs-configs/custom/lisp/a3madkour-publish-living.el \
  emacs-configs/custom/lisp/a3-pub.sh
git commit -m "feat(recipes): Slice 2 handler skeleton + living registration + a3-pub.sh wiring"
```

---

### Task 2: Table/heading/list AST primitives

**Files:**
- Modify: `a3madkour-publish-recipes.el` (add primitives before the entry point)
- Modify: `a3madkour-publish-recipes-test.el`

**Interfaces:**
- Produces: `--find-heading-named (ast name) → headline|nil`; `--find-table-under (headline) → table|nil`; `--table-rows (table) → list-of-list-of-strings`; `--top-level-items (headline) → list-of-item-elements`; `--item-text (item) → string`.

- [ ] **Step 1: Write failing tests**

Append to `a3madkour-publish-recipes-test.el`:
```elisp
(ert-deftest a3madkour-pub-recipes--find-heading-and-table ()
  (let* ((ast (a3madkour-pub-recipes-test--parse "
* Recipe
** Ingredients
#+NAME: ingredients
| qty | item |
|-----+------|
|   2 | oil  |
** Steps
1. Do it.
"))
         (hl (a3madkour-pub-recipes--find-heading-named ast "ingredients"))
         (table (a3madkour-pub-recipes--find-table-under hl))
         (rows (a3madkour-pub-recipes--table-rows table)))
    (should hl)
    (should table)
    (should (equal (car rows) '("qty" "item")))
    (should (equal (nth 1 rows) '("2" "oil")))))

(ert-deftest a3madkour-pub-recipes--list-items ()
  (let* ((ast (a3madkour-pub-recipes-test--parse "
* Recipe
** Steps
1. First step.
2. [02:30] Second step.
"))
         (hl (a3madkour-pub-recipes--find-heading-named ast "steps"))
         (items (a3madkour-pub-recipes--top-level-items hl)))
    (should (= 2 (length items)))
    (should (equal (a3madkour-pub-recipes--item-text (nth 0 items)) "First step."))
    (should (equal (a3madkour-pub-recipes--item-text (nth 1 items)) "[02:30] Second step."))))
```

- [ ] **Step 2: Run, verify fail** (functions undefined)

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-publish-recipes-test.el -f ert-run-tests-batch-and-exit`
Expected: FAIL — `void-function a3madkour-pub-recipes--find-heading-named`.

- [ ] **Step 3: Implement the primitives**

Add to `a3madkour-publish-recipes.el` (before the entry point). These mirror `a3madkour-publish-research.el` lines 46-79:
```elisp
(defun a3madkour-pub-recipes--warn (file fmt &rest args)
  "Emit a WARN with FILE context."
  (apply #'a3madkour-pub/warn "recipes" file fmt args))

(defun a3madkour-pub-recipes--find-heading-named (ast name)
  "First headline in AST whose raw value = NAME (case-insensitive), or nil."
  (cl-loop for hl in (org-element-map ast 'headline #'identity)
           for raw = (org-element-property :raw-value hl)
           when (and raw (string-equal (downcase raw) (downcase name)))
           return hl))

(defun a3madkour-pub-recipes--find-table-under (headline)
  "First table element under HEADLINE (one level into its section), or nil."
  (let ((section (cl-loop for child in (org-element-contents headline)
                          when (eq (org-element-type child) 'section) return child)))
    (when section
      (cl-loop for child in (org-element-contents section)
               when (eq (org-element-type child) 'table) return child))))

(defun a3madkour-pub-recipes--table-rows (table)
  "TABLE's standard rows as list-of-list-of-cell-strings (hlines skipped)."
  (cl-loop for row in (org-element-map table 'table-row #'identity)
           when (eq (org-element-property :type row) 'standard)
           collect (mapcar (lambda (cell)
                             (let ((c (car (org-element-contents cell))))
                               (cond ((stringp c) (string-trim c))
                                     ((null c) "")
                                     (t (string-trim
                                         (substring-no-properties
                                          (org-element-interpret-data c)))))))
                           (org-element-contents row))))

(defun a3madkour-pub-recipes--top-level-items (headline)
  "Direct `item' elements of the first plain-list under HEADLINE, in order."
  (let ((section (cl-loop for child in (org-element-contents headline)
                          when (eq (org-element-type child) 'section) return child)))
    (when section
      (let ((plain-list (cl-loop for child in (org-element-contents section)
                                 when (eq (org-element-type child) 'plain-list) return child)))
        (when plain-list
          (cl-loop for child in (org-element-contents plain-list)
                   when (eq (org-element-type child) 'item) collect child))))))

(defun a3madkour-pub-recipes--item-text (item)
  "Text of an ITEM's paragraph, org markup preserved, nested lists dropped."
  (string-trim
   (substring-no-properties
    (org-element-interpret-data
     (cl-remove-if (lambda (c) (eq (org-element-type c) 'plain-list))
                   (org-element-contents item))))))
```

- [ ] **Step 4: Run, verify pass**

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-publish-recipes-test.el -f ert-run-tests-batch-and-exit`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-recipes.el emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el
git commit -m "feat(recipes): AST primitives — heading/table/list extraction"
```

---

### Task 3: Ingredients table parser

**Files:** Modify `a3madkour-publish-recipes.el`, `a3madkour-publish-recipes-test.el`

**Interfaces:**
- Consumes: `--find-heading-named`, `--find-table-under`, `--table-rows` (Task 2).
- Produces: `--coerce-qty (raw) → number|nil`; `--parse-ingredients (ast file) → list of plists (:qty :unit :item :group :note :alt)|nil`. Empty cells → nil; `group`/`note`/`alt` nil when blank; `item`/`unit`/`qty` keys always present.

- [ ] **Step 1: Write failing tests**

```elisp
(ert-deftest a3madkour-pub-recipes--coerce-qty-forms ()
  (should (equal (a3madkour-pub-recipes--coerce-qty "2") 2))
  (should (equal (a3madkour-pub-recipes--coerce-qty "800") 800))
  (should (equal (a3madkour-pub-recipes--coerce-qty "0.5") 0.5))
  (should (equal (a3madkour-pub-recipes--coerce-qty "1/2") 0.5))
  (should (equal (a3madkour-pub-recipes--coerce-qty "") nil))
  (should (equal (a3madkour-pub-recipes--coerce-qty "  ") nil)))

(ert-deftest a3madkour-pub-recipes--parse-ingredients-happy ()
  (let* ((ast (a3madkour-pub-recipes-test--parse "
* R
** Ingredients
#+NAME: ingredients
| qty | unit | item      | group | note  | alt     |
|-----+------+-----------+-------+-------+---------|
|   2 | tbsp | olive oil | base  |       |         |
|   1 |      | onion     | base  | diced | shallot |
|     |      | salt      |       | taste |         |
"))
         (ings (a3madkour-pub-recipes--parse-ingredients ast "/tmp/x.org")))
    (should (= 3 (length ings)))
    (should (equal (plist-get (nth 0 ings) :qty) 2))
    (should (equal (plist-get (nth 0 ings) :unit) "tbsp"))
    (should (equal (plist-get (nth 0 ings) :item) "olive oil"))
    (should (equal (plist-get (nth 0 ings) :group) "base"))
    (should (equal (plist-get (nth 1 ings) :alt) "shallot"))
    (should (equal (plist-get (nth 1 ings) :note) "diced"))
    (should (equal (plist-get (nth 2 ings) :qty) nil))
    (should (equal (plist-get (nth 2 ings) :unit) nil))
    (should (equal (plist-get (nth 2 ings) :group) nil))
    (should (equal (plist-get (nth 2 ings) :note) "taste"))))

(ert-deftest a3madkour-pub-recipes--parse-ingredients-none ()
  (let ((ast (a3madkour-pub-recipes-test--parse "* R\n** Steps\n1. x\n")))
    (should-not (a3madkour-pub-recipes--parse-ingredients ast "/tmp/x.org"))))
```

- [ ] **Step 2: Run, verify fail**

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-publish-recipes-test.el -f ert-run-tests-batch-and-exit`
Expected: FAIL — `void-function a3madkour-pub-recipes--coerce-qty`.

- [ ] **Step 3: Implement**

```elisp
(defconst a3madkour-pub-recipes--ingredient-cols
  '("qty" "unit" "item" "group" "note" "alt")
  "Expected ingredient-table columns (header row, any order).")

(defun a3madkour-pub-recipes--coerce-qty (raw)
  "Coerce a qty cell RAW to a number, or nil for empty/non-numeric.
Supports integers, decimals, and `a/b' fractions."
  (when (and raw (stringp raw))
    (let ((s (string-trim raw)))
      (cond
       ((string-empty-p s) nil)
       ((string-match "\\`\\([0-9]+\\)/\\([0-9]+\\)\\'" s)
        (/ (float (string-to-number (match-string 1 s)))
           (string-to-number (match-string 2 s))))
       ((string-match-p "\\`[0-9]+\\'" s) (string-to-number s))
       ((string-match-p "\\`[0-9]*\\.[0-9]+\\'" s) (string-to-number s))
       (t nil)))))

(defun a3madkour-pub-recipes--cell (row header col)
  "Value of column COL in ROW per HEADER, trimmed; nil when blank/absent."
  (let ((i (cl-position col header :test #'string-equal)))
    (when i
      (let ((v (nth i row)))
        (when (and v (not (string-empty-p (string-trim v)))) (string-trim v))))))

(cl-defun a3madkour-pub-recipes--parse-ingredients (ast file)
  "Parse the ** Ingredients table in AST → list of plists, or nil.
WARNs on heading-without-table."
  (let ((heading (a3madkour-pub-recipes--find-heading-named ast "ingredients")))
    (unless heading (cl-return-from a3madkour-pub-recipes--parse-ingredients nil))
    (let ((table (a3madkour-pub-recipes--find-table-under heading)))
      (unless table
        (a3madkour-pub-recipes--warn file "ingredients heading present but no table")
        (cl-return-from a3madkour-pub-recipes--parse-ingredients nil))
      (let* ((rows (a3madkour-pub-recipes--table-rows table))
             (header (mapcar #'downcase (car rows)))
             (data (cdr rows)))
        (cl-loop for row in data
                 collect (list :qty   (a3madkour-pub-recipes--coerce-qty
                                       (a3madkour-pub-recipes--cell row header "qty"))
                               :unit  (a3madkour-pub-recipes--cell row header "unit")
                               :item  (a3madkour-pub-recipes--cell row header "item")
                               :group (a3madkour-pub-recipes--cell row header "group")
                               :note  (a3madkour-pub-recipes--cell row header "note")
                               :alt   (a3madkour-pub-recipes--cell row header "alt")))))))
```

- [ ] **Step 4: Run, verify pass**

Expected: PASS (all recipe tests).

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-recipes.el emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el
git commit -m "feat(recipes): ingredients table parser (qty coercion, nullable cells)"
```

---

### Task 4: Steps list parser

**Files:** Modify `a3madkour-publish-recipes.el`, `a3madkour-publish-recipes-test.el`

**Interfaces:**
- Consumes: `--find-heading-named`, `--top-level-items`, `--item-text` (Task 2).
- Produces: `--parse-steps (ast) → list of strings|nil`. Leading `[mm:ss]` kept verbatim.

- [ ] **Step 1: Write failing test**

```elisp
(ert-deftest a3madkour-pub-recipes--parse-steps ()
  (let* ((ast (a3madkour-pub-recipes-test--parse "
* R
** Steps
1. Heat the oil.
2. [02:30] Add tomatoes.
"))
         (steps (a3madkour-pub-recipes--parse-steps ast)))
    (should (equal steps '("Heat the oil." "[02:30] Add tomatoes.")))))
```

- [ ] **Step 2: Run, verify fail**

Expected: FAIL — `void-function a3madkour-pub-recipes--parse-steps`.

- [ ] **Step 3: Implement**

```elisp
(defun a3madkour-pub-recipes--parse-steps (ast)
  "Parse ** Steps ordered list in AST → list of step strings, or nil."
  (let ((heading (a3madkour-pub-recipes--find-heading-named ast "steps")))
    (when heading
      (mapcar #'a3madkour-pub-recipes--item-text
              (a3madkour-pub-recipes--top-level-items heading)))))
```

- [ ] **Step 4: Run, verify pass** — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-recipes.el emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el
git commit -m "feat(recipes): steps list parser ([mm:ss] preserved)"
```

---

### Task 5: Sources list parser

**Files:** Modify `a3madkour-publish-recipes.el`, `a3madkour-publish-recipes-test.el`

**Interfaces:**
- Consumes: `--find-heading-named`, `--top-level-items`, `--item-text`.
- Produces: `--parse-source-item (text) → plist (:name :url :note)`; `--parse-sources (ast) → list of plists|nil`.

- [ ] **Step 1: Write failing tests**

```elisp
(ert-deftest a3madkour-pub-recipes--parse-source-item-forms ()
  (should (equal (a3madkour-pub-recipes--parse-source-item "[[https://x.test][NYT]] — adapted")
                 '(:name "NYT" :url "https://x.test" :note "adapted")))
  (should (equal (a3madkour-pub-recipes--parse-source-item "[[https://x.test][NYT]]")
                 '(:name "NYT" :url "https://x.test")))
  (should (equal (a3madkour-pub-recipes--parse-source-item "Grandma's notebook")
                 '(:name "Grandma's notebook")))
  (should (equal (a3madkour-pub-recipes--parse-source-item "Some book — p. 40")
                 '(:name "Some book" :note "p. 40"))))

(ert-deftest a3madkour-pub-recipes--parse-sources ()
  (let* ((ast (a3madkour-pub-recipes-test--parse "
* R
** Sources
- [[https://x.test][NYT]] — adapted
- Grandma's notebook
"))
         (srcs (a3madkour-pub-recipes--parse-sources ast)))
    (should (= 2 (length srcs)))
    (should (equal (plist-get (nth 0 srcs) :url) "https://x.test"))
    (should (equal (plist-get (nth 1 srcs) :name) "Grandma's notebook"))))
```

- [ ] **Step 2: Run, verify fail** — Expected: FAIL (`void-function`).

- [ ] **Step 3: Implement**

```elisp
(defun a3madkour-pub-recipes--parse-source-item (text)
  "Parse a source list-item TEXT into a plist (:name :url :note).
Forms: `[[url][name]] — note', `[[url][name]]', `name — note', `name'.
The em-dash `—' or ` -- ' introduces the optional note."
  (let ((body text) (note nil) (name nil) (url nil))
    (when (string-match "[[:space:]]+\\(?:—\\|--\\)[[:space:]]+" body)
      (setq note (string-trim (substring body (match-end 0)))
            body (string-trim (substring body 0 (match-beginning 0)))))
    (cond
     ((string-match "\\`\\[\\[\\(.*?\\)\\]\\[\\(.*?\\)\\]\\]\\'" body)
      (setq url (match-string 1 body) name (match-string 2 body)))
     ((string-match "\\`\\[\\[\\(.*?\\)\\]\\]\\'" body)
      (setq url (match-string 1 body) name (match-string 1 body)))
     (t (setq name body)))
    (append (list :name name)
            (when url (list :url url))
            (when (and note (not (string-empty-p note))) (list :note note)))))

(defun a3madkour-pub-recipes--parse-sources (ast)
  "Parse ** Sources list in AST → list of source plists, or nil."
  (let ((heading (a3madkour-pub-recipes--find-heading-named ast "sources")))
    (when heading
      (mapcar (lambda (item)
                (a3madkour-pub-recipes--parse-source-item
                 (a3madkour-pub-recipes--item-text item)))
              (a3madkour-pub-recipes--top-level-items heading)))))
```

- [ ] **Step 4: Run, verify pass** — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-recipes.el emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el
git commit -m "feat(recipes): sources list parser (link + note forms)"
```

---

### Task 6: Drawer-metadata parser

**Files:** Modify `a3madkour-publish-recipes.el`, `a3madkour-publish-recipes-test.el`

**Interfaces:**
- Produces: `--parse-metadata (ast) → alist of recipe-specific frontmatter keys` (servings, yield_unit, prep_minutes, cook_minutes, total_minutes, cuisine, category, video, image). Only present keys included; ints coerced; `total_minutes` derived from prep+cook when absent but both present.

- [ ] **Step 1: Write failing test**

```elisp
(ert-deftest a3madkour-pub-recipes--parse-metadata ()
  (let* ((ast (a3madkour-pub-recipes-test--parse "
:PROPERTIES:
:servings:   4
:yield-unit: servings
:prep-time:  10
:cook-time:  25
:cuisine:    North African
:category:   Main
:video:      dQw4w9WgXcQ
:image:      hero.svg
:END:
Headnote.
* R
** Steps
1. x
"))
         (md (a3madkour-pub-recipes--parse-metadata ast)))
    (should (equal (alist-get 'servings md) 4))
    (should (equal (alist-get 'yield_unit md) "servings"))
    (should (equal (alist-get 'prep_minutes md) 10))
    (should (equal (alist-get 'cook_minutes md) 25))
    (should (equal (alist-get 'total_minutes md) 35))
    (should (equal (alist-get 'cuisine md) "North African"))
    (should (equal (alist-get 'category md) "Main"))
    (should (equal (alist-get 'video md) "dQw4w9WgXcQ"))
    (should (equal (alist-get 'image md) "hero.svg"))))

(ert-deftest a3madkour-pub-recipes--parse-metadata-minimal ()
  (let* ((ast (a3madkour-pub-recipes-test--parse
               ":PROPERTIES:\n:servings: 2\n:END:\nx\n"))
         (md (a3madkour-pub-recipes--parse-metadata ast)))
    (should (equal (alist-get 'servings md) 2))
    (should-not (assq 'total_minutes md))
    (should-not (assq 'cuisine md))))
```

- [ ] **Step 2: Run, verify fail** — Expected: FAIL (`void-function`).

- [ ] **Step 3: Implement**

```elisp
(defconst a3madkour-pub-recipes--drawer-map
  '(("SERVINGS"   servings      int)
    ("YIELD-UNIT" yield_unit    nil)
    ("PREP-TIME"  prep_minutes  int)
    ("COOK-TIME"  cook_minutes  int)
    ("TOTAL-TIME" total_minutes int)
    ("CUISINE"    cuisine       nil)
    ("CATEGORY"   category      nil)
    ("VIDEO"      video         nil)
    ("IMAGE"      image         nil))
  "Property-drawer KEY → (frontmatter-symbol coercion).  KEY is upcased.")

(defun a3madkour-pub-recipes--drawer-alist (ast)
  "Alist of (UPCASED-KEY . VALUE-STRING) from the first property drawer in AST."
  (let ((drawer (org-element-map ast 'property-drawer #'identity nil t)))
    (when drawer
      (org-element-map drawer 'node-property
        (lambda (np)
          (cons (upcase (org-element-property :key np))
                (org-element-property :value np)))))))

(defun a3madkour-pub-recipes--parse-metadata (ast)
  "Extract recipe-specific frontmatter keys from AST's property drawer.
Returns an alist; only present keys are included."
  (let* ((drawer (a3madkour-pub-recipes--drawer-alist ast))
         (out '()))
    (dolist (spec a3madkour-pub-recipes--drawer-map)
      (let* ((raw (cdr (assoc (car spec) drawer)))
             (sym (nth 1 spec))
             (coerce (nth 2 spec)))
        (when (and raw (not (string-empty-p (string-trim raw))))
          (setf (alist-get sym out)
                (if (eq coerce 'int) (string-to-number (string-trim raw))
                  (string-trim raw))))))
    ;; Derive total_minutes when absent but prep+cook both present.
    (when (and (not (assq 'total_minutes out))
               (assq 'prep_minutes out) (assq 'cook_minutes out))
      (setf (alist-get 'total_minutes out)
            (+ (alist-get 'prep_minutes out) (alist-get 'cook_minutes out))))
    out))
```

- [ ] **Step 4: Run, verify pass** — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-recipes.el emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el
git commit -m "feat(recipes): drawer-metadata parser (servings/times/cuisine/…)"
```

---

### Task 7: Flow-style YAML renderers + key-hook

**Files:** Modify `a3madkour-publish-recipes.el`, `a3madkour-publish-recipes-test.el`

**Interfaces:**
- Consumes: `a3madkour-pub/yaml-escape-scalar`, `a3madkour-pub-yaml/render-frontmatter`, `a3madkour-pub-yaml/render-value`.
- Produces: `--render-ingredient (ing) → string`; `--render-source (src) → string`; `--key-hook (k v)`; `--render-frontmatter (alist) → string`. String values quoted, nil → `null`, numbers bare. Ingredient key order: `group, qty, unit, item, note, alt` (qty/unit/item always emitted; group/note/alt omitted when nil).

- [ ] **Step 1: Write failing tests**

```elisp
(ert-deftest a3madkour-pub-recipes--render-ingredient ()
  (should (equal (a3madkour-pub-recipes--render-ingredient
                  '(:qty 2 :unit "tbsp" :item "olive oil" :group "base" :note nil :alt nil))
                 "{ group: \"base\", qty: 2, unit: \"tbsp\", item: \"olive oil\" }"))
  (should (equal (a3madkour-pub-recipes--render-ingredient
                  '(:qty nil :unit nil :item "salt" :group nil :note "to taste" :alt nil))
                 "{ qty: null, unit: null, item: \"salt\", note: \"to taste\" }")))

(ert-deftest a3madkour-pub-recipes--render-source ()
  (should (equal (a3madkour-pub-recipes--render-source '(:name "NYT" :url "https://x" :note "adapted"))
                 "{ name: \"NYT\", url: \"https://x\", note: \"adapted\" }"))
  (should (equal (a3madkour-pub-recipes--render-source '(:name "Book"))
                 "{ name: \"Book\" }")))

(ert-deftest a3madkour-pub-recipes--render-frontmatter-blocks ()
  (let ((out (a3madkour-pub-recipes--render-frontmatter
              '((title . "Shakshuka")
                (servings . 4)
                (steps . ("Heat oil." "[02:30] Add tomatoes."))
                (ingredients . ((:qty 2 :unit "tbsp" :item "oil" :group nil :note nil :alt nil)))
                (sources . ((:name "NYT" :url "https://x" :note nil)))))))
    (should (string-match-p "steps:\n  - \"Heat oil.\"\n  - \"\\[02:30\\] Add tomatoes.\"" out))
    (should (string-match-p "ingredients:\n  - { qty: 2, unit: \"tbsp\", item: \"oil\" }" out))
    (should (string-match-p "sources:\n  - { name: \"NYT\", url: \"https://x\" }" out))
    (should (string-match-p "servings: 4" out))
    (should (string-match-p "title: \"Shakshuka\"" out))))
```

- [ ] **Step 2: Run, verify fail** — Expected: FAIL (`void-function`).

- [ ] **Step 3: Implement**

```elisp
(defun a3madkour-pub-recipes--scalar (v)
  "Render V as a flow-map value: number bare, nil → null, string quoted."
  (cond ((null v) "null")
        ((numberp v) (format "%s" v))
        (t (format "\"%s\"" (a3madkour-pub/yaml-escape-scalar v)))))

(defun a3madkour-pub-recipes--render-ingredient (ing)
  "Render an ingredient plist ING as an inline YAML map.
Order: group qty unit item note alt.  qty/unit/item always; others when non-nil."
  (let ((parts '()))
    (when (plist-get ing :group) (push (format "group: %s" (a3madkour-pub-recipes--scalar (plist-get ing :group))) parts))
    (push (format "qty: %s"  (a3madkour-pub-recipes--scalar (plist-get ing :qty))) parts)
    (push (format "unit: %s" (a3madkour-pub-recipes--scalar (plist-get ing :unit))) parts)
    (push (format "item: %s" (a3madkour-pub-recipes--scalar (plist-get ing :item))) parts)
    (when (plist-get ing :note) (push (format "note: %s" (a3madkour-pub-recipes--scalar (plist-get ing :note))) parts))
    (when (plist-get ing :alt)  (push (format "alt: %s"  (a3madkour-pub-recipes--scalar (plist-get ing :alt))) parts))
    (format "{ %s }" (mapconcat #'identity (nreverse parts) ", "))))

(defun a3madkour-pub-recipes--render-source (src)
  "Render a source plist SRC as an inline YAML map.  name always; url/note when non-nil."
  (let ((parts (list (format "name: %s" (a3madkour-pub-recipes--scalar (plist-get src :name))))))
    (when (plist-get src :url)  (setq parts (append parts (list (format "url: %s" (a3madkour-pub-recipes--scalar (plist-get src :url)))))))
    (when (plist-get src :note) (setq parts (append parts (list (format "note: %s" (a3madkour-pub-recipes--scalar (plist-get src :note)))))))
    (format "{ %s }" (mapconcat #'identity parts ", "))))

(defun a3madkour-pub-recipes--render-block (label render-fn items)
  "Render `LABEL:' + a block sequence of ITEMS via RENDER-FN."
  (format "%s:\n%s" label
          (mapconcat (lambda (it) (concat "  - " (funcall render-fn it))) items "\n")))

(defun a3madkour-pub-recipes--key-hook (k v)
  "render-frontmatter KEY-HOOK for the three structured recipe keys."
  (cond
   ((eq k 'ingredients)
    (if (and v (listp v)) (a3madkour-pub-recipes--render-block "ingredients" #'a3madkour-pub-recipes--render-ingredient v) :omit))
   ((eq k 'sources)
    (if (and v (listp v)) (a3madkour-pub-recipes--render-block "sources" #'a3madkour-pub-recipes--render-source v) :omit))
   ((eq k 'steps)
    (if (and v (listp v))
        (format "steps:\n%s" (mapconcat (lambda (s) (format "  - \"%s\"" (a3madkour-pub/yaml-escape-scalar s))) v "\n"))
      :omit))))

(defun a3madkour-pub-recipes--render-frontmatter (alist)
  "Render ALIST as recipe frontmatter (structured keys via the key-hook)."
  (a3madkour-pub-yaml/render-frontmatter
   alist
   :key-hook #'a3madkour-pub-recipes--key-hook
   :value-fn #'a3madkour-pub-yaml/render-value))
```

- [ ] **Step 4: Run, verify pass** — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-recipes.el emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el
git commit -m "feat(recipes): flow-style YAML renderers + structured key-hook"
```

---

### Task 8: Strip-data-subtrees helper

**Files:** Modify `a3madkour-publish-recipes.el`, `a3madkour-publish-recipes-test.el`

**Interfaces:**
- Produces: `--strip-data-subtrees (org-text) → org-text` with the three data subtrees removed (headnote-only remains).

- [ ] **Step 1: Write failing test**

```elisp
(ert-deftest a3madkour-pub-recipes--strip-subtrees ()
  (let ((out (a3madkour-pub-recipes--strip-data-subtrees "* R
Headnote paragraph.
** Ingredients
| qty | item |
| 1   | x    |
** Steps
1. Do it.
** Sources
- A book
")))
    (should (string-match-p "Headnote paragraph." out))
    (should-not (string-match-p "Ingredients" out))
    (should-not (string-match-p "Steps" out))
    (should-not (string-match-p "Sources" out))))
```

- [ ] **Step 2: Run, verify fail** — Expected: FAIL (`void-function`).

- [ ] **Step 3: Implement** (mirrors research `--strip-outputs-subtree`; re-parses each pass so positions stay valid)

```elisp
(defun a3madkour-pub-recipes--strip-data-subtrees (org-text)
  "Return ORG-TEXT with the ** Ingredients / ** Steps / ** Sources subtrees removed.
Re-parses after each deletion so element positions stay valid."
  (with-temp-buffer
    (insert org-text)
    (org-mode)
    (dolist (name '("ingredients" "steps" "sources"))
      (let* ((ast (org-element-parse-buffer))
             (hl (a3madkour-pub-recipes--find-heading-named ast name)))
        (when hl
          (delete-region (org-element-property :begin hl)
                         (org-element-property :end hl)))))
    (buffer-substring-no-properties (point-min) (point-max))))
```

- [ ] **Step 4: Run, verify pass** — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-recipes.el emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el
git commit -m "feat(recipes): strip data subtrees before ox-hugo body export"
```

---

### Task 9: The pre-publish linter (`a3madkour-recipe-lint.el`)

**Files:**
- Replace stub: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-recipe-lint.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-recipe-lint-test.el`

**Interfaces:**
- Produces: `a3madkour-recipe-lint/lint-file (file) → list of "file:line: message" strings` (empty = clean); `a3madkour-recipe-lint-enabled` (defvar, default t).

- [ ] **Step 1: Write failing tests**

Create `a3madkour-recipe-lint-test.el`:
```elisp
;;; a3madkour-recipe-lint-test.el --- tests for the recipe linter  -*- lexical-binding: t; -*-
(require 'ert)
(require 'a3madkour-recipe-lint)

(defun a3madkour-recipe-lint-test--write (org-text)
  "Write ORG-TEXT to a temp .org file; return its path."
  (let ((f (make-temp-file "recipe-lint-" nil ".org")))
    (with-temp-file f (insert org-text)) f))

(defconst a3madkour-recipe-lint-test--good "#+TITLE: Shakshuka
#+HUGO_SUMMARY: A dish.
:PROPERTIES:
:servings: 4
:video: dQw4w9WgXcQ
:END:
Headnote.
** Ingredients
#+NAME: ingredients
| qty | unit | item | group | note | alt |
|-----+------+------+-------+------+-----|
| 2   | tbsp | oil  |       |      |     |
** Steps
1. [02:30] Add tomatoes.
** Sources
- A book
")

(ert-deftest a3madkour-recipe-lint--clean ()
  (let ((f (a3madkour-recipe-lint-test--write a3madkour-recipe-lint-test--good)))
    (unwind-protect (should-not (a3madkour-recipe-lint/lint-file f))
      (delete-file f))))

(ert-deftest a3madkour-recipe-lint--missing-steps ()
  (let ((f (a3madkour-recipe-lint-test--write "#+TITLE: X
#+HUGO_SUMMARY: y
:PROPERTIES:\n:servings: 2\n:END:
** Ingredients
#+NAME: ingredients
| qty | unit | item | group | note | alt |
| 1   |      | x    |       |      |     |
** Sources
- A
")))
    (unwind-protect
        (should (seq-some (lambda (m) (string-match-p "Steps" m))
                          (a3madkour-recipe-lint/lint-file f)))
      (delete-file f))))

(ert-deftest a3madkour-recipe-lint--bad-qty ()
  (let ((f (a3madkour-recipe-lint-test--write "#+TITLE: X
#+HUGO_SUMMARY: y
:PROPERTIES:\n:servings: 2\n:END:
** Ingredients
#+NAME: ingredients
| qty       | unit | item | group | note | alt |
| a couple  |      | x    |       |      |     |
** Steps
1. Do it.
** Sources
- A
")))
    (unwind-protect
        (should (seq-some (lambda (m) (string-match-p "qty" m))
                          (a3madkour-recipe-lint/lint-file f)))
      (delete-file f))))

(ert-deftest a3madkour-recipe-lint--bad-timecode ()
  (let ((f (a3madkour-recipe-lint-test--write "#+TITLE: X
#+HUGO_SUMMARY: y
:PROPERTIES:\n:servings: 2\n:END:
** Ingredients
#+NAME: ingredients
| qty | unit | item | group | note | alt |
| 1   |      | x    |       |      |     |
** Steps
1. [2:3] Bad.
** Sources
- A
")))
    (unwind-protect
        (should (seq-some (lambda (m) (string-match-p "\\[mm:ss\\]\\|timecode" m))
                          (a3madkour-recipe-lint/lint-file f)))
      (delete-file f))))

(ert-deftest a3madkour-recipe-lint--missing-summary ()
  (let ((f (a3madkour-recipe-lint-test--write "#+TITLE: X
:PROPERTIES:\n:servings: 2\n:END:
** Ingredients
#+NAME: ingredients
| qty | unit | item | group | note | alt |
| 1   |      | x    |       |      |     |
** Steps
1. Do it.
** Sources
- A
")))
    (unwind-protect
        (should (seq-some (lambda (m) (string-match-p "HUGO_SUMMARY\\|summary" m))
                          (a3madkour-recipe-lint/lint-file f)))
      (delete-file f))))
```

- [ ] **Step 2: Run, verify fail** (stub returns nil so clean passes but the negative tests fail)

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-recipe-lint-test.el -f ert-run-tests-batch-and-exit`
Expected: FAIL on the four negative tests (stub returns nil).

- [ ] **Step 3: Implement the linter** (replace the stub file entirely)

```elisp
;;; a3madkour-recipe-lint.el --- recipe pre-publish linter  -*- lexical-binding: t; -*-

;;; Commentary:
;; Slice 2: pre-publish validator for org recipe sources.  Returns a list of
;; "file:line: message" strings (empty = clean).  The recipes publish handler
;; calls this before export and aborts on errors unless disabled.

;;; Code:
(require 'cl-lib)
(require 'org-element)

(defvar a3madkour-recipe-lint-enabled t
  "When nil, the recipes handler skips the lint gate (--skip-recipe-check).")

(defconst a3madkour-recipe-lint--cols '("qty" "unit" "item" "group" "note" "alt")
  "Required ingredient-table header columns.")
(defconst a3madkour-recipe-lint--timecode-re
  "\\`\\[[0-9]\\{1,2\\}:[0-5][0-9]\\(?:\\.[0-9]\\{1,2\\}\\)?\\]"
  "Matches a leading [mm:ss] or [mm:ss.ff] step marker.")
(defconst a3madkour-recipe-lint--video-re "\\`[A-Za-z0-9_-]\\{11\\}\\'"
  "Matches a bare 11-char YouTube id.")

(defun a3madkour-recipe-lint--line-of (element)
  "1-based source line of ELEMENT's :begin (1 if absent)."
  (let ((b (and element (org-element-property :begin element))))
    (if b (line-number-at-pos b) 1)))

(defun a3madkour-recipe-lint--kw (ast name)
  "Value of `#+NAME:'-style keyword NAME (upcased) in AST, or nil."
  (org-element-map ast 'keyword
    (lambda (kw)
      (when (string-equal (upcase (org-element-property :key kw)) name)
        (org-element-property :value kw)))
    nil t))

(defun a3madkour-recipe-lint--drawer-value (ast key)
  "Value of property-drawer KEY (upcased) in AST, or nil."
  (let ((drawer (org-element-map ast 'property-drawer #'identity nil t)))
    (when drawer
      (org-element-map drawer 'node-property
        (lambda (np)
          (when (string-equal (upcase (org-element-property :key np)) key)
            (org-element-property :value np)))
        nil t))))

;; Re-use the handler's AST helpers.
(declare-function a3madkour-pub-recipes--find-heading-named "a3madkour-publish-recipes")
(declare-function a3madkour-pub-recipes--find-table-under "a3madkour-publish-recipes")
(declare-function a3madkour-pub-recipes--table-rows "a3madkour-publish-recipes")
(declare-function a3madkour-pub-recipes--top-level-items "a3madkour-publish-recipes")
(declare-function a3madkour-pub-recipes--item-text "a3madkour-publish-recipes")
(declare-function a3madkour-pub-recipes--coerce-qty "a3madkour-publish-recipes")
(declare-function a3madkour-pub-recipes--cell "a3madkour-publish-recipes")

(defun a3madkour-recipe-lint/lint-file (file)
  "Lint recipe FILE.  Return a list of \"FILE:LINE: message\" strings (empty = clean)."
  (require 'a3madkour-publish-recipes)
  (with-temp-buffer
    (insert-file-contents file)
    (org-mode)
    (let* ((ast (org-element-parse-buffer))
           (errs '())
           (base (file-name-nondirectory file))
           (emit (lambda (line msg) (push (format "%s:%d: %s" base line msg) errs))))
      ;; Rule 6: required metadata.
      (unless (a3madkour-recipe-lint--kw ast "TITLE")
        (funcall emit 1 "missing #+TITLE:"))
      (unless (a3madkour-recipe-lint--kw ast "HUGO_SUMMARY")
        (funcall emit 1 "missing #+HUGO_SUMMARY:"))
      (let ((sv (a3madkour-recipe-lint--drawer-value ast "SERVINGS")))
        (unless (and sv (string-match-p "\\`[0-9]+\\'" (string-trim sv))
                     (> (string-to-number sv) 0))
          (funcall emit 1 "missing or non-positive :servings:")))
      ;; Rule 1: required subheadings.
      (let ((ing (a3madkour-pub-recipes--find-heading-named ast "ingredients"))
            (steps (a3madkour-pub-recipes--find-heading-named ast "steps"))
            (sources (a3madkour-pub-recipes--find-heading-named ast "sources")))
        (unless ing (funcall emit 1 "missing ** Ingredients heading"))
        (unless steps (funcall emit 1 "missing ** Steps heading"))
        (if (not sources)
            (funcall emit 1 "missing ** Sources heading")
          (unless (a3madkour-pub-recipes--top-level-items sources)
            (funcall emit (a3madkour-recipe-lint--line-of sources)
                     "** Sources has no list items")))
        ;; Rules 2-3: ingredient table + rows.
        (when ing
          (let ((table (a3madkour-pub-recipes--find-table-under ing)))
            (if (not table)
                (funcall emit (a3madkour-recipe-lint--line-of ing)
                         "** Ingredients has no table")
              (let* ((rows (a3madkour-pub-recipes--table-rows table))
                     (header (mapcar #'downcase (car rows)))
                     (data (cdr rows)))
                (dolist (col a3madkour-recipe-lint--cols)
                  (unless (cl-position col header :test #'string-equal)
                    (funcall emit (a3madkour-recipe-lint--line-of table)
                             (format "ingredients table missing column %S" col))))
                (let ((ln (a3madkour-recipe-lint--line-of table)))
                  (dolist (row data)
                    (let ((qty (a3madkour-pub-recipes--cell row header "qty"))
                          (item (a3madkour-pub-recipes--cell row header "item")))
                      (when (and qty (not (a3madkour-pub-recipes--coerce-qty qty)))
                        (funcall emit ln (format "ingredient qty %S is not numeric-or-empty" qty)))
                      (unless item
                        (funcall emit ln "ingredient row missing item")))))))))
        ;; Rule 4: step timecodes.
        (when steps
          (dolist (item (a3madkour-pub-recipes--top-level-items steps))
            (let ((txt (a3madkour-pub-recipes--item-text item)))
              (when (and (string-prefix-p "[" txt)
                         (not (string-match-p a3madkour-recipe-lint--timecode-re txt)))
                (funcall emit (a3madkour-recipe-lint--line-of item)
                         (format "malformed [mm:ss] timecode in step: %S"
                                 (substring txt 0 (min 12 (length txt))))))))))
      ;; Rule 5: video id shape.
      (let ((vid (a3madkour-recipe-lint--drawer-value ast "VIDEO")))
        (when (and vid (not (string-match-p a3madkour-recipe-lint--video-re (string-trim vid))))
          (funcall emit 1 (format ":video: %S is not an 11-char YouTube id" vid))))
      (nreverse errs))))

(provide 'a3madkour-recipe-lint)
;;; a3madkour-recipe-lint.el ends here
```

- [ ] **Step 4: Run, verify pass**

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-recipe-lint-test.el -f ert-run-tests-batch-and-exit`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-recipe-lint.el emacs-configs/custom/lisp/a3madkour-recipe-lint-test.el
git commit -m "feat(recipes): pre-publish linter (6 rules, org file:line errors)"
```

---

### Task 10: `recipes` normalize branch

**Files:**
- Modify: `a3madkour-publish-frontmatter.el` (add `recipes` to `--known-sections`; add cond branch + `--normalize-recipes`)
- Modify: `a3madkour-publish-frontmatter-test.el`

**Interfaces:**
- Consumes: `a3madkour-pub-frontmatter--coerce-bool`, `--read-org-keyword`, `a3madkour-pub-frontmatter/last-modified-cascade`.
- Produces: `(a3madkour-pub-frontmatter/normalize 'recipes raw-alist file)` → alist with normalized `title date lastmod draft summary tags`.

- [ ] **Step 1: Write failing test**

Append to `a3madkour-publish-frontmatter-test.el`:
```elisp
(ert-deftest a3madkour-pub-frontmatter--normalize-recipes-standard-fields ()
  (let* ((f (make-temp-file "recipe-fm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file f (insert "#+TITLE: X\n#+HUGO_SUMMARY: A tasty dish.\n#+DATE: 2026-07-09\n"))
          (let ((out (a3madkour-pub-frontmatter/normalize
                      'recipes '((title . "X") (date . "2026-07-09") (draft . "true")) f)))
            (should (equal (alist-get 'summary out) "A tasty dish."))
            (should (eq (alist-get 'draft out) t))
            (should (assq 'tags out))
            (should (alist-get 'lastmod out))
            (should (equal (alist-get 'date out) "2026-07-09"))))
      (delete-file f))))

(ert-deftest a3madkour-pub-frontmatter--normalize-recipes-date-defaults-to-lastmod ()
  (let* ((f (make-temp-file "recipe-fm-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file f (insert "#+TITLE: X\n#+HUGO_SUMMARY: y\n"))
          (let ((out (a3madkour-pub-frontmatter/normalize 'recipes '((title . "X")) f)))
            (should (equal (alist-get 'date out) (alist-get 'lastmod out)))))
      (delete-file f))))
```

- [ ] **Step 2: Run, verify fail** — the `normalize` dispatch errors on unknown section `recipes`.

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-publish-frontmatter-test.el -f ert-run-tests-batch-and-exit`
Expected: FAIL — `unknown section recipes`.

- [ ] **Step 3: Implement**

In `a3madkour-publish-frontmatter.el`, add `recipes` to the `--known-sections` list:
```elisp
    library-reading library-listening library-playing library-watching
    recipes)
```
Add a branch in `a3madkour-pub-frontmatter/normalize`'s cond (next to the essays branch):
```elisp
   ((eq section 'recipes)
    (a3madkour-pub-frontmatter--normalize-recipes raw-alist source-file))
```
Add the normalizer (near `--normalize-essays`):
```elisp
(defun a3madkour-pub-frontmatter--normalize-recipes (raw-alist source-file)
  "Slice 2: recipes standard-field normalizer.
Keeps only title/date/lastmod/draft/summary/tags; the handler injects the
recipe-specific keys afterward.  draft→bool (default false); tags default [];
summary from #+HUGO_SUMMARY:; lastmod via cascade; date defaults to lastmod."
  (let* ((allowed '(title date lastmod draft summary tags))
         (out (cl-remove-if-not (lambda (c) (memq (car c) allowed)) (copy-alist raw-alist))))
    (setf (alist-get 'draft out)
          (a3madkour-pub-frontmatter--coerce-bool (alist-get 'draft out)))
    (unless (assq 'tags out) (push (cons 'tags '()) out))
    (setf (alist-get 'summary out)
          (or (a3madkour-pub-frontmatter--read-org-keyword source-file "HUGO_SUMMARY") ""))
    (let ((drawer-lm (alist-get 'last_modified raw-alist))
          (kw-lm (alist-get 'lastmod raw-alist)))
      (setq out (assq-delete-all 'lastmod out))
      (setq out (assq-delete-all 'last_modified out))
      (setf (alist-get 'lastmod out)
            (a3madkour-pub-frontmatter/last-modified-cascade
             source-file :drawer drawer-lm
             :keyword (when (and (stringp kw-lm) (>= (length kw-lm) 10)) (substring kw-lm 0 10)))))
    (unless (and (assq 'date out) (alist-get 'date out))
      (setf (alist-get 'date out) (alist-get 'lastmod out)))
    out))
```

- [ ] **Step 4: Run, verify pass** — Expected: PASS. Also run the full frontmatter suite to confirm no regression:

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-publish-frontmatter-test.el -f ert-run-tests-batch-and-exit`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "feat(recipes): recipes normalize branch (standard fields)"
```

---

### Task 11: Handler entry point (integration)

**Files:** Modify `a3madkour-publish-recipes.el` (replace the stub entry point), `a3madkour-publish-recipes-test.el`

**Interfaces:**
- Consumes: all Task 2-8 parsers/renderers/strip; `a3madkour-recipe-lint/lint-file`; `a3madkour-pub/note-metadata`, `note-url`; `a3madkour-pub-rewrite/rewrite-to-tmp-file`; `a3madkour-pub-export/export-file`; `a3madkour-pub-frontmatter/normalize`; `a3madkour-pub/asset-validate-and-copy`; `a3madkour-pub-history/*`.
- Produces: the real `a3madkour-pub-recipes/publish-recipe-file` + `--assemble-frontmatter (ast normalized) → alist`.

- [ ] **Step 1: Write failing integration test** (drives assembly + render on a parsed AST, no filesystem export)

```elisp
(ert-deftest a3madkour-pub-recipes--assemble-frontmatter ()
  (let* ((ast (a3madkour-pub-recipes-test--parse "
:PROPERTIES:
:servings: 4
:cuisine: North African
:END:
Headnote.
** Ingredients
#+NAME: ingredients
| qty | unit | item | group | note | alt |
| 2   | tbsp | oil  | base  |      |     |
** Steps
1. [02:30] Add tomatoes.
** Sources
- [[https://x.test][NYT]] — adapted
"))
         (normalized '((title . "Shakshuka") (date . "2026-07-09")
                       (lastmod . "2026-07-09") (draft . nil)
                       (summary . "A dish.") (tags . ("example"))))
         (fm (a3madkour-pub-recipes--assemble-frontmatter ast normalized))
         (out (a3madkour-pub-recipes--render-frontmatter fm)))
    (should (equal (alist-get 'servings fm) 4))
    (should (equal (alist-get 'cuisine fm) "North African"))
    (should (= 1 (length (alist-get 'ingredients fm))))
    (should (equal (alist-get 'steps fm) '("[02:30] Add tomatoes.")))
    (should (string-match-p "ingredients:\n  - { group: \"base\", qty: 2" out))
    (should (string-match-p "sources:\n  - { name: \"NYT\", url: \"https://x.test\", note: \"adapted\" }" out))
    (should (string-match-p "servings: 4" out))))
```

- [ ] **Step 2: Run, verify fail** — Expected: FAIL (`void-function ...--assemble-frontmatter`).

- [ ] **Step 3: Implement assembly + the real entry point** (replace the stub `publish-recipe-file`)

```elisp
(defun a3madkour-pub-recipes--assemble-frontmatter (ast normalized)
  "Merge NORMALIZED standard fields with recipe-specific keys parsed from AST."
  (let ((out (copy-alist normalized)))
    (dolist (cell (a3madkour-pub-recipes--parse-metadata ast))
      (setf (alist-get (car cell) out) (cdr cell)))
    (setf (alist-get 'ingredients out) (a3madkour-pub-recipes--parse-ingredients ast "recipe"))
    (setf (alist-get 'steps out) (a3madkour-pub-recipes--parse-steps ast))
    (setf (alist-get 'sources out) (a3madkour-pub-recipes--parse-sources ast))
    out))

(cl-defun a3madkour-pub-recipes/publish-recipe-file (file run &key on-done)
  "Publish a single recipe FILE to content/recipes/<slug>/index.md.
Pipeline: lint → parse → strip-subtrees → ox-hugo body export →
normalize standard fields → inject recipe keys → render → asset-copy →
write-if-different → record-publish."
  (ignore run)
  (condition-case _err
      (progn
        ;; Step 1: lint gate.
        (when a3madkour-recipe-lint-enabled
          (let ((errs (a3madkour-recipe-lint/lint-file file)))
            (when errs
              (error "a3madkour-pub-recipes: lint failed for %s:\n%s"
                     file (mapconcat #'identity errs "\n")))))
        (let* ((md        (a3madkour-pub/note-metadata file))
               (id        (plist-get md :id))
               (slug      (a3madkour-pub/note-slug file))
               (new-url   (a3madkour-pub/note-url file))
               (site-root (a3madkour-pub-yaml/site-root))
               (bundle-dir (expand-file-name
                            (format "content/%s/%s/"
                                    a3madkour-pub-recipes/section-dir-name slug)
                            site-root))
               (out-path   (expand-file-name "index.md" bundle-dir))
               ;; Parse the structured data from the ORIGINAL source.
               (src-ast    (with-temp-buffer
                             (insert-file-contents file) (org-mode)
                             (org-element-parse-buffer)))
               ;; Body export: rewrite links → strip data subtrees → ox-hugo.
               (tmp-src    (a3madkour-pub-rewrite/rewrite-to-tmp-file file id "a3-pub-recipes"))
               (exported   (unwind-protect
                               (progn
                                 (let ((stripped (a3madkour-pub-recipes--strip-data-subtrees
                                                  (with-temp-buffer
                                                    (insert-file-contents tmp-src)
                                                    (buffer-string)))))
                                   (with-temp-file tmp-src (insert stripped)))
                                 (a3madkour-pub-export/export-file tmp-src))
                             (when (file-exists-p tmp-src) (delete-file tmp-src))))
               ;; Normalize standard fields; P2.14 stable-date.
               (normalized (let ((a3madkour-pub-frontmatter--prior-last-modified
                                  (a3madkour-pub-history/recorded-last-modified id new-url)))
                             (a3madkour-pub-frontmatter/normalize
                              'recipes (plist-get exported :frontmatter) file)))
               (final-fm   (a3madkour-pub-recipes--assemble-frontmatter src-ast normalized))
               (body       (plist-get exported :body)))
          (a3madkour-pub/asset-validate-and-copy file bundle-dir id)
          (a3madkour-pub-yaml/write-if-different
           out-path
           (concat (a3madkour-pub-recipes--render-frontmatter final-fm) body))
          (a3madkour-pub-history/record-publish id new-url (or (plist-get md :state) 'live)
                                                :last-modified (alist-get 'lastmod final-fm)))
        (when on-done (funcall on-done 'ok)))
    (error
     (message "%s" (error-message-string _err))
     (when on-done (funcall on-done 'err)))))
```

- [ ] **Step 4: Run, verify pass** (assembly test + full recipe suite)

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && emacs -Q --batch -L . -l a3madkour-publish-recipes-test.el -f ert-run-tests-batch-and-exit`
Expected: PASS (all recipe tests).

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-recipes.el emacs-configs/custom/lisp/a3madkour-publish-recipes-test.el
git commit -m "feat(recipes): handler entry point — lint→parse→export→render→write"
```

---

### Task 12: `--skip-recipe-check` flag + full dotfiles suite

**Files:** Modify `a3-pub.sh`

**Interfaces:** shell flag `--skip-recipe-check` / env `A3_PUB_SKIP_RECIPE_CHECK=1` → sets `a3madkour-recipe-lint-enabled` nil in the batch emacs.

- [ ] **Step 1: Add the flag** (mirror the `--skip-math-check` handling)

Near the `A3_PUB_SKIP_MATH_CHECK="${A3_PUB_SKIP_MATH_CHECK:-0}"` init, add:
```sh
A3_PUB_SKIP_RECIPE_CHECK="${A3_PUB_SKIP_RECIPE_CHECK:-0}"
```
In the arg-parse `case` (next to `--skip-math-check)`), add:
```sh
    --skip-recipe-check) A3_PUB_SKIP_RECIPE_CHECK=1 ;;
```
In **both** emacs invocations, after the module `-l` list and before the publish `--eval`, add:
```sh
    $( [ "$A3_PUB_SKIP_RECIPE_CHECK" = "1" ] && printf -- '--eval (setq\ a3madkour-recipe-lint-enabled\ nil)' ) \
```
> Note to implementer: if the inline `$(...)` quoting fights `zsh`/`bash` word-splitting, fall back to a conditional that appends `--eval "(setq a3madkour-recipe-lint-enabled nil)"` to an args array. Verify by running the command in Step 2.

- [ ] **Step 2: Verify the flag parses** (dry smoke — no publish)

Run: `cd ~/dotfiles/emacs-configs/custom/lisp && A3_PUB_SKIP_RECIPE_CHECK=1 bash -n a3-pub.sh && echo "syntax-ok"`
Expected: `syntax-ok` (no syntax error).

- [ ] **Step 3: Run the entire dotfiles recipe + frontmatter + linter suite**

Run:
```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs -Q --batch -L . \
  -l a3madkour-recipe-lint-test.el \
  -l a3madkour-publish-recipes-test.el \
  -l a3madkour-publish-frontmatter-test.el \
  -f ert-run-tests-batch-and-exit
```
Expected: PASS (0 unexpected).

- [ ] **Step 4: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3-pub.sh
git commit -m "feat(recipes): --skip-recipe-check flag (mirrors --skip-math-check)"
```

---

### Task 13: Round-trip acceptance (real publish → site linters → dev-server eyeball)

**Files:**
- Create (author's org dir, NOT the repo): a real `recipes/<slug>.org` following the spec shape.
- Verify (site repo): the emitted `content/recipes/<slug>/index.md`.

**Interfaces:** none (end-to-end verification).

- [ ] **Step 1: Author a real recipe** in the org notes dir (org-roam), using the spec's shape: `#+TITLE:`, `#+HUGO_SECTION: recipes`, `#+DATE:`, `#+FILETAGS:`, `#+HUGO_SUMMARY:`, the `:PROPERTIES:` drawer (`:servings:` at minimum), a headnote, `** Ingredients` (`#+NAME: ingredients` table), `** Steps`, `** Sources`. Drop a hand-authored `hero.svg` in the bundle if using `:image:`.

- [ ] **Step 2: Publish it** via the living publish path:

Run the normal publish command (`a3-pub.sh` living publish, however the author invokes it). Expected: no lint errors; `content/recipes/<slug>/index.md` written in the site repo.

- [ ] **Step 3: Run the site linters against the emitted bundle**

Run:
```bash
cd ~/Sync/Workspace/a3madkour.github.io
python3 tools/check_recipes_fixtures.py && python3 tools/check_recipes_links.py && echo "linters-green"
```
Expected: `linters-green`. If either fails, the emitted YAML diverges from the contract — fix the handler mapping (return to the relevant task), do not hand-edit the bundle.

- [ ] **Step 4: Eyeball on the dev server** (kill any running `hugo server` first; do NOT run `hugo --minify` alongside a dev server)

Run: `cd ~/Sync/Workspace/a3madkour.github.io && hugo server --buildDrafts`
Open `/recipes/<slug>/` and confirm: headnote renders; ingredient rail shows groups; scaler works; steps list correct; sources listed; `.json` download present; `<head>` JSON-LD present. Compare against a Slice 1 fixture page for parity.

- [ ] **Step 5: Verify the emitted bundle diff is contract-shaped**

Run: `cd ~/Sync/Workspace/a3madkour.github.io && git diff --stat content/recipes/`
Confirm only the new real recipe bundle appears. **Do not commit the real recipe to the site repo unless the author wants it live** — this is an acceptance artifact. If keeping it, it must be real (non-dummy) content the author authored; the obviously-dummy rule applies only to fixtures.

- [ ] **Step 6: Note the result** — record round-trip pass/fail in the Task 14 memory update. No commit here unless keeping the recipe.

---

### Task 14: Docs + memory

**Files:**
- Modify: `~/Sync/Workspace/a3madkour.github.io/CLAUDE.md`
- Modify: `~/Sync/Workspace/a3madkour.github.io/docs/superpowers/specs/2026-07-06-recipe-section-design.md`
- Memory: `.claude/memory/` (new project entry + MEMORY.md pointer)

- [ ] **Step 1: CLAUDE.md** — under the recipes coverage, add a short "Recipe authoring (org → export)" note: the org shape (`#+HUGO_SECTION: recipes`, drawer props, `** Ingredients` table / `** Steps` / `** Sources`), the `a3madkour-publish-recipes.el` handler (garden peer, living section), and `a3madkour-recipe-lint` (pre-publish gate, `--skip-recipe-check`). Cross-reference the spec + this plan.

- [ ] **Step 2: Section spec** — in `2026-07-06-recipe-section-design.md`, mark Slice 2 shipped and point to `2026-07-09-recipe-slice-2-org-authoring-design.md`.

- [ ] **Step 3: Commit docs** (site repo)

```bash
cd ~/Sync/Workspace/a3madkour.github.io
git add CLAUDE.md docs/superpowers/specs/2026-07-06-recipe-section-design.md
git commit -m "docs(recipes): Slice 2 org authoring shipped — CLAUDE.md + section spec"
```

- [ ] **Step 4: Memory** — add `.claude/memory/project_recipe_slice_2_complete.md` (what shipped, commit range in both repos, round-trip result) and a one-line pointer in `MEMORY.md`. Update `project_recipe_section.md` to mark Slice 2 shipped.

---

## Self-Review

**Spec coverage:**
- Authoring shape (drawer + 3 subheadings, single ingredients table) → Tasks 2-6, spec org example. ✓
- Handler (`a3madkour-publish-recipes.el`, garden peer, lint→parse→strip→export→normalize→inject→render→write) → Tasks 1, 8, 10, 11. ✓
- `org-table-to-lisp`-style parse (hline/header strip, string cells, null qty) → Task 3 (via `--table-rows` + `--coerce-qty`). ✓
- Steps list, `[mm:ss]` verbatim → Task 4. ✓
- Sources link-list forms → Task 5. ✓
- Flow-style `ingredients`/`sources`/`steps` via key-hook → Task 7. ✓
- `recipes` normalize branch (standard fields, date/lastmod/summary/draft/tags) → Task 10. ✓
- Full pre-publish linter (6 rules, file:line) + `--skip-recipe-check` → Tasks 9, 12. ✓
- a3-pub.sh wiring + living registration → Tasks 1, 12. ✓
- Round-trip against the shipped site linters + dev-server → Task 13. ✓
- No new site rendering (video/`[mm:ss]` carried as data) → Tasks 4, 7 (verbatim), spec scope. ✓
- Docs + memory → Task 14. ✓

**Placeholder scan:** No TBD/TODO; every code step shows complete code; the one implementer judgment call (Task 12 shell-quoting of the conditional `--eval`) carries a concrete fallback + a verification command. ✓

**Type consistency:** Parser return shapes are consistent across tasks — ingredient plists `(:qty :unit :item :group :note :alt)` (Task 3) are consumed unchanged by `--render-ingredient` (Task 7), `--assemble-frontmatter` (Task 11), and the linter (Task 9); source plists `(:name :url :note)` likewise; `--find-heading-named`/`--table-rows`/`--top-level-items`/`--item-text`/`--cell`/`--coerce-qty` names match every call site. `a3madkour-recipe-lint-enabled` + `a3madkour-recipe-lint/lint-file` names match between Tasks 1 (stub), 9 (real), 11 (gate), 12 (flag). ✓
