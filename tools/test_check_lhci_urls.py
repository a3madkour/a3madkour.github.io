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
