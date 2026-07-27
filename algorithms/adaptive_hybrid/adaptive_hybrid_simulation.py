"""
Evaluation of Density-Adaptive Hybrid Privacy (DA-Hybrid) on GeoLife
====================================================================

Sweeps the hybrid mechanism across (k, time-window) and writes results in the
same schema as the other five mechanisms so it slots directly into the unified
comparison (evaluation/deep_analysis.py) and the adversarial evaluation
(evaluation/run_adversarial.py).

The hybrid's headline property is 100 % availability by construction: every
report is served either by the bounded k-anonymity branch or the graph-
constrained DP fallback.  We record the branch split, k-guarantee rate, and
spatial error so the mechanism can be placed on the privacy--availability--
utility frontier.
"""

import os
import csv
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict

from adaptive_hybrid import AdaptiveHybridAnonymizer, _haversine_m

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(_HERE, "..", "..")
DATA_DIR = os.path.join(BASE, "data", "processed_data")
RESULT_DIR = os.path.join(BASE, "results", "adaptive_hybrid")
FIGURE_DIR = os.path.join(RESULT_DIR, "figures")

CSV_FILE = os.path.join(DATA_DIR, "device_locations.csv")
NODES_FILE = os.path.join(DATA_DIR, "city_graph_nodes.json")
EDGES_FILE = os.path.join(DATA_DIR, "city_graph_edges.json")

TIME_WINDOWS = [60, 300, 600, 1200]
K_VALUES = [2, 3, 4, 5]
EPSILON = 1.0
MAX_SNAPSHOTS = 300
WINDOW_LABELS = {60: "1 min", 300: "5 min", 600: "10 min", 1200: "20 min"}

plt.rcParams.update({"font.family": "serif", "font.size": 11,
                     "savefig.dpi": 300, "savefig.bbox": "tight"})


def load_graph_data():
    with open(NODES_FILE) as f:
        nodes = json.load(f)
    with open(EDGES_FILE) as f:
        edges = json.load(f)
    return nodes, edges


def build_all_buckets():
    print("Building time-bucket index from CSV...")
    all_buckets = {w: defaultdict(dict) for w in TIME_WINDOWS}
    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            user = row["user_id"]
            node = str(row["location_id"])
            ts = datetime.strptime(f"{row['date']} {row['time']}",
                                   "%Y-%m-%d %H:%M:%S")
            epoch = int(ts.timestamp())
            for w in TIME_WINDOWS:
                all_buckets[w][epoch // w][user] = node
            if i % 4_000_000 == 0 and i > 0:
                print(f"  {i:,} records processed")
    result = {}
    for w in TIME_WINDOWS:
        result[w] = {b: dict(u) for b, u in all_buckets[w].items()}
    print("Index ready.\n")
    return result


def get_snapshots(all_buckets, window, min_users=2):
    buckets = all_buckets[window]
    cands = sorted((s for s in buckets.values() if len(s) >= min_users), key=id)
    if len(cands) > MAX_SNAPSHOTS:
        step = len(cands) // MAX_SNAPSHOTS
        cands = cands[::step][:MAX_SNAPSHOTS]
    return cands


def evaluate_all(nodes_json, edges_json, all_buckets, dist_cache):
    results = {}
    for window in TIME_WINDOWS:
        snapshots = get_snapshots(all_buckets, window, min_users=2)
        print(f"--- {WINDOW_LABELS[window]}: {len(snapshots)} snapshots ---")
        if not snapshots:
            continue
        for k in K_VALUES:
            mech = AdaptiveHybridAnonymizer(
                nodes_json, edges_json, k=k, epsilon=EPSILON,
                dist_cache=dist_cache)
            errors, jumps, regions = [], [], []
            n_kanon, n_gcdp, n_ksat = 0, 0, 0
            total = 0
            last_coords = {}
            for snap in snapshots:
                res = mech.anonymize_snapshot(snap)
                for uid, d in res.items():
                    errors.append(d["location_error"])
                    if d["mode"] == "kanon":
                        n_kanon += 1
                        regions.append(len(d["region"]))
                    else:
                        n_gcdp += 1
                    if d["k_satisfied"]:
                        n_ksat += 1
                    cur = d["cloaked_coords"]
                    if uid in last_coords:
                        p = last_coords[uid]
                        jumps.append(_haversine_m(p[0], p[1], cur[0], cur[1]))
                    last_coords[uid] = cur
                    total += 1
            if total == 0:
                continue
            errors.sort()
            entry = {
                "k": k,
                "epsilon": EPSILON,
                "window_sec": window,
                "window_label": WINDOW_LABELS[window],
                "n_records": total,
                "avg_location_error": float(np.mean(errors)),
                "std_location_error": float(np.std(errors)),
                "p50_location_error": float(np.percentile(errors, 50)),
                "p95_location_error": float(np.percentile(errors, 95)),
                "avg_temporal_jump": float(np.mean(jumps)) if jumps else 0.0,
                "avg_region_size": float(np.mean(regions)) if regions else 0.0,
                "k_satisfaction_rate": n_ksat / total,
                "service_rate": 1.0,                       # 100% by construction
                "kanon_fraction": n_kanon / total,
                "gcdp_fraction": n_gcdp / total,
                "_error_samples": errors[::max(1, len(errors) // 500)],
            }
            results[(k, window)] = entry
            print(f"  k={k}: err={entry['avg_location_error']:.0f}m "
                  f"k-sat={entry['k_satisfaction_rate']:.1%} "
                  f"kanon={entry['kanon_fraction']:.0%} "
                  f"gcdp={entry['gcdp_fraction']:.0%}")
    return results


def _utility_score(r):
    # Balance: strong privacy (k), high availability (always 1), low error.
    return (r["k"] / 6.0) * r["service_rate"] / (1.0 + r["avg_location_error"] / 1000.0)


def write_analysis(results):
    if not results:
        return
    best = max(results.values(), key=_utility_score)
    lines = ["# Density-Adaptive Hybrid (DA-Hybrid) — GeoLife\n\n",
             "100% availability by construction; k-anon branch where density "
             "permits, graph-constrained DP fallback otherwise.\n\n",
             "| k | Δt | Avg Err (m) | P95 (m) | k-sat | k-anon% | gcdp% | Region |\n",
             "|---|-----|-------------|---------|-------|---------|-------|--------|\n"]
    for r in sorted(results.values(), key=lambda x: (x["window_sec"], x["k"])):
        lines.append(f"| {r['k']} | {r['window_label']} "
                     f"| {r['avg_location_error']:.0f} | {r['p95_location_error']:.0f} "
                     f"| {r['k_satisfaction_rate']:.1%} | {r['kanon_fraction']:.0%} "
                     f"| {r['gcdp_fraction']:.0%} | {r['avg_region_size']:.0f} |\n")
    lines += [f"\n## Best configuration\n\n- k={best['k']}, Δt={best['window_label']}, "
              f"avg error={best['avg_location_error']:.0f} m, "
              f"availability=100%\n"]
    with open(os.path.join(RESULT_DIR, "analysis.md"), "w") as f:
        f.writelines(lines)


def fig_mode_split(results):
    ks = K_VALUES
    w = 600
    kanon = [results[(k, w)]["kanon_fraction"] for k in ks if (k, w) in results]
    gcdp = [results[(k, w)]["gcdp_fraction"] for k in ks if (k, w) in results]
    xs = [k for k in ks if (k, w) in results]
    if not xs:
        return
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(xs, kanon, label="k-anonymity branch", color="#2ca02c")
    ax.bar(xs, gcdp, bottom=kanon, label="GC-DP fallback", color="#ff7f0e")
    ax.set_xlabel("Target k")
    ax.set_ylabel("Fraction of reports")
    ax.set_title("DA-Hybrid branch split (Δt = 10 min)")
    ax.legend()
    plt.savefig(os.path.join(FIGURE_DIR, "fig1_branch_split.png"))
    plt.close()


def run():
    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs(FIGURE_DIR, exist_ok=True)
    print("Loading graph data...")
    nodes_json, edges_json = load_graph_data()
    print(f"  {len(nodes_json)} nodes, {len(edges_json)} edges\n")

    # Shared distance cache.
    seed = AdaptiveHybridAnonymizer(nodes_json, edges_json, k=2, epsilon=EPSILON)
    dist_cache = seed.get_dist_cache()

    all_buckets = build_all_buckets()
    results = evaluate_all(nodes_json, edges_json, all_buckets, dist_cache)
    if not results:
        print("ERROR: no results.")
        return

    serializable = {
        f"k{r['k']}_w{r['window_sec']}": {k: v for k, v in r.items()
                                          if not k.startswith("_")}
        for r in results.values()
    }
    with open(os.path.join(RESULT_DIR, "results.json"), "w") as f:
        json.dump(serializable, f, indent=2)

    best = max(results.values(), key=_utility_score)
    with open(os.path.join(RESULT_DIR, "best_config.json"), "w") as f:
        json.dump({k: v for k, v in best.items() if not k.startswith("_")},
                  f, indent=2)

    write_analysis(results)
    fig_mode_split(results)
    print(f"\nDone -> {RESULT_DIR}")


if __name__ == "__main__":
    run()
