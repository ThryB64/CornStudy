# Audit initial — Bibliothèque de recherche externe

Date : 2026-06-12
Auteur : Claude Code (étape 1 — audit, classement, plan ; aucun code EXT, aucune modification du modèle principal)

## 1. Verdict global

**PRÊT POUR L'ÉTAPE 2**, avec 4 corrections mineures (aucune bloquante).

La structure préparée par Codex est cohérente, complète et conforme au protocole.
Les comptes annoncés dans le README sont tous vérifiés exacts :
131 sources cataloguées = 11 repos seed + 24 repos découverts + 42 papers seed + 37 papers découverts + 10 brevets seed + 7 enregistrements de requêtes brevets.
131 fiches sources générées (35 repos + 79 papers + 17 brevets). 37 idées EXT (EXT001→EXT037, sans trou).

## 2. Vérification de structure

| Élément attendu | État |
|---|---|
| `external_research/README.md` | ✅ |
| `sources/seed_repositories.yml` (11) | ✅ |
| `sources/seed_papers.yml` (42) | ✅ |
| `sources/seed_patents.yml` (10) | ✅ |
| `sources/discovered_repositories.yml` (24) | ✅ |
| `sources/discovered_papers.yml` (37) | ✅ |
| `sources/discovered_patents.yml` (7) | ⚠️ requêtes manuelles, pas des brevets (Google Patents 503) |
| `matrices/ideas_matrix.csv` (37 idées) | ✅ |
| `matrices/source_inventory.csv` (11 repos scannés) | ✅ |
| `matrices/source_inventory_catalog.csv` (131) | ✅ |
| `matrices/implementation_candidates.csv` (10) | ✅ |
| `docs/instructions_for_claude.md` | ✅ |
| `docs/anti_leak_rules.md` | ✅ |
| `docs/research_protocol.md` | ✅ |
| `experiments/external_tests/README.md` | ⚠️ existe sous `external_research/experiments/external_tests/`, pas à la racine du projet |
| `results/external_tests/README.md` | ⚠️ idem, sous `external_research/results/external_tests/` |

Sur les deux derniers points : la checklist de mission attendait ces dossiers à la racine du projet, mais **tous les documents de méthode (protocole, instructions) référencent de façon cohérente les chemins internes à `external_research/`**. Ce placement interne est en réalité préférable : il garantit la séparation externe/interne exigée par les règles strictes. Recommandation : conserver le placement actuel, ne pas créer de doublons à la racine.

## 3. Ce qui est bien préparé

- **Règles anti-fuite solides et spécifiques** : COT vendredi ≠ mardi, WASDE date de publication réelle, météo prévue ≠ réalisée, climatologie train-only, holdout verrouillé. Cohérentes avec les règles internes du projet (shift(1), z-scores expandants).
- **Protocole en 9 étapes clair** (inventaire → fiche → hypothèse → EXT → baseline → verdict KEEP/IMPROVE/REJECT/DATA_BLOCKED), avec frontière explicite externe/interne.
- **Matrice d'idées riche** : 37 idées avec mécanisme, données requises, horizon, difficulté, risque de fuite et note anti-fuite par ligne.
- **Clonage soigné** : 11/11 repos présents, log de clonage horodaté, récupération sparse intelligente de `mindymallory/PriceAnalysis` ciblée sur les chapitres corn/ethanol/DDG/basis/hedge/stockage.
- **Honnêteté sur les brevets découverts** : l'échec 503 est documenté au lieu de faux résultats.
- **Discovery scorée** : les papers découverts en seconde passe (Lehecka 0.92, corn-crush 0.9, biofuel-storage 0.9) sont de très bonne qualité et corn-spécifiques.

## 4. État des repos GitHub (11/11 présents)

| Repo | Présent | README | Licence | Langage | Notebooks | Scripts | Données | Intérêt | Priorité |
|---|---|---|---|---|---|---|---|---|---|
| mindymallory/PriceAnalysis | ✅ (sparse partiel) | ✅ | ❌ | Quarto/R (12 qmd) | 0 | 0 py | 6 xlsx | Basis/ethanol/DDG/hedge/stockage — cœur de l'étude | **1 — très haute** |
| mindymallory/RollFutures | ✅ | ✅ | ❌ | R (5 R/Rmd) | 0 | 0 py | 1180 csv (contrats corn) | Méthode de roll volume-based (EXT006) | très haute |
| NDelventhal/cot_reports | ✅ | ✅ | ✅ | Python | 0 | 3 | 0 | Accès COT + types de rapports (EXT003) | très haute |
| PrayusShrestha/crop-price-prediction | ✅ | ✅ | ❌ | Python | 2 | 2 | 6 | Corn futures + météo, comparable à nos blocs | haute |
| cchallu/nbeatsx | ✅ | ✅ | ✅ | Python | 3 | 16 | 0 | NBEATSx exogène (EXT016) | moyenne |
| chrism2671/PyTrendFollow | ✅ | ✅ | ✅ | Python | 6 | 35 | 0 | Benchmark trend-following (EXT011) | moyenne |
| YavuzAkbay/Ornstein-Uhlenbeck | ✅ | ✅ | ✅ | Python | 0 | 2 | 0 | Benchmark OU mean-reversion (EXT012) | moyenne |
| quantiacs/strategy-futures-trend-following | ✅ | ✅ | ✅ | Notebook | 1 | 0 | 0 | Benchmark trend simple | moyenne |
| amstrdm/mlm-trend-following | ✅ | ✅ | ❌ | Python | 0 | 1 | 0 | Trend Mount Lucas minimal (3 fichiers) | basse |
| squeeze-team/AgriJedi | ✅ | ✅ | ❌ | Python (app) | 0 | 29 | 4 | Architecture agri-AI, pas de méthode forecast | basse |
| AsyncAlgoTrading/aat | ✅ | ✅ | ✅ | Python/C++ | 0 | 145 | 1 | Framework trading générique | basse |

**PriceAnalysis (repo prioritaire signalé)** : présent et exploitable. Le clone sparse a récupéré les chapitres clés (01 grains, 02 commodity, 04 futures/hedging, 09 prix espace-temps, 10 fondamentaux, 13 forecasting usage, 15 ending stocks, 17 éthanol, 22 séries temporelles) + bibliographie + fichiers Excel. **Pas un problème bloquant.** Limites notées : chapitres intermédiaires absents (03, 05–08, 11–12, 14, 16, 18–21) et pas de fichier de licence → réutilisation d'idées OK, copie de contenu non.

## 5. Risques détectés

1. **Licences absentes** sur 5 repos (PriceAnalysis, RollFutures, crop-price-prediction, AgriJedi, mlm-trend-following) : s'inspirer des méthodes est acceptable, **ne pas copier de code ni de données** de ces repos dans le projet.
2. **Les 1180 CSV de RollFutures** (contrats corn, volumes, DTE) sont tentants comme source de données. Provenance et licence non établies → usage **méthode seulement** ; nos propres données contrats restent la référence.
3. **`discovered_patents.yml` ne contient aucun brevet** (7 URL de recherche manuelle suite au 503). Les 7 fiches brevets correspondantes sont des placeholders sans objet.
4. **4 doublons seed/découverts** : Singh weather (PAPER001), weather premium (PAPER007), nearby-deferred (PAPER015), transmission UE (PAPER016). Risque de double fiche → fusion notée dans `review_priority.csv`.
5. **Schéma hétérogène** : les sources découvertes n'ont pas d'`id` stable (slugs générés par le catalogue, parfois très longs). Tolérable, mais à normaliser si on régénère le catalogue.
6. **Biais de validation externe** : la quasi-totalité des repos découverts à faible étoile n'ont ni évaluation OOF ni baseline — le protocole (étape G) protège déjà contre l'import naïf de leurs conclusions.
7. Cosmétique : `scripts/__pycache__/` versionnable à exclure ; `external_research/` n'est pas encore commité (dossier untracked dans git).

## 6. Corrections nécessaires avant l'analyse complète (étape 2)

1. **Re-exécuter la recherche brevets** (manuellement via les 7 URL sauvegardées ou re-run du script quand Google Patents répond) et remplacer les 7 placeholders ; sinon, acter que le volet brevets se limite aux 10 seeds.
2. **Fusionner les 4 doublons** dans le catalogue (garder l'ID seed, pointer la fiche découverte vers la fiche seed).
3. **Ajouter `__pycache__/` au .gitignore** du dossier (ou nettoyer) avant commit.
4. Optionnel : ajouter une colonne `id` stable aux YAML découverts lors du prochain run de discovery.

Aucune de ces corrections ne bloque le démarrage des lectures KEEP_CORE.

## 7. Vérification de la matrice d'idées (synthèse)

Les 25 idées attendues (EXT001→EXT025) sont toutes présentes, bien formulées (mécanisme + données + horizon + baseline implicite via EXT025), avec risque de fuite identifié ligne par ligne. 12 idées supplémentaires (EXT026→EXT037) issues de la discovery sont cohérentes. Points d'attention par idée :

| Idée | Testable | Données probables | Fuite identifiée | Statut recommandé |
|---|---|---|---|---|
| EXT001/002 météo fenêtres+lags | ✅ | ✅ (archive météo V136 interne) | ✅ réalisée vs prévue | prioritaire |
| EXT003 COT | ✅ | ✅ (cot_reports) | ✅ vendredi vs mardi | prioritaire |
| EXT004 ethanol/DDG crush | ✅ | ⚠️ DDG histoire incertaine | ✅ lags hebdo/mensuels | prioritaire |
| EXT005 spreads de courbe | ✅ | ✅ (contrats H/M/Q/X internes V24) | ✅ | prioritaire |
| EXT006 roll volume-based | ✅ | ✅ | ✅ volume futur interdit | prioritaire |
| EXT007/008 WASDE release+surprise | ✅ | ⚠️ surprise dépend des vintages (EXT026) | ✅ valeurs révisées | prioritaire ; EXT008 conditionné à EXT026 |
| EXT009/010 GARCH/HAR | ✅ | ✅ | ✅ faible | normal |
| EXT011/012 trend/OU benchmarks | ✅ | ✅ | ✅ faible | normal |
| EXT013 transmission UE | ✅ | ⚠️ spot UE requis → risque DATA_BLOCKED | ✅ | normal |
| EXT014/015 BMA/SHAP | ✅ | ✅ (prédictions OOF internes) | ✅ poids/sélection walk-forward | normal |
| EXT016 NBEATSx | ✅ | ✅ | ✅ | différer après baselines |
| EXT017 régimes | ✅ | ✅ | ✅ sélection plein échantillon | normal |
| EXT018 prime new-crop | ✅ | ✅ | ✅ mapping contrat | prioritaire |
| EXT019/027 crop progress/condition | ✅ | ✅ (NASS public) | ✅ lag hebdo lundi | prioritaire (fusion partielle possible : EXT027 raffine EXT019) |
| EXT020 événements extrêmes | ✅ | ✅ | ✅ seuils ex ante | normal |
| EXT021 foundation models | ✅ | ✅ | ⚠️ mémorisation — risque le plus élevé du lot | différer |
| EXT022 NDVI / EXT023 sentiment | ✅ | ⚠️ couverture/horodatage | ✅ | repoussés (low_medium, justifié) |
| EXT024 VAR offre-demande | ✅ | ⚠️ vintages | ✅ | normal |
| EXT025 random walk baseline | ✅ | ✅ | ✅ | **à faire en premier — discipline de tout le programme** |
| EXT026–EXT037 (discovery) | ✅ | variable, signalé par ligne | ✅ | EXT026/EXT027/EXT033 prioritaires |

Remarque : EXT033 (archive de prévisions météo) est l'idée la plus alignée avec l'existant interne (journal de prévisions V136, leçon V45 « le réalisé est pricé par anticipation »).

## 8. Sources prioritaires (top 10 de lecture)

1. `mindymallory/PriceAnalysis` + PAPER018 (cadre fondamental basis/ethanol/stockage)
2. PAPER027 — Reeve & Vigfusson, random walk vs futures (fonde EXT025)
3. `mindymallory/RollFutures` + PAPER015 nearby/deferred (hygiène de courbe, EXT005/EXT006)
4. `fdfoneill/wasdeparser` + PAPER003/004/005 (bloc WASDE, EXT007/EXT008/EXT026)
5. Lehecka 2014 crop progress + « crop condition reports are not enough » (EXT027)
6. PAPER007/PAPER008 prime météo (EXT018)
7. PAPER001 Singh météo/sol ML (EXT001/EXT002)
8. CropProphet weather forecast archive (EXT033)
9. PAPER017 + corn-crush + distillers + biofuel-storage (bloc éthanol/DDG/stockage, EXT004/EXT029/EXT030/EXT031)
10. `NDelventhal/cot_reports` (EXT003)

Le classement complet des 131 sources avec ordre de lecture est dans `matrices/review_priority.csv` (49 KEEP_CORE, 22 KEEP_METHOD, 37 LOW_PRIORITY, 14 REJECT, 9 MANUAL_REVIEW).

## 9. Conclusion

Le dossier est **propre et prêt pour l'étape 2** (lecture des sources et remplissage des fiches), sous réserve des 4 corrections mineures ci-dessus, qui peuvent être traitées en parallèle du début des lectures. Le plan détaillé de l'étape 2 est dans `docs/claude_next_step_plan.md`.
