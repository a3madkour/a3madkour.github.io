# Works section — design

**Date:** 2026-05-12
**Phase:** 6 (Works: games / music / poetry)
**Status:** spec — ready for plan

## Context

`content/works/_index.md` is a placeholder ("Coming soon.") and `/works/` renders nothing meaningful. The parent design spec §4.13–4.20 specifies a Works umbrella plus three sub-sections (games / music / poetry), each with its own index page and per-item page type. Phase 6 in the master phase list (§14) covers this whole surface.

Three of the per-item page types lean on substantial runtime: game iframe embeds (itch.io / Bitsy / custom WebGL), music platform iframes plus a custom audio player widget, and synced-lyrics rendering driven by `<audio>` `timeupdate` events. The lyrics runtime in particular pairs across page types — a music piece's `:LYRICS_POEM:` field points at a published poem, and the poem page surfaces an "audio pill" back to the music piece.

The site is currently in "fixtures + Hugo templates" mode for all sections; the elisp/ox-hugo pipeline that will produce real frontmatter is Phase 3 work on the user's side and remains blocked. Every prior slice (essays, garden, research, About bio half, citation hover-card) followed the same approach — ship layouts + frontmatter contracts + linter + fixtures so the surface is exercised end-to-end, then drop in real content when ox-hugo lands.

## Goals

1. Render every URL specified in parent spec §4.13–4.20 with content sourced from fixture frontmatter.
2. Lock the frontmatter contract for games, music, and poetry note types so ox-hugo can target a stable shape.
3. Surface every cross-section connection that's meaningful at this stage: games ↔ research / essays / garden notes, music ↔ poetry (via `lyrics_poem` / `set_to_music` round-trip), poems ↔ music (the audio-pill back-edge).
4. Reuse the shared `partials/filter-chips.html` component on all three sub-section indexes — no new chip implementation.
5. Defer runtime-heavy pieces (iframes, custom audio widget, synced-lyrics player) behind `data-pending` stubs that exercise the shape in fixtures without shipping the runtime.
6. Add two new CI gates — `check_works_fixtures.py` (frontmatter contract per type) and `check_works_links.py` (cross-reference resolver + round-trip enforcement) — bringing the Python gate count from 15 → 19.

## Non-goals

- Game iframe embeds (itch / Bitsy / WebGL). Fixtures carry `embed_url`; templates emit a `data-pending` "→ Play in browser" stub link only.
- Music platform iframes (Bandcamp / SoundCloud / YouTube). Fixtures carry `platform_embed`; templates emit "→ Listen on <kind>" text link only.
- Music custom audio player widget. Fixtures carry `audio_url`; templates render a `data-pending` "player coming soon" stub.
- Synced-lyrics runtime + two-column lyrics layout (parent spec §4.18). Music pages with `lyrics_poem` set render a stub block linking to the poem; no `timeupdate` runtime.
- Audio-pill pulse animation on poem pages. Pill renders without animation.
- Gif-vs-hero toggle on game cards (parent spec §4.14). Card preview is the hero SVG only.
- Real game / music / poetry content. All fixture frontmatter values, prose bodies, hero SVGs, cover SVGs, and screenshot SVGs are obvious filler per the standing rule.

## Amendment to parent spec §4.19 — poetry index uses filter chips, not tabs

The parent spec specified three view tabs for `/works/poetry/` (Recent / By collection / By tag). This slice replaces tabs with the standard shared filter-chips strip used on every other index in the site. Rationale:

- Consistency: every other section index uses the chip strip. Tabs would be the only divergent pattern on the site.
- Compositionality: chips compose with AND across dimensions. The tabbed UX was three mutually exclusive views; the chip UX lets a reader narrow by collection AND tag simultaneously.
- Cost: zero new component code; tabs would have required a new sub-page routing scheme or client-state toggle.

The "framing paragraph per collection" affordance from the spec is lost. If a collection ever wants a real intro, that becomes a separate `/works/poetry/collections/<slug>/` page (out of scope for this slice).

## Architecture

### URL structure and layouts

```
/works/                       layouts/works/list.html
/works/games/                 layouts/works-games/list.html
/works/games/<slug>/          layouts/works-games/single.html
/works/music/                 layouts/works-music/list.html
/works/music/<slug>/          layouts/works-music/single.html
/works/poetry/                layouts/works-poetry/list.html
/works/poetry/<slug>/         layouts/works-poetry/single.html
```

Hugo discriminates by `Type`. Each sub-section's `_index.md` sets the type both for itself (Hugo's `cascade` applies to descendants only, not to the cascading page) and for its children:

```yaml
# content/works/games/_index.md
type: works-games
cascade:
  type: works-games
```

Hugo's layout lookup order is Type → Section → default, so `/works/games/` resolves to `layouts/works-games/list.html` and `/works/games/<slug>/` to `layouts/works-games/single.html`. The umbrella at `/works/` doesn't need a Type override — Section=works resolves to `layouts/works/list.html` directly.

This trick is similar to `/research/themes/` and `/research/questions/`, but research's bare section URLs use `build: render: never` to suppress them entirely; Works renders all three indexes, so the explicit-type-and-cascade pattern is required.

The umbrella, three indexes, and three single templates each handle a substantially different shape (3-card overview vs card grid vs list rows vs narrow-column list vs per-item pages with different chrome). They live in separate layout directories rather than a single `layouts/works/` with internal switching.

### Frontmatter contracts

Three contracts, all enforced by `tools/check_works_fixtures.py`. The shared `parse_frontmatter` helper from `tools/check_fixtures.py` is reused — no parser changes needed.

**Games — `content/works/games/<slug>/index.md`**

| Field | Required | Type / values | Notes |
|---|---|---|---|
| `title` | yes | string | |
| `date` | yes | YAML date | |
| `lastmod` | yes | YAML date | |
| `draft` | yes | bool | |
| `status` | yes | enum: `playable` \| `in-progress` \| `archived` | single-active filter chip |
| `game_kind` | yes | enum: `full-release` \| `jam` \| `research-prototype` \| `experiment` | single-active filter chip. Named `game_kind` (not `type` or `kind`) to avoid Hugo's reserved field collisions — see note below the table. |
| `tagline` | yes | string | italic line under title |
| `year` | yes | int | |
| `tags` | optional | list[string] | multi-select filter chip (AND) |
| `summary` | optional | string | |
| `hero` | optional | string | filename inside page bundle |
| `embed_url` | optional | string | renders as `data-pending` stub |
| `source_url` | optional | string | GitHub etc. |
| `itch_url` | optional | string | itch.io page |
| `collaborators` | optional | list[string] | |
| `tech_stack` | optional | list[string] | |
| `length` | optional | string | playthrough length |
| `screenshots` | optional | list[string] | filenames inside page bundle; 3-up grid renders if present |
| `research_questions` | optional | list[string] | `/research/questions/<slug>/` paths |
| `related_essays` | optional | list[string] | `/essays/<slug>/` paths |
| `related_notes` | optional | list[string] | `/garden/<slug>/` paths |

**Why `game_kind` instead of `type` or `kind`:** Hugo reserves `type` as a built-in page variable that determines layout resolution, and `kind` collides with Hugo's `.Kind` page method (returning "page", "section", etc.) in template access patterns. The sub-section `_index.md` files set `type: works-games | works-music | works-poetry` via `cascade.type` so descendant pages resolve to the right layout tree; any per-fixture `type:` value would shadow the cascade and break layout resolution. Naming the games game-kind field `game_kind` is unambiguously a custom user field with no Hugo collision.

**Music — `content/works/music/<slug>/index.md`**

| Field | Required | Type / values | Notes |
|---|---|---|---|
| `title` | yes | string | |
| `date` | yes | YAML date | |
| `lastmod` | yes | YAML date | |
| `draft` | yes | bool | |
| `format` | yes | enum: `album` \| `track` \| `experiment` \| `live` | single-active filter chip |
| `year` | yes | int | |
| `tags` | optional | list[string] | |
| `summary` | optional | string | |
| `tagline` | optional | string | |
| `cover` | optional | string | filename inside page bundle |
| `duration` | optional | string | e.g. `42:18` |
| `tracks` | optional | list[`{title, duration}`] | numbered plain list rendered; no click-to-play |
| `platform_embed` | optional | `{kind, url}` | `kind ∈ {bandcamp, soundcloud, youtube}`; text link only |
| `audio_url` | optional | string | future custom-player input; `data-pending` stub only |
| `lyrics_poem` | optional | string | poetry slug; pairs with poem's `set_to_music` |
| `related_works` | optional | list[string] | `/works/<sub>/<slug>/` paths |
| `related_essays` | optional | list[string] | `/essays/<slug>/` paths |
| `made_with` | optional | list[string] | instruments / DAW etc. |
| `collaborators` | optional | list[string] | |

**Poetry — `content/works/poetry/<slug>/index.md`**

| Field | Required | Type / values | Notes |
|---|---|---|---|
| `title` | yes | string | |
| `date` | yes | YAML date | |
| `lastmod` | yes | YAML date | |
| `draft` | yes | bool | |
| `lines` | yes | int | line count |
| `tags` | optional | list[string] | multi-select filter chip (AND) |
| `collection` | optional | string | single-active filter chip |
| `set_to_music` | optional | string | music slug; pairs with music's `lyrics_poem` |
| `summary` | optional | string | |

### Cross-link consistency — round-trip enforcement

If `music[M].lyrics_poem == P`, then `poetry[P].set_to_music == M`. Asymmetric pairs fail the build. Enforced by `tools/check_works_links.py`. Same architecture as research's parent-question / theme consistency checks.

### Filter dimensions per index

| Section | Dims (chip-strip order) | Multi-select | Notes |
|---|---|---|---|
| Games | status, game_kind, tag | tag only | All three single-active except tag |
| Music | format, tag | tag only | |
| Poetry | collection, tag | tag only | `set_to_music` is a badge on the card, not a filter dim |

`partials/filter-chips.html` already auto-suppresses dimensions with <2 distinct values. The same rule applies here — sparse fixture sets won't render empty chip rows.

### `set_to_music` is a badge, not a chip

The `set_to_music` field on poems is a meaningful affordance ("this poem has a recorded version") but a poor filter facet — it would render a single-binary toggle that adds chip-strip noise without enabling composition. The poem index card surfaces the connection as a badge ("set to music"); the audio-pill on the poem page itself provides the actual cross-link.

### Layout templates

| Layout | Renders | Reuses | New partials |
|---|---|---|---|
| `layouts/works/list.html` | 3-card umbrella overview; each card pulls its sub-section's `.Pages`, shows count + 3 most-recent titles | — | `works/section-card.html` |
| `layouts/works-games/list.html` | Filter chips strip + 2-col responsive card grid (1-col below 720px) | `filter-chips.html` | `works/game-card.html` |
| `layouts/works-games/single.html` | Hero (title + tagline + status pill + year + collaborators + tech_stack + length) → embed-or-play block (stub) → About body → 3-up screens grid (if `screenshots`) → Connections (research questions + essays + notes) → Credits & links | — | `works/status-pill.html`, `works/connections.html` |
| `layouts/works-music/list.html` | Filter chips strip + list rows (80px cover thumb + title + format/length/year + brief description + listen link) | `filter-chips.html` | `works/music-row.html` |
| `layouts/works-music/single.html` | Hero (200px cover + meta strip) → Player frame (stub) → About body → Tracks (numbered plain list if `tracks`) → Synced-lyrics block (stub if `lyrics_poem`) → Connections | — | `works/audio-link.html`, `works/connections.html` |
| `layouts/works-poetry/list.html` | Filter chips strip + narrow-column row list; rows = Petrona-italic title + date + collection badge + "set to music" badge | `filter-chips.html` | `works/poem-row.html` |
| `layouts/works-poetry/single.html` | Title (Petrona italic ~2rem) → audio pill (if `set_to_music`) → body in generous-leading narrow column | — | `works/audio-pill.html` |

### Deferred-runtime stubs

Following the `math` / `video-sync` / `widget` shortcode convention from the essays slice (see CLAUDE.md "deferred-feature stubs"):

| Deferred capability | Stub location | What renders |
|---|---|---|
| Game iframe embed | `works-games/single.html` "embed-or-play block" | `<a class="works-embed-stub" data-pending>→ Play in browser</a>` linking to `embed_url` |
| Music platform iframe | `works-music/single.html` "player frame" | Text link "→ Listen on Bandcamp / SoundCloud / YouTube" from `platform_embed` |
| Music custom audio player | `works-music/single.html` "player frame" | `<div class="works-player-stub" data-pending>→ Listen (player coming soon)</div>` when `audio_url` set without `platform_embed` |
| Synced lyrics | `works-music/single.html` "synced lyrics" block + `lyrics` shortcode | `<div class="synced-lyrics-stub" data-pending>Lyrics: → <poem title></div>` linking to poem page when `lyrics_poem` set. Shortcode body emits a `<div class="synced-lyrics-stub">` container with raw line text inside, no `data-time` parsing |
| Audio-pill pulse animation | `works-poetry/single.html` | Pill renders; CSS animation deferred |

All five stubs carry `data-pending` so the future runtime swap-in is a grep target.

## CSS plan

Four new sections appended to `assets/css/main.css` after §31 (Research graph). Total addition ~380 lines.

- **§32 Works — shared chrome** (~80 lines): status pill (3 colors via existing tokens), audio pill, all five `data-pending` stub styles (italic + dotted underline + `--color-ink-soft`, mirroring `.placeholder` from §29), connections block two-column grid.
- **§33 Works — umbrella + games** (~120 lines): umbrella 3-card overview grid; games index card grid (2-col responsive); game-card shape (16:9 preview, top-right embed pill, bottom-left status badge, body); game page hero, screens 3-up grid, credits.
- **§34 Works — music** (~100 lines): music index list rows; music page hero (200px cover + meta strip), tracks numbered list, lyrics stub block.
- **§35 Works — poetry** (~80 lines): poetry index narrow-column rows (Petrona italic, collection + "set to music" badges); poem page narrow column (~600px, line-height ~2.1).

### Token reuse

No new tokens. Status colors map to existing palette:

| Status | Token | WCAG pairing already verified? |
|---|---|---|
| `playable` | `--color-burgundy` | Yes (§burgundy/stone AA) |
| `in-progress` | `--color-warn` | Rides along; not in checked pairings but matches research's `dormant` |
| `archived` | `--color-ink-soft` | Yes (§ink-soft/stone AA) |

`tools/check-contrast.py` doesn't need a new pairing.

## Fixture set

12 fixtures total: 4 games, 4 music, 4 poetry.

### Games (under `content/works/games/`)

| Slug | status | game_kind | What it exercises |
|---|---|---|---|
| `example-playable-full-release` | playable | full-release | The "everything filled in" fixture — `embed_url`, `screenshots` (3-up), `research_questions`, `related_essays`, `related_notes` cross-refs |
| `example-playable-jam` | playable | jam | Minimal — no embed, no screenshots, no cross-refs; graceful-empty path |
| `example-in-progress-research-prototype` | in-progress | research-prototype | `research_questions` only; in-progress status pill |
| `example-archived-experiment` | archived | experiment | `itch_url` + `source_url`, no `embed_url`; external-link-only path |

All 3 status values + all 4 game_kind values covered. Screenshots rendered by fixture #1 only.

### Music (under `content/works/music/`)

| Slug | format | What it exercises |
|---|---|---|
| `example-album-with-tracks` | album | `tracks` list (6 entries), `platform_embed: {kind: bandcamp}`, no `lyrics_poem` |
| `example-track-with-lyrics` | track | `lyrics_poem: example-poem-with-lyrics` (round-trip pair), `platform_embed: {kind: soundcloud}`, `audio_url` populated — exercises both the lyrics stub and the "audio_url without runtime" path |
| `example-experiment-minimal` | experiment | No tracks, no embed, no cross-refs; minimal music page |
| `example-live-session` | live | `tracks` list (3 entries), `platform_embed: {kind: youtube}`, `made_with` + `collaborators` |

All 4 format values covered. Round-trip lyrics pair exercised exactly once.

### Poetry (under `content/works/poetry/`)

| Slug | collection | set_to_music | What it exercises |
|---|---|---|---|
| `example-poem-with-lyrics` | `greenhouse-demos` | `example-track-with-lyrics` | Round-trip pair; audio pill renders |
| `example-poem-collected` | `greenhouse-demos` | — | Collection-only path; collection chip dim has ≥2 values |
| `example-poem-tagged` | — | — | Tag-only path |
| `example-poem-minimal` | — | — | Required-fields-only lower-bound shape check |

### Cross-section link targets

`example-playable-full-release` points at:
- `research_questions: [/research/questions/example-active-q-1, ...]` — existing research fixtures
- `related_essays: [/essays/example-essay-one, ...]` — existing essay fixtures
- `related_notes: [/garden/story-atoms, ...]` — existing garden fixtures

`tools/check_works_links.py` resolves each against the live content tree.

### Fixture body content

All fixture bodies are lorem ipsum / "Example N" filler — even poetry, which gets short stanzas of lorem-style nonsense. Per the standing rule (memory: filler-text-only), no authored prose, no AI-generated verse, no AI-generated illustrations for the SVGs (geometric placeholders only — same convention as essays' `hero.svg`).

### Hand-authored SVG placeholders

| Type | Count | Notes |
|---|---|---|
| Game hero | 4 | One per game fixture; 16:9 viewBox; used as card preview + page hero |
| Game screenshots | 3 | One set on `example-playable-full-release` only |
| Music cover | 4 | One per music fixture; square viewBox; used as 80px thumb + 200px page hero |

11 SVGs total. Each ~5–10 lines of geometric primitives in palette colors, same style as `content/essays/example-essay-one/hero.svg`.

## Linters

### `tools/check_works_fixtures.py`

Architecture mirrors `check_garden_fixtures.py`. Discriminates by URL path; per-type required / optional / forbidden field enforcement; enum validation; type validation. Reuses shared `parse_frontmatter`.

Validations per type:

**Games:**
- Required fields present, types correct
- `status ∈ {playable, in-progress, archived}`
- `game_kind ∈ {full-release, jam, research-prototype, experiment}`
- `year` is int
- `screenshots` is list of strings (file references)
- `research_questions` / `related_essays` / `related_notes` are lists of strings (path strings); existence resolution is `check_works_links.py`'s job

**Music:**
- Required fields present
- `format ∈ {album, track, experiment, live}`
- `year` is int
- `tracks` (if present) is list of `{title, duration}` dicts; both subkeys strings
- `platform_embed` (if present) is `{kind, url}` dict; `kind ∈ {bandcamp, soundcloud, youtube}`

**Poetry:**
- Required fields present
- `lines` is int

Companion unit-test suite `tools/test_check_works_fixtures.py`.

### `tools/check_works_links.py`

Resolves every cross-reference field against the live content tree:

- `music[M].lyrics_poem` → `content/works/poetry/<slug>/index.md` exists, not draft
- `poetry[P].set_to_music` → `content/works/music/<slug>/index.md` exists, not draft
- Round-trip: `music[M].lyrics_poem == P` ⟹ `poetry[P].set_to_music == M`
- `games[G].research_questions[i]` → `content/research/questions/<slug>/index.md` exists, not draft
- `games[G].related_essays[i]` → `content/essays/<slug>/index.md` exists, not draft
- `games[G].related_notes[i]` → `content/garden/<slug>/index.md` exists, not draft
- `music[M].related_essays[i]` → `content/essays/<slug>/index.md` exists, not draft
- `music[M].related_works[i]` → `content/works/<sub>/<slug>/index.md` exists, not draft

Companion unit-test suite `tools/test_check_works_links.py`.

### Filter-chips config

`data/filter-chips.yaml` gains three new sections (`games`, `music`, `poetry`), each with optional `primary_tags` curation + `primary_top_k` override per the existing pattern. `tools/check_filter_chips_config.py` already validates curated tags against the live taxonomy per section — no linter code change.

## CI integration

`.github/workflows/hugo.yaml` gains four new steps between "Run citation linter unit tests" and the Hugo build:

1. Verify works fixtures
2. Run works fixture linter unit tests
3. Verify works links
4. Run works links linter unit tests

Total Python gates: **15 → 19**.

## Hugo config

No new taxonomies. `collection`, `status`, `format`, `game_kind` are frontmatter facets only (consistent with how `flavor`, `stage`, `status` work on garden — filter dims are not Hugo taxonomies).

## File tree summary

```
content/works/{games,music,poetry}/_index.md            (3 new; cascade: type)
content/works/games/<4 slugs>/{index.md, hero.svg}      (4 fixtures + 4 SVGs)
content/works/games/example-playable-full-release/screen-{1,2,3}.svg
content/works/music/<4 slugs>/{index.md, cover.svg}     (4 fixtures + 4 SVGs)
content/works/poetry/<4 slugs>/index.md                 (4 fixtures)
layouts/works/list.html                                 (1 new)
layouts/works-games/{list,single}.html                  (2 new)
layouts/works-music/{list,single}.html                  (2 new)
layouts/works-poetry/{list,single}.html                 (2 new)
layouts/partials/works/{section-card,game-card,music-row,poem-row,
                       status-pill,audio-pill,audio-link,connections}.html  (8 new)
layouts/shortcodes/lyrics.html                          (no-op stub)
assets/css/main.css                                     (+§32–35, ~380 lines)
tools/check_works_fixtures.py + tools/test_*            (2 new)
tools/check_works_links.py    + tools/test_*            (2 new)
data/filter-chips.yaml                                  (+3 sections)
.github/workflows/hugo.yaml                             (+4 steps)
CLAUDE.md                                               (Phase 6 status, tools list, layouts list, partials list, shortcodes list, deferred-features table)
```

## Out of scope (fixtures exercise; runtime later)

All seven items below have fixture coverage and `data-pending` markers but no runtime in this slice. Each becomes its own future slice when authored content lands or when a runtime design is needed.

- Game iframe embeds (itch / Bitsy / WebGL)
- Music platform iframe (Bandcamp / SoundCloud / YouTube)
- Custom audio player widget + tracklist click-to-play
- Synced-lyrics runtime + two-column lyrics layout (parent spec §4.18)
- Audio-pill pulse animation
- Gif-vs-hero toggle on game cards
- Poetry tabs (parent spec §4.19) — replaced with filter chips in this slice; see amendment above
