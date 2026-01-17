# Algorithms — Graph-based Location Privacy for IoT

This directory contains the **core algorithmic implementations** used in the
_Graph-based Location Privacy for IoT Smart Cities_ project.

Each subfolder corresponds to a **distinct location privacy mechanism or
privacy-preserving strategy**, implemented and evaluated independently, while
following a **consistent documentation and implementation structure**.

---

## Purpose of This Folder

The `algorithms/` directory serves to:

- Provide **modular implementations** of location privacy algorithms
- Enable **fair comparison** between multiple privacy mechanisms
- Support **experimental evaluation** within smart city IoT simulations
- Act as a **research-ready codebase** for extensions and benchmarking

Each algorithm is self-contained and documented using a standardized README
format described below.

---

## Folder Structure

```text
algorithms/
│
├── __init__.py
│
├── k_anonymity/
│   ├── k_anonymity.py
│   ├── README.md
│   └── config.yaml
│
├── differential_privacy/
│   ├── laplace_dp.py
│   ├── README.md
│   └── config.yaml
│
├── graph_constrained_dp/
│   ├── graph_constrained_dp.py
│   ├── README.md
│   └── config.yaml
│
├── density_aware_k_anonymity/
│   ├── density_aware_k.py
│   ├── README.md
│   └── config.yaml
│
└── temporal_cloaking/
    ├── temporal_cloaking.py
    ├── README.md
    └── config.yaml
```

Each subdirectory under `algorithms/` represents a self-contained
location privacy mechanism. Every algorithm follows a consistent structure:

- `*.py` — Core algorithm implementation
- `README.md` — Algorithm-specific documentation (theory, design, usage)
- `config.yaml` — Configurable parameters and experimental settings

This design enables modular experimentation, fair comparison, and
easy integration with the evaluation and experimentation pipeline.

Each algorithm resides in its **own subdirectory** with its own README.

---

## Standard README Structure (Per Algorithm)

Every algorithm subfolder follows the **same README structure** to ensure
clarity, reproducibility, and ease of comparison.

### 1. Algorithm Overview

- High-level description of the privacy mechanism
- Motivation and problem addressed
- Type of location privacy (e.g., differential privacy, graph-based, hybrid)

### 2. Theoretical Background

- Core privacy concepts used
- Mathematical or graph-based foundations
- Assumptions and threat model (if applicable)

### 3. Algorithm Design

- Step-by-step explanation of the algorithm
- Graph construction or spatial modeling approach
- Privacy parameter definitions (e.g., ε, k, budget)

### 4. Implementation Details

- Programming language used
- Key dependencies and libraries
- Important functions or modules

### 5. Inputs and Outputs

- Expected input data format
- Privacy parameters and configuration options
- Output format and interpretation

### 6. Usage Instructions

- How to run the algorithm
- Example commands or function calls
- Configuration or parameter tuning notes

### 7. Privacy–Utility Considerations

- Impact of parameters on privacy and accuracy
- Known trade-offs
- Limitations of the approach

### 8. Evaluation Notes (If Applicable)

- Metrics used for evaluation
- Experimental assumptions
- Compatibility with the main evaluation pipeline

### 9. References

- Academic papers, standards, or prior work
- Links to relevant research

---

## Integration with the Main Framework

Algorithms in this folder are designed to integrate with:

- Smart city IoT simulations
- Location privacy evaluation modules
- Visualization and analytics components
- Comparative privacy–utility analysis workflows

They can be executed independently or as part of a **larger experimental
pipeline** defined in the root project.

---

## Conventions and Guidelines

- One algorithm per folder
- One `README.md` per algorithm
- Clear separation of logic and evaluation
- Consistent naming and parameter definitions across algorithms
- Research-oriented documentation style

---

## Credits

**Author:** Pushkal Gupta
**Project:** Graph-based Location Privacy for IoT Smart Cities

---

## License

This project and all algorithms within this folder are licensed under the
**Apache License, Version 2.0**.

You may not use this code except in compliance with the License.
A copy of the License is available at:

http://www.apache.org/licenses/LICENSE-2.0

```

```
