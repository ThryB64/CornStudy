# 📊 Dashboard indicateur premium v5 — 2026-07-15
_Généré 2026-07-15 07:31:13 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 80.82 €/t · z 1.356 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · CONFIRMÉ z≥1.2** · qualité **CONFIRMED_SIGNAL** · score composite **2/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_EXCESSIVE** · nature **PRIME_EXCESSIVE** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-07-13 (z 1.053) · 2 j · statut **ACTIVE_EARLY**
- Compression réalisée **-1.89 €/t** · MFE 0.0 · MAE 2.25 · distance z→0.5 : 0.856

## Contexte marché
- Courbe EMA : NARROWING (spread front-next -0.5 €/t, CONTANGO)
- MATIF blé/maïs : 0.904 · substitution DATA_BLOCKED
- CBOT_SUPPORT HIGH · ADVERSE_RISK HIGH · PHYSICAL_TENSION LOW
- Météo US MEDIUM · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **34** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_34_OF_40** · paires proxy↔officiel 26
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 34/150', 'V168_MATIF': 'ACCUMULATING 33/150', 'V155_SUMMER': 'ACCUMULATING 127/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_CONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
