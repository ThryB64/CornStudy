# EMA RELATIVE FEATURE IMPORTANCE

> Importance OOF sur `relative_ema_outperformance_h40/h90`.

## Verdict

- H40 top feature : `ema_cbot_basis`
- H40 top family : `basis`
- H90 top feature : `ema_cbot_basis`
- H90 top family : `basis`
- Lecture : Le basis reste le driver le plus robuste de la performance relative EMA/CBOT.

## H40

- Baseline AUC : 0.708
- Baseline balanced accuracy : 0.642

| Feature | Δ AUC permutation | Δ balanced acc. |
|---|---:|---:|
| ema_cbot_basis | 0.278 | 0.195 |
| fedfunds_level_zscore | 0.003 | -0.001 |
| ema_front_vol_20d_adjusted | -0.001 | -0.004 |
| corn_logret_20d | -0.001 | -0.002 |
| corn_realized_vol_20 | -0.003 | 0.000 |
| ema_cbot_basis_zscore_52w | -0.015 | -0.015 |
| corn_gas_ratio | -0.020 | -0.024 |

| Famille retirée | Δ AUC ablation | Δ balanced acc. |
|---|---:|---:|
| basis | 0.194 | 0.132 |
| ema_technical | 0.004 | 0.000 |
| cbot_technical | -0.005 | -0.000 |
| macro_energy | -0.051 | -0.038 |

## H90

- Baseline AUC : 0.770
- Baseline balanced accuracy : 0.692

| Feature | Δ AUC permutation | Δ balanced acc. |
|---|---:|---:|
| ema_cbot_basis | 0.317 | 0.230 |
| fedfunds_level_zscore | 0.002 | -0.001 |
| corn_logret_20d | 0.001 | -0.002 |
| ema_front_vol_20d_adjusted | 0.000 | 0.003 |
| corn_realized_vol_20 | -0.002 | 0.000 |
| ema_cbot_basis_zscore_52w | -0.014 | -0.009 |
| corn_gas_ratio | -0.032 | -0.034 |

| Famille retirée | Δ AUC ablation | Δ balanced acc. |
|---|---:|---:|
| basis | 0.256 | 0.181 |
| ema_technical | 0.001 | 0.002 |
| cbot_technical | -0.007 | -0.002 |
| macro_energy | -0.053 | -0.028 |
