// Essay-specific progressive enhancements.
// - Sidenote/footnote popup on narrow viewports
// - Smooth-scroll on TOC clicks (respects prefers-reduced-motion)
// - Citation hover-card runtime (singleton, hover/focus/tap)
//
// Guards on .essay-body presence; bails on non-essay pages.

import { setupFilterChips } from './filter-chips.js';
import { setupCitationCards } from './citation-card.js';

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

function init() {
  if (!document.querySelector('.essay-body') && !document.querySelector('.essay-grid')) return;
  setupSidenotePopups();
  setupTocSmoothScroll();
  setupCitationCards();
  setupFilterChips({
    containerSelector: '.filter-chips',
    cardSelector: '.essay-card',
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
