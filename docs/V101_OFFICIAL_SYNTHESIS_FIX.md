# V101 — Fix de la source de synthèse LIVE (journal officiel forward)

Session 2026-06-02. `RESEARCH_ONLY_NOT_TRADING`, baseline figée.

## Bug
`artefacts/v99/v99_synthesis_v2_latest.json` affichait `as_of=2025-07-25 / UNCERTAIN_ROLL` (dernière date du
MASTER de features) alors que le journal officiel forward (V27) contenait déjà :
- 2026-05-29 SHORT_PREMIUM_EXTREME (basis 76.15, z 2.056)
- 2026-06-01 SHORT_PREMIUM_EXTREME (basis 75.93, z 2.039)

**Cause** : la synthèse calculait tout depuis le master, dont les features (corn/COT/météo) s'arrêtent à
2025-07-25. Le signal live était donc faux.

## Correctif
- `v101_official_synthesis_fix.py` : `run_v101_official_synthesis(df)` lit le **dernier jour du journal
  officiel** comme SIGNAL autoritatif (as_of, tier, basis officiel, basis_z, warnings) et calcule les
  diagnostics de CONTEXTE (ADVERSE_RISK, CBOT_SUPPORT v2, PHYSICAL_TENSION, objectif) à la **dernière date de
  features**, en FLAGGANT le décalage (`context_as_of`, `context_lag_days`, `data_lag_warning`).
- `synthesize_indicator_v2` (V99) : overlay automatique — si le journal officiel est plus récent que le
  master, le SIGNAL live vient de l'officiel (`live_source=official_forward_journal`), l'abstention master
  (UNCERTAIN) ne s'applique plus, un warning de retard de contexte est ajouté.
- Le bloc `official_live_report_block` est placé EN TÊTE du daily report (état live officiel prioritaire).

## Résultat (live au 2026-06-02)
```
as_of           = 2026-06-01            (au lieu de 2025-07-25)
signal_tier     = SHORT_PREMIUM_EXTREME (au lieu de UNCERTAIN_ROLL)
basis officiel  = 75.93 €/t,  basis_z = 2.039 (proxy_implied)
official warning= NON_REVERSION_RISK_HIGH (z>=2)
context_as_of   = 2025-07-25, lag 311 j  -> diagnostics indicatifs (à rafraîchir)
recommended_ctx = z->0.5
```

## Limite honnête
Le SIGNAL est juste (officiel, récent), mais les **diagnostics de contexte ont 311 j de retard** car la
chaîne de features (CBOT/COT/météo intra-master) n'est pas ré-collectée jusqu'en 2026. Tant que le master
n'est pas rafraîchi, CBOT_SUPPORT/ADVERSE_RISK/PHYSICAL_TENSION live restent **indicatifs**. La vraie levée
de cette limite = ré-collecte des features (chantier data séparé) ou accumulation forward des composants.

Tests `test_v101` (2) + `test_v99` (2) PASS. Ruff PASS.
