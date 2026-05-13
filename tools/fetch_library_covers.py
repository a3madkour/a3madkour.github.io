#!/usr/bin/env python3
"""Fetch cover art for library items.

Stdlib-only. Author-driven; not invoked at build time. See:
docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
COVERS_DIR = REPO_ROOT / "assets" / "images" / "library" / "covers"
DATA_DIR   = REPO_ROOT / "data"
AUDIT_LOG  = REPO_ROOT / "tools" / ".cover-cache.json"
CONFIG     = REPO_ROOT / "tools" / ".fetch-config.json"

MEDIA_CHOICES = ("book", "album", "track", "game", "film", "series", "all")
MEDIUM_TO_LEAF = {
    "book":   "reading",
    "album":  "listening",
    "track":  "listening",
    "game":   "playing",
    "film":   "watching",
    "series": "watching",
}

def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch library cover art")
    p.add_argument("--medium", choices=MEDIA_CHOICES, default="all")
    p.add_argument("--force", action="store_true",
                   help="re-fetch even if cache hit")
    p.add_argument("--dry-run", action="store_true",
                   help="print planned actions; no network or disk writes")
    return p.parse_args(argv)

def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    print(f"medium={args.medium} force={args.force} dry_run={args.dry_run}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
