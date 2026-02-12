import pickle
import os
import matplotlib.pyplot as plt
from density_aware_k_anonymity import SmartCityGraph, DensityAwareAdaptiveKAnonymityAlgorithm, DensityAwareAdaptiveKAnonymityExperiment

if __name__ == "__main__":
    bounds = (39.4, 41.0, 115.4, 117.5)
    
    city = SmartCityGraph(grid_size=5, user_counts_file='user_counts.pkl', bounds=bounds)
    
    print("\n=== USER DISTRIBUTION PER NODE ===")
    for node in sorted(city.user_at_node):
        print(f"Node {node}: {city.user_at_node[node]} users")
    print("=================================\n")
    
    algo = DensityAwareAdaptiveKAnonymityAlgorithm(city)
    exp = DensityAwareAdaptiveKAnonymityExperiment(algo, runs=25)
    
    exp.run_simulation()
    exp.print_summary()
    
    # ====================== CREATE RESULTS FOLDER ======================
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)   


    # ====================== PLOTS (Saved in results/ folder) ======================
    # Plot 1: Density vs Adaptive k
    plt.figure(figsize=(8, 6))
    plt.scatter(exp.densities, exp.k_values, alpha=0.7, color='blue')
    plt.xlabel("Local Density")
    plt.ylabel("Adaptive k")
    plt.title("Density vs Adaptive k")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(results_dir, "density_vs_k.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 2: k vs Region Size
    plt.figure(figsize=(8, 6))
    plt.scatter(exp.k_values, exp.region_sizes, alpha=0.7, color='green')
    plt.xlabel("Adaptive k")
    plt.ylabel("Region Size (nodes)")
    plt.title("k vs Region Size")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(results_dir, "k_vs_region_size.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 3: Region Size Distribution
    plt.figure(figsize=(8, 6))
    plt.hist(exp.region_sizes, bins=range(1, max(exp.region_sizes)+2), alpha=0.75, color='orange', edgecolor='black')
    plt.xlabel("Region Size")
    plt.ylabel("Frequency")
    plt.title("Distribution of Anonymization Region Sizes")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(results_dir, "region_size_distribution.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # =====================================================================
