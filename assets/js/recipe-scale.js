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

// Two significant digits — the floor that keeps a scaled-down quantity from
// rounding away to "0". Number() drops toPrecision's trailing zeros.
function sig2(v) {
  return String(Number(v.toPrecision(2)));
}

function fmtFrac(v) {
  const whole = Math.floor(v + 1e-9);
  let e = Math.round((v - whole) * 8);
  let w = whole;
  if (e === 8) { w += 1; e = 0; }
  const f = VULGAR[e];
  if (w === 0 && f === '') return v > 0 ? sig2(v) : '0';
  if (w === 0) return f;
  return f ? (w + f) : String(w);
}

export function formatQuantity(value, unit) {
  switch (unitMode(unit)) {
    case 'whole': {
      // Under 1 g/ml, whole rounding either zeroes the value (0.25 -> "0") or
      // doubles it (0.5 -> "1"), so the sub-unit range keeps two sig digits.
      if (value > 0 && value < 1) return sig2(value);
      return String(Math.round(value));
    }
    case 'decimal': {
      const r = Math.round(value * 10) / 10;
      return r === 0 && value > 0 ? sig2(value) : r.toString();
    }
    default:
      return fmtFrac(value);
  }
}
