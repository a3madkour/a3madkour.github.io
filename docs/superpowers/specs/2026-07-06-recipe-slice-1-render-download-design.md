# Recipe section — Slice 1 (render + download) design

**Status:** Designed 2026-07-06 (brainstorm + visual companion). Slice 1 of the
recipe feature; parent decomposition in `2026-07-06-recipe-section-design.md`.
Ready for an implementation plan. Visual decisions were validated in the browser
companion; the mockups persist under `.superpowers/brainstorm/*/content/`
(`recipe-layout-styled.html`, `recipe-scaling-dual-v2.html`, `recipe-index.html`).

## Scope

Slice 1 = the site's **consume + contribute** side: render a standard-format
recipe minimally in the house style, list its **sources** (req 1), offer a
**download** in the standard format (req 3), and provide client-side **portion
scaling** (req 6). Explicitly out: synced-video steps (req 4 → later slice 1c),
org authoring/export (slice 2), meal-prep planner (slice 3), nutrition info, and
unit conversion.

## The standard

**schema.org/Recipe, serialized as JSON-LD, is the one standard.** It is the
render model, the `<head>` structured-data block (the site's first JSON-LD), and
the download payload — one canonical object.

**Download = "standard + structured extension" (Option 2).** The emitted object
is a valid schema.org/Recipe with `recipeIngredient` as clean free-text strings
(what Google + the ecosystem expect). Because schema.org has no structured
qty/unit ingredient field, the structured ingredient data (needed for scaling and
the future meal-prep project) rides along under a namespaced, consumer-ignored key
`x-ingredients`. Standard consumers read a normal recipe; our tools read the
structure. `<head>` JSON-LD and the download file are generated from the same
template partial (DRY).

## Data model — two layers

### Authoring layer — Hugo page bundle frontmatter

`content/recipes/<slug>/index.md`:

```yaml
title: "Weeknight Shakshuka"
date: 2026-07-06
lastmod: 2026-07-06
draft: false
summary: "Eggs poached in a spiced tomato sauce."     # cards + <meta> + description
tags: [breakfast, eggs, one-pan]
cuisine: "North African"        # → recipeCuisine
category: "Main"                # → recipeCategory (Breakfast/Main/Side/Dessert…)
servings: 4                     # base yield; the number scaling multiplies
yield_unit: "servings"          # label; default "servings" (e.g. "cookies", "1 tray")
prep_minutes: 10                # → PT10M
cook_minutes: 25                # → PT25M; total = prep+cook unless total_minutes set
image: "hero.svg"               # optional bundle asset (hand-authored placeholder)
video: ""                       # optional YouTube id — carried, UNUSED in slice 1 (slice 1c)
sources:
  - name: "NYT Cooking — Shakshuka"
    url: "https://cooking.nytimes.com/…"    # optional
    note: "adapted"                          # optional
  - name: "Grandma's notebook"
ingredients:
  - { qty: 2,    unit: tbsp, item: "olive oil" }
  - { qty: 1,    unit: null, item: "onion", note: "diced", alt: "shallot" }
  - { qty: 800,  unit: g,    item: "canned tomatoes" }
  - { qty: 4,    unit: null, item: "eggs" }
  - { qty: null, unit: null, item: "salt", note: "to taste" }   # unscalable
  # optional: { group: "For the sauce", qty: …, … } to render sub-headed sections
steps:
  - "Heat the oil in a wide pan over medium heat."
  - "Add the onion; cook until soft, about 5 minutes."
  - "[02:30] Pour in the tomatoes; simmer 15 minutes."   # leading [mm:ss] optional, STRIPPED in slice 1
# body (below frontmatter) = optional headnote / notes prose
```

**Field contract** (enforced by `check_recipes_fixtures.py`):

| Field | Req? | Type / rule |
|---|---|---|
| `title`,`date`,`lastmod`,`draft`,`summary` | required | site-standard |
| `servings` | required | number > 0 |
| `ingredients` | required | non-empty list of objects (see below) |
| `steps` | required | non-empty list of strings; optional leading `[mm:ss]` (synced-poetry grammar) |
| `sources` | required | list of `{name (req), url?, note?}` |
| `tags` | optional | list of strings |
| `cuisine`,`category`,`yield_unit` | optional | strings (`yield_unit` default "servings") |
| `prep_minutes`,`cook_minutes`,`total_minutes` | optional | non-negative ints |
| `image`,`video` | optional | strings (bundle asset / YouTube id) |

**Ingredient object:** `item` (req, string); `qty` (number **or** absent/null →
unscalable); `unit` (string or null); `alt` (optional string); `note` (optional
string); `group` (optional string — sub-heading).

### Standard layer — emitted schema.org/Recipe

| schema.org | From |
|---|---|
| `name` | `title` |
| `description` | `summary` |
| `image` | `image` (if present) |
| `recipeYield` | `"{servings} {yield_unit}"` |
| `prepTime`/`cookTime`/`totalTime` | minutes → ISO-8601 (`PT10M`, `PT1H30M`) |
| `recipeCuisine`/`recipeCategory`/`keywords` | `cuisine`/`category`/`tags` |
| `recipeIngredient` | each ingredient flattened to text at **base servings** (`"2 tbsp olive oil"`, `"1 onion, diced"`, `"salt, to taste"`) |
| `recipeInstructions` | `HowToStep[]`, `.text` = step (leading `[mm:ss]` stripped) |
| `isBasedOn` / `author` | `sources` (url-bearing → `CreativeWork{name,url}`; others → text) |
| `datePublished`/`dateModified` | `date`/`lastmod` |
| `x-ingredients` *(extension)* | the structured ingredient objects verbatim |

Only `name` + `image` are Google-required; the rest are recommended and emitted
when present.

## Single recipe page — layout

Chosen: **two-column (layout B), collapsing to single-column** at the narrow
breakpoint (canonical `720`; verify at the author's ~960 half-screen). Structure
top-to-bottom / left-to-right:

- **Header:** kicker `cuisine · category` (Inter, uppercase, ink-fade); title
  (Petrona 700); italic headnote (`summary` / body first line, ink-soft); meta
  row `Prep · Cook · Total`; **Download pill** (bordered burgundy, Inter,
  "⬇ Download recipe (.json)").
- **Ingredients rail** (`--color-tile` card, `--color-rule` border, **sticky**):
  the scaler control + the ingredient list. Sits left, ~40–42% width.
- **Steps column** (right): numbered list, burgundy circle markers.
- **Sources** (req 1): full-width below, a list; source names link (burgundy
  underline) when `url` present, `note` in faded italic.

No-JS: server renders base-serving quantities and the full page; scaling is a
progressive enhancement.

## Portion scaling (req 6)

Client-side, in `entry-recipes.js`. The single page renders a
`<script type="application/json">` **data island** in the ingredients rail
carrying the structured ingredient objects; the scaler reads that (one mechanism —
the same structured array the download emits as `x-ingredients`), rewrites the
rendered quantities, and leaves the server-rendered base values as the no-JS
fallback.

- **Two synced inputs** in the rail: a **Serves** stepper (editable number input +
  `–`/`+`) on the left, and a **multiplier** field (`×`, editable, subtler
  dashed-underline styling) pushed to the right. Typing either updates the other
  and all quantities. Ratio `r = servings / base`.
- **Unit-aware number formatting:**
  - weight/volume metric (`g`, `ml`) → round to integer; `kg`, `l` → 1 decimal.
  - counts (no unit), `tsp`, `tbsp`, `cup`, `oz`, `lb`, and default → nearest
    **1/8** as a unicode vulgar fraction / mixed number (`1` → `1½` at ×1.5).
  - Vulgar map `⅛ ¼ ⅜ ½ ⅝ ¾ ⅞`.
- **`qty: null` never scales** ("to taste", "a handful") — item + note verbatim.
- **Alternatives** render inline: `1 onion, diced (or shallot)`.
- **Optional groups** render as ingredient sub-headings.
- Scaled quantities get a **burgundy highlight** (value change is the primary
  signal; color is supplementary, not sole meaning — a11y).
- **Out of scope:** unit conversion (`3 tsp`→`1 tbsp`). Quantities scale within
  their authored unit.

## Download + JSON-LD (req 3)

- A **Hugo custom output format** (`RecipeJSON`, media type `application/ld+json`,
  base name `index` → `<slug>/index.recipe.json` or similar) is enabled for the
  recipes single page kind, emitting the schema.org/Recipe object.
- A shared partial `partials/recipes/schema-recipe.html` renders that object; it
  is called by **both** the output-format template **and** the `<head>` JSON-LD
  `<script>`. One source of truth.
- The **Download pill** links to the JSON output's permalink with a `download`
  attribute — no client-side serialization needed.

## Index page — `/recipes/`

Chosen: **simple uniform card grid** (not the bento, not the library umbrella).

- Header: "Recipes" (Petrona) + italic lede.
- **Filter strip** via the shared `partials/filter-chips.html`: dimensions
  **Cuisine / Course / Time** (bucketed: `≤30 min`, `≤1 hr`) + **tags** (in the
  secondary `<details>` disclosure). AND-composition, per the existing convention.
  Time bucket derives from `total_minutes`.
- **Cards** (`--color-tile`, burgundy hover border): kicker (`cuisine · course`),
  title, one-line summary, footer (`⏱ total time` + `yield`).

## Cross-cutting wiring

- **Nav:** add **Recipes** to the top nav (currently Essays / Garden / Research /
  Works / Library / Streams / About). *Proposed position: after Streams, before
  About.* (Nav is otherwise locked — confirm placement with author.)
- **Content section:** `content/recipes/` with `_index.md`; layouts
  `layouts/recipes/{list,single}.html` + the `RecipeJSON` output template;
  partials under `layouts/partials/recipes/` (`schema-recipe.html`, card, rail,
  scaler, sources).
- **JS bundle:** new `assets/js/entry-recipes.js` → `recipes.<hash>.js`, loaded on
  `.Section == "recipes"` (registered in `layouts/partials/scripts.html`). Bundles
  the scaling runtime (`assets/js/recipe-scale.js`) + `filter-chips.js` (index).
- **CSS:** new numbered section **§50** in `assets/css/main.css` (recipe single +
  index + scaler chrome). Uses existing tokens + the `--space-*` scale.
- **Search:** per-layout Pagefind meta — `section:recipes` + `cuisine`,
  `category` filters; add "Recipes" chip to the search modal.
- **Fonts/colors:** existing tokens only; no new palette (contrast already covered
  — burgundy/stone is an AA-checked pairing).

## Fixtures + linters

- **Fixtures:** hand-authored **obviously-dummy** recipes under `content/recipes/`
  ("Example Recipe One", dummy items) — but with **real numeric qty/unit** so
  scaling + JSON-LD are exercised. Include: a grouped-ingredients recipe, a
  `qty: null` "to taste" case, a source with+without url, a step with a `[mm:ss]`
  marker, and a no-`video` recipe. This fixture set **is** the contract slice 2's
  org exporter must satisfy.
- **`check_recipes_fixtures.py`** (34th linter pair): the frontmatter contract
  above — required keys, ingredient/step/source object shapes, `servings > 0`,
  minutes non-negative ints, `[mm:ss]` grammar when present.
- **`check_recipes_links.py`** (35th pair): source `url` well-formedness
  (`https?://`), `video` id shape, and any optional internal cross-refs
  (`related_essays`/`related_garden`) resolve to non-draft fixtures.
- **Post-build JSON-LD validity** folds into the existing `check_smoke`/built-page
  checks: assert each `/recipes/<slug>/` emits a parseable `application/ld+json`
  Recipe and a reachable download `.json`.

## Accessibility

- Scaler inputs carry `aria-label` (servings / multiplier); `–`/`+` are labeled
  buttons.
- Scaled-quantity signal is the **changed number**; burgundy is supplementary
  (never color-only meaning — spec §1 constraint).
- Semantic `<ol>` steps, `<ul>` ingredients/sources; sticky rail is not a focus
  trap.
- Contrast: burgundy/stone (AA) already verified by `check-contrast.py`.

## Tests

- **E2E (Playwright):** a `recipes` smoke spec — recipe page renders ingredients +
  steps; typing a new serving count rescales at least one quantity; the download
  link resolves to a JSON Recipe; index filter chips filter cards. Extends the
  existing `tests/e2e/` suite (gates deploy).
- **Linter unit tests:** `test_check_recipes_fixtures.py` + `test_check_recipes_links.py`.

## Out of scope (slice 1)

Synced-video steps (slice 1c — the `[mm:ss]` data + `video` id are carried now so
the model is stable), org authoring/export (slice 2), meal-prep planner (slice 3),
nutrition info, unit conversion, recipe ratings/reviews.

## Open questions (small — for plan kickoff)

1. **Nav placement** of "Recipes" (proposed: after Streams). Author confirm.
2. **Card thumbnails** on the index — text-only cards (current mock) vs. an
   optional `image` thumbnail slot. Lean text-only for launch; image optional.
3. **`total_minutes`** — always compute from prep+cook, or allow an explicit
   override (for "+ overnight rise" cases)? Lean: allow optional override.
