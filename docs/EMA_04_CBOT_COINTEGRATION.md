# EMA 04 — Relation EMA/CBOT : Cointégration et Causalité de Granger

> Source exploratoire (Barchart proxy). Résultats expérimentaux.

## Résultats clés

| Métrique | Valeur | Verdict |
|---|---|---|
| Engle-Granger stat | -6.16 (p = 7.3e-7) | COINTÉGRÉES |
| Johansen relations cointégrantes | 2 | CONFIRMÉ |
| Demi-vie VECM (mean-reversion) | 83 jours | — |
| VECM alpha EMA | -0.0083 | Correction lente |
| VECM beta | [1.0, -1.22] | EMA ≈ 1.22 × CBOT |
| Granger CBOT → EMA | p ≈ 9.1e-16 in-sample | Transmission forte, surtout contemporaine |
| Granger EMA → CBOT | p ≈ 2.6e-6 in-sample | NON CONFIRMÉ OOF |
| Corrélation niveaux | 0.941 | — |
| Corrélation retours journaliers | 0.460 | — |
| Corrélation rolling 260j (moy.) | 0.719 | — |

## Interprétation

**Cointégration** : EMA et CBOT sont cointégrées à 1% (Engle-Granger, Johansen). Une relation d'équilibre à long terme existe. La demi-vie VECM de 83 jours indique une convergence lente — les déviations (basis) persistent plusieurs mois.

**Granger CBOT → EMA** : très significatif in-sample (p ≈ 9e-16). Ce résultat confirme surtout une transmission mondiale vers EMA et une relation contemporaine forte. Il ne doit pas être présenté comme une prédiction robuste hors échantillon sans validation dédiée.

**Granger EMA → CBOT** : significatif in-sample (p ≈ 2.6e-6), mais **NON CONFIRMÉ en validation OOF robuste** (voir VALID-GRANGER-01). Signal 2022-driven, disparaît en test. Ne pas interpréter comme une causalité établie.

**Corrélation des retours** : 0.460, nettement inférieure à la corrélation des niveaux (0.941). Le signal journalier est bruité — CBOT n'explique pas mécaniquement les retours quotidiens d'EMA.

## Mise en garde

Tous les résultats sont in-sample sauf indication contraire. **Granger EMA→CBOT : NON CONFIRMÉ en validation OOF robuste (2022-driven).** La relation est forte et contemporaine. Ce n'est pas une relation de prédiction EMA→CBOT.

## Artefact produit

`artefacts/ema_study/ema_cbot_cointegration.json`
