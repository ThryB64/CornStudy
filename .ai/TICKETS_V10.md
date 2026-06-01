# Tickets — V10 Market Discovery

Sprint de recherche ouvert sur la prime EMA/CBOT, reprenant l'indicateur V9. Objectif : comprendre
mécaniquement le signal et améliorer le modèle, sans claim non validé. Tout OOF / anti-leakage, holdout
2024 verrouillé. Module `src/mais/research/v10_market_discovery.py`, doc `docs/V10_MARKET_DISCOVERY.md`.

## Tickets (tous DONE après exécution + tests)

- **V10-A** — `DONE` — Économétrie du basis : AR(1) φ=0.96, demi-vie 17j, roulante time-varying.
  Explique R2 et le sweet-spot H40. Artefact `artefacts/v10/basis_econometrics.json`.
- **V10-B** — `DONE` — Attribution des 6 vars (permutation OOF + stabilité de signe). Seules basis_z et
  month_cos importantes et stables. Artefact `feature_attribution.json`.
- **V10-C** — `DONE` — Balayage d'horizon : H40 optimal (0.656), H90 s'effondre (0.559), réfute H90.
  Artefact `horizon_sweep.json`.
- **V10-D** — `DONE` — Survie aux coûts : mur confirmé, aucune sélectivité ne survit à coût 5 forward.
  Artefact `cost_survival.json`.
- **V10-E** — `DONE` — Conditionnement régime : edge concentré en uptrend CBOT (DA 0.690 vs 0.589).
  Artefact `regime_conditioning.json`.
- **V10-F** — `DONE` — Modèle simplifié : 2 vars (basis_z+month_cos) AUC 0.694 vs 0.656, validé
  LOYO + red team. `SIMPLIFIED_FEATURES` ajouté à `structural_indicator_v9`. Artefact `simplified_model.json`.

## Suite V11 (proposée)

- **V11-IND-01** — promouvoir le modèle 2 vars comme défaut de l'indicateur, re-faire backtest V4 dessus.
- **V11-REGIME-01** — tester forward le filtre uptrend (régime appris sur années passées).
- **V11-CQR-01** — abstention par incertitude (largeur d'intervalle CQR) au lieu de bande morte fixe.
- **V11-DATA-01** (`WAITING_DATA`) — EMA officiel Euronext NextHistory.
