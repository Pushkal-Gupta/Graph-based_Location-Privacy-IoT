# Real-Topology Comparison (T-Drive, central-Beijing OSM graph, ~3.1k nodes)

Representative configs, window = 10 min, T-Drive map-matched to the real road network. Privacy = Bayesian-adversary error (m, higher = more private).

| Mechanism | Snapshot AE (m) | Trajectory AE (m) | Availability | Loc. Error (m) |
|---|---|---|---|---|
| k-Anonymity | 236 | 580 | 100.0% | 107 |
| Differential Privacy | 660 | 408 | 100.0% | 454 |
| Graph-Constrained DP | 691 | 431 | 100.0% | 809 |
| Density-Aware k-Anon | 274 | 556 | 100.0% | 128 |
| DA-Hybrid (ours) | 135 | 1154 | 100.0% | 62 |
| Temporal Cloaking | 6178 | 8388 | 100.0% | 6460 |
