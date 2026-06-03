# Phase 3 sub-project D.2 — multi-target export — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish one literate org document to three artifacts in one event — the existing Hugo essay, a PDF technical report, and a Word document — with D.1's 12-kind semantic-block vocabulary rendering correctly across all three targets.

**Architecture:** Auto-triggered by `M-x a3-publish-deliberate` (existing B.4 command) when source carries `#+multi_export: t`. Four new dotfiles modules (filter, pdf backend, word backend, orchestrator) plus three new template files in the site repo (`madkour-paper.cls`, `reference.docx`, `d2-blocks.lua`). Each backend runs in `condition-case`; partial success emits whichever artifacts succeeded via auto-patched `downloads:` frontmatter on the Hugo essay bundle. Site-side: downloads cluster in `essay-meta` partial + linter extension (no new CI step).

**Tech Stack:**
- Emacs 30 (org-export, ox-latex, ox-hugo, pandoc-org)
- xelatex + biber (LaTeX → PDF)
- pandoc + `d2-blocks.lua` (org → docx)
- librsvg `rsvg-convert` (SVG → PDF / PNG)
- Hugo 0.162.1 (essay bundle host, unchanged)
- Python 3 stdlib (linter extension)

**Spec:** `docs/superpowers/specs/2026-06-02-phase-3-d2-multi-target-export-design.md`. Supersedes the 2026-05-13 spec.

---

## Repos touched

| Repo | Location | Files |
|---|---|---|
| Dotfiles | `~/dotfiles/emacs-configs/custom/lisp/` | 4 new modules + 4 test files + `a3-pub.sh` update |
| Site | `~/Sync/Workspace/a3madkour.github.io/` | 3 new template files + 1 fixture bundle + linter/template/CSS edits |

The site repo is the working directory for plan execution. Dotfiles work happens via `cd ~/dotfiles && …` per established B.4 / D.1 / F convention. Both repos commit on `master` directly (per recent flow).

---

## File structure

### Dotfiles (`~/dotfiles/emacs-configs/custom/lisp/`)

| File | Purpose |
|---|---|
| `a3madkour-publish-multi-filter.el` | Shared visibility-tag filter (5 tags) + D.1 vocab translation hooks; `multi-export-doc-p` predicate |
| `a3madkour-publish-multi-filter-test.el` | ert tests for filter + predicate |
| `a3madkour-publish-multi-pdf.el` | ox-latex backend; xelatex + biber 4-pass; SVG → PDF; defcustoms for tool paths |
| `a3madkour-publish-multi-pdf-test.el` | ert tests with mocked shell calls |
| `a3madkour-publish-multi-word.el` | pandoc org → docx; SVG → PNG; serialized filtered-org as pandoc input |
| `a3madkour-publish-multi-word-test.el` | ert tests with mocked shell calls |
| `a3madkour-publish-multi.el` | Orchestrator: `#+multi_export` detection, dispatch, `condition-case` per backend, frontmatter patch, `*a3madkour-pub*` log buffer extension |
| `a3madkour-publish-multi-test.el` | ert tests for orchestrator + partial-success scenarios |
| `a3-pub.sh` (modify) | Add `-l a3madkour-publish-multi-filter -l a3madkour-publish-multi-pdf -l a3madkour-publish-multi-word -l a3madkour-publish-multi` |

### Site (`~/Sync/Workspace/a3madkour.github.io/`)

| File | Purpose |
|---|---|
| `tools/templates/madkour-paper.cls` | LaTeX class (article + amsthm + 12 theorem envs + biblatex authoryear) |
| `tools/templates/d2-blocks.lua` | Pandoc filter: numbering pass + styling pass for 12 D.1 block kinds |
| `tools/templates/reference.docx` | Word reference doc with 12 header + 12 body styles (hand-authored once) |
| `tools/check_fixtures.py` (modify) | Extend YAML parser for 2-deep block mapping; add `multi_export` + `downloads` validation |
| `tools/test_check_fixtures.py` (modify) | Add positive + negative cases for new fields |
| `layouts/partials/essay-meta.html` (modify) | Append `.essay-downloads` cluster after series pill, gated on `.Params.multi_export` |
| `assets/css/main.css` (modify) | Add `.essay-downloads` + `.download-link` rules into existing `.essay-meta` block |
| `content/essays/example-multi/index.md` | End-to-end fixture bundle (B.4 + D.2 emission) |
| `content/essays/example-multi/example-multi.pdf` | Fixture PDF (committed) |
| `content/essays/example-multi/example-multi.docx` | Fixture Word (committed) |
| `content/essays/example-multi/figures/diagram-1.svg` | Hand-authored SVG figure for the fixture |
| `~/org/notes/essay-example-multi.org` | Source org file (lives in dotfiles-adjacent org-roam tree; not in site repo) |

---

## Task-level dependency notes

- Tasks 1–3 (filter) are prerequisite for both backends.
- Task 4 (`madkour-paper.cls`) can run in parallel with filter tasks; needed before Task 6.
- Tasks 8–9 (Lua filter passes) can run in parallel with PDF tasks (Tasks 5–7) — no code overlap.
- Task 10 (`reference.docx`) is hand-authored in Word/LibreOffice; can be drafted in parallel; final styling iterates after Task 22 spot-check.
- Tasks 15–19 (site-side) depend on the orchestrator emitting `multi_export: true` + `downloads:` frontmatter — Task 13 must land before site-side linter changes.
- Tasks 20–22 (e2e fixture) run last; require all earlier tasks complete.

**TDD ordering:** every elisp task writes failing tests first via ert; every Python task writes failing tests first via unittest. Lua/LaTeX testing is integration-style — see Task 9 / Task 6 notes.

---

## Task 1: `multi-export-doc-p` predicate + filter module scaffold

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-filter.el`
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-filter-test.el`

- [ ] **Step 1: Write the failing test**

```elisp
;; a3madkour-publish-multi-filter-test.el (new file — header only at this step)
;;; a3madkour-publish-multi-filter-test.el --- Tests for multi-export filter -*- lexical-binding: t; -*-
(require 'ert)
(require 'a3madkour-publish-multi-filter)

(ert-deftest a3madkour-pub-multi-filter/detects-opt-in-keyword ()
  "Buffer with `#+multi_export: t` is recognized as multi-export."
  (with-temp-buffer
    (insert "#+title: Demo\n#+multi_export: t\n\n* Heading\n")
    (org-mode)
    (should (a3madkour-pub-multi-filter--doc-p))))

(ert-deftest a3madkour-pub-multi-filter/rejects-missing-keyword ()
  "Buffer without `#+multi_export:` is not multi-export."
  (with-temp-buffer
    (insert "#+title: Demo\n\n* Heading\n")
    (org-mode)
    (should-not (a3madkour-pub-multi-filter--doc-p))))

(ert-deftest a3madkour-pub-multi-filter/rejects-falsy-value ()
  "Buffer with `#+multi_export: nil` (or any non-t value) is not multi-export."
  (with-temp-buffer
    (insert "#+multi_export: nil\n")
    (org-mode)
    (should-not (a3madkour-pub-multi-filter--doc-p))))

(provide 'a3madkour-publish-multi-filter-test)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/dotfiles && emacs --batch -L emacs-configs/custom/lisp \
  -l a3madkour-publish-multi-filter-test.el \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -20
```

Expected: load fails with `Cannot open load file: a3madkour-publish-multi-filter`.

- [ ] **Step 3: Write minimal implementation**

```elisp
;;; a3madkour-publish-multi-filter.el --- D.2 multi-export visibility + vocab filter -*- lexical-binding: t; -*-
;; Shared filter module for the D.2 multi-target export pipeline.
;; Provides: opt-in detection, visibility-tag filter, D.1 vocab translation.
(require 'org)
(require 'org-element)

(defconst a3madkour-pub-multi-filter--opt-in-keyword "MULTI_EXPORT"
  "Org buffer-keyword that opts a document into the multi-export pipeline.")

(defun a3madkour-pub-multi-filter--doc-p ()
  "Return non-nil iff current buffer carries `#+multi_export: t'."
  (let ((value (cadar (org-collect-keywords
                       (list a3madkour-pub-multi-filter--opt-in-keyword)))))
    (and value (string= (downcase (string-trim value)) "t"))))

(provide 'a3madkour-publish-multi-filter)
;;; a3madkour-publish-multi-filter.el ends here
```

- [ ] **Step 4: Run test to verify it passes**

Same command as Step 2. Expected: `3 tests passed`.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi-filter.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-filter-test.el
git commit -m "feat(d.2): multi-export filter module + opt-in detection"
```

---

## Task 2: Visibility-tag filter (5 tags + stock `:noexport:`)

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-filter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-filter-test.el`

- [ ] **Step 1: Write the failing tests**

Append to the test file:

```elisp
(defun a3madkour-pub-multi-filter--test--collect-headings (backend buffer-text)
  "Apply filter for BACKEND on BUFFER-TEXT, return remaining top-level headings."
  (with-temp-buffer
    (insert buffer-text)
    (org-mode)
    (a3madkour-pub-multi-filter--apply-visibility backend)
    (let (headings)
      (org-map-entries (lambda () (push (org-get-heading t t t t) headings)) "LEVEL=1")
      (nreverse headings))))

(defconst a3madkour-pub-multi-filter--test--tagged-doc
  "#+multi_export: t

* Universal
* Web only                                          :WEB_ONLY:
* Paper only                                        :PAPER_ONLY:
* PDF skipped                                       :NOEXPORT_PDF:
* Web skipped                                       :NOEXPORT_WEB:
* Word skipped                                      :NOEXPORT_WORD:
")

(ert-deftest a3madkour-pub-multi-filter/visibility-hugo ()
  "Hugo/md backend drops NOEXPORT_WEB and PAPER_ONLY."
  (let ((kept (a3madkour-pub-multi-filter--test--collect-headings
               'hugo a3madkour-pub-multi-filter--test--tagged-doc)))
    (should (member "Universal" kept))
    (should (member "Web only" kept))
    (should (member "PDF skipped" kept))
    (should (member "Word skipped" kept))
    (should-not (member "Paper only" kept))
    (should-not (member "Web skipped" kept))))

(ert-deftest a3madkour-pub-multi-filter/visibility-latex ()
  "LaTeX backend drops NOEXPORT_PDF and WEB_ONLY."
  (let ((kept (a3madkour-pub-multi-filter--test--collect-headings
               'latex a3madkour-pub-multi-filter--test--tagged-doc)))
    (should (member "Universal" kept))
    (should (member "Paper only" kept))
    (should (member "Web skipped" kept))
    (should (member "Word skipped" kept))
    (should-not (member "Web only" kept))
    (should-not (member "PDF skipped" kept))))

(ert-deftest a3madkour-pub-multi-filter/visibility-pandoc ()
  "Pandoc (word) backend drops NOEXPORT_WORD, WEB_ONLY, and PAPER_ONLY."
  (let ((kept (a3madkour-pub-multi-filter--test--collect-headings
               'pandoc a3madkour-pub-multi-filter--test--tagged-doc)))
    (should (member "Universal" kept))
    (should (member "PDF skipped" kept))
    (should (member "Web skipped" kept))
    (should-not (member "Web only" kept))
    (should-not (member "Paper only" kept))
    (should-not (member "Word skipped" kept))))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/dotfiles && emacs --batch -L emacs-configs/custom/lisp \
  -l a3madkour-publish-multi-filter-test.el \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -20
```

Expected: `a3madkour-pub-multi-filter--apply-visibility` is undefined.

- [ ] **Step 3: Implement visibility-tag filter**

Add to `a3madkour-publish-multi-filter.el` (before `provide`):

```elisp
(defconst a3madkour-pub-multi-filter--skip-rules
  '((hugo   . ("NOEXPORT_WEB"  "PAPER_ONLY"))
    (md     . ("NOEXPORT_WEB"  "PAPER_ONLY"))
    (latex  . ("NOEXPORT_PDF"  "WEB_ONLY"))
    (pandoc . ("NOEXPORT_WORD" "WEB_ONLY" "PAPER_ONLY")))
  "Alist of backend → list of tag names whose subtrees must be dropped.
Stock `:noexport:' is dropped natively by each backend and is not listed.")

(defun a3madkour-pub-multi-filter--skip-tags-for (backend)
  "Return the list of tag names to drop for BACKEND, or nil if unknown."
  (cdr (assq backend a3madkour-pub-multi-filter--skip-rules)))

(defun a3madkour-pub-multi-filter--apply-visibility (backend)
  "Delete subtrees in the current buffer that are tagged for BACKEND skip.
No-op when BACKEND has no rules.  Iterates from last to first so deletions
do not invalidate the position of earlier subtrees."
  (let ((skip-tags (a3madkour-pub-multi-filter--skip-tags-for backend)))
    (when skip-tags
      (save-excursion
        (goto-char (point-max))
        (let (positions)
          (org-map-entries
           (lambda ()
             (let ((tags (org-get-tags nil nil)))
               (when (cl-some (lambda (tag) (member tag tags)) skip-tags)
                 (push (point) positions)))))
          (dolist (pos (sort positions #'>))
            (goto-char pos)
            (org-cut-subtree)))))))
```

- [ ] **Step 4: Run tests to verify they pass**

Same command as Step 2. Expected: `6 tests passed`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi-filter.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-filter-test.el
git commit -m "feat(d.2): visibility-tag filter (5 tags + per-backend skip rules)"
```

---

## Task 3: D.1 vocab translation + cross-ref + hook registration

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-filter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-filter-test.el`

The D.1 vocab is `(theorem lemma corollary proposition definition proof remark example note claim conjecture axiom)`. `#+attr_shortcode: :title T :id thm-ivt` on a `#+begin_<kind>` block must translate to per-backend annotations:

- **LaTeX**: inject `#+attr_latex: :options [T]` (title) + `#+name: thm-ivt` (label) before the block.
- **Pandoc**: rewrite the special-block to a Pandoc-friendly form (`#+attr_html: :class <kind> :id thm-ivt :data-title T`) before pandoc reads the filtered org file. Pandoc-org turns `#+attr_html:` annotations into Div attributes.
- **Hugo**: ox-hugo already handles `#+attr_shortcode:` natively (D.1 — no-op here).

- [ ] **Step 1: Write the failing tests**

Append to the test file:

```elisp
(defconst a3madkour-pub-multi-filter--block-kinds
  '("theorem" "lemma" "corollary" "proposition"
    "definition" "proof" "remark" "example" "note"
    "claim" "conjecture" "axiom"))

(ert-deftest a3madkour-pub-multi-filter/vocab-latex-injects-attrs ()
  "attr_shortcode on a D.1 block emits attr_latex + name for LaTeX backend."
  (with-temp-buffer
    (insert "#+multi_export: t\n\n"
            "#+attr_shortcode: :title \"Intermediate Value\" :id thm-ivt\n"
            "#+begin_theorem\nFoo.\n#+end_theorem\n")
    (org-mode)
    (a3madkour-pub-multi-filter--translate-vocab 'latex)
    (let ((text (buffer-string)))
      (should (string-match-p "#\\+attr_latex: :options \\[Intermediate Value\\]" text))
      (should (string-match-p "#\\+name: thm-ivt" text)))))

(ert-deftest a3madkour-pub-multi-filter/vocab-pandoc-injects-attrs ()
  "attr_shortcode on a D.1 block emits attr_html for pandoc backend."
  (with-temp-buffer
    (insert "#+attr_shortcode: :title \"Intermediate Value\" :id thm-ivt\n"
            "#+begin_theorem\nFoo.\n#+end_theorem\n")
    (org-mode)
    (a3madkour-pub-multi-filter--translate-vocab 'pandoc)
    (let ((text (buffer-string)))
      (should (string-match-p "#\\+attr_html: :class theorem :id thm-ivt :data-title \"Intermediate Value\"" text)))))

(ert-deftest a3madkour-pub-multi-filter/vocab-skips-unknown-kinds ()
  "Non-D.1 special blocks are untouched."
  (with-temp-buffer
    (insert "#+attr_shortcode: :title T :id x\n"
            "#+begin_quote\nq\n#+end_quote\n")
    (org-mode)
    (let ((before (buffer-string)))
      (a3madkour-pub-multi-filter--translate-vocab 'latex)
      (should (string= before (buffer-string))))))

(ert-deftest a3madkour-pub-multi-filter/crossref-latex ()
  "[[#thm-ivt][text]] org link rewrites to \\hyperref for latex backend."
  (with-temp-buffer
    (insert "See [[#thm-ivt][Theorem 1]] for details.\n")
    (org-mode)
    (a3madkour-pub-multi-filter--rewrite-crossrefs 'latex)
    (should (string-match-p "\\\\hyperref\\[thm-ivt\\]{Theorem 1}" (buffer-string)))))

(ert-deftest a3madkour-pub-multi-filter/crossref-pandoc-untouched ()
  "Pandoc handles [[#id]] natively; rewrite is a no-op."
  (with-temp-buffer
    (insert "See [[#thm-ivt][Theorem 1]] for details.\n")
    (org-mode)
    (let ((before (buffer-string)))
      (a3madkour-pub-multi-filter--rewrite-crossrefs 'pandoc)
      (should (string= before (buffer-string))))))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/dotfiles && emacs --batch -L emacs-configs/custom/lisp \
  -l a3madkour-publish-multi-filter-test.el \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -25
```

Expected: 5 failures, `a3madkour-pub-multi-filter--translate-vocab` undefined.

- [ ] **Step 3: Implement vocab translation + cross-ref rewrite + hook**

Add to `a3madkour-publish-multi-filter.el` (before `provide`):

```elisp
(defconst a3madkour-pub-multi-filter--vocab-kinds
  '("theorem" "lemma" "corollary" "proposition"
    "definition" "proof" "remark" "example" "note"
    "claim" "conjecture" "axiom")
  "D.1 semantic block kinds the filter recognizes.")

(defun a3madkour-pub-multi-filter--parse-attr-shortcode (attr-line)
  "Parse `:title T :id S' from ATTR-LINE (the value after `#+attr_shortcode: ').
Returns (cons TITLE-OR-NIL ID-OR-NIL)."
  (let ((title (when (string-match
                      ":title[ \t]+\\(\"\\([^\"]+\\)\"\\|\\([^ \t\n]+\\)\\)"
                      attr-line)
                 (or (match-string 2 attr-line) (match-string 3 attr-line))))
        (id (when (string-match ":id[ \t]+\\([^ \t\n]+\\)" attr-line)
              (match-string 1 attr-line))))
    (cons title id)))

(defun a3madkour-pub-multi-filter--translate-vocab (backend)
  "Walk current buffer; for each D.1 special block preceded by `#+attr_shortcode:',
rewrite that attr line into BACKEND-appropriate org annotations."
  (when (memq backend '(latex pandoc))
    (save-excursion
      (goto-char (point-min))
      (while (re-search-forward
              "^#\\+attr_shortcode:[ \t]+\\(.*\\)\n#\\+begin_\\([a-z]+\\)" nil t)
        (let* ((attr-line (match-string 1))
               (kind (match-string 2)))
          (when (member kind a3madkour-pub-multi-filter--vocab-kinds)
            (let* ((parsed (a3madkour-pub-multi-filter--parse-attr-shortcode attr-line))
                   (title (car parsed))
                   (id (cdr parsed)))
              (goto-char (match-beginning 0))
              (delete-region (match-beginning 0)
                             (save-excursion (forward-line 1) (point)))
              (pcase backend
                ('latex
                 (when title
                   (insert (format "#+attr_latex: :options [%s]\n" title)))
                 (when id
                   (insert (format "#+name: %s\n" id))))
                ('pandoc
                 (insert "#+attr_html:")
                 (insert (format " :class %s" kind))
                 (when id (insert (format " :id %s" id)))
                 (when title (insert (format " :data-title \"%s\"" title)))
                 (insert "\n"))))))))))

(defun a3madkour-pub-multi-filter--rewrite-crossrefs (backend)
  "Rewrite [[#id][text]] org links for BACKEND.
LaTeX → `\\hyperref[id]{text}'.  Other backends: no-op."
  (when (eq backend 'latex)
    (save-excursion
      (goto-char (point-min))
      (while (re-search-forward "\\[\\[#\\([a-zA-Z0-9_-]+\\)\\]\\[\\([^]]+\\)\\]\\]" nil t)
        (replace-match (format "\\\\hyperref[%s]{%s}"
                               (match-string 1) (match-string 2))
                       t t)))))

(defun a3madkour-pub-multi-filter--before-processing (backend)
  "`org-export-before-processing-hook' entry point.
Runs only when buffer is multi-export-opted-in.  Applies visibility + vocab + crossref."
  (when (a3madkour-pub-multi-filter--doc-p)
    (a3madkour-pub-multi-filter--apply-visibility backend)
    (a3madkour-pub-multi-filter--translate-vocab backend)
    (a3madkour-pub-multi-filter--rewrite-crossrefs backend)))

(defun a3madkour-pub-multi-filter-install ()
  "Install the multi-export filter on org's pre-processing hook (idempotent)."
  (add-hook 'org-export-before-processing-hook
            #'a3madkour-pub-multi-filter--before-processing))

(a3madkour-pub-multi-filter-install)
```

- [ ] **Step 4: Run tests to verify they pass**

Same command as Step 2. Expected: `11 tests passed`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi-filter.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-filter-test.el
git commit -m "feat(d.2): D.1 vocab translation + crossref + hook registration"
```

---

## Task 4: `madkour-paper.cls` LaTeX class

**Files:**
- Create: `~/Sync/Workspace/a3madkour.github.io/tools/templates/madkour-paper.cls`
- Create: `~/Sync/Workspace/a3madkour.github.io/tools/templates/test-fixtures/smoke.tex`

LaTeX class is template content, not unit-testable in isolation. Test = compile a tiny smoke fixture using the class and assert a `.pdf` is produced. Skip the test if `xelatex` is not on PATH.

- [ ] **Step 1: Create the templates directory + smoke fixture**

```bash
mkdir -p /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates/test-fixtures
```

Create `tools/templates/test-fixtures/smoke.tex`:

```latex
\documentclass{madkour-paper}
\title{Smoke}
\author{Test}
\begin{document}
\maketitle
\begin{theorem}\label{thm-x}Trivial.\end{theorem}
\begin{lemma}Follows.\end{lemma}
\begin{definition}Trivial def.\end{definition}
\begin{proof}Done.\end{proof}
\end{document}
```

- [ ] **Step 2: Write the failing smoke test (shell)**

Plan-only: the smoke is run manually as part of Step 4. No automated unit test for the class file itself — the elisp tests in Tasks 5–7 mock `xelatex` invocations; the real-build smoke happens here and again at Task 21.

- [ ] **Step 3: Create the class file**

Create `tools/templates/madkour-paper.cls`:

```latex
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{madkour-paper}[2026/06/02 Madkour multi-export paper class]

\LoadClass[11pt]{article}

\RequirePackage[utf8]{inputenc}
\RequirePackage{amsmath,amssymb,amsthm}
\RequirePackage{microtype,csquotes,hyperref}
\RequirePackage[backend=biber,style=authoryear]{biblatex}
\RequirePackage{graphicx,listings}

% Theorem-family — shared counter per AMS convention.
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{claim}[theorem]{Claim}
\newtheorem{conjecture}{Conjecture}
\newtheorem{axiom}{Axiom}

% Definition-style — upright body, bold header.
\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{example}{Example}

% Remark-style — upright body, italic header.
\theoremstyle{remark}
\newtheorem{remark}{Remark}
\newtheorem{note}{Note}

% proof — amsthm built-in; auto-appends ∎
```

- [ ] **Step 4: Smoke build and verify**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates/test-fixtures
xelatex -interaction=nonstopmode smoke.tex 2>&1 | tail -8
ls -la smoke.pdf
```

Expected: `smoke.pdf` exists, file size > 1 KB. Clean up: `rm -f smoke.aux smoke.log smoke.out smoke.pdf`.

- [ ] **Step 5: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/templates/madkour-paper.cls \
        tools/templates/test-fixtures/smoke.tex
git commit -m "feat(d.2): madkour-paper.cls (article + amsthm + 12 envs + biblatex)"
```

---

## Task 5: `multi-pdf` module scaffold + tool defcustoms + tool probes

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-pdf.el`
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-pdf-test.el`

- [ ] **Step 1: Write the failing tests**

```elisp
;;; a3madkour-publish-multi-pdf-test.el --- Tests for PDF backend -*- lexical-binding: t; -*-
(require 'ert)
(require 'a3madkour-publish-multi-pdf)

(ert-deftest a3madkour-pub-multi-pdf/defcustoms-defined ()
  (should (boundp 'a3madkour-pub-multi-xelatex-command))
  (should (boundp 'a3madkour-pub-multi-biber-command))
  (should (boundp 'a3madkour-pub-multi-rsvg-convert-command)))

(ert-deftest a3madkour-pub-multi-pdf/probe-tools-all-present ()
  "When all tools resolve, probe returns nil (no missing)."
  (cl-letf (((symbol-function 'executable-find) (lambda (_) "/usr/bin/x")))
    (should-not (a3madkour-pub-multi-pdf--probe-tools))))

(ert-deftest a3madkour-pub-multi-pdf/probe-tools-missing-xelatex ()
  "When xelatex is missing, probe returns a list containing it."
  (cl-letf (((symbol-function 'executable-find)
             (lambda (cmd) (unless (string= cmd "xelatex") "/usr/bin/x"))))
    (let ((missing (a3madkour-pub-multi-pdf--probe-tools)))
      (should (member "xelatex" missing)))))

(provide 'a3madkour-publish-multi-pdf-test)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/dotfiles && emacs --batch -L emacs-configs/custom/lisp \
  -l a3madkour-publish-multi-pdf-test.el \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -10
```

Expected: load failure (module not yet created).

- [ ] **Step 3: Create the module**

Create `a3madkour-publish-multi-pdf.el`:

```elisp
;;; a3madkour-publish-multi-pdf.el --- D.2 PDF backend (ox-latex + xelatex + biber) -*- lexical-binding: t; -*-
(require 'cl-lib)
(require 'a3madkour-publish-multi-filter)

(defgroup a3madkour-pub-multi nil
  "D.2 multi-target export pipeline." :group 'org)

(defcustom a3madkour-pub-multi-xelatex-command "xelatex"
  "External `xelatex' command name or absolute path."
  :type 'string :group 'a3madkour-pub-multi)

(defcustom a3madkour-pub-multi-biber-command "biber"
  "External `biber' command name or absolute path."
  :type 'string :group 'a3madkour-pub-multi)

(defcustom a3madkour-pub-multi-rsvg-convert-command "rsvg-convert"
  "External `rsvg-convert' command name or absolute path."
  :type 'string :group 'a3madkour-pub-multi)

(defun a3madkour-pub-multi-pdf--probe-tools ()
  "Return list of missing required commands (xelatex/biber/rsvg-convert), or nil if all present."
  (let (missing)
    (dolist (cmd (list a3madkour-pub-multi-xelatex-command
                       a3madkour-pub-multi-biber-command
                       a3madkour-pub-multi-rsvg-convert-command))
      (unless (executable-find cmd)
        (push cmd missing)))
    (nreverse missing)))

(provide 'a3madkour-publish-multi-pdf)
;;; a3madkour-publish-multi-pdf.el ends here
```

- [ ] **Step 4: Run tests to verify they pass**

Same command as Step 2. Expected: `3 tests passed`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi-pdf.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-pdf-test.el
git commit -m "feat(d.2): multi-pdf module scaffold + tool defcustoms + probes"
```

---

## Task 6: `multi-pdf/run` — SVG conv + ox-latex + xelatex loop + placement

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-pdf.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-pdf-test.el`

- [ ] **Step 1: Write the failing tests**

Append to test file:

```elisp
(ert-deftest a3madkour-pub-multi-pdf/svg-to-pdf-builds-command ()
  "SVG → PDF helper builds `rsvg-convert -f pdf SRC -o DST'."
  (let (captured)
    (cl-letf (((symbol-function 'call-process)
               (lambda (cmd _ _ _ &rest args) (push (cons cmd args) captured) 0)))
      (a3madkour-pub-multi-pdf--convert-svg "/src/a.svg" "/dst/a.pdf")
      (let ((call (car captured)))
        (should (string= (car call) a3madkour-pub-multi-rsvg-convert-command))
        (should (member "-f" (cdr call)))
        (should (member "pdf" (cdr call)))
        (should (member "/src/a.svg" (cdr call)))
        (should (member "/dst/a.pdf" (cdr call)))))))

(ert-deftest a3madkour-pub-multi-pdf/xelatex-loop-calls-four-times ()
  "Latex compile invokes xelatex/biber/xelatex/xelatex sequence (4 commands)."
  (let (cmd-log)
    (cl-letf (((symbol-function 'call-process)
               (lambda (cmd _ _ _ &rest _args) (push cmd cmd-log) 0)))
      (a3madkour-pub-multi-pdf--compile-tex "/tmp/x/foo.tex")
      (let ((sequence (nreverse cmd-log)))
        (should (= 4 (length sequence)))
        (should (string= (nth 0 sequence) a3madkour-pub-multi-xelatex-command))
        (should (string= (nth 1 sequence) a3madkour-pub-multi-biber-command))
        (should (string= (nth 2 sequence) a3madkour-pub-multi-xelatex-command))
        (should (string= (nth 3 sequence) a3madkour-pub-multi-xelatex-command))))))

(ert-deftest a3madkour-pub-multi-pdf/compile-tex-returns-nil-on-failure ()
  "When xelatex exits non-zero, compile-tex returns nil and stops the loop."
  (cl-letf (((symbol-function 'call-process)
             (lambda (&rest _) 1)))
    (should-not (a3madkour-pub-multi-pdf--compile-tex "/tmp/x/foo.tex"))))
```

- [ ] **Step 2: Run tests to verify they fail**

Same command as Task 5 Step 2. Expected: helpers undefined.

- [ ] **Step 3: Implement SVG conversion + xelatex loop + run sequence**

Add to `a3madkour-publish-multi-pdf.el` (before `provide`):

```elisp
(defun a3madkour-pub-multi-pdf--convert-svg (src dst)
  "Convert SVG at SRC to PDF at DST via `rsvg-convert -f pdf'.
Returns 0 on success."
  (make-directory (file-name-directory dst) t)
  (call-process a3madkour-pub-multi-rsvg-convert-command nil nil nil
                "-f" "pdf" src "-o" dst))

(defun a3madkour-pub-multi-pdf--compile-tex (tex-path)
  "Run xelatex → biber → xelatex → xelatex on TEX-PATH in its own directory.
Returns t on full success, nil on any non-zero exit."
  (let* ((dir (file-name-directory tex-path))
         (base (file-name-base tex-path))
         (default-directory dir)
         (seq (list a3madkour-pub-multi-xelatex-command
                    a3madkour-pub-multi-biber-command
                    a3madkour-pub-multi-xelatex-command
                    a3madkour-pub-multi-xelatex-command)))
    (cl-loop for cmd in seq
             for arg = (if (string= cmd a3madkour-pub-multi-biber-command) base
                         (concat base ".tex"))
             for rc = (call-process cmd nil nil nil "-interaction=nonstopmode" arg)
             unless (zerop rc) return nil
             finally return t)))

(defun a3madkour-pub-multi-pdf--list-svg-figures (source-file)
  "Return list of absolute SVG paths referenced by SOURCE-FILE via `[[file:…]]'.
Delegates to B.4's existing asset walker if available; falls back to nil."
  (when (fboundp 'a3madkour-pub-assets/list-referenced-files)
    (cl-remove-if-not
     (lambda (p) (string= "svg" (file-name-extension p)))
     (a3madkour-pub-assets/list-referenced-files source-file))))

(defun a3madkour-pub-multi-pdf/run (source-file slug bundle-dir templates-dir)
  "Run the PDF backend for SOURCE-FILE / SLUG → BUNDLE-DIR/SLUG.pdf.
TEMPLATES-DIR is the path to `tools/templates/' (contains `madkour-paper.cls').
Returns the absolute path of the placed PDF on success, nil on failure."
  (let* ((work-dir (expand-file-name (format "multi-export-%s/" slug)
                                     temporary-file-directory))
         (fig-dir (expand-file-name "figures/" work-dir))
         (tex-path (expand-file-name (concat slug ".tex") work-dir)))
    (make-directory fig-dir t)
    ;; Make madkour-paper.cls discoverable to xelatex (place a symlink/copy in work-dir).
    (copy-file (expand-file-name "madkour-paper.cls" templates-dir)
               (expand-file-name "madkour-paper.cls" work-dir) t)
    ;; Convert referenced SVGs to PDF for LaTeX.
    (dolist (svg (a3madkour-pub-multi-pdf--list-svg-figures source-file))
      (a3madkour-pub-multi-pdf--convert-svg
       svg (expand-file-name (concat (file-name-base svg) ".pdf") fig-dir)))
    ;; Export org → LaTeX (hooks fire automatically).
    (with-current-buffer (find-file-noselect source-file)
      (let ((org-latex-with-hyperref t))
        (org-latex-export-to-latex)))
    ;; Move the produced .tex into the work dir, then compile.
    (let ((source-tex (expand-file-name (concat slug ".tex")
                                        (file-name-directory source-file))))
      (when (file-exists-p source-tex)
        (rename-file source-tex tex-path t)))
    (when (a3madkour-pub-multi-pdf--compile-tex tex-path)
      (let ((built-pdf (expand-file-name (concat slug ".pdf") work-dir))
            (target (expand-file-name (concat slug ".pdf") bundle-dir)))
        (when (file-exists-p built-pdf)
          (rename-file built-pdf target t)
          target)))))
```

- [ ] **Step 4: Run tests to verify they pass**

Same command as Task 5 Step 2. Expected: `6 tests passed`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi-pdf.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-pdf-test.el
git commit -m "feat(d.2): multi-pdf/run — SVG conv + ox-latex + xelatex loop + placement"
```

---

## Task 7: `multi-pdf/run` error capture into `*a3madkour-pub*` log

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-pdf.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-pdf-test.el`

The `*a3madkour-pub*` log buffer is created by B.4. We append per-backend sections — see spec §3 error reporting example. Each section: `[✓] pdf → <path> (Ns)` or `[✗] pdf → <reason>` with foldable stderr snippet.

- [ ] **Step 1: Write the failing tests**

Append to test file:

```elisp
(ert-deftest a3madkour-pub-multi-pdf/log-success-line ()
  (let ((buf (generate-new-buffer "*log-test*")))
    (unwind-protect
        (progn
          (a3madkour-pub-multi-pdf--log-line buf t "/out/foo.pdf" 7.2 nil)
          (with-current-buffer buf
            (should (string-match-p "\\[✓\\] pdf .*foo\\.pdf .*(7.2s)"
                                    (buffer-string)))))
      (kill-buffer buf))))

(ert-deftest a3madkour-pub-multi-pdf/log-failure-snippet ()
  (let ((buf (generate-new-buffer "*log-test*")))
    (unwind-protect
        (progn
          (a3madkour-pub-multi-pdf--log-line buf nil nil 4.0 "! Undefined control sequence.")
          (with-current-buffer buf
            (let ((s (buffer-string)))
              (should (string-match-p "\\[✗\\] pdf" s))
              (should (string-match-p "Undefined control sequence" s)))))
      (kill-buffer buf))))
```

- [ ] **Step 2: Run tests to verify they fail**

Expected: 2 failures, `--log-line` undefined.

- [ ] **Step 3: Add logging helper**

Add to module:

```elisp
(defun a3madkour-pub-multi-pdf--log-line (buf successp path elapsed err-snippet)
  "Append a single log line to BUF for the PDF backend.
SUCCESSP is t for ✓ / nil for ✗.  PATH is target path on success.
ELAPSED is seconds (float).  ERR-SNIPPET is the stderr tail to inline on failure."
  (with-current-buffer buf
    (goto-char (point-max))
    (if successp
        (insert (format "  [✓] pdf    → %s   (%.1fs)\n" path elapsed))
      (insert (format "  [✗] pdf    → exit %.1fs\n" elapsed))
      (when err-snippet
        (insert (format "              %s\n" err-snippet))))))
```

- [ ] **Step 4: Run tests to verify they pass**

Expected: `8 tests passed`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi-pdf.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-pdf-test.el
git commit -m "feat(d.2): multi-pdf log-line helper for *a3madkour-pub* buffer"
```

---

## Task 8: `d2-blocks.lua` Pass 1 — numbering walker

**Files:**
- Create: `~/Sync/Workspace/a3madkour.github.io/tools/templates/d2-blocks.lua`
- Create: `~/Sync/Workspace/a3madkour.github.io/tools/templates/test-fixtures/numbering-input.org`
- Create: `~/Sync/Workspace/a3madkour.github.io/tools/templates/test-fixtures/test-numbering.sh`

Lua filter testing strategy: integration via pandoc. Run pandoc on a tiny org fixture with the filter, dump intermediate JSON via `pandoc -t json`, grep for the `d2-num` attribute values.

- [ ] **Step 1: Write the failing test fixture**

Create `tools/templates/test-fixtures/numbering-input.org`:

```org
#+title: Numbering smoke

#+begin_theorem
First theorem.
#+end_theorem

#+begin_lemma
First lemma (shares theorem family).
#+end_lemma

#+begin_definition
First definition.
#+end_definition

#+begin_theorem
Second theorem.
#+end_theorem

#+begin_proof
Proof body.
#+end_proof

#+begin_definition
Second definition.
#+end_definition
```

Create `tools/templates/test-fixtures/test-numbering.sh`:

```bash
#!/usr/bin/env bash
# Verify d2-blocks.lua's numbering pass against the org fixture.
# Run from the templates dir: ./test-fixtures/test-numbering.sh
set -euo pipefail
cd "$(dirname "$0")/.."
INPUT=test-fixtures/numbering-input.org
JSON=$(pandoc -f org -t json --lua-filter=d2-blocks.lua "$INPUT")

expect_num() {
  local kind="$1" want="$2"
  # Extract the d2-num attribute for the Nth Div of class $kind.
  if ! echo "$JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
def walk(o, kind):
    if isinstance(o, dict):
        if o.get('t') == 'Div':
            attrs = o.get('c', [None,None])[0]
            classes = attrs[1] if attrs else []
            kv = dict(attrs[2]) if attrs else {}
            if kind in classes:
                yield kv.get('d2-num','')
        for v in o.values(): yield from walk(v, kind)
    elif isinstance(o, list):
        for v in o: yield from walk(v, kind)
nums = list(walk(data, '$kind'))
print(','.join(nums))
" | grep -q "^$want\$"; then
    echo "FAIL: kind=$kind want=$want got=$(echo "$JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
def walk(o, kind):
    if isinstance(o, dict):
        if o.get('t') == 'Div':
            attrs = o.get('c', [None,None])[0]
            classes = attrs[1] if attrs else []
            kv = dict(attrs[2]) if attrs else {}
            if kind in classes:
                yield kv.get('d2-num','')
        for v in o.values(): yield from walk(v, kind)
    elif isinstance(o, list):
        for v in o: yield from walk(v, kind)
print(','.join(walk(data, '$kind')))
")"
    exit 1
  fi
}

# Theorem family shares counter: theorem=1, lemma=2, theorem=3.
expect_num theorem "1,3"
expect_num lemma "2"
# Definition has its own counter.
expect_num definition "1,2"
# Proof is unnumbered (empty d2-num).
expect_num proof ""

echo OK
```

```bash
chmod +x /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates/test-fixtures/test-numbering.sh
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates
./test-fixtures/test-numbering.sh
```

Expected: `pandoc: d2-blocks.lua: cannot open file` (filter doesn't exist).

- [ ] **Step 3: Create the Lua filter — Pass 1 only**

Create `tools/templates/d2-blocks.lua`:

```lua
-- d2-blocks.lua — pandoc filter for D.2 multi-export Word backend.
-- Pass 1: numbering. Walks Div nodes in document order; attaches `d2-num`
-- attribute per AMS counter convention.

local family_kinds = { theorem = true, lemma = true, corollary = true,
                       proposition = true, claim = true }
local own_counter_kinds = { definition = 0, remark = 0, example = 0,
                            note = 0, conjecture = 0, axiom = 0 }
local family_counter = 0

function Div(el)
  local kind = el.classes[1]
  if kind == nil then return nil end
  local n
  if family_kinds[kind] then
    family_counter = family_counter + 1
    n = family_counter
  elseif own_counter_kinds[kind] ~= nil then
    own_counter_kinds[kind] = own_counter_kinds[kind] + 1
    n = own_counter_kinds[kind]
  elseif kind == "proof" then
    n = nil
  else
    return nil  -- not a D.1 kind; pass through untouched
  end
  el.attributes["d2-num"] = (n and tostring(n)) or ""
  return el
end
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates
./test-fixtures/test-numbering.sh
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/templates/d2-blocks.lua tools/templates/test-fixtures/
git commit -m "feat(d.2): d2-blocks.lua pass 1 — D.1 vocab numbering walker"
```

---

## Task 9: `d2-blocks.lua` Pass 2 — styling (header paragraph + body wrap + proof ∎)

**Files:**
- Modify: `~/Sync/Workspace/a3madkour.github.io/tools/templates/d2-blocks.lua`
- Create: `~/Sync/Workspace/a3madkour.github.io/tools/templates/test-fixtures/styling-input.org`
- Create: `~/Sync/Workspace/a3madkour.github.io/tools/templates/test-fixtures/test-styling.sh`

For each `Div.<kind>`, prepend a header `Para` (with a `pandoc.Span` styled `<Kind> Header`) containing `"<Kind> <N>: <Title>"` or `"<Kind> <N>."` (no title) or `"Proof."` (proof; no number). Wrap body in `<Kind> Body` style. Proof appends `∎` to the last paragraph.

- [ ] **Step 1: Write the failing test fixture**

Create `tools/templates/test-fixtures/styling-input.org`:

```org
#+title: Styling smoke

#+attr_html: :class theorem :data-title "Intermediate Value"
#+begin_theorem
Body of theorem.
#+end_theorem

#+begin_definition
Untitled definition body.
#+end_definition

#+begin_proof
Proof body line one.

Last line.
#+end_proof
```

Create `tools/templates/test-fixtures/test-styling.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
INPUT=test-fixtures/styling-input.org
JSON=$(pandoc -f org -t json --lua-filter=d2-blocks.lua "$INPUT")

# Sanity: header for titled theorem contains "Theorem 1: Intermediate Value".
if ! echo "$JSON" | grep -q '"Intermediate Value"'; then
  echo "FAIL: titled theorem header missing title"; exit 1
fi
# Sanity: definition header reads "Definition 1." with no title.
if ! echo "$JSON" | python3 -c "
import json,sys
def text_of(o):
    if isinstance(o,dict):
        if o.get('t')=='Str': return o.get('c','')
        return ''.join(text_of(v) for v in o.values())
    if isinstance(o,list): return ' '.join(text_of(v) for v in o)
    return ''
data=json.load(sys.stdin)
flat=text_of(data)
assert 'Definition 1' in flat, flat
print(flat)
" > /dev/null; then
  echo "FAIL: Definition header"; exit 1
fi
# Proof: appended ∎ tombstone, header label \"Proof.\" without number.
if ! echo "$JSON" | grep -q "∎"; then
  echo "FAIL: proof tombstone missing"; exit 1
fi
echo OK
```

```bash
chmod +x /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates/test-fixtures/test-styling.sh
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates
./test-fixtures/test-styling.sh
```

Expected: FAIL (no styling pass yet).

- [ ] **Step 3: Add the styling pass**

Replace the existing `function Div(el)` block in `d2-blocks.lua` with the combined two-pass version:

```lua
-- d2-blocks.lua — pandoc filter for D.2 multi-export Word backend.
-- Pass 1: numbering; Pass 2: styling.

local family_kinds = { theorem = true, lemma = true, corollary = true,
                       proposition = true, claim = true }
local own_counter_kinds = { definition = 0, remark = 0, example = 0,
                            note = 0, conjecture = 0, axiom = 0 }
local family_counter = 0

-- Map kind → display label (capitalized; same as the kind itself for D.2).
local label_of = {
  theorem = "Theorem", lemma = "Lemma", corollary = "Corollary",
  proposition = "Proposition", definition = "Definition", proof = "Proof",
  remark = "Remark", example = "Example", note = "Note",
  claim = "Claim", conjecture = "Conjecture", axiom = "Axiom",
}

local function header_style(kind)
  return label_of[kind] .. " Header"
end

local function body_style(kind)
  return label_of[kind] .. " Body"
end

local function header_text(kind, num, title)
  local label = label_of[kind]
  if kind == "proof" then return label .. "." end
  if title and title ~= "" then
    return label .. " " .. num .. ": " .. title
  end
  return label .. " " .. num .. "."
end

local function make_header_para(kind, num, title)
  local txt = header_text(kind, num, title)
  local span = pandoc.Span({ pandoc.Str(txt) },
                           pandoc.Attr("", {}, { { "custom-style", header_style(kind) } }))
  return pandoc.Para({ span })
end

local function wrap_body_style(kind, blocks)
  -- Apply the `<Kind> Body' custom-style to each Para in the block list.
  return pandoc.walk_block(pandoc.Div(blocks), {
    Para = function(p)
      local span = pandoc.Span(p.content,
                               pandoc.Attr("", {}, { { "custom-style", body_style(kind) } }))
      return pandoc.Para({ span })
    end,
  }).content
end

function Div(el)
  local kind = el.classes[1]
  if kind == nil or label_of[kind] == nil then return nil end

  local n
  if family_kinds[kind] then
    family_counter = family_counter + 1
    n = family_counter
  elseif own_counter_kinds[kind] ~= nil then
    own_counter_kinds[kind] = own_counter_kinds[kind] + 1
    n = own_counter_kinds[kind]
  elseif kind == "proof" then
    n = nil
  end
  el.attributes["d2-num"] = (n and tostring(n)) or ""

  local title = el.attributes["data-title"] or ""
  local header = make_header_para(kind, n, title)
  local body = wrap_body_style(kind, el.content)

  -- Proof: append ∎ to the last paragraph in body.
  if kind == "proof" and #body > 0 then
    local last = body[#body]
    if last.t == "Para" then
      table.insert(last.content, pandoc.Space())
      table.insert(last.content, pandoc.Str("∎"))
    end
  end

  el.content = { header }
  for _, b in ipairs(body) do table.insert(el.content, b) end
  return el
end
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates
./test-fixtures/test-numbering.sh
./test-fixtures/test-styling.sh
```

Expected: both print `OK`.

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/templates/d2-blocks.lua tools/templates/test-fixtures/
git commit -m "feat(d.2): d2-blocks.lua pass 2 — header + body styling + proof ∎"
```

---

## Task 10: `reference.docx` — 12 header + 12 body styles

**Files:**
- Create: `~/Sync/Workspace/a3madkour.github.io/tools/templates/reference.docx`

This is a hand-authored binary file. Open LibreOffice (`libreoffice --writer reference.docx`) or Word and define 24 paragraph styles:

| Kind | Header style | Body style | Visual tier |
|---|---|---|---|
| Theorem | `Theorem Header` | `Theorem Body` | Strong (bold burgundy + italic title) |
| Lemma | `Lemma Header` | `Lemma Body` | Strong |
| Corollary | `Corollary Header` | `Corollary Body` | Strong |
| Proposition | `Proposition Header` | `Proposition Body` | Strong |
| Definition | `Definition Header` | `Definition Body` | Strong |
| Claim | `Claim Header` | `Claim Body` | Strong |
| Conjecture | `Conjecture Header` | `Conjecture Body` | Soft (semi-bold ink-soft + italic title) |
| Axiom | `Axiom Header` | `Axiom Body` | Soft |
| Remark | `Remark Header` | `Remark Body` | Soft |
| Example | `Example Header` | `Example Body` | Soft |
| Note | `Note Header` | `Note Body` | Soft |
| Proof | `Proof Header` | `Proof Body` | Chrome-less (italic "Proof." no number) |

Burgundy ≈ `#7A1F2B` (matches `--color-burgundy` token). Ink-soft ≈ `#3A3A3A`.

- [ ] **Step 1: Bootstrap with pandoc's default reference**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates
pandoc --print-default-data-file reference.docx > reference.docx
```

This gives a baseline Word doc to extend. Pandoc maps `pandoc.Span(_, {custom-style=...})` to character styles by default — but the Lua filter applies it to whole paragraphs, so they need to be defined as **paragraph styles** in Word.

- [ ] **Step 2: Define the 24 paragraph styles**

Open the doc, add each paragraph style per the table above. Each header style: bold/semibold + color per tier + italic for title portion (the title is part of the same span — apply italic via post-doc adjustment if needed; the styling tier sets the global tone). Each body style: indent 0.25" left margin (strong tier) or no indent (soft / chrome-less), inherit Normal otherwise.

Save and verify the styles list contains all 24 names.

- [ ] **Step 3: Smoke-build the styling fixture with the new reference**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/templates
pandoc -f org -t docx --reference-doc=reference.docx --lua-filter=d2-blocks.lua \
       test-fixtures/styling-input.org -o /tmp/styling-out.docx
```

Open `/tmp/styling-out.docx` in Word/LibreOffice. Verify:
- Titled theorem shows "Theorem 1: Intermediate Value" in the styled header treatment
- Untitled definition shows "Definition 1." plain
- Proof shows "Proof." italic + body ends with ∎

Iterate styles until the visual treatment matches D.1's §47 web aesthetic at a glance. **Don't perfect up front** — get them readable and ship; iterate after Task 21.

- [ ] **Step 4: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/templates/reference.docx
git commit -m "feat(d.2): reference.docx — 12 header + 12 body styles for D.1 vocab"
```

---

## Task 11: `multi-word` module — pandoc orchestration + SVG→PNG

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-word.el`
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-word-test.el`

- [ ] **Step 1: Write the failing tests**

```elisp
;;; a3madkour-publish-multi-word-test.el --- Tests for Word backend -*- lexical-binding: t; -*-
(require 'ert)
(require 'a3madkour-publish-multi-word)

(ert-deftest a3madkour-pub-multi-word/defcustoms-defined ()
  (should (boundp 'a3madkour-pub-multi-pandoc-command)))

(ert-deftest a3madkour-pub-multi-word/probe-tools-pandoc ()
  (cl-letf (((symbol-function 'executable-find)
             (lambda (cmd) (unless (string= cmd "pandoc") "/usr/bin/x"))))
    (should (member "pandoc" (a3madkour-pub-multi-word--probe-tools)))))

(ert-deftest a3madkour-pub-multi-word/svg-to-png-builds-command ()
  (let (captured)
    (cl-letf (((symbol-function 'call-process)
               (lambda (cmd _ _ _ &rest args) (push (cons cmd args) captured) 0)))
      (a3madkour-pub-multi-word--convert-svg "/src/a.svg" "/dst/a.png")
      (let ((args (cdr (car captured))))
        (should (member "-f" args))
        (should (member "png" args))
        (should (member "-d" args))
        (should (member "192" args))))))

(ert-deftest a3madkour-pub-multi-word/pandoc-command-assembled ()
  "Pandoc command includes reference-doc, lua-filter, citeproc, bibliography."
  (let (captured)
    (cl-letf (((symbol-function 'call-process)
               (lambda (cmd _ _ _ &rest args) (push (cons cmd args) captured) 0)))
      (a3madkour-pub-multi-word--invoke-pandoc
       "/tmp/x/in.org" "/out/x.docx"
       "/site/tools/templates/reference.docx"
       "/site/tools/templates/d2-blocks.lua"
       "/bib/library.bib")
      (let ((args (cdr (car captured))))
        (should (member "--reference-doc=/site/tools/templates/reference.docx" args))
        (should (member "--lua-filter=/site/tools/templates/d2-blocks.lua" args))
        (should (member "--citeproc" args))
        (should (member "--bibliography=/bib/library.bib" args))))))

(provide 'a3madkour-publish-multi-word-test)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/dotfiles && emacs --batch -L emacs-configs/custom/lisp \
  -l a3madkour-publish-multi-word-test.el \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -10
```

Expected: load fails.

- [ ] **Step 3: Implement the Word module**

```elisp
;;; a3madkour-publish-multi-word.el --- D.2 Word backend (pandoc) -*- lexical-binding: t; -*-
(require 'cl-lib)
(require 'a3madkour-publish-multi-filter)
(require 'a3madkour-publish-multi-pdf)  ;; for shared defgroup + rsvg-convert defcustom

(defcustom a3madkour-pub-multi-pandoc-command "pandoc"
  "External `pandoc' command name or absolute path."
  :type 'string :group 'a3madkour-pub-multi)

(defun a3madkour-pub-multi-word--probe-tools ()
  "Return list of missing required commands (pandoc/rsvg-convert), or nil."
  (let (missing)
    (dolist (cmd (list a3madkour-pub-multi-pandoc-command
                       a3madkour-pub-multi-rsvg-convert-command))
      (unless (executable-find cmd) (push cmd missing)))
    (nreverse missing)))

(defun a3madkour-pub-multi-word--convert-svg (src dst)
  "Convert SVG SRC → PNG DST via `rsvg-convert -f png -d 192'."
  (make-directory (file-name-directory dst) t)
  (call-process a3madkour-pub-multi-rsvg-convert-command nil nil nil
                "-f" "png" "-d" "192" src "-o" dst))

(defun a3madkour-pub-multi-word--invoke-pandoc (input-org output-docx
                                                 reference-doc lua-filter bib-path)
  "Run pandoc to convert INPUT-ORG → OUTPUT-DOCX using REFERENCE-DOC,
LUA-FILTER, and BIB-PATH (bibliography).  Returns 0 on success."
  (let ((args (list "-f" "org" "-t" "docx"
                    (format "--reference-doc=%s" reference-doc)
                    (format "--lua-filter=%s" lua-filter)
                    "--citeproc"
                    (format "--bibliography=%s" bib-path)
                    input-org "-o" output-docx)))
    (apply #'call-process a3madkour-pub-multi-pandoc-command nil nil nil args)))

(defun a3madkour-pub-multi-word--serialize-filtered (source-file out-org backend)
  "Read SOURCE-FILE, apply visibility + vocab + crossref filters for BACKEND,
write the result to OUT-ORG.  Pandoc cannot see Emacs' export hooks, so this
serializes the post-filter buffer for pandoc input."
  (with-temp-buffer
    (insert-file-contents source-file)
    (org-mode)
    (a3madkour-pub-multi-filter--apply-visibility backend)
    (a3madkour-pub-multi-filter--translate-vocab backend)
    (a3madkour-pub-multi-filter--rewrite-crossrefs backend)
    (write-region (point-min) (point-max) out-org nil 'silent)))

(defun a3madkour-pub-multi-word/run (source-file slug bundle-dir templates-dir bib-path)
  "Run the Word backend for SOURCE-FILE / SLUG → BUNDLE-DIR/SLUG.docx.
Returns the absolute path of the placed Word file on success, nil on failure."
  (let* ((work-dir (expand-file-name (format "multi-export-%s/" slug)
                                     temporary-file-directory))
         (fig-dir (expand-file-name "figures/" work-dir))
         (filtered-org (expand-file-name (concat slug "-filtered.org") work-dir))
         (out-docx (expand-file-name (concat slug ".docx") work-dir))
         (target (expand-file-name (concat slug ".docx") bundle-dir))
         (reference-doc (expand-file-name "reference.docx" templates-dir))
         (lua-filter (expand-file-name "d2-blocks.lua" templates-dir)))
    (make-directory fig-dir t)
    ;; Convert referenced SVGs to PNG for Word.
    (when (fboundp 'a3madkour-pub-assets/list-referenced-files)
      (dolist (svg (cl-remove-if-not
                    (lambda (p) (string= "svg" (file-name-extension p)))
                    (a3madkour-pub-assets/list-referenced-files source-file)))
        (a3madkour-pub-multi-word--convert-svg
         svg (expand-file-name (concat (file-name-base svg) ".png") fig-dir))))
    (a3madkour-pub-multi-word--serialize-filtered source-file filtered-org 'pandoc)
    (when (zerop (a3madkour-pub-multi-word--invoke-pandoc
                  filtered-org out-docx reference-doc lua-filter bib-path))
      (when (file-exists-p out-docx)
        (rename-file out-docx target t)
        target))))

(defun a3madkour-pub-multi-word--log-line (buf successp path elapsed err-snippet)
  "Append a single log line to BUF for the Word backend."
  (with-current-buffer buf
    (goto-char (point-max))
    (if successp
        (insert (format "  [✓] word   → %s   (%.1fs)\n" path elapsed))
      (insert (format "  [✗] word   → exit %.1fs\n" elapsed))
      (when err-snippet
        (insert (format "              %s\n" err-snippet))))))

(provide 'a3madkour-publish-multi-word)
;;; a3madkour-publish-multi-word.el ends here
```

- [ ] **Step 4: Run tests to verify they pass**

Expected: `4 tests passed`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi-word.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-word-test.el
git commit -m "feat(d.2): multi-word module — pandoc orchestration + SVG→PNG + filtered serialize"
```

---

## Task 12: Orchestrator scaffold + dispatch + tool/bib probes

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi.el`
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-test.el`

- [ ] **Step 1: Write the failing tests**

```elisp
;;; a3madkour-publish-multi-test.el --- Tests for D.2 orchestrator -*- lexical-binding: t; -*-
(require 'ert)
(require 'a3madkour-publish-multi)

(ert-deftest a3madkour-pub-multi/templates-dir-resolves ()
  "When SITE_ROOT is settable via helper, templates dir resolves under it."
  (cl-letf (((symbol-function 'a3madkour-pub-essays--site-root)
             (lambda () "/site")))
    (let ((a3madkour-pub-multi-templates-dir nil))
      (should (string= "/site/tools/templates/"
                       (a3madkour-pub-multi--templates-dir))))))

(ert-deftest a3madkour-pub-multi/templates-dir-respects-custom ()
  "Explicit defcustom overrides the auto-resolved default."
  (let ((a3madkour-pub-multi-templates-dir "/custom/tpl/"))
    (should (string= "/custom/tpl/" (a3madkour-pub-multi--templates-dir)))))

(ert-deftest a3madkour-pub-multi/orchestrate-partial-success-pdf-only ()
  "When PDF succeeds and Word fails, returns plist with :pdf set, :word nil."
  (cl-letf (((symbol-function 'a3madkour-pub-multi-pdf/run)
             (lambda (&rest _) "/bundle/x.pdf"))
            ((symbol-function 'a3madkour-pub-multi-word/run)
             (lambda (&rest _) nil))
            ((symbol-function 'a3madkour-pub-multi--patch-downloads-frontmatter)
             (lambda (&rest _) t)))
    (let ((result (a3madkour-pub-multi/orchestrate "/src.org" "x" "/bundle/")))
      (should (string= "/bundle/x.pdf" (plist-get result :pdf)))
      (should-not (plist-get result :word)))))

(ert-deftest a3madkour-pub-multi/orchestrate-both-fail ()
  "When both backends fail, plist :pdf and :word are nil."
  (cl-letf (((symbol-function 'a3madkour-pub-multi-pdf/run) (lambda (&rest _) nil))
            ((symbol-function 'a3madkour-pub-multi-word/run) (lambda (&rest _) nil))
            ((symbol-function 'a3madkour-pub-multi--patch-downloads-frontmatter)
             (lambda (&rest _) t)))
    (let ((result (a3madkour-pub-multi/orchestrate "/src.org" "x" "/bundle/")))
      (should-not (plist-get result :pdf))
      (should-not (plist-get result :word)))))

(provide 'a3madkour-publish-multi-test)
```

- [ ] **Step 2: Run tests to verify they fail**

Expected: load fails.

- [ ] **Step 3: Implement the orchestrator scaffold**

```elisp
;;; a3madkour-publish-multi.el --- D.2 multi-target export orchestrator -*- lexical-binding: t; -*-
(require 'cl-lib)
(require 'a3madkour-publish-multi-filter)
(require 'a3madkour-publish-multi-pdf)
(require 'a3madkour-publish-multi-word)

(defcustom a3madkour-pub-multi-templates-dir nil
  "Directory containing `madkour-paper.cls', `reference.docx', `d2-blocks.lua'.
When nil, resolves to `<SITE_ROOT>/tools/templates/' via
`a3madkour-pub-essays--site-root'."
  :type '(choice (const :tag "Auto from site-root" nil) directory)
  :group 'a3madkour-pub-multi)

(defun a3madkour-pub-multi--templates-dir ()
  "Return the templates directory absolute path with trailing slash."
  (or a3madkour-pub-multi-templates-dir
      (file-name-as-directory
       (expand-file-name "tools/templates"
                         (a3madkour-pub-essays--site-root)))))

(defun a3madkour-pub-multi--bib-path ()
  "Return the bibliography path from F.1's defcustom, or nil."
  (when (and (boundp 'a3madkour-pub-bib-path) a3madkour-pub-bib-path
             (file-readable-p a3madkour-pub-bib-path))
    a3madkour-pub-bib-path))

(defun a3madkour-pub-multi--has-citations-p (source-file)
  "Return non-nil if SOURCE-FILE contains any `[cite:@…]' refs."
  (with-temp-buffer
    (insert-file-contents source-file)
    (re-search-forward "\\[cite:@[^]]+\\]" nil t)))

(defun a3madkour-pub-multi/orchestrate (source-file slug bundle-dir)
  "Dispatch PDF + Word backends for SOURCE-FILE / SLUG → BUNDLE-DIR.
Each backend runs in `condition-case'.  Returns a plist:
  (:pdf <abs-path-or-nil> :word <abs-path-or-nil>)"
  (let* ((tpl-dir (a3madkour-pub-multi--templates-dir))
         (bib-path (a3madkour-pub-multi--bib-path))
         pdf-out word-out)
    ;; PDF backend
    (setq pdf-out
          (condition-case err
              (a3madkour-pub-multi-pdf/run source-file slug bundle-dir tpl-dir)
            (error
             (message "multi-export pdf backend error: %s" err)
             nil)))
    ;; Word backend (skip if citations present but no bib).
    (when (or (not (a3madkour-pub-multi--has-citations-p source-file)) bib-path)
      (setq word-out
            (condition-case err
                (a3madkour-pub-multi-word/run
                 source-file slug bundle-dir tpl-dir (or bib-path ""))
              (error
               (message "multi-export word backend error: %s" err)
               nil))))
    ;; Patch downloads frontmatter (idempotent).
    (a3madkour-pub-multi--patch-downloads-frontmatter
     (expand-file-name "index.md" bundle-dir) slug pdf-out word-out)
    (list :pdf pdf-out :word word-out)))

;; Stub — implemented in Task 13.
(defun a3madkour-pub-multi--patch-downloads-frontmatter (_index-path _slug _pdf _word)
  "Stub for Task 13."
  t)

(provide 'a3madkour-publish-multi)
;;; a3madkour-publish-multi.el ends here
```

- [ ] **Step 4: Run tests to verify they pass**

Expected: `4 tests passed`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-test.el
git commit -m "feat(d.2): orchestrator scaffold + dispatch + condition-case backends"
```

---

## Task 13: Frontmatter patch — `multi_export` + `downloads`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-test.el`

The frontmatter patch reads the index.md YAML, adds (or updates) `multi_export:` and `downloads:` keys, and writes back only if the content actually changed. Output uses **inline flow-style** `downloads: {pdf: "x.pdf", word: "x.docx"}` to keep the site linter's narrow YAML parser happy.

- [ ] **Step 1: Write the failing tests**

Append to the orchestrator test file:

```elisp
(defun a3madkour-pub-multi--test--with-temp-bundle (body)
  (let* ((dir (make-temp-file "multi-bundle-" t))
         (idx (expand-file-name "index.md" dir)))
    (unwind-protect (funcall body dir idx)
      (delete-directory dir t))))

(ert-deftest a3madkour-pub-multi/patch-adds-keys-when-pdf-only ()
  (a3madkour-pub-multi--test--with-temp-bundle
   (lambda (dir idx)
     (write-region "---\ntitle: \"X\"\n---\nBody\n" nil idx)
     (a3madkour-pub-multi--patch-downloads-frontmatter idx "x" "/b/x.pdf" nil)
     (let ((text (with-temp-buffer (insert-file-contents idx) (buffer-string))))
       (should (string-match-p "multi_export: true" text))
       (should (string-match-p "downloads: {pdf: \"x\\.pdf\"}" text))
       (should-not (string-match-p "word:" text))))))

(ert-deftest a3madkour-pub-multi/patch-emits-false-when-both-fail ()
  (a3madkour-pub-multi--test--with-temp-bundle
   (lambda (dir idx)
     (write-region "---\ntitle: \"X\"\n---\nBody\n" nil idx)
     (a3madkour-pub-multi--patch-downloads-frontmatter idx "x" nil nil)
     (let ((text (with-temp-buffer (insert-file-contents idx) (buffer-string))))
       (should (string-match-p "multi_export: false" text))
       (should-not (string-match-p "downloads:" text))))))

(ert-deftest a3madkour-pub-multi/patch-idempotent ()
  (a3madkour-pub-multi--test--with-temp-bundle
   (lambda (dir idx)
     (write-region "---\ntitle: \"X\"\n---\nBody\n" nil idx)
     (a3madkour-pub-multi--patch-downloads-frontmatter idx "x" "/b/x.pdf" "/b/x.docx")
     (let* ((after-first (file-attributes idx))
            (mtime-1 (file-attribute-modification-time after-first)))
       (sleep-for 1.1)  ;; ensure mtime resolution; tolerated for the idempotency check
       (a3madkour-pub-multi--patch-downloads-frontmatter idx "x" "/b/x.pdf" "/b/x.docx")
       (let* ((after-second (file-attributes idx))
              (mtime-2 (file-attribute-modification-time after-second)))
         (should (equal mtime-1 mtime-2)))))))
```

- [ ] **Step 2: Run tests to verify they fail**

Expected: 3 failures (current patch is a stub).

- [ ] **Step 3: Implement the patch helper**

Replace the stub in `a3madkour-publish-multi.el` with:

```elisp
(defun a3madkour-pub-multi--render-downloads-line (pdf word)
  "Return a YAML inline-flow `downloads: {…}' line, or nil if both missing."
  (let ((parts nil))
    (when pdf (push (format "pdf: \"%s.pdf\"" (file-name-base pdf)) parts))
    (when word (push (format "word: \"%s.docx\"" (file-name-base word)) parts))
    (when parts
      (format "downloads: {%s}" (string-join (nreverse parts) ", ")))))

(defun a3madkour-pub-multi--patch-downloads-frontmatter (index-path slug pdf word)
  "Patch INDEX-PATH frontmatter with `multi_export:' + `downloads:' keys.
INDEX-PATH is a Hugo bundle's index.md.  SLUG names the artifacts.
PDF / WORD are absolute paths to placed artifacts, or nil if missing.
Idempotent — writes only when content differs."
  (unless (file-exists-p index-path)
    (error "Cannot patch frontmatter — %s does not exist" index-path))
  (let* ((original (with-temp-buffer
                     (insert-file-contents index-path)
                     (buffer-string)))
         (success (or pdf word))
         (downloads-line (a3madkour-pub-multi--render-downloads-line pdf word))
         (multi-line (format "multi_export: %s" (if success "true" "false")))
         updated)
    (with-temp-buffer
      (insert original)
      (goto-char (point-min))
      ;; Drop existing multi_export / downloads lines first.
      (while (re-search-forward "^multi_export:.*\n" nil t) (replace-match ""))
      (goto-char (point-min))
      (while (re-search-forward "^downloads:.*\n" nil t) (replace-match ""))
      ;; Insert before closing `---' of frontmatter.
      (goto-char (point-min))
      (when (re-search-forward "^---\n" nil t)
        (when (re-search-forward "^---\n" nil t)
          (goto-char (match-beginning 0))
          (insert multi-line "\n")
          (when downloads-line
            (insert downloads-line "\n"))))
      (setq updated (buffer-string)))
    (unless (string= original updated)
      (with-temp-file index-path (insert updated)))))
```

- [ ] **Step 4: Run tests to verify they pass**

Expected: `7 tests passed`.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-test.el
git commit -m "feat(d.2): patch-downloads-frontmatter — inline-flow downloads + idempotent"
```

---

## Task 14: Auto-trigger from `a3-publish-deliberate` + log-buffer section

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays.el` (or wherever `a3-publish-deliberate` lives — confirm via grep)

The B.4 essays handler exposes a hook or extension point. Confirm via:

```bash
grep -n "publish-deliberate\|after-essay-publish\|essay-publish-hook" \
  ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-essays.el
```

If a `defvar` hook already exists (e.g. `a3madkour-pub-essays-after-publish-hook`), add to that. If not, this task includes adding such a hook to `a3madkour-publish-essays.el`.

- [ ] **Step 1: Write the failing tests** (in `a3madkour-publish-multi-test.el`)

```elisp
(ert-deftest a3madkour-pub-multi/auto-trigger-fires-on-opt-in ()
  "When source has #+multi_export: t, the after-publish hook dispatches orchestrate."
  (let (called)
    (cl-letf (((symbol-function 'a3madkour-pub-multi/orchestrate)
               (lambda (&rest args) (setq called args))))
      (with-temp-buffer
        (insert "#+title: T\n#+multi_export: t\n")
        (org-mode)
        (a3madkour-pub-multi--after-essay-publish-handler
         (buffer-file-name) "demo-slug" "/bundle/demo-slug/")
        (should called)))))

(ert-deftest a3madkour-pub-multi/auto-trigger-skips-without-opt-in ()
  (let (called)
    (cl-letf (((symbol-function 'a3madkour-pub-multi/orchestrate)
               (lambda (&rest args) (setq called args))))
      (with-temp-buffer
        (insert "#+title: T\n")
        (org-mode)
        (a3madkour-pub-multi--after-essay-publish-handler
         (buffer-file-name) "demo-slug" "/bundle/demo-slug/")
        (should-not called)))))
```

- [ ] **Step 2: Run tests to verify they fail**

Expected: 2 failures.

- [ ] **Step 3: Add the handler + hook install**

In `a3madkour-publish-multi.el`, before `provide`:

```elisp
(defun a3madkour-pub-multi--after-essay-publish-handler (source-file slug bundle-dir)
  "Hook target for B.4's after-essay-publish hook.
Checks SOURCE-FILE for `#+multi_export: t' and runs `orchestrate' if opted-in."
  (when (with-temp-buffer
          (insert-file-contents source-file)
          (org-mode)
          (a3madkour-pub-multi-filter--doc-p))
    (a3madkour-pub-multi/orchestrate source-file slug bundle-dir)))

(defun a3madkour-pub-multi-install ()
  "Install the auto-trigger on B.4's after-essay-publish hook (idempotent)."
  (when (boundp 'a3madkour-pub-essays-after-publish-hook)
    (add-hook 'a3madkour-pub-essays-after-publish-hook
              #'a3madkour-pub-multi--after-essay-publish-handler)))

(a3madkour-pub-multi-install)
```

If B.4 doesn't expose `a3madkour-pub-essays-after-publish-hook`, add this to `a3madkour-publish-essays.el` in the appropriate spot inside `publish-essay-file`:

```elisp
(defvar a3madkour-pub-essays-after-publish-hook nil
  "Hook run after a successful essay publish.
Args: SOURCE-FILE (org), SLUG (string), BUNDLE-DIR (path).")

;; ... at the end of publish-essay-file's happy path:
(run-hook-with-args 'a3madkour-pub-essays-after-publish-hook
                    source-file slug bundle-dir)
```

- [ ] **Step 4: Run tests to verify they pass**

Expected: `9 tests passed` in the multi suite.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-multi.el \
        emacs-configs/custom/lisp/a3madkour-publish-multi-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-essays.el
git commit -m "feat(d.2): auto-trigger on B.4 after-essay-publish hook + opt-in gate"
```

---

## Task 15: Update `a3-pub.sh` wrapper for new modules

**Files:**
- Modify: `~/dotfiles/a3-pub.sh` (path confirmed via `ls ~/dotfiles/a3-pub.sh`)

Per memory `feedback_plan_wrapper_script_updates`: every new top-level `a3madkour-publish-*.el` module needs explicit `-l <module>` in `a3-pub.sh`. Autoload only saves you for declared functions.

- [ ] **Step 1: Grep for existing `-l a3madkour-publish-*` entries**

```bash
grep -n "a3madkour-publish-" ~/dotfiles/a3-pub.sh
```

- [ ] **Step 2: Add the four new module loads**

In the same block where other modules are loaded, add (in load order):

```sh
  -l a3madkour-publish-multi-filter \
  -l a3madkour-publish-multi-pdf \
  -l a3madkour-publish-multi-word \
  -l a3madkour-publish-multi \
```

The filter loads first because the others `require` it.

- [ ] **Step 3: Smoke run**

```bash
bash -n ~/dotfiles/a3-pub.sh  # syntax check
~/dotfiles/a3-pub.sh --help 2>&1 | head -20  # verify it still launches
```

Expected: no load errors; help text prints.

- [ ] **Step 4: Commit**

```bash
cd ~/dotfiles
git add a3-pub.sh
git commit -m "chore(d.2): a3-pub.sh — load four new multi-export modules"
```

---

## Task 16: Extend `check_fixtures.py` YAML parser for 2-deep block mapping

**Files:**
- Modify: `~/Sync/Workspace/a3madkour.github.io/tools/check_fixtures.py`
- Modify: `~/Sync/Workspace/a3madkour.github.io/tools/test_check_fixtures.py`

The existing parser supports top-level keys + block sequences + inline flow mappings, but not block-style nested mappings. The orchestrator emits `downloads:` as **inline flow** (`downloads: {pdf: "x.pdf", word: "x.docx"}`) — that already round-trips through the existing parser. **No parser change is needed.**

This task verifies that claim with a focused test and adds the necessary scalar coercion if a corner case shows up.

- [ ] **Step 1: Write the failing tests**

Append to `test_check_fixtures.py` (above the `if __name__` line):

```python
class FlowMappingDownloadsTest(unittest.TestCase):
    """Inline flow `downloads:' parses to a dict the validator can introspect."""

    def test_parses_inline_flow_downloads(self):
        fm = lint.parse_frontmatter(
            '---\n'
            'title: "X"\n'
            'multi_export: true\n'
            'downloads: {pdf: "x.pdf", word: "x.docx"}\n'
            '---\nbody\n'
        )
        self.assertIsInstance(fm, dict)
        self.assertEqual(fm.get("multi_export"), True)
        self.assertEqual(fm.get("downloads"), {"pdf": "x.pdf", "word": "x.docx"})

    def test_parses_pdf_only_downloads(self):
        fm = lint.parse_frontmatter(
            '---\n'
            'title: "X"\n'
            'multi_export: true\n'
            'downloads: {pdf: "x.pdf"}\n'
            '---\nbody\n'
        )
        self.assertEqual(fm.get("downloads"), {"pdf": "x.pdf"})
```

- [ ] **Step 2: Run tests**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -20
```

Expected: tests pass on the existing parser (the inline-flow path already exists). If a corner case fails, fix `_parse_flow_mapping` or `parse_scalar` to handle it before moving on.

- [ ] **Step 3: Commit**

```bash
git add tools/test_check_fixtures.py
git commit -m "test(d.2): cover inline-flow downloads mapping in fixtures parser"
```

---

## Task 17: Add `multi_export` + `downloads` validation to `check_fixtures.py`

**Files:**
- Modify: `~/Sync/Workspace/a3madkour.github.io/tools/check_fixtures.py`
- Modify: `~/Sync/Workspace/a3madkour.github.io/tools/test_check_fixtures.py`

Validation rules per spec §6 "Linter extension":

1. `multi_export` (bool, optional). Defaults `false`.
2. `downloads` (dict, optional). Keys: subset of `{pdf, word}`. Values: strings (bundle-relative paths).
3. If `multi_export: true`, at least one of `downloads.pdf` / `downloads.word` MUST be set.
4. If `downloads.pdf` is set, `<bundle>/<value>` must exist.
5. If `downloads.word` is set, `<bundle>/<value>` must exist.

- [ ] **Step 1: Write the failing tests**

Append to `test_check_fixtures.py`:

```python
class MultiExportValidationTest(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def _fm_with(self, extra: str) -> str:
        return VALID_FRONTMATTER.replace(
            "has_video_sync: false\n",
            f"has_video_sync: false\n{extra}\n",
        )

    def test_multi_export_true_with_both_downloads_passes(self):
        body = self._fm_with(
            'multi_export: true\n'
            'downloads: {pdf: "example-essay-one.pdf", word: "example-essay-one.docx"}'
        )
        d = self.repo.root / "content" / "essays" / "example-essay-one"
        self.repo.write_essay("example-essay-one", body, hero=True)
        (d / "example-essay-one.pdf").write_bytes(b"%PDF-1.4 stub")
        (d / "example-essay-one.docx").write_bytes(b"PK stub")
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_multi_export_true_with_missing_pdf_fails(self):
        body = self._fm_with(
            'multi_export: true\n'
            'downloads: {pdf: "example-essay-one.pdf"}'
        )
        self.repo.write_essay("example-essay-one", body, hero=True)
        # Intentionally do NOT create the pdf file.
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("example-essay-one.pdf" in e for e in errors))

    def test_multi_export_true_without_downloads_fails(self):
        body = self._fm_with('multi_export: true')
        self.repo.write_essay("example-essay-one", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("downloads" in e for e in errors))

    def test_multi_export_false_passes(self):
        body = self._fm_with('multi_export: false')
        self.repo.write_essay("example-essay-one", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_unknown_downloads_key_fails(self):
        body = self._fm_with(
            'multi_export: true\n'
            'downloads: {epub: "x.epub"}'
        )
        self.repo.write_essay("example-essay-one", body, hero=True)
        self.repo.write_citations(VALID_CITATIONS)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("epub" in e for e in errors))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -25
```

Expected: 5 new failures.

- [ ] **Step 3: Add the validator logic to `check_fixtures.py`**

Inside `lint_essay`, after the existing `hero` block, append:

```python
    multi_export = fm.get("multi_export", False)
    downloads = fm.get("downloads", {}) or {}
    if not isinstance(downloads, dict):
        errors.append(f"{md_path}: downloads must be a mapping")
        downloads = {}

    if multi_export is True:
        allowed = {"pdf", "word"}
        unknown = set(downloads.keys()) - allowed
        for key in sorted(unknown):
            errors.append(f"{md_path}: downloads.{key} is not a recognized key (allowed: pdf, word)")
        if not (downloads.get("pdf") or downloads.get("word")):
            errors.append(
                f"{md_path}: multi_export: true requires at least one of downloads.pdf / downloads.word"
            )
        for key in ("pdf", "word"):
            rel = downloads.get(key)
            if rel:
                if not (essay_dir / str(rel)).exists():
                    errors.append(f"{md_path}: downloads.{key} '{rel}' not found in page bundle")
```

- [ ] **Step 4: Run tests to verify they pass**

Same command as Step 2. Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add tools/check_fixtures.py tools/test_check_fixtures.py
git commit -m "feat(d.2): essay linter — multi_export + downloads validation"
```

---

## Task 18: `essay-meta.html` — downloads cluster

**Files:**
- Modify: `~/Sync/Workspace/a3madkour.github.io/layouts/partials/essay-meta.html`

- [ ] **Step 1: Append the downloads cluster**

After the `series` block (line 18 currently), insert before the closing `</p>`:

```html
  {{ if .Params.multi_export }}
    <span class="meta-sep">·</span>
    <span class="essay-downloads" aria-label="Download other formats">
      {{ with index .Params "downloads" }}
        {{ with .pdf }}
          <a href="{{ . | relURL }}" class="download-link download-pdf" download>↓ PDF</a>
        {{ end }}
        {{ with .word }}
          <a href="{{ . | relURL }}" class="download-link download-word" download>↓ Word</a>
        {{ end }}
      {{ end }}
    </span>
  {{ end }}
```

Note: each `<a>` is conditional on its key being present — partial-success emits only the link it has. The downloads paths are bundle-relative (e.g. `example-multi.pdf`) and `relURL` resolves correctly inside the bundle context.

- [ ] **Step 2: Smoke-test the template**

The fixture won't exist yet (Tasks 20–21 create it). For now, verify the template parses by running:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
hugo --quiet 2>&1 | tail -10
```

Expected: build succeeds (no template errors); the `multi_export` gate keeps the new block invisible for all existing fixtures.

- [ ] **Step 3: Commit**

```bash
git add layouts/partials/essay-meta.html
git commit -m "feat(d.2): essay-meta — downloads cluster gated on multi_export"
```

---

## Task 19: CSS — `.essay-downloads` + `.download-link` styles

**Files:**
- Modify: `~/Sync/Workspace/a3madkour.github.io/assets/css/main.css`

- [ ] **Step 1: Locate the `.essay-meta` block**

```bash
grep -n "^.essay-meta\b\|^.meta-sep\b\|^.series-pill\b" /Users/a3madkour/Sync/Workspace/a3madkour.github.io/assets/css/main.css
```

- [ ] **Step 2: Append the new rules immediately after the existing `.series-pill` block**

```css
.essay-downloads {
  display: inline-flex;
  gap: 0.35rem;
}
.download-link {
  font-size: 0.7rem;
  padding: 1px 7px;
  background: transparent;
  color: var(--color-burgundy);
  border: 1px solid var(--color-ink-soft);
  border-radius: 99px;
  text-decoration: none;
  white-space: nowrap;
  line-height: 1.4;
}
.download-link:hover { border-color: var(--color-burgundy); }
```

Reuses existing tokens (no new palette entries). `--color-burgundy` on `--color-stone` already passes AAA in the contrast linter; no new pairings needed.

- [ ] **Step 3: Run contrast linter**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
python3 tools/check-contrast.py
```

Expected: pass.

- [ ] **Step 4: Smoke-build**

```bash
hugo --quiet && echo "build ok"
```

Expected: build ok.

- [ ] **Step 5: Commit**

```bash
git add assets/css/main.css
git commit -m "feat(d.2): .essay-downloads + .download-link styles (reuses existing tokens)"
```

---

## Task 20: End-to-end fixture — `essay-example-multi.org`

**Files:**
- Create: `~/org/notes/essay-example-multi.org` (lives in author's org-roam tree)
- Create: `~/Sync/Workspace/a3madkour.github.io/content/essays/example-multi/figures/diagram-1.svg`

The fixture exercises:

- `#+multi_export: t`
- All 5 visibility tags + stock `:noexport:`
- 4 D.1 block kinds (theorem + definition + remark + proof — enough to exercise family + own-counter + chrome-less + cross-ref)
- One `[[#thm-X][text]]` cross-ref
- One `[cite:@key]` against a known `library.bib` entry
- One `[[file:diagram-1.svg]]` SVG figure reference

Content must be obvious filler (lorem ipsum or "Example N"). Per memory `feedback_filler_text_only`.

- [ ] **Step 1: Create the org source**

Path: `~/org/notes/essay-example-multi.org`. Content:

```org
:PROPERTIES:
:ID: 11111111-2222-3333-4444-555555555555
:END:
#+title: Example essay — multi-target export
#+date: 2026-06-02
#+author: Abdelrahman Madkour
#+multi_export: t
#+filetags: :essay:
#+export_file_name: example-multi
#+hugo_section: essays
#+hugo_bundle: example-multi

Lorem ipsum dolor sit amet.

* Universal section
Lorem ipsum body.

#+attr_shortcode: :title "Example" :id thm-example
#+begin_theorem
Example one statement.
#+end_theorem

See [[#thm-example][Theorem 1]].

#+begin_definition
Example one definition.
#+end_definition

#+begin_remark
Lorem ipsum remark.
#+end_remark

#+begin_proof
Lorem ipsum proof body.
#+end_proof

[[file:diagram-1.svg]]

Cite reference: [cite:@example-source-1].

* Web only                                        :WEB_ONLY:
Lorem ipsum web-only.

* Paper only                                      :PAPER_ONLY:
Lorem ipsum paper-only.

* PDF skipped                                     :NOEXPORT_PDF:
Lorem ipsum PDF-skipped.

* Word skipped                                    :NOEXPORT_WORD:
Lorem ipsum Word-skipped.

* Universal trailer
Lorem ipsum trailer.

* Internal scratch                                :noexport:
Lorem ipsum truly internal.
```

- [ ] **Step 2: Hand-author the SVG**

Per memory `feedback_no_ai_visuals_in_mockups` (AI must not author SVG path data): the figure is a minimal hand-drawn shape using CSS-like primitives.

Create `content/essays/example-multi/figures/diagram-1.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100" width="200" height="100">
  <rect x="10" y="10" width="80" height="80" fill="none" stroke="#7A1F2B" stroke-width="2"/>
  <circle cx="140" cy="50" r="35" fill="none" stroke="#3A3A3A" stroke-width="2"/>
  <line x1="50" y1="50" x2="140" y2="50" stroke="#7A1F2B" stroke-width="1" stroke-dasharray="4 2"/>
  <text x="100" y="95" text-anchor="middle" font-family="Inter, sans-serif" font-size="9" fill="#3A3A3A">Diagram 1 (example)</text>
</svg>
```

- [ ] **Step 3: Smoke-build**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
hugo --quiet && echo "build ok"
```

Expected: build ok (essay bundle index.md doesn't exist yet, so no errors).

- [ ] **Step 4: Commit the SVG (org source lives in dotfiles/org-roam, not the site repo — that commits separately)**

```bash
git add content/essays/example-multi/figures/diagram-1.svg
git commit -m "feat(d.2): example-multi fixture — hand-authored SVG figure"
```

Then commit the org source in its own repo:

```bash
cd ~/org/notes
git add essay-example-multi.org
git commit -m "feat(d.2): example-multi org source — multi-export fixture"
```

(If `~/org/notes` is not a git repo, skip the org-source commit — it lives in user's working tree.)

---

## Task 21: End-to-end run — `M-x a3-publish-deliberate` → real bundle

**Files:**
- Created (emitted): `~/Sync/Workspace/a3madkour.github.io/content/essays/example-multi/index.md`
- Created (emitted): `~/Sync/Workspace/a3madkour.github.io/content/essays/example-multi/example-multi.pdf`
- Created (emitted): `~/Sync/Workspace/a3madkour.github.io/content/essays/example-multi/example-multi.docx`

This task is interactive — run from the author's local Emacs. The end-to-end run validates that the orchestrator wires correctly to B.4 and that all three backends produce artifacts on a realistic input.

- [ ] **Step 1: Probe tool availability**

```bash
which xelatex && which biber && which pandoc && which rsvg-convert
```

Expected: all four resolve. If `rsvg-convert` missing: `brew install librsvg`. If `xelatex`/`biber` missing: BasicTeX or full MacTeX install.

- [ ] **Step 2: Run the publish from Emacs**

In Emacs:

```
M-x a3-publish-deliberate RET ~/org/notes/essay-example-multi.org RET
```

Watch `*a3madkour-pub*` log buffer. Expected sequence:

```
multi-export — Example essay — multi-target export
slug:   example-multi
bundle: content/essays/example-multi/

  [✓] hugo   → content/essays/example-multi/index.md           (B.4)
  [✓] pdf    → content/essays/example-multi/example-multi.pdf
  [✓] word   → content/essays/example-multi/example-multi.docx
```

- [ ] **Step 3: Inspect the emitted bundle**

```bash
ls -la /Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-multi/
head -30 /Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/essays/example-multi/index.md
```

Verify `index.md` frontmatter has `multi_export: true` and `downloads: {pdf: "example-multi.pdf", word: "example-multi.docx"}`.

- [ ] **Step 4: Open the PDF and Word file**

Open both in their respective viewers (Preview, Word/LibreOffice). Verify:
- PDF shows Theorem 1: Example with `\hyperref` link to itself working as a clickable internal nav
- PDF shows definition, remark, proof body (no theorem/lemma/corollary skipped)
- Web-only and PDF-skipped sections absent from PDF
- Word shows all kinds with proper headers
- Both show `Diagram 1 (example)` figure rendered

- [ ] **Step 5: Run all site linters**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
bash tools/ci-local.sh 2>&1 | tail -30
```

Expected: all green. The new fixture exercises `multi_export` + `downloads` validation in `check_fixtures.py`.

- [ ] **Step 6: Commit the site-side artifacts**

```bash
git add content/essays/example-multi/index.md \
        content/essays/example-multi/example-multi.pdf \
        content/essays/example-multi/example-multi.docx
git commit -m "feat(d.2): example-multi bundle — end-to-end emission (index + pdf + docx)"
```

---

## Task 22: Spot-check + dev-server eyeball + push

Per memory `feedback_verify_before_merge`: offer a dev-server spot-check with a "what to eyeball" checklist before merging + pushing.

- [ ] **Step 1: Start dev server**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
hugo server --buildDrafts
```

Visit `http://localhost:1313/essays/example-multi/`.

- [ ] **Step 2: Eyeball checklist**

- [ ] Downloads cluster appears in essay meta line (after series pill area)
- [ ] `↓ PDF` link downloads `example-multi.pdf` (network tab: `download` attribute honored)
- [ ] `↓ Word` link downloads `example-multi.docx`
- [ ] Cluster invisible on **other** essays (e.g. `/essays/example-essay-one/`) — confirms `multi_export` gate
- [ ] Cluster width fits in essay meta line at half-screen 1080p (~960px) per memory `feedback_test_at_half_screen_1080p`
- [ ] Cluster width fits at mobile breakpoints (360 / 414 / 768)
- [ ] Pills don't violate the no-`→` arrow convention (`↓` is download, distinct semantics — already cleared in spec §6)
- [ ] Citation hover card still works on the multi-export essay (`[cite:@example-source-1]`)
- [ ] D.1 semantic blocks still render with their CSS §47 visual tiers (no regression on the existing path)

- [ ] **Step 3: Kill dev server, run prod build smoke**

Kill the dev server (Ctrl-C). Then:

```bash
hugo --minify && echo "prod build ok"
```

Per memory `reference_hugo_dev_server_gotcha`: never run `hugo --minify` with a dev server alive. The kill step above guards that.

Expected: prod build clean.

- [ ] **Step 4: Push to origin (after user confirms)**

User confirms the spot-check is green; only then:

```bash
git push origin master
cd ~/dotfiles && git push origin master
```

Push both repos in tandem (site + dotfiles) since the orchestrator + filter + backends + a3-pub.sh wrapper live in dotfiles.

- [ ] **Step 5: Update memory + handoff**

- Add `project_d2_complete.md` to `.claude/memory/` summarizing the slice
- Update `project_next_slice.md` to remove D.2 impl as an option (D.1 + D.2 = sub-project D shipped)
- Update `MEMORY.md` index with the new entry

---

## Self-review checklist (after writing the plan; before handoff)

- **Spec coverage:**
  - §1 Scope — 3 backends + filter + linter + fixture ✓ (Tasks 1–22 cover all)
  - §2 Authoring contract — opt-in keyword + 5 visibility tags + D.1 vocab ✓ (Tasks 1–3, 20)
  - §3 Dispatcher + orchestrator — hook registration + condition-case + frontmatter patch ✓ (Tasks 3, 12–14)
  - §4 D.1 vocab translation — LaTeX class + Lua filter + reference.docx ✓ (Tasks 3, 4, 8–11)
  - §5 Bibliography + asset coordination — F.1 reuse + SVG conversions ✓ (Tasks 6, 11, 12)
  - §6 Site integration — meta cluster + CSS + frontmatter contract + linter ✓ (Tasks 16–19)
  - §7 Module layout — 4 modules + 3 templates ✓
  - §8 Testing strategy — ert + Python + integration + lua via pandoc JSON ✓
- **No placeholders found.**
- **Type consistency:** all backend → tag-list rules match between Tasks 2 / 11 / 12. Frontmatter key names (`multi_export`, `downloads`, `pdf`, `word`) consistent across Tasks 13, 17, 18.
- **Memory-flagged gotchas covered:**
  - `feedback_plan_wrapper_script_updates` → Task 15 explicit
  - `feedback_verify_before_merge` → Task 22 dev-server checklist
  - `feedback_filler_text_only` → Task 20 explicit
  - `feedback_test_at_half_screen_1080p` → Task 22 step 2
  - `reference_hugo_dev_server_gotcha` → Task 22 step 3
  - `reference_finish_publish_snapshot_lifecycle` → orchestrator runs AFTER B.4 finish-publish; the frontmatter patch reads index.md from disk (Task 13), not from snapshot state — already correct
  - `reference_bbt_brace_protection` → no new bib parsing in D.2; F's existing path applies

---

**Plan complete and saved to `docs/superpowers/plans/2026-06-02-phase-3-d2-multi-target-export.md`.**
