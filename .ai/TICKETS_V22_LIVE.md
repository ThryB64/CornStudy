# Tickets — V22 Stabilisation live

Demande utilisateur : corriger le live (pipeline FAIL, rapport périmé) sans toucher la règle de base.
Doc : `docs/V22_LIVE_STABILIZATION.md`.

## Exécuté

- **V22-01** — `DONE` — Pipeline daily non bloquant sur sources secondaires. `ESSENTIAL_COLLECTORS=(cbot_corn,)`,
  échecs secondaires → `collection_warnings`, nouveau statut `PASS_WITH_WARNINGS`. `euronext_ema_daily` vide
  → `STUB` propre (fix du `Invalid value '[]'`). Fichiers : `src/mais/ops/daily.py`,
  `src/mais/collect/euronext_contracts_daily.py`.
- **V22-02** — `DONE` — Gate de fraîcheur. `src/mais/research/data_freshness.py` (compute_freshness +
  staleness_verdict ≤2 OK / 3-5 WARNING / >5 NO_SIGNAL). Intégré dans l'indicateur V21 et le rapport V17 :
  signal live `UNCERTAIN_DATA_STALE` si périmé. Réel : retard 221 j → signal gaté. Tests
  `tests/test_v22_live_stabilization.py` (5 PASS).
- **V22-05** — `DONE` (partiel) — Monitoring : `collection_warnings` dans `daily_status.json`.

## WAITING_DATA / réseau

- **V22-01b** — exécuter le pipeline live (réseau) pour confirmer `PASS_WITH_WARNINGS` réel + fraîcheur OK.
- **V22-03** — journal forward append-only en cron (gater aussi en usage live si données périmées).
- **V22-04** — rapport hebdomadaire automatique.
- **V22-06** — collecte archive météo prévue (collecteur prêt V19).
- **V22-09** — source EMA officielle (déblocage n°1).

## Discipline

Règle basis inchangée (short basis-haut, sortie z→0/0.5, stop −20, warnings). V22 ne change que la
**robustesse** et l'**honnêteté live**, pas le signal.
