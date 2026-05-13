# Homepage v3 — design

**Phase:** 7 (Library + homepage final) — third and last Phase 7 slice.
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §4.1, §5.8, §14.

The current homepage is the role line + essays strip only. This slice assembles the four remaining blocks from the mockup at `.superpowers/brainstorm/1178775-1777859433/content/homepage-v3.html`: hero, Currently widget, Research strip, and a 2-column Garden + Studio block. The footer is already in spec shape (colophon + "Words are mine; not generated"); no work there.

---

## 1. Architecture

### File layout

```
layouts/
  home.html                        # rewritten — thin orchestrator (~20 lines)
  partials/home/                   # new directory
    hero.html
    currently.html
    research-strip.html
    garden-strip.html              # reuses garden/note-tile.html
    studio-strip.html
content/
  _index.html                      # body removed; gain home_lede frontmatter
assets/css/main.css                # +§38 hero, +§39 Currently, +§40 strips
```

### Reused partials (no changes)

- `essay-card.html` + `essay-card-featured.html` — existing essays strip stays as-is.
- `garden/note-tile.html` — garden strip wraps in `.home-garden-strip`; CSS scopes the size reduction.
- `works/glyph-sprite.html` — one-shot SVG sprite (`<symbol id="g-game">` / `g-music` / `g-poetry`). Rendered once at the top of `layouts/home.html` (only when the studio strip will render anything); each studio row references it via `<svg><use href="#g-<medium>"/></svg>`.
- `research/status-pill.html` — not used directly; the home question card renders a smaller meta variant inline (see §4).

### Data flow (all build-time, no JS)

| Block | Source | Selection |
|---|---|---|
| Currently rows | `data/{reading,listening,playing,watching}.yaml` | Per row: items where `status == reading/listening/playing/watching`, sort by `last_modified` desc, take 1. Hide row if empty. Hide whole widget if 4/4 empty. |
| Currently timestamp | derived | `max(last_modified)` across the rows actually shown. Hidden if widget is hidden. |
| Research strip | `where site.RegularPages "Type" "research-question"` | Filter `Params.status == active`, sort by `Params.last_modified` desc, take 2. Hide section if 0. |
| Garden strip | `where site.RegularPages "Section" "garden"` excluding `/garden/` and `/garden/graph/` | `Draft == false`, sort by `Params.last_modified` desc, take 6. Coerce string `last_modified` via `time.AsTime` (matches existing garden templates). |
| Studio strip | `where site.RegularPages "Section" "works"` excluding `/works/`, `/works/games/`, `/works/music/`, `/works/poetry/` | Newest of each medium (games/music/poetry) by `Params.last_modified` + newest remaining across all three. 4 rows max. Hide section if 0. |

### Routing

| Link | Target |
|---|---|
| Currently row "all reading →" | `/library/reading/` |
| Currently row "all listening →" | `/library/listening/` |
| Currently row "all playing →" | `/library/playing/` |
| Currently row "all watching →" | `/library/watching/` |
| Currently row title | `/garden/<note_slug>/` if present, else `canonical_url` (matches library list-row routing) |
| Research strip "All research →" | `/research/` |
| Garden strip "Browse →" | `/garden/` |
| Studio strip "All works →" | `/works/` |

---

## 2. Hero (`partials/home/hero.html`)

Replaces the current single `<p class="role">…</p>` line. Two-column grid (text + SVG mark), collapses to one column below 800px.

- `<h1>` — site title from `site.Title`. Petrona 700, 3.2rem, letter-spacing −0.02em, line-height 1.05.
- `<p class="home-hero-lede">` — copy from `_index.html`'s **new `home_lede`** frontmatter field. Petrona regular, 1.15rem, ink-soft, max ~640px.
- Hero mark SVG — 80×80, burgundy stroke via `currentColor` (auto theme-aware). Hand-authored, lives inline in the partial. Seed shape: curved paths + center dot from the mockup; user can swap later.

`description` frontmatter stays for `<meta name="description">` only; the visible lede no longer derives from it.

Mobile (≤800px): `<h1>` drops to 2.2rem, mark hides via `display: none`.

---

## 3. Currently widget (`partials/home/currently.html`)

Four rows max. Header row: pulse dot + "Currently" label + right-aligned "last modified <date>" timestamp.

```
[•] Currently                                       last modified May 6
─────────────────────────────────────────────────────────────────
reading       Invisible Cities — Italo Calvino                all reading →
listening to  Koyaanisqatsi — Philip Glass                    all listening →
playing       Outer Wilds — Mobius Digital (spoilers in notes) all playing →
watching      Severance S2 — Apple TV+                        all watching →
```

### Verb table (hard-coded in partial)

| YAML status | Visible verb |
|---|---|
| `reading` | reading |
| `listening` | listening to |
| `playing` | playing |
| `watching` | watching |

### Row rules

- Title link target: `note_slug` → `/garden/<note_slug>/` preferred; else `canonical_url`. Matches existing library list-row routing.
- Spoiler tag "(spoilers in notes)" in burgundy text: rendered only when `spoiler_level == heavy` AND `note_slug` is present. `light` does not surface.
- Right-side "all <verb> →" link routes to the matching `/library/<section>/`.

### Empty-row + empty-widget

- Build a Hugo slice of 4 candidate row dicts; filter out rows with no matching active item.
- If result is empty, the partial outputs nothing — no `<section>` tag, no whitespace.
- If non-empty, the wrapper carries `data-active-count="N"` (unused for styling in v1; future-proof for shrinking the grid).

### Timestamp

`max(last_modified)` across rows actually shown. Formatted as Hugo `time.Format "Jan 2"`. Hidden when the widget is hidden.

### Pulse dot

Static burgundy `<span>`. **No CSS keyframes in v1** — animation budget is deferred (§27 audio-pill follows the same posture).

---

## 4. Research strip (`partials/home/research-strip.html`)

Section header `<h2>What I'm chasing</h2>` + right-aligned "All research →". 2-column grid below, single column on mobile.

### Card shape (inline, ~12 lines)

```
│ • active   Procedural narrative   · 4 sub-questions · 7 garden notes
│ How do players construct meaning from procedural systems?
│ Two-to-four lines of running prose framing where my thinking is.
```

- Burgundy `border-left: 3px`, 1.25rem inner padding-left
- Meta row (Inter, 0.7rem, ink-soft): burgundy dot + `active` (burgundy, weight 600) + theme display name + `· X sub-questions · Y garden notes`
- `<h4>` question title (Petrona 600, 1.1rem)
- Framing line: `Params.summary` if present, else first content paragraph trimmed to ~140 chars

### Selection

```hugo
{{- $questions := where site.RegularPages "Type" "research-question" -}}
{{- $active := where $questions "Params.status" "active" -}}
{{- $sorted := sort $active "Params.last_modified" "desc" -}}
{{- $picks := first 2 $sorted -}}
```

Tie-break by slug on equal dates: **deferred to v1.5**. Current fixtures share dates; if the build proves non-deterministic, add a stable secondary sort.

### Theme display name

Look up the theme page by slug from `.Params.theme`:

```hugo
{{- $theme := site.GetPage (printf "/research/themes/%s" .Params.theme) -}}
{{ $theme.Title }}
```

Sub-question count + garden notes count: read from the question's frontmatter (`supporting_notes` slice already exists per spec §10).

Hide whole section if `len $picks == 0`.

---

## 5. Garden strip (`partials/home/garden-strip.html`)

Left column of the 2-column block. Header `<h2>From the Garden</h2>` + "Browse →" → `/garden/`.

### Selection

```hugo
{{- $notes := where site.RegularPages "Section" "garden" -}}
{{- $notes = where $notes "Draft" false -}}
{{- $notes = where $notes "RelPermalink" "ne" "/garden/" -}}
{{- $notes = where $notes "RelPermalink" "ne" "/garden/graph/" -}}
{{- $sorted := sort $notes "Params.last_modified" "desc" -}}
{{- $picks := first 6 $sorted -}}
```

Render via `partial "garden/note-tile.html" (dict "page" .)`. **No new tile partial** — CSS scopes the size reduction to `.home-garden-strip .garden-tile`.

Hide section if `len $picks == 0`.

---

## 6. Studio strip (`partials/home/studio-strip.html`)

Right column. Header `<h2>Lately, in the studio</h2>` + "All works →" → `/works/`.

### Selection algorithm

```
all_works = pages where Section == works
            excluding /works/, /works/games/, /works/music/, /works/poetry/
by_medium[m] = newest of all_works where Type == works-<m>, for m in {games, music, poetry}
picks = compact([by_medium.games, by_medium.music, by_medium.poetry])     # drop nils
remaining = all_works minus picks, sorted by Params.last_modified desc
picks = picks + first 1 of remaining
```

Hugo implementation: 3× `where Type == "works-<m>"` + sort + `first 1`; then re-filter `all_works` excluding the three picks by `.RelPermalink` and take the first survivor.

**Type discrimination caveat (carried from CLAUDE.md):** the works section splits `Type` to `works-games` / `works-music` / `works-poetry` via cascade. If `.Type` returns the bare `works` umbrella, fall back to checking dir name via `.File.Dir` or `.Params.medium`. **Verify on dev server before committing the strip.**

### Row shape (inline, ~15 lines)

- 32×32 `.type-badge` gradient square containing a 16×16 `<svg><use href="#g-<glyph>"/></svg>` referencing the sprite rendered once at the top of `home.html`
- `<h5>` title (Petrona 600, 0.95rem)
- Sub-line (Inter, 0.7rem, ink-soft): `<medium> · <kind/format> · <year> · <status>` — fields drop silently if missing
- Right column (Inter, 0.68rem, ink-soft): `works/<medium>` (e.g., `works/games`)

### Type → medium → glyph map

Stored in the partial as a Hugo dict (badge class derived from `medium`, glyph id matches the sprite's `<symbol id>`):

| `.Type` | `medium` (for sub-line + path) | badge class | sprite id |
|---|---|---|---|
| `works-games` | `games` | `type-badge--games` | `g-game` |
| `works-music` | `music` | `type-badge--music` | `g-music` |
| `works-poetry` | `poetry` | `type-badge--poetry` | `g-poetry` |

Sprite rendered once near the top of `layouts/home.html` (guarded by "studio strip will produce ≥1 row").

Hide section if 0 picks.

---

## 7. Layout chrome (`layouts/home.html`)

```html
{{ define "main" }}
<main class="home">
  {{ partial "home/hero.html" . }}
  {{ partial "home/currently.html" . }}

  <section class="home-essays">
    {{ /* existing essays strip — unchanged */ }}
  </section>

  {{ partial "home/research-strip.html" . }}

  <section class="home-two-col">
    {{ partial "home/garden-strip.html" . }}
    {{ partial "home/studio-strip.html" . }}
  </section>
</main>
{{ end }}
```

`border-bottom: 1px solid var(--color-rule)` on `.home-hero`, `.home-currently`, `.home-essays`, `.home-research-strip`. `.home-two-col` is last; no bottom border.

---

## 8. CSS — three new sections

### §38 home hero

`.home-hero` (grid, 720px + 1fr), `.home-hero h1` (Petrona 700, 3.2rem), `.home-hero-lede` (1.15rem, ink-soft, max 640px), `.home-hero-mark` (80×80, burgundy `currentColor`).

### §39 home Currently widget

`.home-currently`, `.home-currently-label`, `.home-currently-pulse` (7×7 burgundy circle), `.home-currently-timestamp` (right-aligned, Inter 0.7rem, ink-soft), `.home-now-line` (grid: 105px 1fr auto; dashed bottom rule between rows except last). Sub-rules: `.verb`, `.what em`, `.by`, `.spoiler` (burgundy), `.all-link` (steel).

### §40 home strips

- `.home-research-strip`, `.home-research-questions` (2-col grid), `.home-research-question` (burgundy left rail, meta, title, framing)
- `.home-two-col` (2-col grid, gap 2rem)
- `.home-garden-strip` (header + tile grid container)
- `.home-garden-strip .garden-tile` — scoped size reduction: `padding: 0.7rem 0.85rem`, `.tile-title { font-size: 0.88rem; line-height: 1.25; }`, `.tile-meta { font-size: 0.62rem; }`
- `.home-studio-strip`, `.home-work-row` (grid: auto 1fr auto), `.type-badge`, `.type-badge--games` / `--music` / `--poetry` (gradients)

### Type-badge gradients (token-based, not raw hex)

```css
.type-badge--games   { background: linear-gradient(135deg, var(--color-steel),
                       color-mix(in srgb, var(--color-steel) 60%, var(--color-burgundy))); }
.type-badge--music   { background: linear-gradient(135deg,
                       color-mix(in srgb, var(--color-steel) 70%, var(--color-burgundy)),
                       var(--color-burgundy)); }
.type-badge--poetry  { background: linear-gradient(135deg, var(--color-burgundy),
                       var(--color-steel)); }
```

Gradient endpoints resolve to ≥4.5:1 against white in both modes (existing palette guarantees individual tokens meet AA against white; `color-mix` interpolation between two AA-passing tokens is monotonic on this axis). `check-contrast.py` does not validate gradients — judgment call documented here.

### Responsive — single breakpoint

`@media (max-width: 800px)`:
- `.home-hero` → single column; `h1` → 2.2rem; mark hidden
- `.home-two-col` → single column
- `.home-now-line` → `grid-template-columns: 90px 1fr`; `.all-link` hidden
- (essay grid already collapses via existing §X rules)

---

## 9. Verification gates

### Existing CI coverage (no changes)

- `check-contrast.py` re-runs on the new CSS; no new tokens, only new consumers.
- 12 linter pairs unchanged — homepage queries data the linters already validate.
- Hugo smoke build (`hugo --minify` in `.github/workflows/hugo.yaml`) fails if any template explodes.

### No new linter pair

Rationale: every data source (research questions, garden notes, works pages, library yaml) is already gated by an existing linter. The homepage template adds no new authoring surface — only consumption. A new linter would have nothing to lint.

### Dev-server visual spot-check (mandatory)

Before merge:
- Currently widget renders 4 rows with fixture data; routing correct to `/library/<row>/` and `/garden/<note_slug>/`.
- Spoiler tag appears on Outer Wilds row (`spoiler_level: heavy`, `note_slug` present) — burgundy text. No spoiler tag on light-spoiler rows.
- Research strip shows 2 active questions; cards have burgundy left-rail, meta row legible, framing line trimmed cleanly.
- Garden strip shows 6 most-recently-tended notes; reused tile shape sized down.
- Studio strip shows 1 game + 1 music + 1 poetry + 1 fourth pick by recency; gradient badges legible; glyph SVGs render.
- Dark-mode parity for every block.
- Mobile (≤800px): hero collapses, mark hides, 2-col stacks, now-line stays readable, all-link hidden.

---

## 10. Out of scope (deferred)

| Capability | Status | Why |
|---|---|---|
| Pulse-dot animation | Static dot | §27 animation budget; matches audio-pill posture |
| Hero illustration variants (time-of-day, per-visit) | Single hand-authored mark | YAGNI |
| `data/now.yaml` driver for Currently | Build-time `max(last_modified)` from shown items | Phase 3-blocked; reassemble when elisp pipeline lands |
| Currently freshness threshold | None — show whatever's latest | Spec §10 reserves thresholds for About `/now/`, not homepage Currently |
| Pagefind / search button in header | Phase 8 | Out of phase |
| About Now widget | Phase 3 | Elisp-blocked |

---

## 11. Commit shape

Single slice branch `slice/homepage-v3`. Three logical commits:

1. **scaffold home/ partials + rewrite home.html** — hero + currently + research-strip + garden-strip + studio-strip skeletons wired in; site still builds; placeholders for data wiring.
2. **wire data into home/ partials** — selection logic, routing, empty-row hiding, theme lookup.
3. **css §38–§40** — visual polish, dark-mode parity, responsive breakpoint.

If any commit fails CI, the next commit is the fix — never amend.

---

## 12. Risk inventory

- **Hugo `sort` stability on equal-date fixtures.** Tie-break deferred unless build proves non-deterministic. If a CI rebuild shows different research-strip ordering than the previous, add a secondary sort by `.File.LogicalName`.
- **Studio strip `Type` filter.** Spec assumes `.Type` returns `works-games` / `works-music` / `works-poetry`. Verify on dev server; fall back to `.File.Dir` matching if Hugo's cascade isn't surfacing the right type.
- **Garden tile size scope leak.** If the existing `/garden/` index inherits any margin/padding bump from `.home-garden-strip`, the leak is the symptom. Spot-check both pages.

---

*End of spec.*
