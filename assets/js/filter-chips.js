// Multi-dimension AND filter chip strip.
// Used by both /essays/ and /garden/ (and any future filtered list).
//
// HTML contract (rendered by partials/filter-chips.html):
//   <nav class="filter-chips">
//     <div class="filter-dimension" data-dim="tag">
//       <button class="filter-chip is-active" data-dim="tag" data-key="all">All</button>
//       <button class="filter-chip" data-dim="tag" data-key="memory" data-tier="primary">memory</button>
//       …
//       <details class="filter-disclosure">
//         <summary class="filter-chip is-disclosure">
//           <span class="filter-disclosure-label">More tags</span>
//           <span class="filter-disclosure-count" hidden></span>
//         </summary>
//         <div class="filter-disclosure-body">
//           <input class="filter-search">
//           <div class="filter-secondary">
//             <button class="filter-chip" data-dim="tag" data-key="calvino" data-tier="secondary">…</button>
//             <p class="filter-secondary-empty" hidden>No matching tags.</p>
//           </div>
//         </div>
//       </details>
//     </div>
//   </nav>
//
// State model:
//   - tag dim: Set<string>. Empty Set === "All" active.
//   - other dims: string. 'all' === "All" active.
// AND-composition across dims; within tag dim, all selected tags must
// appear on the card (data-tags is space-separated).

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

  // Initialize state per dim
  const state = {};
  container.querySelectorAll('.filter-dimension').forEach((dimEl) => {
    const dim = dimEl.getAttribute('data-dim');
    if (!dim) return;
    state[dim] = dim === 'tag' ? new Set() : 'all';
  });

  function cardMatches(card) {
    for (const dim in state) {
      if (dim === 'tag') {
        if (state.tag.size === 0) continue;
        const tags = (card.getAttribute('data-tags') || '').split(/\s+/).filter(Boolean);
        for (const wanted of state.tag) {
          if (!tags.includes(wanted)) return false;
        }
      } else {
        if (state[dim] === 'all') continue;
        const attr = card.getAttribute(`data-${dim}`) || '';
        if (attr !== state[dim]) return false;
      }
    }
    return true;
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

    refreshChipActiveStates();
  }

  function refreshChipActiveStates() {
    container.querySelectorAll('.filter-dimension').forEach((dimEl) => {
      const dim = dimEl.getAttribute('data-dim');
      if (!dim) return;
      dimEl.querySelectorAll('.filter-chip').forEach((c) => {
        const cKey = c.getAttribute('data-key');
        let active;
        if (dim === 'tag') {
          if (cKey === 'all') {
            active = state.tag.size === 0;
          } else if (cKey) {
            active = state.tag.has(cKey);
          } else {
            active = false; // disclosure summary chip; never marked active
          }
        } else {
          active = cKey === state[dim];
        }
        c.classList.toggle('is-active', active);
      });
    });
  }

  // Click handlers — only chips with a data-key participate.
  // The disclosure summary has no data-key, so clicks bubble up to the
  // <details> element which handles open/close natively.
  container.querySelectorAll('.filter-chip[data-key]').forEach((chip) => {
    chip.addEventListener('click', (e) => {
      e.preventDefault();
      const dim = chip.getAttribute('data-dim');
      const key = chip.getAttribute('data-key');
      if (!dim || !key) return;

      if (dim === 'tag') {
        if (key === 'all') {
          state.tag.clear();
        } else if (state.tag.has(key)) {
          state.tag.delete(key);
        } else {
          state.tag.add(key);
        }
      } else {
        state[dim] = key;
      }

      applyFilters();
    });
  });

  applyFilters();
}
