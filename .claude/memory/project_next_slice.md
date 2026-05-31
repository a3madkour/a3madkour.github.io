---
name: next-slice
description: "Session-start pointer — next slice is B.4 (essays handler). B.3 shipped 2026-05-31: per-page Hugo bundles for both research cascade types (themes + questions sharing one handler); 6 stub bundles emitted from ~/org/notes/research-{themes,questions}-example-*.org replacing 9 hand-authored fixtures; closes B.1.x #10 (fs-mtime cascade). 353 ert + 26 Python integration tests. Per spec §12 sequencing: B.4 → B.5 (works) → B.6 (streams) → B.7 (about) → F → C → D → E."
metadata: 
  node_type: memory
  type: project
  originSessionId: c1b06244-57c3-4b45-89d3-e1e2df8781c2
---

**Next slice = B.4 — essays handler.** B.3 shipped 2026-05-31; see [[b3-complete]].

Per design spec §12 slice ordering: A → B.0 → B.1 → B.1.1 → B.2 → B.3 → **B.4 (next)** → B.5 → B.6 → B.7 → F → C → D → E.

## What B.4 must do

Essays are per-page Hugo bundles (`content/essays/<slug>/index.md`), like garden + research. So B.4 reuses the bundle pipeline shape (ox-hugo invoke, frontmatter normalize, link-rewrite, asset-copy, write-if-different, record-publish).

Essays are the FIRST `publish-deliberate` slice (essays are per-post, deliberate; not the frequent+idempotent living set). Some new infrastructure:
- `a3-publish-deliberate <file>` command (already scaffolded in B.0) gets its first real handler.
- The "two publish commands" rule ([[phase-3-two-publish-commands]]) requires essays to be invoked manually per-post.

Required frontmatter contract (see CLAUDE.md "Essays"): `title, date, lastmod, draft, summary, tags, series, series_order, toc, has_sidenotes, has_citations, has_footnotes, has_math, has_widgets, has_video_sync`. Optional: `tile_size, featured, hero`.

The novel piece is **`has_*` boolean detection** — scan the post-export markdown body for shortcode patterns and set the frontmatter flag automatically:
- `has_sidenotes` ← `{{< sidenote >}}` present
- `has_citations` ← `{{< cite >}}` present
- `has_footnotes` ← `[^...]` footnote refs present
- `has_math` ← `\(...\)` or `\[...\]` math delimiters
- `has_widgets` ← `{{< widget >}}` present
- `has_video_sync` ← `{{< video-sync >}}` present

Author can override per-essay via explicit `#+HUGO_HAS_<X>:` keyword.

## Special considerations carried forward

- **Slash-form section paths** — essays is single-level (`"essays"`), so this convention doesn't add new wrinkles. Dispatch key = section symbol = "essays".
- **`#+HUGO_SECTION:` source value** — single-level, so `essays` (no slash). Matches garden's pattern.
- **last_modified cascade** ([[b3-complete]] #1) — wire essays normalizer into the shared `--last-modified-cascade`.
- **`--rewrite-to-tmp-file` duplication** ([[b3-complete]] follow-up #2): essays would be the third copy. Extract to a shared module BEFORE B.4 lands or accept the third copy as the breaking point.
- **`--inject-description` not needed** — essays use ox-hugo native `#+HUGO_SUMMARY: → summary:` (not `description:`). But the `has_*` detection IS a new injection-style pattern.
- **`hero` / `featured` / `tile_size` pass-through** — Hugo template-side display hints; B emits as-authored.
- **Series infrastructure** (`series` + `series_order` int) — pass-through, no validation in B.

## State of the world at session start

**Site repo (`/Users/a3madkour/Sync/Workspace/a3madkour.github.io/`):**
- master = `bba6066` (per the user's push decision; may not be at origin yet).
- 6 B-emitted research bundles (`example-theme-{one,two}`, `example-question-{one,two,three,four}`) + 4 B-emitted garden bundles.
- `data/{reading,listening,playing,watching}.yaml` still B-emitted stubs (B.2 Task 17 spot-check; real corpus pending).
- 26 Python integration fixtures passing.

**Dotfiles (`~/dotfiles/`):**
- main = `71fabe3`.
- 353 ert tests passing.

**Personal notes (`~/org/notes/`):**
- 4 garden notes + 4 library stub files + 6 research stub files annotated.
- No essay notes annotated yet — B.4 spot-check will seed a few.

## Recommended session start

1. Read site CLAUDE.md (essay frontmatter contract section) + [[b3-complete]] + [[b2-complete]] (for the per-medium pattern, even though essays are per-page) + [[phase-3-decomposition]].
2. Read parent B spec `docs/superpowers/specs/2026-05-24-phase-3-b-per-content-type-publisher-design.md` §7 essay-specific subsection + §11 transition (essays fixtures get replaced in B.4).
3. `superpowers:brainstorming` for B.4 — open design questions: `has_*` detection on post-export markdown vs. raw source scanning; whether to extract `--rewrite-to-tmp-file` to shared module now; publish-deliberate UI/CLI shape.
4. Then `superpowers:writing-plans` for the implementation.

## Pending non-B.4 follow-ups

Logged in [[b3-complete]] §"Known issues / B.3.x follow-ups":
- `--coerce-year` `_file` arg unused
- `--rewrite-to-tmp-file` extract to shared module (becomes acute when B.4 adds third copy)
- Library's `last_modified` cascade upgrade
- `--render-yaml-value` cell-plain-text assumption docstring
- Dotfiles ergonomics for outputs table (#13 from B.3 spec)
- B.2 Task 17 real-corpus spot-check (pending real library authoring)
- B.3 Task 17 real-corpus spot-check (pending real research authoring)

If author wants to pause B and clean up before B.4: B.3.x follow-ups #2 (extract `--rewrite-to-tmp-file`) is the highest-leverage one before adding a third copy.
