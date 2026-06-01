# Tickets — Étude Statistique Complète Maïs CBOT & Euronext EMA

> Créé 2026-05-23. Phase étude post-pivot.  
> Phrase directrice : CBOT explique la tendance mondiale. EMA révèle la prime européenne via le basis.  
> Règle absolue : anti-leakage shift(1), OOF strict, IC95% bootstrap 1000 tirages, BH FDR.  
> Agents ne modifient pas `notebooks/` — chaque ticket notebook crée un module Python + tests + docs + artefacts.

---

## Index

| ID | Titre | Bloc | Priorité | Statut |
|---|---|---|---|---|
| SCOPE-01 | Mise à jour scope projet | Nettoyage | P0 | DONE |
| SCOPE-02 | Archivage modules hors périmètre | Nettoyage | P0 | DONE |
| SCOPE-03 | Correction vocabulaire docs | Nettoyage | P0 | DONE |
| NB-EMA-00 | Module vue d'ensemble projet | Fondations | P0 | DONE |
| NB-EMA-01 | Module audit données EMA v2 | Fondations | P0 | DONE |
| NB-EMA-02 | Module contrats et rolls | Fondations | P0 | DONE |
| NB-EMA-03 | Module séries continues | Fondations | P0 | DONE |
| NB-EMA-04 | Module relation EMA/CBOT | Fondations | P0 | DONE |
| NB-EMA-05 | Module décomposition retour EMA ⭐ | Stat lourdes | P1 | DONE |
| NB-EMA-06 | Module étude résidu EMA ⭐ | Stat lourdes | P1 | DONE |
| NB-EMA-07 | Module basis formel | Stat lourdes | P1 | DONE |
| VALID-GRANGER-01 | Validation Granger OOF ⭐ | Validation | P1 | DONE |
| UTIL-EMA-01 | Fonctions communes statistiques | Utilitaires | P1.5 | DONE |
| NB-EMA-08 | Module benchmark directionnel EMA | Prédictif | P2 | DONE |
| NB-EMA-09 | Module event study grands mouvements | Prédictif | P2 | DONE |
| NB-EMA-10 | Module importance des features EMA | Prédictif | P2 | DONE |
| NB-EMA-11 | Module volatilité EMA (HAR/GARCH) | Prédictif | P2 | DONE |
| NB-EMA-12 | Module prévision prix expérimental | Prédictif | P2 | DONE |
| NB-EMA-13 | Module benchmark hebdomadaire ⭐ | Prédictif | P2 | DONE |
| DATA-EU-01 | Collecteur EC MARS (JRC Agri4cast) ⭐ | Données EU | P3 | DONE |
| DATA-EU-02 | Collecteur Open-Meteo Europe ⭐ | Données EU | P3 | DONE |
| DATA-EU-03 | Collecteur FranceAgriMer / Agreste | Données EU | P3 | DONE |
| DATA-EU-04 | Collecteur ETS CO₂ et TTF enrichi | Données EU | P3 | DONE |
| DATA-WORLD-01 | Enrichissement WASDE EU + Ukraine | Données EU | P3 | DONE |
| NB-EMA-14 | Module rapport de synthèse final | Rapport | P4 | DONE |

---

## BLOC 0 — NETTOYAGE / SCOPE

---

### SCOPE-01 — Mise à jour scope projet

**Priorité :** P0  
**Type :** nettoyage  
**Statut :** DONE  
**Dépendances :** aucune  
**Complexité :** simple

#### Contexte

Le pivot de 2026-05-20 a changé l'objectif du projet de "indicateur opérationnel agriculteur" à "étude statistique complète". Plusieurs fichiers de documentation affichent encore l'ancien objectif. Toute lecture du projet par un tiers ou par un agent crée une confusion sur le vrai objectif.

#### Objectif

Mettre à jour `STATE.md`, `README.md` (si existe) et `PROJECT.md` pour refléter exactement le nouvel objectif. Ajouter la phrase directrice §0.3 de REFLEXION_ETUDE_COMPLETE.md en tête de STATE.md.

#### Fichiers

- `.ai/STATE.md` — remplacer section Mission
- `.ai/PROJECT.md` — mise à jour objectif
- `README.md` (si présent à la racine) — mise à jour intro

#### Tâches

1. Lire `.ai/STATE.md` section "Mission".
2. Remplacer le bloc "Mission — objectif final (pivot 2026-05-10)" par :
   ```
   ## Mission — objectif final (pivot 2026-05-20)
   
   Mener une étude statistique et économique complète du cours du maïs CBOT et Euronext EMA.
   
   Phrase directrice : CBOT explique la tendance mondiale. Euronext EMA ne se prédit pas encore
   bien directement, mais il révèle la prime européenne via le basis. La vraie étude Euronext
   consiste à expliquer le basis, la transmission CBOT→EMA, les périodes de découplage,
   et le résidu européen spécifique.
   
   Ce n'est PAS un indicateur opérationnel agriculteur. C'est une étude scientifique honnête.
   ```
3. Lire `.ai/PROJECT.md` et corriger la description du projet.
4. Vérifier si `README.md` existe à la racine. Si oui, corriger le titre/intro.

#### Critères de validation

- `.ai/STATE.md` ne contient plus "indicateur directionnel" dans la section Mission.
- La phrase directrice est visible dans STATE.md.
- Aucune mention de "BULLISH/BEARISH/UNCERTAIN" dans la section Mission.

#### Outputs

- `.ai/STATE.md` mis à jour
- `.ai/PROJECT.md` mis à jour (si contenu à corriger)

---

### SCOPE-02 — Archivage modules hors périmètre

**Priorité :** P0  
**Type :** nettoyage  
**Statut :** DONE  
**Dépendances :** SCOPE-01  
**Complexité :** simple

#### Contexte

Trois modules Python sont hors périmètre de l'étude actuelle mais représentent du travail à conserver :
- `src/mais/research/storage_targets.py` — cibles de stockage agriculteur
- `src/mais/research/farmer_backtest_v2.py` — backtest agriculteur
- `src/mais/ops/weekly_report.py` — rapport agriculteur hebdomadaire

Les laisser dans le pipeline principal crée de la confusion. Il faut les déplacer dans un dossier `archive/` sans les supprimer.

#### Objectif

Créer `src/mais/research/archive/` et déplacer les 3 modules. Mettre à jour les imports si nécessaire.

#### Fichiers

- `src/mais/research/storage_targets.py` → `src/mais/research/archive/storage_targets.py`
- `src/mais/research/farmer_backtest_v2.py` → `src/mais/research/archive/farmer_backtest_v2.py`
- `src/mais/ops/weekly_report.py` → `src/mais/ops/archive/weekly_report.py`
- `src/mais/research/archive/__init__.py` — créer vide
- `src/mais/ops/archive/__init__.py` — créer vide
- Vérifier les imports dans `src/mais/research/__init__.py`, `src/mais/ops/__init__.py`

#### Tâches

1. Vérifier que les 3 fichiers existent avec `ls`.
2. Créer les dossiers `archive/` avec `__init__.py` vides.
3. Déplacer les fichiers (`mv`).
4. Grep les imports de ces modules dans tout `src/` pour détecter les dépendances brisées.
5. Corriger les imports brisés (changer le chemin ou commenter avec un warning).
6. Depuis la racine du projet : `python -m ruff check src/mais tests`.
7. Depuis la racine du projet : `python -m pytest tests/ -x -q`.

#### Critères de validation

- `ruff check` : 0 erreur
- `pytest` : tous les tests passent
- Les 3 modules ne sont plus dans leur emplacement d'origine
- `src/mais/research/archive/` et `src/mais/ops/archive/` existent

#### Outputs

- Dossiers `archive/` créés avec les modules déplacés

---

### SCOPE-03 — Correction vocabulaire dans les docs

**Priorité :** P0  
**Type :** nettoyage  
**Statut :** DONE  
**Dépendances :** SCOPE-01  
**Complexité :** simple

#### Contexte

Le vocabulaire interdit (§0.2 de REFLEXION_ETUDE_COMPLETE.md) doit être corrigé partout dans `docs/`. Les termes interdits créent de faux claims si lus hors contexte.

**Termes interdits → remplacement :**
- "courbe EMA complète" → "features EMA front, basis, liquidité et fragments de courbe"
- "prévision validée" / "prévision prix EMA validée" → "prévision prix EMA expérimentale"
- "Granger exploitable" / "signal exploitable" (pour EMA→CBOT) → "prometteur, non confirmé OOF"
- "RECOMMANDATION : STOCKER/VENDRE" → supprimer ou reformuler en probabilités
- "indicateur opérationnel" (dans les docs EMA) → "module d'étude"

#### Fichiers

- `docs/EMA_DATA_AUDIT.md`
- `docs/EMA_CBOT_RELATIONSHIP.md`
- `docs/EMA_BASIS_STUDY.md`
- `docs/EMA_FINAL_SYNTHESIS.md`
- Tout autre `docs/*.md` mentionnant ces termes

#### Tâches

1. `grep -rn "courbe EMA complète\|courbe futures EMA complète" docs/` — lister les occurrences.
2. `grep -rn "prévision validée\|prévision prix EMA validée" docs/` — lister.
3. `grep -rn "Granger exploitable\|signal exploitable" docs/` — lister.
4. `grep -rn "RECOMMANDATION" docs/` — lister.
5. Pour chaque occurrence : corriger avec le terme approprié.
6. Ajouter en tête de chaque doc EMA modifié : `> Source exploratoire (Barchart proxy). Résultats expérimentaux.`

#### Critères de validation

- `grep -rn "courbe EMA complète" docs/` retourne 0 résultat
- `grep -rn "Granger exploitable" docs/` retourne 0 résultat
- Tous les fichiers docs/ modifiés ont la mention "expérimental" ou "exploratoire" visible

#### Outputs

- Fichiers `docs/*.md` corrigés

---

## BLOC 1 — P0 FONDATIONS (notebooks 00-04)

> Ces 5 modules sont le prérequis absolu de tout modèle prédictif.  
> Chaque module crée : `src/mais/research/ema_XX.py` + `tests/test_ema_XX.py` + `artefacts/ema_study/XX.json` + `docs/EMA_XX.md`

---

### NB-EMA-00 — Module vue d'ensemble projet

**Priorité :** P0  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** SCOPE-01, SCOPE-02  
**Complexité :** simple

#### Contexte

Le notebook `00_ema_project_overview.ipynb` doit pouvoir afficher le cadrage complet du projet : prix EMA vs CBOT, basis, résultats actuels, roadmap. Ce module Python produit les données et statistiques que le notebook affiche.

#### Objectif

Créer `src/mais/research/ema_project_overview.py` qui produit un JSON de synthèse avec tous les chiffres clés du projet + les données pour les graphiques de cadrage.

#### Fichiers à créer

- `src/mais/research/ema_project_overview.py`
- `tests/test_ema_project_overview.py`
- `artefacts/ema_study/ema_project_overview.json`
- `docs/EMA_00_PROJECT_OVERVIEW.md`

#### Tâches

1. Lire `src/mais/paths.py` pour les chemins.
2. Créer `ema_project_overview.py` avec fonction `build_project_overview()` :
   - Charger `EMA_FRONT_RAW`, `EMA_HARVEST_NOV`, `features.parquet` (colonne `cbot_eur_t`), `ema_cbot_basis`
   - Calculer statistiques descriptives : période, nb jours, prix moyen EMA, prix moyen CBOT EUR/t, basis moyen
   - Charger les résultats connus (depuis `artefacts/`) : DA EXP-BENCH-02, AUC, IC95
   - Produire dict JSON avec : `period`, `n_days`, `ema_stats`, `cbot_stats`, `basis_stats`, `benchmark_results`
3. Fonction `save_overview(output_path)` — sauvegarde JSON.
4. `if __name__ == "__main__"` — exécuter et sauvegarder.
5. Tests : charger le JSON produit, vérifier les clés attendues, vérifier que la période couvre au moins 2014-2023.
6. Rédiger `docs/EMA_00_PROJECT_OVERVIEW.md` avec le tableau des résultats clés actuels.

#### Critères de validation

- `python -m mais.research.ema_project_overview` s'exécute sans erreur
- `artefacts/ema_study/ema_project_overview.json` existe et contient `period`, `n_days`, `benchmark_results`
- `ruff check` : 0 erreur
- Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_project_overview.json`
- `docs/EMA_00_PROJECT_OVERVIEW.md`

---

### NB-EMA-01 — Module audit données EMA v2

**Priorité :** P0  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-00  
**Complexité :** moyen

#### Contexte

EXP-EMA-STUDY-01 a produit un premier audit. Ce module v2 va plus loin : heatmap couverture par contrat × année, distribution des prix par mois (H/M/Q/X), trous de données, comparaison proxy Barchart vs vrais prix Euronext récents (2024-2025). L'objectif est de documenter précisément les limites de la donnée avant tout modèle.

#### Question scientifique

Quelle est la vraie couverture exploitable de la donnée EMA ? Quels contrats, quelles périodes, quels mois sont fiables vs exploratoires ? Quel est l'écart entre proxy Barchart et settlement officiel sur la période de chevauchement ?

#### Objectif

Créer `src/mais/research/ema_data_audit_v2.py` — audit complet avec 6 métriques clés.

#### Fichiers à créer

- `src/mais/research/ema_data_audit_v2.py`
- `tests/test_ema_data_audit_v2.py`
- `artefacts/ema_study/ema_data_audit_v2.json`
- `docs/EMA_01_DATA_AUDIT.md`

#### Tâches

1. Charger `EMA_CONTRACT_DAILY` (4 818 lignes).
2. **Couverture par contrat × année** :
   - Créer tableau pivot : index = année (crop year), colonnes = mois contrat (H/M/Q/X), valeur = nb jours disponibles / nb jours ouvrés attendus
   - Seuil couverture : 80% = acceptable, 60-80% = partiel, <60% = insuffisant
3. **Distribution des prix par mois contrat** :
   - Boxplot stats (min/Q1/median/Q3/max) par mois contrat et par tranche 5 ans
4. **Trous de données** :
   - Lister les gaps > 5 jours ouvrés dans `EMA_FRONT_RAW`
   - Table : date_start, date_end, nb_jours_manquants, cause probable
5. **OI et volume** :
   - OI moyen et max par contrat (H/M/Q/X) et par année
   - % de jours avec OI > 0 par contrat
6. **Comparaison proxy vs officiel** :
   - Charger `EMA_CONTRACT_DAILY` où `source_quality='official'` (si présent)
   - Si overlap avec proxy : calculer corrélation, MAE, biais moyen
   - Sinon : documenter l'absence de données officielles
7. **Verdict final** :
   - Période ML fiable : à déterminer (ex: 2015-2022 si ≥80% couverture)
   - Période exploratoire : reste
   - Période à exclure : si couverture <60% sur contrat principal
8. Sauvegarder JSON structuré avec toutes les métriques.
9. Tests : vérifier que le JSON contient `coverage_matrix`, `gaps`, `verdict_period_ml`.
10. Rédiger `docs/EMA_01_DATA_AUDIT.md` : tableau de couverture, liste gaps, verdict lisible.

#### Critères de validation

- `artefacts/ema_study/ema_data_audit_v2.json` contient `coverage_matrix`, `gaps`, `oi_stats`, `verdict_period_ml`
- Le verdict identifie soit une période ML fiable (ex: "2015-01-01 à 2022-12-31"), soit `"NO_RELIABLE_PERIOD"` si couverture insuffisante — les deux sont valides
- `ruff check` : 0 erreur
- Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_data_audit_v2.json`
- `docs/EMA_01_DATA_AUDIT.md`

---

### NB-EMA-02 — Module contrats et rolls

**Priorité :** P0  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-01  
**Complexité :** moyen

#### Contexte

Le roll audit (DATA-EMA-08, DONE) a produit un rapport texte avec 65 roll details. Ce module formalise l'analyse des rolls pour quantifier précisément leur impact sur les cibles H20/H40/H60. Le résultat clé attendu : % de fenêtres traversant ≥1 roll par horizon.

#### Question scientifique

Dans quelle mesure les rolls biaisent-ils les rendements calculés ? H60 est-il vraiment 100% contaminé par un roll ? Quelle est la distribution des roll gaps et leurs outliers ?

#### Objectif

Créer `src/mais/research/ema_contracts_rolls.py` avec analyse formelle des rolls et impact sur les targets.

#### Fichiers à créer

- `src/mais/research/ema_contracts_rolls.py`
- `tests/test_ema_contracts_rolls.py`
- `artefacts/ema_study/ema_contracts_rolls.json`
- `docs/EMA_02_CONTRACTS_ROLLS.md`

#### Tâches

1. Charger `EMA_CONTRACT_DAILY`, `EMA_FRONT_RAW`, `EMA_FRONT_ADJUSTED`.
2. **Cycles contrats H/M/Q/X** :
   - Pour chaque campagne (crop year), lister les contrats actifs et leurs dates d'expiration
   - Calculer la durée de vie moyenne par mois contrat
3. **Distribution des roll gaps** :
   - Charger les roll gaps depuis `EMA_FRONT_ADJUSTED` (différence raw - adjusted aux dates de roll)
   - Stats : min, Q1, median, Q3, max, nb_rolls, % gaps > 5 €/t, % gaps > 15 €/t
   - Top 10 roll gaps les plus importants (date, gap, contrat_from, contrat_to)
4. **Impact sur les targets** :
   ```python
   for H in [20, 40, 60]:
       for each date t in index:
           window = [t, t+H]
           rolls_in_window = rolls[(roll_date > t) & (roll_date <= t+H)]
           has_roll = len(rolls_in_window) > 0
       pct_windows_with_roll[H] = mean(has_roll)
   ```
   - Résultat clé : H20=?, H40=?, H60=? (attendu: H60 ≈ 100%)
5. **Comparaison raw vs adjusted** :
   - Correlation returns raw vs adjusted sur toute la période
   - Différence de DA si on utilise y_raw vs y_adjusted (calcul rapide via sign de return)
6. **Nombre de contrats actifs par jour** :
   - Distribution : 0, 1, 2, 3, 4+ contrats actifs simultanément
   - Confirmer : 14.9% des dates avec ≥2 contrats actifs
7. Sauvegarder JSON : `roll_stats`, `pct_windows_crossing_roll`, `top_10_gaps`, `active_contracts_dist`
8. Tests : vérifier que `pct_windows_crossing_roll['H60'] > 0.9` (attendu ~1.0).
9. Rédiger `docs/EMA_02_CONTRACTS_ROLLS.md`.

#### Critères de validation

- `pct_windows_crossing_roll` calculé pour H ∈ {20, 40, 60}
- `roll_stats` contient `median_gap`, `max_gap`, `n_rolls`
- `ruff check` : 0 erreur
- Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_contracts_rolls.json`
- `docs/EMA_02_CONTRACTS_ROLLS.md`

---

### NB-EMA-03 — Module séries continues

**Priorité :** P0  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-02  
**Complexité :** moyen

#### Contexte

Les séries continues EMA sont la colonne vertébrale de toute l'analyse. Ce module valide formellement les invariants et caractérise les différences entre séries (front vs liquid, raw vs adjusted, basis). Il sert de référence pour toute la suite.

#### Question scientifique

Les séries continues sont-elles cohérentes entre elles ? Les rolls sont-ils bien absorbés dans l'adjusted ? Quand front et liquid divergent-ils et pourquoi ?

#### Objectif

Créer `src/mais/research/ema_continuous_series.py` — validation et caractérisation des 5 séries continues.

#### Fichiers à créer

- `src/mais/research/ema_continuous_series.py`
- `tests/test_ema_continuous_series.py`
- `artefacts/ema_study/ema_continuous_series.json`
- `docs/EMA_03_CONTINUOUS_SERIES.md`

#### Tâches

1. Charger `EMA_FRONT_RAW`, `EMA_FRONT_ADJUSTED`, `EMA_LIQUID_RAW`, `EMA_LIQUID_ADJUSTED`, `EMA_HARVEST_NOV`.
2. **Invariant roll** : vérifier que `raw_price - adjusted_price == cumulative_adjustment` à chaque date, avec tolérance < 0.01. La `cumulative_adjustment` est le cumsum des roll_gaps aux dates de roll (nulle entre les rolls). Formule exacte : `raw[t] - adjusted[t] = sum(roll_gaps[roll_date <= t])`. Tolérance flottant : `max(abs(raw - adjusted - cumadj)) < 0.01`.
3. **Statistiques descriptives** par série :
   - Période, nb jours, prix moyen, std, min, max, skew, kurtosis
   - Corrélation avec CBOT EUR/t
4. **Corrélation front vs liquid** :
   - Corrélation sur returns (attendu > 0.99)
   - Périodes de divergence (rolling 20j corr < 0.90 — quand ?)
5. **Basis** :
   - Distribution du basis (ema_front_raw - cbot_eur_t)
   - Stats par campagne (crop year)
   - Heatmap basis moyen par mois × année
6. **Transition smooth** :
   - Vérifier que les sauts dans raw sont absorbés dans adjusted
   - Histogramme des returns J-1/J autour des dates de roll : raw vs adjusted
7. Sauvegarder JSON : `series_stats`, `invariant_check`, `front_vs_liquid_corr`, `basis_stats`
8. Tests : `invariant_check` PASS, corrélation front/liquid > 0.99.
9. Rédiger `docs/EMA_03_CONTINUOUS_SERIES.md`.

#### Critères de validation

- Invariant roll PASS
- Corrélation front vs liquid > 0.99
- Basis stats présentes (mean, std, min, max, percentiles)
- `ruff check` : 0 erreur
- Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_continuous_series.json`
- `docs/EMA_03_CONTINUOUS_SERIES.md`

---

### NB-EMA-04 — Module relation EMA/CBOT

**Priorité :** P0  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-03  
**Complexité :** complexe

#### Contexte

EXP-EMA-STUDY-02 a calculé une Granger causality EMA→CBOT (p=0.0144). Ce module formalise rigoureusement tous les tests de relation EMA/CBOT : cointegration Engle-Granger + Johansen, VAR/VECM, rolling correlation, cross-correlation lead-lag. C'est le module le plus important de la fondation.

#### Question scientifique

EMA et CBOT sont-ils cointegrates ? Qui mène qui ? La rolling correlation révèle-t-elle des périodes de découplage ? La Granger causality tient-elle avec les tests formels de cointegration ?

#### Objectif

Créer `src/mais/research/ema_cbot_cointegration.py` — tests formels complets de la relation EMA/CBOT.

#### Fichiers à créer

- `src/mais/research/ema_cbot_cointegration.py`
- `tests/test_ema_cbot_cointegration.py`
- `artefacts/ema_study/ema_cbot_cointegration.json`
- `docs/EMA_04_CBOT_RELATIONSHIP.md`

#### Tâches

1. Charger `EMA_FRONT_ADJUSTED` (log-prix) et `features.parquet` colonne `cbot_eur_t` (log-prix).
2. Aligner les deux séries sur intersection temporelle.
3. **Test de stationnarité** (ADF + KPSS) sur log-prix EMA et log-prix CBOT :
   ```python
   try:
       from statsmodels.tsa.stattools import adfuller, kpss
   except ImportError:
       raise ImportError("statsmodels requis")
   adf_ema = adfuller(log_ema, maxlag=10, autolag='AIC')
   kpss_ema = kpss(log_ema, regression='c', nlags='auto')
   ```
   - Attendu : les deux séries sont I(1)
4. **Test de stationnarité des returns** (différences premières) :
   - Attendu : returns I(0)
5. **Cointegration Engle-Granger** :
   ```python
   from statsmodels.tsa.stattools import coint
   t_stat, p_val, crit = coint(log_ema, log_cbot)
   # p < 0.05 → cointegration confirmée
   ```
6. **Cointegration Johansen** :
   ```python
   from statsmodels.tsa.vector_ar.vecm import coint_johansen
   result = coint_johansen(df[['log_ema', 'log_cbot']], det_order=0, k_ar_diff=4)
   # Trace statistic vs critical values
   ```
7. **VECM si cointegré** (sinon VAR sur returns) :
   ```python
   from statsmodels.tsa.vector_ar.vecm import VECM
   model = VECM(df[['log_ema', 'log_cbot']], k_ar_diff=4, coint_rank=1)
   fitted = model.fit()
   # alpha (vitesse ajustement EMA vs CBOT)
   # beta (vecteur cointegrant)
   ```
8. **Granger causality** (sur returns) :
   ```python
   from statsmodels.tsa.stattools import grangercausalitytests
   # EMA → CBOT : lags 1-5
   # CBOT → EMA : lags 1-5
   ```
   - Comparer avec EXP-EMA-STUDY-02 : p(EMA→CBOT lag1) attendu 0.0144
9. **Rolling correlation** (fenêtres 20j, 60j, 120j, 260j) sur returns :
   - Détecter périodes de découplage : rolling_corr_60j < 0.70
   - Annoter les événements connus (covid 2020, ukraine 2022)
10. **Cross-correlation lead-lag** sur returns (lags -10 à +10) :
    - Pic attendu à lag 0 ou +1 (EMA leads CBOT d'un jour ?)
11. Sauvegarder JSON : `adf_results`, `kpss_results`, `coint_engle_granger`, `coint_johansen`, `vecm_alpha`, `granger_ema_to_cbot`, `granger_cbot_to_ema`, `rolling_corr_stats`, `cross_corr`
12. Tests : vérifier que `coint_engle_granger['p_value']` existe, que `granger_ema_to_cbot` contient les p-values.
13. Rédiger `docs/EMA_04_CBOT_RELATIONSHIP.md` : verdict cointegration, alpha VECM, Granger résumé, tableau cross-correlation.

#### Critères de validation

- Engle-Granger et Johansen exécutés et résultats dans JSON
- VECM ou VAR exécuté
- Granger causality (2 directions) dans JSON pour lags 1-5
- Rolling correlation calculée pour 4 fenêtres
- `ruff check` : 0 erreur
- Tests : PASS (≥ 8 assertions)

#### Outputs

- `artefacts/ema_study/ema_cbot_cointegration.json`
- `docs/EMA_04_CBOT_RELATIONSHIP.md`

---

## BLOC 2 — P1 STATISTIQUES LOURDES (notebooks 05-07)

> Ces modules sont la pièce centrale de l'étude Euronext. Les exécuter AVANT tout modèle prédictif.

---

### NB-EMA-05 — Module décomposition retour EMA ⭐

**Priorité :** P1  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-04  
**Complexité :** complexe

#### Contexte

C'est **l'expérience fondamentale de la Partie B**. Elle quantifie combien de la variance EMA est expliquée par CBOT, EUR/USD et le basis — et ce qui reste comme "résidu européen pur". Le résidu sera l'objet du ticket NB-EMA-06.

#### Question scientifique

Quelle fraction de la variance du retour EMA quotidien est due au CBOT vs EUR/USD vs basis ? Comment les betas varient-ils dans le temps (régimes) ? La crise Ukraine 2022 a-t-elle changé la structure de transmission ?

#### Modèle central

```
EMA_return_1d = α + β₁·CBOT_return_1d + β₂·EURUSD_return_1d + β₃·Δbasis_1d + ε_EU
               = partie_mondiale + partie_change + partie_basis + résidu_EU
```

**Règle anti-leakage :** les betas rolling sont calculés sur fenêtre `[t-260, t-1]` — jamais sur `[t, t+H]`.

#### Objectif

Créer `src/mais/research/ema_return_decomposition.py` — décomposition OLS globale + rolling + par régime.

#### Fichiers à créer

- `src/mais/research/ema_return_decomposition.py`
- `tests/test_ema_return_decomposition.py`
- `artefacts/ema_study/ema_return_decomposition.json`
- `docs/EMA_05_RETURN_DECOMPOSITION.md`

#### Tâches

1. Charger returns EMA (depuis `EMA_FRONT_ADJUSTED`), returns CBOT EUR/t (depuis features), returns EUR/USD, Δbasis.
2. **Note sur l'usage :** cette décomposition est **descriptive/contemporaine** — elle explique la variance EMA historique, elle ne prédit pas t+H. Les betas rolling et le résidu sont contemporains (même date). Toute feature issue de cette décomposition utilisée dans un modèle prédictif devra être laggée de 1 jour (`shift(1)`) avant usage.
3. **OLS global** :
   ```python
   try:
       import statsmodels.formula.api as smf
   except ImportError:
       raise ImportError("statsmodels requis")
   model = smf.ols('ema_return ~ cbot_eur_return + eurusd_return + basis_change', data=df).fit()
   # R², betas, t-stats, F-test, résidus
   ```
4. **Décomposition de variance** (indicative — variables corrélées) :
   ```python
   var_total = df['ema_return'].var()
   var_cbot = (model.params['cbot_eur_return'] * df['cbot_eur_return']).var()
   var_eurusd = (model.params['eurusd_return'] * df['eurusd_return']).var()
   var_basis = (model.params['basis_change'] * df['basis_change']).var()
   var_residual = model.resid.var()
   # Part de chaque composante = var_X / var_total (approximatif si corrélées)
   ```
   **Note :** compléter avec les R² incrémentaux (ajout successif des variables) pour éviter les artefacts de corrélation entre régresseurs :
   ```python
   r2_cbot_only     = smf.ols('ema_return ~ cbot_eur_return', data=df).fit().rsquared
   r2_cbot_eurusd   = smf.ols('ema_return ~ cbot_eur_return + eurusd_return', data=df).fit().rsquared
   r2_full          = model.rsquared
   delta_r2_eurusd  = r2_cbot_eurusd - r2_cbot_only
   delta_r2_basis   = r2_full - r2_cbot_eurusd
   ```
5. **OLS rolling (fenêtre 260j)** :
   ```python
   betas_rolling = []
   for i in range(260, len(df)):
       window = df.iloc[i-260:i]
       m = smf.ols('ema_return ~ cbot_eur_return + eurusd_return + basis_change', data=window).fit()
       betas_rolling.append({'date': df.index[i], 'beta_cbot': m.params[1], 'beta_eurusd': m.params[2], 'beta_basis': m.params[3], 'r2': m.rsquared})
   betas_df = pd.DataFrame(betas_rolling).set_index('date')
   ```
6. **OLS par régime** :
   ```python
   regimes = {
       'normal_2014_2017': ('2014-01-01', '2017-12-31'),
       'drought_2018': ('2018-05-01', '2018-10-31'),
       'covid_2020': ('2020-02-01', '2020-09-30'),
       'ukraine_2022': ('2022-01-01', '2022-12-31'),
       'return_2023_2025': ('2023-01-01', '2025-12-31'),
   }
   ```
   - Pour chaque régime : R², betas, N observations
7. **Calcul du résidu EU** et sauvegarde :
   ```python
   df['ema_residual_return'] = model.resid
   # Sauvegarder pour NB-EMA-06
   ```
8. Sauvegarder JSON : `ols_global`, `variance_decomposition`, `betas_rolling_stats`, `ols_by_regime`, `residual_stats`
9. Sauvegarder `artefacts/ema_study/ema_residual_series.parquet` — le résidu pour NB-EMA-06.
10. Tests : vérifier `r2_global` > 0.05 (attendu 0.25-0.45), `beta_cbot` > 0, `variance_decomposition` somme ≈ 1.
11. Rédiger `docs/EMA_05_RETURN_DECOMPOSITION.md` : tableau betas globaux, tableau décomposition variance, tableau par régime.

#### Critères de validation

- `ols_global` contient `r2`, `beta_cbot`, `beta_eurusd`, `beta_basis`
- `variance_decomposition` contient `pct_cbot`, `pct_eurusd`, `pct_basis`, `pct_residual`
- `betas_rolling_stats` contient `mean`, `std`, `min`, `max` pour chaque beta
- `ema_residual_series.parquet` créé et non vide
- `ruff check` : 0 erreur
- Tests : PASS (≥ 8 assertions)

#### Outputs

- `artefacts/ema_study/ema_return_decomposition.json`
- `artefacts/ema_study/ema_residual_series.parquet`
- `docs/EMA_05_RETURN_DECOMPOSITION.md`

---

### NB-EMA-06 — Module étude résidu EMA ⭐

**Priorité :** P1  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-05  
**Complexité :** critique

#### Contexte

**C'est le notebook le plus important de la Partie B.** Le résidu EU (ε de la décomposition NB-EMA-05) est ce que les données spécifiquement européennes doivent expliquer. Si ce résidu est prévisible avec des features EU, cela justifie la collecte de DATA-EU-01 à 04.

#### Question scientifique

Le résidu EMA (partie non expliquée par CBOT/EUR/USD) est-il prévisible ? Avec quelles variables ? Les grandes variations de résidu correspondent-elles à des événements EU documentés ? Le résidu est-il plus prévisible que le retour brut EMA ?

#### Objectif

Créer `src/mais/research/ema_residual_study.py` — analyse complète du résidu EU : statistiques descriptives, catalogue de chocs, prédictibilité avec features EU disponibles.

#### Fichiers à créer

- `src/mais/research/ema_residual_study.py`
- `tests/test_ema_residual_study.py`
- `artefacts/ema_study/ema_residual_analysis.json`
- `artefacts/ema_study/eu_shocks_catalog.json`
- `docs/EMA_06_RESIDUAL_STUDY.md`

#### Tâches

1. Charger `artefacts/ema_study/ema_residual_series.parquet` (produit par NB-EMA-05).
2. **Statistiques descriptives du résidu** :
   - Distribution : mean (attendu ≈ 0), std, skew, kurtosis, Jarque-Bera
   - Test autocorrélation : Ljung-Box à lags 5, 10, 20
   - Test ARCH : clustering de volatilité (Engle ARCH test)
   - Z-score du résidu (expanding window pour anti-leakage)
3. **Catalogue EU shocks (résidus extrêmes)** :
   ```python
   threshold = 3.0  # z-score
   extreme_residuals = df[abs(df['residual_zscore']) > threshold]
   # Pour chaque date extrême : valeur résidu, z-score, direction
   # Annoter manuellement les événements connus :
   eu_events = {
       '2018-07-01/2018-08-31': 'Sécheresse Europe été 2018',
       '2022-02-24': 'Invasion Ukraine',
       '2020-03-01/2020-04-30': 'Covid-19 choc demande',
       # Autres à identifier depuis les données
   }
   ```
4. **Prédictibilité du résidu avec features EU disponibles** :
   - Construire cibles :
     ```python
     y_residual_up_h5  = (residual_cumsum_5d  > 0).astype(int).shift(-5)
     y_residual_up_h20 = (residual_cumsum_20d > 0).astype(int).shift(-20)
     # Anti-leakage : shift(-H) = futur, mais features = shift(+1) = passé
     ```
   - Feature sets EU disponibles (sans collecte supplémentaire) :
     ```python
     eu_available = ['ema_cbot_basis', 'ema_cbot_basis_zscore_52w', 'eurusd_return_lag1',
                     'ttf_gas_return_lag1', 'ema_oi_total_lag1', 'basis_momentum_20d']
     ```
   - Benchmark walk-forward crop year (min 3 ans train) :
     ```python
     # histgb avec IC95% bootstrap 1000 tirages
     # DA, AUC pour y_residual_up_h20
     # Comparer avec DA(y_up_h20_ema_raw) du EXP-BENCH-02 (0.4673)
     ```
   - Verdict : DA(résidu) > DA(EMA brut) → les variables EU ont plus de signal sur le résidu
5. **Analyse des résidus extrêmes > 2σ** :
   - Composition des features EU à ces dates (z-scores basis, OI, TTF)
   - Pattern commun identifiable ?
6. **Résidu vs variables de stress** :
   - Corrélation résidu ~ basis_zscore
   - Corrélation résidu ~ ttf_gas_return (si disponible)
   - Corrélation résidu ~ eurusd_return
7. Sauvegarder `ema_residual_analysis.json` et `eu_shocks_catalog.json`.
8. Tests :
   - Résidu chargé correctement depuis parquet
   - `eu_shocks_catalog` existe et contient le bon schéma (`date`, `residual_zscore`, `event_label`)
   - DA du résidu calculé et dans JSON
9. Rédiger `docs/EMA_06_RESIDUAL_STUDY.md` : catalogue chocs, tableau prédictibilité, verdict.

#### Critères de validation

- `eu_shocks_catalog.json` existe et possède le schéma correct. Si moins de 3 événements détectés au seuil 3σ, tester aussi seuil 2.5σ et documenter le résultat. Verdict accepté : `NO_EXTREME_EVENT_ENOUGH` si aucun seuil ne produit ≥ 3 événements.
- `ema_residual_analysis.json` contient `da_residual_h20`, `da_ema_raw_h20` (pour comparaison), `ljung_box`, `arch_test`
- La comparaison DA résidu vs DA EMA brut est documentée
- `ruff check` : 0 erreur
- Tests : PASS (≥ 8 assertions)

#### Outputs

- `artefacts/ema_study/ema_residual_analysis.json`
- `artefacts/ema_study/eu_shocks_catalog.json`
- `docs/EMA_06_RESIDUAL_STUDY.md`

---

### NB-EMA-07 — Module basis formel

**Priorité :** P1  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-05  
**Complexité :** complexe

#### Contexte

Le basis mean reversion a déjà été confirmé informellement (70.4% hit rate à H20, 7.64 €/t). Ce module formalise rigoureusement : ADF, KPSS, AR(1), half-life, régimes HMM, drivers du basis. Il approfondit et documente avec des tests statistiques formels ce qui était jusqu'ici descriptif.

#### Question scientifique

Le basis est-il formellement stationnaire (I(0)) ? Quel est le half-life exact ? Y a-t-il des régimes de basis distincts ? Quelles variables externes expliquent le niveau du basis ?

#### Objectif

Créer `src/mais/research/ema_basis_formal.py` — analyse formelle complète du basis.

#### Fichiers à créer

- `src/mais/research/ema_basis_formal.py`
- `tests/test_ema_basis_formal.py`
- `artefacts/ema_study/ema_basis_formal.json`
- `docs/EMA_07_BASIS_STUDY.md`

#### Tâches

1. Charger `EMA_FRONT_ADJUSTED`, `features.parquet` (colonnes `cbot_eur_t`, `eurusd_rate`, `ema_cbot_basis`).
2. **Stationnarité du basis** :
   ```python
   from statsmodels.tsa.stattools import adfuller, kpss
   adf = adfuller(basis.dropna(), maxlag=10, autolag='AIC')
   kpss_result = kpss(basis.dropna(), regression='c', nlags='auto')
   # Attendu : ADF p < 0.05 (stationnaire), KPSS p > 0.05 (confirme)
   ```
3. **AR(1) et half-life** :
   ```python
   from statsmodels.tsa.ar_model import AutoReg
   ar1 = AutoReg(basis.dropna(), lags=1).fit()
   rho = ar1.params['basis.L1']
   half_life = -np.log(2) / np.log(abs(rho))
   # Attendu : rho ≈ 0.95-0.98, half-life ≈ 15-60 jours
   ```
4. **Table de hit rate mean reversion** :
   ```python
   basis_z = expanding_zscore(basis)  # anti-leakage
   for z_threshold in [1.0, 1.5, 2.0, 2.5]:
       for H in [10, 20, 40]:
           # Cas basis_z > threshold (basis élevé) : P(basis baisse à H)
           mask_high = basis_z.shift(1) > z_threshold
           hit_rate_high = (basis.diff(H).shift(-H) < 0)[mask_high].mean()
           # Cas basis_z < -threshold (basis faible) : P(basis monte à H)
           mask_low = basis_z.shift(1) < -z_threshold
           hit_rate_low = (basis.diff(H).shift(-H) > 0)[mask_low].mean()
   ```
5. **Régression basis ~ variables externes** :
   ```python
   # basis_level ~ eurusd_z + ttf_z + ... (OLS)
   # Attendu : EUR faible → basis bas (exports EU moins compétitifs)
   ```
6. **Saisonnalité** :
   - Basis moyen par mois calendaire (janvier, ..., décembre)
   - Basis moyen par mois de campagne (octobre = M1, ..., septembre = M12)
7. **Régimes HMM** (si hmmlearn disponible) :
   ```python
   try:
       from hmmlearn.hmm import GaussianHMM
       model = GaussianHMM(n_components=3, covariance_type='full', n_iter=1000)
       model.fit(basis_scaled)
       states = model.predict(basis_scaled)
       # État 0 : basis contraction, État 1 : normal, État 2 : expansion
   except ImportError:
       # Alternative : k-means sur (basis, basis_momentum) → 3 clusters
   ```
8. **Backtest basis arbitrage (papier)** :
   ```python
   # Signal : basis_z > 2 → SHORT EMA (attend contraction)
   # Signal : basis_z < -2 → LONG EMA (attend expansion)
   # Return : -basis_change_H20 si signal SHORT
   # Métriques : hit_rate, mean_return, Sharpe
   # Anti-leakage : signal au close J, position à J+1 open
   ```
9. Sauvegarder JSON complet.
10. Tests : `half_life` > 0, `adf_p_value` existe, `hit_rate_h20_z2_high` existe.
11. Rédiger `docs/EMA_07_BASIS_STUDY.md`.

#### Critères de validation

- ADF et KPSS exécutés, résultats dans JSON
- `half_life` calculé (valeur en jours)
- Table de hit rate complète (z_threshold × H)
- Backtest basis arbitrage papier avec hit_rate et Sharpe
- `ruff check` : 0 erreur
- Tests : PASS (≥ 8 assertions)

#### Outputs

- `artefacts/ema_study/ema_basis_formal.json`
- `docs/EMA_07_BASIS_STUDY.md`

---

## BLOC 3 — P1 VALIDATION

---

### VALID-GRANGER-01 — Validation Granger OOF ⭐

**Priorité :** P1  
**Type :** validation  
**Statut :** DONE  
**Dépendances :** NB-EMA-04  
**Complexité :** complexe

#### Contexte

EXP-EMA-STUDY-02 a produit un résultat surprenant : EMA Granger-cause CBOT avec p=0.0144 (lag 1). Ce résultat contredit la hiérarchie marché supposée. Avant toute exploitation, il faut valider rigoureusement avec les 5 tests du §15.3 de REFLEXION_ETUDE_COMPLETE.md.

**Vocabulaire obligatoire :** tant que non validé OOF → "EMA→CBOT prometteur, non encore confirmé OOF". Ne jamais écrire "Granger exploitable" avant validation.

#### Question scientifique

La Granger causality EMA→CBOT est-elle robuste temporellement (3 sous-périodes), tient-elle après neutralisation EUR/USD, améliore-t-elle le modèle CBOT en OOF ? Est-ce un artefact de timing (décalage de fermeture des marchés) ?

#### Objectif

Créer `src/mais/research/ema_granger_validation.py` — les 5 tests de validation du §15.3.

#### Fichiers à créer

- `src/mais/research/ema_granger_validation.py`
- `tests/test_ema_granger_validation.py`
- `artefacts/ema_study/ema_granger_validation.json`
- `docs/EMA_GRANGER_VALIDATION.md`

#### Tâches

1. Charger returns EMA et returns CBOT (alignés, même index).
2. **Test 1 — Robustesse temporelle** :
   ```python
   subperiods = {
       '2014_2017': ('2014-01-01', '2017-12-31'),
       '2018_2020': ('2018-01-01', '2020-12-31'),
       '2021_2025': ('2021-01-01', '2025-12-31'),
   }
   for name, (start, end) in subperiods.items():
       sub = df.loc[start:end]
       result = grangercausalitytests(sub[['cbot_return', 'ema_return']], maxlag=5, verbose=False)
       p_lag1 = result[1][0]['ssr_ftest'][1]
       # Critère robustesse : p < 0.05 dans ≥ 2/3 sous-périodes
   ```
3. **Test 2 — Robustesse au choix de lag** :
   - Granger pour lags 1, 2, 3, 4, 5 sur la période complète
   - Si seul lag 1 est significatif → signal court (timing ou arbitrage)
4. **Test 3 — Neutralisation EUR/USD** :
   ```python
   # Régresser EMA_return ~ EURUSD_return → obtenir résidu EMA_eur_neutral
   # Régresser CBOT_return ~ EURUSD_return → obtenir résidu CBOT_eur_neutral
   # Tester Granger sur (CBOT_eur_neutral, EMA_eur_neutral)
   # Si Granger disparaît → c'était la corrélation EUR/USD
   # Si Granger persiste → signal propre EU
   ```
5. **Test 4 — Validation OOF (test ultime)** :
   ```python
   # Feature ajoutée : ema_return_lag1 dans le modèle CBOT
   # Walk-forward crop year (8 folds, min 3 ans train)
   # Modèle baseline : CBOT sans ema_return_lag1
   # Modèle enrichi : CBOT + ema_return_lag1
   # Cible : y_up_h20 CBOT
   # Critère : delta_DA = DA(enrichi) - DA(baseline) > +0.008
   ```
6. **Test 5 — Exclusion crise 2022** :
   ```python
   df_no2022 = df[~df.index.year.isin([2022])]
   result_no2022 = grangercausalitytests(df_no2022[['cbot_return', 'ema_return']], maxlag=5)
   # Si signal disparaît → concentré dans la crise Ukraine
   ```
7. **Verdict final** :
   ```python
   n_subperiods_significant = sum(p < 0.05 for p in subperiod_p_values)
   granger_survives_eurusd = granger_p_neutral < 0.05
   oof_delta_da = da_enriched - da_baseline
   
   if n_subperiods_significant >= 2 and granger_survives_eurusd and oof_delta_da > 0.008:
       verdict = "CONFIRMÉ"
   elif n_subperiods_significant >= 1 or oof_delta_da > 0:
       verdict = "PARTIEL — signal faible, non exploitable"
   else:
       verdict = "INFIRMÉ — artefact statistique"
   ```
8. Sauvegarder JSON avec tous les tests et le verdict.
9. Tests : JSON contient `verdict`, `test1_subperiods`, `test3_eur_neutral`, `test4_oof_delta_da`.
10. Rédiger `docs/EMA_GRANGER_VALIDATION.md` : verdict en titre, détail des 5 tests.

#### Critères de validation

- Les 5 tests exécutés et documentés
- `verdict` ∈ {CONFIRMÉ, PARTIEL, INFIRMÉ}
- `oof_delta_da` calculé en walk-forward strict
- `ruff check` : 0 erreur
- Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_granger_validation.json`
- `docs/EMA_GRANGER_VALIDATION.md`

---

## BLOC 3.5 — P1.5 UTILITAIRES COMMUNS

---

### UTIL-EMA-01 — Fonctions communes statistiques

**Priorité :** P1.5 (après P1, avant P2)  
**Type :** utilitaire  
**Statut :** DONE  
**Dépendances :** NB-EMA-04 (pour connaître les patterns)  
**Complexité :** simple

#### Contexte

Les tickets NB-EMA-08 à 13 vont tous répéter les mêmes fonctions : crop-year split, bootstrap IC95%, correction BH, métriques DA/AUC/Brier, alignement de séries, serialisation JSON. Il faut centraliser ces utilitaires pour éviter la duplication et les incohérences.

#### Objectif

Créer `src/mais/research/ema_utils.py` — bibliothèque de fonctions réutilisables pour tous les modules P2.

#### Fichiers à créer

- `src/mais/research/ema_utils.py`
- `tests/test_ema_utils.py`

#### Tâches

1. **`crop_year_split(df, min_train_years=3)`** :
   ```python
   def crop_year_split(df, min_train_years=3):
       """Yield (train_df, test_df, crop_year_label) pour walk-forward crop year.
       Crop year : octobre → septembre. Min 3 ans train."""
       # Détecter les crop years disponibles dans df.index
       # Générer les folds : train = tout ce qui précède le crop year test
       # Exclure les folds où train < min_train_years
   ```
2. **`bootstrap_ci(values, n_boot=1000, alpha=0.05, seed=42)`** :
   ```python
   def bootstrap_ci(values, n_boot=1000, alpha=0.05, seed=42):
       """IC95% par bootstrap sur un vecteur de valeurs (ex: DA par fold)."""
       rng = np.random.default_rng(seed)
       boots = [rng.choice(values, len(values), replace=True).mean() for _ in range(n_boot)]
       return np.percentile(boots, [100*alpha/2, 100*(1-alpha/2)])
   ```
3. **`benjamini_hochberg(p_values, alpha=0.05)`** :
   ```python
   def benjamini_hochberg(p_values, alpha=0.05):
       """Retourne q-values BH et masque des hypothèses rejetées."""
       ...
   ```
4. **`compute_metrics(y_true, y_pred_proba)`** :
   ```python
   def compute_metrics(y_true, y_pred_proba):
       """DA, AUC, Brier, top20 DA. Retourne dict."""
       from sklearn.metrics import roc_auc_score, brier_score_loss
       ...
   ```
5. **`align_series_strict(series_list, how='inner')`** :
   ```python
   def align_series_strict(series_list, how='inner'):
       """Aligne plusieurs Series/DataFrame sur intersection temporelle."""
       ...
   ```
6. **`safe_json_dump(obj, path)`** :
   ```python
   def safe_json_dump(obj, path):
       """Convertit numpy types → Python natifs avant json.dump."""
       ...
   ```
7. Tests pour chaque fonction (≥ 2 assertions par fonction).
8. Pas de docstring multi-paragraphes — une ligne max par fonction.

#### Critères de validation

- 6 fonctions présentes et testées
- `ruff check` : 0 erreur
- Tests : PASS (≥ 12 assertions)

#### Outputs

- `src/mais/research/ema_utils.py`

---

## BLOC 4 — P2 PRÉDICTIF (notebooks 08-13)

---

### NB-EMA-08 — Module benchmark directionnel EMA

**Priorité :** P2  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-05, NB-EMA-07  
**Complexité :** complexe

#### Contexte

EXP-BENCH-02 a produit un NO_GO sur la direction EMA (DA 0.4673). Ce module reproduit ce benchmark avec le protocole canonique complet (walk-forward crop year, IC95%, BH) sur toutes les feature sets et toutes les cibles — y compris les nouvelles cibles issues de la décomposition (résidu, basis reversion).

#### Question scientifique

Avec les features issues de la décomposition (résidu, basis formel, VECM), peut-on améliorer le DA EMA direction ? La cible `y_residual_up_h20` est-elle plus prévisible que `y_up_h20_ema_raw` ?

#### Objectif

Créer `src/mais/research/ema_direction_benchmark.py` — benchmark directionnel complet multi-features × multi-cibles.

#### Fichiers à créer

- `src/mais/research/ema_direction_benchmark.py`
- `tests/test_ema_direction_benchmark.py`
- `artefacts/ema_study/ema_direction_benchmark.json`
- `docs/EMA_08_DIRECTION_BENCHMARK.md`

#### Tâches

1. Définir les feature sets (7 sets comme dans §5 notebook 08 de REFLEXION) :
   - `cbot_only`, `ema_technical_only`, `basis_only`, `cbot_basis`, `cbot_ema_combined`, `cbot_eu_macro`, `all_selected`
2. Définir les cibles (6) :
   - `y_up_h20_ema_raw`, `y_up_h20_ema_adjusted`, `y_up_h40_ema_noroll`, `y_up_h20_ema_liquid`, `y_up_h20_basis_reversion`, `y_up_h20_residual`
3. Walk-forward crop year :
   - Définir les crop years (octobre à septembre)
   - Min 3 ans train (folds 2017+)
   - Modèle : histgb (sklearn `HistGradientBoostingClassifier`)
4. IC95% bootstrap (1000 tirages) sur la DA agrégée.
5. Correction BH (Benjamini-Hochberg) sur tous les p-values DA > 0.50.
6. Verdict go/no-go par feature set × cible :
   - GO minimal : DA_mean > 0.55 AND AUC > 0.55 AND IC95_lo > 0.50
   - GO professionnel : IC95_lo > 0.55 AND DA_top20 > 0.62
7. Sauvegarder tableau JSON complet.
8. Tests : JSON contient résultats pour au moins 3 feature sets, verdict présent.
9. Rédiger `docs/EMA_08_DIRECTION_BENCHMARK.md` : tableau feature_set × cible × DA × AUC × IC95 × verdict.

#### Critères de validation

- 7 feature sets × 6 cibles = 42 combinaisons testées (ou subset justifié)
- `verdict_go_nogo` présent pour chaque combinaison
- IC95% bootstrap calculé
- Correction BH appliquée
- `ruff check` : 0 erreur
- Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_direction_benchmark.json`
- `docs/EMA_08_DIRECTION_BENCHMARK.md`

---

### NB-EMA-09 — Module event study grands mouvements

**Priorité :** P2  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-06  
**Complexité :** moyen

#### Contexte

Ce module répond à la question : "Quels événements précèdent les grandes variations EMA ?" Il utilise le catalogue eu_shocks_catalog (NB-EMA-06) et l'étend avec des événements WASDE, EC MARS, sécheresse EU, et variations extrêmes CBOT/EUR.

#### Question scientifique

Y a-t-il une réaction asymétrique EMA aux événements ? Les chocs baissiers sont-ils plus brusques que les chocs haussiers ? Quels événements ont le plus fort impact à J+1 / J+5 / J+20 ?

#### Objectif

Créer `src/mais/research/ema_event_study.py` — event study avec fenêtres J-10 à J+20 pour chaque type d'événement.

#### Fichiers à créer

- `src/mais/research/ema_event_study.py`
- `tests/test_ema_event_study.py`
- `artefacts/ema_study/ema_event_study.json`
- `docs/EMA_09_EVENT_STUDY.md`

#### Tâches

1. Charger returns EMA et `eu_shocks_catalog.json` (NB-EMA-06).
2. Définir les types d'événements :
   - WASDE publication dates (mensuel, depuis `wasde_release_dates` si disponible)
   - Résidus EU extrêmes > 3σ (depuis catalogue)
   - CBOT variation > ±3% J-J (depuis features)
   - EUR/USD variation > ±1.5% J-J
   - Basis z-score > ±2 (depuis features EMA)
3. Pour chaque type d'événement :
   ```python
   event_dates = [...]  # dates de l'événement
   windows = range(-10, 21)  # J-10 à J+20
   cumreturns = []
   for d in event_dates:
       window_returns = ema_returns.loc[d-10j:d+20j]
       cumreturns.append(window_returns.cumsum())
   mean_cumreturn = average(cumreturns)  # moyenne sur toutes les occurrences
   # IC95% bootstrap 1000 tirages
   ```
4. **Asymétrie haussière/baissière** :
   - Séparer événements haussiers vs baissiers (signe du résidu ou du retour J+1)
   - Comparer vitesse de réaction : haussier vs baissier
5. **Règles simples (Decision Tree max_depth=2)** :
   ```python
   from sklearn.tree import DecisionTreeClassifier
   # Features : basis_z, cbot_return_lag1, eurusd_z
   # Cible : large_move_h5 (>3%)
   # max_depth=2 → règle lisible
   ```
6. Sauvegarder JSON : `events_by_type`, `mean_cumreturn_by_event`, `ic95_by_event`, `asymmetry_stats`, `decision_rules`
7. Tests : `events_by_type` contient ≥ 3 types, `mean_cumreturn_by_event` non vide.
8. Rédiger `docs/EMA_09_EVENT_STUDY.md` : heatmap event × retour, tableau des règles.

#### Critères de validation

- ≥ 3 types d'événements traités
- IC95% bootstrap pour chaque type
- Asymétrie haussière/baissière documentée
- Decision tree rules lisibles dans le doc
- `ruff check` : 0 erreur
- Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_event_study.json`
- `docs/EMA_09_EVENT_STUDY.md`

---

### NB-EMA-10 — Module importance des features EMA

**Priorité :** P2  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-08  
**Complexité :** moyen

#### Contexte

EXP-BENCH-01 a sélectionné 50 features dont 5 EMA. Ce module approfondit l'analyse d'importance : ablation one-family-out, permutation importance, stabilité par crop year. Il répond à la question : quelles familles de features comptent vraiment pour EMA ?

#### Objectif

Créer `src/mais/research/ema_feature_importance.py` — analyse d'importance multi-méthodes sur les 14 familles.

#### Fichiers à créer

- `src/mais/research/ema_feature_importance.py`
- `tests/test_ema_feature_importance.py`
- `artefacts/ema_study/ema_feature_importance.json`
- `docs/EMA_10_FEATURE_IMPORTANCE.md`

#### Tâches

1. Charger `features.parquet`, définir les 14 familles (§5 notebook 10 de REFLEXION).
2. **Ablation one-family-out** : pour chaque famille, DA sans cette famille → delta DA.
3. **Ablation only-family** : DA avec seulement cette famille.
4. **Permutation importance** : sur modèle histgb walk-forward.
5. **Stabilité par crop year** : variance du delta DA entre crop years.
6. Sauvegarder JSON : tableau `family → da_full, da_without, delta_da, da_alone, stability`.
7. Tests et doc.

#### Critères de validation

- 14 familles traitées, tableau complet
- `ruff check` : 0 erreur, Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_feature_importance.json`
- `docs/EMA_10_FEATURE_IMPORTANCE.md`

---

### NB-EMA-11 — Module volatilité EMA (HAR/GARCH)

**Priorité :** P2  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-05  
**Complexité :** moyen

#### Contexte

La volatilité est souvent plus prévisible que la direction. Ce module teste HAR (Heterogeneous AutoRegression) et GARCH(1,1) pour prédire la volatilité réalisée EMA — une dimension "risque" utile dans le rapport final.

#### Question scientifique

La volatilité EMA est-elle prévisible ? HAR ou GARCH performent-ils mieux que le baseline naive (volatilité passée) ? Peut-on identifier des régimes de haute volatilité ?

#### Objectif

Créer `src/mais/research/ema_volatility.py` — HAR + GARCH walk-forward avec Qlike et MSE.

#### Fichiers à créer

- `src/mais/research/ema_volatility.py`
- `tests/test_ema_volatility.py`
- `artefacts/ema_study/ema_volatility.json`
- `docs/EMA_11_VOLATILITY.md`

#### Tâches

1. Calculer `realized_vol_20d = std(ema_return_1d, 20) * sqrt(252)`.
2. **Baseline** : naive (vol_20d décalée d'1 jour).
3. **HAR** :
   ```python
   # vol_t = c + β_daily*vol_{t-1} + β_weekly*vol_5d + β_monthly*vol_22d + ε
   # OLS rolling 260j, anti-leakage
   try:
       import statsmodels.api as sm
   except ImportError:
       raise ImportError("statsmodels requis")
   ```
4. **GARCH(1,1)** :
   ```python
   try:
       from arch import arch_model
       garch = arch_model(ema_returns, vol='Garch', p=1, q=1)
       res = garch.fit(disp='off')
   except ImportError:
       pass  # GARCH optionnel — documenter l'absence
   ```
5. **HistGBT sur lag features vol** — comparaison.
6. Métriques : RMSE, MAE, Qlike sur fenêtre OOF.
7. Régimes de volatilité : quartiles → `low/normal/high`.
8. Sauvegarder JSON, tests, doc.

#### Critères de validation

- HAR exécuté, Qlike calculé
- Baseline comparée
- Régimes de vol documentés
- `ruff check` : 0 erreur, Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_volatility.json`
- `docs/EMA_11_VOLATILITY.md`

---

### NB-EMA-12 — Module prévision prix expérimental

**Priorité :** P2  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-08, NB-EMA-11  
**Complexité :** complexe

#### Contexte

Le CQR prix EMA a donné 79.2% coverage vs 88% requis (NO_GO). Ce module teste des approches alternatives pour améliorer le coverage : CQR par régime, CQR excluant 2021-2022, GARCH-M, et baseline AR1+basis.

**Statut de sortie obligatoire :** EXPÉRIMENTAL si coverage < 88%.

#### Question scientifique

Peut-on atteindre 88% coverage IC90% sur les prix EMA ? La baseline AR1+basis est-elle compétitive vs les modèles ML en termes de Winkler loss ?

#### Objectif

Créer `src/mais/research/ema_price_forecast.py` — comparaison multi-modèles avec métriques coverage + Winkler.

#### Fichiers à créer

- `src/mais/research/ema_price_forecast.py`
- `tests/test_ema_price_forecast.py`
- `artefacts/ema_study/ema_price_forecast.json`
- `docs/EMA_12_PRICE_FORECAST.md`

#### Tâches

1. Définir les baselines : random walk, seasonal naive, ar1_basis.
2. Modèles : Ridge, HistGBT quantile, CQR standard, CQR par régime, CQR excluant 2021-2022.
3. Walk-forward crop year pour chaque modèle.
4. Métriques : RMSE, MAE, coverage IC90%, Winkler loss, CRPS.
5. Verdict : si coverage < 88% → statut EXPÉRIMENTAL dans le JSON.
6. Tests et doc avec tableau comparatif.

#### Critères de validation

- ≥ 5 modèles testés, coverage documenté pour chacun
- Verdict EXPÉRIMENTAL/VALIDÉ présent
- `ruff check` : 0 erreur, Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_price_forecast.json`
- `docs/EMA_12_PRICE_FORECAST.md`

---

### NB-EMA-13 — Module benchmark hebdomadaire ⭐

**Priorité :** P2  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-08  
**Complexité :** moyen

#### Contexte

Beaucoup de features fondamentales (WASDE, EC MARS, COT) sont hebdomadaires. En daily, on répète la même information 5 fois, ce qui peut gonfler les statistiques. Ce module compare 4 fréquences d'échantillonnage pour savoir si le DA daily est réel ou un artefact d'autocorrélation.

#### Question scientifique

Le DA daily est-il supérieur au DA hebdomadaire ? L'autocorrélation des prédictions daily est-elle élevée (>0.80), suggérant une répétition du signal ? Le weekly donne-t-il un signal plus "pur" ?

#### Objectif

Créer `src/mais/research/ema_weekly_benchmark.py` — comparaison daily vs 3 versions hebdomadaires.

#### Fichiers à créer

- `src/mais/research/ema_weekly_benchmark.py`
- `tests/test_ema_weekly_benchmark.py`
- `artefacts/ema_study/ema_weekly_benchmark.json`
- `docs/EMA_13_WEEKLY_BENCHMARK.md`

#### Tâches

1. Construire 4 versions du dataset :
   - `daily_close` : toutes les clôtures
   - `weekly_friday` : clôture du vendredi
   - `weekly_monday` : clôture du lundi
   - `post_report` : lendemain de la publication WASDE (si dates disponibles)
2. Pour chaque version, même modèle (histgb, features sélectionnées par EXP-BENCH-01).
3. Métriques : DA, AUC, IC95% bootstrap, autocorrélation des prédictions.
4. **H1 à H4** (§5 notebook 13 de REFLEXION) : tester et documenter le résultat de chaque hypothèse.
5. **Cibles grands mouvements hebdomadaires** : `large_up_3pct_week`, `large_down_3pct_week`.
6. Sauvegarder JSON : `comparison_table`, `autocorr_predictions`, `large_moves_weekly`.
7. Tests et doc.

#### Critères de validation

- 4 fréquences comparées
- Autocorrélation des prédictions daily calculée
- H1 à H4 documentées avec résultat
- `ruff check` : 0 erreur, Tests : PASS

#### Outputs

- `artefacts/ema_study/ema_weekly_benchmark.json`
- `docs/EMA_13_WEEKLY_BENCHMARK.md`

---

## BLOC 5 — P3 DONNÉES EUROPÉENNES

---

### DATA-EU-01 — Collecteur EC MARS (JRC Agri4cast) ⭐

**Priorité :** P3  
**Type :** data_collector  
**Statut :** DONE  
**Dépendances :** NB-EMA-06 (pour savoir ce qu'on cherche à expliquer)  
**Complexité :** complexe

#### Contexte

EC MARS (Monitoring Agricultural Resources) publie mensuellement les bulletins de rendement maïs par pays EU. C'est la source européenne de premier rang pour le fundamental agricole. Elle est gratuite via l'API JRC Agri4cast.

#### Objectif

Créer `src/mais/collect/ec_mars.py` — collecteur EC MARS avec audit qualité + intégration anti-leakage dans `features.parquet`.

#### Fichiers à créer

- `src/mais/collect/ec_mars.py`
- `tests/test_ec_mars.py`
- `data/raw/ec_mars/` (répertoire)
- `artefacts/ema_study/ec_mars_audit.json`
- `docs/DATA_EU_01_EC_MARS.md`

#### Tâches

1. **Exploration API** :
   - URL base : `https://agri4cast.jrc.ec.europa.eu/DataPortal/`
   - Datasets pertinents : `CGMS-WOFOST` (yield forecast) ou `MARS Crop Monitoring`
   - Alternative : bulletins PDF mensuels → scraping ou données historiques CSV disponibles
   - Documenter les limites d'accès (authentification requise ?)
2. **Collecteur** :
   ```python
   class ECMARSCollector:
       BASE_URL = "https://agri4cast.jrc.ec.europa.eu/..."
       
       def fetch_yield_forecast(self, crop='maize', region='EU27', year_start=2010):
           """Rendement maïs EU par mois de bulletin."""
           ...
       
       def fetch_biomass_anomaly(self, region='EU27'):
           """Anomalie biomasse / stress hydrique."""
           ...
   ```
3. **Anti-leakage critique** :
   - EC MARS publie le bulletin du mois M à la date de publication réelle (~15 du mois suivant)
   - Le fichier doit contenir `publication_date` (pas `reference_date`)
   - Dans features.parquet : `ec_mars_yield_forecast_lag1` = valeur du dernier bulletin publié avant t
4. **Features à créer** (mensuelles, forward-filled dans features.parquet) :
   ```python
   ec_mars_yield_forecast_eu   # rendement prévu EU (t/ha)
   ec_mars_yield_anomaly_eu    # écart vs moyenne 10 ans (%)
   ec_mars_biomass_anomaly_eu  # anomalie biomasse (%)
   ec_mars_soil_moisture_eu    # humidité sol anomalie
   ec_mars_yield_revision_eu   # révision vs mois précédent (t/ha)
   ```
5. Sauvegarder en parquet : `data/raw/ec_mars/ec_mars_monthly.parquet`.
6. Audit qualité : couverture années, nb bulletins, NaN%.
7. **Delta DA — optionnel (non bloquant pour ce ticket)** : si les données sont disponibles et intégrées dans features.parquet, mesurer delta DA vs baseline CBOT en ablation rapide. Sinon, documenter "à mesurer dans EXP-EU-ABLATION-01". Ne pas bloquer le ticket sur ce résultat.
8. Tests : collecteur s'exécute (ou mock si API non disponible), features créées avec anti-leakage.
9. Rédiger `docs/DATA_EU_01_EC_MARS.md` : source, variables, anti-leakage, delta DA si disponible.

#### Critères de validation

- Collecteur EC MARS fonctionnel ou mock documenté
- Anti-leakage sur publication_date (pas reference_date)
- Features créées avec `_lag1` suffix
- Audit qualité dans JSON
- `ruff check` : 0 erreur, Tests : PASS

#### Outputs

- `data/raw/ec_mars/ec_mars_monthly.parquet`
- `artefacts/ema_study/ec_mars_audit.json`
- `docs/DATA_EU_01_EC_MARS.md`

---

### DATA-EU-02 — Collecteur Open-Meteo Europe ⭐

**Priorité :** P3  
**Type :** data_collector  
**Statut :** DONE  
**Dépendances :** aucune pour la collecte ; NB-EMA-06 recommandé pour l'interprétation  
**Complexité :** complexe

#### Contexte

Open-Meteo offre une API REST gratuite avec des données météo historiques pour n'importe quelle coordonnée. On peut calculer les Growing Degree Days (GDD), le déficit hydrique, les jours de chaleur extrême pour 6 zones maïs EU (France SO, France CO, Italie N, Roumanie, Hongrie, Ukraine O).

#### Objectif

Créer `src/mais/collect/openmeteo_eu.py` — collecteur météo EU pour 6 zones maïs avec calcul GDD, stress thermique, déficit pluie.

#### Fichiers à créer

- `src/mais/collect/openmeteo_eu.py`
- `tests/test_openmeteo_eu.py`
- `data/raw/openmeteo_eu/` (répertoire)
- `artefacts/ema_study/openmeteo_eu_audit.json`
- `docs/DATA_EU_02_OPENMETEO.md`

#### Tâches

1. **Zones maïs EU** :
   ```python
   CORN_ZONES_EU = {
       'france_so':   (44.0, 0.5),   # Landes/Gers
       'france_co':   (46.5, 2.0),   # Beauce/Brie
       'italy_north': (45.0, 11.0),  # Plaine du Pô
       'romania':     (44.5, 26.0),  # Bucarest
       'hungary':     (47.0, 19.0),  # Budapest
       'ukraine_west': (49.0, 27.0), # Kiev
   }
   ```
2. **API Open-Meteo** :
   ```python
   import requests
   BASE = "https://archive-api.open-meteo.com/v1/archive"
   params = {
       'latitude': lat, 'longitude': lon,
       'start_date': '2010-01-01', 'end_date': '2025-12-31',
       'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
       'timezone': 'Europe/Paris'
   }
   ```
3. **Calculs agro** :
   ```python
   # GDD maïs : base 10°C, max 30°C
   gdd_daily = clip(tmax, 10, 30) - 10
   gdd_cumul = gdd_daily.cumsum()  # depuis 1er mai
   
   # Jours de stress thermique
   days_above_32 = (tmax > 32).resample('W').sum()
   days_above_35 = (tmax > 35).resample('W').sum()
   
   # Déficit précipitations vs normale
   precip_deficit_30d = precip_30d - precip_30d_rolling_mean_10y
   ```
4. **Agrégation EU** :
   - Moyenne pondérée des 6 zones (par surface maïs relative)
   - Poids approximatifs : FR=25%, IT=20%, RO=20%, HU=15%, UA=15%, autres=5%
5. **Features à créer** (hebdomadaires, forward-filled) :
   ```python
   eu_gdd_cumul_week       # GDD cumulé semaine (mai-sept)
   eu_gdd_anomaly_week     # anomalie vs moyenne 10 ans
   eu_precip_deficit_30d   # déficit pluie 30j (mm)
   eu_heat_stress_days_4w  # jours >32°C sur 4 semaines
   eu_drought_score_week   # score sécheresse composite
   ```
6. Anti-leakage : features avec shift(1), calculées sur données passées.
7. Tests, audit qualité, doc avec delta DA mesuré.

#### Critères de validation

- 6 zones collectées, GDD calculé
- Features EU disponibles depuis 2010
- Anti-leakage PASS
- `ruff check` : 0 erreur, Tests : PASS

#### Outputs

- `data/raw/openmeteo_eu/openmeteo_eu_daily.parquet`
- `artefacts/ema_study/openmeteo_eu_audit.json`
- `docs/DATA_EU_02_OPENMETEO.md`

---

### DATA-EU-03 — Collecteur FranceAgriMer / Agreste

**Priorité :** P3  
**Type :** data_collector  
**Statut :** DONE  
**Dépendances :** DATA-EU-01  
**Complexité :** moyen

#### Contexte

FranceAgriMer publie les bilans céréaliers mensuels (collecte, exportations, stocks, disponibilités). Agreste publie les estimations de récolte françaises. La France est le plus grand producteur EU de maïs (~14-16 Mt/an). Ces données sont disponibles sur open data gouvernemental français.

#### Objectif

Créer `src/mais/collect/franceagrimer.py` — collecteur bilans céréaliers maïs France (mensuel).

#### Fichiers à créer

- `src/mais/collect/franceagrimer.py`
- `tests/test_franceagrimer.py`
- `data/raw/franceagrimer/` (répertoire)
- `artefacts/ema_study/franceagrimer_audit.json`
- `docs/DATA_EU_03_FRANCEAGRIMER.md`

#### Tâches

1. Sources :
   - FranceAgriMer bilans : `https://www.franceagrimer.fr/Outils-et-ressources/Statistiques`
   - Agreste : `https://agreste.agriculture.gouv.fr/agreste-web/`
   - Données OpenData si disponibles via `data.gouv.fr`
2. Données à récupérer :
   - Production France maïs (Mt/campagne)
   - Collecte mensuelle maïs France (Mt)
   - Exportations France maïs (Mt)
   - Stocks fin de mois (Mt)
   - Import/Export UE France maïs
3. Anti-leakage : date de publication réelle (généralement 15 jours après le mois de référence).
4. Features :
   ```python
   fr_mais_collecte_mensuelle     # collecte mensuelle (Mt)
   fr_mais_stock_fin_mois         # stocks (Mt)
   fr_mais_export_mensuel         # exports (Mt)
   fr_mais_stock_use_ratio        # stocks/utilisation (%)
   fr_mais_collecte_anomaly       # écart vs campagne précédente
   ```
5. Tests, audit, doc.

#### Critères de validation

- Données disponibles depuis ≥ 2015
- Anti-leakage sur publication_date
- `ruff check` : 0 erreur, Tests : PASS

#### Outputs

- `data/raw/franceagrimer/franceagrimer_monthly.parquet`
- `docs/DATA_EU_03_FRANCEAGRIMER.md`

---

### DATA-EU-04 — Collecteur ETS CO₂ et TTF enrichi

**Priorité :** P3  
**Type :** data_collector  
**Statut :** DONE  
**Dépendances :** aucune (données de marché disponibles)  
**Complexité :** simple

#### Contexte

Le TTF gas est déjà collecté via yfinance (2 155 lignes). Le CO₂ ETS (European Trading Scheme) n'est pas encore collecté. Ces deux variables influencent les coûts de production agricole EU (énergie, engrais) et donc le basis EMA. L'ETS CO₂ est disponible gratuitement.

#### Objectif

Enrichir la collecte TTF (historique plus long) et ajouter ETS CO₂ quotidien depuis 2013.

#### Fichiers à créer

- `src/mais/collect/eu_carbon.py`
- `tests/test_eu_carbon.py`
- `docs/DATA_EU_04_ETS_CO2.md`

#### Tâches

1. **TTF enrichi** : vérifier si yfinance donne TTF depuis 2010. Si non, chercher source alternative (ICE, Quandl libre, EEX).
2. **ETS CO₂** :
   ```python
   # Source : EEX EUA spot, ou via yfinance "CO2.L" (EUA futures)
   import yfinance as yf
   co2 = yf.download("CO2.L", start="2013-01-01")  # tenter
   # Alternative : fichier CSV EEX depuis le site (gratuit, historique EU ETS)
   ```
3. **Features** :
   ```python
   ets_co2_price        # prix EUA (€/tonne CO₂)
   ets_co2_return_1d    # rendement quotidien
   ets_co2_zscore_52w   # z-score 52 semaines (expanding)
   ttf_zscore_52w       # idem pour TTF
   ```
4. Anti-leakage : shift(1) sur toutes les features.
5. Brancher dans `build_features()` si les données couvrent la période EMA.
6. Tests et doc.

#### Critères de validation

- ETS CO₂ disponible depuis ≥ 2015
- Features avec z-scores et anti-leakage
- `ruff check` : 0 erreur, Tests : PASS

#### Outputs

- Features `ets_co2_*` dans `features.parquet`
- `docs/DATA_EU_04_ETS_CO2.md`

---

### DATA-WORLD-01 — Enrichissement WASDE EU + Ukraine

**Priorité :** P3  
**Type :** data_collector  
**Statut :** DONE  
**Dépendances :** DATA-EU-01  
**Complexité :** moyen

#### Contexte

Les données WASDE actuelles sont centrées US. Le WASDE contient aussi les projections EU, Ukraine, Brésil. Extraire ces colonnes mondiales permettrait de créer un ratio stocks EU / stocks monde — variable clé pour le basis.

#### Objectif

Étendre le module WASDE pour extraire les colonnes EU et Ukraine corn + calculer le ratio stocks_EU/stocks_monde.

#### Fichiers à créer

- Modifier `src/mais/collect/wasde.py` (ou équivalent) pour ajouter les colonnes EU
- `tests/test_wasde_eu.py`
- `docs/DATA_WORLD_01_WASDE_EU.md`

#### Tâches

1. Identifier la source WASDE actuelle dans le projet (`grep -r "wasde" src/`).
2. Vérifier les colonnes disponibles : y a-t-il déjà des données EU ?
3. Extraire les colonnes WASDE EU :
   ```python
   wasde_eu_production    # production maïs UE (Mt)
   wasde_eu_consumption   # consommation UE (Mt)
   wasde_eu_ending_stocks # stocks fin campagne UE (Mt)
   wasde_ukraine_production
   wasde_ukraine_exports
   ```
4. **Ratio stocks EU/monde** :
   ```python
   eu_world_stock_ratio = wasde_eu_ending_stocks / wasde_world_ending_stocks
   eu_stock_use_ratio   = wasde_eu_ending_stocks / wasde_eu_consumption
   ```
5. Anti-leakage : publication date WASDE (habituellement 8-12 du mois), shift approprié.
6. Tests et doc.

#### Critères de validation

- `wasde_eu_ending_stocks` disponible depuis ≥ 2010
- `eu_world_stock_ratio` calculé et dans features.parquet
- `ruff check` : 0 erreur, Tests : PASS

#### Outputs

- Features `wasde_eu_*` et `eu_world_stock_ratio` dans `features.parquet`
- `docs/DATA_WORLD_01_WASDE_EU.md`

---

## BLOC 6 — P4 RAPPORT FINAL

---

### NB-EMA-14 — Module rapport de synthèse final

**Priorité :** P4  
**Type :** notebook_module  
**Statut :** DONE  
**Dépendances :** NB-EMA-05, NB-EMA-06, NB-EMA-07, NB-EMA-08, NB-EMA-09, NB-EMA-10, VALID-GRANGER-01  
**Complexité :** complexe

#### Contexte

Le rapport final répond aux 8 questions centrales de l'étude (§14 de REFLEXION_ETUDE_COMPLETE.md) avec les résultats OOF réels. Il est le document de référence de la Phase Étude.

#### Objectif

Créer `src/mais/research/ema_synthesis_report.py` — agrégateur de tous les artefacts JSON en un rapport Markdown complet.

#### Fichiers à créer

- `src/mais/research/ema_synthesis_report.py`
- `tests/test_ema_synthesis_report.py`
- `docs/EMA_STUDY_FINAL_REPORT.md`
- `artefacts/ema_study/ema_synthesis.json`

#### Tâches

1. Charger tous les artefacts JSON des modules précédents.
2. Construire la table `État réel d'implémentation` ✅/❌/⚠️ pour chaque module.
3. Répondre aux 8 questions de §14 de REFLEXION avec les vraies valeurs numériques.
4. **Générer `docs/EMA_STUDY_FINAL_REPORT.md`** :
   ```
   1. Ce que le CBOT explique (copier résultats Phase R&D)
   2. Comment EMA se relie au CBOT (NB-EMA-04)
   3. Ce que le basis encode (NB-EMA-07)
   4. Décomposition du retour EMA (NB-EMA-05)
   5. Ce que les modèles prédisent — honnêtement (NB-EMA-08)
   6. Ce qu'ils ne prédisent pas — limites (avec les vraies valeurs)
   7. Données EU et leur contribution (DATA-EU-01/02)
   8. Conclusion : prédictibilité EMA vs CBOT
   ```
5. **Table des claims et preuves** (§19 de REFLEXION) mise à jour avec les vraies valeurs.
6. **Table de synthèse** : OUI/NON/PARTIEL pour chaque question, avec IC95%.
7. Vérifier qu'aucune claim non prouvée n'apparaît dans le rapport (grep "validé" vs vraies valeurs).
8. Tests : rapport généré, 8 questions présentes, table ✅/❌/⚠️ complète.

#### Critères de validation

- `docs/EMA_STUDY_FINAL_REPORT.md` contient les 8 réponses avec valeurs numériques réelles
- Table ✅/❌/⚠️ cohérente avec les artefacts JSON
- Aucune claim non prouvée (grep "validé" sur les résultats expérimentaux)
- `ruff check` : 0 erreur
- Tests : PASS

#### Outputs

- `docs/EMA_STUDY_FINAL_REPORT.md`
- `artefacts/ema_study/ema_synthesis.json`

---

## Ordre d'exécution recommandé

```
P0 — Séquentiel obligatoire (nettoyage avant fondations) :
  SCOPE-01 → SCOPE-02 → SCOPE-03
  puis seulement :
  NB-EMA-00 → NB-EMA-01 → NB-EMA-02 → NB-EMA-03 → NB-EMA-04

P1 — Séquentiel (chaîne de dépendances) :
  NB-EMA-04 → NB-EMA-05 → NB-EMA-06
  NB-EMA-05 → NB-EMA-07
  NB-EMA-04 → VALID-GRANGER-01

P1.5 — Avant bloc prédictif :
  UTIL-EMA-01 (fonctions communes) → avant NB-EMA-08/09/10/12/13

P2 — En parallèle après P1 + UTIL-EMA-01 :
  NB-EMA-08, NB-EMA-09, NB-EMA-10, NB-EMA-11, NB-EMA-12, NB-EMA-13

P3 — En parallèle (collecte indépendante de P2) :
  DATA-EU-01, DATA-EU-02 (indépendants), DATA-EU-03, DATA-EU-04, DATA-WORLD-01

P4 — Après tous les modules :
  NB-EMA-14
```

**Ordre exact d'exécution :**
1. SCOPE-01 → 2. SCOPE-02 → 3. SCOPE-03
4. NB-EMA-00 → 5. NB-EMA-01 → 6. NB-EMA-02 → 7. NB-EMA-03 → 8. NB-EMA-04
9. NB-EMA-05 → 10. NB-EMA-06 + NB-EMA-07 (parallèle) → 11. VALID-GRANGER-01
12. UTIL-EMA-01 → 13. NB-EMA-08 → 14. NB-EMA-13 → 15. NB-EMA-09 → 16. NB-EMA-10 → 17. NB-EMA-11 → 18. NB-EMA-12
19. DATA-EU-01 + DATA-EU-02 + DATA-EU-04 (parallèle) → 20. DATA-EU-03 + DATA-WORLD-01
21. NB-EMA-14
