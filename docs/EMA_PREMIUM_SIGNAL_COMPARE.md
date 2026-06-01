# EMA PREMIUM SIGNAL COMPARE

> Comparaison du modele ML, de la regle basis z-score et de signaux combines.

## Verdict

- H40 meilleure strategie : `ml_with_basis_extreme_filter`
- H40 balanced accuracy : 0.761
- H90 meilleure strategie : `combined_top40_confidence`
- H90 balanced accuracy : 0.844
- Lecture : Le signal combine apporte le meilleur compromis ; utiliser ML + basis plutot que ML seul.

## H40

| Strategie | Coverage | n | DA | AUC | Balanced acc. | Top20 DA |
|---|---:|---:|---:|---:|---:|---:|
| ml_model | 1.000 | 2408 | 0.640 | 0.708 | 0.642 | 0.771 |
| basis_zscore_rule | 1.000 | 2408 | 0.642 | 0.676 | 0.644 | 0.751 |
| combined_equal_weight | 1.000 | 2408 | 0.645 | 0.704 | 0.647 | 0.780 |
| ml_with_basis_extreme_filter | 0.231 | 556 | 0.768 | 0.789 | 0.761 | 0.874 |
| combined_top40_confidence | 0.400 | 963 | 0.738 | 0.772 | 0.730 | 0.828 |

## H90

| Strategie | Coverage | n | DA | AUC | Balanced acc. | Top20 DA |
|---|---:|---:|---:|---:|---:|---:|
| ml_model | 1.000 | 2358 | 0.690 | 0.770 | 0.692 | 0.887 |
| basis_zscore_rule | 1.000 | 2358 | 0.673 | 0.757 | 0.677 | 0.919 |
| combined_equal_weight | 1.000 | 2358 | 0.687 | 0.787 | 0.689 | 0.913 |
| ml_with_basis_extreme_filter | 0.236 | 556 | 0.842 | 0.892 | 0.827 | 0.892 |
| combined_top40_confidence | 0.400 | 943 | 0.855 | 0.884 | 0.844 | 0.931 |
