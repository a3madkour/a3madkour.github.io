// Garden page-level enhancements.
// - Multi-dimension AND filter chips on /garden/
// (Spoilers are CSS+native <details>; citations deferred.)
import { setupFilterChips } from './filter-chips.js';

function init() {
  if (!document.querySelector('.garden-grid') && !document.querySelector('.garden-note')) return;
  if (document.querySelector('.garden-grid .filter-chips')) {
    setupFilterChips({
      containerSelector: '.garden-grid .filter-chips',
      cardSelector: '.garden-tile',
      sectionSelector: '.garden-grid [data-garden-section]',
      emptyStateSelector: '.garden-empty',
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
