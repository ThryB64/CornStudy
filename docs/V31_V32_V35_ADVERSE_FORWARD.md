# V31 / V32 / V35 — Dashboard forward, détection ADVERSE, moteur CBOT

Session 2026-05-31 (suite V30). Discipline : exploration des causes d'échec + suivi forward, PAS de
nouveau modèle. Baseline figée inchangée. Holdout 2024 verrouillé. `RESEARCH_ONLY_NOT_TRADING`.

## V32 — Détection du chemin ADVERSE (DÉCOUVERTE)

**Question** : peut-on prévoir AVANT l'entrée les trades qui finissent ADVERSE (basis qui s'écarte =
100 % des pertes, V29) ? Module `src/mais/research/v32_adverse_path_research.py`.

Sur 42 trades historiques (7 ADVERSE, 16.7 %), features d'entrée causales, **LOO honnête** :

- **LOO AUC multivarié = 0.72** → `ADVERSE_PARTIALLY_PREDICTABLE`. Les pertes ont une signature d'entrée.
- Profil ADVERSE vs compressé :

| feature | ADVERSE | compressé | écart |
|---|---:|---:|---:|
| entry_z | 1.32 | 1.69 | **−0.37** |
| basis_level | 45.7 | 52.8 | **−7.2** |
| backwardation (proxy) | −0.11 | +0.01 | −0.12 |
| realized_vol_20 | 0.24 | 0.32 | −0.07 |

**Lecture** : les ADVERSE sont les primes **modérées et peu élevées** (z et niveau bas), pas les extrêmes.
Cohérent avec V15 (edge concentré sur z>2). AUC univariés : backwardation 0.61, basis_level 0.58.

**Usage** (CONTEXTE, pas veto, anti sur-filtrage) : si `ADVERSE_RISK` élevé (z modéré + basis bas), viser
**z→0.5 seulement** et prudence sur z→0 complet — ce que la baseline figée offre déjà comme objectif prudent.
À re-tester en forward officiel avec plus de trades. n petit → descriptif.

## V35 — CBOT comme moteur de compression (NÉGATIF honnête)

**Question** : parmi les compressions, peut-on prévoir à l'entrée si CBOT_DRIVEN vs EMA_DRIVEN ?
Module `src/mais/research/v35_cbot_compression_engine.py`. 32 compressions, 59 % CBOT_DRIVEN.

- **LOO AUC CBOT_vs_EMA = 0.48 ≈ hasard** → `CBOT_PATH_DOMINATES_BUT_HARD_TO_TIME`.

**Lecture** : on sait que la compression est *en moyenne* CBOT-driven (mécanisme), mais on **ne peut pas
prédire le chemin d'un trade donné**. L'indicateur affiche « compression souvent par rattrapage CBOT »
comme contexte général, pas une prédiction par signal. Contraste net et utile avec V32 (ADVERSE prévisible).

## V31 — Dashboard forward + séparation des projets

Module `src/mais/research/v31_forward_dashboard.py`. Lit le journal officiel (V27) → tableau lisible
(date | basis | z | tier | courbe | warnings | objectifs | statut). Statut `open` /
`open_awaiting_official_history` tant que pas de prix de sortie officiel.

**Séparation explicite** : PROJET 1 (indicateur premium EMA/CBOT, cette étude) ≠ PROJET 2 (module
`daily_snapshot` SELL_THIRDS / cash / stockage agriculteur). Le dashboard ne mélange pas les deux.

## V36 — Drivers physiques / substitution Europe (intégration TTF + blé/maïs)

Motivé par de vraies analyses de marché (S&P Global mai 2026 : *« coûts d'origine, fret, CBOT »* ;
commodity-board : *« logistique tendue + marges éthanol »* ; théorie non-convergence storage/timing).
Module `src/mais/research/v36_physical_eu_drivers.py`. **Intègre enfin une donnée physique EU** : TTF gaz
(`eu_cross_assets`, features causales z expandant + lag) + ratio blé/maïs (substitution fourragère).

- **DÉCOUVERTE descriptive robuste** : `basis ~ ratio blé/maïs` **corrélation 0.60** → la substitution
  fourragère EU explique une part importante du niveau de prime (blé cher relatif → maïs demandé → prime
  EU haute). Grounded dans l'analyse de marché (substitution feed).
- TTF (énergie/fret) : `basis ~ TTF_z` = 0.26 (faible mais positif, cohérent coût séchage/logistique).
- **Discipline** : ajouter TTF+blé au score ADVERSE fait monter l'AUC LOO (+0.20) MAIS avec **9 features
  pour 7 événements ADVERSE** → flag `ADVERSE_AUC_GAIN_NOT_ROBUST_TOO_FEW_EVENTS` (overfit). On NE le
  retient PAS comme prédictif : TTF/blé restent **explication/contexte**, jamais un veto. Tests (2 PASS).

## V37 — Basis résiduel ajusté de la substitution (DÉCOUVERTE sur l'ADVERSE)

Évolution de V16 (fair-value macro rejetée) avec le bon driver trouvé en V36 (blé/maïs r=0.60). Module
`src/mais/research/v37_substitution_residual.py`. Décompose : `basis = part justifiée par substitution
blé/maïs (beta rolling causal) + RÉSIDU local` ; z expandant trailing (anti-leakage).

- **Prédictif (compression OOF)** : ajouter le résidu à la baseline `basis_z + saison` **DÉGRADE** l'AUC
  (0.623 → 0.578, delta **−0.045**) → `RESIDUAL_NO_PREDICTIVE_GAIN`. Règle inchangée (gouvernance).
- **DÉCOUVERTE — ADVERSE** : trades entrés à **résidu ÉLEVÉ** → ADVERSE **5.6 %** (win 0.89, PnL 16.6) ;
  à **résidu BAS** → ADVERSE **27.8 %** (win 0.72, PnL 6.6). Soit **5× moins d'ADVERSE** quand la prime est
  *inexpliquée* par la substitution. **Les pertes ADVERSE se concentrent sur les primes « justifiées » par
  l'économie blé/maïs (résidu bas)** — une prime économiquement justifiée ne se comprime pas. Angle
  économique complémentaire à V32. `adverse_verdict = HIGH_RESIDUAL_AVOIDS_ADVERSE`. n=36 → contexte
  ADVERSE_RISK, pas un veto.

## Synthèse
- Découverte nette : **l'ADVERSE est détectable (AUC 0.72)** → meilleure piste d'amélioration = réduire les
  ADVERSE via objectif prudent, sans toucher la règle.
- Le mécanisme de compression n'est pas timable (V35) → honnêteté maintenue.
- Forward outillé (dashboard V31), projets séparés.
- Document décisionnel : `docs/DECISION_NEXT_STEPS_AFTER_V30.md`.
- Bloqués data (honnêtes) : V33 (courbe officielle, besoin de jours), V34 (archive météo réelle),
  V36 (physique EU, intégration master requise), V37 (validation proxy vs officiel).
