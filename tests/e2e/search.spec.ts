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

test('recipes filter returns visible results, not an empty pane (RC2.1)', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-search-toggle]');
  await page.click('.search-modal-chip[data-section="recipes"]');
  await page.fill('[data-search-input]', 'example');

  const results = page.locator('.search-modal-result');
  await expect(results.first()).toBeVisible({ timeout: 10000 });
  expect(await results.count()).toBeGreaterThan(0);

  // The reported count must match what is actually rendered — the defect was a
  // nonzero status line over an empty pane (SECTION_ORDER dropped the group).
  const status = await page.locator('[data-search-status]').textContent();
  const reported = Number((status || '').match(/^(\d+)/)?.[1]);
  expect(reported).toBe(await results.count());

  // The group heading is labelled, not rendered under a fallback bucket.
  await expect(page.locator('section[data-section="recipes"][role="group"]')).toBeVisible();
});
