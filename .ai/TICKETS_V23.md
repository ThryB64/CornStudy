# Tickets — V23 Enrichissement (risque CBOT, régime, déblocage météo-prévue)

Suite V22. Enrichir l'étude + tenter les déblocages réels. Doc `docs/V23_RESULTS.md`.

## Exécuté

- **V23-01** — `DONE` — Module risque drawdown CBOT (OOF). drawdown 5%/h20 AUC 0.668, 8%/h40 AUC 0.738
  (technique + météo réalisée). Score de risque low/med/high comme contexte. Artefact `cbot_drawdown_risk.json`.
- **V23-02** — `DONE` — Régime CBOT × basis. **Hypothèse réfutée** : below-trend PAS meilleur (above-trend
  win 1.0 vs 0.81). Mais jambe CBOT domine dans les 2 régimes → V21 confirmé, pas de filtre régime.
  Artefact `regime_conditional_basis.json`.
- **V23-03 (DÉBLOCAGE)** — `DONE` — Collecte météo-prévue LIVE réussie (réseau OK) : 10 zones US, J+1..J+15,
  anti-leakage OK, features pondérées. `fetch_forecast` opérationnel, gestion 502 → SKIP propre.
  Artefact `live_forecast_snapshot.json`.

## Reste (data / réseau)

- **V23-FORECAST-ARCHIVE** — archive Previous-Runs (prévisions telles qu'émises J par J, multi-lead) pour
  backtester les RÉVISIONS de prévision sans leakage. Faisable (réseau OK), protocole anti-leakage en place.
- **V22-09 / source EMA officielle** — déblocage n°1 pour sortir du research-only.

## Discipline

Règle basis inchangée. drawdown_risk et météo = contexte/warnings, pas vetoes. Filtre régime rejeté.
