# Réflexion complète — Étude Maïs V3
> Document de travail — 2026-05-17 (mis à jour)
> Objectif : tout mettre dans un seul endroit avant de créer les tickets.
> Ne pas encore implémenter. Réfléchir, critiquer, améliorer.
> **Les questions de la Section 17 ont été tranchées. Les tickets suivront.**

---

## Table des matières

1. [État réel du projet — ce qui marche, ce qui ne marche pas](#1-état-réel-du-projet)
2. [Ce que les résultats nous disent économiquement](#2-lecture-économique-des-résultats)
3. [Le problème fondamental : signal faible sur marché efficient](#3-le-problème-fondamental)
4. [Horizon sweep complet J+1 à J+100](#4-horizon-sweep-complet)
5. [Model zoo complet](#5-model-zoo-complet)
6. [Stacking et méta-apprentissage](#6-stacking-et-méta-apprentissage)
7. [Consensus multi-horizon](#7-consensus-multi-horizon)
8. [Réduction de dimension et compression](#8-réduction-de-dimension-et-compression)
9. [Deep learning temporel](#9-deep-learning-temporel)
10. [Multi-task learning](#10-multi-task-learning)
11. [Nouvelles sources de données et features](#11-nouvelles-sources-de-données-et-features)
12. [Calibration probabiliste et correction de la confiance](#12-calibration-probabiliste-et-correction-de-la-confiance)
13. [Architecture de l'indicateur final](#13-architecture-de-lindicateur-final)
14. [Garde-fous contre le p-hacking](#14-garde-fous-contre-le-p-hacking)
15. [Ce qu'on attend vraiment comme amélioration](#15-ce-quon-attend-vraiment)
16. [Ordre logique des expériences](#16-ordre-logique-des-expériences)
17. [Décisions prises — structure des tickets V3](#17-décisions-prises--structure-des-tickets-v3)

---

## 1. État réel du projet

### Ce qui est solide

**Pipeline complet** : collecte → features → facteurs → modèles → CQR → backtest → indicateur. Tout tourne, ruff PASS, 21 tests unitaires PASS.

**Résultats IND-01 à IND-08 honnêtes** :
- DA h20 meilleur ML : **0.624** (out-of-time 2023–2025)
- CQR coverage : **91.7 %** (objectif ≥88 %)
- Top 20 % confiance DA : **0.728**
- Beats baseline saisonnière (0.605) et momentum (0.579)
- Anti-leakage PASS, pas de contamination oracle

**Découvertes importantes** :
- Asymétrie : le modèle détecte mieux les **fortes baisses** que les hausses
- Cible utile réelle : `y_down_gt_5pct_h20` (AUC=0.707)
- Vraies poches de signal : mois=11, stocks_tendus, post_recolte+low_vol
- Familles utiles (delta_auc) : positioning, market_volatility, seasonality, raw_signal, crop_condition

### Ce qui ne marche pas encore

**96.5 % UNCERTAIN sur 2023–2025** : l'indicateur est trop conservateur. La calibration Platt comprime les probabilités vers 0.5, le `prob_distance` devient trop faible, presque tout passe sous le seuil de confiance. Seulement 8.9 signaux directionnels/an pour un objectif de 20.

**Signaux directionnels rares** : 21 BULLISH + 1 BEARISH sur 623 jours = 3.5 % du temps. C'est trop peu pour être exploitable. Les seuils P(up)=0.60 et confidence=0.45 sont trop stricts avec des probabilités calibrées qui s'étalent entre 0.085 et 0.770.

**h30 dominé par la saisonnalité** : à J+30, le meilleur modèle est `baseline_seasonal_naive`. Le ML n'apporte pas grand chose à cet horizon.

**Familles RETIRER questionables** : `weather_belt_stress` et `wasde_supply_demand` ressortent comme RETIRER selon delta_auc, mais ce sont des drivers économiques fondamentaux. Ce résultat contre-intuitif ne signifie pas que ces variables ne valent rien — il signifie que leur forme actuelle (facteur composite z-scoré globalement) n'apporte pas de gain marginal sur la cible `y_down_gt_5pct_h20`, probablement à cause de multicolinéarité ou d'agrégation trop grossière. **Une famille économiquement fondamentale ne peut pas être supprimée sur la seule base d'une ablation globale.** Elle doit être diagnostiquée par horizon, saison, cible et contexte avant toute décision.

**Futures curve absente** : M1/M2/M3 CBOT non disponibles — le facteur curve_structure est un proxy approximatif. Ne pas simuler avec des données insuffisantes.

### Ce qui est suspect et à investiguer

**DA h30 baseline=0.583 vs ML=0.580** : le ML est légèrement en dessous de la saisonnalité à h30. Normal mais mérite analyse : est-ce que le modèle surfit à des patterns en train qui n'existent plus à h30 ?

**AUC ablation de wasde_supply_demand = −0.022** : enlever le facteur WASDE *améliore* l'AUC de 2.2 pts sur `y_down_gt_5pct_h20`. Soit multicolinéarité avec d'autres features, soit facteur composite mal construit pour cette cible. Diagnostic par horizon/cible obligatoire.

**signal_stability = 0.0 dans la formule de confiance** : dans le runner, la stabilité du signal historique est initialisée à 0 en mode batch, ce qui biaise la confiance vers le bas au démarrage. C'est un bug de conception, pas un résultat du marché — à corriger en V3-01.

### Important : statut de la période 2023–2025

**La période 2023–2025 n'est plus un test vierge parfait.** Les résultats IND-08 ont déjà été calculés et utilisés pour diagnostiquer les limites de l'indicateur. Ce qu'on sait déjà :

- DA h20 = 0.624
- Top 20 % confiance = 0.728
- 96.5 % UNCERTAIN
- Flip rate = 0.037

**Implication** : pour la V3, on ne peut pas utiliser ces chiffres pour "valider" l'indicateur amélioré sans biais de sélection.

**Stratégie correcte pour la V3** :

| Période | Rôle |
|---|---|
| 2010–2021 | Train / validation / exploration de toutes les nouvelles idées |
| 2022 | Validation finale des seuils (fixés une fois, non retouchés ensuite) |
| 2023–2025 | Backtest déjà consulté, documenté honnêtement, non réoptimisé |
| 2026+ (production) | Vrai test temps réel — la vraie validation quotidienne |

Cette honnêteté est indispensable pour une étude académique sérieuse.

---

## 2. Lecture économique des résultats

### Ce que le maïs nous dit vraiment

**Le marché du maïs est semi-efficient, pas totalement aléatoire.**

Preuve empirique : DA=0.624 > 0.5, AUC=0.663 > 0.5. Le signal existe. Mais il est faible et conditionnel.

**Les fondamentaux (WASDE, météo) structurent le moyen terme (J+10 à J+20).**

SHAP h5-h20 : top 1 = factor_wasde_supply_demand, top 2 = factor_crop_condition_pressure. Sens économique : stocks/utilisation du WASDE et conditions de culture définissent le biais moyen terme. Cohérent avec la théorie des marchés agricoles.

**Le positionnement spéculatif (COT) amplifie le mouvement sans le créer.**

factor_positioning apparaît dans le top 5 sur tous les horizons. Signal que les fonds suivent le mouvement fondamental, pas qu'ils le créent.

**La macro (dollar, taux) domine le long terme (J+30).**

À h30, SHAP top 1 = factor_macro_dollar_rates. Sur 30 jours, les corrélations dollar-matières premières prennent le dessus sur les fondamentaux agricoles hebdomadaires.

**Le modèle ne détecte pas bien les hausses.**

Asymétrie observée : tous les Tier 1 par AUC > 0.65 sont des cibles de fortes baisses (`y_down_gt_*`). Deux hypothèses :
1. Les baisses sont associées à des chocs d'offre (météo, WASDE baissier) — plus prévisibles car liés à des publications calendaires.
2. Les hausses sont souvent des rebonds sur des nouvelles imprévues (géopolitique, demande surprise) — moins prévisibles.

**Novembre est le meilleur mois (AUC=0.883).**

Novembre est post-récolte américaine. Les stocks de fin de saison sont connus, le prix est fortement contraint par leur niveau. Signal prévisible car le marché a une information très complète.

**Les stocks tendus amplifient le signal.**

`stocks_tendus` : AUC=0.799. Quand le stocks/utilisation est bas (< percentile 25), chaque nouvelle météo ou export compte davantage. Le marché est plus sensible, plus réactif, et probablement plus tendanciel.

---

## 3. Le problème fondamental

### Pourquoi le signal est faible

Le maïs est une **commodity internationale** traitée par des algorithmes professionnels, des fonds quantitatifs, des traders céréaliers intégrés (Cargill, ADM). Ces acteurs ont accès à :
- Des données météo satellites haute résolution
- Des images satellite de végétation (NDVI)
- Des flux export en temps réel
- Des positions COT avant leur publication publique
- Des modèles de récolte propriétaires

Notre dataset est entièrement public. On ne peut donc pas s'attendre à des prédictions massives. C'est structurellement limité.

**Ce qu'on peut raisonnablement attendre avec des données publiques :**

| Scénario | DA globale | DA top 20% | AUC |
|---|---|---|---|
| Faible mais réel | 55–58 % | 60–65 % | 0.55–0.60 |
| Bon | 58–62 % | 65–70 % | 0.60–0.65 |
| Très bon | 62–66 % | 70–75 % | 0.65–0.70 |
| Excellent (rare) | >66 % | >75 % | >0.70 |

On est actuellement à **Bon** sur la période de test. C'est honnête.

### Diagnostic prioritaire : signal_stability = 0.0

Dans le runner actuel (mode batch), la stabilité du signal historique est initialisée à `signal_stability = 0.0`.

**Conséquence directe** : dans la formule confidence_v1, la composante signal_stability pèse 20 %. Initialiser à 0 déprime systématiquement la confiance de ~12 points de base sur chaque observation en début de série ou en mode batch.

Ce n'est pas un résultat du marché. C'est un bug de conception.

**Correction attendue** :
- Option A : calculer signal_stability progressivement sur une fenêtre glissante (ex. 5j précédents).
- Option B : initialiser à 0.5 (neutre) plutôt qu'à 0 (pessimiste).
- Option C : exclure signal_stability du calcul si la fenêtre disponible est insuffisante (< 5j).

Ce bug participe directement au problème 96.5 % UNCERTAIN. Il est listé en **V3-01, priorité absolue**.

### Ce qui peut vraiment améliorer le signal

Par ordre d'impact attendu :

1. **Corriger les bugs de confiance** — signal_stability = 0.0, Platt trop compressif, seuils trop stricts.
2. **Horizon sweep** — trouver le vrai pic de prédictibilité plutôt que supposer J+20.
3. **Consensus multi-horizon** — réduire le bruit d'un horizon isolé, passer de "J+20 dit 62 %" à "la zone J+15-J+30 est majoritairement haussière".
4. **Meilleure construction des facteurs** — les facteurs composites actuels sont parfois trop agrégés. Décomposer, z-scorer individuellement, mieux aligner temporellement.
5. **Contextes conditionnels** — concentrer les signaux sur les périodes connues pour être prédictibles.
6. **Sources manquantes** — futures curve, Crop Progress hebdo, données export FAS.
7. **Stacking** — combiner plusieurs modèles réduit la variance.

Ce qui n'améliorera probablement pas beaucoup :
- LSTM / Transformer avec 6000 lignes : risque de surapprentissage dépasse le gain
- Features très complexes si elles reproduisent des features existantes
- Trop de modèles dans l'ensemble final (>5-7 modèles = rendements décroissants)

---

## 4. Horizon sweep complet

### Objectif

Cartographier rigoureusement la prédictibilité du maïs de J+1 à J+100. Ne pas supposer que J+20 est optimal. Le prouver ou l'infirmer.

### Grille d'horizons à tester

```
Court terme exact  : J+1, J+2, J+3, J+4, J+5
Court terme         : J+7, J+10, J+12, J+15
Moyen terme dense   : J+18, J+20, J+22, J+25, J+28, J+30
Transition          : J+35, J+40, J+45
Long terme          : J+50, J+60, J+70, J+80
Très long terme     : J+90, J+100
```

Total : **24 horizons**. Pas tous les jours jusqu'à J+100 (trop coûteux), mais assez dense pour voir la courbe et détecter un plateau ou un pic.

**Justification des horizons intermédiaires (J+18, J+22, J+28)** : si J+20 est un pic isolé avec J+18 et J+22 mauvais, c'est du hasard. Si la zone J+18-J+28 est cohérente, c'est un vrai signal. Les intermédiaires permettent de distinguer les deux cas.

### Métriques par horizon

Pour chaque horizon h :
- DA (direction accuracy)
- AUC (vs baseline 0.5)
- Brier score
- RMSE (si cible continue)
- DA top 20 % confiance
- n_obs_test (doit être ≥ 100 pour être pris au sérieux)
- DA saisonnier à même horizon (comparatif obligatoire)
- DA momentum à même horizon
- Écart DA ML vs saisonnier
- Fréquence signaux forts (|P(up) - 0.5| > 0.1)

### Forme de courbe attendue et interprétation

```
DA
 │
70%├──                           ╭──
   │                           ╭╯
65%│                          ╱
   │                        ╱
60%│               ╭────╮ ╱
   │              ╱      ╲
55%│            ╱          ╲──────────
   │          ╱
50%┼──────╮╱
   └──────┬──────────────────────────→ Horizon
        J+5  J+20  J+30  J+60  J+100
```

Ce qu'on cherche :
- **Pic unique** : par exemple J+20 clairement meilleur → simple à justifier
- **Plateau** : J+15 à J+35 tous bons → zone robuste, indicateur sur cette zone
- **Pas de signal** : courbe plate autour de 50-55 % → marché très efficient sur cet horizon
- **Signal long terme** : J+60+ bons → saisonnalité structurelle forte

### Garde-fous pour ne pas conclure trop vite

**Règle de la zone** : un horizon n'est retenu que si ses voisins ±3 horizons sont aussi bons. J+27 isolé avec J+24 et J+30 mauvais = hasard. La zone J+22-J+32 cohérente = signal réel.

**Règle de cohérence** : la performance doit tenir sur chaque split de validation, pas juste en moyenne.

**Règle de la baseline** : l'horizon doit battre `baseline_seasonal_naive` d'au moins 2 pts DA. Sinon le ML n'apporte rien que la saisonnalité.

**Règle de n_obs** : plus l'horizon est long, moins on a d'observations indépendantes (overlapping returns). Pour J+60, on n'a que ~40 périodes indépendantes sur 10 ans. C'est très peu. Documenter systématiquement.

### Ce que l'horizon sweep change dans l'indicateur

Si le sweep révèle que la zone J+15 à J+35 est robuste, l'indicateur devient :

```
"Le maïs présente un biais haussier cohérent sur J+15 à J+35"
```

C'est beaucoup plus fort que :

```
"Le modèle J+20 dit 62 %"
```

---

## 5. Model zoo complet

### Philosophie

Ne pas entraîner 30 modèles pour garder le meilleur. Entraîner pour apprendre ce que chaque famille capture. Le zoo sert à :

1. Identifier les familles de modèles qui capturent des signaux différents (pour le stacking)
2. Comprendre la robustesse du signal (si seulement LGBM marche, le signal est fragile)
3. Trouver des modèles calibrés nativement (pour éviter le post-processing Platt/Isotonic)

**Maximum 5–7 modèles dans l'ensemble final.** Au-delà, les rendements sont décroissants.

### Famille 1 : Linéaires

| Modèle | Forces | Faiblesses |
|---|---|---|
| Ridge | Stable, interprétable | Linéaire seulement |
| Lasso | Sélection de variables | Instable si corrélations |
| ElasticNet | Compromis Ridge/Lasso | À tuner |
| Logistic Regression | Probabilités propres | Linéaire |
| BayesianRidge | Incertitude naturelle | Moins rapide |

**Ce qu'on attend** : DA 55–62 %. Les modèles linéaires sont souvent très compétitifs si les facteurs sont bien construits (ce qui est notre cas). Baseline solide pour le stacking.

**Note importante** : sur les facteurs composites (déjà agrégés et z-scorés), Ridge peut battre LGBM. Les non-linéarités sont déjà capturées au niveau feature.

### Famille 2 : Arbres et boosting

| Modèle | Forces | Faiblesses |
|---|---|---|
| RandomForest | Robuste, peu d'overfitting | Lent à tuner |
| ExtraTrees | Plus rapide que RF | Légèrement moins précis |
| HistGradientBoosting | Rapide, gère NaN | Hyperparamètres |
| LightGBM | Excellent sur tabulaire | Overfitting si mal tunné |
| XGBoost | Solide, bien documenté | Plus lent que LGBM |
| CatBoost | Gère catégorielles | Très lent à tuner |

**Ce qu'on attend** : DA 58–65 %. Ces modèles captent les non-linéarités et interactions.

### Famille 3 : Probabilistes et bayésiens

| Modèle | Forces | Faiblesses |
|---|---|---|
| Naive Bayes | Simple, calibré | Suppose indépendance |
| Logistic + calibration | Probabilités propres | Linéaire |
| Gaussian Process Classifier | Incertitude naturelle | Lourd O(n³) |

**Ce qu'on attend** : DA 53–58 %. Moins performants en DA, mais utiles pour calibration et diversité du stacking.

### Famille 4 : SVM

| Modèle | Forces | Faiblesses |
|---|---|---|
| LinearSVM | Rapide, solide | Pas de probabilités directes |
| RBF SVM | Non-linéaire | Très lent sur 6000+ lignes |

**Note** : avec 6000 lignes, RBF SVM est O(n²) en mémoire → à tester uniquement sur features réduites (PCA ou facteurs composites uniquement).

### Famille 5 : Réseaux de neurones tabulaires

| Modèle | Forces | Faiblesses |
|---|---|---|
| MLP simple (2 couches) | Non-linéaire, flexible | Overfitting, lent à tuner |
| MLP avec BatchNorm + Dropout | Plus robuste | Encore plus à tuner |

**Ce qu'on attend** : DA 56–62 %. Peut faire aussi bien que LGBM sur tabulaire, rarement mieux avec peu de données. Utile pour diversité.

### Famille 6 : Méthodes d'ensemble simples (non-ML)

| Méthode | Principe |
|---|---|
| Vote majoritaire simple | 1 si majorité des modèles > 0.5 |
| Moyenne des probabilités | mean(P(up)) des modèles |
| Stacking Ridge | Ridge sur OOF predictions |
| Stacking LGBM | LGBM sur OOF predictions |
| Borda count | Rang des prédictions, pas valeur absolue |

Vote et moyenne simples souvent compétitifs avec stacking complexe. Toujours inclure ces baselines dans le zoo.

### Protocole de comparaison

Même protocole walk-forward pour tous les modèles :
- 5 splits minimum
- Embargo = horizon H
- Métriques : DA, AUC, Brier, RMSE, DA_top20pct
- Comparaison systématique à seasonal_naive et momentum_20d
- n_obs_test affiché pour chaque résultat

### Candidats probables pour l'ensemble final

- 1 modèle linéaire (Ridge ou ElasticNet) — stable, interprétable
- 1 modèle boosting (LGBM ou XGB) — non-linéaire
- 1 modèle ensemble (RF ou ExtraTrees) — diversité
- 1 modèle de calibration (Logistic Regression) — probabilités propres
- Éventuellement 1 modèle séquentiel si vraie amélioration documentée

---

## 6. Stacking et méta-apprentissage

### Pourquoi le stacking est important ici

Chaque modèle capte quelque chose de différent :
- Ridge : combinaison linéaire des facteurs
- LGBM : interactions non-linéaires
- RF : structure d'ensemble stable
- Logistic : signal probabiliste calibré

Le méta-modèle apprend **quand faire confiance à quel modèle**.

### Architecture complète du stacking

**Niveau 0 — Modèles de base** (par horizon h)

```
features/facteurs → ridge_h → pred_ridge_h (OOF)
features/facteurs → lgbm_h  → pred_lgbm_h  (OOF)
features/facteurs → rf_h    → pred_rf_h    (OOF)
features/facteurs → xgb_h   → pred_xgb_h   (OOF)
features/facteurs → elnet_h → pred_elnet_h (OOF)
features/facteurs → seasonal → pred_seasonal_h (baseline)
features/facteurs → momentum → pred_momentum_h (baseline)
```

**Niveau 1 — Features méta** (entrées du méta-modèle)

```
Prédictions modèles h20 :
  pred_ridge_h20, pred_lgbm_h20, pred_rf_h20, pred_xgb_h20

Prédictions autres horizons :
  pred_lgbm_h10, pred_lgbm_h15, pred_lgbm_h25, pred_lgbm_h30

Méta-features contextuelles (calculées sans leakage) :
  confidence_proxy_h20       (|P - 0.5| × 2)
  cqr_width_h20              (incertitude CQR)
  horizon_disagreement       (std des prédictions multi-horizon)
  season                     (mois → saison)
  regime_current             (bull/bear)
  vol_bucket                 (low/normal/high)
```

**Niveau 2 — Méta-modèles**

```
Tester :
  logistic_meta      (simple, calibré)
  ridge_meta         (stable)
  lgbm_meta          (non-linéaire sur les méta-features)
  weighted_average   (weights = AUC historique par modèle)
  voting             (majorité simple)
```

### Protocole anti-leakage strict pour le stacking

**Règle absolue** : les OOF predictions du niveau 0 doivent être produites par un modèle qui n'a JAMAIS vu les données du fold de test.

Protocole strict :
```
Pour fold k :
  train_folds = {0, 1, ..., k-1}
  test_fold   = {k}

  modèle entraîné sur train_folds seulement
  prédictions sur test_fold → OOF_k

OOF final = concat(OOF_1, OOF_2, ..., OOF_K)
méta-modèle entraîné sur OOF final
```

**Interdit** :
- Modèle entraîné sur toute la série → prédit sur toute la série
- Utiliser les prédictions in-sample comme méta-features

Le méta-modèle ne voit jamais les données de 2023–2025.

### Multi-horizon stacking

Le méta-modèle reçoit les prédictions de **plusieurs horizons** comme features, pas seulement h20.

```
pred_h5   }
pred_h10  }  → méta-modèle  → signal final
pred_h15  }
pred_h20  }
pred_h30  }
```

Avantage : le méta-modèle apprend la structure temporelle. Si h10, h15, h20 sont tous bullish, le signal est plus fort que si seulement h20 l'est.

### Ce qu'on attend du stacking

| Métrique | Individuel | Stacking attendu |
|---|---|---|
| DA globale | 0.624 | 0.630–0.645 |
| DA top 20% | 0.728 | 0.740–0.760 |
| AUC | 0.663 | 0.670–0.690 |
| Flip rate | 0.037 | 0.030–0.050 |
| Brier | 0.2358 | 0.220–0.230 |

Le gain est **modeste mais réel**. Le stacking réduit la variance et améliore la calibration. Il ne transforme pas un signal faible en signal fort.

---

## 7. Consensus multi-horizon

### Pourquoi c'est probablement la meilleure idée de ce document

**Décision prise (Q5)** : le consensus multi-horizon sera intégré à l'indicateur principal V3, pas laissé en expérience exploratoire. Il doit être testé sur 2010–2022, validé sur les métriques (DA top 20 %, AUC, fréquence signaux, flip rate), puis intégré si le gain est confirmé.

Un signal sur un seul horizon = un point de vue.
Un signal cohérent sur plusieurs horizons = une structure.

La vraie phrase professionnelle devient :

> "Le marché présente un biais haussier cohérent sur la zone J+15 à J+30."

C'est beaucoup plus crédible que :

> "Le modèle J+20 prédit une hausse."

### Méthode 1 : Vote simple pondéré

Pour chaque date t :

```python
horizons_actifs = [h for h in [5, 10, 15, 20, 25, 30] if P_up[h] is not None]

votes_bullish  = sum(1 for h in horizons_actifs if P_up[h] > 0.50)
votes_bearish  = sum(1 for h in horizons_actifs if P_up[h] < 0.50)
votes_total    = len(horizons_actifs)

bullish_ratio  = votes_bullish / votes_total
bearish_ratio  = votes_bearish / votes_total
```

Seuils à tester :
```
bullish_ratio > 0.70 → BULLISH modéré
bullish_ratio > 0.85 → BULLISH fort
bullish_ratio > 0.95 → BULLISH très fort (tous les horizons d'accord)
```

### Méthode 2 : Vote pondéré par fiabilité historique

```python
# Poids = AUC historique de chaque horizon (calculé en train/val uniquement)
weights = {5: 0.55, 10: 0.58, 15: 0.60, 20: 0.66, 25: 0.63, 30: 0.59}

weighted_score = sum(P_up[h] * weights[h] for h in horizons_actifs)
               / sum(weights[h] for h in horizons_actifs)
```

Avantage : J+20 (AUC=0.66) pèse davantage que J+5 (AUC=0.55).

### Méthode 3 : Zones d'horizons

| Zone | Horizons | Sens économique |
|---|---|---|
| Z1 — Court terme | J+1 à J+7 | Réactions immédiates, COT, technique |
| Z2 — Sous-mensuel | J+8 à J+15 | Entre deux WASDE, météo court terme |
| Z3 — Mensuel | J+16 à J+30 | Cycle WASDE, saison culturale |
| Z4 — Bimensuel | J+31 à J+45 | Transition saison/hors saison |
| Z5 — Trimestriel | J+46 à J+70 | Tendance saisonnière, macro |
| Z6 — Long terme | J+71 à J+100 | Macro pur, peu exploitable |

Pour chaque zone :
```python
zone_prob_up       = mean([P_up[h] for h in zone])
zone_agreement     = proportion bullish dans la zone
zone_confidence    = mean([confidence[h] for h in zone])
zone_label         = BULLISH si zone_prob_up > 0.58 ET zone_agreement > 0.65
```

### Méthode 4 : Pente de la courbe des probabilités

```python
horizon_array = [5, 10, 15, 20, 25, 30]
prob_array    = [P_up[h] for h in horizon_array]
slope = np.polyfit(horizon_array, prob_array, 1)[0]
```

| Pente | Forme | Sens |
|---|---|---|
| slope > +0.01 | Hausse avec l'horizon | Signal qui se construit |
| slope < −0.01 | Baisse avec l'horizon | Signal court terme → s'estompe |
| |slope| < 0.005 | Plate | Signal stable ou absent |

### Méthode 5 : Stabilité locale autour de l'horizon principal

```python
local_horizons = [15, 18, 20, 22, 25]
local_bullish  = sum(1 for h in local_horizons if P_up[h] > 0.55)
local_ratio    = local_bullish / len(local_horizons)

# Signal h20 confirmé seulement si les voisins confirment
h20_confirmed = (P_up[20] > 0.60) and (local_ratio > 0.65)
```

### Méthode 6 : Désaccord comme signal de prudence

```python
disagreement = std([P_up[h] for h in horizons_actifs])

# h5=0.62, h10=0.60, h20=0.65, h30=0.61 → std=0.02 → accord élevé
# h5=0.55, h10=0.65, h20=0.48, h30=0.70 → std=0.09 → désaccord fort → UNCERTAIN
```

Si `disagreement > 0.08` → réduire la confiance de 20 %, ou forcer UNCERTAIN.

### Score de consensus unifié

```python
consensus_score = (
    0.40 * weighted_vote_score           # vote pondéré par AUC
    + 0.25 * local_agreement_h20         # cohérence autour de J+20
    + 0.20 * (1 - horizon_disagreement)  # pénalité désaccord
    + 0.15 * (horizon_slope + 1) / 2    # biais de pente (normalisé [0,1])
)
# 0 = pas de consensus, 1 = consensus parfait
```

Ce score remplace ou complète le `confidence_v1` actuel comme composante centrale de la décision de signal.

---

## 8. Réduction de dimension et compression

### PCA — Analyse en Composantes Principales

**PCA par famille** (la plus intéressante) :

Au lieu d'une PCA globale sur toutes les features, faire une PCA séparée par famille :

```python
# Famille météo : 200+ colonnes → 5-10 composantes
pca_meteo = PCA(n_components=8, explained_variance_threshold=0.90)
features_meteo_compressed = pca_meteo.fit_transform(meteo_cols)

# Famille WASDE : 50+ colonnes → 5 composantes
pca_wasde = PCA(n_components=5, explained_variance_threshold=0.90)
features_wasde_compressed = pca_wasde.fit_transform(wasde_cols)
```

**Protocole** : PCA fittée sur train/validation uniquement. Jamais sur 2023–2025.

**Nombre de composantes** : coude de la variance expliquée. Garder le nombre qui explique 85-95 % de la variance intra-famille.

**À comparer avec** : facteurs composites actuels. Si la PCA par famille fait aussi bien, cela valide l'approche factorielle. Sinon, cela indique que nos agrégations perdent de l'information.

### Autoencoder

```
features (300) → encodeur → latent (16/32) → décodeur → features (300)
```

On garde uniquement l'encodeur en production. Avec 6000 lignes, overfitting possible — train/val/test séparés obligatoires.

Alternative : Sparse Autoencoder (régularisation L1 pour forcer la parcimonie).

### Compressive Sensing

**Décision prise (Q4)** : expérience académique sérieuse, pas piste prioritaire de performance. À faire pour enrichir le rapport académique, mais pas attendu comme gain majeur de DA.

Si le signal du maïs est sparse dans un sous-espace de basse dimension, une projection aléatoire conserve l'information :

```python
Phi = np.random.randn(n_compressed, n_features) / np.sqrt(n_compressed)
X_compressed = X @ Phi.T
```

Question légitime : "est-ce que l'information du marché du maïs est sparse ?" Défendable dans un rapport académique.

**Résultat attendu** : probablement similaire à PCA en DA, mais avec un cadre théorique différent.

---

## 9. Deep learning temporel

### Contexte et attentes réalistes

**Décision prise (Q3)** : priorité au tabulaire bien fait. Deep learning en exploratoire V3 tardif, uniquement si tabulaire + stacking + consensus sont stabilisés.

**Ce qu'on a** : ~6000 observations journalières. Trop peu pour que les modèles séquentiels complexes brillent.

**Ordre d'exploration** :
1. MLP tabulaire bien régularisé (référence DL)
2. GRU sur séquence 30j → si gain > 1 pt DA, continuer
3. TCN → si gain supplémentaire, continuer
4. LSTM / Transformer seulement si les précédents sont stables

### MLP tabulaire amélioré

```python
model = MLP(
    hidden_layers=[256, 128, 64, 32],
    dropout=0.30,
    batch_norm=True,
    activation='relu',
    output='sigmoid'
)
```

Souvent aussi bon que LSTM sur données tabulaires. C'est la référence à battre.

### GRU (préféré au LSTM)

```
GRU(32 units, 1 couche) + Dense(1) + Sigmoid
```

Pour données financières de taille modeste, GRU est préférable à LSTM (moins de paramètres, aussi bon, plus rapide).

### Temporal Convolutional Network (TCN)

```python
TCN(nb_filters=32, kernel_size=3, dilations=[1, 2, 4, 8, 16], dropout=0.25)
```

Champ réceptif large avec peu de paramètres. Souvent meilleur que LSTM sur séquences financières.

### Transformer léger

Risqué avec 6000 lignes. À tester en dernier, sans attente de miracle.

### Critère de rétention pour tout modèle DL

- Bat le MLP tabulaire d'au moins 1 pt DA
- Stable sur plusieurs seeds/runs (faible variance)
- Converge proprement (loss décroissante)

Un modèle DL n'est gardé dans l'ensemble que s'il satisfait ces trois critères.

---

## 10. Multi-task learning

### Principe

Entraîner un seul modèle pour prédire plusieurs horizons simultanément.

```
features → shared_layers → [head_h5, head_h10, head_h15, head_h20, head_h25, head_h30]
```

La couche partagée apprend une représentation commune du marché.

### Pourquoi c'est pertinent ici

Les horizons ne sont pas indépendants. Si le signal est bullish à J+20, il l'est probablement aussi à J+18 et J+22. Un modèle multi-task impose cette cohérence implicitement.

Partager les couches régularise naturellement : le modèle ne peut pas overfitter à un horizon sans cohérence avec les autres.

### Architecture MLP multi-task

```python
class MultiHorizonMLP(nn.Module):
    def __init__(self, n_features, horizons):
        self.shared = nn.Sequential(
            nn.Linear(n_features, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.2),
        )
        self.heads = nn.ModuleDict({
            f'h{h}': nn.Sequential(nn.Linear(64, 1), nn.Sigmoid())
            for h in horizons
        })

    def forward(self, x):
        shared = self.shared(x)
        return {f'h{h}': head(shared) for h, head in self.heads.items()}
```

### Fonction de perte pondérée

```python
losses = {
    'h5':  bce_loss(pred_h5,  y_h5)  * 0.10,
    'h10': bce_loss(pred_h10, y_h10) * 0.15,
    'h15': bce_loss(pred_h15, y_h15) * 0.20,
    'h20': bce_loss(pred_h20, y_h20) * 0.30,  # horizon principal
    'h25': bce_loss(pred_h25, y_h25) * 0.15,
    'h30': bce_loss(pred_h30, y_h30) * 0.10,
}
total_loss = sum(losses.values())
```

### Alternative rapide : MultiOutputClassifier

```python
from sklearn.multioutput import MultiOutputClassifier
clf = MultiOutputClassifier(LGBMClassifier(...))
clf.fit(X, Y)  # Y = [y_h5, y_h10, y_h20, y_h30]
```

Limitation : ne partage pas les paramètres (chaque modèle est indépendant). Bonne baseline rapide.

---

## 11. Nouvelles sources de données et features

### Statut actuel des collecteurs partiels

**Crop Progress NASS** : collecteur existant mais partiel. Rapport hebdomadaire chaque lundi de mai à novembre. Variable `crop_condition_change_4w` identifiée comme driver HIGH dans l'oracle analysis (IND-03, +3.5 pts DA). À compléter.

**Drought Monitor USDM** : collecteur non câblé. Données hebdomadaires de sécheresse par région (D0 à D4 sur le Corn Belt). Source : drought.unl.edu (accès libre, format CSV disponible). À implémenter.

**Export Sales USDA FAS** : collecteur existant mais bloqué sur `FAS_API_KEY` non fournie. Gratuit à demander à l'USDA. Données hebdomadaires d'export par destination. À activer.

**Futures CBOT M2/M3** : non disponibles proprement. Si données historiques fiables disponibles → implémenter. Si données incomplètes ou bricolées → ne pas simuler. Ticket de diagnostic d'abord, intégration seulement si qualité suffisante.

### Sources manquantes moins prioritaires

**Open Interest CBOT** : volume et open interest sur les contrats maïs. Proxy de participation du marché. Source : barchart ou calcul depuis CFTC.

**Indices satellitaires NDVI/NDWI** : état de la végétation sur le Corn Belt via MODIS ou Landsat (Google Earth Engine, gratuit). Nécessite un traitement géospatial complexe. Très long terme.

### Features à améliorer

**Surprises WASDE décomposées** :
- Séparer par composant (yield_surprise vs production_surprise vs stocks_surprise)
- Ajouter la direction de révision (révision à la baisse = bearish)
- Pondérer par l'importance historique du rapport (juin/juillet plus impactants)

**Positionnement COT décomposé** :
- `cot_mm_long_chg` : variation des longs MM semaine sur semaine
- `cot_mm_short_chg` : variation des shorts MM semaine sur semaine
- `cot_producer_hedge_ratio` : ratio de couverture des producteurs
- `cot_swap_dealer_net` : position nette des swap dealers

**Spreads inter-commodity** :
```python
spread_corn_wheat = log(corn_price) - log(wheat_price)
spread_corn_soja  = log(corn_price) - log(soja_price)
```

**Corrélation dynamique (rolling)** :
```python
corr_corn_dollar_60d = rolling_correlation(corn_returns, dxy_returns, window=60)
corr_corn_oil_60d    = rolling_correlation(corn_returns, oil_returns, window=60)
```

Quand la corrélation corn-dollar est forte → facteurs macro dominent. Ce ratio de domination peut améliorer la pondération des facteurs.

---

## 12. Calibration probabiliste et correction de la confiance

### Priorité absolue — C'est le problème n°1

La calibration Platt actuelle génère 96.5 % UNCERTAIN. C'est le problème le plus urgent avant d'ajouter de la complexité.

Causes identifiées :
1. **Platt avec C=1e10** : régression logistique très peu régularisée → peut compresser les probabilités vers 0.5 si les données de calibration sont peu informatives.
2. **prob_distance hérite de la compression** : `prob_distance = |p_calib - 0.5| × 2` devient trop faible.
3. **signal_stability = 0.0** : bug de conception qui déprime la confiance systématiquement (voir Section 3).
4. **Seuil confidence=0.45 trop strict** : avec des probabilités comprimées, presque rien ne passe.

### Solutions à implémenter (V3-01)

**Solution A : Seuil adaptatif (priorité)**

```python
# Fixer le seuil au percentile 30 des scores de confiance en validation
conf_threshold = val_confidence_scores.quantile(0.30)
# Objectif : obtenir ≥20 signaux/an
# Si <10 signaux/an → baisser encore
```

**Solution B : Confiance indépendante de la calibration**

```python
confidence = (
    0.25 * AUC_contexte_actuel          # AUC historique dans ce contexte
    + 0.25 * accord_modeles             # % modèles en accord
    + 0.20 * |P(up) - 0.5| × 2        # amplitude brute du signal
    + 0.15 * (1 - cqr_width_normalized) # certitude CQR
    + 0.15 * stabilite_signal_3j        # persistance (non initialisée à 0)
)
```

Cette confiance ne dépend pas de la calibration → pas de compression par Platt.

**Solution C : Calibration par saison**

```python
for season in ['pre_semis', 'semis', 'croissance', 'pollinisation', 'recolte', 'post_recolte']:
    calibrator_season = PlattCalibrator()
    calibrator_season.fit(y_prob_season, y_true_season)
```

**Solution D : Classificateur binaire direct**

Entraîner directement un classificateur sur `y_up_h20` (direction binaire). La sortie est directement une probabilité de direction, sans transformation heuristique. Inconvénient : perd la CQR.

**Solution E : Réduire C dans Platt**

Tester `C=1.0` ou `C=0.1` au lieu de `C=1e10`. Un Platt plus régularisé compresse moins.

### Ordre d'implémentation

1. Corriger signal_stability = 0.0 → gain immédiat
2. Seuil adaptatif sur percentile validation → gain immédiat
3. Tester confiance indépendante de calibration → peut être meilleur
4. Si nécessaire : calibration par saison ou C plus petit

### Métriques de qualité de calibration

**ECE** (déjà mesuré : 0.2240 après Platt) : objectif ≤ 0.15.

**Sharpness** : variance des probabilités prédites. Un modèle qui dit toujours 50 % est calibré mais inutile. On veut des probabilités extrêmes ET calibrées.

**Brier Skill Score** :
```
BSS = 1 - Brier / Brier_baseline
```
BSS positif = meilleur que la baseline. Objectif BSS > 0.05.

**Fréquence signaux directionnels** : objectif ≥ 20 signaux/an (BULLISH ou BEARISH). Actuellement 8.9/an.

---

## 13. Architecture de l'indicateur final

### Ce que l'indicateur doit faire

```
INPUT au jour t :
  features brutes ou facteurs composites (sans leakage)

PROCESSING :
  1. Prédictions multi-horizon (J+5, J+10, J+15, J+20, J+25, J+30)
  2. Stacking multi-modèles (Ridge, LGBM, RF, meta-model)
  3. Calibration des probabilités
  4. Consensus multi-horizon (composante centrale)
  5. Score de confiance (composites — sans signal_stability=0)
  6. Contexte économique (saison, régime, volatilité)

OUTPUT :
  - label         : BULLISH / BEARISH / NEUTRAL / UNCERTAIN
  - force         : faible / modéré / fort  (interne)
  - prob_up       : {h5: 0.61, h10: 0.63, h20: 0.66, h30: 0.58}
  - confidence    : 0.72  (calibré, non déprimé)
  - consensus     : {score: 0.74, zone_Z3: BULLISH, zone_Z4: NEUTRAL}
  - top_factors   : [factor_wasde (haussier, +0.12), factor_crop (haussier, +0.09), factor_macro (baissier, -0.06)]
  - contexte      : {saison: pollinisation, regime: bull, vol: normal}
  - horizon_curve : {h5: 0.57, h10: 0.61, h15: 0.64, h20: 0.66, h25: 0.63, h30: 0.58}
  - uncertainty   : {cqr_h20: [−4.5%, +6.2%]}
```

### Labels : 4 publics + force interne

**Décision prise (Q8)** : 4 labels publics (plus lisibles, moins à calibrer) + score de force interne.

| Label public | Condition | Affichage utilisateur |
|---|---|---|
| BULLISH | prob > threshold_prob ET confiance > threshold_conf ET consensus > 0.65 | "BULLISH — force forte" |
| BEARISH | prob < (1-threshold_prob) ET confiance > threshold_conf ET consensus > 0.65 | "BEARISH — force modérée" |
| NEUTRAL | |prob - 0.5| < 0.10 (marché sans direction claire) | "NEUTRAL" |
| UNCERTAIN | confiance < threshold_conf OU désaccord multi-horizon fort | "UNCERTAIN" |

**Force interne (non publiée séparément)** :

```python
# calculée à partir du consensus_score et de la confidence
force = "fort"    si consensus_score > 0.75 ET confidence > 0.70
force = "modéré"  si consensus_score > 0.55 ET confidence > 0.55
force = "faible"  sinon
```

**Affichage exemple** :
```
BULLISH — force forte — confiance 72 % — consensus 78 %
```

### Règle de décision unifiée

```python
def decide_signal(prob_up, confidence, consensus_score, disagreement, threshold_prob, threshold_conf):
    # 1. Désaccord multi-horizon fort → UNCERTAIN
    if disagreement > 0.08:
        return "UNCERTAIN", "faible"

    # 2. Confiance insuffisante → UNCERTAIN
    if confidence < threshold_conf:
        return "UNCERTAIN", "faible"

    # 3. Pas de direction → NEUTRAL
    if abs(prob_up - 0.5) < 0.10:
        return "NEUTRAL", "faible"

    # 4. Consensus insuffisant → signal avec force faible
    if consensus_score < 0.55:
        if prob_up > threshold_prob:
            return "BULLISH", "faible"
        if prob_up < (1 - threshold_prob):
            return "BEARISH", "faible"

    # 5. Signal directionnel avec consensus
    force = "fort" if consensus_score > 0.75 and confidence > 0.70 else "modéré"
    if prob_up > threshold_prob:
        return "BULLISH", force
    if prob_up < (1 - threshold_prob):
        return "BEARISH", force

    return "NEUTRAL", "faible"
```

### Rapport journalier enrichi

```markdown
# Maïs CBOT — Indicateur directionnel — 2026-05-17

## Signal du jour
**BULLISH** — force forte — confiance 72 % — consensus 78 %
Zone principale : J+15 à J+30 (5/6 horizons haussiers)

## Probabilités par horizon
| Horizon | P(hausse) | Intervalle 90 % |
|---------|-----------|-----------------|
| J+5     | 59 %      | [−2.1 %, +4.8 %] |
| J+10    | 63 %      | [−3.2 %, +6.1 %] |
| J+20    | 66 %      | [−4.5 %, +7.9 %] |
| J+30    | 61 %      | [−5.8 %, +9.2 %] |

## Facteurs dominants
Haussiers : WASDE supply/demand (SHAP +0.124) | Crop condition (SHAP +0.098)
Baissiers : Dollar index fort (SHAP −0.071)

## Contexte économique
Saison : pollinisation | Régime : bull | Volatilité : normale
n_obs historiques (même contexte) : 228 — robuste

## Baselines
Saisonnalité : BULLISH | Momentum 20j : BULLISH (+1.8 %) → confirmé

## Limites
- Intervalle CQR à J+20 : large (12.4 pts) → forte incertitude
- WASDE dans 3 jours : risque de choc non capté
```

---

## 14. Garde-fous contre le p-hacking

### Le danger avec cette étude

On a maintenant :
- ~28 horizons à tester
- ~15 modèles dans le zoo
- ~7 méthodes de consensus
- ~6 contextes d'analyse
- ~5 méthodes de calibration
- ~3 méthodes de réduction de dimension

Si on teste tout et qu'on garde le meilleur résultat, on aura trouvé quelque chose par hasard.

### Garde-fous obligatoires

**G1 — Zone, pas horizon isolé**

Un horizon n'est retenu que si ses voisins ±3 horizons sont aussi bons. J+27 isolé = hasard. Zone J+22-J+32 cohérente = signal réel.

**G2 — Stable sur plusieurs splits**

Une performance doit tenir sur au moins 4 des 5 splits walk-forward. Si elle apparaît seulement sur 2012-2013 (la sécheresse) → fragile.

**G3 — Comparaison obligatoire aux baselines simples**

Toujours comparer à `seasonal_naive` et `momentum_20d`. Un modèle complexe qui ne bat pas la saisonnalité n'a aucune valeur ajoutée.

**G4 — n_obs minimum**

| n_obs | Statut |
|---|---|
| < 50 | Non interprétable — ne pas afficher |
| 50–100 | Exploratoire — signaler |
| 100–300 | Acceptable — avec nuance |
| ≥ 300 | Robuste |

**G5 — Test de stabilité temporelle par sous-période**

Performance par sous-période (2010–2013, 2014–2017, 2018–2021, 2022). Si la performance est excellente sur 1 seule période → fragile, documenter.

**G6 — 2023–2025 non réoptimisé**

Toute exploration (horizon sweep, model zoo, consensus) se fait sur 2010–2022. La période 2023–2025 a déjà été consultée (IND-08) et est documentée honnêtement. Elle ne sera plus modifiée pour optimiser.

**G7 — Seuils fixés sur validation, pas sur test**

Les seuils de confiance, de probabilité, de consensus doivent être fixés sur les données de validation (pré-2022). Jamais optimisés sur le test.

**G8 — OOF strict pour tout stacking**

Les OOF predictions du stacking niveau 0 doivent être produites par un modèle qui n'a jamais vu le fold de test. Interdit : prédictions in-sample comme méta-features.

**G9 — Diagnostic avant suppression des familles**

Une famille économiquement fondamentale (WASDE, météo) ne peut pas être supprimée sur la seule base d'une ablation globale. Diagnostic obligatoire par horizon, saison, cible et contexte avant toute décision.

**G10 — Documenter honnêtement les résultats décevants**

Si le model zoo montre que LGBM n'est pas meilleur que Ridge → le dire. Si le consensus multi-horizon n'améliore pas le J+20 seul → le dire. Un bon rapport scientifique documente aussi les idées qui n'ont pas marché.

**G11 — Correction des tests multiples**

Quand on compare 28 horizons, la probabilité de trouver quelque chose par hasard au seuil 5 % augmente fortement. Ne pas sur-interpréter des résultats marginaux (p ≈ 0.05 sur 28 tests = attendre ~1 faux positif). Exiger cohérence de zone + stabilité temporelle.

**G12 — Reproduction indépendante**

Fixer les seeds (random_state). Chaque expérience produit un artefact parquet avec métadonnées (date, seed, paramètres). Pas de résultats qui disparaissent entre deux runs.

---

## 15. Ce qu'on attend vraiment comme amélioration

### Scénario conservateur (probable)

```
DA globale              : 0.620–0.640  (actuel : 0.624)
DA top 20 % confiance   : 0.740–0.760  (actuel : 0.728)
DA top 10 % confiance   : 0.710–0.730  (actuel : 0.698)
AUC                     : 0.670–0.690  (actuel : 0.663)
Brier                   : 0.220–0.235  (actuel : 0.236)
Signaux forts/an        : 20–30        (actuel : 8.9 — à corriger en priorité)
Flip rate               : 0.035–0.060  (actuel : 0.037)
```

**Le plus gros gain attendu est sur la fréquence des signaux** : passer de 8.9 à 20+ par an en ajustant les seuils de confiance et en corrigeant signal_stability. Ce gain ne vient pas d'une amélioration de la DA brute mais d'une confiance mieux calibrée.

### Scénario optimiste (si consensus multi-horizon fonctionne bien)

```
DA top 20 % confiance   : 0.760–0.780
Signaux forts/an        : 25–40
AUC                     : 0.680–0.700
Signal plus interprétable économiquement
```

### Scénario décevant (mais valide scientifiquement)

```
DA globale              : 0.600–0.620
DA top 20 %             : 0.700–0.720
Signaux forts/an        : 12–18
```

Même dans ce cas, l'étude est publiable car elle documente honnêtement les limites du signal sur le marché du maïs avec données publiques.

### Ce qu'il ne faut pas promettre

- DA > 70 % global : irréaliste sur un marché financier actif
- Signal > 80 % du temps : si l'indicateur est souvent "confiant", il est mal calibré
- Performance constante sur toutes les années : 2012 (sécheresse), 2022 (Ukraine) sont structurellement différentes

### Stratégie prioritaire

**Ne cherche pas d'abord plus de complexité. Cherche d'abord plus de robustesse.**

```
1. Corriger l'indicateur trop conservateur (signal_stability, seuils)
2. Trouver la meilleure zone d'horizons (sweep)
3. Tester plus de modèles tabulaires (zoo)
4. Empiler proprement les prédictions (stacking OOF)
5. Construire un consensus multi-horizon (intégré à l'indicateur)
6. Calibrer la confiance (seuils adaptatifs)
7. Ensuite seulement : nouvelles données, DL, compressive sensing
```

---

## 16. Ordre logique des expériences

### Principe directeur

Ne pas répondre à une question avec des données qui dépendent d'une réponse non encore trouvée. Ne pas ajouter de complexité avant d'avoir corrigé les problèmes actuels.

### Étape 0 — CORRECTION IMMÉDIATE (avant tout)

**Corriger l'indicateur actuel** : signal_stability = 0.0, seuil de confiance adaptatif, Platt moins compressif. Objectif : passer de 8.9 à ≥20 signaux/an sans améliorer la DA brute.

C'est la fondation. Si on ne la corrige pas, toutes les expériences suivantes sont construites sur un bug.

### Étape 1 — FOND : que peut-on prédire et sur quel horizon ?

- Horizon sweep complet (V3-02)
- Comparaison cibles par horizon

### Étape 2 — MÉTHODES : quelle méthode est la meilleure ?

- Model zoo tabulaire complet (V3-03)
- Stacking multi-modèles OOF (V3-05)

### Étape 3 — CONTEXTE : dans quels contextes ?

- Analyse contextuelle améliorée (saison × régime × vol × horizon)
- Ablation diagnostic par famille (pas suppression directe)

### Étape 4 — DONNÉES : quelles données manquent ?

- Crop Progress NASS complet (V3-06)
- Drought Monitor câblé (V3-06)
- FAS Export Sales si clé obtenue (V3-06)
- Futures CBOT M2/M3 si données fiables (V3-06, optionnel)

### Étape 5 — CONSENSUS : comment agréger ?

- Consensus multi-horizon intégré (V3-04)
- Multi-task learning (optionnel, après stacking)

### Étape 6 — RÉDUCTION DE DIMENSION : est-ce utile ?

- PCA par famille vs facteurs composites (V3-07)
- Compressive sensing académique (V3-07)
- Autoencoder si PCA insuffisante (V3-07)

### Étape 7 — DEEP LEARNING : vraie amélioration ?

- MLP tabulaire régularisé (V3-08)
- GRU exploratoire (V3-08)
- TCN si GRU promet (V3-08)

### Étape 8 — VALIDATION FINALE

- Re-backtest final sur 2023–2025 avec l'indicateur V3 complet
- Réponses aux questions fondamentales V3
- Rapport final enrichi (V3-09)

### Ce qui est déjà fait (ne pas refaire)

- Étape 1 partielle : IND-01 (baseline), IND-02 (targets), IND-03 (oracle)
- Étape 3 partielle : IND-04 (contextes), IND-05 (ablation — à affiner)
- Étape 4 partielle : IND-06 (WASDE surprises, météo avancée)
- Étape 6 partielle : IND-07 (confidence V1/V2/V3, Platt)
- Étape 8 partielle : IND-08 (backtest final — sur l'indicateur V2)

---

## 17. Décisions prises — structure des tickets V3

### Décisions définitives

**D1 — Horizons** : J+1 à J+45 dense + points longs J+50/J+60/J+70/J+80/J+90/J+100. Grille :
```
J+1, J+2, J+3, J+4, J+5, J+7, J+10, J+12, J+15,
J+18, J+20, J+22, J+25, J+28, J+30,
J+35, J+40, J+45,
J+50, J+60, J+70, J+80, J+90, J+100
```
28 horizons. Horizons intermédiaires inclus pour détection de plateau vs pic isolé.

**D2 — Modèles** : tabulaire bien fait en priorité (Étapes 2-4), deep learning en exploratoire tardif (Étape 7). LSTM/GRU/TCN uniquement après stacking + consensus stabilisés.

**D3 — Compressive sensing** : expérience académique sérieuse. Défendable dans un rapport. Pas attendu comme gain majeur de DA.

**D4 — Consensus multi-horizon** : intégré à l'indicateur principal V3 (pas exploratoire). Si le test sur 2010-2022 valide le gain, il devient composante centrale.

**D5 — Données** : expériences sur données existantes d'abord (V3-01 à V3-05), puis Crop Progress + Drought Monitor + FAS (V3-06). Futures CBOT M2/M3 seulement si données fiables disponibles.

**D6 — Labels** : 4 labels publics (BULLISH / BEARISH / NEUTRAL / UNCERTAIN) + score de force interne (faible / modéré / fort). Pas de 7 labels publics.

**D7 — Objectif** : étude académique + prototype opérationnel. Présenté comme "indicateur d'aide à la lecture du marché du maïs, validé historiquement, signaux prudents et explicables". Pas un outil de trading autonome.

**D8 — Statut 2023-2025** : période déjà consultée, documentée honnêtement. Ne sera pas réoptimisée pour les expériences V3. Le vrai test temps réel commence en production 2026+.

### Structure des tickets V3

```
V3-01 — CORRECTION CALIBRATION / CONFIANCE
  Priorité : CRITIQUE — corriger avant tout le reste
  - Corriger signal_stability = 0.0 (initialiser à 0.5 ou fenêtre glissante)
  - Seuil adaptatif : fixer confidence_threshold au percentile 30 des scores de validation
  - Tester confiance indépendante de la calibration (formule Option B Section 12)
  - Tester Platt avec C=1.0 vs C=1e10
  - Objectif : ≥20 signaux directionnels/an sans régression de DA

V3-02 — HORIZON SWEEP J+1 À J+100
  Priorité : HAUTE
  - Tester les 28 horizons sur 2010–2022 (embargo = horizon H)
  - Métriques : DA, AUC, Brier, DA top 20%, fréquence signaux forts, n_obs
  - Comparaison obligatoire seasonal_naive et momentum_20d à chaque horizon
  - Courbe de prédictibilité + zones (G1 : retenir uniquement si voisins cohérents)
  - Objectif : identifier la zone principale (ex. J+15-J+35) et le pic optimal

V3-03 — MODEL ZOO TABULAIRE COMPLET
  Priorité : HAUTE
  - 10-15 modèles : Ridge, Lasso, ElasticNet, Logistic, BayesianRidge,
    RF, ExtraTrees, HistGB, LGBM, XGB, CatBoost, LinearSVM, MLP
  - Walk-forward identique pour tous, horizon(s) retenus de V3-02
  - Métriques : DA, AUC, Brier, DA_top20pct, stabilité entre splits
  - Vote simple + moyenne des probabilités comme baselines d'ensemble
  - Identifier les 4-5 modèles les plus diversifiés pour le stacking

V3-04 — CONSENSUS MULTI-HORIZON
  Priorité : HAUTE — intégré à l'indicateur principal
  - Implémenter les 6 méthodes (Section 7) sur 2010–2022
  - Score de consensus unifié (formule Section 7)
  - Intégrer comme composante centrale de la règle de décision
  - Zones d'horizons Z1-Z6 avec label par zone
  - Désaccord multi-horizon → forcer UNCERTAIN
  - Calibrer les seuils sur validation 2022
  - Variables de consensus utilisables comme méta-features pour V3-05
  - Objectif : augmenter signaux/an ET maintenir/améliorer DA top 20%

V3-05 — STACKING MULTI-MODÈLES
  Priorité : HAUTE
  - OOF strict : méta-modèle ne voit jamais les données d'entraînement des niveaux 0
  - Méta-features : prédictions modèles + variables de consensus (V3-04) + cqr_width + contexte
  - Tester : logistic_meta, ridge_meta, lgbm_meta, weighted_average, vote
  - Multi-horizon stacking : intégrer prédictions de plusieurs horizons
  - Comparer à chaque modèle individuel et aux ensembles simples
  - Objectif : DA top 20% ≥ 0.74, AUC ≥ 0.670

V3-06 — NOUVELLES DONNÉES PRIORITAIRES
  Priorité : MOYENNE
  - Crop Progress NASS : compléter le collecteur, wirer dans build_features()
  - Drought Monitor : implémenter collecteur (drought.unl.edu CSV)
  - FAS Export Sales : activer si FAS_API_KEY obtenue
  - Spreads corn-wheat, corn-soja : ajouter dans build_features()
  - COT décomposé : ajouter cot_mm_long_chg, cot_mm_short_chg, cot_swap_dealer_net
  - Futures CBOT M2/M3 : ticket de diagnostic de disponibilité d'abord
  - Ablation de chaque nouvelle source (delta_auc par famille)

V3-07 — RÉDUCTION DE DIMENSION
  Priorité : BASSE
  - PCA par famille vs facteurs composites actuels (comparer DA)
  - Compressive sensing : projection aléatoire 50/100/150 dim, comparer à PCA
  - Autoencoder sparse si PCA insuffisante
  - Question académique : "est-ce que l'info du maïs est sparse ?"
  - Rapport comparatif : PCA vs compressive sensing vs facteurs manuels

V3-08 — DEEP LEARNING EXPLORATOIRE
  Priorité : BASSE
  - MLP tabulaire bien régularisé (baseline DL)
  - GRU sur séquence 30j → si gain > 1 pt DA, continuer
  - TCN si GRU promet
  - Critère de rétention strict : +1 pt DA vs MLP, stable sur plusieurs seeds
  - Ne pas intégrer au core indicateur sans preuve de gain durable

V3-09 — RAPPORT FINAL ENRICHI
  Priorité : FINALE
  - Réponses aux 6 questions fondamentales avec toutes les données V3
  - Courbe de prédictibilité complète (horizon sweep)
  - Tableau comparatif modèles (zoo complet)
  - Backtest V3 sur 2023–2025 déjà consulté, sans réoptimisation des seuils, documenté honnêtement
  - Performance indicateur V3 vs V2 (delta DA, signaux/an, AUC)
  - Sections économiques : interprétation des résultats
  - Limites honnêtes documentées (résultats décevants inclus)
  - Architecture finale : composantes, seuils, règle de décision
```

### Questions fondamentales V3 à répondre

1. Le maïs est-il prédictible ? → réponse avec sweep + AUC par horizon
2. À quel horizon est-il le plus prédictible ? → courbe complète + zone robuste
3. Quelles familles de données apportent vraiment du signal ? → ablation diagnostique (pas suppression aveugle)
4. La direction est-elle plus prédictible que l'amplitude ? → AUC direction vs RMSE retour
5. Quand l'indicateur est-il fiable ? → DA par contexte (saison × régime × vol)
6. Quel est le vrai gain du consensus multi-horizon vs un seul horizon ?

---

## Résumé — ce qu'on a, ce qu'il manque, ce qu'on veut

### Ce qu'on a (solide)

| Composant | Statut | Qualité |
|---|---|---|
| Pipeline collecte → features → facteurs | ✅ Complet | Bon |
| Walk-forward avec embargo | ✅ Complet | Bon |
| Baselines (seasonal, momentum) | ✅ Complet | Bon |
| Ridge + LGBM + RF + XGB | ✅ Complet | Bon |
| CQR (intervalles de confiance) | ✅ Complet | Bon |
| SHAP (interprétation) | ✅ Complet | Bon |
| Analyse par contexte | ✅ Complet | Bon |
| Ablation des familles (V2) | ✅ Complet | À affiner |
| Confidence score V1 | ✅ Complet | Bugué (signal_stability=0) |
| Calibration Platt | ✅ Complet | Trop compressive |
| Backtest final 2023–2025 (V2) | ✅ Documenté | Consulté, non réoptimisé |
| Anti-leakage | ✅ Strict | Excellent |

### Ce qu'il manque (à construire)

| Composant | Impact attendu | Complexité | Ticket |
|---|---|---|---|
| Correction calibration/confiance | **Critique** (fréquence signaux) | Faible | V3-01 |
| Horizon sweep J+1-J+100 | **Fort** (base scientifique) | Moyen | V3-02 |
| Model zoo complet | **Moyen** (diversité) | Moyen | V3-03 |
| Consensus multi-horizon | **Fort** (exploitabilité) | Fort | V3-04 |
| Stacking multi-modèles OOF | **Moyen** (robustesse) | Moyen | V3-05 |
| Crop Progress + Drought Monitor | **Moyen** (signal météo) | Moyen | V3-06 |
| PCA / Compressive sensing | **Faible** (académique) | Faible | V3-07 |
| Deep learning GRU/TCN | **Faible** (exploratoire) | Fort | V3-08 |
| Rapport final enrichi | Finalisation | Moyen | V3-09 |

### Ce qu'on veut en sortie finale

Un indicateur qui dit clairement :

1. **Le maïs est-il prédictible aujourd'hui ?** (UNCERTAIN si non)
2. **Dans quelle direction ?** (BULLISH / BEARISH / NEUTRAL)
3. **Sur quelle zone d'horizons ?** (J+15 à J+30 ?)
4. **Avec quelle force ?** (faible / modéré / fort)
5. **Avec quelle confiance ?** (score 0–1, calibré, ≥20 signaux/an)
6. **Pourquoi ?** (top 3 facteurs avec signe et amplitude SHAP)
7. **Dans quel contexte ?** (saison, régime, volatilité)
8. **Avec quelle incertitude ?** (intervalle CQR)

Et un rapport d'étude qui répond à :

- Le maïs est-il prévisible avec des données publiques ? (Oui, modestement, sur J+15-J+30)
- Quand le signal est-il fiable ? (novembre, stocks tendus, pollinisation)
- Quelles données comptent vraiment ? (WASDE, météo belt, positionnement COT)
- Quand faut-il se taire ? (désaccord multi-horizon, confiance faible)
- Quelles sont les limites honnêtes ? (signal asymétrique baisse > hausse, données publiques)
- Qu'est-ce qui n'a pas marché ? (résultats décevants documentés)
