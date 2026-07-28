"""
Adversarial Privacy Evaluation Runner
=====================================

Drives every privacy mechanism through the two adversary models defined in
attacker_models.py and writes an adversary-grounded privacy metric (expected
adversary localisation error, in metres) for each -- the theoretically founded,
cross-family-comparable replacement for the old ad-hoc [0,1] "privacy score".

Outputs
-------
    results/<algo>/adversary.json         (per-config adversary metrics)
    evaluation/adversarial/adversarial_report.md
    evaluation/adversarial/table_adversarial.{md,tex,csv}

Usage
-----
    python3 evaluation/run_adversarial.py            # full run (window = 600 s)
    python3 evaluation/run_adversarial.py --quick     # tiny sample, for testing
"""

import os
import sys
import csv
import json
import argparse
import numpy as np
from datetime import datetime
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_BASE = os.path.join(_HERE, "..")
_DATA = os.path.join(_BASE, "data", "processed_data")
_RESULTS = os.path.join(_BASE, "results")
_OUT = os.path.join(_HERE, "adversarial")

NODES_FILE = os.path.join(_DATA, "city_graph_nodes.json")
EDGES_FILE = os.path.join(_DATA, "city_graph_edges.json")
CSV_FILE = os.path.join(_DATA, "device_locations.csv")

# Make mechanism modules importable (their folders are on separate paths).
for sub in ["k_anonymity", "differential_privacy", "graph_constrained_dp",
            "density-aware_k-anonymity", "temporal_cloaking", "adaptive_hybrid"]:
    sys.path.insert(0, os.path.join(_BASE, "algorithms", sub))
sys.path.insert(0, _HERE)

import attacker_models  # noqa: E402
from adversary_priors import load_node_index  # noqa: E402

WINDOW = 600  # representative 10-min window used throughout the paper


# ---------------------------------------------------------------------
# Snapshot construction (mirrors the simulation drivers)
# ---------------------------------------------------------------------
def build_window_snapshots(window=WINDOW, max_rows=None):
    """
    Return an ordered list of (bucket_id, {user: node}) for the given window,
    in time order.  Only buckets with >= 2 users are kept.
    """
    buckets = defaultdict(dict)
    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break
            ts = datetime.strptime(f"{row['date']} {row['time']}",
                                   "%Y-%m-%d %H:%M:%S")
            b = int(ts.timestamp()) // window
            buckets[b][row["user_id"]] = str(row["location_id"])
    ordered = [(b, buckets[b]) for b in sorted(buckets) if len(buckets[b]) >= 2]
    return ordered


def sample_snapshots(ordered, n):
    """Evenly subsample n snapshots from the ordered bucket list."""
    if len(ordered) <= n:
        return ordered
    step = len(ordered) // n
    return ordered[::step][:n]


# ---------------------------------------------------------------------
# Snapshot-adversary evaluation
# ---------------------------------------------------------------------
def eval_snapshot_dp(obf, snapshots, adv, id_to_idx, coords, scale):
    """Batched Bayesian attack on a coordinate-noise mechanism (DP)."""
    errs, hits = [], []
    D = adv.D
    prior = adv.prior
    logprior = np.log(prior + 1e-300)
    for _, snap in snapshots:
        res = obf.anonymize_snapshot(snap)
        pts, trues = [], []
        for uid, data in res.items():
            pts.append(data["noisy_coords"])
            trues.append(id_to_idx[data["original_node"]])
        if not pts:
            continue
        pts = np.asarray(pts, dtype=float)                     # (m, 2)
        trues = np.asarray(trues, dtype=int)
        # Emission log-density: -||o - coord(v)||_1 / scale, batched over users.
        # l1[m, N] = sum_c |pts[m,c] - coords[N,c]|
        l1 = (np.abs(pts[:, None, 0] - coords[None, :, 0]) +
              np.abs(pts[:, None, 1] - coords[None, :, 1]))     # (m, N)
        logpost = -l1 / max(scale, 1e-12) + logprior[None, :]
        logpost -= logpost.max(axis=1, keepdims=True)
        post = np.exp(logpost)
        post /= post.sum(axis=1, keepdims=True)
        exp_dist = post @ D                                    # (m, N)
        est = np.argmin(exp_dist, axis=1)                      # (m,)
        errs.extend(D[est, trues].tolist())
        hits.extend((est == trues).astype(float).tolist())
    return _summ(errs, hits)


def eval_snapshot_projected(obf, snapshots, adv, id_to_idx, coords, scale):
    """Attack on graph-constrained DP (observation = projected node)."""
    errs, hits = [], []
    for _, snap in snapshots:
        res = obf.anonymize_snapshot(snap)
        for uid, data in res.items():
            obs_idx = id_to_idx[data["cloaked_node"]]
            true_idx = id_to_idx[data["original_node"]]
            e, h = adv.attack_projected(obs_idx, scale, true_idx)
            errs.append(e)
            hits.append(1.0 if h else 0.0)
    return _summ(errs, hits)


def eval_snapshot_region(obf, snapshots, adv, id_to_idx):
    """Attack on cloaking mechanisms (k-anon / density-aware / group)."""
    errs, hits = [], []
    for _, snap in snapshots:
        res = obf.anonymize_snapshot(snap)
        # Nodes that actually hold a user this snapshot.
        user_nodes = defaultdict(list)
        for uid, node in snap.items():
            user_nodes[str(node)].append(uid)
        for uid, data in res.items():
            region = set(str(n) for n in data["region"])
            anon_nodes = [id_to_idx[n] for n in region if n in user_nodes]
            true_idx = id_to_idx[data["original_node"]]
            e, h = adv.attack_anonymity_set(anon_nodes, true_idx)
            errs.append(e)
            hits.append(1.0 if h else 0.0)
    return _summ(errs, hits)


def build_trajectories(window=WINDOW, max_users=200, max_rows=None):
    """Per-user time-ordered [(node, datetime)] for temporal cloaking."""
    from collections import defaultdict as _dd
    trajs = _dd(list)
    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break
            u = row["user_id"]
            ts = datetime.strptime(f"{row['date']} {row['time']}",
                                   "%Y-%m-%d %H:%M:%S")
            trajs[u].append((str(row["location_id"]), ts))
    # Keep the users with the most points (denser -> groups of size k form).
    users = sorted(trajs, key=lambda u: -len(trajs[u]))[:max_users]
    out = {}
    for u in users:
        pts = sorted(trajs[u], key=lambda x: x[1])
        out[u] = pts
    return out


def eval_temporal(cloaker, trajs, sadv, tadv, id_to_idx, min_len=5):
    """
    Evaluate temporal cloaking under both adversaries.  Records that share a
    (window_start, cloaked_node) belong to one release group; their original
    nodes form the anonymity set the adversary faces.
    """
    records = cloaker.cloak_trajectories(trajs)
    if not records:
        return None
    # Group -> anonymity set (nodes of members).
    groups = defaultdict(list)
    for r in records:
        groups[(r["window_start"], r["cloaked_node"])].append(r)
    group_nodes = {g: [id_to_idx[str(rr["original_node"])] for rr in rs
                       if str(rr["original_node"]) in id_to_idx]
                   for g, rs in groups.items()}

    # Snapshot adversary.
    s_err, s_hit = [], []
    for r in records:
        if str(r["original_node"]) not in id_to_idx:
            continue
        g = (r["window_start"], r["cloaked_node"])
        true_idx = id_to_idx[str(r["original_node"])]
        e, h = sadv.attack_anonymity_set(group_nodes[g], true_idx)
        s_err.append(e)
        s_hit.append(1.0 if h else 0.0)
    s = _summ(s_err, s_hit)

    # Trajectory adversary: per-user sequence of (true, group-emission).
    per_user = defaultdict(list)
    for r in records:
        if str(r["original_node"]) in id_to_idx:
            per_user[r["user"]].append(r)
    t_err, t_reid = [], []
    for u, rs in per_user.items():
        if len(rs) < min_len:
            continue
        rs.sort(key=lambda x: x["window_start"])
        true_seq = [id_to_idx[str(r["original_node"])] for r in rs]
        log_em = [tadv.emission_anonymity_set(
                    group_nodes[(r["window_start"], r["cloaked_node"])]) for r in rs]
        te, tr = tadv.track(log_em, true_seq)
        if te is not None:
            t_err.append(te)
            t_reid.append(tr)
    t = ({"trajectory_adv_error_m": float(np.mean(t_err)),
          "trajectory_reid_rate": float(np.mean(t_reid)),
          "n_tracked_users": len(t_err)} if t_err else {})
    return {**(s or {}), **t}


def _hybrid_scale(mech, data, default_scale):
    """Laplace scale actually used for a hybrid fallback report (adaptive eps)."""
    eps = data.get("fallback_epsilon")
    if eps:
        return mech.sensitivity / max(eps, 1e-6)
    return default_scale


def eval_snapshot_hybrid(mech, snapshots, adv, id_to_idx, scale):
    """Attack the DA-Hybrid: dispatch per report by which branch served it."""
    errs, hits = [], []
    for _, snap in snapshots:
        res = mech.anonymize_snapshot(snap)
        user_nodes = defaultdict(list)
        for uid, node in snap.items():
            user_nodes[str(node)].append(uid)
        for uid, data in res.items():
            true_idx = id_to_idx[data["original_node"]]
            if data["mode"] == "kanon":
                region = set(str(n) for n in data["region"])
                anon = [id_to_idx[n] for n in region if n in user_nodes]
                e, h = adv.attack_anonymity_set(anon, true_idx)
            else:  # gcdp fallback (density-adaptive epsilon per report)
                fb_scale = _hybrid_scale(mech, data, scale)
                e, h = adv.attack_projected(id_to_idx[data["cloaked_node"]],
                                            fb_scale, true_idx)
            errs.append(e)
            hits.append(1.0 if h else 0.0)
    return _summ(errs, hits)


def _summ(errs, hits):
    if not errs:
        return None
    errs = np.asarray(errs)
    return {
        "snapshot_adv_error_m": float(np.mean(errs)),
        "snapshot_adv_error_p50_m": float(np.percentile(errs, 50)),
        "snapshot_adv_error_p95_m": float(np.percentile(errs, 95)),
        "snapshot_reid_rate": float(np.mean(hits)),
        "n_reports": int(len(errs)),
        "_errors": errs,   # raw per-report errors (stripped before JSON persist)
    }


# ---------------------------------------------------------------------
# Trajectory-adversary evaluation
# ---------------------------------------------------------------------
def eval_trajectory(mech_kind, obf, snapshots, tadv, id_to_idx, coords,
                    scale=None, min_len=5, max_users=60):
    """
    Track users across the ordered snapshot sequence with a Viterbi decoder.

    mech_kind : "dp" | "projected" | "region"
    Returns aggregate tracking error (m) and per-step re-identification rate.
    """
    # Pre-compute each snapshot's mechanism output once (shared across users).
    per_bucket = []
    for _, snap in snapshots:
        per_bucket.append(obf.anonymize_snapshot(snap))

    # Assemble per-user sequences of (t_index, output).
    user_seq = defaultdict(list)
    for t, res in enumerate(per_bucket):
        for uid, data in res.items():
            user_seq[uid].append((t, data))

    long_users = [u for u, s in user_seq.items() if len(s) >= min_len]
    long_users.sort(key=lambda u: -len(user_seq[u]))
    long_users = long_users[:max_users]

    all_err, all_reid = [], []
    for u in long_users:
        seq = user_seq[u]
        true_seq = [id_to_idx[d["original_node"]] for _, d in seq]
        log_em = []
        for _, d in seq:
            if mech_kind == "dp":
                log_em.append(tadv.emission_dp(d["noisy_coords"], scale))
            elif mech_kind == "projected":
                log_em.append(
                    tadv.emission_projected(id_to_idx[d["cloaked_node"]], scale))
            elif mech_kind == "hybrid":
                if d["mode"] == "kanon":
                    region_nodes = [id_to_idx[str(n)] for n in d["region"]]
                    log_em.append(tadv.emission_anonymity_set(region_nodes))
                else:
                    fb_eps = d.get("fallback_epsilon")
                    sc = (obf.sensitivity / max(fb_eps, 1e-6)) if fb_eps else scale
                    log_em.append(
                        tadv.emission_projected(id_to_idx[d["cloaked_node"]], sc))
            else:  # region
                region_nodes = [id_to_idx[str(n)] for n in d["region"]]
                log_em.append(tadv.emission_anonymity_set(region_nodes))
        terr, treid = tadv.track(log_em, true_seq)
        if terr is not None:
            all_err.append(terr)
            all_reid.append(treid)
    if not all_err:
        return None
    return {
        "trajectory_adv_error_m": float(np.mean(all_err)),
        "trajectory_reid_rate": float(np.mean(all_reid)),
        "n_tracked_users": int(len(all_err)),
    }


# ---------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------
def run(quick=False):
    os.makedirs(_OUT, exist_ok=True)

    n_snap = 8 if quick else 60
    n_traj = 12 if quick else 40
    max_rows = 1_500_000 if quick else None

    print("Loading graph + adversary toolkit...")
    node_ids, id_to_idx, coords = load_node_index(NODES_FILE)
    with open(NODES_FILE) as f:
        nodes_json = json.load(f)
    with open(EDGES_FILE) as f:
        edges_json = json.load(f)

    tk = attacker_models.build_adversary_toolkit(
        NODES_FILE, EDGES_FILE, CSV_FILE, cache_tag="geolife")
    sadv = tk["snapshot_adversary"]
    tadv = tk["trajectory_adversary"]

    print(f"Building window snapshots (w={WINDOW}s)...")
    ordered = build_window_snapshots(WINDOW, max_rows=max_rows)
    print(f"  {len(ordered)} multi-user buckets")
    snaps = sample_snapshots(ordered, n_snap)
    traj_snaps = ordered[:n_traj] if len(ordered) >= n_traj else ordered
    print(f"  snapshot-adv uses {len(snaps)}; trajectory-adv uses {len(traj_snaps)}")

    # Import mechanism classes.
    from k_anonymity import GraphKAnonymizer
    from differential_privacy import DPLocationObfuscator
    from graph_constrained_dp import GraphConstrainedDPObfuscator
    from density_aware_k_anonymity import DensityAwareKAnonymizer
    from adaptive_hybrid import AdaptiveHybridAnonymizer

    # Shared distance cache (node-id keyed) for graph mechanisms.
    print("Precomputing shared distance cache for graph mechanisms...")
    ka_seed = GraphKAnonymizer(nodes_json, edges_json, k=2)
    dist_cache = ka_seed.get_dist_cache()

    records = {}   # algo_key -> config_key -> metrics

    # ---- k-Anonymity (snapshot + trajectory) ----
    print("\n[k-anonymity]")
    for k in ([3] if quick else [2, 3, 4, 5, 6]):
        km = GraphKAnonymizer(nodes_json, edges_json, k=k, dist_cache=dist_cache)
        s = eval_snapshot_region(km, snaps, sadv, id_to_idx)
        t = eval_trajectory("region", km, traj_snaps, tadv, id_to_idx, coords,
                            max_users=n_traj)
        records.setdefault("k_anonymity", {})[f"k{k}_w{WINDOW}"] = {**(s or {}), **(t or {})}
        print(f"  k={k}: snap_AE={s and s['snapshot_adv_error_m']:.0f}m "
              f"traj_AE={t and t['trajectory_adv_error_m']:.0f}m")

    # ---- Differential Privacy ----
    print("\n[differential privacy]")
    for eps in ([1.0] if quick else [0.1, 0.5, 1.0, 2.0, 5.0]):
        dp = DPLocationObfuscator(nodes_json, edges_json, epsilon=eps)
        scale = dp.sensitivity / eps
        s = eval_snapshot_dp(dp, snaps, sadv, id_to_idx, coords, scale)
        t = eval_trajectory("dp", dp, traj_snaps, tadv, id_to_idx, coords,
                            scale=scale, max_users=n_traj)
        records.setdefault("differential_privacy", {})[f"eps{eps}_w{WINDOW}"] = {**(s or {}), **(t or {})}
        print(f"  eps={eps}: snap_AE={s and s['snapshot_adv_error_m']:.0f}m "
              f"traj_AE={t and t['trajectory_adv_error_m']:.0f}m")

    # ---- Graph-Constrained DP ----
    print("\n[graph-constrained DP]")
    for eps in ([1.0] if quick else [0.1, 0.5, 1.0, 2.0, 5.0]):
        gc = GraphConstrainedDPObfuscator(nodes_json, edges_json, epsilon=eps,
                                          dist_cache=dist_cache)
        scale = gc.sensitivity / eps
        s = eval_snapshot_projected(gc, snaps, sadv, id_to_idx, coords, scale)
        t = eval_trajectory("projected", gc, traj_snaps, tadv, id_to_idx, coords,
                            scale=scale, max_users=n_traj)
        records.setdefault("graph_constrained_dp", {})[f"eps{eps}_w{WINDOW}"] = {**(s or {}), **(t or {})}
        print(f"  eps={eps}: snap_AE={s and s['snapshot_adv_error_m']:.0f}m "
              f"traj_AE={t and t['trajectory_adv_error_m']:.0f}m")

    # ---- Density-Aware k-Anonymity ----
    print("\n[density-aware k-anonymity]")
    da = DensityAwareKAnonymizer(nodes_json, edges_json, dist_cache=dist_cache)
    s = eval_snapshot_region(da, snaps, sadv, id_to_idx)
    t = eval_trajectory("region", da, traj_snaps, tadv, id_to_idx, coords,
                        max_users=n_traj)
    records.setdefault("density_aware_k_anonymity", {})[f"w{WINDOW}"] = {**(s or {}), **(t or {})}
    print(f"  snap_AE={s and s['snapshot_adv_error_m']:.0f}m "
          f"traj_AE={t and t['trajectory_adv_error_m']:.0f}m")

    # ---- DA-Hybrid (ours) ----
    print("\n[DA-Hybrid (ours)]")
    for k in ([2] if quick else [2, 3, 4, 5]):
        hy = AdaptiveHybridAnonymizer(nodes_json, edges_json, k=k, epsilon=1.0,
                                      dist_cache=dist_cache)
        scale = hy.sensitivity / hy.epsilon
        s = eval_snapshot_hybrid(hy, snaps, sadv, id_to_idx, scale)
        t = eval_trajectory("hybrid", hy, traj_snaps, tadv, id_to_idx, coords,
                            scale=scale, max_users=n_traj)
        records.setdefault("adaptive_hybrid", {})[f"k{k}_w{WINDOW}"] = {**(s or {}), **(t or {})}
        print(f"  k={k}: snap_AE={s and s['snapshot_adv_error_m']:.0f}m "
              f"traj_AE={t and t['trajectory_adv_error_m']:.0f}m")

    # ---- Temporal Cloaking (trajectory-defending mechanism) ----
    print("\n[temporal cloaking]")
    from temporal_cloaking import TemporalCloaker
    trajs = build_trajectories(WINDOW, max_users=(30 if quick else 250),
                               max_rows=max_rows)
    tc = TemporalCloaker(nodes_json, edges_json, k=3, window_sec=WINDOW)
    tcm = eval_temporal(tc, trajs, sadv, tadv, id_to_idx)
    if tcm:
        records.setdefault("temporal_cloaking", {})[f"k3_w{WINDOW}"] = tcm
        print(f"  snap_AE={tcm.get('snapshot_adv_error_m', float('nan')):.0f}m "
              f"traj_AE={tcm.get('trajectory_adv_error_m', float('nan')):.0f}m")

    # Persist per-algo adversary.json + combined table.
    for algo, cfgs in records.items():
        d = os.path.join(_RESULTS, algo)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "adversary.json"), "w") as f:
            json.dump(cfgs, f, indent=2)

    _write_report(records)
    print(f"\nDone. Adversary metrics -> results/<algo>/adversary.json and {_OUT}")
    return records


def _write_report(records):
    rep_names = {
        "k_anonymity": ("k-Anonymity", "k3_w600"),
        "differential_privacy": ("Differential Privacy", "eps1.0_w600"),
        "graph_constrained_dp": ("Graph-Constrained DP", "eps1.0_w600"),
        "density_aware_k_anonymity": ("Density-Aware k-Anon", "w600"),
        "temporal_cloaking": ("Temporal Cloaking", "k3_w600"),
        "adaptive_hybrid": ("DA-Hybrid (ours)", "k2_w600"),
    }
    lines = ["# Adversary-Grounded Privacy Evaluation\n\n",
             "Privacy = expected error (metres) of an optimal Bayesian adversary "
             "(Shokri et al., IEEE S&P 2011). Higher error = stronger privacy. "
             "Each mechanism is attacked by a single-observation **snapshot** "
             "adversary and a Viterbi **trajectory** adversary using a Markov "
             "mobility prior.\n\n",
             "| Mechanism | Snapshot AE (m) | Snapshot re-id | Trajectory AE (m) | Trajectory re-id |\n",
             "|-----------|:---------------:|:--------------:|:-----------------:|:----------------:|\n"]
    for algo, (name, rep) in rep_names.items():
        if algo not in records:
            continue
        m = records[algo].get(rep) or next(iter(records[algo].values()))
        lines.append(
            f"| {name} "
            f"| {m.get('snapshot_adv_error_m', float('nan')):.0f} "
            f"| {m.get('snapshot_reid_rate', float('nan')):.1%} "
            f"| {m.get('trajectory_adv_error_m', float('nan')):.0f} "
            f"| {m.get('trajectory_reid_rate', float('nan')):.1%} |\n")
    with open(os.path.join(_OUT, "adversarial_report.md"), "w") as f:
        f.writelines(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    run(quick=args.quick)
