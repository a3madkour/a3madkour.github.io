# Phase 3 B.1.1 — Pre-Export ID-Link Rewriter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the B.1 garden handler safely publish notes that contain `[[id:UUID]]` / `[[file:...]]` / `[[<type>:UUID]]` org-roam links, so Hugo's build no longer errors with `REF_NOT_FOUND` on B-emitted bundles.

**Architecture:** A new helper `a3madkour-pub-rewrite/rewrite-buffer-links` scans the current buffer for org bracket-link forms and substitutes each in place with A.1's `rewrite-link` result (resolved HTML anchor or inert plain text). The garden handler invokes this helper on a **copy** of the source written to a `.org` temp file, then hands the rewritten temp file to `export-file`. ox-hugo never sees the bracket form for id/file/typed links → never emits the `{{< relref "<underscore_filename>.md" >}}` shortcodes that fail Hugo's resolution against B's hyphen-slug bundle paths. External URLs and asset-shaped links pass through untouched (ox-hugo handles them correctly already).

**Tech Stack:** Emacs Lisp (`a3madkour-publish-rewrite.el`, `a3madkour-publish-garden.el`), ert (unit tests), Python 3 stdlib + `emacs --batch` (integration fixtures via `tools/test_publish_integration.py`), Hugo (real-corpus spot-check).

---

## Why this slice exists

Round-2 spot-check on 2026-05-25 annotated `~/org/notes/maximum_a_posteriori.org` (3 id-links) and ran `a3-pub.sh --publish-living`. Hugo errored with 3× `REF_NOT_FOUND`. Root cause per `memory/reference_ox_hugo_id_links_become_relref.md`: ox-hugo translates `[[id:UUID][text]]` to `[text]({{< relref "<underscore_filename>.md" >}})` regardless of target publish state, AND the underscore-filename form never matches B-emitted hyphen-slug bundle paths.

The B.1 garden handler is otherwise complete; this slice is the gating fix that unblocks every further linked-note publish.

The architectural choice — pre-export buffer rewrite vs. post-export string substitution vs. `org-link-set-parameters` hooks — was made in the round-2 spot-check synthesis (see `memory/project_b1_complete.md` "round 2"). Pre-export reuses A.1's `rewrite-link` exactly as designed and needs no path-to-id reverse map. The other two options are not in scope for this plan.

## File structure

**New file:** none. All changes are additive edits to existing modules.

**Modified files:**

- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el` — add `a3madkour-pub-rewrite/rewrite-buffer-links` (public helper) at the bottom of the file, just before `(provide ...)`.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el` — add unit tests for the new helper (one new section: `;; -- rewrite-buffer-links`).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden.el` — add `a3madkour-pub-garden--rewrite-to-tmp-file` private helper; wire the helper into `publish-garden-file` so the export runs against a rewritten temp file; refresh the docstring NOTE block (the deferred-link-rewriting paragraph becomes obsolete).
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden-test.el` — add one end-to-end ert test asserting `publish-garden-file` output contains the resolved `<a href="...">` and does NOT contain `{{< relref` or `[[id:`.
- `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el` — Task 7 only: upgrade `--unpublish-delete-bundle` to also WARN loudly + return a distinguishable value when the delete itself errors (separate from the "already absent" benign path). Out of scope: the no-retry behavior fix — just make failures visible.
- `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py` — add a 14th fixture `test_garden_publish_with_cross_link` to `TestGardenPublishLiving`.
- `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` — Task 8 only: §11 "Known issues" subsection gets a one-line note that link rewriting is now in place via the helper added in this slice; the prior placeholder language ("link rewriting intentionally deferred") in the garden handler docstring is rotated out.

## Conventions

- **No `[ ]` outline below tasks** — each task's checklist is exhaustive on its own. Step granularity is one action per step (2-5 minutes).
- **TDD**: every code-touching task writes the failing test first, runs to verify failure, then implements minimal code, then re-runs.
- **Commit boundaries**: one commit per task. Commit messages follow the dotfiles + site repo conventions visible in `git log --oneline -30` (lowercase `feat:` / `test:` / `docs:` prefix; ~50 char first line; bullet body if needed).
- **Run from**: site repo root (`/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`) for Python tests and site commits. Dotfiles tests + commits run from `~/dotfiles/`. The plan uses absolute paths so the directory you're in doesn't matter.
- **Test runner**: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh` runs all 260 ert tests in batch via straight.el bootstrap. There is no faster per-test runner; the 260 tests complete in ~30 s.
- **Python integration fixtures**: each fixture invokes `emacs --batch` end-to-end (5-10 s per call), so a single `test_garden_publish_with_cross_link` fixture adds ~10-20 s to the integration suite. Run as `cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration -v -k test_garden_publish_with_cross_link`.

---

### Task 1: Write failing ert tests for `rewrite-buffer-links`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el` — append at end of file, before `(provide ...)`

- [ ] **Step 1: Read the current end of the test file**

```bash
tail -25 ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el
```

You're looking for the `(provide 'a3madkour-publish-rewrite-test)` line and the line above it; the new tests go just before that `(provide ...)`.

- [ ] **Step 2: Append the new test section**

Insert this block immediately before `(provide 'a3madkour-publish-rewrite-test)`:

```elisp
;; -- rewrite-buffer-links --

(ert-deftest a3madkour-pub-rewrite-test/buffer-links-resolved-id ()
  "Resolved id-link in buffer → replaced by <a href> anchor."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("target-id" :state live :section "garden" :slug "foo")
    ("source-id" :state live :section "garden" :slug "src"))
   (with-temp-buffer
     (insert "prefix [[id:target-id][text]] suffix")
     (a3madkour-pub-rewrite/rewrite-buffer-links "source-id")
     (should (equal (buffer-string)
                    "prefix <a href=\"/garden/foo/\">text</a> suffix")))))

(ert-deftest a3madkour-pub-rewrite-test/buffer-links-unresolved-id-inert ()
  "Unresolved id-link in buffer → replaced by inert plain text + warning."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("source-id" :state live :section "garden" :slug "src"))
   ;; No entry for "unknown-id" → published-p returns nil → :inert.
   (with-temp-buffer
     (insert "alpha [[id:unknown-id][missing]] omega")
     (let ((warnings (a3madkour-pub-rewrite/rewrite-buffer-links "source-id")))
       (should (equal (buffer-string) "alpha missing omega"))
       (should (= 1 (length warnings)))
       (should (string-match-p "private\\|unknown" (car warnings)))))))

(ert-deftest a3madkour-pub-rewrite-test/buffer-links-multiple-on-one-line ()
  "Three links on one line all rewrite correctly (covers the MAP case)."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("t1" :state live :section "garden" :slug "one")
    ("t2" :state live :section "garden" :slug "two")
    ("source-id" :state live :section "garden" :slug "src"))
   (with-temp-buffer
     (insert "see [[id:t1][One]] and [[id:t2][Two]] and [[id:missing][Three]] end")
     (a3madkour-pub-rewrite/rewrite-buffer-links "source-id")
     (should (equal (buffer-string)
                    (concat "see "
                            "<a href=\"/garden/one/\">One</a>"
                            " and "
                            "<a href=\"/garden/two/\">Two</a>"
                            " and Three end"))))))

(ert-deftest a3madkour-pub-rewrite-test/buffer-links-external-url-untouched ()
  "External URL `[[https://...]]' passes through unchanged (ox-hugo handles it)."
  (with-temp-buffer
    (insert "see [[https://example.com][Example]] for details")
    (let ((warnings (a3madkour-pub-rewrite/rewrite-buffer-links "source-id")))
      (should (equal (buffer-string)
                     "see [[https://example.com][Example]] for details"))
      (should-not warnings))))

(ert-deftest a3madkour-pub-rewrite-test/buffer-links-asset-untouched ()
  "Asset-shaped link `[[./assets/...]]' passes through unchanged."
  (with-temp-buffer
    (insert "fig: [[./assets/page/foo/x.png]]")
    (let ((warnings (a3madkour-pub-rewrite/rewrite-buffer-links "source-id")))
      (should (equal (buffer-string)
                     "fig: [[./assets/page/foo/x.png]]"))
      (should-not warnings))))

(ert-deftest a3madkour-pub-rewrite-test/buffer-links-typed-link-class ()
  "[[supports:UUID][text]] resolved → `class=\"link-supports\"' anchor."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("tgt" :state live :section "garden" :slug "ev")
    ("source-id" :state live :section "garden" :slug "src"))
   (with-temp-buffer
     (insert "[[supports:tgt][evidence]]")
     (a3madkour-pub-rewrite/rewrite-buffer-links "source-id")
     (should (equal (buffer-string)
                    "<a class=\"link-supports\" href=\"/garden/ev/\">evidence</a>")))))

(ert-deftest a3madkour-pub-rewrite-test/buffer-links-id-without-display-text ()
  "[[id:UUID]] (no text) → href uses resolved URL as display text."
  (a3madkour-pub-rewrite-test--with-stubbed
   (("target-id" :state live :section "garden" :slug "foo")
    ("source-id" :state live :section "garden" :slug "src"))
   (with-temp-buffer
     (insert "see [[id:target-id]] for context")
     (a3madkour-pub-rewrite/rewrite-buffer-links "source-id")
     (should (equal (buffer-string)
                    "see <a href=\"/garden/foo/\">/garden/foo/</a> for context")))))
```

- [ ] **Step 3: Run the test file; verify the new tests fail with "void function" / unbound symbol**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -40
```

Expected output: 7 failures in the new `buffer-links-*` tests, all with errors of the form `(void-function a3madkour-pub-rewrite/rewrite-buffer-links)`. All 260 pre-existing tests still pass. Total: `260 passed, 7 failed, 0 unexpected`.

(If the count does not match, check that you appended before — not after — `(provide ...)`. The `(provide ...)` line must remain the last form in the file.)

- [ ] **Step 4: Commit the failing tests**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-rewrite-test.el && git commit -m "test(b-1-1): rewrite-buffer-links unit tests (failing)"
```

---

### Task 2: Implement `rewrite-buffer-links`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el` — insert new public helper just before the final `(provide ...)` line.

- [ ] **Step 1: Read the current end of the rewrite source file**

```bash
tail -20 ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-rewrite.el
```

You should see the `t` branch of `cond` that signals the "scheme not yet handled" error, then `(provide 'a3madkour-publish-rewrite)`. The new function goes between those.

- [ ] **Step 2: Insert the new helper**

Insert this block immediately before `(provide 'a3madkour-publish-rewrite)`:

```elisp
(defconst a3madkour-pub-rewrite--bracket-link-re
  "\\[\\[\\([^][]+\\)\\(?:\\]\\[\\([^][]+\\)\\)?\\]\\]"
  "Regex matching an org bracket-link form `[[path]]' or `[[path][text]]'.
Group 1 = path, group 2 = optional display text.  Rejects nested
brackets (`[^][]+') — org's bracket-link syntax does not permit them in
either path or text, so this is sufficient for our scan.")

(defun a3madkour-pub-rewrite/rewrite-buffer-links (source-note-id)
  "Scan the current buffer for org bracket-link forms; rewrite each in place.

For every `[[...]]` form whose path uses a scheme A.1 knows how to resolve
(`id:`, `file:`, or any member of `a3madkour-pub-typed-link-types'), calls
`a3madkour-pub/rewrite-link' and substitutes the match with the returned
`:html' (resolved → inline HTML anchor) or `:inert' (unresolved → plain
text).  External URLs and asset-shaped links pass through unchanged —
ox-hugo handles those correctly on its own.

SOURCE-NOTE-ID is the org-roam :ID: of the file whose contents fill the
buffer; threaded through to `rewrite-link' for source-state checks.

Returns the accumulated list of warning strings (empty list when none).

Intended for use as the pre-export step in B's per-section handlers: the
caller copies the source `.org' to a temp buffer/file, applies this helper,
then hands the rewritten text to `a3madkour-pub-export/export-file'.  This
keeps the `[[...]]` form out of ox-hugo's input → prevents ox-hugo from
emitting `{{< relref \"<underscore_filename>.md\" >}}' shortcodes that
would never resolve against B's hyphen-slug bundle paths."
  (let ((warnings nil))
    (save-excursion
      (goto-char (point-min))
      (while (re-search-forward a3madkour-pub-rewrite--bracket-link-re nil t)
        (let* ((org-link (match-string 0))
               (parsed   (a3madkour-pub--parse-org-link org-link))
               (path     (plist-get parsed :path))
               (scheme   (a3madkour-pub--link-scheme path)))
          (when (or (equal scheme "id")
                    (equal scheme "file")
                    (member scheme a3madkour-pub-typed-link-types))
            (let* ((result      (a3madkour-pub/rewrite-link
                                 org-link source-note-id))
                   (replacement (or (plist-get result :html)
                                    (plist-get result :inert)
                                    ""))
                   (warns       (plist-get result :warnings)))
              (when warns
                (setq warnings (nconc warnings warns)))
              (replace-match replacement t t))))))
    warnings))
```

- [ ] **Step 3: Run the test suite; verify all 7 new tests pass**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -10
```

Expected: `267 passed, 0 failed, 0 unexpected`. (260 baseline + 7 new tests, all passing.)

If any of the new tests still fail, read the failure output carefully:
- `void-function` → the function name in the test doesn't match what's defined; check spelling.
- Wrong string in `buffer-string` assertion → confirm `replace-match` got `t t` (FIXEDCASE, LITERAL) — without LITERAL, ampersands in HTML would be interpreted as back-references.
- Wrong warning count → confirm you're passing through `(plist-get result :warnings)` only when non-nil.

- [ ] **Step 4: Commit the helper**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-rewrite.el && git commit -m "feat(b-1-1): rewrite-buffer-links scanner reuses rewrite-link"
```

---

### Task 3: Write the failing end-to-end ert test for `publish-garden-file`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden-test.el` — append a new test before the final `(provide ...)` line.

- [ ] **Step 1: Read the existing end-to-end test for reference**

```bash
grep -n "publish-garden-file-end-to-end" ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden-test.el
```

You're verifying the test name pattern (`a3madkour-pub-garden--publish-garden-file-end-to-end`) and roughly where it ends so the new test sits next to it.

- [ ] **Step 2: Append the new test before `(provide ...)`**

```elisp
(ert-deftest a3madkour-pub-garden--publish-garden-file-rewrites-links ()
  "publish-garden-file pre-rewrites [[id:UUID]] links so the emitted
markdown has resolved HTML anchors and zero `{{< relref' shortcodes.

This is the B.1.1 regression test: prior to pre-export buffer rewriting,
ox-hugo emitted `[text]({{< relref \"<filename>.md\" >}})' for every
id-link, which then failed Hugo's REF_NOT_FOUND check against B's
hyphen-slug bundles."
  (let* ((notes-dir (make-temp-file "a3-pub-notes-b11-" t))
         (site-dir  (make-temp-file "a3-pub-site-b11-" t))
         ;; Two notes — `b-source.org' links to `a-target.org'.  Alphabetical
         ;; ordering matters: publish-living processes a/ first, so when
         ;; b/ is processed the manifest already has a/'s state.  (One-pass
         ;; cross-link resolution; future two-pass design is out of scope.)
         (target-src (expand-file-name "a-target.org" notes-dir))
         (source-src (expand-file-name "b-source.org" notes-dir))
         (target-id  "11111111-2222-3333-4444-555555555555")
         (source-id  "66666666-7777-8888-9999-aaaaaaaaaaaa"))
    (unwind-protect
        (progn
          (make-directory (expand-file-name "data" site-dir))
          (make-directory (expand-file-name "content/garden" site-dir) t)
          (with-temp-file target-src
            (insert ":PROPERTIES:\n"
                    ":ID: " target-id "\n"
                    ":END:\n"
                    "#+title: Target Note\n"
                    "#+HUGO_PUBLISH: t\n"
                    "#+HUGO_SECTION: garden\n"
                    "#+HUGO_BASE_DIR: " site-dir "\n"
                    "Target body.\n"))
          (with-temp-file source-src
            (insert ":PROPERTIES:\n"
                    ":ID: " source-id "\n"
                    ":END:\n"
                    "#+title: Source Note\n"
                    "#+HUGO_PUBLISH: t\n"
                    "#+HUGO_SECTION: garden\n"
                    "#+HUGO_BASE_DIR: " site-dir "\n"
                    "Body text linking to [[id:" target-id "][the target]] "
                    "and to [[id:00000000-0000-0000-0000-000000000000][a private one]].\n"))
          (let ((a3madkour-pub/site-data-dir
                 (file-name-as-directory (expand-file-name "data" site-dir)))
                (a3madkour-pub/org-notes-dir notes-dir))
            (cl-letf (((symbol-function 'org-roam-db-sync) #'ignore)
                      ;; id-to-file resolves both real IDs to their .org files.
                      ;; The "private" UUID resolves to nil, exercising the
                      ;; :inert branch via published-p returning nil.
                      ((symbol-function 'a3madkour-pub--id-to-file)
                       (lambda (id)
                         (cond ((equal id target-id) target-src)
                               ((equal id source-id) source-src)
                               (t nil)))))
              (a3madkour-pub/begin-publish)
              (a3madkour-pub-garden/publish-garden-file target-src)
              (a3madkour-pub-garden/publish-garden-file source-src)
              (a3madkour-pub/finish-publish)))
          (let* ((out  (expand-file-name
                        "content/garden/source-note/index.md" site-dir))
                 (body (with-temp-buffer
                         (insert-file-contents out)
                         (buffer-string))))
            (should (file-exists-p out))
            ;; Resolved link → HTML anchor at the right hyphen-slug URL.
            (should (string-match-p
                     "<a href=\"/garden/target-note/\">the target</a>"
                     body))
            ;; Unresolved link → inert plain text, no anchor.
            (should (string-match-p "a private one" body))
            (should-not (string-match-p
                         "href=\"[^\"]*private one[^\"]*\"" body))
            ;; And critically: no ox-hugo relref shortcodes survived.
            (should-not (string-match-p "{{< *relref" body))
            (should-not (string-match-p "\\[\\[id:" body))))
      (delete-directory notes-dir t)
      (delete-directory site-dir t))))
```

- [ ] **Step 3: Run the suite; verify the new test fails**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -15
```

Expected: `267 passed, 1 failed, 0 unexpected`. The new test fails with assertion mismatch on the `<a href="/garden/target-note/">` regex (the resolved anchor isn't there — ox-hugo still emits `{{< relref >}}`). Other failures (e.g., the `{{< *relref` `should-not` firing) confirm the bug is present pre-fix.

- [ ] **Step 4: Commit the failing test**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-garden-test.el && git commit -m "test(b-1-1): garden handler link-rewrite end-to-end (failing)"
```

---

### Task 4: Wire `rewrite-buffer-links` into `publish-garden-file`

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-garden.el` — add the new private helper `--rewrite-to-tmp-file`; modify `publish-garden-file` to route through it; rewrite the obsolete deferred-link-rewriting NOTE block in the docstring.

- [ ] **Step 1: Insert the new private helper above `publish-garden-file`**

Place this block immediately before the `(defun a3madkour-pub-garden/publish-garden-file ...)` form:

```elisp
(defun a3madkour-pub-garden--rewrite-to-tmp-file (source-file source-note-id)
  "Copy SOURCE-FILE to a fresh temp `.org' file with all org links
pre-rewritten via `a3madkour-pub-rewrite/rewrite-buffer-links'.

Returns the absolute path of the temp file.  Caller is responsible for
`delete-file' on the returned path (typical pattern: wrap the consumer
in an `unwind-protect' that deletes on cleanup).

Warnings from the rewriter are surfaced via `message' with the SOURCE-FILE
included so authors can grep the publish log.  (Future slices may route
these through a structured warning channel; for now they ride the same
stderr stream as the rest of the publish pipeline's messages.)"
  (let ((tmp (make-temp-file "a3-pub-pre-export-" nil ".org"))
        warnings)
    (with-temp-buffer
      (insert-file-contents source-file)
      (setq warnings
            (a3madkour-pub-rewrite/rewrite-buffer-links source-note-id))
      (write-region (point-min) (point-max) tmp nil 'quiet))
    (dolist (w warnings)
      (message "[a3-pub-garden] rewrite WARN (%s): %s" source-file w))
    tmp))
```

- [ ] **Step 2: Replace the body of `publish-garden-file`**

Replace the entire `(defun a3madkour-pub-garden/publish-garden-file ...)` form with this version. The signature is unchanged; the body now routes through the temp-file helper, and the obsolete deferred-link-rewriting NOTE is removed.

```elisp
(defun a3madkour-pub-garden/publish-garden-file (file)
  "Publish a single garden-section FILE to content/garden/<slug>/index.md.

Pipeline per spec §10:
  pre-export-rewrite-links → export → frontmatter/normalize →
  asset-validate-and-copy → write-if-different → record-publish.

The pre-export rewrite step copies FILE to a temp .org file and calls
`a3madkour-pub-rewrite/rewrite-buffer-links' on it (B.1.1) so that org
bracket-link forms `[[id:UUID]]', `[[file:...]]', and `[[<type>:UUID]]'
are resolved to inline HTML anchors (or inert plain text for unpublished
targets) before ox-hugo sees them.  Without this step ox-hugo emits
`{{< relref \"<underscore_filename>.md\" >}}' shortcodes that fail
Hugo's REF_NOT_FOUND check against B's hyphen-slug bundle paths."
  (let* ((id        (plist-get (a3madkour-pub/note-metadata file) :id))
         (slug      (a3madkour-pub/note-slug file))
         (new-url   (a3madkour-pub/note-url file))
         (site-root (a3madkour-pub-garden--site-root))
         (bundle-dir (expand-file-name
                      (format "content/%s/%s/"
                              a3madkour-pub-garden/section-dir-name slug)
                      site-root))
         (out-path   (expand-file-name "index.md" bundle-dir))
         (tmp-src    (a3madkour-pub-garden--rewrite-to-tmp-file file id))
         (exported   (unwind-protect
                         (a3madkour-pub-export/export-file tmp-src)
                       (when (file-exists-p tmp-src)
                         (delete-file tmp-src))))
         (normalized (a3madkour-pub-frontmatter/normalize
                      'garden (plist-get exported :frontmatter) file))
         (body       (plist-get exported :body)))
    (a3madkour-pub/asset-validate-and-copy file bundle-dir)
    (a3madkour-pub-garden--write-if-different
     out-path
     (concat (a3madkour-pub-garden--render-frontmatter normalized) body))
    (a3madkour-pub-history/record-publish id new-url 'live)))
```

- [ ] **Step 3: Run the suite; verify all 267+1 tests pass**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -10
```

Expected: `268 passed, 0 failed, 0 unexpected`.

If the new end-to-end test fails on the `<a href="/garden/target-note/">` regex:
- Check the rewritten temp file is actually being passed to `export-file` (the variable name change `tmp-src` is intentional — `exported` reads from it).
- Verify `a3madkour-pub--id-to-file` is stubbed in the test to return the source files — `published-p` cascades through `note-metadata` which may invoke id-to-file.

If the new test fails on `{{< *relref` still appearing — the buffer rewrite isn't reaching the export. Likely cause: `note-metadata` returning a different `:id` than the source-id used as the rewrite key. Add a `(message "tmp-src: %s contents: %s" tmp-src (with-temp-buffer (insert-file-contents tmp-src) (buffer-string)))` and re-run to see what's actually exported.

- [ ] **Step 4: Commit the wiring**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-garden.el && git commit -m "feat(b-1-1): garden handler runs rewrite-buffer-links pre-export"
```

---

### Task 5: Add Python integration fixture `test_garden_publish_with_cross_link`

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py` — append a new test method to `TestGardenPublishLiving` and verify it.

- [ ] **Step 1: Find the insertion point in the test file**

```bash
grep -n "def test_garden_emits_lint_clean_output\|^if __name__\|^class TestGardenPublishLiving" /Users/a3madkour/Sync/Workspace/a3madkour.github.io/tools/test_publish_integration.py
```

You're confirming `test_garden_emits_lint_clean_output` is the last method in the class. The new method goes after it, before the next `class` declaration or the `if __name__ == "__main__":` block at file end.

- [ ] **Step 2: Append the new test method**

Insert this method as the last method in `TestGardenPublishLiving` (use the same 4-space indentation as the surrounding methods):

```python
    # ------------------------------------------------------------------
    # Task 17 (B.1.1): test_garden_publish_with_cross_link
    # ------------------------------------------------------------------

    def test_garden_publish_with_cross_link(self) -> None:
        """B.1.1 regression: source note links to (a) a published target and
        (b) a private/unknown UUID.

        Asserts the emitted source bundle:
        - contains an HTML anchor pointing at /garden/<target-slug>/
        - contains the inert plain text for the unpublished link
        - does NOT contain any ``{{< relref`` shortcode (the round-2 bug)
        - does NOT contain any raw `[[id:` bracket form (the pre-export rewrite
          really happened — ox-hugo's input was the rewritten temp file)

        Naming convention: `a-target.org` is alphabetically first so
        publish-living processes it before `b-source.org`; by the time the
        source is processed, the target is already in the manifest and
        rewrite-link resolves to `:html` (not `:inert`).
        """
        target_id = "44444444-5555-6666-7777-888888888888"
        source_id = "99999999-aaaa-bbbb-cccc-dddddddddddd"
        unknown_id = "00000000-0000-0000-0000-000000000000"

        target_src = self.notes_dir / "a-target.org"
        source_src = self.notes_dir / "b-source.org"

        _write_garden_source(target_src, target_id, "Cross Target",
                             self.site_root)
        # Source body with two id-links: one to the published target, one
        # to an unknown UUID (exercises the :inert path).
        source_src.write_text(
            ":PROPERTIES:\n"
            f":ID: {source_id}\n"
            ":END:\n"
            "#+title: Cross Source\n"
            "#+HUGO_PUBLISH: t\n"
            "#+HUGO_SECTION: garden\n"
            f"#+HUGO_BASE_DIR: {self.site_root}/\n"
            "* Overview\n"
            f"Links to [[id:{target_id}][the target]] and to "
            f"[[id:{unknown_id}][a private one]] in one line.\n",
            encoding="utf-8",
        )

        proc = _publish_living(self.notes_dir, self._site_data_dir)
        self.assertEqual(
            proc.returncode, 0,
            msg=(
                "publish-living exited non-zero.\n"
                f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            ),
        )

        source_index = (
            self.site_root / "content" / "garden" / "cross-source" / "index.md"
        )
        self.assertTrue(
            source_index.exists(),
            f"source bundle not created.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
        )

        body = source_index.read_text(encoding="utf-8")
        self.assertIn(
            '<a href="/garden/cross-target/">the target</a>', body,
            f"resolved cross-link missing from emitted markdown.\nbody:\n{body}",
        )
        self.assertIn(
            "a private one", body,
            f"inert text for unpublished link missing.\nbody:\n{body}",
        )
        self.assertNotIn(
            "{{< relref", body,
            f"`{{{{< relref' shortcode survived — pre-export rewrite did not run.\nbody:\n{body}",
        )
        self.assertNotIn(
            "[[id:", body,
            f"raw `[[id:` form survived — bracket-link regex missed a case.\nbody:\n{body}",
        )
```

- [ ] **Step 3: Run the fixture; verify it passes**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration.TestGardenPublishLiving.test_garden_publish_with_cross_link -v
```

Expected output ends with `OK` and a single `test_garden_publish_with_cross_link ... ok` line. Runtime: ~15-20 s (one `_publish_living` call + Python overhead).

If the fixture fails:
- `returncode != 0` → read `proc.stderr` from the failure message; if it mentions `straight-use-package` or load-path issues, the dotfiles bootstrap probably isn't on disk where `DOTFILES_LISP` expects.
- "source bundle not created" → the slug isn't `cross-source` (title is `Cross Source` → slug is `cross-source`). Check `a3madkour-pub/note-slug`'s contract.
- `{{< relref` still appears → the elisp helper from Task 2 isn't being loaded by `_publish_living`. Grep `_publish_living` to confirm `a3madkour-publish-rewrite` is in the `-l` flags list (it should be there from B.1; no change needed in this task).

- [ ] **Step 4: Run the full integration suite to confirm no regressions**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -m unittest tools.test_publish_integration -v 2>&1 | tail -20
```

Expected: `Ran 14 tests in ...s\n\nOK`. (13 baseline + 1 new.)

- [ ] **Step 5: Commit the fixture**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && git add tools/test_publish_integration.py && git commit -m "test(b-1-1): integration fixture for cross-linked garden publish"
```

---

### Task 6: Spot-check round 3 against the real `~/org/notes/` corpus

**Files:**
- Modify: `~/org/notes/maximum_a_posteriori.org` — re-annotate with `#+HUGO_PUBLISH: t` + `#+HUGO_SECTION: garden`. (This file was annotated then rolled back in round 2; a backup of the original sits at `/tmp/b1-spotcheck-backup-203015/` per `memory/project_b1_complete.md`.)
- No other files modified in this task — the publish-living run mutates the site repo's `content/` and `data/url-history.yaml`. Commit those separately at the end if the spot-check is clean.

- [ ] **Step 1: Confirm the backup exists**

```bash
ls /tmp/b1-spotcheck-backup-203015/ 2>/dev/null && echo "backup present" || echo "backup missing — do not annotate without one"
```

If the backup is missing (system reboot likely cleared `/tmp/`), make a fresh one before annotating:

```bash
mkdir -p /tmp/b11-spotcheck-backup-$(date +%H%M%S) && cp ~/org/notes/maximum_a_posteriori.org /tmp/b11-spotcheck-backup-*/
```

- [ ] **Step 2: Annotate `maximum_a_posteriori.org`**

Open the file and add these two lines among the file-level keywords (just below `#+title:` is the conventional position; the order of `#+HUGO_*` keywords doesn't matter):

```
#+HUGO_PUBLISH: t
#+HUGO_SECTION: garden
```

Save and close.

- [ ] **Step 3: Run publish-living against the real site repo**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && ~/dotfiles/emacs-configs/custom/lisp/../../a3-pub.sh --publish-living 2>&1 | tail -40
```

(If the path is wrong on disk, use `which a3-pub.sh` to locate it; the wrapper lives in dotfiles.)

Expected: pipeline exits 0. A new bundle appears at `content/garden/maximum-a-posteriori/index.md`. The publish log mentions Bayesian Statistics as resolved and any unannotated link target (e.g. Inference Queries) as private/unknown.

- [ ] **Step 4: Verify `hugo --minify` is clean**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && hugo --minify 2>&1 | tail -20
```

Expected: zero `REF_NOT_FOUND` errors. Total page count is 3 + N higher than the pre-round-2 baseline (one new bundle plus any other notes you annotated to round out the cross-link surface).

If `REF_NOT_FOUND` still appears: the regex in `rewrite-buffer-links` missed a link form. Grep the published bundle's `index.md` for `{{< relref` to find exactly which link form leaked through, then add a unit test in `a3madkour-publish-rewrite-test.el` covering that shape before fixing the regex.

- [ ] **Step 5: Eyeball the emitted markdown**

```bash
cat /Users/a3madkour/Sync/Workspace/a3madkour.github.io/content/garden/maximum-a-posteriori/index.md
```

Confirm visually:
- The link to Bayesian Statistics shows as `<a href="/garden/bayesian-statistics/">Bayesian Statistics</a>` (inline HTML).
- Any link to an unannotated target shows as inert plain text — the display label survives, no `<a>` tag.
- The frontmatter is well-formed YAML.

- [ ] **Step 6: Commit the round-3 evidence to the site repo**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && git add content/garden/maximum-a-posteriori/ data/url-history.yaml && git commit -m "feat(b-1-1): publish MAP with resolved cross-links (round 3 spot-check)"
```

- [ ] **Step 7: Update the memory snapshot**

Append a "round 3" subsection to `/Users/a3madkour/.claude/projects/-Users-a3madkour-Sync-Workspace-a3madkour-github-io/memory/project_b1_complete.md` describing the spot-check outcome (one short paragraph). Also update `memory/project_next_slice.md`'s pointer to be **B.2 — library handler** (B.1.1 is now shipped).

Concretely, replace the body of `project_next_slice.md` so it points at B.2, and add a note at the top: "B.1.1 shipped <date>; see [[b1-complete]] round-3 subsection."

---

### Task 7: File the `--unpublish-delete-bundle` no-retry follow-up

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish.el` — `--unpublish-delete-bundle` (current line 150) — wrap the `delete-directory` call so a thrown error becomes a loud `message` instead of bubbling silently into `finish-publish`. We are NOT implementing retry or manifest-state reset; this slice's contribution is just visibility.
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el` — add one ert test covering the new visibility behavior.

- [ ] **Step 1: Add the failing test**

Append before `(provide ...)` in `a3madkour-publish-unpublish-test.el`:

```elisp
(ert-deftest a3madkour-pub-unpublish-test/delete-bundle-warns-on-failure ()
  "When `delete-directory' errors, --unpublish-delete-bundle returns 'failed
and emits a [a3-pub] WARN message including the bundle path."
  (let* ((root (make-temp-file "a3-pub-content-" t))
         (bundle (expand-file-name "garden/locked-bundle" root)))
    (unwind-protect
        (progn
          (make-directory bundle t)
          (cl-letf (((symbol-function 'delete-directory)
                     (lambda (&rest _) (error "permission denied (test stub)"))))
            (let ((messages-buffer (get-buffer-create "*Messages*")))
              (with-current-buffer messages-buffer (erase-buffer))
              (let ((result (a3madkour-pub--unpublish-delete-bundle
                             "garden" "locked-bundle" root)))
                (should (eq result 'failed))
                (with-current-buffer messages-buffer
                  (should (string-match-p
                           "\\[a3-pub\\] delete-bundle FAILED" (buffer-string)))
                  (should (string-match-p "locked-bundle" (buffer-string))))))))
      (delete-directory root t))))
```

- [ ] **Step 2: Run; verify the test fails**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "(unpublish-test/delete-bundle-warns-on-failure|FAILED|passed,)" | tail -5
```

Expected: the new test fails (the error propagates out of `delete-directory` and is not caught; the function returns nothing / signals).

- [ ] **Step 3: Implement the visibility upgrade**

Replace the existing `(cond ((file-directory-p bundle) (delete-directory bundle t) t) ...)` body of `--unpublish-delete-bundle` with this version:

```elisp
(defun a3madkour-pub--unpublish-delete-bundle (section slug &optional content-root)
  "Recursively delete `<CONTENT-ROOT>/<SECTION>/<SLUG>/'.

CONTENT-ROOT defaults to `a3madkour-pub-site-content-dir'.

Return values:
  t        — bundle existed and was deleted.
  nil      — bundle was already absent (benign; logged via `message').
  'failed  — bundle existed but `delete-directory' signalled an error.
             The error is caught and reported via `message' with a `[a3-pub]
             delete-bundle FAILED' prefix so the publish log surfaces it.
             The manifest is NOT reset; callers may treat this as transient.

B.1.1 follow-up: prior to this slice, a thrown error from `delete-directory'
propagated into `finish-publish' and aborted the publish run with no clear
attribution.  Visibility-only fix — retry / manifest-state reset for
self-healing on a subsequent run is left as a future task."
  (let* ((root (or content-root (a3madkour-pub--site-content-dir-effective)))
         (bundle (file-name-as-directory
                  (expand-file-name (format "%s/%s" section slug) root))))
    (cond
     ((file-directory-p bundle)
      (condition-case err
          (progn (delete-directory bundle t) t)
        (error
         (message "[a3-pub] delete-bundle FAILED: %s (%s)"
                  bundle (error-message-string err))
         'failed)))
     (t
      (message "[a3-pub] delete-bundle: %s already absent (stale manifest?)" bundle)
      nil))))
```

- [ ] **Step 4: Run all dotfiles tests; verify pass**

```bash
cd ~/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | tail -10
```

Expected: `269 passed, 0 failed, 0 unexpected`. (267 from Task 2 + the Task 3 garden test + the new Task 7 test.)

- [ ] **Step 5: Commit the visibility upgrade**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-unpublish.el emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el && git commit -m "feat(b-1-1): delete-bundle WARNs loudly on failure (no silent abort)"
```

---

### Task 8: Update the B parent spec + site CLAUDE.md status

**Files:**
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` — locate the "Known issues" / "Open questions" section (search for the "deferred" or "link rewriting" mention from B.1's docstring) and add one sentence noting B.1.1 closes that thread.
- Modify: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/CLAUDE.md` — the "Phase 3 — org-mode pipeline" bullet under "Not started, in phase order" lists shipped slices for sub-project B. Update it to mention B.1.1.

- [ ] **Step 1: Edit the B parent spec**

```bash
grep -n "link rewriting\|deferred\|Known issues\|Open questions" /Users/a3madkour/Sync/Workspace/a3madkour.github.io/docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md | head -20
```

In the matching section, replace any wording that says link rewriting is deferred with:

> Link rewriting (B.1.1, shipped 2026-05-26): pre-export buffer rewrite via `a3madkour-pub-rewrite/rewrite-buffer-links` runs in the garden handler before ox-hugo sees the source. Other section handlers (B.2 library, B.3 research, B.4 essays, B.5 works) should adopt the same `--rewrite-to-tmp-file` pattern.

(If the spec doesn't currently mention deferred link rewriting, add the above as a one-sentence note in §11 "Known issues" or the closest equivalent.)

- [ ] **Step 2: Update site CLAUDE.md**

Find the line in the "Phase 3 — org-mode pipeline" bullet that mentions B.1 ship status. Change:

> B.1 (garden handler) shipped 2026-05-25 in dotfiles ...

to:

> B.1 (garden handler) shipped 2026-05-25; B.1.1 (pre-export id-link rewriter) shipped 2026-05-26 (closes the round-2 spot-check finding — Hugo can resolve cross-links to B-emitted hyphen-slug bundles). Next: B.2 (library handler).

Adjust the surrounding wording so the bullet still reads naturally.

- [ ] **Step 3: Commit the doc updates**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && git add docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md CLAUDE.md && git commit -m "docs(b-1-1): close link-rewriting open question; B.1.1 shipped"
```

---

## Self-review against the spec / source

**Spec coverage (per `memory/project_next_slice.md` requirements):**

1. New helper `rewrite-buffer-links (source-note-id)` in `a3madkour-publish-rewrite.el` → Task 2 ✓
2. Wire into garden handler (tmp-file dance to preserve source integrity) → Task 4 ✓
3. ert tests for resolved id-link, unresolved id-link, multi-link line, no `{{< relref` in `*Org Hugo Export*` buffer → Tasks 1 + 3 (the end-to-end test directly inspects the emitted `index.md` which is downstream of the export buffer and is the user-facing artifact) ✓
4. Python integration fixture for "publish with cross-link" — bundles emitted, `hugo --minify` exits 0, resolved link is `/garden/<slug>/`, unresolved is inert → Task 5 ✓
   - Caveat: Task 5 does not invoke `hugo --minify` directly; that check happens in Task 6 against the real corpus. Adding a Hugo invocation to the Python fixture would add `hugo` to the test prerequisites and ~5s overhead per run; the round-3 spot-check covers that path already. If a future slice wants CI-level enforcement, add an opt-in `hugo --minify` step gated on `which hugo`.
5. Re-run round-2 spot-check on `maximum_a_posteriori.org` → Task 6 ✓
6. Follow-up filing for `finish-publish` no-retry → Task 7 (visibility upgrade; full retry/state-reset is out of scope and the docstring says so) ✓

**Placeholder scan:** Every step in this plan contains either a concrete shell command, a concrete elisp/python code block, or an "expected output" assertion. No TBD / TODO / "appropriate" / "etc." language.

**Type consistency:**
- `a3madkour-pub-rewrite/rewrite-buffer-links` takes `source-note-id` (one string arg) and returns a list — consistent across Tasks 1, 2, 4.
- `a3madkour-pub-garden--rewrite-to-tmp-file` takes `(source-file source-note-id)` and returns a string path — consistent in Task 4's helper and consumer.
- `a3madkour-pub/rewrite-link`'s return shape (`:html` / `:inert` / `:warnings` plist) is what the helper destructures — matches the existing rewrite.el lines 178-204 contract.
- `--unpublish-delete-bundle`'s new return value `'failed` is symbol-equal-compared in the Task 7 test (`(should (eq result 'failed))`) — matches.

**Cross-task assumption check:**
- Task 5's fixture relies on `a-target.org` being processed before `b-source.org` so the manifest has the target by the time the source is rewritten. `walk-section` in `a3madkour-publish-living.el` iterates via `directory-files`, which returns alphabetical order on macOS + Linux ext4 — assumption holds. If `walk-section` switches to a non-deterministic iteration order in a future slice, this test will become flaky; document the assumption in the fixture docstring (already done).

---

## Plan complete. Execution handoff.

**Plan complete and saved to `docs/superpowers/plans/2026-05-26-phase-3-b-1-1-id-link-rewriter.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Good fit here because Tasks 1+2, 3+4, and 7 are tight TDD cycles that benefit from a clean context per pair.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch with checkpoints at Tasks 4, 5, and 6 (the natural verification boundaries).

**Which approach?**
