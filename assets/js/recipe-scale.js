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
      // Symmetric with the whole branch: one-decimal rounding is only safe
      // once the value can survive it. Under 0.1 kg/l it inflates rather than
      // zeroes (0.05 -> "0.1" is a 100% error), so keep two sig digits there.
      if (value > 0 && value < 0.1) return sig2(value);
      return (Math.round(value * 10) / 10).toString();
    }
    default:
      return fmtFrac(value);
  }
}

/** Singularise a yield unit for a count of exactly 1.
 *
 * Handles the regular English plurals a `yield_unit` actually takes, plus the
 * -ves/-f family, which the trailing-s rule alone mangles ("loaves" -> "loave",
 * RF2.3). Genuinely irregular forms are returned untouched: `yield_unit` is a
 * free-form optional string with no schema constraint, so this is a best-effort
 * display nicety, not a contract.
 */
export function singularUnit(unit) {
  const u = unit || '';
  if (/ves$/i.test(u)) return u.slice(0, -3) + 'f';
  if (/(ch|sh|s|x|z)es$/i.test(u)) return u.slice(0, -2);
  if (/[^s]s$/i.test(u)) return u.slice(0, -1);
  return u;
}
