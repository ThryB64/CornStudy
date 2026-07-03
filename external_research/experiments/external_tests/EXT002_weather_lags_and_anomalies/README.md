# EXT002 — Weather lags and anomalies

Rolling 7/14/30/60/90 j de température et précipitations nationales pondérées
production, en anomalies standardisées (climatologie expandante par day-of-year),
+ stress thermique 30 j. `run_EXT002.py` produit aussi `weather_lags_features.csv`
et `weather_anomalies_features.csv`.

Anti-fuite : rolling passé uniquement, réalisé décalé J+1, climatologie années
antérieures seulement. Cible : log-retour CBOT. Verdict : **REJECT**.
