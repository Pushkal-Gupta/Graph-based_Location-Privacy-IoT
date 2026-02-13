#!/usr/bin/env python3
"""
Graph-based k-Anonymity Simulation Runner
========================================

Uses the core module to:
- Run experiments
- Compute statistics
- Plot privacy–utility tradeoffs
"""

import json
import numpy as np
import matplotlib.pyplot as plt

from k_anonymity import (
    SmartCityGraph,
    KAnonymityPrivacyManager,
    PrivacyAnalyzer
)

def run_simulation(grid_size, num_users, k_values):
    city = SmartCityGraph(grid_size)
    city.add_users(num_users)

    results = {
        "k": [],
        "avg_location_error": [],
        "avg_region_size": [],
        "user_coverage": []
    }

    for k in k_values:
        manager = KAnonymityPrivacyManager(city, k)
        errors, regions = [], []
        covered = 0

        for uid in range(num_users):
            true_pos = city.user_positions[uid]
            ax, ay, region, users = manager.anonymized_location(uid)

            if len(users) >= k:
                covered += 1
                errors.append(
                    PrivacyAnalyzer.location_error(
                        true_pos, (ax, ay)
                    )
                )
                regions.append(
                    PrivacyAnalyzer.region_size(region, city)
                )

        results["k"].append(k)
        results["avg_location_error"].append(np.mean(errors))
        results["avg_region_size"].append(np.mean(regions))
        results["user_coverage"].append(covered / num_users * 100)

    return results


def plot_results(results):
    k = results["k"]

    plt.figure(figsize=(14, 4))

    plt.subplot(1, 3, 1)
    plt.plot(k, results["avg_location_error"], marker="o")
    plt.title("Average Location Error")
    plt.xlabel("k")
    plt.ylabel("Error")

    plt.subplot(1, 3, 2)
    plt.plot(k, results["avg_region_size"], marker="o")
    plt.title("Average Region Size")
    plt.xlabel("k")
    plt.ylabel("Area")

    plt.subplot(1, 3, 3)
    plt.plot(k, results["user_coverage"], marker="o")
    plt.title("User Coverage (%)")
    plt.xlabel("k")
    plt.ylabel("Coverage")

    plt.tight_layout()
    plt.show()


def main():
    results = run_simulation(
        grid_size=8,
        num_users=25,
        k_values=[2, 3, 4, 5, 6]
    )

    with open("simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    plot_results(results)
    print("Simulation completed successfully.")


if __name__ == "__main__":
    main()