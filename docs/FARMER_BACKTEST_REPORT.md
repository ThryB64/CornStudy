# Backtest agriculteur

## Hypothèses

- Horizon décision : J+20
- État/profil : `iowa`
- Période : `2010-2023` (14 saisons)
- Basis local : -0.20 USD/bu
- Coût stockage : 0.04 USD/bu/mois
- Perte qualité : 0.50%/mois
- Inventaire simulé : 50,000 bu, métriques ramenées en USD/bu
- Source modèle : prédictions calibrées professional_study
- Source CQR : cqr_results.parquet

## Résumé stratégies

| Stratégie | Prix net USD/bu | Capture rate | Gain vs récolte | Sharpe gain | Années > récolte | Max drawdown | N |
|---|---:|---:|---:|---:|---:|---:|---:|
| `SELL_HARVEST` | 4.576 | 82.8% | +0.000 | 0.00 | 0.0% | 0.000 | 14 |
| `MODEL_SIGNAL` | 4.550 | 82.1% | -0.026 | -0.25 | 35.7% | -0.361 | 14 |
| `BENCHMARK_AVG` | 4.542 | 81.1% | -0.033 | -0.07 | 28.6% | -2.005 | 14 |
| `STORE_3M` | 4.516 | 80.8% | -0.060 | -0.14 | 28.6% | -1.990 | 14 |
| `STORE_6M` | 4.536 | 79.8% | -0.040 | -0.04 | 28.6% | -4.023 | 14 |
| `CQR_OPTIMAL` | 4.174 | 76.3% | -0.402 | -0.40 | 7.1% | -5.735 | 14 |

## Prix net annuel USD/bu

| season | SELL_HARVEST | STORE_3M | STORE_6M | MODEL_SIGNAL | CQR_OPTIMAL | BENCHMARK_AVG |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | 5.430 | 6.012 | 6.894 | 5.411 | 5.339 | 6.112 |
| 2011 | 6.205 | 5.628 | 5.607 | 6.215 | 6.405 | 5.813 |
| 2012 | 7.172 | 6.812 | 5.835 | 7.175 | 3.432 | 6.606 |
| 2013 | 4.235 | 3.963 | 4.443 | 4.232 | 2.680 | 4.214 |
| 2014 | 3.275 | 3.483 | 3.160 | 3.289 | 2.835 | 3.306 |
| 2015 | 3.555 | 3.209 | 3.085 | 3.494 | 3.555 | 3.283 |
| 2016 | 3.340 | 3.279 | 3.117 | 3.256 | 3.340 | 3.246 |
| 2017 | 3.305 | 3.110 | 3.272 | 3.303 | 3.305 | 3.229 |
| 2018 | 3.583 | 3.409 | 3.081 | 3.561 | 3.583 | 3.358 |
| 2019 | 3.732 | 3.520 | 2.780 | 3.584 | 3.732 | 3.344 |
| 2020 | 3.837 | 4.849 | 5.192 | 3.876 | 3.837 | 4.626 |
| 2021 | 5.058 | 5.470 | 7.166 | 5.307 | 5.058 | 5.898 |
| 2022 | 6.635 | 6.428 | 6.123 | 6.505 | 6.635 | 6.395 |
| 2023 | 4.700 | 4.047 | 3.748 | 4.498 | 4.700 | 4.165 |

## Capture rate annuel

| season | SELL_HARVEST | STORE_3M | STORE_6M | MODEL_SIGNAL | CQR_OPTIMAL | BENCHMARK_AVG |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | 70.8% | 78.4% | 89.9% | 70.5% | 69.6% | 79.7% |
| 2011 | 76.5% | 69.4% | 69.1% | 76.6% | 79.0% | 71.7% |
| 2012 | 96.7% | 91.9% | 78.7% | 96.8% | 46.3% | 89.1% |
| 2013 | 85.4% | 79.9% | 89.6% | 85.4% | 54.1% | 85.0% |
| 2014 | 79.2% | 84.2% | 76.4% | 79.5% | 68.6% | 79.9% |
| 2015 | 85.1% | 76.8% | 73.8% | 83.6% | 85.1% | 78.6% |
| 2016 | 89.7% | 88.1% | 83.7% | 87.5% | 89.7% | 87.2% |
| 2017 | 85.1% | 80.0% | 84.2% | 85.0% | 85.1% | 83.1% |
| 2018 | 82.4% | 78.4% | 70.9% | 81.9% | 82.4% | 77.2% |
| 2019 | 99.1% | 93.5% | 73.8% | 95.2% | 99.1% | 88.8% |
| 2020 | 51.0% | 64.4% | 69.0% | 51.5% | 51.0% | 61.5% |
| 2021 | 63.4% | 68.5% | 89.8% | 66.5% | 63.4% | 73.9% |
| 2022 | 97.9% | 94.8% | 90.3% | 96.0% | 97.9% | 94.4% |
| 2023 | 96.9% | 83.5% | 77.3% | 92.8% | 96.9% | 85.9% |

## Lecture

Le capture rate est le prix net obtenu par la stratégie divisé par le meilleur prix cash observé dans la saison. Les coûts de stockage et la perte qualité sont déduits avant le calcul. `BENCHMARK_AVG` est la moyenne mécanique de `SELL_HARVEST`, `STORE_3M` et `STORE_6M`.

`MODEL_SIGNAL` utilise les règles agriculteur avec les prédictions calibrées disponibles. Le résultat est conservé tel quel même si une baseline simple fait mieux : c'est la mesure économique réelle du système à ce stade.
