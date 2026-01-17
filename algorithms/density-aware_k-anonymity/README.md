```markdown
# Adaptive Density-Aware k-Anonymity (ADKA) for Location Privacy in IoT Smart Cities

## Project Overview

This project implements **Adaptive Density-Aware k-Anonymity (ADKA)** for ensuring user location privacy in **IoT-enabled smart cities**.  
Unlike traditional graph-based k-anonymity, which uses a fixed k, ADKA dynamically adjusts the anonymity parameter based on local user density, providing an improved **privacy–utility tradeoff**.

The objective is to generalize user locations into **connected anonymization regions** that contain at least *k* users, where k is chosen adaptively based on the local environment.

---

## System Architecture

### Core Components

#### 1. Smart-City Graph Model
Models the smart city as a graph:
- Nodes represent intersections or discrete locations
- Edges represent road connectivity
- Users are randomly distributed across nodes
- Provides a simplified urban layout for evaluating privacy mechanisms

#### 2. ADKA Density Module
Computes local neighborhood density using BFS (depth = 1):
- Counts users at the target node and its 1-hop neighbors
- Determines if the region is sparse, medium, or dense
- Serves as the basis for adaptive privacy selection

#### 3. Adaptive k Selector
Chooses the anonymity level *k* based on density thresholds:
- If density < 4: **k = 10**
- Elif density < 10: **k = 5**
- Else: **k = 2**
- Provides **context-aware privacy adaptation**

#### 4. Region Expansion Module
Implements the graph-based growth logic:
- Starts from the target user's node
- Expands a connected subgraph using Breadth-First Search (BFS)
- Stops when the region contains at least *k* users
- Returns the final connected anonymization region

---

## ADKA Algorithm

### Algorithm Outline

```text
For each target user query:
1. Compute local density using BFS (depth = 1)
2. Select adaptive k value based on density thresholds
3. Initialize an anonymization region with the target node
4. Perform BFS to expand to neighboring nodes
5. Accumulate users in the growing region
6. Stop when region contains ≥ k users
7. Return the connected subgraph as the anonymized location

```

## Key Properties

* Privacy levels adapt automatically based on local density
* Regions are always guaranteed to be connected subgraphs
* Ensures stronger privacy in sparse areas and higher accuracy in dense areas
* Lightweight and efficient for IoT-scale graph processing

---

## Implementation Features

* Density-aware adaptive k-selection logic
* BFS-based anonymization region expansion
* 20-run experimental evaluation pipeline
* Automated visualization of density, k-values, and regions
* Modular and extensible Python codebase

---

## ADKA Experiment Results

### Performance Metrics (Sample Output)

| Run ID | Target Node | Local Density | Selected k | Region Size (Nodes) |
| --- | --- | --- | --- | --- |
| Run 1 | 7 | 3 (Low) | 10 | 11 |
| Run 2 | 22 | 6 (Med) | 5 | 2 |
| Run 3 | 16 | 10 (High) | 2 | 1 |

### Observations

* **Inverse Correlation:** As local density increases, the required k-value decreases
* **Privacy Scaling:** Low density leads to k = 10 and larger anonymization regions
* **Utility Preservation:** High density allows for k = 2 and minimal region sizes
* **Consistency:** Scatter plots confirm correct adaptive behavior across runs

---

## Visualization Outputs

### 1. Density vs. Selected k

Shows how the anonymity requirement decreases as local user density increases.

### 2. Selected k vs. Region Size

Illustrates how the physical region size grows to accommodate larger privacy requirements.

### 3. Anonymized Region Visualization

Displays the graph connectivity with specific highlighting:

* **Blue Nodes:** General city grid
* **Red Nodes:** Anonymized privacy region

---

## Quick Start

### Prerequisites

```bash
pip install networkx matplotlib

```

### Running the Simulation

```bash
python adka.py

```

## Generated Visual Outputs

Running the algorithm will display three figures:

* density_vs_k_plot
* k_vs_region_size_plot
* graph_region_visualization

---

## Technical Details

### Graph Model

* 5 × 5 Grid-based city model
* Undirected road connectivity
* Random user placement across nodes

### Privacy Computation

* Dynamic k-selection thresholds
* Breadth-First Search region expansion
* Connected region topological guarantee

### Metrics Collected

* Local neighborhood density (1-hop)
* Adaptive k-value distribution
* Resulting region node count

---

## Current Limitations

### Scale and Complexity

* Small grid size (5x5) limits complex topology testing
* BFS density estimation limited to 1-hop depth

### Modeling Constraints

* Static user model (no mobility or temporal correlations)
* Absence of coordinate-level Euclidean error metrics

---

## Future Work

### Algorithmic Extensions

* Multi-hop density estimation for smoother adaptation
* Integration with Differential Privacy frameworks
* Mobility-aware anonymization for continuous trajectories

### System Integration

* Real-world IoT deployment models
* Hybrid models combining fixed-k and adaptive-k approaches
* Performance optimization for large-scale city graphs

---

## Research Contributions

* Practical implementation of the ADKA framework for IoT smart cities
* Empirical demonstration of density-based privacy–utility optimization
* Integrated visualization suite for privacy behavior analysis
* Reusable foundation for future adaptive privacy research

---

## References and Context

This work builds on concepts from:

* Graph-based anonymization
* Spatial cloaking
* IoT location privacy
* Privacy–utility tradeoff analysis

---

**Author**: Praagya Garg

**Context**: IoT Smart Cities Privacy Research

**Date**: January 2026

