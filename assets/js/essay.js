// Essay-specific progressive enhancements.
// - Sidenote/footnote popup on narrow viewports
// - Smooth-scroll on TOC clicks (respects prefers-reduced-motion)
// - Citation hover-card hook (no-op placeholder for Phase 3)
//
// Guards on .essay-body presence; bails on non-essay pages.

const RAIL_BREAKPOINT = 1100;

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function isNarrow() {
  return window.innerWidth < RAIL_BREAKPOINT;
}

function setupSidenotePopups() {
  const markers = document.querySelectorAll('.essay-body .sidenote-marker');
  markers.forEach((marker) => {
    marker.addEventListener('click', (e) => {
      if (!isNarrow()) return;
      e.preventDefault();
      const id = marker.getAttribute('aria-controls');
      const aside = id ? document.getElementById(id) : null;
      if (!aside) return;
      aside.classList.toggle('is-open');
    });
    marker.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        marker.click();
      }
    });
  });

  document.addEventListener('click', (e) => {
    if (!(e.target instanceof Element)) return;
    if (e.target.closest('.sidenote-marker') || e.target.closest('.sidenote.is-open')) return;
    document.querySelectorAll('.sidenote.is-open').forEach((el) => el.classList.remove('is-open'));
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.sidenote.is-open').forEach((el) => el.classList.remove('is-open'));
    }
  });
}

function setupTocSmoothScroll() {
  const tocLinks = document.querySelectorAll('.essay-toc a[href^="#"]');
  tocLinks.forEach((link) => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      if (!href) return;
      const target = document.querySelector(href);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({
        behavior: reducedMotion() ? 'auto' : 'smooth',
        block: 'start'
      });
      history.pushState(null, '', href);
    });
  });
}

function setupCitationHook() {
  // Placeholder — Phase 3 will attach a hover-card here. For now we just
  // mark the elements so future code can find them without a markup change.
  document.querySelectorAll('[data-cite-key]').forEach((el) => {
    el.classList.add('citation-hookable');
  });
}

function setupFilterChips() {
  const grid = document.querySelector('.essay-grid');
  const strip = document.querySelector('.filter-strip');
  if (!grid || !strip) return;

  function applyFilter(dim, value) {
    grid.setAttribute('data-filter-state', value === 'all' ? 'all' : `${dim}:${value}`);
    grid.querySelectorAll('.essay-card').forEach((card) => {
      if (value === 'all') {
        card.style.display = '';
        return;
      }
      const cardValue = card.getAttribute(`data-${dim === 'tag' ? 'tags' : dim}`) || '';
      const matches = dim === 'tag'
        ? cardValue.split(' ').includes(value)
        : cardValue === value;
      card.style.display = matches ? '' : 'none';
    });
  }

  strip.querySelectorAll('.filter-dimension').forEach((dimEl) => {
    const dim = dimEl.getAttribute('data-dim');
    if (!dim) return;
    dimEl.querySelectorAll('.filter-chip').forEach((chip) => {
      const handler = (e) => {
        e.preventDefault();
        // Clear all chip active states across all dimensions
        strip.querySelectorAll('.filter-chip').forEach((c) => c.classList.remove('is-active'));
        // Within each other dimension, mark "all" active
        strip.querySelectorAll('.filter-dimension').forEach((other) => {
          if (other !== dimEl) {
            const allChip = other.querySelector('.filter-chip[data-filter="all"]');
            if (allChip) allChip.classList.add('is-active');
          }
        });
        chip.classList.add('is-active');
        const value = chip.getAttribute('data-filter') || 'all';
        applyFilter(dim, value);
      };
      chip.addEventListener('click', handler);
      if (chip.tagName === 'SPAN') {
        chip.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') handler(e);
        });
      }
    });
  });

  // Initial state
  grid.setAttribute('data-filter-state', 'all');
}

function init() {
  if (!document.querySelector('.essay-body') && !document.querySelector('.essay-grid')) return;
  setupSidenotePopups();
  setupTocSmoothScroll();
  setupCitationHook();
  setupFilterChips();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
