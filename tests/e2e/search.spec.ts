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

  // The group carries its real SECTION_LABEL, not a fallback bucket and not the
  // `undefined` that a missing SECTION_LABEL entry interpolates (RC5.3).
  const group = page.locator('section[data-section="recipes"][role="group"]');
  await expect(group).toHaveAttribute('aria-label', 'Recipes');
  await expect(group.locator('h3')).toHaveText('Recipes');
});

test('the status count equals the rendered result count (RF1.1, RF2.6)', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-search-toggle]');
  // 'example' matches across every section, including the taxonomy pages that
  // were counted but never rendered, and enough of them to exceed the 30-row
  // fetch cap that used to be reported as if it were the total.
  await page.fill('[data-search-input]', 'example');
  await expect(page.locator('.search-modal-result').first()).toBeVisible({ timeout: 10000 });

  const status = (await page.locator('[data-search-status]').textContent()) ?? '';
  const rendered = await page.locator('.search-modal-result').count();

  // The status line must describe what is on screen. Either it states a plain
  // count equal to the rows, or it says "N of M" with N equal to the rows.
  const showing = status.match(/showing (\d+) of (\d+)/i);
  if (showing) {
    expect(Number(showing[1])).toBe(rendered);
    expect(Number(showing[2])).toBeGreaterThanOrEqual(rendered);
  } else {
    const plain = status.match(/(\d+) results?/);
    expect(plain, `status did not state a count: "${status}"`).not.toBeNull();
    expect(Number(plain![1])).toBe(rendered);
  }
});
