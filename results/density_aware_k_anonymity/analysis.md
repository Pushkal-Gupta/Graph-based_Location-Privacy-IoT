# Density-Aware Adaptive k-Anonymity — GeoLife Dataset

## Metrics per Time Window

| Δt | Avg Error (m) | Median (m) | P95 (m) | Avg Region | Avg k | k-Sat | Density Dist |
|----|---------------|------------|---------|------------|-------|-------|-------------|
| 1 min | 3233.4 | 0.0 | 14746.5 | 341.0 | 3.1 | 68% | S:15 M:294 D:579 |
| 5 min | 2714.6 | 0.0 | 13453.4 | 304.7 | 3.0 | 72% | S:10 M:291 D:644 |
| 10 min | 2427.3 | 0.0 | 11965.5 | 263.2 | 2.9 | 78% | S:10 M:286 D:739 |
| 20 min | 2497.8 | 0.0 | 13388.3 | 269.0 | 2.9 | 77% | S:22 M:296 D:767 |

## Best Configuration

- **Δt** = 10 min
- Avg error: 2427.3 m
- Avg adaptive k: 2.9
