# Tickets — V11 Programme discipliné

Suite de la review V10. Discipline imposée : modèle simple, H40, basis_z + month_cos, coûts réalistes,
validation forward, pas de meta-model, pas de H90, pas d'EMA brut, pas de bot réel.
Module `src/mais/research/v11_simplified_program.py`, doc `docs/V11_DISCIPLINED_PROGRAM.md`.

## Tickets

- **V11-01** — `DONE` — Promotion modèle simplifié. Verdict `PROMOTE_SIMPLIFIED` : 2 vars meilleur partout
  (AUC 0.694, ECE 0.059, rentable coût 3 +93). Devenu défaut de `run_indicator_v9`.
  Artefact `artefacts/v11/promote_simplified.json`.
- **V11-02** — `DONE` — Filtre régime forward. Verdict `REGIME_FILTER_POST_HOC_ONLY` : le filtre uptrend
  de V10-E ne tient pas hors échantillon, rejeté. Artefact `forward_regime_filter.json`.
- **V11-03** — `DONE` — Décision cost-aware. Verdict `COST_AWARE_BREAKS_WALL` (nuancé : coût 5 positif mais
  n=3 ; coût 3 solide +158). Artefact `cost_aware_decision.json`.
- **V11-04** — `DONE` — Régression basis-change. Direction prédictible (sign-DA 0.63 H40), magnitude non
  (R²<0). Artefact `basis_change_regression.json`.
- **V11-05** — `DONE` — Lab règles exhaustif BH-corrigé. 13/41 survivent BH q=0.10, 9 profitables coût 5.
  Découverte : côté short basis-haut (downtrend) le plus robuste. Artefact `simple_rules_lab_v11.json`.
- **V11-07** — `DONE` (design) — Paper-trading research design (`docs/V11_PAPER_TRADING_DESIGN.md`).
  Journal append-only, évaluation différée J+40, critères de promotion. Aucune exécution réelle.

## Bloqués / différés

- **V11-06** — `WAITING_DATA` — Validation EMA officiel vs proxy (requiert données Euronext/LSEG officielles).
- **V11-08** — synthèse research finale : couverte par `docs/V11_DISCIPLINED_PROGRAM.md`.

## Suite V12 (proposée)

- V12-01 — implémenter le journal paper-trading dans `ops/daily.py` (append-only + évaluation J+40).
- V12-02 — valider forward les règles short basis-haut de V11-05 (conditionnement régime hors échantillon).
- V12-03 — abstention par incertitude (largeur intervalle CQR) au lieu de bande morte fixe.
- V12-DATA — acquisition EMA officiel (déblocage principal).
