# Spatial Privacy Graph-Based Approaches for Location Privacy in IoT Smart Cities

## Overview

Smart cities rely on large-scale IoT deployments such as smartphones, connected vehicles, cameras, and environmental sensors. These devices continuously generate fine-grained spatial data that can unintentionally reveal sensitive user information such as home locations, workplaces, and mobility patterns.

This repository presents **graph-based spatial privacy approaches** to protect location privacy in IoT-enabled smart cities while preserving data utility for urban analytics.

The project demonstrates two core privacy-preserving techniques:

1. **Graph-based k-Anonymity**
2. **Differential Privacy for Location Obfuscation**

Both approaches are implemented as **simulation-based research prototypes** with visual and quantitative privacy–utility analysis.

---

## Objectives

- Protect user location privacy in smart city IoT systems
- Prevent re-identification from spatial and mobility data
- Preserve usefulness of location data for city-scale analytics
- Demonstrate privacy–utility tradeoffs using practical simulations

---

## System Architecture

### Graph-Based Spatial Modeling

- Urban space is modeled as a **graph**
  - Nodes represent intersections or locations
  - Edges represent roads or connectivity
- User movement is represented as paths over the graph
- Privacy regions are constructed using connected subgraphs

### Privacy Mechanisms

- **k-Anonymity**: Ensures every reported location is indistinguishable among at least _k_ users
- **Differential Privacy**: Adds calibrated noise to location coordinates using the Laplace mechanism

---

## Implemented Approaches

### Approach 1: Graph-Based k-Anonymity

**Concept**

- When a user shares a location, the system finds a connected subgraph containing at least _k_ users
- The exact location is replaced with the centroid of this region
- Ensures spatial cloaking while maintaining realistic urban constraints

**Core Components**

- **SmartCityGraph**  
  Models the urban environment as a graph with intersections and roads.

- **KAnonymityPrivacyManager**  
  Finds connected subgraphs containing ≥ _k_ users and computes anonymized locations.

- **PrivacyAnalyzer**  
  Evaluates privacy–utility tradeoffs using quantitative metrics.

**Key Features**

- BFS-based connected subgraph discovery
- Dynamic k-value evaluation
- Privacy vs. utility measurement
- Visual anonymization regions

**Key Metrics**

- Location error
- Anonymization region size
- User coverage percentage

---

### Approach 2: Differential Privacy on Location Data

**Concept**

- Adds Laplace noise to (x, y) coordinates before sharing
- Privacy controlled via the ε (epsilon) parameter
- Smaller ε → stronger privacy, lower accuracy

**Key Features**

- Multiple privacy levels (ε = 0.1 to 5.0)
- Formal statistical privacy guarantees
- Error distribution and noise analysis
- Device-type aware evaluation

---

## Privacy–Utility Tradeoff Analysis

Both approaches demonstrate the fundamental tradeoff:

- **Higher privacy → Lower accuracy**
- **Lower privacy → Higher utility**

Visual outputs include:

- Original vs. anonymized locations
- Privacy region growth with _k_
- Location error vs. _k_ / ε
- Error distributions and noise clouds

---

## Repository Structure

```text
graph-based-location-privacy-iot/
│
├── README.md
├── requirements.txt
│
├── src/
│   ├── k_anonymity_simulation.py
│   └── differential_privacy_simulation.py
│
├── results/
│   ├── simulation_results.json
│   └── dp_simulation_results.json
│
├── figures/
│   ├── k_anonymity_demo.png
│   ├── privacy_utility_analysis.png
│   ├── dp_location_obfuscation_demo.png
│   └── dp_privacy_utility_analysis.png
│
└── .gitignore
```

---

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

# Run Graph-Based k-Anonymity Simulation

- This simulation demonstrates spatial cloaking using graph-based k-anonymity.

```bash
python k_anonymity_simulation.py
```

- Outputs
  - figures/k_anonymity_demo.png
  - figures/privacy_utility_analysis.png
  - results/simulation_results.json

# Run Differential Privacy Simulation

- This simulation demonstrates location obfuscation using differential privacy with the Laplace mechanism.

```bash
python differential_privacy_simulation.py
```

- Outputs
  - figures/dp_location_obfuscation_demo.png
  - figures/dp_privacy_utility_analysis.png
  - results/dp_simulation_results.json

## Current Limitations

- Graph-based anonymization can be computationally expensive for large city graphs
- Higher privacy settings reduce location accuracy
- Geographic and mobility constraints are simplified
- Static user distributions are assumed

---

## Future Directions

- Edge and fog-based privacy computation
- Adaptive graph models for dynamic mobility
- Hybrid privacy mechanisms combining k-anonymity and differential privacy
- AI-driven privacy–utility optimization
- Integration with real-time IoT sensor streams

---

## Research Context

This project aligns with research in:

- Spatial cloaking
- Graph-based anonymization
- Differential privacy
- Privacy-preserving IoT architectures for smart cities

The repository serves as a **research-oriented, extensible foundation** suitable for academic projects, simulations, and further experimentation.

---

## Research Contributions

- Practical implementation of graph-based k-anonymity
- Differential privacy simulation for spatial data
- Quantitative privacy–utility evaluation
- Clear visualization of anonymization effects
- Modular and extensible research codebase
