# EMA DIRECTION BENCHMARKS V2

> Cibles EMA intelligentes : basis, relatif EMA/CBOT, résidu EU, volatilité, EMA H40.

## Verdict

- Meilleure cible robuste : relative_ema_outperformance_h40
- AUC daily robuste : 0.708
- Balanced accuracy robuste : 64.2%
- Meilleure cible par DA brute : eu_residual_shock_up_h20 (82.3%)
- Verdict global : GO_SIGNAL

La sélection robuste n'utilise plus la DA seule. Les cibles déséquilibrées comme `ema_vol_high_h20` doivent être rejetées si AUC, balanced accuracy, MCC ou lift vs classe majoritaire sont faibles.

## Résultats daily

| Cible | n | Base rate | Majority | DA | Lift maj. | AUC | Balanced acc. | MCC | q BH |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basis_reversion_h20 | 553 | 66.2% | 66.2% | 51.9% | -14.3% | 0.467 | 43.3% | -0.146 | 0.198 |
| relative_ema_outperformance_h20 | 2428 | 48.2% | 51.8% | 62.6% | 10.7% | 0.663 | 62.1% | 0.250 | 0.000 |
| relative_ema_outperformance_h40 | 2408 | 51.1% | 51.1% | 64.0% | 12.8% | 0.708 | 64.2% | 0.292 | 0.000 |
| eu_residual_shock_up_h20 | 2046 | 2.0% | 98.0% | 82.3% | -15.8% | 0.666 | 54.2% | 0.031 | 0.000 |
| eu_residual_shock_down_h20 | 2046 | 2.3% | 97.7% | 57.6% | -40.1% | 0.525 | 53.4% | 0.020 | 0.000 |
| ema_vol_high_h20 | 2428 | 16.4% | 83.6% | 65.8% | -17.8% | 0.532 | 51.3% | 0.021 | 0.000 |
| ema_direction_absolute_h40 | 2408 | 50.1% | 50.1% | 51.9% | 1.8% | 0.529 | 51.9% | 0.045 | 0.041 |

## Classement robuste

| Rang | Cible | AUC | Balanced acc. | Top20 DA | Weekly AUC | Stabilité annuelle |
|---:|---|---:|---:|---:|---:|---:|
| 1 | relative_ema_outperformance_h40 | 0.708 | 64.2% | 77.1% | 0.728 | 92.3% |
| 2 | eu_residual_shock_up_h20 | 0.666 | 54.2% | 96.3% | 0.557 | 81.8% |
| 3 | relative_ema_outperformance_h20 | 0.663 | 62.1% | 73.2% | 0.663 | 84.6% |
| 4 | ema_vol_high_h20 | 0.532 | 51.3% | 79.6% | 0.518 | 69.2% |
| 5 | ema_direction_absolute_h40 | 0.529 | 51.9% | 58.2% | 0.535 | 38.5% |
| 6 | eu_residual_shock_down_h20 | 0.525 | 53.4% | 72.4% | 0.278 | 54.5% |
| 7 | basis_reversion_h20 | 0.467 | 43.3% | 62.7% | 0.174 | 54.5% |