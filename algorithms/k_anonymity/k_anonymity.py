"""
Graph-Based Spatial Cloaking for k-Anonymity in Location Privacy
=================================================================

References
----------
[1] Sweeney, L. (2002). k-Anonymity: A Model for Protecting Privacy.
    International Journal of Uncertainty, Fuzziness and Knowledge-Based
    Systems, 10(5), 557-570.  https://doi.org/10.1142/S0218488502001648
    -- Foundational definition: a dataset satisfies k-anonymity when every
       record is indistinguishable from at least k-1 others on the
       quasi-identifier attributes.  Here the quasi-identifier is location.

[2] Gruteser, M. & Grunwald, D. (2003). Anonymous Usage of Location-Based
    Services Through Spatial and Temporal Cloaking.
    Proc. MobiSys 2003, pp. 31-42.  https://doi.org/10.1145/1066116.1189037
    -- Introduced *spatial cloaking*: instead of an exact point, report a
       region R containing at least k users, making the querying user
       indistinguishable among k individuals.  The cloaking region grows
       outward until k users are covered.

[3] Mokbel, M. F., Chow, C.-Y., & Aref, W. G. (2006). The New Casper:
    Query Processing for Location Services without Compromising Privacy.
    Proc. VLDB 2006, pp. 763-774.
    -- Server-side cloaking engine; the region is expanded (BFS-like) until
       k users are covered.  Our BFS expansion on the road network directly
       follows this design.

[4] Duckham, M. & Kulik, L. (2005). A Formal Model of Obfuscation and
    Negotiation for Location Privacy.
    Pervasive Computing, LNCS 3468, pp. 152-170.
    -- Formalises location privacy on spatial graphs; the cloaking region is
       modelled as a connected subgraph rather than an axis-aligned bounding
       box, which is the model adopted here.

Algorithm: BFS Expansion Cloaking on a Road-Network Graph
    (Section 2 of [3], adapted to graphs following [4])

    Input : snapshot S = {user_id -> node_id}, privacy parameter k
    For each user u in S at node v:
      1. R <- {v},  count <- |{ u' in S : node(u') == v }|
      2. BFS from v over the road network graph:
             for each unvisited neighbour n of the frontier:
               R <- R | {n},  count <- count + users_at(n)
               if count >= k: stop
      3. Medoid(R) = argmin_{n in R} dist(n, centroid(R))  [Euclidean]
         -- Reported as the single cloaked location (following [2])
    Output: {user_id -> {original_node, cloaked_node, region, k_achieved}}
"""

import json
import heapq
import math
from collections import defaultdict, deque


class GraphKAnonymizer:
    """
    Graph-based spatial cloaking for location k-anonymity.

    Implements the BFS-expansion cloaking algorithm from Mokbel et al. (2006)
    [3] on a road-network graph, following the connected-subgraph model of
    Duckham & Kulik (2005) [4].  For each user the minimum connected subgraph
    of the road network that contains at least k distinct users is found via
    BFS; the medoid of that subgraph is reported as the anonymised location.
    """

    def __init__(self, nodes, edges, k=3, dist_cache=None):
        """
        Parameters
        ----------
        nodes : str | list
            Path to nodes JSON, or pre-loaded list.
            Each node: {"id": str, "x": float (lon), "y": float (lat)}.
        edges : str | list
            Path to edges JSON, or pre-loaded list.
            Each edge: {"source": str, "target": str, "distance": float (m)}.
        k : int
            Anonymity parameter -- region must cover >= k distinct users.
        dist_cache : dict | None
            Pre-computed all-pairs shortest-path distances
            {source_node: {dest_node: distance_m}}.
            Pass this to share the expensive Dijkstra computation across
            multiple GraphKAnonymizer instances that use the same graph.
        """
        self.k = k
        self.graph, self.node_coords = self._load_graph(nodes, edges)

        if dist_cache is not None:
            self.dist_cache = dist_cache
        else:
            n = len(self.graph)
            print(f"  Precomputing all-pairs shortest paths ({n} nodes)...")
            self.dist_cache = _all_pairs_dijkstra(self.graph)
            print("  Done.")

    # ------------------------------------------------------------------
    # Graph loading
    # ------------------------------------------------------------------
    def _load_graph(self, nodes_input, edges_input):
        if isinstance(nodes_input, str):
            with open(nodes_input) as f:
                nodes_input = json.load(f)
        if isinstance(edges_input, str):
            with open(edges_input) as f:
                edges_input = json.load(f)

        G = {}
        coords = {}

        for n in nodes_input:
            nid = str(n["id"])
            G[nid] = []
            coords[nid] = (float(n["x"]), float(n["y"]))  # (lon, lat)

        for e in edges_input:
            s, t = str(e["source"]), str(e["target"])
            d = float(e["distance"])
            if s in G and t in G:
                G[s].append((t, d))
                G[t].append((s, d))

        return G, coords

    # ------------------------------------------------------------------
    # BFS Expansion Cloaking  [Algorithm 2, adapted from Mokbel et al. 2006]
    # ------------------------------------------------------------------
    def _expand_region(self, origin, density_map):
        """
        Grow a connected subgraph R outward from *origin* via BFS until
        at least k users are covered.

        Parameters
        ----------
        origin      : str   -- user's true node
        density_map : dict  -- {node_id: user_count} for current snapshot

        Returns
        -------
        region  : set[str]  -- connected subgraph forming the cloaking region
        covered : int       -- users covered (>= k when graph is large enough)
        """
        origin = str(origin)
        region = {origin}
        frontier = deque([origin])
        visited = {origin}
        covered = density_map.get(origin, 0)

        while covered < self.k and frontier:
            cur = frontier.popleft()
            for nxt, _ in self.graph.get(cur, []):
                if nxt in visited:
                    continue
                visited.add(nxt)
                region.add(nxt)
                covered += density_map.get(nxt, 0)
                frontier.append(nxt)
                if covered >= self.k:
                    # Stop as soon as k is reached; remaining frontier
                    # nodes would only enlarge the region unnecessarily.
                    break

        return region, covered

    def _medoid(self, region):
        """
        Node in *region* closest (Euclidean) to the centroid of *region*.

        The medoid is used as the single reported cloaked location, following
        the centroid-reporting strategy of Gruteser & Grunwald (2003) [2].
        Using the medoid (an actual graph node) instead of the geometric
        centroid ensures the reported location lies on the road network.
        """
        cx = sum(self.node_coords[n][0] for n in region) / len(region)
        cy = sum(self.node_coords[n][1] for n in region) / len(region)
        return min(
            region,
            key=lambda n: (
                (self.node_coords[n][0] - cx) ** 2 +
                (self.node_coords[n][1] - cy) ** 2
            )
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def anonymize_snapshot(self, snapshot):
        """
        Apply k-anonymity spatial cloaking to a location snapshot.

        Parameters
        ----------
        snapshot : dict
            {user_id: node_id} -- one location record per user.

        Returns
        -------
        dict  {user_id: {
            "original_node"  : str,
            "cloaked_node"   : str,        # medoid of cloaking region
            "cloaked_coords" : (lon, lat),
            "region"         : list[str],
            "k_achieved"     : int,        # actual users covered
        }}
        """
        # User density per node for this snapshot
        density = defaultdict(int)
        for node in snapshot.values():
            density[str(node)] += 1

        result = {}
        for uid, node in snapshot.items():
            node = str(node)
            region, k_achieved = self._expand_region(node, density)
            cloaked = self._medoid(region)
            result[uid] = {
                "original_node":  node,
                "cloaked_node":   cloaked,
                "cloaked_coords": self.node_coords[cloaked],
                "region":         list(region),
                "k_achieved":     k_achieved,
            }
        return result

    # ------------------------------------------------------------------
    # Distance lookup
    # ------------------------------------------------------------------
    def dist(self, u, v):
        """
        Return the precomputed shortest-path distance in metres between u and v.
        O(1) lookup from the all-pairs cache.
        """
        return self.dist_cache[str(u)][str(v)]

    def get_dist_cache(self):
        """Expose the distance cache so callers can share it across instances."""
        return self.dist_cache


# ----------------------------------------------------------------------
# All-pairs shortest paths via Dijkstra
# Reference: Cormen, T.H., Leiserson, C.E., Rivest, R.L., & Stein, C. (2022).
#   Introduction to Algorithms, 4th ed., Chapter 22.
#   Time complexity: O(V * (E + V) log V);  Space: O(V^2)
# ----------------------------------------------------------------------
def _all_pairs_dijkstra(graph):
    """
    Compute all-pairs shortest-path distances on a weighted undirected graph.

    Parameters
    ----------
    graph : dict  {node_id: [(neighbour_id, weight), ...]}

    Returns
    -------
    cache : dict  {source: {dest: distance}}
    """
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
