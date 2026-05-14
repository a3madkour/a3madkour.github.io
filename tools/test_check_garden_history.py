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

    overrides: any of the 10 file paths above keyed by short name — set to None
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
