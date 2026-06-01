# EMA FINAL REPORT V2

> Rapport Phase 2 Euronext. Source EMA exploratoire/proxy ; verdict data NO_RELIABLE_PERIOD_ML.

**Équation directrice :** EMA = CBOT + EUR/USD + basis européen + résidu EU

## 1. Données EMA

**Label : EXPÉRIMENTAL.** Source Barchart proxy majoritaire ; pas de période ML fiable définitive.

## 2. Construction série continue

**Label : SOLIDE_MAIS_PROXY.** Raw pour prix absolu ; adjusted pour rendements/features ; no-roll pour sensibilité.

## 3. Relation EMA/CBOT

**Label : SOLIDE_STRUCTUREL.** Cointégration confirmée, transmission surtout contemporaine. Granger EMA→CBOT non confirmé OOF.

## 4. Basis EMA/CBOT

**Label : RÉSULTAT_PRINCIPAL_EXPÉRIMENTAL.** Le basis est persistant mais mean-reverting ; basis_reversion n'est pas EMA up.

## 5. Résidu EU

**Label : EXPÉRIMENTAL.** Catalogue des événements européens ; attribution automatique limitée par données exogènes manquantes.

## 6. Prédiction

**Label : RELATIVE_GO_DIRECT_NO_GO.** EMA direction directe reste faible ; le meilleur signal robuste est `relative_ema_outperformance_h40`.

`ema_vol_high_h20` ne doit pas être retenu comme meilleur signal : sa DA brute est trompeuse lorsque l'AUC, la balanced accuracy et le MCC restent faibles.

## 7. Table d'implémentation

| Module | Statut | Evidence |
|---|---|---|
| Cointégration EMA/CBOT | ✅ CONFIRMÉ | corr niveaux 0.941, demi-vie VECM 83.3j |
| Granger EMA→CBOT | ❌ NON CONFIRMÉ OOF | REJECTED |
| Basis mean reversion | ⚠️ STRUCTURE OUI, MODÈLE OOF FAIBLE | basis AR/reversion descriptif intéressant ; modèle basis_reversion_h20 AUC 0.467, balanced acc. 43.3% |
| Direction EMA absolue H20/H40 | ❌ NO_GO | H40 DA 51.9%, AUC 0.529, balanced acc. 51.9% |
| Direction EMA relative vs CBOT | ✅ MEILLEUR SIGNAL EMA ROBUSTE | relative_ema_outperformance_h40 : DA 64.0%, AUC 0.708, balanced acc. 64.2%, top20 77.1%, weekly AUC 0.728 |
| Faux bon signal volatilité EMA | ❌ REJETÉ COMME MEILLEUR SIGNAL | ema_vol_high_h20 : DA 65.8%, mais AUC 0.532, balanced acc. 51.3%, MCC 0.021 |
| Baseline basis z-score | ⚠️ RÈGLE SIMPLE TRÈS FORTE | relative H40 modèle balanced acc. 64.2%; meilleure baseline basis_z_rule 64.4% |
| Résidu EU shock | ⚠️ CATALOGUE OK, prédiction expérimentale | events 3σ 46 |
| CQR prix EMA | ❌ NO_GO | Prix absolu sous-couvert en v1. |
| CQR returns/basis/relative | ⚠️ TESTÉ | return_ema_h20 coverage 91.9%, verdict CQR_GO |
| Source données EMA | ⚠️ EXPLORATOIRE | Barchart proxy, verdict NO_RELIABLE_PERIOD_ML. |

## 8. Conclusion

- Le prix EMA est difficile à prédire directement : direction absolue H40 = NO_GO.
- Le meilleur signal EMA robuste est relative_ema_outperformance_h40, pas une cible de volatilité déséquilibrée.
- EMA/CBOT est fortement lié et cointégré, mais EMA→CBOT n'est pas validé OOF.
- Le basis EMA/CBOT est la composante la plus structurée ; une règle simple de basis z-score capture une grande partie du signal relatif.
- Le modèle basis_reversion_h20 reste faible en OOF même si le basis présente une structure de mean reversion descriptive.
- Le résidu EU sert surtout à cataloguer et expliquer les chocs propres à l'Europe.
- Les résultats EMA restent exploratoires tant qu'une source officielle n'est pas validée.

## 9. Suite recommandée

- Faire l'étude dédiée relative EMA/CBOT multi-horizon H10/H20/H40/H60/H90.
- Analyser les erreurs et les top20 signaux de relative_ema_outperformance_h40.
- Construire des filtres d'abstention : data quality, roll window, volatilité extrême, events majeurs.
- Tester un backtest relatif EMA/CBOT réaliste, avec slippage, roll cost, no-trade near expiration.
- Valider une source EMA officielle/autorisée avant tout claim production.