# Recipe audit remediation — design

**Date:** 2026-09-07
**Branch:** `recipes` (rebased onto `main`, 26 commits ahead)
**Trigger:** a `max`-effort code review of the full 25-commit recipe diff, run after
the rebase and before merge. 15 confirmed findings, each with an empirical
reproduction, plus ~15 verified runners-up.
**Predecessor:** `docs/superpowers/specs/2026-07-03-audit-remediation-roadmap.md`
(R1–R6.3, fully closed). This document uses the same row-ID convention with an
`RC` prefix.

---

## 1. Why this exists

The recipe work (Slice 1 render/download, Slice 2 org authoring) shipped green:
35 linter pairs, `node --test`, 16 Playwright tests, a production Hugo build, and
a full org→ox-hugo→Hugo end-to-end run. None of that caught the defects below,
for three structural reasons worth stating because they shape the fix:

1. **The content fixtures are all maximal.** All three shipped recipes carry
   tags, times, and url-bearing sources. Every optional-field path in the
   templates is therefore unexercised by the build, even though the *linter's*
   canonical VALID fixture is deliberately minimal — the two disagree about what
   a legal recipe looks like, and only the linter's view is tested.
2. **The local test environment diverges from CI.** `node --test` passes on the
   author's Node 26 via ESM auto-detection and fails on CI's pinned Node 20.
   `tools/ci-local.sh` mirrors CI step-for-step but not runtime-for-runtime.
3. **New chrome landed outside the reach of existing gates.** The contrast gate
   checks pairings against `--color-stone`; the recipe rail is `--color-tile`.
   The nav regression starts just below 960px, the one width documented as the
   manual check.

The remediation therefore pairs each fix with a guard aimed at the *class*, not
the instance.

## 2. Decisions

Four forks were settled during brainstorming. They govern the rows in §3.

### 2.1 Absence is a template problem; malformed values are a linter problem

The linter marks `tags`, `prep_minutes`, `cook_minutes`, `total_minutes` OPTIONAL
while the templates render them unconditionally. Rather than move fields between
REQUIRED and OPTIONAL — which would break the frontmatter contract
`a3madkour-publish-recipes.el` emits — the fix splits by failure kind:

- **Absent** → the template guards. The time meta line renders only when at least
  one of the three fields is present; `schema-recipe.html` omits the
  corresponding JSON-LD keys entirely rather than emitting `PT0M`; `card.html`
  gains the `| default slice` idiom used by every other card partial.
- **Malformed** → the linter rejects. Zero-padded integers, `1_0`, `inf`, `nan`,
  and the string `"null"` standing in for an absent value are all caught before
  Hugo ever sees them.

REQUIRED/OPTIONAL membership does not move. Slice 2's exporter needs no changes —
verified: `a3madkour-publish-recipes.el:201-203` already emits
`prep_minutes` / `cook_minutes` / `total_minutes`, matching the linter. The
`prep_time` / `cook_time` names in CLAUDE.md are documentation drift only.

### 2.2 The server render is authoritative at rest

`fromServings()` currently runs at load, so a second formatter rewrites every
server-rendered quantity at ratio 1: `0.5 tsp` visibly flips to `½ tsp` after
paint, and a JS-off reader permanently sees a different string than a JS-on one.

The authored string stands until the reader actually scales. `apply()` is skipped
at ratio 1. `formatQuantity` gains a floor so a scaled-down value never renders
`0` — below the fraction table's resolution it falls back to two significant
digits. Unit downshifting (`0.04 kg` → `40 g`) was considered and deferred: it
needs a conversion table, its own linter coverage, and is properly its own slice.

### 2.3 Nav repairs, it does not redesign

Below the canonical `1100px` breakpoint, nav font-size and gap drop one step so
all eight items hold a single row past 860px, down to roughly 760px; below that
the header wraps to two rows exactly as seven items already did. No markup
change, no new breakpoints outside the documented `480/600/720/960/1100/1280`
scale, every destination stays one click away. An overflow `<details>` and a
deliberate two-band header were both considered and rejected as redesigns of what
the header *is*, which is not what a regression fix should buy.

### 2.4 A rescaled quantity signals twice, in two channels

Today the only signal is burgundy text: color-only meaning (against the spec's
hard constraints), at 3.78:1 in dark mode, on a background the contrast gate
never checks, with no announcement at all. The fix uses both available channels
because the two defects are different:

- **Which values moved** → a dotted underline alongside the color, on a class
  renamed `.changed` → `.recipe-q-changed` so the css-refs allowlist stops
  whitelisting a bare `changed` token site-wide.
- **By how much, and say it out loud** → a `role="status"` line in the rail:
  "Scaled ×1.5 — amounts shown for 6 servings".

## 3. Rows

### T1 — Build & deploy blockers

| # | Row | Fix |
|---|---|---|
| RC1.1 | `package.json` has no `"type": "module"`; `node --test` fails on CI's pinned Node 20 (ESM auto-detection only defaults on at 22.7) and blocks deploy | Add `"type": "module"` and `"engines": {"node": ">=20"}`; run the unit step as `node --no-experimental-detect-module --test` in both CI and `ci-local.sh` so Node-20 module semantics are exercised regardless of local runtime |
| RC1.2 | `card.html:5` — `delimit .Params.tags " "` without `\| default slice`; a tagless recipe aborts the Hugo build | Adopt the idiom used by `essay-card.html:14`, `garden/note-tile.html:16`, `streams/stream-card.html:9`, `works/*`, `library/row.html:5` |
| RC1.3 | `check_recipes_fixtures.py` accepts values Hugo mis-parses: `010` → octal 8, `08` → build failure; `_is_num` accepts `1_0`/`inf`/`nan`; explicit `null` arrives as the truthy string `"null"`, so the `item` and `sources[].name` checks can never fire | Reject zero-padded integers for `servings`/`prep_minutes`/`cook_minutes`/`total_minutes`; tighten `_is_num`; treat `"null"` as absent the way the `qty` check at line 74 already does |
| RC1.4 | `card.html:7` — `<h3>` directly under the page `<h1>` trips axe `heading-order`; `gen_lhci_urls.py` now puts `/recipes/` behind an `accessibility: minScore 0.9` deploy gate | `<h3>` → `<h2>`, update the dependent CSS selectors |

### T2 — Wrong output on the shipped fixture

| # | Row | Fix |
|---|---|---|
| RC2.1 | `search.js:6` — `SECTION_ORDER`/`SECTION_LABEL` never learned `recipes`, so the renderer drops every recipe hit while `total` still counts it: "5 results in 79ms" over an empty pane, and recipes silently inflate the All count | Add `recipes` to both maps |
| RC2.2 | `rail.html:20` — the group heading fires only on a truthy, changed `group` and nothing closes an open group, so trailing ungrouped items inherit the previous heading (`salt` renders inside "For the sauce" in the shipped fixture). Separately, group headings are bare `<li>`s, announced as ingredients | Render each group as a heading plus its own `<ul>`, with ungrouped items in an unheaded list; preserve `data-i` indices so the scaler's DOM contract holds |
| RC2.3 | `schema-recipe.html:26` — `{{ with .url }}` gates the whole `isBasedOn` append, so a source with a name but no URL vanishes from the download and the JSON-LD; `example-recipe-two`'s only source (a book) is absent entirely, while the page credits it | Append a `CreativeWork` with `name` always, `url` when present |
| RC2.4 | `rail.html:3` — `<label>Serves` encloses the minus button, so the button is its labeled control; clicking the word "Serves" decrements and rescales, and the input has no programmatic label matching its visible text (WCAG 2.5.3) | Non-wrapping `<label for>` bound to the input by id |
| RC2.5 | `entry-recipes.js:56` — the load-time rewrite (§2.2), plus `formatQuantity` rounding `0.25 g` and `0.04 kg` to `0` | Skip `apply()` at ratio 1; add the two-significant-digit floor |
| RC2.6 | `entry-recipes.js:31` — the servings clamp is never written back (typing `100` yields servings-for-100 with amounts-for-99) and `fromMult` ignores its own `min`/`max` entirely; `min="0.1"` with `step="0.25"` is a permanent `stepMismatch` | Normalize on `change` in both directions, writing the clamped value back to the field; `step="any"` |
| RC2.7 | `single.html:12-19`, `card.html:1,10`, `schema-recipe.html:7,34-36` — all three time fields are OPTIONAL in the linter but rendered unconditionally, so a linter-valid recipe ships "Total 0&nbsp;min" and `"prepTime":"PT0M"`; Google Rich Results rejects zero-length durations and drops the whole Recipe result | §2.1: render the meta line only when at least one time field is present, and omit the JSON-LD keys entirely rather than emitting `PT0M` |

### T3 — Layout & accessibility

| # | Row | Fix |
|---|---|---|
| RC3.1 | `header.html:12` — the 8th nav item wraps the header to two rows at ≤860px (144px vs 96px) and three rows at 700px, on all 139 pages | §2.3: step down nav font-size and gap below `1100px` |
| RC3.2 | `main.css:5978` — the 720px collapse gives the rail `width: 100%` but not `.recipe-steps-col`, which shrink-wraps to 392.5px against a 660px rail at a 700px viewport | Add `.recipe-steps-col { width: 100% }` to the 720px block |
| RC3.3 | `main.css:5842`/`5874` set `outline: none` at `:focus` (out-specifying the global `:focus-visible` ring) with a 1.13:1 background swap as the only replacement; `.recipe-stp { overflow: hidden }` (`:5817`) clips the UA ring on both stepper buttons, which have no author focus style | Restore a real ring on all four controls; stop clipping the steppers |
| RC3.4 | `main.css:5912` — color-only rescale signal at 3.78:1 dark on `--color-tile`, with no announcement | §2.4: rename to `.recipe-q-changed`, add the dotted underline, add the `role="status"` scale line |

### T4 — Hygiene, doc drift, config

| # | Row | Fix |
|---|---|---|
| RC4.1 | `hugo.yaml:30` — the new `application/ld+json` media type claims suffix `json`, changing how `/lhci-pages.json` is served | `mediaType: application/json`; output is byte-identical |
| RC4.2 | `schema-recipe.html` leaks a non-schema.org `x-ingredients` key into public JSON-LD — a third copy of the ingredients per page | Drop it |
| RC4.3 | Valueless `download` attribute names every downloaded file `index.json` | `download="<slug>.json"` |
| RC4.4 | `layouts/recipes/list.html:52` — `#recipe-empty` dropped the `role="status"` both sibling implementations carry (`works/list.html:70`, `filter-chips.html:95`) | Restore it |
| RC4.5 | With JS off, the scaler is fully operable-looking chrome that does nothing | `<noscript><style>.recipe-scaler{display:none}</style></noscript>`, following the `head.html:65` precedent |
| RC4.6 | `image` is never validated — not shape, not existence — and is never rendered to a human, so breakage is invisible | Validate in `check_recipes_links.py`: absolute URL, or a bundle-relative file that exists |
| RC4.7 | `qty: 0` is falsy in Hugo, yielding `"recipeIngredient": ["g zero grams"]` and a row the scaler skips forever | Linter rejects `qty == 0`; it must be a positive number or null |
| RC4.8 | `tools/css-refs-allowlist.txt` allowlists the bare token `changed` site-wide | Follows RC3.4: allowlist the specific `recipe-q-changed` |
| RC4.9 | CLAUDE.md's recipe contract contradicts the linter four ways: names nonexistent `prep_time`/`cook_time`, omits required `date`/`lastmod`, calls required `summary`/`sources` optional | Correct it to the linter's actual REQUIRED/OPTIONAL sets |
| RC4.10 | CLAUDE.md names a nonexistent branch and states "~79 named steps" against an actual 97 | Fix both |
| RC4.11 | An unguarded `cuisine` leaves a dangling `" · Main"` separator on the card | Guard the separator |

### T5 — Class-level guards

| # | Row | Guard |
|---|---|---|
| RC5.1 | Every optional-field path is unexercised by the build | A third content fixture carrying **only** the REQUIRED fields — no tags, no times, a url-less source, a null qty. Lands in the same commit as the template guards it forces (a content fixture that breaks the build cannot be committed alone) |
| RC5.2 | The contrast gate checks against `--color-stone`; the rail is `--color-tile`, which puts `.alt` ("diced", "to taste") at 2.90:1 light / 3.21:1 dark | Add `--color-tile` pairings (burgundy, ink-fade, ink) to `tools/check-contrast.py`; nudge the dark burgundy stop until burgundy/tile clears AA |
| RC5.3 | Nothing asserts that a search filter returns visible results — exactly what RC2.1 swallowed | Playwright: select the recipes chip, assert visible result rows |

## 4. Testing

Each row gets a regression test in whichever layer already covers its surface,
written before the fix where a layer exists:

| Surface | Layer |
|---|---|
| Linter rows (RC1.3, RC4.6, RC4.7) | `unittest` in the paired `tools/test_check_recipes_*.py` |
| Formatter rows (RC2.5, RC2.6) | `node --test` in `tests/unit/recipe-scale.test.mjs` |
| Runtime + layout rows (RC2.1, RC2.4, RC3.1, RC3.2, RC5.3) | Playwright under `tests/e2e/` |
| Token rows (RC3.4, RC5.2) | `tools/check-contrast.py` |
| Template rows (RC1.2, RC2.2, RC2.3, RC4.x) | The production build itself, driven by the RC5.1 minimal fixture |

`tools/ci-local.sh` must pass end-to-end before merge. LHCI cannot run locally
(no system Chrome on this machine) and is verified in CI.

## 5. Sequencing

One commit per row, tier order, each commit green on its own. RC5.1 merges into
the first T1 template commit; RC4.8 follows RC3.4. Approximately 20 commits.

Merge to `main` once, after `ci-local.sh` is green and the branch is reviewed.
Nothing is pushed before then.

## 6. Out of scope

- **Unit downshifting** in the scaler (§2.2) — needs a conversion table and its
  own linter; a later slice.
- **Fixing `parse_frontmatter` centrally** so `null` stops arriving as the string
  `"null"`. The parser is shared by many linters and changing it risks all of
  them; RC1.3 normalizes locally. A central fix is worth its own row later.
- **Publishing real recipe content.** The org pipeline is built and E2E-verified;
  running it against the real corpus is a separate decision.
- **Slice 3** (meal-prep planner) — deferred, unchanged.
- **The dotfiles repo.** Verified unaffected (§2.1).
