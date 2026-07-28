# Cross-Topology / Cross-Dataset Comparison

Location error (m) and availability across settings. Shows whether rankings hold when moving from the grid abstraction to a real road network, and from GeoLife to T-Drive.

| Mechanism | GeoLife / grid err / avail | GeoLife / real err / avail | T-Drive / real err / avail |
|---|---|---|---|
| k-Anonymity | 1189 / 74% | 2517 / 77% | 107 / 100% |
| Differential Privacy | 1568 / 100% | 453 / 100% | 455 / 100% |
| Graph-Constrained DP | 1890 / 100% | 916 / 100% | 812 / 100% |
| Density-Aware k-Anon | 2427 / 78% | 2040 / 72% | 128 / 100% |
| Temporal Cloaking | 5758 / 19% | 4475 / 90% | 6460 / 100% |
| DA-Hybrid (ours) | 1118 / 100% | 603 / 100% | 62 / 100% |
| MIRAGE (ours) | — | 921 / 100% | 798 / 100% |
