# TICKETS — Suite de l'étude EMA/CBOT (V150 → V174)

> Tickets exécutables issus de `.ai/REFLEXION_SUITE_ETUDE.md` (deux audits fusionnés).
> Statut : `TODO` / `IN_PROGRESS` / `DONE` / `NEEDS_REVIEW` / `WAIT`.
> Règle : aucun ticket P1+ de science ne démarre avant que la fondation P0 (V150/V151/V159) soit verte.

## Légende priorité
- **P0** : fondation vérité des données. Bloque tout le reste.
- **P1** : science explicative + acquisition.
- **P2/P3** : extensions, reruns, descriptif.

---

## FONDATION P0

### V150 — Sessionized Official Journal — `DONE` ✅
- **Objet** : chaque ligne du journal officiel porte `record_status` (PROVISIONAL/FINAL/SETTLING/
  REVISED), `collected_at_utc`, `collected_at_paris`, `effective_session_date`, `provisional_warning`.
- **Sous-tâches** :
  - [x] `stamp_timing` existe (`mais/premium/session_timing.py`).
  - [x] Backfill append-only des 9 lignes existantes depuis `logged_at` → 1 FINAL + 8 PROVISIONAL.
  - [x] Estampillage **toujours** appliqué dans `v27_official_forward.append_forward_journal`.
  - [x] Loader `load_forward_journal(final_only=...)` + `latest_final_record()`.
  - [x] Politique REVISED (PROVISIONAL→FINAL en nouvelle ligne, passé jamais réécrit).
- **Tests** : `test_session_truth_v150.py` (5 tests verts) + `test_session_timing.py`.
- **GO atteint** : 100 % des lignes ont une vérité de session ; loader FINAL-only OK.

### V159 — Reproducibility / Audit Test Pack — `DONE` ✅
- `mais/audit/data_truth.py` : session_alignment, finality_gate, cbot_eur_roundtrip (err max 0.008 €/t),
  contract_selection → `artefacts/audit/`. Overall **PASS**. Tests `test_data_truth_audit_v159.py`.

### V151 — Premium Head Single Source — `DONE (partiel)` ✅
- Head expose `session_truth` + `session_warning` (dernier jour PROVISOIRE). Bloc rapport enrichi.
  Tests `test_premium_head.py` verts. **Reste** : brancher dashboard/monthly/lifecycle sur la vue
  FINAL-only (V145/V146/V133).
- **Objet** : head/dashboard/monthly/lifecycle lisent une seule source ; FINAL par défaut ; warning si
  l'état le plus frais est PROVISIONAL.
- **Tests** : `test_single_source_truth_consistency`, `test_dashboard_reads_head_only`.
- **GO** : latest/head/dashboard concordent, aucune lecture stale silencieuse.
- **Dépend de** : V150.

### V159 — Reproducibility / Audit Test Pack — `IN_PROGRESS`
- **Objet** : module `mais/audit/` produisant les rapports de l'§8bis.2 + suite de tests no-lookahead.
- **Audits** : session_alignment, finality_gate, cbot_eur_roundtrip, proxy_vs_official, zscore_recalc,
  contract_selection, event_timestamp.
- **Tests** : un test par audit, tous verts.
- **GO** : pack d'audit exécutable, artefacts écrits sous `artefacts/audit/`.

### V158 — Official Acquisition Package — `TODO` (parallèle, à lancer tôt)
- **Objet** : e-mails prêts (Euronext FR/EN, Barchart FR/EN, CME), champs CSV exacts, contacts, budget.
- **Contacts** : Euronext formulaire Web Services (+ datasolutions@euronext.com à reconfirmer) ;
  Barchart solutions@barchart.com ; CME CMEDataSales@cmegroup.com.
- **Livrable** : `docs/ACQUISITION_PACKAGE.md` + templates.
- **GO** : package complet, prêt à envoyer.

---

## SCIENCE EXPLICATIVE P1

### V152 — Compression Event Study 2.0 — `DONE` ✅
- `mais/research/v152_event_study_v2.py` : aligné start A (premium élevé), [-30,+90], moyenne+médiane+
  q25/75+**IC bootstrap 95 %**+censure (n par offset)+**PNG**. **Run réel : 63 épisodes, basis_z médian
  1.33 au start → 0.34 à +90j** (compression médiane ~1.0 z). Tests `test_v152_event_study.py` (3 verts).

### V153 — START vs IN_PROGRESS Split — `DONE` ✅
- `mais/research/v153_start_vs_inprogress.py` : renommage `COMPRESSION_PROGRESS_SCORE` (descriptif) +
  labels START/INPROG **sans lookahead** (test de non-fuite vert, `test_v153_start_vs_inprogress.py`).
- **Run réel** (5940 j, holdout) : START_h10 AUC OOF **0.549** (base 0.125) ; INPROG_h10 0.521 (base
  0.651). Verdict `START_TIMING_REMAINS_HARD_DESCRIPTIVE_ONLY` → **rejet honnête**, confirme les audits.

### V144 — Proxy↔Officiel Bias Model — `TODO`
- Sur jours où officiel ET proxy existent : `official = a + b·proxy + régime` ; biais, RMSE, stabilité ;
  backtest proxy-corrigé. **GO** : biais stable réutilisable.

### V140 / V127 — Weather Revision Engine (lead-fixed) — `TODO`
- Open‑Meteo Historical Forecast + Previous Runs (day1..day7) + NOAA NOMADS. Features = **révisions**,
  pas météo réalisée. **Test** : `test_revision_engine_no_future`. **GO** : signal OOS sur day1..day7.

### V141 — Curve Forward Validation — `TODO`
- Valider front-next / Nov-Mar en forward ; factoriser la courbe (niveau/pente/courbure) plutôt que
  flags ad hoc. **GO** : la courbe améliore l'explication.

### V142 — MATIF Forward Validation — `TODO`
- Brancher le journal MATIF frais ; confirmer substitution en live. **GO** : robustesse forward.

### V147 — Milestone Automation — `TODO`
- Jalons 10/40/90/180/365 jours auto-déclenchés sur jours FINAL accumulés.

### V149 — Multiview Visuals + CI — `TODO`
- Refaire les visuels avec bootstrap/quantiles/number-at-risk, FINAL-only par défaut.

---

## AXES SCIENTIFIQUES NOUVEAUX (issus Parties 3-5)

| ID | Prio | Objet | Issu de | GO |
|---|---|---|---|---|
| V161 T-PARITY | P1 | Parité d'import EU (fair-value physique) + résidu basis | R1,D1,D2,D7,D8 | résidu mean-reverte mieux que basis_z |
| V162 T-VECM | P1 | Cointégration Johansen + ECM EMA/CBOT | R2,X4 | **`DONE` ✅** `v162_vecm_cointegration.py` — cointégré, β=[1,−0.96], α_ema −0.020/α_cbot +0.019 (les 2 jambes corrigent ~50/50), **demi-vie ECM 14.5j** (réconcilie V120 ~17j), NUANCE V21 ; 3 tests verts |
| V163 T-PROXYBIAS | P1 | = V144 | R3,X3 | biais stable |
| V164 T-REGIME-HMM | P2 | START non supervisé (HMM/BOCPD) vs label A | R4,X5 | accord offset ≤3j ≥70 % épisodes |
| V165 T-CURVE-TS | P2 | Facteurs structure par terme | R5 | 3 facteurs forward utiles |
| V166 T-CONVYIELD | P2 | Convenience yield ↔ bilan physique | R6,X9 | chaîne bilan→CY→basis OOS |
| V167 T-SEASON | P1 | Saisonnalité des starts & survie hors-saison | R7,X6 | **`DONE` ✅** `v167_start_seasonality.py` — 63 départs, pic **août/JJA** (24), compression été 1.45z (lente 32j) vs printemps 0.59z (rapide 11.5j), **edge survit hors-saison** ; cohérent horizons V27 ; 2 tests verts |
| V168 T-SUBBASKET | P2 | Panier de substitution élargi | R8 | basket_z > wheat_corn_z seul |
| V169 T-BAYES | P2 | Survie bayésienne hiérarchique | R9 | postérieurs par régime |
| V170 T-DAG | P3 | DAG causal formel & identifiabilité | R10 | liste effets identifiables |
| **V171 T-PLACEBO** | **P0** | Placebo spreads non liés | X1 | maïs domine témoins |
| **V172 T-OVERFIT** | **P0** | Pack anti-overfitting (DSR/PBO/SPA/purged CV) | X2,Partie 5 | `DONE` ✅ `mais/audit/overfitting.py` (PSR/DSR/PBO-CSCV, 6 tests) **+ branché sur trades réels** `v172_overfit_on_trades.py` : baseline z>1 = **32 trades, Sharpe/trade 0.22**, Sharpe ↗ avec seuil (2.0→0.54) ; **Deflated Sharpe NE survit PAS à 50 essais (0.11)** mais **PBO=0.26 ROBUST** (sélection de seuil non sur-ajustée) → `FRAGILE_UNDER_MULTIPLICITY` honnête ; 2 tests. Reste : SPA + recensement exhaustif des variantes |
| V173 T-COSTGRID | P1 | Stress coûts×slippage×roll par régime | X8 | coût-seuil de mort de l'edge |
| V174 T-FX-BCE | P1 | Règle FX BCE officielle horodatée | D6 | abs_err reconstruction réduit |

**Priorité scientifique chronologique** (après V150/V151/V159) :
`V172 → V171 → V174 → V162 → V161 → V167 → V144 → reste`.

---

## ÉTAT D'AVANCEMENT (mis à jour à chaque session)

- 2026-06-10 : tickets posés. **Fondation P0 livrée & testée** : V150 ✅, V159 ✅, V151 ✅ (partiel),
  V153 ✅. ruff clean, 182 tests verts, 0 régression. Backfill réel exécuté (1 FINAL/8 PROVISIONAL).
  V153 run réel : START AUC 0.549 → timing du départ non démontré (confirme audits).
  **Poussé sur main** (2 commits, fast-forward). **V172 T-OVERFIT** ✅ implémenté (PSR/DSR/PBO-CSCV,
  6 tests). **Daily corrigé** : politique REVISED (le run du soir FINAL upgrade le PROVISIONAL du
  matin — l'ancien code skippait en ALREADY_LOGGED, d'où 8/9 lignes PROVISIONAL).
  **V152** ✅ (event study 2.0, 63 épisodes, PNG) + **V162** ✅ (VECM, demi-vie ECM 14.5j, 2 jambes
  corrigent ~50/50 → nuance V21). 4e push.
  **Prochaine session** : brancher V172 sur les 42 trades réels → V144 proxy↔officiel → T-PLACEBO
  → V161 parité d'import → V167 saison → V140/V127 weather revision → V158 e-mails acquisition.
