#!/usr/bin/env python3
"""Works fixture frontmatter linter.

Walks `content/works/{games,music,poetry}/<slug>/index.md`, validates
per-type contracts (see docs/superpowers/specs/2026-05-12-works-section-design.md).

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

# --- contracts ---

UMBRELLA_OPTIONAL = {"tile_size", "featured", "hero"}
TILE_SIZES = {"small", "medium", "large"}

GAME_REQUIRED = {"title", "date", "lastmod", "draft", "status", "game_kind", "tagline", "year"}
GAME_OPTIONAL = {
    "tags", "summary", "hero", "embed_url", "source_url", "itch_url",
    "collaborators", "tech_stack", "length", "screenshots",
    "research_questions", "related_essays", "related_notes",
} | UMBRELLA_OPTIONAL
GAME_FIELDS = GAME_REQUIRED | GAME_OPTIONAL
GAME_STATUSES = {"playable", "in-progress", "archived"}
GAME_KINDS = {"full-release", "jam", "research-prototype", "experiment"}

MUSIC_REQUIRED = {"title", "date", "lastmod", "draft", "format", "year"}
MUSIC_OPTIONAL = {
    "tags", "summary", "tagline", "cover", "duration",
    "tracks", "platform_embed", "audio_url", "lyrics_poem",
    "related_works", "related_essays", "made_with", "collaborators",
} | UMBRELLA_OPTIONAL
MUSIC_FIELDS = MUSIC_REQUIRED | MUSIC_OPTIONAL
MUSIC_FORMATS = {"album", "track", "experiment", "live"}
PLATFORM_KINDS = {"bandcamp", "soundcloud", "youtube"}

POEM_REQUIRED = {"title", "date", "lastmod", "draft", "lines"}
POEM_OPTIONAL = {"tags", "collection", "set_to_music", "summary", "audio_url"} | UMBRELLA_OPTIONAL
POEM_FIELDS = POEM_REQUIRED | POEM_OPTIONAL


def _validate_umbrella_fields(md: Path, fm: dict[str, object]) -> list[str]:
    """Validate optional Bento-grid fields (tile_size, featured, hero).

    Note: hero is polymorphic:
      - For games, it may be a string (image filename, legacy field) or a bool (Bento grid).
      - For music and poetry, it is a bool (Bento grid).
    """
    errs: list[str] = []
    ts = fm.get("tile_size")
    if ts is not None and ts not in TILE_SIZES:
        errs.append(f"{md}: tile_size='{ts}' not in {sorted(TILE_SIZES)}")

    featured = fm.get("featured")
    if featured is not None and not isinstance(featured, bool):
        errs.append(f"{md}: featured must be bool, got {type(featured).__name__}")

    return errs


def lint_file(md: Path) -> list[str]:
    """Return a list of error strings for a single fixture index.md.

    Sub-section is derived from the path: content/works/<sub>/<slug>/index.md.
    """
    parts = md.parts
    try:
        works_idx = parts.index("works")
        sub = parts[works_idx + 1]
    except (ValueError, IndexError):
        return [f"{md}: cannot determine sub-section from path"]

    if not md.exists():
        return [f"{md}: file does not exist"]

    text = md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md}: no frontmatter"]

    if sub == "games":
        return _lint_game(md, fm)
    if sub == "music":
        return _lint_music(md, fm)
    if sub == "poetry":
        return _lint_poem(md, fm)
    return [f"{md}: unknown works sub-section '{sub}'"]


def _lint_game(md: Path, fm: dict[str, object]) -> list[str]:
    errs: list[str] = []
    for f in sorted(GAME_REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - GAME_FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    status = fm.get("status")
    if status is not None and status not in GAME_STATUSES:
        errs.append(f"{md}: status='{status}' not in {sorted(GAME_STATUSES)}")

    gkind = fm.get("game_kind")
    if gkind is not None and gkind not in GAME_KINDS:
        errs.append(f"{md}: game_kind='{gkind}' not in {sorted(GAME_KINDS)}")

    year = fm.get("year")
    if year is not None and not isinstance(year, int):
        errs.append(f"{md}: year must be an integer, got {type(year).__name__}")

    screenshots = fm.get("screenshots")
    if screenshots is not None and not isinstance(screenshots, list):
        errs.append(f"{md}: screenshots must be a list of strings")

    # For games, hero is polymorphic (string filename or bool for Bento grid)
    # and is validated by _validate_umbrella_fields (bool only for featured/tile_size).
    errs.extend(_validate_umbrella_fields(md, fm))

    return errs


def _lint_music(md: Path, fm: dict[str, object]) -> list[str]:
    errs: list[str] = []
    for f in sorted(MUSIC_REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - MUSIC_FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    fmt = fm.get("format")
    if fmt is not None and fmt not in MUSIC_FORMATS:
        errs.append(f"{md}: format='{fmt}' not in {sorted(MUSIC_FORMATS)}")

    year = fm.get("year")
    if year is not None and not isinstance(year, int):
        errs.append(f"{md}: year must be an integer, got {type(year).__name__}")

    tracks = fm.get("tracks")
    if tracks is not None:
        if not isinstance(tracks, list):
            errs.append(f"{md}: tracks must be a list")
        else:
            for i, t in enumerate(tracks):
                if not isinstance(t, dict):
                    errs.append(f"{md}: tracks[{i}] must be a dict")
                    continue
                if "title" not in t or "duration" not in t:
                    errs.append(f"{md}: tracks[{i}] requires title + duration")

    pe = fm.get("platform_embed")
    if pe is not None:
        if not isinstance(pe, dict):
            errs.append(f"{md}: platform_embed must be a dict")
        else:
            kind = pe.get("kind")
            if kind is None:
                errs.append(f"{md}: platform_embed.kind missing")
            elif kind not in PLATFORM_KINDS:
                errs.append(f"{md}: platform_embed.kind='{kind}' not in {sorted(PLATFORM_KINDS)}")
            if "url" not in pe:
                errs.append(f"{md}: platform_embed.url missing")

    errs.extend(_validate_umbrella_fields(md, fm))

    # For music, hero must be bool (Bento grid directive, no image filename)
    hero = fm.get("hero")
    if hero is not None and not isinstance(hero, bool):
        errs.append(f"{md}: hero must be bool, got {type(hero).__name__}")

    return errs


def _lint_poem(md: Path, fm: dict[str, object]) -> list[str]:
    errs: list[str] = []
    for f in sorted(POEM_REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - POEM_FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    lines = fm.get("lines")
    if lines is not None and not isinstance(lines, int):
        errs.append(f"{md}: lines must be an integer, got {type(lines).__name__}")

    errs.extend(_validate_umbrella_fields(md, fm))

    # For poetry, hero must be bool (Bento grid directive)
    hero = fm.get("hero")
    if hero is not None and not isinstance(hero, bool):
        errs.append(f"{md}: hero must be bool, got {type(hero).__name__}")

    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    works = repo_root / "content" / "works"
    if not works.exists():
        return 0, []
    for sub in ("games", "music", "poetry"):
        sub_dir = works / sub
        if not sub_dir.exists():
            continue
        for child in sorted(sub_dir.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            if not md.exists():
                continue
            all_errs.extend(lint_file(md))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_works_fixtures: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
