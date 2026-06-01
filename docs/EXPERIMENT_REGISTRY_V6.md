# EXPERIMENT REGISTRY V6

> Registry global des experiences V6. Chaque experience doit garder son protocole, ses metriques, son verdict et ses artefacts.

- Records : 25

| Experiment | Target | Model | CV | Verdict |
|---|---|---|---|---|
| `V6-01-ema-y_rel_outperform_h10` | `y_rel_outperform_h10` | `logistic_baseline` | `crop_year_oof` | `WATCHLIST` |
| `V6-01-ema-y_rel_large_outperform_h10` | `y_rel_large_outperform_h10` | `logistic_baseline` | `crop_year_oof` | `WATCHLIST` |
| `V6-01-ema-y_rel_large_underperform_h10` | `y_rel_large_underperform_h10` | `logistic_baseline` | `crop_year_oof` | `WATCHLIST` |
| `V6-01-ema-y_rel_outperform_after_cbot_weak_h10` | `y_rel_outperform_after_cbot_weak_h10` | `logistic_baseline` | `crop_year_oof` | `NO_GO` |
| `V6-01-ema-y_rel_outperform_when_basis_extreme_h10` | `y_rel_outperform_when_basis_extreme_h10` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_outperform_h20` | `y_rel_outperform_h20` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_large_outperform_h20` | `y_rel_large_outperform_h20` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_large_underperform_h20` | `y_rel_large_underperform_h20` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_outperform_after_cbot_weak_h20` | `y_rel_outperform_after_cbot_weak_h20` | `logistic_baseline` | `crop_year_oof` | `WATCHLIST` |
| `V6-01-ema-y_rel_outperform_when_basis_extreme_h20` | `y_rel_outperform_when_basis_extreme_h20` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_outperform_h40` | `y_rel_outperform_h40` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_large_outperform_h40` | `y_rel_large_outperform_h40` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_large_underperform_h40` | `y_rel_large_underperform_h40` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_outperform_after_cbot_weak_h40` | `y_rel_outperform_after_cbot_weak_h40` | `logistic_baseline` | `crop_year_oof` | `WATCHLIST` |
| `V6-01-ema-y_rel_outperform_when_basis_extreme_h40` | `y_rel_outperform_when_basis_extreme_h40` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_outperform_h60` | `y_rel_outperform_h60` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_large_outperform_h60` | `y_rel_large_outperform_h60` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_large_underperform_h60` | `y_rel_large_underperform_h60` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_outperform_after_cbot_weak_h60` | `y_rel_outperform_after_cbot_weak_h60` | `logistic_baseline` | `crop_year_oof` | `WATCHLIST` |
| `V6-01-ema-y_rel_outperform_when_basis_extreme_h60` | `y_rel_outperform_when_basis_extreme_h60` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_outperform_h90` | `y_rel_outperform_h90` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_large_outperform_h90` | `y_rel_large_outperform_h90` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_large_underperform_h90` | `y_rel_large_underperform_h90` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_outperform_after_cbot_weak_h90` | `y_rel_outperform_after_cbot_weak_h90` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |
| `V6-01-ema-y_rel_outperform_h120` | `y_rel_outperform_h120` | `logistic_baseline` | `crop_year_oof` | `PROMISING` |

## Regles

- Toute experience V6 doit enregistrer `experiment_id`, `target`, `horizon`, `model`, `cv_protocol`, `metrics`, `verdict`.
- Les predictions utilisees comme meta-features doivent etre OOF.
- Les backtests restent `RESEARCH_ONLY_NOT_TRADING` tant que la source EMA est proxy.