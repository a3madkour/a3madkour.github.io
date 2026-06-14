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

> **Note (2026-06-13 amend):** the shipped module is now async — `compile-tex-async`, `convert-svgs-fan`, `multi-pdf/run` with `&key on-done`. The patch below targets that architecture. It also drops the load-time `with-eval-after-load 'ox-latex` registration (current lines 17–30) in favor of per-call `let`-binding inside `multi-pdf/run`.

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

### New defcustom + shared heading constant

```elisp
(defcustom a3madkour-pub-multi-bibtex-command "bibtex"
  "External `bibtex' command — used for non-biblatex classes (AAAI / ACM / IEEE)."
  :type 'string :group 'a3madkour-pub-multi)

(defconst a3madkour-pub-multi-pdf--default-class "madkour-paper"
  "Fallback class name when `#+LATEX_CLASS:' is absent.")

(defconst a3madkour-pub-multi-pdf--heading-format
  '(("\\section{%s}" . "\\section*{%s}")
    ("\\subsection{%s}" . "\\subsection*{%s}")
    ("\\subsubsection{%s}" . "\\subsubsection*{%s}")
    ("\\paragraph{%s}" . "\\paragraph*{%s}")
    ("\\subparagraph{%s}" . "\\subparagraph*{%s}"))
  "Section heading templates shared by every D.2 class entry.")

(defun a3madkour-pub-multi-pdf--build-class-entry (class-name preamble)
  "Build an `org-latex-classes' entry from CLASS-NAME + PREAMBLE."
  (cons class-name
        (cons (concat preamble "\n[NO-DEFAULT-PACKAGES]\n[PACKAGES]\n[EXTRA]")
              a3madkour-pub-multi-pdf--heading-format)))
```

### Drop the load-time `with-eval-after-load 'ox-latex` form

Delete the entire block at lines 17–30 of the current module (the one that calls `setf (alist-get "madkour-paper" org-latex-classes ...)`). Per-call let-binding inside `multi-pdf/run` replaces it.

### Update `--probe-tools` to also probe bibtex

```elisp
(defun a3madkour-pub-multi-pdf--probe-tools ()
  "Return list of missing required commands, or nil if all present."
  (let (missing)
    (dolist (cmd (list a3madkour-pub-multi-xelatex-command
                       a3madkour-pub-multi-biber-command
                       a3madkour-pub-multi-bibtex-command
                       a3madkour-pub-multi-rsvg-convert-command))
      (unless (executable-find cmd)
        (push cmd missing)))
    (nreverse missing)))
```

### Engine-aware async compile chain

Replace the `seq` list in `--compile-tex-async` to dispatch on engine. New signature: `&key engine on-done step-cb` (engine defaults to `'biber` for back-compat with the existing test).

```elisp
(cl-defun a3madkour-pub-multi-pdf--compile-tex-async (tex-path &key engine on-done step-cb)
  "Async version of compile-tex.  Chains xelatex → ENGINE → xelatex → xelatex.
ENGINE is `biber' (default) or `bibtex'."
  (let* ((dir (file-name-directory tex-path))
         (base (file-name-base tex-path))
         (pdf-path (expand-file-name (concat base ".pdf") dir))
         (engine (or engine 'biber))
         (bib-command (pcase engine
                        ('biber  a3madkour-pub-multi-biber-command)
                        ('bibtex a3madkour-pub-multi-bibtex-command)
                        (other (error "D.2: unknown bib engine %S" other))))
         (seq (list (cons a3madkour-pub-multi-xelatex-command "pass 1/4")
                    (cons bib-command (format "%s" engine))
                    (cons a3madkour-pub-multi-xelatex-command "pass 3/4")
                    (cons a3madkour-pub-multi-xelatex-command "pass 4/4"))))
    (cl-labels
        ((run-next (remaining)
           (if (null remaining)
               (when on-done (funcall on-done (file-exists-p pdf-path)))
             (let* ((cmd-and-label (car remaining))
                    (cmd (car cmd-and-label))
                    (label (cdr cmd-and-label))
                    (bib-cmd-p (or (string= cmd a3madkour-pub-multi-biber-command)
                                   (string= cmd a3madkour-pub-multi-bibtex-command)))
                    (arg (if bib-cmd-p base (concat base ".tex")))
                    ;; bibtex chokes on -interaction=nonstopmode; only pass it to xelatex.
                    (args (if bib-cmd-p (list arg)
                            (list "-interaction=nonstopmode" arg))))
               (a3-pub-async/run-process
                cmd args
                :name (format "pdf-%s" label)
                :cwd dir
                :on-done
                (lambda (rc _tail)
                  (when step-cb (funcall step-cb label rc))
                  (run-next (cdr remaining))))))))
      (run-next seq))))
```

### Refactor `multi-pdf/run` for pluggable class

```elisp
(cl-defun a3madkour-pub-multi-pdf/run (source-file slug bundle-dir templates-dir
                                       &key run on-done)
  "Async PDF backend.  Resolves #+LATEX_CLASS: against TEMPLATES-DIR (per-class
subdir convention — preamble.tex + class assets).  Defaults to `madkour-paper'
when the keyword is absent."
  (let* ((class-name (or (a3madkour-pub-multi-pdf--read-latex-class source-file)
                         a3madkour-pub-multi-pdf--default-class))
         (resolved (a3madkour-pub-multi-pdf--resolve-class class-name templates-dir))
         (preamble (car resolved))
         (class-dir (cdr resolved))
         (engine (a3madkour-pub-multi-pdf--bib-engine preamble))
         (work-dir (expand-file-name (format "multi-export-%s/" slug)
                                     temporary-file-directory))
         (fig-dir (expand-file-name "figures/" work-dir))
         (tex-path (expand-file-name (concat slug ".tex") work-dir))
         (svgs (a3madkour-pub-multi-pdf--list-svg-figures source-file))
         (svg-pairs (mapcar (lambda (svg)
                              (list svg (expand-file-name
                                         (concat (file-name-base svg) ".pdf")
                                         fig-dir)))
                            svgs)))
    (make-directory fig-dir t)
    (a3madkour-pub-multi-pdf--copy-class-assets class-dir work-dir)
    (when run (push work-dir (a3-pub-async-run-tmp-dirs run)))
    ;; Phase 1: ox-latex export, with per-call class registration.
    (let ((start (current-time))
          (class-entry (a3madkour-pub-multi-pdf--build-class-entry class-name preamble)))
      (with-current-buffer (find-file-noselect source-file)
        (let ((org-latex-with-hyperref t)
              (org-latex-classes (cons class-entry org-latex-classes))
              (org-latex-default-class class-name)
              (org-export-show-temporary-export-buffer nil))
          (org-latex-export-to-latex)))
      (when run
        (a3-pub-async/log-step run "export" :ok
                               :detail (format "org → latex (class=%s, engine=%s)"
                                               class-name engine)
                               :elapsed (float-time
                                         (time-subtract (current-time) start)))))
    ;; Move produced .tex into work dir.
    (let ((source-tex (expand-file-name (concat slug ".tex")
                                        (file-name-directory source-file))))
      (when (file-exists-p source-tex)
        (rename-file source-tex tex-path t)))
    ;; Phase 2: SVG fan → xelatex chain → place.
    (a3madkour-pub-multi-pdf--convert-svgs-fan
     svg-pairs
     :on-done
     (lambda (_svg-rcs)
       (when run
         (a3-pub-async/log-step run "svgs" :ok
                                :detail (format "%d files" (length svg-pairs))))
       (a3madkour-pub-multi-pdf--compile-tex-async
        tex-path
        :engine engine
        :step-cb
        (lambda (label rc)
          (when run
            (a3-pub-async/log-step run "xelatex" (if (zerop rc) :ok :err)
                                   :detail label)))
        :on-done
        (lambda (ok)
          (if (not ok)
              (when on-done
                (funcall on-done '(:status err :err-snippet "PDF not produced")))
            (let ((built (expand-file-name (concat slug ".pdf") work-dir))
                  (target (expand-file-name (concat slug ".pdf") bundle-dir)))
              (if (file-exists-p built)
                  (progn
                    (rename-file built target t)
                    (when run
                      (a3-pub-async/log-step run "pdf" :ok :detail target))
                    (when on-done
                      (funcall on-done (list :status 'ok :path target))))
                (when on-done
                  (funcall on-done '(:status err :err-snippet "built PDF missing"))))))))))))
```

---

## ert test list (add to `a3madkour-publish-multi-pdf-test.el`)

Use the existing `with-a3-pub-async-sync` wrapper + `cl-letf` stubs (see the existing `compile-chain-runs-four-passes` test for the pattern).

1. `resolve-class-returns-preamble-and-dir` — happy path, tmp fixture dir with `preamble.tex` whose body is `"\\documentclass{foo}\n"`. Assert car returned matches body, cdr is the dir.
2. `resolve-class-errors-on-missing-subdir` — `should-error` on nonexistent class.
3. `resolve-class-errors-on-missing-preamble` — tmp empty subdir, `should-error`.
4. `read-latex-class-extracts-keyword` — tmp org file with `#+LATEX_CLASS: aaai24` → `"aaai24"`.
5. `read-latex-class-returns-nil-when-absent`.
6. `read-latex-class-case-insensitive` — `#+latex_class:`, `#+LATEX_CLASS:` both resolve. (Regex uses `case-fold-search`, which is t by default in `re-search-forward`.)
7. `bib-engine-detects-biber-for-biblatex` — `"\\usepackage{biblatex}"` → `'biber`.
8. `bib-engine-detects-biber-with-options` — `"\\usepackage[backend=biber]{biblatex}"` → `'biber`.
9. `bib-engine-falls-back-to-bibtex` — `"\\usepackage{natbib}"` → `'bibtex`.
10. `copy-class-assets-skips-preamble-tex` — tmp dir with `preamble.tex` + `aaai24.sty`; only `aaai24.sty` lands in work-dir.
11. `copy-class-assets-skips-dotfiles` — `.DS_Store` not copied (directory-files regex `\\`[^.]` already filters).
12. `compile-chain-routes-bibtex-engine` — stub `call-process` capturing cmd names; pass `:engine 'bibtex`; assert index-1 cmd equals `a3madkour-pub-multi-bibtex-command`.
13. `compile-chain-routes-biber-engine-by-default` — no `:engine` arg; assert index-1 cmd equals `a3madkour-pub-multi-biber-command`.
14. `run-defaults-to-madkour-paper-when-keyword-absent` — patch `--read-latex-class` to return nil; spy on `--resolve-class`; assert called with `"madkour-paper"`.

Also update the existing `compile-chain-runs-four-passes` test: it now needs to pass `:engine 'biber` explicitly or rely on the default. The default keeps it green without changes.

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
