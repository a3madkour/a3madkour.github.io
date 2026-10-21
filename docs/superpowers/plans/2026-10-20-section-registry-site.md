# Section Registry (site half) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `data/sections.json` (the single per-section field contract for all 14 sections), its stdlib reader `tools/sections.py` with tests, and migrate the 7 fixture linters onto `sections.check_fields`, one commit per linter, each through an equivalence gate.

**Architecture:** `data/sections.json` describes each section's fields (type, required, enum values, ref targets, prompt hints) plus garden/library variants. `tools/sections.py` loads and validates it fail-closed and exposes `check_fields(fm, section_name, path, registry=None)`. Each `tools/check_*_fixtures.py` deletes its field/enum constants and calls `check_fields`; cross-field, uniqueness, structured-shape and format-regex rules stay as code (spec §4).

**Tech Stack:** Python 3 stdlib only (`json`, `re`, `unittest`, `unittest.mock`), Hugo-site linter conventions (`run(...) -> (int, list[str])` + thin `main()`), GitHub Actions (`.github/workflows/hugo.yaml`) mirrored by `tools/ci-local.sh`.

**Spec:** `docs/superpowers/specs/2026-10-20-section-registry-design.md` — this plan covers §8 steps 1-2 (site repo only). The dotfiles half (§5.2, §5.3, §6, §8 steps 3-6) is a separate plan.

**Spec refinements made here (recorded deliberately):**
1. **Canonical messages.** §5.1 said `check_fields` emits "the existing linters' shapes". The 7 linters word the same rule 4 different ways (`'status' is required for media notes`, `forbidden field 'x' on theme`, `media_type='x' not allowed in reading.yaml (allowed: …)`, `featured must be bool, got str` …). `check_fields` emits one wording for every section instead: `{path}: missing required field '{f}'`, `{path}: unknown field '{f}'`, `{path}: {f}='{v}' not in {sorted values}`, `{path}: {f} must be {noun}`, `{path}: {f}[{i}] must be a string`. Existing `test_check_*` assertions on the old wording are updated in the same commit as their linter.
2. **The equivalence gate compares normalized `(file, field, rule)` sets from `run()`,** not raw stdout/stderr, so wording-only changes vanish and only real behaviour changes surface. Every remaining difference is listed in that task's commit message as an intended behaviour change (all of them are new strictness from type checks, plus two redundant-message removals).
3. **The registry is read from the code tree, not the walked tree.** `check_fields` takes an optional `registry=` (default `sections.default_registry()`, i.e. `tools/../data/sections.json`, mtime-cached). Every existing test points `run()` at a temp repo with no `data/sections.json`, and so does `tools/test_publish_integration.py`; reading from `repo_root` would break all of them. `load(repo_root)` keeps the spec's signature for tests and for the elisp-facing contract.
4. **`run()` gains an optional `registry=None` keyword** on all 7 linters (the positional `run(repo_root)` seam is unchanged), so tests can inject a mutated registry instead of writing files.
5. **"Every existing test passes unchanged"** (§7) holds except for wording assertions (refinement 1) and `test_check_works_fixtures.py`, whose vocabulary-file tests are rewritten against the registry because `load_vocab` is removed (§5.1 requires it).

**Not in this plan:** deleting `data/works-vocab.json`. `check_works_fixtures.py` stops reading it in Task 7, but the elisp (`a3madkour-works-vocab.el`) still reads it, and `tools/test_publish_integration.py` still copies it into a temp site root and pins the elisp fixture against it (`TestWorksVocabFixtureDrift`). It is deleted in the dotfiles plan, in the same commit as the elisp switch (spec §8 step 4), together with those two `test_publish_integration.py` references.

## Global Constraints

- Python tooling is stdlib-only; no new dependency, no `pip`, no Node.
- Registry path is exactly `data/sections.json`; top-level keys exactly `version` (= `1`) and `sections`.
- Section keys are exactly these 14, slash form: `essays`, `garden`, `research/themes`, `research/questions`, `works/games`, `works/music`, `works/poetry`, `library/reading`, `library/listening`, `library/playing`, `library/watching`, `streams`, `recipes`, `about`.
- `about` is `{"closed": false, "fields": {}}`; `essays` is `"closed": false`; every other section is closed (default `true`).
- Field types are exactly `text, int, bool, date, list, enum, ref, refs, object, structured`; spec keys exactly `type, required, values, to, default, from, ask, fill, fields, variants`.
- Type nouns are exactly: int → `an integer`; bool → `a boolean`; list/refs → `a list`; text/ref/enum → `a string`; object → `a mapping`; date → `a YYYY-MM-DD date`.
- `date` passes a `datetime.date`/`datetime.datetime` or a `str` matching `^\d{4}-\d{2}-\d{2}` (prefix match, `re.match`).
- `None` on an optional field is "no value" (skips type/enum); on a required field it fails the type/enum check. `""` is a value.
- Messages sort by rule (missing, unknown, enum, type), then field, then list index.
- Variant selection: `null` in a case's `values` matches an absent or `""` selector; an unmatched section-level selector emits `{on}='{v}' not in {sorted union}` and skips the closed-set check; an unmatched object-level selector is silent.
- Library item message prefix stays `{file_name}[{idx}]` (e.g. `reading.yaml[0]`), as today.
- Every linter keeps `run(repo_root, registry=None) -> tuple[int, list[str]]` and its existing `main()` output; a `SectionsError` from the registry load returns `(1, [str(e)])`, never `sys.exit`.
- Tests are invoked exactly as CI does: `python3 -m unittest tools/test_<name>.py -v` from the repo root.
- The equivalence-gate script lives in the session scratchpad and is never committed.
- `data/works-vocab.json` is not deleted or edited in this plan.
- Do not run `hugo --minify` while a `hugo server` is alive.
- Local Playwright runs serially: `npx playwright test --workers=1`.
- Every commit message ends with a blank line then `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

## Review Focus

- `None` from the library parser (`null`, or an empty value) on required vs optional fields: the old linters guarded with `is not None`, which let `year: null` through. Tests: `test_sections` `test_none_on_optional_field_is_no_value` / `test_none_on_required_field_fails` (Task 1); library `test_null_required_field_now_fails`, `test_null_optional_field_is_no_value`, `test_null_tags_still_fails` (Task 8).
- Empty-string values (`status:` with nothing after it parses to `""`) reaching enum/date checks that the old `if x and x not in …` guards skipped. Tests: `test_empty_string_enum_fails`, `test_date_rejects_malformed` (Task 1); research `test_empty_status_now_fails` (Task 2); garden `test_empty_started_now_fails` (Task 6).
- `bool` is a subclass of `int`, and int-looking YAML scalars are typed by `parse_scalar` (`2026` → int, `"1972"` → str). Tests: `test_bool_is_not_an_int`, `test_text_and_ref` (Task 1); recipes `test_non_integer_minutes_get_the_registry_message` (Task 4).
- Date shapes: date objects, ISO datetime strings (streams), quoted bare dates. The registry's prefix match must not loosen garden/library, which require bare dates. Tests: `test_date_accepts_date_datetime_and_iso_prefixed_string` (Task 1); streams `test_datetime_string_date_passes` (Task 3); garden `test_datetime_string_last_modified_still_fails` (Task 6); library `test_datetime_string_date_still_fails` (Task 8).
- Variant selector edges: a falsy `media_type` must select garden's concept case; an unknown value must not trigger a guessed closed-set check; library `extras` must stay silent when the item's own `media_type` is missing or bad. Tests: `test_variant_null_case_when_selector_absent_or_empty`, `test_unknown_selector_value_reports_union_and_skips_closed_set`, `test_object_variant_silent_when_enclosing_selector_is_bad` (Task 1); garden `test_empty_media_type_selects_concept`, `test_unknown_media_type_skips_flavor_checks` (Task 6); library `test_extras_silent_when_media_type_is_missing` (Task 8).

---

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `data/sections.json` | Create (Task 1) | The field contract for all 14 sections. |
| `tools/sections.py` | Create (Task 1) | `load` / `default_registry` / `check_fields` / `case_of` / `section_names` / `main`; fail-closed validation. |
| `tools/test_sections.py` | Create (Task 1) | Loader rejections, every `check_fields` rule, caching, the real file. |
| `.github/workflows/hugo.yaml` | Modify (Task 1) | Two steps before "Verify essay fixtures": validate registry + its tests. |
| `tools/ci-local.sh` | Modify (Task 1) | The same two commands before `python3 tools/check_fixtures.py`. |
| `tools/check_research_fixtures.py` + test | Modify (Task 2) | Themes/questions via `check_fields`; `outputs` shape + weight uniqueness stay. |
| `tools/check_streams_fixtures.py` + test | Modify (Task 3) | Via `check_fields`; `platforms` element enum + archived⇒vod_url stay. |
| `tools/check_recipes_fixtures.py` + test | Modify (Task 4) | Via `check_fields`; structured shapes, servings number, padding, minute sign stay. |
| `tools/check_fixtures.py` + test | Modify (Task 5) | Essays via `check_fields` (open section); series/hero/downloads/date/cite rules stay. |
| `tools/check_garden_fixtures.py` + test | Modify (Task 6) | Flavors as registry variants; bare-date, future-date, URL scheme, topic_map stay. |
| `tools/check_works_fixtures.py` + test | Modify (Task 7) | Drops `load_vocab`/works-vocab.json; `tracks` shape stays. |
| `tools/check_library_fixtures.py` + test | Modify (Task 8) | Per-item `check_fields` with `{file}[{idx}]` prefix; format/cross-field rules stay. |
| `CLAUDE.md` | Modify (Task 9) | Registry prose, step count. |
| `$SCRATCH/eqgate.py` | Scratch only (Tasks 2-8) | Throwaway equivalence gate; never committed. |

`$SCRATCH` below means the executing session's scratchpad directory.

---

### Task 1: Section registry — `data/sections.json`, `tools/sections.py`, tests, CI wiring

**Files:**
- Create: `data/sections.json`
- Create: `tools/sections.py`
- Test: `tools/test_sections.py` (create)
- Modify: `.github/workflows/hugo.yaml` (insert before line 76, `- name: Verify essay fixtures`)
- Modify: `tools/ci-local.sh` (insert before line 33, `python3 tools/check_fixtures.py`)

**Interfaces:**
- Consumes: `tools/test_helpers.py` → `TempRepo` (`.root: Path`, `.write(rel, text) -> Path`, `.cleanup()`).
- Produces:
  - `class SectionsError(Exception)`
  - `load(repo_root: Path) -> dict` — reads `<repo_root>/data/sections.json`, validates, raises `SectionsError`.
  - `default_registry() -> dict` — `load(SITE_ROOT)` cached by mtime; `SITE_ROOT = Path(__file__).resolve().parent.parent`.
  - `check_fields(fm: dict, section_name: str, path: object, registry: dict | None = None) -> list[str]`
  - `case_of(fm: dict, section_name: str, registry: dict | None = None) -> str | None`
  - `section_spec(section_name: str, registry: dict | None = None) -> dict`
  - `section_names(registry: dict | None = None) -> list[str]`
  - `DATE_PREFIX_RE: re.Pattern` (`^\d{4}-\d{2}-\d{2}`)
  - `main() -> int` — `python3 tools/sections.py` prints `sections.json: 14 sections OK`.

- [ ] **Step 1: Write the failing test**

Create `tools/test_sections.py`:

```python
"""Tests for sections.py — run with:
   python3 -m unittest tools/test_sections.py -v
"""
from __future__ import annotations

import copy
import json
import os
import sys
import unittest
from datetime import date as Date, datetime as DateTime
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections  # noqa: E402
from test_helpers import TempRepo  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_SECTIONS = {
    "essays", "garden", "research/themes", "research/questions",
    "works/games", "works/music", "works/poetry",
    "library/reading", "library/listening", "library/playing", "library/watching",
    "streams", "recipes", "about",
}

# A small registry that exercises every rule. Validated through the same
# loader as the real file (see _reg), so a fixture that the loader would
# reject cannot silently test check_fields against an impossible spec.
MINI = {
    "version": 1,
    "sections": {
        "closed": {
            "fields": {
                "title":  {"type": "text", "required": True},
                "count":  {"type": "int"},
                "flag":   {"type": "bool"},
                "when":   {"type": "date"},
                "tags":   {"type": "list"},
                "kind":   {"type": "enum", "values": ["a", "b"], "default": "a"},
                "peer":   {"type": "ref", "to": "closed"},
                "peers":  {"type": "refs", "to": "open"},
                "blob":   {"type": "structured", "required": True},
                "embed":  {"type": "object", "fields": {
                    "kind": {"type": "enum", "required": True, "values": ["x", "y"]},
                    "url":  {"type": "text"},
                }},
            }
        },
        "open": {"closed": False, "fields": {"title": {"type": "text", "required": True}}},
        "flavoured": {
            "fields": {"title": {"type": "text", "required": True}},
            "variants": {"on": "media_type", "cases": {
                "concept": {"values": [None], "fields": {"weight": {"type": "int"}}},
                "media": {"values": ["book", "film"], "fields": {
                    "media_type": {"type": "enum", "required": True, "values": ["book", "film"]},
                    "status": {"type": "enum", "required": True, "values": ["reading"]},
                }},
            }},
        },
        "shelf": {
            "store": "data",
            "fields": {
                "media_type": {"type": "enum", "required": True, "values": ["book", "album"]},
                "year": {"type": "int", "required": True},
                "note": {"type": "text"},
                "extras": {
                    "type": "object",
                    "fields": {"cover_file": {"type": "text"}},
                    "variants": {"on": "media_type", "cases": {
                        "book": {"values": ["book"], "fields": {"progress_pct": {"type": "int"}}},
                        "album": {"values": ["album"], "fields": {"mbid": {"type": "text"}}},
                    }},
                },
            },
        },
    },
}


def _reg(data: dict = MINI) -> dict:
    repo = TempRepo()
    try:
        repo.write("data/sections.json", json.dumps(data))
        return sections.load(repo.root)
    finally:
        repo.cleanup()


def _rejects(test: unittest.TestCase, mutate, fragment: str) -> None:
    data = copy.deepcopy(MINI)
    mutate(data)
    repo = TempRepo()
    try:
        repo.write("data/sections.json", json.dumps(data))
        with test.assertRaises(sections.SectionsError) as cm:
            sections.load(repo.root)
        test.assertIn(fragment, str(cm.exception))
    finally:
        repo.cleanup()


class LoaderTests(unittest.TestCase):
    def test_missing_file_fails_closed(self):
        repo = TempRepo()
        try:
            with self.assertRaises(sections.SectionsError) as cm:
                sections.load(repo.root)
            self.assertIn("registry not found at", str(cm.exception))
        finally:
            repo.cleanup()

    def test_malformed_json_fails_closed(self):
        repo = TempRepo()
        try:
            repo.write("data/sections.json", "{ not json")
            with self.assertRaises(sections.SectionsError) as cm:
                sections.load(repo.root)
            self.assertIn("is not valid JSON", str(cm.exception))
        finally:
            repo.cleanup()

    def test_mini_registry_loads(self):
        self.assertEqual(sorted(_reg()["sections"]), ["closed", "flavoured", "open", "shelf"])

    def test_rejects_wrong_top_level_keys(self):
        _rejects(self, lambda d: d.update(extra=1), "keys must be exactly")

    def test_rejects_unsupported_version(self):
        _rejects(self, lambda d: d.update(version=2), "unsupported version")

    def test_rejects_unknown_section_key(self):
        _rejects(self, lambda d: d["sections"]["open"].update(forbidden=[]),
                 "unknown section key 'forbidden'")

    def test_rejects_unknown_store(self):
        _rejects(self, lambda d: d["sections"]["open"].update(store="yaml"), "store 'yaml'")

    def test_rejects_unknown_type(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["count"].update(type="number"),
                 "unknown type 'number'")

    def test_rejects_unknown_spec_key(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["count"].update(min=0),
                 "unknown spec key 'min'")

    def test_rejects_values_on_non_enum(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["count"].update(values=["1"]),
                 "'values' on non-enum")

    def test_rejects_enum_without_values(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["kind"].pop("values"),
                 "enum needs a non-empty 'values'")

    def test_rejects_default_outside_values(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["kind"].update(default="z"),
                 "default 'z' not in values")

    def test_rejects_to_naming_no_section(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["peer"].update(to="nowhere"),
                 "'to' names no section")

    def test_rejects_ref_without_to(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["peers"].pop("to"),
                 "'to' names no section")

    def test_rejects_to_on_non_ref(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["title"].update(to="open"),
                 "'to' on non-ref")

    def test_rejects_bad_from(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["title"].update(**{"from": "author"}),
                 "'from' must be 'pipeline'")

    def test_rejects_bad_fill(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["when"].update(fill="tomorrow"),
                 "fill 'tomorrow'")

    def test_rejects_object_without_fields(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["embed"].pop("fields"),
                 "object needs a 'fields' object")

    def test_rejects_variants_on_naming_no_field(self):
        _rejects(self, lambda d: d["sections"]["flavoured"]["variants"].update(on="medium"),
                 "'on' names no field")

    def test_rejects_object_variants_on_naming_no_enclosing_field(self):
        _rejects(self,
                 lambda d: d["sections"]["shelf"]["fields"]["extras"]["variants"].update(on="kind"),
                 "'on' names no field of the enclosing section")

    def test_rejects_value_selecting_two_cases(self):
        _rejects(self,
                 lambda d: d["sections"]["flavoured"]["variants"]["cases"]["media"]["values"].append(None),
                 "already selects case")

    def test_rejects_case_field_duplicating_base(self):
        _rejects(self,
                 lambda d: d["sections"]["flavoured"]["variants"]["cases"]["concept"]["fields"].update(
                     title={"type": "text"}),
                 "duplicates a base field")

    def test_real_registry_loads_cleanly(self):
        reg = sections.load(REPO_ROOT)
        self.assertEqual(reg["version"], 1)

    def test_real_registry_names_exactly_the_site_sections(self):
        # The elisp registry's key set is pinned against this one (spec §7);
        # adding or dropping a section must be a deliberate edit here too.
        self.assertEqual(set(sections.load(REPO_ROOT)["sections"]), EXPECTED_SECTIONS)


class DefaultRegistryTests(unittest.TestCase):
    def test_cached_until_mtime_changes(self):
        repo = TempRepo()
        try:
            p = repo.write("data/sections.json", json.dumps(MINI))
            with mock.patch.object(sections, "SITE_ROOT", repo.root), \
                    mock.patch.object(sections, "_CACHE", {}):
                first = sections.default_registry()
                self.assertIs(first, sections.default_registry())
                data = copy.deepcopy(MINI)
                data["sections"]["open"]["fields"]["extra"] = {"type": "text"}
                p.write_text(json.dumps(data))
                st = p.stat()
                os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 10_000_000))
                second = sections.default_registry()
                self.assertIn("extra", second["sections"]["open"]["fields"])
        finally:
            repo.cleanup()

    def test_missing_default_registry_fails_closed(self):
        repo = TempRepo()
        try:
            with mock.patch.object(sections, "SITE_ROOT", repo.root), \
                    mock.patch.object(sections, "_CACHE", {}):
                with self.assertRaises(sections.SectionsError):
                    sections.default_registry()
        finally:
            repo.cleanup()

    def test_main_validates_this_trees_registry(self):
        with mock.patch("sys.stdout"):
            self.assertEqual(sections.main(), 0)
        repo = TempRepo()
        try:
            with mock.patch.object(sections, "SITE_ROOT", repo.root), \
                    mock.patch("sys.stderr"):
                self.assertEqual(sections.main(), 1)
        finally:
            repo.cleanup()

    def test_unknown_section_raises(self):
        with self.assertRaises(sections.SectionsError) as cm:
            sections.check_fields({}, "nowhere", "p", registry=_reg())
        self.assertIn("unknown section 'nowhere'", str(cm.exception))


VALID = {"title": "T", "blob": [1, 2]}


class CheckFieldsTests(unittest.TestCase):
    def setUp(self):
        self.reg = _reg()

    def check(self, fm, section="closed"):
        return sections.check_fields(fm, section, "p.md", registry=self.reg)

    def test_valid_entry_is_clean(self):
        self.assertEqual(self.check(VALID), [])

    # --- required ---
    def test_missing_required(self):
        self.assertEqual(self.check({"blob": 1}), ["p.md: missing required field 'title'"])

    def test_structured_checks_presence_only(self):
        self.assertEqual(self.check({"title": "T", "blob": "anything"}), [])
        self.assertEqual(self.check({"title": "T"}), ["p.md: missing required field 'blob'"])

    # --- closed set ---
    def test_unknown_field_on_closed_section(self):
        self.assertEqual(self.check({**VALID, "bogus": 1}), ["p.md: unknown field 'bogus'"])

    def test_open_section_accepts_unknown_field(self):
        self.assertEqual(self.check({"title": "T", "bogus": 1}, "open"), [])

    def test_open_section_still_checks_declared_types(self):
        self.assertEqual(self.check({"title": 3}, "open"), ["p.md: title must be a string"])

    # --- enum ---
    def test_enum_value_outside_set(self):
        self.assertEqual(self.check({**VALID, "kind": "c"}),
                         ["p.md: kind='c' not in ['a', 'b']"])

    def test_empty_string_enum_fails(self):
        # `kind:` with nothing after it parses to "" — a value, not absence.
        self.assertEqual(self.check({**VALID, "kind": ""}),
                         ["p.md: kind='' not in ['a', 'b']"])

    # --- types ---
    def test_int(self):
        self.assertEqual(self.check({**VALID, "count": "3"}), ["p.md: count must be an integer"])
        self.assertEqual(self.check({**VALID, "count": 3}), [])

    def test_bool_is_not_an_int(self):
        self.assertEqual(self.check({**VALID, "count": True}), ["p.md: count must be an integer"])

    def test_bool(self):
        self.assertEqual(self.check({**VALID, "flag": "yes"}), ["p.md: flag must be a boolean"])
        self.assertEqual(self.check({**VALID, "flag": False}), [])

    def test_date_accepts_date_datetime_and_iso_prefixed_string(self):
        for ok in (Date(2026, 1, 2), DateTime(2026, 1, 2, 3, 4), "2026-04-10T19:00:00-04:00"):
            with self.subTest(ok=ok):
                self.assertEqual(self.check({**VALID, "when": ok}), [])

    def test_date_rejects_malformed(self):
        for bad in ("2025-1-1", "not-a-date", "", 20260101):
            with self.subTest(bad=bad):
                self.assertEqual(self.check({**VALID, "when": bad}),
                                 ["p.md: when must be a YYYY-MM-DD date"])

    def test_text_and_ref(self):
        self.assertEqual(self.check({**VALID, "title": 2026}), ["p.md: title must be a string"])
        self.assertEqual(self.check({**VALID, "peer": ["x"]}), ["p.md: peer must be a string"])

    def test_list_and_refs_need_string_elements(self):
        self.assertEqual(self.check({**VALID, "tags": "a"}), ["p.md: tags must be a list"])
        self.assertEqual(self.check({**VALID, "peers": "x"}), ["p.md: peers must be a list"])
        self.assertEqual(self.check({**VALID, "tags": ["a", 2, Date(2026, 1, 1)]}),
                         ["p.md: tags[1] must be a string", "p.md: tags[2] must be a string"])

    def test_object_must_be_mapping(self):
        self.assertEqual(self.check({**VALID, "embed": "x"}), ["p.md: embed must be a mapping"])

    def test_none_on_optional_field_is_no_value(self):
        self.assertEqual(self.check({**VALID, "count": None, "kind": None}), [])

    def test_none_on_required_field_fails(self):
        self.assertEqual(self.check({"title": None, "blob": 1}), ["p.md: title must be a string"])

    # --- object sub-keys ---
    def test_object_sub_keys(self):
        self.assertEqual(
            self.check({**VALID, "embed": {"url": 5, "extra": 1}}),
            ["p.md: missing required field 'embed.kind'",
             "p.md: unknown field 'embed.extra'",
             "p.md: embed.url must be a string"])
        self.assertEqual(self.check({**VALID, "embed": {"kind": "z", "url": "u"}}),
                         ["p.md: embed.kind='z' not in ['x', 'y']"])

    # --- variants ---
    def test_variant_null_case_when_selector_absent_or_empty(self):
        self.assertEqual(self.check({"title": "T", "weight": 1}, "flavoured"), [])
        self.assertEqual(self.check({"title": "T", "media_type": ""}, "flavoured"),
                         ["p.md: unknown field 'media_type'"])

    def test_variant_case_adds_fields_and_requirements(self):
        self.assertEqual(self.check({"title": "T", "media_type": "book"}, "flavoured"),
                         ["p.md: missing required field 'status'"])
        self.assertEqual(self.check({"title": "T", "media_type": "film", "status": "reading"},
                                    "flavoured"), [])

    def test_variant_fields_are_case_local(self):
        self.assertEqual(self.check({"title": "T", "status": "reading"}, "flavoured"),
                         ["p.md: unknown field 'status'"])
        self.assertEqual(
            self.check({"title": "T", "media_type": "book", "status": "reading", "weight": 1},
                       "flavoured"),
            ["p.md: unknown field 'weight'"])

    def test_unknown_selector_value_reports_union_and_skips_closed_set(self):
        self.assertEqual(
            self.check({"title": "T", "media_type": "scroll", "anything": 1}, "flavoured"),
            ["p.md: media_type='scroll' not in ['book', 'film']"])

    def test_case_of(self):
        self.assertEqual(sections.case_of({}, "flavoured", self.reg), "concept")
        self.assertEqual(sections.case_of({"media_type": "film"}, "flavoured", self.reg), "media")
        self.assertIsNone(sections.case_of({"media_type": "scroll"}, "flavoured", self.reg))
        with self.assertRaises(sections.SectionsError):
            sections.case_of({}, "open", self.reg)

    # --- object variants selected by the enclosing entry ---
    def test_object_variant_sub_keys(self):
        base = {"media_type": "book", "year": 2020}
        self.assertEqual(self.check({**base, "extras": {"progress_pct": 5, "cover_file": "c"}},
                                    "shelf"), [])
        self.assertEqual(self.check({**base, "extras": {"mbid": "m"}}, "shelf"),
                         ["p.md: unknown field 'extras.mbid'"])
        self.assertEqual(self.check({**base, "extras": {"progress_pct": "5"}}, "shelf"),
                         ["p.md: extras.progress_pct must be an integer"])

    def test_object_variant_silent_when_enclosing_selector_is_bad(self):
        # The enclosing field's own enum check owns this failure.
        self.assertEqual(
            self.check({"media_type": "scroll", "year": 2020, "extras": {"anything": 1}}, "shelf"),
            ["p.md: media_type='scroll' not in ['album', 'book']"])
        self.assertEqual(self.check({"year": 2020, "extras": {"anything": 1}}, "shelf"),
                         ["p.md: missing required field 'media_type'"])

    # --- ordering ---
    def test_messages_sorted_by_rule_then_field(self):
        self.assertEqual(
            self.check({"blob": 1, "zeta": 1, "alpha": 1, "kind": "c", "count": "x"}),
            ["p.md: missing required field 'title'",
             "p.md: unknown field 'alpha'",
             "p.md: unknown field 'zeta'",
             "p.md: kind='c' not in ['a', 'b']",
             "p.md: count must be an integer"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m unittest tools/test_sections.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sections'` (the module does not exist yet).

- [ ] **Step 3: Write `tools/sections.py`**

```python
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
    "ask", "fill", "fields", "variants",
})
STORES = frozenset({"frontmatter", "data"})
FILLS = frozenset({"today", "next-weight"})
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
```

- [ ] **Step 4: Write `data/sections.json`**

Transcribed from the current linter constants and `data/works-vocab.json`; enum value lists are sorted. Type assignments follow how each linter and the fixtures under `content/` use the field (a census over all 63 current entries passes with zero violations). Notes on the non-obvious entries:
- `research/themes.author` / `research/questions.author` are `list` (fixtures carry `author: ["…"]`), not the spec example's `text`.
- `works/games.hero` is `structured` (it is a filename string or a Bento bool today); music/poetry `hero` is `bool`.
- `recipes.servings` is `structured`: it accepts an int or a decimal string (`1.5`), which no schema type expresses; the number rule stays in code.
- `garden` media/reference `media_type` lives in the cases, not the base, so a concept note carrying `media_type: ""` is still `unknown field 'media_type'`, as today. `weight` is concept-only, as today.
- Paths-valued link lists (`works/games.related_essays`, `research_questions`, `related_notes`; music `related_works`/`related_essays`; streams `related_works`, which spans three sections) are `list`, not `refs`: `to` names a single section of slugs.
- `platform_embed` is an `object`, which makes its sub-keys closed (new: an extra sub-key now fails — Task 7 records it).

```json
{
  "version": 1,
  "sections": {
    "essays": {
      "closed": false,
      "fields": {
        "title":          {"type": "text", "required": true, "from": "pipeline"},
        "date":           {"type": "date", "required": true, "from": "pipeline"},
        "lastmod":        {"type": "date", "required": true, "from": "pipeline"},
        "draft":          {"type": "bool", "required": true, "from": "pipeline"},
        "summary":        {"type": "text", "required": true},
        "tags":           {"type": "list", "required": true, "from": "pipeline"},
        "series":         {"type": "text", "required": true, "from": "pipeline"},
        "series_order":   {"type": "int",  "required": true, "from": "pipeline"},
        "toc":            {"type": "bool", "required": true, "from": "pipeline"},
        "has_sidenotes":  {"type": "bool", "required": true, "from": "pipeline"},
        "has_citations":  {"type": "bool", "required": true, "from": "pipeline"},
        "has_footnotes":  {"type": "bool", "required": true, "from": "pipeline"},
        "has_math":       {"type": "bool", "required": true, "from": "pipeline"},
        "has_widgets":    {"type": "bool", "required": true, "from": "pipeline"},
        "has_video_sync": {"type": "bool", "required": true, "from": "pipeline"},
        "tile_size":      {"type": "enum", "values": ["large", "medium", "small"]},
        "featured":       {"type": "bool"},
        "hero":           {"type": "text"},
        "block_numbering":{"type": "text"},
        "multi_export":   {"type": "bool", "from": "pipeline"},
        "downloads":      {"type": "structured", "from": "pipeline"},
        "source_stream":  {"type": "ref",  "to": "streams"}
      }
    },
    "garden": {
      "fields": {
        "title":         {"type": "text", "required": true, "from": "pipeline"},
        "draft":         {"type": "bool", "required": true, "from": "pipeline"},
        "last_modified": {"type": "date", "required": true, "from": "pipeline"},
        "growth_stage":  {"type": "enum", "required": true, "from": "pipeline",
                          "values": ["budding", "evergreen", "seedling"]},
        "tags":          {"type": "list", "from": "pipeline"},
        "summary":       {"type": "text"},
        "topic_map":     {"type": "refs", "to": "garden"},
        "roam_refs":     {"type": "text", "from": "pipeline"},
        "year":          {"type": "int"},
        "source_stream": {"type": "ref",  "to": "streams"}
      },
      "variants": {
        "on": "media_type",
        "cases": {
          "concept": {
            "values": [null],
            "fields": {
              "weight": {"type": "int"}
            }
          },
          "media": {
            "values": ["album", "book", "film", "game", "series", "track"],
            "fields": {
              "media_type":    {"type": "enum", "required": true,
                                "values": ["album", "book", "film", "game", "series", "track"]},
              "status":        {"type": "enum", "required": true,
                                "values": ["abandoned", "finished", "queued", "reading"]},
              "creator":       {"type": "text", "required": true},
              "original_url":  {"type": "text"},
              "started":       {"type": "date"},
              "finished":      {"type": "date"},
              "spoiler_level": {"type": "enum", "values": ["heavy", "light", "none"]}
            }
          },
          "reference": {
            "values": ["article", "paper", "talk", "video"],
            "fields": {
              "media_type":   {"type": "enum", "required": true,
                               "values": ["article", "paper", "talk", "video"]},
              "creator":      {"type": "text", "required": true},
              "original_url": {"type": "text"}
            }
          }
        }
      }
    },
    "research/themes": {
      "fields": {
        "title":            {"type": "text", "required": true, "from": "pipeline"},
        "last_modified":    {"type": "date", "required": true, "from": "pipeline"},
        "tags":             {"type": "list", "required": true, "from": "pipeline"},
        "draft":            {"type": "bool", "from": "pipeline"},
        "author":           {"type": "list", "from": "pipeline"},
        "description":      {"type": "text", "required": true},
        "summary":          {"type": "text"},
        "status":           {"type": "enum", "required": true,
                             "values": ["active", "answered", "dormant"], "default": "active"},
        "weight":           {"type": "int",  "required": true, "fill": "next-weight"},
        "garden_topic_ref": {"type": "ref",  "to": "garden"},
        "source_stream":    {"type": "ref",  "to": "streams"}
      }
    },
    "research/questions": {
      "fields": {
        "title":            {"type": "text", "required": true, "from": "pipeline"},
        "last_modified":    {"type": "date", "required": true, "from": "pipeline"},
        "tags":             {"type": "list", "from": "pipeline"},
        "draft":            {"type": "bool", "from": "pipeline"},
        "author":           {"type": "list", "from": "pipeline"},
        "description":      {"type": "text", "required": true},
        "status":           {"type": "enum", "required": true,
                             "values": ["active", "answered", "dormant"], "default": "active"},
        "theme":            {"type": "ref",  "required": true, "to": "research/themes"},
        "parent_question":  {"type": "ref",  "to": "research/questions"},
        "supporting_notes": {"type": "refs", "to": "garden", "ask": true},
        "related_essays":   {"type": "refs", "to": "essays"},
        "started":          {"type": "date", "fill": "today", "ask": true},
        "outputs":          {"type": "structured"},
        "weight":           {"type": "int"},
        "source_stream":    {"type": "ref",  "to": "streams"}
      }
    },
    "works/games": {
      "fields": {
        "title":              {"type": "text", "required": true, "from": "pipeline"},
        "date":               {"type": "date", "required": true, "from": "pipeline"},
        "lastmod":            {"type": "date", "required": true, "from": "pipeline"},
        "draft":              {"type": "bool", "required": true, "from": "pipeline"},
        "status":             {"type": "enum", "required": true,
                               "values": ["archived", "in-progress", "playable"]},
        "game_kind":          {"type": "enum", "required": true,
                               "values": ["experiment", "full-release", "jam", "research-prototype"]},
        "tagline":            {"type": "text", "required": true},
        "year":               {"type": "int",  "required": true},
        "tags":               {"type": "list", "from": "pipeline"},
        "summary":            {"type": "text"},
        "embed_url":          {"type": "text"},
        "source_url":         {"type": "text"},
        "itch_url":           {"type": "text"},
        "collaborators":      {"type": "list"},
        "tech_stack":         {"type": "list"},
        "length":             {"type": "text"},
        "screenshots":        {"type": "list"},
        "research_questions": {"type": "list"},
        "related_essays":     {"type": "list"},
        "related_notes":      {"type": "list"},
        "source_stream":      {"type": "ref",  "to": "streams"},
        "tile_size":          {"type": "enum", "values": ["large", "medium", "small"]},
        "featured":           {"type": "bool"},
        "hero":               {"type": "structured"}
      }
    },
    "works/music": {
      "fields": {
        "title":          {"type": "text", "required": true, "from": "pipeline"},
        "date":           {"type": "date", "required": true, "from": "pipeline"},
        "lastmod":        {"type": "date", "required": true, "from": "pipeline"},
        "draft":          {"type": "bool", "required": true, "from": "pipeline"},
        "format":         {"type": "enum", "required": true,
                           "values": ["album", "experiment", "live", "track"]},
        "year":           {"type": "int",  "required": true},
        "tags":           {"type": "list", "from": "pipeline"},
        "summary":        {"type": "text"},
        "tagline":        {"type": "text"},
        "cover":          {"type": "text"},
        "duration":       {"type": "text"},
        "tracks":         {"type": "structured"},
        "platform_embed": {"type": "object",
                           "fields": {
                             "kind": {"type": "enum", "required": true,
                                      "values": ["bandcamp", "soundcloud", "youtube"]},
                             "url":  {"type": "text", "required": true}
                           }},
        "audio_url":      {"type": "text"},
        "lyrics_poem":    {"type": "ref",  "to": "works/poetry"},
        "related_works":  {"type": "list"},
        "related_essays": {"type": "list"},
        "made_with":      {"type": "list"},
        "collaborators":  {"type": "list"},
        "source_stream":  {"type": "ref",  "to": "streams"},
        "tile_size":      {"type": "enum", "values": ["large", "medium", "small"]},
        "featured":       {"type": "bool"},
        "hero":           {"type": "bool"}
      }
    },
    "works/poetry": {
      "fields": {
        "title":         {"type": "text", "required": true, "from": "pipeline"},
        "date":          {"type": "date", "required": true, "from": "pipeline"},
        "lastmod":       {"type": "date", "required": true, "from": "pipeline"},
        "draft":         {"type": "bool", "required": true, "from": "pipeline"},
        "lines":         {"type": "int",  "required": true, "from": "pipeline"},
        "tags":          {"type": "list", "from": "pipeline"},
        "collection":    {"type": "text"},
        "set_to_music":  {"type": "ref",  "to": "works/music"},
        "summary":       {"type": "text"},
        "audio_url":     {"type": "text"},
        "source_stream": {"type": "ref",  "to": "streams"},
        "tile_size":     {"type": "enum", "values": ["large", "medium", "small"]},
        "featured":      {"type": "bool"},
        "hero":          {"type": "bool"}
      }
    },
    "library/reading": {
      "store": "data",
      "fields": {
        "slug":          {"type": "text", "required": true, "from": "pipeline"},
        "title":         {"type": "text", "required": true, "from": "pipeline"},
        "creator":       {"type": "text", "required": true},
        "year":          {"type": "int",  "required": true},
        "media_type":    {"type": "enum", "required": true, "values": ["book"]},
        "status":        {"type": "enum", "required": true,
                          "values": ["abandoned", "finished", "queued", "reading"]},
        "last_modified": {"type": "date", "required": true, "from": "pipeline"},
        "tags":          {"type": "list", "required": true, "from": "pipeline"},
        "started":       {"type": "date"},
        "finished":      {"type": "date"},
        "spoiler_level": {"type": "enum", "values": ["heavy", "light", "none"]},
        "cite_key":      {"type": "text"},
        "canonical_url": {"type": "text"},
        "note_slug":     {"type": "ref",  "to": "garden"},
        "preview":       {"type": "text"},
        "extras": {
          "type": "object",
          "fields": {
            "cover_file": {"type": "text"},
            "cover_url":  {"type": "text"}
          },
          "variants": {
            "on": "media_type",
            "cases": {
              "book": {
                "values": ["book"],
                "fields": {
                  "progress_pct":   {"type": "int"},
                  "progress_label": {"type": "text"},
                  "isbn":           {"type": "text"}
                }
              }
            }
          }
        }
      }
    },
    "library/listening": {
      "store": "data",
      "fields": {
        "slug":          {"type": "text", "required": true, "from": "pipeline"},
        "title":         {"type": "text", "required": true, "from": "pipeline"},
        "creator":       {"type": "text", "required": true},
        "year":          {"type": "int",  "required": true},
        "media_type":    {"type": "enum", "required": true, "values": ["album", "track"]},
        "status":        {"type": "enum", "required": true,
                          "values": ["dropped", "finished", "listening", "queued"]},
        "last_modified": {"type": "date", "required": true, "from": "pipeline"},
        "tags":          {"type": "list", "required": true, "from": "pipeline"},
        "started":       {"type": "date"},
        "finished":      {"type": "date"},
        "spoiler_level": {"type": "enum", "values": ["heavy", "light", "none"]},
        "cite_key":      {"type": "text"},
        "canonical_url": {"type": "text"},
        "note_slug":     {"type": "ref",  "to": "garden"},
        "preview":       {"type": "text"},
        "extras": {
          "type": "object",
          "fields": {
            "cover_file": {"type": "text"},
            "cover_url":  {"type": "text"}
          },
          "variants": {
            "on": "media_type",
            "cases": {
              "album": {
                "values": ["album"],
                "fields": {
                  "musicbrainz_release_group": {"type": "text"}
                }
              },
              "track": {
                "values": ["track"],
                "fields": {
                  "musicbrainz_release_group": {"type": "text"}
                }
              }
            }
          }
        }
      }
    },
    "library/playing": {
      "store": "data",
      "fields": {
        "slug":          {"type": "text", "required": true, "from": "pipeline"},
        "title":         {"type": "text", "required": true, "from": "pipeline"},
        "creator":       {"type": "text", "required": true},
        "year":          {"type": "int",  "required": true},
        "media_type":    {"type": "enum", "required": true, "values": ["game"]},
        "status":        {"type": "enum", "required": true,
                          "values": ["100pct", "dropped", "finished", "playing", "queued"]},
        "last_modified": {"type": "date", "required": true, "from": "pipeline"},
        "tags":          {"type": "list", "required": true, "from": "pipeline"},
        "started":       {"type": "date"},
        "finished":      {"type": "date"},
        "spoiler_level": {"type": "enum", "values": ["heavy", "light", "none"]},
        "cite_key":      {"type": "text"},
        "canonical_url": {"type": "text"},
        "note_slug":     {"type": "ref",  "to": "garden"},
        "preview":       {"type": "text"},
        "extras": {
          "type": "object",
          "fields": {
            "cover_file": {"type": "text"},
            "cover_url":  {"type": "text"}
          },
          "variants": {
            "on": "media_type",
            "cases": {
              "game": {
                "values": ["game"],
                "fields": {
                  "hours_played": {"type": "int"},
                  "platform":     {"type": "text"},
                  "igdb_id":      {"type": "int"}
                }
              }
            }
          }
        }
      }
    },
    "library/watching": {
      "store": "data",
      "fields": {
        "slug":          {"type": "text", "required": true, "from": "pipeline"},
        "title":         {"type": "text", "required": true, "from": "pipeline"},
        "creator":       {"type": "text", "required": true},
        "year":          {"type": "int",  "required": true},
        "media_type":    {"type": "enum", "required": true, "values": ["film", "series"]},
        "status":        {"type": "enum", "required": true,
                          "values": ["dropped", "finished", "queued", "watching"]},
        "last_modified": {"type": "date", "required": true, "from": "pipeline"},
        "tags":          {"type": "list", "required": true, "from": "pipeline"},
        "started":       {"type": "date"},
        "finished":      {"type": "date"},
        "spoiler_level": {"type": "enum", "values": ["heavy", "light", "none"]},
        "cite_key":      {"type": "text"},
        "canonical_url": {"type": "text"},
        "note_slug":     {"type": "ref",  "to": "garden"},
        "preview":       {"type": "text"},
        "extras": {
          "type": "object",
          "fields": {
            "cover_file": {"type": "text"},
            "cover_url":  {"type": "text"}
          },
          "variants": {
            "on": "media_type",
            "cases": {
              "film": {
                "values": ["film"],
                "fields": {
                  "runtime_min": {"type": "int"},
                  "tmdb_id":     {"type": "int"}
                }
              },
              "series": {
                "values": ["series"],
                "fields": {
                  "episode_count":   {"type": "int"},
                  "current_episode": {"type": "int"},
                  "current_season":  {"type": "int"},
                  "tmdb_id":         {"type": "int"}
                }
              }
            }
          }
        }
      }
    },
    "streams": {
      "fields": {
        "title":              {"type": "text", "required": true, "from": "pipeline"},
        "date":               {"type": "date", "required": true, "from": "pipeline"},
        "draft":              {"type": "bool", "required": true, "from": "pipeline"},
        "platforms":          {"type": "list", "required": true},
        "category":           {"type": "enum", "required": true,
                               "values": ["coding", "creative", "game-dev", "research"]},
        "archive_status":     {"type": "enum", "required": true,
                               "values": ["archived", "live", "private", "removed"]},
        "duration":           {"type": "text"},
        "vod_url":            {"type": "text"},
        "twitch_archive_url": {"type": "text"},
        "archive_url":        {"type": "text"},
        "tags":               {"type": "list", "from": "pipeline"},
        "summary":            {"type": "text"},
        "related_essays":     {"type": "refs", "to": "essays"},
        "related_garden":     {"type": "refs", "to": "garden"},
        "related_research":   {"type": "refs", "to": "research/questions"},
        "related_works":      {"type": "list"}
      }
    },
    "recipes": {
      "fields": {
        "title":         {"type": "text", "required": true, "from": "pipeline"},
        "date":          {"type": "date", "required": true, "from": "pipeline"},
        "lastmod":       {"type": "date", "required": true, "from": "pipeline"},
        "draft":         {"type": "bool", "required": true, "from": "pipeline"},
        "summary":       {"type": "text", "required": true},
        "servings":      {"type": "structured", "required": true, "from": "pipeline"},
        "sources":       {"type": "structured", "required": true, "from": "pipeline"},
        "ingredients":   {"type": "structured", "required": true, "from": "pipeline"},
        "steps":         {"type": "structured", "required": true, "from": "pipeline"},
        "tags":          {"type": "list", "from": "pipeline"},
        "cuisine":       {"type": "text", "from": "pipeline"},
        "category":      {"type": "text", "from": "pipeline"},
        "yield_unit":    {"type": "text", "from": "pipeline"},
        "prep_minutes":  {"type": "int",  "from": "pipeline"},
        "cook_minutes":  {"type": "int",  "from": "pipeline"},
        "total_minutes": {"type": "int",  "from": "pipeline"},
        "image":         {"type": "text", "from": "pipeline"},
        "video":         {"type": "text", "from": "pipeline"},
        "outputs":       {"type": "structured"}
      }
    },
    "about": {
      "closed": false,
      "fields": {}
    }
  }
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m unittest tools/test_sections.py -v`
Expected: PASS — `Ran 55 tests`, `OK`.

Run: `python3 tools/sections.py`
Expected: `sections.json: 14 sections OK`, exit 0.

- [ ] **Step 6: Mutation-check the guards**

Break each guard in turn, confirm `python3 -m unittest tools/test_sections.py` fails, then restore (the file is untracked, so keep a copy: `cp tools/sections.py "$SCRATCH/sections.py.bak"` first, `cp "$SCRATCH/sections.py.bak" tools/sections.py` after each). Each line below is one mutation (old → new); every one must make the suite FAIL:
- `return isinstance(v, int) and not isinstance(v, bool)` → `return isinstance(v, int)`
- `    if closed and case_known:` → `    if False:`
- `        if "values" in fs and t != "enum":` → `        if False:`
- `            if fs.get("to") not in names:` → `            if False:`
- `        if on not in base and on not in case_fields:` → `        if False:`
- `    if v is None and not fs.get("required"):` → `    if v is None:`
- `    key = None if v in (None, "") else v` → `    key = v`
- `            if top:` → `            if False:`
- `    if hit is not None and hit[0] == mtime and mtime is not None:` → `    if hit is not None:`
- `        raise SectionsError(f"sections: registry not found at {path}")` → `        return {"version": 1, "sections": {}}`
- `    out.sort(key=lambda t: (t[0], t[1], t[2]))` → `    pass`
- `            if not isinstance(item, str):` → `            if False:`
- `            if v in seen:` → `            if False:`
- `        for f in sorted(set(cf) & set(base)):` → `        for f in []:`

Restore the original and re-run: PASS.

- [ ] **Step 7: Wire into CI and ci-local**

In `.github/workflows/hugo.yaml`, insert immediately above `      - name: Verify essay fixtures` (line 76):

```yaml
      - name: Validate section registry
        run: python3 tools/sections.py
      - name: Run section registry unit tests
        run: python3 -m unittest tools/test_sections.py -v
```

In `tools/ci-local.sh`, insert immediately above `python3 tools/check_fixtures.py` (line 33), followed by a blank line:

```bash
python3 tools/sections.py
python3 -m unittest tools/test_sections.py -v 2>&1 | tail -3
```

Run: `grep -c '^\s*- name:' .github/workflows/hugo.yaml`
Expected: `105` (was 103).

- [ ] **Step 8: Confirm nothing else moved**

Run: `for t in fixtures research_fixtures streams_fixtures recipes_fixtures garden_fixtures works_fixtures library_fixtures; do python3 -m unittest tools/test_check_$t.py 2>&1 | tail -1; done`
Expected: `OK` seven times (no linter reads the registry yet).

- [ ] **Step 9: Commit**

```bash
git add data/sections.json tools/sections.py tools/test_sections.py .github/workflows/hugo.yaml tools/ci-local.sh
git commit -m "$(cat <<'MSG'
feat(tools): section registry — data/sections.json + sections.py reader

data/sections.json is the single field contract for all 14 sections
(type, required, enum values, ref targets, prompt hints, garden/library
variants), transcribed from the 7 fixture linters and works-vocab.json.
tools/sections.py loads it fail-closed and exposes check_fields(); no
linter reads it yet. CI validates the file and runs its tests before the
fixture linters. Spec 2026-10-20 §4/§5.1/§8 step 1.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
)"
```

### Task 2: Migrate `check_research_fixtures.py`

**Files:**
- Modify: `tools/check_research_fixtures.py` (full rewrite, lines 1-195)
- Test: `tools/test_check_research_fixtures.py` (modify)

**Interfaces:**
- Consumes: `sections.check_fields(fm, section_name, path, registry=None) -> list[str]`, `sections.default_registry() -> dict`, `sections.SectionsError` (Task 1).
- Produces:
  - `lint_theme(theme_dir: Path, registry: dict | None = None) -> list[str]`
  - `lint_question(question_dir: Path, registry: dict | None = None) -> list[str]`
  - `validate_unique_theme_weights(themes: list[dict]) -> list[str]` (unchanged)
  - `run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]`

Constants and code deleted: `STATUSES`, `THEME_REQUIRED`, `THEME_OPTIONAL`, `THEME_FORBIDDEN`, `QUESTION_REQUIRED`, `QUESTION_OPTIONAL`, and the inline status-enum / weight-int / tags-list / list-field checks in both lint functions. `OUTPUT_KINDS` stays (inner shape of the `structured` `outputs` field).

- [ ] **Step 1: Write the failing tests**

In `tools/test_check_research_fixtures.py`:

**1a.** Replace the module header (from the first line through `import check_research_fixtures as lint  # noqa: E402`):

```python
"""Tests for check_research_fixtures.py — run with:
   python3 -m unittest tools/test_check_research_fixtures.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_research_fixtures as lint  # noqa: E402
```

with:

```python
"""Tests for check_research_fixtures.py — run with:
   python3 -m unittest tools/test_check_research_fixtures.py -v
"""
from __future__ import annotations

import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_research_fixtures as lint  # noqa: E402
import sections  # noqa: E402
```

**1b.** Reword an assertion on the old message (refinement 1). Replace:

```python
        self.assertTrue(any("forbidden field 'parent_question'" in e for e in errs))
```

with:

```python
        self.assertTrue(any("unknown field 'parent_question'" in e for e in errs))
```

**1c.** Insert this class above the trailing `if __name__ == "__main__":` block (two blank lines before and after):

```python
class RegistryTests(unittest.TestCase):
    """The field contract is data/sections.json's, read through sections.py."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_empty_status_now_fails(self):
        # `status:` with no value parses to "" — the old `if status and ...`
        # guard let it through; the registry enum check does not.
        _write(self.tmp, "t", THEME_OK.replace("status: active", "status:"))
        errs = lint.lint_theme(self.tmp / "t")
        self.assertTrue(any("status='' not in" in e for e in errs), errs)

    def test_status_enum_comes_from_the_registry(self):
        reg = copy.deepcopy(sections.default_registry())
        reg["sections"]["research/themes"]["fields"]["status"]["values"] = ["dormant"]
        _write(self.tmp, "t", THEME_OK)
        errs = lint.lint_theme(self.tmp / "t", reg)
        self.assertTrue(any("status='active' not in ['dormant']" in e for e in errs), errs)

    def test_run_fails_closed_when_the_registry_cannot_load(self):
        (self.tmp / "content" / "research" / "themes").mkdir(parents=True)
        (self.tmp / "content" / "research" / "questions").mkdir(parents=True)
        boom = sections.SectionsError("sections: registry not found at X")
        with mock.patch.object(lint.sections, "default_registry", side_effect=boom):
            self.assertEqual(lint.run(self.tmp), (1, ["sections: registry not found at X"]))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tools/test_check_research_fixtures.py -v`
Expected: FAIL (failures=1, errors=2): `test_empty_status_now_fails` — `AssertionError: False is not true : []`; `test_status_enum_comes_from_the_registry` — `TypeError: lint_theme() takes 1 positional argument but 2 were given`; `test_run_fails_closed_when_the_registry_cannot_load` — `AttributeError: module 'check_research_fixtures' has no attribute 'sections'`. (The reworded `forbidden` assertion already passes: the old linter emitted both messages.)

- [ ] **Step 3: Rewrite `tools/check_research_fixtures.py`**

Replace the whole file with:

```python
#!/usr/bin/env python3
"""Research fixture frontmatter linter.

Validates theme and question frontmatter contracts per spec §3.1
(2026-05-11 research surface slice). Field sets, enums and types come from
data/sections.json via sections.check_fields (spec 2026-10-20 §5.1); the
structured `outputs` shape and theme-weight uniqueness stay here. Imports
parse_frontmatter from check_fixtures so all linters share one YAML parser.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402
import sections  # noqa: E402


OUTPUT_KINDS = {"paper", "talk", "code"}


def _lint(entry_dir: Path, section: str, registry: dict | None) -> tuple[Path, dict | None, list[str]]:
    """Shared front half: locate, parse, and run the registry field checks."""
    md = entry_dir / "index.md"
    if not md.exists():
        return md, None, [f"{entry_dir}: no index.md"]
    fm = parse_frontmatter(md.read_text())
    if fm is None:
        return md, None, [f"{md}: no frontmatter"]
    return md, fm, sections.check_fields(fm, section, md, registry=registry)


def lint_theme(theme_dir: Path, registry: dict | None = None) -> list[str]:
    """Return list of error strings for one theme dir."""
    _md, _fm, errors = _lint(theme_dir, "research/themes", registry)
    return errors


def lint_question(question_dir: Path, registry: dict | None = None) -> list[str]:
    """Return list of error strings for one question dir."""
    md, fm, errors = _lint(question_dir, "research/questions", registry)
    if fm is None:
        return errors

    # `outputs` is a `structured` field: the registry checks presence only and
    # its inner shape stays here (spec §4).
    outputs = fm.get("outputs")
    if outputs is not None:
        if not isinstance(outputs, list):
            errors.append(f"{md}: outputs must be a list")
        else:
            for i, o in enumerate(outputs):
                if not isinstance(o, dict):
                    errors.append(f"{md}: outputs[{i}] must be a mapping")
                    continue
                kind = o.get("kind")
                if kind not in OUTPUT_KINDS:
                    errors.append(
                        f"{md}: outputs[{i}].kind='{kind}' not in {sorted(OUTPUT_KINDS)}"
                    )
                year = o.get("year")
                if not isinstance(year, int) or not (1900 <= year <= 2100):
                    errors.append(
                        f"{md}: outputs[{i}].year must be a 4-digit int, got {year!r}"
                    )
                title = o.get("title")
                if not isinstance(title, str) or not title.strip():
                    errors.append(f"{md}: outputs[{i}].title must be non-empty string")
                url = o.get("url")
                if not isinstance(url, str) or not url.strip():
                    errors.append(f"{md}: outputs[{i}].url must be non-empty string")

    return errors


def validate_unique_theme_weights(themes: list[dict]) -> list[str]:
    """Theme weights must be unique so themePaletteOrder is deterministic.

    Returns a list of error strings (empty if all weights are distinct or absent).
    """
    seen: dict[int, str] = {}
    errors: list[str] = []
    for theme in themes:
        w = theme.get("weight")
        if w is None:
            continue
        if w in seen:
            errors.append(
                f"theme weight {w} duplicated: {seen[w]} and {theme['slug']}"
            )
        else:
            seen[w] = theme["slug"]
    return errors


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]
    themes_dir = repo_root / "content" / "research" / "themes"
    questions_dir = repo_root / "content" / "research" / "questions"
    errors: list[str] = []
    themes: list[dict] = []
    for d in sorted(themes_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        errors.extend(lint_theme(d, reg))
        md = d / "index.md"
        if md.exists():
            fm = parse_frontmatter(md.read_text())
            if fm is not None:
                fm["slug"] = d.name
                themes.append(fm)
    errors.extend(validate_unique_theme_weights(themes))
    for d in sorted(questions_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        errors.extend(lint_question(d, reg))
    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    themes_dir = repo_root / "content" / "research" / "themes"
    questions_dir = repo_root / "content" / "research" / "questions"
    if not themes_dir.is_dir() or not questions_dir.is_dir():
        print(
            f"error: missing {themes_dir} or {questions_dir}", file=sys.stderr
        )
        return 1
    rc, errors = run(repo_root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"\n{len(errors)} problem(s).", file=sys.stderr)
    if rc == 0:
        print("All research fixtures pass linter.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tools/test_check_research_fixtures.py -v`
Expected: PASS — `Ran 18 tests`, `OK`.

- [ ] **Step 5: Run the linter against the real repo, and its neighbours**

Run: `python3 tools/check_research_fixtures.py`
Expected: `All research fixtures pass linter.`, exit 0.

Run: `python3 -m unittest tools/test_sections.py -v 2>&1 | tail -1`
Expected: `OK`.

- [ ] **Step 6: Run the equivalence gate**

Write `$SCRATCH/eqgate.py` (overwrite any earlier copy) with exactly:

```python
#!/usr/bin/env python3
"""Throwaway equivalence gate for one fixture-linter migration. NOT committed.

Run from the repo root with the migration applied but uncommitted:

    python3 "$SCRATCH/eqgate.py" <linter_module>

"Before" is tools/ at HEAD (git archive); "after" is the working tree. Both
run() over the real content/ + data/ and over one mutated copy per entry in
MUTATIONS. Messages are normalized to (file, field, rule) so wording-only
changes vanish; everything else is printed. Exit 0 = no diff at all.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path.cwd()
LINTER = sys.argv[1]

# (label, relpath, op, *args)
#   frontmatter ops (top-level key):  drop KEY | set KEY RAW | add KEY RAW
#   library yaml ops (item N):        item-drop N KEY | item-set N KEY RAW
#                                     | extras-set N KEY RAW
MUTATIONS: list[tuple] = [
    ("theme: drop status", "content/research/themes/example-theme-one/index.md", "drop", "status"),
    ("theme: drop description", "content/research/themes/example-theme-one/index.md", "drop", "description"),
    ("theme: bad status", "content/research/themes/example-theme-one/index.md", "set", "status", "pondering"),
    ("theme: empty status", "content/research/themes/example-theme-one/index.md", "set", "status", ""),
    ("theme: forbidden parent_question", "content/research/themes/example-theme-one/index.md", "add", "parent_question", "example-question-one"),
    ("theme: forbidden theme", "content/research/themes/example-theme-one/index.md", "add", "theme", "example-theme-two"),
    ("theme: weight not int", "content/research/themes/example-theme-one/index.md", "set", "weight", "high"),
    ("theme: duplicate weight", "content/research/themes/example-theme-one/index.md", "set", "weight", "20"),
    ("theme: tags scalar", "content/research/themes/example-theme-one/index.md", "set", "tags", "research"),
    ("theme: tags block of ints", "content/research/themes/example-theme-one/index.md", "set", "tags", "\n  - 2024"),
    ("theme: bad last_modified", "content/research/themes/example-theme-one/index.md", "set", "last_modified", "not-a-date"),
    ("theme: draft not bool", "content/research/themes/example-theme-one/index.md", "set", "draft", "maybe"),
    ("question: unknown field", "content/research/questions/example-question-one/index.md", "add", "nonsense", "yes"),
    ("question: drop theme", "content/research/questions/example-question-one/index.md", "drop", "theme"),
    ("question: summary not allowed", "content/research/questions/example-question-one/index.md", "add", "summary", "x"),
    ("question: supporting_notes scalar", "content/research/questions/example-question-one/index.md", "set", "supporting_notes", "bayesian-statistics"),
    ("question: weight not int", "content/research/questions/example-question-one/index.md", "set", "weight", "ten"),
    ("question: bad output kind", "content/research/questions/example-question-one/index.md", "set", "outputs", "\n  - { kind: poster, title: \"X\", url: \"https://x\", year: 2025 }"),
    ("question: outputs scalar", "content/research/questions/example-question-one/index.md", "set", "outputs", "nope"),
    ("question: bad started", "content/research/questions/example-question-one/index.md", "set", "started", "2025-9-1"),
]

RUNNER = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import importlib\n"
    "m = importlib.import_module(sys.argv[2])\n"
    "res = m.run(Path(sys.argv[3]))\n"
    "print(json.dumps({'rc': res[0], 'errs': [str(e) for e in res[1]]}))\n"
)

# First match wins; group 1 is the field. Unmatched messages are compared
# verbatim as rule "code" (cross-field / structured / format rules that the
# migration must leave byte-identical).
PATTERNS = [
    (r"missing required field '([\w.]+)'", "missing"),
    (r"'(\w+)' is required for \w+ notes", "missing"),
    (r"([\w.]+) missing$", "missing"),
    (r"unknown field '([\w.]+)'", "unknown"),
    (r"forbidden field '(\w+)' on theme", "unknown"),
    (r"'(\w+)' not permitted on \w+ notes", "unknown"),
    (r"(extras\.\w+) not allowed for media_type", "unknown"),
    (r"([\w.\[\]]+)='.*' not (?:in|allowed in)\b", "enum"),
    (r"(tile_size) '.*' not in", "enum"),
    (r"([\w.]+)='.*' is not a valid YYYY-MM-DD date", "type"),
    (r"(\w+) not YYYY-MM-DD", "type"),
    (r"([\w.]+\[\d+\]) must be a string", "type"),
    (r"(tags) must be a list \(may be empty\)", "type"),
    (r"(canonical_url) must be https", "type"),
    (r"(extras\.\w+) must be (?:10 or 13|a positive|an absolute|a relative|a non-empty)", "type"),
    (r"([\w.]+) must be (?:an integer|a non-negative integer|int\b|a boolean|bool\b"
     r"|a list\b|a string|a mapping|a dict|a YYYY-MM-DD date)", "type"),
]


def norm(msg: str) -> tuple[str, str, str]:
    file, sep, rest = msg.partition(": ")
    if not sep:
        return ("", msg, "code")
    for pat, rule in PATTERNS:
        m = re.match(pat, rest)
        if m:
            return (file, m.group(1).removeprefix("extras."), rule)
    return (file, rest, "code")


def run_side(tools: Path, root: Path) -> tuple[int, set]:
    p = subprocess.run([sys.executable, "-c", RUNNER, str(tools), LINTER, str(root)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"runner crashed under {tools}:\n{p.stderr}")
    out = json.loads(p.stdout.strip().splitlines()[-1])
    return out["rc"], {norm(e) for e in out["errs"]}


def _fm_end(lines: list[str]) -> int:
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return i
    sys.exit("frontmatter not closed")


def _block_end(lines: list[str], i: int, stop: int, indent: str) -> int:
    j = i + 1
    while j < stop and lines[j].startswith(indent + " "):
        j += 1
    return j


def _item_bounds(lines: list[str], n: int) -> tuple[int, int]:
    starts = [i for i, l in enumerate(lines) if l.startswith("  - ")]
    s = starts[n]
    e = starts[n + 1] if n + 1 < len(starts) else len(lines)
    return s, e


def mutate(root: Path, rel: str, op: str, args: tuple) -> None:
    p = root / rel
    lines = p.read_text().split("\n")
    if op in ("drop", "set", "add"):
        end = _fm_end(lines)
        key = args[0]
        idx = next((i for i in range(1, end) if lines[i].startswith(key + ":")), None)
        if op == "add":
            lines.insert(end, f"{key}: {args[1]}")
        else:
            if idx is None:
                sys.exit(f"{rel}: no top-level key '{key}'")
            j = _block_end(lines, idx, end, "")
            lines[idx:j] = [] if op == "drop" else [f"{key}: {args[1]}"]
    else:
        n, key = int(args[0]), args[1]
        s, e = _item_bounds(lines, n)
        idx = next((i for i in range(s, e)
                    if lines[i].startswith(f"    {key}:") or lines[i].startswith(f"  - {key}:")), None)
        if op == "item-drop":
            if idx is None:
                sys.exit(f"{rel}[{n}]: no key '{key}'")
            lines[idx:_block_end(lines, idx, e, "    ")] = []
        elif op == "item-set":
            lead = "  - " if idx is not None and lines[idx].startswith("  - ") else "    "
            if idx is None:
                lines.insert(e, f"    {key}: {args[2]}")
            else:
                lines[idx:_block_end(lines, idx, e, "    ")] = [f"{lead}{key}: {args[2]}"]
        elif op == "extras-set":
            ex = next((i for i in range(s, e) if lines[i].rstrip() == "    extras:"), None)
            if ex is None:
                lines.insert(e, "    extras:")
                ex = e
            j = ex + 1
            while j < len(lines) and lines[j].startswith("      "):
                j += 1
            # Appended last, so it wins over an existing value for the key.
            lines.insert(j, f"      {key}: {args[2]}")
        else:
            sys.exit(f"unknown op {op}")
    p.write_text("\n".join(lines))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="eqgate-"))
    subprocess.run(f"git archive HEAD tools data/sections.json | tar -x -C {tmp}",
                   shell=True, check=True, cwd=REPO)
    old_tools = tmp / "tools"
    new_tools = REPO / "tools"
    cases = [("real repo", REPO)]
    for k, (label, rel, op, *args) in enumerate(MUTATIONS):
        root = tmp / f"m{k}"
        shutil.copytree(REPO / "content", root / "content")
        shutil.copytree(REPO / "data", root / "data")
        mutate(root, rel, op, tuple(args))
        cases.append((label, root))
    diffs = 0
    for label, root in cases:
        rc_b, before = run_side(old_tools, root)
        rc_a, after = run_side(new_tools, root)
        gone, new = sorted(before - after), sorted(after - before)
        if rc_b != rc_a or gone or new:
            diffs += 1
            print(f"DIFF [{label}] rc {rc_b} -> {rc_a}")
            for sign, ts in (("-", gone), ("+", new)):
                for f, field, rule in ts:
                    where = f.replace(f"{root}/", "")
                    print(f"   {sign} {field} ({rule}) @ {where}")
        else:
            print(f"same [{label}] rc {rc_b}, {len(before)} violation(s)")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{diffs} case(s) differ")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run (repo root, migration uncommitted): `python3 "$SCRATCH/eqgate.py" check_research_fixtures`
Expected: every case prints `same [...]` except exactly these, which are the intended behaviour changes recorded in the commit message (exit 1 is expected while they are present):

| Case | Diff |
|---|---|
| `theme: empty status` | `+ status (enum)` |
| `theme: bad last_modified` | `+ last_modified (type)` |
| `theme: draft not bool` | `+ draft (type)` |
| `question: bad started` | `+ started (type)` |

The last line reads `4 case(s) differ`. Any other `DIFF` is a regression: fix the linter (not the gate) and re-run. `same [real repo] rc 0, 0 violation(s)` must be the first line.

- [ ] **Step 7: Commit**

```bash
git add tools/check_research_fixtures.py tools/test_check_research_fixtures.py
git commit -m "$(cat <<'MSG'
refactor(tools): research fixture linter reads data/sections.json

Themes and questions are checked by sections.check_fields against the
research/themes and research/questions registry entries. THEME_FORBIDDEN
is gone: with the themes entry closed, parent_question/theme on a theme are
reported once as `unknown field` (previously twice: forbidden + unknown).
outputs' inner shape and theme-weight uniqueness stay as code.

Equivalence gate (normalized file/field/rule over the real tree + 20
mutations): wording-only changes elsewhere; intended behaviour changes —
- an empty `status:` ("") now fails the enum (old `if status and` skipped it)
- last_modified / started are now type-checked as dates
- draft is now type-checked as a bool

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
)"
```

### Task 3: Migrate `check_streams_fixtures.py`

**Files:**
- Modify: `tools/check_streams_fixtures.py` (full rewrite, lines 1-148)
- Test: `tools/test_check_streams_fixtures.py` (modify)

**Interfaces:**
- Consumes: `sections.check_fields(fm, section_name, path, registry=None) -> list[str]`, `sections.default_registry() -> dict`, `sections.SectionsError` (Task 1).
- Produces:
  - `lint_file(md: Path, registry: dict | None = None) -> list[str]`
  - `run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]`

Constants and code deleted: `REQUIRED`, `OPTIONAL`, `FIELDS`, `CATEGORY_VALUES`, `ARCHIVE_STATUS_VALUES`, and the inline required/unknown/category/archive_status/related-list/tags-list checks. `PLATFORM_VALUES` stays: it is an enum on the *elements* of the `platforms` list, which a `list` field cannot carry (`values` is enum-only, spec §5.1).

- [ ] **Step 1: Write the failing tests**

In `tools/test_check_streams_fixtures.py`:

**1a.** Replace the module header (from the first line through `import check_streams_fixtures as lint  # noqa: E402`):

```python
"""Tests for check_streams_fixtures.py — run with:
   python3 -m unittest tools/test_check_streams_fixtures.py -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_streams_fixtures as lint  # noqa: E402
```

with:

```python
"""Tests for check_streams_fixtures.py — run with:
   python3 -m unittest tools/test_check_streams_fixtures.py -v
"""
from __future__ import annotations

import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_streams_fixtures as lint  # noqa: E402
import sections  # noqa: E402
```

**1b.** Insert this class above the trailing `if __name__ == "__main__":` block (two blank lines before and after):

```python
class StreamsRegistryTests(unittest.TestCase):
    """The field contract is data/sections.json's, read through sections.py."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.streams = self.tmp / "content" / "streams"
        self.streams.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, slug: str, body: str) -> Path:
        d = self.streams / slug
        d.mkdir()
        p = d / "index.md"
        p.write_text(body)
        return p

    def test_datetime_string_date_passes(self):
        # Stream dates carry a time and offset; parse_scalar keeps them strings.
        p = self._write("dt", VALID)
        self.assertEqual(lint.lint_file(p), [])

    def test_non_date_string_now_fails(self):
        p = self._write("bad-date", VALID.replace("date: 2026-04-10T19:00:00-04:00", "date: April"))
        self.assertIn(f"{p}: date must be a YYYY-MM-DD date", lint.lint_file(p))

    def test_category_enum_comes_from_the_registry(self):
        reg = copy.deepcopy(sections.default_registry())
        reg["sections"]["streams"]["fields"]["category"]["values"] = ["research"]
        p = self._write("cat", VALID)
        self.assertIn(f"{p}: category='coding' not in ['research']", lint.lint_file(p, reg))

    def test_run_fails_closed_when_the_registry_cannot_load(self):
        boom = sections.SectionsError("sections: registry not found at X")
        with mock.patch.object(lint.sections, "default_registry", side_effect=boom):
            self.assertEqual(lint.run(self.tmp), (1, ["sections: registry not found at X"]))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tools/test_check_streams_fixtures.py -v`
Expected: FAIL (failures=1, errors=2): `test_non_date_string_now_fails` — `AssertionError: '…/bad-date/index.md: date must be a YYYY-MM-DD date' not found in []`; `test_category_enum_comes_from_the_registry` — `TypeError: lint_file() takes 1 positional argument but 2 were given`; `test_run_fails_closed_when_the_registry_cannot_load` — `AttributeError: module 'check_streams_fixtures' has no attribute 'sections'`.

- [ ] **Step 3: Rewrite `tools/check_streams_fixtures.py`**

Replace the whole file with:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tools/test_check_streams_fixtures.py -v`
Expected: PASS — `Ran 23 tests`, `OK`.

- [ ] **Step 5: Run the linter against the real repo, and its neighbours**

Run: `python3 tools/check_streams_fixtures.py`
Expected: `check_streams_fixtures: OK`, exit 0.

Run: `python3 -m unittest tools/test_sections.py -v 2>&1 | tail -1`
Expected: `OK`.

- [ ] **Step 6: Run the equivalence gate**

Write `$SCRATCH/eqgate.py` (overwrite any earlier copy) with exactly:

```python
#!/usr/bin/env python3
"""Throwaway equivalence gate for one fixture-linter migration. NOT committed.

Run from the repo root with the migration applied but uncommitted:

    python3 "$SCRATCH/eqgate.py" <linter_module>

"Before" is tools/ at HEAD (git archive); "after" is the working tree. Both
run() over the real content/ + data/ and over one mutated copy per entry in
MUTATIONS. Messages are normalized to (file, field, rule) so wording-only
changes vanish; everything else is printed. Exit 0 = no diff at all.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path.cwd()
LINTER = sys.argv[1]

# (label, relpath, op, *args)
#   frontmatter ops (top-level key):  drop KEY | set KEY RAW | add KEY RAW
#   library yaml ops (item N):        item-drop N KEY | item-set N KEY RAW
#                                     | extras-set N KEY RAW
MUTATIONS: list[tuple] = [
    ("drop title", "content/streams/2026-04-10-example-live-coding-stream/index.md", "drop", "title"),
    ("drop platforms", "content/streams/2026-04-10-example-live-coding-stream/index.md", "drop", "platforms"),
    ("drop draft", "content/streams/2026-04-10-example-live-coding-stream/index.md", "drop", "draft"),
    ("bad category", "content/streams/2026-04-10-example-live-coding-stream/index.md", "set", "category", "news"),
    ("bad archive_status", "content/streams/2026-04-10-example-live-coding-stream/index.md", "set", "archive_status", "pending"),
    ("bad platform", "content/streams/2026-04-10-example-live-coding-stream/index.md", "set", "platforms", "[twitch, kick]"),
    ("platforms scalar", "content/streams/2026-04-10-example-live-coding-stream/index.md", "set", "platforms", "twitch"),
    ("archived no vod", "content/streams/2026-04-10-example-live-coding-stream/index.md", "set", "vod_url", "\"\""),
    ("unknown field", "content/streams/2026-04-10-example-live-coding-stream/index.md", "add", "rarity", "99"),
    ("related scalar", "content/streams/2026-04-10-example-live-coding-stream/index.md", "set", "related_garden", "story-atoms"),
    ("tags scalar", "content/streams/2026-04-10-example-live-coding-stream/index.md", "set", "tags", "example"),
    ("bad date", "content/streams/2026-04-10-example-live-coding-stream/index.md", "set", "date", "April"),
    ("title int", "content/streams/2026-04-10-example-live-coding-stream/index.md", "set", "title", "2026"),
]

RUNNER = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import importlib\n"
    "m = importlib.import_module(sys.argv[2])\n"
    "res = m.run(Path(sys.argv[3]))\n"
    "print(json.dumps({'rc': res[0], 'errs': [str(e) for e in res[1]]}))\n"
)

# First match wins; group 1 is the field. Unmatched messages are compared
# verbatim as rule "code" (cross-field / structured / format rules that the
# migration must leave byte-identical).
PATTERNS = [
    (r"missing required field '([\w.]+)'", "missing"),
    (r"'(\w+)' is required for \w+ notes", "missing"),
    (r"([\w.]+) missing$", "missing"),
    (r"unknown field '([\w.]+)'", "unknown"),
    (r"forbidden field '(\w+)' on theme", "unknown"),
    (r"'(\w+)' not permitted on \w+ notes", "unknown"),
    (r"(extras\.\w+) not allowed for media_type", "unknown"),
    (r"([\w.\[\]]+)='.*' not (?:in|allowed in)\b", "enum"),
    (r"(tile_size) '.*' not in", "enum"),
    (r"([\w.]+)='.*' is not a valid YYYY-MM-DD date", "type"),
    (r"(\w+) not YYYY-MM-DD", "type"),
    (r"([\w.]+\[\d+\]) must be a string", "type"),
    (r"(tags) must be a list \(may be empty\)", "type"),
    (r"(canonical_url) must be https", "type"),
    (r"(extras\.\w+) must be (?:10 or 13|a positive|an absolute|a relative|a non-empty)", "type"),
    (r"([\w.]+) must be (?:an integer|a non-negative integer|int\b|a boolean|bool\b"
     r"|a list\b|a string|a mapping|a dict|a YYYY-MM-DD date)", "type"),
]


def norm(msg: str) -> tuple[str, str, str]:
    file, sep, rest = msg.partition(": ")
    if not sep:
        return ("", msg, "code")
    for pat, rule in PATTERNS:
        m = re.match(pat, rest)
        if m:
            return (file, m.group(1).removeprefix("extras."), rule)
    return (file, rest, "code")


def run_side(tools: Path, root: Path) -> tuple[int, set]:
    p = subprocess.run([sys.executable, "-c", RUNNER, str(tools), LINTER, str(root)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"runner crashed under {tools}:\n{p.stderr}")
    out = json.loads(p.stdout.strip().splitlines()[-1])
    return out["rc"], {norm(e) for e in out["errs"]}


def _fm_end(lines: list[str]) -> int:
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return i
    sys.exit("frontmatter not closed")


def _block_end(lines: list[str], i: int, stop: int, indent: str) -> int:
    j = i + 1
    while j < stop and lines[j].startswith(indent + " "):
        j += 1
    return j


def _item_bounds(lines: list[str], n: int) -> tuple[int, int]:
    starts = [i for i, l in enumerate(lines) if l.startswith("  - ")]
    s = starts[n]
    e = starts[n + 1] if n + 1 < len(starts) else len(lines)
    return s, e


def mutate(root: Path, rel: str, op: str, args: tuple) -> None:
    p = root / rel
    lines = p.read_text().split("\n")
    if op in ("drop", "set", "add"):
        end = _fm_end(lines)
        key = args[0]
        idx = next((i for i in range(1, end) if lines[i].startswith(key + ":")), None)
        if op == "add":
            lines.insert(end, f"{key}: {args[1]}")
        else:
            if idx is None:
                sys.exit(f"{rel}: no top-level key '{key}'")
            j = _block_end(lines, idx, end, "")
            lines[idx:j] = [] if op == "drop" else [f"{key}: {args[1]}"]
    else:
        n, key = int(args[0]), args[1]
        s, e = _item_bounds(lines, n)
        idx = next((i for i in range(s, e)
                    if lines[i].startswith(f"    {key}:") or lines[i].startswith(f"  - {key}:")), None)
        if op == "item-drop":
            if idx is None:
                sys.exit(f"{rel}[{n}]: no key '{key}'")
            lines[idx:_block_end(lines, idx, e, "    ")] = []
        elif op == "item-set":
            lead = "  - " if idx is not None and lines[idx].startswith("  - ") else "    "
            if idx is None:
                lines.insert(e, f"    {key}: {args[2]}")
            else:
                lines[idx:_block_end(lines, idx, e, "    ")] = [f"{lead}{key}: {args[2]}"]
        elif op == "extras-set":
            ex = next((i for i in range(s, e) if lines[i].rstrip() == "    extras:"), None)
            if ex is None:
                lines.insert(e, "    extras:")
                ex = e
            j = ex + 1
            while j < len(lines) and lines[j].startswith("      "):
                j += 1
            # Appended last, so it wins over an existing value for the key.
            lines.insert(j, f"      {key}: {args[2]}")
        else:
            sys.exit(f"unknown op {op}")
    p.write_text("\n".join(lines))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="eqgate-"))
    subprocess.run(f"git archive HEAD tools data/sections.json | tar -x -C {tmp}",
                   shell=True, check=True, cwd=REPO)
    old_tools = tmp / "tools"
    new_tools = REPO / "tools"
    cases = [("real repo", REPO)]
    for k, (label, rel, op, *args) in enumerate(MUTATIONS):
        root = tmp / f"m{k}"
        shutil.copytree(REPO / "content", root / "content")
        shutil.copytree(REPO / "data", root / "data")
        mutate(root, rel, op, tuple(args))
        cases.append((label, root))
    diffs = 0
    for label, root in cases:
        rc_b, before = run_side(old_tools, root)
        rc_a, after = run_side(new_tools, root)
        gone, new = sorted(before - after), sorted(after - before)
        if rc_b != rc_a or gone or new:
            diffs += 1
            print(f"DIFF [{label}] rc {rc_b} -> {rc_a}")
            for sign, ts in (("-", gone), ("+", new)):
                for f, field, rule in ts:
                    where = f.replace(f"{root}/", "")
                    print(f"   {sign} {field} ({rule}) @ {where}")
        else:
            print(f"same [{label}] rc {rc_b}, {len(before)} violation(s)")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{diffs} case(s) differ")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run (repo root, migration uncommitted): `python3 "$SCRATCH/eqgate.py" check_streams_fixtures`
Expected: every case prints `same [...]` except exactly these, which are the intended behaviour changes recorded in the commit message (exit 1 is expected while they are present):

| Case | Diff |
|---|---|
| `bad date` | `+ date (type)` |
| `title int` | `+ title (type)` |

The last line reads `2 case(s) differ`. Any other `DIFF` is a regression: fix the linter (not the gate) and re-run. `same [real repo] rc 0, 0 violation(s)` must be the first line.

- [ ] **Step 7: Commit**

```bash
git add tools/check_streams_fixtures.py tools/test_check_streams_fixtures.py
git commit -m "$(cat <<'MSG'
refactor(tools): streams fixture linter reads data/sections.json

Stream frontmatter is checked by sections.check_fields against the
streams registry entry. The per-element platforms enum and the
archived => vod_url rule stay as code.

Equivalence gate (real tree + 13 mutations): intended behaviour changes —
- date is now type-checked (an ISO date or datetime string still passes)
- title is now type-checked as a string

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
)"
```

### Task 4: Migrate `check_recipes_fixtures.py`

**Files:**
- Modify: `tools/check_recipes_fixtures.py` (full rewrite, lines 1-212)
- Test: `tools/test_check_recipes_fixtures.py` (modify)

**Interfaces:**
- Consumes: `sections.check_fields(fm, section_name, path, registry=None) -> list[str]`, `sections.default_registry() -> dict`, `sections.SectionsError` (Task 1).
- Produces:
  - `lint_file(md: Path, registry: dict | None = None) -> list[str]`
  - `run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]`

Constants and code deleted: `REQUIRED`, `OPTIONAL`, `FIELDS`, the inline required/unknown loops, and the non-int branch of the `*_minutes` check (now the registry's `int`; the `< 0` branch stays). `TIMECODE_RE`, `_NUM_RE`, `_PADDED_VALUE_RE`, `_PADDED_NUMERIC_KEYS`, `_NULL_SPELLINGS` and every helper stay.

- [ ] **Step 1: Write the failing tests**

In `tools/test_check_recipes_fixtures.py`:

**1a.** Replace the module header (from the first line through `import check_recipes_fixtures as mod`):

```python
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo
import check_recipes_fixtures as mod
```

with:

```python
import copy
import unittest
from pathlib import Path
from unittest import mock
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_helpers import TempRepo
import check_recipes_fixtures as mod
import sections
```

**1b.** Insert this class above the trailing `if __name__ == "__main__":` block (two blank lines before and after):

```python
class RegistryTests(unittest.TestCase):
    """The field contract is data/sections.json's, read through sections.py."""

    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_tags_scalar_now_fails(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("servings: 4", "servings: 4\ntags: example"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any(e.endswith(": tags must be a list") for e in errs), errs)

    def test_non_integer_minutes_get_the_registry_message(self):
        self.repo.write("content/recipes/ex/index.md",
                        VALID.replace("servings: 4", "servings: 4\nprep_minutes: 1.5"))
        rc, errs = mod.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any(e.endswith(": prep_minutes must be an integer") for e in errs), errs)

    def test_required_set_comes_from_the_registry(self):
        reg = copy.deepcopy(sections.default_registry())
        reg["sections"]["recipes"]["fields"]["video"]["required"] = True
        self.repo.write("content/recipes/ex/index.md", VALID)
        rc, errs = mod.run(self.repo.root, registry=reg)
        self.assertEqual(rc, 1)
        self.assertTrue(any("missing required field 'video'" in e for e in errs), errs)

    def test_run_fails_closed_when_the_registry_cannot_load(self):
        boom = sections.SectionsError("sections: registry not found at X")
        with mock.patch.object(mod.sections, "default_registry", side_effect=boom):
            self.assertEqual(mod.run(self.repo.root), (1, ["sections: registry not found at X"]))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tools/test_check_recipes_fixtures.py -v`
Expected: FAIL (failures=2, errors=2): `test_tags_scalar_now_fails` — `AssertionError: 0 != 1`; `test_non_integer_minutes_get_the_registry_message` — `AssertionError: False is not true : ['…: prep_minutes must be a non-negative integer']`; `test_required_set_comes_from_the_registry` — `TypeError: run() got an unexpected keyword argument 'registry'`; `test_run_fails_closed_when_the_registry_cannot_load` — `AttributeError: module 'check_recipes_fixtures' has no attribute 'sections'`.

- [ ] **Step 3: Rewrite `tools/check_recipes_fixtures.py`**

Replace the whole file with:

```python
#!/usr/bin/env python3
"""Recipe fixture frontmatter shape linter.

Walks content/recipes/<slug>/index.md and validates frontmatter against
spec 2026-07-06-recipe-slice-1-render-download-design.md. Field sets and
types come from data/sections.json via sections.check_fields (spec
2026-10-20); the structured ingredients/sources/steps shapes, the servings
number rule and the zero-padding guard stay here. Stdlib only.
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
import sections  # noqa: E402

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


def lint_file(md: Path, registry: dict | None = None) -> list[str]:
    errs: list[str] = []
    raw = md.read_text()
    fm = parse_frontmatter(raw)
    if fm is None:
        return [f"{md}: no frontmatter"]

    errs.extend(_padded_errors(md, raw))
    errs.extend(sections.check_fields(fm, "recipes", md, registry=registry))

    sv = fm.get("servings")
    if sv is not None and not (_is_num(sv) and float(str(sv)) > 0):
        errs.append(f"{md}: servings must be a number > 0")

    # Integer-ness is the registry's (`int`); the sign is not expressible there.
    for key in ("prep_minutes", "cook_minutes", "total_minutes"):
        v = fm.get(key)
        if isinstance(v, int) and not isinstance(v, bool) and v < 0:
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


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]
    all_errs: list[str] = []
    root = repo_root / "content" / "recipes"
    if root.exists():
        for child in sorted(root.iterdir()):
            md = child / "index.md"
            if child.is_dir() and md.exists():
                all_errs.extend(lint_file(md, reg))
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tools/test_check_recipes_fixtures.py -v`
Expected: PASS — `Ran 25 tests`, `OK`.

- [ ] **Step 5: Run the linter against the real repo, and its neighbours**

Run: `python3 tools/check_recipes_fixtures.py`
Expected: `check_recipes_fixtures: OK`, exit 0.

Run: `python3 -m unittest tools/test_sections.py -v 2>&1 | tail -1`
Expected: `OK`.

- [ ] **Step 6: Run the equivalence gate**

Write `$SCRATCH/eqgate.py` (overwrite any earlier copy) with exactly:

```python
#!/usr/bin/env python3
"""Throwaway equivalence gate for one fixture-linter migration. NOT committed.

Run from the repo root with the migration applied but uncommitted:

    python3 "$SCRATCH/eqgate.py" <linter_module>

"Before" is tools/ at HEAD (git archive); "after" is the working tree. Both
run() over the real content/ + data/ and over one mutated copy per entry in
MUTATIONS. Messages are normalized to (file, field, rule) so wording-only
changes vanish; everything else is printed. Exit 0 = no diff at all.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path.cwd()
LINTER = sys.argv[1]

# (label, relpath, op, *args)
#   frontmatter ops (top-level key):  drop KEY | set KEY RAW | add KEY RAW
#   library yaml ops (item N):        item-drop N KEY | item-set N KEY RAW
#                                     | extras-set N KEY RAW
MUTATIONS: list[tuple] = [
    ("drop servings", "content/recipes/example-recipe-one/index.md", "drop", "servings"),
    ("drop steps", "content/recipes/example-recipe-one/index.md", "drop", "steps"),
    ("drop summary", "content/recipes/example-recipe-one/index.md", "drop", "summary"),
    ("unknown field", "content/recipes/example-recipe-one/index.md", "add", "bogus", "1"),
    ("servings zero", "content/recipes/example-recipe-one/index.md", "set", "servings", "0"),
    ("servings padded", "content/recipes/example-recipe-one/index.md", "set", "servings", "08"),
    ("prep negative", "content/recipes/example-recipe-one/index.md", "set", "prep_minutes", "-5"),
    ("prep float", "content/recipes/example-recipe-one/index.md", "set", "prep_minutes", "1.5"),
    ("prep padded", "content/recipes/example-recipe-one/index.md", "set", "prep_minutes", "010"),
    ("cook bool", "content/recipes/example-recipe-one/index.md", "set", "cook_minutes", "true"),
    ("ingredients empty", "content/recipes/example-recipe-one/index.md", "set", "ingredients", "[]"),
    ("bad timecode", "content/recipes/example-recipe-one/index.md", "set", "steps", "\n  - \"[99:99] bad\""),
    ("tags scalar", "content/recipes/example-recipe-one/index.md", "set", "tags", "example"),
    ("cuisine int", "content/recipes/example-recipe-one/index.md", "set", "cuisine", "7"),
    ("bad lastmod", "content/recipes/example-recipe-one/index.md", "set", "lastmod", "soon"),
]

RUNNER = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import importlib\n"
    "m = importlib.import_module(sys.argv[2])\n"
    "res = m.run(Path(sys.argv[3]))\n"
    "print(json.dumps({'rc': res[0], 'errs': [str(e) for e in res[1]]}))\n"
)

# First match wins; group 1 is the field. Unmatched messages are compared
# verbatim as rule "code" (cross-field / structured / format rules that the
# migration must leave byte-identical).
PATTERNS = [
    (r"missing required field '([\w.]+)'", "missing"),
    (r"'(\w+)' is required for \w+ notes", "missing"),
    (r"([\w.]+) missing$", "missing"),
    (r"unknown field '([\w.]+)'", "unknown"),
    (r"forbidden field '(\w+)' on theme", "unknown"),
    (r"'(\w+)' not permitted on \w+ notes", "unknown"),
    (r"(extras\.\w+) not allowed for media_type", "unknown"),
    (r"([\w.\[\]]+)='.*' not (?:in|allowed in)\b", "enum"),
    (r"(tile_size) '.*' not in", "enum"),
    (r"([\w.]+)='.*' is not a valid YYYY-MM-DD date", "type"),
    (r"(\w+) not YYYY-MM-DD", "type"),
    (r"([\w.]+\[\d+\]) must be a string", "type"),
    (r"(tags) must be a list \(may be empty\)", "type"),
    (r"(canonical_url) must be https", "type"),
    (r"(extras\.\w+) must be (?:10 or 13|a positive|an absolute|a relative|a non-empty)", "type"),
    (r"([\w.]+) must be (?:an integer|a non-negative integer|int\b|a boolean|bool\b"
     r"|a list\b|a string|a mapping|a dict|a YYYY-MM-DD date)", "type"),
]


def norm(msg: str) -> tuple[str, str, str]:
    file, sep, rest = msg.partition(": ")
    if not sep:
        return ("", msg, "code")
    for pat, rule in PATTERNS:
        m = re.match(pat, rest)
        if m:
            return (file, m.group(1).removeprefix("extras."), rule)
    return (file, rest, "code")


def run_side(tools: Path, root: Path) -> tuple[int, set]:
    p = subprocess.run([sys.executable, "-c", RUNNER, str(tools), LINTER, str(root)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"runner crashed under {tools}:\n{p.stderr}")
    out = json.loads(p.stdout.strip().splitlines()[-1])
    return out["rc"], {norm(e) for e in out["errs"]}


def _fm_end(lines: list[str]) -> int:
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return i
    sys.exit("frontmatter not closed")


def _block_end(lines: list[str], i: int, stop: int, indent: str) -> int:
    j = i + 1
    while j < stop and lines[j].startswith(indent + " "):
        j += 1
    return j


def _item_bounds(lines: list[str], n: int) -> tuple[int, int]:
    starts = [i for i, l in enumerate(lines) if l.startswith("  - ")]
    s = starts[n]
    e = starts[n + 1] if n + 1 < len(starts) else len(lines)
    return s, e


def mutate(root: Path, rel: str, op: str, args: tuple) -> None:
    p = root / rel
    lines = p.read_text().split("\n")
    if op in ("drop", "set", "add"):
        end = _fm_end(lines)
        key = args[0]
        idx = next((i for i in range(1, end) if lines[i].startswith(key + ":")), None)
        if op == "add":
            lines.insert(end, f"{key}: {args[1]}")
        else:
            if idx is None:
                sys.exit(f"{rel}: no top-level key '{key}'")
            j = _block_end(lines, idx, end, "")
            lines[idx:j] = [] if op == "drop" else [f"{key}: {args[1]}"]
    else:
        n, key = int(args[0]), args[1]
        s, e = _item_bounds(lines, n)
        idx = next((i for i in range(s, e)
                    if lines[i].startswith(f"    {key}:") or lines[i].startswith(f"  - {key}:")), None)
        if op == "item-drop":
            if idx is None:
                sys.exit(f"{rel}[{n}]: no key '{key}'")
            lines[idx:_block_end(lines, idx, e, "    ")] = []
        elif op == "item-set":
            lead = "  - " if idx is not None and lines[idx].startswith("  - ") else "    "
            if idx is None:
                lines.insert(e, f"    {key}: {args[2]}")
            else:
                lines[idx:_block_end(lines, idx, e, "    ")] = [f"{lead}{key}: {args[2]}"]
        elif op == "extras-set":
            ex = next((i for i in range(s, e) if lines[i].rstrip() == "    extras:"), None)
            if ex is None:
                lines.insert(e, "    extras:")
                ex = e
            j = ex + 1
            while j < len(lines) and lines[j].startswith("      "):
                j += 1
            # Appended last, so it wins over an existing value for the key.
            lines.insert(j, f"      {key}: {args[2]}")
        else:
            sys.exit(f"unknown op {op}")
    p.write_text("\n".join(lines))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="eqgate-"))
    subprocess.run(f"git archive HEAD tools data/sections.json | tar -x -C {tmp}",
                   shell=True, check=True, cwd=REPO)
    old_tools = tmp / "tools"
    new_tools = REPO / "tools"
    cases = [("real repo", REPO)]
    for k, (label, rel, op, *args) in enumerate(MUTATIONS):
        root = tmp / f"m{k}"
        shutil.copytree(REPO / "content", root / "content")
        shutil.copytree(REPO / "data", root / "data")
        mutate(root, rel, op, tuple(args))
        cases.append((label, root))
    diffs = 0
    for label, root in cases:
        rc_b, before = run_side(old_tools, root)
        rc_a, after = run_side(new_tools, root)
        gone, new = sorted(before - after), sorted(after - before)
        if rc_b != rc_a or gone or new:
            diffs += 1
            print(f"DIFF [{label}] rc {rc_b} -> {rc_a}")
            for sign, ts in (("-", gone), ("+", new)):
                for f, field, rule in ts:
                    where = f.replace(f"{root}/", "")
                    print(f"   {sign} {field} ({rule}) @ {where}")
        else:
            print(f"same [{label}] rc {rc_b}, {len(before)} violation(s)")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{diffs} case(s) differ")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run (repo root, migration uncommitted): `python3 "$SCRATCH/eqgate.py" check_recipes_fixtures`
Expected: every case prints `same [...]` except exactly these, which are the intended behaviour changes recorded in the commit message (exit 1 is expected while they are present):

| Case | Diff |
|---|---|
| `tags scalar` | `+ tags (type)` |
| `cuisine int` | `+ cuisine (type)` |
| `bad lastmod` | `+ lastmod (type)` |

The last line reads `3 case(s) differ`. Any other `DIFF` is a regression: fix the linter (not the gate) and re-run. `same [real repo] rc 0, 0 violation(s)` must be the first line.

- [ ] **Step 7: Commit**

```bash
git add tools/check_recipes_fixtures.py tools/test_check_recipes_fixtures.py
git commit -m "$(cat <<'MSG'
refactor(tools): recipes fixture linter reads data/sections.json

Recipe frontmatter is checked by sections.check_fields against the
recipes registry entry. The structured ingredients/sources/steps shapes,
the servings number rule, the zero-padding guard and the minutes sign rule
stay as code; a non-integer *_minutes now gets the registry's
`must be an integer` wording.

Equivalence gate (real tree + 15 mutations): intended behaviour changes —
- tags is now type-checked as a list
- text fields (cuisine, category, …) are now type-checked as strings
- date/lastmod are now type-checked as dates

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
)"
```

### Task 5: Migrate `check_fixtures.py` (essays)

**Files:**
- Modify: `tools/check_fixtures.py` (full rewrite, lines 1-313)
- Test: `tools/test_check_fixtures.py` (modify)

**Interfaces:**
- Consumes: `sections.check_fields(fm, section_name, path, registry=None) -> list[str]`, `sections.default_registry() -> dict`, `sections.SectionsError` (Task 1).
- Produces:
  - `lint_essay(essay_dir: Path, valid_cite_keys: set[str], registry: dict | None = None) -> list[str]`
  - `run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]`
  - `parse_frontmatter`, `parse_scalar`, `_split_top_commas`, `FRONTMATTER_RE`, `parse_citations_yaml` — unchanged (every other linter imports them).

Constants and code deleted: `REQUIRED_FIELDS`, `ALLOWED_TILE_SIZE`, and the inline required-field loop and tile_size check. The parser and every series/hero/downloads/lastmod/cite rule stay. `sections.py` imports nothing from this module, so the new `import sections` creates no cycle.

- [ ] **Step 1: Write the failing tests**

In `tools/test_check_fixtures.py`:

**1a.** Replace the module header (from the first line through `from test_helpers import TempRepo as _TempRepo  # noqa: E402`):

```python
"""Tests for check_fixtures.py — run with: python3 -m unittest tools/test_check_fixtures.py -v"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_fixtures as lint  # noqa: E402  # pyright: ignore[reportMissingImports]
from test_helpers import TempRepo as _TempRepo  # noqa: E402
```

with:

```python
"""Tests for check_fixtures.py — run with: python3 -m unittest tools/test_check_fixtures.py -v"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_fixtures as lint  # noqa: E402  # pyright: ignore[reportMissingImports]
from test_helpers import TempRepo as _TempRepo  # noqa: E402
```

**1b.** Insert this class above the trailing `if __name__ == "__main__":` block (two blank lines before and after):

```python
class EssayRegistryTest(unittest.TestCase):
    """The essay field contract is data/sections.json's (an open section)."""

    def setUp(self) -> None:
        self.repo = TempRepo()
        self.repo.write_citations(VALID_CITATIONS)

    def tearDown(self) -> None:
        self.repo.cleanup()

    def test_undeclared_key_still_passes(self) -> None:
        body = VALID_FRONTMATTER.replace("toc: true\n", "toc: true\ncolophon: yes\n")
        self.repo.write_essay("open", body, hero=True)
        self.assertEqual(lint.run(self.repo.root), (0, []))

    def test_declared_key_is_now_type_checked(self) -> None:
        self.repo.write_essay("typed", VALID_FRONTMATTER.replace("toc: true", "toc: yes"), hero=True)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any(e.endswith(": toc must be a boolean") for e in errors), errors)

    def test_tile_size_message_is_canonical(self) -> None:
        self.repo.write_essay("t", VALID_FRONTMATTER.replace("tile_size: large", "tile_size: huge"),
                              hero=True)
        _rc, errors = lint.run(self.repo.root)
        self.assertTrue(any(e.endswith(": tile_size='huge' not in ['large', 'medium', 'small']")
                            for e in errors), errors)

    def test_run_fails_closed_when_the_registry_cannot_load(self) -> None:
        boom = lint.sections.SectionsError("sections: registry not found at X")
        with mock.patch.object(lint.sections, "default_registry", side_effect=boom):
            self.assertEqual(lint.run(self.repo.root), (1, ["sections: registry not found at X"]))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tools/test_check_fixtures.py -v`
Expected: FAIL (failures=2, errors=1): `test_declared_key_is_now_type_checked` — `AssertionError: 0 != 1`; `test_tile_size_message_is_canonical` — `AssertionError: False is not true : ["…: tile_size 'huge' not in {'medium', 'small', 'large'}"]`; `test_run_fails_closed_when_the_registry_cannot_load` — `AttributeError: module 'check_fixtures' has no attribute 'sections'`.

- [ ] **Step 3: Rewrite `tools/check_fixtures.py`**

Replace the whole file with:

```python
#!/usr/bin/env python3
"""Essay fixture frontmatter linter.

Walks `content/essays/*/index.md`, validates frontmatter against the
`essays` entry of data/sections.json (via sections.check_fields — an open
section: undeclared keys pass, declared ones are type-checked), and checks
every `{{< cite "key" >}}` reference resolves against `data/citations.yaml`.
The series/hero/downloads/date cross-field rules stay here.

This module also hosts the shared frontmatter parser every other linter
imports; sections.py deliberately imports nothing from it.

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sections  # noqa: E402

# Trailing delimiter tolerates optional trailing whitespace and either a
# newline or end-of-string (files whose closing `---` lacks a final newline).
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---[ \t]*(?:\n|$)", re.DOTALL)
CITE_RE = re.compile(r'\{\{<\s*cite\s+"([^"]+)"\s*>\}\}')
ENTRY_HEADER_RE = re.compile(r"^  ([^:\s]+):\s*$")
FIELD_RE = re.compile(r"^    ([a-zA-Z_]+):\s*(.*)$")


def parse_frontmatter(text: str) -> dict[str, object] | None:
    """Parse YAML frontmatter — narrow subset, no third-party deps.

    Supports:
      - Top-level key: value pairs (scalars, inline arrays, quoted strings).
      - Empty-value top-level keys followed by indented block-sequence items
        (each item is either a scalar or a flow-style mapping `{k: v, ...}`).

    Does NOT support: block-style nested mappings, multi-document streams,
    anchors/aliases, or any other YAML feature beyond what the existing
    essay/garden/research fixtures need.
    """
    # Normalize line endings so CRLF (and lone CR) frontmatter parses instead
    # of returning None — otherwise the ~14 linters that skip on None silently
    # ignore the file.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    out: dict[str, object] = {}
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        # Indented lines without a preceding empty-value key are ignored
        # (the look-ahead block below consumes them when appropriate).
        if raw.startswith((" ", "\t")) or ":" not in stripped:
            i += 1
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value != "":
            if value.startswith("{") and value.endswith("}"):
                out[key] = _parse_flow_mapping(value[1:-1])
            else:
                out[key] = parse_scalar(value)
            i += 1
            continue
        # Empty value — look for an indented block sequence on the next lines.
        items: list[object] = []
        j = i + 1
        while j < len(lines):
            nxt = lines[j]
            nxt_stripped = nxt.strip()
            if not nxt_stripped:
                j += 1
                continue
            if nxt.startswith((" ", "\t")) and nxt_stripped.startswith("-"):
                item_text = nxt_stripped[1:].strip()
                items.append(_parse_block_item(item_text))
                j += 1
                continue
            break
        if items:
            out[key] = items
            i = j
        else:
            out[key] = ""
            i += 1
    return out


def _parse_block_item(s: str) -> object:
    """Parse a single block-sequence item value (text after '- ')."""
    if s.startswith("{") and s.endswith("}"):
        return _parse_flow_mapping(s[1:-1])
    return parse_scalar(s)


def _parse_flow_mapping(inner: str) -> dict[str, object]:
    """Parse the inside of a flow-style mapping `{a: 1, b: "two"}`."""
    out: dict[str, object] = {}
    for piece in _split_top_commas(inner):
        if ":" not in piece:
            continue
        key, _, value = piece.partition(":")
        out[key.strip()] = parse_scalar(value.strip())
    return out


def _split_top_commas(s: str) -> list[str]:
    """Split a flow-mapping body on commas not inside quotes or braces."""
    parts: list[str] = []
    buf: list[str] = []
    quote = None
    depth = 0
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ('"', "'"):
            quote = ch
            buf.append(ch)
            continue
        if ch == "{":
            depth += 1
            buf.append(ch)
            continue
        if ch == "}":
            depth -= 1
            buf.append(ch)
            continue
        if ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return parts


def parse_scalar(s: str) -> object:
    if s == "":
        return ""
    if s in ("true", "false"):
        return s == "true"
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        # Split on top-level commas only — commas inside a quoted element
        # (e.g. an author "Lastname, First") must not fragment the item.
        items = _split_top_commas(inner)
        return [it.strip('"').strip("'") for it in items]
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        y, m, d = (int(x) for x in s.split("-"))
        return Date(y, m, d)
    return s


def parse_citations_yaml(text: str) -> dict[str, dict[str, object]]:
    """Two-level parser for data/citations.yaml.

    Format:
        citations:
          <key>:
            <field>: <scalar-or-inline-array>
            ...
          <key>:
            ...

    Returns the parsed mapping. Lines that don't match expected indent
    or shape are skipped — the validator below catches shape violations.
    """
    entries: dict[str, dict[str, object]] = {}
    in_citations = False
    current_key: str | None = None
    for raw in text.splitlines():
        if raw.startswith("#") or raw.strip() == "":
            continue
        if raw.startswith("citations:"):
            in_citations = True
            continue
        if not in_citations:
            continue
        m = ENTRY_HEADER_RE.match(raw)
        if m:
            key = m.group(1)
            current_key = key
            entries[key] = {}
            continue
        m = FIELD_RE.match(raw)
        if m and current_key is not None:
            field, value = m.group(1), m.group(2).strip()
            entries[current_key][field] = parse_scalar(value)
            continue
        # Anything else (e.g., top-level non-comment outside citations) ends the block.
        if not raw.startswith(" "):
            in_citations = False
            current_key = None
    return entries


def lint_essay(essay_dir: Path, valid_cite_keys: set[str],
               registry: dict | None = None) -> list[str]:
    md_path = essay_dir / "index.md"
    if not md_path.exists():
        return [f"{essay_dir}: no index.md"]
    text = md_path.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md_path}: no frontmatter"]

    errors = sections.check_fields(fm, "essays", md_path, registry=registry)

    series = fm.get("series", "")
    series_order = fm.get("series_order", 0)
    if series and series_order == 0:
        errors.append(
            f"{md_path}: series '{series}' set but series_order is 0"
        )

    hero = fm.get("hero", "")
    if hero:
        if not (essay_dir / str(hero)).exists():
            errors.append(f"{md_path}: hero file '{hero}' not found in page bundle")

    multi_export = fm.get("multi_export", False)
    downloads = fm.get("downloads", {}) or {}
    if not isinstance(downloads, dict):
        errors.append(f"{md_path}: downloads must be a mapping")
        downloads = {}

    if multi_export is True:
        allowed = {"pdf", "word"}
        unknown = set(downloads.keys()) - allowed
        for key in sorted(unknown):
            errors.append(f"{md_path}: downloads.{key} is not a recognized key (allowed: pdf, word)")
        if not (downloads.get("pdf") or downloads.get("word")):
            errors.append(
                f"{md_path}: multi_export: true requires at least one of downloads.pdf / downloads.word"
            )
        for key in ("pdf", "word"):
            rel = downloads.get(key)
            if rel:
                if not (essay_dir / str(rel)).exists():
                    errors.append(f"{md_path}: downloads.{key} '{rel}' not found in page bundle")

    date = fm.get("date")
    lastmod = fm.get("lastmod")
    if isinstance(date, Date) and isinstance(lastmod, Date) and lastmod < date:
        errors.append(f"{md_path}: lastmod {lastmod} is before date {date}")

    fm_match = FRONTMATTER_RE.match(text)
    body = text[fm_match.end():] if fm_match else ""
    for cite_key in CITE_RE.findall(body):
        if cite_key not in valid_cite_keys:
            errors.append(
                f"{md_path}: cite key '{cite_key}' not found in data/citations.yaml"
            )
    return errors


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]
    essays_dir = repo_root / "content" / "essays"
    citations_path = repo_root / "data" / "citations.yaml"
    valid_keys = set(parse_citations_yaml(citations_path.read_text(encoding="utf-8"))) if citations_path.exists() else set()

    errors: list[str] = []
    if essays_dir.exists():
        for essay_dir in sorted(essays_dir.iterdir()):
            if not essay_dir.is_dir():
                continue
            errors.extend(lint_essay(essay_dir, valid_keys, reg))

    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("Fixture lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All essay fixtures pass linter.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tools/test_check_fixtures.py -v`
Expected: PASS — `Ran 26 tests`, `OK`.

- [ ] **Step 5: Run the linter against the real repo, and its neighbours**

Run: `python3 tools/check_fixtures.py`
Expected: `All essay fixtures pass linter.`, exit 0.

Run: `python3 -m unittest tools/test_sections.py -v 2>&1 | tail -1`
Expected: `OK`.

Every other linter imports this module's parser, so re-run them all:

Run: `for t in research_fixtures streams_fixtures recipes_fixtures garden_fixtures works_fixtures library_fixtures math toc_depth citations garden_links research_links works_links; do printf '%s ' $t; python3 -m unittest tools/test_check_$t.py 2>&1 | tail -1; done`
Expected: `OK` after every name.

- [ ] **Step 6: Run the equivalence gate**

Write `$SCRATCH/eqgate.py` (overwrite any earlier copy) with exactly:

```python
#!/usr/bin/env python3
"""Throwaway equivalence gate for one fixture-linter migration. NOT committed.

Run from the repo root with the migration applied but uncommitted:

    python3 "$SCRATCH/eqgate.py" <linter_module>

"Before" is tools/ at HEAD (git archive); "after" is the working tree. Both
run() over the real content/ + data/ and over one mutated copy per entry in
MUTATIONS. Messages are normalized to (file, field, rule) so wording-only
changes vanish; everything else is printed. Exit 0 = no diff at all.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path.cwd()
LINTER = sys.argv[1]

# (label, relpath, op, *args)
#   frontmatter ops (top-level key):  drop KEY | set KEY RAW | add KEY RAW
#   library yaml ops (item N):        item-drop N KEY | item-set N KEY RAW
#                                     | extras-set N KEY RAW
MUTATIONS: list[tuple] = [
    ("drop title", "content/essays/example-one/index.md", "drop", "title"),
    ("drop has_math", "content/essays/example-one/index.md", "drop", "has_math"),
    ("bad tile_size", "content/essays/example-one/index.md", "set", "tile_size", "huge"),
    ("series without order", "content/essays/example-one/index.md", "set", "series_order", "0"),
    ("lastmod before date", "content/essays/example-one/index.md", "set", "lastmod", "2026-01-01"),
    ("hero missing", "content/essays/example-one/index.md", "set", "hero", "nope.svg"),
    ("unknown key (open section)", "content/essays/example-one/index.md", "add", "colophon", "yes"),
    ("multi_export without downloads", "content/essays/example-one/index.md", "add", "multi_export", "true"),
    ("toc not bool", "content/essays/example-one/index.md", "set", "toc", "yes"),
    ("series_order not int", "content/essays/example-one/index.md", "set", "series_order", "first"),
    ("tags scalar", "content/essays/example-one/index.md", "set", "tags", "example"),
    ("bad date", "content/essays/example-one/index.md", "set", "date", "someday"),
    ("featured not bool", "content/essays/example-one/index.md", "set", "featured", "\"yes\""),
]

RUNNER = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import importlib\n"
    "m = importlib.import_module(sys.argv[2])\n"
    "res = m.run(Path(sys.argv[3]))\n"
    "print(json.dumps({'rc': res[0], 'errs': [str(e) for e in res[1]]}))\n"
)

# First match wins; group 1 is the field. Unmatched messages are compared
# verbatim as rule "code" (cross-field / structured / format rules that the
# migration must leave byte-identical).
PATTERNS = [
    (r"missing required field '([\w.]+)'", "missing"),
    (r"'(\w+)' is required for \w+ notes", "missing"),
    (r"([\w.]+) missing$", "missing"),
    (r"unknown field '([\w.]+)'", "unknown"),
    (r"forbidden field '(\w+)' on theme", "unknown"),
    (r"'(\w+)' not permitted on \w+ notes", "unknown"),
    (r"(extras\.\w+) not allowed for media_type", "unknown"),
    (r"([\w.\[\]]+)='.*' not (?:in|allowed in)\b", "enum"),
    (r"(tile_size) '.*' not in", "enum"),
    (r"([\w.]+)='.*' is not a valid YYYY-MM-DD date", "type"),
    (r"(\w+) not YYYY-MM-DD", "type"),
    (r"([\w.]+\[\d+\]) must be a string", "type"),
    (r"(tags) must be a list \(may be empty\)", "type"),
    (r"(canonical_url) must be https", "type"),
    (r"(extras\.\w+) must be (?:10 or 13|a positive|an absolute|a relative|a non-empty)", "type"),
    (r"([\w.]+) must be (?:an integer|a non-negative integer|int\b|a boolean|bool\b"
     r"|a list\b|a string|a mapping|a dict|a YYYY-MM-DD date)", "type"),
]


def norm(msg: str) -> tuple[str, str, str]:
    file, sep, rest = msg.partition(": ")
    if not sep:
        return ("", msg, "code")
    for pat, rule in PATTERNS:
        m = re.match(pat, rest)
        if m:
            return (file, m.group(1).removeprefix("extras."), rule)
    return (file, rest, "code")


def run_side(tools: Path, root: Path) -> tuple[int, set]:
    p = subprocess.run([sys.executable, "-c", RUNNER, str(tools), LINTER, str(root)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"runner crashed under {tools}:\n{p.stderr}")
    out = json.loads(p.stdout.strip().splitlines()[-1])
    return out["rc"], {norm(e) for e in out["errs"]}


def _fm_end(lines: list[str]) -> int:
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return i
    sys.exit("frontmatter not closed")


def _block_end(lines: list[str], i: int, stop: int, indent: str) -> int:
    j = i + 1
    while j < stop and lines[j].startswith(indent + " "):
        j += 1
    return j


def _item_bounds(lines: list[str], n: int) -> tuple[int, int]:
    starts = [i for i, l in enumerate(lines) if l.startswith("  - ")]
    s = starts[n]
    e = starts[n + 1] if n + 1 < len(starts) else len(lines)
    return s, e


def mutate(root: Path, rel: str, op: str, args: tuple) -> None:
    p = root / rel
    lines = p.read_text().split("\n")
    if op in ("drop", "set", "add"):
        end = _fm_end(lines)
        key = args[0]
        idx = next((i for i in range(1, end) if lines[i].startswith(key + ":")), None)
        if op == "add":
            lines.insert(end, f"{key}: {args[1]}")
        else:
            if idx is None:
                sys.exit(f"{rel}: no top-level key '{key}'")
            j = _block_end(lines, idx, end, "")
            lines[idx:j] = [] if op == "drop" else [f"{key}: {args[1]}"]
    else:
        n, key = int(args[0]), args[1]
        s, e = _item_bounds(lines, n)
        idx = next((i for i in range(s, e)
                    if lines[i].startswith(f"    {key}:") or lines[i].startswith(f"  - {key}:")), None)
        if op == "item-drop":
            if idx is None:
                sys.exit(f"{rel}[{n}]: no key '{key}'")
            lines[idx:_block_end(lines, idx, e, "    ")] = []
        elif op == "item-set":
            lead = "  - " if idx is not None and lines[idx].startswith("  - ") else "    "
            if idx is None:
                lines.insert(e, f"    {key}: {args[2]}")
            else:
                lines[idx:_block_end(lines, idx, e, "    ")] = [f"{lead}{key}: {args[2]}"]
        elif op == "extras-set":
            ex = next((i for i in range(s, e) if lines[i].rstrip() == "    extras:"), None)
            if ex is None:
                lines.insert(e, "    extras:")
                ex = e
            j = ex + 1
            while j < len(lines) and lines[j].startswith("      "):
                j += 1
            # Appended last, so it wins over an existing value for the key.
            lines.insert(j, f"      {key}: {args[2]}")
        else:
            sys.exit(f"unknown op {op}")
    p.write_text("\n".join(lines))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="eqgate-"))
    subprocess.run(f"git archive HEAD tools data/sections.json | tar -x -C {tmp}",
                   shell=True, check=True, cwd=REPO)
    old_tools = tmp / "tools"
    new_tools = REPO / "tools"
    cases = [("real repo", REPO)]
    for k, (label, rel, op, *args) in enumerate(MUTATIONS):
        root = tmp / f"m{k}"
        shutil.copytree(REPO / "content", root / "content")
        shutil.copytree(REPO / "data", root / "data")
        mutate(root, rel, op, tuple(args))
        cases.append((label, root))
    diffs = 0
    for label, root in cases:
        rc_b, before = run_side(old_tools, root)
        rc_a, after = run_side(new_tools, root)
        gone, new = sorted(before - after), sorted(after - before)
        if rc_b != rc_a or gone or new:
            diffs += 1
            print(f"DIFF [{label}] rc {rc_b} -> {rc_a}")
            for sign, ts in (("-", gone), ("+", new)):
                for f, field, rule in ts:
                    where = f.replace(f"{root}/", "")
                    print(f"   {sign} {field} ({rule}) @ {where}")
        else:
            print(f"same [{label}] rc {rc_b}, {len(before)} violation(s)")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{diffs} case(s) differ")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run (repo root, migration uncommitted): `python3 "$SCRATCH/eqgate.py" check_fixtures`
Expected: every case prints `same [...]` except exactly these, which are the intended behaviour changes recorded in the commit message (exit 1 is expected while they are present):

| Case | Diff |
|---|---|
| `toc not bool` | `+ toc (type)` |
| `series_order not int` | `+ series_order (type)` |
| `tags scalar` | `+ tags (type)` |
| `bad date` | `+ date (type)` |
| `featured not bool` | `+ featured (type)` |

The last line reads `5 case(s) differ`. Any other `DIFF` is a regression: fix the linter (not the gate) and re-run. `same [real repo] rc 0, 0 violation(s)` must be the first line.

- [ ] **Step 7: Commit**

```bash
git add tools/check_fixtures.py tools/test_check_fixtures.py
git commit -m "$(cat <<'MSG'
refactor(tools): essay fixture linter reads data/sections.json

Essay frontmatter is checked by sections.check_fields against the essays
registry entry, an open section (closed: false) as before: undeclared keys
still pass. tile_size's message changes from a set repr to the canonical
sorted list. The series/hero/downloads/lastmod/cite rules stay as code.

Equivalence gate (real tree + 13 mutations): the open-set case is
unchanged; intended behaviour changes — declared keys are now
type-checked (toc/has_*/featured/multi_export as bools, series_order as an
int, tags as a list, date/lastmod as dates, text keys as strings), where
the old linter checked presence only.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
)"
```

### Task 6: Migrate `check_garden_fixtures.py`

**Files:**
- Modify: `tools/check_garden_fixtures.py` (full rewrite, lines 1-203)
- Test: `tools/test_check_garden_fixtures.py` (modify)

**Interfaces:**
- Consumes: `sections.check_fields(fm, section_name, path, registry=None) -> list[str]`, `sections.default_registry() -> dict`, `sections.SectionsError`, `sections.case_of(fm, section_name, registry=None) -> str | None`, `sections.DATE_PREFIX_RE` (Task 1).
- Produces:
  - `derive_flavor(fm: dict[str, object], registry: dict | None = None) -> str` — `'concept' | 'media' | 'reference' | 'unknown'`
  - `lint_note(note_dir: Path, registry: dict | None = None) -> tuple[list[str], dict[str, object] | None]`
  - `run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]`

Constants and code deleted: `ALWAYS_REQUIRED`, `GROWTH_STAGES`, `STATUSES`, `SPOILER_LEVELS`, `MEDIA_TYPES`, `REFERENCE_TYPES`, `ALL_MEDIA_TYPES`, `CONCEPT_FIELDS`, `MEDIA_FIELDS`, `REFERENCE_FIELDS`, `MEDIA_REQUIRED_EXTRA`, `REFERENCE_REQUIRED_EXTRA`, and the inline required/enum/permitted-field checks. The future-date rule, the URL-scheme rule, topic_map resolution and the bare-date rule (re-expressed as "an ISO-prefixed *string* is not a bare date", since `parse_scalar` turns bare dates into `date` objects) stay.

- [ ] **Step 1: Write the failing tests**

In `tools/test_check_garden_fixtures.py`:

**1a.** Replace the module header (from the first line through `from test_helpers import TempRepo as _TempRepo  # noqa: E402`):

```python
"""Tests for check_garden_fixtures.py — run with:
   python3 -m unittest tools/test_check_garden_fixtures.py -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_garden_fixtures as lint  # noqa: E402
from test_helpers import TempRepo as _TempRepo  # noqa: E402
```

with:

```python
"""Tests for check_garden_fixtures.py — run with:
   python3 -m unittest tools/test_check_garden_fixtures.py -v
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_garden_fixtures as lint  # noqa: E402
from test_helpers import TempRepo as _TempRepo  # noqa: E402
```

**1b.** Reword an assertion on the old message (refinement 1). Replace:

```python
        self.assertTrue(any("status" in e and "concept" in e for e in errors))
```

with:

```python
        self.assertTrue(any(e.endswith(": unknown field 'status'") for e in errors), errors)
```

**1c.** Reword an assertion on the old message (refinement 1). Replace:

```python
        self.assertTrue(any("status" in e and "reference" in e for e in errors))
```

with:

```python
        self.assertTrue(any(e.endswith(": unknown field 'status'") for e in errors), errors)
```

**1d.** Reword an assertion on the old message (refinement 1). Replace:

```python
        self.assertTrue(any("last_modified" in e and "not a valid" in e for e in errors))
```

with:

```python
        self.assertTrue(any(e.endswith(": last_modified must be a YYYY-MM-DD date") for e in errors), errors)
```

**1e.** Reword an assertion on the old message (refinement 1). Replace:

```python
        self.assertTrue(any("started" in e and "not a valid" in e for e in errors))
```

with:

```python
        self.assertTrue(any(e.endswith(": started must be a YYYY-MM-DD date") for e in errors), errors)
```

**1f.** Reword an assertion on the old message (refinement 1). Replace:

```python
        self.assertTrue(any("finished" in e and "not a valid" in e for e in errors))
```

with:

```python
        self.assertTrue(any(e.endswith(": finished must be a YYYY-MM-DD date") for e in errors), errors)
```

**1g.** Insert this class above the trailing `if __name__ == "__main__":` block (two blank lines before and after):

```python
class GardenRegistryTest(unittest.TestCase):
    """Flavors are registry variants on media_type (data/sections.json)."""

    def setUp(self) -> None:
        self.repo = TempRepo()

    def tearDown(self) -> None:
        self.repo.cleanup()

    def test_empty_media_type_selects_concept(self) -> None:
        # derive_flavor treated a falsy media_type as concept; so does the
        # registry's null case — and media_type itself is then not permitted.
        self.repo.write_note("n", CONCEPT_NOTE.replace("growth_stage: seedling\n",
                                                       "growth_stage: seedling\nmedia_type:\n"))
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any(e.endswith(": unknown field 'media_type'") for e in errors), errors)

    def test_unknown_media_type_skips_flavor_checks(self) -> None:
        broken = MEDIA_NOTE.replace("media_type: book", "media_type: scroll").replace(
            'original_url: "https://example.invalid/book"', 'original_url: "ftp://x"')
        self.repo.write_note("n", broken)
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("media_type='scroll' not in ['album', 'article', 'book'", errors[0])

    def test_weight_is_concept_only(self) -> None:
        self.repo.write_note("n", MEDIA_NOTE.replace("year: 1972\n", "year: 1972\nweight: 3\n"))
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any(e.endswith(": unknown field 'weight'") for e in errors), errors)

    def test_empty_started_now_fails(self) -> None:
        # The old date loop skipped "" values; a declared date must be a date.
        self.repo.write_note("n", MEDIA_NOTE.replace("started: 2025-12-15", "started:"))
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any(e.endswith(": started must be a YYYY-MM-DD date") for e in errors), errors)

    def test_datetime_string_last_modified_still_fails(self) -> None:
        # The registry's date type accepts an ISO-prefixed string (streams
        # need it); garden keeps its bare-date rule in code.
        self.repo.write_note("n", CONCEPT_NOTE.replace("last_modified: 2026-04-22",
                                                       "last_modified: 2026-04-22T10:00:00"))
        rc, errors = lint.run(self.repo.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("last_modified='2026-04-22T10:00:00' is not a valid" in e
                            for e in errors), errors)

    def test_media_types_come_from_the_registry(self) -> None:
        reg = copy.deepcopy(lint.sections.default_registry())
        cases = reg["sections"]["garden"]["variants"]["cases"]
        cases["media"]["values"] = ["album"]
        cases["media"]["fields"]["media_type"]["values"] = ["album"]
        self.repo.write_note("n", MEDIA_NOTE)
        rc, errors = lint.run(self.repo.root, registry=reg)
        self.assertEqual(rc, 1)
        self.assertTrue(any("media_type='book' not in" in e for e in errors), errors)

    def test_run_fails_closed_when_the_registry_cannot_load(self) -> None:
        self.repo.write_note("n", CONCEPT_NOTE)
        boom = lint.sections.SectionsError("sections: registry not found at X")
        with mock.patch.object(lint.sections, "default_registry", side_effect=boom):
            self.assertEqual(lint.run(self.repo.root), (1, ["sections: registry not found at X"]))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tools/test_check_garden_fixtures.py -v`
Expected: FAIL (failures=8, errors=2): the 5 reworded assertions (`test_concept_with_status_fails`, `test_reference_with_status_fails`, `test_malformed_last_modified_fails`, `test_malformed_started_fails`, `test_malformed_finished_fails`) plus `test_empty_media_type_selects_concept`, `test_weight_is_concept_only`, `test_empty_started_now_fails` fail with `AssertionError`; `test_media_types_come_from_the_registry` and `test_run_fails_closed_when_the_registry_cannot_load` error with `AttributeError: module 'check_garden_fixtures' has no attribute 'sections'`. `test_unknown_media_type_skips_flavor_checks` and `test_datetime_string_last_modified_still_fails` already pass (they pin behaviour that must survive).

- [ ] **Step 3: Rewrite `tools/check_garden_fixtures.py`**

Replace the whole file with:

```python
#!/usr/bin/env python3
"""Garden note fixture frontmatter linter.

Walks `content/garden/<slug>/index.md` (skips `_index.md`), validates
flavor-specific frontmatter per spec §5.1 against the `garden` entry of
data/sections.json (sections.check_fields), and verifies that every
`topic_map:` entry resolves to an existing non-draft note.

Exits 0 on all-pass, 1 on any violation. Stdlib only — imports the YAML
parser from check_fixtures so both linters share one parser.
"""
from __future__ import annotations

import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_frontmatter  # noqa: E402
import sections  # noqa: E402

# --- contract ---
#
# Field sets, enums, types and the concept/media/reference flavors (variants
# on `media_type`) live in data/sections.json (spec 2026-10-20). What stays
# here: the future-date and URL-scheme rules and topic_map resolution.


def derive_flavor(fm: dict[str, object], registry: dict | None = None) -> str:
    """'concept' | 'media' | 'reference', or 'unknown' for an unlisted media_type."""
    return sections.case_of(fm, "garden", registry) or "unknown"


def lint_note(note_dir: Path, registry: dict | None = None) -> tuple[list[str], dict[str, object] | None]:
    """Return (errors, parsed_frontmatter_or_None) for a single note dir."""
    md = note_dir / "index.md"
    if not md.exists():
        return [f"{note_dir}: no index.md"], None
    text = md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        return [f"{md}: no frontmatter"], None

    errors = sections.check_fields(fm, "garden", md, registry=registry)

    # The registry's `date` accepts any ISO-date-prefixed string (stream
    # datetimes). Garden dates must be bare dates, which parse_scalar turns
    # into date objects; flag the prefixed strings the registry let through.
    for date_field in ("last_modified", "started", "finished"):
        val = fm.get(date_field)
        if isinstance(val, str) and sections.DATE_PREFIX_RE.match(val):
            errors.append(f"{md}: {date_field}='{val}' is not a valid YYYY-MM-DD date")

    last_modified = fm.get("last_modified")
    if isinstance(last_modified, Date) and last_modified > Date.today():
        errors.append(f"{md}: last_modified {last_modified} is in the future")

    # An unlisted media_type leaves the flavor — and so the legal field set —
    # unknown; the registry has already reported it. Stop, as before.
    if derive_flavor(fm, registry) == "unknown":
        return errors, fm

    # URL scheme check
    url = fm.get("original_url")
    if url and not (str(url).startswith("http://") or str(url).startswith("https://")):
        errors.append(f"{md}: original_url must be http(s)")

    return errors, fm


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    garden_dir = repo_root / "content" / "garden"
    errors: list[str] = []

    if not garden_dir.exists():
        return 0, []
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]

    # Pass 1: lint each note, build the slug → frontmatter index
    notes: dict[str, dict[str, object]] = {}
    for entry in sorted(garden_dir.iterdir()):
        if not entry.is_dir():
            continue
        slug = entry.name
        if slug.startswith("_"):
            continue
        # Skip section directories (have _index.md but no index.md) — e.g.,
        # /history/ is a Hugo section, not a note. The note linter expects
        # a per-slug index.md and would false-fail on these.
        if (entry / "_index.md").is_file() and not (entry / "index.md").is_file():
            continue
        note_errors, fm = lint_note(entry, reg)
        errors.extend(note_errors)
        if fm is not None:
            notes[slug] = fm

    # Pass 2: validate every topic_map entry resolves to an existing
    # non-draft note in the index
    for slug, fm in notes.items():
        topic_map = fm.get("topic_map")
        if not isinstance(topic_map, list):
            continue
        for i, entry_slug in enumerate(topic_map):
            target = notes.get(str(entry_slug))
            owner_md = garden_dir / slug / "index.md"
            if target is None:
                errors.append(
                    f"{owner_md}: topic_map[{i}]='{entry_slug}' "
                    f"does not resolve to an existing note"
                )
                continue
            if target.get("draft") is True:
                errors.append(
                    f"{owner_md}: topic_map[{i}]='{entry_slug}' "
                    f"is a draft; drafts cannot be in published topic maps"
                )

    return (1 if errors else 0, errors)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errors = run(repo_root)
    if errors:
        print("Garden fixture lint failures:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All garden fixtures pass linter.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tools/test_check_garden_fixtures.py -v`
Expected: PASS — `Ran 34 tests`, `OK`.

- [ ] **Step 5: Run the linter against the real repo, and its neighbours**

Run: `python3 tools/check_garden_fixtures.py`
Expected: `All garden fixtures pass linter.`, exit 0.

Run: `python3 -m unittest tools/test_sections.py -v 2>&1 | tail -1`
Expected: `OK`.

- [ ] **Step 6: Run the equivalence gate**

Write `$SCRATCH/eqgate.py` (overwrite any earlier copy) with exactly:

```python
#!/usr/bin/env python3
"""Throwaway equivalence gate for one fixture-linter migration. NOT committed.

Run from the repo root with the migration applied but uncommitted:

    python3 "$SCRATCH/eqgate.py" <linter_module>

"Before" is tools/ at HEAD (git archive); "after" is the working tree. Both
run() over the real content/ + data/ and over one mutated copy per entry in
MUTATIONS. Messages are normalized to (file, field, rule) so wording-only
changes vanish; everything else is printed. Exit 0 = no diff at all.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path.cwd()
LINTER = sys.argv[1]

# (label, relpath, op, *args)
#   frontmatter ops (top-level key):  drop KEY | set KEY RAW | add KEY RAW
#   library yaml ops (item N):        item-drop N KEY | item-set N KEY RAW
#                                     | extras-set N KEY RAW
MUTATIONS: list[tuple] = [
    ("drop growth_stage", "content/garden/story-atoms/index.md", "drop", "growth_stage"),
    ("bad growth_stage", "content/garden/story-atoms/index.md", "set", "growth_stage", "enormous"),
    ("concept with status", "content/garden/story-atoms/index.md", "add", "status", "reading"),
    ("concept with started", "content/garden/story-atoms/index.md", "add", "started", "2026-01-01"),
    ("concept with bad started", "content/garden/story-atoms/index.md", "add", "started", "2026-1-1"),
    ("concept empty media_type", "content/garden/story-atoms/index.md", "add", "media_type", "\"\""),
    ("future last_modified", "content/garden/story-atoms/index.md", "set", "last_modified", "2099-01-01"),
    ("bad last_modified", "content/garden/story-atoms/index.md", "set", "last_modified", "not-a-date"),
    ("media drop status", "content/garden/invisible-cities/index.md", "drop", "status"),
    ("media drop creator", "content/garden/invisible-cities/index.md", "drop", "creator"),
    ("media bad status", "content/garden/invisible-cities/index.md", "set", "status", "pondering"),
    ("media bad spoiler", "content/garden/invisible-cities/index.md", "set", "spoiler_level", "extreme"),
    ("media bad started", "content/garden/invisible-cities/index.md", "set", "started", "2025-1-1"),
    ("media empty started", "content/garden/invisible-cities/index.md", "set", "started", "\"\""),
    ("media with weight", "content/garden/invisible-cities/index.md", "add", "weight", "3"),
    ("unknown media_type", "content/garden/invisible-cities/index.md", "set", "media_type", "scroll"),
    ("ftp url", "content/garden/invisible-cities/index.md", "set", "original_url", "\"ftp://x\""),
    ("reference with status", "content/garden/nguyen-2020-games-as-art/index.md", "add", "status", "reading"),
    ("reference drop creator", "content/garden/nguyen-2020-games-as-art/index.md", "drop", "creator"),
    ("topic_map unresolved", "content/garden/story-atoms/index.md", "add", "topic_map", "[does-not-exist]"),
    ("year not int", "content/garden/invisible-cities/index.md", "set", "year", "\"1972\""),
    ("tags scalar", "content/garden/story-atoms/index.md", "set", "tags", "narrative"),
    ("datetime last_modified", "content/garden/story-atoms/index.md", "set", "last_modified", "2026-04-29T10:00:00"),
    ("quoted last_modified", "content/garden/story-atoms/index.md", "set", "last_modified", "\"2026-04-29\""),
]

RUNNER = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import importlib\n"
    "m = importlib.import_module(sys.argv[2])\n"
    "res = m.run(Path(sys.argv[3]))\n"
    "print(json.dumps({'rc': res[0], 'errs': [str(e) for e in res[1]]}))\n"
)

# First match wins; group 1 is the field. Unmatched messages are compared
# verbatim as rule "code" (cross-field / structured / format rules that the
# migration must leave byte-identical).
PATTERNS = [
    (r"missing required field '([\w.]+)'", "missing"),
    (r"'(\w+)' is required for \w+ notes", "missing"),
    (r"([\w.]+) missing$", "missing"),
    (r"unknown field '([\w.]+)'", "unknown"),
    (r"forbidden field '(\w+)' on theme", "unknown"),
    (r"'(\w+)' not permitted on \w+ notes", "unknown"),
    (r"(extras\.\w+) not allowed for media_type", "unknown"),
    (r"([\w.\[\]]+)='.*' not (?:in|allowed in)\b", "enum"),
    (r"(tile_size) '.*' not in", "enum"),
    (r"([\w.]+)='.*' is not a valid YYYY-MM-DD date", "type"),
    (r"(\w+) not YYYY-MM-DD", "type"),
    (r"([\w.]+\[\d+\]) must be a string", "type"),
    (r"(tags) must be a list \(may be empty\)", "type"),
    (r"(canonical_url) must be https", "type"),
    (r"(extras\.\w+) must be (?:10 or 13|a positive|an absolute|a relative|a non-empty)", "type"),
    (r"([\w.]+) must be (?:an integer|a non-negative integer|int\b|a boolean|bool\b"
     r"|a list\b|a string|a mapping|a dict|a YYYY-MM-DD date)", "type"),
]


def norm(msg: str) -> tuple[str, str, str]:
    file, sep, rest = msg.partition(": ")
    if not sep:
        return ("", msg, "code")
    for pat, rule in PATTERNS:
        m = re.match(pat, rest)
        if m:
            return (file, m.group(1).removeprefix("extras."), rule)
    return (file, rest, "code")


def run_side(tools: Path, root: Path) -> tuple[int, set]:
    p = subprocess.run([sys.executable, "-c", RUNNER, str(tools), LINTER, str(root)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"runner crashed under {tools}:\n{p.stderr}")
    out = json.loads(p.stdout.strip().splitlines()[-1])
    return out["rc"], {norm(e) for e in out["errs"]}


def _fm_end(lines: list[str]) -> int:
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return i
    sys.exit("frontmatter not closed")


def _block_end(lines: list[str], i: int, stop: int, indent: str) -> int:
    j = i + 1
    while j < stop and lines[j].startswith(indent + " "):
        j += 1
    return j


def _item_bounds(lines: list[str], n: int) -> tuple[int, int]:
    starts = [i for i, l in enumerate(lines) if l.startswith("  - ")]
    s = starts[n]
    e = starts[n + 1] if n + 1 < len(starts) else len(lines)
    return s, e


def mutate(root: Path, rel: str, op: str, args: tuple) -> None:
    p = root / rel
    lines = p.read_text().split("\n")
    if op in ("drop", "set", "add"):
        end = _fm_end(lines)
        key = args[0]
        idx = next((i for i in range(1, end) if lines[i].startswith(key + ":")), None)
        if op == "add":
            lines.insert(end, f"{key}: {args[1]}")
        else:
            if idx is None:
                sys.exit(f"{rel}: no top-level key '{key}'")
            j = _block_end(lines, idx, end, "")
            lines[idx:j] = [] if op == "drop" else [f"{key}: {args[1]}"]
    else:
        n, key = int(args[0]), args[1]
        s, e = _item_bounds(lines, n)
        idx = next((i for i in range(s, e)
                    if lines[i].startswith(f"    {key}:") or lines[i].startswith(f"  - {key}:")), None)
        if op == "item-drop":
            if idx is None:
                sys.exit(f"{rel}[{n}]: no key '{key}'")
            lines[idx:_block_end(lines, idx, e, "    ")] = []
        elif op == "item-set":
            lead = "  - " if idx is not None and lines[idx].startswith("  - ") else "    "
            if idx is None:
                lines.insert(e, f"    {key}: {args[2]}")
            else:
                lines[idx:_block_end(lines, idx, e, "    ")] = [f"{lead}{key}: {args[2]}"]
        elif op == "extras-set":
            ex = next((i for i in range(s, e) if lines[i].rstrip() == "    extras:"), None)
            if ex is None:
                lines.insert(e, "    extras:")
                ex = e
            j = ex + 1
            while j < len(lines) and lines[j].startswith("      "):
                j += 1
            # Appended last, so it wins over an existing value for the key.
            lines.insert(j, f"      {key}: {args[2]}")
        else:
            sys.exit(f"unknown op {op}")
    p.write_text("\n".join(lines))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="eqgate-"))
    subprocess.run(f"git archive HEAD tools data/sections.json | tar -x -C {tmp}",
                   shell=True, check=True, cwd=REPO)
    old_tools = tmp / "tools"
    new_tools = REPO / "tools"
    cases = [("real repo", REPO)]
    for k, (label, rel, op, *args) in enumerate(MUTATIONS):
        root = tmp / f"m{k}"
        shutil.copytree(REPO / "content", root / "content")
        shutil.copytree(REPO / "data", root / "data")
        mutate(root, rel, op, tuple(args))
        cases.append((label, root))
    diffs = 0
    for label, root in cases:
        rc_b, before = run_side(old_tools, root)
        rc_a, after = run_side(new_tools, root)
        gone, new = sorted(before - after), sorted(after - before)
        if rc_b != rc_a or gone or new:
            diffs += 1
            print(f"DIFF [{label}] rc {rc_b} -> {rc_a}")
            for sign, ts in (("-", gone), ("+", new)):
                for f, field, rule in ts:
                    where = f.replace(f"{root}/", "")
                    print(f"   {sign} {field} ({rule}) @ {where}")
        else:
            print(f"same [{label}] rc {rc_b}, {len(before)} violation(s)")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{diffs} case(s) differ")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run (repo root, migration uncommitted): `python3 "$SCRATCH/eqgate.py" check_garden_fixtures`
Expected: every case prints `same [...]` except exactly these, which are the intended behaviour changes recorded in the commit message (exit 1 is expected while they are present):

| Case | Diff |
|---|---|
| `concept with bad started` | `- started (type)` |
| `media empty started` | `+ started (type)` |
| `year not int` | `+ year (type)` |
| `tags scalar` | `+ tags (type)` |

The last line reads `4 case(s) differ`. Any other `DIFF` is a regression: fix the linter (not the gate) and re-run. `same [real repo] rc 0, 0 violation(s)` must be the first line.

- [ ] **Step 7: Commit**

```bash
git add tools/check_garden_fixtures.py tools/test_check_garden_fixtures.py
git commit -m "$(cat <<'MSG'
refactor(tools): garden fixture linter reads data/sections.json

Garden flavors become registry variants on media_type: concept (absent
or empty), media, reference. Wording moves to the canonical messages:
`'f' is required for media notes` -> `missing required field 'f'`,
`'f' not permitted on concept notes` -> `unknown field 'f'`, and a
malformed date -> `f must be a YYYY-MM-DD date`. The bare-date rule, the
future-date rule, the URL scheme rule and topic_map resolution stay.

Equivalence gate (real tree + 24 mutations): intended behaviour changes —
- a malformed date on a field the flavor does not permit (e.g. started on
  a concept note) is reported once, as unknown, not also as a bad date
- an empty `started:` ("") now fails (the old date loop skipped "")
- year and weight are now type-checked as integers
- tags / topic_map are now type-checked as lists

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
)"
```

### Task 7: Migrate `check_works_fixtures.py` (drop `load_vocab`)

**Files:**
- Modify: `tools/check_works_fixtures.py` (full rewrite, lines 1-309)
- Test: `tools/test_check_works_fixtures.py` (modify)

**Interfaces:**
- Consumes: `sections.check_fields(fm, section_name, path, registry=None) -> list[str]`, `sections.default_registry() -> dict`, `sections.SectionsError` (Task 1).
- Produces:
  - `lint_file(md: Path, registry: dict | None = None) -> list[str]`
  - `run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]`
  - `SUB_SECTIONS = ("games", "music", "poetry")`

Constants and code deleted: `TILE_SIZES`, `POEM_REQUIRED`, `POEM_OPTIONAL`, `VOCAB_REL`, `_VOCAB_ENUM_KEYS`, `_VOCAB_FIELD_KEYS`, `_VOCAB_KEYS`, `VocabError`, `load_vocab`, `game_fields`, `music_fields`, `poem_fields`, `_validate_umbrella_fields`, `_lint_game`, `_lint_music`, `_lint_poem`, and the `import json`. The `tracks` shape check survives as `_lint_tracks`.

- [ ] **Step 1: Write the failing tests**

In `tools/test_check_works_fixtures.py`, make four edits.

**1a.** Replace everything above `class WorksFixturesLinterTests(unittest.TestCase):` (lines 1-103: the docstring, imports, fixtures, `VOCAB`, `_LIVE`, `_vocab_json`) with:

```python
"""Tests for check_works_fixtures.py — run with:
   python3 -m unittest tools/test_check_works_fixtures.py -v
"""
from __future__ import annotations

import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_works_fixtures as lint  # noqa: E402
import sections  # noqa: E402
from test_helpers import TempRepo  # noqa: E402


GAME_VALID = """\
---
title: "Example Game"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
status: playable
game_kind: full-release
tagline: "Example tagline."
year: 2026
---

Body.
"""

MUSIC_VALID = """\
---
title: "Example Album"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
format: album
year: 2026
---

Body.
"""

# Minimal valid game fixture with status: playable — used by the registry
# tests below, where TempRepo writes it at an arbitrary path (not necessarily
# "ok") rather than through self._write's games/<slug> convention.
GAME_MD_PLAYABLE = GAME_VALID

REPO_ROOT = Path(__file__).resolve().parent.parent

POEM_VALID = """\
---
title: "Example Poem"
date: 2026-01-01
lastmod: 2026-01-02
draft: false
lines: 14
---

Body.
"""


def _registry(**enum_overrides) -> dict:
    """The live registry with the works enums pinned — a fixture, not a copy.

    The ENUM values are hand-written: a test asserting that "shipped" is
    rejected must control the set it is rejected against, or a later addition
    to the real registry would quietly change what the test means. The FIELD
    SETS are deliberately NOT written out: data/sections.json is their single
    home, shared with the elisp normalizer's allowed-key filter, and a
    transcription here would be exactly the third copy that made the old
    elisp `-key-set-matches-contract` tests vacuous.
    """
    reg = copy.deepcopy(sections.load(REPO_ROOT))
    s = reg["sections"]
    enums = {
        ("works/games", "status"): ["playable", "in-progress", "archived"],
        ("works/games", "game_kind"): ["full-release", "jam", "research-prototype", "experiment"],
        ("works/music", "format"): ["album", "track", "experiment", "live"],
    }
    enums.update(enum_overrides.pop("enums", {}))
    for (sec, field), values in enums.items():
        s[sec]["fields"][field]["values"] = values
    s["works/music"]["fields"]["platform_embed"]["fields"]["kind"]["values"] = (
        enum_overrides.pop("platform_kinds", ["bandcamp", "soundcloud", "youtube"]))
    assert not enum_overrides, enum_overrides
    return reg


# Threaded explicitly into every direct lint_file() call in this file.
REG = _registry()
```

**1b.** In `WorksFixturesLinterTests.setUp`, delete this block (the vocabulary copy; nothing replaces it):

```python
        # lint.run() fails closed on a missing vocab file (see
        # test_missing_vocab_fails_closed below); seed a real one here so
        # every pre-existing test that goes through run() (test_runner_*)
        # keeps passing. Direct lint_file() calls elsewhere in this file
        # thread the module-level VOCAB constant explicitly instead — they
        # never touch this tempdir's copy or the live repo's.
        (self.tmp / "data").mkdir(parents=True)
        shutil.copyfile(
            REPO_ROOT / lint.VOCAB_REL, self.tmp / "data" / "works-vocab.json"
        )
```

**1c.** Point every direct call at the registry fixture:

```bash
sed -i '' 's/lint.lint_file(p, VOCAB)/lint.lint_file(p, REG)/' tools/test_check_works_fixtures.py
grep -c 'lint.lint_file(p, REG)' tools/test_check_works_fixtures.py   # expect 28
grep -c 'VOCAB' tools/test_check_works_fixtures.py                     # expect 0
```

**1d.** Replace everything from `    # --- shared enum vocabulary (single-sourced with the elisp linter) ---` down to (not including) the blank lines before `if __name__ == "__main__":` — the seven vocabulary tests `test_vocab_is_single_source` … `test_umbrella_optional_is_shared_by_all_three_sub_sections` — with:

```python
    # --- the contract is the registry's (data/sections.json) ---

    def test_registry_is_single_source(self):
        """Mutating the registry must change what the linter accepts."""
        repo = TempRepo()
        try:
            repo.write("content/works/games/g/index.md", GAME_MD_PLAYABLE)
            reg = _registry(enums={("works/games", "status"): ["playible"]})  # deliberate typo
            code, errs = lint.run(repo.root, registry=reg)
            self.assertEqual(code, 1)
            self.assertTrue(any("status='playable'" in e for e in errs), errs)
        finally:
            repo.cleanup()

    def _run_against_registry_file(self, text: str | None) -> tuple[int, list[str]]:
        """run() over a one-game tree with this tree's registry replaced."""
        site, repo = TempRepo(), TempRepo()
        try:
            if text is not None:
                site.write("data/sections.json", text)
            repo.write("content/works/games/g/index.md", GAME_MD_PLAYABLE)
            with mock.patch.object(sections, "SITE_ROOT", site.root), \
                    mock.patch.object(sections, "_CACHE", {}):
                return lint.run(repo.root)
        finally:
            site.cleanup()
            repo.cleanup()

    def test_missing_registry_fails_closed(self):
        """A missing registry must fail, never fall back to a hardcoded copy.

        Reported through the uniform `(rc, errs)` seam rather than by
        `sys.exit` from inside `run()`: an aggregator importing this module
        must not have the process pulled out from under it.
        """
        code, errs = self._run_against_registry_file(None)
        self.assertEqual(code, 1)
        self.assertEqual(len(errs), 1)
        self.assertIn("registry not found at", errs[0])

    def test_run_never_exits_the_process_on_a_bad_registry(self):
        """Malformed JSON is a returned error too, not a SystemExit."""
        code, errs = self._run_against_registry_file("{ not json")
        self.assertEqual(code, 1)
        self.assertIn("is not valid JSON", errs[0])

    def test_poetry_only_tree_needs_no_seeded_registry(self):
        """The registry belongs to the code tree, not the content tree.

        data/works-vocab.json had to be seeded into every works-touching temp
        site root (tools/test_publish_integration.py's
        TestPoetryPublishDeliberate included). sections.json is read from this
        repository, so a bare poetry-only tree lints clean as-is.
        """
        repo = TempRepo()
        try:
            repo.write("content/works/poetry/p/index.md", POEM_VALID)
            self.assertEqual(lint.run(repo.root), (0, []))
        finally:
            repo.cleanup()

    def test_field_sets_come_from_the_registry(self):
        """Dropping an optional key from the registry makes it an unknown field.

        This is what makes data/sections.json the single home of the
        emitted-key contract that the elisp normalizer filters against. If
        this module ever re-hardcodes a field set, the fixture below keeps
        passing and the guard is gone.
        """
        repo = TempRepo()
        try:
            reg = _registry()
            del reg["sections"]["works/games"]["fields"]["length"]
            repo.write(
                "content/works/games/g/index.md",
                GAME_VALID.replace("year: 2026\n", "year: 2026\nlength: '2 hours'\n"),
            )
            code, errs = lint.run(repo.root, registry=reg)
            self.assertEqual(code, 1)
            self.assertTrue(any("unknown field 'length'" in e for e in errs), errs)
        finally:
            repo.cleanup()

    def test_required_sets_come_from_the_registry(self):
        """A key promoted to required in the registry is demanded by the linter."""
        repo = TempRepo()
        try:
            reg = _registry()
            reg["sections"]["works/games"]["fields"]["itch_url"]["required"] = True
            repo.write("content/works/games/g/index.md", GAME_VALID)
            code, errs = lint.run(repo.root, registry=reg)
            self.assertEqual(code, 1)
            self.assertTrue(
                any("missing required field 'itch_url'" in e for e in errs), errs
            )
        finally:
            repo.cleanup()

    def test_umbrella_fields_are_declared_per_sub_section(self):
        """tile_size / featured / hero are listed in each works section.

        works-vocab.json shared one `umbrella_optional` list; the registry has
        no inheritance (spec §4), so dropping tile_size from poetry alone
        rejects it on the poem and nowhere else.
        """
        repo = TempRepo()
        try:
            reg = _registry()
            del reg["sections"]["works/poetry"]["fields"]["tile_size"]
            for sub, body in (
                ("games", GAME_VALID), ("music", MUSIC_VALID), ("poetry", POEM_VALID),
            ):
                repo.write(
                    f"content/works/{sub}/x/index.md",
                    body.replace("---\n\nBody.", "tile_size: large\n---\n\nBody."),
                )
            code, errs = lint.run(repo.root, registry=reg)
            self.assertEqual(code, 1)
            self.assertEqual(
                [e for e in errs if "unknown field 'tile_size'" in e],
                [f"{repo.root}/content/works/poetry/x/index.md: unknown field 'tile_size'"],
            )
        finally:
            repo.cleanup()

    def test_platform_embed_sub_keys_are_closed(self):
        """platform_embed is a registry `object`: an unlisted sub-key now fails."""
        body = MUSIC_VALID.replace(
            "year: 2026\n",
            "year: 2026\nplatform_embed: { kind: bandcamp, url: 'https://x', id: 3 }\n",
        )
        p = self._write("music", "embed-extra", body)
        self.assertEqual(lint.lint_file(p, REG),
                         [f"{p}: unknown field 'platform_embed.id'"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tools/test_check_works_fixtures.py -v`
Expected: FAIL (failures=5, errors=33): nearly every test errors with `KeyError: 'game_required'` / `'music_required'` / `'umbrella_optional'` (the old `lint_file` indexes the vocab dict it is now handed a registry in place of) or `TypeError: run() got an unexpected keyword argument 'registry'`; `test_missing_registry_fails_closed`, `test_run_never_exits_the_process_on_a_bad_registry`, `test_poetry_only_tree_needs_no_seeded_registry`, `test_runner_*` fail because the old `run()` still looks for `data/works-vocab.json` in the temp tree.

- [ ] **Step 3: Rewrite `tools/check_works_fixtures.py`**

Replace the whole file with:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tools/test_check_works_fixtures.py -v`
Expected: PASS — `Ran 38 tests`, `OK`.

- [ ] **Step 5: Run the linter against the real repo, and its neighbours**

Run: `python3 tools/check_works_fixtures.py`
Expected: `check_works_fixtures: OK`, exit 0.

Run: `python3 -m unittest tools/test_sections.py -v 2>&1 | tail -1`
Expected: `OK`.

Confirm the vocabulary file is untouched and is no longer read by any site linter:

Run: `git status --short data/works-vocab.json; grep -ln "works-vocab" tools/check_*.py`
Expected: no output from either command (the remaining references are in `tools/test_publish_integration.py` and the elisp, both handled by the dotfiles plan).

- [ ] **Step 6: Run the equivalence gate**

Write `$SCRATCH/eqgate.py` (overwrite any earlier copy) with exactly:

```python
#!/usr/bin/env python3
"""Throwaway equivalence gate for one fixture-linter migration. NOT committed.

Run from the repo root with the migration applied but uncommitted:

    python3 "$SCRATCH/eqgate.py" <linter_module>

"Before" is tools/ at HEAD (git archive); "after" is the working tree. Both
run() over the real content/ + data/ and over one mutated copy per entry in
MUTATIONS. Messages are normalized to (file, field, rule) so wording-only
changes vanish; everything else is printed. Exit 0 = no diff at all.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path.cwd()
LINTER = sys.argv[1]

# (label, relpath, op, *args)
#   frontmatter ops (top-level key):  drop KEY | set KEY RAW | add KEY RAW
#   library yaml ops (item N):        item-drop N KEY | item-set N KEY RAW
#                                     | extras-set N KEY RAW
MUTATIONS: list[tuple] = [
    ("game drop status", "content/works/games/example-playable-jam/index.md", "drop", "status"),
    ("game bad status", "content/works/games/example-playable-jam/index.md", "set", "status", "shipped"),
    ("game bad kind", "content/works/games/example-playable-jam/index.md", "set", "game_kind", "walking-sim"),
    ("game year str", "content/works/games/example-playable-jam/index.md", "set", "year", "'twenty-six'"),
    ("game unknown field", "content/works/games/example-playable-jam/index.md", "add", "rarity", "99"),
    ("game screenshots scalar", "content/works/games/example-playable-jam/index.md", "add", "screenshots", "s1.svg"),
    ("game bad tile_size", "content/works/games/example-playable-jam/index.md", "add", "tile_size", "huge"),
    ("game featured str", "content/works/games/example-playable-jam/index.md", "add", "featured", "\"yes\""),
    ("game hero bool", "content/works/games/example-playable-jam/index.md", "set", "hero", "true"),
    ("game tagline int", "content/works/games/example-playable-jam/index.md", "set", "tagline", "42"),
    ("music drop format", "content/works/music/example-album-with-tracks/index.md", "drop", "format"),
    ("music bad format", "content/works/music/example-album-with-tracks/index.md", "set", "format", "cassette"),
    ("music embed bad kind", "content/works/music/example-album-with-tracks/index.md", "set", "platform_embed", "{ kind: spotify, url: 'https://x' }"),
    ("music embed no url", "content/works/music/example-album-with-tracks/index.md", "set", "platform_embed", "{ kind: bandcamp }"),
    ("music embed no kind", "content/works/music/example-album-with-tracks/index.md", "set", "platform_embed", "{ url: 'https://x' }"),
    ("music embed extra key", "content/works/music/example-album-with-tracks/index.md", "set", "platform_embed", "{ kind: bandcamp, url: 'https://x', id: 3 }"),
    ("music embed scalar", "content/works/music/example-album-with-tracks/index.md", "set", "platform_embed", "bandcamp"),
    ("music track no duration", "content/works/music/example-album-with-tracks/index.md", "set", "tracks", "\n  - { title: \"Lorem One\" }"),
    ("music hero str", "content/works/music/example-album-with-tracks/index.md", "add", "hero", "hero.svg"),
    ("music unknown", "content/works/music/example-album-with-tracks/index.md", "add", "bpm", "128"),
    ("poem drop lines", "content/works/poetry/example-poem-minimal/index.md", "drop", "lines"),
    ("poem lines str", "content/works/poetry/example-poem-minimal/index.md", "set", "lines", "'fourteen'"),
    ("poem hero str", "content/works/poetry/example-poem-minimal/index.md", "add", "hero", "hero.svg"),
    ("poem unknown", "content/works/poetry/example-poem-minimal/index.md", "add", "bpm", "1"),
    ("poem bad date", "content/works/poetry/example-poem-minimal/index.md", "set", "date", "soon"),
]

RUNNER = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import importlib\n"
    "m = importlib.import_module(sys.argv[2])\n"
    "res = m.run(Path(sys.argv[3]))\n"
    "print(json.dumps({'rc': res[0], 'errs': [str(e) for e in res[1]]}))\n"
)

# First match wins; group 1 is the field. Unmatched messages are compared
# verbatim as rule "code" (cross-field / structured / format rules that the
# migration must leave byte-identical).
PATTERNS = [
    (r"missing required field '([\w.]+)'", "missing"),
    (r"'(\w+)' is required for \w+ notes", "missing"),
    (r"([\w.]+) missing$", "missing"),
    (r"unknown field '([\w.]+)'", "unknown"),
    (r"forbidden field '(\w+)' on theme", "unknown"),
    (r"'(\w+)' not permitted on \w+ notes", "unknown"),
    (r"(extras\.\w+) not allowed for media_type", "unknown"),
    (r"([\w.\[\]]+)='.*' not (?:in|allowed in)\b", "enum"),
    (r"(tile_size) '.*' not in", "enum"),
    (r"([\w.]+)='.*' is not a valid YYYY-MM-DD date", "type"),
    (r"(\w+) not YYYY-MM-DD", "type"),
    (r"([\w.]+\[\d+\]) must be a string", "type"),
    (r"(tags) must be a list \(may be empty\)", "type"),
    (r"(canonical_url) must be https", "type"),
    (r"(extras\.\w+) must be (?:10 or 13|a positive|an absolute|a relative|a non-empty)", "type"),
    (r"([\w.]+) must be (?:an integer|a non-negative integer|int\b|a boolean|bool\b"
     r"|a list\b|a string|a mapping|a dict|a YYYY-MM-DD date)", "type"),
]


def norm(msg: str) -> tuple[str, str, str]:
    file, sep, rest = msg.partition(": ")
    if not sep:
        return ("", msg, "code")
    for pat, rule in PATTERNS:
        m = re.match(pat, rest)
        if m:
            return (file, m.group(1).removeprefix("extras."), rule)
    return (file, rest, "code")


def run_side(tools: Path, root: Path) -> tuple[int, set]:
    p = subprocess.run([sys.executable, "-c", RUNNER, str(tools), LINTER, str(root)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"runner crashed under {tools}:\n{p.stderr}")
    out = json.loads(p.stdout.strip().splitlines()[-1])
    return out["rc"], {norm(e) for e in out["errs"]}


def _fm_end(lines: list[str]) -> int:
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return i
    sys.exit("frontmatter not closed")


def _block_end(lines: list[str], i: int, stop: int, indent: str) -> int:
    j = i + 1
    while j < stop and lines[j].startswith(indent + " "):
        j += 1
    return j


def _item_bounds(lines: list[str], n: int) -> tuple[int, int]:
    starts = [i for i, l in enumerate(lines) if l.startswith("  - ")]
    s = starts[n]
    e = starts[n + 1] if n + 1 < len(starts) else len(lines)
    return s, e


def mutate(root: Path, rel: str, op: str, args: tuple) -> None:
    p = root / rel
    lines = p.read_text().split("\n")
    if op in ("drop", "set", "add"):
        end = _fm_end(lines)
        key = args[0]
        idx = next((i for i in range(1, end) if lines[i].startswith(key + ":")), None)
        if op == "add":
            lines.insert(end, f"{key}: {args[1]}")
        else:
            if idx is None:
                sys.exit(f"{rel}: no top-level key '{key}'")
            j = _block_end(lines, idx, end, "")
            lines[idx:j] = [] if op == "drop" else [f"{key}: {args[1]}"]
    else:
        n, key = int(args[0]), args[1]
        s, e = _item_bounds(lines, n)
        idx = next((i for i in range(s, e)
                    if lines[i].startswith(f"    {key}:") or lines[i].startswith(f"  - {key}:")), None)
        if op == "item-drop":
            if idx is None:
                sys.exit(f"{rel}[{n}]: no key '{key}'")
            lines[idx:_block_end(lines, idx, e, "    ")] = []
        elif op == "item-set":
            lead = "  - " if idx is not None and lines[idx].startswith("  - ") else "    "
            if idx is None:
                lines.insert(e, f"    {key}: {args[2]}")
            else:
                lines[idx:_block_end(lines, idx, e, "    ")] = [f"{lead}{key}: {args[2]}"]
        elif op == "extras-set":
            ex = next((i for i in range(s, e) if lines[i].rstrip() == "    extras:"), None)
            if ex is None:
                lines.insert(e, "    extras:")
                ex = e
            j = ex + 1
            while j < len(lines) and lines[j].startswith("      "):
                j += 1
            # Appended last, so it wins over an existing value for the key.
            lines.insert(j, f"      {key}: {args[2]}")
        else:
            sys.exit(f"unknown op {op}")
    p.write_text("\n".join(lines))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="eqgate-"))
    subprocess.run(f"git archive HEAD tools data/sections.json | tar -x -C {tmp}",
                   shell=True, check=True, cwd=REPO)
    old_tools = tmp / "tools"
    new_tools = REPO / "tools"
    cases = [("real repo", REPO)]
    for k, (label, rel, op, *args) in enumerate(MUTATIONS):
        root = tmp / f"m{k}"
        shutil.copytree(REPO / "content", root / "content")
        shutil.copytree(REPO / "data", root / "data")
        mutate(root, rel, op, tuple(args))
        cases.append((label, root))
    diffs = 0
    for label, root in cases:
        rc_b, before = run_side(old_tools, root)
        rc_a, after = run_side(new_tools, root)
        gone, new = sorted(before - after), sorted(after - before)
        if rc_b != rc_a or gone or new:
            diffs += 1
            print(f"DIFF [{label}] rc {rc_b} -> {rc_a}")
            for sign, ts in (("-", gone), ("+", new)):
                for f, field, rule in ts:
                    where = f.replace(f"{root}/", "")
                    print(f"   {sign} {field} ({rule}) @ {where}")
        else:
            print(f"same [{label}] rc {rc_b}, {len(before)} violation(s)")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{diffs} case(s) differ")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run (repo root, migration uncommitted): `python3 "$SCRATCH/eqgate.py" check_works_fixtures`
Expected: every case prints `same [...]` except exactly these, which are the intended behaviour changes recorded in the commit message (exit 1 is expected while they are present):

| Case | Diff |
|---|---|
| `game tagline int` | `+ tagline (type)` |
| `music embed extra key` | `+ platform_embed.id (unknown)` |
| `poem bad date` | `+ date (type)` |

The last line reads `3 case(s) differ`. Any other `DIFF` is a regression: fix the linter (not the gate) and re-run. `same [real repo] rc 0, 0 violation(s)` must be the first line.

- [ ] **Step 7: Commit**

```bash
git add tools/check_works_fixtures.py tools/test_check_works_fixtures.py
git commit -m "$(cat <<'MSG'
refactor(tools): works fixture linter reads data/sections.json, not works-vocab.json

Games, music and poetry are checked by sections.check_fields against the
works/games, works/music and works/poetry registry entries; load_vocab and
the per-type lint functions are gone, and the tracks shape stays as code.
The umbrella tile_size/featured/hero fields are listed in each section
(the registry has no inheritance). The registry is read from this code
tree, so a works temp tree no longer needs a vocabulary file seeded in.

data/works-vocab.json is NOT deleted: a3madkour-works-vocab.el still reads
it, and tools/test_publish_integration.py still copies it and pins the
elisp fixture against it. It goes in the dotfiles plan, in the same commit
as the elisp switch (spec §8 step 4).

Equivalence gate (real tree + 25 mutations): intended behaviour changes —
- platform_embed sub-keys are now closed (an extra key fails)
- text fields (tagline, …) and date/lastmod are now type-checked

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
)"
```

### Task 8: Migrate `check_library_fixtures.py`

**Files:**
- Modify: `tools/check_library_fixtures.py` (full rewrite, lines 1-326)
- Test: `tools/test_check_library_fixtures.py` (modify)

**Interfaces:**
- Consumes: `sections.check_fields(fm, section_name, path, registry=None) -> list[str]`, `sections.default_registry() -> dict`, `sections.SectionsError`, `sections.section_names(registry=None) -> list[str]`, `sections.DATE_PREFIX_RE` (Task 1).
- Produces:
  - `library_files(registry: dict | None = None) -> list[str]` — `['listening.yaml', 'playing.yaml', 'reading.yaml', 'watching.yaml']`
  - `lint_yaml_file(file_name: str, text: str, registry: dict | None = None) -> tuple[list[str], list[str]]`
  - `run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]`
  - `parse_library_yaml(text: str) -> list[dict[str, object]]` — unchanged (imported by `check_library_links`, `check_library_covers`, `check_filter_chips_config`, `fetch_library_covers`).

Constants and code deleted: `ALLOWED_MEDIA_TYPES`, `ALLOWED_STATUSES`, `COVER_KEYS_UNIVERSAL`, `COVER_KEYS_BY_MEDIA`, `ALLOWED_EXTRAS`, `REQUIRED_FIELDS`, `ALLOWED_FIELDS`, `SPOILER_LEVELS`, `_check_date`, `_validate_extras_cover_keys` (replaced by `_validate_extras_formats`), the `from datetime import date as Date` import, and the inline required/unknown/slug-type/year/media_type/status/spoiler/tags-list/extras-mapping/extras-allowed checks. `ISBN_RE`, `SLUG_RE`, `DATE_RE`, `ACTIVE_STATUSES` and the parser stay.

- [ ] **Step 1: Write the failing tests**

In `tools/test_check_library_fixtures.py`:

**1a.** Replace the module header (from the first line through `import check_library_fixtures as lint  # noqa: E402`):

```python
"""Tests for check_library_fixtures.py — run with:
   python3 -m unittest tools/test_check_library_fixtures.py -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_library_fixtures as lint  # noqa: E402
```

with:

```python
"""Tests for check_library_fixtures.py — run with:
   python3 -m unittest tools/test_check_library_fixtures.py -v
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_library_fixtures as lint  # noqa: E402
```

**1b.** Reword an assertion on the old message (refinement 1). Replace:

```python
        self.assertTrue(any("media_type='book' not allowed" in e for e in errs), errs)
```

with:

```python
        self.assertTrue(any("media_type='book' not in ['album', 'track']" in e for e in errs), errs)
```

**1c.** Insert this class above the trailing `if __name__ == "__main__":` block (two blank lines before and after):

```python
class RegistryTests(unittest.TestCase):
    """Per-shelf contracts are data/sections.json's library/<shelf> entries."""

    ITEM = (
        "items:\n"
        "  - slug: x\n"
        "    title: X\n"
        "    creator: Y\n"
        "    year: 2020\n"
        "    media_type: book\n"
        "    status: queued\n"
        "    last_modified: 2026-02-11\n"
        "    tags: []\n"
    )

    def _run(self, text: str, file_name: str = "reading.yaml", registry=None) -> list[str]:
        return lint.lint_yaml_file(file_name, text, registry)[0]

    def test_library_files_come_from_the_registry(self):
        self.assertEqual(lint.library_files(),
                         ["listening.yaml", "playing.yaml", "reading.yaml", "watching.yaml"])

    def test_null_required_field_now_fails(self):
        # `year: null` parses to None; the old `is not None` guard passed it.
        errs = self._run(self.ITEM.replace("year: 2020", "year: null"))
        self.assertEqual(errs, ["reading.yaml[0]: year must be an integer"])

    def test_null_optional_field_is_no_value(self):
        self.assertEqual(self._run(self.ITEM + "    note_slug: null\n    started:\n"), [])

    def test_null_tags_still_fails(self):
        errs = self._run(self.ITEM.replace("tags: []", "tags: null"))
        self.assertEqual(errs, ["reading.yaml[0]: tags must be a list"])

    def test_datetime_string_date_still_fails(self):
        errs = self._run(self.ITEM.replace("last_modified: 2026-02-11",
                                           "last_modified: 2026-02-11T10:00"))
        self.assertEqual(errs, ["reading.yaml[0]: last_modified not YYYY-MM-DD ('2026-02-11T10:00')"])

    def test_extras_silent_when_media_type_is_missing(self):
        # The missing media_type is the one failure; extras are not guessed at.
        text = self.ITEM.replace("    media_type: book\n", "") + "    extras:\n      anything: 1\n"
        self.assertEqual(self._run(text), ["reading.yaml[0]: missing required field 'media_type'"])

    def test_extras_non_int_id_gets_the_registry_message(self):
        text = (self.ITEM.replace("media_type: book", "media_type: game")
                .replace("status: queued", "status: playing")
                + "    extras:\n      igdb_id: abc\n")
        self.assertEqual(self._run(text, "playing.yaml"),
                         ["playing.yaml[0]: extras.igdb_id must be an integer"])

    def test_shelf_statuses_come_from_the_registry(self):
        reg = copy.deepcopy(lint.sections.default_registry())
        reg["sections"]["library/reading"]["fields"]["status"]["values"] = ["finished"]
        errs = self._run(self.ITEM, registry=reg)
        self.assertEqual(errs, ["reading.yaml[0]: status='queued' not in ['finished']"])

    def test_run_fails_closed_when_the_registry_cannot_load(self):
        boom = lint.sections.SectionsError("sections: registry not found at X")
        with mock.patch.object(lint.sections, "default_registry", side_effect=boom):
            self.assertEqual(lint.run(Path("/nonexistent")), (1, ["sections: registry not found at X"]))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tools/test_check_library_fixtures.py -v`
Expected: FAIL (failures=1, errors=9): `test_listening_rejects_book_media_type` — `AssertionError` (old wording `not allowed in listening.yaml`); every `RegistryTests` test errors — `TypeError: lint_yaml_file() takes 2 positional arguments but 3 were given` (6), `AttributeError: module 'check_library_fixtures' has no attribute 'library_files'` / `'sections'` (3).

- [ ] **Step 3: Rewrite `tools/check_library_fixtures.py`**

Replace the whole file with:

```python
#!/usr/bin/env python3
"""Library fixture frontmatter linter.

Validates `data/{reading,listening,playing,watching}.yaml` shape per
docs/superpowers/specs/2026-05-12-library-section-design.md §3, each item
against its shelf's `library/<shelf>` entry in data/sections.json
(sections.check_fields; spec 2026-10-20 §5.1).

Exits 0 on all-pass, 1 on any violation. Stdlib only.
"""
from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_fixtures import parse_scalar  # noqa: E402
import sections  # noqa: E402


ITEM_START_RE = re.compile(r"^  - ([a-zA-Z_]+):\s*(.*)$")
ITEM_FIELD_RE = re.compile(r"^    ([a-zA-Z_]+):\s*(.*)$")
NESTED_FIELD_RE = re.compile(r"^      ([a-zA-Z_]+):\s*(.*)$")
# Only these item-level fields open a nested mapping when their value is empty.
# All other empty-value item fields parse to None.
NESTED_BLOCK_FIELDS = {"extras"}


def _scalar(value: str) -> object:
    """Extend parse_scalar with null → None handling."""
    if value == "null":
        return None
    return parse_scalar(value)


# NOTE (R5.4 item 3): this parses data/<medium>.yaml (a list-of-dicts data
# file), NOT `---` frontmatter — a genuinely different shape, so it stays
# separate from check_fixtures.parse_frontmatter.
def parse_library_yaml(text: str) -> list[dict[str, object]]:
    """Parse a library data yaml file into a list of item dicts.

    Format:
        items:
          - slug: foo
            title: Bar
            tags: [a, b]
            extras:
              progress_pct: 50

    `null`, ints, floats, bools, [a, b] inline arrays handled via parse_scalar.
    """
    items: list[dict[str, object]] = []
    in_items = False
    current: dict[str, object] | None = None
    nested_key: str | None = None
    nested: dict[str, object] | None = None

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw.startswith("items:"):
            in_items = True
            continue
        if not in_items:
            continue

        m = ITEM_START_RE.match(raw)
        if m:
            if current is not None:
                if nested_key is not None and nested is not None:
                    current[nested_key] = nested
                items.append(current)
            current = {}
            nested_key = None
            nested = None
            field, value = m.group(1), m.group(2).strip()
            current[field] = _scalar(value)
            continue

        m_nested = NESTED_FIELD_RE.match(raw)
        if m_nested and nested is not None:
            field, value = m_nested.group(1), m_nested.group(2).strip()
            nested[field] = _scalar(value)
            continue

        m_field = ITEM_FIELD_RE.match(raw)
        if m_field and current is not None:
            field, value = m_field.group(1), m_field.group(2).strip()
            if value == "" and field in NESTED_BLOCK_FIELDS:
                # Open a nested mapping (e.g., extras: <newline> 6-space fields).
                if nested_key is not None and nested is not None:
                    current[nested_key] = nested
                nested_key = field
                nested = {}
            else:
                if nested_key is not None and nested is not None:
                    current[nested_key] = nested
                    nested_key = None
                    nested = None
                current[field] = _scalar(value) if value else None
            continue

    if current is not None:
        if nested_key is not None and nested is not None:
            current[nested_key] = nested
        items.append(current)

    return items


# --- contract ---
#
# Per-shelf field sets, media/status enums, types and the per-media_type
# `extras` sub-keys live in data/sections.json under library/<shelf>
# (store: "data"; spec 2026-10-20 §4). What stays here: the ISBN / slug / date
# / cover-key format rules, slug uniqueness, the finished-date and episode
# cross-field rules, the progress range, and the active-items warning.

ISBN_RE = re.compile(r"^\d{10}$|^\d{13}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ACTIVE_STATUSES = {"reading", "listening", "playing", "watching"}


def library_files(registry: dict | None = None) -> list[str]:
    """`<shelf>.yaml` for every library/<shelf> section in the registry."""
    return sorted(f"{name.split('/', 1)[1]}.yaml"
                  for name in sections.section_names(registry)
                  if name.startswith("library/"))


def _validate_extras_formats(extras: dict, errors: list, ctx: str) -> None:
    """Format rules for cover keys. Type and per-media allowance are the
    registry's; each rule here fires only on a value of the declared type."""
    for key, value in extras.items():
        if key == "isbn":
            if isinstance(value, str) and not ISBN_RE.match(value):
                errors.append(f"{ctx}: extras.isbn must be 10 or 13 digits, got {value!r}")
        elif key in {"igdb_id", "tmdb_id"}:
            if isinstance(value, int) and not isinstance(value, bool) and value <= 0:
                errors.append(f"{ctx}: extras.{key} must be a positive integer, got {value!r}")
        elif key == "musicbrainz_release_group":
            if isinstance(value, str) and not value:
                errors.append(f"{ctx}: extras.musicbrainz_release_group must be a non-empty string")
        elif key == "cover_url":
            if isinstance(value, str):
                parsed = urllib.parse.urlparse(value)
                if not parsed.scheme or not parsed.netloc:
                    errors.append(f"{ctx}: extras.cover_url must be an absolute URL, got {value!r}")
        elif key == "cover_file":
            if isinstance(value, str) and ("/" in value or ".." in value or not value):
                errors.append(f"{ctx}: extras.cover_file must be a relative filename without '/' or '..', got {value!r}")


def lint_yaml_file(file_name: str, text: str,
                   registry: dict | None = None) -> tuple[list[str], list[str]]:
    """Validate one library yaml file.

    Returns (errors, warnings). Errors fail CI; warnings print to stderr only.
    """
    errors: list[str] = []
    warnings: list[str] = []
    section = "library/" + file_name.removesuffix(".yaml")
    if file_name not in library_files(registry):
        return [f"{file_name}: unknown library file"], []

    items = parse_library_yaml(text)

    if not items:
        return [f"{file_name}: no items parsed"], []

    seen_slugs: set[str] = set()
    active_count = 0

    for idx, item in enumerate(items):
        prefix = f"{file_name}[{idx}]"

        errors.extend(sections.check_fields(item, section, prefix, registry=registry))

        slug = item.get("slug")
        if isinstance(slug, str):
            if not SLUG_RE.match(slug):
                errors.append(f"{prefix}: slug '{slug}' not kebab-case")
            if slug in seen_slugs:
                errors.append(f"{prefix}: duplicate slug '{slug}'")
            seen_slugs.add(slug)

        # The registry's `date` accepts any ISO-date-prefixed string (stream
        # datetimes). Library dates are bare dates, so the full match stays
        # here, firing only where the registry's prefix check passed.
        for date_field in ("started", "finished", "last_modified"):
            v = item.get(date_field)
            if isinstance(v, str) and sections.DATE_PREFIX_RE.match(v) and not DATE_RE.match(v):
                errors.append(f"{prefix}: {date_field} not YYYY-MM-DD ('{v}')")

        status = item.get("status")
        if status in ACTIVE_STATUSES:
            active_count += 1

        if status == "finished" and item.get("finished") in (None, ""):
            errors.append(f"{prefix}: finished date required when status='finished'")

        url = item.get("canonical_url")
        if isinstance(url, str) and not url.startswith("https://"):
            errors.append(f"{prefix}: canonical_url must be https:// or null")

        tags = item.get("tags")
        if isinstance(tags, list):
            for t in tags:
                if isinstance(t, str) and not SLUG_RE.match(t):
                    errors.append(f"{prefix}: tag '{t}' not slug-shaped")

        extras = item.get("extras")
        if isinstance(extras, dict):
            pct = extras.get("progress_pct")
            if isinstance(pct, int) and not isinstance(pct, bool) and not 0 <= pct <= 100:
                errors.append(f"{prefix}: progress_pct must be int 0..100, got {pct}")
            ce = extras.get("current_episode")
            ec = extras.get("episode_count")
            if isinstance(ce, int) and isinstance(ec, int) and ce > ec:
                errors.append(f"{prefix}: current_episode ({ce}) > episode_count ({ec})")
            _validate_extras_formats(extras, errors, prefix)

    if active_count > 3:
        warnings.append(f"{file_name}: {active_count} active items, expected ≤3 in currently-active highlight")

    return errors, warnings


def run(repo_root: Path, registry: dict | None = None) -> tuple[int, list[str]]:
    try:
        reg = registry if registry is not None else sections.default_registry()
    except sections.SectionsError as e:
        return 1, [str(e)]
    all_errs: list[str] = []
    all_warns: list[str] = []
    data_dir = repo_root / "data"
    for fname in library_files(reg):
        path = data_dir / fname
        if not path.exists():
            continue
        errs, warns = lint_yaml_file(fname, path.read_text(), reg)
        all_errs.extend(errs)
        all_warns.extend(warns)
    for w in all_warns:
        print(f"warning: {w}", file=sys.stderr)
    return (1 if all_errs else 0), all_errs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    rc, errs = run(repo_root)
    for e in errs:
        print(e, file=sys.stderr)
    if rc == 0:
        print("check_library_fixtures: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tools/test_check_library_fixtures.py -v`
Expected: PASS — `Ran 48 tests`, `OK`.

- [ ] **Step 5: Run the linter against the real repo, and its neighbours**

Run: `python3 tools/check_library_fixtures.py`
Expected: `check_library_fixtures: OK`, exit 0.

Run: `python3 -m unittest tools/test_sections.py -v 2>&1 | tail -1`
Expected: `OK`.

The parser is shared with four other tools; confirm they still pass:

Run: `for t in library_links library_covers filter_chips_config; do printf '%s ' $t; python3 -m unittest tools/test_check_$t.py 2>&1 | tail -1; python3 tools/check_$t.py >/dev/null && echo lint-ok; done`
Expected: `OK` and `lint-ok` for each.

- [ ] **Step 6: Run the equivalence gate**

Write `$SCRATCH/eqgate.py` (overwrite any earlier copy) with exactly:

```python
#!/usr/bin/env python3
"""Throwaway equivalence gate for one fixture-linter migration. NOT committed.

Run from the repo root with the migration applied but uncommitted:

    python3 "$SCRATCH/eqgate.py" <linter_module>

"Before" is tools/ at HEAD (git archive); "after" is the working tree. Both
run() over the real content/ + data/ and over one mutated copy per entry in
MUTATIONS. Messages are normalized to (file, field, rule) so wording-only
changes vanish; everything else is printed. Exit 0 = no diff at all.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path.cwd()
LINTER = sys.argv[1]

# (label, relpath, op, *args)
#   frontmatter ops (top-level key):  drop KEY | set KEY RAW | add KEY RAW
#   library yaml ops (item N):        item-drop N KEY | item-set N KEY RAW
#                                     | extras-set N KEY RAW
MUTATIONS: list[tuple] = [
    ("reading drop creator", "data/reading.yaml", "item-drop", 0, "creator"),
    ("reading drop tags", "data/reading.yaml", "item-drop", 0, "tags"),
    ("reading null tags", "data/reading.yaml", "item-set", 0, "tags", "null"),
    ("reading null year", "data/reading.yaml", "item-set", 0, "year", "null"),
    ("reading unknown field", "data/reading.yaml", "item-set", 0, "rating", "5"),
    ("reading bad status", "data/reading.yaml", "item-set", 0, "status", "bogus"),
    ("reading album media", "data/reading.yaml", "item-set", 0, "media_type", "album"),
    ("reading year str", "data/reading.yaml", "item-set", 0, "year", "\"1972\""),
    ("reading slug int", "data/reading.yaml", "item-set", 0, "slug", "123"),
    ("reading slug bad shape", "data/reading.yaml", "item-set", 0, "slug", "Bad_Slug"),
    ("reading duplicate slug", "data/reading.yaml", "item-set", 1, "slug", "example-book-one"),
    ("reading bad last_modified", "data/reading.yaml", "item-set", 0, "last_modified", "not-a-date"),
    ("reading datetime last_modified", "data/reading.yaml", "item-set", 0, "last_modified", "2026-05-30T10:00"),
    ("reading finished no date", "data/reading.yaml", "item-drop", 0, "finished"),
    ("reading bad spoiler", "data/reading.yaml", "item-set", 0, "spoiler_level", "extreme"),
    ("reading http url", "data/reading.yaml", "item-set", 0, "canonical_url", "http://x"),
    ("reading bad tag", "data/reading.yaml", "item-set", 0, "tags", "[Bad Tag]"),
    ("reading progress out of range", "data/reading.yaml", "extras-set", 0, "progress_pct", "150"),
    ("reading progress str", "data/reading.yaml", "extras-set", 0, "progress_pct", "half"),
    ("reading unknown extras", "data/reading.yaml", "extras-set", 1, "bogus_key", "1"),
    ("reading isbn bad", "data/reading.yaml", "extras-set", 0, "isbn", "not-an-isbn"),
    ("reading isbn unquoted int", "data/reading.yaml", "extras-set", 0, "isbn", "9780156453806"),
    ("reading igdb on book", "data/reading.yaml", "extras-set", 0, "igdb_id", "5"),
    ("reading cover_file slash", "data/reading.yaml", "extras-set", 0, "cover_file", "a/b.jpg"),
    ("reading cover_url relative", "data/reading.yaml", "extras-set", 0, "cover_url", "nope"),
    ("playing igdb str", "data/playing.yaml", "extras-set", 0, "igdb_id", "abc"),
    ("playing igdb zero", "data/playing.yaml", "extras-set", 0, "igdb_id", "0"),
    ("playing tmdb on game", "data/playing.yaml", "extras-set", 0, "tmdb_id", "5"),
    ("listening mbid empty", "data/listening.yaml", "extras-set", 0, "musicbrainz_release_group", "\"\""),
    ("watching episode overflow", "data/watching.yaml", "extras-set", 0, "current_episode", "999"),
    ("watching runtime str", "data/watching.yaml", "extras-set", 0, "runtime_min", "long"),
]

RUNNER = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import importlib\n"
    "m = importlib.import_module(sys.argv[2])\n"
    "res = m.run(Path(sys.argv[3]))\n"
    "print(json.dumps({'rc': res[0], 'errs': [str(e) for e in res[1]]}))\n"
)

# First match wins; group 1 is the field. Unmatched messages are compared
# verbatim as rule "code" (cross-field / structured / format rules that the
# migration must leave byte-identical).
PATTERNS = [
    (r"missing required field '([\w.]+)'", "missing"),
    (r"'(\w+)' is required for \w+ notes", "missing"),
    (r"([\w.]+) missing$", "missing"),
    (r"unknown field '([\w.]+)'", "unknown"),
    (r"forbidden field '(\w+)' on theme", "unknown"),
    (r"'(\w+)' not permitted on \w+ notes", "unknown"),
    (r"(extras\.\w+) not allowed for media_type", "unknown"),
    (r"([\w.\[\]]+)='.*' not (?:in|allowed in)\b", "enum"),
    (r"(tile_size) '.*' not in", "enum"),
    (r"([\w.]+)='.*' is not a valid YYYY-MM-DD date", "type"),
    (r"(\w+) not YYYY-MM-DD", "type"),
    (r"([\w.]+\[\d+\]) must be a string", "type"),
    (r"(tags) must be a list \(may be empty\)", "type"),
    (r"(canonical_url) must be https", "type"),
    (r"(extras\.\w+) must be (?:10 or 13|a positive|an absolute|a relative|a non-empty)", "type"),
    (r"([\w.]+) must be (?:an integer|a non-negative integer|int\b|a boolean|bool\b"
     r"|a list\b|a string|a mapping|a dict|a YYYY-MM-DD date)", "type"),
]


def norm(msg: str) -> tuple[str, str, str]:
    file, sep, rest = msg.partition(": ")
    if not sep:
        return ("", msg, "code")
    for pat, rule in PATTERNS:
        m = re.match(pat, rest)
        if m:
            return (file, m.group(1).removeprefix("extras."), rule)
    return (file, rest, "code")


def run_side(tools: Path, root: Path) -> tuple[int, set]:
    p = subprocess.run([sys.executable, "-c", RUNNER, str(tools), LINTER, str(root)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"runner crashed under {tools}:\n{p.stderr}")
    out = json.loads(p.stdout.strip().splitlines()[-1])
    return out["rc"], {norm(e) for e in out["errs"]}


def _fm_end(lines: list[str]) -> int:
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return i
    sys.exit("frontmatter not closed")


def _block_end(lines: list[str], i: int, stop: int, indent: str) -> int:
    j = i + 1
    while j < stop and lines[j].startswith(indent + " "):
        j += 1
    return j


def _item_bounds(lines: list[str], n: int) -> tuple[int, int]:
    starts = [i for i, l in enumerate(lines) if l.startswith("  - ")]
    s = starts[n]
    e = starts[n + 1] if n + 1 < len(starts) else len(lines)
    return s, e


def mutate(root: Path, rel: str, op: str, args: tuple) -> None:
    p = root / rel
    lines = p.read_text().split("\n")
    if op in ("drop", "set", "add"):
        end = _fm_end(lines)
        key = args[0]
        idx = next((i for i in range(1, end) if lines[i].startswith(key + ":")), None)
        if op == "add":
            lines.insert(end, f"{key}: {args[1]}")
        else:
            if idx is None:
                sys.exit(f"{rel}: no top-level key '{key}'")
            j = _block_end(lines, idx, end, "")
            lines[idx:j] = [] if op == "drop" else [f"{key}: {args[1]}"]
    else:
        n, key = int(args[0]), args[1]
        s, e = _item_bounds(lines, n)
        idx = next((i for i in range(s, e)
                    if lines[i].startswith(f"    {key}:") or lines[i].startswith(f"  - {key}:")), None)
        if op == "item-drop":
            if idx is None:
                sys.exit(f"{rel}[{n}]: no key '{key}'")
            lines[idx:_block_end(lines, idx, e, "    ")] = []
        elif op == "item-set":
            lead = "  - " if idx is not None and lines[idx].startswith("  - ") else "    "
            if idx is None:
                lines.insert(e, f"    {key}: {args[2]}")
            else:
                lines[idx:_block_end(lines, idx, e, "    ")] = [f"{lead}{key}: {args[2]}"]
        elif op == "extras-set":
            ex = next((i for i in range(s, e) if lines[i].rstrip() == "    extras:"), None)
            if ex is None:
                lines.insert(e, "    extras:")
                ex = e
            j = ex + 1
            while j < len(lines) and lines[j].startswith("      "):
                j += 1
            # Appended last, so it wins over an existing value for the key.
            lines.insert(j, f"      {key}: {args[2]}")
        else:
            sys.exit(f"unknown op {op}")
    p.write_text("\n".join(lines))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="eqgate-"))
    subprocess.run(f"git archive HEAD tools data/sections.json | tar -x -C {tmp}",
                   shell=True, check=True, cwd=REPO)
    old_tools = tmp / "tools"
    new_tools = REPO / "tools"
    cases = [("real repo", REPO)]
    for k, (label, rel, op, *args) in enumerate(MUTATIONS):
        root = tmp / f"m{k}"
        shutil.copytree(REPO / "content", root / "content")
        shutil.copytree(REPO / "data", root / "data")
        mutate(root, rel, op, tuple(args))
        cases.append((label, root))
    diffs = 0
    for label, root in cases:
        rc_b, before = run_side(old_tools, root)
        rc_a, after = run_side(new_tools, root)
        gone, new = sorted(before - after), sorted(after - before)
        if rc_b != rc_a or gone or new:
            diffs += 1
            print(f"DIFF [{label}] rc {rc_b} -> {rc_a}")
            for sign, ts in (("-", gone), ("+", new)):
                for f, field, rule in ts:
                    where = f.replace(f"{root}/", "")
                    print(f"   {sign} {field} ({rule}) @ {where}")
        else:
            print(f"same [{label}] rc {rc_b}, {len(before)} violation(s)")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{diffs} case(s) differ")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run (repo root, migration uncommitted): `python3 "$SCRATCH/eqgate.py" check_library_fixtures`
Expected: every case prints `same [...]` except exactly these, which are the intended behaviour changes recorded in the commit message (exit 1 is expected while they are present):

| Case | Diff |
|---|---|
| `reading drop tags` | `- tags (type)` |
| `reading null year` | `+ year (type)` |
| `watching runtime str` | `+ runtime_min (type)` |

The last line reads `3 case(s) differ`. Any other `DIFF` is a regression: fix the linter (not the gate) and re-run. `same [real repo] rc 0, 0 violation(s)` must be the first line.

- [ ] **Step 7: Commit**

```bash
git add tools/check_library_fixtures.py tools/test_check_library_fixtures.py
git commit -m "$(cat <<'MSG'
refactor(tools): library fixture linter reads data/sections.json

Each yaml item is checked by sections.check_fields against its shelf's
library/<shelf> registry entry (store: data), with the existing
`<file>[<idx>]` prefix. Per-shelf media/status enums are in each shelf's
entry; extras is an object whose sub-keys vary by media_type through
object-level variants. ISBN/slug/date/cover-key format rules, slug
uniqueness, finished-date, episode and progress-range rules and the
active-items warning stay as code. Messages move to the canonical forms
(`media_type='x' not in [...]`, `year must be an integer`,
`unknown field 'extras.k'`).

Equivalence gate (real tree + 31 mutations): intended behaviour changes —
- a missing `tags` is reported once (missing), not also as `must be a list`
- a required field set to null (`year: null`) now fails its type check
- extras ints (runtime_min, hours_played, episode counts) are now
  type-checked
- a cover-key format rule now also fires on a key the media type does not
  permit (alongside its `unknown field`), where it used to be skipped

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
)"
```

### Task 9: Document the registry in CLAUDE.md and run the full local CI

**Files:**
- Modify: `CLAUDE.md` (line 14, the `## Commands` linter paragraph; line 124, `### Frontmatter contracts`; line ~194, `### Deployment`)

**Interfaces:**
- Consumes: everything from Tasks 1-8.
- Produces: no code.

`tools/test_sections.py` was wired into `.github/workflows/hugo.yaml` and `tools/ci-local.sh` in Task 1, so this task only documents and verifies. The linter-pair count (38) does not change: `sections.py` is a reader with a test file, not a `check_*.py` pair.

- [ ] **Step 1: Confirm the wiring is in place**

Run: `grep -n "sections.py" .github/workflows/hugo.yaml tools/ci-local.sh`
Expected: four lines — `run: python3 tools/sections.py`, `run: python3 -m unittest tools/test_sections.py -v` in hugo.yaml; `python3 tools/sections.py`, `python3 -m unittest tools/test_sections.py -v 2>&1 | tail -3` in ci-local.sh.

Run: `grep -c '^\s*- name:' .github/workflows/hugo.yaml`
Expected: `105`.

- [ ] **Step 2: Edit `CLAUDE.md`**

**2a.** In the `## Commands` linter bullet (line 14), replace:

```text
`tools/test_test_helpers.py` is a self-test for the shared helper (not a linter pair — there is no corresponding `check_*.py`).
```

with:

```text
`tools/test_test_helpers.py` is a self-test for the shared helper (not a linter pair — there is no corresponding `check_*.py`). `tools/sections.py` + `tools/test_sections.py` are likewise not a linter pair: `sections.py` is the reader for `data/sections.json`, the section registry (see Frontmatter contracts), and `python3 tools/sections.py` validates that file in CI ahead of the fixture linters.
```

**2b.** Directly under the `### Frontmatter contracts` heading (line 124), insert this paragraph followed by a blank line:

```text
**Section registry** — `data/sections.json` is the single field contract for all 14 sections (`essays`, `garden`, `research/themes`, `research/questions`, `works/{games,music,poetry}`, `library/{reading,listening,playing,watching}`, `streams`, `recipes`, `about`): per field its `type` (`text/int/bool/date/list/enum/ref/refs/object/structured`), `required`, enum `values`, `ref` target section, and the `from: pipeline` / `ask` / `fill` / `default` hints the elisp `a3-publish-mark` reads. Garden flavors and the library `extras` sub-keys are `variants` on `media_type`. `tools/sections.py` loads it fail-closed (no hard-coded fallback) and the seven fixture linters below call `sections.check_fields`, which emits one canonical wording for every section (`missing required field 'f'`, `unknown field 'f'`, `f='v' not in [...]`, `f must be <an integer|a boolean|a list|a string|a mapping|a YYYY-MM-DD date>`). The contracts listed below are what that file says; cross-field rules, uniqueness, the inner shape of `structured` fields and format regexes stay in each linter's code. The registry is read from the code tree (`tools/../data/sections.json`), never from the tree a linter's `run(repo_root)` walks. `data/works-vocab.json` is no longer read by any site linter; it remains only for the elisp until the dotfiles switch-over deletes it.
```

**2c.** In `### Deployment` (line ~194), replace:

```text
pre-build linters (contrast + dark-token equality + CSS-refs + the fixture/link linter pairs + 1 sibling-less)
```

with:

```text
pre-build linters (contrast + dark-token equality + CSS-refs + the section registry + the fixture/link linter pairs + 1 sibling-less)
```

and replace `**103 named steps**` with `**105 named steps**`.

- [ ] **Step 3: Verify the edits**

Run: `grep -c "Section registry" CLAUDE.md; grep -c "105 named steps" CLAUDE.md; grep -c "103 named steps" CLAUDE.md`
Expected: `1`, `1`, `0`.

- [ ] **Step 4: Run the full local CI**

Make sure no `hugo server` is running (`pgrep -fl "hugo server"` prints nothing), then:

Run: `tools/ci-local.sh`
Expected: exits 0. If the Playwright stage flakes in parallel (known locally), re-run that stage alone with `npx playwright test --workers=1` and expect `32 passed`, then re-run `tools/ci-local.sh` to completion.

Run: `git status --short`
Expected: only `CLAUDE.md` modified (plus the pre-existing untracked files that were there before this plan: `.claude/memory/*`, `citations.yaml`).

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "$(cat <<'MSG'
docs(claude-md): section registry — data/sections.json + sections.py

Documents the registry as the field contract the seven fixture linters
read, its canonical messages, that it is read from the code tree, and
that works-vocab.json now survives only for the elisp. CI step count
103 -> 105 (registry validation + its unit tests).

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

## Self-Review

**Spec coverage**

- **§4 schema** — Task 1 Step 4 writes every section key (`closed`, `store`, `fields`, `variants`) and every field spec key the spec lists (`type`, `required`, `values`, `to`, `default`, `from`, `ask`, `fill`, `fields`); garden variants on `media_type` (concept = `[null]`, media, reference); library `extras` as an `object` with `media_type` variants; `forbidden` dropped (themes simply omit `parent_question`/`theme`, Task 2 test reworded to `unknown field`); nothing inherited between sections (works umbrella fields repeated per section, Task 7 test `test_umbrella_fields_are_declared_per_sub_section`). Kept-as-code items: archived⇒vod_url (Task 3), theme-weight uniqueness (Task 2), series↔series_order (Task 5), structured inner shapes — ingredients/steps/sources (Task 4), outputs (Task 2), tracks (Task 7) — format regexes ISBN/slug/date (Task 8), and `lyrics_poem`↔`set_to_music` symmetry, which lives in `check_works_links.py` and is not touched.
- **§5.1 `tools/sections.py`** — `load(repo_root)` fails closed on a missing file, malformed JSON, unknown type, unknown spec key, `values` on a non-enum, a `to` naming no section, a `variants.on` naming no field (Task 1 tests `test_missing_file_fails_closed` … `test_rejects_variants_on_naming_no_field`, plus extra rejections: version, store, defaults, fill, from, object fields, duplicate case values, case/base field clash, object-level `on`). `check_fields` covers required, closed set, enum, type, variant selection and `object` sub-keys (one test each, `CheckFieldsTests`). Each linter deletes its constants and calls `check_fields` (Tasks 2-8, constants listed per task); library calls it per item (Task 8); works drops `load_vocab` (Task 7).
- **§7 site testing** — `tools/test_sections.py` has every loader rejection, one test per `check_fields` rule, and the real file loading cleanly (`test_real_registry_loads_cleanly`) and naming exactly the 14 sections. Every `test_check_*` file passes after its migration, with wording-only assertion changes listed per task. The equivalence gate runs per migrated linter (Step 6 of Tasks 2-8) over the real tree plus 13-31 deliberately broken copies, and each surviving difference is recorded in that commit message. Mutation testing of every `sections.py` guard is Task 1 Step 6; each linter's registry-injection test (`…_comes_from_the_registry`) proves the linter reads the registry rather than a re-hardcoded copy.
- **§8 step 1** — Task 1 (one commit: JSON + reader + tests + CI wiring).
- **§8 step 2** — Tasks 2-8, one commit each, in the spec's order: research, streams, recipes, essays, garden, works, library. The spec's "then delete works-vocab.json in the same commit as the elisp switch" is deferred to the dotfiles plan, as stated in the header and in Task 7's commit message.

**Not expressible in the schema, kept as code (all noted in the task that owns them):**
- `streams.platforms` element enum (`PLATFORM_VALUES`): a `list` cannot carry `values`.
- `recipes.servings` int-or-decimal-string: typed `structured`, number rule in code.
- `works/games.hero` filename-or-bool: typed `structured`.
- Garden and library bare-date strictness: the registry's `date` prefix-matches (streams need datetimes), so the linters keep a code rule for ISO-prefixed strings.
- Non-negativity of recipe minutes, positivity of `igdb_id`/`tmdb_id`, the `progress_pct` range: sign/range rules stay in code; only integer-ness is the registry's.
- Path-valued link lists (works `related_*`, `research_questions`, streams `related_works`) are `list`, since `refs.to` names one section of slugs.

**Placeholder scan:** every code step carries the full file or the exact replacement; every command has its expected output; no deferred-work markers.

**Type consistency:** `check_fields(fm, section_name, path, registry=None)`, `run(repo_root, registry=None)`, `lint_*(…, registry=None)` and `sections.SectionsError` are spelled the same in every task; the section keys used in each linter (`"research/themes"`, `"streams"`, `"recipes"`, `"essays"`, `"garden"`, `f"works/{sub}"`, `"library/" + stem`) match `data/sections.json`.
