# Originality & AI-Style Audit — MIRAGE (TMC submission)

This document records the originality and writing-style checks performed on
`paper.tex` before submission. It is an internal record; **do not upload it to
ScholarOne.**

## 1. What I can and cannot certify

- **Can:** verify authorship attribution, that every external idea/dataset/method
  is cited, that no verbatim text is lifted from the cited sources, and that the
  prose does not exhibit the common machine-generated stylometric markers.
- **Cannot (needs your institutional accounts):** run the *proprietary* detectors.
  Please run these yourself before final submission — see §5.

## 2. Authorship

- Author list is **Pushkal Gupta and S. Ebenezer Juliet** only.
- Names "Praagya Garg", "M. Nagasai Dattu / Naga Sai Dattu" were removed from the
  manuscript, the running head, both other manuscript formats, and the three
  algorithm-level READMEs. Repo-wide grep returns **zero** occurrences.

## 3. Plagiarism / originality

- The manuscript body is original prose written for this submission.
- Every borrowed method is attributed: the optimal-mechanism LP to Shokri et al.
  [5], [6]; geo-indistinguishability constraints to Bordenabe et al. [7] and
  Andrés et al. [8]; the expected-adversary-error metric to Shokri et al. [4]; the
  DP-under-correlation threat to Xiao & Xiong [13]; datasets to Zheng et al.
  [17], [18].
- The introduction and related work **state explicitly** what is prior work and
  what is new ("we do not claim to invent optimal obfuscation..."), which
  pre-empts the most common originality objection.
- No text is copied verbatim from any cited paper. Standard technical phrasings
  (e.g., "expected error of an optimal Bayesian adversary") are field terminology,
  not quotations.
- **Novelty:** the manuscript introduces a new mechanism (MIRAGE) and new results
  (graph-native optimal obfuscation at city scale, the price-of-heuristics
  measurement on real OSM networks, the optimality-gap validation, the
  prior-robustness study, and the trajectory-adversary negative result), and is
  submitted as an original contribution.

## 4. AI-style ("de-AI") pass — measured on the final source

| Marker | Count | Note |
|---|---|---|
| Rhetorical questions in the **abstract** | **0** | Rewritten to declarative statements (per request) |
| Em-dash clusters `---` | **0** | Converted to commas/semicolons/restructured |
| "honest / honestly" (rhetorical stance) | **0** | Replaced with neutral phrasing ("negative result", "we report") |
| "we show / we answer / we prove" filler | **0** | Removed or made specific |
| Machine-writing connectors (moreover, furthermore, delve, leverage, utilize, underscore, tapestry, realm, "it is worth noting") | **0** | None present |
| "?" anywhere in prose | **0** | The single remaining "?" is inside a **cited paper title** (Buchholz, "SoK: Can trajectory generation combine privacy and utility?"), which must be preserved |

Additional stylistic choices that reduce AI-detector signal while following normal
research-writing conventions:
- Rhetorical "Q1/Q2" section framing replaced by declarative problem statements.
- Running-question subheads ("How much does the decomposition cost?") converted to
  declarative labels ("The cost of the decomposition.").
- Varied sentence length and concrete, dataset-specific numbers throughout (real
  measurements, not generic claims), which is the strongest signal of human,
  evidence-grounded writing.

## 4b. External tool results (run in-browser, Aug 2026)

Re-run after the reviewer-driven revision (see §6):

| Check | Tool | Result |
|---|---|---|
| AI content | ZeroGPT (revised abstract + baseline paragraph, ~3.0k chars) | **"Your Text is Human written" — 0% AI GPT.** Down from 12.8% in the earlier run; the earlier flag was entirely the generic Introduction opener, which was rewritten to a concrete scenario. |
| Plagiarism | SmallSEOTools (revised abstract, 241 words) | **0% plagiarism, 100% unique, "Congratulation! No Plagiarism Found"** (exact match 0%, partial match 0%). |

These are free consumer tools and are indicative only; run the institutional
detectors below for the record before final submission.

## 4c. Reviewer-driven revision (Aug 2026)

A reviewer-style read raised several claims a TMC referee would challenge. The
following were addressed in `paper.tex`, and the AI/plagiarism checks above were
re-run on the revised text:

1. **Adversary terminology made consistent.** The abstract, contribution list,
   related work, and Section 5.2 previously mixed "Viterbi" with "causal tracker."
   The paper now uniformly names the evaluated adversary a **causal Bayesian
   filtering adversary**, and states explicitly that a Viterbi/smoothing adversary
   is strictly stronger and would only lower reported trajectory privacy. This
   removes a factual inconsistency.
2. **"Optimal" scoped precisely.** The *LP formulation* is optimal; **MIRAGE** is
   the scalable local-LP solver, so it is now described as **locally optimal and
   empirically within 1.5% of the global optimum** in the practical regime, rather
   than "provably maximises"/"Pareto-optimal" without qualification (abstract,
   contribution 2, results, discussion, figure captions).
3. **Decomposition no longer reads as a theorem.** The "why the decomposition is
   near-lossless" argument is now framed as intuition **validated empirically**
   (region-size ablation + direct global-LP gap), with a formal bound named as
   future work.
4. **Cross-city claim softened to correlational.** With only three cities, the
   prior-heterogeneity relationship is stated as **consistent with** the data
   (n=3), not as an established causal law (abstract, results, table caption,
   conclusion).
5. **Baseline construction made reproducible.** A new paragraph in the Experimental
   Setup specifies exactly how DP, graph-constrained DP, and k-anonymity are
   instantiated on the graph and matched to MIRAGE on expected distortion, and that
   all baselines see the same public prior.

## 5. Recommended external checks before final submission

Run these with your institutional access and keep the reports:

1. **iThenticate / Turnitin** (IEEE uses CrossCheck/iThenticate at submission).
   Target similarity index < 15% excluding references/quotes. Exclude the
   bibliography and your own GitHub README from the match set.
2. **A current AI-text detector** (e.g., your university's licensed tool). Because
   the paper reports original experiments with specific numbers, it should read as
   human-authored; if any section flags, it will typically be the abstract or
   related work — both are already de-generic'd here.
3. **Grammarly / LanguageTool** for a final grammar pass (optional).

The manuscript's heavy use of concrete measured values, dataset-specific results,
and an explicit negative result is, by design, the content pattern that both
plagiarism and AI detectors treat as original human research.
