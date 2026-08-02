# Prior-misspecification robustness (geolife_real)

MIRAGE solves with a corrupted prior (alpha = ignorance; 1 = uniform), adversary attacks with the true prior. Privacy (optimal-adversary error, m).

## $D_{\max}=300$\,m

| $\alpha$ | MIRAGE priv | best heuristic | MIRAGE still wins? |
|---|---|---|---|
| 0.0 | 300 | 254 | yes |
| 0.25 | 227 | 231 | no |
| 0.5 | 183 | 219 | no |
| 0.75 | 149 | 222 | no |
| 1.0 | 137 | 227 | no |

## $D_{\max}=500$\,m

| $\alpha$ | MIRAGE priv | best heuristic | MIRAGE still wins? |
|---|---|---|---|
| 0.0 | 488 | 400 | yes |
| 0.25 | 404 | 381 | yes |
| 0.5 | 322 | 366 | no |
| 0.75 | 274 | 355 | no |
| 1.0 | 244 | 365 | no |

