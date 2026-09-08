import { test, expect } from '@playwright/test';

test('recipe renders ingredients + steps and scales', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');

  // Ingredients list is visible; there are 4 steps.
  await expect(page.locator('.recipe-ing li').first()).toBeVisible();
  await expect(page.locator('.recipe-steps li')).toHaveCount(4);

  // Olive-oil row: initial qty is 2 tbsp (base servings = 4).
  const oil = page.locator('.recipe-ing li', { hasText: 'olive oil' }).locator('.q');
  await expect(oil).toHaveText('2 tbsp');

  // Fill servings → 8 (double); expect qty to double to 4 tbsp.
  await page.fill('.recipe-serves', '8');
  await expect(oil).toHaveText('4 tbsp');
});

test('recipe download link points to a JSON Recipe', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const href = await page.locator('.recipe-dl').getAttribute('href');
  // Resolve href (root-relative) against the current page origin.
  const jsonUrl = new URL(href!, page.url()).href;
  const res = await page.request.get(jsonUrl);
  const body = await res.json();
  expect(body['@type']).toBe('Recipe');
});

test('index shows 3 recipe cards', async ({ page }) => {
  await page.goto('/recipes/');
  await expect(page.locator('.recipe-card')).toHaveCount(3);
});

test('an ungrouped ingredient does not inherit the previous group heading', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  // `salt` carries no group; it must not sit inside the "For the sauce" list.
  const saltList = page.locator('.recipe-ing').filter({ hasText: 'salt' });
  await expect(saltList).toHaveCount(1);
  await expect(saltList).not.toContainText('canned tomatoes');
  // Group labels are headings, not list items.
  await expect(page.locator('li.recipe-ing-group')).toHaveCount(0);
  await expect(page.locator('h3.recipe-ing-group')).toHaveCount(2);
});

test('steps column fills the width when the layout collapses (RC3.2)', async ({ page }) => {
  await page.setViewportSize({ width: 700, height: 1000 });
  await page.goto('/recipes/example-recipe-one/');
  const rail = await page.locator('.recipe-rail').boundingBox();
  const steps = await page.locator('.recipe-steps-col').boundingBox();
  expect(Math.abs(rail!.width - steps!.width)).toBeLessThan(2);
});
