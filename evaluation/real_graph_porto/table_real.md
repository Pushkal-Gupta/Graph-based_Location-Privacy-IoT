# Real-Topology Comparison (Porto, central-Beijing OSM graph, ~3.1k nodes)

Representative configs, window = 10 min, Porto map-matched to the real road network. Privacy = Bayesian-adversary error (m, higher = more private).

| Mechanism | Snapshot AE (m) | Trajectory AE (m) | Availability | Loc. Error (m) |
|---|---|---|---|---|
| k-Anonymity | 1139 | 3158 | 100.0% | 624 |
| Differential Privacy | 803 | 2082 | 100.0% | 490 |
| Graph-Constrained DP | 838 | 1518 | 100.0% | 1016 |
| Density-Aware k-Anon | 1122 | 3074 | 100.0% | 589 |
| DA-Hybrid (ours) | 582 | 2909 | 100.0% | 405 |
| MIRAGE (ours) | 699 | 1904 | 100.0% | 798 |
| Temporal Cloaking | 3799 | 4877 | 100.0% | 4100 |
