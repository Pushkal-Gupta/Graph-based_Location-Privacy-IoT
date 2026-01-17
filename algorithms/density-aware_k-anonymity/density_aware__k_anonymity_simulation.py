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
# Density-Aware k-Anonymity Algorithm
# ======================================================================

class DensityAwareKAnonymityAlgorithm:
    """Implementation of the Density-Aware k-Anonymity logic."""

    def __init__(self, city: SmartCityGraph):
        self.city = city

    # 1. Density Computation --------------------------------------------------
    def compute_local_density(self, node: int, depth: int = 1) -> int:
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
    def classify_density_level(self, density: int) -> str:
        if density < 4:
            return "Sparse"
        elif density < 10:
            return "Medium"
        return "Dense"

    # 2. Adaptive k selection --------------------------------------------------
    def select_adaptive_k(self, density: int) -> int:
        if density < 4:
            return 10
        elif density < 10:
            return 5
        return 2

    # 3. Region expansion ------------------------------------------------------
    def expand_anonymization_region(self, start_node: int, k: int) -> Set[int]:
        region = {start_node}
        queue = [start_node]
        user_count = self.city.user_at_node[start_node]

        while user_count < k and queue:
            current = queue.pop(0)

            for neigh in self.city.neighbors(current):
                if neigh not in region:
                    region.add(neigh)
                    queue.append(neigh)
                    user_count += self.city.user_at_node[neigh]
                    if user_count >= k:
                        break

        return region


# ======================================================================
# Density-Aware k-Anonymity Experiment Manager
# ======================================================================

class DensityAwareKAnonymityExperiment:
    """Runs the Density-Aware k-Anonymity simulation multiple times."""

    def __init__(self, algorithm: DensityAwareKAnonymityAlgorithm, runs: int = 20):
        self.algorithm = algorithm
        self.city = algorithm.city
        self.runs = runs

        self.densities: List[int] = []
        self.k_values: List[int] = []
        self.region_sizes: List[int] = []

    def run_simulation(self):
        print("\n====== Running Density-Aware k-Anonymity Experiment ======\n")
        for i in range(self.runs):
            target = random.choice(list(self.city.graph.nodes()))

            d = self.algorithm.compute_local_density(target)
            k = self.algorithm.select_adaptive_k(d)
            region = self.algorithm.expand_anonymization_region(target, k)

            self.densities.append(d)
            self.k_values.append(k)
            self.region_sizes.append(len(region))

            print(
                f"Run {i+1:02d} | Target={target} | Density={d} "
                f"({self.algorithm.classify_density_level(d)}) | k={k} | Region Size={len(region)}"
            )

        print("\n====== Experiment Complete ======\n")
        return self.densities, self.k_values, self.region_sizes

    def get_experiment_summary(self):
        return {
            "avg_density": mean(self.densities),
            "avg_k": mean(self.k_values),
            "avg_region_size": mean(self.region_sizes),
            "max_region_size": max(self.region_sizes),
            "min_region_size": min(self.region_sizes)
        }


# ======================================================================
# Density-Aware k-Anonymity Visualization
# ======================================================================

class DensityAwareKAnonymityViz:
    """Visualization suite for the Density-Aware k-Anonymity results."""

    @staticmethod
    def ensure_results_folder():
        if not os.path.exists("results"):
            os.makedirs("results")

    @staticmethod
    def plot_density_vs_k(density, k):
        DensityAwareKAnonymityViz.ensure_results_folder()
        plt.figure()
        plt.scatter(density, k, color="darkblue")
        plt.xlabel("Local Density")
        plt.ylabel("Selected k")
        plt.title("Density-Aware k-Anonymity: Density vs k")
        plt.grid(True)
        plt.savefig("results/density_vs_k.png", dpi=300)
        plt.show()

    @staticmethod
    def plot_k_vs_region_size(k, region_size):
        DensityAwareKAnonymityViz.ensure_results_folder()
        plt.figure()
        plt.scatter(k, region_size, color="green")
        plt.xlabel("Selected k")
        plt.ylabel("Anonymization Region Size (nodes)")
        plt.title("Density-Aware k-Anonymity: k vs Region Size")
        plt.grid(True)
        plt.savefig("results/k_vs_region_size.png", dpi=300)
        plt.show()

    @staticmethod
    def visualize_specific_region(city: SmartCityGraph, region: Set[int], target: int, density: int, k: int):
        DensityAwareKAnonymityViz.ensure_results_folder()

        pos = city.positions
        plt.figure(figsize=(7, 7))
        nx.draw(city.graph, pos, with_labels=True, node_color="lightblue")

        # region nodes (excluding target)
        region_others = [node for node in region if node != target]
        nx.draw_networkx_nodes(city.graph, pos, nodelist=region_others, node_color="red")

        # target node highlighted
        nx.draw_networkx_nodes(city.graph, pos, nodelist=[target], node_color="yellow")

        plt.title(
            f"Density-Aware k-Anonymity Region\nTarget={target}, Density={density}, k={k}, Region Size={len(region)}"
        )
        plt.savefig("results/region_visualization.png", dpi=300)
        plt.show()


# ======================================================================
# MAIN EXECUTION
# ======================================================================

def main():
    # 1. Initialize the City and the Algorithm
    smart_city = SmartCityGraph(grid_size=5, num_users=30, seed=0)
    algorithm = DensityAwareKAnonymityAlgorithm(smart_city)

    # 2. Run the Experiment
    experiment_manager = DensityAwareKAnonymityExperiment(algorithm, runs=20)
    density_data, k_data, size_data = experiment_manager.run_simulation()

    # 3. Print Summary Statistics
    print("=== Density-Aware k-Anonymity Summary ===")
    for key, value in experiment_manager.get_experiment_summary().items():
        print(f"{key}: {value:.2f}")

    # 4. Generate Analytics Plots
    DensityAwareKAnonymityViz.plot_density_vs_k(density_data, k_data)
    DensityAwareKAnonymityViz.plot_k_vs_region_size(k_data, size_data)

    # 5. Visualize a Sample Run
    sample_node = random.choice(list(smart_city.graph.nodes()))
    sample_density = algorithm.compute_local_density(sample_node)
    sample_k = algorithm.select_adaptive_k(sample_density)
    sample_region = algorithm.expand_anonymization_region(sample_node, sample_k)
    
    DensityAwareKAnonymityViz.visualize_specific_region(
        smart_city, sample_region, sample_node, sample_density, sample_k
    )


if __name__ == "__main__":
    main()
