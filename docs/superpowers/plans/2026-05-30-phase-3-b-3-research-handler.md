# Phase 3 B.3 — Research Handler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the third concrete per-content-type publisher (research), turning `~/org/notes/research-themes-<slug>.org` and `~/org/notes/research-questions-<slug>.org` source files into `content/research/themes/<slug>/index.md` and `content/research/questions/<slug>/index.md` per-page Hugo bundles via `a3-pub.sh --publish-living`. Two cascade types share one handler function; the function branches on `#+HUGO_SECTION:` only where contracts genuinely diverge (normalize step + outputs-table parse).

**Architecture:** New `a3madkour-publish-research.el` module exports `publish-research-file (file)`, registered twice in `a3madkour-pub-living--handlers` (one entry per cascade type, both pointing at the same function — mirrors B.2's library pattern). Internal branch on `#+HUGO_SECTION:` selects per-type frontmatter normalizer; the outputs-table parse runs only for questions. Shared steps (ox-hugo export, link-rewrite via B.1.1's `rewrite-buffer-links`, asset-copy via A.1.c, write-if-different, `record-publish`) are linear and identical to garden. Three shared helpers ship in support: `--filesystem-mtime-of-file` (extends the `last_modified` cascade, retroactively closes B.1.x #10 for garden), `#+HUGO_DESCRIPTION:` keyword wiring (new custom keyword, parallels `#+HUGO_GROWTH_STAGE:`), and the per-section research dispatch in `a3madkour-publish-frontmatter.el`.

**Tech Stack:** Emacs Lisp + ert (dotfiles); `org-element` AST traversal for outputs-table parse + subtree strip; Python integration fixtures under `tools/test_publish_integration.py` (stdlib only); existing site linters `check_research_fixtures.py` + `check_research_links.py` gate output shape.

**Cross-repo commit map:**
- Dotfiles repo (`~/dotfiles/`): all elisp + sibling tests + `a3-pub.sh` update.
- Site repo (this one): integration fixtures, `_publish_living_impl` `-l` extension, fixture-replace (in spot-check task), `CLAUDE.md` status pointer update, memory updates, parent-B-spec amendments.

**Reading list before starting:**
- `CLAUDE.md` (this repo) — current status pointer.
- `docs/superpowers/specs/2026-05-30-phase-3-b-3-research-handler-design.md` — §3 architecture, §5 frontmatter mapping, §6 outputs-table parse, §7 cross-link discipline, §8 last_modified cascade, §10 stub spot-check.
- `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` — §3, §5, §9 (parent context; this slice's spec supersedes the parent's research mapping).
- `docs/superpowers/plans/2026-05-29-phase-3-b-2-library-handler.md` — closest precedent for module scaffolding + integration-fixture layout.
- `docs/superpowers/plans/2026-05-25-phase-3-b-1-garden-handler.md` — closest precedent for per-page-bundle handler (research uses the same bundle shape as garden, not library's YAML rows).
- `tools/check_research_fixtures.py` + `tools/check_research_links.py` — authoritative shape contracts for B-emitted bundles.
- Memory: `.claude/memory/project_b2_complete.md`, `.claude/memory/project_b1_complete.md`, `.claude/memory/project_next_slice.md`, `.claude/memory/reference_goldmark_unsafe_for_ox_hugo_html.md`, `.claude/memory/reference_hugo_int_octal_gotcha.md`, `.claude/memory/feedback_plan_wrapper_script_updates.md`.
- Existing dotfiles modules to grep for call surface before extending: `a3madkour-publish.el` (`note-section`, `begin-publish`, `finish-publish`, dispatch-key form), `a3madkour-publish-history.el` (`record-publish`, `--git-mtime-of-file`), `a3madkour-publish-frontmatter.el` (B.1's garden normalizer + B.2's `--filter-editorial-tags`), `a3madkour-publish-living.el` (handler registration pattern via `with-eval-after-load`), `a3madkour-publish-export.el` (ox-hugo invoke + `--frontmatter-string-to-alist`).
- Existing site fixtures to mirror: `content/research/themes/*/index.md` and `content/research/questions/*/index.md` — shape B.3 must match.

---

## File Structure

**New files (dotfiles):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research.el` — research handler module. Exports `a3madkour-pub-research/publish-research-file`. Hosts `--parse-outputs-table`, `--strip-outputs-subtree`, the cascade-type branch logic, and the end-to-end pipeline.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research-test.el` — sibling test. ~25-30 tests across outputs-table parser, subtree-stripper, per-type normalizers, end-to-end publish.

**Modified files (dotfiles):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el` — add `--filesystem-mtime-of-file` helper.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el` — add 2 fs-mtime tests (file exists + file absent).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` — add `--last-modified-cascade` helper using the new fs-mtime fallback; integrate into garden normalizer (retroactive close of B.1.x #10) and dispatch through to a new `'research-themes` + `'research-questions` per-section normalizer. Add `#+HUGO_DESCRIPTION:` keyword support to `--frontmatter-string-to-alist` (or wherever HUGO_* custom keywords are parsed; verify before writing).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el` — add 6-8 tests: fs-mtime cascade ordering, HUGO_DESCRIPTION parsing, per-type research normalizer field validation (theme required/optional/forbidden + question required/optional + outputs passthrough).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el` — register 2 research handlers via `with-eval-after-load`.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el` — extend the registration test to assert both research entries.
- `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` — add `-l a3madkour-publish-research` to the three publish-side intercepts (publish-living, publish-deliberate, default-exec). NOT `--check-orphans`.

**Modified files (site repo):**
- `tools/test_publish_integration.py` — 6 new fixtures under `TestResearchPublishLiving` (publish-once for both types, idempotency, slug-shift, cross-ref WARN, removed-question unpublish + linter parity); add `_write_research_source` helper; add `-l a3madkour-publish-research` to the `_publish_living_impl` `-l` list.
- `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` — one-line amendment in §3 row for research: `research-theme` / `research-question` → `research-themes` / `research-questions` (matches content dir names + B.2 hyphen-to-slash convention); add `source_stream` + `#+HUGO_DESCRIPTION:` notes to §7 + §9.
- `CLAUDE.md` — status pointer update at slice end ("B.3 research handler shipped"); update "Next: B.4 (essays)".
- `.claude/memory/MEMORY.md` + `.claude/memory/project_b3_complete.md` (new) + `.claude/memory/project_next_slice.md` (updated to point at B.4).

**Touched at spot-check, not by automation:**
- `~/org/notes/research-themes-example-*.org` + `~/org/notes/research-questions-example-*.org` — ~6 hand-written stubs created in the spot-check task.
- `content/research/themes/*/` + `content/research/questions/*/` — 9 existing fixture bundles replaced wholesale by ~6 B-emitted stub bundles after running `a3-pub.sh --publish-living`.

---

## Task 1: `--filesystem-mtime-of-file` helper + `--last-modified-cascade` integration

**Why first:** Closes the last_modified gap (B.1.x #10) that bit B.2's stub spot-check. Garden + research both pick up the cascade as soon as it lands. Pure-IO function; no upstream dependencies; ships with sibling tests.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Grep the existing cascade.** Confirm where `--git-mtime-of-file` is called from today and how garden derives `last_modified`.

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
grep -nE "git-mtime-of-file|last_modified|LAST_MODIFIED|HUGO_LASTMOD" \
  a3madkour-publish-history.el a3madkour-publish-frontmatter.el a3madkour-publish-library.el
```

Expected: locations to extend. Likely B.2's `--normalize-item` reads `:LAST_MODIFIED:` drawer → `--git-mtime-of-file` as a 2-step cascade; garden's normalizer reads `#+HUGO_LASTMOD:` → file-mtime in `--normalize-garden`. The plan extends both to a 5-step cascade via a shared helper.

- [ ] **Step 2: Write failing fs-mtime tests in `a3madkour-publish-history-test.el`.**

```elisp
(ert-deftest a3madkour-pub-history--filesystem-mtime-existing-file ()
  "filesystem-mtime-of-file returns YYYY-MM-DD for an existing file."
  (let* ((tmpdir (make-temp-file "a3-pub-fsmtime-" t))
         (file (expand-file-name "x.org" tmpdir)))
    (unwind-protect
        (progn
          (with-temp-file file (insert "content\n"))
          (let ((result (a3madkour-pub-history/filesystem-mtime-of-file file)))
            (should (stringp result))
            (should (string-match-p "^[0-9]\\{4\\}-[0-9]\\{2\\}-[0-9]\\{2\\}$" result))))
      (delete-directory tmpdir t))))

(ert-deftest a3madkour-pub-history--filesystem-mtime-missing-file ()
  "filesystem-mtime-of-file returns nil for a missing file."
  (should-not (a3madkour-pub-history/filesystem-mtime-of-file
               "/nonexistent/path/x.org")))
```

- [ ] **Step 3: Run; expect failure.**

```bash
emacs --batch -L . -l a3madkour-publish-history -l a3madkour-publish-history-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: 2 failures (`Symbol's function definition is void`).

- [ ] **Step 4: Implement the helper.** Append to `a3madkour-publish-history.el` (before `(provide ...)`):

```elisp
(defun a3madkour-pub-history/filesystem-mtime-of-file (file)
  "Return the YYYY-MM-DD filesystem mtime of FILE.
Returns nil when FILE does not exist.

Used as the ultimate fallback for `last_modified' when neither
:LAST_MODIFIED: drawer, #+HUGO_LASTMOD: keyword, nor git-mtime
(`--git-mtime-of-file') yields a value.  Best-effort idempotence —
editor saves with no content change bump mtime and will produce a
publish diff."
  (when (file-exists-p file)
    (format-time-string "%Y-%m-%d"
                        (file-attribute-modification-time
                         (file-attributes file)))))
```

- [ ] **Step 5: Run; expect green.**

```bash
emacs --batch -L . -l a3madkour-publish-history -l a3madkour-publish-history-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

- [ ] **Step 6: Write failing cascade test in `a3madkour-publish-frontmatter-test.el`.**

```elisp
(ert-deftest a3madkour-pub-frontmatter--last-modified-cascade-drawer-wins ()
  ":LAST_MODIFIED: drawer beats keyword + git-mtime + fs-mtime."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2024-01-01"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2025-01-01")))
    (should (equal (a3madkour-pub-frontmatter/last-modified-cascade
                    "/tmp/x.org" :drawer "2026-05-30" :keyword "2026-05-29")
                   "2026-05-30"))))

(ert-deftest a3madkour-pub-frontmatter--last-modified-cascade-keyword-second ()
  "#+HUGO_LASTMOD: keyword wins when drawer absent."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2024-01-01"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2025-01-01")))
    (should (equal (a3madkour-pub-frontmatter/last-modified-cascade
                    "/tmp/x.org" :keyword "2026-05-29")
                   "2026-05-29"))))

(ert-deftest a3madkour-pub-frontmatter--last-modified-cascade-git-third ()
  "git-mtime wins when drawer + keyword absent."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2024-01-01"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2025-01-01")))
    (should (equal (a3madkour-pub-frontmatter/last-modified-cascade "/tmp/x.org")
                   "2024-01-01"))))

(ert-deftest a3madkour-pub-frontmatter--last-modified-cascade-fs-fourth ()
  "fs-mtime wins when drawer + keyword + git absent."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) nil))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2025-01-01")))
    (should (equal (a3madkour-pub-frontmatter/last-modified-cascade "/tmp/x.org")
                   "2025-01-01"))))

(ert-deftest a3madkour-pub-frontmatter--last-modified-cascade-today-fallback ()
  "today is the ultimate fallback when nothing else resolves."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) nil))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) nil)))
    (let ((result (a3madkour-pub-frontmatter/last-modified-cascade "/tmp/x.org"))
          (today (format-time-string "%Y-%m-%d")))
      (should (equal result today)))))
```

- [ ] **Step 7: Run; expect failure.**

```bash
emacs --batch -L . -l a3madkour-publish-frontmatter -l a3madkour-publish-frontmatter-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

- [ ] **Step 8: Implement the cascade helper.** Append to `a3madkour-publish-frontmatter.el` (after the existing helpers, before per-section dispatch):

```elisp
(cl-defun a3madkour-pub-frontmatter/last-modified-cascade
    (file &key drawer keyword)
  "Resolve the last_modified value for FILE via the 5-step cascade.

Cascade order:
  1. DRAWER (the :LAST_MODIFIED: property if present in the source)
  2. KEYWORD (the #+HUGO_LASTMOD: keyword value if present)
  3. git-mtime via `a3madkour-pub-history/git-mtime-of-file'
  4. filesystem mtime via `a3madkour-pub-history/filesystem-mtime-of-file'
  5. today (`format-time-string \"%Y-%m-%d\"')

Returns a YYYY-MM-DD string; never nil.  Drawer + keyword are passed
in by per-section normalizers (each section reads them from different
places — file-level keyword for garden/essays/research, per-heading
drawer for library)."
  (or drawer
      keyword
      (a3madkour-pub-history/git-mtime-of-file file)
      (a3madkour-pub-history/filesystem-mtime-of-file file)
      (format-time-string "%Y-%m-%d")))
```

- [ ] **Step 9: Update the garden normalizer to use the cascade.** Find the existing `last_modified` derivation in `--normalize-garden` (likely a `or` chain reading `#+HUGO_LASTMOD:` + file-mtime). Replace with a call to `last-modified-cascade`:

```elisp
;; Replace the existing last_modified derivation block with:
(setf (alist-get 'last_modified out)
      (a3madkour-pub-frontmatter/last-modified-cascade
       source-file
       :keyword (alist-get 'lastmod raw)))   ; ox-hugo's emitted key
```

> **Note:** the exact key (`'lastmod` vs `'last_modified`) depends on what ox-hugo emits and whether the existing garden normalizer already renames it. Grep first; pattern-match the existing code. If the existing code reads `(alist-get 'last_modified out)`, that's the key to pass.

- [ ] **Step 10: Run full suite + ensure existing garden tests pass.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: `Ran 314 tests, 314 results as expected, 0 unexpected.` (309 baseline + 2 fs-mtime + 5 cascade − any garden tests that asserted on the OLD `last_modified` derivation that the cascade now supersedes; adjust those tests if any).

> **If a garden test fails:** it's likely asserting on file-mtime fallback. The cascade preserves that as step 4, but if the test stubbed file-mtime and now hits git-mtime first, fix the test to stub both `git-mtime-of-file` + `filesystem-mtime-of-file`.

- [ ] **Step 11: Commit (dotfiles).**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-history.el \
        emacs-configs/custom/lisp/a3madkour-publish-history-test.el \
        emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el \
        emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "feat(b-3): last_modified cascade w/ fs-mtime fallback

Adds filesystem-mtime-of-file helper + last-modified-cascade helper
covering drawer → keyword → git → fs → today.  Garden normalizer
switched to the cascade — closes B.1.x #10 (no fs-mtime fallback bit
B.2 stub spot-check on untracked ~/org/notes/).  Research will pick
the cascade up in Task 5."
```

---

## Task 2: `#+HUGO_DESCRIPTION:` keyword support

**Why now:** Required field on both research types; shared infra change needed before per-section normalizers can read it. Parallels `#+HUGO_GROWTH_STAGE:` pattern that B.1 already wired.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` (or `a3madkour-publish-export.el` — verify in Step 1)
- Modify: corresponding test file

- [ ] **Step 1: Grep for existing custom HUGO_* keyword wiring.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
grep -nE "HUGO_GROWTH_STAGE|HUGO_MEDIA_TYPE|HUGO_TOPIC_MAP" \
  a3madkour-publish-export.el a3madkour-publish-frontmatter.el
```

Expected: locate the function that scans the org buffer for custom `#+HUGO_*:` keywords and adds them to the raw frontmatter alist. Likely in `a3madkour-publish-export.el` (its `--frontmatter-string-to-alist` or sibling). Pattern-match B.1's approach exactly.

- [ ] **Step 2: Write failing test.** In the same test file where HUGO_GROWTH_STAGE is tested (or a new dedicated test file for the keyword parser):

```elisp
(ert-deftest a3madkour-pub-frontmatter--hugo-description-keyword ()
  "#+HUGO_DESCRIPTION: keyword parsed into the raw frontmatter alist as 'description."
  (let* ((src "#+title: Theme One
#+HUGO_PUBLISH: t
#+HUGO_SECTION: research-themes
#+HUGO_DESCRIPTION: A short description of the theme.
")
         (alist (a3madkour-pub-export/frontmatter-string-to-alist src)))
    (should (equal (alist-get 'description alist)
                   "A short description of the theme."))))
```

> **Adjust the function name** to whatever Step 1's grep identified as the keyword parser entry point.

- [ ] **Step 3: Run; expect failure.**

- [ ] **Step 4: Wire `#+HUGO_DESCRIPTION:` into the keyword parser.** Locate the alist that maps `HUGO_*` keyword strings to alist symbol keys (or the equivalent dispatch). Add an entry:

```elisp
;; Add to the existing custom-keyword mapping list:
("HUGO_DESCRIPTION" . description)
```

> **Note:** if the parser uses ox-hugo's `HUGO_CUSTOM_FRONT_MATTER :description ...` escape hatch instead of a dedicated keyword mapping, the wiring goes through that path. The spec'd shape is a top-level `#+HUGO_DESCRIPTION:` keyword that lands in the alist as `'description`.

- [ ] **Step 5: Run; expect green.**

- [ ] **Step 6: Full ert suite.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: 315 tests pass (314 + 1).

- [ ] **Step 7: Commit.**

```bash
git commit -m "feat(b-3): #+HUGO_DESCRIPTION: keyword support

Parallels HUGO_GROWTH_STAGE wiring.  Required field on both research
themes + questions (per check_research_fixtures.py).  Themes carry
both description + summary as distinct fields."
```

---

## Task 3: Scaffold `a3madkour-publish-research.el` module + sibling test + `a3-pub.sh` `-l` line + integration-test `-l` extension

**Why before implementation:** Stub the new module + register it in the wrapper + integration-test loader so all subsequent tasks start from a loadable state. Per [[plan-wrapper-script-updates]] feedback, add the `-l` lines up front (not at the end).

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research-test.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`
- Modify: `tools/test_publish_integration.py` (site repo — `_publish_living_impl` `-l` list)

- [ ] **Step 1: Create the module scaffold.** Write to `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research.el`:

```elisp
;;; a3madkour-publish-research.el --- research per-page bundle handler  -*- lexical-binding: t; -*-

;;; Commentary:

;; B.3: research per-page bundle handler.  Two cascade types share one
;; handler function: themes (research-themes) and questions
;; (research-questions).  Both emit per-page Hugo bundles at
;; content/research/<themes|questions>/<slug>/index.md.
;;
;; Internal branch on #+HUGO_SECTION: selects per-type frontmatter
;; normalizer + the outputs-table parse (question-only).  Everything
;; else — ox-hugo export, link-rewrite, asset-copy, write-if-different,
;; record-publish — is shared with garden.
;;
;; Registered into `a3madkour-pub-living--handlers' as two entries
;; (one per cascade type, both pointing at the same `publish-research-file'
;; entry point) by `a3madkour-publish-living'.

;;; Code:

(require 'cl-lib)
(require 'org-element)
(require 'a3madkour-publish)
(require 'a3madkour-publish-export)
(require 'a3madkour-publish-frontmatter)
(require 'a3madkour-publish-history)
(require 'a3madkour-publish-rewrite)
(require 'a3madkour-publish-assets)

(defun a3madkour-pub-research/publish-research-file (file)
  "Publish a single research FILE to content/research/<type>/<slug>/index.md.

Stub (Task 3): signature only; real implementation lands in Tasks 4-10."
  (ignore file)
  nil)

(provide 'a3madkour-publish-research)

;;; a3madkour-publish-research.el ends here
```

- [ ] **Step 2: Create the sibling test scaffold.** Write to `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research-test.el`:

```elisp
;;; a3madkour-publish-research-test.el --- tests for research handler  -*- lexical-binding: t; -*-

(require 'ert)
(require 'a3madkour-publish-research)

(ert-deftest a3madkour-pub-research--module-loads ()
  "Smoke: module loadable and exposes publish-research-file."
  (should (fboundp 'a3madkour-pub-research/publish-research-file)))

(provide 'a3madkour-publish-research-test)

;;; a3madkour-publish-research-test.el ends here
```

- [ ] **Step 3: Add `-l a3madkour-publish-research` to `a3-pub.sh`.** Three publish-side intercepts need the line; `--check-orphans` does NOT.

```bash
grep -n "a3madkour-publish-library" ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh
```

Expected: three lines (one per publish-side intercept) like `    -l a3madkour-publish-library \`.

In each of those three locations, add immediately AFTER the library line:

```bash
    -l a3madkour-publish-research \
```

- [ ] **Step 4: Add `-l a3madkour-publish-research` to `_publish_living_impl` in `tools/test_publish_integration.py`.**

```bash
grep -n "a3madkour-publish-library" tools/test_publish_integration.py
```

Find the `_publish_living_impl` function's `subprocess.run([...])` args list. Add immediately after the `"a3madkour-publish-library",` line:

```python
            "-l", "a3madkour-publish-research",
```

- [ ] **Step 5: Run the new sibling test.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . -l a3madkour-publish-research -l a3madkour-publish-research-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: 1 pass.

- [ ] **Step 6: Run full suite + smoke the wrapper.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3

cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
```

Expected: 316 tests pass (315 + 1 new); `--publish-living` exits 0 (handler stub not yet registered in living).

- [ ] **Step 7: Commit (dotfiles + site).**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-research.el \
        emacs-configs/custom/lisp/a3madkour-publish-research-test.el \
        emacs-configs/custom/lisp/a3-pub.sh
git commit -m "scaffold(b-3): a3madkour-publish-research module + wrapper -l lines

Stub publish-research-file + smoke test.  Wrapper + integration-test
stacks updated.  Real implementation in Tasks 4-10."

cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add tools/test_publish_integration.py
git commit -m "scaffold(b-3): include a3madkour-publish-research in integration-test loader

Mirrors a3-pub.sh's bootstrap incantation so per-test publish-living
runs can dispatch to the research handler."
```

---

## Task 4: `--research-normalize-common` shared helper

**Spec §5 common fields:** title, draft, last_modified (via cascade), tags (filtered), description (HUGO_DESCRIPTION), summary, source_stream. Shared between both cascade types.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-frontmatter--research-normalize-common-shape ()
  "Common-field normalize covers title/draft/last_modified/tags/description/summary/source_stream."
  (let* ((raw '((title . "Theme One")
                (draft . nil)
                (lastmod . "2026-05-30")
                (tags . ("alpha" "TODO" "beta"))
                (description . "A short description.")
                (summary . "An umbrella thread.")
                (source_stream . "2026-04-10-example-stream")))
         (out (a3madkour-pub-frontmatter/research-normalize-common
               raw "/tmp/x.org")))
    (should (equal (alist-get 'title out) "Theme One"))
    (should (equal (alist-get 'last_modified out) "2026-05-30"))
    (should (equal (alist-get 'tags out) '("alpha" "beta")))   ; TODO filtered
    (should (equal (alist-get 'description out) "A short description."))
    (should (equal (alist-get 'summary out) "An umbrella thread."))
    (should (equal (alist-get 'source_stream out) "2026-04-10-example-stream"))))

(ert-deftest a3madkour-pub-frontmatter--research-normalize-common-defaults ()
  "Missing optional keys are not emitted; required keys derive from cascade."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-01-15"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-01-15")))
    (let* ((raw '((title . "Q1")))
           (out (a3madkour-pub-frontmatter/research-normalize-common
                 raw "/tmp/x.org")))
      (should (equal (alist-get 'title out) "Q1"))
      (should (equal (alist-get 'last_modified out) "2026-01-15"))
      (should-not (assq 'summary out))
      (should-not (assq 'source_stream out))
      (should-not (assq 'description out)))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.** Add to `a3madkour-publish-frontmatter.el` (near the existing garden + library normalizers):

```elisp
(defun a3madkour-pub-frontmatter/research-normalize-common (raw source-file)
  "Apply common-across-both-research-types normalization to RAW alist.
Returns a NEW alist with the cleaned shared fields populated.  Caller
(theme or question per-type normalizer) layers on the type-specific
fields and emits the final alist."
  (let ((out (copy-alist raw)))
    ;; last_modified: cascade.
    (setf (alist-get 'last_modified out)
          (a3madkour-pub-frontmatter/last-modified-cascade
           source-file
           :drawer (alist-get 'last_modified raw)
           :keyword (alist-get 'lastmod raw)))
    ;; Drop ox-hugo's `lastmod' once cascade is resolved.
    (setq out (assq-delete-all 'lastmod out))
    ;; Tags: filter editorial.
    (when-let ((tags (alist-get 'tags out)))
      (setf (alist-get 'tags out)
            (a3madkour-pub-frontmatter/filter-editorial-tags tags)))
    ;; description / summary / source_stream are pass-through from raw
    ;; (already present via custom HUGO_* keyword wiring).  Drop only if
    ;; raw value is nil/empty.
    (dolist (key '(description summary source_stream))
      (let ((v (alist-get key out)))
        (when (or (null v) (and (stringp v) (string-empty-p v)))
          (setq out (assq-delete-all key out)))))
    out))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Commit.**

```bash
git commit -m "feat(b-3): research-normalize-common shared helper

Title/draft pass-through; last_modified via cascade; tags through
editorial filter; description/summary/source_stream pass-through with
empty-string drop.  Theme + question normalizers layer on this in
Tasks 5 + 6."
```

---

## Task 5: Theme normalizer + per-section dispatch entry

**Spec §5 theme-only:** status (enum `{active, dormant, answered}`), weight (int), garden_topic_ref (optional). Forbidden: parent_question, theme.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-frontmatter--research-theme-required-fields ()
  "Theme required fields land in the output alist."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-05-30"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-05-30")))
    (let* ((raw '((title . "Memory and play")
                  (description . "How readers assemble fragments.")
                  (status . "active")
                  (weight . "10")
                  (garden_topic_ref . "memory-in-play")
                  (tags . ("memory" "play"))))
           (out (a3madkour-pub-frontmatter/normalize 'research-themes raw "/tmp/x.org")))
      (should (equal (alist-get 'title out) "Memory and play"))
      (should (equal (alist-get 'status out) "active"))
      (should (equal (alist-get 'weight out) 10))     ; coerced int
      (should (equal (alist-get 'garden_topic_ref out) "memory-in-play")))))

(ert-deftest a3madkour-pub-frontmatter--research-theme-weight-octal-safe ()
  "weight string parsing is octal-safe (per [[hugo-int-octal-gotcha]])."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-05-30"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-05-30")))
    (let* ((raw '((title . "Z") (description . "x") (status . "active")
                  (weight . "08")))
           (out (a3madkour-pub-frontmatter/normalize 'research-themes raw "/tmp/x.org")))
      ;; "08" must NOT octal-trap into a parse error; expect int 8.
      (should (equal (alist-get 'weight out) 8)))))

(ert-deftest a3madkour-pub-frontmatter--research-theme-forbidden-fields-dropped ()
  "parent_question + theme silently dropped on themes (linter is the gate)."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-05-30"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-05-30")))
    (let* ((raw '((title . "T")
                  (description . "x")
                  (status . "active")
                  (parent_question . "qslug")
                  (theme . "other-theme")))
           (out (a3madkour-pub-frontmatter/normalize 'research-themes raw "/tmp/x.org")))
      (should-not (assq 'parent_question out))
      (should-not (assq 'theme out)))))

(ert-deftest a3madkour-pub-frontmatter--research-theme-status-enum-warn ()
  "Out-of-enum status WARNs but still emits."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-05-30"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-05-30")))
    (let* ((raw '((title . "T") (description . "x") (status . "bogus")))
           (warnings '())
           (out (cl-letf (((symbol-function 'message)
                           (lambda (fmt &rest args)
                             (push (apply #'format fmt args) warnings))))
                  (a3madkour-pub-frontmatter/normalize 'research-themes raw "/tmp/x.org"))))
      (should (equal (alist-get 'status out) "bogus"))
      (should (seq-some (lambda (m) (string-match-p "status.*bogus.*not in" m)) warnings)))))
```

- [ ] **Step 2: Run; expect failure** (dispatch on `'research-themes` doesn't exist yet).

- [ ] **Step 3: Implement the theme normalizer + dispatch entry.** Add to `a3madkour-publish-frontmatter.el`:

```elisp
(defconst a3madkour-pub-frontmatter--research-statuses
  '("active" "dormant" "answered")
  "Allowed status values for research themes + questions
(per check_research_fixtures.py STATUSES).")

(defconst a3madkour-pub-frontmatter--theme-forbidden
  '(parent_question theme)
  "Frontmatter keys forbidden on themes (per check_research_fixtures.py
THEME_FORBIDDEN).  Dropped silently in the normalizer; site linter
is the hard gate.")

(defun a3madkour-pub-frontmatter--coerce-weight (raw file)
  "Coerce RAW weight value to int.  String '08' must not octal-trap
(per [[hugo-int-octal-gotcha]]).  Non-numeric raw → WARN + nil."
  (cond
   ((null raw) nil)
   ((integerp raw) raw)
   ((stringp raw)
    (let ((cleaned (string-trim raw)))
      (cond
       ((string-empty-p cleaned) nil)
       ;; Float-trip avoids the octal trap.
       ((string-match-p "^[+-]?[0-9]+\\(\\.[0-9]+\\)?$" cleaned)
        (truncate (string-to-number cleaned)))
       (t (message "a3madkour-pub-frontmatter WARN [%s]: weight=%S non-numeric"
                   (file-name-nondirectory file) raw)
          nil))))
   (t nil)))

(defun a3madkour-pub-frontmatter--normalize-research-theme (raw file)
  "Normalize a research-theme RAW alist.  Returns the cleaned alist."
  (let ((out (a3madkour-pub-frontmatter/research-normalize-common raw file)))
    ;; Status enum check (WARN-don't-fail).
    (let ((status (alist-get 'status out)))
      (unless (member status a3madkour-pub-frontmatter--research-statuses)
        (message "a3madkour-pub-frontmatter WARN [%s]: status=%S not in %S"
                 (file-name-nondirectory file) status
                 a3madkour-pub-frontmatter--research-statuses)))
    ;; Weight coercion to int (octal-safe).
    (when-let ((raw-w (alist-get 'weight out)))
      (setf (alist-get 'weight out)
            (a3madkour-pub-frontmatter--coerce-weight raw-w file)))
    ;; Drop forbidden keys silently.
    (dolist (key a3madkour-pub-frontmatter--theme-forbidden)
      (setq out (assq-delete-all key out)))
    out))
```

Then extend the existing per-section dispatch in `a3madkour-pub-frontmatter/normalize` (the function that routes on the section symbol). Find the existing dispatch (likely a `cond` or `pcase`) and add a clause:

```elisp
;; Add to the existing per-section dispatch in `normalize`:
((eq section 'research-themes)
 (a3madkour-pub-frontmatter--normalize-research-theme raw source-file))
```

- [ ] **Step 4: Run; expect green.**

```bash
emacs --batch -L . -l a3madkour-publish-frontmatter -l a3madkour-publish-frontmatter-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

- [ ] **Step 5: Commit.**

```bash
git commit -m "feat(b-3): theme normalizer + per-section dispatch entry

Status enum WARN (active|dormant|answered); weight coerced to int via
octal-safe float-trip; parent_question + theme silently dropped on
themes (per check_research_fixtures.py THEME_FORBIDDEN)."
```

---

## Task 6: Question normalizer + per-section dispatch entry

**Spec §5 question-only:** theme (required slug), parent_question (optional), status (enum), weight (int optional), started (date), supporting_notes (space-delimited slug list), related_essays (space-delimited slug list). `outputs:` is wired separately in Tasks 7-9.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-frontmatter--research-question-required-fields ()
  "Question required fields + slug-list parsing."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-05-30"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-05-30")))
    (let* ((raw '((title . "What is a narrative atom?")
                  (description . "Active question.")
                  (theme . "procedural-narrative")
                  (status . "active")
                  (supporting_notes . "story-atoms recall-vs-replay")
                  (related_essays . "example-essay-two")
                  (tags . ("narrative"))))
           (out (a3madkour-pub-frontmatter/normalize 'research-questions raw "/tmp/x.org")))
      (should (equal (alist-get 'theme out) "procedural-narrative"))
      (should (equal (alist-get 'status out) "active"))
      (should (equal (alist-get 'supporting_notes out)
                     '("story-atoms" "recall-vs-replay")))
      (should (equal (alist-get 'related_essays out)
                     '("example-essay-two"))))))

(ert-deftest a3madkour-pub-frontmatter--research-question-optional-passthroughs ()
  "Optional question fields pass through; absent → omitted."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-05-30"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-05-30")))
    (let* ((raw '((title . "Q") (description . "x") (theme . "t") (status . "active")
                  (parent_question . "qparent")
                  (started . "2025-09-01")
                  (weight . "20")))
           (out (a3madkour-pub-frontmatter/normalize 'research-questions raw "/tmp/x.org")))
      (should (equal (alist-get 'parent_question out) "qparent"))
      (should (equal (alist-get 'started out) "2025-09-01"))
      (should (equal (alist-get 'weight out) 20)))))

(ert-deftest a3madkour-pub-frontmatter--research-question-slug-list-empty ()
  "Empty supporting_notes / related_essays → key omitted, not emitted as [\"\"]."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-05-30"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-05-30")))
    (let* ((raw '((title . "Q") (description . "x") (theme . "t") (status . "active")
                  (supporting_notes . "")))
           (out (a3madkour-pub-frontmatter/normalize 'research-questions raw "/tmp/x.org")))
      (should-not (assq 'supporting_notes out)))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.** Add to `a3madkour-publish-frontmatter.el`:

```elisp
(defun a3madkour-pub-frontmatter--parse-slug-list (raw)
  "Parse a space-delimited slug-list string RAW into a list of strings.
Empty string or nil → nil."
  (cond
   ((null raw) nil)
   ((listp raw) raw)
   ((stringp raw)
    (let ((trimmed (string-trim raw)))
      (when (and trimmed (not (string-empty-p trimmed)))
        (split-string trimmed "[ \t]+" t))))
   (t nil)))

(defun a3madkour-pub-frontmatter--normalize-research-question (raw file)
  "Normalize a research-question RAW alist.  Returns the cleaned alist."
  (let ((out (a3madkour-pub-frontmatter/research-normalize-common raw file)))
    ;; Status enum check.
    (let ((status (alist-get 'status out)))
      (unless (member status a3madkour-pub-frontmatter--research-statuses)
        (message "a3madkour-pub-frontmatter WARN [%s]: status=%S not in %S"
                 (file-name-nondirectory file) status
                 a3madkour-pub-frontmatter--research-statuses)))
    ;; Weight coercion.
    (when-let ((raw-w (alist-get 'weight out)))
      (setf (alist-get 'weight out)
            (a3madkour-pub-frontmatter--coerce-weight raw-w file)))
    ;; Slug-list parses (supporting_notes, related_essays).
    (dolist (key '(supporting_notes related_essays))
      (let* ((raw-v (alist-get key out))
             (parsed (a3madkour-pub-frontmatter--parse-slug-list raw-v)))
        (if parsed
            (setf (alist-get key out) parsed)
          (setq out (assq-delete-all key out)))))
    ;; outputs: emitted separately in Task 9 (publish-research-file injects
    ;; the parsed outputs plist list).  At normalize time, drop any pre-
    ;; existing outputs key from raw (should never appear via custom keywords).
    (setq out (assq-delete-all 'outputs out))
    out))
```

Extend the per-section dispatch:

```elisp
;; Add to the existing per-section dispatch in `normalize`:
((eq section 'research-questions)
 (a3madkour-pub-frontmatter--normalize-research-question raw source-file))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Full ert suite.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: ~327 tests pass (~322 + ~5 new).

- [ ] **Step 6: Commit.**

```bash
git commit -m "feat(b-3): question normalizer + per-section dispatch entry

Status enum WARN; weight coerced (octal-safe); supporting_notes +
related_essays parsed from space-delimited strings to lists; empty
slug-lists drop the key entirely.  outputs: emission deferred to
publish-research-file (Tasks 7-9 + 10)."
```

---

## Task 7: `--parse-outputs-table` helper

**Spec §6:** Scan parsed org buffer for `* Outputs` heading (case-insensitive raw value), find the first `table` element under it, parse rows to plist list. Header row checks for columns `kind`, `title`, `url`, `year` (case-insensitive). Unknown kind → WARN + skip row. Year coerced to int via float-trip.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(defun a3madkour-pub-research-test--parse-buffer (org-text)
  "Helper: parse ORG-TEXT and return the full element AST."
  (with-temp-buffer
    (insert org-text)
    (org-mode)
    (org-element-parse-buffer)))

(ert-deftest a3madkour-pub-research--parse-outputs-table-happy ()
  "Well-formed outputs table parses to a plist list, row order preserved."
  (let* ((ast (a3madkour-pub-research-test--parse-buffer "
* Outputs                                                  :outputs:
| kind  | title                | url                          | year |
|-------+----------------------+------------------------------+------|
| paper | Save States as Edits | https://example.com/paper    | 2024 |
| talk  | Save States as Edits | https://example.com/talk     | 2024 |
| code  | save-replay-tool     | https://github.com/example/x | 2024 |
"))
         (outputs (a3madkour-pub-research--parse-outputs-table ast "/tmp/x.org")))
    (should (= 3 (length outputs)))
    (should (equal (plist-get (nth 0 outputs) :kind) "paper"))
    (should (equal (plist-get (nth 0 outputs) :title) "Save States as Edits"))
    (should (equal (plist-get (nth 0 outputs) :url) "https://example.com/paper"))
    (should (equal (plist-get (nth 0 outputs) :year) 2024))
    (should (equal (plist-get (nth 1 outputs) :kind) "talk"))
    (should (equal (plist-get (nth 2 outputs) :kind) "code"))))

(ert-deftest a3madkour-pub-research--parse-outputs-table-no-heading ()
  "No * Outputs heading → nil."
  (let ((ast (a3madkour-pub-research-test--parse-buffer "* Some other heading\nbody.\n")))
    (should-not (a3madkour-pub-research--parse-outputs-table ast "/tmp/x.org"))))

(ert-deftest a3madkour-pub-research--parse-outputs-table-empty-heading ()
  "* Outputs heading with no table → nil + WARN."
  (let* ((ast (a3madkour-pub-research-test--parse-buffer "* Outputs\nNo table.\n"))
         (warnings '())
         (result (cl-letf (((symbol-function 'message)
                            (lambda (fmt &rest args)
                              (push (apply #'format fmt args) warnings))))
                   (a3madkour-pub-research--parse-outputs-table ast "/tmp/x.org"))))
    (should-not result)
    (should (seq-some (lambda (m) (string-match-p "outputs heading.*no table" m)) warnings))))

(ert-deftest a3madkour-pub-research--parse-outputs-table-missing-column ()
  "Header missing required column → WARN + nil."
  (let* ((ast (a3madkour-pub-research-test--parse-buffer "
* Outputs
| kind  | title                | url                          |
|-------+----------------------+------------------------------|
| paper | Save States as Edits | https://example.com/paper    |
"))
         (warnings '())
         (result (cl-letf (((symbol-function 'message)
                            (lambda (fmt &rest args)
                              (push (apply #'format fmt args) warnings))))
                   (a3madkour-pub-research--parse-outputs-table ast "/tmp/x.org"))))
    (should-not result)
    (should (seq-some (lambda (m) (string-match-p "missing.*year" m)) warnings))))

(ert-deftest a3madkour-pub-research--parse-outputs-table-unknown-kind-skipped ()
  "Unknown kind row → WARN + skipped; rest of table parsed."
  (let* ((ast (a3madkour-pub-research-test--parse-buffer "
* Outputs
| kind     | title  | url                  | year |
|----------+--------+----------------------+------|
| paper    | Real   | https://example.com  | 2024 |
| dataset  | Bogus  | https://other.com    | 2025 |
| code     | Tool   | https://gh.com       | 2024 |
"))
         (warnings '())
         (outputs (cl-letf (((symbol-function 'message)
                             (lambda (fmt &rest args)
                               (push (apply #'format fmt args) warnings))))
                    (a3madkour-pub-research--parse-outputs-table ast "/tmp/x.org"))))
    (should (= 2 (length outputs)))
    (should (equal (plist-get (nth 0 outputs) :kind) "paper"))
    (should (equal (plist-get (nth 1 outputs) :kind) "code"))
    (should (seq-some (lambda (m) (string-match-p "kind=dataset.*skip" m)) warnings))))

(ert-deftest a3madkour-pub-research--parse-outputs-table-year-octal-safe ()
  "Year string '08' must coerce to int 8 without octal trap."
  (let* ((ast (a3madkour-pub-research-test--parse-buffer "
* Outputs
| kind  | title  | url                  | year |
|-------+--------+----------------------+------|
| paper | Real   | https://example.com  | 08   |
"))
         (outputs (a3madkour-pub-research--parse-outputs-table ast "/tmp/x.org")))
    (should (equal (plist-get (nth 0 outputs) :year) 8))))

(ert-deftest a3madkour-pub-research--parse-outputs-table-case-insensitive-heading ()
  "* outputs and * OUTPUTS both match (raw-value compared case-insensitively)."
  (dolist (heading '("outputs" "OUTPUTS" "OutPuts"))
    (let* ((ast (a3madkour-pub-research-test--parse-buffer
                 (format "
* %s
| kind  | title  | url                  | year |
|-------+--------+----------------------+------|
| paper | Real   | https://example.com  | 2024 |
" heading)))
           (outputs (a3madkour-pub-research--parse-outputs-table ast "/tmp/x.org")))
      (should (= 1 (length outputs))))))
```

- [ ] **Step 2: Run; expect failure.**

```bash
emacs --batch -L . -l a3madkour-publish-research -l a3madkour-publish-research-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

- [ ] **Step 3: Implement.** Add to `a3madkour-publish-research.el`:

```elisp
(defconst a3madkour-pub-research--output-kinds
  '("paper" "talk" "code")
  "Allowed kind values in the outputs table
(per check_research_fixtures.py:20 OUTPUT_KINDS).")

(defconst a3madkour-pub-research--output-cols
  '("kind" "title" "url" "year")
  "Required columns in the outputs table header row.")

(defun a3madkour-pub-research--warn (file fmt &rest args)
  "Emit a WARN message with FILE context."
  (apply #'message (concat "a3madkour-pub-research WARN [%s]: " fmt)
         (file-name-nondirectory file) args))

(defun a3madkour-pub-research--find-outputs-heading (ast)
  "Find the first headline in AST whose raw value matches 'Outputs' (case-insensitive).
Returns the headline element or nil."
  (cl-loop for hl in (org-element-map ast 'headline #'identity)
           for raw = (org-element-property :raw-value hl)
           when (and raw (string-equal (downcase raw) "outputs"))
           return hl))

(defun a3madkour-pub-research--find-table-under (headline)
  "Return the first table element directly under HEADLINE, or nil."
  (cl-loop for child in (org-element-contents headline)
           when (eq (org-element-type child) 'table)
           return child))

(defun a3madkour-pub-research--table-rows (table)
  "Return TABLE's data rows as list-of-list-of-cell-strings.
Skips horizontal-rule rows; the header row is the first standard row."
  (cl-loop for row in (org-element-map table 'table-row #'identity)
           when (eq (org-element-property :type row) 'standard)
           collect (mapcar (lambda (cell)
                             (let ((c (car (org-element-contents cell))))
                               (cond
                                ((stringp c) (string-trim c))
                                ((null c) "")
                                (t (string-trim
                                    (substring-no-properties
                                     (org-element-interpret-data c)))))))
                           (org-element-contents row))))

(defun a3madkour-pub-research--coerce-year (raw file)
  "Coerce year RAW to int.  Float-trip to dodge octal trap on '08'/'09'."
  (when (and raw (stringp raw))
    (let ((cleaned (string-trim raw)))
      (when (string-match-p "^[0-9]+$" cleaned)
        (truncate (string-to-number cleaned))))))

(defun a3madkour-pub-research--parse-outputs-table (ast file)
  "Parse the * Outputs table in AST.  Returns list of plists, or nil.
WARNs on heading-without-table, missing columns, unknown kinds.
Row order preserved.  See spec §6 for the table contract."
  (let ((heading (a3madkour-pub-research--find-outputs-heading ast)))
    (unless heading
      (cl-return-from a3madkour-pub-research--parse-outputs-table nil))
    (let ((table (a3madkour-pub-research--find-table-under heading)))
      (unless table
        (a3madkour-pub-research--warn file "outputs heading present but no table")
        (cl-return-from a3madkour-pub-research--parse-outputs-table nil))
      (let* ((rows (a3madkour-pub-research--table-rows table))
             (header (mapcar #'downcase (car rows)))
             (data-rows (cdr rows))
             (col-indices (mapcar (lambda (col)
                                    (cl-position col header :test #'string-equal))
                                  a3madkour-pub-research--output-cols))
             (results '()))
        ;; Verify all required columns present.
        (cl-loop for col in a3madkour-pub-research--output-cols
                 for idx in col-indices
                 unless idx
                 do (a3madkour-pub-research--warn
                     file "outputs table missing column %S" col))
        (when (memq nil col-indices)
          (cl-return-from a3madkour-pub-research--parse-outputs-table nil))
        ;; Build per-row plists.
        (dolist (row data-rows)
          (let* ((kind (nth (nth 0 col-indices) row))
                 (title (nth (nth 1 col-indices) row))
                 (url (nth (nth 2 col-indices) row))
                 (year-raw (nth (nth 3 col-indices) row))
                 (year (a3madkour-pub-research--coerce-year year-raw file)))
            (cond
             ((not (member kind a3madkour-pub-research--output-kinds))
              (a3madkour-pub-research--warn
               file "outputs row kind=%s not in %S; skipping"
               kind a3madkour-pub-research--output-kinds))
             (t
              (push (list :kind kind :title title :url url :year year) results)))))
        (when results (nreverse results))))))
```

Wrap the function in `cl-defun` so `cl-return-from` works:

```elisp
(cl-defun a3madkour-pub-research--parse-outputs-table (ast file)
  "..."
  ;; body
  )
```

- [ ] **Step 4: Run; expect green.**

```bash
emacs --batch -L . -l a3madkour-publish-research -l a3madkour-publish-research-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: 7 new tests pass.

- [ ] **Step 5: Commit.**

```bash
git commit -m "feat(b-3): --parse-outputs-table helper

Case-insensitive * Outputs heading match; first table under it parsed
to plist list (:kind :title :url :year).  Required columns checked
literally; missing → WARN + nil.  Unknown kind → WARN + row skipped.
Year coerced via float-trip (octal-safe).  Row order preserved."
```

---

## Task 8: `--strip-outputs-subtree` helper

**Spec §6:** Remove the `* Outputs` subtree from the body buffer before ox-hugo runs. Pure buffer mutation operating on the source text, not the AST.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-research--strip-outputs-subtree-happy ()
  "Outputs heading + everything until next same-level heading or EOF is removed."
  (let* ((src "* Intro
Body before.

* Outputs                                                  :outputs:
| kind  | title  | url                  | year |
|-------+--------+----------------------+------|
| paper | Foo    | https://example.com  | 2024 |

* After
Body after.
")
         (result (a3madkour-pub-research--strip-outputs-subtree src)))
    (should (string-match-p "Body before" result))
    (should (string-match-p "Body after" result))
    (should-not (string-match-p "^\\* Outputs" result))
    (should-not (string-match-p "kind " result))))

(ert-deftest a3madkour-pub-research--strip-outputs-subtree-trailing ()
  "Outputs subtree at end-of-file: stripped to EOF."
  (let* ((src "* Intro
Body before.

* Outputs
| kind  | title | url                 | year |
|-------+-------+---------------------+------|
| paper | Foo   | https://example.com | 2024 |
")
         (result (a3madkour-pub-research--strip-outputs-subtree src)))
    (should (string-match-p "Body before" result))
    (should-not (string-match-p "^\\* Outputs" result))))

(ert-deftest a3madkour-pub-research--strip-outputs-subtree-no-outputs ()
  "No * Outputs heading → buffer unchanged."
  (let* ((src "* Intro\nBody.\n* Another\nMore.\n")
         (result (a3madkour-pub-research--strip-outputs-subtree src)))
    (should (string= src result))))

(ert-deftest a3madkour-pub-research--strip-outputs-subtree-case-insensitive ()
  "Lowercased * outputs heading also stripped."
  (let* ((src "* Intro\nBody.\n\n* outputs\n| k | t | u | y |\n|---+---+---+---|\n| paper | F | https://x | 2024 |\n")
         (result (a3madkour-pub-research--strip-outputs-subtree src)))
    (should-not (string-match-p "^\\* outputs" result))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.** Use `org-element` bounds rather than regex parsing (safer for nested subtrees):

```elisp
(defun a3madkour-pub-research--strip-outputs-subtree (org-text)
  "Return ORG-TEXT with any top-level * Outputs subtree removed.
Case-insensitive heading match.  No-op if no Outputs heading found.

Pure-functional: operates on a temp buffer, returns the new string."
  (with-temp-buffer
    (insert org-text)
    (org-mode)
    (let* ((ast (org-element-parse-buffer))
           (heading (a3madkour-pub-research--find-outputs-heading ast)))
      (if (not heading)
          org-text
        (let ((begin (org-element-property :begin heading))
              (end (org-element-property :end heading)))
          (delete-region begin end)
          (buffer-substring-no-properties (point-min) (point-max)))))))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Commit.**

```bash
git commit -m "feat(b-3): --strip-outputs-subtree helper

Removes top-level * Outputs subtree from org text before ox-hugo runs;
prevents the outputs table from rendering as visible body content
(the Hugo template paints the Outputs section from frontmatter).
No-op when no Outputs heading present."
```

---

## Task 9: `publish-research-file` end-to-end

**Spec §3 pipeline:** export → cascade-type branch → normalize → outputs-parse (questions) → outputs-strip (questions) → rewrite-buffer-links → asset-copy → write-bundle → record-publish.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-research-test.el`

- [ ] **Step 1: Grep existing patterns to mirror.** Look at how `publish-garden-file` is structured today — same pipeline minus the outputs handling.

```bash
grep -n "defun a3madkour-pub-garden/publish-garden-file" \
  ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden.el
```

Read the function. The research handler mirrors its shape with two changes: (a) two cascade types branch into different normalizer calls, (b) questions run outputs-parse + outputs-strip between export and link-rewrite.

- [ ] **Step 2: Write the failing end-to-end test.**

```elisp
(ert-deftest a3madkour-pub-research--publish-theme-end-to-end ()
  "publish-research-file emits a theme bundle with the right frontmatter."
  (let* ((notes-dir (make-temp-file "a3-pub-research-notes-" t))
         (site-dir  (make-temp-file "a3-pub-research-site-" t))
         (src (expand-file-name "research-themes-example.org" notes-dir)))
    (unwind-protect
        (progn
          (make-directory (expand-file-name "data" site-dir))
          (make-directory (expand-file-name "content/research/themes" site-dir) t)
          (with-temp-file (expand-file-name "data/url-history.yaml" site-dir)
            (insert "notes: []\n"))
          (with-temp-file src
            (insert ":PROPERTIES:\n"
                    ":ID: " "11111111-aaaa-bbbb-cccc-dddddddddddd\n"
                    ":LAST_MODIFIED: 2026-05-30\n"
                    ":END:\n"
                    "#+title: Example theme\n"
                    "#+HUGO_PUBLISH: t\n"
                    "#+HUGO_SECTION: research-themes\n"
                    "#+HUGO_BASE_DIR: " site-dir "/\n"
                    "#+HUGO_DESCRIPTION: A short description.\n"
                    "#+HUGO_CUSTOM_FRONT_MATTER: :status active\n"
                    "#+HUGO_CUSTOM_FRONT_MATTER: :weight 10\n"
                    "#+filetags: :research:test:\n"
                    "Body paragraph for the theme.\n"))
          (cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil)))
            (let ((a3madkour-pub/site-data-dir (expand-file-name "data/" site-dir)))
              (a3madkour-pub-research/publish-research-file src)))
          (let ((out (expand-file-name "content/research/themes/example-theme/index.md" site-dir)))
            (should (file-exists-p out))
            (with-temp-buffer
              (insert-file-contents out)
              (should (string-match-p "title: Example theme" (buffer-string)))
              (should (string-match-p "description: A short description" (buffer-string)))
              (should (string-match-p "status: active" (buffer-string)))
              (should (string-match-p "Body paragraph for the theme" (buffer-string))))))
      (delete-directory notes-dir t)
      (delete-directory site-dir t))))

(ert-deftest a3madkour-pub-research--publish-question-with-outputs-end-to-end ()
  "publish-research-file emits a question bundle with outputs list, body stripped."
  (let* ((notes-dir (make-temp-file "a3-pub-research-notes-" t))
         (site-dir  (make-temp-file "a3-pub-research-site-" t))
         (src (expand-file-name "research-questions-example.org" notes-dir)))
    (unwind-protect
        (progn
          (make-directory (expand-file-name "data" site-dir))
          (make-directory (expand-file-name "content/research/questions" site-dir) t)
          (with-temp-file (expand-file-name "data/url-history.yaml" site-dir)
            (insert "notes: []\n"))
          (with-temp-file src
            (insert ":PROPERTIES:\n"
                    ":ID: 22222222-aaaa-bbbb-cccc-dddddddddddd\n"
                    ":LAST_MODIFIED: 2026-05-30\n"
                    ":END:\n"
                    "#+title: Example question\n"
                    "#+HUGO_PUBLISH: t\n"
                    "#+HUGO_SECTION: research-questions\n"
                    "#+HUGO_BASE_DIR: " site-dir "/\n"
                    "#+HUGO_DESCRIPTION: An active question.\n"
                    "#+HUGO_CUSTOM_FRONT_MATTER: :theme procedural-narrative\n"
                    "#+HUGO_CUSTOM_FRONT_MATTER: :status active\n"
                    "* Intro\n"
                    "Body paragraph for the question.\n\n"
                    "* Outputs\n"
                    "| kind  | title  | url                  | year |\n"
                    "|-------+--------+----------------------+------|\n"
                    "| paper | Test   | https://example.com  | 2024 |\n"))
          (cl-letf (((symbol-function 'org-roam-db-sync) (lambda () nil)))
            (let ((a3madkour-pub/site-data-dir (expand-file-name "data/" site-dir)))
              (a3madkour-pub-research/publish-research-file src)))
          (let ((out (expand-file-name "content/research/questions/example-question/index.md" site-dir)))
            (should (file-exists-p out))
            (with-temp-buffer
              (insert-file-contents out)
              (let ((body (buffer-string)))
                (should (string-match-p "title: Example question" body))
                (should (string-match-p "outputs:" body))
                (should (string-match-p "kind: paper" body))
                (should (string-match-p "url: https://example.com" body))
                (should (string-match-p "year: 2024" body))
                (should (string-match-p "Body paragraph for the question" body))
                ;; Outputs heading + table stripped from body.
                (should-not (string-match-p "^## Outputs" body))
                (should-not (string-match-p "| kind " body))))))
      (delete-directory notes-dir t)
      (delete-directory site-dir t))))
```

- [ ] **Step 3: Run; expect failure** (`publish-research-file` is still a stub).

- [ ] **Step 4: Implement the end-to-end function.** Replace the stub `publish-research-file` in `a3madkour-publish-research.el`:

```elisp
(defun a3madkour-pub-research--cascade-type (file)
  "Read the cascade type ('research-themes or 'research-questions) from FILE."
  (with-temp-buffer
    (insert-file-contents file)
    (org-mode)
    (goto-char (point-min))
    (cond
     ((re-search-forward "^#\\+HUGO_SECTION:[ \t]+research-themes[ \t]*$" nil t)
      'research-themes)
     ((re-search-forward "^#\\+HUGO_SECTION:[ \t]+research-questions[ \t]*$" nil t)
      'research-questions)
     (t (error "a3madkour-pub-research: %s has no research-themes/research-questions section"
               file)))))

(defun a3madkour-pub-research--dest-bundle-dir (cascade-type slug site-content-dir)
  "Compute the destination bundle dir for CASCADE-TYPE + SLUG under SITE-CONTENT-DIR."
  (let ((subdir (cond
                 ((eq cascade-type 'research-themes) "research/themes")
                 ((eq cascade-type 'research-questions) "research/questions")
                 (t (error "unknown cascade-type %S" cascade-type)))))
    (expand-file-name (concat subdir "/" slug "/") site-content-dir)))

(defun a3madkour-pub-research/publish-research-file (file)
  "Publish a single research FILE to content/research/<type>/<slug>/index.md.

Two cascade types share one pipeline:
  - research-themes  → content/research/themes/<slug>/index.md
  - research-questions → content/research/questions/<slug>/index.md

Internal branch on #+HUGO_SECTION: selects per-type frontmatter
normalizer; the outputs-table parse + body-strip runs only for questions.
Everything else (export, link-rewrite, asset-copy, write, record-publish)
is shared."
  (let* ((cascade-type (a3madkour-pub-research--cascade-type file))
         (site-data-dir (or (and (boundp 'a3madkour-pub/site-data-dir)
                                 a3madkour-pub/site-data-dir)
                            (error "a3madkour-pub/site-data-dir is nil")))
         (site-content-dir (expand-file-name
                            "../content/"
                            (directory-file-name site-data-dir)))
         ;; If the file has an outputs subtree, parse it BEFORE export
         ;; (so we still have the table) and strip it from the source
         ;; copy ox-hugo sees.
         (source-text (with-temp-buffer
                        (insert-file-contents file)
                        (buffer-string)))
         (ast (with-temp-buffer
                (insert source-text)
                (org-mode)
                (org-element-parse-buffer)))
         (outputs (when (eq cascade-type 'research-questions)
                    (a3madkour-pub-research--parse-outputs-table ast file)))
         (stripped-text (if (eq cascade-type 'research-questions)
                            (a3madkour-pub-research--strip-outputs-subtree source-text)
                          source-text))
         ;; Write stripped-text to a tmp file so ox-hugo exports the clean version.
         (tmp-source (make-temp-file "a3-pub-research-stripped-" nil ".org")))
    (unwind-protect
        (progn
          (with-temp-file tmp-source (insert stripped-text))
          ;; Apply the pre-export link rewriter to the tmp source.
          (a3madkour-pub-rewrite/rewrite-buffer-links tmp-source file)
          (let* ((exported (a3madkour-pub-export/export-file tmp-source))
                 (raw-fm (plist-get exported :frontmatter))
                 (body (plist-get exported :body))
                 (normalized (a3madkour-pub-frontmatter/normalize
                              cascade-type raw-fm file))
                 ;; Inject outputs into the final frontmatter (questions only).
                 (final-fm (if outputs
                               (cons (cons 'outputs outputs) normalized)
                             normalized))
                 (slug (or (alist-get 'slug final-fm)
                           (a3madkour-pub-export/title-to-slug
                            (alist-get 'title final-fm))))
                 (bundle-dir (a3madkour-pub-research--dest-bundle-dir
                              cascade-type slug site-content-dir))
                 (index-path (expand-file-name "index.md" bundle-dir)))
            ;; Asset copy (A.1.c).
            (a3madkour-pub-assets/asset-validate-and-copy file bundle-dir)
            ;; Render + write-if-different.
            (let ((rendered (a3madkour-pub-export/render-bundle final-fm body)))
              (make-directory bundle-dir t)
              (let ((existing (when (file-exists-p index-path)
                                (with-temp-buffer
                                  (insert-file-contents index-path)
                                  (buffer-string)))))
                (unless (string= existing rendered)
                  (with-temp-file index-path (insert rendered)))))
            ;; record-publish.
            (let ((file-id (a3madkour-pub/note-id file))
                  (new-url (concat "/research/"
                                   (if (eq cascade-type 'research-themes) "themes" "questions")
                                   "/" slug "/")))
              (a3madkour-pub-history/record-publish
               file-id new-url 'live
               :had-slug-override-p (not (null (alist-get 'slug raw-fm)))))))
      (delete-file tmp-source))))
```

> **Important caveats for the implementer:**
> 1. The exact API of `a3madkour-pub-export/export-file`, `a3madkour-pub-export/render-bundle`, `a3madkour-pub-rewrite/rewrite-buffer-links`, `a3madkour-pub-assets/asset-validate-and-copy`, `a3madkour-pub-history/record-publish` may differ in signature. **Grep each before using and adjust call shapes to match the existing garden handler.** Pattern-match how `publish-garden-file` invokes each.
> 2. If `a3madkour-pub-export/title-to-slug` doesn't exist (it's in `a3madkour-publish-library`), reuse via `(require 'a3madkour-publish-library)` and call `a3madkour-pub-library--title-to-slug` — or extract it into a shared module. The function is identical for both.
> 3. The "write tmp source, rewrite-buffer-links on it" sequence assumes `rewrite-buffer-links` operates on a file path. If it operates on a buffer or string, adjust the call accordingly.

- [ ] **Step 5: Run the end-to-end tests; expect green (after iteration on API mismatches).**

```bash
emacs --batch -L . -l a3madkour-publish-research -l a3madkour-publish-research-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -10
```

- [ ] **Step 6: Run full ert suite.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

- [ ] **Step 7: Commit.**

```bash
git commit -m "feat(b-3): publish-research-file end-to-end

Two cascade types share one pipeline; internal branch on #+HUGO_SECTION:
selects per-type normalizer + question-only outputs parse/strip.  Export
through tmp source so ox-hugo sees the stripped body; record-publish
emits the correct /research/<themes|questions>/<slug>/ URL."
```

---

## Task 10: Register both research handlers in `a3madkour-pub-living--handlers`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el`

- [ ] **Step 1: Grep the existing library registration shape.**

```bash
grep -n -A 5 "with-eval-after-load 'a3madkour-publish-library" \
  ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el
```

Expected: the library `with-eval-after-load` block that adds 4 entries to `a3madkour-pub-living--handlers`. Mirror its shape for research.

- [ ] **Step 2: Write failing test.**

```elisp
(ert-deftest a3madkour-pub-living--research-handlers-registered ()
  "Both research cascade types register publish-research-file."
  (require 'a3madkour-publish-research)
  (dolist (section '(research-themes research-questions))
    (should (eq (cdr (assq section a3madkour-pub-living--handlers))
                'a3madkour-pub-research/publish-research-file))))
```

- [ ] **Step 3: Run; expect failure.**

- [ ] **Step 4: Register via `with-eval-after-load` block.** Append to `a3madkour-publish-living.el`:

```elisp
;; B.3: research handler registration (one entry per cascade type).
(with-eval-after-load 'a3madkour-publish-research
  (dolist (section '(research-themes research-questions))
    (add-to-list 'a3madkour-pub-living--handlers
                 (cons section 'a3madkour-pub-research/publish-research-file))))
```

> **If the dispatch alist is string-keyed** (per [[b2-complete]] architectural decision 1), use string keys instead: `"research/themes"` and `"research/questions"`. Grep the library registration in Step 1 to confirm the exact form.

- [ ] **Step 5: Run; expect green.**

- [ ] **Step 6: Full ert + wrapper smoke.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3

cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
```

Expected: ~340 ert tests pass; wrapper exits 0 (no research `.org` files in `~/org/notes/` yet).

- [ ] **Step 7: Commit.**

```bash
git commit -m "feat(b-3): register research handlers in living--handlers

with-eval-after-load form adds one entry per cascade type
(research-themes + research-questions), both pointing at
publish-research-file (per spec §3 dispatch model)."
```

---

## Task 11: Python integration fixture — `_write_research_source` helper + `test_research_theme_publish_once`

**Why:** Mirror B.2's `TestLibraryPublishLiving` pattern; first of 6 new B.3 fixtures.

**Files:**
- Modify: `tools/test_publish_integration.py` (site repo).

- [ ] **Step 1: Add `_write_research_source` helper near `_write_library_source`.**

```python
def _write_research_source(
    path: Path,
    cascade_type: str,
    title: str,
    fm: dict[str, str],
    site_dir: Path,
    body: str = "Body paragraph for integration test.\n",
    outputs: list[dict[str, str]] | None = None,
) -> None:
    """Write a research .org file at PATH.

    cascade_type is 'research-themes' or 'research-questions'.
    fm is a dict of additional HUGO_CUSTOM_FRONT_MATTER fields
    (status, weight, theme, etc.).  outputs (questions only) renders
    an org table under * Outputs.
    """
    lines = [
        ":PROPERTIES:",
        f":ID: {fm.get('id', '11111111-2222-3333-4444-555555555555')}",
        f":LAST_MODIFIED: {fm.get('last_modified', '2026-05-30')}",
        ":END:",
        f"#+title: {title}",
        "#+HUGO_PUBLISH: t",
        f"#+HUGO_SECTION: {cascade_type}",
        f"#+HUGO_BASE_DIR: {site_dir}/",
        f"#+HUGO_DESCRIPTION: {fm.get('description', 'Test description.')}",
    ]
    for key in ("status", "weight", "theme", "parent_question",
                "garden_topic_ref", "supporting_notes", "related_essays",
                "source_stream", "started", "summary"):
        if key in fm:
            lines.append(f"#+HUGO_CUSTOM_FRONT_MATTER: :{key} {fm[key]}")
    if "tags" in fm:
        lines.append(f"#+filetags: :{':'.join(fm['tags'])}:")
    lines.append("")
    lines.append(body)
    if outputs:
        lines.append("")
        lines.append("* Outputs")
        lines.append("| kind  | title  | url  | year |")
        lines.append("|-------+--------+------+------|")
        for o in outputs:
            lines.append(f"| {o['kind']:<5s} | {o['title']} | {o['url']} | {o['year']} |")
    path.write_text("\n".join(lines), encoding="utf-8")
```

- [ ] **Step 2: Add `TestResearchPublishLiving` class with the first fixture.**

Place it right after `TestLibraryPublishLiving`:

```python
@unittest.skipIf(_MISSING_PREREQS, _SKIP_REASON)
class TestResearchPublishLiving(unittest.TestCase):
    """B.3 integration fixtures: pin research publish-living behavior.

    Each test seeds one or more research-{themes,questions}-<slug>.org
    source files in a tmp notes dir, runs publish-living against a tmp
    site dir, asserts on the resulting content/research/{themes,
    questions}/ bundles.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="b3-research-"))
        self.notes_dir = self.tmp / "notes"
        self.site_root = self.tmp / "site"
        self.notes_dir.mkdir(parents=True)
        (self.site_root / "data").mkdir(parents=True)
        (self.site_root / "content" / "research" / "themes").mkdir(parents=True)
        (self.site_root / "content" / "research" / "questions").mkdir(parents=True)
        (self.site_root / "data" / "url-history.yaml").write_text(
            "notes: []\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    @property
    def _site_data_dir(self) -> Path:
        return self.site_root / "data"

    def test_research_theme_publish_once(self) -> None:
        """Single theme emits a clean bundle under content/research/themes/."""
        src = self.notes_dir / "research-themes-example-theme.org"
        _write_research_source(
            src, "research-themes", "Example theme",
            {
                "status": "active",
                "weight": "10",
                "garden_topic_ref": "memory-in-play",
                "summary": "An umbrella theme.",
                "tags": ["research", "memory"],
            },
            self.site_root,
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc.returncode, 0,
            msg=f"publish-living exited non-zero.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )
        out = self.site_root / "content" / "research" / "themes" / "example-theme" / "index.md"
        self.assertTrue(out.exists(),
                        f"bundle not created.\nstderr:\n{proc.stderr}")
        content = out.read_text(encoding="utf-8")
        self.assertIn("title: Example theme", content)
        self.assertIn("status: active", content)
        self.assertIn("description:", content)
        self.assertIn("weight: 10", content)
```

- [ ] **Step 3: Run.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
python3 -m unittest tools.test_publish_integration.TestResearchPublishLiving.test_research_theme_publish_once -v
```

Expected: pass.

- [ ] **Step 4: Commit.**

```bash
git add tools/test_publish_integration.py
git commit -m "test(b-3): integration fixture — research theme publish-once

Seed 1 theme, assert content/research/themes/<slug>/index.md emitted
with required frontmatter fields."
```

---

## Task 12: Python integration fixture — `test_research_question_publish_once` (with outputs table)

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add the fixture inside `TestResearchPublishLiving`.**

```python
    def test_research_question_publish_once(self) -> None:
        """Single question with outputs table emits clean bundle."""
        src = self.notes_dir / "research-questions-narrative-atom.org"
        _write_research_source(
            src, "research-questions", "What is a narrative atom?",
            {
                "id": "22222222-aaaa-bbbb-cccc-dddddddddddd",
                "theme": "procedural-narrative",
                "status": "active",
                "supporting_notes": "story-atoms",
                "related_essays": "example-essay-two",
                "weight": "20",
                "tags": ["narrative"],
            },
            self.site_root,
            outputs=[
                {"kind": "paper", "title": "Save States as Edits",
                 "url": "https://example.com/paper", "year": 2024},
                {"kind": "code", "title": "save-replay-tool",
                 "url": "https://github.com/example/x", "year": 2024},
            ],
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc.returncode, 0,
            msg=f"publish-living exited non-zero.\nstderr:\n{proc.stderr}",
        )
        out = (self.site_root / "content" / "research" / "questions"
               / "what-is-a-narrative-atom" / "index.md")
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("title: What is a narrative atom?", content)
        self.assertIn("theme: procedural-narrative", content)
        self.assertIn("supporting_notes:", content)
        self.assertIn("story-atoms", content)
        self.assertIn("outputs:", content)
        self.assertIn("kind: paper", content)
        self.assertIn("year: 2024", content)
        # Outputs heading + table stripped from body.
        self.assertNotIn("## Outputs", content)
        self.assertNotIn("| kind", content)
```

- [ ] **Step 2: Run; iterate if outputs serialization is YAML-formatted differently than the test expects** (e.g. `outputs:\n  - kind: paper` instead of inline).

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-3): integration fixture — research question publish-once

Seed 1 question with outputs table, assert bundle emitted with outputs
list in frontmatter and Outputs heading stripped from body."
```

---

## Task 13: Python integration fixture — `test_research_publish_idempotent`

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add the fixture.**

```python
    def test_research_publish_idempotent(self) -> None:
        """Second publish-living run on unchanged source → zero file diff."""
        src = self.notes_dir / "research-themes-idem.org"
        _write_research_source(
            src, "research-themes", "Idempotent theme",
            {"status": "active", "weight": "15",
             "id": "33333333-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr)
        out = (self.site_root / "content" / "research" / "themes"
               / "idempotent-theme" / "index.md")
        self.assertTrue(out.exists())
        content1 = out.read_bytes()
        mtime1 = out.stat().st_mtime_ns
        time.sleep(1.1)
        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        content2 = out.read_bytes()
        mtime2 = out.stat().st_mtime_ns
        self.assertEqual(content1, content2)
        self.assertEqual(mtime1, mtime2,
                         msg="index.md was rewritten on idempotent run")
```

> **Note:** `time` is already imported at top of `test_publish_integration.py` (Task 13 of B.2). If not, add `import time`.

- [ ] **Step 2: Run.**

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-3): integration fixture — research publish idempotent

Second run on unchanged source produces zero content + zero mtime diff."
```

---

## Task 14: Python integration fixture — `test_research_question_slug_shift`

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add the fixture.**

```python
    def test_research_question_slug_shift(self) -> None:
        """Title change → old bundle removed, new bundle at new slug."""
        src = self.notes_dir / "research-questions-shifting.org"
        _write_research_source(
            src, "research-questions", "Original question",
            {"theme": "memory-and-play", "status": "active",
             "id": "44444444-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr)
        original = (self.site_root / "content" / "research" / "questions"
                    / "original-question")
        self.assertTrue(original.exists())
        # Mutate title.
        _write_research_source(
            src, "research-questions", "New question",
            {"theme": "memory-and-play", "status": "active",
             "id": "44444444-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        new_bundle = (self.site_root / "content" / "research" / "questions"
                      / "new-question")
        self.assertTrue(new_bundle.exists(), "new-slug bundle missing")
        self.assertFalse(original.exists(),
                         "original-slug bundle should be removed")
        history = (self._site_data_dir / "url-history.yaml").read_text()
        self.assertIn("original-question", history)
        self.assertIn("new-question", history)
```

> **Caveat:** if [[b1-complete]] open follow-up #5 (delete-bundle no-retry) bites here, the test will fail with the original bundle still present. That's an A.2 / B.x issue, not a B.3 implementation bug. If the test fails on the orphan, log it as a B.3 finding for follow-up — don't try to fix `finish-publish` in this slice.

- [ ] **Step 2: Run; iterate.**

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-3): integration fixture — research question slug shift

Old slug bundle removed, new bundle at new slug, alias recorded in
url-history.yaml."
```

---

## Task 15: Python integration fixture — `test_research_cross_ref_warn`

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add the fixture.**

```python
    def test_research_cross_ref_warn(self) -> None:
        """Broken cross-refs WARN but don't fail; emitted YAML still passes the
        fixtures linter (the links linter is a separate gate)."""
        src = self.notes_dir / "research-questions-broken-refs.org"
        _write_research_source(
            src, "research-questions", "Broken refs question",
            {"theme": "nonexistent-theme",
             "status": "active",
             "supporting_notes": "private-note",
             "id": "55555555-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = (self.site_root / "content" / "research" / "questions"
               / "broken-refs-question" / "index.md")
        self.assertTrue(out.exists())
        # Frontmatter emits the broken refs verbatim (linker is the hard gate).
        content = out.read_text()
        self.assertIn("theme: nonexistent-theme", content)
        self.assertIn("private-note", content)
        # No assertion on stderr WARN strings (link rewrite stays out of
        # frontmatter cross-refs in B.3; cross-ref validation is a runtime
        # link rewriter concern only for body refs).
```

> **Note:** the spec calls for WARN on broken refs, but the v0 cross-ref WARN may not land in B.3 (it requires plumbing `published-p` into `--normalize-research-question`). If the cross-ref WARN logic isn't implemented yet, simplify this test to just assert publish succeeds with broken refs in frontmatter — the linter (`check_research_links.py`) catches them downstream. Worth flagging as a B.3.x follow-up if WARN-side checking is deferred.

- [ ] **Step 2: Run.**

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-3): integration fixture — research cross-ref WARN tolerance

Broken theme + supporting_notes refs emit successfully; site link
linter is the hard gate downstream."
```

---

## Task 16: Python integration fixture — `test_research_publish_removed_unpublish` + linter parity

**Why:** Per spec §11 / parent §11, B-emitted bundles must pass the existing site linters. This fixture is the CI gate guarantee + the removed-note unpublish behavior.

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add the fixture.**

```python
    def test_research_removed_question_unpublish(self) -> None:
        """Deleting a question source → bundle removed on next publish-living."""
        src = self.notes_dir / "research-questions-vanishing.org"
        _write_research_source(
            src, "research-questions", "Vanishing question",
            {"theme": "memory-and-play", "status": "active",
             "id": "66666666-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr)
        bundle = (self.site_root / "content" / "research" / "questions"
                  / "vanishing-question")
        self.assertTrue(bundle.exists())
        # Remove source file.
        src.unlink()
        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        self.assertFalse(bundle.exists(),
                         "removed source → bundle should be unpublished")

    def test_research_yaml_passes_site_linters(self) -> None:
        """B-emitted research bundles pass check_research_fixtures + _links.

        Both linters today have main()-only signatures (no run(root)).  Stand
        up a minimal tmp site dir layout matching what their `Path(__file__)`-
        based resolution expects, chdir, and import + call main().
        """
        # Seed: 1 theme + 1 question pointing at that theme.
        _write_research_source(
            self.notes_dir / "research-themes-mp.org",
            "research-themes", "Memory and play",
            {"status": "active", "weight": "10",
             "id": "77777777-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        _write_research_source(
            self.notes_dir / "research-questions-narrative.org",
            "research-questions", "What is a narrative atom?",
            {"theme": "memory-and-play", "status": "active", "weight": "20",
             "id": "88888888-aaaa-bbbb-cccc-dddddddddddd"},
            self.site_root,
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)

        # The linters resolve repo_root from __file__; we copy their logic
        # by importing them and calling main() with cwd set to site_root.
        prev_cwd = os.getcwd()
        try:
            os.chdir(self.site_root)
            mod_fixtures = _import_linter("check_research_fixtures")
            mod_links = _import_linter("check_research_links")
            # Patch Path(__file__).resolve().parent.parent → self.site_root.
            import unittest.mock as mock
            with mock.patch.object(
                mod_fixtures, "Path",
                wraps=lambda *a, **kw: __import__("pathlib").Path(*a, **kw),
            ):
                # Each linter walks from repo_root.  Since their resolution
                # is hardcoded to their __file__ position (.../tools/x.py →
                # repo_root = parent.parent = a3madkour.github.io), chdir
                # doesn't help.  Solution: invoke via subprocess so each
                # linter resolves relative to ITS file path, and pass a
                # tmp tools/ link OR copy the linter to site_root/tools/.
                pass
            # Pragmatic fallback: run the linter as a subprocess against
            # the tmp site by symlinking tools/ into self.site_root.
            (self.site_root / "tools").symlink_to(
                Path(__file__).resolve().parent
            )
            for linter in ("check_research_fixtures", "check_research_links"):
                result = subprocess.run(
                    ["python3", f"tools/{linter}.py"],
                    cwd=self.site_root,
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(
                    result.returncode, 0,
                    msg=f"{linter}.py failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
                )
        finally:
            os.chdir(prev_cwd)
```

> **Implementer note:** the linter-parity fixture is fragile because both `check_research_fixtures.py` and `check_research_links.py` resolve `repo_root` from `Path(__file__).resolve().parent.parent`. The symlink workaround above mirrors how B.2's parity fixture handles the same issue for library linters. If the symlink approach causes issues (Windows or stricter sandbox), the fallback is to add a `run(root: Path) -> int` entry point to both linters first — that's a small site-side refactor worth doing as part of this task if symlink doesn't work.
>
> **Alternative implementation:** if running the linters as subprocesses is too brittle, copy `data/url-history.yaml` + the minimal needed garden/essays fixture into the tmp site root so the linkers find their cross-link targets — but this expands the fixture significantly. The symlink approach is the pragmatic minimum.

- [ ] **Step 2: Run; iterate on the linter-invocation shape.**

```bash
python3 -m unittest tools.test_publish_integration.TestResearchPublishLiving -v 2>&1 | tail -20
```

Expected: all 6 fixtures pass.

- [ ] **Step 3: Full integration suite to confirm no regression.**

```bash
python3 -m unittest tools.test_publish_integration -v 2>&1 | tail -5
```

Expected: 25 tests pass (19 baseline + 6 new B.3 fixtures).

- [ ] **Step 4: Commit.**

```bash
git commit -m "test(b-3): integration fixtures — research removed-unpublish + linter parity

Removing source file → bundle unpublished on next publish-living.
B-emitted bundles pass check_research_fixtures + check_research_links."
```

---

## Task 17: Stub spot-check + fixture handover + memory + spec amendment + push

**Why:** Per spec §10 stub spot-check + [[verify-before-merge]] feedback, this slice closes with a real publish-living against ~6 hand-written `~/org/notes/research-{themes,questions}-*.org` files, replacing the 9 existing research fixtures with stub B-emitted bundles. Same pattern B.2 followed.

**Files:**
- Create: `~/org/notes/research-themes-example-one.org` (and 1 more theme).
- Create: `~/org/notes/research-questions-example-{one,two,three,four}.org`.
- `content/research/themes/*/` and `content/research/questions/*/` — 9 existing bundles replaced by ~6 B-emitted bundles.
- `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` — one-line `research-theme` → `research-themes` amendment + `source_stream` / `#+HUGO_DESCRIPTION:` notes.
- `CLAUDE.md` (status pointer update).
- `.claude/memory/MEMORY.md` + `.claude/memory/project_b3_complete.md` (new) + `.claude/memory/project_next_slice.md` (update to B.4).

- [ ] **Step 1: Run the full ert suite locally.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: `Ran ~340 tests, ~340 results as expected, 0 unexpected.` (309 baseline + ~30 new across Tasks 1–10.)

- [ ] **Step 2: Run `tools/ci-local.sh`** against the site repo (per [[always-run-ci-locally]]) to establish a green baseline.

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
tools/ci-local.sh
```

Expected: all linters pass; hugo --minify succeeds.

- [ ] **Step 3: Hand-write ~6 stub research source files in `~/org/notes/`.** Use obviously-dummy content per [[filler-text-only]]. The file shapes should exercise the full frontmatter contract — at least one question with an outputs table, one with parent_question, one with cross-refs.

Shape per stub:

```org
:PROPERTIES:
:ID: <distinct-uuid>
:LAST_MODIFIED: 2026-05-30
:END:
#+title: Example theme one
#+HUGO_PUBLISH: t
#+HUGO_SECTION: research-themes
#+HUGO_DESCRIPTION: Example 1. Lorem ipsum theme description.
#+HUGO_CUSTOM_FRONT_MATTER: :status active
#+HUGO_CUSTOM_FRONT_MATTER: :weight 10
#+filetags: :research:example:

Example 1. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

(Repeat with shape variants. For a question with outputs:)

```org
:PROPERTIES:
:ID: <distinct-uuid>
:LAST_MODIFIED: 2026-05-30
:END:
#+title: Example question with outputs
#+HUGO_PUBLISH: t
#+HUGO_SECTION: research-questions
#+HUGO_DESCRIPTION: Example question that has outputs and supporting notes.
#+HUGO_CUSTOM_FRONT_MATTER: :theme example-theme-one
#+HUGO_CUSTOM_FRONT_MATTER: :status active
#+HUGO_CUSTOM_FRONT_MATTER: :supporting_notes bayesian-statistics
#+HUGO_CUSTOM_FRONT_MATTER: :weight 10
#+filetags: :research:example:

Example. Lorem ipsum dolor sit amet, consectetur adipiscing elit.

* Outputs                                                  :outputs:
| kind  | title                | url                          | year |
|-------+----------------------+------------------------------+------|
| paper | Example Paper Title  | https://example.com/paper    | 2024 |
| code  | example-tool         | https://github.com/example/x | 2024 |
```

> **Recommended set for shape coverage:**
> 1. `research-themes-example-one.org` — active, with `garden_topic_ref` pointing at one of the existing 4 B-emitted garden notes (e.g. `bayesian-statistics`).
> 2. `research-themes-example-two.org` — dormant, summary + description distinct.
> 3. `research-questions-example-one.org` — active, supporting_notes + related_essays + outputs table.
> 4. `research-questions-example-two.org` — dormant, supporting_notes only, no outputs.
> 5. `research-questions-example-three.org` — answered, parent_question pointing at example-one, full outputs table.
> 6. `research-questions-example-four.org` — sub-question chaining parent_question to example-three.

- [ ] **Step 4: Run the real publish.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
```

Expected: exit 0. The publisher emits 6 bundles under `content/research/themes/` + `content/research/questions/`. The 9 existing fixture bundles are NOT auto-removed (B's orphan sweep is manifest-based; fixtures aren't in the manifest — per [[publish-living-manifest-sweep]]). The implementer must hand-remove the 9 fixtures after verifying the 6 emitted ones look correct.

- [ ] **Step 5: Inspect 2-3 emitted bundles by hand.** Check that:
- Frontmatter key ordering is deterministic.
- `outputs:` is rendered as a YAML list-of-dicts (not stringified or out-of-order).
- The `* Outputs` heading + table is gone from the body markdown.
- `description:` is present.
- `last_modified` matches the source.

- [ ] **Step 6: Remove the 9 existing fixture bundles.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
# Keep _index.md but remove all per-item dirs.
find content/research/themes -mindepth 1 -maxdepth 1 -type d \
  -not -name '_*' \
  $(printf -- '-not -name %s ' example-theme-one example-theme-two) \
  -exec rm -rf {} +
find content/research/questions -mindepth 1 -maxdepth 1 -type d \
  -not -name '_*' \
  $(printf -- '-not -name %s ' example-question-one example-question-two example-question-three example-question-four) \
  -exec rm -rf {} +
```

> **Adjust the bundle names** to match what your stubs produce (slug-from-title; the names above assume titles like "Example theme one" → `example-theme-one`).

- [ ] **Step 7: Re-run `tools/ci-local.sh`** against the new B-emitted bundles.

```bash
tools/ci-local.sh
```

Expected: all 50+ pre-build linters pass; `check_research_fixtures.py` + `check_research_links.py` both green.

> **If anything fails:** file a focused fix as a B.3.x follow-up if non-blocking; fix in-slice if it blocks publish. Common failure modes:
> - `weight` collisions across themes (linter `validate_unique_theme_weights`). Renumber stubs.
> - Cross-link to a slug that doesn't exist (`supporting_notes` pointing at an unannotated garden note). Either use a B-emitted garden slug, or drop the ref.
> - `parent_question` pointing at a slug that doesn't match the emitted question slug. Verify slug derivation from the test title.

- [ ] **Step 8: Author starts `hugo server --buildDrafts`, visits `/research/`, `/research/themes/`, `/research/questions/`, each per-item page.** Verifies:
- Theme cards render with status/weight/garden_topic_ref.
- Question pages show theme + parent_question + supporting_notes + related_essays.
- Outputs section renders on questions with outputs.
- Cross-links resolve where the target exists (garden topic ref clickable).

- [ ] **Step 9: Update `CLAUDE.md` status pointer.**

Locate the "Project status (as of YYYY-MM-DD)" line and the B sub-project bullet. Update to mark B.3 shipped:

```
... **B.2 (library handler) shipped 2026-05-29/30**; B.3 (research handler) shipped 2026-05-30 — closes per-page-bundle publisher for both research cascade types (themes + questions sharing one handler) + adds last_modified fs-mtime cascade (retroactively closes B.1.x #10). Next: B.4 (essays). See memory/project_b3_complete.md.
```

- [ ] **Step 10: Amend the parent B spec.** Two small edits in `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md`:

- §3 research row: `research-theme` → `research-themes`; `research-question` → `research-questions`.
- §7 common-across-all-sections table: add `source_stream` row mapped from `#+HUGO_SOURCE_STREAM:` keyword.
- §7 research themes / questions subsections: add note that `description:` comes from `#+HUGO_DESCRIPTION:` keyword (new in B.3).
- §9 research subsection: add reference to the `* Outputs` org table parsing contract (point at B.3 spec §6).

- [ ] **Step 11: Commit the site changes.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add content/research/ \
        docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md \
        CLAUDE.md
git commit -m "feat(b-3): research handler ships — stub fixture handover

Replaces 9 hand-authored research fixtures with ~6 B-emitted stub
bundles from ~/org/notes/research-{themes,questions}-example-*.org.
Third per-content-type publisher to ship (after B.1 garden + B.2 library).

Closes:
- B.1 follow-up #10 (fs-mtime fallback completes the last_modified cascade)
- Parent B spec §3 wording mismatch (singular keyword vs plural dir)
- Parent B spec §7 source_stream + #+HUGO_DESCRIPTION: gaps

Real-content authoring deferred to B.3.x (per spec §2 + §11)."
```

- [ ] **Step 12: Update memory.**

Create `.claude/memory/project_b3_complete.md` summarizing what shipped, what tests landed, dotfiles + site commit SHAs, known issues / B.4 follow-ups. Add the index line to `.claude/memory/MEMORY.md`. Update `.claude/memory/project_next_slice.md` to point at B.4 (essays).

```bash
git add .claude/memory/
git commit -m "docs(memory): B.3 research handler shipped — next slice B.4"
```

- [ ] **Step 13: Push.**

```bash
git push origin master
```

Confirm with author before pushing. Author may want to batch with the accumulated unpushed dotfiles commits.

```bash
cd ~/dotfiles
git push origin main
```

---

## Self-Review

**Spec coverage check (against `docs/superpowers/specs/2026-05-30-phase-3-b-3-research-handler-design.md`):**

- §1 Goals: covered by the full task set (handler + stub spot-check pipeline).
- §2 Non-goals (real-content, dotfiles ergonomics, weight uniqueness, cross-link hard-fail, section-index regen, About Now widget): preserved — none touched.
- §3 Architecture (one module, one entry fn, internal branch, two dispatch entries): covered by Tasks 3 + 9 + 10.
- §4 Source layout (flat with prefix, `research-themes` / `research-questions` keywords): covered by Tasks 3 + 5 + 6 + 11+ (test fixtures use this exact form).
- §5 Frontmatter mapping common fields: covered by Tasks 1 (last_modified cascade) + 2 (description) + 4 (research-normalize-common).
- §5 Theme-only fields: covered by Task 5.
- §5 Question-only fields: covered by Task 6.
- §6 Outputs-table parse: covered by Task 7 (parse) + Task 8 (strip) + Task 9 (integration into pipeline).
- §7 Cross-link emission + WARN discipline: partial — the WARN-on-broken-ref logic is described in spec but Task 6 only emits verbatim (linter is the hard gate). If WARN-on-broken-ref is needed at publish time, add a small extension to Task 6 (or file as a B.3.x follow-up — flagged in Task 15's note).
- §8 last_modified cascade: covered by Task 1.
- §9 Slice scope (tasks, tests): covered (16 tasks).
- §10 Stub spot-check: covered by Task 17.
- §11 Carry-forwards + follow-ups: documented in spec; Task 17 handles parent-spec amendments; new follow-ups (#13/#14) get filed into memory in Task 17 Step 12.
- §12 Glossary: spec-only; no plan tasks needed.

**Placeholder scan:** Checked every step for "TBD", "appropriate error handling", "similar to Task N", or undefined symbols. Notes:
1. Task 1 Step 9 says "the exact key (`'lastmod` vs `'last_modified`) depends on what ox-hugo emits" — honest signature-checking advice, agent must grep. Same approach used in B.2 plan.
2. Task 9 Step 4 has a paragraph of caveats about API mismatches (export-file, render-bundle, etc.) — this is real grep-before-write guidance, not a placeholder. Cannot hardcode call shapes without first reading the existing garden handler.
3. Task 15 explicitly flags that cross-ref WARN-on-broken may not land in B.3 — that's a design honesty marker (the spec calls for it but the v0 simple impl in Task 6 omits it); the agent has a decision point flagged with the right context.
4. Task 16 has a documented fragility around the linter-parity invocation (Path(__file__) hardcoding). Same issue B.2 Task 16 faced; same symlink workaround.

**Type consistency:**
- `a3madkour-pub-research/publish-research-file` consistent across Tasks 3 / 9 / 10 / 11+ / 17.
- `--parse-outputs-table` signature `(ast file)` consistent in Tasks 7 / 9.
- `--strip-outputs-subtree` signature `(org-text)` consistent in Tasks 8 / 9.
- Per-section normalize keys `'research-themes` + `'research-questions` consistent across Tasks 5 / 6 / 9 / 10.
- Cascade-type symbols (`'research-themes`, `'research-questions`) used uniformly as both source-side `#+HUGO_SECTION:` values AND dispatch keys; if the existing dispatch alist is string-keyed (per B.2 architectural decision 1), Task 10 Step 4 flags the conversion to string keys.
- Output-kind enum `{paper, talk, code}` consistent across Task 7 + check_research_fixtures.py.
- Status enum `{active, dormant, answered}` consistent across Tasks 5 / 6 + check_research_fixtures.py.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-30-phase-3-b-3-research-handler.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review (spec + quality) between tasks. Matches how B.0 / B.1 / B.1.1 / B.2 were executed.

**2. Inline Execution** — execute tasks in this session via `superpowers:executing-plans`, batch execution with checkpoints for your review.

Which approach?
