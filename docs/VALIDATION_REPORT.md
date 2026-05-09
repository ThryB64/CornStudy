# Validation Report

- Generated at: `2026-05-09 10:16:18 UTC`
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
| `cot_pm_net_pct_oi_surprise_vs_trend` | 0.5097 |
| `cot_mm_net_pct_oi_surprise_vs_trend` | 0.5097 |
| `cot_pm_net_surprise_vs_trend` | 0.5097 |
| `cot_sd_net_surprise_vs_trend` | 0.5097 |
| `cot_mm_long_pct_surprise_vs_trend` | 0.5097 |
| `cot_mm_short_pct_surprise_vs_trend` | 0.5097 |
| `cot_pm_long_surprise_vs_trend` | 0.5097 |
| `cot_mm_short_surprise_vs_trend` | 0.5097 |
| `cot_open_interest_surprise_vs_trend` | 0.5097 |
| `cot_mm_long_surprise_vs_trend` | 0.5097 |
| `cot_sd_short_surprise_vs_trend` | 0.5097 |
| `cot_sd_long_surprise_vs_trend` | 0.5097 |
| `cot_pm_short_surprise_vs_trend` | 0.5097 |
| `cot_mm_net_surprise_vs_trend` | 0.5097 |
| `cot_sd_net_surprise_vs_5y` | 0.4995 |
| `cot_mm_long_pct_surprise_vs_5y` | 0.4995 |
| `cot_mm_net_pct_oi_surprise_vs_5y` | 0.4995 |
| `cot_pm_net_pct_oi_surprise_vs_5y` | 0.4995 |
| `cot_mm_short_pct_surprise_vs_5y` | 0.4995 |
| `cot_mm_long_surprise_vs_5y` | 0.4995 |

## Conclusion

- The rebuilt V2 base is technically consistent for the validated scope.
- Next step can safely focus on data/source quality and model realism.
