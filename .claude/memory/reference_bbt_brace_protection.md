---
name: reference-bbt-brace-protection
description: "BBT (Better-BibTeX) titles wrap every capitalized word in {{ }} for case protection — a BibTeX convention to defeat downstream tools that aggressively title-case. F strips ALL `{`/`}` chars from titles in normalize-entry. Edge case: math literals like `{0,1}-vector` lose braces; author escapes per-entry."
metadata:
  node_type: reference
  type: reference
---

BBT-exported `.bib` entries look like:

```bibtex
@online{meiRWoMRetrievalaugmentedWorld2026,
  title = {R-{{WoM}}: {{Retrieval-augmented World Model For Computer-use Agents}}},
  ...
}
```

The double-braces `{{...}}` around capitalized words are BibTeX's **case-protection** convention. Some downstream tools auto-title-case (e.g., turn `R-WoM` into `R-Wom`); wrapping the word in braces tells BibTeX "don't touch the case of these letters." BBT applies this aggressively — basically every capital sequence.

## Why this matters for F

`data/citations.yaml` is consumed by Hugo's `essay-references` partial and the cite-modal runtime. Both render `title` verbatim into HTML. With braces preserved, users see literal `R-{{WoM}}` text on the rendered page. Ugly.

The F spec §5 originally said "inner braces survive verbatim as part of the yaml string." That was a design choice based on the BibTeX-correctness theory. In practice it produces ugly output. The Task 18 spot-check forced a reversal.

## Current behavior (post-2026-06-01)

`a3madkour-pub-bib--normalize-entry` strips ALL `{` and `}` characters from the title field via:

```elisp
(title (and title-raw
            (replace-regexp-in-string "[{}]" "" title-raw)))
```

This is a deliberate spec deviation. Documented in the docstring + the Task 18 fix commit (`116950b` in dotfiles).

## Edge case

Math literals like `{0,1}-vector` or `\mathbb{R}` lose their braces. Currently the workaround is for the author to backslash-escape in the source `.bib` entry. Rare in real-world bib usage; flag for a future F.x slice if it surfaces.

## Where the strip happens

Only the `title` field — author names, venues, etc. are not touched. The strip happens in normalize-entry (the lossy projection from raw → schema plist), AFTER the parser's `read-balanced-braces` has already removed the outer field-value delimiters. So a triple-braced source title `{{{X}}}` flows: parser strips one pair → `{{X}}` → normalize strips both inner → `X`.
