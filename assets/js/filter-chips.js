// Multi-dimension filter chip strip.
// Used by both /essays/ and /garden/ (and any future filtered list).
//
// HTML contract (rendered by partials/filter-chips.html):
//   <nav class="filter-chips" data-filter-mode="and|single">
//     <div class="filter-dimension" data-dim="tag">
//       <button class="filter-chip is-active" data-dim="tag" data-key="all">All</button>
//       <button class="filter-chip" data-dim="tag" data-key="memory">memory</button>
//       …
//     </div>
//   </nav>
//
// Cards are any element matching `[data-dim-target]` (each grid passes its
// own selector). Each card declares its values as data-{dim} attributes.
// data-tags is space-separated; other dims are single-valued.

export function setupFilterChips({
  containerSelector = '.filter-chips',
  cardSelector,
  sectionSelector,
  emptyStateSelector,
} = {}) {
  const container = document.querySelector(containerSelector);
  if (!container) return;
  if (!cardSelector) {
    console.warn('setupFilterChips: cardSelector is required');
    return;
  }

  const mode = container.getAttribute('data-filter-mode') || 'and';
  // state: { [dim]: activeKey }, all initialized to "all"
  const state = {};
  container.querySelectorAll('.filter-dimension').forEach((dimEl) => {
    const dim = dimEl.getAttribute('data-dim');
    if (dim) state[dim] = 'all';
  });

  function cardMatches(card) {
    if (mode === 'single') {
      // Single-active legacy: at most one dim has a non-"all" active key.
      // A card matches iff that single active dim's value is satisfied.
      let activeDim = null;
      let activeKey = 'all';
      for (const dim in state) {
        if (state[dim] !== 'all') { activeDim = dim; activeKey = state[dim]; break; }
      }
      if (!activeDim) return true;
      return cardHasValue(card, activeDim, activeKey);
    }
    // and mode: every non-"all" dim must match
    for (const dim in state) {
      if (state[dim] === 'all') continue;
      if (!cardHasValue(card, dim, state[dim])) return false;
    }
    return true;
  }

  function cardHasValue(card, dim, key) {
    const attr = card.getAttribute(`data-${dim === 'tag' ? 'tags' : dim}`) || '';
    if (dim === 'tag' || dim === 'tags') {
      return attr.split(/\s+/).filter(Boolean).includes(key);
    }
    return attr === key;
  }

  function applyFilters() {
    const cards = document.querySelectorAll(cardSelector);
    let visibleCount = 0;
    cards.forEach((card) => {
      const visible = cardMatches(card);
      if (visible) {
        card.removeAttribute('hidden');
        visibleCount += 1;
      } else {
        card.setAttribute('hidden', '');
      }
    });

    if (sectionSelector) {
      document.querySelectorAll(sectionSelector).forEach((section) => {
        const anyVisible = section.querySelector(`${cardSelector}:not([hidden])`);
        if (anyVisible) {
          section.removeAttribute('hidden');
        } else {
          section.setAttribute('hidden', '');
        }
      });
    }

    if (emptyStateSelector) {
      const empty = document.querySelector(emptyStateSelector);
      if (empty) {
        if (visibleCount === 0) {
          empty.removeAttribute('hidden');
        } else {
          empty.setAttribute('hidden', '');
        }
      }
    }
  }

  container.querySelectorAll('.filter-chip').forEach((chip) => {
    chip.addEventListener('click', (e) => {
      e.preventDefault();
      const dim = chip.getAttribute('data-dim');
      const key = chip.getAttribute('data-key') || 'all';
      if (!dim) return;

      if (mode === 'single') {
        // Clear every dim back to "all" first
        for (const d in state) state[d] = 'all';
        state[dim] = key;
      } else {
        state[dim] = key;
      }

      // Reflect active state on chip elements
      container.querySelectorAll('.filter-dimension').forEach((dimEl) => {
        const dDim = dimEl.getAttribute('data-dim');
        if (!dDim) return;
        dimEl.querySelectorAll('.filter-chip').forEach((c) => {
          const cKey = c.getAttribute('data-key');
          c.classList.toggle('is-active', cKey === state[dDim]);
        });
      });

      applyFilters();
    });
  });

  applyFilters();
}
