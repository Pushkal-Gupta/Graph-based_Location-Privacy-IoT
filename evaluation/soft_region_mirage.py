"""
Soft-region MIRAGE: closing the trajectory membership leak.
===========================================================
The trajectory adversary beats hard-partition MIRAGE because each release lies in
one fixed region, so observing it reveals region membership. We test a fix: a
MIXTURE of two overlapping partitions. Each release independently uses partition
A or B (hidden coin flip), so a given output can originate from either partition's
region -> the observation no longer reveals a single hard region. The mixture
emission is f(o|v)=1/2 f_A(o|v)+1/2 f_B(o|v); each f_* is still snapshot-optimal,
so the mixture stays near-optimal on snapshots while blurring membership.

We compare the filtering trajectory adversary's tracking error for hard-partition
MIRAGE, soft (2-partition) MIRAGE, and DP, at matched distortion.

Output: evaluation/mirage/soft_region_<ds>.md, fig_soft_region.png
"""
import os, sys, json, numpy as np
from datetime import datetime
from collections import defaultdict
_HERE = os.path.dirname(os.path.abspath(__file__)); _BASE = os.path.join(_HERE, "..")
_PROC = os.path.join(_BASE, "data", "processed_data"); _OUT = os.path.join(_HERE, "mirage")
sys.path.insert(0, _HERE); sys.path.insert(0, os.path.join(_BASE, "algorithms", "mirage"))
import attacker_models as AM
from adversary_priors import load_node_index, estimate_prior_and_transitions
from mirage import solve_region_lp
from run_mirage import graph_files, CSV_MAP
from run_mirage_trajectory import build_trajectories, dp_track
from plotstyle import apply_style, PALETTE; apply_style()
import matplotlib.pyplot as plt


def partition_from_order(D, prior, C, order):
    N = len(prior); un = np.ones(N, bool); regs = []
    for seed in order:
        if not un[seed]:
            continue
        reg = [c for c in np.argsort(D[seed]) if un[c]][:C]
        reg = np.array(reg, int); un[reg] = False; regs.append(reg)
        if not un.any():
            break
    return regs


def build_mech(D, prior, C, dmax, order):
    """Return node -> (region_nodes, local_idx, f_row) for a partition."""
    regions = partition_from_order(D, prior, C, order)
    node2reg = {}; reg_f = []
    for ri, r in enumerate(regions):
        dR = D[np.ix_(r, r)]; pv = prior[r].astype(float); s = pv.sum()
        pv = pv / s if s > 0 else np.full(len(r), 1.0/len(r))
        f = solve_region_lp(dR, pv, dmax)
        if f is None:
            f = np.eye(len(r))
        reg_f.append((r, f))
        for li, v in enumerate(r):
            node2reg[int(v)] = (ri, li)
    return regions, node2reg, reg_f


def track_mixture(seq, mechs, D, prior, T, rng):
    """Filtering trajectory adversary vs a mixture of partition-mechanisms."""
    N = len(prior); b = prior.copy(); errs, utils = [], []
    K = len(mechs)
    for t, v in enumerate(seq):
        if t > 0:
            b = b @ T; s = b.sum(); b = b / s if s > 0 else prior.copy()
        # release: pick a partition uniformly, sample from its region row
        k = int(rng.integers(K))
        regions, node2reg, reg_f = mechs[k]
        ri, li = node2reg[v]; r, f = reg_f[ri]
        row = np.clip(f[li], 0, None); row = row / row.sum() if row.sum() > 0 else np.full(len(r),1/len(r))
        o = int(r[int(rng.choice(len(r), p=row))])
        utils.append(float(D[v, o]))
        # adversary emission = (1/K) sum_k f_k(o|v) over all v (marginalise partition)
        src_w = defaultdict(float)
        for (regions_j, node2reg_j, reg_f_j) in mechs:
            # which region in partition j contains o, and its column
            rj, lj = node2reg_j[o]
            rr, ff = reg_f_j[rj]
            col = ff[:, lj]  # f_j(o | v') for v' in region rr
            for vi, w in zip(rr, col):
                if w > 0:
                    src_w[int(vi)] += w / K
        srcs = np.array(list(src_w.keys())); ws = np.array([src_w[s] for s in srcs])
        post = b[srcs] * ws
        post = post / post.sum() if post.sum() > 0 else np.full(len(srcs), 1/len(srcs))
        exp = D[:, srcs] @ post; est = int(np.argmin(exp))
        errs.append(float(D[est, v]))
        nb = np.zeros(N); nb[srcs] = post; s = nb.sum(); b = nb / s if s > 0 else prior.copy()
    return float(np.mean(errs)), float(np.mean(utils))


def track_hard(seq, mech, D, prior, T, rng):
    return track_mixture(seq, [mech], D, prior, T, rng)


def run(dataset="geolife_real", quick=False):
    nodes_f, edges_f = graph_files(dataset)
    node_ids, id_to_idx, coords = load_node_index(nodes_f)
    D = AM.build_graph_distance_matrix(nodes_f, edges_f, id_to_idx).astype(np.float64)
    prior, T = estimate_prior_and_transitions(f"{_PROC}/{CSV_MAP[dataset]}", node_ids,
                                              id_to_idx, cache_tag=dataset)
    C = 20 if quick else 28
    trajs = build_trajectories(f"{_PROC}/{CSV_MAP[dataset]}",
                               max_users=(8 if quick else 50),
                               max_rows=(400_000 if quick else None), max_len=40)
    seqs = [[id_to_idx[n] for n in s] for s in trajs.values()]
    print(f"[{dataset}] {len(seqs)} traces, C={C}")

    order_a = np.argsort(prior)[::-1]                  # densest-first
    rng0 = np.random.default_rng(7)
    order_b = rng0.permutation(len(prior))             # different seeding -> overlapping regions
    DMAX = [500, 800] if quick else [300, 500, 800, 1200]
    res = {"hard": [], "soft": [], "dp": []}
    rng = np.random.default_rng(0)
    for dm in DMAX:
        mech_a = build_mech(D, prior, C, dm, order_a)
        mech_b = build_mech(D, prior, C, dm, order_b)
        eH = [track_hard(s, mech_a, D, prior, T, rng) for s in seqs]
        eS = [track_mixture(s, [mech_a, mech_b], D, prior, T, rng) for s in seqs]
        res["hard"].append({"dmax": dm, "traj_priv": float(np.mean([e[0] for e in eH])),
                            "util": float(np.mean([e[1] for e in eH]))})
        res["soft"].append({"dmax": dm, "traj_priv": float(np.mean([e[0] for e in eS])),
                            "util": float(np.mean([e[1] for e in eS]))})
        print(f"  Dmax={dm}: hard traj_priv={res['hard'][-1]['traj_priv']:.0f}"
              f"(u={res['hard'][-1]['util']:.0f}) soft traj_priv={res['soft'][-1]['traj_priv']:.0f}"
              f"(u={res['soft'][-1]['util']:.0f})")
    for eps in ([0.003] if quick else [0.006, 0.003, 0.0015]):
        E = [dp_track(s, D, prior, T, eps, rng) for s in seqs]
        res["dp"].append({"eps_m": eps, "traj_priv": float(np.mean([e[0] for e in E])),
                          "util": float(np.mean([e[1] for e in E]))})
    json.dump(res, open(os.path.join(_OUT, f"soft_region_{dataset}.json"), "w"), indent=2)
    _report(res, dataset); _plot(res, dataset)
    print(f"-> {_OUT}/soft_region_{dataset}.md")


def _interp(pts, u):
    pts = sorted(pts, key=lambda r: r["util"]); return float(np.interp(u,[p["util"] for p in pts],[p["traj_priv"] for p in pts]))


def _report(res, dataset):
    lines = [f"# Soft-region MIRAGE: trajectory membership-leak fix ({dataset})\n\n",
             "Filtering trajectory-adversary tracking error (m) at matched distortion. "
             "Soft = mixture of two overlapping partitions so a release does not reveal "
             "a hard region.\n\n",
             "| Dmax | hard-MIRAGE priv/util | soft-MIRAGE priv/util | soft gain |\n|---|---|---|---|\n"]
    for a, b in zip(res["hard"], res["soft"]):
        g = (b["traj_priv"]-a["traj_priv"])/a["traj_priv"]*100 if a["traj_priv"]>0 else 0
        lines.append(f"| {a['dmax']} | {a['traj_priv']:.0f}/{a['util']:.0f} | "
                     f"{b['traj_priv']:.0f}/{b['util']:.0f} | {g:+.0f}% |\n")
    if res["dp"]:
        u = res["soft"][len(res["soft"])//2]["util"]
        lines.append(f"\nAt util~{u:.0f}m: hard={_interp(res['hard'],u):.0f}, "
                     f"soft={_interp(res['soft'],u):.0f}, DP={_interp(res['dp'],u):.0f}.\n")
    open(os.path.join(_OUT, f"soft_region_{dataset}.md"), "w").writelines(lines)


def _plot(res, dataset):
    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    for key, lbl, col, mk in [("hard","hard-partition MIRAGE",PALETTE["mirage"],"s"),
                              ("soft","soft (2-partition) MIRAGE",PALETTE["mirage_t"],"*"),
                              ("dp","Differential Privacy",PALETTE["dp"],"o")]:
        pts = sorted(res[key], key=lambda r: r["util"])
        if not pts: continue
        ax.plot([p["util"] for p in pts], [p["traj_priv"] for p in pts], marker=mk,
                color=col, ms=12 if key=="soft" else 8, label=lbl)
    ax.set_xlabel("Utility loss: distortion (m)"); ax.set_ylabel("Trajectory tracking error (m)")
    ax.set_title(f"Soft regions reduce the trajectory membership leak ({dataset})")
    ax.legend(); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    for d in (os.path.join(_OUT, "fig_soft_region.png"),
              os.path.join(_BASE, "paper", "figures", "fig_soft_region.png")):
        plt.savefig(d, dpi=300)
    plt.close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--dataset", default="geolife_real")
    ap.add_argument("--quick", action="store_true"); a = ap.parse_args()
    run(a.dataset, a.quick)
