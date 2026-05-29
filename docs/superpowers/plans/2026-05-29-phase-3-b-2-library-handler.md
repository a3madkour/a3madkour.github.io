# Phase 3 B.2 — Library Handler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the second concrete per-content-type publisher (library), turning four `~/org/notes/library-{reading,listening,playing,watching}.org` source files into `data/{reading,listening,playing,watching}.yaml` rows via `a3-pub.sh --publish-living`. Library items are URL-less; the publisher emits YAML rows, never per-page Hugo bundles.

**Architecture:** New `a3madkour-publish-library.el` module exports `publish-library-file (file)`, registered four times in `a3madkour-pub-living--handlers` (one entry per `library-<medium>` section symbol, all pointing at the same function). A per-medium config table inside the module captures the four-way variance (yaml filename + default media_type + allowed media_types + allowed statuses). The handler walks top-level org headings via `org-element-parse-buffer`, normalizes each to a YAML-row plist, deterministically renders the yaml, and writes if different. No ox-hugo invocation (drawer-only metadata), no link rewriter (no body), no asset copier (covers are manually committed to `static/library/covers/`). Two shared helpers ship in support: `--git-mtime-of-file` (retroactively closes B.1 follow-up #2 on garden's `last_modified` fallback) and `--filter-editorial-tags` (retroactively closes B.1.1 follow-up #6 on garden's TODO-tag pollution).

**Tech Stack:** Emacs Lisp + ert (dotfiles); `org-element` AST traversal; Python integration fixtures under `tools/test_publish_integration.py` (stdlib only); existing site linters `check_library_fixtures.py` + `check_library_links.py` + `check_library_covers.py` gate output shape.

**Cross-repo commit map:**
- Dotfiles repo (`~/dotfiles/`): all elisp + sibling tests + `a3-pub.sh` update.
- Site repo (this one): integration fixtures, fixture-clear (in spot-check task), `CLAUDE.md` status pointer update, memory updates.

**Reading list before starting:**
- `CLAUDE.md` (this repo) — current status pointer.
- `docs/superpowers/specs/2026-05-29-phase-3-b-2-library-handler-design.md` — §3 config table, §5 property mapping, §6 handler flow, §7 error handling, §8 idempotency.
- `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` §8 — high-level library pipeline (caveat: pre-linter status enums; treat live linter as authoritative).
- `docs/superpowers/plans/2026-05-25-phase-3-b-1-garden-handler.md` — closest implementation precedent (signature shapes, test patterns).
- `tools/check_library_fixtures.py` — authoritative shape contract for B-emitted yaml.
- Memory: `.claude/memory/project_b1_complete.md`, `.claude/memory/project_next_slice.md`, `.claude/memory/reference_goldmark_unsafe_for_ox_hugo_html.md`.
- Existing dotfiles modules to grep for call surface: `a3madkour-publish.el` (`note-section`, `begin-publish`, `finish-publish`), `a3madkour-publish-history.el` (`record-publish`, `manifest` helpers), `a3madkour-publish-frontmatter.el` (B.1's garden normalizer — model for the tag-filter retroactive change), `a3madkour-publish-living.el` (handler registration pattern via `with-eval-after-load`).
- Existing site fixtures to mirror: `data/reading.yaml` / `data/listening.yaml` / `data/playing.yaml` / `data/watching.yaml` — shape B.2 must match.

---

## File Structure

**New files (dotfiles):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el` — library handler module. Exports `a3madkour-pub-library/publish-library-file`. Hosts the per-medium config table, `--normalize-item`, `--render-library-yaml`, slug + dedup helpers, cover-file check.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el` — sibling test. ~25-30 tests across slug derivation, normalize-item branches, render-yaml determinism, end-to-end publish.

**Modified files (dotfiles):**
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el` — add `--git-mtime-of-file` helper.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el` — add 2 git-mtime tests (tracked + untracked).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` — add `--filter-editorial-tags` helper; integrate into the garden normalizer to retroactively close B.1.1 follow-up #6.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el` — add tag-filter tests + extend garden test to assert TODO/NOEXPORT filtered.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el` — register 4 library handlers via `with-eval-after-load`.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el` — extend the registration test to assert all 4 library entries.
- `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` — add `-l a3madkour-publish-library` to the three publish-side intercepts (publish-living, publish-deliberate, default-exec). NOT `--check-orphans`.

**Modified files (site repo):**
- `tools/test_publish_integration.py` — 5 new fixtures (publish-once, idempotency, slug-shift, removed-item, linter-parity) under `TestLibraryPublishLiving`.
- `CLAUDE.md` — status pointer update at slice end ("B.2 library handler shipped"); strike-through `~~B.1.1~~ → B.2` next-up.
- `.claude/memory/MEMORY.md` + `.claude/memory/project_b2_complete.md` (new) + `.claude/memory/project_next_slice.md` (updated to point at B.3).

**Touched at spot-check, not by automation:**
- `data/{reading,listening,playing,watching}.yaml` — fixture rows replaced wholesale by real B-emitted rows when the user runs `a3-pub.sh --publish-living` against real-content `~/org/notes/library-*.org`.

---

## Task 1: `--git-mtime-of-file` helper in `a3madkour-publish-history.el`

**Why first:** Shared helper used by both garden (retroactive fallback fix) and library (per-spec fallback). Pure-IO function — no upstream dependencies. Ships with sibling tests.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-history-test.el`

- [ ] **Step 1: Write the failing tests.**

Add to `a3madkour-publish-history-test.el`:

```elisp
(ert-deftest a3madkour-pub-history--git-mtime-tracked-file ()
  "git-mtime-of-file returns YYYY-MM-DD for a git-tracked file."
  (let* ((tmpdir (make-temp-file "a3-pub-git-" t))
         (file (expand-file-name "tracked.org" tmpdir))
         (default-directory tmpdir))
    (unwind-protect
        (progn
          (call-process "git" nil nil nil "init" "-q")
          (call-process "git" nil nil nil "config" "user.email" "test@example.com")
          (call-process "git" nil nil nil "config" "user.name" "Test")
          (with-temp-file file (insert "content\n"))
          (call-process "git" nil nil nil "add" "tracked.org")
          (call-process "git" nil nil nil "commit" "-q" "-m" "init")
          (let ((result (a3madkour-pub-history/git-mtime-of-file file)))
            (should (stringp result))
            (should (string-match-p "^[0-9]\\{4\\}-[0-9]\\{2\\}-[0-9]\\{2\\}$" result))))
      (delete-directory tmpdir t))))

(ert-deftest a3madkour-pub-history--git-mtime-untracked-file ()
  "git-mtime-of-file returns nil for a file not under git."
  (let* ((tmpdir (make-temp-file "a3-pub-nogit-" t))
         (file (expand-file-name "untracked.org" tmpdir)))
    (unwind-protect
        (progn
          (with-temp-file file (insert "content\n"))
          (should-not (a3madkour-pub-history/git-mtime-of-file file)))
      (delete-directory tmpdir t))))
```

- [ ] **Step 2: Run to verify failure.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . -l a3madkour-publish-history -l a3madkour-publish-history-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: 2 failures (`Symbol's function definition is void: a3madkour-pub-history/git-mtime-of-file`).

- [ ] **Step 3: Implement the helper.** Add at the bottom of `a3madkour-publish-history.el` (before `(provide ...)`):

```elisp
(defun a3madkour-pub-history/git-mtime-of-file (file)
  "Return the YYYY-MM-DD date of the most recent commit touching FILE.
Returns nil when FILE is not under git or has never been committed.

Used as the per-file fallback for `last_modified' when no explicit
property is set on the source (garden + library per spec §8 + §5
respectively)."
  (when (file-exists-p file)
    (let* ((default-directory (file-name-directory (expand-file-name file)))
           (basename (file-name-nondirectory file))
           (raw (with-output-to-string
                  (with-current-buffer standard-output
                    (call-process "git" nil t nil
                                  "log" "-1" "--format=%cs" "--" basename))))
           (trimmed (string-trim raw)))
      (when (and trimmed
                 (not (string-empty-p trimmed))
                 (string-match-p "^[0-9]\\{4\\}-[0-9]\\{2\\}-[0-9]\\{2\\}$" trimmed))
        trimmed))))
```

> **Note on `%cs`:** git's `--format=%cs` is the committer-date in short ISO form (added in git 2.10+, available on all macOS / Linux installs we target). Avoids manual date parsing.

- [ ] **Step 4: Run; expect green.**

```bash
emacs --batch -L . -l a3madkour-publish-history -l a3madkour-publish-history-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: 2 new tests pass (plus existing history tests).

- [ ] **Step 5: Run the full ert suite.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: `Ran 273 tests, 273 results as expected, 0 unexpected.` (271 baseline + 2 new.)

- [ ] **Step 6: Commit (dotfiles).**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-history.el \
        emacs-configs/custom/lisp/a3madkour-publish-history-test.el
git commit -m "feat(b-2): git-mtime-of-file helper in publish-history

Shared by garden (retroactive last_modified fallback fix, closes B.1
follow-up #2) and library (per-item last_modified fallback per B.2
spec §5). Uses git log --format=%cs for the short ISO date."
```

---

## Task 2: `--filter-editorial-tags` helper + retroactive garden integration

**Why now:** Same helper used by both garden (retroactive close of B.1.1 follow-up #6 — TODO tag pollution in `tags:`) and library (per spec §5). Lives in `a3madkour-publish-frontmatter.el` since both callers are normalizers.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

- [ ] **Step 1: Write failing tests.**

Add to `a3madkour-publish-frontmatter-test.el`:

```elisp
(ert-deftest a3madkour-pub-frontmatter--filter-editorial-tags-defaults ()
  "Editorial tags TODO/DONE/WAIT/CANCELED/HOLD/NOEXPORT/ATTACH stripped by default."
  (should (equal (a3madkour-pub-frontmatter/filter-editorial-tags
                  '("alpha" "TODO" "beta" "NOEXPORT" "gamma"))
                 '("alpha" "beta" "gamma")))
  (should (equal (a3madkour-pub-frontmatter/filter-editorial-tags
                  '("TODO" "DONE" "WAIT" "CANCELED" "HOLD" "NOEXPORT" "ATTACH"))
                 nil))
  (should (equal (a3madkour-pub-frontmatter/filter-editorial-tags '()) nil))
  (should (equal (a3madkour-pub-frontmatter/filter-editorial-tags '("clean"))
                 '("clean"))))

(ert-deftest a3madkour-pub-frontmatter--filter-editorial-tags-extra-exclusions ()
  "Per-call extra-exclusions list merges with the defcustom defaults."
  (should (equal (a3madkour-pub-frontmatter/filter-editorial-tags
                  '("alpha" "DRAFT" "beta" "TODO")
                  '("DRAFT"))
                 '("alpha" "beta"))))

(ert-deftest a3madkour-pub-frontmatter--garden-tags-strip-editorial ()
  "Garden normalizer applies the editorial-tag filter (closes B.1.1 #6)."
  (let* ((raw '((title . "Note")
                (tags  . ("Bayesian" "TODO" "stats"))))
         (out (a3madkour-pub-frontmatter/normalize 'garden raw "/tmp/x.org")))
    (should (equal (alist-get 'tags out) '("Bayesian" "stats")))))
```

- [ ] **Step 2: Run to verify failure.**

```bash
emacs --batch -L . -l a3madkour-publish-frontmatter -l a3madkour-publish-frontmatter-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: 3 failures (function undefined; garden normalizer doesn't filter).

- [ ] **Step 3: Implement.** Add to `a3madkour-publish-frontmatter.el` near the top of `;;; Code:`:

```elisp
(defcustom a3madkour-pub-editorial-tags
  '("TODO" "DONE" "WAIT" "CANCELED" "HOLD" "NOEXPORT" "ATTACH")
  "Org tags treated as editorial (org-mode workflow keywords) and
stripped from round-tripped tag lists by `filter-editorial-tags'.
Used by both garden (file-level tags) and library (per-heading tags)
normalizers."
  :type '(repeat string) :group 'a3madkour-publish)

(defun a3madkour-pub-frontmatter/filter-editorial-tags (tags &optional extra-exclusions)
  "Strip editorial tags from TAGS (a list of strings).

EXTRA-EXCLUSIONS is an optional list of additional tag names to strip,
merged with the defcustom default `a3madkour-pub-editorial-tags'.
Preserves order of remaining tags."
  (let ((excl (append a3madkour-pub-editorial-tags extra-exclusions)))
    (seq-filter (lambda (tag) (not (member tag excl))) tags)))
```

Then update `--normalize-garden` to apply the filter. Find the existing function and add to its body (after copy-alist, before return):

```elisp
;; B.2: retroactively close B.1.1 follow-up #6 — strip editorial tags
;; (TODO, NOEXPORT, etc.) from the round-tripped tag list.
(when-let ((tags (alist-get 'tags out)))
  (setf (alist-get 'tags out)
        (a3madkour-pub-frontmatter/filter-editorial-tags tags)))
```

- [ ] **Step 4: Run; expect green.**

```bash
emacs --batch -L . -l a3madkour-publish-frontmatter -l a3madkour-publish-frontmatter-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -5
```

Expected: all 3 new tests pass; existing garden tests still pass.

- [ ] **Step 5: Run full suite.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: `Ran 276 tests, 276 results as expected, 0 unexpected.` (273 + 3 new.)

- [ ] **Step 6: Commit (dotfiles).**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el \
        emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "feat(b-2): filter-editorial-tags helper + retroactive garden fix

Defcustom + helper strip {TODO,DONE,WAIT,CANCELED,HOLD,NOEXPORT,ATTACH}
from round-tripped tag lists. Garden normalizer wired up to use it,
closing B.1.1 follow-up #6 (TODO polluting garden tags:)."
```

---

## Task 3: Scaffold `a3madkour-publish-library.el` module + sibling test + `a3-pub.sh` `-l` line

**Why before implementation:** Stub the new module + register it in the wrapper so all subsequent tasks start from a loadable state. Per [[plan-wrapper-script-updates]] feedback, add the `-l` line up front (not at the end).

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh`

- [ ] **Step 1: Create the module scaffold.** Write to `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el`:

```elisp
;;; a3madkour-publish-library.el --- library per-file publish handler  -*- lexical-binding: t; -*-

;;; Commentary:

;; B.2: library per-file publish handler.  Walks top-level org headings
;; inside one of four source files (library-{reading,listening,playing,
;; watching}.org), normalizes each heading to a YAML row plist, renders
;; the corresponding data/<medium>.yaml deterministically.
;;
;; Registered into `a3madkour-pub-living--handlers' as four entries
;; (one per library-<medium> section symbol, all pointing at the same
;; `publish-library-file' entry point) by `a3madkour-publish-living'.

;;; Code:

(require 'org-element)
(require 'a3madkour-publish)
(require 'a3madkour-publish-frontmatter)
(require 'a3madkour-publish-history)

(defconst a3madkour-pub-library--config
  '((library-reading
     "reading.yaml"  "book"  ("book")
     ("finished" "reading" "queued" "abandoned"))
    (library-listening
     "listening.yaml" "album" ("album" "track")
     ("finished" "listening" "queued" "dropped"))
    (library-playing
     "playing.yaml"   "game"  ("game")
     ("finished" "100pct" "playing" "queued" "dropped"))
    (library-watching
     "watching.yaml"  "film"  ("film" "series")
     ("finished" "watching" "queued" "dropped")))
  "Per-section config: (SYMBOL YAML-FILE DEFAULT-MT (ALLOWED-MT...) (ALLOWED-STATUS...)).
Status enums copied verbatim from check_library_fixtures.py — the linter is
authoritative for B-emitted YAML.")

(defun a3madkour-pub-library--config-for (section)
  "Return (yaml-file default-mt allowed-mt allowed-status) for SECTION.
Errors when SECTION is not a known library section."
  (let ((entry (assq section a3madkour-pub-library--config)))
    (unless entry
      (error "a3madkour-pub-library: unknown library section %S" section))
    (cdr entry)))

(defun a3madkour-pub-library/publish-library-file (file)
  "Publish a single library FILE to data/<medium>.yaml.

Stub (Task 3): signature only; real implementation lands in Tasks 4-10."
  (ignore file)
  nil)

(provide 'a3madkour-publish-library)

;;; a3madkour-publish-library.el ends here
```

- [ ] **Step 2: Create the sibling test scaffold.** Write to `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el`:

```elisp
;;; a3madkour-publish-library-test.el --- tests for library handler  -*- lexical-binding: t; -*-

(require 'ert)
(require 'a3madkour-publish-library)

(ert-deftest a3madkour-pub-library--module-loads ()
  "Smoke: module loadable and exposes publish-library-file."
  (should (fboundp 'a3madkour-pub-library/publish-library-file)))

(ert-deftest a3madkour-pub-library--config-table-shape ()
  "Per-medium config table has all 4 library sections with the right shape."
  (dolist (section '(library-reading library-listening library-playing library-watching))
    (let ((cfg (a3madkour-pub-library--config-for section)))
      (should (= 4 (length cfg)))
      (should (stringp (nth 0 cfg)))           ; yaml filename
      (should (stringp (nth 1 cfg)))           ; default media_type
      (should (listp (nth 2 cfg)))             ; allowed media_types
      (should (listp (nth 3 cfg)))             ; allowed statuses
      (should (member (nth 1 cfg) (nth 2 cfg))))) ; default ∈ allowed
  (should-error (a3madkour-pub-library--config-for 'bogus)))

(provide 'a3madkour-publish-library-test)

;;; a3madkour-publish-library-test.el ends here
```

- [ ] **Step 3: Add `-l a3madkour-publish-library` to `a3-pub.sh`.** Three publish-side intercepts need the line; `--check-orphans` does NOT.

```bash
grep -n "a3madkour-publish-garden" ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh
```

Expected: three lines (one per publish-side intercept) like `    -l a3madkour-publish-garden \`.

In each of those three locations, add immediately AFTER the garden line:

```bash
    -l a3madkour-publish-library \
```

- [ ] **Step 4: Run the new sibling test.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . -l a3madkour-publish-library -l a3madkour-publish-library-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: 2 passes.

- [ ] **Step 5: Run full suite + smoke the wrapper.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3

cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
```

Expected: 278 tests pass (276 + 2 new); `--publish-living` exits 0 silently (handler stub not yet registered in living).

- [ ] **Step 6: Commit (dotfiles).**

```bash
cd ~/dotfiles
git add emacs-configs/custom/lisp/a3madkour-publish-library.el \
        emacs-configs/custom/lisp/a3madkour-publish-library-test.el \
        emacs-configs/custom/lisp/a3-pub.sh
git commit -m "scaffold(b-2): a3madkour-publish-library module + wrapper -l line

Stub publish-library-file + per-medium config table + smoke tests.
Real implementation in Tasks 4-10."
```

---

## Task 4: `--title-to-slug` helper

**Spec §5:** Title → Unicode NFD → drop combining marks → lowercase → collapse `[^a-z0-9]+` runs to single `-` → trim leading/trailing `-`. Empty result → caller WARNs.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el`

- [ ] **Step 1: Write failing tests (table-driven across edge cases).**

```elisp
(ert-deftest a3madkour-pub-library--title-to-slug ()
  "Title-to-slug derivation covers spec §5 edge cases."
  (should (equal (a3madkour-pub-library--title-to-slug "Pride and Prejudice")
                 "pride-and-prejudice"))
  (should (equal (a3madkour-pub-library--title-to-slug "L'Étranger")
                 "l-etranger"))
  (should (equal (a3madkour-pub-library--title-to-slug "Köyaanisqatsi")
                 "koyaanisqatsi"))
  (should (equal (a3madkour-pub-library--title-to-slug "Crime & Punishment")
                 "crime-punishment"))
  (should (equal (a3madkour-pub-library--title-to-slug "Dune: Part One")
                 "dune-part-one"))
  (should (equal (a3madkour-pub-library--title-to-slug "Maximum a Posteriori (MAP)")
                 "maximum-a-posteriori-map"))
  (should (equal (a3madkour-pub-library--title-to-slug "1984")
                 "1984"))
  (should (equal (a3madkour-pub-library--title-to-slug "  Leading-Trailing  ")
                 "leading-trailing"))
  (should (equal (a3madkour-pub-library--title-to-slug "!?!")
                 ""))
  (should (equal (a3madkour-pub-library--title-to-slug "Severance S2")
                 "severance-s2")))
```

- [ ] **Step 2: Run; expect failure.**

```bash
emacs --batch -L . -l a3madkour-publish-library -l a3madkour-publish-library-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

- [ ] **Step 3: Implement.** Add to `a3madkour-publish-library.el` before `publish-library-file`:

```elisp
(defun a3madkour-pub-library--title-to-slug (title)
  "Derive a kebab-case slug from TITLE per spec §5.

Pipeline: NFD-decompose → drop combining marks → lowercase →
collapse non-alphanumeric runs to single `-' → trim leading/trailing
`-'. Returns empty string when no alphanumeric content survives —
callers WARN and skip the item in that case."
  (let* ((decomposed (ucs-normalize-NFD-string title))
         ;; Drop combining marks (Unicode category Mn).
         (stripped (replace-regexp-in-string
                    "\\cM" "" decomposed))
         (lower (downcase stripped))
         ;; Collapse runs of any non-alphanumeric (Unicode-aware) to a single `-'.
         (dashed (replace-regexp-in-string
                  "[^a-z0-9]+" "-" lower))
         ;; Trim leading/trailing `-'.
         (trimmed (replace-regexp-in-string "\\(^-+\\|-+$\\)" "" dashed)))
    trimmed))
```

> **Note on `\\cM`:** Emacs regex syntax for the Unicode "Mark" character class — matches all combining marks across scripts (Latin diacritics, Arabic harakat, etc.).

- [ ] **Step 4: Run; expect green.**

```bash
emacs --batch -L . -l a3madkour-publish-library -l a3madkour-publish-library-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: 10 new should-clauses all pass.

- [ ] **Step 5: Commit (dotfiles).**

```bash
git add emacs-configs/custom/lisp/a3madkour-publish-library.el \
        emacs-configs/custom/lisp/a3madkour-publish-library-test.el
git commit -m "feat(b-2): --title-to-slug helper per spec §5

NFD-decompose → strip combining marks → lowercase → collapse
non-alphanumeric runs → trim. Handles apostrophes, diacritics,
ampersands, colons, parentheticals, all-non-alphanum edge."
```

---

## Task 5: `--normalize-item` — required fields (title, slug, creator, year, media_type, status)

**Spec §5 + §6 step 4:** Each heading → row plist. This task covers the required-field branch: title from `:raw-value`, slug from `:SLUG:` drawer or fallback, creator/year from drawer, media_type with section-default fallback + enum validation, status with enum validation. All validation failures WARN and emit anyway (let linter catch).

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(defun a3madkour-pub-library-test--parse-headline (org-text)
  "Helper: parse ORG-TEXT and return the first top-level headline element."
  (with-temp-buffer
    (insert org-text)
    (org-mode)
    (car (org-element-map (org-element-parse-buffer) 'headline #'identity nil nil nil))))

(ert-deftest a3madkour-pub-library--normalize-required-fields ()
  "Required-field happy path covers title, slug, creator, year, media_type, status."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Pride and Prejudice
:PROPERTIES:
:CREATOR: Jane Austen
:YEAR: 1813
:STATUS: finished
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org")))
    (should (equal (plist-get row :slug) "pride-and-prejudice"))
    (should (equal (plist-get row :title) "Pride and Prejudice"))
    (should (equal (plist-get row :creator) "Jane Austen"))
    (should (equal (plist-get row :year) 1813))
    (should (equal (plist-get row :media_type) "book"))
    (should (equal (plist-get row :status) "finished"))))

(ert-deftest a3madkour-pub-library--normalize-slug-override ()
  "Explicit :SLUG: drawer overrides title-derived fallback."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* L'Étranger
:PROPERTIES:
:SLUG: the-stranger
:CREATOR: Camus
:YEAR: 1942
:STATUS: finished
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org")))
    (should (equal (plist-get row :slug) "the-stranger"))))

(ert-deftest a3madkour-pub-library--normalize-media-type-default ()
  "Missing :MEDIA_TYPE: defaults to the section default (book/album/game/film)."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Untitled
:PROPERTIES:
:CREATOR: Someone
:YEAR: 2024
:STATUS: queued
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-watching))
         (row (a3madkour-pub-library--normalize-item src 'library-watching cfg "/tmp/x.org")))
    (should (equal (plist-get row :media_type) "film"))))

(ert-deftest a3madkour-pub-library--normalize-media-type-override ()
  "Explicit :MEDIA_TYPE: overrides the section default."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Severance S2
:PROPERTIES:
:MEDIA_TYPE: series
:CREATOR: Apple TV+
:YEAR: 2025
:STATUS: finished
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-watching))
         (row (a3madkour-pub-library--normalize-item src 'library-watching cfg "/tmp/x.org")))
    (should (equal (plist-get row :media_type) "series"))))

(ert-deftest a3madkour-pub-library--normalize-status-enum-warn ()
  "Out-of-enum :STATUS: WARNs but still emits the value (linter catches)."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Bogus
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: to-read
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (warnings '())
         (row (cl-letf (((symbol-function 'message)
                         (lambda (fmt &rest args)
                           (push (apply #'format fmt args) warnings))))
                (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org"))))
    (should (equal (plist-get row :status) "to-read"))
    (should (seq-some (lambda (m) (string-match-p "status.*to-read.*not in" m)) warnings))))
```

- [ ] **Step 2: Run; expect failure** (function undefined).

- [ ] **Step 3: Implement `--normalize-item` skeleton with required-field branch.**

```elisp
(defun a3madkour-pub-library--headline-property (headline prop)
  "Read a single drawer property PROP (a string like \"CREATOR\") off HEADLINE.
Returns nil if not set or empty."
  (let ((val (org-element-property
              (intern (concat ":" prop)) headline)))
    (and (stringp val) (not (string-empty-p val)) (string-trim val))))

(defun a3madkour-pub-library--warn (file slug fmt &rest args)
  "Emit a WARN message with FILE + SLUG context."
  (apply #'message (concat "a3madkour-pub-library WARN [%s slug=%s]: " fmt)
         (file-name-nondirectory file) (or slug "?") args))

(defun a3madkour-pub-library--resolve-slug (headline title file)
  "Resolve slug: :SLUG: drawer → fallback `--title-to-slug'.
Empty result → WARN + return nil (caller skips the item)."
  (let* ((drawer-slug (a3madkour-pub-library--headline-property headline "SLUG"))
         (derived (and (not drawer-slug) (a3madkour-pub-library--title-to-slug title)))
         (slug (or drawer-slug derived)))
    (cond
     ((and slug (not (string-empty-p slug))) slug)
     (t (a3madkour-pub-library--warn file nil
                                     "empty slug for title %S; skipping" title)
        nil))))

(cl-defun a3madkour-pub-library--normalize-item (headline section cfg file)
  "Build a YAML-row plist from HEADLINE for SECTION using CFG.
FILE is the source path (used for WARN context + git-mtime fallback in later tasks).

Returns nil when the item should be skipped (e.g. empty slug)."
  (let* ((title (org-element-property :raw-value headline))
         (slug (a3madkour-pub-library--resolve-slug headline title file)))
    (unless slug
      (cl-return-from a3madkour-pub-library--normalize-item nil))
    (let* ((default-mt    (nth 1 cfg))
           (allowed-mt    (nth 2 cfg))
           (allowed-stat  (nth 3 cfg))
           (drawer-mt     (a3madkour-pub-library--headline-property headline "MEDIA_TYPE"))
           (media-type    (or drawer-mt default-mt))
           (status        (a3madkour-pub-library--headline-property headline "STATUS"))
           (creator       (a3madkour-pub-library--headline-property headline "CREATOR"))
           (year-raw      (a3madkour-pub-library--headline-property headline "YEAR"))
           (year          (and year-raw (string-to-number year-raw))))
      (unless (member media-type allowed-mt)
        (a3madkour-pub-library--warn file slug
                                     "media_type=%s not in %S" media-type allowed-mt))
      (unless (and status (member status allowed-stat))
        (a3madkour-pub-library--warn file slug
                                     "status=%s not in %S" status allowed-stat))
      (list :slug slug
            :title title
            :creator creator
            :year year
            :media_type media-type
            :status status))))
```

Add `(require 'cl-lib)` at the top of the module to provide `cl-return-from`.

- [ ] **Step 4: Run; expect green.**

```bash
emacs --batch -L . -l a3madkour-publish-library -l a3madkour-publish-library-test \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: 5 new tests pass.

- [ ] **Step 5: Run full suite.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

- [ ] **Step 6: Commit.**

```bash
git commit -m "feat(b-2): library --normalize-item required fields

Title from :raw-value; slug from :SLUG: drawer or title-derived fallback;
creator/year from drawer (year string→int); media_type with section
default fallback + enum WARN; status enum WARN. Skip item on empty slug."
```

---

## Task 6: `--normalize-item` — optional pass-throughs + `last_modified` fallback

**Spec §5 optional fields:** `started`, `finished`, `spoiler_level`, `cite_key`, `canonical_url`, `note_slug`, `preview`. Plus required-but-fallback `last_modified` (drawer → git-mtime).

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-library--normalize-optional-passthroughs ()
  "Optional drawer fields pass through unchanged."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Item
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: finished
:STARTED: 2024-01-01
:FINISHED: 2024-06-15
:SPOILER_LEVEL: light
:CITE_KEY: doe2024
:CANONICAL_URL: https://example.com/item
:NOTE_SLUG: my-note
:PREVIEW: A short annotation.
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org")))
    (should (equal (plist-get row :started) "2024-01-01"))
    (should (equal (plist-get row :finished) "2024-06-15"))
    (should (equal (plist-get row :spoiler_level) "light"))
    (should (equal (plist-get row :cite_key) "doe2024"))
    (should (equal (plist-get row :canonical_url) "https://example.com/item"))
    (should (equal (plist-get row :note_slug) "my-note"))
    (should (equal (plist-get row :preview) "A short annotation."))))

(ert-deftest a3madkour-pub-library--normalize-optional-absent ()
  "Absent optional drawers don't appear in the row plist."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Item
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: queued
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org")))
    (should-not (plist-member row :started))
    (should-not (plist-member row :finished))
    (should-not (plist-member row :preview))))

(ert-deftest a3madkour-pub-library--normalize-last-modified-drawer ()
  "Per-heading :LAST_MODIFIED: drawer beats git-mtime fallback."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Item
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: queued
:LAST_MODIFIED: 2025-03-14
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org")))
    (should (equal (plist-get row :last_modified) "2025-03-14"))))

(ert-deftest a3madkour-pub-library--normalize-last-modified-git-mtime-fallback ()
  "Absent :LAST_MODIFIED: falls back to git-mtime-of-file."
  (let* ((tmpdir (make-temp-file "a3-pub-libmtime-" t))
         (file (expand-file-name "x.org" tmpdir)))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
                   (lambda (f) (ignore f) "2026-01-15")))
          (let* ((src (a3madkour-pub-library-test--parse-headline
                       "* Item
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: queued
:END:
"))
                 (cfg (a3madkour-pub-library--config-for 'library-reading))
                 (row (a3madkour-pub-library--normalize-item src 'library-reading cfg file)))
            (should (equal (plist-get row :last_modified) "2026-01-15"))))
      (delete-directory tmpdir t))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.** Extend `--normalize-item` after the required-field block:

```elisp
;; Optional drawer pass-throughs.
(dolist (prop '(("STARTED" . :started)
                ("FINISHED" . :finished)
                ("SPOILER_LEVEL" . :spoiler_level)
                ("CITE_KEY" . :cite_key)
                ("CANONICAL_URL" . :canonical_url)
                ("NOTE_SLUG" . :note_slug)
                ("PREVIEW" . :preview)))
  (let ((val (a3madkour-pub-library--headline-property headline (car prop))))
    (when val
      (setq row-plist (plist-put row-plist (cdr prop) val)))))

;; last_modified: :LAST_MODIFIED: drawer → git-mtime fallback.
(let* ((drawer-lm (a3madkour-pub-library--headline-property headline "LAST_MODIFIED"))
       (lm (or drawer-lm
               (a3madkour-pub-history/git-mtime-of-file file))))
  (when lm
    (setq row-plist (plist-put row-plist :last_modified lm))))
```

Refactor the function body so the required-field plist is named `row-plist`:

```elisp
(cl-defun a3madkour-pub-library--normalize-item (headline section cfg file)
  "Build a YAML-row plist from HEADLINE for SECTION using CFG. ..."
  (let* ((title (org-element-property :raw-value headline))
         (slug (a3madkour-pub-library--resolve-slug headline title file)))
    (unless slug
      (cl-return-from a3madkour-pub-library--normalize-item nil))
    (let* ((default-mt    (nth 1 cfg))
           (allowed-mt    (nth 2 cfg))
           (allowed-stat  (nth 3 cfg))
           (drawer-mt     (a3madkour-pub-library--headline-property headline "MEDIA_TYPE"))
           (media-type    (or drawer-mt default-mt))
           (status        (a3madkour-pub-library--headline-property headline "STATUS"))
           (creator       (a3madkour-pub-library--headline-property headline "CREATOR"))
           (year-raw      (a3madkour-pub-library--headline-property headline "YEAR"))
           (year          (and year-raw (string-to-number year-raw)))
           (row-plist     (list :slug slug
                                :title title
                                :creator creator
                                :year year
                                :media_type media-type
                                :status status)))
      (unless (member media-type allowed-mt)
        (a3madkour-pub-library--warn file slug
                                     "media_type=%s not in %S" media-type allowed-mt))
      (unless (and status (member status allowed-stat))
        (a3madkour-pub-library--warn file slug
                                     "status=%s not in %S" status allowed-stat))
      ;; Optional drawer pass-throughs.
      (dolist (prop '(("STARTED" . :started)
                      ("FINISHED" . :finished)
                      ("SPOILER_LEVEL" . :spoiler_level)
                      ("CITE_KEY" . :cite_key)
                      ("CANONICAL_URL" . :canonical_url)
                      ("NOTE_SLUG" . :note_slug)
                      ("PREVIEW" . :preview)))
        (let ((val (a3madkour-pub-library--headline-property headline (car prop))))
          (when val
            (setq row-plist (plist-put row-plist (cdr prop) val)))))
      ;; last_modified: drawer → git-mtime fallback.
      (let* ((drawer-lm (a3madkour-pub-library--headline-property headline "LAST_MODIFIED"))
             (lm (or drawer-lm
                     (a3madkour-pub-history/git-mtime-of-file file))))
        (when lm
          (setq row-plist (plist-put row-plist :last_modified lm))))
      row-plist)))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Commit.**

```bash
git commit -m "feat(b-2): library --normalize-item optional pass-throughs + last_modified

started/finished/spoiler_level/cite_key/canonical_url/note_slug/preview
drawer pass-throughs (absent → omitted). last_modified: :LAST_MODIFIED:
drawer → git-mtime fallback."
```

---

## Task 7: `--normalize-item` — tags filter

**Spec §5:** Per-heading org tags filtered via `--filter-editorial-tags` (from Task 2).

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-library--normalize-tags-roundtrip ()
  "Per-heading org tags round-trip via filter-editorial-tags."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Pride and Prejudice :classics:romance:
:PROPERTIES:
:CREATOR: Austen
:YEAR: 1813
:STATUS: finished
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org")))
    (should (equal (plist-get row :tags) '("classics" "romance")))))

(ert-deftest a3madkour-pub-library--normalize-tags-strips-editorial ()
  "TODO/NOEXPORT/etc. on per-heading tags are stripped."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Item :classics:TODO:fiction:NOEXPORT:
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: queued
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org")))
    (should (equal (plist-get row :tags) '("classics" "fiction")))))

(ert-deftest a3madkour-pub-library--normalize-tags-empty-after-filter ()
  "All-editorial tag list → :tags key still present with empty list (linter needs the key)."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Item :TODO:NOEXPORT:
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: queued
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org")))
    (should (equal (plist-get row :tags) '()))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.** In `--normalize-item`, append after the optional drawer pass-through block (before `last_modified`):

```elisp
;; Tags: per-heading org tags through editorial filter.
(let* ((raw-tags (org-element-property :tags headline))
       (filtered (a3madkour-pub-frontmatter/filter-editorial-tags raw-tags)))
  ;; Always emit :tags (linter requires the field even when empty).
  (setq row-plist (plist-put row-plist :tags filtered)))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Commit.**

```bash
git commit -m "feat(b-2): library --normalize-item tags filter

Per-heading org tags through filter-editorial-tags (shared with garden).
Empty :tags key always emitted (linter requires the field)."
```

---

## Task 8: `--normalize-item` — extras mapping + cover-file existence check

**Spec §5:** Per-medium extras drawer properties → `extras.<key>` nested map. Cover-file existence check: WARN if `<site-static-dir>/library/covers/<value>` missing.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-library--normalize-extras-book ()
  "Book extras: ISBN + progress_pct/progress_label + universal covers."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Item
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: reading
:ISBN: 9780141439518
:PROGRESS_PCT: 42
:PROGRESS_LABEL: p. 84 / 200
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org"))
         (extras (plist-get row :extras)))
    (should (equal (plist-get extras :isbn) "9780141439518"))
    (should (equal (plist-get extras :progress_pct) 42))
    (should (equal (plist-get extras :progress_label) "p. 84 / 200"))))

(ert-deftest a3madkour-pub-library--normalize-extras-game ()
  "Game extras: igdb_id (int) + hours_played (int) + platform."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Outer Wilds
:PROPERTIES:
:CREATOR: Mobius
:YEAR: 2019
:STATUS: playing
:IGDB_ID: 12345
:HOURS_PLAYED: 22
:PLATFORM: PC
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-playing))
         (row (a3madkour-pub-library--normalize-item src 'library-playing cfg "/tmp/x.org"))
         (extras (plist-get row :extras)))
    (should (equal (plist-get extras :igdb_id) 12345))
    (should (equal (plist-get extras :hours_played) 22))
    (should (equal (plist-get extras :platform) "PC"))))

(ert-deftest a3madkour-pub-library--normalize-extras-series ()
  "Series extras: episode_count + current_episode + current_season + tmdb_id."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Severance S2
:PROPERTIES:
:MEDIA_TYPE: series
:CREATOR: Apple TV+
:YEAR: 2025
:STATUS: finished
:EPISODE_COUNT: 10
:CURRENT_EPISODE: 4
:CURRENT_SEASON: 2
:TMDB_ID: 67890
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-watching))
         (row (a3madkour-pub-library--normalize-item src 'library-watching cfg "/tmp/x.org"))
         (extras (plist-get row :extras)))
    (should (equal (plist-get extras :episode_count) 10))
    (should (equal (plist-get extras :current_episode) 4))
    (should (equal (plist-get extras :current_season) 2))
    (should (equal (plist-get extras :tmdb_id) 67890))))

(ert-deftest a3madkour-pub-library--normalize-extras-ignored-cross-medium ()
  ":ISBN: on an album is silently ignored (forward-compatible)."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Album
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: listening
:ISBN: 9780000000000
:MBID: aaaaaaaa-bbbb
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-listening))
         (row (a3madkour-pub-library--normalize-item src 'library-listening cfg "/tmp/x.org"))
         (extras (plist-get row :extras)))
    (should-not (plist-member extras :isbn))
    (should (equal (plist-get extras :musicbrainz_release_group) "aaaaaaaa-bbbb"))))

(ert-deftest a3madkour-pub-library--normalize-cover-file-existence-warn ()
  "Missing cover file → WARN, but :cover_file key still emitted."
  (let* ((src (a3madkour-pub-library-test--parse-headline
               "* Item
:PROPERTIES:
:CREATOR: x
:YEAR: 2024
:STATUS: reading
:COVER_FILE: nonexistent.jpg
:END:
"))
         (cfg (a3madkour-pub-library--config-for 'library-reading))
         (warnings '())
         ;; Stub: --site-static-dir-of returns a tmp dir with no cover file.
         (tmpdir (make-temp-file "a3-pub-covers-" t)))
    (unwind-protect
        (cl-letf (((symbol-function 'a3madkour-pub-library--site-static-dir-of)
                   (lambda (file) (ignore file) tmpdir))
                  ((symbol-function 'message)
                   (lambda (fmt &rest args)
                     (push (apply #'format fmt args) warnings))))
          (let* ((row (a3madkour-pub-library--normalize-item src 'library-reading cfg "/tmp/x.org"))
                 (extras (plist-get row :extras)))
            (should (equal (plist-get extras :cover_file) "nonexistent.jpg"))
            (should (seq-some (lambda (m) (string-match-p "cover.*missing" m)) warnings))))
      (delete-directory tmpdir t))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.** Add the per-medium extras table + cover-stat helper + integrate into `--normalize-item`:

```elisp
(defconst a3madkour-pub-library--extras-by-media
  '(("book"
     ("ISBN" :isbn nil) ("PROGRESS_PCT" :progress_pct int)
     ("PROGRESS_LABEL" :progress_label nil)
     ("COVER_FILE" :cover_file nil) ("COVER_URL" :cover_url nil))
    ("album"
     ("MBID" :musicbrainz_release_group nil)
     ("COVER_FILE" :cover_file nil) ("COVER_URL" :cover_url nil))
    ("track"
     ("MBID" :musicbrainz_release_group nil)
     ("COVER_FILE" :cover_file nil) ("COVER_URL" :cover_url nil))
    ("game"
     ("IGDB_ID" :igdb_id int) ("HOURS_PLAYED" :hours_played int)
     ("PLATFORM" :platform nil)
     ("COVER_FILE" :cover_file nil) ("COVER_URL" :cover_url nil))
    ("film"
     ("RUNTIME_MIN" :runtime_min int) ("TMDB_ID" :tmdb_id int)
     ("COVER_FILE" :cover_file nil) ("COVER_URL" :cover_url nil))
    ("series"
     ("EPISODE_COUNT" :episode_count int) ("CURRENT_EPISODE" :current_episode int)
     ("CURRENT_SEASON" :current_season int) ("TMDB_ID" :tmdb_id int)
     ("COVER_FILE" :cover_file nil) ("COVER_URL" :cover_url nil)))
  "Per-medium extras drawer prop → yaml key + coercion.
Matches `tools/check_library_fixtures.py:ALLOWED_EXTRAS' exactly.")

(defun a3madkour-pub-library--site-static-dir-of (source-file)
  "Derive the site static/ dir given SOURCE-FILE (a library .org).
Cascade: A3_PUB_SITE_STATIC_DIR env var → sibling of `a3madkour-pub/site-data-dir'.
Returns absolute path with trailing slash, or nil if unresolvable."
  (ignore source-file)
  (or (getenv "A3_PUB_SITE_STATIC_DIR")
      (when (and (boundp 'a3madkour-pub/site-data-dir)
                 a3madkour-pub/site-data-dir)
        (expand-file-name "../static/"
                          (directory-file-name a3madkour-pub/site-data-dir)))))

(defun a3madkour-pub-library--collect-extras (headline media-type file slug)
  "Collect extras drawer properties from HEADLINE per MEDIA-TYPE.
WARNs on missing cover-file (emits key anyway).  Returns a plist or nil."
  (let* ((spec (cdr (assoc media-type a3madkour-pub-library--extras-by-media)))
         (result '()))
    (dolist (entry spec)
      (let* ((prop (nth 0 entry))
             (key (nth 1 entry))
             (coerce (nth 2 entry))
             (raw (a3madkour-pub-library--headline-property headline prop)))
        (when raw
          (let ((val (if (eq coerce 'int) (string-to-number raw) raw)))
            (setq result (plist-put result key val))
            ;; Cover-file existence check (WARN only; key still emitted above).
            (when (eq key :cover_file)
              (let* ((static-dir (a3madkour-pub-library--site-static-dir-of file))
                     (cover-path (and static-dir
                                      (expand-file-name (concat "library/covers/" raw)
                                                        static-dir))))
                (when (and cover-path (not (file-exists-p cover-path)))
                  (a3madkour-pub-library--warn file slug
                                               "cover file missing at %s" cover-path))))))))
    result))
```

Then integrate into `--normalize-item` (append before `row-plist` is returned):

```elisp
;; Extras: per-medium drawer mapping + cover-file existence check.
(let ((extras (a3madkour-pub-library--collect-extras headline media-type file slug)))
  (when extras
    (setq row-plist (plist-put row-plist :extras extras))))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Commit.**

```bash
git commit -m "feat(b-2): library --normalize-item extras + cover-file check

Per-medium drawer mapping table (book/album/track/game/film/series).
Cross-medium drawer properties silently dropped (linter is the gate).
Cover-file existence WARN; key still emitted so the linter catches it."
```

---

## Task 9: `--render-library-yaml` — deterministic YAML output

**Spec §6 step 6:** Source-file-order rows; alphabetical keys within each row; comment header; matches `data/<medium>.yaml` shape PyYAML can load.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-library--render-yaml-shape ()
  "Renders a yaml file PyYAML can parse, matching existing fixture shape."
  (let* ((rows (list (list :slug "abc"
                           :title "Abc Title"
                           :creator "Author A"
                           :year 2024
                           :media_type "book"
                           :status "reading"
                           :last_modified "2026-05-01"
                           :tags '("alpha" "beta"))
                     (list :slug "def"
                           :title "Def Title"
                           :creator "Author B"
                           :year 2023
                           :media_type "book"
                           :status "finished"
                           :last_modified "2026-04-15"
                           :finished "2026-04-14"
                           :tags '())))
         (out (a3madkour-pub-library--render-library-yaml
               rows "library-reading.org")))
    ;; Header comment present + items: top-level key.
    (should (string-match-p "# Generated by a3madkour-publish-library" out))
    (should (string-match-p "^items:" out))
    ;; Source-file-order (abc before def) and alphabetical within row.
    (let ((abc-pos (string-match-p "slug: abc" out))
          (def-pos (string-match-p "slug: def" out)))
      (should (and abc-pos def-pos (< abc-pos def-pos))))
    ;; Dates emitted unquoted (PyYAML loads as datetime.date).
    (should (string-match-p "last_modified: 2026-05-01" out))
    (should-not (string-match-p "last_modified: \"" out))
    ;; Tags inline array.
    (should (string-match-p "tags: \\[alpha, beta\\]" out))
    ;; Empty-tag row renders as empty inline array.
    (should (string-match-p "tags: \\[\\]" out))))

(ert-deftest a3madkour-pub-library--render-yaml-extras-nested ()
  "Extras render as a nested map."
  (let* ((rows (list (list :slug "x" :title "X" :creator "y" :year 2024
                           :media_type "game" :status "playing"
                           :last_modified "2026-05-01"
                           :tags '("puzzle")
                           :extras (list :igdb_id 12345
                                         :hours_played 22
                                         :platform "PC"))))
         (out (a3madkour-pub-library--render-library-yaml rows "library-playing.org")))
    (should (string-match-p "extras:" out))
    (should (string-match-p "  igdb_id: 12345" out))
    (should (string-match-p "  hours_played: 22" out))
    (should (string-match-p \"  platform: PC\" out))))

(ert-deftest a3madkour-pub-library--render-yaml-deterministic ()
  "Same input produces byte-identical output across calls."
  (let* ((rows (list (list :slug "x" :title "X" :creator "y" :year 2024
                           :media_type "book" :status "queued"
                           :last_modified "2026-05-01" :tags '("a")))))
    (should (string= (a3madkour-pub-library--render-library-yaml rows "x.org")
                     (a3madkour-pub-library--render-library-yaml rows "x.org")))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.**

```elisp
(defconst a3madkour-pub-library--yaml-key-order
  '(:slug :title :creator :year :media_type :status
    :started :finished :last_modified :note_slug :canonical_url
    :spoiler_level :cite_key :preview :tags :extras)
  "Deterministic key order within each yaml row.
Matches the shape of existing fixtures under data/*.yaml.")

(defun a3madkour-pub-library--render-scalar (val)
  "Render a scalar VAL for inclusion in YAML."
  (cond
   ((null val) "null")
   ((eq val t) "true")
   ((numberp val) (number-to-string val))
   ((stringp val)
    (cond
     ;; YYYY-MM-DD: emit unquoted so PyYAML loads as datetime.date.
     ((string-match-p "^[0-9]\\{4\\}-[0-9]\\{2\\}-[0-9]\\{2\\}$" val) val)
     ;; URLs and quoted text — wrap in double quotes.
     ((string-prefix-p "http" val) (format "\"%s\"" val))
     ;; Plain strings: only quote if they contain `:' or other YAML-sensitive chars.
     ((string-match-p "[:#]" val) (format "\"%s\"" val))
     (t val)))
   (t (format "%S" val))))

(defun a3madkour-pub-library--render-tags (tags)
  "Render a list of tag strings as a YAML flow-sequence."
  (concat "[" (mapconcat #'identity tags ", ") "]"))

(defun a3madkour-pub-library--render-extras (extras indent)
  "Render an EXTRAS plist as a nested YAML block at INDENT (a string)."
  (let ((lines '())
        (keys (seq-filter #'keywordp extras)))
    ;; Render in plist-iteration order (matches insertion order from
    ;; the per-medium extras table — already deterministic).
    (cl-loop for (k v) on extras by #'cddr
             for name = (substring (symbol-name k) 1)
             do (push (format "%s%s: %s" indent name
                              (a3madkour-pub-library--render-scalar v))
                      lines))
    (mapconcat #'identity (nreverse lines) "\n")))

(defun a3madkour-pub-library--render-row (row)
  "Render one ROW plist as a YAML list item ('  - key: value' style)."
  (let ((lines '())
        (first t))
    (dolist (key a3madkour-pub-library--yaml-key-order)
      (when (plist-member row key)
        (let* ((val (plist-get row key))
               (name (substring (symbol-name key) 1))
               (prefix (if first "  - " "    "))
               (line
                (cond
                 ((eq key :tags)
                  (format "%s%s: %s" prefix name
                          (a3madkour-pub-library--render-tags val)))
                 ((eq key :extras)
                  (format "%s%s:\n%s" prefix name
                          (a3madkour-pub-library--render-extras val "      ")))
                 (t
                  (format "%s%s: %s" prefix name
                          (a3madkour-pub-library--render-scalar val))))))
          (push line lines)
          (setq first nil))))
    (mapconcat #'identity (nreverse lines) "\n")))

(defun a3madkour-pub-library--render-library-yaml (rows source-file)
  "Render ROWS (a list of plists) into a complete YAML document.
SOURCE-FILE is recorded in the comment header for provenance."
  (concat
   (format
    "# Generated by a3madkour-publish-library from %s.\n# Manual edits will be overwritten on next publish-living run.\nitems:\n"
    (file-name-nondirectory source-file))
   (mapconcat #'a3madkour-pub-library--render-row rows "\n")
   "\n"))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: PyYAML round-trip smoke** — manually verify a sample renders into something Python can load.

```bash
emacs --batch -L . -l a3madkour-publish-library --eval "
(let ((rows (list (list :slug \"x\" :title \"X\" :creator \"y\" :year 2024
                        :media_type \"book\" :status \"queued\"
                        :last_modified \"2026-05-01\" :tags '(\"a\")))))
  (princ (a3madkour-pub-library--render-library-yaml rows \"x.org\")))" \
  > /tmp/sample.yaml

python3 -c "
import yaml
print(yaml.safe_load(open('/tmp/sample.yaml').read()))
"
```

Expected: Python prints a dict with `items: [...]` where `last_modified` is a `datetime.date` object (not a string).

- [ ] **Step 6: Commit.**

```bash
git commit -m "feat(b-2): library --render-library-yaml deterministic output

Source-file-order rows; deterministic key order within row; comment
header; dates unquoted (PyYAML datetime.date round-trip); tags inline;
extras nested. Idempotent — same input → byte-identical output."
```

---

## Task 10: `publish-library-file` end-to-end

**Spec §6:** Walk top-level headings → normalize each → dedup slugs → render yaml → write-if-different. No `record-publish`.

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-library-test.el`

- [ ] **Step 1: Write the failing end-to-end test.**

```elisp
(ert-deftest a3madkour-pub-library--publish-library-file-end-to-end ()
  "publish-library-file walks headings + writes data/<medium>.yaml."
  (let* ((notes-dir (make-temp-file "a3-pub-libnotes-" t))
         (site-dir  (make-temp-file "a3-pub-libsite-" t))
         (src       (expand-file-name "library-reading.org" notes-dir)))
    (unwind-protect
        (progn
          (make-directory (expand-file-name "data" site-dir))
          (with-temp-file src
            (insert "#+HUGO_PUBLISH: t\n"
                    "#+HUGO_SECTION: library-reading\n\n"
                    "* Pride and Prejudice :classics:romance:\n"
                    ":PROPERTIES:\n"
                    ":CREATOR: Jane Austen\n"
                    ":YEAR: 1813\n"
                    ":STATUS: finished\n"
                    ":FINISHED: 2024-12-15\n"
                    ":LAST_MODIFIED: 2024-12-16\n"
                    ":END:\n\n"
                    "* Lord Jim :classics:\n"
                    ":PROPERTIES:\n"
                    ":CREATOR: Joseph Conrad\n"
                    ":YEAR: 1900\n"
                    ":STATUS: reading\n"
                    ":LAST_MODIFIED: 2025-04-01\n"
                    ":END:\n"))
          (let ((a3madkour-pub/site-data-dir (expand-file-name "data/" site-dir)))
            (a3madkour-pub-library/publish-library-file src))
          (let ((out (expand-file-name "data/reading.yaml" site-dir)))
            (should (file-exists-p out))
            (with-temp-buffer
              (insert-file-contents out)
              (should (string-match-p "slug: pride-and-prejudice" (buffer-string)))
              (should (string-match-p "slug: lord-jim" (buffer-string)))
              (should (string-match-p "title: Pride and Prejudice" (buffer-string)))
              (should (string-match-p "tags: \\[classics, romance\\]" (buffer-string)))
              ;; Source-file-order: P comes before L.
              (let ((p-pos (string-match-p "slug: pride-and-prejudice" (buffer-string)))
                    (l-pos (string-match-p "slug: lord-jim" (buffer-string))))
                (should (< p-pos l-pos))))))
      (delete-directory notes-dir t)
      (delete-directory site-dir t))))

(ert-deftest a3madkour-pub-library--publish-library-file-slug-collision ()
  "Slug collision within file → WARN, skip second occurrence."
  (let* ((notes-dir (make-temp-file "a3-pub-libnotes-" t))
         (site-dir  (make-temp-file "a3-pub-libsite-" t))
         (src       (expand-file-name "library-reading.org" notes-dir))
         (warnings '()))
    (unwind-protect
        (progn
          (make-directory (expand-file-name "data" site-dir))
          (with-temp-file src
            (insert "#+HUGO_PUBLISH: t\n#+HUGO_SECTION: library-reading\n\n"
                    "* Same Title\n:PROPERTIES:\n:CREATOR: x\n:YEAR: 2024\n:STATUS: queued\n:END:\n"
                    "* Same Title\n:PROPERTIES:\n:CREATOR: y\n:YEAR: 2025\n:STATUS: queued\n:END:\n"))
          (cl-letf (((symbol-function 'message)
                     (lambda (fmt &rest args)
                       (push (apply #'format fmt args) warnings))))
            (let ((a3madkour-pub/site-data-dir (expand-file-name "data/" site-dir)))
              (a3madkour-pub-library/publish-library-file src)))
          ;; Yaml only has one row.
          (let ((content (with-temp-buffer
                           (insert-file-contents (expand-file-name "data/reading.yaml" site-dir))
                           (buffer-string))))
            (should (= 1 (length (split-string content "  - slug:" t))))
            (should (seq-some (lambda (m) (string-match-p "slug collision" m)) warnings))))
      (delete-directory notes-dir t)
      (delete-directory site-dir t))))

(ert-deftest a3madkour-pub-library--publish-library-file-idempotent ()
  "Second publish run on unchanged source → file mtime unchanged."
  (let* ((notes-dir (make-temp-file "a3-pub-libnotes-" t))
         (site-dir  (make-temp-file "a3-pub-libsite-" t))
         (src       (expand-file-name "library-reading.org" notes-dir)))
    (unwind-protect
        (progn
          (make-directory (expand-file-name "data" site-dir))
          (with-temp-file src
            (insert "#+HUGO_PUBLISH: t\n#+HUGO_SECTION: library-reading\n\n"
                    "* Item\n:PROPERTIES:\n:CREATOR: x\n:YEAR: 2024\n:STATUS: queued\n"
                    ":LAST_MODIFIED: 2025-01-01\n:END:\n"))
          (let ((a3madkour-pub/site-data-dir (expand-file-name "data/" site-dir)))
            (a3madkour-pub-library/publish-library-file src)
            (let* ((out (expand-file-name "data/reading.yaml" site-dir))
                   (mtime1 (file-attribute-modification-time
                            (file-attributes out))))
              (sleep-for 1.1)
              (a3madkour-pub-library/publish-library-file src)
              (let ((mtime2 (file-attribute-modification-time
                             (file-attributes out))))
                (should (equal mtime1 mtime2))))))
      (delete-directory notes-dir t)
      (delete-directory site-dir t))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Implement.** Add helpers + replace `publish-library-file`:

```elisp
(defun a3madkour-pub-library--write-if-different (path content)
  "Write CONTENT to PATH only if it differs from existing on-disk content."
  (let ((existing (when (file-exists-p path)
                    (with-temp-buffer
                      (insert-file-contents path)
                      (buffer-string)))))
    (unless (string= existing content)
      (make-directory (file-name-directory path) t)
      (with-temp-file path (insert content))
      t)))

(defun a3madkour-pub-library--yaml-path (file cfg)
  "Compute the absolute output yaml path for SOURCE-FILE given CFG."
  (ignore file)
  (let ((data-dir (and (boundp 'a3madkour-pub/site-data-dir)
                       a3madkour-pub/site-data-dir)))
    (unless data-dir
      (error "a3madkour-pub-library: a3madkour-pub/site-data-dir is nil"))
    (expand-file-name (nth 0 cfg) data-dir)))

(defun a3madkour-pub-library/publish-library-file (file)
  "Publish a single library FILE to data/<medium>.yaml.

Walks top-level headings via `org-element-parse-buffer', normalizes each
via `--normalize-item', deduplicates slugs (WARN on collision; skip
second), renders the YAML, writes if different.  Library items do NOT
call `record-publish' (URL-less; per spec §6 step 8)."
  (let* ((section (a3madkour-pub/note-section file))
         (cfg (a3madkour-pub-library--config-for section))
         (out-path (a3madkour-pub-library--yaml-path file cfg))
         (ast (with-temp-buffer
                (insert-file-contents file)
                (org-mode)
                (org-element-parse-buffer)))
         (seen-slugs (make-hash-table :test 'equal))
         (rows '()))
    (org-element-map ast 'headline
      (lambda (hl)
        (when (= 1 (org-element-property :level hl))
          (let ((row (a3madkour-pub-library--normalize-item hl section cfg file)))
            (when row
              (let ((slug (plist-get row :slug)))
                (cond
                 ((gethash slug seen-slugs)
                  (a3madkour-pub-library--warn
                   file slug "slug collision; skipping second occurrence"))
                 (t
                  (puthash slug t seen-slugs)
                  (push row rows)))))))))
    (let ((yaml (a3madkour-pub-library--render-library-yaml
                 (nreverse rows) file)))
      (a3madkour-pub-library--write-if-different out-path yaml))))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Run full ert suite.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

- [ ] **Step 6: Commit.**

```bash
git commit -m "feat(b-2): publish-library-file end-to-end

Walk top-level headings → normalize → dedup → render → write-if-different.
No record-publish (library items are URL-less per spec §6 step 8)."
```

---

## Task 11: Register all 4 library handlers in `a3madkour-pub-living--handlers`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el`

- [ ] **Step 1: Write failing tests.**

```elisp
(ert-deftest a3madkour-pub-living--library-handlers-registered ()
  "All 4 library sections register publish-library-file."
  (require 'a3madkour-publish-library)
  (dolist (section '(library-reading library-listening library-playing library-watching))
    (should (eq (cdr (assq section a3madkour-pub-living--handlers))
                'a3madkour-pub-library/publish-library-file))))
```

- [ ] **Step 2: Run; expect failure.**

- [ ] **Step 3: Register via `with-eval-after-load` block.** Append to `a3madkour-publish-living.el`:

```elisp
;; B.2: library handler registration (one entry per library-<medium> section).
(with-eval-after-load 'a3madkour-publish-library
  (dolist (section '(library-reading library-listening library-playing library-watching))
    (add-to-list 'a3madkour-pub-living--handlers
                 (cons section 'a3madkour-pub-library/publish-library-file))))
```

- [ ] **Step 4: Run; expect green.**

- [ ] **Step 5: Full-suite + wrapper smoke.**

```bash
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3

cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
```

Expected: ≈303 tests pass (276 + ~27 new from Tasks 1-11); `--publish-living` exits 0 (no library `.org` files in `~/org/notes/` yet OR existing garden flow continues to work).

- [ ] **Step 6: Commit.**

```bash
git commit -m "feat(b-2): register 4 library handlers in living--handlers

with-eval-after-load form adds one entry per library-<medium> section
all pointing at publish-library-file (per spec §4 dispatch model)."
```

---

## Task 12: Python integration fixture — `test_library_publish_once`

**Why:** Mirror B.1's `TestGardenPublishLiving` pattern; first of 5 new B.2 fixtures.

**Files:**
- Modify: `tools/test_publish_integration.py` (site repo).

- [ ] **Step 1: Read existing helper signatures to reuse.**

```bash
grep -nE "^def _|^class " tools/test_publish_integration.py | head -20
```

Expected: `_publish_living`, `_write_garden_source`, `TestGardenPublishLiving`. The library fixtures will reuse `_publish_living` (it's section-agnostic) and add a new `_write_library_source` helper.

- [ ] **Step 2: Add `_write_library_source` helper near `_write_garden_source`.**

```python
def _write_library_source(
    path: Path, section: str, items: list[dict[str, str]]
) -> None:
    """Write a library .org file at PATH with the given SECTION + ITEMS.

    Each item is a dict with keys: title, creator, year, status,
    media_type (optional), tags (optional list), last_modified (optional),
    and any extra drawer properties (uppercase keys go into :PROPERTIES:).
    """
    lines = [
        "#+HUGO_PUBLISH: t",
        f"#+HUGO_SECTION: {section}",
        "",
    ]
    for item in items:
        tags = item.get("tags", [])
        tag_str = ":" + ":".join(tags) + ":" if tags else ""
        lines.append(f"* {item['title']} {tag_str}".rstrip())
        lines.append(":PROPERTIES:")
        for key, val in item.items():
            if key in {"title", "tags"}:
                continue
            lines.append(f":{key.upper()}: {val}")
        lines.append(":END:")
        lines.append("")
    path.write_text("\n".join(lines))
```

- [ ] **Step 3: Add `TestLibraryPublishLiving` class with the first fixture.**

Place it right after `TestGardenPublishLiving`:

```python
class TestLibraryPublishLiving(unittest.TestCase):
    """Integration fixtures for B.2's library handler.

    Each test seeds 1 or more library-<medium>.org source files in a tmp
    notes dir, then runs a3-pub.sh --publish-living against a tmp site
    dir, asserting the expected data/<medium>.yaml shape.
    """

    def setUp(self) -> None:
        self.notes_dir = Path(tempfile.mkdtemp(prefix="a3-pub-libnotes-"))
        self.site_root = Path(tempfile.mkdtemp(prefix="a3-pub-libsite-"))
        (self.site_root / "data").mkdir()
        (self.site_root / "static" / "library" / "covers").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.notes_dir, ignore_errors=True)
        shutil.rmtree(self.site_root, ignore_errors=True)

    @property
    def _site_data_dir(self) -> Path:
        return self.site_root / "data"

    def test_library_publish_once(self) -> None:
        """Single-item publish across all 4 library sections."""
        _write_library_source(
            self.notes_dir / "library-reading.org", "library-reading",
            [{"title": "Pride and Prejudice", "creator": "Jane Austen",
              "year": "1813", "status": "finished",
              "finished": "2024-12-15", "last_modified": "2024-12-16",
              "tags": ["classics"]}],
        )
        _write_library_source(
            self.notes_dir / "library-listening.org", "library-listening",
            [{"title": "Koyaanisqatsi", "creator": "Philip Glass",
              "year": "1983", "status": "listening",
              "last_modified": "2026-05-01", "tags": ["soundtrack"]}],
        )
        _write_library_source(
            self.notes_dir / "library-playing.org", "library-playing",
            [{"title": "Outer Wilds", "creator": "Mobius",
              "year": "2019", "status": "playing",
              "last_modified": "2026-05-01", "tags": ["puzzle"]}],
        )
        _write_library_source(
            self.notes_dir / "library-watching.org", "library-watching",
            [{"title": "Severance S2", "creator": "Apple TV+",
              "year": "2025", "status": "finished", "media_type": "series",
              "last_modified": "2026-04-01", "tags": ["drama"]}],
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        for fname in ("reading.yaml", "listening.yaml",
                      "playing.yaml", "watching.yaml"):
            self.assertTrue(
                (self._site_data_dir / fname).exists(),
                msg=f"{fname} not emitted",
            )
```

- [ ] **Step 4: Run.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
python3 -m unittest tools.test_publish_integration.TestLibraryPublishLiving.test_library_publish_once -v
```

Expected: pass.

- [ ] **Step 5: Commit (site).**

```bash
git add tools/test_publish_integration.py
git commit -m "test(b-2): integration fixture — library publish-once

Seed 1 item per medium across 4 library-*.org source files; assert
all 4 data/<medium>.yaml emitted."
```

---

## Task 13: Python integration fixture — `test_library_publish_idempotent`

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add the fixture inside `TestLibraryPublishLiving`.**

```python
    def test_library_publish_idempotent(self) -> None:
        """Second publish-living run on unchanged source → zero diff."""
        _write_library_source(
            self.notes_dir / "library-reading.org", "library-reading",
            [{"title": "Item", "creator": "x", "year": "2024",
              "status": "queued", "last_modified": "2025-01-01"}],
        )
        proc1 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc1.returncode, 0, msg=proc1.stderr)
        yaml_path = self._site_data_dir / "reading.yaml"
        content1 = yaml_path.read_bytes()
        mtime1 = yaml_path.stat().st_mtime_ns
        time.sleep(1.1)
        proc2 = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        content2 = yaml_path.read_bytes()
        mtime2 = yaml_path.stat().st_mtime_ns
        self.assertEqual(content1, content2)
        self.assertEqual(mtime1, mtime2, msg="file rewritten on idempotent run")
```

Add `import time` at the top of the file if not already imported.

- [ ] **Step 2: Run.**

```bash
python3 -m unittest tools.test_publish_integration.TestLibraryPublishLiving.test_library_publish_idempotent -v
```

Expected: pass.

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-2): integration fixture — library publish idempotent

Second run on unchanged source produces zero file diff (content +
mtime unchanged)."
```

---

## Task 14: Python integration fixture — `test_library_slug_shift`

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add the fixture.**

```python
    def test_library_slug_shift(self) -> None:
        """Changing :SLUG: drawer → old slug row gone, new slug row present."""
        src = self.notes_dir / "library-reading.org"
        _write_library_source(
            src, "library-reading",
            [{"title": "Pride and Prejudice", "slug": "pride",
              "creator": "Jane Austen", "year": "1813",
              "status": "finished", "finished": "2024-12-15",
              "last_modified": "2024-12-16"}],
        )
        _publish_living(self.notes_dir, self._site_data_dir)
        content1 = (self._site_data_dir / "reading.yaml").read_text()
        self.assertIn("slug: pride", content1)
        # Bump the slug.
        _write_library_source(
            src, "library-reading",
            [{"title": "Pride and Prejudice", "slug": "pride-and-prejudice",
              "creator": "Jane Austen", "year": "1813",
              "status": "finished", "finished": "2024-12-15",
              "last_modified": "2024-12-16"}],
        )
        _publish_living(self.notes_dir, self._site_data_dir)
        content2 = (self._site_data_dir / "reading.yaml").read_text()
        self.assertNotIn("slug: pride\n", content2)
        self.assertIn("slug: pride-and-prejudice", content2)
```

- [ ] **Step 2: Run; iterate.**

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-2): integration fixture — library slug shift

Old slug disappears, new slug present in same yaml on next publish."
```

---

## Task 15: Python integration fixture — `test_library_removed_item_unpublish`

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Add the fixture.**

```python
    def test_library_removed_item_unpublish(self) -> None:
        """Deleting a heading from source → row disappears on next publish."""
        src = self.notes_dir / "library-reading.org"
        _write_library_source(
            src, "library-reading",
            [
                {"title": "Item One", "creator": "x", "year": "2024",
                 "status": "queued", "last_modified": "2025-01-01"},
                {"title": "Item Two", "creator": "y", "year": "2024",
                 "status": "queued", "last_modified": "2025-01-01"},
            ],
        )
        _publish_living(self.notes_dir, self._site_data_dir)
        content1 = (self._site_data_dir / "reading.yaml").read_text()
        self.assertIn("slug: item-one", content1)
        self.assertIn("slug: item-two", content1)
        # Remove Item One.
        _write_library_source(
            src, "library-reading",
            [{"title": "Item Two", "creator": "y", "year": "2024",
              "status": "queued", "last_modified": "2025-01-01"}],
        )
        _publish_living(self.notes_dir, self._site_data_dir)
        content2 = (self._site_data_dir / "reading.yaml").read_text()
        self.assertNotIn("slug: item-one", content2)
        self.assertIn("slug: item-two", content2)
```

- [ ] **Step 2: Run; iterate.**

- [ ] **Step 3: Commit.**

```bash
git commit -m "test(b-2): integration fixture — library removed item unpublish

Heading deletion → row disappears via full-replace YAML write."
```

---

## Task 16: Python integration fixture — linter parity across all 3 library linters

**Why:** Per spec §11 / parent §11, B-emitted yaml must pass the existing site linters. This fixture is the CI gate guarantee.

**Files:**
- Modify: `tools/test_publish_integration.py`

- [ ] **Step 1: Read the 3 linter signatures.**

```bash
grep -nE "^def run|^def main|^if __name__" tools/check_library_fixtures.py tools/check_library_links.py tools/check_library_covers.py
```

If they have a `run()` entry point (existing pattern), reuse `_import_linter`. If they only have `main()` / `__main__` invocation, call them as subprocesses against a `--data-dir` or `chdir` into a fake site.

- [ ] **Step 2: Add the fixture.**

```python
    def test_library_emits_lint_clean_output(self) -> None:
        """B-emitted yaml passes check_library_fixtures + _links + _covers."""
        # Seed minimal but linter-clean items across all 4 media.
        _write_library_source(
            self.notes_dir / "library-reading.org", "library-reading",
            [{"title": "Item", "creator": "x", "year": "2024",
              "status": "queued", "last_modified": "2025-01-01"}],
        )
        _write_library_source(
            self.notes_dir / "library-listening.org", "library-listening",
            [{"title": "Album", "creator": "y", "year": "2024",
              "status": "listening", "last_modified": "2025-01-01"}],
        )
        _write_library_source(
            self.notes_dir / "library-playing.org", "library-playing",
            [{"title": "Game", "creator": "z", "year": "2024",
              "status": "playing", "last_modified": "2025-01-01"}],
        )
        _write_library_source(
            self.notes_dir / "library-watching.org", "library-watching",
            [{"title": "Film", "creator": "w", "year": "2024",
              "status": "finished", "finished": "2024-12-01",
              "last_modified": "2025-01-01"}],
        )
        # Library linters also need data/library-shelves.yaml to exist
        # (hand-authored; not touched by publisher).
        (self._site_data_dir / "library-shelves.yaml").write_text(
            "shelves: []\n"
        )
        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        # Invoke each linter with cwd = site_root so they find data/.
        for linter in ("check_library_fixtures",
                       "check_library_links",
                       "check_library_covers"):
            mod = _import_linter(linter)
            rc = mod.run(self.site_root)
            self.assertEqual(rc, 0, msg=f"{linter}.run() failed")
```

> **Note:** if any of the three linters don't accept a `Path` argument to `run()`, the fixture must `chdir` into `site_root` and call `run()` with no args. Read each linter's `run()` signature before writing this and adjust accordingly.

- [ ] **Step 3: Run; iterate on linter signatures.**

- [ ] **Step 4: Run the full integration suite to confirm no regression.**

```bash
python3 -m unittest tools.test_publish_integration -v 2>&1 | tail -10
```

Expected: 19 tests pass (14 baseline + 5 new B.2 fixtures).

- [ ] **Step 5: Commit.**

```bash
git add tools/test_publish_integration.py
git commit -m "test(b-2): integration fixture — library yaml passes 3 site linters

B-emitted output passes check_library_fixtures + check_library_links +
check_library_covers against tmp site dir."
```

---

## Task 17 (USER-DRIVEN): Real-corpus spot-check + fixture handover commit + memory update

**Why:** Per spec §11 transition strategy + [[verify-before-merge]] feedback, this slice must do a real `~/org/notes/library-*.org` publish-living run with the author confirming the result before the fixture-replace commit lands.

**Files:**
- The author's real library source files in `~/org/notes/library-*.org` (may not yet exist; spot-check covers seeding).
- This repo's `data/{reading,listening,playing,watching}.yaml` (fixture rows replaced).
- `CLAUDE.md` (status pointer update).
- `.claude/memory/MEMORY.md` + `.claude/memory/project_b2_complete.md` (new) + `.claude/memory/project_next_slice.md` (update to B.3).

- [ ] **Step 1: Run the full ert suite locally.**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp
emacs --batch -L . \
  $(for f in a3madkour-publish*.el; do printf -- '-l %s ' "${f%.el}"; done) \
  -f ert-run-tests-batch-and-exit 2>&1 | tail -3
```

Expected: `Ran ~303 tests, ~303 as expected, 0 unexpected.` (271 baseline + ~32 new across Tasks 1–11.)

- [ ] **Step 2: Run `tools/ci-local.sh`** against the site repo (per [[always-run-ci-locally]]) to establish a green baseline.

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
tools/ci-local.sh
```

Expected: all linters pass; hugo --minify succeeds; pagefind + smoke + page-weight + LHCI all green.

- [ ] **Step 3: Author confirms or seeds real library source files.**

```bash
ls ~/org/notes/library-*.org 2>/dev/null
```

If empty, author writes minimal real seeds (one of each medium) annotated with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: library-<medium>`. The publisher does NOT auto-create source files.

- [ ] **Step 4: Run the real publish.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living
echo "exit=$?"
```

Expected: exit 0; `data/{reading,listening,playing,watching}.yaml` rewritten with real items; fixture rows replaced.

- [ ] **Step 5: Re-run `tools/ci-local.sh`** against the new B-emitted yaml.

Expected: all 50+ pre-build linters pass; `check_library_fixtures.py` + `check_library_links.py` + `check_library_covers.py` all green.

- [ ] **Step 6: Author starts `hugo server --buildDrafts`, visits `/library/`, `/library/reading/`, `/library/listening/`, `/library/playing/`, `/library/watching/`. Verifies:**
- Catalogue grid renders with real items.
- Themed shelves render correctly (note that shelves come from hand-authored `data/library-shelves.yaml`, unchanged by this slice).
- Item tiles show titles, creators, years.
- Cover images load if `:COVER_FILE:` was set + the static file committed.
- Tags appear as filter chips (consistent with existing fixture behavior).

- [ ] **Step 7: If anything looks off,** file a focused fix (don't expand B.2 scope; defer to a B.2.x follow-up).

- [ ] **Step 8: Update `CLAUDE.md` status pointer.**

Locate the "Project status (as of 2026-MM-DD)" line and the B sub-project bullet under "Not started, in phase order". Update to mark B.2 shipped:

```
... **All five [A] shipped ... B.0 (shared publisher infrastructure) shipped 2026-05-25; B.1 (garden handler) shipped 2026-05-25; B.1.1 (pre-export id-link rewriter) shipped 2026-05-26 in dotfiles; **B.2 (library handler) shipped 2026-05-29** — closes per-medium YAML publisher with editorial-tag filter retroactively applied to garden. Next: B.3 (research). See memory/project_b2_complete.md.
```

- [ ] **Step 9: Commit the site changes.**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add data/reading.yaml data/listening.yaml data/playing.yaml data/watching.yaml \
        CLAUDE.md
git commit -m "feat(b-2): library handler ships — real-content handover

Replaces library fixture rows with B-emitted content from
~/org/notes/library-*.org. Second slice to emit real Hugo data from
the elisp publisher (after B.1 garden). Retroactively closes:
- B.1 follow-up #2 (last_modified git-mtime fallback for garden)
- B.1.1 follow-up #6 (editorial-tag filter strips TODO/NOEXPORT from garden tags)"
```

- [ ] **Step 10: Update memory.**

Create `.claude/memory/project_b2_complete.md` summarizing what shipped, what tests landed, dotfiles + site commit SHAs, known issues / B.3 follow-ups; add the index line to `.claude/memory/MEMORY.md`. Update `.claude/memory/project_next_slice.md` to point at B.3 (research themes + questions).

```bash
git add .claude/memory/
git commit -m "docs(memory): B.2 library handler shipped — next slice B.3"
```

- [ ] **Step 11: Push.**

```bash
git push origin master
```

Confirm with author before pushing. Author may want to batch with the accumulated unpushed dotfiles + site commits (per [[next-slice]] §"Push decision").

---

## Self-Review

**Spec coverage check (against `2026-05-29-phase-3-b-2-library-handler-design.md`):**

- §3 Per-medium config table: covered by Task 3 (embedded in module scaffold) and Task 5's `--config-for` use.
- §4 Architecture (single function, four registrations): covered by Tasks 3 + 11.
- §5 Required fields: covered by Tasks 4 (slug helper) + 5 (title/slug/creator/year/media_type/status) + 6 (last_modified + drawer pass-throughs) + 7 (tags filter) + 8 (extras + cover-file).
- §5 Optional fields: covered by Task 6.
- §5 Extras mapping: covered by Task 8.
- §5 Cover-file existence check: covered by Task 8.
- §5 Editorial-tag filter: covered by Task 2 (helper + retroactive garden) + Task 7 (library wiring).
- §6 Handler flow (parse → walk → normalize → dedup → render → write-if-different): covered by Task 10.
- §7 Error handling (WARN-don't-fail): covered by per-task validation tests (5/7/8/10).
- §8 Idempotency: covered by Task 10 ert test + Task 13 integration fixture.
- §8 Transition (full-replace YAML): covered by Task 17 spot-check + the integration test (Task 16) that gates linter parity.
- §10 Sub-helpers all ert-tested: covered by Tasks 1 (git-mtime) + 2 (filter-tags) + 4 (slug) + 5-8 (normalize-item branches) + 9 (render-yaml) + 10 (publish-library-file).
- §11 Slice positioning + spot-check expectation: covered by Task 17.
- §12 Open follow-ups: documented in spec; no plan tasks needed (B.2.x territory).

**Placeholder scan:** I checked every step for "TBD", "appropriate error handling", "similar to Task N", or undefined symbols. Two notes:
1. Task 16 says "if any of the three linters don't accept a Path argument to run(), the fixture must chdir + call run() with no args. Read each linter's run() signature before writing this and adjust accordingly." — this is honest signature-checking advice, not a placeholder; the linter call shape isn't deterministic without grepping each module.
2. Task 17 Step 8's status pointer update references "(as of 2026-MM-DD)" — the implementer fills in the actual date at commit time (2026-05-29 or later). Standard pattern from B.1 plan Task 17.

**Type consistency:** `a3madkour-pub-library/publish-library-file` canonical across Tasks 3 / 5–10 / 11 / 17. `--normalize-item` signature `(headline section cfg file)` consistent across Tasks 5/6/7/8. Plist keys (`:slug`, `:title`, `:creator`, etc.) consistent across normalize + render + tests. Config table tuple shape `(yaml-file default-mt allowed-mt allowed-status)` consistent. ✓

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-29-phase-3-b-2-library-handler.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review (spec + quality) between tasks. Matches how B.0 / B.1 / B.1.1 were executed.

**2. Inline Execution** — execute tasks in this session via `superpowers:executing-plans`, batch execution with checkpoints for your review.

Which approach?
