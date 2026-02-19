import os
import csv
import json
import matplotlib.pyplot as plt
from graph_constrained_dp import (
    SmartCityGraph,
    GraphConstrainedDPAlgorithm,
    GraphConstrainedDPExperiment
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
    city = SmartCityGraph()
    algo = GraphConstrainedDPAlgorithm(city, sensitivity=1.0)
    
    epsilons = [0.1, 0.5, 1.0, 2.0, 5.0]
    exp = GraphConstrainedDPExperiment(algo, epsilon_values=epsilons, runs_per_epsilon=30)
    
    # 2. Run Experiment
    exp.run_simulation()
    exp.print_summary()

    # 3. Resolve Paths (Strictly ../../results/graph_constrained_dp)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up from algorithms/graph_constrained_dp -> algorithms -> root -> results
    results_root = os.path.abspath(os.path.join(current_file_dir, "../../results/graph_constrained_dp"))
    results_dir = get_next_batch_dir(results_root)
    
    print(f"Saving results to: {results_dir}")

    # 4. Save CSV
    csv_path = os.path.join(results_dir, "obfuscated_locations.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "user_id", "original_node", "obfuscated_node", 
            "epsilon", "graph_distance", "euclidean_error", "projection_distance"
        ])
        writer.writerows(exp.raw_data)

    # 5. Save JSON
    json_path = os.path.join(results_dir, "simulation_results.json")
    with open(json_path, "w") as f:
        json.dump(exp.results, f, indent=2)

    # 6. Generate Plots
    # Extract data for plotting
    eps_vals = sorted(epsilons)
    graph_err = [exp.results[f"epsilon_{e}"]["mean_graph_error"] for e in eps_vals]
    euclid_err = [exp.results[f"epsilon_{e}"]["mean_euclidean_error"] for e in eps_vals]
    proj_err = [exp.results[f"epsilon_{e}"]["mean_projection_distance"] for e in eps_vals]

    # Plot 1: Privacy vs Utility
    plt.figure(figsize=(10, 6))
    plt.plot(eps_vals, graph_err, marker="o", label="Graph Distance (Hops/m)")
    plt.plot(eps_vals, euclid_err, marker="s", label="Euclidean Error (m)")
    plt.plot(eps_vals, proj_err, marker="^", label="Projection Distance (m)")
    plt.xscale("log")
    plt.xlabel("Privacy Budget (epsilon)")
    plt.ylabel("Error Metrics")
    plt.title("Privacy-Utility Tradeoff")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(results_dir, "privacy_utility_analysis.png"))
    plt.close()

    print("Graphs generated successfully.")

if __name__ == "__main__":
    main()