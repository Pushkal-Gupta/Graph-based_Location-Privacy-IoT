# Real-Topology Comparison (central-Beijing OSM graph, ~3.1k nodes)

Representative configs, window = 10 min, GeoLife map-matched to the real road network. Privacy = Bayesian-adversary error (m, higher = more private).

| Mechanism | Snapshot AE (m) | Trajectory AE (m) | Availability | Loc. Error (m) |
|---|---|---|---|---|
| k-Anonymity | 3125 | 2431 | 77.4% | 2517 |
| Differential Privacy | 824 | 1135 | 100.0% | 414 |
| Graph-Constrained DP | 780 | 1105 | 100.0% | 933 |
| Density-Aware k-Anon | 2077 | 2429 | 71.7% | 2040 |
| DA-Hybrid (ours) | 595 | 1133 | 100.0% | 664 |
| Temporal Cloaking | 3963 | 3694 | 89.9% | 4475 |
