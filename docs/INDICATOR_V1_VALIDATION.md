# Indicateur selectif de risque V1 - validation walk-forward

Validation hors echantillon (OOS 2014-2025), anti-leakage : refit annuel, purge = horizon entre train et test, standardisation train-only.

## M1 - CBOT Downside Risk (le module le plus credible)

- Cible : baisse de plus de 3 % a H60. AUC = **0.646** (IC95 bootstrap [0.627 ; 0.666]), base rate 0.37, n=2845.
- A H30 : AUC = 0.569 (IC95 [0.546 ; 0.590]).
- Performance PAR ANNEE (extrait) :

| annee | n | base | AUC | DA |
|---|---|---|---|---|
| 2014 | 252 | 0.44 | 0.815 | 0.563 |
| 2015 | 252 | 0.38 | 0.504 | 0.619 |
| 2016 | 250 | 0.26 | 0.740 | 0.744 |
| 2017 | 251 | 0.26 | 0.720 | 0.741 |
| 2018 | 249 | 0.29 | 0.781 | 0.715 |
| 2019 | 252 | 0.41 | 0.672 | 0.690 |
| 2020 | 253 | 0.26 | 0.873 | 0.739 |
| 2021 | 252 | 0.27 | 0.915 | 0.690 |
| 2022 | 251 | 0.38 | 0.542 | 0.554 |
| 2023 | 250 | 0.74 | 0.359 | 0.460 |
| 2024 | 252 | 0.30 | 0.661 | 0.702 |
| 2025 | 81 | 0.68 | 0.622 | 0.457 |

- Confidence Gate / abstention (DA selon la confiance |p-0.5|) :

| confiance min | couverture | DA |
|---|---|---|
| >= 0.00 | 100% | 0.651 |
| >= 0.05 | 88% | 0.668 |
| >= 0.10 | 79% | 0.671 |
| >= 0.15 | 68% | 0.688 |
| >= 0.20 | 56% | 0.711 |

Lecture : agir seulement sur les signaux confiants augmente la DA (de 0.651 sur tous les jours a 0.711 sur les plus confiants), au prix de la couverture.

## M3 - Volatility regime

- Cible : volatilite realisee H20. RMSE modele **0.102** vs baseline persistance 0.120 (-15.1 %), n=2886.

## M4 - Euronext Premium (research-only)

- H60 : basis haut -> retour EMA +3.5 %, basis bas -> +1.4 % (n haut=185, delta basis_z futur -1.83 = reversion).
- H90 : basis haut -> retour EMA +5.7 %, basis bas -> +0.4 % (n haut=185, delta basis_z futur -2.40 = reversion).

RESEARCH_ONLY : prix Euronext ~97 % proxy, couts a integrer (brut/net/+2/+5 EUR/t).

## Statut

V1 valide la THESE : on ne predit pas le prix, mais le risque de baisse et la volatilite sont previsibles hors echantillon, et l'abstention ameliore la qualite. Modules a fusionner ensuite (gate de confiance unique) ; couts reels et placebo etendu restent au backlog.
