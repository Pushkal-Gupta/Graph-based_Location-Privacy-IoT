import networkx as nx
import matplotlib.pyplot as plt
import random
import os
from statistics import mean
from typing import List, Set

# ======================================================================
# Smart City Graph
# ======================================================================

class SmartCityGraph:
    """
    Represents a smart city using a 2D grid graph.
    Provides node coordinates for realistic plotting.
    """

    def __init__(self, grid_size: int = 5, num_users: int = 80, seed: int = None):
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

    
    def classify_density_level(self, density: int) -> str:
        if density < 6:
            return "Sparse"
        elif density < 12:
            return "Medium"
        return "Dense"


    def select_adaptive_k(self, density: int) -> int:
        if density < 6:
            return 10
        elif density < 12:
            return 5
        return 2

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
# Experiment Manager
# ======================================================================

class DensityAwareAdaptiveKAnonymityExperiment:
    """Runs the Density-Aware Adaptive k-Anonymity simulation."""

    def __init__(self, algorithm: DensityAwareAdaptiveKAnonymityAlgorithm, runs: int = 20):
        self.algorithm = algorithm
        self.city = algorithm.city
        self.runs = runs

        self.densities = []
        self.k_values = []
        self.region_sizes = []

    def run_simulation(self):
        print("\n====== Running Density-Aware Adaptive k-Anonymity Experiment ======\n")

        all_nodes = list(self.city.graph.nodes())

        if self.runs > len(all_nodes):
            raise ValueError(f"Error: runs cannot exceed total number of nodes ({len(all_nodes)}).")

        available_nodes = random.sample(all_nodes, self.runs)

        for i in range(self.runs):
            target = available_nodes[i]  

            d = self.algorithm.compute_local_density(target)

            print(f"\n>>> Density Calculation for Run {i+1} (Target Node {target})")
            print(f"Users at target node {target}: {self.city.user_at_node[target]}")
            print(f"Neighbors of {target}: {self.city.neighbors(target)}")
            for neigh in self.city.neighbors(target):
                print(f"  Node {neigh}: {self.city.user_at_node[neigh]} users")
            print(f"--> Local Density = {d}")

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
# Visualization
# ======================================================================

class DensityAwareAdaptiveKAnonymityViz:

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
        nx.draw_networkx_nodes(city.graph, pos, nodelist=non_region_nodes, 
                               node_color="#E0E0E0", node_size=300)

        region_peers = [n for n in region if n != target]
        nx.draw_networkx_nodes(city.graph, pos, nodelist=region_peers, 
                               node_color="#FF6347", node_size=600)

        nx.draw_networkx_nodes(city.graph, pos, nodelist=[target], 
                               node_color="#FFD700", node_shape='*', node_size=900)

        nx.draw_networkx_labels(city.graph, pos, font_size=10)

        plt.title(
            f"Adaptive Anonymization Region\nTarget Node: {target} | Local Density: {density} | Required k: {k}",
            fontsize=12, fontweight='bold'
        )

        plt.axis('off')
        plt.savefig("results/region_visualization.png", dpi=300)
        plt.show()