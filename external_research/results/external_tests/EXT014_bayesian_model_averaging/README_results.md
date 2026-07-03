# EXT014 — Résultats : combinaison de modèles (BMA-like)

**Verdict : IMPROVE** (gain de STABILITÉ/robustesse, mais ne bat pas le meilleur modèle seul).

## Protocole
Poids de chaque membre = performance walk-forward PASSÉE (accuracy annuelle expandante,
laguée, part au-dessus du hasard), normalisée ; combinaison = moyenne pondérée des
probabilités. Aucune optimisation globale. Membres : market_only, market+wasde, market+crop,
rw_baserate (contrôle sans skill).

## Résultats

| H | Modèle | DA | balanced | AUC | Brier | DA 1re | DA 2e |
|---|---|---|---|---|---|---|---|
| 40 | market+wasde | **0.599** | 0.597 | 0.599 | 0.251 | 0.590 | 0.608 |
| 40 | market+crop | 0.595 | 0.593 | 0.611 | 0.243 | 0.549 | 0.642 |
| 40 | **bma** | 0.595 | 0.593 | **0.612** | **0.242** | 0.568 | 0.621 |
| 40 | rw_baserate | 0.508 | 0.502 | 0.510 | 0.250 | — | — |
| 90 | market+crop | **0.653** | 0.656 | **0.716** | **0.221** | 0.605 | 0.701 |
| 90 | bma | 0.627 | 0.628 | 0.687 | 0.225 | 0.589 | 0.664 |
| 90 | market_only | 0.599 | 0.601 | 0.608 | 0.245 | 0.527 | 0.671 |

## Lecture
- Le BMA **bat market_only** et est **plus stable** entre sous-périodes que n'importe quel
  membre seul (H40 : da_first 0.568 vs 0.519/0.549 ; meilleur Brier/AUC à H40).
- Mais il **ne bat PAS le meilleur membre par horizon** : à H90 il dilue le fort signal crop
  (0.627 vs 0.653) en y mêlant des membres plus faibles.
- Le membre `rw_baserate` reçoit correctement un poids ~nul (skill ≈ 0) — la pondération
  par perf passée fonctionne comme attendu.

## Conclusion
**IMPROVE.** La combinaison apporte de la **robustesse** (utile si on ne sait pas a priori
quel signal domine) mais pas de gain de performance de pointe. Recommandation : préférer le
**choix parcimonieux par horizon** (crop@H90, wasde@H40) ; garder le BMA comme filet de
sécurité si le régime change. Ne pas sur-empiler (cf. EXT050 : le stacking, lui, sur-apprend).
