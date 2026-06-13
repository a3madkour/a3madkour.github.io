# Tier 7.1 — LHCI sitemap-derived URLs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land `tools/gen_lhci_urls.py` + a Hugo-emitted page manifest so the LHCI URL list regenerates automatically in CI from sitemap + Hugo metadata. Eliminates fixture-retirement breakage; 4.1 (`check_lhci_urls.py`) stays as defense-in-depth.

**Architecture:** Hugo gains a new `LHCI-PAGES` output format that emits `public/lhci-pages.json` (array of `{url, kind, section, type}` per regular page + section + home). A new stdlib-only Python tool reads that manifest + `tools/lhci-overrides.json` (group-keyed assertion thresholds) and rewrites `lighthouserc.{json,mobile.json}` in place — preserving unrelated fields (preset, numberOfRuns, base assertions, upload target). CI workflow inserts the regen between `hugo --minify` and the LHCI steps.

**Tech Stack:** Hugo extended (existing), Python 3 stdlib only (`json`, `pathlib`, `re`, `argparse`), bash + GitHub Actions YAML.

---

## File Map

**New files**
- `layouts/index.lhci-pages.json` — Hugo template emitting the manifest
- `tools/gen_lhci_urls.py` — the generator
- `tools/test_gen_lhci_urls.py` — sibling unit tests (~12 tests)
- `tools/lhci-overrides.json` — group-keyed assertion overrides (committed; hand-edit surface)
- `docs/superpowers/plans/2026-06-12-lhci-sitemap-derived-urls.md` — this file

**Modified files**
- `hugo.yaml` — add `LHCI-PAGES` to `outputs.home` + declare `outputFormats:`
- `lighthouserc.json` — get regenerated; `collect.url` list replaced with alphabetical-first picks; banner header added
- `lighthouserc.mobile.json` — same; `assertMatrix` rebuilt from `lhci-overrides.json`
- `.github/workflows/hugo.yaml` — insert 2 new steps between `check_page_weights` and "Lighthouse CI (desktop)"
- `tools/ci-local.sh` — mirror the workflow insertion
- `CLAUDE.md` — one-line note about LHCI URL list being CI-generated
- `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` — flip Tier 7.1 ☐ → ✓ after merge

**Memory write (post-merge)**
- `.claude/memory/project_tier_7_1_complete.md`
- `.claude/memory/MEMORY.md` — index pointer

---

## Task 1: Hugo output format declaration + template

Adds the manifest emission. Without this, the Python tool has no input.

**Files:**
- Modify: `hugo.yaml`
- Create: `layouts/index.lhci-pages.json`

- [ ] **Step 1: Edit `hugo.yaml` `outputs:` block**

Find:
```yaml
outputs:
  home: [HTML]
  section: [HTML]
  taxonomy: [HTML]
  term: [HTML]
```

Replace with:
```yaml
outputs:
  home: [HTML, LHCI-PAGES]
  section: [HTML]
  taxonomy: [HTML]
  term: [HTML]

# Tier 7.1: LHCI URL manifest. Generates public/lhci-pages.json with
# {url, kind, section, type} per page. Consumed by tools/gen_lhci_urls.py
# to regenerate lighthouserc.{json,mobile.json} in CI.
outputFormats:
  LHCI-PAGES:
    mediaType: application/json
    baseName: lhci-pages
    isPlainText: true
    notAlternative: true
```

- [ ] **Step 2: Create `layouts/index.lhci-pages.json`**

```go-html-template
{{- $pages := slice -}}

{{/* All regular pages (excluding drafts) */}}
{{- range where site.RegularPages "Draft" "!=" true -}}
  {{- $pages = $pages | append (dict
        "url" .RelPermalink
        "kind" .Kind
        "section" .Section
        "type" .Type) -}}
{{- end -}}

{{/* All section indexes (Kind = "section") at any depth */}}
{{- range .Site.Pages -}}
  {{- if eq .Kind "section" -}}
    {{- $pages = $pages | append (dict
          "url" .RelPermalink
          "kind" "section"
          "section" .Section
          "type" .Type) -}}
  {{- end -}}
{{- end -}}

{{/* Home (Kind = "home") */}}
{{- $pages = $pages | append (dict
      "url" "/"
      "kind" "home"
      "section" ""
      "type" "page") -}}

{{- $pages | jsonify -}}
```

- [ ] **Step 3: Build + confirm the manifest exists**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
rm -rf public && hugo --minify --quiet
test -f public/lhci-pages.json && echo "MANIFEST OK"
python3 -c "import json; m = json.load(open('public/lhci-pages.json')); print(f'{len(m)} entries')"
```

Expected: `MANIFEST OK` and entry count > 50.

- [ ] **Step 4: Commit**

```bash
git add hugo.yaml layouts/index.lhci-pages.json
git commit -m "feat(hugo): emit lhci-pages.json manifest via custom output format"
```

---

## Task 2: Smoke-verify manifest covers existing LHCI URLs

Confirms the Hugo template emits everything the current hand-curated lighthouserc URL list expects. If anything is missing (e.g., subsections not iterated), surface it now before any Python work.

**Files:** none modified — verification only.

- [ ] **Step 1: Write a one-shot verification script (don't commit)**

Save to `/tmp/verify_manifest.py`:

```python
import json
from pathlib import Path

repo = Path("/Users/a3madkour/Sync/Workspace/a3madkour.github.io")
manifest = json.loads((repo / "public" / "lhci-pages.json").read_text())
urls = {p["url"] for p in manifest}

expected = {
    "/",
    "/essays/",
    "/essays/example-one/",
    "/garden/",
    "/garden/emergence-vs-design/",
    "/garden/graph/",
    "/research/",
    "/research/themes/example-theme-one/",
    "/research/questions/example-question-one/",
    "/works/",
    "/library/",
    "/about/",
}

missing = expected - urls
if missing:
    print(f"MISSING from manifest: {missing}")
    # Show what manifest does contain for diagnostics:
    print(f"Manifest URLs sample: {sorted(urls)[:20]}")
    exit(1)
print(f"All {len(expected)} currently-LHCI'd URLs present in manifest (total {len(urls)} URLs)")
```

- [ ] **Step 2: Run**

```bash
python3 /tmp/verify_manifest.py
```

Expected: success message, no missing URLs.

If `/garden/graph/` is missing: it's a standalone page (`content/garden/graph.md` or via Hugo magic). Check whether it's a regular page or section; adjust the template's iteration in Task 1.

If `/research/themes/example-theme-one/` is missing: likely the subsection iteration in Task 1 step 2 needs `range .Site.Pages` (already does) — verify the template generates entries for kind=page under research subsections.

- [ ] **Step 3: Clean up**

```bash
rm /tmp/verify_manifest.py
```

No commit (verification only).

---

## Task 3: Python scaffold — `tools/gen_lhci_urls.py` + sibling test

Empty scaffold that runs cleanly; subsequent tasks add real logic via TDD.

**Files:**
- Create: `tools/gen_lhci_urls.py`
- Create: `tools/test_gen_lhci_urls.py`

- [ ] **Step 1: Write the test scaffold (will fail until implementation exists)**

```python
# tools/test_gen_lhci_urls.py
"""Tests for gen_lhci_urls.py — run with:
   python3 -m unittest tools/test_gen_lhci_urls.py -v
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_lhci_urls as gen  # noqa: E402


class Scaffold(unittest.TestCase):
    def test_module_imports(self) -> None:
        self.assertTrue(hasattr(gen, "run"))
        self.assertTrue(hasattr(gen, "main"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run; expect ImportError**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: ImportError / ModuleNotFoundError.

- [ ] **Step 3: Write the minimal generator**

```python
# tools/gen_lhci_urls.py
#!/usr/bin/env python3
"""LHCI URL generator.

Reads public/lhci-pages.json (Hugo-emitted page manifest) and
tools/lhci-overrides.json (group-keyed assertion thresholds).
Rewrites lighthouserc.{json,mobile.json} in place — replacing
collect.url with alphabetical-first picks per (kind, section, type)
group, and rebuilding assertMatrix (mobile only) from overrides.

Stdlib only.
Exits 0 on success, 1 on any error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def run(repo_root: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Programmatic entry. Returns (rc, errors)."""
    return (0, [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate LHCI URL lists from Hugo manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files.")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root, dry_run=args.dry_run)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return rc
    print("gen_lhci_urls: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 1 test PASS.

- [ ] **Step 5: Run the script end-to-end**

```bash
python3 tools/gen_lhci_urls.py
```
Expected: stdout `gen_lhci_urls: OK`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add tools/gen_lhci_urls.py tools/test_gen_lhci_urls.py
git commit -m "feat(lhci): scaffold gen_lhci_urls.py + sibling test"
```

---

## Task 4: `group_pages` — group manifest by (kind, section, type)

**Files:**
- Modify: `tools/gen_lhci_urls.py`
- Modify: `tools/test_gen_lhci_urls.py`

- [ ] **Step 1: Add tests**

Append to `tools/test_gen_lhci_urls.py`:

```python
SAMPLE_MANIFEST = [
    {"url": "/essays/example-one/", "kind": "page", "section": "essays", "type": "essays"},
    {"url": "/essays/example-explorables/", "kind": "page", "section": "essays", "type": "essays"},
    {"url": "/essays/", "kind": "section", "section": "essays", "type": "essays"},
    {"url": "/research/themes/example-theme-one/", "kind": "page", "section": "research", "type": "research-theme"},
    {"url": "/research/questions/example-question-one/", "kind": "page", "section": "research", "type": "research-question"},
    {"url": "/", "kind": "home", "section": "", "type": "page"},
]


class GroupPages(unittest.TestCase):
    def test_groups_by_tuple(self) -> None:
        grouped = gen.group_pages(SAMPLE_MANIFEST)
        self.assertIn("page:essays:essays", grouped)
        self.assertEqual(
            sorted(grouped["page:essays:essays"]),
            ["/essays/example-explorables/", "/essays/example-one/"],
        )
        self.assertIn("section:essays:essays", grouped)
        self.assertIn("home::page", grouped)

    def test_separates_research_theme_from_question(self) -> None:
        grouped = gen.group_pages(SAMPLE_MANIFEST)
        self.assertIn("page:research:research-theme", grouped)
        self.assertIn("page:research:research-question", grouped)
        self.assertNotEqual(
            grouped["page:research:research-theme"],
            grouped["page:research:research-question"],
        )
```

- [ ] **Step 2: Confirm tests fail**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: `GroupPages` tests FAIL (AttributeError: module has no attribute 'group_pages').

- [ ] **Step 3: Implement `group_pages`**

In `tools/gen_lhci_urls.py`, add before `run`:

```python
def group_pages(manifest: list[dict]) -> dict[str, list[str]]:
    """Group manifest entries by (kind, section, type) tuple.
    Returns {group_key: sorted_unique_urls}.
    group_key = "<kind>:<section>:<type>"."""
    groups: dict[str, set[str]] = {}
    for entry in manifest:
        key = f"{entry['kind']}:{entry['section']}:{entry['type']}"
        groups.setdefault(key, set()).add(entry["url"])
    return {k: sorted(v) for k, v in groups.items()}
```

- [ ] **Step 4: Confirm tests pass**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/gen_lhci_urls.py tools/test_gen_lhci_urls.py
git commit -m "feat(lhci): group_pages — tuple-keyed manifest grouping"
```

---

## Task 5: `pick_representative_urls` — alphabetical-first per group

**Files:**
- Modify: `tools/gen_lhci_urls.py`
- Modify: `tools/test_gen_lhci_urls.py`

- [ ] **Step 1: Add tests**

Append to `tools/test_gen_lhci_urls.py`:

```python
class PickRepresentative(unittest.TestCase):
    def test_picks_alphabetical_first(self) -> None:
        picks = gen.pick_representative_urls(SAMPLE_MANIFEST)
        # example-explorables sorts before example-one ('e' < 'o' at offset 8)
        self.assertEqual(picks["page:essays:essays"], "/essays/example-explorables/")
        self.assertEqual(picks["home::page"], "/")

    def test_stable_unicode_sort(self) -> None:
        manifest = [
            {"url": "/garden/zebra/", "kind": "page", "section": "garden", "type": "garden"},
            {"url": "/garden/álpha/", "kind": "page", "section": "garden", "type": "garden"},
        ]
        picks = gen.pick_representative_urls(manifest)
        # Python sorted() is codepoint-ordinal; '/' < 'z'; 'á' (U+00E1) > 'z' (U+007A).
        # So /garden/zebra/ < /garden/álpha/ — zebra wins.
        self.assertEqual(picks["page:garden:garden"], "/garden/zebra/")

    def test_returns_dict_str_to_str(self) -> None:
        picks = gen.pick_representative_urls(SAMPLE_MANIFEST)
        for k, v in picks.items():
            self.assertIsInstance(k, str)
            self.assertIsInstance(v, str)
```

- [ ] **Step 2: Confirm tests fail**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 3 new tests FAIL.

- [ ] **Step 3: Implement**

In `tools/gen_lhci_urls.py`, add after `group_pages`:

```python
def pick_representative_urls(manifest: list[dict]) -> dict[str, str]:
    """Returns {group_key: first_url_alphabetically} per (kind, section, type)."""
    groups = group_pages(manifest)
    return {key: urls[0] for key, urls in groups.items() if urls}
```

- [ ] **Step 4: Confirm tests pass**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 6 tests PASS total.

- [ ] **Step 5: Commit**

```bash
git add tools/gen_lhci_urls.py tools/test_gen_lhci_urls.py
git commit -m "feat(lhci): pick_representative_urls — alphabetical-first per group"
```

---

## Task 6: `render_assert_matrix` — group-keyed overrides → URL patterns

**Files:**
- Modify: `tools/gen_lhci_urls.py`
- Modify: `tools/test_gen_lhci_urls.py`

- [ ] **Step 1: Add tests**

Append to `tools/test_gen_lhci_urls.py`:

```python
class RenderAssertMatrix(unittest.TestCase):
    def test_empty_overrides_returns_empty_list(self) -> None:
        picks = {"page:essays:essays": "/essays/example-one/"}
        self.assertEqual(gen.render_assert_matrix(picks, []), [])

    def test_override_translates_to_url_pattern(self) -> None:
        picks = {"page:essays:essays": "/essays/example-one/"}
        overrides = [{"group": "page:essays:essays", "perf": 0.85}]
        matrix = gen.render_assert_matrix(picks, overrides)
        self.assertEqual(len(matrix), 1)
        self.assertEqual(matrix[0]["matchingUrlPattern"], "/essays/example-one/$")
        self.assertEqual(
            matrix[0]["assertions"]["categories:performance"],
            ["error", {"minScore": 0.85}],
        )

    def test_multiple_category_overrides(self) -> None:
        picks = {"page:essays:essays": "/essays/example-one/"}
        overrides = [{
            "group": "page:essays:essays",
            "perf": 0.85,
            "accessibility": 0.95,
            "best-practices": 0.9,
            "seo": 0.9,
        }]
        matrix = gen.render_assert_matrix(picks, overrides)
        a = matrix[0]["assertions"]
        self.assertEqual(a["categories:performance"], ["error", {"minScore": 0.85}])
        self.assertEqual(a["categories:accessibility"], ["error", {"minScore": 0.95}])
        self.assertEqual(a["categories:best-practices"], ["error", {"minScore": 0.9}])
        self.assertEqual(a["categories:seo"], ["error", {"minScore": 0.9}])

    def test_unknown_group_raises(self) -> None:
        picks = {"page:essays:essays": "/essays/example-one/"}
        overrides = [{"group": "page:nonexistent:nonexistent", "perf": 0.85}]
        with self.assertRaises(ValueError) as ctx:
            gen.render_assert_matrix(picks, overrides)
        self.assertIn("page:nonexistent:nonexistent", str(ctx.exception))
        self.assertIn("page:essays:essays", str(ctx.exception))  # lists valid groups

    def test_url_regex_escaped(self) -> None:
        picks = {"page:essays:essays": "/essays/a.b+c/"}  # regex metachars
        overrides = [{"group": "page:essays:essays", "perf": 0.85}]
        matrix = gen.render_assert_matrix(picks, overrides)
        # '.' and '+' should be escaped
        self.assertEqual(matrix[0]["matchingUrlPattern"], r"/essays/a\.b\+c/$")
```

- [ ] **Step 2: Confirm tests fail**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 5 new tests FAIL.

- [ ] **Step 3: Implement**

In `tools/gen_lhci_urls.py`, add module-level constant + function:

```python
CATEGORY_MAP = {
    "perf": "categories:performance",
    "accessibility": "categories:accessibility",
    "best-practices": "categories:best-practices",
    "seo": "categories:seo",
}


def render_assert_matrix(
    picks: dict[str, str],
    overrides: list[dict],
) -> list[dict]:
    """Build assertMatrix entries from group-keyed overrides.

    Each override has {group, perf?, accessibility?, best-practices?, seo?}.
    matchingUrlPattern is the regex-escaped picked URL + anchor.
    Raises ValueError if an override references an unknown group."""
    matrix: list[dict] = []
    for ov in overrides:
        group = ov["group"]
        if group not in picks:
            raise ValueError(
                f"override references unknown group '{group}'; "
                f"valid groups: {sorted(picks.keys())}"
            )
        url = picks[group]
        pattern = re.escape(url) + "$"
        assertions: dict = {}
        for short_key, lhci_key in CATEGORY_MAP.items():
            if short_key in ov:
                assertions[lhci_key] = ["error", {"minScore": ov[short_key]}]
        matrix.append({
            "matchingUrlPattern": pattern,
            "assertions": assertions,
        })
    return matrix
```

- [ ] **Step 4: Confirm tests pass**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 11 tests PASS total.

- [ ] **Step 5: Commit**

```bash
git add tools/gen_lhci_urls.py tools/test_gen_lhci_urls.py
git commit -m "feat(lhci): render_assert_matrix — group-keyed overrides → URL patterns"
```

---

## Task 7: `rewrite_lighthouserc` — load, replace, write (plain JSON)

**Files:**
- Modify: `tools/gen_lhci_urls.py`
- Modify: `tools/test_gen_lhci_urls.py`

- [ ] **Step 1: Add tests**

Append to `tools/test_gen_lhci_urls.py`:

```python
DESKTOP_SEED = {
    "ci": {
        "collect": {
            "staticDistDir": "./public",
            "url": ["http://localhost/old/"],
            "settings": {"preset": "desktop"},
            "numberOfRuns": 1,
        },
        "assert": {
            "assertions": {
                "categories:accessibility":  ["error", {"minScore": 0.9}],
                "categories:performance":    ["error", {"minScore": 0.9}],
                "categories:best-practices": ["error", {"minScore": 0.9}],
                "categories:seo":            ["error", {"minScore": 0.9}],
            }
        },
        "upload": {"target": "temporary-public-storage"},
    }
}

MOBILE_SEED = {
    "ci": {
        "collect": {
            "staticDistDir": "./public",
            "url": ["http://localhost/old/"],
            "numberOfRuns": 1,
        },
        "assert": {
            "assertions": {
                "categories:accessibility":  ["error", {"minScore": 0.9}],
                "categories:performance":    ["error", {"minScore": 0.9}],
                "categories:best-practices": ["error", {"minScore": 0.9}],
                "categories:seo":            ["error", {"minScore": 0.9}],
            },
            "assertMatrix": [{"matchingUrlPattern": "/stale/$", "assertions": {}}],
        },
        "upload": {"target": "temporary-public-storage"},
    }
}


class RewriteLighthouserc(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.config = self.tmp / "lighthouserc.json"
        self.config.write_text(json.dumps(DESKTOP_SEED, indent=2), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def test_replaces_collect_url(self) -> None:
        picks = {
            "page:essays:essays": "/essays/example-one/",
            "home::page": "/",
        }
        gen.rewrite_lighthouserc(self.config, picks, overrides=[])
        result = json.loads(self.config.read_text())
        urls = result["ci"]["collect"]["url"]
        # Order: collect.url is sorted by URL for determinism
        self.assertEqual(urls, ["http://localhost/", "http://localhost/essays/example-one/"])

    def test_preserves_unrelated_fields(self) -> None:
        picks = {"home::page": "/"}
        gen.rewrite_lighthouserc(self.config, picks, overrides=[])
        result = json.loads(self.config.read_text())
        self.assertEqual(result["ci"]["collect"]["settings"]["preset"], "desktop")
        self.assertEqual(result["ci"]["collect"]["numberOfRuns"], 1)
        self.assertEqual(result["ci"]["upload"]["target"], "temporary-public-storage")
        # base assertions untouched
        self.assertIn("categories:accessibility", result["ci"]["assert"]["assertions"])

    def test_desktop_strips_assertMatrix(self) -> None:
        # Test that if a stale assertMatrix exists in DESKTOP config, it's removed
        # (desktop typically has no overrides; only mobile uses assertMatrix.)
        cfg = json.loads(self.config.read_text())
        cfg["ci"]["assert"]["assertMatrix"] = [{"matchingUrlPattern": "/stale/$"}]
        self.config.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        picks = {"home::page": "/"}
        gen.rewrite_lighthouserc(self.config, picks, overrides=[])
        result = json.loads(self.config.read_text())
        self.assertNotIn("assertMatrix", result["ci"]["assert"])

    def test_mobile_writes_assertMatrix(self) -> None:
        mobile = self.tmp / "lighthouserc.mobile.json"
        mobile.write_text(json.dumps(MOBILE_SEED, indent=2), encoding="utf-8")
        picks = {"page:essays:essays": "/essays/example-one/"}
        overrides = [{"group": "page:essays:essays", "perf": 0.85}]
        gen.rewrite_lighthouserc(mobile, picks, overrides=overrides)
        result = json.loads(mobile.read_text())
        matrix = result["ci"]["assert"]["assertMatrix"]
        self.assertEqual(len(matrix), 1)
        self.assertEqual(matrix[0]["matchingUrlPattern"], "/essays/example-one/$")

    def test_idempotent(self) -> None:
        picks = {"home::page": "/"}
        gen.rewrite_lighthouserc(self.config, picks, overrides=[])
        first = self.config.read_text()
        gen.rewrite_lighthouserc(self.config, picks, overrides=[])
        second = self.config.read_text()
        self.assertEqual(first, second)
```

- [ ] **Step 2: Confirm tests fail**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 5 new tests FAIL.

- [ ] **Step 3: Implement**

In `tools/gen_lhci_urls.py`, add after `render_assert_matrix`:

```python
def rewrite_lighthouserc(
    config_path: Path,
    picks: dict[str, str],
    overrides: list[dict],
    base_url: str = "http://localhost",
) -> None:
    """Load existing JSON config; replace collect.url + assertMatrix; write back.

    - collect.url := sorted list of base_url + each picked URL.
    - assertMatrix := render_assert_matrix(picks, overrides) when non-empty,
      else removed entirely.
    - All other fields (preset, numberOfRuns, base assertions, upload) preserved.
    - Output: 2-space JSON, trailing newline, sort_keys False.
    """
    config = json.loads(config_path.read_text(encoding="utf-8"))

    urls = sorted(f"{base_url}{path}" for path in picks.values())
    config["ci"]["collect"]["url"] = urls

    matrix = render_assert_matrix(picks, overrides)
    if matrix:
        config["ci"]["assert"]["assertMatrix"] = matrix
    else:
        config["ci"]["assert"].pop("assertMatrix", None)

    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
```

- [ ] **Step 4: Confirm tests pass**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 16 tests PASS total.

- [ ] **Step 5: Commit**

```bash
git add tools/gen_lhci_urls.py tools/test_gen_lhci_urls.py
git commit -m "feat(lhci): rewrite_lighthouserc — replace url + assertMatrix, preserve rest"
```

---

## Task 8: `run` + `main` end-to-end + failure modes

**Files:**
- Modify: `tools/gen_lhci_urls.py`
- Modify: `tools/test_gen_lhci_urls.py`

- [ ] **Step 1: Add tests**

Append to `tools/test_gen_lhci_urls.py`:

```python
class RunEndToEnd(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "public").mkdir()
        (self.tmp / "tools").mkdir()
        (self.tmp / "public" / "lhci-pages.json").write_text(
            json.dumps(SAMPLE_MANIFEST), encoding="utf-8"
        )
        (self.tmp / "tools" / "lhci-overrides.json").write_text(
            json.dumps({"desktop": [], "mobile": [
                {"group": "page:essays:essays", "perf": 0.85}
            ]}), encoding="utf-8"
        )
        (self.tmp / "lighthouserc.json").write_text(
            json.dumps(DESKTOP_SEED, indent=2), encoding="utf-8"
        )
        (self.tmp / "lighthouserc.mobile.json").write_text(
            json.dumps(MOBILE_SEED, indent=2), encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def test_run_full_round_trip(self) -> None:
        rc, errors = gen.run(self.tmp)
        self.assertEqual((rc, errors), (0, []))
        desktop = json.loads((self.tmp / "lighthouserc.json").read_text())
        mobile = json.loads((self.tmp / "lighthouserc.mobile.json").read_text())
        # Desktop: collect.url replaced, no assertMatrix
        self.assertGreater(len(desktop["ci"]["collect"]["url"]), 1)
        self.assertNotIn("assertMatrix", desktop["ci"]["assert"])
        # Mobile: collect.url replaced, assertMatrix targeting picked essay
        matrix = mobile["ci"]["assert"]["assertMatrix"]
        self.assertEqual(len(matrix), 1)

    def test_run_missing_manifest_returns_rc1(self) -> None:
        (self.tmp / "public" / "lhci-pages.json").unlink()
        rc, errors = gen.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("lhci-pages.json" in e for e in errors))

    def test_run_missing_overrides_falls_back_to_empty(self) -> None:
        (self.tmp / "tools" / "lhci-overrides.json").unlink()
        rc, errors = gen.run(self.tmp)
        self.assertEqual((rc, errors), (0, []))
        mobile = json.loads((self.tmp / "lighthouserc.mobile.json").read_text())
        # Without overrides, no assertMatrix
        self.assertNotIn("assertMatrix", mobile["ci"]["assert"])

    def test_run_missing_lighthouserc_returns_rc1(self) -> None:
        (self.tmp / "lighthouserc.json").unlink()
        rc, errors = gen.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("lighthouserc.json" in e for e in errors))

    def test_run_unknown_group_in_overrides_returns_rc1(self) -> None:
        (self.tmp / "tools" / "lhci-overrides.json").write_text(
            json.dumps({"desktop": [], "mobile": [
                {"group": "page:bogus:bogus", "perf": 0.5}
            ]}), encoding="utf-8"
        )
        rc, errors = gen.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("page:bogus:bogus" in e for e in errors))
```

- [ ] **Step 2: Confirm tests fail**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 5 new tests FAIL.

- [ ] **Step 3: Implement `run`**

Replace the placeholder `run` in `tools/gen_lhci_urls.py`:

```python
def run(repo_root: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Programmatic entry. Returns (rc, errors).

    Steps:
    1. Load public/lhci-pages.json. Missing → error.
    2. Load tools/lhci-overrides.json. Missing → empty overrides (no error).
    3. group + pick representative URLs.
    4. For each lighthouserc config (desktop, mobile): rewrite in place
       unless dry_run=True; in that case print the resulting JSON.
    """
    errors: list[str] = []
    manifest_path = repo_root / "public" / "lhci-pages.json"
    if not manifest_path.exists():
        return (1, [f"manifest missing at {manifest_path} — run after `hugo --minify`"])

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest:
        return (1, [f"manifest is empty at {manifest_path}"])

    overrides_path = repo_root / "tools" / "lhci-overrides.json"
    overrides = {"desktop": [], "mobile": []}
    if overrides_path.exists():
        overrides = json.loads(overrides_path.read_text(encoding="utf-8"))

    picks = pick_representative_urls(manifest)

    configs = [
        (repo_root / "lighthouserc.json", overrides.get("desktop", [])),
        (repo_root / "lighthouserc.mobile.json", overrides.get("mobile", [])),
    ]
    for cfg_path, cfg_overrides in configs:
        if not cfg_path.exists():
            errors.append(f"lighthouserc missing at {cfg_path}")
            continue
        try:
            if dry_run:
                # Read current config, compute new content, print diff-style
                _preview_rewrite(cfg_path, picks, cfg_overrides)
            else:
                rewrite_lighthouserc(cfg_path, picks, cfg_overrides)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        return (1, errors)
    return (0, [])


def _preview_rewrite(cfg_path: Path, picks: dict[str, str], overrides: list[dict]) -> None:
    """Compute what rewrite_lighthouserc would write and print to stdout."""
    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    config["ci"]["collect"]["url"] = sorted(f"http://localhost{p}" for p in picks.values())
    matrix = render_assert_matrix(picks, overrides)
    if matrix:
        config["ci"]["assert"]["assertMatrix"] = matrix
    else:
        config["ci"]["assert"].pop("assertMatrix", None)
    print(f"--- {cfg_path.name} (dry-run) ---")
    print(json.dumps(config, indent=2, sort_keys=False))
```

- [ ] **Step 4: Confirm tests pass**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 21 tests PASS total.

- [ ] **Step 5: Commit**

```bash
git add tools/gen_lhci_urls.py tools/test_gen_lhci_urls.py
git commit -m "feat(lhci): run() + failure modes — full end-to-end pipeline"
```

---

## Task 9: `--dry-run` flag verification

The flag was added to argparse in T3; `_preview_rewrite` landed in T8. This task verifies it works end-to-end.

**Files:**
- Modify: `tools/test_gen_lhci_urls.py`

- [ ] **Step 1: Add test**

Append to `tools/test_gen_lhci_urls.py`:

```python
class DryRun(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "public").mkdir()
        (self.tmp / "tools").mkdir()
        (self.tmp / "public" / "lhci-pages.json").write_text(
            json.dumps(SAMPLE_MANIFEST), encoding="utf-8"
        )
        (self.tmp / "lighthouserc.json").write_text(
            json.dumps(DESKTOP_SEED, indent=2), encoding="utf-8"
        )
        (self.tmp / "lighthouserc.mobile.json").write_text(
            json.dumps(MOBILE_SEED, indent=2), encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def test_dry_run_does_not_modify_files(self) -> None:
        before_desktop = (self.tmp / "lighthouserc.json").read_text()
        before_mobile = (self.tmp / "lighthouserc.mobile.json").read_text()
        rc, errors = gen.run(self.tmp, dry_run=True)
        self.assertEqual((rc, errors), (0, []))
        self.assertEqual(before_desktop, (self.tmp / "lighthouserc.json").read_text())
        self.assertEqual(before_mobile, (self.tmp / "lighthouserc.mobile.json").read_text())
```

- [ ] **Step 2: Run; should already pass (dry-run was implemented in T8)**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 22 tests PASS total.

- [ ] **Step 3: Manually exercise `--dry-run` via CLI**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
rm -rf public && hugo --minify --quiet
# create a minimal lhci-overrides.json for the test
echo '{"desktop": [], "mobile": [{"group": "page:essays:essays", "perf": 0.85}]}' > tools/lhci-overrides.json
python3 tools/gen_lhci_urls.py --dry-run 2>&1 | head -40
# Cleanup
rm tools/lhci-overrides.json
```
Expected: prints `--- lighthouserc.json (dry-run) ---` then JSON, then `--- lighthouserc.mobile.json (dry-run) ---` then JSON. Files unchanged.

- [ ] **Step 4: Commit**

```bash
git add tools/test_gen_lhci_urls.py
git commit -m "test(lhci): --dry-run preserves files"
```

---

## Task 10: Create `tools/lhci-overrides.json`

The hand-editable threshold-override surface. Replaces the inline `assertMatrix` entry currently in `lighthouserc.mobile.json`.

**Files:**
- Create: `tools/lhci-overrides.json`

- [ ] **Step 1: Write the file**

```json
{
  "desktop": [],
  "mobile": [
    {"group": "page:essays:essays", "perf": 0.85}
  ]
}
```

The `page:essays:essays` group covers any essay-single page. The 0.85 perf threshold mirrors the existing mobile override on `/essays/example-one/` (current `lighthouserc.mobile.json:assertMatrix[0]`). After the migration, this override automatically follows whatever URL the script picks (`example-explorables` initially, per spec §5 risk 4).

- [ ] **Step 2: Validate JSON parses**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
python3 -c "import json; print(json.load(open('tools/lhci-overrides.json')))"
```
Expected: `{'desktop': [], 'mobile': [{'group': 'page:essays:essays', 'perf': 0.85}]}`

- [ ] **Step 3: Commit**

```bash
git add tools/lhci-overrides.json
git commit -m "feat(lhci): overrides file — group-keyed assertion thresholds"
```

---

## Task 11: Run gen_lhci_urls; commit regenerated configs

First real-corpus run. The committed lighthouserc files get updated to match what CI will produce. After this, the configs are in steady state.

**Files:**
- Modify: `lighthouserc.json`
- Modify: `lighthouserc.mobile.json`

- [ ] **Step 1: Run the regen**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
rm -rf public && hugo --minify --quiet
python3 tools/gen_lhci_urls.py
echo "EXIT=$?"
```
Expected: `gen_lhci_urls: OK`, EXIT=0.

- [ ] **Step 2: Inspect the diff**

```bash
git diff lighthouserc.json lighthouserc.mobile.json | head -100
```
Expected diff:
- `collect.url` lists shift (URLs sorted alphabetically; `example-explorables` replaces `example-one` in the essays slot).
- `assertMatrix` in mobile config now targets `/essays/example-explorables/$` rather than `/essays/example-one/$`.
- All other fields unchanged.

- [ ] **Step 3: Verify LHCI configs are still valid JSON**

```bash
python3 -c "import json; json.load(open('lighthouserc.json'))"
python3 -c "import json; json.load(open('lighthouserc.mobile.json'))"
```
Expected: both succeed silently.

- [ ] **Step 4: Run `check_lhci_urls.py` (4.1) to confirm all picked URLs exist in `public/`**

```bash
python3 tools/check_lhci_urls.py
```
Expected: `check_lhci_urls: OK`.

- [ ] **Step 5: Commit**

```bash
git add lighthouserc.json lighthouserc.mobile.json
git commit -m "chore(lhci): regenerated configs — first run of gen_lhci_urls"
```

---

## Task 12: CI workflow + ci-local.sh wiring

Adds the regen step + sibling-test step to both the GitHub workflow and the local CI mirror.

**Files:**
- Modify: `.github/workflows/hugo.yaml`
- Modify: `tools/ci-local.sh`

- [ ] **Step 1: Edit `.github/workflows/hugo.yaml`**

Find the existing block around line 184–186:

```yaml
      - name: Verify page weights
        run: python3 tools/check_page_weights.py
      - name: Run page-weight linter unit tests
        run: cd tools && python3 -m unittest test_check_page_weights.py -v
      - name: Lighthouse CI (desktop)
```

Insert IMMEDIATELY AFTER the page-weight unit test step, BEFORE the Lighthouse CI desktop step:

```yaml
      - name: Regenerate LHCI URLs from sitemap manifest
        run: python3 tools/gen_lhci_urls.py
      - name: Run gen_lhci_urls unit tests
        run: python3 -m unittest tools/test_gen_lhci_urls.py -v
```

- [ ] **Step 2: Edit `tools/ci-local.sh`**

Find the page-weight invocations (around line 110-118):

```bash
python3 tools/check_page_weights.py
```

Insert IMMEDIATELY AFTER the page-weight block, BEFORE the LHCI section:

```bash

python3 tools/gen_lhci_urls.py
python3 -m unittest tools/test_gen_lhci_urls.py -v 2>&1 | tail -3
```

(Note the leading blank line for visual separation.)

- [ ] **Step 3: Sanity-check the edits**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
grep -n "gen_lhci_urls" tools/ci-local.sh .github/workflows/hugo.yaml
```
Expected: 4 matches — 2 in ci-local.sh (script + test), 2 in hugo.yaml (script step + test step).

- [ ] **Step 4: Commit**

```bash
git add tools/ci-local.sh .github/workflows/hugo.yaml
git commit -m "ci: wire gen_lhci_urls into ci-local.sh + workflow"
```

---

## Task 13: CLAUDE.md note

One-line author guidance.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Find the LHCI block**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
grep -n "lighthouserc\|LHCI URL\|check_lhci_urls" CLAUDE.md | head -10
```

Find a sensible insertion point — likely under the "Deployment" section near the LHCI step description.

- [ ] **Step 2: Add the note**

Insert as a short paragraph near the LHCI step description:

```markdown
**LHCI URL list is CI-generated.** `tools/gen_lhci_urls.py` rewrites `lighthouserc.{json,mobile.json}` between `hugo --minify` and the LHCI steps, picking one representative URL per (kind, section, type) group alphabetically. Edit `tools/lhci-overrides.json` to change per-group assertion thresholds; don't hand-edit the lighthouserc files. 4.1 (`check_lhci_urls.py`) stays as defense-in-depth.
```

(Adjust the exact wording to match surrounding prose style in CLAUDE.md.)

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): note LHCI URL list is CI-generated"
```

---

## Task 14: Roadmap mark + memory entry

Flip Tier 7.1 ☐ → ✓ in the roadmap + write the project memory entry.

**Files:**
- Modify: `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`
- Create: `.claude/memory/project_tier_7_1_complete.md`
- Modify: `.claude/memory/MEMORY.md`

- [ ] **Step 1: Find row 7.1**

```bash
grep -n "^| 7.1 " docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md
```

- [ ] **Step 2: Update row 7.1**

Replace the ☐ row with:

```markdown
| 7.1 | ✓ **LHCI 4.2 — sitemap-derived URLs.** Shipped 2026-06-12 (site commits TBD-FILL-AFTER-MERGE). `tools/gen_lhci_urls.py` (stdlib only) rewrites `lighthouserc.{json,mobile.json}` from Hugo-emitted `public/lhci-pages.json` manifest + `tools/lhci-overrides.json` group-keyed thresholds. Zero drift on fixture retirement. → [project-tier-7-1-complete](../../../.claude/memory/project_tier_7_1_complete.md) | `docs/superpowers/specs/2026-06-12-lhci-sitemap-derived-urls-design.md` + `docs/superpowers/plans/2026-06-12-lhci-sitemap-derived-urls.md` |
```

(`TBD-FILL-AFTER-MERGE` is a deliberate placeholder; T16 backfills with the actual commit range.)

- [ ] **Step 3: Update Tier 7 status note**

Search for "Tier 7 trigger-gated" or similar in the file. Update to reflect that 7.1 closed (only 7.2 remains, still trigger-gated).

- [ ] **Step 4: Write the memory file**

`.claude/memory/project_tier_7_1_complete.md`:

```markdown
---
name: tier-7-1-complete
description: "Tier 7.1 (LHCI sitemap-derived URLs) shipped 2026-06-12; gen_lhci_urls.py + Hugo lhci-pages.json manifest; ~22 unit tests"
metadata:
  node_type: memory
  type: project
---

**Shipped 2026-06-12.** Tier 7.1 — LHCI sitemap-derived URLs (originally 4.2 in [[project-lhci-representative-pages-queued]]). 4.1 (`check_lhci_urls.py`, [[project-lhci-url-validator-complete]]) stays as defense-in-depth.

Site commits: TBD-FILL-AFTER-PUSH.

What landed:

- New Hugo output format `LHCI-PAGES` (`hugo.yaml` + `layouts/index.lhci-pages.json`) emits `public/lhci-pages.json` — array of `{url, kind, section, type}` per regular page + section + home.
- New `tools/gen_lhci_urls.py` — stdlib-only generator. Functions: `group_pages` (tuple-key), `pick_representative_urls` (alphabetical-first per group), `render_assert_matrix` (group-keyed overrides → URL patterns), `rewrite_lighthouserc` (preserves preset, numberOfRuns, base assertions, upload). `run(repo_root, dry_run)` entry + `main()` with `--dry-run` flag.
- New `tools/test_gen_lhci_urls.py` — 22 unit tests covering grouping, picking, override application, idempotency, failure modes.
- New `tools/lhci-overrides.json` — group-keyed assertion thresholds. Replaces the inline `assertMatrix` entry that hand-targeted `/essays/example-one/`.
- CI workflow + `tools/ci-local.sh` insert the regen + sibling test between `hugo --minify` and the LHCI steps.
- CLAUDE.md note added.
- First-CI-after-merge: essay representative shifted from `example-one` to `example-explorables` (alphabetical sort — see [[project_tier_8_1_complete]] explorables slice that landed `example-explorables` fixture earlier today).

Spec: `docs/superpowers/specs/2026-06-12-lhci-sitemap-derived-urls-design.md`.
Plan: `docs/superpowers/plans/2026-06-12-lhci-sitemap-derived-urls.md`.

**Follow-ups (queued in spec §6):**
1. Tier 7.2 — visual-feature autodetect. ~150 LOC. Trigger: after 7.1 fingerprint corpus is observable across 2-3 LHCI runs.
2. Per-essay JS bundle auditing. Trigger: first explorable essay where bundle exceeds page-weight gates.
```

- [ ] **Step 5: Add MEMORY.md pointer**

Find the existing project-tier-*-complete entries (latest is `project-tier-8-1-complete`). Append after that line:

```markdown
- [Tier 7.1 — LHCI sitemap-derived URLs shipped](project_tier_7_1_complete.md) — gen_lhci_urls.py + Hugo lhci-pages.json manifest + 22 unit tests, 2026-06-12
```

Keep under 200 chars per the MEMORY.md size warning.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md .claude/memory/project_tier_7_1_complete.md .claude/memory/MEMORY.md
git commit -m "docs(roadmap+memory): Tier 7.1 closed — LHCI sitemap-derived URLs"
```

---

## Task 15: JSONC banner support (optional polish)

The spec §4 Option A calls for an auto-generated header on each lighthouserc file pointing authors to `tools/lhci-overrides.json`. JSON doesn't support comments natively. This task adds JSONC-style `//` comments to the rewriter, with a tested fallback if LHCI rejects them.

If you want to skip this task and ship the slice without a banner: that's fine — the slice still works. The banner is polish, not a hard requirement.

**Files:**
- Modify: `tools/gen_lhci_urls.py`
- Modify: `tools/test_gen_lhci_urls.py`
- Modify (re-generated): `lighthouserc.json`, `lighthouserc.mobile.json`

- [ ] **Step 1: Verify LHCI accepts JSONC**

Test before implementing — `@lhci/cli` may reject comments outright.

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
cat > /tmp/lhci-test.json <<'EOF'
// Test comment
{
  "ci": {
    "collect": {"staticDistDir": "./public", "url": ["http://localhost/"], "settings": {"preset": "desktop"}, "numberOfRuns": 1},
    "assert": {"assertions": {"categories:performance": ["error", {"minScore": 0.5}]}},
    "upload": {"target": "temporary-public-storage"}
  }
}
EOF
# Try parsing with LHCI's config loader (requires npx)
npx @lhci/cli@latest collect --config=/tmp/lhci-test.json --staticDistDir=./public --upload.target=filesystem --upload.outputDir=/tmp/lhci-test-out --max-old-space-size=4096 2>&1 | head -5
rm /tmp/lhci-test.json
rm -rf /tmp/lhci-test-out
```

**If LHCI accepts the JSONC comment** → proceed to Step 2 (add banner via `//` comments).
**If LHCI rejects** → skip the banner; alternative is to store the banner text in a top-level `"//"` key in the JSON (which is valid JSON and conventionally ignored by readers). Or skip the task entirely.

- [ ] **Step 2 (if JSONC accepted): Add banner constants + write-time prepend**

In `tools/gen_lhci_urls.py`, add module-level constant:

```python
BANNER = """\
// auto-generated by tools/gen_lhci_urls.py
// to change thresholds: edit tools/lhci-overrides.json
// to change URL picks: kill or add fixtures; the script picks
// alphabetically-first per (kind, section, type) group
"""
```

Modify `rewrite_lighthouserc` to prepend BANNER on write, and modify the read path to strip leading `//` lines:

```python
def _strip_jsonc_header(text: str) -> str:
    """Strip leading lines that start with //."""
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith("//"):
        i += 1
    return "".join(lines[i:])


def rewrite_lighthouserc(
    config_path: Path,
    picks: dict[str, str],
    overrides: list[dict],
    base_url: str = "http://localhost",
) -> None:
    raw = config_path.read_text(encoding="utf-8")
    config = json.loads(_strip_jsonc_header(raw))
    # ... rest of function unchanged ...
    config_path.write_text(
        BANNER + json.dumps(config, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
```

- [ ] **Step 3 (if JSONC accepted): Add test**

Append to `tools/test_gen_lhci_urls.py`:

```python
class JsoncBanner(unittest.TestCase):
    def test_banner_prepended_on_write(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        cfg = tmp / "lighthouserc.json"
        cfg.write_text(json.dumps(DESKTOP_SEED, indent=2), encoding="utf-8")
        gen.rewrite_lighthouserc(cfg, {"home::page": "/"}, overrides=[])
        text = cfg.read_text()
        self.assertTrue(text.startswith("//"))
        self.assertIn("gen_lhci_urls.py", text.split("\n")[0])
        shutil.rmtree(tmp)

    def test_banner_idempotent(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        cfg = tmp / "lighthouserc.json"
        cfg.write_text(json.dumps(DESKTOP_SEED, indent=2), encoding="utf-8")
        gen.rewrite_lighthouserc(cfg, {"home::page": "/"}, overrides=[])
        first = cfg.read_text()
        gen.rewrite_lighthouserc(cfg, {"home::page": "/"}, overrides=[])
        self.assertEqual(first, cfg.read_text())  # no banner doubling
        shutil.rmtree(tmp)
```

- [ ] **Step 4: Run all tests**

```bash
python3 -m unittest tools/test_gen_lhci_urls.py -v
```
Expected: 24 tests PASS.

- [ ] **Step 5: Re-run gen_lhci_urls to apply banner**

```bash
python3 tools/gen_lhci_urls.py
```

Inspect the regenerated configs — they should now start with the banner.

```bash
head -5 lighthouserc.json
```

- [ ] **Step 6: Commit**

```bash
git add tools/gen_lhci_urls.py tools/test_gen_lhci_urls.py lighthouserc.json lighthouserc.mobile.json
git commit -m "feat(lhci): JSONC banner — author guidance at top of generated configs"
```

---

## Task 16: End-to-end verification + commit-range backfill

The final pass: run `ci-local.sh`, backfill the TBD placeholders, sanity-check.

- [ ] **Step 1: Run full local CI**

```bash
cd /Users/a3madkour/Sync/Workspace/a3madkour.github.io
bash tools/ci-local.sh 2>&1 | tail -30
```
Expected: all linters green (`gen_lhci_urls: OK`, 22+ tests pass, LHCI URLs validated, etc.). LHCI itself may fail if Chromium isn't installed — that's environmental ([[reference-ci-local-lhci-deps]]), not a slice regression. If everything except LHCI is green, that's the gate cleared.

- [ ] **Step 2: Get the commit range for backfill**

```bash
git log --oneline 6341ce3..HEAD | head -20
```
Note the first and last SHAs of this slice.

- [ ] **Step 3: Backfill placeholders**

Edit `.claude/memory/project_tier_7_1_complete.md` line 11 — replace `TBD-FILL-AFTER-PUSH` with the actual range (format: `<spec_sha>..<last_sha>` + ` (<N> commits)`).

Edit `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md` row 7.1 — replace `TBD-FILL-AFTER-MERGE` similarly.

- [ ] **Step 4: Commit the backfill**

```bash
git add .claude/memory/project_tier_7_1_complete.md docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md
git commit -m "docs: backfill Tier 7.1 commit range"
```

- [ ] **Step 5: Final review + offer to push**

Run: `git log --oneline 6341ce3..HEAD`
Expected: ~16 commits, all green.

Report to author: "Tier 7.1 ready. Local gates green except LHCI (Chromium dep). Ready for your push when satisfied." DO NOT push without explicit author authorization per [[feedback-verify-before-merge]].

---

## Notes for the executor

- **Stdlib only.** No pyyaml, no requests, no anything outside Python stdlib. Per the spec § Constraints.
- **Don't run `hugo --minify` with a dev server alive.** Per [[reference-hugo-dev-server-gotcha]]. Each step that builds must kill any local dev server first.
- **First-CI-after-merge essay shift.** `example-explorables` will replace `example-one` as the essay representative — that's expected per spec §5 risk 4.
- **`tools/lhci-overrides.json` is the new hand-edit surface.** Authors editing this file is normal; editing the lighthouserc files directly is the antipattern that this slice removes.
- **Hugo output format gotcha.** If the manifest emission fails (Task 1 step 3 doesn't produce `public/lhci-pages.json`), the most likely cause is a template lookup mismatch. Hugo expects `layouts/index.lhci-pages.json` (matching the output format's lower-cased name + extension). If the file ends up at a different path, check `hugo --templateMetrics` for actual template resolution.
- **`@lhci/cli` JSONC tolerance — verify before depending.** Task 15 step 1 is the gate; don't assume LHCI parses `// comments`. If it doesn't, skip Task 15 entirely.
