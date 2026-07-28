# MIRAGE ablation (geolife_real)

## Region size C (scalability vs quality)

| C | #regions | Dmax=300 priv | Dmax=800 priv | Dmax=1500 priv | LP time (s, all regions) |
|---|---|---|---|---|---|
| 12 | 263 | 287 | 421 | 441 | 1.3 |
| 20 | 158 | 300 | 551 | 600 | 3.1 |
| 28 | 113 | 300 | 632 | 706 | 7.0 |
| 40 | 79 | 300 | 715 | 804 | 20.8 |

## Geo-indistinguishability (metric-DP) constraint (C=28)

| Variant | Dmax=300 priv/util | Dmax=800 priv/util |
|---|---|---|
| MIRAGE (no DP constraint) | 300/300 | 632/798 |
| MIRAGE + geo-ind eps/m=0.01 | 225/225 | 456/602 |
| MIRAGE + geo-ind eps/m=0.003 | 196/196 | 631/798 |

**Reading:** larger C raises privacy (more room to hide) but costs LP time ~ O(C^3) per region; C=28 is a good knee. Adding a geo-ind constraint trades a little optimality for a formal DP guarantee — MIRAGE subsumes DP as the constrained special case.
