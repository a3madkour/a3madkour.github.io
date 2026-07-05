import { test, expect } from '@playwright/test';

test('works graph mounts an SVG with nodes after d3 init (R5.2 safety net)', async ({ page }) => {
  await page.goto('/works/graph/');

  // Post-R5.2: works matches garden/research — <div class="works-graph-canvas">
  // with the <svg> created inside. Nodes are <g class="works-graph-node">.
  const canvas = page.locator('.works-graph-canvas');
  await expect(canvas.locator('svg')).toBeVisible();

  await expect(canvas.locator('.works-graph-node').first()).toBeVisible();
  expect(await canvas.locator('.works-graph-node').count()).toBeGreaterThan(0);
});
