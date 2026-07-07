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
