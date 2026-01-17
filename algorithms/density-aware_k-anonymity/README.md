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

Models the smart city as a graph:

- Nodes represent intersections  
- Edges represent road connectivity  
- Users are randomly placed across nodes  

This creates a simplified urban layout suitable for evaluating location privacy mechanisms.

---

### 2. ADKA Density Module

Computes local neighborhood density using BFS depth = 1:

- Counts users at the target node  
- Counts users at 1-hop neighbors  
- Determines if the region is sparse, medium, or dense  

---

### 3. Adaptive k Selector

Chooses the anonymity level *k* based on density:

if density < 4:
k = 10
elif density < 10:
k = 5
else:
k = 2


This provides **context-aware privacy adaptation**.

---

### 4. Region Expansion Module

Implements BFS-based region growth:

- Starts from the target node  
- Expands to neighbors  
- Accumulates users  
- Stops when total users ≥ k  

Produces a connected anonymization region.

---

## ADKA Algorithm

### Algorithm Outline

For each target user:

Compute local density (BFS depth = 1)

Select k based on density thresholds

Initialize region with target node

Expand region using BFS

Accumulate users

Stop when users ≥ k

Return anonymized region


---

## Key Properties

- k adapts automatically based on density  
- Ensures stronger privacy in sparse areas  
- Maintains higher accuracy in dense areas  
- Always produces connected regions  
- Lightweight and efficient for IoT graphs  

---

## Implementation Features

- Density-aware adaptive k selection  
- BFS-based anonymization region expansion  
- 20-run experimental evaluation  
- Three visualization outputs:
  1. Density vs Selected k  
  2. Selected k vs Region Size  
  3. Graph-based anonymization region visualization  
- Easy-to-understand modular Python code  

---

## ADKA Experiment Results

### Multi-Run Output Example

Run 1: Target=7, Density=3, k=10, Region Size=11
Run 2: Target=22, Density=6, k=5, Region Size=2
Run 3: Target=16, Density=10, k=2, Region Size=1


### Observations

- Low density ⇒ k = 10 ⇒ larger regions  
- Medium density ⇒ k = 5 ⇒ mid-sized regions  
- High density ⇒ k = 2 ⇒ minimal region size  
- Scatter plots confirm correct adaptive behavior  

---

## Visualization Outputs

### 1. Density vs Selected k
Shows how k decreases as local density increases.

### 2. Selected k vs Region Size
Illustrates how region size grows with larger values of k.

### 3. Anonymized Region Visualization
Displays the graph where:

- Blue nodes = full grid  
- Red nodes = anonymized region  

---

## Quick Start

### Prerequisites

pip install networkx matplotlib


### Run the Program

python adka.py


---

## Generated Visual Outputs

Running the algorithm will display three figures:

- Density vs Selected k  
- Selected k vs Region Size  
- Graph visualization of anonymized region  

---

## Technical Details

### Graph Model

- 5 × 5 grid city graph  
- Undirected connectivity  
- Random user placement  

### Privacy Computation

- Dynamic k selection  
- BFS-based region expansion  
- Connected region guarantee  

### Metrics Collected

- Local density  
- k value  
- Region size  

---

## Current Limitations

- Small grid size  
- Static users (no mobility model)  
- BFS limited to depth 1 for density estimation  
- No coordinate-level error metric  

---

## Future Work

- Multi-hop density estimation  
- Integration with fixed-k algorithms  
- Differential privacy extensions  
- Mobility-aware anonymization  
- Real-world IoT deployment models  

---

## Research Contributions

- First implementation of ADKA for IoT smart cities  
- Demonstrates adaptive k selection based on density  
- Provides clear visualization and empirical evaluation  
- Establishes a reusable foundation for future privacy frameworks  

---

## References and Context

This work builds upon concepts from:

- Graph-based anonymization  
- Spatial cloaking  
- IoT location privacy  
- Privacy–utility optimization  

---

**Author**: Praagya Garg
**Context**: IoT Smart Cities Privacy Research  
**Date**: January 2026
