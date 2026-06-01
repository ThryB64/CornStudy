# V46 — Alignement de settlement CBOT/EMA

Session 2026-06-01. Suite directe de la découverte V44 (co-mouvement CBOT/EMA qui pique à 1 jour de
décalage). On quantifie la non-synchronisation et on teste des ré-alignements du CBOT. `RESEARCH_ONLY_NOT_TRADING`.
Holdout verrouillé. Règle figée inchangée. Module `src/mais/research/v46_settlement_alignment.py`,
tests (2 PASS), artefacts `artefacts/v46/`.

## Méthode
Basis = EMA_t − CBOT_{t−k}. On compare k ∈ {−1, 0, +1} :
- **k=0** : contemporain (baseline LIVE actuelle).
- **k=+1** : CBOT de la veille (LIVE, sans fuite).
- **k=−1** : CBOT du lendemain (DIAGNOSTIC seulement — FUITE, non exploitable live).

Métriques : corrélation de rendement EMA vs CBOT décalé, bruit jour à jour (std de Δbasis), autocorrélation
lag-1 de Δbasis (signature micro-structure), demi-vie AR(1), pouvoir de compression OOF.

## Résultats
| k | corr rendement | bruit Δ (std) | autocorr lag-1 Δ | demi-vie (j) | compression AUC |
|---|---:|---:|---:|---:|---:|
| **−1** (fuite, diag) | **0.424** | **3.32** | 0.002 | 21.3 | 0.620 |
| **0** (baseline live) | 0.095 | 4.21 | **−0.159** | 14.7 | 0.615 |
| **+1** (CBOT veille, live) | −0.04 | 4.46 | −0.011 | 13.3 | 0.621 |

## DÉCOUVERTE : la non-synchronisation est réelle et mécanique
- Le **meilleur alignement informationnel est k=−1** (EMA_t ↔ CBOT du lendemain, corr **0.424** vs 0.095
  contemporain) → confirme un décalage de settlement de ~1 jour.
- **Signature micro-structure** : le basis contemporain (k=0) a une **autocorrélation lag-1 NÉGATIVE
  (−0.159)** sur ses variations = rebond mécanique typique d'un prix non-synchrone. L'alignement k=−1
  l'**annule (0.002)** et **réduit le bruit quotidien de 21 %** (Δstd 4.21 → 3.32).
- → **une partie des variations quotidiennes du basis_z est du bruit d'horloge, pas de l'information.**
  Conséquence pratique : ne pas sur-réagir aux micro-mouvements de basis_z sur 1 jour.

## Mais : non corrigeable LIVE avec des données quotidiennes
- k=−1 utilise le CBOT du LENDEMAIN → **fuite**, inutilisable en live. À l'instant du close Euronext
  (~18h30 CET), le CBOT le plus frais réellement connu est celui du jour (k=0).
- Le k=+1 (CBOT veille), lui exploitable, **n'aide pas** (bruit plus élevé 4.46, AUC ~identique).
  → `live_realignment_helps = False`, verdict `NONSYNC_REAL_BUT_REALIGN_MARGINAL_LIVE`.
- Le **signal de compression est robuste à l'alignement** (AUC 0.615↔0.621) : la non-sync est surtout du
  bruit quotidien, elle ne détruit pas le signal. **La règle figée (k=0) reste le bon choix live.**

## Recommandation
- Conserver le basis contemporain (k=0) pour le live. Ne pas modifier la règle.
- Le **vrai correctif** = CBOT à l'heure exacte du settlement Euronext (snapshot intraday) → **data-gated**
  (nécessite un flux intraday). C'est le levier d'amélioration propre, à brancher plus tard.
- Lecture opérationnelle immédiate : traiter les variations de basis_z à l'échelle de quelques jours, pas au
  jour le jour (≈1 jour de jitter mécanique).
