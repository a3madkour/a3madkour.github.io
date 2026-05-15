// Keyboard navigation within a shelf strip:
//   Tab lands on the first tile's Cite button; ←/→ traverses tiles
//   within the strip (jumps Cite button to Cite button); no wraparound;
//   Tab exits to the next strip's first tile.
//
// Tiles no longer have a wrapping anchor — the Cite button is the
// per-tile focusable anchor for keyboard navigation.

function mountShelf(strip) {
  const tileCtas = strip.querySelectorAll('.library-tile > .library-tile-actions > .cite-cta');
  if (tileCtas.length === 0) return;
  tileCtas.forEach((cta, i) => {
    cta.tabIndex = i === 0 ? 0 : -1;
  });
  strip.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const focused = document.activeElement;
    if (!focused || !focused.classList.contains('cite-cta')) return;
    if (!strip.contains(focused)) return;
    e.preventDefault();
    const ctasNow = Array.from(strip.querySelectorAll('.library-tile > .library-tile-actions > .cite-cta'));
    const idx = ctasNow.indexOf(focused);
    let next;
    if (e.key === 'ArrowRight' && idx < ctasNow.length - 1) next = ctasNow[idx + 1];
    if (e.key === 'ArrowLeft'  && idx > 0)                  next = ctasNow[idx - 1];
    if (next) next.focus();
  });
}

export function initLibraryShelfNav() {
  document.querySelectorAll('.library-shelf-strip').forEach(mountShelf);
}
