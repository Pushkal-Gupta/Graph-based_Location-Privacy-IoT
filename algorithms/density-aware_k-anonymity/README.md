# Density-Aware Adaptive k-Anonymity for Location Privacy in IoT Smart Cities

## Project Overview

This project implements **Density-Aware Adaptive k-Anonymity** for ensuring user location privacy in **IoT-enabled smart cities**.  
Unlike traditional graph-based k-anonymity, which uses a fixed k, Density-Aware Adaptive k-Anonymity dynamically adjusts the anonymity parameter based on local user density, providing an optimized **privacy–utility tradeoff**.

The system models an urban environment as a grid-based graph and generalizes user locations into **connected anonymization regions** that contain at least *k* users, where k is chosen adaptively based on the local spatial context.

---

## System Architecture

### Core Components

#### 1. SmartCityGraph
Models the smart city as a 2D grid graph:
- Nodes represent intersections; edges represent road connectivity
- Randomly distributes a configurable number of users across nodes
- Maintains spatial coordinates for realistic visualization and distance metrics

#### 2. Density-Aware Adaptive k-Anonymity Algorithm
The core logic engine for density-aware privacy:
- **Density Computation:** Uses BFS (depth=1) to count users in a node's immediate neighborhood
- **Adaptive k Selector:** Maps neighborhood density to privacy levels (k=10 for sparse, k=5 for medium, k=2 for dense)
- **Region Expansion:** Grows a connected subgraph until the required *k* users are reached

#### 3. Density-Aware Adaptive k-Anonymity Experiment
An experiment management layer that:
- Orchestrates multiple simulation runs (default: 20 runs)
- Collects statistical data on densities, k-values, and resulting region sizes
- Provides summary metrics including average region size and min/max bounds

#### 4. Density-Aware Adaptive k-Anonymity Visualization
A dedicated visualization suite that:
- Generates scatter plots for privacy–utility analysis
- Produces spatial graph plots highlighting the target user and the anonymized region
- Automatically exports results to a structured `results/` directory

---

## Density-Aware Adaptive k-Anonymity Algorithm

### Algorithm Outline

```text
For each user query:
1. Identify the user's target node in the SmartCityGraph
2. Compute local user density using a 1-hop BFS search
3. Select k value adaptively:
   - Density < 4  -> k = 10 (High Privacy)
   - Density < 10 -> k = 5  (Balanced)
   - Else         -> k = 2  (High Utility)
4. Perform BFS region expansion starting from the target node
5. Accumulate users until the selected k-threshold is met
6. Return the resulting connected subgraph as the privacy region

```

## Key Properties

* Context-aware anonymity levels based on real-time user distribution
* Guaranteed connectivity of anonymization regions via graph-based BFS
* Higher service precision in dense urban areas; higher privacy in sparse regions
* Modular, object-oriented design for research extensibility

---

## Implementation Features

* Object-oriented architecture (City, Algorithm, Experiment, and Visualization classes)
* Automated result export to local `results/` folder
* Configurable simulation parameters (grid size, user count, random seed)
* Multi-run statistical analysis pipeline for Density-Aware Adaptive k-Anonymity
* High-fidelity visualization of spatial anonymization regions

---

## Density-Aware Adaptive k-Anonymity Experiment Results

### Performance Metrics (Example Output)

| Run ID | Target Node | Density Class | Selected k | Region Size |
| --- | --- | --- | --- | --- |
| Run 01 | 12 | Sparse | 10 | 14 |
| Run 05 | 04 | Medium | 5 | 6 |
| Run 18 | 22 | Dense | 2 | 1 |

### Observations

* **Adaptive Efficiency:** The system successfully lowers k in dense areas to preserve location utility.
* **Privacy Assurance:** In sparse areas, the region size expands significantly to ensure k-anonymity.
* **Connectivity:** All generated regions maintain road-network connectivity, preserving spatial realism.

---

## Visualization Outputs

### 1. Density vs. Selected k

A scatter plot demonstrating the inverse relationship between local density and the required anonymity level.

**Output file:** `results/density_vs_k.png`

### 2. Selected k vs. Region Size

Visualizes how the physical area of the privacy region scales with the chosen k-value in the Density-Aware Adaptive k-Anonymity framework.

**Output file:** `results/k_vs_region_size.png`

### 3. Region Visualization

A spatial graph highlighting:

* **Yellow Node:** The actual user location (Target)
* **Red Nodes:** The connected anonymization region
* **Blue Nodes:** The rest of the smart city grid

**Output file:** `results/region_visualization.png`

---

## Quick Start

### Prerequisites

```bash
pip install networkx matplotlib

```

### Running the Simulation

```bash
python density_aware_adaptive_k_anonymity.py

```

## Generated Files

* results/density_vs_k.png
* results/k_vs_region_size.png
* results/region_visualization.png

---

## Technical Details

### Graph Model

* 5 × 5 Grid-based city model (configurable)
* Integer-labeled nodes with (x, y) mapping
* Random user distribution with seed support for reproducibility

### Privacy Computation

* BFS-based density estimation (depth = 1)
* BFS-based region expansion (connected subgraph constraint)
* Threshold-based adaptive k selection

### Metrics Collected

* Neighborhood user density
* Region size (node count)
* Summary statistics (Average k, Avg/Min/Max region size)

---

## Current Limitations

### Topological Complexity

* Grid-based model is a simplification of real-world irregular road networks
* BFS density is limited to a fixed 1-hop depth

### Dynamic Constraints

* Model currently assumes static users (no mobility/trajectory support)
* Temporal privacy correlations are not modeled

---

## Future Work

### Algorithmic Extensions

* Implementation of l-diversity and t-closeness on top of Density-Aware Adaptive k-Anonymity
* Adaptive BFS depth for density estimation
* Differential privacy integration for edge weights

### System Integration

* Support for real-world OpenStreetMap (OSM) graph data
* Integration with fog/edge computing nodes for distributed anonymization
* Trajectory anonymization for moving IoT devices

---

## Research Contributions

* Modular OOP framework for Density-Aware Adaptive k-Anonymity research
* Empirical validation of density-aware privacy selection
* Automated visualization and data collection pipeline
* Extensible baseline for IoT location privacy in smart cities

---

## References and Context

This work builds on concepts from:

* Spatial cloaking and graph-based anonymization
* Location privacy in IoT smart city architectures
* Density-aware privacy-utility optimization

---

**Author**: Praagya Garg

**Context**: IoT Smart Cities Privacy Research

**Date**: January 2026

```

Would you like me to help you adjust the `classify_density` or `select_k` thresholds in your code to see how it impacts the "Average Region Size" in the experiment results?

```
