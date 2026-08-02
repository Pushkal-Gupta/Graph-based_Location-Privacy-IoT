# Soft-region MIRAGE: trajectory membership-leak fix (geolife_real)

Filtering trajectory-adversary tracking error (m) at matched distortion. Soft = mixture of two overlapping partitions so a release does not reveal a hard region.

| Dmax | hard-MIRAGE priv/util | soft-MIRAGE priv/util | soft gain |
|---|---|---|---|
| 300 | 272/343 | 250/328 | -8% |
| 500 | 402/500 | 379/520 | -6% |
| 800 | 556/765 | 527/818 | -5% |
| 1200 | 612/1146 | 596/1187 | -3% |

At util~818m: hard=564, soft=527, DP=669.
