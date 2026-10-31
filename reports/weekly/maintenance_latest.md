# 🔧 Maintenance hebdomadaire — 2026-10-31
**Verdict : OK** (0 FAIL, 0 WARN)

| Check | Statut | Détail |
|---|---|---|
| ci_daily | ✅ OK | daily 2026-10-30 result=OK |
| premium_head | ✅ OK | as_of 2026-10-30, autoritatives à jour (reporting-only en retard : ['v101', 'v99']) |
| single_source | ✅ OK | audit single_source PASS |
| official_journal | ✅ OK | 196 lignes, dernière date il y a 1 j |
| ema_curve | ✅ OK | 111 lignes, dernière date il y a 1 j |
| matif_ratio | ✅ OK | 110 lignes, dernière date il y a 1 j |
| weather_archive | ✅ OK | 63648 lignes, dernière date il y a 1 j |
| critical_tests | ✅ OK | 5 fichiers : -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html |

## Prochains jalons
- Officiel : {'n_days': 111, 'next': 180, 'meaning': 'bilan forward'}
- Data-gated (V177) : {'V166_OFFICIAL': '111/150', 'V168_MATIF': '110/150', 'V155_SUMMER': '234/150'}
- Validation proxy V178 : PROXY_RESEARCH_ONLY

RESEARCH_ONLY_NOT_TRADING.
