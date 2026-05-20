#!/usr/bin/env python3
"""Streams fixture frontmatter + data-yaml shape linter.

Walks `content/streams/<slug>/index.md` and validates per-stream
frontmatter against spec 2026-05-13-streams-section-design.md §4
+ §9. Also validates the three data/streams-*.yaml files (shape only;
content is Action-authored or user-seeded).

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

# --- contract ---

REQUIRED = {"title", "date", "platforms", "category", "archive_status", "draft"}
OPTIONAL = {
    "duration", "vod_url", "twitch_archive_url", "archive_url",
    "tags", "summary",
    "related_essays", "related_garden", "related_research", "related_works",
}
FIELDS = REQUIRED | OPTIONAL

PLATFORM_VALUES = {"twitch", "youtube"}
CATEGORY_VALUES = {"game-dev", "research", "coding", "creative"}
ARCHIVE_STATUS_VALUES = {"live", "archived", "removed", "private"}


def lint_file(md: Path) -> list[str]:
    errs: list[str] = []
    if not md.exists():
        return [f"{md}: file does not exist"]
    text = md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md}: no frontmatter"]

    for f in sorted(REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    # platforms: must be a list, each value in PLATFORM_VALUES
    platforms = fm.get("platforms")
    if platforms is not None:
        if not isinstance(platforms, list):
            errs.append(f"{md}: platforms must be a list")
        else:
            for i, p in enumerate(platforms):
                if str(p) not in PLATFORM_VALUES:
                    errs.append(f"{md}: platforms[{i}]='{p}' not in {sorted(PLATFORM_VALUES)}")

    cat = fm.get("category")
    if cat is not None and cat not in CATEGORY_VALUES:
        errs.append(f"{md}: category='{cat}' not in {sorted(CATEGORY_VALUES)}")

    arc = fm.get("archive_status")
    if arc is not None and arc not in ARCHIVE_STATUS_VALUES:
        errs.append(f"{md}: archive_status='{arc}' not in {sorted(ARCHIVE_STATUS_VALUES)}")

    # cross-validation: archived requires non-empty vod_url
    if arc == "archived":
        vod = fm.get("vod_url") or ""
        if not str(vod).strip():
            errs.append(f"{md}: archive_status=archived requires non-empty vod_url")

    # Related-* must be lists of strings when present
    for rel_field in ("related_essays", "related_garden", "related_research", "related_works"):
        v = fm.get(rel_field)
        if v is not None and not isinstance(v, list):
            errs.append(f"{md}: {rel_field} must be a list")

    # tags must be a list of strings when present
    tags = fm.get("tags")
    if tags is not None and not isinstance(tags, list):
        errs.append(f"{md}: tags must be a list")

    return errs


def _validate_data_yaml(repo_root: Path) -> list[str]:
    """Shape-check the three data/streams-*.yaml files (when present)."""
    errs: list[str] = []
    data = repo_root / "data"
    if not data.exists():
        return errs

    live = data / "streams-live.yaml"
    if live.exists():
        text = live.read_text()
        # Naive top-key presence check — stdlib only, no YAML parser.
        if "live:" not in text:
            errs.append(f"data/streams-live.yaml: missing top-level 'live:' key")
        else:
            for sub in ("twitch:", "youtube:"):
                if sub not in text:
                    errs.append(f"data/streams-live.yaml: missing 'live.{sub.rstrip(':')}' block")
            if "is_live:" not in text:
                errs.append(f"data/streams-live.yaml: missing 'is_live' key under live.<platform>")

    sched = data / "streams-schedule.yaml"
    if sched.exists():
        if "upcoming:" not in sched.read_text():
            errs.append(f"data/streams-schedule.yaml: missing 'upcoming:' top-level key")

    cache = data / "streams-twitch-cache.yaml"
    if cache.exists():
        if "upcoming:" not in cache.read_text():
            errs.append(f"data/streams-twitch-cache.yaml: missing 'upcoming:' top-level key")

    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    streams = repo_root / "content" / "streams"
    if streams.exists():
        for child in sorted(streams.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            if not md.exists():
                continue
            all_errs.extend(lint_file(md))
    all_errs.extend(_validate_data_yaml(repo_root))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_streams_fixtures: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
