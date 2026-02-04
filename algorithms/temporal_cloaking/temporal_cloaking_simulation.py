#!/usr/bin/env python3
"""
Temporal Cloaking for Trajectory Privacy in IoT Smart Cities
===========================================================

This implementation demonstrates temporal privacy by reducing the temporal
resolution of location updates, preventing trajectory-based re-identification.

Author: Nagasai Dattu
Date: February 2026
"""

import networkx as nx
import matplotlib.pyplot as plt
import random
import json
import os
from statistics import mean
from typing import List, Dict, Tuple


# ---------------------------------------------------------------------
# Smart City Temporal Simulator
# ---------------------------------------------------------------------

class SmartCityTemporalGraph:
    """Simulates user trajectories over a graph-based smart city."""

    def __init__(
        self,
        grid_size: int = 5,
        num_users: int = 20,
        time_steps: int = 10,
        seed: int = None,
    ):
        if seed is not None:
            random.seed(seed)

        self.grid_size = grid_size
        self.num_users = num_users
        self.time_steps = time_steps

        self.graph = nx.convert_node_labels_to_integers(
            nx.grid_2d_graph(grid_size, grid_size)
        )
        self.positions = {
            node: (node % grid_size, node // grid_size)
            for node in self.graph.nodes()
        }

        self.trajectories = self._generate_trajectories()

    def _generate_trajectories(self) -> Dict[int, List[int]]:
        trajectories = {}
        nodes = list(self.graph.nodes())

        for user_id in range(self.num_users):
            current = random.choice(nodes)
            path = [current]

            for _ in range(self.time_steps - 1):
                current = random.choice(list(self.graph.neighbors(current)))
                path.append(current)

            trajectories[user_id] = path

        return trajectories


# ---------------------------------------------------------------------
# Temporal Cloaking Mechanism
# ---------------------------------------------------------------------

class TemporalCloakingAlgorithm:
    """Implements temporal cloaking using fixed temporal windows."""

    def __init__(self, temporal_window: int = 3):
        self.temporal_window = temporal_window

    def apply(self, trajectory: List[int]) -> List[Tuple[int, int]]:
        cloaked = []

        for t in range(0, len(trajectory), self.temporal_window):
            window = trajectory[t : t + self.temporal_window]
            representative = random.choice(window)
            cloaked.append((t, representative))

        return cloaked


# ---------------------------------------------------------------------
# Temporal Privacy–Utility Analyzer
# ---------------------------------------------------------------------

class TemporalPrivacyAnalyzer:
    """Analyzes privacy–utility tradeoffs for temporal cloaking."""

    @staticmethod
    def reduction_ratio(original_len: int, cloaked_len: int) -> float:
        return cloaked_len / original_len

    @staticmethod
    def trajectory_distortion(
        original: List[int], cloaked: List[Tuple[int, int]]
    ) -> float:
        cloaked_locations = {loc for _, loc in cloaked}
        hidden = sum(1 for loc in original if loc not in cloaked_locations)
        return hidden / len(original)


# ---------------------------------------------------------------------
# Experiment Runner
# ---------------------------------------------------------------------

def run_temporal_cloaking_simulation():
    print("Temporal Cloaking for Trajectory Privacy in IoT Smart Cities")
    print("=" * 70)

    city = SmartCityTemporalGraph(
        grid_size=5, num_users=20, time_steps=10, seed=0
    )
    cloaker = TemporalCloakingAlgorithm(temporal_window=3)
    analyzer = TemporalPrivacyAnalyzer()

    results = {}

    for user_id, trajectory in city.trajectories.items():
        cloaked = cloaker.apply(trajectory)

        reduction = analyzer.reduction_ratio(
            len(trajectory), len(cloaked)
        )
        distortion = analyzer.trajectory_distortion(
            trajectory, cloaked
        )

        results[user_id] = {
            "original_updates": len(trajectory),
            "cloaked_updates": len(cloaked),
            "reduction_ratio": reduction,
            "trajectory_distortion": distortion,
        }

        print(
            f"User {user_id:02d} | "
            f"Original={len(trajectory)} | "
            f"Cloaked={len(cloaked)} | "
            f"Reduction={reduction:.2f} | "
            f"Distortion={distortion:.2f}"
        )

    summary = {
        "avg_original_updates": mean(
            v["original_updates"] for v in results.values()
        ),
        "avg_cloaked_updates": mean(
            v["cloaked_updates"] for v in results.values()
        ),
        "avg_reduction_ratio": mean(
            v["reduction_ratio"] for v in results.values()
        ),
        "avg_trajectory_distortion": mean(
            v["trajectory_distortion"] for v in results.values()
        ),
    }

    return city, results, summary


# ---------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------

def visualize_results(city, results):
    os.makedirs("results", exist_ok=True)

    original = [v["original_updates"] for v in results.values()]
    cloaked = [v["cloaked_updates"] for v in results.values()]

    plt.figure()
    plt.scatter(original, cloaked, color="purple")
    plt.xlabel("Original Updates")
    plt.ylabel("Cloaked Updates")
    plt.title("Temporal Cloaking: Update Reduction")
    plt.grid(True)
    plt.savefig("results/update_reduction.png", dpi=300)
    plt.show()

    sample_user = next(iter(city.trajectories))
    trajectory = city.trajectories[sample_user]
    cloaked_nodes = [
        loc for _, loc in TemporalCloakingAlgorithm().apply(trajectory)
    ]

    plt.figure(figsize=(7, 7))
    nx.draw(city.graph, city.positions, node_color="lightblue", with_labels=True)
    nx.draw_networkx_nodes(
        city.graph, city.positions, nodelist=trajectory, node_color="gray"
    )
    nx.draw_networkx_nodes(
        city.graph, city.positions, nodelist=cloaked_nodes, node_color="red"
    )
    plt.title(f"Temporal Cloaking Trajectory (User {sample_user})")
    plt.savefig("results/trajectory_visualization.png", dpi=300)
    plt.show()


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    city, results, summary = run_temporal_cloaking_simulation()

    visualize_results(city, results)

    with open("results/temporal_cloaking_results.json", "w") as f:
        json.dump(
            {"per_user": results, "summary": summary},
            f,
            indent=2,
        )

    print("\n=== Summary Statistics ===")
    for k, v in summary.items():
        print(f"{k}: {v:.3f}")


if __name__ == "__main__":
    main()