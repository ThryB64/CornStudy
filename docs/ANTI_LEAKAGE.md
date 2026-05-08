# Anti-leakage : règles et tests

## Définition

Une **fuite (leakage)** se produit quand le modèle a accès à de l'information
qu'il n'aurait pas eue en production. Pour des séries temporelles avec
target = log(P_{t+H}) - log(P_t), une fuite veut dire qu'une feature à la
date `t` utilise des données disponibles uniquement après `t`.

## Les 5 règles automatisées

Implémentées dans [`src/mais/leakage/audit.py`](../src/mais/leakage/audit.py)
et testées dans [`tests/unit/test_leakage.py`](../tests/unit/test_leakage.py).

### 1. SHAPE_ALIGNMENT
Les `Date` de `features.parquet` et `targets.parquet` doivent se chevaucher
à >= 95%. Sinon, l'un des deux a été décalé par accident.

### 2. NAMING_CONVENTION
Aucune colonne de `features.parquet` ne commence par `y_`. Ce préfixe est
réservé aux cibles de `targets.parquet`.

### 3. PERFECT_FIT
Si `|corr(feature_t, target_t)|` > 0.97 sur l'overlap, c'est suspect : la
feature est vraisemblablement une transformation de la cible future. Seuil
configurable via `--threshold`.

### 4. FUTURE_FUNCTION
Pour chaque (feature, target), on compare :
- `corr(feature_t, target_t)` (situation normale)
- `corr(feature_{t+1}, target_t)` (peek 1 jour dans le futur)

Si la deuxième est strictement supérieure de plus de `future_fn_min_improvement`
(défaut 0.05) ET en valeur absolue > 0.10, alors la feature à `t` encode déjà
une partie de l'information future utilisée par la cible. C'est un leak.

### 5. SUSPECT_NAMES
Aucune colonne ne doit avoir un nom :
- qui commence par un chiffre ou `-` suivi d'un chiffre (`5.98`, `175.1`, `-0.41`)
- qui termine par `.1` (artefact de collision pandas merge)
- égal à `Unnamed: 0`, `index` (artefacts CSV)

## Règles métier (à respecter dans le code)

### Tous les indicateurs techniques sont décalés `+1` jour

```python
# src/mais/features/market.py
feature_cols = [c for c in out.columns if c != "Date"]
out[feature_cols] = out[feature_cols].shift(1)
```

### La météo aussi (la donnée du jour J est observée en fin de J)

```python
# src/mais/features/weather_belt.py
out[feat_cols] = out[feat_cols].shift(1)
```

### Les variables fondamentales déclarent leur `lag_days` dans `config/features.yaml`

Exemple :
```yaml
ethanol:
  source: eia_ethanol
  lag_days: 6   # publié mercredi pour la semaine se terminant vendredi précédent
```

### Les classes ordinales (`y_class_h*`) utilisent une fenêtre EXPANDING

```python
# src/mais/targets.py::_expanding_quantile_class
# Les bins à `t` ne dépendent que des valeurs strictement avant `t`.
```

### Walk-forward avec EMBARGO horizon-dépendant

```python
# src/mais/walkforward/splits.py
embargo = max(self.embargo_days, self.horizon_days)
test_start = train_end + 1 + embargo
```

## Procédure d'usage

```bash
make features
make targets
make audit       # exit code != 0 si fail

# En cas de fail, le rapport détaillé est dans :
#   data/metadata/anti_leakage_audit.parquet
```

```bash
mais audit-leakage --no-fail   # n'échoue pas, juste affiche
```

## CI / pre-commit (recommandation)

Ajouter dans `.github/workflows/ci.yml` (à créer) ou `.pre-commit-config.yaml` :

```yaml
- id: mais-audit-leakage
  name: mais audit-leakage
  entry: mais audit-leakage
  language: system
  pass_filenames: false
```
