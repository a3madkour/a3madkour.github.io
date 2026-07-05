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

python3 tools/check_dark_tokens.py
python3 -m unittest tools/test_check_dark_tokens.py -v 2>&1 | tail -3

python3 tools/check_css_refs.py
python3 -m unittest tools/test_check_css_refs.py -v 2>&1 | tail -3

python3 tools/check_spacing_tokens.py
python3 -m unittest tools/test_check_spacing_tokens.py -v 2>&1 | tail -3

python3 tools/check_breakpoints.py
python3 -m unittest tools/test_check_breakpoints.py -v 2>&1 | tail -3

python3 tools/check_fixtures.py
python3 -m unittest tools/test_check_fixtures.py -v 2>&1 | tail -3

python3 tools/check_toc_depth.py
python3 -m unittest tools/test_check_toc_depth.py -v 2>&1 | tail -3

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

python3 tools/check_math.py
python3 -m unittest tools/test_check_math.py -v 2>&1 | tail -3

python3 tools/check_works_fixtures.py
python3 -m unittest tools/test_check_works_fixtures.py -v 2>&1 | tail -3

python3 tools/check_works_links.py
python3 -m unittest tools/test_check_works_links.py -v 2>&1 | tail -3

python3 tools/check_poetry_synced.py
python3 -m unittest tools/test_check_poetry_synced.py -v 2>&1 | tail -3

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

python3 tools/check_streams_fixtures.py
python3 -m unittest tools/test_check_streams_fixtures.py -v 2>&1 | tail -3

python3 tools/check_streams_links.py
python3 -m unittest tools/test_check_streams_links.py -v 2>&1 | tail -3

python3 tools/check_org_assets.py
python3 -m unittest tools/test_check_org_assets.py -v 2>&1 | tail -3

python3 tools/check_graph_chrome.py

separator "Production build (HUGO_ENVIRONMENT=production strips drafts; matches CI)"

# Kill any dev server first — `hugo --minify` poisons the dev-server CSS via
# MIME mismatch if it's alive.
pkill -f 'hugo server' 2>/dev/null || true

rm -rf public
HUGO_ENVIRONMENT=production hugo --gc --minify

# Build the Pagefind index into public/pagefind/ — CI does this between the
# Hugo build and the post-build checks (check_page_weights + LHCI run against
# a site that HAS /pagefind/). Skip with a loud warning if the binary isn't
# installed, so a local "green" doesn't silently omit the Pagefind path.
if command -v pagefind >/dev/null 2>&1; then
  pagefind --site public/ >/dev/null
elif command -v npx >/dev/null 2>&1; then
  # No pagefind binary, but npx is available — build the index via the pinned
  # release so the Playwright search spec (and pagefind-meta checks) exercise
  # the real /pagefind/ path instead of 404ing.
  printf "\033[1;33m⚠ pagefind not on PATH — building index via 'npx pagefind@1.5.2'.\033[0m\n"
  npx --yes pagefind@1.5.2 --site public/ >/dev/null
else
  printf "\033[1;33m⚠ neither pagefind nor npx on PATH — skipping index build; /pagefind/ 404s locally.\n  Install to exercise the full CI path (e.g. 'cargo install pagefind' or download the release binary).\033[0m\n"
fi

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

python3 tools/check_anchor_link.py
python3 -m unittest tools/test_check_anchor_link.py -v 2>&1 | tail -3

python3 tools/check_explorables.py
python3 -m unittest tools/test_check_explorables.py -v 2>&1 | tail -3

python3 tools/gen_lhci_urls.py
python3 -m unittest tools/test_gen_lhci_urls.py -v 2>&1 | tail -3

python3 tools/check_lhci_urls.py
(cd tools && python3 -m unittest test_check_lhci_urls.py -v 2>&1 | tail -3)

separator "Playwright E2E (built site)"

# Dev-only browser E2E over ./public. Needs Node (npx) + the Playwright
# chromium browser. Loud-skip if Node is absent so a local "green" still tells
# the truth about what ran (mirrors the LHCI need_lhci_dep preflight pattern).
if command -v npx >/dev/null 2>&1; then
  [ -d node_modules ] || npm ci
  npx playwright install chromium >/dev/null 2>&1 || true
  npx playwright test
else
  printf "\033[1;33m⚠ npx not found — skipping Playwright E2E. Install Node.js to run it (mirrors CI).\033[0m\n"
fi

separator "Lighthouse CI (desktop + mobile)"

# LHCI is the only CI gate that lives outside Python+Hugo. Catches things the
# static linters can't — third-party cookies on hotlinked images, /favicon.ico
# 404s, layout-shift, render-blocking resources, etc. Skipping it locally was
# what let the library-redesign merge ship red.
#
# Run order mirrors the workflow (desktop first, then mobile). Each invocation
# spins up a temporary static server against ./public, runs Lighthouse once
# per URL, and asserts the four category thresholds in the matching config.
#
# Requires `npx` (Node ≥ 14) and a Chrome/Chromium binary on PATH. We don't
# install Node from the script — fail loudly with a hint if either is missing.

need_lhci_dep() {
  local name="$1" hint="$2"
  if ! command -v "$name" >/dev/null 2>&1; then
    printf "\n\033[1;31m✘ %s not found.\033[0m %s\n" "$name" "$hint"
    exit 1
  fi
}

need_lhci_dep npx "Install Node.js (pacman -S nodejs npm). LHCI runs via 'npx --yes @lhci/cli'."
if ! command -v chromium >/dev/null 2>&1 && ! command -v google-chrome >/dev/null 2>&1; then
  printf "\n\033[1;31m✘ No chromium/google-chrome on PATH.\033[0m Install one (pacman -S chromium) — LHCI drives a headless browser.\n"
  exit 1
fi

npx --yes @lhci/cli@0.13.x autorun --config=lighthouserc.json
npx --yes @lhci/cli@0.13.x autorun --config=lighthouserc.mobile.json

separator "CI-EQUIVALENT GREEN — safe to push"
