# EMA Price CQR Study

> EMA historical prices are exploratory Barchart-derived data, not official Euronext settlement.

## Verdict

- `CQR_PRICE_NO_GO`: No model reached the minimum acceptable 88% empirical coverage.

## Résultats

| Horizon | Modèle | Coverage | Width mean | Winkler | MAE midpoint | N |
|---|---|---:|---:|---:|---:|---:|
| h20 | naive_current | 35.2% | 201.288 | 408.278 | 94.661 | 1575 |
| h20 | seasonal_naive_1y | 72.6% | 72.563 | 251.938 | 29.051 | 1575 |
| h20 | cbot_converted | 79.2% | 112.073 | 160.205 | 42.435 | 1531 |
| h20 | ridge_selected | 60.9% | 104.125 | 386.661 | 47.422 | 1575 |
| h20 | histgb_selected | 70.0% | 58.875 | 281.305 | 29.969 | 1575 |
| h20 | cqr_quantile_selected | 75.0% | 64.667 | 235.560 | 28.934 | 1575 |
| h60 | naive_current | 43.4% | 213.975 | 454.232 | 97.547 | 1575 |
| h60 | seasonal_naive_1y | 73.3% | 79.898 | 223.806 | 29.287 | 1575 |
| h60 | cbot_converted | 80.4% | 127.528 | 199.763 | 45.428 | 1531 |
| h60 | ridge_selected | 54.0% | 142.053 | 598.178 | 74.015 | 1575 |
| h60 | histgb_selected | 59.3% | 87.313 | 345.803 | 41.141 | 1575 |
| h60 | cqr_quantile_selected | 73.0% | 73.123 | 309.625 | 36.101 | 1575 |

## Lecture

- Le prix cible est le prix EMA futur brut, afin de produire une fourchette exploitable métier.
- Les baselines sont conformalisées avec les résidus de calibration walk-forward.
- `coverage` mesure la proportion de prix futurs contenus dans l'intervalle.
- `Width mean` mesure la netteté : plus c'est bas, plus l'intervalle est exploitable.
- `Winkler` pénalise à la fois les intervalles trop larges et les prix hors intervalle.
