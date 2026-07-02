# 📊 Dashboard indicateur premium v5 — 2026-07-02
_Généré 2026-07-02 20:04:31 UTC · RESEARCH_ONLY_NOT_TRADING_

## Signal
- **SHORT_PREMIUM_MODERATE** · basis 76.99 €/t · z 1.102 (official_rolling)
- Baseline vs confirmé : **BASELINE z>1 ACTIVE · non confirmé (<1.2)** · qualité **BASELINE_SIGNAL** · score composite **1/5** (V176, qualifie sans remplacer la baseline)
- Machine d'état : **PRIME_EXCESSIVE** · nature **PRIME_EXCESSIVE** · cycle **ACTIVE_EARLY**
- Objectif **z->0.5** · horizon ~47 j

## Signal actif (V124/V179)
- Entrée 2026-07-02 (z 1.102) · 0 j · statut **ACTIVE_EARLY**
- Compression réalisée **0.0 €/t** · MFE 0.0 · MAE 0.0 · distance z→0.5 : 0.602

## Contexte marché
- Courbe EMA : NARROWING (spread front-next 1.75 €/t, BACKWARDATION)
- MATIF blé/maïs : 0.897 · substitution DATA_BLOCKED
- CBOT_SUPPORT MEDIUM · ADVERSE_RISK HIGH · PHYSICAL_TENSION MEDIUM
- Météo US HIGH · Météo EU UNKNOWN (stale)

## Officiel / proxy & jalons
- Jours officiels **25** · prochain jalon **40** (z-score officiel rolling) · z rolling officiel False
- Validation V178 (40 j) : **ACCUMULATING_25_OF_40** · paires proxy↔officiel 17
- Re-runs data-gated (V177) : {'V166_OFFICIAL': 'ACCUMULATING 25/150', 'V168_MATIF': 'ACCUMULATING 24/150', 'V155_SUMMER': 'ACCUMULATING 114/150'}

## Santé du système
- Cohérence LIVE_SIGNAL_INCONSISTENT · fraîcheur CONTEXT_COHERENT · scope_clean True
- Diagnostics bloqués : aucun
- Warnings : ["ADVERSE_RISK élevé -> risque d'écartement, ne pas renforcer"]

Source unique : data/premium/premium_daily_head.json · baseline z>1 FIGÉE. RESEARCH_ONLY_NOT_TRADING.
