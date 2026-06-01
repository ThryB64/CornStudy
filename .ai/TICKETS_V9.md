# Tickets — V9 Indicateur Structurel Prime EMA/CBOT

Programme V9 = construction et validation honnête du **prototype d'indicateur** recommandé par
la synthèse V8 (`docs/V8_DEEP_DIVE_RESULTATS.md`, §7-9). V8 a démontré que la complexité
(meta-stacking V6 AUC 0.937) est un artefact : un **modèle structurel à 6 variables** atteint la
même performance (AUC ~0.66) sous protocole strict. V9 transforme ce constat en indicateur
explicite, calibré, avec abstention et vetoes, puis le valide en LOYO + backtest stressé + red team.

Statut global hérité maintenu : `RESEARCH_ONLY_NOT_TRADING`. Holdout 2024 reste verrouillé
(`artefacts/v8/holdout_lock.json`), jamais touché sans signature humaine explicite.

## Statuts autorisés
`READY` `IN_PROGRESS` `NEEDS_REVIEW` `DONE` `BLOCKED` `WAITING_DATA` `REJECTED`

## Convention
- Données chargées via `mais.scripts.run_v8_phase_a.load_master_dataset` + `filter_out_holdout`.
- Cible directionnelle primaire : `y_rel_outperform_h40` (EMA surperforme CBOT sur 40j).
- Anti-leakage : `shift(1)` déjà appliqué dans `build_features()`, OOF purged embargo, calibration
  apprise sur train uniquement.
- Coûts backtest en €/t **par leg** (spread = 2 legs).

---

## Phase 1 — Acquisition données officielles (WAITING_DATA, hérité V7/V8)

Bloqué par données externes payantes/manuelles. Non requis pour le prototype.

- **V9-DATA-01** — `WAITING_DATA` — EMA officiel Euronext NextHistory (remplace barchart_proxy).
- **V9-DATA-02** — `WAITING_DATA` — EC MARS automatisé.
- **V9-DATA-03** — `WAITING_DATA` — FranceAgriMer + Eurostat COMEXT.

---

## Phase 2 — Prototype indicateur (constructible avec données actuelles)

### V9-IND-01 — Indicateur structurel hybride V9
- Statut : `DONE`
- Difficulté : `critique`
- Dépendances : aucune (données V8 disponibles)

**Objectif :** Construire l'indicateur cible décrit en V8 §7 :
- Cœur : régression logistique structurelle 6 variables (cbot_eur, basis_z, eurusd, month_sin,
  month_cos, oi_proxy), OOF purged embargo, calibration **Isotonic train-only**.
- Couche saisonnière : initialement jul_aug direct / apr_jun inversé / sep_nov+dec abstention (hypothèse
  V8). **CORRECTION V9 (mesurée OOF)** : l'inversion apr-juin (DA 0.476) et l'abstention sep-déc sont
  FALSIFIÉES → cœur direct conservé sur toutes les saisons ; saison = label de driver seulement.
- Couche règles mean-reversion : R2 (`basis_z < -1.5` → LONG_PREMIUM), R5
  (`basis_z > 1.5` × jan-mar → SHORT_PREMIUM).
- Vetoes : data quality (`ema_data_availability_score < 0.4`), liquidité OI faible, proximité WASDE
  (`days_to_next_wasde ≤ 2`), roll-risk proxy.
- Sortie : `signal ∈ {LONG_PREMIUM, SHORT_PREMIUM, ABSTAIN}`, `confidence ∈ [0,1]`, `drivers`,
  `veto_reasons`, `horizon=40`, `statut=RESEARCH_ONLY_NOT_TRADING`.

**Fichiers à créer :** `src/mais/indicator/structural_indicator_v9.py`,
`tests/test_v9_structural_indicator.py`, `src/mais/scripts/run_v9.py`.

**Critères :** AUC OOF cœur ≥ 0.60 ; calibration Isotonic ECE ≤ raw ; coverage / accuracy par tier
mesurés honnêtement ; snapshot exploitable le plus récent produit ; artefact
`artefacts/v9/structural_indicator_v9.json`.

### V9-IND-02 — Validation Leave-One-Year-Out
- Statut : `DONE`
- Difficulté : `complexe`
- Dépendances : V9-IND-01

**Objectif :** LOYO sur le cœur structurel : pour chaque année, entraîner sur les autres, prédire
l'année tenue. Mesurer AUC/DA par année, stabilité (std), nombre d'années AUC > 0.55.
**Artefact :** `artefacts/v9/loyo_v9.json`.

### V9-IND-03 — Backtest V4 stressé
- Statut : `DONE`
- Difficulté : `complexe`
- Dépendances : V9-IND-01

**Objectif :** Backtest du spread EMA/CBOT H40 piloté par les signaux V9 (non-overlap strict),
coûts {0,1,2,3,5,8} €/t par leg. Mesurer PnL, hit rate, profit factor, max drawdown, part d'années
positives. Verdict maintenu `RESEARCH_ONLY_NOT_TRADING`. **Artefact :** `artefacts/v9/backtest_v4.json`.

### V9-IND-04 — Red team V2
- Statut : `DONE`
- Difficulté : `moyen`
- Dépendances : V9-IND-01

**Objectif :** Test de permutation (≥100 perms) sur l'AUC OOF du cœur structurel et sur l'accuracy
des signaux non-abstenus. p-value empirique. **Artefact :** `artefacts/v9/red_team_v2.json`.

### V9-IND-05 — Synthèse V9
- Statut : `DONE`
- Difficulté : `moyen`
- Dépendances : V9-IND-01..04

**Objectif :** Doc `docs/V9_STRUCTURAL_INDICATOR.md` consolidant architecture, résultats,
limites, et le verdict de promotion (GO_LOYO / FRAGILE / NO_GO) conditionnant l'usage du holdout 2024.

---

## Phase 3 — Holdout (bloqué par signature humaine)

- **V9-HOLDOUT-2024** — `BLOCKED` — usage UNIQUE du holdout 2024, requiert signature humaine
  explicite ET V9-IND-02 + V9-IND-04 PASS.
