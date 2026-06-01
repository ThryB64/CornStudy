# ROADMAP EXPÉRIENCES — V8 — MAIS CBOT + EURONEXT

**Date** : 2026-05-30.
**Statut global** : `RESEARCH_ONLY_NOT_TRADING`.
**Référence** : prolonge `docs/ROADMAP_ETUDE_MAIS_V7.md` ; consolide les expériences A–N proposées par le cadrage utilisateur.

---

## Préambule

V8 ne remplace pas V7 — il **valide, étend et consolide**. Aucun artefact V7 n'est supprimé. Toutes les expériences V8 produisent leurs propres artefacts sous `artefacts/v8/*.json` et sont enregistrées dans `artefacts/registry/experiments.jsonl` (registre unifié après `V8-REGISTRY-MERGE`).

Principes de l'exécution V8 :

1. Aucune expérience ne tourne tant que `V8-INFRA-HOLDOUT`, `V8-REGISTRY-MERGE` et `V8-MT-BH-GLOBAL` ne sont pas DONE.
2. `V8-META-REVALIDATION` est la première expérience scientifique — elle débloque le reste.
3. Chaque expérience produit un artefact JSON, une entrée registry, un test unitaire, un test anti-leakage si applicable.
4. Chaque résultat est obligatoirement verdict ∈ {`GO_RESEARCH`, `PROMISING`, `FRAGILE`, `NO_GO`, `RESEARCH_ONLY_NOT_TRADING`} + p_value + q_BH.
5. Chaque résultat trop bon (AUC > 0.85 avec n < 100, ou DA > 90%) est automatiquement marqué `FRAGILE_REVIEW_REQUIRED`.
6. Pas de notebook agent (règle projet) — seulement modules + docs.

---

## A. CBOT TARGET LAB AVANCÉ — `V8-CBOT-LAB-PLUS`

### Hypothèse économique
Le CBOT direction up/down brut sature autour de DA 62%. Les cibles spécialisées (drawdown, rally, large move conditionnels) sont plus prédictibles parce qu'elles isolent un régime stable du marché.

### Cibles ajoutées par V8 (par rapport à V7-04)
- **Triple barrier** ±3 / ±5 % H40 et H60.
- **Conditionnels fondamentaux** :
  - `y_cbot_up_when_stocks_tight_h60` (ending/use < p25 train)
  - `y_cbot_down_when_stocks_abundant_h60` (> p75 train)
  - `y_cbot_down_when_cot_extreme_long_h40` (cot_noncomm > p80 train)
  - `y_cbot_up_when_cot_extreme_short_h40` (cot_noncomm < p20 train)
  - `y_cbot_up_when_weather_stress_h40` (GDD heat > 2σ OU rain_deficit > 2σ)
  - `y_cbot_move_after_wasde_h5`
  - `y_cbot_up_when_ethanol_parity_cheap`
  - `y_cbot_down_when_ethanol_parity_dear`

### Protocole
- Walk-forward purged + embargo H jours (V7-02 standard).
- Seuils stocks/COT calibrés `expanding` sur train uniquement.
- Verdict par cible : AUC, DA, BA, top20, MCC, n_oof, BH q.

### Livrables
- `artefacts/v8/cbot_target_lab_plus.json`
- Mise à jour `docs/PROFESSIONAL_STUDY_REPORT.md` table cibles CBOT.

---

## B. EMA PREMIUM TARGET LAB AVANCÉ — `V8-EMA-PREMIUM-LAB-PLUS`

### Hypothèse économique
Le signal exploitable n'est pas le prix EMA brut mais la performance relative EMA/CBOT, et certaines décompositions du basis (compression, expansion, reversion).

### Cibles ajoutées par V8
- `y_rel_outperform_h10 / h20 / h40 / h60 / h90 / h120`
- `y_rel_large_outperform_h40 / h90` (top 25%)
- `y_rel_large_underperform_h40 / h90`
- `y_basis_compression_h20 / h40` (basis_t+H < basis_t - σ)
- `y_basis_expansion_h20 / h40`
- `y_basis_reversion_h20 / h40` (retour vers moyenne mobile)
- `y_basis_continuation_h20 / h40`
- `y_basis_extreme_h40 / h90` (basis_z > 1.5 ou < -1.5)
- `y_season_extreme_h40` (saison nov-jan)
- `y_fx_neutral_premium` (basis - drift_fx_long_run)
- `y_fair_value_deviation_h40` (P_EMA - P_fair_estimated)
- `y_residual_eu_shock_h20` (résidu EU > 2σ in 5j)

### Protocole
- Identique CBOT, embargo H jours.
- Marquage automatique FRAGILE si n_oof < 100.

### Livrables
- `artefacts/v8/ema_premium_target_lab_plus.json`

---

## C. CROSS-TARGET STACKING ÉCONOMIQUE — `V8-CROSS-TARGET-V3`

### Hypothèse
Le V7-03 a tourné sur la mauvaise cible (fallback `y_up_h20`). Réécrire avec les bonnes cibles `y_rel_outperform_h40/h90` présentes obligatoirement dans le dataset.

### Experts niveau 0 (tous OOF, nested walk-forward)
- CBOT direction H20/H40/H60/H90
- CBOT drawdown 5pct H20/H60
- CBOT rally 5pct H20/H40
- CBOT volatility H20/H40
- EMA rel_outperform H40/H90/H120
- EMA large_outperform H40/H90
- EMA large_underperform H40/H90
- Basis_extreme_h40/h90
- Basis_compression_h40
- Basis_expansion_h40
- Basis_regime (one-hot 6 régimes)
- Seasonal_expert (4 saisons)
- Roll_risk_score
- Data_quality_score
- FX-neutral premium
- Fair_value_deviation
- EU_residual_shock

### Meta-features
- mean_p, std_p, median_p
- entropy_distribution
- H40_H90_agreement
- H90_H120_agreement
- CBOT_EMA_disagreement
- basis_model_agreement
- volatility_warning_flag
- residual_shock_warning_flag
- max_confidence
- n_bullish / n_bearish / n_uncertain
- interaction cbot_bullish × basis_extreme
- interaction ema_rel × season_harvest

### Comparaisons
- classic seul
- meta seul
- classic + meta
- basis rule seul
- season rule seul
- classic + basis + season (règle économique pure)
- classic + meta + basis + season + roll + Pcorrect (full stack)

### Protocole
Nested walk-forward leave-one-crop-year + embargo 90 jours. Vérification stricte `inner_test_dates ∩ outer_test_dates = ∅` (déjà dans `nested_stacking.py`).

### Livrables
- `artefacts/v8/cross_target_stacking_v3.json`
- `docs/V8_CROSS_TARGET_STACKING_V3.md`

---

## D. CROSS-MARKET CBOT ↔ EMA — `V8-CROSS-MARKET-V3`

### Hypothèses
- H1 : EMA premium extrême → choc CBOT à H5/H10/H20.
- H2 : Signal CBOT → premium EMA à H40/H90.
- H3 : Divergences EMA/CBOT > 2σ = signal d'arbitrage ou stress local ?
- H4 : Lead-lag dominant change selon saison.
- H5 : β EMA→CBOT varie par régime basis.

### Tests
- Ablation OOF systématique :
  - features EMA → CBOT targets
  - features CBOT → EMA premium targets
- Granger BH-corrigé bi-directionnel par horizon (H5/H10/H20/H40/H90).
- Event study autour des divergences > 2σ.
- Régression rolling β(t) 60/120/252 jours.

### Livrables
- `artefacts/v8/cross_market_v3.json`

---

## E. BASIS REGIME STUDY V3 — `V8-BASIS-REGIME-V3`

### Régimes à détecter (méthodes parallèles)
| Méthode | Paramètres | Sortie |
|---|---|---|
| Règles manuelles | z-score basis + delta + saison | label 7 régimes |
| KMeans | k=4/5/6/7 | cluster id |
| GMM | k=4/5/6 | proba cluster |
| HMM | 3/4 états | état + transition matrix |
| Markov Switching Regression | 2/3 régimes | régime latent |

### Validation
- Stabilité walk-forward (5-fold).
- Score Silhouette.
- BIC.
- AUC premium H40 par régime.
- Probabilité de transition imminente.

### Régimes attendus (économiquement)
- NORMAL
- HIGH_STABLE
- HIGH_COMPRESSING
- HIGH_EXPANDING
- LOW_BASIS
- CRISIS_EUROPE
- ROLL_DISTORTED

### Livrables
- `artefacts/v8/basis_regimes_v3.json`
- Comparaison vs V7-08 (6 régimes, dominant NORMAL).

---

## F. SEASONAL EXPERT MODELS — `V8-SEASONAL-V3`

### Saisons opérées
- `jan-mar` : old crop / import / stocks hiver
- `apr-jun` : semis EU / récolte Brésil
- `jul-aug` : stress rendement EU et US
- `sep-nov` : récolte EU
- `dec` : arbitrage / transition crop year

### Pour chaque saison
- meilleur horizon (H20/H40/H60/H90)
- meilleure cible (premium / drawdown / direction)
- seuil basis adapté train-only
- meilleur modèle (LogReg, HistGB, Ridge, LGBM)
- ablation par famille features
- top20/top40 par saison
- backtest research-only train-only seuils

### Méta-modèle saisonnier
```
score(t) = w_season(t) × score_season(t) + (1 - w_season(t)) × score_baseline(t)
```
où `w_season` est calibré OOF.

### Audit (étape obligatoire avant V8)
- Vérifier que V7 seasonal_expert/top20 (AUC 0.98, n=68) utilise des seuils **strictement train-only**. Si non → corriger et republier.

### Livrables
- `artefacts/v8/seasonal_experts_v3.json`
- Mise à jour `docs/EMA_SEASONAL_PREMIUM_REGIMES.md`.

---

## G. ROLL-AWARE PREMIUM FILTERS — `V8-ROLL-FILTERS-V3`

### Filtres testés
- Dur : DTE < {10, 15, 20, 30, 45} jours = no signal
- Dur : fenêtre [-5j, +3j] autour roll estimé = no signal
- Continu : `roll_risk = f(DTE, gap_historique_moyen, vol_récente)`
- Continu : `expected_roll_gap_eur` = gap moyen estimé
- Modèles séparés par période (near_roll, mid_expiry, far_expiry)

### Métriques
- Delta AUC baseline → filtré
- % erreurs `ROLL_ARTIFACT` (V7-14 taxonomy) avant/après
- PnL backtest avec/sans filtre
- Nombre trades restants

### Livrables
- `artefacts/v8/roll_aware_premium_v3.json`

---

## H. FAIR VALUE MODEL EMA — `V8-FAIR-VALUE-V3`

### Modèle
```
EMA_fair(t) = CBOT_EUR(t) + α_FX × ΔFX(t) + α_freight × freight_proxy(t)
            + α_stocks × EU_stocks_z(t) + α_ukraine × Ukraine_risk(t)
            + α_season × season(t) + α_energy × TTF_z(t)
            + α_logistic × logistic_premium(t)
```

### Études
- `EMA - EMA_fair` mean reversion (demi-vie, AR(1))
- Capacité à prédire return relatif H40/H90
- Capacité à expliquer basis_z (R²)
- Comparaison avec basis_z nu (qui est plus utile ?)

### Position dans le rapport
V7-32 avait conclu NO_GO comme **prédicteur OOF**. V8 doit clarifier : NO_GO prédictif, MAIS gardé comme **descriptif explicatif** dans le rapport. Le fair value n'est pas un signal — c'est un cadre.

### Livrables
- `artefacts/v8/fair_value_v3.json`

---

## I. DISTRIBUTIONAL FORECASTING — `V8-DISTRIB-V3`

### Cibles
- `quantile_rel_return_h40 / h90`
- `quantile_basis_change_h20 / h40`
- `CQR_premium_h40 / h90`
- `expected_shortfall_5pct`
- `prob_move_gt_2pct / 3pct / 5pct`

### Méthodes
- LGBMRegressor `objective="quantile"` τ ∈ {0.05, 0.25, 0.50, 0.75, 0.95}
- Conformal quantile regression (CQR) sur calibration set
- Comparaison classif binaire vs quantile τ=0.5 pour `large_outperform_h40`

### Position dans le rapport
V7-35 = POORLY_CALIBRATED. V8 doit dégager si le mauvais résultat vient de :
- Cible mal choisie (return EMA brut au lieu du spread relatif)
- Pas assez de données
- Approche LGBM quantile mal adaptée

Hypothèse V8 H36 : la CQR sur le **spread relatif** est mieux calibrée.

### Livrables
- `artefacts/v8/distributional_v3.json`

---

## J. EVENT STUDY PREMIUM V3 — `V8-EVENT-STUDY-V3`

### Événements étendus (par rapport à V7-10)
| Événement | Fréquence | Source |
|---|---|---|
| WASDE positive/negative stocks | mensuel | USDA |
| EC MARS yield revision | mensuel | JRC |
| FranceAgriMer bilan révision | mensuel | FAM |
| Ukraine corridor open/close | événementiel | press |
| Ukraine production revision | mensuel | USDA FAS |
| Météo extrême EU >35°C ≥3j | quotidien | open-meteo |
| Météo extrême US heat stress | quotidien | NOAA |
| COT extrême long/short percentile90 | hebdo | CFTC |
| EUR/USD shock >1.5% | quotidien | FRED |
| TTF spike ±20% en 1 semaine | hebdo | yfinance |

### Sorties
- abnormal_return_cumul_h5/h20/h40
- basis_response_h5/h20/h40
- volatility_spike_ratio
- hit_rate_post_event
- post_event_AUC

### Livrables
- `artefacts/v8/event_study_v3.json`

---

## K. CAUSALITY & LEAD-LAG V3 — `V8-CAUSALITY-V3`

### Méthodes
1. **Granger bi-directionnel** OOF + correction BH par famille (8 variables × 2 directions = 16 tests).
2. **PCMCI** via `tigramite` (à installer) — graphe causal complet.
3. **Variables instrumentales** sur WASDE (instrument = date publication).
4. **Régression discontinuité** sur seuil basis_z > 2σ.
5. **Conditionnel par régime** et par saison (V8-BASIS-REGIME-V3 × V8-SEASONAL-V3).

### Position V8
V7-18 a fallback Granger bivarié sans BH. V8 doit (a) installer tigramite, (b) corriger BH, (c) tester par sous-période (pré-2020, 2020+2022 crise, 2023+).

### Livrables
- `artefacts/v8/causality_v3.json`
- Graphe DAG dans `docs/V8_CAUSALITY_GRAPH.md`

---

## L. DATA QUALITY SCORE V3 — `V8-DQ-V3`

### Dimensions du score
- **coverage** : % non-NaN sur fenêtre 60j
- **official_source** : flag 0/1 (proxy vs officiel)
- **proxy_flag** : si proxy, qualité de la corrélation officiel/proxy
- **missingness** : run-length max
- **liquidity** : OI relative / spread proxy
- **roll_risk** : DTE + expected_gap
- **publication_lag_confidence** : 1 - lag_jours / 90j

### Usage
- Filtre dur si DQ < 0.4 → pas de signal
- Feature continu pour P(correct)
- Facteur explicatif dans rapport
- Pondération signal × DQ dans backtest

### Livrables
- `artefacts/v8/data_quality_v3.json`

---

## M. P(CORRECT) V3 — `V8-PCORRECT-V3`

### Cible meta
```
correct(t) = 1 si pred_premium_h40(t) ∈ bonne direction
correct(t) = 0 sinon
```
Calculé **OOF strict** sur les prédictions OOF du meta-model V8.

### Features
- probabilité modèle OOF
- basis_z, basis_extreme_flag
- saison
- roll_risk_score
- volatilité_récente 20j
- agreement H40/H90
- entropy distribution
- DQ_score
- event_proximity (jours avant prochain WASDE/MARS)
- jours_dans_regime
- regime_change_score
- n_models_agree
- rolling success rate 30j

### Calibration
- Platt scaling
- Isotonic regression
- ECE par décile
- Brier score

### Validation
- ECE < 0.05
- Brier inférieur sans P(correct)
- top20 P(correct) DA ≥ top20 modèle + 2 pts
- AUC P(correct) > 0.60

### Usage
- `signal_final = signal_premium × P(correct)`
- abstention si P(correct) < 0.45
- signal_fort si P(correct) > 0.65 ET signal > 0.60

### Livrables
- `artefacts/v8/p_correct_v3.json`

---

## N. BACKTESTS RESEARCH-ONLY V3 — `V8-BACKTEST-V3`

### Familles
| Famille | Cible | Horizon | Univers |
|---|---|---|---|
| CBOT long/flat | `y_up_h60` | H60 | CBOT direction |
| CBOT long/short | `y_up_h60` | H60 | CBOT direction |
| EMA/CBOT relative spread | `y_rel_outperform_h40` | H40 | spread |
| Premium indicator | meta_model V8 | H40, H90 | premium |
| Basis rule (z > 1.5) | rule | H40 | basis |
| Season expert | rule saisonnier | H40 | saison |
| Meta model | V8 stacking | H40, H90 | full |
| P(correct) filtré | meta × Pcorrect | H40, H90 | full |
| Roll-aware | meta + filtres | H40, H90 | full |

### Protocole strict
1. Signal vendredi.
2. Entrée lundi ouverture (slippage modélisé).
3. Sortie après H jours.
4. Seuil percentile70/80 train-only.
5. Non-overlap strict ≥ H jours entre trades.
6. No trade si vol > 2σ historique.
7. Coûts 1/2/3/5/8 €/t.
8. Slippage 1/2 €/t.

### Métriques exigées (toutes)
- n_trades, coverage, hit_rate, PnL_total, PnL_mean, PnL par année, max DD, max losing streak, profit factor, Sortino, Calmar, rolling 12m PnL, worst trade, sensibilité coût.

### Verdict toujours `RESEARCH_ONLY_NOT_TRADING`.

### Position V8
V7-13 best `full_signal` PF 3.44 mais hit 33.9% — résultats suspects. V8 doit (a) appliquer stress coûts 5/8, (b) tester leave-one-year-out, (c) tester rolling 12m, (d) comparer règle simple vs meta.

### Livrables
- `artefacts/v8/backtests_v3.json`
- Tables annuelles dans `docs/V8_BACKTESTS_V3.md`

---

## PHASE A — CONSOLIDATION MÉTHODOLOGIQUE (DOIT TERMINER AVANT B–N)

### A.1 `V8-INFRA-HOLDOUT`
Créer `artefacts/v8/holdout_lock.json` :
```json
{
  "lock_date": "2026-05-30",
  "holdout_range": ["2024-01-01", "2024-12-31"],
  "dataset_hash": "<sha256>",
  "dataset_path": "data/processed/features.parquet",
  "n_rows_train_excl_holdout": 0,
  "n_rows_holdout": 0,
  "signature_human": "claude-v8-setup"
}
```
Plus assertion dans tous les modules V8 : `assert not (date in holdout_range)`.

### A.2 `V8-REGISTRY-MERGE`
Fusionner `artefacts/experiments/experiment_registry_v6.csv` et `artefacts/registry/experiments.jsonl` en `artefacts/registry/experiments_unified.jsonl`. Garantir unicité `experiment_id`, garder `dataset_version` distinct.

### A.3 `V8-MT-BH-GLOBAL`
Bilan global FDR par famille :
- Famille CBOT (cibles drawdown/rally/large move)
- Famille EMA premium (H10/H20/H40/H60/H90/H120)
- Famille basis_extreme
- Famille seasonal
- Famille cross-market
- Famille distributional
Bootstrap p-values DA et top20 (5000 itérations) ; AUC via DeLong. BH par famille à α=0.05.

### A.4 `V8-RED-TEAM-PREMIUM`
Pour chaque résultat FRAGILE ou SUSPECT (V8 reflection §6) :
- Permutation des labels (1000 fois, distribution AUC)
- Shuffle dates 7j (rupture corrélation temporelle locale)
- Perturbation seuils ±10%
- Holdout temporel synthétique (mask 6 mois aléatoires)
Verdict : `RED_TEAM_PASS` si AUC empirique > p95 distribution permutation, `RED_TEAM_FAIL` sinon.

### A.5 `V8-CALIBRATION-PLATT-ISO`
Platt vs Isotonic sur premium H40/H90 et CBOT H20/H60. Reporter ECE, Brier, reliability diagram. Choisir le mieux calibré pour V8-PCORRECT-V3.

---

## PHASE B — REVALIDATION V6 (CRITIQUE)

### B.1 `V8-META-REVALIDATION`
Voir `docs/RECHERCHE_MAIS_REFLEXION_PRO_V8.md §13` pour le détail complet.

Résumé :
- 4 cibles : `y_rel_outperform_h40/h90`, `y_rel_outperform_when_basis_extreme_h40/h90`
- 8 combinaisons (classic / meta / classic+meta / basis_rule / season_rule / combo3 / combo4 / full)
- 8 protocoles (V6, embargo H, embargo 2H, LOCY, non-overlap, no-crisis, no-roll, proxy-safe)
- Verdict ∈ {ROBUST / USEFUL_BUT_OVERSTATED / FRAGILE / OVERFIT_OR_LEAKAGE / NO_GO}

### B.2 `V8-CROSS-TARGET-V3`
Voir §C plus haut.

---

## PHASES C–H — EXTENSION ET RAPPORTS

Voir sections A–N pour la cartographie complète. Ordre d'exécution :

```
Sprint 1 :  A.1, A.2, A.3, A.5
Sprint 2 :  A.4, B.1                    (en parallèle)
Sprint 3 :  B.2, V8-CBOT-LAB-PLUS, V8-EMA-PREMIUM-LAB-PLUS
Sprint 4 :  V8-EXPERTS-OOF, V8-META-FEATURES-V3, V8-BASIS-REGIME-V3, V8-SEASONAL-V3
Sprint 5 :  V8-ROLL-FILTERS-V3, V8-DQ-V3, V8-FAIR-VALUE-V3 (audit descriptif)
Sprint 6 :  V8-DISTRIB-V3, V8-EVENT-STUDY-V3, V8-CAUSALITY-V3
Sprint 7 :  V8-PCORRECT-V3, V8-BACKTEST-V3
Sprint 8 :  Synthèse V8 + DECISION_RECHERCHE_MAIS_V8 (update) + INDICATOR-DESIGN-V2 + BOT-PAPER-DESIGN
```

---

## CRITÈRES DE FIN DE V8

V8 est terminé quand :

1. Tous les tickets V8-INFRA et V8-Phase A DONE.
2. V8-META-REVALIDATION conclu (verdict écrit).
3. ≥ 80% des tickets V8-Phase B–G DONE.
4. Tous les pics FRAGILE ont passé V8-RED-TEAM (PASS/FAIL connus).
5. V8-BACKTEST-V3 livré avec stress test coûts 5/8 €/t.
6. `docs/DECISION_RECHERCHE_MAIS_V8.md` mis à jour avec conclusion finale.

Si tous PASS → `RESEARCH_COMPLETE_INDICATOR_DESIGN_READY` (mais toujours `RESEARCH_ONLY_NOT_TRADING`).

Si meta-model V6 ne survit pas → `RESEARCH_DEEPER` et nouvelle phase V9 à cadrer.

---

## CE QUE V8 NE FAIT PAS

- V8 ne code pas l'indicateur final.
- V8 ne code pas le bot.
- V8 ne touche pas le holdout 2024.
- V8 ne fait pas de modifications dans `notebooks/`.
- V8 ne supprime aucun artefact V0–V7.

---

*Document V8 — roadmap expériences — 2026-05-30.*
