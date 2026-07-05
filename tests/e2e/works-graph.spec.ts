import { test, expect } from '@playwright/test';

test('works graph mounts nodes after d3 init (R5.2 safety net)', async ({ page }) => {
  await page.goto('/works/graph/');

  // works-graph.js is the outlier: the canvas element IS the <svg>
  // (<svg class="works-graph-canvas" id="works-graph-canvas">), so nodes mount
  // directly inside it rather than in a nested <svg>. Nodes are
  // <g class="works-graph-node">. Kept generic so it survives the R5.2 extraction.
  const canvas = page.locator('svg.works-graph-canvas');
  await expect(canvas).toBeVisible();

  await expect(canvas.locator('.works-graph-node').first()).toBeVisible();
  expect(await canvas.locator('.works-graph-node').count()).toBeGreaterThan(0);
});
