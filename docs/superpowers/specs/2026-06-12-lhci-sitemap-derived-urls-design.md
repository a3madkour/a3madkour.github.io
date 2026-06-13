# Tier 7.1 — LHCI sitemap-derived URLs

**Status:** designed 2026-06-12. No plan yet. Single-session slice.

**Parent context.** Tier 7.1 of the polish-and-bugfix roadmap; supersedes the manual-edit step that fixture retirements currently break. Carried forward from [`project_lhci_representative_pages_queued`](../../../.claude/memory/project_lhci_representative_pages_queued.md) (originally 4.2). 4.1 (`check_lhci_urls.py`) shipped 2026-06-04 and stays as defense-in-depth — see [`project_lhci_url_validator_complete`](../../../.claude/memory/project_lhci_url_validator_complete.md).

**Driver.** Preemptive — user elected to fire this row before the next manual-edit annoyance. Pays off whenever fixture retirements happen.

---

## 1. Scope

### Goal

Eliminate hand-maintenance of the LHCI URL list. After this slice, `lighthouserc.json` + `lighthouserc.mobile.json` get their `collect.url` fields regenerated in CI from a Hugo-emitted page manifest. Fixture retirements stop breaking LHCI.

### In-scope deliverables

1. **Hugo output format** `LHCI-PAGES` emitting `public/lhci-pages.json` — array of `{url, kind, section, type}` per regular page + section index + home.
2. **`tools/gen_lhci_urls.py`** — reads the manifest + `tools/lhci-overrides.json`, rewrites `lighthouserc.{json,mobile.json}` in place.
3. **`tools/lhci-overrides.json`** — group-keyed assertion overrides. Replaces the inline `assertMatrix` entry that currently hand-targets `/essays/example-one/`.
4. **`tools/test_gen_lhci_urls.py`** — ~12 unit tests covering grouping, picking, override application, idempotency, and failure modes. Stdlib `unittest`.
5. **CI workflow edits** — insert the regen step + sibling-test step into `.github/workflows/hugo.yaml` between `hugo --minify` and the Lighthouse CI steps.
6. **`tools/ci-local.sh` mirror** — same insertion per [[feedback-always-run-ci-locally]].
7. **One-line CLAUDE.md note** — "LHCI URL list is CI-generated; edit `tools/lhci-overrides.json` for thresholds, not the lighthouserc files."
8. **Auto-generated headers on committed lighthouserc files** — short banner pointing authors to `lhci-overrides.json`.

### Out of scope (queued — see §6 follow-ups)

- Tier 7.2 (visual-feature autodetect / fingerprint corpus). Original 4.3 from the queued spec.
- Per-essay JS bundle auditing (LHCI audits HTML pages only).
- Switching the LHCI CI runner. Stays on `npx @lhci/cli`.

### Out of scope (closed — no follow-up)

- Removing 4.1 (`check_lhci_urls.py`). Stays as defense-in-depth against the case where `gen_lhci_urls.py` writes a URL that doesn't materialize in `public/`.
- Changing the base assertion thresholds (0.9 for all four categories on desktop + mobile). Untouched.
- Deleting `lighthouserc.{json,mobile.json}` from git. Stays committed for diff readability — see §4 Option A.

### Constraints carried in

- **Stdlib only.** `json` / `pathlib` / `sys` only. No pyyaml — overrides file is JSON, not YAML.
- **No npm.** LHCI runner stays as `npx @lhci/cli` invocation; this slice doesn't add JS deps.
- **Defense in depth.** 4.1 stays; 4.2's removing-the-drift logic is layered on top.

---

## 2. Architecture

### Data flow

```
hugo --minify  →  public/
                     ├── sitemap.xml             (existing)
                     └── lhci-pages.json         (NEW — Hugo output format)
                              │
                              ▼
                 tools/gen_lhci_urls.py  ←  tools/lhci-overrides.json (hand-edit)
                              │
                              ├──→  rewrite: lighthouserc.json
                              └──→  rewrite: lighthouserc.mobile.json
                              │
                              ▼
                       LHCI desktop + LHCI mobile (existing CI steps, unchanged)
```

### Hugo side — `LHCI-PAGES` output format

`hugo.yaml` gains:

```yaml
outputs:
  home: [HTML, RSS, JSON, LHCI-PAGES]

outputFormats:
  LHCI-PAGES:
    mediaType: application/json
    baseName: lhci-pages
    isPlainText: true
    notAlternative: true
```

Template `layouts/index.lhci-pages.json`:

```go-html-template
{{- $pages := slice -}}

{{/* All regular pages */}}
{{- range where site.RegularPages "Draft" "!=" true -}}
  {{- $pages = $pages | append (dict
        "url" .RelPermalink
        "kind" .Kind
        "section" .Section
        "type" .Type) -}}
{{- end -}}

{{/* Section indexes (Kind=section) */}}
{{- range site.Sections -}}
  {{- $pages = $pages | append (dict
        "url" .RelPermalink
        "kind" "section"
        "section" .Section
        "type" .Type) -}}
{{- end -}}

{{/* Home */}}
{{- $pages = $pages | append (dict
      "url" "/"
      "kind" "home"
      "section" ""
      "type" "page") -}}

{{- $pages | jsonify -}}
```

Output `public/lhci-pages.json` shape:

```json
[
  {"url": "/essays/example-explorables/", "kind": "page", "section": "essays", "type": "essays"},
  {"url": "/essays/example-one/", "kind": "page", "section": "essays", "type": "essays"},
  {"url": "/garden/", "kind": "section", "section": "garden", "type": "garden"},
  {"url": "/garden/emergence-vs-design/", "kind": "page", "section": "garden", "type": "garden"},
  {"url": "/research/themes/example-theme-one/", "kind": "page", "section": "research", "type": "research-theme"},
  {"url": "/research/questions/example-question-one/", "kind": "page", "section": "research", "type": "research-question"},
  ...
]
```

Section §5 risk 1 + 2 cover output-format gotchas + section iteration edge cases — plan addresses with a minimal repro before the full wire-up.

### Python side — `tools/gen_lhci_urls.py`

```python
def group_pages(manifest: list[dict]) -> dict[str, list[str]]:
    """Group page entries by (kind, section, type) → list of URLs.
    Returns {group_key: sorted_urls}.
    group_key = "<kind>:<section>:<type>" with empty parts elided."""

def pick_representative_urls(manifest: list[dict]) -> dict[str, str]:
    """Returns {group_key: first_url_alphabetically} per group."""

def render_assert_matrix(
    picks: dict[str, str],
    overrides: list[dict],
) -> list[dict]:
    """Build the assertMatrix from overrides + current picks.
    Each entry in `overrides` has {group, perf?, accessibility?, best-practices?, seo?}.
    Returns matrix entries with matchingUrlPattern set to the current URL
    (regex-escaped + anchored)."""

def rewrite_lighthouserc(
    config_path: Path,
    picks: dict[str, str],
    overrides: list[dict] | None,
    base_url: str = "http://localhost",
) -> None:
    """Load existing JSON config, replace collect.url + assertMatrix, write back."""

def run(repo_root: Path) -> tuple[int, list[str]]:
    """Programmatic entry. Returns (rc, errors)."""

def main() -> int:
    ...
```

**Failure modes the script handles:**
- `public/lhci-pages.json` missing → exit 1 with "run after `hugo --minify`".
- `tools/lhci-overrides.json` missing → fall back to empty overrides (no `assertMatrix` in mobile).
- Override references unknown `group` → exit 1, listing valid groups.
- Lighthouserc configs missing → exit 1.
- Empty manifest → exit 1.

**Intentionally NOT handled:**
- Malformed JSON in any input → let exception propagate. Loud failures are fine in CI.
- Draft filtering happens in the Hugo template, not Python. Python trusts the manifest.

### `tools/lhci-overrides.json`

```json
{
  "desktop": [],
  "mobile": [
    {"group": "page:essays:essays", "perf": 0.85}
  ]
}
```

Schema symmetric (`desktop` + `mobile` arrays) so adding desktop overrides later doesn't need schema change.

Group key format `"<kind>:<section>:<type>"`. Empty kind/section/type segments are elided in code; the schema requires the full key.

---

## 3. API surface + testing

### Public functions (recap)

| Function | Pure? | Tested via |
|---|---|---|
| `group_pages` | yes | hand-crafted manifest fixtures |
| `pick_representative_urls` | yes | hand-crafted manifest fixtures |
| `render_assert_matrix` | yes | hand-crafted pick + override pairs |
| `rewrite_lighthouserc` | no (I/O) | tempdir + golden-file diff |
| `run` | mostly | tempdir round-trip |
| `main` | no (sys.exit) | not directly tested |

### `tools/test_gen_lhci_urls.py` — test inventory

| # | Test | Covers |
|---|---|---|
| 1 | `test_group_pages_single_section` | basic grouping |
| 2 | `test_group_pages_multi_type_in_section` | research-theme vs research-question split |
| 3 | `test_pick_alphabetical_stable` | earliest URL per group |
| 4 | `test_pick_handles_unicode` | UTF-8 sort consistency |
| 5 | `test_render_assert_matrix_translates_group_to_url` | override key → URL pattern |
| 6 | `test_render_assert_matrix_empty_overrides` | empty/missing override file works |
| 7 | `test_render_assert_matrix_unknown_group_raises` | typo guard in overrides |
| 8 | `test_rewrite_lighthouserc_preserves_unrelated_fields` | `preset`, `numberOfRuns`, `upload`, base `assertions` survive |
| 9 | `test_rewrite_lighthouserc_mobile_writes_assertmatrix` | mobile gets matrix; desktop doesn't |
| 10 | `test_rewrite_lighthouserc_idempotent` | running twice produces byte-identical output |
| 11 | `test_run_missing_manifest_returns_rc1` | exit code on missing inputs |
| 12 | `test_run_full_round_trip_with_temp_repo` | end-to-end wire-up |

Stdlib `unittest`. Sibling-linter style (mirrors `tools/test_check_*.py`).

### Linter pair count

`gen_lhci_urls.py` is a *generator*, not a *coupling checker*. CLAUDE.md's "Twenty-eight linter pairs" count stays at 28. The sibling-test file follows naming convention for consistency.

---

## 4. CI integration + idempotency

### Workflow step insertion

`.github/workflows/hugo.yaml` — after the page-weight linter, before the desktop LHCI step:

```yaml
      - name: Regenerate LHCI URLs from sitemap
        run: python3 tools/gen_lhci_urls.py
      - name: Run gen_lhci_urls unit tests
        run: python3 -m unittest tools/test_gen_lhci_urls.py -v
```

### `tools/ci-local.sh` mirror

Append the same two invocations in the same position.

### Idempotency strategy — Option A: configs become CI-generated

**Decision:** Committed lighthouserc files stay in git for diff/blame readability, but they get auto-regenerated headers and authors stop hand-editing them.

Header banner (top of each file):
```jsonc
// auto-generated by tools/gen_lhci_urls.py
// to change thresholds: edit tools/lhci-overrides.json
// to change URL picks: kill or add fixtures; the script picks alphabetically-first per (kind, section, type)
```

(JSON doesn't support comments natively. The banner uses JSONC-style `//` and the script strips them on load. LHCI itself uses a JSON parser that tolerates this — confirmed by upstream docs. If LHCI's parser rejects them, fall back to a sibling `lighthouserc.HEADER.md` file referenced by the auto-generated configs' top-level `"comment"` key.)

**Why not Option B (gate that committed configs match script output):** Adds toil (author has to remember to regen + commit on every fixture-affecting change). Defeats half the value.

### Local-author surface

| Change | Action |
|---|---|
| Edit a threshold (e.g., bump essay-single mobile perf to 0.80) | Edit `tools/lhci-overrides.json`, run `python3 tools/gen_lhci_urls.py --dry-run` to preview, then run without `--dry-run` to write, commit `lhci-overrides.json` + the regenerated configs |
| Add a new (kind, section, type) group | No action — script picks it up automatically on next Hugo build |
| Retire a fixture | No action — script picks the next alphabetically |
| Override an existing assertion threshold for the picked URL | Edit `tools/lhci-overrides.json` |

### Failure cascade

| Failure | CI behavior | Author action |
|---|---|---|
| `gen_lhci_urls.py` errors (manifest missing, override typo) | CI fails at the regen step | Fix the upstream cause |
| Script writes a URL that doesn't exist in `public/` | `check_lhci_urls.py` (4.1) catches before LHCI | Investigate why the manifest disagreed with the sitemap |
| Hugo template emits malformed JSON | `json.loads` raises | Fix the template |
| LHCI itself rejects the regenerated config | LHCI step fails with parser error | Fix the schema |

### Performance impact

Reads two files (~few KB each), writes two files. Single-digit milliseconds. Doesn't move CI wall-clock.

---

## 5. Risks + open questions for the plan

These don't block the spec but should be resolved during implementation:

1. **Hugo output format scoping.** Custom output formats can over-emit (one JSON per page section). The plan does a minimal repro — create the output format, run `hugo --minify`, confirm `public/lhci-pages.json` exists at the expected path and there are no spurious per-section JSON files.

2. **Section vs term iteration.** `site.Sections` returns top-level sections only. `/research/themes/` and `/research/questions/` may be subsections requiring separate handling. The plan adds a smoke check that all 12 currently-listed URLs appear in the manifest before fully wiring.

3. **Hostname / port stripping.** Sitemap URLs and `.RelPermalink` differ from LHCI's `http://localhost` prefix. Plan verifies the script's URL-prefix transform with a fixture test.

4. **First-CI-after-merge essay shift.** `example-explorables` sorts before `example-one` alphabetically — both share the `example-` prefix; the first differing byte is `e` (101) vs `o` (111). So the essay representative changes from `example-one` to `example-explorables` on first regen. The group-keyed override (`page:essays:essays` → mobile perf 0.85) migrates automatically; the author should expect the diff in the first post-merge CI run and not be alarmed.

5. **`public/lhci-pages.json` ships to production.** Becomes live at `https://a3madkour.github.io/lhci-pages.json`. Harmless (same URL set as `sitemap.xml`, no PII). Plan does not gate this — `robots.txt` doesn't list it; consistent with `sitemap.xml`.

6. **JSONC-style comments in lighthouserc.** `// ...` comments are non-standard JSON. Plan verifies LHCI's parser accepts them (likely yes — most node-stack tools do). Fallback if rejected: store the header in `lighthouserc.HEADER.md` and reference via top-level `"comment"` field.

7. **`--dry-run` flag.** ~5 LOC for the local-author preview workflow described in §4. Plan includes it.

---

## 6. Follow-ups (queued; not in this slice)

1. **Tier 7.2 — visual-feature autodetect.** Original 4.3 from the queued spec. Fingerprint each LHCI URL by sorted CSS classes + shortcode names; auto-extend the LHCI list when novel signatures appear. **Trigger:** After 7.1 lands and the fingerprint corpus is observable (need 2-3 LHCI runs to characterize noise). ~150 LOC.

2. **Per-essay JS bundle auditing.** LHCI audits HTML pages only. Explorables-bearing essays load per-essay JS bundles that LHCI doesn't independently profile. **Trigger:** First explorable essay where the bundle exceeds page-weight gates. Files in Tier 7.x.

3. **Document author workflow in CLAUDE.md.** Briefly note "LHCI URL list is CI-generated; edit `tools/lhci-overrides.json` for thresholds, not the lighthouserc files." Included in this slice's implementation plan (not a follow-up — listed here for visibility).

---

## 7. Pointers

- **Parent roadmap row:** [`2026-06-07-polish-and-bugfix-roadmap.md`](2026-06-07-polish-and-bugfix-roadmap.md) Tier 7.1.
- **Queued-stub memory:** [`project_lhci_representative_pages_queued`](../../../.claude/memory/project_lhci_representative_pages_queued.md) — original 4.2 entry.
- **4.1 (defense-in-depth):** [`project_lhci_url_validator_complete`](../../../.claude/memory/project_lhci_url_validator_complete.md).
- **Reference for sibling-linter style:** `tools/check_math.py` + `tools/test_check_math.py`.
- **Reference for `run(repo_root)` parity contract:** [`project_tier_4_complete`](../../../.claude/memory/project_tier_4_complete.md).
