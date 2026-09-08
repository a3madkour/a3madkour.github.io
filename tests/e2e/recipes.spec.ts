import { test, expect } from '@playwright/test';

test('recipe renders ingredients + steps and scales', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');

  // Ingredients list is visible; there are 4 steps.
  await expect(page.locator('.recipe-ing li').first()).toBeVisible();
  await expect(page.locator('.recipe-steps li')).toHaveCount(4);

  // Olive-oil row: initial qty is 2 tbsp (base servings = 4).
  const oil = page.locator('.recipe-ing li', { hasText: 'olive oil' }).locator('.q');
  await expect(oil).toHaveText('2 tbsp');

  // Fill servings → 8 (double); expect qty to double to 4 tbsp.
  await page.fill('.recipe-serves', '8');
  await expect(oil).toHaveText('4 tbsp');
});

test('recipe download link points to a JSON Recipe', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const href = await page.locator('.recipe-dl').getAttribute('href');
  // Resolve href (root-relative) against the current page origin.
  const jsonUrl = new URL(href!, page.url()).href;
  const res = await page.request.get(jsonUrl);
  const body = await res.json();
  expect(body['@type']).toBe('Recipe');
});

test('index shows 3 recipe cards', async ({ page }) => {
  await page.goto('/recipes/');
  await expect(page.locator('.recipe-card')).toHaveCount(3);
});

test('an ungrouped ingredient does not inherit the previous group heading', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  // `salt` carries no group; it must not sit inside the "For the sauce" list.
  const saltList = page.locator('.recipe-ing').filter({ hasText: 'salt' });
  await expect(saltList).toHaveCount(1);
  await expect(saltList).not.toContainText('canned tomatoes');
  // Group labels are headings, not list items.
  await expect(page.locator('li.recipe-ing-group')).toHaveCount(0);
  await expect(page.locator('h3.recipe-ing-group')).toHaveCount(2);
});

test('clicking the "Serves" label focuses the input and does not rescale', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const oil = page.locator('.recipe-ing li', { hasText: 'olive oil' }).locator('.q');
  await expect(oil).toHaveText('2 tbsp');
  await page.getByText('Serves', { exact: true }).click();
  await expect(oil).toHaveText('2 tbsp');
  await expect(page.locator('.recipe-serves')).toBeFocused();
});

test('steps column fills the width when the layout collapses (RC3.2)', async ({ page }) => {
  await page.setViewportSize({ width: 700, height: 1000 });
  await page.goto('/recipes/example-recipe-one/');
  const rail = await page.locator('.recipe-rail').boundingBox();
  const steps = await page.locator('.recipe-steps-col').boundingBox();
  expect(Math.abs(rail!.width - steps!.width)).toBeLessThan(2);
});
test('the server-rendered quantity is not rewritten at rest', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const tomatoes = page.locator('.recipe-ing li', { hasText: 'canned tomatoes' }).locator('.q');
  await expect(tomatoes).toHaveText('800 g');
  // Scale up, then back to the base: the authored string must return verbatim.
  await page.fill('.recipe-serves', '8');
  await expect(tomatoes).toHaveText('1600 g');
  await page.fill('.recipe-serves', '4');
  await expect(tomatoes).toHaveText('800 g');
  await expect(tomatoes).not.toHaveClass(/recipe-q-changed|changed/);
});

// The test above cannot fail while every fixture quantity happens to survive a
// round-trip through formatQuantity ("800 g" -> "800 g"). This one asserts the
// stronger property directly: at rest the scaler writes no quantity at all, so
// an authored string that the formatter *would* alter (e.g. "0.5 tsp") is safe.
// Node.textContent's setter is only reachable from script — HTML parsing does
// not use it — so a non-empty log means the load-time rewrite came back.
test('the scaler writes no quantity at load, only on a change', async ({ page }) => {
  await page.addInitScript(() => {
    const desc = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent')!;
    (window as unknown as { __qWrites: string[] }).__qWrites = [];
    Object.defineProperty(Node.prototype, 'textContent', {
      ...desc,
      set(this: Node, v: string) {
        const el = this as Element;
        if (el.classList && el.classList.contains('q')) {
          (window as unknown as { __qWrites: string[] }).__qWrites.push(String(v));
        }
        desc.set!.call(this, v);
      },
    });
  });
  await page.goto('/recipes/example-recipe-one/');
  await expect(page.locator('.recipe-ing li').first()).toBeVisible();
  const atRest = await page.evaluate(() => (window as unknown as { __qWrites: string[] }).__qWrites);
  expect(atRest).toEqual([]);

  // A real change still writes.
  await page.fill('.recipe-serves', '8');
  await expect(page.locator('.recipe-ing li', { hasText: 'canned tomatoes' }).locator('.q'))
    .toHaveText('1600 g');
  const afterChange = await page.evaluate(() => (window as unknown as { __qWrites: string[] }).__qWrites);
  expect(afterChange.length).toBeGreaterThan(0);
});
test('a recipe with no times renders no time chrome anywhere', async ({ page }) => {
  // example-recipe-three is the minimal fixture: REQUIRED fields only.
  await page.goto('/recipes/example-recipe-three/');
  await expect(page.locator('.recipe-meta')).not.toContainText('Total');
  await expect(page.locator('.recipe-dl')).toBeVisible();

  await page.goto('/recipes/');
  const minimal = page.locator('.recipe-card[href="/recipes/example-recipe-three/"]');
  // Assert the parent exists first: toHaveCount(0) on a child of a locator that
  // matches nothing passes trivially, so without this the next line has no teeth.
  await expect(minimal).toHaveCount(1);
  await expect(minimal.locator('.recipe-card-time')).toHaveCount(0);
});
test('every scaler control shows a focus ring (RC3.3)', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  for (const sel of ['.recipe-minus', '.recipe-serves', '.recipe-plus', '.recipe-mult']) {
    await page.locator(sel).focus();
    const outline = await page.locator(sel).evaluate((el) => {
      const s = getComputedStyle(el);
      return { width: s.outlineWidth, style: s.outlineStyle };
    });
    expect(outline.style, `${sel} outline-style`).not.toBe('none');
    expect(parseFloat(outline.width), `${sel} outline-width`).toBeGreaterThan(0);
  }
  // The stepper wrapper must not clip its children's rings.
  const overflow = await page.locator('.recipe-stp')
    .evaluate((el) => getComputedStyle(el).overflow);
  expect(overflow).not.toBe('hidden');
});
// RC2.6. The two inputs declare independent bounds (servings 1–99, multiplier
// 0.1–20). Before the fix, fromServings clamped only the arithmetic and left
// the field showing the unclamped number, while fromMult ignored min/max
// entirely. Both paths now share one normalize() and write the clamped value
// back into BOTH fields on `change`.
test('both scaler inputs honour their own declared bounds', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const serves = page.locator('.recipe-serves');
  const mult = page.locator('.recipe-mult');

  // Servings above max clamp, and the clamp is written back to the field.
  await serves.fill('100');
  await serves.blur();
  await expect(serves).toHaveValue('80');   // base 4 x mult max 20
  await expect(mult).toHaveValue('20');

  // Multiplier above max clamps too, instead of scaling x1000.
  await mult.fill('1000');
  await mult.blur();
  await expect(mult).toHaveValue('20');
  await expect(serves).toHaveValue('80');

  // Zero / junk falls back to the base rather than leaving the field lying.
  await serves.fill('0');
  await serves.blur();
  await expect(serves).toHaveValue('4');
  await expect(mult).toHaveValue('1');
});
test('index heading order has no skipped level (axe heading-order)', async ({ page }) => {
  await page.goto('/recipes/');
  // Anchor the cards' existence first: a heading sequence of just [h1] passes
  // the no-skip loop trivially, so without this the assertion has no teeth if
  // the card grid ever renders empty.
  expect(await page.locator('.recipe-card').count()).toBeGreaterThan(0);
  const levels = await page.locator('h1, h2, h3, h4, h5, h6')
    .evaluateAll((els) => els.map((e) => Number(e.tagName.slice(1))));
  expect(levels[0]).toBe(1);
  for (let i = 1; i < levels.length; i++) {
    expect(levels[i] - levels[i - 1]).toBeLessThanOrEqual(1);
  }
});
// RC3.4 + RC4.8. Burgundy text was the only signal a quantity had been
// rescaled: colour-only meaning, and silent to a screen reader. Two channels
// now: a dotted underline on each moved .q, and a role=status line stating the
// ratio and the resulting yield.
test('a rescaled quantity signals in two channels (RC3.4)', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const oil = page.locator('.recipe-ing li', { hasText: 'olive oil' }).locator('.q');
  const status = page.locator('.recipe-scale-status');

  // At rest the region exists and is empty — it must NOT be display:none, or it
  // is absent from the a11y tree until the moment it gains text, which is the
  // pattern screen readers routinely fail to announce.
  await expect(status).toHaveAttribute('role', 'status');
  await expect(status).toHaveText('');
  const rest = await status.evaluate((el) => {
    const s = getComputedStyle(el);
    return { display: s.display, height: el.getBoundingClientRect().height, border: s.borderTopStyle };
  });
  expect(rest.display).not.toBe('none');
  expect(rest.height).toBe(0);          // :empty collapses the visual footprint
  expect(rest.border).toBe('none');
  // The .q underline is likewise absent until a value actually moves.
  expect(await oil.evaluate((el) => getComputedStyle(el).borderBottomStyle)).toBe('none');

  // fill() dispatches `input` only; `change` is the commit point, so blur.
  await page.fill('.recipe-serves', '6');
  await expect(oil).toHaveClass(/recipe-q-changed/);   // channel 1 tracks input
  await page.locator('.recipe-serves').blur();

  // Channel 2: announced, and says by how much.
  await expect(status).toBeVisible();
  await expect(status).toContainText('1.5');
  await expect(status).toContainText('6');

  // Channel 1 pinned to the mechanism actually implemented — a dotted bottom
  // border in currentColor. A weaker regex would pass on an inherited
  // underline the rescale had nothing to do with.
  const rule = await oil.evaluate((el) => {
    const s = getComputedStyle(el);
    return { style: s.borderBottomStyle, width: parseFloat(s.borderBottomWidth), color: s.borderBottomColor, ink: s.color };
  });
  expect(rule.style).toBe('dotted');
  expect(rule.width).toBeGreaterThan(0);
  expect(rule.color).toBe(rule.ink);    // currentColor, so it tracks the theme

  // Back to base: the text empties, but the region stays in the document.
  await page.fill('.recipe-serves', '4');
  await page.locator('.recipe-serves').blur();
  await expect(status).toHaveText('');
  await expect(status).toBeAttached();
  expect(await status.evaluate((el) => getComputedStyle(el).display)).not.toBe('none');
  expect(await oil.evaluate((el) => getComputedStyle(el).borderBottomStyle)).toBe('none');
});

// RC4.8. The blocking half: a live region inserted into the a11y tree in the
// same task that populates it is unreliably announced. Assert via CDP that the
// region is already there, un-ignored, before any interaction.
test('the scale status is a live region present from load (RC4.8)', async ({ page }) => {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Accessibility.enable');
  await page.goto('/recipes/example-recipe-one/');

  const liveRegions = async () => {
    const { nodes } = (await cdp.send('Accessibility.getFullAXTree')) as {
      nodes: { role?: { value?: string }; ignored?: boolean;
               properties?: { name: string; value: { value?: unknown } }[] }[];
    };
    return nodes.filter((n) => !n.ignored && (n.properties || [])
      .some((p) => p.name === 'live' && p.value.value && p.value.value !== 'off'));
  };

  const atLoad = await liveRegions();
  expect(atLoad.length, 'live region must exist before any change').toBe(1);
  expect(atLoad[0].role?.value).toBe('status');

  await page.fill('.recipe-serves', '6');
  await page.locator('.recipe-serves').blur();
  await expect(page.locator('.recipe-scale-status')).toContainText('1.5');
  const afterChange = await liveRegions();
  expect(afterChange.length).toBe(1);
  expect(afterChange[0].role?.value).toBe('status');
});

// RC4.8. The announcement follows N10's commit discipline (`change`, where the
// clamped value is written back) and reads as English at a yield of 1.
test('the scale status states the committed yield, pluralised (RC4.8)', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const serves = page.locator('.recipe-serves');
  const status = page.locator('.recipe-scale-status');

  // A clamped value is announced as clamped, not as the number typed.
  await serves.fill('100');
  await serves.blur();
  await expect(status).toHaveText('Scaled ×20 — amounts shown for 80 servings');

  // Singular at a yield of exactly 1 — not "1 servings".
  await serves.fill('1');
  await serves.blur();
  await expect(status).toHaveText('Scaled ×0.25 — amounts shown for 1 serving');

  // Typing alone (input, no change) must not re-announce per keystroke: the
  // region holds the last committed sentence until the value is committed.
  await serves.fill('12');
  await expect(status).toHaveText('Scaled ×0.25 — amounts shown for 1 serving');
  await serves.blur();
  await expect(status).toHaveText('Scaled ×3 — amounts shown for 12 servings');

  // The unit comes from data-yield-unit, and is singularised generically.
  await page.goto('/recipes/example-recipe-two/');
  const s2 = page.locator('.recipe-serves');
  await s2.fill('12');
  await s2.blur();
  await expect(page.locator('.recipe-scale-status'))
    .toHaveText('Scaled ×1.5 — amounts shown for 12 cookies');
  await s2.fill('1');
  await s2.blur();
  await expect(page.locator('.recipe-scale-status'))
    .toHaveText('Scaled ×0.13 — amounts shown for 1 cookie');
});

// RC4.5. The scaler is JS-only chrome: with scripting off the stepper and the
// multiplier are dead controls, so `rail.html` ships a <noscript><style> that
// removes them. Nothing else in the suite runs with JS disabled, so this is the
// only assertion that the fallback exists at all — and it must also prove the
// ingredients survive, or "hidden" would be indistinguishable from a page that
// failed to render. test.use() is what inherits baseURL; browser.newContext()
// would not.
test.describe('scripting disabled', () => {
  test.use({ javaScriptEnabled: false });

  test('the scaler is hidden rather than left as inert chrome (RC4.5)', async ({ page }) => {
    await page.goto('/recipes/example-recipe-one/');
    await expect(page.locator('.recipe-scaler')).toBeHidden();
    await expect(page.locator('.recipe-scale-status')).toBeHidden();
    // The content the scaler decorates is still fully served.
    await expect(page.locator('.recipe-ing li').first()).toBeVisible();
    await expect(page.locator('.recipe-steps li')).toHaveCount(4);
    await expect(page.locator('.recipe-ing li', { hasText: 'olive oil' }).locator('.q'))
      .toHaveText('2 tbsp');
  });
});

// RC1.2 class. `cuisine` and `category` are both optional; the kicker is the
// element that concatenates them. The minimal fixture declares neither, so the
// wrapper must not render at all — an empty <div> with a separator dot in it is
// the failure this guards. Asserted against both fixtures so a template change
// that dropped the kicker everywhere cannot pass.
test('the kicker renders only when cuisine or category is present', async ({ page }) => {
  await page.goto('/recipes/example-recipe-three/');
  await expect(page.locator('.recipe-kicker')).toHaveCount(0);

  await page.goto('/recipes/example-recipe-one/');
  const kicker = page.locator('.recipe-kicker');
  await expect(kicker).toHaveCount(1);
  await expect(kicker).not.toHaveText('');
  await expect(kicker).toBeVisible();
});
