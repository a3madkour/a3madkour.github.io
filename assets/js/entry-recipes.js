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

  const clean = (n) => (Math.round(n * 100) / 100).toString();

  function fromServings() {
    let s = parseFloat(serves.value);
    if (!(s > 0)) s = base;
    s = Math.min(99, s);
    const r = s / base;
    mult.value = clean(r);
    apply(r);
  }

  function fromMult() {
    let r = parseFloat(mult.value);
    if (!(r > 0)) r = 1;
    serves.value = clean(base * r);
    apply(r);
  }

  serves.addEventListener('input', fromServings);
  mult.addEventListener('input', fromMult);
  rail.querySelector('.recipe-minus').addEventListener('click', () => {
    serves.value = Math.max(1, (parseFloat(serves.value) || base) - 1);
    fromServings();
  });
  rail.querySelector('.recipe-plus').addEventListener('click', () => {
    serves.value = Math.min(99, (parseFloat(serves.value) || base) + 1);
    fromServings();
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
