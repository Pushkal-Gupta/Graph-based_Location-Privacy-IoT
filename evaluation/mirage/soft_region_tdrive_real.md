# Soft-region MIRAGE: trajectory membership-leak fix (tdrive_real)

Filtering trajectory-adversary tracking error (m) at matched distortion. Soft = mixture of two overlapping partitions so a release does not reveal a hard region.

| Dmax | hard-MIRAGE priv/util | soft-MIRAGE priv/util | soft gain |
|---|---|---|---|
| 300 | 244/277 | 251/273 | +3% |
| 500 | 390/466 | 416/481 | +7% |
| 800 | 567/799 | 577/791 | +2% |
| 1200 | 648/1099 | 645/1107 | -0% |

At util~791m: hard=563, soft=577, DP=635.
