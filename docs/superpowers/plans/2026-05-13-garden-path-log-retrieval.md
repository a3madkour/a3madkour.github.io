# Garden Path-Log Retrieval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the garden's persisted visited-notes list real consumers — a "Recent paths" widget on `/garden/`, a popover off the path-log strip on note pages, and a `/garden/history/` page — while upgrading the storage schema from v1 (flat slug array) to v2 (sessions with timestamps).

**Architecture:** Three new ES-module JS files import a shared core (`garden-history.js`) that owns storage + migration + rendering. Two thin mount modules (`garden-recent-paths.js`, `garden-pathlog-popover.js`) handle DOM wire-up. `garden-stack.js` swaps its old `persistVisited()` writes for `startSession()`/`extendSession()` against the v2 envelope. One new Hugo layout (`layouts/garden/history.html`) + one new partial (`layouts/partials/garden/recent-paths.html`). New linter pair gates 10 source-side integration points. CI grows 42 → 44 named steps.

**Tech Stack:** Vanilla ES modules (esbuild bundling via Hugo `js.Build`), Hugo templates, hand-rolled CSS (§43 new section), Python 3 stdlib (linter), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-05-13-garden-path-log-retrieval-design.md` (commit `0aa73e4`).

---

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `assets/js/garden-history.js` | **create** | Shared core: `readHistory / writeHistory / dedupe / formatRelativeTime / renderPath / clearHistory / setConsent`. v1→v2 migration on first read. No DOM mounting. |
| `assets/js/garden-recent-paths.js` | **create** | Mounts on `.garden-recent-paths` (widget) AND `.garden-history` (page) — one module covers both surfaces; only count + empty-state shape differ. |
| `assets/js/garden-pathlog-popover.js` | **create** | Mounts the popover on `.path-log-count`. Mobile bypass. Focus trap, Esc-stops-propagation, aria-expanded. |
| `assets/js/garden-stack.js` | **modify** | Drop `persistVisited`. Add `startSession()` at init end + `extendSession(slug)` in `appendColumn`. Import shared core. Add literal `"version": 2` comment as linter sentinel. |
| `assets/js/entry-garden.js` | **modify** | +2 import lines for the new mount scripts. |
| `assets/css/main.css` | **modify** | Add §43 "Reading history" section (~120 lines: widget + shared chip + popover + page styling). |
| `layouts/partials/garden/recent-paths.html` | **create** | Widget shell (hidden by default; JS hydrates). |
| `layouts/partials/garden/path-log.html` | **modify** | Add `<a class="path-log-history" href="/garden/history/">history →</a>` after `⊞ Graph`. |
| `layouts/garden/list.html` | **modify** | Include the new partial right after `<header class="garden-hero">`. |
| `layouts/garden/history.html` | **create** | New layout — server shell + 3 empty-state branches. |
| `content/garden/history/_index.md` | **create** | Frontmatter only; `layout: history` selects the new template. |
| `tools/check_garden_history.py` | **create** | Linter — 10 source-side assertions. |
| `tools/test_check_garden_history.py` | **create** | Sibling unit tests — 10 fixture cases. |
| `.github/workflows/hugo.yaml` | **modify** | +2 named steps (42 → 44). |
| `CLAUDE.md` | **modify** | Log shipped; close the last Phase 8 deferral. |

---

## Task 1: Scaffold linter pair (RED)

**Files:**
- Create: `tools/check_garden_history.py`
- Create: `tools/test_check_garden_history.py`

TDD scaffold per the project's `check_garden_links.py` pattern: parameterized lint function + sibling unit tests against a tempdir fixture tree.

- [ ] **Step 1: Create `tools/check_garden_history.py` with a stub `lint_garden_history()` returning an empty list.**

```python
#!/usr/bin/env python3
"""Garden path-log retrieval linter.

Asserts source-side integration points for the path-log retrieval slice:
  1. layouts/partials/garden/recent-paths.html exists.
  2. layouts/garden/history.html exists.
  3. content/garden/history/_index.md exists with `layout: history` in frontmatter.
  4. layouts/garden/list.html includes the recent-paths partial.
  5. layouts/partials/garden/path-log.html references /garden/history/.
  6-8. assets/js/{garden-history.js, garden-recent-paths.js, garden-pathlog-popover.js} exist.
  9. assets/js/entry-garden.js imports both new mount scripts.
 10. assets/js/garden-stack.js carries the literal `"version": 2` sentinel.

Exits 0 on success, 1 on any error. Stdlib only. Paired with
tools/test_check_garden_history.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def lint_garden_history(project_root: Path) -> list[str]:
    """Return a list of error strings. Empty list = clean."""
    errors: list[str] = []
    return errors


def main() -> int:
    project = Path(__file__).resolve().parent.parent
    errors = lint_garden_history(project)
    if errors:
        print(f"check_garden_history: {len(errors)} issue(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("check_garden_history: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Create `tools/test_check_garden_history.py` with 10 fixture-driven tests.**

```python
"""Tests for check_garden_history.py — run with:
   python3 -m unittest tools/test_check_garden_history.py -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_garden_history as lint  # noqa: E402


# Minimal valid file contents — happy-path fixtures.
RECENT_PATHS_PARTIAL = """\
<section class="garden-recent-paths" hidden aria-labelledby="recent-paths-heading">
  <h2 id="recent-paths-heading">Recent paths</h2>
  <ol class="recent-paths-list"></ol>
</section>
"""

HISTORY_LAYOUT = """\
{{ define "main" }}
<main class="garden-history">
  <h1>{{ .Title }}</h1>
</main>
{{ end }}
"""

HISTORY_CONTENT = """\
---
title: Reading history
layout: history
---
"""

LIST_HTML = """\
{{ define "main" }}
{{ partial "garden/recent-paths.html" . }}
<section class="garden-grid"></section>
{{ end }}
"""

PATHLOG_PARTIAL = """\
<nav class="garden-path-log">
  <a class="path-log-history" href="{{ "/garden/history/" | relURL }}">history</a>
</nav>
"""

GARDEN_HISTORY_JS = '// shared core\nexport function readHistory() { return []; }\n'
GARDEN_RECENT_JS = "import {readHistory} from './garden-history.js';\n"
GARDEN_POPOVER_JS = "import {readHistory} from './garden-history.js';\n"

ENTRY_GARDEN_JS = """\
import './garden.js';
import './garden-stack.js';
import './garden-graph.js';
import './garden-recent-paths.js';
import './garden-pathlog-popover.js';
"""

GARDEN_STACK_JS = """\
// Garden stacked-column runtime.
// Path-log persistence uses v2 schema (envelope {"version": 2, sessions:[...]}).
import { readHistory, writeHistory } from './garden-history.js';
"""


def _layout_fixture(td: Path, **overrides) -> Path:
    """Lay out a complete project mirror under tmpdir.

    overrides: any of the 8 file paths above keyed by short name — set to None
    to omit the file, or set to a string to override the content.
    """
    files = {
        "layouts/partials/garden/recent-paths.html": RECENT_PATHS_PARTIAL,
        "layouts/garden/history.html": HISTORY_LAYOUT,
        "content/garden/history/_index.md": HISTORY_CONTENT,
        "layouts/garden/list.html": LIST_HTML,
        "layouts/partials/garden/path-log.html": PATHLOG_PARTIAL,
        "assets/js/garden-history.js": GARDEN_HISTORY_JS,
        "assets/js/garden-recent-paths.js": GARDEN_RECENT_JS,
        "assets/js/garden-pathlog-popover.js": GARDEN_POPOVER_JS,
        "assets/js/entry-garden.js": ENTRY_GARDEN_JS,
        "assets/js/garden-stack.js": GARDEN_STACK_JS,
    }
    files.update(overrides)
    for rel, content in files.items():
        if content is None:
            continue
        p = td / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return td


class TestGardenHistoryLinter(unittest.TestCase):
    def test_happy_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td))
            self.assertEqual(lint.lint_garden_history(root), [])

    def test_missing_recent_paths_partial(self):
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"layouts/partials/garden/recent-paths.html": None})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("recent-paths.html" in e and "missing" in e.lower() for e in errors),
                            f"expected 'missing recent-paths.html', got: {errors}")

    def test_missing_history_layout(self):
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"layouts/garden/history.html": None})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("garden/history.html" in e and "missing" in e.lower() for e in errors),
                            f"expected 'missing history.html', got: {errors}")

    def test_missing_history_content(self):
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"content/garden/history/_index.md": None})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("history/_index.md" in e and "missing" in e.lower() for e in errors),
                            f"expected 'missing _index.md', got: {errors}")

    def test_history_content_missing_layout_frontmatter(self):
        bad = "---\ntitle: Reading history\n---\n"
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"content/garden/history/_index.md": bad})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("_index.md" in e and "layout: history" in e for e in errors),
                            f"expected 'missing layout: history', got: {errors}")

    def test_list_html_missing_partial_include(self):
        bad = "{{ define \"main\" }}<section></section>{{ end }}\n"
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"layouts/garden/list.html": bad})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("list.html" in e and "recent-paths" in e for e in errors),
                            f"expected 'list.html missing recent-paths include', got: {errors}")

    def test_pathlog_missing_history_link(self):
        bad = "<nav class=\"garden-path-log\"></nav>\n"
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"layouts/partials/garden/path-log.html": bad})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("path-log.html" in e and "/garden/history/" in e for e in errors),
                            f"expected 'path-log missing /garden/history/', got: {errors}")

    def test_missing_js_module(self):
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"assets/js/garden-history.js": None})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("garden-history.js" in e and "missing" in e.lower() for e in errors),
                            f"expected 'missing garden-history.js', got: {errors}")

    def test_entry_garden_missing_imports(self):
        bad = "import './garden.js';\nimport './garden-stack.js';\n"
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"assets/js/entry-garden.js": bad})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("entry-garden.js" in e and "garden-recent-paths" in e for e in errors),
                            f"expected 'entry-garden.js missing import', got: {errors}")

    def test_garden_stack_missing_v2_sentinel(self):
        bad = "// no sentinel here\n"
        with tempfile.TemporaryDirectory() as td:
            root = _layout_fixture(Path(td), **{"assets/js/garden-stack.js": bad})
            errors = lint.lint_garden_history(root)
            self.assertTrue(any("garden-stack.js" in e and "version" in e for e in errors),
                            f"expected 'garden-stack missing v2 sentinel', got: {errors}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests to confirm RED state.**

```bash
python3 -m unittest tools/test_check_garden_history.py -v
```

Expected: `Ran 10 tests` — `test_happy_path` PASSES (stub returns []), 9 negatives FAIL because the stub doesn't yet detect any of the violations.

- [ ] **Step 4: Commit.**

```bash
git add tools/check_garden_history.py tools/test_check_garden_history.py
git commit -m "test(garden-history): scaffold linter pair (RED)"
```

---

## Task 2: Implement linter

**Files:**
- Modify: `tools/check_garden_history.py` (replace the stub `lint_garden_history`)

- [ ] **Step 1: Replace the stub with the full implementation.**

```python
def lint_garden_history(project_root: Path) -> list[str]:
    """Return a list of error strings. Empty list = clean."""
    errors: list[str] = []

    # 1-3: required new files
    must_exist = [
        ("layouts/partials/garden/recent-paths.html", "widget partial"),
        ("layouts/garden/history.html", "history page layout"),
        ("content/garden/history/_index.md", "history page content"),
    ]
    for rel, desc in must_exist:
        if not (project_root / rel).is_file():
            errors.append(f"{rel}: missing ({desc})")

    # Frontmatter check on _index.md
    idx = project_root / "content/garden/history/_index.md"
    if idx.is_file():
        text = idx.read_text(encoding="utf-8")
        if "layout: history" not in text:
            errors.append(f"content/garden/history/_index.md: missing 'layout: history' in frontmatter")

    # 4: list.html includes recent-paths partial
    list_html = project_root / "layouts/garden/list.html"
    if list_html.is_file():
        text = list_html.read_text(encoding="utf-8")
        if "garden/recent-paths" not in text:
            errors.append("layouts/garden/list.html: does not include partials/garden/recent-paths.html")
    else:
        errors.append("layouts/garden/list.html: missing")

    # 5: path-log.html links to /garden/history/
    pathlog = project_root / "layouts/partials/garden/path-log.html"
    if pathlog.is_file():
        text = pathlog.read_text(encoding="utf-8")
        if "/garden/history/" not in text:
            errors.append("layouts/partials/garden/path-log.html: missing chrome link to /garden/history/")
    else:
        errors.append("layouts/partials/garden/path-log.html: missing")

    # 6-8: new JS modules
    for rel in (
        "assets/js/garden-history.js",
        "assets/js/garden-recent-paths.js",
        "assets/js/garden-pathlog-popover.js",
    ):
        if not (project_root / rel).is_file():
            errors.append(f"{rel}: missing")

    # 9: entry-garden.js imports both mount scripts
    entry = project_root / "assets/js/entry-garden.js"
    if entry.is_file():
        text = entry.read_text(encoding="utf-8")
        if not re.search(r"""import\s+['"]\./garden-recent-paths['"]""", text):
            errors.append("assets/js/entry-garden.js: missing import of './garden-recent-paths'")
        if not re.search(r"""import\s+['"]\./garden-pathlog-popover['"]""", text):
            errors.append("assets/js/entry-garden.js: missing import of './garden-pathlog-popover'")
    else:
        errors.append("assets/js/entry-garden.js: missing")

    # 10: garden-stack.js carries the v2 schema sentinel
    stack = project_root / "assets/js/garden-stack.js"
    if stack.is_file():
        text = stack.read_text(encoding="utf-8")
        if '"version": 2' not in text:
            errors.append('assets/js/garden-stack.js: missing v2 schema sentinel (expected literal \'"version": 2\')')
    else:
        errors.append("assets/js/garden-stack.js: missing")

    return errors
```

- [ ] **Step 2: Run fixture tests — all 10 should pass.**

```bash
python3 -m unittest tools/test_check_garden_history.py -v
```

Expected: `Ran 10 tests in ... OK`.

- [ ] **Step 3: Run the linter against the real project — should FAIL with multiple errors.**

```bash
python3 tools/check_garden_history.py
```

Expected: stderr lists ~8 errors (missing recent-paths.html partial, missing history layout, missing _index.md, list.html doesn't include partial, path-log missing history link, 3 missing JS modules, entry-garden missing imports, garden-stack missing sentinel). Exit 1. This RED state against the project is intentional — Tasks 3–8 clear it.

- [ ] **Step 4: Commit.**

```bash
git add tools/check_garden_history.py
git commit -m "feat(garden-history): implement linter (GREEN fixtures, RED project)"
```

---

## Task 3: Author `garden-history.js` (shared core)

**Files:**
- Create: `assets/js/garden-history.js`

- [ ] **Step 1: Write the module.**

```javascript
// Garden reading-history storage + render core.
// Reads/writes localStorage['garden-path-log'] (or sessionStorage if consent
// is 'session') in v2 envelope: {version: 2, sessions: [{root, slugs, at}]}.
// Migrates v1 (flat slug array) on first read.

const STORAGE_KEY = 'garden-path-log';
const CONSENT_KEY = 'path-log-consent';
const VERSION = 2;
const SESSION_CAP = 20;

function getStore() {
  let consent;
  try { consent = localStorage.getItem(CONSENT_KEY) || 'unset'; }
  catch { consent = 'unset'; }
  if (consent === 'session') return sessionStorage;
  return localStorage;
}

export function readHistory() {
  const store = getStore();
  let raw;
  try { raw = store.getItem(STORAGE_KEY); }
  catch { return []; }
  if (!raw) return [];

  let parsed;
  try { parsed = JSON.parse(raw); }
  catch { return []; }

  // v1 migration: flat array → wrap as one synthetic session.
  if (Array.isArray(parsed)) {
    const sessions = parsed.length === 0 ? [] : [{
      root: parsed[0] || '',
      slugs: parsed.slice(),
      at: 0,
    }];
    writeHistory(sessions);
    return sessions;
  }

  if (parsed && parsed.version === VERSION && Array.isArray(parsed.sessions)) {
    return parsed.sessions;
  }
  return [];
}

export function writeHistory(sessions) {
  const store = getStore();
  const capped = sessions.slice(0, SESSION_CAP);
  const envelope = { version: VERSION, sessions: capped };
  try { store.setItem(STORAGE_KEY, JSON.stringify(envelope)); }
  catch {}
}

export function dedupe(sessions) {
  // Sort newest-first, then keep only the first occurrence per slug-sequence.
  const sorted = sessions.slice().sort((a, b) => b.at - a.at);
  const seen = new Set();
  const out = [];
  for (const s of sorted) {
    const key = s.slugs.join('|');
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(s);
  }
  return out;
}

export function formatRelativeTime(ts) {
  if (!ts) return '';
  const diff = Date.now() - ts;
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  const days = Math.floor(diff / 86_400_000);
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days} days ago`;
  if (days < 14) return 'last week';
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
  return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function slugToLabel(slug) {
  return slug.replace(/-/g, ' ');
}

export function renderPath(session, options = {}) {
  const includeTime = options.includeTime !== false;
  const frag = document.createDocumentFragment();

  if (includeTime) {
    const time = document.createElement('span');
    time.className = 'path-time';
    time.textContent = formatRelativeTime(session.at);
    frag.appendChild(time);
  }

  session.slugs.forEach((slug, i) => {
    if (i > 0) {
      const arrow = document.createElement('span');
      arrow.className = 'path-arrow';
      arrow.setAttribute('aria-hidden', 'true');
      arrow.textContent = '›';
      frag.appendChild(arrow);
    }
    const a = document.createElement('a');
    a.className = 'path-chip';
    if (i === 0 && session.slugs.length > 1) {
      // Leftmost chip loads the full path via ?stack=.
      const rest = session.slugs.slice(1).join(',');
      a.href = `/garden/${slug}/?stack=${encodeURIComponent(rest)}`;
    } else {
      a.href = `/garden/${slug}/`;
    }
    a.textContent = slugToLabel(slug);
    frag.appendChild(a);
  });

  return frag;
}

export function clearHistory() {
  try { localStorage.removeItem(STORAGE_KEY); } catch {}
  try { sessionStorage.removeItem(STORAGE_KEY); } catch {}
}

export function setConsent(value) {
  try { localStorage.setItem(CONSENT_KEY, value); } catch {}
}
```

- [ ] **Step 2: Verify the module parses by running `hugo --minify` (Hugo's js.Build uses esbuild).** No need to start a dev server.

```bash
pkill -f 'hugo server' 2>/dev/null || true
hugo --minify 2>&1 | tail -5
```

Expected: clean build (esbuild rejects malformed ES modules; if there's a syntax error you'll see it here). Garden bundle output file present.

- [ ] **Step 3: Run the linter — should drop the missing-`garden-history.js` error but still fail.**

```bash
python3 tools/check_garden_history.py
```

Expected: still exits 1; one fewer missing-file error.

- [ ] **Step 4: Commit.**

```bash
git add assets/js/garden-history.js
git commit -m "feat(garden-history): add shared storage + render core module"
```

---

## Task 4: Migrate `garden-stack.js` to v2 sessions schema

**Files:**
- Modify: `assets/js/garden-stack.js`

Drop the old `persistVisited(slug)` function; replace with `startSession()` (called at end of `init()`) and `extendSession(slug)` (called in `appendColumn`). Add a comment carrying the literal `"version": 2` substring as the linter sentinel.

- [ ] **Step 1: At the top of `assets/js/garden-stack.js`, add the import and the schema-version comment.** Replace lines 1–3:

```javascript
// Garden stacked-column runtime — eager Matuschak-style.
// Spec: docs/superpowers/specs/2026-05-08-garden-interactions-design.md §5.
// Path-log persistence uses v2 schema (envelope {"version": 2, sessions:[...]}).
// Migration + read/write live in garden-history.js.

import { readHistory, writeHistory } from './garden-history.js';
```

- [ ] **Step 2: Remove the old constants and `persistVisited` function (current lines 11–14 + 71–90).** Find:

```javascript
const CONSENT_KEY = 'path-log-consent';
const VISITED_KEY = 'garden-path-log';
const VISITED_CAP = 100;
```

…and replace with just:

```javascript
const CONSENT_KEY = 'path-log-consent';
```

Then find the entire `function persistVisited(slug) { … }` block (current lines 71–90) and **delete it**.

- [ ] **Step 3: Add `startSession()` and `extendSession()` helpers near the top of the file (right after `state` declaration, before `pending`).**

```javascript
// Session lifecycle for the v2 path-log schema. A session is one continuous
// reading flow on a single page load. startSession() creates a new record;
// extendSession() appends to it. clearStack() does NOT end the session.
let currentSessionAt = 0;

function startSession() {
  if (state.consent === 'unset' || state.consent === 'no') return;
  if (state.slugs.length === 0) return;
  currentSessionAt = Date.now();
  const sessions = readHistory();
  sessions.unshift({
    root: state.slugs[0],
    slugs: state.slugs.slice(),
    at: currentSessionAt,
  });
  writeHistory(sessions);
}

function extendSession(slug) {
  if (state.consent === 'unset' || state.consent === 'no') return;
  if (!currentSessionAt) return;
  const sessions = readHistory();
  const current = sessions.find(s => s.at === currentSessionAt);
  if (!current) return;
  current.slugs.push(slug);
  writeHistory(sessions);
}
```

- [ ] **Step 4: Replace the call inside `appendColumn` (current line ~244): `persistVisited(slug);` → `extendSession(slug);`.**

Find:
```javascript
    dispatchStackChanged();
    persistVisited(slug);
    if (wasOne) showConsentBanner();
```

Replace with:
```javascript
    dispatchStackChanged();
    extendSession(slug);
    if (wasOne) showConsentBanner();
```

- [ ] **Step 5: Replace the retroactive persistence in the consent banner (current line ~122–124).** Find:

```javascript
    if (choice !== 'no') {
      // Persist current stack retroactively.
      state.slugs.forEach(persistVisited);
    }
```

Replace with:

```javascript
    if (choice !== 'no') {
      // Persist the current stack as a session retroactively.
      startSession();
    }
```

- [ ] **Step 6: Call `startSession()` at the end of `init()` once `state.slugs` is finalized and `dispatchStackChanged()` has fired.** Find the existing block (around line ~314):

```javascript
  rewriteURL();
  updatePathLog();
  if (state.slugs.length > 1) {
    focusColumn(state.slugs[state.slugs.length - 1]);
  }
  dispatchStackChanged();
```

Replace with:

```javascript
  rewriteURL();
  updatePathLog();
  if (state.slugs.length > 1) {
    focusColumn(state.slugs[state.slugs.length - 1]);
  }
  dispatchStackChanged();
  startSession();
```

- [ ] **Step 7: Verify the JS parses via Hugo build.**

```bash
pkill -f 'hugo server' 2>/dev/null || true
hugo --minify 2>&1 | tail -5
```

Expected: clean build. If esbuild rejects an import or a syntax error, fix it before moving on.

- [ ] **Step 8: Run the linter — the v2 sentinel check should now pass.**

```bash
python3 tools/check_garden_history.py
```

Expected: still exits 1 (lots remaining), but the `garden-stack.js missing v2 sentinel` line is gone.

- [ ] **Step 9: Commit.**

```bash
git add assets/js/garden-stack.js
git commit -m "feat(garden-history): migrate garden-stack to v2 sessions schema"
```

---

## Task 5: Widget partial + mount module + widget/shared CSS

**Files:**
- Create: `layouts/partials/garden/recent-paths.html`
- Create: `assets/js/garden-recent-paths.js`
- Modify: `assets/css/main.css` (add §43 — widget + shared chip styling)

- [ ] **Step 1: Create the widget partial.**

```html
{{- /* Recent reading paths widget.
       Rendered hidden by default; assets/js/garden-recent-paths.js reveals it
       after reading localStorage['garden-path-log']. The <ol> is populated
       client-side. No JS-off fallback (data lives in localStorage anyway).
*/ -}}
<section class="garden-recent-paths" hidden aria-labelledby="recent-paths-heading">
  <h2 id="recent-paths-heading">Recent paths</h2>
  <ol class="recent-paths-list"></ol>
  <div class="recent-paths-actions">
    <a class="recent-paths-view-all" href="{{ "/garden/history/" | relURL }}">Reading history →</a>
    <button class="recent-paths-clear" type="button">Clear history</button>
  </div>
</section>
```

- [ ] **Step 2: Create the mount module.** This module covers BOTH the widget on `/garden/` AND the `/garden/history/` page hydration (Task 6 doesn't add a separate JS file — it reuses this one).

```javascript
// Mounts the "Recent paths" widget on /garden/ AND the /garden/history/ page.
// One module covers both because rendering is identical; only count + empty
// state differ.

import {
  readHistory,
  dedupe,
  renderPath,
  clearHistory,
  setConsent,
} from './garden-history.js';

const CONSENT_KEY = 'path-log-consent';

function readConsent() {
  try { return localStorage.getItem(CONSENT_KEY) || 'unset'; }
  catch { return 'unset'; }
}

function mountWidget(root) {
  const sessions = dedupe(readHistory()).slice(0, 5);
  if (sessions.length === 0) return;

  const list = root.querySelector('.recent-paths-list');
  sessions.forEach(s => {
    const li = document.createElement('li');
    li.className = 'path-row';
    li.appendChild(renderPath(s));
    list.appendChild(li);
  });

  root.hidden = false;

  const clearBtn = root.querySelector('.recent-paths-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (!confirm('Clear all stored reading history?')) return;
      clearHistory();
      list.replaceChildren();
      root.hidden = true;
    });
  }
}

function mountHistoryPage(root) {
  const consent = readConsent();
  const allSessions = readHistory();
  const dedupSessions = dedupe(allSessions);

  const status = root.querySelector('.garden-history-status');
  const actions = root.querySelector('.garden-history-actions');
  const list = root.querySelector('.garden-history-list');
  const empty = root.querySelector('.garden-history-empty');

  if (dedupSessions.length === 0) {
    empty.hidden = false;
    let branch;
    if (consent === 'no') branch = 'no';
    else if (consent === 'unset') branch = 'unset';
    else branch = 'ok';
    empty.querySelectorAll('[data-state]').forEach(div => {
      div.hidden = div.dataset.state !== branch;
    });
    const reenable = empty.querySelector('.reenable-tracking');
    if (reenable) {
      reenable.addEventListener('click', () => {
        setConsent('unset');
        window.location.reload();
      });
    }
    return;
  }

  const sCount = allSessions.length;
  const dCount = dedupSessions.length;
  status.textContent = `${sCount} session${sCount === 1 ? '' : 's'} stored · ${dCount} unique path${dCount === 1 ? '' : 's'} after dedup`;
  status.hidden = false;
  actions.hidden = false;
  list.hidden = false;

  dedupSessions.forEach(s => {
    const li = document.createElement('li');
    li.className = 'path-row';
    li.appendChild(renderPath(s));
    list.appendChild(li);
  });

  const clearBtn = root.querySelector('.garden-history-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (!confirm('Clear all stored reading history?')) return;
      clearHistory();
      window.location.reload();
    });
  }
}

function init() {
  const widget = document.querySelector('.garden-recent-paths');
  if (widget) mountWidget(widget);

  const historyPage = document.querySelector('.garden-history');
  if (historyPage) mountHistoryPage(historyPage);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

- [ ] **Step 3: Add CSS §43 — widget + shared path-chip parts.** Append to `assets/css/main.css`:

```css

/* ===========================================================================
 * §43 Reading history — garden path-log retrieval surfaces
 *
 * Widget on /garden/, popover on note pages, and /garden/history/ page.
 * All driven by assets/js/garden-history.js + the two mount modules.
 * ===========================================================================
 */

/* Widget on /garden/ index */
.garden-recent-paths {
  margin: 2rem 0;
  padding: 1rem 1.25rem;
  background: color-mix(in srgb, var(--color-warn) 8%, var(--color-tile));
  border: 1px solid var(--color-rule);
  border-radius: 4px;
  font-family: var(--font-body);
}
.garden-recent-paths[hidden] { display: none; }
.garden-recent-paths h2 {
  margin: 0 0 0.75rem;
  font-size: var(--text-md);
  font-weight: 600;
}
.recent-paths-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.recent-paths-actions {
  margin-top: 0.8rem;
  padding-top: 0.6rem;
  border-top: 1px dashed var(--color-rule);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-xs);
}
.recent-paths-view-all {
  color: var(--color-burgundy);
  text-decoration: none;
  border-bottom: 1px dotted var(--color-burgundy);
}
.recent-paths-clear {
  font-family: inherit;
  font-size: var(--text-xs);
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--color-rule);
  border-radius: 3px;
  background: transparent;
  color: var(--color-ink-soft);
  cursor: pointer;
}
.recent-paths-clear:hover { color: var(--color-warn); }

/* Shared row + chip + time + arrow primitives (also used by popover + history page) */
.path-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  padding: 0.35rem 0;
}
.path-time {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--color-ink-soft);
  min-width: 5rem;
  flex-shrink: 0;
}
.path-chip {
  background: var(--color-tile);
  border: 1px solid var(--color-rule);
  border-radius: 3px;
  padding: 0.15rem 0.5rem;
  font-size: var(--text-xs);
  color: var(--color-burgundy);
  text-decoration: none;
  border-bottom: 1px dotted var(--color-burgundy);
}
.path-chip:hover {
  background: color-mix(in srgb, var(--color-burgundy) 10%, var(--color-tile));
}
.path-arrow {
  color: var(--color-ink-fade);
  font-size: var(--text-xs);
}
```

Also update the top-of-file section index comment (search for `§42` or similar to find the existing index block) to mention `§43 Reading history`. If the index pattern is not present at top of file, skip this step.

- [ ] **Step 4: Commit.**

```bash
git add layouts/partials/garden/recent-paths.html assets/js/garden-recent-paths.js assets/css/main.css
git commit -m "feat(garden-history): widget + shared mount module + CSS §43"
```

---

## Task 6: `/garden/history/` content + layout + page CSS

**Files:**
- Create: `content/garden/history/_index.md`
- Create: `layouts/garden/history.html`
- Modify: `assets/css/main.css` (extend §43 with page styling)

- [ ] **Step 1: Create the content file.**

```yaml
---
title: Reading history
layout: history
draft: false
---
```

- [ ] **Step 2: Create the layout.**

```html
{{ define "main" }}
<main class="garden-history">
  <header>
    <h1>{{ .Title }}</h1>
    <p class="lede">Your recent paths through the garden. Up to 20 most-recent sessions; older paths drop off automatically. Lives only in your browser.</p>
  </header>
  <div class="garden-history-status" hidden></div>
  <div class="garden-history-actions" hidden>
    <button class="garden-history-clear" type="button">Clear history</button>
  </div>
  <ol class="garden-history-list" hidden></ol>
  <div class="garden-history-empty" hidden>
    <div data-state="unset">
      <p>Reading history is empty.</p>
      <p><em>Open a note and click an internal link to start a stack. You'll see a prompt to opt in.</em></p>
    </div>
    <div data-state="no" hidden>
      <p>Reading history is empty — tracking is off.</p>
      <p><em>You opted out of path tracking. You can re-enable it.</em></p>
      <button class="reenable-tracking" type="button">Re-enable tracking</button>
    </div>
    <div data-state="ok" hidden>
      <p>No paths recorded yet.</p>
      <p><em>As you walk through the garden, your paths will appear here.</em></p>
    </div>
  </div>
</main>
{{ end }}
```

- [ ] **Step 3: Extend CSS §43 with page styling.** Append to `assets/css/main.css` after the existing §43 block:

```css

/* /garden/history/ page */
.garden-history {
  max-width: 60rem;
  margin: 0 auto;
  padding: 3rem 1.5rem;
  font-family: var(--font-body);
}
.garden-history h1 {
  font-size: var(--text-3xl, 1.75rem);
  margin: 0 0 0.4rem;
}
.garden-history .lede {
  color: var(--color-ink-soft);
  font-size: var(--text-sm);
  margin: 0 0 1.5rem;
}
.garden-history-status {
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  font-style: italic;
  margin: 0 0 1rem;
}
.garden-history-status[hidden],
.garden-history-actions[hidden],
.garden-history-list[hidden],
.garden-history-empty[hidden] { display: none; }
.garden-history-actions {
  margin: 0 0 1rem;
}
.garden-history-clear {
  font-family: inherit;
  font-size: var(--text-xs);
  padding: 0.25rem 0.7rem;
  border: 1px solid var(--color-rule);
  border-radius: 3px;
  background: transparent;
  color: var(--color-ink-soft);
  cursor: pointer;
}
.garden-history-clear:hover { color: var(--color-warn); }
.garden-history-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.garden-history-list li {
  padding: 0.7rem 0;
  border-bottom: 1px solid var(--color-rule);
}
.garden-history-list li:last-child { border-bottom: 0; }
.garden-history-empty {
  background: var(--color-tile);
  border: 1px dashed var(--color-rule);
  border-radius: 4px;
  padding: 1.2rem 1.4rem;
  text-align: center;
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
}
.garden-history-empty .reenable-tracking {
  display: inline-block;
  margin-top: 0.6rem;
  font-family: inherit;
  font-size: var(--text-xs);
  padding: 0.3rem 0.8rem;
  border: 1px solid var(--color-burgundy);
  border-radius: 3px;
  background: var(--color-paper);
  color: var(--color-burgundy);
  cursor: pointer;
}
```

- [ ] **Step 4: Run Hugo build to confirm the new content + layout resolves.**

```bash
pkill -f 'hugo server' 2>/dev/null || true
hugo --minify 2>&1 | tail -10
ls -la public/garden/history/ 2>/dev/null
```

Expected: build succeeds; `public/garden/history/index.html` exists.

- [ ] **Step 5: Commit.**

```bash
git add content/garden/history/_index.md layouts/garden/history.html assets/css/main.css
git commit -m "feat(garden-history): /garden/history/ page + CSS"
```

---

## Task 7: Popover module + path-log.html modification + popover CSS

**Files:**
- Create: `assets/js/garden-pathlog-popover.js`
- Modify: `layouts/partials/garden/path-log.html`
- Modify: `assets/css/main.css` (extend §43 with popover styling)

- [ ] **Step 1: Create the popover mount module.**

```javascript
// Popover off the path-log "N in stack" count on garden note pages.
// Desktop only — mobile bypasses entirely.

import { readHistory, dedupe, renderPath } from './garden-history.js';

const MOBILE_QUERY = '(max-width: 720px)';

function init() {
  if (window.matchMedia(MOBILE_QUERY).matches) return;

  const trigger = document.querySelector('.path-log-count');
  if (!trigger) return;
  if (trigger.tagName !== 'SPAN') return; // belt + braces — already promoted?

  // Identify current page's root slug from the active path-log crumb.
  const activeCrumb = document.querySelector('.path-log-crumb.is-active[data-slug]');
  const rootSlug = activeCrumb ? activeCrumb.dataset.slug : null;

  const all = dedupe(readHistory());
  // Drop the current session (the newest one whose root matches rootSlug).
  const currentIdx = rootSlug ? all.findIndex(s => s.root === rootSlug) : -1;
  const others = all.filter((_, i) => i !== currentIdx).slice(0, 4);

  if (others.length === 0) return;

  // Promote span → button.
  const button = document.createElement('button');
  button.type = 'button';
  button.className = trigger.className;
  if (trigger.dataset.stackCount) button.dataset.stackCount = trigger.dataset.stackCount;
  button.textContent = `${trigger.textContent.trim()} ▾`;
  button.setAttribute('aria-expanded', 'false');
  button.setAttribute('aria-controls', 'path-log-popover');
  trigger.parentNode.replaceChild(button, trigger);

  // Build popover DOM.
  const popover = document.createElement('div');
  popover.id = 'path-log-popover';
  popover.setAttribute('role', 'dialog');
  popover.setAttribute('aria-labelledby', 'path-log-popover-heading');
  popover.hidden = true;
  popover.innerHTML = `
    <h3 id="path-log-popover-heading">Recent paths</h3>
    <ol class="popover-paths"></ol>
    <a class="popover-history-link" href="/garden/history/">full history →</a>
  `;
  button.insertAdjacentElement('afterend', popover);

  const list = popover.querySelector('.popover-paths');
  others.forEach(s => {
    const li = document.createElement('li');
    li.className = 'path-row';
    li.appendChild(renderPath(s));
    list.appendChild(li);
  });

  const focusableSelector = 'a, button';

  function open() {
    popover.hidden = false;
    button.setAttribute('aria-expanded', 'true');
    const first = popover.querySelector(focusableSelector);
    if (first) first.focus();
  }
  function close() {
    popover.hidden = true;
    button.setAttribute('aria-expanded', 'false');
    button.focus();
  }
  function isOpen() { return !popover.hidden; }

  button.addEventListener('click', () => {
    if (isOpen()) close();
    else open();
  });

  document.addEventListener('mousedown', (e) => {
    if (!isOpen()) return;
    if (popover.contains(e.target) || button.contains(e.target)) return;
    close();
  }, true);

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!isOpen()) return;
    e.stopImmediatePropagation();
    close();
  });

  // Focus trap inside the popover.
  popover.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    const focusables = Array.from(popover.querySelectorAll(focusableSelector));
    if (focusables.length === 0) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

- [ ] **Step 2: Modify `layouts/partials/garden/path-log.html` — add the chrome history link.** Find the existing `<span class="path-log-actions">` block and insert the new link after the `⊞ Graph` button:

Current (lines 11–15):
```html
  <span class="path-log-actions">
    <span class="path-log-count" data-stack-count="1">1 in stack</span>
    <button type="button" class="path-log-clear" hidden>clear</button>
    <button type="button" class="graph-toggle" aria-expanded="false" aria-controls="garden-graph-panel">⊞ Graph</button>
  </span>
```

Replace with:
```html
  <span class="path-log-actions">
    <span class="path-log-count" data-stack-count="1">1 in stack</span>
    <button type="button" class="path-log-clear" hidden>clear</button>
    <button type="button" class="graph-toggle" aria-expanded="false" aria-controls="garden-graph-panel">⊞ Graph</button>
    <a class="path-log-history" href="{{ "/garden/history/" | relURL }}">history →</a>
  </span>
```

- [ ] **Step 3: Extend CSS §43 with popover + history-link styling.** Append to `assets/css/main.css` after the existing §43 page block:

```css

/* Path-log popover (note pages, desktop only) */
.garden-path-log .path-log-count {
  /* Span variant — non-interactive when there's no history yet. */
}
.garden-path-log button.path-log-count {
  cursor: pointer;
  font: inherit;
  background: transparent;
  border: 0;
  padding: 0;
  color: var(--color-ink-soft);
}
.garden-path-log button.path-log-count[aria-expanded="true"] {
  color: var(--color-burgundy);
}
.garden-path-log .path-log-actions {
  position: relative; /* popover anchors here */
}
#path-log-popover {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.3rem;
  background: var(--color-paper);
  border: 1px solid var(--color-burgundy);
  border-radius: 4px;
  padding: 0.7rem 0.85rem;
  font-family: var(--font-body);
  font-size: var(--text-xs);
  min-width: 18rem;
  max-width: 28rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  z-index: 10;
}
#path-log-popover[hidden] { display: none; }
#path-log-popover h3 {
  margin: 0 0 0.5rem;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-burgundy);
}
#path-log-popover .popover-paths {
  list-style: none;
  margin: 0;
  padding: 0;
}
#path-log-popover .popover-paths li {
  border-bottom: 1px dashed var(--color-rule);
}
#path-log-popover .popover-paths li:last-child {
  border-bottom: 0;
}
#path-log-popover .popover-history-link {
  display: inline-block;
  margin-top: 0.5rem;
  padding-top: 0.4rem;
  border-top: 1px solid var(--color-rule);
  width: 100%;
  color: var(--color-burgundy);
  text-decoration: none;
  border-bottom: 1px dotted var(--color-burgundy);
}

/* Path-log chrome "history →" link */
.garden-path-log .path-log-history {
  color: var(--color-burgundy);
  text-decoration: none;
  border-bottom: 1px dotted var(--color-burgundy);
  font-size: var(--text-xs);
}
```

- [ ] **Step 4: Run the linter — `path-log.html` and `garden-pathlog-popover.js` checks should now pass; the `entry-garden.js missing imports` is the only remaining failure.**

```bash
python3 tools/check_garden_history.py
```

Expected: exits 1 with just the `entry-garden.js missing import of './garden-recent-paths'` and `entry-garden.js missing import of './garden-pathlog-popover'` errors.

- [ ] **Step 5: Commit.**

```bash
git add assets/js/garden-pathlog-popover.js layouts/partials/garden/path-log.html assets/css/main.css
git commit -m "feat(garden-history): popover module + path-log.html link + CSS"
```

---

## Task 8: Wire `entry-garden.js` imports + `list.html` include

**Files:**
- Modify: `assets/js/entry-garden.js`
- Modify: `layouts/garden/list.html`

- [ ] **Step 1: Add the two imports to `entry-garden.js`.** Replace the file contents with:

```javascript
// Garden-section entry — loaded only on /garden/ list, /garden/<slug>/, and
// /garden/graph/. Pulls the filter-chips runtime, the stacked-column app, and
// the force-directed graph (with the ~95 KB of vendored d3 modules that
// garden-graph.js dynamically imports). Each child module owns its own
// selector guards so they no-op on pages where their selectors don't match.
import './garden.js';
import './garden-stack.js';
import './garden-graph.js';
import './garden-recent-paths.js';
import './garden-pathlog-popover.js';
```

- [ ] **Step 2: Insert the partial include in `layouts/garden/list.html`.** Find the existing `<header class="garden-hero">…</header>` block (lines 5–8). Add the partial include immediately after the `</header>` line (line 8) and before the `{{- /* Exclude the standalone /garden/graph/ page … */ -}}` comment:

Current (lines 5–10):
```html
  <header class="garden-hero">
    <h1>{{ .Title }}</h1>
    {{ with .Content }}<div class="framing">{{ . }}</div>{{ end }}
  </header>

  {{- /* Exclude the standalone /garden/graph/ page (layout=graph) — it lives in
```

Replace with:
```html
  <header class="garden-hero">
    <h1>{{ .Title }}</h1>
    {{ with .Content }}<div class="framing">{{ . }}</div>{{ end }}
  </header>

  {{ partial "garden/recent-paths.html" . }}

  {{- /* Exclude the standalone /garden/graph/ page (layout=graph) — it lives in
```

- [ ] **Step 3: Run the linter — should now GREEN.**

```bash
python3 tools/check_garden_history.py
```

Expected: `check_garden_history: OK`. Exit 0.

- [ ] **Step 4: Run the linter sibling tests again to confirm the linter logic still parses the fixture cases correctly.**

```bash
python3 -m unittest tools/test_check_garden_history.py -v
```

Expected: `Ran 10 tests in ... OK`.

- [ ] **Step 5: Commit.**

```bash
git add assets/js/entry-garden.js layouts/garden/list.html
git commit -m "feat(garden-history): wire entry imports + list.html partial"
```

---

## Task 9: Hugo build + scripted verification

**Files:** (none — verification only)

- [ ] **Step 1: Kill any dev server and run the production build.**

```bash
pkill -f 'hugo server' 2>/dev/null || true
rm -rf public
hugo --minify 2>&1 | tail -10
```

Expected: clean build, `public/garden/history/index.html` exists.

- [ ] **Step 2: Verify the new history page rendered.**

```bash
ls -la public/garden/history/
test -f public/garden/history/index.html && echo "history page rendered" || echo "MISSING"
```

Expected: file present.

- [ ] **Step 3: Confirm the garden bundle grew (~5–7 KB).**

```bash
ls -la public/js/garden.*.js
```

Expected: file size has grown from prior baseline (~117 KB → ~120–124 KB).

- [ ] **Step 4: Spot-check the widget markup is present on `/garden/`.**

```bash
grep -c "garden-recent-paths" public/garden/index.html
```

Expected: `1` (the `<section>` shell is in the rendered HTML).

- [ ] **Step 5: Spot-check the chrome history link is present on a note page.**

```bash
NOTE=$(ls public/garden/ | grep -v '^index\|^history\|^graph' | head -1)
grep -c "path-log-history" "public/garden/$NOTE/index.html"
```

Expected: `1`.

- [ ] **Step 6: Confirm the history page chrome link isn't promoted to button anywhere server-side (the popover does that client-side only).**

```bash
grep -c '<button class="path-log-count"' public/garden/index.html
```

Expected: `0` (still a `<span>` server-side).

- [ ] **Step 7: Run all linter pairs to catch any unintended regression.**

```bash
python3 tools/check-contrast.py && \
python3 tools/check_fixtures.py && python3 -m unittest tools/test_check_fixtures.py 2>&1 | tail -2 && \
python3 tools/check_garden_fixtures.py && python3 -m unittest tools/test_check_garden_fixtures.py 2>&1 | tail -2 && \
python3 tools/check_garden_links.py && python3 -m unittest tools/test_check_garden_links.py 2>&1 | tail -2 && \
python3 tools/check_filter_chips_config.py && python3 -m unittest tools/test_check_filter_chips_config.py 2>&1 | tail -2 && \
python3 tools/check_research_fixtures.py && python3 -m unittest tools/test_check_research_fixtures.py 2>&1 | tail -2 && \
python3 tools/check_research_links.py && python3 -m unittest tools/test_check_research_links.py 2>&1 | tail -2 && \
python3 tools/check_citations.py && python3 -m unittest tools/test_check_citations.py 2>&1 | tail -2 && \
python3 tools/check_works_fixtures.py && python3 -m unittest tools/test_check_works_fixtures.py 2>&1 | tail -2 && \
python3 tools/check_works_links.py && python3 -m unittest tools/test_check_works_links.py 2>&1 | tail -2 && \
python3 tools/check_library_fixtures.py && python3 -m unittest tools/test_check_library_fixtures.py 2>&1 | tail -2 && \
python3 tools/check_library_links.py && python3 -m unittest tools/test_check_library_links.py 2>&1 | tail -2 && \
python3 tools/check_library_covers.py && python3 -m unittest tools/test_check_library_covers.py 2>&1 | tail -2 && \
python3 tools/check_rss_xsl.py && python3 -m unittest tools/test_check_rss_xsl.py 2>&1 | tail -2 && \
python3 tools/check_garden_history.py && python3 -m unittest tools/test_check_garden_history.py 2>&1 | tail -2 && \
python3 tools/check_smoke.py && \
echo "ALL LINTERS OK"
```

Expected: ends with `ALL LINTERS OK`. If anything failed, investigate before moving on.

No commit — verification only.

---

## Task 10: Browser verification (manual — user)

**Files:** (none — manual verification)

The plan executor should hand off to the user for this task. Start the dev server, then ask the user to walk through these scenarios.

- [ ] **Step 1: Start the dev server detached.**

```bash
nohup hugo server --buildDrafts > /tmp/hugo-server.log 2>&1 & disown
sleep 2
echo "Dev server: http://localhost:1313/"
```

- [ ] **Step 2: Hand off to the user with this spot-check list.** Use `AskUserQuestion` if appropriate, or just message them with the bullet list.

Spot-check scenarios:

1. **Empty state, `consent === 'unset'`** — clear localStorage; open `/garden/` → widget hidden; open `/garden/history/` → empty-state "Open a note and click an internal link…" branch visible.
2. **Open a note, navigate stack, see consent banner** — open `/garden/<some-note>/`; click an internal link inside; consent banner appears. Pick "Yes, persist."
3. **Stack builds session** — navigate through 3–4 notes; localStorage now contains `{version:2, sessions:[{root, slugs, at}]}`.
4. **Reload note page, popover available** — reload; "N in stack" is now a `<button>` with `▾` arrow; click it → popover opens with last paths (excluding current). Click outside → closes. Esc → closes + focus returns to trigger. Tab cycles inside.
5. **Widget on /garden/** — go to `/garden/`; the "Recent paths" widget appears at the top, listing up to 5 dedup'd paths with relative-time stamps. Click a path's leftmost chip → navigates with `?stack=…` and the destination rebuilds the stack.
6. **Clear from widget** — click "Clear history" in the widget; confirm; widget hides. Reload `/garden/` → still hidden. Open `/garden/history/` → empty-state shown.
7. **`/garden/history/` page populated** — re-visit some notes to repopulate; navigate to `/garden/history/`; full list of all 20 max sessions with status line and clear button.
8. **Re-enable tracking** — set consent to `no` (in devtools: `localStorage.setItem('path-log-consent', 'no')`); reload `/garden/history/`; empty-state shows "Re-enable tracking" button. Click → consent becomes `unset` and page reloads; banner will reappear on next stack growth.
9. **Mobile viewport (≤720px)** — resize browser to mobile width; visit `/garden/`; widget still shows. Visit a note; "N in stack" stays a `<span>`, no popover trigger. Visit `/garden/history/` → same content but the page-sidebar partial isn't used (just a single column).
10. **v1 → v2 migration** — manually set localStorage to a flat-array v1 form: `localStorage.setItem('garden-path-log', '["note-a","note-b","note-c"]')`. Reload `/garden/`; the widget should show one synthetic session. Inspect localStorage → it's been rewritten as the v2 envelope.

Wait for the user to walk through, report findings, and approve before moving on. Fix any issues raised and re-commit before proceeding to Task 11.

- [ ] **Step 3: Kill the dev server.**

```bash
pkill -f 'hugo server' 2>/dev/null || true
```

---

## Task 11: CI wiring

**Files:**
- Modify: `.github/workflows/hugo.yaml`

- [ ] **Step 1: Insert 2 new named steps after the existing RSS XSL pair and before `Build with Hugo`.**

Find the block:

```yaml
      - name: Verify RSS XSL
        run: python3 tools/check_rss_xsl.py
      - name: Run RSS XSL linter unit tests
        run: python3 -m unittest tools/test_check_rss_xsl.py -v
      - name: Build with Hugo
```

Replace with:

```yaml
      - name: Verify RSS XSL
        run: python3 tools/check_rss_xsl.py
      - name: Run RSS XSL linter unit tests
        run: python3 -m unittest tools/test_check_rss_xsl.py -v
      - name: Verify garden history
        run: python3 tools/check_garden_history.py
      - name: Run garden history linter unit tests
        run: python3 -m unittest tools/test_check_garden_history.py -v
      - name: Build with Hugo
```

- [ ] **Step 2: Validate YAML is well-formed.**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/hugo.yaml')); print('YAML OK')"
```

Expected: `YAML OK`.

- [ ] **Step 3: Confirm step count.**

```bash
grep -c '^      - name:' .github/workflows/hugo.yaml
```

Expected: `44`.

- [ ] **Step 4: Commit.**

```bash
git add .github/workflows/hugo.yaml
git commit -m "ci(garden-history): add linter pair to workflow (42 → 44 steps)"
```

---

## Task 12: CLAUDE.md update

**Files:**
- Modify: `CLAUDE.md`

Three edits: (a) add a new shipped bullet, (b) update the Final-QA bullet to mark all 3 Phase 8 deferrals resolved, (c) drop garden path-log from the Phase 8 follow-up "still waiting" list.

- [ ] **Step 1: Add the shipped bullet at the end of the "Shipped — Phases 0–6 plus targeted polish" list.** Find the existing RSS XSL bullet (most-recent entry in the shipped list) and add a new bullet after it. Suggested text (adapt commit hash to the actual final SHA at push time):

```markdown
- **Garden path-log retrieval** (post-Phase-8 polish, 2026-05-13): the persisted visited-notes list now has 3 consumer surfaces. `localStorage['garden-path-log']` schema migrated from v1 (flat slug array) to v2 (`{version:2, sessions:[{root, slugs, at}]}`); one-shot migration on first read wraps any v1 data as one synthetic session. **Three new surfaces:** (1) "Recent paths" widget at the top of `/garden/` showing up to 5 dedup'd most-recent paths as chip-arrow chains with relative-time stamps; (2) popover off the path-log "N in stack" count on note pages (desktop only) showing up to 4 dedup'd paths excluding the current session — `role=dialog` with focus trap + Esc-stops-propagation; (3) dedicated `/garden/history/` page with full list (up to 20 sessions), three empty-state variants per consent state, and a "Re-enable tracking" button for the `consent === 'no'` branch. Three new JS modules (`garden-history.js` shared core + 2 thin mount scripts; garden bundle grows ~5–7 KB). New linter pair `tools/check_garden_history.py` (10 source-side assertions including v2 schema sentinel in `garden-stack.js`). Workflow grows by 2 named steps (42 → 44). Closes the last Phase 8 deferral.
```

- [ ] **Step 2: Update the Final-QA bullet (line ~183 of CLAUDE.md).** Find:

```markdown
- **Final QA — partial pass** (Phase 8 Slice 3): … RSS link UX (shipped via the RSS XSL pretty-render slice — see entry below); garden path-log retrieval remains open (`docs/superpowers/specs/2026-05-13-garden-path-log-retrieval-design.md`).
```

Replace the trailing portion:

```markdown
- **Final QA — partial pass** (Phase 8 Slice 3): … RSS link UX (shipped via the RSS XSL pretty-render slice — see entry below); garden path-log retrieval (shipped via the garden path-log retrieval slice — see entry below).
```

- [ ] **Step 3: Drop garden path-log from the "Phase 8 follow-up" entry (line ~191 of CLAUDE.md).** Find:

```markdown
- **Phase 8 follow-up: interactive QA walkthrough.** … One non-blocking deferral still waits on its own slice: garden path-log retrieval (`docs/superpowers/specs/2026-05-13-garden-path-log-retrieval-design.md`).
```

Replace the trailing sentence:

```markdown
- **Phase 8 follow-up: interactive QA walkthrough.** … No outstanding deferrals — both queued Phase 8 deferrals shipped (RSS XSL pretty-render + garden path-log retrieval).
```

- [ ] **Step 4: Commit.**

```bash
git add CLAUDE.md
git commit -m "claude.md: log garden path-log retrieval shipped (closes last Phase 8 deferral)"
```

---

## Task 13: Final lint sweep + push handoff

**Files:** (none — verification + push)

- [ ] **Step 1: One more all-linters sweep.**

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
python3 tools/check_rss_xsl.py && \
python3 tools/check_garden_history.py && \
python3 tools/check_smoke.py && \
echo "ALL LINTERS OK"
```

Expected: `ALL LINTERS OK`.

- [ ] **Step 2: Confirm clean working tree.**

```bash
git status
```

Expected: `nothing to commit, working tree clean`.

- [ ] **Step 3: Review the commit list this slice produced.**

```bash
git log --oneline -15
```

Expected commit list (most recent first):
- `claude.md: log garden path-log retrieval shipped (closes last Phase 8 deferral)`
- `ci(garden-history): add linter pair to workflow (42 → 44 steps)`
- `feat(garden-history): wire entry imports + list.html partial`
- `feat(garden-history): popover module + path-log.html link + CSS`
- `feat(garden-history): /garden/history/ page + CSS`
- `feat(garden-history): widget + shared mount module + CSS §43`
- `feat(garden-history): migrate garden-stack to v2 sessions schema`
- `feat(garden-history): add shared storage + render core module`
- `feat(garden-history): implement linter (GREEN fixtures, RED project)`
- `test(garden-history): scaffold linter pair (RED)`
- `spec: garden path-log retrieval (promote stub to full design)`

Plus any browser-verification fix commits inserted during Task 10.

- [ ] **Step 4: Offer the user a final dev-server spot-check checklist, then push to origin/master.** Match the standing preference ([[verify-before-merge]] memory): visual verification + a "what to eyeball" list before push.

Suggested spot-check checklist for the user (re-read in browser, fresh load):

- `/garden/` — widget visible (assuming consent + data); 5 paths with chips + arrows + relative times.
- Click a path's leftmost chip → navigates to `/garden/<root>/?stack=…` and rebuilds the stack.
- `/garden/<note>/` — click "N in stack ▾" → popover opens; Esc closes + focus returns; click outside closes.
- "history →" chrome link present in path-log strip on every note page.
- `/garden/history/` — populated list + clear button works.
- Mobile (≤720px viewport) — widget visible; popover trigger stays inactive `<span>`.

- [ ] **Step 5: Once the user confirms, push.**

```bash
git push origin master
```

Expected: CI runs the new linter pair plus the existing 42 steps + build + LHCI; deploy publishes the new `/garden/history/` page.

- [ ] **Step 6: Verify on live site after deploy.**

Visit `https://a3madkour.github.io/garden/history/` — should render the empty-state branch (no localStorage data on a fresh visitor). Visit `/garden/` — widget hidden (no data). Walk through a stack, see widget appear, etc.

---

## Self-Review

Verifying spec coverage section-by-section:

- §2 goal 1 (3 consumer surfaces rendering paths) → Tasks 5 (widget), 6 (page), 7 (popover).
- §2 goal 2 (schema upgrade with migration) → Tasks 3 (core) + 4 (garden-stack migration).
- §2 goal 3 (privacy stance preserved) → Tasks 3 + 4 (consent gates unchanged; reads/writes still respect localStorage availability).
- §2 goal 4 (CI linter pair) → Tasks 1 + 2 + 11.
- §3 non-goals correctly out-of-scope: no banner re-enable affordance (re-enable lives on /history/ empty state — Task 6), no cross-device sync, no timeline graph, no edit-history-list, no lazy-load. None addressed in any task.
- §4 schema → Task 3 implementation.
- §5 runtime session lifecycle → Task 4 (steps 3–6).
- §6 widget on /garden/ → Tasks 5 + 8 (the partial include in list.html).
- §7 popover → Task 7.
- §8 history page → Task 6.
- §9 module split → Tasks 3, 5, 7 (the 3 new JS files); Task 8 wires entry imports.
- §10 a11y → spread across Tasks 5–7 (aria-labelledby on widget, aria-expanded on popover trigger, role=dialog + focus trap on popover, native `<button>`s with confirm dialogs for destructive actions).
- §11 CSS §43 → split across Tasks 5, 6, 7 (widget/shared/page/popover parts as each surface lands).
- §12 linter pair → Tasks 1 + 2 (10 assertions / 10 fixture cases each).
- §13 risks called out (schema-migration downgrade, localStorage unavailability, bundle size, sentinel rigidity, focus-trap zero-children) — all design notes, no task work needed; defensive code already in the JS modules.
- §15 file list (8 new + 7 modified) — matches the file structure table at the top of this plan.

Type / signature consistency:

- `readHistory()` (no args) — used in Tasks 3 (defines), 4 (imports), 5, 7.
- `writeHistory(sessions)` — used in Tasks 3, 4.
- `dedupe(sessions)` — Tasks 3, 5, 7.
- `renderPath(session, options)` — Tasks 3, 5, 7.
- `clearHistory()` — Tasks 3, 5.
- `setConsent(value)` — Tasks 3, 5.
- `startSession()` / `extendSession(slug)` — Task 4 only.
- `currentSessionAt` (module state) — Task 4 only.
- CSS class names (`.garden-recent-paths`, `.recent-paths-list`, `.recent-paths-actions`, `.recent-paths-view-all`, `.recent-paths-clear`, `.path-row`, `.path-time`, `.path-chip`, `.path-arrow`, `.path-log-history`, `#path-log-popover`, `.popover-paths`, `.popover-history-link`, `.garden-history`, `.garden-history-status`, `.garden-history-actions`, `.garden-history-list`, `.garden-history-empty`, `.garden-history-clear`, `.reenable-tracking`) — consistent across Tasks 5, 6, 7.
- Linter assertion #10 sentinel: literal `"version": 2` substring in `assets/js/garden-stack.js` — Task 4 adds it via the top-of-file comment in step 1.

Placeholder scan: no TBDs, TODOs, vague-criteria, or "similar to Task N" pointers. All step code blocks contain runnable content.

Plan looks complete.

---

*End of plan. Execute via `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`.*
