// Garden graph runtime. Uses d3-force for layout; renders to SVG.
// Spec: docs/superpowers/specs/2026-05-08-garden-interactions-design.md §6.

const PANEL_KEY = 'garden-graph-open';
const POSITIONS_KEY = 'garden-graph-positions';
const TAG_PALETTE = {
  // Map well-known tags to existing site tokens.
  // Anything else falls back to --color-ink-fade.
  'narrative': 'var(--color-burgundy)',
  'memory':    'var(--color-green)',
  'games':     'var(--color-steel)',
  'reading':   'var(--color-warn)',
  'calvino':   'var(--color-warn)',
  'play':      'var(--color-steel)',
  'aesthetics':'var(--color-ink-soft)',
};

const state = {
  data: null,
  panel: null,
  panelOpen: false,
  svg: null,
  simulation: null,
  contentGroup: null,
  filters: { tag: 'all', stage: 'all', local: 'all' /* all | 1-hop | 2-hop */ },
  inStack: new Set(),
  page: { isMobile: false, isNotePage: false, currentSlug: null },
  // Tracks user's last pointer interaction: was it inside the stack columns?
  // Used to disambiguate Esc — if user's "attention" is on the stack (last
  // click was in a column), Esc clears the stack; otherwise the open panel
  // claims Esc.
  lastPointerInStack: false,
  // Added this slice:
  viewTransform: { k: 1, tx: 0, ty: 0 },
  pinnedSlugs: new Set(),
  zoomBehavior: null,
};

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// Cache key encodes everything that would change a node's settled position:
// the active filters, the focused note (for local-graph mode), and the
// canvas viewport. Different (panel vs page) viewports legitimately have
// different layouts so they get separate cache entries.
function positionsCacheKey(canvas) {
  const f = state.filters;
  return `${f.tag}|${f.stage}|${f.local}|${state.page.currentSlug || ''}|${canvas.clientWidth}x${canvas.clientHeight}`;
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
  } catch { return null; }
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
  } catch {}
}

function isMobile() {
  return window.matchMedia('(max-width: 720px)').matches;
}

function tagColor(tag) {
  return TAG_PALETTE[tag] || 'var(--color-ink-fade)';
}

function nodeRadius(degree) {
  return Math.min(16, Math.max(5, 5 + degree * 1.5));
}

function parseData() {
  const tag = document.getElementById('garden-graph-data');
  if (!tag) return null;
  try { return JSON.parse(tag.textContent); } catch { return null; }
}

function bfsNeighborhood(focus, hops, edges) {
  const adj = new Map();
  for (const e of edges) {
    if (!adj.has(e.source)) adj.set(e.source, new Set());
    if (!adj.has(e.target)) adj.set(e.target, new Set());
    adj.get(e.source).add(e.target);
    adj.get(e.target).add(e.source);
  }
  const visited = new Set([focus]);
  let frontier = new Set([focus]);
  for (let i = 0; i < hops; i++) {
    const next = new Set();
    frontier.forEach(s => {
      (adj.get(s) || new Set()).forEach(t => {
        if (!visited.has(t)) { next.add(t); visited.add(t); }
      });
    });
    frontier = next;
  }
  return visited;
}

function applyFilters() {
  if (!state.data) return { nodes: [], edges: [] };
  const f = state.filters;
  let nodes = state.data.nodes;
  if (f.tag !== 'all') nodes = nodes.filter(n => n.tag === f.tag);
  if (f.stage !== 'all') nodes = nodes.filter(n => n.stage === f.stage);
  if (state.page.isNotePage && f.local !== 'all') {
    const hops = f.local === '1-hop' ? 1 : 2;
    const allowed = bfsNeighborhood(state.page.currentSlug, hops, state.data.edges);
    nodes = nodes.filter(n => allowed.has(n.slug));
  }
  const allowed = new Set(nodes.map(n => n.slug));
  const edges = state.data.edges.filter(e => allowed.has(e.source) && allowed.has(e.target));
  return { nodes: nodes.map(n => ({ ...n })), edges: edges.map(e => ({ ...e })) };
}

async function buildSimulation(canvas) {
  const { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } =
    await import('./vendor/d3-force.min.js');

  const { nodes, edges } = applyFilters();
  const w = canvas.clientWidth || 320;
  const h = canvas.clientHeight || 360;

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', `Force-directed graph of ${nodes.length} note(s)`);
  const desc = document.createElementNS(SVG_NS, 'desc');
  desc.textContent = `Garden graph with ${nodes.length} nodes and ${edges.length} edges. Click a node to open it in a stack.`;
  svg.appendChild(desc);

  const contentGroup = document.createElementNS(SVG_NS, 'g');
  contentGroup.setAttribute('class', 'graph-content');
  svg.appendChild(contentGroup);

  const edgeLayer = document.createElementNS(SVG_NS, 'g');
  edgeLayer.setAttribute('class', 'garden-graph-edges');
  contentGroup.appendChild(edgeLayer);
  const nodeLayer = document.createElementNS(SVG_NS, 'g');
  nodeLayer.setAttribute('class', 'garden-graph-nodes');
  contentGroup.appendChild(nodeLayer);

  // Build edge elements
  const edgeEls = edges.map(e => {
    const line = document.createElementNS(SVG_NS, 'line');
    line.setAttribute('class', 'garden-graph-edge' + (e.crossTopic ? ' cross-topic' : ''));
    edgeLayer.appendChild(line);
    return { e, line };
  });

  // Build node elements (each is a <g> with circle + text)
  const nodeEls = nodes.map(n => {
    const g = document.createElementNS(SVG_NS, 'g');
    g.setAttribute('class', 'garden-graph-node' + (state.inStack.has(n.slug) ? ' in-stack' : ''));
    g.setAttribute('tabindex', '0');
    g.setAttribute('role', 'link');
    g.setAttribute('aria-label', `Open ${n.title} in stack`);
    g.dataset.slug = n.slug;

    const c = document.createElementNS(SVG_NS, 'circle');
    c.setAttribute('r', String(nodeRadius(n.degree)));
    c.setAttribute('fill', tagColor(n.tag));
    g.appendChild(c);

    const t = document.createElementNS(SVG_NS, 'text');
    t.textContent = n.title;
    t.setAttribute('x', String(nodeRadius(n.degree) + 3));
    t.setAttribute('y', '3');
    g.appendChild(t);

    g.addEventListener('click', () => { window.location.assign(`/garden/${n.slug}/`); });
    g.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        window.location.assign(`/garden/${n.slug}/`);
      }
    });

    nodeLayer.appendChild(g);
    return { n, g };
  });

  canvas.replaceChildren(svg);

  // Restore cached positions if all current nodes have a cache entry.
  // Hit → skip the simulation entirely (instant, byte-stable layout).
  // Miss or partial → run a fresh settle and save the result.
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
  let canvas;
  const isGraphPage = !!document.querySelector('.garden-graph-page');
  if (isGraphPage) {
    canvas = document.querySelector('.garden-graph-page .garden-graph-canvas');
  } else if (state.panel) {
    canvas = state.panel.querySelector('.garden-graph-panel-canvas');
  }
  if (!canvas) return;
  if (state.simulation) state.simulation.stop();
  buildSimulation(canvas).then(({ svg, simulation, contentGroup }) => {
    state.svg = svg;
    state.simulation = simulation;
    state.contentGroup = contentGroup;
  });
}

function updateInStackMarkers() {
  if (!state.svg) return;
  state.svg.querySelectorAll('.garden-graph-node').forEach(g => {
    const slug = g.dataset.slug;
    g.classList.toggle('in-stack', state.inStack.has(slug));
  });
}

function buildToolbar(host) {
  if (!state.data) return;
  const tags = new Set();
  const stages = new Set();
  state.data.nodes.forEach(n => { if (n.tag) tags.add(n.tag); stages.add(n.stage); });

  const mkChip = (label, dim, value) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'chip';
    b.dataset.dim = dim;
    b.dataset.value = value;
    b.setAttribute('aria-pressed', state.filters[dim] === value ? 'true' : 'false');
    b.textContent = label;
    b.addEventListener('click', () => {
      state.filters[dim] = value;
      host.querySelectorAll(`button[data-dim="${dim}"]`).forEach(c => {
        c.setAttribute('aria-pressed', c.dataset.value === value ? 'true' : 'false');
      });
      rebuildGraph();
    });
    return b;
  };

  host.replaceChildren();

  // Tag dim
  const tagLabel = document.createElement('span'); tagLabel.className = 'label'; tagLabel.textContent = 'Tag:';
  host.append(tagLabel, mkChip('All', 'tag', 'all'));
  Array.from(tags).sort().forEach(t => host.appendChild(mkChip(t, 'tag', t)));

  // Stage dim
  const stageLabel = document.createElement('span'); stageLabel.className = 'label'; stageLabel.textContent = 'Stage:';
  host.append(stageLabel, mkChip('All', 'stage', 'all'));
  ['seedling', 'budding', 'evergreen'].filter(s => stages.has(s)).forEach(s => host.appendChild(mkChip(s, 'stage', s)));

  // Local dim — note pages only
  if (state.page.isNotePage) {
    const localLabel = document.createElement('span'); localLabel.className = 'label'; localLabel.textContent = 'Scope:';
    host.append(localLabel, mkChip('All', 'local', 'all'), mkChip('1-hop', 'local', '1-hop'), mkChip('2-hop', 'local', '2-hop'));
  }
}

function buildLegend(host) {
  host.replaceChildren();
  const tags = new Map();
  (state.data.nodes || []).forEach(n => { if (n.tag) tags.set(n.tag, true); });
  Array.from(tags.keys()).slice(0, 4).forEach(tag => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="swatch" style="background:${tagColor(tag)}"></span>${tag}`;
    host.appendChild(li);
  });
  const note = document.createElement('li');
  note.textContent = 'size = link count · solid = same topic · dashed = cross-topic';
  host.appendChild(note);
}

function openPanel({ animate = true } = {}) {
  if (!state.panel) return;
  if (isMobile()) {
    window.location.assign('/garden/graph/');
    return;
  }
  // Adding `.is-animating` enables the CSS transition for the slide. We add
  // it only on user-initiated toggles, not on the silent restore-from-storage
  // path — so navigating between notes never re-animates a panel that was
  // already open.
  if (animate) state.panel.classList.add('is-animating');
  state.panel.setAttribute('aria-hidden', 'false');
  state.panelOpen = true;
  try { sessionStorage.setItem(PANEL_KEY, '1'); } catch {}
  document.querySelectorAll('.garden-graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'true'));

  const toolbar = state.panel.querySelector('.garden-graph-panel-toolbar');
  const legend = state.panel.querySelector('.garden-graph-panel-legend');
  if (toolbar && !toolbar.children.length) buildToolbar(toolbar);
  if (legend && !legend.children.length) buildLegend(legend);
  rebuildGraph();
}

function closePanel() {
  if (!state.panel) return;
  // Close is always user-initiated (button click or Esc) — always animate.
  state.panel.classList.add('is-animating');
  state.panel.setAttribute('aria-hidden', 'true');
  state.panelOpen = false;
  try { sessionStorage.removeItem(PANEL_KEY); } catch {}
  document.querySelectorAll('.garden-graph-toggle').forEach(b => b.setAttribute('aria-expanded', 'false'));
  const toggle = document.querySelector('.garden-graph-toggle');
  if (toggle) toggle.focus();
}

function init() {
  state.data = parseData();
  if (!state.data) return;
  state.panel = document.getElementById('garden-graph-panel');
  state.page.isMobile = isMobile();
  const stackRoot = document.querySelector('.garden-stack-columns .garden-column');
  state.page.isNotePage = !!stackRoot;
  state.page.currentSlug = stackRoot ? stackRoot.dataset.slug : null;

  // Initial in-stack set
  document.querySelectorAll('.garden-stack-columns .garden-column').forEach(c => {
    state.inStack.add(c.dataset.slug);
  });

  const isGraphPage = !!document.querySelector('.garden-graph-page');

  if (isGraphPage) {
    // Standalone /garden/graph/ — render immediately; no panel.
    const toolbar = document.querySelector('.garden-graph-page .garden-graph-toolbar');
    const legend = document.querySelector('.garden-graph-page .garden-graph-legend');
    if (toolbar) buildToolbar(toolbar);
    if (legend) buildLegend(legend);
    rebuildGraph();
    return;
  }

  // Toggle button(s)
  document.querySelectorAll('.garden-graph-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      if (state.panelOpen) closePanel(); else openPanel();
    });
  });

  // Close button inside panel
  if (state.panel) {
    const close = state.panel.querySelector('.garden-graph-panel-close');
    if (close) close.addEventListener('click', closePanel);
  }

  // Esc when panel focused
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!state.panelOpen) return;
    // Panel claims Esc UNLESS the user's last pointer-down was in the stack
    // (they're reading a column — let Esc clear the stack instead).
    // stopImmediatePropagation prevents garden-stack's keydown handler from
    // also firing — necessary because both listeners attach to `document` and
    // would otherwise both run on the same event.
    if (state.lastPointerInStack) return;
    e.stopImmediatePropagation();
    closePanel();
  });

  // Track whether the user's last pointer interaction was inside the stack
  // columns. Capture phase so this fires before any click handlers can
  // consume the event.
  document.addEventListener('pointerdown', (e) => {
    const stack = document.querySelector('.garden-stack');
    state.lastPointerInStack = stack ? stack.contains(e.target) : false;
  }, true);

  // Listen for stack changes
  window.addEventListener('garden:stack-changed', (e) => {
    state.inStack = new Set(e.detail.slugs);
    updateInStackMarkers();
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
