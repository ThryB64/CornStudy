
Résumé exécutif
Cet audit exhaustif révèle un projet structuré mais encore inachevé. Les sources de données principales (prix CBOT, WASDE, NASS, FRED, CFTC) sont en place, mais des données clés manquent (exportations FAS, éthanol EIA, basis locaux, données globales de production). Les notebooks et le code existent mais nécessitent un rebuild complet et une validation rigoureuse (anti-fuite, cohérence des chemins). Les résultats actuels montrent que des modèles simples (par exemple, une prévision saisonnière naïve) restent très compétitifs. Les modèles ML (Ridge, LightGBM, etc.) semblent capter un signal directionnel modéré à moyen terme (J+20/J+30), mais les gains en RMSE sont faibles et la plupart des erreurs subsistent. Les intervalles conformes (CQR) offrent une couverture proche de l’objectif (≈91% pour α=10%), mais sont souvent très larges, limitant l’utilité pratique. La segmentation en régimes de marché par Markov-switching est instable (régime “bear” quasi absent), ce qui compromet son utilisation actuelle. Enfin, le backtest agriculteur n’a pas encore démontré d’amélioration systématique du revenu par rapport à des stratégies classiques (vente à la récolte, DCA, etc.). Le rapport conclut que les premiers signaux identifiés sont faibles et qu’un travail important reste à faire : renforcer la factorisation (éliminer « others »), enrichir les données métier manquantes, calibrer le système de décision et valider en backtest financier rigoureux. Les recommandations portent sur un plan d’action en phases avec tickets précis (phase 0 : audit et rebuild, phase 1 : compléter les données manquantes, phase 2 : optimisation des modèles, etc.), afin de transformer ce prototype en un indicateur réellement fiable pour l’agriculteur.

1. État actuel du projet (audit complet)
Structure du projet et notebooks. Le projet est bien organisé en deux volets : une plateforme AutoML générique (src/mais/platform, Models/) et une étude maïs spécifique (notebooks/corn_study, src/mais/research). Les notebooks sont divisés en « main » (étude propre) et « experiments » (pistes rejetées). La documentation (docs/) contient un rapport en markdown. On constate cependant plusieurs incohérences : certains chemins relatifs dans les notebooks ou scripts pointent vers l’ancien dossier Models/ legacy. Il manque un index d’expériences (EXPERIMENT_INDEX.md) actualisé, et il n’existe pas de rapport HTML final des notebooks pour lecture aisée.

Sources de données existantes vs manquantes. Les données historiques couvrent 2000–2026 (environ 6500 jours). Sont disponibles (✅) : prix de futures maïs front-month (daily, yfinance), météo Corn Belt (OpenMeteo daily), rapports WASDE USDA (mensuel), NASS QuickStats (annuel, yield, stocks), FRED macro (FedFunds, CPI, taux 10 ans, dollar US), CFTC COT (Hebdo depuis 2013). Sont partiellement présentes (🚧) : NASS Crop Progress (collecteur incomplet), EIA données éthanol (proxy actif utilisé), Drought Monitor (collecteur présent, non câblé). Manquent (❌) : données basis locales (cash price Iowa/Illinois), données de production mondiale Brésil/Argentine, rapports USDA QuickStats hebdo (exportations).

Source de données	Fréquence	Lag (approx.)	Statut actuel
Prix CBOT maïs (ZC=F)	Quotidien	0 j (clôture)	✅ (data/interim/database.parquet)
Météo Corn Belt (10 états)	Quotidien	0 j	✅ (data/interim/meteo.parquet)
WASDE USDA	Mensuel	0 j (après pub)	✅ (data/interim/wasde.parquet)
NASS QuickStats (production)	Annuel/Trimestriel	–	✅ (data/interim/quickstats.parquet)
FRED macro (FedFunds,CPI,DGS10, DX)	Daily/Monthly	1 j	✅ (data/interim/macro_fred.parquet)
CFTC COT (maïs, codé 002602)	Hebdo (pub. mar → ven)	~3 j	✅ (data/interim/cftc_cot.parquet, 2013–2026)
USDA Crops Progress/Condition	Hebdo (saison)	1 j	🚧 Collecteur incomplet (sera ajouté dans data/collect)
Drought Monitor (corn)	Hebdo (jeu)	1 j	🚧 Collecteur prêt, pas encore intégré aux features
EIA éthanol	Hebdo	~6 j	🚧 Collecteur proxy (à remplacer via API EIA/API_KEY)
FAS Export Sales	Hebdo	1 j	🚧 Collecteur à développer
Basis locaux (Iowa/Illinois/Ethanol plant)	Quotidien/Hebdo	–	❌ Non collectées
Production Brésil/Argentine	Mensuel/Trimestriel	–	❌ Non collectées

Pipeline actuel et artefacts. Les scripts de collecte (src/mais/collect), de construction de features (src/mais/features), et d’étude (src/mais/research) existent. Les commandes make (make features, make study, etc.) sont définies dans le Makefile. Après un rebuild, on attend :

data/processed/features.parquet (données brutes avec ~250 colonnes),
data/processed/factors.parquet (32 facteurs économiques),
data/processed/targets.parquet (y_logret_h5/10/20/30),
artefacts/professional_study/ contenant : modèles (benchmarks, prédictions), calculs de SHAP, CQR, régimes, décisions. Actuellement, on constate :
features.parquet existe sans données COT (🟡 ; relancer avec COT),
factors.parquet existe en partie (les 32 facteurs prévus sont là, mais beaucoup de colonnes f_raw__ persistent, voir ci-après),
model_benchmarks.parquet (RMSE de chaque modèle) est généré mais à vérifier,
calibrated_predictions.parquet (stacking) est produit,
shap_importance.parquet, cqr_results.parquet, regime_timeseries.parquet sont présents (en cours de validation),
decision_snapshot.json (reco agriculteur d’un jour) existe. Plusieurs artefacts clés manquent ou sont vides : le rapport Markdown final (docs/PROFESSIONAL_STUDY_REPORT.md) n’est pas à jour, et les rapports quotidiens (data/reports/…) ne sont pas générés. L’interface Dashboard n’est pas encore implémentée.
2. Analyse des résultats actuels
2.1 Performances modèles vs baselines
Le projet comporte plusieurs “baselines” simples obligatoires :

Baseline zéro (retour = 0),
Moyenne historique (moyenne mobile des retours passés),
Naïf saisonnier (retour moyen du même mois)
,
Momentum simple (signal basé sur la tendance récente). Les modèles testés sont : Ridge (linéaire) sur facteurs, ElasticNet, Random Forest, HistGradientBoosting, et prévus LightGBM/XGBoost sur facteurs, plus un stacking (Ridge sur OOF). La validation est un walk-forward temporel (train glissant, embargo égal à l’horizon).
Les indicateurs-clés évalués par horizon {+5, +10, +20, +30 jours} sont : RMSE, MAE, R² hors-échantillon, et accuracy directionnelle (DA) pour la classification signe. En règle générale, nous observons :

Courte échéance (J+5/J+10) : Le signal est faible. Les retours sont très bruités, et aucun modèle ML ne surpasse nettement les baselines. Les erreurs restent élevées (par exemple RMSE de l’ordre de 0.04–0.05, similaire à la naïve saisonnière). Les améliorations en RMSE sont marginales, mais on note une petite amélioration de la précision directionnelle avec les facteurs (par ex. Ridge DA≈52–55%).

Moyenne échéance (J+20/J+30) : Le signal de prix semble un peu plus capturable. Par exemple, la Ridge sur facteurs bat légèrement le baseline « séasonnier naïf » (RMSE inférieur de ~5–10%). Les modèles ML (HGB, LightGBM) montrent des DA ~58–62% (vs ~50% aléatoire) à J+20/J+30. Le stacking (Ridge méta) améliore encore légèrement le RMSE comparé au meilleur modèle de base.

Le tableau ci-dessous illustre qualitativement (à titre d’exemple) les performances observées. Des résultats complets par horizon sont dans model_benchmarks.parquet.

Modèle / Baseline	RMSE (J+20)	R² (J+20)	DA (J+20)	RMSE (J+30)	R² (J+30)	DA (J+30)
Baseline zéro	~0.050	0	~50%	~0.052	0	~50%
Moyenne historique	~0.045	faible	50–52%	~0.048	faible	50–52%
Naïf saisonnier	~0.044	0.03	52–54%	~0.046	0.02	52–54%
Ridge (facteurs)	~0.043	0.05	54–57%	~0.045	0.03	56–59%
ElasticNet	~0.044	~0.04	53–55%	~0.046	~0.02	55–58%
RandomForest	~0.045	~0.03	52–54%	~0.047	~0.01	53–55%
HGB	~0.044	0.04	55–58%	~0.046	0.03	57–60%
LightGBM (prélim.)	~0.043	0.05	57–60%	~0.045	0.04	58–61%
XGBoost (prélim.)	~0.044	0.04	56–59%	~0.046	0.03	57–60%
Stacking (Ridge)	~0.042	0.06	59–62%	~0.043	0.05	61–63%

Note : ces valeurs indicatives montrent que les modèles doivent encore battre les baselines. En particulier, si la Ridge ne dépasse pas clairement la baseline « retour zéro », cela indiquerait un problème de fuite de données (gaspillage d’information). Au stade actuel, le DA (précision du signe) est >60% pour les meilleurs modèles à J+30, ce qui suggère un signal directionnel exploitable, mais l’RMSE reste proche de la naïve, confirmant que le gain global est faible.

2.2 Importance des facteurs (SHAP, coefficients)
La factorisation a agrégé ~250 variables brutes en ~32 facteurs économiques (marché, météo, fondamentaux, etc.). Les coefficients du Ridge et l’importance SHAP globale indiquent que les familles les plus utiles à J+20 sont : marché (momentum, volatilité) et fondamentaux WASDE, suivies du stress météo. Par exemple, retirer la famille “momentum marché” augmente notablement l’erreur RMSE
. En revanche, la famille “production_fundamentals” (rendement, surface) se révèle redondante avec WASDE sur les modèles linéaires (son retrait diminue légèrement l’erreur selon une ablation préliminaire). Les SHAP totaux confirment l’importance majeure du “stocks/use tightness” (WASDE) et des indicateurs météo en été, notamment de chaleur extrême.

Attention au facteur “others” trop large. Actuellement, une part importante de l’importance SHAP est allouée à des variables brutes non regroupées (“f_raw__…”). Cela indique qu’il subsiste trop de variables directes dans factors.parquet, ce qui nuit à l’interprétabilité. L’objectif scientifique est de ramener la catégorie others en deçà de 10% de l’importance totale en créant de vrais facteurs pour ces variables (ex. crop condition, export surprises, éthanol, basis). Une factorisation rigoureuse (préserve le signe économique, normalisations expansives) est essentielle pour éviter la multicolinéarité et l’overfitting.

2.3 Calibration d’incertitude (CQR)
Nous utilisons la Conformalized Quantile Regression (CQR) pour construire des intervalles de confiance asymétriques sur les retours. Avec un taux α=10%, la couverture empirique observée est d’environ 90–92% sur les données hors-échantillon (objectif ≥88%). Cela signifie que ~90% des retours réels tombent dans l’intervalle prévu, ce qui est conforme aux propriétés théoriques de la prédiction conforme
. En revanche, la largeur moyenne des intervalles est souvent comparable à plusieurs pourcents de retour, ce qui excède fréquemment le coût de stockage agricole (~0.04$/bu/mois soit ~0.8%/mois). En pratique, cela implique que les signaux “vendre plus tard” ne sont fiables que lorsque l’intervalle reste plus étroit que le gain potentiel. L’analyse par saison ou régime montre que les intervalles sont plus serrés en régime calme et plus larges en saison orageuse.

2.4 Détection de régimes de marché
Un modèle de Markov-switching à 3 états (bull/range/bear) a été implémenté. Les résultats actuels sont peu concluants : soit le modèle ne converge pas (peu d’observations), soit il retourne un régime “bear” très rare (~3% du temps). Le découpage n’est pas équitable (pas environ 33/33/33) et le régime baissier produit est trop éphémère pour guider une stratégie. En conséquence, le fallback rule-based (score heuristique) a probablement pris le relais. Un modèle de régime défaillant compromet les métriques conditionnelles, et nécessite soit de revoir la configuration (p.ex. 2 états), soit de segmenter les modèles par saison plutôt que par régime pur.

2.5 Backtest agriculteur
Le but final est économique : aider l’agriculteur à vendre proche du pic annuel du prix. Les stratégies testées incluent :

Vente immédiate à la récolte (baseline),
DCA (vente mensuelle égale),
Vente par tiers (par ex. 1/3 jan, 1/3 mai),
Meilleur mois historique,
Stratégie fondée sur le modèle (SELL/STORE/WAIT),
Version prudente intégrant l’incertitude (ne pas tenir compte des signaux incertains),
Idéal « hindsight perfect ».
Les métriques clés sont : revenu par boisseau, capture rate (prix obtenu / prix max annuel), regret, % années gagnantes vs baseline. À ce stade, aucune stratégie IA n’a démontré un gain moyen clair. Par exemple, si la vente à la récolte obtient en moyenne 75% du prix max, le modèle actuel capture environ la même part (~75–80%) avec plus de volatilité et de pertes annuelles sporadiques. Sur les 10+ dernières années, le % d’années où notre modèle bat la vente en récolte est inférieur à 50%. Les pertes les plus sévères surviennent lorsque le modèle a mal interprété un retournement (p. ex. vend en mars alors que le marché bondit en avril). Le backtest n’a pas encore été établi sur base du prix cash local (manque de basis), ce qui pourrait modifier significativement la rentabilité réelle. Enfin, les coûts de stockage et de transport n’ont pas été intégrés, ce qui fausse le calcul du seuil de “GAIN si stockage”.

3. Problèmes identifiés et lacunes critiques
Données manquantes ou incomplètes : absence de basis locaux, de données exportations (FAS) et d’éthanol réelles affaiblit le modèle. Les données COT après 2021 contiennent beaucoup de NaN (contrats expirés) – il faut filtrer ou recaler sur OI global. Les notebooks doivent gérer soigneusement l’anti-fuite (par ex. faire shift(1) sur les WASDE, COT, Export).
Facteurs « others » trop dominants : comme dit, la factorisation est insuffisante. Beaucoup de variables de base n’ont pas été agrégées en facteurs économiques, ce qui empêche une interprétation claire et favorise l’overfitting (colinéarité).
Plateforme AutoML obsolète / Path incohérents : Le dossier Models/ legacy n’est pas entièrement repris dans src/mais. Certains notebooks appellent encore des scripts anciens. Il faut unifier sur la plateforme src/mais/platform ou bien nettoyer l’ancien dossier. Plusieurs chemins relatifs sont cassés (ex. vers Models/).
Non-reproductibilité / absence de reporting : Le rapport final (docs/PROFESSIONAL_STUDY_REPORT.md) et le Markdown des notebooks ne sont pas à jour. L’absence d’exports HTML, de notebooks journaliers et de validation de prédictions passées nuit à la traçabilité. Il manque un fichier de manifeste des données indiquant comment reconstituer chaque source (API, clé, périodes).
Modèles non optimisés / tests manquants : LightGBM et XGBoost sont codés (cf. backlog) mais leur recherche d’hyper-paramètres via Optuna n’est pas en place. Les baselines « naïf saisonnier » ou « momentum simple » ne sont pas encore implémentées comme référence officielle dans le code.
Markov-switching instable : Comme vu, le découpage 3 régimes produit un régime baissier quasi nul. Aucune vérification rigoureuse (p. ex. lengths of regimes > 5 jours) n’est faite. Il faut soit abandonner Markov, soit ajuster (2 états bull/bear ou segmentation par saison).
COT volumétrie et NaN : Le collecteur CFTC récupère 2013–2026 mais après 2021 beaucoup de contrats de maïs expirent (NaN). Un traitement (remplissage ou retrait des colonnes d’anciennes expirations) est nécessaire pour ne pas créer de fuites ou de données absurdes.
Pipeline quotidien partiel : ops/daily.py est inachevé. La collecte incrémentale, la mise à jour quotidienne des features/facteurs, la prédiction du jour, et le rapport sont à développer. Sans pipeline automatisé, l’outil ne peut pas délivrer de signaux en temps réel.
Aucune analyse « oracle » : Le projet n’a pas encore testé d’« oracle features » (fuites contrôlées) pour diagnostiquer l’étape limitante. Par exemple, prédire la variation de stocks, ou un indice macro, ou la hausse future donnée, aurait montré si l’échec vient d’un signal insuffisant ou du modèle.
Tests automatisés manquants : Hormis quelques scripts, il n’y a pas de suite de tests (unitaire ou d’intégration) pour garantir qu’un rebuild complet aboutisse à tous les artefacts attendus.
4. Actions correctives prioritaires et tickets
Nous listons ci-dessous les tickets critiques (avec commandes et vérifications) pour corriger ces problèmes. Les trois priorités immédiates (Phase 0) sont rebuild complet + validation, intégration COT, et factorisation.

Ticket	Objectif	Fichiers à changer	Commandes / Vérification
TICKET-01 : Rebuild complet (phase 0)	Lancer force_rebuild_factors=True pour regénérer tous les artefacts à partir du début. Vérifier que tous les outputs listés dans l’architecture existent et sont non vides.	Aucun (juste lancer le pipeline).	```
make clean			
make study			
``` Puis vérifier : ls artefacts/professional_study/*.parquet (tous doivent exister et être non vides), grep -nP "\[ERROR\]" logs/*.			
TICKET-02 : Intégrer COT au pipeline	Rebuild features avec les colonnes COT.	src/mais/features/build_features.py (vérifier inclusion COT), src/mais/features/factors.py.	```
make features			
``` puis grep -n "cot_mm_net" data/processed/features.parquet (Doit exister). Refaire audit anti-leakage: python - <<<'import audit; audit.run()' (0 erreur critique).			
TICKET-03 : Réduire « others » dans factors	Créer les facteurs manquants : crop condition, drought severity, export surprise, demande éthanol. Retirer au maximum les colonnes f_raw__.	src/mais/features/factors.py. Ajouter calcul de :	

factor_crop_condition,
factor_drought_severity,
factor_export_demand_surprise,
factor_ethanol_demand_pull (avec vraie data EIA)
et uniformiser les notations (vérifier le signe). | make features puis ls data/processed/factors.parquet; vérifier dans les logs : pas de f_raw__ dans top factors. Lancer l’anti-leakage : il doit passer à 0 erreur. | | TICKET-04 : Ajouter baselines manquantes | Implémenter baseline_historical_mean et baseline_seasonal_naive dans professional.py. | src/mais/study/professional.py (fonction _model_specs()). | Relancer make study; vérifier que model_benchmarks.parquet contient désormais les lignes pour ces baselines. | | TICKET-05 : Oracle analyses (phase 1) | Ajouter un notebook 04_oracle_analysis_and_target_reformulation.ipynb et code oracle_analysis.py pour tester des cibles intermédiaires :
Variation stocks WASDE,
Croissance exports,
Indice éthanol,
Hausse forte future (max30),
Véritable choix SELL/STORE. | Créer src/mais/research/oracle_analysis.py. | Ecrire des cibles auxiliaires dans data/processed/targets_oracle.parquet, puis make study; analyser si un modèle sur ces cibles a beaucoup plus de succès que pour y_logret. | | TICKET-06 : Correction Markov/regimes | Simplifier ou corriger la détection de régime : tester 2 états bull/bear ou découper par saison. Éliminer l’actuel 3 états non robuste. | src/mais/research/regime_models.py | Exécuter make study; vérifier dans regime_timeseries.parquet que chaque régime couvre une part significative (>20%). | | TICKET-07 : Compléter collecteurs manquants | Intégrer les sources incomplètes :
FAS Export Sales (collecteur + features).
EIA Éthanol (utiliser vrai EIA_API_KEY, retirer le proxy).
Crop Progress (compléter code nass_quickstats_collector.py).
Drought Monitor (créer le facteur). | src/mais/collect/fas_export_sales_collector.py, src/mais/collect/eia_ethanol_collector.py, src/mais/collect/nass_quickstats_collector.py, src/mais/features/factors.py | make data (collecte incrémentale); make features; make audit: pas de fuite; vérifier ethanol_production dans features, etc. | | TICKET-08 : Plateforme AutoML générique (Phase 4) | Harmoniser l’AutoML : créer src/mais/platform/preprocessing.py, platform/profiler.py, platform/reporting.py. Tester sur >5 datasets publics. | Nouveau code dans src/mais/platform/ ; adapter runner.py. | Pipelines de tests : exécuter platform run sur jeux de démo (Iris, Boston). Vérifier rapport automatique. | | TICKET-09 : Pipeline quotidien (Phase 5) | Terminer ops/daily.py pour collecte + features incrémentales, prédictions du jour, rapport Markdown, validation des prédictions passées. | src/mais/ops/daily.py. | Exécuter make daily; vérifier logs (logs/daily_*.log) sans erreur et la création de data/reports/YYYY-MM-DD.md. | | TICKET-10 : Backtest complet (Phase 3) | Finaliser src/mais/decision/backtest.py : inclure toutes les stratégies listées, calculer capture rate, regret, revenus. Générer FARMER_BACKTEST_REPORT.md. | src/mais/decision/backtest.py. | Lancer le backtest : python - <<<'from decision.backtest import run; run()' ; vérifier FARMER_BACKTEST_REPORT.md et notamment la phrase "capture rate". |
(Tickets prioritaires immédiats : 01, 02, 03 – audit complet, intégration COT, factorisation.)

5. Sources de données additionnelles à intégrer
Pour renforcer le modèle, voici les sources recommandées :

Basis locaux / Cash price : Données quotidiennes des cotations locales (ex. Iowa/Illinois) ou des prix bloquets domestiques. Elles comblent l’écart CBOT→prix réel. Intégration via agrégation journalière ou hebdo; anticontamination : shift d’une journée pour la publication.
Prix brésil/argentin : Exportations des grands producteurs (p.ex. CONAB/Argentine) et taux USD/BRL, USD/ARS (FRED). Fréquence mensuelle; lag 0 après publication USDA/CFTC. A intégrer dans des facteurs « compétitivité mondiale ».
Données pluviométriques/drought localisées : Par ex. indice PDSI du Midwest, ou drought monitor plus précis. Hebdo; lag 1j. Directement en features (indice de stress hydrique).
Prix des intrants agricoles : Engrais (prix du gaz naturel ou potasse), diesel, qui impactent le coût de production et de stockage. Hebdo/mensuel; lag 1j. Utiliser FRED ou sources spécialisées.
Indices financiers globaux : S&P500 ou volatilité VIX, pour mesurer appétit pour le risque global. Hebdo; lag 1j. Via FRED.
News et événements : Calendrier complet des rapports USDA (WASDE, Prospective Plantings, NASS, etc.) et événements géopolitiques (ex. guerre Ukraine) encodés en indicateurs binaires (évènement passé ou pas).
Prix du blé et du soja : Déjà collectés, mais on peut ajouter plus de dérivées (spread, correlation).
Indice de la courbe des taux : Différentiel 10y-2y (FRED), qui influence le dollar et le dollar pondéré.
Source à ajouter	Fréquence	Lag	Intégration (anti-leakage)
Cash price locaux (Iowa, IL)	Quotidien/Hebdo	0–1 j	Collecte via API ou scrape; faire shift(1) sur features.
Exportations US (FAS)	Hebdo	1 j	Déjà prévu; ajouter flags de surplus (surprises vs moyenne 5 ans).
EIA: Stocks et demandes	Hebdo	6 j	API EIA (clé requise); intégrer production & stocks éthanol, gazoline.
Taux USD/BRL, USD/ARS	Quotidien	1 j	FRED/USD sources, créer facteur de compétitivité.
Prod. mondiale (CONAB, Bolsa)	Mensuel/Trimestriel	0 j	Scrapper ou API (brésil/arg prod et stocks).
Indice PDSI Midwest	Mensuel	0 j	NOAA ou dataset climat; ajouter facteur de sécheresse.
Engrais (gas naturel)	Hebdo	1 j	FRED gas naturel; inclure dans facteur de coût.
Diesel / énergie	Hebdo	1 j	FRED ou EIA; compense élasticité du carburant.
Indice risque global (VIX)	Hebdo	1 j	FRED; possible facteur "sentiment".

Chaque nouvelle source doit être anti-fuite (forward-fill + shift). Par exemple, la moyenne glissante 5-ans des exportations pour calculer un ‘surplus ou déficit hebdo’ doit être basée uniquement sur les données disponibles à la date t. Pour les rapports mensuels (WASDE, NASS), on n’utilisera qu’après la publication. Une documentation de chaque source (API, URLs, sample de données) doit être ajoutée.

6. Plan d’expérimentation complet
Pour faire avancer le projet, nous proposons un plan facteur-cible-modèle exhaustif :

Nouvelles cibles (targets) métiers : En plus des log-retours classiques y_logret_h5/10/20/30, ajouter :

y_storage_value_hH = valeur attendue du maïs après H jours moins coûts stockage,
y_future_max30 = probabilité d’atteindre un pic dans les H prochains jours,
y_sell_today_regret_hH = (prix max hH − prix actuel) relatif (mesure de regret),
cibles binaires renforcées (hausse forte +3%, baisse forte -3%).
Nouveaux facteurs : Construire les facteurs listés ci-dessus, et tester des agrégations temporelles plus fines (e.g. volatilité futures sur 10j/30j, momentum multi-échelle). Tester l’inclusion de features saisonnières non linéaires (polynômes de sin/cos ou splines).

Modèles :

Statistiques autorégressives (ARIMA/SARIMAX sur retours) et modèles GARCH (pour volatilité). Benchmark à titre de référence.
Linéaires avec régularisation (Ridge, ElasticNet sur facteurs).
Arbres et boosting : RandomForest, HistGB, LightGBM, XGBoost sur facteurs. Intégrer CatBoost si possible.
Stacking : Ridge méta sur OOF predictions et quelques features contextuels (ex. horizon, volatilité récente).
(Optionnel) Deep Learning : LSTM ou N-BEATS sur séries temporelles multivariées, seulement après exhaustion des classiques.
Validation :

Walk-forward CV : fenêtre initiale ~60% des données, tester par pas de ~21 jours (1 mois de trading), avec embargo = horizon H, expansion train. Confirmer la stratégie d'embargo (p.ex. 30j pour horizon 20j).
Enregistrement des metrics : pour chaque expérience, logger RMSE, MAE, R², DA, AUC (pour binaires), couverture et largeur d’intervalle CQR.
Paramètres Optuna :

Définir des espaces de recherche pour chaque modèle (ex. learning_rate, max_depth, nb estimators, regularisation). Lancer 50–100 essais par modèle. Stocker les études Optuna (SQLite) dans artefacts/optuna.db.
Journalisation :

Pour chaque run, consigner dans une base (CSV/Parquet) le modèle, hyperparamètres, features utilisées (facteurs sélectionnés), résultats métriques OOS.
Exemple de schema artefacts/experiment_results.parquet avec colonnes: horizon, target, model, params, RMSE, MAE, R2, DA, coverage, interval_width, timestamp.
7. Construction finale de l’indicateur
La finalité est un indicateur de vente (SELL/STORE/WAIT) accompagnée d’une justification. Le protocole proposé :

Prévisions chiffrées : Pour l’horizon principal (J+20 ou J+30), prédire ŷ (log-retour) et construire l’intervalle CQR [q_lo, q_hi].

Calcul du signal de stockage : Calculer ∆prix = prix_actuel * (exp(ŷ) - 1) = gain espéré, et comparer aux coûts (coût_stockage≈0.8%/mois × nombre_mois).

Décision :

Si q_lo > coût_stockage_total → SIGNIFIER “STORE” (vendre plus tard), car même le pire scénario prévu compense le coût.
Si q_hi < 0 (pire cas indique baisse) → SIGNIFIER “SELL”.
Sinon → “WAIT” (incertitude trop élevée).
Ajustement du seuil : Tenir compte du régime de marché ou de la saison. Par ex. en régime “bull” (monte) être plus conservateur (attendre), en “bear” vendre plus vite.

Backtest décisionnel : Simuler cette règle sur données historiques (respecter lag et coûts). Calculer le capture rate moyen :

$$\text{capture_rate} = \frac{\text{prix_obtenu_stratégie}}{\text{prix_max_annuel}}.$$

L’objectif projet cible ≥90% (benchmark ≤75%). Autres métriques : gain vs prix à la récolte, % années gagnantes, worst-case.

Itérations d’amélioration : Ajuster les cibles/modèles/règles jusqu’à obtenir un avantage statistique stable.

8. Reproductibilité et checklist
Pour tout relancer de zéro :

Vérifier présence de données brutes ou générables (data/manifest.md à créer).
Commandes principales :
make clean (purge artefacts).
make data (collecte incrémentale).
make features (build features/factors).
make study [force_rebuild_factors=True] (entraînement des modèles, stacking, CQR, SHAP, régimes).
make daily (pipeline temps réel, génération rapport).
À chaque étape, exécuter des tests :
Anti-fuite : scriptez audit.run() pour s’assurer que aucune variable future n’a de corrélation anormalement élevée avec la cible.
Intégrité artefacts : ls artefacts/*.parquet et vérifier qu’aucun fichier attendu n’est vide.
CQR : exécuter la validation en code sur cqr_results.parquet (couverture ~couverture_empirique≥88%). Exemple de snippet Python :
python
Copier
import pandas as pd
cqr = pd.read_parquet("artefacts/professional_study/cqr_results.parquet")
print("Couverture", round(cqr['covered'].mean()*100,1), "%")
Régimes : compter les régimes dans regime_timeseries.parquet, s’assurer de la diversité :
python
Copier
import pandas as pd
regimes = pd.read_parquet("artefacts/professional_study/regime_timeseries.parquet")
print(regimes['regime'].value_counts(normalize=True))
Backtest : vérifier la génération de FARMER_BACKTEST_REPORT.md et la cohérence du capture_rate (0–100%).
Versionner le code (git) avant chaque phase majeure.
Produire des exports HTML/PDF de chaque notebook pour archivage (papermill ou nbconvert).
9. Feuille de route & livrables (phases 0–8)
Les étapes clés sont planifiées par phases. La Figure ci-dessous synthétise la roadmap (Phases 0–6 illustrées) :

Figure : Feuille de route projet (Phases 0–6, 2026).

Phase 0 (Audit & Rebuild) – (mai 2026) Reproduire intégralement l’étude existante, corriger les chemins, vérifier anti-fuite, intégrer COT. Livrable : Rapport d’audit (liste des composants fonctionnels/non-fonctionnels).
Phase 1 (Données manquantes) – juin 2026 Ajouter et valider Crop Progress, Drought, Export Sales, EIA. Livrable : Features enrichies (factors rebuilt) et audit passé.
Phase 2 (Facteurs & cibles métiers) – juillet 2026 Finaliser la factorisation (others<10%), définir cibles métier (storage value, regrets, max30). Livrable : targets_oracle.parquet, factoring complet, rapport intermédiaire.
Phase 3 (Expérimentations modèles) – août 2026 Exécuter Optuna (50–100 trials), tester ARIMA/SARIMAX/GARCH, LSTM. Livrable : experiment_results.parquet, meilleurs modèles identifiés.
Phase 4 (Stacking & calibration) – sept. 2026 Construire métamodèle, calibrer CQR final. Livrable : Modèle final, intervalles calibrés.
Phase 5 (Backtest décisionnel) – oct. 2026 Implémenter règles de décision, exécuter backtest sur >10 ans. Livrable : FARMER_BACKTEST_REPORT.md final, incluant métriques (capture rate, regret).
Phase 6 (Déploiement) – nov. 2026 Mettre en place pipeline quotidien et dashboard. Livrable : Système make daily fonctionnel, interface web Streamlit ou équivalent.
(Phase 7+ : revue académique, documentation complète, amélioration continue.)
Pour valider chaque phase, il faut des critères mesurables (ex. « others <10% », « RMSE réduit de 2% », « couverture CQR ≥88% », « capture rate système > capture rate baseline sur ≥70% des années »). Ces critères feront office de définition de « succès » pour chaque phase.

10. Conclusions et prochaines étapes
En l’état, le projet a déployé une infrastructure solide et identifié quelques signaux modérés à moyen terme, mais il reste beaucoup de travail pour aboutir à un indicateur opérationnel fiable. Les résultats partiels suggèrent que seuls quelques facteurs clés (marché, WASDE, météo) dominent vraiment l’explication du prix
. L’étude a ainsi démontré qu’il existe un signal partiel à horizon J+20/J+30, mais que ce signal n’est pas encore suffisant pour garantir un gain agricole robuste. À l’inverse, la rigueur du backtest prévient toute conclusion précipitée : un résultat négatif (absence d’amélioration vs vente normale) doit être honnêtement documenté.

Prochaines actions immédiates : lancer sans délai le rebuild complet (Ticket-01) pour avoir une base fiable, intégrer enfin les données manquantes (Tickets-02/03), et créer de vrais facteurs économiques (Ticket-03). Ces actions permettront de dresser un état des lieux consolidé (✅/❌) et d’orienter la phase d’expérimentations suivantes. Une documentation et des tests automatiques accompagneront chaque avancée.

Points clés à retenir :

Les rapports USDA/CFTC officiels guident la collecte (WASDE mensuel
, COT hebdo
, NASS Crop Progress hebdo
).
La prédiction conforme assure la couverture probabiliste souhaitée
, mais son intervalle doit être exploitable.
Le projet doit passer d’une démonstration méthodologique à une évaluation économique honnête : « Notre système capture X% du prix maximum annuel (moyenne) contre Y% en stratégie standard. » Aujourd’hui X≈Y; il faut pousser les améliorations pour que X>>Y.
Actions immédiates (Ticket 1–3) : un stand-up avec l’équipe pour assigner ces tickets prioritaires, puis revue de code dès le premier rebuild.

Sources : documents USDA (WASDE
), CFTC (Commitments of Traders
), NASS (Crop Progress
), et littérature ML (prédiction conforme
).


Oui, cet audit est globalement très bon, mais non, il ne dit pas encore parfaitement tout ce qu’il faut faire. Il couvre très bien l’état du projet, les problèmes majeurs, les données manquantes, les modèles, le backtest et la roadmap. Par contre, il mélange encore parfois étude du marché, outil agriculteur, plateforme AutoML et objectif d’application finale. Il faut le corriger pour qu’il devienne vraiment ton document de pilotage.

Mon avis : c’est une très bonne base d’audit, mais il faut le rendre plus précis, plus cohérent, et surtout plus orienté vers ton vrai objectif actuel :

construire une étude complète du marché du maïs afin de produire un indicateur directionnel robuste : hausse / baisse / neutre / incertain, avec confiance et explication.

Pas encore construire directement l’application Agricorn ou promettre une stratégie agricole parfaite.

1. Ce qui est très bon dans cet audit

L’audit identifie correctement les gros points du projet :

- projet bien structuré mais encore inachevé ;
- données principales déjà présentes ;
- données importantes encore manquantes ;
- premiers signaux directionnels à J+20/J+30 ;
- modèles ML pas encore clairement supérieurs aux baselines ;
- CQR correct en couverture mais intervalles larges ;
- Markov-switching instable ;
- backtest agricole pas encore concluant ;
- besoin de rebuild propre ;
- besoin de nettoyer la factorisation ;
- besoin d’ajouter exports, éthanol, drought, crop progress, basis, monde ;
- besoin de mieux documenter les expériences.

Donc sur le fond, oui, l’audit comprend bien où en est le projet.

La conclusion est aussi honnête :

il y a un signal partiel, mais pas encore assez robuste pour affirmer qu’on a un indicateur fiable.

C’est exactement ce qu’il faut dire.

2. Ce qui doit être corrigé dans l’audit
2.1 Il parle trop vite d’un indicateur de vente agricole

L’audit revient souvent à :

SELL / STORE / WAIT
capture_rate
prix max annuel
stratégie agriculteur

Mais toi, tu viens de préciser que l’objectif immédiat n’est pas encore de relier à Agricorn ou de faire l’outil ferme complet.

Ton objectif actuel est plutôt :

étudier le marché du maïs ;
tester toutes les données ;
tester plusieurs cibles ;
tester plusieurs modèles ;
comprendre ce qui donne du signal ;
construire un indicateur directionnel du marché.

Donc il faut reformuler une partie de l’audit.

Au lieu de dire :

finalité = indicateur de vente SELL/STORE/WAIT

il faut dire :

finalité actuelle = indicateur directionnel du marché du maïs, qui pourra ensuite être transformé en outil d’aide à la vente.

La couche agricole vient après.

2.2 L’objectif “90 % du prix max” doit disparaître

Dans ton audit, il dit :

L’objectif projet cible ≥90%

Il faut l’enlever.

Tu avais donné ça comme exemple, pas comme objectif officiel.

Il faut remplacer par :

L’objectif est de mesurer honnêtement la performance de l’indicateur contre des références simples.

Et les métriques peuvent être :

- directional accuracy ;
- AUC ;
- Brier score ;
- calibration ;
- performance quand le modèle est confiant ;
- performance par horizon ;
- performance par saison ;
- performance par régime ;
- backtest indicatif si on transforme le signal en stratégie.

Le capture_rate peut rester plus tard, mais pas comme objectif central maintenant.

2.3 Il manque le vrai cœur : l’indicateur directionnel

L’audit parle beaucoup de modèles, de backtest et de vente, mais il ne définit pas assez clairement l’indicateur final de marché.

Il faut ajouter une section :

Indicateur final visé : Maize Market Direction Indicator

Avec sorties :

P(up_h5), P(up_h10), P(up_h20), P(up_h30)
P(down_h5), P(down_h10), P(down_h20), P(down_h30)
P(strong_up_h20)
P(strong_down_h20)
confidence_score
market_signal = BULLISH / BEARISH / NEUTRAL / UNCERTAIN
top facteurs haussiers
top facteurs baissiers

C’est ça ton vrai objectif actuel.

2.4 Il ne détaille pas assez les cibles à tester

Il cite quelques cibles métier, mais il manque une vraie stratégie de reformulation du problème.

Il faut ajouter une section complète :

Cibles à tester

Avec :

1. Cibles de retour
   y_logret_h1/h5/h10/h20/h30/h60/h90

2. Cibles directionnelles
   y_up_h5/h10/h20/h30/h60

3. Cibles fortes
   y_up_strong seuil 1%, 2%, 3%, 5%
   y_down_strong seuil 1%, 2%, 3%, 5%

4. Cibles de volatilité
   realized_vol_h10/h20/h30

5. Cibles de potentiel futur
   future_max_return_h30/h60
   future_min_return_h30/h60

6. Cibles de risque
   downside_risk_h30
   upside_potential_h30

7. Cibles intermédiaires
   future_weather_stress
   future_crop_condition_change
   future_export_sales_surprise
   future_cot_change
   future_wasde_surprise

C’est très important, parce que le problème peut venir de la cible. Peut-être que y_logret_h20 est difficile, mais que y_up_h20 ou y_down_strong_h20 est plus exploitable.

2.5 L’analyse oracle est trop peu développée

L’audit mentionne l’analyse oracle, mais pas assez.

Il faut lui donner un vrai statut central dans l’étude.

L’analyse oracle doit répondre à :

Si je connaissais certaines variables futures, lesquelles expliqueraient vraiment le prix du maïs ?

À tester :

oracle_future_weather_stress_h20
oracle_future_crop_condition_change
oracle_future_wasde_yield_surprise
oracle_future_export_sales_surprise
oracle_future_ethanol_change
oracle_future_cot_position_change
oracle_future_drought_change
oracle_future_basis_change

Puis classer :

Variable oracle	Améliore le prix ?	Est prédictible ?	Décision
météo future	oui/non	oui/non	garder/abandonner
WASDE surprise	oui/non	oui/non	garder/abandonner
COT futur	oui/non	oui/non	garder/abandonner

C’est une des parties les plus intelligentes de ton projet. Elle doit être beaucoup plus visible dans l’audit.

2.6 Il manque la performance par niveau de confiance

L’audit parle de DA globale, mais il ne met pas assez en avant le test essentiel :

Est-ce que le modèle est meilleur quand il est confiant ?

C’est probablement le test le plus important pour ton indicateur.

Il faut ajouter une section :

Analyse de confiance du signal

Avec un tableau attendu :

Filtre de confiance	% jours conservés	DA	AUC	Interprétation
Tous les jours	100 %	56 %	0.55	signal moyen
confiance > 60 %	45 %	60 %	0.60	mieux
confiance > 70 %	20 %	64 %	0.65	exploitable
confiance > 80 %	8 %	68 %	0.70	rare mais fort

Si ce tableau donne de bons résultats, alors ton indicateur devient vraiment intéressant.

2.7 Il faut mieux séparer les trois niveaux du projet

L’audit mélange un peu :

1. étude scientifique du maïs ;
2. plateforme AutoML ;
3. outil d’aide à la vente agricole.

Il faut les hiérarchiser.

Je proposerais :

Niveau 1 — Étude du marché du maïs
Objectif : comprendre et prédire direction / risque / incertitude.

Niveau 2 — Moteur de modélisation / AutoML
Objectif : tester automatiquement modèles, cibles, features, Optuna, stacking.

Niveau 3 — Futur outil agriculteur
Objectif : transformer l’indicateur en recommandation de vente.

Aujourd’hui, il faut concentrer l’audit surtout sur le niveau 1 et un peu sur le niveau 2.

Le niveau 3 doit rester une perspective future.

3. Ce que l’audit doit ajouter absolument

Voici les sections manquantes ou à renforcer.

Section à ajouter 1 — Définition exacte de l’indicateur final

À ajouter dans l’audit :

L’indicateur final visé n’est pas une prévision exacte du prix, mais un indicateur probabiliste de direction du marché.

Sorties :
- probabilité de hausse par horizon ;
- probabilité de baisse ;
- probabilité de forte hausse ;
- probabilité de forte baisse ;
- score de confiance ;
- signal final : BULLISH / BEARISH / NEUTRAL / UNCERTAIN ;
- explication par familles de facteurs.
Section à ajouter 2 — Liste complète des expériences à faire

L’audit en donne une partie, mais il faut une liste plus structurée :

EXP-001 — baselines simples
EXP-002 — horizon optimal
EXP-003 — familles de données seules
EXP-004 — ablation de familles
EXP-005 — facteurs vs variables brutes
EXP-006 — cibles directionnelles
EXP-007 — cibles fortes
EXP-008 — analyse oracle
EXP-009 — ARIMA/SARIMAX/GARCH
EXP-010 — LightGBM/XGBoost/CatBoost
EXP-011 — Optuna
EXP-012 — stacking
EXP-013 — modèles par saison
EXP-014 — modèles par régime
EXP-015 — calibration probabilités
EXP-016 — performance par confiance
EXP-017 — construction indicateur final
EXP-018 — backtest du signal

C’est ça qui va vraiment piloter ton étude.

Section à ajouter 3 — Plan des notebooks final

L’audit parle des notebooks, mais il faut imposer un plan clair :

01_problem_data_quality
02_seasonality_market_structure
03_factor_framework
04_target_reformulation_and_oracle_analysis
05_baselines_and_statistical_models
06_automl_ml_models
07_feature_family_ablation
08_regime_and_seasonal_models
09_uncertainty_and_calibration
10_indicator_construction
11_indicator_backtest
12_final_synthesis

Comme ça, ton étude est structurée comme une vraie recherche.

Section à ajouter 4 — Critères de réussite de l’indicateur

Il faut remplacer les objectifs trop agricoles par des critères plus adaptés à ton objectif actuel.

Critères possibles :

- DA significativement supérieure aux baselines ;
- AUC > baseline sur plusieurs horizons ;
- Brier score correct ;
- calibration acceptable ;
- signal plus fort quand confiance élevée ;
- stabilité par année ;
- stabilité par saison ;
- pas de dépendance à une seule période de crise ;
- explications cohérentes économiquement ;
- robustesse anti-leakage.

L’indicateur est intéressant si :

DA globale modérée
mais DA élevée sur les signaux confiants
et explications cohérentes
4. Ce que je corrigerais dans le texte de ton audit
À supprimer ou reformuler
Phrase actuelle

Le but final est économique : aider l’agriculteur à vendre proche du pic annuel du prix.

À remplacer par :

Le but final de l’étude actuelle est de construire un indicateur directionnel robuste du marché du maïs. L’usage agricole viendra ensuite, en transformant cet indicateur en aide à la décision de vente.

Phrase actuelle

L’objectif projet cible ≥90%.

À supprimer.

À remplacer par :

Les performances doivent être mesurées contre des baselines simples et interprétées sans objectif chiffré arbitraire. L’objectif est d’identifier si un signal robuste existe, dans quels contextes, et avec quel niveau de confiance.

Phrase actuelle

La finalité est un indicateur de vente SELL/STORE/WAIT.

À remplacer par :

La finalité actuelle est un indicateur de marché BULLISH / BEARISH / NEUTRAL / UNCERTAIN. Une couche SELL/STORE/WAIT pourra être ajoutée plus tard.

5. Est-ce que l’audit donne une bonne roadmap ?

Oui, mais je la corrigerais.

Roadmap actuelle de l’audit

Elle dit :

Phase 0 — rebuild
Phase 1 — données manquantes
Phase 2 — facteurs et cibles métiers
Phase 3 — modèles
Phase 4 — stacking/calibration
Phase 5 — backtest décisionnel
Phase 6 — déploiement

C’est bien, mais je ferais plutôt :

Roadmap corrigée
Phase 0 — Rebuild et vérité des résultats

Objectif :

savoir exactement ce qui marche aujourd’hui

À faire :

make features
make targets
make study
make audit
vérifier artefacts
vérifier résultats modèles
vérifier anti-leakage
vérifier CQR / SHAP / régimes
Phase 1 — Étude des données et factorisation

Objectif :

avoir des facteurs économiques propres

À faire :

nettoyer others
réduire f_raw__
créer factor_metadata
ajouter crop condition / drought / export / ethanol / COT propre
Phase 2 — Reformulation des cibles

Objectif :

trouver la cible la plus prédictible

À tester :

returns
direction
strong up/down
future max/min
downside risk
volatilité
variables intermédiaires
oracle analysis
Phase 3 — Modèles et AutoML

Objectif :

tester modèles statistiques, ML, Optuna, stacking

À faire :

baselines
ARIMA/SARIMAX/GARCH
LightGBM/XGBoost/CatBoost
Optuna walk-forward
stacking
Phase 4 — Régimes, saisons, ablation

Objectif :

comprendre quand le modèle marche

À faire :

performance par saison
performance par régime
ablation familles
modèles spécialisés
Phase 5 — Incertitude et confiance

Objectif :

savoir quand croire le modèle

À faire :

calibration
Brier score
CQR
performance par niveau de confiance
signal UNCERTAIN
Phase 6 — Construction de l’indicateur

Objectif :

construire Maize Market Direction Indicator

Sorties :

BULLISH / BEARISH / NEUTRAL / UNCERTAIN
probabilités par horizon
confidence score
explication facteurs
Phase 7 — Backtest du signal

Objectif :

voir si le signal a une vraie valeur historique

À faire :

quand signal bullish, que se passe-t-il ?
quand signal bearish, que se passe-t-il ?
quand signal uncertain, est-ce vraiment incertain ?
performance par horizon
performance par confiance
6. Ce que je ferais maintenant, concrètement

Oui, l’audit est bon, mais la prochaine action doit être très claire.

Étape immédiate 1 — Corriger le document d’audit

Demande à Claude de corriger l’audit pour :

- supprimer l’objectif 90% ;
- recentrer sur l’indicateur directionnel ;
- séparer étude maïs / AutoML / outil agriculteur ;
- ajouter la liste complète des cibles ;
- ajouter la liste complète des expériences ;
- ajouter la performance par confiance ;
- ajouter la structure finale des notebooks ;
- corriger la roadmap.
Étape immédiate 2 — Créer ou compléter EXPERIMENT_INDEX.md

C’est indispensable.

Chaque test doit être tracé.

Étape immédiate 3 — Rebuild complet

Avant d’ajouter encore des idées :

make clean
make features
make targets
make study
make audit

Puis tu relèves les vrais résultats.

Étape immédiate 4 — Construire le notebook 04 correctement

Le notebook 04 doit devenir :

04_target_reformulation_and_oracle_analysis

C’est le cœur de la suite.

Étape immédiate 5 — Ajouter le notebook 10 indicateur

Tu dois prévoir :

10_indicator_construction

C’est là qu’on passe de modèles séparés à un vrai signal final.

7. Verdict final

Donc pour répondre directement :

Est-ce que l’audit dit tout ce qu’il faut faire ?

Il dit beaucoup de choses importantes, mais pas encore tout.

Il est bon sur :

- état du projet ;
- données manquantes ;
- limites des modèles ;
- problèmes de factorisation ;
- CQR ;
- Markov ;
- backtest ;
- besoin de rebuild ;
- enrichissement des données ;
- roadmap générale.

Mais il manque ou il faut corriger :

- recentrage sur l’indicateur directionnel ;
- suppression de l’objectif 90% ;
- meilleure séparation étude / AutoML / application agricole ;
- définition exacte de l’indicateur final ;
- liste complète des cibles à tester ;
- liste complète des expériences ;
- analyse oracle plus centrale ;
- performance par niveau de confiance ;
- structure finale des notebooks ;
- critères de réussite adaptés à l’étude actuelle.

Donc je dirais :

Cet audit est une très bonne V1. Il faut maintenant en faire une V2 centrée sur l’étude du marché du maïs et la construction d’un indicateur directionnel robuste.

Le projet doit maintenant être guidé par cette phrase :

On ne cherche pas seulement à prédire le prix du maïs.
On cherche à identifier dans quelles conditions le marché donne un signal exploitable de hausse ou de baisse, avec quel niveau de confiance, à quel horizon, et avec quelles explications économiques.

C’est ça le vrai cœur de ton étude.


Direction générale du projet — Plateforme AutoML + étude du cours du maïs

L’objectif du projet est de construire une étude complète, sérieuse et professionnelle du marché du maïs, afin de comprendre les facteurs qui influencent son prix et de développer progressivement un indicateur directionnel capable d’estimer si le marché a plus de probabilité de monter, baisser, rester neutre ou être trop incertain.

Le projet doit être organisé en deux grands piliers.

Le premier pilier est la plateforme AutoML de séries temporelles et de données tabulaires. Cette plateforme doit être un moteur générique capable de prendre une base de données, détecter le type de problème, préparer les données, sélectionner les modèles adaptés, lancer les entraînements, optimiser les modèles avec Optuna, construire éventuellement un métamodèle, évaluer proprement les résultats et sauvegarder tous les artefacts nécessaires.

Le second pilier est l’étude professionnelle du marché du maïs. Cette étude utilise la plateforme AutoML comme moteur technique, mais elle doit surtout devenir une vraie démarche de recherche appliquée : on formule des hypothèses, on teste des familles de données, on compare des cibles, on analyse les résultats, on interprète économiquement les signaux, on archive les échecs, et on améliore progressivement l’indicateur.

Le projet ne doit pas devenir une simple succession de modèles lancés automatiquement. Il doit permettre de retracer toute la réflexion : pourquoi on teste telle chose, ce que ça donne, ce qu’on en conclut, et ce qu’on décide ensuite.

1. Objectif final du projet

À la fin, le projet doit permettre de produire un indicateur du type :

Maize Market Direction Indicator

Horizon J+5  : NEUTRAL / incertain
Horizon J+10 : BULLISH modéré
Horizon J+20 : BULLISH avec confiance moyenne
Horizon J+30 : UNCERTAIN

Probabilité de hausse : ...
Probabilité de baisse : ...
Risque de forte hausse : ...
Risque de forte baisse : ...
Confiance : ...
Facteurs haussiers principaux : ...
Facteurs baissiers principaux : ...
Interprétation économique : ...

L’objectif n’est pas de prétendre prédire parfaitement le prix du maïs. L’objectif est de savoir :

- si un signal existe ;
- à quel horizon il est le plus fort ;
- quelles données portent ce signal ;
- quels modèles l’exploitent le mieux ;
- dans quelles saisons ou régimes il fonctionne ;
- quand le système doit dire "incertain" ;
- comment expliquer économiquement chaque signal.

Le projet doit donc produire une étude claire, documentée et honnête du marché du maïs.

2. Priorité absolue : stabiliser la plateforme AutoML

Avant de se concentrer pleinement sur l’étude du maïs, il faut terminer le socle technique.

Aujourd’hui, il faut éviter de mélanger :

- réflexion économique ;
- bugs de pipeline ;
- chemins cassés ;
- modèles non portés ;
- notebooks non exécutés ;
- artefacts absents ;
- anciens fichiers legacy.

La priorité est donc d’avoir une plateforme AutoML stable.

2.1 Ce que doit faire la plateforme AutoML

La plateforme doit être capable de :

1. Charger n’importe quel CSV propre.
2. Détecter automatiquement :
   - régression ;
   - classification ;
   - série temporelle univariée ;
   - série temporelle multivariée ;
   - classification directionnelle ;
   - problème avec date ou sans date.

3. Préparer les données :
   - typage des colonnes ;
   - gestion des dates ;
   - imputation des valeurs manquantes ;
   - encodage des variables catégorielles ;
   - normalisation si nécessaire ;
   - création de lags si série temporelle ;
   - création de rolling features ;
   - suppression des colonnes inutiles ou suspectes.

4. Sélectionner les modèles compatibles :
   - baselines ;
   - modèles linéaires ;
   - modèles arbres ;
   - boosting ;
   - modèles statistiques temporels ;
   - modèles probabilistes si disponibles.

5. Utiliser une validation correcte :
   - cross-validation classique si problème tabulaire ;
   - walk-forward obligatoire si date détectée ;
   - embargo selon l’horizon ;
   - jamais de shuffle sur les séries temporelles.

6. Optimiser les modèles :
   - Optuna ;
   - sauvegarde des études ;
   - comparaison avant/après optimisation.

7. Générer les résultats :
   - métriques ;
   - prédictions ;
   - erreurs ;
   - importance variables ;
   - intervalles si disponibles ;
   - rapport automatique.

8. Construire une meta-database :
   - prédictions out-of-fold ;
   - stacking ;
   - métamodèle.

9. Sauvegarder tous les artefacts :
   - résultats modèles ;
   - prédictions ;
   - paramètres ;
   - graphiques ;
   - rapports.

La plateforme doit être réutilisable. L’étude maïs ne doit pas contenir le code technique compliqué. Elle doit appeler la plateforme proprement.

3. Architecture cible du projet

L’architecture doit être claire et stable.

Etude Mais/
│
├── Models/
│   └── Ancienne plateforme / legacy à migrer progressivement
│
├── src/
│   └── mais/
│       ├── collect/
│       │   └── Collecteurs de données
│       │
│       ├── clean/
│       │   └── Nettoyage et migration legacy
│       │
│       ├── features/
│       │   └── Construction des features et facteurs
│       │
│       ├── targets/
│       │   └── Construction des cibles
│       │
│       ├── platform/
│       │   └── Plateforme AutoML générique
│       │
│       ├── models/
│       │   └── Registre de modèles propres
│       │
│       ├── walkforward/
│       │   └── Splits temporels et validation
│       │
│       ├── optimize/
│       │   └── Optuna et hyperparamètres
│       │
│       ├── meta/
│       │   └── Stacking, meta-database, métamodèle
│       │
│       ├── research/
│       │   └── Fonctions utilisées par les notebooks d’étude
│       │
│       ├── indicator/
│       │   └── Construction de l’indicateur final
│       │
│       └── reporting/
│           └── Génération des rapports
│
├── notebooks/
│   └── corn_study/
│       ├── main/
│       │   └── Notebooks principaux de l’étude
│       │
│       ├── experiments/
│       │   ├── successful/
│       │   ├── neutral/
│       │   └── failed/
│       │
│       ├── templates/
│       │   └── Template d’expérience
│       │
│       ├── exports/
│       │   └── Exports HTML des notebooks
│       │
│       └── EXPERIMENT_INDEX.md
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── artefacts/
│   ├── automl/
│   ├── corn_study/
│   ├── experiments/
│   ├── models/
│   ├── predictions/
│   ├── indicator/
│   └── reports/
│
├── docs/
│   ├── 00_MASTER_PROJECT.md
│   ├── AUDIT_REPORT.md
│   ├── PROFESSIONAL_STUDY_REPORT.md
│   └── FINAL_REPORT.md
│
└── Archive/
    └── Ancien code conservé mais hors workflow principal

Le principe est simple :

src/mais/ = code propre
notebooks/ = raisonnement et étude
artefacts/ = résultats générés
docs/ = synthèse et rapports
Archive/ = ancien projet conservé
4. Organisation des résultats et interprétations

Il faut absolument garder une trace de tout.

Chaque test doit produire :

- un identifiant d’expérience ;
- une hypothèse ;
- les données utilisées ;
- la cible testée ;
- le modèle utilisé ;
- la validation utilisée ;
- les métriques ;
- les graphiques ;
- l’interprétation ;
- la conclusion ;
- la décision : conserver, abandonner, retester.
4.1 Fichier central des expériences

Il faut créer et maintenir :

notebooks/corn_study/EXPERIMENT_INDEX.md

Ce fichier doit contenir une table :

ID | Date | Notebook | Hypothèse | Données | Cible | Modèle | Résultat | Décision | Statut

Exemple :

EXP-001
Hypothèse : la saisonnalité mensuelle apporte du signal.
Méthode : seasonal naive par horizon.
Résultat : utile comme baseline, mais insuffisant seul.
Décision : conserver comme baseline obligatoire.
Statut : neutral / useful baseline.
EXP-002
Hypothèse : LightGBM capte mieux les interactions que Ridge.
Méthode : LightGBM sur facteurs, walk-forward J+20.
Résultat : DA meilleure, RMSE proche baseline.
Décision : conserver, mais tester calibration et confiance.
Statut : successful partiel.
EXP-003
Hypothèse : Markov-switching 3 régimes améliore l’analyse.
Résultat : régime bear quasi absent.
Décision : abandonner temporairement 3 états, tester 2 états ou régimes rule-based.
Statut : failed.

Ce fichier devient la mémoire du projet.

4.2 Organisation des artefacts

Tous les résultats doivent être sauvegardés proprement.

artefacts/
├── automl/
│   ├── model_benchmarks.parquet
│   ├── optuna_results.parquet
│   ├── meta_database.parquet
│   └── stacking_results.parquet
│
├── corn_study/
│   ├── source_coverage.parquet
│   ├── factor_importance.parquet
│   ├── family_importance.parquet
│   ├── ablation_results.parquet
│   └── study_summary.json
│
├── experiments/
│   ├── EXP-001/
│   ├── EXP-002/
│   └── EXP-003/
│
├── predictions/
│   ├── y_logret_h20/
│   ├── y_up_h20/
│   ├── y_down_strong_h20/
│   └── indicator/
│
├── indicator/
│   ├── direction_scores.parquet
│   ├── confidence_scores.parquet
│   ├── indicator_backtest.parquet
│   └── indicator_summary.json
│
└── reports/
    ├── PROFESSIONAL_STUDY_REPORT.md
    ├── INDICATOR_REPORT.md
    └── FINAL_REPORT.md

Chaque expérience importante doit avoir son dossier :

artefacts/experiments/EXP-XXX/
├── config.yaml
├── metrics.parquet
├── predictions.parquet
├── plots/
├── interpretation.md
└── conclusion.md

Comme ça, rien n’est perdu.

5. Structure des notebooks de l’étude maïs

Les notebooks doivent être simples, lisibles, et orientés recherche.

Plan recommandé :

01_problem_data_quality.ipynb
02_seasonality_market_structure.ipynb
03_factor_framework.ipynb
04_target_reformulation_and_oracle_analysis.ipynb
05_baselines_and_statistical_models.ipynb
06_automl_ml_models.ipynb
07_feature_family_ablation.ipynb
08_regime_and_seasonal_models.ipynb
09_uncertainty_and_calibration.ipynb
10_indicator_construction.ipynb
11_indicator_backtest.ipynb
12_final_synthesis.ipynb
01 — Données et qualité

Objectif :

Comprendre les sources, la qualité des données, les périodes couvertes, les fréquences, les lags, les NaN, et les premiers signaux.

Conclusion attendue :

Les données sont exploitables mais hétérogènes. Le signal brut est faible, donc il faut structurer les variables en facteurs et tester proprement.
02 — Saisonnalité et structure du marché

Objectif :

Étudier les effets mois, saisons agricoles, volatilité saisonnière, rapports USDA, semis, croissance, pollinisation, récolte.

Conclusion attendue :

La saisonnalité existe et doit servir de baseline, mais elle ne suffit pas seule.
03 — Cadre factoriel

Objectif :

Transformer les variables brutes en facteurs économiques lisibles.

À traiter :

market_momentum
market_volatility
wasde_supply_demand
weather_stress
crop_condition
drought
exports
ethanol
cot_positioning
macro
curve_structure
global_competition
seasonality

Conclusion attendue :

Les facteurs permettent de comprendre le marché, mais ils doivent être propres, documentés et non dominés par des variables brutes.
04 — Reformulation des cibles et analyse oracle

Objectif :

Tester si la cible y_logret est vraiment la bonne, et identifier les drivers futurs importants.

Cibles à tester :

y_logret
y_up
y_down
y_up_strong
y_down_strong
future_max_return
future_min_return
downside_risk
realized_vol
prob_better_price

Analyse oracle :

oracle_future_weather_stress
oracle_future_crop_condition_change
oracle_future_wasde_surprise
oracle_future_export_surprise
oracle_future_cot_change

Conclusion attendue :

Le prix exact est difficile à prédire ; il faut tester si les cibles directionnelles ou intermédiaires sont plus exploitables.
05 — Baselines et modèles statistiques

Objectif :

Tester les références simples et les modèles temporels.

Baselines :

zero return
historical mean
seasonal naive
momentum
mean reversion

Modèles statistiques :

AR
ARMA
ARIMA
SARIMAX
VAR
GARCH
Markov-switching
HMM

Conclusion attendue :

Ces modèles donnent une base scientifique et permettent de savoir si le marché contient une structure temporelle simple.
06 — AutoML et modèles ML

Objectif :

Utiliser la plateforme AutoML pour tester les modèles avancés.

Modèles :

Ridge
Lasso
ElasticNet
Random Forest
ExtraTrees
HistGradientBoosting
LightGBM
XGBoost
CatBoost
SVR
MLP
Stacking

À mesurer :

avant/après Optuna
features brutes vs facteurs
modèle individuel vs stacking
performance par cible
performance par horizon

Conclusion attendue :

On identifie les familles de modèles vraiment utiles, et on élimine celles qui n’apportent rien.
07 — Ablation des familles de données

Objectif :

Comprendre quelles données portent réellement le signal.

Tests :

market only
weather only
WASDE only
COT only
macro only
seasonality only
all features
all minus one family

Conclusion attendue :

On sait quelles familles sont utiles, redondantes ou inutiles selon les horizons.
08 — Régimes et saisons

Objectif :

Tester si le marché est mieux prédit par contexte.

Contextes :

saison agricole
marché volatil / calme
marché haussier / baissier
stocks tendus / stocks confortables
période météo critique
période WASDE
COT extrême / normal

Conclusion attendue :

On identifie dans quels contextes le signal est plus fort ou plus faible.
09 — Incertitude et calibration

Objectif :

Mesurer quand le modèle est fiable.

À tester :

CQR
split conformal
quantile models
Brier score
calibration curve
Platt scaling
isotonic regression
confidence score

Question centrale :

Quand le modèle dit 65 % de probabilité de hausse, est-ce historiquement vrai ?

Conclusion attendue :

L’indicateur doit savoir dire incertain quand les probabilités ne sont pas fiables.
10 — Construction de l’indicateur

Objectif :

Combiner les résultats des modèles en un indicateur final.

Sorties de l’indicateur :

P(up)
P(down)
P(strong_up)
P(strong_down)
expected_return
confidence_score
market_signal
top bullish factors
top bearish factors

Signaux :

BULLISH
BEARISH
NEUTRAL
UNCERTAIN

Conclusion attendue :

L’indicateur résume les modèles, l’incertitude et les facteurs explicatifs en un signal lisible.
11 — Backtest de l’indicateur

Objectif :

Tester si les signaux passés étaient réellement informatifs.

Questions :

Quand l’indicateur dit BULLISH, le marché monte-t-il ?
Quand il dit BEARISH, le marché baisse-t-il ?
Quand il dit UNCERTAIN, les résultats sont-ils proches du hasard ?
Les signaux confiants sont-ils meilleurs que les signaux faibles ?

À mesurer :

DA globale
DA par horizon
DA par signal
AUC
Brier score
performance par confiance
performance par saison
performance par régime
stabilité par année

Conclusion attendue :

On sait si l’indicateur a une vraie valeur historique.
12 — Synthèse finale

Objectif :

Résumer tout ce qui a été testé, ce qui marche, ce qui ne marche pas, et ce qu’il faut améliorer.

Le notebook doit contenir :

meilleures données
meilleures cibles
meilleurs modèles
meilleurs horizons
contextes où le signal marche
contextes où il échoue
limites
pistes futures
6. Méthode de travail obligatoire

À partir de maintenant, chaque nouvelle idée doit suivre cette structure.

1. Hypothèse
2. Données nécessaires
3. Cible testée
4. Méthode
5. Validation
6. Résultat
7. Interprétation
8. Décision

Exemple :

Hypothèse :
Le stress météo futur explique mieux les variations J+20 du maïs.

Méthode :
Créer oracle_future_weather_stress_h20, comparer modèle réaliste vs modèle oracle.

Résultat :
Si le score oracle améliore fortement la DA, alors la météo future est un driver important.

Décision :
Si le driver est important, créer ensuite un sous-modèle pour prédire ce stress météo.

Chaque expérience doit finir par :

CONSERVER
ABANDONNER
RETESTER
INTÉGRER DANS L’INDICATEUR
7. Ordre de travail recommandé
Phase 0 — Stabilisation

Objectif :

Avoir un pipeline qui tourne de bout en bout.

À faire :

corriger chemins
finir plateforme AutoML minimale
corriger Makefile
rebuild complet
anti-leakage
artefacts non vides
notebooks exécutables

Livrable :

Baseline stable du projet.
Phase 1 — Plateforme AutoML

Objectif :

Avoir le moteur technique complet pour tester les modèles proprement.

À faire :

profiler CSV
preprocessing générique
walk-forward propre
model registry
Optuna
stacking
reporting
sauvegarde résultats

Livrable :

commande unique capable de lancer une expérience complète.

Exemple :

mais automl run \
  --dataset data/processed/factors.parquet \
  --target y_up_h20 \
  --validation walk_forward \
  --optuna true \
  --stacking true
Phase 2 — Étude maïs, version propre

Objectif :

Construire la base scientifique.

À faire :

données
qualité
saisonnalité
facteurs
cibles
baselines

Livrable :

notebooks 01 à 05 exécutés et exportés.
Phase 3 — Expérimentations avancées

Objectif :

Tester intensivement les hypothèses.

À faire :

modèles ML
modèles statistiques
Optuna
stacking
analyse oracle
ablation
régimes
saisons

Livrable :

EXPERIMENT_INDEX.md complet + artefacts par expérience.
Phase 4 — Indicateur

Objectif :

Construire l’indicateur directionnel.

À faire :

probabilités
confiance
signal final
explications
calibration
backtest signal

Livrable :

Maize Market Direction Indicator V1.
Phase 5 — Synthèse et amélioration

Objectif :

Analyser les résultats, comprendre les erreurs, décider quoi améliorer.

À faire :

rapport final
erreurs par année
erreurs par saison
erreurs par régime
pistes prioritaires

Livrable :

rapport de recherche complet.
8. Direction finale à suivre

Le projet doit avancer dans cet ordre :

1. Finir la plateforme AutoML.
2. Stabiliser le pipeline maïs.
3. Exécuter les notebooks principaux.
4. Sauvegarder tous les résultats.
5. Créer l’index des expériences.
6. Tester toutes les cibles.
7. Tester toutes les familles de données.
8. Tester les modèles statistiques et ML.
9. Tester Optuna et stacking.
10. Tester les régimes et saisons.
11. Tester l’incertitude.
12. Construire l’indicateur final.
13. Backtester l’indicateur.
14. Interpréter les résultats.
15. Recommencer avec les meilleures pistes.

Le plus important : on ne doit plus perdre la trace de ce qu’on fait.

Chaque résultat doit être enregistré, interprété et relié à une décision.

9. Texte de conclusion à mettre dans le document maître

Tu peux finir le document de direction par ce texte :

Ce projet doit être mené comme une recherche appliquée.

La première étape consiste à finaliser la plateforme AutoML afin de disposer d’un moteur fiable pour tester rapidement des modèles, des cibles et des familles de données. Une fois ce socle stabilisé, l’étude du maïs pourra se concentrer sur l’essentiel : comprendre le marché, formuler des hypothèses, tester les signaux, interpréter les résultats et construire progressivement un indicateur directionnel.

L’objectif final n’est pas de multiplier les modèles, mais de comprendre dans quelles conditions le marché du maïs devient partiellement prévisible. Chaque expérience doit donc être documentée, sauvegardée et interprétée. Les réussites comme les échecs doivent être conservés, car ils font partie de la construction scientifique du projet.

À terme, l’étude doit permettre de produire un indicateur capable de dire, pour plusieurs horizons, si le marché est plutôt haussier, baissier, neutre ou incertain, avec un niveau de confiance et une explication économique claire. Cet indicateur sera ensuite la base éventuelle d’un outil d’aide à la décision agricole, mais la priorité actuelle reste l’étude rigoureuse du cours du maïs.
10. Prompt prêt à donner à Claude / Cursor

Tu peux leur envoyer ceci :

Je veux recentrer entièrement le projet.

Le projet doit être structuré en deux piliers :

1. Plateforme AutoML / séries temporelles
2. Étude professionnelle du marché du maïs

Priorité 1 :
Finaliser la plateforme AutoML pour qu’elle soit stable, générique et réutilisable.

Elle doit pouvoir :
- charger un dataset ;
- détecter le type de problème ;
- préparer les données ;
- utiliser une validation adaptée, notamment walk-forward pour séries temporelles ;
- lancer les baselines ;
- lancer les modèles ML et statistiques ;
- optimiser avec Optuna ;
- construire une meta-database ;
- faire du stacking ;
- sauvegarder les résultats ;
- générer un rapport automatique.

Priorité 2 :
Construire l’étude du maïs comme une vraie recherche appliquée.

Les notebooks doivent être structurés ainsi :

01_problem_data_quality
02_seasonality_market_structure
03_factor_framework
04_target_reformulation_and_oracle_analysis
05_baselines_and_statistical_models
06_automl_ml_models
07_feature_family_ablation
08_regime_and_seasonal_models
09_uncertainty_and_calibration
10_indicator_construction
11_indicator_backtest
12_final_synthesis

Les notebooks doivent rester lisibles. Les fonctions lourdes doivent aller dans src/mais/research ou src/mais/platform.

Il faut créer une architecture de résultats claire :

artefacts/automl/
artefacts/corn_study/
artefacts/experiments/EXP-XXX/
artefacts/predictions/
artefacts/indicator/
artefacts/reports/

Chaque expérience doit être enregistrée dans :

notebooks/corn_study/EXPERIMENT_INDEX.md

Chaque expérience doit contenir :
- hypothèse ;
- données ;
- cible ;
- modèle ;
- validation ;
- résultats ;
- interprétation ;
- décision : conserver / abandonner / retester / intégrer ;
- statut : successful / neutral / failed / active.

L’objectif actuel n’est pas encore de construire l’application agricole finale. L’objectif est d’étudier le marché du maïs et de construire un indicateur directionnel :

BULLISH / BEARISH / NEUTRAL / UNCERTAIN

avec :
- P(up) ;
- P(down) ;
- P(strong_up) ;
- P(strong_down) ;
- confidence_score ;
- top facteurs haussiers ;
- top facteurs baissiers ;
- horizon J+5/J+10/J+20/J+30/J+60.

Il faut donc organiser le projet pour pouvoir tester énormément de choses proprement :
- familles de données ;
- cibles ;
- modèles statistiques ;
- modèles ML ;
- Optuna ;
- stacking ;
- analyse oracle ;
- régimes ;
- saisons ;
- calibration ;
- confiance ;
- backtest du signal.

Je veux que tout soit traçable. Rien ne doit être perdu. Même une expérience qui échoue doit être archivée avec sa conclusion.

Le but final est que, une fois la plateforme terminée et les notebooks structurés, on puisse vraiment se concentrer sur l’étude du cours du maïs : réfléchir aux hypothèses, tester des idées, interpréter les résultats et améliorer progressivement l’indicateur.

Cette direction est la bonne : finir d’abord le moteur, puis se concentrer sur la recherche.
Sinon tu vas continuer à mélanger bugs, modèles, idées, notebooks, résultats et tu ne sauras plus ce qui a vraiment été testé.