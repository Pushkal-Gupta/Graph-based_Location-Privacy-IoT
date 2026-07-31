"""
Real-Topology Re-run: do the mechanism rankings hold on a real road network?
============================================================================

Reviewer critique addressed (D): results were on a 30x30 regular grid, not a
real road network.  This script re-runs every mechanism (representative configs,
window = 10 min) on the REAL central-Beijing OSM drive graph produced by
build_real_graph.py, with GeoLife GPS map-matched to that graph
(process_geolife_real.py).  It reports the same four axes as the grid comparison
-- snapshot adversary error, trajectory adversary error, availability, and
location error -- so rankings can be compared directly.

A single dense distance matrix (shared by every mechanism AND the adversary via
MatrixDistCache) keeps the exact Bayesian adversary tractable on the ~3k-node
real graph.

Output: evaluation/real_graph/{table_real.md,table_real.csv,real_metrics.json}
"""

import os
import sys
import csv
import json
import numpy as np
from datetime import datetime
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_BASE = os.path.join(_HERE, "..")
_PROC = os.path.join(_BASE, "data", "processed_data")
_OUT = os.path.join(_HERE, "real_graph")
os.makedirs(_OUT, exist_ok=True)

NODES_FILE = os.path.join(_PROC, "real_graph_nodes.json")
EDGES_FILE = os.path.join(_PROC, "real_graph_edges.json")
CSV_FILE = os.path.join(_PROC, "device_locations_real.csv")

for sub in ["k_anonymity", "differential_privacy", "graph_constrained_dp",
            "density-aware_k-anonymity", "temporal_cloaking", "adaptive_hybrid"]:
    sys.path.insert(0, os.path.join(_BASE, "algorithms", sub))
sys.path.insert(0, _HERE)

import attacker_models as AM
from adversary_priors import load_node_index, estimate_prior_and_transitions
from run_adversarial import (eval_snapshot_region, eval_snapshot_dp,
                             eval_snapshot_projected, eval_snapshot_hybrid,
                             eval_trajectory, eval_temporal)

WINDOW = 600


def build_snapshots(window=WINDOW, max_rows=None, csv_file=CSV_FILE):
    buckets = defaultdict(dict)
    with open(csv_file) as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            if max_rows and i >= max_rows:
                break
            ts = datetime.strptime(f"{row['date']} {row['time']}",
                                   "%Y-%m-%d %H:%M:%S")
            buckets[int(ts.timestamp()) // window][row["user_id"]] = str(row["location_id"])
    ordered = [(b, buckets[b]) for b in sorted(buckets) if len(buckets[b]) >= 2]
    return ordered


def _build_trajectories(max_users=200, max_rows=None, csv_file=CSV_FILE):
    trajs = defaultdict(list)
    with open(csv_file) as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            if max_rows and i >= max_rows:
                break
            ts = datetime.strptime(f"{row['date']} {row['time']}",
                                   "%Y-%m-%d %H:%M:%S")
            trajs[row["user_id"]].append((str(row["location_id"]), ts))
    users = sorted(trajs, key=lambda u: -len(trajs[u]))[:max_users]
    return {u: sorted(trajs[u], key=lambda x: x[1]) for u in users}


def std_metrics(mech, snapshots, kind, k=None):
    """avg location error (m) and availability (served-with-guarantee fraction)."""
    errs, served, tot = [], 0, 0
    for _, snap in snapshots:
        res = mech.anonymize_snapshot(snap)
        for uid, d in res.items():
            tot += 1
            if "location_error" in d:
                errs.append(d["location_error"])
            else:
                errs.append(mech.dist_cache[d["original_node"]][d["cloaked_node"]])
            if kind in ("dp", "projected", "hybrid"):
                served += 1
            else:
                kk = d.get("adaptive_k", k or 3)
                if d.get("k_achieved", 0) >= kk:
                    served += 1
    if tot == 0:
        return float("nan"), float("nan")
    return float(np.mean(errs)), served / tot


def run(quick=False, csv_file=CSV_FILE, cache_tag="geolife_real",
        out_dir=_OUT, label="GeoLife", nodes_file=NODES_FILE, edges_file=EDGES_FILE):
    os.makedirs(out_dir, exist_ok=True)
    n_snap = 8 if quick else 50
    n_traj = 10 if quick else 40
    max_rows = 1_000_000 if quick else None

    print(f"[{label}] Loading real graph + building shared distance matrix...")
    node_ids, id_to_idx, coords = load_node_index(nodes_file)
    with open(nodes_file) as f:
        nodes_json = json.load(f)
    with open(edges_file) as f:
        edges_json = json.load(f)
    D = AM.build_graph_distance_matrix(nodes_file, edges_file, id_to_idx).astype(np.float32)
    print(f"  {len(node_ids)} nodes, distance matrix {D.shape} ({D.nbytes/1e6:.0f} MB)")

    prior, T = estimate_prior_and_transitions(csv_file, node_ids, id_to_idx,
                                              cache_tag=cache_tag)
    sadv = AM.SnapshotAdversary(prior, coords, D)
    tadv = AM.TrajectoryAdversary(prior, coords, D, T)
    cache = AM.MatrixDistCache(D, node_ids)

    ordered = build_snapshots(WINDOW, max_rows=max_rows, csv_file=csv_file)
    print(f"  {len(ordered)} multi-user buckets")
    step = max(1, len(ordered) // n_snap)
    snaps = ordered[::step][:n_snap]
    traj_snaps = ordered[:n_traj]

    from k_anonymity import GraphKAnonymizer
    from differential_privacy import DPLocationObfuscator
    from graph_constrained_dp import GraphConstrainedDPObfuscator
    from density_aware_k_anonymity import DensityAwareKAnonymizer
    from adaptive_hybrid import AdaptiveHybridAnonymizer

    rows = {}

    def record(algo, name, err, avail, s, t):
        rows[algo] = {"name": name, "error": err, "avail": avail,
                      "snap_AE": (s or {}).get("snapshot_adv_error_m", float("nan")),
                      "traj_AE": (t or {}).get("trajectory_adv_error_m", float("nan"))}
        print(f"  {name:22s} err={err:6.0f} avail={avail:5.0%} "
              f"snapAE={rows[algo]['snap_AE']:6.0f} trajAE={rows[algo]['traj_AE']:6.0f}")

    print("\n[k-anonymity k=3]")
    km = GraphKAnonymizer(nodes_json, edges_json, k=3, dist_cache=cache)
    err, av = std_metrics(km, snaps, "region", k=3)
    s = eval_snapshot_region(km, snaps, sadv, id_to_idx)
    t = eval_trajectory("region", km, traj_snaps, tadv, id_to_idx, coords, max_users=n_traj)
    record("k_anonymity", "k-Anonymity", err, av, s, t)

    print("[differential privacy eps=1]")
    dp = DPLocationObfuscator(nodes_json, edges_json, epsilon=1.0)
    scale = dp.sensitivity / 1.0
    err, av = std_metrics(dp, snaps, "dp")
    s = eval_snapshot_dp(dp, snaps, sadv, id_to_idx, coords, scale)
    t = eval_trajectory("dp", dp, traj_snaps, tadv, id_to_idx, coords, scale=scale, max_users=n_traj)
    record("differential_privacy", "Differential Privacy", err, av, s, t)

    print("[graph-constrained DP eps=1]")
    gc = GraphConstrainedDPObfuscator(nodes_json, edges_json, epsilon=1.0, dist_cache=cache)
    scale = gc.sensitivity / 1.0
    err, av = std_metrics(gc, snaps, "projected")
    s = eval_snapshot_projected(gc, snaps, sadv, id_to_idx, coords, scale)
    t = eval_trajectory("projected", gc, traj_snaps, tadv, id_to_idx, coords, scale=scale, max_users=n_traj)
    record("graph_constrained_dp", "Graph-Constrained DP", err, av, s, t)

    print("[density-aware k-anon]")
    da = DensityAwareKAnonymizer(nodes_json, edges_json, dist_cache=cache)
    err, av = std_metrics(da, snaps, "region")
    s = eval_snapshot_region(da, snaps, sadv, id_to_idx)
    t = eval_trajectory("region", da, traj_snaps, tadv, id_to_idx, coords, max_users=n_traj)
    record("density_aware_k_anonymity", "Density-Aware k-Anon", err, av, s, t)

    print("[DA-Hybrid k=2]")
    hy = AdaptiveHybridAnonymizer(nodes_json, edges_json, k=2, epsilon=1.0, dist_cache=cache)
    err, av = std_metrics(hy, snaps, "hybrid")
    s = eval_snapshot_hybrid(hy, snaps, sadv, id_to_idx, hy.sensitivity / hy.epsilon)
    t = eval_trajectory("hybrid", hy, traj_snaps, tadv, id_to_idx, coords,
                        scale=hy.sensitivity / hy.epsilon, max_users=n_traj)
    record("adaptive_hybrid", "DA-Hybrid (ours)", err, av, s, t)

    print("[MIRAGE dmax=800]")
    sys.path.insert(0, os.path.join(_BASE, "algorithms", "mirage"))
    from mirage import MirageMechanism
    mir = MirageMechanism(node_ids, D, prior, dmax=800, cand_size=28)
    mir.precompute(verbose=False,
                   cache_path=os.path.join(_HERE, "cache", f"mirage_main_{label}.json"))
    rev = defaultdict(list)
    for vv, (cand, probs) in mir.mech.items():
        for oo, pp in zip(cand, probs):
            if pp > 0:
                rev[int(oo)].append((vv, float(pp)))
    # snapshot adversary + utility
    m_err, m_util, m_hit = [], [], []
    for _, snap in snaps:
        for uid, node in snap.items():
            v = id_to_idx[str(node)]; o = mir.sample(v)
            m_util.append(float(D[v, o]))
            srcs = rev.get(o, [(v, 1.0)])
            e, h = sadv.attack_distribution([s[0] for s in srcs],
                                            [s[1] for s in srcs], v)
            m_err.append(e); m_hit.append(1.0 if h else 0.0)
    m_s = {"snapshot_adv_error_m": float(np.mean(m_err)),
           "snapshot_reid_rate": float(np.mean(m_hit))}
    # trajectory adversary (Viterbi with MIRAGE's known emission f(o|v))
    Nn = len(node_ids)
    seqs = defaultdict(list)
    for t, (_, snap) in enumerate(traj_snaps):
        for uid, node in snap.items():
            v = id_to_idx[str(node)]; seqs[uid].append((v, mir.sample(v)))
    long_u = sorted([u for u, s in seqs.items() if len(s) >= 5],
                    key=lambda u: -len(seqs[u]))[:n_traj]
    t_err = []
    for u in long_u:
        vs = [x[0] for x in seqs[u]]; os_ = [x[1] for x in seqs[u]]
        log_em = []
        for o in os_:
            e = np.full(Nn, -12.0)
            for vv, pp in rev.get(o, [(o, 1.0)]):
                e[vv] = np.log(pp + 1e-9)
            log_em.append(e)
        te, _ = tadv.track(log_em, vs)
        if te is not None:
            t_err.append(te)
    m_t = {"trajectory_adv_error_m": float(np.mean(t_err)) if t_err else float("nan")}
    record("mirage", "MIRAGE (ours)", float(np.mean(m_util)), 1.0, m_s, m_t)

    print("[temporal cloaking k=3]")
    from temporal_cloaking import TemporalCloaker
    trajs = _build_trajectories(max_users=(30 if quick else 200),
                                max_rows=max_rows, csv_file=csv_file)
    tc = TemporalCloaker(nodes_json, edges_json, k=3, window_sec=WINDOW)
    tcm = eval_temporal(tc, trajs, sadv, tadv, id_to_idx)
    if tcm:
        # error + availability from temporal records.
        recs = tc.cloak_trajectories(trajs)
        errs = [r["location_error"] for r in recs]
        n_served = len(set(r["user"] for r in recs))
        n_total = len(trajs)
        record("temporal_cloaking", "Temporal Cloaking",
               float(np.mean(errs)) if errs else float("nan"),
               (n_served / n_total) if n_total else float("nan"),
               tcm, tcm)

    with open(os.path.join(out_dir, "real_metrics.json"), "w") as f:
        json.dump(rows, f, indent=2)
    _write_table(rows, out_dir, label)
    print(f"\n[{label}] real-graph metrics -> {out_dir}")
    return rows


def _write_table(rows, out_dir=_OUT, label="GeoLife"):
    lines = [f"# Real-Topology Comparison ({label}, central-Beijing OSM graph, ~3.1k nodes)\n\n",
             f"Representative configs, window = 10 min, {label} map-matched to the "
             "real road network. Privacy = Bayesian-adversary error (m, higher = "
             "more private).\n\n",
             "| Mechanism | Snapshot AE (m) | Trajectory AE (m) | Availability | Loc. Error (m) |\n",
             "|---|---|---|---|---|\n"]
    for algo, r in rows.items():
        lines.append(f"| {r['name']} | {r['snap_AE']:.0f} | {r['traj_AE']:.0f} "
                     f"| {r['avail']:.1%} | {r['error']:.0f} |\n")
    with open(os.path.join(out_dir, "table_real.md"), "w") as f:
        f.writelines(lines)
    with open(os.path.join(out_dir, "table_real.csv"), "w") as f:
        f.write("mechanism,snapshot_AE_m,trajectory_AE_m,availability,location_error_m\n")
        for algo, r in rows.items():
            f.write(f"{r['name']},{r['snap_AE']:.1f},{r['traj_AE']:.1f},"
                    f"{r['avail']:.4f},{r['error']:.1f}\n")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--dataset", choices=["geolife", "tdrive", "porto"], default="geolife")
    args = ap.parse_args()
    if args.dataset == "tdrive":
        run(quick=args.quick,
            csv_file=os.path.join(_PROC, "device_locations_tdrive.csv"),
            cache_tag="tdrive_real",
            out_dir=os.path.join(_HERE, "real_graph_tdrive"),
            label="T-Drive")
    elif args.dataset == "porto":
        run(quick=args.quick,
            csv_file=os.path.join(_PROC, "device_locations_porto.csv"),
            cache_tag="porto_real",
            out_dir=os.path.join(_HERE, "real_graph_porto"),
            label="Porto",
            nodes_file=os.path.join(_PROC, "porto_graph_nodes.json"),
            edges_file=os.path.join(_PROC, "porto_graph_edges.json"))
    else:
        run(quick=args.quick)
