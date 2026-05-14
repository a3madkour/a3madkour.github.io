# Garden path-log retrieval — design

**Phase:** Post-Phase-8 polish slice (standalone). Not Phase 3 elisp work.
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §5.6 (path log).
**Filed:** 2026-05-13 (originally as a stub during Phase 8 Slice 3 QA; promoted to full design 2026-05-13).

---

## 1. Problem

The garden persists a visited-notes list in `localStorage['garden-path-log']` (or `sessionStorage`) capped at 100 entries, gated by a 3-state consent banner (`yes / session / no / unset`). The data is **written and never read**: no surface in the site consumes it, so the consent banner asks users to opt into a persistence layer that has no payoff.

Two additional shortcomings of the existing storage:

- **Flat-slug schema, no boundaries.** Today's data is `["slug-a", "slug-b", "slug-c", …]` — a flat append-ordered list. There is no way to tell which slugs belong to which reading session, because session boundaries (page reload, stack root change) are not recorded. The data names which notes were touched, not which *paths* were walked.
- **No timestamps.** Recent-vs-old can only be inferred from array position. No "yesterday" / "last week" surfacing is possible.

For a Zettelkasten-style garden, the *path* (the sequence of links the user followed) is the interesting unit, not the bag of slugs. This slice both adds consumers AND upgrades the storage schema to preserve path structure.

## 2. Goals

- Add **two** consumer surfaces: a "Recent paths" widget on `/garden/` and a popover off the path-log strip on note pages (desktop only). Both render *paths* (slug chains with `›` arrows + relative-time stamps), not flat slug lists.
- Add a **third** surface: a dedicated `/garden/history/` page reached from a chrome link in the path-log strip and from the widget's "Reading history →" link. Shows all stored sessions (up to 20).
- Upgrade the persistence schema from v1 (flat slug array) to v2 (sessions with timestamps), with one-shot migration of any existing v1 data.
- Honor the existing privacy stance (no analytics, no external services, data lives in the user's browser only). The consent banner gains real payoff.
- Add a CI linter pair gating the new files + integration points.

## 3. Non-goals

- **A "Re-enable tracking" affordance on the consent banner itself.** The banner only shows when `consent === 'unset'`. Re-enabling lives on the `/garden/history/` empty-state for `consent === 'no'` (a small button that sets consent back to `unset` so the banner reappears the next time the user grows a stack).
- **Cross-device sync.** The site has no auth; storage is local-only. Out of scope indefinitely.
- **Timeline graph view** of visited notes. Visual nicety; deferred.
- **Editing the visited list** (e.g., "remove this note from history"). Brainstorm did not surface a clear ask. Clear-all-history is the only destructive control.
- **Lazy-loading the popover code on note pages.** The garden bundle is loaded eagerly; popover is included in the bundle even though only desktop users use it. Bundle growth is ~5–7 KB minified — within budget. Lazy import deferred to a future polish if bundle size becomes a concern.

## 4. Storage schema (v2)

### 4.1 Envelope

`localStorage['garden-path-log']` (or `sessionStorage` when `consent === 'session'`) holds:

```js
{
  version: 2,
  sessions: [
    {
      root: "attention-as-material",
      slugs: ["attention-as-material", "readwise", "commonplace-book"],
      at: 1747654321000   // epoch ms when the session was started
    },
    {
      root: "zettelkasten",
      slugs: ["zettelkasten", "evergreen-notes"],
      at: 1747567890000
    }
    // … up to 20 sessions; oldest dropped when 21st starts
  ]
}
```

- **Cap:** 20 sessions max. When the 21st starts, the oldest gets dropped (FIFO by `at`).
- **Dedup:** *not* at write time. Identical-slug-sequence sessions are stored separately and dedup'd at read time only (most-recent `at` wins). This way the persistence layer doesn't lose true repeats — UI just hides them.

### 4.2 Migration from v1

The existing schema is a plain `Array<string>`. On any `readHistory()` call, if `JSON.parse(raw)` produces an array (no `version` field), the helper wraps it as one synthetic v2 session:

```js
{
  root: arr[0] || "",
  slugs: arr,
  at: 0          // sorts last (oldest) in UI
}
```

Then overwrites storage with the v2 envelope. One-shot; idempotent on re-read.

### 4.3 Storage consent integration

Writes are gated by the existing consent state machine in `garden-stack.js`:

| `consent` | Behavior |
|---|---|
| `unset` | No writes. Banner appears when stack grows to ≥2 columns. |
| `no` | No writes. |
| `session` | Writes to `sessionStorage`. |
| `yes` | Writes to `localStorage`. |

No changes to the consent state machine itself; only the data the writes carry changes (v1 flat → v2 envelope).

## 5. Runtime — session lifecycle

Modifications to `assets/js/garden-stack.js`:

### 5.1 Session start

In `init()`, after `state.slugs` is normalized (around current line 307):

- If `state.consent !== 'unset' && state.consent !== 'no'`, create a new session record `{root: rs, slugs: state.slugs.slice(), at: Date.now()}` and prepend it as the head of `sessions[]` (newest first).
- Trim `sessions[]` to the most-recent 20.
- Hold the new session's array index in a module-scope `currentSessionIdx` (always 0 since we prepended).

### 5.2 Session extend

In `appendColumn()`, after `state.slugs.push(slug)` (around current line 239), replace the `persistVisited(slug)` call:

- Read the full envelope, append `slug` to `sessions[currentSessionIdx].slugs`, re-write.
- Same consent gates apply.

### 5.3 `clearStack`

No session-state change. The session's `slugs` stays as recorded. Matches user intent: "clear" means *start over from this root*, not *forget I was here*.

### 5.4 Mobile bypass

The early `if (isMobile()) return;` in `init()` already prevents any session-related code from running. No writes happen on mobile. The widget on `/garden/` can still read pre-existing desktop data.

### 5.5 Old `persistVisited` removal

The current `persistVisited(slug)` function is removed; its responsibilities split between `garden-history.js` (storage + migration) and the new write-points in `init()` + `appendColumn()`.

## 6. Surface 1 — "Recent paths" widget on `/garden/`

### 6.1 Markup (server-rendered, hidden by default)

New partial `layouts/partials/garden/recent-paths.html`, included once at the top of `layouts/garden/list.html` above the existing topic-map section loop:

```html
<section class="garden-recent-paths" hidden aria-labelledby="recent-paths-heading">
  <h2 id="recent-paths-heading">Recent paths</h2>
  <ol class="recent-paths-list"></ol>
  <div class="recent-paths-actions">
    <a class="recent-paths-view-all" href="{{ "/garden/history/" | relURL }}">Reading history →</a>
    <button class="recent-paths-clear" type="button">Clear history</button>
  </div>
</section>
```

The `<ol>` is empty at render. JS populates it. The `<section>` stays `hidden` until JS confirms there are sessions to show.

### 6.2 JS (`assets/js/garden-recent-paths.js`)

~50 lines. On DOMContentLoaded:

1. Find `.garden-recent-paths`; bail if absent (not on `/garden/`).
2. `import {readHistory, dedupe, renderPath, clearHistory} from './garden-history.js'`.
3. `const sessions = dedupe(readHistory()).slice(0, 5);`
4. If `sessions.length === 0`, bail. Section stays hidden.
5. For each session, append a `<li>` with `renderPath(session)` output to `.recent-paths-list`.
6. Reveal section: `el.hidden = false;`.
7. Wire `.recent-paths-clear` click → `confirm("Clear all stored reading history?") && clearHistory() && el.hidden = true`.

### 6.3 Click on a path entry

Each `renderPath` output is a `<li>` containing `<a class="path-chip">` chips separated by `<span class="path-arrow" aria-hidden>›</span>`. Each chip is a real `<a href="/garden/<slug>/">`. **The first chip's href additionally carries the rest of the path as a `?stack=` param**, so clicking the leftmost chip reconstructs the full path; clicking a non-leftmost chip just jumps to that single note. (Rationale: clicking the head of the path = "load this path"; clicking the middle = "jump to that one note." Matches reading affordance.)

### 6.4 Mobile

Same markup, same JS, same behavior. Clicking a path's head chip navigates to `/garden/<root>/?stack=…`; mobile's `init()` bypasses the `?stack=` param, so user lands on root only. Degraded gracefully.

## 7. Surface 2 — Popover off path-log "N in stack" (note pages, desktop only)

### 7.1 Markup changes to `layouts/partials/garden/path-log.html`

Two changes:

1. Promote `<span class="path-log-count">` to `<button class="path-log-count" type="button" aria-expanded="false" aria-controls="path-log-popover">`. (JS will not promote on mobile.)
2. Add a new chrome link at the end of `.path-log-actions`:
   ```html
   <a class="path-log-history" href="{{ "/garden/history/" | relURL }}">history →</a>
   ```
   Always visible (desktop + mobile).

### 7.2 JS (`assets/js/garden-pathlog-popover.js`)

~80 lines. On DOMContentLoaded:

1. If `matchMedia('(max-width: 720px)').matches`, bail. No popover on mobile.
2. Find `.path-log-count`; bail if absent.
3. `import {readHistory, dedupe, renderPath} from './garden-history.js'`.
4. Identify the current session: read the page's root slug from `.path-log-crumb.is-active[data-slug]` (the active crumb already carries the slug — set server-side in the existing `path-log.html` partial). Find the newest session in `readHistory()` whose `root` matches. Compute `const others = dedupe(readHistory()).filter(s => s !== current).slice(0, 4);`. If multiple sessions match the root (user reloaded the same page within a few seconds), the highest-`at` one is "current".
5. If `others.length === 0`, leave the count as a plain `<span>` (not a button). Popover unavailable.
6. Otherwise, build the popover DOM:
   ```html
   <div id="path-log-popover" role="dialog" aria-labelledby="popover-heading" hidden>
     <h3 id="popover-heading">Recent paths</h3>
     <ol class="popover-paths"></ol>
     <a class="popover-history-link" href="/garden/history/">full history →</a>
   </div>
   ```
   Append into `.path-log-actions`.
7. Populate `<ol class="popover-paths">` with `renderPath(session)` for each of the `others`.
8. Wire toggle: click count button toggles `aria-expanded` and `hidden`.
9. Wire close-on-outside-click: capture-phase `mousedown` listener on `document`; if target not inside the popover or trigger, close.
10. Wire Esc: keydown handler closes popover, returns focus to trigger, `stopImmediatePropagation()` so garden-stack.js's Esc-clears-stack handler doesn't fire.
11. Focus management: on open, focus first `<a>` inside `<ol.popover-paths>`. On close (any path), focus returns to the count button.
12. Tab inside popover cycles through path chip-anchors → "full history →" link → back to first chip (focus trap).

### 7.3 Path click in popover

Same semantics as widget: leftmost chip carries `?stack=…`, other chips are bare links. Navigation is full-page (no in-place restore).

## 8. Surface 3 — `/garden/history/` page

### 8.1 Content + layout

- New content: `content/garden/history/_index.md` with frontmatter:
  ```yaml
  ---
  title: Reading history
  layout: history
  ---
  ```
  Body is empty; layout renders everything.

- New layout: `layouts/garden/history.html`. Extends `baseof.html`'s main block. Renders a server-side shell that JS hydrates:
  ```html
  <main class="garden-history">
    <header>
      <h1>Reading history</h1>
      <p class="lede">Your recent paths through the garden. Up to 20 most-recent sessions; older paths drop off automatically. Lives only in your browser.</p>
    </header>
    <div class="garden-history-status" hidden></div>
    <div class="garden-history-actions" hidden>
      <button class="garden-history-clear" type="button">Clear history</button>
    </div>
    <ol class="garden-history-list" hidden></ol>
    <div class="garden-history-empty" hidden>
      <!-- 3 inner divs, one per consent state — JS reveals exactly one -->
      <div data-state="unset">…</div>
      <div data-state="no">…<button class="reenable-tracking">Re-enable tracking</button></div>
      <div data-state="ok">…</div>
    </div>
  </main>
  ```

### 8.2 JS

The `/garden/history/` page reuses `garden-recent-paths.js`-like logic but with `slice(0, 20)` instead of `5` and additional empty-state handling. To keep modules thin, the page hydration code lives inline in `garden-recent-paths.js` behind a feature detect (`.garden-history` selector). One module mounts both `.garden-recent-paths` (widget) and `.garden-history` (full page).

Hydration logic:

1. Read consent + sessions.
2. Reveal `.garden-history-status` with: `${total} sessions stored · ${unique} unique paths after dedup` (using raw history + dedup'd history counts).
3. If sessions exist: reveal `<ol>` + `<button>`, populate list.
4. Else: reveal `<.garden-history-empty>` and inside it reveal the inner div matching consent state.
5. "Clear history" → confirm + `clearHistory()` + re-render (now the empty state shows).
6. "Re-enable tracking" → set `path-log-consent` to `unset` + reload page.

### 8.3 Page-weight classification

`tools/check_page_weights.py`'s prefix table iterates in declared order with first-match-wins; `/garden/history/` matches the existing `/garden/` entry → 600 KB tier. No code change needed. The page has no images / no graph JS / no covers, so it'll comfortably fit; the explicit higher budget gives headroom for the garden JS bundle reference (~117 → ~124 KB after this slice).

## 9. JS module split

| File | LOC | Responsibility |
|---|---|---|
| `assets/js/garden-history.js` | ~120 | Shared core: `readHistory`, `writeHistory`, `dedupe`, `formatRelativeTime`, `renderPath`, `clearHistory`. No DOM mounting; pure logic + render-to-DOM helper. |
| `assets/js/garden-recent-paths.js` | ~80 | Mounts on `.garden-recent-paths` (widget) AND `.garden-history` (full page) — one module covers both since the rendering logic is the same, only `slice` count + empty-state shape differ. |
| `assets/js/garden-pathlog-popover.js` | ~80 | Mounts on `.path-log-count` (note pages). Mobile bypass. Popover DOM, focus trap, Esc, click-outside, aria-expanded. |
| `assets/js/garden-stack.js` | +~30 | Schema v1→v2 migration via `readHistory()` import, session lifecycle (start in `init`, extend in `appendColumn`). Drop the old `persistVisited(slug)` function. |
| `assets/js/entry-garden.js` | +2 imports | `import './garden-recent-paths.js'; import './garden-pathlog-popover.js';` |

Bundle growth estimate: +5–7 KB minified on top of the current ~117 KB garden bundle.

## 10. Accessibility

- **Widget**: `<section aria-labelledby="recent-paths-heading">` with `<h2>` heading. `<ol>` so SR reads ordinal position. Path chips are `<a>` (kbd-navigable by default). `aria-hidden` on the `›` separators.
- **Popover trigger**: `<button aria-expanded="…" aria-controls="path-log-popover">`. Reads as "3 in stack, button, collapsed" / "expanded".
- **Popover content**: `role="dialog"`, `aria-labelledby="popover-heading"`. First chip focused on open. Tab cycles within popover (focus trap). Esc closes + restores focus to trigger + `stopImmediatePropagation()`.
- **`/garden/history/` page**: `<h1>` → `<ol>` tree. Clear-history button confirms via native `confirm()`. Re-enable button is a plain `<button>`. Page-sidebar partial not used (single section, no anchors).
- **`prefers-reduced-motion`**: popover open/close uses `display: none ↔ block` (no animation). Honored by default.
- **Color contrast**: all text uses existing `--color-ink`, `--color-ink-soft`, `--color-burgundy` tokens — already AAA/AA-gated by `tools/check-contrast.py`.

## 11. CSS

New section §43 in `assets/css/main.css`. Selectors:

- `.garden-recent-paths` (section wrapper, padding + background tint to distinguish from topic-maps)
- `.recent-paths-list` (ol, no list-style, gap between items)
- `.path-row` (each `<li>`, flex with arrows + chips)
- `.path-chip` (chip styling — uses `--color-tile` background, `--color-burgundy` text, dotted underline)
- `.path-arrow` (`--color-ink-fade`)
- `.path-time` (`--color-ink-soft`, monospace, fixed width)
- `.recent-paths-actions` (flex row with view-all + clear)
- `.path-log-history` (the new chrome link)
- `#path-log-popover` (absolute-positioned dropdown, `--color-paper` background, `--color-burgundy` border)
- `.popover-paths` (`<ol>` inside popover)
- `.garden-history` (the full page; reuses many widget selectors)
- `.garden-history-empty` (empty-state copy block)

All tokens existing; no new variables introduced.

## 12. Linter pair — `tools/check_garden_history.py` + `tools/test_check_garden_history.py`

### 12.1 Assertions

The linter runs against source files (no `public/` required, so it lives in the pre-build block).

1. `layouts/partials/garden/recent-paths.html` exists.
2. `layouts/garden/history.html` exists.
3. `content/garden/history/_index.md` exists and contains `layout: history` in frontmatter.
4. `layouts/garden/list.html` references `partials/garden/recent-paths.html` (string match against template-include syntax).
5. `layouts/partials/garden/path-log.html` references `/garden/history/` (the chrome link).
6. `assets/js/garden-history.js` exists.
7. `assets/js/garden-recent-paths.js` exists.
8. `assets/js/garden-pathlog-popover.js` exists.
9. `assets/js/entry-garden.js` imports both mount scripts (regex: `import ['"]\./garden-recent-paths['"]` and `import ['"]\./garden-pathlog-popover['"]`).
10. `assets/js/garden-stack.js` contains the literal substring `"version": 2` (schema sentinel; protects against accidental schema-v1 regression).

### 12.2 Sibling test fixtures

Per spec §3.1 paired-test convention:

1. Happy path (all assertions satisfied) → exit 0.
2. Missing `recent-paths.html` partial → exit 1.
3. Missing `history.html` layout → exit 1.
4. Missing `_index.md` for /garden/history/ → exit 1.
5. `list.html` doesn't include the partial → exit 1.
6. `path-log.html` missing the history chrome link → exit 1.
7. Missing one of the 3 new JS files → exit 1 (parameterized across the 3 files).
8. `entry-garden.js` missing the imports → exit 1.
9. `garden-stack.js` missing the v2 sentinel → exit 1.

Stdlib-only (pathlib + re + tempfile + unittest). Follows the same `lint_garden_history(project_root)` parameterized pattern as `check_garden_links.py`.

### 12.3 CI wiring

`.github/workflows/hugo.yaml` gains 2 named steps in the pre-build linter block (after `Run RSS XSL linter unit tests`, before `Build with Hugo`):

```yaml
- name: Verify garden history
  run: python3 tools/check_garden_history.py
- name: Run garden history linter unit tests
  run: python3 -m unittest tools/test_check_garden_history.py -v
```

CI step count: 42 → 44. Added pre-build linter time: <3s.

## 13. Risks

- **Schema-migration timing.** A user on the same browser with v1 data who loads the new garden code will have `garden-path-log` re-serialized as v2 on first read. Subsequent reads use v2. If they downgrade to an older site version (pre-this-slice) afterward, the old `garden-stack.js` will try to `JSON.parse(...)` an object and `.push(slug)` on it — type error, silent storage corruption. Mitigation: not applicable (downgrade is a user choice; the site doesn't ship a back-button to older versions).
- **localStorage availability.** Same as today — wrapped in try/catch; restricted contexts (private browsing strict, sandboxed iframes) just don't get history.
- **Bundle size.** +5–7 KB. Bundles already fit comfortably in the 600 KB tier for garden pages; <1% growth. Acceptable.
- **Linter sentinel rigidity.** Assertion #10 (`"version": 2` substring in garden-stack.js) is a textual sentinel that could false-positive (e.g., a comment containing the literal). Mitigation: keep the sentinel in code form (not a comment) — the migration helper itself sets `version: 2` so a textual presence is correlated with implementation presence.
- **Focus trap on popover.** If the popover has zero focusable children (shouldn't happen — at least the "full history →" link exists), the trap could loop forever. Code defensively handles this by checking `focusable.length === 0` → no trap, allow tab to escape.

## 14. Effort estimate

~1 day across the 4 implementation areas (schema migration + 3 surfaces + linter pair). Single slice, single PR. Browser verification (light/dark, kbd-only, narrow viewport) adds ~30 min.

## 15. Files added / modified

```
NEW:
  assets/js/garden-history.js                    (~120 lines)
  assets/js/garden-recent-paths.js               (~80 lines, mounts both widget + /history/ page)
  assets/js/garden-pathlog-popover.js            (~80 lines, desktop-only)
  layouts/partials/garden/recent-paths.html      (~12 lines, server shell)
  layouts/garden/history.html                    (~40 lines, server shell + empty-state branches)
  content/garden/history/_index.md               (~5 lines frontmatter)
  tools/check_garden_history.py                  (~80 lines)
  tools/test_check_garden_history.py             (~120 lines, ~9 fixture cases)

MODIFY:
  assets/js/garden-stack.js                      (+~30 lines: import readHistory/writeHistory; session start/extend; drop persistVisited)
  assets/js/entry-garden.js                      (+2 import lines)
  assets/css/main.css                            (+ new §43, ~60 lines)
  layouts/garden/list.html                       (+1 partial include line at top of section block)
  layouts/partials/garden/path-log.html          (+1 chrome link line; promote .path-log-count to <button>)
  .github/workflows/hugo.yaml                    (+2 named steps; 42 → 44)
  CLAUDE.md                                      (log shipped; close Phase 8 deferral)
```

Total: 8 new files, 7 modified.

---

*End of design. Plan via `superpowers:writing-plans` when ready to ship.*
