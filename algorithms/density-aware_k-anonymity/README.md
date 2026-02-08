# Density-Aware k-Anonymity for Location Privacy in IoT Smart Cities

## Project Overview

This project implements **Density-Aware k-Anonymity** for ensuring user location privacy in **IoT-enabled smart cities**. The system models an urban environment as a grid-based graph and generalizes user locations into **connected anonymization regions**.

Unlike traditional graph-based k-anonymity which uses a fixed global parameter , this project implements a **Density-Aware Adaptive Algorithm**. It dynamically adjusts the anonymity requirement based on local user density. This approach provides an optimized **privacy–utility tradeoff**: enforcing stricter privacy (higher ) in sparse areas to prevent outlier identification, while allowing higher utility (lower , smaller regions) in dense areas where users are naturally hidden by the crowd.

---

## System Architecture

### Core Components

#### 1. SmartCityGraph

Models the urban environment and population distribution:

* **Topology:** Represents the city as a 5x5 Grid Graph (2D Lattice).
* **Population:** Manages a distribution of 80 users across 25 nodes.
* **Coordinates:** Maps graph nodes to (x, y) coordinates for realistic spatial visualization.
* **State Management:** Tracks real-time user counts per node.

#### 2. DensityAwareAdaptiveKAnonymityAlgorithm

Implements the core logic for context-aware privacy:

* **Local Density Computation:** Uses Breadth-First Search (BFS) to calculate user density within a 1-hop neighborhood.
* **Adaptive k-Selection:** Classifies nodes into density levels (Sparse, Medium, Dense) to determine the required .
* **Region Expansion:** Grows a connected subgraph starting from the target node until the cumulative user count meets .

#### 3. DensityAwareAdaptiveKAnonymityExperiment

Manages the simulation lifecycle:

* **Sampling:** Selects unique target nodes for experimental runs to avoid repetition.
* **Data Collection:** Aggregates metrics for density, selected , and resulting region sizes.
* **Statistical Summary:** Computes average and extreme values for performance analysis.

#### 4. DensityAwareAdaptiveKAnonymityViz

Handles data visualization and reporting:

* **Scatter Plots:** Correlates density with , and  with region size.
* **Spatial Visualization:** Renders the specific anonymization region, distinguishing between the target user, peers, and the rest of the city.

---

## Algorithm Logic

### Core Workflow

For a given target user at node N, the system executes the following process:

```text
1. Density Estimation:
   - Perform BFS (Depth=1) from N.
   - Sum users at N and all immediate neighbors.
   - Result = Local Density (d).

2. Adaptive k-Selection:
   - IF d < 6  (Sparse) -> Set k = 10 (High Privacy required)
   - IF d < 12 (Medium) -> Set k = 5  (Balanced)
   - IF d >= 12 (Dense) -> Set k = 2  (High Utility allowed)

3. Region Expansion (Anonymization):
   - Initialize Region R = {N}.
   - Initialize Queue Q = [N].
   - While sum(users in R) < k:
     a. Dequeue current node C.
     b. Add unvisited neighbors of C to R and Q.
     c. Update cumulative user count.

4. Output:
   - Return Region R (A connected subgraph of the city).

```

---

## Key Properties

* **Context-Awareness:** Privacy requirements are not static; they react to the surrounding environment.
* **Connectivity Guarantee:** The anonymization region is always a connected subgraph, ensuring the reported region is physically traversable.
* **Guaranteed k-Anonymity:** The algorithm strictly ensures that the number of users within the generated region is  the adaptive .
* **Outlier Protection:** Sparse areas automatically trigger higher  values to protect isolated users.

---

## Simulation Parameters

| Parameter | Value | Description |
| --- | --- | --- |
| **Grid Size** | 5 x 5 | Total 25 Nodes (Smart City regions) |
| **Population** | 80 Users | Randomly distributed across the grid |
| **Simulation Runs** | 25 | Iterations (capped at node count for uniqueness) |
| **Density Depth** | 1 Hop | Radius for checking local density |
| **Expansion Logic** | BFS | Breadth-First Search for region growth |
| **Seed** | 42 | Fixed seed for reproducibility |

---

## Performance Metrics

### Privacy Metrics

| Metric | Description | Strategy |
| --- | --- | --- |
| **Adaptive** | The required anonymity set size | 10 (Sparse), 5 (Medium), 2 (Dense) |
| **Local Density** | Users in immediate vicinity | Used to determine the "risk" level of the location |

### Utility Metrics

| Metric | Description | Interpretation |
| --- | --- | --- |
| **Region Size** | Number of nodes in the cloaked area | **Smaller is better.** Indicates higher precision location data. |
| **Expansion Overhead** | Nodes added beyond the neighborhood | Difference between Region Size and 1-hop neighborhood. |

---

## Visualization Outputs

### 1. Correlation Analysis

Analyze the relationship between environmental factors and algorithm decisions.

* **Density vs. Adaptive k:** Visualizes the inverse relationship (High Density  Low ).
* **k vs. Region Size:** Shows the cost of privacy (Higher   Larger physical regions).

**Output files:** `results/density_vs_k.png`, `results/k_vs_region_size.png`

### 2. Spatial Visualization

A detailed topological view of a specific anonymization instance.

* **Yellow Star:** Target User (The subject of the query).
* **Orange Nodes:** Anonymization Region (Peers forming the k-set).
* **Grey Nodes:** Rest of the city.

**Output file:** `results/region_visualization.png`

---

## Quick Start

### Prerequisites

```bash
pip install networkx matplotlib

```

### Running the Simulation

The project includes a dedicated simulation runner.

```bash
python3 density_aware_k_anonymity_simulation.py

```

### Console Output Example

```text
=== USER DISTRIBUTION PER NODE ===
Node 0: 4 users
Node 1: 3 users
Node 2: 6 users
Node 3: 6 users
Node 4: 2 users
Node 5: 1 users
Node 6: 4 users
Node 7: 6 users
Node 8: 5 users
Node 9: 2 users
Node 10: 2 users
Node 11: 3 users
Node 12: 3 users
Node 13: 3 users
Node 14: 2 users
Node 15: 0 users
Node 16: 1 users
Node 17: 5 users
Node 18: 3 users
Node 19: 3 users
Node 20: 3 users
Node 21: 2 users
Node 22: 4 users
Node 23: 4 users
Node 24: 3 users
=================================


====== Running Density-Aware Adaptive k-Anonymity Experiment ======


>>> Density Calculation for Run 1 (Target Node 14)
Users at target node 14: 2
Neighbors of 14: [9, 13, 19]
  Node 9: 2 users
  Node 13: 3 users
  Node 19: 3 users
--> Local Density = 10
Run 01 | Target=14 | Density=10 (Medium) | k=5 | Region Size=3

>>> Density Calculation for Run 2 (Target Node 20)
Users at target node 20: 3
Neighbors of 20: [15, 21]
  Node 15: 0 users
  Node 21: 2 users
--> Local Density = 5
Run 02 | Target=20 | Density=5 (Sparse) | k=10 | Region Size=6

>>> Density Calculation for Run 3 (Target Node 11)
Users at target node 11: 3
Neighbors of 11: [6, 10, 16, 12]
  Node 6: 4 users
  Node 10: 2 users
  Node 16: 1 users
  Node 12: 3 users
--> Local Density = 13
Run 03 | Target=11 | Density=13 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 4 (Target Node 5)
Users at target node 5: 1
Neighbors of 5: [0, 10, 6]
  Node 0: 4 users
  Node 10: 2 users
  Node 6: 4 users
--> Local Density = 11
Run 04 | Target=5 | Density=11 (Medium) | k=5 | Region Size=2

>>> Density Calculation for Run 5 (Target Node 22)
Users at target node 22: 4
Neighbors of 22: [17, 21, 23]
  Node 17: 5 users
  Node 21: 2 users
  Node 23: 4 users
--> Local Density = 15
Run 05 | Target=22 | Density=15 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 6 (Target Node 23)
Users at target node 23: 4
Neighbors of 23: [18, 22, 24]
  Node 18: 3 users
  Node 22: 4 users
  Node 24: 3 users
--> Local Density = 14
Run 06 | Target=23 | Density=14 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 7 (Target Node 6)
Users at target node 6: 4
Neighbors of 6: [1, 5, 11, 7]
  Node 1: 3 users
  Node 5: 1 users
  Node 11: 3 users
  Node 7: 6 users
--> Local Density = 17
Run 07 | Target=6 | Density=17 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 8 (Target Node 8)
Users at target node 8: 5
Neighbors of 8: [3, 7, 13, 9]
  Node 3: 6 users
  Node 7: 6 users
  Node 13: 3 users
  Node 9: 2 users
--> Local Density = 22
Run 08 | Target=8 | Density=22 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 9 (Target Node 2)
Users at target node 2: 6
Neighbors of 2: [1, 7, 3]
  Node 1: 3 users
  Node 7: 6 users
  Node 3: 6 users
--> Local Density = 21
Run 09 | Target=2 | Density=21 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 10 (Target Node 21)
Users at target node 21: 2
Neighbors of 21: [16, 20, 22]
  Node 16: 1 users
  Node 20: 3 users
  Node 22: 4 users
--> Local Density = 10
Run 10 | Target=21 | Density=10 (Medium) | k=5 | Region Size=3

>>> Density Calculation for Run 11 (Target Node 17)
Users at target node 17: 5
Neighbors of 17: [12, 16, 22, 18]
  Node 12: 3 users
  Node 16: 1 users
  Node 22: 4 users
  Node 18: 3 users
--> Local Density = 16
Run 11 | Target=17 | Density=16 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 12 (Target Node 19)
Users at target node 19: 3
Neighbors of 19: [14, 18, 24]
  Node 14: 2 users
  Node 18: 3 users
  Node 24: 3 users
--> Local Density = 11
Run 12 | Target=19 | Density=11 (Medium) | k=5 | Region Size=2

>>> Density Calculation for Run 13 (Target Node 3)
Users at target node 3: 6
Neighbors of 3: [2, 8, 4]
  Node 2: 6 users
  Node 8: 5 users
  Node 4: 2 users
--> Local Density = 19
Run 13 | Target=3 | Density=19 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 14 (Target Node 16)
Users at target node 16: 1
Neighbors of 16: [11, 15, 21, 17]
  Node 11: 3 users
  Node 15: 0 users
  Node 21: 2 users
  Node 17: 5 users
--> Local Density = 11
Run 14 | Target=16 | Density=11 (Medium) | k=5 | Region Size=4

>>> Density Calculation for Run 15 (Target Node 7)
Users at target node 7: 6
Neighbors of 7: [2, 6, 12, 8]
  Node 2: 6 users
  Node 6: 4 users
  Node 12: 3 users
  Node 8: 5 users
--> Local Density = 24
Run 15 | Target=7 | Density=24 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 16 (Target Node 18)
Users at target node 18: 3
Neighbors of 18: [13, 17, 23, 19]
  Node 13: 3 users
  Node 17: 5 users
  Node 23: 4 users
  Node 19: 3 users
--> Local Density = 18
Run 16 | Target=18 | Density=18 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 17 (Target Node 4)
Users at target node 4: 2
Neighbors of 4: [3, 9]
  Node 3: 6 users
  Node 9: 2 users
--> Local Density = 10
Run 17 | Target=4 | Density=10 (Medium) | k=5 | Region Size=2

>>> Density Calculation for Run 18 (Target Node 12)
Users at target node 12: 3
Neighbors of 12: [7, 11, 17, 13]
  Node 7: 6 users
  Node 11: 3 users
  Node 17: 5 users
  Node 13: 3 users
--> Local Density = 20
Run 18 | Target=12 | Density=20 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 19 (Target Node 15)
Users at target node 15: 0
Neighbors of 15: [10, 20, 16]
  Node 10: 2 users
  Node 20: 3 users
  Node 16: 1 users
--> Local Density = 6
Run 19 | Target=15 | Density=6 (Medium) | k=5 | Region Size=3

>>> Density Calculation for Run 20 (Target Node 13)
Users at target node 13: 3
Neighbors of 13: [8, 12, 18, 14]
  Node 8: 5 users
  Node 12: 3 users
  Node 18: 3 users
  Node 14: 2 users
--> Local Density = 16
Run 20 | Target=13 | Density=16 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 21 (Target Node 0)
Users at target node 0: 4
Neighbors of 0: [5, 1]
  Node 5: 1 users
  Node 1: 3 users
--> Local Density = 8
Run 21 | Target=0 | Density=8 (Medium) | k=5 | Region Size=2

>>> Density Calculation for Run 22 (Target Node 1)
Users at target node 1: 3
Neighbors of 1: [0, 6, 2]
  Node 0: 4 users
  Node 6: 4 users
  Node 2: 6 users
--> Local Density = 17
Run 22 | Target=1 | Density=17 (Dense) | k=2 | Region Size=1

>>> Density Calculation for Run 23 (Target Node 24)
Users at target node 24: 3
Neighbors of 24: [19, 23]
  Node 19: 3 users
  Node 23: 4 users
--> Local Density = 10
Run 23 | Target=24 | Density=10 (Medium) | k=5 | Region Size=2

>>> Density Calculation for Run 24 (Target Node 10)
Users at target node 10: 2
Neighbors of 10: [5, 15, 11]
  Node 5: 1 users
  Node 15: 0 users
  Node 11: 3 users
--> Local Density = 6
Run 24 | Target=10 | Density=6 (Medium) | k=5 | Region Size=4

>>> Density Calculation for Run 25 (Target Node 9)
Users at target node 9: 2
Neighbors of 9: [4, 8, 14]
  Node 4: 2 users
  Node 8: 5 users
  Node 14: 2 users
--> Local Density = 11
Run 25 | Target=9 | Density=11 (Medium) | k=5 | Region Size=3
--> Local Density = 11
Run 25 | Target=9 | Density=11 (Medium) | k=5 | Region Size=3

====== Experiment Complete ======

=== Experiment Summary ===
avg_density: 13.64
avg_k: 3.64
avg_region_size: 1.96
max_region_size: 6.00
min_region_size: 1.00

Searching for a interesting region to visualize...
Visualizing region for node 10 (size=4)

```

---

## Technical Details

### Classification Strategy

The system uses a tiered approach to classify density logic:

| Density Level | User Count Threshold | Selected  | Rationale |
| --- | --- | --- | --- |
| **Sparse** |  $< 6$ users | $10$ | High risk of re-identification; requires aggressive aggregation. |
| **Medium** |  $6 - 11$ users | $5$ | Standard urban density; balanced privacy settings. |
| **Dense** |  $\ge 12$ users | $2$ | Crowd provides natural cover; precise location utility is prioritized. |

### Expansion Strategy

| Method | Used? | Pros | Cons |
| --- | --- | --- | --- |
| **BFS Expansion** | **Yes** | Creates compact, circular regions. | May include irrelevant nodes if density is very low. |
| **DFS Expansion** | No | Can follow road networks (snake-like). | Creates elongated regions that are harder to interpret. |

---

## Current Limitations

### Topological Constraints

| Limitation | Impact | Future Mitigation |
| --- | --- | --- |
| **Grid Topology** | Abstract representation of distance | Integration with OSM (OpenStreetMap) data |
| **Static Users** | Snapshot-based privacy only | Implementation of trajectory/temporal cloaking |
| **Uniform Weight** | All nodes have equal importance | Weighted edges for travel time/distance |

### Scalability

| Issue | Description |
| --- | --- |
| **O(N) Complexity** | Region expansion may traverse the whole graph in worst-case sparse scenarios. |
| **Boundary Effects** | Nodes at the grid edge have fewer neighbors, artificially lowering density scores. |

---

## Future Work

### Algorithmic Improvements

| Improvement | Benefit | Priority |
| --- | --- | --- |
| **Granular Density** | Use continuous functions for  instead of discrete tiers | High |
| **Semantic Constraints** | Avoid expanding regions across physical barriers (e.g., rivers) | Medium |
| **Personalized Privacy** | Allow users to set their own base sensitivity levels | High |

### System Integration

| Integration | Use Case |
| --- | --- |
| **Real-time Data** | Handle streaming location updates from moving users |
| **Voronoi Partitioning** | Alternative to grid-based spatial division |

---

## Methodological Attribution

### Foundational Model

This implementation is grounded in the concept of **Spatial Cloaking** and **k-Anonymity**, originally proposed by Gruteser and Grunwald (2003) and Sweeney (2002). It specifically addresses the "uniform k" problem by adopting a density-aware approach, conceptually aligned with **Adaptive Geo-Indistinguishability** and **Context-Aware Location Privacy**.

### Design Choices

* **Graph-Based Model:** We utilize `NetworkX` to enforce topological connectivity, preventing the generation of "island" regions that are physically impossible in real road networks.
* **Local Density:** Density is defined strictly by the 1-hop neighborhood to ensure local processing speed suitable for edge computing.

---

## References

1. **Sweeney, L. (2002).** k-anonymity: A model for protecting privacy. *International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems*.
2. **Gruteser, M., & Grunwald, D. (2003).** Anonymous usage of location-based services through spatial and temporal cloaking. *MobiSys*.
3. **Gedik, B., & Liu, L. (2005).** Location privacy in mobile systems: A personalized anonymization model. *ICDCS*.

---

**Author:** Praagya Garg  
**Context:** IoT Smart Cities Privacy Research  
**Date:** January 2026

