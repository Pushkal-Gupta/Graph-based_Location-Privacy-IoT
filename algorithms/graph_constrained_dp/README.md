# Graph-Constrained Differential Privacy for Location Privacy in IoT Smart Cities

## Project Overview

This project implements **Graph-Constrained Differential Privacy** for ensuring user location privacy in **IoT-enabled smart cities**.

Unlike standard differential privacy, which adds noise to coordinates without spatial awareness, Graph-Constrained Differential Privacy projects obfuscated locations onto valid graph nodes, ensuring that anonymized positions correspond to **real intersections or road locations** within the urban topology.

The system models an urban environment as a grid-based graph and applies the **Laplace mechanism** for differential privacy, followed by a **graph projection step** that maps noisy coordinates to the nearest valid node, preserving both **formal privacy guarantees** and **spatial realism**.

---

## System Architecture

### Core Components

#### 1. SmartCityGraph

Models the smart city as a 2D grid graph:

- Nodes represent intersections; edges represent road connectivity
- Randomly distributes a configurable number of users across nodes
- Maintains spatial coordinates for realistic visualization and distance metrics
- Provides efficient nearest-node lookup for graph projection

#### 2. Graph-Constrained Differential Privacy Algorithm

The core logic engine for graph-aware privacy:

- **Laplace Noise Addition:** Applies standard differential privacy noise to (x, y) coordinates
- **Graph Projection:** Maps noisy coordinates to the nearest valid graph node
- **Constraint Enforcement:** Ensures all obfuscated locations lie on actual road network nodes
- **Utility Metrics:** Computes graph distance and Euclidean error for privacy-utility analysis

#### 3. Graph-Constrained DP Experiment

An experiment management layer that:

- Orchestrates multiple simulation runs (default: 30 runs)
- Collects statistical data on graph distance errors, Euclidean errors, and projection distances
- Provides summary metrics including mean/min/max error bounds across different privacy levels

#### 4. Graph-Constrained DP Visualization

A dedicated visualization suite that:

- Generates privacy-utility tradeoff curves for multiple epsilon values
- Produces spatial graph plots highlighting original, noisy, and graph-constrained locations
- Automatically exports results to a structured `results/` directory

---

## Graph-Constrained Differential Privacy Algorithm

### Algorithm Outline

```text
For each user location query:
1. Identify the user's original node in the SmartCityGraph
2. Extract (x, y) coordinates of the original node
3. Add Laplace noise to coordinates:
   - noise_scale = sensitivity / ε
   - x' = x + Laplace(0, noise_scale)
   - y' = y + Laplace(0, noise_scale)
4. Project noisy coordinates to the graph:
   - Find nearest graph node to (x', y')
   - Return the coordinates of this node as the obfuscated location
5. Result is both differentially private AND spatially realistic
```

## Key Properties

- Formal ε-differential privacy guarantee inherited from Laplace mechanism
- Ensures obfuscated locations correspond to real intersections/roads
- Prevents physically impossible locations (e.g., in buildings, water bodies, empty space)
- Better utility than unconstrained DP for location-based services requiring valid addresses
- Maintains connectivity constraints of the urban graph structure
- Modular, object-oriented design for research extensibility

---

## Implementation Features

- Object-oriented architecture (City, Algorithm, Experiment, and Visualization classes)
- Automated result export to local `results/` folder
- Configurable simulation parameters (grid size, user count, random seed, epsilon values)
- Multi-run statistical analysis pipeline for robust evaluation
- High-fidelity visualization of spatial anonymization with projection steps
- Graph distance and Euclidean error metrics for comprehensive analysis

---

## Graph-Constrained DP Experiment Results

### Performance Metrics (Example Output)

| ε (epsilon) | Privacy Level     | Mean Graph Error (hops) | Mean Euclidean Error | Mean Projection Distance |
| ----------- | ----------------- | ----------------------- | -------------------- | ------------------------ |
| 0.1         | Maximum Privacy   | 3.45                    | 2.87                 | 1.23                     |
| 0.5         | Very High Privacy | 2.10                    | 1.65                 | 0.78                     |
| 1.0         | High Privacy      | 1.40                    | 1.12                 | 0.52                     |
| 2.0         | Medium Privacy    | 0.95                    | 0.73                 | 0.31                     |
| 5.0         | Low Privacy       | 0.50                    | 0.38                 | 0.15                     |

### Observations

- **Graph Constraint Benefit:** All obfuscated locations lie on valid graph nodes, ensuring spatial realism.
- **Privacy-Utility Tradeoff:** Lower ε provides stronger privacy but increases location error.
- **Projection Effect:** The projection step reduces extreme noise outliers by snapping to the nearest node.
- **Connectivity Preservation:** Obfuscated locations maintain the topological structure of the urban network.

---

## Visualization Outputs

### 1. Privacy-Utility Analysis

A comprehensive four-panel analysis showing:

- Graph distance error vs epsilon
- Euclidean error vs epsilon
- Noise projection distance vs epsilon
- Combined error metric comparison

**Output file:** `results/privacy_utility_analysis.png`

### 2. Location Obfuscation Demonstration

Shows original locations (yellow), noisy points (orange X), and graph-constrained locations (red) for multiple epsilon values, with projection lines illustrating the constraint enforcement.

**Output file:** `results/graph_constrained_dp_demo.png`

### 3. Single Obfuscation Visualization

A detailed spatial graph highlighting:

- **Yellow Node:** The actual user location (Original)
- **Orange X:** The noisy point after DP noise addition
- **Purple Dashed Line:** The projection from noisy point to nearest node
- **Red Node:** The final graph-constrained obfuscated location
- **Gray Nodes:** The rest of the smart city grid

**Output file:** `results/single_obfuscation_visualization.png`

---

## Quick Start

### Prerequisites

```bash
pip install networkx matplotlib numpy
```

### Running the Simulation

```bash
python graph_constrained_dp_simulation.py
```

## Generated Files

- `results/privacy_utility_analysis.png`
- `results/graph_constrained_dp_demo.png`
- `results/single_obfuscation_visualization.png`
- `results/simulation_results.json`

---

## Technical Details

### Differential Privacy Mechanism

- **Privacy Model:** ε-differential privacy
- **Sensitivity:** L1 sensitivity = 1.0 (for coordinate perturbation)
- **Noise Distribution:** Laplace(0, scale) where scale = sensitivity / ε
- **Noise Application:** Independent noise added to x and y coordinates

### Graph Projection

- **Method:** Nearest node search using Euclidean distance
- **Complexity:** O(n) for n nodes (can be optimized with spatial indexing)
- **Constraint:** Output location must be a valid graph node

### City Simulation

- **City Model:** 5 × 5 grid graph (configurable)
- **Total Nodes:** 25 intersections
- **User Distribution:** Random placement across nodes
- **Coordinate System:** Integer-labeled nodes with (x, y) mapping

### Metrics Collected

- Graph distance error (shortest path length on graph)
- Euclidean distance error (straight-line distance in coordinate space)
- Projection distance (distance from noisy point to constrained point)
- Summary statistics (mean, min, max) for each metric

---

## Current Limitations

### Simplified Graph Topology

- Grid-based model is a simplification of real-world irregular road networks
- Does not account for one-way streets, bridges, or complex intersections

### Projection Overhead

- Nearest-node search adds computational overhead compared to pure coordinate DP
- May become expensive for very large graphs without spatial indexing

### Uniform Privacy Budget

- Same epsilon applied to all users regardless of context
- Does not adapt to local density or sensitivity requirements

### Static User Model

- Model currently assumes static users (no mobility/trajectory support)
- Does not handle temporal correlations in location data

---

## Future Work

### Algorithmic Extensions

- Implementation of adaptive epsilon selection based on local graph density
- Integration of l-diversity and t-closeness on top of graph-constrained DP
- Hybrid approaches combining k-anonymity with graph-constrained differential privacy

### Graph Optimization

- Spatial indexing (k-d trees, R-trees) for efficient nearest-node queries
- Support for weighted graphs with travel time or distance metrics
- Handling of disconnected graph components

### Real-World Integration

- Support for real-world OpenStreetMap (OSM) graph data
- Road network preprocessing and simplification techniques
- Integration with fog/edge computing nodes for distributed anonymization

### Trajectory Privacy

- Extension to trajectory obfuscation for moving IoT devices
- Temporal graph-constrained DP with sequential composition
- Path-based privacy metrics for mobile users

---

## Research Contributions

- Modular OOP framework for graph-constrained differential privacy research
- Empirical validation of graph constraint benefits for location privacy
- Automated visualization and data collection pipeline for privacy-utility analysis
- Extensible baseline for comparing graph-aware vs unconstrained DP mechanisms
- Clear demonstration of spatial realism preservation in privacy-preserving systems

---

## References and Context

This work builds on concepts from:

- Differential privacy and the Laplace mechanism
- Graph-based spatial modeling in smart cities
- Location privacy in IoT architectures
- Privacy-utility tradeoff optimization in location-based services

This framework serves as a **research-oriented and extensible foundation** for studying graph-constrained privacy mechanisms in smart city environments.

---

**Author:** Naga Sai Dattu
**Context:** IoT Smart Cities Privacy Research  
**Date:** February 2026
