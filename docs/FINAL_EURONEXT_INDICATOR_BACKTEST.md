# Backtest agricole Euronext — indicateur de vente

Version : `euronext_indicator_v1`. **Pas un bot** : ventes partielles (33 %), cooldown, campagnes ; jamais de short/buy/levier. ⚠️ prix Euronext ~97 % proxy.

## Comparaison campagnes × cooldown (prix moyen score & Δ baselines, €/t)

| window | cooldown | campaigns | mean_avg_price_score | score_vs_sell_all_start_mean | score_vs_sell_thirds_mean | score_vs_monthly_dca_mean | score_vs_wait_year_end_mean | score_vs_sell_all_start_won | score_vs_sell_thirds_won | score_vs_monthly_dca_won | score_vs_wait_year_end_won |
|---|---|---|---|---|---|---|---|---|---|---|---|
| calendar | 0 | 17 | 203.950 | 8.170 | 4.140 | 5.700 | 3.950 | 8/17 | 9/17 | 9/17 | 7/17 |
| calendar | 20 | 17 | 204.320 | 8.540 | 4.510 | 6.070 | 4.320 | 9/17 | 8/17 | 9/17 | 9/17 |
| sep_aug | 0 | 17 | 205.000 | 12.920 | 8.600 | 7.700 | 8.350 | 10/17 | 9/17 | 9/17 | 10/17 |
| sep_aug | 20 | 17 | 204.400 | 12.330 | 8.010 | 7.100 | 7.750 | 11/17 | 11/17 | 10/17 | 10/17 |
| oct_sep | 0 | 17 | 204.850 | 14.880 | 8.080 | 7.230 | 10.470 | 10/17 | 11/17 | 9/17 | 8/17 |
| oct_sep | 20 | 17 | 203.600 | 13.630 | 6.830 | 5.980 | 9.220 | 13/17 | 10/17 | 8/17 | 10/17 |

## Synthèse (année civile, cooldown défaut)

```json
{
  "window": "calendar",
  "cooldown": 20,
  "period": "2010-01-04..last",
  "campaigns": 17,
  "sell_fraction": 0.33,
  "mean_avg_price_score": 204.32,
  "mean_avg_price_sell_all_start": 195.78,
  "mean_avg_price_sell_thirds": 199.8,
  "mean_avg_price_monthly_dca": 198.25,
  "mean_avg_price_wait_year_end": 200.0,
  "score_vs_sell_all_start_mean": 8.54,
  "score_vs_sell_all_start_won": 9,
  "score_vs_sell_all_start_total": 17,
  "score_vs_sell_all_start_max_regret": 38.35,
  "score_vs_sell_thirds_mean": 4.51,
  "score_vs_sell_thirds_won": 8,
  "score_vs_sell_thirds_total": 17,
  "score_vs_sell_thirds_max_regret": 12.47,
  "score_vs_monthly_dca_mean": 6.07,
  "score_vs_monthly_dca_won": 9,
  "score_vs_monthly_dca_total": 17,
  "score_vs_monthly_dca_max_regret": 12.39,
  "score_vs_wait_year_end_mean": 4.32,
  "score_vs_wait_year_end_won": 9,
  "score_vs_wait_year_end_total": 17,
  "score_vs_wait_year_end_max_regret": 46.37
}
```

## Lecture honnête

- L'indicateur **n'est pas systématiquement meilleur** que les baselines simples ; le résultat dépend du découpage de campagne et du cooldown (comme pour le CBOT).
- Sur un prix **proxy**, ces chiffres sont **illustratifs**. Aucune conclusion de vente opérationnelle ne doit en être tirée.
- Réponses : utile **visuellement** pour ordonner les périodes (SELL_PARTIAL ≈ avant baisses), mais **pas validé** comme stratégie ; fragile, à reconfirmer en forward sur des **settlements officiels** Euronext.