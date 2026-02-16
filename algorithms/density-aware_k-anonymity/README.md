Perfect 👍 Since your algorithm has evolved significantly (real processed_data integration, 30×30 grid, percentile-based adaptive k, graph JSON loading, no pickle, real trajectory counts, proper results folder structure), your README must reflect the actual architecture.

Below is your **fully updated, detailed, and consistent README** in the exact same structured format.

---

# Density-Aware k-Anonymity for Location Privacy in IoT Smart Cities

## Project Overview

This project implements **Density-Aware Adaptive k-Anonymity (DAAKA)** for protecting user location privacy in IoT-enabled smart cities.

The system models the urban environment as a **grid-based spatial graph constructed from real GeoLife GPS trajectories** and dynamically adjusts the anonymity level (`k`) based on **local trajectory density**.

Unlike traditional fixed-k anonymization methods, this approach:

* Enforces stronger privacy in sparse regions
* Preserves higher utility in dense urban zones
* Automatically adapts to dataset scale using percentile-based thresholds

**Key Feature:**
The system now fully integrates the **Microsoft GeoLife GPS Trajectory Dataset**, builds a structured spatial graph (`city_graph_nodes.json`, `city_graph_edges.json`), and operates on real processed trajectory data.

---

## Features

* Full integration of Microsoft GeoLife GPS dataset
* Automated spatial graph generation (grid-based city model)
* JSON-based graph structure (`nodes` and `edges`)
* Trajectory-to-grid mapping with speed filtering
* Density-aware adaptive k selection using percentile thresholds
* BFS-based connected anonymization region expansion
* Detailed verbose simulation output (per-run explanation)
* Automatic result visualization
* Organized results saved under `results/density_aware_k_anonymity/`

---

## System Architecture

### Core Components

---

### 1. SmartCityGraph

Represents the city as a structured graph loaded from processed dataset files.

**Loads from:**

* `city_graph_nodes.json`
* `city_graph_edges.json`
* `device_locations.csv`

**Responsibilities:**

* Builds graph using NetworkX
* Stores geographic node positions
* Computes trajectory count per node
* Provides neighbor access for density calculation

**Graph Characteristics:**

* Default Grid: 30 × 30 (900 nodes)
* Undirected graph
* Edges store:

  * Distance (meters)
  * Travel time (seconds)

---

### 2. DensityAwareAdaptiveKAnonymityAlgorithm

Implements adaptive privacy logic.

#### Local Density Calculation

* Uses 1-hop neighborhood
* Density = users at node + users at neighbors
* Verbose breakdown printed per run

#### Percentile-Based Adaptive k Selection

Instead of static thresholds, the algorithm computes:

* P33 (33rd percentile)
* P66 (66th percentile)

Density classification:

* **Sparse** → density < P33 → k = 10
* **Medium** → P33 ≤ density < P66 → k = 5
* **Dense** → density ≥ P66 → k = 2

This makes the system fully dataset-scale adaptive.

---

### 3. Region Expansion (Privacy Enforcement)

Uses **Breadth-First Search (BFS)**:

* Starts from target node
* Expands to neighbors
* Stops when total trajectory count ≥ selected k
* Ensures anonymization region is connected

---

### 4. DensityAwareAdaptiveKAnonymityExperiment

Handles simulation and evaluation.

For each run:

* Randomly selects a target node
* Prints:

  * Target node
  * Users at node
  * Neighbor list
  * Users at each neighbor
  * Computed local density
  * Density classification
  * Selected k
  * Region size

Collects:

* Density values
* k values
* Region sizes

Outputs summary statistics.

---

### 5. Visualization

Three analytical plots are generated and saved automatically:

Saved in:

```
results/density_aware_k_anonymity/
```

1. `density_vs_k.png`
2. `k_vs_region_size.png`
3. `region_size_distribution.png`

---

## Dataset Integration

### Dataset

* **Microsoft GeoLife GPS Trajectory Dataset**
* Contains real user movement trajectories in Beijing

### Preprocessing Pipeline

`preprocess_geolife.py` performs:

1. Reads `.plt` trajectory files
2. Filters coordinates within Beijing bounds
3. Applies speed filtering (removes unrealistic movement)
4. Maps GPS points to grid cells
5. Generates:

```
processed_data/
    city_graph_nodes.json
    city_graph_edges.json
    device_locations.csv
```

### Important Notes

* Density is based on **trajectory count**, not unique users
* No synthetic fallback users are used
* No pickle-based user_counts file is used anymore

---

## Algorithm Logic

### Density Calculation

```
Local Density = 
Users at target node +
Users at all 1-hop neighbors
```

### Adaptive k Logic (Percentile-Based)

Let:

* P33 = 33rd percentile of node densities
* P66 = 66th percentile of node densities

Then:

* Sparse → k = 10
* Medium → k = 5
* Dense → k = 2

This ensures:

* Automatic calibration
* Dataset-independent scaling
* Realistic adaptive behavior

---

## Simulation Parameters

| Parameter        | Value                                | Description             |
| ---------------- | ------------------------------------ | ----------------------- |
| Grid Size        | 30 × 30 (default)                    | 900 spatial nodes       |
| Dataset          | GeoLife (real trajectories)          | Processed GPS data      |
| Simulation Runs  | 25                                   | Random node sampling    |
| Density Depth    | 1 hop                                | Local neighborhood      |
| Expansion Method | BFS                                  | Connected anonymization |
| Threshold Method | Percentile-based (P33, P66)          | Adaptive scaling        |
| Output Folder    | `results/density_aware_k_anonymity/` | Saved plots             |

---

## Visualization Outputs

### 1. Density vs Adaptive k

Shows how adaptive k varies across density spectrum.

### 2. k vs Region Size

Shows privacy–utility tradeoff.

### 3. Region Size Distribution

Histogram showing anonymization overhead.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install networkx matplotlib pandas numpy
```

---

### 2. Prepare GeoLife Dataset

Place raw dataset under:

```
data/original_data/Data/
```

---

### 3. Run Preprocessing

```bash
python3 data/processing_script/preprocess_geolife.py
```

This generates:

```
data/processed_data/
    city_graph_nodes.json
    city_graph_edges.json
    device_locations.csv
```

---

### 4. Run Simulation

```bash
python3 algorithms/density-aware_k-anonymity/density_aware_k_anonymity_simulation.py
```

---

### Expected Output

* Full node user distribution
* 25 detailed experiment runs
* One experiment summary
* 3 plots saved in results folder

---

## Current Limitations

* Density based on trajectory frequency, not unique user identity
* Grid-based approximation (not real road network)
* Static snapshot (no temporal cloaking)
* Single-hop density only
* No differential privacy noise added

---

## Future Improvements

* Multi-hop adaptive density
* Unique-user density instead of trajectory count
* Integration with OpenStreetMap (real road graph)
* Temporal cloaking extension
* Differential privacy integration
* Dynamic privacy budget tuning
* Larger grid resolution (e.g., 50×50)

---

**Author:** Praagya Garg  
**Context:** IoT Smart Cities Privacy Research  
**Dataset:** Microsoft GeoLife GPS Trajectory Dataset  
**Date:** January 2026

