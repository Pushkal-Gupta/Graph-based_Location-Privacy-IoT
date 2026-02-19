import os
import csv
import json
import matplotlib.pyplot as plt
import networkx as nx
from temporal_cloaking import (
    SmartCityGraph,
    TemporalCloakingAlgorithm,
    TemporalCloakingExperiment
)

def get_next_batch_dir(base_results_dir):
    os.makedirs(base_results_dir, exist_ok=True)
    existing = [
        d for d in os.listdir(base_results_dir)
        if os.path.isdir(os.path.join(base_results_dir, d)) and d.startswith("batch")
    ]
    batch_nums = []
    for d in existing:
        try:
            batch_nums.append(int(d.replace("batch", "")))
        except ValueError:
            pass
    next_batch = max(batch_nums) + 1 if batch_nums else 1
    batch_dir = os.path.join(base_results_dir, f"batch{next_batch}")
    os.makedirs(batch_dir, exist_ok=True)
    return batch_dir

def main():
    # 1. Setup Simulation
    try:
        city = SmartCityGraph()
    except Exception as e:
        print(f"Data Load Error: {e}")
        return

    # 2. Run Experiment
    # You can change window_size_minutes and k_anonymity here
    algo = TemporalCloakingAlgorithm(city, window_size_minutes=15, k_anonymity=5)
    exp = TemporalCloakingExperiment(algo)
    
    exp.run_simulation()
    exp.print_summary()

    # 3. Resolve Paths (Strictly ../../results/temporal_cloaking)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    results_root = os.path.abspath(os.path.join(current_file_dir, "../../results/temporal_cloaking"))
    results_dir = get_next_batch_dir(results_root)
    print(f"Saving results to: {results_dir}")

    # 4. Save CSV
    csv_path = os.path.join(results_dir, "temporal_cloaking_log.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "generalized_location_node", "start_time", "end_time", "group_size"])
        for row in exp.csv_rows:
            # Format datetimes for CSV
            clean_row = [row[0], row[1], row[2].isoformat(), row[3].isoformat(), row[4]]
            writer.writerow(clean_row)

    # 5. Save JSON
    json_path = os.path.join(results_dir, "simulation_results.json")
    # Convert datetime objects to strings for JSON serialization
    json_serializable = {
        "metrics": exp.metrics,
        "config": {"window": algo.window_size_minutes, "k": algo.k_anonymity}
    }
    with open(json_path, "w") as f:
        json.dump(json_serializable, f, indent=2)

    # 6. Generate Visualization (Comparison Plot)
    print("Generating visualization...")
    plt.figure(figsize=(10, 8))
    
    # Draw basic graph structure
    pos = city.positions
    nx.draw_networkx_edges(city.graph, pos, alpha=0.1, edge_color="gray")
    nx.draw_networkx_nodes(city.graph, pos, node_size=10, node_color="lightgray", alpha=0.5)

    # Plot a few original user trajectories (Blue) - limit to 5 users for clarity
    sample_users = list(exp.cloaked_data.keys())[:5]
    for user in sample_users:
        traj = city.trajectories[user]
        locs = [t[0] for t in traj if t[0] in pos]
        if locs:
            nx.draw_networkx_nodes(city.graph, pos, nodelist=locs, node_size=15, node_color="blue", alpha=0.3)

    # Plot generalized locations (Red)
    generalized_nodes = set()
    for row in exp.csv_rows:
        if row[0] in sample_users: # Only show for sampled users
            generalized_nodes.add(row[1])
    
    if generalized_nodes:
        nx.draw_networkx_nodes(city.graph, pos, nodelist=list(generalized_nodes), node_size=50, node_color="red", alpha=0.8, label="Cloaked Node")

    plt.title(f"Temporal Cloaking: W={algo.window_size_minutes}m, k={algo.k_anonymity}")
    plt.legend(["Original Path (Sample)", "Cloaked Locations"])
    plt.axis('off')
    
    plt.savefig(os.path.join(results_dir, "trajectory_comparison.png"), dpi=300)
    plt.close()
    
    print("Graphs generated successfully.")

if __name__ == "__main__":
    main()