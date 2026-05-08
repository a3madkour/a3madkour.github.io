# Tag two-tier filter — slice design

**Status:** drafted · **Date:** 2026-05-08 · **Slice:** Phase 2 polish — tag scaling
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §4.5–§4.9, §6.1–§6.6
**Predecessor slice:** `docs/superpowers/specs/2026-05-07-garden-notes-design.md` (garden — established the shared filter-chips partial this slice extends)

---

## 0. Context for future Claude sessions

This slice addresses a known scaling limit recorded in the prior session's auto-memory: the shared filter-chips partial renders every distinct tag value as a chip, which works for the current ~11-tag fixture set but breaks down visually as content grows. Once the org-mode pipeline (Phase 3) lands and authored notes start accumulating, garden's tag count is expected to settle around 30–50.

The slice introduces a two-tier model — a small curated set of **primary tags** that always render in the strip, and a larger **secondary set** accessed through a native `<details>` disclosure with live-filter search. A multi-select capability is added to the tag dimension only (other dimensions stay single-active because their values are mutually exclusive).

The same partial powers `/essays/` and `/garden/`, so both pages get the upgrade automatically. Suppression rules ensure the disclosure doesn't appear on small tag counts — small sections look identical to today.

**Decisions made during brainstorm** (expanded in §2):
- Two-tier model: curated primary chips + searchable secondary set
- Primary set sourced from `data/filter-chips.yaml` (manual curation), with an auto top-K fallback (K=10) when curation is absent
- Disclosure built on native `<details>` (matches spoiler precedent — works without JS for open/close)
- Live-filter chips with substring matching (case-insensitive); no separate suggestion dropdown — the chip set *is* the suggestion list
- Keyboard navigation: arrow keys move focus from input through visible chips; Enter toggles; Esc clears
- Multi-select within tag dimension only; flavor/stage/series/year stay single-active
- Linter validates curated tag entries against the live taxonomy

---

## 1. Slice scope

### In scope
1. Two-tier rendering in `layouts/partials/filter-chips.html` — applies only to the tag dim; primary chips inline, secondary chips wrapped inside a `<details>` element after the disclosure chip. Other dims (flavor, stage, series, year) render unchanged.
2. `data/filter-chips.yaml` config: per-section `primary_tags` list (ordered) and optional `primary_top_k` override
3. Auto-fallback: when `primary_tags` is absent or empty, partial computes top-K by note count, alphabetical for count-ties
4. Search input inside the disclosure; live substring filter on secondary chips; "No matching tags" empty state
5. Keyboard navigation: arrow keys input ↔ chips, Enter toggles, Esc clears
6. Multi-select state for the tag dimension in `assets/js/filter-chips.js`; click-to-deselect; "All" clears the entire tag selection
7. Active-secondary-tag indicator in the disclosure summary text when collapsed (e.g., `▾ More tags · calvino` or `▾ More tags · 2 active`)
8. Linter extension (`tools/check_filter_chips_config.py` + unit tests, wired into CI) — validates that every entry in `primary_tags` resolves to an existing taxonomy term in the corresponding section
9. CSS additions to `assets/css/main.css` §16 — disclosure styling, search input, secondary chip wrap, "no match" message

### Deferred (kept as visible/round-trippable hooks)
- Tag count badges on chips (e.g., `memory (4)`) — straightforward addition once content scales; not seeded as a fixture hook because chip text is the only render surface
- Tag hierarchy / parent-child grouping — would require frontmatter changes and a richer config schema; revisit if 50 secondary tags becomes unwieldy
- Synonym handling (e.g., `consolidation` ↔ `memory-consolidation`) — out of scope; org-roam aliases will surface this if needed

### Out of slice (explicit)
- Other dimensions getting two-tier treatment — flavor/stage/series/year are naturally bounded
- Tag taxonomy pages at `/tags/<slug>/` — Hugo still auto-generates these; no change
- Server-side search across notes (Pagefind) — Phase 8

---

## 2. Decisions captured during brainstorm

| Decision | Reasoning | Where it lives |
|---|---|---|
| Two-tier (primary chips + searchable secondary) over flat-with-pagination, hierarchical groups, or alphabetical buckets | Matches the user's authoring posture — curated garden, not a wiki — and keeps the resting state visually quiet. Hierarchy was rejected as premature; the tag set isn't large enough to warrant it. | `layouts/partials/filter-chips.html` |
| Native `<details>` for the disclosure rather than custom popover | Echoes the spoiler runtime in the garden slice (`shortcodes/spoiler.html`). Open/close works without JS; reduced-motion respected via CSS; no positioning/clipping bugs. | `layouts/partials/filter-chips.html` |
| Live-filter chips inside the disclosure rather than `<datalist>` or a separate combobox dropdown | Single source of truth — chips ARE the suggestion list. No styling fight with browser-native widgets. ~30 lines added to `filter-chips.js`. | `assets/js/filter-chips.js` |
| Substring match, case-insensitive | Friendlier than prefix-only; `cal` finds both `calvino` and `recall`. | `assets/js/filter-chips.js` |
| Manual curation as the primary mechanism, with a top-K auto-fallback | Curated lists make the strip stable across builds — chips don't reshuffle as content lands. Auto-fallback means the feature works out of the box on day one and on new sections without authoring overhead. | `data/filter-chips.yaml` + partial |
| K = 10 default | Chosen during brainstorm — feels like the upper bound of "scannable in one row on desktop." Configurable via `primary_top_k`. | `layouts/partials/filter-chips.html` |
| Multi-select within tag dimension; single-active for all other dims | A note has many tags but exactly one flavor and one stage. Multi-select on tag pays off the search affordance — once you can find `calvino` quickly, AND-composing with `memory` is the natural next step. Other dims have nothing to AND. | `assets/js/filter-chips.js` |
| Keyboard model: arrow-key listbox-of-buttons rather than W3C combobox pattern | Lighter ARIA surface; chips are already `<button>` elements. Input gets `aria-controls`; arrow keys move focus through visible chips. | `assets/js/filter-chips.js` |
| Linter validates `primary_tags` against the actual taxonomy | Matches the `topic_map` validation pattern from the garden slice. Stale curation = build failure rather than silent skip. | `tools/check_filter_chips_config.py` |
| Disclosure summary surfaces active secondary tags when collapsed | Otherwise an active filter is invisible to the user after they collapse — would lead to confusion ("why is the list so short?"). Format: single tag → `· calvino`; multiple → `· N active`. | `layouts/partials/filter-chips.html` + CSS |
| Single shared file `data/filter-chips.yaml` keyed by section | Future sections (research, library) can append entries; one obvious place to look. | `data/filter-chips.yaml` |

---

## 3. Architecture

### 3.1 Data flow

1. **Build time (Hugo):**
   - **The two-tier split applies only to the `tag` dim.** Other dims (flavor, stage, series, year) render as today — flat chip strip, no disclosure.
   - For the tag dim: partial reads `site.Data.filter_chips.<section>.primary_tags` if present (ordered list); otherwise iterates `.Site.Taxonomies.tags` (which yields term → `WeightedPages`), sorts by `len pages` desc with alphabetical tie-break, and takes the first K. (Pseudo-syntax — actual implementation will use `range` over the taxonomy map.)
   - Tags not in the primary list become secondary; both lists are passed into the rendered HTML as separate `<button>` runs inside one `<div class="filter-dimension" data-dim="tag">`.
   - Secondary chips live inside `<details><summary class="filter-chip is-disclosure">…</summary>…</details>`.
   - Suppression rule unchanged: dim with `<2` distinct values doesn't render at all. Additionally: if the tag dim has ≤K total values, all tags render as primary and the `<details>` element is omitted entirely.

2. **Page load (browser):**
   - `filter-chips.js` reads chip state, initializes `state` shape: `{ tag: Set<string>, flavor: 'all', stage: 'all', ... }`. Tag is the only `Set`-valued entry.
   - All chips start un-active; "All" chip is the visual default.

3. **User interaction:**
   - Click on primary chip → toggle in `state.tag` set; if set becomes empty, "All" reactivates.
   - Click on "All" → clear `state.tag` entirely.
   - Open disclosure → focus moves to search input.
   - Type in input → for each secondary chip: toggle `hidden` based on substring match against `data-key`.
   - Arrow Down from input → focus first visible secondary chip.
   - Arrow Left/Right between visible secondary chips (skipping `hidden` ones); stops at first/last visible chip — no wraparound.
   - Arrow Up from any visible secondary chip → focus returns to the search input.
   - Enter on chip → toggle in `state.tag`.
   - Esc on input → clear input value, restore all chips visible, refocus input.
   - Tab on input → moves out of the disclosure entirely (default browser behavior); chips remain reachable via Tab in their natural document order.

4. **Filter application:**
   - For each card: `cardMatches(card)` returns true iff every dim's state is satisfied.
   - For tag dim: if `state.tag.size === 0`, pass; else require every tag in `state.tag` to appear in the card's `data-tags`.
   - For other dims: existing equality check.

### 3.2 Components & boundaries

| Component | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `data/filter-chips.yaml` | Declares curated primary tags per section | — | Read by partial at build time |
| `partials/filter-chips.html` | Renders chip strip; resolves primary vs secondary; emits disclosure | `dimensions` slice (existing); `section` (new — used to look up curated config) | Static HTML |
| `assets/js/filter-chips.js` | Chip click handling; multi-select for tag dim; live-filter; keyboard nav | DOM (chip strip + cards) | Card visibility (`hidden` attr) |
| `tools/check_filter_chips_config.py` | Validates `primary_tags` entries are real taxonomy terms in their section | `data/filter-chips.yaml` + `content/<section>/*/index.md` | exit 0 / exit 1 + error messages |
| `tools/test_check_filter_chips_config.py` | Unit tests for the linter | — | Test results |

### 3.3 HTML contract (rendered)

```html
<nav class="filter-chips" aria-label="Filters">
  <div class="filter-dimension" data-dim="tag">
    <span class="filter-label">Tag</span>
    <button type="button" class="filter-chip is-active" data-dim="tag" data-key="all">All</button>
    <!-- Primary chips -->
    <button type="button" class="filter-chip" data-dim="tag" data-key="memory">memory</button>
    <button type="button" class="filter-chip" data-dim="tag" data-key="games">games</button>
    <!-- … -->
    <!-- Disclosure for secondary -->
    <details class="filter-disclosure">
      <summary class="filter-chip is-disclosure">
        <span class="filter-disclosure-label">More tags</span>
        <!-- Populated by filter-chips.js when the tag dim has active selection.
             Empty + hidden on initial render. Content: " · calvino" or " · 2 active". -->
        <span class="filter-disclosure-count" hidden></span>
      </summary>
      <div class="filter-disclosure-body">
        <input type="search" class="filter-search"
               placeholder="Search 32 more tags…"
               aria-label="Search secondary tags"
               aria-controls="filter-secondary-tag"
               autocomplete="off">
        <div class="filter-secondary" id="filter-secondary-tag">
          <button type="button" class="filter-chip" data-dim="tag" data-key="calvino" data-tier="secondary">calvino</button>
          <!-- … -->
          <p class="filter-secondary-empty" hidden>No matching tags.</p>
        </div>
      </div>
    </details>
  </div>
  <!-- Other dims (flavor, stage) unchanged -->
</nav>
```

### 3.4 State shape (JavaScript)

```js
// Before:
const state = { tag: 'all', flavor: 'all', stage: 'all' };

// After:
const state = { tag: new Set(), flavor: 'all', stage: 'all' };
// Empty Set === "All". Adding a key to the Set deactivates "All".
```

`cardHasValue(card, dim, key)` for the tag dim becomes "every key in state[dim] must be in card's data-tags." Other dims unchanged.

### 3.5 CSS additions to §16

- `.filter-disclosure { … }` — wraps `<details>`; removes default disclosure marker; click target is the summary chip
- `.filter-disclosure[open] > summary > .filter-disclosure-label::before` — flip caret glyph
- `.filter-disclosure-body { … }` — padding, dashed border, slightly recessed background
- `.filter-search { … }` — full-width input, mono font, themed border
- `.filter-secondary { display: flex; flex-wrap: wrap; gap: var(--space-1); }`
- `.filter-secondary-empty { color: var(--ink-soft); font-style: italic; }`
- Reduced-motion: no animations on `<details>` open (CSS already global; verify no transitions added)

---

## 4. Linter contract

`tools/check_filter_chips_config.py`:

1. Loads `data/filter-chips.yaml` (absent file → exit 0; auto-fallback applies at build time).
2. For each section key (`garden`, `essays`, future): if `primary_tags` present, walks `content/<section>/` to collect every distinct tag value across non-draft notes.
3. For each entry in `primary_tags`: if not in the live tag set, prints `error: data/filter-chips.yaml:<section>.primary_tags: "<entry>" is not used by any non-draft note in /<section>/`.
4. Optional `primary_top_k` must be a positive integer; otherwise error.
5. Exits 1 on any error; 0 otherwise.
6. Reuses `parse_frontmatter` from `tools/check_fixtures.py`.

Wired into `.github/workflows/hugo.yaml` as the sixth Python check before Hugo build:

> Verify CSS contrast → Verify essay fixtures → Run essay linter unit tests → Verify garden fixtures → Run garden linter unit tests → **Verify filter-chips config** → **Run filter-chips linter unit tests** → Build with Hugo

---

## 5. Edge cases

| Case | Behavior |
|---|---|
| `data/filter-chips.yaml` absent | All sections fall back to top-10 auto-mode |
| Section absent from config | That section falls back to top-K auto-mode |
| `primary_tags: []` | Empty list = same as absent → auto-fallback |
| Curated list contains a stale tag (no live notes use it) | Linter fails build with named tag and section |
| Tag dim has fewer than K total tags | All tags render as primary; disclosure suppressed (no secondary chips) |
| Tag dim has fewer than 2 total tags | Whole dim suppressed (existing rule, unchanged) |
| User selects 3 tags, then clicks "All" | All 3 deselect; tag dim returns to "All"-active visual |
| User selects a secondary tag, then collapses disclosure | Disclosure summary shows `▾ More tags · <tagname>` (or `· N active` for ≥2); chip stays in `state.tag` |
| User types a query, then closes disclosure without selecting | Input value persists (cheap memory). On reopen, search state is preserved; chip visibility re-applied |
| User types a query that matches a primary tag | Primary chips are not affected by search input — only secondary chips inside the disclosure filter. (This avoids the visual pop of primary chips disappearing under the user's hand.) |
| JS disabled | `<details>` open/close works (native). Search input is inert. Chip click does nothing — same as today. |
| `prefers-reduced-motion` | No animations introduced; `<details>` toggles instantly |
| Mobile (<480px) | Primary chips wrap to multiple lines (existing behavior). Disclosure body wraps the same way. Tested at 320px width minimum. |
| Two tags with equal note count in auto-fallback | Sort alphabetically — deterministic across builds |
| New section added later (research, library) | Just add a key in `data/filter-chips.yaml`; no code changes |

---

## 6. Acceptance criteria

- [ ] `/garden/` and `/essays/` indexes render the disclosure when total tag count > K (currently they won't, since fixtures are below threshold; verify by temporarily lowering K in dev)
- [ ] With JS disabled, the disclosure opens and closes correctly; chips inside are visible but inert
- [ ] Substring search filters secondary chips correctly (`cal` → `calvino`, `recall`)
- [ ] Arrow Down from search input moves focus to first visible chip
- [ ] Arrow Left/Right between visible chips skips hidden ones
- [ ] Esc clears search and refocuses input
- [ ] Multi-select tag works: clicking `memory` then `narrative` shows only notes with both
- [ ] Clicking active chip deselects it
- [ ] Clicking "All" clears tag selection
- [ ] Active secondary tags are reflected in the disclosure summary when collapsed
- [ ] Linter rejects a stale curated tag in `data/filter-chips.yaml`
- [ ] Linter unit tests pass (`python3 -m unittest tools/test_check_filter_chips_config.py -v`)
- [ ] CI build green
- [ ] WCAG contrast unchanged (no new color tokens)
- [ ] Reduced-motion: no animations introduced

---

## 7. Out-of-scope reminders

- This slice does not add tag count badges, tag hierarchies, synonyms, or server-side search.
- This slice does not change the visual treatment of `/tags/<slug>/` Hugo-generated taxonomy pages.
- This slice does not introduce new color tokens or change the contrast ratios verified by `tools/check-contrast.py`.

---

## 8. Open questions for the implementation plan

(None blocking — all design decisions are resolved. The plan should sequence: config schema → partial refactor → JS state shape change → keyboard nav → linter + tests → CSS → fixture verification.)