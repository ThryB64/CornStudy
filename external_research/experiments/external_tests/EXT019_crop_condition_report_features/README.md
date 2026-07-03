# EXT019 — Crop condition report features

NASS Crop Progress/Condition hebdo (interne 1980-2026). Publication lundi 16h ET
→ disponible mardi (`available = Date + 2 j`). Niveaux, variations, anomalies par
semaine (climatologie expandante), surprise, avancement. `run_EXT019.py` produit
`crop_condition_features.csv`. Cible : log-retour CBOT.

Verdict : **IMPROVE** (gain de DA stable +4 pts à H90, RMSE neutre ; nul à court
terme). DATA_READY — pas besoin de `crop_condition_data_audit.md`.
