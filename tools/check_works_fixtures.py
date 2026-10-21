#!/usr/bin/env python3
"""Works fixture frontmatter linter.

Walks `content/works/{games,music,poetry}/<slug>/index.md`, validates
per-type contracts (see docs/superpowers/specs/2026-05-12-works-section-design.md).

Field sets, enums and types — including the shared tile_size / featured / hero
umbrella fields and the platform_embed sub-keys — come from the
`works/games`, `works/music` and `works/poetry` entries of data/sections.json
via sections.check_fields (spec 2026-10-20 §5.1). That file replaced
data/works-vocab.json as the contract this linter reads; the vocabulary file
itself stays until the elisp side switches over (dotfiles plan, spec §8 step
4). The structured `tracks` shape stays here.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402
import sections  # noqa: E402

SUB_SECTIONS = ("games", "music", "poetry")


def lint_file(md: Path, registry: dict | None = None) -> list[str]:
    """Return a list of error strings for a single fixture index.md.

    Sub-section is derived from the path: content/works/<sub>/<slug>/index.md.
    `registry` defaults to this tree's data/sections.json (fail-closed).
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

    if sub not in SUB_SECTIONS:
        return [f"{md}: unknown works sub-section '{sub}'"]

    errs = sections.check_fields(fm, f"works/{sub}", md, registry=registry)
    if sub == "music":
        errs.extend(_lint_tracks(md, fm))
    return errs


def _lint_tracks(md: Path, fm: dict[str, object]) -> list[str]:
    """`tracks` is a `structured` field: its inner shape stays code (spec §4)."""
    errs: list[str] = []
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
    return errs


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    works = repo_root / "content" / "works"
    if not works.exists():
        return 0, []
    # One fail-closed load for the whole walk, reported through the uniform
    # `(rc, errs)` seam rather than exiting the process from inside run().
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]
    for sub in SUB_SECTIONS:
        sub_dir = works / sub
        if not sub_dir.exists():
            continue
        for child in sorted(sub_dir.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            if not md.exists():
                continue
            all_errs.extend(lint_file(md, reg))
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
