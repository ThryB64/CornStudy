# EXPERIMENT REGISTRY V6

> Registry global des experiences V6. Chaque experience doit garder son protocole, ses metriques, son verdict et ses artefacts.

- Records : 26

| Experiment | Target | Model | CV | Verdict |
|---|---|---|---|---|
| `V6-02-cbot-y_cbot_drawdown_5pct_h20-histgb` | `y_cbot_drawdown_5pct_h20` | `histgb` | `crop_year_oof` | `WATCHLIST` |
| `V6-02-cbot-y_cbot_drawdown_5pct_h20-logistic` | `y_cbot_drawdown_5pct_h20` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-cbot-y_cbot_drawdown_5pct_h60-histgb` | `y_cbot_drawdown_5pct_h60` | `histgb` | `crop_year_oof` | `WATCHLIST` |
| `V6-02-cbot-y_cbot_drawdown_5pct_h60-logistic` | `y_cbot_drawdown_5pct_h60` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-cbot-y_cbot_large_down_3pct_h90-histgb` | `y_cbot_large_down_3pct_h90` | `histgb` | `crop_year_oof` | `PROMISING` |
| `V6-02-cbot-y_cbot_large_down_3pct_h90-logistic` | `y_cbot_large_down_3pct_h90` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-cbot-y_cbot_rally_5pct_h40-histgb` | `y_cbot_rally_5pct_h40` | `histgb` | `crop_year_oof` | `WATCHLIST` |
| `V6-02-cbot-y_cbot_rally_5pct_h40-logistic` | `y_cbot_rally_5pct_h40` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-cbot-y_cbot_up_h20-histgb` | `y_cbot_up_h20` | `histgb` | `crop_year_oof` | `WATCHLIST` |
| `V6-02-cbot-y_cbot_up_h20-logistic` | `y_cbot_up_h20` | `logistic` | `crop_year_oof` | `WATCHLIST` |
| `V6-02-cbot-y_cbot_up_h60-histgb` | `y_cbot_up_h60` | `histgb` | `crop_year_oof` | `PROMISING` |
| `V6-02-cbot-y_cbot_up_h60-logistic` | `y_cbot_up_h60` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_large_outperform_h90-histgb` | `y_rel_large_outperform_h90` | `histgb` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_large_outperform_h90-logistic` | `y_rel_large_outperform_h90` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_large_underperform_h90-histgb` | `y_rel_large_underperform_h90` | `histgb` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_large_underperform_h90-logistic` | `y_rel_large_underperform_h90` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_h120-histgb` | `y_rel_outperform_h120` | `histgb` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_h120-logistic` | `y_rel_outperform_h120` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_h40-histgb` | `y_rel_outperform_h40` | `histgb` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_h40-logistic` | `y_rel_outperform_h40` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_h90-histgb` | `y_rel_outperform_h90` | `histgb` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_h90-logistic` | `y_rel_outperform_h90` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_when_basis_extreme_h40-histgb` | `y_rel_outperform_when_basis_extreme_h40` | `histgb` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_when_basis_extreme_h40-logistic` | `y_rel_outperform_when_basis_extreme_h40` | `logistic` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_when_basis_extreme_h90-histgb` | `y_rel_outperform_when_basis_extreme_h90` | `histgb` | `crop_year_oof` | `PROMISING` |
| `V6-02-ema-y_rel_outperform_when_basis_extreme_h90-logistic` | `y_rel_outperform_when_basis_extreme_h90` | `logistic` | `crop_year_oof` | `PROMISING` |

## Regles

- Toute experience V6 doit enregistrer `experiment_id`, `target`, `horizon`, `model`, `cv_protocol`, `metrics`, `verdict`.
- Les predictions utilisees comme meta-features doivent etre OOF.
- Les backtests restent `RESEARCH_ONLY_NOT_TRADING` tant que la source EMA est proxy.