#!/usr/bin/env python3
"""Streams bidirectional cross-reference linter.

For each stream X in content/streams/:
  - X.related_essays:  [...] → each must exist (non-draft) under content/essays/
                              AND that page's source_stream must equal X's slug.
  - X.related_garden:  [...] → likewise under content/garden/.
  - X.related_research:[...] → likewise under content/research/{themes,questions}/.
  - X.related_works:   [...] → likewise under content/works/{games,music,poetry}/.

Inverse: for each page (essays/garden/research/works) with source_stream: X:
  - X must exist (non-draft) under content/streams/.
  - X.related_<sec> must include the page's slug (the directory name).

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402


SECTIONS = {
    "essays":   "related_essays",
    "garden":   "related_garden",
    "research": "related_research",
    "works":    "related_works",
}


def _load_fm(md: Path) -> dict | None:
    if not md.exists():
        return None
    return parse_frontmatter(md.read_text())


def _scan_dir_fms(d: Path) -> dict[str, dict]:
    """Return {slug: fm} for each child dir of d that has an index.md."""
    out: dict[str, dict] = {}
    if not d.exists():
        return out
    for child in sorted(d.iterdir()):
        if not child.is_dir():
            continue
        md = child / "index.md"
        fm = _load_fm(md)
        if fm is not None:
            out[child.name] = fm
    return out


def _is_draft(fm: dict) -> bool:
    v = fm.get("draft")
    return str(v).strip().lower() == "true"


def lint_cross_refs(content_root: Path) -> list[str]:
    errs: list[str] = []

    streams_fms = _scan_dir_fms(content_root / "streams")
    essays_fms  = _scan_dir_fms(content_root / "essays")
    garden_fms  = _scan_dir_fms(content_root / "garden")
    themes_fms  = _scan_dir_fms(content_root / "research" / "themes")
    qs_fms      = _scan_dir_fms(content_root / "research" / "questions")
    games_fms   = _scan_dir_fms(content_root / "works" / "games")
    music_fms   = _scan_dir_fms(content_root / "works" / "music")
    poetry_fms  = _scan_dir_fms(content_root / "works" / "poetry")

    # Per-section lookup: slug → (fm, source_dir_name)
    research_combined: dict[str, dict] = {}
    research_combined.update(themes_fms)
    research_combined.update(qs_fms)
    works_combined: dict[str, dict] = {}
    works_combined.update(games_fms)
    works_combined.update(music_fms)
    works_combined.update(poetry_fms)

    section_fms = {
        "essays":   essays_fms,
        "garden":   garden_fms,
        "research": research_combined,
        "works":    works_combined,
    }

    # Forward edges: streams → other sections
    for stream_slug, sfm in streams_fms.items():
        if _is_draft(sfm):
            continue
        for sec, field in SECTIONS.items():
            refs = sfm.get(field)
            if not refs:
                continue
            if not isinstance(refs, list):
                continue
            target_map = section_fms[sec]
            for ref in refs:
                ref_str = str(ref)
                target_fm = target_map.get(ref_str)
                if target_fm is None:
                    errs.append(
                        f"streams/{stream_slug}: {field} ref '{ref_str}' "
                        f"does not resolve to any page in /{sec}/"
                    )
                    continue
                if _is_draft(target_fm):
                    errs.append(
                        f"streams/{stream_slug}: {field} ref '{ref_str}' targets a draft page"
                    )
                    continue
                back = target_fm.get("source_stream")
                if str(back) != stream_slug:
                    errs.append(
                        f"streams/{stream_slug}: asymmetric — {sec}/{ref_str} "
                        f"has source_stream='{back}' but should be '{stream_slug}'"
                    )

    # Back edges: any-section.source_stream → streams
    for sec, fms in section_fms.items():
        field = SECTIONS[sec]
        for slug, fm in fms.items():
            back = fm.get("source_stream")
            if not back:
                continue
            back_str = str(back)
            sfm = streams_fms.get(back_str)
            if sfm is None:
                errs.append(
                    f"{sec}/{slug}: source_stream='{back_str}' "
                    f"does not resolve to any stream in /streams/"
                )
                continue
            if _is_draft(sfm):
                errs.append(
                    f"{sec}/{slug}: source_stream='{back_str}' targets a draft stream"
                )
                continue
            forward = sfm.get(field) or []
            if not isinstance(forward, list) or slug not in [str(x) for x in forward]:
                errs.append(
                    f"{sec}/{slug}: source_stream='{back_str}' "
                    f"but streams/{back_str}.{field} does not include '{slug}'"
                )

    return errs


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
        print("check_streams_links: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
