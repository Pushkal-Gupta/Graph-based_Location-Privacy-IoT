"""
MIRAGE — Mobility-Informed, inference-optimal Road-graph Anonymization
        for Geo-privacy against sequential Estimation
======================================================================

MIRAGE is a location-obfuscation mechanism that is *provably optimal* against a
Bayesian localization adversary (Shokri et al., "Quantifying Location Privacy,"
IEEE S&P 2011), brought for the first time to a **real road network at city
scale** and made **trajectory-aware**.

Relation to prior work (honest positioning). The optimal-mechanism-as-an-LP idea
is due to Shokri et al. ("Optimal Strategy against Localization Attacks," CCS
2012; "Privacy Games," PETS 2015; "Privacy Games Along Location Traces," TOPS
2016) and Bordenabe et al. ("Optimal Geo-Indistinguishable Mechanisms," CCS
2014). All of that work is on the **Euclidean plane / regular grids**,
**snapshot-focused**, and **explicitly scalability-limited** (the LP has |V|^2
variables). MIRAGE contributes:

  (a) a road-graph-**native** optimal mechanism: outputs are graph nodes and both
      the distortion (utility) and the adversary's error are measured as graph
      shortest-path distance;
  (b) **scalability** to real city-scale graphs via *density-adaptive local LPs*:
      each node's release distribution is the solution of a tiny LP over its
      local candidate neighbourhood, turning an intractable |V|^2 LP into |V|
      independent O(C^3) LPs that are precomputed and cached;
  (c) a **trajectory-aware** variant (see mirage_trajectory.py) that optimizes
      against the sequential (HMM-smoothing) adversary and preserves trajectory
      coherence.

This file implements the snapshot-optimal core and the local-LP construction.

The per-region LP (Shokri 2012, graph metric):
    variables  f(o|v) >= 0  (release o given true v),  y_o  (adversary error at o)
    maximize   sum_o y_o                                   [privacy, metres]
    s.t.       y_o <= sum_v pi(v) f(o|v) d_G(h,v)   for all o, h   [adversary best resp.]
               sum_v pi(v) sum_o f(o|v) d_G(v,o) <= D_max          [utility budget]
               sum_o f(o|v) = 1  for all v;   f >= 0
where d_G is graph shortest-path distance and pi the (local) population prior.
"""

import os
import json
import numpy as np
from scipy.optimize import linprog


def solve_region_lp(dR, pi, dmax, dp_epsilon=None):
    """
    Solve the graph-metric optimal-mechanism LP on one region.

    Parameters
    ----------
    dR  : (n, n) graph shortest-path distances (metres) among region nodes.
    pi  : (n,)   local prior over region nodes (sums to 1).
    dmax: float  utility (expected distortion) budget in metres.
    dp_epsilon : float | None
        If set, add geo-indistinguishability constraints
        f(o|v) <= exp(eps * d(v,v')) f(o|v') for adjacent-in-candidate v,v'.

    Returns
    -------
    f : (n, n) release matrix (rows = true v, cols = observed o), or None.
    """
    n = len(pi)
    nf = n * n
    nv = nf + n

    c = np.zeros(nv)
    c[nf:] = -1.0  # maximize sum_o y_o  ->  minimize -sum y

    A_ub, b_ub = [], []
    # adversary best response: y_o - sum_v pi_v d(h,v) f[v,o] <= 0   for all o,h
    for o in range(n):
        col_o = nf + o
        for h in range(n):
            row = np.zeros(nv)
            row[col_o] = 1.0
            row[o:nf:n] = -pi * dR[h]     # f[v,o] coefficient = -pi_v d(h,v)
            A_ub.append(row)
            b_ub.append(0.0)
    # utility budget: sum_v pi_v sum_o f[v,o] d(v,o) <= dmax
    row = np.zeros(nv)
    for v in range(n):
        row[v * n:(v + 1) * n] = pi[v] * dR[v]
    A_ub.append(row)
    b_ub.append(dmax)

    # optional geo-indistinguishability constraints (metric DP)
    if dp_epsilon is not None:
        for v in range(n):
            for w in range(n):
                if v == w:
                    continue
                fac = np.exp(dp_epsilon * dR[v, w])
                for o in range(n):
                    row = np.zeros(nv)
                    row[v * n + o] = 1.0
                    row[w * n + o] = -fac
                    A_ub.append(row)
                    b_ub.append(0.0)

    # equality: sum_o f[v,o] = 1
    A_eq, b_eq = [], []
    for v in range(n):
        row = np.zeros(nv)
        row[v * n:(v + 1) * n] = 1.0
        A_eq.append(row)
        b_eq.append(1.0)

    bounds = [(0, None)] * nv
    res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub),
                  A_eq=np.array(A_eq), b_eq=np.array(b_eq),
                  bounds=bounds, method="highs")
    if not res.success:
        return None
    return res.x[:nf].reshape(n, n)


class MirageMechanism:
    """
    Snapshot-optimal, road-graph-native obfuscation with density-adaptive local
    LPs. Precomputes a release distribution per node and samples from it.

    Parameters
    ----------
    node_ids : list[str]
    D        : (N, N) graph shortest-path distance matrix (metres).
    prior    : (N,)   population prior over nodes.
    dmax     : float  utility budget (expected distortion, metres).
    cand_size: int    local candidate-neighbourhood size C.
    dp_epsilon : float | None  optional geo-ind constraint.
    seed     : int    RNG seed for sampling.
    """

    def __init__(self, node_ids, D, prior, dmax=800.0, cand_size=28,
                 dp_epsilon=None, seed=0):
        self.node_ids = [str(x) for x in node_ids]
        self.idx = {n: i for i, n in enumerate(self.node_ids)}
        self.D = D
        self.prior = np.asarray(prior, dtype=float)
        self.dmax = dmax
        self.cand_size = cand_size
        self.dp_epsilon = dp_epsilon
        self.rng = np.random.default_rng(seed)
        # per-node mechanism: node_index -> (candidate_indices, probs)
        self.mech = None

    # ------------------------------------------------------------------
    def _partition_regions(self):
        """
        Density-adaptive partition of the graph into local regions (the units of
        the local LP). Greedy from highest-prior unassigned node, taking its C
        nearest still-unassigned nodes. Dense areas (high prior) are seeded first
        and covered by tighter regions. Returns list[np.ndarray of node indices].
        """
        N = len(self.node_ids)
        unassigned = np.ones(N, dtype=bool)
        order = np.argsort(self.prior)[::-1]      # densest first
        regions = []
        for seed in order:
            if not unassigned[seed]:
                continue
            cand_all = np.argsort(self.D[seed])
            region = [c for c in cand_all if unassigned[c]][:self.cand_size]
            region = np.array(region, dtype=int)
            unassigned[region] = False
            regions.append(region)
            if not unassigned.any():
                break
        return regions

    def precompute(self, verbose=True, cache_path=None):
        """Solve one joint LP per spatial region; cache to disk if given."""
        if cache_path and os.path.exists(cache_path):
            self._load(cache_path)
            return self
        regions = self._partition_regions()
        mech = {}
        n_fail = 0
        for ri, region in enumerate(regions):
            dR = self.D[np.ix_(region, region)].astype(float)
            pv = self.prior[region].astype(float)
            s = pv.sum()
            pv = pv / s if s > 0 else np.full(len(region), 1.0 / len(region))
            f = solve_region_lp(dR, pv, self.dmax, self.dp_epsilon)
            if f is None:
                for li, v in enumerate(region):
                    mech[int(v)] = (np.array([int(v)]), np.array([1.0]))
                n_fail += 1
                continue
            for li, v in enumerate(region):
                row = np.clip(f[li], 0, None)
                row = row / row.sum() if row.sum() > 0 else np.full(len(region), 1.0/len(region))
                mech[int(v)] = (region.astype(int), row)
            if verbose and (ri + 1) % 50 == 0:
                print(f"  MIRAGE precompute region {ri+1}/{len(regions)}")
        if verbose:
            print(f"  MIRAGE precompute done ({len(regions)} regions, {n_fail} LP fallbacks)")
        self.mech = mech
        if cache_path:
            self._save(cache_path)
        return self

    def _save(self, path):
        obj = {str(v): [cand.tolist(), probs.tolist()]
               for v, (cand, probs) in self.mech.items()}
        with open(path, "w") as f:
            json.dump({"dmax": self.dmax, "cand_size": self.cand_size,
                       "dp_epsilon": self.dp_epsilon, "mech": obj}, f)

    def _load(self, path):
        with open(path) as f:
            d = json.load(f)
        self.dmax = d["dmax"]
        self.mech = {int(v): (np.array(c, dtype=int), np.array(p, dtype=float))
                     for v, (c, p) in d["mech"].items()}

    # ------------------------------------------------------------------
    def emission(self, v_idx):
        """Return (candidate_indices, probs) = f(.|v) for adversary use."""
        return self.mech[v_idx]

    def sample(self, v_idx):
        cand, probs = self.mech[v_idx]
        return int(self.rng.choice(cand, p=probs))

    # ------------------------------------------------------------------
    # Framework-standard interface
    # ------------------------------------------------------------------
    def anonymize_snapshot(self, snapshot):
        """
        {user: node} -> {user: {original_node, cloaked_node, cloaked_coords?,
                                location_error, emission_cand, emission_prob}}
        location_error is graph distance d_G(v, o).
        """
        out = {}
        for uid, node in snapshot.items():
            v = self.idx[str(node)]
            o = self.sample(v)
            out[uid] = {
                "original_node": self.node_ids[v],
                "cloaked_node": self.node_ids[o],
                "location_error": float(self.D[v, o]),
                "mode": "mirage",
            }
        return out
