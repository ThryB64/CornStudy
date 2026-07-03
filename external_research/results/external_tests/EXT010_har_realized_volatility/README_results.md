# EXT010 — Résultats : HAR de volatilité réalisée

**Verdict : KEEP** (benchmark de volatilité principal recommandé).

## Protocole
HAR-RV (Corsi) : vol réalisée h-jours forward régressée sur RV passées 5/22/66 j, OLS
expandant (refit annuel, passé only). Comparé à la RW de vol (rv_h passé) et à rolling 20
mise à l'échelle. Cibles H20/H40/H90. Métriques : RMSE/MAE de vol, QLIKE (variance), corr.

## Résultats

| H | Modèle | RMSE | MAE | corr | QLIKE |
|---|---|---|---|---|---|
| 20 | **HAR** | **0.0335** | **0.0233** | 0.438 | **−4.012** |
| 20 | RW vol | 0.0394 | 0.0251 | 0.432 | −3.903 |
| 20 | roll20 | 0.0394 | 0.0251 | 0.432 | −3.903 |
| 40 | **HAR** | **0.0428** | **0.0320** | 0.440 | **−3.300** |
| 40 | RW vol | 0.0493 | 0.0341 | 0.454 | −3.229 |
| 40 | roll20 | 0.0517 | 0.0341 | 0.466 | −3.182 |
| 90 | **HAR** | **0.0605** | **0.0475** | 0.273 | **−2.423** |
| 90 | RW vol | 0.0790 | 0.0606 | 0.169 | −2.214 |
| 90 | roll20 | 0.0816 | 0.0557 | 0.350 | −2.179 |

(QLIKE : plus bas = meilleur.)

## Lecture
HAR **domine** RW-vol et rolling-20 sur RMSE, MAE et QLIKE à **tous les horizons**, avec
un avantage croissant à long terme (H90 : RMSE 0.0605 vs 0.079 pour la RW, −23 %). La
volatilité du maïs est nettement prévisible (à l'inverse de la direction des prix), et le
HAR capture la persistance multi-échelle mieux que les alternatives naïves.

## Conclusion
**KEEP.** Le HAR devient le **benchmark de volatilité principal** : simple, robuste,
expandant, sans paramètre à régler, meilleur que la RW de vol et le rolling-20 partout.
Brique naturelle pour les gates de risque et un score de vente prudent (cf. EXT009 pour
GARCH/EGARCH et le filtre de vol). C'est le résultat le plus net de l'étape 5 sur l'axe
RISQUE : contrairement à la direction des prix, **la volatilité se prévoit**.
