# Poems as written: design

**Status:** awaiting the author's review. Filed 2026-11-01 from the S1 poem dogfood (friction rows 42-44).
**Evidence:** the trace page at https://claude.ai/artifact/BQMy1L78k5YzDgeKYnLqo4.
**Repos:** dotfiles (publisher) and site (template, CSS, linter, tests).

## Why

A poem's line breaks, spacing and opening characters are the poem. Today it travels through tools built for prose:

- Org deletes a `# ` line, turns a `- ` line into a list, and turns a `* ` line into a heading.
- Org or Goldmark removes indentation.
- Plain and timed poems use separate renderers, so they drift.

A 13-line sample run through the real commands showed 6 lines as written on a plain poem and 8 on a timed one. The `<br>` template patch (site `819a1b1`, `f2943f5`) also splits HTML tags when a poem contains a `- ` or `* ` line, which prints raw markup on the page.

The author asked for this to be consistent, and said essays, notes and blogs are not a concern.

## Goals

1. Every poem line reaches the page as typed: its characters, leading spaces and inner runs of spaces.
2. One renderer handles every poem. Timing marks add behaviour to it and do not select a different path.
3. Plain and timed poems look the same at rest.
4. Line breaks and stanzas work without relying on a fresh stylesheet.

## Non-goals

- Any change to essays, garden, research, library, games, music or recipes.
- Links, footnotes, images or math inside a poem.
- A visual redesign of the poem page.
- New timing features.

## Anti-goals

- A poem line silently changed or dropped.
- A second code path that can drift from the first.
- Author prose in any fixture. Fixtures stay lorem ipsum.

## Design

### Publisher (`a3madkour-publish-poetry.el`)

The ox-hugo export still runs, but only for frontmatter. Its body is discarded.

A new function, `a3madkour-pub-poetry--raw-body (file)`, reads the poem from the org file:

- It skips the file-level property drawer and every line matching `^#\+`, wherever it appears. Those lines are settings, not verse.
- It removes blank lines at the start and end.
- It keeps everything else byte for byte, including `# `, `- `, `* `, indentation and `\[mm:ss]`.
- It trims trailing whitespace at line ends, which a reader can never see.

That text becomes the body of `index.md`, with lines separated by `\n`. `lines:` counts its non-blank lines, and the marker warnings and summary scrub read the same text.

`a3madkour-pub-poetry--collapse-escaped-markers` goes away, since nothing doubles the backslash any more. So does the leading-`##` exclusion in `count-poem-lines`, since nothing produces that heading.

**Refused at publish.** A poem containing `{{<` or `{{%` fails with the line number. Hugo would otherwise read it as a shortcode and break the build. The section gate reports it like any other contract gap.

### Privacy consequence

A `# ` line used to be a comment. Under this design it is verse and it publishes, because the goal is that no line disappears. The same is true of drawers, `:noexport:` subtrees and comment blocks inside a poem. The trace page listed `#` lines among those that would survive, and the author approved writing this design from it. Notes that should stay private belong outside the poem file, or on a `#+` line, which never publishes.

### Renderer (site)

`layouts/partials/works/synced-text-parser.html` becomes `layouts/partials/works/poem-body.html`, and `single.html` always calls it. The `findRE` branch, the `<br>` patch and the `.Content` call all go.

For each line of `.RawContent`:

- Text is HTML-escaped first, which also fixes the literal `&gt;` on timed poems.
- `*word*` becomes `<strong>` and `/word/` becomes `<em>`, using Org's rule: the marker hugs the text and has whitespace, punctuation or a line edge outside it. Nothing else is interpreted.
- Leading spaces and inner runs of spaces are kept.
- Blank lines end a stanza. Lines inside a stanza are joined by `<br>`, as now.

`RenderString` goes away: no line is treated as Markdown.

A poem with no unescaped marker gets the same stanza and line markup with no `data-t`, no `poem-word` spans and no `.poem-synced` wrapper, so the player script stays off. A poem with markers renders as it does today, plus the kept spaces.

**Spacing in CSS.** `.poem-line { white-space: pre-wrap }`, and plain lines also carry `poem-line`. A long line wraps at the column on a phone, with no sideways scrolling. Timed word spans keep the spaces between them.

### Linters and fixtures

- `tools/check_poetry_synced.py`: rules are unchanged, and a new rule rejects `{{<` and `{{%` in a poem body, so a hand-written fixture cannot break the build.
- `check_meta_description`: Hugo still renders the raw body for `.Summary` when `summary` is empty. A poem without a summary must still produce a clean description.
- `example-poem-synced` uses `*irure*`, which moves from italic to bold. That is the Org meaning.

## Tests

Add a fixture, `content/works/poetry/example-poem-marks/`, carrying the trace page's 13-line sample in lorem ipsum, plus a timed twin.

- **ERT:** `raw-body` keeps each sample line, drops `#+` lines and the drawer, and handles a file with no body. The handler writes the raw text to `index.md`, and `{{<` is refused.
- **Playwright:** every sample line appears once and in order on both poems, each on its own row. Indentation shows as a real horizontal offset. No `<ul>`, `<h2>` or stray `aria-label` text appears inside the poem body. The existing plain-versus-timed style test stays.
- **Linter pair:** the `{{<` rule.
- **End to end:** rerun the trace sample through the real commands in a scratch copy. The target is 13 of 13 lines shown as written, in both poem modes.
- Mutation-test each guard, per the standing rule.

## Rollout

1. The dotfiles and site changes land together, because the new publisher output needs the new renderer.
2. The author runs `a3-publish-deliberate` on `defend.org` and `smoke-test-poem.org`. Generated bundles are never hand-edited.
3. Both repos are pushed with the rest of S1.

The `<br>` bug stays in unpushed commits until step 1. No real poem contains a triggering line.

## Left to the builder

- The exact emphasis regex, as long as tests pin hugging and word edges.
- Whether `poem-body.html` keeps one file or splits out a line helper.
- Docs: `CLAUDE.md` and the two poetry specs must describe the new path.

## Calls made without the author

- `*bold*` and `/italic/` are the only marks. Underline, code and links show as typed.
- `#+` lines never publish, even mid-poem.
- `{{<` is refused, not escaped: an escape would alter the stored line and is the rarest case.
