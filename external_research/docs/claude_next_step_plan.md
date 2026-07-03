# Plan d'étape 2 — Lecture des sources et fiches

Date : 2026-06-12
Pré-requis : audit initial validé (`claude_initial_audit.md`), `review_priority.csv` en place.
Périmètre étape 2 : lecture + fiches + enrichissement de la matrice d'idées. **Toujours aucun code EXT, aucun backtest, aucune feature.**

## 0. Corrections rapides en ouverture (30 min)

1. Fusionner les 4 doublons seed/découverts dans `source_inventory_catalog.csv` (PAPER001, PAPER007, PAPER015, PAPER016 ← fiches découvertes correspondantes).
2. Supprimer ou marquer `N/A` les 7 fiches brevets placeholders (requêtes manuelles) ; relancer la recherche brevets si Google Patents répond.
3. Exclure `scripts/__pycache__/` du versionnement.

## 1. Ordre de lecture des sources KEEP_CORE (blocs thématiques)

Traiter un bloc à la fois, une source à la fois (protocole étape B). L'ordre numérique fin est la colonne `claude_order` de `review_priority.csv`.

### Bloc A — Cadre fondamental et discipline de benchmark (ordres 1–7)
- `mindymallory/PriceAnalysis` (repo) + PAPER018 (livre compagnon) : basis, hedge, éthanol, DDG, stockage, ending stocks.
- PAPER027 (random walk / futures comme prévision) : fonde EXT025, baseline de tout le programme.
- `mindymallory/RollFutures`, PAPER015 (+ doublon à fusionner), `facundoallia/calendar-spread` : courbe, roll, spreads (EXT005/EXT006/EXT034).

### Bloc B — USDA / WASDE / événements (ordres 8–17)
- `fdfoneill/wasdeparser` (EXT026, infra vintage), PAPER003, PAPER004, PAPER005, PAPER006.
- Synthèses : « What do we know about USDA reports » (EXT032), « When does USDA info have most impact », options corn post-USDA, effets calendaires WASDE, réaction aux rapports US/Brésil.

### Bloc C — Crop progress / météo / prime météo (ordres 18–29)
- Lehecka 2014 (EXT027), simulation crop progress hebdo, « crop condition reports are not enough » (EXT019).
- PAPER007 + PAPER008 (prime météo, EXT018), PAPER001 Singh (EXT001/EXT002), CropProphet archive de prévisions (EXT033), PAPER012/PAPER013 extrêmes (EXT020), `ccaspar/weather_commodities`.

### Bloc D — COT / positionnement (ordres 30–31)
- `NDelventhal/cot_reports` (EXT003), PAPER022 (ratios spéculatifs).

### Bloc E — Éthanol / DDG / stockage / basis (ordres 32–40)
- PAPER017 (EXT004), corn-crush location (EXT029), distillers grains (EXT030), biofuel-storage Carter et al. (EXT031), PATENT007 (séchage/coûts stockage), PATENT010 (basis futures), PAPER016 + doublon (EXT013), PAPER014.

### Bloc F — Forecasting corn comparables (ordres 41–50)
- PAPER011 (EXT024), PAPER002, PAPER029 (AGRICAF), `PrayusShrestha/crop-price-prediction`, `cstainbrook/Corn-Futures-Capstone`, `SeemaKanuri/...`, challenge Helios, satellite-USDA Piette (EXT028), Sentinel-2, news-attention corn.

### Bloc G — KEEP_METHOD (ordres 51–73, après les blocs cœur)
- Volatilité : PAPER009 (GARCH corn), PAPER042 (Samuelson saisonnier), PAPER010, PAPER037 (HAR).
- Benchmarks : PyTrendFollow, quantiacs, mlm, engineerinvestor (EXT011) ; OU + PAPER041 (EXT012) ; regime-bench + PAPER035 (EXT017/EXT035) ; saisonnalité SirFrancisG.
- Combinaison/sélection : PAPER031 (BMA, EXT014), PAPER032 (SHAP/MI, EXT015), PAPER028 (revue).
- Modèles : nbeatsx + PAPER020 (EXT016), PAPER030 (TSFM, EXT021), PAPER039 (Nelson-Siegel), CY-Bench (EXT037).

### MANUAL_REVIEW (ordres 80+, 10 min chacun)
- « Explosions of corn futures prices » : lire l'abstract, trancher.
- `alekhya-puli14/...` : ouvrir le notebook, trancher.
- 7 requêtes brevets : relancer ou clore le volet brevets découverts.

## 2. Fiches à remplir en premier (10 premières)

Dans `source_cards/`, dans cet ordre : REPO003 (PriceAnalysis), PAPER018, PAPER027, REPO004 (RollFutures), PAPER015, fdfoneill/wasdeparser, PAPER003, PAPER005, Lehecka 2014, PAPER007. Chaque fiche se conclut par KEEP / IMPROVE / REJECT / DATA_BLOCKED + idées EXT alimentées.

## 3. Idées EXT à enrichir en premier

| Idée | Enrichissement attendu en étape 2 |
|---|---|
| EXT025 random walk baseline | Spécifier les baselines exactes (RW, RW avec drift, prix futures) et les horizons — prérequis de tous les autres EXT |
| EXT006 roll volume-based | Extraire la règle de roll exacte de RollFutures ; définir le critère « artefacts de roll réduits » |
| EXT026 WASDE vintage | Valider que wasdeparser donne des données datées publication ; sinon marquer DATA_BLOCKED |
| EXT007/EXT008 WASDE features/surprise | Définir le proxy de surprise sans valeurs révisées (dépend EXT026) |
| EXT027 crop progress surprises | Spécifier la climatologie train-only et le timing lundi ; clarifier le recouvrement avec EXT019 (fusion possible) |
| EXT018 prime new-crop | Préciser le mapping contrat décembre et la fenêtre saisonnière |
| EXT001/EXT002 fenêtres météo | Brancher conceptuellement sur l'archive météo interne (V136) ; réalisé = explicatif, prévu = prédictif (leçon V45) |
| EXT033 archive prévisions | Définir les features de révision de prévision testables avec notre journal forward |
| EXT003 COT | Lister les types de rapports et catégories de traders à tester ; vendredi only |
| EXT004 crush éthanol/DDG | Inventorier les séries DDG disponibles et leurs lags ; sinon DATA_BLOCKED partiel |

## 4. Critères de sortie de l'étape 2

- ≥ 25 fiches KEEP_CORE remplies avec verdict.
- `ideas_matrix.csv` enrichie (colonnes notes/feature_family précisées, statuts mis à jour, idées DATA_BLOCKED marquées).
- Une shortlist de 5–8 EXT prêts à être codés (hypothèse claire + données confirmées + baseline définie), proposée comme tickets pour l'étape 3.
- Aucun fichier hors de `external_research/` modifié.

## 5. Rappels de garde-fous

- Une source à la fois, pas d'audit global répété.
- Pas de code EXT avant validation explicite de l'étape 3.
- Toute conclusion d'une source externe est une *hypothèse* tant qu'elle n'a pas survécu à notre protocole OOF interne (cf. étape G du protocole).
- Holdout 2024 interdit sans ticket humain explicite.
- Repos sans licence (PriceAnalysis, RollFutures, crop-price-prediction, AgriJedi, mlm) : idées oui, copie de code/données non.
