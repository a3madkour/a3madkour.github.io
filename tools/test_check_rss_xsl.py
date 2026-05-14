"""Tests for check_rss_xsl.py — run with:
   python3 -m unittest tools/test_check_rss_xsl.py -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_rss_xsl as lint  # noqa: E402


# Minimal valid XSL: stylesheet root, template match="/", emits <style>.
VALID_XSL = """\
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="utf-8"/>
  <xsl:template match="/">
    <html lang="en">
      <head>
        <title><xsl:value-of select="/rss/channel/title"/></title>
        <style>body { font-family: serif; }</style>
      </head>
      <body><xsl:value-of select="/rss/channel/title"/></body>
    </html>
  </xsl:template>
</xsl:stylesheet>
"""

# Essays RSS template WITH the PI on the line before <rss>.
ESSAYS_RSS_WITH_PI = """\
{{- $pages := where site.RegularPages "Section" "essays" -}}
{{- printf "<?xml-stylesheet type=\\"text/xsl\\" href=\\"%s\\"?>" ((resources.Get "feed/feed.xsl").RelPermalink) | safeHTML }}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel><title>x</title></channel>
</rss>
"""

# Essays RSS template WITHOUT the PI.
ESSAYS_RSS_NO_PI = """\
{{- $pages := where site.RegularPages "Section" "essays" -}}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel><title>x</title></channel>
</rss>
"""

# Essays RSS template with PI AFTER <rss> (invalid placement).
ESSAYS_RSS_PI_AFTER_RSS = """\
{{- $pages := where site.RegularPages "Section" "essays" -}}
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <?xml-stylesheet type="text/xsl" href="/feed/feed.xsl"?>
  <channel><title>x</title></channel>
</rss>
"""

# Garden RSS template — clean, no PI.
GARDEN_RSS_NO_PI = """\
<rss version="2.0">
  <channel><title>garden</title></channel>
</rss>
"""

# Garden RSS template — accidentally has the PI (scope guard violation).
GARDEN_RSS_WITH_PI = """\
{{- printf "<?xml-stylesheet type=\\"text/xsl\\" href=\\"%s\\"?>" ((resources.Get "feed/feed.xsl").RelPermalink) | safeHTML }}
<rss version="2.0">
  <channel><title>garden</title></channel>
</rss>
"""


def _write_fixture(tmpdir: Path, xsl: str | None, essays_rss: str, garden_rss: str) -> tuple[Path, Path, Path]:
    """Lay out a minimal tree under tmpdir mirroring the project layout."""
    xsl_path = tmpdir / "assets" / "feed" / "feed.xsl"
    essays_path = tmpdir / "layouts" / "essays" / "rss.xml"
    garden_path = tmpdir / "layouts" / "garden" / "rss.xml"
    if xsl is not None:
        xsl_path.parent.mkdir(parents=True, exist_ok=True)
        xsl_path.write_text(xsl)
    essays_path.parent.mkdir(parents=True, exist_ok=True)
    essays_path.write_text(essays_rss)
    garden_path.parent.mkdir(parents=True, exist_ok=True)
    garden_path.write_text(garden_rss)
    return xsl_path, essays_path, garden_path


class TestRssXslLinter(unittest.TestCase):
    def test_happy_path(self):
        # Fixture 1: well-formed XSL + essays PI present + garden PI absent.
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), VALID_XSL, ESSAYS_RSS_WITH_PI, GARDEN_RSS_NO_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertEqual(errors, [], f"expected clean, got: {errors}")

    def test_missing_xsl(self):
        # Fixture 2: XSL file does not exist.
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), None, ESSAYS_RSS_WITH_PI, GARDEN_RSS_NO_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertTrue(
                any("feed.xsl" in e and "missing" in e.lower() for e in errors),
                f"expected 'missing feed.xsl' error, got: {errors}",
            )

    def test_missing_essays_pi(self):
        # Fixture 3: XSL present but essays template has no PI.
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), VALID_XSL, ESSAYS_RSS_NO_PI, GARDEN_RSS_NO_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertTrue(
                any("essays/rss.xml" in e and "xml-stylesheet" in e for e in errors),
                f"expected 'essays/rss.xml missing xml-stylesheet' error, got: {errors}",
            )

    def test_essays_pi_after_rss(self):
        # Fixture 4: PI appears after <rss> (invalid placement).
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), VALID_XSL, ESSAYS_RSS_PI_AFTER_RSS, GARDEN_RSS_NO_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertTrue(
                any("essays/rss.xml" in e and "before" in e.lower() for e in errors),
                f"expected 'PI must precede <rss>' error, got: {errors}",
            )

    def test_garden_has_pi(self):
        # Fixture 5: scope guard — garden template has the PI.
        with tempfile.TemporaryDirectory() as td:
            xsl, essays, garden = _write_fixture(
                Path(td), VALID_XSL, ESSAYS_RSS_WITH_PI, GARDEN_RSS_WITH_PI
            )
            errors = lint.lint_rss_xsl(xsl, essays, garden)
            self.assertTrue(
                any("garden/rss.xml" in e and "xml-stylesheet" in e for e in errors),
                f"expected 'garden scope guard' error, got: {errors}",
            )


if __name__ == "__main__":
    unittest.main()
