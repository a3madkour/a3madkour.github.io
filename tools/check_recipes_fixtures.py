#!/usr/bin/env python3
"""Recipe fixture frontmatter shape linter.

Walks content/recipes/<slug>/index.md and validates frontmatter against
spec 2026-07-06-recipe-slice-1-render-download-design.md. Stdlib only.
Exits 0 on all-pass, 1 on any violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402

REQUIRED = {"title", "date", "lastmod", "draft", "summary",
            "servings", "sources", "ingredients", "steps"}
OPTIONAL = {"tags", "cuisine", "category", "yield_unit",
            "prep_minutes", "cook_minutes", "total_minutes",
            "image", "video", "outputs"}
FIELDS = REQUIRED | OPTIONAL

TIMECODE_RE = re.compile(r"^\[(\d{1,2}):([0-5]\d)(?:\.\d{1,2})?\]")


# A YAML 1.1/1.2 plain scalar Hugo will read as a number. Deliberately narrower
# than float(): Python accepts "1_0", "inf", and "nan", none of which Hugo does.
_NUM_RE = re.compile(r"^-?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?$")

# Zero-padded integers are the repo's documented Hugo octal gotcha: `010` is
# parsed by Hugo as 8, and `08` is invalid octal so Hugo keeps it a string and
# the next arithmetic op aborts the build. parse_scalar() converts "010" -> 10,
# so the padding survives only in the raw frontmatter text.
_PADDED_TOP_RE = re.compile(
    r"^(servings|prep_minutes|cook_minutes|total_minutes):[ \t]*-?0\d", re.M)
_PADDED_QTY_RE = re.compile(r"qty:[ \t]*-?0\d")


def _absent(v) -> bool:
    """True when a value is missing, or is the literal string 'null'.

    parse_scalar() has no null handling, so an explicit `item: null` arrives as
    the *truthy* string 'null' and silently passes a `str(...).strip()` check.
    """
    return v is None or (isinstance(v, str) and v.strip() == "null")


def _is_num(v) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, str):
        return bool(_NUM_RE.match(v.strip()))
    return False


def lint_file(md: Path) -> list[str]:
    errs: list[str] = []
    raw = md.read_text()
    fm = parse_frontmatter(raw)
    if fm is None:
        return [f"{md}: no frontmatter"]

    for m in _PADDED_TOP_RE.finditer(raw):
        errs.append(f"{md}: {m.group(1)} is zero-padded — Hugo parses it as octal")
    if _PADDED_QTY_RE.search(raw):
        errs.append(f"{md}: an ingredient qty is zero-padded — Hugo parses it as octal")

    for f in sorted(REQUIRED - fm.keys()):
        errs.append(f"{md}: missing required field '{f}'")
    for f in sorted(fm.keys() - FIELDS):
        errs.append(f"{md}: unknown field '{f}'")

    sv = fm.get("servings")
    if sv is not None and not (_is_num(sv) and float(str(sv)) > 0):
        errs.append(f"{md}: servings must be a number > 0")

    for key in ("prep_minutes", "cook_minutes", "total_minutes"):
        v = fm.get(key)
        if v is not None and not (isinstance(v, int) and not isinstance(v, bool) and v >= 0):
            errs.append(f"{md}: {key} must be a non-negative integer")

    ings = fm.get("ingredients")
    if ings is not None:
        if not isinstance(ings, list) or not ings:
            errs.append(f"{md}: ingredients must be a non-empty list")
        else:
            for i, ing in enumerate(ings):
                if not isinstance(ing, dict):
                    errs.append(f"{md}: ingredients[{i}] must be a flow mapping {{...}}")
                    continue
                if _absent(ing.get("item")) or not str(ing.get("item", "")).strip():
                    errs.append(f"{md}: ingredients[{i}] missing 'item'")
                q = ing.get("qty")
                if not _absent(q) and not (_is_num(q) and float(str(q)) > 0):
                    errs.append(f"{md}: ingredients[{i}] qty must be a positive number or null")
                extra = set(ing.keys()) - {"qty", "unit", "item", "alt", "note", "group"}
                for k in sorted(extra):
                    errs.append(f"{md}: ingredients[{i}] unknown key '{k}'")

    srcs = fm.get("sources")
    if srcs is not None:
        if not isinstance(srcs, list) or not srcs:
            errs.append(f"{md}: sources must be a non-empty list")
        else:
            for i, s in enumerate(srcs):
                if not isinstance(s, dict):
                    errs.append(f"{md}: sources[{i}] must be a flow mapping {{...}}")
                    continue
                if _absent(s.get("name")) or not str(s.get("name", "")).strip():
                    errs.append(f"{md}: sources[{i}] missing 'name'")

    steps = fm.get("steps")
    if steps is not None:
        if not isinstance(steps, list) or not steps:
            errs.append(f"{md}: steps must be a non-empty list")
        else:
            for i, st in enumerate(steps):
                s = str(st)
                m = re.match(r"^\[[^\]]*\]", s)
                if m and not TIMECODE_RE.match(s):
                    errs.append(f"{md}: steps[{i}] leading [..] is not a valid [mm:ss] marker")
    return errs


def run(repo_root: Path) -> tuple[int, list[str]]:
    all_errs: list[str] = []
    root = repo_root / "content" / "recipes"
    if root.exists():
        for child in sorted(root.iterdir()):
            md = child / "index.md"
            if child.is_dir() and md.exists():
                all_errs.extend(lint_file(md))
    return (1 if all_errs else 0), all_errs


def main() -> int:
    rc, errs = run(Path(__file__).resolve().parent.parent)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_recipes_fixtures: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
