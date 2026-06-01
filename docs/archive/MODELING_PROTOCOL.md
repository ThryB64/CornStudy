# Protocole de modélisation

## Principe fondamental

> Un résultat n'est reporté que s'il est obtenu en walk-forward out-of-sample, sans fuite de données, et s'il bat au minimum la baseline "zéro return".

---

## 1. Structure du walk-forward

### Paramètres

```python
WalkForwardConfig(
    initial_train_ratio = 0.60,   # 60% des données pour l'entraînement initial
    step_size = 21,               # avancer de 21 jours trading à chaque fold
    horizon = H,                  # 5, 10, 20 ou 30
    embargo = H,                  # exclure H jours entre train et test
    max_train_size = None,        # expansif (None) — à tester : glissant (5000)
    min_train_rows = 500,
)
```

### Schéma temporel

```
Données totales : 2000 → 2025 (≈ 6300 jours trading)

Split initial :
├── Train       [2000 → ~2014]  60% = 3780 jours
├── Embargo     [~2014 → ~2014+H]  H jours
└── Test fold 1 [~2014+H → ~2014+H+21]  21 jours

Fold 2 : Train s'étend de 21 jours, test avance de 21 jours
...
Fold N : train = [2000 → 2025-H], test = derniers 21 jours
```

### Embargo

L'embargo évite la contamination : si on prédit J+20, les 20 derniers jours du train ne doivent pas être adjacents au premier jour du test.

```python
test_start = train_end + horizon
```

---

## 2. Matrices de features

### Input types

| Input kind | Colonnes | Usage |
|---|---|---|
| `raw` | Features brutes (248 cols) | Ridge raw uniquement |
| `factors` | Facteurs synthétiques (32 cols) | Tous les autres modèles |

### Imputation

```python
from sklearn.impute import SimpleImputer
imp = SimpleImputer(strategy="median")
imp.fit(X_train)
X_test = imp.transform(X_test)
```

L'imputer est fitté sur X_train uniquement. Jamais sur X_test ou les données complètes.

### Standardisation

Pour les modèles linéaires (Ridge, ElasticNet) :

```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(X_train)
X_test = scaler.transform(X_test)
```

Pour les arbres (RF, HGB, LightGBM, XGBoost) : pas de normalisation nécessaire.

---

## 3. Les modèles et leurs hyperparamètres

### Baselines

```python
def baseline_zero_return(X): return np.zeros(len(X))
def baseline_historical_mean(X, y_train): return np.full(len(X), y_train.mean())
def baseline_seasonal_naive(X, month): return historical_monthly_mean(month)
```

### Modèles Ridge et ElasticNet

```python
Pipeline([
    ("scaler", StandardScaler()),
    ("model", Ridge(alpha=1.0)),
])
```

Search space Optuna :
```python
{"alpha": trial.suggest_float("alpha", 0.01, 100.0, log=True)}
```

### Random Forest

```python
RandomForestRegressor(
    n_estimators=200,
    max_depth=None,
    min_samples_leaf=5,
    max_features=0.5,
    random_state=42,
    n_jobs=-1,
)
```

### HistGradientBoosting

```python
HistGradientBoostingRegressor(
    max_iter=200,
    learning_rate=0.05,
    max_depth=4,
    min_samples_leaf=40,
    l2_regularization=1.0,
    random_state=42,
)
```

### LightGBM

```python
lgb.LGBMRegressor(
    n_estimators=200,
    learning_rate=0.04,
    num_leaves=15,
    min_child_samples=40,
    lambda_l2=1.0,
    feature_fraction=0.8,
    verbose=-1,
    random_state=42,
)
```

### XGBoost

```python
xgb.XGBRegressor(
    n_estimators=200,
    learning_rate=0.04,
    max_depth=4,
    subsample=0.8,
    reg_lambda=2.0,
    verbosity=0,
    random_state=42,
)
```

---

## 4. Métriques d'évaluation

### Calcul sur chaque fold

```python
def _metrics(y_true, y_pred):
    residuals = y_true - y_pred
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "da": float(np.mean(np.sign(y_pred) == np.sign(y_true))),
        "hit_1pct": float(np.mean(np.abs(residuals) < 0.01)),
        "hit_3pct": float(np.mean(np.abs(residuals) < 0.03)),
    }
```

### Agrégation inter-folds

```python
mean_rmse = np.mean([fold["rmse"] for fold in fold_metrics])
std_rmse = np.std([fold["rmse"] for fold in fold_metrics])
```

L'écart-type entre folds mesure la stabilité du modèle.

---

## 5. Intervalles de confiance — CQR

### Méthode (Conformalized Quantile Regression)

Split : train (60%) → calibration (15%) → test (25%)

Sur train : entraîner deux quantile regressors :
- `q_lo_model` : quantile alpha/2 (ex. 5%)
- `q_hi_model` : quantile 1 - alpha/2 (ex. 95%)

Sur calibration :
```python
lo_cal = q_lo_model.predict(X_cal)
hi_cal = q_hi_model.predict(X_cal)
scores = np.maximum(lo_cal - y_cal, y_cal - hi_cal)
q_level = min(1.0, (1 - alpha) * (1 + 1/n_cal))
E = np.quantile(scores, q_level)
```

Sur test :
```python
q_lo = q_lo_model.predict(X_test) - E
q_hi = q_hi_model.predict(X_test) + E
covered = (y_true >= q_lo) & (y_true <= q_hi)
```

**Garantie théorique :** P(y ∈ [q_lo - E, q_hi + E]) ≥ 1 - alpha en marginal.

---

## 6. Détection de régimes — Markov-switching

### Modèle

```python
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

mod = MarkovRegression(
    endog=daily_log_returns,
    k_regimes=3,
    trend="c",
    switching_variance=True,
)
res = mod.fit(disp=False, maxiter=200, search_reps=5)
```

### Identification des régimes

```python
probs = res.smoothed_marginal_probabilities  # (nobs, 3)
regime_means = [np.average(returns, weights=probs[:, i]) for i in range(3)]
order = np.argsort(regime_means)
# order[0] = bear, order[1] = range, order[2] = bull
```

### Fallback rule-based si convergence échoue

```python
score = 0.45 * trend + 0.25 * tightness + 0.20 * momentum - 0.10 * vol
regime = "bull" if score > 0.45 else "bear" if score < -0.45 else "range"
```

---

## 7. SHAP — Importance réelle des facteurs

### Méthode

```python
import shap
explainer = shap.TreeExplainer(lgb_model)
shap_values = explainer.shap_values(X_test)
mean_abs_shap = np.abs(shap_values).mean(axis=0)
```

### Agrégation par famille

```python
shap_by_family = {
    family: mean_abs_shap[[i for i, col in enumerate(factor_cols)
                           if factor_family.get(col) == family]].sum()
    for family in FAMILY_ORDER
}
```

### Interprétation locale

Pour une date donnée :
```python
shap_local = dict(zip(factor_cols, shap_values[date_idx]))
top_positive = sorted(shap_local.items(), key=lambda x: x[1], reverse=True)[:3]
top_negative = sorted(shap_local.items(), key=lambda x: x[1])[:3]
```

---

## 8. Règles de publication des résultats

### Ce qu'on peut affirmer

- ✅ "Le modèle X obtient RMSE = Y en walk-forward sur la période 2015-2025"
- ✅ "La directional accuracy de LightGBM à J+20 est 59.3%"
- ✅ "La couverture empirique du CQR est 91.2% pour une cible de 90%"
- ✅ "Le régime bull représente 31% des observations depuis 2013"

### Ce qu'on ne peut pas affirmer

- ❌ "Le modèle est bon en production" (test uniquement sur données historiques)
- ❌ "SHAP est implémenté" si shap_importance.parquet est vide
- ❌ "CQR est implémenté" si cqr_results.parquet est vide
- ❌ "Markov-switching est actif" si le fallback rule-based a été utilisé

---

## 9. Ordre de priorité des modèles

Pour la décision finale agriculteur, l'ordre de confiance recommandé :

1. **Métamodèle Ridge** (stacking) — le plus complet
2. **LightGBM factors** — meilleur modèle individuel attendu
3. **HistGradientBoosting factors** — backup sans dépendance externe
4. **Ridge factors** — explicable, stable, utilisable en toutes conditions
