# Résumé technique — score de vente CBOT

Version : `cbot_sale_score_v1`. Date : 2026-06-13.

## Fichiers créés
| Fichier | Rôle |
|---|---|
| `src/mais/indicator/cbot_sale_score_features.py` | features anti-fuite (marché, WASDE vintage, Crop, HAR vol, régimes ; cible ligne-de-marché) |
| `src/mais/indicator/cbot_sale_score_model.py` | logit L2 par horizon, walk-forward, HAR forecast, gate gelé, métriques directionnelles |
| `src/mais/indicator/cbot_sale_score.py` | orchestrateur : modèles → score → recommandation ; `latest_record` |
| `src/mais/indicator/cbot_sale_score_backtest.py` | backtest décisionnel vendeur (vs récolte/tiers/DCA/attente) |
| `src/mais/indicator/cbot_sale_score_report.py` | `finalize()` : holdout, backtest, artefacts, verdict, `final_report.md` |
| `config/cbot_sale_score.yaml` | config officielle (horizons, variables, seuils, sorties, version) |
| `tests/test_cbot_sale_score.py` / `..._leakage.py` / `..._outputs.py` | 13 tests |

## Fonctions principales
- `features.build_frame()` → DataFrame quotidien (calendrier marché) + dictionnaire.
- `features.target_dates_from_index(index, h)` / `direction_target(px, h)` — cible anti-fuite.
- `model.fit_logit(df, cols, h, holdout_start, c)` → `FittedLogit` (entraîné ≤2023).
- `model.walk_forward_proba(...)` — DA pré-2024 (contexte recherche).
- `model.har_vol_forecast(...)` / `har_train_mask(...)` / `frozen_vol_gate(...)` — risque + gate
  gelé ; `har_train_mask` purge les fenêtres de vol dont la fin tombe en holdout (anti-fuite).
- `score.build_models(df, cfg)` / `score_timeseries(df, models)` / `latest_record(frame, cfg)`.
- `backtest.run_backtest(frame, cfg, start, window, cooldown)` → décisions, par-campagne, synthèse.
- `backtest.run_all_windows(...)` → comparaison découpages (calendar/sep_aug/oct_sep) × cooldown.
- `report.finalize(do_holdout)` → écrit les 9 artefacts + renvoie le verdict.

## Sorties (`artefacts/final_cbot_sale_score/`)
`final_score_timeseries.{parquet,csv}`, `final_score_latest.json`,
`final_holdout_2024_metrics.csv`, `final_backtest_decisions.csv` (calendar, cooldown défaut),
`final_backtest_summary.json`, `final_backtest_comparison.csv` (windows × cooldown),
`final_backtest_by_window.csv` (par campagne), `final_feature_dictionary.csv`,
`final_model_coefficients.csv`, `final_report.md`.

## Coefficients du modèle final (logit L2, ≤2023)
- **H90 (Crop)** : `cond_gd_ex_anom` +1.43, `cond_dev5y` −1.19, `cond_poor_vp` −0.52,
  `base_sin` −0.36, `base_cos` +0.39. Lecture : meilleures conditions (anomalie positive) →
  plus de probabilité de **baisse** des prix (offre abondante) — économiquement cohérent.
- **H40 (WASDE)** : `s2u_pctile` +0.41 (stocks larges → hausse moins probable / baisse), `s2u_z`
  −0.07, `s2u_slow_chg` +0.004, `base_sin` −0.13, `base_cos` +0.55.

## CLI / Makefile
```bash
python -m mais.cli sale-score            # artefacts
python -m mais.cli sale-score --holdout  # + validation holdout 2024+
python -m mais.cli sale-score --latest   # dernier signal
make sale-score                          # = sale-score --holdout
```

## Tests / qualité
- `pytest tests/test_cbot_sale_score*.py` → **13 passed**.
- `ruff check` sur les nouveaux fichiers + `cli.py` → **All checks passed**.
- Reproductible (logit déterministe, seuils en config).
