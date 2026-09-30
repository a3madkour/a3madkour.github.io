#!/usr/bin/env python3
"""Works fixture frontmatter linter.

Walks `content/works/{games,music,poetry}/<slug>/index.md`, validates
per-type contracts (see docs/superpowers/specs/2026-05-12-works-section-design.md).

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

# --- contracts ---

TILE_SIZES = {"small", "medium", "large"}

# Poetry's field sets stay here: poetry is not part of the org authoring
# surface this vocabulary single-sources (only games and music have an
# elisp-side mirror of their emitted-key contract). They still compose with
# the shared `umbrella_optional` list, which the vocabulary owns.
POEM_REQUIRED = {"title", "date", "lastmod", "draft", "lines"}
POEM_OPTIONAL = {"tags", "collection", "set_to_music", "summary", "audio_url", "source_stream"}

# --- shared vocabulary (single-sourced with the elisp author-side linter) ---
#
# Both the enum values AND the games/music emitted-field contract live in
# data/works-vocab.json, because both are mirrored on the elisp side:
# `a3madkour-works-lint.el' checks the enums and
# `a3madkour-publish-frontmatter.el' filters emitted frontmatter to the
# field sets. The field sets were transcribed into elisp (and again into
# the elisp tests) until 2026-09-29, and no test could observe both halves:
# adding an optional key here left the elisp stale and *silently filtered
# the new field out of every published page*. The spec's original argument
# for keeping field sets out ("a misspelled key fails loudly in CI
# regardless") stopped being true the moment the normalizer grew that
# filter.

VOCAB_REL = Path("data") / "works-vocab.json"
_VOCAB_ENUM_KEYS = {"game_statuses", "game_kinds", "music_formats", "platform_kinds"}
_VOCAB_FIELD_KEYS = {
    "umbrella_optional",
    "game_required", "game_optional",
    "music_required", "music_optional",
}
_VOCAB_KEYS = _VOCAB_ENUM_KEYS | _VOCAB_FIELD_KEYS


class VocabError(Exception):
    """The shared vocabulary is missing, malformed or incomplete."""


def load_vocab(repo_root: Path) -> dict[str, set[str]]:
    """Load the shared vocabulary. Fails closed: never returns defaults.

    A fallback here would silently restore the cross-language drift surface
    this file exists to remove. Raises `VocabError` rather than calling
    `sys.exit`, so `run()` keeps the uniform `(int, list[str])` seam every
    linter in this repo exposes and a future aggregator is not aborted
    mid-process.
    """
    path = repo_root / VOCAB_REL
    try:
        raw = json.loads(path.read_text())
    except FileNotFoundError:
        raise VocabError(f"check_works_fixtures: vocabulary not found at {path}")
    except json.JSONDecodeError as e:
        raise VocabError(
            f"check_works_fixtures: vocabulary at {path} is not valid JSON: {e}"
        )
    missing = _VOCAB_KEYS - raw.keys()
    if missing:
        raise VocabError(
            f"check_works_fixtures: vocabulary missing keys: {sorted(missing)}"
        )
    return {k: set(raw[k]) for k in _VOCAB_KEYS}


def game_fields(vocab: dict[str, set[str]]) -> tuple[set[str], set[str]]:
    """(required, every-legal-key) for games, composed from the vocabulary."""
    required = vocab["game_required"]
    return required, required | vocab["game_optional"] | vocab["umbrella_optional"]


def music_fields(vocab: dict[str, set[str]]) -> tuple[set[str], set[str]]:
    """(required, every-legal-key) for music, composed from the vocabulary."""
    required = vocab["music_required"]
    return required, required | vocab["music_optional"] | vocab["umbrella_optional"]


def poem_fields(vocab: dict[str, set[str]]) -> tuple[set[str], set[str]]:
    """(required, every-legal-key) for poetry."""
    return POEM_REQUIRED, POEM_REQUIRED | POEM_OPTIONAL | vocab["umbrella_optional"]


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


def lint_file(md: Path, vocab: dict[str, set[str]]) -> list[str]:
    """Return a list of error strings for a single fixture index.md.

    Sub-section is derived from the path: content/works/<sub>/<slug>/index.md.
    `vocab` is the loaded shared vocabulary (see load_vocab) — a required
    argument, deliberately with no default and never `None`: every
    sub-section, poetry included, now composes its field sets from it
    (`umbrella_optional`), so there is no branch that can legitimately
    skip it. A caller that omits it fails loudly rather than silently
    reading some other vocabulary source.
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
        return _lint_game(md, fm, vocab)
    if sub == "music":
        return _lint_music(md, fm, vocab)
    if sub == "poetry":
        return _lint_poem(md, fm, vocab)
    return [f"{md}: unknown works sub-section '{sub}'"]


def _lint_game(md: Path, fm: dict[str, object], vocab: dict[str, set[str]]) -> list[str]:
    errs: list[str] = []
    required, fields = game_fields(vocab)
    for f in sorted(required - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - fields):
        errs.append(f"{md}: unknown field '{f}'")

    status = fm.get("status")
    if status is not None and status not in vocab["game_statuses"]:
        errs.append(f"{md}: status='{status}' not in {sorted(vocab['game_statuses'])}")

    gkind = fm.get("game_kind")
    if gkind is not None and gkind not in vocab["game_kinds"]:
        errs.append(f"{md}: game_kind='{gkind}' not in {sorted(vocab['game_kinds'])}")

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


def _lint_music(md: Path, fm: dict[str, object], vocab: dict[str, set[str]]) -> list[str]:
    errs: list[str] = []
    required, fields = music_fields(vocab)
    for f in sorted(required - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - fields):
        errs.append(f"{md}: unknown field '{f}'")

    fmt = fm.get("format")
    if fmt is not None and fmt not in vocab["music_formats"]:
        errs.append(f"{md}: format='{fmt}' not in {sorted(vocab['music_formats'])}")

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
            elif kind not in vocab["platform_kinds"]:
                errs.append(f"{md}: platform_embed.kind='{kind}' not in {sorted(vocab['platform_kinds'])}")
            if "url" not in pe:
                errs.append(f"{md}: platform_embed.url missing")

    errs.extend(_validate_umbrella_fields(md, fm))

    # For music, hero must be bool (Bento grid directive, no image filename)
    hero = fm.get("hero")
    if hero is not None and not isinstance(hero, bool):
        errs.append(f"{md}: hero must be bool, got {type(hero).__name__}")

    return errs


def _lint_poem(md: Path, fm: dict[str, object], vocab: dict[str, set[str]]) -> list[str]:
    errs: list[str] = []
    required, fields = poem_fields(vocab)
    for f in sorted(required - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - fields):
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
    # One fail-closed load for the whole walk. Every sub-section needs it
    # now that `umbrella_optional` lives in the vocabulary, so there is no
    # lazy/poetry-only exemption left. A missing or malformed vocabulary is
    # reported through the uniform `(rc, errs)` seam rather than exiting the
    # process from inside `run()` — `main()` owns the exit.
    try:
        vocab = load_vocab(repo_root)
    except VocabError as e:
        return 1, [str(e)]
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
            all_errs.extend(lint_file(md, vocab))
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
