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
import sections  # noqa: E402

# --- contract ---
#
# Field sets, enums and types live in data/sections.json (spec 2026-10-20).
# What stays here is what the schema cannot say: the per-element enum on the
# `platforms` list (a `list` field takes no `values`) and the archived ⇒
# vod_url cross-field rule.

PLATFORM_VALUES = {"twitch", "youtube"}


def lint_file(md: Path, registry: dict | None = None) -> list[str]:
    if not md.exists():
        return [f"{md}: file does not exist"]
    text = md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md}: no frontmatter"]

    errs = sections.check_fields(fm, "streams", md, registry=registry)

    # platforms: each value in PLATFORM_VALUES (list-ness is the registry's)
    platforms = fm.get("platforms")
    if isinstance(platforms, list):
        for i, p in enumerate(platforms):
            if str(p) not in PLATFORM_VALUES:
                errs.append(f"{md}: platforms[{i}]='{p}' not in {sorted(PLATFORM_VALUES)}")

    # cross-validation: archived requires non-empty vod_url
    if fm.get("archive_status") == "archived":
        vod = fm.get("vod_url") or ""
        if not str(vod).strip():
            errs.append(f"{md}: archive_status=archived requires non-empty vod_url")

    return errs


# NOTE (R5.4 item 3): this parses data/streams-*.yaml (live/schedule/cache data
# files), NOT `---` frontmatter — a genuinely different shape, so it stays
# separate from check_fixtures.parse_frontmatter.
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


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]
    all_errs: list[str] = []
    streams = repo_root / "content" / "streams"
    if streams.exists():
        for child in sorted(streams.iterdir()):
            if not child.is_dir():
                continue
            md = child / "index.md"
            if not md.exists():
                continue
            all_errs.extend(lint_file(md, reg))
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
