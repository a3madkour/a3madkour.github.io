import { test, expect } from '@playwright/test';

// Clipboard read requires an explicit permission grant in Chromium.
test.use({ permissions: ['clipboard-read', 'clipboard-write'] });

test('cite modal: open, ArrowRight moves tabs (R3.4), copy writes clipboard', async ({ page }) => {
  await page.goto('/essays/example-one/');

  await page.locator('.cite-cta').first().click();
  const dialog = page.locator('dialog#cite-modal');
  await expect(dialog).toBeVisible();

  const tabs = page.locator('.cite-modal-tabs [role="tab"]');
  await expect(tabs).toHaveCount(5);
  await expect(tabs.nth(0)).toHaveAttribute('aria-selected', 'true'); // BibTeX default

  // WAI-ARIA tabs: focus active tab, ArrowRight → next tab selected + roving.
  await tabs.nth(0).focus();
  await page.keyboard.press('ArrowRight');
  await expect(tabs.nth(1)).toHaveAttribute('aria-selected', 'true');
  await expect(tabs.nth(0)).toHaveAttribute('aria-selected', 'false');

  // Copy writes the rendered citation text to the clipboard.
  await page.locator('.cite-modal-copy').click();
  const clip = await page.evaluate(() => navigator.clipboard.readText());
  expect(clip.length).toBeGreaterThan(0);
});
