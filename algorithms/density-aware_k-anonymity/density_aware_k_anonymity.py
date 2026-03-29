"""
Density-Aware Adaptive k-Anonymity for Location Privacy
=========================================================

References
----------
[1] Sweeney, L. (2002). k-Anonymity: A Model for Protecting Privacy.
    IJUFKS, 10(5), 557-570.
    -- Foundational k-anonymity definition.

[2] Gruteser, M. & Grunwald, D. (2003). Anonymous Usage of Location-Based
    Services Through Spatial and Temporal Cloaking.
    Proc. MobiSys 2003, pp. 31-42.
    -- BFS-expansion spatial cloaking.

[3] Gedik, B. & Liu, L. (2008). Protecting Location Privacy with
    Personalized k-Anonymity: Architecture and Algorithms.
    IEEE Trans. Mobile Computing, 7(1), 1-18.
    -- KEY REFERENCE: introduces *personalised* k-anonymity where each
       user can request a different k value based on context.  Our
       density-aware scheme generalises this by setting k adaptively
       from local user density rather than per-user preferences.

[4] Niu, B., Li, Q., Zhu, X., Cao, G., & Li, H. (2014). Achieving
    k-Anonymity in Privacy-Aware Location-Based Services.
    Proc. INFOCOM 2014, pp. 754-762.
    -- Density-aware cloaking: in sparse regions users need stronger
       anonymity (higher k) because there are fewer candidates to
       hide among; in dense regions a lower k already provides
       sufficient confusion.

[5] Mokbel, M. F., Chow, C.-Y., & Aref, W. G. (2006).
    The New Casper: Query Processing for Location Services without
    Compromising Privacy.  Proc. VLDB 2006.
    -- BFS expansion design.

[6] Duckham, M. & Kulik, L. (2005). A Formal Model of Obfuscation and
    Negotiation for Location Privacy.  Pervasive Computing, LNCS 3468.
    -- Connected-subgraph cloaking model.

Algorithm: Density-Aware Adaptive BFS Cloaking
    (Extension of [2][5] with adaptive k from [3][4])

    Input : snapshot S = {user_id -> node_id}, density thresholds
    For each user u at node v:
      1. density <- |users at v| + Σ |users at neighbours of v|
      2. k <- adaptive_k(density):
             Sparse  (< P33):  k = k_sparse   (high, e.g. 8)
             Medium  (P33-P66): k = k_medium   (mid,  e.g. 5)
             Dense   (> P66):  k = k_dense    (low,  e.g. 2)
      3. BFS expand from v until k users covered (same as [5])
      4. medoid <- closest node to centroid in region
    Output: per-user {original, cloaked, adaptive_k, density, region}
"""

import json
import math
import heapq
import numpy as np
from collections import defaultdict, deque


class DensityAwareKAnonymizer:
    """
    Density-aware adaptive k-anonymity on a road-network graph.

    Extends the BFS-expansion cloaking algorithm of Mokbel et al. (2006)
    [5] with an adaptive k selection strategy inspired by Gedik & Liu
    (2008) [3] and Niu et al. (2014) [4].

    In dense regions where many users are naturally co-located, a small
    k already provides sufficient anonymity; in sparse regions a larger
    k is required to prevent easy re-identification.  The density
    thresholds are computed from the snapshot itself (percentile-based).
    """

    # Default adaptive-k mapping (can be overridden)
    K_SPARSE = 8   # sparse regions need more privacy
    K_MEDIUM = 5
    K_DENSE  = 2   # dense regions already have natural anonymity

    def __init__(self, nodes, edges, dist_cache=None,
                 k_sparse=None, k_medium=None, k_dense=None):
        self.graph, self.node_coords = self._load_graph(nodes, edges)

        self.k_sparse = k_sparse or self.K_SPARSE
        self.k_medium = k_medium or self.K_MEDIUM
        self.k_dense  = k_dense  or self.K_DENSE

        if dist_cache is not None:
            self.dist_cache = dist_cache
        else:
            n = len(self.graph)
            print(f"  Precomputing all-pairs shortest paths ({n} nodes)...")
            self.dist_cache = _all_pairs_dijkstra(self.graph)
            print("  Done.")

    # ------------------------------------------------------------------
    def _load_graph(self, nodes_input, edges_input):
        if isinstance(nodes_input, str):
            with open(nodes_input) as f:
                nodes_input = json.load(f)
        if isinstance(edges_input, str):
            with open(edges_input) as f:
                edges_input = json.load(f)

        G, coords = {}, {}
        for n in nodes_input:
            nid = str(n["id"])
            G[nid] = []
            coords[nid] = (float(n["x"]), float(n["y"]))
        for e in edges_input:
            s, t = str(e["source"]), str(e["target"])
            d = float(e["distance"])
            if s in G and t in G:
                G[s].append((t, d))
                G[t].append((s, d))
        return G, coords

    # ------------------------------------------------------------------
    # Density computation  [Niu et al. 2014, Section 3]
    # ------------------------------------------------------------------
    def _compute_density(self, node, density_map):
        """
        Local density at node = users at node + users at 1-hop neighbours.
        """
        node = str(node)
        total = density_map.get(node, 0)
        for nb, _ in self.graph.get(node, []):
            total += density_map.get(nb, 0)
        return total

    def _select_adaptive_k(self, density, p33, p66):
        """
        Adaptive k selection based on density percentiles.
        Following the personalised privacy model of Gedik & Liu [3]
        and the density-aware strategy of Niu et al. [4].
        """
        if density < p33:
            return self.k_sparse, "Sparse"
        elif density < p66:
            return self.k_medium, "Medium"
        else:
            return self.k_dense, "Dense"

    # ------------------------------------------------------------------
    # BFS Expansion  (same core as k_anonymity.py)
    # ------------------------------------------------------------------
    def _expand_region(self, origin, density_map, k):
        origin = str(origin)
        region = {origin}
        frontier = deque([origin])
        visited = {origin}
        covered = density_map.get(origin, 0)

        while covered < k and frontier:
            cur = frontier.popleft()
            for nxt, _ in self.graph.get(cur, []):
                if nxt in visited:
                    continue
                visited.add(nxt)
                region.add(nxt)
                covered += density_map.get(nxt, 0)
                frontier.append(nxt)
                if covered >= k:
                    break
        return region, covered

    def _medoid(self, region):
        cx = sum(self.node_coords[n][0] for n in region) / len(region)
        cy = sum(self.node_coords[n][1] for n in region) / len(region)
        return min(region, key=lambda n: (
            (self.node_coords[n][0] - cx) ** 2 +
            (self.node_coords[n][1] - cy) ** 2
        ))

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def anonymize_snapshot(self, snapshot):
        """
        Apply density-aware adaptive k-anonymity to a snapshot.

        Parameters
        ----------
        snapshot : dict  {user_id: node_id}

        Returns
        -------
        dict  {user_id: {
            "original_node"  : str,
            "cloaked_node"   : str,
            "cloaked_coords" : (lon, lat),
            "region"         : list[str],
            "k_achieved"     : int,
            "adaptive_k"     : int,
            "density"        : int,
            "density_level"  : str,
        }}
        """
        # Build density map
        density_map = defaultdict(int)
        for node in snapshot.values():
            density_map[str(node)] += 1

        # Compute per-node densities for percentile thresholds
        all_densities = []
        for node in set(str(n) for n in snapshot.values()):
            all_densities.append(self._compute_density(node, density_map))

        if len(all_densities) < 3:
            p33, p66 = 1, 2
        else:
            p33 = float(np.percentile(all_densities, 33))
            p66 = float(np.percentile(all_densities, 66))

        result = {}
        for uid, node in snapshot.items():
            node = str(node)
            density = self._compute_density(node, density_map)
            k, level = self._select_adaptive_k(density, p33, p66)

            region, k_achieved = self._expand_region(node, density_map, k)
            cloaked = self._medoid(region)

            result[uid] = {
                "original_node":  node,
                "cloaked_node":   cloaked,
                "cloaked_coords": self.node_coords[cloaked],
                "region":         list(region),
                "k_achieved":     k_achieved,
                "adaptive_k":     k,
                "density":        density,
                "density_level":  level,
            }
        return result

    # ------------------------------------------------------------------
    def dist(self, u, v):
        return self.dist_cache[str(u)][str(v)]

    def get_dist_cache(self):
        return self.dist_cache


# ----------------------------------------------------------------------
# All-pairs Dijkstra  (shared with k_anonymity.py)
# ----------------------------------------------------------------------
def _all_pairs_dijkstra(graph):
    cache = {}
    for source in graph:
        dist = {n: math.inf for n in graph}
        dist[source] = 0.0
        pq = [(0.0, source)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for v, w in graph[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        cache[source] = dist
    return cache
