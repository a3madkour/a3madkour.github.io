# Graph Manipulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the d3-force garden graph manipulable — add wheel zoom (0.3×–4×), drag-pan on empty SVG space, drag-to-reposition for any node, plus a Reset view and Reset positions toolbar button. Released nodes stay where the user dropped them (Obsidian-style); zoom + pan + pin state persist in the existing positions cache.

**Architecture:** Vendor `d3-zoom`, `d3-drag`, and `d3-selection` next to the existing `d3-force.min.js`. Wrap the SVG's edge and node layers in a single `<g class="graph-content">` so one `transform` attribute handles zoom + pan. Attach `d3-zoom` to the SVG, filtering out events whose target is inside a node group so node drag still works. Attach `d3-drag` to each `.garden-graph-node` group. Extend the position-cache value from a bare `Array<{slug,x,y}>` to `{nodes: Array<{slug,x,y,pinned}>, view: {k,tx,ty}}`, normalizing legacy entries on read. Two new toolbar buttons live in the existing `buildToolbar()` flow — no template changes.

**Tech Stack:** Hugo extended ≥ 0.148.0 · vanilla ES modules built by Hugo's `js.Build` (esbuild) · d3-zoom v3, d3-drag v3, d3-selection v3 (vendored, no npm) · CSS hand-rolled in `assets/css/main.css` sections 27–28.

**Spec:** `docs/superpowers/specs/2026-05-11-graph-manipulation-design.md`

**Predecessor working state:** master @ commit `64468ec` (spec landed). Phase 4 graph view shipped + merged; positions cache key already `${tag}|${stage}|${local}|${slug}|${WxH}`; legacy cache value is `Array<{slug,x,y}>`.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `assets/js/vendor/d3-zoom.min.js` | NEW | Vendored d3-zoom v3 ESM bundle (~9 KB) |
| `assets/js/vendor/d3-drag.min.js` | NEW | Vendored d3-drag v3 ESM bundle (~6 KB) |
| `assets/js/vendor/d3-selection.min.js` | NEW | Vendored d3-selection v3 ESM bundle (~17 KB) |
| `assets/js/garden-graph.js` | MODIFY | SVG structure refactor, zoom + drag integration, state additions, cache shape migration, two new toolbar buttons, debounced persistence, mount-time restore |
| `assets/css/main.css` | MODIFY | Append rules to §27 (panel) and §28 (page): grab/grabbing cursors, toolbar divider, action-chip variant |
| `CLAUDE.md` | MODIFY | Note new vendored modules, cache-shape migration, new toolbar actions; update Project status with merge entry |

**Files NOT changed:** `layouts/partials/garden/graph-panel.html`, `layouts/garden/graph.html` (toolbar contents are JS-generated). No fixtures, no Hugo partials, no CI workflow, no Python tools.

**Branch convention:** work on `graph-manipulation`. Commit per task; merge with `--no-ff` at end.

---

## Task 1: Branch + vendor d3-zoom, d3-drag, d3-selection

**Files:**
- Create: `assets/js/vendor/d3-zoom.min.js`
- Create: `assets/js/vendor/d3-drag.min.js`
- Create: `assets/js/vendor/d3-selection.min.js`

- [ ] **Step 1.1: Create branch**

```bash
git checkout -b graph-manipulation
```

- [ ] **Step 1.2: Fetch d3-zoom v3 bundle**

```bash
curl -sSL 'https://esm.sh/d3-zoom@3?bundle' -o assets/js/vendor/d3-zoom.min.js
```

Verify the file is non-empty and looks like an ESM bundle:

```bash
wc -c assets/js/vendor/d3-zoom.min.js
head -c 200 assets/js/vendor/d3-zoom.min.js
```

Expected: 6 KB–25 KB; first ~200 chars contain ESM source-mappy text and `export{` somewhere in the file.

```bash
grep -c "export" assets/js/vendor/d3-zoom.min.js
```

Expected: ≥ 1.

- [ ] **Step 1.3: Fetch d3-drag v3 bundle**

```bash
curl -sSL 'https://esm.sh/d3-drag@3?bundle' -o assets/js/vendor/d3-drag.min.js
grep -c "export" assets/js/vendor/d3-drag.min.js
```

Expected: file 4 KB–15 KB; `export` count ≥ 1.

- [ ] **Step 1.4: Fetch d3-selection v3 bundle**

```bash
curl -sSL 'https://esm.sh/d3-selection@3?bundle' -o assets/js/vendor/d3-selection.min.js
grep -c "export" assets/js/vendor/d3-selection.min.js
```

Expected: file 12 KB–25 KB; `export` count ≥ 1.

- [ ] **Step 1.5: Confirm Hugo build still succeeds (no consumers yet, just verifying the new files don't break esbuild)**

```bash
hugo --minify
```

Expected: build completes; no errors in stdout. The new files aren't imported anywhere yet — they should sit dormant until Task 4.

- [ ] **Step 1.6: Commit**

```bash
git add assets/js/vendor/d3-zoom.min.js assets/js/vendor/d3-drag.min.js assets/js/vendor/d3-selection.min.js
git commit -m "Vendor d3-zoom, d3-drag, d3-selection for graph manipulation"
```

---

## Task 2: Wrap SVG layers in `<g class="graph-content">`

**Files:**
- Modify: `assets/js/garden-graph.js` (around lines 138–143 of current source — the `edgeLayer` + `nodeLayer` creation block inside `buildSimulation`)

This task is a pure structural refactor: introduce the `<g class="graph-content">` wrapper without adding any interaction yet. The graph should render identically; verify visually before moving on.

- [ ] **Step 2.1: Locate the existing layer-creation block**

Currently `buildSimulation` does:

```js
const edgeLayer = document.createElementNS(SVG_NS, 'g');
edgeLayer.setAttribute('class', 'garden-graph-edges');
svg.appendChild(edgeLayer);
const nodeLayer = document.createElementNS(SVG_NS, 'g');
nodeLayer.setAttribute('class', 'garden-graph-nodes');
svg.appendChild(nodeLayer);
```

- [ ] **Step 2.2: Replace with a wrapper-first structure**

Edit `assets/js/garden-graph.js` so the block becomes:

```js
const contentGroup = document.createElementNS(SVG_NS, 'g');
contentGroup.setAttribute('class', 'graph-content');
svg.appendChild(contentGroup);

const edgeLayer = document.createElementNS(SVG_NS, 'g');
edgeLayer.setAttribute('class', 'garden-graph-edges');
contentGroup.appendChild(edgeLayer);
const nodeLayer = document.createElementNS(SVG_NS, 'g');
nodeLayer.setAttribute('class', 'garden-graph-nodes');
contentGroup.appendChild(nodeLayer);
```

- [ ] **Step 2.3: Plumb `contentGroup` out of `buildSimulation`**

The function returns `{ svg, simulation }` today. Extend to `{ svg, simulation, contentGroup }`:

Find the return line at the end of `buildSimulation`:

```js
return { svg, simulation: sim };
```

Change to:

```js
return { svg, simulation: sim, contentGroup };
```

And in `rebuildGraph`, change:

```js
buildSimulation(canvas).then(({ svg, simulation }) => {
  state.svg = svg;
  state.simulation = simulation;
});
```

to:

```js
buildSimulation(canvas).then(({ svg, simulation, contentGroup }) => {
  state.svg = svg;
  state.simulation = simulation;
  state.contentGroup = contentGroup;
});
```

Also add `contentGroup: null` to the `state` object at the top of the file (around line 32).

- [ ] **Step 2.4: Visual verification**

Start the dev server:

```bash
hugo server --buildDrafts
```

Open `http://localhost:1313/garden/`, click the ⊞ Graph toggle (or navigate to `http://localhost:1313/garden/graph/`). Confirm the graph renders identically — nodes, edges, labels, in-stack markers, all visible in the same positions.

Inspect the DOM in DevTools: confirm the SVG now has `<g class="graph-content"><g class="garden-graph-edges">…</g><g class="garden-graph-nodes">…</g></g>` instead of two top-level groups.

Stop the dev server (Ctrl-C).

- [ ] **Step 2.5: Commit**

```bash
git add assets/js/garden-graph.js
git commit -m "Wrap graph layers in <g class=\"graph-content\"> for zoom/pan transform"
```

---

## Task 3: State additions + position-cache shape migration

**Files:**
- Modify: `assets/js/garden-graph.js` (state object near line 18; `loadCachedPositions` near line 47; `saveCachedPositions` near line 56)

This task ships the data-model upgrade without any UI behavior change. The graph still renders identically; the cache just learns a richer shape and reads legacy entries transparently.

- [ ] **Step 3.1: Extend state object**

Edit the top-level `state` object (currently lines 18–32). Add three new fields:

```js
const state = {
  data: null,
  panel: null,
  panelOpen: false,
  svg: null,
  contentGroup: null,       // added in Task 2
  simulation: null,
  filters: { tag: 'all', stage: 'all', local: 'all' },
  inStack: new Set(),
  page: { isMobile: false, isNotePage: false, currentSlug: null },
  lastPointerInStack: false,
  // Added this slice:
  viewTransform: { k: 1, tx: 0, ty: 0 },
  pinnedSlugs: new Set(),
  zoomBehavior: null,
};
```

- [ ] **Step 3.2: Rewrite `loadCachedPositions` to normalize both shapes**

Replace the current implementation (lines 47–54):

```js
function loadCachedPositions(canvas) {
  try {
    const raw = sessionStorage.getItem(POSITIONS_KEY);
    if (!raw) return null;
    const cache = JSON.parse(raw);
    return cache[positionsCacheKey(canvas)] || null;
  } catch { return null; }
}
```

With:

```js
function loadCachedPositions(canvas) {
  try {
    const raw = sessionStorage.getItem(POSITIONS_KEY);
    if (!raw) return null;
    const cache = JSON.parse(raw);
    const entry = cache[positionsCacheKey(canvas)];
    if (!entry) return null;
    // Legacy shape: bare array of {slug, x, y}. Normalize to new shape.
    if (Array.isArray(entry)) {
      return {
        nodes: entry.map(n => ({ slug: n.slug, x: n.x, y: n.y, pinned: false })),
        view: { k: 1, tx: 0, ty: 0 },
      };
    }
    return entry;
  } catch { return null; }
}
```

- [ ] **Step 3.3: Rewrite `saveCachedPositions` to write the new shape**

Replace the current implementation (lines 56–63):

```js
function saveCachedPositions(canvas, nodes) {
  try {
    const raw = sessionStorage.getItem(POSITIONS_KEY);
    const cache = raw ? JSON.parse(raw) : {};
    cache[positionsCacheKey(canvas)] = nodes.map(n => ({ slug: n.slug, x: n.x, y: n.y }));
    sessionStorage.setItem(POSITIONS_KEY, JSON.stringify(cache));
  } catch {}
}
```

With:

```js
function saveCachedPositions(canvas, nodes, view, pinned) {
  try {
    const raw = sessionStorage.getItem(POSITIONS_KEY);
    const cache = raw ? JSON.parse(raw) : {};
    cache[positionsCacheKey(canvas)] = {
      nodes: nodes.map(n => ({
        slug: n.slug,
        x: n.x,
        y: n.y,
        pinned: pinned.has(n.slug),
      })),
      view: { k: view.k, tx: view.tx, ty: view.ty },
    };
    sessionStorage.setItem(POSITIONS_KEY, JSON.stringify(cache));
  } catch {}
}
```

- [ ] **Step 3.4: Update the existing call sites of `loadCachedPositions` and `saveCachedPositions`**

Inside `buildSimulation` (around line 190):

Find:

```js
const cached = loadCachedPositions(canvas);
const cachedBySlug = cached ? new Map(cached.map(p => [p.slug, p])) : null;
const cacheHit = cachedBySlug && nodes.every(n => cachedBySlug.has(n.slug));
if (cacheHit) {
  nodes.forEach(n => {
    const p = cachedBySlug.get(n.slug);
    n.x = p.x; n.y = p.y;
  });
}
```

Replace with:

```js
const cached = loadCachedPositions(canvas);
const cachedBySlug = cached ? new Map(cached.nodes.map(p => [p.slug, p])) : null;
const cacheHit = cachedBySlug && nodes.every(n => cachedBySlug.has(n.slug));
if (cacheHit) {
  nodes.forEach(n => {
    const p = cachedBySlug.get(n.slug);
    n.x = p.x; n.y = p.y;
    // pinned + view restoration handled in Task 7 (drag/zoom not yet wired)
  });
}
```

Also find the existing `saveCachedPositions(canvas, nodes);` call (around line 224) and replace with:

```js
saveCachedPositions(canvas, nodes, state.viewTransform, state.pinnedSlugs);
```

This passes the current (still-identity) view and the (still-empty) pinned set. The serialized cache value is now the new shape, but no user interaction has changed the defaults yet.

- [ ] **Step 3.5: Visual verification — legacy cache migrates transparently**

Before testing, plant a legacy-shape entry:

```bash
hugo server --buildDrafts
```

In your browser at `http://localhost:1313/garden/`, open DevTools console and run:

```js
sessionStorage.setItem('garden-graph-positions', JSON.stringify({
  'all|all|all||1280x800': [
    { slug: 'fake-slug-that-wont-match', x: 100, y: 100 }
  ]
}));
```

Reload the page, open the graph panel. Verify in DevTools that no errors are thrown; the graph still renders. Now inspect sessionStorage's `garden-graph-positions` value — it should now contain the new-shape entry (`{nodes: [...], view: {...}}`) for whatever cache key the panel actually used.

Clear the planted entry:

```js
sessionStorage.removeItem('garden-graph-positions');
```

Reload, verify graph still renders cleanly. Stop the dev server.

- [ ] **Step 3.6: Commit**

```bash
git add assets/js/garden-graph.js
git commit -m "Extend graph position cache to {nodes,view}; normalize legacy array entries"
```

---

## Task 4: d3-zoom integration — wheel zoom + drag-pan

**Files:**
- Modify: `assets/js/garden-graph.js` (imports at top of `buildSimulation`; new zoom-attach block; debounce helper)

After this task, wheel-zoom and drag-pan work in the current session. Persistence and toolbar buttons come later.

- [ ] **Step 4.1: Add zoom-related imports inside `buildSimulation`**

Find the existing dynamic import at the top of `buildSimulation` (around line 122):

```js
const { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } =
  await import('./vendor/d3-force.min.js');
```

Add two more lines after it:

```js
const { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } =
  await import('./vendor/d3-force.min.js');
const { zoom, zoomIdentity } = await import('./vendor/d3-zoom.min.js');
const { select } = await import('./vendor/d3-selection.min.js');
```

- [ ] **Step 4.2: Add a module-level debounce helper**

Near the top of the file (after the `state` object, around line 33), add:

```js
let persistTimer = null;
function persistCacheDebounced() {
  if (persistTimer) clearTimeout(persistTimer);
  persistTimer = setTimeout(() => {
    persistTimer = null;
    flushCache();
  }, 200);
}
function flushCache() {
  let canvas;
  const isGraphPage = !!document.querySelector('.garden-graph-page');
  if (isGraphPage) {
    canvas = document.querySelector('.garden-graph-page .garden-graph-canvas');
  } else if (state.panel) {
    canvas = state.panel.querySelector('.garden-graph-panel-canvas');
  }
  if (!canvas || !state.simulation) return;
  saveCachedPositions(canvas, state.simulation.nodes(), state.viewTransform, state.pinnedSlugs);
}
```

`flushCache()` recomputes the canvas reference from the current page state rather than capturing it in a closure — this keeps the debounce safe across `rebuildGraph()` calls.

- [ ] **Step 4.3: Attach d3-zoom inside `buildSimulation`**

Find the location right after the SVG mount (`canvas.replaceChildren(svg);`, around line 185) and before the cache-restore block. Insert:

```js
const zoomBehavior = zoom()
  .scaleExtent([0.3, 4])
  .filter(event => !event.target.closest('.garden-graph-node'))
  .on('zoom', ({ transform }) => {
    contentGroup.setAttribute(
      'transform',
      `translate(${transform.x},${transform.y}) scale(${transform.k})`
    );
    state.viewTransform = { k: transform.k, tx: transform.x, ty: transform.y };
    persistCacheDebounced();
  });

select(svg).call(zoomBehavior).on('dblclick.zoom', null);
state.zoomBehavior = zoomBehavior;
```

- [ ] **Step 4.4: Visual verification**

```bash
hugo server --buildDrafts
```

Open `http://localhost:1313/garden/`, open the graph panel.

- Hover over the canvas, scroll the wheel. Verify: graph zooms toward the cursor, clamps at 0.3× (minimum) and 4× (maximum).
- Click and drag on empty SVG space (not on a node). Verify: graph pans; cursor changes per CSS in Task 9 — for now, default cursor is fine.
- Click a node. Verify: navigates to that note (zoom filter shouldn't block clicks — `.filter(e => !e.target.closest('.garden-graph-node'))` lets node events fall through, and we haven't touched the node click handler yet).
- Double-click on empty SVG. Verify: nothing happens (the default `dblclick.zoom` has been disabled).

Open DevTools → Application → Session Storage → `localhost:1313` → `garden-graph-positions`. After a wheel scroll, wait ~250 ms, then refresh the value display. Verify: the stored entry's `view` field has changed from `{k:1, tx:0, ty:0}` to something else.

Stop the dev server.

- [ ] **Step 4.5: Commit**

```bash
git add assets/js/garden-graph.js
git commit -m "Integrate d3-zoom: wheel zoom (0.3x–4x) + drag-pan with debounced persistence"
```

---

## Task 5: d3-drag integration — node drag with stay-put release

**Files:**
- Modify: `assets/js/garden-graph.js` (imports; node-creation loop; click handler)

After this task, dragging a node moves it; releasing leaves it pinned. Click-to-navigate still works on un-dragged nodes.

- [ ] **Step 5.1: Add d3-drag import**

In `buildSimulation`, extend the import block from Task 4:

```js
const { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } =
  await import('./vendor/d3-force.min.js');
const { zoom, zoomIdentity } = await import('./vendor/d3-zoom.min.js');
const { drag } = await import('./vendor/d3-drag.min.js');
const { select } = await import('./vendor/d3-selection.min.js');
```

- [ ] **Step 5.2: Build the drag behavior**

Inside `buildSimulation`, after the zoom-attach block from Task 4 but before the node-creation loop (around line 154 — right before `const nodeEls = nodes.map(n => {`), insert:

```js
const dragBehavior = drag()
  .subject(function() { return this.__data__; })
  .on('start', function(event) {
    const d = event.subject;
    d.fx = d.x;
    d.fy = d.y;
    d.__startX = d.x;
    d.__startY = d.y;
    d.wasDragged = false;
    if (!reducedMotion()) sim.alphaTarget(0.3).restart();
  })
  .on('drag', function(event) {
    const d = event.subject;
    d.fx = event.x;
    d.fy = event.y;
  })
  .on('end', function(event) {
    const d = event.subject;
    if (!reducedMotion()) sim.alphaTarget(0);
    const dx = d.fx - d.__startX;
    const dy = d.fy - d.__startY;
    if ((dx * dx + dy * dy) > 9) {
      d.wasDragged = true;
      state.pinnedSlugs.add(d.slug);
    } else {
      // Pure click — release the pin we just set in 'start' so a click on
      // an un-dragged node doesn't accidentally pin it at its current spot.
      d.fx = null;
      d.fy = null;
    }
    persistCacheDebounced();
  });
```

Note the use of `sim.alphaTarget(...)` (not `alpha`) so the simulation keeps reheating until drag-end — this matches d3's canonical drag pattern.

- [ ] **Step 5.3: Apply drag behavior to each node + bind datum**

In the node-creation loop, find the line that registers the click handler:

```js
g.addEventListener('click', () => { window.location.assign(`/garden/${n.slug}/`); });
```

Replace with the click-suppression-aware version and attach drag:

```js
g.__data__ = n;
select(g).call(dragBehavior);

g.addEventListener('click', () => {
  if (n.wasDragged) {
    n.wasDragged = false;
    return;
  }
  window.location.assign(`/garden/${n.slug}/`);
});
```

(The Enter/Space keyboard handler stays unchanged.)

- [ ] **Step 5.4: Visual verification**

```bash
hugo server --buildDrafts
```

Open the graph panel.

- Click a node without moving the pointer. Verify: navigates to the note as before.
- Use browser back to return. Open the panel.
- Click and *drag* a node (move > 3 px). Verify: node follows the pointer; neighbors react under normal motion settings.
- Release. Verify: node stays where you dropped it; does not snap back.
- Click that same dragged node (no movement). Verify: navigates to the note (`wasDragged` was reset by the click handler).
- Drag a node again. Pan the canvas. Verify: pan filter doesn't conflict with node drag (drags start on the node, pans start on empty space).

Inspect sessionStorage `garden-graph-positions` after a drag-release. Verify: the stored `nodes` array now contains at least one entry with `pinned: true`.

Open DevTools, toggle `prefers-reduced-motion: reduce` (DevTools → Rendering → Emulate CSS media feature). Refresh, open panel, drag a node. Verify: drag still works; neighbors don't visibly animate.

Stop the dev server.

- [ ] **Step 5.5: Commit**

```bash
git add assets/js/garden-graph.js
git commit -m "Integrate d3-drag: stay-put node drag with click suppression on movement"
```

---

## Task 6: Reset view + Reset positions toolbar buttons

**Files:**
- Modify: `assets/js/garden-graph.js` (add `resetView` and `resetPositions` functions; extend `buildToolbar`)

- [ ] **Step 6.1: Stash `select` and `zoomIdentity` on `state` for module-scope access**

Both `resetView` (defined at module scope) and the toolbar buttons (created during `buildToolbar`, also at module scope) need access to `d3-selection.select` and `d3-zoom.zoomIdentity`. These are currently imported only inside `buildSimulation`'s async block. The minimal-change fix: stash them on `state` immediately after the dynamic import.

In `buildSimulation`'s import block (Task 4 added `zoomIdentity` to the destructure), add right after:

```js
const { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } =
  await import('./vendor/d3-force.min.js');
const { zoom, zoomIdentity } = await import('./vendor/d3-zoom.min.js');
const { drag } = await import('./vendor/d3-drag.min.js');
const { select } = await import('./vendor/d3-selection.min.js');
state.d3select = select;
state.zoomIdentity = zoomIdentity;
```

Adjust the top-level `state` declaration to declare the new fields:

```js
const state = {
  // ... existing fields ...
  viewTransform: { k: 1, tx: 0, ty: 0 },
  pinnedSlugs: new Set(),
  zoomBehavior: null,
  d3select: null,
  zoomIdentity: null,
};
```

- [ ] **Step 6.2: Add `resetView` and `resetPositions` functions**

Near the existing `updateInStackMarkers`, `buildToolbar`, `buildLegend` block (around line 247 of the current source), add:

```js
function resetView() {
  if (!state.zoomBehavior || !state.svg || !state.d3select || !state.zoomIdentity) return;
  state.d3select(state.svg).call(state.zoomBehavior.transform, state.zoomIdentity);
  // The 'zoom' handler attached in buildSimulation will fire once and update
  // state.viewTransform + schedule a debounced cache flush.
}

function resetPositions() {
  if (!state.simulation) return;
  state.simulation.nodes().forEach(n => {
    n.fx = null;
    n.fy = null;
  });
  state.pinnedSlugs.clear();
  state.simulation.alpha(0.5).restart();
  persistCacheDebounced();
}
```

- [ ] **Step 6.3: Extend `buildToolbar` with the two action chips**

Find `buildToolbar(host)` (around line 255). At the very end of the function (after the `if (state.page.isNotePage) { ... }` block), append:

```js
// Action chips: visually separated from filter chips
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

- [ ] **Step 6.4: Visual verification**

```bash
hugo server --buildDrafts
```

Open the graph panel. Verify the toolbar now ends with a thin divider followed by "Reset view" and "Reset positions" buttons. (They'll be unstyled — visual polish lands in Task 8.)

- Wheel-zoom to a different scale; click **Reset view**. Verify: zoom snaps to 1×, pan to 0. Pinned positions (if any) unchanged.
- Drag two nodes to new spots; click **Reset positions**. Verify: both nodes settle back into the simulation layout; view transform unchanged.
- Verify also on the standalone `/garden/graph/` page.

Stop the dev server.

- [ ] **Step 6.5: Commit**

```bash
git add assets/js/garden-graph.js
git commit -m "Add Reset view + Reset positions toolbar buttons"
```

---

## Task 7: Mount-time restore — apply cached view + pinned fx/fy

**Files:**
- Modify: `assets/js/garden-graph.js` (cache-hit block inside `buildSimulation`)

After this task, navigating away from a note and back restores the previous zoom, pan, and dragged-pinned positions.

- [ ] **Step 7.1: Extend the cache-hit block to apply pin + view**

Find the cache-hit block from Task 3 (around line 192):

```js
const cached = loadCachedPositions(canvas);
const cachedBySlug = cached ? new Map(cached.nodes.map(p => [p.slug, p])) : null;
const cacheHit = cachedBySlug && nodes.every(n => cachedBySlug.has(n.slug));
if (cacheHit) {
  nodes.forEach(n => {
    const p = cachedBySlug.get(n.slug);
    n.x = p.x; n.y = p.y;
    // pinned + view restoration handled in Task 7 (drag/zoom not yet wired)
  });
}
```

Replace with:

```js
const cached = loadCachedPositions(canvas);
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
  // Apply cached view transform to the wrapper and sync d3-zoom's internal state
  const v = cached.view;
  contentGroup.setAttribute('transform', `translate(${v.tx},${v.ty}) scale(${v.k})`);
  state.viewTransform = { k: v.k, tx: v.tx, ty: v.ty };
  select(svg).call(
    zoomBehavior.transform,
    zoomIdentity.translate(v.tx, v.ty).scale(v.k)
  );
}
```

(Yes, the call to `zoomBehavior.transform` here fires the `'zoom'` listener once, which will re-write `state.viewTransform` to the same value and schedule a debounced flush — harmless, and far simpler than guarding against the recursion.)

- [ ] **Step 7.2: Reset `state.pinnedSlugs` on each `buildSimulation` call**

A subsequent rebuild (e.g., filter change) creates a fresh layout. We must NOT inherit the previous filter's pinned set, because the slug list is potentially different and the layout is unrelated.

At the very start of `buildSimulation`, after the import block, add:

```js
state.pinnedSlugs = new Set();
state.viewTransform = { k: 1, tx: 0, ty: 0 };
```

The cache-hit block above will repopulate both from cache if there's a hit for the new key.

- [ ] **Step 7.3: Visual verification**

```bash
hugo server --buildDrafts
```

Open the graph panel. Pin a node by dragging it to an obviously-off-layout position. Wheel-zoom in to 2×. Pan to a corner.

Click a node to navigate to a different garden note. Wait for the new page to load with the panel auto-restored. Verify:
- The same dragged node is in the same off-layout position.
- The view is at the same zoom and pan.

Click back to the original note. Verify: same restoration.

Now change a filter (e.g., click a tag chip). Verify: fresh layout — pinned positions and view are reset (cache key changed).

Stop the dev server.

- [ ] **Step 7.4: Commit**

```bash
git add assets/js/garden-graph.js
git commit -m "Restore cached view transform + pinned fx/fy on graph mount"
```

---

## Task 8: CSS additions — cursors, toolbar divider, action-chip variant

**Files:**
- Modify: `assets/css/main.css` (§27 around line 1283; §28 around line 1380)

This task adds visual feedback (cursors), separates action chips from filter chips visually, and keeps the toolbar tidy.

- [ ] **Step 8.1: Append cursor + divider + action-chip rules to §27**

In `assets/css/main.css`, find the `.garden-graph-panel-canvas svg { width: 100%; height: 100%; }` block (around line 1289). Right after that block, before the `.garden-graph-panel-legend` block, insert:

```css
/* Cursor states for zoom/pan on the panel canvas */
.garden-graph-panel-canvas svg {
  cursor: grab;
}
.garden-graph-panel-canvas svg:active {
  cursor: grabbing;
}

/* Toolbar divider between filter chips and action chips */
.garden-graph-panel-toolbar .toolbar-divider {
  display: inline-block;
  width: 1px;
  height: 1rem;
  background: var(--color-rule);
  margin: 0 0.4rem;
  vertical-align: middle;
}

/* Action chip variant: italic to visually separate from filter chips */
.garden-graph-panel-toolbar .chip.chip-action {
  font-style: italic;
}
```

Also amend the existing `.garden-graph-node circle { cursor: pointer; ... }` block to add a `:active` variant. Find (around line 1315):

```css
.garden-graph-node circle {
  cursor: pointer;
  stroke: transparent;
  stroke-width: 1;
}
```

Replace with:

```css
.garden-graph-node circle {
  cursor: pointer;
  stroke: transparent;
  stroke-width: 1;
}
.garden-graph-node:active circle {
  cursor: grabbing;
}
```

- [ ] **Step 8.2: Append the same rules to §28 (standalone page)**

Find the `.garden-graph-page .garden-graph-canvas svg` block (around line 1386):

```css
.garden-graph-page .garden-graph-canvas svg {
  width: 100%;
  height: 70vh;
}
```

Right after, insert:

```css
.garden-graph-page .garden-graph-canvas svg {
  cursor: grab;
}
.garden-graph-page .garden-graph-canvas svg:active {
  cursor: grabbing;
}

.garden-graph-page .garden-graph-toolbar .toolbar-divider {
  display: inline-block;
  width: 1px;
  height: 1rem;
  background: var(--color-rule);
  margin: 0 0.4rem;
  vertical-align: middle;
}
.garden-graph-page .garden-graph-toolbar .chip.chip-action {
  font-style: italic;
}
```

(The `.garden-graph-node :active circle { cursor: grabbing; }` from §27 already covers both surfaces because the node selector isn't surface-scoped.)

- [ ] **Step 8.3: Run contrast check (sanity — no token changes, but the script must still pass)**

```bash
python3 tools/check-contrast.py
```

Expected: all four pairings pass in both light and dark modes (output ends with `OK`).

- [ ] **Step 8.4: Visual verification**

```bash
hugo server --buildDrafts
```

Open `http://localhost:1313/garden/`, open the panel.

- Hover over empty SVG space. Cursor = `grab`.
- Mousedown on empty SVG. Cursor = `grabbing`.
- Hover over a node. Cursor = `pointer`.
- Drag a node. Cursor = `grabbing`.
- Verify the toolbar shows a thin vertical divider before "Reset view" and "Reset positions"; both buttons are in italic.

Repeat on `/garden/graph/`.

Stop the dev server.

- [ ] **Step 8.5: Commit**

```bash
git add assets/css/main.css
git commit -m "CSS: cursor states + toolbar divider + action-chip variant for graph manipulation"
```

---

## Task 9: CLAUDE.md update

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 9.1: Update the JS pipeline section**

Find the paragraph in `CLAUDE.md` that describes the JS pipeline and d3-force vendoring (search for "d3-force is vendored"). Replace the relevant sentences with:

```
d3-force, d3-zoom, d3-drag, and d3-selection are vendored under `assets/js/vendor/` (no npm). `garden-graph.js` dynamically imports all four on first graph open. As with d3-force at the predecessor slice, `js.Build` without `splitting: true` inlines these dynamic imports into the main bundle — the ~50 KB of d3 modules ride along with every page until/unless the build is refactored to emit code-split chunks.
```

- [ ] **Step 9.2: Update the Project status section**

Find the "## Project status" section and add a new entry directly below the Phase 4 entry:

```markdown
**Phase 4 follow-up — graph manipulation complete (2026-05-11).** d3-force graph gains hands-on interaction: wheel zoom (0.3×–4×) toward the cursor, drag-pan on empty SVG, drag-to-reposition for any node with Obsidian-style stay-put release. New toolbar buttons **[Reset view]** restores zoom + pan and **[Reset positions]** releases all pinned nodes back to the simulation. Zoom, pan, and pin state persist per filter+viewport in the existing positions cache; legacy cache entries (bare arrays) auto-migrate to the new `{nodes, view}` shape on first read. `d3-zoom`, `d3-drag`, and `d3-selection` vendored alongside `d3-force.min.js` (~32 KB combined). No template changes, no fixture changes, no new CI gates.
```

- [ ] **Step 9.3: Update the Hard constraints / Deferred features table — no change needed**

Sanity check: scan the deferred-features table and confirm none of the rows imply the manipulation slice. (It doesn't — manipulation was queued post-Phase-4, not pre-empted.)

- [ ] **Step 9.4: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: document graph manipulation slice + new vendored d3 modules"
```

---

## Task 10: Final acceptance walkthrough + merge

**Files:** (no edits; verification + merge)

- [ ] **Step 10.1: Run all CI gates locally**

```bash
python3 tools/check-contrast.py
python3 tools/check_fixtures.py
python3 -m unittest tools/test_check_fixtures.py -v
python3 tools/check_garden_fixtures.py
python3 -m unittest tools/test_check_garden_fixtures.py -v
python3 tools/check_garden_links.py
python3 -m unittest tools/test_check_garden_links.py -v
python3 tools/check_filter_chips_config.py
python3 -m unittest tools/test_check_filter_chips_config.py -v
```

Expected: every command exits 0; no failures, no errors.

- [ ] **Step 10.2: Build the site clean**

```bash
hugo --minify
```

Expected: build completes; no errors.

- [ ] **Step 10.3: Acceptance walkthrough (spec §5 checklist)**

Start the dev server fresh (clear any planted sessionStorage state):

```bash
hugo server --buildDrafts
```

In a fresh tab at `http://localhost:1313/garden/`, run through the spec's §5 checklist explicitly. For each, observe the behavior and check the box mentally:

- [ ] Open graph panel on desktop; wheel-zoom toward cursor; clamps at 0.3× and 4×
- [ ] Drag empty SVG → pans; cursor changes from `grab` to `grabbing`
- [ ] Drag a node → node follows pointer; neighbors react (under normal motion)
- [ ] Release a dragged node → stays where placed; not snapped back
- [ ] Click a node without moving the pointer → opens the note
- [ ] Click "Reset view" → zoom snaps to 1×, pan to (0, 0); pinned positions unchanged
- [ ] Click "Reset positions" → all pins clear, simulation re-settles; view transform unchanged
- [ ] Drag a node, navigate to a different garden note, navigate back → pinned position + zoom + pan restored
- [ ] Change a filter chip (Tag or Stage) → fresh layout + view (cache key changed)
- [ ] DevTools → Rendering → `prefers-reduced-motion: reduce` → drag still works; no alpha kick visible
- [ ] DevTools console — inject a legacy array-shaped cache entry, reload, verify loads without error and behaves as `pinned: false` everywhere
- [ ] On the `/garden/graph/` standalone page, repeat all of the above
- [ ] DevTools → Responsive mode → 375 px width, navigate to `/garden/graph/`, attempt touch-like pinch and drag; either works or fails silently (no console errors, no broken navigation)

If any check fails, fix in a new commit before proceeding. Document each fix tersely in the commit message.

- [ ] **Step 10.4: Push the branch**

```bash
git push -u origin graph-manipulation
```

- [ ] **Step 10.5: Open a PR**

The user will decide whether to merge via GitHub PR or local `--no-ff` merge. Pause here and report status to the user with the spec §5 checklist results.

If proceeding locally:

```bash
git checkout master
git merge --no-ff graph-manipulation -m "Merge graph-manipulation: zoom, pan, drag-node, reset buttons"
git push origin master
git branch -d graph-manipulation
git push origin --delete graph-manipulation
```

After merge, GitHub Actions runs the CI gates + builds + deploys. Verify the workflow completes green.

---

## Self-review checklist

**Spec coverage:** Every in-scope item from spec §1 maps to a task:

| Spec §1 item | Plan task |
|---|---|
| Vendor d3-zoom, d3-drag, d3-selection | Task 1 |
| SVG `<g class="graph-content">` wrapper | Task 2 |
| State additions (viewTransform, pinnedSlugs) | Task 3 |
| Cache shape migration with normalization | Task 3 |
| d3-zoom attachment (wheel + pan + scaleExtent + filter + dblclick disable) | Task 4 |
| d3-drag node behavior (start/drag/end with stay-put) | Task 5 |
| wasDragged click suppression | Task 5 |
| Reduced-motion skip alpha kick | Task 5 |
| Reset view button | Task 6 |
| Reset positions button | Task 6 |
| Mount-time restore (view + pinned) | Task 7 |
| Debounced sessionStorage writes | Task 4 (introduced); used by Tasks 4–7 |
| CSS cursors (grab/grabbing/pointer) | Task 8 |
| Toolbar divider + action-chip variant | Task 8 |
| CLAUDE.md update | Task 9 |
| No template changes | (none required — verified in spec §3.8) |
| No fixture changes | (none required) |

**Placeholder scan:** zero "TBD" / "TODO" / "fill in" entries; every step has either a code block or an exact command + expected output.

**Type consistency:** `state.zoomBehavior`, `state.viewTransform`, `state.pinnedSlugs`, `state.contentGroup`, `state.d3select`, `state.zoomIdentity` referenced consistently between Tasks 3, 4, 5, 6, 7. `loadCachedPositions` returns `{nodes, view}` consistently after Task 3. `saveCachedPositions(canvas, nodes, view, pinned)` signature consistent across Tasks 3, 4, 5. `persistCacheDebounced()` and `flushCache()` defined in Task 4, called from Tasks 4, 5, 6, 7. `resetView` and `resetPositions` defined in Task 6, attached to chip click handlers in same task. `wasDragged` flag set in Task 5 drag-end, consumed + reset in same task's click handler.

**Scope check:** Single coherent slice (graph manipulation); spec is ~450 lines, plan is ~10 tasks. Proportional. No subsystem decomposition needed.