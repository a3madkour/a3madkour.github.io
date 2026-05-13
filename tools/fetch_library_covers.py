#!/usr/bin/env python3
"""Fetch cover art for library items.

Stdlib-only. Author-driven; not invoked at build time. See:
docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md
"""
from __future__ import annotations
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_library_fixtures import parse_library_yaml  # noqa: E402

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

# Source priority order. Per-medium ID keys are only consulted for the matching media_type.
MEDIA_TO_ID_KEY = {
    "book":   ("isbn",   "isbn"),
    "album":  ("musicbrainz_release_group", "mbid"),
    "track":  ("musicbrainz_release_group", "mbid"),
    "game":   ("igdb_id", "igdb_id"),
    "film":   ("tmdb_id", "tmdb_id"),
    "series": ("tmdb_id", "tmdb_id"),
}

def pick_source(item: dict) -> tuple[str, object] | None:
    extras = item.get("extras") or {}
    if "cover_file" in extras and extras["cover_file"]:
        return ("cover_file", extras["cover_file"])
    if "cover_url" in extras and extras["cover_url"]:
        return ("cover_url", extras["cover_url"])
    media = item.get("media_type")
    if media in MEDIA_TO_ID_KEY:
        yaml_key, source_kind = MEDIA_TO_ID_KEY[media]
        if yaml_key in extras and extras[yaml_key]:
            return (source_kind, extras[yaml_key])
    return None


@dataclass
class FetchResult:
    kind: str
    slug: str
    path: Path | None = None
    cached: bool = False
    error: str | None = None
    sha256: str | None = None


def dispatch_cover_file(*, slug: str, cover_file: str, covers_dir: Path) -> FetchResult:
    target = covers_dir / cover_file
    if target.exists():
        return FetchResult(kind="cover_file", slug=slug, path=target, cached=True)
    return FetchResult(kind="cover_file", slug=slug, path=target,
                       cached=False, error=f"cover_file {cover_file} not found in {covers_dir}")


LEAVES = ("reading", "listening", "playing", "watching")

def load_leaf(leaf: str) -> list[dict]:
    """Parse data/<leaf>.yaml into a list of item dicts.

    Reuses the hand-rolled parser from check_library_fixtures.py
    (the project bans PyYAML; this preserves that contract).
    """
    path = DATA_DIR / f"{leaf}.yaml"
    return parse_library_yaml(path.read_text())


if __name__ == "__main__":
    sys.exit(main())
