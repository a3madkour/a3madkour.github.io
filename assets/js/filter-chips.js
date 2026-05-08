// Multi-dimension AND filter chip strip.
// Used by both /essays/ and /garden/ (and any future filtered list).
//
// HTML contract (rendered by partials/filter-chips.html):
//   <nav class="filter-chips">
//     <div class="filter-dimension" data-dim="tag">
//       <button class="filter-chip is-active" data-dim="tag" data-key="all">All</button>
//       <button class="filter-chip" data-dim="tag" data-key="memory">memory</button>
//       …
//     </div>
//   </nav>
//
// Cards declare their values as data-{dim} attributes. Visibility is the
// AND of all non-"all" dimensions; sections and the global empty-state
// element toggle their hidden attribute based on tile counts.
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

  // state: { [dim]: activeKey }, all initialized to "all"
  const state = {};
  container.querySelectorAll('.filter-dimension').forEach((dimEl) => {
    const dim = dimEl.getAttribute('data-dim');
    if (dim) state[dim] = 'all';
  });

  function cardMatches(card) {
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
      state[dim] = key;

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
