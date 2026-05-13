#!/usr/bin/env python3
"""Library cover linter.

Validates cover-extras schema (fail), cache coverage (warn),
audit-log consistency (warn), and freshness (warn).
See spec: docs/superpowers/specs/2026-05-12-library-cover-fetch-design.md §9
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Iterable

REPO_ROOT  = Path(__file__).resolve().parent.parent
DATA_DIR   = REPO_ROOT / "data"
COVERS_DIR = REPO_ROOT / "assets" / "images" / "library" / "covers"
AUDIT_LOG  = REPO_ROOT / "tools" / ".cover-cache.json"
LEAVES     = ("reading", "listening", "playing", "watching")

ISBN_RE = re.compile(r"^\d{10}$|^\d{13}$")

COVER_KEYS_UNIVERSAL = {"cover_file", "cover_url"}
COVER_KEYS_BY_MEDIA = {
    "book":   {"isbn"},
    "album":  {"musicbrainz_release_group"},
    "track":  {"musicbrainz_release_group"},
    "game":   {"igdb_id"},
    "film":   {"tmdb_id"},
    "series": {"tmdb_id"},
}


def check_schema(items: Iterable[dict]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    for it in items:
        extras = it.get("extras") or {}
        media  = it.get("media_type")
        slug   = it.get("slug", "<unknown>")
        for key, value in extras.items():
            if key not in COVER_KEYS_UNIVERSAL and key not in COVER_KEYS_BY_MEDIA.get(media, set()):
                continue
            if key == "isbn":
                if not isinstance(value, str) or not ISBN_RE.match(value):
                    errors.append(f"{slug}: extras.isbn must be 10/13 digits, got {value!r}")
            elif key in {"igdb_id", "tmdb_id"}:
                if not isinstance(value, int) or value <= 0:
                    errors.append(f"{slug}: extras.{key} must be positive int, got {value!r}")
            elif key == "musicbrainz_release_group":
                if not isinstance(value, str) or not value:
                    errors.append(f"{slug}: extras.musicbrainz_release_group must be non-empty string")
            elif key == "cover_url":
                p = urllib.parse.urlparse(value) if isinstance(value, str) else None
                if not p or not p.scheme or not p.netloc:
                    errors.append(f"{slug}: extras.cover_url must be absolute URL, got {value!r}")
            elif key == "cover_file":
                if not isinstance(value, str) or "/" in value or ".." in value or not value:
                    errors.append(f"{slug}: extras.cover_file must be relative filename, got {value!r}")
    return errors, []


def check_cache_coverage(items: Iterable[dict], *, covers_dir: Path) -> list[str]:
    warnings: list[str] = []
    for it in items:
        extras = it.get("extras") or {}
        slug = it.get("slug", "<unknown>")
        if "cover_file" in extras and extras["cover_file"]:
            target = covers_dir / extras["cover_file"]
        elif any(k in extras for k in ("cover_url", "isbn", "musicbrainz_release_group", "igdb_id", "tmdb_id")):
            target = covers_dir / f"{slug}.jpg"
        else:
            continue
        if not target.exists():
            try:
                display = target.relative_to(REPO_ROOT)
            except ValueError:
                display = target
            warnings.append(f"{slug}: expected cover at {display} — run tools/fetch_library_covers.py")
    return warnings


def check_audit_consistency(audit: dict, *, covers_dir: Path) -> list[str]:
    warnings: list[str] = []
    for slug, entry in audit.items():
        candidate = covers_dir / f"{slug}.jpg"
        if not candidate.exists():
            warnings.append(f"{slug}: audit entry has no cache file at {candidate.relative_to(REPO_ROOT) if candidate.is_relative_to(REPO_ROOT) else candidate}")
            continue
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != entry.get("sha256"):
            warnings.append(f"{slug}: sha256 mismatch — cache differs from audit log")
    return warnings


def check_freshness(audit: dict, *, stale_days: int, now_iso: str | None = None) -> list[str]:
    now = datetime.datetime.fromisoformat(now_iso.replace("Z", "+00:00")) if now_iso \
          else datetime.datetime.now(datetime.timezone.utc)
    warnings: list[str] = []
    for slug, entry in audit.items():
        fetched = datetime.datetime.fromisoformat(entry["fetched_at"].replace("Z", "+00:00"))
        if (now - fetched).days > stale_days:
            warnings.append(f"{slug}: audit entry is stale ({(now - fetched).days} days old)")
    return warnings


def load_audit_log() -> dict:
    if AUDIT_LOG.exists():
        return json.loads(AUDIT_LOG.read_text())
    return {}


def load_all_items() -> list[dict]:
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from fetch_library_covers import load_leaf  # noqa: E402
    out = []
    for leaf in LEAVES:
        out.extend(load_leaf(leaf))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale-days", type=int, default=365)
    args = ap.parse_args(argv)
    items = load_all_items()
    audit = load_audit_log()
    errs, _ = check_schema(items)
    warns = []
    warns += check_cache_coverage(items, covers_dir=COVERS_DIR)
    warns += check_audit_consistency(audit, covers_dir=COVERS_DIR)
    warns += check_freshness(audit, stale_days=args.stale_days)
    for e in errs:
        print(f"ERROR: {e}", file=sys.stderr)
    for w in warns:
        print(f"WARN:  {w}", file=sys.stderr)
    if errs:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
