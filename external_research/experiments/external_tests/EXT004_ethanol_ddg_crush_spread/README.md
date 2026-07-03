# EXT004 — Ethanol / DDG / crush spread (PARTIAL_DATA)

EIA éthanol production+stocks (hebdo, `available=Date+5j`) + ratios énergie-corn
(oil/corn, gas/corn). **Absents** : prix éthanol, DDG, soybean meal → pas de vraie
marge crush. `run_EXT004.py` produit `ethanol_ddg_features.csv`. Cible : log-retour CBOT.

Verdict : **REJECT** sur proxys ; **PARTIAL_DATA** sur la famille (sourcer prix
éthanol/DDG avant de rouvrir).
