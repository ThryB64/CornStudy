# 📊 Dashboard indicateur premium v5 — 2026-07-14
_Généré 2026-07-14 07:26:50 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 80.68 €/t · z 1.401 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_EXCESSIVE** · nature **PRIME_EXCESSIVE** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-07-13 (z 1.053) · 1 j · statut **ACTIVE_EARLY**
- Compression réalisée **-1.75 €/t** · MFE 0.0 · MAE 1.75 · distance z→0.5 : 0.901

## Contexte marché
- Courbe EMA : NARROWING (spread front-next -0.5 €/t, CONTANGO)
- MATIF blé/maïs : 0.898 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION LOW
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **33** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_33_OF_40** · paires proxy↔officiel 25
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 33/150', 'V168_MATIF': 'ACCUMULATING 32/150', 'V155_SUMMER': 'ACCUMULATING 126/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
