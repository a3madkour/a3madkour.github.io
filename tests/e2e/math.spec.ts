import { test, expect } from '@playwright/test';

test('essay body inline + display math renders to KaTeX', async ({ page }) => {
  await page.goto('/essays/example-one/');
  // At least one rendered KaTeX node (inline \(...\)).
  await expect(page.locator('.katex').first()).toBeVisible();
  // The \[...\] display formula renders as a display block.
  await expect(page.locator('.katex-display').first()).toBeVisible();
  // MathML is emitted for assistive tech (htmlAndMathml output).
  await expect(page.locator('.katex-mathml, math').first()).toBeAttached();
  // No raw delimiter leaks into the visible body text, outside of the
  // `{{< math >}}` wrapped-form stub — that's still `.math-stub[data-pending]`
  // pending Task 2 (shortcode promotion), out of scope for this render hook.
  const leaksRawDelimiter = await page.locator('main').evaluate((main) => {
    const clone = main.cloneNode(true) as HTMLElement;
    clone.querySelectorAll('.math-stub').forEach((el) => el.remove());
    return /\\\(|\\\[/.test(clone.textContent || '');
  });
  expect(leaksRawDelimiter).toBe(false);
});

test('wrapped {{< math >}} shortcode renders and stub is gone', async ({ page }) => {
  await page.goto('/essays/example-one/');
  // The stub container must no longer exist anywhere.
  await expect(page.locator('.math-stub[data-pending]')).toHaveCount(0);
  // example-one has three math spots; all three render as KaTeX.
  expect(await page.locator('.katex').count()).toBeGreaterThanOrEqual(3);
});

test('math nested in AMS blocks renders on example-five', async ({ page }) => {
  await page.goto('/essays/example-five/');
  // Definition block contains rendered math (was bare \(x_0\)).
  await expect(page.locator('.block-definition .katex').first()).toBeVisible();
  // Proof block contains rendered math (was bare \(\alpha + \beta = \gamma\)).
  await expect(page.locator('.block-proof .katex').first()).toBeVisible();
  // No raw delimiter leaks anywhere in the body.
  await expect(page.locator('main')).not.toContainText('\\(');
});

test('katex stylesheet loads on math pages only', async ({ page }) => {
  await page.goto('/essays/example-one/');
  await expect(page.locator('link[rel="stylesheet"][href*="katex"]')).toHaveCount(1);
  // Rendered math is actually styled: KaTeX applies a KaTeX font-family.
  const ff = await page.locator('.katex').first().evaluate(
    (el) => getComputedStyle(el).fontFamily,
  );
  expect(ff.toLowerCase()).toContain('katex');

  // Non-math page (homepage) must NOT pull the katex stylesheet.
  await page.goto('/');
  await expect(page.locator('link[rel="stylesheet"][href*="katex"]')).toHaveCount(0);
});
