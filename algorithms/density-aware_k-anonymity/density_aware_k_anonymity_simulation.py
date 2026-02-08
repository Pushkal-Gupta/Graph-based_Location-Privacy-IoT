import random

from density_aware_k_anonymity import (
    SmartCityGraph,
    DensityAwareAdaptiveKAnonymityAlgorithm,
    DensityAwareAdaptiveKAnonymityExperiment,
    DensityAwareAdaptiveKAnonymityViz
)

def main():
    smart_city = SmartCityGraph(grid_size=5, num_users=80, seed=42)

    print("\n=== USER DISTRIBUTION PER NODE ===")
    for node, count in smart_city.user_at_node.items():
        print(f"Node {node}: {count} users")
    print("=================================\n")

    algorithm = DensityAwareAdaptiveKAnonymityAlgorithm(smart_city)

    experiment_manager = DensityAwareAdaptiveKAnonymityExperiment(algorithm, runs=25)

    density_data, k_data, size_data = experiment_manager.run_simulation()

    print("=== Experiment Summary ===")
    for key, value in experiment_manager.get_experiment_summary().items():
        print(f"{key}: {value:.2f}")

    DensityAwareAdaptiveKAnonymityViz.plot_density_vs_adaptive_k(density_data, k_data)
    DensityAwareAdaptiveKAnonymityViz.plot_k_vs_region_size(k_data, size_data)

    print("\nSearching for a interesting region to visualize...")
    found_viz = False
    
    for _ in range(100):
        node = random.choice(list(smart_city.graph.nodes()))
        d = algorithm.compute_local_density(node)
        k = algorithm.select_adaptive_k(d)
        region = algorithm.expand_anonymization_region(node, k)

        if 4 <= len(region) <= 15:
            print(f"Visualizing region for node {node} (size={len(region)})")
            DensityAwareAdaptiveKAnonymityViz.visualize_specific_region(
                smart_city, region, node, d, k
            )
            found_viz = True
            break
            
    if not found_viz:
        print("Could not find a specific region size in range [4,15], skipping detail viz.")

if __name__ == "__main__":
    main()
