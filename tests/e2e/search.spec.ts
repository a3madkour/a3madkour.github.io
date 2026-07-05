import { test, expect } from '@playwright/test';

test('search modal: open, results as options, ArrowDown sets aria-activedescendant (R3.3)', async ({ page }) => {
  await page.goto('/');

  // "/" opens the dialog (handler ignores the key when focus is in an input;
  // on fresh load focus is on <body>).
  await page.keyboard.press('/');
  const dialog = page.locator('dialog.search-modal');
  await expect(dialog).toBeVisible();

  const input = page.locator('[data-search-input]');
  await expect(input).toHaveAttribute('role', 'combobox');
  await input.fill('example');

  // Results container is the listbox; entries are options.
  const results = page.locator('#search-modal-results-list');
  await expect(results).toHaveAttribute('role', 'listbox');
  const options = results.locator('[role="option"]');
  await expect(options.first()).toBeVisible(); // waits for Pagefind fetch + render

  // ArrowDown activates the first option; combobox points at its id.
  await page.keyboard.press('ArrowDown');
  const activeId = await input.getAttribute('aria-activedescendant');
  expect(activeId).toBeTruthy();
  await expect(page.locator(`#${activeId}`)).toHaveAttribute('aria-selected', 'true');
});
