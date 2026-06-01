# Tickets recherche maïs — programme V82→V100

Actionnables, reviewables. `RESEARCH_ONLY_NOT_TRADING`, baseline figée, holdout verrouillé, aucun fit sur 42
trades. Statut : ✅ DÉJÀ FAIT (v1) · 🔨 NOUVEAU faisable · ⛔ DATA-GATED · 🔁 FORWARD.

## Réconciliation avec l'existant
Plusieurs tickets v2 correspondent à des modules v1 déjà livrés → on ne refait QUE s'il y a apport net :
- V89 survival ≈ **V72** ✅ · V90 magnitude ≈ **V57** ✅ · V88 tension ≈ **V54** ✅ · V93 casebook ≈ **V58** ✅
- V95 production locality ≈ **V71b** ✅ · V96 intercommodity ≈ **V80** ✅ · V98 monthly ≈ **V59** ✅
- V87 intraday ≈ **V60-intraday** ✅ (probe) · V97 proxy ≈ partiel (V27/automation)

**Réellement NOUVEAU & faisable maintenant** : V82, V86, V91, V92, V94, V99.
**Data-gated** : V83 (intra-campagne EU), V84 (MATIF historique → forward), V85 (révisions météo → forward).

---

### V82 — High-basis episode library 🔨 (Priorité 1)
- **Objectif** : transformer les 42 trades en ÉPISODES de marché complets.
- **Colonnes** : start, peak_basis_date, exit_z05, exit_z0, durée, MFE, MAE, path (V32), ratio blé/maïs (z),
  CBOT_SUPPORT (V41), ENSO (V79), production FR/UE anomalie (V71/V71b), roll, crise, raison probable.
- **Leakage** : contexte d'entrée = causal (déjà shift(1) dans les modules sources) ; MFE/MAE/durées = post-entrée par construction (descriptif).
- **Livrables** : `data/research/high_basis_episodes.parquet`, `docs/HIGH_BASIS_EPISODE_LIBRARY.md`.
- **Verdict** : `EPISODE_LIBRARY_BUILT`. Dépendances : V32/V41/V79/V71.

### V84 — MATIF wheat/corn officiel ⛔🔁
- **DÉJÀ amorcé V52** (collecteur EBM live OK, ratio 0.914, journal forward). Historique snapshot-only.
- **Verdict actuel** : `WATCHLIST_DATA_GATED` ; rebrancher dans ADVERSE_RISK/SUBSTITUTION dès couverture forward.

### V86 — CBOT_SUPPORT v2 (score économique + ENSO) 🔨
- **Objectif** : enrichir CBOT_SUPPORT règle-basé (V41) avec ENSO (V79) + corn/wheat (V80), SANS modèle opaque
  (V65 : ML rebond faible). Banding fixe, interprétable.
- **Composants** : trend (>SMA50), momentum 20j>0, COT MM net favorable (V41) + La Niña (V79) + corn/wheat bas.
- **Tests** : séparation ADVERSE & part CBOT_DRIVEN (V70) vs v1 ; ne pas DILUER (leçon V64).
- **Verdict** : `ADD_TO_DAILY_REPORT` si ≥ aussi séparant que v1 avec plus de contexte, sinon `WATCHLIST`.

### V91 — ADVERSE_RISK v3 🔨 (prudent)
- **Objectif** : v3 = v1 focalisé (3 signaux, meilleur séparateur V64) + ENSO/MATIF en EXPLICATION seulement.
- **Garde-fou** : V64 a montré qu'empiler dilue → v3 NE change PAS le tier (reste v1), ajoute des raisons.
- **Verdict** : `EXPLANATION_LAYER_ONLY` (déjà couvert par V64) → probable `KEEP_V1` sauf apport net forward.

### V92 — Target recommendation v3 🔨
- **Objectif** : étendre V56 avec survival (V72) — objectif différencié selon horizon probable + météo EU stress.
- **Tests** : PnL, profit/jour, exposition, MAE, taux d'atteinte ; vs V56.
- **Verdict** : `ADD_TO_INDICATOR` si Pareto-améliore V56, sinon `KEEP_V56`.

### V94 — ENSO → CBOT_SUPPORT 🔨
- **Objectif** : intégrer le régime ENSO comme CONTEXTE macro-climatique de CBOT_SUPPORT (pas un veto).
- **Tests** : ADVERSE / CBOT_DRIVEN par régime sur les épisodes (V82) ; robustesse ex-crise.
- **Caveat** : ~12 épisodes → underpowered au niveau trades ; rester descriptif. `WATCHLIST` probable.

### V99 — Indicator synthesis v2 🔨
- **Objectif** : étendre V77 avec ENSO_CONTEXT + SUBSTITUTION_WARNING + WEATHER_WARNING.
- **Verdict** : `SYNTHESIS_V2_BUILT`, branché daily report.

### V83 / V85 / V87 / V88 / V97 / V100
- V83 EU intra-campagne ⛔ (MARS/COMEXT bloqués, cf. V80) · V85 révisions météo 🔁 (journal V45 enrichi
  persistance) · V87 intraday ✅ probe (V60) · V88 courbe ✅ (V54, forward) · V97 proxy 🔁 · V100 décision 🔁
  (après forward).

---

## Review des tickets
| Ticket | Objectif | Données | Leakage | Métriques | Livrable | GO/NO_GO | Baseline |
|---|---|---|---|---|---|---|---|
| V82 | ✓ | ✓ (tout dispo) | ✓ | ✓ | parquet+doc | ✓ | intacte |
| V86 | ✓ | ✓ | ✓ | ✓ | module+test | ✓ | intacte |
| V91 | ✓ | ✓ | ✓ | ✓ | (≈V64) | KEEP_V1 probable | intacte |
| V92 | ✓ | ✓ | ✓ | ✓ | module+test | ✓ | intacte |
| V94 | ✓ | ✓ | ✓ (ENSO −2m) | ✓ | (dans V82/V86) | WATCHLIST | intacte |
| V99 | ✓ | ✓ | ✓ | ✓ | module+test | ✓ | intacte |
| V83/V84/V85 | ✓ | ⛔/🔁 | n/a | ✓ | forward | DATA_GATED | intacte |

**Ordre d'exécution retenu** : V82 → V86 → V99 (les 3 à vrai apport) ; V92 si Pareto-améliore V56 ; V91/V94
= explication/contexte (pas de nouveau tier) ; reste data-gated/forward.

**Garde-fous** : pas de fit, pas de veto, pas de holdout, pas de dilution de score, négatifs documentés,
chaque module `assert_no_holdout` + tests offline + ruff + entrée STATE/mémoire.
