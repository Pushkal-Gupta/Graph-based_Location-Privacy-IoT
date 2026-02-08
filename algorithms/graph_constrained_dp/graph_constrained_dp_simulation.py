#!/usr/bin/env python3
"""
Graph-Constrained Differential Privacy
(Standard baseline – Laplace DP + graph projection)

Author: Naga Sai Dattu
Date: February 2026
"""

import os
import json
import csv
import math
import random
from statistics import mean

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


# ============================================================
# DETERMINISTIC SEEDING (DUMMY / BASELINE MODE)
# ============================================================

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


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

BASE_RESULTS_DIR = "results/graph_constrained_dp"
RESULTS_DIR = get_next_batch_dir(BASE_RESULTS_DIR)

EPSILON_VALUES = [0.1, 0.5, 1.0, 2.0, 5.0]
RUNS_PER_EPSILON = 30
SENSITIVITY = 1.0


# ============================================================
# DATA LOADING
# ============================================================

def load_dummy_graph():
    G = nx.Graph()
    G.add_node("A", x=0, y=0)
    G.add_node("B", x=1, y=0)
    G.add_node("C", x=1, y=1)
    G.add_node("D", x=0, y=1)

    G.add_edge("A", "B")
    G.add_edge("B", "C")
    G.add_edge("C", "D")
    G.add_edge("D", "A")

    return G


def load_dummy_locations():
    """
    Dummy location records.
    Timestamps are intentionally ignored by this algorithm.
    """
    return [
        (1, "A"),
        (2, "B"),
        (3, "C"),
        (4, "D"),
        (5, "A"),
        (6, "B")
    ]


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


# def load_locations_from_csv(path):
#     import pandas as pd
#     df = pd.read_csv(path)
#     return [(row["user_id"], row["location_id"]) for _, row in df.iterrows()]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def add_laplace_noise(value, epsilon):
    scale = SENSITIVITY / epsilon
    return value + np.random.laplace(0, scale)


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
# GRAPH-CONSTRAINED DP CORE
# ============================================================

def graph_constrained_dp(graph, locations):
    results = {}
    flattened_rows = []

    for epsilon in EPSILON_VALUES:
        graph_errors = []
        euclidean_errors = []
        projection_distances = []

        for _ in range(RUNS_PER_EPSILON):
            user_id, node = random.choice(locations)
            x, y = graph.nodes[node]["x"], graph.nodes[node]["y"]

            noisy_x = add_laplace_noise(x, epsilon)
            noisy_y = add_laplace_noise(y, epsilon)

            obf_node = nearest_graph_node(noisy_x, noisy_y, graph)
            ox, oy = graph.nodes[obf_node]["x"], graph.nodes[obf_node]["y"]

            graph_dist = nx.shortest_path_length(graph, node, obf_node)
            euclid_err = math.dist((x, y), (ox, oy))
            proj_dist = math.dist((noisy_x, noisy_y), (ox, oy))

            graph_errors.append(graph_dist)
            euclidean_errors.append(euclid_err)
            projection_distances.append(proj_dist)

            flattened_rows.append([
                user_id,
                node,
                obf_node,
                epsilon,
                graph_dist,
                euclid_err,
                proj_dist
            ])

        results[f"epsilon_{epsilon}"] = {
            "mean_graph_error": mean(graph_errors),
            "mean_euclidean_error": mean(euclidean_errors),
            "mean_projection_distance": mean(projection_distances)
        }

    return results, flattened_rows


# ============================================================
# OUTPUT WRITERS
# ============================================================

def write_results_json(results):
    output = {
        "metadata": {
            "algorithm": "graph_constrained_differential_privacy",
            "random_seed": RANDOM_SEED,
            "epsilon_values": EPSILON_VALUES,
            "runs_per_epsilon": RUNS_PER_EPSILON,
            "sensitivity": SENSITIVITY,
            "dummy_mode": USE_DUMMY_DATA
        },
        "results": results
    }

    with open(f"{RESULTS_DIR}/simulation_results.json", "w") as f:
        json.dump(output, f, indent=2)


def write_results_csv(rows):
    with open(f"{RESULTS_DIR}/obfuscated_locations.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "user_id",
            "original_node",
            "obfuscated_node",
            "epsilon",
            "graph_distance",
            "euclidean_error",
            "projection_distance"
        ])
        writer.writerows(rows)


# ============================================================
# VISUALIZATIONS
# ============================================================

def plot_privacy_utility(results):
    eps = EPSILON_VALUES
    graph_err = [results[f"epsilon_{e}"]["mean_graph_error"] for e in eps]
    euclid_err = [results[f"epsilon_{e}"]["mean_euclidean_error"] for e in eps]
    proj_err = [results[f"epsilon_{e}"]["mean_projection_distance"] for e in eps]

    plt.figure()
    plt.plot(eps, graph_err, marker="o", label="Graph Distance")
    plt.plot(eps, euclid_err, marker="s", label="Euclidean Error")
    plt.plot(eps, proj_err, marker="^", label="Projection Distance")
    plt.xscale("log")
    plt.xlabel("Privacy Budget (ε)")
    plt.ylabel("Error")
    plt.legend()
    plt.grid(True)

    plt.savefig(f"{RESULTS_DIR}/privacy_utility_analysis.png", dpi=300)
    plt.close()


def plot_graph_constrained_demo(graph):
    fig, axes = plt.subplots(1, len(EPSILON_VALUES), figsize=(18, 4))
    pos = {n: (graph.nodes[n]["x"], graph.nodes[n]["y"]) for n in graph.nodes}

    for ax, epsilon in zip(axes, EPSILON_VALUES):
        user_id, node = load_dummy_locations()[0]
        x, y = graph.nodes[node]["x"], graph.nodes[node]["y"]

        noisy_x = add_laplace_noise(x, epsilon)
        noisy_y = add_laplace_noise(y, epsilon)
        obf_node = nearest_graph_node(noisy_x, noisy_y, graph)
        ox, oy = graph.nodes[obf_node]["x"], graph.nodes[obf_node]["y"]

        nx.draw(graph, pos, ax=ax, node_color="lightgray", with_labels=True)
        ax.scatter([x], [y], color="yellow", s=200, label="Original")
        ax.scatter([noisy_x], [noisy_y], color="orange", marker="x", s=200, label="Noisy")
        ax.scatter([ox], [oy], color="red", s=200, label="Projected")
        ax.plot([noisy_x, ox], [noisy_y, oy], "purple", linestyle="--")

        ax.set_title(f"ε = {epsilon}")
        ax.set_aspect("equal")

    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/graph_constrained_dp_demo.png", dpi=300)
    plt.close()


def plot_single_obfuscation(graph):
    user_id, node = load_dummy_locations()[0]
    epsilon = 1.0

    x, y = graph.nodes[node]["x"], graph.nodes[node]["y"]
    noisy_x = add_laplace_noise(x, epsilon)
    noisy_y = add_laplace_noise(y, epsilon)
    obf_node = nearest_graph_node(noisy_x, noisy_y, graph)
    ox, oy = graph.nodes[obf_node]["x"], graph.nodes[obf_node]["y"]

    pos = {n: (graph.nodes[n]["x"], graph.nodes[n]["y"]) for n in graph.nodes}

    plt.figure(figsize=(6, 6))
    nx.draw(graph, pos, node_color="lightgray", with_labels=True)
    plt.scatter([x], [y], color="yellow", s=300, label="Original")
    plt.scatter([noisy_x], [noisy_y], color="orange", marker="x", s=300, label="Noisy")
    plt.scatter([ox], [oy], color="red", s=300, label="Projected")
    plt.plot([noisy_x, ox], [noisy_y, oy], "purple", linestyle="--")
    plt.legend()
    plt.title("Single Graph-Constrained DP Obfuscation")

    plt.savefig(f"{RESULTS_DIR}/single_obfuscation_visualization.png", dpi=300)
    plt.close()


# ============================================================
# MAIN
# ============================================================

def main():
    if USE_DUMMY_DATA:
        graph = load_dummy_graph()
        locations = load_dummy_locations()
    else:
        raise NotImplementedError("Enable real data loaders when dataset is ready.")

    results, rows = graph_constrained_dp(graph, locations)

    write_results_json(results)
    write_results_csv(rows)

    plot_privacy_utility(results)
    plot_graph_constrained_demo(graph)
    plot_single_obfuscation(graph)

    print("Graph-Constrained DP completed.")
    print(f"Results written to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
