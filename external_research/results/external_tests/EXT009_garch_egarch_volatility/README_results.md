# EXT009 — Résultats : GARCH / EGARCH / GJR-GARCH (outil de risque)

**Verdict : KEEP** (outil de RISQUE, pas de direction). EGARCH = meilleur modèle de vol ;
le filtre de volatilité améliore matériellement le score directionnel.

## Protocole
Refit mensuel expandant (passé only), prévision h-jours de vol, distribution Student.
Comparé à RW de vol et rolling-20. Métriques en unités de rendement % (×100). Plus un
backtest de **filtre de vol** sur le score directionnel H90 (crop).

## Prévision de volatilité (RMSE, plus bas = mieux ; QLIKE plus bas = mieux)

| H | RW vol | roll20 | GARCH | **EGARCH** | GJR |
|---|---|---|---|---|---|
| 20 | 3.94 | 3.94 | 3.64 | **3.31** | 3.64 |
| 40 | 4.93 | 5.17 | 4.74 | **4.24** | 4.74 |
| 90 | 7.90 | 8.16 | 6.80 | **5.97** | 6.80 |

EGARCH domine partout (RMSE, MAE, QLIKE, corr). L'asymétrie (terme de levier) compte sur
le maïs. **EGARCH ≈ HAR (EXT010)** : à H90, EGARCH RMSE 0.0597 vs HAR 0.0605 (équivalents,
léger avantage EGARCH au long horizon) ; GARCH/GJR sans asymétrie sont nettement derrière.

## Filtre de volatilité sur le score directionnel H90 (crop)

| Régime de vol prévue (GARCH) | n | DA | PnL moyen signé |
|---|---|---|---|
| tous | 3961 | 0.658 | +0.067 |
| faible vol (< p90) | 3562 | **0.688** | **+0.077** |
| forte vol (≥ p90) | 399 | **0.383** | **−0.022** |

**Résultat actionnable** : dans le décile haut de volatilité prévue, le score directionnel
**s'inverse** (DA 0.38 < 0.5) et **perd de l'argent** (PnL négatif). Filtrer ces jours
(s'abstenir quand la vol prévue est extrême) fait passer la DA de 0.658 à 0.688 et améliore
le PnL — exactement le rôle d'un gate de risque / d'un score de vente prudent.

## Conclusion
**KEEP** comme outil de risque. (1) EGARCH est le meilleur prévisionnel de volatilité
(≈ HAR, asymétrie en plus) ; pour un usage simple/robuste, HAR (EXT010) suffit, EGARCH en
variante asymétrie-aware. (2) Surtout, le **filtre de vol** est une vraie amélioration de
la gestion du risque : il neutralise le régime de forte volatilité où le signal
directionnel échoue. À intégrer comme gate du score de vente à l'étape 6. Contrairement à
la direction, **la volatilité se prévoit** (cf. EXT010).
