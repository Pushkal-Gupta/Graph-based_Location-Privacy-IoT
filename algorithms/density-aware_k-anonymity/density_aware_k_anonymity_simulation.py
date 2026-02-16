import os
import matplotlib.pyplot as plt

from density_aware_k_anonymity import (
    SmartCityGraph,
    DensityAwareAdaptiveKAnonymityAlgorithm,
    DensityAwareAdaptiveKAnonymityExperiment
)


def main():

    city = SmartCityGraph()

    print("=== USER DISTRIBUTION PER NODE ===")
    for node in sorted(city.user_at_node):
        print(f"Node {node}: {city.user_at_node[node]} users")
    print("=================================\n")

    algo = DensityAwareAdaptiveKAnonymityAlgorithm(city)
    exp = DensityAwareAdaptiveKAnonymityExperiment(algo, runs=25)

    exp.run_simulation()
    exp.print_summary()

    # ========================= FIXED RESULTS PATH =========================
    base_dir = os.path.dirname(os.path.abspath(__file__))

    results_dir = os.path.abspath(
        os.path.join(base_dir, "../../results/density_aware_k_anonymity")
    )

    os.makedirs(results_dir, exist_ok=True)
    # =====================================================================

    # Plot 1
    plt.figure(figsize=(8, 6))
    plt.scatter(exp.densities, exp.k_values, alpha=0.7)
    plt.xlabel("Local Density")
    plt.ylabel("Adaptive k")
    plt.title("Density vs Adaptive k")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(results_dir, "density_vs_k.png"))
    plt.close()

    # Plot 2
    plt.figure(figsize=(8, 6))
    plt.scatter(exp.k_values, exp.region_sizes, alpha=0.7)
    plt.xlabel("Adaptive k")
    plt.ylabel("Region Size")
    plt.title("k vs Region Size")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(results_dir, "k_vs_region_size.png"))
    plt.close()

    # Plot 3
    plt.figure(figsize=(8, 6))
    plt.hist(exp.region_sizes, bins=range(1, max(exp.region_sizes) + 2))
    plt.xlabel("Region Size")
    plt.ylabel("Frequency")
    plt.title("Region Size Distribution")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(results_dir, "region_size_distribution.png"))
    plt.close()


if __name__ == "__main__":
    main()
