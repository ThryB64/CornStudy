# Tickets recherche maïs — programme V60→V78

Tickets actionnables et reviewables. `RESEARCH_ONLY_NOT_TRADING`, baseline figée, holdout verrouillé, aucun
fit sur 42 trades. Chaque ticket : objectif · données · leakage · métriques · livrable · GO/NO_GO · dépendances.

**Légende statut** : ✅ DÉJÀ FAIT (ce tour) · 🔨 À FAIRE (faisable maintenant) · ⛔ DATA-GATED (framework +
forward) · 🔁 FORWARD (accumulation).

---

## Phase 1 — Données haute valeur

### V60-intraday — Basis CBOT aligné settlement Euronext ⛔🔨(probe)
- **Objectif** : basis = EMA(settle) − CBOT au moment du settlement Euronext (≈15h30 CET), pas CBOT close.
- **Données** : intraday CBOT (ZC=F). Gratuit seulement récent (Yahoo ~730 j en 1h). Historique 2014+ payant.
- **Leakage** : aucun (réalignement temporel, pas de futur).
- **Tests** : basis_daily vs basis_aligned — bruit de Δbasis, demi-vie (AR1), n signaux z>1, ADVERSE, compression.
- **Livrable** : `intraday_aligned_basis.py` + probe sur fenêtre récente + verdict.
- **GO/NO_GO** : ADD_TO_PIPELINE si bruit ↓ et demi-vie stable ; sinon WATCHLIST (data-gated) / NO_GO.
- **Dépendances** : —.

### V61 — MATIF blé/maïs officiel ✅ (`v52_matif_substitution.py`)
- Live OK (EBM/EMA, ratio 0.914) ; historique snapshot-only → journal forward. Verdict
  `MATIF_RATIO_LIVE_OK_HISTORICAL_WAITING_DATA`. **À rebrancher dans V64** dès couverture.

### V62 — Courbe EMA officielle / tension physique ✅ (`v54_physical_tension.py`)
- Score backwardation + front cher, live-usable ; validation historique forward (courbe ~330 j contango).

### V63 — Météo prévue extrêmes ✅ (`v51_weather_extremes.py`) + révisions 🔁
- Extrêmes faits (queue réelle mais anticipée ; persistance > intensité). **Révisions** = tracker forward
  (comparer prévision J vs J−1 pour mêmes dates valides) → 🔁 à accumuler. Journal V45 enrichi
  `forecast_consecutive_hot_days`.

---

## Phase 2 — Diagnostic du signal

### V64 — ADVERSE_RISK v2 (explained) 🔨
- **Objectif** : score ADVERSE_RISK enrichi et EXPLIQUÉ, règle-basé (AUCUN fit sur 42).
- **Entrées causales** : basis_z tier, CBOT_SUPPORT (V41), PHYSICAL_TENSION (V54), résidu substitution (V37),
  ratio blé/maïs z (V36), roll month, crise, volatilité réalisée.
- **Leakage** : composants `shift(1)` / z expandants déjà garantis dans les modules sources.
- **Sortie** : LOW/MEDIUM/HIGH + liste de raisons + objectif suggéré. Compatibilité ascendante avec V38.
- **Métriques** : séparation ADVERSE (binaire robuste), monotonie indicative, aide de l'objectif prudent en HIGH.
- **Livrable** : `v64_adverse_risk_v2.py` + test + bloc daily report + doc.
- **GO/NO_GO** : ADD_TO_DAILY_REPORT si sépare l'ADVERSE au moins aussi bien que V38 avec plus d'explication ;
  sinon WATCHLIST. **Jamais un veto.**
- **Dépendances** : V41, V54, V37.

### V65 — CBOT rebound engine 🔨
- **Objectif** : prédire la capacité de RATTRAPAGE CBOT (moteur de compression) en OOF honnête.
- **Données** : momentum 20j, position vs SMA50, RSI/oversold, drawdown réalisé, managed-money COT, vol,
  spreads inter-commo (corn/wheat, corn/soy), USD index, (éthanol margin si dispo).
- **Leakage** : features `shift(1)` ; OOF TimeSeriesSplit + embargo horizon.
- **Cibles** : CBOT rebound h10/h20/h40 (ret>0), drawdown>−3 %/−5 %.
- **Métriques** : OOF AUC vs base rate ; lift sur ADVERSE des signaux ; cohérence avec CBOT_SUPPORT règle-basé.
- **Livrable** : `v65_cbot_rebound_engine.py` + test + doc.
- **GO/NO_GO** : ADD_TO_CBOT_SUPPORT si OOF AUC ≥ 0.55 stable ; sinon NO_GO (garder CBOT_SUPPORT règle-basé).
- **Dépendances** : —.

### V66 — PHYSICAL_TENSION ✅ (`v54`) · V67 — TARGET_RECOMMENDATION ✅ (`v56`)

---

## Phase 3 — Nouvelles cibles

### V68 — Basis compression buckets ✅ (`v57_magnitude_buckets.py`)
- MFE en classes, monotone avec CBOT_SUPPORT. **Casebook pro** (V68-pro) → 🔨 `ADVERSE_CASEBOOK_PRO.md`.

### V69/V72 — Time-to-reversion (survival) 🔨
- **Objectif** : horizon probable de compression (pas seulement oui/non).
- **Données** : basis_z path post-entrée (existant).
- **Leakage** : seulement info à l'entrée pour la stratification ; l'event-time est par construction post-entrée.
- **Méthode** : Kaplan-Meier (réimplémenté sans dépendance lourde) du time-to-z0.5 / time-to-z0, censuré 90 j ;
  médiane de survie par régime CBOT_SUPPORT / ADVERSE_RISK ; taux de stop.
- **Livrable** : `v72_survival_reversion.py` + test + doc.
- **GO/NO_GO** : ADD_TO_HORIZON_ESTIMATE si les médianes diffèrent nettement par régime ; sinon WATCHLIST.
- **Dépendances** : V41, V64.

### V70 — Path classification CBOT-driven / EMA-driven / ADVERSE 🔨
- **Objectif** : par quel CANAL la compression se produit (étend `_classify_path` de V32).
- **Métriques** : répartition des canaux ; lien canal × CBOT_SUPPORT (hyp : CBOT-driven plus fréquent si support).
- **Livrable** : fonction + stats dans V70 (peut être intégrée à V65/V72 ou module court).
- **GO/NO_GO** : KEEP_AS_EXPLANATION (descriptif).

---

## Phase 4 — Fondamentaux & micro

### V71 — EU physical balance drivers ⛔
- FranceAgriMer, EC MARS, Eurostat COMEXT, Ukraine FOB, fret, TTF, stocks. Collecteurs partiels existent
  (`ec_mars`, `franceagrimer`, `eu_carbon`). **À fusionner dans le master** avant tout test → data-gated.

### V73 — Carte causale 🔨 (doc) → `CAUSAL_MAP_CORN_MARKET.md`

### V74 — Options / IV CBOT ⛔
- IV, skew, risk reversal, OI options. Source à identifier (Barchart/CME). DATA_BLOCKED pour l'instant.

---

## Phase 5 — Validation forward

### V75 — Rapport mensuel forward ✅ (`v59_monthly_forward_report.py`)
### V76 — Proxy vs officiel à 40/90 j 🔁 (s'active à l'accumulation du journal officiel)
### V77 — Synthèse indicateur ✅ partiel (`generate_daily_report` agrège la pile) → finaliser après V64
### V78 — Rapport de décision 🔁 (après ≥3–6 mois de forward) → `DECISION_REPORT_V78.md`

---

## Review des tickets (Étape 4)

| Ticket | Objectif clair | Données dispo | Leakage maîtrisé | Métriques | Livrable | GO/NO_GO | Baseline intacte |
|---|---|---|---|---|---|---|---|
| V60-intraday | ✓ | ⛔ récent only | ✓ | ✓ | ✓ | ✓ | ✓ |
| V64 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| V65 | ✓ | ✓ | ✓ (OOF+embargo) | ✓ | ✓ | ✓ | ✓ |
| V69/V72 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| V70 | ✓ | ✓ | ✓ | ✓ | ✓ | descriptif | ✓ |
| V71/V74 | ✓ | ⛔ | n/a | ✓ | framework | DATA_BLOCKED | ✓ |

**Ordre d'exécution retenu (faisable maintenant)** : V73 (carte) → V64 → V65 → V72 → V70 → V60-intraday(probe)
→ V68-pro(casebook). Le reste = forward / data-gated.

**Garde-fous transverses** : pas de fit sur 42 trades ; pas de veto ; pas de holdout ; négatifs documentés ;
chaque module `assert_no_holdout`, tests offline, ruff, entrée STATE + mémoire.
