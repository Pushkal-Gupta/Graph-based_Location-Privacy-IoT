# Differential Privacy Location Obfuscation for IoT Smart Cities

## Project Overview

This project presents a **differential privacy–based location obfuscation framework** for protecting user and device location privacy in **IoT-enabled smart cities**.  
The system applies the **Laplace mechanism** to perturb coordinate-based location data, providing **formal ε-differential privacy guarantees** while preserving statistical utility for smart city analytics.

The objective is to **balance privacy and utility**, enabling aggregate location-based services and data analysis without revealing exact device positions.

---

## System Architecture

### Core Components

#### 1. DifferentialPrivacyLocationObfuscator

Implements ε-differential privacy using the Laplace mechanism:

- Adds calibrated noise to individual location coordinates
- Uses the privacy budget parameter ε to control noise magnitude
- Smaller ε provides stronger privacy at the cost of higher utility loss

#### 2. IoTSmartCitySimulator

Models a realistic smart city IoT environment:

- Simulates 50 IoT devices across a 10 × 10 city area
- Generates realistic spatial clustering around points of interest
- Supports heterogeneous device types (smartphones, sensors, cameras, vehicles)

#### 3. PrivacyUtilityAnalyzer

Evaluates privacy–utility tradeoffs using:

- Location error (Euclidean distance)
- Statistical error metrics (mean, median, standard deviation, maximum)
- Privacy level categorization based on ε values

---

## Differential Privacy Algorithm

### Algorithm Outline

```text
For each location (x, y):
1. Compute noise scale = sensitivity / ε
2. Sample Laplace noise for x and y independently
3. Generate obfuscated coordinates:
   x' = x + Laplace(0, scale)
   y' = y + Laplace(0, scale)
4. Return obfuscated location (x', y')
```

---

## Key Properties

- Formal ε-differential privacy guarantee
- Privacy does not depend on the number of users
- Resistant to post-processing and background knowledge attacks
- Privacy–utility tradeoff is explicitly tunable via ε

---

## Implementation Features

- Coordinate-level differential privacy using the Laplace mechanism
- Configurable privacy budgets (ε = 0.1, 0.5, 1.0, 2.0, 5.0)
- Realistic IoT device distribution and clustering
- Comprehensive statistical and visual privacy–utility analysis
- Exportable results for reproducibility

---

## Simulation Results

### Performance Metrics by Privacy Level

| ε (epsilon) | Privacy Level     | Mean Error | Median Error | Max Error | Std Dev |
| ----------- | ----------------- | ---------- | ------------ | --------- | ------- |
| 0.1         | Maximum Privacy   | 16.65      | 12.14        | 63.48     | 12.56   |
| 0.5         | Very High Privacy | 3.29       | 2.92         | 9.06      | 2.19    |
| 1.0         | High Privacy      | 1.61       | 1.38         | 5.37      | 1.10    |
| 2.0         | Medium Privacy    | 0.77       | 0.68         | 2.00      | 0.48    |
| 5.0         | Low Privacy       | 0.29       | 0.25         | 1.05      | 0.21    |

### Observations

- Location error decreases logarithmically as ε increases
- Strong privacy (ε = 0.1) introduces significant noise
- ε ≈ 1.0 provides a practical balance between privacy and utility
- High ε values preserve accuracy with limited privacy protection

---

## Visualization Outputs

### 1. Location Obfuscation Demonstration

Shows original and obfuscated locations for multiple ε values, with displacement vectors illustrating noise magnitude.

**Output file:**

```bash
dp_location_obfuscation_demo.png
```

### 2. Privacy–Utility Analysis

Four-panel analysis including:

- Mean location error vs ε
- Error distribution boxplots
- Standard deviation vs ε
- Privacy category comparison

**Output file:**

```bash
dp_privacy_utility_analysis.png
```

### 3. Technical Analysis

Detailed plots showing:

- Noise magnitude distributions
- Noise clouds for different ε values
- Continuous privacy–utility curves
- Device-type-specific error analysis

**Output file:**

```bash
dp_technical_analysis.png
```

---

## Quick Start

### Prerequisites

```bash
pip install numpy matplotlib
```

### Running the Simulation

```bash
python differential_privacy_simulation.py
```

---

## Generated Files

- `dp_location_obfuscation_demo.png`
- `dp_privacy_utility_analysis.png`
- `dp_technical_analysis.png`
- `dp_simulation_results.json`

---

## Technical Details

### Laplace Mechanism

- **Sensitivity:** L1 sensitivity = 1.0
- **Noise Scale:** sensitivity / ε
- **Noise Distribution:** Laplace(0, scale)

---

### City Simulation

- **City Area:** 10 × 10 units
- **IoT Devices:** 50
- **Deployment Model:**
  - Clustering around predefined points of interest
  - Random spatial noise for realism

---

## Evaluation Metrics

- Euclidean distance for location error
- Mean error
- Median error
- Standard deviation
- Maximum error
- Privacy categorization based on ε (epsilon) ranges

---

## Current Limitations

### High Noise for Strong Privacy

- Very small ε values introduce large location displacement
- May reduce usefulness for individual location-based services

---

### Privacy Budget Management

- Repeated queries consume privacy budget
- No built-in budget tracking across applications

---

### Coordinate-Based Obfuscation

- Ignores geographic constraints such as roads and buildings
- May produce physically implausible locations

---

### Uniform Noise Application

- Same noise distribution for all users
- Does not adapt to local density or contextual factors

---

## Future Work

### Algorithmic Extensions

- Gaussian differential privacy
- Local differential privacy variants
- Adaptive and personalized ε selection

---

### Geographic Constraints

- Road-network-aware noise generation
- Building and water-body constraints
- Graph-constrained differential privacy

---

### Adaptive Privacy

- Density-aware noise calibration
- Temporal privacy budget management
- Context-aware privacy control

---

### Hybrid Approaches

- Combination of differential privacy and k-anonymity
- Semantic location protection
- Integration with cryptographic techniques

---

## Research Contributions

- Practical implementation of location differential privacy
- Realistic IoT smart city simulation
- Comprehensive privacy–utility evaluation framework
- Visual analytics for understanding privacy effects
- Modular and extensible research codebase

---

## References and Context

This work builds on foundational concepts in:

- Differential privacy
- Laplace mechanism
- Location privacy in IoT systems
- Privacy–utility tradeoff analysis

This framework serves as a **baseline reference** for studying and comparing probabilistic location privacy mechanisms in smart city environments.

---

**Author:** Pushkal Gupta  
**Context:** IoT Smart Cities Privacy Research  
**Date:** January 2026
