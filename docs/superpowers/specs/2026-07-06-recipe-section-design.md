# Recipe section — design STUB

**Status:** STUB filed 2026-07-06 from a brainstorm. Captures the vision, the
interchange standard (researched), the three-slice decomposition, and the locked
decisions. **No slice is designed to implementation depth yet** — each slice below
gets its own focused brainstorm → spec → plan in a future session. Do not implement
from this file.

## Context / why

The author wants a place to share recipes with people. The guiding constraints from
the brainstorm: (1) list where each recipe comes from (sources/attribution);
(2) stay minimal and consistent with the rest of the site; (3) let someone download
the recipe in a **standard** format; (4) optional follow-along YouTube video with
steps synced to timestamps; (6) adjust portions + show ingredient alternatives;
(7) collect recipes into a meal-prep plan that aggregates ingredients.

The key architectural move: **the recipe is a portable standard artifact, not
something locked inside the site.** The site is one consumer/contributor of that
artifact; a future separate project (the meal-prep planner) is another. The standard
is the seam between them.

## The seam: interchange standard (researched 2026-07-06)

**schema.org/Recipe, serialized as JSON-LD, is the interchange format.** It is the
real, dominant web standard (Google Rich Results consume it), it is JSON, and it
natively expresses almost everything wanted:

- `recipeYield`, `recipeIngredient`, `recipeInstructions` (as ordered `HowToStep`s),
  `prepTime`/`cookTime`/`totalTime` (ISO-8601 durations), `nutrition`, `author`,
  `datePublished`, `recipeCuisine`/`recipeCategory`/`keywords`.
- **Video sync (req 4) is standard-native:** each `HowToStep` can carry a `video` /
  `Clip` with a `startOffset` (seconds into the video) — the canonical way to encode
  "step N starts at mm:ss." Maps directly onto the site's existing `[mm:ss]` marker
  convention.
- **Download (req 3) = serialize this object.** The same JSON-LD block emitted into
  the page `<head>` (free SEO rich-results — the site emits no JSON-LD today, this
  would be the first) is what the "Download recipe" button hands back.

**Known wrinkle for the authoring slice:** `recipeIngredient` is an array of
**free-text strings** ("2 cups flour") — schema.org has no structured qty/unit field.
Reliable portion scaling (req 6) and downstream ingredient aggregation (req 7) need
structured ingredient data (qty / unit / item / alt) carried **alongside** the
standard field. Resolving how to encode that while emitting valid schema.org is core
to Slice 2 (candidates: a companion structured block in the page data, or a
schema.org extension / `additionalProperty`).

Cooklang was considered and rejected as the interchange target — it is an *authoring*
markup, not a consumer-facing standard, and diverges from the org pipeline. It may
still inform Slice 2's authoring ergonomics (see research task).

## Decomposition — three slices

### Slice 1 — Recipe section on the site (render + download)  · *design next*
The visible feature. A `content/recipes/` section that consumes a standard-format
recipe and renders it minimally in the house style:
- Sources list (req 1) always shown.
- "Download recipe (.json)" button = the export (req 3); JSON-LD in `<head>`.
- Steps as a numbered list, each optionally carrying an `[mm:ss]` marker; the
  synced-YouTube runtime (req 4) and per-page portion scaling (req 6) are follow-on
  enhancements layered on the same data, not required for the first render.
- Frontmatter contract + `check_recipes_fixtures.py` / `check_recipes_links.py`
  linter pair; nav entry; filter chips.
- **Fixtures = hand-authored dummy recipes** in the standard format (obviously-dummy
  per the site's fixture rule) — Slice 1 does not depend on Slice 2 shipping.

### Slice 2 — Org authoring + lint + clean export  · *brainstorm-later, research-gated*
How a recipe is authored in org and exported to the standard format. **This is the
follow-up the author explicitly asked to defer.** Before designing:
- **Research task:** survey what org offers out of the box for recipes — org tables,
  structured property drawers, any existing org recipe packages, Cooklang-for-org,
  etc. There may be prior art to build on rather than inventing syntax.
- Then design: the authoring convention (target ergonomics — **adding a step should
  be as easy as adding a list item**; ingredients as an **org table** →
  qty/unit/item/alt); a publish handler in the dotfiles pipeline
  (`a3madkour-publish-recipes.el`, peer of the garden/library/research handlers)
  that emits the Hugo bundle **and** the schema.org/Recipe JSON + structured
  ingredients; and a linter guaranteeing a **clean, valid export** every time.
- Resolves the structured-ingredient wrinkle above.

### Slice 3 — Meal-prep planner  · *deferred, separate project*
The stateful "both consumer and contributor" project (req 7). Consumes the
downloadable standard-format recipes, lets someone assemble a plan across recipes,
and aggregates ingredients into a shopping list. This is app-like (persistent
client-side state) and is deliberately **outside** the static-site design. The
site's garden path-log already demonstrates the multi-page `localStorage`
accumulation pattern it would reuse. Not scoped here.

## Locked decisions

- Interchange standard: **schema.org/Recipe** as JSON-LD (render source, `<head>`
  block, and download payload — one canonical model).
- Ingredients authored as an **org table** (structured qty/unit/item/alt) so scaling
  and aggregation are deterministic, not fuzzy free-text parsing.
- Steps: numbered list, each optionally prefixed with **`[mm:ss]`**, reusing the
  synced-poetry timestamp grammar so video-sync comes almost for free.
- Minimal house-style render; **sources always listed**; the download button IS the
  export.
- Meal-prep aggregation is a **separate project**, not part of this feature.

## Reuse map (confirmed 2026-07-06 exploration)

- **Synced-poetry runtime** (`assets/js/poem-synced.js`, `entry-poetry.js`) — the
  media-agnostic reveal/seek engine; adaptable to sync recipe steps to a YouTube
  `currentTime` instead of audio. Basis for req 4.
- **Streams YouTube embed** (`assets/js/streams.js`,
  `layouts/partials/streams/embed.html`) — privacy-enhanced click-to-load iframe
  (`youtube-nocookie.com`). The player-load pattern for req 4.
- **Library umbrella + shelves** (`layouts/library/`, `data/library-*.yaml`, CSS §44)
  — the collection-index pattern (hero + themed shelves + catalogue) for `/recipes/`.
- **Explorables runtime** (`assets/js/explorables/`, `widget` shortcode, CSS §49,
  ReactiveValue/Chart) — the per-page interactive-widget pattern for req 6 scaling.
- **Citations** (`data/citations.yaml`, `cite` shortcode, `check_citations.py`) —
  the attribution/sources model for req 1.
- **Filter chips** (`assets/js/filter-chips.js`, `partials/filter-chips.html`) —
  section-index filtering.
- **Section linter pair pattern** (`tools/check_streams_fixtures.py` +
  `check_streams_links.py`) — the frontmatter-contract + link-resolution gate.
- **Garden path-log** (`assets/js/garden-history.js`, `localStorage` w/ consent gate)
  — the cross-page accumulation pattern for Slice 3.
- No existing recipe work; no JSON-LD anywhere yet (Slice 1 adds the first).

## Explicitly NOT decided here (for the future slice sessions)

Slice-1 layout/wireframes (ingredient panel, scaling control, synced-step list),
exact frontmatter keys, the structured-ingredient encoding, the org authoring grammar,
nav placement/label, and whether req 4 / req 6 ship with Slice 1 or as follow-ons.
