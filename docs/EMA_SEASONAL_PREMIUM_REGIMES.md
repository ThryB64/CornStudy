# EMA SEASONAL PREMIUM REGIMES

> Regimes saisonniers pour filtrer l'indicateur de prime EMA/CBOT.

## Verdict

- Saisons autorisées recherche : sep_nov_eu_harvest, jul_aug_yield_stress, dec_import_export_arbitrage
- Saisons abstention : aucune
- Meilleure saison : `sep_nov_eu_harvest` H90
- Lecture : Most seasons remain usable, but keep confidence tiers.

| Saison | Action | H recommandé | AUC | DA | BAcc | Top20 | H40 AUC | H90 AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sep_nov_eu_harvest | TRADE_ALLOWED_RESEARCH | 90 | 0.916 | 0.842 | 0.846 | 1.000 | 0.868 | 0.916 |
| jul_aug_yield_stress | TRADE_ALLOWED_RESEARCH | 90 | 0.866 | 0.804 | 0.808 | 0.929 | 0.865 | 0.866 |
| dec_import_export_arbitrage | TRADE_ALLOWED_RESEARCH | 40 | 0.830 | 0.736 | 0.731 | 0.955 | 0.830 | 0.758 |
| apr_jun_sowing_weather | CAUTION | 90 | 0.767 | 0.639 | 0.671 | 0.938 | 0.503 | 0.767 |
| jan_mar_old_crop_import | CAUTION | 40 | 0.715 | 0.658 | 0.658 | 0.727 | 0.715 | 0.629 |