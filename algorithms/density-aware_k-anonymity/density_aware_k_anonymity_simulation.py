import networkx as nx
import matplotlib.pyplot as plt
import random
import os
from statistics import mean
from typing import Dict, List, Set, Tuple


# ======================================================================
# Smart City Graph
# ======================================================================

class SmartCityGraph:
    """
    Represents a smart city using a 2D grid graph.
    Provides node coordinates for realistic plotting.
    """

    def __init__(self, grid_size: int = 5, num_users: int = 30, seed: int = None):
        if seed is not None:
            random.seed(seed)

        self.grid_size = grid_size
        self.graph = nx.convert_node_labels_to_integers(nx.grid_2d_graph(grid_size, grid_size))
        self.num_users = num_users

        # Assign simple 2D coordinates for drawing
        self.positions = {node: (node % grid_size, node // grid_size) for node in self.graph.nodes()}

        # Populate users
        self.user_at_node = {node: 0 for node in self.graph.nodes()}
        self._populate_users()

    def _populate_users(self):
        nodes = list(self.graph.nodes())
        for _ in range(self.num_users):
            n = random.choice(nodes)
            self.user_at_node[n] += 1

    def neighbors(self, node: int):
        return list(self.graph.neighbors(node))


# ======================================================================
# ADKA Algorithm
# ======================================================================

class ADKAAlgorithm:
    """Adaptive Density-Aware k-Anonymity implementation."""

    def __init__(self, city: SmartCityGraph):
        self.city = city

    # 1. Density Computation --------------------------------------------------
    def compute_density(self, node: int, depth: int = 1) -> int:
        visited = {node}
        queue = [(node, 0)]
        total_users = self.city.user_at_node[node]

        while queue:
            current, d = queue.pop(0)
            if d == depth:
                continue

            for neigh in self.city.neighbors(current):
                if neigh not in visited:
                    visited.add(neigh)
                    queue.append((neigh, d + 1))
                    total_users += self.city.user_at_node[neigh]

        return total_users

    # Density Interpretation ---------------------------------------------------
    def classify_density(self, density: int) -> str:
        if density < 4:
            return "Sparse"
        elif density < 10:
            return "Medium"
        return "Dense"

    # 2. Adaptive k selection --------------------------------------------------
    def select_k(self, density: int) -> int:
        if density < 4:
            return 10
        elif density < 10:
            return 5
        return 2

    # 3. Region expansion ------------------------------------------------------
    def expand_region(self, start_node: int, k: int) -> Set[int]:
        region = {start_node}
        queue = [start_node]
        user_count = self.city.user_at_node[start_node]

        visited = set()

        while user_count < k and queue:
            current = queue.pop(0)
            visited.add(current)

            for neigh in self.city.neighbors(current):
                if neigh not in region:
                    region.add(neigh)
                    queue.append(neigh)
                    user_count += self.city.user_at_node[neigh]
                    if user_count >= k:
                        break

        return region


# ======================================================================
# ADKA Experiment Manager
# ======================================================================

class ADKAExperiment:
    """Runs ADKA multiple times to collect density/k/region statistics."""

    def __init__(self, adka: ADKAAlgorithm, runs: int = 20):
        self.adka = adka
        self.city = adka.city
        self.runs = runs

        self.densities: List[int] = []
        self.k_values: List[int] = []
        self.region_sizes: List[int] = []

    def run(self):
        print("\n====== Running ADKA Experiment ======\n")
        for i in range(self.runs):
            target = random.choice(list(self.city.graph.nodes()))

            d = self.adka.compute_density(target)
            k = self.adka.select_k(d)
            region = self.adka.expand_region(target, k)

            self.densities.append(d)
            self.k_values.append(k)
            self.region_sizes.append(len(region))

            print(
                f"Run {i+1:02d} | Target={target} | Density={d} "
                f"({self.adka.classify_density(d)}) | k={k} | Region Size={len(region)}"
            )

        print("\n====== Experiment Complete ======\n")

        return self.densities, self.k_values, self.region_sizes

    def summary(self):
        return {
            "avg_density": mean(self.densities),
            "avg_k": mean(self.k_values),
            "avg_region_size": mean(self.region_sizes),
            "max_region_size": max(self.region_sizes),
            "min_region_size": min(self.region_sizes)
        }


# ======================================================================
# Visualization Utilities
# ======================================================================

class ADKAViz:
    """Visualization suite for ADKA experiment."""

    @staticmethod
    def ensure_results_folder():
        if not os.path.exists("results"):
            os.makedirs("results")

    @staticmethod
    def plot_density_vs_k(density, k):
        ADKAViz.ensure_results_folder()
        plt.figure()
        plt.scatter(density, k, color="darkblue")
        plt.xlabel("Density")
        plt.ylabel("Selected k")
        plt.title("ADKA: Density vs Selected k")
        plt.grid(True)
        plt.savefig("results/density_vs_k.png", dpi=300)
        plt.show()

    @staticmethod
    def plot_k_vs_region_size(k, region_size):
        ADKAViz.ensure_results_folder()
        plt.figure()
        plt.scatter(k, region_size, color="green")
        plt.xlabel("Selected k")
        plt.ylabel("Region Size (nodes)")
        plt.title("ADKA: k vs Region Size")
        plt.grid(True)
        plt.savefig("results/k_vs_region_size.png", dpi=300)
        plt.show()

    @staticmethod
    def visualize_region(city: SmartCityGraph, region: Set[int], target: int, density: int, k: int):
        ADKAViz.ensure_results_folder()

        pos = city.positions

        plt.figure(figsize=(7, 7))
        nx.draw(city.graph, pos, with_labels=True, node_color="lightblue")

        # region nodes (excluding target)
        region_others = [node for node in region if node != target]
        nx.draw_networkx_nodes(city.graph, pos, nodelist=region_others, node_color="red")

        # target node highlighted
        nx.draw_networkx_nodes(city.graph, pos, nodelist=[target], node_color="yellow")

        plt.title(
            f"ADKA Region Visualization\nTarget={target}, Density={density}, k={k}, Region Size={len(region)}"
        )
        plt.savefig("results/region_visualization.png", dpi=300)
        plt.show()


# ======================================================================
# MAIN FUNCTION
# ======================================================================

def main():
    # Create city
    city = SmartCityGraph(grid_size=5, num_users=30, seed=0)
    adka = ADKAAlgorithm(city)

    # Run experiment
    experiment = ADKAExperiment(adka, runs=20)
    density_list, k_list, region_sizes = experiment.run()

    # Summary
    print("=== Experiment Summary ===")
    for key, value in experiment.summary().items():
        print(f"{key}: {value}")

    # Plots
    ADKAViz.plot_density_vs_k(density_list, k_list)
    ADKAViz.plot_k_vs_region_size(k_list, region_sizes)

    # Visualize a sample run
    target = random.choice(list(city.graph.nodes()))
    d = adka.compute_density(target)
    k = adka.select_k(d)
    region = adka.expand_region(target, k)
    ADKAViz.visualize_region(city, region, target, d, k)


if __name__ == "__main__":
    main()
