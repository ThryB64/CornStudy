# EXT001 — Résultats : météo par fenêtres agronomiques

**Verdict : REJECT.**

## Question
La météo réalisée, agrégée par stade phénologique du maïs et pondérée par la
production des États, améliore-t-elle la prévision du log-retour CBOT t→t+h ?

## Protocole
Harnais commun (`_common/ext_harness.py`) : walk-forward expandant, refit annuel
purgé, Ridge α=10 fixe, standardisation/imputation train-only, holdout 2024+
exclu. BASE = marché seul (ret_5d, ret_20d, vol_20, saison) ; FAMILLE = 11
anomalies de fenêtres (gdd/prcp par stade + jours de chaleur en pollinisation).

## Résultats (BASE vs BASE+FAMILLE)

| H | RMSE base | RMSE +fam | ΔRMSE % | R² base | R² +fam | ΔDA | DM p |
|---|---|---|---|---|---|---|---|
| 5 | 0.0399 | 0.0433 | +8.5 % | −0.002 | −0.180 | +0.017 | 1.7e-07 |
| 20 | 0.0802 | 0.1014 | +26.5 % | +0.006 | −0.589 | +0.004 | 3.1e-05 |
| 40 | 0.1106 | 0.1573 | +42.3 % | +0.023 | −0.979 | +0.007 | 2.8e-04 |
| 90 | 0.1579 | 0.2155 | +36.5 % | +0.051 | −0.770 | −0.015 | 4.8e-03 |

## Lecture
Ajouter les features météo **dégrade fortement et de façon significative** le RMSE
out-of-sample à tous les horizons (DM p<0.01, mais dans le sens *famille pire*). Le
R² passe de légèrement positif à franchement négatif (jusqu'à −0.98) : surapprentissage
massif, les coefficients météo estimés en expandant ne généralisent pas. Les micro-gains
de direction (+0.4 à +1.7 pt) sont noyés dans une erreur quadratique bien pire et ne
sont pas exploitables.

## Conclusion
Cohérent avec la découverte interne V45 : la météo *réalisée* est déjà intégrée par le
marché (price-in par anticipation) et n'apporte pas d'information directionnelle sur le
CBOT. L'agrégation par fenêtre agronomique ne change pas ce constat. **REJECT** pour la
direction CBOT ; la seule voie météo cohérente reste EXT033 (révisions de *prévisions*).
