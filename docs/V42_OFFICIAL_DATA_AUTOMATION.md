# V42 — Official Data Automation & Backfill

Session 2026-06-01. On industrialise la collecte officielle Euronext EMA : calendrier de marché, table de
sessions append-only, automatisation serveur, évaluation du backfill public, comparaison proxy/officiel.
**Aucune modification de la baseline short basis-haut.** `RESEARCH_ONLY_NOT_TRADING`. Holdout verrouillé.

> **Nommage** : la phase recherche `V41` du dépôt = CBOT_SUPPORT. Cette phase d'INFRASTRUCTURE est nommée
> `V42` pour ne pas écraser ce module. Elle réalise les tickets « V41 Official Data Automation » demandés.

## Pourquoi 29 mai et 1er juin, mais pas 30/31 ?
Parce que **30 mai = samedi, 31 mai = dimanche** : pas de settlement Euronext. Ce n'est pas une panne.
Le système ne doit pas inventer de prix ni paniquer — il marque `NO_SESSION_WEEKEND`.

## V42-01 — Calendrier de marché (`src/mais/calendar/market_calendar.py`)
`is_trading_day`, `is_weekend`, `is_euronext_holiday`, `classify_session`, `previous/next_trading_day`,
`expected_settlement_date`, `sessions_between`. Jours fériés Euronext Paris (calcul de Pâques) : 1 jan,
Vendredi saint, Lundi de Pâques, 1 mai, 25 déc, 26 déc. Vérifié 2026 (Pâques 5 avr → Vendredi saint 3 avr,
Lundi de Pâques 6 avr ; 14 juillet = ouvert). Tests `tests/test_market_calendar.py` (5 PASS).

**Intégration fraîcheur** (`data_freshness.py`) : la staleness est désormais en **jours de MARCHÉ**
(week-ends ET fériés exclus) ; un bloc `calendar` explicite la session du jour, le dernier settlement
attendu, les jours NO_SESSION écoulés et `missing_explained_by_calendar`. Résultat : un dimanche après un
vendredi coté → `staleness 0`, `OK`, week-end expliqué (plus de fausse alerte stale).

## V42-04 — Table de sessions append-only (option B)
`update_market_sessions` écrit `data/official_forward/market_sessions.{parquet,csv}` : une ligne par jour
calendaire avec `session` (TRADING_SESSION / NO_SESSION_WEEKEND / NO_SESSION_HOLIDAY) et `trading_session`.
Append-only (dédup par date, keep last). On voit clairement que les jours manquants sont normaux.
**Les prix ne sont jamais créés le week-end** ; seule la table calendrier porte les NO_SESSION.

## V42-02 — Backfill public Euronext (`assess_public_backfill_coverage`)
Constat vérifié en live : l'endpoint public `live.euronext.com EMA/DPAR` renvoie le **SNAPSHOT du jour**
(contrats actifs + settlement/OI/volume), **pas d'historique profond ni de contrats expirés**.
→ verdict `PUBLIC_BACKFILL_TOO_LIMITED_SNAPSHOT_ONLY`. Stratégie data documentée :
- **Niveau 1 public** : snapshot quotidien → on accumule en forward (append-only).
- **Niveau 2 Web Services** : demande officielle Euronext (REST/JSON historical, settlement/OHLC/OI,
  contrats expirés depuis 2014).
- **Niveau 3 vendors** : Bloomberg `EPA<COMDTY>CT`, LSEG/Refinitiv `0#EMA:`, CQG `PZ`, TT `yEMA`, Barchart.

Store officiel accumulé : **2 jours** (2026-05-29, 2026-06-01), 10 contrats EMA H/M/Q/X 2026-2028.

## V42-03 — Automatisation serveur
- `scripts/run_daily_collect.py` : calendar-aware (NO_SESSION → `SKIPPED_NO_SESSION`, jamais une panne) ;
  collecte snapshot officiel + journal forward V27 + automation V42 ; `--retry` pour le settlement tardif ;
  écrit `reports/daily/{date}.json` et `latest.json`. Code retour non bloquant sur source secondaire.
- `.github/workflows/daily_market_collect.yml` : deux passages (20h30 Paris principal, 07h30 rattrapage),
  `workflow_dispatch`, commit append-only + upload artefacts.

## V42-05 — Comparaison proxy vs officiel (`proxy_vs_official_tracking`)
Pour chaque jour du journal officiel : `basis_official`, `basis_z_official_used`, `basis_proxy`,
`basis_z_proxy`, `spread_official_minus_proxy`, `signal_agreement`. Jalons : 10 j (1re compa), 40 j
(sérieuse), 90 j (conclusion). Actuellement 2 jours → `TOO_SHORT_KEEP_ACCUMULATING`.

## V42-06 — Monitoring calendar-aware
`run_v42_automation` : un jour NO_SESSION → `monitoring_status = OK_NO_SESSION` (pas FAIL). Un jour de
marché → `TRADING_DAY_COLLECT_EXPECTED`. Cohérent avec V22 (`daily_status` PASS_WITH_WARNINGS si seules
les sources secondaires échouent).

## Synthèse
- Le projet passe d'une étude locale à un **système de données officiel forward**.
- Week-end/férié = NO_SESSION explicite, plus jamais une fausse panne.
- Backfill public = snapshot-only (honnête) → l'historique long passe par Web Services/vendor.
- Append-only partout (journal V27 + table sessions) ; baseline intacte.
- Tests : `test_market_calendar` (5) + `test_official_automation` (3) PASS. Artefacts `artefacts/v42/`,
  données `data/official_forward/`.
