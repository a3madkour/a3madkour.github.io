// Garden graph adapter over graph-core.js. Keeps only garden-specific surface:
// the tag palette, N-hop local mode, stack-coordination, and the dynamic
// legend. Shared force/render/cache/zoom/drag/panel logic lives in graph-core.
// Spec: docs/superpowers/specs/2026-05-08-garden-interactions-design.md §6.

import { createGraph, makeFilterChip, buildActionChips } from './graph-core.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

// Hand-curated map from known tags to existing site palette tokens. Multiple
// tags may intentionally share a token (reading + calvino ride --color-warn;
// games + play ride --color-steel) — semantically adjacent, and expanding the
// palette to disambiguate hurts legibility more than it helps. Unmapped tags
// fall through to --color-ink-fade by design ("no curated color yet", not a
// bug). To add a mapping, pick an existing :root token.
const TAG_PALETTE = {
  'narrative': 'var(--color-burgundy)',
  'memory':    'var(--color-green)',
  'games':     'var(--color-steel)',
  'reading':   'var(--color-warn)',
  'calvino':   'var(--color-warn)',
  'play':      'var(--color-steel)',
  'aesthetics':'var(--color-ink-soft)',
};

function tagColor(tag) {
  return TAG_PALETTE[tag] || 'var(--color-ink-fade)';
}

// Node radius backs the legend's "size = link count": r = MIN + degree×PER,
// clamped to MAX.
const NODE_R_MIN = 5;
const NODE_R_MAX = 16;
const NODE_R_PER_DEGREE = 1.5;
function nodeRadius(degree) {
  return Math.min(NODE_R_MAX, Math.max(NODE_R_MIN, NODE_R_MIN + degree * NODE_R_PER_DEGREE));
}

// Garden-only runtime state (data + filters + page + stack context). Core owns
// simulation/svg/view/cache/panel state.
const g = {
  data: null,
  filters: { tag: 'all', stage: 'all', local: 'all' /* all | 1-hop | 2-hop */ },
  inStack: new Set(),
  page: { isNotePage: false, currentSlug: null },
  // Was the user's last pointer-down inside the stack columns? Disambiguates
  // Esc: attention-on-stack → Esc clears the stack; else the panel claims it.
  lastPointerInStack: false,
};

let controller = null;

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

function buildLegend(root) {
  // The structure key (size / solid / dashed) is server-rendered by
  // partials/graph-legend.html. Garden's tag palette is content-dependent, so
  // we inject swatches into the partial's dynamic color-key slot only.
  const slot = root.querySelector('.graph-legend-colorkey[data-graph-legend-dynamic]');
  if (!slot) return;
  slot.replaceChildren();
  const tags = new Map();
  (g.data.nodes || []).forEach(n => { if (n.tag) tags.set(n.tag, true); });
  Array.from(tags.keys()).slice(0, 4).forEach(tag => {
    const key = document.createElement('span');
    key.className = 'graph-legend-key';
    key.innerHTML = `<span class="graph-legend-swatch" style="background:${tagColor(tag)}"></span>${tag}`;
    slot.appendChild(key);
  });
}

function updateInStackMarkers() {
  const svg = controller && controller.getSvg();
  if (!svg) return;
  svg.querySelectorAll('.garden-graph-node').forEach(node => {
    node.classList.toggle('in-stack', g.inStack.has(node.dataset.slug));
  });
}

const adapter = {
  classPrefix: 'garden',
  pageSelector: '.garden-graph-page .garden-graph-canvas',
  panelId: 'garden-graph-panel',
  graphPageUrl: '/garden/graph/',

  parseData() {
    const tag = document.getElementById('garden-graph-data');
    if (!tag) return false;
    try { g.data = JSON.parse(tag.textContent); } catch { return false; }
    return !!g.data;
  },

  applyFilters() {
    if (!g.data) return { nodes: [], edges: [] };
    const f = g.filters;
    let nodes = g.data.nodes;
    if (f.tag !== 'all') nodes = nodes.filter(n => n.tag === f.tag);
    if (f.stage !== 'all') nodes = nodes.filter(n => n.stage === f.stage);
    if (g.page.isNotePage && f.local !== 'all') {
      const hops = f.local === '1-hop' ? 1 : 2;
      const allowed = bfsNeighborhood(g.page.currentSlug, hops, g.data.edges);
      nodes = nodes.filter(n => allowed.has(n.slug));
    }
    const allowed = new Set(nodes.map(n => n.slug));
    const edges = g.data.edges.filter(e => allowed.has(e.source) && allowed.has(e.target));
    return { nodes: nodes.map(n => ({ ...n })), edges: edges.map(e => ({ ...e })) };
  },

  filterCacheKey() {
    const f = g.filters;
    const focus = f.local === 'all' ? '' : (g.page.currentSlug || '');
    return `${f.tag}|${f.stage}|${f.local}|${focus}`;
  },

  nodeRadius(n) { return nodeRadius(n.degree); },

  renderNode(el, n) {
    if (g.inStack.has(n.slug)) el.classList.add('in-stack');
    el.setAttribute('role', 'link');
    el.setAttribute('aria-label', `Open ${n.title} in stack`);
    const c = document.createElementNS(SVG_NS, 'circle');
    c.setAttribute('r', String(nodeRadius(n.degree)));
    c.setAttribute('fill', tagColor(n.tag));
    el.appendChild(c);
    const t = document.createElementNS(SVG_NS, 'text');
    t.textContent = n.title;
    t.setAttribute('x', String(nodeRadius(n.degree) + 3));
    t.setAttribute('y', '3');
    el.appendChild(t);
  },

  edgeClass(e) {
    return 'garden-graph-edge' + (e.crossTopic ? ' cross-topic' : '');
  },

  svgAria({ nodeCount, edgeCount }) {
    return {
      label: `Force-directed graph of ${nodeCount} note(s)`,
      desc: `Garden graph with ${nodeCount} nodes and ${edgeCount} edges. Click a node to open it in a stack.`,
    };
  },

  forceParams: {
    linkDistance: 60,
    linkStrength: 0.6,
    chargeStrength: -180,
    collideRadius: (n) => nodeRadius(n.degree) + 4,
  },

  onNodeClick(n, el) {
    const slug = el.dataset.slug;
    // With a stack root on the page, append/refocus a column rather than a hard
    // navigation. On the standalone /garden/graph/ page there's no stack.
    if (document.querySelector('.garden-stack')) {
      window.dispatchEvent(new CustomEvent('garden:graph-navigate', { detail: { slug } }));
    } else {
      window.location.assign(`/garden/${slug}/`);
    }
  },

  buildToolbar(host, ctrl) {
    if (!g.data) return;
    host.replaceChildren();
    const tags = new Set();
    const stages = new Set();
    g.data.nodes.forEach(n => { if (n.tag) tags.add(n.tag); stages.add(n.stage); });

    const tagLabel = document.createElement('span');
    tagLabel.className = 'label';
    tagLabel.textContent = 'Tag:';
    host.append(tagLabel, makeFilterChip(host, 'All', 'tag', 'all', g.filters, ctrl.rebuild));
    Array.from(tags).sort().forEach(t =>
      host.appendChild(makeFilterChip(host, t, 'tag', t, g.filters, ctrl.rebuild)));

    const stageLabel = document.createElement('span');
    stageLabel.className = 'label';
    stageLabel.textContent = 'Stage:';
    host.append(stageLabel, makeFilterChip(host, 'All', 'stage', 'all', g.filters, ctrl.rebuild));
    ['seedling', 'budding', 'evergreen']
      .filter(s => stages.has(s))
      .forEach(s => host.appendChild(makeFilterChip(host, s, 'stage', s, g.filters, ctrl.rebuild)));

    if (g.page.isNotePage) {
      const localLabel = document.createElement('span');
      localLabel.className = 'label';
      localLabel.textContent = 'Scope:';
      host.append(
        localLabel,
        makeFilterChip(host, 'All', 'local', 'all', g.filters, ctrl.rebuild),
        makeFilterChip(host, '1-hop', 'local', '1-hop', g.filters, ctrl.rebuild),
        makeFilterChip(host, '2-hop', 'local', '2-hop', g.filters, ctrl.rebuild),
      );
    }
    buildActionChips(host, ctrl);
  },

  onOpenPanel(panel) {
    const legend = panel.querySelector('.graph-legend');
    if (legend) buildLegend(legend);
  },
};

function init() {
  if (!adapter.parseData()) return;

  const stackRoot = document.querySelector('.garden-stack-columns .garden-column');
  g.page.isNotePage = !!stackRoot;
  g.page.currentSlug = stackRoot ? stackRoot.dataset.slug : null;
  document.querySelectorAll('.garden-stack-columns .garden-column').forEach(c => {
    g.inStack.add(c.dataset.slug);
  });

  controller = createGraph(adapter);

  const isGraphPage = !!document.querySelector('.garden-graph-page');
  if (isGraphPage) {
    // Standalone /garden/graph/ — render immediately; no panel.
    const toolbar = document.querySelector('.garden-graph-page .graph-toolbar');
    const legend = document.querySelector('.garden-graph-page .graph-legend');
    if (toolbar) adapter.buildToolbar(toolbar, controller);
    if (legend) buildLegend(legend);
    controller.rebuild();
    return;
  }

  const panel = document.getElementById('garden-graph-panel');

  // Persisted width + resize handle (desktop only; panel hidden < 720px in CSS).
  if (panel && !controller.isMobile()) {
    controller.applySavedPanelWidth();
    controller.setupPanelResize();
  }

  document.querySelectorAll('.graph-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      if (controller.isPanelOpen()) controller.closePanel();
      else controller.openPanel();
    });
  });

  if (panel) {
    const close = panel.querySelector('.graph-panel-close');
    if (close) close.addEventListener('click', () => controller.closePanel());
  }

  // Esc closes the panel unless the user's attention is on the stack.
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!controller.isPanelOpen()) return;
    if (g.lastPointerInStack) return;
    e.stopImmediatePropagation();
    controller.closePanel();
  });

  // Track whether the last pointer-down was inside the stack (capture phase, so
  // it runs before click handlers consume the event).
  document.addEventListener('pointerdown', (e) => {
    const stack = document.querySelector('.garden-stack');
    g.lastPointerInStack = stack ? stack.contains(e.target) : false;
  }, true);

  window.addEventListener('garden:stack-changed', (e) => {
    g.inStack = new Set(e.detail.slugs);
    updateInStackMarkers();
  });

  // Restore panel state
  let restore = false;
  try { restore = sessionStorage.getItem('garden-graph-open') === '1'; } catch {}
  if (restore && !controller.isMobile()) controller.openPanel({ animate: false });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
