"""Tests for check_toc_depth.py — run with: python3 -m unittest tools/test_check_toc_depth.py -v"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_toc_depth as lint  # noqa: E402  # pyright: ignore[reportMissingImports]
from test_helpers import TempRepo as _TempRepo  # noqa: E402


def essay(draft: bool, body: str) -> str:
    return (
        "---\n"
        'title: "X"\n'
        "draft: " + ("true" if draft else "false") + "\n"
        "---\n\n" + body
    )


DEEP = essay(False, "## H2 a\n\n### H3 a\n\n#### H4 a\n\nbody\n")
SHALLOW = essay(False, "## H2 a\n\n### H3 a\n\nbody\n")
DRAFT_DEEP = essay(True, "## H2 a\n\n### H3 a\n\n#### H4 a\n\nbody\n")
FENCED_FAKE_DEPTH = essay(
    False,
    "## H2 a\n\n```text\n### not a heading\n#### not a heading\n```\n\nbody\n",
)


class TempRepo(_TempRepo):
    def __init__(self) -> None:
        super().__init__()
        (self.root / "content" / "essays").mkdir(parents=True)

    def write_essay(self, slug: str, text: str) -> None:
        self.write(f"content/essays/{slug}/index.md", text)


class CheckTocDepthTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    def test_one_deep_essay_passes(self) -> None:
        self.repo.write_essay("deep", DEEP)
        self.repo.write_essay("shallow", SHALLOW)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0, msg=f"unexpected failures: {errors}")
        self.assertEqual(errors, [])

    def test_all_shallow_fails(self) -> None:
        self.repo.write_essay("shallow-1", SHALLOW)
        self.repo.write_essay("shallow-2", SHALLOW)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("3 distinct heading levels" in e for e in errors))

    def test_draft_deep_does_not_count(self) -> None:
        self.repo.write_essay("draft-deep", DRAFT_DEEP)
        self.repo.write_essay("shallow", SHALLOW)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("3 distinct heading levels" in e for e in errors))

    def test_fenced_code_block_depth_ignored(self) -> None:
        self.repo.write_essay("fenced", FENCED_FAKE_DEPTH)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("3 distinct heading levels" in e for e in errors))

    def test_empty_essays_section_passes(self) -> None:
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 0)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
