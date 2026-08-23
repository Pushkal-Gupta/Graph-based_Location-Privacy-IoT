# IEEE TMC Submission Package — MIRAGE

This folder is a self-contained submission package for **IEEE Transactions on
Mobile Computing (TMC)**.

**Title:** MIRAGE: Optimal, Road-Graph-Native Location Obfuscation at City Scale
for IoT Smart Cities
**Authors:** Pushkal Gupta, S. Ebenezer Juliet (VIT, Vellore)
**Corresponding author:** Pushkal Gupta — pushkalgupta2005@gmail.com

## Contents

| File | Purpose | Needed at submission |
|---|---|---|
| `paper.tex` | Main manuscript source (IEEEtran, `journal`, `compsoc`, 10pt) | Yes (source) |
| `paper.pdf` | Compiled manuscript, 8 pages | Yes (PDF for review) |
| `figures/` | All 10 figures referenced by the manuscript (300 dpi PNG) | Yes (source) |
| `IEEEtran.cls` | IEEE journal class, bundled so the source compiles anywhere | Optional* |
| `COVER_LETTER.txt` | Cover letter to the Editor-in-Chief | Yes |
| `README_SUBMISSION.md` | This manifest | No (reference only) |

\* IEEE hosts the official `IEEEtran.cls`. It is bundled here only so the package
compiles on any machine. If ScholarOne/PDF eXpress objects to a bundled class file,
delete `IEEEtran.cls` before uploading the source — the manuscript uses the
unmodified standard class.

## How to compile

```
tectonic paper.tex        # produces paper.pdf (recommended; self-contained)
# or, with a full TeX Live install:
pdflatex paper.tex && pdflatex paper.tex
```
The bibliography is embedded as a `thebibliography` block, so **no `.bib`/BibTeX
run is required**.

## Figures used (all in `figures/`)

fig_dual_threat, fig_frontier_geolife_real, fig_frontier_porto_real,
fig_mobility_gap, fig_optimality_gap, fig_cross_topology, fig_prior_robustness,
fig_trajectory_geolife_real, fig_soft_region, fig_energy_sensitivity.

## Reproducibility

Code, processed road graphs, priors, and the figure-generation scripts:
https://github.com/Pushkal-Gupta/Graph-based-Location-Privacy-IoT

## Submission checklist (ScholarOne Manuscripts)

- [ ] Manuscript PDF (`paper.pdf`) uploaded as the main document.
- [ ] LaTeX source + figures uploaded (TMC requests source; required at acceptance).
- [ ] Cover letter (`COVER_LETTER.txt`) pasted/attached.
- [ ] Keywords entered (see the manuscript's IEEEkeywords block).
- [ ] Author list and affiliations entered exactly as on the title page.
- [ ] ORCID / corresponding-author details completed.
- [ ] Suggested reviewers / conflicts of interest declared as prompted.

## Positioning as new work

This manuscript introduces a new mechanism (MIRAGE) and new results — the first
road-graph-native optimal obfuscation mechanism that scales to a real city, the
first measurement of the "price of heuristics" on real OSM networks across two
cities and three datasets, an optimality-gap validation, a prior-robustness
analysis, and a trajectory-adversary negative result. It is submitted as an
original contribution to IEEE TMC. A Springer/Wiley-formatted single-column version
of the same work is available under `../manuscript_springer/` should an alternative
venue be preferred.
