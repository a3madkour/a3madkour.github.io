// Keyboard navigation within a shelf strip:
//   Tab lands on the first tile of each strip; ←/→ traverses tiles within
//   the strip; no wraparound; Tab exits to the next strip's first tile.

function mountShelf(strip) {
  const tiles = strip.querySelectorAll('.library-tile-link');
  if (tiles.length === 0) return;
  tiles.forEach((tile, i) => {
    tile.tabIndex = i === 0 ? 0 : -1;
  });
  strip.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const focused = document.activeElement;
    if (!focused || !focused.classList.contains('library-tile-link')) return;
    if (!strip.contains(focused)) return;
    e.preventDefault();
    const tilesNow = Array.from(strip.querySelectorAll('.library-tile-link'));
    const idx = tilesNow.indexOf(focused);
    let next;
    if (e.key === 'ArrowRight' && idx < tilesNow.length - 1) next = tilesNow[idx + 1];
    if (e.key === 'ArrowLeft'  && idx > 0)                   next = tilesNow[idx - 1];
    if (next) next.focus();
  });
}

export function initLibraryShelfNav() {
  document.querySelectorAll('.library-shelf-strip').forEach(mountShelf);
}
