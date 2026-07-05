import { test, expect } from '@playwright/test';

test('theme toggle cycles system → light → dark → system', async ({ page }) => {
  await page.goto('/');
  const html = page.locator('html');
  const toggle = page.locator('[data-theme-toggle]');
  const stored = () => page.evaluate(() => localStorage.getItem('theme-pref'));

  // Fresh load = system: no data-theme attribute, no stored pref.
  expect(await html.getAttribute('data-theme')).toBeNull();
  expect(await stored()).toBeNull();

  // system → light
  await toggle.click();
  await expect(html).toHaveAttribute('data-theme', 'light');
  expect(await stored()).toBe('light');

  // light → dark
  await toggle.click();
  await expect(html).toHaveAttribute('data-theme', 'dark');
  expect(await stored()).toBe('dark');

  // dark → system (attribute removed, storage cleared)
  await toggle.click();
  expect(await html.getAttribute('data-theme')).toBeNull();
  expect(await stored()).toBeNull();
});
