"""Validate that LHCI URLs resolve to built pages.

Reads lighthouserc.json + lighthouserc.mobile.json. Three checks:
existence (each URL → public/<path>/index.html), desktop/mobile equality
(ordered list), and assertMatrix regex coverage (every matchingUrlPattern
matches at least one URL in collect.url).

Runs in CI after `hugo --minify` and before LHCI to fast-fail on
fixture-slug drift in seconds, not minutes. Paired with
tools/test_check_lhci_urls.py.

Exit codes:
  0 — all checks pass
  1 — one or more validation failures
  2 — bootstrap failure (public/ missing, config missing/unparseable)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


DESKTOP_CONFIG = Path("lighthouserc.json")
MOBILE_CONFIG = Path("lighthouserc.mobile.json")
PUBLIC_DIR = Path("public")
HOST_PREFIX = "http://localhost"


def file_for_url(public: Path, url: str) -> Path:
    """Map an LHCI URL to its built public/ file path."""
    if url.startswith(HOST_PREFIX):
        url = url[len(HOST_PREFIX):]
    rel = url.strip("/")
    if not rel:
        return public / "index.html"
    return public / rel / "index.html"


def check_existence(public: Path, urls: list[str], source: str) -> list[str]:
    """Each URL must resolve to public/<path>/index.html."""
    errors: list[str] = []
    for url in urls:
        f = file_for_url(public, url)
        if not f.is_file():
            relpath = f.relative_to(public)
            errors.append(f"{source}: {url}: missing file at {relpath}")
    return errors
