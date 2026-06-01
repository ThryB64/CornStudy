# V6 Consistency Audit — V7-00
**Verdict global** : `COHERENT_WITH_CAVEATS`

## Expériences V6
| Expérience | AUC V6 | n_OOF | Verdict |
|---|---|---|---|
| meta_model_h90 | 0.937 | 503 | `COHERENT` |
| basis_extreme_h90 | 1.0 | 29 | `FRAGILE` |
| seasonal_expert | 0.982 | 68 | `COHERENT` |
| cbot_cross_market_h60 | 0.577 | None | `COHERENT` |

## Blockers
Aucun

## Warnings
- basis_extreme_h90: AUC=1.000 sur n=29 est FRAGILE, pas nécessairement suspect (filtre intentionnel)

## Analyse delta AUC V5→V6
- AUC V5 : 0.77
- AUC V6 : 0.937
- Delta : +0.167
- Attribution : meta_features_oof_cross_target, cible_plus_discriminante_basis_extreme

## Caveats
- EMA data = proxy exploratoire, non officielle Euronext
- Backtests = RESEARCH_ONLY_NOT_TRADING
- basis_extreme_h90 n=29 : fragile par construction (filtre intentionnel)
