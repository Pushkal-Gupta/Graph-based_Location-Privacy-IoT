import os
import json
import math
import networkx as nx
import pandas as pd
import random
from collections import defaultdict
from datetime import datetime, timedelta

# ==========================================
# SMART CITY GRAPH (REAL DATASET LOADER)
# ==========================================
class SmartCityGraph:
    def __init__(self, seed=42):
        if seed is not None:
            random.seed(seed)
            
        # Standardized Path Resolution
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.abspath(os.path.join(base_dir, "../../data/processed_data"))
        
        self.nodes_path = os.path.join(self.data_dir, "city_graph_nodes.json")
        self.edges_path = os.path.join(self.data_dir, "city_graph_edges.json")
        self.locations_path = os.path.join(self.data_dir, "device_locations.csv")

        self.graph = nx.Graph()
        self.trajectories = defaultdict(list)
        self.positions = {}

        print(f"Loading data from: {self.data_dir}")
        self._load_nodes()
        self._load_edges()
        self._load_trajectories()

    def _load_nodes(self):
        with open(self.nodes_path, "r") as f:
            nodes = json.load(f)
        for node in nodes:
            nid = int(node["id"])
            self.graph.add_node(nid, x=node["x"], y=node["y"])
            self.positions[nid] = (node["x"], node["y"])

    def _load_edges(self):
        with open(self.edges_path, "r") as f:
            edges = json.load(f)
        for edge in edges:
            self.graph.add_edge(
                int(edge["source"]), 
                int(edge["target"]),
                distance=edge.get("distance", 1.0),
                travel_time=edge.get("travel_time", 1.0)
            )

    def _load_trajectories(self):
        df = pd.read_csv(self.locations_path)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        for _, row in df.iterrows():
            # Store (location_id, timestamp)
            self.trajectories[row["user_id"]].append(
                (int(row["location_id"]), row["timestamp"])
            )
        print(f"Loaded {len(self.trajectories)} user trajectories.")

# ==========================================
# TEMPORAL CLOAKING ALGORITHM
# ==========================================
class TemporalCloakingAlgorithm:
    def __init__(self, city, window_size_minutes=15, k_anonymity=5):
        self.city = city
        self.graph = city.graph
        self.trajectories = city.trajectories
        self.window_size_minutes = window_size_minutes
        self.k_anonymity = k_anonymity

    def compute_centroid(self, node_ids):
        xs = [self.city.positions[n][0] for n in node_ids]
        ys = [self.city.positions[n][1] for n in node_ids]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    def nearest_graph_node(self, x, y):
        best_node = None
        best_dist = float("inf")
        for n, pos in self.city.positions.items():
            d = math.dist((x, y), pos)
            if d < best_dist:
                best_dist = d
                best_node = n
        return best_node

    def execute_logic(self):
        # Flatten all events: (user, loc, time)
        events = []
        for user, traj in self.trajectories.items():
            for loc, ts in traj:
                events.append((user, loc, ts))

        if not events:
            return {}, []

        # Sort by time
        events.sort(key=lambda x: x[2])
        start_time = events[0][2]
        end_time = events[-1][2]
        window_delta = timedelta(minutes=self.window_size_minutes)

        cloaked_output = defaultdict(list)
        flattened_rows = []
        current_start = start_time

        # Process Windows
        while current_start <= end_time:
            current_end = current_start + window_delta
            
            # 1. Identify users in current window
            # Filter events strictly within [current_start, current_end)
            window_events = [e for e in events if current_start <= e[2] < current_end]
            users_in_window = set(e[0] for e in window_events)

            # 2. Expansion logic for k-anonymity
            temp_end = current_end
            
            # Look ahead until k users are found or data ends
            while len(users_in_window) < self.k_anonymity and temp_end <= end_time:
                temp_end += window_delta
                window_events = [e for e in events if current_start <= e[2] < temp_end]
                users_in_window = set(e[0] for e in window_events)
            
            # 3. Anonymize if condition met
            if len(users_in_window) >= self.k_anonymity:
                locs = [e[1] for e in window_events]
                cx, cy = self.compute_centroid(locs)
                generalized_loc = self.nearest_graph_node(cx, cy)
                
                group_size = len(users_in_window)
                interval_str = f"{current_start.isoformat()} | {temp_end.isoformat()}"

                for user in users_in_window:
                    cloaked_output[user].append({
                        "original_events": len([e for e in window_events if e[0] == user]),
                        "generalized_location": generalized_loc,
                        "window_start": current_start,
                        "window_end": temp_end,
                        "group_size": group_size
                    })
                    
                    flattened_rows.append([
                        user, generalized_loc, current_start, temp_end, group_size
                    ])

            # Advance Window
            current_start = max(current_end, temp_end)

        return cloaked_output, flattened_rows

# ==========================================
# EXPERIMENT CLASS (Standardized)
# ==========================================
class TemporalCloakingExperiment:
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.cloaked_data = {}
        self.csv_rows = []
        self.metrics = {}

    def run_simulation(self):
        print(f"====== Running Temporal Cloaking Experiment ======")
        print(f"Config: Window={self.algorithm.window_size_minutes}m, k={self.algorithm.k_anonymity}")
        
        self.cloaked_data, self.csv_rows = self.algorithm.execute_logic()
        
        # Calculate simple metrics for summary
        total_intervals = len(self.csv_rows)
        if total_intervals > 0:
            avg_group_size = sum(r[4] for r in self.csv_rows) / total_intervals
        else:
            avg_group_size = 0
            
        self.metrics = {
            "total_users_processed": len(self.cloaked_data),
            "total_anonymized_intervals": total_intervals,
            "average_group_size": avg_group_size
        }
        
        print("====== Experiment Complete ======\n")

    def print_summary(self):
        print("=== Experiment Summary ===")
        print(f"Total Users: {self.metrics['total_users_processed']}")
        print(f"Total Intervals Generated: {self.metrics['total_anonymized_intervals']}")
        print(f"Average Anonymity Group Size: {self.metrics['average_group_size']:.2f}")