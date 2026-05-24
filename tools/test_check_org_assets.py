"""Unit tests for check_org_assets.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_org_assets as mod


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class TestLintBundle(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="check_org_assets_test_"))
        self.bundle = self.tmp / "bundle"
        self.static_shared = self.tmp / "static" / "notes-shared"
        self.static_shared.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _lint(self) -> tuple[list[str], list[str]]:
        return mod.lint_bundle(self.bundle, self.static_shared)

    # ---- Healthy cases -------------------------------------------------

    def test_healthy_local_and_shared(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n'
               '<img src="x.png" alt="x" />\n'
               '<img src="/notes-shared/y.svg" alt="y" />\n')
        _write(self.bundle / "x.png", "binary-data")
        _write(self.static_shared / "y.svg", "<svg/>")
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_empty_bundle(self) -> None:
        _write(self.bundle / "index.md", '---\ntitle: ok\n---\nNo refs.')
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_markdown_image_syntax(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n![alt](x.png)\n')
        _write(self.bundle / "x.png", "d")
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    # ---- Error cases ---------------------------------------------------

    def test_broken_local_ref(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<img src="missing.png" alt="" />')
        errors, _ = self._lint()
        self.assertTrue(any("missing.png" in e and "does not resolve" in e for e in errors),
                        errors)

    def test_broken_shared_ref(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<img src="/notes-shared/missing.svg" alt="" />')
        errors, _ = self._lint()
        self.assertTrue(any("missing.svg" in e and "shared ref" in e for e in errors),
                        errors)

    def test_orphan_file(self) -> None:
        _write(self.bundle / "index.md", '---\ntitle: ok\n---\nNo refs.')
        _write(self.bundle / "cruft.png", "data")
        errors, _ = self._lint()
        self.assertTrue(any("orphan" in e and "cruft.png" in e for e in errors), errors)

    def test_path_traversal(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<img src="../foo.png" alt="" />')
        errors, _ = self._lint()
        self.assertTrue(any("traversal" in e for e in errors), errors)

    # ---- Skip cases ----------------------------------------------------

    def test_external_skip(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<a href="https://example.com">x</a>')
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_anchor_skip(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<a href="#section">x</a>')
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_internal_route_skip(self) -> None:
        _write(self.bundle / "index.md",
               '---\ntitle: ok\n---\n<a href="/garden/other/">x</a>')
        errors, _ = self._lint()
        self.assertEqual(errors, [])

    def test_dotfiles_preserved(self) -> None:
        _write(self.bundle / "index.md", '---\ntitle: ok\n---\nNo refs.')
        _write(self.bundle / ".publish-state", "x")
        errors, _ = self._lint()
        self.assertEqual(errors, [])  # Dotfile is not flagged orphan


if __name__ == "__main__":
    unittest.main()
