# Cheminement de l'étude maïs

Légende : [GARDÉ] (résultat exploitable), [ABANDONNÉ] (n'a rien donné), [BLOQUÉ] (données manquantes), [OUTIL] (audit / anti-fuite), [EXPLORATION] (étape de cadrage). Tous les fichiers de l'étude sont rattachés à la question qu'ils ont servi à répondre (aucun oublié). Version interactive (détail au clic) : `artefacts/rapport_etude/arbre_etude.html`.

## Q-DATA : Quelles données gratuites ai-je, et sont-elles PROPRES (anti-fuite) ?
Avant de modéliser quoi que ce soit, il faut savoir ce dont on dispose et si c'est fiable, car un signal calculé sur des données qui 'voient le futur' est faux. On rassemble donc ~12 sources publiques gratuites (CBOT, Euronext, WASDE, Crop Condition, météo, COT, éthanol, macro, exports) et on les AUDITE : dates de publication réelles, fuites éventuelles, artefacts de construction des séries continues. Concrètement on lance des tests d'intégrité, on reconstruit les rapports USDA en version 'vintage' et on vérifie les calendriers.
_34 fichiers :_
- [BLOQUÉ] `test_barchart_ema_probe.py` : barchart ema probe
- [BLOQUÉ] `test_dce_dalian_collector.py` : dce dalian collector
- [BLOQUÉ] `test_euronext_history_probe.py` : Tests VN-C1 - probe historique endpoint Euronext (offline + mock).
- [BLOQUÉ] `test_intraday_aligned_basis.py` : Tests V60-intraday - basis aligné settlement (offline, intraday synthétique).
- [EXPLORATION] `EXT006_roll_method_volume_based` : EXT006 - Roll method volume-based
- [EXPLORATION] `test_asymmetric_module.py` : asymmetric module
- [EXPLORATION] `test_cli_ema.py` : cli ema
- [EXPLORATION] `test_ema_features_pipeline.py` : ema features pipeline
- [EXPLORATION] `test_ema_h90_stress_test.py` : ema h90 stress test
- [EXPLORATION] `test_ema_targets.py` : ema targets
- [EXPLORATION] `test_euronext_daily_collector.py` : euronext daily collector
- [EXPLORATION] `test_euronext_ema_collector.py` : euronext ema collector
- [EXPLORATION] `test_euronext_evening_snapshots.py` : Tests VN-E1 - capture du soir (offline + mock).
- [EXPLORATION] `test_euronext_features.py` : euronext features
- [GARDÉ] `EXT026_wasde_vintage_pipeline` : EXT026 - WASDE vintage pipeline
- [GARDÉ] `test_hierarchical_explanation.py` : Tests VN-D4 - explication hiérarchique par familles.
- [OUTIL] `test_data_quality.py` : data quality
- [OUTIL] `test_data_truth_audit_v159.py` : V159 - pack d'audit de la vérité des données.
- [OUTIL] `test_ema_data_audit.py` : ema data audit
- [OUTIL] `test_ema_data_audit_v2.py` : Tests pour NB-EMA-01 - Audit données EMA v2.
- [OUTIL] `test_ema_data_quality_split.py` : ema data quality split
- [OUTIL] `test_ema_target_integrity.py` : ema target integrity
- [OUTIL] `test_ema_utils.py` : Tests pour UTIL-EMA-01 - Fonctions utilitaires EMA.
- [OUTIL] `test_experiment_registry.py` : Tests V7-INFRA-00 - Registre global des expériences.
- [OUTIL] `test_experiment_registry_v6.py` : experiment registry v6
- [OUTIL] `test_leakage_calendar.py` : leakage calendar
- [OUTIL] `test_leakage_global.py` : V7-LEAKAGE-00 - Suite de tests anti-leakage global.
- [OUTIL] `test_market_calendar.py` : Tests V42-01 - calendrier de marché Euronext.
- [OUTIL] `test_paths_ema.py` : Tests DATA-PATHS-01 - chemins EMA dans paths.py.
- [OUTIL] `test_proxy_audit.py` : proxy audit
- [OUTIL] `test_publication_calendar.py` : Tests V7-DATA-CAL - Calendrier de publication des données.
- [OUTIL] `test_purged_cv.py` : Tests V7-02 - Purged CV avec embargo.
- [OUTIL] `test_roll_audit.py` : roll audit
- [OUTIL] `test_usda_release_calendar.py` : Tests VN-C5 - calendrier de publication USDA (fallback approximation honnête).
Analyse : Ce qu'on retient : une découverte critique - la série WASDE interne exposait ses valeurs ~8 jours AVANT publication (fuite), corrigée par un pipeline 'vintage' daté à la publication ; et la série Euronext brute sautait de ~10 €/t les jours de roll, corrigée par la série ajustée. On en déduit que, ces deux biais corrigés, la base est SAINE et qu'on peut modéliser sans 'voir le futur'. -> Première vraie question : peut-on simplement prédire le prix ?

## Q1 : Peut-on PRÉDIRE le prix exact du maïs ?  (vient de Q-DATA)
Pour savoir si le prix est seulement prévisible, on le confronte aux baselines triviales - random walk ('demain = aujourd'hui'), dérive, dérive saisonnière, prix des futures - sur le prix et le retour, à 4 horizons (5/20/40/90 j), avec un test de Diebold-Mariano. Pourquoi ces baselines : si on ne bat même pas la marche aléatoire, aucun modèle compliqué n'est justifié.
_20 fichiers :_
- [BLOQUÉ] `test_ema_true_curve_benchmark.py` : ema true curve benchmark
- [EXPLORATION] `test_cbot_target_lab.py` : Tests V7-04 - CBOT Target Lab avancé.
- [EXPLORATION] `test_ema_cqr_v2.py` : ema cqr v2
- [EXPLORATION] `test_ema_price_cqr_study.py` : ema price cqr study
- [EXPLORATION] `test_ema_price_forecast.py` : Tests pour NB-EMA-12 - Prévision prix EMA expérimental.
- [EXPLORATION] `test_ema_target_lab_v5.py` : ema target lab v5
- [EXPLORATION] `test_horizon_sweep.py` : horizon sweep
- [EXPLORATION] `test_model_zoo.py` : model zoo
- [EXPLORATION] `test_target_labs_v6.py` : target labs v6
- [EXPLORATION] `test_weekly_da.py` : weekly da
- [OUTIL] `EXT025_random_walk_and_futures_price_benchmark` : EXT025 - Random walk & futures price benchmark
- [OUTIL] `test_benchmark_canonical.py` : benchmark canonical
- [OUTIL] `test_benchmark_suite.py` : Tests V7-31 - Benchmark suite naïf et professionnel.
- [OUTIL] `test_ema_benchmark.py` : ema benchmark
- [OUTIL] `test_ema_direction_benchmark.py` : Tests pour NB-EMA-08 - Benchmark directionnel EMA.
- [OUTIL] `test_ema_direction_benchmarks_v2.py` : ema direction benchmarks v2
- [OUTIL] `test_ema_roll_target_benchmark.py` : ema roll target benchmark
- [OUTIL] `test_ema_smart_baselines.py` : ema smart baselines
- [OUTIL] `test_ema_weekly_benchmark.py` : Tests pour NB-EMA-13 - Benchmark hebdomadaire EMA.
- [OUTIL] `test_storage_benchmark_ema.py` : storage benchmark ema
Analyse : Résultat net : aucun des 36 couples (modèle x horizon) ne bat la random walk au test de Diebold-Mariano (p<0.10). On retient que le PRIX EXACT n'est pas prévisible en RMSE avec ces données - c'est un résultat solide, pas un échec de méthode. On en déduit qu'il faut CHANGER d'objectif : viser la DIRECTION (hausse/baisse) et expliquer la prime européenne via le BASIS, pas le niveau de prix. -> La direction et le basis sont-ils modélisables ?

## Q2 : Peut-on prédire la DIRECTION et expliquer la prime Euronext via le basis ?  (vient de Q1)
Puisque le prix exact échappe, on regarde la relation CBOT<->Euronext : sont-ils liés par un équilibre de long terme (cointégration) ? Peut-on décomposer le retour Euronext en part CBOT + prime locale ? On teste la cointégration de Johansen, la décomposition du retour et l'étude du résidu européen, pour voir si la prime/le basis est modélisable.
_35 fichiers :_
- [EXPLORATION] `test_cbot_cross_market_v6.py` : cbot cross market v6
- [EXPLORATION] `test_cross_target_oof_v6.py` : cross target oof v6
- [EXPLORATION] `test_ema_cbot_cointegration.py` : Tests pour NB-EMA-04 - Relation EMA/CBOT cointégration.
- [EXPLORATION] `test_ema_cbot_relation_v2.py` : ema cbot relation v2
- [EXPLORATION] `test_ema_cbot_relationship.py` : ema cbot relationship
- [EXPLORATION] `test_ema_cross_data_interactions_v5.py` : ema cross data interactions v5
- [EXPLORATION] `test_ema_decomposition.py` : Tests V7-09 - Décomposition dynamique EMA.
- [EXPLORATION] `test_ema_decomposition_v2.py` : ema decomposition v2
- [EXPLORATION] `test_ema_final_report.py` : Tests pour NB-EMA-14 - Rapport de synthèse final.
- [EXPLORATION] `test_ema_final_report_v2.py` : ema final report v2
- [EXPLORATION] `test_ema_final_report_v3.py` : ema final report v3
- [EXPLORATION] `test_ema_final_report_v4.py` : ema final report v4
- [EXPLORATION] `test_ema_final_synthesis_v5.py` : ema final synthesis v5
- [EXPLORATION] `test_ema_premium_signal_compare.py` : ema premium signal compare
- [EXPLORATION] `test_ema_project_overview.py` : Tests pour NB-EMA-00 - Module vue d'ensemble projet.
- [EXPLORATION] `test_ema_relative_backtest.py` : ema relative backtest
- [EXPLORATION] `test_ema_relative_backtest_v2.py` : ema relative backv2
- [EXPLORATION] `test_ema_relative_backtest_v3.py` : ema relative backv3
- [EXPLORATION] `test_ema_relative_error_analysis.py` : ema relative error analysis
- [EXPLORATION] `test_ema_relative_error_archaeology_v2.py` : ema relative error archaeology v2
- [EXPLORATION] `test_ema_relative_seasonality.py` : ema relative seasonality
- [EXPLORATION] `test_ema_relative_study.py` : ema relative study
- [EXPLORATION] `test_ema_residual_eu_v2.py` : ema residual eu v2
- [EXPLORATION] `test_ema_residual_study.py` : Tests pour NB-EMA-06 - Étude du résidu EU.
- [EXPLORATION] `test_ema_return_decomposition.py` : Tests pour NB-EMA-05 - Décomposition retour EMA.
- [EXPLORATION] `test_ema_seasonal_premium_regimes.py` : ema seasonal premium regimes
- [EXPLORATION] `test_final_corn_study_v6.py` : final corn study v6
- [EXPLORATION] `test_phase2_descriptive.py` : Tests V7 Phase 2 - Tickets descriptifs économiques.
- [EXPLORATION] `test_premium_head.py` : Tests VN-A1 - premium head single source of truth (offline, artefacts mockés).
- [EXPLORATION] `test_v21_integration.py` : Tests V21 - intégration indicateur + collecteur météo prévue (fonctions pures).
- [EXPLORATION] `test_v29_premium_risk_path.py` : Tests V29 - exploration C (premium x drawdown) + D (chemin de compression).
- [EXPLORATION] `test_v49_long_premium_leg.py` : Tests V49 - jambe long premium (offline, master synthétique).
- [GARDÉ] `test_ema_hierarchical_cbot_premium_v5.py` : ema hierarchical cbot premium v5
- [GARDÉ] `test_ema_premium_indicator.py` : ema premium indicator
- [GARDÉ] `test_ema_premium_indicator_v2.py` : ema premium indicator v2
Analyse : On retient que CBOT et Euronext sont cointégrés et que la prime se compresse surtout quand le CBOT MONTE (la jambe CBOT pèse ~6x la jambe EMA) ; le résidu purement européen est faible. On en déduit que l'objet exploitable n'est pas le prix Euronext en soi mais le BASIS et sa dynamique. -> Deux questions en découlent : le basis revient-il à la moyenne (Q3) ? qu'est-ce qui l'explique (Q4) ? - plus deux pistes de prédicteurs : météo (Q2b) et positionnement/demande (Q2c).

## Q3 : Le basis revient-il à la moyenne -> signal de vente ?  (vient de Q2)
Si le basis revient à la moyenne, alors 'basis haut' = bon moment pour vendre. On mesure la demi-vie de réversion, on teste une règle 'vendre quand le basis est haut' avec des coûts réalistes et des règles de sortie, et on assemble des indicateurs structurels de vente à paliers.
_31 fichiers :_
- [EXPLORATION] `test_basis_regimes.py` : Tests V7-08 - Régimes de basis EMA/CBOT.
- [EXPLORATION] `test_ema_abstention_filters.py` : ema abstention filters
- [EXPLORATION] `test_ema_basis_formal.py` : Tests pour NB-EMA-07 - Basis formel EMA/CBOT.
- [EXPLORATION] `test_ema_basis_study.py` : ema basis study
- [EXPLORATION] `test_ema_basis_v2.py` : ema basis v2
- [EXPLORATION] `test_ema_storage_economic_study.py` : ema storage economic study
- [EXPLORATION] `test_ema_theoretical_backtests.py` : ema theoretical backtests
- [EXPLORATION] `test_storage_backtest.py` : storage backtest
- [EXPLORATION] `test_v10_market_discovery.py` : Tests V10 - Market Discovery.
- [EXPLORATION] `test_v11_simplified_program.py` : Tests V11 - programme discipliné.
- [EXPLORATION] `test_v167_seasonality.py` : V167 - saisonnalité des départs de compression.
- [EXPLORATION] `test_v18_literature_replication.py` : Tests V18-LIT - réplication littérature.
- [EXPLORATION] `test_v7_phase3_6.py` : Tests V7 Phase 3-6 - Tickets V7-05, V7-27, V7-35, V7-34, V7-37, V7-38, V7-12, V7-14, V7-36, V7-13, V7-15, V7-28.
- [GARDÉ] `test_v12_mean_reversion_lab.py` : Tests V12 - mean-reversion lab, forward validation, conformal abstention, journal.
- [GARDÉ] `test_v131_target_recommendation_v3.py` : Tests V131 - recommandation d'objectif v3 à 4 états.
- [GARDÉ] `test_v132_indicator_synthesis_v3.py` : Tests V132 - synthèse indicateur v3 (offline, artefacts mockés).
- [GARDÉ] `test_v13_basis_reversion.py` : Tests V13 - indicateur mean-reversion du basis.
- [GARDÉ] `test_v149_indicator_multiview.py` : Tests V149 - visuel multi-vues (EMA/CBOT + multi-seuils), synthétique.
- [GARDÉ] `test_v14_short_indicator.py` : Tests V14 - indicateur short-only, survival, robustesse proxy.
- [GARDÉ] `test_v15_short_realism.py` : Tests V15 - réalisme indicateur short basis-haut.
- [GARDÉ] `test_v175_signal_tiers.py` : V175 - paliers de signal (offline, série synthétique). Baseline intouchée.
- [GARDÉ] `test_v176_composite_indicator.py` : V176 - indicateur composite : causalité, variantes, éligibilité, live (offline).
- [GARDÉ] `test_v17_research_indicator.py` : Tests V17 - indicateur research de prime.
- [GARDÉ] `test_v56_target_recommendation.py` : Tests V56 - règle d'objectif recommandé (offline, master synthétique).
- [GARDÉ] `test_v77_indicator_synthesis.py` : Tests V77 - synthèse indicateur (offline, master synthétique).
- [GARDÉ] `test_v83_indicator_visual.py` : Tests V-VISUAL - génération des figures de l'indicateur (offline).
- [GARDÉ] `test_v99_indicator_synthesis_v2.py` : Tests V99 - synthèse indicateur v2 (offline).
- [GARDÉ] `test_v9_structural_indicator.py` : Tests V9 - indicateur structurel hybride.
- [OUTIL] `test_v6_coherence_audit.py` : Tests V7-00 - Audit de cohérence V6.
- [OUTIL] `test_v7_feature_data_quality.py` : Tests V7-39 - Score de qualité des données (features/data_quality.py).
- [OUTIL] `test_v7_new_modules.py` : Tests V7 - Tickets V7-16, V7-21, V7-18, V7-32, V7-33, V7-03.
Analyse : On retient une demi-vie de réversion de 17-47 jours, et qu'une règle 'vendre quand le basis est haut' survit aux coûts (~5 €/t) hors crise (+115), avec un edge concentré sur les extrêmes (z>2) ; l'indicateur structurel atteint AUC 0.66-0.69. On en déduit un signal de vente RÉEL mais MODESTE et asymétrique (short >> long). -> Cela ouvre : que se passe-t-il quand ça tourne mal (Q5) ? et peut-on en faire un indicateur suivi (Q-LIVE) ?

## Q4 : Qu'est-ce qui EXPLIQUE le basis et la prime ? (macro, substitution, physique)  (vient de Q2)
Un signal qu'on ne comprend pas est fragile : on cherche ce qui EXPLIQUE le basis pour le solidifier - variables macro, causalité de Granger CBOT->prime, substitution blé/maïs, fondamentaux UE, change EUR/USD.
_23 fichiers :_
- [ABANDONNÉ] `test_ema_granger_validation.py` : Tests pour VALID-GRANGER-01 - Validation Granger EMA->CBOT (5 tests).
- [ABANDONNÉ] `test_v166_convenience_yield.py` : V166 - convenience yield : chaîne bilan -> CY -> basis -> compression.
- [ABANDONNÉ] `test_v16_basis_explanation.py` : Tests V16 - explication économique du basis.
- [ABANDONNÉ] `test_v80_intercommodity_spreads.py` : Tests V80 - spreads inter-commodités (offline).
- [BLOQUÉ] `EXT013_basis_and_spot_futures_transmission` : EXT013 - Basis & spot/futures transmission (DATA_BLOCKED)
- [BLOQUÉ] `test_comext_and_eu_pressure.py` : Tests VN-C2/C3 - COMEXT bulk (best-effort honnête) + tension physique UE.
- [BLOQUÉ] `test_franceagrimer.py` : Tests DATA-EU-03 - FranceAgriMer / Agreste.
- [BLOQUÉ] `test_v120_basis_econometrics.py` : Tests V120 - économétrie du basis (offline ; statsmodels requis, sinon skip propre).
- [BLOQUÉ] `test_v121_basis_forecast_model.py` : Tests V121 - modèle de prévision du basis (offline).
- [BLOQUÉ] `test_v162_vecm.py` : V162 - VECM / cointégration EMA-CBOT.
- [BLOQUÉ] `test_v174_fx_bce.py` : V174 - règle FX BCE horodatée : parsing offline + math de reconstruction + audit réel.
- [EXPLORATION] `test_eu_fundamentals_collector.py` : eu fundamentals collector
- [EXPLORATION] `test_fas_exports.py` : fas exports
- [EXPLORATION] `test_new_sources.py` : new sources
- [EXPLORATION] `test_v126_matif_substitution_v2.py` : Tests V126 - substitution MATIF v2 (offline, master mocké).
- [EXPLORATION] `test_v168_substitution_basket.py` : V168 - panier de substitution élargi vs blé seul.
- [EXPLORATION] `test_v36_physical_eu.py` : Tests V36 - drivers physiques EU (offline, master + TTF synthétiques).
- [EXPLORATION] `test_v37_substitution_residual.py` : Tests V37 - basis résiduel ajusté substitution blé/maïs (offline).
- [EXPLORATION] `test_v40_substitution_deep.py` : Tests V40 - substitution blé/maïs approfondie (offline, master synthétique).
- [EXPLORATION] `test_v52_matif_substitution.py` : Tests V52 - substitution MATIF blé/maïs (offline, fetchers mockés).
- [EXPLORATION] `test_v54_physical_tension.py` : Tests V54 - physical tension score (offline, master synthétique).
- [EXPLORATION] `test_world_collector.py` : world collector
- [GARDÉ] `test_wasde_world.py` : Tests DATA-WORLD-01 - WASDE EU + Ukraine.
Analyse : On retient que la macro N'EXPLIQUE PAS le basis (R² hors échantillon -0.25), que la causalité de Granger est rejetée, et que la substitution blé/maïs n'est qu'un CONTEXTE (corr 0.60) ; MATIF et spot UE sont bloqués faute de données. On en déduit que la prime est LOCALE et peu explicable par les fondamentaux disponibles - donc on reste sur le basis lui-même + l'offre US, sans sur-interpréter. -> Cul-de-sac partiel : ces explications ne deviennent pas des prédicteurs.

## Q2b : La MÉTÉO aide-t-elle à prédire ?  (vient de Q2)
La météo est le suspect n°1 pour le maïs, donc on la teste sous TOUTES ses formes - météo réalisée, anomalies, événements extrêmes, fenêtres agronomiques, et surtout la distinction réalisé vs PRÉVISIONS et leurs révisions - pour voir si elle anticipe les mouvements ou si le marché les a déjà intégrés.
_22 fichiers :_
- [ABANDONNÉ] `EXT001_weather_crop_windows` : EXT001 - Weather crop windows
- [ABANDONNÉ] `EXT002_weather_lags_and_anomalies` : EXT002 - Weather lags and anomalies
- [ABANDONNÉ] `EXT020_extreme_weather_events` : EXT020 - Extreme weather events
- [ABANDONNÉ] `test_enso.py` : enso
- [ABANDONNÉ] `test_v127_weather_forecast_extremes.py` : Tests V127 - météo forecast extrême + révisions (offline, fetch mocké).
- [ABANDONNÉ] `test_v136_weather_revision_archive.py` : Tests V136 - archive météo historique (offline, fetch mocké).
- [ABANDONNÉ] `test_v140_weather_revision_engine.py` : Tests V140 - weather revision engine (offline, artefacts V127 mockés).
- [ABANDONNÉ] `test_v155_weather_revision_validation.py` : V155 - validation exploratoire des révisions météo (offline, données synthétiques).
- [ABANDONNÉ] `test_v18_weather_deep.py` : Tests V18-WEATHER-DEEP.
- [ABANDONNÉ] `test_v45_weather_crop_stress.py` : Tests V45 - météo & stress cultural (offline, master synthétique).
- [ABANDONNÉ] `test_v48_weather_forecast_signal.py` : Tests V48 - météo prévue favorable/défavorable (oracle borne supérieure, offline).
- [ABANDONNÉ] `test_v51_weather_extremes.py` : Tests V51 - weather extremes lab (offline, master météo synthétique).
- [ABANDONNÉ] `test_v60_weather_basis_driver.py` : Tests V60 - météo comme driver du basis (offline, master synthétique).
- [ABANDONNÉ] `test_v79_enso_regime.py` : Tests V79 - régime ENSO (offline, ONI mocké).
- [EXPLORATION] `EXT018_weather_risk_premium_new_crop` : EXT018 - Weather risk premium new-crop (PARTIAL_DATA)
- [EXPLORATION] `test_ec_mars.py` : Tests DATA-EU-01 - EC MARS collecteur Eurostat.
- [EXPLORATION] `test_forecast_revision_tape.py` : Tests VN-C4 - forecast revision tape (offline, journal mocké).
- [EXPLORATION] `test_openmeteo_eu.py` : Tests DATA-EU-02 - Open-Meteo EU zones.
- [EXPLORATION] `test_openmeteo_previous_runs.py` : V140-DATA - collecteur Open-Meteo Previous Runs (parsing + revision tape, offline).
- [EXPLORATION] `test_v19_cbot_weather.py` : Tests V19 - CBOT risk lab + infrastructure météo prévisionnelle (anti-leakage).
- [EXPLORATION] `test_v28_forecast_weather.py` : Tests V28 - étude météo prévue anti-leakage (offline-safe, archive synthétique).
- [GARDÉ] `test_crop_condition_phenology.py` : crop condition phenology
Analyse : On retient que la météo RÉALISÉE est déjà 'price-in' par anticipation (AUC 0.508 ~ hasard) : quand on l'observe, le marché l'a déjà intégrée. La seule piste cohérente serait les RÉVISIONS de prévisions, mais l'archive disponible est trop courte. On en déduit qu'on ABANDONNE la météo comme prédicteur (on la garde comme contexte : un été de stress rend le basis moins compressible). -> Cul-de-sac, sauf archive de prévisions future.

## Q2c : Le COT (positions) et l'ÉTHANOL (demande) aident-ils ?  (vient de Q2)
On teste les deux autres suspects classiques : le positionnement des spéculateurs (COT Managed Money - extrêmes, flux) et la demande éthanol/énergie (marge crush), pour voir s'ils donnent un signal directionnel.
_4 fichiers :_
- [ABANDONNÉ] `EXT003_cot_features` : EXT003 - COT features (Managed Money disaggregated)
- [ABANDONNÉ] `EXT004_ethanol_ddg_crush_spread` : EXT004 - Ethanol / DDG / crush spread (PARTIAL_DATA)
- [ABANDONNÉ] `test_cot_advanced.py` : cot advanced
- [ABANDONNÉ] `test_eu_carbon.py` : Tests DATA-EU-04 - ETS CO₂ et TTF enrichi.
Analyse : On retient qu'aucun n'aide hors échantillon : le COT Managed Money dégrade RMSE et DA à tous horizons, et sans vrais prix éthanol/DDG les proxys sont inutiles. On en déduit que ces deux dossiers sont CLOS avec les données actuelles. -> Cul-de-sac.

## Q5 : La compression ADVERSE est-elle prévisible ?  (vient de Q3)
Le short 'basis haut' a des pertes rares mais grosses (cas ADVERSE) : on cherche à savoir si on peut les PRÉVOIR. On distingue l'ISSUE (la compression va-t-elle mal tourner ?) du MÉCANISME (par quel chemin ?), car prévoir l'un ou l'autre n'a pas la même valeur.
_16 fichiers :_
- [ABANDONNÉ] `test_hazard_compression.py` : Tests VN-D1 - hazard time-to-compression (synthétique).
- [ABANDONNÉ] `test_v169_bayes_survival.py` : V169 - survie bayésienne hiérarchique (sampler + pooling + censure).
- [ABANDONNÉ] `test_v44_mechanism_magnitude.py` : Tests V44 - mécanisme & magnitude (offline, master synthétique).
- [ABANDONNÉ] `test_v57_magnitude_buckets.py` : Tests V57 - classes de magnitude de compression (offline, master synthétique).
- [ABANDONNÉ] `test_v72_survival_reversion.py` : Tests V72 - survival / time-to-reversion (offline).
- [EXPLORATION] `test_adverse_discriminator.py` : Tests VN-D3 - discriminant ADVERSE (entry-time only).
- [EXPLORATION] `test_v104_compression_start.py` : Tests CT-01 (v104) - compression_start_date (offline).
- [EXPLORATION] `test_v105_compression_event_study.py` : Tests CT-02 (v105) - event study autour du début de compression (offline).
- [EXPLORATION] `test_v106_compression_trigger.py` : Tests CT-09/10/11 (v106) - compression trigger (offline).
- [EXPLORATION] `test_v50_adverse_casebook.py` : Tests V50 - ADVERSE casebook (offline, master synthétique).
- [EXPLORATION] `test_v58_casebook_enriched.py` : Tests V58 - casebook ADVERSE enrichi (offline, master synthétique).
- [EXPLORATION] `test_v70_path_classification.py` : Tests V70 - classification du canal de compression (offline).
- [GARDÉ] `test_v32_adverse_path.py` : Tests V32 - détection du chemin ADVERSE (offline, master synthétique).
- [GARDÉ] `test_v38_adverse_risk.py` : Tests V38 - module ADVERSE_RISK (offline, master synthétique).
- [GARDÉ] `test_v64_adverse_risk_v2.py` : Tests V64 - ADVERSE_RISK v2 (offline, master synthétique).
- [GARDÉ] `test_v65_cbot_rebound_engine.py` : Tests V65 - CBOT rebound engine (offline, master synthétique).
Analyse : On retient que l'ISSUE ADVERSE (la compression va-t-elle mal tourner ?) est prévisible (LOO AUC 0.72) à partir du niveau d'entrée et d'un basis bas, mais que le MÉCANISME (par quel chemin ?) ne l'est pas (AUC 0.48). On en déduit qu'on ne peut pas prédire COMMENT ça tourne mal, mais qu'on peut estimer le RISQUE a priori - donc viser un score de RISQUE plutôt qu'une prédiction. -> Comment doser ce risque ?

## Q6 : Peut-on DOSER le risque (support CBOT, volatilité, drawdown) ?  (vient de Q5)
Puisqu'on ne prédit pas le mécanisme, on construit des briques de RISQUE indépendantes de la direction - un 'support CBOT' qui protège la prime, la volatilité conditionnelle (HAR/EGARCH), un score de drawdown - pour filtrer les moments dangereux.
_9 fichiers :_
- [EXPLORATION] `test_roll_risk.py` : Tests V7-07 - Roll-aware premium model.
- [EXPLORATION] `test_v23_cbot_risk_regime.py` : Tests V23 - risque drawdown CBOT + reversion conditionnelle au régime.
- [EXPLORATION] `test_v43_signal_quality.py` : Tests V43 - matrice de qualité de signal (offline, master synthétique).
- [GARDÉ] `EXT009_garch_egarch_volatility` : EXT009 - GARCH / EGARCH / GJR-GARCH (risque)
- [GARDÉ] `EXT010_har_realized_volatility` : EXT010 - HAR realized volatility
- [GARDÉ] `test_ema_volatility.py` : Tests pour NB-EMA-11 - Volatilité EMA.
- [GARDÉ] `test_ema_volatility_v2.py` : ema volatility v2
- [GARDÉ] `test_v41_cbot_support.py` : Tests V41 - CBOT_SUPPORT_SCORE (offline, master synthétique).
- [GARDÉ] `test_v86_cbot_support_v2.py` : Tests V86 - CBOT_SUPPORT v2 (offline, ENSO=None).
Analyse : On retient que le support CBOT divise par 2 le risque ADVERSE et double le PnL, que la VOLATILITÉ se prévoit bien (HAR/EGARCH -24 % de RMSE vs random walk - un des résultats les plus solides de l'étude), et que le drawdown CBOT est prévisible (AUC 0.74). On en déduit de vraies briques de gestion du risque, à utiliser comme GATE (filtre) plutôt que comme signal de direction. -> Tout ça tient-il dans un indicateur suivi dans le temps ?

## Q-LIVE : Peut-on en faire un INDICATEUR suivi (forward, machine d'état, courbe) ?  (vient de Q3)
On industrialise pour voir si l'indicateur tient dans la durée : machine d'état de la prime, gates de fraîcheur des données, catalogue de catalyseurs, courbe officielle Euronext, dashboards et collecte automatisée - pour le suivre jour après jour sans tricher.
_83 fichiers :_
- [BLOQUÉ] `EXT005_futures_curve_spreads` : EXT005 - Futures curve spreads & carry (DATA_BLOCKED)
- [BLOQUÉ] `test_barchart_contract_download_probe.py` : barchart contract download probe
- [BLOQUÉ] `test_curve_sign_audit.py` : Tests VN-A3 - audit du signe de courbe.
- [BLOQUÉ] `test_curve_spreads.py` : curve spreads
- [BLOQUÉ] `test_ema_continuous_series_probe.py` : ema continuous series probe
- [BLOQUÉ] `test_ema_curve_ablation.py` : ema curve ablation
- [BLOQUÉ] `test_ema_manual_backfill_validator.py` : ema manual backfill validator
- [BLOQUÉ] `test_euronext_curve.py` : euronext curve
- [BLOQUÉ] `test_euronext_endpoint_probe.py` : euronext endpoint probe
- [BLOQUÉ] `test_proxy_forward_quote.py` : V144-DATA - quote proxy forward du front officiel (offline, fetch injecté).
- [BLOQUÉ] `test_v109_ema_curve_live_tension.py` : Tests V109 - courbe EMA officielle live -> PHYSICAL_TENSION (offline, fetch mocké).
- [BLOQUÉ] `test_v125_curve_accumulation.py` : Tests V125 - accumulation de la courbe EMA + tendance de tension (offline).
- [BLOQUÉ] `test_v128_intraday_aligned_probe.py` : Tests V128 - probe intraday CBOT aligné + accumulation forward (offline, fetch mocké).
- [BLOQUÉ] `test_v30_official_curve.py` : Tests V30 - structure de courbe officielle (contango/backwardation), offline.
- [EXPLORATION] `test_confidence_p_correct.py` : confidence p correct
- [EXPLORATION] `test_consensus.py` : consensus
- [EXPLORATION] `test_consensus_real.py` : consensus real
- [EXPLORATION] `test_ema_continuous_series.py` : Tests pour NB-EMA-03 - Séries continues EMA.
- [EXPLORATION] `test_ema_contract_reference.py` : ema contract reference
- [EXPLORATION] `test_ema_contracts.py` : ema contracts
- [EXPLORATION] `test_ema_contracts_rolls.py` : Tests pour NB-EMA-02 - Contrats EMA et rolls.
- [EXPLORATION] `test_ema_contracts_v2.py` : ema contracts v2
- [EXPLORATION] `test_ema_event_study.py` : Tests pour NB-EMA-09 - Event study grands mouvements EMA.
- [EXPLORATION] `test_ema_event_study_v2.py` : ema event study v2
- [EXPLORATION] `test_euronext_backfill.py` : euronext backfill
- [EXPLORATION] `test_euronext_continuous.py` : euronext continuous
- [EXPLORATION] `test_event_microstructure.py` : Tests VN-E2 - microstructure événementielle (offline, journal mocké).
- [EXPLORATION] `test_event_study.py` : Tests V7-10 - Event study premium.
- [EXPLORATION] `test_forward_milestones.py` : Tests V147/V148 - milestones forward + checkpoint gated.
- [EXPLORATION] `test_indicator_confidence.py` : indicator confidence
- [EXPLORATION] `test_module_a.py` : module a
- [EXPLORATION] `test_module_a_calibration.py` : module a calibration
- [EXPLORATION] `test_roll_season_backtest_v6.py` : roll season backv6
- [EXPLORATION] `test_state_transitions.py` : Tests VN-D2 - transitions d'état.
- [EXPLORATION] `test_v101_official_synthesis_fix.py` : Tests V101 - fix synthèse officielle live (offline, journal mocké).
- [EXPLORATION] `test_v102_active_signal_monitoring.py` : Tests V102 - suivi dynamique du signal actif (offline, journal mocké).
- [EXPLORATION] `test_v103_proxy_official_dashboard.py` : Tests V103 - dashboard proxy/officiel (offline).
- [EXPLORATION] `test_v107_live_context_refresh.py` : Tests V107 - refresh contexte live (offline, fetch + journal mockés).
- [EXPLORATION] `test_v108_live_basis_reconstruction.py` : Tests V108 - reconstruction basis live + ADVERSE_RISK live (offline, fetchers mockés).
- [EXPLORATION] `test_v124_active_monitoring_v2.py` : Tests V124 - santé du signal actif v2 (statuts par paliers 10/20/30 j).
- [EXPLORATION] `test_v129_event_catalyst_library.py` : Tests V129 - catalogue de catalyseurs (détection d'épisodes + classification, données synthétiques).
- [EXPLORATION] `test_v130_basis_regime_econometrics.py` : Tests V130 - économétrie du basis par régimes (synthétique, statsmodels optionnel).
- [EXPLORATION] `test_v133_monthly_forward_report_v2.py` : Tests V133 - rapport forward mensuel v2 (offline).
- [EXPLORATION] `test_v134_data_sourcing_plan.py` : Tests V134 - plan de sourcing (statique).
- [EXPLORATION] `test_v135_decision_checkpoint.py` : Tests V135 - checkpoint décisionnel (offline, artefacts mockés).
- [EXPLORATION] `test_v137_event_date_attribution.py` : Tests V137 - attribution par dates de rapports USDA (synthétique).
- [EXPLORATION] `test_v138_horizon_estimator.py` : Tests V138 - estimateur d'horizon par demi-vie.
- [EXPLORATION] `test_v141_v142_forward.py` : V141/V142 - validation forward gatée (offline via monkeypatch du journal).
- [EXPLORATION] `test_v141_v142_forward_validation.py` : Tests V141/V142 - validateurs forward courbe + MATIF (gated).
- [EXPLORATION] `test_v143_v145_v146.py` : Tests V143 (enrichment) / V145 (lifecycle) / V146 (dashboard v4).
- [EXPLORATION] `test_v152_event_study.py` : V152 - event study 2.0 (aligné start A, CI bootstrap, censure).
- [EXPLORATION] `test_v153_start_vs_inprogress.py` : V153 - labels START/IN_PROGRESS sans lookahead + renommage PROGRESS_SCORE.
- [EXPLORATION] `test_v173_cost_grid.py` : V173 - grille coûtsxslippage par régime (offline, frame synthétique hors holdout).
- [EXPLORATION] `test_v177_data_gated_reruns.py` : V177 - gates de re-run data-gated : ACCUMULATING sous le seuil, TRIGGERED au-dessus.
- [EXPLORATION] `test_v178_official_validation.py` : V178 - validation 40 j proxy<->officiel : gate, paires, seuils figés.
- [EXPLORATION] `test_v179_active_signal_report.py` : V179 - rapport signal actif : assemblage lecture seule, markdown, statuts.
- [EXPLORATION] `test_v180_dashboard_v5.py` : V180 - dashboard v5 : baseline vs confirmé, assemblage lecture seule.
- [EXPLORATION] `test_v181_weekly_maintenance.py` : V181 - maintenance hebdo : checks individuels et verdict global.
- [EXPLORATION] `test_v22_live_stabilization.py` : Tests V22 - stabilisation live : gate de fraîcheur + classification pipeline.
- [EXPLORATION] `test_v26_official_ema.py` : Tests V26 - parser officiel Euronext + validation niveaux (offline-safe).
- [EXPLORATION] `test_v27_official_forward.py` : Tests V27 - forward tracking officiel + journal append-only (offline-safe).
- [EXPLORATION] `test_v31_forward_dashboard.py` : Tests V31 - dashboard forward premium (offline).
- [EXPLORATION] `test_v35_cbot_engine.py` : Test V35 - moteur de compression CBOT (offline, master synthétique).
- [EXPLORATION] `test_v39_enrichment.py` : Tests V39-ENRICH - batch d'expériences d'enrichissement (offline, master synthétique).
- [EXPLORATION] `test_v47_objective_choice.py` : Tests V47 - choix d'objectif z->0.5 vs z->0 (offline, master synthétique).
- [EXPLORATION] `test_v59_monthly_forward_report.py` : Tests V59 - rapport forward mensuel (offline, journaux synthétiques).
- [EXPLORATION] `test_v71_eu_production_balance.py` : Tests V71 - bilan physique EU (production EC MARS), offline (fetch mocké).
- [EXPLORATION] `test_v71b_eu_production_locality.py` : Tests V71b - localité géographique production EU (offline, fetch mocké).
- [EXPLORATION] `test_v81_robustness_audit.py` : Tests V81 - audit de robustesse (offline).
- [EXPLORATION] `test_v82_episode_library.py` : Tests V82 - bibliothèque d'épisodes (offline, with_network=False).
- [EXPLORATION] `test_weekly_report.py` : weekly report
- [GARDÉ] `test_state_machine.py` : Tests V139 - machine d'état premium.
- [OUTIL] `test_module_a_data_status.py` : module a data status
- [OUTIL] `test_official_automation.py` : Tests V42 - automation officielle (calendrier + sessions + proxy/officiel).
- [OUTIL] `test_official_proxy_validation.py` : Tests V144 - validation officielle vs proxy par jalons.
- [OUTIL] `test_session_timing.py` : Tests VN-A2 - session timing PROVISIONAL/FINAL/SETTLING (DSP 18:30 CET Paris).
- [OUTIL] `test_session_truth_v150.py` : V150 - vérité de session : backfill, champs obligatoires, précédence FINAL.
- [OUTIL] `test_single_source_v152.py` : V152-SYNC - cohérence de la source unique premium (head/dashboard/lifecycle/monthly/latest).
- [OUTIL] `test_v122_journal_consistency.py` : Tests V122 - cohérence journal + politique de révision auditée (2026-06-01 STRONG vs EXTREME).
- [OUTIL] `test_v123_freshness_gate.py` : Tests V123 - gate de fraîcheur du contexte (offline, artefacts mockés).
- [OUTIL] `test_v161_import_parity.py` : V161 - parité d'import COMEXT : décodeur JSON-stat + lag de publication (offline).
- [OUTIL] `test_v24_data_forensic.py` : Tests V24 - audit forensique (logique sur données synthétiques + invariants).
- [OUTIL] `test_v46_settlement_alignment.py` : Tests V46 - alignement de settlement CBOT/EMA (offline, master synthétique).
Analyse : On retient un système forward fonctionnel et honnête (il se dégrade quand les données sont périmées), mais qui reste ANALYTIQUE : pas de paper-trading, beaucoup de pistes data-gated, et un edge toujours modeste. On en déduit qu'avant d'aller plus loin il faut REPARTIR DE ZÉRO et tester chaque famille proprement et systématiquement. -> Famille par famille, qu'est-ce qui marche vraiment ?

## Q7 : Systématiquement (recherche externe EXT), quelles familles portent un signal ?  (vient de Q-LIVE)
On repart de ZÉRO avec un protocole anti-fuite strict et on teste SYSTÉMATIQUEMENT 24 familles externes (1 expérience EXT chacune : météo, WASDE, COT, courbe, éthanol, basis, crop condition, volatilité, régimes, et des modèles trend/stacking/deep learning) - pour trancher, famille par famille, ce qui marche.
_27 fichiers :_
- [ABANDONNÉ] `EXT008_wasde_surprise_proxy` : EXT008 - WASDE surprise proxy (révisions, sans consensus)
- [ABANDONNÉ] `EXT011_trend_following_benchmark` : EXT011 - Trend-following benchmark
- [ABANDONNÉ] `EXT012_ou_mean_reversion_benchmark` : EXT012 - OU mean-reversion benchmark (DATA_BLOCKED)
- [ABANDONNÉ] `EXT016_nbeatsx_exogenous_model` : EXT016 - NBEATSx exogenous model
- [ABANDONNÉ] `EXT050_model_stacking_ensemble` : EXT050 - Model stacking ensemble
- [ABANDONNÉ] `test_deep_learning.py` : deep learning
- [ABANDONNÉ] `test_multiple_testing.py` : Tests V7-29 - Multiple testing correction + holdout lock.
- [ABANDONNÉ] `test_overfitting_v172.py` : V172 - anti-overfitting : PSR/DSR/PBO.
- [ABANDONNÉ] `test_red_team_validation.py` : Tests V7-30 - Red team validation.
- [ABANDONNÉ] `test_stacking.py` : stacking
- [ABANDONNÉ] `test_v164_hmm.py` : V164 - HMM régime, triangulation du START.
- [ABANDONNÉ] `test_v170_causal_dag.py` : V170 - d-séparation, back-door et classification d'effets sur DAGs connus.
- [ABANDONNÉ] `test_v171_placebo.py` : V171 - placebo : spécificité de l'edge basis EMA vs spreads témoins.
- [ABANDONNÉ] `test_v172_overfit_on_trades.py` : V172-REAL - pack anti-overfitting branché sur les trades simulés (hors holdout 2024).
- [EXPLORATION] `EXT014_bayesian_model_averaging` : EXT014 - Bayesian model averaging (BMA-like)
- [EXPLORATION] `test_dim_reduction.py` : dim reduction
- [EXPLORATION] `test_ema_feature_importance.py` : Tests pour NB-EMA-10 - Importance des features EMA.
- [EXPLORATION] `test_ema_feature_importance_v2.py` : ema feature importance v2
- [EXPLORATION] `test_ema_feature_selector.py` : ema feature selector
- [EXPLORATION] `test_ema_relative_feature_importance.py` : ema relative feature importance
- [EXPLORATION] `test_meta_model_premium_v6.py` : meta model premium v6
- [EXPLORATION] `test_seasonal_experts.py` : Tests V7-06 - Modèles saisonniers experts.
- [GARDÉ] `EXT007_wasde_release_features` : EXT007 - WASDE release features
- [GARDÉ] `EXT015_shap_feature_selection` : EXT015 - Feature selection / importance (train-only)
- [GARDÉ] `EXT017_market_regime_detection` : EXT017_market_regime_detection
- [GARDÉ] `EXT019_crop_condition_report_features` : EXT019 - Crop condition report features
- [GARDÉ] `EXT024_var_supply_demand_benchmark` : EXT024 - Supply-demand directional benchmark
Analyse : On retient seulement 3 briques : Crop Condition @ H90 (AUC 0.724), WASDE stocks-to-use @ H40, et la volatilité (HAR/EGARCH). On rejette clairement trend-following (le maïs ne tend pas), stacking et deep learning (sur-apprennent), surprise WASDE et COT (rien hors échantillon). On en déduit que la PARCIMONIE gagne et que le seul signal directionnel réel est l'OFFRE US à horizon long. -> Ces 3 briques survivent-elles hors échantillon ?

## Q8 : Survivent-ils au HOLDOUT 2024+ -> un score de vente ?  (vient de Q7)
On assemble les seules briques validées en un score de vente parcimonieux (régression logistique) et on l'éprouve UNE SEULE FOIS sur le holdout 2024+ jamais utilisé avant, contre la random walk ET une simple saisonnalité, pour un verdict honnête.
_3 fichiers :_
- [GARDÉ] `test_cbot_sale_score.py` : Tests config + reproductibilité du score de vente CBOT (étape 7).
- [GARDÉ] `test_cbot_sale_score_leakage.py` : Tests anti-fuite du score de vente CBOT (étape 7).
- [GARDÉ] `test_cbot_sale_score_outputs.py` : Tests des sorties du score de vente CBOT (étape 7).
Analyse : On retient que crop@H90 fait DA 0.686 / AUC 0.816 sur 2024+ et bat largement la random walk - c'est cohérent (2024 = grosse récolte -> baisse). MAIS il ne bat PAS une simple saisonnalité (0.752), et le backtest dépend du cadrage. On en déduit un verdict honnête : FRAGILE - un repère utile, pas une preuve de robustesse. -> À quoi ça ressemble sur le vrai marché Euronext ?

## Q9 : À quoi ressemble l'indicateur sur l'historique EURONEXT ?  (vient de Q8)
On applique le score CBOT à l'historique de prix Euronext et on le VISUALISE (dashboard interactif) pour voir si les recommandations auraient aidé à vendre, et à quel point le résultat est fiable.
_3 fichiers :_
- [GARDÉ] `test_euronext_indicator.py` : Tests de l'indicateur Euronext : chargement, target_date, anti-fuite, recommandations.
- [GARDÉ] `test_euronext_indicator_backtest.py` : Tests du backtest agricole Euronext : pas de short/buy, total vendu <= 100 %, cooldown.
- [GARDÉ] `test_euronext_indicator_dashboard.py` : Tests du dashboard Euronext : HTML créé, autonome (pas d'image externe), graphiques présents.
Analyse : On retient que les recommandations ORDONNENT correctement les retours futurs (SELL_PARTIAL -> -5.8 % à 90 j, WAIT -> +5.1 %), ce qui est visuellement convaincant. MAIS la discrimination hors échantillon est faible (AUC 0.561) et le prix Euronext disponible est à 97 % un proxy. On en déduit un verdict RESEARCH_ONLY : un outil de visualisation honnête, pas un conseil de vente opérationnel. -> Conclusion de l'étude.

## Conclusion de l'étude
- Prédire le PRIX exact du maïs est impossible avec les données gratuites : la random walk reste imbattable en RMSE (aucun modèle sur 36 ne la bat, test de Diebold-Mariano).
- Ce qu'on sait DÉTECTER sur le CBOT avec fiabilité (même si ce n'est pas le prix) :
- La direction à 90 jours via la Crop Condition US : AUC 0.816 sur le holdout 2024+ (jamais vu avant), un résultat solide et économiquement cohérent (grosse récolte = prix qui baisse).
- La direction à 40 jours via le ratio stocks-sur-usage du WASDE : DA 0.705 sur le holdout 2024+.
- Le risque de drawdown du CBOT : prévisible, AUC 0.74 (on sait dire quand le risque monte).
- La volatilité : les modèles HAR et EGARCH battent la random walk de 24 % de RMSE, c'est le résultat le plus solide de l'étude.
- L'issue ADVERSE (quand une vente de prime va mal tourner) : prévisible a priori, AUC 0.72.
- Le seul signal directionnel réel est l'OFFRE US (Crop Condition, WASDE) à horizon long ; la parcimonie gagne : 2 variables (basis_z + saison) suffisent (AUC 0.694), les modèles complexes n'ajoutent rien.
- Ce qu'on garde sur l'EURONEXT et le basis :
- Le basis revient à la moyenne (demi-vie 17 a 47 jours) ; vendre quand le basis est haut survit aux coûts hors crise (+115) ; indicateur structurel de vente AUC 0.656 a 0.694.
- La prime se compresse surtout quand le CBOT monte (la jambe CBOT pèse 6 fois la jambe Euronext) : 'vendre la prime' revient à 'parier sur une hausse relative du CBOT'.
- L'avantage est ASYMÉTRIQUE : vendre une prime haute est robuste, le pari inverse (prime basse) ne l'est pas (short bien supérieur a long).
- Le support CBOT divise par 2 le risque ADVERSE et double le PnL ; et la réversion du basis est plus rapide quand le CBOT soutient (environ 29 jours vers z0, 87.5 % des cas).
- Caractérisation des épisodes de prime haute : les épisodes tirés par le CBOT gagnent presque toujours (gain moyen +22.7), ceux tirés par l'Euronext gagnent moins (+14), et les épisodes ADVERSE ne sont jamais vraiment profitables (excursion favorable 5.7, durée 60 jours) mais sont distinguables tôt.
- La sortie partielle (revenir vers z 0.5 au lieu de z 0) évite plusieurs pertes en queue, surtout en contexte défavorable.
- Les découvertes importantes de l'étude :
- La prime européenne est LOCALE : la macro ne l'explique pas (R² hors échantillon -0.25).
- Spécificité européenne : la prime corrèle avec le basis (+0.59) et PAS avec le CBOT (-0.46), ce qui prouve une prime locale et non un simple artefact du CBOT.
- La demi-vie du basis rétrécit quand l'écart est extrême (8.3 jours en régime modéré, 3.3 jours en régime extrême) : plus le basis est tendu, plus il revient vite.
- Les signaux marginaux (faible écart, z<1.2) sous-performent nettement les signaux forts (gain 6.1 contre 14.1).
- Le CBOT prédit mieux ses BAISSES que ses HAUSSES (asymétrie directionnelle).
- Le signal météo n'est pas dans la météo MOYENNE mais dans les EXTRÊMES prévus : un dôme de chaleur prévu en pollinisation corrèle +0.31 avec le rendement CBOT (extrême prévu = CBOT +1.6 % contre -2.3 % le reste du temps), conforme a la chute non-linéaire du rendement au-delà de 30-32 degrés.
- Le meilleur signal d'alerte ADVERSE est l'écart de prix blé/maïs (wheat_corn_z, AUC 0.653) ; la substitution blé/maïs reste un CONTEXTE (corr 0.60), pas un prédicteur direct.
- Ce qu'on pensait prévisible et qui ne l'est PAS (falsifié par les tests) :
- Le prix exact (random walk imbattable) et la météo réalisée (déjà 'price-in', AUC 0.508).
- Les surprises WASDE en quotidien, les positions COT et la demande éthanol : aucun signal hors échantillon.
- Le mécanisme de la compression de prime (AUC 0.48) et son timing par modèle de hasard.
- La demi-vie du NIVEAU n'est PAS l'horizon de décision : analytique environ 9.5 jours contre 28.6 jours réels sur les trades (facteur 3), il faut recaler l'horizon sur le réel.
- Le trend-following (le maïs ne tend pas), le stacking et le deep learning (ils sur-apprennent).
- L'explication 'fair-value' du basis (causalité de Granger rejetée hors échantillon).
- L'inversion saisonnière supposée du basis n'a pas résisté en forward (falsifiée).
- L'avantage du basis EMA n'est pas aussi SPÉCIFIQUE qu'espéré : le test placebo le retrouve en partie sur des spreads témoins, donc prudence.
- Les stratégies actives portent un risque de SUR-AJUSTEMENT (mesures PSR, DSR, PBO), d'où le choix assumé de préférer le simple au complexe.
- Les limites et les coûts (honnêteté de l'étude) :
- Le mur des coûts : l'avantage net est mince et concentré sur les signaux extrêmes (z>2) ; il survit a des coûts d'environ 5 €/t hors crise mais s'efface au-delà et hors des régimes favorables.
- Le score de vente final est FRAGILE : sur le holdout 2024+ il bat la random walk (DA 0.686) mais ne bat PAS une simple saisonnalité (0.752) sur une fenêtre courte (environ 1.5 an), a reconfirmer en forward.
- L'indicateur Euronext est RESEARCH_ONLY : il ordonne bien les retours (vendre une partie = -5.8 % a 90 jours, attendre = +5.1 %) mais discrimine mal hors échantillon (AUC 0.561) et le prix Euronext disponible est a 97 % un proxy.
- Le système live reste ANALYTIQUE (pas de paper-trading) et beaucoup de pistes sont bloquées par la donnée payante : courbe officielle par maturité, MATIF blé, intraday, consensus d'analystes.
- Bilan : on ne prédit pas le prix, mais on détecte un risque de baisse à 90 jours avec environ 73 % de précision quand l'indicateur dit 'vendre une partie' ; ces signaux forts n'apparaissent qu'environ 1 fois par an (17 épisodes en 16 ans). C'est une aide a la decision de vente, pas une prevision de prix ni un robot de trading.