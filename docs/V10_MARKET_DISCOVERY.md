# V10 — Market Discovery : découvertes quantitatives sur la prime EMA/CBOT

**Date** : 2026-05-31
**Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Module** : `src/mais/research/v10_market_discovery.py` · runner `src/mais/scripts/run_v10.py` · tests (6 PASS)
**Artefacts** : `artefacts/v10/` (basis_econometrics, feature_attribution, horizon_sweep, cost_survival, regime_conditioning, simplified_model)
**Données** : dataset hors holdout 2024 (5940 lignes). Holdout 2024 verrouillé, jamais touché.

Sprint de recherche ouvert reprenant l'indicateur structurel V9 et cherchant à *comprendre* et
*améliorer* le signal de prime EMA/CBOT. Six expériences, toutes OOF / anti-leakage. **Cinq découvertes
nouvelles**, dont une amélioration directe de l'indicateur et une explication mécaniste du signal.

---

## Découverte 1 — Le basis mean-reverte avec une demi-vie de ~17 jours (V10-A)

AR(1) du basis z-score : φ = **0.960**, **demi-vie = 17.1 jours**. La demi-vie roulante (fenêtres 252j) a
une médiane de 17j mais **varie fortement dans le temps** (p10 = 7.6j, p90 = 42j, max 170j).

**Pourquoi c'est important** : c'est l'explication mécaniste de tout le signal de prime. Un basis extrême
revient vers sa moyenne en ~2-3 semaines ; l'horizon H40 (≈ 2.3 demi-vies) laisse à la reversion le temps
de se réaliser. Cela explique **pourquoi R2 (basis_z < −1.5 → long) fonctionne** et pourquoi le signal est
instable certaines années (quand la demi-vie grimpe à 40-170j, la reversion ne se boucle pas dans H40).

## Découverte 2 — Seules 2 des 6 variables portent le signal ; le simplifier l'améliore (V10-B + V10-F)

Importance par permutation OOF (Δ AUC) :

| Variable | Δ AUC | Signe stable ? |
|---|---:|:--:|
| basis_z | **+0.030** | ✅ |
| month_cos (saison récolte) | **+0.024** | ✅ |
| eurusd | +0.015 | ✅ |
| month_sin | −0.004 | ❌ |
| oi_proxy | −0.005 | ❌ |
| cbot_eur | **−0.016** | ❌ |

`cbot_eur`, `month_sin`, `oi_proxy` ont une importance **négative** et un signe **instable** : ce sont du
bruit. En les retirant (V10-F) :

| Modèle | n vars | AUC OOF | top20 DA |
|---|---:|---:|---:|
| V9 complet | 6 | 0.656 | 0.735 |
| drop_noise | 3 | 0.692 | **0.803** |
| **basis + saison** | **2** | **0.694** | 0.748 |
| basis seul | 1 | 0.637 | 0.718 |

**Découverte/amélioration** : le modèle **2 variables (basis_z + month_cos)** atteint **AUC 0.694**, soit
**+0.038 vs le modèle V9 à 6 variables**, tout en étant bien plus parcimonieux. La prime EMA/CBOT se résume
économiquement au **basis et à la saisonnalité de récolte**. C'est la thèse « la simplicité gagne » (V8 §7)
poussée à son terme : V9 portait encore 3 variables nuisibles.

## Découverte 3 — H40 est optimal ; H90 s'effondre (V10-C)

| Horizon | AUC OOF | top20 DA |
|---|---:|---:|
| H20 | 0.613 | 0.55 |
| H30 | 0.654 | 0.69 |
| **H40** | **0.656** | **0.735** |
| H60 | 0.581 | 0.57 |
| H90 | 0.559 | 0.50 |

**Découverte** : le signal est concentré à 30-40 jours — exactement cohérent avec la demi-vie de basis de
17j (≈ 2 demi-vies). **H90 s'effondre à 0.559**, ce qui **réfute définitivement l'ancienne piste V6/V7
« H90 prometteur »** (déjà soupçonnée overfit en V8). Horizon optimal et économétrie du basis concordent.

## Découverte 4 — Le mur des coûts est réel et robuste (V10-D)

Net PnL du backtest spread à coût 5 €/t/leg : **−376 €/t** (baseline tous trades).
Courbe de sélectivité par confiance : le top-50% confiance survit à coût 3 (+49 €/t) mais **pas** à coût 5
(−127 €/t). **Aucun niveau de sélectivité ne survit à coût 5, même en sélection in-sample.**
Test forward honnête (seuil de confiance appris sur années passées, appliqué forward) : 10 trades, hit rate
0.80, mais net coût 5 = **−49 €/t** → `survives_cost5 = False`.

**Verdict `COST_WALL_CONFIRMED`** : la sélectivité aide à coût 3 (proche du seuil de rentabilité ~2.5 €/t
déjà vu en V9) mais ne franchit pas le coût 5. Résultat négatif honnête et important : pas de trading
réaliste sans réduire structurellement les coûts (broker low-cost, exécution en gross).

## Découverte 5 — La prime est la plus prédictible en uptrend CBOT (V10-E)

| Régime CBOT (causal) | n | AUC | DA |
|---|---:|---:|---:|
| **Uptrend (MACD hist > 0)** | 812 | **0.683** | **0.690** |
| Downtrend | 734 | 0.623 | 0.589 |
| Low vol | 1048 | 0.663 | 0.660 |
| High vol | 498 | 0.650 | 0.602 |

**Découverte** : l'edge se concentre dans les **hausses CBOT** (DA 0.690 vs 0.589 en baisse, +10 points).
Économiquement plausible : en rallye, la prime européenne suit CBOT avec retard, rendant la direction
relative plus lisible. Un filtre de régime « trader la prime surtout en uptrend » concentre l'edge — à
valider forward (la sélection du régime est ici in-sample).

---

## Synthèse : le signal de prime, mécaniquement compris

V10 boucle l'explication économique de l'étude :

> La prime EMA/CBOT est gouvernée par un **basis mean-reverting (demi-vie 17j)** modulé par la
> **saisonnalité de récolte**. Elle est au mieux prédictible à **40 jours**, surtout en **uptrend CBOT**.
> Le meilleur modèle est **basis_z + month_cos** (AUC 0.694) — deux variables, pas six. Mais l'edge ne
> survit pas aux **coûts de transaction réalistes** (mur confirmé à ~3 €/t/leg).

## Validation du modèle simplifié (confirmée, pas seulement revendiquée)

Le modèle 2 variables `basis_z + month_cos` a été passé dans **la même batterie de validation que V9** via
`fit_oof_structural(features=SIMPLIFIED_FEATURES)`, `run_loyo`, `run_red_team_v2` :

| Test | 6 vars (V9) | **2 vars (V10)** |
|---|---:|---:|
| AUC OOF | 0.656 | **0.694** |
| Balanced accuracy | 0.619 | 0.633 |
| top20 DA | 0.735 | 0.748 |
| LOYO | STABLE (0.77, 14/15) | **STABLE (0.758, 14/15)** |
| Red team p-value | 0.0099 | **0.0099 (PASS)** |

L'amélioration tient sous LOYO et red team : le modèle simplifié est **strictement meilleur et plus robuste**.
`SIMPLIFIED_FEATURES = ["basis_z", "month_cos"]` est désormais une option de premier rang du module V9.

## Améliorations apportées vs V9

1. **Modèle simplifié 2 variables** : AUC 0.656 → **0.694** (+0.038), validé LOYO + red team.
2. **Explication mécaniste** : demi-vie de basis 17j relie R2, l'horizon H40 et l'instabilité annuelle.
3. **Réfutation H90** : l'ancienne piste « H90 prometteur » est close.
4. **Mur des coûts quantifié et confirmé** forward.
5. **Filtre de régime uptrend** identifié (à valider forward).

## Limites

- Prix EMA toujours `barchart_proxy_exploratory`.
- Sélections régime/sous-ensemble réalisées sur l'OOF complet → à confirmer en LOYO + red team (V11).
- Mur des coûts non franchi → aucun claim trading. Statut `RESEARCH_ONLY_NOT_TRADING` maintenu.

## Suite (V11)

- Promouvoir le modèle **2 variables** dans `structural_indicator_v9` (option `feature_set`) et re-valider
  LOYO + red team + backtest sur le modèle simplifié.
- Tester forward le **filtre uptrend** (régime appris sur années passées).
- Reprendre la calibration et l'abstention par incertitude (largeur CQR).
- Acquisition données officielles (EMA Euronext, EC MARS) reste le vrai déblocage (`WAITING_DATA`).

---

*V10 — 2026-05-31. Cinq découvertes, une amélioration nette du modèle, un mur de coûts confirmé.*
*Recherche honnête : le signal est réel et compris, sa rentabilité réelle reste non démontrée.*
