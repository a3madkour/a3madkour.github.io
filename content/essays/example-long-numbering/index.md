---
block_numbering: "section-prefixed"
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
summary: "Lorem ipsum — long-essay fixture for Tier 2.3 section-prefixed numbering. Five H2 sections, 14 numbered AMS blocks, JS post-processed to Kind M.N form."
tags: ["example", "fixture"]
title: "Example Long Numbering"
toc: true
---
Lorem ipsum dolor sit amet, consectetur adipiscing elit. This fixture stress-tests the navigability of bare integer counters at length — see roadmap row 2.3. Five H2 sections, 14 numbered AMS blocks total. The author would expect "Theorem 3.2" (section 3, second theorem) rather than "Theorem 7", which carries no positional cue.

## 1. Foundations {#sec-foundations}

Lorem ipsum lead.

{{< definition id="def-set" title="Set" >}}
A set is a collection of distinct objects.
{{< /definition >}}

{{< theorem id="thm-cantor" title="Cantor" >}}
There is no surjection from a set to its power set.
{{< /theorem >}}

By {{< ref-block "thm-cantor" >}}.

{{< theorem id="thm-zfc" >}}
Lorem ipsum statement of the foundational axiom system.
{{< /theorem >}}

## 2. Convergence theorems {#sec-convergence}

Lorem ipsum.

{{< theorem id="thm-bolzano" title="Bolzano–Weierstrass" >}}
Every bounded sequence has a convergent subsequence.
{{< /theorem >}}

{{< lemma id="lem-cauchy" >}}
Every Cauchy sequence in ℝ converges.
{{< /lemma >}}

{{< theorem id="thm-completeness" >}}
ℝ is complete.
{{< /theorem >}}

Following from {{< ref-block "thm-bolzano" >}} and {{< ref-block "lem-cauchy" >}}.

## 3. Continuity {#sec-continuity}

Lorem ipsum.

{{< theorem id="thm-ivt" title="Intermediate value" >}}
A continuous function on a connected interval attains every value between its endpoints.
{{< /theorem >}}

### 3.1 Topological version {#sec-continuity-topology}

{{< example id="ex-step" >}}
Step functions are not continuous; the theorem does not apply.
{{< /example >}}

## 4. Differentiation {#sec-differentiation}

Lorem ipsum.

{{< lemma id="lem-rolle" title="Rolle" >}}
If f is continuous on [a,b], differentiable on (a,b), and f(a)=f(b), then f'(c)=0 for some c.
{{< /lemma >}}

{{< lemma id="lem-mvt" title="Mean value" >}}
A differentiable function attains its mean rate of change at some interior point.
{{< /lemma >}}

{{< proposition id="prop-monotonicity" >}}
A differentiable function with positive derivative is increasing.
{{< /proposition >}}

By {{< ref-block "lem-rolle" >}} and {{< ref-block "lem-mvt" >}}.

## 5. Integration {#sec-integration}

Lorem ipsum.

{{< theorem id="thm-ftc-1" title="Fundamental theorem of calculus, part I" >}}
If f is continuous, then F(x) = ∫_a^x f(t)dt is differentiable with F'(x) = f(x).
{{< /theorem >}}

{{< theorem id="thm-ftc-2" title="Fundamental theorem of calculus, part II" >}}
If f is continuous and F is any antiderivative of f, then ∫_a^b f(x)dx = F(b) − F(a).
{{< /theorem >}}

{{< corollary id="cor-substitution" >}}
The substitution rule follows immediately.
{{< /corollary >}}

By {{< ref-block "thm-ftc-1" >}}, {{< ref-block "thm-ftc-2" >}}, and {{< ref-block "cor-substitution" >}}.

## 6. Implementation notes {#sec-impl}

This essay has `block_numbering: "section-prefixed"` in its frontmatter — the only essay on the site that opts in (as of 2026-06-08). The `<main>` element carries `data-block-numbering="section-prefixed"`; `assets/js/block-renumber.js` reads that attribute, walks H2s + `.block-*` containers, and rewrites every `.block-header` and matching `.ref-block` text from `Kind N` to `Kind M.N`.

Each H2 resets the per-section counter. The theorem-family (theorem / lemma / corollary / proposition) shares one counter per section so cross-refs remain unambiguous. Definitions / remarks / examples / notes / claims / conjectures / axioms each keep their own per-section counter.

No JS → bare integers (the server-side render). Roadmap row 2.3.
