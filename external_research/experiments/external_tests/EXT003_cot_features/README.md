# EXT003 — COT features (Managed Money disaggregated)

COT CFTC corn (interne 2013-2026). Date=mardi (positions) → publication vendredi →
disponible lundi suivant (`available = Date + 6 j`). MM/PM net, z-scores, percentiles,
flux, OI, ratio spéc/comm. `run_EXT003.py` produit `cot_features.csv` +
`cot_feature_dictionary.csv`. Éval 2016+. Cible : log-retour CBOT.

Verdict : **REJECT** (dégrade RMSE et DA ; clôture honnête du dossier COT, cohérent
avec V18).
