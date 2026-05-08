# Validation Report

- Generated at: `2026-05-08 14:00:29 UTC`
- Overall status: **PASS** (7/7 checks passed)

## Validation Checks

### Ghost Columns
- Status: **PASS**
- Details: None

### Duplicate Columns
- Status: **PASS**
- Details: None

### Date Alignment Features/Targets
- Status: **PASS**
- Details: overlap=6192, threshold=5882, features=6192, targets=6192

### NaN Rate by Column
- Status: **PASS**
- Details: No column >95% NaN

### Target Coherence y_logret_h*
- Status: **PASS**
- Details: mean_abs_error={'y_logret_h5': 0.0, 'y_logret_h10': 0.0, 'y_logret_h20': 0.0, 'y_logret_h30': 0.0}, valid_rows={'y_logret_h5': 6187, 'y_logret_h10': 6182, 'y_logret_h20': 6172, 'y_logret_h30': 6162}

### Obvious Temporal Leakage
- Status: **PASS**
- Details: passed=True, suspect=0, naming=0, perfect_fit=0, future_dep=0

### Required Outputs (stacking + advisor)
- Status: **PASS**
- Details: All present

## Top NaN Rates

| Column | NaN rate |
|---|---:|
| `wx_belt_prcp_30_anom_z` | 0.2469 |
| `wx_belt_tmax_c_anom_z` | 0.2460 |
| `wx_belt_tmin_c_anom_z` | 0.2460 |
| `wx_belt_tavg_c_anom_z` | 0.2460 |
| `wx_nebraska_tavg_anom_z` | 0.2460 |
| `wx_belt_prcp_mm_anom_z` | 0.2460 |
| `wx_illinois_tavg_anom_z` | 0.2460 |
| `wx_iowa_tavg_anom_z` | 0.2460 |
| `wx_indiana_tavg_anom_z` | 0.2460 |
| `wx_minnesota_tavg_anom_z` | 0.2460 |
| `wasde_stocks_to_use_calc_z_surprise_vs_trend` | 0.1310 |
| `wasde_supply_minus_use_z_surprise_vs_trend` | 0.1310 |
| `wasde_avg_farm_price_z_surprise_vs_trend` | 0.1310 |
| `wasde_stocks_to_use_calc_z_surprise_vs_5y` | 0.1289 |
| `wasde_avg_farm_price_z_surprise_vs_5y` | 0.1289 |
| `wasde_supply_minus_use_z_surprise_vs_5y` | 0.1289 |
| `wasde_stocks_to_use_calc_z_surprise_vs_prev` | 0.1273 |
| `wasde_avg_farm_price_z_surprise_vs_prev` | 0.1273 |
| `wasde_supply_minus_use_z_surprise_vs_prev` | 0.1273 |
| `wasde_avg_farm_price_z` | 0.1271 |

## Conclusion

- The rebuilt V2 base is technically consistent for the validated scope.
- Next step can safely focus on data/source quality and model realism.
