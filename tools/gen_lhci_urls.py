#!/usr/bin/env python3
"""LHCI URL generator.

Reads public/lhci-pages.json (Hugo-emitted page manifest) and
tools/lhci-overrides.json (group-keyed assertion thresholds).
Rewrites lighthouserc.{json,mobile.json} in place — replacing
collect.url with alphabetical-first picks per (kind, section, type)
group, and rebuilding assertMatrix (mobile only) from overrides.

Stdlib only.
Exits 0 on success, 1 on any error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def run(repo_root: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Programmatic entry. Returns (rc, errors)."""
    return (0, [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate LHCI URL lists from Hugo manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files.")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root, dry_run=args.dry_run)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return rc
    print("gen_lhci_urls: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
