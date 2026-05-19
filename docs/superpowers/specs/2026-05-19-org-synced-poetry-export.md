# Org → synced-poetry export — stub spec

**Status:** Queued stub (no plan yet). Filed 2026-05-19 after the time-synced-poetry runtime slice shipped (`23e997b`). Per the project's "design-batch / file-a-slice" convention this is a contract stub only — when scheduled, invoke `superpowers:brainstorming` (org-side authoring affordance is genuinely open) then `superpowers:writing-plans` against this file.

**Phase fit:** Phase 3 (org-mode pipeline). Rides the **Essay / poetry publish** command (the per-post, deliberate one), not the frequent garden/library/research publish. Hard dependency on Phase 3 Slice 1/2 existing (the elisp + ox-hugo publish path). No new runtime work — the consuming runtime already shipped.

## Goal

The time-synced poetry runtime (shipped 2026-05-19) consumes a fixed Hugo-side contract. This slice makes the **elisp/ox-hugo poetry export emit that contract from real org content**, so an authored poem with spoken-timing annotations round-trips to a working synced page with zero hand-editing of the exported markdown.

## The contract the export MUST satisfy (already enforced by the shipped slice)

The exporter's output for a poem is just markdown body + frontmatter; it must match what `layouts/works-poetry/single.html` → `partials/works/synced-text-parser.html` parses and what `tools/check_poetry_synced.py` + `tools/check_works_fixtures.py` validate:

1. **Marker grammar** (spec `docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md` §3): `[mm:ss]` or `[mm:ss.f]` — minutes 0–99, seconds two digits 00–59, optional 1–2 digit fraction. Emit canonical zero-padded form (e.g. `[00:08]`).
2. **Placement:** a marker is at line start (after optional leading whitespace) → line-level time; or immediately preceded by whitespace, glued to the word it times (`[00:06]eiusmod`). No embedded `word[00:06]`.
3. **Escape:** a literal bracket-pair timecode in the poem text must be emitted backslash-escaped `\[mm:ss]` (renders as literal `[mm:ss]`, never a timing event, bypasses shape-check).
4. **Frontmatter `audio_url`** (optional): relative path (page-bundle asset, exported alongside `index.md`) or absolute `https?://` URL. Present ⇒ audio-driven playback + the §9 BibTeX "With audio reading." note fires automatically. Absent ⇒ animation-driven.
5. Must pass `python3 tools/check_poetry_synced.py` (zero errors; untimed-line / non-monotonic / trailing-marker are warnings only) and `python3 tools/check_works_fixtures.py` (poetry contract incl. optional `audio_url`).
6. Markers are body text the exporter writes; they must **not** leak into `summary:`/`description` (the runtime slice fixed the `<meta>` fallback, but the exporter should still set a clean `summary:` for real poems).

## Open question for brainstorming-when-scheduled (do NOT resolve now)

How does the author annotate timing in **org** so ox-hugo emits the markdown markers? Candidates (not decided): inline `[mm:ss]` written literally in the org poem block; a custom org affordance / link type; a side-car timing list mapped to lines; derivation from an audio transcript. Also: how `audio_url` is declared in org (org keyword / property drawer) and how the audio asset is carried into the page bundle. These are authoring-surface design questions — defer to the brainstorm.

## Out of scope

The synced-lyrics (music, two-column) runtime and its own org export — separate already-deferred feature; it will reuse `synced-text-parser.html` but its export contract is filed separately when that runtime is built.

## Touch estimate (informal, for scheduling only)

elisp exporter extension + ox-hugo filter (the bulk), one round-trip fixture authored in org → exported → asserted against the existing linters, no new Hugo/JS/CSS. Plan drafted only when scheduled.
