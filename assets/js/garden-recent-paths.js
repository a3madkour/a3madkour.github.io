// Mounts the "Recent paths" widget on /garden/ AND the /garden/history/ page.
// One module covers both because rendering is identical; only count + empty
// state differ.

import {
  readHistory,
  dedupe,
  renderPath,
  clearHistory,
  setConsent,
} from './garden-history.js';

const CONSENT_KEY = 'path-log-consent';

function readConsent() {
  try { return localStorage.getItem(CONSENT_KEY) || 'unset'; }
  catch { return 'unset'; }
}

function mountWidget(root) {
  const sessions = dedupe(readHistory()).slice(0, 5);
  if (sessions.length === 0) return;

  const list = root.querySelector('.recent-paths-list');
  sessions.forEach(s => {
    const li = document.createElement('li');
    li.appendChild(renderPath(s));
    list.appendChild(li);
  });

  root.hidden = false;

  const clearBtn = root.querySelector('.recent-paths-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (!confirm('Clear all stored reading history?')) return;
      clearHistory();
      list.replaceChildren();
      root.hidden = true;
    });
  }
}

function mountHistoryPage(root) {
  const consent = readConsent();
  const allSessions = readHistory();
  const dedupSessions = dedupe(allSessions);

  const status = root.querySelector('.garden-history-status');
  const actions = root.querySelector('.garden-history-actions');
  const list = root.querySelector('.garden-history-list');
  const empty = root.querySelector('.garden-history-empty');

  if (dedupSessions.length === 0) {
    empty.hidden = false;
    let branch;
    if (consent === 'no') branch = 'no';
    else if (consent === 'unset') branch = 'unset';
    else branch = 'ok';
    empty.querySelectorAll('[data-state]').forEach(div => {
      div.hidden = div.dataset.state !== branch;
    });
    const reenable = empty.querySelector('.reenable-tracking');
    if (reenable) {
      reenable.addEventListener('click', () => {
        setConsent('unset');
        window.location.reload();
      });
    }
    return;
  }

  const sCount = allSessions.length;
  const dCount = dedupSessions.length;
  status.textContent = `${sCount} session${sCount === 1 ? '' : 's'} stored · ${dCount} unique path${dCount === 1 ? '' : 's'} after dedup`;
  status.hidden = false;
  actions.hidden = false;
  list.hidden = false;

  dedupSessions.forEach(s => {
    const li = document.createElement('li');
    li.appendChild(renderPath(s));
    list.appendChild(li);
  });

  const clearBtn = root.querySelector('.garden-history-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (!confirm('Clear all stored reading history?')) return;
      clearHistory();
      window.location.reload();
    });
  }
}

function init() {
  const widget = document.querySelector('.garden-recent-paths');
  if (widget) mountWidget(widget);

  const historyPage = document.querySelector('.garden-history');
  if (historyPage) mountHistoryPage(historyPage);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
