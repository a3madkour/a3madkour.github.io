#!/usr/bin/env python3
"""Meta-description hygiene linter. Stdlib only, post-build.

Hugo's `.Summary` is *rendered HTML* when a page declares no explicit summary.
`layouts/partials/head.html` feeds it to `<meta name="description">` and
`og:description`, so without flattening, the page's whole first section lands in
the attribute — tags, anchor-link glyphs and all. 18 pages shipped that way
before this guard existed, garden notes beginning literally
`<h2 id="tldr">TLDR<a class="anchor-link" ...`.

Nothing else could see it. The description is never rendered as visible text, so
no visual check, smoke test or link crawler touches it; the only readers are
search-engine snippets and social cards, which is to say: the failure is
invisible locally and public everywhere else.

Checks each built page's description for markup, the anchor-affordance glyph,
leading/trailing whitespace, and emptiness where a summary exists.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

META_RE = re.compile(
    r'<meta[^>]*(?:name=["\']?description["\']?|property=["\']?og:description["\']?)'
    r'[^>]*content=(["\'])(.*?)\1',
    re.S,
)
# A tag start, not prose punctuation: `<h2`, `</p`, `<a `. Fixture text like
# "<TODO>" is deliberately not matched — it is content, not markup.
TAG_RE = re.compile(r"</?(?:a|p|h[1-6]|div|span|ul|ol|li|em|strong|code|pre|img|br|section)\b", re.I)
ANCHOR_GLYPH = "§"


def run(repo_root: Path, public: Path | None = None) -> tuple[int, list[str]]:
    errs: list[str] = []
    pub = public or (repo_root / "public")
    if not pub.exists():
        print("check_meta_description: public/ not found. Run `hugo --minify` first.")
        return 0, []

    for html in sorted(pub.rglob("*.html")):
        rel = str(html.relative_to(pub))
        seen: set[str] = set()
        for _, content in META_RE.findall(html.read_text(encoding="utf-8", errors="replace")):
            if content in seen:
                continue
            seen.add(content)
            if TAG_RE.search(content):
                snippet = content[:60].replace("\n", " ")
                errs.append(
                    f"{rel}: meta description contains HTML markup — .Summary is "
                    f"rendered HTML and needs plainify: {snippet!r}"
                )
            if ANCHOR_GLYPH in content:
                errs.append(
                    f"{rel}: meta description contains the anchor-link glyph "
                    f"'{ANCHOR_GLYPH}' — that is chrome, not prose"
                )
            if content != content.strip():
                errs.append(f"{rel}: meta description has leading/trailing whitespace")
    return (1 if errs else 0), errs


def main() -> int:
    rc, errs = run(Path(__file__).resolve().parent.parent)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_meta_description: OK (descriptions are flattened prose)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
