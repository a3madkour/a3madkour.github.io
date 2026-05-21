# Phase 3 A.1.0 — Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Session policy:** the controlling author has set a no-commit-this-session policy. Commit steps below are reminders for the human author to perform during/after review — do NOT git-commit autonomously. Stage files for the author with `git add` but stop short of `git commit`.

**Goal:** Bootstrap the elisp publishing library at `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el` and its ert test runner. Establish the dev loop (write test → run test → see green) so all subsequent A.1.{a,b,c,d} plans can rely on it.

**Architecture:** A single namespaced elisp library (`a3madkour-publish.el`) using `lexical-binding: t` and a `a3madkour-pub/` function prefix. Tests live in sibling `-test.el` files using built-in `ert`. A shell wrapper invokes the runner via `emacs --batch` so tests work without an interactive emacs session.

**Tech Stack:** Emacs 30.2, ert (built-in), bash (for the runner wrapper). No external elisp dependencies in this plan.

**Parent spec:** `docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md` §10, §11.

---

## File Structure

**Created (dotfiles repo: `~/dotfiles/emacs-configs/custom/lisp/`):**
- `a3madkour-publish.el` — the library shell. Headers + `provide` only; no logic yet. Sub-projects A.1.{a..d} fill it in.
- `a3madkour-publish-test.el` — ert test file shell. One dummy "library loads" test; suite expands across the next 4 plans.
- `run-tests.sh` — shell wrapper that invokes `emacs --batch` with the right `-L` and `-l` flags.

**Created (site repo: `docs/`):**
- This plan file (already present once you're reading this): `docs/superpowers/plans/2026-05-20-phase-3-a1-0-bootstrap.md`

**No site-repo source/data files touched** in this plan. (A.1.c will add `data/url-history.yaml`; A.1.c also adds `tools/check_org_assets.py`. A.1.0 is purely elisp scaffolding.)

---

### Task 1: Create the lisp directory + verify path

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/` (directory)

- [ ] **Step 1: Confirm path layout**

Run: `ls -ld ~/dotfiles/emacs-configs/custom/ && readlink ~/emacs-configs`
Expected: directory listing for `custom/` AND `dotfiles/emacs-configs` printed (the symlink target).

- [ ] **Step 2: Create the `lisp/` subdirectory**

Run: `mkdir -p ~/dotfiles/emacs-configs/custom/lisp`
Expected: no output. Directory now exists.

- [ ] **Step 3: Verify**

Run: `ls -la ~/dotfiles/emacs-configs/custom/lisp/`
Expected: empty directory listing (`. ..` only).

---

### Task 2: Create the library shell `a3madkour-publish.el`

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`

- [ ] **Step 1: Write the library file**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el`

Content (write the entire file):

```elisp
;;; a3madkour-publish.el --- Org → Hugo publish pipeline (sub-project A) -*- lexical-binding: t; -*-

;; Author: Abdelrahman Madkour <a3madkour@gmail.com>
;; Version: 0.1.0-bootstrap
;; Package-Requires: ((emacs "30.2"))
;; Keywords: org, hugo, publish

;;; Commentary:

;; Phase 3 sub-project A: access control + link semantics for the
;; org → Hugo publish pipeline driving https://a3madkour.github.io/.
;;
;; This is the bootstrap shell.  A.1.{a..d} implement keyword parsing,
;; slug derivation, URL-history, link rewriting, asset handling, and
;; the unpublish flow.  Consumed by sub-project B (the per-section
;; publisher) via the function surface documented in the design spec at
;; docs/superpowers/specs/2026-05-20-phase-3-access-control-link-semantics-design.md
;; (in the site repo).

;;; Code:

(defgroup a3madkour-pub nil
  "Org → Hugo publish pipeline (sub-project A: access control + link semantics)."
  :group 'org
  :prefix "a3madkour-pub/")

(defconst a3madkour-pub/version "0.1.0-bootstrap"
  "Current version of the publish library.")

(provide 'a3madkour-publish)

;;; a3madkour-publish.el ends here
```

- [ ] **Step 2: Verify the file parses as valid elisp**

Run: `emacs --batch --eval "(progn (find-file \"~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish.el\") (check-parens))"`
Expected: no output (`check-parens` is silent on success; would error if parens unbalanced).

- [ ] **Step 3: Verify the file can be loaded**

Run: `emacs --batch -L ~/dotfiles/emacs-configs/custom/lisp -l a3madkour-publish --eval "(message \"loaded: %s\" a3madkour-pub/version)"`
Expected output line: `loaded: 0.1.0-bootstrap`

---

### Task 3: Create the test file shell `a3madkour-publish-test.el`

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

- [ ] **Step 1: Write the test file**

Path: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el`

Content (write the entire file):

```elisp
;;; a3madkour-publish-test.el --- Tests for a3madkour-publish -*- lexical-binding: t; -*-

;;; Commentary:

;; ert tests for a3madkour-publish.  Run via the `run-tests.sh' wrapper
;; in this directory, or directly:
;;
;;   emacs --batch -L . -l ert -l a3madkour-publish-test.el \
;;     -f ert-run-tests-batch-and-exit

;;; Code:

(require 'ert)
(require 'a3madkour-publish)

(ert-deftest a3madkour-pub-test/library-loads ()
  "Smoke test: the library loads and exposes its version constant."
  (should (stringp a3madkour-pub/version))
  (should (string-match-p "^[0-9]+\\.[0-9]+\\." a3madkour-pub/version)))

(provide 'a3madkour-publish-test)

;;; a3madkour-publish-test.el ends here
```

- [ ] **Step 2: Verify the test file parses**

Run: `emacs --batch --eval "(progn (find-file \"~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el\") (check-parens))"`
Expected: no output.

---

### Task 4: Run the dummy test to verify the dev loop works

- [ ] **Step 1: Invoke ert in batch mode**

Run:
```bash
emacs --batch \
  -L ~/dotfiles/emacs-configs/custom/lisp \
  -l ert \
  -l ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-test.el \
  -f ert-run-tests-batch-and-exit
```

Expected output (final lines):
```
Running 1 tests (…, selector ‘t’)
   passed  1/1  a3madkour-pub-test/library-loads (… sec)

Ran 1 tests, 1 results as expected, 0 unexpected (…)
```

Exit code: `0`. Verify with: `echo $?` → `0`.

- [ ] **Step 2: Sanity-check the test ACTUALLY runs (not silently skipped)**

Edit `a3madkour-publish-test.el` temporarily, change the smoke test to ASSERT FAILURE:

```elisp
(ert-deftest a3madkour-pub-test/library-loads ()
  "Smoke test (temporarily inverted to confirm runner detects failures)."
  (should nil))   ;; ← TEMPORARY
```

Run the same command. Expected: `1 unexpected` failure reported, exit code `1`.

Then REVERT the change to the original assertion:
```elisp
(should (stringp a3madkour-pub/version))
(should (string-match-p "^[0-9]+\\.[0-9]+\\." a3madkour-pub/version))
```

Re-run the test. Expected: `1/1 passed`, exit code `0`.

(This step proves the runner is wired correctly and would catch regressions — not just silently passing because nothing ran.)

---

### Task 5: Create the `run-tests.sh` wrapper

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`

- [ ] **Step 1: Write the wrapper**

Path: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`

Content:

```bash
#!/usr/bin/env bash
# Run all ert tests for the a3madkour-publish library.
# Picks up every *-test.el in this directory.
#
# Usage:
#   ./run-tests.sh              # run all tests
#   ./run-tests.sh -v           # verbose (ert prints per-assertion notes)
set -euo pipefail

LISP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

load_args=()
for test_file in "$LISP_DIR"/*-test.el; do
  load_args+=("-l" "$test_file")
done

if [ ${#load_args[@]} -eq 0 ]; then
  echo "no *-test.el files found in $LISP_DIR" >&2
  exit 2
fi

exec emacs --batch \
  -L "$LISP_DIR" \
  -l ert \
  "${load_args[@]}" \
  -f ert-run-tests-batch-and-exit \
  "$@"
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x ~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`

- [ ] **Step 3: Verify the wrapper picks up the test file and runs green**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`
Expected: same `1/1 passed` output as Task 4 Step 1.
Verify exit code: `echo $?` → `0`.

- [ ] **Step 4: Verify the wrapper returns non-zero on failure**

Temporarily break the test again (as in Task 4 Step 2: `(should nil)`).
Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh; echo "exit=$?"`
Expected: ert reports `1 unexpected`; trailing line `exit=1`.

Revert the test. Re-run the wrapper. Expected: `1/1 passed`; exit `0`.

---

### Task 6: USER VERIFICATION CHECKPOINT

This task is for the human author — do not skip even if every prior step passed. Per the spec §11 testing strategy, each stage of A.1 has a manual-verification checkpoint.

- [ ] **Step 1: Author runs the test wrapper in their normal shell**

The author runs `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh` themselves (not via an agent shell) and confirms:
- Exit code is `0`
- Output shows `1/1 passed` with the test name `a3madkour-pub-test/library-loads`
- No deprecation warnings, no "library not found" errors

If anything looks off (warnings about emacs version, missing load-path entries, unfamiliar errors), pause and surface to the controlling agent. Do NOT proceed to commit until the author signs off.

- [ ] **Step 2: Author confirms readiness to proceed to A.1.a**

The author affirms in the session that the bootstrap is sound and the next plan (A.1.a — foundations: keywords, slug, URL-history) can begin. Document the sign-off in the conversation.

---

### Task 7: Stage files + author commits

Per session policy, the agent stages but does NOT commit. The author reviews `git status` and runs `git commit` themselves.

- [ ] **Step 1: Stage the dotfiles changes**

In the dotfiles repo (`~/dotfiles/`):

```bash
cd ~/dotfiles
git status
git add emacs-configs/custom/lisp/a3madkour-publish.el \
        emacs-configs/custom/lisp/a3madkour-publish-test.el \
        emacs-configs/custom/lisp/run-tests.sh
git status   # confirm staging
```

Expected `git status` after staging shows the three new files under "Changes to be committed".

- [ ] **Step 2: Stage the site-repo plan file**

In the site repo (`/Stuff/a3madkour/Sync/Workspace/a3madkour.github.io/`):

```bash
git status
git add docs/superpowers/plans/2026-05-20-phase-3-a1-0-bootstrap.md
git status
```

Expected: one new file under "Changes to be committed".

- [ ] **Step 3: Author commits (reminder, not for agent)**

Suggested commit messages (author runs both):

In dotfiles:
```bash
git commit -m "feat(publish): bootstrap a3madkour-publish library + ert runner

Sub-project A.1.0 of the Phase 3 org→Hugo publish pipeline.
Empty library shell + dummy ert test + run-tests.sh wrapper.
Logic lands in A.1.{a..d}."
```

In site repo:
```bash
git commit -m "docs(plan): Phase 3 A.1.0 bootstrap implementation plan"
```

---

## Self-Review

**Spec coverage (against spec §10 + §11 — the only sections this plan touches):**
- §10 elisp library file path & namespace → Task 2 (creates the file, sets the `a3madkour-pub/` prefix via `defgroup`).
- §11 "elisp unit tests via ert, batch runner" → Tasks 3 + 5.
- §11 "per-stage manual verification checkpoint" → Task 6.
- Everything else in the spec is deferred to A.1.{a..d} — explicitly out of scope here.

**Placeholder scan:** None. Every step has concrete commands and code; no "TBD" or "fill in details".

**Type consistency:** Only one elisp constant declared (`a3madkour-pub/version`); referenced consistently in the library and the test.

**Scope check:** Bootstrap-only — no logic, no domain code, no dependencies on other sub-projects. Smallest possible plan that establishes the dev loop.
