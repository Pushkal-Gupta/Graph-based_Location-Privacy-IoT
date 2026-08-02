"""
Regenerate ALL paper figures through the unified publication style.
Reads saved result JSON/CSV so no heavy recompute is needed. Writes both to
evaluation/mirage/ (or source dirs) and paper/manuscript*/figures/.
"""
import os, sys, json, csv, numpy as np
_HERE = os.path.dirname(os.path.abspath(__file__)); _BASE = os.path.join(_HERE, "..")
_MIR = os.path.join(_HERE, "mirage"); _RES = os.path.join(_BASE, "results")
sys.path.insert(0, _HERE)
from plotstyle import apply_style, PALETTE, MARKERS, LABEL; apply_style()
import matplotlib.pyplot as plt

FIGDIRS = [os.path.join(_BASE, "paper", "manuscript", "figures"),
           os.path.join(_BASE, "paper", "manuscript_springer", "figures"),
           os.path.join(_BASE, "paper", "figures")]


def save(fig, name):
    for d in FIGDIRS:
        os.makedirs(d, exist_ok=True)
        fig.savefig(os.path.join(d, name), dpi=300, bbox_inches="tight")
    plt.close(fig)


def _load(p):
    return json.load(open(p)) if os.path.exists(p) else None


# ---------- frontier (x3) ----------
def frontier(ds, title):
    fr = _load(os.path.join(_MIR, f"frontier_{ds}.json"))
    if not fr: return
    fig, ax = plt.subplots(figsize=(6.8, 5.0))
    for key in ["mirage", "dp", "kanon"]:
        pts = sorted(fr[key], key=lambda r: r["util"])
        u = [p["util"] for p in pts]; pr = [p["priv"] for p in pts]
        lo = [max(0, p["priv"]-p["priv_lo"]) for p in pts]; hi = [max(0, p["priv_hi"]-p["priv"]) for p in pts]
        ax.errorbar(u, pr, yerr=[lo, hi], marker=MARKERS[key], color=PALETTE[key], capsize=3,
                    ms=13 if key == "mirage" else 8, label=LABEL[key], zorder=3 if key == "mirage" else 2)
    hi = max(max(p["util"] for p in fr["mirage"]), max(p["priv"] for p in fr["mirage"]))
    ax.plot([0, hi], [0, hi], ":", color=PALETTE["ideal"], label="privacy = utility (ideal)")
    ax.set_xlabel("Utility loss: expected distortion (m)")
    ax.set_ylabel("Privacy: optimal-adversary error (m)")
    ax.set_title(f"Privacy--utility frontier: {title}")
    ax.legend(loc="lower right")
    save(fig, f"fig_frontier_{ds}.png")


# ---------- trajectory (x2) ----------
def trajectory(ds, title):
    tr = _load(os.path.join(_MIR, f"trajectory_{ds}.json"))
    if not tr: return
    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    for key, lbl in [("snapshot", "snapshot-MIRAGE"), ("mirage_t", "MIRAGE-T (trajectory-aware)"),
                     ("dp", "Differential Privacy")]:
        pts = sorted(tr[key], key=lambda r: r["util"])
        if not pts: continue
        col = PALETTE["mirage"] if key == "snapshot" else PALETTE.get(key, PALETTE["mirage_t"])
        mk = "s" if key == "snapshot" else MARKERS.get(key, "*")
        ax.plot([p["util"] for p in pts], [p["traj_priv"] for p in pts], marker=mk, color=col,
                ms=13 if key == "mirage_t" else 8, label=lbl)
    ax.set_xlabel("Utility loss: distortion (m)")
    ax.set_ylabel("Trajectory-adversary tracking error (m)")
    ax.set_title(f"Trajectory privacy vs the sequential adversary: {title}")
    ax.legend(loc="lower right")
    save(fig, f"fig_trajectory_{ds}.png")


# ---------- dual-threat (grid) ----------
def dual_threat():
    keys = [("k_anonymity", "kanon"), ("differential_privacy", "dp"),
            ("graph_constrained_dp", "gcdp"), ("density_aware_k_anonymity", "density"),
            ("temporal_cloaking", "temporal"), ("adaptive_hybrid", "hybrid")]
    pts = {}
    for algo, pk in keys:
        d = _load(os.path.join(_RES, algo, "adversary.json"))
        if not d: continue
        m = next(iter(d.values()))
        if "snapshot_adv_error_m" in m and "trajectory_adv_error_m" in m:
            pts[pk] = (m["snapshot_adv_error_m"], m["trajectory_adv_error_m"])
    if not pts: return
    fig, ax = plt.subplots(figsize=(6.8, 6.0))
    mx = max(max(v) for v in pts.values()) * 1.1
    ax.plot([0, mx], [0, mx], ":", color=PALETTE["ideal"], label="equal under both threats")
    for pk, (x, y) in pts.items():
        ax.scatter(x, y, s=170, c=PALETTE.get(pk, "#333"), marker=MARKERS.get(pk, "o"),
                   edgecolors="black", linewidths=0.8, zorder=3, label=LABEL.get(pk, pk))
    ax.set_xlabel("Snapshot adversary error (m) --- single-observation attack")
    ax.set_ylabel("Trajectory adversary error (m) --- tracking attack")
    ax.set_title("Privacy is threat-model dependent")
    ax.legend(fontsize=8, loc="lower right")
    save(fig, "fig_dual_threat.png")


# ---------- cross-topology bars ----------
def cross_topology():
    settings = [("GeoLife / grid", None), ("GeoLife / real", "real_graph"),
                ("T-Drive / real", "real_graph_tdrive")]
    order = [("k_anonymity", "kanon"), ("differential_privacy", "dp"),
             ("graph_constrained_dp", "gcdp"), ("density_aware_k_anonymity", "density"),
             ("temporal_cloaking", "temporal"), ("adaptive_hybrid", "hybrid"), ("mirage", "mirage")]
    data = {}
    # grid from unified csv
    up = os.path.join(_HERE, "unified", "table_unified.csv")
    grid = {}
    if os.path.exists(up):
        for row in csv.DictReader(open(up)):
            grid[row["mechanism"]] = (float(row["location_error_m"]), float(row["availability"]))
    name2algo = {"k-Anonymity": "k_anonymity", "Differential Privacy": "differential_privacy",
                 "Graph-Constrained DP": "graph_constrained_dp", "Density-Aware k-Anon": "density_aware_k_anonymity",
                 "Temporal Cloaking": "temporal_cloaking", "DA-Hybrid (ours)": "adaptive_hybrid"}
    data["GeoLife / grid"] = {name2algo.get(k, k): v for k, v in grid.items()}
    for label, sub in settings[1:]:
        d = _load(os.path.join(_HERE, sub, "real_metrics.json")) or {}
        data[label] = {a: (m["error"], m["avail"]) for a, m in d.items()}
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    keys = [k for k, _ in order]
    x = np.arange(len(keys)); w = 0.8/len(data)
    cols = ["#0072B2", "#D55E00", "#009E73"]
    for i, (label, dd) in enumerate(data.items()):
        av = [dd.get(k, (np.nan, np.nan))[1]*100 for k in keys]
        er = [dd.get(k, (np.nan, np.nan))[0] for k in keys]
        axes[0].bar(x+i*w, av, w, label=label, color=cols[i % 3])
        axes[1].bar(x+i*w, er, w, label=label, color=cols[i % 3])
    labs = [LABEL.get(pk, a).replace(" ", "\n") for a, pk in order]
    for ax, ttl, yl in [(axes[0], "Availability", "Availability (%)"), (axes[1], "Location error", "Error (m)")]:
        ax.set_xticks(x+w); ax.set_xticklabels(labs, fontsize=8); ax.set_title(ttl); ax.set_ylabel(yl)
        ax.legend(fontsize=8); ax.grid(True, axis="y", alpha=0.3)
    save(fig, "fig_cross_topology.png")


# ---------- energy ----------
def energy():
    p = os.path.join(_HERE, "energy_sensitivity", "table_energy_sensitivity.csv")
    if not os.path.exists(p): return
    rows = list(csv.DictReader(open(p)))
    radios = ["BLE", "Zigbee", "LoRa", "NB-IoT", "LTE-M"]
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    pkmap = {"k-Anonymity": "kanon", "Differential Privacy": "dp", "Graph-Constrained DP": "gcdp",
             "Density-Aware k-Anon": "density", "Temporal Cloaking": "temporal", "DA-Hybrid (ours)": "hybrid"}
    x = np.arange(len(radios))
    for row in rows:
        pk = pkmap.get(row["mechanism"], "hybrid")
        fr = [float(row[f"{r}_radio_frac"])*100 for r in radios]
        ax.plot(x, fr, marker=MARKERS.get(pk, "o"), color=PALETTE.get(pk, "#333"), label=row["mechanism"])
    ax.axhline(98, ls="--", color=PALETTE["ideal"])
    ax.set_xticks(x); ax.set_xticklabels(radios); ax.set_ylim(0, 105)
    ax.set_xlabel("Radio technology (increasing transmit energy)"); ax.set_ylabel("Radio share of per-report energy (%)")
    ax.set_title("Radio dominance is radio-dependent, not universal")
    ax.legend(fontsize=8, loc="lower right")
    save(fig, "fig_energy_sensitivity.png")


# ---------- mobility gap (3 cities) ----------
def mobility():
    pts = [("GeoLife", 0.788, 20, "#0072B2"), ("T-Drive", 0.835, 15, "#009E73"), ("Porto", 0.867, 10, "#D55E00")]
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    xs = [p[1] for p in pts]; ys = [p[2] for p in pts]
    for name, x, y, c in pts:
        ax.scatter(x, y, s=200, c=c, edgecolors="black", zorder=3)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(9, 5), fontsize=12)
    b = np.polyfit(xs, ys, 1); xr = np.linspace(min(xs), max(xs), 10)
    ax.plot(xr, np.polyval(b, xr), "--", color=PALETTE["ideal"])
    ax.set_xlabel("Within-region prior entropy (normalised)"); ax.set_ylabel("MIRAGE gain over best heuristic (%)")
    ax.set_title("The optimal-mechanism advantage tracks prior heterogeneity")
    save(fig, "fig_mobility_gap.png")


def main():
    frontier("geolife_real", "GeoLife, Beijing")
    frontier("tdrive_real", "T-Drive, Beijing")
    frontier("porto_real", "Porto, Portugal")
    trajectory("geolife_real", "GeoLife (stationary)")
    trajectory("tdrive_real", "T-Drive (mobile)")
    dual_threat(); cross_topology(); energy(); mobility()
    print("All figures regenerated with unified style.")


if __name__ == "__main__":
    main()
