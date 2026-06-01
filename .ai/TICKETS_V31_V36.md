# Tickets — V31..V36 (forward officiel + exploration causes d'échec)

Suite V30. Baseline figée inchangée. `RESEARCH_ONLY_NOT_TRADING`. Holdout verrouillé.
Docs : `docs/V31_V32_V35_ADVERSE_FORWARD.md`, `docs/DECISION_NEXT_STEPS_AFTER_V30.md`.

## V31 — Dashboard forward + séparation projets
- **V31-03** — `DONE` — `v31_forward_dashboard.py` : dashboard lisible du journal officiel (statut
  open/awaiting), markdown + parquet. Tests test_v31 (3 PASS).
- **V31-04** — `DONE` — Séparation explicite PROJET 1 (premium) ≠ PROJET 2 (SELL_THIRDS/cash) documentée.
- **V31-01/02** — `IN_PROGRESS (forward)` — accumulation quotidienne via cron `daily-run --collect` (step
  official_forward déjà branché). Bilan auto à 3/6/12 mois = à venir.

## V32 — ADVERSE path research
- **V32-01** — `DONE` — `v32_adverse_path_research.py` : **ADVERSE prévisible à l'entrée, LOO AUC 0.72**.
  Signature : entry_z bas + basis_level bas. Score ADVERSE_RISK = contexte (pas veto). Tests (3 PASS).

## V35 — CBOT compression engine
- **V35-01** — `DONE` — `v35_cbot_compression_engine.py` : mécanisme CBOT_DRIVEN vs EMA_DRIVEN **NON
  prévisible** (LOO AUC 0.48). Contexte général seulement. (Couvert par tests V32 partagés.)

## V37 — Basis résiduel substitution
- **V37-01** — `DONE` — `v37_substitution_residual.py` : décompose basis = substitution blé/maïs + résidu
  (beta rolling causal). PRÉDICTIF compression OOF : pas de gain (delta −0.045, règle inchangée).
  **DÉCOUVERTE ADVERSE** : résidu élevé → ADVERSE 5.6% vs 27.8% (résidu bas) = 5× ; les pertes se
  concentrent sur les primes justifiées par l'économie blé/maïs. Contexte ADVERSE_RISK, pas veto.
  Tests test_v37 (2 PASS).

## V38 — Module ADVERSE_RISK + substitution blé/maïs (doc `docs/V38_ADVERSE_RISK.md`)
- **V38-01** — `DONE` — `v38_adverse_risk.py` : score ADVERSE_RISK règle-basé (0..3 → LOW/MEDIUM/HIGH)
  assemblé de V32 (prime modérée) + V37 (résidu bas) + V36 (ratio blé/maïs), causaux, aucun fit.
- **V38-04** — `DONE` — Validation descriptive (42 trades) : palier **monotone** ADVERSE 0 %→18 %→25 %
  ET PnL 27.6→11.5→5.0. `ADVERSE_RISK_TIER_SEPARATES`. z→0.5 vs z→0 ≈ neutre PnL (plafonne la queue).
- **V38-02** — `DONE` — Deep dive ratio blé/maïs : corr basis 0.587 ; ratio haut = moins compressible
  (11 % vs 19 %) et plus ADVERSE (24 % vs 10 %) ; avr-juin le plus ADVERSE. `substitution_supports_premium`.
- **V38-05** — `DONE` — `adverse_risk_report_block` appendé à `generate_daily_report` (additif, try/except,
  jamais un veto). Tests test_v38 (3 PASS). Artefacts v38.

## V39-ENRICH — Batch d'expériences d'enrichissement (doc `docs/V39_ENRICHMENT.md`)
- **V39E-01..06** — `DONE` — `v39_enrichment.py` (6 expériences, anti-leakage, descriptif). Tests test_v39 (2 PASS).
  - **E1 durée** : HIGH plus long (61 j) + plus stoppé (0.25) ; LOW long mais 0 stop + revert complet.
  - **E2 coût/queue** : palier HIGH **net-négatif après coût** (−2.0) vs LOW +16 → valide ADVERSE_RISK V38.
  - **E3 éthanol** : `ETHANOL_WEAK_DRIVER_OF_EU_BASIS` (corr basis 0.17, CBOT −0.33). Négatif honnête.
  - **E4 tendance CBOT (DÉCOUVERTE)** : entrer en uptrend CBOT (>SMA50) → ADVERSE 10.5 % vs 21.7 %, PnL
    18 vs 8 → **÷2 ADVERSE, ×2 PnL**. Candidat ADVERSE_RISK (après forward, pas maintenant).
  - **E5 stockage US** : `US_BALANCE_WEAK_DRIVER_OF_EU_BASIS` (corr 0.17). Négatif honnête, cohérent V16.
  - **E6 COT (DÉCOUVERTE convergente)** : managed money net long → ADVERSE 11.8 % vs 23.5 %. Même
    direction qu'E4 → « short premium ≈ long CBOT relatif » renforcé.

## V40 — Substitution blé/maïs approfondie (doc `docs/V40_V41_SUBSTITUTION_CBOT_SUPPORT.md`)
- **V40-01** — `BLOQUÉ DATA` — MATIF blé/maïs : blé pipeline = CBOT (ZW=F), pas Euronext. À brancher comme EMA.
- **V40-04/05/06** — `DONE` — `v40_substitution_deep.py` : **spécificité EU** corr(ratio,basis)=+0.587 vs
  corr(ratio,CBOT)=−0.464 (signes opposés → prime LOCALE EU, pas artefact CBOT) ; reversion ratio haut
  47j/ADVERSE 24% vs bas 29j/9.5% ; interaction énergie négative (TTF data-gated → proxy US). Tests (2 PASS).
- **V40-07** — `PARTIEL` — saison déjà en V38 ; météo EU forecast data-gated.

## V41 — CBOT_SUPPORT_SCORE (doc idem)
- **V41-01/02/05/06** — `DONE` — `v41_cbot_support.py` : score règle-basé (uptrend SMA50 + momentum 20j +
  managed money net), miroir d'ADVERSE_RISK. Gradué NON monotone (HIGH n=8 bruité) MAIS **split binaire
  robuste** : support faible → ADVERSE 21.7%/PnL 8.4 vs CBOT soutenu → 10.5%/18.1
  (`CBOT_SUPPORT_BINARY_ROBUST_GRADED_NOISY`). Bloc ajouté au rapport quotidien. Tests test_v41 (3 PASS).
- **V41-03/04** — `À FAIRE/DATA` — drawdown risk (V29 dispo, non foldé anti-overfit) ; météo US forecast data-gated.

## V42 — Official Data Automation & Backfill (doc `docs/V42_OFFICIAL_DATA_AUTOMATION.md`)
> Nommage : phase recherche V41 = CBOT_SUPPORT (pris) → infra nommée **V42** (= tickets « V41 Automation » demandés).
- **V42-01** — `DONE` — `src/mais/calendar/market_calendar.py` : trading day / week-end / férié Euronext /
  NO_SESSION + expected_settlement / prev/next trading day. Intégré à `data_freshness` (staleness en jours
  de MARCHÉ + bloc calendar). Tests test_market_calendar (5 PASS).
- **V42-02** — `DONE (constat)` — `assess_public_backfill_coverage` : endpoint public = SNAPSHOT du jour,
  pas d'historique profond → `PUBLIC_BACKFILL_TOO_LIMITED_SNAPSHOT_ONLY`. Stratégie 3 niveaux (public /
  Web Services / vendors Bloomberg-LSEG-CQG-TT-Barchart). Store officiel = 2 jours (29 mai + 1 juin).
- **V42-03** — `DONE` — `scripts/run_daily_collect.py` (calendar-aware, --retry) +
  `.github/workflows/daily_market_collect.yml` (20h30 + 07h30 Paris, commit append-only, artefacts).
- **V42-04** — `DONE` — `update_market_sessions` : table sessions append-only (option B) →
  `data/official_forward/market_sessions.{parquet,csv}`. Prix jamais créés le week-end.
- **V42-05** — `DONE (machinerie)` — `proxy_vs_official_tracking` : spread + accord de signal proxy/officiel.
  2 jours → `TOO_SHORT_KEEP_ACCUMULATING` (jalons 10/40/90 j). Tests test_official_automation (3 PASS).
- **V42-06** — `DONE` — monitoring calendar-aware : NO_SESSION → OK_NO_SESSION (jamais FAIL).

## V43 — Matrice de qualité de signal (doc `docs/V43_SIGNAL_QUALITY_MATRIX.md`)
- **V43-01** — `DONE` — `v43_signal_quality_matrix.py` : croise ADVERSE_RISK × CBOT_SUPPORT → quality
  HIGH/MEDIUM/LOW. `QUALITY_SEPARATES_OUTCOMES` (monotone) mais extrêmes fins (HIGH n=1, LOW n=3).
  Cellule robuste : bucket MEDIUM, CBOT soutenu → ADVERSE 11.8% vs 25% / PnL 15.9 vs 6.9. Bloc ajouté au
  rapport quotidien (3e contexte). Tests test_v43 (2 PASS). Contexte, pas veto.

## V44 — Mécanisme & magnitude (doc `docs/V44_MECHANISM_MAGNITUDE.md`)
- **V44-E1** — `DONE (méthodo)` — lead-lag CBOT/EMA : contemporain faible 0.095, pic à 1 j 0.424 →
  `NONSYNC_PRICING_PEAK_AT_1D` = price discovery non-synchrone (settlement), PAS un leadership économique.
  Vraie lead-lag = intraday (data-gated). Justifie le shift(1).
- **V44-E2** — `DONE` — magnitude : baisse +5.7 €/t si signal vs −2.8 sans (anomalie compressible nette,
  n=380) ; OOF R² amplitude 0.093 → `MAGNITUDE_PARTIALLY_PREDICTABLE` (modeste, cohérent V35).
- **V44-E3** — `DONE` — saisonnalité causale basis : prime haute juil-sept (soudure), basse févr/récolte.
  Tests test_v44 (2 PASS).

## Bloqués data (conçus, à relancer)
- **V33** — courbe officielle (basis haut + backwardation vs contango) : besoin de jours officiels.
- **V34** — archive météo prévue réelle : host historical-forecast time out ; accumuler forward.
- **V36** — `DONE (partiel)` — `v36_physical_eu_drivers.py` : TTF gaz EU (eu_cross_assets) intégré +
  ratio blé/maïs. **DÉCOUVERTE : basis ~ ratio blé/maïs r=0.60** (substitution fourragère explique le
  niveau de prime, grounded S&P/commodity-board). TTF~basis 0.26. Gain AUC ADVERSE flaggé overfit
  (9 feats/7 events) → contexte, pas prédicteur. Tests test_v36 (2 PASS). Reste : MARS/FranceAgriMer/
  Ukraine à merger pour un module physique complet.
- **V37** — validation proxy vs officiel (≥40 j puis 3/6/12 mois).
- **V38** — paper trading (coûts réels, slippage) : conditions dans DECISION_NEXT_STEPS_AFTER_V30.md.
