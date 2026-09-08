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

test('site header stays one row below 960px with all 8 nav items (RC3.1)', async ({ page }) => {
  // Count only the section destinations. The RSS anchor and the live pill are
  // both `a[href]` inside .site-nav, and the pill is conditional: the
  // streams-poll cron rewrites data/streams-live.yaml every 5 minutes, so a
  // build made while the owner is live carries a 10th link. Excluding the icon
  // links keeps this assertion about the thing that regressed.
  const sectionLinks = page.locator(
    '.site-nav a[href]:not(.icon-button):not(.header-live-pill)',
  );
  const header = page.locator('.site-header');
  const headerHeight = async () => (await header.boundingBox())!.height;

  // The live pill is worth ~80px of row budget, and whether it is in the build
  // depends on the cron-authored data/streams-live.yaml rather than on
  // anything this test controls. So assert each state at a width that state
  // actually reaches, and set the pill explicitly instead of inheriting it.
  const setPill = (live: boolean) =>
    page.evaluate((want) => {
      const nav = document.querySelector('.site-nav')!;
      const existing = nav.querySelector('.header-live-pill');
      if (!want) { existing?.remove(); return; }
      if (existing) return;
      const a = document.createElement('a');
      a.className = 'header-live-pill';
      a.href = 'https://example.invalid/';
      a.innerHTML =
        '<span class="header-live-pill-dot" aria-hidden="true"></span>' +
        '<span class="header-live-pill-label">LIVE</span>';
      nav.appendChild(a);
    }, live);

  // 860px: two rows (144px) before the fix. Holds with the pill either way.
  await page.setViewportSize({ width: 860, height: 900 });
  await page.goto('/');
  await expect(sectionLinks).toHaveCount(8);
  await setPill(true);
  expect(await headerHeight()).toBeLessThan(120);
  await setPill(false);
  expect(await headerHeight()).toBeLessThan(120);

  // 760px: near the floor of the one-row range when not live (first wrap at
  // 745), so the 745-860 band is load-bearing rather than merely claimed.
  // While live the floor is 820, so the pill is removed for this one.
  await page.setViewportSize({ width: 760, height: 900 });
  await page.goto('/');
  await setPill(false);
  await expect(sectionLinks).toHaveCount(8);
  expect(await headerHeight()).toBeLessThan(120);
});
