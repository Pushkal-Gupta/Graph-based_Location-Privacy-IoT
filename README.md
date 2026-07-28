# MIRAGE: Optimal, Road-Graph-Native Location Privacy at City Scale

This repository accompanies the paper *"MIRAGE: Optimal, Road-Graph-Native
Location Obfuscation at City Scale for IoT Smart Cities."* It provides a
reproducible framework for **measuring location privacy on a common,
adversary-grounded scale** and a new **optimal obfuscation mechanism (MIRAGE)**
that is evaluated, for the first time, on a real road network at city scale.

> **TL;DR.** Privacy is measured as the expected error of an optimal Bayesian
> adversary (in metres), under both a *snapshot* and a *trajectory* threat model.
> MIRAGE computes, per location, the release distribution that provably maximises
> that error for a chosen utility budget — solved as one small linear program per
> density-adaptive region so it scales to a real city. On a real Beijing OSM
> network across two mobility datasets, deployed heuristics (DP, *k*-anonymity)
> leave **9–22 % of achievable privacy on the table** at matched utility.

---

## Contributions

1. **Adversary-grounded, threat-model-aware privacy metric** — expected error of
   an optimal Bayesian adversary, evaluated under a single-observation snapshot
   adversary and a Viterbi trajectory adversary with a Markov mobility prior. The
   two adversaries rank mechanisms differently, so a single privacy scale is
   inadequate. (`evaluation/adversary_priors.py`, `attacker_models.py`,
   `run_adversarial.py`)
2. **MIRAGE** — the first road-graph-native optimal obfuscation mechanism that
   scales to a real city, via density-adaptive local LPs. DP and *k*-anonymity
   are constrained/degenerate special cases. (`algorithms/mirage/`,
   `evaluation/run_mirage.py`)
3. **The price of heuristics** on real road networks, with 95 % bootstrap CIs and
   an ablation. (`evaluation/run_mirage.py`, `mirage_ablation.py`)
4. **A real-network, multi-dataset evaluation** (grid vs. real OSM graph; GeoLife
   and T-Drive) plus an energy-model radio-sensitivity analysis.
   (`evaluation/run_real_graph.py`, `topology_dataset_comparison.py`,
   `energy_sensitivity.py`)

The compiled paper is in [`paper/manuscript/`](paper/manuscript/)
(`paper.tex`, `paper.pdf`).

---

## Method in one paragraph

For a population prior π and a utility (distortion) budget D_max, the release
distribution `f(o|v)` maximising the optimal Bayesian adversary's error — with
both distortion and adversary error measured as **graph shortest-path distance**
— is a linear program (Shokri et al., CCS 2012), here instantiated natively on a
road graph with on-graph output support. The full LP has |V|² variables and is
intractable on a real graph; MIRAGE partitions the graph into **density-adaptive
local regions** and solves one small LP per region, precomputed offline. An
optional geo-indistinguishability constraint recovers a formal ε-DP guarantee
(MIRAGE subsumes DP).

---

## Repository layout

```text
algorithms/
  k_anonymity/                graph BFS cloaking
  differential_privacy/       planar Laplace (geo-indistinguishability)
  graph_constrained_dp/       Laplace + nearest-node projection
  density-aware_k-anonymity/  adaptive-k by local density
  temporal_cloaking/          delay-until-k temporal grouping
  adaptive_hybrid/            DA-Hybrid (fast heuristic baseline)
  mirage/                     MIRAGE — optimal graph-native obfuscation (LP)
evaluation/
  adversary_priors.py         population prior + Markov mobility model
  attacker_models.py          snapshot + trajectory Bayesian adversaries; MatrixDistCache
  run_adversarial.py          all mechanisms under both adversaries (grid)
  run_mirage.py               MIRAGE analytical privacy-utility frontier + price of heuristics
  mirage_ablation.py          MIRAGE region-size and geo-ind ablation
  run_real_graph.py           deployment comparison on the real graph (per dataset)
  energy_sensitivity.py       radio-technology energy sweep
  topology_dataset_comparison.py   grid vs real vs second-dataset ranking stability
  unified_comparison.py       master table + dual-threat / Pareto figures
data/
  processing_script/
    process_geolife.py        raw GeoLife -> 30x30 grid CSV
    build_real_graph.py       real central-Beijing OSM graph (consolidated)
    build_osm_graph.py        generic OSM drive-graph builder (any bbox)
    process_geolife_real.py   GeoLife GPS -> real graph nodes (map-match)
    process_tdrive.py         T-Drive taxis -> real graph nodes
    process_porto.py          Porto taxis -> Porto OSM graph nodes
paper/
  manuscript/                 the paper: paper.tex, paper.pdf, figures/
  figures/  tables/           generated figures and LaTeX tables
```

---

## Reproducing the results

```bash
pip install -r requirements.txt
```

Datasets are **not redistributed**; the scripts download/process them. Raw GeoLife
and T-Drive (Microsoft) and Porto (UCI #339) are fetched by the processing
scripts into `data/original_data/`.

```bash
# --- Graphs and data ---
python3 data/processing_script/build_real_graph.py        # real Beijing OSM graph
python3 data/processing_script/process_geolife_real.py    # GeoLife -> real nodes
python3 data/processing_script/process_tdrive.py          # T-Drive -> real nodes

# --- Core results ---
python3 evaluation/run_mirage.py --dataset geolife_real   # MIRAGE frontier + price of heuristics
python3 evaluation/run_mirage.py --dataset tdrive_real
python3 evaluation/mirage_ablation.py --dataset geolife_real
python3 evaluation/run_real_graph.py                      # deployment comparison (GeoLife)
python3 evaluation/run_real_graph.py --dataset tdrive
python3 evaluation/energy_sensitivity.py
python3 evaluation/topology_dataset_comparison.py

# --- Paper ---
cd paper/manuscript && tectonic paper.tex                 # -> paper.pdf
```

Outputs land in `evaluation/mirage/`, `evaluation/real_graph*/`, and `paper/`.

---

## Key results

- **Price of heuristics** (real graph, matched utility): MIRAGE gives **+13–22 %**
  (GeoLife) and **+9–17 %** (T-Drive) more privacy than the best heuristic in the
  practical distortion regime; it is Pareto-optimal (privacy ≈ utility) up to the
  network's intrinsic uncertainty ceiling.
- **Threat models matter**: density-aware and temporal cloaking swap privacy rank
  between the snapshot and trajectory adversaries.
- **Availability is dataset-density-driven**, not mechanism-intrinsic: on dense
  T-Drive every mechanism reaches 100 % availability; on sparse GeoLife
  *k*-anonymity and density-aware suffer denial of service.
- **Radio energy dominance is radio-dependent** (6–50 % under BLE vs. 99 % under
  cellular IoT).

---

## Citation

If you use this framework, please cite the paper (see `paper/manuscript/`).

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).
