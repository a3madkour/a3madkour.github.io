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
