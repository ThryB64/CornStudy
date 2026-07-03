# Étape 6 — Données manquantes pour continuer plus loin

Date : 2026-06-13. Les principales sources **publiques gratuites** ont été explorées (12 repos,
131 fiches sources, 26 expériences). Pour progresser au-delà du score de vente B, il faut des
données plus spécifiques — la plupart payantes. Classées par priorité, chacune avec : pourquoi,
quelle hypothèse elle débloque, probablement gratuite/payante, fournisseurs.

## Priorité 1 — débloquent des pistes déjà identifiées et à fort prior

| Donnée | Pourquoi utile | Hypothèse débloquée | Gratuit ? | Fournisseurs |
|---|---|---|---|---|
| **EUR/USD quotidien historique** | reconstruit le basis €/t (EXT013) et alimente l'OU (EXT012) | transmission CBOT↔EMA (VECM, V21), demi-vie basis (V10/V138) | **GRATUIT** | FRED `DEXUSEU`, ECB SDW, BIS |
| **Contrats CBOT par maturité (courbe propre)** | spreads nearby-deferred, full carry, old/new crop (EXT005), prime new-crop (EXT018) | l'info de stockage prédit-elle le retour du nearby ? | partiel (payant pour l'historique profond) | CME DataMine (payant), Barchart, Nasdaq Data Link |
| **Consensus analystes pré-WASDE** | vraie surprise = publié − attendu (EXT008) | la surprise WASDE bouge-t-elle le CBOT en quotidien ? | **payant** | Reuters/Refinitiv poll, Bloomberg, Dow Jones |
| **Options maïs : vol implicite, skew, OI** | risque ex ante supérieur aux modèles HAR/EGARCH ; gate plus fin | la vol implicite améliore-t-elle le gate de risque / le score ? | partiel | CME (settlements gratuits partiels), Barchart, ORATS, IVolatility |
| **Archive de prévisions météo forward** | seule voie météo **prédictive** (V45 : le réalisé est price-in) — EXT033 | les **révisions** de prévisions chaud/sec prédisent-elles la direction CBOT H1-H10 ? | **GRATUIT (forward)** | Open-Meteo previous-runs, GFS/ECMWF archives, CropProphet (payant) |

## Priorité 2 — enrichissent le contexte / la demande / les flux

| Donnée | Pourquoi utile | Hypothèse débloquée | Gratuit ? | Fournisseurs |
|---|---|---|---|---|
| **Prix physiques FOB / cash bids** | vraie transmission spot-futures, basis local | le basis cash prédit-il la convergence ? | partiel | DTN, USDA AMS (partiel gratuit), FranceAgriMer |
| **Prix éthanol + DDG** | vraie marge crush (EXT004) | la marge crush est-elle une variable d'état lente de la demande ? | partiel | CME (éthanol), EIA, USDA AMS (DDG) |
| **Freight / barge rates** | coût de transport → basis régional | le coût barge explique-t-il la pression basis ? | partiel | USDA AMS Grain Transportation Report (gratuit), Baltic |
| **Export flows / inspections** | demande export hebdo | les ventes export anticipent-elles la direction ? | **GRATUIT** | USDA FAS Export Sales, Grain Inspections |
| **Satellite / NDVI** | santé de culture plus précoce que Crop Condition | un proxy NDVI devance-t-il le rapport USDA ? | **GRATUIT (brut)** | NASA MODIS, Sentinel-2, USDA-NASS CDL |
| **Crop Condition plus granulaire (par État)** | pondération production fine (EXT027) | les surprises hebdo par État ajoutent-elles du signal ? | **GRATUIT** | NASS QuickStats API |
| **News professionnelles datées** | catalyseurs (V129/V143) horodatés | les catalyseurs structurent-ils les fenêtres de mouvement ? | payant | AgriCensus, World Grain, Reuters Ags |

## Priorité 3 — fournisseurs premium (couverture complète, coûteux)

| Fournisseur | Apport | Coût |
|---|---|---|
| **Bloomberg Terminal** | courbe, options, consensus, news, flux — tout en un | très élevé |
| **LSEG (Refinitiv) Eikon** | équivalent, fort sur les ags | très élevé |
| **S&P Global Platts** | prix physiques, freight, balances | élevé |
| **Fastmarkets (Agricensus)** | prix physiques ags, FOB, news | élevé |
| **AgFlow** | flux commerciaux physiques, exports | moyen-élevé |
| **Kpler** | suivi cargaisons / exports temps réel | élevé |
| **DTN complet** | cash bids, météo, prévisions agronomiques | moyen |

## Lecture
- **Quick wins gratuits** : EUR/USD (FRED) débloque basis + OU + VECM ; archive prévisions
  météo forward (Open-Meteo previous-runs) débloque la seule voie météo prédictive ; export
  flows et NASS granulaire sont gratuits. **À sourcer en priorité car gratuits et débloquants.**
- **Payant mais décisif** : consensus analystes pré-WASDE (vraie surprise) et options maïs
  (vol implicite) — sans eux, deux familles restent plafonnées.
- **Premium** : seulement si le score B est validé forward et qu'un budget data est justifié.

## Conclusion
**Les principales sources publiques gratuites ont été explorées ; pour progresser, il faut de
nouvelles données plus spécifiques, en partie gratuites (eurusd, prévisions météo forward,
exports, NASS par État) mais surtout payantes (consensus WASDE, options, courbe propre, prix
physiques).** Le prochain palier de signal viendra de ces données, pas d'un modèle plus
complexe sur les données actuelles.
