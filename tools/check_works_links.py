#!/usr/bin/env python3
"""Works cross-reference linter.

Resolves every cross-reference field on content/works/* fixtures against
the live content tree:

  - music.lyrics_poem → content/works/poetry/<slug>/index.md (non-draft)
  - poetry.set_to_music → content/works/music/<slug>/index.md (non-draft)
  - Round-trip: music[M].lyrics_poem == P  ⟹  poetry[P].set_to_music == M
  - games.research_questions[*] → content/research/questions/<slug>/index.md
  - games.related_essays[*]     → content/essays/<slug>/index.md
  - games.related_notes[*]      → content/garden/<slug>/index.md
  - music.related_essays[*]     → content/essays/<slug>/index.md
  - music.related_works[*]      → content/works/<sub>/<slug>/index.md

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


PATH_STRIP_RE = re.compile(r"^/+|/+$")


def _resolve_to_index(content_root: Path, rel_url: str) -> Path:
    """Map a Hugo-style URL like '/essays/foo/' to a filesystem index.md path."""
    stripped = PATH_STRIP_RE.sub("", rel_url)
    return content_root / stripped / "index.md"


def _is_draft(md: Path) -> bool:
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return False
    return bool(fm.get("draft"))


def _load_fm(md: Path) -> dict[str, object] | None:
    if not md.exists():
        return None
    return parse_frontmatter(md.read_text())


def lint_cross_refs(content_root: Path) -> list[str]:
    errs: list[str] = []

    music_dir = content_root / "works" / "music"
    poetry_dir = content_root / "works" / "poetry"
    games_dir = content_root / "works" / "games"

    music_fms: dict[str, dict[str, object]] = {}
    if music_dir.exists():
        for child in sorted(music_dir.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            fm = _load_fm(md)
            if fm is not None:
                music_fms[child.name] = fm

    poetry_fms: dict[str, dict[str, object]] = {}
    if poetry_dir.exists():
        for child in sorted(poetry_dir.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            fm = _load_fm(md)
            if fm is not None:
                poetry_fms[child.name] = fm

    games_fms: dict[str, dict[str, object]] = {}
    if games_dir.exists():
        for child in sorted(games_dir.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            fm = _load_fm(md)
            if fm is not None:
                games_fms[child.name] = fm

    # music.lyrics_poem resolution + round-trip
    for slug, fm in music_fms.items():
        target = fm.get("lyrics_poem")
        if target is None:
            continue
        target_str = str(target)
        if target_str not in poetry_fms:
            errs.append(f"works/music/{slug}: lyrics_poem='{target_str}' does not resolve to an existing poem")
            continue
        if poetry_fms[target_str].get("draft"):
            errs.append(f"works/music/{slug}: lyrics_poem='{target_str}' targets a draft poem")
            continue
        back = poetry_fms[target_str].get("set_to_music")
        if str(back) != slug:
            errs.append(
                f"works/music/{slug}: asymmetric round-trip — "
                f"music.lyrics_poem='{target_str}' but poetry/{target_str}.set_to_music='{back}'"
            )

    # poetry.set_to_music resolution
    for slug, fm in poetry_fms.items():
        target = fm.get("set_to_music")
        if target is None:
            continue
        target_str = str(target)
        if target_str not in music_fms:
            errs.append(f"works/poetry/{slug}: set_to_music='{target_str}' does not resolve to an existing music piece")
            continue
        if music_fms[target_str].get("draft"):
            errs.append(f"works/poetry/{slug}: set_to_music='{target_str}' targets a draft music piece")

    # games cross-section refs
    for slug, fm in games_fms.items():
        for field, label in [
            ("research_questions", "research_questions"),
            ("related_essays", "related_essays"),
            ("related_notes", "related_notes"),
        ]:
            refs = fm.get(field)
            if not refs:
                continue
            if not isinstance(refs, list):
                continue
            for ref in refs:
                _validate_url_ref(content_root, f"works/games/{slug}", label, str(ref), errs)

    # music cross-section refs
    for slug, fm in music_fms.items():
        for field, label in [
            ("related_essays", "related_essays"),
            ("related_works", "related_works"),
        ]:
            refs = fm.get(field)
            if not refs:
                continue
            if not isinstance(refs, list):
                continue
            for ref in refs:
                _validate_url_ref(content_root, f"works/music/{slug}", label, str(ref), errs)

    return errs


def _validate_url_ref(content_root: Path, source: str, field: str, ref: str, errs: list[str]) -> None:
    md = _resolve_to_index(content_root, ref)
    if not md.exists():
        errs.append(f"{source}: {field} ref '{ref}' does not resolve to an existing page")
        return
    if _is_draft(md):
        errs.append(f"{source}: {field} ref '{ref}' targets a draft page")


def run(repo_root: Path) -> tuple[int, list[str]]:
    content_root = repo_root / "content"
    if not content_root.exists():
        return 0, []
    errs = lint_cross_refs(content_root)
    return (1 if errs else 0), errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_works_links: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
