// Research graph adapter over graph-core.js. Keeps only research-specific
// surface: theme/question node shapes, the multi-select tag filter, and
// kind-based navigation. Shared infra lives in graph-core.
// Spec: docs/superpowers/specs/2026-05-11-research-graph-design.md §5.6.

import { createGraph, makeFilterChip, buildActionChips } from './graph-core.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

const NODE_R_MIN = 5;
const NODE_R_MAX = 16;
const NODE_R_PER_DEGREE = 1.5;
function nodeRadius(degree) {
  return Math.min(NODE_R_MAX, Math.max(NODE_R_MIN, NODE_R_MIN + degree * NODE_R_PER_DEGREE));
}

// Research-only runtime state. Core owns simulation/svg/view/cache/panel.
const r = {
  data: null,
  filters: { tag: 'all', status: 'all' },
  page: { currentSlug: null },
};

let controller = null;

// Tag dim is multi-select (stored as comma-joined 'tag1,tag2' or 'all').
function tagActive(value) {
  if (value === 'all') return r.filters.tag === 'all' || r.filters.tag === '';
  return r.filters.tag.split(',').filter(Boolean).includes(value);
}

// Multi-select tag chip (core's makeFilterChip is single-select, so tags are
// hand-rolled here; status + actions reuse the core primitives).
function makeTagChip(host, label, value, ctrl) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'graph-chip';
  b.dataset.dim = 'tag';
  b.dataset.value = value;
  b.setAttribute('aria-pressed', tagActive(value) ? 'true' : 'false');
  b.textContent = label;
  b.addEventListener('click', () => {
    if (value === 'all') {
      r.filters.tag = 'all';
    } else {
      const current = r.filters.tag === 'all' ? [] : r.filters.tag.split(',').filter(Boolean);
      const idx = current.indexOf(value);
      if (idx >= 0) current.splice(idx, 1); else current.push(value);
      r.filters.tag = current.length ? current.join(',') : 'all';
    }
    host.querySelectorAll('button[data-dim="tag"]').forEach(c => {
      c.setAttribute('aria-pressed', tagActive(c.dataset.value) ? 'true' : 'false');
    });
    ctrl.rebuild();
  });
  return b;
}

const adapter = {
  classPrefix: 'research',
  pageSelector: '.research-graph-page .research-graph-canvas',
  panelId: 'research-graph-panel',
  graphPageUrl: '/research/graph/',

  parseData() {
    const el = document.getElementById('research-graph-data');
    if (!el) return false;
    try {
      const raw = JSON.parse(el.textContent);
      // Deterministic palette index from themePaletteOrder (sorted by weight).
      const paletteOrder = raw.themePaletteOrder || [];
      const paletteIndex = (slug) => {
        const idx = paletteOrder.indexOf(slug);
        return idx >= 0 ? idx : 0;
      };
      const nodes = [
        ...(raw.themes || []).map(t => ({
          slug: t.slug, title: t.title, kind: 'theme', status: t.status,
          tags: t.tags || [], themeColorIdx: paletteIndex(t.slug), degree: t.degree || 0,
        })),
        ...(raw.questions || []).map(q => ({
          slug: q.slug, title: q.title, kind: 'question', theme: q.theme, status: q.status,
          tags: q.tags || [], themeColorIdx: paletteIndex(q.theme), degree: q.degree || 0,
        })),
      ];
      const edges = (raw.edges || []).map(e => ({
        source: e.source, target: e.target, kind: e.kind || 'parent-child', via: e.via || null,
      }));
      r.data = { nodes, edges };
    } catch { return false; }
    return !!r.data;
  },

  applyFilters() {
    if (!r.data) return { nodes: [], edges: [] };
    const f = r.filters;
    let nodes = r.data.nodes;
    if (f.tag !== 'all') {
      const tags = f.tag.split(',').filter(Boolean);
      nodes = nodes.filter(n => tags.every(t => (n.tags || []).includes(t)));
    }
    // Status is single-select and applies to questions only (themes always show).
    if (f.status !== 'all') {
      nodes = nodes.filter(n => n.kind === 'theme' || n.status === f.status);
    }
    const allowed = new Set(nodes.map(n => n.slug));
    const edges = r.data.edges.filter(e => allowed.has(e.source) && allowed.has(e.target));
    return { nodes: nodes.map(n => ({ ...n })), edges: edges.map(e => ({ ...e })) };
  },

  filterCacheKey() {
    return `${r.filters.tag}|${r.filters.status}`;
  },

  nodeRadius(n) { return nodeRadius(n.degree); },

  renderNode(el, n) {
    // Themes render as squares (<rect>), questions as circles. data-theme-color
    // drives fill via CSS §31; is-here marks the current hub page's node.
    el.classList.add(`research-graph-node-${n.kind}`);
    if (r.page.currentSlug && n.slug === r.page.currentSlug) el.classList.add('is-here');
    el.setAttribute('data-theme-color', String(n.themeColorIdx));
    el.setAttribute('data-status', n.status || '');
    el.setAttribute('role', 'link');
    el.setAttribute('aria-label', n.title);
    const rad = nodeRadius(n.degree);
    if (n.kind === 'theme') {
      const rect = document.createElementNS(SVG_NS, 'rect');
      rect.setAttribute('width', String(rad * 1.6));
      rect.setAttribute('height', String(rad * 1.6));
      rect.setAttribute('x', String(-rad * 0.8));
      rect.setAttribute('y', String(-rad * 0.8));
      el.appendChild(rect);
    } else {
      const c = document.createElementNS(SVG_NS, 'circle');
      c.setAttribute('r', String(rad));
      el.appendChild(c);
    }
    const t = document.createElementNS(SVG_NS, 'text');
    t.textContent = n.title;
    t.setAttribute('x', String(rad + 3));
    t.setAttribute('y', '3');
    el.appendChild(t);
  },

  edgeClass(e) {
    return e.kind === 'cross-theme'
      ? 'research-graph-edge research-graph-edge-cross-theme'
      : 'research-graph-edge';
  },

  svgAria({ nodeCount, edgeCount }) {
    return {
      label: `Force-directed research graph of ${nodeCount} node(s)`,
      desc: `Research graph with ${nodeCount} nodes and ${edgeCount} edges. Click a node to navigate to its hub page.`,
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
    const url = n && n.kind === 'theme'
      ? `/research/themes/${slug}/`
      : `/research/questions/${slug}/`;
    window.location.assign(url);
  },

  buildToolbar(host, ctrl) {
    if (!r.data) return;
    host.replaceChildren();
    const tags = new Set();
    const statuses = new Set();
    r.data.nodes.forEach(n => {
      (n.tags || []).forEach(t => tags.add(t));
      if (n.status) statuses.add(n.status);
    });

    const tagLabel = document.createElement('span');
    tagLabel.className = 'label';
    tagLabel.textContent = 'Tag:';
    host.append(tagLabel, makeTagChip(host, 'All', 'all', ctrl));
    Array.from(tags).sort().forEach(t => host.appendChild(makeTagChip(host, t, t, ctrl)));

    const statusLabel = document.createElement('span');
    statusLabel.className = 'label';
    statusLabel.textContent = 'Status:';
    host.append(statusLabel, makeFilterChip(host, 'All', 'status', 'all', r.filters, ctrl.rebuild));
    ['active', 'dormant', 'answered']
      .filter(s => statuses.has(s))
      .forEach(s => host.appendChild(makeFilterChip(host, s, 'status', s, r.filters, ctrl.rebuild)));

    buildActionChips(host, ctrl);
  },
};

function init() {
  if (!adapter.parseData()) return;

  const hereBar = document.querySelector('.graph-launcher-bar[data-graph-current]');
  r.page.currentSlug = hereBar ? hereBar.dataset.graphCurrent : null;

  controller = createGraph(adapter);

  const isGraphPage = !!document.querySelector('.research-graph-page');
  if (isGraphPage) {
    const toolbar = document.querySelector('.research-graph-page .graph-toolbar');
    if (toolbar) adapter.buildToolbar(toolbar, controller);
    controller.rebuild();
    return;
  }

  const panel = document.getElementById('research-graph-panel');
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
  try { restore = sessionStorage.getItem('research-graph-open') === '1'; } catch {}
  if (restore && !controller.isMobile()) controller.openPanel({ animate: false });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
