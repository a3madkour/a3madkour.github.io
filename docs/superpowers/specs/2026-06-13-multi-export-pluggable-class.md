# D.2 pluggable LaTeX class — site convention + dotfiles patch

**Date:** 2026-06-13
**Scope:** Make D.2 multi-export's PDF backend honor `#+LATEX_CLASS:` per-essay instead of hardcoding `madkour-paper`. Unblocks shipping conference papers (AAAI 2024 dropped as the first concrete case).
**Status:** Site-side landed; dotfiles patch staged here for a separate `~/dotfiles` session.

---

## Site-side changes (this repo)

Already committed:

```
tools/templates/
  <class-name>/
    preamble.tex         # documentclass + usepackages — second element of org-latex-classes entry
    <class-assets>       # .cls / .sty / .bst / logos — copied into the work dir verbatim
  reference.docx         # pandoc word ref — flat, not per-class
  d2-blocks.lua          # pandoc filter — flat
```

`madkour-paper.cls` migrated into `tools/templates/madkour-paper/`. A back-compat symlink at `tools/templates/madkour-paper.cls` → `madkour-paper/madkour-paper.cls` keeps the current orchestrator working until the dotfiles patch lands; delete it in the same commit that ships the patch.

AAAI 2024 (anonymous-submission variant) installed at `tools/templates/aaai24/` (`aaai24.sty` + `aaai24.bst` + `preamble.tex`).

CLAUDE.md "Multi-target export templates" section documents the contract.

---

## Dotfiles patch (`~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-multi-pdf.el`)

### New helpers

```elisp
(defun a3madkour-pub-multi-pdf--read-latex-class (source-file)
  "Return value of #+LATEX_CLASS in SOURCE-FILE, or nil when absent."
  (with-temp-buffer
    (insert-file-contents source-file)
    (goto-char (point-min))
    (when (re-search-forward "^#\\+latex_class:[ \t]+\\(\\S-+\\)" nil t)
      (match-string-no-properties 1))))

(defun a3madkour-pub-multi-pdf--resolve-class (class-name templates-dir)
  "Return (PREAMBLE . CLASS-DIR) for CLASS-NAME under TEMPLATES-DIR.
Errors when the subdir or preamble.tex is missing."
  (let* ((class-dir (file-name-as-directory
                     (expand-file-name class-name templates-dir)))
         (preamble-file (expand-file-name "preamble.tex" class-dir)))
    (unless (file-directory-p class-dir)
      (error "D.2: LaTeX class %S has no template subdir at %s"
             class-name class-dir))
    (unless (file-readable-p preamble-file)
      (error "D.2: LaTeX class %S missing preamble.tex at %s"
             class-name preamble-file))
    (cons (with-temp-buffer
            (insert-file-contents preamble-file)
            (buffer-string))
          class-dir)))

(defun a3madkour-pub-multi-pdf--copy-class-assets (class-dir work-dir)
  "Copy every regular file in CLASS-DIR — except preamble.tex — into WORK-DIR."
  (dolist (f (directory-files class-dir t "\\`[^.]"))
    (when (and (file-regular-p f)
               (not (string= "preamble.tex" (file-name-nondirectory f))))
      (copy-file f (expand-file-name (file-name-nondirectory f) work-dir) t))))

(defun a3madkour-pub-multi-pdf--bib-engine (preamble)
  "Return \\='biber if PREAMBLE uses biblatex, else \\='bibtex.
AAAI/ACM-style templates load natbib + bibtex; ours loads biblatex + biber."
  (if (string-match-p "\\\\usepackage\\(\\[[^]]*\\]\\)?{biblatex}" preamble)
      'biber
    'bibtex))
```

### Replace the hardcoded class entry in `multi-pdf/run`

Current shape (per plan §742–769): `copy-file madkour-paper.cls`, hardcoded `org-latex-classes` registration of `madkour-paper`, hardcoded `org-latex-default-class`.

New shape:

```elisp
(defun a3madkour-pub-multi-pdf/run (source-file slug bundle-dir templates-dir)
  "Run the PDF backend for SOURCE-FILE / SLUG → BUNDLE-DIR/SLUG.pdf.
TEMPLATES-DIR is the path to `tools/templates/'; per-class subdirs hold
preamble.tex + the conference assets. Returns the absolute path of the
placed PDF on success, nil on failure."
  (let* ((class-name (or (a3madkour-pub-multi-pdf--read-latex-class source-file)
                         "madkour-paper"))
         (resolved (a3madkour-pub-multi-pdf--resolve-class class-name templates-dir))
         (preamble (car resolved))
         (class-dir (cdr resolved))
         (engine (a3madkour-pub-multi-pdf--bib-engine preamble))
         (work-dir (expand-file-name (format "multi-export-%s/" slug)
                                     temporary-file-directory))
         (fig-dir (expand-file-name "figures/" work-dir))
         (tex-path (expand-file-name (concat slug ".tex") work-dir)))
    (make-directory fig-dir t)
    (a3madkour-pub-multi-pdf--copy-class-assets class-dir work-dir)
    (dolist (svg (a3madkour-pub-multi-pdf--list-svg-figures source-file))
      (a3madkour-pub-multi-pdf--convert-svg
       svg (expand-file-name (concat (file-name-base svg) ".pdf") fig-dir)))
    (let* ((class-entry (list class-name
                              preamble
                              '("\\section{%s}" . "\\section*{%s}")
                              '("\\subsection{%s}" . "\\subsection*{%s}")
                              '("\\subsubsection{%s}" . "\\subsubsection*{%s}")
                              '("\\paragraph{%s}" . "\\paragraph*{%s}")
                              '("\\subparagraph{%s}" . "\\subparagraph*{%s}")))
           (org-latex-classes (cons class-entry org-latex-classes))
           (org-latex-default-class class-name)
           (org-latex-with-hyperref t))
      (with-current-buffer (find-file-noselect source-file)
        (org-latex-export-to-latex)))
    (let ((source-tex (expand-file-name (concat slug ".tex")
                                        (file-name-directory source-file))))
      (when (file-exists-p source-tex)
        (rename-file source-tex tex-path t)))
    (when (a3madkour-pub-multi-pdf--compile-tex tex-path engine)
      (let ((built-pdf (expand-file-name (concat slug ".pdf") work-dir))
            (target (expand-file-name (concat slug ".pdf") bundle-dir)))
        (when (file-exists-p built-pdf)
          (rename-file built-pdf target t)
          target)))))
```

### Engine-aware compile loop

```elisp
(defun a3madkour-pub-multi-pdf--compile-tex (tex-path engine)
  "Run xelatex → ENGINE → xelatex → xelatex on TEX-PATH in its own directory.
ENGINE is \\='biber or \\='bibtex. Returns t on full success, nil on non-zero exit."
  (let* ((dir (file-name-directory tex-path))
         (base (file-name-base tex-path))
         (default-directory dir)
         (bib-command (pcase engine
                        ('biber  a3madkour-pub-multi-biber-command)
                        ('bibtex a3madkour-pub-multi-bibtex-command)
                        (other (error "D.2: unknown bib engine %S" other))))
         (seq (list a3madkour-pub-multi-xelatex-command
                    bib-command
                    a3madkour-pub-multi-xelatex-command
                    a3madkour-pub-multi-xelatex-command)))
    (cl-loop for cmd in seq
             for arg = (cond
                        ((string= cmd a3madkour-pub-multi-biber-command) base)
                        ((string= cmd a3madkour-pub-multi-bibtex-command) base)
                        (t (concat base ".tex")))
             for rc = (call-process cmd nil nil nil "-interaction=nonstopmode" arg)
             unless (zerop rc) return nil
             finally return t)))

(defcustom a3madkour-pub-multi-bibtex-command "bibtex"
  "Bibtex binary used for non-biblatex classes (AAAI / ACM / IEEE style)."
  :type 'string
  :group 'a3madkour-pub-multi)
```

Note: `bibtex` does not take `-interaction=nonstopmode` — it ignores unknown flags but emits a warning. If that warning annoys, split the `call-process` arg list per command. The simple form keeps the loop uniform.

### Drop the existing class registration

The post-ship bug-fix #1 commit (`90ad9e9`) added an `org-latex-classes` registration of `madkour-paper` at module load time. Remove it — the new `multi-pdf/run` registers per-call inside the let-binding.

---

## ert test list (add to `a3madkour-publish-multi-pdf-test.el`)

1. `resolve-class-returns-preamble-and-dir` — happy path, fixture dir with `preamble.tex`.
2. `resolve-class-errors-on-missing-subdir` — should-error.
3. `resolve-class-errors-on-missing-preamble` — empty subdir, should-error.
4. `read-latex-class-extracts-keyword` — org buffer with `#+LATEX_CLASS: aaai24` → "aaai24".
5. `read-latex-class-returns-nil-when-absent`.
6. `read-latex-class-case-insensitive` — `#+latex_class:`, `#+LaTeX_Class:` both resolve.
7. `bib-engine-detects-biber-for-biblatex`.
8. `bib-engine-detects-biber-with-options` — `\usepackage[backend=biber]{biblatex}`.
9. `bib-engine-falls-back-to-bibtex` — natbib preamble.
10. `copy-class-assets-skips-preamble-tex` — directory with `preamble.tex` + `aaai24.sty` → only `aaai24.sty` lands in work-dir.
11. `copy-class-assets-skips-dotfiles` — `.DS_Store` not copied.
12. `compile-tex-routes-bibtex-engine` — stub `call-process`, assert `a3madkour-pub-multi-bibtex-command` invoked at index 1.
13. `compile-tex-routes-biber-engine` — stub `call-process`, assert biber at index 1.
14. `run-defaults-to-madkour-paper-when-keyword-absent` — fixture with no `#+LATEX_CLASS:`, assert resolve called with "madkour-paper".

Suite delta: +14 tests. Run from `~/dotfiles`:

```bash
emacs -Q --batch \
  -L emacs-configs/custom/lisp \
  -l a3madkour-publish-multi-pdf-test.el \
  -f ert-run-tests-batch-and-exit
```

---

## Sample org usage

```org
#+TITLE: A worked example
#+AUTHOR: Anonymous Submission
#+LATEX_CLASS: aaai24
#+MULTI_EXPORT: t
#+LATEX_HEADER: \affiliations{Northeastern University}
```

For the camera-ready variant once AAAI accepts: clone `tools/templates/aaai24/` → `tools/templates/aaai24-cameraready/`, drop the `submission` option on `\usepackage[submission]{aaai24}`, and bump `#+LATEX_CLASS:` to `aaai24-cameraready`. Authors / affiliations stay in `#+LATEX_HEADER:` lines.

---

## Out of scope (filed for later if needed)

- Per-class section heading templates. Currently universal `\section{%s}` / `\subsection{%s}` / etc. — works for AAAI, ACM article-based, IEEE article-based. If a class uses non-standard sectioning (LNCS sometimes), add a `headings.el` sidecar in the class subdir and load it from `resolve-class`.
- Pandoc Word side: `reference.docx` is flat — one Word ref doc for every essay. Adequate for the personal-site case; revisit if a conference Word template is needed.
- `bibtex` warning noise from the shared `-interaction=nonstopmode` arg. Cosmetic.
- Validation linter: a `tools/check_d2_templates.py` that asserts every subdir under `tools/templates/` has a `preamble.tex`. Cheap, skip until churn warrants.
