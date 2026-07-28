"""
Adversary Models for Location-Privacy Evaluation
================================================

This module replaces the ad-hoc, mechanism-specific "privacy score" (a number
in [0,1] with no operational meaning and no cross-mechanism comparability) with
a principled, *adversary-grounded* privacy metric expressed in physical units
(metres) and directly comparable across all mechanism families.

Following Shokri et al. [1], privacy is defined as the *expected error of an
optimal Bayesian adversary* who tries to infer a user's true location from the
released (anonymised) report, using publicly available background knowledge:
the population prior pi(v) and, for trajectory attacks, a first-order Markov
mobility model P(v_{t+1}|v_t) (see adversary_priors.py).

Two threat models are implemented so that mechanisms defending *different*
threats are each evaluated against the threat they actually target -- resolving
the incomparability of scoring a snapshot mechanism and a trajectory mechanism
on one scale:

  * SnapshotAdversary  -- single-observation Bayesian localisation attack.
        Privacy = E[ d(true, adversary_estimate) ] in metres  (higher = better).
        This is the threat that k-anonymity / DP / graph-constrained DP defend.

  * TrajectoryAdversary -- multi-observation Hidden-Markov tracking attack
        (Viterbi decoding with the mobility prior).  Privacy = expected
        tracking error in metres and a per-step re-identification hit-rate.
        This is the threat that temporal cloaking defends.

Every mechanism is evaluated under *both* adversaries, yielding a 2-D privacy
profile (snapshot-AE, trajectory-AE) instead of a single incomparable scalar.

References
----------
[1] R. Shokri, G. Theodorakopoulos, J.-Y. Le Boudec, and J.-P. Hubaux,
    "Quantifying Location Privacy," IEEE S&P, 2011.
[2] M. E. Andres et al., "Geo-indistinguishability," ACM CCS, 2013.
[3] Y. Xiao and L. Xiong, "Protecting Locations with Differential Privacy
    under Temporal Correlations," ACM CCS, 2015.
"""

import os
import json
import numpy as np

try:
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra as _sp_dijkstra
    _HAVE_SCIPY = True
except Exception:  # pragma: no cover
    _HAVE_SCIPY = False


# =====================================================================
# Graph distance matrix (node-index space)
# =====================================================================
def build_graph_distance_matrix(nodes_file, edges_file, id_to_idx):
    """
    Build an (N, N) all-pairs shortest-path distance matrix (metres),
    indexed by canonical node index (from adversary_priors.load_node_index).

    Uses scipy's Dijkstra on a sparse adjacency for speed; falls back to a
    pure-python heap implementation if scipy is unavailable.
    """
    N = len(id_to_idx)
    with open(edges_file) as f:
        edges = json.load(f)

    rows, cols, data = [], [], []
    for e in edges:
        s, t = str(e["source"]), str(e["target"])
        if s in id_to_idx and t in id_to_idx:
            i, j = id_to_idx[s], id_to_idx[t]
            w = float(e["distance"])
            rows += [i, j]
            cols += [j, i]
            data += [w, w]

    if _HAVE_SCIPY:
        A = csr_matrix((data, (rows, cols)), shape=(N, N))
        D = _sp_dijkstra(A, directed=False)
        # Replace unreachable (inf) with a large finite sentinel.
        finite_max = D[np.isfinite(D)].max() if np.isfinite(D).any() else 1.0
        D[~np.isfinite(D)] = finite_max * 10.0
        return D

    # Pure-python fallback (slower but dependency-free).
    import heapq
    adj = [[] for _ in range(N)]
    for i, j, w in zip(rows, cols, data):
        adj[i].append((j, w))
    D = np.full((N, N), np.inf)
    for src in range(N):
        dist = D[src]
        dist[src] = 0.0
        pq = [(0.0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
    finite_max = D[np.isfinite(D)].max() if np.isfinite(D).any() else 1.0
    D[~np.isfinite(D)] = finite_max * 10.0
    return D


# =====================================================================
# Matrix-backed distance cache (shared by mechanisms and the adversary)
# =====================================================================
class _MatrixRow:
    __slots__ = ("mat", "i", "idx")

    def __init__(self, mat, i, idx):
        self.mat = mat
        self.i = i
        self.idx = idx

    def __getitem__(self, b):
        return float(self.mat[self.i, self.idx[str(b)]])


class MatrixDistCache:
    """
    Drop-in replacement for the mechanisms' nested-dict distance cache, backed
    by a dense numpy matrix.  Supports `cache[a][b]` -> shortest-path metres.
    Lets a large real graph share ONE distance matrix across every mechanism and
    the adversary, instead of a memory-heavy dict-of-dicts.
    """

    def __init__(self, mat, node_ids):
        self.mat = mat
        self.idx = {str(n): i for i, n in enumerate(node_ids)}

    def __getitem__(self, a):
        return _MatrixRow(self.mat, self.idx[str(a)], self.idx)


# =====================================================================
# Snapshot adversary: single-observation Bayesian localisation
# =====================================================================
class SnapshotAdversary:
    """
    Optimal single-observation adversary.

    Given a released report, the adversary forms a posterior over the true
    node and outputs the estimate that minimises expected distance to the
    truth (the Bayes estimator under a distance loss).  Its *expected error*
    against the true location is the privacy of the mechanism (Shokri et al.).

    Comparability across mechanisms comes from the fact that the same quantity
    -- expected adversary localisation error in metres -- is measured for all
    of them; only the observation model P(observation | true node) differs.
    """

    def __init__(self, prior, coords, Dmat):
        """
        prior  : np.ndarray (N,)   -- population prior pi(v)
        coords : np.ndarray (N, 2) -- (lon, lat) per node index
        Dmat   : np.ndarray (N, N) -- graph shortest-path distances (metres)
        """
        self.prior = prior
        self.coords = coords
        self.D = Dmat
        self.N = len(prior)

    # ---- Bayes estimator shared by all observation models -------------
    def _bayes_error(self, posterior, true_idx):
        """
        Given a posterior over nodes and the true node index, return
        (expected_adversary_error_metres, is_exact_hit).

        The adversary picks the node minimising expected distance under the
        posterior; error is the graph distance from that estimate to the
        true node.
        """
        # Expected distance of every candidate estimate under the posterior.
        exp_dist = posterior @ self.D                # shape (N,)
        est = int(np.argmin(exp_dist))
        return float(self.D[est, true_idx]), (est == true_idx)

    # ---- Observation model: differential privacy (planar Laplace) -----
    def attack_dp(self, noisy_lonlat, scale, true_idx):
        """
        DP / coordinate-noise mechanisms.  The mechanism adds independent
        Laplace(scale) noise to each coordinate, so the emission log-density
        of observing point o given true node v is  -||o - coord(v)||_1 / scale.
        Posterior(v) proportional to emission(v) * prior(v).
        """
        o = np.asarray(noisy_lonlat, dtype=float)
        l1 = np.abs(self.coords - o).sum(axis=1)     # (N,)
        logpost = -l1 / max(scale, 1e-12) + np.log(self.prior + 1e-300)
        logpost -= logpost.max()
        post = np.exp(logpost)
        post /= post.sum()
        return self._bayes_error(post, true_idx)

    # ---- Observation model: projected DP (observed = a graph node) ----
    def attack_projected(self, obs_idx, scale, true_idx):
        """
        Graph-constrained DP: observation is a graph node (the projection of
        the noisy point).  Emission uses the node coordinate as the observed
        point, otherwise identical to attack_dp.
        """
        return self.attack_dp(self.coords[obs_idx], scale, true_idx)

    # ---- Observation model: arbitrary emission (MIRAGE / optimal mechanism) --
    def attack_distribution(self, source_idxs, emit_probs, true_idx):
        """
        General observation model: the adversary observed something that node v
        could have produced with probability emit_probs[v] = f(o|v), for v in
        source_idxs. Posterior P(v|o) ∝ prior(v) f(o|v); Bayes estimate over ALL
        nodes minimises expected graph distance. Used for MIRAGE, whose emission
        f is known exactly.
        """
        idxs = np.asarray(source_idxs, dtype=int)
        w = self.prior[idxs] * np.asarray(emit_probs, dtype=float)
        if w.sum() <= 0:
            w = np.ones(len(idxs))
        w = w / w.sum()
        exp_dist = (self.D[:, idxs] * w).sum(axis=1)   # (N,)
        est = int(np.argmin(exp_dist))
        return float(self.D[est, true_idx]), (est == true_idx)

    # ---- Observation model: anonymity set (k-anon / density / group) --
    def attack_anonymity_set(self, anonset_idxs, true_idx):
        """
        Cloaking mechanisms release an anonymity set (the >=k users covered by
        the cloaking region / temporal group).  The adversary cannot
        distinguish among its members, so the posterior is the prior restricted
        to the set.  The best estimate minimises expected distance to the set;
        error is measured to the true node.

        A larger, more spatially spread anonymity set -> larger adversary error
        -> stronger privacy, exactly as k-anonymity intends.
        """
        idxs = np.asarray(sorted(set(int(i) for i in anonset_idxs)), dtype=int)
        if idxs.size == 0:
            idxs = np.array([true_idx], dtype=int)
        w = self.prior[idxs]
        if w.sum() <= 0:
            w = np.ones_like(w)
        w = w / w.sum()
        # Expected distance of each candidate estimate under the restricted post.
        exp_dist = (self.D[:, idxs] * w).sum(axis=1)   # (N,)
        est = int(np.argmin(exp_dist))
        return float(self.D[est, true_idx]), (est == true_idx)


# =====================================================================
# Trajectory adversary: HMM tracking via Viterbi with a mobility prior
# =====================================================================
class TrajectoryAdversary:
    """
    Multi-observation adversary that tracks a user across a *sequence* of
    anonymised reports by combining the per-report emission model with a
    first-order Markov mobility prior P(v_{t+1}|v_t), decoded with Viterbi.

    This is the threat temporal mechanisms defend and the threat that
    independent per-report noise (plain DP) fails to defend, because temporal
    correlation lets the adversary average out noise (Xiao & Xiong [3]).

    Privacy is reported as:
      * tracking_error : mean graph distance (metres) between the Viterbi
                         estimate and the true node, over all time steps;
      * reid_rate      : fraction of time steps the estimate is exactly correct.
    """

    def __init__(self, prior, coords, Dmat, T, transition_floor=1e-6):
        self.prior = prior
        self.coords = coords
        self.D = Dmat
        self.N = len(prior)
        # Pre-log the transition matrix once (with a floor for numerical safety).
        # float32 halves the per-step N x N memory churn in Viterbi (the dominant
        # cost on the ~3k-node real graph) at negligible accuracy cost.
        self.logT = np.log(np.maximum(T, transition_floor)).astype(np.float32)

    def _viterbi(self, log_emissions):
        """
        Standard Viterbi decoding.

        log_emissions : list of np.ndarray (N,) -- per-step log P(obs_t | v).
        Returns the most-likely state sequence (list of node indices).
        """
        Tlen = len(log_emissions)
        if Tlen == 0:
            return []
        delta = np.log(self.prior + 1e-300) + log_emissions[0]
        backptr = np.zeros((Tlen, self.N), dtype=np.int32)
        for t in range(1, Tlen):
            # score[i, j] = delta_prev[i] + logT[i, j]
            scores = delta[:, None] + self.logT       # (N, N)
            best_prev = np.argmax(scores, axis=0)      # (N,)
            delta = scores[best_prev, np.arange(self.N)] + log_emissions[t]
            backptr[t] = best_prev
        path = np.zeros(Tlen, dtype=np.int32)
        path[-1] = int(np.argmax(delta))
        for t in range(Tlen - 1, 0, -1):
            path[t - 1] = backptr[t, path[t]]
        return path.tolist()

    # ---- Emission builders per mechanism family -----------------------
    def emission_dp(self, noisy_lonlat, scale):
        o = np.asarray(noisy_lonlat, dtype=float)
        l1 = np.abs(self.coords - o).sum(axis=1)
        return -l1 / max(scale, 1e-12)

    def emission_projected(self, obs_idx, scale):
        return self.emission_dp(self.coords[obs_idx], scale)

    def emission_anonymity_set(self, anonset_idxs, soft=6.0):
        """
        Uniform-ish emission over the anonymity set: members get log 0, others a
        strong (but finite) penalty so Viterbi can still move through them if the
        mobility prior demands it.
        """
        e = np.full(self.N, -soft, dtype=float)
        idxs = np.asarray(sorted(set(int(i) for i in anonset_idxs)), dtype=int)
        if idxs.size:
            e[idxs] = 0.0
        return e

    def track(self, log_emissions, true_idx_seq):
        """
        Decode a sequence and score it.

        Returns (tracking_error_metres, reid_rate) for the sequence.
        """
        est = self._viterbi(log_emissions)
        if not est:
            return None, None
        errs = [float(self.D[e, t]) for e, t in zip(est, true_idx_seq)]
        hits = [1.0 if e == t else 0.0 for e, t in zip(est, true_idx_seq)]
        return float(np.mean(errs)), float(np.mean(hits))


# =====================================================================
# Convenience: assemble the full adversary toolkit for a graph
# =====================================================================
def build_adversary_toolkit(nodes_file, edges_file, csv_file,
                            cache_tag="geolife", rebuild_priors=False):
    """
    One-call setup: load node index, estimate/load prior + transitions, build
    the distance matrix, and return everything needed to instantiate both
    adversaries.

    Returns a dict with keys:
      node_ids, id_to_idx, coords, prior, T, D,
      snapshot_adversary, trajectory_adversary
    """
    from adversary_priors import load_node_index, estimate_prior_and_transitions

    node_ids, id_to_idx, coords = load_node_index(nodes_file)
    prior, T = estimate_prior_and_transitions(
        csv_file, node_ids, id_to_idx, cache_tag=cache_tag,
        rebuild=rebuild_priors)
    D = build_graph_distance_matrix(nodes_file, edges_file, id_to_idx)

    return {
        "node_ids": node_ids,
        "id_to_idx": id_to_idx,
        "coords": coords,
        "prior": prior,
        "T": T,
        "D": D,
        "snapshot_adversary": SnapshotAdversary(prior, coords, D),
        "trajectory_adversary": TrajectoryAdversary(prior, coords, D, T),
    }
