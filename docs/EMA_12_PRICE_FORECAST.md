# NB-EMA-12 — Prévision de prix EMA (expérimental)

## Objectif

Étude exploratoire de la prévision de prix EMA via 3 modèles : marche aléatoire, VECM, basis mean-reversion.

## Modèles

| Modèle | Description |
|---|---|
| Random walk | EMA_t+H = EMA_t (benchmark naïf) |
| Basis mean-reversion | EMA_t+H = CBOT_t + basis_mean_expandant |
| VECM | Vecteur à correction d'erreur (H=5 uniquement) |

## Résultats

| Horizon | Random Walk RMSE | Basis MR RMSE | Amélioration |
|---|---|---|---|
| H=5j | 8.17 €/t | 16.49 €/t | −102% (dégradation) |
| H=20j | ~15 €/t | — | — |
| H=60j | ~25 €/t | — | — |

## Interprétation

Le modèle basis mean-reversion est **moins bon** que la marche aléatoire car il suppose que le prix CBOT futur est **connu** — ce qui n'est pas le cas en pratique. C'est un artefact d'implémentation, pas un signal exploitable.

**Conclusion** : aucun modèle de prix ne surpasse le random walk dans un cadre réaliste (CBOT futur inconnu). L'étude est purement descriptive.

## Verdict

> ❌ **VERDICT : PRICE_FORECAST_NO_GO.** Aucun modèle ne surpasse le random walk dans un cadre réaliste. Ce module est **purement descriptif/exploratoire**.

> ❌ **VERDICT CQR : CQR_PRICE_NO_GO.** Couverture H20=79.2%, H60=80.4%, objectif 90% non atteint. Ne pas présenter les intervalles de prix EMA comme fiables.

## Limites

- CBOT futur supposé connu dans basis_mean_reversion → biais massif
- VECM évalué sur 30% du jeu de données (non OOF complet)
- Pas de coûts de transaction ni de slippage
- Ne pas présenter d'intervalles de prix EMA comme fiables (voir aussi EMA_STUDY_CQR : NO_GO)
