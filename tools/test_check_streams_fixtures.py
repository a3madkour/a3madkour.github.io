"""Tests for check_streams_fixtures.py — run with:
   python3 -m unittest tools/test_check_streams_fixtures.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_streams_fixtures as lint  # noqa: E402


VALID = """\
---
title: "Example stream"
date: 2026-04-10T19:00:00-04:00
platforms: [twitch, youtube]
category: coding
archive_status: archived
vod_url: "https://www.youtube.com/watch?v=abc"
draft: false
---

Body.
"""


class StreamsFixturesLinterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.streams = self.tmp / "content" / "streams"
        self.streams.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, slug: str, body: str) -> Path:
        d = self.streams / slug
        d.mkdir()
        p = d / "index.md"
        p.write_text(body)
        return p

    def test_valid_passes(self):
        p = self._write("2026-04-10-ex", VALID)
        self.assertEqual(lint.lint_file(p), [])

    def test_missing_title(self):
        body = VALID.replace('title: "Example stream"\n', "")
        p = self._write("missing-title", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'title'" in e for e in errs))

    def test_missing_date(self):
        body = VALID.replace("date: 2026-04-10T19:00:00-04:00\n", "")
        p = self._write("missing-date", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'date'" in e for e in errs))

    def test_missing_platforms(self):
        body = VALID.replace("platforms: [twitch, youtube]\n", "")
        p = self._write("missing-platforms", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'platforms'" in e for e in errs))

    def test_missing_category(self):
        body = VALID.replace("category: coding\n", "")
        p = self._write("missing-category", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'category'" in e for e in errs))

    def test_missing_archive_status(self):
        body = VALID.replace("archive_status: archived\n", "")
        p = self._write("missing-archive-status", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'archive_status'" in e for e in errs))

    def test_missing_draft(self):
        body = VALID.replace("draft: false\n", "")
        p = self._write("missing-draft", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("missing required field 'draft'" in e for e in errs))

    def test_bad_archive_status_enum(self):
        body = VALID.replace("archive_status: archived", "archive_status: pending")
        p = self._write("bad-status", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("archive_status='pending'" in e for e in errs))

    def test_bad_category_enum(self):
        body = VALID.replace("category: coding", "category: news")
        p = self._write("bad-category", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("category='news'" in e for e in errs))

    def test_platform_not_in_enum(self):
        body = VALID.replace("platforms: [twitch, youtube]", "platforms: [twitch, kick]")
        p = self._write("bad-platform", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("platforms[1]='kick'" in e for e in errs))

    def test_platforms_not_a_list(self):
        body = VALID.replace("platforms: [twitch, youtube]", "platforms: twitch")
        p = self._write("platforms-not-list", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("platforms must be a list" in e for e in errs))

    def test_archived_requires_vod_url(self):
        body = VALID.replace('vod_url: "https://www.youtube.com/watch?v=abc"\n', 'vod_url: ""\n')
        p = self._write("archived-no-vod", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("archive_status=archived requires non-empty vod_url" in e for e in errs))

    def test_removed_allows_empty_vod(self):
        body = VALID.replace("archive_status: archived", "archive_status: removed")
        body = body.replace('vod_url: "https://www.youtube.com/watch?v=abc"\n', 'vod_url: ""\n')
        p = self._write("removed-no-vod", body)
        self.assertEqual(lint.lint_file(p), [])

    def test_unknown_field(self):
        body = VALID.replace("draft: false\n", "draft: false\nrarity: 99\n")
        p = self._write("extra-field", body)
        errs = lint.lint_file(p)
        self.assertTrue(any("unknown field 'rarity'" in e for e in errs))

    def test_with_all_optionals(self):
        body = """\
---
title: "Full Stream"
date: 2026-04-10T19:00:00-04:00
duration: "2h 15m"
platforms: [twitch, youtube]
vod_url: "https://www.youtube.com/watch?v=abc"
twitch_archive_url: "https://twitch.tv/videos/123"
archive_url: "https://archive.org/details/abc"
archive_status: archived
category: research
tags: [example, research-reading]
summary: "Summary."
related_essays: [example-essay-one]
related_garden: [story-atoms]
related_research: [what-is-a-narrative-atom]
related_works: [example-playable-full-release]
draft: false
---

Body.
"""
        p = self._write("full", body)
        self.assertEqual(lint.lint_file(p), [])

    def test_runner_walks_streams_dir(self):
        self._write("a", VALID)
        self._write("b", VALID)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(errs, [])

    def test_runner_aggregates_errors(self):
        bad = VALID.replace("category: coding", "category: news")
        self._write("ok", VALID)
        self._write("bad", bad)
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(len(errs) >= 1)

    def test_data_yaml_streams_live_shape(self):
        # data/streams-live.yaml must have last_polled + live.{twitch,youtube} with is_live bool.
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "streams-live.yaml").write_text(
            "last_polled: 2026-05-19T00:00:00Z\n"
            "live:\n"
            "  twitch:\n"
            "    is_live: false\n"
            "    title: \"\"\n"
            "    started_at: \"\"\n"
            "    url: \"\"\n"
            "  youtube:\n"
            "    is_live: false\n"
            "    video_id: \"\"\n"
            "    title: \"\"\n"
            "    started_at: \"\"\n"
            "    url: \"\"\n"
        )
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 0, errs)

    def test_data_yaml_streams_live_missing_keys(self):
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "streams-live.yaml").write_text("foo: bar\n")
        rc, errs = lint.run(self.tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(any("streams-live.yaml" in e and "live" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
