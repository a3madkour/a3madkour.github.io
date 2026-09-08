# Recipe Slice 2 — Org authoring + lint + clean export

**Status:** Designed 2026-07-09 (brainstorm complete, approved). Ready for
`writing-plans`. Supersedes the Slice 2 stub in
`docs/superpowers/specs/2026-07-06-recipe-section-design.md` §Slice 2.

**Depends on:** Slice 1 (SHIPPED, `6d8cf4a`) — this slice produces, from org
source, exactly the Hugo bundle that Slice 1 already renders. It adds **no new
site rendering.**

**Where the code lives:** the handler + linter are **dotfiles elisp**
(`~/dotfiles/emacs-configs/custom/lisp/`), peers of the garden/library/research
publish handlers and of `org-math-lint`. The site repo is unchanged except that
the emitted bundles must keep passing the existing
`tools/check_recipes_fixtures.py` / `tools/check_recipes_links.py`.

## Context / why

Slice 1 shipped the visible recipe feature but its fixtures are hand-authored
YAML. Slice 2 is the authoring path the author explicitly deferred: write a
recipe in org-mode and publish it to the shipped frontmatter contract, with a
pre-publish linter that guarantees a clean, valid export every time.

The section spec's locked decisions hold: schema.org/Recipe is the interchange
standard (Slice 1 emits it); ingredients are authored as a structured org table;
steps are a list where adding a step = adding a list item, each optionally
carrying an `[mm:ss]` marker reusing the synced-poetry grammar.

## Prior-art research (2026-07-09) — what this builds on

- **org-chef** is the canonical Emacs recipe package: a level-1 heading + a
  `:PROPERTIES:` drawer (`source-url` / `servings` / `prep-time` / `cook-time` /
  `ready-in`) + `Ingredients` (plain list) and `Directions` (ordered list)
  subheadings. Its ingredients are **free-text strings**; its scaling command
  regex-matches leading numbers and is brittle on fractions/ranges. **We adopt
  its PROPERTIES-drawer idiom and reuse its key spellings where they overlap**
  (so a future org-chef import path stays trivial) **but reject its free-text
  ingredient list.**
- **Cooklang** has the right *data model* (typed `qty`/`unit`/`item`) but no org
  tooling — its inline `@item{qty%unit}` markup fights org's parser. We borrow
  the model (structured columns), not the syntax.
- **Structured ingredients in org**: the one established *computable* convention
  is an **org table**, one ingredient per row (emacs-otdb / nutrition setups),
  consumed via `org-table-to-lisp`. This is the pattern we build on.
- **Consuming an org table at export**: `org-table-to-lisp` returns rows as
  lists of **cell strings**, with `hline` symbols for rules. The handler must
  strip `hline` + the header row itself, and cast cells (empty cell → null).
  Org's own guidance for emitting a table to a non-table target is to write a
  translator function, not to rely on a built-in table exporter.

Sources: github.com/Chobbes/org-chef, cooklang.org/docs/spec,
github.com/akroshko/emacs-otdb, orgmode.org/manual/Tables-in-Arbitrary-Syntax.html.

## The authoring contract (org shape)

**One `.org` file per recipe** — garden-style per-file model (a recipe is a
standalone artifact, not a tiny aggregated row). The filename determines the
slug → `content/recipes/<slug>/index.md`.

```org
#+TITLE: Shakshuka
#+HUGO_SECTION: recipes
#+DATE: 2026-07-09
#+FILETAGS: :example:one-pan:
#+HUGO_SUMMARY: Eggs poached in a spiced tomato sauce — a fast one-pan dish.
:PROPERTIES:
:servings:    4
:yield-unit:  servings
:prep-time:   10
:cook-time:   25
:cuisine:     North African
:category:    Main
:video:       dQw4w9WgXcQ
:image:       hero.svg
:END:

A short headnote paragraph. This prose (everything before the first
`**` subheading) is exported as the page body.

** Ingredients
#+NAME: ingredients
| qty | unit | item      | group | note  | alt     |
|-----+------+-----------+-------+-------+---------|
|   2 | tbsp | olive oil | base  |       |         |
|   1 |      | onion     | base  | diced | shallot |
| 800 | g    | tomatoes  | sauce |       |         |
|     |      | salt      |       | taste |         |

** Steps
1. Heat the oil over medium.
2. Add the onion; cook until soft, ~5 min.
3. [02:30] Pour in the tomatoes; simmer 15 min.

** Sources
- [[https://example.com/lorem][Example Cooking — Lorem]] — adapted
- Example notebook
```

### Skeleton rules

- **Sectioned/explicit** (chosen over flat/convention-based): three fixed
  level-2 subheadings — `** Ingredients`, `** Steps`, `** Sources`. Order is not
  significant; the handler locates them by heading text.
- **Headnote** = all content before the first `**` subheading → exported as the
  page body via ox-hugo. The three subtrees carry structured data, not prose, and
  must NOT appear in the exported body.
- `** Ingredients` holds exactly one `#+NAME: ingredients` table.
- `** Steps` holds exactly one ordered list.
- `** Sources` holds exactly one plain list.

## Mapping org → frontmatter contract

The emitted frontmatter must satisfy `tools/check_recipes_fixtures.py`:
**REQUIRED** `title, date, lastmod, draft, summary, servings, sources,
ingredients, steps`; **OPTIONAL** `tags, cuisine, category, yield_unit,
prep_minutes, cook_minutes, total_minutes, image, video, outputs`.

| Frontmatter key | Source in org | Notes |
|---|---|---|
| `title` | `#+TITLE:` | required; ox-hugo native |
| `date` | `#+DATE:` | required; ox-hugo native; normalize defaults to `lastmod` if absent |
| `tags` | `#+FILETAGS:` | optional; ox-hugo maps filetags → `tags` list |
| `summary` | `#+HUGO_SUMMARY:` | required; read directly (ox-hugo has no native summary keyword — same as essays) |
| `servings` | `:servings:` | required; int > 0 |
| `yield_unit` | `:yield-unit:` | optional; default `"servings"` |
| `prep_minutes` | `:prep-time:` | optional int (org-chef spelling; value = minutes) |
| `cook_minutes` | `:cook-time:` | optional int |
| `total_minutes` | `:total-time:` or derived | optional; if absent and both prep+cook present, emit their sum |
| `cuisine` | `:cuisine:` | optional |
| `category` | `:category:` | optional |
| `video` | `:video:` | optional; bare YouTube id |
| `image` | `:image:` | optional; asset filename in the bundle |
| `lastmod` | `last-modified-cascade` | drawer → keyword → git-mtime → prior-recorded → fs-mtime → today (essays/P2.14 machinery) |
| `draft` | `#+HUGO_DRAFT:` / publish state | coerced to bool, default false (essays convention) |

**Standard fields (`title`/`date`/`lastmod`/`draft`/`summary`/`tags`) reuse the
essays normalize machinery** via a new `recipes` branch in
`a3madkour-publish-frontmatter.el`; the handler then **injects** the
recipe-specific keys (servings, ingredients, steps, sources, …) into the
normalized alist — exactly as the research handler injects `outputs`.
| `ingredients` | `** Ingredients` table | see below |
| `steps` | `** Steps` ordered list | see below |
| `sources` | `** Sources` list | see below |

### Ingredients (table → flow-style array)

Fixed columns `qty | unit | item | group | note | alt` (header row required).
Parse via `org-table-to-lisp`; drop `hline` rows and the header; per row:

- `qty` — empty cell → `null`; otherwise cast to number (int or float; fraction
  cells like `1/2` accepted and evaluated, matching Slice 1's scaler expectations).
- `unit` — empty → `null`.
- `item` — required non-empty string.
- `group`, `note`, `alt` — empty → key omitted from that entry.

Emitted as flow-style YAML (byte-compatible with Slice 1 fixtures):

```yaml
ingredients:
  - { group: "base", qty: 2, unit: tbsp, item: "olive oil" }
  - { group: "base", qty: 1, unit: null, item: "onion", note: "diced", alt: "shallot" }
  - { qty: null, unit: null, item: "salt", note: "to taste" }
```

### Steps (ordered list → string array)

Each list item's text → one `steps` string. A leading `[mm:ss]` (or `[mm:ss.ff]`)
is kept **verbatim** in the string — Slice 1 owns rendering/stripping and the
synced-video runtime (deferred 1c). Timecode grammar matches Slice 1's
`TIMECODE_RE` = `^\[(\d{1,2}):([0-5]\d)(?:\.\d{1,2})?\]`.

### Sources (list → object array)

Each list item is one of:
- `[[url][name]] — note` → `{ name, url, note }`
- `[[url][name]]` → `{ name, url }`
- `name — note` → `{ name, note }`
- `name` → `{ name }`

The `—` / ` -- ` separator introduces the optional note. `sources` is REQUIRED,
so `** Sources` with at least one item is mandatory.

## The handler — `a3madkour-publish-recipes.el`

Per-file handler, structural peer of `a3madkour-publish-garden.el`. Entry point
`a3madkour-pub-recipes/publish-recipe-file (file run &key on-done)`:

1. **Lint** the source via `a3madkour-recipe-lint/lint-file` (unless disabled);
   abort the file's publish on errors.
2. **Parse** the source with `org-element` — drawer/keyword metadata, then the
   `** Ingredients` / `** Steps` / `** Sources` subtrees' structured data.
3. **Export body** — strip the three data subtrees from a temp copy (reusing the
   `rewrite-to-tmp-file` pattern), then `a3madkour-pub-export/export-file` so only
   the headnote reaches the body.
4. **Normalize + inject** — run the standard fields through
   `a3madkour-pub-frontmatter/normalize 'recipes` (date/lastmod/draft/summary/tags),
   then inject the recipe-specific keys (servings, `ingredients`, `steps`,
   `sources`, …) into the normalized alist.
5. **Render** via a recipe `--render-frontmatter` wrapper: a **`key-hook`** emits
   the flow-style block sequences for `ingredients` / `sources` / `steps` verbatim
   (the mechanism the research handler uses for `outputs`); a handler-local
   flow-object renderer produces the `{ k: v, ... }` lines.
6. `a3madkour-pub/asset-validate-and-copy` the `:image:` → `write-if-different` →
   `record-publish` (state + stable `lastmod`).

Registration: add a `recipes` entry to the living-publish handler table
(`a3madkour-publish-living`) and `-l a3madkour-publish-recipes` to `a3-pub.sh`
(per the "plans update the wrapper script for new elisp modules" rule).

## The pre-publish linter — `a3madkour-recipe-lint`

Analog of `org-math-lint`: a3-pub.sh runs it **before** export (default-on;
`--skip-recipe-check` to bypass), failing fast with an **org `file:line`**
message instead of a cryptic YAML-shape failure surfacing later in site CI.

Rules (each reports file:line):

1. `** Ingredients` and `** Steps` subheadings present; `** Sources` present with
   ≥1 item (all feed REQUIRED fields).
2. `#+NAME: ingredients` table present under `** Ingredients` with the required
   header columns `qty unit item group note alt` (extra columns rejected).
3. Every ingredient row: `qty` numeric-or-empty; `item` non-empty.
4. Every step timecode (if present) matches `TIMECODE_RE`.
5. `:video:` (if present) is a bare YouTube-id shape (`[A-Za-z0-9_-]{11}`).
6. Required metadata present: `#+TITLE:`, `#+HUGO_SUMMARY:`, `:servings:` (int > 0).

Non-goals for the linter: it validates authorability, not schema.org semantics —
the emitted-YAML shape is still backstopped by `check_recipes_fixtures.py` /
`check_recipes_links.py` in site CI.

## Testing

- **ert** (dotfiles): parse → golden frontmatter for a representative recipe
  (all field types, nullable qty, grouped + ungrouped ingredients, a `[mm:ss]`
  step, mixed source forms); the linter's rules each get a red + green case.
- **Round-trip acceptance**: publish a real org recipe from the authoring dir →
  the emitted `content/recipes/<slug>/index.md` passes
  `check_recipes_fixtures.py` + `check_recipes_links.py` and renders correctly on
  `hugo server` (ingredients rail, scaler, steps, sources, JSON-LD, `.json`
  download).
- Site fixtures stay hand-authored dummies (the site's fixture rule); the real
  exported recipe lives in the author's org dir, not in the repo.

## Scope boundaries

- **In:** org authoring shape, the `a3madkour-publish-recipes.el` handler, the
  `a3madkour-recipe-lint` pre-publish linter, ert + round-trip tests, a3-pub.sh
  wiring.
- **Out:** synced-video *rendering* (deferred slice 1c — Slice 2 only carries
  `video` + `[mm:ss]` through as data); the meal-prep planner (Slice 3, a
  separate stateful project); any change to Slice 1's site rendering.

## Locked decisions (this slice)

1. Single `#+NAME: ingredients` org table with a `group` **column** (not
   per-group subheading tables).
2. Sectioned/explicit skeleton: `** Ingredients` / `** Steps` / `** Sources`.
3. Sources authored as an org link list under `** Sources`.
4. org-chef PROPERTIES idiom + overlapping key spellings; site-native keys for
   the rest.
5. Full org-side pre-publish linter (`a3madkour-recipe-lint`), a3-pub.sh-invoked,
   default-on with `--skip-recipe-check`.
6. No new site rendering; emitted bundle is byte-compatible with the Slice 1
   contract.
