# Recipe run follow-ups — deliberately deferred

**Date:** 2026-09-07
**Branch:** `dag/N19` (final node of the 19-node recipe-remediation graph)
**Trigger:** the 19-node remediation run that closed all 29 `RC` rows of
`2026-09-07-recipe-audit-remediation-design.md`. Reviewers on individual nodes
surfaced defects outside their row's scope; the final node verified each one and
recorded it here rather than widening the diff.
**Predecessors:** `2026-09-07-recipe-audit-remediation-design.md` (RC1–RC5, all
closed), `2026-07-03-audit-remediation-roadmap.md` (R1–R6.3, all closed). Same
row-ID convention, `RF` prefix.

**Nothing in this document is fixed.** Every row below reproduces on the merged
tree at the commit that closed the run.

---

## 1. Why this exists

The remediation run's charter was the 29 `RC` rows. Four late findings were
folded into the last node because they were cheap and squarely inside the recipe
surface: the `formatQuantity` decimal floor, a dead `.recipe-ing` margin rule,
two missing E2E guards, and the stale test counts in `CLAUDE.md`. Everything
else that surfaced falls into one of three buckets — outside the recipe surface,
requiring a design call, or pre-existing — and lands here instead.

Three of these (RF1.1, RF1.2, RF1.3) are live defects on the deployed site today.
They are not recipe defects; the recipe work is what made them visible.

Two structural observations are worth carrying forward, because they explain
why several rows below went unseen for months:

1. **A gate that reads tokens cannot see a literal.** `check-contrast.py` parses
   the `:root` blocks. Three colours in `main.css` are hardcoded hexes outside
   those blocks, so they are structurally invisible to the only accessibility
   gate in CI (RF1.2, RF3.1). Two more tokens were checked only by
   value-coincidence with a sibling until RF3.3 closed that.
2. **Coupling recorded in a comment is coupling that is not enforced.** RF2.1 is
   a template and a linter that must agree on a three-branch shape ladder, with
   nothing but a `{{- /* mirrored by … */ -}}` note holding them together. The
   N17 review failure is the existence proof that this drifts and survives
   review.

---

## 2. Rows

### T1 — Live defects on the deployed site

| # | Row | Evidence | Where to start |
|---|---|---|---|
| RF1.1 | **Search silently drops every result outside the chip vocabulary.** `assets/js/search.js:6` — `SECTION_ORDER` lists `essays garden research works library streams recipes home about`. `performSearch` groups by `d.meta.section \|\| 'other'` (`:137`), `renderResults` computes `total` from *all* groups (`:76`) but iterates only `SECTION_ORDER` (`:83`). Any section not in that array is counted in the status line and never rendered — as is the `'other'` fallback bucket the grouping itself creates. | Sections present in the built index but absent from `SECTION_ORDER`: `tags` 50 pages, `series` 2, `credits` 1, `blog` 1 (`grep -rlo 'data-pagefind-filter=section:<s>' public --include='*.html' \| wc -l`). Reproduced in a headless browser against the built `public/`, default All chip: query `example` → status `"30 results in 185ms"`, `.search-modal-result` count **25**, rendered groups `[essays, research, works, streams, recipes]`. Query `one` → 30 / 23. Query `a` → 30 / 27. | Needs a design call, which is why it is not fixed here: give `tags`/`series`/`credits`/`blog` their own groups, or add a rendered `Other` bucket, or exclude them from the index. Whichever is chosen, `renderResults` should also render `groups.other` or assert it is empty — today it can never be reached. |
| RF1.2 | **`.rss-link` fails the non-text contrast bar on every page in light mode.** `assets/css/main.css:407-408` — `.rss-link { color: #ee7e2c; }`. This is the header RSS icon, present in the site chrome on all pages. WCAG 2.1 SC 1.4.11 sets 3:1 for meaningful non-text content; this is below it. Invisible to `tools/check-contrast.py` because the value is a hardcoded hex, not a `--color-*` token, and the gate only parses the `:root` blocks. | Computed against the light `--color-stone` (`#eeeeea`): **2.36:1**. Dark mode is fine at 6.47:1, so the failure is light-mode-only. | Tokenize as `--color-rss` in all three token blocks (`:root`, `:root[data-theme="dark"]`, and the `prefers-color-scheme` block — they must stay identical or `check_dark_tokens.py` fails), darken the light value to clear 3:1, and add the pairing to `check-contrast.py` so the gate can see it. Darkening alone leaves the class of defect open. |
| RF1.3 | **The streams cron has been failing to push since the default-branch rename.** `.github/workflows/streams-poll.yaml:46-47` still runs `git pull --rebase origin master` / `git push origin master`. The repo's default branch was renamed `master` → `main` and `origin/master` deleted (see `75afdbe ci(deploy): trigger Pages deploy on main`). The workflow runs every 5 minutes and cannot have committed anything since. | `data/streams-live.yaml` is action-authored and rewritten on every poll; it still reads `last_polled: 2026-05-19T00:00:00Z` with both `is_live: false`. That is the stuck live-pill state, and it is the direct consequence. | Two-line change to `main` in both commands. Worth also checking the workflow's run history for the accumulated failures, and whether any other workflow or script still names `master` (`grep -rn 'origin/master\|origin master' .github/ tools/`). |

### T2 — Correctness and guard gaps, not currently user-visible

| # | Row | Evidence | Where to start |
|---|---|---|---|
| RF2.1 | **The `image` shape ladder is coupled to its linter by a comment only.** `layouts/partials/recipes/schema-recipe.html:54-67` branches three ways (absolute http(s) → pass through; root-relative `/…` → `absURL`; anything else → prefix with `.Permalink`). `tools/check_recipes_links.py:40-77` validates the same three shapes and must stay identical. The only thing binding them is the comment `mirrored by tools/check_recipes_links.py`. Drift reintroduces a shape the linter certifies and the template mangles — a class no other check can see, since a mangled-but-well-formed URL passes `check_html_links.py` too. | Only **one** of the three branches is exercised by a fixture: `content/recipes/example-recipe-one/index.md:15` declares `image: "hero.svg"` (the bundle branch). No fixture declares an absolute or a root-relative image, so two of three branches have zero coverage in the build *and* in the linter's fixtures. The N17 review failure occurred in exactly this ladder. | Cheap and mechanical: add one recipe fixture per shape (or one fixture cycling all three across a test matrix in `tools/test_check_recipes_links.py`), then assert that for each, the linter accepts it *and* the emitted `"image"` in `public/recipes/<slug>/index.json` equals the expected absolute URL. That single assertion is what makes the two implementations one contract. |
| RF2.2 | **`ENAMETOOLONG` turns a clean rejection into a traceback.** `tools/check_recipes_links.py:73` and `:76` call `Path.exists()` on a path built from author-supplied frontmatter. `exists()` swallows `ENOENT` but propagates other `OSError`s, so a path component over 255 bytes crashes the linter instead of reporting a bad `image`. | `Path('static/' + 'x'*300 + '.jpg').exists()` → `OSError [Errno 63] File name too long`. The linter's own control flow expects a boolean here. | One-line `try/except OSError: return False` helper wrapping both call sites, plus a unit test in `tools/test_check_recipes_links.py` asserting the over-long path is reported as a normal "not found" error rather than raising. Worth grepping the other 34 linters for bare `.exists()` on author-supplied paths. |
| RF2.3 | **`unitFor` mishandles irregular plurals.** `assets/js/entry-recipes.js:45-50` singularises `yield_unit` at a yield of exactly 1 with two regexes. `/[^s]s$/` strips one character from anything ending in a non-`s` plus `s`, which includes `-ves` plurals. | Evaluated directly: `loaves` → `loave`. (`cookies`→`cookie`, `servings`→`serving`, `boxes`→`box`, `biscuits`→`biscuit` are all correct.) `yield_unit` is free-form: `tools/check_recipes_fixtures.py:23` lists it in `OPTIONAL` with no value constraint, so any noun can reach this code. | Either constrain `yield_unit` to a small enum in the linter (which also gives the exporter something to validate against), or add an irregular-plural map to `unitFor` for the `-ves` / `-ies` / invariant cases. The enum is the smaller surface. Announcing the plural form at yield 1 would be a third option — worse copy, no code. |
| RF2.4 | **`#recipe-serves` declares no `step`, and the multiplier path writes fractional values into it.** `layouts/partials/recipes/rail.html:7` — `type="number" min="1" max="99"` with no `step`, so the implied step is 1. `fromMult`'s write-back puts the computed servings into that field. This is the same defect class RC2.6 removed from the sibling input, which gained `step="any"`. | Driven in a real browser on `/recipes/example-recipe-one/`: setting `.recipe-mult` to `0.3` and blurring leaves `#recipe-serves` at `{"value":"1.2","step":null,"stepMismatch":true,"valid":false}`. | Inert today: no `:invalid` styling targets it and it is not inside a `<form>`, so nothing surfaces the invalid state. Fix is `step="any"` to match the multiplier, or round the write-back. Left alone because deciding *which* is a behavioural call about whether fractional servings are legal at all. |
| RF2.5 | ~~**Five pages ship duplicate `id` attributes.**~~ **WITHDRAWN — false positive.** A real `html.parser` pass over all 129 built pages finds **zero** duplicated `id` attributes. The original finding came from `grep -o 'id=[a-zA-Z0-9_-]*'`, which matches a bare `id=` with an empty capture inside quoted attribute values; those empty matches then collide with each other. Of the three apparent occurrences of e.g. `id=tldr`, exactly one is a DOM element — the other two were inside `<meta name=description>` and `og:description` attribute values. | Disproved by parse, not by grep. | No action. **But the investigation surfaced a real defect**: those meta attributes contained raw rendered HTML, on 18 pages. Fixed in `b4ff675`, guarded by `tools/check_meta_description.py`. A finding worth having chased even though the row itself was wrong. |
| RF2.6 | **The search status line reports a ceiling, not a count.** `assets/js/search.js:133` — `search.results.slice(0, 30)`; `total` is then computed from the 30 fetched, so the line reads `"30 results"` for any query matching 30 or more. | Four different queries (`example`, `lorem`, `one`, `a`) all report exactly `30 results`, with 25/29/23/27 rows rendered. `search.results.length` — the true total — is available and discarded. | Report `search.results.length` in the status line and say the pane is showing the top 30, or paginate. Interacts with RF1.1: fixing that changes the rendered count but not the ceiling. |

### T3 — Standards, hygiene, and watch items

| # | Row | Evidence | Where to start |
|---|---|---|---|
| RF3.1 | **`.header-live-pill-dot` is under the 3:1 non-text bar in dark mode.** `assets/css/main.css:5149` — `background: #b22222`, another hardcoded hex outside the token blocks and therefore invisible to `check-contrast.py`. | Computed against the dark `--color-stone` (`#181818`): **2.66:1**. Light mode is 5.74:1. | Materially mitigated: the dot sits inside a pill that carries the literal text "LIVE", so the colour is not the only channel and SC 1.4.11's "meaningful" test is arguable. Fix alongside RF1.2 — same root cause (untokenized literal), same one-line remedy, and the pairing then joins the gate. |
| RF3.2 | **`<noscript><style>` sits in `<body>`.** `layouts/partials/recipes/rail.html:2`. `<style>` is metadata content; its content model places it in `<head>`, with the HTML spec's body-allowance being a parser concession rather than a conformance one. The precedent it cites — `layouts/partials/head.html:65`, the `.cite-static` no-JS rule — is inside `<head>`, where it conforms. | In the built page the block renders at byte offset 4697, against `<body` at 2336 and `</head>` at 2329. Every browser honours it (RF's own new E2E guard depends on that), and no validator runs in CI, so nothing catches it. | Move the rule into `head.html` gated on `.Section == "recipes"`, matching the `.cite-static` pattern one line above it. Zero behavioural change; it is purely about not carrying a second, weaker precedent. |
| RF3.3 | ~~**`--color-paper` is in the contrast gate only by value-coincidence.**~~ **CLOSED.** Four pairings added to `check-contrast.py`: `ink`/`ink-soft`/`burgundy` **on** paper, and paper **on** burgundy. Both directions render, so both are gated — burgundy text on a paper control (`.reenable-tracking`, `.recipe-stp button`) and paper text on a burgundy fill (`.search-modal-chip.is-active`, `.download-link:hover`). `ink-fade` on paper was considered and rejected: `.recipe-mult` is `background: transparent`, so that text sits on the rail, not on a panel — gating it would gate a hypothetical. A value-identity assertion (paper == tile) was also considered and rejected: the two tokens are documented as semantically distinct and are *allowed* to diverge; asserting equality would forbid the very change the gate exists to make safe. | Mutation-proven in both directions rather than observed passing: with the pairings absent, nudging light `--color-paper` to `#6e6a64` (ink at 3.23:1) still exits **0** — the gap. With them present, the same mutation exits **1** naming all four paper pairings, and an equivalent dark-mode nudge (`#7a7a7a`, applied to both dark blocks so `check_dark_tokens` stays green) also exits 1. Clean tree: 21 pairings x 2 modes, all PASS. | Done — `tools/check-contrast.py`, `CLAUDE.md` prose. |

| RF3.4 | **Two checked pairings sit ~0.1 above the AA bar.** — **AMENDED, and the row understated it.** A full margin sweep of all 21 pairings x 2 modes puts the *thinnest* pair at `color-warn on color-stone` / `color-stone on color-warn`, **4.55:1** — tighter than either pairing the row named, and not mentioned by it. The full thin set: warn/stone both directions **+0.05**; burgundy against tile and paper, all four directions, **+0.06** (dark); `ink-fade on stone` **+0.12** (light); `green-soft on stone` **+0.26** (light). | `python3 tools/check-contrast.py` now prints each pairing's margin and closes with the sub-0.25 set, so the sweep is reproducible from the tool rather than from this table. Mutation-proven: nudging `--color-green-soft` to `#507159` (4.69:1) makes it appear in the block at `+0.19`, in sort order, with the run still exiting 0. | Partly done. The *reporting* half is closed — the margin is now in the gate's output instead of in this document. The *palette* half is a visual-identity call and stays open: three hue-preserving nudges lift everything to >=0.25 margin — light `--color-warn` `#a05a1a`->`#9c5719` (4.55->4.76), light `--color-ink-fade` `#6e6a64`->`#6c6862` (4.62->4.76), dark `--color-burgundy` `#de6f7d`->`#df7481` (4.56->4.75, and must be edited in both dark blocks or `check_dark_tokens.py` fails). Each is a 1.5-3.2% shift toward black/white; none changes another pairing's verdict. |

---

## 3. Verified clean

Recorded so a later pass does not re-litigate them:

- **`grep -c '^\s*- name:' .github/workflows/hugo.yaml` → 103**, matching the
  number documented in `CLAUDE.md`. No drift. (This line read `97` when first
  written — a miscount, not drift; re-verified 2026-09-07.)
- **`--color-paper` / `--color-tile` semantics** are distinct and correctly
  documented in `CLAUDE.md`; the *gate* coverage was the thin part, and RF3.3 closed it; the
  palette was never wrong.
- **The other two hardcoded literals in `main.css`** (`#000` at `:5165`, the
  YouTube embed letterbox; the `rgba(178,34,34,…)` pill background at
  `:5135-5136`) are decorative backgrounds behind opaque content, not
  foreground colours, and carry no contrast obligation.
