"""
Unified Comparison: Adversary-Grounded Privacy, Availability, Utility, Energy
============================================================================

Produces the paper's headline comparison using the *new* metrics:
  * privacy   = expected Bayesian-adversary error (metres), under a snapshot
                adversary AND a trajectory adversary (attacker_models.py),
  * availability = fraction of reports served,
  * utility   = spatial location error (metres),
  * energy    = per-report energy under two radio technologies.

Figures
-------
  fig_dual_threat.png   snapshot vs trajectory adversary error (the core
                        "one privacy scale is inadequate" result)
  fig_pareto_privacy.png  privacy (adversary error) vs utility (location
                          error), with DA-Hybrid tracing the frontier
Tables
------
  table_unified.{md,tex,csv}   master comparison

All outputs are also copied to paper/figures and paper/tables.
"""

import os
import sys
import json
import shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
RESULT_BASE = os.path.join(_ROOT, "results")
OUT = os.path.join(_HERE, "unified")
PAPER_FIG = os.path.join(_ROOT, "paper", "figures")
PAPER_TABLE = os.path.join(_ROOT, "paper", "tables")
for d in (OUT, PAPER_FIG, PAPER_TABLE):
    os.makedirs(d, exist_ok=True)
sys.path.insert(0, _HERE)

from energy_sensitivity import compute_energy_mJ, radio_energy  # noqa: E402

BASELINE_N = {60: 888, 300: 945, 600: 1019, 900: 1019, 1200: 1085}

# (display name, representative config, on-graph output?, colour, marker)
MECHS = {
    "k_anonymity":               ("k-Anonymity",         "k3_w600",   True,  "#1f77b4", "o"),
    "differential_privacy":      ("Differential Privacy","eps1.0_w600", False, "#d62728", "s"),
    "graph_constrained_dp":      ("Graph-Constrained DP","eps1.0_w600", True,  "#2ca02c", "^"),
    "density_aware_k_anonymity": ("Density-Aware k-Anon","w600",       True,  "#ff7f0e", "D"),
    "temporal_cloaking":         ("Temporal Cloaking",   "k3_w600",   True,  "#9467bd", "P"),
    "adaptive_hybrid":           ("DA-Hybrid (ours)",    "k2_w600",   True,  "#17becf", "*"),
}


def _load(algo, fname):
    p = os.path.join(RESULT_BASE, algo, fname)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None


def _rep(cfgs, key):
    if cfgs is None:
        return None
    if key in cfgs:
        return cfgs[key]
    for v in cfgs.values():
        if v.get("window_sec") == 600:
            return v
    return next(iter(cfgs.values()), None)


def availability(metrics, algo):
    n = metrics.get("n_records", 0)
    base = BASELINE_N.get(metrics.get("window_sec", 600), 1019)
    sr = min(n / base, 1.0)
    if algo in ("differential_privacy", "graph_constrained_dp", "adaptive_hybrid"):
        return sr
    return sr * metrics.get("k_satisfaction_rate", 1.0)


def gather():
    rows = {}
    for algo, (name, cfg, ongraph, color, marker) in MECHS.items():
        res = _rep(_load(algo, "results.json"), cfg)
        adv = _rep(_load(algo, "adversary.json"), cfg)
        if res is None:
            continue
        rows[algo] = {
            "name": name, "ongraph": ongraph, "color": color, "marker": marker,
            "error": res.get("avg_location_error", float("nan")),
            "avail": availability(res, algo),
            "snap_AE": (adv or {}).get("snapshot_adv_error_m", float("nan")),
            "traj_AE": (adv or {}).get("trajectory_adv_error_m", float("nan")),
            "snap_reid": (adv or {}).get("snapshot_reid_rate", float("nan")),
            "traj_reid": (adv or {}).get("trajectory_reid_rate", float("nan")),
            "E_LoRa": radio_energy("LoRa") + compute_energy_mJ(res, algo),
            "E_BLE": radio_energy("BLE") + compute_energy_mJ(res, algo),
        }
    return rows


def write_table(rows):
    hdr = ("| Mechanism | Snapshot AE (m) | Trajectory AE (m) | Availability | "
           "Loc. Error (m) | On-graph | E LoRa (mJ) | E BLE (mJ) |\n")
    sep = "|" + "---|" * 8 + "\n"
    lines = ["# Unified Comparison (adversary-grounded privacy)\n\n",
             "Privacy is the expected error of an optimal Bayesian adversary "
             "(metres, higher=better) under snapshot and trajectory threat "
             "models. Representative configs at window=10 min.\n\n", hdr, sep]
    for algo, r in rows.items():
        lines.append(
            f"| {r['name']} | {r['snap_AE']:.0f} | {r['traj_AE']:.0f} | "
            f"{r['avail']:.1%} | {r['error']:.0f} | "
            f"{'yes' if r['ongraph'] else 'no'} | "
            f"{r['E_LoRa']:.2f} | {r['E_BLE']:.2f} |\n")
    with open(os.path.join(OUT, "table_unified.md"), "w") as f:
        f.writelines(lines)

    # LaTeX
    tex = [r"\begin{table*}[t]", r"\centering",
           r"\caption{Unified comparison under adversary-grounded privacy "
           r"(expected Bayesian-adversary error, metres; higher is more "
           r"private) for snapshot and trajectory threat models. "
           r"Window $=10$\,min.}",
           r"\label{tab:unified}",
           r"\begin{tabular}{lrrrrccc}", r"\toprule",
           r"Mechanism & Snap.\ AE & Traj.\ AE & Avail. & Loc.\ Err & "
           r"On-graph & $E_{\mathrm{LoRa}}$ & $E_{\mathrm{BLE}}$ \\",
           r" & (m) & (m) & & (m) & & (mJ) & (mJ) \\", r"\midrule"]
    for algo, r in rows.items():
        nm = r["name"].replace("DA-Hybrid (ours)", r"\textbf{DA-Hybrid (ours)}")
        tex.append(
            f"{nm} & {r['snap_AE']:.0f} & {r['traj_AE']:.0f} & {r['avail']*100:.0f}\\% & "
            f"{r['error']:.0f} & {'yes' if r['ongraph'] else 'no'} & "
            f"{r['E_LoRa']:.2f} & {r['E_BLE']:.2f} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    with open(os.path.join(OUT, "table_unified.tex"), "w") as f:
        f.write("\n".join(tex))
    shutil.copy2(os.path.join(OUT, "table_unified.tex"),
                 os.path.join(PAPER_TABLE, "table_unified.tex"))

    # CSV
    with open(os.path.join(OUT, "table_unified.csv"), "w") as f:
        f.write("mechanism,snapshot_AE_m,trajectory_AE_m,availability,"
                "location_error_m,on_graph,E_LoRa_mJ,E_BLE_mJ\n")
        for algo, r in rows.items():
            f.write(f"{r['name']},{r['snap_AE']:.1f},{r['traj_AE']:.1f},"
                    f"{r['avail']:.4f},{r['error']:.1f},{int(r['ongraph'])},"
                    f"{r['E_LoRa']:.4f},{r['E_BLE']:.4f}\n")


def fig_dual_threat(rows):
    fig, ax = plt.subplots(figsize=(7, 6))
    valid = {a: r for a, r in rows.items()
             if np.isfinite(r["snap_AE"]) and np.isfinite(r["traj_AE"])}
    mx = max(max(r["snap_AE"], r["traj_AE"]) for r in valid.values()) * 1.1
    ax.plot([0, mx], [0, mx], "--", color="gray", alpha=0.6, zorder=1)
    ax.text(mx * 0.55, mx * 0.5, "equal privacy\nunder both threats",
            color="gray", fontsize=8, rotation=45, ha="center")
    for a, r in valid.items():
        ax.scatter(r["snap_AE"], r["traj_AE"], s=260 if a == "adaptive_hybrid" else 150,
                   c=r["color"], marker=r["marker"], edgecolors="black",
                   linewidths=0.8, zorder=3, label=r["name"])
        ax.annotate(r["name"], (r["snap_AE"], r["traj_AE"]),
                    textcoords="offset points", xytext=(7, 5), fontsize=8)
    ax.set_xlabel("Snapshot adversary error (m)  —  privacy vs. single-observation attack")
    ax.set_ylabel("Trajectory adversary error (m)  —  privacy vs. tracking attack")
    ax.set_title("Privacy is threat-model-dependent:\nmechanisms rank differently under the two adversaries")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    plt.tight_layout()
    for dst in (os.path.join(OUT, "fig_dual_threat.png"),
                os.path.join(PAPER_FIG, "fig_dual_threat.png")):
        plt.savefig(dst, dpi=300)
    plt.close()


def fig_pareto(rows):
    """Privacy (snapshot adversary error) vs utility (location error).
    Ideal = lower-right (high privacy, low error). Marker size ~ availability."""
    fig, ax = plt.subplots(figsize=(8, 6))
    for a, r in rows.items():
        if not np.isfinite(r["snap_AE"]):
            continue
        size = 80 + 400 * r["avail"]
        ax.scatter(r["snap_AE"], r["error"], s=size, c=r["color"],
                   marker=r["marker"], edgecolors="black", linewidths=0.8,
                   alpha=0.9, zorder=3, label=r["name"])
        ax.annotate(r["name"], (r["snap_AE"], r["error"]),
                    textcoords="offset points", xytext=(7, 4), fontsize=8)

    # DA-Hybrid frontier across its k sweep.
    hy = _load("adaptive_hybrid", "results.json")
    hy_adv = _load("adaptive_hybrid", "adversary.json")
    if hy and hy_adv:
        pts = []
        for k in [2, 3, 4, 5]:
            key = f"k{k}_w600"
            if key in hy and key in hy_adv:
                pts.append((hy_adv[key].get("snapshot_adv_error_m"),
                            hy[key]["avg_location_error"]))
        pts = [p for p in pts if p[0] is not None]
        if len(pts) > 1:
            pts.sort()
            xs, ys = zip(*pts)
            ax.plot(xs, ys, ":", color="#17becf", lw=1.8, zorder=2,
                    label="DA-Hybrid frontier (k=2..5)")
    ax.set_xlabel("Privacy: snapshot adversary error (m) — higher is better →")
    ax.set_ylabel("Utility loss: location error (m) — lower is better ↓")
    ax.set_title("Privacy–Utility frontier (marker size ∝ availability)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")
    plt.tight_layout()
    for dst in (os.path.join(OUT, "fig_pareto_privacy.png"),
                os.path.join(PAPER_FIG, "fig_pareto_privacy.png")):
        plt.savefig(dst, dpi=300)
    plt.close()


def run():
    rows = gather()
    if not rows:
        print("No results found.")
        return
    write_table(rows)
    fig_dual_threat(rows)
    fig_pareto(rows)
    print(f"Unified comparison -> {OUT} (+ paper/)")
    print("\nMechanism            snapAE  trajAE  avail  error")
    for a, r in rows.items():
        print(f"  {r['name']:22s} {r['snap_AE']:6.0f} {r['traj_AE']:6.0f} "
              f"{r['avail']:5.0%} {r['error']:6.0f}")


if __name__ == "__main__":
    run()
