"""
Evaluation of Graph-Based k-Anonymity on the Microsoft GeoLife Dataset
=======================================================================

Loads the preprocessed GeoLife road-network snapshots and evaluates
graph-based spatial cloaking k-anonymity across a range of k values
and temporal window sizes.  Produces publication-quality figures.

Dataset
-------
Zheng, Y., Zhang, L., Xie, X., & Ma, W.-Y. (2009). Mining Interesting
Locations and Travel Sequences from GPS Trajectories. WWW 2009.

Zheng, Y., Li, Q., Chen, Y., Xie, X., & Ma, W.-Y. (2008). Understanding
Mobility Based on GPS Traces. UbiComp 2008.

Algorithm reference
-------------------
See k_anonymity.py for full citation list.  Core algorithm:
  Gruteser & Grunwald (2003) -- spatial cloaking concept.
  Mokbel, Chow & Aref (2006) -- BFS region expansion design.

Evaluation methodology
----------------------
Gedik, B. & Liu, L. (2008). Protecting Location Privacy with Personalized
k-Anonymity: Architecture and Algorithms.
IEEE Transactions on Mobile Computing, 7(1), 1-18.
  -- Standard evaluation metrics for location k-anonymity:
     location error (privacy cost) and region size (privacy gain).

Metrics
-------
  Location Error   : graph shortest-path distance (metres) from the user's
                     true road-network node to the cloaked (reported) node.
  Region Size      : number of road-network nodes in the cloaking region
                     (proxy for the spatial uncertainty introduced).
  Temporal Jump    : graph distance between a user's consecutive cloaked
                     nodes across adjacent time windows (stability metric).
  k-Satisfaction   : fraction of records where k_achieved >= k.
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

from k_anonymity import GraphKAnonymizer


# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
_HERE       = os.path.dirname(os.path.abspath(__file__))
BASE        = os.path.join(_HERE, "..", "..")
DATA_DIR    = os.path.join(BASE, "data", "processed_data")
RESULT_DIR  = os.path.join(BASE, "results", "k_anonymity")
FIGURE_DIR  = os.path.join(RESULT_DIR, "figures")

TRAJ_INDEX  = os.path.join(DATA_DIR, "device_locations_indexed.jsonl")
NODES_FILE  = os.path.join(DATA_DIR, "city_graph_nodes.json")
EDGES_FILE  = os.path.join(DATA_DIR, "city_graph_edges.json")

TIME_WINDOWS  = [60, 300, 600, 1200]   # seconds
K_VALUES      = [2, 3, 4, 5, 6]
MAX_SNAPSHOTS = 300   # cap per window for tractable runtime

WINDOW_LABELS = {60: "1 min", 300: "5 min", 600: "10 min", 1200: "20 min"}
COLORS        = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

# Paper-quality matplotlib defaults
plt.rcParams.update({
    "font.family":      "serif",
    "font.size":        11,
    "axes.titlesize":   12,
    "axes.labelsize":   11,
    "legend.fontsize":  10,
    "xtick.labelsize":  10,
    "ytick.labelsize":  10,
    "savefig.dpi":      300,
    "savefig.bbox":     "tight",
})


# -----------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------
def load_graph_data():
    with open(NODES_FILE) as f:
        nodes = json.load(f)
    with open(EDGES_FILE) as f:
        edges = json.load(f)
    return nodes, edges


def build_all_buckets():
    """
    Single pass through the pre-indexed JSONL to build temporal snapshots
    for all time windows simultaneously.

    The JSONL carries pre-computed bucket keys (t60, t300, t600, t1200),
    so no timestamp arithmetic is needed here.

    The dataset is user-sorted (not time-sorted), so a naive sequential
    stream would produce single-user snapshots.  Instead we accumulate
    {bucket: {user: node}} dicts and yield them after the full pass.

    Returns
    -------
    all_buckets : dict
        {window_sec: {bucket_id: {user_id: node_id}}}
    """
    print("Building time-bucket index (single pass through JSONL)...")
    all_buckets = {w: defaultdict(dict) for w in TIME_WINDOWS}

    with open(TRAJ_INDEX) as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            user, node = row["user"], row["node"]
            for w in TIME_WINDOWS:
                b = row[f"t{w}"]
                # Last seen node wins within each bucket (most recent position)
                all_buckets[w][b][user] = node
            if i % 2_000_000 == 0 and i > 0:
                print(f"  {i:,} records processed")

    # Convert to plain dicts; count multi-user buckets per window
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
    """
    Return a representative sample of snapshots (dicts {user: node})
    sorted by bucket id (chronological order), capped at MAX_SNAPSHOTS.

    Snapshots with fewer than min_users active users are skipped.
    """
    buckets = all_buckets[window]
    candidates = sorted(
        (snap for snap in buckets.values() if len(snap) >= min_users),
        key=id   # stable but arbitrary; actual time-ordering not required
    )
    if len(candidates) > MAX_SNAPSHOTS:
        # Evenly spaced sample across the timeline
        step = len(candidates) // MAX_SNAPSHOTS
        candidates = candidates[::step][:MAX_SNAPSHOTS]
    return candidates


# -----------------------------------------------------------------------
# Core evaluation
# Computes all metrics described in Gedik & Liu (2008) for each (k, window)
# -----------------------------------------------------------------------
def evaluate_all(nodes_json, edges_json, all_buckets):
    """
    Run evaluation for all (k, window) combinations.

    The road-network graph and all-pairs distances are computed ONCE and
    shared across every k value -- only the anonymity parameter k differs
    between GraphKAnonymizer instances.

    Returns
    -------
    results : dict  {(k, window_sec): metrics_dict}
    """
    print("Loading graph and computing all-pairs distances (once)...")
    base = GraphKAnonymizer(nodes_json, edges_json, k=2)
    dist_cache = base.get_dist_cache()
    print(f"Graph: {len(base.graph)} nodes, distances cached.\n")

    results = {}

    for window in TIME_WINDOWS:
        print(f"--- Time window: {WINDOW_LABELS[window]} ---")
        snapshots = get_snapshots(all_buckets, window, min_users=2)
        print(f"  Snapshots to evaluate: {len(snapshots)}")

        if not snapshots:
            continue

        for k in K_VALUES:
            anon = GraphKAnonymizer(nodes_json, edges_json,
                                    k=k, dist_cache=dist_cache)

            errors, region_sizes, temporal_jumps = [], [], []
            k_satisfied = 0
            total = 0
            last_cloaked = {}   # user_id -> previous cloaked node

            for snap in snapshots:
                if len(snap) < k:
                    continue

                res = anon.anonymize_snapshot(snap)

                for uid, data in res.items():
                    orig   = data["original_node"]
                    cloak  = data["cloaked_node"]
                    region = data["region"]

                    d = anon.dist(orig, cloak)
                    errors.append(d)
                    region_sizes.append(len(region))

                    if data["k_achieved"] >= k:
                        k_satisfied += 1

                    if uid in last_cloaked:
                        temporal_jumps.append(anon.dist(last_cloaked[uid], cloak))

                    last_cloaked[uid] = cloak
                    total += 1

            if total == 0:
                continue

            errors.sort()
            entry = {
                "k":                   k,
                "window_sec":          window,
                "window_label":        WINDOW_LABELS[window],
                "n_records":           total,
                "avg_location_error":  float(np.mean(errors)),
                "std_location_error":  float(np.std(errors)),
                "p50_location_error":  float(np.percentile(errors, 50)),
                "p95_location_error":  float(np.percentile(errors, 95)),
                "avg_region_size":     float(np.mean(region_sizes)),
                "std_region_size":     float(np.std(region_sizes)),
                "avg_temporal_jump":   float(np.mean(temporal_jumps))
                                       if temporal_jumps else 0.0,
                "k_satisfaction_rate": k_satisfied / total,
                # Down-sampled error list for CDF plots (at most 500 pts)
                "_error_samples":      errors[::max(1, len(errors) // 500)],
            }
            results[(k, window)] = entry

            print(f"  k={k}: err={entry['avg_location_error']:.0f} m  "
                  f"region={entry['avg_region_size']:.1f} nodes  "
                  f"k-sat={entry['k_satisfaction_rate']*100:.0f}%")

        print()

    return results


# -----------------------------------------------------------------------
# Figure 1 -- Spatial Cloaking Visualisation
# Side-by-side: true GPS locations vs k-anonymous cloaking regions
# Plotted in real Beijing longitude/latitude coordinates
# -----------------------------------------------------------------------
def fig_spatial_cloaking(nodes_json, edges_json, dist_cache,
                          all_buckets, window=300, k=3):
    print("  Generating Fig 1: spatial cloaking visualisation...")

    anon   = GraphKAnonymizer(nodes_json, edges_json, k=k,
                              dist_cache=dist_cache)
    coords = anon.node_coords

    # Find a snapshot with enough users for a clear illustration
    snap = None
    for candidate in get_snapshots(all_buckets, window, min_users=k * 2):
        if len(candidate) >= k * 2:
            snap = dict(list(candidate.items())[:30])  # cap at 30 for clarity
            break
    if snap is None:
        print("  Skipping Fig 1: no suitable snapshot found.")
        return

    result  = anon.anonymize_snapshot(snap)
    tracked = list(result.keys())[0]

    # Collect all nodes that appear in the snapshot or its cloaking regions
    active_nodes = (
        {str(n) for n in snap.values()} |
        {n for data in result.values() for n in data["region"]}
    )
    edge_lines = [
        (str(e["source"]), str(e["target"]))
        for e in edges_json
        if str(e["source"]) in active_nodes or str(e["target"]) in active_nodes
    ]

    def draw_background(ax):
        ax.set_facecolor("#1a1a2e")
        for s, t in edge_lines:
            if s in coords and t in coords:
                ax.plot([coords[s][0], coords[t][0]],
                        [coords[s][1], coords[t][1]],
                        color="#3a3a5e", lw=0.7, alpha=0.8, zorder=1)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # ---- Left: raw / true locations ----
    ax = axes[0]
    draw_background(ax)
    for uid, node in snap.items():
        n = str(node)
        if n not in coords:
            continue
        color = "#ff4444" if uid == tracked else "#00ccff"
        size  = 120       if uid == tracked else 45
        ax.scatter(coords[n][0], coords[n][1], s=size, c=color, zorder=4,
                   edgecolors="white", linewidths=0.5)
    ax.set_title("(a)  True Locations — No Privacy", fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color="#ff4444", label="Tracked user"),
        mpatches.Patch(color="#00ccff", label="Other users"),
    ], loc="best", framealpha=0.8)

    # ---- Right: k-anonymous cloaking regions ----
    ax = axes[1]
    draw_background(ax)
    PAD = 0.0008
    for uid, data in result.items():
        region = [n for n in data["region"] if n in coords]
        cloak  = data["cloaked_node"]
        if len(region) >= 2:
            rxs = [coords[n][0] for n in region]
            rys = [coords[n][1] for n in region]
            rect = mpatches.FancyBboxPatch(
                (min(rxs) - PAD, min(rys) - PAD),
                max(rxs) - min(rxs) + 2 * PAD,
                max(rys) - min(rys) + 2 * PAD,
                boxstyle="round,pad=0.0003",
                linewidth=0.6, edgecolor="#ffaa00",
                facecolor="#ffaa00", alpha=0.18, zorder=3,
            )
            ax.add_patch(rect)
        if cloak in coords:
            color = "#ff4444" if uid == tracked else "#ffff66"
            size  = 180       if uid == tracked else 70
            ax.scatter(coords[cloak][0], coords[cloak][1],
                       marker="*", s=size, c=color, zorder=5,
                       edgecolors="black", linewidths=0.4)
    ax.set_title(f"(b)  k-Anonymous Cloaking Regions (k = {k})", fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color="#ffaa00", alpha=0.4, label="Cloaking region"),
        plt.Line2D([0], [0], marker="*", color="w",
                   markerfacecolor="#ff4444", markersize=13,
                   label="Tracked user (cloaked)"),
        plt.Line2D([0], [0], marker="*", color="w",
                   markerfacecolor="#ffff66", markersize=11,
                   label="Other users (cloaked)"),
    ], loc="best", framealpha=0.8)

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "fig1_spatial_cloaking.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 2 -- Location Error vs k  (privacy cost)
# -----------------------------------------------------------------------
def fig_error_vs_k(results):
    print("  Generating Fig 2: location error vs k...")
    fig, ax = plt.subplots(figsize=(7, 4.5))

    for i, window in enumerate(TIME_WINDOWS):
        ks, means, stds = [], [], []
        for k in K_VALUES:
            if (k, window) in results:
                r = results[(k, window)]
                ks.append(k)
                means.append(r["avg_location_error"])
                stds.append(r["std_location_error"])
        if not ks:
            continue
        means = np.array(means)
        stds  = np.array(stds)
        ax.plot(ks, means, marker="o", color=COLORS[i], linewidth=2,
                label=f"\u0394t = {WINDOW_LABELS[window]}")
        ax.fill_between(ks, means - stds, means + stds,
                        color=COLORS[i], alpha=0.12)

    ax.set_xlabel("Anonymity Parameter k")
    ax.set_ylabel("Location Error (metres)")
    ax.set_title("Location Error vs k  [Privacy Cost]")
    ax.set_xticks(K_VALUES)
    ax.legend()
    ax.grid(True, alpha=0.35)

    path = os.path.join(FIGURE_DIR, "fig2_error_vs_k.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 3 -- Cloaking Region Size vs k  (privacy gain)
# -----------------------------------------------------------------------
def fig_region_size_vs_k(results):
    print("  Generating Fig 3: region size vs k...")
    fig, ax = plt.subplots(figsize=(7, 4.5))

    for i, window in enumerate(TIME_WINDOWS):
        ks, sizes, stds = [], [], []
        for k in K_VALUES:
            if (k, window) in results:
                r = results[(k, window)]
                ks.append(k)
                sizes.append(r["avg_region_size"])
                stds.append(r["std_region_size"])
        if not ks:
            continue
        sizes = np.array(sizes)
        stds  = np.array(stds)
        ax.plot(ks, sizes, marker="s", color=COLORS[i], linewidth=2,
                label=f"\u0394t = {WINDOW_LABELS[window]}")
        ax.fill_between(ks, sizes - stds, sizes + stds,
                        color=COLORS[i], alpha=0.12)

    ax.set_xlabel("Anonymity Parameter k")
    ax.set_ylabel("Cloaking Region Size (nodes)")
    ax.set_title("Cloaking Region Size vs k  [Privacy Gain]")
    ax.set_xticks(K_VALUES)
    ax.legend()
    ax.grid(True, alpha=0.35)

    path = os.path.join(FIGURE_DIR, "fig3_region_size_vs_k.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 4 -- Privacy-Utility Tradeoff
# Following the evaluation framework of Gedik & Liu (2008):
#   x-axis: privacy gain (region size)
#   y-axis: utility = 1 / (1 + location_error)
# -----------------------------------------------------------------------
def fig_privacy_utility(results):
    print("  Generating Fig 4: privacy-utility tradeoff...")
    fig, ax = plt.subplots(figsize=(7, 5))

    for i, window in enumerate(TIME_WINDOWS):
        privs, utils, lbls = [], [], []
        for k in K_VALUES:
            if (k, window) in results:
                r = results[(k, window)]
                privs.append(r["avg_region_size"])
                utils.append(1.0 / (1.0 + r["avg_location_error"]))
                lbls.append(f"k={k}")
        if not privs:
            continue
        ax.plot(privs, utils, marker="o", color=COLORS[i], linewidth=1.5,
                linestyle="--", label=f"\u0394t = {WINDOW_LABELS[window]}")
        for p, u, lbl in zip(privs, utils, lbls):
            ax.annotate(lbl, (p, u), textcoords="offset points",
                        xytext=(4, 4), fontsize=8, color=COLORS[i])

    ax.set_xlabel("Privacy Gain  (avg cloaking region, nodes)")
    ax.set_ylabel("Utility Score  1/(1 + location error)")
    ax.set_title("Privacy-Utility Tradeoff")
    ax.legend()
    ax.grid(True, alpha=0.35)

    path = os.path.join(FIGURE_DIR, "fig4_privacy_utility.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 5 -- CDF of Location Errors for each k
# -----------------------------------------------------------------------
def fig_error_cdf(results):
    print("  Generating Fig 5: CDF of location errors...")

    # Use the window with the most data points as the representative
    best_window = max(
        TIME_WINDOWS,
        key=lambda w: sum(
            results[(k, w)]["n_records"]
            for k in K_VALUES if (k, w) in results
        )
    )

    fig, ax = plt.subplots(figsize=(7, 4.5))

    for i, k in enumerate(K_VALUES):
        if (k, best_window) not in results:
            continue
        samples = sorted(results[(k, best_window)]["_error_samples"])
        cdf = np.arange(1, len(samples) + 1) / len(samples)
        ax.plot(samples, cdf, color=COLORS[i], linewidth=2, label=f"k = {k}")

    ax.set_xlabel("Location Error (metres)")
    ax.set_ylabel("Cumulative Probability")
    ax.set_title(
        f"CDF of Location Errors  (\u0394t = {WINDOW_LABELS[best_window]})")
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.02)
    ax.legend()
    ax.grid(True, alpha=0.35)

    path = os.path.join(FIGURE_DIR, "fig5_error_cdf.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 6 -- Heatmap: avg location error for each (k, window) pair
# -----------------------------------------------------------------------
def fig_heatmap(results):
    print("  Generating Fig 6: error heatmap...")
    matrix = np.full((len(K_VALUES), len(TIME_WINDOWS)), np.nan)
    for i, k in enumerate(K_VALUES):
        for j, w in enumerate(TIME_WINDOWS):
            if (k, w) in results:
                matrix[i, j] = results[(k, w)]["avg_location_error"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", origin="lower")

    ax.set_xticks(range(len(TIME_WINDOWS)))
    ax.set_xticklabels([WINDOW_LABELS[w] for w in TIME_WINDOWS])
    ax.set_yticks(range(len(K_VALUES)))
    ax.set_yticklabels([str(k) for k in K_VALUES])
    ax.set_xlabel("Time Window (\u0394t)")
    ax.set_ylabel("Anonymity Parameter k")
    ax.set_title("Avg Location Error (metres) by k and Time Window")

    vmax = float(np.nanmax(matrix))
    for i in range(len(K_VALUES)):
        for j in range(len(TIME_WINDOWS)):
            if not np.isnan(matrix[i, j]):
                txt_color = "white" if matrix[i, j] > 0.55 * vmax else "black"
                ax.text(j, i, f"{matrix[i, j]:.0f}",
                        ha="center", va="center",
                        fontsize=9, color=txt_color)

    plt.colorbar(im, ax=ax, label="Location Error (m)")
    plt.tight_layout()

    path = os.path.join(FIGURE_DIR, "fig6_heatmap.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Utility score  (Gedik & Liu 2008 inspired composite metric)
# Higher is better: rewards large regions (privacy) and low error (utility)
# -----------------------------------------------------------------------
def _utility_score(r):
    privacy = math.log(r["avg_region_size"] + 1)
    utility = 1.0 / (1.0 + r["avg_location_error"] + 0.5 * r["avg_temporal_jump"])
    return privacy * utility


# -----------------------------------------------------------------------
# Analysis report (Markdown table)
# -----------------------------------------------------------------------
def write_analysis(results):
    best = max(results.values(), key=_utility_score)

    lines = [
        "# k-Anonymity Evaluation — GeoLife Dataset\n\n",
        "## Metrics per (k, Time Window)\n\n",
        "| k | \u0394t | Avg Error (m) | Median (m) |"
        " P95 (m) | Avg Region | Temp Jump | k-Sat |\n",
        "|---|-----|---------------|------------|"
        "---------|------------|-----------|-------|\n",
    ]
    for r in sorted(results.values(),
                    key=lambda x: (x["window_sec"], x["k"])):
        lines.append(
            f"| {r['k']} | {r['window_label']} "
            f"| {r['avg_location_error']:.1f} "
            f"| {r['p50_location_error']:.1f} "
            f"| {r['p95_location_error']:.1f} "
            f"| {r['avg_region_size']:.1f} "
            f"| {r['avg_temporal_jump']:.1f} "
            f"| {r['k_satisfaction_rate'] * 100:.0f}% |\n"
        )

    lines += [
        f"\n## Best Configuration (privacy-utility score)\n\n",
        f"- **k** = {best['k']}\n",
        f"- **\u0394t** = {best['window_label']}\n",
        f"- Avg location error: {best['avg_location_error']:.1f} m\n",
        f"- Avg region size: {best['avg_region_size']:.1f} nodes\n",
        f"- k-satisfaction rate: {best['k_satisfaction_rate'] * 100:.0f}%\n",
    ]

    with open(os.path.join(RESULT_DIR, "analysis.md"), "w") as f:
        f.writelines(lines)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
def run():
    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs(FIGURE_DIR, exist_ok=True)

    # Step 1: load graph data
    print("Loading graph data...")
    nodes_json, edges_json = load_graph_data()
    print(f"  {len(nodes_json)} nodes, {len(edges_json)} edges\n")

    # Step 2: build time-bucket index (single JSONL pass)
    all_buckets = build_all_buckets()

    # Step 3: evaluate all (k, window) combinations
    print("=== Evaluation ===")
    results = evaluate_all(nodes_json, edges_json, all_buckets)

    if not results:
        print("ERROR: No results produced -- check data files.")
        return

    # Step 4: persist results
    serializable = {
        f"k{r['k']}_w{r['window_sec']}": {
            key: val for key, val in r.items() if not key.startswith("_")
        }
        for r in results.values()
    }
    with open(os.path.join(RESULT_DIR, "results.json"), "w") as f:
        json.dump(serializable, f, indent=2)

    best = max(results.values(), key=_utility_score)
    best_save = {k: v for k, v in best.items() if not k.startswith("_")}
    with open(os.path.join(RESULT_DIR, "best_config.json"), "w") as f:
        json.dump(best_save, f, indent=2)

    write_analysis(results)

    # Step 5: generate figures
    print("\n=== Figures ===")
    # Reuse dist_cache for the spatial figure
    base_anon  = GraphKAnonymizer(nodes_json, edges_json, k=2)
    dist_cache = base_anon.get_dist_cache()

    fig_spatial_cloaking(nodes_json, edges_json, dist_cache,
                         all_buckets, window=300, k=3)
    fig_error_vs_k(results)
    fig_region_size_vs_k(results)
    fig_privacy_utility(results)
    fig_error_cdf(results)
    fig_heatmap(results)

    print(f"\n=== Done ===")
    print(f"Results  -> {RESULT_DIR}")
    print(f"Figures  -> {FIGURE_DIR}")
    print(f"Best config: k={best['k']}, \u0394t={best['window_label']}, "
          f"avg error={best['avg_location_error']:.1f} m")


if __name__ == "__main__":
    run()
