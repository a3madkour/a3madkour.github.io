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
        # Python sorted() is codepoint-ordinal; 'á' (U+00E1) > 'z' (U+007A).
        # So /garden/zebra/ sorts before /garden/álpha/.
        self.assertEqual(picks["page:garden:garden"], "/garden/zebra/")

    def test_returns_dict_str_to_str(self) -> None:
        picks = gen.pick_representative_urls(SAMPLE_MANIFEST)
        for k, v in picks.items():
            self.assertIsInstance(k, str)
            self.assertIsInstance(v, str)


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
        # collect.url sorted by URL for determinism
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
        # If a stale assertMatrix exists in DESKTOP config, it's removed
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


if __name__ == "__main__":
    unittest.main()
