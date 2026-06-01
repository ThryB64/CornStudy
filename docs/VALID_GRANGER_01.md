# VALID-GRANGER-01 — Validation Granger EMA→CBOT

> Source exploratoire (Barchart proxy). Résultats expérimentaux.

## Verdict final : **REJETÉ (1/5 tests robustes)**

| Test | Verdict |
|---|---|
| T1 — Robustesse temporelle (3 sous-périodes) | NOT_ROBUST |
| T2 — Robustesse aux lags (max_lag 1/3/5/10) | NOT_ROBUST |
| T3 — Neutralisation log vs pct returns | ROBUST |
| T4 — Validation OOF (train/test 50/50) | NOT_SIGNIFICANT |
| T5 — Exclusion 2022 (guerre Ukraine) | 2022_DRIVEN |

## Interprétation

**Le signal Granger EMA→CBOT est piloté par la période 2022** et ne se confirme pas hors d'échantillon (T4: NOT_SIGNIFICANT en période test).

- Le signal est présent sur l'ensemble complet (in-sample) avec p ≈ 2.6e-6 (NB-EMA-04), mais disparaît dès qu'on exclut 2022 ou qu'on valide sur la deuxième moitié de la série.
- La robustesse ne tient que pour T3 (cohérence entre log-returns et pct-returns), ce qui confirme que la transformation mathématique n'est pas le problème — c'est le signal lui-même qui est fragile.

## Conclusion pour l'étude

**Granger EMA→CBOT : REJETÉ en validation robuste OOF.** Ne pas utiliser ce résultat pour affirmer que EMA prédit CBOT.

La causalité inverse **CBOT→EMA** reste robuste et économiquement sensée (transmission mondiale → régionale). À retenir : la relation EMA/CBOT est forte et **contemporaine**, pas prédictive dans le sens EMA→CBOT.

## Artefact produit

`artefacts/ema_study/ema_granger_validation.json`
