// Works constellation adapter over graph-core.js. Keeps only works-specific
// surface: the badge + glyph node shape, the medium filter, and the badge
// gradient <defs>. Shared infra lives in graph-core. Normalized in R5.2 to the
// garden/research conventions (JS-built toolbar, inert panel, <div> canvas).
// Spec: docs/superpowers/specs/2026-05-12-works-umbrella-polish-design.md §3.4.

import { createGraph, makeFilterChip, buildActionChips } from './graph-core.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

// Featured nodes get a larger badge + glyph; the spec §3.4 fixes these sizes.
const BADGE_REGULAR = 36;
const BADGE_FEATURED = 48;
const GLYPH_REGULAR = 20;
const GLYPH_FEATURED = 28;
function badgeSize(featured) { return featured ? BADGE_FEATURED : BADGE_REGULAR; }
function glyphSize(featured) { return featured ? GLYPH_FEATURED : GLYPH_REGULAR; }
// Collide radius — half the badge plus a generous gap (the gap is what visibly
// pushes nodes apart).
function nodeRadius(featured) { return badgeSize(featured) / 2 + 38; }

const MEDIUM_LABELS = { game: 'Games', music: 'Music', poetry: 'Poetry' };
const MEDIUM_ORDER = ['game', 'music', 'poetry'];

// Works-only runtime state. Core owns simulation/svg/view/cache/panel.
const wk = {
  data: null,
  filters: { medium: 'all' },
  page: { currentSlug: null },
};

let controller = null;

const adapter = {
  classPrefix: 'works',
  pageSelector: '.works-graph-page .works-graph-canvas',
  panelId: 'works-graph-panel',
  graphPageUrl: '/works/graph/',

  parseData() {
    const el = document.getElementById('works-graph-data');
    if (!el) return false;
    try {
      const raw = JSON.parse(el.textContent);
      const nodes = (raw.nodes || []).map(n => ({
        slug: n.slug, title: n.title, url: n.url, medium: n.medium,
        tags: n.tags || [], featured: !!n.featured, year: n.year || 0,
      }));
      const edges = (raw.edges || []).map(e => ({
        source: e.source, target: e.target, kind: e.kind || 'tag-share',
        via: e.via || null, shared: e.shared || null, weight: e.weight || 1,
      }));
      wk.data = { nodes, edges };
    } catch { return false; }
    return !!wk.data;
  },

  applyFilters() {
    if (!wk.data) return { nodes: [], edges: [] };
    const f = wk.filters;
    let nodes = wk.data.nodes;
    if (f.medium !== 'all') nodes = nodes.filter(n => n.medium === f.medium);
    const allowed = new Set(nodes.map(n => n.slug));
    const edges = wk.data.edges.filter(e => allowed.has(e.source) && allowed.has(e.target));
    return { nodes: nodes.map(n => ({ ...n })), edges: edges.map(e => ({ ...e })) };
  },

  filterCacheKey() { return `${wk.filters.medium}`; },

  nodeRadius(n) { return nodeRadius(n.featured); },

  renderNode(el, n) {
    // Every node is a rounded-rect badge + inline glyph <use> + centered label.
    if (n.featured) el.classList.add('works-graph-node-featured');
    if (wk.page.currentSlug && n.slug === wk.page.currentSlug) el.classList.add('is-here');
    el.setAttribute('data-medium', n.medium);
    el.setAttribute('data-featured', n.featured ? 'true' : 'false');
    el.setAttribute('role', 'link');
    el.setAttribute('aria-label', n.title);
    el.dataset.url = n.url;

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
    el.appendChild(rect);

    const gsize = glyphSize(n.featured);
    const ghalf = gsize / 2;
    const use = document.createElementNS(SVG_NS, 'use');
    use.setAttribute('class', 'works-graph-node-glyph');
    use.setAttribute('href', `#g-${n.medium}`);
    use.setAttribute('x', String(-ghalf));
    use.setAttribute('y', String(-ghalf));
    use.setAttribute('width', String(gsize));
    use.setAttribute('height', String(gsize));
    el.appendChild(use);

    const t = document.createElementNS(SVG_NS, 'text');
    t.setAttribute('class', 'works-graph-node-label');
    t.setAttribute('text-anchor', 'middle');
    t.setAttribute('x', '0');
    t.setAttribute('y', String(half + 14));
    t.textContent = n.title;
    el.appendChild(t);
  },

  edgeClass(e) {
    return e.kind === 'cross-ref'
      ? 'works-graph-edge works-graph-edge-cross-ref'
      : 'works-graph-edge works-graph-edge-tag-share';
  },

  svgAria({ nodeCount, edgeCount }) {
    return {
      label: `Force-directed works constellation of ${nodeCount} node(s)`,
      desc: `Works constellation with ${nodeCount} nodes and ${edgeCount} edges. Click a node to navigate to its page.`,
    };
  },

  forceParams: {
    linkDistance: 160,
    linkStrength: 0.35,
    chargeStrength: -700,
    collideRadius: (n) => nodeRadius(n.featured),
  },

  onNodeClick(n, el) {
    const url = el.dataset.url;
    if (url) window.location.assign(url);
  },

  onSvgCreate(svg) {
    // Badge gradient <defs> — referenced by CSS §36
    // .works-graph-node-badge { fill: url(#works-graph-badge-gradient); }.
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
  },

  buildToolbar(host, ctrl) {
    if (!wk.data) return;
    host.replaceChildren();
    const present = new Set(wk.data.nodes.map(n => n.medium));
    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = 'Medium';
    host.append(label, makeFilterChip(host, 'All', 'medium', 'all', wk.filters, ctrl.rebuild));
    MEDIUM_ORDER
      .filter(m => present.has(m))
      .forEach(m => host.appendChild(
        makeFilterChip(host, MEDIUM_LABELS[m], 'medium', m, wk.filters, ctrl.rebuild)));
    buildActionChips(host, ctrl);
  },
};

function init() {
  if (!adapter.parseData()) return;

  const hereBar = document.querySelector('.graph-launcher-bar[data-graph-current]');
  wk.page.currentSlug = hereBar ? hereBar.dataset.graphCurrent : null;

  controller = createGraph(adapter);

  const isGraphPage = !!document.querySelector('.works-graph-page');
  if (isGraphPage) {
    const toolbar = document.querySelector('.works-graph-page .graph-toolbar');
    if (toolbar) adapter.buildToolbar(toolbar, controller);
    controller.rebuild();
    return;
  }

  const panel = document.getElementById('works-graph-panel');
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

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!controller.isPanelOpen()) return;
    e.stopImmediatePropagation();
    controller.closePanel();
  });

  let restore = false;
  try { restore = sessionStorage.getItem('works-graph-open') === '1'; } catch {}
  if (restore && !controller.isMobile()) controller.openPanel({ animate: false });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
