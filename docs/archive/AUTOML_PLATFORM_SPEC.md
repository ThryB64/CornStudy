# Spécification — Plateforme AutoML / AutoForecast

## Objectif

Créer un outil générique capable de prendre un fichier CSV et de produire automatiquement un benchmark de modèles, un métamodèle, des explications et un rapport, sans configuration manuelle pour les cas standard.

La plateforme doit fonctionner sur :

- Régression tabulaire
- Classification binaire
- Classification multi-classe
- Classification ordinale
- Série temporelle univariée
- Série temporelle multivariée avec exogènes

L'étude du maïs est le cas d'usage primaire de cette plateforme. Mais la plateforme doit pouvoir tourner sur d'autres datasets (tests sur au moins 5 datasets différents avant de considérer la plateforme "finie").

---

## Composants de la plateforme

### 1. Profiler de dataset

**Rôle :** analyser un CSV et produire une fiche de caractérisation automatique.

**Entrée :** chemin vers un fichier CSV ou DataFrame pandas.

**Sorties :**
- Type de problème détecté (parmi les 6 types)
- Nom de la colonne cible (ou propositions)
- Type de la cible (numérique, binaire, ordinale, catégorielle)
- Présence d'une colonne date
- Nombre de lignes, colonnes
- Taux de missing par colonne
- Colonnes quasi-constantes
- Colonnes haute cardinalité
- Corrélations fortes entre features
- Distribution de la cible (normale, skewed, bimodale, binaire)
- Recommandations : split recommandé, modèles compatibles

**Fichier cible :** `src/mais/optimize/profiler.py` (existe, à compléter)

**Décision clé :** si une colonne `Date` est détectée et que le problème est une régression, le profiler doit recommander automatiquement un walk-forward au lieu d'un split aléatoire.

---

### 2. Module de prétraitement

**Rôle :** transformer les données brutes en features utilisables par les modèles.

**Fichier cible :** à créer dans `src/mais/platform/preprocessing/`

**Étapes automatiques :**

| Étape | Description |
|---|---|
| Détection types | Numérique, catégoriel, booléen, date, ID |
| Suppression colonnes ID | Colonnes haute cardinalité sans signal |
| Gestion NaN numériques | Median imputation par défaut |
| Gestion NaN catégoriels | Mode imputation ou catégorie "MISSING" |
| Détection outliers | IQR ou z-score expansant |
| Encodage catégoriel | OrdinalEncoder pour arbres, OneHot pour linéaires |
| Normalisation | StandardScaler pour modèles linéaires/SVM |
| Variables temporelles | Extraction year, month, day, dayofweek, week |
| Lags automatiques | Si série temporelle : lags 1, 5, 10, 21 par défaut |
| Rolling features | Moyenne et std sur 5, 10, 21 jours |
| Anti-leakage | `shift(horizon)` obligatoire sur toutes les variables |
| Colonnes quasi-constantes | Suppression si variance < seuil |
| Multicolinéarité | Warning si VIF > 10 entre features |

**Mode contrôlable :**

```python
preprocessing_config = {
    "mode": "auto" | "light" | "custom",
    "steps_disabled": ["outlier_detection", "rolling_features"],
    "custom_encoders": {...},
    "lag_values": [1, 5, 10, 20],
    "rolling_windows": [5, 21],
}
```

---

### 3. Registre de modèles

**Rôle :** maintenir la liste des modèles disponibles par type de problème.

**Fichier cible :** `src/mais/models/registry.py` (existe, à compléter)

**Organisation par type de problème :**

**Régression tabulaire :**
- LinearRegression, Ridge, Lasso, ElasticNet
- RandomForestRegressor
- HistGradientBoostingRegressor
- XGBoostRegressor, LightGBMRegressor, CatBoostRegressor
- SVR, KNNRegressor, MLPRegressor

**Classification binaire :**
- LogisticRegression
- RandomForestClassifier
- XGBoostClassifier, LightGBMClassifier, CatBoostClassifier
- SVC, KNNClassifier, GaussianNB

**Classification multi-classe / ordinale :**
- Mêmes modèles avec `multiclass` objective
- OrdinalClassifier wrapper pour la classification ordinale

**Série temporelle univariée :**
- NaiveBaseline (last value)
- SeasonalNaive
- ExponentialSmoothing
- ARIMA (via statsmodels)
- SARIMA

**Série temporelle multivariée :**
- Ridge avec features lagées
- ElasticNet avec features lagées
- RandomForestRegressor
- XGBoostRegressor, LightGBMRegressor
- SARIMAX
- MarkovRegression (régimes)

**Chaque modèle doit avoir :**
- Un `search_space` Optuna
- Des hyperparamètres par défaut testés
- Une méthode `compatible_with(problem_type) -> bool`
- Un flag `needs_scaling: bool`

---

### 4. Moteur Optuna

**Rôle :** optimiser les hyperparamètres de chaque modèle.

**Fichier cible :** `src/mais/optimize/runner.py` (existe, à compléter)

**Fonctionnalités :**

```python
optimize_model(
    model_name: str,
    X_train, y_train,
    cv_strategy: "kfold" | "walkforward",
    metric: "rmse" | "mae" | "auc" | "da",
    n_trials: int = 100,
    timeout: int | None = None,
    n_jobs: int = 1,
    resume: bool = False,   # reprendre une étude existante
    storage: str | None = None,  # SQLite pour persistance
)
```

**Search spaces par famille :**

```python
# Ridge
{"alpha": trial.suggest_float("alpha", 0.01, 100.0, log=True)}

# LightGBM
{
    "n_estimators": trial.suggest_int("n_estimators", 50, 500),
    "learning_rate": trial.suggest_float("lr", 0.01, 0.3, log=True),
    "num_leaves": trial.suggest_int("num_leaves", 8, 64),
    "min_child_samples": trial.suggest_int("min_child_samples", 10, 100),
    "lambda_l2": trial.suggest_float("lambda_l2", 0.0, 5.0),
    "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1.0),
}

# XGBoost
{
    "n_estimators": trial.suggest_int("n_estimators", 50, 500),
    "learning_rate": trial.suggest_float("lr", 0.01, 0.3, log=True),
    "max_depth": trial.suggest_int("max_depth", 3, 8),
    "subsample": trial.suggest_float("subsample", 0.5, 1.0),
    "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 5.0),
}
```

**Reprise d'étude :** si un fichier `study.db` SQLite existe pour ce modèle, continuer depuis le dernier essai.

---

### 5. Walk-forward et validation croisée

**Règle fondamentale :** si une colonne `Date` est détectée, le split aléatoire est interdit.

**Fichier cible :** `src/mais/walkforward/` (à créer ou adapter depuis `study/professional.py`)

**Stratégies disponibles :**

```python
WalkForwardConfig(
    initial_train_ratio: float = 0.60,
    step_size: int = 21,          # jours
    horizon: int = 20,            # jours
    embargo: int | None = None,   # défaut = horizon
    max_train_size: int | None = None,  # None = expansif
    min_train_rows: int = 500,
)
```

**Mode expansif vs glissant :**
- Expansif : la fenêtre d'entraînement grandit à chaque step (recommandé par défaut)
- Glissant : la fenêtre reste de taille fixe (à tester pour tester la dérive)

---

### 6. Meta-database et stacking

**Rôle :** produire des prédictions out-of-fold pour chaque modèle, les assembler en meta-database, entraîner un métamodèle dessus.

**Fichier cible :** `src/mais/meta/meta_database.py` (existe), `src/mais/meta/stacking.py` (existe)

**Pipeline :**

```
Modèle 1 → OOF predictions (train) + test predictions
Modèle 2 → OOF predictions (train) + test predictions
...
Modèle N → OOF predictions (train) + test predictions
         ↓
meta_database.parquet
[OOF preds modèle 1, ..., OOF preds modèle N, features de contexte]
         ↓
Métamodèle (Ridge ou LightGBM)
         ↓
Prédiction finale
```

**Features de contexte dans la meta-database :**

| Feature | Justification |
|---|---|
| `horizon` | Le métamodèle peut spécialiser par horizon |
| `regime` | Bull/bear/range influence quelle modèle croire |
| `realized_vol_60d` | En forte volatilité, certains modèles sont meilleurs |
| `days_since_last_wasde` | Proximité d'un rapport USDA |
| `model_error_30d_mean` | Erreur récente de chaque modèle de base |
| `model_error_30d_std` | Incertitude récente de chaque modèle |

**Règle anti-leakage du stacking :**
Les prédictions train du métamodèle doivent être des OOF (out-of-fold), jamais des prédictions sur les données d'entraînement des modèles de base.

---

### 7. Interprétabilité

**Rôle :** expliquer les prédictions à l'utilisateur.

**Outputs obligatoires :**

1. **SHAP global :** importance moyenne des features sur la période de test (TreeExplainer pour LightGBM/XGBoost)
2. **SHAP par famille :** agrégation SHAP par famille de facteurs
3. **SHAP local :** décomposition d'une prédiction particulière (pour le rapport quotidien)
4. **Erreurs par période :** RMSE par mois, par trimestre, par régime
5. **Corrélations features-cibles :** tableau de corrélations brutes (Spearman)
6. **Analyse des résidus :** autocorrélation, hétéroscédasticité, distribution

**Fichier cible :** `src/mais/platform/explainability/` (à créer)

---

### 8. Rapport automatique

**Rôle :** générer un rapport Markdown à la fin d'un run.

**Structure du rapport AutoML :**

```markdown
# Rapport AutoML — [Dataset] — [Date]

## Dataset
- Lignes : X
- Colonnes : Y
- Période : YYYY-MM-DD → YYYY-MM-DD
- Cible : [colonne]
- Type de problème : [type]

## Prétraitement
- Colonnes supprimées : [liste]
- Imputations appliquées : [liste]
- Features créées : [liste]

## Modèles testés
[Tableau benchmark]

## Métamodèle
[Résultats stacking]

## Importance des variables
[SHAP top 10]

## Limites
[Liste honnête]

## Recommandations
[Prochaines étapes]
```

---

### 9. Critère de "plateforme finie"

La plateforme est considérée opérationnelle si :

- [ ] Elle lit n'importe quel CSV propre (pas de données manquantes critiques)
- [ ] Elle détecte automatiquement le type de problème
- [ ] Elle propose les modèles compatibles
- [ ] Elle lance le prétraitement adapté
- [ ] Elle fait walk-forward si date détectée
- [ ] Elle optimise Optuna sur demande
- [ ] Elle produit un benchmark reproductible
- [ ] Elle produit un rapport complet
- [ ] Elle sauvegarde tous les artefacts
- [ ] Elle est testée sur 5 datasets différents du maïs (maïs, blé, soja, pétrole, SP500)
