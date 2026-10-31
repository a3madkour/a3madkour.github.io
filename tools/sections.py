#!/usr/bin/env python3
"""Section registry reader — the single field contract (spec 2026-10-20 §4/§5.1).

`data/sections.json` names every section and lists its fields: type,
required-ness, enum values, ref targets and the prompt hints the elisp
`a3-publish-mark` reads. The fixture linters call `check_fields` instead of
keeping their own REQUIRED / OPTIONAL / enum constants; their cross-field,
uniqueness, structured-shape and format-regex rules stay as code.

Fails closed: a missing or malformed registry raises `SectionsError`, never a
hard-coded fallback. Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date as Date
from pathlib import Path

SECTIONS_REL = Path("data") / "sections.json"
# The registry is a property of this code tree, not of the content tree a
# linter walks: the linters' run(repo_root) is pointed at temp repos by their
# tests and by tools/test_publish_integration.py, none of which carry a copy.
SITE_ROOT = Path(__file__).resolve().parent.parent

TYPES = frozenset({
    "text", "int", "bool", "date", "list", "enum",
    "ref", "refs", "object", "structured",
})
SECTION_KEYS = frozenset({"closed", "store", "fields", "variants"})
FIELD_KEYS = frozenset({
    "type", "required", "values", "to", "default", "from",
    "ask", "fill", "fields", "variants", "source",
})
STORES = frozenset({"frontmatter", "data"})
FILLS = frozenset({"today", "next-weight"})
# Where in the org buffer a `from: pipeline` field comes from, so
# `a3-publish-mark` can check it and prompt when it would come out empty.
SOURCES = frozenset({"title", "filetags", "drawer", "date"})
VARIANT_KEYS = frozenset({"on", "cases"})
CASE_KEYS = frozenset({"values", "fields"})

DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

NOUN = {
    "int": "an integer",
    "bool": "a boolean",
    "list": "a list",
    "refs": "a list",
    "text": "a string",
    "ref": "a string",
    "enum": "a string",
    "object": "a mapping",
    "date": "a YYYY-MM-DD date",
}

# Deterministic message order: by rule, then field, then list index.
RULE_MISSING, RULE_UNKNOWN, RULE_ENUM, RULE_TYPE = 0, 1, 2, 3


class SectionsError(Exception):
    """The registry is missing, malformed, or names an unknown section."""


# --- loading + validation ---------------------------------------------------

def load(repo_root: Path) -> dict:
    """Read and validate `<repo_root>/data/sections.json`. Fails closed."""
    path = Path(repo_root) / SECTIONS_REL
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SectionsError(f"sections: registry not found at {path}")
    except json.JSONDecodeError as e:
        raise SectionsError(f"sections: registry at {path} is not valid JSON: {e}")
    _validate(raw)
    return raw


def _fail(where: str, what: str) -> None:
    raise SectionsError(f"sections: {where}: {what}")


def _validate(raw: object) -> None:
    if not isinstance(raw, dict):
        _fail("<root>", "top level must be an object")
    if set(raw) != {"version", "sections"}:
        _fail("<root>", f"keys must be exactly ['sections', 'version'], got {sorted(raw)}")
    if raw["version"] != 1:
        _fail("<root>", f"unsupported version {raw['version']!r}")
    sections = raw["sections"]
    if not isinstance(sections, dict) or not sections:
        _fail("<root>", "'sections' must be a non-empty object")
    names = set(sections)
    for name, spec in sections.items():
        if not isinstance(spec, dict):
            _fail(name, "section spec must be an object")
        for k in sorted(set(spec) - SECTION_KEYS):
            _fail(name, f"unknown section key '{k}'")
        if "closed" in spec and not isinstance(spec["closed"], bool):
            _fail(name, "'closed' must be a boolean")
        if spec.get("store", "frontmatter") not in STORES:
            _fail(name, f"store '{spec['store']}' not in {sorted(STORES)}")
        if not isinstance(spec.get("fields"), dict):
            _fail(name, "'fields' must be an object")
        _validate_fields(name, spec["fields"], names, parent_fields=spec["fields"])
        if "variants" in spec:
            _validate_variants(name, spec["variants"], names,
                               base=spec["fields"], selector_fields=None)


def _validate_fields(where: str, fields: dict, names: set, parent_fields: dict) -> None:
    for fname, fs in fields.items():
        at = f"{where}.{fname}"
        if not isinstance(fs, dict):
            _fail(at, "field spec must be an object")
        for k in sorted(set(fs) - FIELD_KEYS):
            _fail(at, f"unknown spec key '{k}'")
        t = fs.get("type")
        if t not in TYPES:
            _fail(at, f"unknown type {t!r}")
        for flag in ("required", "ask"):
            if flag in fs and not isinstance(fs[flag], bool):
                _fail(at, f"'{flag}' must be a boolean")
        if "values" in fs and t != "enum":
            _fail(at, f"'values' on non-enum type '{t}'")
        if t == "enum":
            vals = fs.get("values")
            if (not isinstance(vals, list) or not vals
                    or not all(isinstance(v, str) for v in vals)):
                _fail(at, "enum needs a non-empty 'values' list of strings")
        if "to" in fs and t not in ("ref", "refs"):
            _fail(at, f"'to' on non-ref type '{t}'")
        if t in ("ref", "refs"):
            if fs.get("to") not in names:
                _fail(at, f"'to' names no section: {fs.get('to')!r}")
        if "default" in fs:
            if t == "enum":
                if fs["default"] not in fs["values"]:
                    _fail(at, f"default {fs['default']!r} not in values")
            elif t == "bool":
                if not isinstance(fs["default"], bool):
                    _fail(at, "bool default must be a boolean")
            else:
                _fail(at, f"'default' on type '{t}'")
        if "from" in fs and fs["from"] != "pipeline":
            _fail(at, f"'from' must be 'pipeline', got {fs['from']!r}")
        if "source" in fs:
            if fs["source"] not in SOURCES:
                _fail(at, f"source {fs['source']!r} not in {sorted(SOURCES)}")
            if fs.get("from") != "pipeline":
                _fail(at, "'source' needs 'from': 'pipeline'")
        if "fill" in fs and fs["fill"] not in FILLS:
            _fail(at, f"fill {fs['fill']!r} not in {sorted(FILLS)}")
        if "fields" in fs and t != "object":
            _fail(at, f"'fields' on non-object type '{t}'")
        if "variants" in fs and t != "object":
            _fail(at, f"'variants' on non-object type '{t}'")
        if t == "object":
            if not isinstance(fs.get("fields"), dict):
                _fail(at, "object needs a 'fields' object")
            _validate_fields(at, fs["fields"], names, parent_fields=fs["fields"])
            if "variants" in fs:
                _validate_variants(at, fs["variants"], names,
                                   base=fs["fields"], selector_fields=parent_fields)


def _validate_variants(where: str, variants: object, names: set,
                       base: dict, selector_fields: dict | None) -> None:
    """Section-level variants select on a field of the section itself (base or
    any case); object-level variants select on a field of the enclosing
    section (`selector_fields`)."""
    at = f"{where}.variants"
    if not isinstance(variants, dict) or set(variants) != VARIANT_KEYS:
        _fail(at, "must be an object with exactly 'on' and 'cases'")
    cases = variants["cases"]
    if not isinstance(cases, dict) or not cases:
        _fail(at, "'cases' must be a non-empty object")
    seen: dict = {}
    case_fields: set = set()
    for cname, case in cases.items():
        cat = f"{at}.{cname}"
        if not isinstance(case, dict):
            _fail(cat, "case must be an object")
        for k in sorted(set(case) - CASE_KEYS):
            _fail(cat, f"unknown case key '{k}'")
        vals = case.get("values")
        if (not isinstance(vals, list) or not vals
                or not all(v is None or isinstance(v, str) for v in vals)):
            _fail(cat, "'values' must be a non-empty list of strings or null")
        for v in vals:
            if v in seen:
                _fail(cat, f"value {v!r} already selects case '{seen[v]}'")
            seen[v] = cname
        cf = case.get("fields", {})
        if not isinstance(cf, dict):
            _fail(cat, "'fields' must be an object")
        for f in sorted(set(cf) & set(base)):
            _fail(cat, f"field '{f}' duplicates a base field")
        _validate_fields(cat, cf, names, parent_fields=cf)
        case_fields |= set(cf)
    on = variants["on"]
    if selector_fields is None:
        if on not in base and on not in case_fields:
            _fail(at, f"'on' names no field: {on!r}")
    elif on not in selector_fields:
        _fail(at, f"'on' names no field of the enclosing section: {on!r}")


# --- the process-wide registry ----------------------------------------------

_CACHE: dict = {}


def default_registry() -> dict:
    """The registry of this code tree, cached by mtime. Fails closed."""
    path = SITE_ROOT / SECTIONS_REL
    try:
        mtime = path.stat().st_mtime_ns
    except FileNotFoundError:
        mtime = None
    hit = _CACHE.get(path)
    if hit is not None and hit[0] == mtime and mtime is not None:
        return hit[1]
    reg = load(SITE_ROOT)
    _CACHE[path] = (mtime, reg)
    return reg


def section_spec(section_name: str, registry: dict | None = None) -> dict:
    reg = registry if registry is not None else default_registry()
    try:
        return reg["sections"][section_name]
    except KeyError:
        raise SectionsError(f"sections: unknown section '{section_name}'")


def section_names(registry: dict | None = None) -> list[str]:
    reg = registry if registry is not None else default_registry()
    return sorted(reg["sections"])


# --- variant selection --------------------------------------------------------

def _select(variants: dict, selector: dict) -> tuple[str | None, dict | None]:
    v = selector.get(variants["on"])
    key = None if v in (None, "") else v
    for cname, case in variants["cases"].items():
        if key in case["values"]:
            return cname, case
    return None, None


def case_of(fm: dict, section_name: str, registry: dict | None = None) -> str | None:
    """The section-level variant case `fm` selects, or None when its selector
    value matches no case. Raises SectionsError for a section without variants."""
    spec = section_spec(section_name, registry)
    if "variants" not in spec:
        raise SectionsError(f"sections: section '{section_name}' has no variants")
    return _select(spec["variants"], fm)[0]


# --- checking -----------------------------------------------------------------

def _type_ok(t: str, v: object) -> bool:
    if t in ("text", "ref"):
        return isinstance(v, str)
    if t == "int":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "bool":
        return isinstance(v, bool)
    if t == "date":
        # datetime is a subclass of date, so both pass.
        return isinstance(v, Date) or (isinstance(v, str) and bool(DATE_PREFIX_RE.match(v)))
    if t in ("list", "refs"):
        return isinstance(v, list)
    if t == "object":
        return isinstance(v, dict)
    raise AssertionError(t)


def _check_value(v: object, fs: dict, f: str, path: str,
                 selector: dict, out: list) -> None:
    t = fs["type"]
    # None is what the library parser yields for `null` and for an empty
    # value. On an optional field it means "no value"; a required field must
    # carry one, so it falls through and fails its type/enum check.
    if v is None and not fs.get("required"):
        return
    if t == "structured":
        return
    if t == "enum":
        if v not in fs["values"]:
            out.append((RULE_ENUM, f, -1,
                        f"{path}: {f}='{v}' not in {sorted(fs['values'])}"))
        return
    if not _type_ok(t, v):
        out.append((RULE_TYPE, f, -1, f"{path}: {f} must be {NOUN[t]}"))
        return
    if t in ("list", "refs"):
        for i, item in enumerate(v):
            if not isinstance(item, str):
                out.append((RULE_TYPE, f, i, f"{path}: {f}[{i}] must be a string"))
    elif t == "object":
        _check_level(v, fs["fields"], fs.get("variants"), True, selector,
                     f + ".", path, out, top=False)


def _check_level(values: dict, fields: dict, variants: dict | None, closed: bool,
                 selector: dict, prefix: str, path: str, out: list, top: bool) -> None:
    active = dict(fields)
    case_known = True
    if variants is not None:
        _, case = _select(variants, selector)
        if case is None:
            case_known = False
            # A section-level selector is the field's own check. An
            # object-level selector belongs to the enclosing section, whose
            # own enum check already reports a bad value; stay silent there.
            if top:
                on = variants["on"]
                allowed = sorted({x for c in variants["cases"].values()
                                  for x in c["values"] if x is not None})
                out.append((RULE_ENUM, on, -1,
                            f"{path}: {on}='{selector.get(on)}' not in {allowed}"))
        else:
            active.update(case.get("fields", {}))
    for f in sorted(active):
        if active[f].get("required") and f not in values:
            out.append((RULE_MISSING, prefix + f, -1,
                        f"{path}: missing required field '{prefix}{f}'"))
    # With no matching case the legal field set is unknown, so the closed-set
    # check is skipped rather than guessed.
    if closed and case_known:
        for f in sorted(set(values) - set(active)):
            out.append((RULE_UNKNOWN, prefix + f, -1,
                        f"{path}: unknown field '{prefix}{f}'"))
    for f in sorted(active):
        if f in values:
            _check_value(values[f], active[f], prefix + f, path, selector, out)


def check_fields(fm: dict, section_name: str, path: object,
                 registry: dict | None = None) -> list[str]:
    """Required, closed-set, enum, type and variant checks for one entry.

    `path` is the message prefix: a file path for frontmatter sections, a
    `<file>[<idx>]` item label for data-store sections.
    """
    spec = section_spec(section_name, registry)
    out: list = []
    _check_level(fm, spec["fields"], spec.get("variants"),
                 spec.get("closed", True), fm, "", str(path), out, top=True)
    out.sort(key=lambda t: (t[0], t[1], t[2]))
    return [t[3] for t in out]


def main() -> int:
    """Validate this tree's registry: `python3 tools/sections.py` (a CI step)."""
    try:
        reg = load(SITE_ROOT)
    except SectionsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"sections.json: {len(reg['sections'])} sections OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
