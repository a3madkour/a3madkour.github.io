// Pure, DOM-free scaling helpers. Imported by entry-recipes.js (browser)
// and tests/unit/recipe-scale.test.mjs (node --test). No side effects.
const WHOLE_UNITS = new Set(['g', 'ml']);
const DECIMAL_UNITS = new Set(['kg', 'l']);
const VULGAR = { 0: '', 1: '⅛', 2: '¼', 3: '⅜', 4: '½', 5: '⅝', 6: '¾', 7: '⅞' };

export function unitMode(unit) {
  const u = (unit || '').toLowerCase();
  if (WHOLE_UNITS.has(u)) return 'whole';
  if (DECIMAL_UNITS.has(u)) return 'decimal';
  return 'frac';
}

function fmtFrac(v) {
  const whole = Math.floor(v + 1e-9);
  let e = Math.round((v - whole) * 8);
  let w = whole;
  if (e === 8) { w += 1; e = 0; }
  const f = VULGAR[e];
  if (w === 0 && f === '') return '0';
  if (w === 0) return f;
  return f ? (w + f) : String(w);
}

export function formatQuantity(value, unit) {
  switch (unitMode(unit)) {
    case 'whole':   return String(Math.round(value));
    case 'decimal': return (Math.round(value * 10) / 10).toString();
    default:        return fmtFrac(value);
  }
}
