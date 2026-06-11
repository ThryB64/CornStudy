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

### V158 — Official Acquisition Package — `DONE` ✅
- `docs/ACQUISITION_PACKAGE.md` : e-mails prêts (Euronext FR/EN, Barchart EN, CME EN), champs CSV
  exacts, contacts vérifiés, ordre de bataille, engagement d'usage, post-réception. **Action externe
  restante** : envoyer les e-mails (côté utilisateur).

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

### V144 — Proxy↔Officiel Bias Model — `DATA_ACCUMULATING` (débloqué 2026-06-11)
- Sur jours où officiel ET proxy existent : `official = a + b·proxy + régime` ; biais, RMSE, stabilité ;
  backtest proxy-corrigé. **GO** : biais stable réutilisable.
- **Déblocage** : Barchart vit toujours → `proxy_forward_quote.py` quote chaque jour LE MÊME contrat que
  le front officiel (daily CI, journal committé). 1re paire 2026-06-10 : proxy 216.5 = officiel 216.5.
  V144 démarre à ~40 paires (vers fin juillet 2026). 3 tests.

### V140 / V127 — Weather Revision Engine (lead-fixed) — `TODO`
- Open‑Meteo Historical Forecast + Previous Runs (day1..day7) + NOAA NOMADS. Features = **révisions**,
  pas météo réalisée. **Test** : `test_revision_engine_no_future`. **GO** : signal OOS sur day1..day7.

### V141 — Curve Forward Validation — `MACHINERY_DONE / ACCUMULATING` (2026-06-11)
- Valider front-next / Nov-Mar en forward ; factoriser la courbe (niveau/pente/courbure) plutôt que
  flags ad hoc. **GO** : la courbe améliore l'explication.
- `v141_v142_forward_validation.py` branché daily : Spearman sur variations, **gate 40 jours FINAL**
  (actuel : ACCUMULATING_2_DAYS), mûrit automatiquement. 2 tests.

### V142 — MATIF Forward Validation — `MACHINERY_DONE / ACCUMULATING` (2026-06-11)
- Brancher le journal MATIF frais ; confirmer substitution en live. **GO** : robustesse forward.
- Même module et même gate que V141 (ratio MATIF vs Δbasis officiel).

### V147 — Milestone Automation — `TODO`
- Jalons 10/40/90/180/365 jours auto-déclenchés sur jours FINAL accumulés.

### V149 — Multiview Visuals + CI — `TODO`
- Refaire les visuels avec bootstrap/quantiles/number-at-risk, FINAL-only par défaut.

---

## AXES SCIENTIFIQUES NOUVEAUX (issus Parties 3-5)

| ID | Prio | Objet | Issu de | GO |
|---|---|---|---|---|
| V161 T-PARITY | P1 | Parité d'import EU (fair-value physique) + résidu basis | R1,D1,D2,D7,D8 | **`DONE` ✅ (NO_GO honnête, 2026-06-11)** `v161_import_parity.py` + collecteur `comext_unit_value.py` (API COMEXT host dédié, 366 mois 2015→2026-02, UA/BR/EXT_EU). **Réel : corr(basis, parité d'import)=0.089, résidu demi-vie 20.4 j vs basis_z 19.5 j → la parité d'import N'EXPLIQUE PAS la prime** (3e confirmation prime LOCALE après V16 macro + V41 substitution). Lag publication 60 j anti-leakage ; refresh daily ; 2 tests |
| V162 T-VECM | P1 | Cointégration Johansen + ECM EMA/CBOT | R2,X4 | **`DONE` ✅** `v162_vecm_cointegration.py` — cointégré, β=[1,−0.96], α_ema −0.020/α_cbot +0.019 (les 2 jambes corrigent ~50/50), **demi-vie ECM 14.5j** (réconcilie V120 ~17j), NUANCE V21 ; 3 tests verts |
| V163 T-PROXYBIAS | P1 | = V144 | R3,X3 | biais stable |
| V164 T-REGIME-HMM | P2 | START non supervisé (HMM/BOCPD) vs label A | R4,X5 | **`DONE` ✅** `v164_hmm_regime.py` — Markov-switching 2 états sur Δbasis_z ; **85 % des bascules HMM coïncident avec un départ label-A (±5j)** → `START_TRIANGULATED` : le label START est RÉEL (validé indépendamment), complète V153 (réel mais non prédictible ex-ante) ; 2 tests verts |
| V165 T-CURVE-TS | P2 | Facteurs structure par terme | R5 | 3 facteurs forward utiles |
| V166 T-CONVYIELD | P2 | Convenience yield ↔ bilan physique | R6,X9 | chaîne bilan→CY→basis OOS |
| V167 T-SEASON | P1 | Saisonnalité des starts & survie hors-saison | R7,X6 | **`DONE` ✅** `v167_start_seasonality.py` — 63 départs, pic **août/JJA** (24), compression été 1.45z (lente 32j) vs printemps 0.59z (rapide 11.5j), **edge survit hors-saison** ; cohérent horizons V27 ; 2 tests verts |
| V168 T-SUBBASKET | P2 | Panier de substitution élargi | R8 | basket_z > wheat_corn_z seul |
| V169 T-BAYES | P2 | Survie bayésienne hiérarchique | R9 | postérieurs par régime |
| V170 T-DAG | P3 | DAG causal formel & identifiabilité | R10 | liste effets identifiables |
| **V171 T-PLACEBO** | **P0** | Placebo spreads non liés | X1 | **`DONE` ✅** `v171_placebo_spreads.py` — basis EMA Sharpe/trade **0.94 (rang 1/6)** vs meilleur témoin 0.37 → **EDGE_SPECIFIC_TO_EMA_BASIS** (~2.5× le témoin) ; 4 tests verts. Témoins internes (faute de colza/canola) → falsification partielle |
| **V172 T-OVERFIT** | **P0** | Pack anti-overfitting (DSR/PBO/SPA/purged CV) | X2,Partie 5 | `DONE` ✅ `mais/audit/overfitting.py` (PSR/DSR/PBO-CSCV, 6 tests) **+ branché sur trades réels** `v172_overfit_on_trades.py` : baseline z>1 = **32 trades, Sharpe/trade 0.22**, Sharpe ↗ avec seuil (2.0→0.54) ; **Deflated Sharpe NE survit PAS à 50 essais (0.11)** mais **PBO=0.26 ROBUST** (sélection de seuil non sur-ajustée) → `FRAGILE_UNDER_MULTIPLICITY` honnête ; 2 tests. **+ White Reality Check / Hansen SPA** : p_White 0.07 / p_SPA **0.060** (borderline, juste au-dessus de 5 %) → `NOT_SIGNIFICANT_AFTER_SNOOPING`. Défense complète : PBO 0.26 (robuste) + DSR ne survit pas + SPA limite + placebo spécifique (V171) = edge réel/spécifique mais petit après correction. Reste : recensement exhaustif des variantes |
| V173 T-COSTGRID | P1 | Stress coûts×slippage×roll par régime | X8 | **`DONE` ✅ (2026-06-11)** `v173_cost_grid.py` sur les 42 trades réels : **coût de mort global 5 €/t/jambe (slip 0.5)** ; survit à 8 en EXTREME (brut 29.9), été jul_aug (20.4) et CBOT above_trend (20.4) ; meurt à 1-3 en apr_jun/MODERATE/below_trend. Cohérent V167/V10-E ; descriptif, baseline intouchée ; 3 tests |
| V174 T-FX-BCE | P1 | Règle FX BCE officielle horodatée | D6 | **`DONE` ✅ (2026-06-11)** collecteur `ecb_fx_collector.py` (SDMX gratuit, archive committée) + audit `fx_bce.py` : taux BCE 14:15 CET connu avant DSP 18:30 → règle horodatée sans fuite ; **écart BCE vs règle yfinance max 0.19 €/t (PASS)** ; branché daily ; 3 tests |

**Priorité scientifique chronologique** (après V150/V151/V159) :
`V172 → V171 → V174 → V162 → V161 → V167 → V144 → reste`.

---

## CLÔTURE — tickets data-gated / external (honnête)

Ces tickets ne sont **pas** abandonnés : ils sont **bloqués sur une donnée ou une action externe**, pas
sur du code. Le code/la machinerie sont prêts ou triviaux une fois la donnée là.

| Ticket | Blocage | Débloque quand |
|---|---|---|
| V144 proxy↔officiel | **aucun overlap temporel** (proxy s'arrête 2025-07, journal officiel = juin 2026) ; module `official_proxy_validation.py` existe déjà | ≥40 jours officiels accumulés, ou export historique (V158) |
| V165 facteurs de courbe | colonnes proxy trop creuses (f1 n=332, f2 n=7) — comme V141 | courbe officielle multi-échéances accumulée (V125 forward) ou export Euronext |
| V161 parité d'import | besoin FOB Black Sea/Brésil + fret (pas en repo, souvent paywall) | brancher COMEXT prix unitaires (D1) + Baltic (D2) — gratuit mais à collecter |
| V140/V127 weather revision engine | **collecteur CODÉ** `openmeteo_previous_runs.py` (lead-fixe day1..7 + `revision_tape`, 3 tests offline verts) ; archive en WAITING_DATA (réseau indispo ici) | lancer `fetch_previous_runs()` avec réseau → V140 consomme `load_revisions()` |
| V158 envoi e-mails | action externe (utilisateur) | e-mails prêts dans `docs/ACQUISITION_PACKAGE.md` |

## ÉTAT D'AVANCEMENT (mis à jour à chaque session)

- 2026-06-11 (session 2, « continue les tickets intégralement ») : **V174** ✅ (BCE horodaté, écart max
  0.19 €/t vs yfinance), **V173** ✅ (coût de mort 5 €/t/jambe global ; 8 en EXTREME/été/above_trend,
  1-3 en apr_jun/MODERATE/below_trend), **V161** ✅ NO_GO honnête (corr basis↔parité 0.089, résidu ne
  mean-reverte pas mieux → prime LOCALE confirmée 3e fois), **V144 débloqué** (quote proxy forward
  quotidienne du front officiel, 1re paire 06-10 : 216.5=216.5), **V141/V142 machinerie** ✅ (gate 40 j
  FINAL, ACCUMULATING_2_DAYS). 4 nouveaux collecteurs/modules branchés daily (BCE, COMEXT, proxy quote,
  validation forward). 13 tests neufs verts, ruff clean. **Restent data-gated/external** : V165 (courbe
  multi-échéances), V144 (≈40 paires fin juillet), re-run V155 (été), e-mails V158 (utilisateur),
  V166/V168/V169/V170 (P2/P3 ouverts).

- 2026-06-11 (session 1) : **V152-SYNC** ✅ (le CI commite désormais la source unique : data/premium, reports/monthly,
  couches autoritatives ; audit `single_source.py` 7 checks PASS ; monthly V133 quotidien ; 5 tests).
  **V140/V127 DÉBLOQUÉ** ✅ : réseau revenu, bug API corrigé (hourly only), 25 296 lignes collectées
  (17 zones, 92 j), archive append-only `data/weather/forecast_revisions.parquet` + append quotidien CI.
  **V155 (nouveau)** : validation exploratoire révisions→CBOT, n=62 → `PRELIMINARY_N_SMALL` (re-run été).
  **V175 (nouveau)** : signal tiers descriptif — PRE_SIGNAL→signal 47 % (n=34, préavis médian 2 j),
  WATCHLIST→signal 19 %, aucun discriminant ex-ante robuste (artefact gap-jump corrigé) = 3e
  triangulation du timing non prédictible. Restent data-gated : V144 (40 j off.), V165 (courbe),
  V161 (FOB/fret→COMEXT/Baltic à brancher), re-run V155 (été), envoi e-mails V158 (utilisateur).

- 2026-06-10 : tickets posés. **Fondation P0 livrée & testée** : V150 ✅, V159 ✅, V151 ✅ (partiel),
  V153 ✅. ruff clean, 182 tests verts, 0 régression. Backfill réel exécuté (1 FINAL/8 PROVISIONAL).
  V153 run réel : START AUC 0.549 → timing du départ non démontré (confirme audits).
  **Poussé sur main** (2 commits, fast-forward). **V172 T-OVERFIT** ✅ implémenté (PSR/DSR/PBO-CSCV,
  6 tests). **Daily corrigé** : politique REVISED (le run du soir FINAL upgrade le PROVISIONAL du
  matin — l'ancien code skippait en ALREADY_LOGGED, d'où 8/9 lignes PROVISIONAL).
  **V152** ✅ (event study 2.0) + **V162** ✅ (VECM) + **V167** ✅ (saison) + **V172-réel** ✅ (DSR/PBO/
  SPA sur trades) + **V171** ✅ (placebo, edge spécifique) + **V164** ✅ (HMM, START triangulé) +
  **V158** ✅ (package acquisition). **9 pushes.**
  **Implémentables faits.** Restent UNIQUEMENT data-gated/external (voir section Clôture) : V144, V165,
  V161, V140/V127 (données à collecter), envoi e-mails V158 (utilisateur).
  **Bilan robustesse (sur trades réels)** : edge SPÉCIFIQUE (V171 rang 1/6) + sélection ROBUSTE (PBO
  0.26) mais PETIT/LIMITE (DSR ne survit pas à 50 essais, SPA p≈0.06) ; START réel (V164 85 %) mais
  non prédictible ex-ante (V153 AUC 0.55) ; correction symétrique 2 jambes (V162, nuance V21).
