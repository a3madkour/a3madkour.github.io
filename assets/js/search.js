/* Site-wide search modal.
   Opens on header icon click or `/` keypress (when not in an input).
   Lazy-loads /pagefind/pagefind.js on first open.
*/

// Every section value Pagefind can emit must appear here, or its hits are
// dropped from the pane while still counting toward the total (RF1.1).
// The tail after 'about' is not chip-backed — those pages are only
// reachable under the All filter, which is exactly why they were invisible.
const SECTION_ORDER = ['essays', 'garden', 'research', 'works', 'library', 'streams', 'recipes', 'home', 'about',
                       'blog', 'credits', 'series', 'tags', 'other'];
const SECTION_LABEL = {
  essays:   'Essays',
  garden:   'Garden',
  research: 'Research',
  works:    'Works',
  library:  'Library',
  streams:  'Streams',
  recipes:  'Recipes',
  home:     'Home',
  about:    'About',
  blog:     'Blog',
  credits:  'Credits',
  series:   'Series',
  tags:     'Tags',
  other:    'Other',
};

let pagefindInstance = null;
let pagefindLoadPromise = null;
let currentSection = 'all';
let debounceTimer = null;
let resultRows = [];
let activeRowIndex = -1;
let searchInput = null; // set in init(); used to drive aria-activedescendant

function loadPagefind() {
  if (pagefindLoadPromise) return pagefindLoadPromise;
  pagefindLoadPromise = import('/pagefind/pagefind.js')
    .then((mod) => mod)
    .catch((err) => {
      console.error('[search] Failed to load Pagefind:', err);
      pagefindLoadPromise = null;
      throw err;
    });
  return pagefindLoadPromise;
}

function openModal(modal, input) {
  if (modal.open) return;
  modal.showModal();
  input.focus();
  // Pre-warm Pagefind once the modal is open (the user will probably search).
  loadPagefind().then((p) => { pagefindInstance = p; }).catch(() => {});
}

function closeModal(modal) {
  if (modal.open) modal.close();
}

function debounce(fn, ms) {
  return (...args) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => fn(...args), ms);
  };
}

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderResults(resultsEl, statusEl, groups, totalMs, query, matchCount) {
  resultRows = [];
  activeRowIndex = -1;

  if (!query) {
    resultsEl.innerHTML = '';
    statusEl.textContent = '';
    return;
  }

  // Count what will actually render, not what was fetched: a section missing
  // from SECTION_ORDER contributes rows to `groups` that never reach the pane.
  const shown = SECTION_ORDER.reduce((acc, s) => acc + (groups[s] ? groups[s].length : 0), 0);
  if (shown === 0) {
    resultsEl.innerHTML = '<p class="search-modal-empty">No results.</p>';
    statusEl.textContent = `0 results in ${totalMs}ms`;
    return;
  }

  const matches = typeof matchCount === 'number' ? matchCount : shown;
  const sections = SECTION_ORDER.filter((s) => groups[s] && groups[s].length > 0);
  let html = '';
  let optIdx = 0; // running index so each option gets a unique id for aria-activedescendant
  for (const section of sections) {
    // section is a `group` inside the listbox; the <ol> is presentational so
    // the listbox → group → option chain stays valid.
    html += `<section data-section="${section}" role="group" aria-label="${SECTION_LABEL[section]}"><h3>${SECTION_LABEL[section]}</h3><ol role="presentation">`;
    for (const row of groups[section]) {
      const spoilers = parseInt(row.meta?.spoilers || '0', 10);
      const title = row.meta?.title || row.url;
      // role="option" carries the selection; the inner <a> is taken out of the
      // tab order (tabindex=-1) — arrow-key listbox nav drives it, Enter opens.
      html += `
        <li class="search-modal-result" id="search-opt-${optIdx}" role="option" aria-selected="false" data-url="${escapeHtml(row.url)}">
          <a href="${escapeHtml(row.url)}" tabindex="-1">
            <div class="search-modal-result-title">${escapeHtml(title)}</div>
            <div class="search-modal-result-snippet">${row.excerpt}</div>
            ${spoilers > 0 ? `<div class="search-modal-result-spoilers">${spoilers} spoiler block${spoilers === 1 ? '' : 's'} hidden from search</div>` : ''}
          </a>
        </li>`;
      optIdx += 1;
    }
    html += '</ol></section>';
  }
  resultsEl.innerHTML = html;
  resultRows = Array.from(resultsEl.querySelectorAll('.search-modal-result'));
  activeRowIndex = -1;
  if (searchInput) {
    searchInput.removeAttribute('aria-activedescendant');
    searchInput.setAttribute('aria-expanded', resultRows.length > 0 ? 'true' : 'false');
  }
  // Say what is on screen. When Pagefind matched more than the 30 rows we
  // fetch, say so explicitly rather than reporting the cap as the total.
  statusEl.textContent = matches > shown
    ? `Showing ${shown} of ${matches} results in ${totalMs}ms`
    : `${shown} result${shown === 1 ? '' : 's'} in ${totalMs}ms`;
}

async function performSearch(query, resultsEl, statusEl) {
  if (!query || !query.trim()) {
    renderResults(resultsEl, statusEl, {}, 0, '');
    return;
  }
  try {
    if (!pagefindInstance) pagefindInstance = await loadPagefind();
  } catch (e) {
    resultsEl.innerHTML = '<p class="search-modal-empty">Search is unavailable.</p>';
    return;
  }
  const t0 = performance.now();
  const search = currentSection === 'all'
    ? await pagefindInstance.search(query)
    : await pagefindInstance.search(query, { filters: { section: [currentSection] } });
  // Pagefind returns ids; fetch their data in parallel.
  const top = search.results.slice(0, 30);
  const datas = await Promise.all(top.map((r) => r.data()));
  const groups = {};
  for (const d of datas) {
    const section = d.meta?.section || 'other';
    if (!groups[section]) groups[section] = [];
    groups[section].push(d);
  }
  const elapsed = Math.round(performance.now() - t0);
  renderResults(resultsEl, statusEl, groups, elapsed, query, search.results.length);
}

function setActiveRow(idx) {
  if (resultRows.length === 0) return;
  if (activeRowIndex >= 0) {
    resultRows[activeRowIndex].classList.remove('is-active');
    resultRows[activeRowIndex].setAttribute('aria-selected', 'false');
  }
  activeRowIndex = Math.max(0, Math.min(resultRows.length - 1, idx));
  const active = resultRows[activeRowIndex];
  active.classList.add('is-active');
  active.setAttribute('aria-selected', 'true');
  active.scrollIntoView({ block: 'nearest' });
  if (searchInput && active.id) searchInput.setAttribute('aria-activedescendant', active.id);
}

function openActiveRow(newTab) {
  if (activeRowIndex < 0) return;
  const row = resultRows[activeRowIndex];
  const url = row.dataset.url;
  if (!url) return;
  if (newTab) window.open(url, '_blank');
  else window.location.href = url;
}

function init() {
  const modal = document.querySelector('.search-modal');
  if (!modal) return;
  const input = modal.querySelector('[data-search-input]');
  searchInput = input;
  const resultsEl = modal.querySelector('[data-search-results]');
  const statusEl = modal.querySelector('[data-search-status]');
  const chips = modal.querySelectorAll('[data-section]');
  const trigger = document.querySelector('[data-search-toggle]');

  // Header icon click
  if (trigger) trigger.addEventListener('click', () => openModal(modal, input));

  // `/` keyboard shortcut anywhere
  window.addEventListener('keydown', (e) => {
    if (e.key !== '/') return;
    const tag = (document.activeElement?.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || document.activeElement?.isContentEditable) return;
    e.preventDefault();
    openModal(modal, input);
  });

  // Filter chips
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      chips.forEach((c) => c.classList.remove('is-active'));
      chip.classList.add('is-active');
      currentSection = chip.dataset.section;
      performSearch(input.value, resultsEl, statusEl);
    });
  });

  // Debounced input
  const debouncedSearch = debounce(() => performSearch(input.value, resultsEl, statusEl), 150);
  input.addEventListener('input', debouncedSearch);

  // Keyboard nav inside the modal
  modal.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveRow(activeRowIndex < 0 ? 0 : activeRowIndex + 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveRow(activeRowIndex - 1);
    } else if (e.key === 'Enter') {
      if (activeRowIndex >= 0) {
        e.preventDefault();
        openActiveRow(e.metaKey || e.ctrlKey);
      }
    }
  });

  // Reset state on close
  modal.addEventListener('close', () => {
    input.value = '';
    input.removeAttribute('aria-activedescendant');
    input.setAttribute('aria-expanded', 'false');
    resultsEl.innerHTML = '';
    statusEl.textContent = '';
    activeRowIndex = -1;
    resultRows = [];
    currentSection = 'all';
    chips.forEach((c) => c.classList.toggle('is-active', c.dataset.section === 'all'));
  });

  // Click backdrop to close (Pagefind UX expectation)
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal(modal);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
