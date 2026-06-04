# LHCI URL Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship slice 4.1 of the LHCI representative-page-set design — a sibling linter pair that fast-fails on `lighthouserc.{json,mobile.json}` URL drift in seconds instead of letting LHCI burn a CI cycle 404'ing for ~3 min.

**Architecture:** A single Python module `tools/check_lhci_urls.py` with three pure check functions (`check_existence`, `check_equality`, `check_assert_matrix`) and a `run()` orchestrator that accepts injected paths for testability. `main()` is the CLI entrypoint; `tools/test_check_lhci_urls.py` calls the pure helpers and `run()` directly against `tempfile.TemporaryDirectory`-backed fakes. Two CI steps added after `check_smoke.py` in `.github/workflows/hugo.yaml`.

**Tech Stack:** Python 3 stdlib only (`json`, `re`, `pathlib`, `unittest`, `tempfile`). No new dependencies. Mirrors the shape of `tools/check_org_assets.py` + `tools/test_check_org_assets.py`.

---

## File structure

**Create:**
- `tools/check_lhci_urls.py` — 3 pure check functions + `run()` + `main()`. ~80 lines.
- `tools/test_check_lhci_urls.py` — ~16 test methods, ~200 lines.

**Modify:**
- `.github/workflows/hugo.yaml` — add 2 CI steps between current smoke step and page-weights step (lines ~169–175).
- `CLAUDE.md` — update linter-pair count (25→26 pairs), CI step count (63→65), and add the new linter to the §"Commands" list.

**Memory updates (after merge):**
- Create `.claude/memory/project_lhci_url_validator_complete.md` — ship report.
- Update `.claude/memory/MEMORY.md` index entry for `project_lhci_representative_pages_queued.md` → mark 4.1 shipped, 4.2 + 4.3 still queued.
- Update `.claude/memory/project_lhci_representative_pages_queued.md` body to reflect 4.1 shipped, repoint the index to the ship-report memory.

---

## Task 1: Scaffold module with `file_for_url` helper + existence check (TDD)

**Files:**
- Create: `tools/check_lhci_urls.py`
- Create: `tools/test_check_lhci_urls.py`

- [ ] **Step 1: Write the failing existence tests**

Create `tools/test_check_lhci_urls.py` with the test scaffolding and the first three tests for `file_for_url` + `check_existence`:

```python
"""Unit tests for check_lhci_urls.py."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_lhci_urls as mod


def _touch(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("<html><body>ok</body></html>", encoding="utf-8")


class TestFileForUrl(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="check_lhci_urls_test_"))
        self.public = self.tmp / "public"
        self.public.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_root_url_maps_to_index_html(self) -> None:
        self.assertEqual(
            mod.file_for_url(self.public, "http://localhost/"),
            self.public / "index.html",
        )

    def test_nested_path_maps_to_path_index_html(self) -> None:
        self.assertEqual(
            mod.file_for_url(self.public, "http://localhost/essays/example-one/"),
            self.public / "essays/example-one/index.html",
        )

    def test_strips_localhost_prefix_and_trailing_slash(self) -> None:
        # Trailing slash absent should still resolve.
        self.assertEqual(
            mod.file_for_url(self.public, "http://localhost/about"),
            self.public / "about/index.html",
        )


class TestCheckExistence(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="check_lhci_urls_test_"))
        self.public = self.tmp / "public"
        self.public.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_all_urls_resolve(self) -> None:
        _touch(self.public / "index.html")
        _touch(self.public / "essays/example-one/index.html")
        urls = ["http://localhost/", "http://localhost/essays/example-one/"]
        errors = mod.check_existence(self.public, urls, "lighthouserc.json")
        self.assertEqual(errors, [])

    def test_missing_url_reports_relpath_and_source(self) -> None:
        _touch(self.public / "index.html")
        urls = ["http://localhost/", "http://localhost/missing/"]
        errors = mod.check_existence(self.public, urls, "lighthouserc.json")
        self.assertEqual(len(errors), 1)
        self.assertIn("lighthouserc.json", errors[0])
        self.assertIn("/missing/", errors[0])
        self.assertIn("missing/index.html", errors[0])
```

- [ ] **Step 2: Run tests to verify they fail with ImportError**

Run: `cd tools && python3 -m unittest test_check_lhci_urls.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'check_lhci_urls'`.

- [ ] **Step 3: Write the minimal implementation**

Create `tools/check_lhci_urls.py`:

```python
"""Validate that LHCI URLs resolve to built pages.

Reads lighthouserc.json + lighthouserc.mobile.json. Three checks:
existence (each URL → public/<path>/index.html), desktop/mobile equality
(ordered list), and assertMatrix regex coverage (every matchingUrlPattern
matches at least one URL in collect.url).

Runs in CI after `hugo --minify` and before LHCI to fast-fail on
fixture-slug drift in seconds, not minutes. Paired with
tools/test_check_lhci_urls.py.

Exit codes:
  0 — all checks pass
  1 — one or more validation failures
  2 — bootstrap failure (public/ missing, config missing/unparseable)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


DESKTOP_CONFIG = Path("lighthouserc.json")
MOBILE_CONFIG = Path("lighthouserc.mobile.json")
PUBLIC_DIR = Path("public")
HOST_PREFIX = "http://localhost"


def file_for_url(public: Path, url: str) -> Path:
    """Map an LHCI URL to its built public/ file path."""
    if url.startswith(HOST_PREFIX):
        url = url[len(HOST_PREFIX):]
    rel = url.strip("/")
    if not rel:
        return public / "index.html"
    return public / rel / "index.html"


def check_existence(public: Path, urls: list[str], source: str) -> list[str]:
    """Each URL must resolve to public/<path>/index.html."""
    errors: list[str] = []
    for url in urls:
        f = file_for_url(public, url)
        if not f.is_file():
            relpath = f.relative_to(public)
            errors.append(f"{source}: {url}: missing file at {relpath}")
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m unittest test_check_lhci_urls.py -v`
Expected: PASS — 5 tests run.

- [ ] **Step 5: Commit**

```bash
git add tools/check_lhci_urls.py tools/test_check_lhci_urls.py
git commit -m "feat(lhci-4.1): scaffold check_lhci_urls — file_for_url + check_existence"
```

---

## Task 2: Desktop/mobile equality check (TDD)

**Files:**
- Modify: `tools/test_check_lhci_urls.py` — append `TestCheckEquality` class
- Modify: `tools/check_lhci_urls.py` — append `check_equality` function

- [ ] **Step 1: Write the failing equality tests**

Append to `tools/test_check_lhci_urls.py`:

```python
class TestCheckEquality(unittest.TestCase):
    def test_identical_lists_pass(self) -> None:
        urls = ["http://localhost/", "http://localhost/essays/"]
        self.assertEqual(mod.check_equality(urls, urls), [])

    def test_mobile_extra_url_fails(self) -> None:
        desktop = ["http://localhost/", "http://localhost/essays/"]
        mobile = desktop + ["http://localhost/garden/"]
        errors = mod.check_equality(desktop, mobile)
        self.assertEqual(len(errors), 1)
        self.assertIn("1 added", errors[0])
        self.assertIn("0 removed", errors[0])

    def test_desktop_extra_url_fails(self) -> None:
        desktop = ["http://localhost/", "http://localhost/essays/", "http://localhost/garden/"]
        mobile = ["http://localhost/", "http://localhost/essays/"]
        errors = mod.check_equality(desktop, mobile)
        self.assertEqual(len(errors), 1)
        self.assertIn("0 added", errors[0])
        self.assertIn("1 removed", errors[0])

    def test_reordered_lists_fail(self) -> None:
        desktop = ["http://localhost/", "http://localhost/essays/"]
        mobile = ["http://localhost/essays/", "http://localhost/"]
        errors = mod.check_equality(desktop, mobile)
        self.assertEqual(len(errors), 1)
        self.assertIn("ordering differs", errors[0])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m unittest test_check_lhci_urls.TestCheckEquality -v`
Expected: FAIL with `AttributeError: module 'check_lhci_urls' has no attribute 'check_equality'`.

- [ ] **Step 3: Write the minimal implementation**

Append to `tools/check_lhci_urls.py`:

```python
def check_equality(desktop_urls: list[str], mobile_urls: list[str]) -> list[str]:
    """The two collect.url arrays must be ordered-equal."""
    if desktop_urls == mobile_urls:
        return []
    d_set = set(desktop_urls)
    m_set = set(mobile_urls)
    added = m_set - d_set
    removed = d_set - m_set
    if added or removed:
        return [
            f"lighthouserc.mobile.json: collect.url differs from lighthouserc.json "
            f"({len(added)} added, {len(removed)} removed)"
        ]
    return [
        "lighthouserc.mobile.json: collect.url ordering differs from lighthouserc.json"
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m unittest test_check_lhci_urls -v`
Expected: PASS — 9 tests total (5 existing + 4 new).

- [ ] **Step 5: Commit**

```bash
git add tools/check_lhci_urls.py tools/test_check_lhci_urls.py
git commit -m "feat(lhci-4.1): check_equality — ordered desktop/mobile URL parity"
```

---

## Task 3: assertMatrix regex coverage check (TDD)

**Files:**
- Modify: `tools/test_check_lhci_urls.py` — append `TestCheckAssertMatrix` class
- Modify: `tools/check_lhci_urls.py` — append `check_assert_matrix` function

- [ ] **Step 1: Write the failing assertMatrix tests**

Append to `tools/test_check_lhci_urls.py`:

```python
class TestCheckAssertMatrix(unittest.TestCase):
    def test_matrix_pattern_matches_url(self) -> None:
        config = {
            "ci": {
                "assert": {
                    "assertMatrix": [
                        {"matchingUrlPattern": "/essays/example-one/$"}
                    ]
                }
            }
        }
        urls = ["http://localhost/essays/example-one/"]
        errors = mod.check_assert_matrix(config, urls, "lighthouserc.mobile.json")
        self.assertEqual(errors, [])

    def test_matrix_pattern_matches_no_url(self) -> None:
        config = {
            "ci": {
                "assert": {
                    "assertMatrix": [
                        {"matchingUrlPattern": "/essays/retired-slug/$"}
                    ]
                }
            }
        }
        urls = ["http://localhost/essays/example-one/"]
        errors = mod.check_assert_matrix(config, urls, "lighthouserc.mobile.json")
        self.assertEqual(len(errors), 1)
        self.assertIn("assertMatrix[0]", errors[0])
        self.assertIn("retired-slug", errors[0])
        self.assertIn("matches no URL", errors[0])

    def test_matrix_absent_returns_no_errors(self) -> None:
        config = {"ci": {"assert": {}}}
        errors = mod.check_assert_matrix(config, [], "lighthouserc.json")
        self.assertEqual(errors, [])

    def test_invalid_regex_reports_syntax_error(self) -> None:
        config = {
            "ci": {
                "assert": {
                    "assertMatrix": [
                        {"matchingUrlPattern": "/["}
                    ]
                }
            }
        }
        urls = ["http://localhost/"]
        errors = mod.check_assert_matrix(config, urls, "lighthouserc.mobile.json")
        self.assertEqual(len(errors), 1)
        self.assertIn("not a valid regex", errors[0])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m unittest test_check_lhci_urls.TestCheckAssertMatrix -v`
Expected: FAIL with `AttributeError: module 'check_lhci_urls' has no attribute 'check_assert_matrix'`.

- [ ] **Step 3: Write the minimal implementation**

Append to `tools/check_lhci_urls.py`:

```python
def check_assert_matrix(config: dict, urls: list[str], source: str) -> list[str]:
    """Each assertMatrix matchingUrlPattern must match at least one URL."""
    errors: list[str] = []
    matrix = config.get("ci", {}).get("assert", {}).get("assertMatrix", [])
    for i, entry in enumerate(matrix):
        pattern = entry.get("matchingUrlPattern", "")
        try:
            rx = re.compile(pattern)
        except re.error as e:
            errors.append(
                f"{source}: assertMatrix[{i}].matchingUrlPattern "
                f"'{pattern}' is not a valid regex: {e}"
            )
            continue
        if not any(rx.search(u) for u in urls):
            errors.append(
                f"{source}: assertMatrix[{i}].matchingUrlPattern "
                f"'{pattern}' matches no URL in collect.url"
            )
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m unittest test_check_lhci_urls -v`
Expected: PASS — 13 tests total.

- [ ] **Step 5: Commit**

```bash
git add tools/check_lhci_urls.py tools/test_check_lhci_urls.py
git commit -m "feat(lhci-4.1): check_assert_matrix — regex coverage + syntax validation"
```

---

## Task 4: `run()` orchestrator + bootstrap edges (TDD)

**Files:**
- Modify: `tools/test_check_lhci_urls.py` — append `TestRun` class
- Modify: `tools/check_lhci_urls.py` — append `run()` and `main()` + `if __name__`

- [ ] **Step 1: Write the failing orchestrator tests**

Append to `tools/test_check_lhci_urls.py`. The helper class manages a temp dir with both configs and a fake `public/`:

```python
class TestRun(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="check_lhci_urls_test_"))
        self.public = self.tmp / "public"
        self.public.mkdir()
        self.desktop_config = self.tmp / "lighthouserc.json"
        self.mobile_config = self.tmp / "lighthouserc.mobile.json"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_configs(
        self, urls: list[str], mobile_matrix: list[dict] | None = None
    ) -> None:
        self.desktop_config.write_text(
            json.dumps({"ci": {"collect": {"url": urls}}}), encoding="utf-8"
        )
        mobile_body: dict = {"ci": {"collect": {"url": urls}}}
        if mobile_matrix is not None:
            mobile_body["ci"]["assert"] = {"assertMatrix": mobile_matrix}
        self.mobile_config.write_text(json.dumps(mobile_body), encoding="utf-8")

    def _run(self) -> tuple[int, list[str]]:
        return mod.run(self.public, self.desktop_config, self.mobile_config)

    def test_clean_run_returns_zero(self) -> None:
        _touch(self.public / "index.html")
        _touch(self.public / "essays/example-one/index.html")
        self._write_configs(
            ["http://localhost/", "http://localhost/essays/example-one/"],
            mobile_matrix=[{"matchingUrlPattern": "/essays/example-one/$"}],
        )
        code, errors = self._run()
        self.assertEqual(code, 0, msg=f"errors={errors}")
        self.assertEqual(errors, [])

    def test_multiple_failures_aggregate(self) -> None:
        # Existence: /missing/ won't resolve. Equality: mobile has extra.
        # AssertMatrix: pattern matches nothing.
        _touch(self.public / "index.html")
        self.desktop_config.write_text(
            json.dumps({"ci": {"collect": {"url": ["http://localhost/", "http://localhost/missing/"]}}}),
            encoding="utf-8",
        )
        self.mobile_config.write_text(
            json.dumps({
                "ci": {
                    "collect": {"url": ["http://localhost/", "http://localhost/missing/", "http://localhost/extra/"]},
                    "assert": {"assertMatrix": [{"matchingUrlPattern": "/retired/$"}]},
                }
            }),
            encoding="utf-8",
        )
        code, errors = self._run()
        self.assertEqual(code, 1)
        # At least: 2 existence errors (one per config) for /missing/ + 1 existence for /extra/ + 1 equality + 1 regex
        joined = "\n".join(errors)
        self.assertIn("/missing/", joined)
        self.assertIn("/extra/", joined)
        self.assertIn("1 added", joined)
        self.assertIn("/retired/", joined)

    def test_missing_public_dir_returns_two(self) -> None:
        shutil.rmtree(self.public)
        self._write_configs(["http://localhost/"])
        code, errors = self._run()
        self.assertEqual(code, 2)
        self.assertTrue(any("public/" in e for e in errors))

    def test_missing_config_returns_two(self) -> None:
        _touch(self.public / "index.html")
        self.desktop_config.write_text(
            json.dumps({"ci": {"collect": {"url": ["http://localhost/"]}}}), encoding="utf-8"
        )
        # mobile_config not written
        code, errors = self._run()
        self.assertEqual(code, 2)
        self.assertTrue(any("lighthouserc.mobile.json" in e for e in errors))

    def test_unparseable_json_returns_two(self) -> None:
        _touch(self.public / "index.html")
        self.desktop_config.write_text("not json {", encoding="utf-8")
        self.mobile_config.write_text(
            json.dumps({"ci": {"collect": {"url": ["http://localhost/"]}}}), encoding="utf-8"
        )
        code, errors = self._run()
        self.assertEqual(code, 2)
        self.assertTrue(any("invalid JSON" in e or "JSON" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools && python3 -m unittest test_check_lhci_urls.TestRun -v`
Expected: FAIL with `AttributeError: module 'check_lhci_urls' has no attribute 'run'`.

- [ ] **Step 3: Write the minimal implementation**

Append to `tools/check_lhci_urls.py`:

```python
def run(
    public_dir: Path,
    desktop_config: Path,
    mobile_config: Path,
) -> tuple[int, list[str]]:
    """Orchestrate the three checks. Returns (exit_code, error_lines).

    exit_code 2 reserved for bootstrap failures (missing public/, missing
    config, unparseable JSON). exit_code 1 for validation failures. 0 on
    clean.
    """
    if not public_dir.is_dir():
        return 2, [
            f"check_lhci_urls: {public_dir}/ not found. Run `hugo --minify` first."
        ]

    for cfg in (desktop_config, mobile_config):
        if not cfg.is_file():
            return 2, [f"check_lhci_urls: {cfg.name} not found"]

    try:
        desktop = json.loads(desktop_config.read_text(encoding="utf-8"))
        mobile = json.loads(mobile_config.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return 2, [f"check_lhci_urls: invalid JSON: {e}"]

    desktop_urls: list[str] = desktop.get("ci", {}).get("collect", {}).get("url", [])
    mobile_urls: list[str] = mobile.get("ci", {}).get("collect", {}).get("url", [])

    errors: list[str] = []
    errors.extend(check_existence(public_dir, desktop_urls, "lighthouserc.json"))
    errors.extend(check_existence(public_dir, mobile_urls, "lighthouserc.mobile.json"))
    errors.extend(check_equality(desktop_urls, mobile_urls))
    errors.extend(check_assert_matrix(desktop, desktop_urls, "lighthouserc.json"))
    errors.extend(check_assert_matrix(mobile, mobile_urls, "lighthouserc.mobile.json"))

    return (1 if errors else 0), errors


def main() -> int:
    code, errors = run(PUBLIC_DIR, DESKTOP_CONFIG, MOBILE_CONFIG)

    if code == 0:
        # Compute matrix count for the success line.
        try:
            desktop = json.loads(DESKTOP_CONFIG.read_text(encoding="utf-8"))
            mobile = json.loads(MOBILE_CONFIG.read_text(encoding="utf-8"))
            url_count = len(desktop.get("ci", {}).get("collect", {}).get("url", []))
            matrix_count = (
                len(desktop.get("ci", {}).get("assert", {}).get("assertMatrix", []))
                + len(mobile.get("ci", {}).get("assert", {}).get("assertMatrix", []))
            )
            print(
                f"check_lhci_urls: OK ({url_count} URLs, "
                f"{matrix_count} assertMatrix overrides)"
            )
        except Exception:
            print("check_lhci_urls: OK")
        return 0

    if code == 2:
        for e in errors:
            print(e, file=sys.stderr)
        return 2

    print(f"check_lhci_urls: {len(errors)} issue(s):", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools && python3 -m unittest test_check_lhci_urls -v`
Expected: PASS — 18 tests total.

- [ ] **Step 5: Commit**

```bash
git add tools/check_lhci_urls.py tools/test_check_lhci_urls.py
git commit -m "feat(lhci-4.1): run() orchestrator + main() with exit-code contract"
```

---

## Task 5: Manual smoke against live configs

**Files:** None (verification only).

- [ ] **Step 1: Build the site so `public/` exists**

Run: `hugo --minify` (only if `public/` is stale or missing). Verify `public/essays/example-one/index.html` exists.

- [ ] **Step 2: Run the linter against the real configs**

Run: `python3 tools/check_lhci_urls.py`
Expected: `check_lhci_urls: OK (12 URLs, 1 assertMatrix overrides)` and exit 0.

- [ ] **Step 3: Smoke-test a drift scenario**

Temporarily edit `lighthouserc.mobile.json` to add a fake URL like `"http://localhost/does-not-exist/"` to `collect.url`.
Run: `python3 tools/check_lhci_urls.py`
Expected: exit 1 with two error lines — one for existence (`/does-not-exist/`), one for equality (`1 added, 0 removed`).

Revert the edit.

- [ ] **Step 4: Smoke-test a regex-coverage drift**

Temporarily edit `lighthouserc.mobile.json` `assertMatrix[0].matchingUrlPattern` to `"/essays/retired-slug/$"`.
Run: `python3 tools/check_lhci_urls.py`
Expected: exit 1 with one error line — `assertMatrix[0].matchingUrlPattern '/essays/retired-slug/$' matches no URL in collect.url`.

Revert the edit. No commit (no file changes).

---

## Task 6: Wire into CI workflow

**Files:**
- Modify: `.github/workflows/hugo.yaml` — insert two steps after the "Verify build smoke test" step.

- [ ] **Step 1: Locate the insertion point**

Run: `grep -n "Verify build smoke test\|Verify page weights" .github/workflows/hugo.yaml`
Expected output (line numbers approximate):
```
169:      - name: Verify build smoke test
170:        run: python3 tools/check_smoke.py
171:      - name: Verify page weights against §8 budgets
```

- [ ] **Step 2: Insert the two steps**

After the existing smoke step and before the page-weights step, insert:

```yaml
      - name: Verify LHCI URLs resolve to built pages
        run: python3 tools/check_lhci_urls.py
      - name: Run LHCI URL linter unit tests
        run: cd tools && python3 -m unittest test_check_lhci_urls.py -v
```

The two-space indent matches the rest of the workflow file's step list under `jobs.build.steps`.

- [ ] **Step 3: Sanity-check the yaml parses**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/hugo.yaml'))"`
Expected: no output, exit 0.

If `yaml` module is missing locally, run: `python3 -c "import json; print(json.dumps([line for line in open('.github/workflows/hugo.yaml')]))" > /dev/null` as a weaker syntax check, or use the project's preferred yaml tool.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci(lhci-4.1): wire check_lhci_urls into hugo.yaml after smoke"
```

---

## Task 7: Update CLAUDE.md counts and command list

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the linter-pair count in §"Commands"**

Locate the line beginning `Twenty-five linter pairs under \`tools/check_*.py\``.

Change:
```
Twenty-five linter pairs under `tools/check_*.py` + `tools/test_check_*.py`
```
To:
```
Twenty-six linter pairs under `tools/check_*.py` + `tools/test_check_*.py`
```

In the same paragraph, the comma-separated list of linter topics needs a new entry. Append `, LHCI URL resolution` to the topic list (right before `, org-asset references`):

```
... library shelves, icon attribution, RSS XSL, garden history, streams fixtures, streams links, pagefind metadata, cite metadata, page weights, LHCI URL resolution, org-asset references.
```

- [ ] **Step 2: Update the CI step count in §"Deployment"**

Locate the line: `Total: 63 named steps.`
Change to: `Total: 65 named steps.`

In the same paragraph, after `→ smoke test →` insert ` LHCI URL check →`:

Before:
```
... → install Pagefind 1.5.2 binary → build Pagefind index into `public/pagefind/` → smoke test → page-weight linter + unit tests → Lighthouse CI desktop ...
```

After:
```
... → install Pagefind 1.5.2 binary → build Pagefind index into `public/pagefind/` → smoke test → LHCI URL check → page-weight linter + unit tests → Lighthouse CI desktop ...
```

- [ ] **Step 3: Verify with grep**

Run: `grep -n "Twenty-six\|65 named\|LHCI URL" CLAUDE.md`
Expected: three hits showing the new counts + the inserted phrases.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(lhci-4.1): CLAUDE.md — 26 linter pairs, 65 CI steps"
```

---

## Task 8: Local CI verification + push

**Files:** None (verification only). Per `feedback_always_run_ci_locally`: always run `tools/ci-local.sh` before pushing.

- [ ] **Step 1: Run the full local CI**

Run: `tools/ci-local.sh`
Expected: every step passes including the new `check_lhci_urls` step and its unit-test step. LHCI mobile may show local-variance per `reference_lhci_kitchen_sink_essay_variance` — that's pre-existing and not regressed.

If `check_lhci_urls` fails locally on the real configs, that's a real drift signal — investigate before pushing.

- [ ] **Step 2: Confirm git log shape**

Run: `git log --oneline master..HEAD`
Expected: 5 commits (Tasks 1–4 + CI + docs). Commits all in one branch off master.

- [ ] **Step 3: Push**

Run: `git push origin master`
Expected: GitHub Actions hugo.yaml workflow runs and goes green; deploy step publishes.

Monitor the CI run; the new step should add ~1s to the workflow.

---

## Memory updates (post-merge)

Once CI is green:

- [ ] **Create `.claude/memory/project_lhci_url_validator_complete.md`** — short ship report. Frontmatter `type: project`, link to `[[project_lhci_representative_pages_queued]]` and `[[reference_lhci_kitchen_sink_essay_variance]]`. Note that 4.1 ships and 4.2 + 4.3 remain queued.
- [ ] **Update `.claude/memory/project_lhci_representative_pages_queued.md`** body to reflect 4.1 shipped; cross-link to the new ship-report memory.
- [ ] **Update `.claude/memory/MEMORY.md`** index entry for the queued slice to point at the ship-report (since the queue is partially closed). Replace the "queued" hook with "4.1 shipped; 4.2/4.3 deferred".

These don't need their own commits — memory writes don't go through git.

---

## Self-review

**Spec coverage:**

- §4.1.1 existence — Task 1 ✓
- §4.1.2 equality — Task 2 ✓
- §4.1.3 assertMatrix regex coverage — Task 3 ✓
- §4.2 error message format — Tasks 1–3 (per-check error strings) + Task 4 (`main()` final summary line) ✓
- §4.3 exit codes (0/1/2) — Task 4 ✓
- §4.4 CI placement — Task 6 ✓
- §4.5 ~10 test methods — actually 18 across the four `Test*` classes ✓
- §3 non-goals — no audit of every page, no threshold changes, validator read-only ✓

**Placeholder scan:** no TBD/TODO/"handle edge cases" abstractions. Every code step has complete code.

**Type consistency:** `check_existence`, `check_equality`, `check_assert_matrix`, `file_for_url`, `run`, `main` — names stable across all tasks. `run()` returns `tuple[int, list[str]]` consistently. Error-line shape (`f"{source}: {detail}"`) consistent across check functions.

**Scope check:** single-implementation-plan-sized — 5 commits, ~80 LOC source + ~200 LOC tests + 2 CI step lines + 3 doc edits. Maps cleanly to slice 4.1 only; 4.2 / 4.3 not touched.

**Commit cadence:** 5 commits across 8 tasks (4 TDD cycles + CI + docs). Each commit ships a working, testable unit.
