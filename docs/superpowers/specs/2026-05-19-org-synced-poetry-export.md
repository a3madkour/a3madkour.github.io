# Org → synced-poetry export — design

**Status:** Designed 2026-06-12. Brainstorm transcript folded into this spec; the original stub (filed 2026-05-19) has been replaced.

**Phase fit:** Phase 3 (org-mode pipeline). Rides the **deliberate publish** command (`a3madkour-publish-deliberate.el`), not the frequent garden/library/research publish. Hard dependency on B.0 shared infra (already shipped). No new Hugo/JS/CSS — the consuming runtime shipped 2026-05-19 (see `[[project-time-synced-poetry-slice]]`).

**Roadmap row:** Tier 8.2 in `docs/superpowers/specs/2026-06-07-polish-and-bugfix-roadmap.md`.

## Goal

Make the elisp/ox-hugo poetry export emit the shipped Hugo-side synced-poetry contract from real org content, so an authored poem with spoken-timing annotations round-trips to a working synced page with zero hand-editing of the exported markdown.

## The contract the export MUST satisfy (already enforced)

The exporter's output for a poem is markdown body + frontmatter; it must match what `layouts/works-poetry/single.html` → `partials/works/synced-text-parser.html` parses and what `tools/check_poetry_synced.py` + `tools/check_works_fixtures.py` validate:

1. **Marker grammar** (spec `docs/superpowers/specs/2026-05-13-time-synced-poetry-design.md` §3): `[mm:ss]` or `[mm:ss.f]` — minutes 0–99, seconds two digits 00–59, optional 1–2 digit fraction. Emit canonical zero-padded form (e.g. `[00:08]`).
2. **Placement:** a marker at line start (after optional leading whitespace) → line-level time; or immediately preceded by whitespace, glued to the word it times (`[00:06]eiusmod`). No embedded `word[00:06]`.
3. **Escape:** a literal bracket-pair timecode in the poem text must be emitted backslash-escaped `\[mm:ss]` (renders as literal, never a timing event, bypasses shape-check).
4. **Frontmatter `audio_url`** (optional): relative path (bundle asset, exported alongside `index.md`) or absolute `https?://` URL. Present ⇒ audio-driven playback + the §9 BibTeX "With audio reading." note fires automatically. Absent ⇒ animation-driven (if any markers exist) or plain poem (if no markers).
5. Must pass `python3 tools/check_poetry_synced.py` (zero errors; untimed-line / non-monotonic / trailing-marker are warnings only) and `python3 tools/check_works_fixtures.py` (poetry contract incl. optional `audio_url`).
6. Markers are body text the exporter writes; they must **not** leak into `summary:` / `description` (the runtime slice fixed the `<meta>` fallback, but the exporter should still set a clean `summary:` for real poems).

The shipped fixture `content/works/poetry/example-poem-synced/index.md` is the byte-shape target.

## Authoring surface

A poem is an `.org` file under `~/org/notes/works/poetry/<slug>.org`. Minimum shape:

```org
:PROPERTIES:
:ID: <uuid>
:END:
#+TITLE: Untitled Poem
#+DATE: 2026-06-12
#+AUDIO: reading.mp3                 ;; optional — relative filename OR absolute URL
#+HUGO_TAGS: example synced          ;; optional, ox-hugo normal
#+HUGO_CUSTOM_FRONT_MATTER: :collection greenhouse-demos  ;; optional

[00:01]Lorem [00:02]ipsum [00:03]dolor [00:04]sit
[00:05]amet [00:06]consectetur [00:07]adipiscing [00:08]elit

[00:17]Duis aute *irure* reprehenderit
[00:18]ut [00:19]enim \[00:99] [00:20]minim [00:21]veniam
```

The `:PROPERTIES:` drawer is file-level (org-roam-compatible); the poem body has no `** Heading` because the shipped markdown body has no `## Heading` either — title lives in frontmatter only. Plan must confirm B.4 / shared write infra honors a file-level `:ID:` for `works-poetry` (essays may use heading-level — verify before assuming parity).

Decisions baked into this surface:

- **Timing markers live inline in the body.** `[mm:ss]` line-start = line-level, whitespace + glued = word-level, `\[mm:ss]` = literal escape. Default expectation: ox-hugo passes the body through verbatim and the exporter does **not** rewrite markers — see §Risks #1 for the empirical-verification + protect-and-restore fallback. Author sees what ships.
- **Audio is declared once via `#+AUDIO:`.** Relative filenames are looked up in the per-poem asset dir `~/org/notes/works/poetry/assets/<ID>/` (mirroring the essays asset-dir convention from B.4 / D.2). Absolute URLs (`https?://…`) pass through. Single knob, both shapes covered.
- **No custom org link type, no side-car timing block.** Both were considered (alternative authoring forms in the brainstorm); inline literal won on zero-new-elisp and what-you-see-is-what-you-ship.

## Routing & module structure

`a3madkour-pub/note-section` already returns a section symbol per file. A new branch returns `'works-poetry` for files under `~/org/notes/works/poetry/`. The dispatch alist in `a3madkour-publish-deliberate.el` gains one entry:

```elisp
(defvar a3madkour-pub-deliberate--handlers
  '((essays       . a3madkour-pub-essays/publish-essay-file)
    (works-poetry . a3madkour-pub-poetry/publish-poetry-file)))
```

`a3madkour-publish-poetry.el` is a **peer of `a3madkour-publish-essays.el`**, not a subordinate. Both call into the existing shared B.0 infra (`a3madkour-pub-rewrite/rewrite-to-tmp-file`, `a3madkour-pub-export/export-file`, `a3madkour-pub/asset-validate-and-copy`, `a3madkour-pub-record/record-publish`). The essays handler is **not modified** by this slice.

Rationale for peer (vs. wrap-essays or shared-core refactor):

- Wrapping essays would force opt-out of its `has_*` scan + essay-flavored frontmatter normalizer — fragile.
- A core/adapter refactor is premature with one sibling. Revisit if a third handler (e.g. music-side lyrics export) emerges.
- Peer keeps blast radius scoped to one new file + one dispatch-alist line.

`a3-pub.sh` needs `-l a3madkour-publish-poetry` appended (per `[[feedback-plan-wrapper-script-updates]]`).

## Handler pipeline (`a3madkour-pub-poetry/publish-poetry-file`)

Six stages, mostly orchestrating shared infra:

1. **Pre-export rewrite** — call `a3madkour-pub-rewrite/rewrite-to-tmp-file` (link normalization). Markers are paragraph text, untouched by the rewriter.
2. **ox-hugo export** — `a3madkour-pub-export/export-file` produces a markdown buffer. Markers and the `\[mm:ss]` escape should pass through verbatim (verified by fixture round-trip during plan; if ox-hugo eats the backslash, fall back to a protect-and-restore pre-export pass like D.2's strategies — flagged in §Risks, not pre-emptively coded).
3. **Frontmatter normalize** — new `a3madkour-pub-frontmatter--normalize-works-poetry` that:
   - Strips/ignores essay-only keys ox-hugo may have set.
   - Sets `lines:` to the **count of non-blank lines in the emitted markdown body** (auto-derived; author never declares it). Stanza-break blank lines excluded; lines with only `[mm:ss]` markers still count; any leading H2 heading that survives export is excluded.
   - Reads `#+AUDIO:` value: `https?://…` → `audio_url: "<url>"`; else → `audio_url: "<filename>"` (the bundled relative path).
   - Ensures `summary:` exists and **strips any `[mm:ss]` or `\[mm:ss]` substrings from it** (covers the §6 leak rule even if author copy-pastes from body).
   - Passes through `collection`, `tags`, `set_to_music`, `source_stream`, `tile_size`, `featured`, `hero`.
4. **Asset validation + copy** — `a3madkour-pub/asset-validate-and-copy` (existing) handles body-link assets if any. New small helper `a3madkour-pub-poetry--copy-audio-asset`: when `#+AUDIO:` is relative, resolve to `~/org/notes/works/poetry/assets/<ID>/<filename>`, validate (extension ∈ `{mp3, m4a, ogg, wav}`, exists, non-zero size), copy into the bundle next to `index.md`. Absolute URLs are not fetched.
5. **Write `index.md` if changed** — generic write path (existing infra).
6. **Record publish** — `a3madkour-pub-record/record-publish 'published` on success, `'failed` on any error (per Tier 1.1 self-heal convention).

**Out of pipeline for this slice:** D.2 multi-export dispatch is skipped on poetry (no PDF/Word target shape exists for synced poems). If `#+multi_export: t` appears on a poem, the handler logs a warning and ignores it rather than dispatching.

## Lint coupling & failure modes

The handler is intentionally loose; the **site-side linters are the gate**. After write, the next `tools/ci-local.sh` (or CI) runs `check_works_fixtures.py` + `check_poetry_synced.py`.

The handler adds two **soft warnings** that surface in `:warnings` on the publish result (matching Tier 1.10's `:orphan-warnings` precedent) — they don't fail the publish, the author decides whether to fix:

1. `#+AUDIO:` is set but the body has zero `[mm:ss]` markers → "you declared audio but the poem isn't timed — the synced runtime won't engage."
2. Body has `[mm:ss]` markers but no `#+AUDIO:` → "synced poem with no audio — the runtime will use animation-driven sync." (Valid — animation-driven sync is a real mode — but worth surfacing once.)

**Hard failures** (raise during publish, no `index.md` written):

- `#+AUDIO:` is relative but the file doesn't exist in `assets/<ID>/`.
- `#+AUDIO:` is relative but the extension is outside the allowlist.
- No `#+TITLE:` or `:ID:` (generic B.0 preconditions, not poetry-specific).

The runtime handles all three legitimate modes (no-markers, markers-only animation, markers + audio). The exporter mirrors that — it does not require markers ↔ audio pairing.

## Tests & closure bar

### ert tests

Added to dotfiles test suite, following B.2 / B.4 pattern:

1. `a3madkour-pub-poetry/section-detection` — `~/org/notes/works/poetry/foo.org` → `'works-poetry`.
2. `a3madkour-pub-poetry/lines-counter` — auto-counts non-blank body lines correctly (stanza breaks excluded; line with only a marker still counts; escape doesn't disturb count).
3. `a3madkour-pub-poetry/audio-keyword-relative` — `#+AUDIO: reading.mp3` → frontmatter `audio_url: "reading.mp3"`, copy invoked with `assets/<ID>/reading.mp3`.
4. `a3madkour-pub-poetry/audio-keyword-absolute` — `#+AUDIO: https://…` → frontmatter `audio_url: "https://…"`, no copy.
5. `a3madkour-pub-poetry/audio-missing-file` — relative `#+AUDIO:` pointing at missing file → raises.
6. `a3madkour-pub-poetry/audio-bad-extension` — `#+AUDIO: notes.txt` → raises.
7. `a3madkour-pub-poetry/summary-marker-scrub` — `#+HUGO_DESCRIPTION:` containing `[00:08]ipsum` → summary emitted with markers removed.
8. `a3madkour-pub-poetry/normalize-key-allowlist` — passes through `collection`, `tags`, `set_to_music`, `source_stream`, `tile_size`, `featured`, `hero`; drops essay-only keys.
9. `a3madkour-pub-poetry/multi-export-warn-and-skip` — `#+multi_export: t` on a poem → warning surfaced, D.2 dispatch not invoked.
10. `a3madkour-pub-poetry/soft-warning-audio-without-markers` — `#+AUDIO:` set, body untimed → soft warning on the publish result, no failure.
11. `a3madkour-pub-poetry/soft-warning-markers-without-audio` — body timed, `#+AUDIO:` absent → soft warning.

Expected test budget: dotfiles `662 → ~675` ert tests.

### Integration test

(`a3madkour-pub-poetry-integration-test.el`, mirrors B.2 / B.4 pattern.)

12. **Round-trip dummy fixture** — author a minimal in-test `.org` fixture mirroring the shipped `example-poem-synced/index.md`, publish it to a tmpdir bundle, assert the emitted markdown body matches the shipped fixture byte-for-byte (or with documented byte-level differences) and passes both site-side linters via subprocess.

### Closure bar (Full scope)

The slice closes only when **a real authored poem with real timings + a real audio asset is live on master** under `content/works/poetry/<slug>/`. That requires the author to: (a) write/select a poem, (b) annotate it with `[mm:ss]` markers against an audio recording, (c) drop the audio file in `assets/<ID>/`, (d) run the publish, (e) verify site-side linters + dev-server playback, (f) commit + push site repo. Plan must call this out as the final manual gate, distinct from elisp shipment.

## Risks & open items for the plan

1. **ox-hugo backslash-escape behavior is empirically untested.** ox-hugo may eat `\[mm:ss]` (Org's escape semantics in paragraph text) and emit a bare `[mm:ss]` to markdown — which the runtime would then parse as a real timing event. Plan's first integration task is to round-trip the dummy fixture and **observe** what reaches `index.md`. If the backslash is consumed: add a pre-export protect-and-restore pass (replace `\[` with a sentinel before export, restore after, mirrors D.2's strategies). If preserved: nothing to do.
2. **`#+AUDIO:` keyword interaction with `a3madkour-pub-keywords/extract`.** Per `[[reference-dotfiles-keywords-api]]` the canonical reader is `extract` + `boolean-p`, not `org-collect-keywords`. The plan must use the canonical API and add `AUDIO` to whatever keyword registry the project keeps (if one exists — confirm during plan).
3. **Page-bundle directory for `works/poetry/`.** Confirm during plan that B.4 / shared write infra already produces `content/works/poetry/<slug>/` as a page bundle (not a single `<slug>.md`) — the runtime relies on the bundle layout for audio sibling files. If not currently handled for the `works/poetry/` section structure, that's a small extension inside this slice.
4. **`url-history.yaml` integration.** Per A.1 conventions every published slug gets recorded for redirect-stability. Confirm the poetry handler emits the right `url-history` entry shape (probably `works/poetry/<slug>` path) — small if it just calls existing infra, larger if `works-poetry` is a new top-level key.
5. **Marker placement gotchas.** Author may write `word[00:08]` (no leading whitespace) by accident. Runtime treats this as malformed; linter flags it. Soft-warn in handler? Probably no — the linter catches it; double-coverage is noise.
6. **Per-poem asset dir bootstrap.** The directory `~/org/notes/works/poetry/assets/<ID>/` doesn't exist until the author creates it. The handler validates the file path on `#+AUDIO:` (raises if missing). Authoring convention: `mkdir -p assets/<ID> && cp ~/Downloads/reading.mp3 .` — a one-time setup, no tooling. Plan can include a tiny `a3madkour-pub-poetry/ensure-asset-dir` helper if it shaves friction, but YAGNI by default.
7. **Site-side fixture / linter changes required: none expected.** The slice consumes the existing runtime contract verbatim. If something forces a linter tweak (e.g. `audio_url` extension allowlist), that's a sign the design has drifted — re-open this spec rather than papering it in the plan.

## Out of scope

The synced-lyrics (music, two-column) runtime and its own org export — separate already-deferred feature; it will reuse `synced-text-parser.html` but its export contract is filed separately when that runtime is built.

## Touch estimate (informal, for scheduling only)

- Dotfiles: one new `a3madkour-publish-poetry.el` (~150–250 LOC), one new frontmatter normalizer alist entry, one dispatch-alist line, one `a3-pub.sh` `-l` line, ~12 ert tests + 1 integration test.
- Site repo: zero code; the slice produces author content under `content/works/poetry/<real-slug>/` only as part of the Full-scope closure gate.
- Plan drafted after spec approval via `superpowers:writing-plans`.
