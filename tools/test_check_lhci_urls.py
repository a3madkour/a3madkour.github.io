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
