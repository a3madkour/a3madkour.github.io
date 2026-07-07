# Recipe Section — Slice 1 (render + download) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a `content/recipes/` section that renders a recipe (two-column, house-styled) with a sources list, client-side portion scaling, and a schema.org/Recipe JSON download — plus a filterable index, nav entry, fixtures, two linter pairs, and E2E.

**Architecture:** Recipes are Hugo page bundles whose frontmatter is a *structured authoring layer*; a shared partial compiles that to a schema.org/Recipe object emitted both as `<head>` JSON-LD and as a downloadable `RECIPE` output-format `.json`. A pure JS module (`recipe-scale.js`) does unit-aware quantity scaling read from a per-page JSON data island; no-JS renders base quantities. Everything follows the site's existing section patterns (streams/library).

**Tech Stack:** Hugo extended ≥0.162.1, hand-rolled CSS (main.css §50), esbuild multi-entry JS, stdlib-only Python linters, Playwright E2E, `node --test` for pure JS units.

**Spec:** `docs/superpowers/specs/2026-07-06-recipe-slice-1-render-download-design.md`

## Global Constraints

- **Standard:** schema.org/Recipe (JSON-LD). `<head>` block and download share ONE partial (`partials/recipes/schema-recipe.html`). `recipeIngredient` = free-text strings; structured data rides under a non-standard `x-ingredients` key.
- **Frontmatter is parsed by `tools/check_fixtures.py:parse_frontmatter`, which supports scalars, inline arrays, and *flow-style* mappings in sequences (`- {k: v}`) but NOT block-style nested mappings.** Therefore `ingredients` and `sources` MUST be authored flow-style (`- { qty: 2, unit: tbsp, item: "olive oil" }`).
- **Fixtures are obviously-dummy** ("Example Recipe One", dummy items) but carry **real numeric qty/unit** so scaling + JSON-LD are exercised (spec §1 fixture rule).
- **Stdlib-only Python**; linters expose `run(repo_root) -> (int, list[str])` + a thin `main()`; unit tests use `tools/test_helpers.py:TempRepo`.
- **No new palette** — existing tokens only; burgundy/stone is AA-verified.
- **Resolved open questions (author's leans):** nav "Recipes" goes **after Streams, before About**; index cards are **text-only** (no thumbnails); `total_minutes` is an **optional override**, else computed `prep+cook`.
- **No AI-authored prose** anywhere, including fixtures.

---

### Task 1: Recipe fixtures + section index

**Files:**
- Create: `content/recipes/_index.md`
- Create: `content/recipes/example-recipe-one/index.md`
- Create: `content/recipes/example-recipe-two/index.md`
- Create: `content/recipes/example-recipe-three/index.md`

**Interfaces:**
- Produces: the frontmatter contract every later task consumes. Field names are fixed here: `title,date,lastmod,draft,summary,tags,cuisine,category,servings,yield_unit,prep_minutes,cook_minutes,total_minutes,image,video,sources,ingredients,steps` + Hugo `outputs`.

- [ ] **Step 1: Write the section index**

`content/recipes/_index.md`:
```markdown
---
title: "Recipes"
cascade:
  outputs: ["HTML", "RECIPE"]
---

Things worth cooking twice — with sources, scalable portions, and a clean download.
```

- [ ] **Step 2: Write fixture one (grouped ingredients, video, url source, [mm:ss] step)**

`content/recipes/example-recipe-one/index.md`:
```markdown
---
title: "Example Recipe One"
date: 2026-07-06
lastmod: 2026-07-06
draft: false
summary: "Lorem ipsum poached in a dolor sit tomato sauce — a fast one-pan example."
tags: [example, one-pan]
cuisine: "Example North"
category: "Main"
servings: 4
yield_unit: "servings"
prep_minutes: 10
cook_minutes: 25
video: "dQw4w9WgXcQ"
sources:
  - { name: "Example Cooking — Lorem", url: "https://example.com/lorem", note: "adapted" }
  - { name: "Example notebook" }
ingredients:
  - { group: "For the base", qty: 2, unit: tbsp, item: "olive oil" }
  - { group: "For the base", qty: 1, unit: null, item: "onion", note: "diced", alt: "shallot" }
  - { group: "For the sauce", qty: 800, unit: g, item: "canned tomatoes" }
  - { group: "For the sauce", qty: 4, unit: null, item: "eggs" }
  - { qty: null, unit: null, item: "salt", note: "to taste" }
steps:
  - "Heat the oil in a wide pan over medium heat."
  - "Add the onion; cook until soft, about 5 minutes."
  - "[02:30] Pour in the tomatoes; simmer 15 minutes."
  - "Make wells, crack in the eggs, cover, and cook until set."
---

An obviously-dummy headnote. Lorem ipsum dolor sit amet.
```

- [ ] **Step 3: Write fixture two (ungrouped, no video, source without url, decimal unit)**

`content/recipes/example-recipe-two/index.md`:
```markdown
---
title: "Example Recipe Two"
date: 2026-07-05
lastmod: 2026-07-05
draft: false
summary: "A second dummy example with no video and a longer total time."
tags: [example, baking]
cuisine: "Example South"
category: "Dessert"
servings: 8
yield_unit: "cookies"
prep_minutes: 20
cook_minutes: 12
total_minutes: 92
sources:
  - { name: "Example Book of Dummies" }
ingredients:
  - { qty: 1.5, unit: kg, item: "flour" }
  - { qty: 2, unit: cup, item: "sugar" }
  - { qty: 3, unit: null, item: "eggs" }
  - { qty: null, unit: null, item: "vanilla", note: "a splash" }
steps:
  - "Cream the sugar into the butter."
  - "Fold in the flour and eggs."
  - "Bake until golden."
---

Another dummy headnote.
```

- [ ] **Step 4: Write fixture three (quick, for the Time filter bucket)**

`content/recipes/example-recipe-three/index.md`:
```markdown
---
title: "Example Recipe Three"
date: 2026-07-04
lastmod: 2026-07-04
draft: false
summary: "A quick twenty-minute dummy example."
tags: [example, quick]
cuisine: "Example North"
category: "Side"
servings: 3
prep_minutes: 5
cook_minutes: 15
sources:
  - { name: "Example Weeknight", url: "https://example.com/weeknight" }
ingredients:
  - { qty: 400, unit: g, item: "beans" }
  - { qty: 2, unit: tsp, item: "cumin" }
steps:
  - "Warm the beans with the spice."
  - "Serve."
---
```

- [ ] **Step 5: Verify Hugo builds the section**

Run: `hugo --quiet && ls public/recipes/example-recipe-one/index.html`
Expected: file exists (a bare `single.html` is added in Task 5; for now Hugo uses the default — build must not error).

- [ ] **Step 6: Commit**

```bash
git add content/recipes/
git commit -m "feat(recipes): section index + obviously-dummy fixtures"
```

---

### Task 2: Frontmatter contract linter (`check_recipes_fixtures.py`)

**Files:**
- Create: `tools/check_recipes_fixtures.py`
- Create: `tools/test_check_recipes_fixtures.py`

**Interfaces:**
- Consumes: `check_fixtures.parse_frontmatter`, `test_helpers.TempRepo`.
- Produces: `run(repo_root: Path) -> tuple[int, list[str]]`, `main() -> int`, `lint_file(md: Path) -> list[str]`.

- [ ] **Step 1: Write the failing test**

`tools/test_check_recipes_fixtures.py`:
```python
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo
import check_recipes_fixtures as mod

VALID = """---
title: "Example Recipe One"
date: 2026-07-06
lastmod: 2026-07-06
draft: false
summary: "Dummy."
servings: 4
sources:
  - { name: "Example", url: "https://example.com/x" }
ingredients:
  - { qty: 2, unit: tbsp, item: "olive oil" }
  - { qty: null, unit: null, item: "salt", note: "to taste" }
steps:
  - "Do the thing."
---
Body.
"""


class T(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_valid_passes(self):
        self.repo.write("content/recipes/ex/index.md", VALID)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_missing_required(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('servings: 4\n', ''))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("servings" in e for e in errs))

    def test_unknown_field(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('servings: 4', 'servings: 4\nbogus: 1'))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("bogus" in e for e in errs))

    def test_ingredient_missing_item(self):
        bad = VALID.replace('{ qty: 2, unit: tbsp, item: "olive oil" }',
                            '{ qty: 2, unit: tbsp }')
        self.repo.write("content/recipes/ex/index.md", bad)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("item" in e for e in errs))

    def test_servings_non_positive(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace('servings: 4', 'servings: 0'))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)

    def test_source_missing_name(self):
        bad = VALID.replace('{ name: "Example", url: "https://example.com/x" }',
                            '{ url: "https://example.com/x" }')
        self.repo.write("content/recipes/ex/index.md", bad)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("name" in e for e in errs))

    def test_bad_timecode(self):
        bad = VALID.replace('"Do the thing."', '"[99:99] bad marker step."')
        self.repo.write("content/recipes/ex/index.md", bad)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tools/test_check_recipes_fixtures.py`
Expected: FAIL — `ModuleNotFoundError: check_recipes_fixtures`.

- [ ] **Step 3: Write the linter**

`tools/check_recipes_fixtures.py`:
```python
#!/usr/bin/env python3
"""Recipe fixture frontmatter shape linter.

Walks content/recipes/<slug>/index.md and validates frontmatter against
spec 2026-07-06-recipe-slice-1-render-download-design.md. Stdlib only.
Exits 0 on all-pass, 1 on any violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

REQUIRED = {"title", "date", "lastmod", "draft", "summary",
            "servings", "sources", "ingredients", "steps"}
OPTIONAL = {"tags", "cuisine", "category", "yield_unit",
            "prep_minutes", "cook_minutes", "total_minutes",
            "image", "video", "outputs"}
FIELDS = REQUIRED | OPTIONAL

TIMECODE_RE = re.compile(r"^\[(\d{1,2}):([0-5]\d)(?:\.\d{1,2})?\]")


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def lint_file(md: Path) -> list[str]:
    errs: list[str] = []
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return [f"{md}: no frontmatter"]

    for f in sorted(REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    sv = fm.get("servings")
    if sv is not None and not (_is_num(sv) and sv > 0):
        errs.append(f"{md}: servings must be a number > 0")

    for key in ("prep_minutes", "cook_minutes", "total_minutes"):
        v = fm.get(key)
        if v is not None and not (isinstance(v, int) and not isinstance(v, bool) and v >= 0):
            errs.append(f"{md}: {key} must be a non-negative integer")

    ings = fm.get("ingredients")
    if ings is not None:
        if not isinstance(ings, list) or not ings:
            errs.append(f"{md}: ingredients must be a non-empty list")
        else:
            for i, ing in enumerate(ings):
                if not isinstance(ing, dict):
                    errs.append(f"{md}: ingredients[{i}] must be a flow mapping {{...}}")
                    continue
                if not str(ing.get("item", "")).strip():
                    errs.append(f"{md}: ingredients[{i}] missing 'item'")
                q = ing.get("qty")
                if q is not None and not _is_num(q):
                    errs.append(f"{md}: ingredients[{i}] qty must be a number or null")
                extra = set(ing.keys()) - {"qty", "unit", "item", "alt", "note", "group"}
                for k in sorted(extra):
                    errs.append(f"{md}: ingredients[{i}] unknown key '{k}'")

    srcs = fm.get("sources")
    if srcs is not None:
        if not isinstance(srcs, list) or not srcs:
            errs.append(f"{md}: sources must be a non-empty list")
        else:
            for i, s in enumerate(srcs):
                if not isinstance(s, dict):
                    errs.append(f"{md}: sources[{i}] must be a flow mapping {{...}}")
                    continue
                if not str(s.get("name", "")).strip():
                    errs.append(f"{md}: sources[{i}] missing 'name'")

    steps = fm.get("steps")
    if steps is not None:
        if not isinstance(steps, list) or not steps:
            errs.append(f"{md}: steps must be a non-empty list")
        else:
            for i, st in enumerate(steps):
                s = str(st)
                m = re.match(r"^\[[^\]]*\]", s)
                if m and not TIMECODE_RE.match(s):
                    errs.append(f"{md}: steps[{i}] leading [..] is not a valid [mm:ss] marker")
    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    root = repo_root / "content" / "recipes"
    if root.exists():
        for child in sorted(root.iterdir()):
            md = child / "index.md"
            if child.is_dir() and md.exists():
                all_errs.extend(lint_file(md))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    rc, errs = run(Path(__file__).resolve().parent.parent)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_recipes_fixtures: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests + the linter against the repo**

Run: `python3 tools/test_check_recipes_fixtures.py && python3 tools/check_recipes_fixtures.py`
Expected: tests PASS; linter prints `check_recipes_fixtures: OK` for the Task-1 fixtures.

- [ ] **Step 5: Commit**

```bash
git add tools/check_recipes_fixtures.py tools/test_check_recipes_fixtures.py
git commit -m "feat(tools): recipe fixtures frontmatter linter (34th pair)"
```

---

### Task 3: Links/reference linter (`check_recipes_links.py`)

**Files:**
- Create: `tools/check_recipes_links.py`
- Create: `tools/test_check_recipes_links.py`

**Interfaces:**
- Produces: `run(repo_root) -> (int, list[str])`, `main()`, `lint_file(md)`.
- Validates: source `url` well-formedness (`https?://…`) and `video` id shape (`^[A-Za-z0-9_-]{11}$`).

- [ ] **Step 1: Write the failing test**

`tools/test_check_recipes_links.py`:
```python
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo
import check_recipes_links as mod

BASE = """---
title: "Ex"
date: 2026-07-06
lastmod: 2026-07-06
draft: false
summary: "d"
servings: 4
sources:
  - {{ name: "Ex", url: "{url}" }}
ingredients:
  - {{ qty: 1, unit: null, item: "x" }}
steps:
  - "s"
video: "{video}"
---
"""


class T(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_good(self):
        self.repo.write("content/recipes/ex/index.md",
                        BASE.format(url="https://example.com/x", video="dQw4w9WgXcQ"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_bad_url(self):
        self.repo.write("content/recipes/ex/index.md",
                        BASE.format(url="notaurl", video="dQw4w9WgXcQ"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("url" in e for e in errs))

    def test_bad_video(self):
        self.repo.write("content/recipes/ex/index.md",
                        BASE.format(url="https://example.com/x", video="short"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("video" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tools/test_check_recipes_links.py`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write the linter**

`tools/check_recipes_links.py`:
```python
#!/usr/bin/env python3
"""Recipe source-URL + video-id well-formedness linter. Stdlib only."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

URL_RE = re.compile(r"^https?://\S+$")
VIDEO_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def lint_file(md: Path) -> list[str]:
    errs: list[str] = []
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return []
    for i, s in enumerate(fm.get("sources") or []):
        if isinstance(s, dict) and s.get("url"):
            if not URL_RE.match(str(s["url"])):
                errs.append(f"{md}: sources[{i}] url is not a well-formed http(s) URL")
    vid = fm.get("video")
    if vid:
        if not VIDEO_RE.match(str(vid)):
            errs.append(f"{md}: video '{vid}' is not an 11-char YouTube id")
    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    root = repo_root / "content" / "recipes"
    if root.exists():
        for child in sorted(root.iterdir()):
            md = child / "index.md"
            if child.is_dir() and md.exists():
                all_errs.extend(lint_file(md))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    rc, errs = run(Path(__file__).resolve().parent.parent)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_recipes_links: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests + linter**

Run: `python3 tools/test_check_recipes_links.py && python3 tools/check_recipes_links.py`
Expected: tests PASS; linter prints `check_recipes_links: OK`.

- [ ] **Step 5: Commit**

```bash
git add tools/check_recipes_links.py tools/test_check_recipes_links.py
git commit -m "feat(tools): recipe links linter (35th pair)"
```

---

### Task 4: Scaling runtime (`recipe-scale.js`) — pure logic, TDD

**Files:**
- Create: `assets/js/recipe-scale.js`
- Create: `tests/unit/recipe-scale.test.mjs`

**Interfaces:**
- Produces (ESM exports consumed by Task 8's `entry-recipes.js` and by the unit test):
  - `formatQuantity(scaledValue: number, unit: string|null) -> string` — number-only display (unit appended by caller).
  - `unitMode(unit: string|null) -> "whole"|"decimal"|"frac"`.

- [ ] **Step 1: Write the failing test**

`tests/unit/recipe-scale.test.mjs`:
```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatQuantity, unitMode } from '../../assets/js/recipe-scale.js';

test('grams round to whole', () => {
  assert.equal(unitMode('g'), 'whole');
  assert.equal(formatQuantity(1200, 'g'), '1200');
  assert.equal(formatQuantity(400.4, 'g'), '400');
});

test('kg/l show one decimal, trailing zero trimmed', () => {
  assert.equal(unitMode('kg'), 'decimal');
  assert.equal(formatQuantity(2.25, 'kg'), '2.3');
  assert.equal(formatQuantity(3, 'kg'), '3');
});

test('spoons and counts use eighths fractions', () => {
  assert.equal(unitMode('tbsp'), 'frac');
  assert.equal(unitMode(null), 'frac');
  assert.equal(formatQuantity(3, 'tbsp'), '3');
  assert.equal(formatQuantity(1.5, null), '1½');
  assert.equal(formatQuantity(0.5, null), '½');
  assert.equal(formatQuantity(0.25, 'tsp'), '¼');
  assert.equal(formatQuantity(2.75, null), '2¾');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/unit/recipe-scale.test.mjs`
Expected: FAIL — cannot find module `recipe-scale.js`.

- [ ] **Step 3: Write the module**

`assets/js/recipe-scale.js`:
```javascript
// Pure, DOM-free scaling helpers. Imported by entry-recipes.js (browser)
// and tests/unit/recipe-scale.test.mjs (node --test). No side effects.
const WHOLE_UNITS = new Set(['g', 'ml']);
const DECIMAL_UNITS = new Set(['kg', 'l']);
const VULGAR = { 0: '', 1: '⅛', 2: '¼', 3: '⅜', 4: '½', 5: '⅝', 6: '¾', 7: '⅞' };

export function unitMode(unit) {
  const u = (unit || '').toLowerCase();
  if (WHOLE_UNITS.has(u)) return 'whole';
  if (DECIMAL_UNITS.has(u)) return 'decimal';
  return 'frac';
}

function fmtFrac(v) {
  const whole = Math.floor(v + 1e-9);
  let e = Math.round((v - whole) * 8);
  let w = whole;
  if (e === 8) { w += 1; e = 0; }
  const f = VULGAR[e];
  if (w === 0 && f === '') return '0';
  if (w === 0) return f;
  return f ? (w + f) : String(w);
}

export function formatQuantity(value, unit) {
  switch (unitMode(unit)) {
    case 'whole':   return String(Math.round(value));
    case 'decimal': return (Math.round(value * 10) / 10).toString();
    default:        return fmtFrac(value);
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/unit/recipe-scale.test.mjs`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add assets/js/recipe-scale.js tests/unit/recipe-scale.test.mjs
git commit -m "feat(recipes): pure unit-aware quantity scaling + node --test units"
```

---

### Task 5: schema.org emit partial + RECIPE output format + JSON-LD in head

**Files:**
- Create: `layouts/partials/recipes/schema-recipe.html`
- Create: `layouts/recipes/single.recipe.json` (RECIPE output template)
- Modify: `hugo.yaml` (add `RECIPE` output format + `RECIPE` media type)
- Modify: `layouts/partials/head.html` (emit JSON-LD on recipe pages)
- Modify: `tools/check_smoke.py` (assert built recipe emits ld+json + .json)

**Interfaces:**
- Produces: partial returns a **JSON string** of the schema.org/Recipe object for `.` (a recipe Page). Consumed by the head `<script>` and the RECIPE output template.

- [ ] **Step 1: Add the RECIPE output format + media type to `hugo.yaml`**

Under `outputFormats:` add:
```yaml
  RECIPE:
    mediaType: application/ld+json
    baseName: index
    isPlainText: true
    notAlternative: true
```
Under a top-level `mediaTypes:` (create if absent; ld+json is built-in in modern Hugo, so this may be unnecessary — verify build):
```yaml
mediaTypes:
  application/ld+json:
    suffixes: ["json"]
```

- [ ] **Step 2: Write the shared schema partial**

`layouts/partials/recipes/schema-recipe.html` — builds a dict and returns `jsonify`. (Uses `dict`/`slice`; times via `printf "PT%dM"`.)
```go-html-template
{{- $p := . -}}
{{- $total := or $p.Params.total_minutes (add (default 0 $p.Params.prep_minutes) (default 0 $p.Params.cook_minutes)) -}}
{{- $ingText := slice -}}
{{- range $p.Params.ingredients -}}
  {{- $q := "" -}}
  {{- with .qty }}{{ $q = printf "%v " . }}{{ end -}}
  {{- $u := "" }}{{ with .unit }}{{ $u = printf "%s " . }}{{ end -}}
  {{- $line := printf "%s%s%s" $q $u .item -}}
  {{- with .note }}{{ $line = printf "%s, %s" $line . }}{{ end -}}
  {{- $ingText = $ingText | append (trim $line " ") -}}
{{- end -}}
{{- $steps := slice -}}
{{- range $p.Params.steps -}}
  {{- $t := replaceRE `^\[\d{1,2}:[0-5]\d(?:\.\d{1,2})?\]\s*` "" . -}}
  {{- $steps = $steps | append (dict "@type" "HowToStep" "text" $t) -}}
{{- end -}}
{{- $based := slice -}}
{{- range $p.Params.sources -}}
  {{- with .url }}{{ $based = $based | append (dict "@type" "CreativeWork" "name" $.name "url" .) }}{{ end -}}
{{- end -}}
{{- $obj := dict
    "@context" "https://schema.org"
    "@type" "Recipe"
    "name" $p.Title
    "description" $p.Params.summary
    "datePublished" ($p.Date.Format "2006-01-02")
    "recipeYield" (printf "%v %s" $p.Params.servings (default "servings" $p.Params.yield_unit))
    "prepTime" (printf "PT%dM" (int (default 0 $p.Params.prep_minutes)))
    "cookTime" (printf "PT%dM" (int (default 0 $p.Params.cook_minutes)))
    "totalTime" (printf "PT%dM" (int $total))
    "recipeCuisine" $p.Params.cuisine
    "recipeCategory" $p.Params.category
    "keywords" (delimit $p.Params.tags ", ")
    "recipeIngredient" $ingText
    "recipeInstructions" $steps
    "x-ingredients" $p.Params.ingredients
-}}
{{- with $based }}{{ $obj = merge $obj (dict "isBasedOn" .) }}{{ end -}}
{{- $obj | jsonify -}}
```
Note: `.name` inside the sources `range` refers to the source's name; if Hugo scoping needs it, use `.name`/`$.name` as the build dictates — the verification step catches mis-scoping.

- [ ] **Step 3: Write the RECIPE output template**

`layouts/recipes/single.recipe.json`:
```go-html-template
{{- partial "recipes/schema-recipe.html" . -}}
```

- [ ] **Step 4: Emit JSON-LD in `<head>` for recipe pages**

In `layouts/partials/head.html`, before `</head>`:
```go-html-template
{{- if and (eq .Section "recipes") .IsPage -}}
<script type="application/ld+json">{{ partial "recipes/schema-recipe.html" . | safeJS }}</script>
{{- end -}}
```

- [ ] **Step 5: Build + eyeball the emitted JSON**

Run: `hugo --quiet && cat public/recipes/example-recipe-one/index.json | python3 -m json.tool | head -30`
Expected: valid JSON; `@type": "Recipe"`, `recipeIngredient` array of strings, `recipeInstructions` array of HowToStep, `x-ingredients` present. If the file is named differently, adjust `baseName`/verify the RECIPE output path; the `.RelPermalink` used in Task 6 must match.

- [ ] **Step 6: Add a built-page assertion to `check_smoke.py`**

Append a check: for each `public/recipes/*/`, assert `index.html` contains `application/ld+json` and a sibling `index.json` exists and parses as JSON with `"@type": "Recipe"`. (Follow the file's existing per-page assertion style; add to its checks list.)

- [ ] **Step 7: Run smoke + commit**

```bash
python3 tools/check_smoke.py
git add hugo.yaml layouts/partials/recipes/schema-recipe.html layouts/recipes/single.recipe.json layouts/partials/head.html tools/check_smoke.py
git commit -m "feat(recipes): schema.org/Recipe JSON-LD + RECIPE download output format"
```

---

### Task 6: Single-page template + partials + CSS §50

**Files:**
- Create: `layouts/recipes/single.html`
- Create: `layouts/partials/recipes/rail.html`
- Create: `layouts/partials/recipes/sources.html`
- Modify: `assets/css/main.css` (add §50)

**Interfaces:**
- Consumes: the frontmatter contract (Task 1), the RECIPE output permalink (Task 5) via `.OutputFormats.Get "RECIPE"`.
- Produces: DOM the scaler (Task 8) binds to — a rail containing `<script type="application/json" class="recipe-data">` (the `x-ingredients` array), `.recipe-serves` input, `.recipe-mult` input, and `<ul class="recipe-ing">` with `<li data-i="N">` per ingredient.

- [ ] **Step 1: Write `single.html`**

`layouts/recipes/single.html`:
```go-html-template
{{ define "main" }}
{{ $total := or .Params.total_minutes (add (default 0 .Params.prep_minutes) (default 0 .Params.cook_minutes)) }}
<article class="recipe">
  <header class="recipe-head">
    <div class="recipe-kicker">{{ .Params.cuisine }}{{ with .Params.category }} · {{ . }}{{ end }}</div>
    <h1>{{ .Title }}</h1>
    {{ with .Params.summary }}<p class="recipe-note">{{ . }}</p>{{ end }}
    <div class="recipe-meta">
      {{ with .Params.prep_minutes }}Prep {{ . }}&nbsp;min · {{ end }}
      {{ with .Params.cook_minutes }}Cook {{ . }}&nbsp;min · {{ end }}
      Total {{ $total }}&nbsp;min
      {{ with .OutputFormats.Get "RECIPE" }}
        · <a class="recipe-dl" href="{{ .RelPermalink }}" download>⬇ Download recipe (.json)</a>
      {{ end }}
    </div>
  </header>

  <div class="recipe-body">
    {{ partial "recipes/rail.html" . }}
    <div class="recipe-steps-col">
      <h2 class="recipe-sec">Steps</h2>
      <ol class="recipe-steps">
        {{ range .Params.steps }}
          <li>{{ replaceRE `^\[\d{1,2}:[0-5]\d(?:\.\d{1,2})?\]\s*` "" . }}</li>
        {{ end }}
      </ol>
      {{ with .Content }}<div class="recipe-headnote">{{ . }}</div>{{ end }}
    </div>
  </div>

  {{ partial "recipes/sources.html" . }}
</article>
{{ end }}
```

- [ ] **Step 2: Write `rail.html`** (ingredients + scaler + data island)

`layouts/partials/recipes/rail.html`:
```go-html-template
<aside class="recipe-rail" data-base-servings="{{ .Params.servings }}">
  <div class="recipe-scaler">
    <label>Serves
      <span class="recipe-stp">
        <button type="button" class="recipe-minus" aria-label="fewer servings">–</button>
        <input class="recipe-serves numin" type="number" min="1" max="99"
               value="{{ .Params.servings }}" inputmode="decimal" aria-label="servings">
        <button type="button" class="recipe-plus" aria-label="more servings">+</button>
      </span>
    </label>
    <span class="recipe-mult-wrap">
      <input class="recipe-mult" type="number" min="0.1" max="20" step="0.25"
             value="1" inputmode="decimal" aria-label="multiplier"><span class="recipe-x">×</span>
    </span>
  </div>
  <h2 class="recipe-sec">Ingredients</h2>
  <ul class="recipe-ing">
    {{ range $i, $ing := .Params.ingredients }}
      <li data-i="{{ $i }}">
        {{ with $ing.qty }}<span class="q">{{ . }}{{ with $ing.unit }} {{ . }}{{ end }}</span> {{ end }}
        {{ $ing.item }}{{ with $ing.note }}, <span class="alt">{{ . }}</span>{{ end }}{{ with $ing.alt }} <span class="alt">(or {{ . }})</span>{{ end }}
      </li>
    {{ end }}
  </ul>
  <script type="application/json" class="recipe-data">{{ .Params.ingredients | jsonify }}</script>
</aside>
```

- [ ] **Step 3: Write `sources.html`**

`layouts/partials/recipes/sources.html`:
```go-html-template
<section class="recipe-sources">
  <h2 class="recipe-sec">Sources</h2>
  <ul>
    {{ range .Params.sources }}
      <li>{{ with .url }}<a href="{{ . }}">{{ $.name }}</a>{{ else }}{{ .name }}{{ end }}{{ with .note }} <span class="alt">· {{ . }}</span>{{ end }}</li>
    {{ end }}
  </ul>
</section>
```
(If `$.name` mis-scopes, bind `{{ $n := .name }}` before the `with .url`. Verify in Step 5.)

- [ ] **Step 4: Add CSS §50**

Append to `assets/css/main.css` a `/* §50 — Recipes */` block porting the validated mockup styles (`recipe-scaling-dual-v2.html`, `recipe-index.html`) to real tokens: `.recipe` reading layout; `.recipe-body{display:flex;gap:var(--space-2xl)}`; `.recipe-rail{flex:0 0 42%;position:sticky;top:var(--space-lg);background:var(--color-tile);border:1px solid var(--color-rule);border-radius:8px;padding:var(--space-md) var(--space-lg)}`; `.recipe-steps-col{flex:1}`; numbered `.recipe-steps li` with burgundy circle markers; `.recipe-serves`/`.recipe-mult` chrome (dashed-underline × field); `.recipe-dl` bordered burgundy pill; `.q.changed{color:var(--color-burgundy)}`; `.alt{color:var(--color-ink-fade);font-style:italic}`; and `@media (max-width: 720px){ .recipe-body{flex-direction:column} .recipe-rail{position:static;flex-basis:auto} }`. Match the canonical breakpoint scale (§ breakpoints comment) and `--space-*` tokens (guarded by `check_spacing_tokens.py` / `check_breakpoints.py`).

- [ ] **Step 5: Build + verify render**

Run: `hugo --quiet && python3 tools/check_css_refs.py && python3 tools/check_spacing_tokens.py && python3 tools/check_breakpoints.py`
Expected: build OK; the three guards pass (add any new class to `tools/css-refs-allowlist.txt` only if genuinely dynamic — these are static, so no allowlist needed).

- [ ] **Step 6: Commit**

```bash
git add layouts/recipes/single.html layouts/partials/recipes/rail.html layouts/partials/recipes/sources.html assets/css/main.css
git commit -m "feat(recipes): single-page template (two-column rail + steps) + CSS §50"
```

---

### Task 7: Index page + filter chips + Pagefind meta

**Files:**
- Create: `layouts/recipes/list.html`
- Create: `layouts/partials/recipes/card.html`
- Modify: `data/filter-chips.yaml` (add a `recipes` section if curated tags are wanted — optional)

**Interfaces:**
- Consumes: `partials/filter-chips.html` with `setupFilterChips` contract — cards need `data-tags` (space-delimited) + `data-<dim>` attrs; chips container + card selector wired in Task 8.

- [ ] **Step 1: Write `card.html`**

`layouts/partials/recipes/card.html`:
```go-html-template
{{ $total := or .Params.total_minutes (add (default 0 .Params.prep_minutes) (default 0 .Params.cook_minutes)) }}
<a class="recipe-card" href="{{ .RelPermalink }}"
   data-cuisine="{{ .Params.cuisine }}" data-category="{{ .Params.category }}"
   data-time="{{ $total }}" data-tags="{{ delimit .Params.tags " " }}">
  <div class="recipe-card-kicker">{{ .Params.cuisine }}{{ with .Params.category }} · {{ . }}{{ end }}</div>
  <h3>{{ .Title }}</h3>
  <p class="recipe-card-sum">{{ .Params.summary }}</p>
  <div class="recipe-card-foot"><span>⏱ {{ $total }} min</span><span>{{ .Params.servings }} {{ default "servings" .Params.yield_unit }}</span></div>
</a>
```

- [ ] **Step 2: Write `list.html`** (header + filter chips + grid)

`layouts/recipes/list.html`:
```go-html-template
{{ define "main" }}
<div class="recipe-index">
  <h1>{{ .Title }}</h1>
  {{ with .Content }}<div class="recipe-lede">{{ . }}</div>{{ end }}
  {{ partial "filter-chips.html" (dict
      "page" .
      "pages" .Pages
      "dims" (slice
        (dict "key" "cuisine" "label" "Cuisine" "attr" "data-cuisine")
        (dict "key" "category" "label" "Course" "attr" "data-category"))
  ) }}
  <div class="recipe-grid" id="recipe-grid">
    {{ range .Pages }}{{ partial "recipes/card.html" . }}{{ end }}
  </div>
</div>
{{ end }}
```
Note: pass whatever dict shape `partials/filter-chips.html` actually expects — inspect it and match its documented params (Cuisine/Course dims; Time-bucket + tags may need a small derived `data-time` bucket helper). Adjust to the real contract; the E2E in Task 9 gates behavior.

- [ ] **Step 3: Add Pagefind meta to `single.html`**

In `single.html` header, add hidden spans (one key per element — Pagefind 1.x rule):
```go-html-template
<span data-pagefind-meta="section:recipes" hidden></span>
<span data-pagefind-filter="section:recipes" hidden></span>
{{ with .Params.cuisine }}<span data-pagefind-meta="cuisine:{{ . }}" hidden></span>{{ end }}
{{ with .Params.category }}<span data-pagefind-meta="category:{{ . }}" hidden></span>{{ end }}
```

- [ ] **Step 4: Build + verify index**

Run: `hugo --quiet && test -f public/recipes/index.html && grep -q recipe-card public/recipes/index.html && echo OK`
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add layouts/recipes/list.html layouts/partials/recipes/card.html data/filter-chips.yaml
git commit -m "feat(recipes): filterable index + cards + Pagefind meta"
```

---

### Task 8: JS entry wiring (scaler DOM binding + filter chips)

**Files:**
- Create: `assets/js/entry-recipes.js`
- Modify: `layouts/partials/scripts.html` (register the entry)

**Interfaces:**
- Consumes: `recipe-scale.js` (`formatQuantity`), `filter-chips.js` (`setupFilterChips`), the DOM from Tasks 6–7.

- [ ] **Step 1: Write `entry-recipes.js`**

`assets/js/entry-recipes.js`:
```javascript
import { formatQuantity } from './recipe-scale.js';
import { setupFilterChips } from './filter-chips.js';

function initScaler(rail) {
  const base = parseFloat(rail.dataset.baseServings) || 1;
  const data = JSON.parse(rail.querySelector('.recipe-data').textContent);
  const serves = rail.querySelector('.recipe-serves');
  const mult = rail.querySelector('.recipe-mult');
  const items = rail.querySelectorAll('.recipe-ing li');

  function apply(r) {
    items.forEach((li) => {
      const ing = data[+li.dataset.i];
      const q = li.querySelector('.q');
      if (!q || ing.qty == null) return;
      const val = ing.qty * r;
      q.textContent = formatQuantity(val, ing.unit) + (ing.unit ? ' ' + ing.unit : '');
      q.classList.toggle('changed', Math.abs(r - 1) > 1e-9);
    });
  }
  const clean = (n) => (Math.round(n * 100) / 100).toString();
  function fromServings() {
    let s = parseFloat(serves.value); if (!(s > 0)) s = base;
    const r = s / base; mult.value = clean(r); apply(r);
  }
  function fromMult() {
    let r = parseFloat(mult.value); if (!(r > 0)) r = 1;
    serves.value = clean(base * r); apply(r);
  }
  serves.addEventListener('input', fromServings);
  mult.addEventListener('input', fromMult);
  rail.querySelector('.recipe-minus').addEventListener('click', () => { serves.value = Math.max(1, (parseFloat(serves.value) || base) - 1); fromServings(); });
  rail.querySelector('.recipe-plus').addEventListener('click', () => { serves.value = Math.min(99, (parseFloat(serves.value) || base) + 1); fromServings(); });
  fromServings();
}

document.querySelectorAll('.recipe-rail').forEach(initScaler);

if (document.getElementById('recipe-grid')) {
  setupFilterChips({ containerSelector: '.filter-chips', cardSelector: '.recipe-card' });
}
```
Note: match `setupFilterChips`'s real option names (see `assets/js/filter-chips.js` and existing callers like `entry-streams.js`).

- [ ] **Step 2: Register the entry in `scripts.html`**

Mirror the streams block. Add near the other entries:
```go-html-template
{{- if eq .Section "recipes" }}
{{- $recipesOpts := dict "minify" hugo.IsProduction "targetPath" "js/recipes.js" }}
{{- $recipes := resources.Get "js/entry-recipes.js" | js.Build $recipesOpts | fingerprint }}
<script src="{{ $recipes.RelPermalink }}" integrity="{{ $recipes.Data.Integrity }}" defer></script>
{{- end }}
```
(Copy the exact `*Opts` shape used by the sibling `$streamsOpts` in the same file.)

- [ ] **Step 3: Build + verify the bundle loads**

Run: `hugo --quiet && grep -q 'recipes\.' public/recipes/example-recipe-one/index.html && echo OK`
Expected: `OK` (the fingerprinted `recipes.<hash>.js` script tag is present).

- [ ] **Step 4: Commit**

```bash
git add assets/js/entry-recipes.js layouts/partials/scripts.html
git commit -m "feat(recipes): entry bundle — scaler DOM binding + filter chips"
```

---

### Task 9: E2E smoke spec

**Files:**
- Create: `tests/e2e/recipes.spec.js`

**Interfaces:**
- Consumes: the built `public/` (Playwright config serves it, per existing specs).

- [ ] **Step 1: Write the spec** (mirror an existing `tests/e2e/*.spec.js` for setup/serve)

`tests/e2e/recipes.spec.js`:
```javascript
const { test, expect } = require('@playwright/test');

test('recipe renders ingredients + steps and scales', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  await expect(page.locator('.recipe-ing li').first()).toBeVisible();
  await expect(page.locator('.recipe-steps li')).toHaveCount(4);
  const oil = page.locator('.recipe-ing li', { hasText: 'olive oil' }).locator('.q');
  await expect(oil).toHaveText('2 tbsp');
  await page.fill('.recipe-serves', '8');
  await expect(oil).toHaveText('4 tbsp');
});

test('recipe download link points to a JSON Recipe', async ({ page }) => {
  await page.goto('/recipes/example-recipe-one/');
  const href = await page.locator('.recipe-dl').getAttribute('href');
  const res = await page.request.get(href);
  const body = await res.json();
  expect(body['@type']).toBe('Recipe');
});

test('index filters cards', async ({ page }) => {
  await page.goto('/recipes/');
  await expect(page.locator('.recipe-card')).toHaveCount(3);
});
```

- [ ] **Step 2: Run E2E**

Run: `hugo --quiet && npx pagefind@1.5.2 --site public/ >/dev/null 2>&1; npx playwright test tests/e2e/recipes.spec.js`
Expected: 3 passing (adjust the scaled-value expectation if the ingredient order differs).

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/recipes.spec.js
git commit -m "test(recipes): E2E — render, scale, download, index filter"
```

---

### Task 10: Nav + CI wiring

**Files:**
- Modify: `layouts/partials/header.html` (add Recipes after Streams)
- Modify: `.github/workflows/hugo.yaml` (run the 2 linter pairs + node unit tests)
- Modify: `tools/ci-local.sh` (mirror)

- [ ] **Step 1: Add the nav item**

In `layouts/partials/header.html`, insert between the Streams and About dicts:
```go-html-template
        (dict "url" "/recipes/" "label" "Recipes")
```
(Placement: after `/streams/`, before `/about/`.)

- [ ] **Step 2: Wire linters into CI**

In `.github/workflows/hugo.yaml`, add (in the pre-build linter block, each linter then its test — following the existing pattern):
```yaml
      - name: Recipe fixtures linter
        run: python3 tools/check_recipes_fixtures.py
      - name: Recipe fixtures linter tests
        run: python3 tools/test_check_recipes_fixtures.py
      - name: Recipe links linter
        run: python3 tools/check_recipes_links.py
      - name: Recipe links linter tests
        run: python3 tools/test_check_recipes_links.py
```
And after the Node setup step (near the Playwright step):
```yaml
      - name: JS unit tests
        run: node --test tests/unit/
```

- [ ] **Step 3: Mirror in `tools/ci-local.sh`**

Add the four linter/test invocations to the linter list, and a Node-guarded `node --test tests/unit/` near the Playwright block (loud-skip if Node absent, matching the existing Playwright guard).

- [ ] **Step 4: Run the full local gate**

Run: `bash tools/ci-local.sh`
Expected: all linters + tests green (LHCI may stop locally on chromium — expected per repo convention).

- [ ] **Step 5: Commit**

```bash
git add layouts/partials/header.html .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "feat(recipes): nav entry + CI wiring (linters + JS unit tests)"
```

---

### Task 11: Docs — CLAUDE.md drift

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the linter roster + counts**

In the linter list: add the recipe fixtures + links pairs; bump "Thirty-three linter pairs" → the new count; add `entry-recipes.js` to the JS multi-entry table; add "Recipes" to the top-nav list; add `content/recipes/` to the content sections; note CSS §50; note the `RECIPE` output format + the first JSON-LD emission; note `tests/unit/` (`node --test`) as a new client-side unit layer alongside Playwright.

- [ ] **Step 2: Verify counts**

Run: `ls tools/check_*.py | wc -l` and reconcile the prose numbers.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: CLAUDE.md — recipes section, entry-recipes, §50, RECIPE output, node unit tests"
```

---

## Self-Review

**Spec coverage:** req 1 sources → Tasks 1/6 (`sources.html`); req 2 minimal/house-style → Tasks 6/7 + CSS §50; req 3 standard + download → Task 5 (schema partial, RECIPE output, JSON-LD); req 6 scaling → Tasks 4/8; index → Task 7; nav/search/Pagefind → Tasks 7/10; fixtures + linters → Tasks 1–3; E2E → Task 9; docs → Task 11. Synced video (req 4) / meal-prep (req 7) / org authoring correctly deferred per spec.

**Placeholder scan:** template partials (`schema-recipe.html`, `list.html` filter-chips dict, CSS §50, `setupFilterChips` options) carry explicit "match the real contract — verify in build/E2E" notes rather than invented signatures, because those three interfaces (`partials/filter-chips.html` param dict, `setupFilterChips` option names, the exact RECIPE output filename) are repo-specific and MUST be read from source at implementation time. Every Python/JS unit (the true TDD surface) is complete and runnable. This is a deliberate, flagged boundary, not a hidden gap.

**Type consistency:** `formatQuantity(value, unit)` / `unitMode(unit)` names match across Task 4 (def), Task 8 (use), and the unit test. Frontmatter field names are fixed in Task 1 and reused verbatim in Tasks 2/5/6/7. `run(repo_root) -> (int, list[str])` uniform across both linters.

## Execution note

Two interfaces are intentionally verify-at-build (flagged inline): the `partials/filter-chips.html` param dict, `setupFilterChips`'s option names, and the RECIPE output permalink/filename. The first implementer task touching each MUST open the referenced source file and match it exactly before writing the consumer.
