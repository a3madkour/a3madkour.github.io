# Citation hover-card runtime — design

**Date:** 2026-05-12
**Phase:** 3 (org-mode pipeline, Hugo-side slice)
**Status:** spec — ready for plan

## Context

The site already has the static half of citations:

- The `cite` shortcode (`layouts/shortcodes/cite.html`) emits inline `<cite class="citation" data-cite-key="KEY"><a href="#ref-KEY">[Author Year]</a></cite>` and records used keys on page scratch.
- The `essay-references` partial (`layouts/partials/essay-references.html`) renders the references list at the bottom of any essay with citations, sourced from `data/citations.yaml`.
- CSS §13 styles `.citation` (burgundy) and `.essay-references` (including a `:target` highlight that the click-jump fallback already exercises).
- `essay.js` has a placeholder `setupCitationHook()` that only adds a `.citation-hookable` class — unused by anything else.

What's missing is the **interactive** hover-card: a small popover that shows the full citation entry without forcing the reader to leave the paragraph and scroll to the references list. The parent design spec lists this as a deferred Phase-3 feature; the cite shortcode + fixture data + CSS scaffolding were intentionally shipped early so the runtime drops in without markup changes.

`data/citations.yaml` is also the only data file in the repo without a CI linter. Garden, research, essays, filter chips, and contrast are all linted; citations is not. This slice closes that gap.

Two fixture citations exercise the runtime today (essays #1 and series part 1 — three `cite` shortcode invocations across two pages, three distinct keys in `data/citations.yaml`).

## Goals

1. Reveal full citation content without leaving the reading flow.
2. Keep the existing click-jump-to-references behavior intact (no-JS fallback and a deliberate "second tap = jump" affordance on mobile).
3. Use the rendered references list as the single source of truth for card content — no duplicate JSON blob.
4. Add the missing `notes_ref` link (in both the references list and the card) so the field stops being unused.
5. Lint `data/citations.yaml` to match the discipline applied to every other data file in the repo.
6. Stay page-narrow in the JS payload: nothing new on non-essay pages.

## Non-goals

- BibTeX export / copy-to-clipboard.
- "Cited by N other essays" backlinks (no cross-essay citation graph yet).
- Multi-citation grouping (no `[1,2,3]` cluster syntax).
- Citation rendering anywhere outside `/essays/` (garden's `roam_refs` is frontmatter metadata, not inline-rendered).
- Replacing the references list. The list stays as the no-JS fallback and the canonical destination of the click-jump.

## Architecture

### New JS module — `assets/js/citation-card.js`

Singleton card runtime. Exports `setupCitationCards()`. Imported by `essay.js` (same file that imports `filter-chips.js`). Estimated payload: ~2 KB minified, added to the existing essay bundle (`js/essay.<hash>.js`). No new bundle, no new entry point.

The module:

1. Guards on `.essay-body` presence + `.citation` count > 0; bails if either is false.
2. Injects the singleton card element once (lazily — only if a citation is interacted with).
3. Attaches one delegated `mouseenter`/`focusin` listener to `.essay-body` to catch citation events, and a small set of pointer/keyboard handlers on the card itself.

### Server-side change — `partials/essay-references.html`

When a citation entry has `notes_ref` set, the partial appends a `→ related note` link next to `→ source`. The card runtime inherits it for free via DOM-clone — no separate data attribute needed, the link element itself is the carrier.

### Existing infrastructure unchanged

- `cite` shortcode emits the same markup.
- `essay.js` deletes the obsolete `setupCitationHook()` placeholder and calls `setupCitationCards()` from the new module instead.
- CSS §13 gains a card subsection; no new tokens.

## Data flow

Card content comes from the rendered references list, not a separate data path:

```
data/citations.yaml
    ↓ (Hugo build)
essay-references.html partial
    ↓ (server-rendered)
<li id="ref-KEY">authors (year). <em>title</em>. venue. → source [→ related note]</li>
    ↓ (JS clone on open)
.citation-card-body innerHTML
```

When the user opens the card for key `KEY`, JS queries `document.getElementById('ref-' + KEY)` and clones its `innerHTML` into the card body. If the element is missing (defensive — shouldn't happen because `has_citations: true` always renders the list), the runtime no-ops on that citation and the click-jump fallback continues to work.

## Card element

One singleton per page, appended to `<body>` lazily on first interaction:

```html
<aside id="citation-card" class="citation-card" role="region" aria-label="Citation details" hidden>
  <div class="citation-card-body"><!-- cloned from #ref-KEY innerHTML --></div>
  <button class="citation-card-close" aria-label="Close citation" type="button">×</button>
</aside>
```

- `role="region"` (not `tooltip` — `role="tooltip"` is for non-interactive text only; the card has links).
- `aria-describedby` is set dynamically on the triggering `<cite>` when the card opens, and cleared on close.
- The close button is visually hidden on viewports ≥ 720px (desktop has hover-out / Esc / outside-click).
- `aria-modal` is not used — the card is a floating region, not a modal. Background content remains interactive.

## Interaction model

### Desktop, pointer (≥720px)

| Event | Effect |
|---|---|
| `mouseenter` on `.citation` | After 150ms delay, position + show card above (flip below if too close to viewport top). Fade in `opacity` 0→1 over 120ms. |
| `mouseleave` from `.citation` | Start 200ms hide timer. |
| `mouseenter` on `.citation-card` | Cancel hide timer. |
| `mouseleave` from `.citation-card` | Start 200ms hide timer. |
| Re-`mouseenter` on the originating `.citation` | Cancel hide timer. |
| `Esc` keydown | Hide immediately, return focus to triggering citation. |
| Click on `.citation > a` | Pass-through. Browser jumps to `#ref-KEY`; `:target` highlights the entry; card hides as the page scrolls and cursor leaves. |
| Click outside `.citation` + `.citation-card` | Hide. |

### Desktop, keyboard (≥720px)

| Event | Effect |
|---|---|
| `focus` on `.citation > a` | Show card immediately (no fade if `prefers-reduced-motion`, no delay either way). |
| `focusout` from `.citation > a` | If `relatedTarget` is inside the card, keep open; otherwise hide. |
| Tab inside card | Cycles through card's focusable elements (source link, related-note link if present). |
| `Esc` | Hide; return focus to triggering citation. |

### Mobile (≤720px)

The card renders as a bottom sheet rather than an anchored popover. State variable `lastActivatedKey: string | null` tracks the most recently opened citation.

| Event | Effect |
|---|---|
| First tap on `.citation` (where `lastActivatedKey !== key`) | `preventDefault()`; set `lastActivatedKey = key`; show card as bottom sheet. |
| Second tap on `.citation` (where `lastActivatedKey === key`) | Pass-through. Hide card. Browser jumps + highlights references entry. Reset `lastActivatedKey`. |
| Tap on a different `.citation` | `preventDefault()`; swap card content to new entry; update `lastActivatedKey`. No flicker (same singleton). |
| Tap on `.citation-card-close` | Hide; reset `lastActivatedKey`. |
| Tap outside `.citation` + `.citation-card` | Hide; reset `lastActivatedKey`. |

## Positioning algorithm (desktop)

On show:

1. Measure citation bounding rect + card scrollHeight.
2. Default placement: card top-edge at `citation.top - cardHeight - 8`.
3. If that falls above `viewport.scrollY + 8`, flip below: `citation.bottom + 8`.
4. Horizontal: center on citation, then clamp so `card.left >= 8` and `card.right <= viewport.width - 8`.
5. Card uses `position: absolute` with `top` and `left` set in `px`, so it scrolls with the page and stays anchored to the citation's flow position.

On viewport resize: hide the card (don't reposition — cheap and predictable).

## CSS — additions to §13

```css
.citation-card {
  position: absolute;
  z-index: 50;
  max-width: 320px;
  padding: 1rem 1.25rem;
  background: var(--color-stone);
  border: 1px solid var(--color-rule);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  font-size: var(--text-sm);
  line-height: 1.5;
  transition: opacity 120ms ease-out;
}
.citation-card[hidden] { display: none; }    /* author-side display would mask the UA rule */
.citation-card em { font-style: italic; }
.citation-card a { color: var(--color-burgundy); }
.citation-card-close {
  display: none;  /* desktop hides; mobile media query shows */
}

@media (max-width: 720px) {
  .citation-card {
    position: fixed;
    left: 8px; right: 8px; bottom: 8px;
    top: auto;
    max-width: none;
    padding: 1.25rem 1.25rem 1rem;
    box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.16);
    border-radius: 8px;
  }
  .citation-card-close {
    display: block;
    position: absolute;
    top: 0.5rem; right: 0.75rem;
    background: none; border: none;
    font-size: 1.5rem; line-height: 1; color: var(--color-ink-soft);
    cursor: pointer;
  }
}

@media (prefers-reduced-motion: reduce) {
  .citation-card { transition: none; }
}
```

No new color tokens — all values resolve through existing AAA-verified tokens (`--color-stone`, `--color-ink`, `--color-burgundy`, `--color-rule`, `--color-ink-soft`). No new contrast pairings to verify in `tools/check-contrast.py`.

## Accessibility

- ARIA: `role="region"` + `aria-label="Citation details"`. `aria-describedby` set on the triggering `<cite>` when open.
- Keyboard: full keyboard parity with pointer. Esc dismisses and restores focus. Tab cycles inside the card without focus trap (this is a floating region, not a modal — users can Tab past it).
- Reduced motion: no fade. Show/hide are instant.
- No-JS fallback: cite links still jump to references list with `:target` highlight. Documented in §13 already.
- Touch target: the close button on mobile is at least 44×44px (padded; tested in plan).
- The card never auto-opens on page load. It never steals focus.

## Linter — `tools/check_citations.py`

Validates `data/citations.yaml` shape and cross-references. CI gate.

### Required entry fields

| Field | Type | Validation |
|---|---|---|
| `authors` | list of strings | non-empty; each item non-empty |
| `year` | int | 1500 ≤ year ≤ current_year + 2 |
| `title` | string | non-empty |
| `venue` | string | non-empty |

### Optional fields

| Field | Type | Validation |
|---|---|---|
| `url` | string | must start with `http://` or `https://` if present |
| `notes_ref` | string | if present and non-empty, must resolve to `content/garden/<slug>/index.md` and that note must not be `draft: true` |

### Top-level shape

- Root must have a single key `citations:` mapping to a dict.
- Each citation key must be a string with the shape `^[a-z0-9-]+$` (lowercase kebab-case, mirroring the slug discipline elsewhere).
- Unknown fields on any entry are errors (catches typos like `year_published`).

### Reused utilities

- `parse_frontmatter` from `tools/check_fixtures.py` (already shared across all linters) — for reading garden note frontmatter when resolving `notes_ref`.
- `parse_yaml_*` family from `tools/check_fixtures.py` — for parsing `data/citations.yaml` itself (which uses flow-style mappings inside a top-level map — the same shape extension Slice 1 already added to the parser).

### Unit tests — `tools/test_check_citations.py`

Mirrors the existing test files (`test_check_garden_fixtures.py` etc.). Coverage:

1. Happy path: all three current fixtures pass.
2. Missing required field (one test per: authors, year, title, venue).
3. Empty authors list rejected.
4. Empty string in authors list rejected.
5. Year out of range (low: 1499; high: current_year + 3).
6. Year as string instead of int rejected.
7. Non-http URL rejected.
8. `notes_ref` pointing to non-existent garden slug rejected.
9. `notes_ref` pointing to draft garden note rejected.
10. Unknown field on entry rejected.
11. Bad citation key format (uppercase / underscores) rejected.

Target ~12 unit tests, all stdlib-only.

### CI wiring

`.github/workflows/hugo.yaml` gains two new gates after the existing research-links linter checks (the current last Python gate before the Hugo build step):

```yaml
- name: Verify citations
  run: python3 tools/check_citations.py
- name: Run citation linter unit tests
  run: python3 -m unittest tools/test_check_citations.py -v
```


## Fixture fix

`data/citations.yaml` entry `example-source-2` currently has `notes_ref: "example-note-slug"`, which doesn't resolve to any garden note. Change to `notes_ref: story-atoms` — that slug already exists, is non-draft, and is already used as a cross-theme bridge in the research graph (well-connected, low risk of being deleted). The change is fixture-internal; no template or runtime touches required.

## Docs

### `CLAUDE.md`

- Deferred-features table: move `Citation hover-card runtime` row from "Phase 3" to shipped, dated 2026-05-12.
- §13 CSS section description: add the card subsection ("singleton card popover; bottom-sheet on mobile").
- Commands section: add `python3 tools/check_citations.py` + `python3 -m unittest tools/test_check_citations.py -v`.
- Deployment workflow description: bump the "thirteen Python checks" count to fifteen.
- Add a Phase 3 status paragraph noting the citation slice landed; cross-link the design + plan docs.

### `MEMORY.md` + new memory file

New project memory: `project_citation_hover_card_slice.md` — short note that the slice merged, when, and what it includes.

## Out of scope (Phase 8 / later)

- Pagefind integration: citations are not search-targeted; the references list is plain HTML, which Pagefind will index for free when Phase 8 lands.
- Lightbox-style modal variant: not needed at the current scale.
- Cross-essay "cited by" backlinks: requires walking all essays at build time to compute the inverse graph. Defer until the org-mode pipeline lands real citations.

## Risks / open questions

- **DOM clone timing**: if the references list is moved or restructured later, the clone selector breaks silently. Mitigation: the runtime guards on `getElementById('ref-' + key)` returning truthy and no-ops gracefully — click-jump still works.
- **Focus on hover**: hover-trigger could surprise screen-reader users. Mitigation: hover never moves focus; focus path is purely keyboard (focus on the citation anchor → card opens via the focus path).
- **Bottom sheet on landscape phones**: 720px breakpoint is the same one used elsewhere (garden / research). Landscape phones (e.g., 812×375 iPhone in landscape) are wider than 720 and get desktop behavior; this is consistent with the rest of the site.

## Acceptance

The slice ships when:

- [ ] `citation-card.js` module renders the card on hover/focus/tap per spec, with the singleton + clone-from-DOM architecture.
- [ ] Click pass-through to references list still works; `:target` highlight preserved.
- [ ] Mobile bottom-sheet + close button + two-tap-to-jump behavior verified.
- [ ] `essay-references.html` partial emits `→ related note` link when `notes_ref` is set.
- [ ] `tools/check_citations.py` + its unit tests both pass; both wired in CI.
- [ ] Fixture `example-source-2.notes_ref` updated to `story-atoms`; linter validates it.
- [ ] No regressions in any existing linter or contrast check.
- [ ] Dev-server spot check confirms hover + click + mobile (Chrome devtools narrow viewport) all work as described.
- [ ] `CLAUDE.md` updated; new `MEMORY.md` entry written.

## Open coordination

When Phase 3's elisp pipeline arrives, `data/citations.yaml` will be overwritten with real bib data. The linter's contract is the same shape ox-hugo will produce, so the runtime + linter survive the swap without changes.
