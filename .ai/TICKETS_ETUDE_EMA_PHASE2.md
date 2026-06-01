# Tickets — Phase 2 Euronext EMA

> Créé 2026-05-24. Suite de TICKETS_ETUDE_EMA.md (Phase 1 DONE).
> Basé sur analyse experte du 2026-05-24.
> Réf : `.ai/REFLEXION_PHASE2_EMA.md`
>
> **Objectif reformulé :** EMA = CBOT + EUR/USD + basis + résidu EU.
> **Règle absolue :** anti-leakage shift(1), OOF strict, IC95 bootstrap, BH FDR.
> **Wording gelé :** source EMA = exploratoire/proxy. Granger EMA→CBOT = NON VALIDÉ OOF.

---

## Index

| ID | Titre | Bloc | Priorité | Statut |
|---|---|---|---|---|
| FIX-P0-01 | Correction incohérences scientifiques P0 | Nettoyage | P0 | DONE |
| NB2-00 | Audit data EMA source qualité | Fondations | P0 | DONE |
| NB2-01 | Contrats, rolls, séries continues v2 | Fondations | P0 | DONE |
| NB2-02 | Relation EMA/CBOT transmission v2 | Fondations | P0 | DONE |
| NB2-03 | Basis EMA/CBOT — étude complète ⭐ | Basis | P1 | DONE |
| NB2-04 | Décomposition retour EMA (descriptif vs prédictif) | Décomposition | P1 | DONE |
| NB2-05 | Résidu EU et chocs européens ⭐ | Résidu EU | P1 | DONE |
| NB2-06 | Feature importance OOF + par année | Prédiction | P2 | DONE |
| NB2-07 | Direction benchmarks EMA — nouvelles cibles ⭐ | Prédiction | P2 | DONE |
| NB2-08 | Event study EMA | Prédiction | P2 | DONE |
| NB2-09 | Volatilité EMA améliorée | Prédiction | P2 | DONE |
| NB2-10 | CQR sur returns (pas sur prix) | Prédiction | P3 | DONE |
| NB2-11 | Rapport final Euronext | Rapport | P4 | DONE |
| FIX-EMA-01 | Target NaN integrity | Debug scientifique | P0 | DONE |
| FIX-EMA-02 | Sélection robuste meilleur signal | Debug scientifique | P0 | DONE |
| FIX-EMA-03 | Raw vs adjusted vs no-roll après fix target | Debug scientifique | P0 | DONE |
| FIX-EMA-04 | Benchmark hebdomadaire généralisé | Debug scientifique | P1 | DONE |
| FIX-EMA-05 | Split qualité données EMA | Debug scientifique | P1 | DONE |
| FIX-EMA-06 | Baselines intelligentes EMA | Debug scientifique | P1 | DONE |
| FIX-EMA-07 | Indicateur premium EMA/CBOT | Debug scientifique | P2 | DONE |
| FIX-EMA-08 | Backtests théoriques relatifs/basis | Debug scientifique | P2 | DONE |
| REL-EMA-01 | Corriger rapport final relatif EMA/CBOT | Suite relative | P0 | DONE |
| REL-EMA-02 | Étude relative EMA/CBOT reproductible | Suite relative | P0 | DONE |
| REL-EMA-03 | Analyse des erreurs relative H40 | Suite relative | P1 | DONE |
| REL-EMA-04 | Filtres d'abstention relative H40 | Suite relative | P1 | DONE |
| REL-EMA-05 | Backtest relatif EMA/CBOT réaliste | Suite relative | P1 | DONE |
| EMA-NEXT-01 | Rapport final V3 pivot prime européenne | Suite premium | P0 | DONE |
| EMA-NEXT-02 | Notebook narratif relatif EMA/CBOT | Suite premium | P0 | BLOCKED |
| EMA-NEXT-03 | Feature importance relative H40/H90 | Suite premium | P1 | DONE |
| EMA-NEXT-04 | Étude saisonnière relative EMA/CBOT | Suite premium | P1 | DONE |
| EMA-PREM-01 | ML vs basis z-score vs signal combiné | Premium | P1 | DONE |
| EMA-PREM-02 | European Premium Indicator V2 | Premium | P1 | DONE |
| EMA-BT-01 | Backtest relatif V2 coûts réalistes | Backtest | P1 | DONE |
| FINAL-EMA-01 | Rapport final EMA V3 | Synthèse | P2 | DONE |
| EMA-V4-01 | Rapport final EMA V4 | V4 | P0 | DONE |
| EMA-H90-01 | Stress test strict H90 | V4 | P0 | DONE |
| EMA-ERR-02 | Error archaeology relative H40/H90 | V4 | P1 | DONE |
| EMA-SEASON-02 | Seasonal premium regime study | V4 | P1 | DONE |
| EMA-BT-03 | Backtest relatif V3 exécution réaliste | V4 | P1 | DONE |
| EMA-V5-01 | Target lab EMA nouvelles cibles | V5 | P0 | DONE |
| EMA-V5-02 | Cross-data interaction lab premium | V5 | P1 | DONE |
| EMA-V5-03 | Modèle hiérarchique CBOT + prime EU | V5 | P1 | DONE |
| EMA-V5-04 | Synthèse finale V5 enrichie | V5 | P2 | DONE |
| V6-00 | Experiment registry global | V6 | P0 | DONE |
| V6-01 | Target labs EMA + CBOT complets | V6 | P0 | DONE |
| V6-02 | Cross-target OOF factory + meta-features | V6 | P0 | DONE |
| V6-03 | Meta-model premium + confiance + abstention | V6 | P1 | DONE |
| V6-04 | Roll-aware, seasonal experts, backtests V6 | V6 | P1 | DONE |
| V6-05 | CBOT/cross-market/decomposition/event studies | V6 | P1 | DONE |
| V6-06 | Rapport final V6 + review intégrale | V6 | P2 | DONE |
| V6-17 | Notebook V6 complet | V6 | P2 | BLOCKED |

---

## BLOC P0 — CORRECTIONS ET FONDATIONS

---

### FIX-P0-01 — Correction incohérences scientifiques P0

**Priorité :** P0
**Type :** correction
**Statut :** DONE (review utilisateur 2026-05-24 : "Fait tout les tickets intégralement")
**Complexité :** simple

#### Objectif

Corriger 7 incohérences identifiées dans l'analyse experte avant tout travail Phase 2.

#### Liste des corrections

**1. Open-Meteo audit n_zones=0 → DONE 2026-05-24**
- Fichier corrigé : `artefacts/ema_study/openmeteo_eu_audit.json`
- n_zones=5 (ukraine_west manquant documenté)

**2. Wording Granger dans docs**
- Fichiers : `docs/EMA_04_CBOT_RELATION.md`, `docs/EMA_STUDY_FINAL_REPORT.md`
- Chercher "EMA → CBOT" ou "Granger validé"
- Remplacer par : "Granger EMA→CBOT NON CONFIRMÉ en validation OOF robuste (2022-driven)"
- Garder : "relation contemporaine forte confirmée"

**3. Basis backtest mark non-OOF**
- Fichier : `docs/EMA_07_BASIS_FORMAL.md`
- Ajouter : "⚠️ Backtest exploratoire : sans coûts, sans contrainte liquidité, non walk-forward OOF. À ne pas présenter comme résultat de production."

**4. Feature importance fedfunds suspect**
- Fichier : `docs/EMA_10_FEATURE_IMPORTANCE.md`
- Ajouter note : "fedfunds_level_zscore : probable proxy de régime temporel macro (2021-2022), non confirmé comme driver causal direct EMA. Vérification OOF requise."

**5. CQR verdict NO_GO explicite**
- Fichier : `docs/EMA_12_PRICE_FORECAST.md`
- Ajouter encadré : "VERDICT : CQR_PRICE_NO_GO. Couverture H20=79.2%, H60=80.4%. Objectif 90% non atteint. Ne pas présenter d'intervalles EMA comme fiables."

**6. Courbe EMA : pas une vraie courbe**
- Fichier : `docs/DATA_EU_01_EC_MARS.md` (ou rapport final)
- Dans tout endroit mentionnant "courbe Euronext" : ajouter "1.25 contrats/date en moyenne, 14.9% dates avec ≥2 contrats. Ce n'est pas une vraie courbe multi-maturité."

**7. Source EMA label partout**
- Dans `artefacts/ema_study/ema_final_report.json` et `docs/EMA_STUDY_FINAL_REPORT.md`
- Ajouter section : `"source_quality": "exploratoire_barchart_proxy"`, `"verdict_data": "NO_RELIABLE_PERIOD_ML"`

#### Fichiers à modifier
- `artefacts/ema_study/openmeteo_eu_audit.json` ✅ DONE
- `docs/EMA_04_CBOT_RELATION.md`
- `docs/EMA_STUDY_FINAL_REPORT.md`
- `docs/EMA_07_BASIS_FORMAL.md`
- `docs/EMA_10_FEATURE_IMPORTANCE.md`
- `docs/EMA_12_PRICE_FORECAST.md`
- `artefacts/ema_study/ema_final_report.json`

#### Résultat ticket (2026-05-24)

- Wording Granger durci dans le fichier réel `docs/EMA_04_CBOT_COINTEGRATION.md` : EMA→CBOT = NON CONFIRMÉ OOF, relation surtout contemporaine.
- Rapport final Markdown enrichi avec `source_quality`, `verdict_data`, CQR_PRICE_NO_GO et courbe EMA partielle.
- `artefacts/ema_study/ema_final_report.json` enrichi avec `source_quality="exploratoire_barchart_proxy"` et `verdict_data="NO_RELIABLE_PERIOD_ML"`.
- Vérification : `python3 -m json.tool artefacts/ema_study/ema_final_report.json` PASS.
- Tests non lancés : pas de test code, modifications docs/JSON uniquement.

---

### NB2-00 — Audit data EMA source qualité

**Priorité :** P0
**Type :** module + doc + artefact
**Statut :** DONE
**Dépendances :** FIX-P0-01
**Complexité :** moyen

#### Objectif

Produire un audit data EMA complet avec labels source officielle/proxy/exploratoire et périodes utilisables pour la recherche.

#### Contenu du module `src/mais/research/ema_data_audit_v2.py`

```
Livrables :
- couverture par année (2010-2026)
- couverture par contrat H/M/Q/X
- gaps jours manquants
- source label : officiel / proxy_barchart / exploratoire
- lignes aberrantes (prix > 3σ)
- volume/OI disponibilité
- contrats actifs par date (mean, min, max)
- comparaison proxy vs officiel récent (2025-2026)
- periods_usable_for_research
- periods_excluded
- data_quality_score par année
```

#### Sorties
- `artefacts/ema_study/ema_data_audit_v2.json`
- `docs/EMA_DATA_AUDIT_V2.md`

#### Anti-leakage
Aucun (c'est un audit, pas une feature).

---

### NB2-01 — Contrats, rolls, séries continues v2

**Priorité :** P0
**Type :** module + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-00
**Complexité :** simple

#### Objectif

Documenter proprement l'architecture raw/adjusted avec impact sur returns.

#### Contenu `src/mais/research/ema_contracts_v2.py`

```
- front raw vs adjusted : plot retours comparés
- roll gaps distribution
- fenêtres H20/H40/H60 traversant un roll (%)
- impact sur DA : raw vs adjusted
- harvest_nov couverture par crop year
- recommandation : raw pour prix absolu, adjusted pour returns/features tech
```

#### Sorties
- `artefacts/ema_study/ema_contracts_v2.json`
- `docs/EMA_CONTRACTS_V2.md`

---

### NB2-02 — Relation EMA/CBOT transmission v2

**Priorité :** P0
**Type :** module + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-00
**Complexité :** moyen

#### Objectif

Version améliorée de la relation EMA/CBOT avec rolling correlations et distinction in-sample/OOF.

#### Contenu `src/mais/research/ema_cbot_relation_v2.py`

```
- corrélation prix rolling 60j / 260j (avec plot)
- corrélation rendements rolling (vs corrélation statique)
- lead-lag -5j à +5j
- VECM half-life (83j confirmé)
- Granger : résultats in-sample ET OOF séparément
- transmission β1 CBOT stable par période ?
- R² rolling décomposition
```

**Wording obligatoire dans la doc :**
- "Granger EMA→CBOT IN-SAMPLE : significatif mais NON CONFIRMÉ en validation robuste OOF"
- "La relation est surtout contemporaine"

#### Sorties
- `artefacts/ema_study/ema_cbot_relation_v2.json`
- `docs/EMA_CBOT_RELATION_V2.md`

---

## BLOC P1 — BASIS, DÉCOMPOSITION, RÉSIDU EU

---

### NB2-03 — Basis EMA/CBOT — étude complète ⭐

**Priorité :** P1
**Type :** module + doc + artefact
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-02
**Complexité :** complexe

#### Objectif

Étude complète et rigoureuse du basis EMA/CBOT. C'est le module le plus important Phase 2.

#### Contenu `src/mais/research/ema_basis_v2.py`

```
Section 1 — Statistiques descriptives
- distribution basis (mean 37.25, std 15.50, min -11.71, max 110.66)
- basis positif : 98.9% du temps
- ADF/KPSS stationnarité
- AR(1) phi=0.970, half-life=22.8j
- ACF/PACF

Section 2 — Z-score et régimes
- basis_zscore = (basis - EWM_mean_60j) / EWM_std_60j (expanding, shift(1))
- régimes : high_basis (z>+1.5, z>+2), normal, low_basis (z<-1.5, z<-2)
- distribution par régime
- durée moyenne de chaque régime

Section 3 — Mean reversion walk-forward OOF ⭐
- seuils gelés sur train, appliqués sur test
- thresholds testés : z > 1.0, 1.5, 2.0, 2.5
- horizons : H20, H40, H60
- métriques : hit_rate, DA, IC95 bootstrap 500 tirages, BH correction
- annual stability (DA par année)
- attention roll H60 : ~99% traverse un roll → utiliser adjusted
- distinction : mean reversion du BASIS vs direction EMA absolue

Section 4 — Validation hebdomadaire
- reproduire mean reversion en weekly
- si DA disparaît en weekly → signal fragile

Section 5 — Stabilité par période
- 2010-2014 / 2015-2019 / 2020-2022 / 2023-2026
- le signal basis est-il stable ?
```

**Règle anti-confusion obligatoire dans doc :**
"Le basis peut revenir vers sa moyenne de 3 façons : EMA baisse, CBOT monte, ou les deux évoluent ensemble. basis_reversion ≠ EMA up."

#### Sorties
- `artefacts/ema_study/ema_basis_v2.json`
- `docs/EMA_BASIS_V2.md`
- `tests/test_ema_basis_v2.py` (≥ 8 tests)

---

### NB2-04 — Décomposition retour EMA (descriptif vs prédictif)

**Priorité :** P1
**Type :** module + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-03
**Complexité :** moyen

#### Objectif

Séparer clairement la décomposition descriptive (contemporaine) de la décomposition prédictive (décalée).

#### Contenu `src/mais/research/ema_decomposition_v2.py`

```
Bloc 1 — DESCRIPTIF (variables contemporaines)
ΔEMA_t = β1 × ΔCBOT_t + β2 × Δbasis_t + résidu_t
→ R² attendu ≈ 0.936
→ Label : "Modèle descriptif, NON prédictif (variables contemporaines)"

Bloc 2 — PRÉDICTIF (variables décalées shift(1))
ΔEMA_t+H = β1 × ΔCBOT_t + β2 × basis_z_t + β3 × vol_t + ...
→ R² attendu < 0.05 (honnête)
→ Walk-forward OOF
→ Comparer avec naive (drift)

Bloc 3 — Décomposition rolling par fenêtre 260j
β1(t) = sensibilité CBOT rolling (stable ?)
β2(t) = sensibilité basis rolling (varie en crise ?)

Bloc 4 — Décomposition par régime
β1, β2 en régime normal vs crise
```

**Label obligatoire :** Toujours indiquer DESCRIPTIF / PRÉDICTIF sur chaque résultat.

#### Sorties
- `artefacts/ema_study/ema_decomposition_v2.json`
- `docs/EMA_DECOMPOSITION_V2.md`

---

### NB2-05 — Résidu EU et chocs européens ⭐

**Priorité :** P1
**Type :** module + doc + artefact
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-04
**Complexité :** complexe

#### Objectif

Cataloguer et expliquer les événements européens non capturés par CBOT.

#### Contenu `src/mais/research/ema_residual_eu_v2.py`

```
Section 1 — Calcul résidu
résidu_t = ΔEMA_t - (β1_train × ΔCBOT_t + β2_train × Δbasis_t)
β estimés sur train, appliqués sur test (OOF strict)

Section 2 — Catalogue événements
- seuils : 2σ (149 events), 3σ (49 events)
- pour chaque event : date, type, magnitude, contexte
- replay dates majeures : 2012 sécheresse, 2018 canicule EU,
  2020 COVID, 2022 Ukraine, 2023 Mer Noire

Section 3 — Attribution par drivers
Pour chaque spike résidu, tester corrélation avec :
  a. Météo EU (eu_heat_stress_days, eu_precip_deficit)
  b. Ukraine exports (WASDE ukraine_exports)
  c. EUR/USD choc
  d. TTF gas spike
  e. MARS bulletins (proxy : date publication)
  f. FranceAgriMer/Eurostat production FR/RO/HU (anomalie)
  g. OI Euronext (si disponible)

Section 4 — Prédictibilité résidu
- peut-on prédire résidu_shock_up (>+2σ) ?
- targets : eu_residual_shock_up_h20, eu_residual_shock_down_h20
- features : météo EU (lag 5-20j), wasde_eu_stocks_zscore, ttf_zscore,
  eurusd_choc, ukraine_exports_change
- walk-forward OOF, IC95 bootstrap, BH

Section 5 — Leave-one-crisis-out
Retirer 2012, 2020, 2021, 2022 une par une.
Vérifier que le signal n'est pas 2022-driven.
```

#### Sorties
- `artefacts/ema_study/ema_residual_eu_v2.json`
- `artefacts/ema_study/eu_event_catalogue.json` (dates annotées)
- `docs/EMA_RESIDUAL_EU_V2.md`
- `tests/test_ema_residual_eu_v2.py` (≥ 8 tests)

---

## BLOC P2 — PRÉDICTION

---

### NB2-06 — Feature importance OOF + par année

**Priorité :** P2
**Type :** module + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-05
**Complexité :** moyen

#### Objectif

Feature importance rigoureuse. Pas d'importance in-sample seule. Vérification fedfunds_level_zscore.

#### Contenu `src/mais/research/ema_feature_importance_v2.py`

```
Section 1 — MI + Spearman + permutation OOF
- Mutual Information (non-paramétrique)
- Spearman rho
- Permutation importance OOF (train sur fold precedent, permute sur test)

Section 2 — Stability par année
- importance par crop year 2012 à 2025
- heatmap features × années
- identifier features stables vs 2022-driven

Section 3 — fedfunds_level_zscore audit
- scatter fedfunds vs EMA H20 par année
- importance en excluant 2021-2022
- conclusion : driver causal ou proxy régime ?

Section 4 — Ablation familles EU
- famille_météo_eu : {eu_gdd_anomaly, eu_heat_stress, eu_precip_deficit}
- famille_wasde_eu : {wasde_eu_production, wasde_eu_stocks, wasde_ukraine_exports}
- famille_basis : {basis_lag1, basis_zscore}
- famille_ttf : {ttf_zscore}
- famille_eurusd : {eurusd_lag1}
- famille_france_agrimer : {fr_mais_prod_anomaly}
→ delta AUC/DA vs baseline par famille

Section 5 — Weekly importance
Reproduire Section 1 sur données hebdomadaires.
```

#### Sorties
- `artefacts/ema_study/ema_feature_importance_v2.json`
- `docs/EMA_FEATURE_IMPORTANCE_V2.md`

---

### NB2-07 — Direction benchmarks EMA — nouvelles cibles ⭐

**Priorité :** P2
**Type :** module + doc + artefact
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-06
**Complexité :** complexe

#### Objectif

Benchmark complet sur les 5 nouvelles cibles prédictives intelligentes.

#### Nouvelles cibles

```python
# Cible 1 : basis reversion (meilleure piste actuelle)
basis_reversion_h20 = (basis_t+20 < basis_t) if basis_z_t > 1.5 else NaN

# Cible 2 : direction relative EMA vs CBOT
relative_return_h20 = return_EMA_h20 - return_CBOT_EUR_h20 > 0

# Cible 3 : résidu EU shock
eu_residual_shock_up_h20 = résidu_t+20 > +2σ
eu_residual_shock_down_h20 = résidu_t+20 < -2σ

# Cible 4 : volatilité EMA (régime)
ema_vol_high_h20 = vol_realized_t+20 > 25%

# Cible 5 : EMA direction absolue (secondaire)
y_up_h40_ema  # H40 uniquement (H20 trop bruité)
```

#### Protocole

```
- Walk-forward OOF (min 3 ans train)
- IC95 bootstrap 500 tirages
- BH correction (q < 0.05)
- DA par année (stability)
- Weekly DA (mandatory)
- Comparaison daily vs weekly
- Leave-one-crisis-out (2022)
```

#### Métriques par cible

```
DA, AUC, Brier, DA top20, IC95 DA, q BH,
DA par année (heatmap), DA weekly
```

**Règle : si DA hebdo < 0.53 → verdic WEEKLY_NO_GO**

#### Sorties
- `artefacts/ema_study/ema_direction_benchmarks_v2.json`
- `docs/EMA_DIRECTION_BENCHMARKS_V2.md`
- `tests/test_ema_direction_benchmarks_v2.py` (≥ 8 tests)

---

### NB2-08 — Event study EMA

**Priorité :** P2
**Type :** module + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-07
**Complexité :** moyen

#### Objectif

Étudier les grands mouvements EMA : avant/après quels événements ?

#### Contenu `src/mais/research/ema_event_study_v2.py`

```
Grands mouvements (>3%, >5%, >7%) :
- fenêtres pré-event : [-20, -10, -5, -1]
- fenêtres post-event : [+1, +5, +10, +20]
- contexte : WASDE date, MARS date, Ukraine events,
  EUR/USD choc, stress météo EU (eu_heat_stress_days > seuil)

Event windows :
- autour des publications WASDE
- autour des publications MARS mensuels (proxy date)
- Ukraine : dates clés 2022 (corridor, blocus, déblocage)
- fortes variations EUR/USD (z > 2)
- stress météo EU intense

Outputs :
- cumulative returns avant/après chaque type d'événement
- t-test / bootstrap sur retours event windows
- catalogue événements annotés avec type
```

#### Sorties
- `artefacts/ema_study/ema_event_study_v2.json`
- `docs/EMA_EVENT_STUDY_V2.md`

---

### NB2-09 — Volatilité EMA améliorée

**Priorité :** P2
**Type :** module + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-07
**Complexité :** moyen

#### Objectif

Améliorer le module volatilité avec régimes et événements (HAR-RV R²=0.013 était insuffisant).

#### Contenu `src/mais/research/ema_volatility_v2.py`

```
Section 1 — Vol rolling et régimes
- vol 20j, 60j, 90j rolling
- GARCH(1,1) persistence
- régimes vol : normal (<20%), elevated (20-30%), stress (>30%)

Section 2 — HAR-RV amélioré avec régimes
- HAR-RV de base (R²~0.013)
- HAR-RV + régime (dummy crises)
- HAR-RV + basis_zscore (plus de vol quand basis dévié ?)
- HAR-RV + résidu EU (chocs EU augmentent vol ?)

Section 3 — Vol avant/après événements
- vol avant WASDE, MARS, Ukraine events
- vol vs basis z-score
- vol vs résidu EU

Section 4 — Prédire régime vol
- target : vol_regime_high_h20 (vol > 25% dans 20j ?)
- OOF walk-forward
- IC95 bootstrap
```

#### Sorties
- `artefacts/ema_study/ema_volatility_v2.json`
- `docs/EMA_VOLATILITY_V2.md`

---

## BLOC P3 — CQR SUR RETURNS

---

### NB2-10 — CQR sur returns (pas sur prix absolus)

**Priorité :** P3
**Type :** module + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-09
**Complexité :** moyen

#### Objectif

Reconstruire CQR sur les rendements plutôt que le prix absolu.

#### Contenu `src/mais/research/ema_cqr_v2.py`

```
Target : return_EMA_h20 (log-return, pas prix absolu)

Protocole CQR :
- split : calibration 20%, test 80% (OOF strict)
- quantiles : q10, q50, q90
- couverture empirique par fold
- Winkler loss
- split : années normales vs crises (calibration séparée)

Améliorations vs v1 :
- calibration par régime (normal vs crise)
- adaptive intervals (vol adaptative)
- couverture par année (heatmap)
- verdict par année : PASS / FAIL

Verdict global :
si couverture empirique < 88% → CQR_NO_GO
```

#### Sorties
- `artefacts/ema_study/ema_cqr_v2.json`
- `docs/EMA_CQR_V2.md`

---

## BLOC P4 — RAPPORT FINAL

---

### NB2-11 — Rapport final Euronext propre

**Priorité :** P4
**Type :** doc + artefact
**Statut :** NEEDS_REVIEW
**Dépendances :** NB2-10
**Complexité :** moyen

#### Objectif

Synthèse honnête et professionnelle de l'étude Euronext Phase 2.

#### Structure `docs/EMA_FINAL_REPORT_V2.md`

```
1. Données EMA (source, qualité, limites)
2. Construction série continue (architecture raw/adjusted)
3. Relation EMA/CBOT (transmission, cointégration, Granger LIMITÉ)
4. Basis EMA/CBOT (RÉSULTAT PRINCIPAL)
5. Résidu EU (catalogue événements)
6. Prédiction (cibles validées / non validées, avec verdicts clairs)
7. Limites (source exploratoire, NO_RELIABLE_PERIOD_ML)
8. Suite recommandée (données officielles, vrais bulletins MARS)

Labels sur chaque section :
SOLIDE / EXPÉRIMENTAL / NON VALIDÉ / NO_GO
```

#### Table `État d'implémentation`

Maintenir une table ✅/❌/⚠️ :
- Cointégration EMA/CBOT : ✅ CONFIRMÉ
- Granger EMA→CBOT : ❌ REJETÉ OOF
- Basis mean reversion : ⚠️ EXPÉRIMENTAL (OOF Phase 2)
- Direction EMA absolue H20 : ❌ NO_GO
- Direction EMA relative : ⚠️ À TESTER Phase 2
- Résidu EU shock : ⚠️ À TESTER Phase 2
- CQR prix EMA : ❌ NO_GO
- Source données EMA : ⚠️ EXPLORATOIRE

#### Sorties
- `artefacts/ema_study/ema_final_report_v2.json`
- `docs/EMA_FINAL_REPORT_V2.md`

---

## Dépendances globales

```
FIX-P0-01
   └── NB2-00
        └── NB2-01, NB2-02
              └── NB2-03 (basis ⭐)
                    └── NB2-04
                          └── NB2-05 (résidu EU ⭐)
                                └── NB2-06 (importance)
                                      └── NB2-07 (benchmarks ⭐)
                                            └── NB2-08, NB2-09
                                                  └── NB2-10 (CQR)
                                                        └── NB2-11 (rapport)
```

---

## PHASE DEBUG — cohérence targets et benchmarks

### FIX-EMA-01 — Target NaN integrity

**Priorité :** P0
**Type :** correction + audit
**Statut :** NEEDS_REVIEW
**Dépendances :** aucune
**Complexité :** moyen

#### Objectif

Corriger les cibles EMA construites via comparaisons futures pour éviter que `NaN > 0` devienne artificiellement `False` puis `0`.

#### Fichiers à modifier
- `src/mais/research/ema_utils.py`
- `src/mais/research/ema_direction_benchmark.py`
- `src/mais/research/ema_direction_benchmarks_v2.py`
- `src/mais/research/ema_residual_eu_v2.py`
- `src/mais/research/ema_volatility_v2.py`
- `src/mais/research/ema_target_integrity.py`
- `tests/test_ema_utils.py`
- `tests/test_ema_direction_benchmarks_v2.py`
- `tests/test_ema_residual_eu_v2.py`
- `tests/test_ema_volatility_v2.py`
- `tests/test_ema_target_integrity.py`
- `docs/EMA_TARGET_INTEGRITY.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Les dernières `H` observations des cibles futures restent `NaN`.
- Les cibles `relative_return`, `basis_reversion`, `vol_high`, `residual_shock` ne convertissent plus les futurs manquants en 0.
- Un audit cible produit un verdict clair.
- Les benchmarks peuvent ignorer ces `NaN` via `dropna()`.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_utils.py src/mais/research/ema_direction_benchmark.py src/mais/research/ema_direction_benchmarks_v2.py src/mais/research/ema_residual_eu_v2.py src/mais/research/ema_volatility_v2.py src/mais/research/ema_target_integrity.py tests/test_ema_utils.py tests/test_ema_direction_benchmarks_v2.py tests/test_ema_residual_eu_v2.py tests/test_ema_volatility_v2.py tests/test_ema_target_integrity.py
venv/bin/python -m pytest tests/test_ema_utils.py tests/test_ema_direction_benchmarks_v2.py tests/test_ema_residual_eu_v2.py tests/test_ema_volatility_v2.py tests/test_ema_target_integrity.py
```

#### Résultat ticket (2026-05-24)

- Helpers centralisés ajoutés : `binary_target_from_future_return()` et `binary_target_from_condition()`.
- Cibles EMA corrigées pour préserver les futurs manquants en `NaN` au lieu de les convertir en `0`.
- Benchmark directionnel v2 corrigé : suppression de la réinjection de `ema_targets.parquet`, qui pouvait restaurer d'anciennes valeurs de target en fin de série.
- Audit cible créé : `ema_target_integrity`, avec document `docs/EMA_TARGET_INTEGRITY.md`.
- Vérifications : `ruff check` ciblé PASS ; pytest ciblé `42 passed, 48 warnings`.
- Warnings résiduels : classes rares/déséquilibrées dans les tests résidu EU et volatilité, cohérents avec le diagnostic scientifique.

### FIX-EMA-02 — Sélection robuste meilleur signal

**Priorité :** P0
**Type :** correction benchmark + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** FIX-EMA-01
**Complexité :** moyen

#### Objectif

Ne plus sélectionner le meilleur signal EMA par DA brute seule, car les cibles déséquilibrées peuvent gonfler la DA.

#### Fichiers à modifier
- `src/mais/research/ema_direction_benchmarks_v2.py`
- `tests/test_ema_direction_benchmarks_v2.py`
- `docs/EMA_DIRECTION_BENCHMARKS_V2.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Les métriques incluent baseline classe majoritaire, lift vs baseline, MCC, precision/recall, base rate, confusion matrix.
- Le champ `key_findings` distingue `best_by_da` et `robust_best_signal`.
- La sélection robuste suit l'ordre : AUC, balanced accuracy, top20 DA, weekly performance, stabilité annuelle, DA brute.
- La doc indique explicitement que `ema_vol_high_h20` ne doit pas être retenu uniquement sur DA si AUC/balanced accuracy sont faibles.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_direction_benchmarks_v2.py tests/test_ema_direction_benchmarks_v2.py
venv/bin/python -m pytest tests/test_ema_direction_benchmarks_v2.py
```

#### Résultat ticket (2026-05-24)

- Sélection robuste ajoutée : AUC → balanced accuracy → top20 DA → weekly AUC → weekly balanced accuracy → stabilité annuelle → DA.
- `best_by_da` séparé de `robust_best_signal`.
- Métriques ajoutées : `majority_baseline_da`, `lift_vs_majority`, `mcc`, base rate, confusion matrix, precision/recall déjà présents.
- Résultat clé après correction target : `robust_best_signal = relative_ema_outperformance_h40`, AUC daily `0.708`, balanced accuracy `0.642`, weekly AUC `0.728`.
- La meilleure cible par DA brute est `eu_residual_shock_up_h20` (`0.823`) mais elle n'est pas retenue comme meilleur signal robuste.
- Vérifications : ruff ciblé PASS ; pytest ciblé `10 passed, 306 warnings`.
- Warnings résiduels : classes rares/déséquilibrées, exactement le point diagnostiqué.

### FIX-EMA-03 — Raw vs adjusted vs no-roll après fix target

**Priorité :** P0
**Type :** benchmark + audit roll
**Statut :** NEEDS_REVIEW
**Dépendances :** FIX-EMA-01
**Complexité :** moyen

#### Objectif

Refaire le benchmark raw / adjusted / no-roll après correction de l'intégrité des targets, et vérifier que les tails futures des targets roll-aware ne contiennent pas de faux 0.

#### Fichiers à modifier
- `src/mais/research/ema_roll_target_benchmark.py`
- `tests/test_ema_roll_target_benchmark.py`
- `docs/EMA_ROLL_TARGET_AFTER_FIX.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Les résultats couvrent H20/H40/H60 × raw/adjusted/no-roll.
- Le payload contient un audit tail-NaN des targets roll-aware.
- Le verdict indique si les rolls expliquent ou non l'échec EMA direct.
- La doc rappelle que H60 no-roll peut être structurellement indisponible.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_roll_target_benchmark.py tests/test_ema_roll_target_benchmark.py
venv/bin/python -m pytest tests/test_ema_roll_target_benchmark.py
```

#### Résultat ticket (2026-05-24)

- Benchmark raw / adjusted / no-roll enrichi avec audit tail-NaN des targets H20/H40/H60.
- Audit tail-NaN réel : PASS sur toutes les targets roll-aware.
- Verdict réel : `ROLL_TARGET_NOT_EXPLAINED`.
- Résultats primaires `cbot_ema_combined` : H20 raw DA `46.7%`, adjusted `44.7%`, no-roll `44.6%`; H40 raw `40.9%`, adjusted `40.4%`, no-roll `32.0%`; H60 raw `45.5%`, adjusted `45.3%`, no-roll skipped.
- Conclusion : les rolls restent un risque méthodologique majeur, mais ils n'expliquent pas à eux seuls l'échec de la direction EMA brute.
- Vérifications : ruff ciblé PASS ; pytest ciblé `4 passed`.

### FIX-EMA-04 — Benchmark hebdomadaire généralisé

**Priorité :** P1
**Type :** benchmark + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** FIX-EMA-01
**Complexité :** moyen

#### Objectif

Refaire les benchmarks EMA en fréquence hebdomadaire vendredi→vendredi sur H4, H8 et H12 semaines.

#### Fichiers à modifier
- `src/mais/research/ema_weekly_benchmark.py`
- `tests/test_ema_weekly_benchmark.py`
- `docs/EMA_WEEKLY_BENCHMARK.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Tester EMA direct, relative EMA/CBOT, basis reversion et volatilité en weekly.
- Produire n, base rate, DA ou hit rate, IC95 bootstrap, et verdict `WEEKLY_GO` / `WEEKLY_NO_GO`.
- Documenter clairement que weekly réduit le bruit mais ne transforme pas EMA direct en signal validé si le seuil 0.53 n'est pas atteint.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_weekly_benchmark.py tests/test_ema_weekly_benchmark.py
venv/bin/python -m pytest tests/test_ema_weekly_benchmark.py
```

#### Résultat ticket (2026-05-24)

- Benchmark weekly généralisé H4/H8/H12 ajouté sur EMA direct momentum, relative EMA/CBOT via basis z-score, basis reversion et volatilité persistante.
- Meilleur signal weekly : `basis_reversion` H12, hit rate `76.4%` sur `144` événements.
- Signal relatif EMA/CBOT weekly : H4 `57.7%`, H8 `60.7%`, H12 `62.0%`, tous `WEEKLY_GO` selon règle descriptive.
- EMA direct momentum : H4 `54.6%` `WEEKLY_GO` descriptif, H8 `53.3%` mais CI basse insuffisante, H12 `49.0%`.
- Conclusion : le weekly soutient surtout le basis et le relatif EMA/CBOT ; EMA direct reste non robuste hors H4 descriptif.
- Vérifications : ruff ciblé PASS ; pytest ciblé `10 passed`.

### FIX-EMA-05 — Split qualité données EMA

**Priorité :** P1
**Type :** benchmark + audit data
**Statut :** NEEDS_REVIEW
**Dépendances :** FIX-EMA-01
**Complexité :** moyen

#### Objectif

Comparer les signaux EMA sur all data, proxy dominant, official recent, haute disponibilité et faible qualité exclue.

#### Fichiers à modifier
- `src/mais/research/ema_data_quality_split.py`
- `tests/test_ema_data_quality_split.py`
- `docs/EMA_DATA_QUALITY_SPLIT.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Les splits contiennent `n_rows`, période, official/proxy shares.
- Les benchmarks couvrent au moins `relative_ema_outperformance_h40`, `ema_direction_absolute_h40`, `basis_reversion_h20`.
- Les splits trop courts retournent un statut explicite, pas une métrique forcée.
- La doc conclut si le signal robuste dépend principalement du proxy.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_data_quality_split.py tests/test_ema_data_quality_split.py
venv/bin/python -m pytest tests/test_ema_data_quality_split.py
```

#### Résultat ticket (2026-05-24)

- Module `ema_data_quality_split` créé avec splits `all_data`, `proxy_dominant`, `official_recent`, `high_availability`, `low_quality_excluded`.
- Signal suivi : `relative_ema_outperformance_h40`.
- Résultat : all data AUC `0.708`, proxy dominant AUC `0.708`, high availability AUC `0.706`.
- `official_recent` ne contient que `21` lignes alignées utiles dans ce protocole et retourne `no_valid_folds`.
- Conclusion : le signal robuste est observé sur historique proxy/high-availability ; il n'est pas invalidé, mais il n'est pas confirmable OOF sur la courte période officielle récente.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed, 15 warnings`.

### FIX-EMA-06 — Baselines intelligentes EMA

**Priorité :** P1
**Type :** benchmark
**Statut :** NEEDS_REVIEW
**Dépendances :** FIX-EMA-02
**Complexité :** moyen

#### Objectif

Comparer les signaux EMA aux baselines simples : classe majoritaire, momentum EMA, momentum CBOT, règle basis z-score, saisonnalité mensuelle, random.

#### Fichiers à modifier
- `src/mais/research/ema_smart_baselines.py`
- `tests/test_ema_smart_baselines.py`
- `docs/EMA_SMART_BASELINES.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Tester `relative_ema_outperformance_h40` et `ema_direction_absolute_h40`.
- Comparer les baselines au modèle robuste issu de `ema_direction_benchmarks_v2`.
- Indiquer clairement si le meilleur modèle bat la meilleure baseline.
- Inclure DA, balanced accuracy, lift vs majority et n.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_smart_baselines.py tests/test_ema_smart_baselines.py
venv/bin/python -m pytest tests/test_ema_smart_baselines.py
```

#### Résultat ticket (2026-05-24)

- Baselines ajoutées : walk-forward majority, EMA momentum 20j, CBOT momentum 20j, basis z-rule, seasonal month rule, random 50/50.
- Sur `relative_ema_outperformance_h40`, le modèle robuste balanced accuracy `64.2%`, AUC `0.708`.
- Meilleure baseline : `basis_z_rule`, balanced accuracy `64.4%`, DA `64.2%`.
- Conclusion importante : le modèle ne bat pas la règle simple basis z-score en balanced accuracy ; le signal relatif est réel, mais il est largement porté par la structure du basis.
- Sur `ema_direction_absolute_h40`, le modèle reste faible (balanced accuracy `51.9%`) et une baseline CBOT momentum fait mieux (`53.4%`).
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed, 170 warnings`.

### FIX-EMA-07 — Indicateur premium EMA/CBOT

**Priorité :** P2
**Type :** indicateur étude + doc
**Statut :** NEEDS_REVIEW
**Dépendances :** FIX-EMA-06
**Complexité :** moyen

#### Objectif

Construire un premier indicateur professionnel non-trading : prime européenne EMA/CBOT, zone de basis, probabilité historique de reversion, lecture relative EMA vs CBOT.

#### Fichiers à modifier
- `src/mais/research/ema_premium_indicator.py`
- `tests/test_ema_premium_indicator.py`
- `docs/EMA_PREMIUM_INDICATOR.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Sortir le snapshot le plus récent : basis, z-score, zone normale/extrême, signal relatif.
- Calculer les hit rates historiques de reversion H20/H40/H60 par zone.
- Mentionner explicitement que l'indicateur prédit la composante relative/basis, pas EMA up/down.
- Inclure un score de confiance lié au nombre d'événements et à la source proxy.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_premium_indicator.py tests/test_ema_premium_indicator.py
venv/bin/python -m pytest tests/test_ema_premium_indicator.py
```

#### Résultat ticket (2026-05-24)

- Indicateur `ema_premium_indicator` créé.
- Snapshot le plus récent exploitable : `2025-07-25`, EMA `207.00` EUR/t, CBOT converti `134.33` EUR/t, basis `72.67` EUR/t, z-score `1.70`.
- Zone : `high_premium`; signal relatif : `ema_expected_to_underperform_cbot`; confiance `medium`.
- Meilleure statistique historique associée : high premium H60, `385` événements, hit rate de reversion `76.6%`.
- La doc précise que l'indicateur porte sur le basis / relatif EMA-CBOT, pas sur EMA up/down.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

### FIX-EMA-08 — Backtests théoriques relatifs/basis

**Priorité :** P2
**Type :** backtest exploratoire
**Statut :** NEEDS_REVIEW
**Dépendances :** FIX-EMA-07
**Complexité :** moyen

#### Objectif

Tester théoriquement trois règles simples : EMA direct momentum, relative EMA/CBOT via basis z-score, basis mean reversion extrême. Ce n'est pas un backtest de production.

#### Fichiers à modifier
- `src/mais/research/ema_theoretical_backtests.py`
- `tests/test_ema_theoretical_backtests.py`
- `docs/EMA_THEORETICAL_BACKTESTS.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Backtests H40/H60 non-overlapping approximatifs.
- Inclure coûts/frictions simples en EUR/t.
- Rapporter n trades, hit rate, PnL total/moyen, worst year, Sharpe naïf, max drawdown.
- Mentionner explicitement : exploratoire, proxy, pas de trading réel.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_theoretical_backtests.py tests/test_ema_theoretical_backtests.py
venv/bin/python -m pytest tests/test_ema_theoretical_backtests.py
```

#### Résultat ticket (2026-05-24)

- Backtests théoriques non-overlapping H40/H60 créés avec coût simplifié `1.0` EUR/t par leg.
- Statut global : `THEORETICAL_ONLY_NOT_PRODUCTION`, verdict production `NO_PRODUCTION_BACKTEST`.
- Meilleur résultat exploratoire : `basis_extreme_mean_reversion` H60, `7` trades, hit rate `71.4%`, PnL moyen `10.20` EUR/t.
- `relative_basis_z_rule` H40 : `74` trades, hit rate `56.8%`, PnL moyen `3.24` EUR/t ; H60 : `49` trades, hit rate `65.3%`, PnL moyen `1.42` EUR/t.
- EMA direct momentum reste faible : H40 hit rate `54.1%`, H60 `51.0%`.
- Conclusion : le backtest soutient l'axe relatif/basis, mais l'échantillon extrême est trop petit pour un claim trading.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

## SUITE RELATIVE EMA/CBOT — audit 2026-05-25

### REL-EMA-01 — Corriger rapport final relatif EMA/CBOT

**Priorité :** P0
**Type :** correction rapport + artefact
**Statut :** DONE
**Dépendances :** FIX-EMA-02, FIX-EMA-06
**Complexité :** simple

#### Objectif

Corriger `EMA_FINAL_REPORT_V2` pour acter que le meilleur signal EMA robuste est `relative_ema_outperformance_h40`, et non une cible gonflée par déséquilibre comme `ema_vol_high_h20`.

#### Fichiers à modifier
- `src/mais/research/ema_final_report_v2.py`
- `tests/test_ema_final_report_v2.py`
- `docs/EMA_FINAL_REPORT_V2.md`
- `artefacts/ema_study/ema_final_report_v2.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Le rapport met `relative_ema_outperformance_h40` comme signal EMA robuste principal.
- Le rapport indique que `ema_vol_high_h20` est un faux bon signal si AUC/balanced accuracy/MCC sont faibles.
- EMA direction absolue reste `NO_GO`.
- Basis = structure intéressante, mais modèle `basis_reversion_h20` faible en OOF.
- Les prochaines étapes pivotent vers l'étude relative EMA/CBOT.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_final_report_v2.py tests/test_ema_final_report_v2.py
venv/bin/python -m pytest tests/test_ema_final_report_v2.py
```

#### Résultat ticket (2026-05-25)

- `EMA_FINAL_REPORT_V2` corrigé : le meilleur signal EMA robuste est désormais `relative_ema_outperformance_h40`.
- Statut relatif H40 : DA `64.0%`, AUC `0.708`, balanced accuracy `64.2%`, top20 `77.1%`, weekly AUC `0.728`.
- `ema_vol_high_h20` est explicitement rejeté comme meilleur signal : DA brute `65.8%`, mais AUC `0.532`, balanced accuracy `51.3%`, MCC `0.021`.
- EMA direction absolue H40 reste `NO_GO` : DA `51.9%`, AUC `0.529`.
- Basis mean reversion est reformulé : structure descriptive intéressante, mais modèle `basis_reversion_h20` faible en OOF.
- Next steps du rapport pivotés vers étude relative EMA/CBOT, analyse d'erreurs, abstention filters et backtest relatif réaliste.
- Vérifications : ruff ciblé PASS ; pytest ciblé `6 passed`.

### REL-EMA-02 — Étude relative EMA/CBOT reproductible

**Priorité :** P0
**Type :** module + doc
**Statut :** DONE
**Dépendances :** REL-EMA-01
**Complexité :** moyen

#### Objectif

Produire une étude reproductible hors notebook sur `relative_ema_outperformance` multi-horizon H10/H20/H40/H60/H90.

#### Fichiers à modifier
- `src/mais/research/ema_relative_study.py`
- `tests/test_ema_relative_study.py`
- `docs/EMA_RELATIVE_STUDY.md`
- `artefacts/ema_study/ema_relative_study.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Note notebooks

Le notebook demandé `notebooks/corn_study/euronext/06_relative_ema_cbot.ipynb` reste à créer manuellement ou par un ticket dédié si la règle agents autorise explicitement `notebooks/`.

### REL-EMA-03 — Analyse des erreurs relative H40

**Priorité :** P1
**Type :** module + doc + artefact
**Statut :** DONE
**Dépendances :** REL-EMA-02
**Complexité :** moyen

#### Objectif

Cataloguer les meilleures prédictions correctes, les pires erreurs et les top20 signaux échoués sur `relative_ema_outperformance_h40`.

#### Fichiers à modifier
- `src/mais/research/ema_relative_error_analysis.py`
- `tests/test_ema_relative_error_analysis.py`
- `docs/EMA_RELATIVE_ERROR_ANALYSIS.md`
- `artefacts/ema_study/ema_relative_error_analysis.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Produire les top corrects, worst errors et failed top20.
- Ajouter une classification heuristique : basis_extreme, roll_risk_proxy, crisis_period, volatility_context, unknown.
- Résumer les erreurs par type pour préparer les filtres d'abstention.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_relative_error_analysis.py tests/test_ema_relative_error_analysis.py
venv/bin/python -m pytest tests/test_ema_relative_error_analysis.py
```

#### Résultat REL-EMA-02 (2026-05-25)

- Étude relative EMA/CBOT multi-horizon créée sur H10/H20/H40/H60/H90.
- Verdict : `RELATIVE_EMA_CBOT_SIGNAL_CONFIRMED`.
- H40 confirme le benchmark : DA `64.0%`, AUC `0.708`, top20 DA `77.1%`, weekly AUC `0.728`.
- H90 ressort comme meilleur horizon exploratoire : DA `69.0%`, AUC `0.770`, balanced accuracy `69.2%`, top20 DA `88.7%`.
- Conclusion : le signal relatif augmente avec l'horizon dans ce protocole ; H40 reste le cœur robuste déjà validé, H90 devient un candidat prioritaire à stress tester.
- Vérifications : ruff ciblé PASS ; pytest ciblé `6 passed`.

### REL-EMA-04 — Filtres d'abstention relative H40

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** REL-EMA-03
**Complexité :** moyen

#### Objectif

Tester des filtres d'abstention sur `relative_ema_outperformance_h40` : top20 confidence, hors roll risk proxy, hors crise, basis extrême contrôlé, combinaison stricte.

#### Fichiers à modifier
- `src/mais/research/ema_abstention_filters.py`
- `tests/test_ema_abstention_filters.py`
- `docs/EMA_ABSTENTION_FILTERS.md`
- `artefacts/ema_study/ema_abstention_filters.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Rapporter coverage, n, DA, AUC, balanced accuracy et top20 DA par filtre.
- Comparer chaque filtre à la baseline all signals.
- Identifier le filtre le plus utile sans sur-optimisation.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_abstention_filters.py tests/test_ema_abstention_filters.py
venv/bin/python -m pytest tests/test_ema_abstention_filters.py
```

#### Résultat REL-EMA-03 (2026-05-25)

- Analyse des erreurs H40 créée avec top corrects, worst errors et failed top20.
- Tag principal des pires erreurs : `roll_risk_proxy`.
- Tag principal des failed top20 : `roll_risk_proxy`.
- Les failed top20 contiennent aussi beaucoup de `basis_extreme` et `crisis_period`.
- Conclusion : les premiers filtres d'abstention doivent tester roll-risk proxy, crise, et confiance/top20.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Résultat REL-EMA-04 (2026-05-25)

- Filtres d'abstention créés pour `relative_ema_outperformance_h40`.
- Baseline all signals : DA `64.0%`, balanced accuracy `64.2%`, AUC `0.708`.
- Meilleur filtre avec couverture suffisante : `basis_extreme_only`, coverage `23.1%`, DA `76.8%`, balanced accuracy `76.1%`, AUC `0.789`.
- `top20_confidence` confirme aussi un signal sélectif : coverage `20.0%`, DA `77.2%`, AUC `0.796`.
- Lecture : l'abstention améliore fortement la sélection, mais doit être testée en backtest relatif avant tout claim économique.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

### REL-EMA-05 — Backtest relatif EMA/CBOT réaliste

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** REL-EMA-04
**Complexité :** moyen

#### Objectif

Backtester de façon réaliste et prudente le signal relatif EMA/CBOT H40 en long/short spread, avec filtres d'abstention, coûts/frictions, non-overlap approximatif et aucun claim trading production.

#### Fichiers à modifier
- `src/mais/research/ema_relative_backtest.py`
- `tests/test_ema_relative_backtest.py`
- `docs/EMA_RELATIVE_BACKTEST.md`
- `artefacts/ema_study/ema_relative_backtest.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Backtest H40 non-overlapping approximatif.
- Stratégies : all signals, top20 confidence, basis extreme, top20+basis extreme, règle basis z-score.
- Inclure coûts par leg, PnL net EUR/t, hit rate, profit factor, drawdown, turnover, PnL par année.
- Statut explicite : recherche seulement, source proxy, pas de trading production.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_relative_backtest.py tests/test_ema_relative_backtest.py
venv/bin/python -m pytest tests/test_ema_relative_backtest.py
```

#### Résultat REL-EMA-05 (2026-05-25)

- Backtest relatif EMA/CBOT H40 créé en long/short spread, non-overlap approximatif, coût `1.0` EUR/t par leg (`2.0` EUR/t par trade spread).
- Statut global : `RESEARCH_ONLY_NOT_TRADING`, verdict production `NO_PRODUCTION_BACKTEST`.
- Meilleure stratégie exploratoire : `model_top20_confidence`, `25` trades, hit rate `76.0%`, PnL moyen net `11.77` EUR/t, PnL total net `294.13` EUR/t, profit factor `6.90`.
- Baseline modèle tous signaux : `59` trades, hit rate `59.3%`, PnL moyen net `3.03` EUR/t.
- Règle simple `basis_zscore_rule` : `59` trades, hit rate `55.9%`, PnL moyen net `0.52` EUR/t.
- Filtre `model_no_roll_risk` négatif dans ce protocole : PnL moyen net `-0.96` EUR/t.
- Conclusion : le signal relatif sélectif survit aux coûts simplifiés, mais la source proxy et l'absence de bid-ask/liquidité interdisent tout claim trading production.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review REL-EMA-02 à REL-EMA-05 (2026-05-25)

- Review demandée par l'utilisateur : tickets validés `DONE`.
- Vérifications groupées review : ruff ciblé PASS ; pytest ciblé `21 passed`.
- Réserves maintenues : source EMA exploratoire/proxy, pas de claim trading production, notebook non modifié car dossier interdit par règles agents.

## SUITE PREMIUM EMA/CBOT — audit 2026-05-25

### EMA-NEXT-01 — Rapport final V3 pivot prime européenne

**Priorité :** P0
**Type :** rapport + artefact
**Statut :** DONE
**Dépendances :** REL-EMA-05
**Complexité :** simple

#### Objectif

Créer un rapport final V3 qui fige le pivot scientifique : EMA brut `NO_GO`, EMA relatif CBOT `GO_RESEARCH`, basis comme moteur central, backtests uniquement recherche.

#### Fichiers à modifier
- `src/mais/research/ema_final_report_v3.py`
- `tests/test_ema_final_report_v3.py`
- `docs/EMA_FINAL_REPORT_V3.md`
- `artefacts/ema_study/ema_final_report_v3.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- Le rapport place `relative_ema_outperformance_h40` comme résultat principal prudent.
- H90 est marqué candidat exploratoire à stress tester, pas résultat final production.
- EMA direct, volatilité, stockage, CQR prix absolu restent `NO_GO`.
- Backtest relatif marqué `RESEARCH_ONLY_NOT_TRADING`.
- Source EMA proxy et `NO_RELIABLE_PERIOD_ML` visibles.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_final_report_v3.py tests/test_ema_final_report_v3.py
venv/bin/python -m pytest tests/test_ema_final_report_v3.py
```

#### Résultat EMA-NEXT-01 (2026-05-25)

- Rapport final V3 créé : `docs/EMA_FINAL_REPORT_V3.md` + `artefacts/ema_study/ema_final_report_v3.json`.
- Pivot figé : ancienne question `EMA up/down` rejetée comme cible principale ; nouvelle question `prime relative EMA/CBOT` validée en recherche exploratoire.
- Résultat principal : `relative_ema_outperformance_h40`, DA daily `64.0%`, AUC `0.708`, balanced accuracy `64.2%`, top20 DA `77.1%`, weekly AUC `0.728`.
- H90 marqué candidat prometteur mais non final : DA `69.0%`, AUC `0.770`, top20 DA `88.7%`, stress tests requis.
- Backtest top20 conservé en statut `RESEARCH_ONLY_NOT_TRADING`, production `NO_PRODUCTION_BACKTEST`.
- NO_GO maintenus : EMA direction absolue, volatilité EMA, stockage EMA, CQR prix absolu EMA.
- Vérifications : ruff ciblé PASS ; pytest ciblé `6 passed`.

#### Review EMA-NEXT-01 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserves conservées dans le rapport : source EMA proxy, `NO_RELIABLE_PERIOD_ML`, backtest non-production.

### EMA-NEXT-02 — Notebook narratif relatif EMA/CBOT

**Priorité :** P0
**Type :** notebook
**Statut :** IN_PROGRESS
**Dépendances :** EMA-NEXT-01
**Complexité :** simple

#### Blocage

Le dossier `notebooks/` est interdit en lecture/modification par les règles agents. À exécuter uniquement si la règle est explicitement levée.

### EMA-NEXT-03 — Feature importance relative H40/H90

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** EMA-NEXT-01
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_relative_feature_importance.py`
- `tests/test_ema_relative_feature_importance.py`
- `docs/EMA_RELATIVE_FEATURE_IMPORTANCE.md`
- `artefacts/ema_study/ema_relative_feature_importance.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Critères de réussite
- Calculer importance permutation OOF sur H40 et H90.
- Calculer ablation par familles simples : basis, EMA technique, CBOT technique, macro/energie.
- Rapporter AUC, balanced accuracy, top features et conclusion économique.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_relative_feature_importance.py tests/test_ema_relative_feature_importance.py
venv/bin/python -m pytest tests/test_ema_relative_feature_importance.py
```

#### Résultat EMA-NEXT-03 (2026-05-25)

- Importance relative H40/H90 créée : `docs/EMA_RELATIVE_FEATURE_IMPORTANCE.md` + artefact JSON.
- H40 : top feature `ema_cbot_basis`; permutation du basis fait tomber l'AUC de `0.708` à `0.430` (delta `+0.278`).
- H90 : top feature `ema_cbot_basis`; permutation du basis fait tomber l'AUC de `0.770` à `0.452` (delta `+0.317`).
- Ablation famille `basis` : H40 AUC `0.514` (delta `+0.194`), H90 AUC `0.513` (delta `+0.256`).
- Conclusion : le signal relatif EMA/CBOT est massivement porté par le basis ; l'indicateur premium doit assumer ce moteur économique.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-NEXT-03 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : importance OOF exploratoire sur données EMA proxy.

### EMA-NEXT-04 — Étude saisonnière relative EMA/CBOT

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** EMA-NEXT-03
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_relative_seasonality.py`
- `tests/test_ema_relative_seasonality.py`
- `docs/EMA_RELATIVE_SEASONALITY.md`
- `artefacts/ema_study/ema_relative_seasonality.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Critères de réussite
- Étudier H40 et H90 par saison agricole européenne.
- Rapporter n, base rate, DA, AUC, balanced accuracy, top20 DA et basis moyen.
- Identifier la meilleure saison et les saisons fragiles.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_relative_seasonality.py tests/test_ema_relative_seasonality.py
venv/bin/python -m pytest tests/test_ema_relative_seasonality.py
```

#### Résultat EMA-NEXT-04 (2026-05-25)

- Étude saisonnière relative H40/H90 créée : `docs/EMA_RELATIVE_SEASONALITY.md` + artefact JSON.
- H40 meilleure saison : `sep_nov_eu_harvest`, AUC `0.868`, DA `80.8%`; `jul_aug_yield_stress` est aussi fort, AUC `0.865`, DA `81.2%`.
- H40 saison fragile : `apr_jun_sowing_weather`, AUC `0.503`, DA `41.7%`.
- H90 meilleure saison : `sep_nov_eu_harvest`, AUC `0.916`, DA `84.2%`.
- Conclusion : la prime relative est particulièrement lisible autour de la récolte européenne ; la saison doit devenir un filtre de confiance.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-NEXT-04 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : saisonnalité exploratoire sur données EMA proxy.

### EMA-PREM-01 — ML vs basis z-score vs signal combiné

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** EMA-NEXT-04
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_premium_signal_compare.py`
- `tests/test_ema_premium_signal_compare.py`
- `docs/EMA_PREMIUM_SIGNAL_COMPARE.md`
- `artefacts/ema_study/ema_premium_signal_compare.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Critères de réussite
- Comparer modèle ML, règle basis z-score et combinaison sur H40/H90.
- Rapporter DA, AUC, balanced accuracy, top20 DA et couverture si filtre.
- Conclure si le ML bat la règle simple ou si le signal combiné est préférable.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_premium_signal_compare.py tests/test_ema_premium_signal_compare.py
venv/bin/python -m pytest tests/test_ema_premium_signal_compare.py
```

#### Résultat EMA-PREM-01 (2026-05-25)

- Comparaison ML / basis z-score / combinaison créée : `docs/EMA_PREMIUM_SIGNAL_COMPARE.md` + artefact JSON.
- H40 : meilleur protocole `ml_with_basis_extreme_filter`, coverage `23.1%`, AUC `0.789`, balanced accuracy `76.1%`, top20 DA `87.4%`.
- H40 tous signaux : ML AUC `0.708`, balanced accuracy `64.2%`; basis z-score AUC `0.676`, balanced accuracy `64.4%`; combinaison pleine AUC `0.704`, balanced accuracy `64.7%`.
- H90 : meilleur protocole `combined_top40_confidence`, coverage `40.0%`, AUC `0.884`, balanced accuracy `84.4%`, top20 DA `93.1%`.
- Conclusion : utiliser un signal premium hybride ML + basis + abstention, pas un ML seul.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-PREM-01 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : résultats exploratoires sur source EMA proxy.

### EMA-PREM-02 — European Premium Indicator V2

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** EMA-PREM-01
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_premium_indicator_v2.py`
- `tests/test_ema_premium_indicator_v2.py`
- `docs/EMA_PREMIUM_INDICATOR_V2.md`
- `artefacts/ema_study/ema_premium_indicator_v2.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Critères de réussite
- Produire un snapshot récent : basis, z-score, probas H40/H90, score premium.
- Sortir `EU_PREMIUM_BULLISH`, `EU_PREMIUM_BEARISH`, `NEUTRAL` ou `UNCERTAIN`.
- Mentionner explicitement : signal relatif EMA/CBOT, pas EMA direction absolue.
- Inclure historique compact et confidence tiers.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_premium_indicator_v2.py tests/test_ema_premium_indicator_v2.py
venv/bin/python -m pytest tests/test_ema_premium_indicator_v2.py
```

#### Résultat EMA-PREM-02 (2026-05-25)

- European Premium Indicator V2 créé : `docs/EMA_PREMIUM_INDICATOR_V2.md` + artefact JSON.
- Snapshot récent exploitable `2025-03-07` : signal `NEUTRAL`, confidence `low`, premium score `0.410`, basis `48.32` EUR/t, z-score `0.127`.
- Historique : `2358` signaux, accuracy tous signaux `63.9%`.
- Signaux `medium/high` : coverage `57.7%`, accuracy `71.8%`.
- Sorties disponibles : `EU_PREMIUM_BULLISH`, `EU_PREMIUM_BEARISH`, `NEUTRAL`, `UNCERTAIN`.
- Wording : indicateur relatif EMA/CBOT uniquement, pas EMA direction absolue.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-PREM-02 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : indicateur recherche sur historique EMA proxy.

### EMA-BT-01 — Backtest relatif V2 coûts réalistes

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** EMA-PREM-02
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_relative_backtest_v2.py`
- `tests/test_ema_relative_backtest_v2.py`
- `docs/EMA_RELATIVE_BACKTEST_V2.md`
- `artefacts/ema_study/ema_relative_backtest_v2.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Critères de réussite
- Entrées weekly, non-overlap strict H40/H90.
- Stress coûts/slippage `1/2/3/5` EUR/t par leg.
- Stratégies premium H40/H90 : top confidence, basis extreme, combined/premium medium-high.
- Rapporter hit rate, PnL net, profit factor, drawdown, positive year share.
- Verdict explicite recherche seulement.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_relative_backtest_v2.py tests/test_ema_relative_backtest_v2.py
venv/bin/python -m pytest tests/test_ema_relative_backtest_v2.py
```

#### Résultat EMA-BT-01 (2026-05-25)

- Backtest relatif V2 créé : `docs/EMA_RELATIVE_BACKTEST_V2.md` + artefact JSON.
- Protocole : entrées weekly vendredi, non-overlap strict, coûts stressés `1/2/3/5` EUR/t par leg, 2 legs.
- Meilleure stratégie : `h90_combined_top40_weekly`, H90, `21` trades.
- À `1.0` EUR/t par leg : hit rate `80.95%`, PnL moyen `12.50` EUR/t, PnL total `262.58` EUR/t, profit factor `10.36`.
- À `5.0` EUR/t par leg : hit rate `57.14%`, PnL moyen `4.50` EUR/t, PnL total `94.58` EUR/t, profit factor `2.22`, positive year share `46.2%`.
- Conclusion : le meilleur signal reste positif sous coûts simplifiés élevés, mais l'échantillon est petit et la source proxy interdit tout claim production.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-BT-01 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : recherche seulement, pas de bid-ask historique, pas de marge, pas de roll execution réel.

### FINAL-EMA-01 — Rapport final EMA V3

**Priorité :** P2
**Type :** synthèse
**Statut :** DONE
**Dépendances :** EMA-BT-01
**Complexité :** simple

#### Fichiers à modifier
- `docs/EMA_FINAL_SYNTHESIS_V3.md`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Résultat FINAL-EMA-01 (2026-05-25)

- Synthèse finale V3 créée : `docs/EMA_FINAL_SYNTHESIS_V3.md`.
- Le document fige la conclusion : ne plus forcer EMA brut ; étudier et prédire la prime européenne EMA/CBOT.
- Sections incluses : verdict central, CBOT, EMA absolu, EMA relatif, basis, saisonnalité, indicateur premium V2, backtests relatifs, NO_GO, limites, conclusion finale.
- Vérification doc : `213` lignes ; mentions clés présentes (`NO_RELIABLE_PERIOD_ML`, `EU_PREMIUM_*`, `RESEARCH_ONLY_NOT_TRADING`).

#### Review FINAL-EMA-01 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.

## VAGUE V4 — Stress tests et rapport final

### EMA-V4-01 — Rapport final EMA V4

**Priorité :** P0
**Type :** rapport + artefact
**Statut :** DONE
**Dépendances :** FINAL-EMA-01
**Complexité :** simple

#### Objectif

Créer le rapport final V4 demandé : conclusion scientifique stabilisée, H40 principal prudent, H90 candidat stress-test, backtests `RESEARCH_ONLY_NOT_TRADING`, et roadmap V4.

#### Fichiers à modifier
- `src/mais/research/ema_final_report_v4.py`
- `tests/test_ema_final_report_v4.py`
- `docs/EMA_FINAL_REPORT_V4.md`
- `artefacts/ema_study/ema_final_report_v4.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Fichiers interdits
- `data/`
- `notebooks/`
- `*.parquet`
- `*.csv`

#### Critères de réussite
- EMA brut reste `NO_GO`.
- EMA relatif H40 = horizon principal prudent.
- H90 = candidat avancé à stress tester.
- Basis = variable centrale.
- Backtests = recherche seulement.
- Roadmap V4 inclut H90 strict, error archaeology, backtest V3, données EU.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_final_report_v4.py tests/test_ema_final_report_v4.py
venv/bin/python -m pytest tests/test_ema_final_report_v4.py
```

#### Résultat EMA-V4-01 (2026-05-25)

- Rapport final V4 créé : `docs/EMA_FINAL_REPORT_V4.md` + `artefacts/ema_study/ema_final_report_v4.json`.
- Conclusion officielle : CBOT = moteur mondial ; EMA brut = `NO_GO_AS_MAIN_TARGET`; EMA relatif H40 = `MAIN_RESEARCH_SIGNAL`; H90 = `PROMISING_STRESS_TEST_REQUIRED`; basis = `CENTRAL_ECONOMIC_DRIVER`.
- H40 principal prudent : DA `64.0%`, AUC `0.708`, balanced accuracy `64.2%`, top20 `77.1%`, weekly AUC `0.728`.
- H90 candidat : DA `69.0%`, AUC `0.770`, top20 `88.7%`, weekly AUC `0.766`.
- Backtests maintenus `NO_PRODUCTION_BACKTEST`.
- Roadmap V4 incluse : H90 strict, error archaeology, seasonal regimes, backtest V3, données EU, notebook bloqué.
- Vérifications : ruff ciblé PASS ; pytest ciblé `6 passed`.

#### Review EMA-V4-01 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : rapport basé sur source EMA proxy/exploratoire.

### EMA-H90-01 — Stress test strict H90

**Priorité :** P0
**Type :** module + doc
**Statut :** DONE
**Dépendances :** EMA-V4-01
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_h90_stress_test.py`
- `tests/test_ema_h90_stress_test.py`
- `docs/EMA_H90_STRESS_TEST.md`
- `artefacts/ema_study/ema_h90_stress_test.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Critères de réussite
- Tester H90 all OOF, non-overlap strict, no-roll proxy, no-crisis, leave-one-crisis-out.
- Ajouter stress coûts H90 issu du backtest V2.
- Produire un verdict `H90_MAIN_GO`, `H90_RESEARCH_ONLY` ou `H90_REJECTED_OVERLAP`.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_h90_stress_test.py tests/test_ema_h90_stress_test.py
venv/bin/python -m pytest tests/test_ema_h90_stress_test.py
```

#### Résultat EMA-H90-01 (2026-05-25)

- Stress test H90 créé : `docs/EMA_H90_STRESS_TEST.md` + artefact JSON.
- Verdict : `H90_MAIN_GO_RESEARCH_ONLY`, production `NO_PRODUCTION_BACKTEST`.
- All OOF : n `2358`, DA `69.0%`, AUC `0.770`, balanced accuracy `69.2%`, top20 `88.7%`.
- Strict non-overlap : n `26`, DA `76.9%`, AUC `0.922`, balanced accuracy `79.7%`, top20 `100.0%`.
- No-roll proxy : n `941`, DA `63.7%`, AUC `0.724`.
- No-crisis 2020-2022 : n `1785`, DA `70.0%`, AUC `0.758`.
- Leave-one-crisis-out stable : sans 2020 AUC `0.756`, sans 2021 AUC `0.766`, sans 2022 AUC `0.780`.
- Backtest V2 à coût `5` EUR/t/leg reste positif.
- Conclusion : H90 survit aux principaux stress tests, mais reste recherche uniquement à cause source proxy et exécution non réelle.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-H90-01 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : échantillon strict non-overlap petit (`26` observations), donc statut research-only.

### EMA-ERR-02 — Error archaeology relative H40/H90

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** EMA-H90-01
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_relative_error_archaeology_v2.py`
- `tests/test_ema_relative_error_archaeology_v2.py`
- `docs/EMA_RELATIVE_ERROR_ARCHAEOLOGY_V2.md`
- `artefacts/ema_study/ema_relative_error_archaeology_v2.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Critères de réussite
- Cataloguer H40/H90 : top corrects, worst errors, failed top20.
- Classer heuristiquement : ROLL_ARTIFACT, CRISIS_PERIOD, BASIS_EXTREME, CBOT_SHOCK, EU_PREMIUM_SHOCK, UNKNOWN.
- Résumer les tags dominants par horizon.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_relative_error_archaeology_v2.py tests/test_ema_relative_error_archaeology_v2.py
venv/bin/python -m pytest tests/test_ema_relative_error_archaeology_v2.py
```

#### Résultat EMA-ERR-02 (2026-05-25)

- Archéologie des erreurs H40/H90 créée : `docs/EMA_RELATIVE_ERROR_ARCHAEOLOGY_V2.md` + artefact JSON.
- H40 : `868` erreurs, `50` failed top20 ; tag dominant pires erreurs `ROLL_ARTIFACT` (`86`), puis `BASIS_EXTREME` (`56`) et `CRISIS_PERIOD` (`54`).
- H40 failed top20 : `ROLL_ARTIFACT` (`50`), `BASIS_EXTREME` (`34`), `CRISIS_PERIOD` (`33`).
- H90 : `731` erreurs, `50` failed top20 ; tag dominant pires erreurs `ROLL_ARTIFACT` (`70`), puis `CRISIS_PERIOD` (`44`) et `BASIS_EXTREME` (`29`).
- Conclusion : les prochains filtres d'abstention doivent intégrer roll-risk, crises et régimes de basis extrême.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-ERR-02 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : classification heuristique, pas attribution économique définitive.

### EMA-SEASON-02 — Seasonal premium regime study

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** EMA-ERR-02
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_seasonal_premium_regimes.py`
- `tests/test_ema_seasonal_premium_regimes.py`
- `docs/EMA_SEASONAL_PREMIUM_REGIMES.md`
- `artefacts/ema_study/ema_seasonal_premium_regimes.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Critères de réussite
- Définir les régimes saisonniers de prime européenne.
- Pour chaque saison, comparer H40 et H90 et recommander horizon/action.
- Marquer les saisons `TRADE_ALLOWED_RESEARCH`, `CAUTION` ou `ABSTAIN`.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_seasonal_premium_regimes.py tests/test_ema_seasonal_premium_regimes.py
venv/bin/python -m pytest tests/test_ema_seasonal_premium_regimes.py
```

#### Résultat EMA-SEASON-02 (2026-05-25)

- Régimes saisonniers premium créés : `docs/EMA_SEASONAL_PREMIUM_REGIMES.md` + artefact JSON.
- `TRADE_ALLOWED_RESEARCH` : `sep_nov_eu_harvest` H90 AUC `0.916`, DA `84.2%`; `jul_aug_yield_stress` H90 AUC `0.866`, DA `80.4%`; `dec_import_export_arbitrage` H40 AUC `0.830`, DA `73.6%`.
- `CAUTION` : `apr_jun_sowing_weather` H90 AUC `0.767`, DA `63.9%`; `jan_mar_old_crop_import` H40 AUC `0.715`, DA `65.8%`.
- Aucune saison en `ABSTAIN` dans ce protocole V4, mais les confidence tiers restent requis.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-SEASON-02 (2026-05-25)

- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : régimes de recherche sur source EMA proxy.

### EMA-BT-03 — Backtest relatif V3 exécution réaliste

**Priorité :** P1
**Type :** module + doc
**Statut :** DONE
**Dépendances :** EMA-SEASON-02
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_relative_backtest_v3.py`
- `tests/test_ema_relative_backtest_v3.py`
- `docs/EMA_RELATIVE_BACKTEST_V3.md`
- `artefacts/ema_study/ema_relative_backtest_v3.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Critères de réussite
- Backtest H90 premium avec seuil top40 train-only par année.
- Entrées weekly, saisons fortes uniquement, no-trade near-roll proxy, non-overlap strict.
- Coûts dynamiques : commission + slippage stress + roll cost proxy.
- Rapporter hit rate, PnL, PF, Sortino, average win/loss, worst trade, max drawdown, positive years.
- Maintenir `RESEARCH_ONLY_NOT_TRADING`.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_relative_backtest_v3.py tests/test_ema_relative_backtest_v3.py
venv/bin/python -m pytest tests/test_ema_relative_backtest_v3.py
```

#### Résultat EMA-BT-03 (2026-05-25)

- Backtest V3 créé et généré : `docs/EMA_RELATIVE_BACKTEST_V3.md`, `artefacts/ema_study/ema_relative_backtest_v3.json`.
- Protocole : H90, entrées weekly vendredi, seuil top40 calibré train-only par années passées, saisons fortes uniquement, exclusion near-roll proxy, non-overlap strict 90 jours.
- Signaux candidats avant non-overlap : `48`; trades finaux stricts : `9`.
- Coût/slippage `1.0` EUR/t par leg : hit rate `66.7%`, PnL total `99.40` EUR/t, PnL moyen `11.04` EUR/t, profit factor `4.86`, Sortino `2.62`, max drawdown `-23.14` EUR/t.
- Coût/slippage `5.0` EUR/t par leg : hit rate `55.6%`, PnL total `27.40` EUR/t, PnL moyen `3.04` EUR/t, profit factor `1.48`, Sortino `0.81`, max drawdown `-33.88` EUR/t.
- Verdict maintenu : `RESEARCH_ONLY_NOT_TRADING`, `NO_PRODUCTION_BACKTEST`.
- Réserve : échantillon très petit après filtres stricts (`9` trades), source EMA proxy, coûts/roll/slippage encore approximés.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-BT-03 (2026-05-25)

- Critères ticket vérifiés : seuil train-only, weekly, saisons fortes, no-roll proxy, non-overlap strict, coûts stressés, métriques complètes, wording research-only.
- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : résultat prometteur mais non tradable, à considérer comme validation recherche de la prime européenne.

### EMA-V5-01 — Target lab EMA nouvelles cibles

**Priorité :** P0
**Type :** module + doc + artefact
**Statut :** DONE
**Dépendances :** EMA-BT-03
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_target_lab_v5.py`
- `tests/test_ema_target_lab_v5.py`
- `docs/EMA_TARGET_LAB_V5.md`
- `artefacts/ema_study/ema_target_lab_v5.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Objectif

Tester de nouvelles cibles EMA orientées prime européenne plutôt que direction brute : compression du basis, reversion extrême, outperformance forte, sous-performance forte, continuation/reversion relative, et cibles conditionnées par régime CBOT/basis.

#### Critères de réussite
- Au moins 6 cibles testées.
- Horizons H20/H40/H90.
- Protocole OOF crop-year strict.
- Métriques : DA, balanced accuracy, AUC, MCC, top20, base rate, coverage.
- Verdict : identifier les cibles prometteuses vs NO_GO.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_target_lab_v5.py tests/test_ema_target_lab_v5.py
venv/bin/python -m pytest tests/test_ema_target_lab_v5.py
```

#### Résultat EMA-V5-01 (2026-05-26)

- Target lab V5 créé : `src/mais/research/ema_target_lab_v5.py`, `docs/EMA_TARGET_LAB_V5.md`, `artefacts/ema_study/ema_target_lab_v5.json`.
- `24` cibles testées sur H20/H40/H90 ; `24` évaluables ; `9` cibles `PROMISING_TARGET`, `5` cibles `WATCHLIST_TARGET`.
- Meilleure cible : `y_rel_outperform_when_basis_extreme_h90`, n `510`, AUC `0.881`, balanced accuracy `0.728`, top20 DA `0.912`, base rate `0.396`.
- Cible forte H40 : `y_rel_outperform_when_basis_extreme_h40`, n `553`, AUC `0.803`, balanced accuracy `0.712`, top20 DA `0.827`.
- Les queues relatives confirment aussi le signal : `y_rel_large_outperform_h90` AUC `0.781`, `y_rel_large_underperform_h90` AUC `0.770`.
- Conclusion : les nouvelles cibles utiles restent des cibles de prime relative/basis, pas des cibles EMA absolues.
- Vérifications : ruff ciblé PASS ; pytest ciblé `6 passed`.

#### Review EMA-V5-01 (2026-05-26)

- Critères vérifiés : plus de 6 cibles, H20/H40/H90, OOF crop-year, métriques robustes, verdicts par cible.
- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : source EMA proxy et cibles conditionnelles parfois plus petites ; research-only.

### EMA-V5-02 — Cross-data interaction lab premium

**Priorité :** P1
**Type :** module + doc + artefact
**Statut :** DONE
**Dépendances :** EMA-V5-01
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_cross_data_interactions_v5.py`
- `tests/test_ema_cross_data_interactions_v5.py`
- `docs/EMA_CROSS_DATA_INTERACTIONS_V5.md`
- `artefacts/ema_study/ema_cross_data_interactions_v5.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Objectif

Tester si les croisements basis × saison, basis × volatilité, basis × CBOT momentum, basis × énergie/EURUSD/météo/WASDE ajoutent une vraie valeur OOF au signal premium.

#### Critères de réussite
- Comparer base model vs cross features.
- H40/H90 au minimum.
- Ablation par famille de croisements.
- Métriques : AUC, balanced accuracy, top20, delta vs base, stabilité annuelle.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_cross_data_interactions_v5.py tests/test_ema_cross_data_interactions_v5.py
venv/bin/python -m pytest tests/test_ema_cross_data_interactions_v5.py
```

#### Résultat EMA-V5-02 (2026-05-26)

- Cross-data lab créé : `src/mais/research/ema_cross_data_interactions_v5.py`, `docs/EMA_CROSS_DATA_INTERACTIONS_V5.md`, `artefacts/ema_study/ema_cross_data_interactions_v5.json`.
- `40` expériences OOF évaluées : targets H40/H90 x base/market/season/EU/all-cross.
- Meilleur overall : `y_rel_outperform_when_basis_extreme_h90` avec `all_cross`, AUC `0.906`, balanced accuracy `0.756`.
- Meilleur gain vs base : `y_rel_outperform_h40` avec `base_plus_season_cross`, delta AUC `+0.028`, delta balanced accuracy `+0.007`, top20 DA `0.848`.
- Gain notable : `y_rel_outperform_when_basis_extreme_h90` avec `base_plus_market_cross`, delta AUC `+0.022`, delta balanced accuracy `+0.060`, top20 DA `0.980`.
- Conclusion : les croisements basis × saison/marché ajoutent de la valeur OOF ; les croisements EU/WASDE disponibles n'ajoutent pas encore de gain mesurable dans ce run.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-V5-02 (2026-05-26)

- Critères vérifiés : base vs cross, H40/H90, delta AUC/BA/top20, ablation par familles de croisements.
- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : les interactions affinent le basis, elles ne prouvent pas une causalité.

### EMA-V5-03 — Modèle hiérarchique CBOT + prime EU

**Priorité :** P1
**Type :** module + doc + artefact
**Statut :** DONE
**Dépendances :** EMA-V5-02
**Complexité :** moyen

#### Fichiers à modifier
- `src/mais/research/ema_hierarchical_cbot_premium_v5.py`
- `tests/test_ema_hierarchical_cbot_premium_v5.py`
- `docs/EMA_HIERARCHICAL_CBOT_PREMIUM_V5.md`
- `artefacts/ema_study/ema_hierarchical_cbot_premium_v5.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Objectif

Tester l'architecture finale logique : modèle CBOT mondial + modèle prime relative EU, puis comparaison contre la direction EMA brute directe.

#### Critères de réussite
- Construire un signal hiérarchique EMA = CBOT expected direction + premium expected direction.
- Comparer direct EMA, CBOT seul, premium seul, hiérarchique.
- H40/H90, OOF crop-year, metrics robustes.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_hierarchical_cbot_premium_v5.py tests/test_ema_hierarchical_cbot_premium_v5.py
venv/bin/python -m pytest tests/test_ema_hierarchical_cbot_premium_v5.py
```

#### Résultat EMA-V5-03 (2026-05-26)

- Modèle hiérarchique créé : `src/mais/research/ema_hierarchical_cbot_premium_v5.py`, `docs/EMA_HIERARCHICAL_CBOT_PREMIUM_V5.md`, `artefacts/ema_study/ema_hierarchical_cbot_premium_v5.json`.
- Comparaison sur direction EMA absolue diagnostic : `direct_ema`, `cbot_only`, `premium_only`, `hierarchical_fixed`, `hierarchical_train_weighted`.
- Meilleur modèle : `cbot_only` H40, AUC `0.559`, balanced accuracy `0.545`, DA `0.545`, top20 DA `0.482`.
- H40 : `hierarchical_fixed` AUC `0.540`, delta AUC vs direct `+0.024`, mais balanced accuracy `0.516`.
- H90 : `hierarchical_train_weighted` AUC `0.532`, delta AUC vs direct `+0.122`, mais balanced accuracy `0.507`.
- Conclusion : la décomposition CBOT + prime améliore certains diagnostics AUC, mais ne transforme pas EMA direction absolue en cible robuste. Le signal principal doit rester EMA/CBOT relatif.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-V5-03 (2026-05-26)

- Critères vérifiés : signal hiérarchique, comparaison direct/CBOT/premium/hiérarchique, H40/H90, OOF crop-year.
- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : cible EMA absolue toujours diagnostic/NO_GO, pas cible finale.

### EMA-V5-04 — Synthèse finale V5 enrichie

**Priorité :** P2
**Type :** doc + artefact
**Statut :** DONE
**Dépendances :** EMA-V5-03
**Complexité :** simple

#### Fichiers à modifier
- `src/mais/research/ema_final_synthesis_v5.py`
- `tests/test_ema_final_synthesis_v5.py`
- `docs/FINAL_CORN_STUDY_CBOT_EMA_V5.md`
- `artefacts/ema_study/ema_final_synthesis_v5.json`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Objectif

Produire la synthèse V5 : CBOT moteur mondial, EMA brut NO_GO, prime EMA/CBOT cible principale, nouvelles cibles V5, croisements utiles, hiérarchie CBOT+prime, limites proxy/research-only.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/ema_final_synthesis_v5.py tests/test_ema_final_synthesis_v5.py
venv/bin/python -m pytest tests/test_ema_final_synthesis_v5.py
```

#### Résultat EMA-V5-04 (2026-05-26)

- Synthèse V5 créée : `src/mais/research/ema_final_synthesis_v5.py`, `docs/FINAL_CORN_STUDY_CBOT_EMA_V5.md`, `artefacts/ema_study/ema_final_synthesis_v5.json`.
- Conclusion centrale : CBOT = `GLOBAL_MAIZE_DRIVER`, EMA absolu = `NO_GO_AS_MAIN_TARGET`, EMA/CBOT H40 = `PRIMARY_RESEARCH_SIGNAL`, EMA/CBOT H90 = `PROMISING_RESEARCH_SIGNAL`, basis = `CENTRAL_ECONOMIC_DRIVER`.
- V5 target lab : meilleure cible `y_rel_outperform_when_basis_extreme_h90`, AUC `0.881`, balanced accuracy `0.728`, top20 DA `0.912`.
- V5 cross-data : meilleur overall `y_rel_outperform_when_basis_extreme_h90` avec `all_cross`, AUC `0.906`, balanced accuracy `0.756`; meilleur delta H40 `base_plus_season_cross`, delta AUC `+0.028`.
- V5 hiérarchique : meilleur diagnostic `cbot_only` H40, AUC `0.559`, balanced accuracy `0.545`; conclusion EMA absolu reste faible.
- Backtest V3 rappelé : `RESEARCH_ONLY_NOT_TRADING`, `NO_PRODUCTION_BACKTEST`, high-cost PnL moyen `3.04` EUR/t mais seulement `9` trades stricts.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review EMA-V5-04 (2026-05-26)

- Critères vérifiés : synthèse V5 couvre target lab, cross-data, hiérarchie, backtest, limites proxy, no-go et roadmap.
- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : la synthèse est research-only tant que la source EMA historique officielle n'est pas validée.

### V6-00 — Experiment registry global

**Priorité :** P0
**Type :** infrastructure + tests + doc
**Statut :** DONE
**Dépendances :** EMA-V5-04
**Complexité :** simple

#### Fichiers à modifier
- `src/mais/research/experiment_registry_v6.py`
- `tests/test_experiment_registry_v6.py`
- `docs/EXPERIMENT_REGISTRY_V6.md`
- `artefacts/experiments/experiment_registry_v6.csv`
- `artefacts/experiments/experiment_registry_v6.parquet`
- `.ai/STATE.md`
- `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Objectif

Créer un registry unique pour les expériences V6 : chaque run doit pouvoir enregistrer son ID, protocole, cible, métriques, verdict et chemins d'artefacts.

#### Vérifications à lancer

```bash
venv/bin/ruff check src/mais/research/experiment_registry_v6.py tests/test_experiment_registry_v6.py
venv/bin/python -m pytest tests/test_experiment_registry_v6.py
```

#### Résultat V6-00 (2026-05-26)

- Registry V6 créé : `src/mais/research/experiment_registry_v6.py`, `docs/EXPERIMENT_REGISTRY_V6.md`.
- Artefacts générés : `artefacts/experiments/experiment_registry_v6.csv`, `artefacts/experiments/experiment_registry_v6.parquet`.
- Champs obligatoires : `experiment_id`, `date_run`, `git_commit`, `dataset_version`, `feature_set`, `target`, `horizon`, `model`, `cv_protocol`, `train_period`, `test_period`, `metrics`, `artefact_paths`, `verdict`, `config_hash`.
- Seed initial : `3` records (`GO` registry, `PROMISING` EMA premium V6, `PROMISING` CBOT V6).
- Vérifications : ruff ciblé PASS ; pytest ciblé `4 passed`.

#### Review V6-00 (2026-05-26)

- Critères vérifiés : CSV/parquet générés, verdict présent, métriques aplaties, hash config présent, chemins d'artefacts enregistrés.
- Review demandée par l'utilisateur : validé `DONE`.

### V6-01 — Target labs EMA + CBOT complets

**Statut :** DONE
**Dépendances :** V6-00
**Fichiers à modifier :** `src/mais/research/target_labs_v6.py`, `tests/test_target_labs_v6.py`, `docs/TARGET_LABS_V6.md`, `artefacts/v6/target_labs_v6.json`, `.ai/STATE.md`, `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Résultat V6-01 (2026-05-26)

- Target labs V6 créés : `src/mais/research/target_labs_v6.py`, `docs/TARGET_LABS_V6.md`, `artefacts/v6/target_labs_v6.json`.
- `55` cibles testées, `53` évaluables en OOF.
- Meilleure cible EMA : `y_rel_outperform_when_basis_extreme_h40`, AUC `0.968`, balanced accuracy `0.908`, top20 `1.000`.
- Autres EMA forts : `y_rel_outperform_h120` AUC `0.921`, `y_rel_large_outperform_h120` AUC `0.910`, `y_rel_outperform_when_basis_extreme_h20` AUC `0.877`.
- Meilleure cible CBOT : `y_cbot_drawdown_5pct_h20`, AUC `0.750`, balanced accuracy `0.693`, top20 `0.889`.
- Autres CBOT prometteurs : drawdown H60 AUC `0.718`, large_down H90 AUC `0.716`, large_down H60 AUC `0.705`.
- Conclusion : les meilleurs capteurs V6 sont la prime EMA conditionnelle au basis extrême et le risque de drawdown CBOT.
- Vérifications : ruff ciblé PASS ; pytest ciblé `6 passed`.

#### Review V6-01 (2026-05-26)

- Critères vérifiés : NaN tail conservés, supports/base rates/rare flags présents, EMA + CBOT couverts, registry alimenté.
- Review demandée par l'utilisateur : validé `DONE`.

### V6-02 — Cross-target OOF factory + meta-features

**Statut :** DONE
**Dépendances :** V6-01
**Fichiers à modifier :** `src/mais/research/cross_target_oof_v6.py`, `tests/test_cross_target_oof_v6.py`, `docs/CROSS_TARGET_OOF_V6.md`, `artefacts/v6/cross_target_oof_v6.json`, `.ai/STATE.md`, `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Résultat V6-02 (2026-05-26)

- Cross-target OOF factory créé : `src/mais/research/cross_target_oof_v6.py`, `docs/CROSS_TARGET_OOF_V6.md`, `artefacts/v6/cross_target_oof_v6.json`.
- Artefacts générés : `artefacts/v6/cross_target_oof_predictions_v6.parquet` et `artefacts/v6/meta_features_v6.parquet`.
- `26` séries OOF auxiliaires, `35` colonnes meta-features.
- Meilleure série OOF : `y_rel_outperform_when_basis_extreme_h90` logistic, AUC `1.000`, mais n `29` seulement donc capteur étroit.
- Signal large robuste : `y_rel_outperform_h120` logistic AUC `0.883` sur n `763`; `y_rel_outperform_h40` logistic AUC `0.808` sur n `763`.
- Tests anti-leakage : `is_oof=True` et `train_end < test_start` validés.
- Vérifications : ruff ciblé PASS ; pytest ciblé `5 passed`.

#### Review V6-02 (2026-05-26)

- Critères vérifiés : manifest OOF complet, dates de folds strictement ordonnées, meta-features agrégées, registry alimenté.
- Review demandée par l'utilisateur : validé `DONE`.
- Réserve : certaines cibles conditionnelles ont un support faible et doivent être traitées comme capteurs de contexte.

### V6-03 — Meta-model premium + confiance + abstention

**Statut :** NEEDS_REVIEW
**Dépendances :** V6-02
**Fichiers à modifier :** `src/mais/research/meta_model_premium_v6.py`, `tests/test_meta_model_premium_v6.py`, `docs/META_MODEL_PREMIUM_V6.md`, `artefacts/v6/meta_model_premium_v6.json`, `.ai/STATE.md`, `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Résultat V6-03 (2026-05-27)

- Meta-model premium V6 créé : `src/mais/research/meta_model_premium_v6.py`, `tests/test_meta_model_premium_v6.py`, `docs/META_MODEL_PREMIUM_V6.md`, `artefacts/v6/meta_model_premium_v6.json`.
- Comparaison stricte OOF : `classic`, `meta_only`, `classic_plus_meta`, `meta_plus_basis`, `full_stack`.
- Garde anti-leakage : les meta-features sont uniquement les prédictions OOF V6-02 ; les features classiques sont `shift(1)` ; l'imputation est apprise sur le train du fold uniquement.
- Meilleur résultat robuste large : `y_rel_outperform_h90` avec `classic_plus_meta`, n `503`, AUC `0.937`, balanced accuracy `0.854`, top20 DA `0.970`, ECE `0.121`.
- Meilleur capteur contexte étroit : `y_rel_outperform_when_basis_extreme_h90`, AUC `1.000`, mais n `29` seulement ; documenté comme signal de contexte fragile, pas preuve générale.
- Meilleur gain réel des meta-features vs classic : `y_rel_outperform_h40` avec `meta_only`, delta AUC `+0.0209`.
- Abstention sur le meilleur modèle robuste : `top40_confidence` coverage `39.96%`, DA `0.970`, AUC `0.977`; `top20_confidence` coverage `20.08%`, DA `0.970`, AUC `0.971`.
- Verdict scientifique : le stacking OOF améliore surtout la confiance/sélectivité ; pour H90, `classic_plus_meta` produit un signal très fort mais reste exploratoire/proxy EMA.
- Vérifications : ruff ciblé PASS ; pytest ciblé `6 passed`.
- Statut mis en `NEEDS_REVIEW` conformément aux règles AGENTS ; V6-04 reste `BLOCKED` tant qu'une review ne passe pas V6-03 en `DONE`.

#### Review V6-03 (2026-05-27)

- Review intégrale demandée par l'utilisateur : validé `DONE`.
- Critères vérifiés : meta-features OOF uniquement, features classiques `shift(1)`, imputation train-only, comparaison classic/meta/full stack, politiques d'abstention présentes, artefact et doc générés.
- Tests relancés : ruff ciblé PASS ; pytest ciblé `6 passed`.
- Réserve conservée : les résultats EMA restent exploratoires/proxy, et les lignes parfaites sur `basis_extreme_h90` sont à petit support.

### V6-04 — Roll-aware, seasonal experts, backtests V6

**Statut :** DONE
**Dépendances :** V6-03
**Fichiers à modifier :** `src/mais/research/roll_season_backtest_v6.py`, `tests/test_roll_season_backtest_v6.py`, `docs/ROLL_SEASON_BACKTEST_V6.md`, `artefacts/v6/roll_season_backtest_v6.json`, `.ai/STATE.md`, `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Résultat V6-04 (2026-05-27)

- Module roll-aware/seasonal/backtest V6 créé : `src/mais/research/roll_season_backtest_v6.py`, tests dédiés, doc et artefact générés.
- Scénarios testés : H40, H90, expert saisonnier H40/H90, accord H40/H90.
- Politiques : all, no-roll proxy, strong season, strong season no-roll, top40 train-only, top20 train-only, top40 no-roll.
- Meilleure politique : `seasonal_expert/top20_train_only`, n `68`, coverage `13.5%`, DA `98.5%`, balanced accuracy `98.3%`, AUC `0.982`, annual stability `100%`.
- Meilleur backtest research-only : `seasonal_expert/top40_no_roll`, `9` trades, coût `1` EUR/t/leg, hit rate `88.9%`, PnL total `179.65` EUR/t, PF `100.16`, max drawdown `-1.81` EUR/t. À `3` EUR/t/leg, PnL total `143.65` EUR/t ; à `5`/`8`, voir artefact.
- Garde-fous : seuils confidence train-only par année, non-overlap strict, coûts par jambe, roll proxy cost, verdict `RESEARCH_ONLY_NOT_TRADING`.
- Vérifications : ruff ciblé PASS ; pytest ciblé `6 passed`.

#### Review V6-04 (2026-05-27)

- Review intégrale demandée par l'utilisateur : validé `DONE`.
- Critères vérifiés : filtres roll-aware présents, expert saisonnier présent, stress coûts 1/2/3/5/8, trades non-overlap testés, doc/artefact générés.
- Réserve forte maintenue : meilleur backtest à petit nombre de trades (`9`) et source EMA proxy ; résultat prometteur mais non tradable.

### V6-05 — CBOT/cross-market/decomposition/event studies

**Statut :** DONE
**Dépendances :** V6-04
**Fichiers à modifier :** `src/mais/research/cbot_cross_market_v6.py`, `tests/test_cbot_cross_market_v6.py`, `docs/CBOT_CROSS_MARKET_V6.md`, `artefacts/v6/cbot_cross_market_v6.json`, `.ai/STATE.md`, `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Résultat V6-05 (2026-05-27)

- Module CBOT/cross-market/décomposition/events créé : `src/mais/research/cbot_cross_market_v6.py`, tests dédiés, doc et artefact générés.
- CBOT cross-market : les features EMA premium ajoutent du signal à certains risques CBOT. Meilleur gain : `y_cbot_up_h60` avec `cbot_full_cross_market`, AUC `0.577`, delta AUC `+0.059` vs `cbot_base`; `y_cbot_large_down_3pct_h90` avec `cbot_plus_ema_premium`, AUC `0.636`, delta `+0.056`.
- EMA impact of CBOT meta : les meta-signaux CBOT n'améliorent pas EMA premium ; H40 delta AUC `-0.0167`, H90 delta AUC `-0.0237` vs base EMA. Conclusion : CBOT explique le monde, mais la prime EMA reste surtout basis/premium.
- Décomposition EMA : R² descriptif élevé, H40 all `0.888`, H90 all `0.961`; sensibilité CBOT plus forte en crise (`~0.79/0.80`) qu'en période normale (`~0.57/0.65`).
- Event study premium ajoutée : WASDE, basis extrême, vol CBOT top décile, gas ratio top décile, mois roll proxy.
- Vérifications : ruff ciblé PASS ; pytest ciblé `6 passed`.

#### Review V6-05 (2026-05-27)

- Review intégrale demandée par l'utilisateur : validé `DONE`.
- Critères vérifiés : comparaisons OOF shift(1), cross-market dans les deux sens, décomposition H40/H90 normale/crise, event study, doc/artefact générés.
- Réserve : les gains CBOT restent modestes en niveau absolu ; EMA source proxy maintenue.

### V6-06 — Rapport final V6 + review intégrale

**Statut :** DONE
**Dépendances :** V6-05
**Fichiers à modifier :** `src/mais/research/final_corn_study_v6.py`, `tests/test_final_corn_study_v6.py`, `docs/FINAL_CORN_STUDY_V6.md`, `artefacts/v6/final_corn_study_v6.json`, `.ai/STATE.md`, `.ai/TICKETS_ETUDE_EMA_PHASE2.md`

#### Résultat V6-06 (2026-05-27)

- Rapport final V6 + review intégrale créés : `src/mais/research/final_corn_study_v6.py`, `tests/test_final_corn_study_v6.py`, `docs/FINAL_CORN_STUDY_V6.md`, `artefacts/v6/final_corn_study_v6.json`.
- Conclusion centrale V6 : CBOT = moteur mondial ; EMA absolu = `NO_GO_AS_MAIN_TARGET`; EMA/CBOT premium = `PRIMARY_RESEARCH_SIGNAL`; production/trading = `RESEARCH_ONLY_NOT_TRADING`.
- Synthèse V6 : meilleur meta-model robuste `y_rel_outperform_h90/classic_plus_meta`, n `503`, AUC `0.937`, top20 `0.970`; meilleur filtre saison/roll `seasonal_expert/top20_train_only`, BA `0.983`, AUC `0.982`; meilleur backtest research-only `seasonal_expert/top40_no_roll`, `9` trades, PnL `179.65` EUR/t à `1` EUR/t/leg.
- Review automatisée : JSON/docs/tests/registry présents, support robuste meta OK, signal parfait contexte non promu comme preuve générale, backtest research-only, caveat proxy EMA présent.
- Verdict review : `PASS_WITH_RESEARCH_ONLY_CAVEATS`.
- Vérifications finales groupées V6 : ruff ciblé PASS ; pytest V6 groupé `37 passed in 186.06s`.
- V6-17 reste `BLOCKED` : les règles projet interdisent lecture/modification de `notebooks/`.

#### Review V6-06 (2026-05-27)

- Review intégrale demandée par l'utilisateur : validé `DONE`.
- Aucune correction restante dans le périmètre exécutable V6.
- Réserves finales : source EMA proxy, backtests research-only, petit échantillon de trades, notebook bloqué par règle AGENTS.

### V6-17 — Notebook V6 complet

**Statut :** BLOCKED
**Dépendances :** V6-06
**Blocage :** les règles AGENTS interdisent lecture/modification de `notebooks/`.
