# EMA Data Audit

> EMA historical prices are exploratory Barchart-derived data, not official Euronext settlement.

## Verdict

- Pivot directionnel EMA direct : non validé actuellement.
- Libellé recommandé : **EMA front/basis/liquidity features, with partial curve fragments**.
- EMA est surtout exploitable pour prix européen réel, basis CBOT-EMA, stockage et harvest_nov.

## Contrats

- Lignes : 4818
- Période : 2010-01-04 -> 2026-05-20
- Dates uniques : 3868
- Contrats uniques : 75
- Sources : `{'barchart_proxy_exploratory': 4144, 'euronext_ajax_prices': 10, 'euronext_chart_history': 664}`
- Mois utilisables : `{'H': 1131, 'M': 1274, 'Q': 1212, 'X': 1201}`
- Lignes F/Janvier utilisables : 0

## Séries Continues

- `front_raw` : 3377 lignes, 2010-01-04 -> 2026-05-20
- `front_adjusted` : 3377 lignes, 2010-01-04 -> 2026-05-20
- `liquid_raw` : 3377 lignes, 2010-01-04 -> 2026-05-20
- `harvest_nov` : 1095 lignes, 2010-08-10 -> 2026-05-20

## Rolls Front

- Rolls : 69
- Gap moyen absolu : 9.688 EUR/t
- Gap médian absolu : 6.000 EUR/t
- Gap maximum absolu : 54.250 EUR/t (2013-08-08)

## Densité De Courbe

- Lignes : 4818
- Dates uniques : 3868
- Contrats moyens par date : 1.246
- Distribution contrats/date : `{'1': 3293, '2': 380, '3': 44, '4': 127, '5': 23, '10': 1}`
- Dates avec >=2 contrats : 14.9%
- Dates avec >=3 contrats : 5.0%

## Features De Courbe Sparse

- `ema_carry_front_second` : 14.8% non-null
- `ema_curve_slope_3` : 5.0% non-null
- `ema_curve_slope_6` : 13.7% non-null
- `ema_roll_yield_ann` : 14.8% non-null
- `ema_spread_f0_f1` : 14.8% non-null
- `ema_spread_f0_f2` : 5.0% non-null
- `ema_spread_f1_f2` : 5.0% non-null
- `ema_spread_nov_mar` : 2.9% non-null

## Targets Et Rolls

- H20 : cross-roll 39.7%, raw=3357, adjusted=3357, no-roll=2023
- H40 : cross-roll 79.1%, raw=3337, adjusted=3337, no-roll=699
- H60 : cross-roll 100.0%, raw=3317, adjusted=3317, no-roll=0

## Conclusion Méthodologique

- Ne pas présenter les features EMA comme une courbe futures complète — libellé correct : "features EMA front, basis, liquidité et fragments de courbe" tant que les contrats simultanés restent rares (14.9% des dates avec ≥2 contrats).
- Pour la direction EMA, H20 reste la seule cible raisonnablement testable en no-roll ; H60 no-roll est structurellement indisponible.
- Le moteur directionnel principal reste CBOT ; EMA doit être traité comme couche prix local, basis et décision stockage.
