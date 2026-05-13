# Library section — design spec

**Date**: 2026-05-12
**Phase**: 7 (library + homepage final — first slice: library only)
**Status**: design approved, plan pending
**Implements**: parent spec §3 (`/library/*` routes), §4.21–4.23 (per-page designs), §10.4 (yaml schema)
**Inherits constraints from**: parent spec §1 (no AI art, no AI text, accessibility AAA body / AA accent, fixture-only content)

---

## 1. Motivation

The library is the consumption-side counterpart to works (the creation side). It surfaces what the author is reading / listening to / playing / watching, and what they've finished, as a polished catalog filtered from media-flavor garden notes.

Per parent §10.4, library data is canonically `data/{reading,listening,playing,watching}.yaml` — produced by the future elisp pipeline by walking media-flavor org-roam nodes. This slice ships the Hugo-side surface against fixture yaml that round-trips when the elisp pipeline lands (Phase 3).

The slice unblocks two downstream things: (1) the homepage v3 "Currently" widget reads the same yaml, (2) the about-page Currently slot is library-shaped. Both are out of scope here but become trivial follow-ups.

## 2. Scope

**In scope (this slice):**

- 4 list pages: `/library/`, `/library/reading/`, `/library/listening/`, `/library/playing/`, `/library/watching/`. (Umbrella + 4 leaves.)
- 4 fixture yaml files at `data/{reading,listening,playing,watching}.yaml` per parent §10.4 schema. ~6 items per yaml = ~24 total.
- 2 hand-authored type-glyph SVGs in `assets/images/icons/library/`: `book.svg`, `clapper.svg`. Reused: `gamepad.svg`, `eighth-note.svg` from `assets/images/icons/works/`.
- New `layouts/library/` (umbrella + 4 leaf layouts). Type discrimination via `cascade.type` on each subsection's `_index.md`.
- New `partials/library/` set: `umbrella-card`, `currently-active`, `year-section`, `row`, `status-badge`, `type-glyph`.
- New CSS section `§37 Library` in `assets/css/main.css` (umbrella grid, currently-active card, progress bar, year section, row, status badge gutter, "Up next" block, empty state, glyph block).
- New JS entry `assets/js/entry-library.js` (~5 KB) — bundles `filter-chips.js`, dispatches per-page `setupFilterChips`. Loaded by `partials/scripts.html` predicate `.Section == "library"`.
- 2 new linter pairs in `tools/`: `check_library_fixtures.py` + `test_check_library_fixtures.py`; `check_library_links.py` + `test_check_library_links.py`. CI runs each linter then its sibling test, mirroring the existing 9 pairs.
- Add `Library` to top nav between **Works** and **About**.
- Extend `data/filter-chips.yaml` with a `library/` section (per-page subsections + per-page `primary_tags` curation).

**Out of scope (deferred to later slices):**

- Cover thumbnails (book / album / game / film / series). The "no AI illustrations" rule means real covers must be hand-sourced; deferred until that asset pipeline exists. Type-glyph blocks stand in.
- Last.fm scrobbles on Listening (parent §4.23 already says "absent for now").
- Library RSS feed.
- Homepage Currently widget — Phase 7 second slice.
- About-page Currently slot — Phase 7 second slice (about page §6 placeholder already exists).
- `/library/graph/` constellation — parent spec doesn't ask for one; defer unless appetite shows up later.
- Pagefind search modal — Phase 8.
- Per-item library pages. Library rows always link to the canonical `/garden/<slug>/` (parent §3); rows where `note_slug` is null omit the "→ my notes" link with no fallback page.
- Garden-note backfill for items without an existing media-flavor note. Reuse the 4 existing media notes (invisible-cities, koyaanisqatsi-soundtrack, outer-wilds, severance-s2); other fixture rows get `note_slug: null`.
- KaTeX, video-sync, widgets, audio runtime — none apply to library.

## 3. Architecture

### 3.1 Content + layouts

```
content/library/
  _index.md                    # cascade.type: library-umbrella
  reading/_index.md            # cascade.type: library-reading
  listening/_index.md          # cascade.type: library-listening
  playing/_index.md            # cascade.type: library-playing
  watching/_index.md           # cascade.type: library-watching

layouts/library/
  list.html                    # umbrella
  reading/list.html
  listening/list.html
  playing/list.html
  watching/list.html
```

Layout dispatch follows the existing research pattern (research-theme / research-question discriminated by `cascade.type`). Bare subsection routes render normally — unlike research where `build: render: never` hid the bare type indexes, the library leaves are the user-facing pages.

### 3.2 Partials

```
layouts/partials/library/
  umbrella-card.html      # one of the four overview cards
  currently-active.html   # 0–3 highlight grid above the year sections
  year-section.html       # wraps a year's rows; renders the rule + year label
  row.html                # one library row (used inside year-section)
  status-badge.html       # shape+color badge in the row gutter
  type-glyph.html         # switch between book / eighth-note / gamepad / clapper
```

Each partial takes a single `dict` arg (`item` or `items`) plus the active page context for url-building. No global state.

### 3.3 Data contract (parent §10.4, restated for clarity)

Each yaml file:

```yaml
items:
  - slug: invisible-cities             # required, kebab-case
    title: Invisible Cities            # required
    creator: Italo Calvino             # required
    year: 1972                         # required, int
    media_type: book                   # required, validated per page (see §3.4)
    status: reading                    # required, validated per page (see §3.5)
    started: 2025-12-15                # optional, YYYY-MM-DD
    finished: null                     # optional, YYYY-MM-DD; required when status: finished
    spoiler_level: light               # optional: none | light | heavy
    last_modified: 2026-04-22          # required, YYYY-MM-DD
    cite_key: calvino1972cities        # optional; when set, must resolve in citations.yaml
    canonical_url: "https://..."       # optional; must be HTTPS or null
    note_slug: invisible-cities        # optional; when set, must resolve to a non-draft garden note
    preview: "Re-reading for ..."      # optional; rendered as the takeaway line
    tags: [fiction, italian]           # required (may be empty); array of slug-shaped strings
    extras:                            # optional, type-specific (see §3.6)
      progress_pct: 51
      progress_label: "p. 84 / 165"
```

### 3.4 Per-page `media_type` allowlist

| File | Allowed `media_type` values |
|---|---|
| `data/reading.yaml`   | `book` |
| `data/listening.yaml` | `album`, `track` |
| `data/playing.yaml`   | `game` |
| `data/watching.yaml`  | `film`, `series` |

Linter rejects mismatches.

### 3.5 Status taxonomy per page

| Page | Allowed `status` values | Glyph |
|---|---|---|
| Reading   | `finished`, `reading`, `queued`, `abandoned` | ✓ ▶ ↑ ✗ |
| Listening | `finished`, `listening`, `queued`, `dropped` | ✓ ▶ ↑ ✗ |
| Playing   | `finished`, `100pct`, `playing`, `queued`, `dropped` | ✓ ★ ▶ ↑ ✗ |
| Watching  | `finished`, `watching`, `queued`, `dropped` | ✓ ▶ ↑ ✗ |

Status badges in the row gutter use shape + color (CB-safe — never color-only meaning per parent §1). Color tokens: ✓ `--color-evergreen`, ▶ `--color-steel`, ↑ `--color-ink-soft`, ✗ `--color-burgundy`, ★ `--color-warn`.

### 3.6 `extras` shape per `media_type`

| `media_type` | `extras` keys |
|---|---|
| `book`   | `progress_pct` (0–100, int), `progress_label` (string) |
| `album`  | (none) |
| `track`  | (none) |
| `game`   | `hours_played` (int or null), `platform` (string: PC / Switch / PS5 / Web / …) |
| `film`   | `runtime_min` (int or null) |
| `series` | `episode_count` (int), `current_episode` (int or null), `current_season` (int or null) |

Linter validates `extras` keys against the allowlist for the row's `media_type`. Unknown keys reject.

### 3.7 Currently-active highlight rules

- Items with status ∈ {reading, listening, playing, watching} appear in the highlight at the top of their leaf page; not in year sections.
- Layout: 1 active = full-width card; 2–3 active = 2-column grid; 4+ active is not currently expected (no spec'd behavior — linter warns).
- Reading + Watching show a CSS progress bar driven by `extras.progress_pct` (Reading) or computed from `extras.current_episode / extras.episode_count` (Watching, series only — films have no bar).
- Listening + Playing skip the progress bar (rotation/play-session progress doesn't fit a single number cleanly); show `started` date only.

### 3.8 Year sections

- Items with status ∈ {finished, abandoned, dropped, 100pct} are grouped by `finished` year DESC. Items missing `finished` (e.g., abandoned without a date) sort under "Undated" at the bottom of year sections.
- Section header rule: small caps Inter, 0.78rem, with hairline rule extending right. (See parent spec §4.22 wireframe.)

### 3.9 "Up next" block

- Items with status ∈ {queued} appear here, not in year sections. Looser format: single-line per item — `↑ Title · Creator · Year`.
- Sorted by `last_modified` DESC (most recently triaged first).

### 3.10 Spoiler treatment

- `spoiler_level: heavy` → inline tag in row meta, `--color-burgundy`, "spoilers: heavy"
- `spoiler_level: light` → muted tag, `--color-ink-soft`, "spoilers: light"
- `spoiler_level: none` or unset → omit
- No content masking on library pages (the rows don't carry author prose); spoiler-aware indexing is a Phase 8 search-modal concern.

### 3.11 Empty state

When a yaml has zero items: page renders the hero + lede only, with a muted "Nothing here yet." note. No filter chip strip, no year sections.

### 3.12 Filter chip dimensions per page

| Page | Status dim | Other dim | Tag dim |
|---|---|---|---|
| Reading   | yes | — | yes (two-tier disclosure) |
| Listening | yes | format: album / track (drawn from `media_type`) | yes (two-tier) |
| Playing   | yes | platform: dynamic from `extras.platform` values | yes (two-tier) |
| Watching  | yes | format: film / series (drawn from `media_type`) | yes (two-tier) |

Suppression rule (existing): a dimension with <2 distinct values doesn't render.

**Tag chip primary set**: `data/filter-chips.yaml` `library/<page>.primary_tags` (manual, ordered) when curated; otherwise top-K=10 by item count. Two-tier rendering (primary inline, secondary in `<details>` disclosure with search) per existing `partials/filter-chips.html`. **`data-tags` attribute on rows must be space-delimited** (`delimit $tags " "`) — comma silently zeros all chip matches per `[[reference_filter_chips_data_tags_space_delimited]]`.

### 3.13 Cross-link rules

- `note_slug` set → row renders "→ my notes" linking to `/garden/<slug>/`. Linter verifies slug resolves to a non-draft garden page.
- `note_slug` null → "→ my notes" link omitted, no fallback.
- `canonical_url` set → row renders "→ original" linking to it. Linter verifies HTTPS.
- `cite_key` set → linter verifies it resolves in `data/citations.yaml`. Not currently rendered in the row UI (future addition: bibliography-style citation under the row).

### 3.14 Link label convention

Per `[[feedback_no_arrow_prefix_on_links]]`, content-level links in rows use plain text — no arrow prefix and no arrow suffix. Row links render as `my notes` and `original` (no `→`). The summary-style chrome arrows ("All reading →") on the umbrella card footer keep their suffix arrow (matches the existing essays/works pattern).

## 4. Visual design

The `.superpowers/brainstorm/689377-1778641359/content/library-wireframes-v3.html` mockup is the canonical reference. Summarized:

### 4.1 Umbrella `/library/`

2×2 grid of cards on desktop; stacks to 1 col at ≤720px. Each card: medium label + small glyph, stats line, top-3 active-or-recent items (status badge + italic title + creator/year), "All X →" footer link. Card background `#fff8eb`, border `--color-rule`.

### 4.2 List pages `/library/{reading,listening,playing,watching}/`

Top-down: breadcrumb (Library › Page) → page H1 → italic lede → "Currently active" highlight → stats line + chip strip → year sections → "Up next".

Currently-active card: 64px glyph block (gradient per medium) + content column (italic title, meta line, optional progress bar, takeaway in italic Petrona, row links).

Year-section row: 24px status badge + 44px glyph block + content column (title with floated tag chips, meta line, takeaway, row links).

### 4.3 Glyph blocks

| Medium | SVG | Tint gradient |
|---|---|---|
| `book`           | `book.svg` (new)            | burgundy → darker |
| `album`, `track` | `eighth-note.svg` (reused)  | steel → darker |
| `game`           | `gamepad.svg` (reused)      | evergreen → darker |
| `film`, `series` | `clapper.svg` (new)         | violet → darker |

`--color-violet` is a new token (added to `:root` and `[data-theme="dark"]` blocks). Not gated by `tools/check-contrast.py` — it appears only as a glyph-block background, not behind text. The glyph color is `var(--color-tile)`, which flips with theme: near-white (`#fdfcf8`) on dark violet (`#5d4a8a`) in light mode → 7.27:1 (AAA); near-black (`#2a2a2a`) on light violet (`#b8a6e0`) in dark mode → 6.54:1 (AA). Both pass spec §1's "AA accent" requirement; verified numerically per `[[feedback_verify_contrast_ratios]]`.

### 4.4 CSS section §37

New section in `assets/css/main.css`:

- `.library-umbrella` grid (2×2 desktop / 1 col mobile)
- `.library-um-card`
- `.library-currently` grid (1-col / 2-col by `data-active-count`)
- `.library-curr-card`
- `.library-progress` + `.library-progress > span`
- `.library-year` (rule + label)
- `.library-row` grid (badge + glyph + content)
- `.library-status-badge` (`.b-fin`, `.b-act`, `.b-queue`, `.b-aban`, `.b-100`)
- `.library-glyph-block` + per-treatment modifiers (`.book`, `.music`, `.game`, `.watching`). `.music` covers `media_type ∈ {album, track}`; `.watching` covers `{film, series}`.
- `.library-upnext` block
- `.library-empty` muted note
- Responsive collapses at ≤720px (umbrella stacks; currently grid stacks; row glyph block hides ≤480px)

### 4.5 Glyph cost

Two new hand-authored SVGs:

- `book.svg` — open book with page lines, 24×24 viewbox (matches works glyph sizing).
- `clapper.svg` — film clapper-board with diagonal stripes on the slate, 24×24.

Both monochrome (currentColor); container provides the tint gradient.

## 5. JS

### 5.1 Bundle layout

New entry `assets/js/entry-library.js`:

```js
import { setupFilterChips } from "./filter-chips.js";

const page = document.body.dataset.libraryPage;
if (page) {
  setupFilterChips({
    containerSelector: `.library-chips[data-page="${page}"]`,
    cardSelector: ".library-row",
    sectionSelector: ".library-year",
    emptyStateSelector: ".library-empty",
  });
}
```

`<body data-library-page="reading">` set by leaf layouts.

`partials/scripts.html` adds:

```go
{{- if and (eq .Section "library") (ne .Path "/library/") -}}
  {{- $libBundle := resources.Get "js/entry-library.js" | js.Build (dict "minify" true) -}}
  ...
{{- end -}}
```

The umbrella (`/library/`) does not load the bundle — it has no chips, no rows.

### 5.2 No graph view

Library has no force-directed graph in this slice. No d3 imports. Bundle ≈ 5 KB minified (filter-chips.js + tiny dispatcher).

## 6. Linters

### 6.1 `tools/check_library_fixtures.py`

Validates each `data/{reading,listening,playing,watching}.yaml`:

- Top-level shape: `items: [...]`, list of objects.
- Required fields present + correct type per §3.3.
- `media_type` ∈ allowlist for the file (per §3.4).
- `status` ∈ allowlist for the file (per §3.5).
- Date fields parse as ISO YYYY-MM-DD.
- `finished` required when `status == finished`.
- `tags` is a list of slug-shaped strings (`^[a-z0-9-]+$`).
- `extras` keys ∈ allowlist for `media_type` (per §3.6).
- `progress_pct` in [0, 100] when present.
- `current_episode <= episode_count` when both present.
- Currently-active count per page ≤ 3 (warn, not fail — fixtures may exceed in future).
- Slug uniqueness within file.

Mirrors `tools/check_works_fixtures.py` structure. Has sibling `test_check_library_fixtures.py` with 8–10 passing/failing fixtures.

### 6.2 `tools/check_library_links.py`

Cross-resolves every library item:

- `note_slug` set → must point to an existing non-draft `content/garden/<slug>/index.md`.
- `cite_key` set → must exist as a key in `data/citations.yaml`.
- `canonical_url` set → must start with `https://` or be null.

Mirrors `tools/check_works_links.py`. Sibling `test_check_library_links.py`.

### 6.3 CI integration

`.github/workflows/hugo.yaml` gets 2 new linter steps + 2 new sibling-test steps (so 4 new CI steps total; 19 → 23). Each runs in ~1s.

## 7. Fixtures

~6 items per yaml × 4 yamls = ~24 total. Each yaml seeds:

- 1–2 currently-active rows (status: reading/listening/playing/watching).
- 2–3 finished rows across at least 2 years (exercise the year-section grouping).
- 1–2 queued rows (exercise "Up next").
- 1 abandoned/dropped row (exercise the ✗ badge).
- 1+ row with `note_slug` pointing to an existing media garden note: invisible-cities (reading), koyaanisqatsi-soundtrack (listening), outer-wilds (playing), severance-s2 (watching).
- Other rows: `note_slug: null`.

Filler convention (existing): `Lorem Ipsum N` titles, `Author N` / `Studio N` / `Director N` creators, `2018`–`2025` year spread. No authored prose. Per `[[feedback_filler_text_only]]`.

Listening yaml includes ≥1 `track` (not just albums) so the format chip dim has ≥2 values and renders. Watching yaml includes ≥1 film and ≥1 series for the same reason.

## 8. Nav

`layouts/partials/header.html` nav list grows from 5 → 6 items:

```
Essays · Garden · Research · Works · Library · About
```

`Library` slot inserted between Works and About. Active-state logic (`hasPrefix .RelPermalink "/library/"`) follows the existing pattern.

## 9. Testing

### 9.1 Automated

- Both new linters + their unit-test siblings in CI.
- Existing `tools/check-contrast.py` re-runs and must pass (no token changes besides the new `--color-violet` which is glyph-block-only, white-on-violet contrast verified numerically out of band).
- All 9 existing linter pairs continue to pass (no fixture changes outside library; garden notes unchanged).

### 9.2 Manual dev-server spot-check (per `[[feedback_verify_before_merge.md]]`)

Before merge, spot-check:

1. `/library/` — 2×2 cards render; counts match yaml; "All X →" links navigate correctly.
2. `/library/reading/` — currently-active highlight shows 2 books with progress bars; chip strip filters correctly across status + tag dims (AND); year sections collapse correctly; "Up next" renders.
3. `/library/listening/` — eighth-note glyph; format chip dim shows album + track; no progress bar.
4. `/library/playing/` — gamepad glyph; platform chip dim populated from `extras.platform`; ★ status badge renders for `100pct` row.
5. `/library/watching/` — clapper glyph; format chip dim shows film + series; series row has episode progress bar; film row has no bar.
6. Cross-links: rows with `note_slug` link to `/garden/<slug>/`; rows without omit the link (no broken-link fallback).
7. Theme toggle: light + dark + system; glyph blocks legible in both; status badges still distinguishable.
8. Narrow viewport: umbrella stacks; currently-active stacks; row glyphs hide at ≤480px without breaking layout.

## 10. Memory references

- `[[feedback_filler_text_only]]` — fixture content stays obvious filler.
- `[[feedback_deferred_features_stay_visible]]` — covers / Last.fm / RSS deferred but documented; CLAUDE.md table updated.
- `[[feedback_dont_defer_cheap_things]]` — progress bar shipped (cheap CSS); year sections shipped.
- `[[feedback_verify_before_merge]]` — dev-server spot-check before merge.
- `[[feedback_no_arrow_prefix_on_links]]` — row links use plain "→ my notes" suffix style (matches existing surface).
- `[[reference_filter_chips_data_tags_space_delimited]]` — `data-tags` attribute on rows uses space delimiter.
- `[[feedback_class_rename_grep_full_codebase]]` — none of the new class names collide with existing; no renames in this slice.
- `[[reference_hugo_dev_server_gotcha]]` — implementer must not run `hugo --minify` with a live dev server during development.

## 11. Acceptance criteria

- All 4 library pages render with fixture content; no broken links; no Hugo build warnings.
- All 4 yaml files validate against `check_library_fixtures.py`.
- All cross-links validate against `check_library_links.py`.
- Filter chips work per page (status / format-or-platform / tag dims; AND across; multi-select within tag dim).
- Currently-active highlight, year sections, "Up next" block, empty state all render correctly.
- Both new SVG glyphs land in `assets/images/icons/library/`; gamepad + eighth-note reused from works.
- New CSS section §37 added; existing sections untouched.
- New JS entry adds ~5 KB to library pages only; no other section affected.
- Top nav grows from 5 → 6 items; `Library` active-state highlights on `/library/*`.
- Dev-server spot-check passes per §9.2 before merge.
- CI passes (contrast + 11 linter pairs = 23 steps).
