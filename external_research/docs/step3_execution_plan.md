# Plan d'exécution — Étape 3 (P0)

Date : 2026-06-12. Périmètre : EXT025, EXT006, EXT026 uniquement. Aucune modification du modèle principal ni des données internes ; tout vit sous `external_research/experiments/external_tests/` et `external_research/results/external_tests/`.

## État des données constaté (audit préalable)

| Donnée | Disponibilité | Conséquence |
|---|---|---|
| CBOT continu (corn OHLCV quotidien) | ✅ `data/interim/database.parquet`, 2000-10→2025-07, source vendeur legacy | EXT025 OK ; EXT006 : pas d'identité de contrat → artefacts mesurables indirectement seulement |
| Contrats CBOT individuels (prix+volume) | ❌ absents (`data/raw/cbot_corn/cbot_corn.csv` quasi vide) | EXT006 CBOT : reconstruction volume-based DATA_BLOCKED |
| Contrats EMA (prix, volume, OI, expiry) | ⚠️ `data/processed/euronext/ema_contract_daily.parquet` : 2010-2024 = front-month seul (~1,09 contrat/date), courbe multi-contrats depuis 2025 | EXT006 : audit des rolls du front historique OK ; roll volume-causal = prototype sur 2025-2026 seulement |
| Séries continues EMA du projet | ✅ `ema_front_continuous_{raw,adjusted}.parquet` etc. | comparaison raw vs adjusted possible |
| WASDE brut vintage | ✅ 210 fichiers txt USDA (2002-03→2025-07) + `csv/wasde/wasde_links_table.csv` avec vraies dates de publication + parse `wasde_txt.csv` | EXT026 : vrai pipeline vintage constructible |
| WASDE quotidien du projet | ⚠️ `data/interim/wasde.parquet` (legacy `wasde_completed.csv`) : `report_date` du parse = 1er du mois, publication réelle ~le 8-12 | **suspicion de fuite ~7-11 jours à auditer — point central de EXT026** |
| Calendrier USDA | ✅ `usda_calendar.parquet` (WASDE/Grain Stocks/Acreage) | croisement des dates |
| Holdout | 2024 verrouillé (règle 12) | évaluations headline arrêtées au 2023-12-31, segment 2024+ rapporté séparément à titre indicatif sans comparaison de modèles |

## Ordre d'exécution

1. **EXT025** (aucune dépendance) → 2. **EXT006** (réutilise la lecture des séries) → 3. **EXT026** (indépendant).

## EXT025 — Benchmarks RW / drift / naïfs

- Scripts : `run_ext025.py` (génère les prédictions), `evaluate_ext025.py` (métriques, DM, comparaisons).
- Séries cibles : CBOT corn_close (2000-2023 headline), EMA front continu raw (2010-2023), basis EMA−CBOT_eur si eurusd disponible dans les données internes (sinon noté).
- Benchmarks : RW (P_t), RW+drift (drift log expandant, passé seulement), Naive Last Return (dernier rendement répété), MA20 (passé seulement). Futures-as-forecast : **DATA_BLOCKED historiquement** (pas de courbe profonde) — noté, démontrable plus tard sur la courbe 2025+.
- Horizons : H5, H10, H20, H30, H40, H90 (jours de bourse).
- Métriques : RMSE, MAE, R², direction accuracy (pour les benchmarks directionnels ; RW = référence sans direction), DM-test vs RW (HAC Bartlett lag h-1, ajustement Harvey).
- Sorties : `predictions_ext025.csv`, `metrics_ext025.csv`, `comparison_ext025.csv`, `dm_tests_ext025.csv`, `README_results.md`.
- Anti-fuite : drift/MA expandants ou roulants passés uniquement ; aucune normalisation globale ; pas de split random ; horizon h jamais chevauché par l'estimation.
- Critères : KEEP si le tableau est produit, stable et reproductible ; REJECT n'a pas de sens ici (pas de claim) ; DATA_BLOCKED si une série cible manque.

## EXT006 — Roll et artefacts de série continue

- Scripts : `run_ext006.py` (construit séries + rolls + prototype), `evaluate_ext006.py` (métriques d'artefacts).
- Volets :
  - V1 EMA historique : extraire les dates de roll du front (changement de `contract_code`), caractériser la règle implicite (days_to_expiry au roll), mesurer les retours des jours de roll vs jours normaux, comparer raw vs adjusted du projet.
  - V2 CBOT : sans identité de contrat — comparer gaps overnight dans les fenêtres de roll présumées (10 derniers jours de bourse de fév/avr/juin/août/nov, échéances H,K,N,U,Z) vs hors fenêtres.
  - V3 prototype causal : sur le segment multi-contrats 2025-2026 EMA, roll « volume J-1 > volume courant J-1 » vs front par expiry ; documenter la divergence.
  - V4 impact basis : taille des sauts de roll EMA rapportée à la vol quotidienne du basis (ordre de grandeur de contamination de basis_z).
- Sorties : `continuous_current.csv`, `continuous_volume_roll.csv` (prototype 2025+), `roll_dates.csv`, `roll_artifacts_metrics.csv`, `roll_comparison_metrics.csv`, `README_results.md`.
- Anti-fuite : décision de roll sur volume J-1 uniquement (prototype) ; pas d'optimisation de paramètres sur la série ; CSV de RollFutures jamais utilisés comme données.
- Critères : KEEP si la série actuelle est validée fiable ; IMPROVE si artefacts réels mais gérables (flags) ; REJECT si la série doit être reconstruite ; DATA_BLOCKED pour le volet reconstruction historique volume-based (attendu).

## EXT026 — Pipeline WASDE vintage

- Scripts : `run_ext026.py` (audit + construction vintage), `validate_ext026.py` (validation 3 rapports historiques vs txt bruts).
- Volets :
  - Clonage `fdfoneill/wasdeparser` (tentative ; notre archive txt interne peut suffire — documenter).
  - Audit anti-fuite de `data/interim/wasde.parquet` : dates de changement de valeur vs vraies dates de publication (links table + calendrier) ; distribution des écarts ; verdict fuite oui/non/ampleur.
  - Construction vintage : `wasde_txt.csv` (valeurs par rapport) × vraies dates de publication → dataset (publication_date, campagne approx., production, yield, beginning/ending stocks, exports, feed_residual, ethanol, stocks_to_use, variations M−M-1, available_from = jour ouvré suivant la publication — règle conservatrice car publication 12h ET intra-séance).
  - Validation : 3 rapports (été 2023-07, automne 2023-11, hiver 2024-01) — valeurs parsées vs texte brut.
- Sorties : `wasde_current_audit.md`, `wasde_vintage_dataset.csv`, `wasde_publication_dates.csv`, `wasde_feature_dictionary.csv`, `wasde_validation_report.md`, `README_results.md`.
- Anti-fuite : une valeur n'existe qu'à partir de sa publication réelle ; jamais de valeur révisée avant publication ; date manquante → premier jour ouvré suivant la date la plus conservatrice documentée ; aucune interpolation.
- Critères : KEEP si le vintage est constructible et validé ; IMPROVE si partiel (variables manquantes) ; DATA_BLOCKED si les dates de publication ne sont pas fiables.

## Risques transverses

- Holdout 2024 : aucune comparaison de modèles sur 2024+ ; segments séparés.
- Aucun écriture hors de `external_research/results/external_tests/`.
- Si une fuite est découverte (EXT026 attendu) : documenter, proposer correction, NE PAS modifier les données internes (ticket projet séparé).
