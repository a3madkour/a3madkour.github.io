// Garden reading-history storage + render core.
// Reads/writes localStorage['garden-path-log'] (or sessionStorage if consent
// is 'session') in v2 envelope: {version: 2, sessions: [{root, slugs, at}]}.
// Migrates v1 (flat slug array) on first read.

const STORAGE_KEY = 'garden-path-log';
const CONSENT_KEY = 'path-log-consent';
const VERSION = 2;
const SESSION_CAP = 20;

function getStore() {
  let consent;
  try { consent = localStorage.getItem(CONSENT_KEY) || 'unset'; }
  catch { consent = 'unset'; }
  if (consent === 'session') return sessionStorage;
  return localStorage;
}

export function readHistory() {
  const store = getStore();
  let raw;
  try { raw = store.getItem(STORAGE_KEY); }
  catch { return []; }
  if (!raw) return [];

  let parsed;
  try { parsed = JSON.parse(raw); }
  catch { return []; }

  // v1 migration: flat array → wrap as one synthetic session.
  if (Array.isArray(parsed)) {
    const sessions = parsed.length === 0 ? [] : [{
      root: parsed[0] || '',
      slugs: parsed.slice(),
      at: 0,
    }];
    writeHistory(sessions);
    return sessions;
  }

  if (parsed && parsed.version === VERSION && Array.isArray(parsed.sessions)) {
    return parsed.sessions;
  }
  return [];
}

export function writeHistory(sessions) {
  const store = getStore();
  const capped = sessions.slice(0, SESSION_CAP);
  const envelope = { version: VERSION, sessions: capped };
  try { store.setItem(STORAGE_KEY, JSON.stringify(envelope)); }
  catch {}
}

export function dedupe(sessions) {
  // Sort newest-first, then keep only the first occurrence per slug-sequence.
  const sorted = sessions.slice().sort((a, b) => b.at - a.at);
  const seen = new Set();
  const out = [];
  for (const s of sorted) {
    const key = s.slugs.join('|');
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(s);
  }
  return out;
}

export function formatRelativeTime(ts) {
  if (!ts) return '';
  const diff = Date.now() - ts;
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  const days = Math.floor(diff / 86_400_000);
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days} days ago`;
  if (days < 14) return 'last week';
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
  return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function slugToLabel(slug) {
  return slug.replace(/-/g, ' ');
}

export function renderPath(session, options = {}) {
  const includeTime = options.includeTime !== false;
  const frag = document.createDocumentFragment();

  if (includeTime) {
    const time = document.createElement('span');
    time.className = 'path-time';
    time.textContent = formatRelativeTime(session.at);
    frag.appendChild(time);
  }

  session.slugs.forEach((slug, i) => {
    if (i > 0) {
      const arrow = document.createElement('span');
      arrow.className = 'path-arrow';
      arrow.setAttribute('aria-hidden', 'true');
      arrow.textContent = '›';
      frag.appendChild(arrow);
    }
    const a = document.createElement('a');
    a.className = 'path-chip';
    if (i === 0 && session.slugs.length > 1) {
      // Leftmost chip loads the full path via ?stack=.
      const rest = session.slugs.slice(1).join(',');
      a.href = `/garden/${slug}/?stack=${encodeURIComponent(rest)}`;
    } else {
      a.href = `/garden/${slug}/`;
    }
    a.textContent = slugToLabel(slug);
    frag.appendChild(a);
  });

  return frag;
}

export function clearHistory() {
  try { localStorage.removeItem(STORAGE_KEY); } catch {}
  try { sessionStorage.removeItem(STORAGE_KEY); } catch {}
}

export function setConsent(value) {
  try { localStorage.setItem(CONSENT_KEY, value); } catch {}
}
