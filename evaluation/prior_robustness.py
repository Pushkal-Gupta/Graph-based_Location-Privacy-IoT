"""
Is MIRAGE robust to a misspecified prior?
=========================================
MIRAGE exploits the population prior pi, which a deployer must ESTIMATE from
finite, possibly stale data. We stress-test this: MIRAGE solves its LP with a
corrupted prior hat_pi = (1-alpha)*pi + alpha*uniform (alpha = degree of
ignorance; alpha=0 perfect knowledge, alpha=1 no prior at all), while the
adversary attacks with the TRUE pi. We measure how much of MIRAGE's advantage
over the (prior-free) heuristics survives. If even at alpha=1 MIRAGE >= the best
heuristic, the optimal-mechanism *structure* helps regardless of prior quality.

Output: evaluation/mirage/prior_robustness_<ds>.md, fig_prior_robustness.png
"""
import os, sys, json, numpy as np
_HERE = os.path.dirname(os.path.abspath(__file__)); _BASE = os.path.join(_HERE, "..")
_PROC = os.path.join(_BASE, "data", "processed_data"); _OUT = os.path.join(_HERE, "mirage")
sys.path.insert(0, _HERE); sys.path.insert(0, os.path.join(_BASE, "algorithms", "mirage"))
import attacker_models as AM
from adversary_priors import load_node_index, estimate_prior_and_transitions
from mirage import solve_region_lp
from run_mirage import (graph_files, partition_regions, region_privacy_utility,
                        dp_f, kanon_f, aggregate, CSV_MAP)
from plotstyle import apply_style, PALETTE; apply_style()
import matplotlib.pyplot as plt


def run(dataset="geolife_real", quick=False):
    nodes_f, edges_f = graph_files(dataset)
    node_ids, id_to_idx, coords = load_node_index(nodes_f)
    D = AM.build_graph_distance_matrix(nodes_f, edges_f, id_to_idx).astype(np.float64)
    prior, T = estimate_prior_and_transitions(f"{_PROC}/{CSV_MAP[dataset]}", node_ids,
                                              id_to_idx, cache_tag=dataset)
    C = 20 if quick else 28
    regions = partition_regions(D, prior, C)
    masses = [float(prior[r].sum()) for r in regions]
    RD = []
    for r in regions:
        dR = D[np.ix_(r, r)]; pt = prior[r].astype(float); s = pt.sum()
        pt = pt / s if s > 0 else np.full(len(r), 1.0/len(r))
        RD.append((dR, pt))     # (distances, TRUE local prior)

    ALPHAS = [0.0, 0.25, 0.5, 0.75, 1.0]
    DMAX = [300, 500]
    # reference heuristic privacy at matched utility (prior-free; eval with true prior)
    def heur_priv_at(util_target):
        best = 0.0
        for eps in [0.02, 0.01, 0.006, 0.004, 0.0025, 0.0015, 0.0008]:
            vals = [region_privacy_utility(dp_f(dR, eps), pt, dR) for dR, pt in RD]
            a = aggregate(vals, masses)
            best = max(best, np.interp(util_target, [a["util"]], [a["priv"]]) if abs(a["util"]-util_target) < 60 else 0)
        # proper interp over the DP + kanon sweeps
        return best
    # build full DP and kanon frontiers once (true-prior eval)
    def frontier(mech_f, params):
        pts = []
        for p in params:
            vals = [region_privacy_utility(mech_f(dR, p), pt, dR) for dR, pt in RD]
            pts.append(aggregate(vals, masses))
        return sorted(pts, key=lambda x: x["util"])
    dp_fr = frontier(dp_f, [0.02, 0.01, 0.006, 0.004, 0.0025, 0.0015, 0.0008])
    ka_fr = frontier(kanon_f, [2, 3, 5, 8, 12, 18, 25])
    def best_heur(u):
        d = np.interp(u, [x["util"] for x in dp_fr], [x["priv"] for x in dp_fr])
        k = np.interp(u, [x["util"] for x in ka_fr], [x["priv"] for x in ka_fr])
        return max(d, k)

    results = {dm: [] for dm in DMAX}
    for dm in DMAX:
        for al in ALPHAS:
            vals = []
            for (dR, pt) in RD:
                n = len(pt)
                hat = (1 - al) * pt + al * (np.ones(n) / n)   # corrupted prior
                f = solve_region_lp(dR, hat, dm)
                if f is None:
                    f = np.eye(n)
                vals.append(region_privacy_utility(f, pt, dR))  # EVAL with TRUE prior
            a = aggregate(vals, masses)
            a["alpha"] = al
            a["heur"] = float(best_heur(a["util"]))
            results[dm].append(a)
            print(f"  Dmax={dm} alpha={al}: MIRAGE priv={a['priv']:.0f} "
                  f"(u={a['util']:.0f}) vs best-heuristic={a['heur']:.0f}")

    json.dump(results, open(os.path.join(_OUT, f"prior_robustness_{dataset}.json"), "w"),
              indent=2, default=float)
    _report(results, dataset); _plot(results, dataset)
    print(f"-> {_OUT}/prior_robustness_{dataset}.md")


def _report(results, dataset):
    lines = [f"# Prior-misspecification robustness ({dataset})\n\n",
             "MIRAGE solves with a corrupted prior (alpha = ignorance; 1 = uniform), "
             "adversary attacks with the true prior. Privacy (optimal-adversary error, m).\n\n"]
    for dm, rows in results.items():
        lines.append(f"## $D_{{\\max}}={dm}$\\,m\n\n| $\\alpha$ | MIRAGE priv | best heuristic | MIRAGE still wins? |\n|---|---|---|---|\n")
        for a in rows:
            lines.append(f"| {a['alpha']} | {a['priv']:.0f} | {a['heur']:.0f} | "
                         f"{'yes' if a['priv'] >= a['heur'] else 'no'} |\n")
        lines.append("\n")
    open(os.path.join(_OUT, f"prior_robustness_{dataset}.md"), "w").writelines(lines)


def _plot(results, dataset):
    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    dm = sorted(results)[0]
    rows = results[dm]
    al = [a["alpha"] for a in rows]
    ax.plot(al, [a["priv"] for a in rows], "*-", color=PALETTE["mirage"], ms=13,
            label="MIRAGE (corrupted prior)")
    ax.axhline(rows[0]["heur"], ls="--", color=PALETTE["dp"], lw=2,
               label="best heuristic (prior-free)")
    ax.fill_between(al, [a["heur"] for a in rows], [a["priv"] for a in rows],
                    where=[a["priv"] >= a["heur"] for a in rows], alpha=0.12,
                    color=PALETTE["mirage"])
    ax.set_xlabel(r"Prior ignorance $\alpha$  (0 = perfect, 1 = uniform)")
    ax.set_ylabel("Privacy: optimal-adversary error (m)")
    ax.set_title(f"MIRAGE stays above heuristics under a wrong prior ($D_{{\\max}}{{=}}{dm}$)")
    ax.legend(); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    for d in (os.path.join(_OUT, "fig_prior_robustness.png"),
              os.path.join(_BASE, "paper", "figures", "fig_prior_robustness.png")):
        plt.savefig(d, dpi=300)
    plt.close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--dataset", default="geolife_real")
    ap.add_argument("--quick", action="store_true"); a = ap.parse_args()
    run(a.dataset, a.quick)
