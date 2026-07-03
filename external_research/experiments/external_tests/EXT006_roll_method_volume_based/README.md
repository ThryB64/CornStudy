# EXT006 — Roll method volume-based

Hypothèse : la méthode de roll de la série continue contamine retours/momentum/basis ; une règle volume-causale (volume J-1) est plus saine (mindymallory/RollFutures, Hu et al.).

- `run_ext006.py` : V1 audit des 69 rolls EMA historiques (raw vs adjusted), V2 fenêtres de roll présumées CBOT vendeur, V3 prototype volume-causal sur le segment multi-contrats 2025+, V4 comparaisons.
- `evaluate_ext006.py` : sauts en €/t au roll, tests de Welch, flips du momentum 20j raw vs adjusted.

Anti-fuite : décision de roll sur volumes J-1 mémorisés ; roll forcé DTE≤3 (règle fixe) ; aucun paramètre optimisé ; CSV de RollFutures non utilisés.

Résultats : `external_research/results/external_tests/EXT006_roll_method_volume_based/` — **verdict IMPROVE** (artefacts EMA raw quantifiés : 10,2 €/t/roll, 6,6× ; reconstruction historique volume-based DATA_BLOCKED ; voir `README_results.md`).
