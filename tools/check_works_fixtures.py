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
from check_fixtures import (  # noqa: E402
    FRONTMATTER_RE,
    _parse_block_item,
    parse_frontmatter,
    parse_scalar,
)

# --- contracts ---

GAME_REQUIRED = {"title", "date", "lastmod", "draft", "status", "kind", "tagline", "year"}
GAME_OPTIONAL = {
    "tags", "summary", "hero", "embed_url", "source_url", "itch_url",
    "collaborators", "tech_stack", "length", "screenshots",
    "research_questions", "related_essays", "related_notes",
}
GAME_FIELDS = GAME_REQUIRED | GAME_OPTIONAL
GAME_STATUSES = {"playable", "in-progress", "archived"}
GAME_KINDS = {"full-release", "jam", "research-prototype", "experiment"}

MUSIC_REQUIRED = {"title", "date", "lastmod", "draft", "format", "year"}
MUSIC_OPTIONAL = {
    "tags", "summary", "tagline", "cover", "duration",
    "tracks", "platform_embed", "audio_url", "lyrics_poem",
    "related_works", "related_essays", "made_with", "collaborators",
}
MUSIC_FIELDS = MUSIC_REQUIRED | MUSIC_OPTIONAL
MUSIC_FORMATS = {"album", "track", "experiment", "live"}
PLATFORM_KINDS = {"bandcamp", "soundcloud", "youtube"}

POEM_REQUIRED = {"title", "date", "lastmod", "draft", "lines"}
POEM_OPTIONAL = {"tags", "collection", "set_to_music", "summary"}
POEM_FIELDS = POEM_REQUIRED | POEM_OPTIONAL


def _parse_works_fields(text: str) -> dict[str, object] | None:
    """Parse frontmatter AND scan the document body for top-level key: value lines.

    Works fixtures sometimes have extra fields appended after the closing '---' for
    test-fixture convenience; this helper merges both regions.  Frontmatter fields
    take precedence.  Inline-dict string values ('{ k: v }') are coerced to dicts.
    """
    fm = parse_frontmatter(text)
    if fm is None:
        return None

    # Coerce any top-level values that are inline-dict strings
    for key, val in list(fm.items()):
        if isinstance(val, str) and val.startswith("{") and val.endswith("}"):
            fm[key] = _parse_block_item(val)

    # Also scan the body for top-level key: value lines
    m = FRONTMATTER_RE.match(text)
    if m:
        body = text[m.end():]
        lines = body.splitlines()
        i = 0
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue
            if raw.startswith((" ", "\t")) or ":" not in stripped:
                i += 1
                continue
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if key in fm:  # frontmatter wins
                i += 1
                continue
            if value != "":
                parsed = parse_scalar(value)
                if isinstance(parsed, str) and parsed.startswith("{") and parsed.endswith("}"):
                    parsed = _parse_block_item(parsed)
                fm[key] = parsed
                i += 1
                continue
            # Empty value — look for an indented block sequence
            items: list[object] = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                nxt_stripped = nxt.strip()
                if not nxt_stripped:
                    j += 1
                    continue
                if nxt.startswith((" ", "\t")) and nxt_stripped.startswith("-"):
                    item_text = nxt_stripped[1:].strip()
                    items.append(_parse_block_item(item_text))
                    j += 1
                    continue
                break
            if items:
                fm[key] = items
                i = j
            else:
                fm[key] = ""
                i += 1
    return fm


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
    fm = _parse_works_fields(text)
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

    gkind = fm.get("kind")
    if gkind is not None and gkind not in GAME_KINDS:
        errs.append(f"{md}: kind='{gkind}' not in {sorted(GAME_KINDS)}")

    year = fm.get("year")
    if year is not None and not isinstance(year, int):
        errs.append(f"{md}: year must be an integer, got {type(year).__name__}")

    screenshots = fm.get("screenshots")
    if screenshots is not None and not isinstance(screenshots, list):
        errs.append(f"{md}: screenshots must be a list of strings")

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
