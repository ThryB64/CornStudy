# EXT011 — Résultats : benchmark trend-following

**Verdict : REJECT** (le trend-following ne marche pas sur le maïs) — mais **negative
control précieux** : il prouve que l'edge directionnel d'EXT024 n'est PAS du momentum.

## Protocole
Règles figées ex ante (aucun tuning) sur le CBOT continu : momentum 20/60/120, croisement
MA 50/200, EWMAC(16,64). Évalué en direction (signe du signal vs retour futur H40/H90) et
en stratégie (Sharpe/maxDD/hit/turnover, position causale t→t+1). Éval 2008-2023.

## Direction (DA vs classe majoritaire)

| Signal | DA H40 | DA H90 |
|---|---|---|
| mom20 | 0.495 | 0.482 |
| mom60 | 0.511 | 0.436 |
| mom120 | **0.409** | **0.388** |
| ma_50_200 | 0.440 | 0.440 |
| ewmac_16_64 | 0.482 | 0.408 |

**Tous les signaux de tendance sont sous 0.5** (pire que pile/face), surtout aux longs
lookbacks (mom120, EWMAC). Le maïs **ne tend pas** à ces horizons — il a une composante de
retour à la moyenne et de saisonnalité.

## Stratégie (global)

| Signal | Sharpe | max DD | hit | turnover |
|---|---|---|---|---|
| mom20 | 0.20 | −57 % | 0.495 | 0.20 |
| mom60 | −0.10 | −90 % | 0.492 | 0.13 |
| mom120 | −0.19 | −92 % | 0.488 | 0.07 |
| ma_50_200 | −0.24 | −95 % | 0.494 | 0.02 |
| ewmac_16_64 | −0.08 | −89 % | 0.489 | 0.05 |
| buy_and_hold | 0.01 | −77 % | 0.499 | — |

Seul mom20 a un Sharpe marginalement positif (0.20) mais avec −57 % de drawdown. Tous les
autres sont négatifs et pires que le buy-and-hold (≈0).

## Lecture
1. **Le trend-following échoue sur le maïs** (direction < 0.5, stratégies à Sharpe ≤ 0.20
   avec drawdowns énormes). Le maïs n'est pas un actif tendanciel : saisonnalité + retour à
   la moyenne dominent.
2. **Negative control clé** : l'edge directionnel d'EXT024 (DA 0.59-0.66) **n'est donc pas
   du momentum déguisé**. Un signe de momentum fixe est anti-prédictif ; le logit d'EXT024
   exploite la saisonnalité (dominante, EXT015) et apprend un coefficient de *retour à la
   moyenne* sur les retours courts (faibles importances en EXT015) + les fondamentaux. Le
   gain fondamental est réel et distinct du suivi de tendance.

## Conclusion
**REJECT** comme prédicteur/stratégie. Mais résultat utile : il **renforce la crédibilité**
du signal EXT024/EXT015 en éliminant l'explication « ce n'est que du momentum ». Le plancher
technique que tout signal fondamental devait battre est ici un plancher *négatif* — facile à
battre, ce qui ne flatte pas les fondamentaux mais confirme qu'ils apportent autre chose que
de la tendance.
