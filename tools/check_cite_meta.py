"""Verify citation export markup on every citable page in public/.

Asserts each citable page (essays/garden/research/works single pages) has:
- citation_title, citation_author, citation_publication_date,
  citation_online_date, citation_public_url meta tags
- <script type="application/json" id="cite-data"> that parses, with:
    - self.citekey matching `madkour-<year>-<slug>`
    - self.formats with all 5 keys (bibtex, apa, chicago, mla, ris)
    - every refs key existing in data/citations.yaml
- <section id="cite-this"> static fallback

Non-citable pages (About, Library, Home, umbrellas, graph pages) are
skipped silently.

Stdlib only. Exits non-zero on any violation.
"""
from __future__ import annotations
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

PUBLIC = Path('public')

REQUIRED_META = [
    'citation_title',
    'citation_author',
    'citation_publication_date',
    'citation_online_date',
    'citation_public_url',
]
REQUIRED_FORMATS = ['bibtex', 'apa', 'chicago', 'mla', 'ris']
CITEKEY_RE = re.compile(r'^madkour-\d{4}-[a-z0-9-]+$')

CITABLE_PREFIXES = (
    'public/essays/',
    'public/garden/',
    'public/research/themes/',
    'public/research/questions/',
    'public/works/games/',
    'public/works/music/',
    'public/works/poetry/',
    'public/streams/',
)

NON_CITABLE_EXACT = {
    'public/index.html',
    'public/about/index.html',
    'public/library/index.html',
    'public/library/reading/index.html',
    'public/library/listening/index.html',
    'public/library/playing/index.html',
    'public/library/watching/index.html',
    'public/essays/index.html',
    'public/garden/index.html',
    'public/garden/graph/index.html',
    'public/garden/history/index.html',
    'public/research/index.html',
    'public/research/graph/index.html',
    'public/works/index.html',
    'public/works/graph/index.html',
    'public/works/games/index.html',
    'public/works/music/index.html',
    'public/works/poetry/index.html',
    'public/streams/index.html',
}


def is_citable_path(p: str) -> bool:
    p = p.replace('\\', '/')
    if p in NON_CITABLE_EXACT:
        return False
    if not any(p.startswith(prefix) for prefix in CITABLE_PREFIXES):
        return False
    rest = p[len('public/'):]
    parts = rest.split('/')
    if parts[-1] != 'index.html':
        return False
    # Need at least: <section>/<slug>/index.html (3 parts) or deeper.
    return len(parts) >= 3


class _MetaCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metas = []
        self.cite_data = None
        self.has_cite_this = False
        self._in_cite_data = False
        self._cite_data_buf = []

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        name = attrs_d.get('name') or ''
        cls = attrs_d.get('class') or ''
        if tag == 'meta' and name.startswith('citation_'):
            self.metas.append((name, attrs_d.get('content') or ''))
        elif tag == 'script' and 'cite-data' in cls.split():
            self._in_cite_data = True
        elif tag == 'section' and attrs_d.get('id') == 'cite-this':
            self.has_cite_this = True

    def handle_endtag(self, tag):
        if tag == 'script' and self._in_cite_data:
            self._in_cite_data = False
            self.cite_data = ''.join(self._cite_data_buf).strip()

    def handle_data(self, data):
        if self._in_cite_data:
            self._cite_data_buf.append(data)


def inspect_html(html: str, citations: dict) -> list[str]:
    issues = []
    p = _MetaCollector()
    p.feed(html)

    meta_names = [m[0] for m in p.metas]
    for required in REQUIRED_META:
        if required not in meta_names:
            issues.append(f'missing <meta name="{required}">')

    if p.cite_data is None:
        issues.append('missing <script class="cite-data">')
    else:
        try:
            blob = json.loads(p.cite_data)
        except json.JSONDecodeError as e:
            issues.append(f'cite-data JSON parse error: {e}')
            blob = None
        if blob is not None:
            self_obj = blob.get('self')
            if not isinstance(self_obj, dict):
                issues.append('cite-data.self missing or not a dict')
            else:
                key = self_obj.get('citekey', '')
                if not CITEKEY_RE.match(key):
                    issues.append(f'bad citekey shape: {key!r}')
                formats = self_obj.get('formats', {})
                for f in REQUIRED_FORMATS:
                    if not formats.get(f):
                        issues.append(f'self.formats.{f} missing or empty')
            refs = blob.get('refs', {})
            if isinstance(refs, dict):
                for key in refs:
                    if key not in citations:
                        issues.append(
                            f'refs.{key} not found in data/citations.yaml'
                        )

    if not p.has_cite_this:
        issues.append('missing <section id="cite-this">')

    return issues


def load_citations() -> dict:
    """Stdlib-only YAML key extraction. Returns {key: {}} for each
    top-level entry under `citations:` in data/citations.yaml."""
    path = Path('data/citations.yaml')
    text = path.read_text()
    keys = set()
    in_citations = False
    for line in text.splitlines():
        if line.strip().startswith('#') or not line.strip():
            continue
        if line.startswith('citations:'):
            in_citations = True
            continue
        if in_citations and re.match(r'^  [a-zA-Z0-9_-]+:\s*$', line):
            keys.add(line.strip().rstrip(':'))
    return {k: {} for k in keys}


def main() -> int:
    if not PUBLIC.exists():
        print('public/ not found — run `hugo --minify` first.', file=sys.stderr)
        return 2
    citations = load_citations()
    failures = 0
    for html_path in PUBLIC.rglob('*.html'):
        rel = str(html_path).replace('\\', '/')
        if not is_citable_path(rel):
            continue
        html = html_path.read_text(encoding='utf-8', errors='replace')
        issues = inspect_html(html, citations=citations)
        if issues:
            failures += 1
            print(f'{rel}:')
            for issue in issues:
                print(f'  - {issue}')
    if failures:
        print(
            f'\n{failures} citable page(s) failed cite-meta validation.',
            file=sys.stderr,
        )
        return 1
    print('cite-meta: OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
