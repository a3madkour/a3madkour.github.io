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

test('clicking the "Serves" label focuses the input and does not rescale', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const oil = page.locator('.recipe-ing li', { hasText: 'olive oil' }).locator('.q');
  await expect(oil).toHaveText('2 tbsp');
  await page.getByText('Serves', { exact: true }).click();
  await expect(oil).toHaveText('2 tbsp');
  await expect(page.locator('.recipe-serves')).toBeFocused();
});

test('steps column fills the width when the layout collapses (RC3.2)', async ({ page }) => {
  await page.setViewportSize({ width: 700, height: 1000 });
  await page.goto('/recipes/example-recipe-one/');
  const rail = await page.locator('.recipe-rail').boundingBox();
  const steps = await page.locator('.recipe-steps-col').boundingBox();
  expect(Math.abs(rail!.width - steps!.width)).toBeLessThan(2);
});
test('the server-rendered quantity is not rewritten at rest', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const tomatoes = page.locator('.recipe-ing li', { hasText: 'canned tomatoes' }).locator('.q');
  await expect(tomatoes).toHaveText('800 g');
  // Scale up, then back to the base: the authored string must return verbatim.
  await page.fill('.recipe-serves', '8');
  await expect(tomatoes).toHaveText('1600 g');
  await page.fill('.recipe-serves', '4');
  await expect(tomatoes).toHaveText('800 g');
  await expect(tomatoes).not.toHaveClass(/recipe-q-changed|changed/);
});

// The test above cannot fail while every fixture quantity happens to survive a
// round-trip through formatQuantity ("800 g" -> "800 g"). This one asserts the
// stronger property directly: at rest the scaler writes no quantity at all, so
// an authored string that the formatter *would* alter (e.g. "0.5 tsp") is safe.
// Node.textContent's setter is only reachable from script — HTML parsing does
// not use it — so a non-empty log means the load-time rewrite came back.
test('the scaler writes no quantity at load, only on a change', async ({ page }) => {
  await page.addInitScript(() => {
    const desc = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent')!;
    (window as unknown as { __qWrites: string[] }).__qWrites = [];
    Object.defineProperty(Node.prototype, 'textContent', {
      ...desc,
      set(this: Node, v: string) {
        const el = this as Element;
        if (el.classList && el.classList.contains('q')) {
          (window as unknown as { __qWrites: string[] }).__qWrites.push(String(v));
        }
        desc.set!.call(this, v);
      },
    });
  });
  await page.goto('/recipes/example-recipe-one/');
  await expect(page.locator('.recipe-ing li').first()).toBeVisible();
  const atRest = await page.evaluate(() => (window as unknown as { __qWrites: string[] }).__qWrites);
  expect(atRest).toEqual([]);

  // A real change still writes.
  await page.fill('.recipe-serves', '8');
  await expect(page.locator('.recipe-ing li', { hasText: 'canned tomatoes' }).locator('.q'))
    .toHaveText('1600 g');
  const afterChange = await page.evaluate(() => (window as unknown as { __qWrites: string[] }).__qWrites);
  expect(afterChange.length).toBeGreaterThan(0);
});

// RC2.6. The two inputs declare independent bounds (servings 1–99, multiplier
// 0.1–20). Before the fix, fromServings clamped only the arithmetic and left
// the field showing the unclamped number, while fromMult ignored min/max
// entirely. Both paths now share one normalize() and write the clamped value
// back into BOTH fields on `change`.
test('both scaler inputs honour their own declared bounds', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const serves = page.locator('.recipe-serves');
  const mult = page.locator('.recipe-mult');

  // Servings above max clamp, and the clamp is written back to the field.
  await serves.fill('100');
  await serves.blur();
  await expect(serves).toHaveValue('80');   // base 4 x mult max 20
  await expect(mult).toHaveValue('20');

  // Multiplier above max clamps too, instead of scaling x1000.
  await mult.fill('1000');
  await mult.blur();
  await expect(mult).toHaveValue('20');
  await expect(serves).toHaveValue('80');

  // Zero / junk falls back to the base rather than leaving the field lying.
  await serves.fill('0');
  await serves.blur();
  await expect(serves).toHaveValue('4');
  await expect(mult).toHaveValue('1');
});
