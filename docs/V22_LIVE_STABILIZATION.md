# V22 — Stabilisation live : pipeline robuste + gate de fraîcheur

**Date** : 2026-05-31 · **Statut** : `RESEARCH_ONLY_NOT_TRADING`
**Modules** : `src/mais/ops/daily.py` (classification), `src/mais/research/data_freshness.py` (gate),
`src/mais/research/v21_indicator_integration.py` + `v17_research_indicator.py` (intégration du gate),
`src/mais/collect/euronext_contracts_daily.py` (collecteur défensif). Tests : `test_v22_live_stabilization.py` (5 PASS).

Réponse aux deux blocages live identifiés : (1) le pipeline quotidien finissait en **FAIL** dès qu'une
source secondaire échouait ; (2) le rapport affichait un signal **périmé** (2025-07-25) sans le signaler.

---

## V22-01 — Pipeline quotidien : essentiel vs secondaire

Avant : `_collect` levait `RuntimeError` dès qu'**une** source commençait par `FAIL` → `overall_status=FAIL`
même quand seules des sources secondaires (ice_dxy, enso_oni timeout, euronext_ema_daily, fred STUB...)
échouaient.

Après :
- `ESSENTIAL_COLLECTORS = ("cbot_corn",)` — seul l'échec du **prix CBOT cœur** (qui alimente
  `build_features()`) bloque le pipeline.
- Les échecs **secondaires** sont collectés dans `collection_warnings` (non bloquants).
- Nouveau statut **`PASS_WITH_WARNINGS`** quand toutes les étapes passent mais des sources secondaires ont
  échoué.
- `euronext_contracts_daily.download` : si la source renvoie une liste vide (`[]`), lève désormais
  `NotImplementedError` → classé **STUB** (propre) au lieu d'un `FAIL` cryptique
  (`Invalid value '[]' for dtype float64`).

Résultat attendu : avec uniquement ice_dxy / enso_oni / euronext_ema_daily / fred / wasde en échec ou stub,
le pipeline finit en **`PASS_WITH_WARNINGS`**, plus en `FAIL`.

## V22-02 — Gate de fraîcheur (le correctif central)

`src/mais/research/data_freshness.py` calcule, par source clé (CBOT, EMA, FX, basis), la dernière date
disponible et le **retard en jours ouvrés** vs aujourd'hui :

| Retard | Verdict | Effet |
|---|---|---|
| ≤ 2 j | `OK` | signal autorisé |
| 3-5 j | `WARNING_STALE` | signal autorisé, prudence |
| > 5 j | `NO_SIGNAL_STALE` | **signal refusé → `UNCERTAIN_DATA_STALE`** |

Intégré dans :
- `run_integrated_indicator` (V21) : le snapshot live est **gaté** ; on conserve `raw_signal_before_gate`.
- `generate_daily_report` (V17) : le rapport affiche dernière donnée, date de génération, retard, verdict.

**Effet réel mesuré** : les données s'arrêtent au **2025-07-25** ; généré le 2026-05-31 → **retard 221 jours
ouvrés** → `NO_SIGNAL_STALE` → le signal live (qui aurait été `UNCERTAIN_ROLL` brut) devient honnêtement
**`UNCERTAIN_DATA_STALE`**. Le système **refuse de signaler sur données périmées** (correctif demandé).

Extrait du rapport corrigé :
```
# Rapport maïs EMA/CBOT — dernière donnée 2025-07-25 (généré pour 2026-05-31)
**Fraîcheur** : NO_SIGNAL_STALE | retard 221 j ouvrés (dernier basis 2025-07-25, ...)
5. **Signal premium : UNCERTAIN_DATA_STALE** (brut UNCERTAIN_ROLL — GATÉ : données périmées)
```

## V22-03/04/05 — Journal, monitoring (état)

- **Journal forward** (`run_premium_journal`, V14) : opérationnel, append-only. À brancher en cron une fois
  les données live fraîches (sinon il enregistrerait des signaux périmés — à gater de même en usage live).
- **Monitoring collecteurs** : `collection_warnings` dans `daily_status.json` liste les sources secondaires
  en échec (visibilité sans blocage).

## Ce qui reste WAITING_DATA (réseau / sources externes)

- Données live fraîches (CBOT/EMA/FX à jour) — nécessite l'exécution réseau du pipeline ou un flux officiel.
- **Source EMA officielle** (Euronext NextHistory / Refinitiv / Bloomberg / Barchart) — déblocage n°1.
- **Archive météo prévue** (Open-Meteo Historical Forecast / GFS) — collecteur prêt (V19).

---

## Synthèse V22

| Problème | Avant | Après |
|---|---|---|
| Pipeline daily | `FAIL` sur source secondaire | `PASS_WITH_WARNINGS` (seul cbot_corn bloque) |
| euronext_ema_daily vide | `FAIL` cryptique | `STUB` propre (non bloquant) |
| Rapport périmé | signal affiché comme actif | **`UNCERTAIN_DATA_STALE`** + retard affiché |
| Honnêteté live | absente | gate de fraîcheur (≤2 OK / 3-5 WARN / >5 NO_SIGNAL) |

La règle basis et la recherche restent **inchangées**. V22 rend le **live honnête** : le système ne
prétend plus produire un signal exploitable sur des données vieilles de 221 jours.

*V22 — 2026-05-31. Pipeline non bloquant sur secondaires, gate de fraîcheur opérationnel. Research-only.*
