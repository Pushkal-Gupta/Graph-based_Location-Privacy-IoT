# Adaptive Density-Aware k-Anonymity for IoT Location Privacy (ADKA)

This project implements Algorithm 4: Adaptive Density-Aware k-Anonymity (ADKA), designed to protect user location privacy in IoT-enabled Smart Cities. Unlike traditional graph-based k-anonymity with a fixed k, ADKA dynamically adjusts the anonymity level based on local user density, achieving a better privacy–utility tradeoff.

This approach ensures:
- Higher privacy in sparse regions
- Higher spatial accuracy in dense regions
- Context-aware anonymization

---

## Features

- Simulated 5×5 smart-city grid graph using NetworkX  
- Random distribution of users across graph nodes  
- Density-aware adaptive k selection (k ∈ {2, 5, 10})  
- BFS-based region expansion until at least k users are included  
- Support for multiple-run experiments  
- Three types of visual outputs generated using Matplotlib:
  1. Density vs Selected k plot
  2. Selected k vs Region Size plot
  3. Graph-based visualization of the anonymized region

---

## Algorithm Overview

Adaptive Density-Aware k-Anonymity (ADKA) consists of the following stages:

### Graph Construction
A 5×5 grid graph is used to represent a smart city layout, where each node corresponds to a road intersection.

### Density Computation
For a given target user, local density is computed using breadth-first search with depth 1:
- Users at the target node
- Users at immediate neighboring nodes

### Adaptive k Selection
The anonymity parameter k is selected based on the computed density:

if density < 4:
k = 10
elif density < 10:
k = 5
else:
k = 2


### Region Expansion
The anonymization region is constructed by expanding outward from the target node using BFS until the total number of users in the region is at least k.

### Visualization Outputs
The algorithm produces three visual outputs:
1. A scatter plot showing Density vs Selected k
2. A scatter plot showing Selected k vs Region Size
3. A graph-based visualization of the city graph where:
   - Blue nodes represent the entire city graph
   - Red nodes represent the anonymized region for a sample target user

---

## Example Terminal Output

Users per node: {0: 2, 1: 0, ..., 24: 1}

Target: 7
Density: 6
Selected k: 5
Output region: {2, 6, 7, 12}


This output indicates:
- The target user is located at node 7
- The local neighborhood density is 6
- ADKA selects k = 5
- The anonymized region contains nodes {2, 6, 7, 12}

---

## Visualization Results

When the program is executed, the following figures are displayed sequentially:

1. Density vs Selected k  
   This plot illustrates how the anonymity parameter k decreases as local user density increases.

2. Selected k vs Region Size  
   This plot shows the relationship between the chosen k value and the size of the anonymization region in terms of graph nodes.

3. Anonymized Region Visualization  
   This figure displays the smart-city graph with the anonymized region highlighted:
   - Blue nodes represent the entire graph
   - Red nodes represent the anonymization region for a selected target user

---

## Multi-Run Experiment Description

The multi-run experiment performs 20 anonymization runs using randomly selected target users. For each run, the following are recorded:
- Local density
- Selected k value
- Size of the anonymization region

The generated plots validate that ADKA dynamically adapts k based on density and produces appropriately sized anonymization regions.
