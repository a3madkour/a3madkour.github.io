import { test, expect } from '@playwright/test';

test('garden graph mounts an SVG with nodes after d3 init (R5.2 safety net)', async ({ page }) => {
  await page.goto('/garden/graph/');

  const canvas = page.locator('.garden-graph-canvas');
  await expect(canvas.locator('svg')).toBeVisible();

  // garden-graph.js appends one <g class="garden-graph-node"> per node after
  // force init. Kept generic so it survives the R5.2 graph-core extraction.
  await expect(canvas.locator('.garden-graph-node').first()).toBeVisible();
  expect(await canvas.locator('.garden-graph-node').count()).toBeGreaterThan(0);
});
