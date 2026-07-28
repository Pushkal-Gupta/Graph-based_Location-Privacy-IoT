# Real-Topology Comparison (GeoLife, central-Beijing OSM graph, ~3.1k nodes)

Representative configs, window = 10 min, GeoLife map-matched to the real road network. Privacy = Bayesian-adversary error (m, higher = more private).

| Mechanism | Snapshot AE (m) | Trajectory AE (m) | Availability | Loc. Error (m) |
|---|---|---|---|---|
| k-Anonymity | 3125 | 2431 | 77.4% | 2517 |
| Differential Privacy | 767 | 1084 | 100.0% | 453 |
| Graph-Constrained DP | 712 | 1248 | 100.0% | 916 |
| Density-Aware k-Anon | 2077 | 2429 | 71.7% | 2040 |
| DA-Hybrid (ours) | 545 | 924 | 100.0% | 603 |
| MIRAGE (ours) | 715 | 855 | 100.0% | 921 |
| Temporal Cloaking | 3963 | 3694 | 89.9% | 4475 |
