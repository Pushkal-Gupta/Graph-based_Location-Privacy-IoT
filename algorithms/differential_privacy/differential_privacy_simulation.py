"""
Evaluation of Differential Privacy Location Obfuscation on GeoLife
===================================================================

Loads the preprocessed GeoLife road-network snapshots and evaluates
coordinate-based differential privacy (planar Laplace mechanism)
across a range of ε values and temporal window sizes.  Produces
publication-quality figures.

Dataset
-------
Zheng, Y., Zhang, L., Xie, X., & Ma, W.-Y. (2009). Mining Interesting
Locations and Travel Sequences from GPS Trajectories. WWW 2009.

Algorithm reference
-------------------
See differential_privacy.py for full citation list.  Core mechanism:
  Dwork et al. (2006) -- Laplace mechanism.
  Andrés et al. (2013) -- geo-indistinguishability.

Evaluation methodology
----------------------
Shokri, R., Theodorakopoulos, G., Le Boudec, J.-Y., & Hubaux, J.-P.
(2011). Quantifying Location Privacy.  Proc. IEEE S&P 2011.
  -- Standard evaluation framework for location privacy mechanisms:
     expected estimation error as the primary privacy metric.
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

from differential_privacy import DPLocationObfuscator, _haversine_m


# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
_HERE       = os.path.dirname(os.path.abspath(__file__))
BASE        = os.path.join(_HERE, "..", "..")
DATA_DIR    = os.path.join(BASE, "data", "processed_data")
RESULT_DIR  = os.path.join(BASE, "results", "differential_privacy")
FIGURE_DIR  = os.path.join(RESULT_DIR, "figures")

CSV_FILE    = os.path.join(DATA_DIR, "device_locations.csv")
NODES_FILE  = os.path.join(DATA_DIR, "city_graph_nodes.json")
EDGES_FILE  = os.path.join(DATA_DIR, "city_graph_edges.json")

TIME_WINDOWS  = [60, 300, 600, 1200]
EPSILON_VALUES = [0.1, 0.5, 1.0, 2.0, 5.0]
MAX_SNAPSHOTS  = 300

WINDOW_LABELS = {60: "1 min", 300: "5 min", 600: "10 min", 1200: "20 min"}
COLORS        = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

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
# Data loading  (CSV with timestamp-based bucketing)
# -----------------------------------------------------------------------
def load_graph_data():
    with open(NODES_FILE) as f:
        nodes = json.load(f)
    with open(EDGES_FILE) as f:
        edges = json.load(f)
    return nodes, edges


def build_all_buckets():
    """Read device_locations.csv and build temporal snapshots."""
    import csv
    from datetime import datetime

    print("Building time-bucket index from CSV...")
    all_buckets = {w: defaultdict(dict) for w in TIME_WINDOWS}

    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            user = row["user_id"]
            node = str(row["location_id"])
            ts = datetime.strptime(
                f"{row['date']} {row['time']}", "%Y-%m-%d %H:%M:%S")
            epoch = int(ts.timestamp())
            for w in TIME_WINDOWS:
                b = epoch // w
                all_buckets[w][b][user] = node
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
        (snap for snap in buckets.values() if len(snap) >= min_users),
        key=id,
    )
    if len(candidates) > MAX_SNAPSHOTS:
        step = len(candidates) // MAX_SNAPSHOTS
        candidates = candidates[::step][:MAX_SNAPSHOTS]
    return candidates


# -----------------------------------------------------------------------
# Core evaluation
# -----------------------------------------------------------------------
def evaluate_all(nodes_json, edges_json, all_buckets):
    """
    Run evaluation for all (ε, window) combinations.
    """
    print("Evaluating differential privacy across (ε, window) grid...\n")

    results = {}

    for window in TIME_WINDOWS:
        print(f"--- Time window: {WINDOW_LABELS[window]} ---")
        snapshots = get_snapshots(all_buckets, window, min_users=2)
        print(f"  Snapshots to evaluate: {len(snapshots)}")
        if not snapshots:
            continue

        for eps in EPSILON_VALUES:
            obf = DPLocationObfuscator(nodes_json, edges_json, epsilon=eps)

            errors, temporal_jumps = [], []
            total = 0
            last_noisy = {}  # user_id -> previous noisy coords

            for snap in snapshots:
                res = obf.anonymize_snapshot(snap)

                for uid, data in res.items():
                    errors.append(data["location_error"])

                    if uid in last_noisy:
                        prev = last_noisy[uid]
                        cur  = data["noisy_coords"]
                        temporal_jumps.append(
                            _haversine_m(prev[0], prev[1], cur[0], cur[1])
                        )

                    last_noisy[uid] = data["noisy_coords"]
                    total += 1

            if total == 0:
                continue

            errors.sort()
            entry = {
                "epsilon":             eps,
                "window_sec":          window,
                "window_label":        WINDOW_LABELS[window],
                "n_records":           total,
                "avg_location_error":  float(np.mean(errors)),
                "std_location_error":  float(np.std(errors)),
                "p50_location_error":  float(np.percentile(errors, 50)),
                "p95_location_error":  float(np.percentile(errors, 95)),
                "avg_temporal_jump":   float(np.mean(temporal_jumps))
                                       if temporal_jumps else 0.0,
                "_error_samples":      errors[::max(1, len(errors) // 500)],
            }
            results[(eps, window)] = entry

            print(f"  ε={eps}: err={entry['avg_location_error']:.0f} m  "
                  f"p95={entry['p95_location_error']:.0f} m")

        print()

    return results


# -----------------------------------------------------------------------
# Figure 1 -- Spatial Obfuscation Visualisation
# -----------------------------------------------------------------------
def fig_spatial_obfuscation(nodes_json, edges_json, all_buckets,
                             window=300, epsilon=1.0):
    print("  Generating Fig 1: spatial obfuscation visualisation...")
    obf = DPLocationObfuscator(nodes_json, edges_json, epsilon=epsilon)
    coords = obf.node_coords

    snap = None
    for candidate in get_snapshots(all_buckets, window, min_users=4):
        if len(candidate) >= 4:
            snap = dict(list(candidate.items())[:30])
            break
    if snap is None:
        print("  Skipping Fig 1: no suitable snapshot found.")
        return

    result = obf.anonymize_snapshot(snap)
    tracked = list(result.keys())[0]

    # Build edge lines for context
    with open(EDGES_FILE) as f:
        edges_raw = json.load(f)
    active_nodes = {str(n) for n in snap.values()}
    edge_lines = [
        (str(e["source"]), str(e["target"]))
        for e in edges_raw
        if str(e["source"]) in active_nodes or str(e["target"]) in active_nodes
    ]

    def draw_bg(ax):
        ax.set_facecolor("#1a1a2e")
        for s, t in edge_lines:
            if s in coords and t in coords:
                ax.plot([coords[s][0], coords[t][0]],
                        [coords[s][1], coords[t][1]],
                        color="#3a3a5e", lw=0.7, alpha=0.8, zorder=1)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: true locations
    ax = axes[0]
    draw_bg(ax)
    for uid, node in snap.items():
        n = str(node)
        if n not in coords:
            continue
        c = "#ff4444" if uid == tracked else "#00ccff"
        s = 120 if uid == tracked else 45
        ax.scatter(coords[n][0], coords[n][1], s=s, c=c, zorder=4,
                   edgecolors="white", linewidths=0.5)
    ax.set_title("(a)  True Locations — No Privacy", fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color="#ff4444", label="Tracked user"),
        mpatches.Patch(color="#00ccff", label="Other users"),
    ], loc="best", framealpha=0.8)

    # Right: DP-obfuscated locations
    ax = axes[1]
    draw_bg(ax)
    for uid, data in result.items():
        ox, oy = data["original_coords"]
        nx_, ny_ = data["noisy_coords"]
        c_orig = "#ff4444" if uid == tracked else "#00ccff"
        c_noisy = "#ff8888" if uid == tracked else "#ffff66"
        ax.scatter(ox, oy, s=30, c=c_orig, alpha=0.4, zorder=3)
        ax.scatter(nx_, ny_, s=60, c=c_noisy, marker="*", zorder=5,
                   edgecolors="black", linewidths=0.4)
        ax.plot([ox, nx_], [oy, ny_], color="gray", lw=0.5,
                alpha=0.5, zorder=2)
    ax.set_title(f"(b)  DP-Obfuscated (ε = {epsilon})", fontweight="bold")
    ax.legend(handles=[
        plt.Line2D([0], [0], marker="o", color="w",
                   markerfacecolor="#00ccff", markersize=7, alpha=0.5,
                   label="Original"),
        plt.Line2D([0], [0], marker="*", color="w",
                   markerfacecolor="#ffff66", markersize=11,
                   label="Noisy"),
    ], loc="best", framealpha=0.8)

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "fig1_spatial_obfuscation.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 2 -- Location Error vs ε
# -----------------------------------------------------------------------
def fig_error_vs_epsilon(results):
    print("  Generating Fig 2: location error vs ε...")
    fig, ax = plt.subplots(figsize=(7, 4.5))

    for i, window in enumerate(TIME_WINDOWS):
        eps_list, means, stds = [], [], []
        for eps in EPSILON_VALUES:
            if (eps, window) in results:
                r = results[(eps, window)]
                eps_list.append(eps)
                means.append(r["avg_location_error"])
                stds.append(r["std_location_error"])
        if not eps_list:
            continue
        means = np.array(means)
        stds  = np.array(stds)
        ax.plot(eps_list, means, marker="o", color=COLORS[i], linewidth=2,
                label=f"Δt = {WINDOW_LABELS[window]}")
        ax.fill_between(eps_list, means - stds, means + stds,
                        color=COLORS[i], alpha=0.12)

    ax.set_xscale("log")
    ax.set_xlabel("Privacy Budget ε")
    ax.set_ylabel("Location Error (metres)")
    ax.set_title("Location Error vs ε  [Privacy–Utility Tradeoff]")
    ax.legend()
    ax.grid(True, alpha=0.35)

    path = os.path.join(FIGURE_DIR, "fig2_error_vs_epsilon.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 3 -- Privacy-Utility Tradeoff Scatter
# -----------------------------------------------------------------------
def fig_privacy_utility(results):
    print("  Generating Fig 3: privacy-utility tradeoff...")
    fig, ax = plt.subplots(figsize=(7, 5))

    for i, window in enumerate(TIME_WINDOWS):
        privs, utils, lbls = [], [], []
        for eps in EPSILON_VALUES:
            if (eps, window) in results:
                r = results[(eps, window)]
                privs.append(1.0 / eps)  # higher = more private
                utils.append(1.0 / (1.0 + r["avg_location_error"]))
                lbls.append(f"ε={eps}")
        if not privs:
            continue
        ax.plot(privs, utils, marker="o", color=COLORS[i], linewidth=1.5,
                linestyle="--", label=f"Δt = {WINDOW_LABELS[window]}")
        for p, u, lbl in zip(privs, utils, lbls):
            ax.annotate(lbl, (p, u), textcoords="offset points",
                        xytext=(4, 4), fontsize=8, color=COLORS[i])

    ax.set_xlabel("Privacy Strength  (1/ε)")
    ax.set_ylabel("Utility Score  1/(1 + location error)")
    ax.set_title("Privacy-Utility Tradeoff  [Differential Privacy]")
    ax.legend()
    ax.grid(True, alpha=0.35)

    path = os.path.join(FIGURE_DIR, "fig3_privacy_utility.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 4 -- CDF of Location Errors
# -----------------------------------------------------------------------
def fig_error_cdf(results):
    print("  Generating Fig 4: CDF of location errors...")

    best_window = max(
        TIME_WINDOWS,
        key=lambda w: sum(
            results[(eps, w)]["n_records"]
            for eps in EPSILON_VALUES if (eps, w) in results
        )
    )

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, eps in enumerate(EPSILON_VALUES):
        if (eps, best_window) not in results:
            continue
        samples = sorted(results[(eps, best_window)]["_error_samples"])
        cdf = np.arange(1, len(samples) + 1) / len(samples)
        ax.plot(samples, cdf, color=COLORS[i], linewidth=2,
                label=f"ε = {eps}")

    ax.set_xlabel("Location Error (metres)")
    ax.set_ylabel("Cumulative Probability")
    ax.set_title(
        f"CDF of Location Errors  (Δt = {WINDOW_LABELS[best_window]})")
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.02)
    ax.legend()
    ax.grid(True, alpha=0.35)

    path = os.path.join(FIGURE_DIR, "fig4_error_cdf.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 5 -- Heatmap: avg error for each (ε, window) pair
# -----------------------------------------------------------------------
def fig_heatmap(results):
    print("  Generating Fig 5: error heatmap...")
    matrix = np.full((len(EPSILON_VALUES), len(TIME_WINDOWS)), np.nan)
    for i, eps in enumerate(EPSILON_VALUES):
        for j, w in enumerate(TIME_WINDOWS):
            if (eps, w) in results:
                matrix[i, j] = results[(eps, w)]["avg_location_error"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", origin="lower")

    ax.set_xticks(range(len(TIME_WINDOWS)))
    ax.set_xticklabels([WINDOW_LABELS[w] for w in TIME_WINDOWS])
    ax.set_yticks(range(len(EPSILON_VALUES)))
    ax.set_yticklabels([str(e) for e in EPSILON_VALUES])
    ax.set_xlabel("Time Window (Δt)")
    ax.set_ylabel("Privacy Budget ε")
    ax.set_title("Avg Location Error (metres) by ε and Time Window")

    vmax = float(np.nanmax(matrix))
    for i in range(len(EPSILON_VALUES)):
        for j in range(len(TIME_WINDOWS)):
            if not np.isnan(matrix[i, j]):
                txt_color = "white" if matrix[i, j] > 0.55 * vmax else "black"
                ax.text(j, i, f"{matrix[i, j]:.0f}",
                        ha="center", va="center",
                        fontsize=9, color=txt_color)

    plt.colorbar(im, ax=ax, label="Location Error (m)")
    plt.tight_layout()

    path = os.path.join(FIGURE_DIR, "fig5_heatmap.png")
    plt.savefig(path)
    plt.close()
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Composite utility score  (for best-config selection)
# -----------------------------------------------------------------------
def _utility_score(r):
    privacy = 1.0 / r["epsilon"]
    utility = 1.0 / (1.0 + r["avg_location_error"]
                      + 0.5 * r["avg_temporal_jump"])
    return privacy * utility


# -----------------------------------------------------------------------
# Analysis report
# -----------------------------------------------------------------------
def write_analysis(results):
    best = max(results.values(), key=_utility_score)

    lines = [
        "# Differential Privacy Evaluation — GeoLife Dataset\n\n",
        "## Metrics per (ε, Time Window)\n\n",
        "| ε | Δt | Avg Error (m) | Median (m) |"
        " P95 (m) | Temp Jump | Records |\n",
        "|---|-----|---------------|------------|"
        "---------|-----------|----------|\n",
    ]
    for r in sorted(results.values(),
                    key=lambda x: (x["window_sec"], x["epsilon"])):
        lines.append(
            f"| {r['epsilon']} | {r['window_label']} "
            f"| {r['avg_location_error']:.1f} "
            f"| {r['p50_location_error']:.1f} "
            f"| {r['p95_location_error']:.1f} "
            f"| {r['avg_temporal_jump']:.1f} "
            f"| {r['n_records']} |\n"
        )

    lines += [
        f"\n## Best Configuration (privacy-utility score)\n\n",
        f"- **ε** = {best['epsilon']}\n",
        f"- **Δt** = {best['window_label']}\n",
        f"- Avg location error: {best['avg_location_error']:.1f} m\n",
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
        print("ERROR: No results produced -- check data files.")
        return

    # Persist results
    serializable = {
        f"eps{r['epsilon']}_w{r['window_sec']}": {
            k: v for k, v in r.items() if not k.startswith("_")
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

    # Figures
    print("\n=== Figures ===")
    fig_spatial_obfuscation(nodes_json, edges_json, all_buckets,
                            window=300, epsilon=1.0)
    fig_error_vs_epsilon(results)
    fig_privacy_utility(results)
    fig_error_cdf(results)
    fig_heatmap(results)

    print(f"\n=== Done ===")
    print(f"Results  -> {RESULT_DIR}")
    print(f"Figures  -> {FIGURE_DIR}")
    print(f"Best config: ε={best['epsilon']}, "
          f"Δt={best['window_label']}, "
          f"avg error={best['avg_location_error']:.1f} m")


if __name__ == "__main__":
    run()