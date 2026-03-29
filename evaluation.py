#!/usr/bin/env python3
"""
Cross-Algorithm Evaluation and Comparison
==========================================

Reads results.json from each of the five algorithm result directories
and produces unified comparison figures, tables, and a summary report.

Pipeline
--------
    run_all.py  ->  results/  ->  evaluation.py  ->  paper/

Reads from
----------
    results/k_anonymity/results.json
    results/differential_privacy/results.json
    results/graph_constrained_dp/results.json
    results/density_aware_k_anonymity/results.json
    results/temporal_cloaking/results.json

Outputs
-------
    evaluation/comparison_figures/
    evaluation/comparison_report.md
    paper/figures/  (publication-ready copies)
    paper/tables/   (LaTeX-ready tables)
"""

import os
import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
_HERE       = os.path.dirname(os.path.abspath(__file__))
RESULT_BASE = os.path.join(_HERE, "results")
EVAL_DIR    = os.path.join(_HERE, "evaluation")
FIG_DIR     = os.path.join(EVAL_DIR, "comparison_figures")
PAPER_FIG   = os.path.join(_HERE, "paper", "figures")
PAPER_TABLE = os.path.join(_HERE, "paper", "tables")

ALGORITHMS = {
    "k_anonymity":               "k-Anonymity",
    "differential_privacy":      "Differential Privacy",
    "graph_constrained_dp":      "Graph-Constrained DP",
    "density_aware_k_anonymity": "Density-Aware k-Anon",
    "temporal_cloaking":         "Temporal Cloaking",
}

ALGO_COLORS = {
    "k_anonymity":               "#1f77b4",
    "differential_privacy":      "#ff7f0e",
    "graph_constrained_dp":      "#2ca02c",
    "density_aware_k_anonymity": "#d62728",
    "temporal_cloaking":         "#9467bd",
}

plt.rcParams.update({
    "font.family": "serif", "font.size": 11, "axes.titlesize": 13,
    "axes.labelsize": 11, "legend.fontsize": 9, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "savefig.dpi": 300, "savefig.bbox": "tight",
})


# -----------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------
def load_all_results():
    """
    Load results.json from each algorithm's results directory.

    Returns
    -------
    data : dict  {algo_key: {config_key: metrics_dict}}
    """
    data = {}
    for algo_key in ALGORITHMS:
        path = os.path.join(RESULT_BASE, algo_key, "results.json")
        if not os.path.exists(path):
            print(f"  WARNING: {path} not found, skipping {algo_key}")
            continue
        with open(path) as f:
            data[algo_key] = json.load(f)
        print(f"  Loaded {algo_key}: {len(data[algo_key])} configurations")
    return data


def extract_best_per_algo(data):
    """
    For each algorithm, find the configuration with the best
    privacy-utility balance (lowest avg_location_error among configs
    with reasonable privacy, or overall best composite score).

    Returns: {algo_key: best_config_dict}
    """
    bests = {}
    for algo_key, configs in data.items():
        best = None
        best_score = -math.inf
        for cfg_key, metrics in configs.items():
            err = metrics.get("avg_location_error", math.inf)
            # Simple composite: lower error is better
            # We pick the config closest to a balanced operating point
            score = -err  # minimise error as a simple heuristic
            if score > best_score:
                best_score = score
                best = dict(metrics)
                best["config_key"] = cfg_key
        if best is not None:
            bests[algo_key] = best
    return bests


def extract_representative(data):
    """
    For each algorithm, extract a representative set of results
    for the most common time window (10 min / 600s) to allow
    fair cross-algorithm comparison.

    Returns: {algo_key: metrics_dict} for the representative config.
    """
    reps = {}
    for algo_key, configs in data.items():
        # Try to find a mid-range config (e.g., window=600)
        candidates = []
        for cfg_key, metrics in configs.items():
            candidates.append(metrics)

        if not candidates:
            continue

        # Pick the config with window_sec=600 if available, else median error
        w600 = [c for c in candidates if c.get("window_sec") == 600]
        if w600:
            # Among w600 configs, pick the one with median error
            w600.sort(key=lambda x: x.get("avg_location_error", math.inf))
            reps[algo_key] = w600[len(w600) // 2]
        else:
            candidates.sort(key=lambda x: x.get("avg_location_error", math.inf))
            reps[algo_key] = candidates[len(candidates) // 2]

    return reps


# -----------------------------------------------------------------------
# Figure 1 -- Bar Chart: Avg Location Error across Algorithms
# -----------------------------------------------------------------------
def fig_error_comparison(reps):
    print("  Generating: avg error comparison bar chart...")
    algos = [a for a in ALGORITHMS if a in reps]
    labels = [ALGORITHMS[a] for a in algos]
    errors = [reps[a]["avg_location_error"] for a in algos]
    colors = [ALGO_COLORS[a] for a in algos]

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(algos))
    bars = ax.bar(x, errors, color=colors, alpha=0.85, edgecolor="black",
                  linewidth=0.6)

    # Add value labels on bars
    for bar, val in zip(bars, errors):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20,
                f"{val:.0f} m", ha="center", va="bottom", fontsize=10,
                fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel("Avg Location Error (metres)")
    ax.set_title("Location Error Comparison Across Privacy Algorithms")
    ax.grid(True, alpha=0.3, axis="y")

    path = os.path.join(FIG_DIR, "fig1_error_comparison.png")
    plt.savefig(path); plt.close()
    _copy_to_paper(path)
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 2 -- Privacy-Utility Tradeoff (all algorithms on one plot)
# -----------------------------------------------------------------------
def fig_privacy_utility_all(data):
    print("  Generating: cross-algorithm privacy-utility tradeoff...")
    fig, ax = plt.subplots(figsize=(9, 6))

    for algo_key, configs in data.items():
        if algo_key not in ALGORITHMS:
            continue
        label = ALGORITHMS[algo_key]
        color = ALGO_COLORS[algo_key]

        points = []
        for cfg_key, metrics in configs.items():
            err = metrics.get("avg_location_error", None)
            if err is None:
                continue

            # Privacy gain proxy depends on algorithm type
            if "avg_region_size" in metrics:
                priv = metrics["avg_region_size"]
            elif "epsilon" in metrics:
                priv = 1.0 / metrics["epsilon"] * 100  # scaled
            elif "avg_group_size" in metrics:
                priv = metrics["avg_group_size"] * 10  # scaled
            else:
                priv = 50  # neutral

            util = 1.0 / (1.0 + err)
            points.append((priv, util))

        if not points:
            continue

        privs, utils = zip(*points)
        ax.scatter(privs, utils, c=color, s=60, alpha=0.7, label=label,
                   edgecolors="black", linewidths=0.4)

    ax.set_xlabel("Privacy Gain (algorithm-specific proxy)")
    ax.set_ylabel("Utility Score  1/(1 + location error)")
    ax.set_title("Privacy–Utility Tradeoff — All Algorithms")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.35)

    path = os.path.join(FIG_DIR, "fig2_privacy_utility_all.png")
    plt.savefig(path); plt.close()
    _copy_to_paper(path)
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 3 -- Radar / Spider Chart: Multi-Metric Comparison
# -----------------------------------------------------------------------
def fig_radar(reps):
    print("  Generating: radar chart...")
    algos = [a for a in ALGORITHMS if a in reps]
    if len(algos) < 2:
        print("    Skipping radar: need >= 2 algorithms.")
        return

    # Metrics for radar (normalise to [0, 1] range)
    metric_keys = ["avg_location_error", "p95_location_error",
                    "avg_temporal_jump"]
    metric_labels = ["Avg Error", "P95 Error", "Temporal Jump"]

    # Collect raw values
    raw = {a: [] for a in algos}
    for mk in metric_keys:
        vals = [reps[a].get(mk, 0) for a in algos]
        for a, v in zip(algos, vals):
            raw[a].append(v)

    # Normalise: for error metrics, lower is better → invert
    maxvals = [max(reps[a].get(mk, 0) for a in algos) or 1
               for mk in metric_keys]
    normalised = {}
    for a in algos:
        normalised[a] = [1.0 - (raw[a][i] / maxvals[i])
                         for i in range(len(metric_keys))]

    N = len(metric_keys)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    for a in algos:
        vals = normalised[a] + normalised[a][:1]
        ax.plot(angles, vals, "o-", linewidth=2, color=ALGO_COLORS[a],
                label=ALGORITHMS[a])
        ax.fill(angles, vals, alpha=0.1, color=ALGO_COLORS[a])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_labels)
    ax.set_ylim(0, 1.1)
    ax.set_title("Multi-Metric Comparison (higher = better)", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    path = os.path.join(FIG_DIR, "fig3_radar.png")
    plt.savefig(path); plt.close()
    _copy_to_paper(path)
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Figure 4 -- Grouped Bar: P50 and P95 Errors
# -----------------------------------------------------------------------
def fig_percentile_comparison(reps):
    print("  Generating: percentile comparison...")
    algos = [a for a in ALGORITHMS if a in reps]
    labels = [ALGORITHMS[a] for a in algos]
    p50 = [reps[a].get("p50_location_error", 0) for a in algos]
    p95 = [reps[a].get("p95_location_error", 0) for a in algos]

    x = np.arange(len(algos))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - width / 2, p50, width, label="Median (P50)",
           color="#4c72b0", edgecolor="black", linewidth=0.5)
    ax.bar(x + width / 2, p95, width, label="95th Percentile (P95)",
           color="#dd8452", edgecolor="black", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel("Location Error (metres)")
    ax.set_title("Median and P95 Location Error — Algorithm Comparison")
    ax.legend(); ax.grid(True, alpha=0.3, axis="y")

    path = os.path.join(FIG_DIR, "fig4_percentile_comparison.png")
    plt.savefig(path); plt.close()
    _copy_to_paper(path)
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# LaTeX Table
# -----------------------------------------------------------------------
def write_latex_table(reps):
    print("  Generating: LaTeX comparison table...")
    algos = [a for a in ALGORITHMS if a in reps]

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Cross-Algorithm Comparison — Representative Configuration}",
        r"\label{tab:comparison}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Algorithm & Avg Error (m) & P50 (m) & P95 (m) & Temp Jump (m) \\",
        r"\midrule",
    ]
    for a in algos:
        r = reps[a]
        lines.append(
            f"  {ALGORITHMS[a]} "
            f"& {r.get('avg_location_error', 0):.1f} "
            f"& {r.get('p50_location_error', 0):.1f} "
            f"& {r.get('p95_location_error', 0):.1f} "
            f"& {r.get('avg_temporal_jump', 0):.1f} \\\\")
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]

    path = os.path.join(PAPER_TABLE, "comparison_table.tex")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Markdown Report
# -----------------------------------------------------------------------
def write_report(reps, data):
    print("  Generating: comparison report...")
    algos = [a for a in ALGORITHMS if a in reps]

    lines = [
        "# Cross-Algorithm Evaluation Report\n\n",
        "## Representative Configuration Comparison\n\n",
        "| Algorithm | Avg Error (m) | Median (m) | P95 (m) |"
        " Temporal Jump (m) | Config |\n",
        "|-----------|---------------|------------|---------|"
        "-------------------|--------|\n",
    ]
    for a in algos:
        r = reps[a]
        cfg = r.get("config_key", r.get("window_label", "—"))
        lines.append(
            f"| {ALGORITHMS[a]} "
            f"| {r.get('avg_location_error', 0):.1f} "
            f"| {r.get('p50_location_error', 0):.1f} "
            f"| {r.get('p95_location_error', 0):.1f} "
            f"| {r.get('avg_temporal_jump', 0):.1f} "
            f"| {cfg} |\n")

    # Ranking
    ranked = sorted(algos, key=lambda a: reps[a].get("avg_location_error", math.inf))
    lines += [
        "\n## Ranking by Avg Location Error (lower = better utility)\n\n",
    ]
    for i, a in enumerate(ranked, 1):
        lines.append(
            f"{i}. **{ALGORITHMS[a]}** — "
            f"{reps[a].get('avg_location_error', 0):.1f} m\n")

    # Key findings
    best_a = ranked[0]
    worst_a = ranked[-1]
    lines += [
        "\n## Key Findings\n\n",
        f"- **Lowest error**: {ALGORITHMS[best_a]} "
        f"({reps[best_a].get('avg_location_error', 0):.1f} m)\n",
        f"- **Highest error**: {ALGORITHMS[worst_a]} "
        f"({reps[worst_a].get('avg_location_error', 0):.1f} m)\n",
        f"- Total configurations evaluated: "
        f"{sum(len(v) for v in data.values())}\n",
    ]

    path = os.path.join(EVAL_DIR, "comparison_report.md")
    with open(path, "w") as f:
        f.writelines(lines)
    print(f"    Saved: {path}")


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------
def _copy_to_paper(src_path):
    """Copy a figure to the paper/figures directory."""
    import shutil
    dst = os.path.join(PAPER_FIG, os.path.basename(src_path))
    shutil.copy2(src_path, dst)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
def run():
    for d in [EVAL_DIR, FIG_DIR, PAPER_FIG, PAPER_TABLE]:
        os.makedirs(d, exist_ok=True)

    print("=" * 70)
    print("  CROSS-ALGORITHM EVALUATION")
    print("=" * 70)

    print("\nLoading results from all algorithms...")
    data = load_all_results()

    if not data:
        print("ERROR: No results found. Run run_all.py first.")
        return

    reps = extract_representative(data)
    print(f"\n  Representative configs loaded for {len(reps)} algorithms.\n")

    # Generate comparative outputs
    print("=== Comparative Figures ===")
    fig_error_comparison(reps)
    fig_privacy_utility_all(data)
    fig_radar(reps)
    fig_percentile_comparison(reps)

    print("\n=== Tables and Reports ===")
    write_latex_table(reps)
    write_report(reps, data)

    print(f"\n{'=' * 70}")
    print(f"  Evaluation complete.")
    print(f"  Figures -> {FIG_DIR}")
    print(f"  Report  -> {EVAL_DIR}/comparison_report.md")
    print(f"  Paper   -> {PAPER_FIG}, {PAPER_TABLE}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run()
