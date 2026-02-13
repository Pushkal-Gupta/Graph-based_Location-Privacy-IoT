# Input Design for Graph-Based Spatiotemporal Privacy Algorithms

This document explains the **standardized input representation** used across all privacy algorithms in this project.  
The goal is to enforce **one common dataset**, **one data model**, and **strict comparability** across different privacy techniques.

The algorithms covered are:

- `k_anonymity`
- `density_aware_k_anonymity`
- `differential_privacy`
- `graph_constrained_dp`
- `temporal_cloaking`

All algorithms operate on the **same city graph** and the **same trajectory dataset**, differing only in how user trajectories are transformed.

---

## 1. High-Level Design Philosophy

The project follows a **graph-based spatiotemporal mobility model**:

- The **city graph** represents the spatial structure and movement constraints
- **Trajectories** represent user movement over time
- **Privacy algorithms operate only on trajectories**, never on the graph itself

This separation:

- Avoids redundancy
- Improves modularity
- Matches standard practice in trajectory privacy research
- Enables fair, algorithm-to-algorithm comparison

---

## 2. Data Directory Structure

```text
data/
├── synthetic/
│   ├── city_graph_nodes.json
│   ├── city_graph_edges.json
│   └── device_locations.csv
```

The dataset is explicitly divided into:

- **Graph data** (global, public, shared)
- **Trajectory data** (user-specific, sensitive)

---

## 3. Spatial Model: City Graph

The city graph defines **where movement is possible** in the city.

Instead of a single monolithic file, the graph is split into **nodes** and **edges** to improve clarity, modular loading, and reuse.

Conceptually, the graph is still:

```text
G = (V, E)
```

- **V** → locations
- **E** → valid movement paths between locations

---

## 3.1 Graph Nodes (`city_graph_nodes.json`)

### Purpose

Defines all valid **spatial locations** in the city.

Nodes may represent:

- Road intersections
- Buildings
- Regions
- Grid cells

### JSON Schema

```json
{
  "nodes": [
    { "id": "A", "x": 0, "y": 0 },
    { "id": "B", "x": 1, "y": 0 },
    { "id": "C", "x": 1, "y": 1 }
  ]
}
```

### Notes

- `id` is a unique node identifier
- `(x, y)` coordinates are optional but useful for:
  - Visualization
  - Spatial generalization
  - Density-aware algorithms
- Nodes are shared across all users and all algorithms

---

## 3.2 Graph Edges (`city_graph_edges.json`)

### Purpose

Defines **valid movement paths** between nodes.

Edges encode real-world constraints such as:

- Road connectivity
- Physical distance
- Travel time

### JSON Schema

```json
{
  "edges": [
    {
      "source": "A",
      "target": "B",
      "distance": 120,
      "travel_time": 15
    },
    {
      "source": "B",
      "target": "C",
      "distance": 80,
      "travel_time": 10
    }
  ]
}
```

### Notes

- `source` and `target` must match node IDs from `city_graph_nodes.json`
- `distance` is typically measured in meters
- `travel_time` is typically measured in seconds
- Edges may be treated as directed or undirected depending on the algorithm

---

## 4. Spatiotemporal Model: Trajectories (`device_locations.csv`)

### Purpose

Stores **user movement observations over time**.

This is the **primary sensitive dataset** on which all privacy algorithms operate.

The graph is never modified — **only trajectories are transformed**.

---

### Canonical Trajectory Definition

A trajectory for user _u_ is defined as a time-ordered sequence:

```text
Trajectory_u = [(v₁, τ₁), (v₂, τ₂), ...]
```

Where:

- `v` is a node ID from the city graph
- `τ` is a timestamp

---

### CSV Schema

**Format**

```text
user_id,location_id,timestamp
```

**Sample**

```text
1,A,2026-02-01 08:00:00
1,B,2026-02-01 08:10:00
1,C,2026-02-01 08:25:00
2,B,2026-02-01 08:05:00
2,C,2026-02-01 08:20:00
```

---

### Important Rules

- `location_id` must match a node ID in `city_graph_nodes.json`
- Trajectory order is determined **only by timestamps**
- Distance is **not stored** in the trajectory
- Spatial distance and reachability are derived from the graph when needed
- All privacy algorithms consume this exact format without modification

---

## 5. Why This Design Matters

This input design ensures:

- One shared spatial reality (the graph)
- One shared sensitive dataset (trajectories)
- Algorithm differences reflect **privacy logic only**, not data inconsistencies

As a result:

- Experimental results are reproducible
- Privacy guarantees are comparable
- The system scales cleanly to new algorithms

---

## Summary

This input design establishes a **clean separation between spatial structure and sensitive mobility data**:

- The **city graph** provides a single, shared spatial reality that encodes movement constraints.
- **Trajectories** capture user behavior over time and are the sole target of privacy transformations.
- All privacy algorithms consume the **same inputs** and differ only in how they transform trajectories.

As a result, the system guarantees:

- Consistent and reproducible experiments
- Fair comparison across privacy techniques
- Modular extensibility for future algorithms

In short: **one graph, one trajectory format, many privacy mechanisms — no ambiguity, no data leakage through design.**
