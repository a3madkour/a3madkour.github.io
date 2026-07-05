import { test, expect } from '@playwright/test';

test('research graph mounts an SVG with nodes after d3 init (R5.2 safety net)', async ({ page }) => {
  await page.goto('/research/graph/');

  // research-graph.js mirrors garden: the canvas is a <div> and the <svg> is
  // created inside it. Nodes are <g class="research-graph-node research-graph-node-{kind}">.
  const canvas = page.locator('.research-graph-canvas');
  await expect(canvas.locator('svg')).toBeVisible();

  await expect(canvas.locator('.research-graph-node').first()).toBeVisible();
  expect(await canvas.locator('.research-graph-node').count()).toBeGreaterThan(0);
});
