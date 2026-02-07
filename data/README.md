# Input Design for Graph-Based Spatiotemporal Privacy Algorithms

This document explains the **standardized input representation** used across all privacy algorithms in this project.  
The goal is to ensure **one common dataset**, **one data model**, and **consistent comparability** across different privacy techniques.

The algorithms covered are:

- `k_anonymity`
- `density_aware_k_anonymity`
- `differential_privacy`
- `graph_constrained_dp`
- `temporal_cloaking`

All algorithms operate on the **same graph** and the **same trajectory dataset**, differing only in how they transform the data.

---

## 1. High-Level Design Philosophy

The project follows a **graph-based spatiotemporal mobility model**:

- **Graph** represents the _spatial structure_ of the city
- **Trajectories** represent _user movement over time_
- **Privacy algorithms** transform trajectories, not the graph

This separation avoids redundancy, improves modularity, and matches standard research practice in trajectory privacy.

---

## 2. Data Directory Structure

```text
data/
├── synthetic/
│   ├── city_graph.json
│   └── device_locations.csv
```

---

This structure is split into:

- **Graph data** (global, public)
- **Trajectory data** (user-specific, sensitive)

---

## 3. Spatial Model: City Graph (`city_graph.json`)

### Purpose:

Defines **where movement is possible** in the city.

- Nodes represent locations
- Edges represent valid movement paths
- Edge attributes store distance and travel time

### Conceptual Model

Graph G = (V, E)

V → locations (junctions, buildings, grid cells)
E → paths between locations

### JSON Schema

```json
{
  "nodes": [
    { "id": "A", "x": 0, "y": 0 },
    { "id": "B", "x": 1, "y": 0 },
    { "id": "C", "x": 1, "y": 1 }
  ],
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

• distance is typically in meters

• travel_time is typically in seconds

• Coordinates (x, y) are optional but useful for visualization and spatial generalization

• The graph is shared by all users and all algorithms

---

## 4. Spatiotemporal Model: Trajectories (device_locations.csv)

### Purpose

• Stores user movement observations over time.

• This is the primary sensitive dataset that privacy algorithms operate on.

• Canonical Trajectory Definition

• A trajectory is defined as a time-ordered sequence of locations:

```bash
Trajectory_u = [(v₁, τ₁), (v₂, τ₂), ...]
```

Where:
• v is a node in the graph
• τ is a timestamp

### CSV Schema

*Format*
```text
device_id,location_id,date,timestamp
```

```text
1,A,2026-02-01 08:00:00
1,B,2026-02-01 08:10:00
1,C,2026-02-01 08:25:00
2,B,2026-02-01 08:05:00
2,C,2026-02-01 08:20:00
```

### Important Rules

• location_id must match a node ID in city_graph.json

• Timestamps define trajectory order (row order is not relied upon)

• Distance is not stored in the trajectory

• Spatial distance is derived from the graph when needed
