# EXT026 — Résultats : pipeline WASDE vintage

Date : 2026-06-12. Scripts : `external_research/experiments/external_tests/EXT026_wasde_vintage_pipeline/{run,validate}_ext026.py`.

## Verdict : **KEEP** (pipeline vintage construit et validé) — avec **FUITE DÉTECTÉE dans les données internes actuelles**, correction à proposer en ticket projet séparé.

## Réponses aux questions posées

### 1. Les données WASDE actuelles sont-elles fiables anti-fuite ?

**NON.** Audit de `data/interim/wasde.parquet` (série quotidienne alimentant les colonnes `wasde_*` de la base de features) sur 160 rapports à date de publication réelle connue :

- **143/160 rapports (89 %) ont leurs valeurs visibles AVANT la publication réelle.**
- Lag médian : **−8 jours** (les valeurs du rapport du ~10 du mois apparaissent dès le ~1er-4).
- Cause : l'expansion quotidienne est calée sur `report_date` (= 1er du mois dans le parse legacy) au lieu de la vraie date de publication (~8-12 du mois).
- Détail dans `wasde_current_audit.md` et `wasde_audit_lags.csv`.

**Portée** : toute feature `wasde_*` consommée par des modèles internes a bénéficié d'une avance d'information ~8 jours. À relativiser : V18 avait conclu WASDE NO_GO sur la prime MÊME AVEC cette avance (le négatif reste négatif — une fuite qui n'aide pas renforce le NO_GO). Pour le CBOT en revanche, tout résultat futur utilisant `wasde_*` interne serait optimiste. **Correction proposée (ticket projet, hors périmètre externe)** : recaler l'expansion quotidienne sur `publication_date + 1 jour ouvré` à partir du dataset vintage produit ici.

### 2. Peut-on construire un vrai pipeline vintage ?

**OUI — c'est fait.** Le projet possédait déjà la matière première (210 fichiers txt USDA Cornell 2002-2025, archive interne `data/wasde_raw/` + parse `csv/wasde/wasde_txt.csv`) :

- `wasde_vintage_dataset.csv` : **207 rapports**, 2002-03-12 → 2025-07-11, une ligne par rapport, valeurs telles que publiées, avec `publication_date`, `available_from` (= publication + 1 jour ouvré, règle conservatrice — publication 12h ET intra-séance), campagne marketing approximative, variations M−M-1 (proxy de surprise pour EXT008).
- Dates de publication : 3 sources hiérarchisées — table de liens Cornell (34), calendrier USDA interne `is_wasde_day` (126), fallback conservateur jour-12 (47, soit 23 %, marqués `pub_date_source=fallback_day12`).
- `wasdeparser` (fdfoneill, MIT) cloné dans `external_research/github_repos/` : extrait moins de variables que notre parse interne → conservé comme outil de contre-vérification, notre archive reste la source primaire.

### 3. Validation historique

`wasde_validation_report.md` : 3 rapports (été 2023-07, automne 2023-11, hiver 2024-01), 8 variables chacun — **24/24 valeurs parsées retrouvées textuellement dans les bruts USDA. VALIDATED.**

### 4. Variables prêtes pour EXT007/EXT008

| Prêtes (couverture 100 %) | Partielles | Bloquées/faibles |
|---|---|---|
| production, beginning/ending_stocks, stocks_to_use (publié + recalculé), imports, supply_total, feed_and_residual, food_seed_industrial, domestic_total, exports, use_total, avg_farm_price + toutes les variations M−M-1 | ethanol_byproducts (87 %), dates de publication exactes (77 % réelles, 23 % fallback ±2-4 j) | area_planted/harvested, yield (51 % — absents des rapports d'hiver par construction WASDE) |

### 5. Risque de fuite résiduel du vintage

- 47 rapports en fallback jour-12 : la vraie date est dans [8, 12] du mois historiquement ; le fallback + 1 jour ouvré reste conservateur dans la quasi-totalité des cas. Améliorable en complétant le calendrier USDA officiel (release-dates JSON, collecteur déjà présent dans le projet).
- Divergences links/calendrier observées (ex. wasde1012 : URL datée 15/12 vs calendrier 10/12) : la hiérarchie choisie (links > calendrier) est documentée ; impact limité par `available_from`.
- Le mélange old crop/new crop (mai-septembre, deux campagnes par rapport) : le parse retient une campagne par rapport — la colonne `marketing_year_approx` est une approximation, à raffiner pour EXT008 si la surprise doit être par campagne stricte.

## Fichiers produits

`wasde_current_audit.md`, `wasde_audit_lags.csv`, `wasde_vintage_dataset.csv`, `wasde_publication_dates.csv`, `wasde_feature_dictionary.csv`, `wasde_validation_report.md`.
