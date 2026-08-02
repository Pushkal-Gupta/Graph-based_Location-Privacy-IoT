"""
Is MIRAGE's advantage statistically significant (not just CI overlap)?
=====================================================================
Paired, region-level test. At a matched aggregate utility we compute each
mechanism's privacy PER REGION and pair MIRAGE against each heuristic by region.
A mass-weighted paired bootstrap over regions gives the mean privacy difference,
its 95% CI, and a one-sided p-value (fraction of bootstrap means <= 0). Because
regions are the independent units and the comparison is paired, this controls for
region-to-region heterogeneity.

Output: evaluation/mirage/significance_<ds>.md
"""
import os, sys, json, numpy as np
_HERE = os.path.dirname(os.path.abspath(__file__)); _BASE = os.path.join(_HERE, "..")
_PROC = os.path.join(_BASE, "data", "processed_data"); _OUT = os.path.join(_HERE, "mirage")
sys.path.insert(0, _HERE); sys.path.insert(0, os.path.join(_BASE, "algorithms", "mirage"))
import attacker_models as AM
from adversary_priors import load_node_index, estimate_prior_and_transitions
from mirage import solve_region_lp
from run_mirage import graph_files, partition_regions, region_privacy_utility, dp_f, kanon_f, CSV_MAP


def agg_util(per_region, masses):
    return float(np.average([u for _, u in per_region], weights=masses))


def run(dataset="geolife_real", dmax=500):
    nodes_f, edges_f = graph_files(dataset)
    node_ids, id_to_idx, coords = load_node_index(nodes_f)
    D = AM.build_graph_distance_matrix(nodes_f, edges_f, id_to_idx).astype(np.float64)
    prior, T = estimate_prior_and_transitions(f"{_PROC}/{CSV_MAP[dataset]}", node_ids,
                                              id_to_idx, cache_tag=dataset)
    regions = partition_regions(D, prior, 28)
    masses = np.array([float(prior[r].sum()) for r in regions])
    RD = []
    for r in regions:
        dR = D[np.ix_(r, r)]; pv = prior[r].astype(float); s = pv.sum()
        pv = pv / s if s > 0 else np.full(len(r), 1.0/len(r))
        RD.append((dR, pv))

    mir = [region_privacy_utility(solve_region_lp(dR, pv, dmax) if solve_region_lp(dR, pv, dmax) is not None else np.eye(len(pv)), pv, dR) for dR, pv in RD]
    mir_u = agg_util(mir, masses)

    # choose DP eps and k giving aggregate utility closest to MIRAGE's
    def pick(mech_f, params):
        best, bp = None, None
        for p in params:
            pr = [region_privacy_utility(mech_f(dR, p), pv, dR) for dR, pv in RD]
            u = agg_util(pr, masses)
            if best is None or abs(u - mir_u) < abs(best - mir_u):
                best, bp, bpr = u, p, pr
        return bp, bpr
    eps, dp = pick(dp_f, [0.02, 0.01, 0.006, 0.004, 0.0025, 0.0015, 0.0008])
    k, ka = pick(kanon_f, [2, 3, 5, 8, 12, 18, 25])

    mir_p = np.array([p for p, _ in mir]); dp_p = np.array([p for p, _ in dp]); ka_p = np.array([p for p, _ in ka])

    def paired_boot(a, b, B=5000, seed=0):
        d = a - b; rng = np.random.default_rng(seed); w = masses / masses.sum()
        idx = rng.choice(len(d), size=(B, len(d)), p=w)
        bm = d[idx].mean(1)
        mean = float(np.average(d, weights=w))
        return mean, float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5)), float((bm <= 0).mean())

    lines = [f"# Statistical significance of MIRAGE's advantage ({dataset})\n\n",
             f"Region-level paired bootstrap ({len(regions)} regions), MIRAGE "
             f"($D_{{\\max}}={dmax}$, util {mir_u:.0f}\\,m) vs.\\ each heuristic at "
             f"matched aggregate utility. Positive = MIRAGE more private.\n\n",
             "| Comparison | Mean $\\Delta$ priv (m) | 95% CI | one-sided $p$ |\n|---|---|---|---|\n"]
    for name, arr in [(f"vs DP ($\\varepsilon$/m={eps})", dp_p), (f"vs $k$-anon (k={k})", ka_p)]:
        m, lo, hi, p = paired_boot(mir_p, arr)
        lines.append(f"| {name} | {m:+.0f} | [{lo:+.0f}, {hi:+.0f}] | "
                     f"{'<0.001' if p < 0.001 else f'{p:.3f}'} |\n")
    lines.append(f"\nMIRAGE utility {mir_u:.0f}\\,m; DP {agg_util(dp,masses):.0f}\\,m; "
                 f"$k$-anon {agg_util(ka,masses):.0f}\\,m.\n")
    open(os.path.join(_OUT, f"significance_{dataset}.md"), "w").writelines(lines)
    print("".join(lines))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--dataset", default="geolife_real")
    ap.add_argument("--dmax", type=int, default=500); a = ap.parse_args()
    run(a.dataset, a.dmax)
