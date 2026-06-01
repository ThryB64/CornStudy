# Bibliothèque des épisodes de basis haut (V82)

Les 42 signaux short-premium vus comme ÉPISODES de marché. Descriptif, anti-leakage, baseline figée. `RESEARCH_ONLY_NOT_TRADING`.

42 épisodes. Répartition par canal : {'CBOT_DRIVEN': 19, 'EMA_DRIVEN': 13, 'ADVERSE': 7, 'BOTH': 3}.

## Familles d'épisodes (par canal de compression)

- **CBOT_DRIVEN** : n=19, win=1.0, PnL=22.7, MFE=37.01, durée=43.0 j, CBOT_SUPPORT dominant=LOW
- **EMA_DRIVEN** : n=13, win=0.923, PnL=14.01, MFE=27.65, durée=39.6 j, CBOT_SUPPORT dominant=LOW
- **BOTH** : n=3, win=1.0, PnL=16.79, MFE=18.98, durée=10.0 j, CBOT_SUPPORT dominant=HIGH
- **ADVERSE** : n=7, win=0.0, PnL=-17.83, MFE=5.67, durée=60.1 j, CBOT_SUPPORT dominant=LOW

## Épisodes (extrait)

| entrée | tier | z | path | CBOT_SUP | ADV_RISK | ENSO | durée | MFE | PnL | raison |
|---|---|---:|---|---|---|---|---:|---:|---:|---|
| 2010-03-30 | SHORT_PREMIUM_MODERATE | 1.03 | CBOT_DRIVEN | LOW | MEDIUM | None | 30 | 4.8 | 3.9 | compression par rattrapage CBOT |
| 2010-05-24 | SHORT_PREMIUM_MODERATE | 1.16 | ADVERSE | MEDIUM | MEDIUM | None | 56 | 10.18 | -22.8 | échec : prime seulement modérée ; échec : mois de roll |
| 2010-07-07 | SHORT_PREMIUM_EXTREME | 3.85 | CBOT_DRIVEN | MEDIUM | LOW | None | 75 | 52.96 | 53.0 | compression par rattrapage CBOT |
| 2010-08-16 | SHORT_PREMIUM_EXTREME | 2.67 | CBOT_DRIVEN | MEDIUM | MEDIUM | None | 47 | 50.55 | 50.5 | compression par rattrapage CBOT |
| 2010-09-27 | SHORT_PREMIUM_MODERATE | 1.17 | BOTH | MEDIUM | MEDIUM | None | 18 | 27.02 | 27.0 | compression mixte |
| 2011-01-04 | SHORT_PREMIUM_MODERATE | 1.01 | CBOT_DRIVEN | MEDIUM | MEDIUM | None | 23 | 40.01 | 10.3 | compression par rattrapage CBOT |
| 2011-07-01 | SHORT_PREMIUM_MODERATE | 1.42 | CBOT_DRIVEN | LOW | MEDIUM | None | 7 | 77.49 | 25.1 | compression par rattrapage CBOT |
| 2012-12-04 | SHORT_PREMIUM_MODERATE | 1.27 | EMA_DRIVEN | MEDIUM | MEDIUM | None | 62 | 24.64 | 22.1 | compression par repli EMA |
| 2013-01-15 | SHORT_PREMIUM_MODERATE | 1.15 | EMA_DRIVEN | MEDIUM | MEDIUM | None | 34 | 33.13 | 30.4 | compression par repli EMA |
| 2013-04-05 | SHORT_PREMIUM_MODERATE | 1.2 | CBOT_DRIVEN | LOW | MEDIUM | None | 17 | 37.3 | 23.4 | compression par rattrapage CBOT |
| 2013-07-16 | SHORT_PREMIUM_EXTREME | 3.7 | EMA_DRIVEN | LOW | LOW | None | 68 | 32.36 | -1.7 | compression par repli EMA |
| 2013-09-16 | SHORT_PREMIUM_MODERATE | 1.33 | ADVERSE | LOW | MEDIUM | None | 55 | 0.0 | -27.0 | échec : CBOT non porteur ; échec : prime seulement modérée |
| 2013-12-04 | SHORT_PREMIUM_EXTREME | 2.79 | CBOT_DRIVEN | LOW | MEDIUM | None | 90 | 30.42 | 22.9 | compression par rattrapage CBOT |
| 2014-01-13 | SHORT_PREMIUM_MODERATE | 1.24 | CBOT_DRIVEN | MEDIUM | MEDIUM | None | 90 | 19.54 | 7.2 | compression par rattrapage CBOT |
| 2014-03-06 | SHORT_PREMIUM_MODERATE | 1.02 | ADVERSE | HIGH | MEDIUM | None | 90 | 12.86 | -15.9 | échec : prime seulement modérée |
| 2014-07-09 | SHORT_PREMIUM_MODERATE | 1.08 | EMA_DRIVEN | LOW | MEDIUM | None | 42 | 15.48 | 3.8 | compression par repli EMA |
| 2015-08-11 | SHORT_PREMIUM_MODERATE | 1.49 | EMA_DRIVEN | LOW | MEDIUM | None | 25 | 19.16 | 14.8 | compression par repli EMA |
| 2016-06-10 | SHORT_PREMIUM_MODERATE | 1.09 | BOTH | HIGH | MEDIUM | None | 6 | 14.04 | 14.0 | compression mixte |
| 2016-07-20 | SHORT_PREMIUM_STRONG | 1.9 | EMA_DRIVEN | LOW | LOW | None | 60 | 17.98 | 12.7 | compression par repli EMA |
| 2016-08-29 | SHORT_PREMIUM_EXTREME | 2.22 | CBOT_DRIVEN | LOW | LOW | None | 32 | 31.01 | 24.1 | compression par rattrapage CBOT |
| 2017-05-09 | SHORT_PREMIUM_MODERATE | 1.19 | BOTH | LOW | MEDIUM | None | 6 | 15.88 | 9.3 | compression mixte |
| 2017-06-22 | SHORT_PREMIUM_MODERATE | 1.07 | EMA_DRIVEN | LOW | HIGH | None | 10 | 14.01 | 5.6 | compression par repli EMA |
| 2017-08-28 | SHORT_PREMIUM_MODERATE | 1.11 | CBOT_DRIVEN | LOW | MEDIUM | None | 14 | 17.88 | 6.8 | compression par rattrapage CBOT |
| 2017-12-04 | SHORT_PREMIUM_MODERATE | 1.24 | EMA_DRIVEN | LOW | MEDIUM | None | 29 | 10.13 | 4.5 | compression par repli EMA |
| 2018-03-28 | SHORT_PREMIUM_MODERATE | 1.07 | CBOT_DRIVEN | HIGH | MEDIUM | None | 3 | 18.62 | 5.3 | compression par rattrapage CBOT |
| 2018-06-15 | SHORT_PREMIUM_MODERATE | 1.25 | ADVERSE | LOW | MEDIUM | None | 37 | 5.13 | -22.0 | échec : CBOT non porteur ; échec : prime seulement modérée |
| 2018-08-09 | SHORT_PREMIUM_EXTREME | 4.93 | EMA_DRIVEN | MEDIUM | MEDIUM | None | 47 | 24.0 | 23.7 | compression par repli EMA |
| 2018-09-18 | SHORT_PREMIUM_STRONG | 1.64 | CBOT_DRIVEN | LOW | MEDIUM | None | 20 | 21.15 | 20.8 | compression par rattrapage CBOT |
| 2020-03-18 | SHORT_PREMIUM_MODERATE | 1.27 | ADVERSE | LOW | HIGH | None | 81 | 4.21 | -23.4 | échec : CBOT non porteur ; échec : prime seulement modérée |
| 2020-04-27 | SHORT_PREMIUM_EXTREME | 2.18 | ADVERSE | LOW | MEDIUM | None | 90 | 7.33 | -2.1 | échec : CBOT non porteur |
| 2020-06-08 | SHORT_PREMIUM_STRONG | 1.98 | CBOT_DRIVEN | MEDIUM | MEDIUM | None | 90 | 18.9 | 11.9 | compression par rattrapage CBOT |
| 2020-07-20 | SHORT_PREMIUM_STRONG | 1.92 | CBOT_DRIVEN | LOW | MEDIUM | None | 66 | 20.48 | 12.7 | compression par rattrapage CBOT |
| 2020-08-31 | SHORT_PREMIUM_MODERATE | 1.05 | CBOT_DRIVEN | MEDIUM | HIGH | None | 84 | 28.83 | 21.0 | compression par rattrapage CBOT |
| 2020-12-14 | SHORT_PREMIUM_MODERATE | 1.03 | CBOT_DRIVEN | HIGH | MEDIUM | None | 11 | 62.49 | 10.0 | compression par rattrapage CBOT |
| 2021-07-16 | SHORT_PREMIUM_MODERATE | 1.02 | EMA_DRIVEN | LOW | MEDIUM | None | 18 | 31.75 | 24.6 | compression par repli EMA |
| 2021-10-04 | SHORT_PREMIUM_MODERATE | 1.11 | CBOT_DRIVEN | HIGH | MEDIUM | None | 51 | 40.09 | 24.1 | compression par rattrapage CBOT |
| 2022-03-08 | SHORT_PREMIUM_EXTREME | 3.17 | CBOT_DRIVEN | HIGH | MEDIUM | None | 31 | 70.14 | 48.2 | compression par rattrapage CBOT |
| 2022-05-05 | SHORT_PREMIUM_MODERATE | 1.01 | EMA_DRIVEN | HIGH | MEDIUM | None | 29 | 52.98 | 15.8 | compression par repli EMA |
| 2022-07-18 | SHORT_PREMIUM_EXTREME | 2.35 | CBOT_DRIVEN | LOW | LOW | None | 36 | 60.52 | 50.2 | compression par rattrapage CBOT |
| 2022-10-03 | SHORT_PREMIUM_MODERATE | 1.02 | EMA_DRIVEN | HIGH | MEDIUM | None | 49 | 47.23 | 9.0 | compression par repli EMA |
| 2023-07-21 | SHORT_PREMIUM_MODERATE | 1.01 | EMA_DRIVEN | LOW | HIGH | None | 42 | 36.61 | 16.7 | compression par repli EMA |
| 2025-07-09 | SHORT_PREMIUM_MODERATE | 1.01 | ADVERSE | LOW | MEDIUM | None | 12 | 0.0 | -11.6 | échec : CBOT non porteur ; échec : prime seulement modérée ; échec : mois de roll |