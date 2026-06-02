---
date: 2026-06-01
draft: false
has_citations: false
has_footnotes: false
has_math: true
has_sidenotes: false
has_video_sync: false
has_widgets: false
lastmod: 2026-06-01
series: ""
series_order: 0
summary: "Lorem ipsum — AMS-style block kitchen sink for D.1."
tags: []
title: "Example Five"
toc: true
---

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Demonstration essay for the AMS-style semantic blocks (D.1).

## Section one — definitions and theorems

{{< definition title="Continuity" >}}A function `f` is continuous at \(x_0\) if for every `ε > 0` there exists `δ > 0` such that `|x - x_0| < δ` implies `|f(x) - f(x_0)| < ε`.{{< /definition >}}

{{< theorem title="Intermediate Value" id="thm-ivt" >}}If `f` is continuous on the closed interval `[a, b]` and `c` is any value between `f(a)` and `f(b)`, then there exists `x ∈ [a, b]` with `f(x) = c`.{{< /theorem >}}

{{< proof of="Intermediate Value" >}}Suppose without loss of generality that `f(a) < c < f(b)`. Lorem ipsum proof sketch \(\alpha + \beta = \gamma\).{{< /proof >}}

{{< lemma >}}Lemma without a title — shares the theorem-family counter with theorem above.{{< /lemma >}}

{{< corollary >}}Corollary without a title — also shares the theorem-family counter.{{< /corollary >}}

{{< proposition title="Trivial proposition" >}}A proposition with a title — counter continues from the theorem family.{{< /proposition >}}

## Section two — supporting prose

{{< remark >}}Remark without a title — separate counter.{{< /remark >}}

{{< example title="Counterexample" >}}Example with a title — independent counter.{{< /example >}}

{{< note >}}Note without a title — independent counter.{{< /note >}}

{{< claim >}}Claim without a title — independent counter.{{< /claim >}}

{{< conjecture title="Riemann-style" >}}Conjecture with a title — independent counter.{{< /conjecture >}}

{{< axiom >}}Axiom without a title — independent counter.{{< /axiom >}}

## Section three — cross-reference

By the [Intermediate Value Theorem](#thm-ivt), the equation `f(x) = c` has a solution in `[a, b]`. The visible link text "Intermediate Value Theorem" is author-typed (V1 does not auto-format cross-references; see D.x follow-ups).
