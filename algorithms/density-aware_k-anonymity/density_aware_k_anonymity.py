import networkx as nx
import json
import pandas as pd
import random
import os
import numpy as np
from statistics import mean


# =========================================================
# SMART CITY GRAPH (REAL DATASET LOADER)
# =========================================================

class SmartCityGraph:
    def __init__(self, seed=42):
        if seed is not None:
            random.seed(seed)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.abspath(
            os.path.join(base_dir, "../../data/processed_data")
        )

        nodes_path = os.path.join(data_dir, "city_graph_nodes.json")
        edges_path = os.path.join(data_dir, "city_graph_edges.json")
        locations_path = os.path.join(data_dir, "device_locations.csv")

        self.graph = nx.Graph()
        self.positions = {}
        self.user_at_node = {}

        self._load_nodes(nodes_path)
        self._load_edges(edges_path)
        self._load_user_distribution(locations_path)

        total_records = sum(self.user_at_node.values())
        print(f"Loaded processed dataset → {total_records} trajectory records\n")

    def _load_nodes(self, path):
        with open(path, "r") as f:
            nodes = json.load(f)

        for node in nodes:
            node_id = int(node["id"])
            self.graph.add_node(node_id)
            self.positions[node_id] = (node["x"], node["y"])
            self.user_at_node[node_id] = 0

    def _load_edges(self, path):
        with open(path, "r") as f:
            edges = json.load(f)

        for edge in edges:
            source = int(edge["source"])
            target = int(edge["target"])
            self.graph.add_edge(
                source,
                target,
                distance=edge["distance"],
                travel_time=edge["travel_time"]
            )

    def _load_user_distribution(self, path):
        df = pd.read_csv(path)

        for _, row in df.iterrows():
            node_id = int(row["location_id"])
            if node_id in self.user_at_node:
                self.user_at_node[node_id] += 1

    def neighbors(self, node):
        return list(self.graph.neighbors(node))


# =========================================================
# DENSITY-AWARE ADAPTIVE k-ANONYMITY
# =========================================================

class DensityAwareAdaptiveKAnonymityAlgorithm:
    def __init__(self, city):
        self.city = city

        densities = list(city.user_at_node.values())
        self.p33 = np.percentile(densities, 33)
        self.p66 = np.percentile(densities, 66)

        print("Adaptive Density Thresholds:")
        print(f"P33: {self.p33:.2f}")
        print(f"P66: {self.p66:.2f}\n")

    def compute_local_density(self, node, verbose=False):
        total = self.city.user_at_node[node]
        neighbors = self.city.neighbors(node)

        if verbose:
            print(f">>> Density Calculation (Target Node {node})")
            print(f"Users at target node {node}: {self.city.user_at_node[node]}")
            print(f"Neighbors of {node}: {neighbors}")

        for neigh in neighbors:
            total += self.city.user_at_node[neigh]
            if verbose:
                print(f"  Node {neigh}: {self.city.user_at_node[neigh]} users")

        if verbose:
            print(f"--> Local Density = {total}\n")

        return total

    def classify_density_level(self, density):
        if density < self.p33:
            return "Sparse"
        elif density < self.p66:
            return "Medium"
        return "Dense"

    def select_adaptive_k(self, density):
        if density < self.p33:
            return 10
        elif density < self.p66:
            return 5
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
                    if count >= k:
                        break
        return region


# =========================================================
# EXPERIMENT CLASS
# =========================================================

class DensityAwareAdaptiveKAnonymityExperiment:
    def __init__(self, algorithm, runs=25):
        self.algorithm = algorithm
        self.city = algorithm.city
        self.runs = runs
        self.densities = []
        self.k_values = []
        self.region_sizes = []

    def run_simulation(self):
        print("====== Running Density-Aware Adaptive k-Anonymity Experiment ======\n")

        nodes = list(self.city.graph.nodes())
        selected = random.sample(nodes, min(self.runs, len(nodes)))

        for i, target in enumerate(selected, 1):
            density = self.algorithm.compute_local_density(
                target,
                verbose=True
            )

            k = self.algorithm.select_adaptive_k(density)
            region = self.algorithm.expand_anonymization_region(target, k)

            self.densities.append(density)
            self.k_values.append(k)
            self.region_sizes.append(len(region))

            print(
                f"Run {i:02d} | Target={target} | "
                f"Density={density} "
                f"({self.algorithm.classify_density_level(density)}) | "
                f"k={k} | Region Size={len(region)}\n"
            )

        print("====== Experiment Complete ======\n")

    def print_summary(self):
        print("=== Experiment Summary ===")
        print(f"avg_density: {mean(self.densities):.2f}")
        print(f"avg_k: {mean(self.k_values):.2f}")
        print(f"avg_region_size: {mean(self.region_sizes):.2f}")
        print(f"max_region_size: {max(self.region_sizes):.2f}")
        print(f"min_region_size: {min(self.region_sizes):.2f}")
