#!/usr/bin/env python3
"""
Differential Privacy Location Obfuscation for IoT Smart Cities
===============================================================
This implementation demonstrates location privacy using differential privacy
with Laplace noise addition to coordinate-based location data.

Author: Pushkal Gupta
Date: January 2026
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import random
import json
import math
from typing import List, Tuple, Dict


# ---------------------------------------------------------------------
# Differential Privacy Obfuscator
# ---------------------------------------------------------------------

class DifferentialPrivacyLocationObfuscator:
    """Implements differential privacy for location data using Laplace mechanism."""

    def __init__(self, epsilon_values: List[float] = [0.1, 0.5, 1.0, 2.0, 5.0]):
        """
        Initialize the differential privacy obfuscator.

        Args:
            epsilon_values: List of privacy budget values (smaller = more private)
        """
        self.epsilon_values = epsilon_values
        self.sensitivity = 1.0  # L1 sensitivity for location coordinates

    def add_laplace_noise(self, value: float, epsilon: float) -> float:
        """
        Add Laplace noise to a single coordinate value.
        """
        scale = self.sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        return value + noise

    def obfuscate_location(
        self, x: float, y: float, epsilon: float
    ) -> Tuple[float, float]:
        """
        Add differential privacy noise to location coordinates.
        """
        noisy_x = self.add_laplace_noise(x, epsilon)
        noisy_y = self.add_laplace_noise(y, epsilon)
        return noisy_x, noisy_y

    def batch_obfuscate(
        self, locations: List[Tuple[float, float]], epsilon: float
    ) -> List[Tuple[float, float]]:
        """
        Obfuscate multiple locations with the same privacy parameter.
        """
        return [
            self.obfuscate_location(x, y, epsilon)
            for x, y in locations
        ]


# ---------------------------------------------------------------------
# Smart City Simulator
# ---------------------------------------------------------------------

class IoTSmartCitySimulator:
    """Simulates IoT devices in a smart city for location privacy testing."""

    def __init__(self, city_size: float = 10.0, num_devices: int = 50):
        self.city_size = city_size
        self.num_devices = num_devices
        self.device_locations = self._generate_device_locations()
        self.device_types = self._assign_device_types()

    def _generate_device_locations(self) -> List[Tuple[float, float]]:
        locations = []

        poi_centers = [
            (2.0, 2.0),
            (8.0, 3.0),
            (5.0, 7.0),
            (3.0, 8.0),
            (7.0, 8.0),
        ]

        clustered_devices = int(0.7 * self.num_devices)
        random_devices = self.num_devices - clustered_devices

        for _ in range(clustered_devices):
            center = random.choice(poi_centers)
            x = np.random.normal(center[0], 0.8)
            y = np.random.normal(center[1], 0.8)
            x = max(0, min(self.city_size, x))
            y = max(0, min(self.city_size, y))
            locations.append((x, y))

        for _ in range(random_devices):
            x = random.uniform(0, self.city_size)
            y = random.uniform(0, self.city_size)
            locations.append((x, y))

        return locations

    def _assign_device_types(self) -> List[str]:
        device_types = [
            "smartphone",
            "vehicle_gps",
            "smart_camera",
            "sensor_node",
            "wearable",
        ]
        weights = [0.4, 0.2, 0.15, 0.15, 0.1]
        return np.random.choice(
            device_types, size=self.num_devices, p=weights
        ).tolist()


# ---------------------------------------------------------------------
# Privacy–Utility Analyzer
# ---------------------------------------------------------------------

class PrivacyUtilityAnalyzer:
    """Analyzes privacy-utility tradeoffs."""

    @staticmethod
    def calculate_location_error(
        original: Tuple[float, float],
        obfuscated: Tuple[float, float],
    ) -> float:
        return math.dist(original, obfuscated)

    @staticmethod
    def calculate_privacy_level(epsilon: float) -> str:
        if epsilon >= 5.0:
            return "Low Privacy"
        elif epsilon >= 2.0:
            return "Medium Privacy"
        elif epsilon >= 1.0:
            return "High Privacy"
        elif epsilon >= 0.5:
            return "Very High Privacy"
        else:
            return "Maximum Privacy"

    @staticmethod
    def calculate_utility_loss(errors: List[float]) -> Dict[str, float]:
        return {
            "mean_error": np.mean(errors),
            "median_error": np.median(errors),
            "std_error": np.std(errors),
            "max_error": np.max(errors),
            "min_error": np.min(errors),
        }


# ---------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------

def run_differential_privacy_simulation():
    print("Differential Privacy Location Obfuscation for IoT Smart Cities")
    print("=" * 70)

    city_sim = IoTSmartCitySimulator(city_size=10.0, num_devices=50)
    dp_obfuscator = DifferentialPrivacyLocationObfuscator()
    analyzer = PrivacyUtilityAnalyzer()

    print("Smart City Simulation Setup:")
    print(f" City Size: {city_sim.city_size} x {city_sim.city_size} units")
    print(f" IoT Devices: {city_sim.num_devices}")
    print(f" Device Types: {set(city_sim.device_types)}")
    print(f" Privacy Levels (ε): {dp_obfuscator.epsilon_values}")
    print("-" * 70)

    results = {
        "epsilon_values": dp_obfuscator.epsilon_values,
        "privacy_levels": [],
        "mean_errors": [],
        "median_errors": [],
        "std_errors": [],
        "utility_metrics": {},
    }

    for epsilon in dp_obfuscator.epsilon_values:
        print(f"\nTesting Differential Privacy with ε = {epsilon}")

        obfuscated_locations = dp_obfuscator.batch_obfuscate(
            city_sim.device_locations, epsilon
        )

        errors = [
            analyzer.calculate_location_error(orig, obf)
            for orig, obf in zip(
                city_sim.device_locations, obfuscated_locations
            )
        ]

        utility_metrics = analyzer.calculate_utility_loss(errors)
        privacy_level = analyzer.calculate_privacy_level(epsilon)

        results["privacy_levels"].append(privacy_level)
        results["mean_errors"].append(utility_metrics["mean_error"])
        results["median_errors"].append(utility_metrics["median_error"])
        results["std_errors"].append(utility_metrics["std_error"])
        results[f"epsilon_{epsilon}"] = utility_metrics

        print(f" Privacy Level: {privacy_level}")
        print(f" Mean Location Error: {utility_metrics['mean_error']:.3f}")
        print(f" Median Error: {utility_metrics['median_error']:.3f}")
        print(f" Std Deviation: {utility_metrics['std_error']:.3f}")
        print(f" Max Error: {utility_metrics['max_error']:.3f}")

    return city_sim, dp_obfuscator, results


# ---------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------

def create_privacy_visualizations(
    city_sim: IoTSmartCitySimulator,
    dp_obfuscator: DifferentialPrivacyLocationObfuscator,
    results: Dict,
):
    fig1, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig1.suptitle("Differential Privacy Location Obfuscation Comparison")

    vis_epsilons = dp_obfuscator.epsilon_values

    for idx, epsilon in enumerate(vis_epsilons):
        ax = axes[idx // 3, idx % 3]

        obfuscated_locs = dp_obfuscator.batch_obfuscate(
            city_sim.device_locations, epsilon
        )

        orig_x, orig_y = zip(*city_sim.device_locations)
        obf_x, obf_y = zip(*obfuscated_locs)

        ax.scatter(orig_x, orig_y, c="blue", alpha=0.7, label="Original")
        ax.scatter(obf_x, obf_y, c="red", alpha=0.7, label="Obfuscated")

        for i in range(min(10, len(orig_x))):
            ax.plot(
                [orig_x[i], obf_x[i]],
                [orig_y[i], obf_y[i]],
                color="gray",
                alpha=0.5,
            )

        privacy_level = PrivacyUtilityAnalyzer.calculate_privacy_level(epsilon)
        mean_error = results["mean_errors"][idx]

        ax.set_title(
            f"ε = {epsilon} ({privacy_level})\nMean Error: {mean_error:.2f}"
        )
        ax.set_xlim(-1, city_sim.city_size + 1)
        ax.set_ylim(-1, city_sim.city_size + 1)
        ax.grid(True)
        ax.legend()

    plt.tight_layout()
    plt.savefig("dp_location_obfuscation_demo.png", dpi=300)

    return fig1


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    city_sim, dp_obfuscator, results = run_differential_privacy_simulation()

    create_privacy_visualizations(city_sim, dp_obfuscator, results)

    with open("dp_simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nSimulation completed successfully.")
    plt.show()


if __name__ == "__main__":
    main()
