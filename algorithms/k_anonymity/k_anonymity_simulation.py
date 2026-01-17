#!/usr/bin/env python3
"""
Graph-based k-Anonymity Simulation for Location Privacy in IoT Smart Cities
===========================================================================

This implementation demonstrates a spatial privacy approach where user
locations are generalized using connected subgraphs to achieve k-anonymity.

Author: Pushkal Gupta
Date: January 2026
"""

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import random
import json
import math
from typing import List, Tuple, Dict, Set


# ---------------------------------------------------------------------
# Smart City Graph
# ---------------------------------------------------------------------

class SmartCityGraph:
    """Represents a smart city as a graph with intersections and roads."""

    def __init__(self, grid_size: int = 8):
        self.grid_size = grid_size
        self.graph = nx.Graph()
        self.users: Dict[int, int] = {}
        self.user_positions: Dict[int, Tuple[float, float]] = {}
        self._create_city_graph()

    def _create_city_graph(self):
        """Create a grid-based city graph with intersections and roads."""

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                node_id = i * self.grid_size + j
                self.graph.add_node(
                    node_id,
                    pos=(i, j),
                    intersection_type="normal"
                )

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                current = i * self.grid_size + j

                if j < self.grid_size - 1:
                    right = i * self.grid_size + (j + 1)
                    self.graph.add_edge(current, right, road_type="street")

                if i < self.grid_size - 1:
                    down = (i + 1) * self.grid_size + j
                    self.graph.add_edge(current, down, road_type="avenue")

        for i in range(0, self.grid_size - 1, 2):
            for j in range(0, self.grid_size - 1, 2):
                if random.random() > 0.7:
                    current = i * self.grid_size + j
                    diagonal = (i + 1) * self.grid_size + (j + 1)
                    self.graph.add_edge(
                        current,
                        diagonal,
                        road_type="diagonal"
                    )

    def add_users(self, num_users: int):
        """Add users randomly distributed across the city."""

        nodes = list(self.graph.nodes())
        for user_id in range(num_users):
            node = random.choice(nodes)
            self.users[user_id] = node

            base_x, base_y = self.graph.nodes[node]["pos"]
            self.user_positions[user_id] = (
                base_x + random.uniform(-0.3, 0.3),
                base_y + random.uniform(-0.3, 0.3)
            )

    def get_users_at_node(self, node_id: int) -> List[int]:
        """Return users present at a given node."""
        return [
            user_id
            for user_id, user_node in self.users.items()
            if user_node == node_id
        ]

    def move_user(self, user_id: int, new_node: int):
        """Move a user to another node."""
        if new_node in self.graph.nodes:
            self.users[user_id] = new_node
            base_x, base_y = self.graph.nodes[new_node]["pos"]
            self.user_positions[user_id] = (
                base_x + random.uniform(-0.3, 0.3),
                base_y + random.uniform(-0.3, 0.3)
            )


# ---------------------------------------------------------------------
# k-Anonymity Privacy Manager
# ---------------------------------------------------------------------

class KAnonymityPrivacyManager:
    """Graph-based k-anonymity using connected subgraphs."""

    def __init__(self, city_graph: SmartCityGraph, k: int = 3):
        self.city = city_graph
        self.k = k

    def find_k_anonymous_region(
        self,
        query_user: int
    ) -> Tuple[Set[int], List[int]]:

        query_node = self.city.users[query_user]
        visited = set()
        queue = [query_node]
        region_nodes = {query_node}
        users_in_region = {query_user}

        while queue and len(users_in_region) < self.k:
            current_node = queue.pop(0)

            if current_node in visited:
                continue

            visited.add(current_node)
            users_in_region.update(
                self.city.get_users_at_node(current_node)
            )

            if len(users_in_region) >= self.k:
                break

            for neighbor in self.city.graph.neighbors(current_node):
                if neighbor not in visited:
                    queue.append(neighbor)
                    region_nodes.add(neighbor)

        return region_nodes, list(users_in_region)

    def get_anonymized_location(
        self,
        query_user: int
    ) -> Tuple[float, float, Set[int], List[int]]:

        region_nodes, users_in_region = self.find_k_anonymous_region(
            query_user
        )

        if len(users_in_region) < self.k:
            region_nodes = set(
                list(self.city.graph.nodes())[: self.k]
            )

        positions = [
            self.city.graph.nodes[node]["pos"]
            for node in region_nodes
        ]

        centroid_x = sum(p[0] for p in positions) / len(positions)
        centroid_y = sum(p[1] for p in positions) / len(positions)

        return centroid_x, centroid_y, region_nodes, users_in_region


# ---------------------------------------------------------------------
# Privacy Analysis
# ---------------------------------------------------------------------

class PrivacyAnalyzer:
    """Privacy vs utility metrics."""

    @staticmethod
    def calculate_location_error(
        true_pos: Tuple[float, float],
        anon_pos: Tuple[float, float]
    ) -> float:
        return math.dist(true_pos, anon_pos)

    @staticmethod
    def calculate_region_size(
        region_nodes: Set[int],
        city: SmartCityGraph
    ) -> float:

        if len(region_nodes) <= 1:
            return 0.0

        positions = [
            city.graph.nodes[node]["pos"]
            for node in region_nodes
        ]

        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]

        return (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)


# ---------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------

def run_simulation(
    grid_size: int = 8,
    num_users: int = 20,
    k_values: List[int] = [2, 3, 5, 7]
):

    print("Initializing graph-based k-anonymity simulation")
    print(f"Grid size: {grid_size}x{grid_size}")
    print(f"Users: {num_users}")
    print(f"k-values: {k_values}")
    print("-" * 60)

    city = SmartCityGraph(grid_size)
    city.add_users(num_users)

    results = {
        "k_values": k_values,
        "privacy_errors": [],
        "region_sizes": [],
        "user_coverage": []
    }

    for k in k_values:
        print(f"\nTesting k-anonymity with k = {k}")
        manager = KAnonymityPrivacyManager(city, k)

        errors = []
        region_sizes = []
        successful = 0

        for user_id in range(num_users):
            try:
                true_pos = city.user_positions[user_id]
                anon_x, anon_y, region_nodes, users = (
                    manager.get_anonymized_location(user_id)
                )

                if len(users) >= k:
                    successful += 1
                    errors.append(
                        PrivacyAnalyzer.calculate_location_error(
                            true_pos,
                            (anon_x, anon_y)
                        )
                    )
                    region_sizes.append(
                        PrivacyAnalyzer.calculate_region_size(
                            region_nodes,
                            city
                        )
                    )

            except Exception as e:
                print(f"Error for user {user_id}: {e}")

        results["privacy_errors"].append(
            np.mean(errors) if errors else float("inf")
        )
        results["region_sizes"].append(
            np.mean(region_sizes) if region_sizes else 0
        )
        results["user_coverage"].append(
            (successful / num_users) * 100
        )

        print(f"Average location error: {results['privacy_errors'][-1]:.2f}")
        print(f"Average region size: {results['region_sizes'][-1]:.2f}")
        print(f"User coverage: {results['user_coverage'][-1]:.1f}%")

    return city, results


# ---------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------

def visualize_simulation(
    city: SmartCityGraph,
    k: int = 3,
    sample_users: List[int] = None
):

    if sample_users is None:
        sample_users = list(range(min(5, len(city.users))))

    manager = KAnonymityPrivacyManager(city, k)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    pos = nx.get_node_attributes(city.graph, "pos")

    ax1.set_title("Original User Locations")
    nx.draw(
        city.graph,
        pos,
        ax=ax1,
        node_color="lightgray",
        node_size=100,
        edge_color="gray",
        alpha=0.6
    )

    for uid, (x, y) in city.user_positions.items():
        ax1.scatter(
            x,
            y,
            c="red" if uid in sample_users else "blue",
            s=100 if uid in sample_users else 50,
            alpha=1.0 if uid in sample_users else 0.6,
            edgecolor="black"
        )

    ax1.set_aspect("equal")
    ax1.grid(True)

    ax2.set_title(f"k-Anonymous Regions (k={k})")
    nx.draw(
        city.graph,
        pos,
        ax=ax2,
        node_color="lightgray",
        node_size=100,
        edge_color="gray",
        alpha=0.6
    )

    colors = ["red", "green", "orange", "purple", "brown"]

    for i, uid in enumerate(sample_users):
        anon_x, anon_y, region_nodes, _ = (
            manager.get_anonymized_location(uid)
        )
        color = colors[i % len(colors)]

        positions = [
            city.graph.nodes[n]["pos"]
            for n in region_nodes
        ]
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]

        polygon = Polygon(
            [
                (min(xs) - 0.4, min(ys) - 0.4),
                (max(xs) + 0.4, min(ys) - 0.4),
                (max(xs) + 0.4, max(ys) + 0.4),
                (min(xs) - 0.4, max(ys) + 0.4),
            ],
            alpha=0.2,
            color=color
        )
        ax2.add_patch(polygon)

        ax2.scatter(
            anon_x,
            anon_y,
            c=color,
            s=200,
            marker="*",
            edgecolor="black"
        )

    ax2.set_aspect("equal")
    ax2.grid(True)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    city, results = run_simulation(
        grid_size=8,
        num_users=25,
        k_values=[2, 3, 4, 5, 6]
    )

    fig1 = visualize_simulation(city, k=3)
    plt.savefig("k_anonymity_demo.png", dpi=300, bbox_inches="tight")

    with open("simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Simulation completed successfully.")
    plt.show()


if __name__ == "__main__":
    main()
