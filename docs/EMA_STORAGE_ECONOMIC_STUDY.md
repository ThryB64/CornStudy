# EMA Storage Economic Study

> EMA historical prices are exploratory Barchart-derived data, not official Euronext settlement.

## Verdict

- `STORAGE_ECONOMIC_NO_GO`: No model strategy beats simple economic baselines by a material margin.

## Baselines

- `never_store`: gain=0.000 EUR/t, median=0.000, store=0.0%, years+=0/13, regret=8.660
- `always_store_1m`: gain=-0.293 EUR/t, median=-0.750, store=100.0%, years+=6/13, regret=5.262
- `oracle_store_1m`: gain=4.969 EUR/t, median=0.000, store=45.7%, years+=13/13, regret=0.000
- `always_store_3m`: gain=-1.319 EUR/t, median=-2.000, store=100.0%, years+=6/13, regret=9.980
- `oracle_store_3m`: gain=8.660 EUR/t, median=0.000, store=44.2%, years+=13/13, regret=0.000
- `always_store_6m`: gain=-4.003 EUR/t, median=-5.250, store=100.0%, years+=3/13, regret=16.337
- `oracle_store_6m`: gain=12.334 EUR/t, median=0.000, store=39.5%, years+=13/13, regret=0.000

## Model Strategies

- `cbot_only_pred_value_margin_0`: gain=-1.109 EUR/t, median=0.000, store=68.8%, years+=3/8, regret=9.690
- `cbot_only_pred_value_margin_3`: gain=-1.196 EUR/t, median=0.000, store=61.0%, years+=3/8, regret=9.778
- `cbot_only_pred_value_margin_5`: gain=-1.158 EUR/t, median=0.000, store=53.7%, years+=3/8, regret=9.740
- `ema_curve_only_pred_value_margin_0`: gain=-0.470 EUR/t, median=0.000, store=28.3%, years+=5/8, regret=9.051
- `ema_curve_only_pred_value_margin_3`: gain=-0.127 EUR/t, median=0.000, store=20.8%, years+=4/8, regret=8.709
- `ema_curve_only_pred_value_margin_5`: gain=-0.277 EUR/t, median=0.000, store=13.7%, years+=3/8, regret=8.858
- `cbot_ema_combined_pred_value_margin_0`: gain=-1.157 EUR/t, median=0.000, store=23.1%, years+=2/8, regret=9.739
- `cbot_ema_combined_pred_value_margin_3`: gain=-0.976 EUR/t, median=0.000, store=18.3%, years+=2/8, regret=9.557
- `cbot_ema_combined_pred_value_margin_5`: gain=-0.793 EUR/t, median=0.000, store=15.0%, years+=2/8, regret=9.374
- `selected_full_pred_value_margin_0`: gain=-0.534 EUR/t, median=0.000, store=59.9%, years+=3/8, regret=9.116
- `selected_full_pred_value_margin_3`: gain=-0.293 EUR/t, median=0.000, store=54.7%, years+=3/8, regret=8.874
- `selected_full_pred_value_margin_5`: gain=0.005 EUR/t, median=0.000, store=50.2%, years+=3/8, regret=8.576

## Interpretation

- La métrique principale est le gain net moyen EUR/t, pas la DA seule.
- Les stratégies avec marge ne stockent que si la valeur prédite dépasse le seuil économique.
- Les résultats restent exploratoires tant que les coûts de stockage locaux et financiers ne sont pas personnalisés.
