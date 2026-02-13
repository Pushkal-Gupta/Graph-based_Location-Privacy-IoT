#!/usr/bin/env python3
"""
Standard Temporal Cloaking Implementation
(Abul et al. 2008 style – trajectory-centric)

Author: Naga Sai Dattu
Date: February 2026
"""

import os
import json
import math
import csv
from collections import defaultdict
from datetime import datetime, timedelta

import networkx as nx
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================
def get_next_batch_dir(base_dir):
    os.makedirs(base_dir, exist_ok=True)

    existing = [
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("batch")
    ]

    batch_nums = []
    for d in existing:
        try:
            batch_nums.append(int(d.replace("batch", "")))
        except ValueError:
            pass

    next_batch = max(batch_nums) + 1 if batch_nums else 1
    batch_dir = os.path.join(base_dir, f"batch{next_batch}")
    os.makedirs(batch_dir, exist_ok=True)

    return batch_dir

USE_DUMMY_DATA = True

BASE_RESULTS_DIR = "results/temporal_cloaking"
RESULTS_DIR = get_next_batch_dir(BASE_RESULTS_DIR)

WINDOW_SIZE_MINUTES = 15
K_ANONYMITY = 3


# ============================================================
# DATA LOADING
# ============================================================

def load_dummy_graph():
    G = nx.Graph()
    G.add_node("A", x=0, y=0)
    G.add_node("B", x=1, y=0)
    G.add_node("C", x=1, y=1)
    G.add_node("D", x=0, y=1)

    G.add_edge("A", "B", distance=1.0)
    G.add_edge("B", "C", distance=1.0)
    G.add_edge("C", "D", distance=1.0)
    G.add_edge("D", "A", distance=1.0)

    return G


def load_dummy_trajectories():
    base = datetime(2026, 2, 1, 8, 0, 0)

    return {
        1: [("A", base), ("B", base + timedelta(minutes=10)), ("C", base + timedelta(minutes=25))],
        2: [("B", base + timedelta(minutes=5)), ("C", base + timedelta(minutes=20))],
        3: [("A", base + timedelta(minutes=7)), ("D", base + timedelta(minutes=22))]
    }


# ------------------------------------------------------------
# REAL DATA LOADERS (COMMENTED – ENABLE LATER)
# ------------------------------------------------------------

# def load_graph_from_json(path):
#     with open(path) as f:
#         data = json.load(f)
#     G = nx.Graph()
#     for node in data["nodes"]:
#         G.add_node(node["id"], x=node["x"], y=node["y"])
#     for edge in data["edges"]:
#         G.add_edge(edge["source"], edge["target"],
#                    distance=edge["distance"],
#                    travel_time=edge["travel_time"])
#     return G


# def load_trajectories_from_csv(path):
#     import pandas as pd
#     df = pd.read_csv(path)
#     trajectories = defaultdict(list)
#     for _, row in df.iterrows():
#         trajectories[row["user_id"]].append(
#             (row["location_id"], pd.to_datetime(row["timestamp"]))
#         )
#     return trajectories


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def compute_centroid(nodes, graph):
    xs = [graph.nodes[n]["x"] for n in nodes]
    ys = [graph.nodes[n]["y"] for n in nodes]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def nearest_graph_node(x, y, graph):
    best_node = None
    best_dist = float("inf")
    for n, data in graph.nodes(data=True):
        d = math.dist((x, y), (data["x"], data["y"]))
        if d < best_dist:
            best_dist = d
            best_node = n
    return best_node


# ============================================================
# TEMPORAL CLOAKING CORE
# ============================================================

def temporal_cloaking(graph, trajectories):
    events = []

    for user, traj in trajectories.items():
        for loc, ts in traj:
            events.append((user, loc, ts))

    events.sort(key=lambda x: x[2])

    start_time = events[0][2]
    end_time = events[-1][2]
    window_size = timedelta(minutes=WINDOW_SIZE_MINUTES)

    cloaked_output = defaultdict(list)
    flattened_rows = []

    current_start = start_time

    while current_start <= end_time:
        current_end = current_start + window_size
        window_events = [e for e in events if current_start <= e[2] < current_end]

        users_in_window = set(e[0] for e in window_events)

        # Temporal expansion if k not satisfied
        while len(users_in_window) < K_ANONYMITY and current_end <= end_time:
            current_end += window_size
            window_events = [e for e in events if current_start <= e[2] < current_end]
            users_in_window = set(e[0] for e in window_events)

        if len(users_in_window) >= K_ANONYMITY:
            locs = [e[1] for e in window_events]
            cx, cy = compute_centroid(locs, graph)
            generalized_loc = nearest_graph_node(cx, cy, graph)

            for user in users_in_window:
                cloaked_output[user].append({
                    "location": generalized_loc,
                    "time_interval": (current_start.isoformat(), current_end.isoformat()),
                    "group_size": len(users_in_window)
                })

                flattened_rows.append([
                    user,
                    generalized_loc,
                    current_start.isoformat(),
                    current_end.isoformat(),
                    len(users_in_window)
                ])

        current_start = current_end

    return cloaked_output, flattened_rows


# ============================================================
# OUTPUT WRITERS
# ============================================================

def write_results_json(results):
    summary = {
        "total_users": len(results),
        "window_size_minutes": WINDOW_SIZE_MINUTES,
        "k": K_ANONYMITY
    }

    with open(f"{RESULTS_DIR}/temporal_cloaking_results.json", "w") as f:
        json.dump({"per_user": results, "summary": summary}, f, indent=2)


def write_trajectory_csv(rows):
    with open(f"{RESULTS_DIR}/trajectory_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "user_id",
            "generalized_location",
            "window_start",
            "window_end",
            "group_size"
        ])
        writer.writerows(rows)


# ============================================================
# VISUALIZATIONS (MINIMAL BUT CORRECT)
# ============================================================

def plot_trajectory_comparison(graph, trajectories, cloaked):
    plt.figure(figsize=(6, 6))
    pos = {n: (graph.nodes[n]["x"], graph.nodes[n]["y"]) for n in graph.nodes}

    nx.draw(graph, pos, node_color="lightgray", with_labels=True)

    for traj in trajectories.values():
        nx.draw_networkx_nodes(graph, pos, nodelist=[p[0] for p in traj],
                               node_color="blue", alpha=0.4)

    for traj in cloaked.values():
        nx.draw_networkx_nodes(graph, pos,
                               nodelist=[p["location"] for p in traj],
                               node_color="red")

    plt.title("Original (Blue) vs Cloaked (Red)")
    plt.savefig(f"{RESULTS_DIR}/trajectory_comparison.png", dpi=300)
    plt.close()


def plot_dummy_analysis():
    plt.figure()
    plt.plot([10, 20, 30], [0.5, 1.0, 1.8])
    plt.xlabel("Window Size (min)")
    plt.ylabel("Spatial Error")
    plt.savefig(f"{RESULTS_DIR}/temporal_analysis.png", dpi=300)
    plt.close()

    plt.figure()
    plt.plot([10, 20, 30], [0.2, 0.4, 0.7])
    plt.xlabel("Spatial Error")
    plt.ylabel("Privacy Gain")
    plt.savefig(f"{RESULTS_DIR}/privacy_utility_tradeoff.png", dpi=300)
    plt.close()


# ============================================================
# MAIN
# ============================================================

def main():
    if USE_DUMMY_DATA:
        graph = load_dummy_graph()
        trajectories = load_dummy_trajectories()
    else:
        raise NotImplementedError("Enable real data loaders when dataset is ready.")

    cloaked, flattened = temporal_cloaking(graph, trajectories)

    write_results_json(cloaked)
    write_trajectory_csv(flattened)

    plot_trajectory_comparison(graph, trajectories, cloaked)
    plot_dummy_analysis()

    print("Temporal cloaking completed. Results written to results/temporal_cloaking/")


if __name__ == "__main__":
    main()