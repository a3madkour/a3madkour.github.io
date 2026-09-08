import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatQuantity, unitMode } from '../../assets/js/recipe-scale.js';

test('grams round to whole', () => {
  assert.equal(unitMode('g'), 'whole');
  assert.equal(formatQuantity(1200, 'g'), '1200');
  assert.equal(formatQuantity(400.4, 'g'), '400');
});

test('kg/l show one decimal, trailing zero trimmed', () => {
  assert.equal(unitMode('kg'), 'decimal');
  assert.equal(formatQuantity(2.25, 'kg'), '2.3');
  assert.equal(formatQuantity(3, 'kg'), '3');
});

test('spoons and counts use eighths fractions', () => {
  assert.equal(unitMode('tbsp'), 'frac');
  assert.equal(unitMode(null), 'frac');
  assert.equal(formatQuantity(3, 'tbsp'), '3');
  assert.equal(formatQuantity(1.5, null), '1½');
  assert.equal(formatQuantity(0.5, null), '½');
  assert.equal(formatQuantity(0.25, 'tsp'), '¼');
  assert.equal(formatQuantity(2.75, null), '2¾');
});

test('a positive quantity never formats to zero', () => {
  assert.equal(formatQuantity(0.25, 'g'), '0.25');
  assert.equal(formatQuantity(0.04, 'kg'), '0.04');
  assert.equal(formatQuantity(0.05, null), '0.05');
  assert.equal(formatQuantity(0.5, 'g'), '0.5');
});

test('zero stays zero', () => {
  assert.equal(formatQuantity(0, 'g'), '0');
  assert.equal(formatQuantity(0, null), '0');
});

test('values above the floor are unchanged', () => {
  assert.equal(formatQuantity(1200, 'g'), '1200');
  assert.equal(formatQuantity(2.25, 'kg'), '2.3');
  assert.equal(formatQuantity(1.5, null), '1½');
});

// The decimal branch's floor is a range guard, symmetric with the whole
// branch's: one-decimal rounding is only safe once the value can survive it.
// Below 0.1 it inflates (0.05 -> "0.1" is a 100% error), so keep two sig digits.
test('sub-0.1 kg/l quantities keep two significant digits, not a rounded 0.1', () => {
  assert.equal(formatQuantity(0.05, 'kg'), '0.05');
  assert.equal(formatQuantity(0.06, 'kg'), '0.06');
  assert.equal(formatQuantity(0.09, 'l'), '0.09');
  assert.equal(formatQuantity(0.099, 'kg'), '0.099');
});

test('the decimal floor does not disturb values at or above 0.1', () => {
  assert.equal(formatQuantity(0.1, 'kg'), '0.1');
  assert.equal(formatQuantity(0.15, 'kg'), '0.2');
  assert.equal(formatQuantity(0.94, 'l'), '0.9');
  assert.equal(formatQuantity(1.25, 'kg'), '1.3');
});
