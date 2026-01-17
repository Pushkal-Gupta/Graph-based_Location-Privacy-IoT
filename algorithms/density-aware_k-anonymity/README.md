# Adaptive Density-Aware k-Anonymity (ADKA) for Location Privacy in IoT Smart Cities

## Project Overview

This project implements **Algorithm 4: Adaptive Density-Aware k-Anonymity (ADKA)** for ensuring user location privacy in IoT-enabled smart cities.  
Unlike traditional graph-based k-anonymity, which uses a fixed k, ADKA dynamically adjusts the anonymity parameter based on local user density, providing an improved privacy–utility tradeoff.

The system models an urban environment as a grid-based graph and generalizes user locations into **connected anonymization regions** that contain at least *k* users, where k is chosen adaptively.

---

## System Architecture

### Core Components

---

### 1. Smart-City Graph Model

The smart city is represented as a **5 × 5 grid graph**:

- Nodes represent intersections  
- Edges represent road connectivity  
- Users are randomly placed across nodes  

This forms a simplified urban structure suitable for evaluating privacy mechanisms.

---

### 2. ADKA Density Module

Computes local neighborhood density using BFS depth = 1:

- Counts users at the target node  
- Counts users at all 1-hop neighbors  
- Determines whether the area is sparse, medium-density, or dense  

---

### 3. Adaptive k Selector

Selects the anonymity parameter *k* dynamically:

if density < 4:
k = 10 # high privacy
elif density < 10:
k = 5 # moderate privacy
else:
k = 2 # high accuracy


This enables **context-aware anonymization**.

---

### 4. Region Expansion Module

Builds a connected anonymization region using BFS:

- Starts from the target node  
- Expands to neighbors  
- Accumulates users  
- Stops once total users ≥ k  

This ensures connected, realistic anonymization regions.

---

## ADKA Algorithm

### Algorithm Outline

For each target user:

Compute local neighborhood density (BFS depth = 1)

Select k based on density thresholds

Initialize region with target node

Expand region using BFS

Accumulate users in region

Stop once users ≥ k

Output anonymized region


---

## Key Properties

- k varies automatically based on local density  
- Higher privacy in sparse regions  
- Higher accuracy in dense regions  
- Regions are always connected  
- Efficient for grid-based smart city environments  

---

## Implementation Features

- Density-aware dynamic k selection  
- BFS region expansion  
- Multi-run experimentation (20 runs)  
- Three visualization outputs:
  1. Density vs Selected k  
  2. Selected k vs Region Size  
  3. Graph visualization of anonymized region  
- Simple, modular Python implementation  

---

## ADKA Experiment Results

### Multi-Run Metrics

Each run logs:

- Target node  
- Local density  
- Selected k  
- Region size (in nodes)  

Example:

Run 1: Target=7, Density=3, k=10, Region Size=11
Run 2: Target=22, Density=6, k=5, Region Size=2
Run 3: Target=16, Density=10, k=2, Region Size=1


---

## Observations

- Low density → high k → larger anonymized regions  
- Moderate density → k = 5 → medium regions  
- High density → k = 2 → small, accurate regions  
- Scatter plots confirm correct adaptive behavior  

---

## Visualization Outputs

### 1. Density vs Selected k  
Shows how selected k decreases as local density increases.

### 2. Selected k vs Region Size  
Shows how larger k produces larger anonymization regions.

### 3. Graph Visualization of Anonymized Region  
Displays the city grid where:

- Blue nodes = entire graph  
- Red nodes = anonymized region  

---

## Quick Start

### Prerequisites

pip install networkx matplotlib


### Run the Algorithm

python adka.py


---

## Generated Files

The program displays three visual outputs:

- Density vs Selected k  
- Selected k vs Region Size  
- Graph visualization of a sample anonymized region  

---

## Technical Details

### Graph Model

- 5 × 5 grid structure  
- Undirected edges  
- Random user assignment  

### Privacy Computation

- Density-aware k  
- BFS-based region expansion  
- Connected anonymization guarantee  

### Metrics Collected

- Local density  
- Selected k  
- Region size  

---

## Current Limitations

- Small grid size (5 × 5)  
- No temporal (trajectory) privacy  
- Density estimation limited to BFS depth 1  
- No location error/utility metric  

---

## Future Work

- Multi-scale density estimation  
- Integration with fixed-k algorithm for comparison  
- Differential privacy extensions  
- Real-world traffic models  
- Mobility-aware region construction  

---

## Research Contributions

- First minimal implementation of ADKA  
- Demonstrates dynamic, density-aware privacy protection  
- Produces comprehensive visualization outputs  
- Provides baseline for advanced privacy models  

---

## References and Context

This work draws upon:

- Graph-based k-anonymity  
- Location privacy in IoT networks  
- Spatial cloaking techniques  

It forms a foundation for future smart city privacy research.

---

**Author**: Pushkal Gupta  
**Context**: IoT Smart Cities Privacy Research  
**Date**: January 2026
