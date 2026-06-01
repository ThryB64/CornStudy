# Réflexion Phase 2 — Étude Euronext EMA

> Analyse experte reçue le 2026-05-24. Document de référence pour la Phase 2.

---

## Reformulation de l'objectif

**Ancien objectif (incorrect) :**
Prédire directement le prix Euronext EMA.

**Nouvel objectif (correct) :**
Comprendre et modéliser le prix Euronext EMA comme la combinaison :
1. Tendance mondiale CBOT (β1)
2. Effet change EUR/USD
3. Prime européenne basis EMA/CBOT
4. Chocs spécifiques Europe (résidu EU)

> Ce n'est pas "prédire EMA". C'est une vraie étude de transmission mondiale → Europe.

---

## Bilan état actuel

### Ce qui est très solide
1. Architecture raw / adjusted (series continues)
2. Roll audit (68 rolls, gap moyen 9.83 €/t, max 54.25 €/t)
3. Relation prix EMA/CBOT (corr 0.9409)
4. Cointégration EMA/CBOT (EG p=7.28e-7, VECM demi-vie 83j)
5. Importance du basis (R² passe de 0.211 à 0.936 avec basis)
6. Décomposition EMA = CBOT + basis (descriptif, contemporain)
7. Résidu EU stationnaire (ADF valide, 49 events à 3σ)
8. Échec documenté de la prédiction EMA directe (DA ≈ 0.467)

### Résultats fragiles ou à corriger

**Source EMA** : Barchart proxy exploratoire. verdict_period_ml = NO_RELIABLE_PERIOD.
→ Tous les résultats EMA doivent être marqués EXPÉRIMENTAL.

**Granger** : in-sample significatif, validation robuste rejetée (2022-driven).
→ Wording correct : "relation contemporaine forte, causalité Granger EMA→CBOT NON VALIDÉE OOF".

**Basis backtest** : 100% gagnants (+429 €/t) sans coûts, non-OOF.
→ Marquer : hypothèse de mean reversion, non un résultat de production.

**Feature importance** : fedfunds_level_zscore top MI=0.357.
→ Suspect : probablement proxy de régime temporel macro, pas driver causal EMA.
→ À vérifier : permutation OOF, importance par année, sans 2021-2022.

**Courbe EMA** : 1.25 contrats/date en moyenne, 14.9% dates avec 2+ contrats.
→ Pas une vraie courbe complète. On a surtout une série front + fragments.

**Open-Meteo audit** : n_zones=0 → CORRIGÉ 2026-05-24 : n_zones=5 (ukraine_west manquant).

**EC MARS / FranceAgriMer** : proxies Eurostat annuels, pas vrais bulletins mensuels.

**CQR prix EMA** : NO_GO (couverture H20=79.2%, H60=80.4%, objectif 90%).

---

## Structure en 4 Axes

### Axe 1 — Transmission mondiale → Europe
*Question : Comment CBOT se transmet à EMA ?*
- corrélations rolling
- cointégration
- VECM
- lead-lag
- Granger robuste
- décomposition returns

### Axe 2 — Basis EMA/CBOT
*Question : Quand le Matif est-il anormalement cher/bas vs CBOT ?*
- basis z-score
- stationnarité
- AR(1), half-life
- mean reversion OOF
- seuils z > 1.5 / 2 / 2.5
- stabilité annuelle

### Axe 3 — Résidu européen
*Question : Quels événements expliquent les décrochages EMA non expliqués par CBOT ?*
- résidus 2σ / 3σ
- event study
- MARS, Ukraine, météo EU, TTF/gaz, production FR/RO/HU, EUR/USD, import/export

### Axe 4 — Prédiction
*Meilleures cibles pour la suite :*
1. `basis_reversion_h20/h40/h60`
2. `relative_return_ema_minus_cbot_h20/h40`
3. `eu_residual_shock_h20`
4. `ema_volatility_regime_h20`
5. `y_up_h40_ema` (secondaire uniquement)

---

## Structure notebooks Phase 2

| NB | Titre | Priorité |
|---|---|---|
| NB2-00 | Data audit EMA officiel/proxy/exploratoire | P0 |
| NB2-01 | Contrats, rolls et séries continues | P0 |
| NB2-02 | Relation EMA/CBOT (transmission) | P0 |
| NB2-03 | Basis EMA/CBOT ⭐ | P1 |
| NB2-04 | Décomposition retour EMA | P1 |
| NB2-05 | Résidu EU et chocs européens | P1 |
| NB2-06 | Feature importance EMA (OOF, par année) | P2 |
| NB2-07 | Direction benchmarks EMA (nouvelles cibles) | P2 |
| NB2-08 | Event study EMA | P2 |
| NB2-09 | Volatilité EMA (améliorée) | P2 |
| NB2-10 | Prix/CQR expérimental (sur returns) | P3 |
| NB2-11 | Rapport final Euronext propre | P4 |

---

## Nouvelles expériences prioritaires

### EXP-1 : Prédire le basis
- Cibles : `basis_change_h20`, `basis_reversion_h20`
- Pourquoi : stationnaire + mean-reverting = meilleure cible stat

### EXP-2 : EMA relative performance
- Cible : `relative_return_h20 = return_EMA_h20 - return_CBOT_EUR_h20`
- Élimine la tendance mondiale. Très propre scientifiquement.

### EXP-3 : Résidu EU shock
- Cibles : `eu_residual_shock_up` (>+2σ), `eu_residual_shock_down` (<-2σ)
- Drivers : météo EU, Ukraine, EUR/USD, TTF, MARS, FR/RO/HU production

### EXP-4 : Validation hebdomadaire (mandatory)
- Reproduire TOUS les benchmarks en hebdomadaire
- Si signal disparaît en weekly → signal fragile

### EXP-5 : Années normales vs crises
- Normales : 2014-2019
- Crises : 2012, 2020, 2021, 2022
- Post-crise : 2023-2025

### EXP-6 : Leave-one-crisis-out
- Retirer chaque crise (2012, 2020, 2021, 2022) une par une
- Vérifier que le signal ne dépend pas d'une seule crise

---

## Règles méthodologiques à respecter

1. **Toujours classer** : DESCRIPTIF / PRÉDICTIF OOF / EXPLORATOIRE / NON VALIDÉ
2. **Séparer** : direction EMA absolue vs direction relative EMA-CBOT vs mean reversion basis
3. **Ne pas confondre** : basis reversion ≠ EMA up (le basis peut revenir sans que EMA monte)
4. **Attention** : targets construites trop proches des features → mean reversion mécanique
5. **Multiple testing** : bootstrap IC95 + BH + annual stability + holdout gelé

---

## Verdict expert

> **Ne pas forcer EMA direct pour l'instant.**
> Le meilleur signal EMA actuel est la **mean reversion du basis**.
> Axes prioritaires : Basis (NB2-03) → Résidu EU (NB2-05) → Prédiction cibles intelligentes.
