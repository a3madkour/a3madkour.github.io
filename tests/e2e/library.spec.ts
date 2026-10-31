import { test, expect } from '@playwright/test';

// A heading's § affordance is emitted as the heading's next sibling. Unless
// the heading is laid out inline, the glyph drops to a line of its own under
// it — which is how "Browse the catalogue" shipped.
test('library umbrella: every heading § sits on its heading line', async ({ page }) => {
  await page.goto('/library/');
  const pairs = page.locator('main h2[id] + .anchor-link');
  const n = await pairs.count();
  expect(n).toBeGreaterThan(0);
  for (let i = 0; i < n; i++) {
    const glyph = pairs.nth(i);
    const heading = glyph.locator('xpath=preceding-sibling::h2[1]');
    const h = await heading.boundingBox();
    const g = await glyph.boundingBox();
    expect(h && g, 'both boxes laid out').toBeTruthy();
    const mid = g!.y + g!.height / 2;
    expect(mid, `§ after "${await heading.innerText()}"`).toBeGreaterThanOrEqual(h!.y);
    expect(mid, `§ after "${await heading.innerText()}"`).toBeLessThanOrEqual(h!.y + h!.height);
  }
});
