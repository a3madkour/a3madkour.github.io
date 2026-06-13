#!/usr/bin/env python3
"""LHCI URL generator.

Reads public/lhci-pages.json (Hugo-emitted page manifest) and
tools/lhci-overrides.json (group-keyed assertion thresholds).
Rewrites lighthouserc.{json,mobile.json} in place — replacing
collect.url with alphabetical-first picks per (kind, section, type)
group, and rebuilding assertMatrix (mobile only) from overrides.

Stdlib only.
Exits 0 on success, 1 on any error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def group_pages(manifest: list[dict]) -> dict[str, list[str]]:
    """Group manifest entries by (kind, section, type) tuple.
    Returns {group_key: sorted_unique_urls}.
    group_key = "<kind>:<section>:<type>"."""
    groups: dict[str, set[str]] = {}
    for entry in manifest:
        key = f"{entry['kind']}:{entry['section']}:{entry['type']}"
        groups.setdefault(key, set()).add(entry["url"])
    return {k: sorted(v) for k, v in groups.items()}


def pick_representative_urls(manifest: list[dict]) -> dict[str, str]:
    """Returns {group_key: first_url_alphabetically} per (kind, section, type)."""
    groups = group_pages(manifest)
    return {key: urls[0] for key, urls in groups.items() if urls}


CATEGORY_MAP = {
    "perf": "categories:performance",
    "accessibility": "categories:accessibility",
    "best-practices": "categories:best-practices",
    "seo": "categories:seo",
}


def render_assert_matrix(
    picks: dict[str, str],
    overrides: list[dict],
) -> list[dict]:
    """Build assertMatrix entries from group-keyed overrides.

    Each override has {group, perf?, accessibility?, best-practices?, seo?}.
    matchingUrlPattern is the regex-escaped picked URL + anchor.
    Raises ValueError if an override references an unknown group."""
    matrix: list[dict] = []
    for ov in overrides:
        group = ov["group"]
        if group not in picks:
            raise ValueError(
                f"override references unknown group '{group}'; "
                f"valid groups: {sorted(picks.keys())}"
            )
        url = picks[group]
        # re.escape on Python ≥3.13 escapes '-' even though it's only special
        # inside character classes.  LHCI patterns are plain prefix matches so
        # hyphens in URL slugs must remain literal.
        pattern = re.escape(url).replace(r"\-", "-") + "$"
        assertions: dict = {}
        for short_key, lhci_key in CATEGORY_MAP.items():
            if short_key in ov:
                assertions[lhci_key] = ["error", {"minScore": ov[short_key]}]
        matrix.append({
            "matchingUrlPattern": pattern,
            "assertions": assertions,
        })
    return matrix


def rewrite_lighthouserc(
    config_path: Path,
    picks: dict[str, str],
    overrides: list[dict],
    base_url: str = "http://localhost",
) -> None:
    """Load existing JSON config; replace collect.url + assertMatrix; write back.

    - collect.url := sorted list of base_url + each picked URL.
    - assertMatrix := render_assert_matrix(picks, overrides) when non-empty,
      else removed entirely.
    - All other fields (preset, numberOfRuns, base assertions, upload) preserved.
    - Output: 2-space JSON, trailing newline, sort_keys False.
    """
    config = json.loads(config_path.read_text(encoding="utf-8"))

    urls = sorted(f"{base_url}{path}" for path in picks.values())
    config["ci"]["collect"]["url"] = urls

    matrix = render_assert_matrix(picks, overrides)
    if matrix:
        config["ci"]["assert"]["assertMatrix"] = matrix
    else:
        config["ci"]["assert"].pop("assertMatrix", None)

    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def run(repo_root: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Programmatic entry. Returns (rc, errors).

    Steps:
    1. Load public/lhci-pages.json. Missing → error.
    2. Load tools/lhci-overrides.json. Missing → empty overrides (no error).
    3. group + pick representative URLs.
    4. For each lighthouserc config (desktop, mobile): rewrite in place
       unless dry_run=True; in that case print the resulting JSON.
    """
    errors: list[str] = []
    manifest_path = repo_root / "public" / "lhci-pages.json"
    if not manifest_path.exists():
        return (1, [f"manifest missing at {manifest_path} — run after `hugo --minify`"])

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest:
        return (1, [f"manifest is empty at {manifest_path}"])

    overrides_path = repo_root / "tools" / "lhci-overrides.json"
    overrides = {"desktop": [], "mobile": []}
    if overrides_path.exists():
        overrides = json.loads(overrides_path.read_text(encoding="utf-8"))

    picks = pick_representative_urls(manifest)

    configs = [
        (repo_root / "lighthouserc.json", overrides.get("desktop", [])),
        (repo_root / "lighthouserc.mobile.json", overrides.get("mobile", [])),
    ]
    for cfg_path, cfg_overrides in configs:
        if not cfg_path.exists():
            errors.append(f"lighthouserc missing at {cfg_path}")
            continue
        try:
            if dry_run:
                _preview_rewrite(cfg_path, picks, cfg_overrides)
            else:
                rewrite_lighthouserc(cfg_path, picks, cfg_overrides)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        return (1, errors)
    return (0, [])


def _preview_rewrite(cfg_path: Path, picks: dict[str, str], overrides: list[dict]) -> None:
    """Compute what rewrite_lighthouserc would write and print to stdout."""
    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    config["ci"]["collect"]["url"] = sorted(f"http://localhost{p}" for p in picks.values())
    matrix = render_assert_matrix(picks, overrides)
    if matrix:
        config["ci"]["assert"]["assertMatrix"] = matrix
    else:
        config["ci"]["assert"].pop("assertMatrix", None)
    print(f"--- {cfg_path.name} (dry-run) ---")
    print(json.dumps(config, indent=2, sort_keys=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate LHCI URL lists from Hugo manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files.")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root, dry_run=args.dry_run)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return rc
    print("gen_lhci_urls: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
