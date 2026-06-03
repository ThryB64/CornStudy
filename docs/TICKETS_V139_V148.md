# Backlog V139-V148 — faire vivre l'indicateur (forward, machine d'état)

Statut : RESEARCH_ONLY_NOT_TRADING. Baseline `basis_z` figée. **Plus de modèle sur les 42 trades.**
Priorité = accumulation forward + machine d'état + météo forecast + courbe + catalyseurs.

| # | Ticket | Objectif | Source | Leakage | Statut attendu |
|---|--------|----------|--------|---------|----------------|
| V139 | Premium state machine | cycle de vie : PRIME_EXCESSIVE/JUSTIFIED, COMPRESSION_STARTED/HEALTHY/DELAYED, ADVERSE_LIKE, TARGET_Z05/Z0 | interne (journal+V124+V109+V125) | aucun (état à t) | GO (intègre au head) |
| V140 | Weather revision engine | révisions pluie/temp US+EU J vs J-1, jours>32/35°C ; US→CBOT_SUPPORT, EU→PHYSICAL_TENSION/ADVERSE | Open-Meteo forecast | datage émission | GO (corrige UNKNOWN) |
| V141 | EMA curve forward validation | backwardation se détend avant compression ? ADVERSE gardent backwardation ? courbe→z0.5/z0 | courbe accumulée | forward | WATCHLIST (n=2) |
| V142 | MATIF forward validation | ratio officiel EBM/EMA forward | journal MATIF | forward | WATCHLIST (n=1) |
| V143 | Event catalyst enrichment | + COT_SHORT_COVERING, classes EU, fusion V129/V137 | master+COT+USDA cal | descriptif ex-post | EXPLANATORY_ONLY |
| V144 | Official proxy validation 10/40/90d | z rolling officiel quand assez de jours, vs proxy | journal officiel | forward | NOT_YET (<10j) |
| V145 | Active signal lifecycle report | rapport V124+V139 | interne | aucun | GO |
| V146 | Indicator dashboard v4 | dashboard enrichi (head+state+diagnostics+milestones) | interne | aucun | GO |
| V147 | Forward milestone report | tracker 10/40/90/180/365j | journal officiel | aucun | GO |
| V148 | Decision checkpoint 40 jours | bilan gated | journal officiel | aucun | NOT_YET (<40j) |

## Invariants
Baseline/seuils inchangés ; holdout intact ; anti-leakage ; tests+ruff+doc+artefact ; statuts honnêtes ;
forward-gated quand les données manquent. RESEARCH_ONLY_NOT_TRADING.
