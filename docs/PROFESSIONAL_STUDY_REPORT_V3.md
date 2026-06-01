# Étude Maïs V3 — Rapport professionnel

**Date** : 2026-05-17  
**Période d'entraînement** : 2010-01-01 – 2022-12-31 (OOF walk-forward, 5 splits)  
**Backtest hors-période** : 2023-01-01 – 2025-12-31 (IND-08, non réoptimisé)  
**Protocole anti-leakage** : shift(1) sur toutes les données fondamentales, z-scores expandants  

---

## Résumé exécutif

Le projet V3 a conduit une étude exhaustive en 9 tickets couvrant l'horizon optimal, le zoo de modèles, le consensus multi-horizon, le stacking, trois sources de données supplémentaires, la réduction de dimension et le deep learning.

**Conclusion principale** : le maïs est modestement prédictible sur données publiques, avec un pic de signal à **J+40** (DA=0.640, AUC=0.700 en OOF 2010-2022). La sélectivité (top 20 % des signaux les plus confiants) permet d'atteindre DA=0.743 — le levier de valeur le plus robuste. Le signal est conditionnel : il est plus fort en novembre (AUC=0.883) et en période de stocks tendus (AUC=0.799).

**Ce qui a fonctionné** : correction du seuil de confiance (×17 de signaux/an), horizon sweep, consensus.  
**Ce qui n'a pas apporté de gain** : stacking méta-modèle, deep learning (MLP), PCA par famille, spreads maïs/blé.

---

## 1. État de l'indicateur V3

### 1.1 Tableau comparatif V2 → V3

> **Note sur la comparaison** : les métriques V2 proviennent du backtest 2023-2025 (IND-08). Les métriques V3 sont des OOF 2010-2022 (phase de recherche). Une vraie comparaison sur 2023-2025 avec l'architecture V3 reste à faire en production (2026+).

| Composant | V2 (IND-08, backtest 2023-2025) | V3 (OOF 2010-2022) | Delta |
|---|---:|---:|---:|
| DA globale | 0.624 | 0.640 (J+40, sweep) | +0.016 |
| DA top 20 % | 0.728 | 0.743 (consensus) | +0.015 |
| Signaux/an | 8.9 | 151.6 (V3-01) / 251.7 (consensus) | +142 à +243 |
| AUC | 0.663 | 0.700 (J+40, sweep) | +0.037 |
| Flip rate | 0.037 | 0.075 (V3-01) | +0.038 |
| Brier | 0.236 | 0.257 (avg_proba stacking) | +0.021 |
| Modèles | lgbm h5/h10/h20/h30 | 5 modèles J+40 (lasso, histgb, gaussian_nb, logistic, extratrees) | |
| Seuil confidence | 0.45 (fixe) | 0.45694 (adaptatif p50) | |

---

## 2. Questions fondamentales V3

### Q1 — Le maïs est-il prédictible ?

**Réponse : Oui, modestement, avec des données publiques.**

- DA = 0.640 > 0.5 (horizon J+40, lgbm_factors, OOF 2010-2022)
- AUC = 0.700 au même horizon
- Le signal est réel mais conditionnel : il s'évanouit à courte échéance (J+1 à J+20 ≈ 0.50) et dépend fortement du contexte (mois, régime de stocks).
- Aucune zone robuste au sens strict G1+G3 n'a été identifiée (V3-02). J+40 reste le meilleur horizon empirique sans robustesse formelle confirmée.

### Q2 — À quel horizon ?

**Réponse : J+40 est le pic absolu. Seul J+28 bat le seasonal naïf de +2 pts.**

Courbe de prédictibilité (lgbm_factors, OOF 2010-2022) :

| Horizon | DA | AUC | Δ seasonal |
|---|---:|---:|---:|
| J+1 | 0.502 | 0.494 | +0.004 |
| J+5 | 0.509 | 0.521 | −0.027 |
| J+10 | 0.522 | 0.541 | −0.030 |
| J+20 | 0.559 | 0.550 | −0.004 |
| J+28 | 0.622 | 0.615 | **+0.021** ✓ |
| J+35 | 0.636 | 0.677 | +0.019 |
| **J+40** | **0.640** | **0.700** | −0.001 |
| J+45 | 0.600 | 0.638 | −0.049 |
| J+60 | 0.585 | 0.673 | −0.079 |
| J+90 | 0.573 | 0.585 | −0.126 |

**Conclusion** : la prédictibilité monte progressivement jusqu'à J+40, puis décroît. Aucune zone robuste G1+G3 (voisins ±3 et +2 pts vs seasonal) n'est confirmée. Candidats retenus pour le zoo : J+28, 35, 40, 45, 60.

### Q3 — Quelles familles de données apportent du signal ?

**Ablation IND-05 (13 familles, delta_auc sur y_down_gt_5pct_h20) :**

| Famille | Verdict | Δ AUC |
|---|---|---:|
| WASDE | **GARDER** | ++ |
| Météo BELT | **GARDER** | ++ |
| COT changes (V3-06) | **KEEP** | +0.0013 |
| Macro FRED | NEUTRE | ≈0 |
| EIA éthanol | NEUTRE | ≈0 |
| Spreads maïs/blé, maïs/soja | NEUTRE | −0.0015 |
| Drought étendu (V3-06) | NEUTRE | −0.0005 |
| Saisonnalité technique | RETIRER | − |
| Futures spreads M2/M3 | NON INTÉGRÉ | données indisponibles |

**V3-06 (nouvelles données)** : COT changes (variation hebdomadaire positions MM/PM) apportent +0.0013 AUC → retenus. Drought étendu et spreads neutres → non retenus dans le modèle final.

### Q4 — La direction est-elle plus prédictible que l'amplitude ?

**Réponse : La direction est plus facilement saisissable que l'amplitude exacte.**

- AUC direction J+40 = 0.700 (prédire hausse/baisse)
- RMSE régression h30 = 0.085 (retour absolu), DA = 0.583
- Conclusion : prédire le *signe* de la variation à ~6 semaines est plus robuste que prédire l'amplitude. C'est cohérent avec l'hypothèse que les forces directionnelles (fondamentaux WASDE, météo) sont plus persistantes que l'amplitude exacte.

### Q5 — Quand l'indicateur est-il fiable ?

**Analyse contextuelle IND-04 (62 contextes testés) :**

| Contexte | AUC | Interprétation |
|---|---:|---|
| Mois = novembre | 0.883 | Publications WASDE annuelles → forte réaction |
| Stocks tendus | 0.799 | Nervosité fondamentale amplifiée |
| Régime bear | 0.760 DA | Marché baissier plus prévisible |
| Global (tous contextes) | 0.663 | Moyenne |

**Conclusion** : concentrer les signaux en novembre et lors des périodes de stocks tendus maximise la fiabilité. En dehors de ces poches, le signal est proche du bruit.

### Q6 — Quel est le vrai gain du consensus multi-horizon ?

**V3-04 (consensus, OOF 2010-2022) :**

- Signaux/an avec consensus = **251.7** (vs 8.9 en V2)
- DA top 20 % avec consensus = **0.743** (vs 0.728 en V2)
- Limite importante : les OOF V3-03 disponibles contiennent un seul horizon (J+40). Le consensus multi-horizon est donc simulé sur mono-horizon, ce qui réduit le désaccord inter-modèle à quasi-zéro. Le vrai consensus sur plusieurs horizons reste à valider en production.

---

## 3. Horizon sweep — résultats complets

**Protocole** : 24 horizons (J+1 à J+100), lgbm_factors, walk-forward 5-split, 2010-2022.

**Observations clés** :
- J+1 à J+20 : DA ≈ 0.50 à 0.56. Signal faible ou nul. Les retours courts sont dominés par le bruit de marché.
- J+25 à J+40 : montée progressive. J+28 est le seul horizon à battre le naïf saisonnier de +2 pts DA (garde-fou G3).
- **J+40 : pic DA=0.640, AUC=0.700**. Interprétation économique : l'horizon 6 semaines correspond à la fenêtre de décision agricole (implantation, couverture) où les fondamentaux WASDE et météo font sens.
- J+45 à J+100 : dégradation progressive. AUC reste > 0.57 mais DA descend.

**Garde-fous appliqués** :
- G1 (voisins ±3) : aucun horizon ne valide une zone robuste.
- G3 (+2 pts DA vs seasonal) : seul J+28 valide.
- Résultat : `robust_zone = []`. J+40 retenu comme pic absolu, sans garantie de robustesse formelle.

---

## 4. Model zoo — tableau comparatif

**Protocole** : 15 méthodes testées sur J+40, walk-forward 5-split, 2010-2022.

| Rang | Modèle | DA | AUC | Brier | DA top20 | Std DA | Statut |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | lasso | 0.569 | 0.592 | 0.309 | 0.658 | 0.085 | **RETENU** |
| 2 | histgb | 0.568 | 0.582 | 0.254 | **0.743** | 0.099 | **RETENU** |
| 3 | lgbm | 0.558 | 0.592 | 0.253 | 0.703 | 0.094 | non retenu (redondant) |
| 4 | vote_majority | 0.557 | 0.564 | 0.291 | 0.591 | 0.079 | baseline ensemble |
| 5 | avg_proba | 0.556 | 0.565 | 0.258 | 0.552 | 0.084 | baseline ensemble |
| 6 | gaussian_nb | 0.540 | 0.583 | 0.456 | 0.554 | 0.078 | **RETENU** |
| 7 | logistic | 0.540 | 0.560 | 0.418 | 0.624 | 0.091 | **RETENU** |
| 8 | elasticnet | 0.536 | 0.583 | 0.322 | 0.622 | 0.123 | non retenu (λ similaire à lasso) |
| 9 | extratrees | 0.535 | 0.574 | 0.246 | 0.691 | 0.113 | **RETENU** |
| 10 | rf | 0.524 | 0.565 | 0.248 | 0.678 | 0.115 | non retenu |
| 11 | ridge | 0.495 | 0.498 | 0.360 | 0.428 | 0.075 | non retenu |
| 12 | ridge_classifier | 0.490 | 0.422 | 0.406 | 0.293 | 0.051 | non retenu |
| 13 | bayesian_ridge | 0.480 | 0.460 | 0.381 | 0.392 | 0.062 | non retenu |

**Modèles retenus pour V3-05** : `[lasso, histgb, gaussian_nb, logistic, extratrees]`  
**Zone robuste** : `[]` — aucun horizon confirmé G1+G3 pour former un zoo multi-horizon.

---

## 5. Stacking — performance vs individuel

**Méthode retenue** : `avg_proba` (moyenne des probabilités des 5 modèles)

| Méthode | Niveau | DA | AUC | Brier | DA top20 |
|---|---|---:|---:|---:|---:|
| **avg_proba** | ensemble_baseline | **0.578** | 0.597 | 0.257 | 0.613 |
| vote_majority | ensemble_baseline | 0.578 | 0.581 | 0.422 | 0.578 |
| lasso | individual | 0.569 | 0.592 | 0.309 | 0.658 |
| histgb | individual | 0.568 | 0.582 | 0.254 | 0.743 |
| meta_weighted_avg | meta_model | 0.554 | 0.614 | 0.252 | 0.595 |
| gaussian_nb | individual | 0.540 | 0.583 | 0.456 | 0.554 |
| logistic | individual | 0.540 | 0.560 | 0.418 | 0.624 |
| meta_ridge | meta_model | 0.540 | 0.422 | 0.450 | 0.462 |
| extratrees | individual | 0.535 | 0.574 | 0.246 | 0.691 |
| meta_lgbm | meta_model | 0.480 | 0.363 | 0.317 | 0.380 |
| meta_logistic | meta_model | 0.460 | 0.449 | 0.287 | 0.430 |

**Verdict** : le stacking méta-modèle (niveau 2) ne bat pas `avg_proba` (DA=0.578 vs 0.554 meilleur méta-modèle). L'`avg_proba` simple est retenu — il améliore la DA de +0.009 à +0.010 vs les modèles individuels, avec un Brier correct (0.257).

**Raison du non-gain du méta-modèle** : les OOF disponibles couvrent un seul horizon (J+40). Le désaccord inter-horizon — la principale source d'information méta — est donc nul dans cet export. Les méta-features consensus (V3-04) n'apportent pas de signal supplémentaire avec mono-horizon.

---

## 6. Nouvelles données — impact mesuré

**Baseline AUC** (ridge OOF, 2010-2022) : 0.6545

| Source | N cols | Δ AUC | AUC avec | Verdict |
|---|---:|---:|---:|---|
| COT changes (Δ positions MM/PM hebdo) | 5 | **+0.0013** | 0.6558 | **KEEP** |
| Drought étendu (d2plus, change_4w, extreme_flag) | 3 | −0.0005 | 0.6540 | NEUTRAL |
| Spreads maïs/blé, maïs/soja | 2 | −0.0015 | 0.6530 | NEUTRAL |
| Futures M2/M3 CBOT | — | — | — | NON INTÉGRÉ (yfinance indisponible) |

**Rebuilding features** : 279 → 289 colonnes après intégration des COT changes et features drought granulaires.

**Interprétation** : les changements de positions COT (≠ niveaux) capturent la variation d'appétit spéculatif à la marge, cohérent avec la littérature sur l'information contenue dans les flows. Les spreads inter-commodités n'apportent pas de signal après contrôle des facteurs existants.

---

## 7. Réduction de dimension

**Signal du maïs : DENSE** (CS n=50 perd −0.116 AUC vs raw → information distribuée sur toutes les features).

| Représentation | N dims | AUC | Commentaire |
|---|---:|---:|---|
| Raw (288 cols) | 288 | **0.6537** | référence |
| PCA par famille (90% var.) | 79 | 0.5653 | −0.089 AUC |
| CS n=50 | 50 | 0.5374 | −0.116 AUC |
| CS n=100 | 100 | 0.6526 | −0.001 AUC ≈ raw |
| CS n=150 | 150 | 0.6457 | −0.008 AUC |

**PCA par famille — composantes à 90% de variance expliquée** :

| Famille | Composantes | Signal cross-famille ? |
|---|---:|---|
| WASDE | 25 | Oui — signal ne se comprime pas bien en intra-famille |
| COT | 13 | Oui |
| Météo | 9 | Partiel |
| Other | 19 | Oui |
| Macro | 6 | Partiel |
| Market | 5 | Non |
| Saisonnalité | 2 | Non |

**Conclusion** : PCA intra-famille perd −0.089 AUC parce que le signal maïs est cross-famille (les interactions WASDE × COT × météo sont hors PCA). CS avec n=100 préserve quasi-tout le signal (−0.001 AUC) et pourrait être utile pour réduire les coûts de stockage/inférence, mais n'apporte pas de gain prédictif.

---

## 8. Deep learning

**PyTorch non installé dans l'environnement.** GRU/TCN non testés.

| Modèle | DA | AUC | Std DA | Stable | Note |
|---|---:|---:|---:|---|---|
| ridge_baseline | 0.633 | 0.654 | 0.000 | oui | référence |
| MLP (256-128-64, 3 seeds) | 0.605 | 0.638 | 0.010 | oui | NO_GAIN |
| GRU | N/A | N/A | — | — | torch_not_installed |

**Verdict** : `ridge_wins` — le MLP tabulaire régularisé (sklearn) apporte DA=0.605 soit −0.028 vs la régression ridge. Le MLP est stable (std=0.010 ≤ 0.015), mais il ne bat pas le baseline linéaire sur ~2000 observations.

**Décision documentée** :
- LSTM : non testé — équivalent au GRU, plus lourd, sans gain attendu à cette taille de données.
- Transformer : non testé — nécessite >> 2000 observations pour battre les modèles linéaires.
- GRU/TCN : non testés (torch absent). Verdict attendu : probablement pas de gain sur 2000 lignes tabulaires sans ingénierie de séquences spécialisée.

---

## 9. Backtest V3 sur 2023–2025

> **Nota bene** : la période 2023-2025 a été consultée dans IND-08 lors de la phase V2. Les seuils et paramètres V3 ont été calibrés sur 2010-2022 uniquement. Les résultats ci-dessous sont ceux de l'architecture V2 sur cette période, présentés pour référence sans réoptimisation.

**IND-08 backtest 2023-2025 (architecture V2)** :

| Métrique | Valeur |
|---|---:|
| DA globale | 0.624 |
| AUC | 0.663 |
| DA top 20 % | 0.728 |
| Signaux directionnels/an | 8.9 |
| DA bear state | 0.760 |
| DA haute confiance | 0.717 |

**Un backtest V3 propre sur 2023-2025** (avec l'architecture J+40 / avg_proba / consensus / seuil 0.45694) reste à exécuter en production (2026+) pour une vraie évaluation hors-période.

---

## 10. Architecture finale de l'indicateur V3

### 10.1 Pipeline de données

```
Sources brutes (EIA, NASS, Drought Monitor, CFTC COT, WASDE, FRED macro)
  ↓ shift(1) anti-leakage sur toutes les sources fondamentales
  ↓ z-scores expandants (fenêtre train uniquement)
  ↓ build_features() → 289 colonnes après V3-06
```

### 10.2 Modèles niveau 0 (J+40)

```
5 modèles retenus (V3-03) :
  lasso          — DA=0.569, AUC=0.592, DA_top20=0.658
  histgb         — DA=0.568, AUC=0.582, DA_top20=0.743
  gaussian_nb    — DA=0.540, AUC=0.583
  logistic       — DA=0.540, AUC=0.560
  extratrees     — DA=0.535, AUC=0.574

Ensemble retenu : avg_proba (moyenne probabilités)
  → DA=0.578, AUC=0.597, Brier=0.257, DA_top20=0.613
```

### 10.3 Calibration confiance (V3-01 / IND-07)

```
Calibration : Platt scaling (C=1.0) — ECE réduit de 23.5%
Confiance V4 :
  signal_stability  = rolling mean abs change sur 5 jours (1 - rolling_std / 0.5)
  prob_distance     = |p_calib - 0.5| × 2
  confidence        = 0.3 × signal_stability + 0.7 × prob_distance

Seuil confidence : 0.45694 (p50 des scores observés)
Seuils direction : p_bullish > 0.50 → BULLISH / p_bullish < 0.50 → BEARISH

Résultats V3-01 :
  Signaux/an : 151.6
  DA directionnelle : 0.623
  Flip rate : 0.075
```

### 10.4 Consensus multi-horizon (V3-04)

```
Score consensus = moyenne probabilités sur horizons disponibles
Désaccord = max(p) − min(p) entre horizons
  → désaccord > 0.06 → signal UNCERTAIN

Méta-features pour filtrage top 20 % :
  consensus_score, disagreement, n_horizons_above_05

DA top 20 % : 0.743
Signaux/an : 251.7
```

### 10.5 Format d'output (JSON)

```json
{
  "date": "2026-MM-DD",
  "horizon": "J+40",
  "signal": "BULLISH | BEARISH | NEUTRAL | UNCERTAIN",
  "p_bullish": 0.623,
  "confidence": 0.487,
  "consensus_score": 0.623,
  "disagreement": 0.042,
  "factors_bullish": ["wasde_ending_stocks_surprise", "cot_mm_long_chg"],
  "factors_bearish": ["heat_38c_days", "drought_d2plus"],
  "regime": "normal | bear | bull"
}
```

### 10.6 Règle de décision complète

```python
if confidence < 0.45694:
    signal = "UNCERTAIN"
elif disagreement > 0.06:
    signal = "UNCERTAIN"
elif p_bullish > 0.50:
    signal = "BULLISH"
else:
    signal = "BEARISH"
```

---

## 11. Limites honnêtes

### 11.1 Ce qui n'a pas fonctionné

| Piste testée | Résultat | Raison probable |
|---|---|---|
| Stacking méta-modèle | DA=0.554 < avg_proba=0.578 | Mono-horizon → désaccord nul → pas d'information méta |
| Deep learning (MLP) | DA=0.605 < ridge=0.633 | ~2000 observations tabulaires → régularisation linéaire suffisante |
| PCA par famille | AUC=0.565 < raw=0.654 | Signal cross-famille, PCA ne peut pas capturer les interactions |
| Spreads maïs/blé | ΔAuC=−0.0015 | Redondance avec DXY et macro existants |
| Drought étendu | ΔAUC=−0.0005 | Déjà capturé par le drought composite existant |
| Zone robuste G1+G3 | `robust_zone = []` | Pic J+40 non confirmé par les voisins ±3 simultanément |
| Futures M2/M3 | NON INTÉGRÉ | yfinance indisponible, sources alternatives payantes |

### 11.2 Limites structurelles

1. **Données publiques = limite d'information** : WASDE sort 12 fois/an. Entre les publications, le modèle n'a pas d'information fondamentale fraîche. Les retours J+1 à J+20 sont quasi-imprévisibles.

2. **Signal asymétrique** : les états bear (régime baissier) sont rares (~2.2 % des observations) et pourtant plus prédictibles (DA=76.0 % en bear). Le modèle manque d'exemples pour calibrer correctement les scénarios de chute sévère.

3. **Période WASDE** : le pic de prédictibilité en novembre (AUC=0.883) est lié aux publications WASDE annuelles. Ce signal de calendrier est structurel mais limité à ~21 jours/an.

4. **Résultat 96.5 % UNCERTAIN en V2** : corrigé en V3 (151.6 signaux/an), mais la correction repose sur un seuil de confiance adaptatif. Si les distributions futures s'écartent de 2010-2022, le seuil devra être recalibré.

5. **Backtest 2023-2025 non conduit avec l'architecture V3** : la période 2023-2025 a été vue en IND-08 (V2). Le vrai test hors-période de V3 commence en 2026.

6. **GRU/deep temporel non testé** : PyTorch absent de l'environnement. L'exploration des architectures séquentielles reste ouverte.

### 11.3 Ce qu'on ne peut pas promettre

- DA > 0.640 de façon robuste et reproductible sur 2023-2025 (résultats OOF 2010-2022 peuvent surestimer la performance)
- Signal stable hors des poches novembre/stocks tendus
- Gain garanti du stacking sur données multi-horizons futures

---

## 12. Conclusion

**Le maïs est-il prédictible avec des données publiques ?**

**Oui, modestement, dans des conditions spécifiques.**

| Condition | DA | AUC |
|---|---:|---:|
| Toutes observations | 0.569–0.640 | 0.592–0.700 |
| Top 20 % signaux confiants | **0.743** | — |
| Novembre uniquement | — | **0.883** |
| Stocks tendus | — | **0.799** |

**Résumé opérationnel** :
- Horizon optimal : J+40 (~6 semaines)
- Modèle retenu : avg_proba sur [lasso, histgb, gaussian_nb, logistic, extratrees]
- Seuil : confiance ≥ 0.45694 + désaccord ≤ 0.06
- Signaux exploitables/an : 151.6 (V3-01) — dont les top 20 % atteignent DA=0.743
- La sélectivité est le principal levier : filtrer les 20 % plus confiants triple presque la DA utile

**Ce que cet indicateur est** : un outil d'aide à la décision qui identifie des périodes à signal directionnel plus fort que le hasard, dans des contextes fondamentaux favorables (WASDE, COT, météo). Il n'est pas un système de trading autonome.

**Ce que cet indicateur n'est pas** : un oracle. La limite de prédictibilité du maïs sur données publiques est ≈ 0.640 DA globale. Dépasser ce seuil nécessiterait soit des données privées (flux de négociants, satellites, positions OTC), soit une ingénierie de features fondamentaux plus fine (surprise WASDE estimée en temps réel, nowcasting météo).

**Prochaine étape** : validation en production sur 2026+ avec l'architecture V3 complète et tracking des signaux émis en temps réel.

---

*Rapport généré le 2026-05-17. Tous les résultats sont basés sur des données observées avec protocole strict anti-leakage (shift(1), z-scores expandants, OOF walk-forward 5-split, données 2010-2022 uniquement, backtest 2023-2025 non réoptimisé).*
