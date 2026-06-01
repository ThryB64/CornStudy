# EMA TARGET INTEGRITY

> Audit FIX-EMA-01 : les cibles futures inconnues doivent rester NaN.

**Verdict :** TARGET_INTEGRITY_PASS

| Target | Horizon | Non-null | Base rate | Tail NaN | Verdict |
|---|---:|---:|---:|---:|---|
| y_up_h20_ema_raw | 20 | 2969 | 49.4% | 20 | PASS |
| y_up_h40_ema_raw | 40 | 2949 | 53.1% | 40 | PASS |
| y_ema_outperforms_cbot_h20 | 20 | 2969 | 48.5% | 20 | PASS |
| y_ema_outperforms_cbot_h40 | 40 | 2949 | 51.3% | 40 | PASS |
| basis_reversion_h20 | 20 | 701 | 65.5% | 20 | PASS |
| ema_vol_high_h20 | 20 | 2969 | 19.3% | 20 | PASS |
| eu_residual_shock_up_h20 | 20 | 2448 | 2.0% | 20 | PASS |
| eu_residual_shock_down_h20 | 20 | 2448 | 2.3% | 20 | PASS |

## Règle

Futures inconnus en fin de série doivent rester NaN, jamais devenir 0 via NaN > 0.