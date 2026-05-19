// Research graph runtime. Uses d3-force for layout; renders to SVG.
// Spec: docs/superpowers/specs/2026-05-11-research-graph-design.md §5.6.

const PANEL_KEY = 'research-graph-open';
const POSITIONS_KEY = 'research-graph-positions';

const state = {
  data: null,
  panel: null,
  panelOpen: false,
  svg: null,
  simulation: null,
  contentGroup: null,
  filters: { tag: 'all', status: 'all' },
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
// Returns the active graph canvas element (the standalone /research/graph/
// page's canvas, or the side panel's canvas), or null if neither is
// mounted. The standalone page takes precedence because it can coexist
// with state.panel = null.
function getActiveCanvas() {
  if (document.querySelector('.research-graph-page')) {
    return document.querySelector('.research-graph-page .research-graph-canvas');
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
// the active filters and the canvas viewport. Research graph always renders
// all nodes (no local N-hop mode), so the cache is shared across /research/
// and /research/graph/.
function positionsCacheKey(canvas) {
  const f = state.filters;
  return `${f.tag}|${f.status}|${canvas.clientWidth}x${canvas.clientHeight}`;
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
    console.warn('research-graph: dropping unreadable positions cache', e);
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
    // QuotaExceededError on small-budget sessionStorage (rare for ~14 KB),
    // SecurityError in locked-down contexts, or JSON.stringify on a node
    // with a custom toJSON throwing. Don't blow up the graph runtime; just
    // log so a developer can spot it.
    console.warn('research-graph: positions cache write failed', e);
  }
}

function isMobile() {
  return window.matchMedia('(max-width: 720px)').matches;
}

// Node radius is the contract that backs the legend's "size = link count":
// r = NODE_R_MIN + (degree × NODE_R_PER_DEGREE), clamped to NODE_R_MAX.
// Tweak these if a future fixture set makes high-degree nodes feel too
// uniform or low-degree ones too thin to click.
const NODE_R_MIN = 5;
const NODE_R_MAX = 16;
const NODE_R_PER_DEGREE = 1.5;
function nodeRadius(degree) {
  return Math.min(NODE_R_MAX, Math.max(NODE_R_MIN, NODE_R_MIN + degree * NODE_R_PER_DEGREE));
}

function parseData() {
  const el = document.getElementById('research-graph-data');
  if (!el) return null;
  try {
    const raw = JSON.parse(el.textContent);
    // Build deterministic palette index from themePaletteOrder (sorted by weight).
    const paletteOrder = raw.themePaletteOrder || [];
    const paletteIndex = (slug) => {
      const idx = paletteOrder.indexOf(slug);
      return idx >= 0 ? idx : 0;
    };
    // Flatten themes + questions into a unified nodes array.
    const nodes = [
      ...(raw.themes || []).map(t => ({
        slug: t.slug,
        title: t.title,
        kind: 'theme',
        status: t.status,
        tags: t.tags || [],
        themeColorIdx: paletteIndex(t.slug),
        degree: t.degree || 0,
      })),
      ...(raw.questions || []).map(q => ({
        slug: q.slug,
        title: q.title,
        kind: 'question',
        theme: q.theme,
        status: q.status,
        tags: q.tags || [],
        themeColorIdx: paletteIndex(q.theme),
        degree: q.degree || 0,
      })),
    ];
    // Normalize edges: kind field replaces the boolean crossTopic.
    const edges = (raw.edges || []).map(e => ({
      source: e.source,
      target: e.target,
      kind: e.kind || 'parent-child',
      via: e.via || null,
    }));
    return { nodes, edges };
  } catch { return null; }
}

function applyFilters() {
  if (!state.data) return { nodes: [], edges: [] };
  const f = state.filters;
  let nodes = state.data.nodes;
  // Tag filter: multi-select (stored as comma-joined string 'tag1,tag2' or 'all').
  if (f.tag !== 'all') {
    const tags = f.tag.split(',').filter(Boolean);
    nodes = nodes.filter(n => tags.every(t => (n.tags || []).includes(t)));
  }
  // Status filter: single-select; applies to questions only (themes always visible).
  if (f.status !== 'all') {
    nodes = nodes.filter(n => n.kind === 'theme' || n.status === f.status);
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
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', `Force-directed research graph of ${nodes.length} node(s)`);
  const desc = document.createElementNS(SVG_NS, 'desc');
  desc.textContent = `Research graph with ${nodes.length} nodes and ${edges.length} edges. Click a node to navigate to its hub page.`;
  svg.appendChild(desc);

  const contentGroup = document.createElementNS(SVG_NS, 'g');
  contentGroup.setAttribute('class', 'graph-content');
  svg.appendChild(contentGroup);

  const edgeLayer = document.createElementNS(SVG_NS, 'g');
  edgeLayer.setAttribute('class', 'research-graph-edges');
  contentGroup.appendChild(edgeLayer);
  const nodeLayer = document.createElementNS(SVG_NS, 'g');
  nodeLayer.setAttribute('class', 'research-graph-nodes');
  contentGroup.appendChild(nodeLayer);

  // Build edge elements
  const edgeEls = edges.map(e => {
    const line = document.createElementNS(SVG_NS, 'line');
    line.setAttribute('class', e.kind === 'cross-theme'
      ? 'research-graph-edge research-graph-edge-cross-theme'
      : 'research-graph-edge');
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

  // Build node elements — themes get <rect>, questions get <circle>.
  // data-theme-color drives fill via CSS §31; data-status surfaces for filtering.
  const nodeEls = nodes.map(n => {
    const g = document.createElementNS(SVG_NS, 'g');
    g.setAttribute('class', `research-graph-node research-graph-node-${n.kind}`
      + (state.page.currentSlug && n.slug === state.page.currentSlug ? ' is-here' : ''));
    g.setAttribute('data-theme-color', String(n.themeColorIdx));
    g.setAttribute('data-status', n.status || '');
    g.setAttribute('tabindex', '0');
    g.setAttribute('role', 'link');
    g.setAttribute('aria-label', n.title);
    g.dataset.slug = n.slug;

    const r = nodeRadius(n.degree);
    if (n.kind === 'theme') {
      // Themes render as squares (rect centered on the node's position).
      const rect = document.createElementNS(SVG_NS, 'rect');
      rect.setAttribute('width',  String(r * 1.6));
      rect.setAttribute('height', String(r * 1.6));
      rect.setAttribute('x', String(-r * 0.8));
      rect.setAttribute('y', String(-r * 0.8));
      g.appendChild(rect);
    } else {
      // Questions render as circles.
      const c = document.createElementNS(SVG_NS, 'circle');
      c.setAttribute('r', String(r));
      g.appendChild(c);
    }

    const t = document.createElementNS(SVG_NS, 'text');
    t.textContent = n.title;
    t.setAttribute('x', String(r + 3));
    t.setAttribute('y', '3');
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
    const slug = g.dataset.slug;
    const d = g.__data__;
    // Navigate by node kind: themes → /research/themes/<slug>/;
    // questions → /research/questions/<slug>/.
    const url = d && d.kind === 'theme'
      ? `/research/themes/${slug}/`
      : `/research/questions/${slug}/`;
    window.location.assign(url);
  }
  nodeLayer.addEventListener('click', (e) => {
    const g = e.target.closest('.research-graph-node');
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
    const g = e.target.closest('.research-graph-node');
    if (!g || !nodeLayer.contains(g)) return;
    e.preventDefault();
    openSlugForElement(g);
  });

  canvas.replaceChildren(svg);

  const zoomBehavior = zoom()
    .scaleExtent([0.3, 4])
    .filter(event => !event.target.closest('.research-graph-node'))
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
    .force('link', forceLink(edges).id(d => d.slug).distance(60).strength(0.6))
    .force('charge', forceManyBody().strength(-180))
    .force('center', forceCenter(w / 2, h / 2))
    .force('collide', forceCollide().radius(d => nodeRadius(d.degree) + 4));

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

const PANEL_WIDTH_KEY = 'research-graph-panel-width';
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
  if (state.panel.querySelector('.graph-panel-resize')) return;

  const handle = document.createElement('div');
  handle.className = 'graph-panel-resize';
  handle.setAttribute('role', 'separator');
  handle.setAttribute('aria-orientation', 'vertical');
  handle.setAttribute('aria-label', 'Resize graph panel');
  state.panel.appendChild(handle);

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

// Filter chips use aria-pressed toggle semantics (each chip is "currently
// selected or not" within its dimension); action chips are one-shot buttons.
// Different semantics, different visual treatment (.chip vs .chip-action),
// different builder concerns — separate them.

// Returns true when the chip's value is "active" for the given dim.
// Tag dim: comma-joined multi-select — value is active when it appears in the
// joined string (or the joined string equals 'all' and this is the All chip).
// Other dims: single-select — active when the stored value equals chip value.
function chipIsActive(dim, value) {
  if (dim === 'tag') {
    if (value === 'all') return state.filters.tag === 'all' || state.filters.tag === '';
    const active = state.filters.tag.split(',').filter(Boolean);
    return active.includes(value);
  }
  return state.filters[dim] === value;
}

function makeFilterChip(host, label, dim, value) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'graph-chip';
  b.dataset.dim = dim;
  b.dataset.value = value;
  b.setAttribute('aria-pressed', chipIsActive(dim, value) ? 'true' : 'false');
  b.textContent = label;
  b.addEventListener('click', () => {
    if (dim === 'tag') {
      if (value === 'all') {
        // All chip clears the tag selection.
        state.filters.tag = 'all';
      } else {
        // Toggle: add when absent, remove when present.
        const current = state.filters.tag === 'all' ? [] : state.filters.tag.split(',').filter(Boolean);
        const idx = current.indexOf(value);
        if (idx >= 0) {
          current.splice(idx, 1);
        } else {
          current.push(value);
        }
        state.filters.tag = current.length ? current.join(',') : 'all';
      }
    } else {
      // Single-select: replace.
      state.filters[dim] = value;
    }
    // Re-sync aria-pressed on all chips for this dimension.
    host.querySelectorAll(`button[data-dim="${dim}"]`).forEach(c => {
      c.setAttribute('aria-pressed', chipIsActive(dim, c.dataset.value) ? 'true' : 'false');
    });
    rebuildGraph();
  });
  return b;
}

function makeActionChip(label, onClick) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'graph-action';
  b.textContent = label;
  b.addEventListener('click', onClick);
  return b;
}

function buildFilterChips(host) {
  const tags = new Set();
  const statuses = new Set();
  state.data.nodes.forEach(n => {
    (n.tags || []).forEach(t => tags.add(t));
    if (n.status) statuses.add(n.status);
  });

  // Tag dim — multi-select
  const tagLabel = document.createElement('span'); tagLabel.className = 'label'; tagLabel.textContent = 'Tag:';
  host.append(tagLabel, makeFilterChip(host, 'All', 'tag', 'all'));
  Array.from(tags).sort().forEach(t => host.appendChild(makeFilterChip(host, t, 'tag', t)));

  // Status dim — single-select; applies to questions only
  const statusLabel = document.createElement('span'); statusLabel.className = 'label'; statusLabel.textContent = 'Status:';
  host.append(statusLabel, makeFilterChip(host, 'All', 'status', 'all'));
  ['active', 'dormant', 'answered']
    .filter(s => statuses.has(s))
    .forEach(s => host.appendChild(makeFilterChip(host, s, 'status', s)));
}

function buildActionChips(host) {
  const divider = document.createElement('span');
  divider.className = 'graph-toolbar-divider';
  divider.setAttribute('aria-hidden', 'true');
  const hint = document.createElement('span');
  hint.className = 'graph-hint';
  hint.setAttribute('aria-hidden', 'true');
  hint.innerHTML = '<kbd>Shift</kbd>+drag to pin';
  host.append(
    divider,
    makeActionChip('Reset view', resetView),
    makeActionChip('Reset positions', resetPositions),
    hint,
  );
}

function buildToolbar(host) {
  if (!state.data) return;
  host.replaceChildren();
  buildFilterChips(host);
  buildActionChips(host);
}


function openPanel({ animate = true } = {}) {
  if (!state.panel) return;
  if (isMobile()) {
    window.location.assign('/research/graph/');
    return;
  }
  // Adding `.is-animating` enables the CSS transition for the slide. We add
  // it only on user-initiated toggles, not on the silent restore-from-storage
  // path — so navigating between notes never re-animates a panel that was
  // already open.
  if (animate) state.panel.classList.add('is-animating');
  state.panel.setAttribute('aria-hidden', 'false');
  state.panel.removeAttribute('inert');
  state.panelOpen = true;
  try { sessionStorage.setItem(PANEL_KEY, '1'); } catch {}
  document.querySelectorAll('.graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'true'));

  const toolbar = state.panel.querySelector('.graph-toolbar');
  if (toolbar && !toolbar.children.length) buildToolbar(toolbar);
  rebuildGraph();
}

function closePanel() {
  if (!state.panel) return;
  // Close is always user-initiated (button click or Esc) — always animate.
  state.panel.classList.add('is-animating');
  state.panel.setAttribute('aria-hidden', 'true');
  state.panel.setAttribute('inert', '');
  state.panelOpen = false;
  try { sessionStorage.removeItem(PANEL_KEY); } catch {}
  document.querySelectorAll('.graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'false'));
  const toggle = document.querySelector('.graph-toggle');
  if (toggle) toggle.focus();
}

function init() {
  state.data = parseData();
  if (!state.data) return;
  state.panel = document.getElementById('research-graph-panel');
  state.page.isMobile = isMobile();
  const hereBar = document.querySelector('.graph-launcher-bar[data-graph-current]');
  state.page.currentSlug = hereBar ? hereBar.dataset.graphCurrent : null;

  const isGraphPage = !!document.querySelector('.research-graph-page');

  if (isGraphPage) {
    // Standalone /research/graph/ — render immediately; no panel.
    const toolbar = document.querySelector('.research-graph-page .graph-toolbar');
    if (toolbar) buildToolbar(toolbar);
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
