"""
MIRAGE-T: trajectory-optimal MIRAGE against the sequential adversary.
====================================================================
Snapshot-MIRAGE optimises each release against the STATIC prior. A trajectory
adversary, however, exploits the Markov mobility model: its effective belief at
step t is the mobility-propagated posterior, which is far more concentrated than
the static prior. MIRAGE-T instead solves, at each step, the region LP against
the adversary's *current belief* (receding-horizon / certainty-equivalent
optimal control), so it hides precisely where the adversary is confident.

We evaluate the filtering (causal) trajectory adversary's tracking error for
snapshot-MIRAGE vs MIRAGE-T vs DP, at matched distortion, on real trajectories.
The mechanism uses the same density-adaptive region partition as MIRAGE; only the
per-step prior differs (static vs mobility-propagated belief).

Output: evaluation/mirage/trajectory_<dataset>.md, fig_trajectory_<dataset>.png
"""
import os, sys, json, argparse, numpy as np
from datetime import datetime
from collections import defaultdict
_HERE = os.path.dirname(os.path.abspath(__file__)); _BASE = os.path.join(_HERE, "..")
_PROC = os.path.join(_BASE, "data", "processed_data"); _OUT = os.path.join(_HERE, "mirage")
sys.path.insert(0, os.path.join(_BASE, "algorithms", "mirage")); sys.path.insert(0, _HERE)
import attacker_models as AM
from adversary_priors import load_node_index, estimate_prior_and_transitions
from mirage import solve_region_lp
from run_mirage import graph_files, partition_regions, CSV_MAP
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt


def build_trajectories(csv_file, window=600, max_users=60, max_rows=None, max_len=40):
    trajs = defaultdict(list)
    import csv as _csv
    with open(csv_file) as f:
        for i, row in enumerate(_csv.DictReader(f)):
            if max_rows and i >= max_rows:
                break
            ts = datetime.strptime(f"{row['date']} {row['time']}", "%Y-%m-%d %H:%M:%S")
            trajs[row["user_id"]].append((int(ts.timestamp()) // window, str(row["location_id"])))
    # collapse to one node per window (last), keep users with long sequences
    seqs = {}
    for u, pts in trajs.items():
        pts.sort()
        seq, last_b = [], None
        for b, node in pts:
            if b != last_b:
                seq.append(node); last_b = b
        if len(seq) >= 6:
            seqs[u] = seq[:max_len]      # cap length for tractable per-step LPs
    users = sorted(seqs, key=lambda u: -len(seqs[u]))[:max_users]
    return {u: seqs[u] for u in users}


def track(true_seq_idx, regions, node2reg, reg_dR, reg_local, D, prior, T, dmax,
          rng, dynamic=True, static_cache=None):
    """Simulate releases + filtering-adversary tracking error for one user."""
    N = len(prior)
    b = prior.copy()
    errs, utils = [], []
    for t, v in enumerate(true_seq_idx):
        if t > 0:
            b = b @ T; s = b.sum(); b = b / s if s > 0 else prior.copy()
        ri = node2reg[v]; r = regions[ri]; dR = reg_dR[ri]; lv = reg_local[ri][v]
        if dynamic:
            pv = b[r].astype(float); s = pv.sum()
            pv = pv / s if s > 0 else np.full(len(r), 1.0 / len(r))
            f = solve_region_lp(dR, pv, dmax)
        else:
            if static_cache[ri] is None:
                pv = prior[r].astype(float); s = pv.sum()
                pv = pv / s if s > 0 else np.full(len(r), 1.0 / len(r))
                static_cache[ri] = solve_region_lp(dR, pv, dmax)
            f = static_cache[ri]
        if f is None:
            f = np.eye(len(r))
        row = np.clip(f[lv], 0, None); row = row / row.sum() if row.sum() > 0 else np.full(len(r), 1.0/len(r))
        o_local = int(rng.choice(len(r), p=row)); o = int(r[o_local])
        utils.append(float(D[v, o]))
        # adversary Bayes update within region (region is revealed by the release)
        post = b[r] * f[:, o_local]
        post = post / post.sum() if post.sum() > 0 else np.full(len(r), 1.0/len(r))
        exp = D[:, r] @ post; est = int(np.argmin(exp))
        errs.append(float(D[est, v]))
        nb = np.zeros(N); nb[r] = post; b = nb
    return float(np.mean(errs)), float(np.mean(utils))


def dp_track(true_seq_idx, D, prior, T, eps_m, rng, CAND=40):
    """Filtering-adversary tracking error for per-report geo-ind DP."""
    N = len(prior); b = prior.copy(); errs, utils = [], []
    for t, v in enumerate(true_seq_idx):
        if t > 0:
            b = b @ T; s = b.sum(); b = b / s if s > 0 else prior.copy()
        cand = np.argsort(D[v])[:CAND]
        w = np.exp(-eps_m * D[v, cand]); w = w / w.sum()
        o = int(cand[rng.choice(len(cand), p=w)])
        utils.append(float(D[v, o]))
        src = np.argsort(D[o])[:CAND]
        emit = np.exp(-eps_m * D[o, src])
        post = b[src] * emit
        post = post / post.sum() if post.sum() > 0 else np.full(len(src), 1.0/len(src))
        exp = D[:, src] @ post; est = int(np.argmin(exp))
        errs.append(float(D[est, v]))
        nb = np.zeros(N); nb[src] = post; b = nb / nb.sum()
    return float(np.mean(errs)), float(np.mean(utils))


def run(dataset="geolife_real", quick=False):
    nodes_f, edges_f = graph_files(dataset)
    node_ids, id_to_idx, coords = load_node_index(nodes_f)
    D = AM.build_graph_distance_matrix(nodes_f, edges_f, id_to_idx).astype(np.float64)
    prior, T = estimate_prior_and_transitions(f"{_PROC}/{CSV_MAP[dataset]}", node_ids,
                                              id_to_idx, cache_tag=dataset)
    C = 20 if quick else 28
    regions = partition_regions(D, prior, C)
    node2reg = {int(v): ri for ri, r in enumerate(regions) for v in r}
    reg_dR = [D[np.ix_(r, r)] for r in regions]
    reg_local = [{int(v): i for i, v in enumerate(r)} for r in regions]
    trajs = build_trajectories(f"{_PROC}/{CSV_MAP[dataset]}",
                               max_users=(8 if quick else 60),
                               max_rows=(400_000 if quick else None))
    print(f"[{dataset}] {len(node_ids)} nodes, {len(regions)} regions, {len(trajs)} user traces")

    DMAX = [500, 800] if quick else [300, 500, 800, 1200]
    rng = np.random.default_rng(0)
    res = {"snapshot": [], "mirage_t": [], "dp": []}
    seqs = [[id_to_idx[n] for n in s] for s in trajs.values()]

    for dm in DMAX:
        for tag, dyn in [("snapshot", False), ("mirage_t", True)]:
            E, U = [], []
            for s in seqs:
                sc = [None] * len(regions)
                e, u = track(s, regions, node2reg, reg_dR, reg_local, D, prior, T,
                             dm, rng, dynamic=dyn, static_cache=sc)
                E.append(e); U.append(u)
            res[tag].append({"dmax": dm, "traj_priv": float(np.mean(E)),
                             "util": float(np.mean(U))})
        print(f"  Dmax={dm}: snapshot traj_priv={res['snapshot'][-1]['traj_priv']:.0f} "
              f"(u={res['snapshot'][-1]['util']:.0f}) | "
              f"MIRAGE-T traj_priv={res['mirage_t'][-1]['traj_priv']:.0f} "
              f"(u={res['mirage_t'][-1]['util']:.0f})")
    for eps in ([0.003] if quick else [0.006, 0.003, 0.0015]):
        E, U = [], []
        for s in seqs:
            e, u = dp_track(s, D, prior, T, eps, rng)
            E.append(e); U.append(u)
        res["dp"].append({"eps_m": eps, "traj_priv": float(np.mean(E)), "util": float(np.mean(U))})
        print(f"  DP eps/m={eps}: traj_priv={res['dp'][-1]['traj_priv']:.0f} (u={res['dp'][-1]['util']:.0f})")

    json.dump(res, open(os.path.join(_OUT, f"trajectory_{dataset}.json"), "w"), indent=2)
    _report(res, dataset); _plot(res, dataset)
    print(f"[{dataset}] -> {_OUT}")
    return res


def _report(res, dataset):
    lines = [f"# Trajectory privacy: MIRAGE-T vs snapshot-MIRAGE ({dataset})\n\n",
             "Filtering trajectory-adversary tracking error (privacy, m) at matched "
             "distortion. MIRAGE-T solves each release against the adversary's "
             "mobility-propagated belief.\n\n",
             "| Dmax | snapshot-MIRAGE priv/util | MIRAGE-T priv/util | MIRAGE-T gain |\n|---|---|---|---|\n"]
    for a, b in zip(res["snapshot"], res["mirage_t"]):
        g = (b["traj_priv"] - a["traj_priv"]) / a["traj_priv"] * 100 if a["traj_priv"] > 0 else float("nan")
        lines.append(f"| {a['dmax']} | {a['traj_priv']:.0f}/{a['util']:.0f} | "
                     f"{b['traj_priv']:.0f}/{b['util']:.0f} | {g:+.0f}% |\n")
    open(os.path.join(_OUT, f"trajectory_{dataset}.md"), "w").writelines(lines)


def _plot(res, dataset):
    fig, ax = plt.subplots(figsize=(7, 5))
    for key, lbl, col, mk in [("snapshot", "snapshot-MIRAGE", "#ff7f0e", "s"),
                              ("mirage_t", "MIRAGE-T (trajectory-optimal)", "#d62728", "*"),
                              ("dp", "Differential Privacy", "#1f77b4", "o")]:
        pts = sorted(res[key], key=lambda r: r["util"])
        if not pts: continue
        ax.plot([p["util"] for p in pts], [p["traj_priv"] for p in pts], marker=mk,
                color=col, lw=2, ms=11 if key == "mirage_t" else 7, label=lbl)
    ax.set_xlabel("Utility loss: distortion (m)"); ax.set_ylabel("Trajectory-adversary tracking error (m)")
    ax.set_title(f"Trajectory privacy vs the sequential adversary ({dataset})")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    plt.tight_layout()
    for d in (os.path.join(_OUT, f"fig_trajectory_{dataset}.png"),
              os.path.join(_BASE, "paper", "figures", f"fig_trajectory_{dataset}.png")):
        plt.savefig(d, dpi=300)
    plt.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dataset", default="geolife_real")
    ap.add_argument("--quick", action="store_true"); a = ap.parse_args()
    run(a.dataset, a.quick)
