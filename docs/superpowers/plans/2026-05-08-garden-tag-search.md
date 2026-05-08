# Tag Two-Tier Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the tag two-tier filter on `/garden/` and `/essays/` — a curated primary chip set + a `<details>` disclosure containing a search input that live-filters secondary chips, multi-select within the tag dimension, with a top-K auto-fallback when curation is absent and a CI-gated linter that validates curation against the live taxonomy.

**Architecture:** All work happens behind the existing `partials/filter-chips.html` interface plus the shared `assets/js/filter-chips.js` module. The partial gains a `section` parameter and emits a `<details>` element after primary chips when there are secondary chips to disclose. Caller templates pre-rank tag values by note count (desc, alphabetical ties). The JS state shape changes for the tag dim only — from a single string to a `Set` — and a search-input event handler toggles `hidden` on secondary chips. A new Python linter (`tools/check_filter_chips_config.py`) validates `data/filter-chips.yaml`, wired into CI as the sixth Python gate.

**Tech Stack:** Hugo extended ≥0.148.0, Python 3 (linter — stdlib only), vanilla JS (ES modules, esbuild via Hugo's `js.Build`), CSS (additions to `assets/css/main.css` §16).

**Spec:** `docs/superpowers/specs/2026-05-08-garden-tag-search-design.md`. Read it before starting.

**Existing reusable components (don't reimplement):**
- `tools/check_fixtures.py` exposes `parse_frontmatter` at module level. The new linter imports it.
- `assets/css/main.css` §16 already defines `.filter-chips`, `.filter-dimension`, `.filter-label`, `.filter-chip`, `.filter-chip:hover`, `.filter-chip.is-active`, `.filter-chip:focus-visible`. Reuse — additions are purely additive.
- `assets/js/filter-chips.js` already implements the multi-dim AND filter; only the tag dim's state shape and the disclosure interaction layer are new.
- `layouts/garden/list.html` and `layouts/essays/list.html` both call the partial with `(dict "dimensions" $dims)`. Both gain a `section` key in this slice.

**Verification model:**
- Python linter: TDD via stdlib `unittest`.
- Hugo templates / CSS / JS: build-and-inspect — `hugo --minify` succeeds, then `hugo server --buildDrafts` is exercised in the browser. Each non-Python task ends with explicit build success + a browser check on the affected URL.
- The final task does a full keyboard + mouse walkthrough on `/garden/` with K temporarily lowered to 4 so the disclosure actually renders against the existing 12-tag fixture set.

**Working assumption:** Run `hugo server --buildDrafts` in a separate terminal during implementation; inspect at `http://localhost:1313/`.

**Tag count baseline (informational):**
- Garden fixtures: 12 distinct tags across 14 notes — `aesthetics, calvino, games, glass, listening, memory, mystery, narrative, play, playing, reading, series`. With K=10, 10 primary + 2 secondary.
- Essay fixtures: 3 distinct tags across 6 notes — `example-tag-a, example-tag-b, example-tag-c`. Below K, so disclosure suppressed on `/essays/`.

---

## Task 1: Linter + tests (TDD)

**Files:**
- Create: `tools/check_filter_chips_config.py`
- Create: `tools/test_check_filter_chips_config.py`

The linter loads `data/filter-chips.yaml`, walks each declared section's `content/<section>/*/index.md` to collect every distinct tag from non-draft notes, and validates that every entry in `primary_tags` resolves to a real tag. Optional `primary_top_k` must be a positive integer. Stdlib only.

- [ ] **Step 1: Write the failing tests**

Create `tools/test_check_filter_chips_config.py`:

```python
"""Tests for check_filter_chips_config.py — run with:
   python3 -m unittest tools/test_check_filter_chips_config.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_filter_chips_config as lint  # noqa: E402


GARDEN_NOTE = """\
---
title: "Salience and memory"
draft: false
last_modified: 2026-04-22
growth_stage: seedling
tags: ["memory", "narrative"]
---

Body.
"""

ESSAY_NOTE = """\
---
title: "Example essay"
date: 2026-01-01
lastmod: 2026-01-01
draft: false
summary: "x"
tags: ["example-tag-a", "example-tag-b"]
series: ""
series_order: 0
toc: false
has_sidenotes: false
has_citations: false
has_footnotes: false
has_math: false
has_widgets: false
has_video_sync: false
---

Body.
"""


class TempRepo:
    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "content" / "garden").mkdir(parents=True)
        (self.root / "content" / "essays").mkdir(parents=True)
        (self.root / "data").mkdir(parents=True)

    def write_garden(self, slug: str, body: str = GARDEN_NOTE) -> None:
        d = self.root / "content" / "garden" / slug
        d.mkdir(exist_ok=True)
        (d / "index.md").write_text(body)

    def write_essay(self, slug: str, body: str = ESSAY_NOTE) -> None:
        d = self.root / "content" / "essays" / slug
        d.mkdir(exist_ok=True)
        (d / "index.md").write_text(body)

    def write_config(self, content: str) -> None:
        (self.root / "data" / "filter-chips.yaml").write_text(content)

    def cleanup(self) -> None:
        shutil.rmtree(self.root)


class FilterChipsLinterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    # --- happy paths ---

    def test_no_config_file_passes(self) -> None:
        # Auto-fallback applies at build time; absence is not an error.
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_config_with_no_sections_passes(self) -> None:
        self.repo.write_config("# empty\n")
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_garden_curation_passes(self) -> None:
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["memory", "narrative"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_valid_top_k_override_passes(self) -> None:
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: 8\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_empty_primary_tags_passes(self) -> None:
        # Empty list means auto-fallback at build time.
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: []\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    def test_section_not_in_config_passes(self) -> None:
        # essays section absent from config → auto-fallback applies.
        self.repo.write_garden("salience-and-memory")
        self.repo.write_essay("essay-1")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["memory"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected: {errors}")

    # --- failures ---

    def test_stale_garden_tag_fails(self) -> None:
        self.repo.write_garden("salience-and-memory")
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["memory", "ghost-tag"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        joined = "\n".join(errors)
        self.assertIn("ghost-tag", joined)
        self.assertIn("garden", joined)

    def test_stale_essay_tag_fails(self) -> None:
        self.repo.write_essay("essay-1")
        self.repo.write_config(
            'essays:\n'
            '  primary_tags: ["nope"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("nope" in e and "essays" in e for e in errors))

    def test_draft_only_tag_does_not_count(self) -> None:
        # A tag that appears only on drafts must not satisfy primary_tags.
        draft = GARDEN_NOTE.replace("draft: false", "draft: true").replace(
            '["memory", "narrative"]', '["draft-only"]'
        )
        self.repo.write_garden("draft-note", draft)
        self.repo.write_config(
            'garden:\n'
            '  primary_tags: ["draft-only"]\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("draft-only" in e for e in errors))

    def test_invalid_top_k_string_fails(self) -> None:
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: "ten"\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("primary_top_k" in e for e in errors))

    def test_invalid_top_k_zero_fails(self) -> None:
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: 0\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("primary_top_k" in e for e in errors))

    def test_invalid_top_k_negative_fails(self) -> None:
        self.repo.write_config(
            'garden:\n'
            '  primary_top_k: -1\n'
        )
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("primary_top_k" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tools/test_check_filter_chips_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'check_filter_chips_config'`

- [ ] **Step 3: Write minimal implementation**

Create `tools/check_filter_chips_config.py`:

```python
#!/usr/bin/env python3
"""Filter-chips config linter.

Validates `data/filter-chips.yaml`: every entry in each section's
`primary_tags` must resolve to a tag used by at least one non-draft note in
that section's `content/<section>/`. Optional `primary_top_k` must be a
positive integer.

Exits 0 on all-pass (or absent config file), 1 on any violation.
Stdlib only — imports the YAML-subset parser from check_fixtures.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter, parse_scalar  # noqa: E402

# YAML structure we accept (narrow subset, no third-party deps):
#
#   <section>:
#     primary_tags: ["a", "b"]
#     primary_top_k: 10
#
# - Top-level keys are section names (`garden`, `essays`, ...).
# - `primary_tags` is a flow-style list of strings (same shape as the
#   `tags:` field elsewhere) OR may be omitted/empty.
# - `primary_top_k` is an integer.

SECTION_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*$")
KV_RE = re.compile(r"^\s{2}([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def parse_config(text: str) -> dict[str, dict[str, object]]:
    """Parse the data/filter-chips.yaml subset we accept."""
    out: dict[str, dict[str, object]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = SECTION_RE.match(line)
        if m:
            current = m.group(1)
            out[current] = {}
            continue
        m = KV_RE.match(line)
        if m and current is not None:
            key, value = m.group(1), m.group(2).strip()
            out[current][key] = parse_scalar(value)
    return out


def collect_tags(section_dir: Path) -> set[str]:
    """Return the set of tags used by any non-draft note in section_dir."""
    tags: set[str] = set()
    if not section_dir.exists():
        return tags
    for entry in sorted(section_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        md = entry / "index.md"
        if not md.exists():
            continue
        fm = parse_frontmatter(md.read_text())
        if not fm:
            continue
        if fm.get("draft") is True:
            continue
        page_tags = fm.get("tags") or []
        if isinstance(page_tags, list):
            for t in page_tags:
                tags.add(str(t))
    return tags


def run(repo_root: Path) -> tuple[int, list[str]]:
    config_path = repo_root / "data" / "filter-chips.yaml"
    errors: list[str] = []

    if not config_path.exists():
        return 0, []

    config = parse_config(config_path.read_text())

    for section, section_cfg in config.items():
        # Validate primary_top_k if present
        top_k = section_cfg.get("primary_top_k")
        if top_k is not None:
            if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
                errors.append(
                    f"data/filter-chips.yaml:{section}.primary_top_k "
                    f"must be a positive integer, got {top_k!r}"
                )

        # Validate primary_tags entries
        primary = section_cfg.get("primary_tags")
        if not primary:
            continue
        if not isinstance(primary, list):
            errors.append(
                f"data/filter-chips.yaml:{section}.primary_tags "
                f"must be a list, got {type(primary).__name__}"
            )
            continue
        live = collect_tags(repo_root / "content" / section)
        for entry in primary:
            if str(entry) not in live:
                errors.append(
                    f"data/filter-chips.yaml:{section}.primary_tags: "
                    f'"{entry}" is not used by any non-draft note '
                    f"in /content/{section}/"
                )

    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("Filter-chips config lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All filter-chips config entries pass linter.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tools/test_check_filter_chips_config.py -v`
Expected: all 12 tests PASS.

- [ ] **Step 5: Make the script executable and run against the real repo**

Run:
```bash
chmod +x tools/check_filter_chips_config.py
python3 tools/check_filter_chips_config.py
```
Expected: `All filter-chips config entries pass linter.` (the config doesn't exist yet — exit code 0).

- [ ] **Step 6: Commit**

```bash
git add tools/check_filter_chips_config.py tools/test_check_filter_chips_config.py
git commit -m "Add filter-chips config linter

Stdlib-only Python linter validates data/filter-chips.yaml: every entry in
primary_tags must resolve to a tag used by a non-draft note in the matching
section. Optional primary_top_k must be a positive integer. Reuses
parse_frontmatter from check_fixtures."
```

---

## Task 2: Wire linter into CI

**Files:**
- Modify: `.github/workflows/hugo.yaml`

Add two new build steps before the Hugo build, mirroring the existing pair pattern (verifier + unit tests).

- [ ] **Step 1: Insert new CI steps**

Find the block (currently around lines 47–55):

```yaml
      - name: Verify garden fixtures
        run: python3 tools/check_garden_fixtures.py
      - name: Run garden linter unit tests
        run: python3 -m unittest tools/test_check_garden_fixtures.py -v
      - name: Build with Hugo
```

Replace with:

```yaml
      - name: Verify garden fixtures
        run: python3 tools/check_garden_fixtures.py
      - name: Run garden linter unit tests
        run: python3 -m unittest tools/test_check_garden_fixtures.py -v
      - name: Verify filter-chips config
        run: python3 tools/check_filter_chips_config.py
      - name: Run filter-chips linter unit tests
        run: python3 -m unittest tools/test_check_filter_chips_config.py -v
      - name: Build with Hugo
```

- [ ] **Step 2: Verify both linter commands run locally**

Run: `python3 tools/check_filter_chips_config.py && python3 -m unittest tools/test_check_filter_chips_config.py -v`
Expected: linter prints all-pass; tests all pass.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "Wire filter-chips config linter into CI

Adds the new linter and its unit tests as the sixth Python gate, before
the Hugo build. Mirrors the verifier+tests pattern used for essay and
garden fixtures."
```

---

## Task 3: Create `data/filter-chips.yaml`

**Files:**
- Create: `data/filter-chips.yaml`

Empty stub keyed by section. Both sections start with auto-fallback (no `primary_tags` declared). Curation is a future authoring task; this slice ships the mechanism.

- [ ] **Step 1: Create the file**

Create `data/filter-chips.yaml`:

```yaml
# Filter-chips configuration — controls the primary tag set for each
# section's filter strip on the index page.
#
# Schema (per top-level section key):
#   primary_tags:    ordered list of tag slugs to render as primary chips.
#                    When omitted, falls back to top-K by note count.
#   primary_top_k:   integer; overrides the default K=10 used by auto-mode.
#                    Only consulted when primary_tags is absent or empty.
#
# Linter: tools/check_filter_chips_config.py validates that every entry in
# primary_tags resolves to a tag used by a non-draft note in the matching
# section. Stale entries fail the build.

garden:
  # Auto top-10 fallback applies until curated.
essays:
  # Auto top-10 fallback applies until curated.
```

- [ ] **Step 2: Verify the linter still passes**

Run: `python3 tools/check_filter_chips_config.py`
Expected: `All filter-chips config entries pass linter.`

- [ ] **Step 3: Commit**

```bash
git add data/filter-chips.yaml
git commit -m "Add empty filter-chips config stub

Both sections start in auto top-10 mode. Curation is a future authoring
task; this commit ships the file shape and inline schema docs."
```

---

## Task 4: Caller templates rank tags + pass section

**Files:**
- Modify: `layouts/garden/list.html`
- Modify: `layouts/essays/list.html`

The partial currently receives `dimensions` with each dim carrying a flat `values` slice. To support top-K auto-fallback by frequency, callers pre-rank the tag values: most-used first, alphabetical for ties. Both callers also pass `section` so the partial can look up `site.Data.filter_chips.<section>`.

The flavor/stage/series/year dims get no ranking change — they're not two-tier and order doesn't affect the disclosure logic.

- [ ] **Step 1: Update `layouts/garden/list.html`**

Replace lines 14–45 (everything from `{{- $tags := slice -}}` through `{{ partial "filter-chips.html" ... }}`):

```hugo
    {{- /* ----- Build dimension value sets for the filter strip ----- */ -}}
    {{- $tagCounts := dict -}}
    {{- $flavors := slice -}}
    {{- $stages := slice -}}
    {{- range $pages -}}
      {{- range .Params.tags -}}
        {{- $cur := index $tagCounts . | default 0 -}}
        {{- $tagCounts = merge $tagCounts (dict . (add $cur 1)) -}}
      {{- end -}}
      {{- $mt := .Params.media_type -}}
      {{- $f := "concept" -}}
      {{- if $mt -}}
        {{- if in (slice "book" "album" "track" "game" "film" "series") $mt -}}
          {{- $f = "media" -}}
        {{- else -}}
          {{- $f = "reference" -}}
        {{- end -}}
      {{- end -}}
      {{- if not (in $flavors $f) -}}{{- $flavors = $flavors | append $f -}}{{- end -}}
      {{- $st := .Params.growth_stage | default "seedling" -}}
      {{- if not (in $stages $st) -}}{{- $stages = $stages | append $st -}}{{- end -}}
    {{- end -}}

    {{- /* Rank tags by count desc, alphabetical for ties */ -}}
    {{- $tagPairs := slice -}}
    {{- range $name, $count := $tagCounts -}}
      {{- $tagPairs = $tagPairs | append (dict "name" $name "count" $count) -}}
    {{- end -}}
    {{- $tags := slice -}}
    {{- range (sort (sort $tagPairs "name" "asc") "count" "desc") -}}
      {{- $tags = $tags | append .name -}}
    {{- end -}}

    {{- $dims := slice -}}
    {{- if ge (len $tags) 2 -}}
      {{- $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" $tags) -}}
    {{- end -}}
    {{- if ge (len $flavors) 2 -}}
      {{- $dims = $dims | append (dict "key" "flavor" "label" "Flavor" "values" $flavors) -}}
    {{- end -}}
    {{- if ge (len $stages) 2 -}}
      {{- $dims = $dims | append (dict "key" "stage" "label" "Stage" "values" $stages) -}}
    {{- end -}}
    {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "garden") }}
```

- [ ] **Step 2: Update `layouts/essays/list.html`**

Replace lines 11–36 (the whole dimension-building block + partial call):

```hugo
    {{/* Collect dimensions from pages */}}
    {{ $tagCounts := dict }}
    {{ $seriesList := slice }}
    {{ $years := slice }}
    {{ range .Pages }}
      {{ range .Params.tags }}
        {{ $cur := index $tagCounts . | default 0 }}
        {{ $tagCounts = merge $tagCounts (dict . (add $cur 1)) }}
      {{ end }}
      {{ with .Params.series }}
        {{ if not (in $seriesList .) }}{{ $seriesList = $seriesList | append . }}{{ end }}
      {{ end }}
      {{ $y := .Date.Format "2006" }}
      {{ if not (in $years $y) }}{{ $years = $years | append $y }}{{ end }}
    {{ end }}

    {{/* Rank tags by count desc, alphabetical for ties */}}
    {{ $tagPairs := slice }}
    {{ range $name, $count := $tagCounts }}
      {{ $tagPairs = $tagPairs | append (dict "name" $name "count" $count) }}
    {{ end }}
    {{ $tags := slice }}
    {{ range (sort (sort $tagPairs "name" "asc") "count" "desc") }}
      {{ $tags = $tags | append .name }}
    {{ end }}

    {{ $dims := slice }}
    {{ if ge (len $tags) 2 }}
      {{ $dims = $dims | append (dict "key" "tag" "label" "Tag" "values" $tags) }}
    {{ end }}
    {{ if ge (len $seriesList) 2 }}
      {{ $dims = $dims | append (dict "key" "series" "label" "Series" "values" $seriesList) }}
    {{ end }}
    {{ if ge (len $years) 2 }}
      {{ $dims = $dims | append (dict "key" "year" "label" "Year" "values" $years) }}
    {{ end }}
    {{ partial "filter-chips.html" (dict "dimensions" $dims "section" "essays") }}
```

- [ ] **Step 3: Build and verify**

Run: `hugo --minify 2>&1 | tail -10`
Expected: `Total in <N> ms`. No template errors.

Open `http://localhost:1313/garden/` and `http://localhost:1313/essays/` in the browser. The chip strip should render identically to before this task — only ordering of tag chips may change (high-count tags now appear first instead of arbitrary order).

- [ ] **Step 4: Commit**

```bash
git add layouts/garden/list.html layouts/essays/list.html
git commit -m "Rank tag values by frequency in list templates

Both /garden/ and /essays/ list templates now compute tag counts and rank
the values list by count desc, alphabetical for ties. Both pass section
name to the filter-chips partial. No visible behavior change yet — the
two-tier rendering lands in the next commit."
```

---

## Task 5: Partial — render two-tier for tag dim

**Files:**
- Modify: `layouts/partials/filter-chips.html`

Add the disclosure rendering. Tag dim: split values into primary (curated or top-K) and secondary; emit primary chips inline plus a `<details>` block for the secondary set when there are any. Other dims: rendered as today.

- [ ] **Step 1: Replace the partial**

Replace the entire contents of `layouts/partials/filter-chips.html`:

```hugo
{{- /* Shared multi-dimension AND filter chip strip.
   Inputs:
     dimensions  — slice of dicts: { key, label, values }
                   key:    machine name (used as data-dim, e.g. "tag")
                   label:  display label (e.g. "Tag")
                   values: slice of strings (the chip values).
                           For the tag dim, values must be pre-ranked by
                           note count (desc, alphabetical for ties) — the
                           caller does this.
     section     — section slug (e.g. "garden", "essays") used to look up
                   site.Data.filter_chips.<section> for curated primary tags.
   Suppression rule: dimensions with len(values) < 2 are not rendered.
   Visibility is the AND of all non-default active chips; logic lives in
   assets/js/filter-chips.js.

   Two-tier behavior applies ONLY to the tag dim:
     - primary tags = curated list from site.Data.filter_chips.<section>.primary_tags
                      (in declared order), or first K of values when absent.
                      K defaults to 10; override per section via primary_top_k.
     - secondary tags = remaining values (in their ranked order).
     - When secondary is non-empty, render <details> with a search input
       and the secondary chips. When empty (≤K total values), no <details>.
*/ -}}
{{- $dims := .dimensions | default slice -}}
{{- $section := .section | default "" -}}
{{- $sectionCfg := dict -}}
{{- with site.Data.filter_chips -}}
  {{- $sectionCfg = index . $section | default dict -}}
{{- end -}}
{{- $curated := $sectionCfg.primary_tags | default slice -}}
{{- $topK := $sectionCfg.primary_top_k | default 10 -}}

{{- $renderable := slice -}}
{{- range $dims -}}
  {{- if ge (len .values) 2 -}}
    {{- $renderable = $renderable | append . -}}
  {{- end -}}
{{- end -}}

{{- if $renderable -}}
<nav class="filter-chips" aria-label="Filters">
  {{- range $renderable -}}
    {{- $key := .key -}}
    {{- $label := .label -}}
    {{- $values := .values -}}
    <div class="filter-dimension" data-dim="{{ $key }}">
      <span class="filter-label">{{ $label }}</span>
      <button type="button" class="filter-chip is-active" data-dim="{{ $key }}" data-key="all">All</button>

      {{- if eq $key "tag" -}}
        {{- /* Resolve primary set */ -}}
        {{- $primary := slice -}}
        {{- if $curated -}}
          {{- range $curated -}}
            {{- if in $values . -}}{{- $primary = $primary | append . -}}{{- end -}}
          {{- end -}}
        {{- else -}}
          {{- $primary = first $topK $values -}}
        {{- end -}}
        {{- /* Secondary = values not in primary, preserving ranked order */ -}}
        {{- $secondary := slice -}}
        {{- range $values -}}
          {{- if not (in $primary .) -}}{{- $secondary = $secondary | append . -}}{{- end -}}
        {{- end -}}

        {{- range $primary -}}
          <button type="button" class="filter-chip" data-dim="tag" data-key="{{ . }}" data-tier="primary">{{ . }}</button>
        {{- end -}}

        {{- if $secondary -}}
          <details class="filter-disclosure">
            <summary class="filter-chip is-disclosure">
              <span class="filter-disclosure-label">More tags</span>
              <span class="filter-disclosure-count" hidden></span>
            </summary>
            <div class="filter-disclosure-body">
              <input type="search" class="filter-search"
                     placeholder="Search {{ len $secondary }} more tags…"
                     aria-label="Search secondary tags"
                     aria-controls="filter-secondary-tag"
                     autocomplete="off">
              <div class="filter-secondary" id="filter-secondary-tag">
                {{- range $secondary -}}
                  <button type="button" class="filter-chip" data-dim="tag" data-key="{{ . }}" data-tier="secondary">{{ . }}</button>
                {{- end -}}
                <p class="filter-secondary-empty" hidden>No matching tags.</p>
              </div>
            </div>
          </details>
        {{- end -}}

      {{- else -}}
        {{- /* Other dims: flat chip list, unchanged */ -}}
        {{- range $values -}}
          <button type="button" class="filter-chip" data-dim="{{ $key }}" data-key="{{ . }}">{{ . }}</button>
        {{- end -}}
      {{- end -}}

    </div>
  {{- end -}}
</nav>
{{- end -}}
```

- [ ] **Step 2: Build and inspect HTML output**

Run: `hugo --minify 2>&1 | tail -10`
Expected: `Total in <N> ms`. No template errors.

Run: `grep -A2 "filter-disclosure" public/garden/index.html | head -20`
Expected: shows a `<details class="filter-disclosure">` block with a `<summary class="filter-chip is-disclosure">` containing "More tags" — because garden has 12 distinct tags and K=10. Should also show 2 secondary chips inside `.filter-secondary`.

Run: `grep -c "filter-disclosure" public/essays/index.html`
Expected: `0`. Essays has only 3 tags (below K), so no disclosure.

- [ ] **Step 3: Browser smoke check**

Open `http://localhost:1313/garden/`. The chip strip should:
- Show 10 primary tag chips
- Show a "More tags" pill at the end (still unstyled — CSS lands in Task 6)
- Clicking the pill toggles the `<details>` open (native behavior)
- Inside, a search input and 2 secondary chips visible

Open `http://localhost:1313/essays/`. The chip strip should look unchanged (no disclosure).

- [ ] **Step 4: Commit**

```bash
git add layouts/partials/filter-chips.html
git commit -m "Render two-tier filter chips for tag dim

Partial gains a section parameter and resolves primary tags from
site.Data.filter_chips.<section>.primary_tags (when present) or the first
K of the ranked values (default K=10). Secondary tags wrap inside a
native <details> element with a search input and a hidden empty-state
message. Other dimensions render unchanged.

CSS for the disclosure styling lands in the next commit; for now the
pill is functional but unstyled."
```

---

## Task 6: CSS — disclosure, search input, secondary chips

**Files:**
- Modify: `assets/css/main.css` (extends §16)

Add styling for the new elements. No new color tokens — reuses existing palette. No animations (reduced-motion safe by default).

- [ ] **Step 1: Append CSS to §16**

Find the end of §16 (currently the closing brace of `.filter-chip:focus-visible`, around line 626). Insert the following block right before the §17 comment header:

```css
/* Two-tier disclosure for the tag dim.
   .filter-disclosure is a flex child of .filter-dimension. When open, it
   takes flex-basis:100% so the body wraps onto a new line below the chips. */
.filter-disclosure[open] {
  flex-basis: 100%;
}
.filter-disclosure > summary {
  list-style: none;       /* drop default disclosure marker */
  cursor: pointer;
}
.filter-disclosure > summary::-webkit-details-marker {
  display: none;
}
.filter-disclosure > summary.filter-chip.is-disclosure {
  border-style: dashed;
  background: transparent;
  color: var(--color-ink-soft);
}
.filter-disclosure > summary.filter-chip.is-disclosure::before {
  content: "▾ ";
  display: inline-block;
  margin-right: 0.15rem;
}
.filter-disclosure[open] > summary.filter-chip.is-disclosure::before {
  content: "▴ ";
}
.filter-disclosure[open] > summary.filter-chip.is-disclosure {
  border-style: solid;
  border-color: var(--color-burgundy);
  color: var(--color-burgundy);
}
.filter-disclosure-count {
  margin-left: 0.25rem;
  font-style: italic;
}
.filter-disclosure-body {
  margin-top: 0.6rem;
  padding: 0.7rem 0.85rem;
  border: 1px dashed var(--color-rule);
  border-radius: 6px;
  background: var(--color-stone);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.filter-search {
  width: 100%;
  max-width: 28rem;
  padding: 0.35rem 0.6rem;
  border: 1px solid var(--color-rule);
  border-radius: 3px;
  background: var(--color-stone);
  color: var(--color-ink);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}
.filter-search:focus-visible {
  outline: 2px solid var(--color-burgundy);
  outline-offset: 1px;
  border-color: var(--color-burgundy);
}
.filter-secondary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.filter-secondary-empty {
  margin: 0;
  color: var(--color-ink-fade);
  font-style: italic;
  font-size: var(--text-xs);
}
```

- [ ] **Step 2: Build and verify the contrast checker still passes**

Run: `python3 tools/check-contrast.py && hugo --minify 2>&1 | tail -5`
Expected: contrast checker passes (no new tokens added); Hugo build succeeds.

- [ ] **Step 3: Browser visual check**

Open `http://localhost:1313/garden/`. Confirm:
- The "More tags" pill has dashed border and a `▾` glyph before the label
- Clicking opens the `<details>`; glyph flips to `▴` and pill border becomes solid burgundy
- The disclosure body has a dashed border, light background, and contains the search input + two secondary chips wrapping
- Layout still flows correctly at 320px width (responsive — chips wrap to multiple lines)

- [ ] **Step 4: Commit**

```bash
git add assets/css/main.css
git commit -m "Style the filter-chips disclosure and search input

Adds CSS to §16 for the new two-tier chip disclosure: dashed-border
summary chip with caret glyph, recessed disclosure body with dashed
outline, mono-font search input, and a small italic empty-state line.
No new color tokens — reuses existing palette. No animations."
```

---

## Task 7: JS — multi-select state for tag dim

**Files:**
- Modify: `assets/js/filter-chips.js`

The existing module treats every dim's state as a single string (`'all'` or a chip key). For the tag dim only, change to a `Set<string>`. Empty Set behaves like "All". Click handler toggles set membership; "All" chip clears the set; "All" chip's visual active state mirrors `tag` set emptiness.

Other dims keep current single-active behavior.

- [ ] **Step 1: Replace `assets/js/filter-chips.js`**

Replace the entire contents:

```javascript
// Multi-dimension AND filter chip strip.
// Used by both /essays/ and /garden/ (and any future filtered list).
//
// HTML contract (rendered by partials/filter-chips.html):
//   <nav class="filter-chips">
//     <div class="filter-dimension" data-dim="tag">
//       <button class="filter-chip is-active" data-dim="tag" data-key="all">All</button>
//       <button class="filter-chip" data-dim="tag" data-key="memory" data-tier="primary">memory</button>
//       …
//       <details class="filter-disclosure">
//         <summary class="filter-chip is-disclosure">
//           <span class="filter-disclosure-label">More tags</span>
//           <span class="filter-disclosure-count" hidden></span>
//         </summary>
//         <div class="filter-disclosure-body">
//           <input class="filter-search">
//           <div class="filter-secondary">
//             <button class="filter-chip" data-dim="tag" data-key="calvino" data-tier="secondary">…</button>
//             <p class="filter-secondary-empty" hidden>No matching tags.</p>
//           </div>
//         </div>
//       </details>
//     </div>
//   </nav>
//
// State model:
//   - tag dim: Set<string>. Empty Set === "All" active.
//   - other dims: string. 'all' === "All" active.
// AND-composition across dims; within tag dim, all selected tags must
// appear on the card (data-tags is space-separated).

export function setupFilterChips({
  containerSelector = '.filter-chips',
  cardSelector,
  sectionSelector,
  emptyStateSelector,
} = {}) {
  const container = document.querySelector(containerSelector);
  if (!container) return;
  if (!cardSelector) {
    console.warn('setupFilterChips: cardSelector is required');
    return;
  }

  // Initialize state per dim
  const state = {};
  container.querySelectorAll('.filter-dimension').forEach((dimEl) => {
    const dim = dimEl.getAttribute('data-dim');
    if (!dim) return;
    state[dim] = dim === 'tag' ? new Set() : 'all';
  });

  function cardMatches(card) {
    for (const dim in state) {
      if (dim === 'tag') {
        if (state.tag.size === 0) continue;
        const tags = (card.getAttribute('data-tags') || '').split(/\s+/).filter(Boolean);
        for (const wanted of state.tag) {
          if (!tags.includes(wanted)) return false;
        }
      } else {
        if (state[dim] === 'all') continue;
        const attr = card.getAttribute(`data-${dim}`) || '';
        if (attr !== state[dim]) return false;
      }
    }
    return true;
  }

  function applyFilters() {
    const cards = document.querySelectorAll(cardSelector);
    let visibleCount = 0;
    cards.forEach((card) => {
      const visible = cardMatches(card);
      if (visible) {
        card.removeAttribute('hidden');
        visibleCount += 1;
      } else {
        card.setAttribute('hidden', '');
      }
    });

    if (sectionSelector) {
      document.querySelectorAll(sectionSelector).forEach((section) => {
        const anyVisible = section.querySelector(`${cardSelector}:not([hidden])`);
        if (anyVisible) {
          section.removeAttribute('hidden');
        } else {
          section.setAttribute('hidden', '');
        }
      });
    }

    if (emptyStateSelector) {
      const empty = document.querySelector(emptyStateSelector);
      if (empty) {
        if (visibleCount === 0) {
          empty.removeAttribute('hidden');
        } else {
          empty.setAttribute('hidden', '');
        }
      }
    }

    refreshChipActiveStates();
  }

  function refreshChipActiveStates() {
    container.querySelectorAll('.filter-dimension').forEach((dimEl) => {
      const dim = dimEl.getAttribute('data-dim');
      if (!dim) return;
      dimEl.querySelectorAll('.filter-chip').forEach((c) => {
        const cKey = c.getAttribute('data-key');
        let active;
        if (dim === 'tag') {
          if (cKey === 'all') {
            active = state.tag.size === 0;
          } else if (cKey) {
            active = state.tag.has(cKey);
          } else {
            active = false; // disclosure summary chip; never marked active
          }
        } else {
          active = cKey === state[dim];
        }
        c.classList.toggle('is-active', active);
      });
    });
  }

  // Click handlers — only chips with a data-key participate.
  // The disclosure summary has no data-key, so clicks bubble up to the
  // <details> element which handles open/close natively.
  container.querySelectorAll('.filter-chip[data-key]').forEach((chip) => {
    chip.addEventListener('click', (e) => {
      e.preventDefault();
      const dim = chip.getAttribute('data-dim');
      const key = chip.getAttribute('data-key');
      if (!dim || !key) return;

      if (dim === 'tag') {
        if (key === 'all') {
          state.tag.clear();
        } else if (state.tag.has(key)) {
          state.tag.delete(key);
        } else {
          state.tag.add(key);
        }
      } else {
        state[dim] = key;
      }

      applyFilters();
    });
  });

  applyFilters();
}
```

- [ ] **Step 2: Build and verify**

Run: `hugo --minify 2>&1 | tail -5`
Expected: build succeeds.

- [ ] **Step 3: Browser interaction check**

Open `http://localhost:1313/garden/`. Test:
- Click `memory` → notes narrow to memory-tagged ones; chip becomes burgundy
- Click `narrative` → notes narrow further (must have BOTH); both chips burgundy
- Click `memory` again → it deselects; only narrative-tagged notes shown
- Click `All` → all tags clear; full grid restored

The "More tags" disclosure is still inert beyond open/close — search and secondary chip selection wired up in Task 8.

- [ ] **Step 4: Commit**

```bash
git add assets/js/filter-chips.js
git commit -m "Multi-select state for tag dim in filter-chips.js

State.tag becomes a Set<string>; empty set === 'All' active. Clicking
a tag chip toggles set membership; clicking 'All' clears the set.
Other dims keep single-active behavior. AND-composition across dims is
unchanged; within tag dim, all selected tags must appear on the card.

Disclosure interaction (search input, keyboard nav, summary count) lands
in subsequent commits."
```

---

## Task 8: JS — live-filter search input + empty state

**Files:**
- Modify: `assets/js/filter-chips.js`

When the user types in the search input, toggle `hidden` on each secondary chip whose `data-key` doesn't substring-match the (lowercase) input value. Show "No matching tags." when zero chips match. On disclosure open, focus moves to the search input. Esc clears the input and re-shows all secondary chips.

- [ ] **Step 1: Add disclosure setup function**

In `assets/js/filter-chips.js`, insert the following helper between `refreshChipActiveStates` and the `// Click handlers — only chips with a data-key …` comment:

```javascript
  function setupDisclosure() {
    const details = container.querySelector('.filter-disclosure');
    if (!details) return;
    const input = details.querySelector('.filter-search');
    const secondary = details.querySelector('.filter-secondary');
    const empty = details.querySelector('.filter-secondary-empty');
    if (!input || !secondary || !empty) return;

    function applySearch() {
      const q = input.value.trim().toLowerCase();
      const chips = secondary.querySelectorAll('.filter-chip[data-tier="secondary"]');
      let visible = 0;
      chips.forEach((chip) => {
        const key = (chip.getAttribute('data-key') || '').toLowerCase();
        const matches = q === '' || key.includes(q);
        if (matches) {
          chip.removeAttribute('hidden');
          visible += 1;
        } else {
          chip.setAttribute('hidden', '');
        }
      });
      if (visible === 0 && q !== '') {
        empty.removeAttribute('hidden');
      } else {
        empty.setAttribute('hidden', '');
      }
    }

    input.addEventListener('input', applySearch);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        input.value = '';
        applySearch();
        input.focus();
      }
    });

    // Focus the search input when the disclosure opens.
    details.addEventListener('toggle', () => {
      if (details.open) {
        input.focus();
      }
    });
  }
```

- [ ] **Step 2: Call `setupDisclosure()` from the entry function**

The tail of `setupFilterChips` currently ends with:

```javascript
  container.querySelectorAll('.filter-chip[data-key]').forEach((chip) => {
    chip.addEventListener('click', (e) => {
      // … unchanged …
    });
  });

  applyFilters();
}
```

Insert one new line — `setupDisclosure();` — directly above the existing `applyFilters();` call so the tail becomes:

```javascript
  container.querySelectorAll('.filter-chip[data-key]').forEach((chip) => {
    chip.addEventListener('click', (e) => {
      // … unchanged …
    });
  });

  setupDisclosure();
  applyFilters();
}
```

- [ ] **Step 3: Build and verify**

Run: `hugo --minify 2>&1 | tail -5`
Expected: build succeeds.

- [ ] **Step 4: Browser interaction check**

Open `http://localhost:1313/garden/`. Click "More tags" to open the disclosure. Confirm:
- Search input has focus on open
- Typing `cal` narrows visible secondary chips (assuming `calvino` is in the secondary set — it should be, since it's one of the lower-count tags)
- Typing `xyz` shows the "No matching tags." line
- Clearing the input restores all secondary chips
- Pressing Esc clears the input and restores chips
- Clicking a secondary chip toggles it as a tag selection (existing behavior from Task 7)

- [ ] **Step 5: Commit**

```bash
git add assets/js/filter-chips.js
git commit -m "Live-filter search input inside filter disclosure

Typing in .filter-search substring-matches secondary chip data-keys
(case-insensitive); non-matching chips get hidden. The empty-state
message shows when zero chips match. Esc clears the search; the
disclosure auto-focuses the input on open."
```

---

## Task 9: JS — keyboard navigation

**Files:**
- Modify: `assets/js/filter-chips.js`

Arrow Down from the search input moves focus to the first visible secondary chip. Arrow Left/Right between visible chips (skipping `hidden` ones), no wraparound. Arrow Up from any visible chip returns focus to the search input. Enter on a chip toggles selection (this is the chip's native button behavior — already wired in Task 7).

- [ ] **Step 1: Extend `setupDisclosure`**

After Task 8, the inside of `setupDisclosure` ends with:

```javascript
    input.addEventListener('input', applySearch);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        input.value = '';
        applySearch();
        input.focus();
      }
    });

    details.addEventListener('toggle', () => {
      if (details.open) {
        input.focus();
      }
    });
  }
```

Replace that whole tail (from `input.addEventListener('input', applySearch);` through the closing `}` of `setupDisclosure`) with:

```javascript
    input.addEventListener('input', applySearch);

    function visibleSecondaryChips() {
      return Array.from(
        secondary.querySelectorAll('.filter-chip[data-tier="secondary"]:not([hidden])')
      );
    }

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        input.value = '';
        applySearch();
        input.focus();
        return;
      }
      if (e.key === 'ArrowDown') {
        const chips = visibleSecondaryChips();
        if (chips.length > 0) {
          e.preventDefault();
          chips[0].focus();
        }
      }
    });

    secondary.addEventListener('keydown', (e) => {
      const target = e.target;
      if (!(target instanceof HTMLElement)) return;
      if (!target.matches('.filter-chip[data-tier="secondary"]')) return;
      const chips = visibleSecondaryChips();
      const idx = chips.indexOf(target);
      if (idx === -1) return;
      if (e.key === 'ArrowRight') {
        if (idx < chips.length - 1) {
          e.preventDefault();
          chips[idx + 1].focus();
        }
      } else if (e.key === 'ArrowLeft') {
        if (idx > 0) {
          e.preventDefault();
          chips[idx - 1].focus();
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        input.focus();
      }
    });

    details.addEventListener('toggle', () => {
      if (details.open) {
        input.focus();
      }
    });
  }
```

- [ ] **Step 2: Build and verify**

Run: `hugo --minify 2>&1 | tail -5`
Expected: build succeeds.

- [ ] **Step 3: Keyboard-only walkthrough**

Open `http://localhost:1313/garden/`. Click "More tags" to open. Test:
- Tab to the search input (or it's already focused on open)
- Type `c` → only chips containing "c" remain visible
- Press Arrow Down → focus moves to first visible chip
- Press Arrow Right → focus moves to next visible chip; stops at last
- Press Arrow Left → focus moves back; stops at first
- Press Arrow Up → focus returns to search input
- Press Enter on a focused chip → it toggles to active (burgundy)
- Press Esc with input focused → input clears, all chips visible again

- [ ] **Step 4: Commit**

```bash
git add assets/js/filter-chips.js
git commit -m "Keyboard navigation for filter-chips disclosure

Arrow Down from search input focuses first visible secondary chip;
Arrow Left/Right step between visible chips (no wraparound, hidden chips
skipped); Arrow Up from any chip returns focus to the search input.
Enter on a focused chip toggles selection via the chip's native button
behavior."
```

---

## Task 10: JS — disclosure summary count indicator

**Files:**
- Modify: `assets/js/filter-chips.js`

When the user has secondary tags selected and the disclosure is collapsed, the summary should indicate the active state. Format: 1 secondary tag → `· calvino`; 2+ secondary tags → `· N active`. The count element is already in the DOM (rendered hidden by the partial); JS toggles its content and `hidden` attribute.

A "secondary" tag is one whose chip carries `data-tier="secondary"`. Primary tag selections do not contribute to the count (they're already visible in the resting strip).

- [ ] **Step 1: Add `refreshDisclosureSummary` helper inside `setupFilterChips`**

In `assets/js/filter-chips.js`, insert this helper just below `refreshChipActiveStates`:

```javascript
  function refreshDisclosureSummary() {
    const countEl = container.querySelector('.filter-disclosure-count');
    if (!countEl) return;
    if (!state.tag) return;
    // Find which selected tag keys are secondary-tier
    const secondaryEls = container.querySelectorAll(
      '.filter-chip[data-tier="secondary"]'
    );
    const secondaryKeys = new Set(
      Array.from(secondaryEls)
        .map((el) => el.getAttribute('data-key'))
        .filter(Boolean)
    );
    const activeSecondary = Array.from(state.tag).filter((k) =>
      secondaryKeys.has(k)
    );
    if (activeSecondary.length === 0) {
      countEl.textContent = '';
      countEl.setAttribute('hidden', '');
    } else if (activeSecondary.length === 1) {
      countEl.textContent = ` · ${activeSecondary[0]}`;
      countEl.removeAttribute('hidden');
    } else {
      countEl.textContent = ` · ${activeSecondary.length} active`;
      countEl.removeAttribute('hidden');
    }
  }
```

- [ ] **Step 2: Call it from `applyFilters`**

`applyFilters` currently ends with a single `refreshChipActiveStates();` call before its closing brace. Add `refreshDisclosureSummary();` immediately after it so the function tail reads:

```javascript
    refreshChipActiveStates();
    refreshDisclosureSummary();
  }
```

- [ ] **Step 3: Build and verify**

Run: `hugo --minify 2>&1 | tail -5`
Expected: build succeeds.

- [ ] **Step 4: Browser interaction check**

Open `http://localhost:1313/garden/`. Test:
- Open disclosure, click `calvino` (or any secondary tag), close disclosure → summary now reads "More tags · calvino"
- Reopen and click another secondary tag → close → summary reads "More tags · 2 active"
- Click `All` → summary clears; reads just "More tags"
- Selecting a primary tag (e.g. `memory`) does NOT affect the summary text

- [ ] **Step 5: Commit**

```bash
git add assets/js/filter-chips.js
git commit -m "Surface active secondary tags in disclosure summary

When the disclosure is collapsed and one or more secondary tags are
selected, the summary shows them: single tag → '· calvino', multiple
→ '· N active'. Primary tag selections do not contribute (they're
already visible in the resting strip)."
```

---

## Task 11: End-to-end verification with temporary low K

**Files:**
- Modify: `data/filter-chips.yaml` (temporarily, then revert)

Garden's 12 fixture tags + K=10 mean the disclosure renders with only 2 secondary chips, which is a thin smoke test. Lower K to 4 temporarily so the disclosure handles a larger secondary set, then revert.

- [ ] **Step 1: Lower K for both sections**

Edit `data/filter-chips.yaml` to:

```yaml
garden:
  primary_top_k: 4
essays:
  primary_top_k: 4
```

- [ ] **Step 2: Rebuild and walkthrough**

Run: `hugo --minify 2>&1 | tail -5`
Expected: build succeeds.

Open `http://localhost:1313/garden/`. With K=4, the strip has 4 primary chips + a "More tags" disclosure with 8 secondary chips.

Run through the full acceptance criteria from the spec:
- [ ] Disclosure renders; clicking opens with native `<details>`
- [ ] Search input focuses on open
- [ ] Typing `g` narrows visible secondary chips (matches `glass`, `mystery`? — substring on `data-key`; check what's actually there)
- [ ] "No matching tags" appears for `xxx`
- [ ] Esc clears input and refocuses
- [ ] Arrow Down → first visible chip; Arrow Left/Right step; Arrow Up → input
- [ ] Enter on chip toggles it active
- [ ] Click primary chip + secondary chip → AND-composes (cards must have both)
- [ ] Click "All" → tag selections clear
- [ ] Close disclosure with one secondary tag selected → summary reads "· <tagname>"
- [ ] Close with two secondary tags → summary reads "· 2 active"

- [ ] **Step 3: JS-disabled smoke check**

In the browser dev tools, disable JavaScript and reload `/garden/`. Confirm:
- Page loads
- `<details>` opens and closes when clicked (native)
- Chip clicks do nothing (expected — same as today)
- No console errors

Re-enable JS for subsequent tests.

- [ ] **Step 4: Run all CI gates locally**

Run:
```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && \
python3 -m unittest tools/test_check_fixtures.py -v && \
python3 tools/check_garden_fixtures.py && \
python3 -m unittest tools/test_check_garden_fixtures.py -v && \
python3 tools/check_filter_chips_config.py && \
python3 -m unittest tools/test_check_filter_chips_config.py -v && \
hugo --minify
```
Expected: every step exits 0; the Hugo build succeeds.

- [ ] **Step 5: Revert K override**

Edit `data/filter-chips.yaml` back to:

```yaml
# Filter-chips configuration — controls the primary tag set for each
# section's filter strip on the index page.
#
# Schema (per top-level section key):
#   primary_tags:    ordered list of tag slugs to render as primary chips.
#                    When omitted, falls back to top-K by note count.
#   primary_top_k:   integer; overrides the default K=10 used by auto-mode.
#                    Only consulted when primary_tags is absent or empty.
#
# Linter: tools/check_filter_chips_config.py validates that every entry in
# primary_tags resolves to a tag used by a non-draft note in the matching
# section. Stale entries fail the build.

garden:
  # Auto top-10 fallback applies until curated.
essays:
  # Auto top-10 fallback applies until curated.
```

Run: `hugo --minify 2>&1 | tail -5`
Expected: build succeeds. Garden disclosure still renders (12 tags > 10).

- [ ] **Step 6: Commit (no functional change — empty stub restored)**

This step has nothing to commit if the file is already at the committed state. Verify:

Run: `git status data/filter-chips.yaml`
Expected: `nothing to commit` for that file.

If for any reason it differs from Task 3's committed state, restore it and skip the commit.

---

## Task 12: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

Document the new feature in the existing CLAUDE.md so future sessions know about it without spelunking. Update: filter-chips description in §Architecture, add the new linter to the commands list, mention the new data file, update the project status block.

- [ ] **Step 1: Update the `## Commands` section**

Find the commands list (around line 11–17). Add two new lines after the garden linter unit-test line:

```
- `python3 tools/check_filter_chips_config.py` — filter-chips config linter (CI gate)
- `python3 -m unittest tools/test_check_filter_chips_config.py -v` — filter-chips linter unit tests (CI gate)
```

- [ ] **Step 2: Update the Filter chips paragraph in §Architecture**

Find the "Filter chips" subsection. Replace its body with:

```markdown
### Filter chips

`/essays/` and `/garden/` both render filter chip strips via the shared `partials/filter-chips.html` partial (essays: tag / series / year; garden: tag / flavor / stage). **Suppression rule:** dimensions with <2 distinct values don't render.

**Two-tier rendering** (tag dim only): primary chips render inline in the strip. When the section has more tags than K (default 10), the remaining tags become "secondary" and live inside a native `<details>` disclosure with a search input. The primary set is sourced from `data/filter-chips.yaml` `<section>.primary_tags` (manual curation, ordered) or computed as the top-K by note count when curation is absent (alphabetical for ties). `data/filter-chips.yaml` also accepts `<section>.primary_top_k` to override K per section. `tools/check_filter_chips_config.py` validates every curated tag against the live taxonomy.

**Active-state model:** per-dimension AND across dimensions; **multi-select within the tag dimension only** (`memory` + `calvino` → notes with both). Other dims (flavor, stage, series, year) stay single-active because their values are mutually exclusive. Clicking an active tag chip deselects it; clicking "All" clears the entire tag selection. The disclosure summary shows active secondary tags when collapsed (`▾ More tags · calvino` or `· N active`).

**Search inside the disclosure:** substring match, case-insensitive, applied to secondary chips' `data-key`. Live-filter — the chips themselves narrow as you type. Keyboard navigation: Arrow Down from input → first visible chip, Arrow Left/Right between visible chips (no wraparound), Arrow Up returns to input, Enter toggles, Esc clears.

The shared logic lives in `assets/js/filter-chips.js`; `essay.js` and `garden.js` each call `setupFilterChips({ containerSelector, cardSelector, sectionSelector?, emptyStateSelector? })`. Garden's empty-intersection state: section wrappers with no visible tiles get `hidden`; a `.garden-empty` element shows when zero tiles globally pass.

**No in-strip no-JS fallback.** Chips are `<button>` elements (no anchor href). With JS disabled, the disclosure still opens and closes (native `<details>`), but chips and the search input are inert. Tag and series taxonomy pages still exist at `/tags/<slug>/` and `/series/<slug>/` (Hugo auto-generated) for direct entry.

Taxonomies are declared in `hugo.yaml` (`tag: tags`, `series: series`).
```

- [ ] **Step 3: Update the Deployment section**

Find the Deployment section. Replace the line listing CI steps:

```markdown
**Verify CSS contrast (WCAG)** → **Verify essay fixtures** → **Run essay linter unit tests** → **Verify garden fixtures** → **Run garden linter unit tests** → Build with Hugo → Upload artifact → Deploy. All five Python checks must pass before the Hugo build.
```

with:

```markdown
**Verify CSS contrast (WCAG)** → **Verify essay fixtures** → **Run essay linter unit tests** → **Verify garden fixtures** → **Run garden linter unit tests** → **Verify filter-chips config** → **Run filter-chips linter unit tests** → Build with Hugo → Upload artifact → Deploy. All seven Python checks must pass before the Hugo build.
```

- [ ] **Step 4: Update the Project status section**

At the end of `## Project status (2026-05-07)`, before the "**Phase 2 — remaining slices (not started).**" subsection, add a new completed-slice paragraph:

```markdown
**Phase 2 polish — tag two-tier filter complete (2026-05-08).** Shared `partials/filter-chips.html` upgraded to render the tag dim in two tiers: curated primary chips from `data/filter-chips.yaml` (or top-K auto-fallback by note count, K=10) plus a native `<details>` disclosure with a search input that live-filters secondary chips. Multi-select within tag dim (`memory` + `calvino` → AND), single-active for flavor/stage/series/year. Keyboard nav (arrow keys + Esc); active-secondary tags surface in the disclosure summary when collapsed. New CI gate: `tools/check_filter_chips_config.py` validates curated tags against the live taxonomy. Both `/garden/` and `/essays/` get the upgrade automatically; suppression keeps the disclosure invisible on small tag sets (essays' 3-tag fixture set is below threshold).
```

- [ ] **Step 5: Verify CLAUDE.md is internally consistent**

Read through CLAUDE.md once. Confirm:
- Commands list has 7 Python entries (4 verifiers + 3 unit-test commands now — wait, that's contrast (1), essay verifier + tests (2), garden verifier + tests (2), filter-chips verifier + tests (2). 7 Python commands. Same count as the CI step count.)
- Filter chips paragraph reads coherently end-to-end
- Project status mentions the new slice and date
- No dead references to old behavior

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "Document tag two-tier filter in CLAUDE.md

Updates the filter-chips architecture section, commands list, deployment
gate sequence, and project status to reflect the two-tier rendering
behavior, the new data/filter-chips.yaml config, the multi-select tag
dimension, and the new CI gate."
```

---

## Final verification

After Task 12, run the full CI gate sequence one more time:

```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && \
python3 -m unittest tools/test_check_fixtures.py -v && \
python3 tools/check_garden_fixtures.py && \
python3 -m unittest tools/test_check_garden_fixtures.py -v && \
python3 tools/check_filter_chips_config.py && \
python3 -m unittest tools/test_check_filter_chips_config.py -v && \
hugo --minify
```

Expected: all green, Hugo build succeeds.

Also: run `git log --oneline master..HEAD` to confirm the commit history is one commit per task (12 commits total). Push when ready.
