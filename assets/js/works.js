// Works page-level enhancements.
// - Multi-dimension AND filter chips on the three works index pages.
import { setupFilterChips } from './filter-chips.js';

function init() {
  // Games index
  if (document.querySelector('.works-games-index .filter-chips')) {
    setupFilterChips({
      containerSelector: '.works-games-index .filter-chips',
      cardSelector: '.works-game-card',
    });
  }
  // Music index
  if (document.querySelector('.works-music-index .filter-chips')) {
    setupFilterChips({
      containerSelector: '.works-music-index .filter-chips',
      cardSelector: '.works-music-row',
    });
  }
  // Poetry index
  if (document.querySelector('.works-poetry-index .filter-chips')) {
    setupFilterChips({
      containerSelector: '.works-poetry-index .filter-chips',
      cardSelector: '.works-poem-row',
    });
  }

  // Umbrella (/works/) — Bento grid + tag + medium dims + graph toggle.
  if (document.querySelector('.works-umbrella .works-bento')) {
    setupFilterChips({
      containerSelector: '.works-umbrella .filter-chips',
      cardSelector: '.works-tile',
      emptyStateSelector: '.works-empty',
    });

    const toggle = document.getElementById('works-graph-toggle');
    const panel = document.getElementById('works-graph-panel');
    if (toggle && panel) {
      const closeBtn = panel.querySelector('.graph-panel-close');
      const open = () => {
        panel.hidden = false;
        toggle.setAttribute('aria-expanded', 'true');
      };
      const close = () => {
        panel.hidden = true;
        toggle.setAttribute('aria-expanded', 'false');
      };
      toggle.addEventListener('click', () => {
        // Mobile fallback: navigate to standalone /works/graph/ instead of toggling.
        if (window.matchMedia('(max-width: 720px)').matches) {
          window.location.href = '/works/graph/';
          return;
        }
        if (panel.hidden) open(); else close();
      });
      if (closeBtn) closeBtn.addEventListener('click', close);
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !panel.hidden) close();
      });
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
