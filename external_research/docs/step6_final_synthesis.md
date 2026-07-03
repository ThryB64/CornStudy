# Étape 6 — Synthèse finale (recherche externe `external_research/`)

Date : 2026-06-13. Rapport principal de clôture de la recherche externe. Aucune intégration
codée, aucun nouveau modèle, aucun gros entraînement. Résultats P2 **corrigés** (étape 5 bis :
fuite `target_date` calendaire → vraie ligne de marché ; verdicts inchangés). Holdout 2024+
jamais utilisé (règle 12). Modèle principal et données internes non touchés.

## 1. Résumé exécutif
- **Testé** : 12 repos GitHub, 131 fiches sources (papers/brevets/repos), 46 idées, **26
  expériences EXT** (P0 fondations, P1 fondamentaux, P2 modèles avancés).
- **Conclusion principale** : **le prix exact du maïs CBOT n'est pas prédictible** avec les
  données publiques gratuites (la random walk est imbattable en RMSE). En revanche, il existe
  un **signal directionnel modeste mais stable à H40-H90** (Crop Condition + WASDE
  stocks-to-use) et un **signal de volatilité/risque solide** (HAR/EGARCH).
- **Décision stratégique** : **Option B — abandonner la prévision de prix, construire un score
  de vente / direction / risque H40-H90**, conditionné par le régime et gaté par la
  volatilité ; + volet C ciblé (sourcer des données pour les familles bloquées).

## 2. Méthodologie
- **Sources** : repos (trend-following, OU, NBEATSx, COT, WASDE parser, roll, price analysis),
  études (Reeve-Vigfusson, Lehecka, Li-Hayes-Jacobs, Janzen, Huang-Serra-Garcia, Musunuru,
  Corsi HAR, AGRICAF, Penone VECM…), brevets, idées internes V*.
- **Anti-fuite** (`anti_leak_rules.md`) : walk-forward expandant, refit annuel **purgé**,
  standardisation/imputation **train-only**, sélection **dans** chaque train, lags de
  publication réels (WASDE+1BD, COT vendredi, crop lundi→mardi, météo J+1), z-scores
  expandants `shift(1)`, **holdout 2024+ exclu**. La seule fuite trouvée (`target_date`
  calendaire, 14-28 lignes de fin 2023) a été **corrigée à la racine** (étape 5 bis).
- **Benchmarks** : random walk (EXT025) = référence imposée à tout EXT, DM-test à l'appui.
- **Cible** : log-retour CBOT t→t+h (H5/H20/H40/H90), en RMSE **et** en direction (signe).

## 3. Résultats principaux
| Axe | Résultat | Verdict |
|---|---|---|
| **Prix / RMSE** | RW imbattable (0/36 DM) ; fondamentaux dégradent | **non prédictible** |
| **Direction H90** | Crop Condition DA **0,669**, AUC **0,724**, stable (0,632/0,707), +6,6 pts vs marché | **prédictible (modeste)** |
| **Direction H40** | WASDE stocks-to-use, gain plus faible mais stabilisant | prédictible (faible) |
| **Volatilité** | HAR/EGARCH −22 à −24 % RMSE vs RW, tous horizons | **solide** |
| **Score de risque** | filtre vol : décile haut → signal s'inverse (DA 0,41), DA 0,669→0,699 | **actionnable** |
| **Régimes** | fort en uptrend/low-vol/bilan extrême, nul en neutre | conditionnement |
| **Modèles complexes** | stacking/RF/DL sur-apprennent | **rien à garder** |

## 4. Ce qui marche (gardé)
- **Crop Condition @ H90** (anomalie good/excellent, déviation 5 ans, poor/very-poor) —
  meilleur signal directionnel ; conditions : horizon long, cadrage direction, parcimonie.
- **WASDE stocks-to-use @ H40** (ré-encodé stationnaire) — état de bilan lent.
- **HAR / EGARCH** — volatilité/risque ; **filtre de vol** comme gate.
- **Conditionnement par régime** (uptrend/low-vol/bilan extrême) — à valider forward.
- **Infra** : pipeline WASDE vintage (anti-fuite), hygiène de roll (`adjusted_price`).

## 5. Ce qui ne marche pas (rejeté)
- **Météo réalisée** (price-in), **surprise WASDE** (sans consensus), **COT** (aucun second
  ordre), **proxys éthanol** (pas de vraie marge crush), **trend-following** (le maïs ne tend
  pas), **stacking / DL** (sur-apprentissage). La **complexité n'apporte rien** : parcimonie gagne.

## 6. Ce qui est bloqué (données manquantes)
- **Courbe futures** (EXT005), **basis/VECM** (EXT013), **OU mean-reversion** (EXT012),
  **vraie surprise WASDE** (EXT008), **prime new-crop prédictive** (EXT018), **météo prévue**
  (EXT033). Manque : EUR/USD quotidien, contrats CBOT par maturité, consensus analystes,
  options (vol implicite), archive de prévisions météo forward. Détail : `step6_missing_data_recommendations.md`.

## 7. Conclusion scientifique
- **A-t-on tout exploré raisonnablement avec le public gratuit ?** **Oui**, largement (12 repos,
  131 fiches, 26 expériences couvrant toutes les familles à fort prior). Les sources publiques
  gratuites sont **épuisées** pour ce qui est testable sans nouvelles données.
- **Les données actuelles suffisent-elles pour prédire le prix ?** **Non.** `La prédiction
  pure du prix n'est pas validée avec les données actuelles.`
- **Suffisent-elles pour un indicateur utile ?** **Oui, partiellement** : un score de
  vente/direction/risque H40-H90, modeste mais stable. `Le signal peut être utile pour un
  indicateur d'aide à la décision, pas pour un bot autonome.`
- **Faut-il changer d'objectif ?** **Oui** : du prix vers le **score de vente** (Option B).

## 8. Recommandation finale
**PIVOTER (Option B)** : formaliser à l'étape 7 un **score de vente/direction/risque H40-H90**
(Crop Condition + WASDE stocks-to-use + saison, conditionné régime, gaté vol HAR/EGARCH), en
walk-forward strict, puis **validation holdout 2024+** (ticket projet humain) et backtest
décisionnel coût-aware. En parallèle, **sourcer** les données gratuites débloquantes (eurusd,
prévisions météo forward, exports) puis payantes (consensus WASDE, options). **Ne pas**
poursuivre la prévision de prix ni la complexité (DL/stacking).

## 9. Tableau final des décisions
| family | best_experiment | best_horizon | signal_type | verdict | recommended_action |
|---|---|---|---|---|---|
| Crop Condition | EXT024/EXT019 | H90 | direction/score | **IMPROVE (fort)** | cœur du score de vente |
| WASDE stocks-to-use | EXT007/EXT024 | H40 | direction | IMPROVE | ré-encoder stationnaire, intégrer |
| Volatilité | EXT010/EXT009 | H20-H90 | volatilité/risque | **KEEP** | gate de risque du score |
| Régimes | EXT017 | H90 | conditionnement | IMPROVE | confiance ; valider forward |
| Sélection variables | EXT015 | H90 | diagnostic | KEEP | confirme parcimonie |
| Combinaison | EXT014 | H90 | direction | IMPROVE (filet) | robustesse seulement |
| Benchmark prix | EXT025 | tous | prix | KEEP (réf.) | random walk = plancher |
| WASDE vintage | EXT026 | — | infra | KEEP | source WASDE anti-fuite |
| Roll | EXT006 | tous | hygiène | IMPROVE | adjusted_price / hors rolls |
| Trend-following | EXT011 | — | direction | REJECT | negative control |
| Stacking | EXT050 | — | direction | REJECT | parcimonie gagne |
| DL (NBEATSx) | EXT016 | — | — | NOT_WORTH_YET | rouvrir si données riches |
| Météo réalisée | EXT001/002/020 | — | contexte | REJECT | price-in |
| Surprise WASDE | EXT008 | — | — | REJECT | sourcer consensus |
| COT | EXT003 | — | — | REJECT | dossier clos |
| Éthanol/DDG | EXT004 | — | — | REJECT | sourcer prix éthanol/DDG |
| Courbe futures | EXT005 | — | — | DATA_BLOCKED | contrats CBOT par maturité |
| Basis/VECM | EXT013 | — | — | DATA_BLOCKED | eurusd quotidien + spot UE |
| OU mean-reversion | EXT012 | — | — | DATA_BLOCKED | dépend du basis |
| Prime new-crop | EXT018 | — | descriptif | PARTIAL_DATA | contrats Dec + météo forward |
| Météo prévue | EXT033 | H1-H10 | direction | DATA_BLOCKED | archive prévisions forward |

---
### Réponses directes (résultat attendu L)
1. Signal robuste trouvé ? **Partiel** : direction H90 + volatilité, pas le prix.
2. Prix exact prédictible ? **Non** (RW imbattable).
3. Direction H40/H90 partiellement prédictible ? **Oui**, modeste mais stable (crop@H90 0,669).
4. WASDE + Crop Condition apportent ? **Oui**, en direction long-horizon (Crop > WASDE).
5. HAR/GARCH utiles pour le risque ? **Oui**, le résultat le plus solide.
6. Modèles complexes apportent ? **Non** (sur-apprentissage ; parcimonie gagne).
7. À garder ? Crop@H90, WASDE s2u@H40, HAR/EGARCH, régimes (forward), vintage/roll.
8. À rejeter ? Météo réalisée, surprise WASDE, COT, éthanol proxys, trend, stacking, DL.
9. Bloqué ? Courbe, basis/VECM, OU, vraie surprise WASDE, météo prévue, options.
10. Intégrer à l'étude principale ? **Oui**, les briques KEEP/IMPROVE solides (étape 7).
11. Pivoter vers un score de vente ? **Oui** (Option B).
12. Données payantes nécessaires ? Consensus WASDE, options (vol implicite), courbe propre,
    prix physiques ; + gratuites débloquantes (eurusd, prévisions météo forward, exports).
