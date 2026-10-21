# Section Registry (dotfiles half) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every hand-written elisp section list and field/enum copy with (a) one registry defconst keyed by slash name and (b) a reader over the site's `data/sections.json`, then make `a3-publish-mark` ask for, and write, every field it cannot derive.

**Architecture:** A new leaf module `a3madkour-sections.el` reads `<site-root>/data/sections.json` (mtime cache, fail-closed, no load-time deps) and generalises `a3madkour-works-vocab.el`, which is deleted. A new leaf module `a3madkour-publish-registry.el` holds the one section table (mode, handler symbol, library data config) and the only slash→hyphen converter; `a3madkour-publish.el`, living/deliberate dispatch, the frontmatter dispatch, works, research and library derive from it. Handlers are resolved by symbol at dispatch time. `a3-publish-mark` gathers every missing value first, then writes in one pass.

**Tech Stack:** Emacs 30 Lisp (lexical-binding), ERT via `./run-tests.sh`, native `json-parse-string`, `ob-core`'s header-argument parser (the one ox-hugo uses), ox-hugo, `a3-pub.sh`.

**Spec:** `docs/superpowers/specs/2026-10-20-section-registry-design.md` (site repo) — §3, §5.2, §5.3, §6, §7 (dotfiles parts), §8 steps 3–5.

## Prerequisite

The site plan (`docs/superpowers/plans/2026-10-20-section-registry-site.md`, written in parallel) is merged locally in `/Users/a3madkour/Sync/Workspace/a3madkour.github.io`:

- `data/sections.json` exists with exactly 14 sections: `essays`, `garden`, `research/themes`, `research/questions`, `works/games`, `works/music`, `works/poetry`, `library/reading`, `library/listening`, `library/playing`, `library/watching`, `streams`, `recipes`, `about`.
- `tools/check_works_fixtures.py` and `tools/test_check_works_fixtures.py` no longer read `data/works-vocab.json` (site plan Task 7). `tools/test_publish_integration.py` still does: it copies the file into the poetry test's tmp site root and pins `a3madkour-works-vocab-fixture.el` against it. **This plan's Task 6 Step 7 updates it** (the site plan defers those two references here).
- The file encodes what this plan's consumers derive from it. Each item is pinned by a cross-repo test in Task 2, so a mismatch fails loudly rather than silently. When one fails, fix `data/sections.json` in the site repo; do not add an elisp copy.
  - `works/games` and `works/music` mark `title`/`date`/`lastmod`/`draft` as `"from": "pipeline"`. Their remaining `required` fields are what works-lint rule 1 requires.
  - `works/music.platform_embed` is `{"type": "object", "fields": {"kind": {"type": "enum", "values": [...platform_kinds...]}, "url": {...}}}`.
  - Every `library/*` section has `media_type` and `status` enums.
  - `research/themes` has no `theme`/`parent_question` field. `research/questions.theme` is `{"type": "ref", "to": "research/themes"}`.
  - `garden` has `variants.on = "media_type"` with a case whose `values` is `[null]`.

Verify before Task 1:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 -c "import json;d=json.load(open('data/sections.json'));print(d['version'], sorted(d['sections']))"
```

Expected: `1 ['about', 'essays', 'garden', 'library/listening', 'library/playing', 'library/reading', 'library/watching', 'recipes', 'research/questions', 'research/themes', 'streams', 'works/games', 'works/music', 'works/poetry']`.

## Global Constraints

- Real publishes run only through `a3-pub.sh` (it sets `load-prefer-newer` and the straight bootstrap). Tests run only through `./run-tests.sh`. The only bare `emacs --batch` allowed is the byte-compile check.
- Every new `.el` file's first line ends with `-*- lexical-binding: t; -*-`.
- No fallback copies. A missing or malformed `data/sections.json` is an error. No elisp defconst may restate a field set or enum the JSON holds. The test fixture `a3madkour-sections-fixture.json` is test input; its section names are pinned to the real file by a cross-repo test.
- Full ERT suite green at every commit. `./run-tests.sh 2>&1 | grep -E "^Ran|unexpected"` must print `0 unexpected` (933 tests today, of which 1 is skipped; the count moves as tests are added and removed).
- Mutation-test every guard: break it, watch the named test fail, revert, and watch it pass again.
- Commit only the paths each task names. `/Users/a3madkour/dotfiles` has unrelated dirty files (`.zshrc`, `init.el`, …) that must stay unstaged.
- The site repo is touched in exactly two commits: Task 4 Step 13b seeds `data/sections.json` into `tools/test_publish_integration.py`'s tmp roots; Task 6 deletes `data/works-vocab.json` and the integration test's last references to it.
- A docstring line may be at most 80 characters, and an apostrophe must never sit right before a symbol. Both are byte-compile warnings, and the new files must compile clean.

## Review Focus

1. **Unloaded handler is now loud (an intended behaviour change).** Before, a living section whose handler module was not loaded was silently skipped: no triple, so the orphan sweep saw its pages as removed (S1 row 9). Now the registry always yields the triple, and a non-`fboundp` handler reports `err` and logs `handler-missing` naming the function. Deliberate signals before `begin-publish`. Tests are in Task 4.
2. **JSON `false`/`null` decoding.** `"required": false` and garden's `"values": [null]` must decode to `nil`. The defaults, `:false`/`:null`, are truthy. With them every optional field becomes required, and a concept note selects no variant case. Tests are in Task 2.
3. **The session-default fixture can hide real path resolution.** In the batch test run, `a3madkour-sections-file` points at the committed fixture, so a broken `site-data-dir → data/sections.json` path would pass every test that does not unbind it. Three Task 2 tests cover this: `with-root`, which unbinds it and resolves through `a3madkour-pub/site-data-dir`; the `emacs -Q` subprocess test; and the cross-repo real-file tests.
4. **Custom-front-matter values round-trip.** ox-hugo splits values on ` :` (`org-babel-balanced-split`), and `org-babel-read` turns a bare `2026` into a number. Mark must therefore quote text values and refuse an embedded `"`. It must also detect, replace and remove one key on a multi-key line (`:status active :weight 10`) without disturbing the keys beside it. Tests are in Task 7.
5. **Field-set drift in the filtering normalizers.** The essays, poetry, works and themes normalizers drop every key outside the contract. A field that the real file lacks but the old elisp list had would vanish from every page, with no error. Covered by the Task 5/6 one-time equivalence runs against the old constants, which are run before those constants are deleted, with any difference recorded in the commit message, and by the Task 2 cross-repo structural tests.

---

## File Structure

All dotfiles paths are under `/Users/a3madkour/dotfiles/emacs-configs/custom/lisp/` unless absolute.

**Created**
- `a3madkour-sections.el`: the contract reader (Task 2).
- `a3madkour-sections-test.el`: reader tests and cross-repo tests (Task 2).
- `a3madkour-sections-fixture.el`: test support: fixture path and text, the `with-root` and `with-real-site` macros, `mutate`, and the session default (Task 2). Its name deliberately does not match `*-test.el`.
- `a3madkour-sections-fixture.json`: the test contract, all 14 sections (Task 2).
- `a3madkour-publish-registry.el`: the registry (Task 3).
- `a3madkour-publish-registry-test.el` (Task 3).

**Modified**
- `a3madkour-publish.el`: requires the registry. `a3madkour-pub/sections` and `a3madkour-pub-deliberate-sections` are derived (Task 4).
- `a3madkour-publish-living.el`: registry lookup and a loud missing handler. The 5 `with-eval-after-load` blocks are deleted (Task 4).
- `a3madkour-publish-deliberate.el`: registry lookup and a loud missing handler. `--handlers` is deleted (Task 4).
- `a3madkour-publish-frontmatter.el`: `--known-sections` is derived (Task 4). Essays and research read the contract (Task 5). Works reads the contract and `works-vocab` is dropped (Task 6).
- `a3madkour-publish-works.el`: `--sections` is derived (Task 4).
- `a3madkour-publish-research.el`: the converter is deleted (Task 4).
- `a3madkour-publish-library.el`: `--config` is deleted, and `config-for` reads the registry and the contract (Task 4).
- `a3madkour-publish-poetry.el`: the key defconsts are deleted (Task 5).
- `a3madkour-works-lint.el`: rules 1, 2 and 6 read the contract (Task 6).
- `a3madkour-publish-author.el`: `--default-medium-for` (Task 4). The mark fill-in (Tasks 7–9).
- `a3madkour-publish-garden.el` and `a3madkour-publish-essays.el`: header comments only (Task 4).
- Tests: `-living-test`, `-deliberate-test`, `-poetry-test`, `-works-test`, `-unpublish-test`, `-research-test`, `-library-test`, `-author-test` (Task 4). `-frontmatter-test`, `-essays-test`, `-poetry-test`, `-research-test` (Task 5). `-frontmatter-test`, `-works-test`, `a3madkour-works-lint-test` (Task 6). `-author-test` (Tasks 7–9). `-research-test` (Task 1).
- `a3-pub.sh`: `-l` lines (Task 10).
- `/Users/a3madkour/dotfiles/emacs-configs/custom/config.org`: the Website publish requires (Task 10).

**Deleted**
- `a3madkour-works-vocab.el`, `a3madkour-works-vocab-test.el`, `a3madkour-works-vocab-fixture.el`, and the untracked `a3madkour-works-vocab.elc` (Task 6).
- Site: `/Users/a3madkour/Sync/Workspace/a3madkour.github.io/data/works-vocab.json` (Task 6).

---

### Task 1: Spike: how ox-hugo exports a `refs` custom-front-matter value

The mark task's `refs` write format depends on this result. The spec assumes a space-separated list (§6 step 4). That is unverified: the example notes carry a single value.

**Files:**
- Modify: `a3madkour-publish-research-test.el`. Append after the `publish-question-with-outputs-end-to-end` test (current line 339).

**Interfaces:**
- Consumes: `a3madkour-pub-research/publish-research-file (file run &key on-done)`, `a3madkour-pub/begin-publish`, `a3madkour-pub/finish-publish`, `make-a3-pub-async-run`.
- Produces: `a3madkour-pub-research-test--publish-question (cfm-line) -> (STATUS . BUNDLE-TEXT)`, plus one or two pin tests.

- [ ] **Step 1: Write the two probe tests**

Append to `a3madkour-publish-research-test.el`:

```elisp
;;; Spike (section-registry plan Task 1): how a `refs' value written by
;;; `a3-publish-mark' reaches the page.  `#+HUGO_CUSTOM_FRONT_MATTER:' values
;;; go through `org-babel-parse-header-arguments' inside ox-hugo, so
;;; `:k a b' arrives as the STRING "a b" while `:k '(a b)' arrives as a
;;; LIST of symbols.  These tests pin which form ends up as a YAML list in
;;; the published bundle, through the real research handler and ox-hugo.

(defun a3madkour-pub-research-test--publish-question (cfm-line)
  "Publish a research question carrying CFM-LINE; return (STATUS . TEXT).
STATUS is what the handler passed to ON-DONE; TEXT is the bundle's
index.md, or nil when no bundle was written."
  (let* ((notes-dir (make-temp-file "a3-pub-research-notes-" t))
         (site-dir  (make-temp-file "a3-pub-research-site-" t))
         (src (expand-file-name "research-questions-refs.org" notes-dir))
         (out (expand-file-name
               "content/research/questions/refs-question/index.md" site-dir))
         (status 'never-called))
    (unwind-protect
        (progn
          (make-directory (expand-file-name "data" site-dir) t)
          (make-directory (expand-file-name "content/research/questions" site-dir) t)
          (with-temp-file (expand-file-name "data/url-history.yaml" site-dir)
            (insert "notes: []\n"))
          (with-temp-file src
            (insert ":PROPERTIES:\n"
                    ":ID: 33333333-aaaa-bbbb-cccc-dddddddddddd\n"
                    ":LAST_MODIFIED: 2026-05-30\n"
                    ":END:\n"
                    "#+title: Refs question\n"
                    "#+HUGO_PUBLISH: t\n"
                    "#+HUGO_SECTION: research/questions\n"
                    "#+HUGO_BASE_DIR: " site-dir "\n"
                    "#+HUGO_DESCRIPTION: A question.\n"
                    "#+HUGO_CUSTOM_FRONT_MATTER: :theme procedural-narrative\n"
                    "#+HUGO_CUSTOM_FRONT_MATTER: :status active\n"
                    cfm-line "\n"
                    "\nBody.\n"))
          (let ((a3madkour-pub/site-data-dir
                 (file-name-as-directory (expand-file-name "data" site-dir)))
                (a3madkour-pub/org-notes-dir notes-dir))
            (cl-letf (((symbol-function 'org-roam-db-sync) #'ignore))
              (a3madkour-pub/begin-publish)
              (a3madkour-pub-research/publish-research-file
               src (make-a3-pub-async-run)
               :on-done (lambda (s) (setq status s)))
              (a3madkour-pub/finish-publish)))
          (cons status
                (and (file-exists-p out)
                     (with-temp-buffer
                       (insert-file-contents out)
                       (buffer-string)))))
      (delete-directory notes-dir t)
      (delete-directory site-dir t))))

(ert-deftest a3madkour-pub-research--refs-space-list-exports-as-yaml-list ()
  "`:supporting_notes a b' — the form `a3-publish-mark' writes for a refs
field — reaches the page as a YAML list."
  (let ((res (a3madkour-pub-research-test--publish-question
              "#+HUGO_CUSTOM_FRONT_MATTER: :supporting_notes example-note-one example-note-two")))
    (should (eq (car res) 'ok))
    (should (string-match-p
             "^supporting_notes: \\[\"example-note-one\", \"example-note-two\"\\]$"
             (cdr res)))))

(ert-deftest a3madkour-pub-research--refs-quoted-list-exports-as-yaml-list ()
  "`:supporting_notes \\='(a b)' — ox-hugo's documented list form."
  (let ((res (a3madkour-pub-research-test--publish-question
              "#+HUGO_CUSTOM_FRONT_MATTER: :supporting_notes '(example-note-one example-note-two)")))
    (should (eq (car res) 'ok))
    (should (string-match-p
             "^supporting_notes: \\[\"example-note-one\", \"example-note-two\"\\]$"
             (cdr res)))))
```

- [ ] **Step 2: Run both probes and record the outcome**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "refs-space-list|refs-quoted-list|^Ran|unexpected"
```

Expected, from reading the code: the space form PASSES. ox-hugo hands the string `"a b"` to `a3madkour-pub-frontmatter--parse-slug-list`, which splits it, and `a3madkour-pub-yaml/render-value` renders `["a", "b"]`. The quoted form is unknown. If the YAML round-trip in `a3madkour-pub-export/export-file` yields a vector, `--parse-slug-list` drops it (its `listp` test fails). On failure, inspect `(cdr res)` with `(message "%S" ...)` in a scratch `ert` run to record what was emitted.

- [ ] **Step 3: Apply the decision rule**

| Space form | Quoted form | Decision |
|---|---|---|
| PASS | FAIL | **Branch A** (expected). Delete `--refs-quoted-list-exports-as-yaml-list`, and record "quoted form emits: <what you saw>" in the commit message. Task 7 uses the Branch A `refs` renderer. |
| PASS | PASS | **Branch A.** Keep both tests. Mark still writes the space form: the spec says so, and works-lint's `--parse-plist` and mark's own key reader handle it. |
| FAIL | PASS | **Branch B.** Delete the space test. Task 7 uses the Branch B `refs` renderer, and the Task 7 renderer test's `refs` line is swapped to the Branch B expectation shown there. |
| FAIL | FAIL | **Stop.** Spec §6 step 4's refs assumption is false for both forms. Report back with the two emitted bundles; do not continue to Task 7. |

- [ ] **Step 4: Run the full suite, which must be green**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "^Ran|unexpected"
```

Expected: `0 unexpected`.

- [ ] **Step 5: Mutation-check the pin**

In the kept test, change the expected regexp's `example-note-two` to `example-note-three`. Run Step 2's command; the test FAILS. Revert; it PASSES.

- [ ] **Step 6: Commit**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-research-test.el && git commit -F - <<'EOF'
test(research): pin how a refs custom-front-matter value reaches YAML

Spike for the section-registry mark fill-in: publishes a research
question through the real handler and ox-hugo with
`:supporting_notes a b`, and asserts the bundle carries
`supporting_notes: ["a", "b"]`.  Result: <space form PASS/FAIL; quoted
form PASS/FAIL, emitted: ...>.  a3-publish-mark writes the <space|quoted>
form (Branch <A|B>).

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

(Fill the angle-bracket slots from Step 3 before committing; they record an observation, not code.)

---

### Task 2: `a3madkour-sections.el`, the contract reader

**Files:**
- Create: `a3madkour-sections.el`, `a3madkour-sections-fixture.json`, `a3madkour-sections-fixture.el`, `a3madkour-sections-test.el`.

**Interfaces (Produces, exact):**
- `a3madkour-sections-file`: defvar, nil or an absolute path that overrides the site-root resolution.
- `(a3madkour-sections/read) -> ALIST`: the parsed file (symbol keys), validated and cached by (path, mtime). Signals `error` when the file is missing, malformed, the wrong version, or carries a section without fields or a bad `variants.on`.
- `(a3madkour-sections/names) -> (STRING ...)`: section names in file order.
- `(a3madkour-sections/spec SECTION) -> ALIST`: one section's raw spec (`fields`, `variants`, `closed`, `store`). Signals on an unknown SECTION.
- `(a3madkour-sections/fields SECTION &optional VARIANT-CASE) -> ((NAME . SPEC) ...)`: NAME is a string. SPEC is an alist with symbol keys `type required values to default from ask fill fields`; JSON `false`/`null` decode to nil. Base fields come first in file order, then VARIANT-CASE's fields (a case-name string). Signals on an unknown case.
- `(a3madkour-sections/variant-case SECTION VALUE) -> STRING|nil`: the case whose `values` contains VALUE (nil means the field is absent). nil when SECTION has no variants. Signals when VALUE selects no case.
- `(a3madkour-sections/field SECTION PATH) -> SPEC`: PATH is `"name"` or `"object.sub"`. It searches base fields and then every case. Signals when absent.
- `(a3madkour-sections/enum SECTION PATH) -> (STRING ...)`: the `values` of an enum field. Signals when the field is not `type: enum`.
- `(a3madkour-sections/emitted-keys SECTION) -> (STRING ...)`: every field name legal in SECTION's emitted frontmatter, which is base plus every variant case, deduplicated, in file order. For games and music this is exactly works-vocab's `<type>_required + <type>_optional + umbrella_optional`, because the site plan transcribes those three lists as the sections' fields.
- `(a3madkour-sections/required-authored SECTION) -> (STRING ...)`: base fields that are `required` and not `from: pipeline`.
- Fixture (test support): `a3madkour-sections-test--fixture-path`, `a3madkour-sections-test--json`, `(a3madkour-sections-test/write SITE-ROOT &optional JSON)`, `(a3madkour-sections-test/mutate OLD NEW &optional JSON)`, macro `(a3madkour-sections-test--with-root JSON &rest BODY)`, macro `(a3madkour-sections-test--with-real-site &rest BODY)`, `(a3madkour-sections-test--real-site-root)`.

- [ ] **Step 1: Write the fixture JSON**

Create `a3madkour-sections-fixture.json`. Keep the spacing exactly as shown: mutation tests replace exact substrings, and `mutate` errors if a substring is absent.

```json
{
  "version": 1,
  "sections": {
    "essays": {
      "closed": false,
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"},
        "date": {"type": "date", "required": true, "from": "pipeline"},
        "lastmod": {"type": "date", "required": true, "from": "pipeline"},
        "draft": {"type": "bool", "required": true, "from": "pipeline"},
        "summary": {"type": "text", "required": true, "from": "pipeline"},
        "tags": {"type": "list", "required": true, "from": "pipeline"},
        "series": {"type": "text", "required": true, "from": "pipeline"},
        "series_order": {"type": "int", "required": true, "from": "pipeline"},
        "toc": {"type": "bool", "required": true, "from": "pipeline"},
        "has_sidenotes": {"type": "bool", "required": true, "from": "pipeline"},
        "has_citations": {"type": "bool", "required": true, "from": "pipeline"},
        "has_footnotes": {"type": "bool", "required": true, "from": "pipeline"},
        "has_math": {"type": "bool", "required": true, "from": "pipeline"},
        "has_widgets": {"type": "bool", "required": true, "from": "pipeline"},
        "has_video_sync": {"type": "bool", "required": true, "from": "pipeline"},
        "tile_size": {"type": "enum", "values": ["large", "medium", "small"]},
        "featured": {"type": "bool"},
        "hero": {"type": "text"},
        "source_stream": {"type": "ref", "to": "streams"}
      }
    },
    "garden": {
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"},
        "draft": {"type": "bool", "required": true, "from": "pipeline"},
        "last_modified": {"type": "date", "required": true, "from": "pipeline"},
        "growth_stage": {"type": "enum", "required": true, "from": "pipeline", "values": ["seedling", "budding", "evergreen"]},
        "tags": {"type": "list", "from": "pipeline"},
        "summary": {"type": "text"},
        "topic_map": {"type": "refs", "to": "garden"},
        "roam_refs": {"type": "list"},
        "year": {"type": "int"},
        "weight": {"type": "int"},
        "source_stream": {"type": "ref", "to": "streams"},
        "media_type": {"type": "enum", "values": ["book", "album", "track", "game", "film", "series", "paper", "video", "article", "talk"]}
      },
      "variants": {
        "on": "media_type",
        "cases": {
          "concept": {"values": [null], "fields": {}},
          "media": {
            "values": ["book", "album", "track", "game", "film", "series"],
            "fields": {
              "status": {"type": "enum", "required": true, "values": ["reading", "finished", "abandoned", "queued"]},
              "creator": {"type": "text", "required": true},
              "started": {"type": "date"},
              "finished": {"type": "date"},
              "spoiler_level": {"type": "enum", "values": ["none", "light", "heavy"]},
              "original_url": {"type": "text"}
            }
          },
          "reference": {
            "values": ["paper", "video", "article", "talk"],
            "fields": {
              "creator": {"type": "text", "required": true},
              "original_url": {"type": "text"}
            }
          }
        }
      }
    },
    "research/themes": {
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"},
        "last_modified": {"type": "date", "required": true, "from": "pipeline"},
        "tags": {"type": "list", "required": true, "from": "pipeline"},
        "draft": {"type": "bool", "from": "pipeline"},
        "author": {"type": "text", "from": "pipeline"},
        "description": {"type": "text", "required": true},
        "summary": {"type": "text"},
        "status": {"type": "enum", "required": true, "values": ["active", "dormant", "answered"], "default": "active"},
        "weight": {"type": "int", "required": true, "fill": "next-weight"},
        "garden_topic_ref": {"type": "ref", "to": "garden"},
        "source_stream": {"type": "ref", "to": "streams"}
      }
    },
    "research/questions": {
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"},
        "last_modified": {"type": "date", "required": true, "from": "pipeline"},
        "tags": {"type": "list", "from": "pipeline"},
        "draft": {"type": "bool", "from": "pipeline"},
        "author": {"type": "text", "from": "pipeline"},
        "description": {"type": "text", "required": true},
        "summary": {"type": "text"},
        "status": {"type": "enum", "required": true, "values": ["active", "dormant", "answered"], "default": "active"},
        "weight": {"type": "int"},
        "theme": {"type": "ref", "to": "research/themes", "required": true},
        "parent_question": {"type": "ref", "to": "research/questions"},
        "supporting_notes": {"type": "refs", "to": "garden", "ask": true},
        "related_essays": {"type": "refs", "to": "essays"},
        "started": {"type": "date", "fill": "today", "ask": true},
        "outputs": {"type": "structured"},
        "source_stream": {"type": "ref", "to": "streams"}
      }
    },
    "works/games": {
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"},
        "date": {"type": "date", "required": true, "from": "pipeline"},
        "lastmod": {"type": "date", "required": true, "from": "pipeline"},
        "draft": {"type": "bool", "required": true, "from": "pipeline"},
        "status": {"type": "enum", "required": true, "values": ["playable", "in-progress", "archived"]},
        "game_kind": {"type": "enum", "required": true, "values": ["full-release", "jam", "research-prototype", "experiment"]},
        "tagline": {"type": "text", "required": true},
        "year": {"type": "int", "required": true},
        "tags": {"type": "list"},
        "summary": {"type": "text"},
        "embed_url": {"type": "text"},
        "source_url": {"type": "text"},
        "itch_url": {"type": "text"},
        "collaborators": {"type": "list"},
        "tech_stack": {"type": "list"},
        "length": {"type": "text"},
        "screenshots": {"type": "list"},
        "research_questions": {"type": "refs", "to": "research/questions"},
        "related_essays": {"type": "refs", "to": "essays"},
        "related_notes": {"type": "refs", "to": "garden"},
        "source_stream": {"type": "ref", "to": "streams"},
        "tile_size": {"type": "enum", "values": ["small", "medium", "large"]},
        "featured": {"type": "bool"},
        "hero": {"type": "text"}
      }
    },
    "works/music": {
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"},
        "date": {"type": "date", "required": true, "from": "pipeline"},
        "lastmod": {"type": "date", "required": true, "from": "pipeline"},
        "draft": {"type": "bool", "required": true, "from": "pipeline"},
        "format": {"type": "enum", "required": true, "values": ["album", "track", "experiment", "live"]},
        "year": {"type": "int", "required": true},
        "tags": {"type": "list"},
        "summary": {"type": "text"},
        "tagline": {"type": "text"},
        "cover": {"type": "text"},
        "duration": {"type": "text"},
        "tracks": {"type": "structured"},
        "platform_embed": {"type": "object", "fields": {"kind": {"type": "enum", "required": true, "values": ["bandcamp", "soundcloud", "youtube"]}, "url": {"type": "text", "required": true}}},
        "audio_url": {"type": "text"},
        "lyrics_poem": {"type": "ref", "to": "works/poetry"},
        "related_works": {"type": "list"},
        "related_essays": {"type": "refs", "to": "essays"},
        "made_with": {"type": "list"},
        "collaborators": {"type": "list"},
        "source_stream": {"type": "ref", "to": "streams"},
        "tile_size": {"type": "enum", "values": ["small", "medium", "large"]},
        "featured": {"type": "bool"},
        "hero": {"type": "bool"}
      }
    },
    "works/poetry": {
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"},
        "date": {"type": "date", "required": true, "from": "pipeline"},
        "lastmod": {"type": "date", "required": true, "from": "pipeline"},
        "draft": {"type": "bool", "required": true, "from": "pipeline"},
        "lines": {"type": "int", "required": true, "from": "pipeline"},
        "tags": {"type": "list"},
        "collection": {"type": "text"},
        "set_to_music": {"type": "ref", "to": "works/music"},
        "summary": {"type": "text"},
        "audio_url": {"type": "text"},
        "source_stream": {"type": "ref", "to": "streams"},
        "tile_size": {"type": "enum", "values": ["small", "medium", "large"]},
        "featured": {"type": "bool"},
        "hero": {"type": "text"}
      }
    },
    "library/reading": {
      "store": "data",
      "fields": {
        "slug": {"type": "text", "required": true},
        "title": {"type": "text", "required": true},
        "creator": {"type": "text", "required": true},
        "year": {"type": "int", "required": true},
        "media_type": {"type": "enum", "required": true, "values": ["book"]},
        "status": {"type": "enum", "required": true, "values": ["finished", "reading", "queued", "abandoned"]},
        "last_modified": {"type": "date", "required": true},
        "tags": {"type": "list", "required": true},
        "started": {"type": "date"},
        "finished": {"type": "date"},
        "spoiler_level": {"type": "enum", "values": ["none", "light", "heavy"]},
        "cite_key": {"type": "text"},
        "canonical_url": {"type": "text"},
        "note_slug": {"type": "text"},
        "preview": {"type": "text"},
        "extras": {"type": "object", "fields": {"cover_file": {"type": "text"}, "cover_url": {"type": "text"}}}
      }
    },
    "library/listening": {
      "store": "data",
      "fields": {
        "slug": {"type": "text", "required": true},
        "title": {"type": "text", "required": true},
        "creator": {"type": "text", "required": true},
        "year": {"type": "int", "required": true},
        "media_type": {"type": "enum", "required": true, "values": ["album", "track"]},
        "status": {"type": "enum", "required": true, "values": ["finished", "listening", "queued", "dropped"]},
        "last_modified": {"type": "date", "required": true},
        "tags": {"type": "list", "required": true},
        "extras": {"type": "object", "fields": {"cover_file": {"type": "text"}, "cover_url": {"type": "text"}}}
      }
    },
    "library/playing": {
      "store": "data",
      "fields": {
        "slug": {"type": "text", "required": true},
        "title": {"type": "text", "required": true},
        "creator": {"type": "text", "required": true},
        "year": {"type": "int", "required": true},
        "media_type": {"type": "enum", "required": true, "values": ["game"]},
        "status": {"type": "enum", "required": true, "values": ["finished", "100pct", "playing", "queued", "dropped"]},
        "last_modified": {"type": "date", "required": true},
        "tags": {"type": "list", "required": true},
        "extras": {"type": "object", "fields": {"cover_file": {"type": "text"}, "cover_url": {"type": "text"}}}
      }
    },
    "library/watching": {
      "store": "data",
      "fields": {
        "slug": {"type": "text", "required": true},
        "title": {"type": "text", "required": true},
        "creator": {"type": "text", "required": true},
        "year": {"type": "int", "required": true},
        "media_type": {"type": "enum", "required": true, "values": ["film", "series"]},
        "status": {"type": "enum", "required": true, "values": ["finished", "watching", "queued", "dropped"]},
        "last_modified": {"type": "date", "required": true},
        "tags": {"type": "list", "required": true},
        "extras": {"type": "object", "fields": {"cover_file": {"type": "text"}, "cover_url": {"type": "text"}}}
      }
    },
    "streams": {
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"},
        "date": {"type": "date", "required": true, "from": "pipeline"},
        "draft": {"type": "bool", "required": true, "from": "pipeline"},
        "platforms": {"type": "list", "required": true},
        "category": {"type": "enum", "required": true, "values": ["game-dev", "research", "coding", "creative"]},
        "archive_status": {"type": "enum", "required": true, "values": ["live", "archived", "removed", "private"]},
        "vod_url": {"type": "text"},
        "tags": {"type": "list"},
        "summary": {"type": "text"}
      }
    },
    "recipes": {
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"},
        "date": {"type": "date", "required": true, "from": "pipeline"},
        "lastmod": {"type": "date", "required": true, "from": "pipeline"},
        "draft": {"type": "bool", "required": true, "from": "pipeline"},
        "summary": {"type": "text", "required": true, "from": "pipeline"},
        "tags": {"type": "list", "from": "pipeline"},
        "servings": {"type": "int", "required": true, "from": "pipeline"},
        "sources": {"type": "structured", "required": true},
        "ingredients": {"type": "structured", "required": true},
        "steps": {"type": "structured", "required": true}
      }
    },
    "about": {
      "fields": {
        "title": {"type": "text", "required": true, "from": "pipeline"}
      }
    }
  }
}
```

Fixture annotations (`from`, `ask`, `fill`) are test inputs. They are chosen so that `essays` and a concept `garden` note ask nothing, which keeps the existing `a3-publish-mark` tests prompt-free. They are not a copy of the real contract's annotations.

- [ ] **Step 2: Write the fixture support module**

Create `a3madkour-sections-fixture.el`:

```elisp
;;; a3madkour-sections-fixture.el --- test support for the section contract  -*- lexical-binding: t; -*-

;;; Commentary:

;; Test support, not a test.  Its name deliberately does not match
;; run-tests.sh's `*-test.el' glob: a file that is both `require'd by test
;; files and loaded by the runner makes ert refuse to redefine its tests.
;;
;; `a3madkour-sections-fixture.json' is a TEST INPUT, not a copy of the
;; contract.  The contract lives in the site repo's `data/sections.json'.
;; The cross-repo tests in `a3madkour-sections-test.el' pin the fixture's
;; section NAMES to that file and check every structural fact the pipeline
;; depends on against the real file itself.
;;
;; Session default: in a batch test run (`noninteractive'), loading this
;; file points `a3madkour-sections-file' at the fixture, so the ~150
;; existing tests whose code paths now read the contract need no wrapper.
;; `a3madkour-sections-test--with-root' unbinds it, so tests written with
;; that macro exercise the production resolution through
;; `a3madkour-pub/site-data-dir'.  It is never set in an interactive Emacs:
;; running ert there must not silently repoint a real publish at a fixture.

;;; Code:

(require 'ert)
(require 'a3madkour-sections)
;; Defines `a3madkour-pub/site-data-dir', so the `let' in the macros below is
;; a DYNAMIC binding (a `let' over a variable Emacs does not yet know to be
;; special is lexical under `lexical-binding: t', and the reader never sees
;; it).
(require 'a3madkour-publish-history)
;; Loaded eagerly so `a3madkour-pub-yaml/site-root' exists before any test
;; mocks it: the reader requires it lazily, and a `cl-letf' over an
;; undefined symbol is clobbered when that lazy `require' loads the defun.
(require 'a3madkour-publish-yaml)

(defconst a3madkour-sections-test--fixture-path
  (expand-file-name "a3madkour-sections-fixture.json"
                    (file-name-directory (or load-file-name buffer-file-name)))
  "Absolute path of the committed fixture contract.")

(defconst a3madkour-sections-test--json
  (with-temp-buffer
    (insert-file-contents a3madkour-sections-test--fixture-path)
    (buffer-string))
  "Text of the fixture contract.")

(when noninteractive
  (setq a3madkour-sections-file a3madkour-sections-test--fixture-path))

(defun a3madkour-sections-test/write (site-root &optional json)
  "Write JSON (default: the fixture) to SITE-ROOT's data/sections.json."
  (make-directory (expand-file-name "data" site-root) t)
  (with-temp-file (expand-file-name "data/sections.json" site-root)
    (insert (or json a3madkour-sections-test--json))))

(defun a3madkour-sections-test/mutate (old new &optional json)
  "Return JSON (default: the fixture) with every OLD replaced by NEW.
Signals when OLD does not occur, so a mutation test cannot pass
vacuously against a fixture whose spelling has drifted."
  (let ((json (or json a3madkour-sections-test--json)))
    (unless (string-search old json)
      (error "a3madkour-sections-test/mutate: %S not in fixture" old))
    (string-replace old new json)))

(defmacro a3madkour-sections-test--with-root (json &rest body)
  "Run BODY over a temp site root whose data/sections.json holds JSON.
When JSON is nil no contract file is written.  The root is supplied the
way production supplies it, through `a3madkour-pub/site-data-dir', with
the session-default `a3madkour-sections-file' unbound."
  (declare (indent 1))
  `(let* ((a3madkour-sections--cache nil)
          (a3madkour-sections-file nil)
          (root (file-name-as-directory (make-temp-file "a3-sections" t))))
     (unwind-protect
         (progn
           (when ,json (a3madkour-sections-test/write root ,json))
           (let ((a3madkour-pub/site-data-dir
                  (file-name-as-directory (expand-file-name "data" root))))
             ,@body))
       (delete-directory root t))))

(defun a3madkour-sections-test--real-site-root ()
  "The real site checkout: $A3_PUB_SITE_ROOT, else the author's path."
  (file-name-as-directory
   (expand-file-name (or (getenv "A3_PUB_SITE_ROOT")
                         "~/Sync/Workspace/a3madkour.github.io"))))

(defmacro a3madkour-sections-test--with-real-site (&rest body)
  "Run BODY against the REAL site repo's data/sections.json.
Skips only when the site checkout itself is absent; a checkout without
data/sections.json is a failure (the plan's prerequisite)."
  (declare (indent 0))
  `(let ((real-root (a3madkour-sections-test--real-site-root)))
     (unless (file-directory-p real-root)
       (ert-skip (format "site repo not found at %s" real-root)))
     (let ((a3madkour-sections--cache nil)
           (a3madkour-sections-file nil)
           (a3madkour-pub/site-data-dir
            (file-name-as-directory (expand-file-name "data" real-root))))
       ,@body)))

(provide 'a3madkour-sections-fixture)

;;; a3madkour-sections-fixture.el ends here
```

- [ ] **Step 3: Write the failing reader tests**

Create `a3madkour-sections-test.el`:

```elisp
;;; a3madkour-sections-test.el --- tests for the section contract reader  -*- lexical-binding: t; -*-

;;; Code:

(require 'ert)
(require 'cl-lib)
(require 'a3madkour-sections)
(require 'a3madkour-sections-fixture)

(defun a3madkour-sections-test--err (fn)
  "Call FN; return the message of the error it signals, or nil."
  (condition-case err (progn (funcall fn) nil)
    (error (error-message-string err))))

;;; Fail closed

(ert-deftest a3madkour-sections--fails-closed-when-missing ()
  (a3madkour-sections-test--with-root nil
    (should (string-match-p "contract not found at .*data/sections\\.json"
                            (a3madkour-sections-test--err
                             #'a3madkour-sections/names)))))

(ert-deftest a3madkour-sections--fails-closed-when-malformed ()
  (a3madkour-sections-test--with-root "{ not json"
    (should (string-match-p "is not valid JSON"
                            (a3madkour-sections-test--err
                             #'a3madkour-sections/names)))))

(ert-deftest a3madkour-sections--fails-closed-on-wrong-version ()
  (a3madkour-sections-test--with-root
      "{\"version\": 2, \"sections\": {\"about\": {\"fields\": {\"title\": {\"type\": \"text\"}}}}}"
    (should (string-match-p "version 2, expected 1"
                            (a3madkour-sections-test--err
                             #'a3madkour-sections/names)))))

(ert-deftest a3madkour-sections--fails-closed-on-section-without-fields ()
  (a3madkour-sections-test--with-root
      "{\"version\": 1, \"sections\": {\"about\": {}}}"
    (should (string-match-p "section about in .* has no fields"
                            (a3madkour-sections-test--err
                             #'a3madkour-sections/names)))))

(ert-deftest a3madkour-sections--fails-closed-on-variants-on-a-non-field ()
  (a3madkour-sections-test--with-root
      "{\"version\": 1, \"sections\": {\"garden\": {\"fields\": {\"title\": {\"type\": \"text\"}}, \"variants\": {\"on\": \"media_type\", \"cases\": {}}}}}"
    (should (string-match-p "variants.on \"media_type\" is not a field"
                            (a3madkour-sections-test--err
                             #'a3madkour-sections/names)))))

(ert-deftest a3madkour-sections--fails-closed-without-site-data-dir ()
  (let ((a3madkour-sections--cache nil)
        (a3madkour-sections-file nil)
        (a3madkour-pub/site-data-dir nil))
    (should (string-match-p "site-data-dir is not set"
                            (a3madkour-sections-test--err
                             #'a3madkour-sections/names)))))

(ert-deftest a3madkour-sections--unknown-section-signals ()
  (a3madkour-sections-test--with-root a3madkour-sections-test--json
    (should (string-match-p "unknown section \"works/bogus\""
                            (a3madkour-sections-test--err
                             (lambda () (a3madkour-sections/spec "works/bogus")))))))

;;; Resolution and cache

(ert-deftest a3madkour-sections--resolves-through-site-data-dir ()
  "`with-root' unbinds the session default, so this read went through
`a3madkour-pub/site-data-dir' → <root>/data/sections.json."
  (a3madkour-sections-test--with-root
      (a3madkour-sections-test/mutate "\"about\": {" "\"colophon\": {")
    (should (member "colophon" (a3madkour-sections/names)))
    (should-not (member "about" (a3madkour-sections/names)))))

(ert-deftest a3madkour-sections--override-file-wins ()
  (let ((f (make-temp-file "a3-sections-override" nil ".json")))
    (unwind-protect
        (progn
          (with-temp-file f
            (insert (a3madkour-sections-test/mutate "\"about\": {" "\"colophon\": {")))
          (let ((a3madkour-sections--cache nil)
                (a3madkour-sections-file f))
            (should (member "colophon" (a3madkour-sections/names)))))
      (delete-file f))))

(ert-deftest a3madkour-sections--cache-notices-an-edited-file ()
  "Keyed on mtime, not path alone: async publish keeps one Emacs alive
across runs, so an edited contract must be re-read."
  (a3madkour-sections-test--with-root a3madkour-sections-test--json
    (should (member "playable" (a3madkour-sections/enum "works/games" "status")))
    (let ((root (file-name-directory
                 (directory-file-name a3madkour-pub/site-data-dir))))
      (a3madkour-sections-test/write
       root (a3madkour-sections-test/mutate "\"playable\"" "\"shippable\""))
      (set-file-times (expand-file-name "data/sections.json" root)
                      (time-add (current-time) 10))
      (should (member "shippable" (a3madkour-sections/enum "works/games" "status")))
      (should-not (member "playable" (a3madkour-sections/enum "works/games" "status"))))))

;;; Queries over the fixture

(ert-deftest a3madkour-sections--names-in-file-order ()
  (should (equal (a3madkour-sections/names)
                 '("essays" "garden" "research/themes" "research/questions"
                   "works/games" "works/music" "works/poetry"
                   "library/reading" "library/listening" "library/playing"
                   "library/watching" "streams" "recipes" "about"))))

(ert-deftest a3madkour-sections--fields-base-and-variant ()
  (let ((base (mapcar #'car (a3madkour-sections/fields "garden")))
        (media (mapcar #'car (a3madkour-sections/fields "garden" "media"))))
    (should (member "media_type" base))
    (should-not (member "status" base))
    (should (member "status" media))
    (should (member "creator" media))
    (should (equal (cl-subseq media 0 (length base)) base)))
  (should (equal (alist-get 'type (cdr (assoc "status" (a3madkour-sections/fields "research/themes"))))
                 "enum"))
  (should-error (a3madkour-sections/fields "garden" "bogus-case")))

(ert-deftest a3madkour-sections--null-and-false-decode-to-nil ()
  "`\"values\": [null]' selects the concept case for an ABSENT field, and
`\"required\": false' is not required.  Under the json.el defaults these
decode to `:null' / `:false', both truthy."
  (should (equal (a3madkour-sections/variant-case "garden" nil) "concept"))
  (a3madkour-sections-test--with-root
      "{\"version\": 1, \"sections\": {\"about\": {\"fields\": {\"title\": {\"type\": \"text\", \"required\": true}, \"blurb\": {\"type\": \"text\", \"required\": false}}}}}"
    (should (equal (a3madkour-sections/required-authored "about") '("title")))))

(ert-deftest a3madkour-sections--variant-case-selection ()
  (should (equal (a3madkour-sections/variant-case "garden" "book") "media"))
  (should (equal (a3madkour-sections/variant-case "garden" "paper") "reference"))
  (should-not (a3madkour-sections/variant-case "research/themes" nil))
  (should-error (a3madkour-sections/variant-case "garden" "hologram")))

(ert-deftest a3madkour-sections--enum-lookup ()
  (should (equal (a3madkour-sections/enum "research/themes" "status")
                 '("active" "dormant" "answered")))
  (should (equal (a3madkour-sections/enum "works/music" "platform_embed.kind")
                 '("bandcamp" "soundcloud" "youtube")))
  ;; A variant-case field is found too.
  (should (member "queued" (a3madkour-sections/enum "garden" "status")))
  (should-error (a3madkour-sections/enum "research/themes" "description"))
  (should-error (a3madkour-sections/enum "research/themes" "no_such_field")))

(ert-deftest a3madkour-sections--emitted-keys-compose-base-and-every-case ()
  (let ((games (a3madkour-sections/emitted-keys "works/games"))
        (music (a3madkour-sections/emitted-keys "works/music"))
        (garden (a3madkour-sections/emitted-keys "garden")))
    (should (member "hero" games))
    (should (member "tile_size" games))
    (should (member "status" games))
    (should-not (member "format" games))
    (should (member "format" music))
    (should-not (member "status" music))
    (should (member "status" garden))
    (should (member "original_url" garden))
    ;; `creator' is in two cases but emitted once.
    (should (= (length garden) (length (delete-dups (copy-sequence garden)))))))

(ert-deftest a3madkour-sections--required-authored-excludes-pipeline ()
  (should (equal (a3madkour-sections/required-authored "works/games")
                 '("status" "game_kind" "tagline" "year")))
  (should (equal (a3madkour-sections/required-authored "works/music")
                 '("format" "year"))))

;;; No load-time dependencies

(ert-deftest a3madkour-sections--loads-under-emacs-Q ()
  "The reader, and the frontmatter normalizer that requires it, load on a
bare `emacs -Q' — the leaf property `a3madkour-works-vocab' had."
  (let* ((dir (file-name-directory (locate-library "a3madkour-sections")))
         (emacs (expand-file-name invocation-name invocation-directory))
         (status (call-process emacs nil nil nil "-Q" "--batch"
                               "--eval" "(setq load-prefer-newer t)"
                               "-L" dir
                               "--eval" "(require 'a3madkour-sections)"
                               "--eval" "(require 'a3madkour-publish-frontmatter)")))
    (should (equal status 0))))

;;; Cross-repo: the REAL data/sections.json

(ert-deftest a3madkour-sections--real-contract-sections-match-fixture ()
  (a3madkour-sections-test--with-real-site
    (let ((real (sort (a3madkour-sections/names) #'string<)))
      (should (= (length real) 14))
      (let ((a3madkour-sections--cache nil)
            (a3madkour-sections-file a3madkour-sections-test--fixture-path))
        (should (equal real (sort (a3madkour-sections/names) #'string<)))))))

(ert-deftest a3madkour-sections--real-contract-answers-every-consumer ()
  "Every query the publish pipeline makes resolves against the real file."
  (a3madkour-sections-test--with-real-site
    (dolist (s (a3madkour-sections/names))
      (should (a3madkour-sections/emitted-keys s))
      (should (a3madkour-sections/fields s)))
    (dolist (q '(("research/themes" . "status") ("research/questions" . "status")
                 ("works/games" . "status") ("works/games" . "game_kind")
                 ("works/music" . "format") ("works/music" . "platform_embed.kind")))
      (should (a3madkour-sections/enum (car q) (cdr q))))
    (dolist (s '("library/reading" "library/listening"
                 "library/playing" "library/watching"))
      (should (a3madkour-sections/enum s "media_type"))
      (should (a3madkour-sections/enum s "status")))
    (should (equal (a3madkour-sections/variant-case "garden" nil) "concept"))
    (dolist (s '("works/games" "works/music"))
      (let ((ra (a3madkour-sections/required-authored s)))
        (should ra)
        (dolist (p '("title" "date" "lastmod" "draft"))
          (should-not (member p ra)))))
    (let ((themes (a3madkour-sections/emitted-keys "research/themes")))
      (should-not (member "theme" themes))
      (should-not (member "parent_question" themes)))
    (should (equal (alist-get 'to (a3madkour-sections/field
                                   "research/questions" "theme"))
                   "research/themes"))))

(provide 'a3madkour-sections-test)

;;; a3madkour-sections-test.el ends here
```

- [ ] **Step 4: Run, and expect FAIL**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-sections|Cannot open load file|^Ran|unexpected"
```

Expected: the run aborts while loading, with `Cannot open load file ... a3madkour-sections`, because the module does not exist yet.

- [ ] **Step 5: Write the reader**

Create `a3madkour-sections.el`:

```elisp
;;; a3madkour-sections.el --- reader for the site's section contract  -*- lexical-binding: t; -*-

;;; Commentary:

;; Per-section field contracts are NOT defined in elisp.  They live in the
;; site repo at `data/sections.json', which the site's fixture linters read
;; through `tools/sections.py', so the two languages cannot drift.  This
;; module generalises (and replaces) `a3madkour-works-vocab', which did the
;; same for games/music only.
;;
;; A missing or malformed contract is an error, never a skipped check and
;; never a fallback to a hardcoded copy: a fallback would silently restore
;; the drift surface the file exists to remove.
;;
;; No load-time dependency on the publish stack: the site-root helper is
;; required lazily inside `--path', so `a3madkour-publish-frontmatter'
;; (which requires this module) still loads on a bare `emacs -Q'.
;;
;; JSON `false' and `null' decode to nil.  `closed' is not consumed here
;; (the site linter owns the closed-set rule); `store' is read only for the
;; value "data" (library), whose items `a3-publish-mark' leaves alone.

;;; Code:

(require 'json)
(require 'cl-lib)

(defconst a3madkour-sections--rel "data/sections.json"
  "Contract path, relative to the site root.")

(defconst a3madkour-sections--version 1
  "The contract schema version this reader understands.")

(defvar a3madkour-sections-file nil
  "Absolute path of the contract to read instead of the site root's.
nil (the default) resolves `data/sections.json' under the root derived
from `a3madkour-pub/site-data-dir'.")

(defvar a3madkour-sections--cache nil
  "(PATH MTIME . PARSED) for the last read, or nil.
Keyed on mtime as well as path: async publish keeps one Emacs alive
across runs, so an edited contract must be noticed without a restart.")

(defvar a3madkour-pub/site-data-dir)
(declare-function a3madkour-pub-yaml/site-root "a3madkour-publish-yaml")

(defun a3madkour-sections--path ()
  "Absolute path of the contract file."
  (or a3madkour-sections-file
      (progn
        (unless (bound-and-true-p a3madkour-pub/site-data-dir)
          (error "a3madkour-sections: a3madkour-pub/site-data-dir is not set; \
cannot locate %s" a3madkour-sections--rel))
        ;; Lazy: keeps this module free of the org-roam/yaml stack.
        (require 'a3madkour-publish-yaml)
        (expand-file-name a3madkour-sections--rel
                          (a3madkour-pub-yaml/site-root)))))

(defun a3madkour-sections--validate (parsed path)
  "Signal unless PARSED (read from PATH) is a usable version-1 contract."
  (let ((version (and (consp parsed) (alist-get 'version parsed))))
    (unless (equal version a3madkour-sections--version)
      (error "a3madkour-sections: contract at %s has version %S, expected %d"
             path version a3madkour-sections--version)))
  (let ((sections (alist-get 'sections parsed)))
    (unless (consp sections)
      (error "a3madkour-sections: contract at %s has no sections" path))
    (dolist (cell sections)
      (let* ((name (symbol-name (car cell)))
             (fields (alist-get 'fields (cdr cell)))
             (variants (alist-get 'variants (cdr cell))))
        (unless (consp fields)
          (error "a3madkour-sections: section %s in %s has no fields"
                 name path))
        (when variants
          (let ((on (alist-get 'on variants)))
            (unless (and (stringp on) (assq (intern on) fields))
              (error "a3madkour-sections: section %s variants.on %S is \
not a field (%s)" name on path))))))))

(defun a3madkour-sections/read ()
  "Read, validate and cache the contract.  Signal `error' on any problem."
  (let* ((path (a3madkour-sections--path))
         (attrs (file-attributes path))
         (mtime (and attrs (file-attribute-modification-time attrs))))
    (if (and a3madkour-sections--cache
             (equal (car a3madkour-sections--cache) path)
             (equal (cadr a3madkour-sections--cache) mtime))
        (cddr a3madkour-sections--cache)
      (unless attrs
        (error "a3madkour-sections: contract not found at %s" path))
      (let* ((text (with-temp-buffer
                     (insert-file-contents path)
                     (buffer-string)))
             (parsed (condition-case err
                         (json-parse-string text
                                            :object-type 'alist
                                            :array-type 'list
                                            :null-object nil
                                            :false-object nil)
                       (error
                        (error "a3madkour-sections: contract at %s is not \
valid JSON: %S" path err)))))
        (a3madkour-sections--validate parsed path)
        (setq a3madkour-sections--cache (cons path (cons mtime parsed)))
        parsed))))

(defun a3madkour-sections/names ()
  "Section names, as slash-form strings, in file order."
  (mapcar (lambda (c) (symbol-name (car c)))
          (alist-get 'sections (a3madkour-sections/read))))

(defun a3madkour-sections/spec (section)
  "The raw spec alist of SECTION (a slash-form string).  Signal if unknown."
  (or (alist-get (intern section) (alist-get 'sections (a3madkour-sections/read)))
      (error "a3madkour-sections: unknown section %S (contract at %s)"
             section (a3madkour-sections--path))))

(defun a3madkour-sections--cells (fields)
  "FIELDS (a parsed JSON object) as ((NAME-STRING . SPEC) ...)."
  (mapcar (lambda (c) (cons (symbol-name (car c)) (cdr c))) fields))

(defun a3madkour-sections--cases (spec)
  "The parsed `variants.cases' object of section SPEC, or nil."
  (alist-get 'cases (alist-get 'variants spec)))

(defun a3madkour-sections/fields (section &optional variant-case)
  "SECTION's fields as ((NAME . SPEC) ...).
NAME is a string; SPEC an alist keyed by the JSON's field-spec keys as
symbols.  Base fields come first in file order, then the fields of
VARIANT-CASE (a case name string) when given."
  (let* ((spec (a3madkour-sections/spec section))
         (base (a3madkour-sections--cells (alist-get 'fields spec))))
    (if (not variant-case)
        base
      (let ((case (assq (intern variant-case)
                        (a3madkour-sections--cases spec))))
        (unless case
          (error "a3madkour-sections: section %s has no variant case %S"
                 section variant-case))
        (append base (a3madkour-sections--cells
                      (alist-get 'fields (cdr case))))))))

(defun a3madkour-sections/variant-case (section value)
  "Name of SECTION's variant case selected by VALUE, or nil.
VALUE is the buffer's value of the section's `variants.on' field (nil
when that field is absent).  nil when SECTION has no variants.  Signal
when VALUE selects no case."
  (let ((cases (a3madkour-sections--cases (a3madkour-sections/spec section))))
    (when cases
      (or (cl-loop for (name . case) in cases
                   when (member value (alist-get 'values case))
                   return (symbol-name name))
          (error "a3madkour-sections: section %s has no variant case for %S"
                 section value)))))

(defun a3madkour-sections--all-cells (section)
  "Base fields of SECTION, then each case's new fields, de-duplicated."
  (let* ((spec (a3madkour-sections/spec section))
         (cells (a3madkour-sections--cells (alist-get 'fields spec))))
    (dolist (case (a3madkour-sections--cases spec))
      (dolist (f (a3madkour-sections--cells (alist-get 'fields (cdr case))))
        (unless (assoc (car f) cells)
          (setq cells (append cells (list f))))))
    cells))

(defun a3madkour-sections/field (section path)
  "Spec of field PATH in SECTION, searching base fields then every case.
PATH is a field name, or \"OBJECT.SUB\" for a sub-field of an `object'
field.  Signal when absent."
  (let* ((parts (split-string path "\\." t))
         (spec (cdr (assoc (car parts) (a3madkour-sections--all-cells section)))))
    (dolist (p (cdr parts))
      (setq spec (and spec (alist-get (intern p) (alist-get 'fields spec)))))
    (or spec
        (error "a3madkour-sections: section %s has no field %s" section path))))

(defun a3madkour-sections/enum (section path)
  "Allowed values of enum field PATH in SECTION.  Signal if not an enum."
  (let ((spec (a3madkour-sections/field section path)))
    (unless (equal (alist-get 'type spec) "enum")
      (error "a3madkour-sections: %s.%s is not an enum (type %S)"
             section path (alist-get 'type spec)))
    (alist-get 'values spec)))

(defun a3madkour-sections/emitted-keys (section)
  "Every field name legal in SECTION's emitted frontmatter, as strings.
Base fields plus every variant case's, de-duplicated, in file order."
  (mapcar #'car (a3madkour-sections--all-cells section)))

(defun a3madkour-sections/required-authored (section)
  "Base fields of SECTION that are required and not derived by the pipeline."
  (cl-loop for (name . spec) in (a3madkour-sections/fields section)
           when (and (alist-get 'required spec)
                     (not (equal (alist-get 'from spec) "pipeline")))
           collect name))

(provide 'a3madkour-sections)

;;; a3madkour-sections.el ends here
```

- [ ] **Step 6: Run, and expect PASS**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-sections--|^Ran|unexpected"
```

Expected: every `a3madkour-sections--` test passes. The two `real-contract` tests pass if the prerequisite holds, and report `skipped` only if the site checkout is absent. `0 unexpected`.

- [ ] **Step 7: Mutation-test the guards (revert after each)**

| Break | Expected failing test |
|---|---|
| Replace `(unless attrs (error ...not found...))` with `(unless attrs (setq path nil))` | `--fails-closed-when-missing` |
| Cache key: change `(equal (cadr a3madkour-sections--cache) mtime)` to `t` | `--cache-notices-an-edited-file` |
| Delete `:null-object nil` | `--null-and-false-decode-to-nil` (concept case) and `--variant-case-selection` |
| Delete `:false-object nil` | `--null-and-false-decode-to-nil` (`blurb` counted required) |
| Delete the `variants` check in `--validate` | `--fails-closed-on-variants-on-a-non-field` |
| Add `(require 'a3madkour-publish-yaml)` after `(require 'cl-lib)` | `--loads-under-emacs-Q` (yaml is not on the `-Q` load-path) |
| In the fixture JSON, rename `"about": {` to `"colophon": {` | `--real-contract-sections-match-fixture` |

- [ ] **Step 8: Byte-compile check (no warnings)**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && emacs --batch --eval "(setq byte-compile-error-on-warn t)" -L . -f batch-byte-compile a3madkour-sections.el && rm -f a3madkour-sections.elc && echo COMPILED-CLEAN
```

Expected: `COMPILED-CLEAN`. The `.elc` is removed so it can never shadow a later edit.

- [ ] **Step 9: Full suite green**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "^Ran|unexpected"
```

Expected: `0 unexpected`.

- [ ] **Step 10: Commit**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3madkour-sections.el emacs-configs/custom/lisp/a3madkour-sections-test.el emacs-configs/custom/lisp/a3madkour-sections-fixture.el emacs-configs/custom/lisp/a3madkour-sections-fixture.json && git commit -F - <<'EOF'
feat(sections): reader for the site's data/sections.json contract

Generalises a3madkour-works-vocab to every section: reads
<site-root>/data/sections.json (mtime cache, fail-closed, no load-time
deps), exposes spec / fields / variant-case / field / enum /
emitted-keys / required-authored.  JSON false/null decode to nil.
Cross-repo tests pin the fixture's section names to the real file and
check every structural fact the pipeline relies on against it.  No
consumer switched yet.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

### Task 3: `a3madkour-publish-registry.el`, the section table

**Files:**
- Create: `a3madkour-publish-registry.el`, `a3madkour-publish-registry-test.el`.

**Interfaces (Produces, exact):**
- `a3madkour-pub-registry`: defconst, `(("SLASH-NAME" :mode living|deliberate|nil :handler SYMBOL-OR-NIL [:data-file "x.yaml" :default-medium "m"]) ...)`, in `#+HUGO_SECTION:` completion order.
- `(a3madkour-pub-registry/names) -> (STRING ...)`.
- `(a3madkour-pub-registry/entry SECTION) -> PLIST`: signals on an unknown SECTION.
- `(a3madkour-pub-registry/get SECTION PROP) -> VALUE`.
- `(a3madkour-pub-registry/sections-with-mode MODE) -> (STRING ...)`.
- `(a3madkour-pub-registry/sections-for-handler HANDLER) -> (STRING ...)`.
- `(a3madkour-pub-registry/handler SECTION MODE) -> SYMBOL|nil`: the handler when SECTION is registered with MODE; nil otherwise, including for an unknown SECTION.
- `(a3madkour-pub-section/symbol SECTION) -> SYMBOL`: `"works/poetry"` → `works-poetry`. Signals on an unknown SECTION. It is the only slash→hyphen conversion in the codebase.
- `(a3madkour-pub-section/from-symbol SYMBOL) -> STRING`: the inverse. Signals on an unknown symbol.

- [ ] **Step 1: Write the failing tests**

Create `a3madkour-publish-registry-test.el`:

```elisp
;;; a3madkour-publish-registry-test.el --- tests for the section registry  -*- lexical-binding: t; -*-

;;; Code:

(require 'ert)
(require 'cl-lib)
(require 'a3madkour-publish-registry)
(require 'a3madkour-sections)
(require 'a3madkour-sections-fixture)

(ert-deftest a3madkour-pub-registry--unknown-section-signals ()
  (should-error (a3madkour-pub-registry/entry "bogus"))
  (should-not (a3madkour-pub-registry/handler "bogus" 'living)))

(ert-deftest a3madkour-pub-registry--section-symbol-total-and-injective ()
  (let ((syms (mapcar #'a3madkour-pub-section/symbol (a3madkour-pub-registry/names))))
    (should (eq (a3madkour-pub-section/symbol "works/poetry") 'works-poetry))
    (should (eq (a3madkour-pub-section/symbol "research/themes") 'research-themes))
    (should (eq (a3madkour-pub-section/symbol "garden") 'garden))
    (should (= (length syms) (length (delete-dups (copy-sequence syms)))))
    (dolist (s (a3madkour-pub-registry/names))
      (should (equal (a3madkour-pub-section/from-symbol
                      (a3madkour-pub-section/symbol s))
                     s)))
    (should-error (a3madkour-pub-section/symbol "works/bogus"))
    (should-error (a3madkour-pub-section/from-symbol 'works-bogus))))

(ert-deftest a3madkour-pub-registry--modes-and-handlers ()
  (should (equal (a3madkour-pub-registry/sections-with-mode 'deliberate)
                 '("essays" "works/poetry")))
  (should (equal (a3madkour-pub-registry/sections-with-mode nil)
                 '("streams" "about")))
  (should (eq (a3madkour-pub-registry/handler "garden" 'living)
              'a3madkour-pub-garden/publish-garden-file))
  (should-not (a3madkour-pub-registry/handler "essays" 'living))
  (should (eq (a3madkour-pub-registry/handler "essays" 'deliberate)
              'a3madkour-pub-essays/publish-essay-file))
  (should-not (a3madkour-pub-registry/handler "streams" 'living))
  (should (equal (a3madkour-pub-registry/sections-for-handler
                  'a3madkour-pub-works/publish-works-file)
                 '("works/games" "works/music"))))

(ert-deftest a3madkour-pub-registry--every-handler-fboundp-after-load ()
  (dolist (f '(a3madkour-publish-garden a3madkour-publish-library
               a3madkour-publish-research a3madkour-publish-recipes
               a3madkour-publish-works a3madkour-publish-essays
               a3madkour-publish-poetry))
    (require f))
  (dolist (s (a3madkour-pub-registry/names))
    (let ((h (a3madkour-pub-registry/get s :handler)))
      (when h
        (should (fboundp h))))))

(ert-deftest a3madkour-pub-registry--library-entries-carry-data-config ()
  (let ((libs (a3madkour-pub-registry/sections-for-handler
               'a3madkour-pub-library/publish-library-file)))
    (should (equal libs '("library/reading" "library/listening"
                          "library/playing" "library/watching")))
    (dolist (s libs)
      (should (string-suffix-p ".yaml" (a3madkour-pub-registry/get s :data-file)))
      (should (member (a3madkour-pub-registry/get s :default-medium)
                      (a3madkour-sections/enum s "media_type"))))))

(ert-deftest a3madkour-pub-registry--keys-equal-fixture-contract ()
  (should (equal (sort (a3madkour-pub-registry/names) #'string<)
                 (sort (a3madkour-sections/names) #'string<))))

(ert-deftest a3madkour-pub-registry--keys-equal-real-sections-json ()
  "Cross-repo: the registry's section keys equal the site file's."
  (a3madkour-sections-test--with-real-site
    (should (equal (sort (a3madkour-pub-registry/names) #'string<)
                   (sort (a3madkour-sections/names) #'string<)))
    (dolist (s (a3madkour-pub-registry/sections-for-handler
                'a3madkour-pub-library/publish-library-file))
      (should (member (a3madkour-pub-registry/get s :default-medium)
                      (a3madkour-sections/enum s "media_type"))))))

(ert-deftest a3madkour-pub-registry--loads-without-handler-modules ()
  "Handlers are named, never required: the registry loads on `emacs -Q'
and pulls in no handler or dispatch module."
  (let* ((dir (file-name-directory (locate-library "a3madkour-publish-registry")))
         (emacs (expand-file-name invocation-name invocation-directory))
         (status (call-process
                  emacs nil nil nil "-Q" "--batch"
                  "--eval" "(setq load-prefer-newer t)"
                  "-L" dir
                  "--eval" "(require 'a3madkour-publish-registry)"
                  "--eval" "(kill-emacs (if (or (featurep 'a3madkour-publish-garden) (featurep 'a3madkour-publish-deliberate) (featurep 'a3madkour-publish-essays) (featurep 'a3madkour-publish)) 3 0))")))
    (should (equal status 0))))

(provide 'a3madkour-publish-registry-test)

;;; a3madkour-publish-registry-test.el ends here
```

- [ ] **Step 2: Run, and expect FAIL**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-registry--|Cannot open load file|^Ran|unexpected"
```

Expected: the load aborts with `Cannot open load file ... a3madkour-publish-registry`.

- [ ] **Step 3: Write the registry**

Create `a3madkour-publish-registry.el`:

```elisp
;;; a3madkour-publish-registry.el --- the one table of publishable sections  -*- lexical-binding: t; -*-

;;; Commentary:

;; Every section the publisher knows, stored once in slash form.  It
;; replaces the scattered lists (`a3madkour-pub/sections',
;; `a3madkour-pub-deliberate-sections', the living and deliberate handler
;; tables, frontmatter's `--known-sections', library's `--config', works'
;; `--sections') and the hand-written slash→hyphen converters.
;;
;; Holds only what the PIPELINE needs: mode, handler, library data config.
;; Field contracts live in the site's `data/sections.json' (read by
;; `a3madkour-sections').  The two key sets are pinned equal by a
;; cross-repo test.
;;
;; Handlers are named by SYMBOL and resolved when called; this module
;; requires none of them.  That removes the old load-order coupling (five
;; `with-eval-after-load' registrations) and keeps `a3madkour-publish' from
;; depending on the deliberate modules.  A registered handler that is not
;; loaded at dispatch is a loud per-file error, not a silent skip.

;;; Code:

(defconst a3madkour-pub-registry
  '(("essays"             :mode deliberate
     :handler a3madkour-pub-essays/publish-essay-file)
    ("garden"             :mode living
     :handler a3madkour-pub-garden/publish-garden-file)
    ("research/themes"    :mode living
     :handler a3madkour-pub-research/publish-research-file)
    ("research/questions" :mode living
     :handler a3madkour-pub-research/publish-research-file)
    ("works/games"        :mode living
     :handler a3madkour-pub-works/publish-works-file)
    ("works/music"        :mode living
     :handler a3madkour-pub-works/publish-works-file)
    ("works/poetry"       :mode deliberate
     :handler a3madkour-pub-poetry/publish-poetry-file)
    ("library/reading"    :mode living
     :handler a3madkour-pub-library/publish-library-file
     :data-file "reading.yaml"   :default-medium "book")
    ("library/listening"  :mode living
     :handler a3madkour-pub-library/publish-library-file
     :data-file "listening.yaml" :default-medium "album")
    ("library/playing"    :mode living
     :handler a3madkour-pub-library/publish-library-file
     :data-file "playing.yaml"   :default-medium "game")
    ("library/watching"   :mode living
     :handler a3madkour-pub-library/publish-library-file
     :data-file "watching.yaml"  :default-medium "film")
    ("streams"            :mode nil :handler nil)
    ("recipes"            :mode living
     :handler a3madkour-pub-recipes/publish-recipe-file)
    ("about"              :mode nil :handler nil))
  "Every publishable section, keyed by its `#+HUGO_SECTION:' slash form.

Each entry is (SECTION . PLIST):
  :mode            `living' (published by `a3-publish-living'),
                   `deliberate' (by `a3-publish-deliberate'), or nil
                   (valid section, no handler yet: streams, about).
  :handler         handler function SYMBOL, signature
                   (file run &key on-done); resolved at dispatch.
  :data-file       library only: the data/ yaml file the section writes.
  :default-medium  library only: the media_type used when a heading
                   declares none.

Order is the `a3-publish-mark' completion order.")

(defun a3madkour-pub-registry/names ()
  "Every registered section, as slash-form strings, in registry order."
  (mapcar #'car a3madkour-pub-registry))

(defun a3madkour-pub-registry/entry (section)
  "The plist registered for SECTION.  Signal if SECTION is unknown."
  (let ((cell (assoc section a3madkour-pub-registry)))
    (unless cell
      (error "a3madkour-pub-registry: unknown section %S" section))
    (cdr cell)))

(defun a3madkour-pub-registry/get (section prop)
  "Property PROP of SECTION's registry entry."
  (plist-get (a3madkour-pub-registry/entry section) prop))

(defun a3madkour-pub-registry/sections-with-mode (mode)
  "Sections whose :mode is MODE, in registry order."
  (let (out)
    (dolist (cell a3madkour-pub-registry (nreverse out))
      (when (eq (plist-get (cdr cell) :mode) mode)
        (push (car cell) out)))))

(defun a3madkour-pub-registry/sections-for-handler (handler)
  "Sections whose :handler is HANDLER, in registry order."
  (let (out)
    (dolist (cell a3madkour-pub-registry (nreverse out))
      (when (eq (plist-get (cdr cell) :handler) handler)
        (push (car cell) out)))))

(defun a3madkour-pub-registry/handler (section mode)
  "Handler symbol of SECTION when it is registered with MODE, else nil.
An unknown SECTION also yields nil: callers see the section first as a
note's `#+HUGO_SECTION:', which `a3madkour-pub/valid-section-p' guards."
  (let ((entry (cdr (assoc section a3madkour-pub-registry))))
    (and entry
         (eq (plist-get entry :mode) mode)
         (plist-get entry :handler))))

(defun a3madkour-pub-section/symbol (section)
  "The hyphen-form symbol of slash-form SECTION.
\"works/poetry\" -> `works-poetry'.  The only slash->hyphen conversion in
the publisher.  Signal if SECTION is not registered."
  (a3madkour-pub-registry/entry section)
  (intern (replace-regexp-in-string "/" "-" section)))

(defun a3madkour-pub-section/from-symbol (symbol)
  "The slash-form section whose hyphen form is SYMBOL.  Signal if none."
  (or (catch 'found
        (dolist (s (a3madkour-pub-registry/names))
          (when (eq (a3madkour-pub-section/symbol s) symbol)
            (throw 'found s))))
      (error "a3madkour-pub-registry: no section for symbol %S" symbol)))

(provide 'a3madkour-publish-registry)

;;; a3madkour-publish-registry.el ends here
```

- [ ] **Step 4: Run, and expect PASS**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-registry--|^Ran|unexpected"
```

Expected: every `a3madkour-pub-registry--` test passes, and `0 unexpected`.

- [ ] **Step 5: Mutation-test the guards (revert after each)**

| Break | Expected failing test |
|---|---|
| Add `("colophon" :mode nil :handler nil)` to the registry | `--keys-equal-fixture-contract` and `--keys-equal-real-sections-json` |
| Add `(require 'a3madkour-publish-garden)` below the Commentary | `--loads-without-handler-modules` |
| Change library/watching `:default-medium "film"` to `"films"` | `--library-entries-carry-data-config` and `--keys-equal-real-sections-json` |
| Change `--symbol`'s `"-"` to `""` | `--section-symbol-total-and-injective` |

- [ ] **Step 6: Byte-compile check**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && emacs --batch --eval "(setq byte-compile-error-on-warn t)" -L . -f batch-byte-compile a3madkour-publish-registry.el && rm -f a3madkour-publish-registry.elc && echo COMPILED-CLEAN
```

Expected: `COMPILED-CLEAN`.

- [ ] **Step 7: Full suite green**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "^Ran|unexpected"
```

- [ ] **Step 8: Commit**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-registry.el emacs-configs/custom/lisp/a3madkour-publish-registry-test.el && git commit -F - <<'EOF'
feat(registry): one table of publishable sections

a3madkour-pub-registry holds, per slash-form section, its publish mode,
handler symbol and (library) data file + default medium, plus the only
slash->hyphen converter, a3madkour-pub-section/symbol.  Handlers are
named, never required.  Cross-repo test: registry keys == the site's
data/sections.json keys.  Nothing consumes it yet.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

### Task 4: Switch dispatch and the derived lists to the registry; delete the old lists

**Files:**
- Modify: `a3madkour-publish.el:20-53` and `:158-165`; `a3madkour-publish-living.el` (whole file); `a3madkour-publish-deliberate.el:13-58` and `:105-110`; `a3madkour-publish-frontmatter.el:36-68`; `a3madkour-publish-works.el:137-151`; `a3madkour-publish-research.el:214-218` and `:274`; `a3madkour-publish-library.el:10-12`, `:16-59`; `a3madkour-publish-author.el:181-183`; header comments in `-garden.el:9`, `-research.el:15`, `-works.el:5-6`, `-essays.el:10`.
- Tests: `a3madkour-publish-living-test.el`, `-deliberate-test.el`, `-poetry-test.el`, `-works-test.el`, `-unpublish-test.el`, `-research-test.el`, `-library-test.el`, `-author-test.el`.

**Interfaces:**
- Consumes: Task 3's registry API and Task 2's `a3madkour-sections/enum`.
- Produces: `(a3madkour-pub-living--dispatch TRIPLE RUN REPORT)`, `(a3madkour-pub-deliberate--handler-for SECTION FILE) -> SYMBOL` (signals), `(a3madkour-pub-works--sections) -> (STRING ...)`. `a3madkour-pub/sections` and `a3madkour-pub-deliberate-sections` keep their names and values (now derived). `a3madkour-pub-library--config-for` keeps its 4-element return shape.
- Deletes: `a3madkour-pub-living--handlers`, `a3madkour-pub-deliberate--handlers`, the 5 `with-eval-after-load` blocks, `a3madkour-pub-works--sections` (defconst), `a3madkour-pub-research--section-to-normalize-sym`, `a3madkour-pub-library--config`.

- [ ] **Step 1: Write the new failing tests**

Append to `a3madkour-publish-living-test.el` before its `(provide ...)`:

```elisp
;; -- Section registry: dispatch follows the registry, loudly --

(ert-deftest a3madkour-pub-living--collect-follows-registry-modes ()
  "Only `:mode living' sections yield triples; deliberate (essays) and
handler-less (streams) sections are skipped."
  (let ((dir (make-temp-file "a3-living-modes" t)))
    (unwind-protect
        (progn
          (dolist (spec '(("g.org" . "garden") ("e.org" . "essays")
                          ("s.org" . "streams")))
            (with-temp-file (expand-file-name (car spec) dir)
              (insert (format "#+TITLE: %s\n#+HUGO_SECTION: %s\n#+HUGO_PUBLISH: t\n"
                              (car spec) (cdr spec)))))
          (let ((a3madkour-pub/org-notes-dir dir))
            (a3madkour-pub--reset-metadata-cache)
            (let ((triples (a3madkour-pub-living--collect-triples)))
              (should (equal (mapcar #'car triples) '("garden")))
              (should (eq (nth 2 (car triples))
                          'a3madkour-pub-garden/publish-garden-file)))))
      (delete-directory dir t))))

(ert-deftest a3madkour-pub-living-test/unloaded-handler-is-a-loud-per-file-error ()
  "A registered handler that is not `fboundp' reports `err' for its file
and logs a `handler-missing' step naming the function; the other files
still run.  Intended behaviour change: before the registry the section
was silently skipped, so its pages looked removed (S1 row 9)."
  (let ((captured 'unset) (logged nil) (other-ran nil))
    (a3-pub-living-test--capture-finish-status captured
      (cl-letf (((symbol-function 'a3madkour-pub-living--collect-triples)
                 (lambda ()
                   (list (list "garden" "/a.org" 'a3madkour-pub-living-test--no-such-handler)
                         (list "garden" "/b.org" 'ok-h))))
                ((symbol-function 'ok-h)
                 (lambda (_f _r &rest rest)
                   (setq other-ran t)
                   (funcall (plist-get rest :on-done) 'ok)))
                ((symbol-function 'a3-pub-async/log-step)
                 (lambda (_run label status &rest kw)
                   (push (list label status (plist-get kw :err-snippet)) logged))))
        (a3-publish-living)))
    (should (eq captured 'err))
    (should other-ran)
    (should (cl-some (lambda (l)
                       (and (equal (nth 0 l) "handler-missing")
                            (eq (nth 1 l) :err)
                            (string-match-p "a3madkour-pub-living-test--no-such-handler"
                                            (nth 2 l))))
                     logged))))
```

Append to `a3madkour-publish-deliberate-test.el` before its `(provide ...)` (or at the end if it has none):

```elisp
(ert-deftest a3madkour-pub-deliberate-test/unloaded-handler-errors-before-begin ()
  "A registered deliberate handler that is not loaded signals naming the
function, before `begin-publish' takes the run lock."
  (cl-letf (((symbol-function 'a3madkour-pub--resolve-file-or-id) (lambda (_) "/fake/e.org"))
            ((symbol-function 'a3madkour-pub/note-section) (lambda (_) "essays"))
            ((symbol-function 'a3madkour-pub-registry/handler)
             (lambda (&rest _) 'a3madkour-pub-deliberate-test--no-such-handler))
            ((symbol-function 'a3-pub-async/begin-publish)
             (lambda (&rest _) (error "begin-publish must not run"))))
    (let ((err (should-error (a3-publish-deliberate "/fake/e.org"))))
      (should (string-match-p
               "a3madkour-pub-deliberate-test--no-such-handler.*is not loaded"
               (error-message-string err))))))
```

Append to `a3madkour-publish-library-test.el` before its `(provide ...)`:

```elisp
(ert-deftest a3madkour-pub-library--config-reads-registry-and-contract ()
  "yaml file + default medium come from the registry, the allowed lists
from the site's section contract."
  (should (equal (a3madkour-pub-library--config-for "library/reading")
                 '("reading.yaml" "book" ("book")
                   ("finished" "reading" "queued" "abandoned"))))
  (a3madkour-sections-test--with-root
      (a3madkour-sections-test/mutate "\"abandoned\"" "\"dnf\"")
    (should (member "dnf" (nth 3 (a3madkour-pub-library--config-for
                                  "library/reading"))))))
```

Add `(require 'a3madkour-sections-fixture)` after the existing `require` lines at the top of each of `a3madkour-publish-library-test.el`, `a3madkour-publish-author-test.el`, `a3madkour-publish-living-test.el` and `a3madkour-publish-deliberate-test.el`.

- [ ] **Step 2: Run, and expect FAIL**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "collect-follows-registry-modes|unloaded-handler|config-reads-registry|^Ran|unexpected"
```

Expected: `collect-follows-registry-modes` PASSES already. Every handler module is loaded in the test session, so the old eval-after-load table yields the same garden-only triple. It is a regression pin for the rewrite, and its mutation is in Step 15. `unloaded-handler-is-a-loud-per-file-error` FAILS: no `handler-missing` log. `unloaded-handler-errors-before-begin` FAILS: the stub of `a3madkour-pub-registry/handler` is ignored, so the essays handler runs and `begin-publish` errors with the wrong message. `config-reads-registry-and-contract` FAILS on its mutated assertion.

- [ ] **Step 3: `a3madkour-publish.el`: derive both lists**

After `(require 'a3madkour-publish-id)` (line 32) add:

```elisp
(require 'a3madkour-publish-registry)
```

Replace lines 37–47 (the `a3madkour-pub/sections` defconst) with:

```elisp
(defconst a3madkour-pub/sections (a3madkour-pub-registry/names)
  "Permitted values for the org-side `#+HUGO_SECTION:' keyword.
Derived from `a3madkour-pub-registry'; see the phase-3 design spec §4.")
```

Replace lines 158–165 (the `a3madkour-pub-deliberate-sections` defconst) with:

```elisp
(defconst a3madkour-pub-deliberate-sections
  (a3madkour-pub-registry/sections-with-mode 'deliberate)
  "URL sections published only by `a3-publish-deliberate', never by a living run.

A living run's new-set cannot contain these, so the living orphan sweep must
not treat their manifest entries as removed.  Derived from the registry's
`:mode deliberate' entries, so it cannot disagree with the dispatch.")
```

- [ ] **Step 4: `a3madkour-publish-living.el`: replace the whole file**

```elisp
;;; a3madkour-publish-living.el --- publish-living top-level command  -*- lexical-binding: t; -*-

;;; Commentary:

;; Top-level command for sub-project B's living-surfaces publish.
;; Wraps the begin/walk/finish lifecycle around every section that
;; `a3madkour-pub-registry' marks `:mode living'.
;;
;; Handlers are named by symbol in the registry and resolved at dispatch.
;; A registered handler that is not loaded is a loud per-file error: the
;; file reports `err' and the run buffer logs `handler-missing' naming the
;; function.  It used to be a silent skip, which made the section's pages
;; look removed to the orphan sweep (S1 row 9).
;;
;; Idempotency contract (per design spec §11): running with no source
;; changes produces zero file diffs in content/ + data/.

;;; Code:

(require 'a3madkour-publish)
(require 'a3madkour-publish-registry)
(require 'a3madkour-publish-async)
(require 'a3madkour-publish-unpublish)

(defun a3madkour-pub-living--collect-triples ()
  "Return (section file handler) triples for every living-section file
under `a3madkour-pub/org-notes-dir'.

Walks the notes tree exactly once.  HANDLER is the registry's symbol; it
is not checked here (see `a3madkour-pub-living--dispatch')."
  (let ((triples nil))
    (dolist (file (directory-files-recursively
                   a3madkour-pub/org-notes-dir "\\.org\\'"))
      (let ((section (a3madkour-pub/note-section file)))
        (when section
          (let ((handler (a3madkour-pub-registry/handler section 'living)))
            (when handler
              (push (list section file handler) triples))))))
    (nreverse triples)))

(defun a3madkour-pub-living--dispatch (triple run report)
  "Run TRIPLE's handler on its file, reporting the outcome via REPORT.
A handler that is not `fboundp' reports `err' and logs a
`handler-missing' step naming the function."
  (let ((section (nth 0 triple))
        (file (nth 1 triple))
        (handler (nth 2 triple)))
    (if (not (fboundp handler))
        (let ((msg (format "%s: handler `%s' for section %s is not loaded"
                           file handler section)))
          (message "a3-publish-living: %s" msg)
          (a3-pub-async/log-step run "handler-missing" :err :err-snippet msg)
          (funcall report 'err))
      (condition-case _err
          (funcall handler file run
                   :on-done (lambda (s) (funcall report s)))
        (error (funcall report 'err))))))

;;;###autoload
(defun a3-publish-living ()
  "Publish all living-section source notes from `org-notes-dir'.

Async lifecycle: walks every living section's source set into a flat
\(section file handler) triple list, dispatches each in parallel, and
calls finish-publish once after the barrier reports done."
  (interactive)
  (let* ((triples (a3madkour-pub-living--collect-triples))
         (n (length triples))
         (run (a3-pub-async/begin-publish
               :scope 'living
               :source-label (format "living (%d notes)" n)
               :planned-steps n)))
    (if (zerop n)
        (a3-pub-async/finish-publish run :scope 'living :status 'ok)
      (let ((report (a3-pub-async/barrier
                     n :on-all-done
                     (lambda (results)
                       (let ((status (if (cl-some (lambda (r) (eq r 'err)) results)
                                         'err 'ok)))
                         (a3-pub-async/finish-publish
                          run :scope 'living :status status))))))
        (dolist (triple triples)
          (a3madkour-pub-living--dispatch triple run report))))))

(provide 'a3madkour-publish-living)

;;; a3madkour-publish-living.el ends here
```

- [ ] **Step 5: `a3madkour-publish-deliberate.el`**

After `(require 'a3madkour-publish)` (line 13) add `(require 'a3madkour-publish-registry)`.

Replace lines 20–24 (the `a3madkour-pub-deliberate--handlers` defvar) with:

```elisp
(defun a3madkour-pub-deliberate--handler-for (section file)
  "The deliberate handler for SECTION (FILE is for the message).
Signal when SECTION is not deliberate in `a3madkour-pub-registry', or
when its handler is not loaded; both before any run lock is taken."
  (let ((handler (a3madkour-pub-registry/handler (or section "") 'deliberate)))
    (unless handler
      (error "a3madkour-pub-deliberate: no handler registered for section %S \
\(file: %s)" section file))
    (unless (fboundp handler)
      (error "a3madkour-pub-deliberate: handler `%s' for section %s is not \
loaded (file: %s)" handler section file))
    handler))
```

In `a3-publish-deliberate`, replace lines 36–39:

```elisp
         (handler (cdr (assq (intern (or section "")) a3madkour-pub-deliberate--handlers))))
    (unless handler
      (error "a3madkour-pub-deliberate: no handler registered for section %S (file: %s)"
             section file))
```

with:

```elisp
         (handler (a3madkour-pub-deliberate--handler-for section file)))
```

In `a3-unpublish-deliberate`, replace:

```elisp
      (unless (assq (intern section) a3madkour-pub-deliberate--handlers)
```

with:

```elisp
      (unless (member section a3madkour-pub-deliberate-sections)
```

- [ ] **Step 6: `a3madkour-publish-frontmatter.el`: derive `--known-sections`**

After `(require 'a3madkour-publish-keywords)` (line 36) add `(require 'a3madkour-publish-registry)`. Replace lines 60–68 with:

```elisp
(defconst a3madkour-pub-frontmatter--known-sections
  (mapcar #'a3madkour-pub-section/symbol (a3madkour-pub-registry/names))
  "Closed set of section symbols `normalize' accepts.
Derived from `a3madkour-pub-registry' (hyphen form of every section).")
```

- [ ] **Step 7: `a3madkour-publish-works.el`: derive the served sections**

Add `(require 'a3madkour-publish-registry)` after `(require 'a3madkour-publish)` (line 18). Replace lines 137–151 with:

```elisp
(defun a3madkour-pub-works--sections ()
  "Slash-form sections this handler serves, from `a3madkour-pub-registry'."
  (a3madkour-pub-registry/sections-for-handler
   'a3madkour-pub-works/publish-works-file))

(defun a3madkour-pub-works--bundle-subdir (section)
  "Content subdirectory for SECTION.  Signals for an unserved section."
  (unless (member section (a3madkour-pub-works--sections))
    (error "a3madkour-pub-works: unserved section %S" section))
  section)

(defun a3madkour-pub-works--normalize-symbol (section)
  "Hyphen-form normalize symbol for slash-form SECTION."
  (a3madkour-pub-works--bundle-subdir section)
  (a3madkour-pub-section/symbol section))
```

Then run `grep -n "a3madkour-pub-works--sections" a3madkour-*.el`. Every hit must be a call `(a3madkour-pub-works--sections)`, never a bare variable reference. Fix any bare reference in a test file by adding the parentheses.

- [ ] **Step 8: `a3madkour-publish-research.el`: drop the converter**

Delete lines 214–218 (`a3madkour-pub-research--section-to-normalize-sym`). At line 274 replace `(a3madkour-pub-research--section-to-normalize-sym section)` with `(a3madkour-pub-section/symbol section)`.

- [ ] **Step 9: `a3madkour-publish-library.el`: config from the registry and the contract**

After `(require 'a3madkour-publish-history)` (line 22) add:

```elisp
(require 'a3madkour-publish-registry)
(require 'a3madkour-sections)
```

Replace lines 24–59 (the `--config` defconst, `--config-for` and `/sections`) with:

```elisp
(defun a3madkour-pub-library/sections ()
  "The library section strings (e.g. \"library/reading\"), from the registry."
  (a3madkour-pub-registry/sections-for-handler
   'a3madkour-pub-library/publish-library-file))

(defun a3madkour-pub-library--config-for (section)
  "Return (yaml-file default-mt allowed-mt allowed-status) for SECTION.
SECTION is the slash-form `#+HUGO_SECTION:' string.  The yaml file and
default medium come from `a3madkour-pub-registry'; the allowed media
types and statuses from the site's section contract (`a3madkour-sections',
which fails closed).  Errors when SECTION is not a library section."
  (unless (member section (a3madkour-pub-library/sections))
    (error "a3madkour-pub-library: unknown library section %S" section))
  (list (a3madkour-pub-registry/get section :data-file)
        (a3madkour-pub-registry/get section :default-medium)
        (a3madkour-sections/enum section "media_type")
        (a3madkour-sections/enum section "status")))
```

- [ ] **Step 10: `a3madkour-publish-author.el`: default medium from the registry**

Add `(require 'a3madkour-publish-registry)` after `(require 'a3madkour-publish-library)`. Replace lines 181–183 with:

```elisp
(defun a3madkour-pub-author--default-medium-for (section)
  "Return the default medium string for SECTION (a library section)."
  (a3madkour-pub-registry/get section :default-medium))
```

- [ ] **Step 11: Header comments that named the deleted tables**

Edit each, replacing exactly:
- `a3madkour-publish-garden.el` line 9: ``;; Registered into `a3madkour-pub-living--handlers' (see Task 11) as`` → ``;; Registered in `a3madkour-pub-registry' as``.
- `a3madkour-publish-library.el` line 10: ``;; Registered into `a3madkour-pub-living--handlers' as four entries`` → ``;; Registered in `a3madkour-pub-registry' as four entries``. Line 12: ``;; `publish-library-file' entry point) by `a3madkour-publish-living'.`` → ``;; `publish-library-file' entry point).``.
- `a3madkour-publish-research.el` line 15: ``;; Registered into `a3madkour-pub-living--handlers' as two entries`` → ``;; Registered in `a3madkour-pub-registry' as two entries``. Line 17: ``;; entry point) by `a3madkour-publish-living'.`` → ``;; entry point).``.
- `a3madkour-publish-works.el` line 6: ``;; `a3madkour-pub-living--handlers' (works/games, works/music) against a`` → ``;; `a3madkour-pub-registry' (works/games, works/music) against a``.
- `a3madkour-publish-essays.el` line 10: ``;; Registered into `a3madkour-pub-deliberate--handlers' (see Task 9) as`` → ``;; Registered in `a3madkour-pub-registry' as``.

- [ ] **Step 12: Port the tests that read the deleted tables**

`a3madkour-publish-living-test.el`: replace the three `-handlers-registered` tests with:

```elisp
(ert-deftest a3madkour-pub-living-test/garden-handler-registered ()
  "The registry names garden's living handler (slash-form string key)."
  (should (eq (a3madkour-pub-registry/handler "garden" 'living)
              'a3madkour-pub-garden/publish-garden-file)))

(ert-deftest a3madkour-pub-living-test/library-handlers-registered ()
  "All four library sections are living, on `publish-library-file'."
  (dolist (section '("library/reading" "library/listening"
                     "library/playing" "library/watching"))
    (should (eq (a3madkour-pub-registry/handler section 'living)
                'a3madkour-pub-library/publish-library-file))))

(ert-deftest a3madkour-pub-living-test/research-handlers-registered ()
  "Both research sections are living, on `publish-research-file'."
  (dolist (section '("research/themes" "research/questions"))
    (should (eq (a3madkour-pub-registry/handler section 'living)
                'a3madkour-pub-research/publish-research-file))))
```

In `--collect-walks-tree-once`, replace

```elisp
          (let ((a3madkour-pub/org-notes-dir dir)
                (a3madkour-pub-living--handlers
                 '(("garden" . ignore) ("recipes" . ignore) ("works/games" . ignore))))
```

with `(let ((a3madkour-pub/org-notes-dir dir))`. In `--collect-yields-one-triple-per-match`, replace

```elisp
          (let ((a3madkour-pub/org-notes-dir dir)
                (a3madkour-pub-living--handlers
                 '(("garden" . ignore) ("recipes" . ignore))))
```

with `(let ((a3madkour-pub/org-notes-dir dir))`. Also update the comment at lines 8–10 to read: `;; Loaded so the P4.1 end-to-end idempotency test drives a real living-section handler (the registry names it; this makes it fboundp).`

`a3madkour-publish-deliberate-test.el`: replace `essays-handler-registered`'s body with

```elisp
  (should (eq (a3madkour-pub-registry/handler "essays" 'deliberate)
              'a3madkour-pub-essays/publish-essay-file)))
```

(keep its `ert-deftest` line and docstring, and drop the `(require 'a3madkour-publish-deliberate)` line inside it). In `citations-emit-fires-after-finish`, replace

```elisp
  (let ((calls nil)
        (a3madkour-pub-deliberate--handlers
         (list (cons 'essays
                     (lambda (_file _run &rest rest)
                       (funcall (plist-get rest :on-done) 'ok))))))
    (cl-letf (((symbol-function 'a3madkour-pub/begin-publish) (lambda () nil))
```

with

```elisp
  (let ((calls nil))
    (cl-letf (((symbol-function 'a3madkour-pub-deliberate--handler-for)
               (lambda (&rest _)
                 (lambda (_file _run &rest rest)
                   (funcall (plist-get rest :on-done) 'ok))))
              ((symbol-function 'a3madkour-pub/begin-publish) (lambda () nil))
```

`a3madkour-publish-poetry-test.el`: replace `dispatch-registered`'s body with

```elisp
  (should (eq (a3madkour-pub-registry/handler "works/poetry" 'deliberate)
              'a3madkour-pub-poetry/publish-poetry-file)))
```

`a3madkour-publish-works-test.el`: replace `registers-both-sections`'s body with

```elisp
  (should (eq (a3madkour-pub-registry/handler "works/games" 'living)
              'a3madkour-pub-works/publish-works-file))
  (should (eq (a3madkour-pub-registry/handler "works/music" 'living)
              'a3madkour-pub-works/publish-works-file)))
```

`a3madkour-publish-unpublish-test.el`: replace `deliberate-sections-match-handler-registry` with

```elisp
(ert-deftest a3madkour-pub-unpublish-test/deliberate-sections-match-handler-registry ()
  "The sweep's deliberate-section list is exactly the sections
`a3-publish-deliberate' dispatches, and none of them is living — a living
run must never sweep a deliberate section's pages."
  (require 'a3madkour-publish-deliberate)
  (should a3madkour-pub-deliberate-sections)
  (dolist (s a3madkour-pub-deliberate-sections)
    (should (fboundp (a3madkour-pub-deliberate--handler-for s "test")))
    (should-not (a3madkour-pub-registry/handler s 'living))))
```

`a3madkour-publish-research-test.el`: delete the `a3madkour-pub-research--section-to-normalize-sym` test, which `a3madkour-pub-registry--section-symbol-total-and-injective` now covers.

- [ ] **Step 13: No reference to a deleted symbol survives**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && grep -n "living--handlers\|deliberate--handlers\|works--sections\b\|section-to-normalize-sym\|pub-library--config\b" a3madkour-*.el
```

Expected: only calls `(a3madkour-pub-works--sections)`, and no other hits.

- [ ] **Step 13b: Site integration tests seed `data/sections.json` into their tmp roots**

From this task on, a publish reads `data/sections.json` from the site root it is pointed at (library config here; essays, research and poetry normalizers in Task 5; works in Task 6). `tools/test_publish_integration.py` (site repo; a manual, not CI, test) builds tmp site roots without it, so every class that publishes would fail closed. Add one helper and call it at every place that sets `A3_PUB_SITE_DATA_DIR`.

Add next to `_emacs_eval` (around `tools/test_publish_integration.py:53`):

```python
def _seed_sections(site_data_dir) -> None:
    """Copy the live section contract into a tmp site's data dir.

    The elisp publisher reads `data/sections.json` from the site root it
    publishes into and fails closed without it.  Copied from the live file,
    never written out, so the tmp root cannot drift from the contract.
    """
    dst = Path(site_data_dir) / "sections.json"
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SITE_ROOT / "data" / "sections.json", dst)
```

Then call `_seed_sections(...)` with the same data-dir value immediately before each `env["A3_PUB_SITE_DATA_DIR"] = ...` assignment. The value is `site_data_dir` in `_publish_living_impl`, and `os.path.join(self.site_root, "data")` or `self.site_root / "data"` in the essays, citation-roundtrip, sync-purges and poetry classes. Find them with:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && grep -n 'env\["A3_PUB_SITE_DATA_DIR"\]' tools/test_publish_integration.py
```

Expected after the edit: every hit is preceded by a `_seed_sections(` line.

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && grep -n -B1 'env\["A3_PUB_SITE_DATA_DIR"\]' tools/test_publish_integration.py | grep -c "_seed_sections("
```

Expected: the same count as the first grep (5 today).

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/test_publish_integration.py 2>&1 | tail -3
```

Expected: `OK`. If it prints `OK (skipped=N)` with every class skipped, the prerequisites are missing and the run proves nothing; fix the prerequisites first.

Mutation: comment out the `shutil.copyfile` line in `_seed_sections`. Expected: `TestLibraryPublishLiving` fails with the contract-not-found error. Revert.

Commit in the site repo, separately from the dotfiles commit in Step 16:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && git add tools/test_publish_integration.py && git commit -F - <<'EOF'
test(integration): seed data/sections.json into tmp site roots

The elisp publisher now reads the section contract from the site root it
publishes into and fails closed without it.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

Because Task 6 Step 7 then finds the poetry root already seeded, its part (b) reduces to deleting the old `works-vocab.json` copy and its comment.

- [ ] **Step 14: Run, and expect PASS; then the full suite**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "collect-follows-registry-modes|unloaded-handler|config-reads-registry|handlers-registered|registers-both|dispatch-registered|deliberate-sections-match|^Ran|unexpected"
```

Expected: all listed tests pass, and `0 unexpected`.

- [ ] **Step 15: Mutation-test the guards (revert after each)**

| Break | Expected failing test |
|---|---|
| In `--dispatch`, replace the `(if (not (fboundp handler)) ...)` with just its `condition-case` else-branch | `unloaded-handler-is-a-loud-per-file-error` (no `handler-missing` log) |
| In `--handler-for`, delete the `(unless (fboundp handler) ...)` form | `unloaded-handler-errors-before-begin` |
| In `--config-for`, replace `(a3madkour-sections/enum section "status")` with `'("finished" "reading" "queued" "abandoned")` | `config-reads-registry-and-contract` |
| Change `--collect-triples`'s `'living` to `'deliberate` | `collect-follows-registry-modes` |

- [ ] **Step 16: Commit**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish.el emacs-configs/custom/lisp/a3madkour-publish-living.el emacs-configs/custom/lisp/a3madkour-publish-deliberate.el emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el emacs-configs/custom/lisp/a3madkour-publish-works.el emacs-configs/custom/lisp/a3madkour-publish-research.el emacs-configs/custom/lisp/a3madkour-publish-library.el emacs-configs/custom/lisp/a3madkour-publish-author.el emacs-configs/custom/lisp/a3madkour-publish-garden.el emacs-configs/custom/lisp/a3madkour-publish-essays.el emacs-configs/custom/lisp/a3madkour-publish-living-test.el emacs-configs/custom/lisp/a3madkour-publish-deliberate-test.el emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el emacs-configs/custom/lisp/a3madkour-publish-works-test.el emacs-configs/custom/lisp/a3madkour-publish-unpublish-test.el emacs-configs/custom/lisp/a3madkour-publish-research-test.el emacs-configs/custom/lisp/a3madkour-publish-library-test.el emacs-configs/custom/lisp/a3madkour-publish-author-test.el && git commit -F - <<'EOF'
refactor(publish): dispatch and section lists derive from the registry

a3madkour-pub/sections, a3madkour-pub-deliberate-sections, the living
and deliberate handler lookups, frontmatter --known-sections, works'
served sections, research's slash->hyphen converter and library's
yaml-file/default-medium all come from a3madkour-pub-registry; library's
allowed media types and statuses come from data/sections.json.  The old
lists and the 5 with-eval-after-load registrations are deleted.

Intended behaviour change: a registered handler that is not loaded is
now a loud per-file error (living: the file reports err and the run logs
handler-missing naming the function; deliberate: signals before
begin-publish).  It used to be skipped silently, which made the
section's pages look removed to the orphan sweep (S1 row 9).

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

### Task 5: Essays, research and poetry normalizers read the contract

**Files:**
- Modify: `a3madkour-publish-frontmatter.el:235-243` (deleted), `:269-270`, `:460-469` (deleted), `:505-553`; `a3madkour-publish-poetry.el:165-176`.
- Tests: `a3madkour-publish-frontmatter-test.el`, `a3madkour-publish-poetry-test.el`, `a3madkour-publish-essays-test.el`, `a3madkour-publish-research-test.el`. Each gets the fixture `require` and the new tests.

**Interfaces:**
- Consumes: `a3madkour-sections/emitted-keys`, `a3madkour-sections/enum`.
- Produces: unchanged normalizer signatures. Deletes `a3madkour-pub-frontmatter--essay-required-keys`, `--essay-optional-keys`, `--research-statuses`, `--theme-forbidden`, `a3madkour-pub-poetry--required-keys`, `--optional-keys`. `a3madkour-pub-poetry--allowed-keys` stays as a zero-arg function.

- [ ] **Step 1: One-time equivalence against the real file (BEFORE editing)**

The old constants still exist at this point. This run compares them with the real contract:

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./a3-pub.sh --eval '(progn
  (setq a3madkour-pub/site-data-dir (expand-file-name "~/Sync/Workspace/a3madkour.github.io/data/"))
  (require (quote a3madkour-sections))
  (cl-flet ((cmp (label old new)
              (let ((o (sort (mapcar (lambda (x) (format "%s" x)) old) (function string<)))
                    (n (sort (copy-sequence new) (function string<))))
                (princ (format "%s equal=%S only-old=%S only-new=%S\n" label (equal o n)
                               (cl-set-difference o n :test (function equal))
                               (cl-set-difference n o :test (function equal)))))))
    (cmp "essays" (append a3madkour-pub-frontmatter--essay-required-keys a3madkour-pub-frontmatter--essay-optional-keys)
         (a3madkour-sections/emitted-keys "essays"))
    (cmp "poetry" (a3madkour-pub-poetry--allowed-keys) (a3madkour-sections/emitted-keys "works/poetry"))
    (cmp "theme-statuses" a3madkour-pub-frontmatter--research-statuses (a3madkour-sections/enum "research/themes" "status"))
    (cmp "question-statuses" a3madkour-pub-frontmatter--research-statuses (a3madkour-sections/enum "research/questions" "status"))
    (princ (format "themes-forbidden-absent=%S\n"
                   (cl-notany (lambda (k) (member (symbol-name k) (a3madkour-sections/emitted-keys "research/themes")))
                              a3madkour-pub-frontmatter--theme-forbidden)))))' 2>&1 | grep -E "equal=|forbidden-absent="
```

Expected: `equal=t` on all four lines, and `themes-forbidden-absent=t`.
- An `only-old` key is a field the new filter would silently drop. **Stop**, and add it to the site's `data/sections.json` (site-repo commit) before continuing.
- An `only-new` key (for example `multi_export`/`downloads` on essays) is accepted: ox-hugo does not emit it, so no page changes. Record it in the commit message as an intended difference.
- Themes now keep only their contract set, where before they dropped only `theme`/`parent_question`. Record that in the commit message.

- [ ] **Step 2: Write the failing tests**

Add `(require 'a3madkour-sections-fixture)` after the top `require`s of `a3madkour-publish-frontmatter-test.el`, `a3madkour-publish-poetry-test.el`, `a3madkour-publish-essays-test.el` and `a3madkour-publish-research-test.el`.

Append to `a3madkour-publish-frontmatter-test.el` (before any trailing `provide`):

```elisp
;;; Section registry Task 5: the filters read data/sections.json

(ert-deftest a3madkour-pub-frontmatter--essays-filter-follows-the-contract ()
  "Rename `hero' in the contract: the old name is dropped, the new kept."
  (a3madkour-sections-test--with-root
      (a3madkour-sections-test/mutate "\"hero\"" "\"hero_image\"")
    (let* ((tmp (make-temp-file "essays-norm-" nil ".org"))
           (out (unwind-protect
                    (progn
                      (with-temp-file tmp
                        (insert ":PROPERTIES:\n:ID: e1\n:END:\n#+title: x\n"))
                      (a3madkour-pub-frontmatter/normalize
                       'essays '((title . "x") (date . "2026-04-12")
                                 (hero . "h.png") (hero_image . "i.png"))
                       tmp))
                  (delete-file tmp))))
      (should-not (assq 'hero out))
      (should (equal (alist-get 'hero_image out) "i.png")))))

(ert-deftest a3madkour-pub-frontmatter--theme-keeps-only-its-contract-fields ()
  "Themes drop every key outside the contract — `theme' only because the
contract lacks it: rename `garden_topic_ref' to `theme' and it survives."
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-05-30"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-05-30")))
    (let ((raw '((title . "T") (description . "x") (status . "active")
                 (slug . "t") (theme . "other") (garden_topic_ref . "g"))))
      (let ((out (a3madkour-pub-frontmatter/normalize 'research-themes raw "/tmp/x.org")))
        (should-not (assq 'slug out))
        (should-not (assq 'theme out))
        (should (equal (alist-get 'garden_topic_ref out) "g")))
      (a3madkour-sections-test--with-root
          (a3madkour-sections-test/mutate "\"garden_topic_ref\"" "\"theme\"")
        (let ((out (a3madkour-pub-frontmatter/normalize 'research-themes raw "/tmp/x.org")))
          (should (equal (alist-get 'theme out) "other"))
          (should-not (assq 'garden_topic_ref out)))))))

(ert-deftest a3madkour-pub-frontmatter--research-status-enum-follows-the-contract ()
  (cl-letf (((symbol-function 'a3madkour-pub-history/git-mtime-of-file)
             (lambda (_) "2026-05-30"))
            ((symbol-function 'a3madkour-pub-history/filesystem-mtime-of-file)
             (lambda (_) "2026-05-30")))
    (a3madkour-sections-test--with-root
        (a3madkour-sections-test/mutate "\"dormant\"" "\"paused\"")
      (dolist (section '(research-themes research-questions))
        (let ((warnings '()))
          (cl-letf (((symbol-function 'message)
                     (lambda (fmt &rest args) (push (apply #'format fmt args) warnings))))
            (a3madkour-pub-frontmatter/normalize
             section '((title . "T") (description . "x") (status . "paused")) "/tmp/x.org")
            (should-not (cl-some (lambda (w) (string-match-p "status=" w)) warnings))
            (a3madkour-pub-frontmatter/normalize
             section '((title . "T") (description . "x") (status . "dormant")) "/tmp/x.org")
            (should (cl-some (lambda (w) (string-match-p "status=\"dormant\"" w))
                             warnings))))))))
```

Append to `a3madkour-publish-poetry-test.el`:

```elisp
(ert-deftest a3madkour-pub-poetry-test/allowed-keys-follow-the-contract ()
  (a3madkour-sections-test--with-root
      (a3madkour-sections-test/mutate "\"collection\"" "\"cycle\"")
    (let ((out (a3madkour-pub-frontmatter/normalize
                'works-poetry
                '((title . "P") (date . "2026-06-12") (lastmod . "2026-06-12")
                  (collection . "old") (cycle . "new"))
                nil)))
      (should-not (assq 'collection out))
      (should (equal (alist-get 'cycle out) "new")))))
```

- [ ] **Step 3: Run, and expect FAIL**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "follows-the-contract|keeps-only-its-contract|^Ran|unexpected"
```

Expected: all four FAIL. The hardcoded lists keep `hero` and drop `hero_image`. The theme filter drops only `theme`/`parent_question`, so `slug` survives. The status warnings follow the defconst. The poetry list keeps `collection`.

- [ ] **Step 4: Implement**

`a3madkour-publish-frontmatter.el`: after `(require 'a3madkour-publish-registry)` add `(require 'a3madkour-sections)`. Delete lines 235–243 (the two essay defconsts). Replace lines 269–270:

```elisp
  (let* ((allowed (append a3madkour-pub-frontmatter--essay-required-keys
                          a3madkour-pub-frontmatter--essay-optional-keys))
```

with

```elisp
  (let* ((allowed (mapcar #'intern (a3madkour-sections/emitted-keys "essays")))
```

and change the docstring's step 1 line to `  1. Drop ox-hugo noise keys (anything outside the essays contract in data/sections.json).`

Delete lines 460–469 (`--research-statuses` and `--theme-forbidden`). Replace `--normalize-research-question`'s status block

```elisp
    (let ((status (alist-get 'status out)))
      (unless (member status a3madkour-pub-frontmatter--research-statuses)
        (a3madkour-pub/warn "frontmatter" file "status=%S not in %S" status
                 a3madkour-pub-frontmatter--research-statuses)))
```

with

```elisp
    (let ((status (alist-get 'status out))
          (statuses (a3madkour-sections/enum "research/questions" "status")))
      (unless (member status statuses)
        (a3madkour-pub/warn "frontmatter" file "status=%S not in %S"
                            status statuses)))
```

Replace the whole `a3madkour-pub-frontmatter--normalize-research-theme` with:

```elisp
(defun a3madkour-pub-frontmatter--normalize-research-theme (raw file)
  "Normalize a research-theme RAW alist.  Returns the cleaned alist.
Keys outside the themes contract (data/sections.json) are dropped
silently — `theme' and `parent_question' among them — and the site
linter stays the hard gate."
  (let ((out (a3madkour-pub-frontmatter/research-normalize-common raw file))
        (statuses (a3madkour-sections/enum "research/themes" "status"))
        (legal (mapcar #'intern
                       (a3madkour-sections/emitted-keys "research/themes"))))
    ;; Status enum check (WARN-don't-fail).
    (let ((status (alist-get 'status out)))
      (unless (member status statuses)
        (a3madkour-pub/warn "frontmatter" file "status=%S not in %S"
                            status statuses)))
    ;; Weight coercion to int (octal-safe).  Drop the key when coercion
    ;; returns nil (non-numeric raw) rather than leaving (weight . nil)
    ;; in the alist, which would serialize as weight: null and fail the
    ;; research fixtures linter.
    (when-let ((raw-w (alist-get 'weight out)))
      (let ((coerced (a3madkour-pub-frontmatter--coerce-weight raw-w file)))
        (if coerced
            (setf (alist-get 'weight out) coerced)
          (setq out (assq-delete-all 'weight out)))))
    (cl-remove-if-not (lambda (cell) (memq (car cell) legal)) out)))
```

`a3madkour-publish-poetry.el`: add `(require 'a3madkour-sections)` after `(require 'a3madkour-publish-keywords)` (line 25). Replace lines 165–176 with:

```elisp
(defun a3madkour-pub-poetry--allowed-keys ()
  "All keys allowed in emitted poetry frontmatter, as symbols.
Read from the site's section contract (data/sections.json, works/poetry)."
  (mapcar #'intern (a3madkour-sections/emitted-keys "works/poetry")))
```

- [ ] **Step 5: Run, and expect PASS; then the full suite**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "follows-the-contract|keeps-only-its-contract|theme-forbidden|status-enum-warn|essays-required-keys-present|passes-through-allowed-keys|^Ran|unexpected"
```

Expected: all pass, including the pre-existing `research-theme-forbidden-fields-dropped`, `research-theme-status-enum-warn`, `essays-required-keys-present` and `normalize-passes-through-allowed-keys`. `0 unexpected`.

- [ ] **Step 6: Mutation-test the guards (revert after each)**

| Break | Expected failing test |
|---|---|
| Essays `allowed`: restore the old literal 19-key list | `essays-filter-follows-the-contract` |
| Theme: replace the final `cl-remove-if-not` with `(dolist (k '(theme parent_question)) (setq out (assq-delete-all k out))) out` | `theme-keeps-only-its-contract-fields` |
| Question statuses: replace the `enum` call with `'("active" "dormant" "answered")` | `research-status-enum-follows-the-contract` |
| Poetry: return the old literal 14-key list | `allowed-keys-follow-the-contract` |

- [ ] **Step 7: Commit**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el emacs-configs/custom/lisp/a3madkour-publish-poetry.el emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el emacs-configs/custom/lisp/a3madkour-publish-poetry-test.el emacs-configs/custom/lisp/a3madkour-publish-essays-test.el emacs-configs/custom/lisp/a3madkour-publish-research-test.el && git commit -F - <<'EOF'
refactor(frontmatter): essays/research/poetry read data/sections.json

Deletes the essay key lists, research statuses, THEME_FORBIDDEN copy and
poetry key lists; the normalizers read emitted-keys / enums from
a3madkour-sections.  Themes now keep exactly their contract field set
(previously: drop only theme/parent_question).

Equivalence vs the deleted constants, real data/sections.json:
essays equal=<t|...>, poetry equal=<t|...>, statuses equal=<t|...>;
intended differences: <none | list>.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

(Fill the angle-bracket slots with Step 1's printed results.)

---

### Task 6: Works normalizer and works-lint read the contract; delete works-vocab (both repos)

**Dependency:** the site plan's works migration has landed, so no site *linter* reads `data/works-vocab.json`. `tools/test_publish_integration.py` still does; Step 7 updates it.

**Files:**
- Modify: `a3madkour-publish-frontmatter.el:37-41` (works-vocab require and comment), `:593-616`; `a3madkour-works-lint.el:1-56`, `:132-144`, `:161-173`, `:259-262`.
- Modify (site): `tools/test_publish_integration.py:2089-2094` (Compromise 3 docstring), `:2111-2133` (poetry `setUp` copy), `:2250-2310` (delete `TestWorksVocabularyIsSingleSourced`).
- Tests: `a3madkour-publish-frontmatter-test.el`, `a3madkour-publish-works-test.el`, `a3madkour-works-lint-test.el`.
- Delete: `a3madkour-works-vocab.el`, `a3madkour-works-vocab-test.el`, `a3madkour-works-vocab-fixture.el`, `a3madkour-works-vocab.elc`; site `data/works-vocab.json`.

**Interfaces:**
- Consumes: `a3madkour-sections/emitted-keys`, `/fields`, `/enum`, `/required-authored`; `a3madkour-pub-section/from-symbol`; `a3madkour-pub-registry/sections-for-handler`.
- Produces: `a3madkour-pub-frontmatter--works-allowed-keys (section-symbol) -> (SYMBOL ...)` (same signature). `a3madkour-works-lint/lint-file` is unchanged in signature. Deletes `a3madkour-works-lint/vocab`, the `a3madkour-works-lint--vocab-cache` alias, `a3madkour-works-lint--required`, and the whole `a3madkour-works-vocab` feature.
- Behaviour change, recorded in the commit message: lint rule 2 now checks every enum field the section's contract declares. That adds `tile_size`, which only the site linter checked before.

- [ ] **Step 1: One-time equivalence (BEFORE editing; works-vocab still loads)**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./a3-pub.sh --eval '(progn
  (setq a3madkour-pub/site-data-dir (expand-file-name "~/Sync/Workspace/a3madkour.github.io/data/"))
  (require (quote a3madkour-works-vocab)) (require (quote a3madkour-sections))
  (dolist (p (quote (("works/games" . works-games) ("works/music" . works-music))))
    (princ (format "%s keys equal=%S\n" (car p)
                   (equal (sort (a3madkour-sections/emitted-keys (car p)) (function string<))
                          (sort (mapcar (function symbol-name) (a3madkour-works-vocab/emitted-keys (cdr p))) (function string<))))))
  (dolist (e (quote (("works/games" "status" "game_statuses") ("works/games" "game_kind" "game_kinds")
                     ("works/music" "format" "music_formats") ("works/music" "platform_embed.kind" "platform_kinds"))))
    (princ (format "%s.%s equal=%S\n" (nth 0 e) (nth 1 e)
                   (equal (a3madkour-sections/enum (nth 0 e) (nth 1 e)) (a3madkour-works-vocab/list (nth 2 e))))))
  (princ (format "required games=%S music=%S\n"
                 (a3madkour-sections/required-authored "works/games")
                 (a3madkour-sections/required-authored "works/music"))))' 2>&1 | grep -E "equal=|required "
```

Expected: six `equal=t` lines, and `required games=("status" "game_kind" "tagline" "year") music=("format" "year")`. These match the old `a3madkour-works-lint--required`. Any `equal=nil` means the site file was transcribed wrong: **stop**, fix `data/sections.json` (site commit) and re-run.

- [ ] **Step 2: Write the failing tests**

Append to `a3madkour-works-lint-test.el` (before its `provide`, if any):

```elisp
;;; Section registry Task 6: rules read data/sections.json

(ert-deftest a3madkour-works-lint--enum-rule-follows-the-contract ()
  (a3madkour-works-lint-test--with-vocab
      (a3madkour-sections-test/mutate "\"playable\"" "\"shippable\"")
    (dolist (case '(("playable" . t) ("shippable" . nil)))
      (let ((f (a3madkour-works-lint-test--file
                (format "#+TITLE: G
#+HUGO_SECTION: works/games
#+HUGO_CUSTOM_FRONT_MATTER: :status %s :game_kind jam :year 2026 :tagline T
" (car case)))))
        (unwind-protect
            (let ((flagged (cl-some (lambda (e) (string-match-p ":status=" e))
                                    (a3madkour-works-lint/lint-file f))))
              (should (eq (and flagged t) (cdr case))))
          (delete-file f))))))

(ert-deftest a3madkour-works-lint--checks-every-contract-enum ()
  "Intended behaviour change: `tile_size' is an enum in the contract, so
the lint now checks it (only the site linter did before)."
  (a3madkour-works-lint-test--with-vocab a3madkour-works-lint-test--vocab
    (let ((f (a3madkour-works-lint-test--file "#+TITLE: G
#+HUGO_SECTION: works/games
#+HUGO_CUSTOM_FRONT_MATTER: :status playable :game_kind jam :year 2026 :tagline T
#+HUGO_CUSTOM_FRONT_MATTER: :tile_size huge
")))
      (unwind-protect
          (should (cl-some (lambda (e) (string-match-p ":tile_size=\"huge\" not in" e))
                           (a3madkour-works-lint/lint-file f)))
        (delete-file f)))))

(ert-deftest a3madkour-works-lint--required-rule-follows-the-contract ()
  (dolist (case (list (cons a3madkour-works-lint-test--vocab t)
                      (cons (a3madkour-sections-test/mutate
                             "\"tagline\": {\"type\": \"text\", \"required\": true}"
                             "\"tagline\": {\"type\": \"text\"}")
                            nil)))
    (a3madkour-works-lint-test--with-vocab (car case)
      (let ((f (a3madkour-works-lint-test--file "#+TITLE: G
#+HUGO_SECTION: works/games
#+HUGO_CUSTOM_FRONT_MATTER: :status playable :game_kind jam :year 2026
")))
        (unwind-protect
            (should (eq (and (cl-some (lambda (e) (string-match-p "missing required key :tagline" e))
                                      (a3madkour-works-lint/lint-file f))
                             t)
                        (cdr case)))
          (delete-file f))))))

(ert-deftest a3madkour-works-lint--platform-kind-follows-the-contract ()
  (a3madkour-works-lint-test--with-vocab
      (a3madkour-sections-test/mutate "\"soundcloud\"" "\"mixcloud\"")
    (let ((f (a3madkour-works-lint-test--file "#+TITLE: M
#+HUGO_SECTION: works/music
#+HUGO_CUSTOM_FRONT_MATTER: :format album :year 2026
#+HUGO_CUSTOM_FRONT_MATTER: :platform_kind mixcloud :platform_url https://example.com/x
")))
      (unwind-protect
          (should-not (cl-some (lambda (e) (string-match-p "platform_kind=" e))
                               (a3madkour-works-lint/lint-file f)))
        (delete-file f)))))
```

- [ ] **Step 3: Rewire the works test files to the new fixture**

1. In `a3madkour-publish-frontmatter-test.el`, replace

```elisp
                     (sort (mapcar #'symbol-name
                                   (a3madkour-works-vocab/emitted-keys 'works-games))
                           #'string<))))))
```

with

```elisp
                     (sort (a3madkour-sections/emitted-keys "works/games")
                           #'string<))))))
```

and replace

```elisp
                     (sort (mapcar #'symbol-name
                                   (remq 'platform_embed
                                         (a3madkour-works-vocab/emitted-keys
                                          'works-music)))
                           #'string<))))))
```

with

```elisp
                     (sort (remove "platform_embed"
                                   (a3madkour-sections/emitted-keys "works/music"))
                           #'string<))))))
```

2. In `a3madkour-works-lint-test.el`, replace the `a3madkour-works-lint-test--with-vocab` macro (lines 8–23) with:

```elisp
(defmacro a3madkour-works-lint-test--with-vocab (json &rest body)
  "Run BODY over a temp site root whose data/sections.json holds JSON.
When JSON is nil, no contract file is written."
  (declare (indent 1))
  `(a3madkour-sections-test--with-root ,json ,@body))
```

Then delete these five tests outright; their replacements are the reader tests in `a3madkour-sections-test.el`: `a3madkour-works-lint--vocab-reads-file`, `--vocab-fails-closed-when-missing`, `--vocab-fails-closed-when-malformed`, `--vocab-fails-closed-on-missing-key` and `--vocab-fails-closed-on-unknown-key`.

3. The mechanical renames:

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && sed -i '' \
  -e 's/a3madkour-works-vocab-test--with-root/a3madkour-sections-test--with-root/g' \
  -e 's/a3madkour-works-vocab-test--json/a3madkour-sections-test--json/g' \
  -e 's#a3madkour-works-vocab-test/write#a3madkour-sections-test/write#g' \
  -e 's/a3madkour-works-vocab-fixture/a3madkour-sections-fixture/g' \
  -e 's#data/works-vocab\.json#data/sections.json#g' \
  -e 's/a3madkour-works-vocab/a3madkour-sections/g' \
  a3madkour-publish-frontmatter-test.el a3madkour-publish-works-test.el a3madkour-works-lint-test.el
```

(The `sections-test/write` calls in `-works-test.el` stay. Under the session default the reader does not consult that site root, so the writes are inert, and they keep the temp roots shaped like production.)

- [ ] **Step 4: Run, and expect FAIL**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-works-lint--|works-.*-keeps-exactly|works-filter-follows|works-fails-closed|^Ran|unexpected"
```

Expected: the four new lint tests FAIL, because the lint still reads works-vocab, whose file is absent from the `with-root` temp roots. Most ported lint and frontmatter works tests also FAIL with `vocabulary not found`. That is the evidence that they now supply `sections.json` and not `works-vocab.json`.

- [ ] **Step 5: Implement: the frontmatter works filter**

In `a3madkour-publish-frontmatter.el`, delete lines 37–41 (the works-vocab comment and `(require 'a3madkour-works-vocab)`). Replace the whole `a3madkour-pub-frontmatter--works-allowed-keys`, from its `(defun` line to the end of that defun, with:

```elisp
(defun a3madkour-pub-frontmatter--works-allowed-keys (section)
  "Every key legal in emitted frontmatter for works SECTION, as symbols.

SECTION is the hyphen-form symbol (`works-games' / `works-music').  Read
from the site's section contract (data/sections.json), which is the one
home of this contract: `tools/check_works_fixtures.py' checks pages
against the same file.  Fails closed: a missing or malformed contract
signals, so a works publish aborts rather than emitting unfiltered
frontmatter (ox-hugo's own `author'/`slug' would reach the page).

`platform_kind' / `platform_url' are deliberately NOT in the contract:
they are inputs the music normalizer folds into `platform_embed', and
filtering them out is what keeps them off the page.  `tracks' IS in it
although the handler injects it after `normalize' — the set is the
contract, not a record of who writes each key."
  (mapcar #'intern
          (a3madkour-sections/emitted-keys
           (a3madkour-pub-section/from-symbol section))))
```

- [ ] **Step 6: Implement: works-lint**

Replace `a3madkour-works-lint.el` lines 1–56 (the header through the `--required` defconst) with:

```elisp
;;; a3madkour-works-lint.el --- works pre-publish linter  -*- lexical-binding: t; -*-

;;; Commentary:

;; Pre-publish lint for works/games and works/music org sources.  Reports
;; org `FILE:LINE: message' strings, mirroring a3madkour-recipe-lint.el.
;;
;; Required keys and enum values are NOT defined here.  They are read from
;; the site repo's data/sections.json (via `a3madkour-sections'), which
;; tools/check_works_fixtures.py also checks against, so the two languages
;; cannot drift.  A missing or malformed contract is an error, never a
;; skipped check.

;;; Code:

(require 'cl-lib)
(require 'org-element)
(require 'a3madkour-sections)
(require 'a3madkour-publish-registry)
;; `a3madkour-pub--extract-id' lives here.  The note ID must be read from the
;; file-level `:PROPERTIES: :ID: ... :END:' drawer, which is the documented
;; authoring convention (design spec §3.1) and what the handler itself uses
;; via `a3madkour-pub/note-metadata'.  Reading a `#+ID:' KEYWORD instead made
;; the asset directory resolve to `<dir>/assets/' for every real file, so
;; every declared hero/screenshots/cover false-failed rule 4.
(require 'a3madkour-publish)
;; `a3madkour-pub/poetry-dir' is defined in `a3madkour-publish-poetry', not
;; `a3madkour-publish'.  Requiring the poetry module directly is safe: it
;; does not depend on this module or on `a3madkour-publish-works'.
(require 'a3madkour-publish-poetry)

(defvar a3madkour-works-lint-enabled t
  "When non-nil, the works handler runs this linter before publishing.")
```

In `a3madkour-works-lint/lint-file`, replace

```elisp
      (when (member section '("works/games" "works/music"))
        (let* ((games-p (string-equal section "works/games"))
               (sym     (if games-p 'works-games 'works-music))
               (cells   (a3madkour-works-lint--cfm-cells ast))
```

with

```elisp
      (when (member section (a3madkour-pub-registry/sections-for-handler
                             'a3madkour-pub-works/publish-works-file))
        (let* ((games-p (string-equal section "works/games"))
               (cells   (a3madkour-works-lint--cfm-cells ast))
```

Replace rules 1 and 2:

```elisp
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
```

with

```elisp
            ;; 1 — required keys: the contract's required fields that the
            ;; author writes (title/date/lastmod/draft are `from: pipeline').
            (dolist (k (mapcar #'intern
                               (a3madkour-sections/required-authored section)))
              (unless (alist-get k cells)
                (push (format "%s:1: missing required key :%s" base k) errs)))
            ;; 2 — enum membership: every enum field the contract declares.
            (dolist (cell (a3madkour-sections/fields section))
              (when (equal (alist-get 'type (cdr cell)) "enum")
                (let* ((k (intern (car cell)))
                       (v (val k)))
                  (when v
                    (let ((allowed (alist-get 'values (cdr cell))))
                      (unless (member v allowed)
                        (add k ":%s=%S not in %S" k v allowed)))))))
```

In rule 6, replace `(a3madkour-works-lint/vocab "platform_kinds")` with `(a3madkour-sections/enum section "platform_embed.kind")`.

- [ ] **Step 7: Move `tools/test_publish_integration.py` off works-vocab, then delete it in both repos**

The elisp normalizer now reads `data/sections.json` from the publish's site root, so the poetry integration test's tmp root must carry that file instead.

(a) In `TestPoetryPublishDeliberate`'s docstring, replace the Compromise 3 paragraph with:

```python
    Compromise 3 — the tmp site root must carry `data/sections.json`, even
    though nothing here publishes a game or a release.  The elisp poetry
    normalizer filters emitted frontmatter to the `works/poetry` contract it
    reads from the publish's site root, and fails closed without it.
    (`check_works_fixtures` reads the registry from the code tree, not from
    `repo_root`, so the linter half does not need the copy.)
```

(b) In its `setUp`, delete the whole `# Compromise 3 — ...` comment and the `shutil.copyfile(... "works-vocab.json" ...)` call. The contract copy is already made by `_seed_sections` (Task 4 Step 13b), called before the poetry class sets `A3_PUB_SITE_DATA_DIR`.

(c) Delete the class `TestWorksVocabularyIsSingleSourced` (decorator through the end of `test_fixture_matches_the_live_vocabulary`). Its subject, `a3madkour-works-vocab-fixture.el`, is deleted below. The new fixture `a3madkour-sections-fixture.json` is test input, and its section names are pinned to the real file by `a3madkour-sections--real-contract-sections-match-fixture` (Task 2), so no Python twin is needed.

Then check that nothing else references the file:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && grep -rln "works-vocab" tools layouts tests assets data 2>/dev/null | grep -v "^data/works-vocab.json$"
```

Expected: no output. A hit in `tools/check_works_fixtures.py` or its test means the site plan's works migration has not landed: **stop**.

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/test_publish_integration.py 2>&1 | tail -3
```

Expected: `OK` (or `OK (skipped=N)` when the integration prerequisites are absent; in that case it proves nothing, so run it on the machine with Emacs and the dotfiles checkout).

```bash
cd /Users/a3madkour/dotfiles && git rm emacs-configs/custom/lisp/a3madkour-works-vocab.el emacs-configs/custom/lisp/a3madkour-works-vocab-test.el emacs-configs/custom/lisp/a3madkour-works-vocab-fixture.el && rm -f emacs-configs/custom/lisp/a3madkour-works-vocab.elc
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && grep -ln "works-vocab" *.el a3-pub.sh ../config.org
```

Expected: no output from the final grep.

- [ ] **Step 8: Run, and expect PASS; then the full suite**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-works-lint--|works-.*-keeps-exactly|works-filter-follows|works-fails-closed|platform-embed-round-trips|^Ran|unexpected"
```

Expected: all pass, and `0 unexpected`.

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && python3 tools/check_works_fixtures.py && python3 tools/test_check_works_fixtures.py
```

Expected: both exit 0.

- [ ] **Step 9: Mutation-test the guards (revert after each)**

| Break | Expected failing test |
|---|---|
| Rule 2: replace `(a3madkour-sections/fields section)` with `nil` | `--enum-rule-follows-the-contract`, `--checks-every-contract-enum`, `--rejects-unknown-status` |
| Rule 1: replace the `required-authored` call with `'("status" "game_kind" "tagline" "year")` | `--required-rule-follows-the-contract` |
| Rule 6: replace the `enum` call with `'("bandcamp" "soundcloud" "youtube")` | `--platform-kind-follows-the-contract` |
| `--works-allowed-keys`: return `'(title year)` | `works-games-keeps-exactly-the-vocabulary-keys` |

- [ ] **Step 10: Commit (dotfiles, then site)**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-frontmatter.el emacs-configs/custom/lisp/a3madkour-works-lint.el emacs-configs/custom/lisp/a3madkour-publish-frontmatter-test.el emacs-configs/custom/lisp/a3madkour-publish-works-test.el emacs-configs/custom/lisp/a3madkour-works-lint-test.el && git commit -F - <<'EOF'
refactor(works): normalizer + works-lint read data/sections.json

The works emitted-key filter and works-lint's required-key, enum and
platform_kind rules read a3madkour-sections; a3madkour-works-vocab
(+ test + fixture) is deleted and its tests are ported to
a3madkour-sections-test.  Equivalence vs works-vocab.json on the real
contract: games/music keys equal, all four enums equal, required
sets equal.

Intended behaviour change: lint rule 2 now checks every enum field the
section's contract declares, which adds tile_size.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && git rm data/works-vocab.json && git add tools/test_publish_integration.py && git commit -F - <<'EOF'
chore(data): delete works-vocab.json, folded into sections.json

The poetry integration test now copies data/sections.json into its tmp
site root; TestWorksVocabularyIsSingleSourced goes with the elisp fixture
it pinned.

Neither repo reads it any more: tools/check_works_fixtures.py moved to
data/sections.json in the site plan, and the elisp reader
a3madkour-works-vocab was replaced by a3madkour-sections (dotfiles).

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

### Task 7: Mark helpers: custom-front-matter keys, presence, upsert and remove

`a3madkour-pub-author--upsert-keyword` upserts by keyword. A file has many `#+HUGO_CUSTOM_FRONT_MATTER:` lines, and one line may hold several keys, so these helpers work by (keyword, `:key`). They split values exactly as ox-hugo does, with `org-babel-balanced-split` and `org-babel-parse-header-arguments`.

**Files:**
- Modify: `a3madkour-publish-author.el`. Add `(require 'ob-core)`, `(require 'a3madkour-sections)` and `(require 'a3madkour-publish-yaml)` after `(require 'a3madkour-publish-id)`, and insert the helpers after `a3madkour-pub-author--upsert-keyword` (line 102).
- Test: `a3madkour-publish-author-test.el`. Add `(require 'ob-core)` at the top.

**Interfaces (Produces, exact):**
- `a3madkour-pub-author--keyword-fields`: defconst `(("title" . "TITLE") ("description" . "HUGO_DESCRIPTION") ("summary" . "HUGO_SUMMARY"))`.
- `(a3madkour-pub-author--cfm-segments VALUE) -> ((KEY . SEGMENT) ...)`.
- `(a3madkour-pub-author--cfm-lines) -> ((BEG END VALUE) ...)`.
- `(a3madkour-pub-author--cfm-keys) -> (STRING ...)`.
- `(a3madkour-pub-author--cfm-get KEY) -> STRING|nil`.
- `(a3madkour-pub-author--field-present-p NAME) -> BOOL`.
- `(a3madkour-pub-author--cfm-value TYPE VALUE) -> STRING`.
- `(a3madkour-pub-author--upsert-cfm-key KEY RENDERED)`.
- `(a3madkour-pub-author--remove-cfm-key KEY)`.
- `(a3madkour-pub-author--remove-field NAME)`.
- `(a3madkour-pub-author--write-field NAME TYPE VALUE)`.

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-author-test.el` (before its `provide`, if any):

```elisp
;; -- Section registry Task 7: custom front matter helpers --

(ert-deftest a3madkour-pub-author-test/cfm-segments-split-like-ox-hugo ()
  (should (equal (a3madkour-pub-author--cfm-segments ":status active :weight 10")
                 '(("status" . ":status active") ("weight" . ":weight 10"))))
  (should (equal (a3madkour-pub-author--cfm-segments ":tagline \"a :b c\" :year 2026")
                 '(("tagline" . ":tagline \"a :b c\"") ("year" . ":year 2026"))))
  (should (null (a3madkour-pub-author--cfm-segments "   "))))

(ert-deftest a3madkour-pub-author-test/cfm-keys-span-every-line ()
  (with-temp-buffer
    (org-mode)
    (insert "#+title: T\n"
            "#+HUGO_CUSTOM_FRONT_MATTER: :status active :weight 10\n"
            "#+hugo_custom_front_matter: :theme t-1\n")
    (should (equal (a3madkour-pub-author--cfm-keys) '("status" "weight" "theme")))
    (should (a3madkour-pub-author--field-present-p "weight"))
    (should-not (a3madkour-pub-author--field-present-p "description"))
    (should (equal (a3madkour-pub-author--cfm-get "theme") "t-1"))
    (should (equal (a3madkour-pub-author--cfm-get "weight") "10"))
    (should-not (a3madkour-pub-author--cfm-get "media_type"))))

(ert-deftest a3madkour-pub-author-test/field-present-reads-dedicated-keywords ()
  (with-temp-buffer
    (org-mode)
    (insert "#+title: T\n#+HUGO_DESCRIPTION: D\n#+HUGO_SUMMARY:\n")
    (should (a3madkour-pub-author--field-present-p "title"))
    (should (a3madkour-pub-author--field-present-p "description"))
    ;; Present with no value counts as absent: mark fills it.
    (should-not (a3madkour-pub-author--field-present-p "summary"))))

(ert-deftest a3madkour-pub-author-test/upsert-cfm-key-replaces-one-segment ()
  (with-temp-buffer
    (org-mode)
    (insert "#+HUGO_SECTION: research/themes\n"
            "#+HUGO_CUSTOM_FRONT_MATTER: :status active :weight 10\n")
    (a3madkour-pub-author--upsert-cfm-key "weight" "20")
    (should (equal (buffer-string)
                   (concat "#+HUGO_SECTION: research/themes\n"
                           "#+HUGO_CUSTOM_FRONT_MATTER: :status active :weight 20\n")))))

(ert-deftest a3madkour-pub-author-test/upsert-cfm-key-appends-after-last-cfm-line ()
  (with-temp-buffer
    (org-mode)
    (insert ":PROPERTIES:\n:ID: x-1\n:END:\n"
            "#+HUGO_SECTION: research/themes\n"
            "#+HUGO_CUSTOM_FRONT_MATTER: :status active\n"
            "#+title: T\n\nBody\n")
    (a3madkour-pub-author--upsert-cfm-key "weight" "10")
    (should (equal (buffer-string)
                   (concat ":PROPERTIES:\n:ID: x-1\n:END:\n"
                           "#+HUGO_SECTION: research/themes\n"
                           "#+HUGO_CUSTOM_FRONT_MATTER: :status active\n"
                           "#+HUGO_CUSTOM_FRONT_MATTER: :weight 10\n"
                           "#+title: T\n\nBody\n")))))

(ert-deftest a3madkour-pub-author-test/upsert-cfm-key-first-line-goes-after-section ()
  (with-temp-buffer
    (org-mode)
    (insert ":PROPERTIES:\n:ID: x-1\n:END:\n#+HUGO_SECTION: garden\n#+title: T\n")
    (a3madkour-pub-author--upsert-cfm-key "year" "2026")
    (should (equal (buffer-string)
                   (concat ":PROPERTIES:\n:ID: x-1\n:END:\n#+HUGO_SECTION: garden\n"
                           "#+HUGO_CUSTOM_FRONT_MATTER: :year 2026\n#+title: T\n")))))

(ert-deftest a3madkour-pub-author-test/upsert-cfm-key-keeps-drawer-first ()
  (with-temp-buffer
    (org-mode)
    (insert ":PROPERTIES:\n:ID:       abc-123\n:END:\n#+title: T\n")
    (a3madkour-pub-author--upsert-cfm-key "year" "2026")
    (should (string-prefix-p ":PROPERTIES:\n:ID:       abc-123\n:END:\n#+HUGO_CUSTOM_FRONT_MATTER: :year 2026\n"
                             (buffer-string)))
    (should (equal (org-entry-get (point-min) "ID") "abc-123"))))

(ert-deftest a3madkour-pub-author-test/remove-cfm-key-keeps-neighbours ()
  (with-temp-buffer
    (org-mode)
    (insert "#+HUGO_CUSTOM_FRONT_MATTER: :status active :topic_map a b\n"
            "#+HUGO_CUSTOM_FRONT_MATTER: :topic_map c\n"
            "#+title: T\n")
    (a3madkour-pub-author--remove-cfm-key "topic_map")
    (should (equal (buffer-string)
                   "#+HUGO_CUSTOM_FRONT_MATTER: :status active\n#+title: T\n"))))

(ert-deftest a3madkour-pub-author-test/remove-field-handles-keyword-fields ()
  (with-temp-buffer
    (org-mode)
    (insert "#+title: T\n#+HUGO_SUMMARY: S\n#+HUGO_CUSTOM_FRONT_MATTER: :weight 10\n")
    (a3madkour-pub-author--remove-field "summary")
    (a3madkour-pub-author--remove-field "weight")
    (should (equal (buffer-string) "#+title: T\n"))))

(ert-deftest a3madkour-pub-author-test/cfm-value-round-trips-through-ox-hugo-parser ()
  "Text is quoted so ox-hugo's parser returns it verbatim: spaces, a
` :' that would otherwise start a new key, a colon, and digits that
`org-babel-read' would turn into a number."
  (dolist (v '("plain" "two words" "A: colon" "x :y z" "2026"))
    (let ((parsed (org-babel-parse-header-arguments
                   (format ":k %s" (a3madkour-pub-author--cfm-value "text" v)))))
      (should (equal (cdr (assq :k parsed)) v))))
  (should (equal (a3madkour-pub-author--cfm-value "int" 40) "40"))
  (should (equal (a3madkour-pub-author--cfm-value "bool" t) "true"))
  (should (equal (a3madkour-pub-author--cfm-value "bool" nil) "false"))
  (should (equal (a3madkour-pub-author--cfm-value "enum" "active") "active"))
  (should (equal (a3madkour-pub-author--cfm-value "date" "2026-10-20") "2026-10-20"))
  (should (equal (a3madkour-pub-author--cfm-value "list" '("a" "b")) "a b"))
  ;; Branch A (Task 1).  Under Branch B this line is instead:
  ;;   (should (equal (a3madkour-pub-author--cfm-value "refs" '("a" "b")) "'(a b)"))
  (should (equal (a3madkour-pub-author--cfm-value "refs" '("a" "b")) "a b")))

(ert-deftest a3madkour-pub-author-test/write-field-routes-keyword-vs-cfm ()
  (with-temp-buffer
    (org-mode)
    (insert "#+HUGO_SECTION: research/themes\n#+title: T\n")
    (a3madkour-pub-author--write-field "description" "text" "A \"quoted\" line.")
    (a3madkour-pub-author--write-field "status" "enum" "active")
    (should (string-match-p "^#\\+HUGO_DESCRIPTION: A \"quoted\" line\\.$" (buffer-string)))
    (should (string-match-p "^#\\+HUGO_CUSTOM_FRONT_MATTER: :status active$" (buffer-string)))))
```

- [ ] **Step 2: Run, and expect FAIL**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "cfm-|field-present|remove-field|write-field|^Ran|unexpected"
```

Expected: every new test FAILS with `void-function a3madkour-pub-author--...`.

- [ ] **Step 3: Implement**

In `a3madkour-publish-author.el`, add after `(require 'a3madkour-publish-id)`:

```elisp
(require 'ob-core)          ; the header-argument parser ox-hugo uses
(require 'a3madkour-publish-yaml)
(require 'a3madkour-sections)
```

Insert after `a3madkour-pub-author--upsert-keyword`:

```elisp
;; -- internal: #+HUGO_CUSTOM_FRONT_MATTER: by (keyword, :key) --
;;
;; A note carries many `#+HUGO_CUSTOM_FRONT_MATTER:' lines and one line may
;; carry several keys, so `--upsert-keyword' (one value per keyword) cannot
;; address them.  Values are split exactly where ox-hugo splits them: its
;; `org-hugo--parse-property-arguments' is `org-babel-parse-header-arguments',
;; which cuts on a colon preceded by whitespace, outside quotes and parens.

(defconst a3madkour-pub-author--keyword-fields
  '(("title" . "TITLE")
    ("description" . "HUGO_DESCRIPTION")
    ("summary" . "HUGO_SUMMARY"))
  "Fields written as their own `#+KEYWORD:' line, not a custom key.
Identical across sections (spec §6 step 4).")

(defconst a3madkour-pub-author--cfm-re
  "^#\\+HUGO_CUSTOM_FRONT_MATTER:[ \t]*\\(.*\\)$"
  "A custom front matter line; group 1 is its value.")

(defun a3madkour-pub-author--cfm-segments (value)
  "Split custom front matter VALUE into ((KEY . SEGMENT) ...).
KEY is the key without its colon; SEGMENT the trimmed `:key value' text."
  (when (and value (string-match-p "[^ \t]" value))
    (let* ((raw (org-babel-balanced-split value '((32 9) . 58)))
           (segs (cons (car raw)
                       (mapcar (lambda (r) (concat ":" r)) (cdr raw)))))
      (delq nil
            (mapcar (lambda (s)
                      (let ((s (string-trim s)))
                        (when (string-match "\\`:\\([^ \t]+\\)" s)
                          (cons (match-string 1 s) s))))
                    segs)))))

(defun a3madkour-pub-author--cfm-lines ()
  "Every custom front matter line as (BEG END VALUE), in buffer order."
  (save-excursion
    (goto-char (point-min))
    (let ((case-fold-search t) out)
      (while (re-search-forward a3madkour-pub-author--cfm-re nil t)
        (push (list (match-beginning 0) (match-end 0)
                    (match-string-no-properties 1))
              out))
      (nreverse out))))

(defun a3madkour-pub-author--cfm-keys ()
  "Every key named on any custom front matter line, in buffer order."
  (cl-loop for (_beg _end value) in (a3madkour-pub-author--cfm-lines)
           append (mapcar #'car (a3madkour-pub-author--cfm-segments value))))

(defun a3madkour-pub-author--cfm-get (key)
  "Value of custom front matter KEY as a string, or nil.
Parsed as ox-hugo parses it; the last line naming KEY wins."
  (let ((sym (intern (concat ":" key))) val)
    (dolist (l (a3madkour-pub-author--cfm-lines) val)
      (let ((cell (assq sym (org-babel-parse-header-arguments (nth 2 l) t))))
        (when cell
          (setq val (format "%s" (cdr cell))))))))

(defun a3madkour-pub-author--field-present-p (name)
  "Non-nil when field NAME already has a value in the buffer.
Reads the dedicated keyword for title/description/summary (a keyword with
an empty value counts as absent), else the custom front matter keys."
  (let ((kw (cdr (assoc name a3madkour-pub-author--keyword-fields))))
    (if kw
        (let ((v (a3madkour-pub-keywords/extract kw)))
          (and v (not (string-empty-p v))))
      (and (member name (a3madkour-pub-author--cfm-keys)) t))))

(defun a3madkour-pub-author--cfm-value (type value)
  "Render VALUE of field TYPE for a `:key VALUE' custom front matter segment.
Text is always double-quoted (the caller has rejected embedded quotes), so
spaces, ` :' and digit-only strings survive ox-hugo's parser verbatim."
  (pcase type
    ("text" (format "\"%s\"" value))
    ("int" (number-to-string value))
    ("bool" (if value "true" "false"))
    ("list" (mapconcat #'identity value " "))
    ;; Branch A (Task 1: the space list reaches the page as a YAML list).
    ;; Branch B replaces this line with:
    ;;   ("refs" (format "'(%s)" (mapconcat #'identity value " ")))
    ("refs" (mapconcat #'identity value " "))
    (_ value)))

(defun a3madkour-pub-author--cfm-insert-point ()
  "Where a new custom front matter line goes: after the last such line,
else after `#+HUGO_SECTION:', else after a leading file property drawer,
else at `point-min'."
  (save-excursion
    (let ((lines (a3madkour-pub-author--cfm-lines))
          (case-fold-search t))
      (cond
       (lines
        (goto-char (nth 1 (car (last lines))))
        (forward-line 1))
       ((progn (goto-char (point-min))
               (re-search-forward "^#\\+HUGO_SECTION:.*$" nil t))
        (forward-line 1))
       (t
        (goto-char (point-min))
        (when (and (looking-at "^[ \t]*:PROPERTIES:[ \t]*$")
                   (re-search-forward "^[ \t]*:END:[ \t]*$" nil t))
          (forward-line 1))))
      (point))))

(defun a3madkour-pub-author--upsert-cfm-key (key rendered)
  "Set custom front matter KEY to RENDERED (already a segment value).
A line naming KEY has that one segment replaced, its other keys kept;
otherwise a new `#+HUGO_CUSTOM_FRONT_MATTER: :KEY RENDERED' line is
inserted (see `--cfm-insert-point').  Hoists a displaced file property
drawer first, as `--upsert-keyword' does."
  (a3madkour-pub-author--hoist-file-property-drawer)
  (let ((seg (format ":%s %s" key rendered))
        (hit (cl-find-if (lambda (l)
                           (assoc key (a3madkour-pub-author--cfm-segments (nth 2 l))))
                         (a3madkour-pub-author--cfm-lines))))
    (save-excursion
      (if hit
          (let ((segs (a3madkour-pub-author--cfm-segments (nth 2 hit))))
            (setcdr (assoc key segs) seg)
            (delete-region (nth 0 hit) (nth 1 hit))
            (goto-char (nth 0 hit))
            (insert "#+HUGO_CUSTOM_FRONT_MATTER: " (mapconcat #'cdr segs " ")))
        (goto-char (a3madkour-pub-author--cfm-insert-point))
        (unless (bolp) (insert "\n"))
        (insert "#+HUGO_CUSTOM_FRONT_MATTER: " seg "\n")))))

(defun a3madkour-pub-author--remove-cfm-key (key)
  "Remove KEY's segment from every custom front matter line.
A line left with no keys is deleted with its newline."
  (save-excursion
    ;; Bottom-up, so earlier lines' positions stay valid.
    (dolist (l (reverse (a3madkour-pub-author--cfm-lines)))
      (let* ((segs (a3madkour-pub-author--cfm-segments (nth 2 l)))
             (kept (cl-remove-if (lambda (s) (equal (car s) key)) segs)))
        (unless (equal kept segs)
          (if kept
              (progn
                (delete-region (nth 0 l) (nth 1 l))
                (goto-char (nth 0 l))
                (insert "#+HUGO_CUSTOM_FRONT_MATTER: "
                        (mapconcat #'cdr kept " ")))
            (delete-region (nth 0 l) (min (point-max) (1+ (nth 1 l))))))))))

(defun a3madkour-pub-author--remove-field (name)
  "Remove field NAME: its keyword line, or its custom front matter key."
  (let ((kw (cdr (assoc name a3madkour-pub-author--keyword-fields))))
    (if (not kw)
        (a3madkour-pub-author--remove-cfm-key name)
      (save-excursion
        (goto-char (point-min))
        (let ((case-fold-search t))
          (while (re-search-forward
                  (format "^#\\+%s:.*\n?" (regexp-quote kw)) nil t)
            (replace-match "" t t)))))))

(defun a3madkour-pub-author--write-field (name type value)
  "Write field NAME (of TYPE) with VALUE into the buffer preamble."
  (let ((kw (cdr (assoc name a3madkour-pub-author--keyword-fields))))
    (if kw
        (a3madkour-pub-author--upsert-keyword kw value)
      (a3madkour-pub-author--upsert-cfm-key
       name (a3madkour-pub-author--cfm-value type value)))))
```

If Task 1 chose Branch B, replace the `("refs" ...)` line in `--cfm-value` with `("refs" (format "'(%s)" (mapconcat #'identity value " ")))`, and swap the test line as its comment shows.

- [ ] **Step 4: Run, and expect PASS; then the full suite**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "cfm-|field-present|remove-field|write-field|mark-|^Ran|unexpected"
```

Expected: all new tests pass, all existing `mark-` tests still pass, and `0 unexpected`.

- [ ] **Step 5: Mutation-test the guards (revert after each)**

| Break | Expected failing test |
|---|---|
| `--remove-cfm-key`: always delete the whole line (replace the `(if kept ...)` with its else-branch) | `remove-cfm-key-keeps-neighbours` |
| `--cfm-value` text: `(format "%s" value)` (no quotes) | `cfm-value-round-trips-through-ox-hugo-parser` (`x :y z` and `2026`) |
| `--upsert-cfm-key`: drop the `(a3madkour-pub-author--hoist-file-property-drawer)` call, and drop the drawer branch in `--cfm-insert-point` | `upsert-cfm-key-keeps-drawer-first` |
| `--field-present-p`: drop the `(not (string-empty-p v))` | `field-present-reads-dedicated-keywords` |

- [ ] **Step 6: Commit**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-author.el emacs-configs/custom/lisp/a3madkour-publish-author-test.el && git commit -F - <<'EOF'
feat(author): custom-front-matter helpers keyed by (keyword, :key)

Detect, read, upsert and remove one key across many
#+HUGO_CUSTOM_FRONT_MATTER: lines (multi-key lines keep their other
keys), splitting exactly where ox-hugo does (org-babel-balanced-split /
org-babel-parse-header-arguments).  Text values are quoted so spaces,
" :" and digit-only strings survive the parser.  Groundwork for the
a3-publish-mark fill-in; mark itself is unchanged.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

### Task 8: Mark helpers: published targets, the next weight, what to ask, and how to ask it

**Files:**
- Modify: `a3madkour-publish-author.el`. Insert after Task 7's helpers.
- Test: `a3madkour-publish-author-test.el`.

**Interfaces (Produces, exact):**
- `(a3madkour-pub-author--site-root) -> DIR`: signals `user-error` when `site-data-dir` is unset.
- `(a3madkour-pub-author--fm-scalar FILE KEY) -> STRING|nil`: top-level scalar KEY in FILE's YAML frontmatter, unquoted.
- `(a3madkour-pub-author--published-targets TO) -> ((SLUG . TITLE) ...)`: sorted by slug.
- `(a3madkour-pub-author--next-weight SECTION) -> INTEGER`.
- `(a3madkour-pub-author--fields-to-fill SECTION) -> ((NAME . SPEC) ...)`.
- `(a3madkour-pub-author--ask SECTION NAME SPEC) -> VALUE|skip`.
- Macro `(a3madkour-pub-author--with-contract &rest BODY)`: turns a contract `error` into a `user-error` (a `user-error` passes through unchanged).
- Test support (in the test file): macro `a3madkour-pub-author-test--with-site`, `(a3madkour-pub-author-test--page SECTION SLUG &rest KV)`, macro `a3madkour-pub-author-test--answering`.

- [ ] **Step 1: Write the test support and the failing tests**

Append to `a3madkour-publish-author-test.el`:

```elisp
;; -- Section registry Tasks 8-9: prompt stubs over a temp site --

(defmacro a3madkour-pub-author-test--with-site (&rest body)
  "Run BODY in an org temp buffer over a temp site root carrying the
sections fixture (resolved through `a3madkour-pub/site-data-dir')."
  (declare (indent 0))
  `(a3madkour-sections-test--with-root a3madkour-sections-test--json
     (with-temp-buffer (org-mode) ,@body)))

(defun a3madkour-pub-author-test--page (section slug &rest kv)
  "Publish a stub content/SECTION/SLUG/index.md with frontmatter KV.
KV alternates key and already-rendered YAML value strings."
  (let ((dir (expand-file-name (format "content/%s/%s" section slug)
                               (a3madkour-pub-yaml/site-root))))
    (make-directory dir t)
    (with-temp-file (expand-file-name "index.md" dir)
      (insert "---\n")
      (while kv (insert (format "%s: %s\n" (pop kv) (pop kv))))
      (insert "---\nBody\n"))))

(defmacro a3madkour-pub-author-test--answering (answers &rest body)
  "Run BODY with every prompt answered from ANSWERS, or the test fails.
ANSWERS is an alist (REGEXP . ANSWER) matched against the prompt text.
ANSWER is returned as-is, except: a function is called; for
`completing-read' the keyword `:default' returns the DEF argument and
`:first' the first candidate; for `completing-read-multiple' `:first'
returns a one-element list."
  (declare (indent 1))
  `(let ((answers ,answers))
     (cl-flet ((answer (prompt)
                 (let ((hit (cl-find-if (lambda (a) (string-match-p (car a) prompt))
                                        answers)))
                   (unless hit (ert-fail (list "unexpected prompt" prompt)))
                   (let ((v (cdr hit)))
                     (if (functionp v) (funcall v) v)))))
       (cl-letf (((symbol-function 'completing-read)
                  (lambda (prompt coll &optional _p _r _i _h def &rest _)
                    (let ((v (answer prompt)))
                      (cond ((eq v :default) def)
                            ((eq v :first) (car coll))
                            (t v)))))
                 ((symbol-function 'completing-read-multiple)
                  (lambda (prompt coll &rest _)
                    (let ((v (answer prompt)))
                      (if (eq v :first) (list (car coll)) v))))
                 ((symbol-function 'read-string)
                  (lambda (prompt &rest _) (answer prompt)))
                 ((symbol-function 'y-or-n-p)
                  (lambda (prompt) (answer prompt))))
         ,@body))))

(ert-deftest a3madkour-pub-author-test/published-targets-read-bundle-titles ()
  (a3madkour-pub-author-test--with-site
    (a3madkour-pub-author-test--page "research/themes" "beta" "title" "\"Beta \\\"B\\\"\"")
    (a3madkour-pub-author-test--page "research/themes" "alpha" "title" "Alpha")
    (a3madkour-pub-author-test--page "research/themes" "untitled")
    (with-temp-file (expand-file-name "content/research/themes/_index.md"
                                      (a3madkour-pub-yaml/site-root))
      (insert "---\ntitle: Section\n---\n"))
    (should (equal (a3madkour-pub-author--published-targets "research/themes")
                   '(("alpha" . "Alpha") ("beta" . "Beta \"B\"")
                     ("untitled" . "untitled"))))
    (should-not (a3madkour-pub-author--published-targets "streams"))))

(ert-deftest a3madkour-pub-author-test/next-weight-is-max-plus-ten ()
  (a3madkour-pub-author-test--with-site
    (should (= (a3madkour-pub-author--next-weight "research/themes") 10))
    (a3madkour-pub-author-test--page "research/themes" "a" "weight" "10")
    (a3madkour-pub-author-test--page "research/themes" "b" "weight" "30")
    (a3madkour-pub-author-test--page "research/themes" "c" "weight" "\"x\"")
    (should (= (a3madkour-pub-author--next-weight "research/themes") 40))))

(ert-deftest a3madkour-pub-author-test/fields-to-fill-per-section ()
  (a3madkour-pub-author-test--with-site
    (insert "#+title: T\n")
    (should (equal (mapcar #'car (a3madkour-pub-author--fields-to-fill "research/themes"))
                   '("description" "status" "weight")))
    (should (equal (mapcar #'car (a3madkour-pub-author--fields-to-fill "research/questions"))
                   '("description" "status" "theme" "supporting_notes" "started")))
    (should-not (a3madkour-pub-author--fields-to-fill "garden"))
    (should-not (a3madkour-pub-author--fields-to-fill "essays"))
    (should-not (a3madkour-pub-author--fields-to-fill "library/reading"))
    (should (equal (mapcar #'car (a3madkour-pub-author--fields-to-fill "recipes"))
                   '("sources" "ingredients" "steps")))
    (insert "#+HUGO_CUSTOM_FRONT_MATTER: :status dormant :media_type book\n")
    (should (equal (mapcar #'car (a3madkour-pub-author--fields-to-fill "research/themes"))
                   '("description" "weight")))
    (should (equal (mapcar #'car (a3madkour-pub-author--fields-to-fill "garden"))
                   '("creator")))))

(ert-deftest a3madkour-pub-author-test/fields-to-fill-bad-variant-is-user-error ()
  (a3madkour-pub-author-test--with-site
    (insert "#+HUGO_CUSTOM_FRONT_MATTER: :media_type hologram\n")
    (should-error (a3madkour-pub-author--fields-to-fill "garden") :type 'user-error)))

(ert-deftest a3madkour-pub-author-test/ask-by-type ()
  (a3madkour-pub-author-test--with-site
    (let ((ints '("abc" "7")) (texts '("" "has \"quote\"" "ok text")))
      (a3madkour-pub-author-test--answering
          (list (cons " status: " :default)
                (cons " weight" (lambda () (pop ints)))
                (cons " tagline: " (lambda () (pop texts)))
                (cons " summary (optional): " ""))
        (should (equal (a3madkour-pub-author--ask
                        "research/themes" "status"
                        (a3madkour-sections/field "research/themes" "status"))
                       "active"))
        (should (equal (a3madkour-pub-author--ask
                        "research/questions" "weight" '((type . "int") (required . t)))
                       7))
        (should (equal (a3madkour-pub-author--ask
                        "works/games" "tagline" '((type . "text") (required . t)))
                       "ok text"))
        (should (eq (a3madkour-pub-author--ask
                     "research/themes" "summary" '((type . "text")))
                    'skip))
        (should (equal (a3madkour-pub-author--ask
                        "research/questions" "started"
                        (a3madkour-sections/field "research/questions" "started"))
                       (format-time-string "%Y-%m-%d")))))))

(ert-deftest a3madkour-pub-author-test/ask-ref-without-targets ()
  (a3madkour-pub-author-test--with-site
    (let ((err (should-error (a3madkour-pub-author--ask
                              "research/questions" "theme"
                              (a3madkour-sections/field "research/questions" "theme"))
                             :type 'user-error)))
      (should (string-match-p "publish a research/themes page first"
                              (error-message-string err))))
    (should (eq (a3madkour-pub-author--ask
                 "research/questions" "supporting_notes"
                 (a3madkour-sections/field "research/questions" "supporting_notes"))
                'skip))))
```

- [ ] **Step 2: Run, and expect FAIL**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "published-targets|next-weight|fields-to-fill|ask-|^Ran|unexpected"
```

Expected: all FAIL with `void-function`.

- [ ] **Step 3: Implement**

Insert after Task 7's helpers in `a3madkour-publish-author.el`:

```elisp
;; -- internal: what a3-publish-mark asks, and how --

(defmacro a3madkour-pub-author--with-contract (&rest body)
  "Run BODY; turn a section-contract `error' into a `user-error'.
A `user-error' passes through unchanged."
  `(condition-case err (progn ,@body)
     (user-error (signal (car err) (cdr err)))
     (error (user-error "a3-publish-mark: %s" (error-message-string err)))))

(defun a3madkour-pub-author--site-root ()
  "The Hugo site root, or a `user-error' when it cannot be located."
  (unless (bound-and-true-p a3madkour-pub/site-data-dir)
    (user-error "a3-publish-mark: `a3madkour-pub/site-data-dir' is not set"))
  (a3madkour-pub-yaml/site-root))

(defun a3madkour-pub-author--fm-scalar (file key)
  "Top-level scalar KEY of FILE's YAML frontmatter, unquoted, or nil."
  (with-temp-buffer
    (insert-file-contents file)
    (goto-char (point-min))
    (when (looking-at "---[ \t]*\n\\(\\(?:.*\n\\)*?\\)---[ \t]*$")
      (let ((fm (match-string-no-properties 1)))
        (when (string-match (format "^%s:[ \t]*\\(.*?\\)[ \t]*$"
                                    (regexp-quote key))
                            fm)
          (let ((v (match-string 1 fm)))
            (if (string-match-p "\\`\".*\"\\'" v)
                (condition-case nil (read v) (error (substring v 1 -1)))
              v)))))))

(defun a3madkour-pub-author--bundles (section)
  "The index.md of every page bundle under content/SECTION/, or nil."
  (let ((dir (expand-file-name (concat "content/" section)
                               (a3madkour-pub-author--site-root))))
    (when (file-directory-p dir)
      (cl-loop for sub in (directory-files dir t "\\`[^._]")
               for md = (expand-file-name "index.md" sub)
               when (and (file-directory-p sub) (file-exists-p md))
               collect md))))

(defun a3madkour-pub-author--published-targets (to)
  "Published pages of section TO as ((SLUG . TITLE) ...), sorted by slug.
TITLE is the bundle frontmatter's title, falling back to SLUG."
  (sort (mapcar (lambda (md)
                  (let ((slug (file-name-nondirectory
                               (directory-file-name (file-name-directory md)))))
                    (cons slug (or (a3madkour-pub-author--fm-scalar md "title")
                                   slug))))
                (a3madkour-pub-author--bundles to))
        (lambda (a b) (string< (car a) (car b)))))

(defun a3madkour-pub-author--next-weight (section)
  "Largest numeric weight among SECTION's published pages + 10, or 10."
  (let ((ws (cl-loop for md in (a3madkour-pub-author--bundles section)
                     for w = (a3madkour-pub-author--fm-scalar md "weight")
                     when (and w (string-match-p "\\`[0-9]+\\'" w))
                     collect (string-to-number w))))
    (if ws (+ 10 (apply #'max ws)) 10)))

(defun a3madkour-pub-author--fields-to-fill (section)
  "SECTION's fields `a3-publish-mark' must supply, as ((NAME . SPEC) ...).
A field qualifies when it is not `from: pipeline', is `required' or
`ask', and is absent from the buffer.  The variant case comes from the
buffer's value of the section's `variants.on' field.  A `store: data'
section (library) yields nil: `a3-library-insert-item' writes its items."
  (let ((spec (a3madkour-sections/spec section)))
    (unless (equal (alist-get 'store spec) "data")
      (let* ((on (alist-get 'on (alist-get 'variants spec)))
             (case (a3madkour-pub-author--with-contract
                     (a3madkour-sections/variant-case
                      section (and on (a3madkour-pub-author--cfm-get on))))))
        (cl-remove-if-not
         (lambda (cell)
           (let ((fs (cdr cell)))
             (and (not (equal (alist-get 'from fs) "pipeline"))
                  (or (alist-get 'required fs) (alist-get 'ask fs))
                  (not (a3madkour-pub-author--field-present-p (car cell))))))
         (a3madkour-sections/fields section case))))))

(defconst a3madkour-pub-author--string-shapes
  '(("int" "\\`[0-9]+\\'" "a whole number")
    ("date" "\\`[0-9]\\{4\\}-[0-9]\\{2\\}-[0-9]\\{2\\}\\'" "a YYYY-MM-DD date"))
  "Per-type (REGEXP DESCRIPTION) a typed answer must match.")

(defun a3madkour-pub-author--ask-string (name type required keyword-p prompt)
  "Read field NAME of string-entered TYPE; re-prompt until acceptable.
An empty answer returns `skip' unless REQUIRED.  A double quote is
refused unless KEYWORD-P (custom front matter cannot carry one)."
  (let ((shape (cdr (assoc type a3madkour-pub-author--string-shapes)))
        v done)
    (while (not done)
      (setq v (string-trim (read-string prompt)))
      (cond
       ((string-empty-p v)
        (if required (message "%s is required" name) (setq done t)))
       ((and (not keyword-p) (string-match-p "\"" v))
        (message "%s: a double quote cannot be written to \
#+HUGO_CUSTOM_FRONT_MATTER" name))
       ((and shape (not (string-match-p (car shape) v)))
        (message "%s must be %s" name (cadr shape)))
       (t (setq done t))))
    (cond ((string-empty-p v) 'skip)
          ((equal type "int") (string-to-number v))
          ((equal type "list") (split-string v "[ \t]+" t))
          (t v))))

(defun a3madkour-pub-author--ask-ref (name spec prompt)
  "Pick field NAME's ref/refs value (SPEC) from published targets."
  (let* ((to (alist-get 'to spec))
         (required (alist-get 'required spec))
         (choices (mapcar (lambda (c)
                            (cons (format "%s (%s)" (cdr c) (car c)) (car c)))
                          (a3madkour-pub-author--published-targets to))))
    (cond
     ((and (null choices) required)
      (user-error "a3-publish-mark: %s needs a published %s page; \
publish a %s page first" name to to))
     ((null choices) 'skip)
     ((equal (alist-get 'type spec) "ref")
      (let (pick)
        (while (progn (setq pick (completing-read prompt (mapcar #'car choices)
                                                  nil t))
                      (and required (string-empty-p pick))))
        (if (string-empty-p pick) 'skip (cdr (assoc pick choices)))))
     (t
      (let (picks)
        (while (progn (setq picks (completing-read-multiple
                                   prompt (mapcar #'car choices) nil t))
                      (and required (null picks))))
        (if picks
            (mapcar (lambda (p) (cdr (assoc p choices))) picks)
          'skip))))))

(defun a3madkour-pub-author--ask (section name spec)
  "Obtain the value of SECTION's field NAME (SPEC), prompting as needed.
Returns the value, or `skip' for an optional field left empty.  Writes
nothing.  Signals `user-error' for a required ref with no targets."
  (let* ((type (alist-get 'type spec))
         (required (alist-get 'required spec))
         (fill (alist-get 'fill spec))
         (keyword-p (assoc name a3madkour-pub-author--keyword-fields))
         (prompt (format "%s %s%s: " section name (if required "" " (optional)"))))
    (cond
     ((equal fill "today") (format-time-string "%Y-%m-%d"))
     ((equal fill "next-weight") (a3madkour-pub-author--next-weight section))
     ((equal type "enum")
      (let (v)
        (while (progn (setq v (completing-read prompt (alist-get 'values spec)
                                               nil t nil nil
                                               (alist-get 'default spec)))
                      (and required (string-empty-p v))))
        (if (string-empty-p v) 'skip v)))
     ((equal type "bool")
      (y-or-n-p (format "%s %s? (default %s) " section name
                        (if (alist-get 'default spec) "yes" "no"))))
     ((member type '("ref" "refs"))
      (a3madkour-pub-author--ask-ref name spec prompt))
     ((member type '("text" "int" "date" "list"))
      (a3madkour-pub-author--ask-string name type required keyword-p prompt))
     (t (error "a3-publish-mark: no prompt for field %s of type %S" name type)))))
```

- [ ] **Step 4: Run, and expect PASS; then the full suite**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "published-targets|next-weight|fields-to-fill|ask-|^Ran|unexpected"
```

Expected: all pass, and `0 unexpected`.

- [ ] **Step 5: Mutation-test the guards (revert after each)**

| Break | Expected failing test |
|---|---|
| `--ask-ref`: change the required-no-targets clause to return `'skip` | `ask-ref-without-targets` |
| `--fields-to-fill`: delete the `(not (a3madkour-pub-author--field-present-p ...))` conjunct | `fields-to-fill-per-section` |
| `--ask-string`: delete the double-quote clause | `ask-by-type` (returns `has "quote"`) |
| `--next-weight`: drop `+ 10` | `next-weight-is-max-plus-ten` |

- [ ] **Step 6: Commit**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-author.el emacs-configs/custom/lisp/a3madkour-publish-author-test.el && git commit -F - <<'EOF'
feat(author): decide and prompt for the fields a section still needs

fields-to-fill reads data/sections.json (not from:pipeline, required or
ask, absent from the buffer; garden's variant case from :media_type;
library skipped).  ask prompts per the spec §6 type table: enum
completing-read with default, bool y-or-n-p, ref/refs over published
content/<to>/*/index.md titles, text/int/date read-string with
re-prompt, fill today / next-weight with no prompt.  Writes nothing;
mark is wired up in the next commit.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

### Task 9: The `a3-publish-mark` fill-in (spec §6)

**Files:**
- Modify: `a3madkour-publish-author.el:104-141` (`a3-publish-mark`). Insert `--stale-fields` and `--gather` before it.
- Test: `a3madkour-publish-author-test.el`. Also add `(require 'a3madkour-publish-research)` and `(require 'a3madkour-publish-async)` at the top for the end-to-end test.

**Interfaces:**
- Consumes: Tasks 7–8.
- Produces: `(a3madkour-pub-author--stale-fields SECTION) -> (STRING ...)`, `(a3madkour-pub-author--gather SECTION) -> (:values ((NAME TYPE VALUE) ...) :by-hand (NAME ...))`. `(a3-publish-mark SECTION) -> SECTION|nil` keeps its signature and return contract.

- [ ] **Step 1: Write the failing tests**

Append to `a3madkour-publish-author-test.el`:

```elisp
;; -- Section registry Task 9: the a3-publish-mark fill-in --

(ert-deftest a3madkour-pub-author-test/mark-theme-fills-status-description-weight ()
  (a3madkour-pub-author-test--with-site
    (a3madkour-pub-author-test--page "research/themes" "alpha" "title" "\"Alpha\"" "weight" "10")
    (a3madkour-pub-author-test--page "research/themes" "beta" "title" "\"Beta\"" "weight" "30")
    (insert "#+title: New theme\n\nBody\n")
    (a3madkour-pub-author-test--answering
        '((" description: " . "What the theme asks.")
          (" status: " . :default))
      (should (equal (a3-publish-mark "research/themes") "research/themes")))
    (let ((s (buffer-string)))
      (should (string-match-p "^#\\+HUGO_PUBLISH: t$" s))
      (should (string-match-p "^#\\+HUGO_SECTION: research/themes$" s))
      (should (string-match-p "^#\\+HUGO_DESCRIPTION: What the theme asks\\.$" s))
      (should (string-match-p "^#\\+HUGO_CUSTOM_FRONT_MATTER: :status active$" s))
      (should (string-match-p "^#\\+HUGO_CUSTOM_FRONT_MATTER: :weight 40$" s)))))

(defun a3madkour-pub-author-test--question-site ()
  "Publish one theme and two garden notes under the current site root."
  (a3madkour-pub-author-test--page "research/themes" "procedural-narrative"
                                   "title" "\"Procedural narrative\"")
  (a3madkour-pub-author-test--page "garden" "note-a" "title" "\"Note A\"")
  (a3madkour-pub-author-test--page "garden" "note-b" "title" "\"Note B\""))

(defconst a3madkour-pub-author-test--question-answers
  '((" description: " . "Does it hold?")
    (" status: " . :default)
    (" theme: " . "Procedural narrative (procedural-narrative)")
    (" supporting_notes (optional): " . ("Note A (note-a)" "Note B (note-b)"))))

(ert-deftest a3madkour-pub-author-test/mark-question-picks-theme-from-published-set ()
  (a3madkour-pub-author-test--with-site
    (a3madkour-pub-author-test--question-site)
    (insert "#+title: New question\n")
    (a3madkour-pub-author-test--answering a3madkour-pub-author-test--question-answers
      (a3-publish-mark "research/questions"))
    (let ((s (buffer-string)))
      (should (string-match-p "^#\\+HUGO_CUSTOM_FRONT_MATTER: :theme procedural-narrative$" s))
      ;; Branch A form (Task 1); under Branch B: ":supporting_notes '(note-a note-b)".
      (should (string-match-p "^#\\+HUGO_CUSTOM_FRONT_MATTER: :supporting_notes note-a note-b$" s))
      (should (string-match-p (format "^#\\+HUGO_CUSTOM_FRONT_MATTER: :started %s$"
                                      (format-time-string "%Y-%m-%d"))
                              s))
      (should (string-match-p "^#\\+HUGO_CUSTOM_FRONT_MATTER: :status active$" s)))))

(ert-deftest a3madkour-pub-author-test/mark-second-run-asks-nothing ()
  (a3madkour-pub-author-test--with-site
    (a3madkour-pub-author-test--question-site)
    (insert "#+title: New question\n")
    (a3madkour-pub-author-test--answering a3madkour-pub-author-test--question-answers
      (a3-publish-mark "research/questions"))
    (let ((after-first (buffer-string)))
      (a3madkour-pub-author-test--answering nil
        (a3-publish-mark "research/questions"))
      (should (equal (buffer-string) after-first)))))

(ert-deftest a3madkour-pub-author-test/mark-never-overwrites-a-present-field ()
  (a3madkour-pub-author-test--with-site
    (insert "#+title: T\n#+HUGO_DESCRIPTION: Kept.\n"
            "#+HUGO_CUSTOM_FRONT_MATTER: :status dormant\n")
    (a3madkour-pub-author-test--answering nil
      (a3-publish-mark "research/themes"))
    (let ((s (buffer-string)))
      (should (string-match-p "^#\\+HUGO_DESCRIPTION: Kept\\.$" s))
      (should (string-match-p ":status dormant" s))
      (should-not (string-match-p ":status active" s))
      (should (string-match-p "^#\\+HUGO_CUSTOM_FRONT_MATTER: :weight 10$" s)))))

(ert-deftest a3madkour-pub-author-test/mark-quit-mid-way-changes-nothing ()
  "C-g at the third prompt, after two were answered: nothing is written,
not even #+HUGO_PUBLISH."
  (a3madkour-pub-author-test--with-site
    (a3madkour-pub-author-test--question-site)
    (insert "#+title: New question\n")
    (let ((before (buffer-string)))
      (a3madkour-pub-author-test--answering
          (list (cons " description: " "Does it hold?")
                (cons " status: " :default)
                (cons " theme: " (lambda () (signal 'quit nil))))
        ;; Not `should-error': it catches only `error' conditions, and
        ;; `quit' is not one (verified: it escapes `should-error').
        (should (eq (condition-case nil
                        (progn (a3-publish-mark "research/questions") 'returned)
                      (quit 'quit))
                    'quit)))
      (should (equal (buffer-string) before)))))

(ert-deftest a3madkour-pub-author-test/mark-required-ref-without-targets-errors ()
  (a3madkour-pub-author-test--with-site
    (insert "#+title: New question\n")
    (let ((before (buffer-string)))
      (a3madkour-pub-author-test--answering
          '((" description: " . "Q?") (" status: " . :default))
        (let ((err (should-error (a3-publish-mark "research/questions")
                                 :type 'user-error)))
          (should (string-match-p "publish a research/themes page first"
                                  (error-message-string err)))))
      (should (equal (buffer-string) before)))))

(ert-deftest a3madkour-pub-author-test/mark-fill-keeps-drawer-first ()
  (a3madkour-pub-author-test--with-site
    (insert ":PROPERTIES:\n:ID:       abc-123\n:END:\n#+title: T\n")
    (a3madkour-pub-author-test--answering
        '((" description: " . "D.") (" status: " . :default))
      (a3-publish-mark "research/themes"))
    (should (string-prefix-p ":PROPERTIES:\n:ID:       abc-123\n:END:\n" (buffer-string)))
    (should (eq (org-element-type (org-element-at-point (point-min))) 'property-drawer))
    (should (equal (org-entry-get (point-min) "ID") "abc-123"))))

(ert-deftest a3madkour-pub-author-test/mark-section-change-offers-removal ()
  (dolist (accept '(t nil))
    (a3madkour-pub-author-test--with-site
      (insert "#+HUGO_PUBLISH: t\n#+HUGO_SECTION: garden\n"
              "#+HUGO_CUSTOM_FRONT_MATTER: :year 2026 :topic_map a b\n#+title: T\n")
      (a3madkour-pub-author-test--answering
          (list (cons "\\`Move from" t)
                (cons "\\`Remove fields not in research/themes (year, topic_map)" accept)
                (cons " description: " "D.")
                (cons " status: " :default))
        (a3-publish-mark "research/themes"))
      (let ((s (buffer-string)))
        (should (string-match-p ":status active" s))
        (if accept
            (progn (should-not (string-match-p "topic_map" s))
                   (should-not (string-match-p ":year" s)))
          (should (string-match-p ":year 2026 :topic_map a b" s)))))))

(ert-deftest a3madkour-pub-author-test/mark-garden-media-variant-asks-its-fields ()
  (a3madkour-pub-author-test--with-site
    (insert "#+title: A book\n#+HUGO_CUSTOM_FRONT_MATTER: :media_type book\n")
    (a3madkour-pub-author-test--answering
        '((" status: " . "finished") (" creator: " . "Example Author"))
      (a3-publish-mark "garden"))
    (should (string-match-p ":status finished" (buffer-string)))
    (should (string-match-p ":creator \"Example Author\"" (buffer-string)))))

(ert-deftest a3madkour-pub-author-test/mark-library-and-structured ()
  (a3madkour-pub-author-test--with-site
    (insert "#+title: Shelf\n")
    (a3madkour-pub-author-test--answering nil
      (a3-publish-mark "library/reading"))
    (should (string-match-p "^#\\+HUGO_SECTION: library/reading$" (buffer-string))))
  (a3madkour-pub-author-test--with-site
    (insert "#+title: Soup\n")
    (let (said)
      (cl-letf (((symbol-function 'message)
                 (lambda (fmt &rest args) (push (apply #'format fmt args) said))))
        (a3madkour-pub-author-test--answering nil
          (a3-publish-mark "recipes")))
      (should (cl-some (lambda (m) (string-match-p "sources, ingredients, steps" m))
                       said)))))

(ert-deftest a3madkour-pub-author-test/mark-errors-on-missing-contract ()
  (a3madkour-sections-test--with-root nil
    (with-temp-buffer
      (org-mode)
      (insert "#+title: T\n")
      (let ((err (should-error (a3-publish-mark "garden") :type 'user-error)))
        (should (string-match-p "contract not found at" (error-message-string err))))
      (should (equal (buffer-string) "#+title: T\n")))))

(ert-deftest a3madkour-pub-author-test/mark-output-publishes-through-ox-hugo ()
  "End to end: what mark writes for a question reaches the bundle with
`theme' as a string and `supporting_notes' as a YAML list."
  (a3madkour-pub-author-test--with-site
    (a3madkour-pub-author-test--question-site)
    (let* ((root (a3madkour-pub-yaml/site-root))
           (notes-dir (make-temp-file "a3-mark-e2e-notes" t))
           (src (expand-file-name "marked-question.org" notes-dir)))
      (unwind-protect
          (progn
            (make-directory (expand-file-name "content/research/questions" root) t)
            (with-temp-file (expand-file-name "data/url-history.yaml" root)
              (insert "notes: []\n"))
            (insert ":PROPERTIES:\n:ID: 44444444-aaaa-bbbb-cccc-dddddddddddd\n"
                    ":LAST_MODIFIED: 2026-05-30\n:END:\n"
                    "#+title: Marked question\n#+HUGO_BASE_DIR: " root "\n\nBody.\n")
            (a3madkour-pub-author-test--answering a3madkour-pub-author-test--question-answers
              (a3-publish-mark "research/questions"))
            (write-region (point-min) (point-max) src)
            (let ((a3madkour-pub/org-notes-dir notes-dir) (status nil))
              (cl-letf (((symbol-function 'org-roam-db-sync) #'ignore))
                (a3madkour-pub/begin-publish)
                (a3madkour-pub-research/publish-research-file
                 src (make-a3-pub-async-run) :on-done (lambda (s) (setq status s)))
                (a3madkour-pub/finish-publish))
              (should (eq status 'ok)))
            (let ((md (with-temp-buffer
                        (insert-file-contents
                         (expand-file-name
                          "content/research/questions/marked-question/index.md" root))
                        (buffer-string))))
              (should (string-match-p "^theme: \"procedural-narrative\"$" md))
              (should (string-match-p "^supporting_notes: \\[\"note-a\", \"note-b\"\\]$" md))
              (should (string-match-p "^description: \"Does it hold\\?\"$" md))
              (should (string-match-p "^status: \"active\"$" md))))
        (delete-directory notes-dir t)))))
```

- [ ] **Step 2: Run, and expect FAIL**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-author-test/mark-|^Ran|unexpected"
```

Expected: the new `mark-` tests FAIL (the current mark writes only `HUGO_PUBLISH`/`HUGO_SECTION`, and its section change does no removal). `mark-errors-on-missing-contract` FAILS because nothing is checked. The pre-existing `mark-` tests still pass.

- [ ] **Step 3: Implement**

Insert before `a3-publish-mark` in `a3madkour-publish-author.el`:

```elisp
(defun a3madkour-pub-author--stale-fields (section)
  "Fields in the buffer that SECTION's contract does not list.
Candidates are the custom front matter keys plus description/summary;
`#+TITLE:' is never offered for removal."
  (let ((legal (a3madkour-sections/emitted-keys section))
        (present (append
                  (cl-loop for (name . _kw) in a3madkour-pub-author--keyword-fields
                           when (and (not (equal name "title"))
                                     (a3madkour-pub-author--field-present-p name))
                           collect name)
                  (a3madkour-pub-author--cfm-keys))))
    (cl-remove-if (lambda (n) (member n legal))
                  (delete-dups present))))

(defun a3madkour-pub-author--gather (section)
  "Collect every value SECTION still needs; write nothing.
Returns (:values ((NAME TYPE VALUE) ...) :by-hand (NAME ...)).  BY-HAND
lists required `structured'/`object' fields, which are not prompted."
  (let (values by-hand)
    (dolist (cell (a3madkour-pub-author--fields-to-fill section))
      (let* ((name (car cell))
             (fs (cdr cell))
             (type (alist-get 'type fs)))
        (if (member type '("structured" "object"))
            (when (alist-get 'required fs) (push name by-hand))
          (let ((v (a3madkour-pub-author--ask section name fs)))
            (unless (eq v 'skip)
              (push (list name type v) values))))))
    (list :values (nreverse values) :by-hand (nreverse by-hand))))
```

Replace the whole `a3-publish-mark` (lines 104–141) with:

```elisp
;;;###autoload
(cl-defun a3-publish-mark (section)
  "Mark the current org buffer for publish at SECTION and fill its fields.

Sets `#+HUGO_PUBLISH: t' + `#+HUGO_SECTION: SECTION', then supplies
every field SECTION's contract (data/sections.json) requires or marks
`ask' that the publisher cannot derive and the buffer lacks: prompting
for each (enum, bool, ref/refs over published pages, text) or filling it
(today, next weight).  title/description/summary are written as
`#+TITLE:'/`#+HUGO_DESCRIPTION:'/`#+HUGO_SUMMARY:', everything else as
`#+HUGO_CUSTOM_FRONT_MATTER: :key value'.  A field already present is
never prompted for or overwritten.

Every value is gathered BEFORE anything is written, so `C-g' (or a
`user-error' such as a required ref with no published targets) leaves
the buffer untouched.

Cross-section guard: if the buffer already has `#+HUGO_SECTION: <other>'
and SECTION differs, prompts `y-or-n-p' before changing; declining
aborts and returns nil.  On a change, offers (one `y-or-n-p') to remove
the fields the new section's contract does not list.

Refuses outside `org-mode', in a read-only buffer, or when the contract
is missing or malformed.  Returns SECTION, or nil if declined."
  (interactive
   (let ((current (a3madkour-pub-keywords/extract "HUGO_SECTION")))
     (list (completing-read "Section: " a3madkour-pub/sections
                            nil t nil nil current))))
  (unless (derived-mode-p 'org-mode)
    (user-error "a3-publish-mark: current buffer is not org-mode"))
  (when buffer-read-only
    (user-error "a3-publish-mark: buffer is read-only"))
  (a3madkour-pub-author--with-contract (a3madkour-sections/spec section))
  (let ((current (a3madkour-pub-keywords/extract "HUGO_SECTION")))
    (when (and current
               (not (string= current section))
               (not (y-or-n-p
                     (format "Move from `%s' to `%s'? (next publish-living will record slug-shift) "
                             current section))))
      (cl-return-from a3-publish-mark nil))
    (let* ((stale (and current
                       (not (string-empty-p current))
                       (not (string= current section))
                       (a3madkour-pub-author--stale-fields section)))
           (remove (and stale
                        (y-or-n-p (format "Remove fields not in %s (%s)? "
                                          section (string-join stale ", ")))))
           (plan (a3madkour-pub-author--gather section)))
      ;; Everything above only read and prompted; everything below writes.
      (a3madkour-pub-author--upsert-keyword "HUGO_PUBLISH" "t")
      (a3madkour-pub-author--upsert-keyword "HUGO_SECTION" section)
      (when remove
        (mapc #'a3madkour-pub-author--remove-field stale))
      (dolist (v (plist-get plan :values))
        (apply #'a3madkour-pub-author--write-field v))
      (when (plist-get plan :by-hand)
        (message "a3-publish-mark: %s also needs %s (structured; fill in by hand)"
                 section (string-join (plist-get plan :by-hand) ", ")))
      section)))
```

Update the commentary at line 10 of `a3madkour-publish-author.el`, which reads `;; All six compose existing primitives (sections registry, library config,`, to `;; All six compose existing primitives (the section registry and the site's`. Change line 11, `;; keywords API, publish manifest).  No new tables.`, to `;; data/sections.json contract, keywords API, publish manifest).  No new tables.`

- [ ] **Step 4: Run, and expect PASS; then the full suite**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "a3madkour-pub-author-test/|^Ran|unexpected"
```

Expected: every author test passes, old and new, including the `S1 row 10` drawer tests. `0 unexpected`.

- [ ] **Step 5: Mutation-test the guards (revert after each)**

| Break | Expected failing test |
|---|---|
| Atomicity: move the two `upsert-keyword` lines to just before `(let* ((stale` | `mark-quit-mid-way-changes-nothing`, `mark-required-ref-without-targets-errors` |
| Never-overwrite: delete the `field-present-p` conjunct in `--fields-to-fill` | `mark-second-run-asks-nothing`, `mark-never-overwrites-a-present-field` |
| No-targets: make `--ask-ref`'s required-no-targets clause return `'skip` | `mark-required-ref-without-targets-errors` |
| Removal: ignore the answer (`(when stale (mapc ...))`) | `mark-section-change-offers-removal` (decline branch) |
| Contract check: delete the top `(a3madkour-pub-author--with-contract (a3madkour-sections/spec section))` | `mark-errors-on-missing-contract` (a raw `error`, not `user-error`, from `fields-to-fill`) |

- [ ] **Step 6: Commit**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3madkour-publish-author.el emacs-configs/custom/lisp/a3madkour-publish-author-test.el && git commit -F - <<'EOF'
feat(author): a3-publish-mark fills the fields a section needs

After setting HUGO_PUBLISH/HUGO_SECTION, mark asks for every field the
section's data/sections.json contract requires (or marks ask) that the
pipeline cannot derive and the buffer lacks, gathers all answers before
writing anything (C-g or a missing ref target leaves the buffer
untouched), and writes title/description/summary as their keywords and
everything else as #+HUGO_CUSTOM_FRONT_MATTER: :key value.  Idempotent;
a section change offers to remove the fields the new section does not
list; the file property drawer stays first.  An end-to-end test runs a
marked question through the real research handler and ox-hugo.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

### Task 10: Load wiring: `a3-pub.sh` `-l` lines and the `config.org` requires

**Files:**
- Modify: `a3-pub.sh`: every `-l a3madkour-publish \` line (5 batch blocks: check-orphans, publish-living, publish-deliberate, sync-citations, default) and every `-l a3madkour-publish-frontmatter \` line (3 blocks: living, deliberate, default).
- Modify: `/Users/a3madkour/dotfiles/emacs-configs/custom/config.org`, the `* Website publish` block (line ~5241).
- Not tracked: `/Users/a3madkour/dotfiles/emacs-configs/custom/config.el` is generated by `org-babel-load-file` in `init.el:43`, and it re-tangles when `config.org` is newer. Do not edit or commit it.

- [ ] **Step 1: Add the `-l` lines**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && perl -0pi -e 's/^([ \t]*)-l a3madkour-publish \\\n/$1-l a3madkour-publish \\\n$1-l a3madkour-publish-registry \\\n/mg; s/^([ \t]*)-l a3madkour-publish-frontmatter \\\n/$1-l a3madkour-publish-frontmatter \\\n$1-l a3madkour-sections \\\n/mg' a3-pub.sh && bash -n a3-pub.sh && grep -c -- "-l a3madkour-publish-registry " a3-pub.sh && grep -c -- "-l a3madkour-sections " a3-pub.sh && grep -c "works-vocab" a3-pub.sh
```

Expected: `5`, `3`, `0`, and no syntax error.

- [ ] **Step 2: Spot-check public functions of both new modules through the wrapper**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./a3-pub.sh --eval '(progn (setq a3madkour-pub/site-data-dir (expand-file-name "~/Sync/Workspace/a3madkour.github.io/data/")) (princ (format "registry=%d sections=%d poetry-sym=%S\n" (length (a3madkour-pub-registry/names)) (length (a3madkour-sections/names)) (a3madkour-pub-section/symbol "works/poetry"))))' 2>&1 | grep "registry="
```

Expected: `registry=14 sections=14 poetry-sym=works-poetry`.

- [ ] **Step 3: `config.org` requires**

In the `* Website publish` block, insert directly after its `#+begin_src emacs-lisp` line and before `(require 'a3madkour-publish-deliberate)`:

```elisp
;; The section registry and the reader for the site's data/sections.json
;; contract.  Both also arrive transitively through the modules below; named
;; here so the dependency is visible (plan-wrapper rule).
(require 'a3madkour-publish-registry)
(require 'a3madkour-sections)
```

Then confirm the line is present and no works-vocab reference remains:

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom && grep -n "a3madkour-publish-registry\|a3madkour-sections\|works-vocab" config.org
```

Expected: the two new `require` lines and no `works-vocab`. For the running interactive Emacs, either restart it (`init.el` re-tangles `config.el` because `config.org` is now newer) or evaluate the two `require`s with `M-:`.

- [ ] **Step 4: Full suite green**

```bash
cd /Users/a3madkour/dotfiles/emacs-configs/custom/lisp && ./run-tests.sh 2>&1 | grep -E "^Ran|unexpected"
```

- [ ] **Step 5: Commit**

```bash
cd /Users/a3madkour/dotfiles && git add emacs-configs/custom/lisp/a3-pub.sh emacs-configs/custom/config.org && git commit -F - <<'EOF'
chore(publish): load the registry and sections reader explicitly

a3-pub.sh loads a3madkour-publish-registry in all five batch blocks and
a3madkour-sections in the three that load the frontmatter normalizer;
config.org's Website publish block requires both.  (config.el is
generated by org-babel-load-file and untracked.)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

### Task 11: A real `a3-pub.sh --publish-living` changes nothing

This is the idempotency contract (§11 of the phase-3 design) applied to the whole refactor: the registry dispatch, the contract-driven filters and the loud missing-handler path, all run against the real `~/org` corpus.

- [ ] **Step 1: Snapshot the site working tree**

```bash
SCRATCH=$(mktemp -d) && echo "$SCRATCH" && cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && git status --porcelain=v1 > "$SCRATCH/before.txt" && git diff --stat > "$SCRATCH/before-diff.txt"
```

- [ ] **Step 2: Run the living publish (no pipe, so the exit status is real)**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && /Users/a3madkour/dotfiles/emacs-configs/custom/lisp/a3-pub.sh --publish-living > "$SCRATCH/living.log" 2>&1; echo "exit=$?"
```

Expected: `exit=0`. If org-math-lint is not installed, the wrapper says so and exits non-zero before Emacs starts. Then re-run with `--skip-math-check` appended, and record that in the hand-off.

- [ ] **Step 3: Assert zero content change and no handler errors**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && git status --porcelain=v1 > "$SCRATCH/after.txt" && git diff --stat > "$SCRATCH/after-diff.txt" && diff "$SCRATCH/before.txt" "$SCRATCH/after.txt" && diff "$SCRATCH/before-diff.txt" "$SCRATCH/after-diff.txt" && echo NO-CONTENT-DIFF; grep -nE "handler-missing|ERROR|WARN.*status=|not in \(" "$SCRATCH/living.log"
```

Expected: `NO-CONTENT-DIFF`, and the final grep prints nothing.
- A content diff means a filter now drops or adds a key that real pages carry. Inspect it with `git diff`, then fix `data/sections.json` (site) or the normalizer, re-run the suite, and repeat this task.
- A `handler-missing` line means a living module is absent from the `--publish-living` `-l` list. Add it and repeat.

- [ ] **Step 4: Restore the site tree if Step 3 failed**

Do this only when Step 3 printed a diff and you are about to fix and re-run:

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io && git diff --name-only | grep -E "^(content|data)/" | xargs git checkout --
```

No commit for this task; it is verification.

---

### Task 12: Hand-off: resume the S1 research dogfood

Not automated. The user marks their own node; the agent reports and stops.

- [ ] **Step 1: Report to the user**

Report the commits (dotfiles Tasks 1–10, site Task 6), the Task 11 result, and these two behaviour changes:
- A registered handler that is not loaded is now a loud per-file error.
- works-lint now checks `tile_size`.

Then hand back the S1 research step (spec §7 end-to-end, roadmap S1):
1. In the real research org node, run `M-x a3-publish-mark` → `research/themes`, and answer status, description and the next weight. Repeat for the question node → `research/questions`, picking the theme, supporting notes and started.
2. `a3-publish-living` (or `a3-pub.sh --publish-living`).
3. `python3 tools/check_research_fixtures.py && python3 tools/check_research_links.py` pass.
4. `hugo --minify` builds (no dev server alive).
5. Visual check of `/research/`, the theme page, the question page and `/research/graph/`.
6. `tools/ci-local.sh` passes (Playwright serial, per row 14).
7. Log friction row 15 as resolved in the authoring-infra roadmap (spec §8 step 6; a site-repo doc edit).

---

## Self-review

**Spec coverage**

| Spec | Covered by |
|---|---|
| §3: knowledge split, registry keys == JSON keys, slash names stored once, symbol derived by `a3madkour-pub-section/symbol` alone | Tasks 2–3. Cross-repo `--keys-equal-real-sections-json`. Task 4 Step 13 grep proves the converters are gone. |
| §3: works-vocab folded in and deleted | Task 6 (both repos). |
| §5.2: reader at site root, mtime cache, fail-closed, API `spec`/`fields`/`enum`/`emitted-keys`, no load-time deps | Task 2. Return shapes are fixed in its Interfaces. `--loads-under-emacs-Q` pins the leaf property. |
| §5.2: consumers switch (research, essays, poetry, works, library; works-lint rule 2; mark) | Task 4 (library), Task 5 (essays/research/poetry), Task 6 (works and lint rules 1/2/6), Tasks 7–9 (mark). |
| §5.3: one defconst keyed by slash name, `:mode`/`:handler`/`:data-file`/`:default-medium` | Task 3. |
| §5.3: replaces every §1 list including the living `with-eval-after-load` blocks; handlers resolved when called | Task 4. Fixed decision: a missing handler is loud (Review Focus 1). |
| §5.3: derived `a3madkour-pub/sections` (streams/about as `:mode nil`), deliberate-sections, frontmatter dispatch, works `--sections` | Task 4 Steps 3, 6, 7. |
| §6 steps 1–6: pick section, collect fields (garden variant, library skipped), gather-then-write with the type table, ref targets from `content/<to>/*/index.md`, write via `upsert-keyword` (drawer hoist kept) plus a per-key cfm helper, idempotent, section-change removal | Tasks 7–9. Each §6 bullet has a named test in Task 9. Mutations cover atomicity, never-overwrite and no-targets. |
| §6 errors: JSON missing/malformed (names path), required ref without targets, not org-mode / read-only | `mark-errors-on-missing-contract`, `mark-required-ref-without-targets-errors`, and the existing `mark-refuses-*` tests. |
| §6 step 4: refs round-trip verified first | Task 1 spike, decision rule, Branch A/B code in Task 7; the end-to-end pin is in Task 9. |
| §7 dotfiles: reader tests ported (fail closed, mtime cache, emitted-keys) | Task 2 (ported from `a3madkour-works-vocab-test.el`), deleted in Task 6. |
| §7 dotfiles: registry tests (handlers fboundp, slash→symbol total and injective, deliberate-sections == `:mode deliberate`, cross-repo key set) | Task 3; Task 4 ports the unpublish row-2 test. |
| §7 dotfiles: mark tests (theme, question, second run, C-g, no targets, drawer first, section change) | Task 9. |
| §7 mutation list (dotfiles items: cross-repo key check, atomicity, never-overwrite, no-targets) | Task 3 Step 5, Task 9 Step 5, plus every other guard's table. |
| §8 step 3 (registry, derived lists, old lists deleted in the same commit, `a3-pub.sh` `-l`) | Tasks 3–4 and Task 10. `-l` is split into its own commit after the modules exist; the modules already load transitively before it. |
| §8 step 4 (normalizers and works-lint read sections; works-vocab and site works-vocab.json deleted) | Tasks 5–6. |
| §8 step 5 (mark fill-in) | Tasks 7–9. |

**Ambiguities resolved here**

- *Return shapes.* `fields` returns `((NAME-STRING . SPEC-ALIST) ...)`. `emitted-keys` returns strings, and the callers `intern` them. `enum` takes a dotted path (`platform_embed.kind`), because platform kinds hang off an object field.
- *works-lint rule 1.* The spec says only "keys/enums from sections". This plan defines `required-authored` as `required` and not `from: pipeline`, which reproduces the old `--required` exactly (Task 6 Step 1 checks it). Rule 2 checks every contract enum, which adds `tile_size` (intended, recorded).
- *Theme filtering.* The spec says the forbidden keys become "not in the themes field set". Implemented as a closed filter on themes only; questions are unchanged, as the spec does not ask for them.
- *Which fields mark may remove on a section change.* Custom front matter keys plus description/summary. `#+TITLE:` is never offered, because org-roam uses it.
- *Fixture versus real file.* The fixture's annotations are test inputs, and only its section names are pinned. Real-contract facts are asserted against the real file (Review Focus 3).
