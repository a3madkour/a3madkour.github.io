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

    def test_rejects_bad_source(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["title"].update(
                     **{"from": "pipeline", "source": "elsewhere"}),
                 "source 'elsewhere' not in")

    def test_drawer_is_a_valid_source(self):
        reg = copy.deepcopy(MINI)
        reg["sections"]["closed"]["fields"]["title"].update(
            **{"from": "pipeline", "source": "drawer"})
        self.assertEqual(_reg(reg)["sections"]["closed"]["fields"]["title"]["source"], "drawer")

    def test_rejects_source_without_from_pipeline(self):
        _rejects(self, lambda d: d["sections"]["closed"]["fields"]["title"].update(source="title"),
                 "'source' needs 'from': 'pipeline'")

    def test_real_registry_sources_required_buffer_fields(self):
        """Every required pipeline field mark can supply names its buffer source:
        tags from #+filetags, title from #+title.  Essays tags are the
        exception: the essays normalizer always writes the key (`tags: []`
        for an essay with none), so mark never asks for tags there.
        Library (store: data) rows come from item notes."""
        reg = sections.load(sections.SITE_ROOT)
        for name, spec in reg["sections"].items():
            if spec.get("store") == "data":
                continue
            for field, want in (("title", "title"), ("tags", "filetags")):
                if (name, field) == ("essays", "tags"):
                    want = None
                fs = spec["fields"].get(field)
                if fs and fs.get("required") and fs.get("from") == "pipeline":
                    self.assertEqual(fs.get("source"), want, f"{name}.{field}")

    def test_real_registry_garden_media_fields_come_from_the_drawer(self):
        reg = sections.load(sections.SITE_ROOT)
        cases = reg["sections"]["garden"]["variants"]["cases"]
        for cname in ("media-book", "media-listening", "media-playing", "media-watching"):
            for field in ("media_type", "status", "creator", "started", "finished"):
                fs = cases[cname]["fields"][field]
                self.assertEqual((fs.get("from"), fs.get("source")), ("pipeline", "drawer"),
                                 f"{cname}.{field}")

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

    # --- garden media cases follow the shelf ---
    def test_garden_media_status_follows_shelf(self):
        reg = sections.load(sections.SITE_ROOT)
        base = {"title": "T", "draft": False, "last_modified": "2026-01-01",
                "growth_stage": "seedling", "media_type": "game", "creator": "C"}
        errs = sections.check_fields({**base, "status": "100pct"}, "garden", "p.md", registry=reg)
        self.assertFalse([e for e in errs if "status" in e], errs)
        errs = sections.check_fields({**base, "status": "reading"}, "garden", "p.md", registry=reg)
        self.assertTrue(any("status='reading' not in [" in e for e in errs), errs)

    def test_series_abandoned_rejected(self):
        reg = sections.load(sections.SITE_ROOT)
        fm = {"title": "T", "draft": False, "last_modified": "2026-01-01",
              "growth_stage": "seedling", "media_type": "series", "creator": "C",
              "status": "abandoned"}
        errs = sections.check_fields(fm, "garden", "p.md", registry=reg)
        self.assertTrue(any("status='abandoned' not in [" in e for e in errs), errs)

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
