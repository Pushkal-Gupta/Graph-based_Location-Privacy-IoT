"""
Graph-Constrained Differential Privacy for Location Privacy
=============================================================

References
----------
[1] Dwork, C. (2006). Differential Privacy.
    Proc. ICALP 2006, LNCS 4052, pp. 1-12.
    -- Foundational ε-differential privacy definition.

[2] Dwork, C., McSherry, F., Nissim, K., & Smith, A. (2006).
    Calibrating Noise to Sensitivity in Private Data Analysis.
    Proc. TCC 2006, LNCS 3876, pp. 265-284.
    -- Laplace mechanism: Lap(Δf/ε) noise achieves ε-DP.

[3] Andrés, M. E., Bordenabe, N. E., Chatzikokolakis, K., & Palamidessi, C.
    (2013). Geo-indistinguishability: Differential Privacy for
    Location-Based Systems.  Proc. CCS 2013, pp. 901-914.
    -- Planar Laplace mechanism for location coordinates.

[4] Bordenabe, N. E., Chatzikokolakis, K., & Palamidessi, C. (2014).
    Optimal Geo-Indistinguishability Mechanisms.
    Proc. CCS 2014, pp. 251-262.
    -- Formalises the problem of graph-constrained location privacy:
       noisy outputs must be projected back onto a discrete spatial
       structure to remain physically meaningful.

[5] Xiao, Y. & Xiong, L. (2015). Protecting Locations with Differential
    Privacy under Temporal Correlations.
    Proc. CCS 2015, pp. 1298-1309.
    -- Demonstrates importance of projecting DP outputs onto valid
       spatial domains to preserve utility.

Algorithm: Laplace Noise with Graph Projection
    (Combining [3] with the projection step formalised in [4])

    Input : snapshot S = {user_id -> node_id}, privacy budget ε,
            graph G = (V, E)
    For each user u in S at node v:
      1. (lon, lat) <- coordinates of v
      2. noisy_lon <- lon + Lap(0, Δ/ε)
         noisy_lat <- lat + Lap(0, Δ/ε)
      3. projected_node <- argmin_{n ∈ V} haversine(noisy, coords(n))
         -- Project noisy point back onto nearest graph node [4]
      4. location_error <- shortest_path(v, projected_node) on G
    Output: {user_id -> {original_node, projected_node, location_error}}
"""

import json
import math
import heapq
import numpy as np


def _haversine_m(lon1, lat1, lon2, lat2):
    """Great-circle distance in metres between two (lon, lat) points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class GraphConstrainedDPObfuscator:
    """
    Graph-constrained differential privacy for location data.

    Extends the planar Laplace mechanism of Andrés et al. (2013) [3]
    with a graph projection step (Bordenabe et al. 2014 [4]):
    after adding Laplace noise to geographic coordinates, the noisy
    point is mapped to the nearest node in the road-network graph,
    ensuring the reported location lies on a valid spatial structure.

    Error is measured as the *graph shortest-path distance* between
    the true node and the projected node, not Euclidean distance.
    """

    def __init__(self, nodes, edges, epsilon=1.0, dist_cache=None):
        """
        Parameters
        ----------
        nodes : str | list
            Path to nodes JSON, or pre-loaded list.
        edges : str | list
            Path to edges JSON, or pre-loaded list.
        epsilon : float
            Privacy budget.
        dist_cache : dict | None
            Pre-computed all-pairs shortest paths.
        """
        self.epsilon = epsilon
        self.graph, self.node_coords = self._load_graph(nodes, edges)
        self.sensitivity = self._estimate_sensitivity()

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

    def _estimate_sensitivity(self):
        """Median edge length in coordinate space."""
        dists = []
        for node, neighbours in self.graph.items():
            for nb, _ in neighbours:
                dx = self.node_coords[node][0] - self.node_coords[nb][0]
                dy = self.node_coords[node][1] - self.node_coords[nb][1]
                dists.append(math.sqrt(dx * dx + dy * dy))
        return float(np.median(dists)) if dists else 0.01

    # ------------------------------------------------------------------
    # Laplace noise + graph projection
    # ------------------------------------------------------------------
    def _add_laplace(self, value):
        scale = self.sensitivity / self.epsilon
        return value + np.random.laplace(0, scale)

    def _project_to_graph(self, x, y):
        """
        Find the graph node closest (Euclidean) to the noisy point.
        This is the graph-projection step from Bordenabe et al. [4].
        """
        best_node, best_d = None, math.inf
        for nid, (nx_, ny_) in self.node_coords.items():
            d = (x - nx_) ** 2 + (y - ny_) ** 2
            if d < best_d:
                best_d = d
                best_node = nid
        return best_node

    # ------------------------------------------------------------------
    def anonymize_snapshot(self, snapshot):
        """
        Apply graph-constrained DP obfuscation to a location snapshot.

        Parameters
        ----------
        snapshot : dict  {user_id: node_id}

        Returns
        -------
        dict  {user_id: {
            "original_node"     : str,
            "cloaked_node"      : str,   (projected graph node)
            "cloaked_coords"    : (lon, lat),
            "projection_dist"   : float, (noisy point → graph node, metres)
            "location_error"    : float, (graph dist orig → projected, m)
        }}
        """
        result = {}
        for uid, node in snapshot.items():
            node = str(node)
            ox, oy = self.node_coords[node]

            nx_ = self._add_laplace(ox)
            ny_ = self._add_laplace(oy)

            proj = self._project_to_graph(nx_, ny_)
            px, py = self.node_coords[proj]

            proj_dist = _haversine_m(nx_, ny_, px, py)
            graph_err = self.dist_cache[node][proj]

            result[uid] = {
                "original_node":    node,
                "cloaked_node":     proj,
                "cloaked_coords":   (px, py),
                "projection_dist":  proj_dist,
                "location_error":   graph_err,
            }
        return result

    # ------------------------------------------------------------------
    def dist(self, u, v):
        return self.dist_cache[str(u)][str(v)]

    def get_dist_cache(self):
        return self.dist_cache


# ----------------------------------------------------------------------
# All-pairs Dijkstra  (same as k_anonymity.py)
# Reference: Cormen et al. (2022), Introduction to Algorithms, Ch. 22.
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
