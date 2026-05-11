# Graph manipulation — slice design

**Status:** drafted · **Date:** 2026-05-11 · **Slice:** Phase 4 follow-up — graph zoom, pan, drag-node
**Parent spec:** `docs/superpowers/specs/2026-05-03-personal-site-design.md` §4.6
**Predecessor slice:** `docs/superpowers/specs/2026-05-08-garden-interactions-design.md` (Phase 4 — shipped the d3-force graph this slice extends)

---

## 0. Context for future Claude sessions

The Phase 4 garden-interactions slice (merged 2026-05-09 in commit `1181ba1`) shipped a static d3-force graph: nodes settle once, the layout is byte-stable across navigation (via a positions cache in `sessionStorage["garden-graph-positions"]`), and clicks navigate. There is no way to zoom, pan, or move nodes manually. The graph is legible at the current fixture size (~14 notes, ~27 edges), but the design intent — "let readers wander a knowledge graph" — implies hands-on manipulation. This slice adds the three interactions that close that gap: **wheel zoom**, **drag-pan**, **drag a node**.

The slice is deliberately small. Two new vendored modules (~15 KB combined), additions to `garden-graph.js`, two new toolbar buttons, a handful of CSS rules. No template changes, no fixture changes, no new CI gates.

**Decisions made during brainstorm** (expanded in §2):
- Drag-end keeps the node where the user released it (Obsidian-style, not the simulation-restoring default)
- A single "Reset positions" toolbar button releases all user-pinned nodes back to the simulation
- A single "Reset view" toolbar button restores zoom = 1, pan = (0, 0)
- Both buttons live in the existing graph toolbar next to the filter chips, separated by a divider
- Zoom and pan state persists across navigation in the same positions cache (keyed by filter + viewport + slug)
- Vendor both `d3-zoom` and `d3-drag` rather than hand-roll pointer-event handling

---

## 1. Slice scope

### In scope

1. Vendor `d3-zoom`, `d3-drag`, and `d3-selection` at `assets/js/vendor/d3-zoom.min.js`, `assets/js/vendor/d3-drag.min.js`, and `assets/js/vendor/d3-selection.min.js` (esm.sh `?bundle` recipe, same as the existing `d3-force.min.js`). `d3-selection` is required because both `d3-zoom` and `d3-drag` are "behaviors" attached to elements via the d3-selection API (`d3.select(el).call(behavior)`); they don't operate on raw DOM nodes.
2. SVG structure: wrap the existing edge + node layers in a single `<g class="graph-content">` so a single transform handles zoom + pan
3. `garden-graph.js` runtime:
   - Attach `d3-zoom` to the SVG with `scaleExtent([0.3, 4])`, filter out events whose target is inside a node group, disable the dblclick-zoom default
   - Attach `d3-drag` to each `<g class="garden-graph-node">` for node repositioning
   - State additions: `state.viewTransform = {k, tx, ty}`, `state.pinnedSlugs = Set<slug>`
   - Drag handlers: `start` sets `fx/fy` and kicks `simulation.alpha(0.3).restart()`; `end` keeps `fx/fy` set and records the slug as pinned
   - `wasDragged` flag suppresses the node click → navigate handler when the pointer actually moved during drag
   - Zoom handler writes `transform="translate(tx,ty) scale(k)"` to `<g class="graph-content">` and mirrors `{k, tx, ty}` into `state.viewTransform`
   - sessionStorage writes (positions, view) debounced 200 ms after the last zoom/drag event so wheel-spam doesn't thrash storage
4. Positions cache shape migration: the existing per-key value (`Array<{slug, x, y}>`) grows to `{nodes: Array<{slug, x, y, pinned}>, view: {k, tx, ty}}`. Reader normalizes legacy array-shaped entries on first read; no migration script.
5. Toolbar additions (rendered by `buildToolbar()` in `garden-graph.js`, no template changes):
   - `[Reset view]` — `svg.call(zoom.transform, zoomIdentity)`; existing zoom listener handles state + persistence
   - `[Reset positions]` — clears `fx/fy` on every node, empties `state.pinnedSlugs`, calls `simulation.alpha(0.5).restart()`; cache rewrites after convergence
6. CSS additions in `assets/css/main.css` §27 / §28:
   - `.garden-graph-canvas svg { cursor: grab; }` and `:active { cursor: grabbing; }`
   - `.garden-graph-node { cursor: pointer; }` (override the SVG cursor inheritance)
   - Visual separator between filter chips and action chips in the toolbar (gap or border-left on the first action chip)
7. CLAUDE.md update — note the new vendored modules, the cache-shape migration, the new toolbar buttons; update the Project status / Phase 4 follow-up entry

### Deferred (kept as round-trippable hooks)

- Touch interactions (pinch-zoom, two-finger pan): `d3-zoom` supports these for free on the standalone `/garden/graph/` page. We won't advertise or test them; if they work, that's a bonus. Documented in §7 as a "free win, not a commitment."
- Keyboard zoom / pan / drag: out of scope for v1. Could revisit if accessibility QA flags it. Keyboard users still navigate notes via the existing Enter/Space handlers on focused nodes.
- Per-node release (double-click or right-click to unpin a single node): rejected in favor of the global Reset positions button as the v1 escape hatch. Easy to add later.
- Floating canvas-corner placement for action buttons: rejected in favor of toolbar placement. Documented in §2.

### Out of slice (explicit)

- Semantic-zoom (rendering different content at different zoom levels — e.g., titles at low zoom, snippets at high zoom): not a v1 need; `d3-zoom`'s identity transform suffices.
- Inertia / momentum on pan: `d3-zoom` ships without it; we won't enable.
- Minimap: explicitly out.
- Bundle splitting to actually lazy-load `d3-zoom` and `d3-drag`: `js.Build` lacks `splitting: true`, so dynamic `import()` is inlined into the main bundle today (same constraint as `d3-force`). Same documentation note as the predecessor slice. Worth doing eventually but unchanged scope here.

---

## 2. Decisions captured during brainstorm

| Decision | Reasoning | Where it lives |
|---|---|---|
| Drag-end keeps `fx/fy` (Obsidian-style) over clearing them (simulation restores) | Hands-on layout is the point of manipulation. Snap-back trains users to fight the simulation. Reset positions is the explicit escape hatch. | `garden-graph.js` drag-end handler |
| Single "Reset positions" button over per-node release | Coarse but discoverable. Per-node double-click adds discoverability cost for a rarely-needed surgical action. | `buildToolbar()` |
| Reset view and Reset positions as two separate buttons | Different actions, different mental models. Combining into "Reset everything" hides what the button does. | `buildToolbar()` |
| Toolbar placement (next to filter chips) over floating canvas-corner overlay | Single visual home for graph controls; works identically in panel and standalone page; no new responsive layout work for small panel widths. | `buildToolbar()` |
| Persist zoom/pan in the existing positions cache (per filter + viewport + slug key) over not persisting | When a user navigates between notes, the panel stays open — re-zooming each time feels broken. The positions cache is already key-scoped correctly. | `garden-graph.js` state + cache |
| Vendor `d3-zoom` + `d3-drag` + `d3-selection` over hand-rolling pointer events | `d3-zoom` handles wheel + drag + transform math + clamp + filter in ~9 KB. `d3-drag` handles pointer capture and mid-drag DOM changes in ~6 KB. `d3-selection` (~17 KB) is required as the binding surface (`d3.select(el).call(behavior)`). Hand-rolling all three saves the ~32 KB total but invites bugs in node-drag hit-testing and pointer capture. | new vendored files |
| Suppress click-navigation during drag via `wasDragged` flag | Without it, every drag-release also opens the note. Simpler than introspecting d3-drag's distance-since-start. | drag-end + click handler |
| Skip `alpha(0.3).restart()` under `prefers-reduced-motion` | Drag still works; neighbors just don't animate. Aligns with site-wide reduced-motion convention. | drag-start handler |

---

## 3. Architecture

### 3.1 SVG structure change

The current SVG has two top-level groups:

```html
<svg viewBox="...">
  <desc>...</desc>
  <g class="garden-graph-edges">...</g>
  <g class="garden-graph-nodes">...</g>
</svg>
```

Becomes:

```html
<svg viewBox="...">
  <desc>...</desc>
  <g class="graph-content">
    <g class="garden-graph-edges">...</g>
    <g class="garden-graph-nodes">...</g>
  </g>
</svg>
```

All zoom + pan applies via `transform` on `.graph-content`. The simulation, node hit-targets, edge math, and accessibility metadata stay in unscaled "data space."

### 3.2 Vendored libraries

Three files added next to the existing `assets/js/vendor/d3-force.min.js`, fetched via the same esm.sh `?bundle` recipe:

```
https://esm.sh/d3-zoom@3?bundle
https://esm.sh/d3-drag@3?bundle
https://esm.sh/d3-selection@3?bundle
```

Approximate sizes minified: `d3-zoom` ~9 KB, `d3-drag` ~6 KB, `d3-selection` ~17 KB. Total bundle delta ~32 KB.

The `d3-selection` cost is paid because both `d3-zoom` and `d3-drag` expose their public API as a function-on-selection: `d3.select(svg).call(zoomBehavior)`, `d3.select(g).call(dragBehavior)`. Bypassing it would mean shimming the ~10 selection methods these behaviors touch (`.on`, `.property`, `.each`, `.call`, `.datum`, etc.), which trades bundle weight for a fragile maintenance surface every time we update a d3 module. We pay the 17 KB and use the canonical API.

As with `d3-force`, `js.Build` inlines the dynamic `import()` into the main bundle because the build lacks `splitting: true` — same constraint, same documented trade-off as the predecessor slice.

### 3.3 State additions

```js
// existing
const state = {
  data: null,
  panel: null,
  panelOpen: false,
  svg: null,
  simulation: null,
  filters: { tag: 'all', stage: 'all', local: 'all' },
  inStack: new Set(),
  page: { isMobile: false, isNotePage: false, currentSlug: null },
  lastPointerInStack: false,
};

// added
state.viewTransform = { k: 1, tx: 0, ty: 0 };
state.pinnedSlugs = new Set();
state.zoomBehavior = null;     // d3-zoom instance, retained for resetView()
```

### 3.4 Positions cache shape

Cache key (unchanged): `${tag}|${stage}|${local}|${slug}|${WxH}`

Cache value (extended):

```js
// before this slice
[{ slug, x, y }, ...]

// after this slice
{
  nodes: [{ slug, x, y, pinned }, ...],
  view: { k, tx, ty }
}
```

Reader normalization:

```js
function loadCachedPositions(canvas) {
  // ...
  const entry = cache[positionsCacheKey(canvas)];
  if (!entry) return null;
  if (Array.isArray(entry)) {
    return { nodes: entry.map(n => ({ ...n, pinned: false })),
             view: { k: 1, tx: 0, ty: 0 } };
  }
  return entry;
}
```

No migration script. Legacy entries upgrade on first read.

### 3.5 Interaction model

#### Wheel zoom

```js
import { zoom, zoomIdentity } from './vendor/d3-zoom.min.js';
import { select } from './vendor/d3-selection.min.js';

const zoomBehavior = zoom()
  .scaleExtent([0.3, 4])
  .filter(event => !event.target.closest('.garden-graph-node'))
  .on('zoom', ({ transform }) => {
    contentGroup.setAttribute('transform', transform.toString());
    state.viewTransform = { k: transform.k, tx: transform.x, ty: transform.y };
    persistCacheDebounced();
  });

select(svg).call(zoomBehavior).on('dblclick.zoom', null);
state.zoomBehavior = zoomBehavior;
```

- `scaleExtent([0.3, 4])` clamps zoom; d3-zoom handles wheel events past the clamp without UI flicker.
- `.filter` excludes events whose target is inside a node group so node-drag and node-click still work.
- `.on('dblclick.zoom', null)` removes the default double-click-to-zoom-2× behavior.
- `translateExtent` is left unset — pan is free. The graph can extend beyond the viewport; Reset view re-centers.

#### Drag-pan

Handled entirely by `d3-zoom`'s built-in pointer drag on empty SVG space. No additional code.

#### Drag node

```js
import { drag } from './vendor/d3-drag.min.js';
// `select` already imported above

const dragBehavior = drag()
  .on('start', (event, d) => {
    d.fx = d.x;
    d.fy = d.y;
    if (!reducedMotion()) simulation.alpha(0.3).restart();
  })
  .on('drag', (event, d) => {
    d.fx = event.x;
    d.fy = event.y;
  })
  .on('end', (event, d) => {
    // fx/fy stay set — Obsidian-style pin
    state.pinnedSlugs.add(d.slug);
    if (event.subject.startX !== undefined) {
      const dx = event.x - event.subject.startX;
      const dy = event.y - event.subject.startY;
      d.wasDragged = (dx * dx + dy * dy) > 9; // >3px movement
    }
    persistCacheDebounced();
  });

nodeEls.forEach(({ n, g }) => {
  // bind node datum so d3-drag handlers receive `d` directly
  g.__data__ = n;
  select(g).call(dragBehavior.subject(() => ({
    startX: n.x, startY: n.y, x: n.x, y: n.y
  })));
});
```

Note: `d3-drag`'s `event.x / event.y` are already in the parent's local coordinate system, so they account for the `<g class="graph-content">` transform. We don't need to invert the zoom matrix manually.

The existing click handler on each node consults `n.wasDragged`:

```js
g.addEventListener('click', () => {
  if (n.wasDragged) { n.wasDragged = false; return; }
  window.location.assign(`/garden/${n.slug}/`);
});
```

`wasDragged` resets on the next pointerdown (set in drag-start to `false`).

#### Reset view

```js
function resetView() {
  if (!state.zoomBehavior || !state.svg) return;
  select(state.svg).call(state.zoomBehavior.transform, zoomIdentity);
  // zoom handler fires once, writes state.viewTransform = {k:1, tx:0, ty:0}
  // and persists.
}
```

#### Reset positions

```js
function resetPositions() {
  state.simulation.nodes().forEach(n => {
    n.fx = null;
    n.fy = null;
  });
  state.pinnedSlugs.clear();
  state.simulation.alpha(0.5).restart();
  // After convergence, persistCacheDebounced() writes fresh positions.
  // View transform is untouched.
}
```

### 3.6 Cache persistence

```js
let persistTimer = null;
function persistCacheDebounced() {
  if (persistTimer) clearTimeout(persistTimer);
  persistTimer = setTimeout(() => {
    saveCachedPositions(canvas, nodes, state.viewTransform, state.pinnedSlugs);
    persistTimer = null;
  }, 200);
}

function saveCachedPositions(canvas, nodes, view, pinned) {
  try {
    const raw = sessionStorage.getItem(POSITIONS_KEY);
    const cache = raw ? JSON.parse(raw) : {};
    cache[positionsCacheKey(canvas)] = {
      nodes: nodes.map(n => ({
        slug: n.slug, x: n.x, y: n.y, pinned: pinned.has(n.slug)
      })),
      view: { ...view }
    };
    sessionStorage.setItem(POSITIONS_KEY, JSON.stringify(cache));
  } catch {}
}
```

### 3.7 Mount-time restore

In `buildSimulation`, after appending the SVG but before running the simulation:

```js
const cached = loadCachedPositions(canvas);  // shape-normalized
const cachedBySlug = cached ? new Map(cached.nodes.map(p => [p.slug, p])) : null;
const cacheHit = cachedBySlug && nodes.every(n => cachedBySlug.has(n.slug));

if (cacheHit) {
  nodes.forEach(n => {
    const p = cachedBySlug.get(n.slug);
    n.x = p.x;
    n.y = p.y;
    if (p.pinned) {
      n.fx = p.x;
      n.fy = p.y;
      state.pinnedSlugs.add(n.slug);
    }
  });
  // Apply cached view transform
  const v = cached.view;
  contentGroup.setAttribute('transform', `translate(${v.tx},${v.ty}) scale(${v.k})`);
  state.viewTransform = { ...v };
  // Sync d3-zoom's internal state so the next wheel starts from here
  select(svg).call(zoomBehavior.transform, zoomIdentity.translate(v.tx, v.ty).scale(v.k));
}
```

### 3.8 Toolbar additions

`buildToolbar(host)` already populates the filter chips. After the existing chip rendering, append a divider span and two action chips:

```js
const divider = document.createElement('span');
divider.className = 'toolbar-divider';
divider.setAttribute('aria-hidden', 'true');
host.append(divider);

const resetViewBtn = document.createElement('button');
resetViewBtn.type = 'button';
resetViewBtn.className = 'chip chip-action';
resetViewBtn.textContent = 'Reset view';
resetViewBtn.addEventListener('click', resetView);
host.append(resetViewBtn);

const resetPosBtn = document.createElement('button');
resetPosBtn.type = 'button';
resetPosBtn.className = 'chip chip-action';
resetPosBtn.textContent = 'Reset positions';
resetPosBtn.addEventListener('click', resetPositions);
host.append(resetPosBtn);
```

No partial change; both `graph-panel.html` and `graph.html` already delegate toolbar contents to JS.

### 3.9 CSS additions

In `assets/css/main.css` §27 (graph panel) and §28 (graph standalone page):

```css
.garden-graph-canvas svg {
  cursor: grab;
}
.garden-graph-canvas svg:active {
  cursor: grabbing;
}
.garden-graph-node {
  cursor: pointer;       /* override the grab cursor on nodes */
}
.garden-graph-node:active {
  cursor: grabbing;      /* visual cue during node drag */
}

/* Toolbar divider between filter chips and action chips */
.garden-graph-panel-toolbar .toolbar-divider,
.garden-graph-toolbar .toolbar-divider {
  display: inline-block;
  width: 1px;
  height: 1rem;
  background: var(--color-rule);
  margin: 0 0.5rem;
  vertical-align: middle;
}

/* Action chip variant: subtle visual differentiation from filter chips */
.chip.chip-action {
  font-style: italic;     /* or a different border style; design pass during impl */
}
```

The action-chip styling is a placeholder for the implementation pass — the design intent is "visually distinct from filter chips so users don't read them as another filter dimension," with the specific styling decided when the chips render in context. Italic is a safe default; could swap to a thinner border, lighter weight, or a leading glyph if it doesn't feel right.

---

## 4. Edge cases

| Case | Resolution |
|---|---|
| Drag releases on the same pixel (no movement) | `wasDragged` stays `false`; click handler navigates as today. Threshold = 3 px (distance² > 9). |
| Reduced motion + drag | Drag-start skips `alpha(0.3).restart()`. The dragged node still updates `fx/fy`; neighbors don't animate. Pan + zoom are instant DOM mutations, motion-agnostic. |
| Legacy session cache (array-shaped) | Reader normalizes on first load. Existing positions preserved, `pinned: false` for all, view = identity. One-time, transparent. |
| sessionStorage write thrash on wheel | All writes debounced 200 ms after last zoom/drag event. Final state always flushes (debounce, not throttle). |
| Touch / coarse pointer on `/garden/graph/` (mobile) | `d3-zoom` supports pinch and two-finger pan; `d3-drag` supports touch drag. Works "for free" — not advertised, not tested. If broken, follow-up patch. |
| Keyboard focus on a node, then user presses Enter | Existing Enter/Space → navigate handler unchanged. Keyboard users do not drag or zoom (out of scope). |
| Zoom past clamp (0.3× or 4×) | `d3-zoom` clamps internally; wheel events still fire but the transform stays at the boundary. No flicker. |
| Pan far past viewport edges | `translateExtent` unset → pan is free. Reset view re-centers. |
| Filter change mid-drag | Filter chip click requires pointer-up first; race is practically impossible. Not guarded. |
| Reset positions while a node is mid-drag | Reset button click also requires pointer-up. Not guarded. |
| Zoom transform restored from cache, but viewport size changed (window resize between mounts) | Cache key includes `WxH` — different viewport = different cache key = no stale view applied. |
| Node drag while panel is closing (`is-animating`) | Drag-start fires before close-animation completes. Not user-reachable: panel-close click target is the × button, not the canvas. |
| `state.zoomBehavior` referenced before zoom attached | All toolbar buttons render after `buildSimulation` completes (panel-open path) or after `init` runs (graph page). Reset view is no-op if `state.zoomBehavior` is null. |

---

## 5. Manual verification checklist

To record in the plan and run before merge. No automated tests for this slice — the JS surface is too small to justify a test harness, and existing CI gates (contrast, fixture linters, garden-links linter) don't touch runtime JS.

- [ ] Open graph panel on desktop; wheel-zoom toward cursor; verify clamps at 0.3× and 4×
- [ ] Drag empty SVG → pans; cursor changes from `grab` to `grabbing`
- [ ] Drag a node → node follows pointer; neighbors react (under normal motion)
- [ ] Release a dragged node → stays where placed; not snapped back
- [ ] Click a node without moving the pointer → opens the note
- [ ] Click "Reset view" → zoom snaps to 1×, pan to (0, 0); pinned positions unchanged
- [ ] Click "Reset positions" → all pins clear, simulation re-settles; view transform unchanged
- [ ] Drag a node, navigate to a different garden note, navigate back → pinned position + zoom + pan restored
- [ ] Change a filter chip (Tag or Stage) → fresh layout + view (cache key changed)
- [ ] Activate `prefers-reduced-motion` → drag still works; no alpha kick visible
- [ ] Open browser DevTools, manually inject a legacy array-shaped cache entry → reload, verify it loads without error and behaves as `pinned: false` everywhere
- [ ] Verify on the `/garden/graph/` standalone page that all the above work identically
- [ ] On mobile viewport (≤720px), navigate to `/garden/graph/` and confirm touch interactions either work or fail silently (no console errors, no broken navigation)

---

## 6. Cross-references

- Predecessor slice (Phase 4 garden interactions): `docs/superpowers/specs/2026-05-08-garden-interactions-design.md` — established the d3-force graph, side panel, position cache
- Predecessor plan: `docs/superpowers/plans/2026-05-08-garden-interactions.md`
- Parent design spec §4.6 (graph view): `docs/superpowers/specs/2026-05-03-personal-site-design.md`
- Existing graph runtime: `assets/js/garden-graph.js`
- Existing vendored library pattern: `assets/js/vendor/d3-force.min.js`
- Project context (Phase 4 status, queued slices): `~/.claude/projects/.../memory/project_phase_4_status.md`, `project_graph_manipulation_slice.md`