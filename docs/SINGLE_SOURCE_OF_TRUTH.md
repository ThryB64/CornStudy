# SINGLE SOURCE OF TRUTH — live premium EMA/CBOT

_V150/V151/V152 · 2026-06-11 · RESEARCH_ONLY_NOT_TRADING_

## La chaîne de vérité

```
journal officiel (data/forward_journal/official_forward_journal.jsonl, append-only, sessionisé V150)
   └─ vue canonique : load_forward_journal(final_only=True)   [REVISED > FINAL > PROVISIONAL]
        └─ V132 synthèse (artefacts/v132/indicator_v3_latest.json)
             └─ HEAD = data/premium/premium_daily_head.json   ← SEULE source autoritative
                  ├─ dashboard v4 (data/premium/dashboard_v4.md)      — lit le head
                  ├─ lifecycle (data/premium/lifecycle.md)            — même as_of
                  ├─ monthly (reports/monthly/latest.md, V133)        — régénéré chaque jour
                  └─ reports/daily/latest.json (bloc premium_head)    — copie embarquée du head
```

## Règles

1. **Un seul record canonique par date de marché** : la vue `final_only=True` garde le meilleur statut
   (REVISED > FINAL > PROVISIONAL). Les lignes PROVISIONAL restent dans le JSONL (audit log) mais ne sont
   jamais la vérité finale. Le run du soir (FINAL, DSP 18:30 CET) upgrade le PROVISIONAL du matin en
   ajoutant une ligne REVISED — le passé n'est jamais réécrit.
2. **Si le dernier jour est PROVISIONAL**, le head porte `session_warning` et le dashboard l'affiche.
3. **Le CI commite la vérité** : depuis V152-SYNC, le workflow `daily_market_collect.yml` commite
   `data/premium/`, `reports/monthly/` et les couches autoritatives `artefacts/v99 v101 v107 v109 v122
   v123 v124 v132 state_machine` (petits JSON). Avant, le CI régénérait ces fichiers dans son checkout
   sans les pousser → le repo servait un head du 06-02 alors que le journal était au 06-10 (constat de
   l'audit du 2026-06-10, corrigé).
4. **Audit automatique** : `mais.audit.single_source.run_single_source_audit()` tourne en fin de daily
   (étape 16) et écrit `artefacts/audit/single_source_report.json`. 7 checks : head=V132,
   head=journal, session_truth présent, dashboard lit le head, lifecycle sync, monthly sync,
   latest.json embarque le même head. Verdict courant : **PASS (7/7)**.

## Tests

- `tests/test_session_truth_v150.py` : `test_final_over_provisional_precedence`,
  `test_official_journal_has_session_fields_real`.
- `tests/test_single_source_v152.py` : `test_single_source_truth_consistency`,
  `test_dashboard_reads_head_only`, `test_monthly_reads_head_only`,
  `test_no_stale_artifact_used_in_live_report`, `test_head_exposes_session_truth`.

## Resynchronisation locale (si besoin)

Le head local peut être reconstruit offline depuis les journaux commités :
`run_v122 → run_v123_freshness → run_v132_synthesis → run_v139_state_machine → build_premium_head →
run_v145_lifecycle → run_v147_milestones → run_v146_dashboard → run_v133_monthly_v2`.
Les couches contextuelles réseau-dépendantes (v99/v101/v107) restent celles du dernier run CI commité.
