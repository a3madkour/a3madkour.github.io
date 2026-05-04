// Theme toggle — cycles light → dark → system.
// Stores override in localStorage key "theme-pref".
// On load: if "theme-pref" is set, applies it; otherwise CSS handles
// system preference via @media (prefers-color-scheme: dark) :root:not([data-theme]).

(function () {
  const STORAGE_KEY = 'theme-pref';
  const ORDER = ['system', 'light', 'dark'];

  const root = document.documentElement;

  function apply(pref) {
    if (pref === 'light' || pref === 'dark') {
      root.setAttribute('data-theme', pref);
    } else {
      root.removeAttribute('data-theme');
    }
  }

  function read() {
    const stored = localStorage.getItem(STORAGE_KEY);
    return ORDER.includes(stored) ? stored : 'system';
  }

  function next(current) {
    const i = ORDER.indexOf(current);
    return ORDER[(i + 1) % ORDER.length];
  }

  // Initialize on load
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
      if (newPref === 'system') {
        localStorage.removeItem(STORAGE_KEY);
      } else {
        localStorage.setItem(STORAGE_KEY, newPref);
      }
      apply(newPref);
      updateButtonLabel(button, newPref);
    });
  });
})();
