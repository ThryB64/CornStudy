# EMA DATA QUALITY SPLIT

> Comparaison des signaux EMA par qualité/source de données.

## Verdict

- Signal suivi : relative_ema_outperformance_h40
- AUC all data : 0.708
- AUC proxy dominant : 0.708
- Official recent : no_valid_folds (22 lignes)
- Conclusion : Signal robuste observable surtout sur historique proxy; période officielle récente trop courte pour validation OOF.

## Splits

| Split | n | Période | Official share | Proxy share | Relative H40 AUC | Relative H40 balanced acc. |
|---|---:|---|---:|---:|---:|---:|
| all_data | 2990 | 2010-01-05 -> 2025-07-28 | 0.004 | 0.996 | 0.708 | 0.642 |
| proxy_dominant | 2990 | 2010-01-05 -> 2025-07-28 | 0.004 | 0.996 | 0.708 | 0.642 |
| official_recent | 22 | 2025-06-09 -> 2025-07-28 | 0.500 | 0.500 | N/A | N/A |
| high_availability | 2967 | 2010-01-05 -> 2025-07-28 | 0.004 | 0.996 | 0.706 | 0.639 |
| low_quality_excluded | 27 | 2025-05-28 -> 2025-07-28 | 0.469 | 0.531 | N/A | N/A |