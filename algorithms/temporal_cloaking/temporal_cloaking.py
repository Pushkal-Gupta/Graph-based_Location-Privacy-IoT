"""
Trajectory Privacy via Temporal Cloaking on a Road-Network Graph
=================================================================

References
----------
[1] Gruteser, M. & Grunwald, D. (2003). Anonymous Usage of Location-Based
    Services Through Spatial and Temporal Cloaking.
    Proc. MobiSys 2003, pp. 31-42.
    -- Introduces *temporal* cloaking alongside spatial cloaking:
       a location update is delayed until k other users have reported
       within the same time interval, preventing timing-based
       re-identification.  Our algorithm follows this delay-until-k
       model.

[2] Gedik, B. & Liu, L. (2008). Protecting Location Privacy with
    Personalized k-Anonymity.
    IEEE Trans. Mobile Computing, 7(1), 1-18.
    -- Evaluation framework for cloaking systems: location error
       and region size as primary metrics.

[3] Chow, C.-Y. & Mokbel, M. F. (2011). Trajectory Privacy in
    Location-Based Services and Data Publication.
    ACM SIGKDD Explorations, 13(1), 19-29.
    -- Formalises trajectory privacy: an attacker who observes
       anonymised trajectory segments should not be able to link
       them to a single user.  Temporal cloaking reduces linkability
       by merging users within time windows.

[4] Xu, T. & Cai, Y. (2009). Exploring Historical Location Data for
    Anonymity Preservation in Location-Based Services.
    Proc. INFOCOM 2009, pp. 547-555.
    -- Shows that temporal correlation of location updates is a major
       privacy leak; temporal cloaking breaks this correlation.

[5] Mokbel, M. F., Chow, C.-Y., & Aref, W. G. (2006).
    The New Casper.  Proc. VLDB 2006.
    -- BFS expansion design reused for the spatial component.

Algorithm: Temporal Window Cloaking with Graph-Based Spatial Merging
    (Combining temporal delay from [1] with graph cloaking from [5])

    Input : trajectories T = {user_id: [(node, timestamp), ...]},
            time window Δt (seconds), anonymity parameter k
    Process:
      1. Divide the timeline into non-overlapping windows of size Δt
      2. For each window W = [t, t+Δt):
           a. Collect all users who report during W
           b. If |users| < k: expand W forward (increase delay)
              until k users are found or a timeout is reached
           c. For all users in the final group:
              - cloaked_node <- medoid of their node set (graph-aware)
              - temporal_delay <- |expanded W| - Δt
      3. Error = graph shortest-path dist(original, cloaked)
    Output: per-user {original_node, cloaked_node, group_size, delay}
"""

import json
import csv
import math
import heapq
import bisect
from collections import defaultdict, deque
from datetime import datetime, timedelta


class LazyDistCache:
    """Computes Dijkstra shortest paths on-demand and caches them."""
    def __init__(self, graph):
        self.graph = graph
        self.cache = {}

    def get_dist(self, u, v):
        if u not in self.cache:
            self.cache[u] = {}
        if v not in self.cache[u]:
            self.cache[u][v] = self._single_pair_dijkstra(u, v)
        return self.cache[u][v]

    def _single_pair_dijkstra(self, source, target):
        if source == target: 
            return 0.0
            
        dist = {source: 0.0}
        pq = [(0.0, source)]
        
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, math.inf):
                continue
                
            if u == target:
                return d
                
            for v, w in self.graph.get(u, []):
                nd = d + w
                if nd < dist.get(v, math.inf):
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
                    
        return math.inf # Unreachable


class TemporalCloaker:
    """
    Temporal cloaking for trajectory privacy on a road-network graph.

    Implements the temporal delay model of Gruteser & Grunwald (2003)
    [1] on a road-network graph, using medoid-based spatial merging
    (following the connected-subgraph model of [5]).

    For each time window, users whose reports fall within the window
    are grouped; if fewer than k users are present, the window is
    expanded forward until k users are collected.  All grouped users
    then report the graph medoid of their node set.
    """

    def __init__(self, nodes, edges, k=5, window_sec=600, dist_cache=None):
        """
        Parameters
        ----------
        nodes : str | list
        edges : str | list
        k : int
            Minimum group size (anonymity parameter).
        window_sec : int
            Base time window in seconds.
        dist_cache : dict | None | LazyDistCache
            Pre-computed distances or an instance of LazyDistCache.
        """
        self.k = k
        self.window_sec = window_sec
        self.graph, self.node_coords = self._load_graph(nodes, edges)

        if dist_cache is not None:
            self.dist_cache = dist_cache
        else:
            n = len(self.graph)
            print(f"  Setting up lazy distance cache ({n} nodes)...")
            self.dist_cache = LazyDistCache(self.graph)

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
    def _medoid(self, node_set):
        """Graph node closest (Euclidean) to the centroid of node_set."""
        nodes = [str(n) for n in node_set if str(n) in self.node_coords]
        if not nodes:
            return str(list(node_set)[0])
        cx = sum(self.node_coords[n][0] for n in nodes) / len(nodes)
        cy = sum(self.node_coords[n][1] for n in nodes) / len(nodes)
        return min(nodes, key=lambda n: (
            (self.node_coords[n][0] - cx) ** 2 +
            (self.node_coords[n][1] - cy) ** 2
        ))

    # ------------------------------------------------------------------
    # Core algorithm  [Gruteser & Grunwald 2003, Section 3.2]
    # ------------------------------------------------------------------
    def cloak_trajectories(self, trajectories):
        """
        Apply temporal cloaking to a set of user trajectories.

        Parameters
        ----------
        trajectories : dict
            {user_id: [(node_id, datetime), ...]}  sorted by time.

        Returns
        -------
        records : list[dict]
            Per-event cloaking records.
        """
        # Flatten all events
        events = []
        for user, traj in trajectories.items():
            for node, ts in traj:
                events.append((user, str(node), ts))

        if not events:
            return []

        events.sort(key=lambda x: x[2])
        
        # Extract timestamps for fast binary search
        timestamps = [e[2] for e in events]
        
        start_time = events[0][2]
        end_time   = events[-1][2]
        base_delta = timedelta(seconds=self.window_sec)
        max_expand = 5  # max number of expansions to prevent infinite loops

        records = []
        cur_start = start_time

        while cur_start <= end_time:
            cur_end = cur_start + base_delta

            # O(log N) fast slice instead of slow O(N) list comprehension
            left_idx = bisect.bisect_left(timestamps, cur_start)
            right_idx = bisect.bisect_left(timestamps, cur_end)
            window_events = events[left_idx:right_idx]
            
            users_in_window = set(e[0] for e in window_events)

            # Expansion loop [1]: widen window until k users are found
            expansions = 0
            actual_end = cur_end
            
            while len(users_in_window) < self.k and expansions < max_expand:
                actual_end += base_delta
                if actual_end > end_time + base_delta:
                    break
                    
                # Re-slice with binary search to include new window width
                right_idx = bisect.bisect_left(timestamps, actual_end)
                window_events = events[left_idx:right_idx]
                users_in_window = set(e[0] for e in window_events)
                expansions += 1

            if len(users_in_window) >= self.k:
                # Compute cloaked location (medoid of all nodes in window)
                all_nodes = set(e[1] for e in window_events)
                cloaked = self._medoid(all_nodes)

                delay_sec = max(0.0, (actual_end - cur_end).total_seconds())

                # Each user's last event in the window is the representative
                user_last = {}
                for user, node, ts in window_events:
                    if user not in user_last or ts > user_last[user][1]:
                        user_last[user] = (node, ts)

                for user, (orig_node, ts) in user_last.items():
                    orig_node = str(orig_node)
                    
                    # Compute distance lazily
                    err = self.dist_cache.get_dist(orig_node, cloaked)
                    
                    records.append({
                        "user":           user,
                        "original_node":  orig_node,
                        "cloaked_node":   cloaked,
                        "cloaked_coords": self.node_coords.get(cloaked, (0, 0)),
                        "group_size":     len(users_in_window),
                        "temporal_delay": delay_sec,
                        "location_error": err,
                        "k_achieved":     len(users_in_window),
                        "window_start":   cur_start,
                        "window_end":     actual_end,
                    })

            # Advance past the processed window
            cur_start = max(cur_end, actual_end)

        return records

    # ------------------------------------------------------------------
    def dist(self, u, v):
        return self.dist_cache.get_dist(str(u), str(v))

    def get_dist_cache(self):
        return self.dist_cache