import networkx as nx
import matplotlib.pyplot as plt
import random
import os
import pickle                    # ← ADD THIS LINE
from statistics import mean
from typing import Set

class SmartCityGraph:
    def __init__(self, grid_size=5, user_counts_file=None, bounds=None, seed=42):
        if seed is not None:
            random.seed(seed)
        self.grid_size = grid_size
        self.graph = nx.convert_node_labels_to_integers(nx.grid_2d_graph(grid_size, grid_size))

        # Geographic positions
        if bounds:
            min_lat, max_lat, min_lon, max_lon = bounds
            lat_step = (max_lat - min_lat) / grid_size
            lon_step = (max_lon - min_lon) / grid_size
            self.positions = {}
            for node in self.graph.nodes():
                row = node // grid_size
                col = node % grid_size
                self.positions[node] = (min_lon + col * lon_step + lon_step/2,
                                       min_lat + row * lat_step + lat_step/2)
        else:
            self.positions = {node: (node % grid_size, node // grid_size) for node in self.graph.nodes()}

        # ==================== IMPROVED LOADING ====================
        self.user_at_node = {node: 0 for node in self.graph.nodes()}

        if user_counts_file and os.path.exists(user_counts_file):
            try:
                with open(user_counts_file, 'rb') as f:
                    counts = pickle.load(f)
                for node in self.user_at_node:
                    self.user_at_node[node] = counts.get(node, 0)
                total_users = sum(self.user_at_node.values())
                print(f"Loaded GeoLife data → {total_users} unique users across grid")
            except Exception as e:
                print(f"Error loading {user_counts_file}: {e}")
                print("Falling back to random users")
                self._populate_random_users()
        else:
            print("No user_counts.pkl found → using random synthetic users")
            self._populate_random_users()
        # ========================================================

    def _populate_random_users(self):
        """Fallback when no real data is available"""
        nodes = list(self.graph.nodes())
        for _ in range(80):                    # Only used when no GeoLife data
            n = random.choice(nodes)
            self.user_at_node[n] += 1

    def neighbors(self, node):
        return list(self.graph.neighbors(node))


class DensityAwareAdaptiveKAnonymityAlgorithm:
    def __init__(self, city):
        self.city = city

    def compute_local_density(self, node, depth=1):
        visited = {node}
        queue = [(node, 0)]
        total = self.city.user_at_node[node]

        while queue:
            curr, d = queue.pop(0)
            if d >= depth: continue
            for neigh in self.city.neighbors(curr):
                if neigh not in visited:
                    visited.add(neigh)
                    queue.append((neigh, d+1))
                    total += self.city.user_at_node[neigh]
        return total

    def classify_density_level(self, density):
        if density < 10: return "Sparse"
        elif density < 30: return "Medium"
        return "Dense"

    def select_adaptive_k(self, density):
        if density < 10: return 10
        elif density < 30: return 5
        return 2

    def expand_anonymization_region(self, start_node, k):
        region = {start_node}
        queue = [start_node]
        count = self.city.user_at_node[start_node]

        while count < k and queue:
            curr = queue.pop(0)
            for neigh in self.city.neighbors(curr):
                if neigh not in region:
                    region.add(neigh)
                    queue.append(neigh)
                    count += self.city.user_at_node[neigh]
                    if count >= k: break
        return region


# === VERBOSE EXPERIMENT (restored nice output) ===
class DensityAwareAdaptiveKAnonymityExperiment:
    def __init__(self, algorithm, runs=25):
        self.algorithm = algorithm
        self.city = algorithm.city
        self.runs = runs
        self.densities, self.k_values, self.region_sizes = [], [], []

    def run_simulation(self):
        print("\n====== Running Density-Aware Adaptive k-Anonymity Experiment ======\n")
        
        nodes = list(self.city.graph.nodes())
        selected = random.sample(nodes, min(self.runs, len(nodes)))

        for i, target in enumerate(selected, 1):
            density = self.algorithm.compute_local_density(target)
            print(f">>> Density Calculation for Run {i} (Target Node {target})")
            print(f"Users at target node {target}: {self.city.user_at_node[target]}")
            print(f"Neighbors of {target}: {self.city.neighbors(target)}")
            for n in self.city.neighbors(target):
                print(f"  Node {n}: {self.city.user_at_node[n]} users")
            print(f"--> Local Density = {density}")

            k = self.algorithm.select_adaptive_k(density)
            region = self.algorithm.expand_anonymization_region(target, k)

            self.densities.append(density)
            self.k_values.append(k)
            self.region_sizes.append(len(region))

            print(f"Run {i:02d} | Target={target} | Density={density} "
                  f"({self.algorithm.classify_density_level(density)}) | k={k} | Region Size={len(region)}\n")

        print("====== Experiment Complete ======\n")

    def print_summary(self):
        print("=== Experiment Summary ===")
        print(f"avg_density: {mean(self.densities):.2f}")
        print(f"avg_k: {mean(self.k_values):.2f}")
        print(f"avg_region_size: {mean(self.region_sizes):.2f}")
        print(f"max_region_size: {max(self.region_sizes):.2f}")
        print(f"min_region_size: {min(self.region_sizes):.2f}")
