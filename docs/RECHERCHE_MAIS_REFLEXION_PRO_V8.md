# RECHERCHE MAIS — RÉFLEXION V8 (NIVEAU CHERCHEUR SENIOR)

**Auteur** : Étude Mais, document de cadrage V8 produit après audit complet V0→V7.
**Date** : 2026-05-30.
**Statut global** : `RESEARCH_ONLY_NOT_TRADING`.
**Source EMA** : `barchart_proxy_exploratory`, MAE proxy/officiel ≈ 37 €/t, verdict source `PROXY_FORBIDDEN` pour usage benchmark décisionnel — toléré uniquement en study/research.

---

## 1. Résumé exécutif

L'étude a accumulé 38 tickets V7 DONE, 32 artefacts JSON, 8 grands rapports docs/EMA_*, un meta-model premium V6 affichant `AUC=0.937` sur `y_rel_outperform_h90` (n=503), et un cross-target stacking V7 strict NO_GO (`AUC=0.5454`). Ce gap apparent V6/V7 doit être désamorcé : **les deux artefacts ne portent pas sur la même cible** (V6 = premium relatif H90, V7-03 = direction CBOT H20 par fallback) et n'utilisent pas le même protocole (V6 = walk-forward classique seul-niveau, V7-03 = nested leave-one-crop-year embargo 90j). Le NO_GO V7-03 ne réfute pas V6 ; il ouvre seulement la question : `que devient V6 sous protocole V7 ?`. Cette question est centrale pour V8 et porte le ticket `V8-META-REVALIDATION`.

Hors cette dette, l'étude V7 a confirmé :

- CBOT est le moteur mondial du maïs ; sa direction brute reste modeste (DA≈62%, AUC≈67.5% J+60).
- Les cibles CBOT spécialisées (drawdown 5%, large_down 3%) sont plus prédictibles (AUC 0.70–0.75).
- EMA direction absolue est `NO_GO` (AUC≈0.50).
- La performance relative EMA/CBOT est le cœur exploitable (V6 H40 AUC≈0.71–0.78, H90 AUC≈0.77–0.93).
- Le basis EMA/CBOT est cointégré (Engle-Granger p≈7e-7) avec demi-vie ≈22.8j et AR(1) φ≈0.97.
- Les régimes de basis extrêmes filtrent un sous-ensemble très prédictible mais à très faible support (n=29–91).
- La saisonnalité expert (politique `seasonal_expert/top20`) donne `AUC≈0.98` à n=68 — pic local probablement sur-estimé.
- Causalité CBOT↔EMA : bidirectionnelle (V7-18 Granger fallback), avec contemporanéité dominante (corr 1-day ≈0.34, corr de niveau ≈0.94).

Et il a documenté des faiblesses :

- Distributional forecast `POORLY_CALIBRATED`.
- Fair value EMA `NO_GO` comme prédicteur de premium.
- Modèle nested stacking V7-03 mal cadré (cible fallback).
- Holdout 2024 non verrouillé physiquement (pas de `holdout_lock.json` sur disque).
- Registre V6/V7 dispersé (CSV V6 séparé + JSONL V7).
- Aucun artefact dédié à une `red team` formelle.
- Aucun artefact dédié à un test de multiplicité global (BH corrections existent mais pas de bilan FDR par famille).

L'objectif de V8 est de **consolider l'étude scientifiquement** avant tout passage en indicateur ou bot, en :

1. Revalidant le meta-model V6 sous protocole V7 strict ;
2. Étoffant les cibles et les experts (CBOT Lab, EMA Premium Lab, Cross-Target Stacking économique) ;
3. Renforçant les filtres économiques (basis, saison, roll, FX, data quality) ;
4. Construisant une vraie chaîne `P(correct)` calibrée ;
5. Préparant l'architecture future hybride sans la coder.

---

## 2. Thèse actuelle (V7) — encore confirmée ?

| Élément de la thèse | Confirmé V7 ? | Force du signal | Risque révision |
|---|---|---|---|
| CBOT = moteur mondial | OUI | Modeste mais réel (DA 62%) | Faible |
| EMA = prix européen avec drivers spécifiques | OUI | Décomposition cohérente | Faible |
| EMA absolu non prédictible | OUI | AUC 0.50–0.53 | Faible |
| Basis EMA/CBOT = prime européenne mesurable | OUI | Cointégration robuste | Faible |
| Performance relative EMA/CBOT plus prédictible | OUI | V6 H40 AUC 0.77, H90 0.93 | **MOYEN** — protocole non strict |
| Basis extrême + saison + filtres roll = boost | OUI | V6 seasonal top20 AUC 0.98 | **ÉLEVÉ** — n=68, sur-optimisation |
| Règles économiques simples robustes contre ML | À TESTER | Pas encore comparé formellement | — |
| Indicateur futur = hybride CBOT + premium + basis + saison + roll + DQ + abstention | OUI | Architecture V7-28 prête | — |

**Verdict** : la thèse est **confirmée dans sa structure** (modèle structurel `P_EMA = P_CBOT × S + Basis + ε_EU`), mais **fragilisée localement** sur deux points : (a) le delta V6 vs V7-03 doit être résolu — pas par interprétation, par re-test ; (b) les pics extrêmes (basis_extreme H90 AUC 1.0 n=29, seasonal_expert/top20 AUC 0.98 n=68) doivent être marqués `FRAGILE` partout dans les rapports tant que red team n'a pas été menée.

---

## 3. Ce qui est VALIDÉ

Critères : OOF strict, n ≥ 200, AUC supérieur au benchmark naïf de ≥ 5 points, pas de leakage suspect détecté, plusieurs protocoles concordants.

| Résultat | n | Métriques | Source(s) |
|---|---:|---|---|
| CBOT J+60 direction (Hist Gradient Boosting) | ≥1000 | DA 62.4%, AUC 67.5%, DA hebdo 61.6% | `docs/PROFESSIONAL_STUDY_REPORT.md`, V6 canonical |
| EMA/CBOT cointégration | 3082 | EG p≈7.3e-7, demi-life 22.8j, AR(1) φ≈0.97 | `artefacts/ema_study/ema_cbot_relationship.json` |
| EMA direction absolue = NO_GO | 2023+ | DA 0.467, AUC 0.502 | `EXP-BENCH-02`, `VAL-EMA-02` |
| Basis mean reversion confirmé | 339 (high+low) | reversion 70% (high), 68% (low) | `artefacts/ema_study/ema_basis_study.json` |
| Causalité contemporaine EMA↔CBOT dominante | 3082 | corr returns 0.34, lead-lag mostly_contemporaneous | `EMA_CBOT_RELATIONSHIP.md` |
| Premium relatif H40 classic seul | 503 | AUC 0.768, top20 0.80, MCC 0.50 | `meta_model_premium_v6.json` |
| Inter-commodity spreads computed | — | 4–6 spreads documentés | `inter_commodity.json` |
| Source EMA proxy non utilisable en benchmark | 3078 overlap | spread 2σ sur 68.97%, MAE 37 €/t | `proxy_vs_real_ema_report.json` |
| Holdout 2024 réservé (déclaratif) | — | `holdout_used: false` partout dans V7 | `final_indicator_v7.json` |

---

## 4. Ce qui est PROMETTEUR mais FRAGILE

Critères : signal très fort mais l'un des éléments suivants : n petit, protocole non strict, sur-optimisation possible, support saisonnier étroit, peu de folds OOF, source proxy.

| Résultat | n | Métriques | Risque |
|---|---:|---|---|
| Premium meta-model H90 classic_plus_meta | 503 | AUC 0.937, BA 0.854, top20 0.97, ECE 0.121 | Protocole V6 (walk-forward simple) non revalidé en nested ; meta-features `pred_*_oof` peuvent contenir un leakage subtil si la fenêtre OOF interne déborde sur l'extérieur ; **REVALIDATION V8 PRIORITAIRE** |
| Basis extreme H40/H90 | 65/29 | AUC 0.95/1.00 | n ridiculement faible. AUC=1.0 sur n=29 = bruit pur en termes statistiques. Marquer FRAGILE partout, ne jamais citer comme preuve. |
| Seasonal expert top20 | 68 | DA 98.5%, AUC 0.98 | Top20 = 13.5% des dates de la saison ; calibré in-sample probablement ; tester train-only avec walk-forward strict. |
| Roll-aware backtest top40_no_roll | 9 trades | +179.65 €/t (cost 1) à +53.65 (cost 8) | 9 trades = anecdote, pas une preuve. Pas tradable. |
| Premium H40 classic_plus_meta gain | 503 | +0.015 AUC vs classic, +0.04 top20 | Gain réel mais modeste ; à confirmer en nested. |
| Cross-market `EMA_ADDS_TO_CBOT` (V7-05) | — | verdict positif | Métrique exacte du gain à publier ; régressions à tester sur cibles spécialisées CBOT (drawdown, rally). |
| CBOT drawdown 5pct H20/H60 | — | AUC 0.75/0.72, top20 0.89/0.92 | Calibrés sur les classes minoritaires ; à stress-tester via leave-one-year-out. |
| Backtest V7-13 best `full_signal` | 59 trades | hit 33.9%, PnL +47.57 €/t, PF 3.44 | DA hit < 50% ; PnL positif vient de l'asymétrie pertes/gains ; à stress-tester avec coûts 5/8 €/t et slippage. |

---

## 5. Ce qui est REJETÉ (NO_GO documentés)

Critères : OOF strict appliqué, plusieurs tentatives échouées, signal ≤ baseline naïf.

| Cible / module | Verdict | Source |
|---|---|---|
| EMA direction absolue H20/H40 (`y_up_h20_ema`, `y_up_h40_ema`) | NO_GO | EXP-BENCH-02, VAL-EMA-02 |
| Stockage économique EMA | NO_GO | `ema_storage_economic_study.json` |
| CQR prix EMA absolu | NO_GO (cover 80%/88% target) | `ema_price_cqr_study.json` |
| Fair value EMA `EMA - EMA_fair` comme prédicteur premium | NO_GO | `fair_value_model.json` |
| Distributional forecast premium | POORLY_CALIBRATED | `distributional_forecast.json` |
| Cross-target stacking V7-03 sur `y_up_h20` (fallback) | NO_GO (AUC 0.5454) | `cross_target_stacking_v2.json` — **note** : pas la bonne cible, fallback automatique |
| Storage EMA classifier `STORAGE_NO_GO` | NO_GO | `EXP-BENCH-04`, `storage_benchmark_ema.json` |
| Granger fedfunds → premium (rejeté OOF) | NO_GO en OOF | feedback_phase2_ema_wording memory |

---

## 6. Ce qui est SUSPECT ou doit être AUDITÉ

Critères : pic de signal sans explication économique stable, protocole partiellement strict, dépendance à une fenêtre temporelle particulière, métriques discordantes selon angles.

1. **Meta-model V6 H90 AUC 0.937** — voir §4. Protocole walk-forward classique sur 503 obs ; le saut V5→V6 vient des meta-features `pred_*_oof`. Suspect tant que `V8-META-REVALIDATION` n'a pas conclu.
2. **Basis_extreme_h90 AUC=1.0 (n=29)** — statistiquement bruit. À retirer des conclusions ou marquer FRAGILE explicit.
3. **Seasonal expert AUC=0.98 (n=68)** — vérifier que les seuils top20 sont strictement train-only, et que le découpage walk-forward est respecté à l'intérieur de chaque saison.
4. **V7-03 NESTED STACKING fallback sur `y_up_h20`** — incohérent avec son intention (V6 ciblait `y_rel_outperform_h90`). Ré-exécuter V7-03 avec les bonnes cibles présentes dans `df` (ce qui suppose un runner qui construit `y_rel_outperform_*` explicitement).
5. **Holdout 2024 — pas de verrouillage physique** — `final_indicator_v7.json` affirme `holdout_used: false` mais aucun fichier `holdout_lock.json` n'existe sur disque. À créer comme dispositif réel (`{date: 2026-05-30, holdout_range: 2024-01-01..2024-12-31, hash_dataset: ..., signature_human: ...}`).
6. **Registre V6/V7 fragmenté** — `experiments/experiment_registry_v6.csv` (V6) + `registry/experiments.jsonl` (V7 = 36 entrées) ne sont pas reliés. Unifier (V8-INFRA).
7. **Causality V7-18 Granger fallback** — `tigramite` non installé donc PCMCI non testé. Granger bivariée sans correction de multiplicité est faible. À renforcer avec BH ou Bonferroni inter-variables.
8. **Backtests V7-13 (best PnL +47.57 €/t, hit 33.9%)** — peu de trades (59), pas de stress-test coûts 5/8 €/t publié, max DD -3.5 mais top10 max DD -18.63 → instabilité.
9. **V7-12 P(correct)** — calibration faite, mais on n'a pas vu de comparaison `signal × P(correct)` vs `signal seul` sur backtest research-only ; à publier.
10. **V7-32 fair value NO_GO** — la fair value comme prédicteur de premium est NO_GO, mais comme **explicateur** descriptif elle peut rester utile. Distinguer dans le rapport.

---

## 7. Découvertes principales

1. **Le basis cointègre fortement EMA/CBOT** avec demi-vie ≈ 23 jours — durée idéale pour signaux H20–H40.
2. **Le delta V5→V6 (AUC 0.77 → 0.94)** est attribuable aux `meta-features OOF` (predicted_*_oof). Sans elles, classic seul reste à 0.77. Le gain est concentré sur H90 et sur le sous-régime basis extrême.
3. **La direction CBOT brute (y_up_h20) ne profite pas d'un meta-stacking** : V7-03 a fait NO_GO précisément parce que le signal CBOT seul est déjà près du plafond (AUC 0.647) — ajouter un autre apprenant EMA H20 ne fait que diluer.
4. **EMA aide CBOT plus que l'inverse** (V7-05 `EMA_ADDS_TO_CBOT`) — signal contre-intuitif : le marché européen, plus petit, contient localement de l'information avancée pour certains horizons.
5. **La fair value structurelle (CBOT_EUR + FX + freight + EU stocks + Ukraine + season + energy)** n'est PAS un prédicteur OOF de la prime EMA/CBOT. Elle reste un cadre explicatif descriptif.
6. **Les régimes de basis sont identifiables** (V7-08, 6 régimes documentés, dominant=NORMAL), mais leur valeur prédictive conditionnelle n'a pas été comparée systématiquement à la règle z-score nue.
7. **L'OI et la liquidité EMA** ne sont pas encore traités comme prédicteur direct (V7-16 microstructure features livré mais pas exploité comme filtre).
8. **Pas de feature stable** — la stabilité top20 (V7-37) montre que `corn_dist_to_52w_high` est la plus stable, ce qui suggère que la régularité est dans la structure de prix, pas dans les fondamentaux mesurés.
9. **Le modèle décroît rapidement** (V7-38 decay) — recommandation : re-entraîner tous les 30 jours. C'est court, et suggère que le modèle apprend du bruit autant que du signal.

---

## 8. Limites méthodologiques

| # | Limite | Conséquence | Mitigation V8 |
|---|---|---|---|
| 1 | Walk-forward V6 non nested | AUC V6 possiblement gonflée pour les meta-features | `V8-META-REVALIDATION` |
| 2 | Aucun `holdout_lock.json` physique | Verrouillage du holdout 2024 = déclaratif uniquement | `V8-INFRA-HOLDOUT` |
| 3 | Multiplicité non corrigée | Risque FDR élevé (plusieurs cibles × horizons × protocoles) | `V8-MT-BH-GLOBAL` |
| 4 | Pas de red team formelle | Pas de garantie que les pics extrêmes survivent à des chocs | `V8-RED-TEAM-PREMIUM` |
| 5 | Cross-target stacking V7-03 mal câblé | NO_GO faussement attribué au stacking | `V8-META-REVALIDATION` couvre |
| 6 | Granger sans BH | Faux positifs causalité | `V8-CAUSALITY-BH` |
| 7 | Calibration ECE 0.12+ | Probabilités non utilisables telles quelles | `V8-CALIBRATION-PLATT-ISO` |
| 8 | Registre V6/V7 fragmenté | Pas de vue unique | `V8-REGISTRY-MERGE` |
| 9 | Pas d'évaluation rolling 12m du backtest | Stabilité année par année non vérifiée | `V8-BACKTEST-ROLLING-12M` |
| 10 | Cibles basis-extreme à n<50 | Bruit statistique pris pour preuve | Marquer FRAGILE partout, exiger n≥200 pour `VALIDATED` |

---

## 9. Limites data

| # | Limite | Conséquence | Mitigation |
|---|---|---|---|
| 1 | EMA = proxy Barchart | Tout résultat EMA est research-only | Acquisition Euronext NextHistory / Refinitiv (`V7-01B`, déjà WAITING_DATA) |
| 2 | Pas d'EC MARS automatisé | Drivers EU yield manquants | `V7-11A` WAITING_DATA |
| 3 | Pas de FranceAgriMer en flux | Bilans EU manquants | `V7-11B` WAITING_DATA |
| 4 | Pas d'Eurostat COMEXT en flux | Flux import/export EU absents | `V7-11C` WAITING_DATA |
| 5 | Pas d'Ukraine flux export en quasi-temps réel | Risque corridor mal modélisé | `V7-11D` |
| 6 | Pas de météo EU pondérée par production | Risque rendement mal capté | `V7-11E` |
| 7 | Pas de prix FOB Bordeaux/Ukraine systématiques | Parité d'export non testable | `V7-11F` |
| 8 | Pas d'historique TTF/CO2/engrais long | Coûts intrants mal pris en compte | `V7-11G` |
| 9 | FAS API key absente | `export_sales_mt` NaN | `ETUDE-09` réactiver |
| 10 | COT NaN pré-2013 | Granger early-period biaisé | Documenté `ETUDE-14`, OK |

---

## 10. Prochaines hypothèses à tester (V8)

H21–H40 — extensions des H1–H20 du roadmap V7 :

| # | Hypothèse | Cible / variable | Méthode | Priorité |
|---|---|---|---|---|
| H21 | Meta-model V6 conserve AUC ≥ 0.85 en nested walk-forward + embargo 2H | `y_rel_outperform_h90` | nested LOCY embargo 90/180j | **CRITIQUE** |
| H22 | Top20 confidence rule reste DA ≥ 85% avec seuils train-only stricts | premium H40/H90 | rolling threshold OOF | HAUTE |
| H23 | CBOT drawdown 5% H20 est robuste à leave-one-year-out | `y_cbot_drawdown_5pct_h20` | LOYO | HAUTE |
| H24 | OI EMA + bid-ask proxy filtrent les FP du modèle premium | erreurs V7-14 | filtre liquidité | HAUTE |
| H25 | Saisonnier expert nov-déc reste signifiant à H40 sous BH | premium H40 | seasonal OOF | HAUTE |
| H26 | Le ratio maïs/blé EU est plus prédictif du premium que le ratio US | `premium_h40` | corrélation, OOF | MOYENNE |
| H27 | Le triple-barrier ±3% sur EMA/CBOT spread donne un signal plus net | spread relatif | triple barrier | MOYENNE |
| H28 | La règle simple `basis_z > 1.5` bat le meta-model en backtest avec coût 5 €/t | backtest | comparaison directe | **CRITIQUE** |
| H29 | P(correct) > 0.65 améliore le PnL net après coûts | backtest | filtration | HAUTE |
| H30 | Le delta CBOT→EMA s'inverse selon le régime (V7-08) | direction | interactions × régime | MOYENNE |
| H31 | Le quantile τ=0.5 quantile-LGBM bat un modèle classification pour `large_outperform_h40` | quantile vs classif | comparaison | MOYENNE |
| H32 | Les erreurs `ROLL_ARTIFACT` (V7-14) disparaissent avec filtre DTE < 20 | erreurs | ablation | HAUTE |
| H33 | EMA → CBOT survit à un Granger BH-corrigé sur 2010–2019 (hors 2020+2022) | lead-lag | Granger OOF + BH | HAUTE |
| H34 | Les top20 confidence rules sont stables entre 2010–2019 vs 2020–2023 | stability | rolling 36m | HAUTE |
| H35 | Les EMA OI changes ont un AUC > 0.55 OOF sur `large_outperform_h40` | microstructure | LGBM OOF | MOYENNE |
| H36 | Un modèle distributionnel CQR sur le spread (pas EMA seul) est mieux calibré | distributional | CQR OOF | MOYENNE |
| H37 | Un modèle Kalman sur (CBOT, EMA, basis) prédit mieux les bêtas t+1 | dynamique | DLM/Kalman | BASSE |
| H38 | La règle économique simple `signal = (basis_z > 1.5) × (season ∈ {nov,dec,jan})` bat le meta-model en stability | combinaison | comparaison | HAUTE |
| H39 | Les divergences `EMA_OI_change × basis_z` prédisent l'expansion vs compression du basis | divergence | classifier OOF | MOYENNE |
| H40 | `P(correct)` calibrée Platt est mieux que isotonique sur le premium H90 | calibration | comparaison | HAUTE |

---

## 11. Plan de recherche détaillé V8 (par phase)

### Phase A — Consolidation méthodologique (BLOQUE tout le reste)

- **V8-INFRA-HOLDOUT** : créer `artefacts/holdout_lock.json` avec hash dataset + range + signature.
- **V8-REGISTRY-MERGE** : unifier `experiments/experiment_registry_v6.csv` et `registry/experiments.jsonl` en `registry/experiments_unified.jsonl`.
- **V8-MT-BH-GLOBAL** : balayer tout le registre, calculer p_values manquantes (DeLong / Hanley-McNeil pour AUC, bootstrap pour top20), appliquer BH par famille (CBOT, EMA premium, basis_extreme, seasonal, cross-market).
- **V8-RED-TEAM-PREMIUM** : injecter chocs (permutation labels, shuffle des dates, perturbation des seuils, holdout temporel synthétique) sur tous les pics flaggés FRAGILE — produire `red_team_report.json`.
- **V8-CALIBRATION-PLATT-ISO** : Platt vs Isotonique sur premium H40/H90 et CBOT H20/H60.

### Phase B — Revalidation V6 (CRITIQUE)

- **V8-META-REVALIDATION** : voir §13.
- **V8-CROSS-TARGET-V3** : reconstruire le cross-target stacking proprement avec présence garantie des cibles `y_rel_outperform_*` dans le dataset (élimination du fallback `y_up_h20`).

### Phase C — Extension target labs

- **V8-CBOT-LAB-PLUS** : triple-barrier ±3% / ±5% sur CBOT, large move conditionnels (stocks tendus, COT extreme, weather stress, post-WASDE).
- **V8-EMA-PREMIUM-LAB-PLUS** : large_outperform / large_underperform / basis_compression / basis_expansion / basis_reversion / basis_continuation H10/H20/H40/H60/H90/H120 ; FX-neutral premium ; fair_value deviation ; residual EU shocks.

### Phase D — Experts et meta-features économiques

- **V8-EXPERTS-OOF** : CBOT direction, CBOT drawdown, CBOT rally, CBOT vol, EMA premium H40/H90, basis_extreme, basis_compression, basis_expansion, basis_regime, seasonal_expert, roll_risk, data_quality, FX_neutral, fair_value_deviation, EU_residual_shock — tous OOF.
- **V8-META-FEATURES-V3** : mean_p, std_p, entropy, H40/H90 agreement, CBOT/EMA disagreement, n_bullish, n_bearish, basis_extreme_flag, roll_warning, dq_warning.

### Phase E — Filtres et régimes

- **V8-BASIS-REGIME-V3** : KMeans + GMM + HMM, validation BIC + silhouette, AUC par régime.
- **V8-SEASONAL-V3** : modèles experts par saison, threshold train-only, walk-forward intra-saison.
- **V8-ROLL-FILTERS-V3** : DTE filters, OI filters, expected_roll_gap_eur, modèle séparé par période roll.
- **V8-DQ-V3** : DQ score complet (coverage, official, proxy, missingness, liquidity, roll, publication lag).

### Phase F — Cross-market et causalité

- **V8-CROSS-MARKET-V3** : ablation systématique EMA→CBOT et CBOT→EMA, par saison, par régime, par horizon.
- **V8-CAUSALITY-V3** : Granger BH-corrigé + PCMCI (installer tigramite), graphe causal final.

### Phase G — Distributional, P(correct), backtests

- **V8-DISTRIB-V3** : CQR sur spread relatif (pas EMA brut), CRPS, expected shortfall.
- **V8-PCORRECT-V3** : Platt vs Iso, comparaison `signal × Pcorrect` vs signal seul en backtest.
- **V8-BACKTEST-V3** : stress test coûts 1/2/3/5/8/12 €/t, slippage 1/2 €/t, rolling 12m PnL, leave-one-year-out PnL, Sortino, Calmar.

### Phase H — Rapport et architecture

- **V8-DECISION** : document de décision V8 (livré au début de la phase pour cadrer, mis à jour après chaque phase).
- **V8-INDICATOR-DESIGN-V2** : architecture hybride détaillée, sans coder.
- **V8-BOT-PAPER-DESIGN** : design d'un journal de signaux + dashboard sans exécution.

---

## 12. Priorités d'exécution

```text
Sprint 1 (semaine 1) — Phase A complète
  V8-INFRA-HOLDOUT  ←  doit être premier
  V8-REGISTRY-MERGE
  V8-MT-BH-GLOBAL
  V8-CALIBRATION-PLATT-ISO

Sprint 2 (semaine 2) — Phase B
  V8-META-REVALIDATION   ←  DÉBLOQUE tout le reste
  V8-CROSS-TARGET-V3
  V8-RED-TEAM-PREMIUM (en parallèle)

Sprint 3 (semaine 3-4) — Phase C + D + E
  V8-CBOT-LAB-PLUS
  V8-EMA-PREMIUM-LAB-PLUS
  V8-EXPERTS-OOF
  V8-META-FEATURES-V3
  V8-BASIS-REGIME-V3 / SEASONAL-V3 / ROLL-FILTERS-V3 / DQ-V3 (en parallèle)

Sprint 4 (semaine 5) — Phase F + G
  V8-CROSS-MARKET-V3
  V8-CAUSALITY-V3
  V8-DISTRIB-V3
  V8-PCORRECT-V3
  V8-BACKTEST-V3

Sprint 5 (semaine 6) — Phase H
  V8-DECISION (update)
  V8-INDICATOR-DESIGN-V2
  V8-BOT-PAPER-DESIGN
```

---

## 13. V8-META-REVALIDATION — détail

### Objectif
Tester rigoureusement si le meta-model V6 (`AUC=0.937` sur `y_rel_outperform_h90`) survit au protocole V7 strict (nested walk-forward, embargo 90j, leave-one-crop-year).

### Cibles
- `y_rel_outperform_h40`
- `y_rel_outperform_h90`
- `y_rel_outperform_when_basis_extreme_h40` (marqué FRAGILE si n_oof < 100)
- `y_rel_outperform_when_basis_extreme_h90` (marqué FRAGILE)

### Combinaisons
1. `classic_only` (features économiques classiques)
2. `meta_only` (OOF predictions de base learners CBOT/EMA)
3. `classic_plus_meta` (V6 winning set)
4. `basis_rule_only` (règle `basis_z > 1.5`)
5. `season_rule_only` (règle saison nov-déc)
6. `classic + basis_rule` (sanity)
7. `classic + season_rule` (sanity)
8. `classic + meta + basis_rule + season_rule` (full stack)

### Protocoles
- A) Walk-forward V6 (reproduction)
- B) Purged CV embargo H (V7-02 standard)
- C) Purged CV embargo 2H (precaution)
- D) Leave-one-crop-year (V7-03 standard)
- E) Non-overlap strict (gap = H entre obs)
- F) No-crisis (exclure 2020 + 2022)
- G) No-roll (exclure DTE < 20)
- H) Proxy-safe period (si V7-01B livre une période officielle)

### Verdicts possibles
| Code | Condition |
|---|---|
| `META_PREMIUM_ROBUST` | AUC moyen ≥ 0.85 sur ≥ 5 protocoles, BH q ≤ 0.05, ECE ≤ 0.10 |
| `META_PREMIUM_USEFUL_BUT_OVERSTATED` | AUC entre 0.70 et 0.85, gain net vs classic ≥ +0.02 AUC |
| `META_PREMIUM_FRAGILE` | AUC > 0.7 mais effondre sous au moins 2 protocoles (perte ≥ 0.10) |
| `META_PREMIUM_LIKELY_OVERFIT_OR_LEAKAGE` | AUC chute > 0.20 sous protocole B/C/D vs A ; gain vs classic disparaît |
| `META_PREMIUM_NO_GO` | AUC < 0.60 sous protocoles stricts |

### Livrables
- `artefacts/v8/meta_revalidation.json`
- `docs/V8_META_REVALIDATION.md`
- Mise à jour `docs/PROFESSIONAL_STUDY_REPORT.md` table d'implémentation.

---

## 14. Risques de leakage

| Risque | Détection actuelle | Action V8 |
|---|---|---|
| Meta-features `pred_*_oof` non strictement OOF | V7-00 audit dit COHERENT mais protocole pas nested | `V8-META-REVALIDATION` |
| Seuils top20 calibrés sur tout l'échantillon | possible dans V6 seasonal_expert | `V8-SEASONAL-V3` re-test |
| Z-scores expanding qui voient le futur | `LEAKAGE-00` test global dit OK | Maintenir ; ajouter assert dans tests `tests/test_v8_anti_leakage.py` |
| Forward-fill de WASDE qui propage futur | partiellement audité | Re-tester sur `data_quality` |
| Cibles basis-extreme construites avec valeur t (pas shift) | possible — vérifier le shift(1) sur basis_z avant comparaison au seuil | Audit code `build_features()` |
| Holdout 2024 réellement réservé | aucun lock physique | `V8-INFRA-HOLDOUT` |

---

## 15. Risques de sur-optimisation

| Risque | Détection | Action V8 |
|---|---|---|
| Multiplicité des cibles × horizons × protocoles | partiellement BH sur V7-02 mais pas global | `V8-MT-BH-GLOBAL` |
| Choix `top20` calibré post-hoc | non documenté formellement | `V8-RULE-TRAIN-ONLY` test |
| Choix `embargo=90j` justifié uniquement par V7-02 best | OK mais à confirmer en stabilité | `V8-EMBARGO-ROBUSTNESS` |
| 30+ règles testées sur même dataset | pas de p-value globale | `V8-MT-BH-GLOBAL` |
| Saisons et régimes choisis a posteriori | économiquement motivés mais formel BH manquant | `V8-MT-BH-FAMILY` |
| Surcharge feature_count (V7 = 80 features dans nested stacking) | risque overfit base learners | Lasso ou ablation |
| Hyper-paramètres optimisés sur train ou OOF ? | non audité | `V8-HYPER-AUDIT` |

---

## 16. Roadmap vers indicateur futur (post-V8)

### Conditions d'éligibilité (préalables)
- Source EMA officielle obtenue ET delta proxy/officiel < 0.05 AUC.
- Meta-model V6 verdict ∈ {ROBUST, USEFUL_BUT_OVERSTATED}.
- BH global publié et signaux retenus avec q ≤ 0.05.
- Red team passée pour tous les pics utilisés.
- Backtest research-only stable rolling 12m sur ≥ 7 ans, PF > 1.3 à coût 5 €/t.
- P(correct) calibrée ECE < 0.05.

### Architecture cible (V7-28 raffinée)

```text
INDICATEUR_V8 (research-only) =
  CBOT_global_module      (direction + drawdown + rally + vol)
  ⊕ EMA_premium_module    (H40, H90)
  ⊕ Basis_regime_module   (V8-BASIS-REGIME-V3)
  ⊕ Seasonal_module       (expert par saison)
  ⊕ Roll_risk_filter      (DTE, OI, expected_gap)
  ⊕ Data_quality_filter   (coverage, source, lag)
  ⊕ Event_risk_filter     (proximity WASDE, MARS, EUR/USD shock)
  ⊕ P(correct)_module     (Platt/Iso)
  ⊕ Abstention_logic
  → Output: {
       global_cbot_signal,
       eu_premium_signal,
       final_research_signal,
       confidence,
       drivers_haussiers,
       drivers_baissiers,
       abstention_reasons,
       horizon_recommandé,
       statut: "RESEARCH_ONLY_NOT_TRADING"
     }
```

### Étapes restantes après V8

1. Acquisition EMA officielle + revalidation (V7-01B).
2. Période proxy-safe contre période officielle : delta AUC.
3. Validation finale sur holdout 2024 (une seule fois, traçabilité totale).
4. Conformité légale + revue indépendante (humaine).
5. Mise en production interne (paper trading uniquement).

---

## 17. Roadmap vers bot paper-trading (research-only)

**Pas avant 6 mois minimum après V8.** Et seulement si V8 conclut `META_PREMIUM_ROBUST` ou équivalent.

Modules minimaux du bot paper :
- Journal de signaux quotidien (CSV/JSONL append-only).
- Simulateur avec coûts 1/2/3/5/8 €/t par leg.
- Suivi quotidien hit-rate / PnL / coverage.
- Monitoring `data_quality_score` < seuil → arrêt automatique.
- Monitoring drift (`pred_distribution_kl` vs train) → alerte.
- Dashboard (Markdown ou HTML simple) : signaux, PnL cumulé, par régime, par saison.
- Logs des erreurs avec tag (V7-14 taxonomy).

Critères avant bot réel (post paper) :
- Paper trading 6–12 mois.
- PnL net stable > +25 €/t/an (rendement net après coûts).
- Hit rate stable > 60%.
- Drawdown max < -20 €/t.
- P(correct) stable ECE < 0.05 en live.
- Validation humaine (revue mensuelle).
- Conformité légale (statut publication/recommandation/produit).

---

## 18. Annexes — pointeurs clés

| Élément | Chemin |
|---|---|
| Roadmap V7 complète | `docs/ROADMAP_ETUDE_MAIS_V7.md` |
| Tickets V7 (52) | `.ai/TICKETS_V7.md` |
| State (continuum projet) | `.ai/STATE.md` |
| V6 meta-model results | `artefacts/v6/meta_model_premium_v6.json`, `docs/META_MODEL_PREMIUM_V6.md` |
| V7 nested stacking | `artefacts/v7/cross_target_stacking_v2.json`, `src/mais/meta/nested_stacking.py` |
| V7 final report | `artefacts/v7/final_report_v7.json`, `docs/FINAL_CORN_STUDY_V7.md` |
| Source EMA audit proxy | `artefacts/proxy_vs_real_ema_report.json`, `docs/EMA_DATA_AUDIT.md` |
| Backtests V7-13 | `artefacts/v7/backtests_v7.json` |
| Registry V6 | `artefacts/experiments/experiment_registry_v6.csv` |
| Registry V7 | `artefacts/registry/experiments.jsonl` (36 entrées) |
| Holdout lock | **MANQUANT** — à créer `artefacts/v8/holdout_lock.json` |
| Multiple testing | `artefacts/v7/bh_corrections.json` partiel, manque vue globale |
| Red team | **MANQUANT** — à créer |

---

## 19. Verdict V8 (cadrage initial — pré-expérience)

**Verdict ouvert.** L'étude V7 a accumulé une masse de signaux dont la robustesse statistique n'est pas garantie. Avant tout claim de "indicateur prêt", V8 doit conclure par écrit sur trois questions :

1. **Le meta-model V6 survit-il au protocole V7 strict ?** → V8-META-REVALIDATION.
2. **Le top20/seasonal expert tient-il en stress test ?** → V8-RED-TEAM-PREMIUM.
3. **Les règles économiques simples (basis_z, saison) battent-elles le ML après coûts ?** → V8-BACKTEST-V3 comparaison directe.

Si les trois réponses sont positives, l'étude entre en `INDICATOR_READY_FOR_PAPER_TRADING_DESIGN`. Sinon, on documente le gap et on revient en `RESEARCH_DEEPER`.

**Aucune décision d'indicateur ou de bot ne sera prise avant la conclusion écrite de V8.**

---

*Document V8 — réflexion initiale produite après audit complet 2026-05-30. À mettre à jour à chaque fin de sprint V8.*
