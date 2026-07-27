"""
Density-Adaptive Hybrid Location Privacy (DA-Hybrid)
====================================================

A new mechanism (not a re-implementation of prior work) that combines the
complementary strengths of spatial cloaking and graph-constrained differential
privacy under a single, density-driven controller.  It is designed to occupy
the empty region of the privacy--utility Pareto frontier that a benchmark of
the five classical mechanisms leaves open: high *availability*, strong
*privacy*, and *on-graph* outputs at moderate spatial error.

Motivation
----------
The classical mechanisms fail in complementary ways:

  * Graph k-anonymity attains low spatial error where users are plentiful, but
    in sparse neighbourhoods it either (i) fails to find k users -> denial of
    service (low availability), or (ii) expands the cloaking region enormously
    -> huge spatial error and an energy-costly BFS.
  * Graph-constrained DP always produces a valid on-graph output (100 %
    availability) with a bounded, density-independent error, but pays an error
    premium where cloaking would have been cheap.

DA-Hybrid uses the *local user density* -- already computed by the framework --
to pick, per report, the mechanism that is locally best, with a guaranteed
fallback that removes denial of service entirely:

  For each user u at node v in a snapshot:
    1. Estimate local density rho(v) = users at v + users at 1-hop neighbours.
    2. Attempt bounded graph k-anonymity: grow a connected region by BFS until
       it covers >= k users OR it reaches a size cap R_max(rho).  The cap
       shrinks as density rises (dense areas need little expansion).
    3. If k users are covered within the cap -> report the region medoid
       (k-anonymity: low error, on-graph, k-satisfied).
    4. Otherwise -> fall back to graph-constrained DP at budget eps: add planar
       Laplace noise and project to the nearest node (always succeeds).

Because step 4 never fails, availability is 100 % by construction, while step 3
recovers k-anonymity's low error wherever density permits.  The size cap bounds
k-anonymity's worst-case error and BFS energy in sparse areas.

Guarantees
----------
  * Availability: 100 % (every report is served -- k-anon or DP fallback).
  * Privacy: reports served by the k-anon branch satisfy k-anonymity; reports
    served by the DP branch satisfy eps-geo-indistinguishability.  The mechanism
    therefore offers a per-report privacy guarantee everywhere, of one of two
    well-understood types, chosen by density.
  * Output validity: every reported location is a graph node (on-network).

References (mechanisms combined; the *combination and controller* are new)
-------------------------------------------------------------------------
[1] M. F. Mokbel et al., "The New Casper," VLDB, 2006.            (BFS cloaking)
[2] N. E. Bordenabe et al., "Optimal geo-indistinguishable
    mechanisms for location privacy," ACM CCS, 2014.       (graph projection)
[3] B. Niu et al., "Achieving k-anonymity in privacy-aware
    location-based services," IEEE INFOCOM, 2014.        (density adaptation)
"""

import json
import math
import heapq
from collections import defaultdict, deque

import numpy as np


def _haversine_m(lon1, lat1, lon2, lat2):
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class AdaptiveHybridAnonymizer:
    """
    Density-adaptive hybrid of graph k-anonymity and graph-constrained DP.

    Parameters
    ----------
    nodes, edges : str | list        -- graph (paths or preloaded, as elsewhere)
    k : int                          -- target anonymity level for the cloak branch
    epsilon : float                  -- privacy budget for the DP fallback branch
    region_cap : int                 -- base BFS size cap (dense areas use less)
    dist_cache : dict | None         -- shared all-pairs distances {src:{dst:m}}
    """

    K_DEFAULT = 3
    EPS_DEFAULT = 1.0
    REGION_CAP = 40           # base cap on cloaking-region node count

    def __init__(self, nodes, edges, k=K_DEFAULT, epsilon=EPS_DEFAULT,
                 region_cap=REGION_CAP, dist_cache=None):
        self.k = k
        self.epsilon = epsilon
        self.region_cap = region_cap
        self.graph, self.node_coords = self._load_graph(nodes, edges)
        self.sensitivity = self._estimate_sensitivity()
        # Cache node-id/coord arrays for fast DP projection.
        self._nid_list = list(self.node_coords.keys())
        self._coord_arr = np.array([self.node_coords[n] for n in self._nid_list],
                                   dtype=float)

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
        dists = []
        for node, nbrs in self.graph.items():
            for nb, _ in nbrs:
                dx = self.node_coords[node][0] - self.node_coords[nb][0]
                dy = self.node_coords[node][1] - self.node_coords[nb][1]
                dists.append(math.sqrt(dx * dx + dy * dy))
        return float(np.median(dists)) if dists else 0.01

    # ------------------------------------------------------------------
    # Density
    # ------------------------------------------------------------------
    def _local_density(self, node, density_map):
        node = str(node)
        total = density_map.get(node, 0)
        for nb, _ in self.graph.get(node, []):
            total += density_map.get(nb, 0)
        return total

    def _adaptive_cap(self, density, p66):
        """
        Region-size cap as a function of local density.  Dense nodes get a
        tight cap (they need little expansion); sparse nodes get the full base
        cap before we give up and use the DP fallback.
        """
        if p66 <= 0:
            return self.region_cap
        # Scale between 25% (very dense) and 100% (sparse) of the base cap.
        ratio = min(density / (p66 + 1e-9), 2.0)
        frac = max(0.25, 1.0 - 0.375 * ratio)
        return max(4, int(round(self.region_cap * frac)))

    # ------------------------------------------------------------------
    # Bounded BFS cloaking branch
    # ------------------------------------------------------------------
    def _bounded_region(self, origin, density_map, cap):
        """
        Grow a connected region until >= k users are covered or the region
        reaches `cap` nodes.  Returns (region, covered, hit_k).
        """
        origin = str(origin)
        region = {origin}
        frontier = deque([origin])
        visited = {origin}
        covered = density_map.get(origin, 0)
        hit_k = covered >= self.k

        while covered < self.k and frontier and len(region) < cap:
            cur = frontier.popleft()
            for nxt, _ in self.graph.get(cur, []):
                if nxt in visited:
                    continue
                visited.add(nxt)
                region.add(nxt)
                covered += density_map.get(nxt, 0)
                frontier.append(nxt)
                if covered >= self.k:
                    hit_k = True
                    break
                if len(region) >= cap:
                    break
        return region, covered, (covered >= self.k)

    def _medoid(self, region):
        cx = sum(self.node_coords[n][0] for n in region) / len(region)
        cy = sum(self.node_coords[n][1] for n in region) / len(region)
        return min(region, key=lambda n: (
            (self.node_coords[n][0] - cx) ** 2 +
            (self.node_coords[n][1] - cy) ** 2))

    # ------------------------------------------------------------------
    # DP fallback branch (density-adaptive privacy budget)
    # ------------------------------------------------------------------
    def _fallback_epsilon(self, density, p33, p66):
        """
        The fallback fires precisely where the cloaking branch could not gather
        k users, i.e. in sparse neighbourhoods -- exactly where anonymity is
        hardest and most needed (Niu et al.).  We therefore *strengthen* the DP
        budget (lower eps -> more noise -> more privacy) as density falls, so the
        hybrid raises privacy in sparse areas instead of leaving them exposed.
        """
        if density < p33:
            return self.epsilon * 0.5     # sparse: strongest fallback privacy
        elif density < p66:
            return self.epsilon * 0.75    # medium
        return self.epsilon               # (dense rarely reaches the fallback)

    def _dp_project(self, node, epsilon):
        ox, oy = self.node_coords[node]
        scale = self.sensitivity / max(epsilon, 1e-6)
        nx_ = ox + np.random.laplace(0, scale)
        ny_ = oy + np.random.laplace(0, scale)
        # Nearest graph node (vectorised Euclidean in coordinate space).
        d2 = ((self._coord_arr[:, 0] - nx_) ** 2 +
              (self._coord_arr[:, 1] - ny_) ** 2)
        proj = self._nid_list[int(np.argmin(d2))]
        return proj

    # ------------------------------------------------------------------
    # Main entry point (framework-standard interface)
    # ------------------------------------------------------------------
    def anonymize_snapshot(self, snapshot):
        """
        Returns {user_id: {
            "original_node", "cloaked_node", "cloaked_coords",
            "location_error"  (graph shortest-path metres),
            "mode"            ("kanon" | "gcdp"),
            "region"          (list[str], present when mode == "kanon"),
            "k_achieved"      (int),
            "k_satisfied"     (bool),
            "density"         (int),
        }}
        """
        density_map = defaultdict(int)
        for node in snapshot.values():
            density_map[str(node)] += 1

        # Density percentile thresholds for the adaptive cap and fallback eps.
        densities = [self._local_density(n, density_map)
                     for n in set(str(x) for x in snapshot.values())]
        if len(densities) >= 3:
            p33 = float(np.percentile(densities, 33))
            p66 = float(np.percentile(densities, 66))
        else:
            p33, p66 = 1.0, 1.0

        result = {}
        for uid, node in snapshot.items():
            node = str(node)
            density = self._local_density(node, density_map)
            cap = self._adaptive_cap(density, p66)
            region, covered, hit_k = self._bounded_region(node, density_map, cap)

            if hit_k:
                cloaked = self._medoid(region)
                err = self.dist_cache[node][cloaked]
                result[uid] = {
                    "original_node": node,
                    "cloaked_node": cloaked,
                    "cloaked_coords": self.node_coords[cloaked],
                    "location_error": err,
                    "mode": "kanon",
                    "region": list(region),
                    "k_achieved": covered,
                    "k_satisfied": True,
                    "density": density,
                }
            else:
                eps_fb = self._fallback_epsilon(density, p33, p66)
                proj = self._dp_project(node, eps_fb)
                err = self.dist_cache[node][proj]
                result[uid] = {
                    "original_node": node,
                    "cloaked_node": proj,
                    "cloaked_coords": self.node_coords[proj],
                    "location_error": err,
                    "mode": "gcdp",
                    "region": [proj],
                    "k_achieved": covered,
                    "k_satisfied": False,
                    "density": density,
                    "fallback_epsilon": eps_fb,
                }
        return result

    # ------------------------------------------------------------------
    def dist(self, u, v):
        return self.dist_cache[str(u)][str(v)]

    def get_dist_cache(self):
        return self.dist_cache


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
