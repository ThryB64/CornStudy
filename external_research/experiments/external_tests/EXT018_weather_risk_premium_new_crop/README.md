# EXT018 — Weather risk premium new-crop (PARTIAL_DATA)

Contrats décembre CBOT absents → approximation série continue + saisonnalité,
conditionnée stocks (WASDE) et stress météo d'été. `run_EXT018.py` produit
`weather_risk_premium_features.csv` + `premium_seasonal_descriptive.csv`.

- **Descriptif** (Janzen/Li-Hayes-Jacobs) : prime confirmée — biais baissier
  pré-récolte en année normale, rally estival en année de stress.
- **Prédictif** : REJECT (le stress n'est connu qu'en contemporain, pas ex ante).

Verdict : **PARTIAL_DATA** ; descriptif confirmé, prédictif rejeté.
