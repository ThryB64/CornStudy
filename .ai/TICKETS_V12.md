# Tickets — V12 Mean-reversion lab + validation forward + abstention conforme

Suite V11. Discipline : basis + saison, H40, coûts réalistes, validation hors échantillon, pas de meta-model,
pas de bot. Module `src/mais/research/v12_mean_reversion_lab.py`, doc `docs/V12_MEAN_REVERSION_LAB.md`.

## Tickets

- **V12-A** — `DONE` — Anatomie reversion. Temps médian 54j ; sortie au niveau (basis_z→0) PnL moyen 23.4 vs
  9.2 (H40 fixe). Réserve n=41 / hit mécanique. Artefact `artefacts/v12/reversion_anatomy.json`.
- **V12-B** — `DONE` — Validation forward split-half. Verdict `FORWARD_RULES_GENERALIZE` : seule la famille
  short basis_z>1 généralise les deux moitiés ; long basis-bas non. Artefact `forward_rule_validation.json`.
- **V12-C** — `DONE` — Abstention conforme CQR. sign-DA 0.605→0.78 sur signaux agis ; couverture 0.70 vs 0.80
  (sous-couverture connue). Meilleure que bande morte fixe. Artefact `conformal_abstention.json`.
- **V12-D** — `DONE` — Journal paper-trading implémenté (`build_premium_journal` + `evaluate_matured_journal`).
  766 signaux mûrs, DA 0.651, positif coût 1 seulement. Artefact `premium_journal_eval.json`.

## Suite V13 (proposée)

- **V13-01** — intégrer l'abstention conforme dans `structural_indicator_v9` (remplacer la bande morte fixe).
- **V13-02** — tester l'horizon de détention 50-60j et la sortie au niveau (forward, sous abstention).
- **V13-03** — brancher le journal en cron quotidien (`ops/daily.py`, append-only, éval J+40).
- **V13-DATA** — `WAITING_DATA` — acquisition EMA officiel Euronext (déblocage principal).
