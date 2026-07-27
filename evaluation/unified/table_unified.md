# Unified Comparison (adversary-grounded privacy)

Privacy is the expected error of an optimal Bayesian adversary (metres, higher=better) under snapshot and trajectory threat models. Representative configs at window=10 min.

| Mechanism | Snapshot AE (m) | Trajectory AE (m) | Availability | Loc. Error (m) | On-graph | E LoRa (mJ) | E BLE (mJ) |
|---|---|---|---|---|---|---|---|
| k-Anonymity | 5193 | 5141 | 74.5% | 1189 | yes | 5.57 | 0.62 |
| Differential Privacy | 1651 | 1893 | 100.0% | 1569 | no | 5.05 | 0.10 |
| Graph-Constrained DP | 1829 | 1915 | 100.0% | 1890 | yes | 5.16 | 0.21 |
| Density-Aware k-Anon | 4256 | 5563 | 78.2% | 2427 | yes | 5.78 | 0.83 |
| Temporal Cloaking | 6376 | 5037 | 18.5% | 5758 | yes | 5.05 | 0.10 |
| DA-Hybrid (ours) | 1441 | 1707 | 100.0% | 1117 | yes | 5.10 | 0.15 |
