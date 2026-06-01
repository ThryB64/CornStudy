# Spécification — Étude professionnelle du prix du maïs

## Objectif de l'étude

Produire une étude complète, reproductible et honnête du prix du maïs CBOT :

1. Identifier les facteurs explicatifs du prix par horizon et par saison.
2. Prévoir l'évolution à J+5, J+10, J+20 et J+30 avec des intervalles calibrés.
3. Détecter les régimes de marché (bull/range/bear) par apprentissage statistique.
4. Transformer les prévisions en recommandations de vente pour les agriculteurs.
5. Backtester ces recommandations sur 15+ ans de données.
6. Mesurer le gain économique réel vs stratégies simples.

---

## Architecture de l'étude

```
données brutes (data/interim/)
        ↓
features.parquet (248 colonnes)
        ↓
factors.parquet (32 facteurs, 9 familles)
        ↓
walk-forward splits (embargo = horizon)
        ↓
benchmarks modèles + OOF predictions
        ↓
meta-database.parquet
        ↓
métamodèle Ridge (stacking)
        ↓
calibrated_predictions.parquet (conformal ou CQR)
        ↓
regime_timeseries.parquet (Markov-switching)
        ↓
cqr_results.parquet (intervalles asymétriques)
        ↓
shap_importance.parquet
        ↓
decision_snapshot.json
        ↓
PROFESSIONAL_STUDY_REPORT.md
```

---

## Les 4 horizons de prévision

| Horizon | Cible | Interprétation | Facteurs dominants attendus |
|---|---|---|---|
| J+5 | `y_logret_h5` | Très court terme, trading | Momentum, surprises WASDE, COT, basis |
| J+10 | `y_logret_h10` | Court terme, décision rapide | Météo hebdo, export sales, éthanol |
| J+20 | `y_logret_h20` | Moyen terme, décision agriculteur standard | Crop condition, stocks, weather stress |
| J+30 | `y_logret_h30` | Long terme, stratégie de vente | Fondamentaux WASDE, production monde, macro |

La cible est le log-return (différence de log-prix) sur l'horizon. Ce n'est pas un prix absolu, mais une variation relative. Cela rend la cible stationnaire et comparable entre périodes.

```python
y_logret_h{H} = log(price_{t+H}) - log(price_t)
```

**Pourquoi le log-return ?**
- Stationnaire → modèles plus stables
- Symétrique → +10% ≠ -10% sur les prix, mais +10% = -10% sur les returns
- Additif → log-return J+20 = somme des log-returns journaliers

---

## Modèles de l'étude

### Niveau 0 — Baselines (obligatoires)

| Modèle | Définition | Code |
|---|---|---|
| Zéro return | `y_pred = 0` | `baseline_zero_return` |
| Historical mean | Moyenne expandante des returns | À ajouter |
| Seasonal naive | Moyenne du même mois sur 5 ans | À ajouter |
| Momentum simple | Signe du return 20 derniers jours | À ajouter |

### Niveau 1 — Modèles explicables

| Modèle | Input | Code |
|---|---|---|
| Ridge sur features brutes | `raw_cols` | `ridge_raw` |
| Ridge sur facteurs | `factor_cols` | `ridge_factors` |
| ElasticNet sur facteurs | `factor_cols` | `elastic_factors` |

### Niveau 2 — Modèles ML

| Modèle | Input | Code |
|---|---|---|
| Random Forest | `factor_cols` | `rf_factors` |
| HistGradientBoosting | `factor_cols` | `hgb_factors` |
| LightGBM | `factor_cols` | `lgbm_factors` |
| XGBoost | `factor_cols` | `xgb_factors` |

### Niveau 3 — Métamodèle (stacking)

| Modèle | Input | Code |
|---|---|---|
| Ridge stacking | OOF de niveaux 1+2 + contexte | `meta_ridge` |

### Niveau 4 — Modèles de régime

| Modèle | Rôle | Code |
|---|---|---|
| MarkovRegression (3 états) | Détection régimes | `_build_regimes()` |

---

## Métriques d'évaluation

### Métriques statistiques

| Métrique | Formule | Pertinence |
|---|---|---|
| RMSE | √(mean(ε²)) | Erreur quadratique standard |
| MAE | mean(|ε|) | Robuste aux extrêmes |
| DA | mean(sign(ŷ) == sign(y)) | Direction correcte |
| R² OOS | 1 - SS_res/SS_tot | Variance expliquée |
| Hit 1% | P(|ε| < 0.01) | Précision sur petits mouvements |
| Hit 3% | P(|ε| < 0.03) | Précision sur grands mouvements |

### Métriques d'incertitude (CQR)

| Métrique | Définition | Cible |
|---|---|---|
| Couverture empirique | P(y ∈ [q_lo, q_hi]) | ≥ 90% |
| Largeur moyenne de l'intervalle | mean(q_hi - q_lo) | Minimiser |
| Calibration par régime | Couverture par état Markov | Uniforme |

---

## Rapport final

Le rapport `PROFESSIONAL_STUDY_REPORT.md` doit contenir :

1. **Résumé exécutif** — 1 page, résultats clés, conclusion principale
2. **Données** — Sources, couverture, qualité, gaps
3. **Facteurs** — 32 facteurs, familles, recettes de construction
4. **Modèles** — Benchmark complet avec baselines
5. **Régimes** — Distribution bull/range/bear, transitions
6. **Intervalles** — Couverture CQR empirique vs cible
7. **SHAP** — Importance par famille, par horizon, par régime
8. **Backtest agriculteur** — Stratégies, métriques économiques
9. **Table d'implémentation** — ✅/❌/⚠️ exacte
10. **Limites** — Ce qu'on ne sait pas, biais possibles
11. **Prochaines étapes** — Roadmap honnête

**Règle absolue :** aucun ✅ dans la table d'implémentation si la fonctionnalité n'est pas réellement implémentée, testée et productivement active.

---

## État d'implémentation actuel

| Composant | Statut | Note |
|---|---|---|
| Collecte données (11 sources) | ✅ | Actif |
| Anti-leakage audit | ✅ | Automatique |
| Cibles y_logret_h{5,10,20,30} | ✅ | Expanding quantile |
| Features (marché, météo, WASDE, FRED, NASS) | ✅ | 248 colonnes |
| Facteurs synthétiques (9 familles) | ✅ | 32 facteurs |
| Walk-forward avec embargo | ✅ | 8 ans initial, step 21j |
| Benchmarks (Ridge, RF, HGB, ElasticNet) | ✅ | 4 horizons |
| LightGBM + XGBoost dans benchmarks | ✅ | Optionnel, try/except |
| SHAP via TreeExplainer | ✅ | LightGBM → XGBoost |
| CQR (module cqr.py) | ✅ | Calibré sur set séparé |
| Markov-switching 3 états | ✅ | Fallback rule-based |
| Stacking Ridge | ✅ | Sur meta-database |
| Décision SELL/STORE/WAIT | ✅ | Moteur YAML |
| EIA éthanol | ⚠️ | Proxy corn/oil, clé API manquante |
| Crop Progress / Drought Monitor | ⚠️ | Collecteurs présents, pas dans features |
| Backtest agriculteur complet | ⚠️ | Partiel dans decision/backtest.py |
| Basis locale | ❌ | Pas de collecteur |
| Rapport quotidien | ❌ | ops/daily.py existe, non intégré |
| Optimisation Optuna | ❌ | optimize/ existe, non câblé dans study |
| Modèles deep learning (LSTM, TFT) | ❌ | Hors périmètre actuel |
