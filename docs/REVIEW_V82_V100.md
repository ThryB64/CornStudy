# Review phase V82→V100 (synthèse critique)

Bilan honnête de la phase V82+. `RESEARCH_ONLY_NOT_TRADING`, baseline figée, holdout verrouillé.

## Nouvelles découvertes
- **V82 (episode library)** : en regardant les 42 signaux comme ÉPISODES, les **familles par canal** se
  détachent nettement. Le MFE révèle que les **ADVERSE n'ont quasi jamais été profitables** (MFE 5.7 vs
  CBOT_DRIVEN 37 €/t) et **traînent ~60 j** → ils sont distinguables tôt (faible MFE + durée qui s'allonge).
- **V86 (CBOT_SUPPORT v2)** : ajouter du contexte **économiquement aligné** (corn/wheat V80 + La Niña V79)
  **AMÉLIORE** la séparation ADVERSE (gap 0.143 vs v1 0.112) et la part CBOT_DRIVEN (0.571 vs 0.526).
  Contraste direct avec **V64** où empiler du bruit (roll/crise/vol) DILUAIT ADVERSE_RISK. **Leçon** : le
  contenu économique compte, pas le nombre de composants.

## Ce qui améliore réellement l'indicateur (GO / ADD)
- **V86** CBOT_SUPPORT v2 → branché daily report (sépare mieux l'ADVERSE).
- **V99** synthèse v2 → vue d'ensemble enrichie (ENSO_CONTEXT, SUBSTITUTION/WEATHER warnings, CBOT_SUPPORT v2),
  remplace V77 dans le rapport.
- **V82** episode library → base analytique réutilisable (`data/research/high_basis_episodes.parquet`).

## Ce qui est explicatif seulement
- V82 (descriptif), ENSO_CONTEXT (V79, WATCHLIST), SUBSTITUTION/WEATHER warnings (contexte, jamais veto).

## Déjà livré en v1 (pas de v2 nécessaire — apport net nul attendu)
- V89 survival = **V72** · V90 magnitude = **V57** · V88 tension = **V54** · V93 casebook = **V58** ·
  V95 locality = **V71b** · V96 intercommodity = **V80** · V98 monthly = **V59** · V87 intraday = **V60** ·
  V92 objectif : V56 déjà risk-efficient ; v3 différé (pas d'apport net démontré sans nouvelle donnée).
- V91 ADVERSE_RISK v3 : V64 a montré qu'enrichir le SCORE dilue → on garde v1 + V64 explication.

## Bloqué par la donnée (vérifié)
- V83 (intra-campagne EU), V84 (MATIF historique → forward), COMEXT (probé V80, hors API), options/IV,
  intraday historique, archive révisions météo. V85 (révisions) = forward (journal V45 enrichi persistance).

## À suivre en forward
- Journaux (signal officiel, MATIF, météo+persistance, ENSO via recompute) → V97 proxy vs officiel, V98
  rapport mensuel (V59), V100 décision après 3-6 mois.

## Réponse d'étape à la grande question
> Quand un basis haut est-il anomalie compressible vs prime justifiée ?

- **Anomalie compressible** (objectif z→0, horizon ~29-42 j) : **CBOT_SUPPORT (v2) HIGH** — uptrend +
  momentum + COT favorable + corn cheap vs blé + (La Niña) ; prime forte ; pas de substitution/tension.
  Canal attendu : CBOT_DRIVEN.
- **Prime justifiée / danger** (objectif z→0.5 ou warning) : CBOT non porteur, prime modérée (z<1.5),
  ratio blé/maïs élevé (substitution feed), tension physique (backwardation), roll/crise.

Le **CBOT porteur reste le discriminant central** ; v2 le qualifie mieux. La prime est **locale**.

## Prochaine roadmap
Tout repose désormais sur le **forward** (accumulation) et de **nouvelles données EU intra-campagne**
(MARS/COMEXT, actuellement bloquées). Pas de nouveaux modèles sur les 42 trades (sur-ajustement interdit).
V100 (décision) se tranchera après plusieurs mois de track record officiel.
