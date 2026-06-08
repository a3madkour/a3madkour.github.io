---
date: 2026-06-08
draft: false
has_citations: false
has_footnotes: false
has_math: false
has_sidenotes: false
has_video_sync: false
has_widgets: false
lastmod: 2026-06-08
series: ""
series_order: 0
summary: "Lorem ipsum — D.1 cross-ref fixture exercising ref-block shortcode with backward, forward, and broken references."
tags: ["example", "fixture"]
title: "Example Blocks Crossref"
toc: true
---
Lorem ipsum dolor sit amet, consectetur adipiscing elit. This fixture exercises the {{</* ref-block */>}} shortcode against AMS-style D.1 blocks — see roadmap row 2.2.

## Backward references — block before reference {#backward}

The typical pattern: declare the theorem, then refer back to it.

{{< theorem id="thm-monotone" title="Monotone convergence" >}}
Every bounded monotone sequence converges.
{{< /theorem >}}

By {{< ref-block "thm-monotone" >}} every bounded monotone sequence converges. Lorem ipsum body referring to {{< ref-block "thm-monotone" >}} again.

{{< definition id="def-cauchy" >}}
A sequence is Cauchy iff for every ε > 0 there exists N such that for all m, n > N, |x_m - x_n| < ε.
{{< /definition >}}

{{< ref-block "def-cauchy" >}} is independent of the convergence notion used.

{{< lemma id="lem-cauchy-bounded" >}}
Every Cauchy sequence is bounded.
{{< /lemma >}}

This follows from {{< ref-block "lem-cauchy-bounded" >}}; together with {{< ref-block "thm-monotone" >}} it gives completeness.

## Forward references — reference before block {#forward}

The harder case: reference points to a block defined later in the document. The server-side scratch lookup has no entry yet, so the link renders with the bare id as text — a visible "unresolved" state. Hugo cannot do a second pass over the page after all shortcodes have populated scratch.

We will prove {{< ref-block "lem-future" >}} below. Note the rendered text shows the id (`lem-future`) instead of the formatted label, because the lemma's `Scratch.Set` hasn't fired yet at the time this ref-block runs.

Lorem ipsum.

{{< lemma id="lem-future" title="Forward-declared" >}}
This block is referenced from earlier in the document.
{{< /lemma >}}

After the block has been rendered, subsequent refs work normally: {{< ref-block "lem-future" >}}.

## Broken references — id not on this page {#broken}

If the ref id never resolves on the page, the rendered text stays as the bare id. The author should treat this as a visible error to fix at publish time.

See {{< ref-block "thm-does-not-exist" >}} (intentionally broken to demonstrate the unresolved state).

## All numbered block kinds — coverage {#coverage}

{{< corollary id="cor-completeness" >}}
The reals are complete.
{{< /corollary >}}

By {{< ref-block "cor-completeness" >}}.

{{< proposition id="prop-mvt" >}}
Mean value proposition placeholder.
{{< /proposition >}}

By {{< ref-block "prop-mvt" >}}.

{{< remark id="rmk-historical" >}}
Historical context for the result.
{{< /remark >}}

See {{< ref-block "rmk-historical" >}}.

{{< example id="ex-harmonic" >}}
The harmonic series diverges.
{{< /example >}}

See {{< ref-block "ex-harmonic" >}}.

{{< note id="note-style" >}}
Stylistic note on AMS conventions.
{{< /note >}}

See {{< ref-block "note-style" >}}.

{{< claim id="cl-uniqueness" >}}
Uniqueness placeholder.
{{< /claim >}}

By {{< ref-block "cl-uniqueness" >}}.

{{< conjecture id="conj-open" >}}
Open conjecture placeholder.
{{< /conjecture >}}

See {{< ref-block "conj-open" >}}.

{{< axiom id="ax-choice" >}}
Axiom of choice.
{{< /axiom >}}

By {{< ref-block "ax-choice" >}}.

## Late backward reference {#late-backward}

Verifying that scratch persists across the full page — we recall {{< ref-block "thm-monotone" >}} from the top of the document, alongside {{< ref-block "def-cauchy" >}} and {{< ref-block "lem-future" >}}. All three should resolve to their formatted labels even though the blocks they point to are far above this paragraph.
