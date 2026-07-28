"""
MIRAGE — the price of heuristics on a real road network (analytical frontier).
=============================================================================

Computes the privacy--utility frontier of MIRAGE (optimal, graph-native
obfuscation) against the heuristics (DP geo-indistinguishability, k-anonymity)
*analytically* and *consistently* on the SAME density-adaptive regions, so the
comparison isolates mechanism quality from sampling noise.

Per region R with local prior pi (renormalised) and graph distances d_G:
  utility(f)  = sum_v pi(v) sum_o f(o|v) d_G(v,o)           (expected distortion, m)
  privacy(f)  = sum_o min_h sum_v pi(v) f(o|v) d_G(h,v)     (optimal-adversary error, m)
Region results are aggregated weighted by region prior mass. 95% CIs come from a
weighted bootstrap over regions. The MIRAGE−heuristic gap = the "price of
heuristics": how much privacy a deployable heuristic leaves on the table at
equal utility.

Outputs: evaluation/mirage/{frontier_<ds>.json, fig_frontier_<ds>.png,
         price_of_heuristics_<ds>.md, table_frontier_<ds>.md}
"""
import os, sys, json, argparse, numpy as np
_HERE = os.path.dirname(os.path.abspath(__file__)); _BASE = os.path.join(_HERE, "..")
_PROC = os.path.join(_BASE, "data", "processed_data")
_OUT = os.path.join(_HERE, "mirage"); os.makedirs(_OUT, exist_ok=True)
for sub in ["mirage"]:
    sys.path.insert(0, os.path.join(_BASE, "algorithms", sub))
sys.path.insert(0, _HERE)
import attacker_models as AM
from adversary_priors import load_node_index, estimate_prior_and_transitions
from mirage import solve_region_lp
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

CSV_MAP = {"geolife_real": "device_locations_real.csv",
           "tdrive_real": "device_locations_tdrive.csv",
           "porto_real": "device_locations_porto.csv"}


def graph_files(dataset):
    if dataset.endswith("_grid"):
        return f"{_PROC}/city_graph_nodes.json", f"{_PROC}/city_graph_edges.json"
    if dataset.startswith("porto"):
        return f"{_PROC}/porto_graph_nodes.json", f"{_PROC}/porto_graph_edges.json"
    return f"{_PROC}/real_graph_nodes.json", f"{_PROC}/real_graph_edges.json"


# ---- analytical privacy / utility of a release matrix on a region ----
def region_privacy_utility(f, pi, dR):
    util = float((pi[:, None] * f * dR).sum())
    priv = 0.0
    for o in range(len(pi)):
        w = pi * f[:, o]
        priv += float((dR @ w).min())
    return priv, util


# ---- mechanisms on a region (all share the region + prior) ----
def dp_f(dR, eps_m):
    W = np.exp(-eps_m * dR); return W / W.sum(1, keepdims=True)

def kanon_f(dR, k):
    n = len(dR); f = np.zeros((n, n))
    for v in range(n):
        nn = np.argsort(dR[v])[:min(k, n)]; f[v, nn] = 1.0 / len(nn)
    return f


def partition_regions(D, prior, C):
    N = len(prior); un = np.ones(N, bool); order = np.argsort(prior)[::-1]; regs = []
    for seed in order:
        if not un[seed]: continue
        reg = [c for c in np.argsort(D[seed]) if un[c]][:C]
        reg = np.array(reg, int); un[reg] = False; regs.append(reg)
        if not un.any(): break
    return regs


def wbootstrap(vals, weights, B=1000, seed=0):
    vals = np.asarray(vals); weights = np.asarray(weights, float)
    if len(vals) == 0: return (float("nan"),)*3
    p = weights / weights.sum(); rng = np.random.default_rng(seed)
    idx = rng.choice(len(vals), size=(B, len(vals)), p=p)
    # weighted-resample estimate of the mean == mean over resample (already p-weighted)
    est = vals[idx].mean(1)
    base = float(np.average(vals, weights=weights))
    return base, float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def aggregate(region_vals, masses):
    """region_vals: list of (priv,util); masses: region prior mass. -> aggregate."""
    pv = np.array([r[0] for r in region_vals]); uv = np.array([r[1] for r in region_vals])
    m = np.array(masses)
    priv, plo, phi = wbootstrap(pv, m)
    util = float(np.average(uv, weights=m))
    return {"priv": priv, "priv_lo": plo, "priv_hi": phi, "util": util}


def run(dataset="geolife_real", quick=False):
    nodes_f, edges_f = graph_files(dataset)
    csv_file = f"{_PROC}/{CSV_MAP[dataset]}"
    node_ids, id_to_idx, coords = load_node_index(nodes_f)
    D = AM.build_graph_distance_matrix(nodes_f, edges_f, id_to_idx).astype(np.float64)
    prior, T = estimate_prior_and_transitions(csv_file, node_ids, id_to_idx, cache_tag=dataset)
    C = 20 if quick else 28
    regions = partition_regions(D, prior, C)
    masses = [float(prior[r].sum()) for r in regions]
    print(f"[{dataset}] {len(node_ids)} nodes -> {len(regions)} regions (C={C})")

    # precompute per-region (dR, pi)
    R = []
    for r in regions:
        dR = D[np.ix_(r, r)]; pv = prior[r].astype(float)
        pv = pv / pv.sum() if pv.sum() > 0 else np.full(len(r), 1.0/len(r))
        R.append((dR, pv))

    DMAX = [200, 1000] if quick else [150, 300, 500, 800, 1200, 1800, 2500]
    EPS = [0.01, 0.003] if quick else [0.02, 0.01, 0.006, 0.004, 0.0025, 0.0015, 0.0008]
    KS = [3, 10] if quick else [2, 3, 5, 8, 12, 18, 25]
    frontier = {"mirage": [], "dp": [], "kanon": []}

    for dm in DMAX:
        vals = []
        for dR, pv in R:
            f = solve_region_lp(dR, pv, dm)
            if f is None: f = np.eye(len(pv))
            vals.append(region_privacy_utility(f, pv, dR))
        a = aggregate(vals, masses); a["dmax"] = dm; frontier["mirage"].append(a)
        print(f"  MIRAGE dmax={dm}: priv={a['priv']:.0f} [{a['priv_lo']:.0f},{a['priv_hi']:.0f}] util={a['util']:.0f}")
    for eps in EPS:
        vals = [region_privacy_utility(dp_f(dR, eps), pv, dR) for dR, pv in R]
        a = aggregate(vals, masses); a["eps_m"] = eps; frontier["dp"].append(a)
        print(f"  DP eps/m={eps}: priv={a['priv']:.0f} util={a['util']:.0f}")
    for k in KS:
        vals = [region_privacy_utility(kanon_f(dR, k), pv, dR) for dR, pv in R]
        a = aggregate(vals, masses); a["k"] = k; frontier["kanon"].append(a)
        print(f"  k-anon k={k}: priv={a['priv']:.0f} util={a['util']:.0f}")

    with open(os.path.join(_OUT, f"frontier_{dataset}.json"), "w") as f:
        json.dump(frontier, f, indent=2)
    _plot(frontier, dataset); _price(frontier, dataset); _table(frontier, dataset)
    print(f"[{dataset}] -> {_OUT}")
    return frontier


def _plot(frontier, dataset):
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for key, lbl, col, mk in [("mirage", "MIRAGE (optimal, ours)", "#d62728", "*"),
                              ("dp", "Differential Privacy (geo-ind)", "#1f77b4", "s"),
                              ("kanon", "k-Anonymity", "#2ca02c", "o")]:
        pts = sorted(frontier[key], key=lambda r: r["util"])
        u = [p["util"] for p in pts]; pr = [p["priv"] for p in pts]
        lo = [max(0, p["priv"]-p["priv_lo"]) for p in pts]; hi = [max(0, p["priv_hi"]-p["priv"]) for p in pts]
        ax.errorbar(u, pr, yerr=[lo, hi], marker=mk, color=col, lw=2, capsize=3,
                    ms=12 if key == "mirage" else 7, label=lbl, zorder=3 if key=="mirage" else 2)
    hi = max(max(p["util"] for p in frontier["mirage"]), max(p["priv"] for p in frontier["mirage"]))
    ax.plot([0, hi], [0, hi], "--", color="gray", alpha=0.5, label="privacy = utility (ideal)")
    ax.set_xlabel("Utility loss: expected distortion (m) — lower is better")
    ax.set_ylabel("Privacy: optimal-adversary error (m) — higher is better")
    ax.set_title(f"Privacy–utility frontier ({dataset}):\nMIRAGE vs heuristics (95% CI). Vertical gap = price of heuristics.")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8, loc="lower right")
    plt.tight_layout()
    for d in (os.path.join(_OUT, f"fig_frontier_{dataset}.png"),
              os.path.join(_BASE, "paper", "figures", f"fig_frontier_{dataset}.png")):
        plt.savefig(d, dpi=300)
    plt.close()


def _interp_priv(pts, u):
    pts = sorted(pts, key=lambda r: r["util"])
    us = [p["util"] for p in pts]; pr = [p["priv"] for p in pts]
    return float(np.interp(u, us, pr))


def _price(frontier, dataset):
    lines = [f"# Price of heuristics ({dataset})\n\n",
             "MIRAGE vs the best heuristic at MATCHED utility loss "
             "(privacy = optimal-adversary error, metres):\n\n",
             "| Utility (m) | MIRAGE priv | DP priv | k-anon priv | MIRAGE gain over best |\n",
             "|---|---|---|---|---|\n"]
    for m in frontier["mirage"]:
        u = m["util"]
        dpp = _interp_priv(frontier["dp"], u); kap = _interp_priv(frontier["kanon"], u)
        best = max(dpp, kap); gain = (m["priv"]-best)/best*100 if best > 0 else float("nan")
        lines.append(f"| {u:.0f} | {m['priv']:.0f} | {dpp:.0f} | {kap:.0f} | +{gain:.0f}% |\n")
    with open(os.path.join(_OUT, f"price_of_heuristics_{dataset}.md"), "w") as f:
        f.writelines(lines)


def _table(frontier, dataset):
    lines = [f"# MIRAGE frontier ({dataset})\n\n| Mechanism | param | Utility (m) | Privacy (m) | 95% CI |\n|---|---|---|---|---|\n"]
    for m in frontier["mirage"]:
        lines.append(f"| MIRAGE | Dmax={m['dmax']} | {m['util']:.0f} | {m['priv']:.0f} | [{m['priv_lo']:.0f},{m['priv_hi']:.0f}] |\n")
    for m in frontier["dp"]:
        lines.append(f"| DP | eps/m={m['eps_m']} | {m['util']:.0f} | {m['priv']:.0f} | [{m['priv_lo']:.0f},{m['priv_hi']:.0f}] |\n")
    for m in frontier["kanon"]:
        lines.append(f"| k-anon | k={m['k']} | {m['util']:.0f} | {m['priv']:.0f} | [{m['priv_lo']:.0f},{m['priv_hi']:.0f}] |\n")
    with open(os.path.join(_OUT, f"table_frontier_{dataset}.md"), "w") as f:
        f.writelines(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geolife_real")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    run(a.dataset, a.quick)
