"""
Cross-Topology / Cross-Dataset Comparison
=========================================

Capstone for reviewer critiques D (grid vs real road network) and E (single
dataset).  Merges three evaluation settings into one comparison so we can state
directly whether the mechanism rankings hold:

  1. GeoLife / 30x30 grid          (evaluation/unified/table_unified.csv)
  2. GeoLife / real OSM graph      (evaluation/real_graph/real_metrics.json)
  3. T-Drive  / real OSM graph     (evaluation/real_graph_tdrive/real_metrics.json)

Outputs:
  evaluation/cross_comparison/table_cross.md
  evaluation/cross_comparison/fig_cross_topology.png   (availability + error + privacy)
  evaluation/cross_comparison/ranking_stability.md
"""

import os
import csv
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
OUT = os.path.join(_HERE, "cross_comparison")
PAPER_FIG = os.path.join(_ROOT, "paper", "figures")
os.makedirs(OUT, exist_ok=True)

ORDER = ["k_anonymity", "differential_privacy", "graph_constrained_dp",
         "density_aware_k_anonymity", "temporal_cloaking", "adaptive_hybrid", "mirage"]
NAMES = {"k_anonymity": "k-Anonymity", "differential_privacy": "Differential Privacy",
         "graph_constrained_dp": "Graph-Constrained DP",
         "density_aware_k_anonymity": "Density-Aware k-Anon",
         "temporal_cloaking": "Temporal Cloaking", "adaptive_hybrid": "DA-Hybrid (ours)",
         "mirage": "MIRAGE (ours)"}
NAME_TO_KEY = {v: k for k, v in NAMES.items()}


def load_grid():
    p = os.path.join(_HERE, "unified", "table_unified.csv")
    if not os.path.exists(p):
        return {}
    out = {}
    with open(p) as f:
        for row in csv.DictReader(f):
            key = NAME_TO_KEY.get(row["mechanism"])
            if key:
                out[key] = {"snap_AE": float(row["snapshot_AE_m"]),
                            "traj_AE": float(row["trajectory_AE_m"]),
                            "avail": float(row["availability"]),
                            "error": float(row["location_error_m"])}
    return out


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        d = json.load(f)
    return {k: {"snap_AE": v["snap_AE"], "traj_AE": v["traj_AE"],
                "avail": v["avail"], "error": v["error"]} for k, v in d.items()}


def run():
    settings = [
        ("GeoLife / grid", load_grid()),
        ("GeoLife / real", load_json(os.path.join(_HERE, "real_graph", "real_metrics.json"))),
        ("T-Drive / real", load_json(os.path.join(_HERE, "real_graph_tdrive", "real_metrics.json"))),
    ]
    settings = [(n, d) for n, d in settings if d]
    if not settings:
        print("No inputs found yet.")
        return

    # ---- combined table ----
    lines = ["# Cross-Topology / Cross-Dataset Comparison\n\n",
             "Location error (m) and availability across settings. "
             "Shows whether rankings hold when moving from the grid abstraction "
             "to a real road network, and from GeoLife to T-Drive.\n\n"]
    header = "| Mechanism | " + " | ".join(f"{n} err / avail" for n, _ in settings) + " |\n"
    lines += [header, "|" + "---|" * (1 + len(settings)) + "\n"]
    for k in ORDER:
        cells = [NAMES[k]]
        for _, d in settings:
            if k in d:
                cells.append(f"{d[k]['error']:.0f} / {d[k]['avail']:.0%}")
            else:
                cells.append("—")
        lines.append("| " + " | ".join(cells) + " |\n")
    with open(os.path.join(OUT, "table_cross.md"), "w") as f:
        f.writelines(lines)

    # ---- ranking stability ----
    rlines = ["# Ranking stability across settings\n\n"]
    for metric, better in [("error", "lower"), ("avail", "higher"), ("snap_AE", "higher")]:
        rlines.append(f"\n## By {metric} ({better} = better)\n\n")
        for n, d in settings:
            rev = (better == "higher")
            ranked = sorted([k for k in ORDER if k in d],
                            key=lambda k: d[k][metric], reverse=rev)
            rlines.append(f"- **{n}**: " + " > ".join(NAMES[k] for k in ranked) + "\n")
    with open(os.path.join(OUT, "ranking_stability.md"), "w") as f:
        f.writelines(rlines)

    # ---- figure: availability and error grouped by setting ----
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    keys = [k for k in ORDER if any(k in d for _, d in settings)]
    x = np.arange(len(keys))
    w = 0.8 / len(settings)
    for i, (n, d) in enumerate(settings):
        av = [d.get(k, {}).get("avail", np.nan) * 100 for k in keys]
        er = [d.get(k, {}).get("error", np.nan) for k in keys]
        axes[0].bar(x + i * w, av, w, label=n)
        axes[1].bar(x + i * w, er, w, label=n)
    for ax, ttl, yl in [(axes[0], "Availability across topology/dataset", "Availability (%)"),
                        (axes[1], "Location error across topology/dataset", "Location error (m)")]:
        ax.set_xticks(x + w * (len(settings) - 1) / 2)
        ax.set_xticklabels([NAMES[k].replace(" ", "\n") for k in keys], fontsize=8)
        ax.set_title(ttl)
        ax.set_ylabel(yl)
        ax.legend(fontsize=8)
        ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    for dst in (os.path.join(OUT, "fig_cross_topology.png"),
                os.path.join(PAPER_FIG, "fig_cross_topology.png")):
        plt.savefig(dst, dpi=300)
    plt.close()
    print(f"Cross comparison -> {OUT} ({len(settings)} settings)")


if __name__ == "__main__":
    run()
