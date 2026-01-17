# Graph-based k-Anonymity for Location Privacy in IoT Smart Cities

## Project Overview

This project presents a **graph-based k-anonymity framework** for protecting user location privacy in **IoT-enabled smart cities**.  
The system models an urban environment as a graph and generalizes precise user locations into **connected anonymization regions** that contain at least _k_ users.

The objective is to **balance privacy and utility**, ensuring that location-based smart city services can operate while preventing the disclosure of exact user positions.

---

## System Architecture

### Core Components

#### 1. SmartCityGraph

Models the smart city as a graph:

- Nodes represent intersections or discrete locations
- Edges represent road connectivity
- Users are randomly distributed across nodes
- Each user has a slightly perturbed continuous position

#### 2. KAnonymityPrivacyManager

Implements the graph-based k-anonymity algorithm:

- Starts from the querying user’s node
- Expands a connected subgraph using Breadth-First Search (BFS)
- Stops when the region contains at least _k_ users
- Returns an anonymized location as the **centroid of the region**

#### 3. PrivacyAnalyzer

Evaluates privacy–utility tradeoffs using:

- Location error (Euclidean distance)
- Anonymization region size
- User coverage (successful anonymization rate)

---

## Graph-based k-Anonymity Algorithm

### Algorithm Outline

```text
For each user query:
1. Identify the user's current graph node
2. Initialize a region with this node
3. Perform BFS to expand to neighboring nodes
4. Accumulate users in the region
5. Stop when region contains ≥ k users
6. Compute centroid of region as anonymized location
```

## Key Properties

- Regions are always connected subgraphs
- Spatial realism is preserved through road connectivity
- Privacy increases monotonically with k

---

## Implementation Features

- Graph-based spatial anonymization
- Configurable k-anonymity levels (k = 2, 3, 4, 5, 6)
- Full privacy–utility analysis pipeline
- Visualization of anonymization regions and errors
- Exportable results for reproducibility

---

## Simulation Results

### Performance Metrics

| k-value | Average Location Error | Average Region Size | User Coverage |
| ------- | ---------------------- | ------------------- | ------------- |
| 2       | 0.34 units             | 8.72 sq units       | 100.0%        |
| 3       | 0.58 units             | 16.88 sq units      | 100.0%        |
| 4       | 0.73 units             | 23.08 sq units      | 100.0%        |
| 5       | 0.87 units             | 28.72 sq units      | 100.0%        |
| 6       | 0.96 units             | 34.84 sq units      | 100.0%        |

### Observations

- Increasing k improves privacy but degrades location accuracy
- Location error increases approximately linearly with k
- All users are successfully anonymized for all tested k-values
- Region size grows predictably with privacy requirements

---

## Visualization Outputs

### 1. k-Anonymity Demonstration

Shows original user locations, anonymized centroids, and connected privacy regions.

**Output file:**

```bash
k_anonymity_demo.png
```

### 2. Privacy–Utility Tradeoff Analysis

Four-panel analysis including:

- Location error vs k
- Region size vs k
- User coverage vs k
- Normalized metric comparison

**Output file:**

```bash
privacy_utility_analysis.png
```

---

## Quick Start

### Prerequisites

```bash
pip install networkx numpy matplotlib
```

### Running the Simulation

```bash
python k_anonymity_simulation.py
```

## Generated Files

- k_anonymity_demo.png
- privacy_utility_analysis.png
- simulation_results.json

---

## Technical Details

### Graph Model

- Grid-based city model (8 × 8 intersections)
- Undirected road network
- Random diagonal roads for realism
- Random user placement with spatial noise

### Privacy Computation

- Breadth-First Search region expansion
- Connected subgraph constraint
- Centroid-based spatial generalization

### Evaluation Metrics

- Euclidean distance for location error
- Bounding box area for region size
- Coverage percentage for system effectiveness

---

## Current Limitations

### Computational Cost

- BFS expansion is expensive for large graphs
- Not optimized for real-time, high-density systems

### Utility Degradation

- Location accuracy decreases with higher k
- May affect quality of location-based services

### Graph Dependency

- Sparse areas may struggle to achieve k-anonymity
- Performance depends on city topology

### Static User Model

- Limited support for continuous user mobility
- Temporal correlations not modeled

### Simplistic Region Representation

- Centroid-based anonymization only
- Semantic locations not considered

---

## Future Work

### Algorithmic Extensions

- Adaptive k based on local density
- Differential privacy on graph structures
- Temporal anonymization for trajectories

### System Integration

- Real-time IoT data streams
- Fog and edge computing deployment
- Distributed anonymization

### Advanced Privacy Models

- l-diversity and t-closeness
- Personalized privacy preferences
- Adversarial inference resistance

### Performance Optimization

- Precomputed anonymization regions
- Spatial indexing
- Parallel BFS expansion

---

## Research Contributions

- Practical implementation of graph-based k-anonymity
- End-to-end privacy–utility evaluation framework
- Clear visualization of anonymization behavior
- Modular and extensible research codebase

---

## References and Context

This work builds on concepts from:

- Spatial cloaking
- Graph-based anonymization
- Location privacy in IoT systems
- Privacy–utility tradeoff analysis

It serves as a baseline framework for studying location privacy in smart city environments.

---

**Author**: Pushkal Gupta  
**Context**: IoT Smart Cities Privacy Research  
**Date**: January 2026
