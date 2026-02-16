import networkx as nx
import json
import pandas as pd
import random
import os
import numpy as np
import math
from statistics import mean

# ==========================================
# SMART CITY GRAPH (REAL DATASET LOADER)
# ==========================================
class SmartCityGraph:
    def __init__(self, seed=42):
        if seed is not None:
            random.seed(seed)
        
        # Dynamic path resolution relative to this script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.abspath(os.path.join(base_dir, "../../data/processed_data"))
        
        nodes_path = os.path.join(data_dir, "city_graph_nodes.json")
        edges_path = os.path.join(data_dir, "city_graph_edges.json")
        locations_path = os.path.join(data_dir, "device_locations.csv")

        self.graph = nx.Graph()
        self.positions = {}
        self.active_users = [] # List of (user_id, node_id)
        
        print(f"Loading data from: {data_dir}")
        self._load_nodes(nodes_path)
        self._load_edges(edges_path)
        self._load_user_locations(locations_path)
        
        print(f"Loaded processed dataset -> {len(self.graph.nodes)} nodes, {len(self.active_users)} user records\n")

    def _load_nodes(self, path):
        with open(path, "r") as f:
            nodes = json.load(f)
        
        for node in nodes:
            node_id = int(node["id"])
            self.graph.add_node(node_id)
            # Ensure coordinates are floats
            self.positions[node_id] = (float(node["x"]), float(node["y"]))
            # Add attributes to graph for distance calculations
            self.graph.nodes[node_id]["x"] = float(node["x"])
            self.graph.nodes[node_id]["y"] = float(node["y"])

    def _load_edges(self, path):
        with open(path, "r") as f:
            edges = json.load(f)
            
        for edge in edges:
            source = int(edge["source"])
            target = int(edge["target"])
            self.graph.add_edge(
                source,
                target,
                distance=edge.get("distance", 1.0),
                travel_time=edge.get("travel_time", 1.0)
            )

    def _load_user_locations(self, path):
        # Expects CSV with headers: user_id, location_id, ...
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            u_id = row["user_id"]
            n_id = int(row["location_id"])
            
            # Only add if node exists in graph
            if self.graph.has_node(n_id):
                self.active_users.append((u_id, n_id))

# ==========================================
# GRAPH-CONSTRAINED DP ALGORITHM
# ==========================================
class GraphConstrainedDPAlgorithm:
    def __init__(self, city, sensitivity=1.0):
        self.city = city
        self.sensitivity = sensitivity

    def add_laplace_noise(self, value, epsilon):
        scale = self.sensitivity / epsilon
        return value + np.random.laplace(0, scale)

    def nearest_graph_node(self, x, y):
        best_node = None
        best_dist = float("inf")

        # Optimization: In a real large graph, use a KD-Tree here.
        # For simulation baseline, linear scan is acceptable but slow for huge graphs.
        for n, pos in self.city.positions.items():
            nx_x, nx_y = pos
            d = math.dist((x, y), (nx_x, nx_y))
            if d < best_dist:
                best_dist = d
                best_node = n
        return best_node

    def obfuscate(self, original_node, epsilon):
        # 1. Get original coordinates
        ox, oy = self.city.positions[original_node]

        # 2. Add Laplace Noise
        noisy_x = self.add_laplace_noise(ox, epsilon)
        noisy_y = self.add_laplace_noise(oy, epsilon)

        # 3. Graph Projection
        projected_node = self.nearest_graph_node(noisy_x, noisy_y)
        
        # Calculate intermediate metrics for this single run
        px, py = self.city.positions[projected_node]
        
        metrics = {
            "original_node": original_node,
            "projected_node": projected_node,
            "noisy_x": noisy_x,
            "noisy_y": noisy_y,
            "euclidean_error": math.dist((ox, oy), (px, py)),
            "projection_distance": math.dist((noisy_x, noisy_y), (px, py))
        }
        
        return projected_node, metrics

# ==========================================
# EXPERIMENT CLASS
# ==========================================
class GraphConstrainedDPExperiment:
    def __init__(self, algorithm, epsilon_values, runs_per_epsilon=30):
        self.algorithm = algorithm
        self.city = algorithm.city
        self.epsilon_values = epsilon_values
        self.runs = runs_per_epsilon
        self.results = {} # Store aggregated results
        self.raw_data = [] # Store CSV rows

    def run_simulation(self):
        print("====== Running Graph-Constrained DP Experiment ======\n")
        
        if not self.city.active_users:
            print("ERROR: No active users found in device_locations.csv")
            return

        for epsilon in self.epsilon_values:
            print(f"Processing Epsilon: {epsilon}")
            
            graph_errors = []
            euclidean_errors = []
            projection_dists = []

            # Sample random users if dataset is too large, or iterate all
            # For this baseline, we pick random users for 'runs' times
            selected_samples = random.sample(self.city.active_users, min(self.runs, len(self.city.active_users)))
            
            # If runs > users, we might sample with replacement or just loop runs
            # Strict implementation: Just loop 'runs' times picking random user
            for i in range(self.runs):
                user_id, target_node = random.choice(self.city.active_users)
                
                obf_node, metrics = self.algorithm.obfuscate(target_node, epsilon)
                
                # Compute Graph Distance (Hop Count / Weighted)
                try:
                    g_dist = nx.shortest_path_length(
                        self.city.graph, 
                        source=target_node, 
                        target=obf_node, 
                        weight="distance"
                    )
                except nx.NetworkXNoPath:
                    g_dist = -1 # Disconnected graph handling

                graph_errors.append(g_dist)
                euclidean_errors.append(metrics["euclidean_error"])
                projection_dists.append(metrics["projection_distance"])

                self.raw_data.append([
                    user_id, target_node, obf_node, epsilon, 
                    g_dist, metrics["euclidean_error"], metrics["projection_distance"]
                ])

            self.results[f"epsilon_{epsilon}"] = {
                "mean_graph_error": mean(graph_errors),
                "mean_euclidean_error": mean(euclidean_errors),
                "mean_projection_distance": mean(projection_dists)
            }
            
        print("\n====== Experiment Complete ======\n")

    def print_summary(self):
        print("=== Experiment Summary ===")
        for eps, metrics in self.results.items():
            print(f"[{eps}]")
            print(f"  Avg Graph Error: {metrics['mean_graph_error']:.2f}")
            print(f"  Avg Euclidean Error: {metrics['mean_euclidean_error']:.2f}")