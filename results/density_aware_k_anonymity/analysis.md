# Density-Aware Adaptive k-Anonymity — GeoLife Dataset

## Metrics per Time Window

| Δt | Avg Error (m) | Median (m) | P95 (m) | Avg Region | Avg k | k-Sat | Density Dist |
|----|---------------|------------|---------|------------|-------|-------|-------------|
| 1 min | 3205.5 | 0.0 | 15452.1 | 341.0 | 3.1 | 68% | S:15 M:294 D:579 |
| 5 min | 2669.4 | 0.0 | 13416.3 | 306.0 | 3.0 | 72% | S:9 M:293 D:642 |
| 10 min | 2545.6 | 0.0 | 13431.3 | 281.7 | 2.9 | 75% | S:15 M:291 D:713 |
| 20 min | 2452.1 | 0.0 | 13196.2 | 269.0 | 2.9 | 77% | S:22 M:296 D:767 |

## Best Configuration

- **Δt** = 20 min
- Avg error: 2452.1 m
- Avg adaptive k: 2.9
