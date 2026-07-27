# Adversary-Grounded Privacy Evaluation

Privacy = expected error (metres) of an optimal Bayesian adversary (Shokri et al., IEEE S&P 2011). Higher error = stronger privacy. Each mechanism is attacked by a single-observation **snapshot** adversary and a Viterbi **trajectory** adversary using a Markov mobility prior.

| Mechanism | Snapshot AE (m) | Snapshot re-id | Trajectory AE (m) | Trajectory re-id |
|-----------|:---------------:|:--------------:|:-----------------:|:----------------:|
| k-Anonymity | 5193 | 38.0% | 5141 | 19.7% |
| Differential Privacy | 1651 | 21.5% | 1893 | 21.5% |
| Graph-Constrained DP | 1829 | 16.6% | 1915 | 22.1% |
| Density-Aware k-Anon | 4256 | 48.3% | 5563 | 23.5% |
| Temporal Cloaking | 6376 | 28.1% | 5037 | 41.2% |
| DA-Hybrid (ours) | 1441 | 38.0% | 1707 | 26.0% |
