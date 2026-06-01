# CROSS TARGET OOF V6

> Predictions OOF de cibles auxiliaires EMA/CBOT, transformees en meta-features.

- Prediction rows : 14910
- Meta rows : 804
- Series OOF : 26
- Meta columns : 35
- Best OOF : `y_rel_outperform_when_basis_extreme_h90` / `logistic` AUC 1.0

## Metrics

| Market | Target | Model | n | AUC | DA | BA |
|---|---|---|---:|---:|---:|---:|
| cbot | `y_cbot_drawdown_5pct_h20` | histgb | 641 | 0.660 | 0.727 | 0.640 |
| cbot | `y_cbot_drawdown_5pct_h20` | logistic | 641 | 0.714 | 0.688 | 0.665 |
| cbot | `y_cbot_drawdown_5pct_h60` | histgb | 563 | 0.656 | 0.654 | 0.624 |
| cbot | `y_cbot_drawdown_5pct_h60` | logistic | 563 | 0.754 | 0.689 | 0.694 |
| cbot | `y_cbot_large_down_3pct_h90` | histgb | 590 | 0.724 | 0.714 | 0.657 |
| cbot | `y_cbot_large_down_3pct_h90` | logistic | 590 | 0.711 | 0.659 | 0.639 |
| cbot | `y_cbot_rally_5pct_h40` | histgb | 548 | 0.680 | 0.712 | 0.574 |
| cbot | `y_cbot_rally_5pct_h40` | logistic | 548 | 0.716 | 0.617 | 0.651 |
| cbot | `y_cbot_up_h20` | histgb | 641 | 0.675 | 0.652 | 0.652 |
| cbot | `y_cbot_up_h20` | logistic | 641 | 0.676 | 0.665 | 0.661 |
| cbot | `y_cbot_up_h60` | histgb | 563 | 0.707 | 0.632 | 0.623 |
| cbot | `y_cbot_up_h60` | logistic | 563 | 0.725 | 0.643 | 0.635 |
| ema | `y_rel_large_outperform_h90` | histgb | 763 | 0.827 | 0.818 | 0.755 |
| ema | `y_rel_large_outperform_h90` | logistic | 763 | 0.806 | 0.768 | 0.745 |
| ema | `y_rel_large_underperform_h90` | histgb | 763 | 0.795 | 0.777 | 0.747 |
| ema | `y_rel_large_underperform_h90` | logistic | 763 | 0.787 | 0.725 | 0.712 |
| ema | `y_rel_outperform_h120` | histgb | 763 | 0.875 | 0.831 | 0.782 |
| ema | `y_rel_outperform_h120` | logistic | 763 | 0.883 | 0.793 | 0.793 |
| ema | `y_rel_outperform_h40` | histgb | 763 | 0.748 | 0.727 | 0.705 |
| ema | `y_rel_outperform_h40` | logistic | 763 | 0.808 | 0.717 | 0.701 |
| ema | `y_rel_outperform_h90` | histgb | 763 | 0.783 | 0.803 | 0.756 |
| ema | `y_rel_outperform_h90` | logistic | 763 | 0.790 | 0.733 | 0.718 |
| ema | `y_rel_outperform_when_basis_extreme_h40` | histgb | 65 | 0.846 | 0.892 | 0.708 |
| ema | `y_rel_outperform_when_basis_extreme_h40` | logistic | 65 | 0.925 | 0.923 | 0.792 |
| ema | `y_rel_outperform_when_basis_extreme_h90` | histgb | 29 | 0.942 | 0.897 | 0.750 |
| ema | `y_rel_outperform_when_basis_extreme_h90` | logistic | 29 | 1.000 | 1.000 | 1.000 |