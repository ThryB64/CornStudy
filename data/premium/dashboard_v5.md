# 📊 Dashboard indicateur premium v5 — 2026-11-03
_Généré 2026-11-03 12:59:59 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 99.33 €/t · z 1.267 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **0/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **ADVERSE_LIKE** · nature **PRIME_EXCESSIVE** · cycle **ADVERSE_LIKE**
- Objectif **z->0.5** · horizon ~51 j

## Signal actif (V124/V179)
- Entrée 2026-10-06 (z 1.466) · 28 j · statut **ADVERSE_LIKE**
- Compression réalisée **-5.38 €/t** · MFE 0.49 · MAE 18.44 · distance z→0.5 : 0.767

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 2.75 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.891 · substitution DATA_BLOCKED
- CBOT_SUPPORT MEDIUM · ADVERSE_RISK HIGH · PHYSICAL_TENSION MEDIUM
- Météo US UNKNOWN (stale) · Météo EU LOW

## Officiel / proxy & jalons
- Jours officiels **113** · prochain jalon **180** (bilan forward) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 61
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 113/150', 'V168_MATIF': 'ACCUMULATING 112/150', 'V155_SUMMER': 'TRIGGERED 238/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer", 'santé du signal ADVERSE_LIKE (signature lente/adverse)']

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
