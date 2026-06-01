# EMA SMART BASELINES

> Comparaison du modèle EMA aux règles simples.

## Verdict

- Target robuste : relative_ema_outperformance_h40
- Balanced accuracy modèle : 0.642
- Meilleure baseline : basis_z_rule (0.644)
- Modèle bat meilleure baseline : False

## relative_ema_outperformance_h40

| Baseline | n | DA | Balanced acc. | Lift majority |
|---|---:|---:|---:|---:|
| walk_forward_majority | 2408 | 0.511 | 0.500 | 0.000 |
| ema_momentum_20d | 2408 | 0.492 | 0.493 | -0.019 |
| cbot_momentum_20d | 2408 | 0.540 | 0.540 | 0.029 |
| basis_z_rule | 2408 | 0.642 | 0.644 | 0.131 |
| seasonal_month_rule | 2408 | 0.621 | 0.619 | 0.110 |
| random_50_50 | 2408 | 0.494 | 0.494 | -0.017 |
| model_reference | 2408 | 0.640 | 0.642 | N/A |

## ema_direction_absolute_h40

| Baseline | n | DA | Balanced acc. | Lift majority |
|---|---:|---:|---:|---:|
| walk_forward_majority | 2408 | 0.501 | 0.500 | 0.000 |
| ema_momentum_20d | 2408 | 0.473 | 0.473 | -0.027 |
| cbot_momentum_20d | 2408 | 0.534 | 0.534 | 0.033 |
| basis_z_rule | 2408 | 0.526 | 0.526 | 0.025 |
| seasonal_month_rule | 2408 | 0.517 | 0.517 | 0.017 |
| random_50_50 | 2408 | 0.500 | 0.500 | -0.000 |
| model_reference | 2408 | 0.519 | 0.519 | N/A |
