import { test, expect } from '@playwright/test';

test('tag chip narrows the essay grid; "All" restores it', async ({ page }) => {
  await page.goto('/essays/');

  const cards = page.locator('.essay-card');
  const total = await cards.count();
  expect(total).toBeGreaterThan(1);

  // "example" is a primary (always-visible) tag chip on the essays index,
  // present on some-but-not-all essays (several fixtures have empty tags).
  await page.locator('.filter-chip[data-dim="tag"][data-key="example"]').click();

  const visible = page.locator('.essay-card:not([hidden])');
  const shown = await visible.count();
  expect(shown).toBeGreaterThan(0);
  expect(shown).toBeLessThan(total);
  // Every visible card carries the exact tag token (data-tags is space-delimited).
  for (const card of await visible.all()) {
    const tags = (await card.getAttribute('data-tags')) || '';
    expect(tags.split(/\s+/)).toContain('example');
  }

  // "All" clears the tag selection → every card visible again.
  await page.locator('.filter-chip[data-dim="tag"][data-key="all"]').click();
  expect(await page.locator('.essay-card:not([hidden])').count()).toBe(total);
});
