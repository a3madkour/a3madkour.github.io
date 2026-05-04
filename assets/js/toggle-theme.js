// Theme toggle — cycles system → light → dark → system.
// Stores override in localStorage key "theme-pref".
// Initial apply happens via an inline script in head.html (FOUC prevention);
// this file handles the click cycle and label updates.

(function () {
  const STORAGE_KEY = 'theme-pref';
  const ORDER = ['system', 'light', 'dark'];

  const root = document.documentElement;

  // Storage may throw in restricted contexts (private browsing strict, sandboxed
  // iframes). Wrap access so the toggle still works for the session even when
  // persistence is unavailable.
  function readStored() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (_) {
      return null;
    }
  }

  function writeStored(value) {
    try {
      if (value === null) localStorage.removeItem(STORAGE_KEY);
      else localStorage.setItem(STORAGE_KEY, value);
    } catch (_) {
      // ignore — session-only persistence
    }
  }

  function apply(pref) {
    if (pref === 'light' || pref === 'dark') {
      root.setAttribute('data-theme', pref);
    } else {
      root.removeAttribute('data-theme');
    }
  }

  function read() {
    const stored = readStored();
    return ORDER.includes(stored) ? stored : 'system';
  }

  function next(current) {
    const i = ORDER.indexOf(current);
    return ORDER[(i + 1) % ORDER.length];
  }

  // Re-apply on script execution (matches the inline-head script's result;
  // safe to run again — idempotent).
  apply(read());

  function updateButtonLabel(button, pref) {
    const labels = {
      system: 'Theme: system (click to switch to light)',
      light:  'Theme: light (click to switch to dark)',
      dark:   'Theme: dark (click to switch to system)',
    };
    button.setAttribute('aria-label', labels[pref]);
    button.setAttribute('title', labels[pref]);
    button.dataset.themePref = pref;
  }

  document.addEventListener('DOMContentLoaded', () => {
    const button = document.querySelector('[data-theme-toggle]');
    if (!button) return;

    updateButtonLabel(button, read());

    button.addEventListener('click', () => {
      const newPref = next(read());
      writeStored(newPref === 'system' ? null : newPref);
      apply(newPref);
      updateButtonLabel(button, newPref);
    });
  });
})();
