import { test, expect } from '@playwright/test';

test('homepage renders the site brand', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.site-brand')).toHaveText('a3madkour');
});

test('no-js class is removed after load (R3.6 guard)', async ({ page }) => {
  await page.goto('/');
  // baseof.html ships <html class="no-js">; the inline head script strips it.
  await expect(page.locator('html')).not.toHaveClass(/\bno-js\b/);
});

test('site header stays one row at 860px with all 8 nav items (RC3.1)', async ({ page }) => {
  await page.setViewportSize({ width: 860, height: 900 });
  await page.goto('/');
  const header = page.locator('.site-header');
  const box = await header.boundingBox();
  const navLinks = page.locator('.site-nav a[href]');
  await expect(navLinks).toHaveCount(9); // 8 sections + the RSS icon link
  // One row of nav plus padding; two rows measured 144px before the fix.
  expect(box!.height).toBeLessThan(120);
});
