// Works constellation graph runtime. Uses d3-force for layout; renders to SVG.
// Spec: docs/superpowers/specs/2026-05-12-works-umbrella-polish-design.md §3.4.
//
// Copy + trim of research-graph.js with three structural differences:
//   - Every node is the same shape: a rounded-rect badge background with an
//     inline <use href="#g-{medium}"> glyph (from partials/works/glyph-sprite).
//   - Edges classify as "tag-share" (solid) or "cross-ref" (dashed).
//   - In-panel filter chips only carry a "medium" dimension. Tag-level
//     filtering is owned by the umbrella's top-strip filter-chips and is not
//     mirrored here (the panel and the tiles filter independently).

const PANEL_KEY = 'works-graph-open';
const POSITIONS_KEY = 'works-graph-positions';

const state = {
  data: null,
  panel: null,
  panelOpen: false,
  svg: null,
  simulation: null,
  contentGroup: null,
  filters: { medium: 'all' },
  page: { isMobile: false },
  viewTransform: { k: 1, tx: 0, ty: 0 },
  pinnedSlugs: new Set(),
  zoomBehavior: null,
  d3select: null,
  zoomIdentity: null,
};

let persistTimer = null;
function persistCacheDebounced() {
  if (persistTimer) clearTimeout(persistTimer);
  persistTimer = setTimeout(() => {
    persistTimer = null;
    flushCache();
  }, 200);
}
// Returns the active graph canvas element (the standalone /works/graph/
// page's canvas, or the side panel's canvas), or null if neither is
// mounted. The standalone page takes precedence because it can coexist
// with state.panel = null.
function getActiveCanvas() {
  if (document.querySelector('.works-graph-page')) {
    return document.querySelector('.works-graph-page .works-graph-canvas');
  }
  if (state.panel) {
    return state.panel.querySelector('.graph-panel-canvas');
  }
  return null;
}

function flushCache() {
  const canvas = getActiveCanvas();
  if (!canvas || !state.simulation) return;
  saveCachedPositions(canvas, state.simulation.nodes(), state.viewTransform, state.pinnedSlugs);
}

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// Cache key encodes everything that would change a node's settled position:
// the active filters and the canvas viewport. Works graph always renders
// all nodes (no local N-hop mode), so the cache is shared across /works/
// and /works/graph/.
function positionsCacheKey(canvas) {
  const f = state.filters;
  return `${f.medium}|${canvas.clientWidth}x${canvas.clientHeight}`;
}

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
  } catch (e) {
    // Corrupt JSON or a SecurityError on sessionStorage. Drop the whole key
    // rather than fail every page load; the next save will rebuild it.
    console.warn('works-graph: dropping unreadable positions cache', e);
    try { sessionStorage.removeItem(POSITIONS_KEY); } catch {}
    return null;
  }
}

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
  } catch (e) {
    // QuotaExceededError on small-budget sessionStorage, SecurityError in
    // locked-down contexts, or JSON.stringify on a node with a custom toJSON
    // throwing. Don't blow up the graph runtime; just log so a developer
    // can spot it.
    console.warn('works-graph: positions cache write failed', e);
  }
}

function isMobile() {
  return window.matchMedia('(max-width: 720px)').matches;
}

// Badge + glyph sizes are the contract that backs the legend's "featured =
// larger badge". Featured nodes get a 72-px badge with a 40-px glyph;
// regular nodes get a 52-px badge with a 30-px glyph. The spec §3.4 calls
// these out explicitly.
const BADGE_REGULAR = 36;
const BADGE_FEATURED = 48;
const GLYPH_REGULAR = 20;
const GLYPH_FEATURED = 28;
function badgeSize(featured) { return featured ? BADGE_FEATURED : BADGE_REGULAR; }
function glyphSize(featured) { return featured ? GLYPH_FEATURED : GLYPH_REGULAR; }
// Collide radius for the simulation — half the badge size plus a generous gap.
// The gap (not the badge size) is what actually pushes nodes apart visually.
function nodeRadius(featured) { return badgeSize(featured) / 2 + 38; }

function parseData() {
  const el = document.getElementById('works-graph-data');
  if (!el) return null;
  try {
    const raw = JSON.parse(el.textContent);
    const nodes = (raw.nodes || []).map(n => ({
      slug: n.slug,
      title: n.title,
      url: n.url,
      medium: n.medium,
      tags: n.tags || [],
      featured: !!n.featured,
      year: n.year || 0,
    }));
    // Normalize edges: kind field is "tag-share" | "cross-ref".
    const edges = (raw.edges || []).map(e => ({
      source: e.source,
      target: e.target,
      kind: e.kind || 'tag-share',
      via: e.via || null,
      shared: e.shared || null,
      weight: e.weight || 1,
    }));
    return { nodes, edges };
  } catch { return null; }
}

// The toolbar's medium chips use the plural form ("games") to stay consistent
// with the umbrella's top-strip filter dim values. Node data uses singular
// ("game"). Map plural→singular here so the chip click can match.
function mediumSingular(plural) {
  if (plural === 'games') return 'game';
  if (plural === 'music') return 'music';
  if (plural === 'poetry') return 'poetry';
  return plural;
}

function applyFilters() {
  if (!state.data) return { nodes: [], edges: [] };
  const f = state.filters;
  let nodes = state.data.nodes;
  // Medium filter: single-select.
  if (f.medium !== 'all') {
    const want = mediumSingular(f.medium);
    nodes = nodes.filter(n => n.medium === want);
  }
  const allowed = new Set(nodes.map(n => n.slug));
  const edges = state.data.edges.filter(e => allowed.has(e.source) && allowed.has(e.target));
  return { nodes: nodes.map(n => ({ ...n })), edges: edges.map(e => ({ ...e })) };
}

async function buildSimulation(canvas) {
  const { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } =
    await import('./vendor/d3-force.min.js');
  const { zoom, zoomIdentity } = await import('./vendor/d3-zoom.min.js');
  const { drag } = await import('./vendor/d3-drag.min.js');
  const { select } = await import('./vendor/d3-selection.min.js');
  state.d3select = select;
  state.zoomIdentity = zoomIdentity;
  state.pinnedSlugs = new Set();
  state.viewTransform = { k: 1, tx: 0, ty: 0 };

  // d3-zoom calls selection.interrupt() inside its transform setter to cancel
  // in-progress zoom transitions. That method lives in d3-transition, which we
  // don't vendor. Stub it as a chainable no-op on the d3-selection prototype
  // so zoomBehavior.transform(...) works without dragging in d3-transition.
  const selProto = Object.getPrototypeOf(select(document.body));
  if (typeof selProto.interrupt !== 'function') {
    selProto.interrupt = function() { return this; };
  }

  const { nodes, edges } = applyFilters();
  const w = canvas.clientWidth || 320;
  const h = canvas.clientHeight || 360;

  const SVG_NS = 'http://www.w3.org/2000/svg';

  // The canvas is already an <svg> (rendered by partials/works/graph-panel.html
  // or the standalone graph page); set the viewBox + a11y, then build inner
  // structure into it. If for any reason it isn't an <svg>, create one and
  // mount it as a child below.
  let svg;
  if (canvas.tagName && canvas.tagName.toLowerCase() === 'svg') {
    svg = canvas;
  } else {
    svg = document.createElementNS(SVG_NS, 'svg');
  }
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', `Force-directed works constellation of ${nodes.length} node(s)`);
  // Clear any prior children before rebuilding.
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const desc = document.createElementNS(SVG_NS, 'desc');
  desc.textContent = `Works constellation with ${nodes.length} nodes and ${edges.length} edges. Click a node to navigate to its page.`;
  svg.appendChild(desc);

  // <defs> with the badge gradient (referenced by CSS §36
  // .works-graph-node-badge { fill: url(#works-graph-badge-gradient); }).
  const defs = document.createElementNS(SVG_NS, 'defs');
  const grad = document.createElementNS(SVG_NS, 'linearGradient');
  grad.setAttribute('id', 'works-graph-badge-gradient');
  grad.setAttribute('x1', '0');
  grad.setAttribute('y1', '0');
  grad.setAttribute('x2', '1');
  grad.setAttribute('y2', '1');
  const stop1 = document.createElementNS(SVG_NS, 'stop');
  stop1.setAttribute('offset', '0%');
  stop1.setAttribute('stop-color', 'var(--color-burgundy)');
  stop1.setAttribute('stop-opacity', '0.10');
  const stop2 = document.createElementNS(SVG_NS, 'stop');
  stop2.setAttribute('offset', '100%');
  stop2.setAttribute('stop-color', 'var(--color-steel)');
  stop2.setAttribute('stop-opacity', '0.08');
  grad.appendChild(stop1);
  grad.appendChild(stop2);
  defs.appendChild(grad);
  svg.appendChild(defs);

  const contentGroup = document.createElementNS(SVG_NS, 'g');
  contentGroup.setAttribute('class', 'graph-content');
  svg.appendChild(contentGroup);

  const edgeLayer = document.createElementNS(SVG_NS, 'g');
  edgeLayer.setAttribute('class', 'works-graph-edges');
  contentGroup.appendChild(edgeLayer);
  const nodeLayer = document.createElementNS(SVG_NS, 'g');
  nodeLayer.setAttribute('class', 'works-graph-nodes');
  contentGroup.appendChild(nodeLayer);

  // Build edge elements — solid for tag-share, dashed for cross-ref.
  const edgeEls = edges.map(e => {
    const line = document.createElementNS(SVG_NS, 'line');
    line.setAttribute('class', e.kind === 'cross-ref'
      ? 'works-graph-edge works-graph-edge-cross-ref'
      : 'works-graph-edge works-graph-edge-tag-share');
    edgeLayer.appendChild(line);
    return { e, line };
  });

  const dragBehavior = drag()
    .subject(function() { return this.__data__; })
    .on('start', function(event) {
      const d = event.subject;
      d.fx = d.x;
      d.fy = d.y;
      d.__startX = d.x;
      d.__startY = d.y;
      d.wasDragged = false;
      d.__reheated = false;
      svg.classList.add('is-dragging-node');
      // Do NOT reheat here — every click triggers start, and reheating on a
      // click makes neighbors visibly drift during the navigation that follows.
      // Defer the reheat to the first real `drag` event below.
    })
    .on('drag', function(event) {
      const d = event.subject;
      d.fx = event.x;
      d.fy = event.y;
      if (!d.__reheated && !reducedMotion()) {
        sim.alphaTarget(0.3).restart();
        d.__reheated = true;
      }
    })
    .on('end', function(event) {
      const d = event.subject;
      svg.classList.remove('is-dragging-node');
      if (d.__reheated && !reducedMotion()) sim.alphaTarget(0);
      const dx = d.fx - d.__startX;
      const dy = d.fy - d.__startY;
      const moved = (dx * dx + dy * dy) > 9;
      const shouldPin = moved && event.sourceEvent && event.sourceEvent.shiftKey;
      if (moved) d.wasDragged = true;
      if (shouldPin) {
        state.pinnedSlugs.add(d.slug);
      } else {
        // Plain drag (no Shift) OR pure click — release any pin. Shift+drag is
        // the opt-in gesture for "place this node and keep it there."
        d.fx = null;
        d.fy = null;
        state.pinnedSlugs.delete(d.slug);
      }
      persistCacheDebounced();
    });

  // Build node elements — every node is a <g> with a rounded-rect badge plus
  // an inline <use href="#g-{medium}"> glyph from the sprite. Featured nodes
  // get the larger 72-px badge + 40-px glyph; regular nodes get 52 + 30.
  const nodeEls = nodes.map(n => {
    const g = document.createElementNS(SVG_NS, 'g');
    g.setAttribute('class', `works-graph-node${n.featured ? ' works-graph-node-featured' : ''}`);
    g.setAttribute('data-medium', n.medium);
    g.setAttribute('data-featured', n.featured ? 'true' : 'false');
    g.setAttribute('tabindex', '0');
    g.setAttribute('role', 'link');
    g.setAttribute('aria-label', n.title);
    g.dataset.slug = n.slug;
    g.dataset.url = n.url;

    const size = badgeSize(n.featured);
    const half = size / 2;
    const rect = document.createElementNS(SVG_NS, 'rect');
    rect.setAttribute('class', 'works-graph-node-badge');
    rect.setAttribute('width', String(size));
    rect.setAttribute('height', String(size));
    rect.setAttribute('x', String(-half));
    rect.setAttribute('y', String(-half));
    rect.setAttribute('rx', '10');
    rect.setAttribute('ry', '10');
    g.appendChild(rect);

    const gsize = glyphSize(n.featured);
    const ghalf = gsize / 2;
    const use = document.createElementNS(SVG_NS, 'use');
    use.setAttribute('class', 'works-graph-node-glyph');
    use.setAttribute('href', `#g-${n.medium}`);
    use.setAttribute('x', String(-ghalf));
    use.setAttribute('y', String(-ghalf));
    use.setAttribute('width', String(gsize));
    use.setAttribute('height', String(gsize));
    g.appendChild(use);

    const t = document.createElementNS(SVG_NS, 'text');
    t.setAttribute('class', 'works-graph-node-label');
    t.setAttribute('text-anchor', 'middle');
    t.setAttribute('x', '0');
    t.setAttribute('y', String(half + 14));
    t.textContent = n.title;
    g.appendChild(t);

    g.__data__ = n;
    select(g).call(dragBehavior);

    nodeLayer.appendChild(g);
    return { n, g };
  });

  // Delegate click + keydown for all nodes onto the node layer instead of
  // attaching two listeners per node. Node identity comes from the SVG
  // element's `__data__` (set above) and its `dataset.slug`, not from a
  // per-node closure — so the listeners survive a rebuild and don't grow
  // with the graph.
  function openSlugForElement(g) {
    const url = g.dataset.url;
    if (url) window.location.assign(url);
  }
  nodeLayer.addEventListener('click', (e) => {
    const g = e.target.closest('.works-graph-node');
    if (!g || !nodeLayer.contains(g)) return;
    const d = g.__data__;
    if (d && d.wasDragged) {
      d.wasDragged = false;
      return;
    }
    openSlugForElement(g);
  });
  nodeLayer.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const g = e.target.closest('.works-graph-node');
    if (!g || !nodeLayer.contains(g)) return;
    e.preventDefault();
    openSlugForElement(g);
  });

  // If we created a fresh <svg> (canvas wasn't already an svg), mount it.
  if (svg !== canvas) {
    canvas.replaceChildren(svg);
  }

  const zoomBehavior = zoom()
    .scaleExtent([0.3, 4])
    .filter(event => !event.target.closest('.works-graph-node'))
    .on('start', (event) => {
      // Wheel-zoom also fires start/end; only flip the cursor for drag-pan.
      if (event.sourceEvent && event.sourceEvent.type !== 'wheel') {
        svg.classList.add('is-panning');
      }
    })
    .on('zoom', ({ transform }) => {
      contentGroup.setAttribute(
        'transform',
        `translate(${transform.x},${transform.y}) scale(${transform.k})`
      );
      state.viewTransform = { k: transform.k, tx: transform.x, ty: transform.y };
      persistCacheDebounced();
    })
    .on('end', () => {
      svg.classList.remove('is-panning');
    });

  select(svg).call(zoomBehavior).on('dblclick.zoom', null);
  state.zoomBehavior = zoomBehavior;

  // Restore cached positions if all current nodes have a cache entry.
  // Hit → skip the simulation entirely (instant, byte-stable layout).
  // Miss or partial → run a fresh settle and save the result.
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

  const sim = forceSimulation(nodes)
    .force('link', forceLink(edges).id(d => d.slug).distance(160).strength(0.35))
    .force('charge', forceManyBody().strength(-700))
    .force('center', forceCenter(w / 2, h / 2))
    .force('collide', forceCollide().radius(d => nodeRadius(d.featured)));

  function renderTick() {
    edgeEls.forEach(({ e, line }) => {
      line.setAttribute('x1', e.source.x);
      line.setAttribute('y1', e.source.y);
      line.setAttribute('x2', e.target.x);
      line.setAttribute('y2', e.target.y);
    });
    nodeEls.forEach(({ n, g }) => {
      g.setAttribute('transform', `translate(${n.x}, ${n.y})`);
    });
  }

  sim.on('tick', renderTick);
  state.renderTick = renderTick;

  // On cache hit, nodes already start at their settled positions — render
  // directly without ticking. On cache miss, pre-tick to convergence and
  // store the result for the next mount within this session.
  sim.stop();
  if (!cacheHit) {
    for (let i = 0; i < 300; i++) sim.tick();
    saveCachedPositions(canvas, nodes, state.viewTransform, state.pinnedSlugs);
  }
  renderTick();

  return { svg, simulation: sim, contentGroup };
}

function rebuildGraph() {
  const canvas = getActiveCanvas();
  if (!canvas) return;
  if (state.simulation) state.simulation.stop();
  buildSimulation(canvas).then(({ svg, simulation, contentGroup }) => {
    state.svg = svg;
    state.simulation = simulation;
    state.contentGroup = contentGroup;
  });
}

function resetView() {
  if (!state.zoomBehavior || !state.svg || !state.d3select || !state.zoomIdentity) return;
  state.d3select(state.svg).call(state.zoomBehavior.transform, state.zoomIdentity);
  // The 'zoom' handler attached in buildSimulation will fire once and update
  // state.viewTransform + schedule a debounced cache flush.
}

function resetPositions() {
  if (!state.simulation) return;
  const sim = state.simulation;
  sim.nodes().forEach(n => {
    n.fx = null;
    n.fy = null;
  });
  state.pinnedSlugs.clear();
  // Under reduced motion, settle synchronously and persist immediately —
  // matches the build-time fast path and skips the unwanted animation.
  if (reducedMotion()) {
    sim.alpha(0.5);
    for (let i = 0; i < 300; i++) sim.tick();
    if (state.renderTick) state.renderTick();
    flushCache();
    return;
  }
  // Animate to convergence, then persist once — debounced persist would
  // capture mid-settle positions and bake them into the cache.
  sim.alpha(0.5).restart();
  sim.on('end.reset', () => {
    sim.on('end.reset', null);
    flushCache();
  });
}

const PANEL_WIDTH_KEY = 'works-graph-panel-width';
const PANEL_MIN = 240;
function panelMaxWidth() { return Math.round(window.innerWidth * 0.8); }

function applySavedPanelWidth() {
  if (!state.panel) return;
  try {
    const saved = localStorage.getItem(PANEL_WIDTH_KEY);
    if (!saved) return;
    const w = parseInt(saved, 10);
    if (!Number.isFinite(w)) return;
    const clamped = Math.max(PANEL_MIN, Math.min(panelMaxWidth(), w));
    state.panel.style.width = `${clamped}px`;
  } catch {}
}

function setupPanelResize() {
  if (!state.panel) return;
  // The works graph-panel partial pre-renders the resize handle; wire it up
  // in place if found, otherwise create one (parity with research-graph).
  let handle = state.panel.querySelector('.graph-panel-resize');
  if (!handle) {
    handle = document.createElement('div');
    handle.className = 'graph-panel-resize';
    handle.setAttribute('role', 'separator');
    handle.setAttribute('aria-orientation', 'vertical');
    handle.setAttribute('aria-label', 'Resize graph panel');
    state.panel.appendChild(handle);
  }
  if (handle.dataset.wired === 'true') return;
  handle.dataset.wired = 'true';

  let startX = 0;
  let startWidth = 0;
  let pointerId = null;

  function onMove(ev) {
    const dx = startX - ev.clientX; // dragging left widens the panel
    const next = Math.max(PANEL_MIN, Math.min(panelMaxWidth(), startWidth + dx));
    state.panel.style.width = `${next}px`;
  }
  function onUp() {
    if (pointerId !== null) {
      try { handle.releasePointerCapture(pointerId); } catch {}
      pointerId = null;
    }
    handle.classList.remove('is-resizing');
    document.body.style.removeProperty('cursor');
    handle.removeEventListener('pointermove', onMove);
    handle.removeEventListener('pointerup', onUp);
    handle.removeEventListener('pointercancel', onUp);
    try {
      const finalWidth = parseInt(state.panel.style.width, 10);
      if (Number.isFinite(finalWidth)) {
        localStorage.setItem(PANEL_WIDTH_KEY, String(finalWidth));
      }
    } catch {}
  }

  handle.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    startX = e.clientX;
    startWidth = state.panel.getBoundingClientRect().width;
    pointerId = e.pointerId;
    try { handle.setPointerCapture(pointerId); } catch {}
    handle.classList.add('is-resizing');
    document.body.style.cursor = 'ew-resize';
    handle.addEventListener('pointermove', onMove);
    handle.addEventListener('pointerup', onUp);
    handle.addEventListener('pointercancel', onUp);
  });
}

// The graph panel's toolbar is rendered by partials/works/graph-panel.html
// with its medium chips + reset buttons already in the markup. This module
// wires click handlers onto the existing elements rather than rebuilding
// them, so the SSR HTML stays the source of truth.
function wireToolbar(toolbar) {
  if (!toolbar) return;
  if (toolbar.dataset.wired === 'true') return;
  toolbar.dataset.wired = 'true';

  toolbar.querySelectorAll('button[data-dim="medium"][data-key]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-key') || 'all';
      state.filters.medium = key;
      toolbar.querySelectorAll('button[data-dim="medium"]').forEach(b => {
        b.setAttribute('aria-pressed', b.getAttribute('data-key') === key ? 'true' : 'false');
      });
      rebuildGraph();
    });
  });

  const resetViewBtn = toolbar.querySelector('button[data-action="reset-view"]');
  if (resetViewBtn) resetViewBtn.addEventListener('click', resetView);
  const resetPosBtn = toolbar.querySelector('button[data-action="reset-positions"]');
  if (resetPosBtn) resetPosBtn.addEventListener('click', resetPositions);
}

function openPanel({ animate = true } = {}) {
  if (!state.panel) return;
  if (isMobile()) {
    window.location.assign('/works/graph/');
    return;
  }
  // Adding `.is-animating` enables the CSS transition for the slide. We add
  // it only on user-initiated toggles, not on the silent restore-from-storage
  // path — so navigating between notes never re-animates a panel that was
  // already open.
  if (animate) state.panel.classList.add('is-animating');
  state.panel.removeAttribute('hidden');
  state.panel.setAttribute('aria-hidden', 'false');
  state.panelOpen = true;
  try { sessionStorage.setItem(PANEL_KEY, '1'); } catch {}
  document.querySelectorAll('.graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'true'));

  const toolbar = state.panel.querySelector('.graph-toolbar');
  wireToolbar(toolbar);
  rebuildGraph();
}

function closePanel() {
  if (!state.panel) return;
  // Close is always user-initiated (button click or Esc) — always animate.
  state.panel.classList.add('is-animating');
  state.panel.setAttribute('aria-hidden', 'true');
  state.panel.setAttribute('hidden', '');
  state.panelOpen = false;
  try { sessionStorage.removeItem(PANEL_KEY); } catch {}
  document.querySelectorAll('.graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'false'));
  const toggle = document.querySelector('.graph-toggle');
  if (toggle) toggle.focus();
}

function init() {
  state.data = parseData();
  if (!state.data) return;
  state.panel = document.getElementById('works-graph-panel');
  state.page.isMobile = isMobile();

  const isGraphPage = !!document.querySelector('.works-graph-page');

  if (isGraphPage) {
    // Standalone /works/graph/ — render immediately; no panel.
    const toolbar = document.querySelector('.works-graph-page .graph-toolbar');
    if (toolbar) wireToolbar(toolbar);
    rebuildGraph();
    return;
  }

  // Apply persisted width + attach resize handle (desktop only — the panel is
  // hidden under 720px via CSS).
  if (state.panel && !isMobile()) {
    applySavedPanelWidth();
    setupPanelResize();
  }

  // Toggle button(s)
  document.querySelectorAll('.graph-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      if (state.panelOpen) closePanel(); else openPanel();
    });
  });

  // Close button inside panel
  if (state.panel) {
    const close = state.panel.querySelector('.graph-panel-close');
    if (close) close.addEventListener('click', closePanel);
  }

  // Esc when panel focused
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!state.panelOpen) return;
    e.stopImmediatePropagation();
    closePanel();
  });

  // Restore panel state
  let restore = false;
  try { restore = sessionStorage.getItem(PANEL_KEY) === '1'; } catch {}
  if (restore && !isMobile()) openPanel({ animate: false });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
