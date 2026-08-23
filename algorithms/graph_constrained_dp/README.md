# Graph-Constrained Differential Privacy for Location Privacy in IoT Smart Cities

## Project Overview

This project implements **Graph-Constrained Differential Privacy** for protecting user location privacy in **IoT-enabled smart cities**. The system perturbs user locations using a formal differential privacy mechanism and then constrains the perturbed outputs to valid locations on a city graph, ensuring spatial realism while preserving privacy guarantees.

Unlike unconstrained coordinate-based differential privacy, graph-constrained differential privacy ensures that anonymized locations always correspond to real intersections or road nodes, preventing physically impossible outputs while maintaining formal ε-differential privacy through post-processing immunity.

---

## System Architecture

### Core Components

#### 1. LocationSimulator

Models static user location observations in smart cities:

- Represents user locations as nodes in a city graph
- Supports deterministic dummy distributions for reproducible experiments
- Loads real user location datasets from CSV when enabled
- Maintains spatial coordinates for distance and utility evaluation

#### 2. GraphConstrainedDPAlgorithm

Implements the core graph-constrained differential privacy mechanism:

- **Laplace Noise Injection:** Applies Laplace(0, sensitivity / ε) noise to coordinates
- **Graph Projection:** Snaps noisy coordinates to the nearest valid graph node
- **Post-processing Guarantee:** Projection preserves ε-differential privacy
- **Single-Point Obfuscation:** Processes each location independently

#### 3. PrivacyUtilityAnalyzer

Evaluates privacy–utility tradeoffs under differential privacy:

- **Graph Error:** Shortest-path distance between original and obfuscated nodes
- **Euclidean Error:** Straight-line distance between original and obfuscated coordinates
- **Projection Distance:** Distance between noisy and projected points
- **Aggregated Metrics:** Mean errors computed across multiple trials per ε

#### 4. GraphConstrainedDPVisualizer

Provides comprehensive spatial visualization:

- Multi-ε obfuscation demonstrations (original → noisy → projected)
- Privacy–utility tradeoff plots
- Single-obfuscation detailed diagrams
- Publication-ready figures exported per experiment batch

---

## Graph-Constrained Differential Privacy Algorithm

### Algorithm Outline

```text
For each user location L = (x, y):

1. Noise Injection:
   - Compute scale = sensitivity / ε
   - Sample Laplace noise independently for x and y
   - Obtain noisy point (x', y')

2. Graph Projection:
   - Find nearest node v in city graph to (x', y')
   - Replace noisy point with node v

3. Output:
   - Release v as the obfuscated location

4. Privacy Guarantee:
   - Laplace mechanism ensures ε-differential privacy
   - Projection is deterministic post-processing → privacy preserved
```

---

## Key Properties

- **Formal ε-Differential Privacy:** Guaranteed by Laplace mechanism
- **Spatial Realism:** Outputs are valid graph nodes (intersections / roads)
- **Topology Preservation:** Obfuscated locations respect road network structure
- **Configurable Tradeoff:** ε controls privacy–utility balance
- **Stateless Processing:** Suitable for independent location releases

---

## Implementation Features

- Deterministic dummy mode with fixed random seed for reproducibility
- Multiple ε values evaluated in a single run
- Multi-run aggregation for statistically stable metrics
- Clean separation between algorithm, evaluation, and visualization
- Exportable CSV and JSON artifacts for analysis and plotting
- Automatic experiment batching (batch1, batch2, …)

---

## Simulation Parameters

| Parameter   | Default Value           | Description                                |
| ----------- | ----------------------- | ------------------------------------------ |
| City Graph  | 4-node square (dummy)   | Deterministic test graph                   |
| Num Users   | 6 (dummy)               | Location records sampled                   |
| ε Values    | 0.1, 0.5, 1.0, 2.0, 5.0 | Privacy budgets                            |
| Runs per ε  | 30                      | Independent trials per privacy level       |
| Sensitivity | 1.0                     | L1 sensitivity for coordinate perturbation |
| Random Seed | 42                      | Ensures reproducible experiments           |

---

## Performance Metrics

### Privacy Metrics

| Metric           | Description             | Target       |
| ---------------- | ----------------------- | ------------ |
| Privacy Budget ε | Noise magnitude control | Configurable |

### Utility Metrics

| Metric                   | Description                                              | Interpretation         |
| ------------------------ | -------------------------------------------------------- | ---------------------- |
| Mean Graph Error         | Shortest-path hops between original and obfuscated nodes | Topological distortion |
| Mean Euclidean Error     | Straight-line distance between original and obfuscated   | Spatial distortion     |
| Mean Projection Distance | Distance from noisy to projected point                   | Projection impact      |

---

## Visualization Outputs

### 1. Privacy–Utility Analysis

Shows error trends across ε values:

- Graph error vs ε
- Euclidean error vs ε
- Projection distance vs ε

**Output file:** `results/graph_constrained_dp/batchX/privacy_utility_analysis.png`

### 2. Location Obfuscation Demonstration

Multi-ε visualization of:

- Original node (yellow)
- Noisy point (orange X)
- Projected node (red)
- Projection line (purple dashed)

**Output file:** `results/graph_constrained_dp/batchX/graph_constrained_dp_demo.png`

### 3. Single Obfuscation Visualization

Detailed illustration of one obfuscation event.

**Output file:** `results/graph_constrained_dp/batchX/single_obfuscation_visualization.png`

---

## Quick Start

### Prerequisites

```bash
pip install numpy matplotlib networkx
```

### Running the Simulation

```bash
python3 graph_constrained_dp_simulation.py
```

### Generated Files

- `results/graph_constrained_dp/batchX/privacy_utility_analysis.png`
- `results/graph_constrained_dp/batchX/graph_constrained_dp_demo.png`
- `results/graph_constrained_dp/batchX/single_obfuscation_visualization.png`
- `results/graph_constrained_dp/batchX/obfuscated_locations.csv`
- `results/graph_constrained_dp/batchX/simulation_results.json`

---

## Technical Details

### Noise Injection Strategies

| Strategy                  | Description                      | Pros                | Cons               |
| ------------------------- | -------------------------------- | ------------------- | ------------------ |
| Laplace DP                | Add Laplace noise to coordinates | Formal ε-DP         | Unrealistic points |
| Graph-Constrained Laplace | Laplace + projection             | Formal DP + realism | Projection error   |

### Graph Projection Methods

| Method       | Description                | Use Case                  |
| ------------ | -------------------------- | ------------------------- |
| Nearest Node | Snap to closest graph node | Road/intersection privacy |

---

## Current Limitations

### Computational Complexity

| Issue                  | Impact              | Workaround                  |
| ---------------------- | ------------------- | --------------------------- |
| Nearest-node scan      | O(n) per query      | Spatial indexing (future)   |
| Shortest-path failures | Disconnected graphs | Catch exceptions / sentinel |

### Model Assumptions

| Assumption       | Impact                     | Mitigation            |
| ---------------- | -------------------------- | --------------------- |
| Static locations | No temporal composition    | Temporal DP extension |
| Uniform ε        | Same privacy for all users | Adaptive budgets      |

### Privacy Analysis Limitations

| Limitation           | Description                | Mitigation             |
| -------------------- | -------------------------- | ---------------------- |
| Independent releases | No composition accounting  | Sequential DP models   |
| Semantic ignorance   | Sensitive places unmodeled | Semantic DP extensions |

---

## Future Work

### Algorithmic Improvements

| Improvement              | Benefit               | Priority |
| ------------------------ | --------------------- | -------- |
| Adaptive ε selection     | Density-aware privacy | High     |
| Geo-indistinguishability | Distance-aware DP     | High     |
| Hybrid DP + k-anonymity  | Stronger guarantees   | Medium   |

### System Integration

| Integration      | Use Case           | Challenge           |
| ---------------- | ------------------ | ------------------- |
| Real IoT streams | Live anonymization | Latency constraints |
| Edge deployment  | On-device privacy  | Resource limits     |

### Advanced Privacy Features

| Feature                   | Description                             | Privacy Gain |
| ------------------------- | --------------------------------------- | ------------ |
| Adaptive ε-Selection      | Context-aware privacy budget allocation | High         |
| Trajectory-aware DP       | Protect movement sequences              | Very High    |
| Semantic Location Privacy | Protect sensitive locations (home/work) | High         |

### Evaluation Enhancements

| Enhancement         | Benefit              | Research Value |
| ------------------- | -------------------- | -------------- |
| Real-world datasets | Practical validation | High           |
| Attack simulations  | Privacy verification | Critical       |

---

## Research Contributions

### Theoretical Contributions

- Demonstration of post-processing invariance of differential privacy
- Graph-aware formulation of location privacy
- Baseline for comparing unconstrained and constrained DP

### Practical Contributions

- Reproducible experimental framework with batching
- Clean separation of algorithm and evaluation
- Publication-ready visualizations

### Empirical Contributions

- Quantitative privacy–utility tradeoff characterization
- Projection impact analysis
- Comparative baseline for hybrid privacy schemes

---

## Methodological Attribution and Design Choices

### Foundational Model

This implementation is grounded in classical ε-differential privacy using the Laplace mechanism, as introduced by Cynthia Dwork et al., and incorporates spatial intuition from geo-indistinguishability.

Key references:

- Dwork, C. (2006): Foundations of differential privacy and Laplace mechanism.
- Dwork, C., & Roth, A. (2014): The Algorithmic Foundations of Differential Privacy.
- Andrés, M. E., et al. (2013): Geo-indistinguishability for location-based privacy.

### Alignment with Differential Privacy Principles

The implemented algorithm conforms to the core principles of differential privacy:

- **Noise calibration:** Laplace(0, sensitivity / ε) ensures ε-DP.
- **Post-processing:** Graph projection does not weaken privacy guarantees.
- **Stateless releases:** Each location processed independently.

### Concrete Design Choices in This Implementation

While the underlying privacy model follows classical differential privacy theory, several explicit design choices were fixed in this implementation to create a clear, reproducible baseline:

- **Fixed sensitivity:** Sensitivity = 1.0 for baseline comparability
- **Deterministic projection:** Nearest-node graph projection
- **Deterministic dummy graph:** Fixed 4-node square for reproducible testing
- **Random seeding:** Seed = 42 for experiment reproducibility
- **Per-run batching:** Full provenance with experiment batching
- **Real data loaders:** Included but disabled by default

### Scope and Limitations

The current implementation provides a standard, reproducible baseline, not an optimized or adaptive DP system. Advanced variants (adaptive ε, trajectory DP, semantic privacy) are explicitly deferred to future work.

---

## References and Context

### Foundational Papers

1. Dwork, C. (2006). Differential Privacy.
2. Dwork, C., & Roth, A. (2014). The Algorithmic Foundations of Differential Privacy.
3. Andrés, M. E., et al. (2013). Geo-Indistinguishability.

### Related Work

- **Location privacy in smart cities:** Foundational work on protecting user locations
- **Spatial cloaking and k-anonymity:** Non-differential privacy baseline approaches
- **Trajectory privacy and temporal cloaking:** Temporal dimension of privacy protection
- **Differential Privacy:** Formal privacy framework with strong theoretical guarantees

### Research Context

This work is part of the broader "Spatio-temporal Privacy Graph-Based Approaches for Location Privacy in IoT Smart Cities" research initiative, contributing specifically to formal privacy-utility tradeoff characterization and graph-constrained mechanisms for smart city IoT deployments.

---

**Author:** Pushkal Gupta  
**Context:** IoT Smart Cities Privacy Research  
**Date:** February 2026
