---
id: PAPER009
source_type: paper
title: Forecasting Volatility of Returns for Corn Using GARCH Models
priority: high
status: analyzed_2026-06-12
note: Musunuru, Yu, Larson (~2013, Texas Journal of Agriculture and Natural Resources) — à confirmer.
---
# GARCH/TGARCH/EGARCH sur le corn (Musunuru, Yu, Larson)

## 1. Référence

Musunuru, N., Yu, M., Larson, A. (~2013). Forecasting Volatility of Returns for Corn Using GARCH Models. Texas J. of Agriculture and Natural Resources (à confirmer).

## 2. Sujet

Modéliser et prévoir la volatilité des retours corn futures avec la famille GARCH ; tester l'asymétrie (les hausses et baisses ont-elles le même effet sur la vol future ?).

## 3. Données

Retours quotidiens corn futures CBOT, années 1990s-2010s.

## 4. Méthode

GARCH(1,1), TGARCH, EGARCH ; sélection par critères d'information ; prévision de vol hors échantillon.

## 5. Résultats importants

- GARCH(1,1) capture l'essentiel du clustering de vol du corn.
- **Asymétrie INVERSE aux actions** : sur les grains, les chocs POSITIFS de prix (peur de pénurie) augmentent davantage la vol future que les chocs négatifs — l'« inverse leverage effect » des commodities.
- La saisonnalité de la vol (été) n'est pas entièrement capturée par GARCH standard.

## 6. Apport pour notre étude

- Notre `realized_vol_60d` (régimes) est une fenêtre brute ; un GARCH(1,1) donne une vol conditionnelle plus réactive pour les MÊMES usages (gates UNCERTAIN_VOL, sizing).
- L'inverse leverage est une feature de contexte : vol conditionnelle post-hausse ≠ post-baisse → affiner le drawdown_risk V23 (AUC 0.74).
- À combiner avec PAPER042 (saisonnalité de vol + Samuelson) pour une vol de référence corn complète.

## 7. Hypothèses testables

- H1 (EXT009) : GARCH(1,1) estimé en expandant sur CBOT : la vol conditionnelle à J prédit-elle la vol réalisée [J, J+20] mieux que realized_vol_60d ? (Baseline de vol propre, utile à V124/V128.)
- H2 : EGARCH : le terme d'asymétrie est-il positif (inverse leverage) sur notre période 2010-2023 ? Si oui, le flag « choc haussier récent » devient un amplificateur de risque ADVERSE court terme.

## 8. Risques et limites

Vol ≠ direction (n'améliore pas la DA en soi) ; estimation GARCH sur fenêtres expandantes = coûteux mais trivial ; `arch` dispo en import optionnel (règle projet).

## 9. EXT associées

EXT009 (principal), EXT010 (HAR concurrent), EXT017.

## 10. Conclusion

**Priorité haute** (bloc 2 benchmarks) : EXT009 est peu risqué, à coupler avec EXT010 (HAR) dans une seule expérience de vol.
