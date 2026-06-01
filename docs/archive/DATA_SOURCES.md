# Sources de données — Étude du maïs

## Principe d'organisation

Chaque source est documentée avec :
- **Portail officiel** de téléchargement
- **Fréquence** de publication
- **Lag** de disponibilité après la période couverte
- **Collecteur** dans le code
- **Statut** dans le pipeline actuel
- **Variables clés** à extraire

---

## Bloc 1 — Prix et marché CBOT

**Fréquence :** quotidienne
**Lag :** 0 jour
**Collecteur :** `yfinance_collector.py`
**Statut :** ✅ actif

**Variables à collecter :**

| Variable | Symbole YFinance | Signification |
|---|---|---|
| Prix close front-month | `ZC=F` | Prix settlement journalier |
| Volume | inclus | Activité du marché |
| Open Interest | externe | Participation totale |
| Spread front-second | manuel | Contango/backwardation |
| Soja front-month | `ZS=F` | Pour ratio corn/soy |
| Blé front-month | `ZW=F` | Pour ratio corn/wheat |
| Pétrole (WTI) | `CL=F` | Pour ratio corn/oil |
| Dollar Index (DXY) | `DX-Y.NYB` | Compétitivité export |
| Ethanol (proxy) | `UNL` | Si direct non dispo |

**Dérivées calculées dans features/market.py :**
- `corn_return_1d`, `corn_return_5d`, `corn_return_20d`
- `corn_vol_20d`, `corn_vol_60d` (réalisée)
- `corn_soy_ratio`, `corn_wheat_ratio`
- `corn_dist_to_52w_high`, `corn_dist_to_52w_low`
- Indicateurs techniques (RSI, ATR, Bollinger)

---

## Bloc 2 — Météo Corn Belt

**Fréquence :** quotidienne
**Lag :** 0 jour
**Collecteur :** `openmeteo_collector.py`
**Statut :** ✅ actif

**États couverts avec pondération production :**

| État | Poids approximatif |
|---|---|
| Iowa | 18% |
| Illinois | 15% |
| Nebraska | 12% |
| Minnesota | 10% |
| Indiana | 8% |
| Kansas | 6% |
| South Dakota | 5% |
| Ohio | 5% |
| Missouri | 5% |
| Wisconsin | 4% |
| Autres | 12% |

**Variables par station/état :**

| Variable | Signification |
|---|---|
| `tavg` | Température moyenne |
| `tmax`, `tmin` | Extremes thermiques |
| `prcp` | Précipitations |
| `wind` | Vent moyen |
| `humidity` | Humidité relative |

**Dérivées calculées dans features/weather_belt.py :**
- `belt_tavg_anom` : anomalie vs normale saisonnière pondérée
- `belt_prcp_anom` : anomalie précipitations pondérée
- `belt_heat_days_10d` : jours > 32°C dans les 10 derniers jours
- `belt_frost_days_14d` : jours < 2°C dans les 14 derniers jours
- `belt_gdd_cum` : Degrés-jours de croissance cumulés

**Manquant :**
- GDD (Growing Degree Days) calculé proprement
- Stress hydrique (SMAP, Drought Monitor)
- NDVI (NASA satellite)

---

## Bloc 3 — WASDE / USDA

**Fréquence :** mensuelle (1 rapport/mois)
**Lag :** 0 jour après publication
**Portail :** USDA ERS WASDE Report
**Collecteur :** `usda_wasde_collector.py`
**Statut :** ✅ actif

**Variables US à collecter :**

| Variable | Signification |
|---|---|
| `yield_bu_acre` | Rendement US |
| `area_harvested_mbu` | Superficie récoltée |
| `production_mbu` | Production totale US |
| `beginning_stocks_mbu` | Stocks début de campagne |
| `ending_stocks_mbu` | Stocks fin de campagne |
| `feed_use_mbu` | Consommation animale |
| `ethanol_use_mbu` | Consommation éthanol |
| `exports_mbu` | Exports |
| `total_use_mbu` | Demande totale |
| `stu` | Stocks-to-use ratio (calculé) |
| `avg_farm_price` | Prix ferme USDA |

**Variables monde à ajouter :**

| Variable | Source | Statut |
|---|---|---|
| World production | PSD Online | ❌ |
| World ending stocks | PSD Online | ❌ |
| Brazil production | CONAB/PSD | ❌ |
| Argentina production | Bolsa Cereales | ❌ |
| Ukraine exports | FAO/PSD | ❌ |
| China imports | PSD Online | ❌ |

**Règle anti-leakage :**
Données WASDE = publiées mensuellement → `shift(1)` + forward-fill sur les dates de marché.

---

## Bloc 4 — NASS QuickStats

**Fréquence :** annuelle / trimestrielle
**Lag :** variable selon rapport
**Portail :** NASS QuickStats
**Collecteur :** `nass_quickstats_collector.py`
**Statut :** ✅ actif

**Rapports principaux :**

| Rapport | Fréquence | Variables clés |
|---|---|---|
| Prospective Plantings | Mars | Area planted intention |
| Grain Stocks | Trimestriel | On-farm + off-farm stocks |
| Acreage | Juin | Final planted area |
| Small Grains Summary | Annuel | Yield, production |
| Production | Août-nov | Yield final |

---

## Bloc 5 — Crop Progress / Crop Condition

**Fréquence :** hebdomadaire (lundi, pendant saison)
**Lag :** 1 jour
**Portail :** NASS Weekly Crop Progress
**Collecteur :** ⚠️ partiel (dans nass_quickstats_collector.py)
**Statut :** ⚠️ pas dans features.parquet

**Variables à collecter :**

| Variable | Signification |
|---|---|
| `planted_pct` | % superficie plantée |
| `emerged_pct` | % émergé |
| `silking_pct` | % en floraison |
| `dough_pct` | % en stade pâteux |
| `dented_pct` | % denté |
| `mature_pct` | % mûr |
| `harvested_pct` | % récolté |
| `condition_gd_ex_pct` | % good/excellent |
| `condition_poor_vp_pct` | % poor/very poor |
| `progress_gap_5y` | Écart vs moyenne 5 ans |

**Règle :** ces données sont hebdomadaires et ne couvrent que la saison (avril-novembre). En hiver, forward-fill.

---

## Bloc 6 — Drought Monitor

**Fréquence :** hebdomadaire (jeudi)
**Lag :** 1 jour
**Portail :** droughtmonitor.unl.edu
**Collecteur :** `drought_monitor_collector.py`
**Statut :** ⚠️ collecteur présent, pas dans features

**Variables :**

| Variable | Signification |
|---|---|
| `corn_area_d0_pct` | % maïs en D0 (anormalement sec) |
| `corn_area_d1_pct` | % maïs en D1 (sécheresse modérée) |
| `corn_area_d2_pct` | % maïs en D2 (sécheresse sévère) |
| `corn_area_d3_pct` | % maïs en D3 (extrême) |
| `corn_area_d4_pct` | % maïs en D4 (catastrophique) |
| `drought_composite` | Score synthétique (D0×0.1 + D1×0.3 + D2×0.5 + D3×0.75 + D4×1.0) |

---

## Bloc 7 — EIA Éthanol

**Fréquence :** hebdomadaire (mercredi)
**Lag :** 6 jours
**Portail :** EIA API v2
**Collecteur :** `eia_ethanol_collector.py`
**Statut :** ⚠️ nécessite clé API réelle — proxy corn/oil actif

**Variables idéales :**

| Variable | Series EIA | Signification |
|---|---|---|
| `ethanol_production_kbd` | WGFRPUS2 | Production hebdo (kbbl/jour) |
| `ethanol_stocks_kbbl` | WGTSTUS1 | Stocks totaux (kbbl) |
| `ethanol_demand_implied` | calculé | Production - export + import |
| `ethanol_stocks_days` | calculé | Stocks / demande journalière |

**Proxy actuel :**
```python
ethanol_proxy_crush_margin = oil_price / corn_price
```

**Action requise :** obtenir une clé `EIA_API_KEY` gratuite sur eia.gov/opendata.

---

## Bloc 8 — Exportations (FAS)

**Fréquence :** hebdomadaire (jeudi)
**Lag :** 1 jour
**Portail :** USDA FAS Export Sales Reporting
**Collecteur :** `fas_export_sales_collector.py`
**Statut :** ⚠️ collecteur présent, pas intégré dans features

**Variables :**

| Variable | Signification |
|---|---|
| `export_sales_mt` | Ventes nettes de la semaine |
| `export_shipments_mt` | Shipments exportés |
| `outstanding_sales_mt` | Carnet de commandes |
| `china_sales_mt` | Achats Chine de la semaine |
| `mexico_sales_mt` | Achats Mexique |
| `sales_vs_5y_avg_z` | Surprise vs moyenne 5 ans |

---

## Bloc 9 — Macroéconomie (FRED)

**Fréquence :** mensuelle (certaines quotidiennes)
**Lag :** 1 jour
**Portail :** FRED API (St. Louis Fed)
**Collecteur :** `fred_collector.py`
**Statut :** ✅ actif

**Variables actuelles :**

| Variable FRED | Signification |
|---|---|
| `FEDFUNDS` | Taux directeur Fed |
| `CPIAUCNS` | Inflation US (CPI) |
| `DGS10` | Taux 10 ans |
| `DTWEXBGS` | Dollar trade-weighted |

**Variables à ajouter :**

| Variable | Signification |
|---|---|
| USD/BRL | Compétitivité Brésil |
| USD/ARS | Compétitivité Argentine |
| Natural gas price | Coût engrais azotés |
| Diesel price | Coût transport/récolte |

---

## Bloc 10 — CFTC COT

**Fréquence :** hebdomadaire (mardi → publié vendredi)
**Lag :** 3 jours
**Portail :** CFTC Disaggregated Reports
**Collecteur :** `cftc_cot_collector.py`
**Statut :** ✅ actif (695 lignes depuis 2013)

**Variables :**

| Variable | Signification |
|---|---|
| `cot_mm_long`, `cot_mm_short` | Managed Money (fonds) |
| `cot_mm_net` | Position nette fonds |
| `cot_pm_long`, `cot_pm_short` | Producer/Merchant |
| `cot_pm_net` | Position nette commerciaux |
| `cot_open_interest` | Open Interest total |
| `cot_mm_net_pct_oi` | Position nette fonds / OI |
| `cot_mm_net_z52` | Z-score 52 semaines de mm_net |

---

## Règles anti-leakage par fréquence

| Fréquence source | Traitement obligatoire |
|---|---|
| Quotidienne | `shift(1)` si besoin |
| Hebdomadaire | `ffill()` + `shift(1)` sur dates marché |
| Mensuelle | `ffill()` + `shift(1)` sur dates marché |
| Annuelle | `ffill()` + `shift(1)` sur dates marché |

**Règle absolue :** aucune donnée future ne peut entrer dans les features de la date t.

---

## Priorité d'ajout des données manquantes

| Source | Priorité | Impact attendu |
|---|---|---|
| Crop Progress / Crop Condition | Haute | Facteur clé J+10/J+20 saison |
| Drought Monitor | Haute | Stress hydrique direct |
| EIA éthanol (vraie clé API) | Haute | Demande intérieure |
| FAS exports | Moyenne | Compétitivité export |
| Prix monde (Brésil, Argentine) | Moyenne | Offre mondiale |
| Basis locale | Moyenne | Décision agriculteur réelle |
| NDVI (NASA) | Faible | Redondant avec Drought |
