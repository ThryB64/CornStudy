# ROLL SEASON BACKTEST V6

> Tests roll-aware, experts saisonniers et backtests research-only EMA/CBOT.

- Source quality : `exploratoire_barchart_proxy`
- Production verdict : `RESEARCH_ONLY_NOT_TRADING`
- Best policy : `seasonal_expert` / `top20_train_only`
- Best backtest : `seasonal_expert` / `top40_no_roll`
- Lecture : Roll-aware and seasonal filters materially improve selectivity in research-only spread tests.

## Policy Results

| Scenario | Policy | n | Coverage | AUC | BA | DA | Stability |
|---|---|---:|---:|---:|---:|---:|---:|
| `h40` | `all` | 503 | 1.000 | 0.783 | 0.725 | 0.722 | 0.833 |
| `h40` | `no_roll_proxy` | 322 | 0.640 | 0.701 | 0.653 | 0.655 | 0.667 |
| `h40` | `strong_season` | 395 | 0.785 | 0.823 | 0.778 | 0.744 | 0.667 |
| `h40` | `strong_season_no_roll` | 216 | 0.429 | 0.652 | 0.678 | 0.662 | 0.600 |
| `h40` | `top40_train_only` | 187 | 0.372 | 0.826 | 0.797 | 0.802 | 1.000 |
| `h40` | `top20_train_only` | 79 | 0.157 | 0.907 | 0.762 | 0.772 | 1.000 |
| `h40` | `top40_no_roll` | 110 | 0.219 | 0.736 | 0.677 | 0.691 | 1.000 |
| `h90` | `all` | 503 | 1.000 | 0.937 | 0.854 | 0.837 | 1.000 |
| `h90` | `no_roll_proxy` | 322 | 0.640 | 0.889 | 0.799 | 0.776 | 0.833 |
| `h90` | `strong_season` | 395 | 0.785 | 0.950 | 0.868 | 0.838 | 1.000 |
| `h90` | `strong_season_no_roll` | 216 | 0.429 | 0.869 | 0.796 | 0.745 | 0.667 |
| `h90` | `top40_train_only` | 168 | 0.334 | 0.977 | 0.970 | 0.970 | 1.000 |
| `h90` | `top20_train_only` | 68 | 0.135 | 0.967 | 0.970 | 0.971 | 1.000 |
| `h90` | `top40_no_roll` | 81 | 0.161 | 0.971 | 0.966 | 0.975 | 1.000 |
| `seasonal_expert` | `all` | 503 | 1.000 | 0.941 | 0.852 | 0.835 | 1.000 |
| `seasonal_expert` | `no_roll_proxy` | 322 | 0.640 | 0.895 | 0.797 | 0.773 | 0.750 |
| `seasonal_expert` | `strong_season` | 395 | 0.785 | 0.956 | 0.866 | 0.835 | 1.000 |
| `seasonal_expert` | `strong_season_no_roll` | 216 | 0.429 | 0.882 | 0.792 | 0.741 | 0.000 |
| `seasonal_expert` | `top40_train_only` | 168 | 0.334 | 0.989 | 0.978 | 0.976 | 1.000 |
| `seasonal_expert` | `top20_train_only` | 68 | 0.135 | 0.982 | 0.983 | 0.985 | 1.000 |
| `seasonal_expert` | `top40_no_roll` | 81 | 0.161 | 0.999 | 0.982 | 0.988 | 1.000 |
| `h40_h90_agreement` | `all` | 461 | 1.000 | 0.943 | 0.855 | 0.835 | 1.000 |
| `h40_h90_agreement` | `no_roll_proxy` | 300 | 0.651 | 0.904 | 0.800 | 0.773 | 0.800 |
| `h40_h90_agreement` | `strong_season` | 359 | 0.779 | 0.947 | 0.865 | 0.833 | 1.000 |
| `h40_h90_agreement` | `strong_season_no_roll` | 200 | 0.434 | 0.870 | 0.784 | 0.735 | 0.600 |
| `h40_h90_agreement` | `top40_train_only` | 160 | 0.347 | 0.974 | 0.981 | 0.981 | 1.000 |
| `h40_h90_agreement` | `top20_train_only` | 58 | 0.126 | 0.971 | 0.945 | 0.948 | 1.000 |
| `h40_h90_agreement` | `top40_no_roll` | 86 | 0.187 | 0.967 | 0.981 | 0.988 | 1.000 |

## Backtests Research Only

| Scenario | Policy | Cost | Trades | Hit | PnL | PF | DD |
|---|---|---:|---:|---:|---:|---:|---:|
| `h40` | `top40_no_roll` | 1.0 | 12 | 0.667 | 117.42 | 2.55 | -35.46 |
| `h40` | `top40_no_roll` | 2.0 | 12 | 0.667 | 93.42 | 2.12 | -41.46 |
| `h40` | `top40_no_roll` | 3.0 | 12 | 0.667 | 69.42 | 1.76 | -47.46 |
| `h40` | `top40_no_roll` | 5.0 | 12 | 0.583 | 21.42 | 1.19 | -59.46 |
| `h40` | `top40_no_roll` | 8.0 | 12 | 0.417 | -50.58 | 0.66 | -77.46 |
| `h90` | `top40_no_roll` | 1.0 | 9 | 0.778 | 159.01 | 10.06 | -17.56 |
| `h90` | `top40_no_roll` | 2.0 | 9 | 0.778 | 141.01 | 7.54 | -21.56 |
| `h90` | `top40_no_roll` | 3.0 | 9 | 0.778 | 123.01 | 5.81 | -25.56 |
| `h90` | `top40_no_roll` | 5.0 | 9 | 0.778 | 87.01 | 3.59 | -33.56 |
| `h90` | `top40_no_roll` | 8.0 | 9 | 0.556 | 33.01 | 1.60 | -50.16 |
| `seasonal_expert` | `top40_no_roll` | 1.0 | 9 | 0.889 | 179.65 | 100.16 | -1.81 |
| `seasonal_expert` | `top40_no_roll` | 2.0 | 9 | 0.889 | 161.65 | 43.41 | -3.81 |
| `seasonal_expert` | `top40_no_roll` | 3.0 | 9 | 0.889 | 143.65 | 25.72 | -5.81 |
| `seasonal_expert` | `top40_no_roll` | 5.0 | 9 | 0.778 | 107.65 | 9.33 | -12.93 |
| `seasonal_expert` | `top40_no_roll` | 8.0 | 9 | 0.556 | 53.65 | 2.56 | -29.53 |
| `h40_h90_agreement` | `pre_filtered` | 1.0 | 16 | 0.625 | 152.07 | 2.80 | -44.44 |
| `h40_h90_agreement` | `pre_filtered` | 2.0 | 16 | 0.625 | 118.07 | 2.21 | -50.44 |
| `h40_h90_agreement` | `pre_filtered` | 3.0 | 16 | 0.438 | 84.07 | 1.74 | -56.44 |
| `h40_h90_agreement` | `pre_filtered` | 5.0 | 16 | 0.438 | 16.07 | 1.11 | -79.50 |
| `h40_h90_agreement` | `pre_filtered` | 8.0 | 16 | 0.312 | -85.93 | 0.61 | -133.50 |