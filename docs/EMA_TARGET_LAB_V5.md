# EMA TARGET LAB V5

> Laboratoire de nouvelles cibles EMA centrees sur la prime europeenne, le basis et la performance relative.

## Verdict

- Cibles testees : 24
- Cibles evaluables : 24
- Cibles prometteuses : 9
- Cibles watchlist : 5
- Meilleure cible : `y_rel_outperform_when_basis_extreme_h90`
- Famille : `conditional_relative`
- Horizon : H90
- AUC : 0.881
- Balanced accuracy : 0.728
- Top20 DA : 0.912
- Lecture : Some non-raw EMA targets are promising; prioritize premium/basis targets before adding more models to raw EMA direction.

## Resultats

| Target | Famille | H | Verdict | n | Base rate | DA | AUC | Bal. acc | MCC | Top20 |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `y_rel_outperform_h20` | relative_direction | 20 | WATCHLIST_TARGET | 2428 | 0.482 | 0.626 | 0.663 | 0.621 | 0.250 | 0.732 |
| `y_rel_large_outperform_h20` | relative_tail | 20 | WATCHLIST_TARGET | 2428 | 0.430 | 0.636 | 0.662 | 0.611 | 0.238 | 0.757 |
| `y_rel_large_underperform_h20` | relative_tail | 20 | WATCHLIST_TARGET | 2428 | 0.458 | 0.604 | 0.658 | 0.613 | 0.229 | 0.703 |
| `y_basis_compress_h20` | basis_reversion | 20 | NO_GO_TARGET | 938 | 0.651 | 0.527 | 0.472 | 0.463 | -0.076 | 0.594 |
| `y_basis_reverts_to_normal_h20` | basis_reversion | 20 | NO_GO_TARGET | 504 | 0.310 | 0.433 | 0.437 | 0.478 | -0.043 | 0.600 |
| `y_basis_widens_h20` | basis_continuation | 20 | NO_GO_TARGET | 938 | 0.192 | 0.608 | 0.454 | 0.412 | -0.163 | 0.786 |
| `y_rel_outperform_after_cbot_weak_h20` | conditional_relative | 20 | NO_GO_TARGET | 1094 | 0.449 | 0.579 | 0.572 | 0.560 | 0.128 | 0.683 |
| `y_rel_outperform_when_basis_extreme_h20` | conditional_relative | 20 | WATCHLIST_TARGET | 553 | 0.439 | 0.626 | 0.717 | 0.604 | 0.223 | 0.791 |
| `y_rel_outperform_h40` | relative_direction | 40 | PROMISING_TARGET | 2408 | 0.511 | 0.640 | 0.708 | 0.642 | 0.292 | 0.771 |
| `y_rel_large_outperform_h40` | relative_tail | 40 | PROMISING_TARGET | 2408 | 0.461 | 0.669 | 0.715 | 0.657 | 0.331 | 0.788 |
| `y_rel_large_underperform_h40` | relative_tail | 40 | PROMISING_TARGET | 2408 | 0.447 | 0.636 | 0.707 | 0.647 | 0.299 | 0.761 |
| `y_basis_compress_h40` | basis_reversion | 40 | NO_GO_TARGET | 935 | 0.738 | 0.496 | 0.458 | 0.490 | -0.017 | 0.663 |
| `y_basis_reverts_to_normal_h40` | basis_reversion | 40 | NO_GO_TARGET | 511 | 0.429 | 0.454 | 0.551 | 0.482 | -0.039 | 0.608 |
| `y_basis_widens_h40` | basis_continuation | 40 | NO_GO_TARGET | 913 | 0.171 | 0.549 | 0.511 | 0.501 | 0.002 | 0.780 |
| `y_rel_outperform_after_cbot_weak_h40` | conditional_relative | 40 | WATCHLIST_TARGET | 1077 | 0.481 | 0.605 | 0.676 | 0.595 | 0.227 | 0.781 |
| `y_rel_outperform_when_basis_extreme_h40` | conditional_relative | 40 | PROMISING_TARGET | 553 | 0.481 | 0.718 | 0.803 | 0.712 | 0.447 | 0.827 |
| `y_rel_outperform_h90` | relative_direction | 90 | PROMISING_TARGET | 2358 | 0.528 | 0.690 | 0.770 | 0.692 | 0.384 | 0.887 |
| `y_rel_large_outperform_h90` | relative_tail | 90 | PROMISING_TARGET | 2358 | 0.495 | 0.695 | 0.781 | 0.695 | 0.391 | 0.907 |
| `y_rel_large_underperform_h90` | relative_tail | 90 | PROMISING_TARGET | 2358 | 0.441 | 0.691 | 0.770 | 0.696 | 0.389 | 0.870 |
| `y_basis_compress_h90` | basis_reversion | 90 | NO_GO_TARGET | 935 | 0.826 | 0.631 | 0.511 | 0.539 | 0.063 | 0.610 |
| `y_basis_reverts_to_normal_h90` | basis_reversion | 90 | NO_GO_TARGET | 553 | 0.689 | 0.550 | 0.476 | 0.471 | -0.059 | 0.709 |
| `y_basis_widens_h90` | basis_continuation | 90 | NO_GO_TARGET | 861 | 0.094 | 0.700 | 0.585 | 0.547 | 0.062 | 0.599 |
| `y_rel_outperform_after_cbot_weak_h90` | conditional_relative | 90 | PROMISING_TARGET | 1043 | 0.456 | 0.646 | 0.788 | 0.629 | 0.283 | 0.947 |
| `y_rel_outperform_when_basis_extreme_h90` | conditional_relative | 90 | PROMISING_TARGET | 510 | 0.396 | 0.769 | 0.881 | 0.728 | 0.511 | 0.912 |

## Familles

| Famille | n | Best AUC | Best bal. acc | Best top20 |
|---|---:|---:|---:|---:|
| basis_continuation | 3 | 0.585 | 0.547 | 0.786 |
| basis_reversion | 6 | 0.551 | 0.539 | 0.709 |
| conditional_relative | 6 | 0.881 | 0.728 | 0.947 |
| relative_direction | 3 | 0.770 | 0.692 | 0.887 |
| relative_tail | 6 | 0.781 | 0.696 | 0.907 |

## Limites

- Source EMA historique exploratoire/proxy.
- Les cibles conditionnelles reduisent parfois fortement l'echantillon.
- Ces resultats ne sont pas des signaux de trading production.