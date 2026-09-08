// Recipes entry — loaded on every /recipes/ page (index + single pages).
// scripts.html sets the load predicate: {{ if eq .Section "recipes" }}.
// Wires two halves:
//   1. Scaler DOM binding (single pages): .recipe-rail[data-base-servings]
//   2. Filter chips (index): #recipe-grid guard → setupFilterChips
import { formatQuantity } from './recipe-scale.js';
import { setupFilterChips } from './filter-chips.js';

function initScaler(rail) {
  const base = parseFloat(rail.dataset.baseServings) || 1;
  const data = JSON.parse(rail.querySelector('.recipe-data').textContent);
  const serves = rail.querySelector('.recipe-serves');
  const mult = rail.querySelector('.recipe-mult');
  // Rail-scoped, and spans every <ul> in the rail (one per run of ingredients).
  const items = rail.querySelectorAll('.recipe-ing li');

  // The server render is authoritative at rest. Capture the authored strings so
  // returning to ratio 1 restores them verbatim rather than re-formatting them
  // through a second, lossy formatter (which flipped "0.5 tsp" to "½ tsp").
  const originals = new Map();
  items.forEach((li) => {
    const q = li.querySelector('.q');
    if (q) originals.set(q, q.textContent);
  });

  function apply(r) {
    const isBase = Math.abs(r - 1) <= 1e-9;
    items.forEach((li) => {
      const ing = data[+li.dataset.i];
      const q = li.querySelector('.q');
      if (!q || ing.qty == null) return;
      q.textContent = isBase
        ? originals.get(q)
        : formatQuantity(ing.qty * r, ing.unit) + (ing.unit ? ' ' + ing.unit : '');
      q.classList.toggle('changed', !isBase);
    });
  }

  // Both controls declare their own bounds in rail.html; the JS must respect
  // BOTH of them on BOTH paths or the two fields can disagree about what is
  // currently on screen.
  const SERVES_MIN = 1;
  const SERVES_MAX = 99;
  const MULT_MIN = 0.1;
  const MULT_MAX = 20;

  const clean = (n) => (Math.round(n * 100) / 100).toString();

  // Servings is the source of truth; the ratio is derived, then both are
  // clamped against BOTH controls' declared bounds so the two can never
  // disagree about what is currently displayed.
  function normalize(rawServings) {
    let s = Math.min(SERVES_MAX, Math.max(SERVES_MIN, rawServings));
    let r = s / base;
    if (r > MULT_MAX) { r = MULT_MAX; s = base * r; }
    if (r < MULT_MIN) { r = MULT_MIN; s = base * r; }
    return { s, r };
  }

  function fromServings(writeBack) {
    let raw = parseFloat(serves.value);
    if (!(raw > 0)) raw = base;
    const { s, r } = normalize(raw);
    mult.value = clean(r);
    if (writeBack) serves.value = clean(s);
    apply(r);
  }

  function fromMult(writeBack) {
    let raw = parseFloat(mult.value);
    if (!(raw > 0)) raw = 1;
    const { s, r } = normalize(base * raw);
    serves.value = clean(s);
    if (writeBack) mult.value = clean(r);
    apply(r);
  }

  // `input` tracks as you type without fighting the caret; `change` (blur or
  // Enter) is where the clamped value is written back into the field.
  serves.addEventListener('input', () => fromServings(false));
  serves.addEventListener('change', () => fromServings(true));
  mult.addEventListener('input', () => fromMult(false));
  mult.addEventListener('change', () => fromMult(true));
  rail.querySelector('.recipe-minus').addEventListener('click', () => {
    serves.value = Math.max(SERVES_MIN, (parseFloat(serves.value) || base) - 1);
    fromServings(true);
  });
  rail.querySelector('.recipe-plus').addEventListener('click', () => {
    serves.value = Math.min(SERVES_MAX, (parseFloat(serves.value) || base) + 1);
    fromServings(true);
  });
}

document.querySelectorAll('.recipe-rail').forEach(initScaler);

if (document.getElementById('recipe-grid')) {
  setupFilterChips({
    containerSelector: '.filter-chips',
    cardSelector: '.recipe-card',
    emptyStateSelector: '#recipe-empty',
  });
}
