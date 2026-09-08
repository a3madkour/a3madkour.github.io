# Recipe Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close all 29 rows of the post-review recipe remediation so the `recipes` branch can merge to `main` with no known defects.

**Architecture:** Fixes land as one commit per task on the `recipes` branch, tier-ordered (blockers → wrong output → layout/a11y → hygiene → guards). Absence of an optional field is guarded in Hugo templates; a malformed value is rejected by the Python linters. The scaler becomes server-authoritative at rest. Three new guards (a minimal content fixture, `--color-tile` contrast pairings, a search E2E) target the *classes* these defects came from.

**Tech Stack:** Hugo extended 0.162.1 (Go templates, goldmark), hand-rolled CSS (`assets/css/main.css`, §51 = recipes), esbuild multi-entry JS via `js.Build`, stdlib-only Python 3 linters (`unittest`), Playwright (`@playwright/test` 1.61.1), `node --test`.

**Spec:** `docs/superpowers/specs/2026-09-07-recipe-audit-remediation-design.md`

## Global Constraints

- **Work in `/Users/a3madkour/Sync/Workspace/a3madkour.github.io-recipes` on branch `recipes`.** This is a git worktree; `main` is checked out elsewhere. Never push.
- **Python is stdlib-only.** No third-party imports in `tools/`.
- **No npm for the shipped site.** `package.json` is devDependencies-only and must stay that way.
- **Dark tokens are duplicated.** `:root[data-theme="dark"]` and the `@media (prefers-color-scheme: dark) :root:not([data-theme])` block carry identical values; `tools/check_dark_tokens.py` fails if they diverge. Any token change edits **both** blocks.
- **Breakpoints are a fixed scale:** `480 · 600 · 720 · 960 · 1100 · 1280`. `tools/check_breakpoints.py` rejects any other `@media` width without an allowlist entry.
- **Spacing uses `--space-*` tokens.** `tools/check_spacing_tokens.py` rejects raw rem values in spacing properties.
- **Fixture content is obviously dummy** — lorem ipsum / "Example N". Never authored prose.
- **Never color-only meaning**; WCAG 2.1 AAA body / AA accents.
- **Full local gate:** `bash tools/ci-local.sh` must exit 0 (LHCI is expected to fail locally — no system Chrome — that step alone may be disregarded).

---

### Task 1: Node ESM declaration + CI runtime parity (RC1.1)

**Files:**
- Modify: `package.json`
- Modify: `.github/workflows/hugo.yaml:212-213`
- Modify: `tools/ci-local.sh:170`

**Interfaces:**
- Consumes: nothing.
- Produces: `tests/unit/*.test.mjs` runs correctly under Node 20 module resolution. No API surface.

- [ ] **Step 1: Reproduce the CI failure locally**

Run: `node --no-experimental-detect-module --test tests/unit/*.test.mjs`

Expected: FAIL — `SyntaxError: Named export 'formatQuantity' not found. The requested module '../../assets/js/recipe-scale.js' is a CommonJS module`. This flag forces the Node 20 semantics that CI actually uses; without it your local Node auto-detects ESM and hides the bug.

- [ ] **Step 2: Declare the package as ESM**

In `package.json`, add `"type": "module"` and an `engines` floor. The file becomes:

```json
{
  "name": "a3madkour-site-e2e",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "description": "Dev-only Playwright E2E harness. NOT shipped — see CLAUDE.md 'No npm' note. devDependencies only; adds zero bytes to the built site.",
  "engines": {
    "node": ">=20"
  },
  "scripts": {
    "test:e2e": "playwright test"
  },
  "devDependencies": {
    "@playwright/test": "1.61.1"
  }
}
```

- [ ] **Step 3: Verify the repro now passes**

Run: `node --no-experimental-detect-module --test tests/unit/*.test.mjs`
Expected: PASS, `# pass 3`, `# fail 0`

- [ ] **Step 4: Make CI exercise Node-20 semantics permanently**

In `.github/workflows/hugo.yaml`, change the `JS unit tests` step so the flag is always on — this is the guard, not the fix:

```yaml
      - name: JS unit tests
        run: node --no-experimental-detect-module --test tests/unit/*.test.mjs
```

In `tools/ci-local.sh`, change line 170 identically:

```bash
  node --no-experimental-detect-module --test tests/unit/*.test.mjs
```

- [ ] **Step 5: Commit**

```bash
git add package.json .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "fix(recipes): declare package ESM so node --test passes on CI's Node 20

RC1.1. Without \"type\": \"module\" Node 20 classifies bare .js as CommonJS;
ESM auto-detection only defaults on at 22.7, so the unit step passed on a
local Node 26 and would have failed the deploy gate. Both CI and ci-local.sh
now pass --no-experimental-detect-module so Node-20 module semantics are
exercised regardless of local runtime."
```

---

### Task 2: Recipe fixtures linter — value-shape hardening (RC1.3, RC4.7)

**Files:**
- Modify: `tools/check_recipes_fixtures.py`
- Test: `tools/test_check_recipes_fixtures.py`

**Interfaces:**
- Consumes: `check_fixtures.parse_frontmatter(text) -> dict | None`, and `check_fixtures.parse_scalar`, which maps `"010"` → `int 10` (`re.fullmatch(r"-?\d+", s)`), destroying the padding. The padded form is therefore only detectable in the **raw** frontmatter text, not the parsed dict.
- Produces: `mod.run(repo_root) -> (int, list[str])` — unchanged signature. New rejections: zero-padded numerics, non-decimal numeric strings, `qty: 0`, and `"null"` standing in for a required string.

- [ ] **Step 1: Write the failing tests**

Append to the `T` class in `tools/test_check_recipes_fixtures.py`:

```python
    def test_zero_padded_minutes_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("servings: 4", "servings: 4\nprep_minutes: 010"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("zero-padded" in e for e in errs), errs)

    def test_zero_padded_servings_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("servings: 4", "servings: 08"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("zero-padded" in e for e in errs), errs)

    def test_zero_padded_qty_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("{ qty: 2, unit: tbsp", "{ qty: 08, unit: tbsp"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("zero-padded" in e for e in errs), errs)

    def test_underscore_and_inf_rejected(self):
        for bad in ("1_0", "inf", "nan"):
            with self.subTest(bad=bad):
                self.repo.write("content/recipes/ex/index.md",
                                VALID.replace("servings: 4", f"servings: {bad}"))
                rc, errs = mod.run(self.repo.root)
                self.assertEqual(rc, 1, f"{bad} should be rejected")

    def test_zero_qty_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("{ qty: 2, unit: tbsp", "{ qty: 0, unit: tbsp"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("qty" in e for e in errs), errs)

    def test_explicit_null_item_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('item: "olive oil"', "item: null"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing 'item'" in e for e in errs), errs)

    def test_explicit_null_source_name_rejected(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('{ name: "Example", url: "https://example.com/x" }',
                                      '{ name: null, url: "https://example.com/x" }'))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing 'name'" in e for e in errs), errs)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tools.test_check_recipes_fixtures -v`
Expected: 7 failures — every new test reports `rc == 0` where 1 was expected.

- [ ] **Step 3: Implement the hardening**

In `tools/check_recipes_fixtures.py`, replace the `_is_num` function with the block below and add the two module-level regexes above it:

```python
# A YAML 1.1/1.2 plain scalar Hugo will read as a number. Deliberately narrower
# than float(): Python accepts "1_0", "inf", and "nan", none of which Hugo does.
_NUM_RE = re.compile(r"^-?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?$")

# Zero-padded integers are the repo's documented Hugo octal gotcha: `010` is
# parsed by Hugo as 8, and `08` is invalid octal so Hugo keeps it a string and
# the next arithmetic op aborts the build. parse_scalar() converts "010" -> 10,
# so the padding survives only in the raw frontmatter text.
_PADDED_TOP_RE = re.compile(
    r"^(servings|prep_minutes|cook_minutes|total_minutes):[ \t]*-?0\d", re.M)
_PADDED_QTY_RE = re.compile(r"qty:[ \t]*-?0\d")


def _absent(v) -> bool:
    """True when a value is missing, or is the literal string 'null'.

    parse_scalar() has no null handling, so an explicit `item: null` arrives as
    the *truthy* string 'null' and silently passes a `str(...).strip()` check.
    """
    return v is None or (isinstance(v, str) and v.strip() == "null")


def _is_num(v) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, str):
        return bool(_NUM_RE.match(v.strip()))
    return False
```

Then change `lint_file` to read the raw text once, scan it, and use `_absent`. Replace the opening of `lint_file` and the three checks that follow:

```python
def lint_file(md: Path) -> list[str]:
    errs: list[str] = []
    raw = md.read_text()
    fm = parse_frontmatter(raw)
    if fm is None:
        return [f"{md}: no frontmatter"]

    for m in _PADDED_TOP_RE.finditer(raw):
        errs.append(f"{md}: {m.group(1)} is zero-padded — Hugo parses it as octal")
    if _PADDED_QTY_RE.search(raw):
        errs.append(f"{md}: an ingredient qty is zero-padded — Hugo parses it as octal")
```

In the ingredients loop, replace the `item` and `qty` checks with:

```python
                if _absent(ing.get("item")) or not str(ing.get("item", "")).strip():
                    errs.append(f"{md}: ingredients[{i}] missing 'item'")
                q = ing.get("qty")
                if not _absent(q) and not (_is_num(q) and float(str(q)) > 0):
                    errs.append(f"{md}: ingredients[{i}] qty must be a positive number or null")
```

In the sources loop, replace the `name` check with:

```python
                if _absent(s.get("name")) or not str(s.get("name", "")).strip():
                    errs.append(f"{md}: sources[{i}] missing 'name'")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tools.test_check_recipes_fixtures -v`
Expected: PASS, all tests OK.

Run: `python3 tools/check_recipes_fixtures.py`
Expected: `check_recipes_fixtures: OK` — the three shipped fixtures still validate.

- [ ] **Step 5: Commit**

```bash
git add tools/check_recipes_fixtures.py tools/test_check_recipes_fixtures.py
git commit -m "fix(tools): recipe linter rejects octal-padded, non-decimal, and 'null' values

RC1.3 + RC4.7. parse_scalar maps '010' to int 10, so zero-padding is only
visible in the raw frontmatter — scanned there. _is_num no longer accepts
Python-only forms (1_0, inf, nan). Explicit nulls arrive as the truthy string
'null', which made the item/name checks unreachable; _absent() handles it the
way the qty check already did. qty: 0 is now rejected outright."
```

---

### Task 3: Minimal fixture + optional-field template guards (RC5.1, RC1.2, RC2.7)

**Files:**
- Create: `content/recipes/example-recipe-three/index.md`
- Modify: `layouts/partials/recipes/card.html:1,5,10`
- Modify: `layouts/recipes/single.html:2,12-19`
- Modify: `layouts/partials/recipes/schema-recipe.html:7,28-40`
- Modify: `tests/e2e/recipes.spec.ts:31`

**Interfaces:**
- Consumes: the linter contract from Task 2 (REQUIRED = `title, date, lastmod, draft, summary, servings, sources, ingredients, steps`).
- Produces: a build-exercised minimal recipe. Later tasks that touch `card.html`, `single.html`, or `schema-recipe.html` inherit a fixture that will fail the build if they reintroduce an unguarded optional field.

- [ ] **Step 1: Write the failing fixture**

Create `content/recipes/example-recipe-three/index.md` — only REQUIRED fields, one url-less source, a null qty, no tags, no times, no cuisine, no category:

```markdown
---
title: "Example Recipe Three"
date: 2026-07-08
lastmod: 2026-07-08
draft: false
summary: "Lorem ipsum with nothing optional — the minimal legal recipe."
servings: 2
sources:
  - { name: "Example Book of Dummies" }
ingredients:
  - { qty: 1, unit: null, item: "lorem" }
  - { qty: null, unit: null, item: "ipsum", note: "to taste" }
steps:
  - "Combine the lorem and the ipsum."
  - "Serve."
---

An obviously-dummy headnote for the minimal case.
```

- [ ] **Step 2: Run the build to verify it fails**

Run: `hugo --gc --minify --environment production`
Expected: FAIL — `error calling delimit: can't iterate over <nil>` from `card.html:5`, because this recipe has no `tags`.

- [ ] **Step 3: Guard tags on the card**

In `layouts/partials/recipes/card.html`, line 5, adopt the repo-wide idiom:

```html
   data-tags="{{ delimit (.Params.tags | default slice) " " }}">
```

- [ ] **Step 4: Re-run the build; confirm it now completes but renders "0 min"**

Run: `hugo --gc --minify --environment production`
Expected: PASS.

Run: `grep -o 'Total 0&nbsp;min' public/recipes/example-recipe-three/index.html`
Expected: a match — this is RC2.7, still unfixed.

Run: `python3 -c "import json;d=json.load(open('public/recipes/example-recipe-three/index.json'));print(d['prepTime'],d['cookTime'],d['totalTime'])"`
Expected: `PT0M PT0M PT0M`

- [ ] **Step 5: Guard the time meta line on the single page**

In `layouts/recipes/single.html`, replace line 2 and the `.recipe-meta` block (lines 12–19) with:

```html
{{ $total := or .Params.total_minutes (add (default 0 .Params.prep_minutes) (default 0 .Params.cook_minutes)) }}
{{ $hasTime := or .Params.prep_minutes .Params.cook_minutes .Params.total_minutes }}
```

```html
    <div class="recipe-meta">
      {{ with .Params.prep_minutes }}Prep {{ . }}&nbsp;min · {{ end }}
      {{ with .Params.cook_minutes }}Cook {{ . }}&nbsp;min · {{ end }}
      {{ if $hasTime }}Total {{ $total }}&nbsp;min{{ end }}
      {{ with .OutputFormats.Get "RECIPE" }}
        {{ if $hasTime }} · {{ end }}<a class="recipe-dl" href="{{ .RelPermalink }}" download><span aria-hidden="true">⬇</span> Download recipe (.json)</a>
      {{ end }}
    </div>
```

- [ ] **Step 6: Guard the time badge on the card**

In `layouts/partials/recipes/card.html`, replace line 1 and line 10:

```html
{{- $total := or .Params.total_minutes (add (default 0 .Params.prep_minutes) (default 0 .Params.cook_minutes)) -}}
{{- $hasTime := or .Params.total_minutes .Params.prep_minutes .Params.cook_minutes -}}
```

```html
    {{ if $hasTime }}<span class="recipe-card-time"><span aria-hidden="true">⏱</span> {{ $total }}&nbsp;min</span>{{ end }}
```

- [ ] **Step 7: Omit the duration keys from JSON-LD when absent**

In `layouts/partials/recipes/schema-recipe.html`, remove the three `*Time` entries from the `$obj` literal (lines 34–36) so the dict becomes:

```go-html-template
{{- $obj := dict
    "@context" "https://schema.org"
    "@type" "Recipe"
    "name" $p.Title
    "datePublished" ($p.Date.Format "2006-01-02")
    "recipeYield" (printf "%v %s" $p.Params.servings (default "servings" $p.Params.yield_unit))
    "recipeIngredient" $ingText
    "recipeInstructions" $steps
    "x-ingredients" $p.Params.ingredients
-}}
```

Then add the conditional merges immediately after that literal, before the existing `with $p.Params.summary` line:

```go-html-template
{{- with $p.Params.prep_minutes }}{{- $obj = merge $obj (dict "prepTime" (printf "PT%dM" (int .))) -}}{{- end -}}
{{- with $p.Params.cook_minutes }}{{- $obj = merge $obj (dict "cookTime" (printf "PT%dM" (int .))) -}}{{- end -}}
{{- if or $p.Params.total_minutes (and $p.Params.prep_minutes $p.Params.cook_minutes) -}}
  {{- $obj = merge $obj (dict "totalTime" (printf "PT%dM" (int $total))) -}}
{{- end -}}
```

- [ ] **Step 8: Update the index card count**

`tests/e2e/recipes.spec.ts:31` asserts 3 cards; there are now 4. Change it:

```typescript
test('index shows 4 recipe cards', async ({ page }) => {
  await page.goto('/recipes/');
  await expect(page.locator('.recipe-card')).toHaveCount(4);
});
```

- [ ] **Step 9: Verify all three defects are closed**

Run: `hugo --gc --minify --environment production`
Expected: PASS.

Run: `grep -c 'Total 0&nbsp;min' public/recipes/example-recipe-three/index.html || echo "absent"`
Expected: `absent`

Run: `python3 -c "import json;d=json.load(open('public/recipes/example-recipe-three/index.json'));print(sorted(k for k in d if k.endswith('Time')))"`
Expected: `[]`

Run: `python3 -c "import json;d=json.load(open('public/recipes/example-recipe-one/index.json'));print(d['prepTime'],d['cookTime'],d['totalTime'])"`
Expected: `PT10M PT25M PT35M` — the maximal fixture is unchanged.

Run: `python3 tools/check_recipes_fixtures.py && python3 tools/check_recipes_links.py`
Expected: both `OK`.

- [ ] **Step 10: Commit**

```bash
git add content/recipes/example-recipe-three layouts/partials/recipes/card.html \
        layouts/recipes/single.html layouts/partials/recipes/schema-recipe.html \
        tests/e2e/recipes.spec.ts
git commit -m "fix(recipes): guard optional fields; add minimal build-exercised fixture

RC5.1 + RC1.2 + RC2.7. Every shipped fixture was maximal, so no optional-field
path was exercised by the build. example-recipe-three carries only the REQUIRED
set — no tags, no times, a url-less source, a null qty — which immediately
reproduced the tagless delimit build abort and the PT0M/'Total 0 min' output
that voids the Google rich result. Times now render only when present and the
JSON-LD omits the duration keys entirely rather than emitting zero-length ones."
```

---

### Task 4: Index card heading order (RC1.4)

**Files:**
- Modify: `layouts/partials/recipes/card.html:7`
- Modify: `assets/css/main.css:6055`
- Test: `tests/e2e/recipes.spec.ts`

**Interfaces:**
- Consumes: nothing.
- Produces: `/recipes/` heading sequence `[h1, h2, h2, h2, h2]`, matching `/garden/` and `/streams/`.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/recipes.spec.ts`:

```typescript
test('index heading order has no skipped level (axe heading-order)', async ({ page }) => {
  await page.goto('/recipes/');
  const levels = await page.locator('h1, h2, h3, h4, h5, h6')
    .evaluateAll((els) => els.map((e) => Number(e.tagName.slice(1))));
  expect(levels[0]).toBe(1);
  for (let i = 1; i < levels.length; i++) {
    expect(levels[i] - levels[i - 1]).toBeLessThanOrEqual(1);
  }
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx playwright test tests/e2e/recipes.spec.ts -g "heading order"`
Expected: FAIL — the first card jumps from level 1 to level 3.

- [ ] **Step 3: Promote the card heading**

In `layouts/partials/recipes/card.html`, line 7:

```html
  <h2>{{ .Title }}</h2>
```

In `assets/css/main.css`, line 6055, change the selector to match:

```css
.recipe-card h2 {
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `hugo --gc --minify --environment production && npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS, all recipe specs green.

Run: `python3 tools/check_css_refs.py`
Expected: `OK` — no orphaned selector left behind.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/recipes/card.html assets/css/main.css tests/e2e/recipes.spec.ts
git commit -m "fix(recipes): index cards use h2, not h3, under the page h1

RC1.4. /recipes/ rendered [h1,h3,h3,h3] while every other card partial emits
h2, tripping axe heading-order — and gen_lhci_urls.py now puts /recipes/
behind an accessibility minScore 0.9 assertion that blocks deploy."
```

---

### Task 5: Register recipes in the search modal (RC2.1, RC5.3)

**Files:**
- Modify: `assets/js/search.js:6-16`
- Test: `tests/e2e/search.spec.ts`

**Interfaces:**
- Consumes: `data-pagefind-filter="section:recipes"` already emitted by `layouts/recipes/{single,list}.html`, and the `data-section="recipes"` chip already present in `search-modal.html:33`.
- Produces: `SECTION_ORDER` includes `'recipes'`; the renderer groups and displays recipe hits.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/search.spec.ts`:

```typescript
test('recipes filter returns visible results, not an empty pane (RC2.1)', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-search-toggle]');
  await page.click('.search-modal-chip[data-section="recipes"]');
  await page.fill('[data-search-input]', 'example');
  const results = page.locator('.search-modal-result');
  await expect(results.first()).toBeVisible({ timeout: 10000 });
  const count = await results.count();
  expect(count).toBeGreaterThan(0);
});
```

If the input selector differs, read `layouts/partials/search-modal.html` and use the attribute it actually carries — do not guess.

- [ ] **Step 2: Run it to verify it fails**

Run: `npx playwright test tests/e2e/search.spec.ts -g "recipes filter"`
Expected: FAIL — the status line reports a nonzero result count while no `.search-modal-result` element exists, because `SECTION_ORDER.filter(...)` drops the whole `recipes` group.

- [ ] **Step 3: Register the section**

In `assets/js/search.js`, lines 6–16:

```javascript
const SECTION_ORDER = ['essays', 'garden', 'research', 'works', 'library', 'streams', 'recipes', 'home', 'about'];
const SECTION_LABEL = {
  essays:   'Essays',
  garden:   'Garden',
  research: 'Research',
  works:    'Works',
  library:  'Library',
  streams:  'Streams',
  recipes:  'Recipes',
  home:     'Home',
  about:    'About',
};
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `hugo --gc --minify --environment production`, rebuild the Pagefind index as `tools/ci-local.sh` does, then `npx playwright test tests/e2e/search.spec.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add assets/js/search.js tests/e2e/search.spec.ts
git commit -m "fix(search): register the recipes section so its hits render

RC2.1 + RC5.3. The chip, the Pagefind filter, and the meta span all shipped;
SECTION_ORDER/SECTION_LABEL did not, so the renderer dropped every recipe hit
while the total still counted it — a nonzero result count over an empty pane,
and silent inflation of the All count. The new E2E asserts a filter that
reports results actually shows them."
```

---

### Task 6: Ingredient grouping — real headings, closed groups (RC2.2)

**Files:**
- Modify: `layouts/partials/recipes/rail.html:16-29`
- Modify: `assets/css/main.css` (`.recipe-ing-group` block, ~line 5895)
- Test: `tests/e2e/recipes.spec.ts`

**Interfaces:**
- Consumes: `.Params.ingredients` entries with an optional `group` key.
- Produces: DOM contract for the scaler is **preserved** — `.recipe-ing li` still selects exactly the ingredient rows (group headings are now `<h3>`, outside any `<ul>`), and `data-i` still equals the ingredient's index in `.Params.ingredients`. Task 9 and Task 10 depend on both facts.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/recipes.spec.ts`:

```typescript
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx playwright test tests/e2e/recipes.spec.ts -g "ungrouped ingredient"`
Expected: FAIL — one `<ul>` holds every row, `li.recipe-ing-group` count is 2, `h3.recipe-ing-group` count is 0.

- [ ] **Step 3: Emit one list per run of ingredients**

In `layouts/partials/recipes/rail.html`, replace lines 16–29 with the block below. It tracks the current group in a scratch and opens/closes a `<ul>` at every transition, so document order is preserved exactly — an ungrouped run after a grouped one gets its own unheaded list:

```go-html-template
  <h2 class="recipe-sec">Ingredients</h2>
  {{- $sc := newScratch -}}
  {{- $sc.Set "g" "\x00init" -}}
  {{- range $i, $ing := .Params.ingredients -}}
    {{- $g := $ing.group | default "" -}}
    {{- if ne ($sc.Get "g") $g -}}
      {{- if ne ($sc.Get "g") "\x00init" -}}</ul>{{- end -}}
      {{- with $g }}<h3 class="recipe-ing-group">{{ . }}</h3>{{- end -}}
      <ul class="recipe-ing">
      {{- $sc.Set "g" $g -}}
    {{- end -}}
      <li data-i="{{ $i }}">
        {{ with $ing.qty }}<span class="q">{{ . }}{{ with $ing.unit }} {{ . }}{{ end }}</span> {{ end }}
        {{ $ing.item }}{{ with $ing.note }}, <span class="alt">{{ . }}</span>{{ end }}{{ with $ing.alt }} <span class="alt">(or {{ . }})</span>{{ end }}
      </li>
  {{- end -}}
  {{- if ne ($sc.Get "g") "\x00init" -}}</ul>{{- end -}}
```

- [ ] **Step 4: Restyle the group label as a heading**

In `assets/css/main.css`, the `.recipe-ing-group` rule currently styles an `<li>`. Replace that whole block with:

```css
.recipe-ing-group {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-ink-fade);
  margin: var(--space-sm) 0 var(--space-3xs);
  padding-top: var(--space-2xs);
}

/* Consecutive ingredient lists read as one column, not stacked blocks. */
.recipe-ing + .recipe-ing,
.recipe-ing-group + .recipe-ing {
  margin-top: 0;
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `hugo --gc --minify --environment production && npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS, including the pre-existing scaling test (which proves `data-i` and `.recipe-ing li` still resolve).

Run: `python3 tools/check_css_refs.py && python3 tools/check_spacing_tokens.py`
Expected: both `OK`.

- [ ] **Step 6: Commit**

```bash
git add layouts/partials/recipes/rail.html assets/css/main.css tests/e2e/recipes.spec.ts
git commit -m "fix(recipes): group headings are real headings; ungrouped runs close the group

RC2.2. The old guard fired only on a truthy, changed group and nothing closed
an open one, so trailing ungrouped items inherited the previous heading — in
the shipped fixture, 'salt' rendered inside 'For the sauce'. Group labels were
also bare <li>s, announced by screen readers as ingredients. Each run of
ingredients now gets its own <ul>, preceded by an <h3> when it is named.
data-i and .recipe-ing li are unchanged, so the scaler contract holds."
```

---

### Task 7: JSON-LD correctness — sources, x-ingredients, image (RC2.3, RC4.2)

**Files:**
- Modify: `layouts/partials/recipes/schema-recipe.html:23-27,39,45`

**Interfaces:**
- Consumes: `.Params.sources` (`name` required, `url`/`note` optional), `.Params.image`.
- Produces: `isBasedOn` present whenever any source exists; no `x-ingredients` key; `image` absolutised correctly for bundle-relative, root-relative, and absolute values.

- [ ] **Step 1: Confirm the defect in the built output**

Run: `python3 -c "import json;d=json.load(open('public/recipes/example-recipe-two/index.json'));print('isBasedOn' in d)"`
Expected: `False` — its only source is a book with no URL, so the whole entry was dropped while the page still credits it.

Run: `python3 -c "import json;d=json.load(open('public/recipes/example-recipe-one/index.json'));print(len(d['isBasedOn']), 'x-ingredients' in d)"`
Expected: `1 True` — one of two sources dropped, and a non-schema.org key is being published.

- [ ] **Step 2: Always append the source, add the URL only when present**

In `layouts/partials/recipes/schema-recipe.html`, replace lines 23–27:

```go-html-template
{{- $based := slice -}}
{{- range $p.Params.sources -}}
  {{- $cw := dict "@type" "CreativeWork" "name" .name -}}
  {{- with .url }}{{- $cw = merge $cw (dict "url" .) -}}{{- end -}}
  {{- $based = $based | append $cw -}}
{{- end -}}
```

- [ ] **Step 3: Drop the non-schema key**

Remove this line from the `$obj` literal:

```go-html-template
    "x-ingredients" $p.Params.ingredients
```

- [ ] **Step 4: Absolutise image correctly**

Replace line 45 (`with $p.Params.image`) with:

```go-html-template
{{- with $p.Params.image -}}
  {{- $img := . -}}
  {{- if or (hasPrefix $img "http://") (hasPrefix $img "https://") -}}
  {{- else if hasPrefix $img "/" -}}
    {{- $img = absURL $img -}}
  {{- else -}}
    {{- $img = printf "%s%s" $p.Permalink $img -}}
  {{- end -}}
  {{- $obj = merge $obj (dict "image" $img) -}}
{{- end -}}
```

- [ ] **Step 5: Verify**

Run: `hugo --gc --minify --environment production`

Run: `python3 -c "import json;d=json.load(open('public/recipes/example-recipe-two/index.json'));print(d['isBasedOn'])"`
Expected: a one-element list containing `{'@type': 'CreativeWork', 'name': 'Example Book of Dummies'}`.

Run: `python3 -c "import json;d=json.load(open('public/recipes/example-recipe-one/index.json'));print(len(d['isBasedOn']),'x-ingredients' in d, d['image'])"`
Expected: `2 False` and an absolute URL ending `/recipes/example-recipe-one/hero.svg`.

Run: `python3 -c "import json;d=json.load(open('public/recipes/example-recipe-three/index.json'));print(d['isBasedOn'][0]['name'])"`
Expected: `Example Book of Dummies`

Run: `npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add layouts/partials/recipes/schema-recipe.html
git commit -m "fix(recipes): url-less sources reach isBasedOn; drop x-ingredients; fix image

RC2.3 + RC4.2. 'with .url' gated the whole isBasedOn append, so a book source
vanished from the download while the page still credited it — schema.org
accepts a CreativeWork with name alone, so the drop bought nothing. The
non-schema x-ingredients key was a third copy of the ingredients in public
JSON-LD. image now handles absolute, root-relative, and bundle-relative forms
instead of blindly prefixing the permalink."
```

---

### Task 8: Serves label targets the input, not the minus button (RC2.4)

**Files:**
- Modify: `layouts/partials/recipes/rail.html:3-10`
- Test: `tests/e2e/recipes.spec.ts`

**Interfaces:**
- Consumes: nothing.
- Produces: `#recipe-serves` id on the servings input. Task 9/Task 10 select it by class (`.recipe-serves`), which is unchanged.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/recipes.spec.ts`:

```typescript
test('clicking the "Serves" label focuses the input and does not rescale', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const oil = page.locator('.recipe-ing li', { hasText: 'olive oil' }).locator('.q');
  await expect(oil).toHaveText('2 tbsp');
  await page.getByText('Serves', { exact: true }).click();
  await expect(oil).toHaveText('2 tbsp');
  await expect(page.locator('.recipe-serves')).toBeFocused();
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx playwright test tests/e2e/recipes.spec.ts -g "Serves"`
Expected: FAIL — the click decrements servings, the quantity becomes `1½ tbsp`, and focus lands on `.recipe-minus`.

- [ ] **Step 3: Stop wrapping the controls in the label**

In `layouts/partials/recipes/rail.html`, replace lines 3–10:

```go-html-template
    <label class="recipe-serves-label" for="recipe-serves">Serves</label>
    <span class="recipe-stp">
      <button type="button" class="recipe-minus" aria-label="fewer servings">–</button>
      <input id="recipe-serves" class="recipe-serves numin" type="number" min="1" max="99"
             value="{{ .Params.servings }}" inputmode="decimal">
      <button type="button" class="recipe-plus" aria-label="more servings">+</button>
    </span>
```

The `aria-label="servings"` is removed deliberately: the visible `<label>` now names the control, and an `aria-label` would override it — breaking WCAG 2.5.3 (Label in Name) in the other direction.

- [ ] **Step 4: Run the test to verify it passes**

Run: `hugo --gc --minify --environment production && npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/recipes/rail.html tests/e2e/recipes.spec.ts
git commit -m "fix(recipes): 'Serves' label targets the input, not the minus button

RC2.4. A label's labeled control is its first labelable descendant, and
<button> is labelable — so the label pointed at .recipe-minus and clicking the
word 'Serves' decremented servings and rescaled the whole recipe. The input
also had no programmatic label matching its visible text (WCAG 2.5.3)."
```

---

### Task 9: Server render is authoritative at rest; formatter floor (RC2.5)

**Files:**
- Modify: `assets/js/recipe-scale.js:14-31`
- Modify: `assets/js/entry-recipes.js:9-59`
- Test: `tests/unit/recipe-scale.test.mjs`
- Test: `tests/e2e/recipes.spec.ts`

**Interfaces:**
- Consumes: `.recipe-ing li[data-i]` and `.q` (Task 6 preserved both).
- Produces: `formatQuantity(value, unit) -> string` — same signature, never returns `"0"` for a positive input. `initScaler` no longer calls `apply()` at load.

- [ ] **Step 1: Write the failing unit tests**

Append to `tests/unit/recipe-scale.test.mjs`:

```javascript
test('a positive quantity never formats to zero', () => {
  assert.equal(formatQuantity(0.25, 'g'), '0.25');
  assert.equal(formatQuantity(0.04, 'kg'), '0.04');
  assert.equal(formatQuantity(0.05, null), '0.05');
  assert.equal(formatQuantity(0.5, 'g'), '0.5');
});

test('zero stays zero', () => {
  assert.equal(formatQuantity(0, 'g'), '0');
  assert.equal(formatQuantity(0, null), '0');
});

test('values above the floor are unchanged', () => {
  assert.equal(formatQuantity(1200, 'g'), '1200');
  assert.equal(formatQuantity(2.25, 'kg'), '2.3');
  assert.equal(formatQuantity(1.5, null), '1½');
});
```

- [ ] **Step 2: Run them to verify they fail**

Run: `node --no-experimental-detect-module --test tests/unit/*.test.mjs`
Expected: FAIL — `formatQuantity(0.25,'g')` returns `'0'`, `(0.04,'kg')` returns `'0'`, `(0.5,'g')` returns `'1'`.

- [ ] **Step 3: Add the floor**

In `assets/js/recipe-scale.js`, add `sig2` above `fmtFrac` and rewrite the two exported paths:

```javascript
// Two significant digits — the floor that keeps a scaled-down quantity from
// rounding away to "0". Number() drops toPrecision's trailing zeros.
function sig2(v) {
  return String(Number(v.toPrecision(2)));
}

function fmtFrac(v) {
  const whole = Math.floor(v + 1e-9);
  let e = Math.round((v - whole) * 8);
  let w = whole;
  if (e === 8) { w += 1; e = 0; }
  const f = VULGAR[e];
  if (w === 0 && f === '') return v > 0 ? sig2(v) : '0';
  if (w === 0) return f;
  return f ? (w + f) : String(w);
}

export function formatQuantity(value, unit) {
  switch (unitMode(unit)) {
    case 'whole': {
      const r = Math.round(value);
      return r === 0 && value > 0 ? sig2(value) : String(r);
    }
    case 'decimal': {
      const r = Math.round(value * 10) / 10;
      return r === 0 && value > 0 ? sig2(value) : r.toString();
    }
    default:
      return fmtFrac(value);
  }
}
```

- [ ] **Step 4: Run the unit tests to verify they pass**

Run: `node --no-experimental-detect-module --test tests/unit/*.test.mjs`
Expected: PASS.

- [ ] **Step 5: Write the failing E2E for the load-time rewrite**

Append to `tests/e2e/recipes.spec.ts`:

```typescript
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
```

- [ ] **Step 6: Make the DOM binding server-authoritative**

In `assets/js/entry-recipes.js`, replace `initScaler`'s body from line 10 through the `apply` function, and delete the trailing `fromServings();` call on line 56:

```javascript
function initScaler(rail) {
  const base = parseFloat(rail.dataset.baseServings) || 1;
  const data = JSON.parse(rail.querySelector('.recipe-data').textContent);
  const serves = rail.querySelector('.recipe-serves');
  const mult = rail.querySelector('.recipe-mult');
  const items = rail.querySelectorAll('.recipe-ing li');

  // The server render is authoritative at rest. Capture the authored strings so
  // returning to ratio 1 restores them verbatim rather than re-formatting them
  // through a second, lossy formatter (which flipped "0.5 tsp" to "½ tsp").
  const originals = new Map();
  items.forEach((li) => {
    const q = li.querySelector('.q');
    if (q) originals.set(q, q.textContent);
  });

  function apply(r) {
    const isBase = Math.abs(r - 1) <= 1e-9;
    items.forEach((li) => {
      const ing = data[+li.dataset.i];
      const q = li.querySelector('.q');
      if (!q || ing.qty == null) return;
      q.textContent = isBase
        ? originals.get(q)
        : formatQuantity(ing.qty * r, ing.unit) + (ing.unit ? ' ' + ing.unit : '');
      q.classList.toggle('changed', !isBase);
    });
  }
```

Leave `fromServings` / `fromMult` / the listeners as they are — Task 10 rewrites them. Delete only the bare `fromServings();` call that sits immediately before the closing brace of `initScaler`.

- [ ] **Step 7: Run the E2E to verify it passes**

Run: `hugo --gc --minify --environment production && npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS — including the pre-existing scaling test.

- [ ] **Step 8: Commit**

```bash
git add assets/js/recipe-scale.js assets/js/entry-recipes.js \
        tests/unit/recipe-scale.test.mjs tests/e2e/recipes.spec.ts
git commit -m "fix(recipes): server render authoritative at rest; formatter gains a floor

RC2.5. fromServings() ran at load, so a second formatter rewrote every
server-rendered quantity at ratio 1 — '0.5 tsp' flipped to '½ tsp' after paint
and a JS-off reader saw a permanently different string. The authored text is
captured and restored at ratio 1 instead. formatQuantity had no floor, so
0.25 g and 0.04 kg both rendered as '0'; they now fall back to two significant
digits."
```

---

### Task 10: Clamp write-back and multiplier bounds (RC2.6)

**Files:**
- Modify: `assets/js/entry-recipes.js:27-54`
- Modify: `layouts/partials/recipes/rail.html:12`
- Test: `tests/e2e/recipes.spec.ts`

**Interfaces:**
- Consumes: `apply(r)` and `base` from Task 9's `initScaler`.
- Produces: `normalize(s) -> {s, r}`, used by both input handlers. Task 14 calls it for the status line.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/recipes.spec.ts`:

```typescript
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx playwright test tests/e2e/recipes.spec.ts -g "declared bounds"`
Expected: FAIL — `serves` still reads `100` while `mult` reads `24.75`, above its own `max="20"`.

- [ ] **Step 3: Normalize in one place, write back on change**

In `assets/js/entry-recipes.js`, replace everything from `const clean = ...` through the two `addEventListener` lines for `serves`/`mult` (lines 27–46) with:

```javascript
  const SERVES_MIN = 1;
  const SERVES_MAX = 99;
  const MULT_MIN = 0.1;
  const MULT_MAX = 20;

  const clean = (n) => (Math.round(n * 100) / 100).toString();

  // Servings is the source of truth; the ratio is derived, then both are
  // clamped against BOTH controls' declared bounds so the two can never
  // disagree about what is currently displayed.
  function normalize(rawServings) {
    let s = Math.min(SERVES_MAX, Math.max(SERVES_MIN, rawServings));
    let r = s / base;
    if (r > MULT_MAX) { r = MULT_MAX; s = base * r; }
    if (r < MULT_MIN) { r = MULT_MIN; s = base * r; }
    return { s, r };
  }

  function fromServings(writeBack) {
    let raw = parseFloat(serves.value);
    if (!(raw > 0)) raw = base;
    const { s, r } = normalize(raw);
    mult.value = clean(r);
    if (writeBack) serves.value = clean(s);
    apply(r);
  }

  function fromMult(writeBack) {
    let raw = parseFloat(mult.value);
    if (!(raw > 0)) raw = 1;
    const { s, r } = normalize(base * raw);
    serves.value = clean(s);
    if (writeBack) mult.value = clean(r);
    apply(r);
  }

  // `input` tracks as you type without fighting the caret; `change` (blur or
  // Enter) is where the clamped value is written back into the field.
  serves.addEventListener('input', () => fromServings(false));
  serves.addEventListener('change', () => fromServings(true));
  mult.addEventListener('input', () => fromMult(false));
  mult.addEventListener('change', () => fromMult(true));
```

The two stepper button handlers below call `fromServings()` with no argument; change both to `fromServings(true)`:

```javascript
  rail.querySelector('.recipe-minus').addEventListener('click', () => {
    serves.value = Math.max(1, (parseFloat(serves.value) || base) - 1);
    fromServings(true);
  });
  rail.querySelector('.recipe-plus').addEventListener('click', () => {
    serves.value = Math.min(99, (parseFloat(serves.value) || base) + 1);
    fromServings(true);
  });
```

- [ ] **Step 4: Fix the permanent stepMismatch**

In `layouts/partials/recipes/rail.html`, line 12 — `min="0.1"` with `step="0.25"` means every valid value fails constraint validation, because the implied step base is `min`:

```html
      <input class="recipe-mult" type="number" min="0.1" max="20" step="any"
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `hugo --gc --minify --environment production && npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS, all recipe specs.

- [ ] **Step 6: Commit**

```bash
git add assets/js/entry-recipes.js layouts/partials/recipes/rail.html tests/e2e/recipes.spec.ts
git commit -m "fix(recipes): clamp written back; multiplier honours its own bounds

RC2.6. fromServings clamped the math but never the field, so typing 100 gave
servings-for-100 with amounts-for-99 and a multiplier of 24.75 above its own
max of 20; fromMult ignored min/max entirely, so 1000 scaled x1000. Both
paths now go through one normalize() and write the clamped value back on
change. step=\"0.25\" against min=\"0.1\" was a permanent stepMismatch."
```

---

### Task 11: Nav holds one row below 960px (RC3.1)

**Files:**
- Modify: `assets/css/main.css` (append to the site-header section, after line 377)
- Test: `tests/e2e/core.spec.ts`

**Interfaces:**
- Consumes: nothing.
- Produces: no API. Visual only.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/core.spec.ts`:

```typescript
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx playwright test tests/e2e/core.spec.ts -g "one row at 860px"`
Expected: FAIL — height ≈ 144.

- [ ] **Step 3: Step the nav scale down below the 1100px breakpoint**

In `assets/css/main.css`, immediately after the `.site-nav a[aria-current="page"]` rule (line 377), add:

```css
/* RC3.1 — the nav carries 8 items plus three icon buttons. At the canonical
   1100px tier, step type and gap down one notch so the row still fits well
   below 960px (the half-screen width used for manual checks) instead of
   wrapping the icon buttons onto a second row on every page. */
@media (max-width: 1100px) {
  .site-nav {
    gap: var(--space-md);
    font-size: var(--text-xs);
  }
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `hugo --gc --minify --environment production && npx playwright test tests/e2e/core.spec.ts`
Expected: PASS.

Run: `python3 tools/check_breakpoints.py && python3 tools/check_spacing_tokens.py`
Expected: both `OK` — 1100 is on the canonical scale, and the gap uses a `--space-*` token.

- [ ] **Step 5: Commit**

```bash
git add assets/css/main.css tests/e2e/core.spec.ts
git commit -m "fix(css): nav holds one row below 960px with 8 items

RC3.1. Adding Recipes tipped the header over its one-row budget: 144px
instead of 96px at 860px, and 196px instead of 144px at 700px, on all 139
pages. 960px — the documented manual-check width — was unaffected, which is
why it slipped through. Type and gap now step down at the canonical 1100px
tier; no markup change, every destination stays visible."
```

---

### Task 12: Steps column fills the width on mobile (RC3.2)

**Files:**
- Modify: `assets/css/main.css` (the `@media (max-width: 720px)` block in §51, ~line 5977)
- Test: `tests/e2e/recipes.spec.ts`

**Interfaces:**
- Consumes: nothing.
- Produces: no API. Visual only.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/recipes.spec.ts`:

```typescript
test('steps column fills the width when the layout collapses (RC3.2)', async ({ page }) => {
  await page.setViewportSize({ width: 700, height: 1000 });
  await page.goto('/recipes/example-recipe-one/');
  const rail = await page.locator('.recipe-rail').boundingBox();
  const steps = await page.locator('.recipe-steps-col').boundingBox();
  expect(Math.abs(rail!.width - steps!.width)).toBeLessThan(2);
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx playwright test tests/e2e/recipes.spec.ts -g "steps column fills"`
Expected: FAIL — rail 660, steps 392.5, a 267px gap.

- [ ] **Step 3: Stretch the steps column**

In `assets/css/main.css`, inside the existing `@media (max-width: 720px)` block in §51, add the rule:

```css
  .recipe-steps-col {
    width: 100%;
  }
```

`.recipe-body` sets `align-items: flex-start`, so flipping `flex-direction` to `column` cross-sizes children to `fit-content`; `flex: 1` only governs the main axis, which is why the rail's explicit `width: 100%` worked and the steps column's `flex: 1` did not.

- [ ] **Step 4: Run the test to verify it passes**

Run: `hugo --gc --minify --environment production && npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add assets/css/main.css tests/e2e/recipes.spec.ts
git commit -m "fix(css): steps column fills the width when recipes collapse to one column

RC3.2. The 720px block gave the rail width:100% but not .recipe-steps-col,
which shrink-wrapped to 392.5px against a 660px rail at a 700px viewport —
the Steps rule and headnote border stopped ~245px short of the rules above
and below them."
```

---

### Task 13: Restore focus indicators on the scaler controls (RC3.3)

**Files:**
- Modify: `assets/css/main.css` (`.recipe-stp`, `.numin:focus`, `.recipe-mult:focus` — §51, lines ~5800-5880)
- Test: `tests/e2e/recipes.spec.ts`

**Interfaces:**
- Consumes: the global `:focus-visible { outline: 2px solid var(--color-burgundy) }` at `main.css:317`.
- Produces: no API. Visual only.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/recipes.spec.ts`:

```typescript
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx playwright test tests/e2e/recipes.spec.ts -g "focus ring"`
Expected: FAIL — `.recipe-serves` and `.recipe-mult` report `outline-style: none`, and `.recipe-stp` reports `overflow: hidden`.

- [ ] **Step 3: Stop clipping the steppers and round them individually**

In `assets/css/main.css`, remove `overflow: hidden;` from `.recipe-stp` and give the buttons their own corner radii plus a ring:

```css
.recipe-stp {
  border: 1px solid var(--color-rule);
  background: var(--color-paper);
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
}
```

Immediately after the `.recipe-stp button:hover` rule, add:

```css
.recipe-stp button:first-child { border-radius: 6px 0 0 6px; }
.recipe-stp button:last-child  { border-radius: 0 6px 6px 0; }
.recipe-stp button:focus-visible {
  outline: 2px solid var(--color-burgundy);
  outline-offset: -2px;
}
```

- [ ] **Step 4: Give the two inputs a real ring instead of a background swap**

Replace the `.numin:focus` rule:

```css
.numin:focus-visible {
  outline: 2px solid var(--color-burgundy);
  outline-offset: -2px;
  background: var(--color-paper);
}
```

Replace the `.recipe-mult:focus` rule:

```css
.recipe-mult:focus-visible {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 2px;
  border-bottom-color: var(--color-burgundy);
  color: var(--color-ink);
}
```

The old `background: var(--color-stone)` substitute computed to 1.13:1 against `--color-paper` in light mode and 1.24:1 in dark, versus the 3:1 that SC 1.4.11 requires of a non-text indicator.

- [ ] **Step 5: Run the test to verify it passes**

Run: `hugo --gc --minify --environment production && npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add assets/css/main.css tests/e2e/recipes.spec.ts
git commit -m "fix(a11y): restore focus indicators on all four scaler controls

RC3.3. .numin:focus and .recipe-mult:focus out-specified the global
:focus-visible ring and set outline:none, substituting a background swap that
computes to 1.13:1 light / 1.24:1 dark against the 3:1 SC 1.4.11 requires.
.recipe-stp{overflow:hidden} additionally clipped the UA ring on both stepper
buttons, which carried no author focus style at all."
```

---

### Task 14: Two-channel rescale signal (RC3.4, RC4.8)

**Files:**
- Modify: `layouts/partials/recipes/rail.html:1,15`
- Modify: `assets/js/entry-recipes.js` (`apply`, `fromServings`, `fromMult`)
- Modify: `assets/css/main.css` (`.q.changed`, §51)
- Modify: `tools/css-refs-allowlist.txt`
- Test: `tests/e2e/recipes.spec.ts`

**Interfaces:**
- Consumes: `normalize()` and `apply()` from Tasks 9–10.
- Produces: `.recipe-q-changed` replaces `.changed`; `.recipe-scale-status[role="status"]` inside `.recipe-rail`.

- [ ] **Step 1: Write the failing test**

Append to `tests/e2e/recipes.spec.ts`:

```typescript
test('a rescaled quantity signals in two channels (RC3.4)', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const oil = page.locator('.recipe-ing li', { hasText: 'olive oil' }).locator('.q');
  const status = page.locator('.recipe-scale-status');

  await expect(status).toBeHidden();

  await page.fill('.recipe-serves', '6');
  await expect(oil).toHaveClass(/recipe-q-changed/);
  // Channel 2: a non-colour, announced signal.
  await expect(status).toBeVisible();
  await expect(status).toHaveAttribute('role', 'status');
  await expect(status).toContainText('1.5');
  await expect(status).toContainText('6');
  // Channel 1: not colour alone — the underline is a second visual channel.
  const decoration = await oil.evaluate((el) => getComputedStyle(el).textDecorationLine
    + ' ' + getComputedStyle(el).borderBottomStyle);
  expect(decoration).toMatch(/underline|dotted/);

  await page.fill('.recipe-serves', '4');
  await expect(status).toBeHidden();
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx playwright test tests/e2e/recipes.spec.ts -g "two channels"`
Expected: FAIL — `.recipe-scale-status` does not exist.

- [ ] **Step 3: Add the status element and the yield unit to the rail**

In `layouts/partials/recipes/rail.html`, line 1 gains the unit the status line needs:

```go-html-template
<aside class="recipe-rail" data-base-servings="{{ .Params.servings }}" data-yield-unit="{{ default "servings" .Params.yield_unit }}">
```

Immediately after the closing `</div>` of `.recipe-scaler` (line 15), add:

```html
  <p class="recipe-scale-status" role="status" hidden></p>
```

- [ ] **Step 4: Drive both channels from the runtime**

In `assets/js/entry-recipes.js`, add the status lookup beside the other element lookups in `initScaler`:

```javascript
  const status = rail.querySelector('.recipe-scale-status');
  const yieldUnit = rail.dataset.yieldUnit || 'servings';
```

In `apply`, change the class token:

```javascript
      q.classList.toggle('recipe-q-changed', !isBase);
```

Then add a status updater directly below `apply`, and call it from both handlers:

```javascript
  // Second channel: says by how much, and announces it. .recipe-q-changed says
  // which values moved; colour alone would carry the whole meaning otherwise.
  function updateStatus(s, r) {
    if (!status) return;
    const isBase = Math.abs(r - 1) <= 1e-9;
    status.hidden = isBase;
    status.textContent = isBase
      ? ''
      : `Scaled ×${clean(r)} — amounts shown for ${clean(s)} ${yieldUnit}`;
  }
```

In `fromServings`, after `apply(r);` add `updateStatus(s, r);`. In `fromMult`, after `apply(r);` add `updateStatus(s, r);`.

- [ ] **Step 5: Style both channels**

In `assets/css/main.css`, replace the `.q.changed` rule:

```css
.q.recipe-q-changed {
  color: var(--color-burgundy);
  border-bottom: 1px dotted currentColor;
}

.recipe-scale-status {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--color-burgundy);
  margin: var(--space-sm) 0 0;
  padding-top: var(--space-2xs);
  border-top: 1px dashed var(--color-rule);
}
.recipe-scale-status[hidden] { display: none; }
```

The explicit `[hidden]` rule is required: any author-side `display` value overrides the UA `[hidden] { display: none }`, the same cascade gotcha already handled for `.filter-chip` and `.garden-tile`.

- [ ] **Step 6: Narrow the allowlist entry**

In `tools/css-refs-allowlist.txt`, replace the `changed` entry with the specific class:

```
# §51 recipe scaler: the JS scaler adds `.recipe-q-changed` to `.q` elements
# when a quantity differs from the authored amount, and reveals
# `.recipe-scale-status`. Neither appears as a literal in layouts — both are
# toggled at runtime by assets/js/entry-recipes.js. Verified by
# tests/e2e/recipes.spec.ts.
recipe-q-changed
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `hugo --gc --minify --environment production && npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS.

Run: `python3 tools/check_css_refs.py`
Expected: `OK`.

Run: `grep -rn '\.changed\|classList.toggle(.changed' assets/ layouts/ tools/css-refs-allowlist.txt`
Expected: no matches for the bare `changed` token.

- [ ] **Step 8: Commit**

```bash
git add layouts/partials/recipes/rail.html assets/js/entry-recipes.js \
        assets/css/main.css tools/css-refs-allowlist.txt tests/e2e/recipes.spec.ts
git commit -m "feat(recipes): rescaled quantities signal in two channels

RC3.4 + RC4.8. The only signal was burgundy text: colour-only meaning against
the spec's hard constraints, with no announcement — a screen-reader user
pressing '+' got silence while every quantity changed. A dotted underline now
marks which values moved and a role=status line states by how much. The class
is renamed .changed -> .recipe-q-changed so the css-refs allowlist stops
whitelisting a bare 'changed' token site-wide."
```

---

### Task 15: Contrast gate covers the rail surface (RC5.2)

**Files:**
- Modify: `tools/check-contrast.py:21-30`
- Modify: `assets/css/main.css` (dark token blocks — **both** `:root[data-theme="dark"]` at ~line 90 and the `prefers-color-scheme` block at ~line 109; light `:root` at ~line 43)

**Interfaces:**
- Consumes: `parse_palette`, which reads `:root` and `:root[data-theme="dark"]`.
- Produces: three new entries in `PAIRINGS`. No signature change.

- [ ] **Step 1: Add the failing pairings**

In `tools/check-contrast.py`, append to `PAIRINGS`:

```python
    ("color-ink",      "color-tile", 7.0, "body text on tile/rail surface"),
    ("color-burgundy", "color-tile", 4.5, "rescaled-quantity accent on rail surface"),
    ("color-ink-fade", "color-tile", 4.5, "ingredient qualifier text on rail surface"),
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 tools/check-contrast.py`
Expected: FAIL — dark `burgundy/tile` 3.78 < 4.5; light `ink-fade/tile` 2.90 < 4.5; dark `ink-fade/tile` 3.21 < 4.5. (`ink/tile` already passes at 16.91 light / 11.51 dark.)

- [ ] **Step 3: Nudge the three failing stops**

These values were computed against `--color-tile` (`#fdfcf8` light, `#2a2a2a` dark) and re-checked against `--color-stone` so no existing pairing regresses.

In the light `:root` block:

```css
  --color-ink-fade: #78746d;
```

In **both** dark blocks (`:root[data-theme="dark"]` and the `prefers-color-scheme: dark` media block) — they must stay byte-identical:

```css
  --color-ink-fade: #9b978e;
  --color-burgundy: #de6f7d;
```

Resulting ratios: light ink-fade/tile 4.53 (was 2.90), dark ink-fade/tile 4.93 (was 3.21), dark burgundy/tile 4.56 (was 3.78), dark burgundy/stone 5.64 (was 4.68, still passing).

- [ ] **Step 4: Verify the gate and the dark-token duplication**

Run: `python3 tools/check-contrast.py`
Expected: PASS, all 12 pairings.

Run: `python3 tools/check_dark_tokens.py`
Expected: `OK` — the two dark blocks still agree.

- [ ] **Step 5: Commit**

```bash
git add tools/check-contrast.py assets/css/main.css
git commit -m "fix(a11y): contrast gate covers the tile surface; nudge two token stops

RC5.2. Every pairing was checked against --color-stone, but the recipe rail
is --color-tile — which put .alt ('diced', 'to taste', 'or shallot') at
2.90:1 light and 3.21:1 dark, and the rescale accent at 3.78:1 dark, all with
CI green. Three tile pairings added; ink-fade and dark burgundy nudged to
clear AA on both surfaces."
```

---

### Task 16: Config and chrome corrections (RC4.1, RC4.3, RC4.4, RC4.5, RC4.11)

**Files:**
- Modify: `hugo.yaml:30-32`
- Modify: `layouts/recipes/single.html` (the `.recipe-dl` anchor)
- Modify: `layouts/recipes/list.html:52`
- Modify: `layouts/partials/recipes/rail.html` (wrap `.recipe-scaler` in a noscript guard)
- Modify: `layouts/partials/recipes/card.html:6`
- Modify: `layouts/recipes/single.html:9`

**Interfaces:**
- Consumes: nothing.
- Produces: no API changes.

- [ ] **Step 1: Confirm the media-type leak**

Run: `grep -A3 'mediaTypes' hugo.yaml`
Expected: `application/ld+json` claiming `suffixes: ["json"]` — which makes Hugo serve every `.json` output, including `/lhci-pages.json`, as `application/ld+json`.

- [ ] **Step 2: Use a media type that does not claim the suffix globally**

In `hugo.yaml`, delete the `mediaTypes:` block entirely (lines 30–32) and change the `RECIPE` output format to reuse the built-in JSON type. Read the `RECIPE` block first; change only its `mediaType` line to:

```yaml
    mediaType: application/json
```

- [ ] **Step 3: Name the downloaded file**

In `layouts/recipes/single.html`, the `.recipe-dl` anchor has a valueless `download`, so every saved file is called `index.json`:

```html
        <a class="recipe-dl" href="{{ .RelPermalink }}" download="{{ $.File.ContentBaseName }}.json"><span aria-hidden="true">⬇</span> Download recipe (.json)</a>
```

- [ ] **Step 4: Announce the empty filter state**

In `layouts/recipes/list.html`, line 52 — both sibling implementations carry `role="status"`:

```html
  <p class="recipe-empty" id="recipe-empty" role="status" hidden>No recipes match the current filters.</p>
```

- [ ] **Step 5: Hide the inert scaler when JS is off**

In `layouts/partials/recipes/rail.html`, immediately before the `<div class="recipe-scaler">` line, add:

```html
  <noscript><style>.recipe-scaler,.recipe-scale-status{display:none}</style></noscript>
```

This follows the `head.html:65` precedent. With JS off the scaler is fully operable-looking chrome that does nothing.

- [ ] **Step 6: Guard the dangling kicker separator**

Both the card and the single page build a kicker as `cuisine · category`. With a category but no cuisine, the output starts with a dangling `" · "`.

In `layouts/partials/recipes/card.html`, line 6:

```html
  <div class="recipe-card-kicker">{{ .Params.cuisine }}{{ if and .Params.cuisine .Params.category }} · {{ end }}{{ .Params.category }}</div>
```

In `layouts/recipes/single.html`, line 9:

```html
    <div class="recipe-kicker">{{ .Params.cuisine }}{{ if and .Params.cuisine .Params.category }} · {{ end }}{{ .Params.category }}</div>
```

- [ ] **Step 7: Verify**

Run: `hugo --gc --minify --environment production`
Expected: PASS.

Run: `python3 -c "import json;print(json.load(open('public/recipes/example-recipe-one/index.json'))['@type'])"`
Expected: `Recipe` — the output format still emits the same bytes.

Run: `grep -o 'download="[^"]*"' public/recipes/example-recipe-one/index.html`
Expected: `download="example-recipe-one.json"`

Run: `grep -o 'role=status' public/recipes/index.html`
Expected: a match.

Run: `python3 tools/gen_lhci_urls.py && python3 tools/check_lhci_urls.py`
Expected: `OK` — `check_lhci_urls.main()` takes no arguments; it reads `PUBLIC_DIR`, `DESKTOP_CONFIG`, and `MOBILE_CONFIG` itself, and must run after the regen so it validates the emitted list.

Run: `npx playwright test tests/e2e/recipes.spec.ts`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add hugo.yaml layouts/recipes/single.html layouts/recipes/list.html \
        layouts/partials/recipes/rail.html layouts/partials/recipes/card.html
git commit -m "fix(recipes): config and chrome corrections

RC4.1 the application/ld+json media type claimed suffix 'json' and changed how
/lhci-pages.json is served; application/json emits byte-identical output.
RC4.3 a valueless download attribute named every saved file index.json.
RC4.4 #recipe-empty dropped the role=status both sibling implementations carry.
RC4.5 with JS off the scaler was operable-looking chrome that did nothing.
RC4.11 a category without a cuisine left a dangling ' · ' separator."
```

---

### Task 17: Validate the image path (RC4.6)

**Files:**
- Modify: `tools/check_recipes_links.py`
- Test: `tools/test_check_recipes_links.py`

**Interfaces:**
- Consumes: `lint_file(md: Path) -> list[str]`, and the bundle directory `md.parent`.
- Produces: same signature; new rejection for a bundle-relative `image` that does not exist on disk, and for a malformed absolute one.

- [ ] **Step 1: Write the failing tests**

Append to the `T` class in `tools/test_check_recipes_links.py`. That file's fixture is a `str.format` template named `BASE`, with `{url}` and `{video}` placeholders and no `image` key — so each test formats it and appends the `image` line before the closing `---`:

```python
    def _with_image(self, value):
        base = BASE.format(url="https://example.com/x", video="dQw4w9WgXcQ")
        return base.replace('video: "dQw4w9WgXcQ"',
                            f'video: "dQw4w9WgXcQ"\nimage: "{value}"')

    def test_missing_bundle_image_rejected(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("nope.svg"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("image" in e for e in errs), errs)

    def test_present_bundle_image_passes(self):
        self.repo.write("content/recipes/ex/index.md", self._with_image("hero.svg"))
        self.repo.write("content/recipes/ex/hero.svg", "<svg/>")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_absolute_image_url_passes(self):
        self.repo.write("content/recipes/ex/index.md",
                        self._with_image("https://example.com/a.png"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 -m unittest tools.test_check_recipes_links -v`
Expected: the missing-image test fails (`rc == 0`, no error raised).

- [ ] **Step 3: Validate the field**

In `tools/check_recipes_links.py`, add to `lint_file`, after the `video` check:

```python
    img = fm.get("image")
    if img and str(img).strip() not in ("", "null"):
        val = str(img).strip()
        if val.startswith(("http://", "https://")):
            if not URL_RE.match(val):
                errs.append(f"{md}: image is not a well-formed http(s) URL")
        elif val.startswith("/"):
            target = md.parent.parent.parent.parent / "static" / val.lstrip("/")
            if not target.exists():
                errs.append(f"{md}: image '{val}' not found under static/")
        else:
            if not (md.parent / val).exists():
                errs.append(f"{md}: image '{val}' not found in the page bundle")
```

The `image` value is never rendered to a human — it reaches only JSON-LD — so nothing else in the pipeline would surface a broken path.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tools.test_check_recipes_links -v`
Expected: PASS.

Run: `python3 tools/check_recipes_links.py`
Expected: `check_recipes_links: OK` — `example-recipe-one` ships `hero.svg` alongside its `index.md`, so the one real `image:` in the tree resolves.

- [ ] **Step 5: Commit**

```bash
git add tools/check_recipes_links.py tools/test_check_recipes_links.py
git commit -m "feat(tools): validate the recipe image path

RC4.6. image reaches only JSON-LD, never a rendered <img>, so a broken path
was invisible to every existing check — including the html-link crawler.
Absolute URLs are shape-checked; root-relative paths resolve under static/;
bundle-relative ones must exist in the page bundle."
```

---

### Task 18: Documentation drift (RC4.9, RC4.10)

**Files:**
- Modify: `CLAUDE.md` (Recipes frontmatter contract; the stale branch reference; the CI step count)

**Interfaces:**
- Consumes: the linter's REQUIRED/OPTIONAL sets from `tools/check_recipes_fixtures.py:18-22`.
- Produces: documentation only.

- [ ] **Step 1: Confirm each drift**

Run: `grep -n 'prep_time' CLAUDE.md`
Expected: a match in the Recipes contract — a field name that exists nowhere in the codebase.

Run: `grep -c '^\s*- name:' .github/workflows/hugo.yaml`
Expected: `97`, against CLAUDE.md's "~79 named steps".

- [ ] **Step 2: Correct the frontmatter contract**

Replace the **Recipes** contract sentence in CLAUDE.md's "Frontmatter contracts" section so it matches the linter exactly:

```markdown
**Recipes** (`content/recipes/<slug>/index.md`) — enforced by `tools/check_recipes_fixtures.py` (34th pair) + `tools/check_recipes_links.py` (35th pair). Required: `title, date, lastmod, draft, summary, servings, sources, ingredients, steps`. Optional: `tags, cuisine, category, yield_unit, prep_minutes, cook_minutes, total_minutes, image, video, outputs`. `ingredients` and `sources` are flow-style YAML objects; `qty` on an ingredient may be `null` (uncountable items) but never `0`, and numeric fields must not be zero-padded (Hugo reads `010` as octal 8). Optional fields are guarded at the template layer — a recipe with no times renders no time line and emits no `*Time` JSON-LD keys; `content/recipes/example-recipe-three/` is the minimal fixture that keeps those paths build-exercised. Spec: `docs/superpowers/specs/2026-07-06-recipe-slice-1-render-download-design.md`; remediation: `docs/superpowers/specs/2026-09-07-recipe-audit-remediation-design.md`.
```

- [ ] **Step 3: Fix the step count and the stale branch reference**

Search CLAUDE.md for `~79 named steps` and replace with `~97 named steps`. Search for the branch name that no longer exists (`grep -n 'master' CLAUDE.md`) and correct it to `main`, matching the rename already recorded in git history.

- [ ] **Step 4: Verify nothing else drifted in the sections you touched**

Run: `grep -n 'Thirty-five linter pairs\|10 spec files' CLAUDE.md`
Expected: both present and accurate — these were reconciled during the rebase; confirm the E2E test count still matches `grep -h 'test(' tests/e2e/*.spec.ts | grep -c '^\s*test('` and update the number if this plan's new specs changed it.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: correct the recipe frontmatter contract and two stale facts

RC4.9 + RC4.10. The documented contract contradicted the linter four ways —
it named nonexistent prep_time/cook_time, omitted required date/lastmod, and
called required summary/sources optional. Since Slice 2's org exporter is
specced against this document, the drift was load-bearing. Also corrects the
CI step count (97, not ~79) and a branch name that no longer exists."
```

---

### Task 19: Full gate and merge readiness

**Files:** none — verification only.

- [ ] **Step 1: Run the complete local CI mirror**

Run: `bash tools/ci-local.sh`
Expected: every stage green through Playwright. LHCI will fail with `No chromium/google-chrome on PATH` — that is the known local gap and is covered in CI.

- [ ] **Step 2: Confirm the E2E and unit counts**

Run: `npx playwright test`
Expected: all specs pass. Record the new total.

Run: `node --no-experimental-detect-module --test tests/unit/*.test.mjs`
Expected: PASS.

- [ ] **Step 3: Re-verify every row against the built site**

Run each verification command from Tasks 3, 5, 7, and 16 once more against a fresh `hugo --gc --minify --environment production`, since later tasks touched the same templates.

- [ ] **Step 4: Update the E2E count in CLAUDE.md if it changed**

This plan adds specs in Tasks 4, 5, 6, 8, 9, 10, 11, 12, 13, and 14. Recount and correct the "10 spec files, 16 tests" sentence.

```bash
git add CLAUDE.md
git commit -m "docs: recount E2E specs after the remediation pass"
```

---

## Self-Review

**Spec coverage.** All 29 rows map to a task: RC1.1→T1, RC1.2→T3, RC1.3→T2, RC1.4→T4, RC2.1→T5, RC2.2→T6, RC2.3→T7, RC2.4→T8, RC2.5→T9, RC2.6→T10, RC2.7→T3, RC3.1→T11, RC3.2→T12, RC3.3→T13, RC3.4→T14, RC4.1/4.3/4.4/4.5/4.11→T16, RC4.2→T7, RC4.6→T17, RC4.7→T2, RC4.8→T14, RC4.9/4.10→T18, RC5.1→T3, RC5.2→T15, RC5.3→T5. Spec §4's testing table is satisfied: linter rows carry `unittest`, formatter rows carry `node --test`, runtime/layout rows carry Playwright, token rows carry `check-contrast.py`.

**Type consistency.** `formatQuantity(value, unit)` and `unitMode(unit)` keep their signatures throughout. `normalize(rawServings) -> {s, r}` is introduced in Task 10 and consumed only there and in Task 14. `apply(r)` is introduced in Task 9 and called by Tasks 10 and 14. The class token is `changed` up to Task 14 and `recipe-q-changed` after — Task 9's test deliberately matches `/recipe-q-changed|changed/` so it passes on both sides of that rename.

**Known ordering constraint.** Tasks 9, 10, and 14 all edit `initScaler` in `assets/js/entry-recipes.js` and must run in that order; Task 14 also depends on Task 10's `clean()` and `normalize()`. Tasks 6 and 8 both edit `rail.html`, as do Tasks 14 and 16. Tasks 11, 12, 13, 14, and 15 all edit `assets/css/main.css`, but in disjoint regions (nav ~line 377; §51 mobile block; §51 scaler chrome; §51 `.q`; the token blocks).
