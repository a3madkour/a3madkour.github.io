import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo  # noqa: E402
import check_image_ladder as mod  # noqa: E402

TPL = """\
{{- with $p.Params.image -}}
  {{- $img := . -}}
  {{- if or (hasPrefix $img "http://") (hasPrefix $img "https://") -}}
  {{- else if hasPrefix $img "/" -}}
    {{- $img = absURL $img -}}
  {{- else -}}
    {{- $img = printf "%s%s" $p.Permalink $img -}}
  {{- end -}}
{{- end -}}
"""

LINT = '''\
def lint_file(md):
    if val.startswith(("http://", "https://")):
        pass
    elif val.startswith("//"):
        pass
    elif val.startswith("/"):
        pass
'''


class T(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.write("layouts/partials/recipes/schema-recipe.html", TPL)
        self.repo.write("tools/check_recipes_links.py", LINT)

    def tearDown(self):
        self.repo.cleanup()

    def test_matching_ladders_pass(self):
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)

    def test_template_gains_a_branch_the_linter_lacks(self):
        """The dangerous direction: the linter certifies what the template mangles."""
        tpl = TPL.replace(
            '{{- else if hasPrefix $img "/" -}}',
            '{{- else if hasPrefix $img "data:" -}}\n  {{- else if hasPrefix $img "/" -}}',
        )
        self.repo.write("layouts/partials/recipes/schema-recipe.html", tpl)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("'data:'" in e and "does not" in e for e in errs), errs)

    def test_linter_gains_a_branch_the_template_lacks(self):
        """The other direction: a legitimate shape gets falsely rejected."""
        lint = LINT.replace(
            '    elif val.startswith("//"):',
            '    elif val.startswith("ftp://"):\n        pass\n    elif val.startswith("//"):',
        )
        self.repo.write("tools/check_recipes_links.py", lint)
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("'ftp://'" in e for e in errs), errs)

    def test_protocol_relative_is_an_allowed_linter_only_extra(self):
        """`//` narrows within the template's `/` branch; it is not drift."""
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 0, errs)
        self.assertFalse(any("'//'" in e for e in errs), errs)

    def test_ladder_removed_from_template_is_loud(self):
        self.repo.write("layouts/partials/recipes/schema-recipe.html", "{{- /* gone */ -}}")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("has the ladder moved" in e for e in errs), errs)

    def test_ladder_removed_from_linter_is_loud(self):
        self.repo.write("tools/check_recipes_links.py", "def lint_file(md):\n    pass\n")
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("has the ladder moved" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
