# Carnets de recherche — Maïs CBOT

Organisation en deux niveaux : **main/** (carnets propres, raisonnement final) et **experiments/** (explorations classifiées).

## main/ — Séquence principale

Lire dans l'ordre. Chaque carnet pose une question précise, importe les fonctions depuis `src/mais/research/`, et se concentre sur le raisonnement, les résultats et l'interprétation.

| # | Carnet | Question | Modules utilisés |
|---|--------|----------|-----------------|
| 01 | `01_problem_data_quality.ipynb` | Quelles données sont fiables et portent un signal ? | `data_quality` |
| 02 | `02_seasonality_market_structure.ipynb` | Le calendrier agricole structure-t-il le marché ? | `seasonality`, `data_quality` |
| 03 | `03_factor_framework.ipynb` | Peut-on résumer 249 features en familles interprétables ? | `data_quality` |
| 04 | `04_targets_reformulation.ipynb` | `y_logret_h20` est-elle la bonne cible ? | `target_reformulation` |
| 05 | `05_statistical_models.ipynb` | AR/ARIMA/GARCH apportent-ils un signal ? | `statistical_models` |
| 06 | `06_automl_ml_models.ipynb` | Optuna + stacking améliorent-ils la DA ? | `model_benchmarks`, `automl_bridge` |
| 07 | `07_regime_seasonal_models.ipynb` | Les modèles par régime/saison font-ils mieux ? | `regime_models` |
| 08 | `08_uncertainty_calibration.ipynb` | Peut-on calibrer la confiance du modèle ? | `uncertainty` |
| 09 | `09_farmer_decision_backtest.ipynb` | Le modèle aide-t-il l'agriculteur à gagner plus ? | `farmer_backtest` |
| 10 | `10_final_synthesis.ipynb` | Synthèse — ce qui est prouvé, ce qui reste ouvert | tous |

## experiments/ — Explorations classifiées

```
experiments/
  successful/   — expériences qui ont amélioré la DA ou une métrique clé
  neutral/      — résultats mitigés, gardés pour référence
    01_donnees_et_correlations.ipynb
    02_analyse_saisonnalite.ipynb
    03_facteurs_et_shap.ipynb
    04_benchmarks_modeles.ipynb
    05_intervalles_cqr.ipynb
    06_regimes_et_backtest.ipynb
    07_conclusions_et_suite.ipynb
  failed/       — approches dégradant les résultats, archivées
```

## templates/

- `EXP_TEMPLATE.ipynb` — modèle de notebook pour toute nouvelle expérience
  (sections : hypothèse / méthode / résultats / décision / log)

## EXPERIMENT_INDEX.md

Généré automatiquement par `ExperimentLogger`. Liste toutes les expériences avec leur décision (successful / neutral / failed).

## Lancer les carnets

```bash
cd "Etude Mais"
venv/bin/jupyter notebook notebooks/corn_study/
```

## Dépendances

Les données doivent être générées avant (`make study`) :
- `data/processed/features.parquet`
- `data/processed/targets.parquet`
- `data/processed/factors.parquet` (optionnel)
- `artefacts/professional_study/*.parquet`
- `artefacts/farmer_backtest/*.parquet`

## Package research

Tout le code réutilisable est dans `src/mais/research/` :

| Module | Rôle |
|--------|------|
| `data_quality` | Chargement, classification familles, couverture, corrélations |
| `seasonality` | Rendements mensuels, heatmap, effet WASDE |
| `target_reformulation` | Construction des cibles y_store, y_up, y_regret |
| `model_benchmarks` | Walk-forward benchmark, métriques DA/RMSE/MAE |
| `statistical_models` | AR, ARIMA, GARCH, Markov 2-états |
| `automl_bridge` | Interface vers Models/ (60+ modèles) |
| `regime_models` | Régimes rule-based, modèles par régime/saison |
| `uncertainty` | CQR split-conformal, calibration probabilités |
| `farmer_backtest` | Backtest stratégies agriculteur (DCA, stockage, signal) |
| `reporting` | Graphiques standardisés, tables stylisées |
| `experiment_logger` | Enregistrement expériences dans EXPERIMENT_INDEX.md |
