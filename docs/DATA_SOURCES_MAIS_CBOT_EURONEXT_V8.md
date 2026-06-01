# SOURCES DE DONNÉES — MAIS CBOT + EURONEXT EMA — V8

**Date** : 2026-05-30.
**Statut** : recherche documentaire, non utilisé en production.
**Légende statut intégration projet** :
- `INTÉGRÉ` : déjà collecté dans le pipeline `mais`
- `MANQUANT` : pas dans le pipeline
- `PROXY` : version proxy uniquement (ex : barchart pour EMA)
- `PARTIEL` : intégré mais incomplet ou avec gap.

Chaque source est notée sur 5 dimensions :
- **Fréquence** : intraday / quotidien / hebdo / mensuel / trimestriel / annuel
- **Historique** : profondeur récupérable
- **Accès** : API / scraping / manuel / abonnement
- **Coût** : gratuit / abonnement / institutionnel
- **Publication lag** : décalage entre fait économique et publication (CRITIQUE pour anti-leakage).

---

## 1. FUTURES — CBOT (USDA)

### 1.1 CME / CBOT Corn Futures (ZC)
- **Variable** : prix settlement, OHLCV, OI par contrat (H, K, N, U, Z).
- **Source officielle** : CME Group (cmegroup.com).
- **Fréquence** : intraday + EOD settlement.
- **Historique** : 30+ ans accessibles via CME Datamine.
- **Accès** : CME Datamine (abonnement institutionnel), Bloomberg (BBG), Refinitiv Eikon, Nasdaq Data Link, Quandl historical, Barchart OnDemand.
- **Coût** : gratuit via yfinance (EOD lag jours), abonnement pour EOD officiel.
- **Publication lag** : nul (en intraday) / jour ouvré suivant pour settlement officiel.
- **Lien CBOT** : direct (c'est CBOT lui-même).
- **Lien EMA** : moteur principal du basis ; `cbot_eur_t = cbot_close × 36.744 / eurusd` déjà dans pipeline.
- **Variables à construire** : returns 1/5/20/60d, vol réalisée, contango/backwardation, term structure slope.
- **Statut projet** : `INTÉGRÉ` (via yfinance + features pipeline).
- **Risque leakage** : faible — settlement quotidien public.

[CME Corn Futures](https://www.cmegroup.com/markets/agriculture/grains/corn.html)

---

## 2. FUTURES — EURONEXT MATIF (EMA)

### 2.1 Euronext Corn Futures (EMA, code DPAR)
- **Variable** : settlement, OHLCV, OI par contrat (H/M/Q/X + legacy F).
- **Source officielle** : Euronext NextHistory (`euronext.com/data/historical-data`).
- **Fréquence** : intraday + EOD settlement (méthodologie : 5 minutes précédant 18:30 CET).
- **Historique** : produits actifs uniquement via API publique ; complet historique via abonnement NextHistory.
- **Accès** :
  - **Officiel** : Euronext Web Services API + NextHistory EOD (abonnement).
  - **Proxy actuel** : Barchart OnDemand `XB*` (utilisé en `barchart_proxy_exploratory`).
  - **Alternatives commerciales** : Refinitiv LSEG Eikon, Bloomberg EMA Comdty, Nasdaq Data Link, ICE Data Services, CQG, Roper Technologies.
- **Coût** : ~500–3000 €/an selon profondeur (NextHistory), 0 € via Barchart EOD avec rate limit.
- **Publication lag** : jour ouvré suivant pour settlement officiel.
- **Lien CBOT** : basis EMA - CBOT_EUR.
- **Lien EMA** : direct.
- **Variables à construire** : front_adjusted, basis, basis_z, curve slope, OI ratio front/next.
- **Statut projet** : `PROXY` — `barchart_proxy_exploratory`. Validation `VAL-EMA-01` : MAE 37 €/t vs proxy CBOT→EUR, verdict `PROXY_FORBIDDEN` en benchmark décisionnel. Tolerable en research-only, NON pour indicateur ou bot.
- **Risque leakage** : faible (EOD), MAIS le proxy actuel ne reflète pas le settlement officiel — un signal apparent peut être un artefact du proxy.
- **Priorité V8** : `V7-01B` HAUTE — acquisition officielle + delta proxy/officiel < 0.05 AUC obligatoire avant tout claim indicateur.

[Euronext Commodities](https://live.euronext.com/en/products/commodities), [Corn EMA-DPAR](https://live.euronext.com/en/product/commodities-futures/EMA-DPAR), [NextHistory](https://www.euronext.com/en/data/historical-data), [Daily Settlement Methodology](https://live.euronext.com/en/products/commodities/dsp), [Euronext Web Services](https://www.euronext.com/en/data/how-access-market-data/web-services)

---

## 3. BILANS FONDAMENTAUX MONDIAUX

### 3.1 USDA WASDE
- **Variable** : balance maïs mondiale, ending_stocks, use, production par pays, S&D.
- **Source** : USDA Office of Chief Economist.
- **Fréquence** : mensuelle (12/an, calendrier fixé d'avance).
- **Historique** : depuis 1973.
- **Accès** : PDF + CSV téléchargeable jour J+1 sur usda.gov.
- **Coût** : gratuit.
- **Publication lag** : 0–1 jour après publication officielle.
- **Calendrier 2026** : 12 jan, 10 fév, 10 mar, 9 avr, 12 mai, 11 juin, 10 juil, 12 août, 11 sep, 9 oct, 10 nov, 10 déc.
- **Variables à construire** : WASDE surprise vs consensus (Reuters/Bloomberg), z-scores expanding, drift_mensuel.
- **Statut projet** : `INTÉGRÉ` partiellement (132 colonnes WASDE — voir STATE).
- **Risque leakage** : modéré — la valeur au mois M doit être propagée avec `shift(1)` après date publication, pas date du mois nominal.

[WASDE Report](https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report), [ERS Developer / API](https://www.ers.usda.gov/developer)

### 3.2 USDA NASS Crop Progress / Crop Condition
- **Variable** : avancement semis/floraison/récolte/condition maïs US par état.
- **Fréquence** : hebdomadaire, lundi 15:00 CST (avril–novembre, saisonnier).
- **Historique** : depuis 1980+.
- **Accès** : QuickStats API (clé gratuite).
- **Coût** : gratuit.
- **Publication lag** : ~1 jour ouvré.
- **Variables à construire** : pct_good_excellent_z, semis_avance_vs_moyenne, harvest_avance_vs_moyenne.
- **Statut projet** : `INTÉGRÉ` (2568 lignes non-null, saisonnier mai-oct).
- **Risque leakage** : nul si date publication respectée.

[NASS QuickStats](https://www.nass.usda.gov/Quick_Stats/), [Developers](https://www.nass.usda.gov/developer/index.php), [Crop Progress Charts](https://www.nass.usda.gov/Charts_and_Maps/Crop_Progress_&_Condition/index.php)

### 3.3 USDA FAS Export Sales (ESRQS)
- **Variable** : ventes export hebdo maïs US, par destination.
- **Fréquence** : hebdomadaire, jeudi 8:30 ET.
- **Historique** : depuis 1990+.
- **Accès** : API ESRQS (sans clé jusqu'au 02/04/2026, nouvelle plateforme ensuite).
- **Coût** : gratuit.
- **Publication lag** : ~1 jour ouvré.
- **Variables à construire** : export_pace_vs_USDA_forecast, surprise_destination (Chine, Mexique, Japon).
- **Statut projet** : `MANQUANT` actif — `FAS_API_KEY` non fournie, colonnes NaN. Historique partiel possible via ETUDE-09.
- **Risque leakage** : nul si date publication respectée.

[FAS Data](https://www.fas.usda.gov/data), [ESRQS](https://apps.fas.usda.gov/esrquery/esrq.aspx), [Weekly Export Sales](https://www.fas.usda.gov/data/weekly-export-sales-2)

### 3.4 CFTC Commitments of Traders (COT)
- **Variable** : positions traders (commercial, non-commercial, non-reportable) maïs.
- **Fréquence** : hebdomadaire (mardi, publié vendredi 15:30 ET).
- **Historique** : depuis 1986.
- **Accès** : API CFTC Public Reporting Environment (CSV/RDF/RSS/TSV/XML).
- **Coût** : gratuit.
- **Publication lag** : 3 jours (mardi snapshot → vendredi publication).
- **Variables à construire** : net_noncomm_z, change_noncomm_5w, crowding_ratio (net / OI total), percentile_long/short_252w.
- **Statut projet** : `INTÉGRÉ` (3152 non-null, NaN pre-2013 documenté ETUDE-14).
- **Risque leakage** : faible mais important — utiliser la date de **publication** (vendredi), pas la date de snapshot (mardi).

[CFTC COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm), [Public Reporting Environment](https://publicreporting.cftc.gov/stories/s/Commitments-of-Traders/r4w3-av2u/), [Historical Compressed](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm)

### 3.5 USDA Drought Monitor
- **Variable** : index D0–D4 par état + Corn Belt agrégé.
- **Fréquence** : hebdomadaire (jeudi 8:30 ET).
- **Historique** : depuis 2000.
- **Accès** : web + CSV.
- **Coût** : gratuit.
- **Publication lag** : ~1 jour.
- **Statut projet** : `INTÉGRÉ` (3300 lignes).

### 3.6 EIA Ethanol Weekly
- **Variable** : production éthanol US, stocks, demande.
- **Fréquence** : hebdomadaire.
- **Historique** : depuis 2010.
- **Accès** : API v2 EIA.
- **Statut projet** : `INTÉGRÉ` (3805 lignes).

---

## 4. BILANS FONDAMENTAUX EUROPE

### 4.1 EC MARS Bulletin (JRC)
- **Variable** : rendements EU corn estimés + NDVI anomaly EU + crop condition.
- **Fréquence** : mensuelle.
- **Historique** : depuis 2007 (Agri4Cast Toolbox).
- **Accès** : Agri4Cast Toolbox (web download, partiellement API).
- **Coût** : gratuit.
- **Publication lag** : ~10–20 jours après la fin du mois observé.
- **Variables à construire** : yield_revision_mom, ndvi_anomaly_eu, yield_forecast_z.
- **Statut projet** : `MANQUANT` — `V7-11A` WAITING_DATA.
- **Priorité** : HAUTE — driver Europe principal.

[JRC MARS Bulletin](https://joint-research-centre.ec.europa.eu/monitoring-agricultural-resources-mars/jrc-mars-bulletin_en), [MARS overview](https://joint-research-centre.ec.europa.eu/monitoring-agricultural-resources-mars_en), [Crop Monitoring Europe (Copernicus)](https://www.copernicus.eu/en/use-cases/crop-monitoring-europe)

### 4.2 FranceAgriMer — bilans céréales + note conjoncture
- **Variable** : bilan maïs France (production, utilisation, stocks, exports), port shipments.
- **Fréquence** : mensuelle (note conjoncture) + hebdo (cereobs).
- **Historique** : ≥20 ans (cereobs).
- **Accès** : PDF mensuel + data.gouv.fr datasets.
- **Coût** : gratuit.
- **Publication lag** : 15–30 jours.
- **Variables à construire** : bilan_revision_mom, exports_pace_yoy, stocks_france_z.
- **Statut projet** : `MANQUANT` actif — `V7-11B` WAITING_DATA.

[FranceAgriMer Chiffres et bilans](https://www.franceagrimer.fr/Eclairer/Etudes-et-Analyses/Chiffres-et-bilans), [Note de conjoncture mensuelle grandes cultures](https://www.franceagrimer.fr/chiffre-et-analyses-economiques/note-de-conjoncture-mensuelle-grandes-cultures), [data.gouv.fr FranceAgriMer datasets](https://www.data.gouv.fr/organizations/franceagrimer-etablissement-national-des-produits-de-l-agriculture-et-de-la-mer/datasets)

### 4.3 Eurostat COMEXT — import/export maïs EU
- **Variable** : import/export maïs UE (HS 1005) par pays et partenaire.
- **Fréquence** : mensuelle.
- **Historique** : depuis 1988.
- **Accès** : API REST `https://ec.europa.eu/eurostat/api/comext/dissemination` + Easy Comext + bulk CSV.
- **Coût** : gratuit.
- **Publication lag** : 6–8 semaines après le mois.
- **Variables à construire** : import_eu_corn_mt (Ukraine, USA, Brésil), export_eu_corn_mt, balance trade.
- **Statut projet** : `MANQUANT` — `V7-11C` WAITING_DATA.

[Eurostat ITG Database](https://ec.europa.eu/eurostat/web/international-trade-in-goods/database), [Easy Comext](https://ec.europa.eu/eurostat/comext/newxtweb/), [Comext API Getting Started](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/comext-database), [Agri-food data portal cereals](https://agridata.ec.europa.eu/extensions/DataPortal/cereals.html)

### 4.4 European Commission — Cereals Market Observatory
- **Variable** : prix moyens EU par État Membre, market dashboards.
- **Fréquence** : hebdomadaire/mensuelle.
- **Historique** : ≥15 ans.
- **Accès** : web + Agridata Portal.
- **Coût** : gratuit.
- **Publication lag** : 7–14 jours.
- **Statut projet** : `MANQUANT`.

[EC Cereals Statistics](https://agriculture.ec.europa.eu/data-and-analysis/markets/overviews/market-observatories/crops/cereals-statistics_en)

---

## 5. UKRAINE + MER NOIRE

### 5.1 UkrAgroConsult AgriSupp
- **Variable** : exports maïs Ukraine mensuels, ports.
- **Fréquence** : mensuelle/quotidienne (selon abonnement).
- **Historique** : multi-années (plateforme AgriSupp).
- **Accès** : abonnement payant ; news gratuites partielles.
- **Coût** : abonnement institutionnel.
- **Publication lag** : 1–2 semaines.
- **Statut projet** : `MANQUANT` — `V7-11D` WAITING_DATA.

[UkrAgroConsult](https://ukragroconsult.com/en/), [APK-Inform](https://www.apk-inform.com/en)

### 5.2 USDA FAS GAIN reports (Ukraine)
- **Variable** : Grain and Feed Quarterly Ukraine.
- **Fréquence** : trimestrielle + ad-hoc.
- **Accès** : gratuit, PDF GAIN report.

### 5.3 Ukraine Customs / Open Data Portal
- **Variable** : exports détaillés.
- **Fréquence** : mensuelle.
- **Accès** : partiel ; en pratique GAIN/UkrAgroConsult dominent.

---

## 6. BRÉSIL

### 6.1 CONAB Safra/Safrinha
- **Variable** : production maïs 1ère, 2ème, 3ème récolte ; stocks.
- **Fréquence** : mensuelle.
- **Historique** : ≥20 ans.
- **Accès** : web conab.gov.br + PDF.
- **Coût** : gratuit.
- **Publication lag** : 7–14 jours.
- **Variables à construire** : safra_revision_mom, ratio safrinha/safra.
- **Statut projet** : `MANQUANT`.

[USDA FAS GAIN Brazil Reports](https://apps.fas.usda.gov/newgainapi/api/Report/DownloadReportByFileName?fileName=Grain+and+Feed+Annual_Brasilia_Brazil_BR2025-0009.pdf)

### 6.2 SECEX (MDIC) — exports Brésil
- **Variable** : exports maïs mensuels par port (Paranaguá, Santos, Itaqui).
- **Fréquence** : mensuelle.
- **Accès** : web public.
- **Coût** : gratuit.
- **Publication lag** : 1–2 semaines.

---

## 7. ARGENTINE

### 7.1 Bolsa de Cereales Buenos Aires
- **Variable** : estimations production maïs Argentine, semis/récolte progress.
- **Fréquence** : hebdomadaire/mensuelle.
- **Accès** : web public.
- **Coût** : gratuit.

---

## 8. CHINE

### 8.1 Dalian DCE Corn Futures
- **Variable** : settlement, OHLCV, OI futures maïs Chine.
- **Fréquence** : intraday + EOD.
- **Historique** : depuis 2004.
- **Accès** :
  - DCE officiel (`dce.com.cn`)
  - ICE Data Services (consolidated feed, abonnement)
  - Nasdaq Data Link (Chinese Futures Data)
  - CEIC (settlement monthly avg)
  - Barchart `XV*0`.
- **Coût** : gratuit DCE direct, payant pour API enterprise.
- **Publication lag** : EOD jour J+1.
- **Variables à construire** : DCE_z, spread DCE-CBOT_CNY, lead-lag.
- **Statut projet** : `MANQUANT` (collecteur `dce_dalian_collector.py` existe — à activer).

[DCE Site](http://www.dce.com.cn/DCE/), [ICE DCE Catalog](https://developer.ice.com/fixed-income-data-services/catalog/dalian-commodity-exchange-dce), [Nasdaq Data Link DY8](https://data.nasdaq.com/databases/DY8), [Barchart DCE Corn](https://www.barchart.com/futures/quotes/XV*0/futures-prices)

### 8.2 China customs / imports
- **Variable** : imports maïs Chine.
- **Fréquence** : mensuelle.
- **Accès** : web GACC + USDA FAS GAIN China.

---

## 9. PRIX FOB / FRET

### 9.1 FOB Bordeaux corn
- **Variable** : prix FOB Bordeaux maïs.
- **Source** : FranceAgriMer + CommoPrices.
- **Fréquence** : quotidienne.
- **Accès** : CommoPrices abonnement, FranceAgriMer hebdo gratuit.
- **Coût** : abonnement (CommoPrices), gratuit partiel.
- **Statut projet** : `MANQUANT` — `V7-11F` WAITING_DATA.

[CommoPrices Corn FOB Bordeaux](https://commoprices.com/en/series/THJXJ/corn-fob-bordeaux-french-market), [GrainsPrices FOB](https://grainsprices.com/markets/fob), [US Grains FOB charts](https://grains.org/markets-tools-data/markets/fob-price-charts/)

### 9.2 FOB Ukraine (Odessa/Mykolaiv)
- **Source** : IGC, USDA FAS, Argus, GASC tenders.
- **Coût** : Argus payant, IGC abonnement, GASC partiel public.

### 9.3 FOB Brésil (Paranaguá)
- **Source** : MDIC/SECEX + USDA FAS.
- **Coût** : partiel public.

### 9.4 Baltic Dry Index + sub-indices Panamax/Supramax
- **Variable** : BDI composite + Panamax (60–70k tonnes grain typique), Capesize, Supramax.
- **Fréquence** : quotidienne.
- **Historique** : 1985+.
- **Accès** :
  - Trading Economics (gratuit limité)
  - Investing.com (gratuit limité)
  - Baltic Exchange direct (abonnement)
  - Bloomberg/Reuters (institutionnel)
  - HandyBulk (daily breakdown).
- **Publication lag** : 1 jour.
- **Variables à construire** : BDI_z, BPI/BDI ratio, freight_proxy_panamax_grain.
- **Statut projet** : `MANQUANT` ou `PARTIEL` (proxy via yfinance possible).

[Baltic Exchange Indices](https://www.balticexchange.com/en/data-services/market-information0/indices.html), [Trading Economics Baltic](https://tradingeconomics.com/commodity/baltic), [HandyBulk BDI](https://www.handybulk.com/baltic-dry-index/)

---

## 10. ÉNERGIE EU

### 10.1 TTF Dutch Natural Gas Futures
- **Variable** : prix TTF gaz front month.
- **Fréquence** : intraday + EOD.
- **Historique** : depuis 2003 (ICE Endex).
- **Accès** :
  - yfinance ticker `TTF=F`
  - ICE Endex
  - Investing.com
  - EnergyRiskIQ CSV (limité)
  - OilPriceAPI (commercial).
- **Coût** : gratuit (yfinance), abonnement pour qualité institutionnelle.
- **Publication lag** : nul (intraday).
- **Variables à construire** : ttf_z, ttf_change_5d, ttf_corn_ratio (impact séchage).
- **Statut projet** : `INTÉGRÉ` (2155 lignes via yfinance, EXP-EU-00).
- **Risque leakage** : nul.

[TTF Yahoo Finance](https://finance.yahoo.com/quote/TTF=F/history/), [ICE Dutch TTF](https://www.ice.com/products/27996665/Dutch-TTF-Natural-Gas-Futures/data), [Trading Economics EU Gas](https://tradingeconomics.com/commodity/eu-natural-gas)

### 10.2 EU ETS CO2 Allowance
- **Variable** : prix EUA spot/futures.
- **Fréquence** : quotidienne.
- **Historique** : depuis 2005 (Phase II).
- **Accès** : ICE/EEX + Investing.com.
- **Coût** : gratuit (yfinance proxy), payant qualité.
- **Statut projet** : `MANQUANT`.

### 10.3 Engrais EU (urea, ammonia, phosphate)
- **Source** : Yara, CRU Group, ICIS.
- **Coût** : abonnement institutionnel.
- **Statut projet** : `MANQUANT` — `V7-11G` WAITING_DATA.

---

## 11. CHANGE / MACRO

### 11.1 EUR/USD
- **Source** : yfinance / ECB / FRED.
- **Fréquence** : intraday + EOD.
- **Historique** : 30+ ans.
- **Accès** : gratuit.
- **Variables à construire** : eurusd_level, eurusd_z, regime (appréciation/dépréciation).
- **Statut projet** : `INTÉGRÉ` (5827 lignes via yfinance).

### 11.2 Fed Funds Rate / EUR rate
- **Source** : FRED.
- **Fréquence** : quotidienne.
- **Statut projet** : `INTÉGRÉ` partiellement ; Granger fedfunds → premium REJETÉ OOF (voir feedback memory).

### 11.3 BTP/Bund spread (stress financier EU)
- **Source** : ECB + FRED.
- **Statut projet** : `MANQUANT`.

---

## 12. PRIX MAÏS / INDICES MONDIAUX

### 12.1 FAO Cereal Price Index
- **Variable** : index prix céréales monde (incl maïs).
- **Fréquence** : mensuelle.
- **Historique** : depuis 1990 (séries indexées).
- **Accès** : gratuit via fao.org.
- **Publication lag** : début mois suivant (~7–10 jours).
- **Calendrier 2026** : 9 janv, 6 fév, 6 mar, 3 avr, 8 mai, 5 juin, 3 juil, 7 août, 4 sep, 2 oct, 6 nov, 4 déc.

[FAO Food Price Index](https://www.fao.org/worldfoodsituation/foodpricesindex/en), [AMIS FAO Cereals Index](https://www.amis-outlook.org/indicators/prices/fao-food-price-index/fao-cereals-price-index/en/), [FAO Prices Hub](https://www.fao.org/prices/en)

### 12.2 IGC Grain Market Report (GMR)
- **Variable** : prix, freight, S&D mondiaux.
- **Fréquence** : mensuelle (GMR) + hebdo (GMI).
- **Accès** : abonnement annuel ~2200 £/an (GMR Markets & Trade Plus).
- **Coût** : ~2200 £ / 2860 $ / 2596 €.

[IGC GMR Subscription](https://www.igc.int/en/subscriptions/subscription.aspx), [IGC Publications](http://www.igc.int/en/public-site/publications.aspx), [GMR Summary](https://www.igc.int/en/gmr_summary.aspx)

---

## 13. MÉTÉO

### 13.1 Open-Meteo
- **Variable** : températures, précipitations, vent, par lat/lon historique + forecast.
- **Fréquence** : quotidienne (historique) + horaire (récent).
- **Historique** : depuis 1940.
- **Accès** : API gratuite.
- **Statut projet** : `INTÉGRÉ` partiel via collecteur EU.
- **Priorité V8** : pondérer par production EU (poids France/Roumanie/Hongrie/Espagne/Ukraine ouest).

### 13.2 Copernicus / Sentinel NDVI/EVI
- **Variable** : indices végétation par tile.
- **Accès** : Copernicus Open Access Hub, gratuit.
- **Statut projet** : `MANQUANT`.

### 13.3 NOAA US weather (GHCN, GDD)
- **Source** : NOAA via FRED proxy ou direct.
- **Statut projet** : `INTÉGRÉ` partiel (via WASDE + drought monitor).

---

## 14. OPTIONS / VOLATILITÉ

### 14.1 CBOT Corn options implied vol
- **Variable** : vol implicite ATM 30/60/90 jours.
- **Source** : CME Group, CBOE, Quandl.
- **Coût** : payant qualité.
- **Statut projet** : `MANQUANT`.

### 14.2 Euronext EMA options
- **Variable** : vol implicite EMA.
- **Source** : Euronext NextHistory.
- **Coût** : abonnement.
- **Statut projet** : `MANQUANT`.

---

## 15. PRIORISATION V8

### Priorité 1 (CRITIQUE)
| Source | Statut | Action V8 |
|---|---|---|
| Euronext EMA officiel (NextHistory) | PROXY | Acquisition obligatoire, ticket `V7-01B` actif WAITING_DATA |
| EC MARS Bulletin | MANQUANT | `V7-11A` — parser Agri4Cast PDFs + agrégation mensuelle |
| FAS Export Sales (key API) | MANQUANT actif | Activer `FAS_API_KEY`, brancher pipeline existant |
| FOB Ukraine + FOB Bordeaux | MANQUANT | `V7-11F` — base parité d'export |
| FranceAgriMer bilans | MANQUANT | `V7-11B` |
| Eurostat COMEXT corn EU | MANQUANT | `V7-11C` — API gratuite, intégration directe |

### Priorité 2 (HAUTE)
| Source | Statut | Action V8 |
|---|---|---|
| Baltic Dry Index + sub-indices | PARTIEL | brancher yfinance + Trading Economics |
| Météo EU pondérée production | PARTIEL | pondération + NDVI Copernicus |
| EU ETS CO2 | MANQUANT | ICE/EEX historique |
| Engrais (urea/ammonia) | MANQUANT | `V7-11G` (probablement payant) |
| Ukraine exports détaillés | MANQUANT | `V7-11D` — UkrAgroConsult ou GAIN reports |

### Priorité 3 (MOYENNE)
| Source | Statut | Action V8 |
|---|---|---|
| CONAB Brazil | MANQUANT | scraping mensuel |
| Bolsa de Cereales Argentine | MANQUANT | scraping hebdo |
| Dalian DCE futures | MANQUANT | collector existe, activer |
| FAO Cereal Price Index | MANQUANT | API gratuite |
| BTP/Bund spread | MANQUANT | FRED |

### Priorité 4 (BASSE / OPTIONNEL)
- Options implied vol CBOT/EMA (payant) — pour modèle distributionnel V8.
- Refinitiv/Bloomberg complets — uniquement si transition vers indicateur production.

---

## 16. RISQUES LEAKAGE / PUBLICATION LAG

**Règle générale V8** : pour toute source S, la valeur publiée le jour J ne devient utilisable comme feature qu'à partir de J+1 (shift(1)) à la date de publication réelle, pas à la date de l'événement décrit.

| Source | Publication lag | Risque si non géré |
|---|---|---|
| WASDE | ~0 jour après publication officielle (date connue d'avance) | Modéré — ne pas attribuer la valeur à `date_mois`, mais à `date_publication` |
| NASS Crop Progress | ~1 jour | Faible |
| FAS Export Sales | ~1 jour | Faible |
| COT CFTC | 3 jours (Tue snapshot → Fri publication) | **ÉLEVÉ** — utiliser date Friday, pas Tuesday |
| EC MARS | 10–20 jours après fin mois | Modéré |
| FranceAgriMer | 15–30 jours | Modéré |
| Eurostat COMEXT | 6–8 semaines | Modéré |
| CONAB | 7–14 jours | Modéré |
| FAO | 7–10 jours | Modéré |
| EMA settlement officiel | J+1 | Faible |
| TTF gas | nul | Nul |
| BDI | J+1 | Faible |

---

## 17. ESTIMATION COÛTS POUR ÉTUDE COMPLÈTE (par an, base 2026)

| Niveau | Sources | Coût annuel |
|---|---|---|
| Gratuit minimal | WASDE, NASS, COT, FAS (free), FAO, TTF (yfinance), CBOT (yfinance), EUR/USD, Eurostat COMEXT, EC MARS, BDI (free) | 0 € |
| Recherche EMA officiel | Euronext NextHistory EOD | ~500–3000 € |
| Recherche complet | + IGC GMR + CommoPrices FOB Bordeaux + Argus Black Sea | ~5000–10000 € |
| Production institutionnelle | + Refinitiv Eikon ou Bloomberg complet | ~25000+ € |

Pour V8 actuel : **niveau "gratuit minimal + Euronext NextHistory" suffit** pour conclure la phase recherche.

---

## 18. PIPELINE D'INTÉGRATION V8 (PROPOSITION)

```text
[Sources gratuites]                     [Sources WAITING_DATA]
    yfinance ─── CBOT, EMA proxy, EUR/USD, TTF, BDI proxy
    FRED   ──── fedfunds, btp_bund
    USDA   ──── WASDE, NASS, FAS, drought, EIA
    CFTC   ──── COT
    Open-Meteo ── EU/US weather

         ↓
    src/mais/collect/*

         ↓
    data/interim/

         ↓
    build_features() → data/processed/features.parquet

         ↓
[NEW V8] add EMA officiel slot
         add EC MARS slot
         add FranceAgriMer slot
         add Eurostat COMEXT slot
         add Ukraine exports slot
         add FOB Bordeaux slot

         ↓
    data/processed/features_v8.parquet (avec slots NaN si data absente)

         ↓
    experiments V8 (read-only sur features_v8.parquet)
```

---

## 19. CHECKLIST D'ACCEPTATION D'UNE NOUVELLE SOURCE V8

Avant d'intégrer une source au pipeline `features_v8.parquet` :

1. **Anti-leakage** : `shift(1)` sur date publication, pas date de l'événement.
2. **Z-score expanding** ou rolling, calibré sur train uniquement.
3. **NaN policy** documentée (forward-fill avec limite ? remplir 0 ?).
4. **Stabilité historique** : pas de rupture méthodologique non documentée.
5. **Test unitaire anti-leakage** : `tests/test_v8_anti_leakage.py::test_source_X`.
6. **Documentation** : fiche source dans ce document + factor_metadata.yaml.
7. **Validation V8-DQ-V3** : DQ score positif sur la période.
8. **Ablation préliminaire** : delta_AUC sur cible canonique (premium H40) ≥ 0 et ECE ne se dégrade pas.

---

## Sources principales

- [USDA WASDE](https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report)
- [USDA NASS QuickStats](https://www.nass.usda.gov/Quick_Stats/)
- [USDA FAS Data](https://www.fas.usda.gov/data)
- [CFTC COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)
- [Euronext NextHistory](https://www.euronext.com/en/data/historical-data)
- [Euronext Corn EMA](https://live.euronext.com/en/product/commodities-futures/EMA-DPAR)
- [CME Corn Futures](https://www.cmegroup.com/markets/agriculture/grains/corn.html)
- [JRC MARS Bulletin](https://joint-research-centre.ec.europa.eu/monitoring-agricultural-resources-mars/jrc-mars-bulletin_en)
- [FranceAgriMer Chiffres et bilans](https://www.franceagrimer.fr/Eclairer/Etudes-et-Analyses/Chiffres-et-bilans)
- [Eurostat ITG / COMEXT](https://ec.europa.eu/eurostat/web/international-trade-in-goods/database)
- [EC Cereals Statistics](https://agriculture.ec.europa.eu/data-and-analysis/markets/overviews/market-observatories/crops/cereals-statistics_en)
- [UkrAgroConsult](https://ukragroconsult.com/en/)
- [Baltic Exchange Indices](https://www.balticexchange.com/en/data-services/market-information0/indices.html)
- [ICE Dutch TTF](https://www.ice.com/products/27996665/Dutch-TTF-Natural-Gas-Futures/data)
- [DCE Site](http://www.dce.com.cn/DCE/)
- [FAO Food Price Index](https://www.fao.org/worldfoodsituation/foodpricesindex/en)
- [IGC Subscriptions](https://www.igc.int/en/subscriptions/subscription.aspx)
- [CommoPrices Corn FOB Bordeaux](https://commoprices.com/en/series/THJXJ/corn-fob-bordeaux-french-market)

*Document V8 — sources de données — produit après recherche web 2026-05-30. À mettre à jour à chaque acquisition de nouvelle source.*
