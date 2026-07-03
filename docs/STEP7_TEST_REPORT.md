# Étape 7 — Rapport de tests

Date : 2026-06-13. Tests du score de vente CBOT (`mais.indicator.cbot_sale_score*`).

## Commandes
```bash
./venv/bin/python -m pytest tests/test_cbot_sale_score.py \
    tests/test_cbot_sale_score_leakage.py tests/test_cbot_sale_score_outputs.py -v
./venv/bin/python -m ruff check src/mais/indicator/cbot_sale_score*.py src/mais/cli.py \
    tests/test_cbot_sale_score*.py
./venv/bin/python -m py_compile src/mais/indicator/cbot_sale_score*.py src/mais/cli.py
```

## Résultats
- **pytest : 14 passed** (révisé après ajout du test anti-fuite HAR).
- **ruff : All checks passed** (0 erreur sur les nouveaux fichiers + `cli.py`).
- **py_compile : OK** sur les 5 modules + `cli.py`.

## Couverture des tests
| Fichier | Test | Vérifie |
|---|---|---|
| `test_cbot_sale_score_leakage.py` | `target_dates_use_market_rows_not_calendar_days` | cible = `index[i+h]`, PAS `date + h jours` ; h dernières lignes sans cible |
| | `direction_target_is_forward_sign` | signe forward, NaN si pas de futur |
| | `holdout_2024_not_in_training` | aucune décision ni cible ≥ 2024-01-01 dans le train (logit) |
| | `har_vol_training_excludes_2024_targets` | aucune cible de **volatilité future** HAR en train ne tombe en 2024+ (purge corrigée) |
| | `expanding_transforms_use_past_only` | z-score expandant `shift(1)` (NaN initial) |
| | `only_allowed_features_in_score_models` | uniquement les variables autorisées ; aucune famille rejetée (cot/ethanol/weather/trend/stack/basis) |
| `test_cbot_sale_score_outputs.py` | `recommendations_are_in_allowed_set` | sorties ∈ {SELL_PARTIAL, WAIT, WATCH, RISK_HIGH, NO_SIGNAL}, jamais BUY |
| | `probabilities_in_unit_interval` | prob/confiance ∈ [0,1] |
| | `risk_high_only_when_vol_high` | RISK_HIGH ⇒ vol décile haut |
| | `no_signal_when_features_missing` | NO_SIGNAL ⇒ features manquantes |
| | `latest_record_shape` | `price_forecast_enabled` non vrai ; note « pas un bot » |
| `test_cbot_sale_score.py` | `config_exists_and_has_required_keys` | `config/cbot_sale_score.yaml` complet |
| | `score_is_reproducible` | deux exécutions identiques (déterminisme) |
| | `model_is_parsimonious` | 3-6 variables par horizon |

## Conclusion
Tous les tests passent ; le code est lint-clean et reproductible. Les tests d'anti-fuite
(cible ligne-de-marché, exclusion holdout, transforms passé-only) et de sorties (vocabulaire,
jamais de BUY) verrouillent les garde-fous demandés à l'étape 7.
