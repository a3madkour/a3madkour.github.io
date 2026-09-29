# works/games + works/music org handlers — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `works/games` and `works/music` be authored in org-mode and published by `a3-publish-living`, closing the largest gap in the org authoring surface.

**Architecture:** One new dotfiles module `a3madkour-publish-works.el` registers two living-section entries that share one entry point and branch on section. Standard frontmatter routes through two new normalize branches in `frontmatter.el`; `tracks` is parsed from an org table and injected afterwards, exactly as recipes does with `ingredients`. Enum vocabularies move to one JSON file in the site repo that both `check_works_fixtures.py` and a new `a3madkour-works-lint.el` read fail-closed.

**Tech Stack:** Emacs Lisp (ert), ox-hugo, org-element; Python 3 stdlib (unittest); Hugo.

**Spec:** `docs/superpowers/specs/2026-09-28-works-games-music-handlers-design.md`

## Global Constraints

- **Two-symbol convention.** Dispatch alist, `#+HUGO_SECTION:` and `a3madkour-pub/sections` use the **slash** form (`works/games`). The normalize dispatch arm uses the **hyphen** form (`works-games`). Both symbols already exist in `a3madkour-pub-frontmatter--known-sections`; that constant needs no change.
- **Python tooling is stdlib-only.** No third-party imports in `tools/`.
- **Elisp takes no new package dependencies.** JSON via built-in `json-parse-string` (Emacs 27+).
- **Fixture content is obviously dummy** — lorem ipsum or "Example N". Never authored prose.
- **Every guard is mutation-tested**: break it, watch the test fail. A guard observed passing proves nothing.
- **`.elc` shadowing**: `require` prefers a stale `.elc` over a newer `.el`. Run `rm -f ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish*.elc` before any TDD cycle.
- Tests run with `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh`. Baseline is **751 passing**; every task states its expected new total.

## Review Focus

Five conditions the spec implies that no task's happy path exercises. Each has a test assigned to the task that owns the code.

1. **A work with every optional field absent.** Recipes needed `example-recipe-three` for exactly this, and it exists because the optional-absent path shipped broken. A game with only the eight required keys must emit no empty `screenshots: []`, no `hero:`, no `collaborators:`. → Task 4.
2. **A `screenshots` filename containing a space.** Whitespace splitting turns `"my shot.png"` into two names, both broken, and the bundle silently lacks the image. → Task 8.
3. **Two org files whose titles slugify identically.** Both resolve to the same `content/works/games/<slug>/index.md` and the second silently overwrites the first. → Task 7.
4. **A `#+NAME: tracks` table with a header row and no data rows.** Must omit the `tracks` key entirely, not emit `tracks: []`, which would render an empty track list. → Task 3.
5. **`#+HUGO_SECTION: works/games` present but `#+HUGO_PUBLISH:` absent or nil.** Must not publish. → Task 7.

---

### Task 1: Shared enum vocabulary, read fail-closed by the Python linter

**Files:**
- Create: `data/works-vocab.json` (site repo)
- Modify: `tools/check_works_fixtures.py:22-42` (replace four constants with a loader)
- Test: `tools/test_check_works_fixtures.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `data/works-vocab.json` with keys `game_statuses`, `game_kinds`, `music_formats`, `platform_kinds`, each a list of strings. Task 2 reads the same file from elisp.

- [ ] **Step 1: Write the failing test**

In `tools/test_check_works_fixtures.py`:

```python
def test_vocab_is_single_source(self):
    """Mutating the vocab file must change what the linter accepts."""
    repo = TempRepo()
    repo.write("data/works-vocab.json", json.dumps({
        "game_statuses": ["playible"],          # deliberate typo
        "game_kinds": ["jam"],
        "music_formats": ["album"],
        "platform_kinds": ["bandcamp"],
    }))
    repo.write("content/works/games/g/index.md", GAME_MD_PLAYABLE)
    code, errs = check_works_fixtures.run(repo.root)
    self.assertEqual(code, 1)
    self.assertTrue(any("status='playable'" in e for e in errs))

def test_missing_vocab_fails_closed(self):
    """A missing vocab file must error, never fall back to a hardcoded copy."""
    repo = TempRepo()
    repo.write("content/works/games/g/index.md", GAME_MD_PLAYABLE)
    with self.assertRaises(SystemExit):
        check_works_fixtures.run(repo.root)
```

`GAME_MD_PLAYABLE` is a module-level constant holding a minimal valid game fixture with `status: playable`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tools.test_check_works_fixtures -v`
Expected: FAIL — the linter still reads hardcoded constants, so the typo'd vocab changes nothing and `test_vocab_is_single_source` gets exit code 0.

- [ ] **Step 3: Create the vocabulary file**

`data/works-vocab.json`:

```json
{
  "game_statuses":  ["playable", "in-progress", "archived"],
  "game_kinds":     ["full-release", "jam", "research-prototype", "experiment"],
  "music_formats":  ["album", "track", "experiment", "live"],
  "platform_kinds": ["bandcamp", "soundcloud", "youtube"]
}
```

- [ ] **Step 4: Replace the constants with a fail-closed loader**

In `tools/check_works_fixtures.py`, delete the four `GAME_STATUSES` / `GAME_KINDS` / `MUSIC_FORMATS` / `PLATFORM_KINDS` assignments and add:

```python
import json

VOCAB_REL = Path("data") / "works-vocab.json"


def load_vocab(repo_root: Path) -> dict[str, set[str]]:
    """Load the shared enum vocabulary. Fails closed: never returns defaults.

    A fallback here would silently restore the cross-language drift surface
    this file exists to remove.
    """
    path = repo_root / VOCAB_REL
    try:
        raw = json.loads(path.read_text())
    except FileNotFoundError:
        sys.exit(f"check_works_fixtures: vocabulary not found at {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"check_works_fixtures: vocabulary at {path} is not valid JSON: {e}")
    required = {"game_statuses", "game_kinds", "music_formats", "platform_kinds"}
    missing = required - raw.keys()
    if missing:
        sys.exit(f"check_works_fixtures: vocabulary missing keys: {sorted(missing)}")
    return {k: set(raw[k]) for k in required}
```

Thread the loaded dict through: `run()` calls `load_vocab(repo_root)` once and passes it to `_validate_game` / `_validate_music`, which take a new `vocab` parameter and read `vocab["game_statuses"]` where they previously read the module constant.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m unittest tools.test_check_works_fixtures -v`
Expected: PASS, including the pre-existing enum-rejection tests, which now prove the loader is wired rather than the constants.

- [ ] **Step 6: Verify against the real tree**

Run: `python3 tools/check_works_fixtures.py`
Expected: exit 0, all 12 works fixtures pass.

- [ ] **Step 7: Mutation-check by hand**

Run: `python3 -c "import json,pathlib; p=pathlib.Path('data/works-vocab.json'); d=json.loads(p.read_text()); d['game_statuses']=['playible']; p.write_text(json.dumps(d))" && python3 tools/check_works_fixtures.py; git checkout data/works-vocab.json`
Expected: exit 1, naming all four game fixtures. If it exits 0, the loader is not actually being read.

- [ ] **Step 8: Commit**

```bash
git add data/works-vocab.json tools/check_works_fixtures.py tools/test_check_works_fixtures.py
git commit -m "feat(works): single-source the works enum vocabulary (fail-closed)"
```

---

### Task 2: Elisp vocabulary reader

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-works-lint.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-works-lint-test.el`

**Interfaces:**
- Consumes: `data/works-vocab.json` from Task 1; `a3madkour-pub-yaml/site-root` for the repo path.
- Produces: `(a3madkour-works-lint/vocab KEY)` → list of strings, where KEY is one of `game_statuses`, `game_kinds`, `music_formats`, `platform_kinds`. Signals `error` when the file is missing or malformed. Also `a3madkour-works-lint-enabled` (defvar, default `t`) and `a3madkour-works-lint/lint-file` (stub here, filled in Tasks 8–9).

- [ ] **Step 1: Write the failing test**

`a3madkour-works-lint-test.el`:

```elisp
;;; a3madkour-works-lint-test.el --- tests for works pre-publish lint  -*- lexical-binding: t; -*-
(require 'ert)
(require 'a3madkour-works-lint)

(defmacro a3madkour-works-lint-test--with-vocab (json &rest body)
  "Run BODY with a temp site root whose data/works-vocab.json holds JSON.
When JSON is nil, no vocabulary file is written."
  (declare (indent 1))
  `(let* ((root (make-temp-file "a3-works-vocab" t)))
     (unwind-protect
         (progn
           (when ,json
             (make-directory (expand-file-name "data" root) t)
             (with-temp-file (expand-file-name "data/works-vocab.json" root)
               (insert ,json)))
           (cl-letf (((symbol-function 'a3madkour-pub-yaml/site-root)
                      (lambda () root)))
             ,@body))
       (delete-directory root t))))

(ert-deftest a3madkour-works-lint--vocab-reads-file ()
  (a3madkour-works-lint-test--with-vocab
      "{\"game_statuses\":[\"playable\"],\"game_kinds\":[\"jam\"],\"music_formats\":[\"album\"],\"platform_kinds\":[\"bandcamp\"]}"
    (should (equal (a3madkour-works-lint/vocab "game_statuses") '("playable")))
    (should (equal (a3madkour-works-lint/vocab "game_kinds") '("jam")))))

(ert-deftest a3madkour-works-lint--vocab-fails-closed-when-missing ()
  (a3madkour-works-lint-test--with-vocab nil
    (should-error (a3madkour-works-lint/vocab "game_statuses"))))

(ert-deftest a3madkour-works-lint--vocab-fails-closed-when-malformed ()
  (a3madkour-works-lint-test--with-vocab "{ not json"
    (should-error (a3madkour-works-lint/vocab "game_statuses"))))

(ert-deftest a3madkour-works-lint--vocab-fails-closed-on-missing-key ()
  (a3madkour-works-lint-test--with-vocab "{\"game_statuses\":[\"playable\"]}"
    (should-error (a3madkour-works-lint/vocab "game_kinds"))))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rm -f ~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish*.elc && ~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: FAIL — `a3madkour-works-lint` is not loadable.

- [ ] **Step 3: Write the module**

`a3madkour-works-lint.el`:

```elisp
;;; a3madkour-works-lint.el --- works pre-publish linter  -*- lexical-binding: t; -*-

;;; Commentary:

;; Pre-publish lint for works/games and works/music org sources.  Reports
;; org `FILE:LINE: message' strings, mirroring a3madkour-recipe-lint.el.
;;
;; The four enum vocabularies are NOT defined here.  They live in the site
;; repo at data/works-vocab.json and are shared with
;; tools/check_works_fixtures.py, so the two languages cannot drift.  A
;; missing or malformed vocabulary is an error, never a skipped check.

;;; Code:

(require 'a3madkour-publish-yaml)

(defvar a3madkour-works-lint-enabled t
  "When non-nil, the works handler runs this linter before publishing.")

(defconst a3madkour-works-lint--vocab-rel "data/works-vocab.json"
  "Vocabulary path, relative to the site root.")

(defconst a3madkour-works-lint--vocab-keys
  '("game_statuses" "game_kinds" "music_formats" "platform_kinds")
  "Keys every vocabulary file must define.")

(defvar a3madkour-works-lint--vocab-cache nil
  "Cons of (PATH . ALIST) for the last vocabulary read, or nil.")

(defun a3madkour-works-lint--read-vocab ()
  "Read and validate the vocabulary.  Signal `error' on any problem."
  (let ((path (expand-file-name a3madkour-works-lint--vocab-rel
                                (a3madkour-pub-yaml/site-root))))
    (if (and a3madkour-works-lint--vocab-cache
             (equal (car a3madkour-works-lint--vocab-cache) path))
        (cdr a3madkour-works-lint--vocab-cache)
      (unless (file-exists-p path)
        (error "a3madkour-works-lint: vocabulary not found at %s" path))
      (let* ((text (with-temp-buffer (insert-file-contents path) (buffer-string)))
             (parsed (condition-case err
                         (json-parse-string text :object-type 'alist
                                                 :array-type 'list)
                       (error
                        (error "a3madkour-works-lint: vocabulary at %s is not valid JSON: %S"
                               path err)))))
        (dolist (k a3madkour-works-lint--vocab-keys)
          (unless (assoc k parsed)
            (error "a3madkour-works-lint: vocabulary at %s missing key %s" path k)))
        (setq a3madkour-works-lint--vocab-cache (cons path parsed))
        parsed))))

(defun a3madkour-works-lint/vocab (key)
  "Return the list of allowed values for KEY (a string)."
  (unless (member key a3madkour-works-lint--vocab-keys)
    (error "a3madkour-works-lint: unknown vocabulary key %s" key))
  (cdr (assoc key (a3madkour-works-lint--read-vocab))))

(defun a3madkour-works-lint/lint-file (file)
  "Lint works FILE.  Return a list of \"FILE:LINE: message\" strings.
Rules are added in later tasks; this returns the empty list."
  (ignore file)
  nil)

(provide 'a3madkour-works-lint)

;;; a3madkour-works-lint.el ends here
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: PASS, **755 passing** (751 + 4).

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-works-lint.el emacs-configs/custom/lisp/a3madkour-works-lint-test.el
git commit -m "feat(works): elisp reader for the shared enum vocabulary (fail-closed)"
```

---

### Task 3: Tracks table parsing

**Files:**
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-works.el`
- Create: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-works-test.el`

**Interfaces:**
- Consumes: `org-element`.
- Produces: `(a3madkour-pub-works--parse-tracks AST)` → list of alists `((title . "Lorem One") (duration . "3:14"))`, or `nil` when the table is absent **or has no data rows**. Task 5 renders it; Task 7 injects it.

- [ ] **Step 1: Write the failing test**

`a3madkour-publish-works-test.el`:

```elisp
;;; a3madkour-publish-works-test.el --- tests for the works handler  -*- lexical-binding: t; -*-
(require 'ert)
(require 'a3madkour-publish-works)

(defun a3madkour-pub-works-test--parse (org-text)
  "Parse ORG-TEXT and return its element AST."
  (with-temp-buffer (insert org-text) (org-mode) (org-element-parse-buffer)))

(ert-deftest a3madkour-pub-works--module-loads ()
  (should (fboundp 'a3madkour-pub-works/publish-works-file)))

(ert-deftest a3madkour-pub-works--parse-tracks-basic ()
  (let* ((ast (a3madkour-pub-works-test--parse "
#+NAME: tracks
| title     | duration |
|-----------+----------|
| Lorem One | 3:14     |
| Lorem Two | 4:20     |
"))
         (tracks (a3madkour-pub-works--parse-tracks ast)))
    (should (equal (length tracks) 2))
    (should (equal (alist-get 'title (car tracks)) "Lorem One"))
    (should (equal (alist-get 'duration (car tracks)) "3:14"))
    (should (equal (alist-get 'duration (nth 1 tracks)) "4:20"))))

(ert-deftest a3madkour-pub-works--parse-tracks-absent-is-nil ()
  (should (null (a3madkour-pub-works--parse-tracks
                 (a3madkour-pub-works-test--parse "Just a body.")))))

;; Review Focus #4 — header row only must yield nil, not an empty list,
;; so the key is omitted rather than emitted as `tracks: []'.
(ert-deftest a3madkour-pub-works--parse-tracks-header-only-is-nil ()
  (should (null (a3madkour-pub-works--parse-tracks
                 (a3madkour-pub-works-test--parse "
#+NAME: tracks
| title | duration |
|-------+----------|
")))))

(ert-deftest a3madkour-pub-works--parse-tracks-trims-cells ()
  (let ((tracks (a3madkour-pub-works--parse-tracks
                 (a3madkour-pub-works-test--parse "
#+NAME: tracks
| title       | duration |
|-------------+----------|
|   Padded    |   1:05   |
"))))
    (should (equal (alist-get 'title (car tracks)) "Padded"))))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: FAIL — `a3madkour-publish-works` is not loadable.

- [ ] **Step 3: Write the module skeleton and the parser**

`a3madkour-publish-works.el`:

```elisp
;;; a3madkour-publish-works.el --- works/games + works/music publish handler  -*- lexical-binding: t; -*-

;;; Commentary:

;; Slice A1: one handler for two living sections.  Registered twice into
;; `a3madkour-pub-living--handlers' (works/games, works/music) against a
;; single entry point that branches on section.
;;
;; Authoring uses `#+HUGO_CUSTOM_FRONT_MATTER:' (the research idiom), NOT a
;; :PROPERTIES: drawer — see the design spec §3.  Only music's track list is
;; parsed from the AST, as an org table, mirroring recipes' ingredients.

;;; Code:

(require 'cl-lib)
(require 'org-element)

(defconst a3madkour-pub-works--track-cols '("title" "duration")
  "Required columns of the `#+NAME: tracks' table, in any order.")

(defun a3madkour-pub-works--named-table (ast name)
  "Return the table element in AST carrying `#+NAME: NAME', or nil."
  (org-element-map ast 'table
    (lambda (tbl)
      (when (string-equal (or (org-element-property :name tbl) "") name)
        tbl))
    nil t))

(defun a3madkour-pub-works--table-rows (table)
  "Return TABLE's non-rule rows as lists of trimmed cell strings."
  (when table
    (delq nil
          (org-element-map table 'table-row
            (lambda (row)
              (when (eq (org-element-property :type row) 'standard)
                (org-element-map row 'table-cell
                  (lambda (cell)
                    (string-trim
                     (substring-no-properties
                      (org-element-interpret-data
                       (org-element-contents cell))))))))))))

(defun a3madkour-pub-works--parse-tracks (ast)
  "Parse the `#+NAME: tracks' table in AST.

Returns a list of ((title . STR) (duration . STR)) alists, or nil when the
table is absent or carries only a header row.  Returning nil rather than an
empty list is deliberate: the caller omits the key entirely, so the page does
not render an empty track list."
  (let* ((table (a3madkour-pub-works--named-table ast "tracks"))
         (rows (a3madkour-pub-works--table-rows table)))
    (when (and rows (cdr rows))
      (let* ((header (mapcar #'downcase (car rows)))
             (ti (cl-position "title" header :test #'string-equal))
             (di (cl-position "duration" header :test #'string-equal)))
        (when (and ti di)
          (delq nil
                (mapcar (lambda (row)
                          (let ((title (nth ti row))
                                (duration (nth di row)))
                            (unless (and (or (null title) (string-empty-p title))
                                         (or (null duration) (string-empty-p duration)))
                              (list (cons 'title (or title ""))
                                    (cons 'duration (or duration ""))))))
                        (cdr rows)))))))

(defun a3madkour-pub-works/publish-works-file (file run &key on-done)
  "Publish a works FILE.  Filled in by Task 7."
  (ignore file run)
  (when on-done (funcall on-done 'err)))

(provide 'a3madkour-publish-works)

;;; a3madkour-publish-works.el ends here
```

Note: `publish-works-file` must be `cl-defun` once it takes `&key`; declare it as `(cl-defun a3madkour-pub-works/publish-works-file (file run &key on-done) ...)` and add `(require 'cl-lib)` (already present).

- [ ] **Step 4: Run tests to verify they pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: PASS, **760 passing** (755 + 5).

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-works.el emacs-configs/custom/lisp/a3madkour-publish-works-test.el
git commit -m "feat(works): parse the #+NAME: tracks org table"
```

---

### Task 4: Normalize branches for works-games and works-music

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el` (add two `cond` arms + two normalizers)
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el`

**Interfaces:**
- Consumes: `a3madkour-pub-frontmatter--coerce-slug-list`, `--parse-slug-list`, `--coerce-bool` (all existing).
- Produces: `(a3madkour-pub-frontmatter/normalize 'works-games RAW FILE)` and `'works-music` → normalized alists. `year` is an integer; `hero`/`featured` are booleans for music; comma fields are lists of trimmed strings; slug fields are lists of site paths; absent optionals produce **no key**.

`a3madkour-pub-frontmatter--known-sections` already contains `works-games` and `works-music`. Do not modify it.

- [ ] **Step 1: Write the failing test**

```elisp
(ert-deftest a3madkour-pub-frontmatter--works-games-comma-vs-whitespace ()
  "Review Focus: free-text lists split on comma, slug lists on whitespace."
  (let ((out (a3madkour-pub-frontmatter/normalize
              'works-games
              '((title . "G") (year . "2026")
                (collaborators . "Alice Example, Bob Example")
                (tech_stack . "Godot, GDScript")
                (research_questions . "example-question-one example-question-two"))
              "/tmp/g.org")))
    (should (equal (alist-get 'collaborators out) '("Alice Example" "Bob Example")))
    (should (equal (alist-get 'tech_stack out) '("Godot" "GDScript")))
    (should (equal (alist-get 'research_questions out)
                   '("/research/questions/example-question-one/"
                     "/research/questions/example-question-two/")))
    (should (equal (alist-get 'year out) 2026))))

(ert-deftest a3madkour-pub-frontmatter--works-music-bool-coercion ()
  "hero and featured must emit real booleans, not strings."
  (let ((out (a3madkour-pub-frontmatter/normalize
              'works-music
              '((title . "M") (year . "2026") (format . "album")
                (hero . "t") (featured . "t"))
              "/tmp/m.org")))
    (should (eq (alist-get 'hero out) t))
    (should (eq (alist-get 'featured out) t))))

;; Review Focus #1 — every optional absent must produce no keys at all.
(ert-deftest a3madkour-pub-frontmatter--works-games-minimal-emits-no-empty-keys ()
  (let ((out (a3madkour-pub-frontmatter/normalize
              'works-games
              '((title . "G") (year . "2026") (status . "playable")
                (game_kind . "jam") (tagline . "T"))
              "/tmp/g.org")))
    (dolist (k '(screenshots collaborators tech_stack hero featured
                 research_questions related_essays related_notes))
      (should-not (assq k out)))))

(ert-deftest a3madkour-pub-frontmatter--works-screenshots-stay-filenames ()
  "screenshots split on whitespace but are NOT expanded to site paths."
  (let ((out (a3madkour-pub-frontmatter/normalize
              'works-games
              '((title . "G") (year . "2026") (screenshots . "a.png b.png"))
              "/tmp/g.org")))
    (should (equal (alist-get 'screenshots out) '("a.png" "b.png")))))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: FAIL — normalize currently falls through to the B.0 pass-through, so `year` stays the string `"2026"`.

- [ ] **Step 3: Implement the normalizers**

Add to `a3madkour-publish-frontmatter.el`:

```elisp
(defconst a3madkour-pub-frontmatter--works-comma-keys
  '(collaborators tech_stack made_with)
  "Works list keys holding free text, split on comma rather than whitespace.
A collaborator named \"Alice Example\" is one person, not two.")

(defconst a3madkour-pub-frontmatter--works-path-keys
  '((research_questions . "/research/questions/%s/")
    (related_essays     . "/essays/%s/")
    (related_notes      . "/garden/%s/")
    (related_works      . "/works/%s/"))
  "Works slug-list keys and the site-path template each expands to.")

(defun a3madkour-pub-frontmatter--split-commas (raw)
  "Split RAW on commas, trimming each field.  Drops empty fields."
  (cond
   ((null raw) nil)
   ((listp raw) raw)
   ((stringp raw)
    (delq nil (mapcar (lambda (s)
                        (let ((t* (string-trim s)))
                          (unless (string-empty-p t*) t*)))
                      (split-string raw "," t))))
   (t nil)))

(defun a3madkour-pub-frontmatter--normalize-works-common (raw file)
  "Normalization shared by works-games and works-music."
  (let ((out (copy-alist raw)))
    ;; year → integer (check_works_fixtures.py rejects a string).
    (let ((y (alist-get 'year out)))
      (when (stringp y) (setf (alist-get 'year out) (string-to-number y))))
    ;; Free-text lists split on comma.
    (dolist (k a3madkour-pub-frontmatter--works-comma-keys)
      (when (assq k out)
        (let ((v (a3madkour-pub-frontmatter--split-commas (alist-get k out))))
          (if v (setf (alist-get k out) v) (setq out (assq-delete-all k out))))))
    ;; Slug lists split on whitespace and expand to site paths.
    (dolist (cell a3madkour-pub-frontmatter--works-path-keys)
      (let ((k (car cell)) (tmpl (cdr cell)))
        (when (assq k out)
          (let ((slugs (a3madkour-pub-frontmatter--coerce-slug-list (alist-get k out))))
            (if slugs
                (setf (alist-get k out)
                      (mapcar (lambda (s) (format tmpl s)) slugs))
              (setq out (assq-delete-all k out)))))))
    ;; featured is a bool on both types.
    (when (assq 'featured out)
      (setf (alist-get 'featured out)
            (a3madkour-pub-frontmatter--coerce-bool (alist-get 'featured out))))
    (ignore file)
    out))

(defun a3madkour-pub-frontmatter--normalize-works-games (raw file)
  "Normalize a works-games RAW alist.  `hero' is a FILENAME here."
  (let ((out (a3madkour-pub-frontmatter--normalize-works-common raw file)))
    ;; screenshots: whitespace-split, left as bare filenames (no path expansion).
    (when (assq 'screenshots out)
      (let ((v (a3madkour-pub-frontmatter--coerce-slug-list (alist-get 'screenshots out))))
        (if v (setf (alist-get 'screenshots out) v)
          (setq out (assq-delete-all 'screenshots out)))))
    out))

(defun a3madkour-pub-frontmatter--normalize-works-music (raw file)
  "Normalize a works-music RAW alist.  `hero' is a BOOL here (Bento directive)."
  (let ((out (a3madkour-pub-frontmatter--normalize-works-common raw file)))
    (when (assq 'hero out)
      (setf (alist-get 'hero out)
            (a3madkour-pub-frontmatter--coerce-bool (alist-get 'hero out))))
    out))
```

Add two arms to the `cond` in `a3madkour-pub-frontmatter/normalize`, directly after the `works-poetry` arm:

```elisp
   ((eq section 'works-games)
    (a3madkour-pub-frontmatter--normalize-works-games raw-alist source-file))
   ((eq section 'works-music)
    (a3madkour-pub-frontmatter--normalize-works-music raw-alist source-file))
```

Note on `--coerce-bool`: confirm its nil-return contract before relying on it. If it returns nil for a *false* value, `(setf (alist-get 'hero out) nil)` leaves the key present with value nil; the renderer must then omit it. If that is the behaviour, delete the key instead of setting nil.

- [ ] **Step 4: Run tests to verify they pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: PASS, **764 passing** (760 + 4).

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el
git commit -m "feat(works): normalize branches for works-games and works-music"
```

---

### Task 5: Frontmatter rendering for tracks and platform_embed

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-works.el`
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-works-test.el`

**Interfaces:**
- Consumes: `a3madkour-pub-yaml/render-frontmatter` (`&key key-hook value-fn`), `a3madkour-pub/yaml-escape-scalar`, Task 3's track alists.
- Produces: `(a3madkour-pub-works--render-frontmatter ALIST)` → a `---`-delimited YAML string.

- [ ] **Step 1: Write the failing test**

```elisp
(ert-deftest a3madkour-pub-works--renders-tracks-block ()
  (let ((out (a3madkour-pub-works--render-frontmatter
              '((title . "M")
                (tracks . (((title . "Lorem One") (duration . "3:14"))
                           ((title . "Lorem Two") (duration . "4:20"))))))))
    (should (string-match-p "tracks:\n" out))
    (should (string-match-p
             "  - { title: \"Lorem One\", duration: \"3:14\" }" out))
    (should (string-match-p
             "  - { title: \"Lorem Two\", duration: \"4:20\" }" out))))

(ert-deftest a3madkour-pub-works--renders-platform-embed-map ()
  (let ((out (a3madkour-pub-works--render-frontmatter
              '((title . "M")
                (platform_embed . ((kind . "bandcamp")
                                   (url . "https://example.bandcamp.com/album/x")))))))
    (should (string-match-p
             "platform_embed: { kind: bandcamp, url: \"https://example.bandcamp.com/album/x\" }"
             out))))

(ert-deftest a3madkour-pub-works--omits-empty-structured-keys ()
  (let ((out (a3madkour-pub-works--render-frontmatter
              '((title . "M") (tracks . nil) (platform_embed . nil)))))
    (should-not (string-match-p "tracks:" out))
    (should-not (string-match-p "platform_embed:" out))))

(ert-deftest a3madkour-pub-works--escapes-quotes-in-track-titles ()
  (let ((out (a3madkour-pub-works--render-frontmatter
              '((title . "M")
                (tracks . (((title . "He said \"hi\"") (duration . "1:00"))))))))
    (should-not (string-match-p "title: \"He said \"hi\"\"" out))))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: FAIL — `a3madkour-pub-works--render-frontmatter` is not defined.

- [ ] **Step 3: Implement the key-hook and renderer**

Add to `a3madkour-publish-works.el`, with `(require 'a3madkour-publish-yaml)` and `(require 'a3madkour-publish)` at the top:

```elisp
(defun a3madkour-pub-works--render-track (track)
  "Render one TRACK alist as an inline flow map."
  (format "  - { title: \"%s\", duration: \"%s\" }"
          (a3madkour-pub/yaml-escape-scalar (or (alist-get 'title track) ""))
          (a3madkour-pub/yaml-escape-scalar (or (alist-get 'duration track) ""))))

(defun a3madkour-pub-works--render-platform-embed (pe)
  "Render PLATFORM-EMBED alist PE as an inline flow map.
`kind' is a closed enum so it is emitted bare; `url' is quoted."
  (format "platform_embed: { kind: %s, url: \"%s\" }"
          (or (alist-get 'kind pe) "")
          (a3madkour-pub/yaml-escape-scalar (or (alist-get 'url pe) ""))))

(defun a3madkour-pub-works--key-hook (k v)
  "render-frontmatter KEY-HOOK for the two structured works keys."
  (cond
   ((eq k 'tracks)
    (if (and v (listp v))
        (format "tracks:\n%s"
                (mapconcat #'a3madkour-pub-works--render-track v "\n"))
      :omit))
   ((eq k 'platform_embed)
    (if (and v (listp v))
        (a3madkour-pub-works--render-platform-embed v)
      :omit))))

(defun a3madkour-pub-works--render-frontmatter (alist)
  "Render ALIST as works frontmatter (structured keys via the key-hook)."
  (a3madkour-pub-yaml/render-frontmatter
   alist
   :key-hook #'a3madkour-pub-works--key-hook
   :value-fn #'a3madkour-pub-yaml/render-value))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: PASS, **768 passing** (764 + 4).

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-works.el emacs-configs/custom/lisp/a3madkour-publish-works-test.el
git commit -m "feat(works): render tracks and platform_embed as flow-style YAML"
```

---

### Task 6: `extra-refs` on asset-validate-and-copy

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets.el:501-568`
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-assets-test.el`

**Interfaces:**
- Consumes: nothing new.
- Produces: `(a3madkour-pub/asset-validate-and-copy ORG-FILE BUNDLE-DEST-DIR &optional SOURCE-NOTE-ID DRY-RUN EXTRA-REFS)`. `EXTRA-REFS` is a list of bare filenames resolved under `<org-dir>/assets/<source-note-id>/`. They are copied into the bundle **and** added to the cleanup-stale keep-set. Defaults to nil, so all five existing callers are unaffected.

- [ ] **Step 1: Write the failing test**

```elisp
(ert-deftest a3madkour-pub-assets--extra-refs-copied-and-kept ()
  "A frontmatter-declared asset must land in the bundle AND survive cleanup-stale."
  (let* ((root (make-temp-file "a3-assets-extra" t))
         (org-dir (expand-file-name "notes/" root))
         (asset-dir (expand-file-name "notes/assets/ID-1/" root))
         (bundle (expand-file-name "bundle/" root))
         (org-file (expand-file-name "g.org" org-dir)))
    (unwind-protect
        (progn
          (make-directory asset-dir t)
          (make-directory bundle t)
          (with-temp-file org-file (insert "#+TITLE: G\n\nBody with no asset links.\n"))
          (with-temp-file (expand-file-name "shot-1.png" asset-dir) (insert "png"))
          (a3madkour-pub/asset-validate-and-copy org-file bundle "ID-1" nil '("shot-1.png"))
          (should (file-exists-p (expand-file-name "shot-1.png" bundle))))
      (delete-directory root t))))

(ert-deftest a3madkour-pub-assets--extra-refs-missing-source-is-an-error ()
  (let* ((root (make-temp-file "a3-assets-extra" t))
         (org-dir (expand-file-name "notes/" root))
         (bundle (expand-file-name "bundle/" root))
         (org-file (expand-file-name "g.org" org-dir)))
    (unwind-protect
        (progn
          (make-directory org-dir t) (make-directory bundle t)
          (with-temp-file org-file (insert "#+TITLE: G\n"))
          (let ((res (a3madkour-pub/asset-validate-and-copy
                      org-file bundle "ID-1" nil '("missing.png"))))
            (should (plist-get res :errors))))
      (delete-directory root t))))

(ert-deftest a3madkour-pub-assets--extra-refs-defaults-nil-unchanged ()
  "Existing three-argument callers must behave exactly as before."
  (let* ((root (make-temp-file "a3-assets-extra" t))
         (org-dir (expand-file-name "notes/" root))
         (bundle (expand-file-name "bundle/" root))
         (org-file (expand-file-name "g.org" org-dir)))
    (unwind-protect
        (progn
          (make-directory org-dir t) (make-directory bundle t)
          (with-temp-file org-file (insert "#+TITLE: G\n"))
          (let ((res (a3madkour-pub/asset-validate-and-copy org-file bundle "ID-1")))
            (should-not (plist-get res :errors))))
      (delete-directory root t))))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: FAIL — the function takes four arguments; the five-argument call signals `wrong-number-of-arguments`.

- [ ] **Step 3: Add the parameter and the copy loop**

Change the signature at `a3madkour-publish-assets.el:501`:

```elisp
(defun a3madkour-pub/asset-validate-and-copy
    (org-file bundle-dest-dir &optional source-note-id dry-run extra-refs)
```

Extend the docstring with:

```
EXTRA-REFS is a list of bare filenames declared in frontmatter rather than
linked from the body.  Each resolves to <org-dir>/assets/<SOURCE-NOTE-ID>/<name>.
They are copied into BUNDLE-DEST-DIR and added to the cleanup-stale keep-set,
so they are not deleted as strays.  This exists because `--extract-asset-refs'
scans body links only; without it a frontmatter-declared asset is either never
copied (recipes bug #4) or copied and then removed by cleanup-stale unless the
caller carefully orders its copy after this call (poetry's audio constraint).
```

Insert immediately **before** the `(let ((removed ...)))` form:

```elisp
    ;; Frontmatter-declared assets: copy, and register so cleanup-stale keeps them.
    (dolist (name extra-refs)
      (let* ((basename (file-name-nondirectory name))
             (src (expand-file-name
                   basename
                   (expand-file-name (format "assets/%s/" (or source-note-id ""))
                                     (file-name-directory org-file))))
             (dest (expand-file-name basename bundle-dest-dir)))
        (cond
         ((not (file-exists-p src))
          (push (format "extra-ref not found: %s" src) errors))
         (dry-run nil)
         (t
          (make-directory (file-name-directory dest) t)
          (condition-case err
              (progn
                (copy-file src dest t)
                (push dest copied)
                (push basename referenced-basenames))
            (error
             (push (format "copy failed: %s -> %s (%S)" src dest err) errors)))))))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: PASS, **771 passing** (768 + 3). All pre-existing asset tests still pass, proving the parameter is additive.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-assets.el emacs-configs/custom/lisp/a3madkour-publish-assets-test.el
git commit -m "feat(assets): extra-refs so frontmatter assets join the keep-set"
```

---

### Task 7: Handler entry point and living registration

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-works.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el` (registration at the bottom)
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-works-test.el`

**Interfaces:**
- Consumes: Tasks 3, 4, 5, 6; `a3madkour-pub/note-metadata`, `note-slug`, `note-url`, `note-section`; `a3madkour-pub-rewrite/rewrite-to-tmp-file`; `a3madkour-pub-export/export-file`; `a3madkour-pub-history/recorded-last-modified`, `record-publish`; `a3madkour-pub-yaml/site-root`, `write-if-different`.
- Produces: `(a3madkour-pub-works/publish-works-file FILE RUN &key ON-DONE)` calling `ON-DONE` exactly once with `'ok` or `'err`; and `(a3madkour-pub-works/planned-steps FILE)` → 3.

- [ ] **Step 1: Write the failing test**

```elisp
(ert-deftest a3madkour-pub-works--registers-both-sections ()
  (require 'a3madkour-publish-living)
  (require 'a3madkour-publish-works)
  (should (equal (cdr (assoc "works/games" a3madkour-pub-living--handlers))
                 'a3madkour-pub-works/publish-works-file))
  (should (equal (cdr (assoc "works/music" a3madkour-pub-living--handlers))
                 'a3madkour-pub-works/publish-works-file)))

(ert-deftest a3madkour-pub-works--bundle-dir-for-section ()
  (should (equal (a3madkour-pub-works--bundle-subdir "works/games") "works/games"))
  (should (equal (a3madkour-pub-works--bundle-subdir "works/music") "works/music"))
  (should-error (a3madkour-pub-works--bundle-subdir "works/poetry")))

(ert-deftest a3madkour-pub-works--normalize-symbol-for-section ()
  "Two-symbol convention: slash on the wire, hyphen into normalize."
  (should (eq (a3madkour-pub-works--normalize-symbol "works/games") 'works-games))
  (should (eq (a3madkour-pub-works--normalize-symbol "works/music") 'works-music)))

;; Review Focus #3 — two titles that slugify identically must not silently
;; overwrite one another.
(ert-deftest a3madkour-pub-works--duplicate-slug-is-refused ()
  (let ((seen (make-hash-table :test #'equal)))
    (should (a3madkour-pub-works--claim-slug seen "mnemosyne" "/tmp/a.org"))
    (should-error (a3madkour-pub-works--claim-slug seen "mnemosyne" "/tmp/b.org"))))

;; Review Focus #5 — section set but publish flag absent must not publish.
(ert-deftest a3madkour-pub-works--unmarked-file-is-not-collected ()
  (let* ((dir (make-temp-file "a3-works-unmarked" t))
         (f (expand-file-name "g.org" dir)))
    (unwind-protect
        (progn
          (with-temp-file f
            (insert "#+TITLE: G\n#+HUGO_SECTION: works/games\n"))
          (should-not (equal (a3madkour-pub/note-section f) "works/games")))
      (delete-directory dir t))))
```

If `note-section` returns the section regardless of the publish flag, replace the final assertion with one against whatever predicate `collect-triples` relies on, and record the finding — an unmarked file reaching a handler would be a real defect.

- [ ] **Step 2: Run test to verify it fails**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: FAIL — neither the helpers nor the registration exist.

- [ ] **Step 3: Implement the helpers and the entry point**

```elisp
(defconst a3madkour-pub-works--sections
  '(("works/games" . works-games)
    ("works/music" . works-music))
  "Sections this handler serves, mapping the slash form to the hyphen form.")

(defun a3madkour-pub-works--bundle-subdir (section)
  "Content subdirectory for SECTION.  Signals for an unserved section."
  (unless (assoc section a3madkour-pub-works--sections)
    (error "a3madkour-pub-works: unserved section %S" section))
  section)

(defun a3madkour-pub-works--normalize-symbol (section)
  "Hyphen-form normalize symbol for slash-form SECTION."
  (or (cdr (assoc section a3madkour-pub-works--sections))
      (error "a3madkour-pub-works: unserved section %S" section)))

(defun a3madkour-pub-works--claim-slug (table slug file)
  "Claim SLUG in TABLE for FILE.  Signals when SLUG is already taken.
Two org titles that slugify identically would otherwise write the same
bundle, and the second would silently overwrite the first."
  (let ((prior (gethash slug table)))
    (when (and prior (not (equal prior file)))
      (error "a3madkour-pub-works: slug %S claimed by both %s and %s"
             slug prior file))
    (puthash slug file table)
    t))

(defvar a3madkour-pub-works--slugs-seen (make-hash-table :test #'equal)
  "Slug → file, for the duration of one publish run.")

(defun a3madkour-pub-works--asset-names (section fm)
  "Bare asset filenames declared in frontmatter FM for SECTION."
  (let ((names '()))
    (pcase section
      ("works/games"
       (when-let ((h (alist-get 'hero fm))) (when (stringp h) (push h names)))
       (dolist (s (alist-get 'screenshots fm)) (push s names)))
      ("works/music"
       (when-let ((c (alist-get 'cover fm))) (when (stringp c) (push c names)))))
    (nreverse names)))

(cl-defun a3madkour-pub-works/publish-works-file (file run &key on-done)
  "Publish a works/games or works/music FILE to content/works/<type>/<slug>/index.md.
Pipeline: lint → parse tracks → rewrite links → ox-hugo → normalize →
inject tracks → render → asset-copy → write-if-different → record-publish."
  (ignore run)
  (condition-case err
      (progn
        (when a3madkour-works-lint-enabled
          (let ((errs (a3madkour-works-lint/lint-file file)))
            (when errs
              (error "a3madkour-pub-works: lint failed for %s:\n%s"
                     file (mapconcat #'identity errs "\n")))))
        (let* ((section   (a3madkour-pub/note-section file))
               (subdir    (a3madkour-pub-works--bundle-subdir section))
               (nsym      (a3madkour-pub-works--normalize-symbol section))
               (md        (a3madkour-pub/note-metadata file))
               (id        (plist-get md :id))
               (slug      (a3madkour-pub/note-slug file))
               (new-url   (a3madkour-pub/note-url file))
               (site-root (a3madkour-pub-yaml/site-root))
               (bundle-dir (expand-file-name
                            (format "content/%s/%s/" subdir slug) site-root))
               (out-path   (expand-file-name "index.md" bundle-dir))
               (src-ast    (with-temp-buffer
                             (insert-file-contents file) (org-mode)
                             (org-element-parse-buffer)))
               (tmp-src    (a3madkour-pub-rewrite/rewrite-to-tmp-file
                            file id "a3-pub-works"))
               (exported   (unwind-protect
                               (a3madkour-pub-export/export-file tmp-src)
                             (when (file-exists-p tmp-src) (delete-file tmp-src))))
               (normalized (let ((a3madkour-pub-frontmatter--prior-last-modified
                                  (a3madkour-pub-history/recorded-last-modified id new-url)))
                             (a3madkour-pub-frontmatter/normalize
                              nsym (plist-get exported :frontmatter) file)))
               (final-fm   (let ((out (copy-alist normalized)))
                             (when (eq nsym 'works-music)
                               (when-let ((tr (a3madkour-pub-works--parse-tracks src-ast)))
                                 (setf (alist-get 'tracks out) tr)))
                             out))
               (body       (plist-get exported :body)))
          (a3madkour-pub-works--claim-slug a3madkour-pub-works--slugs-seen slug file)
          (a3madkour-pub/asset-validate-and-copy
           file bundle-dir id nil
           (a3madkour-pub-works--asset-names section final-fm))
          (a3madkour-pub-yaml/write-if-different
           out-path
           (concat (a3madkour-pub-works--render-frontmatter final-fm) body))
          (a3madkour-pub-history/record-publish
           id new-url (or (plist-get md :state) 'live)
           :last-modified (alist-get 'lastmod final-fm)))
        (when on-done (funcall on-done 'ok)))
    (error
     (message "%s" (error-message-string err))
     (when on-done (funcall on-done 'err)))))

(defun a3madkour-pub-works/planned-steps (_file)
  "Return rough step count for the works handler."
  3)
```

- [ ] **Step 4: Register both sections**

At the bottom of `a3madkour-publish-living.el`, after the recipes block:

```elisp
;; Slice A1: works/games + works/music registration (one entry point, two
;; sections — mirrors library.el's four media and research.el's two types).
(with-eval-after-load 'a3madkour-publish-works
  (dolist (section '("works/games" "works/music"))
    (add-to-list 'a3madkour-pub-living--handlers
                 (cons section 'a3madkour-pub-works/publish-works-file))))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: PASS, **776 passing** (771 + 5).

- [ ] **Step 6: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-works.el emacs-configs/custom/lisp/a3madkour-publish-living.el emacs-configs/custom/lisp/a3madkour-publish-works-test.el
git commit -m "feat(works): handler entry point + living registration for games and music"
```

---

### Task 8: Lint rules — required keys, enums, assets, hero polymorphism

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-works-lint.el`
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-works-lint-test.el`

**Interfaces:**
- Consumes: `a3madkour-works-lint/vocab` (Task 2); `a3madkour-pub/note-section`.
- Produces: `(a3madkour-works-lint/lint-file FILE)` → list of `"FILE:LINE: message"` strings, empty when clean.

- [ ] **Step 1: Write the failing test**

```elisp
(defun a3madkour-works-lint-test--file (text)
  "Write TEXT to a temp .org file and return its path."
  (let ((f (make-temp-file "a3-works-lint" nil ".org")))
    (with-temp-file f (insert text)) f))

(ert-deftest a3madkour-works-lint--rejects-unknown-status ()
  (let ((f (a3madkour-works-lint-test--file "#+TITLE: G
#+HUGO_SECTION: works/games
#+HUGO_CUSTOM_FRONT_MATTER: :status playible :game_kind jam :year 2026 :tagline T
")))
    (unwind-protect
        (let ((errs (a3madkour-works-lint/lint-file f)))
          (should (cl-some (lambda (e) (string-match-p "status" e)) errs)))
      (delete-file f))))

(ert-deftest a3madkour-works-lint--rejects-missing-required-key ()
  (let ((f (a3madkour-works-lint-test--file "#+TITLE: G
#+HUGO_SECTION: works/games
#+HUGO_CUSTOM_FRONT_MATTER: :status playable :year 2026 :tagline T
")))
    (unwind-protect
        (let ((errs (a3madkour-works-lint/lint-file f)))
          (should (cl-some (lambda (e) (string-match-p "game_kind" e)) errs)))
      (delete-file f))))

(ert-deftest a3madkour-works-lint--rejects-filename-in-music-hero ()
  "hero is a bool for music and a filename for games."
  (let ((f (a3madkour-works-lint-test--file "#+TITLE: M
#+HUGO_SECTION: works/music
#+HUGO_CUSTOM_FRONT_MATTER: :format album :year 2026 :hero cover.png
")))
    (unwind-protect
        (let ((errs (a3madkour-works-lint/lint-file f)))
          (should (cl-some (lambda (e) (string-match-p "hero" e)) errs)))
      (delete-file f))))

(ert-deftest a3madkour-works-lint--rejects-bool-in-games-hero ()
  (let ((f (a3madkour-works-lint-test--file "#+TITLE: G
#+HUGO_SECTION: works/games
#+HUGO_CUSTOM_FRONT_MATTER: :status playable :game_kind jam :year 2026 :tagline T :hero t
")))
    (unwind-protect
        (let ((errs (a3madkour-works-lint/lint-file f)))
          (should (cl-some (lambda (e) (string-match-p "hero" e)) errs)))
      (delete-file f))))

;; Review Focus #2 — a space inside a screenshot filename silently becomes
;; two broken names under whitespace splitting.
(ert-deftest a3madkour-works-lint--rejects-space-in-asset-filename ()
  (let ((f (a3madkour-works-lint-test--file "#+TITLE: G
#+HUGO_SECTION: works/games
#+HUGO_CUSTOM_FRONT_MATTER: :status playable :game_kind jam :year 2026 :tagline T
#+HUGO_CUSTOM_FRONT_MATTER: :screenshots \"my shot.png\"
")))
    (unwind-protect
        (let ((errs (a3madkour-works-lint/lint-file f)))
          (should (cl-some (lambda (e) (string-match-p "space" e)) errs)))
      (delete-file f))))

(ert-deftest a3madkour-works-lint--clean-file-has-no-errors ()
  (let ((f (a3madkour-works-lint-test--file "#+TITLE: G
#+HUGO_SECTION: works/games
#+HUGO_CUSTOM_FRONT_MATTER: :status playable :game_kind jam :year 2026 :tagline T
")))
    (unwind-protect
        (should (null (a3madkour-works-lint/lint-file f)))
      (delete-file f))))
```

Each of these must run against a vocabulary. Wrap every body in the Task 2 macro with the real values, so the tests never depend on a sibling checkout being present:

```elisp
(defconst a3madkour-works-lint-test--vocab
  "{\"game_statuses\":[\"playable\",\"in-progress\",\"archived\"],
    \"game_kinds\":[\"full-release\",\"jam\",\"research-prototype\",\"experiment\"],
    \"music_formats\":[\"album\",\"track\",\"experiment\",\"live\"],
    \"platform_kinds\":[\"bandcamp\",\"soundcloud\",\"youtube\"]}")

;; e.g.
(ert-deftest a3madkour-works-lint--rejects-unknown-status ()
  (a3madkour-works-lint-test--with-vocab a3madkour-works-lint-test--vocab
    (let ((f (a3madkour-works-lint-test--file "...")))
      (unwind-protect
          (should (cl-some (lambda (e) (string-match-p "status" e))
                           (a3madkour-works-lint/lint-file f)))
        (delete-file f)))))
```

Also clear the cache between tests, since `--vocab-cache` keys on path and two temp roots can collide within one run: add `(setq a3madkour-works-lint--vocab-cache nil)` at the top of the macro body in Task 2.

- [ ] **Step 2: Run test to verify it fails**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: FAIL — `lint-file` is the Task 2 stub and returns nil for everything.

- [ ] **Step 3: Implement the rules**

Add the keyword reader, the plist parser and the rules. `--kw` mirrors `a3madkour-recipe-lint--kw`:

```elisp
(defconst a3madkour-works-lint--required
  '((works-games . (status game_kind tagline year))
    (works-music . (format year)))
  "Required `#+HUGO_CUSTOM_FRONT_MATTER' keys per section.
title/date/lastmod/draft come from ox-hugo and are not authored here.")

(defun a3madkour-works-lint--kw (ast name)
  "Value of keyword NAME (upcased) in AST, or nil."
  (org-element-map ast 'keyword
    (lambda (kw)
      (when (string-equal (upcase (org-element-property :key kw)) name)
        (org-element-property :value kw)))
    nil t))

(defun a3madkour-works-lint--parse-plist (s)
  "Parse `:key value :key \"quoted value\"' string S into ((SYMBOL . STRING) ...)."
  (let ((pos 0) (len (length s)) (out '()))
    (while (and (< pos len)
                (string-match ":\\([A-Za-z0-9_-]+\\)[ \t]+" s pos))
      (let* ((key (intern (match-string 1 s)))
             (vstart (match-end 0)))
        (if (and (< vstart len) (eq (aref s vstart) ?\"))
            (let ((end (string-match "\"" s (1+ vstart))))
              (push (cons key (substring s (1+ vstart) (or end len))) out)
              (setq pos (if end (1+ end) len)))
          (let ((end (or (string-match "[ \t]+:[A-Za-z0-9_-]+[ \t]" s vstart) len)))
            (push (cons key (string-trim (substring s vstart end))) out)
            (setq pos end)))))
    (nreverse out)))

(defun a3madkour-works-lint--cfm-cells (ast)
  "Merged custom-front-matter cells as ((KEY VALUE . LINE) ...), later lines winning."
  (let ((cells '()))
    (org-element-map ast 'keyword
      (lambda (kw)
        (when (string-equal (upcase (org-element-property :key kw))
                            "HUGO_CUSTOM_FRONT_MATTER")
          (let ((line (line-number-at-pos (org-element-property :begin kw))))
            (dolist (pair (a3madkour-works-lint--parse-plist
                           (or (org-element-property :value kw) "")))
              (setf (alist-get (car pair) cells) (cons (cdr pair) line)))))))
    cells))

(defun a3madkour-works-lint--looks-like-filename-p (v)
  "Non-nil when V has a file extension."
  (and (stringp v) (string-match-p "\\.[A-Za-z0-9]+\\'" v)))

(defun a3madkour-works-lint/lint-file (file)
  "Lint works FILE.  Return a list of \"FILE:LINE: message\" strings (empty = clean)."
  (with-temp-buffer
    (insert-file-contents file)
    (org-mode)
    (let* ((ast     (org-element-parse-buffer))
           (base    (file-name-nondirectory file))
           (section (a3madkour-works-lint--kw ast "HUGO_SECTION"))
           (errs    '()))
      (when (member section '("works/games" "works/music"))
        (let* ((games-p (string-equal section "works/games"))
               (sym     (if games-p 'works-games 'works-music))
               (cells   (a3madkour-works-lint--cfm-cells ast))
               (id      (a3madkour-works-lint--kw ast "ID"))
               (asset-dir (expand-file-name
                           (format "assets/%s/" (or id ""))
                           (file-name-directory file))))
          (cl-flet* ((val (k) (car (alist-get k cells)))
                     (ln  (k) (or (cdr (alist-get k cells)) 1))
                     (add (k fmt &rest args)
                          (push (format "%s:%d: %s" base (ln k)
                                        (apply #'format fmt args))
                                errs)))
            ;; 1 — required keys
            (dolist (k (cdr (assq sym a3madkour-works-lint--required)))
              (unless (alist-get k cells)
                (push (format "%s:1: missing required key :%s" base k) errs)))
            ;; 2 — enum membership, against the shared vocabulary
            (dolist (spec (if games-p
                              '((status . "game_statuses") (game_kind . "game_kinds"))
                            '((format . "music_formats"))))
              (let ((v (val (car spec))))
                (when v
                  (let ((allowed (a3madkour-works-lint/vocab (cdr spec))))
                    (unless (member v allowed)
                      (add (car spec) ":%s=%S not in %S" (car spec) v allowed))))))
            ;; 3 — hero polymorphism: filename for games, bool for music
            (let ((h (val 'hero)))
              (when h
                (if games-p
                    (unless (a3madkour-works-lint--looks-like-filename-p h)
                      (add 'hero ":hero must be a filename for works/games, got %S" h))
                  (when (a3madkour-works-lint--looks-like-filename-p h)
                    (add 'hero ":hero must be a boolean for works/music, got %S" h)))))
            ;; 4 — asset filenames: no whitespace, and present on disk
            (dolist (k (if games-p '(hero screenshots) '(cover)))
              (let ((raw (val k)))
                (when (and raw (or (not (eq k 'hero)) games-p))
                  (dolist (name (split-string raw "[ \t]+" t))
                    (cond
                     ((string-match-p "[ \t]" name)
                      (add k ":%s entry %S contains a space" k name))
                     ((not (file-exists-p (expand-file-name name asset-dir)))
                      (add k ":%s entry %S not found in %s" k name asset-dir)))))))
            ;; A quoted multi-word filename survives `val' intact, so catch it
            ;; before the split above can hide it as two names.
            (dolist (k (if games-p '(hero screenshots) '(cover)))
              (let ((raw (val k)))
                (when (and raw (string-match-p "[^ \t]\\(?:[ \t]\\)[^ \t]*\\.[A-Za-z0-9]+\\'" raw)
                           (not (string-match-p "\\`[^ \t]+\\'" raw)))
                  (add k ":%s value %S contains a space; filenames may not" k raw))))))
        (setq errs (nreverse errs)))
      errs)))
```

Note the two-part space check: `screenshots "my shot.png"` arrives as one string and would be split into two plausible-looking names, so the second pass catches a value whose whitespace sits *inside* what is clearly one filename.

- [ ] **Step 4: Run tests to verify they pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: PASS, **782 passing** (776 + 6).

- [ ] **Step 5: Mutation-check the vocabulary coupling**

Temporarily point the test vocab's `game_statuses` at `["archived"]` and re-run `a3madkour-works-lint--clean-file-has-no-errors`.
Expected: it now FAILS, proving the enum check reads the vocabulary rather than a hardcoded list. Revert.

- [ ] **Step 6: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-works-lint.el emacs-configs/custom/lisp/a3madkour-works-lint-test.el
git commit -m "feat(works): lint required keys, enums, hero polymorphism and assets"
```

---

### Task 9: Symmetry lint for lyrics_poem ↔ set_to_music

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-works-lint.el`
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-works.el` (stale-bundle warning)
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-works-lint-test.el`

**Interfaces:**
- Consumes: Task 8's lint accumulation; `a3madkour-pub/poetry-dir`.
- Produces: an additional lint error class, and `(a3madkour-pub-works--warn-stale-backlink SLUG BUNDLE-DIR)` emitting a `a3madkour-pub/warn` naming the republish command.

- [ ] **Step 1: Write the failing test**

```elisp
(ert-deftest a3madkour-works-lint--requires-reciprocal-set-to-music ()
  "A music item claiming a poem must find set_to_music in that poem's org."
  (let* ((dir (make-temp-file "a3-works-sym" t))
         (poem (expand-file-name "tessellations.org" dir))
         (music (a3madkour-works-lint-test--file
                 (format "#+TITLE: M
#+HUGO_SECTION: works/music
#+HUGO_CUSTOM_FRONT_MATTER: :format album :year 2026 :lyrics_poem tessellations
"))))
    (unwind-protect
        (progn
          (with-temp-file poem (insert "#+TITLE: Tessellations\n#+HUGO_SECTION: works/poetry\n"))
          (let ((a3madkour-pub/poetry-dir dir))
            (let ((errs (a3madkour-works-lint/lint-file music)))
              (should (cl-some (lambda (e) (string-match-p "set_to_music" e)) errs)))))
      (delete-file music) (delete-directory dir t))))

(ert-deftest a3madkour-works-lint--accepts-reciprocal-set-to-music ()
  (let* ((dir (make-temp-file "a3-works-sym" t))
         (poem (expand-file-name "tessellations.org" dir))
         (music (a3madkour-works-lint-test--file "#+TITLE: M
#+HUGO_SECTION: works/music
#+HUGO_CUSTOM_FRONT_MATTER: :format album :year 2026 :lyrics_poem tessellations
")))
    (unwind-protect
        (progn
          (with-temp-file poem
            (insert "#+TITLE: Tessellations
#+HUGO_SECTION: works/poetry
#+HUGO_CUSTOM_FRONT_MATTER: :set_to_music m
"))
          (let ((a3madkour-pub/poetry-dir dir))
            (should-not (cl-some (lambda (e) (string-match-p "set_to_music" e))
                                 (a3madkour-works-lint/lint-file music)))))
      (delete-file music) (delete-directory dir t))))

(ert-deftest a3madkour-works-lint--missing-poem-file-is-an-error ()
  (let ((music (a3madkour-works-lint-test--file "#+TITLE: M
#+HUGO_SECTION: works/music
#+HUGO_CUSTOM_FRONT_MATTER: :format album :year 2026 :lyrics_poem nonexistent
")))
    (unwind-protect
        (let ((a3madkour-pub/poetry-dir (make-temp-file "a3-empty" t)))
          (should (cl-some (lambda (e) (string-match-p "nonexistent" e))
                           (a3madkour-works-lint/lint-file music))))
      (delete-file music))))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: FAIL — no symmetry rule exists.

- [ ] **Step 3: Implement the symmetry rule**

Add the helper, then call it from `lint-file`'s music branch. It reuses Task 8's `--cfm-cells` so both sides of the link parse identically:

```elisp
(defun a3madkour-works-lint--poem-declares-set-to-music-p (poem-file)
  "Non-nil when POEM-FILE's custom front matter declares `set_to_music'."
  (with-temp-buffer
    (insert-file-contents poem-file)
    (org-mode)
    (and (alist-get 'set_to_music
                    (a3madkour-works-lint--cfm-cells (org-element-parse-buffer)))
         t)))

(defun a3madkour-works-lint--check-lyrics-symmetry (base cells)
  "Return a list of symmetry errors for the music item described by CELLS.

`check_works_links.py' enforces lyrics_poem <-> set_to_music in both
directions, but the two ends are written by different handlers in different
modes, so satisfying one never satisfies the other.  Catching it here turns a
post-push CI failure into a file:line error."
  (let* ((cell (alist-get 'lyrics_poem cells))
         (slug (car cell))
         (line (or (cdr cell) 1))
         (errs '()))
    (when slug
      (let ((poem (expand-file-name (format "%s.org" slug) a3madkour-pub/poetry-dir)))
        (cond
         ((not (file-exists-p poem))
          (push (format "%s:%d: :lyrics_poem %S has no org source at %s"
                        base line slug poem)
                errs))
         ((not (a3madkour-works-lint--poem-declares-set-to-music-p poem))
          (push (format "%s:%d: :lyrics_poem %S but %s does not declare :set_to_music"
                        base line slug (file-name-nondirectory poem))
                errs)))))
    errs))
```

Call it inside `lint-file`, in the `cl-flet*` body, guarded to music:

```elisp
            ;; 5 — lyrics_poem must have its reciprocal set_to_music
            (unless games-p
              (setq errs (append (a3madkour-works-lint--check-lyrics-symmetry base cells)
                                 errs)))
```

Add `(require 'a3madkour-publish)` at the top of the module for `a3madkour-pub/poetry-dir`.

- [ ] **Step 4: Add the stale-bundle warning to the handler**

In `a3madkour-publish-works.el`, after the bundle write, for music items carrying `lyrics_poem`:

```elisp
(defun a3madkour-pub-works--warn-stale-backlink (poem-slug site-root)
  "WARN when POEM-SLUG's published bundle lacks its set_to_music back-link.

The org sources agree (the lint enforces that), but poetry publishes
deliberately, so its bundle may legitimately lag.  A warning, not an error —
naming the exact command to close the gap."
  (let ((bundle (expand-file-name
                 (format "content/works/poetry/%s/index.md" poem-slug) site-root)))
    (when (and (file-exists-p bundle)
               (not (with-temp-buffer
                      (insert-file-contents bundle)
                      (goto-char (point-min))
                      (re-search-forward "^set_to_music:" nil t))))
      (a3madkour-pub/warn
       "works" bundle
       "poem bundle lacks set_to_music; run: a3-pub.sh --publish-deliberate %s"
       (expand-file-name (format "%s.org" poem-slug) a3madkour-pub/poetry-dir)))))
```

Call it from the entry point when `nsym` is `works-music` and `lyrics_poem` is present.

- [ ] **Step 5: Run tests to verify they pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: PASS, **785 passing** (782 + 3).

- [ ] **Step 6: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-works-lint.el emacs-configs/custom/lisp/a3madkour-publish-works.el emacs-configs/custom/lisp/a3madkour-works-lint-test.el
git commit -m "feat(works): lint lyrics_poem symmetry; warn on a stale poem bundle"
```

---

### Task 10: Walk the notes tree once in collect-triples

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living.el:40-52`
- Test: `~/dotfiles/emacs-configs/custom/lisp/a3madkour-publish-living-test.el`

**Interfaces:**
- Consumes: nothing new.
- Produces: `a3madkour-pub-living--collect-triples` with unchanged output semantics — a list of `(SECTION FILE HANDLER)` triples — but one tree walk instead of one per registered handler.

- [ ] **Step 1: Write the failing test**

```elisp
(ert-deftest a3madkour-pub-living--collect-walks-tree-once ()
  "With N registered handlers the tree must be walked once, not N times."
  (let* ((dir (make-temp-file "a3-living-walk" t))
         (calls 0))
    (unwind-protect
        (progn
          (with-temp-file (expand-file-name "a.org" dir)
            (insert "#+TITLE: A\n#+HUGO_SECTION: garden\n#+HUGO_PUBLISH: t\n"))
          (let ((a3madkour-pub/org-notes-dir dir)
                (a3madkour-pub-living--handlers
                 '(("garden" . ignore) ("recipes" . ignore) ("works/games" . ignore))))
            (cl-letf* ((orig (symbol-function 'directory-files-recursively))
                       ((symbol-function 'directory-files-recursively)
                        (lambda (&rest args)
                          (setq calls (1+ calls))
                          (apply orig args))))
              (a3madkour-pub-living--collect-triples))
            (should (equal calls 1))))
      (delete-directory dir t))))

(ert-deftest a3madkour-pub-living--collect-yields-one-triple-per-match ()
  (let* ((dir (make-temp-file "a3-living-walk" t)))
    (unwind-protect
        (progn
          (with-temp-file (expand-file-name "a.org" dir)
            (insert "#+TITLE: A\n#+HUGO_SECTION: garden\n#+HUGO_PUBLISH: t\n"))
          (let ((a3madkour-pub/org-notes-dir dir)
                (a3madkour-pub-living--handlers
                 '(("garden" . ignore) ("recipes" . ignore))))
            (let ((triples (a3madkour-pub-living--collect-triples)))
              (should (equal (length triples) 1))
              (should (equal (car (car triples)) "garden")))))
      (delete-directory dir t))))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: FAIL — `calls` is 3, one per registered handler.

- [ ] **Step 3: Invert the loops**

```elisp
(defun a3madkour-pub-living--collect-triples ()
  "Return list of (section file handler) triples for every living-section
file under `a3madkour-pub/org-notes-dir'.

Walks the notes tree exactly once and dispatches per file.  The previous
shape nested the walk inside the per-handler loop, which cost one full
traversal per registered section."
  (let ((triples nil))
    (dolist (file (directory-files-recursively
                   a3madkour-pub/org-notes-dir "\\.org\\'"))
      (let ((section (a3madkour-pub/note-section file)))
        (when section
          (let ((handler (cdr (assoc section a3madkour-pub-living--handlers))))
            (when handler
              (push (list section file handler) triples))))))
    (nreverse triples)))
```

Note the ordering change: triples now come out in file order rather than grouped by handler. Confirm nothing downstream depends on the grouping — `a3-publish-living` dispatches in parallel into a barrier, so it should not, but check before committing.

- [ ] **Step 4: Run tests to verify they pass**

Run: `~/dotfiles/emacs-configs/custom/lisp/run-tests.sh 2>&1 | tail -5`
Expected: PASS, **787 passing** (785 + 2), with every pre-existing living test still green.

- [ ] **Step 5: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-living.el emacs-configs/custom/lisp/a3madkour-publish-living-test.el
git commit -m "perf(living): walk the notes tree once, not once per handler"
```

---

### Task 11: Wire the modules into a3-pub.sh

**Files:**
- Modify: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh` (three `-l` blocks around lines 194, 264, 355; flag parsing near line 94; the init block near line 52)

**Interfaces:**
- Consumes: Tasks 2, 7, 8, 9.
- Produces: `--skip-works-check` flag; `A3_PUB_SKIP_WORKS_CHECK` exported env var; `a3madkour-works-lint-enabled` set from it in all three invocation paths.

- [ ] **Step 1: Add the flag default and parser**

Next to the recipe-check block near line 52:

```bash
# Slice A1: --skip-works-check flag init.  Default is on (run the works
# lint).  Like the recipe lint, this is an elisp-side check, so the value
# travels as an exported env var read by --eval, not as a shell branch.
: "${A3_PUB_SKIP_WORKS_CHECK:=}"
export A3_PUB_SKIP_WORKS_CHECK
```

And in the argument loop beside line 94:

```bash
    --skip-works-check) A3_PUB_SKIP_WORKS_CHECK=1 ;;
```

- [ ] **Step 2: Add the module loads to all three blocks**

In each of the three `-l` stacks, beside the recipes pair:

```bash
    -l a3madkour-works-lint \
    -l a3madkour-publish-works \
```

- [ ] **Step 3: Add the enabled-flag eval to all three blocks**

Beside each existing recipe-lint `--eval`:

```bash
    --eval "(setq a3madkour-works-lint-enabled (not (equal (getenv \"A3_PUB_SKIP_WORKS_CHECK\") \"1\")))" \
```

- [ ] **Step 4: Verify the wiring is complete in all three paths**

Run:
```bash
grep -c 'a3madkour-publish-works' ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh
grep -c 'a3madkour-works-lint' ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh
grep -c 'A3_PUB_SKIP_WORKS_CHECK' ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh
```
Expected: `3`, `6` (three loads + three evals), and `4` (default, export, parser, and at least one eval reference — count and confirm each occurrence is in the path you intended rather than trusting the total).

- [ ] **Step 5: Smoke-test the flag end to end**

Run: `A3_PUB_SKIP_WORKS_CHECK=1 ~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living 2>&1 | tail -20`
Expected: the run completes; no works lint errors are reported even if a deliberately broken works org file is present.

- [ ] **Step 6: Commit**

```bash
cd ~/dotfiles && git add emacs-configs/custom/lisp/a3-pub.sh
git commit -m "feat(works): wire works handler + lint into a3-pub.sh (--skip-works-check)"
```

---

### Task 12: Real end-to-end run and site fixtures

Green ERT is not the completion bar. Recipe Slice 2 passed 780/780 while two integration bugs sat in the tree, because tests bypass `note-section` and ox-hugo. Both of those bugs were found only here.

**Files:**
- Create: two throwaway org sources under the real notes tree (or a scratch dir wired via `a3madkour-pub/org-notes-dir`)
- Verify: `content/works/games/<slug>/index.md`, `content/works/music/<slug>/index.md`

**Interfaces:**
- Consumes: every prior task.
- Produces: evidence, plus any regression tests for defects found.

- [ ] **Step 1: Author a maximal game and a maximal music org file**

The game exercises every optional field: `hero`, three `screenshots`, `collaborators` with a two-word name, `tech_stack`, `research_questions` pointing at an existing question fixture, `related_essays`, `related_notes`, `embed_url`, `source_url`, `itch_url`, `length`, `featured`, `tile_size`. The music file exercises `tracks` (three rows), `platform_embed`, `cover`, `duration`, `made_with`, `lyrics_poem` pointing at a poem whose org declares `set_to_music`. Content is lorem ipsum per the fixture-content constraint.

- [ ] **Step 2: Author a minimal game — Review Focus #1 at integration level**

Required keys only. No optionals at all.

- [ ] **Step 3: Publish**

Run: `~/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living 2>&1 | tail -30`
Expected: exit 0, three new bundles.

- [ ] **Step 4: Inspect the emitted frontmatter**

Run: `cat content/works/games/<slug>/index.md | sed -n '1,40p'` for each.
Expected: `year` unquoted integer; `collaborators` one entry for the two-word name; `research_questions` expanded to `/research/questions/<slug>/`; music's `hero` an unquoted `true`; `tracks` a block sequence of flow maps; the minimal game carrying **no** `screenshots`, `hero`, `collaborators` or `featured` keys at all.

- [ ] **Step 5: Confirm the assets landed and survived cleanup**

Run: `ls content/works/games/<slug>/ content/works/music/<slug>/`
Expected: `hero.png` and all three screenshots present in the game bundle; `cover.png` in the music bundle. Their presence *after* the run is the `extra-refs` proof — cleanup-stale runs in the same call.

- [ ] **Step 6: Run both site linters and the full CI gate**

Run:
```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
python3 tools/check_works_fixtures.py && python3 tools/check_works_links.py
```
Expected: both exit 0.

- [ ] **Step 7: Build and view**

Run: `hugo --minify && python3 tools/check_html_links.py public`
Expected: build succeeds; the three new pages render; no broken links. Then `hugo server` and eyeball each page — the game hero and screenshot gallery, the music track list and platform embed, and the minimal game rendering cleanly with no empty sections.

Do not run `hugo --minify` while a dev server is alive; it poisons the dev-server CSS through a MIME mismatch. Kill the server, clean `public/`, then build.

- [ ] **Step 8: Run the full local CI mirror**

Run: `tools/ci-local.sh`
Expected: all gates green.

- [ ] **Step 9: Write a regression test for every defect found**

Any bug this task surfaces gets a test in the owning module before it is fixed. Recipe Slice 2 found five here; expect some.

- [ ] **Step 10: Commit**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
git add content/works data
git commit -m "test(works): real end-to-end publish of game and music fixtures"
```

---

## Notes for the executor

- **`--coerce-bool` contract** (Task 4, Step 3): verify whether it distinguishes "absent" from "false" before relying on it. If a false value and a missing key both yield nil, the key must be deleted rather than set, or the renderer will emit `hero: ` with an empty value.
- **`note-section` and the publish flag** (Task 7, Step 1): if an unmarked file still reports its section, that is a pre-existing defect affecting every living handler, not just this one. Record it and raise it rather than working around it locally.
- **Ordering change in `collect-triples`** (Task 10): triples come out file-ordered rather than handler-grouped. Confirm the async barrier does not depend on grouping.
- **The `extra-refs` back-port** to poetry's audio and recipes' image is deliberately **not** in this plan. It belongs in its own change, once this seam is proven.
