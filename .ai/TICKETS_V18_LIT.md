# Tickets — V18-LIT : réplication de littérature et intégration indicateur

Demande utilisateur : la découverte (compression de prime quand basis haut) relève de familles connues
(théorie du stockage, basis trading, convergence). On fait une revue structurée, on réplique les familles,
et on n'intègre que ce qui améliore l'indicateur OOF vs baseline `basis_z + saison`.

Docs : `docs/LITERATURE_REVIEW_MAIS_CBOT_EURONEXT.md`, `docs/LITERATURE_TO_EXPERIMENTS_MATRIX.md`,
`docs/V18_LIT_RESULTS.md`. Module : `src/mais/research/v18_literature_replication.py`.

## Tickets

- **V18-LIT-01** — `DONE` — Revue bibliographique (15 familles, mécanismes + méthode à répliquer).
- **V18-LIT-02** — `DONE` — Matrice études → expériences → variable indicateur + pipeline d'intégration.
- **V18-STORE-01** — `DONE` — Théorie du stockage (courbe). `NO_GO` de données (~332 obs courbe).
- **V18-BASIS-01** — `DONE` — Convergence (AR1/OU/threshold/régime). `KEEP_AS_EXPLANATION` : demi-vie 17.3j
  globale, 8.5j modéré, 13.2j extrême → plafond plus long pour entrées extrêmes.
- **V18-EVENT-01** — `DONE` — Event study WASDE. `NO_GO` (delta −0.018) : confirme prime locale (V16).
- **V18-COT-01** — `DONE` — COT positioning. `NO_GO` (delta −0.084).
- **V18-WEATHER-01** — `DONE` — Météo/crop stress. **`WATCHLIST`** (delta +0.016) : seule piste positive.
- **V18-COMMOD-01** — `DONE` — Inter-commodités. `NO_GO` (delta −0.101).
- **V18-OPTIONS-01** — `DONE` — Options/IV. `DATA_BLOCKED` (pas de volatilité implicite).
- **V18-ML-01** — référencé (déjà fait V3-V13) : ML ne bat pas basis_z → `NO_GO`.
- **V18-LIT-SUMMARY** — `DONE` — Matrice de verdicts. Aucune famille `ADD_TO_INDICATOR` ; indicateur inchangé.

## Décision

L'indicateur V17 (basis_z + saison + sortie z→0/0.5 + warnings) **reste inchangé** : aucune famille de
littérature ne le bat OOF. La parcimonie est confirmée une 4ᵉ fois.

## V18-WEATHER-DEEP (exécuté)

- **V18-WEATHER-DEEP** — `DONE` — Module `src/mais/research/v18_weather_deep.py`, doc `docs/V18_WEATHER_DEEP.md`.
  **Population** : basis haut + stress météo élevé → compression 33% vs 68% sans stress (corr +0.145) =
  confirmation mécaniste forte de la théorie du stockage (le stress « justifie » la prime, durable).
  **Trade** : `WEATHER_NEUTRAL` (n=6 stress élevé trop petit ; sortie dynamique capte les reversions
  partielles). **Décision** : pas de warning dur ajouté (ne pas sur-filtrer sur n=6) ; météo = contexte
  documenté, WATCHLIST maintenu. Indicateur V17 inchangé.

## Suite

- **V18-DATA** `WAITING_DATA` — EMA officiel + courbe multi-échéances + physiques EU (EC MARS, condition de
  culture EU) ; re-tester théorie du stockage (courbe) ET météo EU avec plus de données et de trades.
