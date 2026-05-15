#!/usr/bin/env bash
# Run the full CI-equivalent locally before `git push`.
#
# Mirrors .github/workflows/hugo.yaml step-for-step. Exits non-zero on the
# FIRST failure (set -e) so a green run means CI will be green.
#
# Usage: tools/ci-local.sh
#
# Requires: hugo (extended), python3 (stdlib only).

set -euo pipefail

cd "$(dirname "$0")/.."

separator() { printf "\n\033[1;34m── %s ──\033[0m\n" "$1"; }

separator "Pre-build linters + sibling tests"

python3 tools/check-contrast.py

python3 tools/check_fixtures.py
python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -3

python3 tools/check_garden_fixtures.py
python3 -m unittest tools/test_check_garden_fixtures.py -v 2>&1 | tail -3

python3 tools/check_garden_links.py
python3 -m unittest tools/test_check_garden_links.py -v 2>&1 | tail -3

python3 tools/check_filter_chips_config.py
python3 -m unittest tools/test_check_filter_chips_config.py -v 2>&1 | tail -3

python3 tools/check_research_fixtures.py
python3 -m unittest tools/test_check_research_fixtures.py -v 2>&1 | tail -3

python3 tools/check_research_links.py
python3 -m unittest tools/test_check_research_links.py -v 2>&1 | tail -3

python3 tools/check_citations.py
python3 -m unittest tools/test_check_citations.py -v 2>&1 | tail -3

python3 tools/check_works_fixtures.py
python3 -m unittest tools/test_check_works_fixtures.py -v 2>&1 | tail -3

python3 tools/check_works_links.py
python3 -m unittest tools/test_check_works_links.py -v 2>&1 | tail -3

python3 tools/check_library_fixtures.py
python3 -m unittest tools/test_check_library_fixtures.py -v 2>&1 | tail -3

python3 tools/check_library_links.py
python3 -m unittest tools/test_check_library_links.py -v 2>&1 | tail -3

python3 tools/check_library_covers.py
python3 -m unittest tools/test_check_library_covers.py -v 2>&1 | tail -3

python3 tools/check_icon_attribution.py
python3 -m unittest tools/test_check_icon_attribution.py -v 2>&1 | tail -3

python3 tools/check_library_shelves.py
python3 -m unittest tools/test_check_library_shelves.py -v 2>&1 | tail -3

python3 tools/check_rss_xsl.py
python3 -m unittest tools/test_check_rss_xsl.py -v 2>&1 | tail -3

python3 tools/check_garden_history.py
python3 -m unittest tools/test_check_garden_history.py -v 2>&1 | tail -3

separator "Production build (HUGO_ENVIRONMENT=production strips drafts; matches CI)"

# Kill any dev server first — `hugo --minify` poisons the dev-server CSS via
# MIME mismatch if it's alive.
pkill -f 'hugo server' 2>/dev/null || true

rm -rf public
HUGO_ENVIRONMENT=production hugo --minify

separator "Post-build linters + sibling tests"

# Pagefind test must be invoked from tools/ (it does a bare `from
# check_pagefind_meta import ...` with no sys.path manipulation, matching
# the CI workflow's `cd tools && python3 -m unittest ...` form).
(cd tools && python3 -m unittest test_check_pagefind_meta.py -v 2>&1 | tail -3)
python3 tools/check_pagefind_meta.py

(cd tools && python3 -m unittest test_check_cite_meta.py -v 2>&1 | tail -3)
python3 tools/check_cite_meta.py

python3 -m unittest tools/test_check_page_weights.py -v 2>&1 | tail -3
python3 tools/check_page_weights.py

python3 tools/check_smoke.py

separator "CI-EQUIVALENT GREEN — safe to push"
