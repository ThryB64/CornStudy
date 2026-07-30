# 📊 Dashboard indicateur premium v5 — 2026-07-30
_Généré 2026-07-30 20:04:54 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 87.34 €/t · z 1.265 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **COMPRESSION_HEALTHY** · nature **PRIME_EXCESSIVE** · cycle **COMPRESSION_HEALTHY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-07-29 (z 1.458) · 1 j · statut **HEALTHY**
- Compression réalisée **1.07 €/t** · MFE 1.36 · MAE 0.0 · distance z→0.5 : 0.765

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 0.25 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.928 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION MEDIUM
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **45** · prochain jalon **90** (validation proxy/officiel) · z rolling officiel True
- Validation V178 (40 j) : **PROXY_RESEARCH_ONLY** · paires proxy↔officiel 37
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 45/150', 'V168_MATIF': 'ACCUMULATING 44/150', 'V155_SUMMER': 'ACCUMULATING 142/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
