"""Unit tests for check_cite_meta.py.

Mirrors the layout of test_check_pagefind_meta.py: synthetic HTML strings,
no Hugo dependency, stdlib only.
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from check_cite_meta import (
    inspect_html,
    is_citable_path,
    CITEKEY_RE,
)

CITATIONS_FIXTURE = {
    "example-source-1": {},
}

HAPPY = """
<html><head>
<meta name="citation_title" content="A">
<meta name="citation_author" content="Madkour, Abdelrahman">
<meta name="citation_publication_date" content="2026-05-13">
<meta name="citation_online_date" content="2026-05-13">
<meta name="citation_public_url" content="https://x/y/">
</head><body>
<section id="cite-this"><details></details></section>
<script type="application/json" id="cite-data">
{"self":{"citekey":"madkour-2026-my-slug","title":"A","formats":{"bibtex":"x","apa":"x","chicago":"x","mla":"x","ris":"x"}},"refs":{}}
</script>
</body></html>
"""


class TestCiteMeta(unittest.TestCase):
    def test_happy_path_passes(self):
        issues = inspect_html(HAPPY, citations=CITATIONS_FIXTURE)
        self.assertEqual(issues, [])

    def test_missing_meta_tag_fails(self):
        broken = HAPPY.replace('<meta name="citation_title" content="A">', '')
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('citation_title' in i for i in issues))

    def test_bad_citekey_shape_fails(self):
        broken = HAPPY.replace('madkour-2026-my-slug', 'wrong_format')
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('citekey' in i for i in issues))

    def test_missing_cite_data_fails(self):
        broken = HAPPY.replace(
            '<script type="application/json" id="cite-data">',
            '<script type="application/json" id="something-else">',
        )
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('cite-data' in i for i in issues))

    def test_missing_static_section_fails(self):
        broken = HAPPY.replace(
            '<section id="cite-this"><details></details></section>', ''
        )
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('cite-this' in i for i in issues))

    def test_ref_key_not_in_citations_fails(self):
        broken = HAPPY.replace(
            '"refs":{}',
            '"refs":{"unknown-key":{"title":"x","formats":{"bibtex":"y","apa":"y","chicago":"y","mla":"y","ris":"y"}}}',
        )
        issues = inspect_html(broken, citations=CITATIONS_FIXTURE)
        self.assertTrue(any('unknown-key' in i for i in issues))

    def test_is_citable_path_essays(self):
        self.assertTrue(is_citable_path('public/essays/some-slug/index.html'))

    def test_is_citable_path_about_not_citable(self):
        self.assertFalse(is_citable_path('public/about/index.html'))

    def test_is_citable_path_library_not_citable(self):
        self.assertFalse(is_citable_path('public/library/reading/index.html'))

    def test_is_citable_path_garden_note_yes_index_no(self):
        self.assertTrue(is_citable_path('public/garden/some-note/index.html'))
        self.assertFalse(is_citable_path('public/garden/index.html'))

    def test_is_citable_path_garden_graph_not_citable(self):
        self.assertFalse(is_citable_path('public/garden/graph/index.html'))

    def test_is_citable_path_garden_history_not_citable(self):
        self.assertFalse(is_citable_path('public/garden/history/index.html'))

    def test_is_citable_path_works_subsection_not_citable(self):
        self.assertFalse(is_citable_path('public/works/games/index.html'))
        self.assertFalse(is_citable_path('public/works/music/index.html'))
        self.assertFalse(is_citable_path('public/works/poetry/index.html'))

    def test_is_citable_path_works_game_yes(self):
        self.assertTrue(
            is_citable_path('public/works/games/example-1/index.html')
        )

    def test_citekey_re_accepts_kebab_slug(self):
        self.assertRegex('madkour-2026-on-knowing-tools', CITEKEY_RE)

    def test_citekey_re_rejects_underscore(self):
        self.assertNotRegex('madkour-2026-on_knowing_tools', CITEKEY_RE)


if __name__ == '__main__':
    unittest.main()
