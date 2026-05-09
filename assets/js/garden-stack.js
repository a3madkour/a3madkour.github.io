// Garden stacked-column runtime — eager Matuschak-style.
// Spec: docs/superpowers/specs/2026-05-08-garden-interactions-design.md §5.

const STACK_ROOT = '.garden-stack';
const COLUMNS = '.garden-stack-columns';
const COLUMN = '.garden-column';
const PATHLOG = '.garden-path-log';
const MOBILE_QUERY = '(max-width: 720px)';
const FETCH_OPTS = { credentials: 'same-origin' };

const CONSENT_KEY = 'path-log-consent';
const VISITED_KEY = 'garden-path-log';
const VISITED_CAP = 100;

const state = {
  slugs: [],
  consent: 'unset', // 'unset' | 'yes' | 'session' | 'no'
};

function isMobile() {
  return window.matchMedia(MOBILE_QUERY).matches;
}

function motionPref() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
}

function urlStackParam() {
  const p = new URL(window.location.href).searchParams.get('stack');
  return p ? p.split(',').map(s => s.trim()).filter(Boolean) : [];
}

function rootSlug() {
  const root = document.querySelector(`${COLUMNS} ${COLUMN}`);
  return root ? root.getAttribute('data-slug') : null;
}

function rewriteURL() {
  const url = new URL(window.location.href);
  if (state.slugs.length <= 1) {
    url.searchParams.delete('stack');
  } else {
    url.searchParams.set('stack', state.slugs.join(','));
  }
  history.replaceState(null, '', url.toString());
}

function dispatchStackChanged() {
  window.dispatchEvent(new CustomEvent('garden:stack-changed', {
    detail: { slugs: state.slugs.slice() },
  }));
}

function readConsent() {
  try {
    return localStorage.getItem(CONSENT_KEY) || 'unset';
  } catch { return 'unset'; }
}

function writeConsent(value) {
  try { localStorage.setItem(CONSENT_KEY, value); } catch {}
  state.consent = value;
}

function persistVisited(slug) {
  if (state.consent === 'unset' || state.consent === 'no') return;
  const store = state.consent === 'session' ? sessionStorage : localStorage;
  let list;
  try {
    list = JSON.parse(store.getItem(VISITED_KEY) || '[]');
  } catch { list = []; }
  list.push(slug);
  if (list.length > VISITED_CAP) list = list.slice(-VISITED_CAP);
  try { store.setItem(VISITED_KEY, JSON.stringify(list)); } catch {}
}

function showConsentBanner() {
  if (state.consent !== 'unset') return;
  const log = document.querySelector(PATHLOG);
  if (!log) return;
  if (document.querySelector('.garden-consent-banner')) return;

  const banner = document.createElement('aside');
  banner.className = 'garden-consent-banner';
  banner.setAttribute('role', 'dialog');
  banner.setAttribute('aria-label', 'Track reading path');
  banner.innerHTML = `
    <span>Track your reading path across visits?</span>
    <span class="opts">
      <button type="button" data-choice="yes">Yes, persist</button>
      <button type="button" data-choice="session">Just this session</button>
      <button type="button" data-choice="no">No, never</button>
    </span>
  `;
  log.parentNode.insertBefore(banner, log);

  banner.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-choice]');
    if (!btn) return;
    const choice = btn.dataset.choice;
    writeConsent(choice);
    if (choice !== 'no') {
      // Persist current stack retroactively.
      state.slugs.forEach(persistVisited);
    }
    banner.parentNode.removeChild(banner);
  });
}

function updatePathLog() {
  const log = document.querySelector(PATHLOG);
  if (!log) return;

  const label = log.querySelector('.path-log-label');
  const actions = log.querySelector('.path-log-actions');
  const gardenAnchor = log.querySelector('.path-log-crumb[href$="/garden/"]');

  // Clear everything between label and actions, except the static "Garden" anchor
  Array.from(log.children).forEach(child => {
    if (child !== label && child !== actions && child !== gardenAnchor) {
      log.removeChild(child);
    }
  });

  // Rebuild crumb chain: › <crumb>...
  state.slugs.forEach((slug, i) => {
    const sep = document.createElement('span');
    sep.className = 'path-log-sep';
    sep.setAttribute('aria-hidden', 'true');
    sep.textContent = '›';
    log.insertBefore(sep, actions);

    const a = document.createElement('a');
    a.className = 'path-log-crumb';
    a.href = `/garden/${slug}/`;
    a.dataset.slug = slug;
    if (i === state.slugs.length - 1) {
      a.classList.add('is-active');
      a.setAttribute('aria-current', 'page');
    }
    const col = document.querySelector(`${COLUMN}[data-slug="${CSS.escape(slug)}"]`);
    a.textContent = col ? col.querySelector('.garden-note-title').textContent.trim() : slug;
    log.insertBefore(a, actions);
  });

  const count = actions.querySelector('.path-log-count');
  const clear = actions.querySelector('.path-log-clear');
  if (count) {
    count.textContent = `${state.slugs.length} in stack`;
    count.dataset.stackCount = String(state.slugs.length);
  }
  if (clear) clear.hidden = state.slugs.length < 2;
}

async function fetchColumn(slug) {
  const res = await fetch(`/garden/${slug}/`, FETCH_OPTS);
  if (!res.ok) return null;
  const text = await res.text();
  const doc = new DOMParser().parseFromString(text, 'text/html');
  const col = doc.querySelector(`${COLUMN}[data-slug="${CSS.escape(slug)}"]`);
  return col ? col.cloneNode(true) : null;
}

function focusColumn(slug) {
  const col = document.querySelector(`${COLUMN}[data-slug="${CSS.escape(slug)}"]`);
  if (!col) return;
  document.querySelectorAll(`${COLUMN}.is-active`).forEach(c => c.classList.remove('is-active'));
  col.classList.add('is-active');
  col.scrollIntoView({ behavior: motionPref(), inline: 'start', block: 'nearest' });
  const heading = col.querySelector('.garden-note-title');
  if (heading) heading.focus();
}

async function appendColumn(slug) {
  if (state.slugs.includes(slug)) {
    focusColumn(slug);
    return;
  }
  const cols = document.querySelector(COLUMNS);
  if (!cols) return;
  const col = await fetchColumn(slug);
  if (!col) return;
  const wasOne = state.slugs.length === 1;
  cols.appendChild(col);
  state.slugs.push(slug);
  rewriteURL();
  focusColumn(slug);
  updatePathLog();
  dispatchStackChanged();
  persistVisited(slug);
  if (wasOne) showConsentBanner();
}

function clearStack() {
  if (state.slugs.length < 2) return;
  const cols = document.querySelector(COLUMNS);
  const root = state.slugs[0];
  Array.from(cols.querySelectorAll(COLUMN)).forEach(col => {
    if (col.getAttribute('data-slug') !== root) cols.removeChild(col);
  });
  state.slugs = [root];
  rewriteURL();
  focusColumn(root);
  updatePathLog();
  dispatchStackChanged();
}

function isInternalGardenLink(a) {
  if (!a || a.tagName !== 'A' || !a.href) return null;
  const u = new URL(a.href, window.location.href);
  if (u.origin !== window.location.origin) return null;
  const m = u.pathname.match(/^\/garden\/([a-z0-9][a-z0-9-]*)\/?$/);
  return m ? m[1] : null;
}

async function init() {
  const root = document.querySelector(STACK_ROOT);
  if (!root) return;

  const rs = rootSlug();
  if (!rs) return;

  state.consent = readConsent();

  // Mobile bypass: links navigate normally; no init.
  if (isMobile()) {
    state.slugs = [rs];
    return;
  }

  // Normalize: URL slug is column 0. ?stack= entries appended in order, deduped, URL slug skipped.
  const declared = urlStackParam();
  state.slugs = [rs];
  for (const s of declared) {
    if (s !== rs && !state.slugs.includes(s)) state.slugs.push(s);
  }

  // Fetch slugs 1..N in parallel; drop unresolved.
  const fetches = state.slugs.slice(1).map(s => fetchColumn(s).then(col => ({ slug: s, col })));
  const results = await Promise.all(fetches);
  const cols = document.querySelector(COLUMNS);
  const finalSlugs = [rs];
  for (const r of results) {
    if (r.col) {
      cols.appendChild(r.col);
      finalSlugs.push(r.slug);
    }
  }
  state.slugs = finalSlugs;

  rewriteURL();
  updatePathLog();
  if (state.slugs.length > 1) {
    focusColumn(state.slugs[state.slugs.length - 1]);
  }
  dispatchStackChanged();

  // Delegated click handler for internal /garden/ links inside any column
  root.addEventListener('click', (e) => {
    const a = e.target.closest('a');
    const slug = isInternalGardenLink(a);
    if (!slug) return;
    e.preventDefault();
    appendColumn(slug);
  });

  // Path-log clear button
  const clear = document.querySelector(`${PATHLOG} .path-log-clear`);
  if (clear) clear.addEventListener('click', clearStack);

  // Esc: clear stack if graph panel isn't focused
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (state.slugs.length < 2) return;
    const panel = document.getElementById('garden-graph-panel');
    if (panel && panel.contains(document.activeElement) && panel.getAttribute('aria-hidden') === 'false') {
      // Panel will handle Esc; do nothing.
      return;
    }
    clearStack();
  });

  // Path log: clicking a crumb refocuses (re-uses existing column, no fetch)
  const log = document.querySelector(PATHLOG);
  if (log) {
    log.addEventListener('click', (e) => {
      const a = e.target.closest('a.path-log-crumb');
      if (!a) return;
      const slug = a.dataset.slug;
      if (slug && state.slugs.includes(slug)) {
        e.preventDefault();
        focusColumn(slug);
      }
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
