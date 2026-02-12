# Density-Aware k-Anonymity for Location Privacy in IoT Smart Cities

## Project Overview

This project implements **Density-Aware Adaptive k-Anonymity (DAAKA)** for protecting user location privacy in IoT-enabled smart cities. 

The system models the urban environment as a grid-based graph and dynamically adjusts the anonymity level (`k`) based on **local user density** derived from real-world GPS trajectories. This adaptive approach provides a better **privacy-utility tradeoff** compared to traditional fixed-k methods: stricter privacy in sparse areas and higher utility in dense regions.

**Key Feature**: The project now uses the **real Microsoft GeoLife GPS Trajectory Dataset** instead of synthetic random users.

---

## Features

- Real GPS trajectory data processing from GeoLife dataset
- Grid-based spatial modeling of Beijing area
- Density-aware adaptive k selection
- Connected region expansion using BFS
- Detailed simulation with metrics and visualization
- All outputs saved in a clean `results/` folder

---

## System Architecture

### Core Components

#### 1. SmartCityGraph
- Represents the city as a **5x5 grid graph** (25 nodes)
- Loads real user counts from GeoLife trajectories via `user_counts.pkl`
- Maps nodes to geographic coordinates using Beijing bounding box

#### 2. DensityAwareAdaptiveKAnonymityAlgorithm
- Computes local density using 1-hop BFS
- Adaptive k-selection based on density levels
- Expands connected anonymization region until required k is met

#### 3. DensityAwareAdaptiveKAnonymityExperiment
- Runs multiple simulation iterations
- Collects density, k, and region size metrics
- Generates detailed console output

#### 4. Visualization
- Three analytical plots saved in `results/` folder

---

## Dataset Integration

- **Dataset**: Microsoft GeoLife GPS Trajectory Dataset
- **Processing**: `preprocess_geolife.py` reads `.plt` files, assigns trajectories to 5x5 grid cells, and counts **unique users** per cell
- **Output**: `user_counts.pkl` containing real user distribution
- **Sampling**: Limited to first 50 users for performance (can be increased)

---

## Algorithm Logic

### Adaptive k-Selection
- **Sparse** (< 10 users) → k = 10
- **Medium** (10–29 users) → k = 5
- **Dense** (≥ 30 users) → k = 2

### Region Expansion
Uses BFS to grow a connected region starting from the target node until the total unique users ≥ selected k.

---

## Simulation Parameters

| Parameter           | Value          | Description                              |
|---------------------|----------------|------------------------------------------|
| Grid Size           | 5 × 5          | 25 nodes covering Beijing area           |
| Dataset             | GeoLife        | Real GPS trajectories (up to 50 users)   |
| Simulation Runs     | 25             | Randomly sampled target nodes            |
| Density Depth       | 1 hop          | Neighborhood for density calculation     |
| Expansion Method    | BFS            | Ensures connected regions                |
| Output Folder       | `results/`     | All plots saved here                     |

---

## Visualization Outputs

All plots are automatically saved in the **`results/`** folder:

1. **`density_vs_k.png`**  
   Shows relationship between local density and chosen adaptive k

2. **`k_vs_region_size.png`**  
   Shows how selected k affects the size of the anonymization region

3. **`region_size_distribution.png`**  
   Histogram showing frequency of different region sizes (utility analysis)

---

## Quick Start

### 1. Prerequisites

```bash
pip install networkx matplotlib pandas geopandas shapely
```

### 2. Prepare the Dataset

```bash
python3 preprocess_geolife.py
```
→ Make sure your GeoLife data is in `./geolife_data/Data/` folder

### 3. Run the Simulation

```bash
python3 density_aware_k_anonymity_simulation.py
```

### Expected Output
- User distribution table from real data
- Detailed per-run analysis
- Experiment summary (avg density, avg k, avg region size)
- 3 plots saved in `results/` folder

---

## Project Structure

```
.
├── preprocess_geolife.py           # GeoLife data → grid user counts
├── density_aware_k_anonymity.py    # Core classes
├── density_aware_k_anonymity_simulation.py  # Main simulation runner
├── user_counts.pkl                 # Generated user distribution
├── results/                        # Output plots
│   ├── density_vs_k.png
│   ├── k_vs_region_size.png
│   └── region_size_distribution.png
└── geolife_data/                   # Raw dataset folder
```

---

## Current Limitations

- Coarse 5×5 grid (large cell size ≈ 35–40 km)
- Static snapshot (no temporal analysis yet)
- Limited to 50 users for faster processing

---

## Future Improvements

- Finer grid resolution (20×20 or higher)
- Real road network integration (OSM)
- Temporal cloaking support
- Full 182 users from GeoLife dataset
- Interactive visualizations


---

**Author:** Praagya Garg  
**Context:** IoT Smart Cities Privacy Research  
**Dataset**: Microsoft GeoLife GPS Trajectory Dataset  
**Date:** January 2026


