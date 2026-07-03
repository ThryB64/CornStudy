---
id: REPO007
source_type: repository
title: chrism2671/PyTrendFollow
priority: medium
status: analyzed_2026-06-12
---
# chrism2671/PyTrendFollow

## 1. Identification

- URL : https://github.com/chrism2671/PyTrendFollow — propriétaire : Chris M.
- Licence : ✅ présente
- État : cloné ; 35 py + 6 notebooks + docs pédagogiques (`Introduction to Trend Following.ipynb`, `Working with Prices.ipynb`)
- Langage : Python (style Carver/systematic, IB + Quandl)

## 2. Objectif

Trading systématique trend-following multi-futures « hedge fund style » : signaux EWMAC, dimensionnement par volatilité cible (~25 %), roll automatique des contrats, backtest + exécution IB.

## 3. Données utilisées

Contrats futures individuels (Quandl historique / IB live), gestion du roll intégrée.

## 4. Cible prédite

Aucune prédiction ponctuelle : position continue proportionnelle au signal de tendance normalisé par la vol.

## 5. Horizons

Moyen terme (croisements EWMA multi-vitesses, typiquement 16-64j) — recouvre nos H20-H120.

## 6. Modèles

Trend-following EWMAC, vol targeting, agrégation multi-instruments. Package `arch` en dépendance (vol).

## 7. Méthode d'évaluation

Backtest historique avec coûts ; le « ~20 %/an à vol 25 % » du README est in-sample/sélectionné — à ne pas prendre au pied de la lettre. Pas de walk-forward formel des paramètres.

## 8. Risques de fuite

Paramètres EWMAC standards (peu de tuning = peu de fuite) ; risque résiduel : choix d'instruments survivants. Pour EXT011 : fixer les paramètres ex ante (16/64, vol target), aucun tuning sur nos années de test.

## 9. Réutilisable

- **Méthode** : EWMAC + vol targeting = benchmark technique honnête pour CBOT corn ; structure de gestion du roll (croise EXT006).
- **Métrique** : Sharpe net de coûts du trend pur = plancher que nos signaux fondamentaux doivent battre sur les mêmes périodes.

## 10. Faible / inutilisable

Infra IB/Quandl morte pour nous ; multi-marchés inutile (nous : corn + basis EMA) ; pas d'évaluation directionnelle (AUC/DA) — il faudra convertir le signal en direction pour comparer à nos métriques.

## 11. Hypothèses testables

- H1 : EWMAC(16,64) + vol targeting sur CBOT corn continu : DA et PnL net coût 3-5 €/t éq. sur 2010-2023 — le trend pur bat-il la RW ? (Notre V31+ : uptrend CBOT divise l'ADVERSE par 2 — le trend a déjà une valeur de CONTEXTE prouvée chez nous.)
- H2 : le signal EWMAC CBOT comme variable de contexte du basis (remplaçant/complétant notre `above_trend_252`) — améliore-t-il le gating short basis-haut ?

## 12. EXT associées

EXT011 (principal), EXT017 (trend comme régime), EXT006 (logique de roll).

## 13. Conclusion

**À garder pour plus tard** (bloc benchmarks) : référence propre pour EXT011. Paramètres figés ex ante, zéro tuning.
