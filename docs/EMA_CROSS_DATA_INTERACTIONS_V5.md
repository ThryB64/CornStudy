# EMA CROSS DATA INTERACTIONS V5

> Test OOF des croisements basis x marche, saison, meteo EU et WASDE quand les colonnes existent.

## Verdict

- Meilleur overall : `y_rel_outperform_when_basis_extreme_h90` / `all_cross`
- AUC overall : 0.906
- Balanced accuracy overall : 0.756
- Meilleur delta : `y_rel_outperform_h40` / `base_plus_season_cross`
- Delta AUC vs base : 0.029
- Delta balanced accuracy vs base : 0.007
- Lecture : Cross-data interactions add meaningful OOF value for at least one premium target.

## Feature sets

- `base` : 7 features
- `base_plus_market_cross` : 12 features
- `base_plus_season_cross` : 11 features
- `base_plus_eu_cross` : 7 features
- `all_cross` : 16 features

## Resultats

| Target | H | Set | n | AUC | dAUC | Bal. acc | dBal | Top20 |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| `y_rel_outperform_h40` | 40 | `base` | 2409 | 0.708 | 0.000 | 0.642 | 0.000 | 0.771 |
| `y_rel_outperform_h40` | 40 | `base_plus_market_cross` | 2409 | 0.683 | -0.025 | 0.617 | -0.025 | 0.761 |
| `y_rel_outperform_h40` | 40 | `base_plus_season_cross` | 2409 | 0.736 | 0.029 | 0.649 | 0.007 | 0.848 |
| `y_rel_outperform_h40` | 40 | `base_plus_eu_cross` | 2409 | 0.708 | 0.000 | 0.642 | 0.000 | 0.771 |
| `y_rel_outperform_h40` | 40 | `all_cross` | 2409 | 0.716 | 0.008 | 0.637 | -0.005 | 0.827 |
| `y_rel_outperform_when_basis_extreme_h40` | 40 | `base` | 553 | 0.803 | 0.000 | 0.712 | 0.000 | 0.827 |
| `y_rel_outperform_when_basis_extreme_h40` | 40 | `base_plus_market_cross` | 553 | 0.785 | -0.017 | 0.696 | -0.016 | 0.791 |
| `y_rel_outperform_when_basis_extreme_h40` | 40 | `base_plus_season_cross` | 553 | 0.776 | -0.027 | 0.728 | 0.016 | 0.782 |
| `y_rel_outperform_when_basis_extreme_h40` | 40 | `base_plus_eu_cross` | 553 | 0.803 | 0.000 | 0.712 | 0.000 | 0.827 |
| `y_rel_outperform_when_basis_extreme_h40` | 40 | `all_cross` | 553 | 0.755 | -0.048 | 0.739 | 0.027 | 0.864 |
| `y_rel_large_outperform_h40` | 40 | `base` | 2409 | 0.715 | 0.000 | 0.657 | 0.000 | 0.788 |
| `y_rel_large_outperform_h40` | 40 | `base_plus_market_cross` | 2409 | 0.683 | -0.032 | 0.621 | -0.036 | 0.773 |
| `y_rel_large_outperform_h40` | 40 | `base_plus_season_cross` | 2409 | 0.740 | 0.025 | 0.657 | 0.000 | 0.844 |
| `y_rel_large_outperform_h40` | 40 | `base_plus_eu_cross` | 2409 | 0.715 | 0.000 | 0.657 | 0.000 | 0.788 |
| `y_rel_large_outperform_h40` | 40 | `all_cross` | 2409 | 0.720 | 0.005 | 0.627 | -0.030 | 0.838 |
| `y_rel_large_underperform_h40` | 40 | `base` | 2409 | 0.707 | 0.000 | 0.647 | 0.000 | 0.761 |
| `y_rel_large_underperform_h40` | 40 | `base_plus_market_cross` | 2409 | 0.688 | -0.019 | 0.622 | -0.026 | 0.740 |
| `y_rel_large_underperform_h40` | 40 | `base_plus_season_cross` | 2409 | 0.733 | 0.026 | 0.647 | -0.000 | 0.852 |
| `y_rel_large_underperform_h40` | 40 | `base_plus_eu_cross` | 2409 | 0.707 | 0.000 | 0.647 | 0.000 | 0.761 |
| `y_rel_large_underperform_h40` | 40 | `all_cross` | 2409 | 0.713 | 0.006 | 0.633 | -0.014 | 0.821 |
| `y_rel_outperform_h90` | 90 | `base` | 2359 | 0.770 | 0.000 | 0.692 | 0.000 | 0.887 |
| `y_rel_outperform_h90` | 90 | `base_plus_market_cross` | 2359 | 0.757 | -0.013 | 0.676 | -0.016 | 0.839 |
| `y_rel_outperform_h90` | 90 | `base_plus_season_cross` | 2359 | 0.778 | 0.009 | 0.695 | 0.003 | 0.941 |
| `y_rel_outperform_h90` | 90 | `base_plus_eu_cross` | 2359 | 0.770 | 0.000 | 0.692 | 0.000 | 0.887 |
| `y_rel_outperform_h90` | 90 | `all_cross` | 2359 | 0.761 | -0.009 | 0.687 | -0.004 | 0.881 |
| `y_rel_outperform_when_basis_extreme_h90` | 90 | `base` | 510 | 0.881 | 0.000 | 0.728 | 0.000 | 0.912 |
| `y_rel_outperform_when_basis_extreme_h90` | 90 | `base_plus_market_cross` | 510 | 0.903 | 0.022 | 0.788 | 0.060 | 0.980 |
| `y_rel_outperform_when_basis_extreme_h90` | 90 | `base_plus_season_cross` | 510 | 0.845 | -0.036 | 0.752 | 0.024 | 0.931 |
| `y_rel_outperform_when_basis_extreme_h90` | 90 | `base_plus_eu_cross` | 510 | 0.881 | 0.000 | 0.728 | 0.000 | 0.912 |
| `y_rel_outperform_when_basis_extreme_h90` | 90 | `all_cross` | 510 | 0.906 | 0.025 | 0.756 | 0.029 | 0.873 |
| `y_rel_large_outperform_h90` | 90 | `base` | 2359 | 0.781 | 0.000 | 0.694 | 0.000 | 0.907 |
| `y_rel_large_outperform_h90` | 90 | `base_plus_market_cross` | 2359 | 0.764 | -0.017 | 0.672 | -0.022 | 0.847 |
| `y_rel_large_outperform_h90` | 90 | `base_plus_season_cross` | 2359 | 0.788 | 0.007 | 0.711 | 0.017 | 0.960 |
| `y_rel_large_outperform_h90` | 90 | `base_plus_eu_cross` | 2359 | 0.781 | 0.000 | 0.694 | 0.000 | 0.907 |
| `y_rel_large_outperform_h90` | 90 | `all_cross` | 2359 | 0.768 | -0.013 | 0.691 | -0.003 | 0.877 |
| `y_rel_large_underperform_h90` | 90 | `base` | 2359 | 0.769 | 0.000 | 0.695 | 0.000 | 0.870 |
| `y_rel_large_underperform_h90` | 90 | `base_plus_market_cross` | 2359 | 0.756 | -0.013 | 0.685 | -0.011 | 0.826 |
| `y_rel_large_underperform_h90` | 90 | `base_plus_season_cross` | 2359 | 0.771 | 0.002 | 0.690 | -0.006 | 0.938 |
| `y_rel_large_underperform_h90` | 90 | `base_plus_eu_cross` | 2359 | 0.769 | 0.000 | 0.695 | 0.000 | 0.870 |
| `y_rel_large_underperform_h90` | 90 | `all_cross` | 2359 | 0.755 | -0.014 | 0.687 | -0.009 | 0.879 |

## Limites

- Source EMA proxy.
- Les croisements sont des hypotheses economiques, pas des preuves causales.
- Les colonnes EU/WASDE ne sont utilisees que si elles existent dans le master features.