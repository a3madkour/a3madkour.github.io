# Tier 8.2 — Org → synced-poetry export — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the org-mode → ox-hugo → site path that emits the already-shipped time-synced-poetry runtime contract from real org content, so an authored poem with `[mm:ss]` markers + audio round-trips to a working synced page with zero hand-editing.

**Architecture:** New peer module `a3madkour-publish-poetry.el` in dotfiles, sibling to `a3madkour-publish-essays.el`. Registered in `a3madkour-publish-deliberate.el`'s dispatch alist under the symbol `'works/poetry`. The handler reuses the shared B.0 infra (`rewrite-to-tmp-file`, `export-file`, `asset-validate-and-copy`, `record-publish`) and adds: a poetry-specific frontmatter normalizer, a `#+AUDIO:` keyword reader with URL-vs-filename routing, an audio-asset copy helper, and two soft warnings. Site-repo changes: extend the integration test suite to cover poetry; the final real-poem publication lives as authored content under `content/works/poetry/<slug>/`.

**Tech Stack:** Emacs Lisp (lexical-binding), ox-hugo, ert, Python (subprocess integration tests, stdlib only), Hugo (consumer — untouched).

**Spec:** `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md` (commit `e81e227`).

**Convention note (caught during Task 2):** The dotfiles codebase uses **two parallel section symbol forms**: the `#+HUGO_SECTION:` enum + deliberate dispatch alist use **slash form** (`'works/poetry`, matches the Hugo nested-section path); the `a3madkour-pub-frontmatter--known-sections` whitelist + normalize dispatch arms use **hyphen form** (`'works-poetry`, matches existing `research-themes` / `library-reading` pattern). The poetry handler must use **slash form** for dispatch alist + `note-section` results, and **hyphen form** for the `normalize` call. Plan respects this throughout — don't bulk-rename one to the other.

**Repo touch summary:**
- Dotfiles (`/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/`): one new module + one new `*-test.el` + one dispatch-alist line + one frontmatter dispatch arm + one wrapper-script `-l` line.
- Site repo: integration-test additions in `tools/test_publish_integration.py`; final real-poem publication under `content/works/poetry/<real-slug>/` (Task 12 closure step).

---

## File structure

**Dotfiles — created:**
- `lisp/a3madkour-publish-poetry.el` — new handler module (~200 LOC target).
- `lisp/a3madkour-publish-poetry-test.el` — ert tests (11 tests per spec §Tests).

**Dotfiles — modified:**
- `lisp/a3madkour-publish-deliberate.el` — alist entry + `(require 'a3madkour-publish-poetry)`.
- `lisp/a3madkour-publish-frontmatter.el` — dispatch arm + new normalizer (or normalizer in poetry module + alist-driven dispatch; Task 3 decides based on existing pattern).
- `lisp/a3-pub.sh` — append `-l a3madkour-publish-poetry`.

**Site repo — modified:**
- `tools/test_publish_integration.py` — append poetry integration test class.

**Site repo — created (Task 12 closure):**
- `content/works/poetry/<real-slug>/index.md` + sibling audio file. Authored from a real org poem at `~/org/notes/works/poetry/<real-slug>.org`.

---

## Pre-flight (read once before starting)

1. **Spec:** `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md` — re-read end to end.
2. **Shipped runtime contract:** `layouts/partials/works/synced-text-parser.html` + `tools/check_poetry_synced.py` + `tools/check_works_fixtures.py:44-46`.
3. **Shipped fixture target shape (byte-stable goal):** `content/works/poetry/example-poem-synced/index.md` (22 lines, quoted in spec §Authoring surface).
4. **Peer handler precedent:** `lisp/a3madkour-publish-essays.el` (299 LOC). Mirror the structure; do not modify it.
5. **Shared B.0 infra you will call:**
   - `a3madkour-pub/note-metadata` (`lisp/a3madkour-publish.el`)
   - `a3madkour-pub-rewrite/rewrite-to-tmp-file` (`lisp/a3madkour-publish-rewrite.el`)
   - `a3madkour-pub-export/export-file` (`lisp/a3madkour-publish-export.el`)
   - `a3madkour-pub-frontmatter/normalize` (`lisp/a3madkour-publish-frontmatter.el:58`)
   - `a3madkour-pub/asset-validate-and-copy` (`lisp/a3madkour-publish-assets.el:501`)
   - `a3madkour-pub-history/record-publish` (`lisp/a3madkour-publish-history.el:199`)
   - `a3madkour-pub-keywords/extract` + `a3madkour-pub-keywords/boolean-p` (`lisp/a3madkour-publish-keywords.el:10,25`)
6. **Test runner:** `lisp/run-tests.sh` (auto-discovers every `*-test.el` and runs ert batch). Current baseline: 662 tests.

---

## Task 0: Empirical reconnaissance — does ox-hugo preserve `\[mm:ss]`?

**Why:** Spec §Risks #1 calls out that ox-hugo's paragraph handling may eat the `\` and emit a bare `[mm:ss]` — which the runtime would then parse as a real timing event. This task observes what actually happens before designing the export path. No code commits.

**Files:** None modified. Scratch only.

- [ ] **Step 0.1: Write a 6-line scratch org fixture**

Create `/tmp/synced-poetry-recon.org`:

```org
:PROPERTIES:
:ID:       11111111-1111-1111-1111-111111111111
:END:
#+TITLE: Recon
#+HUGO_SECTION: works/poetry
#+DATE: 2026-06-12

[00:01]Lorem [00:02]ipsum
[00:17]Duis aute \[00:99] reprehenderit
```

- [ ] **Step 0.2: Export through ox-hugo with the same invocation a3-pub.sh uses**

Run from dotfiles root:

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom
emacs --batch \
  --eval "(setq user-emacs-directory \"$(pwd)/\")" \
  --eval "(setq straight-base-dir user-emacs-directory)" \
  -l straight/repos/straight.el/bootstrap.el \
  --eval "(straight-use-package 'org-roam)" \
  --eval "(straight-use-package 'ox-hugo)" \
  --eval "(dolist (dir (directory-files (expand-file-name \"straight/build/\" user-emacs-directory) t \"^[^.]\")) (when (file-directory-p dir) (add-to-list 'load-path dir)))" \
  --visit=/tmp/synced-poetry-recon.org \
  --eval "(require 'ox-hugo)" \
  --eval "(org-hugo-export-to-md)" 2>&1 | tail -20
```

The output bundle goes to (probably) `content/works/poetry/recon.md` next to wherever org-hugo decides — observe whichever path it lands at.

- [ ] **Step 0.3: Read the emitted markdown body and record the answer**

Expected outcomes (one of):

**Case A — backslash preserved:** Body contains `\[00:99]` literally. The runtime escape works; no exporter intervention needed.

**Case B — backslash consumed:** Body contains bare `[00:99]`. The runtime would treat it as a timing event. The plan needs a protect-and-restore pre-export pass (Task 6 will add it).

**Case C — some other transform** (e.g. ox-hugo emits ` \\\[00:99\\\] ` with HTML escapes): record exactly what comes out; the plan branches on this evidence.

- [ ] **Step 0.4: Document the answer in the plan**

Add a one-line note at the top of Task 6 (the asset/handler stage where escape handling lives): "Recon outcome: Case A/B/C — observed body bytes were `<exact>`". This determines whether Task 6 includes a `--protect-escape` pre-export helper.

If **Case B or C**, also extend Step 6's failing-test list with a regression test that asserts the escape survives.

No commits in Task 0 — the outcome is recorded in the working tree (this plan file).

---

## Task 1: Skeleton module + dispatch wiring

**Files:**
- Create: `lisp/a3madkour-publish-poetry.el`
- Modify: `lisp/a3madkour-publish-deliberate.el:15-22`
- Modify: `lisp/a3-pub.sh:222` (append `-l` line)
- Test: `lisp/a3madkour-publish-poetry-test.el` (create)

- [ ] **Step 1.1: Write the failing skeleton test**

Create `lisp/a3madkour-publish-poetry-test.el`:

```elisp
;;; a3madkour-publish-poetry-test.el --- ert tests for works/poetry handler  -*- lexical-binding: t; -*-

;;; Code:

(require 'ert)
(require 'cl-lib)
(require 'a3madkour-publish-poetry)
(require 'a3madkour-publish-deliberate)

(ert-deftest a3madkour-pub-poetry-test/module-provides ()
  "The poetry module loads and provides its feature."
  (should (featurep 'a3madkour-publish-poetry)))

(ert-deftest a3madkour-pub-poetry-test/dispatch-registered ()
  "The deliberate dispatch alist contains a works/poetry entry."
  (should (eq (cdr (assq 'works/poetry a3madkour-pub-deliberate--handlers))
              'a3madkour-pub-poetry/publish-poetry-file)))

(ert-deftest a3madkour-pub-poetry-test/section-dir-default ()
  "`section-dir-name' defaults to \"works/poetry\" (relative to site root)."
  (should (equal a3madkour-pub-poetry/section-dir-name "works/poetry")))

(provide 'a3madkour-publish-poetry-test)

;;; a3madkour-publish-poetry-test.el ends here
```

- [ ] **Step 1.2: Run tests to verify they fail (module not loadable)**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh -t '^a3madkour-pub-poetry-test/'`
Expected: FAIL with "Cannot open load file: a3madkour-publish-poetry".

- [ ] **Step 1.3: Create the skeleton module**

Create `lisp/a3madkour-publish-poetry.el`:

```elisp
;;; a3madkour-publish-poetry.el --- Tier 8.2 works/poetry per-file publish handler  -*- lexical-binding: t; -*-

;;; Commentary:

;; Publishes a single org-mode poem into a synced-poetry page bundle
;; under `content/works/poetry/<slug>/'.
;;
;; Peer of `a3madkour-publish-essays.el'.  Both call into shared B.0
;; infra (rewrite-to-tmp-file, export-file, asset-validate-and-copy,
;; record-publish).  The essays handler is not modified by this slice.
;;
;; Authoring contract: see
;; `docs/superpowers/specs/2026-05-19-org-synced-poetry-export.md'.

;;; Code:

(require 'cl-lib)
(require 'a3madkour-publish)
(require 'a3madkour-publish-export)
(require 'a3madkour-publish-frontmatter)
(require 'a3madkour-publish-rewrite)
(require 'a3madkour-publish-assets)
(require 'a3madkour-publish-history)
(require 'a3madkour-publish-keywords)

(defgroup a3madkour-pub-poetry nil
  "Tier 8.2 works/poetry publish handler."
  :group 'a3madkour-pub)

(defcustom a3madkour-pub-poetry/section-dir-name "works/poetry"
  "Relative content directory under `content/' for poetry bundles.
The on-disk path becomes `content/<section-dir-name>/<slug>/index.md'.
Independent of the `#+HUGO_SECTION:' dispatch symbol (`works/poetry')."
  :type 'string
  :group 'a3madkour-pub-poetry)

(defcustom a3madkour-pub/poetry-dir
  (expand-file-name "notes/works/poetry/" (getenv "HOME"))
  "Root directory of the author's poem org files.
Each poem lives at `<poetry-dir>/<slug>.org' with assets under
`<poetry-dir>/assets/<id>/'."
  :type 'directory
  :group 'a3madkour-pub-poetry)

(defconst a3madkour-pub-poetry--audio-extensions
  '("mp3" "m4a" "ogg" "wav")
  "Allowed audio extensions for `#+AUDIO:' relative filenames.")

(cl-defun a3madkour-pub-poetry/publish-poetry-file (file run &key on-done)
  "Publish a single poem FILE to `content/works/poetry/<slug>/index.md'.

Stub for Task 10.  Tasks 2-9 build out the supporting helpers
(section detection, normalizer, audio keyword resolver, asset copy,
summary scrub, soft warnings, multi-export warn-and-skip).  Task 10
wires them into this entry point."
  (ignore file run on-done)
  (error "a3madkour-pub-poetry/publish-poetry-file: not yet implemented (Task 10)"))

(provide 'a3madkour-publish-poetry)

;;; a3madkour-publish-poetry.el ends here
```

- [ ] **Step 1.4: Wire into deliberate dispatch**

Edit `lisp/a3madkour-publish-deliberate.el`. Locate the `require` block (line 15) and the dispatch alist (line 20):

```elisp
(require 'a3madkour-publish-essays)
(require 'a3madkour-publish-poetry)   ;; NEW

(defvar a3madkour-pub-deliberate--handlers
  '((essays       . a3madkour-pub-essays/publish-essay-file)
    (works/poetry . a3madkour-pub-poetry/publish-poetry-file))   ;; NEW
  "Alist of (SECTION-SYMBOL . HANDLER-FUNCTION).
Handler signature: (file run &key on-done).")
```

- [ ] **Step 1.5: Wire into a3-pub.sh**

Edit `lisp/a3-pub.sh`. In the `--publish-deliberate` block (around line 222), append after the existing `-l a3madkour-publish-essays` line:

```bash
    -l a3madkour-publish-essays \
    -l a3madkour-publish-poetry \
    -l a3madkour-publish-bib \
```

- [ ] **Step 1.6: Run the three tests; verify they pass**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh -t '^a3madkour-pub-poetry-test/'`
Expected: PASS — 3 tests run, 3 passed.

- [ ] **Step 1.7: Run the full suite; verify no regressions**

Run: `cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh`
Expected: PASS — 662 + 3 = 665 tests run, 0 failed.

- [ ] **Step 1.8: Commit (dotfiles)**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el \
        emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-deliberate.el \
        emacs-configs/custom/lisp/a3-pub.sh
git commit -m "feat(poetry): Tier 8.2 skeleton — works/poetry handler stub + dispatch wiring"
```

---

## Task 2: Section detection — `#+HUGO_SECTION: works/poetry` routes to the new handler

**Files:**
- Test: `lisp/a3madkour-publish-poetry-test.el`
- Modify: none (existing `a3madkour-pub/note-section` already reads `#+HUGO_SECTION:` via keyword-extract)

This task is a thin verification that no infra change is needed — the new section symbol just works because `note-section` is generic.

- [ ] **Step 2.1: Write the failing test**

Append to `lisp/a3madkour-publish-poetry-test.el`:

```elisp
(ert-deftest a3madkour-pub-poetry-test/section-detection ()
  "A .org file with `#+HUGO_SECTION: works/poetry' resolves to that section."
  (let ((tmp (make-temp-file "poetry-section-" nil ".org"
                             ":PROPERTIES:\n:ID: 22222222-2222-2222-2222-222222222222\n:END:\n#+TITLE: T\n#+HUGO_SECTION: works/poetry\n#+HUGO_PUBLISH: t\n#+DATE: 2026-06-12\n\nbody\n")))
    (unwind-protect
        (should (equal (a3madkour-pub/note-section tmp) "works/poetry"))
      (delete-file tmp))))
```

- [ ] **Step 2.2: Run; verify PASS (infra already supports this)**

Run: `./run-tests.sh -t '^a3madkour-pub-poetry-test/section-detection$'`
Expected: PASS — `note-section` is generic over the keyword value.

If FAIL, the failure mode is informative — possibly `note-metadata` caches and clears around the temp file. Inspect, do not work around without understanding.

- [ ] **Step 2.3: Commit**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el
git commit -m "test(poetry): verify works/poetry section detection routes through generic note-section"
```

---

## Task 3: Frontmatter normalizer skeleton + dispatch arm

**Files:**
- Modify: `lisp/a3madkour-publish-poetry.el` (add normalizer)
- Modify: `lisp/a3madkour-publish-frontmatter.el:58-89` (add dispatch arm)
- Modify: `lisp/a3madkour-publish-poetry-test.el`

- [ ] **Step 3.1: Write the failing test for normalizer routing**

Append to `lisp/a3madkour-publish-poetry-test.el`:

```elisp
(ert-deftest a3madkour-pub-poetry-test/normalize-passes-through-allowed-keys ()
  "Normalizer passes through allowed optional keys; drops essay-only keys."
  (let* ((raw '((title . "Untitled Poem")
                (date . "2026-06-12")
                (lastmod . "2026-06-12")
                (draft . nil)
                (tags . ("example" "synced"))
                (collection . "greenhouse-demos")
                (set_to_music . "music-slug")
                (source_stream . "stream-slug")
                (has_sidenotes . t)            ; essay-only — should be dropped
                (has_citations . t)            ; essay-only — should be dropped
                (toc . t)))                    ; essay-only — should be dropped
         (out (a3madkour-pub-frontmatter/normalize 'works-poetry raw nil)))
    (should (equal (alist-get 'title out) "Untitled Poem"))
    (should (equal (alist-get 'collection out) "greenhouse-demos"))
    (should (equal (alist-get 'set_to_music out) "music-slug"))
    (should (equal (alist-get 'source_stream out) "stream-slug"))
    (should (equal (alist-get 'tags out) '("example" "synced")))
    (should-not (alist-get 'has_sidenotes out))
    (should-not (alist-get 'has_citations out))
    (should-not (alist-get 'toc out))))
```

- [ ] **Step 3.2: Run; expect FAIL (no dispatch arm)**

Run: `./run-tests.sh -t '^a3madkour-pub-poetry-test/normalize-passes-through-allowed-keys$'`
Expected: FAIL — raw alist returned unchanged because `normalize` hits the `(t raw-alist)` default arm.

- [ ] **Step 3.3: Implement the normalizer**

In `lisp/a3madkour-publish-poetry.el`, append before the `(provide ...)`:

```elisp
(defconst a3madkour-pub-poetry--required-keys
  '(title date lastmod draft lines)
  "5 required frontmatter keys per check_works_fixtures.py poetry contract.")

(defconst a3madkour-pub-poetry--optional-keys
  '(tags collection set_to_music summary audio_url source_stream
         tile_size featured hero)
  "9 optional frontmatter keys per spec §Authoring + check_works_fixtures.py.")

(defun a3madkour-pub-poetry--allowed-keys ()
  "All keys allowed in the emitted poetry frontmatter."
  (append a3madkour-pub-poetry--required-keys
          a3madkour-pub-poetry--optional-keys))

(defun a3madkour-pub-frontmatter--normalize-works-poetry (raw-alist source-file)
  "Tier 8.2: works/poetry frontmatter normalizer.

Pipeline:
  1. Filter RAW-ALIST to only allowed keys (drops ox-hugo noise + essay-only keys).
  2. Coerce draft to bool (default nil).
  3. Default lines=0 (Task 4 wires real auto-counting via :body-line-count
     injected into raw-alist by the handler).
  4. Default summary=\"\" (linter requires the key; marker scrub lands in Task 7).
  5. audio_url passed through if present (Tasks 5-6 wire the #+AUDIO: keyword
     reader into raw-alist injection).

SOURCE-FILE is the original .org path (passed through for parity with
peer normalizers; this normalizer does not yet read it, but Tasks 4-7
may extend it to do so via `a3madkour-pub-frontmatter--read-org-keyword')."
  (ignore source-file)
  (let* ((allowed (a3madkour-pub-poetry--allowed-keys))
         (out (cl-remove-if-not
               (lambda (cell) (memq (car cell) allowed))
               (copy-tree raw-alist))))
    ;; Default draft → nil (false)
    (setf (alist-get 'draft out) (and (alist-get 'draft out) t))
    ;; Default lines → 0 (Task 4 will inject :body-line-count and use it)
    (unless (alist-get 'lines out)
      (setf (alist-get 'lines out) 0))
    ;; Default summary → "" (linter requires key)
    (unless (alist-get 'summary out)
      (setf (alist-get 'summary out) ""))
    out))
```

- [ ] **Step 3.4: Add the dispatch arm**

Edit `lisp/a3madkour-publish-frontmatter.el:58-89`. In the `cond` inside `a3madkour-pub-frontmatter/normalize`, add a new arm before the default:

```elisp
   ((eq section 'research-questions)
    (a3madkour-pub-frontmatter--normalize-research-question raw-alist source-file))
   ((eq section 'works-poetry)                              ;; NEW
    (a3madkour-pub-frontmatter--normalize-works-poetry raw-alist source-file))   ;; NEW
   ;; ... (t raw-alist)
```

Also add an autoload-style requires at the top of `a3madkour-publish-frontmatter.el` if peer normalizers do (essays uses `(require 'a3madkour-publish-essays)` for `--merge-has-flags`). Poetry's normalizer is self-contained, so no extra require here.

- [ ] **Step 3.5: Run; verify PASS**

Run: `./run-tests.sh -t '^a3madkour-pub-poetry-test/normalize-passes-through-allowed-keys$'`
Expected: PASS.

- [ ] **Step 3.6: Run the full suite; verify no regressions**

Run: `./run-tests.sh`
Expected: 665 + 1 = 666 tests, 0 failed.

- [ ] **Step 3.7: Commit**

```bash
cd /Users/a3madkour/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el \
        emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el \
        emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el
git commit -m "feat(poetry): frontmatter normalizer + dispatch arm — key allowlist (req=5, opt=9)"
```

---

## Task 4: Auto-count `lines:` from emitted markdown body

**Files:**
- Modify: `lisp/a3madkour-publish-poetry.el` (add `--count-poem-lines`)
- Modify: `lisp/a3madkour-publish-poetry-test.el`

- [ ] **Step 4.1: Write the failing tests**

Append:

```elisp
(ert-deftest a3madkour-pub-poetry-test/lines-counter-basic ()
  "Counts non-blank lines; stanza breaks excluded."
  (let ((body "[00:01]Lorem [00:02]ipsum [00:03]dolor [00:04]sit
[00:05]amet [00:06]consectetur [00:07]adipiscing [00:08]elit

[00:09]sed [00:10]do [00:11]eiusmod [00:12]tempor
[00:13]incididunt [00:14]ut [00:15]labore [00:16]dolore

[00:17]Duis aute *irure* reprehenderit

[00:18]ut [00:19]enim \\[00:99] [00:20]minim [00:21]veniam"))
    (should (= (a3madkour-pub-poetry--count-poem-lines body) 6))))

(ert-deftest a3madkour-pub-poetry-test/lines-counter-marker-only-line-counts ()
  "A line containing only a `[mm:ss]' marker still counts."
  (let ((body "[00:01]Lorem
[00:17]
[00:18]veniam"))
    (should (= (a3madkour-pub-poetry--count-poem-lines body) 3))))

(ert-deftest a3madkour-pub-poetry-test/lines-counter-skips-leading-h2 ()
  "A leading H2 (e.g. `## Title') is excluded from the count."
  (let ((body "## Untitled Poem

[00:01]Lorem
[00:02]ipsum"))
    (should (= (a3madkour-pub-poetry--count-poem-lines body) 2))))

(ert-deftest a3madkour-pub-poetry-test/lines-counter-empty-body ()
  "Empty body → 0."
  (should (= (a3madkour-pub-poetry--count-poem-lines "") 0))
  (should (= (a3madkour-pub-poetry--count-poem-lines "   \n\n   \n") 0)))
```

- [ ] **Step 4.2: Run; expect FAIL (function undefined)**

Run: `./run-tests.sh -t '^a3madkour-pub-poetry-test/lines-counter-'`
Expected: FAIL — "Symbol's function definition is void: a3madkour-pub-poetry--count-poem-lines".

- [ ] **Step 4.3: Implement the counter**

Append to `a3madkour-publish-poetry.el`, before `(provide ...)`:

```elisp
(defun a3madkour-pub-poetry--count-poem-lines (body)
  "Return the count of non-blank poem lines in markdown BODY.

Rules:
  - Stanza-break blank lines excluded.
  - Lines with only `[mm:ss]' markers still count.
  - A leading H2 (line matching `## ...') is excluded.

Used by the handler to inject `:body-line-count' into the raw frontmatter
alist; the normalizer reads it as `lines:'."
  (let* ((lines (split-string (or body "") "\n"))
         (stripped (if (and lines
                            (string-match-p "\\`##[ \t]" (car lines)))
                       (cdr lines)
                     lines)))
    (cl-count-if (lambda (l) (not (string-blank-p l))) stripped)))
```

- [ ] **Step 4.4: Wire the count into the normalizer**

Edit `a3madkour-publish-poetry.el`. Replace the `lines:` default block in `a3madkour-pub-frontmatter--normalize-works-poetry`:

```elisp
    ;; lines: prefer caller-injected :body-line-count, else explicit lines,
    ;; else 0 (caught by linter when handler forgets to inject).
    (let ((injected (alist-get :body-line-count raw-alist)))
      (when injected
        (setf (alist-get 'lines out) injected)))
    (unless (alist-get 'lines out)
      (setf (alist-get 'lines out) 0))
    (setq out (assq-delete-all :body-line-count out))
```

Add a normalizer test that uses the injection path:

```elisp
(ert-deftest a3madkour-pub-poetry-test/normalize-uses-injected-line-count ()
  "Normalizer reads `:body-line-count' from raw-alist and emits `lines:'."
  (let* ((raw '((title . "T") (date . "2026-06-12") (lastmod . "2026-06-12")
                (draft . nil) (:body-line-count . 6)))
         (out (a3madkour-pub-frontmatter/normalize 'works-poetry raw nil)))
    (should (= (alist-get 'lines out) 6))
    (should-not (assq :body-line-count out))))
```

- [ ] **Step 4.5: Run; verify all pass**

Run: `./run-tests.sh -t '^a3madkour-pub-poetry-test/'`
Expected: all current poetry tests PASS.

- [ ] **Step 4.6: Commit**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el \
        emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el
git commit -m "feat(poetry): auto-count lines: from emitted markdown body"
```

---

## Task 5: `#+AUDIO:` keyword reader — absolute URL form

**Files:**
- Modify: `lisp/a3madkour-publish-poetry.el`
- Modify: `lisp/a3madkour-publish-poetry-test.el`

- [ ] **Step 5.1: Write the failing tests (URL form only — relative file path goes in Task 6)**

Append:

```elisp
(ert-deftest a3madkour-pub-poetry-test/audio-classify-absolute-https ()
  "An absolute https:// URL classifies as :url."
  (let ((c (a3madkour-pub-poetry--classify-audio "https://example.com/r.mp3")))
    (should (equal (plist-get c :kind) :url))
    (should (equal (plist-get c :value) "https://example.com/r.mp3"))))

(ert-deftest a3madkour-pub-poetry-test/audio-classify-absolute-http ()
  "An absolute http:// URL classifies as :url."
  (let ((c (a3madkour-pub-poetry--classify-audio "http://example.com/r.mp3")))
    (should (equal (plist-get c :kind) :url))))

(ert-deftest a3madkour-pub-poetry-test/audio-classify-relative-filename ()
  "A bare filename classifies as :file."
  (let ((c (a3madkour-pub-poetry--classify-audio "reading.mp3")))
    (should (equal (plist-get c :kind) :file))
    (should (equal (plist-get c :value) "reading.mp3"))))

(ert-deftest a3madkour-pub-poetry-test/audio-classify-empty ()
  "Empty / nil input → nil."
  (should-not (a3madkour-pub-poetry--classify-audio nil))
  (should-not (a3madkour-pub-poetry--classify-audio ""))
  (should-not (a3madkour-pub-poetry--classify-audio "   ")))
```

- [ ] **Step 5.2: Run; expect FAIL**

Run: `./run-tests.sh -t '^a3madkour-pub-poetry-test/audio-classify-'`
Expected: FAIL — function void.

- [ ] **Step 5.3: Implement the classifier**

Append to `a3madkour-publish-poetry.el`, before `(provide ...)`:

```elisp
(defun a3madkour-pub-poetry--classify-audio (raw)
  "Classify the value of an `#+AUDIO:' keyword.

Return nil for nil/empty input.  Otherwise return a plist:
  (:kind :url  :value <trimmed-url>)   for `http(s)://...'
  (:kind :file :value <trimmed-name>)  for bare filenames"
  (when (and raw (stringp raw))
    (let ((v (string-trim raw)))
      (cond
       ((string-empty-p v) nil)
       ((string-match-p "\\`https?://" v) (list :kind :url :value v))
       (t                                 (list :kind :file :value v))))))
```

- [ ] **Step 5.4: Add a handler-side reader test (keyword extraction → classification → frontmatter injection)**

Append:

```elisp
(ert-deftest a3madkour-pub-poetry-test/audio-keyword-absolute-emission ()
  "`#+AUDIO: https://...' → frontmatter `audio_url:' set to the URL; no asset copy."
  (let* ((raw '((title . "T") (date . "2026-06-12") (lastmod . "2026-06-12")
                (draft . nil) (:body-line-count . 1)
                (audio_url . "https://example.com/reading.mp3")))
         (out (a3madkour-pub-frontmatter/normalize 'works-poetry raw nil)))
    (should (equal (alist-get 'audio_url out)
                   "https://example.com/reading.mp3"))))
```

- [ ] **Step 5.5: Run; verify all pass**

Expected: PASS.

- [ ] **Step 5.6: Commit**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el \
        emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el
git commit -m "feat(poetry): #+AUDIO: keyword classifier (URL vs file)"
```

---

## Task 6: Audio asset copy — relative filename form (+ Case C escape collapse)

**Files:**
- Modify: `lisp/a3madkour-publish-poetry.el`
- Modify: `lisp/a3madkour-publish-poetry-test.el`

**Task 0 recon outcome (recorded 2026-06-12): Case C.** ox-hugo doubles the backslash — org `\[00:99]` is emitted as markdown `\\[00:99]`. The runtime parser (`layouts/partials/works/synced-text-parser.html:21`) only matches `\[mm:ss]` (one backslash); given `\\[00:99]` it eats the second `\`+`[…]` as the escape sentinel and leaves a stray first `\` in rendered output. Fix: post-export, collapse every `\\[mm:ss]` substring to `\[mm:ss]` before writing `index.md`. This restores the shipped fixture's escape shape byte-for-byte. Step 6.4 below implements this; Step 6.5 adds the regression test.

- [ ] **Step 6.1: Write the failing tests**

Append:

```elisp
(ert-deftest a3madkour-pub-poetry-test/copy-audio-asset-success ()
  "Relative `#+AUDIO:' filename → file copied from poetry-dir/assets/<id>/ to bundle."
  (let* ((src-id (format "33333333-3333-3333-3333-%012d" (random 1000000)))
         (poetry-root (make-temp-file "poetry-src-" t))
         (bundle-dir (make-temp-file "poetry-bundle-" t))
         (src-assets (expand-file-name (format "assets/%s/" src-id) poetry-root))
         (src-audio (expand-file-name "reading.mp3" src-assets)))
    (make-directory src-assets t)
    (with-temp-file src-audio (insert "ID3" (make-string 64 ?x)))   ; non-zero
    (let ((a3madkour-pub/poetry-dir poetry-root))
      (a3madkour-pub-poetry--copy-audio-asset src-id "reading.mp3" bundle-dir))
    (should (file-exists-p (expand-file-name "reading.mp3" bundle-dir)))
    (delete-directory poetry-root t)
    (delete-directory bundle-dir t)))

(ert-deftest a3madkour-pub-poetry-test/copy-audio-asset-missing-file ()
  "Missing source file → signals `user-error'."
  (let* ((src-id "44444444-4444-4444-4444-444444444444")
         (poetry-root (make-temp-file "poetry-src-" t))
         (bundle-dir (make-temp-file "poetry-bundle-" t)))
    (let ((a3madkour-pub/poetry-dir poetry-root))
      (should-error
       (a3madkour-pub-poetry--copy-audio-asset src-id "nope.mp3" bundle-dir)
       :type 'user-error))
    (delete-directory poetry-root t)
    (delete-directory bundle-dir t)))

(ert-deftest a3madkour-pub-poetry-test/copy-audio-asset-bad-extension ()
  "Disallowed extension → signals `user-error', no copy attempted."
  (let* ((src-id "55555555-5555-5555-5555-555555555555")
         (poetry-root (make-temp-file "poetry-src-" t))
         (bundle-dir (make-temp-file "poetry-bundle-" t))
         (src-assets (expand-file-name (format "assets/%s/" src-id) poetry-root)))
    (make-directory src-assets t)
    (with-temp-file (expand-file-name "notes.txt" src-assets) (insert "x"))
    (let ((a3madkour-pub/poetry-dir poetry-root))
      (should-error
       (a3madkour-pub-poetry--copy-audio-asset src-id "notes.txt" bundle-dir)
       :type 'user-error))
    (delete-directory poetry-root t)
    (delete-directory bundle-dir t)))

(ert-deftest a3madkour-pub-poetry-test/copy-audio-asset-zero-byte ()
  "Zero-byte file → signals `user-error'."
  (let* ((src-id "66666666-6666-6666-6666-666666666666")
         (poetry-root (make-temp-file "poetry-src-" t))
         (bundle-dir (make-temp-file "poetry-bundle-" t))
         (src-assets (expand-file-name (format "assets/%s/" src-id) poetry-root)))
    (make-directory src-assets t)
    (with-temp-file (expand-file-name "empty.mp3" src-assets))   ; zero bytes
    (let ((a3madkour-pub/poetry-dir poetry-root))
      (should-error
       (a3madkour-pub-poetry--copy-audio-asset src-id "empty.mp3" bundle-dir)
       :type 'user-error))
    (delete-directory poetry-root t)
    (delete-directory bundle-dir t)))
```

- [ ] **Step 6.2: Run; expect FAIL**

Expected: FAIL — function void.

- [ ] **Step 6.3: Implement the copier**

Append to `a3madkour-publish-poetry.el`:

```elisp
(defun a3madkour-pub-poetry--copy-audio-asset (id filename bundle-dest-dir)
  "Copy `<poetry-dir>/assets/ID/FILENAME' → `BUNDLE-DEST-DIR/FILENAME'.

Validates:
  - Extension is in `a3madkour-pub-poetry--audio-extensions'.
  - Source file exists.
  - Source file is non-zero bytes.

Signals `user-error' on any validation failure.  Returns FILENAME on
success.  Creates BUNDLE-DEST-DIR if missing."
  (let* ((ext (file-name-extension filename))
         (src (expand-file-name (format "assets/%s/%s" id filename)
                                a3madkour-pub/poetry-dir))
         (dest (expand-file-name filename bundle-dest-dir)))
    (unless (and ext (member (downcase ext) a3madkour-pub-poetry--audio-extensions))
      (user-error "a3madkour-pub-poetry: #+AUDIO: extension %S not in allowlist %S"
                  ext a3madkour-pub-poetry--audio-extensions))
    (unless (file-exists-p src)
      (user-error "a3madkour-pub-poetry: #+AUDIO: source file not found: %s" src))
    (let ((size (nth 7 (file-attributes src))))
      (unless (and size (> size 0))
        (user-error "a3madkour-pub-poetry: #+AUDIO: source file is empty: %s" src)))
    (make-directory bundle-dest-dir t)
    (copy-file src dest t)
    filename))
```

- [ ] **Step 6.4: Add Case C escape collapse helper**

Append to `a3madkour-publish-poetry.el`, before `(provide ...)`:

```elisp
(defun a3madkour-pub-poetry--collapse-escaped-markers (md)
  "Collapse double-backslash escape sequences ox-hugo emits.

Task 0 recon outcome: org-source `\\[mm:ss]' (single backslash) is emitted
by ox-hugo as markdown `\\\\[mm:ss]' (double backslash).  The runtime
parser (layouts/partials/works/synced-text-parser.html:21) matches only
the single-backslash form; the doubled form leaves a stray backslash in
rendered output.  This helper restores the single-backslash shape that
the parser + shipped fixture expect."
  (replace-regexp-in-string
   "\\\\\\\\\\(\\[[0-9]\\{1,2\\}:[0-9]\\{2\\}\\(?:\\.[0-9]\\{1,2\\}\\)?\\]\\)"
   "\\\\\\1"
   md t))
```

The regex in Emacs syntax (`\\\\\\\\\[…\\]` = `\\\\\[…\]`): four backslashes match two literal backslashes (one is the markdown double-escape, one is consumed by Elisp string literal escaping), followed by the `[mm:ss]` capture. Replacement is `\\\1` = `\` + group 1 = single backslash + `[mm:ss]`.

Append regression tests:

```elisp
(ert-deftest a3madkour-pub-poetry-test/collapse-double-backslash-escape ()
  "ox-hugo Case C output `\\\\[mm:ss]' collapses to `\\[mm:ss]'."
  (let ((md "[00:18]ut [00:19]enim \\\\[00:99] [00:20]minim"))
    (should (equal (a3madkour-pub-poetry--collapse-escaped-markers md)
                   "[00:18]ut [00:19]enim \\[00:99] [00:20]minim"))))

(ert-deftest a3madkour-pub-poetry-test/collapse-leaves-bare-markers-alone ()
  "Bare `[mm:ss]' (no leading backslash) is untouched."
  (let ((md "[00:01]Lorem [00:02]ipsum"))
    (should (equal (a3madkour-pub-poetry--collapse-escaped-markers md) md))))

(ert-deftest a3madkour-pub-poetry-test/collapse-leaves-single-backslash-alone ()
  "An already-single-backslash escape `\\[mm:ss]' is left untouched."
  (let ((md "[00:18]ut \\[00:99] [00:20]minim"))
    (should (equal (a3madkour-pub-poetry--collapse-escaped-markers md) md))))
```

- [ ] **Step 6.5: Run; verify all pass**

Expected: PASS.

- [ ] **Step 6.6: Commit**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el \
        emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el
git commit -m "feat(poetry): audio-asset copy helper (extension + existence + non-zero validation)"
```

---

## Task 7: Summary marker scrub

**Files:**
- Modify: `lisp/a3madkour-publish-poetry.el`
- Modify: `lisp/a3madkour-publish-poetry-test.el`

- [ ] **Step 7.1: Write the failing test**

Append:

```elisp
(ert-deftest a3madkour-pub-poetry-test/summary-marker-scrub ()
  "Summary containing `[mm:ss]' or `\\[mm:ss]' substrings has them stripped."
  (let* ((raw '((title . "T") (date . "2026-06-12") (lastmod . "2026-06-12")
                (draft . nil) (:body-line-count . 1)
                (summary . "Example [00:08]ipsum poem with \\[00:99] literal.")))
         (out (a3madkour-pub-frontmatter/normalize 'works-poetry raw nil)))
    (should (equal (alist-get 'summary out)
                   "Example ipsum poem with  literal."))))

(ert-deftest a3madkour-pub-poetry-test/summary-empty-preserved ()
  "Empty / missing summary stays empty."
  (let* ((raw '((title . "T") (date . "2026-06-12") (lastmod . "2026-06-12")
                (draft . nil) (:body-line-count . 1)))
         (out (a3madkour-pub-frontmatter/normalize 'works-poetry raw nil)))
    (should (equal (alist-get 'summary out) ""))))
```

- [ ] **Step 7.2: Run; expect FAIL on the first test (no scrub yet)**

Expected: FAIL — summary returned with markers intact.

- [ ] **Step 7.3: Implement the scrub helper and wire into normalizer**

Append to `a3madkour-publish-poetry.el`:

```elisp
(defconst a3madkour-pub-poetry--marker-regexp
  "\\\\?\\[[0-9]\\{1,2\\}:[0-9]\\{2\\}\\(?:\\.[0-9]\\{1,2\\}\\)?\\]"
  "Matches `[mm:ss]', `[mm:ss.f]', `\\[mm:ss]', `\\[mm:ss.f]'.
Used to scrub timing markers from `summary:' values.")

(defun a3madkour-pub-poetry--scrub-markers (s)
  "Return S with all `[mm:ss]'-shaped markers removed.
Returns nil for nil input."
  (when s
    (replace-regexp-in-string a3madkour-pub-poetry--marker-regexp "" s t t)))
```

In `a3madkour-pub-frontmatter--normalize-works-poetry`, replace the summary default block:

```elisp
    ;; summary: scrub timing markers (per spec §6); default "" if missing.
    (let ((s (alist-get 'summary out)))
      (setf (alist-get 'summary out)
            (or (a3madkour-pub-poetry--scrub-markers s) "")))
```

- [ ] **Step 7.4: Run; verify PASS**

Expected: PASS.

- [ ] **Step 7.5: Commit**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el \
        emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el
git commit -m "feat(poetry): scrub [mm:ss] markers from summary frontmatter"
```

---

## Task 8: Soft warnings — markers vs audio_url mismatches

**Files:**
- Modify: `lisp/a3madkour-publish-poetry.el`
- Modify: `lisp/a3madkour-publish-poetry-test.el`

- [ ] **Step 8.1: Write the failing tests**

Append:

```elisp
(ert-deftest a3madkour-pub-poetry-test/soft-warn-audio-without-markers ()
  "#+AUDIO: set, body has zero markers → soft warning surfaced."
  (let ((warnings (a3madkour-pub-poetry--collect-warnings
                   "Plain poem with no timings"
                   "reading.mp3")))
    (should (cl-some (lambda (w) (string-match-p "isn't timed" w)) warnings))))

(ert-deftest a3madkour-pub-poetry-test/soft-warn-markers-without-audio ()
  "Body has markers, #+AUDIO: absent → soft warning surfaced."
  (let ((warnings (a3madkour-pub-poetry--collect-warnings
                   "[00:01]Lorem [00:02]ipsum"
                   nil)))
    (should (cl-some (lambda (w) (string-match-p "animation-driven sync" w))
                     warnings))))

(ert-deftest a3madkour-pub-poetry-test/soft-warn-both-present-quiet ()
  "Markers + audio → no soft warnings."
  (should (null (a3madkour-pub-poetry--collect-warnings
                 "[00:01]Lorem [00:02]ipsum"
                 "reading.mp3"))))

(ert-deftest a3madkour-pub-poetry-test/soft-warn-both-absent-quiet ()
  "No markers, no audio (plain poem) → no soft warnings."
  (should (null (a3madkour-pub-poetry--collect-warnings
                 "Plain poem"
                 nil))))
```

- [ ] **Step 8.2: Run; expect FAIL**

Expected: FAIL — function void.

- [ ] **Step 8.3: Implement the warnings collector**

Append to `a3madkour-publish-poetry.el`:

```elisp
(defun a3madkour-pub-poetry--body-has-markers-p (body)
  "Non-nil if BODY contains at least one `[mm:ss]' marker (unescaped).
Treats `\\[mm:ss]' as escaped (literal) and excludes it."
  (and body
       (let ((case-fold-search nil))
         (string-match-p
          ;; Negative lookbehind isn't supported in elisp; emulate by requiring
          ;; the char before [mm:ss] to be either start-of-line, whitespace, or
          ;; nothing (and not a backslash).  Use a non-capturing leading group.
          "\\(?:^\\|[^\\\\]\\)\\[[0-9]\\{1,2\\}:[0-9]\\{2\\}\\(?:\\.[0-9]\\{1,2\\}\\)?\\]"
          body))))

(defun a3madkour-pub-poetry--collect-warnings (body audio-raw)
  "Return the list of soft-warning strings for BODY + AUDIO-RAW.
AUDIO-RAW is the raw `#+AUDIO:' keyword value (string or nil)."
  (let ((warnings nil)
        (has-markers (a3madkour-pub-poetry--body-has-markers-p body))
        (has-audio   (and audio-raw (not (string-blank-p audio-raw)))))
    (cond
     ((and has-audio (not has-markers))
      (push "#+AUDIO: declared but the poem isn't timed — the synced runtime won't engage."
            warnings))
     ((and has-markers (not has-audio))
      (push "Body has [mm:ss] markers but no #+AUDIO: — the runtime will use animation-driven sync."
            warnings)))
    (nreverse warnings)))
```

- [ ] **Step 8.4: Run; verify PASS**

Expected: PASS.

- [ ] **Step 8.5: Commit**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el \
        emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el
git commit -m "feat(poetry): soft warnings for marker/audio mismatch (audio-without-markers, markers-without-audio)"
```

---

## Task 9: `#+multi_export: t` warn-and-skip on poetry

**Files:**
- Modify: `lisp/a3madkour-publish-poetry.el`
- Modify: `lisp/a3madkour-publish-poetry-test.el`

- [ ] **Step 9.1: Write the failing test**

Append:

```elisp
(ert-deftest a3madkour-pub-poetry-test/multi-export-warn-and-skip ()
  "`#+multi_export: t' on a poem → warning surfaced, D.2 dispatch not invoked."
  (let* ((dispatched nil)
         (file (make-temp-file "poetry-multi-" nil ".org"
                               ":PROPERTIES:\n:ID: 77777777-7777-7777-7777-777777777777\n:END:\n#+TITLE: T\n#+HUGO_SECTION: works/poetry\n#+multi_export: t\n\n[00:01]hi\n")))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub-multi/dispatch-export)
                   (lambda (&rest _args) (setq dispatched t))))
          (let ((warnings (a3madkour-pub-poetry--maybe-warn-multi-export file)))
            (should (cl-some (lambda (w) (string-match-p "multi_export" w)) warnings))
            (should-not dispatched)))
      (delete-file file))))
```

- [ ] **Step 9.2: Run; expect FAIL**

Expected: FAIL — function void.

- [ ] **Step 9.3: Implement the check**

Append to `a3madkour-publish-poetry.el`:

```elisp
(defun a3madkour-pub-poetry--maybe-warn-multi-export (file)
  "Return a warning list iff FILE has `#+multi_export: t' (poetry doesn't support it).
Returns nil otherwise.  D.2 dispatch is never invoked on poetry."
  (with-temp-buffer
    (insert-file-contents file)
    (when (a3madkour-pub-keywords/boolean-p
           (a3madkour-pub-keywords/extract "multi_export"))
      (list "#+multi_export: t set on a poem — D.2 PDF/Word target shape doesn't exist for synced poetry; ignoring."))))
```

- [ ] **Step 9.4: Run; verify PASS**

Expected: PASS.

- [ ] **Step 9.5: Commit**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el \
        emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el
git commit -m "feat(poetry): warn-and-skip on #+multi_export: t (D.2 inapplicable to synced poetry)"
```

---

## Task 10: Wire the handler entry point — `a3madkour-pub-poetry/publish-poetry-file`

This is the integration point. The previous tasks built the pieces; this stage orchestrates them in the 6-stage pipeline.

**Files:**
- Modify: `lisp/a3madkour-publish-poetry.el`
- Modify: `lisp/a3madkour-publish-poetry-test.el`

- [ ] **Step 10.1: Write the failing integration test (in-process)**

Append:

```elisp
(ert-deftest a3madkour-pub-poetry-test/handler-end-to-end-in-process ()
  "Round-trip: build a tmp corpus, publish a poem, assert emitted bytes + manifest.
Uses a fake mp3 (non-zero bytes) for the audio asset.  Does NOT call run-tests.sh
or hugo — pure in-process emacs."
  (let* ((id "88888888-8888-8888-8888-888888888888")
         (slug "test-poem")
         (poetry-root (make-temp-file "poetry-corpus-" t))
         (site-root   (make-temp-file "poetry-site-" t))
         (org-file (expand-file-name (format "%s.org" slug) poetry-root))
         (assets-dir (expand-file-name (format "assets/%s/" id) poetry-root))
         (audio-file (expand-file-name "reading.mp3" assets-dir)))
    (make-directory assets-dir t)
    (with-temp-file audio-file (insert "ID3" (make-string 256 ?x)))
    (with-temp-file org-file
      (insert ":PROPERTIES:\n:ID:       " id "\n:END:\n")
      (insert "#+TITLE: Test Poem\n")
      (insert "#+DATE: 2026-06-12\n")
      (insert "#+HUGO_SECTION: works/poetry\n")
      (insert "#+HUGO_PUBLISH: t\n")
      (insert "#+AUDIO: reading.mp3\n")
      (insert "\n")
      (insert "[00:01]Lorem [00:02]ipsum\n")
      (insert "[00:17]Duis aute\n"))
    (unwind-protect
        (let* ((a3madkour-pub/poetry-dir poetry-root)
               (a3madkour-pub/site-data-dir (expand-file-name "data/" site-root))
               (a3madkour-pub-poetry/section-dir-name "works/poetry")
               (result (a3madkour-pub-poetry/publish-poetry-file
                        org-file nil :on-done #'ignore))
               (bundle-dir (expand-file-name
                            (format "content/works/poetry/%s/" slug) site-root))
               (index-md (expand-file-name "index.md" bundle-dir))
               (bundled-audio (expand-file-name "reading.mp3" bundle-dir)))
          (should (file-exists-p index-md))
          (should (file-exists-p bundled-audio))
          (let ((emitted (with-temp-buffer (insert-file-contents index-md) (buffer-string))))
            (should (string-match-p "audio_url: \"reading.mp3\"" emitted))
            (should (string-match-p "lines: 2" emitted))
            (should (string-match-p "\\[00:01\\]Lorem \\[00:02\\]ipsum" emitted))))
      (delete-directory poetry-root t)
      (delete-directory site-root t))))
```

- [ ] **Step 10.2: Run; expect FAIL (handler still stubbed)**

Expected: FAIL — `(error "a3madkour-pub-poetry/publish-poetry-file: not yet implemented (Task 10)")`.

- [ ] **Step 10.3: Replace the stub with the real pipeline**

In `lisp/a3madkour-publish-poetry.el`, replace the entire stub body of `a3madkour-pub-poetry/publish-poetry-file` with:

```elisp
(defun a3madkour-pub-poetry--site-root ()
  "Resolve the site root from `a3madkour-pub/site-data-dir' (one level up from data/)."
  (file-name-as-directory
   (file-name-directory (directory-file-name a3madkour-pub/site-data-dir))))

(cl-defun a3madkour-pub-poetry/publish-poetry-file (file run &key on-done)
  "Publish a single poem FILE to `content/works/poetry/<slug>/index.md'.

Pipeline:
  1. Resolve metadata (id / slug).
  2. Soft-warning sweep (multi_export + marker/audio mismatch); collect for result.
  3. Pre-export rewrite via shared rewrite-to-tmp-file.
  4. ox-hugo export → markdown buffer.
  5. Read `#+AUDIO:'; classify; if relative, copy to bundle; inject `audio_url'.
  6. Normalize via 'works-poetry dispatch arm (injects lines, scrubs summary).
  7. Render frontmatter + body; write if different.
  8. record-publish.

RUN is the a3-pub-async-run handle (currently unused; reserved for parity
with peer handlers).  ON-DONE is invoked with 'ok on completion or 'err on
failure.

Returns a plist:
  (:status 'ok|'err  :id ID  :slug SLUG  :url URL  :warnings (...))"
  (ignore run)
  (let ((warnings nil))
    (condition-case err
        (let* ((md         (a3madkour-pub/note-metadata file))
               (id         (plist-get md :id))
               (slug       (plist-get md :slug))
               (new-url    (a3madkour-pub/note-url file))
               (site-root  (a3madkour-pub-poetry--site-root))
               (bundle-dir (expand-file-name
                            (format "content/%s/%s/"
                                    a3madkour-pub-poetry/section-dir-name slug)
                            site-root))
               (audio-raw  (with-temp-buffer
                             (insert-file-contents file)
                             (a3madkour-pub-keywords/extract "AUDIO")))
               (audio-class (a3madkour-pub-poetry--classify-audio audio-raw)))
          ;; Stage 2: multi_export warn-and-skip.
          (setq warnings
                (append warnings
                        (a3madkour-pub-poetry--maybe-warn-multi-export file)))
          ;; Stage 3: pre-export rewrite.
          (let* ((tmp-file (a3madkour-pub-rewrite/rewrite-to-tmp-file file))
                 ;; Stage 4: ox-hugo export to markdown buffer.
                 (export-result (a3madkour-pub-export/export-file tmp-file))
                 (md-buffer (plist-get export-result :buffer))
                 (raw-fm    (plist-get export-result :frontmatter))
                 ;; Case C: collapse `\\[mm:ss]' → `\[mm:ss]' before downstream use.
                 (body      (a3madkour-pub-poetry--collapse-escaped-markers
                             (with-current-buffer md-buffer (buffer-string)))))
            ;; Stage 5: audio asset copy (relative form only).
            (when (and audio-class (eq (plist-get audio-class :kind) :file))
              (a3madkour-pub-poetry--copy-audio-asset
               id (plist-get audio-class :value) bundle-dir))
            ;; Stage 5b: inject audio_url + line-count into raw-fm.
            (when audio-class
              (setf (alist-get 'audio_url raw-fm) (plist-get audio-class :value)))
            (setf (alist-get :body-line-count raw-fm)
                  (a3madkour-pub-poetry--count-poem-lines body))
            ;; Stage 5c: soft warnings re. marker/audio mismatch.
            (setq warnings
                  (append warnings
                          (a3madkour-pub-poetry--collect-warnings body audio-raw)))
            ;; Stage 6: normalize.
            (let* ((normalized (a3madkour-pub-frontmatter/normalize
                                'works-poetry raw-fm file))
                   ;; Stage 7: render + write.
                   (rendered (a3madkour-pub-frontmatter/render
                              normalized body))
                   (index-md (expand-file-name "index.md" bundle-dir)))
              (make-directory bundle-dir t)
              (a3madkour-pub--write-if-different index-md rendered)
              ;; Stage 7b: shared asset pipeline (body-link assets, if any).
              (a3madkour-pub/asset-validate-and-copy file bundle-dir id nil)
              ;; Stage 8: record-publish.
              (a3madkour-pub-history/record-publish id new-url 'live)
              (when on-done (funcall on-done 'ok))
              (list :status 'ok :id id :slug slug :url new-url :warnings warnings))))
      (error
       (when on-done (funcall on-done 'err))
       (list :status 'err
             :id nil :slug nil :url nil
             :warnings warnings
             :error (error-message-string err))))))
```

If `a3madkour-pub-frontmatter/render` or `a3madkour-pub--write-if-different` don't exist with exactly these names, grep dotfiles for the existing render/write helpers used by essays and substitute them. Do not invent new helpers.

- [ ] **Step 10.4: Run the end-to-end test; verify PASS**

Run: `./run-tests.sh -t 'a3madkour-pub-poetry-test/handler-end-to-end-in-process'`
Expected: PASS.

Expect to debug 1-3 wiring issues here — this is the integration point. Likely failure modes:

- Helper name mismatch (e.g. `render-frontmatter` vs `frontmatter/render`). Grep essays handler for the exact names and substitute.
- `audio_url` rendering as `'\"…\"'` (single-quote-escaped) — check render output and tighten the regex assertion if needed.
- `note-url` returning a path with `works/poetry` instead of `works/poetry/`. If so, override the URL computation in poetry handler analogously to essays.

For each wiring issue: read the error, find the actual symbol/shape in dotfiles, adjust the handler, re-run.

- [ ] **Step 10.5: Run the full suite; verify no regressions**

Run: `./run-tests.sh`
Expected: full suite, 0 failed. Target: 662 + ~14 new = ~676 tests.

- [ ] **Step 10.6: Commit**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-poetry.el \
        emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el
git commit -m "feat(poetry): wire handler entry point — 6-stage pipeline, end-to-end in-process test"
```

---

## Task 11: Subprocess integration test (site repo Python suite)

**Files:**
- Modify: `tools/test_publish_integration.py` (site repo)

This task exercises the full `a3-pub.sh --publish-deliberate` shell path against a tmpdir corpus, then runs both site-side linters on the emitted bundle. Mirrors B.4's integration test pattern.

- [ ] **Step 11.1: Find the existing test class layout**

Read `tools/test_publish_integration.py` end to end. Find the class or test-runner pattern used for essays. Copy that pattern for poetry.

- [ ] **Step 11.2: Write the failing test**

Append a new test class at the bottom of `tools/test_publish_integration.py`. Concrete sketch (adapt the helper names to whatever the file currently uses):

```python
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

class PoetryPublishIntegrationTest(unittest.TestCase):
    """End-to-end: a3-pub.sh --publish-deliberate against a tmp poetry corpus."""

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="poetry-int-"))
        self.org_root = self.tmpdir / "org" / "notes" / "works" / "poetry"
        self.site_root = self.tmpdir / "site"
        (self.site_root / "data").mkdir(parents=True)
        (self.site_root / "content").mkdir(parents=True)
        self.org_root.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_poem(self, slug: str, id_: str, audio_filename: str | None) -> Path:
        org = self.org_root / f"{slug}.org"
        audio_line = f"#+AUDIO: {audio_filename}\n" if audio_filename else ""
        org.write_text(
            f":PROPERTIES:\n:ID:       {id_}\n:END:\n"
            f"#+TITLE: {slug.title()}\n"
            f"#+DATE: 2026-06-12\n"
            f"#+HUGO_SECTION: works/poetry\n"
            f"#+HUGO_PUBLISH: t\n"
            f"{audio_line}"
            f"\n"
            f"[00:01]Lorem [00:02]ipsum\n"
            f"[00:17]Duis aute *irure* reprehenderit\n"
        )
        if audio_filename:
            assets = self.org_root / "assets" / id_
            assets.mkdir(parents=True)
            (assets / audio_filename).write_bytes(b"ID3" + b"x" * 1024)
        return org

    def test_round_trip_with_relative_audio(self):
        slug = "test-poem"
        id_ = "99999999-9999-9999-9999-999999999999"
        org = self._write_poem(slug, id_, "reading.mp3")

        env = os.environ.copy()
        env["A3_PUB_SITE_DATA_DIR"] = str(self.site_root / "data")
        # poetry-dir is a defcustom; override via --eval would be cleaner but
        # the deliberate command takes only a file path.  Symlink the org root
        # into the default location for the test, or set HOME → tmpdir.
        env["HOME"] = str(self.tmpdir / "fake-home")
        (self.tmpdir / "fake-home" / "notes" / "works" / "poetry").mkdir(parents=True)
        # Move the real org file + assets under the fake HOME path.
        # (See dotfiles/emacs-configs/custom/lisp/a3madkour-publish-poetry.el
        # for the `poetry-dir' defcustom shape — it defaults to ~/notes/works/poetry/.)
        shutil.copytree(
            self.org_root,
            Path(env["HOME"]) / "notes" / "works" / "poetry",
            dirs_exist_ok=True,
        )
        target_path = str(
            Path(env["HOME"]) / "notes" / "works" / "poetry" / f"{slug}.org"
        )

        result = subprocess.run(
            [
                "/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh",
                "--publish-deliberate",
                target_path,
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

        bundle = self.site_root / "content" / "works" / "poetry" / slug
        self.assertTrue((bundle / "index.md").exists())
        self.assertTrue((bundle / "reading.mp3").exists())

        emitted = (bundle / "index.md").read_text()
        self.assertIn('audio_url: "reading.mp3"', emitted)
        self.assertIn("lines: 2", emitted)
        self.assertIn("[00:01]Lorem [00:02]ipsum", emitted)

        # Run both site-side linters against the emitted bundle.
        for tool in ("check_poetry_synced.py", "check_works_fixtures.py"):
            lint = subprocess.run(
                ["python3", f"tools/{tool}"],
                cwd=str(self.site_root),  # linters typically scan `content/`
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(
                lint.returncode, 0,
                msg=f"{tool} failed:\n{lint.stdout}\n{lint.stderr}",
            )
```

The above sketch contains two pragmatic compromises that should be cleaned in code review: the `HOME=` override for `poetry-dir` is awkward, and the linter `cwd=` may need adjustment if the linters scan a hardcoded path. Verify by reading the linters' main blocks before settling on the test shape.

- [ ] **Step 11.3: Run the test**

Run from site repo root: `python3 tools/test_publish_integration.py PoetryPublishIntegrationTest`
Expected: PASS (after the wiring compromises above are resolved).

- [ ] **Step 11.4: Commit (site repo)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
git commit -m "test(poetry): subprocess integration test — a3-pub.sh round-trip + linter gates"
```

---

## Task 12: Closure — author + publish a real poem (manual gate)

This task is intentionally manual; it cannot be subagent-driven. The handler is shipped after Task 11, but per spec §Closure bar the slice closes only when a real authored poem with real timings + a real audio asset is live on master.

**Files:**
- Create: `~/org/notes/works/poetry/<your-real-slug>.org` (author)
- Create: `~/org/notes/works/poetry/assets/<id>/<your-real-audio>.mp3` (author + record)
- Create (via handler): `content/works/poetry/<your-real-slug>/index.md` + sibling audio file.

- [ ] **Step 12.1: Author content**

Write or select a real poem. Generate a fresh org-roam `:ID:` (`org-id-new` from an interactive Emacs buffer, or `uuidgen` from the shell). Save to `~/org/notes/works/poetry/<slug>.org` with the shape from spec §Authoring surface.

- [ ] **Step 12.2: Record / source audio**

Record or source a reading of the poem. Save to `~/org/notes/works/poetry/assets/<id>/<filename>.mp3` (or `.m4a` / `.ogg` / `.wav`). Time the audio against the poem in a separate Emacs session — listen + transcribe `[mm:ss]` markers into the org body.

- [ ] **Step 12.3: Publish via a3-pub.sh**

Run from anywhere:

```bash
/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh \
  --publish-deliberate \
  ~/org/notes/works/poetry/<slug>.org
```

- [ ] **Step 12.4: Verify locally**

Run from site repo:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
tools/ci-local.sh                          # site-side gates incl. poetry linters
hugo server --buildDrafts                  # dev server
```

Visit `http://localhost:1313/works/poetry/<slug>/`. Check:
1. Page renders.
2. Audio player chrome appears (since `audio_url:` set).
3. Pressing play reveals each word at its `[mm:ss]` timestamp.
4. `\[mm:ss]` literals render as `[mm:ss]` text (not timing events).
5. Mobile breakpoint (~960px wide per `[[feedback-test-at-half-screen-1080p]]`) lays out cleanly.

- [ ] **Step 12.5: Commit + push site repo**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add content/works/poetry/<slug>/  data/url-history.yaml
git commit -m "content(works/poetry): publish <slug> — first real synced poem closes Tier 8.2"
git push origin master
```

Wait for GitHub Actions to pass. Site deploys after green CI. Verify production `https://a3madkour.github.io/works/poetry/<slug>/` plays correctly.

- [ ] **Step 12.6: Update roadmap status**

Edit `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`. Mark Tier 8.2 row closed (mirror the format of Tier 1, 4, 5 closures: `✓` + `2026-06-XX` + commit hashes).

- [ ] **Step 12.7: Final commit (roadmap status)**

```bash
git add docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md
git commit -m "docs(roadmap): Tier 8.2 closed — org → synced-poetry export shipped"
git push origin master
```

---

## Verification matrix (full slice)

| Layer | Gate | How to run | Pass condition |
|---|---|---|---|
| Dotfiles unit | ert | `cd dotfiles/.../lisp && ./run-tests.sh` | 0 failed; total ~676 |
| Site repo unit | linters | `tools/ci-local.sh` | 0 failed |
| Subprocess integration | Python ut | `python3 tools/test_publish_integration.py PoetryPublishIntegrationTest` | 0 failed |
| Real-poem manual | author eye | `hugo server` + production smoke | Page renders, audio plays, markers reveal |
| CI | GHA | `git push origin master` | Green |

---

## Self-review notes

Already done by the plan author against spec §Tests + §Risks:

- Spec §Tests #1 (section-detection) → Task 2 ✓
- Spec §Tests #2 (lines-counter) → Task 4 ✓
- Spec §Tests #3 (audio-keyword-relative) → Task 6 ✓
- Spec §Tests #4 (audio-keyword-absolute) → Task 5 ✓
- Spec §Tests #5 (audio-missing-file) → Task 6 ✓
- Spec §Tests #6 (audio-bad-extension) → Task 6 ✓
- Spec §Tests #7 (summary-marker-scrub) → Task 7 ✓
- Spec §Tests #8 (normalize-key-allowlist) → Task 3 ✓
- Spec §Tests #9 (multi-export-warn-and-skip) → Task 9 ✓
- Spec §Tests #10 (soft-warning-audio-without-markers) → Task 8 ✓
- Spec §Tests #11 (soft-warning-markers-without-audio) → Task 8 ✓
- Spec §Tests #12 (round-trip dummy fixture) → Task 10 (in-process) + Task 11 (subprocess) ✓
- Spec §Risks #1 (ox-hugo backslash escape) → Task 0 + Task 6 conditional ✓
- Spec §Risks #2 (canonical keyword API) → Task 5 + Task 9 (both use `a3madkour-pub-keywords/extract`) ✓
- Spec §Risks #3 (page-bundle directory) → Task 10 wiring + Task 11 subprocess test ✓
- Spec §Risks #4 (url-history integration) → Task 10 (`record-publish` call) ✓
- Spec §Risks #5 (marker placement) → linter handles; no soft-warn added (per spec) ✓
- Spec §Risks #6 (per-poem asset dir bootstrap) → Task 6 raises on missing dir; no auto-create ✓
- Spec §Risks #7 (no site-side fixture/linter changes) → confirmed ✓
- Spec §Closure bar (real poem live) → Task 12 ✓
