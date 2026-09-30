# works/games + works/music org handlers — design

**Date:** 2026-09-28
**Status:** designed; plan next
**Slice ID:** A1 (first slice of the "author everything from Emacs" decomposition)
**Scope:** dotfiles — one new handler module + one new lint module + additive changes to
three shared modules and `a3-pub.sh`; site repo — one new data file and a refactor of one
shipped linter.

**Predecessors:** `2026-07-09-recipe-slice-2-org-authoring-design.md` (the closest
analogue — org authoring for a living section), `2026-05-24-phase-3-b-per-content-type-publisher-design.md`
(the B-series handler contract), `~/dotfiles/.../2026-07-05-publish-pipeline-audit-roadmap.md`
(P3.2, the handler-skeleton duplication this slice deliberately does not close).

---

## §1. Why

`a3madkour-pub/sections` permits `works/games` and `works/music`, but neither appears in
`a3madkour-pub-living--handlers` nor in `a3madkour-pub-deliberate--handlers`. Publishing
either errors with `no handler registered for section`. Both sections are therefore
hand-authored markdown in the site repo today, with no org source, no manifest entry and
no unpublish path.

This is the largest remaining gap in the org authoring surface. An audit of that surface
(2026-09-27) tiered the gaps as:

1. **No path, real content** — `works/games`, `works/music`. ← this slice
2. **Contested ownership** — `streams` (the cron poller already writes
   `content/streams/<slug>/index.md`). Slice A2.
3. **Structural pages** — 19 `_index.md` files, `about`, `credits`. Slice B1.
4. **Curated YAML** — `filter-chips`, `library-shelves`, `library-media`,
   `streams-schedule`. Slice B1.

Slice C, the authoring guide covering every content kind, depends on A1/A2/B1 landing.

## §2. Decisions taken

| Decision | Choice | Rationale |
|---|---|---|
| Publish mode | **Living**, both sections | A game's metadata changes over its life (`status: in-progress` → `playable`, new screenshots, new links) and the works umbrella exists to be a browsable catalogue. Living brings orphan sweep, idempotency and the P2.14 date cascade for free. |
| Module structure | **One module, type branch** | The handler skeleton is already copied 4× (audit row P3.2). Two peer modules would make it 6; one module with a branch makes it 5. Games and music share ~80% of their shape. |
| Close P3.2 here? | **No** | Extracting the skeleton from four shipped, proven handlers inside a slice whose job is two new ones risks breaking garden, research, essays and recipes at once. Prove the fifth copy, extract later from five known-good call sites. |
| Authoring idiom | **`#+HUGO_CUSTOM_FRONT_MATTER:`**, not a `:PROPERTIES:` drawer | See §3. |
| Enum vocabulary | **One JSON file, read by both languages, fail-closed** | See §4. |
| Frontmatter-declared assets | **New optional `extra-refs` on `asset-validate-and-copy`** | See §6. |
| `lyrics_poem` symmetry | **Author declares both sides; lint checks early** | See §7. |

## §3. Authoring surface

Two idioms already exist in the tree: recipes uses a file-level `:PROPERTIES:` drawer
(chosen to align key spellings with org-chef); research uses `#+HUGO_CUSTOM_FRONT_MATTER:`
with whitespace-separated slug lists expanded to site paths by
`a3madkour-pub-frontmatter--parse-slug-list`.

**Games and music follow research.** The drawer route cost recipe Slice 2 two distinct
bugs:

- `org-element` only tags a file-leading `:PROPERTIES:` drawer as `property-drawer` when
  it is the *literal* first buffer element. Keywords-first authoring made it a generic
  `drawer` and silently dropped all metadata.
- ox-hugo renders a generic drawer's contents **into the body**, so the drawer had to be
  stripped before export.

Recipes paid for those because org-chef alignment was worth it. There is no org-chef for
games, so the drawer buys nothing here and re-imports both traps.
`HUGO_CUSTOM_FRONT_MATTER` is ox-hugo-native, position-insensitive, and already carries
the slug-list machinery.

**A claim this spec originally made here was wrong**, and the end-to-end run disproved it:
"no drawer means no strip stage, so the body-leak bug cannot recur by construction." The
drawer is indeed gone, but music's `#+NAME: tracks` table is *also* data that must not
reach the body — and because nothing stripped it, it rendered as a second raw `<table>`
beside the real Tracks section. **The rule is about data-bearing elements, not about
drawers specifically:** anything parsed for frontmatter must be removed before export,
whichever org construct carries it. Music therefore does run a strip stage
(`--strip-named-table`); games, which parse nothing from the body, do not.

### 3.1 A game

```org
:PROPERTIES:
:ID:       3f2a...
:END:
#+TITLE: Mnemosyne
#+DATE: 2026-03-01
#+HUGO_SECTION: works/games
#+HUGO_PUBLISH: t
#+FILETAGS: :godot:procgen:
#+HUGO_SUMMARY: A memory-palace roguelike built for a thesis chapter.
#+HUGO_CUSTOM_FRONT_MATTER: :status playable :game_kind research-prototype
#+HUGO_CUSTOM_FRONT_MATTER: :year 2026 :tagline "Walk a palace you cannot remember."
#+HUGO_CUSTOM_FRONT_MATTER: :itch_url "https://..." :source_url "https://..."
#+HUGO_CUSTOM_FRONT_MATTER: :tech_stack "Godot GDScript" :collaborators "Alice Example"
#+HUGO_CUSTOM_FRONT_MATTER: :research_questions "example-question-one"
#+HUGO_CUSTOM_FRONT_MATTER: :hero hero.png :screenshots "shot-1.png shot-2.png"

Prose body. Renders as `.Content` beneath the hero and the external links.
```

### 3.2 A music release

Same shape, with `:format album :year 2026 :cover cover.png :duration "42:18"`, plus the
track list as an org table — the recipes `#+NAME: ingredients` pattern, parsed with
`org-table-to-lisp`:

```org
#+NAME: tracks
| title       | duration |
|-------------+----------|
| Lorem One   | 3:14     |
| Lorem Two   | 4:20     |
```

### 3.3 Key mapping and three consequences

**Org keys mirror emitted frontmatter keys exactly** — with one documented exception, below.
What the author types is what lands, which keeps the guide (slice C) trivial and makes
debugging a one-step comparison.

**The exception: `platform_embed`.** This principle cannot hold for a key whose value is a
nested map, because `#+HUGO_CUSTOM_FRONT_MATTER:` carries only flat scalars — ox-hugo
round-trips any value as a string. The original design had the author write
`:platform_embed` directly; the end-to-end run proved that **silently does nothing**: the
value arrives as a string, the render key-hook `:omit`s any non-list, and the field
vanishes from the page with no error at any layer. A field that cannot be authored is worse
than an inconsistent one, so `platform_embed` is authored as **two flat keys**,
`:platform_kind` and `:platform_url`, which the music normalizer assembles into the nested
map the site expects. The lint requires both-or-neither, validates `platform_kind` against
the shared vocabulary's `platform_kinds`, and **rejects the direct `:platform_embed` form
outright** rather than dropping it — otherwise anyone following the old spec would hit the
original silent failure.

This is the general lesson, not a one-off: any future works field whose emitted shape is a
map or a list of maps needs either flat component keys assembled in the normalizer (this
pattern) or a named org table parsed from the AST (the `tracks` pattern). It cannot be
carried by a single custom-front-matter key.

1. **List separators are not uniform.** `--coerce-slug-list` splits on whitespace, which
   is correct for slug and filename fields but wrong for free-text ones —
   `:collaborators "Alice Example"` would become two people. The normalizer dispatches
   **per key, not per type**, against this closed list:

   | Separator | Fields | Normalized to |
   |---|---|---|
   | whitespace | `research_questions`, `related_essays`, `related_notes`, `related_works` | site paths via `--parse-slug-list` |
   | whitespace | `screenshots` | bare filenames, left as-is (a filename containing a space is rejected by the lint) |
   | **comma** | `collaborators`, `tech_stack`, `made_with` | trimmed strings, order preserved |

   `tags` is not in this table — it arrives via `#+FILETAGS:` on the existing path and is
   unchanged by this slice.

2. **`hero` is polymorphic.** `check_works_fixtures.py` places `hero` in the shared
   `UMBRELLA_OPTIONAL` set, but requires it to be a **bool** for music (a Bento grid
   directive) while games use it as a **filename**. The org key stays `hero` for both; the
   lint enforces the type per section. Renaming one side would break the mirror principle
   for one field and make the guide explain an exception.

   Music's `hero` and `featured` reach the normalizer as strings, since
   `HUGO_CUSTOM_FRONT_MATTER` carries no type information. Both route through the existing
   `a3madkour-pub-frontmatter--coerce-bool` (P2.9, which already maps the string
   `"false"` to nil) so the emitted YAML is a real boolean rather than a quoted string —
   `check_works_fixtures.py:170` rejects anything that is not a bool.

3. **`year` must be an integer.** `check_works_fixtures.py` rejects a string. The
   normalizer coerces, as the garden normalizer already does for `year` and `weight`.

## §4. The shared enum vocabulary

`check_works_fixtures.py` hardcodes four enum sets: `GAME_STATUSES`, `GAME_KINDS`,
`MUSIC_FORMATS`, `PLATFORM_KINDS`. An org-side lint needs the same four. A second copy in
elisp would be a cross-language drift surface with no test able to observe both halves —
the same shape as the `check_image_ladder.py` problem, which shipped and survived a
review.

**`data/works-vocab.json`**, read by both consumers:

```json
{
  "game_statuses":  ["playable", "in-progress", "archived"],
  "game_kinds":     ["full-release", "jam", "research-prototype", "experiment"],
  "music_formats":  ["album", "track", "experiment", "live"],
  "platform_kinds": ["bandcamp", "soundcloud", "youtube"]
}
```

**JSON, not YAML** — both languages parse it with zero new dependencies (`json-parse-string`
is built into Emacs 27+; Python has `json`). YAML would force an elisp YAML package into
the dotfiles dependency tree to read four string lists.

**`data/`, not `tools/`** — precedent: `check_filter_chips_config.py` already reads
`data/filter-chips.yaml`. It also leaves the door open for a template to read the
vocabulary later. If one ever does: `index site.Data "works-vocab"`, never dot syntax.

**Scope is the four enum lists only.** Not the required/optional field sets — those are
entangled with Python set algebra (`GAME_OPTIONAL | UMBRELLA_OPTIONAL`) and moving them
would be a far larger refactor of a shipped gate for a smaller gain. A misspelled *key*
fails loudly in CI regardless; a misspelled enum *value* is what benefits from an early
check.

**Both consumers fail closed.** This is what makes it one source rather than two.
`check_works_fixtures.py` errors if the file is missing or malformed and never falls back
to a hardcoded copy — a fallback would silently restore the drift surface being removed.
`a3madkour-works-lint.el` errors if it cannot resolve or parse the file rather than
skipping validation. The residual failure mode is the elisp module pointing at a stale
path after a repo reorganisation, which now fails loudly at publish time.

## §5. Handler pipeline

One module, `a3madkour-publish-works.el`, registering two entries that share one entry
point — the shape `library.el` uses for four media and `research.el` for two types:

```elisp
(with-eval-after-load 'a3madkour-publish-works
  (dolist (section '("works/games" "works/music"))
    (add-to-list 'a3madkour-pub-living--handlers
                 (cons section 'a3madkour-pub-works/publish-works-file))))
```

**No new dir defcustom.** `a3madkour-pub-living--collect-triples` discovers living-section
files by walking `a3madkour-pub/org-notes-dir` recursively and matching each file's
`#+HUGO_SECTION:`. `poetry-dir` and `essays-dir` exist only because those sections are
*deliberate* and addressed by path. A game org file may live anywhere under the notes
tree. This also removes the failure mode that bit poetry, where a wrong dir default
silently cleanup-staled the audio.

**Stages**, per file, inside one `condition-case` that calls `on-done` exactly once with
`'ok` / `'err` / `'cancelled`:

1. resolve metadata — id, slug, url
2. works-lint (default-on; `--skip-works-check`)
3. dispatch on section → games branch / music branch
4. *music only* — parse `#+NAME: tracks` via `org-table-to-lisp`
5. pre-export rewrite to a tmp file (`rewrite-to-tmp-file`) — resolves org-roam id links
6. ox-hugo export → body markdown
7. normalize — new `works-games` / `works-music` branches in `frontmatter.el`
8. inject type-specific keys (`tracks`)
9. render frontmatter via `a3madkour-publish-yaml.el` with a key-hook for the nested
   flow-style values (`tracks`, `platform_embed`) — the seam research uses for `outputs`
   and recipes for `ingredients`
10. write-if-different → `content/works/{games,music}/<slug>/index.md`
11. asset copy (§6)
12. `record-publish` with `(or (plist-get md :state) 'live)` and the P2.14-resolved date

### 5.1 The two-symbol convention

Established by poetry and already the cause of one caught bug. Dispatch alist,
`#+HUGO_SECTION:` and `a3madkour-pub/sections` use the **slash** form (`works/games`);
the normalize whitelist `a3madkour-pub-frontmatter--known-sections` and its dispatch arm
use the **hyphen** form (`works-games`). A1 must apply this deliberately, not rediscover
it.

### 5.2 `a3-pub.sh`

All three `-l` blocks need `-l a3madkour-publish-works` and `-l a3madkour-works-lint`,
plus the `--skip-works-check` flag, its exported `A3_PUB_SKIP_WORKS_CHECK` env var, and
the `--eval` that sets the enabled flag from it. Recipes wired exactly this shape; it is
easy to half-complete.

### 5.3 Targeted fix: `collect-triples` walks the tree once

`collect-triples` nests `directory-files-recursively` *inside* the per-handler loop, so it
walks the entire notes tree once per registered section — eight full walks today, ten
after A1. Inverting it to walk once and dispatch per file is roughly five lines and
removes an O(handlers × files) that this slice would otherwise worsen. Included because
A1 is already changing this registration surface.

## §6. Assets

Games declare `hero` and a `screenshots` list; music declares `cover`. None are body
links. `a3madkour-pub/asset-validate-and-copy (org-file bundle-dest-dir &optional
source-note-id dry-run)` derives its reference set from `--extract-asset-refs`, which
scans **body org links only**, and then removes any bundle file outside that set
(cleanup-stale).

This has already bitten twice:

- **Recipes bug #4** — a bare `:image:` filename was never copied into the bundle,
  producing a broken JSON-LD image URL that no other check could see.
- **Poetry** — the audio copy must run *after* `asset-validate-and-copy`, or cleanup-stale
  deletes it. The fix was a stage number and a comment, correct only while nobody
  reorders two stages.

**Add an optional `extra-refs` parameter to `asset-validate-and-copy`.** The works handler
collects its frontmatter-declared basenames and passes them in, so they become *part of*
the reference set instead of racing cleanup-stale afterwards. The parameter defaults to
nil, leaving all five existing callers byte-for-byte unaffected — additive to shared
infra, not a refactor of it.

**The poetry and recipes back-port is explicitly out of scope for A1.** Prove the seam on
a new handler first, then migrate two proven ones in their own change.

**Source location:** `<org-file-dir>/assets/<id>/<filename>` — the per-note asset dir
keyed by org-roam id that poetry established.

**Lint responsibility:** every filename named in `hero`, `cover` or `screenshots` must
exist on disk at publish time, reported as an org `file:line` error. This is the check CI
genuinely cannot make early — by the time `check_works_fixtures.py` runs, a missing
screenshot is an already-committed broken reference.

## §7. The `lyrics_poem` ↔ `set_to_music` obligation

`check_works_links.py` enforces the round trip: a music item declaring `lyrics_poem`
requires the target poem to declare `set_to_music` back. The two ends are written by
**different handlers in different modes** — music by the new living works handler, the poem
by `poetry.el` under deliberate publish — so satisfying one end never satisfies the other.

**Rejected: the music handler writes the back-link into the poem's bundle.** One handler
writing another's output breaks the single-writer invariant this design rests on, and it
would put the poem's bundle out of sync with its own org source; the next
`a3-publish-deliberate` on that poem would silently revert it. That is a worse, and
intermittent, bug than the one it fixes.

**Chosen: the author declares both sides, and the lint makes that cheap.**

1. `a3madkour-works-lint.el` resolves the counterpart **org file** and verifies it declares
   the reciprocal key. A mismatch is a `file:line` error, before anything exports.
2. Org-source symmetry is not sufficient alone: the poem's org file can be correct while
   its *bundle* is stale, since poetry publishes deliberately. So when the music handler
   publishes and the counterpart bundle lacks the back-link, it emits a **warning** naming
   the exact command — `a3-publish-deliberate ~/org/notes/works/poetry/<slug>.org`. A
   warning rather than an error, because the bundle is legitimately allowed to lag until
   the author chooses to republish.

**Recorded for a later slice, not done here:** a bidirectional link stored twice is a
denormalization that will keep costing. The site could derive `set_to_music` at render
time by scanning music pages for `lyrics_poem`, making the poem's copy unnecessary and the
symmetry unbreakable by construction. That changes a shipped template *and* a shipped
linter, so it does not belong in A1 — but it is the real fix, and A1 should not imply the
current shape is correct.

## §8. Verification

Every guard is mutation-tested: broken, then watched to fail. A guard observed passing
proves nothing.

| Guard | Mutation that must fail it |
|---|---|
| Vocabulary is single-source | `"playable"` → `"playible"` in the JSON; all four game fixtures must fail the Python linter |
| Both sides fail closed | Delete `data/works-vocab.json`; Python linter and elisp lint must both error, not skip |
| `extra-refs` | Publish a game with a screenshot; the file must land in the bundle **and** survive cleanup-stale |
| Asset existence | Delete a declared screenshot; publish must fail with `file:line`, not emit a dangling name |
| Symmetry lint | Point `lyrics_poem` at a poem whose org lacks `set_to_music`; lint must error |
| `collect-triples` inversion | A file matching a registered section is collected exactly once; the tree is walked once total |
| `hero` polymorphism | A filename in music's `hero` and a bool in games' must each be rejected |
| List separators | `:collaborators "Alice Example"` must emit one name, not two; `:research_questions "a b"` must emit two paths |
| Bool coercion | Music's `:hero t` must emit an unquoted `true`, which `check_works_fixtures.py:170` accepts |

**Green ERT is not the completion bar.** Recipe Slice 2 passed 780/780 while two
integration bugs sat in the tree, because tests bypass `note-section` and ox-hugo. A1
requires a **real end-to-end run**: an actual game and an actual music org file, through
real ox-hugo, into the site repo, with `check_works_fixtures.py` and
`check_works_links.py` clean and Hugo building both pages.

## §8a. What the end-to-end run found (2026-09-29)

The scoped end-to-end run — real ox-hugo, real Hugo, real site linters — found **six
defects that 829 green unit tests did not**, two of which meant `check_works_fixtures.py`
failed on every real publish. They are recorded here because the *class* matters more than
the individual fixes:

| # | Defect | Why the unit tests missed it |
|---|---|---|
| 1 | The lint read the note ID from a `#+ID:` keyword, not the `:PROPERTIES: :ID:` drawer, so the asset rule computed the wrong directory and false-failed every declared asset | **The lint's own fixtures authored `#+ID:` too** — the tests certified the bug |
| 2 | Rule 5's space guard rejected the documented multi-file form `:screenshots "a.png b.png"` | No test used more than one screenshot |
| 3 | `lastmod` (required) was never set; the normalizer ignored the P2.14 cascade the handler binds | Unit tests assert on keys they pass in, not on the full required set |
| 4 | No allowed-key filtering, so ox-hugo's `author`/`slug` leaked in | Tests feed hand-built alists; only real ox-hugo adds those keys |
| 5 | The `#+NAME: tracks` table was never stripped pre-export and rendered as a second raw `<table>` | Body output is only visible after a real export |
| 6 | `platform_embed` was unauthorable (see §3.3) | Tests called the renderer with a real alist; only ox-hugo flattens it |

Every one of these needed real ox-hugo, real Hugo, or the real authoring convention to
surface. The standing conclusion for any future handler in this family: **green ERT is not
an acceptance gate.** A slice is not done until one real file has gone through the real
exporter into the real site and passed the real linters.

## §9. Out of scope

- Closing P3.2 (handler-skeleton extraction) — deferred until five known-good call sites exist.
- Back-porting `extra-refs` to poetry and recipes.
- Deriving `set_to_music` at render time (§7).
- `streams`, section indexes, curated YAML — slices A2 and B1.
- The authoring guide — slice C, which depends on this.
