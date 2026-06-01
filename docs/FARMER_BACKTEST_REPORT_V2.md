# Backtest agriculteur V2 — 8 stratégies

## Objectif

Comparer 8 stratégies de vente de maïs, de la plus simple (vente à récolte) à la borne
théorique (hindsight parfait). La question centrale : *à quel point le modèle aide-t-il,*
*et dans quelles conditions ?*

## Hypothèses

- Horizon décision : J+30
- État/profil : `iowa`
- Période : `2010–2023` (14 saisons)
- Basis local : -0.20 USD/bu
- Coût stockage : 0.04 USD/bu/mois
- Perte qualité : 0.50%/mois
- Prédictions modèle : calibrated_predictions.parquet
- CQR : cqr_results.parquet

> **PERFECT_HINDSIGHT** = borne théorique : vente au prix maximum observé dans la saison.
> C'est un plafond irréalisable, fourni uniquement comme référence de regret.

## Résumé par stratégie

| Stratégie | Prix moyen USD/bu | Capture rate | vs Récolte | vs Mensuel | Regret | % années gagne | Sharpe | N |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `PERFECT_HINDSIGHT` ⭐ | 5.666 | 100.0% | +1.090 | +1.320 | 0.000 | 100.0% | 0.99 | 14 |
| `SELL_HARVEST` | 4.576 | 82.8% | +0.000 | +0.230 | 1.090 | 0.0% | 0.00 | 14 |
| `MODEL_SIGNAL` | 4.537 | 81.7% | -0.039 | +0.191 | 1.129 | 35.7% | -0.37 | 14 |
| `SELL_THIRDS` | 4.520 | 80.7% | -0.056 | +0.174 | 1.146 | 28.6% | -0.11 | 14 |
| `SELL_MONTHLY` | 4.346 | 77.3% | -0.230 | +0.000 | 1.320 | 21.4% | -0.34 | 14 |
| `CQR_CAUTIOUS` | 4.177 | 76.4% | -0.398 | -0.169 | 1.489 | 7.1% | -0.39 | 14 |
| `MODEL_STORAGE_VALUE` | 4.202 | 76.2% | -0.373 | -0.144 | 1.464 | 21.4% | -0.35 | 14 |
| `SELL_THRESHOLD` | 4.168 | 73.6% | -0.408 | -0.179 | 1.498 | 0.0% | -0.75 | 14 |

## Capture rate par année

| season | SELL_HARVEST | SELL_MONTHLY | SELL_THIRDS | SELL_THRESHOLD | MODEL_SIGNAL | MODEL_STORAGE_VALUE | CQR_CAUTIOUS | PERFECT_HINDSIGHT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | 70.8% | 78.5% | 78.4% | 70.8% | 70.5% | 69.6% | 69.6% | 100.0% |
| 2011 | 76.5% | 73.9% | 70.1% | 76.5% | 76.6% | 79.0% | 79.0% | 100.0% |
| 2012 | 96.7% | 79.4% | 89.6% | 96.7% | 96.8% | 46.3% | 46.3% | 100.0% |
| 2013 | 85.4% | 75.9% | 79.5% | 54.1% | 85.4% | 54.1% | 54.1% | 100.0% |
| 2014 | 79.2% | 79.1% | 76.8% | 69.8% | 79.5% | 69.7% | 69.7% | 100.0% |
| 2015 | 85.1% | 75.7% | 83.1% | 63.5% | 83.7% | 85.1% | 85.1% | 100.0% |
| 2016 | 89.7% | 83.2% | 86.9% | 71.1% | 87.5% | 89.7% | 89.7% | 100.0% |
| 2017 | 85.1% | 79.4% | 79.9% | 73.2% | 82.8% | 85.9% | 85.1% | 100.0% |
| 2018 | 82.4% | 76.2% | 82.5% | 78.4% | 79.5% | 69.6% | 82.4% | 100.0% |
| 2019 | 99.1% | 80.8% | 87.4% | 99.1% | 95.2% | 94.2% | 99.1% | 100.0% |
| 2020 | 51.0% | 63.7% | 64.8% | 51.0% | 51.5% | 65.1% | 51.0% | 100.0% |
| 2021 | 63.4% | 75.7% | 73.3% | 63.4% | 66.5% | 63.4% | 63.4% | 100.0% |
| 2022 | 97.9% | 81.5% | 92.1% | 97.9% | 96.0% | 97.9% | 97.9% | 100.0% |
| 2023 | 96.9% | 79.1% | 85.8% | 65.2% | 92.8% | 96.9% | 96.9% | 100.0% |

## Delta vs SELL_HARVEST par année (USD/bu)

| season | SELL_HARVEST | SELL_MONTHLY | SELL_THIRDS | SELL_THRESHOLD | MODEL_SIGNAL | MODEL_STORAGE_VALUE | CQR_CAUTIOUS | PERFECT_HINDSIGHT |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | +0.000 | +0.594 | +0.585 | +0.000 | -0.019 | -0.091 | -0.091 | +2.240 |
| 2011 | +0.000 | -0.207 | -0.517 | +0.000 | +0.010 | +0.200 | +0.200 | +1.908 |
| 2012 | +0.000 | -1.282 | -0.526 | +0.000 | +0.002 | -3.741 | -3.741 | +0.243 |
| 2013 | +0.000 | -0.474 | -0.295 | -1.555 | -0.003 | -1.555 | -1.555 | +0.723 |
| 2014 | +0.000 | -0.004 | -0.101 | -0.388 | +0.014 | -0.391 | -0.391 | +0.860 |
| 2015 | +0.000 | -0.394 | -0.085 | -0.903 | -0.059 | +0.000 | +0.000 | +0.623 |
| 2016 | +0.000 | -0.242 | -0.107 | -0.694 | -0.084 | +0.000 | +0.000 | +0.382 |
| 2017 | +0.000 | -0.220 | -0.201 | -0.462 | -0.087 | +0.031 | +0.000 | +0.580 |
| 2018 | +0.000 | -0.268 | +0.005 | -0.176 | -0.128 | -0.559 | +0.000 | +0.765 |
| 2019 | +0.000 | -0.691 | -0.443 | +0.000 | -0.149 | -0.188 | +0.000 | +0.032 |
| 2020 | +0.000 | +0.960 | +1.043 | +0.000 | +0.038 | +1.065 | +0.000 | +3.690 |
| 2021 | +0.000 | +0.988 | +0.791 | +0.000 | +0.249 | +0.000 | +0.000 | +2.925 |
| 2022 | +0.000 | -1.111 | -0.396 | +0.000 | -0.130 | +0.000 | +0.000 | +0.143 |
| 2023 | +0.000 | -0.864 | -0.538 | -1.538 | -0.202 | +0.000 | +0.000 | +0.150 |

## Analyse des mauvaises années (MODEL_SIGNAL < SELL_HARVEST)

| Année | Delta USD/bu | Capture rate |
|---:|---:|---:|
| 2023 | -0.202 | 92.8% |
| 2019 | -0.149 | 95.2% |
| 2022 | -0.130 | 96.0% |
| 2018 | -0.128 | 79.5% |
| 2017 | -0.087 | 82.8% |
| 2016 | -0.084 | 87.5% |
| 2015 | -0.059 | 83.7% |
| 2010 | -0.019 | 70.5% |
| 2013 | -0.003 | 85.4% |

Dans ces années, le modèle a tenu l'inventaire trop longtemps ou a vendu trop tôt. Un marché en tendance baissière prolongée ou une forte hausse initiale manquée sont les causes typiques.

## Interprétation

- `SELL_HARVEST` et `SELL_THIRDS` définissent la baseline réaliste la plus accessible.
- `SELL_MONTHLY` est un DCA (dollar-cost averaging) sur l'année : robuste mais ne profite pas des pics.
- `MODEL_SIGNAL` et `MODEL_STORAGE_VALUE` bénéficient des prédictions calibrées. Un gain vs récolte significatif valide l'utilité pratique du modèle.
- `CQR_CAUTIOUS` est plus conservateur : ne vend que si la borne basse de l'intervalle est négative — réduit les ventes prématurées mais peut manquer la fenêtre de hausse.
- `PERFECT_HINDSIGHT` est irréalisable et sert uniquement à mesurer le *regret* théorique maximum de chaque stratégie.
