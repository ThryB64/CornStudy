# Backlog VNEXT — tickets priorisés et exécutables

Statut : RESEARCH_ONLY_NOT_TRADING. Baseline `basis_z` figée. Holdout 2024 verrouillé.
Ordre = priorité. Champs par ticket : Objectif · Pourquoi · Données · Source · Leakage · Métriques ·
Livrables · Statut attendu (GO / WATCHLIST / DATA_BLOCKED / EXPLANATORY_ONLY).

---

## A — AUDIT & HARDENING (à fermer avant toute nouvelle piste)

### VN-A1 — Single source of truth premium + séparation legacy
- **Objectif** : un `premium_daily_head.json` autoritatif (le seul « dernier état » premium) ; toutes les
  autres couches s'y réfèrent ou sont marquées STALE / LEGACY / REPORTING_ONLY. Marquer explicitement
  `ops/daily.py`, `decision/`, `farmer_backtest` comme LEGACY hors périmètre premium.
- **Pourquoi** : le dépôt mélange l'indicateur premium et un pipeline farmer/SELL_NOW ; un lecteur peut
  confondre les états et les périmètres.
- **Données** : artefacts V132/V122/V101 + journal. Aucune externe.
- **Source** : interne.
- **Leakage** : aucun (orchestration/étiquetage).
- **Métriques** : le head pointe vers le même `as_of` que le journal ; 0 mention farmer/SELL_NOW dans le head.
- **Livrables** : `v_head_premium.py` (build `premium_daily_head.json`), bannière LEGACY dans le rapport
  legacy, doc périmètre `docs/PREMIUM_SCOPE.md`, tests.
- **Statut attendu** : GO.

### VN-A2 — Session timing PROVISIONAL/FINAL/REVISED de bout en bout
- **Objectif** : estampiller chaque ligne forward avec `collected_at_utc`, `collected_at_paris`,
  `effective_session_date`, `record_status` ∈ {PROVISIONAL, FINAL, REVISED}, `cbot_close_date`,
  `eurusd_close_date` ; règle DSP 18:30 CET (PROVISIONAL avant, FINAL après 18:35) ; invariants vérifiés.
- **Pourquoi** : risque méthodologique #1 — un snapshot du matin reprend le settlement de la veille daté du
  jour → faux changement de signal. Le DSP commodités reste 18:30 CET malgré l'extension à 20:15.
- **Données** : journal V27, snapshots officiels.
- **Source** : interne + règle Euronext (DSP 18:30 CET).
- **Leakage** : élimine un look-ahead d'horodatage ; révision FINAL interdite (V122).
- **Métriques** : invariants (effective_session_date cohérente avec l'heure de collecte ; pas de FINAL avant
  18:35) ; n violations détectées = 0.
- **Livrables** : `v_session_timing.py` (stamping + invariants), extension de `append_forward_journal`,
  tests des cas matin/soir/week-end.
- **Statut attendu** : GO.

### VN-A3 — Audit du signe de courbe (contango/backwardation) sur toutes les couches
- **Objectif** : vérifier que front-next, le signe, et la définition contango/backwardation sont identiques
  entre snapshot brut, V30, V109, V125, V132.
- **Pourquoi** : une incohérence de signe fausserait PHYSICAL_TENSION et l'objectif recommandé.
- **Données** : snapshots de courbe accumulés.
- **Source** : interne.
- **Leakage** : aucun.
- **Métriques** : concordance 100% du `curve_shape` entre couches sur les dates communes.
- **Livrables** : `v_curve_sign_audit.py` + test ; corrections si divergence.
- **Statut attendu** : GO.

### VN-A4 — quality_flag & fraîcheur robustes
- **Objectif** : éviter les faux `low_liquidity` quand le volume est simplement absent (utiliser OI, pas
  seulement volume) ; brancher la fraîcheur (V123) dans le head.
- **Pourquoi** : un faux low_liquidity dégrade la confiance à tort.
- **Données** : snapshots (OI/volume), V123.
- **Source** : interne.
- **Leakage** : aucun.
- **Métriques** : quality_flag stable sur jours à volume manquant mais OI normal.
- **Livrables** : correctif quality_flag + test.
- **Statut attendu** : GO.

### VN-A5 — CI Parquet + docs mois de contrat + restatuts de sources
- **Objectif** : épingler pyarrow en CI ; corriger docs obsolètes sur les mois de contrat ; appliquer les
  restatuts de V134 (COMEXT → PARTIAL, USDA/Previous-Runs → ACTIONABLE).
- **Pourquoi** : distinguer erreurs d'environnement vs logiques ; tenir la doc à jour.
- **Données** : —
- **Source** : interne + sources officielles consultées.
- **Leakage** : aucun.
- **Métriques** : CI reproductible ; V134 à jour.
- **Livrables** : note CI, MAJ `DATA_SOURCING_PLAN.md` + `v134`.
- **Statut attendu** : GO.

---

## B — RED-TEAM DES RÉSULTATS

### VN-B1 — Réécrire la narration trigger V105 (conforme aux chiffres)
- **Objectif** : corriger l'`interpretation` de V105 : les chiffres mesurent CBOT **−0.0241** (et CBOT_DRIVEN
  −0.0145) en pré-start ; le CBOT **baisse** légèrement avant le début de compression, il ne monte pas. La
  narration « si le CBOT monte … c'est le précurseur » est fausse. Conclusion honnête = pas de précurseur
  CBOT haussier ; cohérent avec V106 (score inversé, reflète l'en-cours).
- **Pourquoi** : décalage narration/chiffres = risque de fausse conclusion propagée.
- **Données** : artefact V105 (déjà calculé).
- **Source** : interne.
- **Leakage** : aucun (ex-post).
- **Métriques** : interpretation alignée au signe réel ; verdict inchangé (NO_CLEAR_SINGLE_PRECURSOR).
- **Livrables** : patch `v105_compression_event_study.py` (texte) + note red-team.
- **Statut attendu** : GO.

### VN-B2 — Scan systématique interpretation vs chiffres
- **Objectif** : balayer les artefacts research dont l'`interpretation` pourrait « raconter » plus que les
  nombres ; produire une liste d'écarts.
- **Pourquoi** : éviter d'autres V105.
- **Données** : artefacts JSON.
- **Source** : interne.
- **Leakage** : aucun.
- **Métriques** : n écarts narration/chiffres détectés.
- **Livrables** : `docs/REDTEAM_NARRATIVE_SCAN.md`.
- **Statut attendu** : EXPLANATORY_ONLY.

---

## C — DONNÉES LEADING À OUVRIR

### VN-C1 — Probe historique de l'endpoint Euronext public
- **Objectif** : tester si le petit endpoint AJAX public admet un paramètre d'historique court ; sinon
  documenter `NO_PUBLIC_RANGE` et basculer sur les voies officielles (Web Services / NextHistory / CFTS).
- **Pourquoi** : ne pas présumer l'historique d'un endpoint de snapshot live.
- **Données** : endpoint Euronext.
- **Source** : publique (probe) / officielle (à activer).
- **Leakage** : aucun.
- **Métriques** : présence/absence prouvée d'un range.
- **Livrables** : `v_euronext_history_probe.py` + verdict ; MAJ V134.
- **Statut attendu** : WATCHLIST (probable NO_PUBLIC_RANGE).

### VN-C2 — COMEXT requalifié : bulk download maïs UE
- **Objectif** : récupérer le bulk CSV mensuel/annuel COMEXT (flux maïs UE) et l'intégrer comme série.
- **Pourquoi** : flux physiques EU = brique majeure de la prime locale ; statut DATA_BLOCKED était erroné.
- **Données** : COMEXT bulk (CN maïs, import/export UE).
- **Source** : publique officielle (Eurostat bulk).
- **Leakage** : mensuel → shift(1) + publication lag ; jamais réindexé.
- **Métriques** : série récupérée, n mois, couverture.
- **Livrables** : `collect/comext_bulk.py` + test (mock) + artefact ; MAJ V134.
- **Statut attendu** : WATCHLIST→GO si bulk accessible, sinon DATA_BLOCKED honnête.

### VN-C3 — Indice de tension physique UE (COMEXT + FranceAgriMer + MARS)
- **Objectif** : indice mensuel→nowcast « prime justifiée vs fragile » (balance locale EU).
- **Pourquoi** : rendre l'indicateur capable de dire « prime haute mais justifiée » vs « prête à se dégonfler ».
- **Données** : COMEXT (VN-C2), FranceAgriMer bilans, MARS rendements.
- **Source** : publiques officielles.
- **Leakage** : variables de balance (lentes) shift(1) ; pas de timing journalier.
- **Métriques** : relation à la durée/compression des primes (descriptif), pas une AUC.
- **Livrables** : `v_eu_physical_pressure.py` + test + doc.
- **Statut attendu** : WATCHLIST (dépend C2 + parsing MARS/FAM).

### VN-C4 — Forecast revision tape (Open-Meteo Previous-Runs)
- **Objectif** : vraies révisions multi-lead — Δ jours >32°C lead 3 jour-sur-jour, Δ pluie lead 5, écart
  run-précédent/courant, dispersion inter-modèles, surprise vs climatologie.
- **Pourquoi** : transformer « météo chaude = storytelling » en révisions datées, anti-leakage, leading.
- **Données** : Open-Meteo Previous-Runs (lead 1-7 j depuis 2024) + Historical Forecast.
- **Source** : publique gratuite.
- **Leakage** : daté à l'émission ; révision = Δ entre runs ; jamais réindexé.
- **Métriques** : lien révision→direction CBOT/durée prime (descriptif).
- **Livrables** : `collect/openmeteo_previous_runs.py` + `v_forecast_revision_tape.py` + tests + journal.
- **Statut attendu** : WATCHLIST→GO (best-effort timeout).

### VN-C5 — Calendrier USDA exact (event tape)
- **Objectif** : dates officielles WASDE/Grain Stocks/Acreage/Crop Progress 2026 + QuickStats ; brancher dans
  V137 pour distance-au-rapport exacte.
- **Pourquoi** : passer V129/V137 du proxy à l'horodatage exact.
- **Données** : calendrier USDA officiel, NASS QuickStats (clé gratuite).
- **Source** : publique officielle.
- **Leakage** : dates connues à l'avance → utilisables comme distance ; réaction = ex-post.
- **Métriques** : couverture du calendrier ; raffinement attribution V137.
- **Livrables** : `collect/usda_release_calendar.py` + test + MAJ V137.
- **Statut attendu** : GO (calendrier statique) / WATCHLIST (QuickStats live).

---

## D — NOUVELLES EXPÉRIENCES (changement de modèle)

### VN-D1 — Modèle de hazard time-to-compression-start
- **Objectif** : P(compression démarre dans 5/10/20 j) ; covariables strictement causales.
- **Pourquoi** : remplacer « retournement exact demain » (non prédictible) par une probabilité conditionnelle.
- **Données** : master (basis_z, vitesse spread, distance report, révisions météo, COT, substitution, roll).
- **Source** : interne + C4/C5.
- **Leakage** : covariables < t, cible future ; walk-forward ; holdout intact.
- **Métriques** : OOF AUC/Brier par horizon vs base rate ; calibration.
- **Livrables** : `v_hazard_compression.py` + tests + artefact.
- **Statut attendu** : WATCHLIST (honnête : V106 a montré le timing dur).

### VN-D2 — Transitions d'état de l'indicateur
- **Objectif** : trajectoires EXTREME_STATIC / EXTREME_EARLY_RELAXATION / STRONG_CBOT_CATCHUP /
  STRONG_PHYSICAL_JUSTIFIED / WAIT_CONFIRMATION / ADVERSE_DRIFT (au lieu du seul tier).
- **Pourquoi** : plus de signaux exploitables sans baisser brutalement les seuils.
- **Données** : journal + diagnostics (tension, CBOT_SUPPORT, MFE/MAE, révisions).
- **Source** : interne.
- **Leakage** : état à t depuis l'info à t ; pas de futur.
- **Métriques** : cohérence des transitions, distribution, lien au PnL réalisé (descriptif).
- **Livrables** : `v_state_transitions.py` + tests + intégration head.
- **Statut attendu** : GO (descriptif décisionnel).

### VN-D3 — Discriminant « bon short premium vs ADVERSE » post-entrée
- **Objectif** : ce qui distingue tôt un mauvais short (MFE faible, spread qui ne se détend pas, CBOT_SUPPORT
  qui se renforce, révision météo défavorable, ratio blé/maïs qui se tend).
- **Pourquoi** : vrai filtre professionnel (≠ prédire la compression en général).
- **Données** : épisodes V82 + diagnostics post-entrée.
- **Source** : interne.
- **Leakage** : features j+1..j+k post-entrée, cible = issue ADVERSE/gagnant ; pas de look-ahead au-delà de l'horizon évalué.
- **Métriques** : séparation ADVERSE (gap), robustesse ex-crise.
- **Livrables** : `v_adverse_discriminator.py` + tests + doc.
- **Statut attendu** : WATCHLIST (n petit).

### VN-D4 — Explication hiérarchique par familles de drivers
- **Objectif** : familles (CBOT, météo anticipée, tension EMA, substitution, balance UE, calendrier) →
  contribution marginale sur 3 cibles (P(compression), temps→z0.5, risque ADVERSE).
- **Pourquoi** : défendable devant un externe ; ≠ boîte noire.
- **Données** : master + C3/C4/C5.
- **Source** : interne + leading C.
- **Leakage** : strict, walk-forward.
- **Métriques** : Δ contribution par famille (ablation), pas une AUC magique.
- **Livrables** : `v_hierarchical_explanation.py` + tests + doc.
- **Statut attendu** : EXPLANATORY_ONLY→GO si une famille améliore vraiment une décision.

---

## E — EVENT MODE FORWARD (le levier « quand »)

### VN-E1 — Capture intraday du soir les jours d'événements
- **Objectif** : snapshots publics répétés (17:55/18:05/18:20/18:35/19:00/20:15 CET) les jours
  WASDE/Grain Stocks/Acreage/gros appels d'offres/chocs météo ; append-only ; PROVISIONAL avant 18:30.
- **Pourquoi** : avec l'extension à 20:15 CET (réagir aux WASDE pendant que CME est ouvert), on peut bâtir
  une base microstructure du soir SANS intraday payant.
- **Données** : endpoint Euronext public (toutes échéances : settlement/last, OI, bid/ask) + CBOT live.
- **Source** : publique.
- **Leakage** : horodatage strict ; PROVISIONAL/FINAL ; pas de réindexation.
- **Métriques** : nb d'événements capturés, complétude des snapshots.
- **Livrables** : `collect/euronext_evening_snapshots.py` + scheduler/cron doc + journal append-only + tests.
- **Statut attendu** : GO (forward, s'accumule).

### VN-E2 — Base microstructure événementielle EMA
- **Objectif** : mesurer la réaction du front, du spread front-next, de la courbe et du ratio substitution
  autour des événements (intra-soir et J+1).
- **Pourquoi** : c'est la donnée qui manque pour comprendre les débuts de compression.
- **Données** : VN-E1 + CBOT + calendrier C5.
- **Source** : interne (dérivé E1).
- **Leakage** : ex-post sur événements passés ; forward.
- **Métriques** : Δfront/Δspread/Δcourbe par type d'événement (descriptif).
- **Livrables** : `v_event_microstructure.py` + tests + doc.
- **Statut attendu** : WATCHLIST (dépend de E1 accumulé).

---

## Ordre d'exécution

1. **A** (A1→A5) — fermer la dette avant tout. 2. **B** (B1→B2) — red-team rapide. 3. **C** (C1→C5) — ouvrir
les sources. 4. **E1** — démarrer la capture forward tôt (s'accumule pendant le reste). 5. **D** (D1→D4) puis
**E2** — modèles + microstructure quand les données existent.

## Invariants (tous tickets)

Baseline figée ; seuils inchangés ; aucune optimisation sur les 42 trades ; holdout intact ; anti-leakage
strict ; imports optionnels try/except ; tests + ruff + doc + artefact ; statuts honnêtes ; si une piste
échoue on l'écrit. RESEARCH_ONLY_NOT_TRADING.
