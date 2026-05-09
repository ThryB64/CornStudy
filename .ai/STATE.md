# État du projet — Etude Mais

## État actuel

TICKET-R01 exécuté : features régénérées avec COT et audit anti-leakage PASS. En attente de review.

## Paliers complétés (code)

| Palier | Description | Statut code |
|---|---|---|
| 1 | macro_fred + quickstats + production dans build_features() | ✅ |
| 2 | CFTC COT collecteur + intégration features | ✅ |
| 2b | EIA éthanol collecteur (proxy corn/oil en fallback) | ✅ |
| 3 | XGBoost + LightGBM dans _model_specs() | ✅ |
| 4 | SHAP réel via TreeExplainer | ✅ |
| 5 | CQR module (mais.meta.cqr) + wiring dans professional.py | ✅ |
| 6 | Markov-switching dans _build_regimes() (fallback rule-based) | ✅ |

## Dernier ticket terminé

Aucun validé `DONE` par review.

## Ticket en cours

Aucun.

## Ticket en review

TICKET-R01 — Rebuild features.parquet avec données COT.

## Prochaine priorité

Review TICKET-R01. Si validé `DONE`, passer à TICKET-R02 → TICKET-R03.

## Problèmes connus

- EIA éthanol nécessite `EIA_API_KEY` réelle — proxy corn/oil actif en fallback.
- MarkovRegression peut être lent sur de grands datasets (>5000 obs) — fallback rule-based prévu.
- Collinéarité production_fundamentals ↔ WASDE : Δ RMSE négatif sur Ridge (redondance documentée).

## Note courte pour les agents

Lire `AGENTS.md` et `.ai/TICKETS.md`. Ne pas lire `data/`, `artefacts/`, `*.parquet`. Un seul ticket à la fois. Finir en `NEEDS_REVIEW`.
