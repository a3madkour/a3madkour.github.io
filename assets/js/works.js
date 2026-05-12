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
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
