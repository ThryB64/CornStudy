# V44 — Mécanisme & magnitude de la compression EMA/CBOT

Session 2026-06-01. Trois angles nouveaux pour mieux EXPLIQUER et PRÉDIRE la compression, anti-leakage,
négatifs honnêtes acceptés, aucune touche à la règle figée. `RESEARCH_ONLY_NOT_TRADING`. Holdout verrouillé.
Module `src/mais/research/v44_mechanism_magnitude.py`, tests (2 PASS), artefacts `artefacts/v44/`.

## E1 — Lead-lag CBOT ↔ EMA (DÉCOUVERTE méthodologique)
Corrélations croisées rendement_EMA_t vs rendement_CBOT_{t−k} :

| lag k | −1 | 0 | +1 |
|---|---:|---:|---:|
| corr | **0.424** | 0.095 | −0.04 |

- **Contemporain faible (0.095), pic à un décalage de 1 jour (0.424)** → `NONSYNC_PRICING_PEAK_AT_1D`.
- **Interprétation honnête** : c'est un effet de **price discovery non-synchrone** — Euronext settle ~18h30 CET,
  le CBOT plus tard le même jour calendaire ; les deux séries quotidiennes ne sont pas alignées dans le temps.
  Le pic à |1 j| est donc un **artefact d'alignement de settlement**, PAS une preuve que l'EMA « mène » le CBOT.
- **On NE conclut PAS** sur la direction de causalité : la vraie lead-lag exige des **timestamps intraday**
  (data-gated). Conséquence pratique : ça justifie le `shift(1)` anti-leakage déjà imposé, et explique
  pourquoi une partie des variations quotidiennes du basis est mécanique (décalage), pas informative.

## E2 — Magnitude de compression (passage binaire → quantitatif)
Sur l'horizon 40 j, baisse du basis (€/t, >0 = compression) :

- **Signal actif (basis_z≥1) : baisse moyenne +5.7 €/t** ; **pas de signal : −2.8 €/t** (la prime MONTE).
  → confirmation quantitative nette que le signal isole une **anomalie compressible** (n=380).
- Prédire l'AMPLEUR exacte : **OOF R² = 0.093** (entry_z + résidu + momentum CBOT + saison, n=159) →
  `MAGNITUDE_PARTIALLY_PREDICTABLE`. Modeste mais positif : ~9 % de la variance d'amplitude est captée.
  Cohérent avec V35 (le chemin/timing précis n'est pas prévisible) : on sait que ça compresse et
  grossièrement de combien, pas exactement comment.

## E3 — Saisonnalité causale du basis (explicatif)
Profil mensuel du basis EU (z expandant, sans look-ahead) :

- **Prime la plus HAUTE** : août (z 0.63), juillet (0.52), septembre (0.39) — été / soudure old-crop,
  tension d'offre + risque météo de campagne.
- **Prime la plus BASSE** : février (z −0.13), avril/mai (~−0.01) — proche/après récolte hémisphère sud
  et reconstitution d'offre.
- Lecture : la prime européenne se FORME en été et se détend autour des récoltes. Explicatif, anti-leakage,
  cohérent avec la médiane de reversion saisonnière déjà utilisée (V14/V17).

## Synthèse
- **Mécanisme** : le co-mouvement CBOT/EMA est non-synchrone (décalage 1 j) — prudence sur toute lecture
  de « qui mène » sans intraday ; renforce la discipline anti-leakage.
- **Magnitude** : la compression est nette quand le signal est actif (+5.7 vs −2.8 €/t) et faiblement
  prédictible en amplitude (R² 0.09) — honnête.
- **Saison** : prime haute en été (juil-sept), basse en hiver/récolte — quand surveiller les signaux.
- Aucune touche à la règle ; tout descriptif/explicatif. Data-gated : lead-lag intraday réel.
