"""
Evaluation of Temporal Cloaking on the Microsoft GeoLife Dataset
=================================================================

Loads the GeoLife trajectory CSV and evaluates temporal cloaking
across time window sizes and k values.

Dataset: Zheng et al. (2009), GeoLife GPS Trajectories.
Algorithm: See temporal_cloaking.py for full citation list.
Evaluation: Gedik & Liu (2008); Chow & Mokbel (2011).
"""

import os
import csv
import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
from datetime import datetime

from temporal_cloaking import TemporalCloaker


# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
_HERE       = os.path.dirname(os.path.abspath(__file__))
BASE        = os.path.join(_HERE, "..", "..")
DATA_DIR    = os.path.join(BASE, "data", "processed_data")
RESULT_DIR  = os.path.join(BASE, "results", "temporal_cloaking")
FIGURE_DIR  = os.path.join(RESULT_DIR, "figures")

CSV_FILE    = os.path.join(DATA_DIR, "device_locations.csv")
NODES_FILE  = os.path.join(DATA_DIR, "city_graph_nodes.json")
EDGES_FILE  = os.path.join(DATA_DIR, "city_graph_edges.json")

WINDOW_SECS = [300, 600, 900, 1200]       # 5, 10, 15, 20 min
K_VALUES    = [3, 5, 7, 10]
MAX_EVENTS  = 500_000   # cap CSV rows for tractable runtime

WINDOW_LABELS = {300: "5 min", 600: "10 min", 900: "15 min", 1200: "20 min"}
COLORS        = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

plt.rcParams.update({
    "font.family": "serif", "font.size": 11, "axes.titlesize": 12,
    "axes.labelsize": 11, "legend.fontsize": 10, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "savefig.dpi": 300, "savefig.bbox": "tight",
})


# -----------------------------------------------------------------------
# Data loading (CSV with timestamps)
# -----------------------------------------------------------------------
def load_graph_data():
    with open(NODES_FILE) as f:
        nodes = json.load(f)
    with open(EDGES_FILE) as f:
        edges = json.load(f)
    return nodes, edges


def load_trajectories():
    """
    Load device_locations.csv and build trajectory dict.

    CSV schema: user_id, location_id, date, time
    Returns: {user_id: [(node_id, datetime), ...]}  sorted by time.
    """
    print("Loading trajectories from CSV...")
    trajectories = defaultdict(list)
    count = 0

    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = row["user_id"]
            node = str(row["location_id"])
            ts   = datetime.strptime(
                f"{row['date']} {row['time']}", "%Y-%m-%d %H:%M:%S")
            trajectories[user].append((node, ts))
            count += 1
            if count >= MAX_EVENTS:
                break

    # Sort each trajectory by time
    for user in trajectories:
        trajectories[user].sort(key=lambda x: x[1])

    print(f"  {count:,} events loaded, {len(trajectories)} users.\n")
    return dict(trajectories)


# -----------------------------------------------------------------------
# Core evaluation
# -----------------------------------------------------------------------
def evaluate_all(nodes_json, edges_json, trajectories):
    print("Loading graph and computing all-pairs distances (once)...")
    base = TemporalCloaker(nodes_json, edges_json, k=3, window_sec=300)
    dist_cache = base.get_dist_cache()
    print(f"Graph: {len(base.graph)} nodes, distances cached.\n")

    results = {}

    for window_sec in WINDOW_SECS:
        print(f"--- Time window: {WINDOW_LABELS[window_sec]} ---")

        for k in K_VALUES:
            cloaker = TemporalCloaker(
                nodes_json, edges_json, k=k,
                window_sec=window_sec, dist_cache=dist_cache)

            records = cloaker.cloak_trajectories(trajectories)

            if not records:
                print(f"  k={k}: no records produced")
                continue

            errors  = [r["location_error"] for r in records]
            delays  = [r["temporal_delay"] for r in records]
            groups  = [r["group_size"]     for r in records]
            k_sat   = sum(1 for r in records
                          if r["k_achieved"] >= k) / len(records)

            # Temporal jumps: consecutive cloaked nodes per user
            user_seq = defaultdict(list)
            for r in records:
                user_seq[r["user"]].append(r["cloaked_node"])
            temporal_jumps = []
            for user, seq in user_seq.items():
                for i in range(1, len(seq)):
                    temporal_jumps.append(
                        cloaker.dist(seq[i - 1], seq[i]))

            errors.sort()
            entry = {
                "k":                   k,
                "window_sec":          window_sec,
                "window_label":        WINDOW_LABELS[window_sec],
                "n_records":           len(records),
                "avg_location_error":  float(np.mean(errors)),
                "std_location_error":  float(np.std(errors)),
                "p50_location_error":  float(np.percentile(errors, 50)),
                "p95_location_error":  float(np.percentile(errors, 95)),
                "avg_group_size":      float(np.mean(groups)),
                "avg_temporal_delay":  float(np.mean(delays)),
                "max_temporal_delay":  float(np.max(delays)),
                "avg_temporal_jump":   float(np.mean(temporal_jumps))
                                       if temporal_jumps else 0.0,
                "k_satisfaction_rate": k_sat,
                "_error_samples":      errors[::max(1, len(errors) // 500)],
            }
            results[(k, window_sec)] = entry

            print(f"  k={k}: err={entry['avg_location_error']:.0f} m  "
                  f"delay={entry['avg_temporal_delay']:.0f} s  "
                  f"group={entry['avg_group_size']:.1f}  "
                  f"k-sat={k_sat*100:.0f}%")
        print()

    return results


# -----------------------------------------------------------------------
# Figure 1 -- Spatial Visualisation
# -----------------------------------------------------------------------
def fig_spatial(nodes_json, edges_json, dist_cache, trajectories,
                window_sec=600, k=5):
    print("  Generating Fig 1: spatial visualisation...")
    cloaker = TemporalCloaker(
        nodes_json, edges_json, k=k,
        window_sec=window_sec, dist_cache=dist_cache)
    coords = cloaker.node_coords

    # Use a subset for clarity
    sub_trajs = dict(list(trajectories.items())[:10])
    records = cloaker.cloak_trajectories(sub_trajs)

    if not records:
        print("  Skipping Fig 1."); return

    with open(EDGES_FILE) as f:
        edges_raw = json.load(f)

    orig_nodes = set()
    cloak_nodes = set()
    for r in records:
        orig_nodes.add(r["original_node"])
        cloak_nodes.add(r["cloaked_node"])
    active = orig_nodes | cloak_nodes
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

    # Left: original trajectory points
    ax = axes[0]; bg(ax)
    for n in orig_nodes:
        if n in coords:
            ax.scatter(coords[n][0], coords[n][1], s=30, c="#00ccff",
                       zorder=4, edgecolors="white", linewidths=0.3)
    ax.set_title("(a)  Original Trajectory Points", fontweight="bold")

    # Right: temporal-cloaked locations
    ax = axes[1]; bg(ax)
    for n in cloak_nodes:
        if n in coords:
            ax.scatter(coords[n][0], coords[n][1], marker="*", s=100,
                       c="#ffff66", zorder=5, edgecolors="black",
                       linewidths=0.4)
    ax.set_title(f"(b)  Temporal Cloaking (k={k}, Δt={WINDOW_LABELS[window_sec]})",
                 fontweight="bold")
    ax.legend(handles=[
        plt.Line2D([0], [0], marker="*", color="w", # type: ignore
                   markerfacecolor="#ffff66", markersize=11,
                   label="Cloaked location"),
    ], loc="best", framealpha=0.8)

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "fig1_spatial_temporal_cloaking.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 2 -- Error vs k
# -----------------------------------------------------------------------
def fig_error_vs_k(results):
    print("  Generating Fig 2: error vs k...")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, w in enumerate(WINDOW_SECS):
        ks, means, stds = [], [], []
        for k in K_VALUES:
            if (k, w) in results:
                r = results[(k, w)]
                ks.append(k); means.append(r["avg_location_error"])
                stds.append(r["std_location_error"])
        if not ks: continue
        means, stds = np.array(means), np.array(stds)
        ax.plot(ks, means, marker="o", color=COLORS[i], linewidth=2,
                label=f"Δt = {WINDOW_LABELS[w]}")
        ax.fill_between(ks, means - stds, means + stds,
                        color=COLORS[i], alpha=0.12)
    ax.set_xlabel("Anonymity Parameter k")
    ax.set_ylabel("Location Error (metres)")
    ax.set_title("Location Error vs k  [Temporal Cloaking]")
    ax.set_xticks(K_VALUES); ax.legend(); ax.grid(True, alpha=0.35)
    path = os.path.join(FIGURE_DIR, "fig2_error_vs_k.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 3 -- Temporal Delay vs k
# -----------------------------------------------------------------------
def fig_delay_vs_k(results):
    print("  Generating Fig 3: temporal delay vs k...")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, w in enumerate(WINDOW_SECS):
        ks, delays = [], []
        for k in K_VALUES:
            if (k, w) in results:
                ks.append(k)
                delays.append(results[(k, w)]["avg_temporal_delay"])
        if not ks: continue
        ax.plot(ks, delays, marker="s", color=COLORS[i], linewidth=2,
                label=f"Δt = {WINDOW_LABELS[w]}")
    ax.set_xlabel("Anonymity Parameter k")
    ax.set_ylabel("Avg Temporal Delay (seconds)")
    ax.set_title("Temporal Delay vs k  [Privacy Cost in Time]")
    ax.set_xticks(K_VALUES); ax.legend(); ax.grid(True, alpha=0.35)
    path = os.path.join(FIGURE_DIR, "fig3_delay_vs_k.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 4 -- CDF of Location Errors
# -----------------------------------------------------------------------
def fig_error_cdf(results):
    print("  Generating Fig 4: CDF of errors...")
    best_w = max(WINDOW_SECS, key=lambda w: sum(
        results[(k, w)]["n_records"] for k in K_VALUES
        if (k, w) in results))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, k in enumerate(K_VALUES):
        if (k, best_w) not in results: continue
        samp = sorted(results[(k, best_w)]["_error_samples"])
        cdf = np.arange(1, len(samp) + 1) / len(samp)
        ax.plot(samp, cdf, color=COLORS[i], linewidth=2, label=f"k = {k}")
    ax.set_xlabel("Location Error (metres)")
    ax.set_ylabel("Cumulative Probability")
    ax.set_title(f"CDF of Errors  (Δt = {WINDOW_LABELS[best_w]})")
    ax.set_xlim(left=0); ax.set_ylim(0, 1.02)
    ax.legend(); ax.grid(True, alpha=0.35)
    path = os.path.join(FIGURE_DIR, "fig4_error_cdf.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 5 -- Heatmap
# -----------------------------------------------------------------------
def fig_heatmap(results):
    print("  Generating Fig 5: error heatmap...")
    mat = np.full((len(K_VALUES), len(WINDOW_SECS)), np.nan)
    for i, k in enumerate(K_VALUES):
        for j, w in enumerate(WINDOW_SECS):
            if (k, w) in results:
                mat[i, j] = results[(k, w)]["avg_location_error"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    im = ax.imshow(mat, aspect="auto", cmap="YlOrRd", origin="lower")
    ax.set_xticks(range(len(WINDOW_SECS)))
    ax.set_xticklabels([WINDOW_LABELS[w] for w in WINDOW_SECS])
    ax.set_yticks(range(len(K_VALUES)))
    ax.set_yticklabels([str(k) for k in K_VALUES])
    ax.set_xlabel("Time Window (Δt)"); ax.set_ylabel("Anonymity Parameter k")
    ax.set_title("Avg Location Error (m) — Temporal Cloaking")
    vmax = float(np.nanmax(mat)) if not np.all(np.isnan(mat)) else 1
    for i in range(len(K_VALUES)):
        for j in range(len(WINDOW_SECS)):
            if not np.isnan(mat[i, j]):
                tc = "white" if mat[i, j] > 0.55 * vmax else "black"
                ax.text(j, i, f"{mat[i, j]:.0f}", ha="center",
                        va="center", fontsize=9, color=tc)
    plt.colorbar(im, ax=ax, label="Location Error (m)")
    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "fig5_heatmap.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
def _utility_score(r):
    privacy = math.log(r["avg_group_size"] + 1)
    utility = 1.0 / (1.0 + r["avg_location_error"]
                      + 0.01 * r["avg_temporal_delay"]
                      + 0.5 * r["avg_temporal_jump"])
    return privacy * utility


def write_analysis(results):
    best = max(results.values(), key=_utility_score)
    lines = [
        "# Temporal Cloaking Evaluation — GeoLife Dataset\n\n",
        "## Metrics per (k, Time Window)\n\n",
        "| k | Δt | Avg Error (m) | Median (m) | P95 (m) |"
        " Avg Group | Avg Delay (s) | k-Sat |\n",
        "|---|-----|---------------|------------|---------|"
        "-----------|---------------|-------|\n",
    ]
    for r in sorted(results.values(),
                    key=lambda x: (x["window_sec"], x["k"])):
        lines.append(
            f"| {r['k']} | {r['window_label']} "
            f"| {r['avg_location_error']:.1f} "
            f"| {r['p50_location_error']:.1f} "
            f"| {r['p95_location_error']:.1f} "
            f"| {r['avg_group_size']:.1f} "
            f"| {r['avg_temporal_delay']:.1f} "
            f"| {r['k_satisfaction_rate']*100:.0f}% |\n")
    lines += [
        f"\n## Best Configuration\n\n",
        f"- **k** = {best['k']}\n",
        f"- **Δt** = {best['window_label']}\n",
        f"- Avg error: {best['avg_location_error']:.1f} m\n",
        f"- Avg delay: {best['avg_temporal_delay']:.1f} s\n",
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

    trajectories = load_trajectories()

    print("=== Evaluation ===")
    results = evaluate_all(nodes_json, edges_json, trajectories)

    if not results:
        print("ERROR: No results produced."); return

    serializable = {
        f"k{r['k']}_w{r['window_sec']}": {
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
    base = TemporalCloaker(nodes_json, edges_json, k=3, window_sec=300)
    dc = base.get_dist_cache()
    fig_spatial(nodes_json, edges_json, dc, trajectories,
                window_sec=600, k=5)
    fig_error_vs_k(results)
    fig_delay_vs_k(results)
    fig_error_cdf(results)
    fig_heatmap(results)

    print(f"\n=== Done ===")
    print(f"Results  -> {RESULT_DIR}")
    print(f"Best config: k={best['k']}, Δt={best['window_label']}, "
          f"err={best['avg_location_error']:.1f} m, "
          f"delay={best['avg_temporal_delay']:.1f} s")


if __name__ == "__main__":
    run()
