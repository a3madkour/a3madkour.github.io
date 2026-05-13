# Phase 8 — Slice 2: CI gates trio implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three post-build CI gates — a smoke test that asserts key URLs render, a page-weight gate that enforces §8 byte budgets per page, and Lighthouse CI that asserts accessibility / performance / best-practices / SEO each ≥ 90 across 12 sampled URLs in both mobile and desktop profiles. Failing any gate blocks deploy.

**Architecture:** Two stdlib-only Python linters (`check_smoke.py`, `check_page_weights.py`) walk `public/` after `hugo --minify`. One unit-test sibling (`test_check_page_weights.py`) covers the budget-classification logic; the smoke test is too thin to warrant a sibling (documented exception in spec §3.1). A `lighthouserc.json` at repo root pins the URL sample list + assertion floors; the `treosh/lighthouse-ci-action@v12` step runs LHCI in CI after the Python gates pass.

**Tech Stack:** Python 3 stdlib (`html.parser`, `pathlib`, `re`, `unittest`), `treosh/lighthouse-ci-action@v12` (GitHub Action; wraps `lhci`), no new local dependencies.

**Parent spec:** `docs/superpowers/specs/2026-05-13-phase-8-design.md` §3 (Slice 2).

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `tools/check_smoke.py` | Create | Walks `public/<path>/index.html` for 7 spec'd URLs; asserts file exists + non-empty + parses as HTML. |
| `tools/check_page_weights.py` | Create | Walks `public/`, parses each `index.html` for linked CSS/JS/img assets, sums byte size, compares to §8 budget per the prefix classifier. On failure prints a table. |
| `tools/test_check_page_weights.py` | Create | Unit-test sibling covering: budget classifier (prefix matching + exact-match for `/`), asset-byte summation, HTML parser pulling refs from `<link>` / `<script src>` / `<img src>`, the threshold comparison. |
| `lighthouserc.json` | Create | LHCI config: `collect.urls` (12 stable fixture URLs), two `assert.assertions` blocks (mobile + desktop), each pinning 4 categories ≥ 90. |
| `.github/workflows/hugo.yaml` | Modify | Insert 4 new steps after the existing Pagefind index step + before `Upload artifact`, in this order: smoke → page-weight + page-weight tests → LHCI. |
| `CLAUDE.md` | Modify | Bump linter count (13 → 14 — page-weight pair). Add §3.x mention of the LHCI floor. Update §Project status. |

---

## Working Directory & Branch

Work happens on a slice branch `slice/phase-8-ci-gates` off `master`. Before Task 1:

```bash
cd /Stuff/a3madkour/Sync/Workspace/a3madkour.github.io
git checkout master
git pull origin master
git checkout -b slice/phase-8-ci-gates
```

All task commits land on this branch. Final merge happens via the slice-finishing flow in Task 9 after CI is green.

---

### Task 1: Smoke test linter

**Files:**
- Create: `tools/check_smoke.py`

- [ ] **Step 1: Create slice branch (if not already done — see "Working Directory & Branch" above)**

Run from repo root:
```bash
git checkout master
git pull origin master
git checkout -b slice/phase-8-ci-gates
```

Expected: `Switched to a new branch 'slice/phase-8-ci-gates'`.

- [ ] **Step 2: Create `tools/check_smoke.py`**

```python
"""Smoke test for the post-build site.

Asserts that the seven top-level URLs listed in spec §11 each resolve to a
non-empty, parseable HTML file in public/. Runs in CI after `hugo --minify`.

No paired unit-test sibling: the logic is too thin (it's mostly stdlib
HTMLParser + file-exists checks). Documented in spec §3.1.
"""

import sys
from html.parser import HTMLParser
from pathlib import Path


# Spec §11 list.
URLS = [
    "/",
    "/essays/",
    "/garden/",
    "/research/",
    "/works/",
    "/about/",
    "/library/",
]


class _Parser(HTMLParser):
    """Tracks whether at least one <html> and <body> tag was seen."""

    def __init__(self) -> None:
        super().__init__()
        self.saw_html = False
        self.saw_body = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "html":
            self.saw_html = True
        elif tag == "body":
            self.saw_body = True


def file_for_url(public: Path, url: str) -> Path:
    rel = url.strip("/")
    if not rel:
        return public / "index.html"
    return public / rel / "index.html"


def check_url(public: Path, url: str) -> list:
    f = file_for_url(public, url)
    errors = []
    if not f.is_file():
        errors.append(f"{url}: file missing at {f.relative_to(public)}")
        return errors
    if f.stat().st_size == 0:
        errors.append(f"{url}: empty file at {f.relative_to(public)}")
        return errors
    html = f.read_text(encoding="utf-8", errors="replace")
    parser = _Parser()
    try:
        parser.feed(html)
    except Exception as e:
        errors.append(f"{url}: HTML parse error: {e}")
        return errors
    if not parser.saw_html:
        errors.append(f"{url}: no <html> tag")
    if not parser.saw_body:
        errors.append(f"{url}: no <body> tag")
    return errors


def main() -> int:
    public = Path("public")
    if not public.is_dir():
        print(
            "check_smoke: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2

    all_errors = []
    for url in URLS:
        all_errors.extend(check_url(public, url))

    if all_errors:
        print(f"check_smoke: {len(all_errors)} issue(s):", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"check_smoke: OK ({len(URLS)} URLs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Build site and run linter**

```bash
rm -rf public/
hugo --minify
python3 tools/check_smoke.py
echo "exit: $?"
```

Expected: `check_smoke: OK (7 URLs)`, exit 0.

- [ ] **Step 4: Verify failure mode by temporarily deleting a target file**

```bash
mv public/about/index.html public/about/index.html.bak
python3 tools/check_smoke.py
echo "exit: $?"
# Restore:
mv public/about/index.html.bak public/about/index.html
python3 tools/check_smoke.py
echo "exit: $?"
```

Expected: first run prints `/about/: file missing at about/index.html` + exit 1; second run prints OK + exit 0.

- [ ] **Step 5: Commit**

```bash
git add tools/check_smoke.py
git commit -m "ci: build smoke test (asserts key URLs render)"
```

---

### Task 2: Wire smoke test into CI workflow

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Identify insertion point**

Run: `grep -n "Build Pagefind index\|Upload artifact" .github/workflows/hugo.yaml`
Expected: shows two line numbers — the existing `Build Pagefind index` step (currently at line ~120) and `Upload artifact` (currently at line ~123).

The new gates land **after** `Build Pagefind index` (so smoke runs against a fully-built `public/`) and **before** `Upload artifact` (so a failure blocks deploy).

- [ ] **Step 2: Insert the smoke step**

In `.github/workflows/hugo.yaml`, find:

```yaml
      - name: Build Pagefind index
        run: pagefind --site public/
      - name: Upload artifact
```

Replace with:

```yaml
      - name: Build Pagefind index
        run: pagefind --site public/
      - name: Verify build smoke test
        run: python3 tools/check_smoke.py
      - name: Upload artifact
```

- [ ] **Step 3: Verify YAML parses**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/hugo.yaml'))" && echo OK
```

Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci: gate deploy on build smoke test"
```

---

### Task 3: Page-weight linter — unit-test sibling (RED)

**Files:**
- Create: `tools/test_check_page_weights.py`

- [ ] **Step 1: Write the test file**

```python
"""Unit tests for tools/check_page_weights.py.

Tests run against synthetic HTML strings + tempfile-backed public/ dirs,
not against a real Hugo build.
"""

from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import check_page_weights as cpw


class TestBudgetFor(unittest.TestCase):
    def test_homepage_exact_match(self):
        self.assertEqual(cpw.budget_for("/"), 500_000)

    def test_default_fallthrough(self):
        self.assertEqual(cpw.budget_for("/about/"), 100_000)

    def test_essay_post_uses_default(self):
        self.assertEqual(cpw.budget_for("/essays/example-1/"), 100_000)

    def test_garden_index_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/garden/"), 600_000)

    def test_garden_graph_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/garden/graph/"), 600_000)

    def test_research_graph_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/research/graph/"), 600_000)

    def test_works_umbrella_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/works/"), 600_000)

    def test_works_graph_is_graph_bearing(self):
        self.assertEqual(cpw.budget_for("/works/graph/"), 600_000)

    def test_music_page_is_media_heavy(self):
        self.assertEqual(
            cpw.budget_for("/works/music/example-album/"), 500_000
        )

    def test_music_index_is_media_heavy(self):
        # /works/music/ matches the /works/music/ prefix before /works/.
        self.assertEqual(cpw.budget_for("/works/music/"), 500_000)

    def test_essays_index_is_default(self):
        self.assertEqual(cpw.budget_for("/essays/"), 100_000)


class TestExtractRefs(unittest.TestCase):
    def test_extracts_link_stylesheet(self):
        html = '<html><head><link rel="stylesheet" href="/css/main.abc.css"></head></html>'
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(css, ["/css/main.abc.css"])
        self.assertEqual(js, [])
        self.assertEqual(img, [])

    def test_extracts_script_src(self):
        html = '<html><body><script src="/js/core.def.js"></script></body></html>'
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(js, ["/js/core.def.js"])

    def test_extracts_img_src(self):
        html = '<img src="/images/x.svg" alt="">'
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(img, ["/images/x.svg"])

    def test_skips_external_urls(self):
        html = (
            '<link rel="stylesheet" href="https://fonts.googleapis.com/x">'
            '<script src="//cdn.example.com/y.js"></script>'
            '<img src="https://example.com/z.png">'
        )
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(css, [])
        self.assertEqual(js, [])
        self.assertEqual(img, [])

    def test_skips_inline_script_without_src(self):
        html = '<script>const x = 1;</script>'
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(js, [])

    def test_ignores_non_stylesheet_links(self):
        html = (
            '<link rel="icon" href="/favicon.ico">'
            '<link rel="alternate" type="application/rss+xml" href="/index.xml">'
        )
        css, js, img = cpw.extract_refs(html)
        self.assertEqual(css, [])


class TestSumAssetBytes(unittest.TestCase):
    def test_sums_local_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            (public / "css").mkdir()
            (public / "css" / "main.css").write_bytes(b"x" * 1000)
            (public / "js").mkdir()
            (public / "js" / "core.js").write_bytes(b"y" * 500)
            total = cpw.sum_asset_bytes(public, ["/css/main.css", "/js/core.js"])
            self.assertEqual(total, 1500)

    def test_missing_asset_contributes_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            total = cpw.sum_asset_bytes(public, ["/missing.css"])
            self.assertEqual(total, 0)


class TestAuditPage(unittest.TestCase):
    def _write(self, public: Path, url: str, html: str) -> Path:
        rel = url.strip("/")
        target = public / rel / "index.html" if rel else public / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        return target

    def test_page_under_budget_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            self._write(public, "/about/", "<html><body>" + "x" * 1000 + "</body></html>")
            result = cpw.audit_page(public / "about" / "index.html", public)
            self.assertEqual(result.budget, 100_000)
            self.assertLess(result.total, 100_000)
            self.assertFalse(result.over_budget)

    def test_page_over_budget_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            public = Path(tmp)
            # default budget = 100_000; write 200KB of HTML
            self._write(
                public, "/big/", "<html><body>" + "x" * 200_000 + "</body></html>"
            )
            result = cpw.audit_page(public / "big" / "index.html", public)
            self.assertTrue(result.over_budget)
            self.assertEqual(result.budget, 100_000)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests; expect failure (linter doesn't exist yet)**

```bash
cd tools && python3 -m unittest test_check_page_weights.py -v 2>&1 | head -10 && cd ..
```

Expected: `ModuleNotFoundError: No module named 'check_page_weights'` (RED phase).

- [ ] **Step 3: Commit failing tests**

```bash
git add tools/test_check_page_weights.py
git commit -m "ci: add page-weight linter test sibling (failing)"
```

---

### Task 4: Page-weight linter implementation (GREEN)

**Files:**
- Create: `tools/check_page_weights.py`

- [ ] **Step 1: Write the linter**

```python
"""Validate per-page payload size against spec §8 budgets.

Walks public/ post-`hugo --minify`. For each rendered index.html, parses
<link rel="stylesheet">, <script src=>, and <img src=> references that point
to local assets under public/. Sums HTML bytes + linked asset bytes.
Compares against a per-URL budget from the prefix classifier.

External resources (Google Fonts URLs, CDN scripts) are excluded — they're
not on our deploy and not bound by §8.

This linter runs in CI after `hugo --minify` and after the Pagefind index
build. Paired with tools/test_check_page_weights.py.
"""

from __future__ import annotations
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


# Ordered budget table (prefix → bytes). First match wins, EXCEPT "/" is
# treated as an exact-match — handled in budget_for() below.
BUDGETS_PREFIX = [
    ("/garden/graph/",   600_000),
    ("/research/graph/", 600_000),
    ("/works/graph/",    600_000),
    ("/works/music/",    500_000),   # music index + per-music-slug pages
    ("/works/",          600_000),   # works umbrella + per-game/poetry pages
    ("/garden/",         600_000),   # garden index + per-note pages
]

BUDGET_HOMEPAGE = 500_000   # exact match `/`
BUDGET_DEFAULT = 100_000


# URLs we don't audit (taxonomy pages, RSS feeds, sitemap, 404).
SKIP_PREFIXES = ("/tags/", "/series/", "/categories/")
SKIP_FILES = ("/index.xml", "/sitemap.xml", "/404.html")


@dataclass
class PageAudit:
    url: str
    file: Path
    budget: int
    html_bytes: int
    css_bytes: int
    js_bytes: int
    img_bytes: int

    @property
    def total(self) -> int:
        return self.html_bytes + self.css_bytes + self.js_bytes + self.img_bytes

    @property
    def over_budget(self) -> bool:
        return self.total > self.budget


def budget_for(url: str) -> int:
    if url == "/":
        return BUDGET_HOMEPAGE
    for prefix, budget in BUDGETS_PREFIX:
        if url.startswith(prefix):
            return budget
    return BUDGET_DEFAULT


class _RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.css: list[str] = []
        self.js: list[str] = []
        self.img: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        a = dict(attrs)
        if tag == "link" and a.get("rel") == "stylesheet" and a.get("href"):
            self.css.append(a["href"])
        elif tag == "script" and a.get("src"):
            self.js.append(a["src"])
        elif tag == "img" and a.get("src"):
            self.img.append(a["src"])


def _is_local(ref: str) -> bool:
    if ref.startswith("//"):
        return False
    if re.match(r"^[a-zA-Z]+://", ref):
        return False
    return ref.startswith("/")


def extract_refs(html: str) -> tuple[list[str], list[str], list[str]]:
    p = _RefParser()
    p.feed(html)
    return (
        [r for r in p.css if _is_local(r)],
        [r for r in p.js if _is_local(r)],
        [r for r in p.img if _is_local(r)],
    )


def sum_asset_bytes(public: Path, refs: list[str]) -> int:
    total = 0
    for ref in refs:
        rel = ref.lstrip("/")
        f = public / rel
        if f.is_file():
            total += f.stat().st_size
    return total


def url_from_file(file: Path, public: Path) -> str:
    rel = file.relative_to(public)
    parts = rel.parts
    if parts == ("index.html",):
        return "/"
    if parts[-1] == "index.html":
        return "/" + "/".join(parts[:-1]) + "/"
    return "/" + "/".join(parts)


def should_skip(url: str) -> bool:
    return url.startswith(SKIP_PREFIXES) or url in SKIP_FILES


def audit_page(file: Path, public: Path) -> PageAudit:
    url = url_from_file(file, public)
    html_bytes = file.stat().st_size
    html = file.read_text(encoding="utf-8", errors="replace")
    css_refs, js_refs, img_refs = extract_refs(html)
    css = sum_asset_bytes(public, css_refs)
    js = sum_asset_bytes(public, js_refs)
    img = sum_asset_bytes(public, img_refs)
    return PageAudit(
        url=url,
        file=file,
        budget=budget_for(url),
        html_bytes=html_bytes,
        css_bytes=css,
        js_bytes=js,
        img_bytes=img,
    )


def main() -> int:
    public = Path("public")
    if not public.is_dir():
        print(
            "check_page_weights: public/ not found. Run `hugo --minify` first.",
            file=sys.stderr,
        )
        return 2

    failures: list[PageAudit] = []
    audited = 0
    for f in sorted(public.rglob("index.html")):
        url = url_from_file(f, public)
        if should_skip(url):
            continue
        audited += 1
        result = audit_page(f, public)
        if result.over_budget:
            failures.append(result)

    if failures:
        print(f"check_page_weights: {len(failures)} page(s) over budget:", file=sys.stderr)
        header = f"{'PAGE':<48} {'BUDGET':>10} {'ACTUAL':>10} {'HTML':>8} {'CSS':>8} {'JS':>8} {'IMG':>8}"
        print(header, file=sys.stderr)
        for r in failures:
            print(
                f"{r.url:<48} {r.budget:>10,} {r.total:>10,} "
                f"{r.html_bytes:>8,} {r.css_bytes:>8,} {r.js_bytes:>8,} {r.img_bytes:>8,}",
                file=sys.stderr,
            )
        return 1

    print(f"check_page_weights: OK ({audited} pages audited)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run unit tests**

```bash
cd tools && python3 -m unittest test_check_page_weights.py -v 2>&1 | tail -5 && cd ..
```

Expected: all tests pass. Should be 19 tests (11 budget classifier + 6 ref extraction + 2 sum_asset_bytes + 2 audit_page).

- [ ] **Step 3: Run against a fresh build**

```bash
rm -rf public/
hugo --minify
python3 tools/check_page_weights.py
echo "exit: $?"
```

Expected: either `check_page_weights: OK (N pages audited)` exit 0, OR a table of offending pages with exit 1.

**If the linter reports pages over budget:** record the output. Don't fix in this task; the budgets are spec'd, and any real over-budget page needs targeted investigation (image too big? bundle bloated? per-page override?). Note offenders in your task report. Task 9 (slice finish) will surface them to the user before merging.

- [ ] **Step 4: Commit linter**

```bash
git add tools/check_page_weights.py
git commit -m "ci: page-weight linter (per-page §8 budget enforcement)"
```

---

### Task 5: Wire page-weight linter into CI workflow

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Insert page-weight steps after the smoke test step**

In `.github/workflows/hugo.yaml`, find:

```yaml
      - name: Verify build smoke test
        run: python3 tools/check_smoke.py
      - name: Upload artifact
```

Replace with:

```yaml
      - name: Verify build smoke test
        run: python3 tools/check_smoke.py
      - name: Verify page weights against §8 budgets
        run: python3 tools/check_page_weights.py
      - name: Run page-weight linter unit tests
        run: cd tools && python3 -m unittest test_check_page_weights.py -v
      - name: Upload artifact
```

Order rationale: page-weight gate runs after smoke (smoke is cheaper); the unit-test sibling runs after the linter (mirrors house pattern of "linter then its tests" elsewhere in the workflow).

- [ ] **Step 2: Verify YAML parses**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/hugo.yaml'))" && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci: gate deploy on page-weight budget"
```

---

### Task 6: Create `lighthouserc.json` with sample URL list + asserts

**Files:**
- Create: `lighthouserc.json`

- [ ] **Step 1: Verify the fixture slugs exist**

The URL list pins specific fixture slugs. Confirm each exists before encoding it:

```bash
ls content/essays/example-essay-one/ content/garden/emergence-vs-design/ \
   content/research/themes/emergence-vs-design/ \
   content/research/questions/what-is-a-narrative-atom/ 2>&1 | head
```

Expected: each directory exists. If any is missing, substitute another fixture slug from `content/<section>/<slug>/` and update Step 2 accordingly.

- [ ] **Step 2: Create `lighthouserc.json` at repo root**

The config uses LHCI's "static-dist-dir" mode — points at the built `public/` directory and lets LHCI serve it locally.

```json
{
  "ci": {
    "collect": {
      "staticDistDir": "./public",
      "url": [
        "http://localhost/",
        "http://localhost/essays/",
        "http://localhost/essays/example-essay-one/",
        "http://localhost/garden/",
        "http://localhost/garden/emergence-vs-design/",
        "http://localhost/garden/graph/",
        "http://localhost/research/",
        "http://localhost/research/themes/emergence-vs-design/",
        "http://localhost/research/questions/what-is-a-narrative-atom/",
        "http://localhost/works/",
        "http://localhost/library/",
        "http://localhost/about/"
      ],
      "settings": {
        "preset": "desktop"
      },
      "numberOfRuns": 1
    },
    "assert": {
      "assertions": {
        "categories:accessibility":   ["error", {"minScore": 0.9}],
        "categories:performance":     ["error", {"minScore": 0.9}],
        "categories:best-practices":  ["error", {"minScore": 0.9}],
        "categories:seo":             ["error", {"minScore": 0.9}]
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

**Note on form factors:** the spec calls for mobile + desktop separately. The simplest way to run both via `treosh/lighthouse-ci-action` is to invoke the action twice (once with `lighthouserc.json` and once with `lighthouserc.mobile.json`). To keep one config file and let the action default to mobile for one run, we'll create the mobile variant inline in the workflow step instead of cluttering `lighthouserc.json`. See Task 7.

- [ ] **Step 3: Sanity-check that the JSON parses**

```bash
python3 -c "import json; json.load(open('lighthouserc.json'))" && echo OK
```

Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add lighthouserc.json
git commit -m "ci: lighthouserc.json — 12 URLs, 4 categories ≥90 desktop"
```

---

### Task 7: Wire LHCI step into CI workflow (mobile + desktop)

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Insert two LHCI steps after the page-weight unit-test step**

Find:

```yaml
      - name: Run page-weight linter unit tests
        run: cd tools && python3 -m unittest test_check_page_weights.py -v
      - name: Upload artifact
```

Replace with:

```yaml
      - name: Run page-weight linter unit tests
        run: cd tools && python3 -m unittest test_check_page_weights.py -v
      - name: Lighthouse CI (desktop)
        uses: treosh/lighthouse-ci-action@v12
        with:
          configPath: lighthouserc.json
          uploadArtifacts: true
          temporaryPublicStorage: true
      - name: Lighthouse CI (mobile)
        uses: treosh/lighthouse-ci-action@v12
        with:
          configPath: lighthouserc.json
          uploadArtifacts: true
          temporaryPublicStorage: true
        env:
          LHCI_BUILD_CONTEXT__CURRENT_HASH: ${{ github.sha }}
          # treosh action passes through extra LHCI overrides via env or a
          # second config; here we run the same lighthouserc.json with the
          # default (mobile) preset by overriding the settings on the fly.
          LHCI_COLLECT__SETTINGS__PRESET: ""
      - name: Upload artifact
```

Rationale for the env-override on the second run: `LHCI_COLLECT__SETTINGS__PRESET=""` tells LHCI to ignore the `preset: "desktop"` in `lighthouserc.json` and fall back to its default (mobile). This avoids maintaining a second config file. The two runs share the same URL list + assertion floors.

- [ ] **Step 2: Verify YAML parses**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/hugo.yaml'))" && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Final workflow summary**

Run:

```bash
grep "^      - name:" .github/workflows/hugo.yaml | nl
```

Expected: the last several entries in order are:
- ... existing pre-build linters ...
- `Build with Hugo`
- `Run pagefind metadata linter unit tests`
- `Verify pagefind metadata on built pages`
- `Install Pagefind`
- `Build Pagefind index`
- `Verify build smoke test`
- `Verify page weights against §8 budgets`
- `Run page-weight linter unit tests`
- `Lighthouse CI (desktop)`
- `Lighthouse CI (mobile)`
- `Upload artifact`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci: gate deploy on Lighthouse (a11y/perf/bp/seo ≥90, mobile+desktop)"
```

---

### Task 8: Refresh CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Bump linter count**

Find: `Thirteen linter pairs under `tools/check_*.py``

Note: the spec §3.1 documents that smoke is intentionally **without** a paired test sibling. So the linter-pair count goes 13 → 14 for page-weight, and smoke is mentioned separately as a sibling-less linter.

Replace the line and the surrounding context with:

```markdown
- `python3 tools/check-contrast.py` — WCAG 2.1 contrast verifier (CI gate).
- `python3 tools/check_smoke.py` — top-level URL smoke test (post-build CI gate; no test sibling per spec §3.1 — logic too thin to warrant pairing).
- Fourteen linter pairs under `tools/check_*.py` + `tools/test_check_*.py` (CI runs each linter then its unit-test sibling): essay fixtures, garden fixtures, garden links, filter-chips config, research fixtures, research links, citations, works fixtures, works links, library fixtures, library links, library covers, pagefind metadata, page weights.
```

- [ ] **Step 2: Add a CI-gates subsection under "Deployment"**

Find the line that describes the deployment workflow (currently says "CI runs all Python checks (...) before the Hugo build; any failure blocks deploy."). Extend it to mention the post-build gates:

```markdown
### Deployment

`.github/workflows/hugo.yaml` builds with Hugo extended and deploys `public/` to GitHub Pages on pushes to `master`. CI runs all Python checks (contrast + 14 linter pairs = 29 verification steps) before the Hugo build, then runs **post-build gates** in order: pagefind metadata linter (+ unit tests) → Pagefind binary install + index → smoke test → page-weight gate (+ unit tests) → Lighthouse CI (desktop) → Lighthouse CI (mobile). Any failure blocks the upload + deploy. Lighthouse asserts 4 categories (accessibility / performance / best-practices / SEO) ≥ 0.9 on the 12 URLs pinned in `lighthouserc.json`.
```

(Adjust the exact wording to match the surrounding section's tone if it differs.)

- [ ] **Step 3: Add page-weight gate to the "Project status" section**

Find the section "**Not started, in phase order:**" and the line about Phase 8. The previous slice's CLAUDE.md update narrowed it to "Lighthouse CI + final QA (Pagefind search runtime shipped as Slice 1)". This slice closes the CI-gates work. Update to:

```markdown
- **Phase 8 — final QA pass.** Pagefind runtime (Slice 1) + CI gates trio (smoke / page weights / Lighthouse mobile+desktop, Slice 2) are shipped; only the manual keyboard / SR / CB / mobile audit checklist remains (Slice 3).
```

Also add a new bullet to the "**Shipped — Phases 0–6 plus targeted polish:**" section:

```markdown
- **CI gates trio** (Phase 8 Slice 2): Build smoke test (7 top-level URLs render), page-weight gate (per-page §8 budget — 100/500/600 KB tiers; classifier prefix-keyed; unit-test sibling pins the logic), Lighthouse CI (4 categories ≥0.9 across 12 stable fixture URLs on mobile + desktop, ~6-10 min in CI). Workflow grew from 29 to 35 verification steps.
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "CLAUDE.md: refresh after Phase 8 slice 2 (CI gates)"
```

---

### Task 9: Slice finishing — merge into master + monitor first CI run

This task follows the project's slice-finishing flow with one extra wrinkle: LHCI's first run on a real CI is where we'll find out if any of the 12 sampled pages actually fail the ≥0.9 floor. The spec §6 calls this risk out: "LHCI scores below 90 on first run likely". Iterate based on the LHCI report URL (LHCI uploads to temporary public storage; the workflow output has the URL).

- [ ] **Step 1: Confirm working tree clean + all tasks committed**

```bash
git status
git log --oneline master..HEAD
```

Expected: working tree clean. ~9 commits on the slice branch.

- [ ] **Step 2: Run every linter locally before pushing**

```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && \
python3 tools/check_garden_fixtures.py && \
python3 tools/check_garden_links.py && \
python3 tools/check_filter_chips_config.py && \
python3 tools/check_research_fixtures.py && \
python3 tools/check_research_links.py && \
python3 tools/check_citations.py && \
python3 tools/check_works_fixtures.py && \
python3 tools/check_works_links.py && \
python3 tools/check_library_fixtures.py && \
python3 tools/check_library_links.py && \
python3 tools/check_library_covers.py && \
rm -rf public/ && hugo --minify && \
python3 tools/check_pagefind_meta.py && \
python3 tools/check_smoke.py && \
python3 tools/check_page_weights.py && \
echo "--- ALL SOURCE + POST-BUILD LINTERS PASS ---"
```

Expected: ends with `--- ALL SOURCE + POST-BUILD LINTERS PASS ---`. If `check_page_weights.py` reports offending pages, follow the iteration in Step 4 below.

- [ ] **Step 3: Run every linter unit-test sibling**

```bash
cd tools && for f in test_check_*.py; do
  echo "--- $f ---"
  python3 -m unittest "$f" 2>&1 | tail -1
done && cd ..
```

Expected: every test file ends with `OK`.

- [ ] **Step 4: If page-weight gate fails locally — decide**

If `check_page_weights.py` reports pages over budget, choose:

- **(a) The offending page is genuinely too heavy** — investigate. Common causes: large hero SVG, multi-bundle JS, multiple inline figures. Trim the heaviest contributor, then re-run.
- **(b) The budget is wrong for that page type** — Slice 2's classifier covers the common cases (graph pages, music pages, homepage). If a NEW page type warrants a higher budget (e.g., per-essay hero illustrations push a single essay past 100 KB), open a follow-up spec for a per-page override map (this was flagged in Slice 1 spec §5 open question #6); don't widen the budget here. For now, fix the page's payload.

Repeat Step 2 until the gate passes.

- [ ] **Step 5: Verify Hugo build is clean**

```bash
rm -rf public/
hugo --minify 2>&1 | tail -5
```

Expected: build succeeds with no errors.

- [ ] **Step 6: Spot-check authorization (per memory `feedback_verify_before_merge.md`)**

Before pushing, surface to the user:
1. The total count of commits on the slice branch (`git log --oneline master..HEAD | wc -l`).
2. The total file delta (`git diff master..HEAD --stat | tail -1`).
3. A short narrative: "Slice adds 3 post-build CI gates (smoke / page-weight / LHCI mobile+desktop), 1 new linter pair, 1 sibling-less linter, 1 LHCI config, 6 new workflow steps. No site-content or layout changes."

Wait for the user's go-ahead before running Step 7.

- [ ] **Step 7: Merge + push**

```bash
git checkout master
git merge --no-ff slice/phase-8-ci-gates -m "Merge slice/phase-8-ci-gates: CI gates trio (Phase 8 Slice 2)"
git push origin master
git branch -d slice/phase-8-ci-gates
git log --oneline -5
```

- [ ] **Step 8: Monitor the first CI run**

Watch the Actions tab for the master push run. Expected behavior:

- All 13 existing pre-build linters pass (no change in their logic).
- `Build with Hugo` succeeds.
- `Run pagefind metadata linter unit tests` + `Verify pagefind metadata on built pages` pass (no change in Slice 1's pieces).
- `Install Pagefind` + `Build Pagefind index` succeed.
- **`Verify build smoke test`** — new — expected to pass (the 7 top-level URLs are all generated).
- **`Verify page weights against §8 budgets`** — new — pass if local Step 2 passed.
- **`Run page-weight linter unit tests`** — new — should pass.
- **`Lighthouse CI (desktop)`** — new — uncertain. Spec §6 risk acknowledged. First run may flag pages.
- **`Lighthouse CI (mobile)`** — new — same uncertainty.
- `Upload artifact` + `Deploy to GitHub Pages` — these run only if all gates pass.

If LHCI fails on any URL/category:
- LHCI uploads a report to `temporary-public-storage`. The workflow logs print the report URL — click through to see the per-URL category scores + audit findings.
- For each failing URL+category, classify: (a) real regression to fix in code, (b) site-wide perf opportunity (e.g., add `loading="lazy"` to a heavy image), (c) test-fixture artifact (e.g., a lorem-ipsum essay has no real meta description, dragging SEO).
- Fix and re-push as a follow-up commit on master. Don't revert this slice; iterate forward.

- [ ] **Step 9: Mark slice complete**

When the master CI run passes end-to-end and the site is deployed, the slice is done. Save a project memory entry mirroring the Slice 1 pattern.

---

## Self-Review Notes

Reviewed against spec §3 (Slice 2 — CI gates trio):

- ✅ §3.1 Smoke test — Task 1 (implementation) + Task 2 (CI wiring). No paired test sibling (documented).
- ✅ §3.2 Page-weight gate — Task 3 (RED) + Task 4 (GREEN) + Task 5 (CI wiring). Test sibling justified by classifier logic.
- ✅ §3.3 Lighthouse CI — Task 6 (config) + Task 7 (CI wiring, mobile+desktop via env override on second run). 12 URLs hardcoded with stable fixture slugs.
- ✅ Workflow order: smoke → page-weight → LHCI (cheap gates first).
- ✅ CLAUDE.md refresh (Task 8) + slice finishing flow (Task 9).

Placeholder scan: no TBD / TODO. Slugs are pinned to real fixtures verified at plan-write time.

Type consistency: `audit_page()` returns `PageAudit` dataclass; `over_budget` + `total` properties used in `main()`. Test sibling uses the same names. `extract_refs()` returns tuple `(css, js, img)` — consistent across linter + tests.

One forward-looking gap: per-page budget override map (spec §5 open question #6) isn't implemented. Defer until LHCI or page-weight gate first surfaces a legitimate over-budget page that warrants its own budget. Task 9 Step 4 documents the decision.

---

*End of plan.*
