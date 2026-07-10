# 📊 Dashboard indicateur premium v5 — 2026-07-10
_Généré 2026-07-10 20:02:04 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 80.08 €/t · z 1.346 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_EXCESSIVE** · nature **PRIME_EXCESSIVE** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-07-10 (z 1.346) · 0 j · statut **ACTIVE_EARLY**
- Compression réalisée **0.0 €/t** · MFE 0.0 · MAE 0.0 · distance z→0.5 : 0.846

## Contexte marché
- Courbe EMA : NARROWING (spread front-next -0.5 €/t, CONTANGO)
- MATIF blé/maïs : 0.882 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION LOW
- Météo US HIGH · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **31** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_31_OF_40** · paires proxy↔officiel 23
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 31/150', 'V168_MATIF': 'ACCUMULATING 30/150', 'V155_SUMMER': 'ACCUMULATING 122/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_INCONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
