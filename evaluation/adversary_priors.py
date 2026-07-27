"""
Adversary Background Knowledge: Population Prior and Mobility Model
==================================================================

The privacy of a location-obfuscation mechanism is only meaningful relative
to an *adversary* who tries to invert it.  Following the standard evaluation
framework of Shokri et al. [1], a strong adversary is equipped with two pieces
of public background knowledge, both estimated here from the trajectory
dataset itself:

  1. A *population prior*  pi(v)  -- the marginal probability that an arbitrary
     user is located at node v.  This is the adversary's belief about where
     people are before observing any report.  Estimated as the normalised
     occupancy histogram over all trajectory records.

  2. A *mobility model*  P(v_{t+1} | v_t)  -- a first-order Markov transition
     matrix capturing how users move between adjacent time steps.  This is the
     background knowledge a *trajectory* adversary exploits to track a user
     across a sequence of anonymised reports (Xiao & Xiong [2]).

Both are expensive to estimate (one pass over ~16.9M records) so they are
cached to disk (`evaluation/cache/`) and reused across all mechanisms.

References
----------
[1] R. Shokri, G. Theodorakopoulos, J.-Y. Le Boudec, and J.-P. Hubaux,
    "Quantifying Location Privacy," IEEE S&P, 2011.
[2] Y. Xiao and L. Xiong, "Protecting Locations with Differential Privacy
    under Temporal Correlations," ACM CCS, 2015.
"""

import os
import csv
import json
import numpy as np

_HERE      = os.path.dirname(os.path.abspath(__file__))
_BASE      = os.path.join(_HERE, "..")
_DATA      = os.path.join(_BASE, "data", "processed_data")
_CACHE     = os.path.join(_HERE, "cache")

NODES_FILE = os.path.join(_DATA, "city_graph_nodes.json")


def load_node_index(nodes_file=NODES_FILE):
    """
    Return (node_ids, id_to_idx, coords) where
      node_ids  : list[str]            -- canonical node ordering
      id_to_idx : dict[str -> int]     -- inverse map
      coords    : np.ndarray (N, 2)    -- (lon, lat) per node index
    """
    with open(nodes_file) as f:
        nodes = json.load(f)
    node_ids = [str(n["id"]) for n in nodes]
    id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    coords = np.array([[float(n["x"]), float(n["y"])] for n in nodes],
                      dtype=float)
    return node_ids, id_to_idx, coords


def estimate_prior_and_transitions(csv_file, node_ids, id_to_idx,
                                   cache_tag="geolife", rebuild=False,
                                   laplace_smoothing=1.0):
    """
    Estimate the population prior pi(v) and first-order Markov transition
    matrix T[v, w] = P(next=w | cur=v) from a device_locations.csv file.

    The CSV is assumed sorted by (user_id, date, time) -- as produced by
    process_geolife.py -- so consecutive rows of the same user are adjacent
    in time and give one transition each.

    Parameters
    ----------
    csv_file : str   -- path to device_locations.csv (cols: user_id, location_id, date, time)
    node_ids : list  -- canonical node ordering from load_node_index
    id_to_idx: dict
    cache_tag: str   -- distinguishes datasets (e.g. "geolife", "tdrive")
    rebuild  : bool  -- force re-computation even if a cache exists
    laplace_smoothing : float -- additive smoothing on transition counts so the
                                 adversary never assigns probability 0 to a move.

    Returns
    -------
    prior : np.ndarray (N,)     -- normalised occupancy distribution
    T     : np.ndarray (N, N)   -- row-stochastic transition matrix
    """
    os.makedirs(_CACHE, exist_ok=True)
    prior_path = os.path.join(_CACHE, f"prior_{cache_tag}.npy")
    trans_path = os.path.join(_CACHE, f"transitions_{cache_tag}.npy")

    if not rebuild and os.path.exists(prior_path) and os.path.exists(trans_path):
        prior = np.load(prior_path)
        T = np.load(trans_path)
        if prior.shape[0] == len(node_ids) and T.shape[0] == len(node_ids):
            return prior, T

    N = len(node_ids)
    counts = np.zeros(N, dtype=np.float64)
    trans = np.zeros((N, N), dtype=np.float64)

    prev_user, prev_idx = None, None
    n_rows = 0
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            nid = str(row["location_id"])
            idx = id_to_idx.get(nid)
            if idx is None:
                prev_user, prev_idx = row["user_id"], None
                continue
            counts[idx] += 1.0
            user = row["user_id"]
            if user == prev_user and prev_idx is not None:
                trans[prev_idx, idx] += 1.0
            prev_user, prev_idx = user, idx
            n_rows += 1
            if n_rows % 4_000_000 == 0:
                print(f"    prior/transitions: {n_rows:,} rows")

    # Population prior (occupancy), with tiny floor so no node is impossible.
    prior = counts + 1e-9
    prior /= prior.sum()

    # Row-stochastic transition matrix with Laplace smoothing.
    trans += laplace_smoothing
    row_sums = trans.sum(axis=1, keepdims=True)
    T = trans / row_sums

    np.save(prior_path, prior)
    np.save(trans_path, T)
    print(f"    prior/transitions cached ({n_rows:,} rows, {N} nodes) -> {_CACHE}")
    return prior, T


if __name__ == "__main__":
    # Smoke test / cache warmer.
    node_ids, id_to_idx, coords = load_node_index()
    csv_file = os.path.join(_DATA, "device_locations.csv")
    prior, T = estimate_prior_and_transitions(csv_file, node_ids, id_to_idx,
                                              rebuild=True)
    print("nodes:", len(node_ids))
    print("prior sum:", prior.sum(), "top-5 occupancy nodes:",
          np.argsort(prior)[::-1][:5].tolist())
    print("transition rows stochastic:", np.allclose(T.sum(axis=1), 1.0))
    print("mean self-transition prob:", float(np.mean(np.diag(T))))
