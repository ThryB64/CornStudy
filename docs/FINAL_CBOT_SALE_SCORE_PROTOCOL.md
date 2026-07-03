# Protocole scientifique — score de vente CBOT

Version : `cbot_sale_score_v1`. Date : 2026-06-13.

## 1. Sources de données (internes, gratuites)
| Source | Fichier | Usage |
|---|---|---|
| Prix CBOT continu | `data/interim/market.parquet` (`corn_close`) | cible + saison + vol + momentum (baseline) |
| Crop Condition NASS | `data/raw/usda_nass_crop_condition/crop_progress.parquet` | features H90 |
| WASDE vintage (EXT026) | `external_research/results/external_tests/EXT026_wasde_vintage_pipeline/wasde_vintage_dataset.csv` | features H40 (lu en **lecture seule**) |

## 2. Cible
Signe du **log-retour CBOT** t→t+h (1=hausse, 0=baisse), h ∈ {40, 90} **lignes de marché**.
`target_date = index[i+h]` (vraie séance), **jamais** `date + h jours calendaires`.

## 3. Règles anti-fuite (`external_research/docs/anti_leak_rules.md`)
1. Pas de split aléatoire — walk-forward expandant, refit annuel **purgé** (cible du train <
   frontière de test).
2. **WASDE** disponible à `publication + 1 jour ouvré` (vintage publication-only, jamais
   révisé).
3. **Crop Condition** disponible après publication (lundi 16 h ET → +2 jours).
4. Standardisation / imputation / **sélection** estimées **train-only** ; z-scores et
   percentiles **expandants** `shift(1)` (passé strict).
5. Seuils figés ex ante (`config/cbot_sale_score.yaml`) ; gate de vol = décile 90 **gelé** sur
   ≤2023. **HAR purgé** (revue) : l'OLS de volatilité n'utilise que des fenêtres dont la vraie
   date de fin `index[i+h]` est < holdout (sinon une vol « future » de fin 2023 agrégeant des
   retours 2024 fuiterait) — testé par `test_har_vol_training_excludes_2024_targets`. Effet sur
   le gate : négligeable (0.1922 → 0.1923), mais la purge est désormais correcte.
6. **Holdout 2024+** jamais utilisé pour entraîner, sélectionner ou tuner (règle 12) — évalué
   **une seule fois**.

## 4. Walk-forward et holdout
- Recherche (≤2023) : walk-forward expandant, refit annuel, `min_train = 750`.
- Modèle final : logit L2 (`C=1.0`) entraîné sur **toutes** les décisions ≤2023 dont la
  **cible** est aussi ≤2023, puis appliqué à toute la chronologie.
- Holdout : 2024-01-01 → fin des prix (2025-07-25), évalué une fois.

## 5. Métriques
- **Direction** : DA, balanced accuracy, ROC-AUC, Brier, matrice de confusion,
  précision/rappel hausse & baisse.
- **Décision** : nombre de signaux par classe, prix moyen vs baselines, années
  gagnantes/perdantes, max regret.
- **Risque** : vol réalisée, gate (périodes neutralisées).

## 6. Baselines imposées
Random walk / base-rate, saison seule, Crop seule, WASDE seule, marché seul (momentum) ;
pour le backtest : vente-récolte, tiers, DCA mensuel, attente.

## 7. Reproductibilité
Logit déterministe (`lbfgs`, pas d'aléa), seuils en config, aucune dépendance à un seed.
Test `test_score_is_reproducible` garantit l'égalité de deux exécutions.

## 8. Garde-fous testés
`tests/test_cbot_sale_score_leakage.py` : cible ligne-de-marché, exclusion holdout du train,
transforms passé-only, variables autorisées uniquement. `..._outputs.py` : vocabulaire de
sortie, jamais de BUY. `..._.py` : config + reproductibilité + parcimonie.
