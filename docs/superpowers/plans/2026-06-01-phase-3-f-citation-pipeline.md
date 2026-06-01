# Phase 3 F — citation pipeline implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the org-side citation pipeline — pre-export `[cite:@key]` rewrite, `.bib` resolution (citar in emacs, parser fallback in shell, BBT JSON-RPC sync), per-publish merge into `data/citations.yaml`, fail-fast on missing keys, `notes_ref` auto-detect, plus `M-x a3-sync-citations` for full rebuild + Zotero refresh.

**Architecture:** Two new elisp modules. `a3madkour-publish-bib.el` owns `.bib` parsing + citar adapter + BBT JSON-RPC behind a single `bib-resolve` interface. `a3madkour-publish-citations.el` owns the buffer rewriter, accumulator, yaml emitter, and `a3-sync-citations` command. F plugs into the existing per-handler chokepoint `rewrite-to-tmp-file` — every page-bundle handler (garden / essays / research) gets cite rewriting for free. Library handler is unaffected (doesn't use `rewrite-to-tmp-file`; library rows don't carry cites).

**Tech Stack:** Emacs Lisp (ert tests), citar/org-cite, Python 3 stdlib (integration + linter tests via `unittest`), `url-retrieve-synchronously` for BBT JSON-RPC.

**Spec:** `docs/superpowers/specs/2026-06-01-phase-3-f-citation-pipeline-design.md`

**Working directories:**
- Dotfiles: `/Users/a3madkour/dotfiles/`
- Site: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`
- Author bib: `/Users/a3madkour/org/notes/ref-notes/library.bib` (already exists; 15.6k entries)

**Test commands (used throughout):**
- ert: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -20`
- integration: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration -v 2>&1 | tail -30`
- python linter: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_check_citations -v 2>&1 | tail -10`

**Baseline counts before F:** 398 ert + 33 integration (per [[b4-complete]]). Target after F: ~483 ert + ~36 integration.

---

## Task 1 — Loosen `check_citations.py` key regex

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/check_citations.py:34` (`KEY_RE`)
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_check_citations.py` (append 3 tests)

- [ ] **Step 1: Write 3 failing tests**

Append to `tools/test_check_citations.py` (before any `if __name__ == "__main__":` block; if none exists, just append):

```python
class TestKeyRegexLoosenedForBBT(unittest.TestCase):
    """F Task 1: KEY_RE must accept BBT-style camelCase keys like
    abelaConstructiveApproachGeneration2015 while still rejecting underscores
    and leading hyphens."""

    def _write_yaml(self, key: str) -> Path:
        d = Path(tempfile.mkdtemp())
        (d / "data").mkdir()
        (d / "content" / "garden").mkdir(parents=True)
        path = d / "data" / "citations.yaml"
        path.write_text(
            "citations:\n"
            f"  {key}:\n"
            '    authors: ["Lastname, F."]\n'
            "    year: 2020\n"
            '    title: "T"\n'
            '    venue: "V"\n'
        )
        return path

    def test_camel_case_bbt_key_accepted(self) -> None:
        from check_citations import lint_citations
        p = self._write_yaml("abelaConstructiveApproachGeneration2015")
        errors = lint_citations(p, p.parent.parent / "content" / "garden")
        self.assertEqual(errors, [], f"camelCase key wrongly rejected: {errors}")

    def test_underscore_key_rejected(self) -> None:
        from check_citations import lint_citations
        p = self._write_yaml("bad_underscore_key")
        errors = lint_citations(p, p.parent.parent / "content" / "garden")
        self.assertTrue(any("must match" in e for e in errors),
                        f"underscore key wrongly accepted: {errors}")

    def test_leading_hyphen_key_rejected(self) -> None:
        from check_citations import lint_citations
        p = self._write_yaml("-leading-hyphen")
        errors = lint_citations(p, p.parent.parent / "content" / "garden")
        self.assertTrue(any("must match" in e for e in errors),
                        f"leading-hyphen key wrongly accepted: {errors}")
```

If the file lacks `import tempfile` / `from pathlib import Path` / `import unittest`, add them at the top.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_check_citations.TestKeyRegexLoosenedForBBT -v 2>&1 | tail -10`
Expected: `test_camel_case_bbt_key_accepted` FAILs (current regex rejects uppercase); other two PASS.

- [ ] **Step 3: Loosen `KEY_RE`**

Edit `tools/check_citations.py` line 34:

```python
KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")
```

(Was: `re.compile(r"^[a-z0-9][a-z0-9-]*$")`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_check_citations -v 2>&1 | tail -10`
Expected: all `TestKeyRegexLoosenedForBBT` tests PASS; pre-existing tests stay green.

- [ ] **Step 5: Verify the full linter still passes on the existing yaml**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_citations.py`
Expected: `OK — citations.yaml validates.`

- [ ] **Step 6: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/check_citations.py tools/test_check_citations.py
git commit -m "$(cat <<'EOF'
feat(f): loosen check_citations KEY_RE to accept BBT camelCase (Task 1)

Real Zotero+BBT cite keys are camelCase
(e.g. abelaConstructiveApproachGeneration2015).  Loosens
^[a-z0-9][a-z0-9-]*$ to ^[A-Za-z0-9][A-Za-z0-9-]*$.  Underscores
and leading hyphens still rejected; existing fixture keys
(example-source-N) still pass.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2 — Stub `library.bib` fixture

**Files:**
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/fixtures/citations/library.bib` (new dir)

- [ ] **Step 1: Create the fixture directory + file**

Run: `mkdir -p /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/fixtures/citations`

Then write `tools/fixtures/citations/library.bib`:

```bibtex
% Fixture .bib for F sub-project (citation pipeline).
% 8 entries covering all @types F maps; hand-written, NOT Zotero-derived.
% Exercises: brace-protected titles, multi-author splits, missing-author
% fallback, every venue-chain branch (journaltitle/booktitle/publisher/eventtitle).

@article{loremIpsumDolorSit2020,
  title = {Lorem {{Ipsum}} Dolor Sit Amet},
  author = {Lastname, First and Other, Second},
  journaltitle = {Journal of Examples},
  date = {2020-06-15},
  volume = {42},
  issue = {3},
  pages = {1--12},
  doi = {10.1000/example.001},
  url = {https://example.invalid/article-1}
}

@book{consecteturAdipiscingElit2018,
  title = {Consectetur Adipiscing Elit},
  author = {Author, One and Author, Two and Author, Three},
  publisher = {Example Press},
  date = {2018},
  isbn = {978-0-00-000000-2}
}

@inproceedings{utLaboreEtDolore2022,
  title = {Ut {{Labore}} et Dolore Magna},
  author = {Solo, A.},
  booktitle = {Proceedings of the Example Conference},
  eventtitle = {Example Conf},
  date = {2022-09-01}
}

@incollection{magnaAliquaEnimAd2015,
  title = {Magna Aliqua Enim Ad},
  author = {Editor-In-Chief, M. and Co, J.},
  booktitle = {Handbook of Examples},
  publisher = {Example Academic},
  date = {2015}
}

@online{minimVeniamQuisNostrud2024,
  title = {Minim Veniam Quis Nostrud Exercitation},
  url = {https://example.invalid/online-1},
  urldate = {2024-01-05},
  date = {2024-01-01}
}

@misc{exerciseUllamcoLaboris2019,
  title = {Exercise Ullamco Laboris Nisi},
  author = {Workshop, ACM},
  publisher = {Example Workshop},
  date = {2019}
}

@report{aliquipExCommodoConsequat2021,
  title = {Aliquip Ex Commodo Consequat},
  author = {Org, Research},
  publisher = {Example Lab},
  date = {2021}
}

@thesis{duisAuteIrureDolor2017,
  title = {Duis Aute Irure Dolor},
  author = {Candidate, P. H.},
  publisher = {Example University},
  date = {2017}
}

@online{noAuthorOnlineExample2023,
  title = {Anonymous Example Without An Author},
  url = {https://example.invalid/no-author},
  date = {2023}
}
```

(9 entries total — extra `@online` exercises the empty-author fallback. Task description says "8" — we ship 9 because the no-author edge case is worth dedicated fixture coverage.)

- [ ] **Step 2: Sanity-check the file**

Run: `wc -l /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/fixtures/citations/library.bib`
Expected: ~70 lines.

Run: `grep -c "^@" /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/fixtures/citations/library.bib`
Expected: `9`.

- [ ] **Step 3: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/fixtures/citations/library.bib
git commit -m "$(cat <<'EOF'
feat(f): stub library.bib fixture (Task 2)

9 hand-written BBT-keyed entries covering @article/@book/
@inproceedings/@incollection/@online/@misc/@report/@thesis plus a
no-author @online for empty-author fallback testing.  Lives at
tools/fixtures/citations/library.bib; loaded by F's ert + integration
tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3 — `.bib` parser: entry recognition + simple fields

**Files:**
- Create: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el`
- Create: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el`

- [ ] **Step 1: Write the module skeleton**

Create `a3madkour-publish-bib.el`:

```elisp
;;; a3madkour-publish-bib.el --- bib resolver for F citation pipeline -*- lexical-binding: t; -*-

;;; Commentary:

;; F sub-project resolver module.  Reads BibTeX entries via three
;; engines hidden behind one interface:
;;
;;   (a3madkour-pub-bib/resolve KEY)  → entry plist or nil
;;     ├─ citar path     (preferred when citar is loaded; M-x context)
;;     ├─ parser path    (stdlib .bib parser; batch / shell context)
;;     └─ BBT JSON-RPC   (NEVER called from resolve; only from
;;                        `bib-refresh-from-zotero', invoked by
;;                        `a3-sync-citations')
;;
;; Plist shape returned by resolve:
;;   (:authors ("Last, F" ...) :year INT :title STR :venue STR
;;    :url STR-or-nil :doi STR-or-nil :publisher STR-or-nil
;;    :volume STR-or-nil :issue STR-or-nil :pages STR-or-nil
;;    :isbn STR-or-nil :type STR-or-nil)
;;
;; The parser produces a raw per-entry alist; `normalize-entry' is the
;; lossy projection from raw → schema plist.

;;; Code:

(require 'cl-lib)
(require 'subr-x)

(defcustom a3madkour-pub-bib/library-path
  (expand-file-name "~/org/notes/ref-notes/library.bib")
  "Path to the BibTeX library used by F.  Default is the author's
Zotero/BBT-exported file."
  :type 'file
  :group 'a3madkour-pub)

(defcustom a3madkour-pub-bib/bbt-endpoint
  "http://localhost:23119/better-bibtex/json-rpc"
  "Better-BibTeX JSON-RPC endpoint.  Set to nil to disable
`bib-refresh-from-zotero' entirely."
  :type '(choice (const :tag "Disabled" nil) string)
  :group 'a3madkour-pub)

(defvar a3madkour-pub-bib--parser-cache nil
  "Hash table mapping cite-key (string) to raw-field-alist for the
current publish run.  Reset by `a3madkour-pub-bib/parser-init'.")

;; ---------------------------------------------------------------------
;; Parser: entry recognition + simple field reading
;; ---------------------------------------------------------------------

(defun a3madkour-pub-bib--parser-init ()
  "Allocate a fresh empty parser cache hash."
  (setq a3madkour-pub-bib--parser-cache
        (make-hash-table :test 'equal :size 256)))

(defun a3madkour-pub-bib--strip-outer-braces (s)
  "Strip exactly one pair of OUTERMOST braces from S if present.
Inner braces survive verbatim."
  (let ((trimmed (string-trim s)))
    (if (and (string-prefix-p "{" trimmed)
             (string-suffix-p "}" trimmed)
             (>= (length trimmed) 2))
        (substring trimmed 1 -1)
      trimmed)))

(defun a3madkour-pub-bib--read-balanced-braces ()
  "Reader: at point just AFTER an opening `{', read forward until the
matching `}', honoring nested braces.  Returns the inside-braces string
WITHOUT the closing brace.  Point is left just AFTER the matching brace."
  (let ((start (point))
        (depth 1))
    (while (and (> depth 0) (not (eobp)))
      (let ((next (re-search-forward "[{}]" nil t)))
        (cond
         ((not next) (error "a3-pub-bib: unbalanced braces (parse start %d)" start))
         ((eq (char-before) ?{) (setq depth (1+ depth)))
         ((eq (char-before) ?}) (setq depth (1- depth))))))
    (when (> depth 0)
      (error "a3-pub-bib: unbalanced braces (parse start %d)" start))
    ;; (point) is just AFTER the closing brace; the inside spans (start..(point)-1).
    (buffer-substring-no-properties start (1- (point)))))

(defun a3madkour-pub-bib--read-quoted-value ()
  "Reader: at point just AFTER an opening `\"', read forward until the
closing `\"' (no escapes — BibTeX doesn't have them inside double-quotes
for our V1 corpus).  Returns the inside string; point is just AFTER the
closing quote."
  (let ((start (point)))
    (unless (re-search-forward "\"" nil t)
      (error "a3-pub-bib: unterminated quoted value at pos %d" start))
    (buffer-substring-no-properties start (1- (point)))))

(defun a3madkour-pub-bib--parse-field-value ()
  "Reader: at point at the first non-whitespace char of a field value,
read one value form: `{...}', `\"...\"', or a bare numeric token like
`2018'.  Returns the value string."
  (skip-chars-forward " \t\n\r")
  (cond
   ((eq (char-after) ?{)  (forward-char 1) (a3madkour-pub-bib--read-balanced-braces))
   ((eq (char-after) ?\") (forward-char 1) (a3madkour-pub-bib--read-quoted-value))
   ((looking-at "\\([0-9]+\\)")
    (goto-char (match-end 0))
    (match-string-no-properties 1))
   (t (error "a3-pub-bib: unexpected field-value start at pos %d" (point)))))

(defun a3madkour-pub-bib--parse-one-entry ()
  "Reader: at point at the `@' of an entry, parse one `@type{key, ...}'.
Returns (KEY . ALIST-OF-FIELDS).  KEY is the entry key (string).  ALIST
keys are interned symbols of lowercased field names.  Special pseudo-key
:bibtype carries the entry type string (without `@')."
  (unless (looking-at "@\\([A-Za-z]+\\)[ \t]*{[ \t]*\\([^ \t,\n]+\\)[ \t]*,")
    (error "a3-pub-bib: not at entry start at pos %d" (point)))
  (let ((entry-type (downcase (match-string-no-properties 1)))
        (entry-key  (match-string-no-properties 2))
        (fields     `((:bibtype . ,(downcase (match-string-no-properties 1))))))
    (goto-char (match-end 0))
    (cl-block field-loop
      (while t
        (skip-chars-forward " \t\n\r,")
        (cond
         ((eq (char-after) ?}) (forward-char 1) (cl-return-from field-loop))
         ((eobp) (error "a3-pub-bib: unexpected EOF inside entry %s" entry-key))
         ((looking-at "\\([A-Za-z][A-Za-z0-9_-]*\\)[ \t]*=[ \t]*")
          (let ((name (intern (downcase (match-string-no-properties 1)))))
            (goto-char (match-end 0))
            (let ((value (a3madkour-pub-bib--parse-field-value)))
              (push (cons name value) fields))))
         (t (error "a3-pub-bib: malformed field in entry %s at pos %d"
                   entry-key (point))))))
    (cons entry-key (nreverse fields))))

(defun a3madkour-pub-bib--parse-buffer ()
  "Parse the current buffer (assumed to hold .bib text), populating
`a3madkour-pub-bib--parser-cache'.  Skips bare-line BibTeX comments,
recognizes (but does not yet substitute) @string and skips @preamble.
Returns the number of entries cached."
  (a3madkour-pub-bib--parser-init)
  (goto-char (point-min))
  (let ((count 0))
    (while (re-search-forward "^@" nil t)
      (backward-char 1)
      (cond
       ((looking-at "@string[ \t]*{")
        (goto-char (match-end 0))
        (a3madkour-pub-bib--read-balanced-braces))     ;; skip for Task 3
       ((looking-at "@preamble[ \t]*{")
        (goto-char (match-end 0))
        (a3madkour-pub-bib--read-balanced-braces))
       (t
        (let ((pair (a3madkour-pub-bib--parse-one-entry)))
          (puthash (car pair) (cdr pair) a3madkour-pub-bib--parser-cache)
          (setq count (1+ count))))))
    count))

(defun a3madkour-pub-bib/parse-file (path)
  "Parse the .bib file at PATH into the parser cache.  Returns the
number of entries cached.  Signals if PATH does not exist."
  (unless (file-exists-p path)
    (error "a3-pub-bib: library.bib not found at %s" path))
  (with-temp-buffer
    (insert-file-contents path)
    (a3madkour-pub-bib--parse-buffer)))

(provide 'a3madkour-publish-bib)

;;; a3madkour-publish-bib.el ends here
```

- [ ] **Step 2: Write the test sibling**

Create `a3madkour-publish-bib-test.el`:

```elisp
;;; a3madkour-publish-bib-test.el --- ert tests for F bib resolver -*- lexical-binding: t; -*-

(require 'ert)
(require 'cl-lib)
(require 'a3madkour-publish-bib)

;; -- Helpers --

(defmacro a3madkour-pub-bib-test--with-bib (bib-string &rest body)
  "Parse BIB-STRING into the parser cache, then run BODY."
  (declare (indent 1))
  `(with-temp-buffer
     (insert ,bib-string)
     (a3madkour-pub-bib--parse-buffer)
     ,@body))

;; -- Task 3: entry recognition + simple fields --

(ert-deftest a3madkour-pub-bib-test/parses-single-entry ()
  "F Task 3: a minimal @article entry parses into the cache."
  (a3madkour-pub-bib-test--with-bib
      "@article{key1, title = {Hello}, year = 2020}"
    (let ((entry (gethash "key1" a3madkour-pub-bib--parser-cache)))
      (should entry)
      (should (equal (alist-get 'title entry) "Hello"))
      (should (equal (alist-get 'year entry) "2020"))
      (should (equal (alist-get :bibtype entry) "article")))))

(ert-deftest a3madkour-pub-bib-test/parses-quoted-field ()
  "F Task 3: double-quoted field value is read."
  (a3madkour-pub-bib-test--with-bib
      "@misc{key2, title = \"Quoted Title\"}"
    (should (equal (alist-get 'title
                              (gethash "key2" a3madkour-pub-bib--parser-cache))
                   "Quoted Title"))))

(ert-deftest a3madkour-pub-bib-test/parses-bare-numeric-field ()
  "F Task 3: bare numeric field value (e.g. year = 2018) is read."
  (a3madkour-pub-bib-test--with-bib
      "@book{key3, title = {T}, year = 2018}"
    (should (equal (alist-get 'year
                              (gethash "key3" a3madkour-pub-bib--parser-cache))
                   "2018"))))

(ert-deftest a3madkour-pub-bib-test/parses-multiple-entries ()
  "F Task 3: 3 sibling entries all land in the cache."
  (a3madkour-pub-bib-test--with-bib
      "@article{a, title={A}}\n@book{b, title={B}}\n@misc{c, title={C}}"
    (should (= 3 (hash-table-count a3madkour-pub-bib--parser-cache)))
    (should (equal "A" (alist-get 'title (gethash "a" a3madkour-pub-bib--parser-cache))))
    (should (equal "B" (alist-get 'title (gethash "b" a3madkour-pub-bib--parser-cache))))
    (should (equal "C" (alist-get 'title (gethash "c" a3madkour-pub-bib--parser-cache))))))

(ert-deftest a3madkour-pub-bib-test/skips-bibtex-comments ()
  "F Task 3: lines starting with `%' (BibTeX comment) are skipped."
  (a3madkour-pub-bib-test--with-bib
      "% comment line\n@article{ok, title = {T}}"
    (should (gethash "ok" a3madkour-pub-bib--parser-cache))))

(ert-deftest a3madkour-pub-bib-test/skips-string-and-preamble ()
  "F Task 3: @string and @preamble blocks are recognized and skipped."
  (a3madkour-pub-bib-test--with-bib
      "@string{me = \"Author\"}\n@preamble{\"junk\"}\n@misc{ok, title={T}}"
    (should (gethash "ok" a3madkour-pub-bib--parser-cache))
    (should-not (gethash "me" a3madkour-pub-bib--parser-cache))))

(ert-deftest a3madkour-pub-bib-test/case-preserves-key ()
  "F Task 3: BBT camelCase keys keep their case in the cache."
  (a3madkour-pub-bib-test--with-bib
      "@article{abelaConstructiveApproachGeneration2015, title={T}}"
    (should (gethash "abelaConstructiveApproachGeneration2015"
                     a3madkour-pub-bib--parser-cache))
    (should-not (gethash "abelaconstructiveapproachgeneration2015"
                         a3madkour-pub-bib--parser-cache))))

(ert-deftest a3madkour-pub-bib-test/parse-file-returns-count ()
  "F Task 3: parse-file returns the number of entries cached."
  (let* ((tmp (make-temp-file "bib-fixture-" nil ".bib")))
    (unwind-protect
        (progn
          (with-temp-file tmp
            (insert "@article{a, title={A}}\n@book{b, title={B}}"))
          (should (= 2 (a3madkour-pub-bib/parse-file tmp))))
      (delete-file tmp))))

(ert-deftest a3madkour-pub-bib-test/parse-file-signals-on-missing ()
  "F Task 3: parse-file signals when path doesn't exist."
  (should-error
   (a3madkour-pub-bib/parse-file "/nonexistent/path/library.bib")))

(provide 'a3madkour-publish-bib-test)

;;; a3madkour-publish-bib-test.el ends here
```

- [ ] **Step 3: Run ert to verify Task 3 tests pass**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-bib|Ran [0-9]+|FAIL" | head -20`
Expected: 9 new tests all PASS; `Ran <baseline+9> tests, all results as expected, 0 unexpected`.

- [ ] **Step 4: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el
git commit -m "$(cat <<'EOF'
feat(f): bib parser module — entry recognition + simple fields (Task 3)

a3madkour-publish-bib.el reads BibTeX entries into a per-run cache.
Task 3 covers @type{key, field = value} where value is {braced},
"quoted", or bare numeric.  @string + @preamble blocks recognized
and skipped (substitution lands in Task 5).  Case-preserved keys
support BBT camelCase.  9 ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4 — `.bib` parser: nested braces + author splitting + date extraction

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el` (add helpers)
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el` (append tests)

- [ ] **Step 1: Write 8 failing tests**

Append to `a3madkour-publish-bib-test.el` before its `(provide ...)`:

```elisp
;; -- Task 4: nested braces + author splitting + date extraction --

(ert-deftest a3madkour-pub-bib-test/preserves-nested-braces ()
  "F Task 4: nested {{...}} brace protection — outer pair stripped by
normalize-entry; for the raw parser, both braces survive on the value
string (normalize is Task 6)."
  (a3madkour-pub-bib-test--with-bib
      "@article{k, title = {{Egyptian Streets}}}"
    (let ((title (alist-get 'title (gethash "k" a3madkour-pub-bib--parser-cache))))
      (should (equal title "{Egyptian Streets}")))))

(ert-deftest a3madkour-pub-bib-test/strip-outer-braces-one-pair ()
  "F Task 4: helper strips exactly one outer brace-pair."
  (should (equal (a3madkour-pub-bib--strip-outer-braces "{Hello}")    "Hello"))
  (should (equal (a3madkour-pub-bib--strip-outer-braces "{{Hello}}")  "{Hello}"))
  (should (equal (a3madkour-pub-bib--strip-outer-braces "Hello")      "Hello"))
  (should (equal (a3madkour-pub-bib--strip-outer-braces "  {Hi}  ")   "Hi")))

(ert-deftest a3madkour-pub-bib-test/split-authors-on-and ()
  "F Task 4: BibTeX author field splits on ' and ' (BibTeX convention)."
  (should (equal (a3madkour-pub-bib--split-authors "Lastname, F. and Other, G.")
                 '("Lastname, F." "Other, G.")))
  (should (equal (a3madkour-pub-bib--split-authors "One, A. and Two, B. and Three, C.")
                 '("One, A." "Two, B." "Three, C.")))
  (should (equal (a3madkour-pub-bib--split-authors "Solo, A.")
                 '("Solo, A."))))

(ert-deftest a3madkour-pub-bib-test/split-authors-empty-string ()
  "F Task 4: empty author field returns empty list."
  (should (equal (a3madkour-pub-bib--split-authors "") nil))
  (should (equal (a3madkour-pub-bib--split-authors "   ") nil)))

(ert-deftest a3madkour-pub-bib-test/year-from-date-iso ()
  "F Task 4: extract year int from ISO date string."
  (should (= 2014 (a3madkour-pub-bib--year-from-date "2014-12-27")))
  (should (= 2014 (a3madkour-pub-bib--year-from-date "2014-12-27T16:00:18+00:00")))
  (should (= 2014 (a3madkour-pub-bib--year-from-date "2014"))))

(ert-deftest a3madkour-pub-bib-test/year-from-date-nil-on-junk ()
  "F Task 4: junk input returns nil."
  (should-not (a3madkour-pub-bib--year-from-date "junk"))
  (should-not (a3madkour-pub-bib--year-from-date ""))
  (should-not (a3madkour-pub-bib--year-from-date nil)))

(ert-deftest a3madkour-pub-bib-test/parser-handles-real-fixture ()
  "F Task 4: the stub library.bib fixture parses without error and yields
9 entries, including the BBT camelCase key from Task 3."
  ;; tools/fixtures/citations/library.bib lives in the SITE repo; locate
  ;; via a robust path discovery (a3-pub.sh sets cwd, so use $PWD or env).
  (let ((fixture
         (or (and (boundp 'a3madkour-pub-test/site-root)
                  (expand-file-name
                   "tools/fixtures/citations/library.bib"
                   a3madkour-pub-test/site-root))
             (expand-file-name
              "../../../../Sync/Workspace/a3madkour.github.io/tools/fixtures/citations/library.bib"
              (file-name-directory (or load-file-name buffer-file-name "."))))))
    (skip-unless (file-exists-p fixture))
    (let ((n (a3madkour-pub-bib/parse-file fixture)))
      (should (= 9 n))
      (should (gethash "loremIpsumDolorSit2020" a3madkour-pub-bib--parser-cache)))))

(ert-deftest a3madkour-pub-bib-test/multiline-field-value-survives ()
  "F Task 4: a {...} value spanning multiple lines reads as one string."
  (a3madkour-pub-bib-test--with-bib
      "@article{k,\n  title = {Line one\n  line two},\n  year = 2020}"
    (let ((title (alist-get 'title (gethash "k" a3madkour-pub-bib--parser-cache))))
      (should (string-match-p "Line one" title))
      (should (string-match-p "line two" title)))))
```

- [ ] **Step 2: Run to verify failures**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "split-authors|year-from-date|nested-braces|FAIL" | head -15`
Expected: tests for `split-authors`, `year-from-date`, and fixture parse fail (helpers not yet defined; fixture path may not resolve until later).

- [ ] **Step 3: Add the helpers**

Append to `a3madkour-publish-bib.el` BEFORE the `(provide ...)` line:

```elisp
(defun a3madkour-pub-bib--split-authors (s)
  "Split S on ` and ' (BibTeX author-list convention).  Returns a list
of trimmed author strings; empty input → nil."
  (when (and (stringp s) (not (string-empty-p (string-trim s))))
    (mapcar #'string-trim
            (split-string s " and " t "[ \t\n\r]+"))))

(defun a3madkour-pub-bib--year-from-date (s)
  "Extract a 4-digit year int from S (an ISO date string, year-only, or
junk).  Returns int or nil."
  (when (and (stringp s)
             (string-match "\\`\\([0-9]\\{4\\}\\)" s))
    (string-to-number (match-string 1 s))))
```

- [ ] **Step 4: Re-run all tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-bib|Ran [0-9]+|FAIL" | head -20`
Expected: 17 total `a3madkour-pub-bib` tests pass (9 Task 3 + 8 Task 4).

Note: `parser-handles-real-fixture` may skip if the fixture path doesn't resolve in your test runner. If it skips silently, that's fine — Task 17's integration test pins fixture loading.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el
git commit -m "$(cat <<'EOF'
feat(f): bib parser — nested braces, author split, year extraction (Task 4)

split-authors splits BibTeX author lists on ' and ' per the BibTeX
convention.  year-from-date extracts the first 4 digits of an ISO
date or year-only string.  strip-outer-braces removes one outer
pair (used by normalize-entry in Task 6).  8 new ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5 — `.bib` parser: `@string` substitution + error paths

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el`

- [ ] **Step 1: Write 5 failing tests**

Append to `a3madkour-publish-bib-test.el` before its `(provide ...)`:

```elisp
;; -- Task 5: @string substitution + error paths --

(ert-deftest a3madkour-pub-bib-test/string-substitution ()
  "F Task 5: @string{shortcut = \"expansion\"} substitutes when a field
value is the bare shortcut token (BibTeX `concat`-by-#-of-strings is OUT
of V1; we only handle the bare-reference form because real Zotero/BBT
output doesn't use the `#` concat form)."
  (a3madkour-pub-bib-test--with-bib
      "@string{acm = \"ACM\"}\n@article{k, title = {T}, publisher = acm}"
    (should (equal "ACM"
                   (alist-get 'publisher
                              (gethash "k" a3madkour-pub-bib--parser-cache))))))

(ert-deftest a3madkour-pub-bib-test/unbalanced-braces-signals ()
  "F Task 5: unbalanced braces in a field value signal a clear error."
  (should-error
   (a3madkour-pub-bib-test--with-bib
       "@article{k, title = {Hello"
     nil)))

(ert-deftest a3madkour-pub-bib-test/malformed-entry-header-signals ()
  "F Task 5: an `@type` without `{key,` signals."
  (should-error
   (a3madkour-pub-bib-test--with-bib
       "@article corrupt"
     nil)))

(ert-deftest a3madkour-pub-bib-test/unterminated-quoted-value-signals ()
  "F Task 5: an opened `\"` with no closing `\"` signals."
  (should-error
   (a3madkour-pub-bib-test--with-bib
       "@article{k, title = \"unterminated"
     nil)))

(ert-deftest a3madkour-pub-bib-test/empty-file-returns-zero ()
  "F Task 5: parsing an empty buffer is a no-op returning 0."
  (a3madkour-pub-bib-test--with-bib ""
    (should (= 0 (hash-table-count a3madkour-pub-bib--parser-cache)))))
```

- [ ] **Step 2: Run to verify failures**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "string-substitution|unbalanced|malformed|unterminated|FAIL" | head -10`
Expected: `string-substitution` fails (no substitution logic yet); other error-path tests may already pass via Task 3's parse-error checks.

- [ ] **Step 3: Implement `@string` substitution**

Update the parser to:
1. Cache `@string` shortcut→expansion bindings in a session defvar.
2. When a field value is a bare identifier matching a cached `@string` key, substitute the expansion.

Edit `a3madkour-publish-bib.el`. Add the defvar near the top with other defvars:

```elisp
(defvar a3madkour-pub-bib--string-table nil
  "Hash table mapping @string shortcut symbol to its expansion (string).
Reset by `parser-init'; populated during buffer parse.")
```

Update `a3madkour-pub-bib--parser-init`:

```elisp
(defun a3madkour-pub-bib--parser-init ()
  "Allocate a fresh empty parser cache + @string table."
  (setq a3madkour-pub-bib--parser-cache (make-hash-table :test 'equal :size 256))
  (setq a3madkour-pub-bib--string-table (make-hash-table :test 'eq :size 32)))
```

Update the `@string` branch in `a3madkour-pub-bib--parse-buffer`:

```elisp
       ((looking-at "@string[ \t]*{[ \t]*\\([A-Za-z][A-Za-z0-9_-]*\\)[ \t]*=[ \t]*")
        (let ((shortcut (intern (downcase (match-string-no-properties 1)))))
          (goto-char (match-end 0))
          (let ((expansion (a3madkour-pub-bib--parse-field-value)))
            (puthash shortcut expansion a3madkour-pub-bib--string-table)
            ;; Skip the trailing `}'.
            (skip-chars-forward " \t\n\r")
            (when (eq (char-after) ?})
              (forward-char 1)))))
```

Update `a3madkour-pub-bib--parse-field-value` to handle bare-identifier substitution:

```elisp
(defun a3madkour-pub-bib--parse-field-value ()
  "Reader: at point at the first non-whitespace char of a field value,
read one value form: `{...}', `\"...\"', a bare numeric token, or a
bare identifier matched against the @string table."
  (skip-chars-forward " \t\n\r")
  (cond
   ((eq (char-after) ?{)  (forward-char 1) (a3madkour-pub-bib--read-balanced-braces))
   ((eq (char-after) ?\") (forward-char 1) (a3madkour-pub-bib--read-quoted-value))
   ((looking-at "\\([0-9]+\\)")
    (goto-char (match-end 0))
    (match-string-no-properties 1))
   ((looking-at "\\([A-Za-z][A-Za-z0-9_-]*\\)")
    (let ((token (intern (downcase (match-string-no-properties 1)))))
      (goto-char (match-end 0))
      (or (and a3madkour-pub-bib--string-table
               (gethash token a3madkour-pub-bib--string-table))
          (symbol-name token))))
   (t (error "a3-pub-bib: unexpected field-value start at pos %d" (point)))))
```

- [ ] **Step 4: Re-run all tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-bib|Ran [0-9]+|FAIL" | head -25`
Expected: 22 total `a3madkour-pub-bib` tests pass (9 + 8 + 5).

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el
git commit -m "$(cat <<'EOF'
feat(f): bib parser — @string substitution + error paths (Task 5)

@string{shortcut = "expansion"} now substitutes when a field value
is the bare shortcut token.  Unbalanced braces, malformed @type
headers, and unterminated quoted values signal clear errors with
position info.  Empty buffer is a 0-count no-op.  5 new ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6 — `normalize-entry`: raw alist → schema plist

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el`

- [ ] **Step 1: Write 10 failing tests**

Append to `a3madkour-publish-bib-test.el` before its `(provide ...)`:

```elisp
;; -- Task 6: normalize-entry --

(defmacro a3madkour-pub-bib-test--normalized (bib-string key &rest body)
  "Parse BIB-STRING, fetch KEY's raw alist, normalize it; bind ENTRY."
  (declare (indent 2))
  `(a3madkour-pub-bib-test--with-bib ,bib-string
     (let ((entry (a3madkour-pub-bib--normalize-entry
                   (gethash ,key a3madkour-pub-bib--parser-cache))))
       ,@body)))

(ert-deftest a3madkour-pub-bib-test/normalize-authors-list ()
  "F Task 6: authors split on ' and ' → list of strings."
  (a3madkour-pub-bib-test--normalized
      "@article{k, author = {Last, F. and Other, G.}, title={T}, date={2020}, journaltitle={J}}"
      "k"
    (should (equal '("Last, F." "Other, G.") (plist-get entry :authors)))))

(ert-deftest a3madkour-pub-bib-test/normalize-empty-author-fallback ()
  "F Task 6: missing author → :authors '(\"Unknown\")."
  (a3madkour-pub-bib-test--normalized
      "@online{k, title={T}, date={2024}, url={https://example.invalid/x}}"
      "k"
    (should (equal '("Unknown") (plist-get entry :authors)))))

(ert-deftest a3madkour-pub-bib-test/normalize-year-from-iso-date ()
  "F Task 6: ISO date → integer year."
  (a3madkour-pub-bib-test--normalized
      "@article{k, author={A, A}, title={T}, date={2014-12-27}, journaltitle={J}}"
      "k"
    (should (= 2014 (plist-get entry :year)))))

(ert-deftest a3madkour-pub-bib-test/normalize-year-from-legacy-year ()
  "F Task 6: legacy `year = 2018' (no date) extracts to int."
  (a3madkour-pub-bib-test--normalized
      "@book{k, author={A, A}, title={T}, year={2018}, publisher={P}}"
      "k"
    (should (= 2018 (plist-get entry :year)))))

(ert-deftest a3madkour-pub-bib-test/normalize-venue-journaltitle-wins ()
  "F Task 6: journaltitle is preferred over booktitle/publisher."
  (a3madkour-pub-bib-test--normalized
      "@article{k, author={A, A}, title={T}, date={2020}, journaltitle={J}, publisher={P}}"
      "k"
    (should (equal "J" (plist-get entry :venue)))))

(ert-deftest a3madkour-pub-bib-test/normalize-venue-booktitle-fallback ()
  "F Task 6: no journaltitle → booktitle wins."
  (a3madkour-pub-bib-test--normalized
      "@inproceedings{k, author={A, A}, title={T}, date={2020}, booktitle={Proc Conf}}"
      "k"
    (should (equal "Proc Conf" (plist-get entry :venue)))))

(ert-deftest a3madkour-pub-bib-test/normalize-venue-publisher-fallback ()
  "F Task 6: no journaltitle/booktitle → publisher wins."
  (a3madkour-pub-bib-test--normalized
      "@book{k, author={A, A}, title={T}, date={2020}, publisher={Book Co}}"
      "k"
    (should (equal "Book Co" (plist-get entry :venue)))))

(ert-deftest a3madkour-pub-bib-test/normalize-venue-eventtitle-fallback ()
  "F Task 6: no journaltitle/booktitle/publisher → eventtitle wins."
  (a3madkour-pub-bib-test--normalized
      "@misc{k, author={A, A}, title={T}, date={2020}, eventtitle={Some Event}}"
      "k"
    (should (equal "Some Event" (plist-get entry :venue)))))

(ert-deftest a3madkour-pub-bib-test/normalize-type-known-enum ()
  "F Task 6: @article → \"article\"; @inproceedings → \"inproceedings\"."
  (a3madkour-pub-bib-test--normalized
      "@article{k, author={A, A}, title={T}, date={2020}, journaltitle={J}}"
      "k"
    (should (equal "article" (plist-get entry :type)))))

(ert-deftest a3madkour-pub-bib-test/normalize-type-unknown-to-misc ()
  "F Task 6: unknown @entrytype maps to \"misc\"."
  (a3madkour-pub-bib-test--normalized
      "@weirdtype{k, author={A, A}, title={T}, date={2020}, publisher={P}}"
      "k"
    (should (equal "misc" (plist-get entry :type)))))

(ert-deftest a3madkour-pub-bib-test/normalize-strips-outer-title-braces ()
  "F Task 6: title outer braces stripped; inner survive."
  (a3madkour-pub-bib-test--normalized
      "@article{k, author={A, A}, title={{Egyptian Streets}}, date={2014}, journaltitle={J}}"
      "k"
    (should (equal "{Egyptian Streets}" (plist-get entry :title)))))

(ert-deftest a3madkour-pub-bib-test/normalize-rejects-bad-url ()
  "F Task 6: non-http URL is dropped to nil."
  (a3madkour-pub-bib-test--normalized
      "@misc{k, author={A, A}, title={T}, date={2020}, publisher={P}, url={ftp://nope}}"
      "k"
    (should-not (plist-get entry :url))))
```

- [ ] **Step 2: Run to verify failures**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "normalize|FAIL" | head -15`
Expected: all `normalize-*` tests FAIL (`a3madkour-pub-bib--normalize-entry` undefined).

- [ ] **Step 3: Implement `normalize-entry`**

Append to `a3madkour-publish-bib.el` BEFORE the `(provide ...)` line:

```elisp
;; ---------------------------------------------------------------------
;; normalize-entry: raw alist → schema plist (Task 6)
;; ---------------------------------------------------------------------

(defconst a3madkour-pub-bib--type-enum
  '("article" "book" "inproceedings" "incollection" "online" "misc"
    "report" "thesis" "unpublished")
  "Known yaml :type enum.  Unknown @entrytypes collapse to \"misc\".")

(defun a3madkour-pub-bib--normalize-venue (raw)
  "Pick venue from RAW alist by priority chain."
  (or (alist-get 'journaltitle raw)
      (alist-get 'booktitle raw)
      (alist-get 'publisher raw)
      (alist-get 'eventtitle raw)))

(defun a3madkour-pub-bib--normalize-url (raw)
  "Return RAW's url field iff it starts with http(s)://; else nil."
  (let ((u (alist-get 'url raw)))
    (and (stringp u)
         (or (string-prefix-p "http://" u) (string-prefix-p "https://" u))
         u)))

(defun a3madkour-pub-bib--normalize-type (raw)
  "Return RAW's :bibtype iff in the known enum; else \"misc\"."
  (let ((t1 (alist-get :bibtype raw)))
    (if (and t1 (member t1 a3madkour-pub-bib--type-enum))
        t1
      "misc")))

(defun a3madkour-pub-bib--normalize-entry (raw)
  "Map a parser-cache RAW alist to the schema plist.  Returns nil for nil."
  (when raw
    (let* ((authors-raw (alist-get 'author raw))
           (authors (or (a3madkour-pub-bib--split-authors authors-raw)
                        '("Unknown")))
           (year (or (a3madkour-pub-bib--year-from-date (alist-get 'date raw))
                     (a3madkour-pub-bib--year-from-date (alist-get 'year raw))))
           (title-raw (alist-get 'title raw))
           (title (and title-raw (a3madkour-pub-bib--strip-outer-braces title-raw)))
           (venue (a3madkour-pub-bib--normalize-venue raw)))
      (list :authors   authors
            :year      year
            :title     title
            :venue     venue
            :url       (a3madkour-pub-bib--normalize-url raw)
            :doi       (alist-get 'doi raw)
            :publisher (alist-get 'publisher raw)
            :volume    (alist-get 'volume raw)
            :issue     (or (alist-get 'issue raw) (alist-get 'number raw))
            :pages     (alist-get 'pages raw)
            :isbn      (alist-get 'isbn raw)
            :type      (a3madkour-pub-bib--normalize-type raw)))))
```

- [ ] **Step 4: Re-run all tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-bib|Ran [0-9]+|FAIL" | head -30`
Expected: 34 total `a3madkour-pub-bib` tests pass.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el
git commit -m "$(cat <<'EOF'
feat(f): bib normalize-entry — raw alist → schema plist (Task 6)

Maps the parser's raw field alist into the data/citations.yaml schema
shape: authors split on ' and ', year from ISO date or legacy year,
venue resolved through journaltitle→booktitle→publisher→eventtitle
chain, outer brace-stripped title, dropped non-http URL, type enum
with misc fallback, empty-author fallback to ("Unknown").  12 new
ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7 — `bib-resolve` dispatch + citar adapter

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el`

- [ ] **Step 1: Write 5 failing tests**

Append to `a3madkour-publish-bib-test.el` before its `(provide ...)`:

```elisp
;; -- Task 7: bib-resolve dispatch + citar adapter --

(ert-deftest a3madkour-pub-bib-test/resolve-via-parser ()
  "F Task 7: when citar is NOT loaded (forced), resolve goes through
the parser path and returns the schema plist."
  (a3madkour-pub-bib-test--with-bib
      "@article{k, author={A, A}, title={T}, date={2020}, journaltitle={J}}"
    (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
               (lambda () nil)))
      (let ((entry (a3madkour-pub-bib/resolve "k")))
        (should entry)
        (should (equal "T" (plist-get entry :title)))
        (should (equal '("A, A") (plist-get entry :authors)))))))

(ert-deftest a3madkour-pub-bib-test/resolve-unknown-returns-nil ()
  "F Task 7: resolve returns nil for unknown keys."
  (a3madkour-pub-bib-test--with-bib "@article{a, title={A}}"
    (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
               (lambda () nil)))
      (should-not (a3madkour-pub-bib/resolve "nonexistent")))))

(ert-deftest a3madkour-pub-bib-test/resolve-via-citar-when-loaded ()
  "F Task 7: when citar IS loaded (forced), resolve calls citar."
  (let ((calls 0))
    (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
               (lambda () t))
              ((symbol-function 'a3madkour-pub-bib--read-via-citar)
               (lambda (key)
                 (setq calls (1+ calls))
                 (list :authors '("CitarA, A") :year 2020 :title "CitarT"
                       :venue "CitarV" :url nil :doi nil :publisher nil
                       :volume nil :issue nil :pages nil :isbn nil
                       :type "article"))))
      (let ((entry (a3madkour-pub-bib/resolve "k")))
        (should (= 1 calls))
        (should (equal "CitarT" (plist-get entry :title)))))))

(ert-deftest a3madkour-pub-bib-test/resolve-parity-parser-vs-citar ()
  "F Task 7: parser and citar paths return plist-equal results for the
same fixture entry.  Drift safeguard — see spec §9."
  (a3madkour-pub-bib-test--with-bib
      "@article{k, author={Last, F.}, title={T}, date={2020}, journaltitle={J}}"
    (let* ((parser-result
            (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
                       (lambda () nil)))
              (a3madkour-pub-bib/resolve "k")))
           (citar-result
            (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
                       (lambda () t))
                      ((symbol-function 'a3madkour-pub-bib--read-via-citar)
                       (lambda (_) parser-result)))   ;; stub returns same plist
              (a3madkour-pub-bib/resolve "k"))))
      (should (equal parser-result citar-result)))))

(ert-deftest a3madkour-pub-bib-test/citar-loaded-p-detection ()
  "F Task 7: citar-loaded-p returns truthy iff citar is featurep'd."
  ;; Force not loaded.
  (cl-letf (((symbol-function 'featurep)
             (lambda (sym) (and (not (eq sym 'citar))))))
    (should-not (a3madkour-pub-bib--citar-loaded-p)))
  ;; Force loaded.
  (cl-letf (((symbol-function 'featurep)
             (lambda (sym) (or (eq sym 'citar)))))
    (should (a3madkour-pub-bib--citar-loaded-p))))
```

- [ ] **Step 2: Run to verify failures**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "resolve|citar-loaded-p|FAIL" | head -15`
Expected: all 5 new tests FAIL (functions undefined).

- [ ] **Step 3: Implement the dispatcher + adapter**

Append to `a3madkour-publish-bib.el` BEFORE the `(provide ...)` line:

```elisp
;; ---------------------------------------------------------------------
;; bib-resolve: dispatch + citar adapter (Task 7)
;; ---------------------------------------------------------------------

(defun a3madkour-pub-bib--citar-loaded-p ()
  "Return non-nil iff citar is loaded (featurep) AND its API is bound."
  (and (featurep 'citar)
       (fboundp 'citar-get-entry)
       (fboundp 'citar-get-value)))

(defun a3madkour-pub-bib--read-via-parser (key)
  "Parser path: KEY → schema plist via parser cache + normalize-entry."
  (a3madkour-pub-bib--normalize-entry
   (and a3madkour-pub-bib--parser-cache
        (gethash key a3madkour-pub-bib--parser-cache))))

(defun a3madkour-pub-bib--read-via-citar (key)
  "Citar path: KEY → schema plist via citar's API.  Mirrors normalize-entry
by reading citar's field accessors.  Returns nil if citar doesn't know KEY."
  (when (a3madkour-pub-bib--citar-loaded-p)
    (let ((entry (citar-get-entry key)))
      (when entry
        ;; citar-get-value returns a string or nil; behave like the parser's
        ;; raw alist by building a synthetic alist and feeding normalize-entry.
        (let ((raw
               (delq nil
                     (mapcar
                      (lambda (field)
                        (let ((v (citar-get-value field entry)))
                          (and v (cons (intern (downcase (symbol-name field))) v))))
                      '(:bibtype author title date year journaltitle booktitle
                                 publisher eventtitle url doi volume issue
                                 number pages isbn)))))
          ;; citar's :bibtype isn't a real field name; pull it from entry.
          (let ((bt (or (citar-get-value 'type entry)
                        (alist-get '=type= entry)
                        (citar-get-value '=type= entry))))
            (when bt
              (push (cons :bibtype (downcase (format "%s" bt))) raw)))
          (a3madkour-pub-bib--normalize-entry raw))))))

(defun a3madkour-pub-bib/resolve (key)
  "Resolve KEY (string) to a schema plist or nil.

Dispatcher: prefers citar when loaded; otherwise uses parser cache.
The parser cache must be primed by `parse-file' or an in-test
`parser-init'+`parse-buffer' before resolve can return non-nil on
the parser path."
  (if (a3madkour-pub-bib--citar-loaded-p)
      (a3madkour-pub-bib--read-via-citar key)
    (a3madkour-pub-bib--read-via-parser key)))
```

- [ ] **Step 4: Re-run all tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-bib|Ran [0-9]+|FAIL" | head -30`
Expected: 39 total `a3madkour-pub-bib` tests pass.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el
git commit -m "$(cat <<'EOF'
feat(f): bib-resolve dispatch + citar adapter (Task 7)

resolve dispatches between citar-loaded path and parser path with
the same plist shape via normalize-entry.  Parity test pins the
shapes equal entry-by-entry as a drift safeguard.  5 new ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8 — `cite--scan-buffer`: org-element citation discovery

**Files:**
- Create: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el`
- Create: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el`

- [ ] **Step 1: Write the module skeleton**

Create `a3madkour-publish-citations.el`:

```elisp
;;; a3madkour-publish-citations.el --- F citation pipeline -*- lexical-binding: t; -*-

;;; Commentary:

;; F sub-project orchestrator.  Owns:
;;   - pre-export buffer rewriter: [cite:@key] → @@hugo:{{< cite "key" >}}@@
;;   - per-run cite-key accumulator
;;   - notes_ref auto-detection
;;   - data/citations.yaml emitter (merge-on-publish, purge-on-sync)
;;   - M-x a3-sync-citations command

;;; Code:

(require 'cl-lib)
(require 'subr-x)
(require 'org)
(require 'org-element)
(require 'a3madkour-publish-bib)

(defvar a3madkour-pub-citations--accumulator nil
  "Hash table mapping cite-key (string) to list of (SOURCE-FILE . POS)
pairs, populated by the rewriter during the publish run.")

(defun a3madkour-pub-citations--accumulator-init ()
  "Allocate a fresh empty accumulator hash."
  (setq a3madkour-pub-citations--accumulator
        (make-hash-table :test 'equal :size 64)))

(defun a3madkour-pub-citations--scan-buffer ()
  "Walk the current org buffer via `org-element-parse-buffer'; return a
list of (KEY . POS) pairs for every citation element.  POS is the
buffer position of the element's `begin' marker.  Multi-cite forms
return one pair per key in source order.  Style-overrides (`/text',
`/noauthor', `/locators') and prefix/suffix text are NOT filtered here
— Task 9's rewriter checks those and signals."
  (let ((tree (org-element-parse-buffer))
        (acc nil))
    (org-element-map tree 'citation
      (lambda (cite)
        (let ((begin (org-element-property :begin cite)))
          (dolist (ref (org-element-map cite 'citation-reference #'identity))
            (let ((key (org-element-property :key ref)))
              (when (and key (not (string-empty-p key)))
                (push (cons key begin) acc)))))))
    (nreverse acc)))

(provide 'a3madkour-publish-citations)

;;; a3madkour-publish-citations.el ends here
```

- [ ] **Step 2: Write the test sibling**

Create `a3madkour-publish-citations-test.el`:

```elisp
;;; a3madkour-publish-citations-test.el --- ert tests for F citations -*- lexical-binding: t; -*-

(require 'ert)
(require 'cl-lib)
(require 'org)
(require 'a3madkour-publish-citations)

;; -- Helpers --

(defmacro a3madkour-pub-citations-test--with-org (org-string &rest body)
  "Insert ORG-STRING into a temp org buffer, run BODY there."
  (declare (indent 1))
  `(with-temp-buffer
     (org-mode)
     (insert ,org-string)
     (goto-char (point-min))
     ,@body))

;; -- Task 8: cite--scan-buffer --

(ert-deftest a3madkour-pub-citations-test/scan-bare-cite ()
  "F Task 8: a bare [cite:@k] is discovered."
  (a3madkour-pub-citations-test--with-org
      "* Heading\nBody [cite:@key1] more.\n"
    (let ((pairs (a3madkour-pub-citations--scan-buffer)))
      (should (= 1 (length pairs)))
      (should (equal "key1" (car (car pairs)))))))

(ert-deftest a3madkour-pub-citations-test/scan-multi-cite ()
  "F Task 8: [cite:@a;@b;@c] yields 3 pairs in source order."
  (a3madkour-pub-citations-test--with-org
      "Body [cite:@a;@b;@c] tail.\n"
    (let ((pairs (a3madkour-pub-citations--scan-buffer)))
      (should (= 3 (length pairs)))
      (should (equal '("a" "b" "c") (mapcar #'car pairs))))))

(ert-deftest a3madkour-pub-citations-test/scan-skips-src-blocks ()
  "F Task 8: [cite:@k] inside a #+BEGIN_SRC block is NOT discovered."
  (a3madkour-pub-citations-test--with-org
      "Body.\n#+BEGIN_SRC text\n[cite:@should-skip]\n#+END_SRC\n"
    (let ((pairs (a3madkour-pub-citations--scan-buffer)))
      (should-not pairs))))

(ert-deftest a3madkour-pub-citations-test/scan-skips-noexport-subtree ()
  "F Task 8: a :noexport: subtree is excluded from the scan."
  (a3madkour-pub-citations-test--with-org
      "* Public\nBody [cite:@public]\n* Private :noexport:\n[cite:@hidden]\n"
    (let* ((pairs (a3madkour-pub-citations--scan-buffer))
           (keys (mapcar #'car pairs)))
      ;; In org-element, :noexport: trees are still parsed; we filter them.
      ;; If org-element-parse-buffer does NOT filter them, this test pins
      ;; the requirement: scan must filter manually.
      (should (member "public" keys))
      (should-not (member "hidden" keys)))))

(ert-deftest a3madkour-pub-citations-test/scan-finds-cite-in-footnote ()
  "F Task 8: cite inside [fn:: ...] inline footnote is discovered."
  (a3madkour-pub-citations-test--with-org
      "Body[fn::See [cite:@fnkey].]\n"
    (let ((pairs (a3madkour-pub-citations--scan-buffer)))
      (should (member "fnkey" (mapcar #'car pairs))))))

(ert-deftest a3madkour-pub-citations-test/scan-finds-cite-in-table ()
  "F Task 8: cite inside a table cell is discovered."
  (a3madkour-pub-citations-test--with-org
      "| col |\n|-----|\n| [cite:@tab] |\n"
    (let ((pairs (a3madkour-pub-citations--scan-buffer)))
      (should (member "tab" (mapcar #'car pairs))))))

(ert-deftest a3madkour-pub-citations-test/scan-empty-buffer ()
  "F Task 8: empty buffer returns nil."
  (a3madkour-pub-citations-test--with-org ""
    (should-not (a3madkour-pub-citations--scan-buffer))))

(provide 'a3madkour-publish-citations-test)

;;; a3madkour-publish-citations-test.el ends here
```

- [ ] **Step 3: Run tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-citations|FAIL|Ran [0-9]+" | head -25`
Expected: 6 of 7 PASS. The `scan-skips-noexport-subtree` test may FAIL — `org-element-parse-buffer` does NOT filter `:noexport:` by default.

- [ ] **Step 4: Filter `:noexport:` if test fails**

If Step 3 surfaces the `:noexport:` failure, update `a3madkour-pub-citations--scan-buffer` to filter heading-bound `:noexport:` subtrees:

```elisp
(defun a3madkour-pub-citations--in-noexport-p (cite tree)
  "Return non-nil iff CITE element is inside a heading marked :noexport:."
  (let ((node (org-element-property :parent cite)))
    (while (and node
                (not (and (eq (org-element-type node) 'headline)
                          (member "noexport"
                                  (org-element-property :tags node)))))
      (setq node (org-element-property :parent node)))
    node))
```

Then in the `org-element-map` callback inside `scan-buffer`, wrap the body with `(unless (a3madkour-pub-citations--in-noexport-p cite tree) ...)`.

- [ ] **Step 5: Re-run and verify**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-citations|FAIL|Ran [0-9]+" | head -15`
Expected: all 7 PASS.

- [ ] **Step 6: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el
git commit -m "$(cat <<'EOF'
feat(f): citation scanner via org-element (Task 8)

scan-buffer walks the org parse tree for citation elements, returning
(key . pos) pairs in source order.  Multi-cite [cite:@a;@b;@c] yields
3 pairs; src blocks and :noexport: subtrees are excluded.  Works
through footnotes and table cells.  7 ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9 — `rewrite-cite-keys-in-buffer` + fail-fast

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el`

- [ ] **Step 1: Write 11 failing tests**

Append to `a3madkour-publish-citations-test.el` before its `(provide ...)`:

```elisp
;; -- Task 9: rewrite-cite-keys-in-buffer --

(defmacro a3madkour-pub-citations-test--rewritten (org-string &rest body)
  "Insert ORG-STRING, init accumulator, prime parser cache with a stub
.bib that resolves a/b/c/key1/fnkey/tab/public, run rewriter, run BODY."
  (declare (indent 1))
  `(progn
     (a3madkour-pub-citations--accumulator-init)
     (a3madkour-pub-bib-test--with-bib
         "@misc{key1, title={T}, date={2020}, author={A, A}, publisher={P}}
@misc{a, title={T}, date={2020}, author={A, A}, publisher={P}}
@misc{b, title={T}, date={2020}, author={A, A}, publisher={P}}
@misc{c, title={T}, date={2020}, author={A, A}, publisher={P}}
@misc{fnkey, title={T}, date={2020}, author={A, A}, publisher={P}}
@misc{tab, title={T}, date={2020}, author={A, A}, publisher={P}}
@misc{public, title={T}, date={2020}, author={A, A}, publisher={P}}"
       (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
                  (lambda () nil)))
         (a3madkour-pub-citations-test--with-org ,org-string
           (a3madkour-pub-citations/rewrite-cite-keys-in-buffer "/fake/source.org")
           ,@body)))))

(ert-deftest a3madkour-pub-citations-test/rewrite-bare-cite ()
  "F Task 9: [cite:@key1] becomes @@hugo:{{< cite \"key1\" >}}@@."
  (a3madkour-pub-citations-test--rewritten
      "Body [cite:@key1] tail.\n"
    (goto-char (point-min))
    (should (search-forward "@@hugo:{{< cite \"key1\" >}}@@" nil t))
    (should-not (search-forward "[cite:" nil t))))

(ert-deftest a3madkour-pub-citations-test/rewrite-multi-cite ()
  "F Task 9: [cite:@a;@b;@c] becomes 3 adjacent shortcodes inside one
@@hugo: wrapper."
  (a3madkour-pub-citations-test--rewritten
      "Body [cite:@a;@b;@c] tail.\n"
    (goto-char (point-min))
    (should (search-forward
             "@@hugo:{{< cite \"a\" >}}{{< cite \"b\" >}}{{< cite \"c\" >}}@@"
             nil t))))

(ert-deftest a3madkour-pub-citations-test/rewrite-populates-accumulator ()
  "F Task 9: each rewritten key lands in the accumulator with source file."
  (a3madkour-pub-citations-test--rewritten
      "Body [cite:@a;@b] tail.\n"
    (should (gethash "a" a3madkour-pub-citations--accumulator))
    (should (gethash "b" a3madkour-pub-citations--accumulator))
    (let ((a-entries (gethash "a" a3madkour-pub-citations--accumulator)))
      (should (equal "/fake/source.org" (caar a-entries))))))

(ert-deftest a3madkour-pub-citations-test/rewrite-fails-on-unknown-key ()
  "F Task 9: missing bib entry → fail-fast with source pointer."
  (a3madkour-pub-citations--accumulator-init)
  (a3madkour-pub-bib-test--with-bib "@misc{known, title={T}}"
    (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
               (lambda () nil)))
      (a3madkour-pub-citations-test--with-org "Body [cite:@nope] tail.\n"
        (let ((err (should-error
                    (a3madkour-pub-citations/rewrite-cite-keys-in-buffer
                     "/fake/source.org"))))
          (should (string-match-p "nope" (format "%s" err))))))))

(ert-deftest a3madkour-pub-citations-test/rewrite-fails-on-style-override ()
  "F Task 9: [cite/text:@k] signals an unsupported-form error."
  (a3madkour-pub-citations--accumulator-init)
  (a3madkour-pub-bib-test--with-bib "@misc{k, title={T}}"
    (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
               (lambda () nil)))
      (a3madkour-pub-citations-test--with-org "[cite/text:@k]"
        (let ((err (should-error
                    (a3madkour-pub-citations/rewrite-cite-keys-in-buffer
                     "/fake/source.org"))))
          (should (string-match-p "cite/style\\|not supported"
                                  (format "%s" err))))))))

(ert-deftest a3madkour-pub-citations-test/rewrite-fails-on-prefix-suffix ()
  "F Task 9: [cite:see @k] (prefix text) signals unsupported."
  (a3madkour-pub-citations--accumulator-init)
  (a3madkour-pub-bib-test--with-bib "@misc{k, title={T}}"
    (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
               (lambda () nil)))
      (a3madkour-pub-citations-test--with-org "[cite:see @k]"
        (should-error
         (a3madkour-pub-citations/rewrite-cite-keys-in-buffer
          "/fake/source.org"))))))

(ert-deftest a3madkour-pub-citations-test/rewrite-strips-print-bibliography ()
  "F Task 9: #+print_bibliography: lines are removed."
  (a3madkour-pub-citations--accumulator-init)
  (a3madkour-pub-bib-test--with-bib "@misc{k, title={T}}"
    (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
               (lambda () nil)))
      (a3madkour-pub-citations-test--with-org
          "Body [cite:@k]\n\n#+print_bibliography:\n"
        (a3madkour-pub-citations/rewrite-cite-keys-in-buffer "/fake/source.org")
        (goto-char (point-min))
        (should-not (search-forward "#+print_bibliography" nil t))))))

(ert-deftest a3madkour-pub-citations-test/rewrite-no-cites-is-noop ()
  "F Task 9: buffer without any [cite:] is unchanged."
  (a3madkour-pub-citations--accumulator-init)
  (a3madkour-pub-bib-test--with-bib ""
    (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
               (lambda () nil)))
      (a3madkour-pub-citations-test--with-org "Body without cites.\n"
        (let ((before (buffer-string)))
          (a3madkour-pub-citations/rewrite-cite-keys-in-buffer "/fake/source.org")
          (should (equal before (buffer-string))))))))

(ert-deftest a3madkour-pub-citations-test/rewrite-stops-on-first-error ()
  "F Task 9: when [cite:@nope1] and [cite:@nope2] both fail, the first one
stops the run (no second-error reporting)."
  (a3madkour-pub-citations--accumulator-init)
  (a3madkour-pub-bib-test--with-bib ""
    (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
               (lambda () nil)))
      (a3madkour-pub-citations-test--with-org "[cite:@nope1] [cite:@nope2]"
        (let ((err (should-error
                    (a3madkour-pub-citations/rewrite-cite-keys-in-buffer
                     "/fake/source.org"))))
          (should (string-match-p "nope1" (format "%s" err)))
          (should-not (string-match-p "nope2" (format "%s" err))))))))

(ert-deftest a3madkour-pub-citations-test/rewrite-preserves-non-cite-content ()
  "F Task 9: rewriter only touches [cite:...] forms; everything else is verbatim."
  (a3madkour-pub-citations-test--rewritten
      "* Heading\n\nA paragraph with [cite:@key1] inline.\n\nSecond paragraph.\n"
    (goto-char (point-min))
    (should (search-forward "Heading" nil t))
    (goto-char (point-min))
    (should (search-forward "Second paragraph" nil t))))

(ert-deftest a3madkour-pub-citations-test/rewrite-multiple-bare-cites ()
  "F Task 9: two separate [cite:@a] [cite:@b] sites both rewrite."
  (a3madkour-pub-citations-test--rewritten
      "First [cite:@a] middle [cite:@b] last.\n"
    (goto-char (point-min))
    (should (search-forward "@@hugo:{{< cite \"a\" >}}@@" nil t))
    (goto-char (point-min))
    (should (search-forward "@@hugo:{{< cite \"b\" >}}@@" nil t))))
```

- [ ] **Step 2: Run to verify failures**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "rewrite-|FAIL" | head -20`
Expected: all 11 new tests FAIL (`rewrite-cite-keys-in-buffer` undefined).

- [ ] **Step 3: Implement the rewriter**

Append to `a3madkour-publish-citations.el` BEFORE the `(provide ...)` line:

```elisp
;; ---------------------------------------------------------------------
;; rewrite-cite-keys-in-buffer (Task 9)
;; ---------------------------------------------------------------------

(defun a3madkour-pub-citations--shortcode-for-keys (keys)
  "Build `@@hugo:{{< cite \"k1\" >}}{{< cite \"k2\" >}}@@' for KEYS."
  (concat "@@hugo:"
          (mapconcat (lambda (k) (format "{{< cite \"%s\" >}}" k)) keys "")
          "@@"))

(defun a3madkour-pub-citations--source-line-of (pos source-file)
  "Compute the 1-indexed line number of POS for error messages.
SOURCE-FILE is included in the returned `FILE:LINE' string."
  (format "%s:%d"
          source-file
          (save-excursion
            (goto-char pos)
            (line-number-at-pos))))

(defun a3madkour-pub-citations--check-supported-form (cite source-file)
  "Signal if CITE uses style override, prefix, or suffix.  Returns t on OK."
  (let* ((style (org-element-property :style cite))
         (prefix (org-element-property :prefix cite))
         (suffix (org-element-property :suffix cite))
         (pos (org-element-property :begin cite))
         (loc (a3madkour-pub-citations--source-line-of pos source-file)))
    (cond
     ((and style (not (string-empty-p style)))
      (error "%s: cite/style not supported in V1: [cite/%s:...]\n  hint: V1 supports [cite:@key] and [cite:@k1;@k2]. Style overrides, prefix, and suffix are tracked as F-follow-up work; see docs/superpowers/specs/2026-06-01-phase-3-f-citation-pipeline-design.md §1 non-goals."
             loc style))
     ((or (and prefix (not (string-empty-p (org-element-interpret-data prefix))))
          (and suffix (not (string-empty-p (org-element-interpret-data suffix)))))
      (error "%s: cite prefix/suffix not supported in V1\n  hint: V1 supports [cite:@key] and [cite:@k1;@k2]. Style overrides, prefix, and suffix are tracked as F-follow-up work."
             loc)))
    t))

(defun a3madkour-pub-citations--strip-print-bibliography ()
  "Remove any `#+print_bibliography:' line from the current buffer."
  (save-excursion
    (goto-char (point-min))
    (while (re-search-forward "^\\s-*#\\+print_bibliography:.*$" nil t)
      (replace-match "" nil t))))

(defun a3madkour-pub-citations/rewrite-cite-keys-in-buffer (source-file)
  "Walk current buffer for [cite:...] forms; rewrite each to
`@@hugo:{{< cite \"k\" >}}@@'; populate the run accumulator.
SOURCE-FILE is the original path, used for error messages and
accumulator provenance.  Fail-fast on the first error."
  (unless a3madkour-pub-citations--accumulator
    (a3madkour-pub-citations--accumulator-init))
  (a3madkour-pub-citations--strip-print-bibliography)
  ;; Collect citation elements with their begin/end positions, then rewrite
  ;; back-to-front so earlier rewrites don't shift later positions.
  (let* ((tree (org-element-parse-buffer))
         (cites
          (org-element-map tree 'citation
            (lambda (cite)
              (let ((begin (org-element-property :begin cite))
                    (end   (org-element-property :end   cite)))
                (list :cite cite :begin begin :end end))))))
    (dolist (info (nreverse cites))
      (let* ((cite   (plist-get info :cite))
             (begin  (plist-get info :begin))
             (end    (plist-get info :end))
             (_      (a3madkour-pub-citations--check-supported-form cite source-file))
             (keys
              (org-element-map cite 'citation-reference
                (lambda (ref) (org-element-property :key ref)))))
        ;; Validate each key resolves; fail-fast on first nil.
        (dolist (k keys)
          (unless (a3madkour-pub-bib/resolve k)
            (error "%s: cite key %s not found in library.bib"
                   (a3madkour-pub-citations--source-line-of begin source-file)
                   k)))
        ;; Accumulate.
        (dolist (k keys)
          (let ((current (gethash k a3madkour-pub-citations--accumulator)))
            (puthash k (cons (cons source-file begin) current)
                     a3madkour-pub-citations--accumulator)))
        ;; Replace [cite:...] span with the shortcode wrapper.  The
        ;; org-element `end' property includes trailing whitespace; trim
        ;; back to just past the closing `]'.
        (save-excursion
          (goto-char end)
          (skip-chars-backward " \t\n\r")
          (let ((replace-end (point)))
            (delete-region begin replace-end)
            (goto-char begin)
            (insert (a3madkour-pub-citations--shortcode-for-keys keys))))))))
```

- [ ] **Step 4: Re-run all tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-citations|FAIL|Ran [0-9]+" | head -25`
Expected: 18 `a3madkour-pub-citations` tests pass (7 Task 8 + 11 Task 9).

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el
git commit -m "$(cat <<'EOF'
feat(f): citation rewriter + accumulator (Task 9)

rewrite-cite-keys-in-buffer walks org-element citation tree back-to-front,
fails fast on unknown keys / style overrides / prefix-suffix forms,
emits @@hugo:{{< cite "k" >}}@@ shortcodes (one per multi-cite member),
strips #+print_bibliography: directives, and populates the run
accumulator with source-file provenance.  11 new ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10 — `cite--lookup-notes-ref`: ref-note auto-detect

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el`

- [ ] **Step 1: Confirm prerequisite — manifest snapshot defvar**

This task assumes A.1.d's `a3madkour-pub--manifest-snapshot` defvar exists (per spec §6 "manifest-backed, not filesystem-backed"). Verify with:

Run: `grep -n "manifest-snapshot" /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
Expected: at least one match (the defvar is what B's per-handler `record-publish` consumes).

If the defvar isn't named exactly `a3madkour-pub--manifest-snapshot`, substitute the actual name in subsequent code below.

- [ ] **Step 2: Write 5 failing tests**

Append to `a3madkour-publish-citations-test.el` before its `(provide ...)`:

```elisp
;; -- Task 10: cite--lookup-notes-ref --

(defmacro a3madkour-pub-citations-test--with-manifest (manifest-alist &rest body)
  "Let-bind the manifest snapshot defvar to MANIFEST-ALIST and run BODY."
  (declare (indent 1))
  `(let ((a3madkour-pub--manifest-snapshot ,manifest-alist))
     ,@body))

(defmacro a3madkour-pub-citations-test--with-ref-note-dir (specs &rest body)
  "SPECS is an alist of (KEY-SYMBOL . PROPERTY-STRINGS).  Create a temp
ref-notes directory with one .org file per key; let-bind the F ref-notes
dir to it; run BODY."
  (declare (indent 1))
  `(let ((tmp (make-temp-file "a3-pub-ref-notes-" t)))
     (unwind-protect
         (progn
           (dolist (spec ,specs)
             (let* ((key (car spec))
                    (props (cdr spec))
                    (path (expand-file-name
                           (format "%s.org" key) tmp)))
               (with-temp-file path
                 (insert props))))
           (let ((a3madkour-pub-citations--ref-notes-dir
                  (file-name-as-directory tmp)))
             ,@body))
       (delete-directory tmp t))))

(ert-deftest a3madkour-pub-citations-test/notes-ref-absent-returns-nil ()
  "F Task 10: no ref-note file → nil."
  (a3madkour-pub-citations-test--with-ref-note-dir nil
    (a3madkour-pub-citations-test--with-manifest nil
      (should-not (a3madkour-pub-citations--lookup-notes-ref "abc")))))

(ert-deftest a3madkour-pub-citations-test/notes-ref-unpublished-returns-nil ()
  "F Task 10: ref-note exists but HUGO_PUBLISH is missing → nil."
  (a3madkour-pub-citations-test--with-ref-note-dir
      '(("myKey2020" . "#+HUGO_SECTION: garden\n#+title: T\n"))
    (a3madkour-pub-citations-test--with-manifest nil
      (should-not (a3madkour-pub-citations--lookup-notes-ref "myKey2020")))))

(ert-deftest a3madkour-pub-citations-test/notes-ref-wrong-section-returns-nil ()
  "F Task 10: ref-note has HUGO_SECTION other than garden → nil."
  (a3madkour-pub-citations-test--with-ref-note-dir
      '(("myKey2020" .
         "#+HUGO_PUBLISH: t\n#+HUGO_SECTION: essays\n#+title: T\n"))
    (a3madkour-pub-citations-test--with-manifest nil
      (should-not (a3madkour-pub-citations--lookup-notes-ref "myKey2020")))))

(ert-deftest a3madkour-pub-citations-test/notes-ref-not-in-manifest-returns-nil ()
  "F Task 10: ref-note is published but not in the manifest snapshot → nil."
  (a3madkour-pub-citations-test--with-ref-note-dir
      '(("myKey2020" .
         "#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n#+title: T\n"))
    (a3madkour-pub-citations-test--with-manifest
        '((notes . [((id . "id-x")
                     (current_url . "/garden/some-other/")
                     (state . "live"))]))
      (should-not (a3madkour-pub-citations--lookup-notes-ref "myKey2020")))))

(ert-deftest a3madkour-pub-citations-test/notes-ref-happy-path-returns-slug ()
  "F Task 10: ref-note published AND in manifest under /garden/<slug>/ →
returns <slug> string."
  (a3madkour-pub-citations-test--with-ref-note-dir
      '(("myKey2020" .
         "#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n#+title: My Key\n"))
    (a3madkour-pub-citations-test--with-manifest
        '((notes . [((id . "id-key")
                     (current_url . "/garden/mykey2020/")
                     (state . "live"))]))
      (should (equal "mykey2020"
                     (a3madkour-pub-citations--lookup-notes-ref "myKey2020"))))))
```

- [ ] **Step 3: Run to verify failures**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "notes-ref|FAIL" | head -10`
Expected: 5 new tests FAIL (`lookup-notes-ref` undefined).

- [ ] **Step 4: Implement the lookup**

Append to `a3madkour-publish-citations.el` BEFORE the `(provide ...)` line:

```elisp
;; ---------------------------------------------------------------------
;; cite--lookup-notes-ref: manifest-backed ref-note auto-detect (Task 10)
;; ---------------------------------------------------------------------

(defcustom a3madkour-pub-citations--ref-notes-dir
  (expand-file-name "~/org/notes/ref-notes/")
  "Directory holding per-cite-key reference org notes.  For a cite key
KEY, F probes for `<ref-notes-dir>/<KEY>.org' to auto-populate the
:notes_ref yaml field."
  :type 'directory
  :group 'a3madkour-pub)

(defun a3madkour-pub-citations--read-keyword (file keyword)
  "Read first `#+<KEYWORD>: <VALUE>' line from FILE; return VALUE or nil."
  (with-temp-buffer
    (insert-file-contents file nil 0 4096)  ; first 4KB is enough for keywords
    (goto-char (point-min))
    (when (re-search-forward
           (format "^#\\+%s:[ \t]*\\(.*\\)$" (upcase keyword)) nil t)
      (string-trim (match-string 1)))))

(defun a3madkour-pub-citations--manifest-slug-for-garden-url (manifest url)
  "Search MANIFEST (the snapshot alist) for an entry whose current_url
equals URL; return its slug (the path component between /garden/ and /),
or nil if not found."
  (let ((notes (alist-get 'notes manifest)))
    (cl-some
     (lambda (note-alist)
       (let ((cur-url (alist-get 'current_url note-alist))
             (state   (alist-get 'state       note-alist)))
         (and (equal cur-url url)
              (equal state "live")
              (when (string-match "\\`/garden/\\([^/]+\\)/\\'" cur-url)
                (match-string 1 cur-url)))))
     ;; alist-get may return vector or list; coerce to list.
     (if (vectorp notes) (append notes nil) notes))))

(defun a3madkour-pub-citations--lookup-notes-ref (cite-key)
  "If a ref-note exists for CITE-KEY, is published as garden, and resolves
in the manifest snapshot, return its garden slug.  Otherwise nil."
  (let ((path (expand-file-name
               (format "%s.org" cite-key)
               a3madkour-pub-citations--ref-notes-dir)))
    (when (file-exists-p path)
      (let ((publish (a3madkour-pub-citations--read-keyword path "HUGO_PUBLISH"))
            (section (a3madkour-pub-citations--read-keyword path "HUGO_SECTION"))
            (slug-override (a3madkour-pub-citations--read-keyword path "HUGO_SLUG")))
        (when (and (equal publish "t")
                   (equal section "garden"))
          (let* ((default-slug (or slug-override
                                   (downcase
                                    (file-name-base path))))
                 (url (format "/garden/%s/" default-slug)))
            (a3madkour-pub-citations--manifest-slug-for-garden-url
             (and (boundp 'a3madkour-pub--manifest-snapshot)
                  a3madkour-pub--manifest-snapshot)
             url)))))))
```

- [ ] **Step 5: Re-run all tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-citations|FAIL|Ran [0-9]+" | head -30`
Expected: 23 `a3madkour-pub-citations` tests pass.

- [ ] **Step 6: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el
git commit -m "$(cat <<'EOF'
feat(f): notes_ref auto-detect via manifest snapshot (Task 10)

For each cite-key, probe ~/org/notes/ref-notes/<KEY>.org; require
HUGO_PUBLISH=t AND HUGO_SECTION=garden; resolve through the
manifest snapshot (A.1.d) to obtain the garden URL slug.  Silent on
miss (queued/draft ref-notes are normal state).  5 new ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11 — `cite-emit-yaml`: merge + atomic write

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el`

- [ ] **Step 1: Write 8 failing tests**

Append to `a3madkour-publish-citations-test.el` before its `(provide ...)`:

```elisp
;; -- Task 11: cite-emit-yaml --

(defmacro a3madkour-pub-citations-test--with-yaml-dir (&rest body)
  "Set up a temp site root with data/ subdir; let-bind a3madkour-pub/site-data-dir."
  (declare (indent 0))
  `(let* ((tmp-root (make-temp-file "a3-pub-citations-" t))
          (tmp-data (expand-file-name "data/" tmp-root)))
     (make-directory tmp-data t)
     (unwind-protect
         (let ((a3madkour-pub/site-data-dir tmp-data))
           ,@body)
       (delete-directory tmp-root t))))

(ert-deftest a3madkour-pub-citations-test/emit-writes-yaml-for-cited-keys ()
  "F Task 11: emit-yaml writes data/citations.yaml with each accumulated key."
  (a3madkour-pub-citations-test--with-yaml-dir
    (a3madkour-pub-bib-test--with-bib
        "@misc{a, author={A,A}, title={T-A}, date={2020}, publisher={P}}"
      (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil)))
        (a3madkour-pub-citations--accumulator-init)
        (puthash "a" '(("/fake/x.org" . 1)) a3madkour-pub-citations--accumulator)
        (a3madkour-pub-citations/emit-yaml)
        (let ((yaml-text (with-temp-buffer
                           (insert-file-contents
                            (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir))
                           (buffer-string))))
          (should (string-match-p "^citations:" yaml-text))
          (should (string-match-p "  a:" yaml-text))
          (should (string-match-p "title: \"T-A\"" yaml-text)))))))

(ert-deftest a3madkour-pub-citations-test/emit-merges-with-existing ()
  "F Task 11: pre-existing keys NOT in accumulator survive untouched."
  (a3madkour-pub-citations-test--with-yaml-dir
    (let ((existing (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir)))
      (with-temp-file existing
        (insert "citations:\n  preexisting:\n    authors: [\"X, Y\"]\n"
                "    year: 2010\n    title: \"Old\"\n    venue: \"V\"\n"))
      (a3madkour-pub-bib-test--with-bib
          "@misc{newkey, author={A,A}, title={NT}, date={2020}, publisher={P}}"
        (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil)))
          (a3madkour-pub-citations--accumulator-init)
          (puthash "newkey" '(("/fake/x.org" . 1))
                   a3madkour-pub-citations--accumulator)
          (a3madkour-pub-citations/emit-yaml)
          (let ((yaml-text (with-temp-buffer
                             (insert-file-contents existing)
                             (buffer-string))))
            (should (string-match-p "  preexisting:" yaml-text))
            (should (string-match-p "  newkey:" yaml-text))))))))

(ert-deftest a3madkour-pub-citations-test/emit-sorted-by-key ()
  "F Task 11: keys in output are sorted lexicographically for deterministic diffs."
  (a3madkour-pub-citations-test--with-yaml-dir
    (a3madkour-pub-bib-test--with-bib
        "@misc{zeta, author={A,A}, title={Z}, date={2020}, publisher={P}}
@misc{alpha, author={A,A}, title={A}, date={2020}, publisher={P}}
@misc{mu, author={A,A}, title={M}, date={2020}, publisher={P}}"
      (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil)))
        (a3madkour-pub-citations--accumulator-init)
        (dolist (k '("zeta" "alpha" "mu"))
          (puthash k '(("/x.org" . 1)) a3madkour-pub-citations--accumulator))
        (a3madkour-pub-citations/emit-yaml)
        (let* ((yaml-text (with-temp-buffer
                            (insert-file-contents
                             (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir))
                            (buffer-string)))
               (a-pos    (string-match "^  alpha:" yaml-text))
               (m-pos    (string-match "^  mu:"    yaml-text))
               (z-pos    (string-match "^  zeta:"  yaml-text)))
          (should (and a-pos m-pos z-pos))
          (should (< a-pos m-pos))
          (should (< m-pos z-pos)))))))

(ert-deftest a3madkour-pub-citations-test/emit-idempotent ()
  "F Task 11: re-running emit-yaml with same accumulator yields identical bytes."
  (a3madkour-pub-citations-test--with-yaml-dir
    (a3madkour-pub-bib-test--with-bib
        "@misc{k, author={A,A}, title={T}, date={2020}, publisher={P}}"
      (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil)))
        (a3madkour-pub-citations--accumulator-init)
        (puthash "k" '(("/x.org" . 1)) a3madkour-pub-citations--accumulator)
        (a3madkour-pub-citations/emit-yaml)
        (let ((first (with-temp-buffer
                       (insert-file-contents
                        (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir))
                       (buffer-string))))
          (a3madkour-pub-citations/emit-yaml)
          (let ((second (with-temp-buffer
                          (insert-file-contents
                           (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir))
                          (buffer-string))))
            (should (equal first second))))))))

(ert-deftest a3madkour-pub-citations-test/emit-empty-accumulator-noop ()
  "F Task 11: empty accumulator does NOT write or modify the yaml."
  (a3madkour-pub-citations-test--with-yaml-dir
    (let ((existing (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir)))
      (with-temp-file existing (insert "citations:\n  k:\n    authors: [\"X\"]\n"))
      (let ((before (with-temp-buffer (insert-file-contents existing) (buffer-string))))
        (a3madkour-pub-citations--accumulator-init)
        (a3madkour-pub-citations/emit-yaml)
        (let ((after (with-temp-buffer (insert-file-contents existing) (buffer-string))))
          (should (equal before after)))))))

(ert-deftest a3madkour-pub-citations-test/emit-fails-on-missing-required-field ()
  "F Task 11: bib entry without title fails-fast at emit."
  (a3madkour-pub-citations-test--with-yaml-dir
    (a3madkour-pub-bib-test--with-bib
        "@misc{k, author={A,A}, date={2020}, publisher={P}}"
      (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil)))
        (a3madkour-pub-citations--accumulator-init)
        (puthash "k" '(("/x.org" . 1)) a3madkour-pub-citations--accumulator)
        (let ((err (should-error (a3madkour-pub-citations/emit-yaml))))
          (should (string-match-p "title\\|required" (format "%s" err))))))))

(ert-deftest a3madkour-pub-citations-test/emit-replace-purge-mode ()
  "F Task 11: emit-yaml with :mode 'replace drops keys not in accumulator."
  (a3madkour-pub-citations-test--with-yaml-dir
    (let ((existing (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir)))
      (with-temp-file existing
        (insert "citations:\n  stale:\n    authors: [\"X\"]\n"
                "    year: 2010\n    title: \"S\"\n    venue: \"V\"\n"))
      (a3madkour-pub-bib-test--with-bib
          "@misc{kept, author={A,A}, title={K}, date={2020}, publisher={P}}"
        (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil)))
          (a3madkour-pub-citations--accumulator-init)
          (puthash "kept" '(("/x.org" . 1)) a3madkour-pub-citations--accumulator)
          (a3madkour-pub-citations/emit-yaml :mode 'replace)
          (let ((yaml-text (with-temp-buffer
                             (insert-file-contents existing) (buffer-string))))
            (should     (string-match-p "  kept:"  yaml-text))
            (should-not (string-match-p "  stale:" yaml-text))))))))

(ert-deftest a3madkour-pub-citations-test/emit-uses-tmp-rename ()
  "F Task 11: write goes via .tmp file (atomicity)."
  (a3madkour-pub-citations-test--with-yaml-dir
    (a3madkour-pub-bib-test--with-bib
        "@misc{k, author={A,A}, title={T}, date={2020}, publisher={P}}"
      (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil)))
        (let ((calls nil))
          (cl-letf (((symbol-function 'rename-file)
                     (lambda (from to &optional ok-overwrite)
                       (push (cons from to) calls))))
            (a3madkour-pub-citations--accumulator-init)
            (puthash "k" '(("/x.org" . 1)) a3madkour-pub-citations--accumulator)
            (a3madkour-pub-citations/emit-yaml)
            (should (cl-some (lambda (pair) (string-match-p "\\.tmp\\'" (car pair)))
                             calls))))))))
```

- [ ] **Step 2: Run to verify failures**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "emit-|FAIL" | head -15`
Expected: 8 new tests FAIL (`emit-yaml` undefined; `site-data-dir` may already be defined by B's modules).

- [ ] **Step 3: Verify `site-data-dir` defvar already exists**

Run: `grep -n "site-data-dir" /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`
Expected: at least one match. (`a3madkour-pub/site-data-dir` was added in B.0.)

- [ ] **Step 4: Implement `emit-yaml`**

Append to `a3madkour-publish-citations.el` BEFORE the `(provide ...)` line:

```elisp
;; ---------------------------------------------------------------------
;; cite-emit-yaml: merge / replace into data/citations.yaml (Task 11)
;; ---------------------------------------------------------------------

(defconst a3madkour-pub-citations--required-fields
  '(:authors :year :title :venue)
  "Yaml fields that MUST be non-nil for a citation entry to be valid.")

(defun a3madkour-pub-citations--yaml-escape (s)
  "Escape S for embedding in a double-quoted yaml scalar (basic)."
  (let ((out (replace-regexp-in-string "\\\\" "\\\\\\\\" s)))
    (replace-regexp-in-string "\"" "\\\\\"" out)))

(defun a3madkour-pub-citations--yaml-format-value (key val)
  "Format VAL for yaml.  KEY is the plist key (used for :authors list shape)."
  (cond
   ((eq key :authors)
    (concat "[" (mapconcat
                 (lambda (a) (format "\"%s\""
                                     (a3madkour-pub-citations--yaml-escape a)))
                 val ", ") "]"))
   ((eq key :year) (format "%d" val))
   ((stringp val)  (format "\"%s\"" (a3madkour-pub-citations--yaml-escape val)))
   (t              (format "%s" val))))

(defconst a3madkour-pub-citations--yaml-key-order
  '(:authors :year :title :venue :url :doi :publisher :volume
    :issue :pages :isbn :type :notes_ref))

(defun a3madkour-pub-citations--render-entry (key entry)
  "Render `<key>: ...' yaml block for ENTRY plist."
  (with-output-to-string
    (princ (format "  %s:\n" key))
    (dolist (k a3madkour-pub-citations--yaml-key-order)
      (let ((v (plist-get entry k)))
        (when (and v (not (and (listp v) (null v))))
          (let ((field-name (substring (symbol-name k) 1)))
            (princ (format "    %s: %s\n"
                           field-name
                           (a3madkour-pub-citations--yaml-format-value k v)))))))))

(defun a3madkour-pub-citations--parse-existing-yaml (path)
  "Read PATH and return an alist (KEY . RAW-ENTRY-STRING) of citation
blocks.  Lightweight parse: each `  <key>:' header starts a block; the
block ends at the next `  <key>:' or EOF."
  (when (file-exists-p path)
    (with-temp-buffer
      (insert-file-contents path)
      (goto-char (point-min))
      (let ((entries nil)
            current-key
            block-start)
        (while (re-search-forward "^  \\([A-Za-z0-9][A-Za-z0-9-]*\\):\\s-*$"
                                  nil t)
          (when current-key
            (let ((blk (string-trim-right
                        (buffer-substring-no-properties
                         block-start (match-beginning 0))
                        "\n+")))
              (push (cons current-key blk) entries)))
          (setq current-key (match-string-no-properties 1)
                block-start (match-beginning 0)))
        (when current-key
          (let ((blk (string-trim-right
                      (buffer-substring-no-properties block-start (point-max))
                      "\n+")))
            (push (cons current-key blk) entries)))
        (nreverse entries)))))

(defun a3madkour-pub-citations--validate-entry (key entry)
  "Signal if ENTRY is missing any required field."
  (dolist (req a3madkour-pub-citations--required-fields)
    (unless (plist-get entry req)
      (error "%s: bib entry missing required field %s"
             key (substring (symbol-name req) 1)))))

(cl-defun a3madkour-pub-citations/emit-yaml (&key (mode 'merge))
  "Write `data/citations.yaml' from the accumulator.

MODE: `'merge' (default) keeps existing keys not in the accumulator.
      `'replace' drops keys not in the accumulator (sync command path).

Skips file write entirely if the accumulator is empty and MODE is merge."
  (unless a3madkour-pub-citations--accumulator
    (a3madkour-pub-citations--accumulator-init))
  (let ((acc-keys (sort (let (keys)
                          (maphash (lambda (k _) (push k keys))
                                   a3madkour-pub-citations--accumulator)
                          keys)
                        #'string-lessp)))
    (when (or acc-keys (eq mode 'replace))
      (let* ((yaml-path (expand-file-name "citations.yaml"
                                          a3madkour-pub/site-data-dir))
             (tmp-path  (concat yaml-path ".tmp"))
             (existing  (a3madkour-pub-citations--parse-existing-yaml yaml-path))
             ;; New-from-accumulator entries (plists)
             (new-rendered
              (mapcar
               (lambda (k)
                 (let ((entry (a3madkour-pub-bib/resolve k)))
                   (a3madkour-pub-citations--validate-entry k entry)
                   ;; Attach notes_ref if auto-detect resolves.
                   (let ((nref (a3madkour-pub-citations--lookup-notes-ref k)))
                     (when nref
                       (setq entry (plist-put entry :notes_ref nref))))
                   (cons k (a3madkour-pub-citations--render-entry k entry))))
               acc-keys))
             ;; Final entries: per-MODE merge with existing.
             (final
              (cond
               ((eq mode 'replace) new-rendered)
               (t
                (let* ((carry
                        (cl-remove-if
                         (lambda (pair) (assoc (car pair) new-rendered))
                         existing))
                       (merged (append new-rendered carry)))
                  (sort merged
                        (lambda (a b) (string-lessp (car a) (car b)))))))))
        (with-temp-file tmp-path
          (insert "citations:\n")
          (dolist (pair final)
            (insert (cdr pair) "\n")))
        (rename-file tmp-path yaml-path t)))))
```

- [ ] **Step 5: Re-run all tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-citations|FAIL|Ran [0-9]+" | head -35`
Expected: 31 `a3madkour-pub-citations` tests pass (7 + 11 + 5 + 8).

- [ ] **Step 6: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el
git commit -m "$(cat <<'EOF'
feat(f): cite-emit-yaml merge + replace modes (Task 11)

emit-yaml renders accumulator entries to data/citations.yaml via
atomic .tmp+rename.  Merge mode preserves untouched keys (per-publish
default).  Replace mode purges (a3-sync-citations only).  Output is
sorted by key.  Fails-fast on required field missing; idempotent
re-run.  8 new ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12 — Wire rewriter into `rewrite-to-tmp-file`

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el:381-410` (`rewrite-to-tmp-file`)
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el`

- [ ] **Step 1: Write 1 failing test**

Append to `a3madkour-publish-rewrite-test.el` before its `(provide ...)`:

```elisp
;; -- F Task 12: rewrite-to-tmp-file also runs cite rewriter --

(ert-deftest a3madkour-pub-rewrite-test/tmp-file-runs-cite-rewriter ()
  "F Task 12: rewrite-to-tmp-file calls the citation rewriter, so the
written tmp file contains the @@hugo: shortcode in place of [cite:@k]."
  (require 'a3madkour-publish-citations)
  (let* ((src (make-temp-file "rewrite-cite-" nil ".org"))
         tmp)
    (unwind-protect
        (progn
          (with-temp-file src
            (insert "* H\nBody [cite:@k1] tail.\n"))
          (a3madkour-pub-bib-test--with-bib
              "@misc{k1, author={A,A}, title={T}, date={2020}, publisher={P}}"
            (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p)
                       (lambda () nil))
                      ;; Stub id-link rewriter: just return the buffer string unchanged.
                      ((symbol-function 'a3madkour-pub-rewrite/rewrite-buffer-links)
                       (lambda (&rest _) nil)))
              (a3madkour-pub-citations--accumulator-init)
              (setq tmp (a3madkour-pub-rewrite/rewrite-to-tmp-file src "id-x"))
              (let ((written (with-temp-buffer
                               (insert-file-contents tmp)
                               (buffer-string))))
                (should (string-match-p "@@hugo:{{< cite \"k1\" >}}@@" written))
                (should-not (string-match-p "\\[cite:" written))))))
      (when tmp (delete-file tmp))
      (delete-file src))))
```

- [ ] **Step 2: Run to verify failure**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "tmp-file-runs-cite|FAIL" | head -5`
Expected: FAIL (citations rewriter not yet called).

- [ ] **Step 3: Wire the rewriter**

Update `a3madkour-publish-rewrite.el:381-414` (`rewrite-to-tmp-file`). Locate the existing `with-temp-buffer` block:

```elisp
          (with-temp-buffer
            (insert-file-contents source-file)
            (setq warnings
                  (a3madkour-pub-rewrite/rewrite-buffer-links source-note-id))
            (write-region (point-min) (point-max) tmp nil 'quiet))
```

Replace with:

```elisp
          (with-temp-buffer
            (insert-file-contents source-file)
            (setq warnings
                  (a3madkour-pub-rewrite/rewrite-buffer-links source-note-id))
            ;; F Task 12: cite-key rewrite runs in the same pre-export pass.
            ;; Loaded lazily so non-F-aware tests of rewrite-to-tmp-file still
            ;; work; the citations module is part of a3-pub.sh's `-l' list
            ;; in publish-living / publish-deliberate / sync exec blocks.
            (when (require 'a3madkour-publish-citations nil 'noerror)
              (a3madkour-pub-citations/rewrite-cite-keys-in-buffer source-file))
            (write-region (point-min) (point-max) tmp nil 'quiet))
```

- [ ] **Step 4: Re-run tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "tmp-file|Ran [0-9]+|FAIL" | head -15`
Expected: new test PASS; pre-existing `rewrite-to-tmp-file-*` tests still PASS (they don't contain `[cite:@...]` so the rewriter is a no-op on them).

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el
git commit -m "$(cat <<'EOF'
feat(f): rewrite-to-tmp-file runs cite-key rewriter (Task 12)

Single chokepoint plug: rewrite-to-tmp-file now invokes F's
rewrite-cite-keys-in-buffer right after B.1.1's link rewriter.
All page-bundle handlers (garden/essays/research) inherit cite
rewriting for free.  Library handler doesn't use this entry point,
so library rows are unaffected.  1 new ert test.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13 — Wire `emit-yaml` tail call into living + deliberate

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el` (or wherever living's tests live)

- [ ] **Step 1: Locate the finish-publish call in each module**

Run: `grep -n "finish-publish" /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate.el`
Note both line numbers.

- [ ] **Step 2: Add the tail call AFTER finish-publish in both files**

In `a3madkour-publish-living.el`, AFTER the `(a3madkour-pub/finish-publish)` line in `a3-publish-living`, add:

```elisp
    ;; F Task 13: flush accumulated cite-keys to data/citations.yaml.
    (when (require 'a3madkour-publish-citations nil 'noerror)
      (a3madkour-pub-citations/emit-yaml :mode 'merge))
```

In `a3madkour-publish-deliberate.el`, AFTER `(a3madkour-pub/finish-publish :scope 'deliberate)` in `a3-publish-deliberate`, add the same block.

- [ ] **Step 3: Write 1 integration-style ert test**

Append to `a3madkour-publish-deliberate-test.el` before its `(provide ...)`:

```elisp
;; -- F Task 13: deliberate triggers cite emit-yaml --

(ert-deftest a3madkour-pub-deliberate-test/citations-emit-fires-after-finish ()
  "F Task 13: a3-publish-deliberate calls emit-yaml after finish-publish.
Stub finish-publish + emit-yaml; assert call order: finish-publish first,
then emit-yaml."
  (let ((calls nil))
    (cl-letf (((symbol-function 'a3madkour-pub/begin-publish) (lambda () nil))
              ((symbol-function 'a3madkour-pub/finish-publish)
               (lambda (&rest _) (push 'finish calls)))
              ((symbol-function 'a3madkour-pub-citations/emit-yaml)
               (lambda (&rest _) (push 'emit calls)))
              ((symbol-function 'a3madkour-pub-deliberate--dispatch)
               (lambda (&rest _) nil))
              ((symbol-function 'a3madkour-pub/note-section) (lambda (_) 'essays))
              ;; Ensure the require call succeeds (module already loaded by the test runner).
              ((symbol-function 'require)
               (lambda (feat &rest _) (or (memq feat features) t))))
      (a3-publish-deliberate "/fake/file.org")
      (should (equal (reverse calls) '(finish emit))))))
```

- [ ] **Step 4: Run the test**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "citations-emit-fires|FAIL|Ran [0-9]+" | head -10`
Expected: PASS; total ert count grew by 1.

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-deliberate-test.el
git commit -m "$(cat <<'EOF'
feat(f): living + deliberate flush cite accumulator (Task 13)

Both top-level commands tail-call emit-yaml after finish-publish.
Merge mode keeps unrelated cite keys untouched.  Ordering test pins
finish-publish before emit-yaml.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14 — BBT JSON-RPC client

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el`

- [ ] **Step 1: Write 5 failing tests**

Append to `a3madkour-publish-bib-test.el` before its `(provide ...)`:

```elisp
;; -- Task 14: BBT JSON-RPC client --

(ert-deftest a3madkour-pub-bib-test/refresh-disabled-when-endpoint-nil ()
  "F Task 14: bbt-endpoint=nil disables refresh; returns nil; no HTTP call."
  (let ((a3madkour-pub-bib/bbt-endpoint nil)
        (calls 0))
    (cl-letf (((symbol-function 'url-retrieve-synchronously)
               (lambda (&rest _) (setq calls (1+ calls)) nil)))
      (should-not (a3madkour-pub-bib/refresh-from-zotero))
      (should (= 0 calls)))))

(ert-deftest a3madkour-pub-bib-test/refresh-200-writes-file ()
  "F Task 14: 200 response with valid body atomic-writes the .bib path."
  (let* ((tmp-bib (make-temp-file "f-bbt-" nil ".bib"))
         (a3madkour-pub-bib/library-path tmp-bib)
         (a3madkour-pub-bib/bbt-endpoint "http://localhost:23119/x"))
    (unwind-protect
        (cl-letf (((symbol-function 'url-retrieve-synchronously)
                   (lambda (&rest _)
                     (with-current-buffer (generate-new-buffer "*bbt-mock*")
                       (insert "HTTP/1.1 200 OK\r\n"
                               "Content-Type: application/json\r\n\r\n"
                               "{\"jsonrpc\":\"2.0\",\"result\":\"@article{ok, title={T}}\\n\"}")
                       (current-buffer)))))
          (should (a3madkour-pub-bib/refresh-from-zotero))
          (let ((written (with-temp-buffer
                           (insert-file-contents tmp-bib) (buffer-string))))
            (should (string-match-p "@article{ok" written))))
      (when (file-exists-p tmp-bib) (delete-file tmp-bib)))))

(ert-deftest a3madkour-pub-bib-test/refresh-non-200-warns-and-returns-nil ()
  "F Task 14: non-2xx response returns nil without writing the .bib."
  (let* ((tmp-bib (make-temp-file "f-bbt-" nil ".bib"))
         (a3madkour-pub-bib/library-path tmp-bib)
         (a3madkour-pub-bib/bbt-endpoint "http://localhost:23119/x"))
    (with-temp-file tmp-bib (insert "@misc{original, title={Orig}}"))
    (unwind-protect
        (cl-letf (((symbol-function 'url-retrieve-synchronously)
                   (lambda (&rest _)
                     (with-current-buffer (generate-new-buffer "*bbt-mock*")
                       (insert "HTTP/1.1 503 Service Unavailable\r\n\r\n{}")
                       (current-buffer)))))
          (should-not (a3madkour-pub-bib/refresh-from-zotero))
          (let ((post (with-temp-buffer
                        (insert-file-contents tmp-bib) (buffer-string))))
            (should (string-match-p "original" post))))
      (when (file-exists-p tmp-bib) (delete-file tmp-bib)))))

(ert-deftest a3madkour-pub-bib-test/refresh-connection-refused-returns-nil ()
  "F Task 14: ECONNREFUSED (url-retrieve-synchronously signals or returns nil)."
  (let ((a3madkour-pub-bib/library-path
         (make-temp-file "f-bbt-" nil ".bib"))
        (a3madkour-pub-bib/bbt-endpoint "http://localhost:23119/x"))
    (unwind-protect
        (cl-letf (((symbol-function 'url-retrieve-synchronously)
                   (lambda (&rest _)
                     (signal 'file-error '("Connection refused")))))
          (should-not (a3madkour-pub-bib/refresh-from-zotero)))
      (when (file-exists-p a3madkour-pub-bib/library-path)
        (delete-file a3madkour-pub-bib/library-path)))))

(ert-deftest a3madkour-pub-bib-test/refresh-malformed-json-returns-nil ()
  "F Task 14: 200 with garbage body returns nil without writing."
  (let* ((tmp-bib (make-temp-file "f-bbt-" nil ".bib"))
         (a3madkour-pub-bib/library-path tmp-bib)
         (a3madkour-pub-bib/bbt-endpoint "http://localhost:23119/x"))
    (with-temp-file tmp-bib (insert "@misc{original, title={Orig}}"))
    (unwind-protect
        (cl-letf (((symbol-function 'url-retrieve-synchronously)
                   (lambda (&rest _)
                     (with-current-buffer (generate-new-buffer "*bbt-mock*")
                       (insert "HTTP/1.1 200 OK\r\n\r\nNOT VALID JSON")
                       (current-buffer)))))
          (should-not (a3madkour-pub-bib/refresh-from-zotero))
          (let ((post (with-temp-buffer
                        (insert-file-contents tmp-bib) (buffer-string))))
            (should (string-match-p "original" post))))
      (when (file-exists-p tmp-bib) (delete-file tmp-bib)))))
```

- [ ] **Step 2: Run to verify failures**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "refresh-|FAIL" | head -10`
Expected: 5 new tests FAIL (`refresh-from-zotero` undefined).

- [ ] **Step 3: Implement the BBT client**

Append to `a3madkour-publish-bib.el` BEFORE the `(provide ...)` line:

```elisp
;; ---------------------------------------------------------------------
;; BBT JSON-RPC client (Task 14)
;; ---------------------------------------------------------------------

(require 'url)
(require 'url-http)
(require 'json)

(defconst a3madkour-pub-bib--bbt-timeout 2
  "Connection/read timeout (seconds) for BBT JSON-RPC.")

(defun a3madkour-pub-bib--bbt-payload ()
  "Build the JSON-RPC request body for item.export → Better BibTeX."
  (json-encode
   '(("jsonrpc" . "2.0")
     ("method"  . "item.export")
     ("params"  . (("library_id" . 1)
                   ("translator" . "Better BibTeX"))))))

(defun a3madkour-pub-bib--parse-bbt-response (response-buffer)
  "Parse RESPONSE-BUFFER (raw HTTP response) and return the BBT result
string on 2xx + valid JSON, else nil.  Buffer is killed at end."
  (unwind-protect
      (with-current-buffer response-buffer
        (goto-char (point-min))
        (cond
         ;; Status line
         ((not (re-search-forward "^HTTP/[0-9.]+ \\([0-9]+\\)" nil t)) nil)
         ((not (let ((code (string-to-number (match-string 1))))
                 (and (>= code 200) (< code 300)))) nil)
         (t
          ;; Skip headers (CRLF/CRLF or LF/LF) to the body.
          (goto-char (point-min))
          (when (re-search-forward "\r?\n\r?\n" nil t)
            (let ((body (buffer-substring-no-properties (point) (point-max))))
              (condition-case nil
                  (let ((parsed (json-read-from-string body)))
                    (or (cdr (assoc 'result parsed))
                        ;; alist alternative
                        (cdr (assq 'result parsed))))
                (error nil)))))))
    (when (buffer-live-p response-buffer)
      (kill-buffer response-buffer))))

(defun a3madkour-pub-bib/refresh-from-zotero ()
  "Fetch a fresh BibTeX dump via BBT JSON-RPC and atomic-write it to
`a3madkour-pub-bib/library-path'.  Returns t on success, nil on
disabled / unreachable / non-2xx / malformed response."
  (when a3madkour-pub-bib/bbt-endpoint
    (let* ((url-request-method "POST")
           (url-request-extra-headers '(("Content-Type" . "application/json")))
           (url-request-data (a3madkour-pub-bib--bbt-payload))
           (url-show-status nil)
           (timeout a3madkour-pub-bib--bbt-timeout)
           (result
            (condition-case _
                (with-timeout (timeout nil)
                  (a3madkour-pub-bib--parse-bbt-response
                   (url-retrieve-synchronously
                    a3madkour-pub-bib/bbt-endpoint t t timeout)))
              (error nil))))
      (cond
       ((not (stringp result))
        (message "[a3-pub-bib] BBT JSON-RPC: refresh failed; keeping on-disk .bib")
        nil)
       (t
        (let ((tmp (concat a3madkour-pub-bib/library-path ".tmp")))
          (with-temp-file tmp (insert result))
          (rename-file tmp a3madkour-pub-bib/library-path t)
          t))))))
```

- [ ] **Step 4: Re-run all tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-bib|FAIL|Ran [0-9]+" | head -30`
Expected: 44 total `a3madkour-pub-bib` tests pass (39 prior + 5).

- [ ] **Step 5: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-bib-test.el
git commit -m "$(cat <<'EOF'
feat(f): BBT JSON-RPC client for library.bib refresh (Task 14)

refresh-from-zotero posts item.export to better-bibtex/json-rpc
with 2s timeout; on 2xx + valid JSON atomic-writes the result to
library-path; otherwise warns and returns nil so callers can
fall back to on-disk .bib.  Disabled when bbt-endpoint=nil.
5 new ert tests covering 200/non-2xx/refused/malformed/disabled.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15 — `a3-sync-citations` command + `a3-pub.sh` flag

**Files:**
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el`
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`

- [ ] **Step 1: Locate the manifest walker prerequisite**

Run: `grep -rn "walk-published-source-set\|published-sources\|note-section" /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el | head -10`

The sync command needs a function returning all currently-published `.org` paths. If A.1's API does NOT expose this directly, define a local helper that walks `a3madkour-pub--manifest-snapshot`'s `notes` array and resolves each id → source file via `org-roam-id-find` (A.1's existing helper).

- [ ] **Step 2: Write 3 failing tests**

Append to `a3madkour-publish-citations-test.el` before its `(provide ...)`:

```elisp
;; -- Task 15: a3-sync-citations --

(ert-deftest a3madkour-pub-citations-test/sync-rebuilds-from-corpus ()
  "F Task 15: a3-sync-citations walks the corpus, accumulates, and writes
data/citations.yaml in replace mode."
  (a3madkour-pub-citations-test--with-yaml-dir
    (a3madkour-pub-bib-test--with-bib
        "@misc{a, author={A,A}, title={A}, date={2020}, publisher={P}}
@misc{b, author={A,A}, title={B}, date={2020}, publisher={P}}"
      (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil))
                ((symbol-function 'a3madkour-pub-bib/refresh-from-zotero) (lambda () nil))
                ((symbol-function 'a3madkour-pub-citations--published-source-files)
                 (lambda ()
                   (let ((src (make-temp-file "f-sync-" nil ".org")))
                     (with-temp-file src
                       (insert "Body [cite:@a] [cite:@b]\n"))
                     (list src))))
                ((symbol-function 'a3madkour-pub-rewrite/rewrite-buffer-links)
                 (lambda (&rest _) nil)))
        (a3-sync-citations)
        (let ((yaml (with-temp-buffer
                      (insert-file-contents
                       (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir))
                      (buffer-string))))
          (should (string-match-p "  a:" yaml))
          (should (string-match-p "  b:" yaml)))))))

(ert-deftest a3madkour-pub-citations-test/sync-purges-stale-keys ()
  "F Task 15: sync drops keys present in yaml but not in corpus."
  (a3madkour-pub-citations-test--with-yaml-dir
    (let ((existing (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir)))
      (with-temp-file existing
        (insert "citations:\n  stale:\n    authors: [\"X\"]\n"
                "    year: 2010\n    title: \"S\"\n    venue: \"V\"\n"))
      (a3madkour-pub-bib-test--with-bib
          "@misc{kept, author={A,A}, title={K}, date={2020}, publisher={P}}"
        (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil))
                  ((symbol-function 'a3madkour-pub-bib/refresh-from-zotero) (lambda () nil))
                  ((symbol-function 'a3madkour-pub-citations--published-source-files)
                   (lambda ()
                     (let ((src (make-temp-file "f-sync-" nil ".org")))
                       (with-temp-file src (insert "[cite:@kept]"))
                       (list src))))
                  ((symbol-function 'a3madkour-pub-rewrite/rewrite-buffer-links)
                   (lambda (&rest _) nil)))
          (a3-sync-citations)
          (let ((yaml (with-temp-buffer (insert-file-contents existing) (buffer-string))))
            (should     (string-match-p "  kept:"  yaml))
            (should-not (string-match-p "  stale:" yaml))))))))

(ert-deftest a3madkour-pub-citations-test/sync-bbt-failure-continues ()
  "F Task 15: BBT refresh failing (returns nil) does NOT block sync; the
on-disk .bib is used as-is."
  (a3madkour-pub-citations-test--with-yaml-dir
    (a3madkour-pub-bib-test--with-bib
        "@misc{a, author={A,A}, title={A}, date={2020}, publisher={P}}"
      (cl-letf (((symbol-function 'a3madkour-pub-bib--citar-loaded-p) (lambda () nil))
                ((symbol-function 'a3madkour-pub-bib/refresh-from-zotero)
                 (lambda () (message "[bbt mock] refused") nil))
                ((symbol-function 'a3madkour-pub-citations--published-source-files)
                 (lambda ()
                   (let ((src (make-temp-file "f-sync-" nil ".org")))
                     (with-temp-file src (insert "[cite:@a]"))
                     (list src))))
                ((symbol-function 'a3madkour-pub-rewrite/rewrite-buffer-links)
                 (lambda (&rest _) nil)))
        (a3-sync-citations)
        (let ((yaml (with-temp-buffer
                      (insert-file-contents
                       (expand-file-name "citations.yaml" a3madkour-pub/site-data-dir))
                      (buffer-string))))
          (should (string-match-p "  a:" yaml)))))))
```

- [ ] **Step 3: Run to verify failures**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "sync-|FAIL" | head -10`
Expected: 3 new tests FAIL.

- [ ] **Step 4: Implement `a3-sync-citations`**

Append to `a3madkour-publish-citations.el` BEFORE the `(provide ...)` line:

```elisp
;; ---------------------------------------------------------------------
;; a3-sync-citations: full rebuild (Task 15)
;; ---------------------------------------------------------------------

(defun a3madkour-pub-citations--published-source-files ()
  "Walk the manifest snapshot, return list of currently-published `.org'
source-file paths.  Skips entries whose state ≠ \"live\" or whose id
does not resolve via org-roam-id-find."
  (let* ((manifest (and (boundp 'a3madkour-pub--manifest-snapshot)
                        a3madkour-pub--manifest-snapshot))
         (notes (alist-get 'notes manifest)))
    (when (vectorp notes) (setq notes (append notes nil)))
    (delq nil
          (mapcar
           (lambda (note)
             (let ((id (alist-get 'id note))
                   (state (alist-get 'state note)))
               (when (and (equal state "live")
                          (fboundp 'org-roam-id-find))
                 (let ((hit (org-roam-id-find id)))
                   (when hit (car hit))))))
           notes))))

;;;###autoload
(defun a3-sync-citations ()
  "Full rebuild: refresh library.bib from Zotero (best-effort), walk
all currently-published org source files, re-resolve every cite-key,
and overwrite data/citations.yaml in replace mode (purge unused keys).

Errors fail-fast on first unresolvable cite-key."
  (interactive)
  ;; 1. Refresh .bib (best effort).
  (a3madkour-pub-bib/refresh-from-zotero)
  ;; 2. Reset parser cache so the post-refresh .bib is read fresh.
  (when (and (not (a3madkour-pub-bib--citar-loaded-p))
             a3madkour-pub-bib/library-path
             (file-exists-p a3madkour-pub-bib/library-path))
    (a3madkour-pub-bib/parse-file a3madkour-pub-bib/library-path))
  ;; 3. Walk corpus + accumulate.
  (a3madkour-pub-citations--accumulator-init)
  (let ((added 0))
    (dolist (src (a3madkour-pub-citations--published-source-files))
      (when (file-exists-p src)
        (with-temp-buffer
          (insert-file-contents src)
          (org-mode)
          (let ((pairs (a3madkour-pub-citations--scan-buffer)))
            (dolist (pair pairs)
              (let* ((k (car pair))
                     (pos (cdr pair))
                     (existing (gethash k a3madkour-pub-citations--accumulator)))
                (unless (a3madkour-pub-bib/resolve k)
                  (error "%s:%d: cite key %s not found in library.bib" src pos k))
                (puthash k (cons (cons src pos) existing)
                         a3madkour-pub-citations--accumulator)
                (setq added (1+ added))))))))
    ;; 4. Overwrite yaml in replace mode.
    (a3madkour-pub-citations/emit-yaml :mode 'replace)
    (message "[a3-sync-citations] %d cite refs across %d keys synced."
             added
             (hash-table-count a3madkour-pub-citations--accumulator))))
```

- [ ] **Step 5: Re-run tests**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-citations|FAIL|Ran [0-9]+" | head -30`
Expected: 34 `a3madkour-pub-citations` tests pass (31 prior + 3).

- [ ] **Step 6: Add `a3-pub.sh --sync-citations` flag intercept**

Run: `grep -n "publish-deliberate\|publish-living\|check-orphans" /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh | head -10`

Use that grep to find the existing flag-dispatch block. Add a new branch for `--sync-citations` that loads both bib and citations modules and invokes `(a3-sync-citations)`:

```bash
if [[ "$1" == "--sync-citations" ]]; then
  exec emacs --batch \
    -l a3madkour-publish \
    -l a3madkour-publish-history \
    -l a3madkour-publish-bib \
    -l a3madkour-publish-citations \
    --eval "(a3madkour-pub/begin-publish)" \
    --eval "(a3-sync-citations)" \
    --eval "(a3madkour-pub/finish-publish)"
fi
```

Also add `-l a3madkour-publish-bib` and `-l a3madkour-publish-citations` to BOTH the existing `--publish-living` and `--publish-deliberate` `exec` blocks. Use exact paths in the `-l` directives per the existing pattern in the script.

- [ ] **Step 7: Smoke-test the shell entry point**

(Do NOT run the full flow against the real corpus yet — that's Task 18. This step just confirms the flag dispatches without missing-module errors.)

Run: `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --sync-citations --help 2>&1 | head -5`

If `--help` isn't supported, accept any non-error output. The acceptance criterion is: no `Cannot open load file` for either F module.

- [ ] **Step 8: Commit (dotfiles)**

```bash
cd /Users/a3madkour
git add dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations.el dotfiles/emacs-configs/custom/lisp/a3madkour-publish-citations-test.el dotfiles/emacs-configs/custom/lisp/a3-pub.sh
git commit -m "$(cat <<'EOF'
feat(f): a3-sync-citations + a3-pub.sh --sync-citations (Task 15)

M-x a3-sync-citations and the shell flag both perform: bib refresh
(best-effort), walk manifest-published sources, accumulate cite-keys,
overwrite data/citations.yaml in replace mode.  Adds -l bib + -l
citations to publish-living and publish-deliberate exec blocks.
3 new ert tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 16 — Integration fixtures + `TestCitationRoundtrip`

**Files:**
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/fixtures/citations/example-cite-one.org`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/fixtures/citations/example-cite-two.org`
- Create: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/fixtures/citations/ref-notes/dummyKey2024.org`
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Create source fixtures**

Run: `mkdir -p /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/fixtures/citations/ref-notes`

Write `tools/fixtures/citations/example-cite-one.org`:

```org
:PROPERTIES:
:ID:       essay-cite-one-uuid-placeholder
:END:
#+title: Example cite-one
#+date: 2026-06-01
#+filetags: :example-tag:
#+HUGO_PUBLISH: t
#+HUGO_SECTION: essays
#+HUGO_SUMMARY: Lorem ipsum cite roundtrip.

* Section one — example heading

Lorem ipsum [cite:@loremIpsumDolorSit2020] and also [cite:@dummyKey2024].

Multi-cite case: [cite:@loremIpsumDolorSit2020;@consecteturAdipiscingElit2018].
```

Write `tools/fixtures/citations/example-cite-two.org`:

```org
:PROPERTIES:
:ID:       essay-cite-two-uuid-placeholder
:END:
#+title: Example cite-two
#+date: 2026-06-01
#+filetags: :example-tag:
#+HUGO_PUBLISH: t
#+HUGO_SECTION: essays
#+HUGO_SUMMARY: Narrow case.

* Section one
Just [cite:@utLaboreEtDolore2022].
```

Write `tools/fixtures/citations/ref-notes/dummyKey2024.org`:

```org
:PROPERTIES:
:ID:       dummy-key-2024-uuid
:END:
#+title: Dummy Key 2024 — example ref-note
#+filetags: :example-ref:
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
#+HUGO_GROWTH_STAGE: seedling

A note about the cited paper.
```

- [ ] **Step 2: Write the integration test**

Append to `tools/test_publish_integration.py` after the existing classes. If this test must run inside a TestCase, define `TestCitationRoundtrip(unittest.TestCase)`:

```python
class TestCitationRoundtrip(unittest.TestCase):
    """F Task 16: stub library.bib + 2 stub essays citing 4 keys →
    data/citations.yaml carries exactly those 4 keys with the schema mapping."""

    FIXTURE_BIB = (
        Path(__file__).resolve().parent / "fixtures" / "citations" / "library.bib"
    )
    FIXTURE_SRC = Path(__file__).resolve().parent / "fixtures" / "citations"

    def setUp(self) -> None:
        self.site_root = tempfile.mkdtemp(prefix="a3-pub-cite-roundtrip-")
        for sub in ("content/essays", "content/garden", "data"):
            os.makedirs(os.path.join(self.site_root, sub), exist_ok=True)
        # Seed an empty manifest so begin-publish has something to snapshot.
        with open(os.path.join(self.site_root, "data", "url-history.yaml"), "w") as f:
            f.write("manifest_version: 1\nnotes: []\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.site_root, ignore_errors=True)

    def _publish(self, src_org: Path) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["A3_PUB_SITE_ROOT"] = self.site_root
        env["A3_PUB_BIB_PATH"]  = str(self.FIXTURE_BIB)
        return subprocess.run(
            ["/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh",
             "--publish-deliberate", str(src_org)],
            env=env, capture_output=True, text=True, timeout=60)

    def test_two_essays_yield_four_citations(self) -> None:
        for src in ("example-cite-one.org", "example-cite-two.org"):
            result = self._publish(self.FIXTURE_SRC / src)
            self.assertEqual(result.returncode, 0,
                             f"{src} failed:\n{result.stderr}")

        yaml_path = os.path.join(self.site_root, "data", "citations.yaml")
        self.assertTrue(os.path.exists(yaml_path),
                        "citations.yaml was not emitted")
        with open(yaml_path) as f:
            text = f.read()

        for key in ("loremIpsumDolorSit2020", "consecteturAdipiscingElit2018",
                    "utLaboreEtDolore2022", "dummyKey2024"):
            self.assertIn(f"  {key}:", text, f"missing key {key}")

        # Schema mapping spot-checks (per spec §5):
        # - title with outer braces stripped
        self.assertIn('title: "Lorem Ipsum Dolor Sit Amet"', text)
        # - venue chosen from journaltitle for @article
        self.assertIn('venue: "Journal of Examples"', text)
        # - type enum
        self.assertIn('type: "article"', text)
        # - publisher fallback path for @book
        self.assertIn('venue: "Example Press"', text)
```

(If the test file lacks `import tempfile`, `import shutil`, `import subprocess`, `import os`, or `from pathlib import Path` at the top, add them.)

- [ ] **Step 3: Wire the env-var → defcustom bridge**

The fixture test passes `A3_PUB_SITE_ROOT` and `A3_PUB_BIB_PATH`. Verify (or add) the corresponding handling in `a3-pub.sh` so the emacs invocation picks them up. If not already present:

Add early in `a3-pub.sh`, before any `exec emacs`:

```bash
if [[ -n "${A3_PUB_SITE_ROOT:-}" ]]; then
  EMACS_INIT_EVAL+=(--eval "(setq a3madkour-pub/site-content-dir \"$A3_PUB_SITE_ROOT/content/\")")
  EMACS_INIT_EVAL+=(--eval "(setq a3madkour-pub/site-data-dir    \"$A3_PUB_SITE_ROOT/data/\")")
fi
if [[ -n "${A3_PUB_BIB_PATH:-}" ]]; then
  EMACS_INIT_EVAL+=(--eval "(setq a3madkour-pub-bib/library-path \"$A3_PUB_BIB_PATH\")")
fi
```

Then thread `"${EMACS_INIT_EVAL[@]}"` into each `exec emacs ...` command alongside the existing `-l` directives.

(The exact name `EMACS_INIT_EVAL` may differ in the existing script — adapt as needed. The principle: env-var → `--eval (setq …)`.)

- [ ] **Step 4: Run the integration test**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration.TestCitationRoundtrip -v 2>&1 | tail -25`
Expected: 1 test PASS. If it FAILs with `Cannot open load file`, check that all `-l` lines in `a3-pub.sh --publish-deliberate` include `a3madkour-publish-bib` and `a3madkour-publish-citations`.

- [ ] **Step 5: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/fixtures/citations/ tools/test_publish_integration.py
git commit -m "$(cat <<'EOF'
test(f): integration — citation roundtrip end-to-end (Task 16)

3 fixture .org files (2 essays + 1 ref-note) + integration test
that publish-deliberates both essays and asserts data/citations.yaml
carries 4 expected keys with schema mapping intact (title outer-
braces stripped, venue picked per type, type enum correct).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 17 — Integration: `TestSyncPurges` + `TestHugoRendersCitedEssay`

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py`

- [ ] **Step 1: Append `TestSyncPurges`**

```python
class TestSyncPurges(unittest.TestCase):
    """F Task 17: pre-seeded data/citations.yaml with stale keys → after
    a3-sync-citations against a corpus citing only one key → yaml has
    exactly that one key."""

    FIXTURE_BIB = TestCitationRoundtrip.FIXTURE_BIB
    FIXTURE_SRC = TestCitationRoundtrip.FIXTURE_SRC

    def setUp(self) -> None:
        self.site_root = tempfile.mkdtemp(prefix="a3-pub-cite-sync-")
        for sub in ("content/essays", "data"):
            os.makedirs(os.path.join(self.site_root, sub), exist_ok=True)
        # Seed yaml with stale keys.
        with open(os.path.join(self.site_root, "data", "citations.yaml"), "w") as f:
            f.write(
                'citations:\n'
                '  staleKey-1:\n'
                '    authors: ["X, Y"]\n'
                '    year: 2010\n'
                '    title: "Stale"\n'
                '    venue: "V"\n'
                '  staleKey-2:\n'
                '    authors: ["A, B"]\n'
                '    year: 2011\n'
                '    title: "Stale Two"\n'
                '    venue: "V"\n'
            )
        # Seed manifest pointing at example-cite-two only.
        with open(os.path.join(self.site_root, "data", "url-history.yaml"), "w") as f:
            f.write(
                "manifest_version: 1\n"
                "notes:\n"
                f"  - id: essay-cite-two-uuid-placeholder\n"
                f"    current_url: /essays/example-cite-two/\n"
                f"    state: live\n"
                f"    aliases: []\n"
                f"    source_file: {self.FIXTURE_SRC / 'example-cite-two.org'}\n"
            )

    def tearDown(self) -> None:
        shutil.rmtree(self.site_root, ignore_errors=True)

    def test_sync_drops_uncited_keys(self) -> None:
        env = os.environ.copy()
        env["A3_PUB_SITE_ROOT"] = self.site_root
        env["A3_PUB_BIB_PATH"]  = str(self.FIXTURE_BIB)
        result = subprocess.run(
            ["/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh",
             "--sync-citations"],
            env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(os.path.join(self.site_root, "data", "citations.yaml")) as f:
            text = f.read()
        self.assertIn("  utLaboreEtDolore2022:", text)
        self.assertNotIn("  staleKey-1:", text)
        self.assertNotIn("  staleKey-2:", text)
```

(This test depends on the manifest snapshot's `source_file` field resolving to an actual `.org` path. If A.1's manifest does NOT carry a `source_file` field — confirm with `grep -n "source_file" /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el` — then `published-source-files` in Task 15 must fall back to `org-roam-id-find`, and the fixture ref-note must be roam-indexed. In that case, gate this test with `@unittest.skip(...)` and treat it as an author-run manual check; flag the gap as a Task 15 follow-up.)

- [ ] **Step 2: Append `TestHugoRendersCitedEssay`**

```python
class TestHugoRendersCitedEssay(unittest.TestCase):
    """F Task 17b: after publishing a cited essay, `hugo --minify` builds
    successfully and produces a /essays/example-cite-one/ page whose HTML
    contains a <cite> anchor pointing at #ref-loremIpsumDolorSit2020."""

    FIXTURE_BIB = TestCitationRoundtrip.FIXTURE_BIB
    FIXTURE_SRC = TestCitationRoundtrip.FIXTURE_SRC

    def setUp(self) -> None:
        # Run inside the real site repo so Hugo has all layouts/partials.
        self.site_root = "/Users/a3madkour/Sync/Workspace/a3madkour.github.io"
        # Snapshot existing yaml + essays we may mutate.
        self.yaml_backup = (
            Path(self.site_root) / "data" / "citations.yaml"
        ).read_text()

    def tearDown(self) -> None:
        # Restore yaml.
        (Path(self.site_root) / "data" / "citations.yaml").write_text(self.yaml_backup)
        # Remove the test-cite essay bundle if we created it.
        bundle = Path(self.site_root) / "content" / "essays" / "example-cite-one"
        if bundle.exists():
            shutil.rmtree(bundle, ignore_errors=True)

    def test_hugo_builds_and_cite_anchor_renders(self) -> None:
        env = os.environ.copy()
        env["A3_PUB_BIB_PATH"]  = str(self.FIXTURE_BIB)
        # Publish the cited fixture into the live site tree.
        publish = subprocess.run(
            ["/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh",
             "--publish-deliberate",
             str(self.FIXTURE_SRC / "example-cite-one.org")],
            env=env, cwd=self.site_root, capture_output=True, text=True, timeout=60)
        self.assertEqual(publish.returncode, 0, publish.stderr)

        # Build hugo.
        build = subprocess.run(
            ["hugo", "--minify"],
            cwd=self.site_root, capture_output=True, text=True, timeout=120)
        self.assertEqual(build.returncode, 0, build.stderr)

        out_html = Path(self.site_root) / "public" / "essays" / "example-cite-one" / "index.html"
        self.assertTrue(out_html.exists(), f"{out_html} not generated")
        html = out_html.read_text()
        self.assertIn('href="#ref-loremIpsumDolorSit2020"', html,
                      "cite shortcode anchor not rendered")
        self.assertIn('id="ref-loremIpsumDolorSit2020"', html,
                      "essay-references partial did not render the entry id")
```

(This test mutates the live site tree's `data/citations.yaml` + creates a content bundle. The `tearDown` restores yaml and removes the bundle. If you'd rather NOT touch the live tree, gate this with `@unittest.skip("manual smoke")` and flag for manual run during Task 18.)

- [ ] **Step 3: Run both new tests**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration.TestSyncPurges tools.test_publish_integration.TestHugoRendersCitedEssay -v 2>&1 | tail -25`
Expected: both PASS (or `TestSyncPurges` skipped per Step 1 caveat, plus `TestHugoRendersCitedEssay` PASSes).

- [ ] **Step 4: Run the full integration suite to catch regressions**

Run: `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration -v 2>&1 | tail -10`
Expected: 36 total (33 baseline + 3 new) PASS.

- [ ] **Step 5: Commit (site)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
git commit -m "$(cat <<'EOF'
test(f): integration — sync purges + hugo renders cite (Task 17)

TestSyncPurges pre-seeds stale keys in data/citations.yaml then
runs a3-pub.sh --sync-citations and asserts only currently-cited
keys survive.  TestHugoRendersCitedEssay publishes a fixture into
the live site tree, builds with hugo --minify, and asserts the
cite shortcode anchor + essay-references entry both render.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 18 — Real-corpus spot-check (manual)

This task does not produce code; it produces author confidence and may surface fix-up commits.

- [ ] **Step 1: Prerequisite check — `library.bib` exists**

Run: `ls -la ~/org/notes/ref-notes/library.bib && wc -l ~/org/notes/ref-notes/library.bib`
Expected: ~15.6k lines (matching the spec's stated size). If missing, run BBT export manually before proceeding.

- [ ] **Step 2: Stage two cited essays in `~/org/essays/`**

Pick (or create) two essay sources that cite real BBT keys from your library. Each must have `#+HUGO_PUBLISH: t` and `#+HUGO_SECTION: essays`. Use real cite-keys you've referenced in your queue or notes (e.g. `friedmanApproximateKnowledgeCompilation`).

- [ ] **Step 3: Time `a3-publish-deliberate` against the real bib**

Run (M-x):
```
M-x a3-publish-deliberate RET ~/org/essays/<your-essay-1>.org RET
```

Then in `*Messages*` look for any cite-related warning. Expected: clean run; `data/citations.yaml` grows with the cited keys.

- [ ] **Step 4: Time `M-x a3-sync-citations` against the real bib**

Run:
```
M-x a3-sync-citations RET
```

Wall-clock benchmark target: under 5 seconds end-to-end on the full 15.6k-entry `.bib`. If it's substantially slower (>15s), open a follow-up: `project_f_perf_regression` memory.

- [ ] **Step 5: Verify Hugo build passes**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
hugo --minify 2>&1 | tail -5
python3 tools/check_citations.py
```

Expected: clean Hugo build; `OK — citations.yaml validates.` from the linter.

- [ ] **Step 6: Spot-check the rendered essay**

Open `public/essays/<your-essay-1>/index.html` (or run `hugo server --buildDrafts`); verify:
- Inline `[Author Year]` brackets render correctly.
- Anchors jump to `#ref-<key>` in the references section.
- The reference list shows the entry with title/authors/year matching what's in `library.bib`.
- The author-format buttons (BibTeX / APA / RIS) on each ref work via the existing modal.

- [ ] **Step 7: If any issue surfaces, add a fix-up commit per finding**

For each issue (e.g. a parser edge case the real .bib trips, a mapping case the spec didn't anticipate, an essay-references rendering glitch):
1. Add a failing ert test exercising the case.
2. Fix the code minimally.
3. Re-run all tests.
4. Commit with subject `fix(f): <one-line description> (Task 18 spot-check)`.

- [ ] **Step 8: Update memory**

Once Task 18 is clean (no outstanding spot-check issues), update memory file `project_f_complete.md` summarizing:
- Final ert + integration counts
- Notable Task 18 fix-ups (if any)
- Performance numbers on the real `.bib`
- Per-spec acceptance: every spec §1 goal landed; every spec §14 follow-up still queued as memorable
- Any lessons that became durable references (e.g. surprising BBT edge cases)

---

## Self-Review

### Spec coverage

- §1 Goals — Task 9 (rewriter + accumulator), Task 11 (emit-yaml), Task 13 (wire into living/deliberate), Task 15 (a3-sync-citations + a3-pub.sh flag). ✓
- §1 Non-goals — style overrides, prefix/suffix, positional `#+print_bibliography:`, rich passthrough are NOT in any task. Task 9 strips `#+print_bibliography:` and fails-fast on style overrides + prefix/suffix per §3.1. ✓
- §2 Module structure — Tasks 3–7 build `a3madkour-publish-bib.el`; Tasks 8–11 + 15 build `a3madkour-publish-citations.el`. Task 12 modifies `a3madkour-publish-rewrite.el`. Task 13 modifies living + deliberate. Task 15 also modifies `a3-pub.sh`. ✓
- §3 Source-side contract (supported forms + buffer safety + #+print_bibliography:) — Tasks 8 + 9. ✓
- §4 Bib resolver architecture — Tasks 3–7 (parser), Task 7 (citar adapter + dispatch), Task 14 (BBT JSON-RPC). ✓
- §5 BibTeX → yaml mapping — Task 6 (`normalize-entry`). ✓
- §6 `notes_ref` auto-detection — Task 10. ✓
- §7 Per-publish data flow — Tasks 9 (rewriter+accumulator) + 12 (wired into chokepoint) + 13 (emit-yaml tail call). ✓
- §8 Sync data flow — Task 15. ✓
- §9 Error handling — Task 9 (rewriter fail-fast), Task 11 (emit-yaml validation), Task 14 (BBT silent-fail). ✓
- §10 Linter changes — Task 1. ✓
- §11 Wrapper script — Task 15. ✓
- §12 Testing — every task is TDD-first. Total: ~85 ert (Task 3:9, Task 4:8, Task 5:5, Task 6:12, Task 7:5, Task 8:7, Task 9:11, Task 10:5, Task 11:8, Task 13:1, Task 14:5, Task 15:3) + 3 wiring tests (Task 12 + Task 13 + sync) + 3 integration (Task 16 + Task 17a + Task 17b). ✓

### Placeholder scan

- No `TBD` / `TODO` / "implement later".
- No "similar to Task N" without code repeated.
- No "add appropriate error handling" — every fail-fast path has exact `error` call + message string.

### Type consistency

- `bib-resolve` returns a plist with the same keys across all tasks: `:authors`, `:year`, `:title`, `:venue`, `:url`, `:doi`, `:publisher`, `:volume`, `:issue`, `:pages`, `:isbn`, `:type`.
- The accumulator stores `(SOURCE-FILE . POS)` pairs throughout (Tasks 9 + 11 + 15).
- `:notes_ref` is added by `emit-yaml` (Task 11), populated via `--lookup-notes-ref` (Task 10). Consistent.
- `cite-emit-yaml` accepts `:mode 'merge | 'replace`. Used identically in living/deliberate (Task 13: merge) vs sync (Task 15: replace).
- `bbt-endpoint` defcustom (Task 14) referenced in same form by sync (Task 15).


