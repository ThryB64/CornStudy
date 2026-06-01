# Réflexion — Trois études complémentaires sur le maïs (CBOT + Euronext)
> Révisé le 2026-05-18. Pivot : target Euronext Matif, features CBOT + données européennes.
> Règle centrale : tout résultat doit être prouvé en OOF strict, IC95%, correction tests multiples,
> évaluation économique. Aucun claim non vérifié dans le rapport final.

---

## 0. Vision globale et recentrage

### 0.1 Ce qu'on peut honnêtement faire

Un indicateur ne peut pas savoir si le prix actuel est le maximum de campagne. C'est impossible en temps réel — même pour les traders professionnels. Cette prétention était la faille centrale de l'objectif initial.

Ce qu'on peut faire honnêtement :

1. **Mesurer le biais directionnel** : étant donné les fondamentaux visibles aujourd'hui, le marché a-t-il plus de chances de monter ou de descendre dans les 40 prochains jours ? (DA 62–64%, faible mais réel)

2. **Identifier ce qui précède les grands mouvements** : quelles combinaisons de signaux observables précèdent des variations de ±5% ? (étude événementielle, extraction de règles lisibles)

3. **Prédire une fourchette de prix** avec un intervalle calibré : non pas "le prix sera 215 €/t" mais "avec 90% de probabilité, le prix sera entre 195 et 238 €/t dans 3 mois" (CQR conformal)

Ces trois objectifs sont défendables, mesurables, et utiles pour un agriculteur.

### 0.2 Pivot vers Euronext Matif comme cible principale

**Pourquoi Euronext plutôt que CBOT ?**
- Les agriculteurs français/européens vendent sur le marché Euronext (EMA, EUR/tonne)
- Le Matif est plus directement utile pour les décisions agricoles en France
- Le CBOT et l'Euronext sont très corrélés (r ≈ 0.85–0.95) mais avec des divergences importantes
- Le marché Euronext est moins liquide → potentiellement moins efficient → plus de signal

**Architecture des données :**
```
Features (X) :
  Données CBOT existantes (fondamentaux US, COT, météo US, WASDE)  ← conservées
  + Données Euronext / Europe (fondamentaux EU, crop EU, météo EU)  ← nouvelles
  + Signaux cross-market (basis CBOT-EMA, EUR/USD, gas EU)          ← nouvelles

Cible (y) :
  Prix Euronext Matif (EMA) — EUR/tonne                            ← pivot
  → direction : P(hausse EMA dans H jours)
  → amplitude : return_ema_hH
  → prix absolu : price_ema_t+H (pour prédiction avec CI)
```

Les fondamentaux US (WASDE, COT, météo Corn Belt) restent des features car le maïs CBOT tire le Euronext. La corrélation est une source d'information, pas un problème.

---

## 1. Trois modules complémentaires

| Module | Question | Sortie | Fréquence |
|---|---|---|---|
| **A — Contexte marché** | Quel est le biais fondamental actuel ? | Dashboard 8–10 signaux | Hebdomadaire (lundi) |
| **B — Grandes variations** | Quoi précède les mouvements de ±5% ? | Règles + carte de risque | Publication d'événement |
| **C — Prédiction de prix** | À quelle fourchette s'attendre dans H jours ? | Prix estimé + IC90% | Hebdomadaire (lundi) |

Ces modules sont complémentaires et non concurrents. Un agriculteur reçoit les trois à la fois.

---

## 2. Données d'entrée — inventaire complet

### 2.1 Données CBOT conservées comme features

Toutes les features existantes restent pertinentes — le CBOT tire l'Euronext :

```
WASDE US (ending stocks, yield, production, feed use, exports, surprises)
COT CFTC (managed money net, commercials, percentiles, crowding score)
Météo Corn Belt (GDD, heat stress, precipitation deficit, drought)
Crop condition NASS (G+E%, momentum, phénologie)
EIA éthanol (production, stocks)
FAS Export Sales US (engagements hebdomadaires)
Horizon sweep features (J+28/35/40/45/60)
Courbe futures CBOT (spreads Z/H/K/N, carry, contango/backwardation)
Signaux cross-asset US (corn/soy ratio, ethanol crush spread, natgas EIA)
```

### 2.2 Nouvelles données Euronext / Europe

**Publications de référence européennes :**

| Source | Fréquence | Contenu | URL / API |
|---|---|---|---|
| EC MARS bulletin | Mensuel (~15) | Crop monitoring EU, rendements estimés | mars.jrc.ec.europa.eu |
| Agreste France | Hebdomadaire (saison) | Crop progress France (surfaces, conditions) | agreste.agriculture.gouv.fr |
| FranceAgriMer | Mensuel | Bilan offertes/demandes France | franceagrimer.fr |
| IGC (Grains Council) | Mensuel | Bilan offre/demande mondial | igc.int |
| Eurostat COMEXT | Mensuel | Flux import/export céréales EU | ec.europa.eu/eurostat |
| COCERAL | Trimestriel | Estimations production EU | coceral.eu |
| UkrAgroConsult | Hebdomadaire/mensuel | Production Ukraine | ukragroconsult.com |
| Copernicus AGRI | Continu | Télédétection cultures EU | copernicus.eu |

**Features fondamentales EU à construire :**

```python
# Bilan EU (EC MARS / FranceAgriMer / IGC)
eu_ending_stocks_mt          # stocks finaux EU (Mt)
eu_production_estimate_mt    # production EU (Mt) — révisée mensuellement
eu_yield_estimate_tha        # rendement EU (t/ha)
eu_stocks_use_ratio          # ratio stocks/utilisation EU
eu_ending_stocks_surprise    # surprise vs mois précédent (signal MARS)
france_corn_production_mt    # France = 1er producteur EU (variable)
ukraine_production_estimate  # Ukraine = ~30% import EU mais post-2022

# Export pace EU
eu_export_pace_mt            # export EU cumulé depuis début campagne
eu_export_pace_vs_forecast   # pace vs prévision EC
eu_import_pace_ukraine       # importations depuis Ukraine (signal tension)

# Crop progress Europe (Agreste + MARS)
france_ge_pct               # état cultures France G+E%
france_crop_condition_lag1  # décalé 1 semaine (publication lundi)
eu_drought_index            # indice sécheresse EU (Copernicus)
eu_soil_moisture_anomaly    # anomalie humidité sol EU vs 30 ans

# Météo EU (Copernicus / ECMWF)
eu_temperature_anomaly      # anomalie T° EU vs normales 30 ans
eu_precip_anomaly_corn_belt # anomalie précip sur zones maïs EU (France, RO, HU)
france_gdd_cumulated        # GDD cumulés France (Corn Belt européenne)
romania_precip_deficit      # Roumanie = 2ème producteur EU
```

**Données Euronext spécifiques :**

```python
# Euronext Commitment of Traders (moins détaillé que CFTC mais disponible)
ema_net_spec_position       # positions nettes spéculatifs Matif
ema_open_interest           # open interest total Matif
ema_cot_percentile          # percentile historique (expanding)

# Spreads Euronext (contrats : novembre, janvier, mars, juin, août)
ema_nov_jan_spread          # spread Nov-Jan (signal offre post-récolte)
ema_jan_mar_spread          # spread Jan-Mars
ema_mar_jun_spread          # spread Mars-Juin
ema_contango_flag           # contango = offre confortable
ema_backwardation_flag      # backwardation = tension physique

# Basis CBOT-Euronext (après conversion EUR/USD)
cbot_ema_basis              # (CBOT_EUR/t) - (EMA EUR/t) — signal relatif
cbot_ema_basis_zscore       # z-score expanding (anti-leakage)
```

**Cross-asset Europe :**

```python
# EUR/USD — critique pour compétitivité exportations EU
eurusd_rate                 # taux de change spot
eurusd_zscore_52w           # z-score 52 semaines

# Energie EU (impacte coûts séchage et engrais)
ttf_natgas_eur              # gas naturel EU (TTF), proxy coût azote
ttf_natgas_zscore           # z-score expanding

# Fret maritime (coût transport grains)
bdi_index                   # Baltic Dry Index (proxy fret mondial)
black_sea_freight_proxy     # fret Mer Noire si disponible

# Concurrence internationale
brazil_corn_export_pace     # Brésil = concurrent export
argentina_production_est    # Argentine (impact hivernal US = été argentin)
```

---

### 2.3 Données mondiales — principaux acteurs du marché maïs

Le maïs est un marché global. Les fondamentaux US et EU ne suffisent pas — la Chine, le Brésil et l'Argentine représentent à eux seuls 60%+ de la production et du commerce mondial.

#### Sources de référence mondiales

| Source | Pays/Zone | Fréquence | Contenu |
|---|---|---|---|
| WASDE USDA (section mondiale) | Monde | Mensuel | Bilan offre/demande mondial par pays |
| IGC Grain Market Report | Monde | Mensuel | Bilan et commerce mondial |
| FAO FPMA | Monde | Mensuel | Prix et marchés alimentaires |
| CONAB | Brésil | Mensuel (9×/an) | Production, stocks, exports Brésil |
| Bolsa de Cereales Buenos Aires | Argentine | Hebdomadaire (saison) | Avancement cultures, production |
| CNGOIC / COFCO | Chine | Mensuel | Production, stocks, imports Chine |
| China Customs (Douanes) | Chine | Mensuel (lag 3 sem) | Flux réels import/export Chine |
| Ukraine MinAgro | Ukraine | Hebdomadaire (récolte) | Progression récolte, exports |
| APK-Inform / UkrAgroConsult | Ukraine | Hebdomadaire | Estimations production et exports |
| MAFF Japan | Japon | Mensuel | Tenders, stocks, consommation |
| Dalian Commodity Exchange (DCE) | Chine | Quotidien | Prix futures maïs chinois |

---

#### Chine — le facteur de demande dominant

La Chine est à la fois le 2ème producteur mondial (~22%) et le principal facteur d'incertitude sur les imports. Une seule décision d'achat de la Chine peut faire bouger les prix de 3–5%.

```python
# Production et bilans
china_corn_production_mt       # production annuelle (Mt) — source WASDE/CNGOIC
china_corn_consumption_mt      # consommation totale (feed + industrial + food)
china_corn_ending_stocks_mt    # stocks finaux (WASDE, souvent surestimés)
china_stocks_use_ratio         # ratio stocks/usage Chine

# Imports/exports
china_corn_import_pace_mt      # imports cumulés depuis déb campagne (customs)
china_corn_import_ytd_vs_5y    # pace import vs moyenne 5 ans
china_corn_import_flag         # 1 si imports en accélération forte

# Signal prix Dalian (DCE) — très important
dce_corn_price_cny_t           # prix futures maïs Dalian (CNY/tonne), contrat spot
dce_corn_price_usd_t           # converti USD/tonne

# Import parity : quand le maïs mondial est compétitif vs prix chinois
china_import_parity_usd_t = (
    cbot_price_usd_t            # CBOT converti en USD/t
    * (1 + china_tariff_rate)   # tarif douanier (1% quota / 65% hors quota)
    + pacific_freight_usd_t     # fret Pacifique (variable, ~30-60 $/t)
    + port_handling_usd_t       # frais portuaires (~10-15 $/t)
)
china_import_incentive = dce_corn_price_usd_t - china_import_parity_usd_t
# Positif → Chine a intérêt à importer → signal haussier CBOT et Euronext
# Négatif → pas d'incentive import → signal neutre/baissier

# Cycle porcin (demand side)
china_hog_inventory_index      # effectif porcin (proxy demande aliment)
# La Fièvre Porcine Africaine (2019-2020) a détruit 40% du cheptel → chute demande maïs
# La reconstruction du cheptel a relancé les imports
china_asf_recovery_flag        # 1 si reconstruction troupeau en cours

# Réserves d'État
china_state_reserve_activity   # 1 si achat réserve en cours, -1 si vente
# Les achats de réserves peuvent absorber des millions de tonnes → signal bullish
```

---

#### Brésil — le concurrent export principal

Le Brésil est devenu le 1er ou 2ème exportateur mondial selon les années. Il représente la principale variable de compétition avec les États-Unis sur les marchés export (Asie, Moyen-Orient).

```python
# Production — deux récoltes
# Safra (1ère récolte) : plantée oct-nov, récoltée fév-mars (25% production)
# Safrinha (2ème récolte) : plantée jan-fév, récoltée juin-août (75% production)
brazil_conab_production_mt       # estimation CONAB (mise à jour mensuelle)
brazil_safrinha_progress_pct     # avancement 2ème récolte (clé : juin-août)
brazil_safrinha_planted_pct      # surfaces plantées safrinha
brazil_conab_export_forecast_mt  # prévision exports CONAB

# Exports
brazil_export_inspection_mt      # inspections portuaires cumulées (hebdo)
brazil_export_ytd_vs_5y          # pace exports vs 5 ans
brazil_fob_paranagua_usd_t       # prix FOB Paranagua/Santos (USD/t)

# Compétition Brésil vs États-Unis
brazil_us_fob_spread = (
    brazil_fob_paranagua_usd_t   # coût Brésil
    - us_fob_gulf_usd_t          # coût US Gulf
)
# Négatif → Brésil moins cher → capte la demande mondiale → baissier CBOT+EMA
# Positif → US moins cher → US gagne des marchés → haussier CBOT+EMA

# Calendrier saisonnier Brésil (signal structurel)
brazil_harvest_pressure_flag = int(month in [6, 7, 8] and brazil_safrinha_progress_pct < 85)
# Quand la safrinha n'est pas encore récoltée : offre tendue → haussier
# Quand elle est récoltée : afflux de grains brésiliens → pression sur les prix
```

---

#### Argentine — le 3ème exportateur

L'Argentine a une dynamique particulière : sa politique d'export taxes (retenciones) peut bloquer ou libérer massivement l'offre selon les décisions gouvernementales.

```python
# Production
argentina_bolsa_production_mt    # Bolsa de Cereales Buenos Aires (hebdo saison)
argentina_minagro_production_mt  # estimation officielle (mensuelle)
argentina_harvest_progress_pct   # avancement récolte (mars-juin)

# Compétition export
argentina_export_inspection_mt   # inspections portuaires Rosario
argentina_fob_rosario_usd_t      # prix FOB Rosario (USD/t)

# Risque politique
argentina_peso_blue_rate         # taux de change parallèle (signal stress devise)
argentina_retenciones_pct        # taux taxes export (variable selon gouvernement)
argentina_farmer_selling_flag    # 1 si agriculteurs argentins vendent activement
# Les agriculteurs argentins stockent souvent → attente dévaluation ou levée taxes
# Quand ils vendent : afflux offre mondiale → baissier

# Calendrier (saison inverse de l'hémisphère nord)
argentina_planting_progress_pct  # semis nov-déc
# Récolte : mars-juin → disponibilité supply mondiale printemps/été boréal
```

---

#### Ukraine — l'incertitude géopolitique permanente post-2022

Avant 2022 : Ukraine = ~15-20% des exports mondiaux de maïs. Post-invasion : variable selon corridor maritime et accords.

```python
# Production
ukraine_production_estimate_mt   # MinAgro/APK-Inform (mensuel)
ukraine_harvest_progress_pct     # avancement récolte (hebdo août-oct)
ukraine_planted_area_mha         # surfaces emblavées (signal annuel)

# Exports
ukraine_export_pace_mt           # inspections/licences exports (hebdo)
ukraine_export_ytd_vs_prev_year  # pace vs année précédente
ukraine_corridor_status          # 1 si corridor maritime opérationnel, 0 sinon
ukraine_rail_volume_mt           # alternative ferroviaire si mer bloquée

# Risque géopolitique (facteur exogène)
ukraine_conflict_intensity       # proxy : nb d'alertes/frappes (if available)
# Si corridor perturbé : EMA monte (pénurie import EU), CBOT moins impacté
```

---

#### Importateurs clés — signaux de demande

Les grands importateurs génèrent des signaux de demande via leurs tenders (appels d'offres) :

```python
# Japon (~7% du commerce mondial, importateur stable)
japan_corn_tender_mt             # appels d'offres réguliers (mensuel)
japan_import_pace_mt             # imports cumulés depuis déb campagne
japan_stocks_ratio               # ratio stocks/utilisation Japon

# Corée du Sud (~6% du commerce mondial)
korea_corn_tender_mt             # tenders KREI/KGMS
korea_import_pace_mt

# Mexique (~6% du commerce mondial, proximité avec US)
mexico_corn_import_mt            # imports (proxy demande US directe)
mexico_production_mt             # production locale

# Égypte (~3%, grand importateur Proche-Orient)
egypt_gasc_tender_mt             # tenders GASC (appels d'offres fréquents)

# Agrégat demande asiatique
asia_total_tender_volume_mt      # somme des appels d'offres Japan+Korea+Vietnam+...
asia_tender_momentum             # variation sur 4 semaines (accélération demande)
```

---

#### Bilan mondial — signal macro

```python
# WASDE monde (publié avec WASDE US, même document)
world_corn_production_mt         # production mondiale (Mt)
world_corn_consumption_mt        # consommation mondiale
world_corn_trade_mt              # commerce mondial
world_ending_stocks_mt           # stocks finaux mondiaux
world_stocks_use_ratio           # ratio stocks/usage mondial (le plus important)
world_ending_stocks_surprise     # révision vs mois précédent WASDE

# IGC report (publication indépendante, souvent en avance sur WASDE)
igc_production_estimate_mt       # alternative à WASDE sur monde
igc_world_stocks_estimate        # cross-check stocks mondiaux

# Concentration risque
top5_exporter_pct_world_trade    # part US+BR+AR+UA+EU dans exports mondiaux
# Si > 90% → choc dans l'un d'eux = choc mondial
```

---

#### Features dérivées — dynamique mondiale

```python
# La compétition entre les 4 grands exportateurs
us_br_ar_ua_relative_price = {
    "us_gulf":         us_fob_gulf_usd_t,
    "brazil_paranagua": brazil_fob_paranagua_usd_t,
    "argentina_rosario": argentina_fob_rosario_usd_t,
    "ukraine_odessa":   ukraine_fob_odessa_usd_t,
}
cheapest_exporter = min(us_br_ar_ua_relative_price)
# Signal : quand US n'est pas le moins cher → bearish pour CBOT et EMA

# Import parity Chine (l'incentive d'achat le plus important)
china_import_incentive_usd_t     # déjà défini ci-dessus — à répliquer pour EU
eu_import_incentive_from_brazil  = ema_price_eur_t - brazil_fob_paranagua_eur_t - eu_freight_t
# Si eu_import_incentive < 0 : EU peut acheter Brésil moins cher → bearish EMA

# Tension physique mondiale
global_physical_tightness_score = (
    world_stocks_use_ratio       # bas → tendu
    + china_import_incentive     # positif → demande Chine active
    - brazil_us_fob_spread       # si Brésil cher → offre moins abondante
)
```

---

#### Calendrier publications mondiales

```python
# Agenda mensuel
publications_calendar = {
    "WASDE":          "2ème vendredi du mois",
    "CONAB_Brazil":   "mi-mois (8-9 fois/an)",
    "IGC_Report":     "dernière semaine du mois",
    "FAO_FPMA":       "début de mois",
    "EC_MARS":        "~15 du mois",
    # Hebdomadaire
    "Ukraine_MinAgro": "vendredi (pendant récolte)",
    "Bolsa_Argentina": "mercredi/jeudi (pendant saison)",
    "Brazil_Inspections": "hebdomadaire",
    "Japan_tender":   "irrégulier mais fréquent",
    # Quotidien
    "DCE_Dalian":     "quotidien (futures chinois)",
    "Brazil_fob":     "quotidien (prix FOB)",
}
```

---

### 2.4 Données cibles — Euronext Matif

```python
# Prix Euronext EMA (en EUR/tonne)
# Fournisseurs : Euronext, Yahoo Finance (EMA=F), Quandl/Refinitiv

# Cibles de direction
y_up_hH_ema     = int(price_ema_t+H > price_ema_t)        # binaire
y_return_hH_ema = (price_ema_t+H - price_ema_t) / price_ema_t  # continu

# Cibles de magnitude (pour Module B)
y_strong_up_ema   = int(return_h40_ema > +0.05)
y_strong_down_ema = int(return_h40_ema < -0.05)
y_triple_barrier  = classifie_triple_barrier(price_ema, barrier=0.03, h=40)

# Cibles de prix absolu (pour Module C)
y_price_ema_1m  = price_ema_t+20   # prix dans 1 mois (EUR/t)
y_price_ema_3m  = price_ema_t+60   # prix dans 3 mois
y_price_ema_6m  = price_ema_t+120  # prix dans 6 mois

# Cible agricole
y_regret_60d    = int(max(price_ema_{t+1...t+60}) > price_ema_t * 1.03)
```

---

## 3. Module A — Indicateur de contexte de marché

### 3.1 Principe

Pas de DA à maximiser. Pas de claim de prédire le prix. Un dashboard de signaux fondamentaux, chacun scoré, agrégé en une orientation générale du marché.

Analogie : une météo agricole du marché. Pas "il fera soleil demain". Plutôt : "pression atmosphérique basse, vent d'ouest, humidité forte → probabilité de pluie élevée". Le farmer sait quoi faire même sans prédiction exacte.

### 3.2 Signaux fondamentaux (8–10)

Chaque signal est calculé de manière indépendante, scoré entre -1 (baissier) et +1 (haussier) :

```python
signals = {
    # ── Offre mondiale ────────────────────────────────────────────────
    "bilan_mondial": score_from_stocks_use_ratio(world_stocks_use_ratio),
    # +1 si ratio mondial faible (tension globale), -1 si ratio élevé

    "bilan_stocks_eu": score_from_stocks_use_ratio(eu_stocks_use_ratio),
    # +1 si stocks EU tendus, -1 si abondants

    "crop_condition_eu": score_from_ge_pct(france_ge_pct, eu_soil_moisture),
    # +1 si conditions dégradées EU (baisse offre future), -1 si bonnes

    # ── Offre compétiteurs ───────────────────────────────────────────
    "brazil_competition": score_from_fob_spread(brazil_us_fob_spread),
    # +1 si Brésil cher vs US → offre mondiale plus tendue (bullish)
    # -1 si Brésil pas cher → capte les marchés export → bearish

    "brazil_supply_pressure": score_from_harvest(brazil_safrinha_progress_pct, month),
    # -1 si safrinha récoltée (afflux offre) en juin-août
    # +1 si safrinha en retard ou problème qualité

    "ukraine_supply": score_from_ukraine(ukraine_corridor_status, ukraine_export_pace_mt),
    # +1 si corridor bloqué ou exports lents (offre réduite)
    # -1 si exports Ukraine normaux ou accélérés

    # ── Demande mondiale ─────────────────────────────────────────────
    "china_demand": score_from_china_incentive(china_import_incentive_usd_t),
    # +1 si DCE > import parity → Chine a incentive à importer (bullish CBOT+EMA)
    # -1 si pas d'incentive → Chine n'achète pas

    "wasde_surprise_mondial": score_from_surprise(world_ending_stocks_surprise),
    # +1 si stocks mondiaux révisés à la baisse, -1 si à la hausse

    "export_pace_eu": score_from_pace_vs_forecast(eu_export_pace_vs_forecast),
    # +1 si exports EU accélèrent vs prévisions, -1 si retard

    # ── Positionnement marché ────────────────────────────────────────
    "cot_positioning": score_from_cot(ema_cot_percentile, cot_mm_percentile),
    # Signal CONTRARIAN : extrême long fonds → risque baissier
    # +1 si fonds très vendeurs (contrarian haussier), -1 si très acheteurs

    "futures_structure": score_from_spread(ema_backwardation_flag, ema_contango_flag),
    # +1 si backwardation EMA (tension physique EU), -1 si contango

    # ── Cross-market ─────────────────────────────────────────────────
    "cbot_ema_basis": score_from_basis(cbot_ema_basis_zscore),
    # +1 si EMA prime vs CBOT (tension EU spécifique)

    "eur_usd_competitiveness": score_from_eurusd(eurusd_zscore_52w),
    # +1 si EUR faible → exports EU compétitifs → soutient demande EMA
}

# Agrégation pondérée (poids calibrés en OOF, somme = 1)
# Signaux monde/offre : 50% | Signaux demande : 30% | Signaux marché : 20%
context_score = weighted_mean(signals, weights=calibrated_weights)

# Signal global
if context_score > 0.30:    signal = "HAUSSIER"
elif context_score < -0.30:  signal = "BAISSIER"
else:                         signal = "NEUTRE"

# Signal dominant (driver principal de la semaine)
dominant_signal = max(signals, key=lambda k: abs(signals[k]))
```

### 3.3 Output — Dashboard hebdomadaire

```
MAÏS EURONEXT — Semaine du [DATE]
Prix actuel : 218 €/t  |  Variation hebdo : +1.2%

CONTEXTE MARCHÉ : LÉGÈREMENT HAUSSIER (score : +0.38)
Driver dominant : Demande Chine (incentive import actif)

OFFRE MONDIALE
  ↑ HAUSSIER  Bilan mondial          Stocks/usage mondial : -12% vs moy 5 ans
  ↑ HAUSSIER  Bilan stocks EU        Ratio stocks EU tendu (-15% vs moy 5 ans)
  ↗ NEUTRE+   Crop condition France  G+E% à 68% (vs 5 ans : 71%)
  → NEUTRE    Brésil safrinha        Récolte 85% — flux normaux, pas de pression extra

DEMANDE MONDIALE
  ↑ HAUSSIER  Chine import           DCE > import parity (+14 $/t) → achats attendus
  ↑ HAUSSIER  Export pace EU         Exportations EU +12% vs prévisions Commission
  ↘ NEUTRE-   Bilan WASDE mondial    Surprise neutre ce mois

POSITIONNEMENT MARCHÉ
  ↓ BAISSIER  COT fonds spéculatifs  Fonds très achetés → risque contrarian
  ↑ HAUSSIER  Structure futures EMA  Backwardation Nov-Jan : tension physique EU
  → NEUTRE    Basis CBOT-EMA         Convergence normale (pas de tension EU spécifique)
  ↑ HAUSSIER  EUR/USD                Euro affaibli : exports EU compétitifs

Points de vigilance :
  ⚠ Fonds spéculatifs en position extrême → retournement possible si mauvaise nouvelle
  ⚠ Publication EC MARS dans 8 jours → ne pas prendre de grande décision avant
  ⚠ Ukraine corridor : situation à surveiller (impact imports EU)
```

### 3.4 Validation du Module A

Le Module A ne cherche pas une DA maximale — il cherche la **cohérence** :

- Quand score haussier, le retour 40 jours est-il positif en moyenne ? (validation ex-post)
- Le score est-il stable d'une semaine à l'autre ? (cohérence temporelle)
- Les signaux individuels sont-ils indépendants ? (absence de double-comptage)
- Le score corrèle-t-il avec la DA hebdomadaire du Module C ? (cohérence inter-modules)

---

## 4. Module B — Étude des grandes variations

### 4.1 Principe

Pas de prédiction quotidienne. Une étude de ce qui précède les mouvements de ±5% sur le Euronext Matif.

> Quelles combinaisons de signaux observables précèdent systématiquement les grandes variations de prix ?

C'est une étude de marché, pas un outil de trading. Le résultat est un ensemble de règles lisibles, vérifiées statistiquement.

### 4.2 Définition des grands mouvements

```python
# Seuils testés
thresholds = [0.03, 0.05, 0.07, 0.10]  # 3%, 5%, 7%, 10%
horizons   = [20, 40, 60, 90]           # jours

# Pour chaque (threshold, horizon) :
big_up_flag   = int(return_ema_hH > +threshold)
big_down_flag = int(return_ema_hH < -threshold)

# Triple-barrier (plus réaliste)
first_hit = "UP" if max_path > +threshold before H
          else "DOWN" if min_path < -threshold before H
          else "NO_HIT"
```

### 4.3 Étude événementielle

Analyser les fenêtres autour des publications clés :

| Publication | Fréquence | Fenêtre d'analyse |
|---|---|---|
| EC MARS bulletin | Mensuel | J-10 → J+10 |
| WASDE US | Mensuel | J-5 → J+10 |
| Agreste crop progress | Hebdomadaire (saison) | J-3 → J+5 |
| FAS Export Sales | Hebdomadaire | J-1 → J+3 |
| COT Euronext | Hebdomadaire | J-1 → J+3 |
| Rapport COCERAL | Trimestriel | J-10 → J+10 |

Pour chaque publication :
- Mesurer la proportion de grands mouvements dans les H jours suivants
- Comparer à la base rate de grands mouvements (bruit de fond)
- Tester si la direction du mouvement est prévisible depuis la surprise

### 4.4 Extraction de règles lisibles

Objectif : produire des règles du type :

```
RÈGLE_01 : FORTE HAUSSE PROBABLE
Condition : eu_stocks_use_ratio < percentile_25
         ET wasde_ending_stocks_surprise < -2_sigma
         ET france_ge_pct < 65%
         ET ema_backwardation_flag = 1
Fréquence historique : 78% des fois → hausse > 5% dans 40 jours
Support : 23 occurrences sur 2010–2022
IC95% [62% ; 91%]

RÈGLE_02 : FORTE BAISSE PROBABLE (CONTRARIAN COT)
Condition : cot_mm_extreme_long_flag = 1
         ET eu_production_estimate revises_up
         ET eurusd_zscore > 1.5 (EUR fort → exports moins compétitifs)
Fréquence historique : 71% des fois → baisse > 5% dans 60 jours
Support : 17 occurrences sur 2010–2022
IC95% [47% ; 88%]
```

Ces règles sont :
- Économiquement motivées (mécanisme explicable)
- Rares (pas de surfit)
- Testables sur le futur (out-of-sample)
- Lisibles par un agriculteur

### 4.5 Méthode d'extraction

```python
# Option 1 : Decision tree shallow (max_depth=3)
# Interprétable, évite le surfit, règles lisibles

# Option 2 : Règles manuelles + validation statistique
# Écrire les règles depuis la connaissance économique
# Tester chaque règle sur OOF : support, précision, IC95%

# Option 3 : Association rules mining (Apriori)
# Trouver les combinaisons de conditions fréquentes

# Validation :
# Chaque règle doit avoir :
#   - Support >= 15 occurrences sur 2010–2022
#   - IC95% précision entièrement au-dessus de 60%
#   - Mécanisme économique documenté
#   - Test de Granger ou chi² pour l'indépendance des conditions
```

### 4.6 Carte de risque hebdomadaire

Chaque lundi : calculer le niveau de risque actuel selon les règles actives.

```
CARTE DE RISQUE — Semaine du [DATE]

Risque de forte baisse (>5% dans 40j) :
  Indicateur : MODÉRÉ (score : 0.42/1.0)
  Règles actives :
    ✓ COT fonds en zone extrême (règle_02 partielle)
    ✗ Pas de révision haussière production EU ce mois
    ✗ EUR/USD neutre
  Conclusion : risque baissier présent mais incomplet

Opportunité de forte hausse (>5% dans 40j) :
  Indicateur : FAIBLE (score : 0.18/1.0)
  Règles actives :
    ✓ Stocks EU sous la moyenne 5 ans
    ✗ Crop condition France correcte (pas de stress visible)
    ✗ WASDE neutre ce mois
  Conclusion : pas de catalyseur haussier identifié
```

---

## 5. Module C — Prédiction de prix avec intervalle de confiance

### 5.1 Principe et honnêteté

Ce module produit une estimation du prix futur, avec un **intervalle calibré**. Il ne dit pas "le prix sera 215 €/t". Il dit :

> Avec 90% de probabilité, le prix du maïs Euronext dans 3 mois sera entre 195 €/t et 238 €/t.

L'intervalle est calibré en conformal (CQR — déjà implémenté dans le projet). La couverture 90% est vérifiable ex-post.

### 5.2 Horizons de prédiction

| Horizon | Jours | Utilité agricole |
|---|---|---|
| Court terme | J+20 (≈1 mois) | Décision de vente imminente |
| Moyen terme | J+60 (≈3 mois) | Planification stockage |
| Long terme | J+120 (≈6 mois) | Décision contrat à terme |

Pour chaque horizon : estimation centrale + IC90% + largeur intervalle (indicateur d'incertitude).

### 5.3 Architecture du modèle

```python
# Niveau 0 : modèles de régression par horizon
# Cible : price_ema_t+H (en EUR/tonne)
# Features : toutes les features X (CBOT + EU)

models_regression = {
    "ridge":      Ridge(alpha=1.0),
    "histgb":     HistGradientBoostingRegressor(),
    "elasticnet": ElasticNet(),
    "quantile_10": GradientBoostingRegressor(loss="quantile", alpha=0.10),
    "quantile_50": GradientBoostingRegressor(loss="quantile", alpha=0.50),
    "quantile_90": GradientBoostingRegressor(loss="quantile", alpha=0.90),
}

# Niveau 1 : CQR (Conformal Quantile Regression) — déjà implémenté
# Calibre les intervalles pour garantir la couverture sur le set de validation
from mais.meta.cqr import walk_forward_cqr

# Validation : couverture cible 90%
coverage = mean(price_actual in [lower_ci, upper_ci])
# Objectif : coverage >= 0.90 sur l'ensemble de validation
# Sharpness : réduire la largeur de l'intervalle sans sacrifier la couverture
```

### 5.4 Métriques de validation

Pour le Module C, les métriques clés sont différentes des modules A et B :

```python
metrics_regression = {
    "rmse":         root_mean_squared_error(y_true, y_pred),       # RMSE (€/t)
    "mae":          mean_absolute_error(y_true, y_pred),           # MAE (€/t)
    "mape":         mean_absolute_percentage_error(y_true, y_pred), # MAPE (%)
    "r2":           r2_score(y_true, y_pred),                      # R² ([-∞, 1])
    "coverage_90":  mean(y_true in ci90),                          # Couverture IC90%
    "sharpness":    mean(ci90_upper - ci90_lower),                 # Largeur IC90% (€/t)
    "winkler_loss": winkler_score(y_true, lower, upper, alpha=0.1), # Trade-off coverage/sharpness
}
```

Baselines à battre :
- **Naive** : `price_t+H = price_t` (marche aléatoire)
- **Seasonal naive** : prix moyen de la même semaine les années précédentes
- **ARIMA** simple sans features fondamentales

### 5.5 Output — Rapport prix hebdomadaire

```
PRÉVISION PRIX MAÏS EURONEXT — Semaine du [DATE]
Prix actuel : 218 €/t

Horizon 1 mois (J+20) :
  Estimation centrale : 221 €/t  [IC90% : 208 – 236 €/t]
  Incertitude : MODÉRÉE (intervalle = 28 €/t)

Horizon 3 mois (J+60) :
  Estimation centrale : 227 €/t  [IC90% : 195 – 261 €/t]
  Incertitude : ÉLEVÉE (intervalle = 66 €/t)
  ⚠ Publication EC MARS et WASDE prévues → incertitude supplémentaire

Horizon 6 mois (J+120) :
  Estimation centrale : 215 €/t  [IC90% : 172 – 259 €/t]
  Incertitude : TRÈS ÉLEVÉE (intervalle = 87 €/t)
  Note : à 6 mois, l'incertitude domine — utiliser avec prudence

Note de calibration :
  Historique : 91.2% des prix réels sont restés dans l'IC90% (objectif ≥ 90%)
  Ce n'est pas une garantie. Les chocs exogènes ne sont pas prévisibles.
```

### 5.6 Adaptive intervals (incertitude contextuelle)

Les intervalles doivent être plus larges dans les situations incertaines :

```python
# Facteurs qui élargissent l'intervalle automatiquement
ci_multiplier = 1.0
if days_to_mars_bulletin <= 7:    ci_multiplier *= 1.15  # EC MARS imminent
if days_to_wasde <= 5:            ci_multiplier *= 1.10  # WASDE US imminent
if ema_cot_extreme_flag:          ci_multiplier *= 1.20  # COT extrême → retournement potentiel
if eu_drought_index > percentile_90: ci_multiplier *= 1.15  # Stress climatique élevé
if ukraine_conflict_escalation_flag: ci_multiplier *= 1.30  # Risque géopolitique actif

ci_adjusted = [lower / ci_multiplier, upper * ci_multiplier]
```

---

## 6. Anti-leakage — règles spécifiques Euronext

Le timing des publications européennes diffère du marché US :

```
EC MARS bulletin : publié ~15 du mois → features disponibles le 16
Agreste crop progress : publié lundi AM → features disponibles lundi PM
  → shift(1) suffisant si signal produit mardi
  → shift(2) si signal produit le lundi même
FAS Export Sales US : jeudi 8h30 ET → disponible jeudi PM Europe
Euronext COT : publié vendredi PM → disponible lundi suivant

Règle générale : shift(1) sur toutes les features SAUF si publication confirmée
avant 9h00 heure de Paris pour un signal produit à la clôture du même jour.
```

---

## 7. Architecture finale — pipeline intégré

```
┌─────────────────────────────────────────────────────────────────────┐
│ COLLECTE HEBDOMADAIRE (vendredi soir / samedi)                     │
│  CBOT : COT, WASDE, FAS, météo US, crop condition US               │
│  EU : MARS (si nouveau), Agreste, FranceAgriMer, Eurostat          │
│  Cross-market : EUR/USD, TTF gas, BDI, spreads futures EMA        │
│  Prix : EMA close vendredi                                          │
└─────────────────────────┬───────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FEATURE ENGINEERING (samedi)                                       │
│  Anti-leakage : shift(1) sur toutes les sources                    │
│  Z-scores expanding (calculés uniquement sur données passées)      │
│  Phénologie EU (semaines calendaires européennes)                  │
│  Basis CBOT-EMA, info_intensity_score                              │
└─────────────────────────┬───────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│ MODULE A : Contexte marché (samedi soir)                           │
│  8 signaux fondamentaux → score [-1, +1]                          │
│  HAUSSIER / NEUTRE / BAISSIER + raison dominante                  │
└────────────────────┬────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────────┐
│ MODULE B : Carte de risque (samedi soir)                           │
│  Règles grandes variations → score risque baissier/haussier        │
│  Alertes si règle active                                           │
└────────────────────┬────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────────┐
│ MODULE C : Prédiction prix (dimanche)                              │
│  Régression + CQR : prix J+20/60/120 avec IC90%                   │
│  Adaptive intervals si événement proche                            │
└────────────────────┬────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────────┐
│ RAPPORT LUNDI MATIN (6h00)                                         │
│  Module A : dashboard contexte                                     │
│  Module B : carte de risque                                        │
│  Module C : fourchettes de prix                                    │
│  Typed uncertainty : UNCERTAIN_NEAR_MARS / _COT_EXTREME / etc.    │
│  Limites honnêtes du modèle                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Principe de fiabilité (inchangé)

### 8.1 Moins de signaux, meilleurs signaux

L'agriculteur prend 6–12 décisions par an. Un signal fiable 25 fois/an est plus utile que du bruit 150 fois/an.

- UNCERTAIN n'est pas un échec — c'est une décision honnête de ne pas décider
- Filtrer sur P(correct) > 0.65 même si ça réduit les signaux de 70%
- Évaluer toujours sur fréquence hebdomadaire (un lundi = une observation)
- Critère de sélection final : gain économique (€/t/an), pas AUC

### 8.2 Incertitude typée

| Code | Signification | Action recommandée |
|---|---|---|
| `UNCERTAIN_NEAR_MARS` | EC MARS dans ≤ 7 jours | Attendre la publication |
| `UNCERTAIN_NEAR_WASDE` | WASDE US dans ≤ 5 jours | Attendre la publication |
| `UNCERTAIN_COT_EXTREME` | COT en zone de retournement | Risque contrarian élevé |
| `UNCERTAIN_UKRAINE_RISK` | Situation Ukraine instable | Facteur exogène imprévisible |
| `UNCERTAIN_DISAGREEMENT` | Modules A/B/C divergent | Signal peu lisible cette semaine |
| `UNCERTAIN_DATA_MISSING` | data_availability < 0.7 | Données EU incomplètes |

### 8.3 Validation robuste

- **IC95% bootstrap** (1000 tirages) sur chaque métrique finale
- **Correction Benjamini-Hochberg** pour les comparaisons multiples
- **Leave-one-year-out** : retirer 2012, 2020, 2022 séparément — mesurer la dégradation
- **No-crisis-years** : tester sans les années de choc (test de robustesse hors crise)
- **Rolling drift alert** : si performance rolling 4 semaines chute → UNCERTAIN automatique
- **Stress test** : données manquantes (MARS non publié, COT absent) → dégradation gracieuse

---

## 9. Archéologie des erreurs et diagnostic

### 9.1 Avant tout développement : comprendre les erreurs actuelles

Prendre les 100 journées où le modèle CBOT était très confiant et s'est trompé.
Analyser : pré-WASDE / COT extrême / saison météo / crise / années normales.
Résultat : liste de 3–5 circonstances où taire le signal.

### 9.2 Replay sur événements historiques Euronext

| Événement EU | Date | Mouvement EMA | Test |
|---|---|---|---|
| Sécheresse EU | Été 2018 | +30% | Signal anticipait ? |
| Choc Covid | Mars 2020 | -15% puis +50% | Transition gérée ? |
| Ukraine invasion | Fév 2022 | +60% | Délai de réaction ? |
| Récolte France record | Automne 2021 | -20% | Signal baissier ? |
| MARS révision baissière | Août 2022 | +12% | Anticipé ou réactif ? |

### 9.3 Tests de causalité de Granger (avant intégration)

Pour chaque nouvelle feature EU : tester d'abord si elle Granger-cause le retour EMA après contrôle des features existantes. Si p-value > 0.05 après BH : variable redondante, ne pas intégrer.

### 9.4 SHAP × mois (quand chaque driver domine)

Matrice feature × mois calendaire sur les données CBOT. Identifier quand chaque driver est actif. Guide pour la spécialisation saisonnière des experts (Module A gate).

---

## 10. Ce qu'il faut éviter

- **Ajouter des données sans mécanisme économique** : chaque source EU doit avoir un raisonnement causal en une phrase
- **Confondre corrélation CBOT-EMA et prédiction** : la corrélation est une feature, pas une preuve que le modèle marche
- **Surestimer les intervalles de confiance** : un IC qui couvre 99% sur 90% déclaré est non informatif
- **Multiplier les seuils libres** : limiter à 3–4 paramètres calibrés sur OOF uniquement
- **Confondre DA quotidienne et valeur agricole** : mesurer sur hebdomadaire, toujours
- **Retourner vers le deep learning massif** avant d'avoir stabilisé les fondamentaux EU
- **Prétendre prédire le maximum de campagne** : l'indicateur mesure un biais, pas un sommet

---

## 11. Roadmap par sprints

### Sprint 0 — Fondations Euronext + données mondiales (URGENT)

```
EXP-EU-00B : Benchmark pivot Euronext minimal  ← FAIRE EN PREMIER
  Objectif : prouver empiriquement que le pivot Euronext vaut le coup
  avant de construire toute l'architecture.

  Comparer 2 cibles × 3 horizons :
    - cible CBOT h20 / h40 / h60  (retour log, sign = direction)
    - cible Euronext EMA h20 / h40 / h60

  Sur 4 feature sets :
    1. CBOT features seules (baseline : modèle actuel)
    2. EMA prix seul + EUR/USD + basis CBOT-EMA
    3. CBOT + EMA + EUR/USD + basis (combiné)
    4. CBOT + données existantes complètes (tout ce qu'on a aujourd'hui)

  Métriques (OOF walk-forward strict, 2012–2024) :
    DA (directionnel)    — principale référence
    AUC                  — robustesse du ranking
    DA top-20%           — performance en signal fort
    RMSE continu         — pour target régression
    IC95% bootstrap (1000 draws) sur chaque DA
    Stabilité annuelle   — DA par année civile (drift ?)
    DA hebdomadaire      — agrégé en semaines

  Outputs attendus :
    tableau_benchmark_pivot.csv   — toutes les métriques × (target, features, horizon)
    pivot_decision.json           — verdict automatique + seuils
    notebook 00_benchmark_pivot_ema.ipynb — visualisation

  Arbre de décision :
    → si DA(EMA) > DA(CBOT) sur horizon h40 : pivot Euronext validé ✓
    → si DA(EMA) ≈ DA(CBOT) (±0.01) : pivot utile (plus métier, même performance)
    → si DA(EMA) < DA(CBOT) : garder CBOT comme moteur, EMA comme conversion
    Seuil minimum DA > 0.55 OOF pour valider le pivot

  Durée estimée : 2–3 heures de compute (walk-forward 2012–2024)
  Fichiers : notebooks/corn_study/euronext/00_benchmark_pivot_ema.ipynb

EXP-EU-00 : Collecteur prix Euronext EMA
  → prix EMA historiques 2010–2025 (Yahoo Finance / Euronext API)
  → calendrier contrats Nov/Jan/Mar/Jun/Aug
  → vérification continuité, qualité, roll des contrats

EXP-EU-01 : Collecteur données fondamentales EU
  → EC MARS bulletin (parser HTML)
  → Agreste crop progress France (Excel)
  → FranceAgriMer bilans (mensuel)
  → EUR/USD, TTF gas, BDI
  → Euronext COT si accessible
  → Eurostat COMEXT (import/export EU)

EXP-WORLD-01 : Collecteur Chine
  → Prix DCE Dalian corn futures (via yfinance ou API)
  → China customs imports corn (mensuel, lag 3 sem)
  → Calcul import parity et china_import_incentive
  → Hog inventory proxy si disponible

EXP-WORLD-02 : Collecteur Brésil
  → CONAB reports (PDF parsing ou web scraping)
  → Export inspections portuaires brésiliennes (ANEC / SECEX)
  → Prix FOB Paranagua/Santos (yfinance ou API)
  → Calcul brazil_us_fob_spread

EXP-WORLD-03 : Collecteur Argentine + Ukraine
  → Bolsa de Cereales crop progress (web scraping)
  → Ukraine MinAgro exports (USDA FAS ou web)
  → Ukraine corridor status (manual flag ou actualité)

EXP-WORLD-04 : Collecteur importateurs clés
  → Japan MAFF tenders (USDA FAS Japan)
  → Korea KREI tenders
  → Egypt GASC tenders (USDA FAS Egypt)
  → Agrégation asia_total_tender_volume

EXP-EU-02 : Features engineering complet
  → z-scores expanding sur toutes sources (anti-leakage strict)
  → basis CBOT-EMA (conversion EUR/USD)
  → info_intensity_score (MARS, Agreste, WASDE, CONAB, DCE)
  → phénologie EU + Brésil + Argentine (calendriers hemisphères)
  → Granger tests sur toutes les nouvelles features avant intégration
```

### Sprint 1 — Diagnostic (en parallèle)

```
EXP-DIAG-01 : Archéologie des erreurs CBOT
  → 100 pires erreurs du modèle actuel
  → circonstances → liste "ne pas signaler"

EXP-DIAG-02 : Replay événements Euronext
  → 2018, 2020, 2022, révisions MARS importantes
  → limites honnêtes de l'indicateur

EXP-DIAG-03 : SHAP × mois sur données CBOT
  → quand chaque driver domine
  → guide spécialisation saisonnière
```

### Sprint 2 — Module A (Dashboard contexte)

```
EXP-MOD-A-01 : Construction des 8 signaux fondamentaux EU
  → bilan stocks EU, export pace EU, crop condition EU, WASDE US,
     COT positionnement, structure futures EMA, basis, EUR/USD
  → calibration poids sur OOF 2010–2020

EXP-MOD-A-02 : Validation et cohérence
  → vérifier : quand score haussier, retour 40j positif en moyenne ?
  → stabilité semaine à semaine
  → IC95% sur chaque signal individuel
```

### Sprint 3 — Module B (Grandes variations)

```
EXP-MOD-B-01 : Étude événementielle EU
  → fenêtres J-10/J+10 autour MARS, Agreste, WASDE
  → proportion grands mouvements (>5%) autour des publications
  → comparaison base rate

EXP-MOD-B-02 : Extraction de règles
  → decision tree max_depth=3 sur données fondamentales EU
  → validation : support ≥ 15 occurrences, IC95% > 60%
  → description économique de chaque règle

EXP-MOD-B-03 : Carte de risque hebdomadaire
  → score risque baissier / score opportunité haussière
  → alertes typées quand règle active
```

### Sprint 4 — Module C (Prédiction de prix avec CI)

```
EXP-MOD-C-01 : Régression prix EMA (J+20, J+60, J+120)
  → modèles : Ridge, HistGBM, quantile regressor
  → baseline : naive, seasonal naive, ARIMA
  → métriques : RMSE, MAE, couverture IC90%, sharpness

EXP-MOD-C-02 : CQR calibration sur Euronext
  → adapter walk_forward_cqr() pour target EMA prix absolu
  → adaptive intervals (MARS/WASDE proximity)
  → validation couverture ≥ 90% sur OOF 2010–2022

EXP-MOD-C-03 : Winkler loss optimization
  → réduire la largeur IC sans sacrifier la couverture
  → comparer : IC fixe vs adaptive vs conditionnelle
```

### Sprint 5 — Intégration et rapport complet

```
EXP-INT-01 : Stacking augmenté cross-fitted sur target EMA
  → X_augmented = CBOT features + EU features + prédictions OOF
  → nested walk-forward obligatoire
  → comparaison : CBOT only vs EU only vs CBOT+EU

EXP-INT-02 : Rapport hebdomadaire intégré
  → pipeline lundi matin automatique
  → Modules A + B + C dans un seul rapport
  → typed uncertainty, limites honnêtes

EXP-INT-03 : Backtest économique Euronext
  → 6 stratégies × 8 crop years EU (2015–2022)
  → gain net en €/t/an vs SELL_HARVEST_EU
  → critère final de validation
```

---

## 12. Priorisation si ressources limitées

Si on ne fait que 4 choses :

1. **EXP-EU-00/01** — Collecter les données EMA + EU (fondation incontournable)
2. **EXP-MOD-A** — Dashboard contexte marché (le plus lisible agricolment)
3. **EXP-MOD-C** — Prédiction prix avec IC (la plus utile pour les décisions concrètes)
4. **EXP-INT-03** — Backtest économique sur EU (seul critère de vérité)

Module B (grandes variations) est enrichissant mais peut être fait plus tard.

---

## 13. Critère de succès global

### Module A
- Cohérence : quand score haussier > 0.30, retour 40j EU positif dans ≥ 60% des cas (OOF)
- Stabilité : signal ne change pas de signe d'une semaine à l'autre sans catalyseur
- Lisibilité : chaque signal compréhensible en une phrase

### Module B
- Règles avec support ≥ 15 occurrences sur 2010–2022
- IC95% précision entièrement > 60% pour chaque règle
- Mécanisme économique documenté

### Module C
- Couverture IC90% ≥ 90% sur validation OOF 2015–2022
- RMSE < RMSE seasonal naive (au moins sur J+60)
- Sharpness améliorée vs IC constant (intervalles adaptatifs plus informatifs)

### Global
- Backtest économique : gain net > 0 €/t/an vs SELL_HARVEST_EU sur ≥ 5/8 crop years EU
- IC95% gain moyen hors 0
- Dégradation gracieuse si données manquantes (pas de crash)

> L'indicateur est fiable quand il satisfait les trois critères simultanément.
> Un seul module excellent ne suffit pas — les trois doivent fonctionner ensemble.
