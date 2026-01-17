# Adaptive Density-Aware k-Anonymity for IoT Location Privacy (ADKA)

This project implements **Algorithm 4: Adaptive Density-Aware k-Anonymity (ADKA)**, designed to protect user location privacy in IoT-enabled Smart Cities. Unlike traditional graph-based k-anonymity (fixed k), ADKA **dynamically adjusts the anonymity level (k)** based on the **local population density** around the user.

This ensures:
- Higher privacy in **sparse** areas  
- Higher accuracy in **dense** areas  
- Better overall **privacy–utility tradeoff**

---

##  Features

-  Simulated **5×5 smart-city grid graph** using NetworkX  
-  Random distribution of users across nodes  
-  Density-aware **adaptive k selection** (k ∈ {2, 5, 10})  
-  BFS-based region expansion until ≥ k users are covered  
-  Visualization using Matplotlib (red nodes = anonymized region)  
-  Support for **multiple-run experiments**  
-  Plots for:
  - Density vs Selected k  
  - k vs Region Size  

---

##  Algorithm Overview (ADKA)

ADKA consists of four main stages:

###  Graph Construction  
A 5×5 grid graph models a portion of a smart city.  
Each node represents an intersection.

###  Density Computation  
For a target user, ADKA computes **local density** using BFS:

> Count users at the target node + its 1-hop neighbors.

###  Dynamic k Selection  
Based on density:

if density < 4:
k = 10 # high privacy in low-density regions
elif density < 10:
k = 5 # medium privacy in medium-density regions
else:
k = 2 # high accuracy in high-density regions


###  Region Expansion  
Perform BFS from the target node until the region contains at least **k users**.

###  Visualization  
Red nodes = anonymized region  
Blue nodes = entire city graph


---

##  Example Terminal Output

Users per node: {0: 2, 1: 0, ..., 24: 1}

Target: 7
Density: 6
Selected k: 5
Output region: {2, 6, 7, 12}


This indicates:
- Target user is at node 7  
- Local density = 6  
- ADKA selected k = 5  
- The anonymized region includes nodes {2, 6, 7, 12}  

---

##  Example Visualization

A Matplotlib window will appear showing:

-  **Blue nodes** → the entire graph  
-  **Red nodes** → anonymized region for the target user  

Example (conceptual):

[0] -- [1] -- [2] ← part of connected anonymized region
|
[7] ← target user


---

## Multi-Run Experiment Output (ADKA)

The multi-run experiment produces:

- 20 random target selections  
- Density, k, and region size per run  
- Two plots:
  - **Density vs Selected k**
  - **Selected k vs Region Size**

These validate the adaptive behavior of ADKA.

