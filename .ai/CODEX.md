# CODEX — Etude Mais

Ce fichier documente les décisions techniques structurantes du projet.

## Architecture

```
src/mais/
├── collect/        # Collecteurs de données (WASDE, FRED, NASS, CFTC, EIA, OpenMeteo)
├── features/       # Feature engineering
│   ├── __init__.py     # build_features() — pipeline principal
│   ├── factors.py      # Facteurs synthétiques (32 facteurs, 9 familles)
│   ├── market.py       # Features marché (returns, vols, technique)
│   ├── weather_belt.py # Météo pondérée par belt agronomique
│   ├── surprise.py     # Features de surprise vs tendance
│   └── seasonality.py  # Fourier + saisons agronomiques
├── meta/           # Méta-apprentissage
│   ├── conformal.py    # Split-conformal symétrique (legacy)
│   ├── stacking.py     # Ridge stacking sur meta-database
│   └── cqr.py          # CQR : CQRModel + walk_forward_cqr()
├── study/
│   └── professional.py # build_professional_study() — orchestrateur principal
├── decision/       # Moteur de décision agriculteur SELL/STORE/WAIT
├── leakage/        # Audit anti-leakage automatisé
├── targets.py      # Calcul des cibles y_logret_h{5,10,20,30}
├── paths.py        # Constantes de chemins
└── utils.py        # Utilitaires (get_logger, read_parquet, etc.)
```

## Décisions techniques

### Anti-leakage
Toutes les sources fondamentales (FRED, NASS, WASDE, COT, EIA) sont `shift(1)` + reindex sur les dates marché avant merge. Les z-scores sont expandants (pas rolling fixe).

### Familles de facteurs (FAMILY_ORDER)
```python
["market_momentum", "market_volatility", "wasde_supply_demand",
 "weather_belt_stress", "production_fundamentals", "macro_dollar_rates",
 "cot_positioning", "seasonality", "cross_commodity", "others"]
```

### CQR
- Deux quantile regressors (alpha/2, 1-alpha/2) sur LightGBM ou sklearn GBR.
- Correction conforme `_e` calibrée sur un set de calibration séparé.
- Score de conformité : `max(q_lo - y, y - q_hi)`.
- Niveau quantile ajusté : `(1 - alpha) * (1 + 1/n)`.

### Régime Markov-switching
- `MarkovRegression` (statsmodels) à 3 états, `switching_variance=True`.
- Régimes identifiés par moyenne de return pondérée par probabilités lissées.
- Fallback rule-based si convergence échoue ou < 500 observations.

### Imports optionnels
```python
try:
    import lightgbm as lgb
    ...
except ImportError:
    pass
```
lightgbm, xgboost, shap, statsmodels sont tous optionnels.

## Sources de données

| Source | Collecteur | Fréquence | Lag |
|---|---|---|---|
| WASDE (USDA) | wasde_collector.py | Mensuelle | ~0j |
| FRED (macro) | fred_collector.py | Mensuelle | ~1j |
| NASS QuickStats | nass_collector.py | Annuelle/trim. | variable |
| CFTC COT | cftc_cot_collector.py | Hebdomadaire | 3j |
| EIA éthanol | eia_ethanol_collector.py | Hebdomadaire | 6j (nécessite clé API) |
| OpenMeteo | openmeteo_collector.py | Journalière | 0j |
| Base marché | database (CSV/parquet) | Journalière | 0j |

## Ce qu'il ne faut JAMAIS modifier sans ticket

- Le schéma de `_build_regimes()` (colonnes de retour).
- Le `shift(1)` anti-leakage des sources fondamentales.
- La table ✅/❌/⚠️ dans `_write_report()` de professional.py.
