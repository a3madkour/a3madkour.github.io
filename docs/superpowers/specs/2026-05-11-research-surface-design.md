# Research surface (Slice 1) — slice design

**Status:** drafted · **Date:** 2026-05-11 · **Slice:** Phase 5 part 1 — research surface layouts + fixtures + cross-references
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §4.10–§4.12
**Successor slice (deferred):** research force-directed graph runtime (Slice 2)

---

## 0. Context for future Claude sessions

Phase 5 adds the third major content surface to the site, after essays (Phase 2) and garden (Phases 2 + 4). The parent spec §4.10–§4.12 covers three page types — `/research/` index, `/research/themes/<slug>/`, `/research/questions/<slug>/` — plus an "Open graph" toggle on the index that reveals a force-directed research graph. This slice ships everything except the graph. The graph and its toggle are a separately-spec'd Slice 2 follow-up.

Currently `content/research/` is a stub: a single `_index.md` with `(Coming soon.)` as the body. No layouts, no fixtures, no linters. The top nav has `Research` as item 3 of 5; it currently routes to a sad placeholder page. This slice replaces all of that with a working surface.

The surface design follows the patterns already established by the essays and garden slices: realistic-named fixture set with filler bodies, explicit frontmatter contracts validated by Python linters in CI, hand-authored SVG icons matching the stage-glyph pattern, and round-trippable structure that the org-mode pipeline (Phase 3) will populate without template changes.

**Decisions made during brainstorm** (expanded in §2):
- Two slices total. This slice = layouts + fixtures + cross-refs + linters. The graph + graph data partial = Slice 2.
- Fixture set is 3 themes + 6 questions, sized to exercise every variant.
- Cross-references are explicit lists in frontmatter (`parent_question`, `supporting_notes`, `related_essays`, `garden_topic_ref`); siblings + sub-questions computed by Hugo `where`; backlinks computed at build time via internal-link extraction (`partialCached` data partial, same pattern as `partials/garden/graph-data.html`).
- "Open graph" toggle on `/research/` is omitted entirely in Slice 1 (no inert button, no stub page).
- Type-discrimination via `cascade: { type: research-theme }` and `cascade: { type: research-question }` on the section `_index.md`s. The bare section pages (`/research/themes/` and `/research/questions/`) are hidden with `_build: { render: false }`.
- Two new linters: `check_research_fixtures.py` (frontmatter contract) + `check_research_links.py` (cross-reference resolution). Both stdlib-only, both wired into the GitHub Actions workflow.

---

## 1. Slice scope

### In scope

1. **Frontmatter contracts** for themes and questions (§3.1).
2. **Three layouts**:
   - `layouts/research/list.html` — `/research/` index page (theme cards grid + tag filter chips, no graph toggle).
   - `layouts/research-theme/single.html` — `/research/themes/<slug>/` (research framing + optional garden-topic embed when `garden_topic_ref` is set).
   - `layouts/research-question/single.html` — `/research/questions/<slug>/` (full question hub).
3. **Four partials**:
   - `partials/research/backlinks-data.html` — build-time JSON keyed by question slug, computed by walking essays + garden + research and extracting internal `/research/questions/<slug>/` references via `findRE`. `partialCached`.
   - `partials/research/theme-card.html` — single theme card markup used by the index grid (and reusable wherever a theme card might appear later).
   - `partials/research/output-item.html` — single output entry (kind-icon + title + year + link), takes a `{kind, title, url, year}` dict.
   - `partials/research/status-pill.html` — small badge component for active/dormant/answered. Color uses existing palette tokens (`--color-burgundy` active, `--color-warn` dormant, `--color-green` answered).
4. **Hand-authored SVG icons** for output kinds, in `assets/images/icons/`:
   - `output-paper.svg` — document with horizontal text lines.
   - `output-talk.svg` — podium / speaker bubble.
   - `output-code.svg` — angle brackets.
   Same conventions as the stage glyphs (`currentColor` stroke, ~24×24 viewBox, hand-drawn vibe).
5. **CSS §30 "Research"** in `assets/css/main.css`. New classes for the index grid, theme card, theme page sections, question hub layout, status pill, three-column questions block on theme pages, outputs list, sub-questions / siblings / backlinks lists.
6. **Fixtures**:
   - 3 themes (§3.2 — `memory-and-play` / `procedural-narrative` / `save-game-as-form`).
   - 6 questions (§3.2 — one with a `parent_question` sub-relation to another, one with no `supporting_notes`/`related_essays` to exercise empty-state, etc.).
   - All bodies are obvious filler (lorem-ipsum, "Example N" — never authored prose).
7. **Section infrastructure**:
   - `content/research/_index.md` replaces the stub with real frontmatter (no body, no "Coming soon").
   - `content/research/themes/_index.md` — cascade + `_build: render: false`.
   - `content/research/questions/_index.md` — cascade + `_build: render: false`.
8. **Two new CI gates**:
   - `tools/check_research_fixtures.py` + `tools/test_check_research_fixtures.py`.
   - `tools/check_research_links.py` + `tools/test_check_research_links.py`.
   - Both imported from `tools/check_fixtures.py`'s `parse_frontmatter` (shared with garden linters).
9. **GitHub Actions workflow update** — add the new linter steps to `.github/workflows/hugo.yaml` (matches the existing 9-check pattern, becomes 11).
10. **CLAUDE.md update** — Architecture section (layouts list, partials list, fixture contract, CSS §30 mention); Project status section (Phase 5 surface complete, graph deferred to Slice 2).

### Deferred (kept as round-trippable hooks)

| Item | Hook in Slice 1 | What Slice 2 adds |
|---|---|---|
| Force-directed research graph | None (no graph runtime, no graph data partial) | New runtime `assets/js/research-graph.js` mirroring `garden-graph.js`; new partial `partials/research/graph-data.html`; multi-entry bundle gets a `research` entry; CSS extends §30. |
| "Open graph" toggle button on `/research/` | Omitted | Re-rendered in the filter chip strip via a new template branch. |
| Mobile-specific graph fallback (a `/research/graph/` standalone page) | None | Mirrors `/garden/graph/`. |
| Citation hover-card runtime referenced in supporting-notes section | Not in Slice 1 scope; same site-wide placeholder | Phase 3 / later |
| KaTeX math in question current-thinking bodies | Not in Slice 1 scope; same site-wide placeholder | Phase 3 / later |

### Out of slice (explicit)

- The graph itself, including any new JS module, vendored d3 changes, or graph data partial.
- Any homepage cross-link or Currently strip wiring (Phase 7).
- Library cross-links from research (Phase 7).
- A `/research/series/` or `/research/themes/<slug>/timeline/` — not in parent spec.
- Frontmatter coercion or org-mode pipeline integration. The frontmatter contract is fixed in §3.1 so ox-hugo can target it (Phase 3), but no actual elisp work happens here.

---

## 2. Decisions captured during brainstorm

| Decision | Reasoning | Where it lives |
|---|---|---|
| Two slices (surface first, graph later) over one big slice | The surface is the visual + content payload; the graph is interactive runtime mirroring garden-graph. Splitting lets the surface ship + be reviewed before adding 95 KB of d3 to the page-weight conversation. | This spec is Slice 1 only; Slice 2 gets its own spec when we're ready. |
| 3 themes / 6 questions fixture set over a 5-theme / 10-question maximum or a 2-theme / 3-question minimum | 3+6 hits every variant exactly once (with/without garden_topic_ref, all 3 statuses, with/without supporting_notes/related_essays/outputs, top-level vs sub-question). A larger set adds maintenance overhead without new coverage. | §3.2 |
| Explicit lists in frontmatter (`supporting_notes`, `related_essays`, `parent_question`) over tag-derived linkage | Captures author intent; matches `topic_map:` precedent in garden; matches what ox-hugo will write from org-roam IDs. Tag-derived would be noisy (broad tags pull too much). | §3.1 |
| Backlinks computed via build-time internal-link extraction over explicit declarations | Symmetric with garden's link extraction; doesn't require essays/garden notes to declare which research questions they support; surfaces ambient mentions. | §3.3 backlinks |
| "Open graph" toggle omitted from Slice 1 over showing inert / stub | Inert buttons confuse readers. A stub page would be throw-away code in Slice 2. Omitting is cleanest; Slice 2 adds the button when the runtime is ready. | `layouts/research/list.html` has no graph toggle |
| Type-discrimination via `cascade: { type: research-theme }` + `cascade: { type: research-question }` over per-page `type:` declarations | Less repetition in fixture frontmatter; Hugo's section-based layout lookup doesn't distinguish nested subdirectories so a type override is needed; cascade is the cleanest way. | `content/research/themes/_index.md`, `content/research/questions/_index.md` |
| Bare section pages (`/research/themes/`, `/research/questions/`) hidden with `_build: render: false` over rendering them as list pages | Users never navigate to those URLs in the design (they enter via /research/ → card → hub). Letting them 404 keeps the URL space honest. | §3.4 |
| Reuse `partials/garden/topic-section.html` for the embedded garden topic on theme pages over duplicating the tile-grid renderer | The garden tile renderer already exists, is tested via fixtures, and produces the exact visual the spec calls for (parent §4.11). Re-use is free. | `layouts/research-theme/single.html` |
| Two new linters (fixtures + cross-refs) over one or none | Matches the garden precedent (`check_garden_fixtures.py` + `check_garden_links.py`). Fixture contract catches authoring bugs; cross-ref linter catches dangling references at CI time, not at runtime. | `tools/check_research_*.py` |
| Three output kinds (paper / talk / code) over an open string field | Closed enum the linter can validate; matches the spec's three icons. Easy to extend later if we want poster/blog/dataset. | §3.1 question frontmatter |

---

## 3. Architecture

### 3.1 Frontmatter contracts

**Theme** (`content/research/themes/<slug>/index.md`):

```yaml
---
title: "Memory and play"
status: active                        # active | dormant | answered
tags: [memory, play]                  # list, may be empty
last_modified: 2026-05-11
description: "Short framing for the card and theme-page hero."
weight: 10                            # ordering; lower = earlier
# optional:
garden_topic_ref: memory-in-play      # slug of an existing garden note that has topic_map declared
summary: "Optional 1-2 sentence longer summary shown on the theme page hero."
---
```

**Question** (`content/research/questions/<slug>/index.md`):

```yaml
---
title: "How do readers form narrative from shuffle?"
theme: memory-and-play                # required, slug of an existing theme
status: active                        # active | dormant | answered
last_modified: 2026-05-11
description: "Short framing for cards and search results."
# optional:
parent_question: ""                   # slug of another question in the same theme — makes this a sub-question
started: 2025-09-01
tags: [memory, narrative]
supporting_notes: [story-atoms, salience-and-memory]   # garden slugs
related_essays: [example-essay-one]                     # essay slugs
outputs:
  - { kind: paper, title: "Title", url: "https://...", year: 2025 }
  - { kind: talk,  title: "Title", url: "https://...", year: 2024 }
weight: 10
---
```

**Linter contract** (`check_research_fixtures.py`):
- Required keys present and non-empty on themes: `title, status, tags, last_modified, description, weight`.
- Required keys present and non-empty on questions: `title, theme, status, last_modified, description`.
- `status ∈ {active, dormant, answered}` on both.
- `tags`, if present, is a list of strings.
- `outputs[].kind ∈ {paper, talk, code}`; `outputs[].year` is a 4-digit integer; `outputs[].title` and `outputs[].url` are non-empty strings.
- Themes do not declare `parent_question` (question-only field).
- Themes do not declare `theme` (would be circular).
- `weight`, if present, is an integer.

**Cross-ref linter contract** (`check_research_links.py`):
- A theme's `garden_topic_ref`, if set, resolves to an existing non-draft garden note that has `topic_map` declared.
- A question's `theme` resolves to an existing theme.
- A question's `parent_question`, if set, resolves to an existing question in the same theme.
- Every entry in a question's `supporting_notes` resolves to a non-draft garden note.
- Every entry in a question's `related_essays` resolves to a non-draft essay page.

### 3.2 Fixture set

**3 themes** (`content/research/themes/<slug>/index.md`, plus filler body):

| slug | status | `garden_topic_ref` | tags | weight |
|---|---|---|---|---|
| `memory-and-play` | active | `memory-in-play` | [memory, play] | 10 |
| `procedural-narrative` | dormant | `procedural-narrative` | [narrative, procedural] | 20 |
| `save-game-as-form` | answered | *(unset)* | [aesthetics, games] | 30 |

**6 questions** (`content/research/questions/<slug>/index.md`, plus filler body):

| slug | theme | status | `parent_question` | `supporting_notes` | `related_essays` | `outputs` |
|---|---|---|---|---|---|---|
| `how-do-readers-form-narrative-from-shuffle` | `memory-and-play` | active | — | `story-atoms`, `salience-and-memory` | `example-essay-one` | 1 paper, 1 talk |
| `what-counts-as-story-recall` | `memory-and-play` | active | `how-do-readers-form-narrative-from-shuffle` | `recall-vs-replay` | — | — |
| `when-does-replay-feel-like-cheating` | `memory-and-play` | dormant | — | — | — | — |
| `can-procedural-text-have-a-throughline` | `procedural-narrative` | dormant | — | `procedural-narrative` | — | — |
| `what-is-a-narrative-atom` | `procedural-narrative` | active | — | `story-atoms` | `example-essay-two` | — |
| `when-is-a-save-an-edit` | `save-game-as-form` | answered | — | `the-save-game` | `example-essay-three` | 1 paper, 1 code |

The set exercises:
- All 3 theme statuses (active / dormant / answered).
- Theme with `garden_topic_ref` (memory-and-play, procedural-narrative) and without (save-game-as-form).
- All 3 question statuses.
- Top-level question (5 of 6) and sub-question (`what-counts-as-story-recall` has `parent_question`).
- With + without `supporting_notes` (one question has none).
- With + without `related_essays` (three questions have none).
- With + without `outputs` (two questions have outputs).
- All 3 output kinds: paper (×2), talk (×1), code (×1).

Filler bodies follow the established `Example N. Lorem ipsum dolor sit amet...` pattern from essays/garden.

### 3.3 Page structures

#### `/research/` (index) — `layouts/research/list.html`

```
.reading-column.research-page

  Hero section:
    h1 "Research"
    framing paragraph (from .Content of content/research/_index.md, OR a fallback if .Content is empty)

  Filter strip (uses the shared partials/filter-chips.html):
    Tag dim — primary chips of every tag declared across the 3 themes
    No flavor / no status filter for v1 (themes have status but it's not a filter dim)
    No "Open graph" toggle (Slice 2 adds it)

  .research-grid (2 cols desktop, 1 col mobile):
    For each theme (sorted by .Params.weight, then .Title):
      partial "research/theme-card.html" — see §3.4
```

#### `/research/themes/<slug>/` — `layouts/research-theme/single.html`

```
.reading-column.research-theme-page

  Breadcrumb: <a href="/research/">Research</a> › <span>{{ .Title }}</span>

  Hero:
    h1 .Title
    status pill (.status-pill .status-{active|dormant|answered})
    p .description
    if .Params.summary: p .summary
    if .Params.garden_topic_ref: cross-link
        "↗ also at <a href="/garden/{{ .Params.garden_topic_ref }}/">/garden/{{ .Params.garden_topic_ref }}/</a>"

  Three-column block .three-col-questions:
    Iterate questions where Params.theme == this theme's slug, group by status:
      Active questions: <h3>Active</h3> + ul of question titles linked to /research/questions/<slug>/
      Dormant questions: <h3>Dormant</h3> + ul
      Answered questions: <h3>Answered</h3> + ul
    Omit a column if empty.

  Aggregated outputs section .outputs-list (only if any questions in this theme have outputs):
    h2 "Outputs"
    Iterate child questions' outputs, flatten, sort by year desc:
      partial "research/output-item.html" (passing the {kind, title, url, year} dict)

  Garden topic embed (only if .Params.garden_topic_ref is set):
    h2 "From the Garden"
    Render the topic_map tile grid via partials/garden/topic-section.html, passing the
    referenced garden page as the "context" argument. This re-uses the garden tile
    renderer end-to-end — same visual as /garden/'s topic sections.
```

#### `/research/questions/<slug>/` — `layouts/research-question/single.html`

```
.reading-column.research-question-hub

  Breadcrumb: <a href="/research/">Research</a> › <a href="/research/themes/{{ .Params.theme }}/">{{ theme.Title }}</a> › <span>{{ .Title }}</span>

  Status strip .status-strip:
    status pill
    "Last tended: <time>{{ .Params.last_modified }}</time>"
    if .Params.started: "Started: <time>{{ .Params.started }}</time>"
    tag list (small chips, no filtering — just visual context)

  Question statement .question-statement:
    h1 .Title (rendered large, Petrona italic, same vibe as essay h1)

  Current thinking section:
    h2 "Current thinking"
    .Content (the markdown body — filler in fixtures, real prose later)

  Sub-questions (only if any exist where parent_question == this question's slug):
    h2 "Sub-questions"
    ul of sub-question {title} + {description}, linked

  Sibling questions (only if any exist; computed as same theme, not this question, not the current question's parent_question target, and not a question whose parent_question is this slug):
    h2 "Sibling questions"
    ul of question titles, linked, with status pill inline
    (Omitted entirely — heading and all — when empty, e.g. on save-game-as-form's single question.)

  Supporting Garden notes (only if .Params.supporting_notes is non-empty):
    h2 "Supporting notes"
    .garden-tiles grid — re-use partials/garden/note-tile.html for each slug

  Related essays (only if .Params.related_essays is non-empty):
    h2 "Related essays"
    ul of essay cards (re-use partials/essay-card.html OR a compact list using partials/essay-meta.html — to be decided in the plan; design intent is a list with date + reading time + tags)

  Outputs (only if .Params.outputs is non-empty):
    h2 "Outputs"
    ul of partials/research/output-item.html

  Backlinks (always rendered; shows "No backlinks yet" if empty):
    h2 "Backlinks"
    Read partials/research/backlinks-data.html (JSON), look up this question's slug,
    render the list of backlinking pages: {kind icon} {title} {url}
```

### 3.4 Component partials

**`partials/research/theme-card.html`** — takes a theme page as argument.
```
<article class="research-card" data-theme-slug="{{ slug }}">
  partial "research/status-pill.html" with theme.Params.status
  <h2><a href="{{ theme.RelPermalink }}">{{ theme.Title }}</a></h2>
  {{ if theme.Params.garden_topic_ref }}
    <span class="research-card-badge">↗ also a Garden topic</span>
  {{ end }}
  <p class="research-card-description">{{ theme.Params.description }}</p>
  <ul class="research-card-tags">…tags…</ul>
  <div class="research-card-counts">
    Iterate questions where theme matches; count by status:
    {{ active }}/{{ dormant }}/{{ answered }} questions ·
    {{ supporting }} supporting notes (sum of unique slugs across this theme's questions' supporting_notes)
  </div>
</article>
```

**`partials/research/status-pill.html`** — takes a status string ("active" | "dormant" | "answered").
```
<span class="status-pill status-{{ . }}">{{ . }}</span>
```

Color mapping (in CSS §30):
- `.status-active` → `--color-burgundy`
- `.status-dormant` → `--color-warn` (yellow/orange)
- `.status-answered` → `--color-green`

**`partials/research/output-item.html`** — takes a dict `{kind, title, url, year}`.
```
<li class="output-item output-item-{{ .kind }}">
  <span class="output-icon" aria-hidden="true">
    {{ with resources.Get (printf "images/icons/output-%s.svg" .kind) }}{{ .Content | safeHTML }}{{ end }}
  </span>
  <a href="{{ .url }}" class="output-title">{{ .title }}</a>
  <span class="output-year">{{ .year }}</span>
</li>
```

**`partials/research/backlinks-data.html`** — `partialCached`, returns JSON.
```
{{ $backlinks := dict }}
{{ range site.RegularPages }}
  {{ $raw := .RawContent }}
  {{ range findRE `/research/questions/([a-z0-9][a-z0-9-]*)/` $raw }}
    {{ $slug := replaceRE `^/research/questions/(.*)/$` "$1" . }}
    {{ ... append to $backlinks[$slug] ... }}
  {{ end }}
{{ end }}
{{ return $backlinks | jsonify }}
```

The exact Hugo template syntax for the scratchpad-like accumulation is for the plan to nail down (Hugo's dict mutation is cumbersome but doable via `merge`). The contract is: JSON dict keyed by question slug, value is `[{title, url, kind}]` where `kind ∈ {"essay", "garden", "question"}`. Question hub template parses the JSON via `index $data $thisSlug`.

### 3.5 CSS additions — §30 "Research"

Roughly 150–200 lines. Sections:

- `.research-page` — index wrapper.
- `.research-grid` — 2-col → 1-col responsive grid.
- `.research-card` + sub-elements (`.research-card-description`, `.research-card-tags`, `.research-card-counts`, `.research-card-badge`).
- `.research-theme-page` — theme page wrapper.
- `.research-theme-page .breadcrumb` — small text, secondary color.
- `.three-col-questions` — three-column inner block, responsive.
- `.outputs-list` — flat list of output items.
- `.output-item` + `.output-icon` + `.output-title` + `.output-year`.
- `.research-question-hub` — question hub wrapper.
- `.research-question-hub .status-strip` — top strip with pill + dates + tags.
- `.question-statement` — large italic Petrona heading style.
- `.research-sub-questions`, `.research-siblings`, `.research-backlinks` — list styling.
- `.status-pill` + `.status-active` / `.status-dormant` / `.status-answered` — colored badges. May reuse existing garden status-pill classes if compatible (review during plan-writing).

No contrast verifier change needed — the status pill colors use existing palette tokens already verified.

### 3.6 Hugo lookup

`content/research/themes/<slug>/index.md` inherits `type: research-theme` from `content/research/themes/_index.md`'s `cascade`. Hugo lookup resolves to `layouts/research-theme/single.html`. Same mechanism for questions → `layouts/research-question/single.html`. The `/research/` index uses default section-based lookup → `layouts/research/list.html`.

The bare section pages (`/research/themes/`, `/research/questions/`) declare `_build: { render: false }` in their `_index.md`, so they aren't generated. Hugo's `RegularPages` collection still includes the child pages; only the section list pages are suppressed.

---

## 4. Anticipated org-mode contract (Phase 3 round-trip)

When the org-mode pipeline lands, each theme is one org-roam node + an `ox-hugo` export target; each question is another. The exporter writes the frontmatter contracts in §3.1 directly. Specifically:

- `parent_question` is resolved from `:ROAM_REFS:` to a slug.
- `supporting_notes` is resolved from explicit links inside the question's org body that match a particular pattern (e.g. `:type:supporting` or a property drawer entry).
- `related_essays` is resolved the same way.
- `outputs` is built from a property drawer block in the org file.

The layouts written in this slice consume the contract as-is. No template changes are needed when the pipeline lands; the fixture frontmatter is simply replaced with org-exported frontmatter, and the body markdown becomes real prose. Backlinks recompute automatically because they're built from `.RawContent` scanning.

---

## 5. Files touched

**New layouts:**
- `layouts/research/list.html`
- `layouts/research-theme/single.html`
- `layouts/research-question/single.html`

**New partials:**
- `layouts/partials/research/backlinks-data.html`
- `layouts/partials/research/theme-card.html`
- `layouts/partials/research/output-item.html`
- `layouts/partials/research/status-pill.html`

**New SVG icons:**
- `assets/images/icons/output-paper.svg`
- `assets/images/icons/output-talk.svg`
- `assets/images/icons/output-code.svg`

**Modified:**
- `assets/css/main.css` — append §30 "Research"
- `content/research/_index.md` — replace `(Coming soon.)` body with frontmatter-only file (or a small framing paragraph, decided at plan time)
- `.github/workflows/hugo.yaml` — add the two new linter steps (fixtures + cross-refs), bringing the gate count from 9 to 11
- `CLAUDE.md` — Architecture section (layouts, partials, fixtures, CSS §30); Project status section (Phase 5 surface complete; graph deferred)

**New content fixtures:**
- `content/research/themes/_index.md` — cascade + render: false
- `content/research/questions/_index.md` — cascade + render: false
- `content/research/themes/memory-and-play/index.md`
- `content/research/themes/procedural-narrative/index.md`
- `content/research/themes/save-game-as-form/index.md`
- `content/research/questions/how-do-readers-form-narrative-from-shuffle/index.md`
- `content/research/questions/what-counts-as-story-recall/index.md`
- `content/research/questions/when-does-replay-feel-like-cheating/index.md`
- `content/research/questions/can-procedural-text-have-a-throughline/index.md`
- `content/research/questions/what-is-a-narrative-atom/index.md`
- `content/research/questions/when-is-a-save-an-edit/index.md`

**New tools (CI gates):**
- `tools/check_research_fixtures.py` + `tools/test_check_research_fixtures.py`
- `tools/check_research_links.py` + `tools/test_check_research_links.py`

**Not touched:**
- `hugo.yaml` (Hugo lookup resolves everything via type + cascade)
- `data/` (research has no data files in Slice 1)
- `assets/js/` (no JS in Slice 1; graph is Slice 2)
- Garden / essays / about layouts (cross-references read; layouts don't change)
- `tools/check_fixtures.py` (imported from; not modified)
- The existing 5 linters (`check_contrast.py`, `check_fixtures.py`, `check_garden_fixtures.py`, `check_garden_links.py`, `check_filter_chips_config.py`)

---

## 6. Acceptance criteria

1. Visiting `/research/` renders the hero, the tag filter chips (with at least 4 distinct tags from the fixture set), and a 2-column grid of 3 theme cards.
2. Each theme card shows title, description, status pill, tag list, optional "↗ also a Garden topic" badge (visible on `memory-and-play` and `procedural-narrative`, absent on `save-game-as-form`), and the questions counts + supporting-notes count.
3. Visiting `/research/themes/memory-and-play/` shows the breadcrumb, hero, three-column questions block (Active = 2 questions, Dormant = 1, Answered = 0; the Answered column is omitted), aggregated outputs (1 paper + 1 talk from the one question that has outputs), and a "From the Garden" tile grid populated from the `memory-in-play` topic_map.
4. Visiting `/research/themes/save-game-as-form/` shows the breadcrumb, hero, three-column questions block (Active = 0, Dormant = 0, Answered = 1), aggregated outputs (1 paper + 1 code), and **no** "From the Garden" section.
5. Visiting `/research/questions/how-do-readers-form-narrative-from-shuffle/` shows the breadcrumb (Research › Memory and play › ...), status strip with active pill + dates + tags, large question statement, "Current thinking" prose (filler), "Sub-questions" with `what-counts-as-story-recall`, "Sibling questions" with `when-does-replay-feel-like-cheating` (the only same-theme question that isn't this question's child), "Supporting notes" tile grid (2 tiles), "Related essays" list (1 entry), "Outputs" list (1 paper + 1 talk with the appropriate icons), and a "Backlinks" section. Backlinks may be empty if no fixture body references this question's URL; if so, the section renders "No backlinks yet" (always rendered, unlike the other optional sections).
6. Visiting `/research/questions/when-does-replay-feel-like-cheating/` shows the question hub with **empty** supporting-notes, related-essays, and outputs sections (the section headings are omitted, not empty-stated, when there's no data).
7. `python3 tools/check_research_fixtures.py` exits 0 and prints `All research fixtures pass linter.`
8. `python3 tools/check_research_links.py` exits 0 and prints something like `OK — verified 3 theme(s), 6 question(s).`
9. Both new linters have unit tests covering: required field missing, invalid status enum, invalid output kind, dangling `parent_question`, dangling `supporting_notes` slug, dangling `related_essays` slug, theme `garden_topic_ref` pointing at a non-topic-map garden note, question whose `parent_question` points at a question in a different theme.
10. All 11 CI gates in `.github/workflows/hugo.yaml` pass (5 original + 2 new pairs = 9 → 11; the count quoted in CLAUDE.md updates to "all eleven Python checks").
11. `hugo --minify` builds cleanly (modulo the pre-existing `.Site.Data` deprecation warning).
12. CSS contrast verifier still passes — no new contrast pairs introduced (the status-pill colors use already-verified palette tokens).
13. `/research/`, `/research/themes/*/`, `/research/questions/*/` all load only the `core.<hash>.js` bundle. No essay or garden JS leaks into the research surface; no new bundle is introduced (the graph runtime that needs its own bundle is Slice 2).
14. The two bare section URLs `/research/themes/` and `/research/questions/` return 404 (because `_build: render: false`).

---

*End of spec.*
