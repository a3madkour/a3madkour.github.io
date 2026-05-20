// Streams runtime. Spec: docs/superpowers/specs/2026-05-13-streams-section-design.md §8.
// Two responsibilities:
//   1. Click-to-load YouTube embed (per-stream single pages).
//   2. Filter-chip setup for the /streams/ section index (no-op on single pages).
// Self-guards on selectors so it's safe to load on any streams page.

import { setupFilterChips } from './filter-chips.js';

export function initStreams() {
  initEmbed();
  initListFilters();
}

function initEmbed() {
  const els = document.querySelectorAll('.yt-embed');
  if (!els.length) return;
  els.forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.dataset.videoId;
      if (!id) return;
      if (el.classList.contains('yt-embed-loaded')) return;
      const iframe = document.createElement('iframe');
      iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1`;
      iframe.allow =
        'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
      iframe.allowFullscreen = true;
      iframe.title = 'YouTube video';
      iframe.loading = 'lazy';
      iframe.style.width = '100%';
      iframe.style.height = '100%';
      iframe.style.border = '0';
      el.replaceChildren(iframe);
      el.classList.add('yt-embed-loaded');
    });
  });
}

function initListFilters() {
  if (!document.querySelector('.streams-index .filter-chips')) return;
  setupFilterChips({
    containerSelector: '.streams-index .filter-chips',
    cardSelector: '.stream-card',
  });
}
