# Cross-Algorithm Evaluation Report

## Representative Configuration Comparison

| Algorithm | Avg Error (m) | Median (m) | P95 (m) | Temporal Jump (m) | Config |
|-----------|---------------|------------|---------|-------------------|--------|
| k-Anonymity | 1189.1 | 0.0 | 6747.4 | 6150.4 | 10 min |
| Differential Privacy | 1544.8 | 1296.8 | 3567.6 | 6589.7 | 10 min |
| Graph-Constrained DP | 1842.7 | 1705.5 | 4454.5 | 8464.9 | 10 min |
| Density-Aware k-Anon | 2545.6 | 0.0 | 13431.3 | 6453.3 | 10 min |
| Temporal Cloaking | 5757.7 | 3927.1 | 16126.6 | 2865.6 | 10 min |

## Ranking by Avg Location Error (lower = better utility)

1. **k-Anonymity** — 1189.1 m
2. **Differential Privacy** — 1544.8 m
3. **Graph-Constrained DP** — 1842.7 m
4. **Density-Aware k-Anon** — 2545.6 m
5. **Temporal Cloaking** — 5757.7 m

## Key Findings

- **Lowest error**: k-Anonymity (1189.1 m)
- **Highest error**: Temporal Cloaking (5757.7 m)
- Total configurations evaluated: 68
