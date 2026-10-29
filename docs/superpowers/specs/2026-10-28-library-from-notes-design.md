# Library from notes — design

Date: 2026-10-28. Status: draft for approval. Part of the S1 dogfood (library step).
Repos: site (this repo) and dotfiles (`~/emacs-configs` = `~/dotfiles/emacs-configs`).

## 1. Intent

Abdelrahman reads, listens to, plays and watches things, and writes notes about some of them. Today the
same book can exist as three unrelated records: a `queue.org` entry, a ref note in
`~/org/notes/ref-notes/`, and a hand-typed heading in `~/org/notes/library-reading.org`. None of them
points at the others. Status and dates are typed twice, finishing a book in the queue never reaches the
library, and only Boox reading has any tooling.

What he wants, in his words: "write a note about it in some way, have it be in my notes files and have it
be easily exportable to the website library, but have the option to opt out, so let's not make it public
by default."

The design: **one org note per item is the only record.** The reading queue and the Boox flow write
status and dates onto that note. One command shares the note. Sharing publishes a garden page *and* a
library row that link to each other. One command unshares both.

## 2. Decisions made by the user

- The item's note lives in his notes files. It is private by default, and publishing is opt-in per item
  with an easy opt-out.
- **If an item is in the library, it is in the garden.** Sharing is one decision that covers both
  surfaces. There is never a library row without a garden page.
- **Only the parts he writes for the site go on the site.** Highlights, noter section headings, margin
  notes and queue properties never publish, even on a shared note.
- The queue and the Boox are for reading only. Albums, games, films and series do not use the queue or
  the tablet.
- The per-medium walkthrough in §5 was approved ("that sounds good, keep going").

## 3. Goals, non-goals, anti-goals

**Goals**
1. One note per library item. The library row and the garden page are both derived from it at publish
   time. Nothing is typed twice.
2. Reading lifecycle wiring: adding to the queue, starting, finishing (by queue DONE or
   `boox-retire-document`) and dropping each update the note's status and dates. This works the same for
   Boox and non-Boox reading.
3. A non-reading lifecycle (listening, playing, watching): an add command plus a status command, with no
   queue.
4. `a3-library-share` / `a3-library-unshare` commands. On the next `a3-publish-living`, both surfaces
   appear or disappear.
5. Only a designated site section of the note becomes the garden page body.
6. The four `library-*.org` shelf files stop being a source of rows.

**Non-goals**
- Papers in the library, and any change to the paper reading flow (user decision; see §8, C1).
- Changing the site's library templates or shelf curation model (`data/library-shelves.yaml` stays
  hand-edited).
- Computing reading progress from the Boox. Progress stays an optional hand-set property.
- The legacy Supernote code (`a3madkour/supernote-*` in `config.org` ~L1989–2075). It is left untouched,
  and its removal is a separate decision.
- Cover fetching changes. The existing `cover_file` path is reused as is.

**Anti-goals** (these would make it a failure even if it works)
- Any private text reaching the site: highlights, noter headings, margin notes, or a body from a note that
  is not shared.
- Sharing that publishes a garden page with an empty body.
- Having to edit generated output (`data/<medium>.yaml`, `content/garden/<slug>/index.md`) by hand. Per
  the dogfood rule, every defect is fixed in the function that produced the output.
- A second place where status lives. The queue entry's TODO state may *trigger* a note update, but the
  note is authoritative.

## 4. Current state (what exists, with locations)

**Site**
- Shelf pages `/library/{reading,listening,playing,watching}/` plus the `/library/` umbrella. They read
  `data/<medium>.yaml` (generated; "Manual edits will be overwritten"). Hand-edited:
  `data/library-shelves.yaml` (curated shelves and the hero slug) and `data/library-media.yaml`.
- A library row already has `note_slug` (a ref to a garden note; the templates render a "Related note" /
  "Note" link) and `cite_key` (must resolve in `data/citations.yaml`, per `tools/check_library_links.py`).
  No row sets either today.
- Garden *media* notes (`media_type` ∈ album/book/film/game/series/track) require `status` and `creator`.
  Their status enum is `abandoned/finished/queued/reading` for every media type. The existing ones
  (`content/garden/invisible-cities/`, `outer-wilds/`, …) are hand fixtures, not pipeline output.
- Library status vocabularies (from `data/sections.json`):
  - reading `abandoned/finished/queued/reading`
  - listening `dropped/finished/listening/queued`
  - playing `100pct/dropped/finished/playing/queued`
  - watching `dropped/finished/queued/watching`
- `check_library_fixtures.py` requires a `finished` date when `status: finished`.

**Dotfiles publisher**
- `a3madkour-pub-library/publish-library-file` (`lisp/a3madkour-publish-library.el` L405) treats one org
  file as one whole shelf. Every level-1 heading becomes a row, and the file rewrites the *entire*
  `data/<medium>.yaml` (`--yaml-path` ignores the source file). Rows from several notes cannot be
  combined.
- `a3madkour-pub-garden/publish-garden-file` (`lisp/a3madkour-publish-garden.el` L48) exports the whole
  file. It goes through a rewritten temp copy (`a3madkour-pub-rewrite/rewrite-to-tmp-file`), which is the
  natural place to narrow the body.
- Garden frontmatter (`a3madkour-pub-frontmatter--normalize-garden`) does not read media fields from org.
  It passes `creator` through only if ox-hugo already emitted it, so the pipeline cannot produce a garden
  media note today.
- `a3-publish-mark` / `a3-publish-unmark` (`lisp/a3madkour-publish-author.el`) set or flip
  `#+HUGO_PUBLISH:` and `#+HUGO_SECTION:`, and prompt for missing contract fields. Living publish refuses
  a note missing a required field (`--contract-gap`, commit `12fa18c`).
- `a3-library-insert-item` (author.el L460) inserts a heading into a shelf file.

**Dotfiles reading flow** (`custom/config.org`)
- `a3madkour/citar-add-to-reading-queue` (L1958) appends
  `* TODO Read <title> (<year>) :active:toread:` with `:CITEKEY:`/`:AUTHOR:` to `~/org/queue.org`. Entries
  are created **already active**. It refuses past the WIP limit (`a3madkour/reading-queue-wip-limit` = 5).
- `a3madkour/toggle-active` (L3521) flips `:active:`/`:inactive:`. `a3madkour/deactivate-on-done`
  (L3548) runs on `org-after-todo-state-change-hook`. TODO keywords: `TODO NEXT WAIT | DONE DROP`.
- Boox (L2078 onward): `boox--queue-entries` (`:CITEKEY:` → `paper`; `:READING_FILE:` → `book`, which
  gets a `:BOOX_KEY:`). Also `boox-push-queue`, `boox-import` (writes `* Tablet Highlights` into the
  note), `boox--note-for-key` / `boox--ensure-book-note` (create the note), and `boox-retire-document`
  (import, delete from the tablet, then `boox--close-queue-entry`, which does `org-todo "DONE"`, so it
  runs the after-todo hook).
- Ref note shape (e.g. `ref-notes/pierceTypesProgrammingLanguages2002.org`): a file-level drawer
  (`:ID: :ROAM_REFS: :NOTER_DOCUMENT: :LAST_MODIFIED:`, and on Pierce a hand-added `:PROGRESS:`), then
  `#+title:`, `#+filetags: :Ref:Book:…:`, then one level-1 heading (the book title) with the book's
  sections as level-2 headings carrying `:NOTER_PAGE:`. 22 ref notes exist, none published; 2 are
  tagged `:Book:`. The Boox functions are all `a3madkour/boox-…`; short names below drop the prefix.
- `~/org/queue.org` is empty. The `library-*.org` files hold 2 dummy items each.

## 5. The design

### 5.1 The item note

Any org-roam note can be a library item:
- for a book in Zotero, the citar ref note;
- for a book not in Zotero, a plain book note (the shape `boox--ensure-book-note` already makes);
- for anything else, a new org-roam node.

A note is a library item when its **file-level property drawer** carries `:LIBRARY_MEDIUM:`. The library
properties live there, prefixed, so they never collide with noter/Boox keys or a hand-set `:PROGRESS:`:

| Property | Meaning |
|---|---|
| `:LIBRARY_MEDIUM:` | `book`, `album`, `track`, `game`, `film` or `series`. Determines the shelf (book→reading, album/track→listening, game→playing, film/series→watching). |
| `:LIBRARY_STATUS:` | That shelf's own status word (see §4). |
| `:LIBRARY_STARTED:` / `:LIBRARY_FINISHED:` | `YYYY-MM-DD`. Stamped by commands. |
| `:LIBRARY_CREATOR:` / `:LIBRARY_YEAR:` | Filled from the bib entry for Zotero books, asked for otherwise. |
| `:LIBRARY_PREVIEW:` | Optional one-line row preview (see §5.4). |
| `:LIBRARY_COVER:` | Optional `cover_file` name under `static/library/covers/`. |
| per-medium extras | e.g. `:LIBRARY_PROGRESS_PCT:`, `:LIBRARY_PROGRESS_LABEL:`, `:LIBRARY_HOURS_PLAYED:`, `:LIBRARY_PLATFORM:`, `:LIBRARY_CURRENT_EPISODE:`. The set is whatever the shelf's `extras` contract in `data/sections.json` defines, with the property name derived from the key. |

**The site section.** The note's public body is exactly one level-1 heading tagged `:site:`, a sibling of
the ref note's existing title heading. Its contents (not the heading line itself) become the garden page
body, and nothing else in the file is exported. That includes link rewriting and **asset copying**:
`publish-garden-file` currently runs `a3madkour-pub/asset-validate-and-copy` and the link rewriter over
the whole original file, so an image linked from a private heading would be copied into the public
bundle. Both must operate on the `:site:` subtree only. The `:site:` tag never shows as a site tag.

**Tags.** One cleaned tag list feeds both the garden page and the library row (my call, C7):
- the editorial filter runs as now;
- structural tags `Ref` and `Book` (plus any others in a defcustom list) are dropped;
- the rest are converted to lowercase kebab-case (`ProgrammingLanguages` → `programming-languages`), which
  satisfies `check_library_fixtures`'s `^[a-z0-9][a-z0-9-]*$`.

This applies to item notes only; concept garden notes' tags are unchanged.

### 5.2 Lifecycles

Common to all media:
- **`a3-library-status`**, run in an item note, offers that medium's status words. Moving to the in-progress
  word (`reading`/`listening`/`playing`/`watching`) stamps `STARTED` if empty. Moving to `finished` or
  `100pct` stamps `FINISHED`. Moving to `queued` stamps nothing.
- **`a3-library-add`** (replaces `a3-library-insert-item`) creates a new org-roam node. It asks for
  medium, title, creator, year and status, then stamps dates as above. For a film the status prompt
  defaults to `finished`.

**Reading, Zotero book**
1. `citar-add-to-reading-queue`, on a bib entry whose type is a book, also ensures the ref note exists
   (`citar-create-note`, as `boox--note-for-key` does). It sets `LIBRARY_MEDIUM: book`, creator and year
   from the bib entry, and `LIBRARY_STATUS: reading` with `STARTED` today, because queue entries are born
   active (§8, call C2). Papers are queued exactly as today, with no library properties.
2. `toggle-active` on a `:toread:` entry: going inactive sets the note to `queued`; going active sets it to
   `reading`, stamping `STARTED` only if empty.
3. Boox push, import and refresh are unchanged.
4. Finishing goes through the after-todo-state hook on a `:toread:` entry. **DONE** → `finished` + date.
   **DROP** → `abandoned`. `boox-retire-document` already marks the entry DONE, so it needs no change of
   its own. Marking DONE by hand covers non-Boox reading.
5. `a3-library-status` on a book note with an open queue entry, set to `finished`/`abandoned`, also
   closes that entry (DONE/DROP), so the WIP slot frees up. It goes through the same function as step 4,
   which guards against the hook re-entering.

**Reading, book not in Zotero.** A new `a3-reading-queue-add-book` creates the queue entry and the book
note together. It asks for title, creator and year, and optionally a file:
- with a file, it writes `:READING_FILE:`, so the Boox path works as today;
- without one, the entry is a paper/other-device read.

The command assigns the `:BOOX_KEY:` itself, up front (`boox--book-key` when there is a file, the same
slug scheme from the title when there isn't), and creates the note as `org-ref-notes/<key>.org` through
`boox--ensure-book-note`. `boox--note-for-key` finds notes only by that file name, so this is what keeps
push, import and refresh unchanged; any other name would make the first import create a second note
(my call, C8). Steps 2–5 above apply, with the note found by `:BOOX_KEY:` instead of `:CITEKEY:`.

**Listening, playing, watching.** `a3-library-add`, then `a3-library-status` as needed. There is no
queue, no WIP limit and no tablet.

### 5.3 Share / unshare

- **`a3-library-share`**, run in an item note:
  1. Refuses unless the note has a non-empty `:site:` section; it offers to insert an empty `* … :site:`
     heading and stop.
  2. Runs the existing mark path with section `garden`, so it sets `#+HUGO_PUBLISH: t` +
     `#+HUGO_SECTION: garden` and prompts for missing garden-contract fields.
  3. Prompts for any required library-row field still missing (creator, year, status).
- **`a3-library-unshare`** is `a3-publish-unmark` on that note.
- Both take effect on the next `M-x a3-publish-living`, like every other living section. On unshare the
  garden bundle goes through the existing manifest orphan sweep, and the row disappears because the
  shelf is regenerated from shared notes only.
- **Living-publish contract gate:** a garden note with `:LIBRARY_MEDIUM:` but no non-empty `:site:`
  section is refused (logged as a contract error), the same way `--contract-gap` refuses a note with a
  missing required field. This is the backstop for the empty-body anti-goal if someone sets the header by
  hand.

### 5.4 Publishing

**Garden page.** For a note with `:LIBRARY_MEDIUM:`, `publish-garden-file`:
- narrows the exported content to the `:site:` subtree's contents, in the rewrite-to-temp stage, before
  ox-hugo sees it;
- emits the media frontmatter from the `LIBRARY_*` properties: `media_type`, `status`, `creator`, `year`,
  `started`, `finished`.

`roam_refs` already flows. Concept garden notes (no `:LIBRARY_MEDIUM:`) are unchanged.

**Library rows.** The library sections stop being "one file → one shelf". After the garden handler runs,
a collector builds each `data/<medium>.yaml` from **every currently shared item note** of that shelf, not
only the notes changed in this run. Each row:
- `slug` = `note_slug` = the garden slug;
- title, creator, year, `media_type`, status, started, finished;
- `last_modified`, using the same value the garden page got;
- tags, from the note's filetags through the editorial filter;
- `preview` = `:LIBRARY_PREVIEW:`, or else the first sentence of the `:site:` section;
- extras from the `LIBRARY_*` extras properties.

`cite_key` is emitted only when the note's `ROAM_REFS` key exists in `data/citations.yaml`. Otherwise
`check_library_links` would fail. Each yaml is written only if its bytes differ, as now.

**Contract.** `data/sections.json`:
- the garden `media` variant's `status` must accept each media type's shelf vocabulary. Split the `media`
  case per shelf (book / album+track / game / film+series), each with its shelf's status values. Knock-on
  effects: `check_garden_fixtures.derive_flavor` returns the case *name*, so it must map the four new
  cases back to the `media` flavor; and the hand fixture `content/garden/severance-s2/` (series,
  `status: abandoned`) changes to `dropped`;
- the garden media fields (`media_type`, `status`, `creator`, `year`, `started`, `finished`) become
  `from: pipeline`, with a new `source` kind that reads the `LIBRARY_*` drawer. Without this, mark and
  the contract gate pick the variant from `media_type` in `#+HUGO_CUSTOM_FRONT_MATTER`. An item note
  would then be checked as a concept note, or mark would write status into custom front matter, making a
  second place status lives (my call, C9);
- the library shelves' `extras` contracts are unchanged.

**Garden page header.** `layouts/partials/garden/note-header.html` (~L33–47) and `main.css` (~L1288) draw
a glyph and colour only for `queued/reading/finished/abandoned`. The new words reuse those by meaning:
- `listening`/`playing`/`watching` → the `reading` glyph;
- `dropped` → `abandoned`;
- `100pct` → `finished`, with the visible label "100%".

This keeps one meaning per glyph site-wide and adds no new colour token (my call, C10). The label text
always shows, so meaning is never carried by colour alone.

Library sections remain `store: data`.

### 5.5 Migration

User decision (2026-10-28): the lorem-ipsum library examples are removed, not migrated.
- Delete the 4 `~/org/notes/library-*.org` files. They are the user's org files, so the user deletes them
  or explicitly approves the delete when the plan reaches that step.
- The next living publish regenerates `data/{reading,listening,playing,watching}.yaml` from shared item
  notes only. Until something is shared, each holds an empty `items:` list. The collector writes that
  empty file through the fixed function; nobody hand-edits it.
- `data/library-shelves.yaml` (hand-edited) drops its `example-*` slug references and the
  `hero: example-book-one` pin. The shelves can stay tag-driven or be emptied; the hero falls back to the
  newest item when absent.
- **Empty library must work.** `/library/`, the four shelf pages, the homepage Currently widget, the
  library linters (`check_library_{fixtures,links,shelves,covers}`), smoke, Pagefind, LHCI URL generation
  and the E2E suite must all pass with zero rows, each showing a sensible empty state. Where a site
  linter's unit tests need rows, they keep their own temp-dir fixtures, as they do now.
- The hand-written garden media fixtures (`content/garden/invisible-cities/`, `outer-wilds/`, …) are site
  fixtures, not library rows, and stay as they are, apart from the `severance-s2` status change in §5.4.
- `a3-library-insert-item` and the per-file library handler are removed once nothing uses them.

## 6. Constraints

- **Dogfood rule:** fix the function that ran, never its output. Test first, mutation-test each guard,
  then re-run the real command (`a3-publish-living` over `~/org`).
- **Privacy boundary:** the site sees only shared notes, and only their `:site:` subtree plus the
  `LIBRARY_*` metadata.
- **Tests:**
  - ERT for every new function (`run-tests.sh`; selector args are ignored, so filter the log);
  - the `boox-core.el` / `tests/boox-tests.el` tangled split in `config.org` for the reading-flow pure
    helpers;
  - site linters `check_library_{fixtures,links,shelves,covers}`, `check_garden_{fixtures,links}`,
    `python3 tools/sections.py`, and their `test_` siblings;
  - `hugo --minify` with no dev server alive.
- **New elisp modules** need an explicit `-l` in `a3-pub.sh` (memory: plans update a3-pub.sh).
- Both repos stay unpushed until the end of S1 and are pushed together.
- **No AI-authored prose on the site.** Dummy items use lorem ipsum only.
- **The user's real org files** (ref notes, `queue.org`) are not modified by the build or the tests. Real
  items get shared only when the user runs the commands.

## 7. Left to the builder

- Module boundaries. Likely a new `a3madkour-publish-library-notes.el` (collector + share/unshare) plus
  the reading-flow hooks in `config.org`'s Boox/citar sections, next to their helpers.
- How the collector enumerates shared item notes: reuse living publish's file discovery and filter on
  `:LIBRARY_MEDIUM:` + `HUGO_PUBLISH: t`.
- How the bib entry type is read through citar (`=type=`), and which types count as a book (`book`,
  presumably `inbook`/`mvbook`; not `incollection`).
- The first-sentence extraction for `preview`.
- Whether `a3-library-status` also updates `:LAST_MODIFIED:`.

## 8. Calls I made (to check while reading)

- **C1 (now the user's decision, 2026-10-28). Papers stay out of the library.** In the user's words:
  "papers should not go through the library, papers will just be notes in the garden from the website
  side, from the workflow emacs side it should remain as it is now." On the site, a paper is a garden note
  (reference flavor, via normal mark). In Emacs, the queue/Boox flow for papers is unchanged: no
  `LIBRARY_*` properties, and no status writes from the hooks.
- **C2. Queue add = start reading.** Entries are born `:active:`, so a queued book becomes `reading` at
  once. `queued` is reached by toggling inactive, or by `a3-library-add` for a book you want but aren't
  reading.
- **C3. One `:site:`-tagged heading** is the public body. The tag name is my choice.
- **C4 (now the user's decision). The lorem-ipsum library examples are removed;** the library is
  empty until real items are shared.
- **C5. Preview falls back to the first sentence of the site section,** so it isn't written twice.
- **C6. DROP on a queue entry = abandoned.**
- **C7. Item-note tags are cleaned once,** with `Ref`/`Book` dropped and the rest kebab-cased. The same
  list goes to the garden page and the row.
- **C8. Non-Zotero book notes are named `<BOOX_KEY>.org`,** with the key assigned at queue time, so the
  Boox code stays untouched.
- **C9. Garden media fields come from the `LIBRARY_*` drawer** via the registry's `from: pipeline` +
  `source`.
- **C10. New status words reuse the four existing garden glyphs by meaning;** `100pct` shows as "100%".
