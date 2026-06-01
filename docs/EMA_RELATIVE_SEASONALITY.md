# EMA RELATIVE SEASONALITY

> Etude saisonniere de `relative_ema_outperformance`.

## Verdict

- H40 meilleure saison : `sep_nov_eu_harvest` AUC 0.868
- H90 meilleure saison : `sep_nov_eu_harvest` AUC 0.916
- Lecture : La prime relative semble particulierement lisible autour de la recolte europeenne.

## H40

| Saison | n | Base rate | DA | AUC | Balanced acc. | Top20 DA | Basis moyen |
|---|---:|---:|---:|---:|---:|---:|---:|
| sep_nov_eu_harvest | 438 | 0.342 | 0.808 | 0.868 | 0.771 | 0.989 | 42.40 |
| dec_import_export_arbitrage | 220 | 0.164 | 0.736 | 0.830 | 0.731 | 0.955 | 40.38 |
| jan_mar_old_crop_import | 643 | 0.529 | 0.658 | 0.715 | 0.658 | 0.727 | 35.09 |
| apr_jun_sowing_weather | 755 | 0.795 | 0.417 | 0.503 | 0.473 | 0.570 | 35.70 |
| jul_aug_yield_stress | 352 | 0.298 | 0.812 | 0.865 | 0.773 | 0.957 | 46.63 |

## H90

| Saison | n | Base rate | DA | AUC | Balanced acc. | Top20 DA | Basis moyen |
|---|---:|---:|---:|---:|---:|---:|---:|
| sep_nov_eu_harvest | 438 | 0.336 | 0.842 | 0.916 | 0.846 | 1.000 | 42.40 |
| dec_import_export_arbitrage | 220 | 0.364 | 0.650 | 0.758 | 0.655 | 0.977 | 40.38 |
| jan_mar_old_crop_import | 627 | 0.697 | 0.592 | 0.629 | 0.566 | 0.656 | 34.76 |
| apr_jun_sowing_weather | 721 | 0.684 | 0.639 | 0.767 | 0.671 | 0.938 | 35.49 |
| jul_aug_yield_stress | 352 | 0.247 | 0.804 | 0.866 | 0.808 | 0.929 | 46.63 |
