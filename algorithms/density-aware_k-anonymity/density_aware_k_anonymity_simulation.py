"""
Evaluation of Density-Aware Adaptive k-Anonymity on GeoLife
=============================================================

Evaluates density-aware adaptive k-anonymity across temporal window
sizes.  The adaptive k is selected per-user based on local density,
so the primary sweep is over time windows (density thresholds are
computed automatically from each snapshot).

Dataset: Zheng et al. (2009), GeoLife GPS Trajectories.
Algorithm: See density_aware_k_anonymity.py for full citations.
Evaluation: Gedik & Liu (2008).
"""

import os
import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

from density_aware_k_anonymity import DensityAwareKAnonymizer


# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
_HERE       = os.path.dirname(os.path.abspath(__file__))
BASE        = os.path.join(_HERE, "..", "..")
DATA_DIR    = os.path.join(BASE, "data", "processed_data")
RESULT_DIR  = os.path.join(BASE, "results", "density_aware_k_anonymity")
FIGURE_DIR  = os.path.join(RESULT_DIR, "figures")

TRAJ_INDEX  = os.path.join(DATA_DIR, "device_locations_indexed.jsonl")
NODES_FILE  = os.path.join(DATA_DIR, "city_graph_nodes.json")
EDGES_FILE  = os.path.join(DATA_DIR, "city_graph_edges.json")

TIME_WINDOWS  = [60, 300, 600, 1200]
MAX_SNAPSHOTS = 300

WINDOW_LABELS = {60: "1 min", 300: "5 min", 600: "10 min", 1200: "20 min"}
COLORS        = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

plt.rcParams.update({
    "font.family": "serif", "font.size": 11, "axes.titlesize": 12,
    "axes.labelsize": 11, "legend.fontsize": 10, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "savefig.dpi": 300, "savefig.bbox": "tight",
})


# -----------------------------------------------------------------------
# Data loading (JSONL)
# -----------------------------------------------------------------------
def load_graph_data():
    with open(NODES_FILE) as f:
        nodes = json.load(f)
    with open(EDGES_FILE) as f:
        edges = json.load(f)
    return nodes, edges


def build_all_buckets():
    print("Building time-bucket index (single pass through JSONL)...")
    all_buckets = {w: defaultdict(dict) for w in TIME_WINDOWS}
    with open(TRAJ_INDEX) as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            user, node = row["user"], row["node"]
            for w in TIME_WINDOWS:
                all_buckets[w][row[f"t{w}"]][user] = node
            if i % 2_000_000 == 0 and i > 0:
                print(f"  {i:,} records processed")
    result = {}
    for w in TIME_WINDOWS:
        buckets = {b: dict(users) for b, users in all_buckets[w].items()}
        multi = sum(1 for u in buckets.values() if len(u) >= 2)
        print(f"  Window {WINDOW_LABELS[w]}: {len(buckets):,} buckets, "
              f"{multi:,} with >= 2 users")
        result[w] = buckets
    print("Index ready.\n")
    return result


def get_snapshots(all_buckets, window, min_users=2):
    buckets = all_buckets[window]
    candidates = sorted(
        (s for s in buckets.values() if len(s) >= min_users), key=id)
    if len(candidates) > MAX_SNAPSHOTS:
        step = len(candidates) // MAX_SNAPSHOTS
        candidates = candidates[::step][:MAX_SNAPSHOTS]
    return candidates


# -----------------------------------------------------------------------
# Core evaluation
# -----------------------------------------------------------------------
def evaluate_all(nodes_json, edges_json, all_buckets):
    print("Loading graph and computing all-pairs distances (once)...")
    base = DensityAwareKAnonymizer(nodes_json, edges_json)
    dist_cache = base.get_dist_cache()
    print(f"Graph: {len(base.graph)} nodes, distances cached.\n")

    results = {}

    for window in TIME_WINDOWS:
        print(f"--- Time window: {WINDOW_LABELS[window]} ---")
        snapshots = get_snapshots(all_buckets, window, min_users=2)
        print(f"  Snapshots to evaluate: {len(snapshots)}")
        if not snapshots:
            continue

        anon = DensityAwareKAnonymizer(
            nodes_json, edges_json, dist_cache=dist_cache)

        errors, region_sizes, temporal_jumps = [], [], []
        adaptive_ks, densities = [], []
        density_levels = {"Sparse": 0, "Medium": 0, "Dense": 0}
        k_satisfied, total = 0, 0
        last_cloaked = {}

        for snap in snapshots:
            if len(snap) < 2:
                continue
            res = anon.anonymize_snapshot(snap)

            for uid, data in res.items():
                orig  = data["original_node"]
                cloak = data["cloaked_node"]

                d = anon.dist(orig, cloak)
                errors.append(d)
                region_sizes.append(len(data["region"]))
                adaptive_ks.append(data["adaptive_k"])
                densities.append(data["density"])
                density_levels[data["density_level"]] += 1

                if data["k_achieved"] >= data["adaptive_k"]:
                    k_satisfied += 1

                if uid in last_cloaked:
                    temporal_jumps.append(
                        anon.dist(last_cloaked[uid], cloak))
                last_cloaked[uid] = cloak
                total += 1

        if total == 0:
            continue

        errors.sort()
        entry = {
            "window_sec":          window,
            "window_label":        WINDOW_LABELS[window],
            "n_records":           total,
            "avg_location_error":  float(np.mean(errors)),
            "std_location_error":  float(np.std(errors)),
            "p50_location_error":  float(np.percentile(errors, 50)),
            "p95_location_error":  float(np.percentile(errors, 95)),
            "avg_region_size":     float(np.mean(region_sizes)),
            "std_region_size":     float(np.std(region_sizes)),
            "avg_adaptive_k":      float(np.mean(adaptive_ks)),
            "avg_density":         float(np.mean(densities)),
            "density_distribution": dict(density_levels),
            "avg_temporal_jump":   float(np.mean(temporal_jumps))
                                   if temporal_jumps else 0.0,
            "k_satisfaction_rate": k_satisfied / total,
            "_error_samples":      errors[::max(1, len(errors) // 500)],
            "_adaptive_ks":        adaptive_ks[::max(1, len(adaptive_ks) // 500)],
            "_densities":          densities[::max(1, len(densities) // 500)],
        }
        results[window] = entry
        print(f"  err={entry['avg_location_error']:.0f} m  "
              f"avg_k={entry['avg_adaptive_k']:.1f}  "
              f"region={entry['avg_region_size']:.1f}  "
              f"k-sat={entry['k_satisfaction_rate']*100:.0f}%")
        print()

    return results


# -----------------------------------------------------------------------
# Figure 1 -- Spatial Cloaking Visualisation
# -----------------------------------------------------------------------
def fig_spatial(nodes_json, edges_json, dist_cache, all_buckets, window=300):
    print("  Generating Fig 1: spatial visualisation...")
    anon = DensityAwareKAnonymizer(
        nodes_json, edges_json, dist_cache=dist_cache)
    coords = anon.node_coords

    snap = None
    for c in get_snapshots(all_buckets, window, min_users=4):
        if len(c) >= 4:
            snap = dict(list(c.items())[:30])
            break
    if snap is None:
        print("  Skipping Fig 1."); return

    result = anon.anonymize_snapshot(snap)
    tracked = list(result.keys())[0]

    active = {str(n) for n in snap.values()} | \
             {n for d in result.values() for n in d["region"]}
    with open(EDGES_FILE) as f:
        edges_raw = json.load(f)
    elines = [(str(e["source"]), str(e["target"])) for e in edges_raw
              if str(e["source"]) in active or str(e["target"]) in active]

    def bg(ax):
        ax.set_facecolor("#1a1a2e")
        for s, t in elines:
            if s in coords and t in coords:
                ax.plot([coords[s][0], coords[t][0]],
                        [coords[s][1], coords[t][1]],
                        color="#3a3a5e", lw=0.7, alpha=0.8, zorder=1)
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]; bg(ax)
    LEVEL_COLORS = {"Sparse": "#ff4444", "Medium": "#ffaa00", "Dense": "#00cc66"}
    for uid, node in snap.items():
        n = str(node)
        if n not in coords: continue
        level = result[uid]["density_level"]
        ax.scatter(coords[n][0], coords[n][1], s=60,
                   c=LEVEL_COLORS[level], zorder=4,
                   edgecolors="white", linewidths=0.5)
    ax.set_title("(a)  True Locations — Coloured by Density", fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color=c, label=l) for l, c in LEVEL_COLORS.items()
    ], loc="best", framealpha=0.8)

    ax = axes[1]; bg(ax)
    PAD = 0.0008
    for uid, data in result.items():
        region = [n for n in data["region"] if n in coords]
        cn = data["cloaked_node"]
        if len(region) >= 2:
            rxs = [coords[n][0] for n in region]
            rys = [coords[n][1] for n in region]
            rect = mpatches.FancyBboxPatch(
                (min(rxs) - PAD, min(rys) - PAD),
                max(rxs) - min(rxs) + 2 * PAD,
                max(rys) - min(rys) + 2 * PAD,
                boxstyle="round,pad=0.0003", linewidth=0.6,
                edgecolor="#ffaa00", facecolor="#ffaa00", alpha=0.18, zorder=3)
            ax.add_patch(rect)
        if cn in coords:
            c = "#ff4444" if uid == tracked else "#ffff66"
            ax.scatter(coords[cn][0], coords[cn][1], marker="*",
                       s=180 if uid == tracked else 70, c=c,
                       zorder=5, edgecolors="black", linewidths=0.4)
    ax.set_title("(b)  Density-Aware Adaptive Cloaking", fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color="#ffaa00", alpha=0.4, label="Cloaking region"),
        plt.Line2D([0], [0], marker="*", color="w",
                   markerfacecolor="#ffff66", markersize=11,
                   label="Cloaked location"),
    ], loc="best", framealpha=0.8)

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "fig1_spatial_density_aware.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 2 -- Error vs Time Window  (grouped by density level)
# -----------------------------------------------------------------------
def fig_error_vs_window(results):
    print("  Generating Fig 2: error vs time window...")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ws = sorted(w for w in results.keys())
    labels = [WINDOW_LABELS[w] for w in ws]
    means = [results[w]["avg_location_error"] for w in ws]
    stds  = [results[w]["std_location_error"] for w in ws]
    x = np.arange(len(ws))
    ax.bar(x, means, yerr=stds, color=COLORS[0], alpha=0.8,
           capsize=4, label="Avg ± Std")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_xlabel("Time Window (Δt)")
    ax.set_ylabel("Location Error (metres)")
    ax.set_title("Location Error vs Time Window  [Density-Aware k-Anonymity]")
    ax.legend(); ax.grid(True, alpha=0.35, axis="y")
    path = os.path.join(FIGURE_DIR, "fig2_error_vs_window.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 3 -- Adaptive k Distribution
# -----------------------------------------------------------------------
def fig_adaptive_k_dist(results):
    print("  Generating Fig 3: adaptive k distribution...")
    fig, axes = plt.subplots(1, len(results), figsize=(4 * len(results), 4),
                              squeeze=False)
    for idx, (w, r) in enumerate(sorted(results.items())):
        ax = axes[0][idx]
        ks = r["_adaptive_ks"]
        bins = sorted(set(ks))
        ax.hist(ks, bins=[b - 0.5 for b in bins] + [max(bins) + 0.5],
                color=COLORS[idx % len(COLORS)], alpha=0.8, edgecolor="black")
        ax.set_xlabel("Adaptive k")
        ax.set_ylabel("Frequency")
        ax.set_title(f"Δt = {WINDOW_LABELS[w]}")
        ax.grid(True, alpha=0.35, axis="y")
    plt.suptitle("Distribution of Adaptive k  [Density-Aware Selection]",
                 fontweight="bold", y=1.02)
    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "fig3_adaptive_k_distribution.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 4 -- Privacy-Utility Tradeoff
# -----------------------------------------------------------------------
def fig_privacy_utility(results):
    print("  Generating Fig 4: privacy-utility tradeoff...")
    fig, ax = plt.subplots(figsize=(7, 5))

    for i, (w, r) in enumerate(sorted(results.items())):
        priv = r["avg_region_size"]
        util = 1.0 / (1.0 + r["avg_location_error"])
        ax.scatter(priv, util, s=120, color=COLORS[i], zorder=5,
                   edgecolors="black", linewidths=0.5)
        ax.annotate(f"Δt={WINDOW_LABELS[w]}\navg_k={r['avg_adaptive_k']:.1f}",
                    (priv, util), textcoords="offset points",
                    xytext=(8, 4), fontsize=9, color=COLORS[i])

    ax.set_xlabel("Privacy Gain  (avg cloaking region, nodes)")
    ax.set_ylabel("Utility Score  1/(1 + location error)")
    ax.set_title("Privacy-Utility Tradeoff  [Density-Aware k-Anonymity]")
    ax.grid(True, alpha=0.35)
    path = os.path.join(FIGURE_DIR, "fig4_privacy_utility.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 5 -- CDF of Location Errors
# -----------------------------------------------------------------------
def fig_error_cdf(results):
    print("  Generating Fig 5: CDF of errors...")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, (w, r) in enumerate(sorted(results.items())):
        samp = sorted(r["_error_samples"])
        cdf = np.arange(1, len(samp) + 1) / len(samp)
        ax.plot(samp, cdf, color=COLORS[i], linewidth=2,
                label=f"Δt = {WINDOW_LABELS[w]}")
    ax.set_xlabel("Location Error (metres)")
    ax.set_ylabel("Cumulative Probability")
    ax.set_title("CDF of Location Errors  [Density-Aware k-Anonymity]")
    ax.set_xlim(left=0); ax.set_ylim(0, 1.02)
    ax.legend(); ax.grid(True, alpha=0.35)
    path = os.path.join(FIGURE_DIR, "fig5_error_cdf.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
def _utility_score(r):
    privacy = math.log(r["avg_region_size"] + 1)
    utility = 1.0 / (1.0 + r["avg_location_error"]
                      + 0.5 * r["avg_temporal_jump"])
    return privacy * utility


def write_analysis(results):
    best = max(results.values(), key=_utility_score)
    lines = [
        "# Density-Aware Adaptive k-Anonymity — GeoLife Dataset\n\n",
        "## Metrics per Time Window\n\n",
        "| Δt | Avg Error (m) | Median (m) | P95 (m) |"
        " Avg Region | Avg k | k-Sat | Density Dist |\n",
        "|----|---------------|------------|---------|"
        "------------|-------|-------|-------------|\n",
    ]
    for r in sorted(results.values(), key=lambda x: x["window_sec"]):
        dd = r["density_distribution"]
        dd_str = f"S:{dd['Sparse']} M:{dd['Medium']} D:{dd['Dense']}"
        lines.append(
            f"| {r['window_label']} "
            f"| {r['avg_location_error']:.1f} "
            f"| {r['p50_location_error']:.1f} "
            f"| {r['p95_location_error']:.1f} "
            f"| {r['avg_region_size']:.1f} "
            f"| {r['avg_adaptive_k']:.1f} "
            f"| {r['k_satisfaction_rate']*100:.0f}% "
            f"| {dd_str} |\n")
    lines += [
        f"\n## Best Configuration\n\n",
        f"- **Δt** = {best['window_label']}\n",
        f"- Avg error: {best['avg_location_error']:.1f} m\n",
        f"- Avg adaptive k: {best['avg_adaptive_k']:.1f}\n",
    ]
    with open(os.path.join(RESULT_DIR, "analysis.md"), "w") as f:
        f.writelines(lines)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
def run():
    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs(FIGURE_DIR, exist_ok=True)

    print("Loading graph data...")
    nodes_json, edges_json = load_graph_data()
    print(f"  {len(nodes_json)} nodes, {len(edges_json)} edges\n")

    all_buckets = build_all_buckets()

    print("=== Evaluation ===")
    results = evaluate_all(nodes_json, edges_json, all_buckets)

    if not results:
        print("ERROR: No results produced."); return

    serializable = {
        f"w{r['window_sec']}": {
            k: v for k, v in r.items() if not k.startswith("_")
        } for r in results.values()
    }
    with open(os.path.join(RESULT_DIR, "results.json"), "w") as f:
        json.dump(serializable, f, indent=2)

    best = max(results.values(), key=_utility_score)
    best_save = {k: v for k, v in best.items() if not k.startswith("_")}
    with open(os.path.join(RESULT_DIR, "best_config.json"), "w") as f:
        json.dump(best_save, f, indent=2)

    write_analysis(results)

    print("\n=== Figures ===")
    base = DensityAwareKAnonymizer(nodes_json, edges_json)
    dc = base.get_dist_cache()
    fig_spatial(nodes_json, edges_json, dc, all_buckets, window=300)
    fig_error_vs_window(results)
    fig_adaptive_k_dist(results)
    fig_privacy_utility(results)
    fig_error_cdf(results)

    print(f"\n=== Done ===")
    print(f"Results  -> {RESULT_DIR}")
    print(f"Best: Δt={best['window_label']}, "
          f"err={best['avg_location_error']:.1f} m, "
          f"avg_k={best['avg_adaptive_k']:.1f}")


if __name__ == "__main__":
    run()
