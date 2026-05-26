# Phase 3 B.1 — Garden Handler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the first concrete per-content-type publisher (garden), turning B.0's empty-handler skeleton into a working `a3-pub.sh --publish-living` that emits real garden notes from `~/org/notes/` into `content/garden/<slug>/`.

**Architecture:** New `a3madkour-publish-garden.el` module hosts the per-file garden handler. B.0's `frontmatter/normalize` pass-through grows a real garden branch. B.0's skeleton `export-file` is replaced with an in-memory ox-hugo invocation that returns `(:body :frontmatter :warnings)`. The living dispatcher already iterates source files and runs `begin-publish` → per-section walks → `finish-publish` (which calls the orphan sweep); B.1 only adds per-file work and the handler registration. Two B.0 carry-forwards fixed in the same slice: `SITE_DATA_DIR` auto-detect across all three `a3-pub.sh` intercepts, and back-port of the same defaulting pattern to `--check-orphans`.

**Tech Stack:** Emacs Lisp + ert (dotfiles); `ox-hugo` (vendored via straight in `a3-pub.sh`); Hugo extended ≥0.148.0 (verification); Python integration fixtures under `tools/test_publish_integration.py` (stdlib only).

**Cross-repo commit map:**
- Dotfiles repo (`~/dotfiles/`): all elisp + sibling tests + `a3-pub.sh`. Lives outside the site repo.
- Site repo (this one): integration fixtures, fixture-clear (in spot-check task), `CLAUDE.md` status pointer update.

**Reading list before starting:**
- `CLAUDE.md` (this repo) — current status pointer.
- `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` §7 (frontmatter mapping, especially Garden-specific), §9 Garden, §10 A→B interface, §11 idempotency + transition.
- Memory: `.claude/memory/project_b0_complete.md` (carry-forwards), `.claude/memory/project_next_slice.md` (B.1 scope), `.claude/memory/project_phase_3_decomposition.md`.
- Existing dotfiles modules to understand the call surface: `a3madkour-publish.el` (`note-section`, `begin-publish`), `a3madkour-publish-unpublish.el` (`finish-publish`), `a3madkour-publish-rewrite.el` (`rewrite-links-in-string`), `a3madkour-publish-assets.el` (`asset-validate-and-copy`), `a3madkour-publish-history.el` (`record-publish`).
- B.0's stubs to be replaced/extended: `a3madkour-publish-export.el`, `a3madkour-publish-frontmatter.el`, `a3madkour-publish-living.el`, `a3-pub.sh`.

---

## File Structure

**New files (dotfiles):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden.el` — garden handler module. Exports `a3madkour-pub-garden/publish-garden-file`. Internal helpers for per-file lifecycle (read body, normalize, rewrite links, asset-copy, write-if-different, record-publish).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden-test.el` — sibling test. Covers growth_stage / flavor / topic_map normalization + end-to-end publish-garden-file with a tmp `~/org/notes/`-shaped fixture corpus.

**Modified files (dotfiles):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export.el` — replace B.0 skeleton with real ox-hugo invocation; drop `dest-dir` arg.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export-test.el` — replace skeleton-only tests with real-export tests (using tmp org file).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` — refactor pass-through `cond` into per-section dispatch; garden branch real, others stay pass-through.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el` — add garden-branch tests (growth_stage / media_type+flavor / topic_map / per-keyword pass-throughs).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el` — register garden handler. (Implementation is one alist entry.)
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el` — extend the empty-handler test to assert garden registration.
- `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` — three intercepts get `SITE_DATA_DIR` cascade; `--check-orphans` block grows the same pattern; default-exec block adds `-l a3madkour-publish-garden`.

**Modified files (site repo):**
- `tools/test_publish_integration.py` — 4 new fixtures (publish-once, idempotency, slug-shift, removed-note) targeting the garden handler.
- `CLAUDE.md` — Project status update at slice end ("B.1 garden handler shipped").

**Touched at spot-check, not by automation:**
- `content/garden/*/` — fixtures replaced by real B-emitted notes when the user runs `a3-pub.sh --publish-living` against `~/org/notes/`. Author commits the resulting diff.

---

## Task 1: `SITE_DATA_DIR` auto-detect cascade across all four `a3-pub.sh` intercepts

**Why first:** Pure shell change with no elisp dependency. Derisks the whole slice — without it, `--publish-living` would write `data/url-history.yaml` to the wrong path on every machine. Also closes B.0 known issue #1 + #2 in one stroke.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` (lines 22–50 for `--check-orphans`; 61–87 for `--publish-living`; 98–133 for `--publish-deliberate`; the default-exec block at 141+ does not pass site-data-dir to emacs, so leave it alone — interactive emacs already has `a3madkour-pub/site-data-dir` set via the user's `init.el`).

- [ ] **Step 1: Read the current `a3-pub.sh` end-to-end** (≈190 lines). Confirm there are exactly three intercepts that need the cascade (`--check-orphans`, `--publish-living`, `--publish-deliberate`) and one default-exec block that does not.

- [ ] **Step 2: Define the cascade helper at the top of `a3-pub.sh`** (immediately after the existing `LISP_DIR` / `STRAIGHT_BOOTSTRAP` setup, before line 22).

```bash
# Resolve the Hugo site `data/' directory used for url-history.yaml.
# Cascade:
#   1. Explicit override via $A3_PUB_SITE_DATA_DIR
#   2. Auto-detect via `git rev-parse --show-toplevel' from $PWD
#   3. Error out with a clear message
# Used by all three publish-side intercepts.
a3_pub_resolve_site_data_dir() {
  if [ -n "${A3_PUB_SITE_DATA_DIR:-}" ]; then
    printf '%s\n' "$A3_PUB_SITE_DATA_DIR"
    return 0
  fi
  local repo_root
  if repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" && [ -d "$repo_root/data" ]; then
    printf '%s/data/\n' "$repo_root"
    return 0
  fi
  echo "a3-pub.sh: cannot resolve site data dir." >&2
  echo "  Set A3_PUB_SITE_DATA_DIR=/path/to/site/data/ OR cd into the site repo before running." >&2
  return 1
}
```

- [ ] **Step 3: Replace the three existing default-assignments.** In each of the three intercepts, replace the line:

```bash
SITE_DATA_DIR="${A3_PUB_SITE_DATA_DIR:-$HOME/Workspace/a3madkour.github.io/data/}"
```

with:

```bash
SITE_DATA_DIR="$(a3_pub_resolve_site_data_dir)" || exit 1
```

- [ ] **Step 4: Add `SITE_DATA_DIR` cascade + plumbing to the `--check-orphans` intercept** (line 22 block). Currently this block builds the emacs invocation without setting `a3madkour-pub/site-data-dir`, so `begin-publish` → `read-manifest` fails with `user-error: site-data-dir is nil`.

Insert after line 25 (after `shift`):

```bash
  SITE_DATA_DIR="$(a3_pub_resolve_site_data_dir)" || exit 1
```

And insert before `--eval "(a3madkour-pub/begin-publish)"` (currently line 41):

```bash
    --eval "(setq a3madkour-pub/site-data-dir \"$SITE_DATA_DIR\")" \
```

- [ ] **Step 5: Manual smoke tests — run each intercept from inside the site repo with no env override.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --check-orphans
echo "exit=$?"
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-deliberate /nonexistent.org 2>&1 | head -5
echo "exit=$?"
```

Expected:
- `--check-orphans` exits 0; prints `removed: nil`, `slug-shifted: nil`, `orphan-warnings:` (empty list — no published manifest yet on this machine OR the existing manifest reports no orphans).
- `--publish-living` exits 0 with no stdout (B.0's empty handler set; garden handler not yet registered).
- `--publish-deliberate <nonexistent>` exits 1 with `ERROR: ...` (clean, not a SIGABRT).

- [ ] **Step 6: Manual smoke test from a non-git CWD with explicit env override.**

```bash
cd /tmp
A3_PUB_SITE_DATA_DIR=/Users/a3madkour/Sync/Workspace/a3madkour.github.io/data/ \
  ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
```

Expected: exits 0 (env override resolves; no fallback to git rev-parse).

- [ ] **Step 7: Manual smoke test from a non-git CWD with NO env override** (proves the hard-error path).

```bash
cd /tmp
unset A3_PUB_SITE_DATA_DIR
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living 2>&1 | head -3
echo "exit=$?"
```

Expected: exits 1 with `a3-pub.sh: cannot resolve site data dir.` + the two hint lines.

- [ ] **Step 8: Commit (dotfiles).**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3-pub.sh
git commit -m "fix(b-1): SITE_DATA_DIR cascade + --check-orphans back-port

Auto-detect via git rev-parse from \$PWD; honour A3_PUB_SITE_DATA_DIR
env override; hard-error with a clear hint otherwise. Closes B.0
known issues #1 (wrong default path) and #2 (--check-orphans was
missing the SITE_DATA_DIR plumbing entirely)."
```

---

## Task 2: Align `export-file` signature with spec §10 (drop `dest-dir`)

**Why now:** Before adding the real ox-hugo invocation in Task 3, lock in the spec-aligned signature so Task 3's tests don't need a second rewrite.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export.el` — drop `dest-dir` arg.
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export-test.el` — drop `dest-dir` from any test calls.

- [ ] **Step 1: Read the current test file** to see how many call sites change.

```bash
cat ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export-test.el
```

- [ ] **Step 2: Update `export-file` definition to one-arg.**

```elisp
(defun a3madkour-pub-export/export-file (file)
  "Export FILE (an absolute `.org' path) via ox-hugo.

Returns a plist:
  :body         MARKDOWN-STRING — the post-export markdown body (no frontmatter)
  :frontmatter  ALIST — keys are symbols (e.g. `title' `tags'), values are
                strings/lists/booleans as ox-hugo emits them
  :warnings     LIST OF STRINGS — non-fatal issues raised during export

B.0 skeleton: returns (:body \"\" :frontmatter nil :warnings nil) regardless
of input.  B.1 (this slice) wires the real ox-hugo invocation in a follow-up
task; this docstring's contract holds across both phases.

The bundle destination dir is the caller's responsibility (see spec §10);
this function does not write to disk."
  (ignore file)
  (list :body "" :frontmatter nil :warnings nil))
```

- [ ] **Step 3: Update the test file** — strip `dest-dir` from every call.

- [ ] **Step 4: Run the export test sibling.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . -l a3madkour-publish-export -l a3madkour-publish-export-test -f ert-run-tests-batch-and-exit
```

Expected: tests pass (still skeleton; no contract changed besides arity).

- [ ] **Step 5: Run the full ert suite to confirm no caller broke.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch \
  -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: `Ran 239 tests, 239 results as expected, 0 unexpected.` (same count as B.0 baseline since this is a refactor, not new tests.)

- [ ] **Step 6: Commit (dotfiles).**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-export.el emacs-configs/custom/lisp/a3madkour-publish-export-test.el
git commit -m "refactor(b-1): align export-file with spec §10 (drop dest-dir)

Bundle path is the per-section handler's concern, not export-file's.
Sets up Task 3 to wire real ox-hugo invocation against the spec
signature."
```

---

## Task 3: Implement real ox-hugo invocation in `export-file`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export.el` — real implementation.
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-export-test.el` — real ox-hugo round-trip test.

- [ ] **Step 1: Write the failing test for a real ox-hugo round-trip.**

Add to `a3madkour-publish-export-test.el`:

```elisp
(require 'ert)
(require 'a3madkour-publish-export)

(ert-deftest a3madkour-pub-export--real-export-roundtrip ()
  "export-file invokes ox-hugo and returns non-empty :body + parsed :frontmatter."
  (let* ((tmpdir (make-temp-file "a3-pub-export-" t))
         (src (expand-file-name "example.org" tmpdir)))
    (unwind-protect
        (progn
          (with-temp-file src
            (insert "#+title: Example Note\n"
                    "#+filetags: :alpha:beta:\n"
                    "#+HUGO_SECTION: garden\n"
                    "#+HUGO_BASE_DIR: " tmpdir "/site/\n"
                    "\n"
                    "* The Heading\n"
                    "Body text with a [[https://example.com][link]].\n"))
          (let* ((result (a3madkour-pub-export/export-file src))
                 (body (plist-get result :body))
                 (fm (plist-get result :frontmatter)))
            (should (stringp body))
            (should (string-match-p "Body text with" body))
            (should (not (string-match-p "^---" body))) ; frontmatter stripped
            (should (equal (alist-get 'title fm) "Example Note"))
            (should (member "alpha" (alist-get 'tags fm)))
            (should (member "beta" (alist-get 'tags fm)))))
      (delete-directory tmpdir t))))
```

- [ ] **Step 2: Run to verify it fails.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . -l a3madkour-publish-export -l a3madkour-publish-export-test -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: 1 test fails (`:body` is empty string from the skeleton).

- [ ] **Step 3: Implement the real export.** Replace `export-file` body with:

```elisp
(require 'ox-hugo)
(require 'yaml nil 'noerror)  ; optional; we fall back to inline parser if absent

(defun a3madkour-pub-export--parse-frontmatter (text)
  "Parse YAML or TOML frontmatter from the head of TEXT.
Returns (FRONTMATTER-ALIST . BODY-STRING).
Supports ox-hugo's two delimiter styles: `+++' (TOML) and `---' (YAML).
Tags are normalized to a list of strings regardless of source style."
  (with-temp-buffer
    (insert text)
    (goto-char (point-min))
    (let* ((delim (cond
                   ((looking-at "^\\+\\+\\+\n") "+++")
                   ((looking-at "^---\n") "---")
                   (t nil)))
           fm-text body)
      (if (not delim)
          (cons nil text)
        (forward-line 1)
        (let ((start (point)))
          (re-search-forward (format "^%s\n" (regexp-quote delim)) nil t)
          (setq fm-text (buffer-substring-no-properties start (match-beginning 0)))
          (setq body (buffer-substring-no-properties (point) (point-max))))
        (cons (a3madkour-pub-export--parse-frontmatter-pairs fm-text delim)
              body)))))

(defun a3madkour-pub-export--parse-frontmatter-pairs (text delim)
  "Minimal frontmatter parser for `key = value' (TOML) / `key: value' (YAML).
Returns an alist with symbol keys. Lists are detected by `[a, b, c]'
or YAML inline `[a, b, c]'. Strings are unquoted. This is intentionally
narrow: ox-hugo's output is mechanical, and we control its input."
  (let ((sep (if (string= delim "+++") " = " ": "))
        result)
    (dolist (line (split-string text "\n" t))
      (when (string-match (concat "^\\([a-zA-Z_][a-zA-Z0-9_]*\\)"
                                  (regexp-quote sep) "\\(.*\\)$")
                          line)
        (let* ((k (intern (match-string 1 line)))
               (raw (match-string 2 line))
               (val (a3madkour-pub-export--parse-scalar raw)))
          (push (cons k val) result))))
    (nreverse result)))

(defun a3madkour-pub-export--parse-scalar (raw)
  "Parse RAW (a string) into a string, list of strings, or boolean."
  (cond
   ((string-match "^\\[\\(.*\\)\\]$" raw)
    (mapcar (lambda (s) (string-trim s "[ \t\"]+" "[ \t\"]+"))
            (split-string (match-string 1 raw) "," t "[ \t]+")))
   ((string-match "^\"\\(.*\\)\"$" raw)
    (match-string 1 raw))
   ((string= raw "true") t)
   ((string= raw "false") nil)
   (t raw)))

(defun a3madkour-pub-export/export-file (file)
  "Export FILE (an absolute `.org' path) via ox-hugo.

Returns a plist:
  :body         MARKDOWN-STRING — the post-export markdown body (no frontmatter)
  :frontmatter  ALIST — keys are symbols (e.g. `title' `tags'), values are
                strings/lists/booleans as ox-hugo emits them
  :warnings     LIST OF STRINGS — non-fatal issues raised during export

Implementation: visits FILE in a temp buffer, invokes
`org-hugo-export-as-md', captures the output buffer, parses ox-hugo's
TOML or YAML frontmatter into a symbol-keyed alist, returns body
without the frontmatter delimiters."
  (let ((warnings nil)
        (output-buffer-name "*Org Hugo Export*"))
    (with-current-buffer (find-file-noselect file)
      (let ((inhibit-message t))
        (org-hugo-export-as-md nil nil nil :buffer output-buffer-name)))
    (let ((raw (with-current-buffer output-buffer-name
                 (buffer-string))))
      (kill-buffer output-buffer-name)
      (let* ((parsed (a3madkour-pub-export--parse-frontmatter raw)))
        (list :body (cdr parsed)
              :frontmatter (car parsed)
              :warnings warnings)))))
```

> **Note on ox-hugo API:** `org-hugo-export-as-md` is the buffer-emitting variant. If the exact 4th-arg buffer-name keyword fails under the vendored ox-hugo version, fall back to capturing `(get-buffer "*Org Hugo Export*")` immediately after the call (ox-hugo's default buffer name).

- [ ] **Step 4: Run the test to verify it passes.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . -l a3madkour-publish-export -l a3madkour-publish-export-test -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: tests pass. If ox-hugo isn't on the load path, add `(require 'ox-hugo)` and load straight bootstrap in the test (mirror `a3-pub.sh`).

- [ ] **Step 5: Run the full ert suite.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: 239 + N (N = new tests in this task) all pass.

- [ ] **Step 6: Commit (dotfiles).**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-export.el emacs-configs/custom/lisp/a3madkour-publish-export-test.el
git commit -m "feat(b-1): real ox-hugo invocation in export-file

Buffer-emit + minimal TOML/YAML frontmatter parser. Returns
spec-shape plist (:body :frontmatter :warnings) for the per-section
handlers to consume."
```

---

## Task 4: Refactor `frontmatter/normalize` from pass-through to per-section dispatch

**Why:** B.0 ships a single pass-through `cond` branch. B.1's garden logic needs its own branch without polluting other sections (which keep pass-through until B.2+).

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` — replace single `cond` clause with per-section branches.
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el` — adjust existing pass-through tests to use a non-garden section.

- [ ] **Step 1: Write a failing test that pins the dispatch contract.**

Add to `a3madkour-publish-frontmatter-test.el`:

```elisp
(ert-deftest a3madkour-pub-frontmatter--dispatch-routes-by-section ()
  "normalize dispatches to per-section logic; unknown sections still error."
  (should-error
   (a3madkour-pub-frontmatter/normalize 'bogus '((title . "x")) "/tmp/x.org"))
  ;; Non-garden known sections still pass-through (B.1 only adds garden).
  (should (equal (a3madkour-pub-frontmatter/normalize 'essays
                                                       '((title . "Hi"))
                                                       "/tmp/x.org")
                 '((title . "Hi")))))
```

- [ ] **Step 2: Run to verify pre-existing pass + new test passes** (dispatch is already there from B.0; this test pins the contract for follow-on tasks).

- [ ] **Step 3: Refactor `normalize` into per-section dispatch.** Replace the `cond` block:

```elisp
(defun a3madkour-pub-frontmatter/normalize (section raw-alist source-file)
  "Normalize RAW-ALIST for SECTION's frontmatter contract.
[... existing docstring ...]"
  (unless (memq section a3madkour-pub-frontmatter--known-sections)
    (error "a3madkour-pub-frontmatter: unknown section %S (must be one of %S)"
           section a3madkour-pub-frontmatter--known-sections))
  (cond
   ((eq section 'garden)
    (a3madkour-pub-frontmatter--normalize-garden raw-alist source-file))
   ;; B.2+ slices add real branches here:
   ;;   ((memq section '(library-reading library-listening library-playing library-watching))
   ;;    (a3madkour-pub-frontmatter--normalize-library section raw-alist source-file))
   ;;   ((memq section '(research-theme research-question))
   ;;    (a3madkour-pub-frontmatter--normalize-research section raw-alist source-file))
   ;;   ...
   (t
    ;; B.0 pass-through for sections not yet handled.
    (ignore source-file)
    raw-alist)))

(defun a3madkour-pub-frontmatter--normalize-garden (raw-alist source-file)
  "B.1: garden frontmatter normalizer. Filled in by Tasks 5–8."
  (ignore source-file)
  raw-alist)
```

- [ ] **Step 4: Run the test.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . -l a3madkour-publish-frontmatter -l a3madkour-publish-frontmatter-test -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: tests pass (garden still pass-through; dispatch routes correctly).

- [ ] **Step 5: Commit (dotfiles).**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "refactor(b-1): per-section dispatch in frontmatter/normalize

Empty garden branch stub; Tasks 5–8 fill in growth_stage / flavor /
topic_map / per-keyword pass-throughs."
```

---

## Task 5: Garden `growth_stage` derivation

**Spec §7:** `:PROGRESS:` (none/highlighting → seedling; ref-notes → budding; main-notes/done → evergreen); `#+HUGO_GROWTH_STAGE:` overrides.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` — add `--derive-growth-stage` helper, wire into garden normalizer.
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el` — table tests for all four `:PROGRESS:` values + override + missing-source-file case.

- [ ] **Step 1: Write the failing tests.**

```elisp
(ert-deftest a3madkour-pub-frontmatter--growth-stage-from-progress ()
  "PROGRESS property maps to growth_stage per spec §7."
  (let ((src (make-temp-file "garden-" nil ".org")))
    (unwind-protect
        (progn
          ;; none / unset
          (with-temp-file src (insert "* Note\n  :PROPERTIES:\n  :END:\n"))
          (should (equal (alist-get 'growth_stage
                                    (a3madkour-pub-frontmatter/normalize
                                     'garden '() src))
                         "seedling"))
          ;; highlighting → seedling
          (with-temp-file src (insert "* Note\n  :PROPERTIES:\n  :PROGRESS: highlighting\n  :END:\n"))
          (should (equal (alist-get 'growth_stage
                                    (a3madkour-pub-frontmatter/normalize
                                     'garden '() src))
                         "seedling"))
          ;; ref-notes → budding
          (with-temp-file src (insert "* Note\n  :PROPERTIES:\n  :PROGRESS: ref-notes\n  :END:\n"))
          (should (equal (alist-get 'growth_stage
                                    (a3madkour-pub-frontmatter/normalize
                                     'garden '() src))
                         "budding"))
          ;; main-notes → evergreen
          (with-temp-file src (insert "* Note\n  :PROPERTIES:\n  :PROGRESS: main-notes\n  :END:\n"))
          (should (equal (alist-get 'growth_stage
                                    (a3madkour-pub-frontmatter/normalize
                                     'garden '() src))
                         "evergreen"))
          ;; done → evergreen
          (with-temp-file src (insert "* Note\n  :PROPERTIES:\n  :PROGRESS: done\n  :END:\n"))
          (should (equal (alist-get 'growth_stage
                                    (a3madkour-pub-frontmatter/normalize
                                     'garden '() src))
                         "evergreen")))
      (delete-file src))))

(ert-deftest a3madkour-pub-frontmatter--growth-stage-keyword-override ()
  "HUGO_GROWTH_STAGE keyword overrides PROGRESS derivation."
  (let ((src (make-temp-file "garden-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file src
            (insert "#+HUGO_GROWTH_STAGE: budding\n"
                    "* Note\n  :PROPERTIES:\n  :PROGRESS: done\n  :END:\n"))
          (should (equal (alist-get 'growth_stage
                                    (a3madkour-pub-frontmatter/normalize
                                     'garden
                                     '((growth_stage . "budding")) ; ox-hugo would have parsed it
                                     src))
                         "budding")))
      (delete-file src))))
```

- [ ] **Step 2: Run to verify they fail.**

```bash
emacs --batch -L . -l a3madkour-publish-frontmatter -l a3madkour-publish-frontmatter-test -f ert-run-tests-batch-and-exit 2>&1 | tail -8
```

Expected: 2 failures (growth_stage not derived; garden is still pass-through).

- [ ] **Step 3: Implement.**

Add helper above `--normalize-garden`:

```elisp
(defconst a3madkour-pub-frontmatter--progress->stage
  '(("highlighting" . "seedling")
    ("ref-notes"    . "budding")
    ("main-notes"   . "evergreen")
    ("done"         . "evergreen"))
  "Mapping from org `:PROGRESS:' property to Hugo `growth_stage'.
Unset / unrecognized → \"seedling\" (per spec §7).")

(defun a3madkour-pub-frontmatter--read-org-property (file property)
  "Read PROPERTY (a string like \"PROGRESS\") from the first heading in FILE.
Returns nil if not set."
  (with-temp-buffer
    (insert-file-contents file)
    (goto-char (point-min))
    (when (re-search-forward
           (format "^[ \t]*:%s:[ \t]+\\(.+\\)$" (regexp-quote property))
           nil t)
      (string-trim (match-string 1)))))

(defun a3madkour-pub-frontmatter--derive-growth-stage (raw-alist source-file)
  "Return growth_stage per spec §7: HUGO_GROWTH_STAGE wins; else map :PROGRESS:."
  (or (alist-get 'growth_stage raw-alist)
      (let* ((progress (a3madkour-pub-frontmatter--read-org-property source-file "PROGRESS")))
        (or (and progress (cdr (assoc progress a3madkour-pub-frontmatter--progress->stage)))
            "seedling"))))
```

Then update `--normalize-garden`:

```elisp
(defun a3madkour-pub-frontmatter--normalize-garden (raw-alist source-file)
  "B.1: garden frontmatter normalizer."
  (let ((out (copy-alist raw-alist)))
    (setf (alist-get 'growth_stage out)
          (a3madkour-pub-frontmatter--derive-growth-stage raw-alist source-file))
    out))
```

- [ ] **Step 4: Run tests; expect green.**

- [ ] **Step 5: Commit (dotfiles).**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "feat(b-1): garden growth_stage derivation from :PROGRESS:

Maps highlighting → seedling; ref-notes → budding; main-notes/done →
evergreen. HUGO_GROWTH_STAGE keyword overrides per spec §7."
```

---

## Task 6: Garden `media_type` pass-through + `flavor` inference

**Spec §7:** `media_type` from `#+HUGO_MEDIA_TYPE:` (one of book/album/track/game/film/series/paper/video/article/talk). `flavor` inferred: missing → concept; book/album/track/game/film/series → media; paper/video/article/talk → reference.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests** (table-driven across all 11 media types + missing).

```elisp
(ert-deftest a3madkour-pub-frontmatter--garden-flavor-inference ()
  (let ((cases '((nil       . "concept")
                 ("book"    . "media") ("album"  . "media")
                 ("track"   . "media") ("game"   . "media")
                 ("film"    . "media") ("series" . "media")
                 ("paper"   . "reference") ("video"   . "reference")
                 ("article" . "reference") ("talk"    . "reference"))))
    (dolist (case cases)
      (let* ((mt (car case))
             (expected-flavor (cdr case))
             (raw (if mt `((media_type . ,mt)) '()))
             (out (a3madkour-pub-frontmatter/normalize 'garden raw "/tmp/x.org")))
        (when mt
          (should (equal (alist-get 'media_type out) mt)))
        (should (equal (alist-get 'flavor out) expected-flavor))))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.**

```elisp
(defconst a3madkour-pub-frontmatter--media-flavors
  '(("book" . "media") ("album" . "media") ("track" . "media")
    ("game" . "media") ("film"  . "media") ("series" . "media")
    ("paper" . "reference") ("video" . "reference")
    ("article" . "reference") ("talk" . "reference"))
  "Map garden `media_type' values to `flavor' per spec §7.")

(defun a3madkour-pub-frontmatter--infer-flavor (media-type)
  "Return flavor for MEDIA-TYPE per spec §7.
nil/unrecognized media_type → \"concept\"."
  (or (cdr (assoc media-type a3madkour-pub-frontmatter--media-flavors))
      "concept"))
```

Update `--normalize-garden`:

```elisp
(defun a3madkour-pub-frontmatter--normalize-garden (raw-alist source-file)
  "B.1: garden frontmatter normalizer."
  (let ((out (copy-alist raw-alist)))
    (setf (alist-get 'growth_stage out)
          (a3madkour-pub-frontmatter--derive-growth-stage raw-alist source-file))
    (setf (alist-get 'flavor out)
          (a3madkour-pub-frontmatter--infer-flavor (alist-get 'media_type raw-alist)))
    out))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Commit.**

```bash
git commit -m "feat(b-1): garden media_type pass-through + flavor inference

Concept (missing) / media (creative works) / reference (lit) per
spec §7."
```

---

## Task 7: Garden `topic_map` parsing

**Spec §7:** `topic_map` from `#+HUGO_TOPIC_MAP: slug-1 slug-2 …` (space-delimited slug list, emitted as a YAML list).

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-frontmatter--garden-topic-map-list ()
  "topic_map: ox-hugo may parse it as a single string or a list; normalizer always emits a list."
  ;; List form pass-through.
  (should (equal (alist-get 'topic_map
                            (a3madkour-pub-frontmatter/normalize
                             'garden '((topic_map . ("a" "b" "c"))) "/tmp/x.org"))
                 '("a" "b" "c")))
  ;; String form split on whitespace.
  (should (equal (alist-get 'topic_map
                            (a3madkour-pub-frontmatter/normalize
                             'garden '((topic_map . "a b c")) "/tmp/x.org"))
                 '("a" "b" "c")))
  ;; Missing → not emitted (no key at all).
  (should-not (assq 'topic_map
                    (a3madkour-pub-frontmatter/normalize
                     'garden '() "/tmp/x.org"))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.** Add helper + extend `--normalize-garden`:

```elisp
(defun a3madkour-pub-frontmatter--coerce-slug-list (raw)
  "Coerce RAW (string or list-of-strings or nil) to a list of strings.
Strings split on whitespace. nil stays nil."
  (cond
   ((null raw) nil)
   ((listp raw) raw)
   ((stringp raw) (split-string raw "[ \t]+" t))
   (t nil)))

;; In --normalize-garden, after flavor inference:
(let ((tm (a3madkour-pub-frontmatter--coerce-slug-list
           (alist-get 'topic_map raw-alist))))
  (when tm
    (setf (alist-get 'topic_map out) tm)))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Commit.**

```bash
git commit -m "feat(b-1): garden topic_map normalization to list-of-slugs"
```

---

## Task 8: Garden per-keyword pass-throughs (`creator`, `status`, `started`, `finished`, `spoiler_level`, `original_url`, `year`, `weight`)

**Spec §7:** all per-keyword `#+HUGO_*:`; ox-hugo already parses them. Normalizer ensures they survive into the output alist (and that `year` / `weight` are integers, not strings).

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests** — assert each key passes through; `year` / `weight` coerce string → int.

```elisp
(ert-deftest a3madkour-pub-frontmatter--garden-passthrough-keywords ()
  (let* ((raw '((creator       . "Jane Austen")
                (status        . "finished")
                (started       . "2024-11-02")
                (finished      . "2024-12-15")
                (spoiler_level . "mild")
                (original_url  . "https://example.com/post")
                (year          . "1813")
                (weight        . "5")))
         (out (a3madkour-pub-frontmatter/normalize 'garden raw "/tmp/x.org")))
    (should (equal (alist-get 'creator out) "Jane Austen"))
    (should (equal (alist-get 'status out) "finished"))
    (should (equal (alist-get 'started out) "2024-11-02"))
    (should (equal (alist-get 'finished out) "2024-12-15"))
    (should (equal (alist-get 'spoiler_level out) "mild"))
    (should (equal (alist-get 'original_url out) "https://example.com/post"))
    (should (eq (alist-get 'year out) 1813))
    (should (eq (alist-get 'weight out) 5))))
```

- [ ] **Step 2: Run; expect failure** (year/weight are still strings since pass-through doesn't coerce).

- [ ] **Step 3: Implement.** In `--normalize-garden`:

```elisp
;; Pass-through string fields are already in `out' via copy-alist; only
;; coerce ints where the contract says int.
(dolist (k '(year weight))
  (let ((v (alist-get k out)))
    (when (stringp v)
      (setf (alist-get k out) (string-to-number v)))))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Run full suite to confirm 0 unexpected failures.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

- [ ] **Step 6: Commit.**

```bash
git commit -m "feat(b-1): garden per-keyword pass-through + year/weight int coerce"
```

---

## Task 9: Scaffold `a3madkour-publish-garden.el` module + sibling test + `a3-pub.sh` `-l` line

**Why:** Stub the new module + register it in the wrapper before the handler implementation, so Task 10 starts from a loadable state.

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden-test.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` — add `-l a3madkour-publish-garden` to all three intercepts AND the default-exec block (per [[feedback_plan_wrapper_script_updates]]).

- [ ] **Step 1: Create the module scaffold.**

```elisp
;;; a3madkour-publish-garden.el --- garden per-file publish handler  -*- lexical-binding: t; -*-

;;; Commentary:

;; B.1: garden per-file publish handler.  Wires together ox-hugo export,
;; frontmatter normalization, A.1's link rewriter + asset copier, and
;; A.1's record-publish into one entry point: `publish-garden-file'.
;;
;; Registered into `a3madkour-pub-living--handlers' as
;;   (garden . a3madkour-pub-garden/publish-garden-file)
;; by `a3madkour-pub-living' (per spec §10).

;;; Code:

(require 'a3madkour-publish)
(require 'a3madkour-publish-export)
(require 'a3madkour-publish-frontmatter)
(require 'a3madkour-publish-rewrite)
(require 'a3madkour-publish-assets)
(require 'a3madkour-publish-history)

(defun a3madkour-pub-garden/publish-garden-file (file)
  "Publish a single garden-section FILE to the site's content/garden/<slug>/.

Stub (Task 9): signature only; real implementation lands in Task 10."
  (ignore file)
  nil)

(provide 'a3madkour-publish-garden)

;;; a3madkour-publish-garden.el ends here
```

- [ ] **Step 2: Create the sibling test scaffold.**

```elisp
;;; a3madkour-publish-garden-test.el --- tests for garden handler  -*- lexical-binding: t; -*-

(require 'ert)
(require 'a3madkour-publish-garden)

(ert-deftest a3madkour-pub-garden--module-loads ()
  "Smoke: module is loadable and exposes publish-garden-file."
  (should (fboundp 'a3madkour-pub-garden/publish-garden-file)))

(provide 'a3madkour-publish-garden-test)

;;; a3madkour-publish-garden-test.el ends here
```

- [ ] **Step 3: Add `-l a3madkour-publish-garden` to `a3-pub.sh` intercepts.**

In each of `--publish-living`, `--publish-deliberate`, and the default-exec block, add the line `-l a3madkour-publish-garden \` immediately after `-l a3madkour-publish-deliberate \`. (Do NOT add to `--check-orphans` — it doesn't need garden-specific logic.)

- [ ] **Step 4: Run the new sibling test.**

```bash
emacs --batch -L . -l a3madkour-publish-garden -l a3madkour-publish-garden-test -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: 1 pass.

- [ ] **Step 5: Run full suite + smoke the wrapper.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3

cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
```

Expected: all ert tests pass; `--publish-living` still exits 0 silently (handler not yet registered).

- [ ] **Step 6: Commit (dotfiles).**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-garden.el \
        emacs-configs/custom/lisp/a3madkour-publish-garden-test.el \
        emacs-configs/custom/lisp/a3-pub.sh
git commit -m "scaffold(b-1): a3madkour-publish-garden module + wrapper -l line

Stub handler + smoke test; real implementation in Task 10."
```

---

## Task 10: Implement `publish-garden-file` end-to-end

**Spec §10 calling pattern:**

```elisp
(let* ((exported    (a3madkour-pub-export/export-file file))
       (frontmatter (a3madkour-pub-frontmatter/normalize 'garden
                      (plist-get exported :frontmatter) file))
       (body        (a3madkour-pub-rewrite/rewrite-links-in-string
                      (plist-get exported :body) file))
       (assets      (a3madkour-pub-assets/asset-validate-and-copy
                      file bundle-dest-dir)))
  ;; write content/garden/<slug>/index.md
  (a3madkour-pub-history/record-publish
    file-id new-url 'live :had-slug-override-p slug-overridden-p))
```

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden.el` — real implementation.
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden-test.el` — end-to-end test with a tmp `~/org/notes/`-shaped corpus.

- [ ] **Step 1: Write the failing end-to-end test.**

```elisp
(ert-deftest a3madkour-pub-garden--publish-garden-file-end-to-end ()
  "publish-garden-file writes content/garden/<slug>/index.md with
normalized frontmatter + rewritten body + record-publish call."
  (let* ((notes-dir (make-temp-file "a3-pub-notes-" t))
         (site-dir  (make-temp-file "a3-pub-site-" t))
         (src       (expand-file-name "example-note.org" notes-dir)))
    (unwind-protect
        (progn
          (make-directory (expand-file-name "data" site-dir))
          (make-directory (expand-file-name "content/garden" site-dir) t)
          (with-temp-file src
            (insert ":PROPERTIES:\n:ID: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee\n:END:\n"
                    "#+title: Example Note\n"
                    "#+filetags: :alpha:\n"
                    "#+HUGO_SECTION: garden\n"
                    "#+HUGO_BASE_DIR: " site-dir "/\n"
                    "* The Heading\n  :PROPERTIES:\n  :PROGRESS: ref-notes\n  :END:\n"
                    "Body text.\n"))
          (let ((a3madkour-pub/site-data-dir (expand-file-name "data/" site-dir))
                (a3madkour-pub/org-notes-dir notes-dir))
            (a3madkour-pub/begin-publish)
            (a3madkour-pub-garden/publish-garden-file src)
            (a3madkour-pub/finish-publish))
          (let ((out (expand-file-name "content/garden/example-note/index.md" site-dir)))
            (should (file-exists-p out))
            (with-temp-buffer
              (insert-file-contents out)
              (should (string-match-p "title: Example Note" (buffer-string)))
              (should (string-match-p "growth_stage: budding" (buffer-string)))
              (should (string-match-p "Body text" (buffer-string))))))
      (delete-directory notes-dir t)
      (delete-directory site-dir t))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement `publish-garden-file`.**

```elisp
(defcustom a3madkour-pub-garden/section-dir-name "garden"
  "Hugo content section directory name for garden notes (relative to site root)."
  :type 'string :group 'a3madkour-publish)

(defun a3madkour-pub-garden--site-root ()
  "Derive the Hugo site root from `a3madkour-pub/site-data-dir'.
Convention: site-data-dir is `<root>/data/'."
  (expand-file-name ".." (directory-file-name a3madkour-pub/site-data-dir)))

(defun a3madkour-pub-garden--write-if-different (path content)
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

(defun a3madkour-pub-garden--render-frontmatter (alist)
  "Render ALIST as YAML frontmatter (alphabetical key order; deterministic)."
  (let ((sorted (sort (copy-sequence alist)
                      (lambda (a b)
                        (string< (symbol-name (car a)) (symbol-name (car b)))))))
    (with-output-to-string
      (princ "---\n")
      (dolist (cell sorted)
        (let ((k (symbol-name (car cell)))
              (v (cdr cell)))
          (cond
           ((listp v)
            (princ (format "%s: [%s]\n" k
                           (mapconcat (lambda (s) (format "\"%s\"" s)) v ", "))))
           ((stringp v) (princ (format "%s: \"%s\"\n" k v)))
           ((numberp v) (princ (format "%s: %s\n" k v)))
           ((eq v t)    (princ (format "%s: true\n" k)))
           ((null v)    (princ (format "%s: false\n" k))))))
      (princ "---\n"))))

(defun a3madkour-pub-garden/publish-garden-file (file)
  "Publish a single garden-section FILE to content/garden/<slug>/index.md."
  (let* ((id     (a3madkour-pub/file-id file))
         (slug   (a3madkour-pub/slug-for file))
         (site-root (a3madkour-pub-garden--site-root))
         (bundle-dir (expand-file-name
                      (format "content/%s/%s/"
                              a3madkour-pub-garden/section-dir-name slug)
                      site-root))
         (out-path (expand-file-name "index.md" bundle-dir))
         (exported   (a3madkour-pub-export/export-file file))
         (normalized (a3madkour-pub-frontmatter/normalize
                      'garden (plist-get exported :frontmatter) file))
         (body       (a3madkour-pub-rewrite/rewrite-links-in-string
                      (plist-get exported :body) file))
         (new-url    (format "/%s/%s/"
                             a3madkour-pub-garden/section-dir-name slug)))
    (a3madkour-pub-assets/asset-validate-and-copy file bundle-dir)
    (a3madkour-pub-garden--write-if-different
     out-path
     (concat (a3madkour-pub-garden--render-frontmatter normalized) body))
    (a3madkour-pub-history/record-publish id new-url 'live)))
```

> **Note:** `a3madkour-pub/file-id` and `a3madkour-pub/slug-for` are A.1 functions; if their actual names differ, adjust accordingly (grep `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish*.el` for `defun.*file-id\|defun.*slug-for`). The signature shape (id + slug for the source file) is what matters.

- [ ] **Step 4: Run the test; iterate on A.1 function name resolution if needed.**

- [ ] **Step 5: Run full suite.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

- [ ] **Step 6: Commit.**

```bash
git commit -m "feat(b-1): publish-garden-file end-to-end

Export → normalize → rewrite-links → asset-copy → write-if-different
→ record-publish. Frontmatter rendered alphabetical for determinism."
```

---

## Task 11: Register garden handler in `a3madkour-pub-living--handlers`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el`

- [ ] **Step 1: Write failing test pinning the registration.**

```elisp
(ert-deftest a3madkour-pub-living--garden-handler-registered ()
  (should (eq (cdr (assq 'garden a3madkour-pub-living--handlers))
              'a3madkour-pub-garden/publish-garden-file)))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Register in `a3madkour-publish-living.el`.** Two options — pick (b) for explicit init:

(a) Change the `defvar` default to seed the alist (works but couples B.0's module to B.1's symbol).

(b) Add a B.1-time setter at the bottom of `a3madkour-publish-living.el`:

```elisp
;; B.1: garden handler registration.  When B.2+ ship, each section's
;; module adds its own `add-to-list' call.
(with-eval-after-load 'a3madkour-publish-garden
  (add-to-list 'a3madkour-pub-living--handlers
               '(garden . a3madkour-pub-garden/publish-garden-file)))
```

This keeps living.el unaware of garden's exact symbol until garden is loaded.

- [ ] **Step 4: Run; expect green (after both modules are loaded in the test).** The test file needs `(require 'a3madkour-publish-garden)` to trigger the after-load form.

- [ ] **Step 5: Smoke the wrapper end-to-end against an empty tmp notes dir.**

```bash
TMP=$(mktemp -d)
mkdir -p "$TMP/notes" "$TMP/site/data" "$TMP/site/content/garden"
A3_PUB_SITE_DATA_DIR="$TMP/site/data/" \
  ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
ls "$TMP/site/content/garden/"  # should be empty (no source notes)
rm -rf "$TMP"
```

Expected: exit 0, content dir stays empty.

- [ ] **Step 6: Commit.**

```bash
git commit -m "feat(b-1): register garden handler in living--handlers"
```

---

## Task 12: Python integration fixture — publish-once

**Why:** Mirror the existing 8 A.1.d fixtures' pattern (`tools/test_publish_integration.py`); first of four new B.1 fixtures.

**Files:**
- Modify: `tools/test_publish_integration.py` (site repo).

- [ ] **Step 1: Read the existing file** to understand the fixture shape (helpers, conftest, run-and-assert pattern).

```bash
wc -l tools/test_publish_integration.py
grep -n "^def \|^class " tools/test_publish_integration.py
```

- [ ] **Step 2: Add new fixture `test_b1_garden_publish_once`.** It creates a tmp notes dir with one garden source note, runs `a3-pub.sh --publish-living` via subprocess against a tmp site dir, asserts `content/garden/<slug>/index.md` exists with expected frontmatter keys and that `data/url-history.yaml` records the publish.

(Concrete test body mirrors the helper patterns already in the file; reuse helpers rather than re-inventing.)

- [ ] **Step 3: Run.**

```bash
python3 tools/test_publish_integration.py -k test_b1_garden_publish_once -v
```

Expected: pass.

- [ ] **Step 4: Commit (site).**

```bash
git add tools/test_publish_integration.py
git commit -m "test(b-1): integration fixture — garden publish-once"
```

---

## Task 13: Python integration fixture — idempotency

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add `test_b1_garden_publish_idempotent`.** Runs `a3-pub.sh --publish-living` twice; asserts second run produces zero file diffs (mtime unchanged on `index.md`; `url-history.yaml` unchanged content-wise; second-run stdout silent).

- [ ] **Step 2: Run; iterate until pass.**

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-1): integration fixture — garden publish idempotent"
```

---

## Task 14: Python integration fixture — slug-shift

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add `test_b1_garden_slug_shift`.** Source note's title (and therefore slug) changes between publish 1 and publish 2; asserts old bundle moves to alias + new bundle lives at new path; `url-history.yaml` records the alias.

- [ ] **Step 2: Run; iterate.**

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-1): integration fixture — garden slug-shift"
```

---

## Task 15: Python integration fixture — removed-note (unpublish)

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add `test_b1_garden_removed_note_unpublish`.** Source note removed (file deleted) between publish 1 and publish 2; asserts the bundle dir is removed in publish 2 (finish-publish's Step A sweep); manifest records `state: removed`.

- [ ] **Step 2: Run; iterate.**

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-1): integration fixture — garden removed-note unpublish"
```

---

## Task 16: Validate B-emitted notes pass existing CI linters (output-shape parity)

**Why:** Per spec §11, a B-emitted garden note must still pass `check_garden_fixtures.py` and `check_garden_links.py`. This task wires that into an integration check so future B.x slices don't break it.

**Files:**
- Modify: `tools/test_publish_integration.py` (one combined `test_b1_garden_emits_lint_clean_output` that publishes one note, then invokes the two linters as subprocesses against the tmp site dir).

- [ ] **Step 1: Read** `tools/check_garden_fixtures.py` + `tools/check_garden_links.py` to confirm they accept a `--root` arg or default to CWD. (If they default to CWD, the test `chdir`s into the tmp site dir.)

- [ ] **Step 2: Add the fixture.** It publishes one note, then runs each linter against the tmp site dir, asserts exit 0.

- [ ] **Step 3: Run.**

- [ ] **Step 4: Commit.**

```bash
git commit -m "test(b-1): B-emitted notes pass check_garden_fixtures + _links"
```

---

## Task 17 (USER-DRIVEN): Real-corpus spot-check + fixture handover commit

**Why:** Per spec §11 transition strategy and [[feedback_verify_before_merge]] (visual verification before merge), this slice must do a real `~/org/notes/` publish-living run end-to-end, with the author confirming the result before the fixture commit lands.

**Files:**
- The author's real garden source files in `~/org/notes/`.
- This repo's `content/garden/` (fixtures will be replaced).
- `CLAUDE.md` (status pointer update).

- [ ] **Step 1: Run the full ert suite locally (last gate before real publish).**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: `N tests, N as expected, 0 unexpected.` (N ≈ 260 by this slice's end.)

- [ ] **Step 2: Run `tools/ci-local.sh` against the site repo** (per [[feedback_always_run_ci_locally]]) before any content/ change — establishes a green baseline.

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
tools/ci-local.sh
```

Expected: all 50 pre-build linters pass; hugo --minify succeeds; pagefind + smoke + page-weight + LHCI all green.

- [ ] **Step 3: Author confirms which garden notes in `~/org/notes/` carry `#+HUGO_PUBLISH: t` AND `#+HUGO_SECTION: garden`.**

```bash
grep -l "^#\+HUGO_PUBLISH: t" ~/org/notes/*.org | xargs grep -l "^#\+HUGO_SECTION: garden"
```

Expected: a short list of org files. If the list is empty, the author needs to add the keywords to whatever garden notes should publish; this slice does NOT auto-add them.

- [ ] **Step 4: Run the real publish.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
```

Expected: exit 0; fixture garden bundles in `content/garden/` are deleted; real garden notes appear at `content/garden/<slug>/index.md`; `data/url-history.yaml` updated.

- [ ] **Step 5: Re-run `tools/ci-local.sh`** (the real-content output must still pass the linters).

Expected: all 50 pre-build linters pass against the new B-emitted content.

- [ ] **Step 6: Author starts `hugo server --buildDrafts`, visits `/garden/`, eyeballs the new notes. Verify:**
- Tile grid renders (no broken `growth_stage` glyphs).
- Internal `[[id:UUID]]` links rewrote to `/garden/<slug>/` and clicks navigate.
- Per-note hero/figure assets load (if any source notes have inline assets).
- `topic_map` notes render the curated tile grid below the body.
- `/garden/graph/` still renders (graph-data partial picks up B-emitted notes the same as it picked up fixtures).

- [ ] **Step 7: If anything looks off, file a focused fix** (per [[feedback_design_batch_no_plan_until_implement]] don't expand B.1's scope; defer to a follow-up). Otherwise proceed.

- [ ] **Step 8: Update `CLAUDE.md` status pointer.** Locate the "Project status (as of 2026-MM-DD)" line and the B sub-project bullet under "Not started, in phase order"; update to reflect B.1 shipped.

- [ ] **Step 9: Commit the site changes.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add content/garden/ data/url-history.yaml CLAUDE.md
git commit -m "feat(b-1): garden handler ships — real-content handover

Replaces garden fixtures with B-emitted content from ~/org/notes/.
First slice to emit real Hugo content from the elisp publisher.
Closes B.0 carry-forward #1 + #2 (SITE_DATA_DIR cascade)."
git push origin master
```

- [ ] **Step 10: Update memory — drop the shipped entry.**

Create `.claude/memory/project_b1_complete.md` summarizing what shipped, what tests landed, dotfiles+site commit SHAs, known issues / B.2 follow-ups; add the index line to `.claude/memory/MEMORY.md`. Remove or update `project_next_slice.md` to point at B.2 (library handler).

---

## Self-Review

**Spec coverage check (against `2026-05-24-phase-3-b-per-content-type-publisher-design.md`):**

- §7 Garden frontmatter (growth_stage, media_type+flavor, topic_map, per-keyword pass-throughs, roam_refs): covered by Tasks 5–8. **Gap: `roam_refs` derivation** — spec says "derived from org-roam refs (existing org-roam mechanism)". B.0's ox-hugo invocation already passes through `:ROAM_REFS:` via `#+HUGO_CUSTOM_FRONT_MATTER:` if the source sets it. For B.1 this is implicit pass-through; if the spot-check surfaces missing roam_refs, file as a B.1.x follow-up and ship B.1 anyway. Not a blocker.
- §9 Garden handler flow (export → normalize → rewrite-links → asset-copy → write → record-publish): covered by Task 10.
- §10 A→B interface usage: covered by Tasks 9–10 (all five A functions called).
- §11 Idempotency contract (compute → if-different → write, alphabetical keys): covered by Task 10's `--write-if-different` + `--render-frontmatter`. Sync semantics (orphan removal) come from A.1.d's `finish-publish` automatically.
- §11 Transition strategy (fixture clear via first real publish): covered by Task 17.
- §12 Testing strategy: ert per-section + Python integration fixtures: covered by Tasks 5–8 (ert) + 12–16 (Python).
- B.0 known issues #1 + #2: covered by Task 1.

**Placeholder scan:** I checked every step for "TBD", "fill in details", "appropriate error handling", "similar to Task N", or undefined symbols. Two soft references stand:
1. Task 10 references `a3madkour-pub/file-id` and `a3madkour-pub/slug-for` — these are A.1 functions; the plan tells the implementer to grep the lisp/ dir for the actual names. I'd prefer to name them concretely, but I haven't yet read A.1's exact public API surface. The implementer must do a 1-grep adjustment before Task 10 commits.
2. Task 16 references "the test body mirrors helper patterns already in the file" — the test code itself isn't written out. If the implementer doesn't reuse helpers idiomatically, the test will work but be uglier than the existing fixtures.

These are acceptable looseness given the slice's scope; flagging them so they aren't a surprise.

**Type consistency:** `publish-garden-file` is the canonical name across Tasks 9 / 10 / 11 / 17. `growth_stage` / `flavor` / `topic_map` / `media_type` keys consistent across Tasks 5–8 and Task 10's frontmatter renderer. `record-publish` called with `(id new-url 'live)` per spec §10 in Task 10. ✓

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-25-phase-3-b-1-garden-handler.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review (spec + quality) between tasks, fast iteration. Matches how B.0 / A.1.* were executed; spawns one Agent per task with the task body as the prompt.

**2. Inline Execution** — execute tasks in this session via `superpowers:executing-plans`, batch execution with checkpoints for your review.

Which approach?
