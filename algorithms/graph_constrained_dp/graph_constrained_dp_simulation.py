"""
Evaluation of Graph-Constrained DP on the Microsoft GeoLife Dataset
====================================================================

Evaluates graph-constrained differential privacy (Laplace noise with
graph projection) across ε values and temporal window sizes.

Dataset: Zheng et al. (2009), GeoLife GPS Trajectories.
Algorithm: See graph_constrained_dp.py for full citation list.
Evaluation: Shokri et al. (2011), Quantifying Location Privacy.
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

from graph_constrained_dp import GraphConstrainedDPObfuscator, _haversine_m


# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
_HERE       = os.path.dirname(os.path.abspath(__file__))
BASE        = os.path.join(_HERE, "..", "..")
DATA_DIR    = os.path.join(BASE, "data", "processed_data")
RESULT_DIR  = os.path.join(BASE, "results", "graph_constrained_dp")
FIGURE_DIR  = os.path.join(RESULT_DIR, "figures")

TRAJ_INDEX  = os.path.join(DATA_DIR, "device_locations_indexed.jsonl")
NODES_FILE  = os.path.join(DATA_DIR, "city_graph_nodes.json")
EDGES_FILE  = os.path.join(DATA_DIR, "city_graph_edges.json")

TIME_WINDOWS   = [60, 300, 600, 1200]
EPSILON_VALUES = [0.1, 0.5, 1.0, 2.0, 5.0]
MAX_SNAPSHOTS  = 300

WINDOW_LABELS = {60: "1 min", 300: "5 min", 600: "10 min", 1200: "20 min"}
COLORS        = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

plt.rcParams.update({
    "font.family": "serif", "font.size": 11, "axes.titlesize": 12,
    "axes.labelsize": 11, "legend.fontsize": 10, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "savefig.dpi": 300, "savefig.bbox": "tight",
})


# -----------------------------------------------------------------------
# Data loading (JSONL buckets — same as k_anonymity)
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
    base = GraphConstrainedDPObfuscator(nodes_json, edges_json, epsilon=1.0)
    dist_cache = base.get_dist_cache()
    print(f"Graph: {len(base.graph)} nodes, distances cached.\n")

    results = {}

    for window in TIME_WINDOWS:
        print(f"--- Time window: {WINDOW_LABELS[window]} ---")
        snapshots = get_snapshots(all_buckets, window, min_users=2)
        print(f"  Snapshots to evaluate: {len(snapshots)}")
        if not snapshots:
            continue

        for eps in EPSILON_VALUES:
            obf = GraphConstrainedDPObfuscator(
                nodes_json, edges_json, epsilon=eps, dist_cache=dist_cache)

            errors, proj_dists, temporal_jumps = [], [], []
            total = 0
            last_cloaked = {}

            for snap in snapshots:
                res = obf.anonymize_snapshot(snap)
                for uid, data in res.items():
                    errors.append(data["location_error"])
                    proj_dists.append(data["projection_dist"])

                    if uid in last_cloaked:
                        temporal_jumps.append(
                            obf.dist(last_cloaked[uid], data["cloaked_node"]))
                    last_cloaked[uid] = data["cloaked_node"]
                    total += 1

            if total == 0:
                continue

            errors.sort()
            entry = {
                "epsilon":              eps,
                "window_sec":           window,
                "window_label":         WINDOW_LABELS[window],
                "n_records":            total,
                "avg_location_error":   float(np.mean(errors)),
                "std_location_error":   float(np.std(errors)),
                "p50_location_error":   float(np.percentile(errors, 50)),
                "p95_location_error":   float(np.percentile(errors, 95)),
                "avg_projection_dist":  float(np.mean(proj_dists)),
                "avg_temporal_jump":    float(np.mean(temporal_jumps))
                                        if temporal_jumps else 0.0,
                "_error_samples":       errors[::max(1, len(errors) // 500)],
            }
            results[(eps, window)] = entry
            print(f"  ε={eps}: err={entry['avg_location_error']:.0f} m  "
                  f"proj={entry['avg_projection_dist']:.0f} m")

        print()
    return results


# -----------------------------------------------------------------------
# Figure 1 -- Spatial Visualisation
# -----------------------------------------------------------------------
def fig_spatial(nodes_json, edges_json, dist_cache, all_buckets,
                window=300, epsilon=1.0):
    print("  Generating Fig 1: spatial visualisation...")
    obf = GraphConstrainedDPObfuscator(
        nodes_json, edges_json, epsilon=epsilon, dist_cache=dist_cache)
    coords = obf.node_coords

    snap = None
    for c in get_snapshots(all_buckets, window, min_users=4):
        if len(c) >= 4:
            snap = dict(list(c.items())[:30])
            break
    if snap is None:
        print("  Skipping Fig 1.")
        return

    result = obf.anonymize_snapshot(snap)
    tracked = list(result.keys())[0]

    active = {str(n) for n in snap.values()}
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
    for uid, node in snap.items():
        n = str(node)
        if n not in coords: continue
        c = "#ff4444" if uid == tracked else "#00ccff"
        ax.scatter(coords[n][0], coords[n][1],
                   s=120 if uid == tracked else 45, c=c,
                   zorder=4, edgecolors="white", linewidths=0.5)
    ax.set_title("(a)  True Locations", fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color="#ff4444", label="Tracked user"),
        mpatches.Patch(color="#00ccff", label="Other users"),
    ], loc="best", framealpha=0.8)

    ax = axes[1]; bg(ax)
    for uid, data in result.items():
        cn = data["cloaked_node"]
        if cn not in coords: continue
        c = "#ff4444" if uid == tracked else "#ffff66"
        ax.scatter(coords[cn][0], coords[cn][1],
                   marker="*", s=180 if uid == tracked else 70, c=c,
                   zorder=5, edgecolors="black", linewidths=0.4)
    ax.set_title(f"(b)  Graph-Constrained DP (ε = {epsilon})",
                 fontweight="bold")
    ax.legend(handles=[
        plt.Line2D([0], [0], marker="*", color="w",
                   markerfacecolor="#ff4444", markersize=13,
                   label="Tracked (projected)"),
        plt.Line2D([0], [0], marker="*", color="w",
                   markerfacecolor="#ffff66", markersize=11,
                   label="Others (projected)"),
    ], loc="best", framealpha=0.8)

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "fig1_spatial_gc_dp.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 2 -- Error vs ε
# -----------------------------------------------------------------------
def fig_error_vs_epsilon(results):
    print("  Generating Fig 2: error vs ε...")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, w in enumerate(TIME_WINDOWS):
        eps_l, means, stds = [], [], []
        for eps in EPSILON_VALUES:
            if (eps, w) in results:
                r = results[(eps, w)]
                eps_l.append(eps); means.append(r["avg_location_error"])
                stds.append(r["std_location_error"])
        if not eps_l: continue
        means, stds = np.array(means), np.array(stds)
        ax.plot(eps_l, means, marker="o", color=COLORS[i], linewidth=2,
                label=f"Δt = {WINDOW_LABELS[w]}")
        ax.fill_between(eps_l, means - stds, means + stds,
                        color=COLORS[i], alpha=0.12)
    ax.set_xscale("log")
    ax.set_xlabel("Privacy Budget ε")
    ax.set_ylabel("Graph Distance Error (metres)")
    ax.set_title("Location Error vs ε  [Graph-Constrained DP]")
    ax.legend(); ax.grid(True, alpha=0.35)
    path = os.path.join(FIGURE_DIR, "fig2_error_vs_epsilon.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 3 -- Projection Distance vs ε
# -----------------------------------------------------------------------
def fig_projection_vs_epsilon(results):
    print("  Generating Fig 3: projection distance vs ε...")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, w in enumerate(TIME_WINDOWS):
        eps_l, projs = [], []
        for eps in EPSILON_VALUES:
            if (eps, w) in results:
                eps_l.append(eps)
                projs.append(results[(eps, w)]["avg_projection_dist"])
        if not eps_l: continue
        ax.plot(eps_l, projs, marker="s", color=COLORS[i], linewidth=2,
                label=f"Δt = {WINDOW_LABELS[w]}")
    ax.set_xscale("log")
    ax.set_xlabel("Privacy Budget ε")
    ax.set_ylabel("Projection Distance (metres)")
    ax.set_title("Noise-to-Graph Projection Distance vs ε")
    ax.legend(); ax.grid(True, alpha=0.35)
    path = os.path.join(FIGURE_DIR, "fig3_projection_vs_epsilon.png")
    plt.savefig(path); plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 4 -- CDF
# -----------------------------------------------------------------------
def fig_error_cdf(results):
    print("  Generating Fig 4: CDF of errors...")
    best_w = max(TIME_WINDOWS, key=lambda w: sum(
        results[(e, w)]["n_records"] for e in EPSILON_VALUES
        if (e, w) in results))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, eps in enumerate(EPSILON_VALUES):
        if (eps, best_w) not in results: continue
        samp = sorted(results[(eps, best_w)]["_error_samples"])
        cdf = np.arange(1, len(samp) + 1) / len(samp)
        ax.plot(samp, cdf, color=COLORS[i], linewidth=2, label=f"ε = {eps}")
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
    mat = np.full((len(EPSILON_VALUES), len(TIME_WINDOWS)), np.nan)
    for i, eps in enumerate(EPSILON_VALUES):
        for j, w in enumerate(TIME_WINDOWS):
            if (eps, w) in results:
                mat[i, j] = results[(eps, w)]["avg_location_error"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    im = ax.imshow(mat, aspect="auto", cmap="YlOrRd", origin="lower")
    ax.set_xticks(range(len(TIME_WINDOWS)))
    ax.set_xticklabels([WINDOW_LABELS[w] for w in TIME_WINDOWS])
    ax.set_yticks(range(len(EPSILON_VALUES)))
    ax.set_yticklabels([str(e) for e in EPSILON_VALUES])
    ax.set_xlabel("Time Window (Δt)"); ax.set_ylabel("Privacy Budget ε")
    ax.set_title("Avg Location Error (m) — Graph-Constrained DP")
    vmax = float(np.nanmax(mat))
    for i in range(len(EPSILON_VALUES)):
        for j in range(len(TIME_WINDOWS)):
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
    privacy = 1.0 / r["epsilon"]
    utility = 1.0 / (1.0 + r["avg_location_error"]
                      + 0.5 * r["avg_temporal_jump"])
    return privacy * utility


def write_analysis(results):
    best = max(results.values(), key=_utility_score)
    lines = [
        "# Graph-Constrained DP Evaluation — GeoLife Dataset\n\n",
        "## Metrics per (ε, Time Window)\n\n",
        "| ε | Δt | Avg Error (m) | Median (m) | P95 (m) |"
        " Proj Dist | Temp Jump |\n",
        "|---|-----|---------------|------------|---------|"
        "-----------|----------|\n",
    ]
    for r in sorted(results.values(),
                    key=lambda x: (x["window_sec"], x["epsilon"])):
        lines.append(
            f"| {r['epsilon']} | {r['window_label']} "
            f"| {r['avg_location_error']:.1f} "
            f"| {r['p50_location_error']:.1f} "
            f"| {r['p95_location_error']:.1f} "
            f"| {r['avg_projection_dist']:.1f} "
            f"| {r['avg_temporal_jump']:.1f} |\n"
        )
    lines += [
        f"\n## Best Configuration\n\n",
        f"- **ε** = {best['epsilon']}\n",
        f"- **Δt** = {best['window_label']}\n",
        f"- Avg graph error: {best['avg_location_error']:.1f} m\n",
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
        f"eps{r['epsilon']}_w{r['window_sec']}": {
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
    base = GraphConstrainedDPObfuscator(
        nodes_json, edges_json, epsilon=1.0)
    dc = base.get_dist_cache()
    fig_spatial(nodes_json, edges_json, dc, all_buckets, window=300, epsilon=1.0)
    fig_error_vs_epsilon(results)
    fig_projection_vs_epsilon(results)
    fig_error_cdf(results)
    fig_heatmap(results)

    print(f"\n=== Done ===")
    print(f"Results  -> {RESULT_DIR}")
    print(f"Best config: ε={best['epsilon']}, Δt={best['window_label']}, "
          f"err={best['avg_location_error']:.1f} m")


if __name__ == "__main__":
    run()
