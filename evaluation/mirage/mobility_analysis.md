# Why the price of heuristics varies across cities

MIRAGE exploits the prior; heuristics do not. The gain tracks local prior heterogeneity: lower within-region prior entropy (more skewed occupancy) => more structure for the optimal mechanism => larger gap.

| City | Nodes | Prior entropy (norm) | Within-region entropy | Mobility cond. entropy | Self-transition | MIRAGE gain |
|---|---|---|---|---|---|---|
| GeoLife | 3154 | 0.803 | 0.788 | 0.302 | 0.73 | 20% |
| T-Drive | 3154 | 0.894 | 0.835 | 0.754 | 0.23 | 15% |
| Porto | 3455 | 0.744 | 0.867 | 0.190 | 0.61 | 10% |

**Reading.** Datasets with lower within-region prior entropy (more concentrated occupancy) show a larger optimal-vs-heuristic gap, confirming that MIRAGE's advantage comes from exploiting prior structure the heuristics ignore.
