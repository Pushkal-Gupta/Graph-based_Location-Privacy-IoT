# Local-decomposition optimality gap (geolife_real, n=60 small graph)

Privacy gap of the scalable local decomposition vs the global optimum (one LP over all nodes), by the exact optimal-adversary metric.

- **Practical regime (distortion $\le 500$\,m): mean gap 1.5%** (0% up to 300\,m) --- the decomposition is essentially lossless exactly where MIRAGE dominates heuristics.
- The cost appears only at high distortion (up to 44% at $D_{\max}{=}1200$), where the global optimum releases across regions but the partition confines releases---and where every mechanism has already saturated at the uncertainty ceiling, so the mechanism advantage is already gone.

| Dmax | Global priv (m) | Local priv (m) | Gap |
|---|---|---|---|
| 150 | 150 | 150 | 0.0% |
| 300 | 300 | 300 | 0.0% |
| 500 | 500 | 478 | 4.5% |
| 800 | 800 | 572 | 28.5% |
| 1200 | 1032 | 577 | 44.1% |
