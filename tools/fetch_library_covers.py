#!/usr/bin/env python3
"""Fetch cover art for library items.

Stdlib-only. Author-driven; not invoked at build time. See:
docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, cast

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

def load_audit_log() -> dict:
    if AUDIT_LOG.exists():
        return json.loads(AUDIT_LOG.read_text())
    return {}

def write_audit_log(log: dict) -> None:
    AUDIT_LOG.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n")

def update_audit_entry(log: dict, slug: str, source_kind: str, source: object, sha256: str) -> None:
    log[slug] = {
        "source_kind": source_kind,
        "source": source,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha256,
    }

def load_config() -> dict:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text())
    return {"contact_email": "anonymous@example.com"}

def build_ua(cfg: dict) -> str:
    return f"a3madkour-site/0.1 ({cfg.get('contact_email', 'anonymous@example.com')})"

PER_SOURCE_SLEEP_MS = {"cover_url": 50, "isbn": 100, "mbid": 250}
DEFAULT_TIMEOUT_S = 10

def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    cfg = load_config()
    ua = build_ua(cfg)
    audit = load_audit_log()
    rc = 0

    leaves = LEAVES if args.medium == "all" else (MEDIUM_TO_LEAF[args.medium],)
    for leaf in leaves:
        for item in load_leaf(leaf):
            if args.medium != "all" and item.get("media_type") != args.medium:
                continue
            source = pick_source(item)
            if source is None:
                continue
            kind, value = source
            slug = item["slug"]
            target = COVERS_DIR / (cast(str, value) if kind == "cover_file" else f"{slug}.jpg")
            if target.exists() and not args.force:
                continue
            if args.dry_run:
                print(f"[dry-run] {slug}: fetch via {kind} → {target}")
                continue
            result: FetchResult | None = None
            try:
                if kind == "cover_file":
                    result = dispatch_cover_file(slug=slug, cover_file=cast(str, value), covers_dir=COVERS_DIR)
                elif kind == "cover_url":
                    result = dispatch_cover_url(slug=slug, url=cast(str, value), covers_dir=COVERS_DIR, ua=ua, timeout_s=DEFAULT_TIMEOUT_S)
                elif kind == "isbn":
                    result = dispatch_isbn(slug=slug, isbn=cast(str, value), covers_dir=COVERS_DIR, ua=ua, timeout_s=DEFAULT_TIMEOUT_S)
                elif kind == "mbid":
                    result = dispatch_mbid(slug=slug, mbid=cast(str, value), covers_dir=COVERS_DIR, ua=ua, timeout_s=DEFAULT_TIMEOUT_S)
                elif kind == "igdb_id":
                    dispatch_igdb(slug=slug, igdb_id=cast(int, value), covers_dir=COVERS_DIR, ua=ua, timeout_s=DEFAULT_TIMEOUT_S)
                    continue
                elif kind == "tmdb_id":
                    dispatch_tmdb(slug=slug, tmdb_id=cast(int, value), covers_dir=COVERS_DIR, ua=ua, timeout_s=DEFAULT_TIMEOUT_S)
                    continue
            except NotImplementedError as e:
                print(f"{slug}: {e}", file=sys.stderr)
                rc = 1
                continue
            if result is None or not result.cached:
                if result is not None:
                    print(f"{slug}: {result.error}", file=sys.stderr)
                rc = 1
                continue
            if result.sha256:
                update_audit_entry(audit, slug, kind, value, result.sha256)
            ms = PER_SOURCE_SLEEP_MS.get(kind, 0)
            if ms:
                time.sleep(ms / 1000)

    if not args.dry_run:
        write_audit_log(audit)
    return rc

# Source priority order. Per-medium ID keys are only consulted for the matching media_type.
MEDIA_TO_ID_KEY = {
    "book":   ("isbn",   "isbn"),
    "album":  ("musicbrainz_release_group", "mbid"),
    "track":  ("musicbrainz_release_group", "mbid"),
    "game":   ("igdb_id", "igdb_id"),
    "film":   ("tmdb_id", "tmdb_id"),
    "series": ("tmdb_id", "tmdb_id"),
}

def pick_source(item: dict) -> tuple[str, str | int] | None:
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


RETRY_BACKOFF_S = 2.0

def _download(url: str, ua: str, timeout_s: int) -> bytes:
    """Single GET. Raises urllib.error.HTTPError on non-2xx."""
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read()

def _download_with_retry(url: str, ua: str, timeout_s: int) -> bytes:
    """Download with one retry on 5xx."""
    try:
        return _download(url, ua, timeout_s)
    except urllib.error.HTTPError as e:
        if 500 <= e.code < 600:
            time.sleep(RETRY_BACKOFF_S)
            return _download(url, ua, timeout_s)
        raise

def dispatch_cover_url(*, slug: str, url: str, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    target = covers_dir / f"{slug}.jpg"
    try:
        body = _download_with_retry(url, ua, timeout_s)
    except urllib.error.HTTPError as e:
        return FetchResult(kind="cover_url", slug=slug, path=target,
                           cached=False, error=f"HTTP {e.code}: {url}")
    except urllib.error.URLError as e:
        return FetchResult(kind="cover_url", slug=slug, path=target,
                           cached=False, error=f"URLError: {e.reason} for {url}")
    covers_dir.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return FetchResult(kind="cover_url", slug=slug, path=target,
                       cached=True, sha256=hashlib.sha256(body).hexdigest())


def openlibrary_url(isbn: str) -> str:
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

def coverart_archive_url(mbid: str) -> str:
    return f"https://coverartarchive.org/release-group/{mbid}/front-500"

def dispatch_isbn(*, slug: str, isbn: str, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    url = openlibrary_url(isbn)
    result = dispatch_cover_url(slug=slug, url=url, covers_dir=covers_dir, ua=ua, timeout_s=timeout_s)
    return FetchResult(kind="isbn", slug=slug, path=result.path,
                       cached=result.cached, error=result.error, sha256=result.sha256)

def dispatch_mbid(*, slug: str, mbid: str, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    url = coverart_archive_url(mbid)
    result = dispatch_cover_url(slug=slug, url=url, covers_dir=covers_dir, ua=ua, timeout_s=timeout_s)
    return FetchResult(kind="mbid", slug=slug, path=result.path,
                       cached=result.cached, error=result.error, sha256=result.sha256)


def dispatch_igdb(*, slug: str, igdb_id: int, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    raise NotImplementedError(
        f"IGDB live fetch requires IGDB_CLIENT_ID + IGDB_CLIENT_SECRET; "
        f"rerun when wired (slug={slug}, igdb_id={igdb_id})"
    )


def dispatch_tmdb(*, slug: str, tmdb_id: int, covers_dir: Path, ua: str, timeout_s: int) -> FetchResult:
    raise NotImplementedError(
        f"TMDB live fetch requires TMDB_API_KEY; "
        f"rerun when wired (slug={slug}, tmdb_id={tmdb_id})"
    )


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
