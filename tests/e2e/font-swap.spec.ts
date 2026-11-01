import { test, expect } from '@playwright/test';

// The web fonts swap in over a fallback, and a fallback with different metrics
// rewraps the page: on Linux DejaVu Sans is wide enough to add rows of filter
// chips above the fold, which failed the mobile Lighthouse gate while this
// suite and every Mac stayed green. So the stacks must name the metric-matched
// faces in §3 of main.css, and the swap itself must not move the page. This
// measures whatever fallback the machine has, so CI measures Linux.

test.use({ viewport: { width: 412, height: 823 }, isMobile: true, hasTouch: true });

test('the font stacks start with the metric-matched fallbacks', async ({ page }) => {
  await page.goto('/garden/');
  const stacks = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement);
    return [style.getPropertyValue('--font-ui'), style.getPropertyValue('--font-body')];
  });
  expect(stacks[0]).toMatch(/^\s*"Inter",\s*"Inter Fallback",\s*"Inter Fallback DejaVu",/);
  expect(stacks[1]).toMatch(/^\s*"Petrona",\s*"Petrona Fallback",/);
});

for (const url of ['/garden/', '/works/', '/works/games/', '/credits/']) {
  test(`the web fonts swap in without moving ${url}`, async ({ page }) => {
    let release = () => {};
    const held = new Promise<void>((resolve) => { release = resolve; });
    await page.route('**/fonts/*.woff2', async (route) => {
      await held;
      await route.continue();
    });
    await page.addInitScript(() => {
      const shifts: number[] = [];
      (window as unknown as { shifts: number[] }).shifts = shifts;
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) shifts.push((entry as unknown as { value: number }).value);
      }).observe({ type: 'layout-shift', buffered: true });
    });
    const total = () => page.evaluate(() =>
      (window as unknown as { shifts: number[] }).shifts.reduce((sum, value) => sum + value, 0));

    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(500);
    const beforeSwap = await total();
    release();
    await expect.poll(() => page.evaluate(() => document.fonts.status)).toBe('loaded');
    await page.waitForTimeout(500);

    // Half the 0.1 Lighthouse calls good: the gate also counts the rest of the page.
    expect((await total()) - beforeSwap).toBeLessThan(0.05);
  });
}
