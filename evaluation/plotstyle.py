"""
Unified publication figure style (colorblind-safe).
Palette: Okabe--Ito (designed for colour-vision deficiency), each hue paired with
a distinct marker shape as secondary encoding, per accessibility best practice.
Import apply_style() and use PALETTE / MARKERS / LABEL by mechanism key.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt

# Okabe--Ito, assigned in fixed order (never cycled). MIRAGE = vermillion (star).
PALETTE = {
    "mirage":   "#D55E00",  # vermillion  (ours)
    "mirage_t": "#E69F00",  # orange      (trajectory variant)
    "dp":       "#0072B2",  # blue
    "kanon":    "#009E73",  # bluish green
    "gcdp":     "#56B4E9",  # sky blue
    "density":  "#E69F00",  # orange
    "temporal": "#CC79A7",  # reddish purple
    "hybrid":   "#000000",  # black
    "global":   "#000000",  # black (reference optimum)
    "ideal":    "#999999",  # grey (guide line)
}
MARKERS = {
    "mirage": "*", "mirage_t": "P", "dp": "s", "kanon": "o", "gcdp": "^",
    "density": "D", "temporal": "X", "hybrid": "v", "global": "o",
}
LABEL = {
    "mirage": "MIRAGE (ours)", "mirage_t": "MIRAGE-T", "dp": "Differential Privacy",
    "kanon": "$k$-Anonymity", "gcdp": "Graph-Constrained DP",
    "density": "Density-Aware", "temporal": "Temporal Cloaking",
    "hybrid": "DA-Hybrid", "global": "Global optimum",
}


def apply_style():
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 12,
        "axes.titlesize": 13,
        "axes.labelsize": 12.5,
        "axes.titleweight": "bold",
        "legend.fontsize": 10,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.30,
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "lines.linewidth": 2.2,
        "lines.markersize": 8,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "legend.frameon": True,
        "legend.framealpha": 0.9,
        "legend.edgecolor": "0.8",
    })


def style_series(ax, key, **kw):
    """Convenience: default colour+marker+label for a mechanism key."""
    kw.setdefault("color", PALETTE.get(key, "#333333"))
    kw.setdefault("marker", MARKERS.get(key, "o"))
    kw.setdefault("label", LABEL.get(key, key))
    return kw
