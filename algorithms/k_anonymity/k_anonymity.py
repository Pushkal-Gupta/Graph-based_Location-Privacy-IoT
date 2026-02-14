#!/usr/bin/env python3
"""
Graph-based k-Anonymity Core Module
==================================

Contains ONLY:
- City graph model
- Graph-based k-anonymity algorithm
- Privacy / utility metrics

No simulation, plotting, or execution logic.
"""

import networkx as nx
import random
import math
from typing import List, Tuple, Dict, Set


# ---------------------------------------------------------------------
# Smart City Graph
# ---------------------------------------------------------------------

class SmartCityGraph:
    """Graph-based city model."""

    def __init__(self, grid_size: int = 8):
        self.grid_size = grid_size
        self.graph = nx.Graph()
        self.users: Dict[int, int] = {}
        self.user_positions: Dict[int, Tuple[float, float]] = {}
        self._create_city_graph()

    def _create_city_graph(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                node = i * self.grid_size + j
                self.graph.add_node(node, pos=(i, j))

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                node = i * self.grid_size + j
                if j + 1 < self.grid_size:
                    self.graph.add_edge(node, node + 1)
                if i + 1 < self.grid_size:
                    self.graph.add_edge(node, node + self.grid_size)

    def add_users(self, num_users: int):
        nodes = list(self.graph.nodes())
        for uid in range(num_users):
            node = random.choice(nodes)
            self.users[uid] = node
            x, y = self.graph.nodes[node]["pos"]
            self.user_positions[uid] = (
                x + random.uniform(-0.3, 0.3),
                y + random.uniform(-0.3, 0.3)
            )

    def get_users_at_node(self, node_id: int) -> List[int]:
        return [
            u for u, n in self.users.items()
            if n == node_id
        ]


# ---------------------------------------------------------------------
# k-Anonymity Algorithm
# ---------------------------------------------------------------------

class KAnonymityPrivacyManager:
    """Graph-based spatial k-anonymity."""

    def __init__(self, city: SmartCityGraph, k: int):
        self.city = city
        self.k = k

    def find_k_anonymous_region(
        self, query_user: int
    ) -> Tuple[Set[int], List[int]]:

        start_node = self.city.users[query_user]
        visited = set()
        queue = [start_node]
        region_nodes = {start_node}
        users = {query_user}

        while queue and len(users) < self.k:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)

            users.update(self.city.get_users_at_node(node))

            for nbr in self.city.graph.neighbors(node):
                if nbr not in visited:
                    queue.append(nbr)
                    region_nodes.add(nbr)

        return region_nodes, list(users)

    def anonymized_location(
        self, query_user: int
    ) -> Tuple[float, float, Set[int], List[int]]:

        region_nodes, users = self.find_k_anonymous_region(query_user)

        positions = [
            self.city.graph.nodes[n]["pos"]
            for n in region_nodes
        ]

        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)

        return cx, cy, region_nodes, users


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------

class PrivacyAnalyzer:
    """Privacy and utility metrics."""

    @staticmethod
    def location_error(true_pos, anon_pos) -> float:
        return math.dist(true_pos, anon_pos)

    @staticmethod
    def region_size(region_nodes: Set[int], city: SmartCityGraph) -> float:
        coords = [city.graph.nodes[n]["pos"] for n in region_nodes]
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        return (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)