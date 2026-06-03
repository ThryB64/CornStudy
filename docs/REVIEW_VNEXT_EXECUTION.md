# Review d'exécution VNEXT (A → E)

Date : 2026-06-03. Statut : RESEARCH_ONLY_NOT_TRADING. Baseline figée, holdout verrouillé.
Bilan de l'exécution du backlog VNEXT (docs : REFLEXION_VNEXT, TICKETS_VNEXT, REVIEW_TICKETS_VNEXT).

## A — Audit & hardening (FAIT)

- **A1 single source of truth** : `data/premium/premium_daily_head.json` (`mais.premium.head`) — le seul
  « dernier état » premium, `scope_clean=True` (aucun SELL_NOW/farmer), couches REPORTING_ONLY/LEGACY
  explicitées. Doc `PREMIUM_SCOPE.md`. Head = headline du rapport quotidien + étape finale du collecteur.
- **A2 session timing** : `mais.premium.session_timing` — PROVISIONAL/FINAL/SETTLING selon DSP 18:30 CET
  (Paris), champs `collected_at_utc/paris`, `effective_session_date`, `provisional_warning`, invariants.
  Estampillé à l'écriture du journal V27.
- **A3 signe de courbe** : `CURVE_SIGN_CONSISTENT` live (front−next, >0=BACKWARDATION identique V30/V109/V125 ;
  différence de définition du front documentée : nearby vs most-liquid).
- **A4 quality_flag** : piloté par l'OPEN INTEREST (corrige les faux `low_liquidity` quand le volume n'est
  pas publié sur un snapshot de settlement).
- **A5 sources/CI** : V134 requalifié (COMEXT→PARTIAL bulk, Previous-Runs/USDA→ACTIONABLE) ; note CI pyarrow.

## B — Red-team (FAIT)

- **B1** : narration trigger V105 corrigée — le CBOT **baisse** (−0.024) avant le début de compression, il ne
  monte pas ; champ `cbot_pre_start_direction=DOWN` ; verdict inchangé (NO_CLEAR_SINGLE_PRECURSOR), cohérent
  V106. C'était l'unique contradiction franche.
- **B2** : scan ciblé (`REDTEAM_NARRATIVE_SCAN.md`) — aucun autre écart narration/chiffres franc.

## C — Données leading (FAIT, statuts honnêtes)

- **C1** probe Euronext public : NO_PUBLIC_RANGE attendu → voies officielles (Web Services/NextHistory/CFTS).
- **C5** calendrier USDA exact (best-effort) + V137 tolérance ±1 si EXACT, sinon ±2 (précision exposée).
- **C4** forecast revision tape : Δ inter-émissions depuis le journal V127 (Previous-Runs = backfill).
- **C2** COMEXT requalifié PARTIAL (bulk existe) ; DATA_BLOCKED honnête ce run (pas de fausse série).
- **C3** tension physique UE : skeleton, détrend YoY obligatoire, WATCHLIST partiel (dépend C2).

## D — Modèles (FAIT, négatifs honnêtes)

- **D2 transitions d'état** : taxonomie (EXTREME_STATIC/EARLY_RELAXATION, STRONG_PHYSICAL_JUSTIFIED/CBOT_CATCHUP,
  WAIT_CONFIRMATION, STILL_WIDENING). **Constat** : tous les états actifs compressent à 20 j (réversion du
  niveau, EXTREME_STATIC le plus à −1.36). `STILL_WIDENING` (ex « ADVERSE_DRIFT ») renommé car il ne capte
  PAS le risque PnL (pré-pic) — risque ADVERSE réel = path-based (V82/V124).
- **D1 hazard time-to-compression** : **WATCHLIST_NO_CLEAR_EDGE** — AUC h5 0.57 / h10 0.61 / h20 0.58, près de
  la base rate. Confirme V106 : le timing est dur. Aucun edge prétendu.
- **D3 discriminant ADVERSE** (entry-time only, n=7 adverse) : meilleur séparateur précoce = **wheat_corn_z
  (AUC 0.653)** — maïs cher relatif au blé = adverse-prone ; WATCHLIST (n petit), cohérent V38.
- **D4 explication hiérarchique** : famille **MARKET** porte le signal (ΔAUC +0.118) ; SUBSTITUTION marginal
  (+0.03) ; POSITIONING/COT n'ajoute rien (−0.02). AUC complet 0.607 (faible) → EXPLANATORY_ONLY, cohérent
  V121 (exogène ajoute peu OOS).

## E — Event mode forward (FAIT, forward)

- **E1** capture du soir : `euronext_evening_snapshots` + `scripts/run_evening_event_capture.py` (créneaux
  17:55–20:15 CET, PROVISIONAL/FINAL, append-only). À lancer par cron les jours d'événements.
- **E2** microstructure : lit le journal E1, Δfront/Δspread/ΔCBOT par événement ; WATCHLIST jusqu'à
  accumulation (forward).

## Découvertes nettes de VNEXT

1. **Le CBOT ne monte pas avant la compression** (il baisse légèrement) — correction d'une fausse narration.
2. **Tous les états de prime active compressent à 20 j** (réversion du niveau) ; le risque réel est le CHEMIN.
3. **Le hazard de timing n'ajoute pas d'edge** (AUC ≈ base rate) — re-confirmé proprement.
4. **wheat_corn_z** est le meilleur flag précoce d'ADVERSE (substitution locale).
5. **La famille MARKET domine** ; positionnement COT n'ajoute rien OOS.

## Ce qui reste forward / payant

- Forward : capture du soir (E1→E2), revision tape (C4), accumulation officielle (head/V133).
- Payant/best-effort : COMEXT bulk automatisé (C2/C3), Euronext historique officiel, Previous-Runs backfill.

Tout reste **RESEARCH_ONLY_NOT_TRADING**. Aucune optimisation sur les 42 trades ; tous les négatifs écrits.
