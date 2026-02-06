#!/usr/bin/env python3
"""
Graph-Constrained Differential Privacy for IoT Smart Cities
================================================================================

This implementation demonstrates location privacy using graph-constrained
differential privacy, where noise is added to coordinates but the result
is projected onto valid graph nodes to maintain spatial realism.

Author: Pushkal Gupta
Date: January 2026
"""

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random
import json
import math
import os
from typing import List, Tuple, Dict, Set
from statistics import mean

# ================================================================================
# Smart City Graph
# ================================================================================

class SmartCityGraph:
    """
    Represents a smart city using a 2D grid graph.
    Provides node coordinates for realistic plotting and distance calculations.
    """
    
    def __init__(self, grid_size: int = 5, num_users: int = 30, seed: int = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.grid_size = grid_size
        self.graph = nx.convert_node_labels_to_integers(
            nx.grid_2d_graph(grid_size, grid_size)
        )
        self.num_users = num_users
        
        # Assign 2D coordinates for each node
        self.positions = {
            node: (node % grid_size, node // grid_size) 
            for node in self.graph.nodes()
        }
        
        # Populate users across nodes
        self.user_at_node = {node: 0 for node in self.graph.nodes()}
        self._populate_users()
    
    def _populate_users(self):
        """Randomly distribute users across graph nodes."""
        nodes = list(self.graph.nodes())
        for _ in range(self.num_users):
            n = random.choice(nodes)
            self.user_at_node[n] += 1
    
    def get_node_position(self, node: int) -> Tuple[float, float]:
        """Return the (x, y) coordinates of a node."""
        return self.positions[node]
    
    def find_nearest_node(self, x: float, y: float) -> int:
        """
        Find the nearest graph node to given coordinates.
        This is the key operation for graph-constraint enforcement.
        """
        min_distance = float('inf')
        nearest_node = None
        
        for node, (nx, ny) in self.positions.items():
            distance = math.sqrt((x - nx) ** 2 + (y - ny) ** 2)
            if distance < min_distance:
                min_distance = distance
                nearest_node = node
        
        return nearest_node

# ================================================================================
# Graph-Constrained Differential Privacy Algorithm
# ================================================================================

class GraphConstrainedDifferentialPrivacy:
    """
    Implements graph-constrained differential privacy for location data.
    Combines Laplace mechanism with graph projection to ensure spatial realism.
    """
    
    def __init__(self, city: SmartCityGraph, epsilon_values: List[float] = [0.1, 0.5, 1.0, 2.0, 5.0]):
        """
        Initialize the graph-constrained DP algorithm.
        
        Args:
            city: SmartCityGraph instance
            epsilon_values: List of privacy budget values
        """
        self.city = city
        self.epsilon_values = epsilon_values
        self.sensitivity = 1.0  # L1 sensitivity for coordinate perturbation
    
    # 1. Differential Privacy Noise Addition --------------------------------
    
    def add_laplace_noise(self, value: float, epsilon: float) -> float:
        """Add Laplace noise to a single coordinate value."""
        scale = self.sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        return value + noise
    
    def apply_unconstrained_noise(self, x: float, y: float, epsilon: float) -> Tuple[float, float]:
        """
        Apply standard differential privacy noise to coordinates.
        This is the unconstrained version.
        """
        noisy_x = self.add_laplace_noise(x, epsilon)
        noisy_y = self.add_laplace_noise(y, epsilon)
        return noisy_x, noisy_y
    
    # 2. Graph Constraint Projection ----------------------------------------
    
    def project_to_graph(self, noisy_x: float, noisy_y: float) -> Tuple[int, float, float]:
        """
        Project noisy coordinates onto the nearest valid graph node.
        This enforces the graph constraint.
        
        Returns:
            (nearest_node, constrained_x, constrained_y)
        """
        nearest_node = self.city.find_nearest_node(noisy_x, noisy_y)
        constrained_x, constrained_y = self.city.get_node_position(nearest_node)
        return nearest_node, constrained_x, constrained_y
    
    # 3. Full Graph-Constrained DP Obfuscation ------------------------------
    
    def obfuscate_location(self, node: int, epsilon: float) -> Tuple[int, float, float, float, float]:
        """
        Apply graph-constrained differential privacy to a location.
        
        Args:
            node: Original node ID
            epsilon: Privacy budget
        
        Returns:
            (obfuscated_node, noisy_x, noisy_y, constrained_x, constrained_y)
        """
        # Get original coordinates
        orig_x, orig_y = self.city.get_node_position(node)
        
        # Step 1: Add differential privacy noise
        noisy_x, noisy_y = self.apply_unconstrained_noise(orig_x, orig_y, epsilon)
        
        # Step 2: Project to nearest graph node
        obfuscated_node, constrained_x, constrained_y = self.project_to_graph(noisy_x, noisy_y)
        
        return obfuscated_node, noisy_x, noisy_y, constrained_x, constrained_y
    
    # 4. Utility Metrics -----------------------------------------------------
    
    def calculate_graph_distance(self, node1: int, node2: int) -> int:
        """Calculate shortest path distance between two nodes on the graph."""
        try:
            return nx.shortest_path_length(self.city.graph, node1, node2)
        except nx.NetworkXNoPath:
            return float('inf')
    
    def calculate_euclidean_error(self, orig_node: int, obf_node: int) -> float:
        """Calculate Euclidean distance between original and obfuscated positions."""
        orig_x, orig_y = self.city.get_node_position(orig_node)
        obf_x, obf_y = self.city.get_node_position(obf_node)
        return math.sqrt((orig_x - obf_x) ** 2 + (orig_y - obf_y) ** 2)

# ================================================================================
# Graph-Constrained DP Experiment Manager
# ================================================================================

class GraphConstrainedDPExperiment:
    """
    Runs graph-constrained differential privacy experiments.
    Compares graph-constrained vs unconstrained approaches.
    """
    
    def __init__(self, algorithm: GraphConstrainedDifferentialPrivacy, runs: int = 30):
        self.algorithm = algorithm
        self.city = algorithm.city
        self.runs = runs
        
        # Storage for results
        self.results = {
            "epsilon_values": algorithm.epsilon_values,
            "graph_constrained": {},
            "unconstrained": {},
            "comparison": {}
        }
    
    def run_simulation(self):
        """Execute the full experimental pipeline."""
        print("\n====== Running Graph-Constrained Differential Privacy Experiment ======\n")
        
        for epsilon in self.algorithm.epsilon_values:
            print(f"Testing with ε = {epsilon}")
            
            graph_errors = []
            euclidean_errors = []
            projection_distances = []
            
            for i in range(self.runs):
                # Select a random target node
                target_node = random.choice(list(self.city.graph.nodes()))
                
                # Apply graph-constrained DP
                obf_node, noisy_x, noisy_y, const_x, const_y = \
                    self.algorithm.obfuscate_location(target_node, epsilon)
                
                # Calculate metrics
                graph_dist = self.algorithm.calculate_graph_distance(target_node, obf_node)
                euclidean_err = self.algorithm.calculate_euclidean_error(target_node, obf_node)
                
                # Distance from noisy point to projected point
                projection_dist = math.sqrt((noisy_x - const_x) ** 2 + (noisy_y - const_y) ** 2)
                
                graph_errors.append(graph_dist)
                euclidean_errors.append(euclidean_err)
                projection_distances.append(projection_dist)
            
            # Store aggregated results
            self.results["graph_constrained"][f"epsilon_{epsilon}"] = {
                "mean_graph_error": mean(graph_errors),
                "mean_euclidean_error": mean(euclidean_errors),
                "mean_projection_distance": mean(projection_distances),
                "max_graph_error": max(graph_errors),
                "min_graph_error": min(graph_errors)
            }
            
            print(f"  Mean Graph Distance Error: {mean(graph_errors):.2f} hops")
            print(f"  Mean Euclidean Error: {mean(euclidean_errors):.2f} units")
            print(f"  Mean Projection Distance: {mean(projection_distances):.2f} units\n")
        
        print("====== Experiment Complete ======\n")
        return self.results
    
    def get_experiment_summary(self) -> Dict:
        """Return summary statistics for all epsilon values."""
        summary = {}
        for eps_key, metrics in self.results["graph_constrained"].items():
            summary[eps_key] = {
                "graph_error": metrics["mean_graph_error"],
                "euclidean_error": metrics["mean_euclidean_error"],
                "projection_dist": metrics["mean_projection_distance"]
            }
        return summary

# ================================================================================
# Graph-Constrained DP Visualization
# ================================================================================

class GraphConstrainedDPVisualization:
    """Visualization suite for graph-constrained differential privacy results."""
    
    @staticmethod
    def ensure_results_folder():
        """Create results directory if it doesn't exist."""
        if not os.path.exists("results"):
            os.makedirs("results")
    
    @staticmethod
    def plot_privacy_utility_analysis(results: Dict):
        """
        Create comprehensive privacy-utility analysis plots.
        Shows the tradeoff across different epsilon values.
        """
        GraphConstrainedDPVisualization.ensure_results_folder()
        
        epsilon_values = results["epsilon_values"]
        graph_errors = [
            results["graph_constrained"][f"epsilon_{eps}"]["mean_graph_error"]
            for eps in epsilon_values
        ]
        euclidean_errors = [
            results["graph_constrained"][f"epsilon_{eps}"]["mean_euclidean_error"]
            for eps in epsilon_values
        ]
        projection_dists = [
            results["graph_constrained"][f"epsilon_{eps}"]["mean_projection_distance"]
            for eps in epsilon_values
        ]
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("Graph-Constrained Differential Privacy: Privacy-Utility Analysis", 
                     fontsize=14, fontweight='bold')
        
        # Plot 1: Graph Distance Error vs Epsilon
        axes[0, 0].plot(epsilon_values, graph_errors, marker='o', color='darkblue', linewidth=2)
        axes[0, 0].set_xlabel('Privacy Budget (ε)', fontsize=11)
        axes[0, 0].set_ylabel('Mean Graph Distance (hops)', fontsize=11)
        axes[0, 0].set_title('Graph Distance Error vs ε')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_xscale('log')
        
        # Plot 2: Euclidean Error vs Epsilon
        axes[0, 1].plot(epsilon_values, euclidean_errors, marker='s', color='darkgreen', linewidth=2)
        axes[0, 1].set_xlabel('Privacy Budget (ε)', fontsize=11)
        axes[0, 1].set_ylabel('Mean Euclidean Error (units)', fontsize=11)
        axes[0, 1].set_title('Euclidean Error vs ε')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_xscale('log')
        
        # Plot 3: Projection Distance vs Epsilon
        axes[1, 0].plot(epsilon_values, projection_dists, marker='^', color='darkorange', linewidth=2)
        axes[1, 0].set_xlabel('Privacy Budget (ε)', fontsize=11)
        axes[1, 0].set_ylabel('Mean Projection Distance (units)', fontsize=11)
        axes[1, 0].set_title('Noise Projection Distance vs ε')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_xscale('log')
        
        # Plot 4: Combined comparison
        axes[1, 1].plot(epsilon_values, graph_errors, marker='o', label='Graph Distance', linewidth=2)
        axes[1, 1].plot(epsilon_values, euclidean_errors, marker='s', label='Euclidean Error', linewidth=2)
        axes[1, 1].set_xlabel('Privacy Budget (ε)', fontsize=11)
        axes[1, 1].set_ylabel('Error Magnitude', fontsize=11)
        axes[1, 1].set_title('Combined Error Metrics')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_xscale('log')
        
        plt.tight_layout()
        plt.savefig("results/privacy_utility_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def visualize_obfuscation_demo(
        city: SmartCityGraph,
        algorithm: GraphConstrainedDifferentialPrivacy,
        num_examples: int = 6
    ):
        """
        Demonstrate graph-constrained obfuscation for multiple epsilon values.
        Shows original location, noisy location, and graph-constrained location.
        """
        GraphConstrainedDPVisualization.ensure_results_folder()
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle("Graph-Constrained Differential Privacy: Location Obfuscation Demonstration",
                     fontsize=14, fontweight='bold')
        
        epsilon_samples = algorithm.epsilon_values[:6]
        
        for idx, epsilon in enumerate(epsilon_samples):
            ax = axes[idx // 3, idx % 3]
            
            # Draw the city graph
            pos = city.positions
            nx.draw(city.graph, pos, ax=ax, node_color='lightblue', 
                   node_size=200, with_labels=True, font_size=8)
            
            # Select a target node
            target_node = random.choice(list(city.graph.nodes()))
            orig_x, orig_y = city.get_node_position(target_node)
            
            # Apply obfuscation
            obf_node, noisy_x, noisy_y, const_x, const_y = \
                algorithm.obfuscate_location(target_node, epsilon)
            
            # Highlight original node (yellow)
            nx.draw_networkx_nodes(city.graph, pos, nodelist=[target_node],
                                  node_color='yellow', node_size=300, ax=ax)
            
            # Highlight obfuscated node (red)
            nx.draw_networkx_nodes(city.graph, pos, nodelist=[obf_node],
                                  node_color='red', node_size=300, ax=ax)
            
            # Show noisy point (before projection)
            ax.scatter([noisy_x], [noisy_y], color='orange', s=100, 
                      marker='x', linewidths=3, label='Noisy Point', zorder=5)
            
            # Draw projection line
            ax.plot([noisy_x, const_x], [noisy_y, const_y], 
                   'purple', linestyle='--', linewidth=2, label='Projection', zorder=4)
            
            graph_dist = algorithm.calculate_graph_distance(target_node, obf_node)
            euclidean_err = algorithm.calculate_euclidean_error(target_node, obf_node)
            
            ax.set_title(f"ε = {epsilon}\nGraph Dist: {graph_dist} hops | "
                        f"Euclidean Error: {euclidean_err:.2f}", fontsize=10)
            ax.set_xlim(-0.5, city.grid_size - 0.5)
            ax.set_ylim(-0.5, city.grid_size - 0.5)
            ax.legend(loc='upper right', fontsize=8)
        
        plt.tight_layout()
        plt.savefig("results/graph_constrained_dp_demo.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def visualize_single_obfuscation(
        city: SmartCityGraph,
        target_node: int,
        obf_node: int,
        noisy_x: float,
        noisy_y: float,
        const_x: float,
        const_y: float,
        epsilon: float
    ):
        """Detailed visualization of a single obfuscation operation."""
        GraphConstrainedDPVisualization.ensure_results_folder()
        
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Draw city graph
        pos = city.positions
        nx.draw(city.graph, pos, ax=ax, node_color='lightgray', 
               node_size=300, with_labels=True, font_size=10)
        
        # Highlight original location
        nx.draw_networkx_nodes(city.graph, pos, nodelist=[target_node],
                              node_color='yellow', node_size=500, ax=ax, label='Original')
        
        # Highlight obfuscated location
        nx.draw_networkx_nodes(city.graph, pos, nodelist=[obf_node],
                              node_color='red', node_size=500, ax=ax, label='Obfuscated')
        
        # Show noisy point
        ax.scatter([noisy_x], [noisy_y], color='orange', s=200,
                  marker='X', linewidths=3, label='Noisy Point (DP)', zorder=5)
        
        # Show projection
        ax.plot([noisy_x, const_x], [noisy_y, const_y],
               'purple', linestyle='--', linewidth=3, label='Graph Projection', zorder=4)
        
        ax.set_title(f"Graph-Constrained Differential Privacy Obfuscation\n"
                    f"ε = {epsilon} | Target Node: {target_node} → Obfuscated Node: {obf_node}",
                    fontsize=12, fontweight='bold')
        ax.set_xlim(-0.5, city.grid_size - 0.5)
        ax.set_ylim(-0.5, city.grid_size - 0.5)
        ax.legend(loc='upper right', fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig("results/single_obfuscation_visualization.png", dpi=300, bbox_inches='tight')
        plt.close()

# ================================================================================
# MAIN EXECUTION
# ================================================================================

def main():
    """Main execution pipeline for graph-constrained differential privacy simulation."""
    
    print("\n" + "="*80)
    print("Graph-Constrained Differential Privacy for IoT Smart Cities")
    print("="*80 + "\n")
    
    # 1. Initialize the City and Algorithm
    print("Initializing Smart City Graph...")
    smart_city = SmartCityGraph(grid_size=5, num_users=30, seed=42)
    print(f"  Grid Size: {smart_city.grid_size} × {smart_city.grid_size}")
    print(f"  Total Nodes: {len(smart_city.graph.nodes())}")
    print(f"  Total Users: {smart_city.num_users}\n")
    
    print("Initializing Graph-Constrained DP Algorithm...")
    algorithm = GraphConstrainedDifferentialPrivacy(smart_city)
    print(f"  Privacy Budgets (ε): {algorithm.epsilon_values}\n")
    
    # 2. Run the Experiment
    experiment_manager = GraphConstrainedDPExperiment(algorithm, runs=30)
    results = experiment_manager.run_simulation()
    
    # 3. Print Summary Statistics
    print("=== Experiment Summary ===")
    summary = experiment_manager.get_experiment_summary()
    for eps_key, metrics in summary.items():
        print(f"\n{eps_key}:")
        print(f"  Graph Distance Error: {metrics['graph_error']:.2f} hops")
        print(f"  Euclidean Error: {metrics['euclidean_error']:.2f} units")
        print(f"  Projection Distance: {metrics['projection_dist']:.2f} units")
    
    # 4. Generate Visualizations
    print("\n\nGenerating visualizations...")
    GraphConstrainedDPVisualization.plot_privacy_utility_analysis(results)
    print("  ✓ Privacy-utility analysis saved")
    
    GraphConstrainedDPVisualization.visualize_obfuscation_demo(smart_city, algorithm)
    print("  ✓ Obfuscation demonstration saved")
    
    # 5. Detailed single example
    sample_node = random.choice(list(smart_city.graph.nodes()))
    sample_epsilon = 1.0
    obf_node, noisy_x, noisy_y, const_x, const_y = \
        algorithm.obfuscate_location(sample_node, sample_epsilon)
    
    GraphConstrainedDPVisualization.visualize_single_obfuscation(
        smart_city, sample_node, obf_node, noisy_x, noisy_y, 
        const_x, const_y, sample_epsilon
    )
    print("  ✓ Single obfuscation visualization saved")
    
    # 6. Save results to JSON
    with open("results/simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("  ✓ Results saved to JSON\n")
    
    print("="*80)
    print("Simulation completed successfully!")
    print("Check the 'results/' folder for all outputs.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()