# Graph-Based Privacy Simulation — Canonical Data Specification & Dataset Documentation

This document serves two purposes:

1. It defines the **authoritative canonical input contract** for all privacy algorithms implemented in this project.
2. It documents the dataset construction, preprocessing pipeline, and experimental context used to generate the canonical data.

The specification sections (Spatial Model, Trajectory Model, Invariants, Metric Semantics, Reproducibility Constraints, and Threat Model) define the formal rules that all algorithms must obey.

The later sections describe the underlying dataset, preprocessing pipeline, and research applications for completeness and reproducibility.

All privacy algorithms must operate strictly within the canonical specification defined in this document.

---

## Directory Structure

All algorithms consume data in the following format:

```text
data/
├── city_graph_nodes.json
├── city_graph_edges.json
└── device_locations.csv
```

The dataset is intentionally divided into:

- **Graph data** (shared, public spatial structure)
- **Trajectory data** (user-specific, sensitive observations)

---

## 1. Spatial Model — City Graph

The spatial environment is represented as a graph:

```text
G = (V, E)
```

Where:

- **V** → set of valid spatial locations
- **E** → set of valid movement connections

The graph encodes movement constraints.  
Privacy algorithms **must not modify the graph**.

---

### 1.1 Graph Nodes (`city_graph_nodes.json`)

Defines valid spatial locations.

#### Schema

```json
[
  { "id": "0", "x": 116.3, "y": 39.95 },
  { "id": "1", "x": 116.31, "y": 39.95 }
]
```

### Rules (Graph Nodes)

- `id` must be unique
- `id` must be referenced by trajectories
- `(x, y)` coordinates are used for:
  - Visualization
  - Density computation
  - Spatial aggregation

---

### 1.2 Graph Edges (`city_graph_edges.json`)

The graph is stored as an **undirected 2D grid graph**.

Each edge is stored once and represents bidirectional movement.

#### Schema

```json
[
  {
    "source": "0",
    "target": "1",
    "distance": 120.5,
    "travel_time": 15
  }
]
```

#### Edge Semantics

- Edges are undirected.
- Shortest path calculations must treat edges as bidirectional.
- distance (meters) is the canonical spatial metric.
- All reachability and spatial aggregation must use shortest-path distance over this graph.

### Rules (Graph Edges)

- `source` and `target` must match node IDs
- `distance` is measured in meters
- `travel_time` is measured in seconds
- Edges are strictly undirected and must not be reinterpreted as directed
- All algorithms must treat edges as bidirectional

---

## 1.3 Graph Metric Definition

The spatial metric space is defined as:

- Nodes: V
- Edges: E
- Metric: Shortest-path distance using `distance` edge weight

Formally:

d(u, v) = shortest_path_distance(u, v)

Where shortest path must be computed using Dijkstra’s algorithm or an equivalent exact algorithm.

The graph is connected by construction (30×30 grid).
Disconnected components are not permitted.

If multiple shortest paths exist between two nodes, only the shortest-path distance value is canonical; path identity is not guaranteed to be unique.

---

## 1.4 Spatial Abstraction Model

The city graph is a **deterministic 30×30 grid abstraction**, not a real road network.

Properties:

- 900 nodes
- 1,740 undirected edges
- Regular Manhattan-style adjacency
- Deterministic topology

This graph represents a spatial quantization layer applied to raw GPS coordinates.

It is a controlled spatial model used for algorithmic experimentation.

---

## 2. Spatiotemporal Model — Trajectories

All privacy algorithms operate on:

```text
device_locations.csv
```

This file contains the sensitive user mobility data.

---

### 2.1 Canonical Trajectory Definition

For user `u`:

```text
Trajectory_u = [(v₁, τ₁), (v₂, τ₂), ...]
```

Where:

- `v` is a node ID from the graph
- `τ` is a timestamp

Trajectories are ordered in non-decreasing chronological order.

---

### 2.2 CSV Schema

```text
user_id,location_id,date,time
```

#### Example

```text
0,551,2008-10-23,02:53:04
0,551,2008-10-23,02:53:10
1,203,2008-10-23,08:12:00
```

#### Date Format Rules

To ensure consistency across all records, the date must strictly adhere to the ISO 8601 subset:

Format: `YYYY-MM-DD`

Year: Four digits (e.g., 2026).

Month: Two digits ranging from 01 to 12.

Day: Two digits ranging from 01 to 31.

Timezone: No timezone information is to be encoded within the date field.

---

#### Time Format Rules

Time must be recorded with second-level precision using a standard 24-hour clock:

Format: `HH:MM:SS`

Clock: 24-hour format (ranges from 00 to 23).

Padding: Both minute and second fields must be two digits.

Precision: No sub-second precision (milliseconds/microseconds) is allowed. Time precision is exactly one second.

---

#### Temporal Semantics

These rules govern how records relate to one another and how they should be processed:

Standard Basis: All records are assumed to be in UTC.

Chronological Integrity: For each unique user_id, records must be strictly non-decreasing in (date, time) lexicographic order.

Collision Handling: If identical (date, time) pairs occur for the same user, stable file ordering is preserved (the record appearing first in the source remains first).

---

## 3. Mandatory Invariants

All algorithms must respect the following:

- `location_id` must exist in `city_graph_nodes.json`
- Graph structure must remain unchanged
- Trajectories must remain time-ordered
- No algorithm may alter node coordinates or edge topology
- Distance and reachability must be derived from the graph — never inferred from trajectories

---

## 4. Design Principle

This specification enforces:

- A single shared spatial reality (the graph)
- A single shared sensitive dataset (trajectories)
- Isolation of algorithmic differences to privacy logic only

By fixing the spatial model, temporal semantics, and metric definition, we ensure:

- Fair and reproducible comparison between privacy mechanisms
- Deterministic experimental behavior
- Modular extensibility for future algorithms

## 5. Reproducibility Constraints

To ensure a single shared spatial and temporal reality:

- Grid size is fixed at 30×30
- Graph topology is deterministic and must not change
- Preprocessing must be fully deterministic
- No randomness is permitted in data generation
- Output dataset must be versioned

Bounding box parameters and speed thresholds are defined in the processing documentation and must remain fixed across experimental runs.

All published experiments must reference:

- Dataset version
- Processing script version
- Git commit hash (recommended)

---

## 6. Threat Model Assumptions

All privacy evaluations assume:

- The adversary has full knowledge of the graph G = (V, E)
- The adversary may observe partial or full released trajectories
- Timestamps are considered public information
- Node coordinates are public
- Only user identity linkage is considered sensitive
- No auxiliary external side information beyond the graph and released dataset is assumed

Privacy mechanisms are evaluated strictly under these assumptions.

---

## 7. Dataset Overview

This project implements a graph-based spatial abstraction layer over real-world mobility data using the **Microsoft GeoLife GPS Trajectory Dataset**. Raw GPS trajectories are mapped onto a structured city grid graph to create a controlled spatial environment for privacy algorithm experimentation and mobility analysis.

The system ensures:

- **Single Shared Reality:** A unified graph model for all spatial analysis.
- **Data Integrity:** A single shared sensitive dataset with a clear separation between raw and processed data.
- **Consistency:** A deterministic and reproducible preprocessing pipeline.

---

## 8. Dataset Details

**Dataset Name:** Microsoft GeoLife GPS Trajectory Dataset  
**Source:** Microsoft Research Asia  
**Official Link:** https://www.microsoft.com/en-us/download/details.aspx?id=52367

#### Statistics (Version 1.3)

| Category             | Value                    |
| -------------------- | ------------------------ |
| **Users**            | 182                      |
| **Period**           | April 2007 – August 2012 |
| **GPS Points**       | ~24 Million              |
| **Total Distance**   | ~1.29 Million km         |
| **Primary Location** | Beijing, China           |

---

## 9. Dataset Setup Instructions

This repository does **not** redistribute the Microsoft GeoLife dataset. You must acquire it manually:

1. Visit the official Microsoft download page.
2. Download the **GeoLife GPS Trajectory Dataset (Version 1.3)**.
3. Extract the archive into your local project directory.

---

## 10. Processing Pipeline

#### 10.1 City Grid Construction

The script creates a **30×30 spatial grid** and generates the following files:

- `city_graph_nodes.json`
- `city_graph_edges.json` (Fully connected 2D grid graph)

#### 10.2 Trajectory Mapping

- **Filtering:** GPS points are filtered within a specific bounding box.
- **Speed Cleaning:** Removes unrealistic jumps via speed filtering.
- **Abstraction:** Maps latitude/longitude coordinates to specific grid cell IDs.
- **Output:** Generates `device_locations.csv`.

---

## 11. Sanity Checks & Validation

The following metrics were validated to ensure data quality:

- **Node Count:** 900 distinct city nodes.
- **Edge Count:** 1,740 undirected edges.
- **User Coverage:** 179 distinct users successfully mapped.
- **Mobility Patterns:** Confirmed heavy-tailed user contribution and central urban concentration.

---

## 12. Research Applications

This framework provides a unified spatial model for:

- **Location Privacy:** Graph-based k-anonymity simulations.
- **Mobility Mining:** Spatial entropy and pattern analysis.
- **Anonymization:** Evaluating trajectory protection algorithms.

---

## 13. Reproducibility

To regenerate the processed data from the raw GeoLife files, run:

```bash
cd processing_script
python process_geolife.py
```

All outputs will be stored in the `processed_data/` directory.

## Citation & License

The GeoLife dataset is released by Microsoft Research under a **non-commercial research license**.

When using this framework in academic work, you must cite the original GeoLife publications as specified in the official user guide provided with the dataset.

Please ensure compliance with all licensing terms before redistributing, publishing, or using the dataset in derived research.
