# Définition de "done" — Critères de complétion

## Principe

Chaque composant a des critères explicites et mesurables. "Done" n'est pas "le code est écrit". "Done" signifie que le composant fonctionne, est testé, et produit les sorties attendues.

---

## Plateforme AutoML

### Done si :

- [ ] Profiler lit n'importe quel CSV sans erreur et produit une fiche de caractérisation
- [ ] Profiler détecte correctement : régression, classification binaire, classification multi-classe, classification ordinale, série temporelle univariée, série temporelle multivariée
- [ ] Prétraitement applique imputation, encodage, normalisation, lags si série temporelle
- [ ] Walk-forward obligatoire si date détectée (split aléatoire interdit)
- [ ] Optuna optimise au moins Ridge, RF, HGB, LightGBM
- [ ] Meta-database produite avec OOF predictions (pas de leakage)
- [ ] Stacking converge et bat les modèles individuels en moyenne
- [ ] Rapport automatique généré avec benchmark, SHAP, limitations
- [ ] Tests passent sur 5 datasets différents (maïs, blé, soja, SP500, Titanic)
- [ ] Aucune exception non gérée sur un CSV propre quelconque

### Métriques de succès plateforme :

Sur un dataset de référence (ex. Corn prix CBOT) :
```
- Profiler détecte "série temporelle multivariée" ✅
- Walk-forward proposé automatiquement ✅
- LightGBM optimisé par Optuna > LightGBM hyperparams fixes ✅ (amélioration > 2%)
- Stacking > meilleur modèle individuel ✅ (amélioration > 1% RMSE)
- Rapport généré en < 5 minutes ✅
```

---

## Étude du maïs — Données

### Done si :

- [ ] Prix CBOT disponibles depuis 2000 minimum
- [ ] Météo Corn Belt 10 états disponibles quotidien depuis 2000
- [ ] WASDE disponible depuis 2000
- [ ] NASS QuickStats disponible depuis 2000
- [ ] CFTC COT disponible depuis 2009 (2013 avec données complètes)
- [ ] FRED macro disponible depuis 2000
- [ ] Anti-leakage audit passe sur toutes les sources
- [ ] Aucun gap > 5 jours dans les prix CBOT
- [ ] Forward-fill appliqué correctement sur sources hebdomadaires et mensuelles

### Non-blocant mais important :

- [ ] EIA éthanol avec vraie clé API (proxy corn/oil actif en attendant)
- [ ] Crop Progress disponible depuis 2005
- [ ] Drought Monitor disponible depuis 2000
- [ ] FAS Export Sales disponible depuis 2005
- [ ] Basis locale disponible (pour backtest réaliste)

---

## Étude du maïs — Modèles

### Done si :

- [ ] Toutes les baselines testées : zéro return, historical mean, seasonal naive, momentum
- [ ] Walk-forward en 4 horizons (J+5, J+10, J+20, J+30)
- [ ] Ridge factors bat la baseline zéro return sur RMSE
- [ ] LightGBM factors bat Ridge factors sur DA à J+20
- [ ] Stacking bat le meilleur modèle individuel sur au moins 2 horizons
- [ ] CQR couverture empirique ≥ 88% (cible 90%, tolérance 2%)
- [ ] Markov-switching converge sur 3 états (pas uniquement le fallback rule-based)
- [ ] SHAP importance calculée et sauvegardée (`shap_importance.parquet` non vide)
- [ ] Aucun claim non vérifié dans la table d'implémentation du rapport

### Métriques minimales sur J+20 (horizon principal agriculteur) :

```
Baseline zéro return : RMSE = R₀
Ridge factors : RMSE < R₀  [condition nécessaire]
LightGBM factors : DA ≥ 55%  [cible]
Stacking : RMSE ≤ RMSE(LightGBM) × 0.98  [légère amélioration]
CQR 90% : couverture empirique ≥ 88%
```

Si Ridge ne bat pas la baseline → problème de leakage à investiguer.

---

## Étude du maïs — Régimes

### Done si :

- [ ] Markov-switching 3 états converge (pas le fallback)
- [ ] Les 3 régimes ont des propriétés distinctes (return moyen significativement différent)
- [ ] Distribution des régimes cohérente avec l'histoire (pas 90% bull ou 90% bear)
- [ ] Régime "range" représente 40-60% du temps
- [ ] Régimes "bull" et "bear" représentent chacun 15-35% du temps
- [ ] La transition bull→bear est détectée en 2012-2013 (chute post-sécheresse)
- [ ] `regime_timeseries.parquet` est non vide et couvre la période complète

---

## Étude du maïs — Rapport

### Done si :

- [ ] `docs/PROFESSIONAL_STUDY_REPORT.md` existe et est à jour
- [ ] Table d'implémentation ✅/❌/⚠️ exacte
- [ ] Benchmark complet avec toutes les baselines
- [ ] SHAP importance affichée par famille et par horizon
- [ ] Distribution des régimes documentée
- [ ] Couverture CQR empirique vs cible documentée
- [ ] Ablation study par famille documentée
- [ ] Limites honnêtement listées
- [ ] Pas de claim non implémenté marqué ✅

---

## Backtest agriculteur

### Done si :

- [ ] Au moins 4 stratégies testées (récolte, mensuelle, tiers, système)
- [ ] Période couverte ≥ 10 années complètes
- [ ] Capture rate calculé pour chaque année
- [ ] Capture rate moyen affiché par stratégie
- [ ] % années gagnantes calculé par stratégie vs vente récolte
- [ ] Pire année documentée (drawdown de revenu)
- [ ] Coûts de stockage intégrés dans le calcul
- [ ] Limites documentées (pas de basis locale, pas de slippage)

### Seuil de succès minimal :

```
Capture rate (système) > Capture rate (vente récolte) sur 70%+ des années testées
```

Si ce seuil n'est pas atteint, le système n'apporte pas de valeur ajoutée. C'est un résultat valide (et honnête) à documenter.

---

## Pipeline quotidien

### Done si :

- [ ] `make daily` tourne sans erreur sur un jour ouvré
- [ ] Prix CBOT mis à jour automatiquement
- [ ] Prédictions produites pour les 4 horizons
- [ ] Snapshot JSON sauvegardé avec toutes les informations
- [ ] Rapport quotidien Markdown généré
- [ ] Validation des prédictions passées effectuée
- [ ] Log d'exécution sans erreur critique
- [ ] Temps d'exécution total < 15 minutes

---

## Projet global — "Fini"

Le projet est terminé quand :

1. ✅ Plateforme AutoML testée sur 5 datasets différents
2. ✅ Données maïs complètes depuis 2000 (avec CFTC depuis 2013)
3. ✅ Modèles battent toutes les baselines sur J+20
4. ✅ CQR calibré à 90% empirique
5. ✅ Markov-switching converge et produit 3 régimes distincts
6. ✅ SHAP importance disponible par famille et par horizon
7. ✅ Backtest agriculteur sur 10+ ans avec gain documenté
8. ✅ Pipeline quotidien tourne automatiquement
9. ✅ Rapport final complet et honnête (pas de ✅ non mérité)
10. ✅ Journal des expériences complet (EXP-001 à EXP-N documentées)

---

## Ce qui ne compte PAS comme "done"

- "Le code est écrit" — sans résultats mesurés
- "J'ai ajouté LightGBM" — sans vérifier qu'il bat Ridge
- "CQR est implémenté" — sans vérifier que `cqr_results.parquet` est non vide
- "SHAP est fait" — sans vérifier que `shap_importance.parquet` est non vide
- "Markov converge" — sans vérifier que les 3 régimes ont des propriétés distinctes
- "Le backtest est bon" — sans avoir testé sur au moins 10 années complètes
