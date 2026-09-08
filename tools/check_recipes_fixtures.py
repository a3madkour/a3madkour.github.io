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
from check_fixtures import (  # noqa: E402
    FRONTMATTER_RE,
    _split_top_commas,
    parse_frontmatter,
)

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
# so the padding survives only in the raw frontmatter text — but it must be read
# there *positionally*: scanned as a bare substring it also fires on body prose,
# on fenced YAML in the body, and on quoted strings that merely contain
# "qty: 08". Hence _padded_errors() below, which walks the frontmatter block
# only and tests the value slot of the keys it cares about.
_PADDED_VALUE_RE = re.compile(r"^-?0\d")
_PADDED_NUMERIC_KEYS = frozenset(
    {"servings", "prep_minutes", "cook_minutes", "total_minutes"})

# YAML's null resolution is exactly these four spellings plus the empty scalar
# (yaml.org/type/null.html; goYAML, which Hugo uses, matches). Deliberately a
# set and not a .lower() test: goYAML reads "nULL" as the string "nULL".
_NULL_SPELLINGS = frozenset({"~", "null", "Null", "NULL"})


def _absent(v) -> bool:
    """True when a value is missing, or is a YAML null spelling.

    parse_scalar() has no null handling, so an explicit `item: null` arrives as
    the *truthy* string 'null' and silently passes a `str(...).strip()` check.
    """
    return v is None or (isinstance(v, str) and v.strip() in _NULL_SPELLINGS)


def _frontmatter_text(raw: str) -> str:
    """The frontmatter block only, delimited exactly as check_fixtures does.

    Reuses that module's FRONTMATTER_RE (and its CRLF normalization) rather
    than re-deriving the delimiters, so the two cannot drift apart.
    """
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    m = FRONTMATTER_RE.match(text)
    return m.group(1) if m else ""


def _flow_has_padded_qty(inner: str) -> bool:
    """True when a flow mapping's `qty` *value* is zero-padded.

    Splits with check_fixtures._split_top_commas, which is quote- and
    brace-aware, so `note: "was qty: 08"` stays one piece keyed on `note`.
    """
    for piece in _split_top_commas(inner):
        key, sep, value = piece.partition(":")
        if sep and key.strip() == "qty" and _PADDED_VALUE_RE.match(value.strip()):
            return True
    return False


def _padded_errors(md: Path, raw: str) -> list[str]:
    """Zero-padding diagnostics, read from value positions in frontmatter."""
    errs: list[str] = []
    qty_padded = False
    for line in _frontmatter_text(raw).splitlines():
        top_level = bool(line) and not line[0].isspace()
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("-"):
            s = s[1:].strip()
        if s.startswith("{") and s.endswith("}"):
            qty_padded = qty_padded or _flow_has_padded_qty(s[1:-1])
            continue
        key, sep, value = s.partition(":")
        if not sep:
            continue
        key, value = key.strip(), value.strip()
        if value.startswith("{") and value.endswith("}"):
            qty_padded = qty_padded or _flow_has_padded_qty(value[1:-1])
            continue
        if (top_level and key in _PADDED_NUMERIC_KEYS
                and _PADDED_VALUE_RE.match(value)):
            errs.append(f"{md}: {key} is zero-padded — Hugo parses it as octal")
    if qty_padded:
        errs.append(f"{md}: an ingredient qty is zero-padded — Hugo parses it as octal")
    return errs


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

    errs.extend(_padded_errors(md, raw))

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
