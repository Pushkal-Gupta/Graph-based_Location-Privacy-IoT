import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

        self.positions = {node: (node % grid_size, node // grid_size) for node in self.graph.nodes()}

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
# Density-Aware Adaptive k-Anonymity Algorithm
# ======================================================================

class DensityAwareAdaptiveKAnonymityAlgorithm:
    """Implementation of the Density-Aware Adaptive k-Anonymity (DAAKA) logic."""

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
        if density < 6:
            return "Sparse"
        elif density < 12:
            return "Medium"
        return "Dense"

    # 2. Adaptive k selection --------------------------------------------------
    def select_adaptive_k(self, density: int) -> int:
        if density < 6:
            return 10
        elif density < 12:
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
# Density-Aware Adaptive k-Anonymity Experiment Manager
# ======================================================================

class DensityAwareAdaptiveKAnonymityExperiment:
    """Runs the Density-Aware Adaptive k-Anonymity simulation multiple times."""

    def __init__(self, algorithm: DensityAwareAdaptiveKAnonymityAlgorithm, runs: int = 20):
        self.algorithm = algorithm
        self.city = algorithm.city
        self.runs = runs

        self.densities: List[int] = []
        self.k_values: List[int] = []
        self.region_sizes: List[int] = []

    def run_simulation(self):
        print("\n====== Running Density-Aware Adaptive k-Anonymity Experiment ======\n")
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
# Density-Aware Adaptive k-Anonymity Visualization
# ======================================================================

class DensityAwareAdaptiveKAnonymityViz:
    """Visualization suite for the Density-Aware Adaptive k-Anonymity results."""

    @staticmethod
    def ensure_results_folder():
        if not os.path.exists("results"):
            os.makedirs("results")

    @staticmethod
    def plot_density_vs_adaptive_k(density, k):
        DensityAwareAdaptiveKAnonymityViz.ensure_results_folder()
        plt.figure()
        plt.scatter(density, k, color="darkblue", alpha=0.7)
        plt.xlim(0, max(density) + 2)
        plt.ylim(0, 12)
        plt.yticks([2, 5, 10]) 
        plt.xlabel("Local Density (users in neighborhood)")
        plt.ylabel("Selected Adaptive k")
        plt.title("Density-Aware Adaptive k-Anonymity: Density vs k")
        plt.grid(True)
        plt.savefig("results/density_vs_k.png", dpi=300)
        plt.show()

    @staticmethod
    def plot_k_vs_region_size(k, region_size):
        DensityAwareAdaptiveKAnonymityViz.ensure_results_folder()
        plt.figure()
        plt.scatter(k, region_size, color="green", alpha=0.7)
        plt.xticks([2, 5, 10])
        plt.xlabel("Selected Adaptive k")
        plt.ylabel("Anonymization Region Size (nodes)")
        plt.title("Density-Aware Adaptive k-Anonymity: k vs Region Size")
        plt.grid(True)
        plt.savefig("results/k_vs_region_size.png", dpi=300)
        plt.show()

    @staticmethod
    def visualize_specific_region(city: SmartCityGraph, region: Set[int], target: int, density: int, k: int):
        DensityAwareAdaptiveKAnonymityViz.ensure_results_folder()
        pos = city.positions
        
        plt.figure(figsize=(8, 8))
        
        nx.draw_networkx_edges(city.graph, pos, edge_color="#d3d3d3", width=1.0, alpha=0.5)

        region_subgraph = city.graph.subgraph(region)
        nx.draw_networkx_edges(region_subgraph, pos, edge_color="#FF6347", width=2.5)

        non_region_nodes = [n for n in city.graph.nodes() if n not in region]
        nx.draw_networkx_nodes(
            city.graph, pos, nodelist=non_region_nodes, 
            node_color="#E0E0E0", node_size=300
        )
        
        region_peers = [n for n in region if n != target]
        nx.draw_networkx_nodes(
            city.graph, pos, nodelist=region_peers, 
            node_color="#FF6347", node_size=600, label="Region Peer"
        )
        
        nx.draw_networkx_nodes(
            city.graph, pos, nodelist=[target], 
            node_color="#FFD700", node_shape='*', node_size=900, label="Target User"
        )

        nx.draw_networkx_labels(city.graph, pos, font_size=10, font_family="sans-serif")

        target_patch = mpatches.Patch(color='#FFD700', label='Target User')
        peer_patch = mpatches.Patch(color='#FF6347', label=f'Anonymity Group (Size: {len(region)})')
        bg_patch = mpatches.Patch(color='#E0E0E0', label='Other Nodes')
        
        plt.legend(handles=[target_patch, peer_patch, bg_patch], loc='upper left')

        plt.title(
            f"Adaptive Anonymization Region\nTarget Node: {target} | Local Density: {density} | Required k: {k}", 
            fontsize=12, fontweight='bold'
        )
        
        plt.axis('off')
        plt.savefig("results/region_visualization.png", dpi=300)
        plt.show()


# ======================================================================
# MAIN EXECUTION
# ======================================================================

def main():
    smart_city = SmartCityGraph(grid_size=5, num_users=80, seed=42)
    algorithm = DensityAwareAdaptiveKAnonymityAlgorithm(smart_city)

    experiment_manager = DensityAwareAdaptiveKAnonymityExperiment(algorithm, runs=30)
    density_data, k_data, size_data = experiment_manager.run_simulation()

    print("=== Density-Aware Adaptive k-Anonymity Summary ===")
    for key, value in experiment_manager.get_experiment_summary().items():
        print(f"{key}: {value:.2f}")

    DensityAwareAdaptiveKAnonymityViz.plot_density_vs_adaptive_k(density_data, k_data)
    DensityAwareAdaptiveKAnonymityViz.plot_k_vs_region_size(k_data, size_data)

    print("\nSearching for an interesting region to visualize...")
    max_attempts = 100
    for _ in range(max_attempts):
        sample_node = random.choice(list(smart_city.graph.nodes()))
        sample_density = algorithm.compute_local_density(sample_node)
        sample_k = algorithm.select_adaptive_k(sample_density)
        sample_region = algorithm.expand_anonymization_region(sample_node, sample_k)
        
        if 4 <= len(sample_region) <= 15:
            print(f"Visualizing interesting node {sample_node} with region size {len(sample_region)}")
            DensityAwareAdaptiveKAnonymityViz.visualize_specific_region(
                smart_city, sample_region, sample_node, sample_density, sample_k
            )
            break


if __name__ == "__main__":
    main()
