# CBOT CROSS MARKET V6

> Études CBOT, croisement EMA/CBOT, décomposition EMA et event study premium.

- Source quality : `exploratoire_barchart_proxy_for_ema_cross_market`
- Lecture : EMA premium signals add value to selected CBOT risk targets; EMA still needs proxy caveats.

## CBOT Cross-Market

| Target | Set | n | AUC | dAUC | BA | MCC |
|---|---|---:|---:|---:|---:|---:|
| `y_cbot_up_h60` | `cbot_base` | 2463 | 0.518 | 0.000 | 0.498 | -0.004 |
| `y_cbot_up_h60` | `cbot_plus_ema_premium` | 2463 | 0.568 | 0.050 | 0.544 | 0.088 |
| `y_cbot_up_h60` | `cbot_plus_ema_meta` | 2463 | 0.536 | 0.018 | 0.515 | 0.030 |
| `y_cbot_up_h60` | `cbot_full_cross_market` | 2463 | 0.577 | 0.059 | 0.546 | 0.092 |
| `y_cbot_drawdown_5pct_h20` | `cbot_base` | 2477 | 0.513 | 0.000 | 0.529 | 0.051 |
| `y_cbot_drawdown_5pct_h20` | `cbot_plus_ema_premium` | 2477 | 0.567 | 0.054 | 0.575 | 0.132 |
| `y_cbot_drawdown_5pct_h20` | `cbot_plus_ema_meta` | 2477 | 0.511 | -0.001 | 0.529 | 0.051 |
| `y_cbot_drawdown_5pct_h20` | `cbot_full_cross_market` | 2477 | 0.560 | 0.047 | 0.570 | 0.122 |
| `y_cbot_large_down_3pct_h90` | `cbot_base` | 2435 | 0.580 | 0.000 | 0.550 | 0.105 |
| `y_cbot_large_down_3pct_h90` | `cbot_plus_ema_premium` | 2435 | 0.636 | 0.056 | 0.606 | 0.221 |
| `y_cbot_large_down_3pct_h90` | `cbot_plus_ema_meta` | 2435 | 0.579 | -0.001 | 0.540 | 0.087 |
| `y_cbot_large_down_3pct_h90` | `cbot_full_cross_market` | 2435 | 0.633 | 0.053 | 0.604 | 0.218 |

## EMA Impact Of CBOT Meta

| Target | Set | n | AUC | dAUC | BA |
|---|---|---:|---:|---:|---:|
| `y_rel_outperform_h40` | `ema_base` | 503 | 0.839 | 0.000 | 0.758 |
| `y_rel_outperform_h40` | `ema_plus_cbot_meta` | 503 | 0.822 | -0.017 | 0.747 |
| `y_rel_outperform_h90` | `ema_base` | 503 | 0.949 | 0.000 | 0.864 |
| `y_rel_outperform_h90` | `ema_plus_cbot_meta` | 503 | 0.925 | -0.024 | 0.850 |

## Decomposition

- `h40_all` : status=OK, n=769, r2=0.888223225483652
- `h40_normal` : status=OK, n=513, r2=0.8131488385281541
- `h40_crisis` : status=OK, n=256, r2=0.9656030953187591
- `h90_all` : status=OK, n=769, r2=0.9613296120681625
- `h90_normal` : status=OK, n=513, r2=0.8682128526384891
- `h90_crisis` : status=OK, n=256, r2=0.9901345827168534

## Event Study

| Event | H | n | Mean rel ret | Outperform rate |
|---|---:|---:|---:|---:|
| `wasde_day` | 40 | 24 | -0.0213 | 0.458 |
| `wasde_day` | 90 | 24 | -0.0523 | 0.417 |
| `basis_extreme_abs_z2` | 40 | 112 | -0.0480 | 0.286 |
| `basis_extreme_abs_z2` | 90 | 112 | -0.1153 | 0.188 |
| `cbot_vol_top_decile` | 40 | 79 | 0.0204 | 0.633 |
| `cbot_vol_top_decile` | 90 | 79 | -0.0297 | 0.443 |
| `gas_ratio_top_decile` | 40 | 79 | 0.0483 | 0.722 |
| `gas_ratio_top_decile` | 90 | 79 | -0.0095 | 0.582 |
| `roll_proxy_month` | 40 | 275 | -0.0203 | 0.451 |
| `roll_proxy_month` | 90 | 275 | -0.0608 | 0.422 |