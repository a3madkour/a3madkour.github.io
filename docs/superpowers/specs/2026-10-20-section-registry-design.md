# Section registry + shared field contract — design

Date: 2026-10-20. Status: approved in chat; awaiting written-spec review.
Repos: site (`a3madkour.github.io`) and dotfiles (`~/dotfiles/emacs-configs/custom/lisp/`).
Roadmap: interrupts S1 of `2026-10-15-authoring-infra-roadmap.md`. The research
step of the dogfood is paused until this lands (friction row 15).

## 1. Problem

`a3-publish-mark` writes `#+HUGO_PUBLISH` and `#+HUGO_SECTION` and stops. The
author then has to hand-type every other field the section requires. For a
research theme that is `status`, `weight` and `description`, plus `theme` on a
question. The only place those fields are spelled out is the site's Python
linter, so a forgotten field shows up as a linter failure after the publish.

The cause is structural. Per-section knowledge is written down many times, in
two languages, with nothing tying the copies together:

- **Section lists.** About 8 elisp lists in 3 spellings (`works/poetry`,
  `works-poetry`, the interned symbol `'works/poetry`):
  - `a3madkour-pub/sections` (`a3madkour-publish.el:37`)
  - `a3madkour-pub-deliberate-sections` (`:158`)
  - the deliberate handler table (`a3madkour-publish-deliberate.el:20`)
  - the living handler table, filled by 5 `with-eval-after-load` blocks
    (`a3madkour-publish-living.el:92-119`)
  - `--known-sections` (`a3madkour-publish-frontmatter.el:60`)
  - library `--config` (`a3madkour-publish-library.el:24`)
  - works `--sections` (`a3madkour-publish-works.el:137`)
  - works-lint `--required` (`a3madkour-works-lint.el:52`)

  Hand-written converters bridge the spellings in research.el:214,
  works.el:148 and works-lint.el:143.
- **Field contracts.** Required, optional and enum sets live as module
  constants in the 7 `tools/check_*_fixtures.py` files. They are copied by
  hand into the elisp normalizers:
  - research statuses (`frontmatter.el:460`)
  - essay keys (`:235/:241`)
  - poetry keys (`poetry.el:165`)
  - library statuses and media (`library.el:24-36`)

  The same values are hard-coded a third time in `layouts/`.

**Prior art.** `data/works-vocab.json` already settles the approach: it is the
single copy of the games/music contract, read by
`tools/check_works_fixtures.py` and `a3madkour-works-vocab.el`. A missing file
is an error, never a fallback. This project generalises that file to every
section.

## 2. Goals and non-goals

**Goals**
1. One machine-readable field contract per section, read by the site linters
   and by the elisp, so the two cannot drift.
2. One elisp section registry that replaces the scattered section lists and
   the hand-written slash↔hyphen converters.
3. `a3-publish-mark` asks only for the values it cannot derive, and writes
   them.

**Non-goals.** These are queued as follow-up stubs (§9):
- a shared publish template for the handlers (C)
- dedup of the org table/subtree helpers (D)
- the `a3-pub.sh` bootstrap and its load lists (E)
- site Python dedup beyond what `check_fields` replaces (F)
- templates reading `site.Data.sections` (G)
- a generic links checker driven by `ref` types (part of F)

## 3. Architecture

Knowledge is split by who needs it.

| Lives in | Holds | Read by |
|---|---|---|
| site `data/sections.json` | Section names. Per-section fields: type, required, enum values, ref targets, prompt behaviour. Garden/library variants. | `tools/sections.py` → the 7 fixture linters; `a3madkour-sections.el` → normalizers, works-lint, `a3-publish-mark` |
| dotfiles `a3madkour-pub-registry` (one defconst in `a3madkour-publish.el` or a new `a3madkour-publish-registry.el`) | Per section: living or deliberate, handler function, content-dir or data-file config (library yaml file, default medium). | living/deliberate dispatch, frontmatter dispatch, author helpers |

The registry's section keys must equal the JSON's. A test pins this (§7).
Section names are stored once, in slash form. The hyphen symbol is derived by
one function, `a3madkour-pub-section/symbol`, and nothing else spells it.

`data/works-vocab.json` is folded into `sections.json` and deleted.
`a3madkour-works-vocab.el` is replaced by `a3madkour-sections.el`.

## 4. `data/sections.json` schema

```json
{
  "version": 1,
  "sections": {
    "<slash-name>": {
      "closed": true,
      "store": "frontmatter",
      "fields": { "<name>": { ...field spec... } },
      "variants": { "on": "<field>", "cases": { "<case>": { "values": [...], "fields": {...} } } }
    }
  }
}
```

**Section keys**
- `closed` (default `true`): unknown fields are errors. Essays are `false`,
  matching today's behaviour.
- `store`: `"frontmatter"` (default) or `"data"` (library: entries are items
  in a data yaml file, not page frontmatter).
- `variants`: optional. The case is chosen by the value of the `on` field.
  Each case lists the `values` of `on` that select it, and adds fields.
  - Garden uses this keyed on `media_type`: `concept` (field absent), `media`,
    `reference`.
  - Library uses it to vary `extras` sub-keys by `media_type`.

**Field spec keys**

| Key | Meaning |
|---|---|
| `type` | `text`, `int`, `bool`, `date`, `list`, `enum`, `ref`, `refs`, `object`, `structured` |
| `required` | Default `false`. |
| `values` | Enum only. The allowed values. |
| `to` | `ref`/`refs` only. The target section, which must exist in the file. |
| `default` | Preselected answer for `enum`/`bool` prompts. |
| `from` | `"pipeline"`: the publisher derives it (title, drawer dates, filetags, the has_math scanner). It is validated but never prompted. |
| `ask` | Optional field that `a3-publish-mark` offers anyway. |
| `fill` | `"today"` or `"next-weight"`: derived at mark time with no prompt. |
| `fields` | `object` only (library `extras`). Nested specs; variants may add to them. |

**Worked example**, research:

```json
"research/themes": {
  "fields": {
    "title":            {"type": "text", "required": true, "from": "pipeline"},
    "last_modified":    {"type": "date", "required": true, "from": "pipeline"},
    "tags":             {"type": "list", "required": true, "from": "pipeline"},
    "draft":            {"type": "bool", "from": "pipeline"},
    "author":           {"type": "text", "from": "pipeline"},
    "description":      {"type": "text", "required": true},
    "summary":          {"type": "text"},
    "status":           {"type": "enum", "required": true,
                         "values": ["active", "dormant", "answered"], "default": "active"},
    "weight":           {"type": "int",  "required": true, "fill": "next-weight"},
    "garden_topic_ref": {"type": "ref",  "to": "garden"},
    "source_stream":    {"type": "ref",  "to": "streams"}
  }
},
"research/questions": {
  "fields": {
    "theme":            {"type": "ref",  "to": "research/themes", "required": true},
    "parent_question":  {"type": "ref",  "to": "research/questions"},
    "supporting_notes": {"type": "refs", "to": "garden", "ask": true},
    "related_essays":   {"type": "refs", "to": "essays"},
    "started":          {"type": "date", "fill": "today", "ask": true},
    "outputs":          {"type": "structured"},
    "...": "plus title/last_modified/status/description/etc. as above"
  }
}
```

The real file lists every field in full. Nothing is inherited between
sections, so each entry reads on its own.

**Kept as code, not schema.** This bounds the file to a flat description of
fields:
- cross-field rules, e.g. `archive_status: archived` ⇒ `vod_url`;
- uniqueness of theme weights;
- `series` ↔ `series_order` coupling;
- `lyrics_poem` ↔ `set_to_music` symmetry;
- the inner shape of `structured` fields (ingredients, steps, sources,
  outputs, tracks, lines);
- format regexes (ISBN, slug, date).

**`forbidden` is dropped** from the Section 1 sketch. With `closed: true`, an
unlisted field is already an error. `THEME_FORBIDDEN`'s two keys are simply
absent from the themes entry. The error text keeps the linter's existing
`unknown field` wording.

## 5. Readers

### 5.1 Site — `tools/sections.py`
- `load(repo_root) -> dict` reads and validates the file. It fails closed if
  the file is missing or malformed, or on:
  - an unknown type or spec key;
  - `values` on a non-enum;
  - a `to` that names no section;
  - a `variants.on` that is not a field.
- `check_fields(fm, section_name, path) -> list[str]` checks required,
  closed-set, enum, type and variant selection. It emits messages in the
  existing linters' `"{path}: …"` shapes.
- Each `check_*_fixtures.py` deletes its field and enum constants and calls
  `check_fields`. Its cross-field and structured code stays.
- `check_library_fixtures.py` calls it per yaml item.
- `check_works_fixtures.py` drops `load_vocab`.

### 5.2 Dotfiles — `a3madkour-sections.el`
- Generalises `a3madkour-works-vocab.el`: reads the JSON at the site root,
  caches by mtime, and fails closed with no hard-coded fallback.
- API:
  - `a3madkour-sections/spec SECTION`
  - `a3madkour-sections/fields SECTION &optional VARIANT-CASE`
  - `a3madkour-sections/enum SECTION FIELD`
  - `a3madkour-sections/emitted-keys SECTION`
- It keeps the no-load-time-dependency property, so
  `a3madkour-publish-frontmatter` still loads under `emacs -Q`.
- Consumers switch over:
  - the normalizers' allowed-key filters and enum checks (research, essays,
    poetry, works, library);
  - `a3madkour-works-lint` rule 2;
  - `a3-publish-mark` (§6).

### 5.3 Dotfiles — the registry
- One defconst, keyed by slash name. Each entry has `:mode living|deliberate`,
  `:handler FN`, plus section-specific keys: library `:data-file`,
  `:default-medium`.
- It replaces every list in §1, including the living
  `with-eval-after-load` blocks. Handlers are named by symbol and resolved
  when called, which removes the load-order coupling.
- These are derived from it:
  - `a3madkour-pub/sections` (still including handler-less `streams`/`about`
    as `:mode nil`)
  - `a3madkour-pub-deliberate-sections`
  - the frontmatter dispatch
  - works `--sections`

## 6. `a3-publish-mark` flow

1. **Pick a section** (unchanged).
2. **Collect the fields to ask for.** That is every field that is not
   `from: pipeline`, is `required` or `ask`, and is absent from the buffer.
   - For garden, the variant case comes from the buffer's `media_type`; when
     that is absent the case is concept.
   - Library sections keep `a3-library-insert-item`/`-extras`; mark adds no
     prompts there in this project.
3. **Gather every value before writing anything.** A `C-g` mid-way leaves the
   buffer untouched.

   | Type | Input |
   |---|---|
   | `enum` | `completing-read`, require-match, preselects `default` |
   | `bool` | `y-or-n-p` with `default` |
   | `ref` | `completing-read` over published targets as "Title (slug)", storing the slug |
   | `refs` | `completing-read-multiple`; an empty answer skips an optional field |
   | `text` | `read-string`; a required field re-prompts on empty |
   | `fill: today` | today's ISO date, no prompt |
   | `fill: next-weight` | max existing weight in the section + 10 (10 if none), no prompt |
   | `structured` | not prompted; listed in the closing message if required |

   Published targets are the bundles under `content/<to>/*/index.md` in the
   site root, with titles read from their frontmatter.
4. **Write everything in one pass** via `a3madkour-pub-author--upsert-keyword`,
   so the drawer-first hoist from row 10 is kept.
   - `title`, `description` and `summary` map to `#+TITLE`,
     `#+HUGO_DESCRIPTION` and `#+HUGO_SUMMARY`. This is one small elisp alist,
     identical across sections.
   - Everything else is written as `#+HUGO_CUSTOM_FRONT_MATTER: :key value`;
     `refs` values become a space-separated list.
   - The `refs` round-trip through ox-hugo into a YAML list is verified in
     the plan's first step. It is unverified today: the example notes carry
     a single value.
5. **Idempotent.** A field already in the buffer is never prompted for or
   overwritten.
6. **Section change.** After the existing cross-section confirm, mark lists
   any fields that are not in the new section's set. It asks one `y-or-n-p`
   to remove them, then prompts for the new section's missing fields.

**Errors** (each is a `user-error` with nothing written):
- the JSON is missing or malformed (names the path);
- a required `ref` has no published targets ("publish a research/themes page
  first");
- the buffer is not in org-mode, or is read-only.

## 7. Testing

**Site (Python)**
- `tools/test_sections.py`:
  - every loader rejection in §5.1;
  - one test per `check_fields` rule: required, closed set, enum, type,
    variant selection, the variant `object` sub-keys;
  - the real `data/sections.json` loads cleanly.
- Every existing `test_check_*_fixtures.py` passes unchanged after its
  linter migrates.
- **Equivalence gate per migrated linter.** A throwaway scratchpad script runs
  the linter before and after over all fixtures plus a set of deliberately
  broken copies, and diffs stdout, stderr and the exit code.
  - Any difference is either fixed, or recorded in the commit message as an
    intended behaviour change.
  - The open-set essays case is the expected one.

**Dotfiles (ERT)**
- Reader tests, ported from the works-vocab tests:
  - fails closed;
  - the mtime cache invalidates;
  - `emitted-keys` matches the JSON.
- Registry tests:
  - every handler is fboundp after load;
  - slash→symbol is total and injective;
  - the derived `deliberate-sections` equals the `:mode deliberate` keys
    (the row 2 test keeps passing);
  - **cross-repo**: the registry key set equals `sections.json`'s key set.
- Mark tests stub `completing-read`, `completing-read-multiple`,
  `read-string` and `y-or-n-p` with `cl-letf`, over temp org buffers and a
  temp site root:
  - a theme gets status, description and the next weight;
  - a question picks a theme from the published set;
  - a second run asks nothing;
  - `C-g` mid-way changes nothing;
  - a required ref with no targets errors;
  - the drawer stays first;
  - a section change offers removal.
- The full suite stays green; it is 933 tests today.

**Mutation testing.** Break each guard and watch a test fail:
- the loader failing closed;
- each `check_fields` rule;
- the cross-repo key check;
- the gather-before-write atomicity;
- never-overwrite;
- the no-targets error.

**End-to-end.** This is the resumed research dogfood:
1. mark the user's real node as a theme and a question;
2. `a3-publish-living`;
3. the research linters pass;
4. Hugo builds;
5. a visual check of `/research/`, the theme page, the question page and
   `/research/graph/`;
6. `tools/ci-local.sh` passes (Playwright serial, per row 14).

## 8. Migration order

Each step is its own commit, green in both repos.
1. `data/sections.json` (all sections, transcribed from the current linter
   constants) + `tools/sections.py` + tests.
2. Migrate the linters one at a time, each through the equivalence gate.
   Order: research, streams, recipes, essays, garden, works (then delete
   `works-vocab.json` in the same commit as the elisp switch, step 4),
   library.
3. Dotfiles: `a3madkour-sections.el` + the registry + the derived lists. The
   dispatch switches over, with the old lists deleted in the same commit.
4. Dotfiles: the normalizers and works-lint read from `a3madkour-sections`.
   `a3madkour-works-vocab.el` and site `data/works-vocab.json` are deleted.
5. Dotfiles: the `a3-publish-mark` fill-in.
6. Log friction row 15 as resolved. Resume S1 research.

The dotfiles change in step 3 also updates `a3-pub.sh`'s `-l` lists for the
new modules (per the plan-wrapper rule). It does not restructure them; that
is E.

## 9. Follow-ups (queued as stubs, not built here)

- **C**: a shared publish-file template for the 6 per-file handlers, which
  repeat the same 8-step sequence.
- **D**: shared org AST helpers:
  - `--table-rows` ×3
  - `--find-table-under` ×2
  - strip-subtree ×3
  - lint `--kw` ×2
  - the library slugifier
- **E**: `a3-pub.sh`: 5 copies of the bootstrap and 5 diverging `-l` lists
  (71 loads); the cause of row 9.
- **F**: site Python dedup:
  - the slug-map loader ×5
  - the section walk and `main()` ×7
  - a generic ref checker from the `ref` types
  - **bug candidate:** the draft predicate is written 5 ways with different
    meanings (`streams_links.py:55` string-compares, the others use
    truthiness).
- **G**: templates read `site.Data.sections` instead of hard-coding:
  - garden media types ×8
  - research statuses ×3
  - library status chips ×4
  - growth stages

  This needs a visual check.
