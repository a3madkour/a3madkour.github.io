// Shared d3-force graph runtime. `createGraph(adapter)` returns a per-instance
// controller; the three sections (garden / research / works) supply thin
// adapters with the divergent surface. Design:
// docs/superpowers/specs/2026-07-04-r5.2-graph-core-design.md
//
// MUST stay at assets/js/ depth — the `./vendor/d3-*.min.js` dynamic imports
// below are relative to the compiled bundle, which Hugo emits at js/.
//
// Adapter contract (all methods synchronous unless noted):
//   classPrefix     : string — drives emitted classes: `${p}-graph-node`,
//                     `${p}-graph-edge`, `${p}-graph-nodes`, `${p}-graph-edges`,
//                     and the zoom filter `.${p}-graph-node`.
//   pageSelector    : string — the standalone graph-page canvas selector.
//   panelId         : string — the side-panel element id.
//   graphPageUrl    : string — mobile panel-open redirect target.
//   parseData()     : → bool — read + stash the section's JSON; false if absent.
//   applyFilters()  : → {nodes, edges} — filtered per the adapter's own state.
//   filterCacheKey(): → string — the filter fragment folded into the cache key.
//   nodeRadius(node): → number.
//   renderNode(g,n) : void — set role/aria/extra-classes + append shape into the
//                     core-created <g> (which already carries `${p}-graph-node`,
//                     tabindex, dataset.slug, __data__, and the drag behavior).
//   edgeClass(edge) : → string — full class attribute for the edge <line>.
//   svgAria(counts) : → {label, desc} — {nodeCount, edgeCount} → a11y strings.
//   forceParams     : {linkDistance, linkStrength, chargeStrength, collideRadius(node)}.
//   onNodeClick(n,el): void — navigation.
//   buildToolbar(host, controller): void — build filter + action chips.
//   onSvgCreate?(svg) : void — e.g. works injects its <defs> gradient.
//   onOpenPanel?(panel): void — e.g. garden fills its dynamic legend.
// Controller returned: { rebuild, resetView, resetPositions, openPanel,
//                        closePanel, isPanelOpen, getActiveCanvas, getSvg }.

const SVG_NS = 'http://www.w3.org/2000/svg';

// Filter chips use aria-pressed toggle semantics (single-select within a
// dimension); action chips are one-shot buttons. Shared by adapters that want
// them — an adapter with bespoke chips (e.g. research's multi-select tags) can
// skip these and build its own.
export function makeFilterChip(host, label, dim, value, filters, rebuild) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'graph-chip';
  b.dataset.dim = dim;
  b.dataset.value = value;
  b.setAttribute('aria-pressed', filters[dim] === value ? 'true' : 'false');
  b.textContent = label;
  b.addEventListener('click', () => {
    filters[dim] = value;
    host.querySelectorAll(`button[data-dim="${dim}"]`).forEach(c => {
      c.setAttribute('aria-pressed', c.dataset.value === value ? 'true' : 'false');
    });
    rebuild();
  });
  return b;
}

export function makeActionChip(label, onClick) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'graph-action';
  b.textContent = label;
  b.addEventListener('click', onClick);
  return b;
}

export function buildActionChips(host, { resetView, resetPositions }) {
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

export function createGraph(adapter) {
  const p = adapter.classPrefix;
  const POSITIONS_KEY = `${p}-graph-positions`;
  const PANEL_KEY = `${p}-graph-open`;
  const PANEL_WIDTH_KEY = `${p}-graph-panel-width`;
  const PANEL_MIN = 240;

  const state = {
    panel: null,
    panelOpen: false,
    svg: null,
    simulation: null,
    contentGroup: null,
    viewTransform: { k: 1, tx: 0, ty: 0 },
    pinnedSlugs: new Set(),
    zoomBehavior: null,
    d3select: null,
    zoomIdentity: null,
    renderTick: null,
  };

  let persistTimer = null;
  function persistCacheDebounced() {
    if (persistTimer) clearTimeout(persistTimer);
    persistTimer = setTimeout(() => {
      persistTimer = null;
      flushCache();
    }, 200);
  }

  // The active canvas: the standalone graph-page's canvas takes precedence (it
  // can coexist with a null panel), else the side panel's canvas.
  function getActiveCanvas() {
    const pageCanvas = document.querySelector(adapter.pageSelector);
    if (pageCanvas) return pageCanvas;
    if (state.panel) return state.panel.querySelector('.graph-panel-canvas');
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

  function isMobile() {
    return window.matchMedia('(max-width: 720px)').matches;
  }

  // Cache key encodes everything that changes a node's settled position: the
  // adapter's active filters + the canvas viewport.
  function positionsCacheKey(canvas) {
    return `${adapter.filterCacheKey()}|${canvas.clientWidth}x${canvas.clientHeight}`;
  }

  function loadCachedPositions(canvas) {
    try {
      const raw = sessionStorage.getItem(POSITIONS_KEY);
      if (!raw) return null;
      const cache = JSON.parse(raw);
      const entry = cache[positionsCacheKey(canvas)];
      if (!entry) return null;
      if (Array.isArray(entry)) {
        // Legacy shape: bare array of {slug, x, y}. Normalize.
        return {
          nodes: entry.map(n => ({ slug: n.slug, x: n.x, y: n.y, pinned: false })),
          view: { k: 1, tx: 0, ty: 0 },
        };
      }
      return entry;
    } catch (e) {
      console.warn(`${p}-graph: dropping unreadable positions cache`, e);
      try { sessionStorage.removeItem(POSITIONS_KEY); } catch {}
      return null;
    }
  }

  function saveCachedPositions(canvas, nodes, view, pinned) {
    try {
      const raw = sessionStorage.getItem(POSITIONS_KEY);
      const cache = raw ? JSON.parse(raw) : {};
      cache[positionsCacheKey(canvas)] = {
        nodes: nodes.map(n => ({ slug: n.slug, x: n.x, y: n.y, pinned: pinned.has(n.slug) })),
        view: { k: view.k, tx: view.tx, ty: view.ty },
      };
      sessionStorage.setItem(POSITIONS_KEY, JSON.stringify(cache));
    } catch (e) {
      console.warn(`${p}-graph: positions cache write failed`, e);
    }
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

    // d3-zoom calls selection.interrupt() (d3-transition, which we don't
    // vendor) inside its transform setter. Stub it as a chainable no-op once.
    const selProto = Object.getPrototypeOf(select(document.body));
    if (typeof selProto.interrupt !== 'function') {
      selProto.interrupt = function() { return this; };
    }

    const { nodes, edges } = adapter.applyFilters();
    const w = canvas.clientWidth || 320;
    const h = canvas.clientHeight || 360;

    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    svg.setAttribute('role', 'img');
    const aria = adapter.svgAria({ nodeCount: nodes.length, edgeCount: edges.length });
    svg.setAttribute('aria-label', aria.label);
    const desc = document.createElementNS(SVG_NS, 'desc');
    desc.textContent = aria.desc;
    svg.appendChild(desc);

    adapter.onSvgCreate?.(svg);

    const contentGroup = document.createElementNS(SVG_NS, 'g');
    contentGroup.setAttribute('class', 'graph-content');
    svg.appendChild(contentGroup);

    const edgeLayer = document.createElementNS(SVG_NS, 'g');
    edgeLayer.setAttribute('class', `${p}-graph-edges`);
    contentGroup.appendChild(edgeLayer);
    const nodeLayer = document.createElementNS(SVG_NS, 'g');
    nodeLayer.setAttribute('class', `${p}-graph-nodes`);
    contentGroup.appendChild(nodeLayer);

    const edgeEls = edges.map(e => {
      const line = document.createElementNS(SVG_NS, 'line');
      line.setAttribute('class', adapter.edgeClass(e));
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
        // Defer reheat to the first real drag — reheating on a plain click
        // makes neighbors drift during the navigation that follows.
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
          d.fx = null;
          d.fy = null;
          state.pinnedSlugs.delete(d.slug);
        }
        persistCacheDebounced();
      });

    // Build node <g>s: core owns the shared scaffold (base class, tabindex,
    // dataset, __data__, drag, append); the adapter draws role/aria/shape.
    const nodeEls = nodes.map(n => {
      const g = document.createElementNS(SVG_NS, 'g');
      g.setAttribute('class', `${p}-graph-node`);
      g.setAttribute('tabindex', '0');
      g.dataset.slug = n.slug;
      g.__data__ = n;
      select(g).call(dragBehavior);
      adapter.renderNode(g, n);
      nodeLayer.appendChild(g);
      return { n, g };
    });

    // Delegate click + keydown onto the node layer. Node identity comes from
    // the element's __data__ + dataset.slug, so listeners survive a rebuild.
    function fireNodeClick(g) {
      adapter.onNodeClick(g.__data__, g);
    }
    nodeLayer.addEventListener('click', (e) => {
      const g = e.target.closest(`.${p}-graph-node`);
      if (!g || !nodeLayer.contains(g)) return;
      const d = g.__data__;
      if (d && d.wasDragged) {
        d.wasDragged = false;
        return;
      }
      fireNodeClick(g);
    });
    nodeLayer.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const g = e.target.closest(`.${p}-graph-node`);
      if (!g || !nodeLayer.contains(g)) return;
      e.preventDefault();
      fireNodeClick(g);
    });

    canvas.replaceChildren(svg);

    const zoomBehavior = zoom()
      .scaleExtent([0.3, 4])
      .filter(event => !event.target.closest(`.${p}-graph-node`))
      .on('start', (event) => {
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

    // Restore cached positions if every current node has a cache entry.
    const cached = loadCachedPositions(canvas);
    const cachedBySlug = cached ? new Map(cached.nodes.map(pos => [pos.slug, pos])) : null;
    const cacheHit = cachedBySlug && nodes.every(n => cachedBySlug.has(n.slug));
    if (cacheHit) {
      nodes.forEach(n => {
        const pos = cachedBySlug.get(n.slug);
        n.x = pos.x;
        n.y = pos.y;
        if (pos.pinned) {
          n.fx = pos.x;
          n.fy = pos.y;
          state.pinnedSlugs.add(n.slug);
        }
      });
      const v = cached.view;
      contentGroup.setAttribute('transform', `translate(${v.tx},${v.ty}) scale(${v.k})`);
      state.viewTransform = { k: v.k, tx: v.tx, ty: v.ty };
      select(svg).call(
        zoomBehavior.transform,
        zoomIdentity.translate(v.tx, v.ty).scale(v.k)
      );
    }

    const fp = adapter.forceParams;
    const sim = forceSimulation(nodes)
      .force('link', forceLink(edges).id(d => d.slug).distance(fp.linkDistance).strength(fp.linkStrength))
      .force('charge', forceManyBody().strength(fp.chargeStrength))
      .force('center', forceCenter(w / 2, h / 2))
      .force('collide', forceCollide().radius(d => fp.collideRadius(d)));

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

    // Cache hit → nodes already at settled positions; render without ticking.
    // Miss → pre-tick to convergence and store for the next mount this session.
    sim.stop();
    if (!cacheHit) {
      for (let i = 0; i < 300; i++) sim.tick();
      saveCachedPositions(canvas, nodes, state.viewTransform, state.pinnedSlugs);
    }
    renderTick();

    return { svg, simulation: sim, contentGroup };
  }

  function rebuild() {
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
  }

  function resetPositions() {
    if (!state.simulation) return;
    const sim = state.simulation;
    sim.nodes().forEach(n => { n.fx = null; n.fy = null; });
    state.pinnedSlugs.clear();
    if (reducedMotion()) {
      sim.alpha(0.5);
      for (let i = 0; i < 300; i++) sim.tick();
      if (state.renderTick) state.renderTick();
      flushCache();
      return;
    }
    sim.alpha(0.5).restart();
    sim.on('end.reset', () => {
      sim.on('end.reset', null);
      flushCache();
    });
  }

  function panelMaxWidth() { return Math.round(window.innerWidth * 0.8); }

  function applySavedPanelWidth() {
    if (!state.panel) return;
    try {
      const saved = localStorage.getItem(PANEL_WIDTH_KEY);
      if (!saved) return;
      const wid = parseInt(saved, 10);
      if (!Number.isFinite(wid)) return;
      const clamped = Math.max(PANEL_MIN, Math.min(panelMaxWidth(), wid));
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

  function openPanel({ animate = true } = {}) {
    if (!state.panel) return;
    if (isMobile()) {
      window.location.assign(adapter.graphPageUrl);
      return;
    }
    if (animate) state.panel.classList.add('is-animating');
    state.panel.setAttribute('aria-hidden', 'false');
    state.panel.removeAttribute('inert');
    state.panelOpen = true;
    try { sessionStorage.setItem(PANEL_KEY, '1'); } catch {}
    document.querySelectorAll('.graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'true'));

    const toolbar = state.panel.querySelector('.graph-toolbar');
    if (toolbar && !toolbar.children.length) adapter.buildToolbar(toolbar, controller);
    adapter.onOpenPanel?.(state.panel);
    rebuild();
  }

  function closePanel() {
    if (!state.panel) return;
    state.panel.classList.add('is-animating');
    state.panel.setAttribute('aria-hidden', 'true');
    state.panel.setAttribute('inert', '');
    state.panelOpen = false;
    try { sessionStorage.removeItem(PANEL_KEY); } catch {}
    document.querySelectorAll('.graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'false'));
    const toggle = document.querySelector('.graph-toggle');
    if (toggle) toggle.focus();
  }

  state.panel = document.getElementById(adapter.panelId);

  const controller = {
    rebuild,
    resetView,
    resetPositions,
    openPanel,
    closePanel,
    isPanelOpen: () => state.panelOpen,
    getActiveCanvas,
    getSvg: () => state.svg,
    applySavedPanelWidth,
    setupPanelResize,
    isMobile,
  };
  return controller;
}
