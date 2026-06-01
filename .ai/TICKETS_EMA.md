# Tickets EXP — Phase Euronext Matif (pivot cible)
> Créé le 2026-05-18. Source : `.ai/REFLEXION_AMELIORATION_INDICATEUR.md`
> Objectif : construire un indicateur fiable sur le maïs Euronext (EMA, EUR/tonne)
> couvrant trois modules : A (contexte marché), B (grandes variations), C (prédiction prix CI).
>
> **Règle centrale** : tout résultat prouvé en OOF strict, IC95% bootstrap, correction BH.
> **Anti-leakage** : shift(1) obligatoire sur toutes les features fondamentales.
> **Baseline** : les tickets R&D CBOT (TICKETS_RD.md) restent valides comme référence.

---

## Conventions transversales

### Statut résultat

| Verdict | Signification |
|---|---|
| CONFIRMÉ | Résultat positif clair, IC95% non-nul, répliqué |
| PROMETTEUR | Signal positif mais non significatif ou non répliqué |
| NEUTRE | Pas d'effet mesurable |
| REJETÉ | Signal négatif ou inférieur à la baseline |
| INCONCLU | Données insuffisantes ou artefact non exploitable |
| STUB | Collecteur non implémenté — données à sourcer manuellement |

### IC95% obligatoire (tous les tickets de modélisation)

```
DA  = 0.XXX [IC95% : 0.XXX ; 0.XXX]   — 1000 bootstrap draws
AUC = 0.XXX [IC95% : 0.XXX ; 0.XXX]
```

### Correction pour tests multiples

Benjamini-Hochberg (FDR) sur toutes les comparaisons inter-modèles ou inter-features.

### Référence agricole

DA hebdomadaire (1 point/semaine, lundi) = référence principale.
DA quotidienne = secondaire (souvent gonflée par autocorrélation WASDE/COT).

### Typed uncertainty

Signal déclaré UNCERTAIN automatiquement si :
- `data_availability_score < 0.7`
- Rolling DA 4 semaines < 0.48
- Publication majeure dans ≤ 5 jours (WASDE/MARS)

---

## Index général

| Ticket | Titre | Priorité | Type | Statut | Dépendances |
|---|---|---|---|---|---|
| [EXP-EU-00B](#exp-eu-00b--benchmark-pivot-euronext-minimal) | Benchmark pivot Euronext minimal | **PRIORITÉ 0** | critique | TODO | — |
| [EXP-EU-00](#exp-eu-00--collecteur-prix-euronext-ema) | Collecteur prix Euronext EMA | **PRIORITÉ 0** | moyen | IN_PROGRESS | — |
| [EXP-EU-01](#exp-eu-01--collecteur-données-fondamentales-eu) | Collecteur données fondamentales EU | HAUTE | moyen | TODO | EXP-EU-00 |
| [EXP-WORLD-01](#exp-world-01--collecteur-chine-dce-dalian) | Collecteur Chine — DCE Dalian | HAUTE | moyen | TODO | — |
| [EXP-WORLD-02](#exp-world-02--collecteur-brésil) | Collecteur Brésil — CONAB + FOB | HAUTE | moyen | TODO | — |
| [EXP-WORLD-03](#exp-world-03--collecteur-argentine--ukraine) | Collecteur Argentine + Ukraine | HAUTE | moyen | TODO | — |
| [EXP-WORLD-04](#exp-world-04--collecteur-importateurs-clés) | Collecteur importateurs clés | MOYENNE | simple | TODO | — |
| [EXP-EU-02](#exp-eu-02--features-engineering-euronext-complet) | Features engineering EU complet | HAUTE | complexe | TODO | EXP-EU-00/01, EXP-WORLD-01/02/03 |
| [EXP-DIAG-01](#exp-diag-01--archéologie-des-erreurs-cbot) | Archéologie des erreurs CBOT | HAUTE | moyen | TODO | EXP-EU-00B |
| [EXP-DIAG-02](#exp-diag-02--replay-événements-historiques-euronext) | Replay événements historiques Euronext | HAUTE | moyen | TODO | EXP-EU-00 |
| [EXP-DIAG-03](#exp-diag-03--shap--mois-drivers-saisonniers) | SHAP × mois — drivers saisonniers | MOYENNE | moyen | TODO | EXP-EU-00B |
| [EXP-MOD-A-01](#exp-mod-a-01--construction-des-12-signaux-fondamentaux) | Construction des 12 signaux fondamentaux | HAUTE | complexe | TODO | EXP-EU-02 |
| [EXP-MOD-A-02](#exp-mod-a-02--calibration-et-validation-module-a) | Calibration et validation Module A | HAUTE | complexe | TODO | EXP-MOD-A-01 |
| [EXP-MOD-B-01](#exp-mod-b-01--étude-événementielle-grandes-variations) | Étude événementielle — grandes variations | MOYENNE | complexe | TODO | EXP-EU-02 |
| [EXP-MOD-B-02](#exp-mod-b-02--extraction-de-règles-lisibles) | Extraction de règles lisibles | MOYENNE | complexe | TODO | EXP-MOD-B-01 |
| [EXP-MOD-B-03](#exp-mod-b-03--carte-de-risque-hebdomadaire) | Carte de risque hebdomadaire | MOYENNE | moyen | TODO | EXP-MOD-B-02 |
| [EXP-MOD-C-01](#exp-mod-c-01--régression-prix-ema-avec-baselines) | Régression prix EMA avec baselines | HAUTE | complexe | TODO | EXP-EU-02 |
| [EXP-MOD-C-02](#exp-mod-c-02--cqr-calibration-sur-euronext) | CQR calibration sur Euronext | HAUTE | complexe | TODO | EXP-MOD-C-01 |
| [EXP-MOD-C-03](#exp-mod-c-03--winkler-loss--adaptive-intervals) | Winkler loss + adaptive intervals | MOYENNE | moyen | TODO | EXP-MOD-C-02 |
| [EXP-INT-01](#exp-int-01--stacking-augmenté-cross-fitted-ema) | Stacking augmenté cross-fitted EMA | MOYENNE | critique | TODO | EXP-MOD-A-02, EXP-MOD-C-02 |
| [EXP-INT-02](#exp-int-02--rapport-hebdomadaire-intégré-euronext) | Rapport hebdomadaire intégré Euronext | MOYENNE | complexe | TODO | EXP-MOD-A-02, EXP-MOD-B-03, EXP-MOD-C-02 |
| [EXP-INT-03](#exp-int-03--backtest-économique-euronext) | Backtest économique Euronext | HAUTE | complexe | TODO | EXP-INT-02 |

**Ordre d'exécution :**
```
Sprint 0 (URGENT) :
  EXP-EU-00B ← FAIRE EN PREMIER — valide le pivot avant tout
  EXP-EU-00 + EXP-WORLD-01/02/03/04 (en parallèle)
  EXP-EU-01 (après EU-00)
  EXP-EU-02 (après EU-00/01 + WORLD-01/02/03)

Sprint 1 (en parallèle du Sprint 0) :
  EXP-DIAG-01 + EXP-DIAG-02 + EXP-DIAG-03

Sprint 2 :
  EXP-MOD-A-01 → EXP-MOD-A-02

Sprint 3 :
  EXP-MOD-B-01 → EXP-MOD-B-02 → EXP-MOD-B-03

Sprint 4 :
  EXP-MOD-C-01 → EXP-MOD-C-02 → EXP-MOD-C-03

Sprint 5 :
  EXP-INT-01 → EXP-INT-02 → EXP-INT-03
```

---

## EXP-EU-00B — Benchmark pivot Euronext minimal

**Priorité** : PRIORITÉ 0 — ne lancer aucun autre ticket de modélisation avant  
**Type** : critique  
**Statut** : IN_PROGRESS  
**Dépendances** : EXP-EU-00 (données EMA requises pour la moitié du benchmark)  
**Notebook** : `notebooks/corn_study/euronext/00_benchmark_pivot_ema.ipynb`

### Contexte

Avant de construire toute l'architecture Euronext (collecteurs, features EU, 3 modules), il faut prouver empiriquement que le pivot vers EMA comme cible principale est justifié. Ce ticket est le juge de paix du pivot : si EMA n'est pas plus prédictible que CBOT, l'architecture reste CBOT mais avec conversion en EUR/t pour l'affichage.

### Question centrale

Avec les mêmes features existantes (CBOT) et le même protocole OOF, est-ce que prédire la direction du Euronext EMA donne un DA ≥ DA(CBOT) ?

### Design expérimental

**Cibles testées × horizons :**

| Cible | H20 | H40 | H60 |
|---|---|---|---|
| `y_up_hH_cbot` | x | x | x |
| `y_up_hH_ema` | x | x | x |

**Feature sets :**

| Feature set | Description | Objectif |
|---|---|---|
| `cbot_only` | Features CBOT existantes (baseline actuel) | Est-ce que les drivers CBOT prédisent EMA ? |
| `ema_cross` | EMA prix t + EUR/USD + basis CBOT-EMA | Peut-on prédire EMA depuis EMA lui-même ? |
| `cbot_ema_combined` | CBOT + EMA prix + EUR/USD + basis | Combiné — meilleur des deux |
| `cbot_full` | Toutes les features existantes du pipeline | Benchmark complet actuel |

**Protocole** :
- Walk-forward OOF strict, expanding, min_train = 3 ans
- N_splits ≥ 8 (2012→2024)
- Même random_state=42 partout
- Anti-leakage : shift(1) sur toutes les features fondamentales

**Modèles** :
- `ridge` (rapide, interprétable — résultat principal)
- `lgbm` (si temps disponible — cross-check)

### Métriques obligatoires

Pour chaque cellule (target × feature_set × horizon × model) :
- DA OOF quotidienne + IC95% bootstrap (1000 draws)
- DA hebdomadaire (agrégé sur lundis)
- AUC OOF + IC95%
- Stabilité annuelle : DA par année civile + std inter-années

### Arbre de décision (verdict automatique sur h40)

```python
da_ema_h40  = résultat EMA  × cbot_only × ridge × h40
da_cbot_h40 = résultat CBOT × cbot_only × ridge × h40

if da_ema_h40 > da_cbot_h40 + 0.01:
    verdict = "PIVOT_VALIDÉ"       # EMA > CBOT → construire architecture EU
elif abs(da_ema_h40 - da_cbot_h40) <= 0.01:
    verdict = "PIVOT_UTILE"        # EMA ≈ CBOT → pivot justifié métier
else:
    verdict = "CBOT_MOTEUR"        # CBOT > EMA → garder CBOT, EMA en conversion

# Seuil minimum absolu
if da_ema_h40 < 0.55:
    verdict += "_DA_INSUFFISANT"   # Même si EMA > CBOT, le niveau est trop bas
```

### Objectifs mesurables

- Tableau complet : 2 cibles × 4 feature sets × 3 horizons × 2 modèles → 48 cellules
- IC95% bootstrap sur chaque DA
- `pivot_decision.json` avec verdict automatique
- Si PIVOT_VALIDÉ : lancer Sprint 0 complet
- Si CBOT_MOTEUR : réévaluer l'architecture (CBOT reste cible, EMA en affichage)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `notebooks/corn_study/euronext/00_benchmark_pivot_ema.ipynb` | **CRÉER** ✓ (stub existant) |
| `artefacts/benchmark_pivot/tableau_benchmark_pivot.csv` | Produit — 48 lignes de résultats |
| `artefacts/benchmark_pivot/pivot_decision.json` | Produit — verdict automatique |
| `artefacts/benchmark_pivot/benchmark_pivot_ema.png` | Produit — visualisation DA × (CBOT vs EMA) |

### Sorties attendues

```json
{
  "generated_at": "2026-XX-XX",
  "da_cbot_h40": 0.XXX,
  "da_ema_h40":  0.XXX,
  "diff_ema_minus_cbot": 0.XXX,
  "da_ema_ci95": [0.XXX, 0.XXX],
  "verdict": "PIVOT_VALIDÉ | PIVOT_UTILE | CBOT_MOTEUR",
  "da_minimum_ok": true | false,
  "recommendation": "..."
}
```

### Vérifications

- [ ] DA CBOT reproductible vs benchmark R&D-01 (±0.005 tolérance)
- [ ] IC95% calculés sur 1000 bootstrap draws
- [ ] Verdict JSON produit et lisible
- [ ] Aucune fuite de données futures dans les features

---

## EXP-EU-00 — Collecteur prix Euronext EMA

**Priorité** : PRIORITÉ 0 — fondation incontournable  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : aucune  
**Notebook** : `notebooks/corn_study/euronext/01_ema_data_collection.ipynb`

### Contexte

Le pivot vers Euronext EMA nécessite l'historique de prix EMA (EUR/tonne) depuis au moins 2010. Sans ces données, EXP-EU-00B ne peut tester que la moitié du benchmark (cibles CBOT seulement).

### Sources à tester (par ordre de préférence)

| Source | Ticker | Couverture attendue | Fiabilité |
|---|---|---|---|
| Yahoo Finance | `EMA=F` | Variable — souvent partielle | Faible |
| Euronext.com | Export manuel CSV | 2000–présent | Haute (source officielle) |
| Quandl/NASDAQ Data Link | `CHRIS/LIFFE_EMA1` | 2005–présent | Haute (payant) |
| Investing.com | Scrape manuel | 2010–présent | Moyenne |

### Objectifs mesurables

- Historique EMA quotidien ≥ 2010–2024 (≥ 3500 jours ouvrés)
- NaN < 2% sur ema_close
- Continuité vérifiée (pas de gaps > 10 jours ouvrés consécutifs)
- Corrélation CBOT-EMA calculée et documentée (attendu r ≈ 0.85–0.95)
- Saisonnalité mensuelle EMA documentée (vs CBOT)
- Basis CBOT-EMA calculé et distribué (EWM std, z-score)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/euronext_ema_collector.py` | **CRÉER** ✓ (existant, à finaliser) |
| `config/sources.yaml` | **MODIFIER** ✓ (fait — `euronext_ema` ajouté) |
| `data/raw/euronext_ema/euronext_ema.csv` | Produit par le collecteur |
| `notebooks/corn_study/euronext/01_ema_data_collection.ipynb` | **CRÉER** ✓ (stub existant) |
| `artefacts/ema_data_quality.png` | Produit — 4 panels qualité données |

### Tâches détaillées

**T1 — Collecte automatique** : tenter `run_collector("euronext_ema")`. Si retourne STUB, passer à T2.

**T2 — Collecte manuelle** (si T1 échoue) :
1. Aller sur euronext.com > Products > Derivatives > Agricultural > Corn (Maïs Rendu Rouen)
2. Historical Data > Export CSV (format standard Euronext)
3. Sauvegarder dans `data/raw/euronext_ema/ema_manual.csv`
4. Le collecteur détecte ce fichier automatiquement (fallback implémenté)

**T3 — Validation qualité** :
```python
assert len(ema) >= 3500, "Historique trop court"
assert ema["ema_close"].isna().mean() < 0.02, "Trop de NaN"
assert ema.index.min().year <= 2012, "Départ trop tardif"
corr_ema_cbot = ema["ema_close"].corr(cbot_eur_t)
assert corr_ema_cbot > 0.80, f"Corrélation insuffisante: {corr_ema_cbot:.3f}"
```

**T4 — Construction des cibles EMA** :
```python
for h in [20, 40, 60]:
    ema_targets[f"y_logret_h{h}_ema"] = np.log(ema_close.shift(-h) / ema_close)
    ema_targets[f"y_up_h{h}_ema"] = (ema_close.shift(-h) > ema_close).astype(int)
    # Note: shift(-h) = regarder H jours dans le futur = OK pour la cible y uniquement
    # Anti-leakage : ces colonnes ne sont JAMAIS utilisées comme features
```

### Vérifications

- [ ] Fichier CSV produit dans `data/raw/euronext_ema/`
- [ ] NaN rate < 2%
- [ ] Corrélation CBOT-EMA (EUR/t) > 0.80
- [ ] Basis calculé (stats : moyenne, std, min, max)
- [ ] Notebook exécutable de bout en bout

---

## EXP-EU-01 — Collecteur données fondamentales EU

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : EXP-EU-00 (EUR/USD requis pour conversion)  

### Contexte

Les fondamentaux européens sont essentiels pour le Module A (signaux contexte) et pour améliorer la prédiction EMA. Ces données ne sont pas disponibles automatiquement — elles nécessitent soit des scrapers, soit des téléchargements manuels.

### Sources à collecter

#### Bloc 1 — Cross-assets EU (collecteur eu_cross_assets, déjà implémenté)

| Feature | Ticker | Source |
|---|---|---|
| `eurusd_rate` | `EURUSD=X` | Yahoo Finance — **enabled: true** |
| `ttf_natgas_eur` | `TTF=F` | Yahoo Finance — **enabled: true** |
| `bdi_index` | Manuel | balticexchange.com ou FRED `DBDI` |

Action : `run_collector("eu_cross_assets")` puis vérifier couverture.

#### Bloc 2 — EC MARS bulletin (stub — collecteur manuel)

Source : https://agri4cast.jrc.ec.europa.eu/DataPortal/
- Données : rendements estimés EU par culture et par pays (mensuel ~15)
- Format : Excel ou API AGRI4CAST JRC
- Colonnes cibles :
  - `eu_yield_estimate_tha` — rendement EU maïs (t/ha)
  - `eu_production_estimate_mt` — production EU maïs (Mt)
  - `eu_ending_stocks_surprise` — révision vs mois précédent
  - `eu_soil_moisture_anomaly` — anomalie humidité sol (Copernicus/MARS)

Procédure manuelle :
1. Accéder au portail JRC AGRI4CAST
2. Sélectionner : Indicators > Crop yield forecast > Corn > EU28
3. Télécharger série historique 2000–présent
4. Sauvegarder dans `data/raw/ec_mars_bulletin/`

**Anti-leakage** : publication ~15 du mois → `shift(1)` mensuel dans `build_features()`.

#### Bloc 3 — Agreste France (stub — collecteur manuel)

Source : https://agreste.agriculture.gouv.fr/agreste-web/
- Données : état des cultures France, G+E% hebdomadaire (saison maïs = mai-octobre)
- Colonnes cibles :
  - `france_ge_pct` — proportion plants en état Bon ou Très Bon
  - `france_corn_harvested_pct` — avancement récolte maïs
- Procédure : télécharger Tableaux "Cultures d'été" section Conjoncture

**Anti-leakage** : publication lundi AM → shift(1) avant utilisation dans modèle produit le lundi.

#### Bloc 4 — FranceAgriMer (stub — collecteur manuel)

Source : https://www.franceagrimer.fr/filieres-vegetales/Cereales
- Données : bilan offre/demande maïs France (mensuel ~10 du mois)
- Colonnes cibles :
  - `france_ending_stocks_mt` — stocks finaux France
  - `france_export_pace_mt` — exports cumulés campagne

#### Bloc 5 — Euronext COT (stub — si accessible)

Source : Euronext website ou abonnement
- Données : positions spéculatives Matif maïs (hebdomadaire vendredi)
- Colonnes cibles :
  - `ema_net_spec_position` — positions nettes spéculatifs
  - `ema_open_interest` — open interest total
  - `ema_cot_percentile` — percentile historique expanding

### Objectifs mesurables

- Bloc 1 (cross-assets) : données disponibles, ≥ 2010, NaN < 5%
- Bloc 2 (EC MARS) : au minimum historique 2015–2024 disponible manuellement
- Bloc 3 (Agreste) : au minimum saisons 2015–2024 disponibles
- Blocs 4 et 5 : "best effort" — données si disponibles gratuitement

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/eu_fundamentals_collector.py` | **CRÉER** ✓ (stub implémenté) |
| `data/raw/eu_cross_assets/eu_cross_assets.csv` | Produit (Bloc 1) |
| `data/raw/ec_mars_bulletin/` | Données manuelles (Bloc 2) |
| `data/raw/agreste_france/` | Données manuelles (Bloc 3) |
| `data/raw/franceagrimer/` | Données manuelles (Bloc 4) |

### Vérifications

- [ ] `run_collector("eu_cross_assets")` → OK (EUR/USD + TTF disponibles)
- [ ] `eurusd_rate` couvre ≥ 2010, NaN < 2%
- [ ] `ttf_natgas_eur` couvre ≥ 2010 (ou note sur gap historique)
- [ ] Au moins 1 source EU fondamentale disponible (MARS, Agreste, ou FranceAgriMer)

---

## EXP-WORLD-01 — Collecteur Chine — DCE Dalian

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : aucune  

### Contexte

La Chine est le facteur de demande le plus important du marché maïs mondial. Le prix DCE Dalian (futures maïs chinois) permet de calculer l'`china_import_incentive`, le signal de demande le plus puissant du système.

```
china_import_incentive = DCE_prix_USD_t - (CBOT_USD_t × (1 + tariff) + fret_Pacifique + frais_portuaires)
Positif → Chine a intérêt à importer → signal haussier CBOT et EMA
Négatif → pas d'incentive → signal neutre/baissier
```

### Sources à tester

| Source | Ticket | Coût | Couverture |
|---|---|---|---|
| yfinance `0#DCE:C` | Tenter en T1 | Gratuit | Incertain |
| Quandl `DCE/CORN` | T2 si abonnement | Payant | 2005–présent |
| DCE website manuel | T3 fallback | Gratuit | Sélectif |
| USDA FAS PSD | T4 substitut | Gratuit | Annuel seulement |

### Tâches détaillées

**T1 — Tentative yfinance** :
```python
result = run_collector("dce_dalian_corn")
# Si STUB → passer T2
```

**T2 — Fallback manuel DCE website** :
1. Aller sur http://www.dce.com.cn/DCE/business/quotedata/corn/c_futures/
2. Télécharger historique prix maïs (玉米, code c)
3. Sauvegarder dans `data/raw/dce_dalian_corn/dce_corn_manual.csv`
4. Colonnes : Date, Close_CNY_t (prix CNY/tonne), Volume

**T3 — Calcul china_import_parity** (après T1 ou T2) :
```python
# Paramètres 2024 (à vérifier)
china_tariff_rate = 0.01          # quota : 1% (7.2 Mt/an) ; hors quota : 65%
pacific_freight_usd_t = 45.0      # variable — proxy via Baltic Dry Index
port_handling_usd_t = 12.0        # frais portuaires Shanghai

china_import_parity = (
    cbot_usd_t * (1 + china_tariff_rate)   # CBOT converti USD/t × 39.368 / 100
    + pacific_freight_usd_t
    + port_handling_usd_t
)
china_import_incentive = dce_usd_t - china_import_parity
```

**T4 — Validation du signal** :
- Granger causality test : `china_import_incentive → y_logret_h40_ema`
- Si p-value > 0.05 après BH : documenter comme signal non confirmé

**T5 — Proxy si DCE indisponible** :
- Utiliser WASDE world ending stocks comme proxy demande Chine
- Documenter clairement la substitution dans les artefacts

### Objectifs mesurables

- `dce_corn_close_cny_t` disponible ≥ 2015 (idéalement 2010)
- `china_import_incentive` calculable sur la période disponible
- Granger test effectué et documenté
- Si données indisponibles : proxy WASDE implémenté et documenté

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/dce_dalian_collector.py` | **CRÉER** ✓ (stub implémenté) |
| `data/raw/dce_dalian_corn/dce_corn.csv` | Produit |
| `artefacts/world/china_import_incentive.parquet` | Produit — série temporelle signal |

### Vérifications

- [ ] Données DCE disponibles (yfinance ou manuel) OU proxy documenté
- [ ] `china_import_incentive` calculable
- [ ] Granger causality test effectué
- [ ] Anti-leakage : CNY/USD FX converti avec taux J-1

---

## EXP-WORLD-02 — Collecteur Brésil

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : aucune  

### Contexte

Le Brésil est le 1er ou 2ème exportateur mondial de maïs selon les années. La safrinha (2ème récolte brésilienne, 75% de la production) récoltée juin-août est le facteur de compétition saisonnier le plus important pour l'EMA pendant l'été européen.

Signal clé : `brazil_us_fob_spread = brazil_fob_paranagua_usd_t - us_fob_gulf_usd_t`
- Négatif → Brésil moins cher → capte les marchés export → baissier CBOT+EMA
- Positif → US moins cher → US gagne les marchés → haussier CBOT+EMA

### Sources à collecter

#### CONAB (production + exports)

Source : https://www.conab.gov.br/info-agro/safras/serie-historica-das-safras
- Données : production totale Brésil, safrinha, exports prévus (mensuel, 9×/an)
- Format : Excel (séries historiques par culture)
- Colonnes cibles :
  - `brazil_conab_production_mt` — production totale Brésil (Mt)
  - `brazil_safrinha_progress_pct` — avancement safrinha (hebdo saison)
  - `brazil_conab_export_forecast_mt` — prévision exports CONAB

#### Prix FOB Paranagua/Santos

Source : USDA FAS, ABIOVE, CNA Brasil, ou Reuters
- Données : prix FOB quotidien USD/tonne
- Proxy possible : calculer depuis CBOT × facteur de conversion si non disponible

#### Export inspections (ANEC/SECEX)

Source : ANEC (Association Nationale des Exportateurs de Céréales) ou SECEX Brésil
- Données : inspections portuaires hebdomadaires (proxy exports réels)

### Tâches détaillées

**T1 — Scraping CONAB** :
- Télécharger Excel séries historiques safra maïs
- Parser avec `pandas.read_excel()`
- Extraire : production totale, safrinha, exports
- Sauvegarder dans `data/raw/conab_brazil/`

**T2 — Prix FOB Paranagua** :
- Tenter USDA FAS PSD API (données annuelles gratuites)
- Si manquant : calculer proxy = CBOT_USD_t + transport_differential (constante ~15-20 $/t)

**T3 — Calendrier safrinha** (signal structurel) :
```python
def brazil_safrinha_pressure_flag(date: pd.Timestamp, progress_pct: float) -> int:
    month = date.month
    if month in [6, 7, 8]:         # période récolte safrinha
        if progress_pct < 85:
            return 1   # récolte en retard → offre tendue → haussier
        else:
            return -1  # récolte complète → afflux offre → baissier
    return 0           # hors saison
```

**T4 — Granger causality** : tester `brazil_us_fob_spread → y_logret_h40_ema`

### Objectifs mesurables

- `brazil_conab_production_mt` disponible ≥ 2015
- `brazil_fob_paranagua_usd_t` disponible ≥ 2015 (ou proxy documenté)
- `brazil_us_fob_spread` calculable sur la période disponible
- `brazil_safrinha_pressure_flag` calculable depuis le calendrier
- Granger test effectué et documenté

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/world_collector.py` | **MODIFIER** — implémenter `conab_brazil` et `brazil_fob_prices` |
| `data/raw/conab_brazil/` | Données CONAB |
| `data/raw/brazil_fob_prices/` | Prix FOB |
| `artefacts/world/brazil_signals.parquet` | Produit — `brazil_us_fob_spread`, `brazil_safrinha_pressure_flag` |

### Vérifications

- [ ] Production CONAB disponible ≥ 2015
- [ ] FOB spread calculable (réel ou proxy documenté)
- [ ] Safrinha flag fonctionnel pour toutes les saisons
- [ ] Anti-leakage : données CONAB = shift(1) mensuel

---

## EXP-WORLD-03 — Collecteur Argentine + Ukraine

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : aucune  

### Contexte

Argentine : 3ème exportateur mondial, dynamique particulière avec les `retenciones` (taxes export) qui peuvent bloquer ou libérer massivement l'offre.

Ukraine : 15-20% des exports mondiaux pré-2022. Post-invasion, variable selon l'état du corridor maritime. Si le corridor est bloqué, l'EMA monte car l'EU est un importateur majeur depuis l'Ukraine.

### Argentine — Bolsa de Cereales

Source : https://www.bolsadecereales.com/
- Données : avancement cultures, estimations production (hebdo pendant saison)
- Colonnes cibles :
  - `argentina_harvest_progress_pct` — récolte mars-juin
  - `argentina_bolsa_production_mt` — estimation production
  - `argentina_retenciones_pct` — taux taxes export (si changement)
  - `argentina_fob_rosario_usd_t` — prix FOB Rosario

Procédure :
1. Accéder à bolsadecereales.com > Cultivos > Maíz > Panorama semanal
2. Télécharger les fichiers hebdomadaires pendant la saison (nov-juin)
3. Sauvegarder dans `data/raw/bcr_argentina/`

### Ukraine — MinAgro + corridor

Sources :
- MinAgro Ukraine : https://minagro.gov.ua/ (récolte hebdomadaire, exports)
- USDA FAS Ukraine Attaché Reports (proxy gratuit, mensuel)
- Ukraine corridor status : **flag manuel** — nécessite suivi actualité

Colonnes cibles :
- `ukraine_export_pace_mt` — exports cumulés campagne
- `ukraine_corridor_status` — 1 si corridor maritime opérationnel, 0 sinon
- `ukraine_harvest_progress_pct` — avancement récolte maïs (août-octobre)

**Importante** : le corridor_status est un facteur exogène géopolitique. Il ne peut pas être prédit. Il génère automatiquement le code `UNCERTAIN_UKRAINE_RISK` si la situation est incertaine.

### Tâches détaillées

**T1 — Argentine** :
- Collecter estimations production Bolsa de Cereales (scraping ou manuel)
- Calculer `argentina_fob_rosario_usd_t` (FOB Rosario, proxy depuis CIF Chicago + coût)
- Implémenter `world_collector.download()` pour source `bcr_argentina`

**T2 — Ukraine** :
- Collecter données export USDA FAS Ukraine (proxy gratuit)
- Créer fichier `data/raw/ukraine_corridor/corridor_status.csv` :
  ```csv
  Date,ukraine_corridor_status,note
  2022-02-24,0,"Invasion — corridor bloqué"
  2022-08-01,1,"Accord céréales — corridor réouvert"
  2023-07-17,0,"Russie dénonce accord"
  ...
  ```
- Ce fichier est maintenu manuellement et mis à jour lors des événements géopolitiques

**T3 — Signal géopolitique Ukraine** :
```python
# Auto-UNCERTAIN si situation instable
def ukraine_risk_flag(corridor_status: int, days_since_change: int) -> str:
    if corridor_status == 0:
        return "UNCERTAIN_UKRAINE_RISK"
    if days_since_change < 30:
        return "UNCERTAIN_UKRAINE_RISK"   # situation récemment changée
    return "STABLE"
```

### Objectifs mesurables

- `argentina_harvest_progress_pct` disponible ≥ 2015 pour les saisons (mars-juin)
- `ukraine_export_pace_mt` disponible ≥ 2015
- `ukraine_corridor_status` disponible depuis 2022 (historique de flag)
- Signal géopolitique Ukraine implémenté dans le système d'incertitude

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/collect/world_collector.py` | **MODIFIER** — implémenter `bcr_argentina` et `ukraine_exports` |
| `data/raw/bcr_argentina/` | Données Bolsa de Cereales |
| `data/raw/ukraine_exports/` | Données export Ukraine |
| `data/raw/ukraine_corridor/corridor_status.csv` | **CRÉER** — flag manuel historique |

### Vérifications

- [ ] Argentine : au moins production et avancement récolte disponibles
- [ ] Ukraine : exports USDA FAS + corridor_status depuis 2022
- [ ] Anti-leakage : données exportation Argentina/Ukraine = shift(1) semaine

---

## EXP-WORLD-04 — Collecteur importateurs clés

**Priorité** : MOYENNE  
**Type** : simple  
**Statut** : TODO  
**Dépendances** : aucune  

### Contexte

Les grands importateurs (Japon, Corée, Égypte) génèrent des signaux de demande via leurs tenders (appels d'offres). Ces tenders sont des faits observables qui signalent un besoin d'achat immédiat → signal haussier à court terme.

### Sources

| Pays | Source | Fréquence | Données |
|---|---|---|---|
| Japon | USDA FAS Japan Attaché | Mensuel | tenders, imports, stocks |
| Corée du Sud | USDA FAS Korea Attaché | Mensuel | tenders KREI/KGMS |
| Égypte | USDA FAS Egypt + GASC | Irrégulier | tenders GASC |
| Agrégat | USDA FAS PSD Global | Mensuel | imports totaux par pays |

### Tâches

**T1 — USDA FAS Global** : télécharger PSD données annuelles imports par pays.
- URL : https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads
- Filtres : Commodity = Corn, Attribute = Imports, Countries = Japan/Korea/Egypt/Mexico

**T2 — Construire agrégats** :
```python
# Agrégat demande asiatique
asia_total_tender_volume_mt = (
    japan_import_pace_mt + korea_import_pace_mt + vietnam_import_mt
)
asia_tender_momentum = asia_total_tender_volume_mt.diff(4)  # variation 4 semaines
```

**T3 — Calendar flag** :
```python
# Flag si tender annoncé récemment (dans les 7 derniers jours)
japan_tender_flag = int(japan_tender_announced_within_7d)
# Source : USDA FAS Grain Circular + Japanese MAFF announcements
```

### Objectifs mesurables

- Imports annuels Japan, Corée, Égypte disponibles ≥ 2010 (via USDA FAS PSD)
- `asia_total_tender_volume_mt` calculable sur données disponibles
- Granger test sur `asia_tender_momentum → y_logret_h20_ema`

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `data/raw/asia_tenders/` | Données USDA FAS PSD |
| `artefacts/world/asia_demand_signals.parquet` | Produit |

---

## EXP-EU-02 — Features engineering Euronext complet

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : TODO  
**Dépendances** : EXP-EU-00, EXP-EU-01, EXP-WORLD-01, EXP-WORLD-02, EXP-WORLD-03  

### Contexte

Transformer toutes les données collectées (EMA, EU, mondiale) en features prêtes pour les modèles. Respect absolu de l'anti-leakage. Toutes les features doivent être disponibles en t-1 maximum pour le modèle calculé en t.

### Features à construire

#### Bloc 1 — Features EMA (prix)

```python
# Prix EMA (shift(1) = valeur de hier)
ema_close_lag1               = ema_close.shift(1)
ema_return_1d                = ema_close.pct_change(1).shift(1)
ema_return_5d                = ema_close.pct_change(5).shift(1)
ema_return_20d               = ema_close.pct_change(20).shift(1)
ema_zscore_52w               = zscore_expanding(ema_close).shift(1)

# Structure terme EMA (si données disponibles)
ema_nov_jan_spread           = ema_nov_price - ema_jan_price   # puis shift(1)
ema_backwardation_flag       = (ema_nov_price > ema_jan_price).astype(int).shift(1)
ema_contango_flag            = (ema_jan_price > ema_nov_price).astype(int).shift(1)
```

#### Bloc 2 — Basis CBOT-EMA

```python
# Conversion CBOT USD/bu → EUR/tonne : × 39.368 / EUR_USD
cbot_eur_t = cbot_close_usd_bu * 39.368 / eurusd_rate
basis = cbot_eur_t - ema_close   # positif = EMA décote vs CBOT (normal = 0 ± 20 €/t)
basis_lag1 = basis.shift(1)
basis_zscore_expanding = zscore_expanding(basis_lag1)  # anti-leakage expanding
```

#### Bloc 3 — EUR/USD compétitivité

```python
eurusd_lag1         = eurusd_rate.shift(1)
eurusd_zscore_52w   = zscore_expanding(eurusd_lag1, window=252)
# EUR faible (z < 0) = exports EU compétitifs = haussier pour EMA
eurusd_change_5d    = eurusd_rate.pct_change(5).shift(1)
```

#### Bloc 4 — TTF gaz EU (coûts)

```python
ttf_lag1            = ttf_natgas_eur.shift(1)
ttf_zscore          = zscore_expanding(ttf_lag1)
ttf_vs_natgas_ratio = ttf_lag1 / natgas_us_lag1   # spread EU vs US gaz
```

#### Bloc 5 — Fondamentaux EU (si disponibles)

```python
# EC MARS (mensuel, shift 1 mois)
eu_yield_est_lag1m             = eu_yield_estimate_tha.shift(30)  # 30 jours calendaires
eu_yield_surprise              = eu_yield_estimate_tha - eu_yield_estimate_tha.shift(30)
eu_production_est_lag1m        = eu_production_estimate_mt.shift(30)

# Agreste France (hebdomadaire, shift 1 semaine)
france_ge_pct_lag1w            = france_ge_pct.shift(5)  # 5 jours ouvrés
france_ge_momentum_4w          = france_ge_pct - france_ge_pct.shift(20)

# Stocks EU
eu_stocks_use_ratio_lag1m      = eu_stocks_use_ratio.shift(30)
eu_stocks_surprise_lag1m       = eu_stocks_surprise.shift(30)
```

#### Bloc 6 — Monde (Chine, Brésil, Ukraine)

```python
# Chine — shift selon fréquence
china_import_incentive_lag1    = china_import_incentive.shift(1)
china_import_flag_lag1         = china_import_flag.shift(1)

# Brésil — shift selon fréquence publication
brazil_us_fob_spread_lag1      = brazil_us_fob_spread.shift(1)
brazil_safrinha_pressure_flag  = compute_flag(safrinha_progress, month).shift(1)

# Ukraine — shift 1 semaine
ukraine_corridor_status_lag1   = ukraine_corridor_status.shift(5)
ukraine_export_pace_lag1w      = ukraine_export_pace_mt.shift(5)
```

#### Bloc 7 — Phénologie EU (calendrier)

```python
# Stades phénologiques EU (analogue phénologie US mais décalés de ~6 semaines)
eu_corn_planting_week    = int(week_of_year in range(18, 23))   # mai
eu_corn_pollination_week = int(week_of_year in range(28, 33))   # juillet
eu_corn_maturity_week    = int(week_of_year in range(35, 42))   # sept-oct
eu_safrinha_brazil_supply_window = int(month in [6, 7, 8])
```

#### Bloc 8 — Info intensity score EU

```python
# Nombre de publications majeures dans les 5 derniers jours (pondéré)
info_intensity_eu = (
    is_mars_day * 3 +       # EC MARS bulletin
    is_wasde_day * 3 +      # WASDE (même document affecte EMA)
    is_agreste_day * 2 +    # Agreste France
    is_franceagrimer_day * 2 +
    is_conab_day * 1.5 +    # CONAB Brésil
    is_igc_day * 1
)
```

### Tests de causalité de Granger (obligatoires avant intégration)

Pour chaque nouvelle feature EU/monde, tester Granger causality vs `y_logret_h40_ema` :
- Maxlag = 20 jours ouvrés (4 semaines)
- p-value < 0.05 après correction Benjamini-Hochberg → intégrer
- p-value ≥ 0.05 → documenter comme "non confirmé" et ne pas intégrer dans le pipeline principal

### Objectifs mesurables

- Toutes les features produites avec shift(1) minimum
- Tests Granger effectués sur chaque nouvelle famille
- Tableau de résultats Granger : feature × (p-value, verdict INTÉGRER/REJETER)
- Features intégrées dans `build_features()` sans briser les features CBOT existantes
- `pytest tests/ -x -q` → PASS
- `from mais.features import build_features; df = build_features()` → OK

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/features/ema_features.py` | **CRÉER** — module features EMA + cross-market |
| `src/mais/features/eu_fundamentals_features.py` | **CRÉER** — features EC MARS, Agreste, FranceAgriMer |
| `src/mais/features/world_features.py` | **CRÉER** — features Chine, Brésil, Argentine, Ukraine |
| `src/mais/features/__init__.py` | **MODIFIER** — importer les nouveaux modules |
| `artefacts/granger_tests/granger_results.csv` | Produit — tableau Granger par feature |
| `tests/test_ema_features.py` | **CRÉER** — 10 tests anti-leakage |

### Vérifications

- [ ] Toutes les features EMA ont shift(1) minimum
- [ ] Basis CBOT-EMA calculé avec EUR/USD t-1
- [ ] Tests Granger effectués sur chaque nouvelle feature
- [ ] `build_features()` retourne ≥ 300 colonnes (vs 289 actuellement)
- [ ] Aucune colonne `y_*` dans les features (anti-leakage)
- [ ] `pytest tests/test_ema_features.py` → PASS

---

## EXP-DIAG-01 — Archéologie des erreurs CBOT

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : EXP-EU-00B (benchmark OOF requis pour les erreurs)  

### Contexte

Avant d'ajouter des features EU, comprendre d'abord pourquoi le modèle CBOT existant se trompe. Prendre les 100 journées où le modèle était très confiant ET s'est trompé → analyser les circonstances. Résultat : liste de 3–5 types de circonstances où le signal doit être tu.

### Tâches

**T1 — Identifier les 100 pires erreurs OOF** :
```python
# Charger prédictions OOF du benchmark canonique (R&D-01)
preds = pd.read_parquet("artefacts/canonical/oof_predictions.parquet")

# Erreurs avec haute confiance
preds["error"] = preds["y_true"] != preds["y_pred"]
preds["confidence"] = abs(preds["proba"] - 0.5) * 2  # 0=incertain, 1=max confiant

worst = preds[preds["error"]].nlargest(100, "confidence")
print(f"100 pires erreurs : dates {worst['date'].min()} → {worst['date'].max()}")
```

**T2 — Analyser les circonstances** pour chaque erreur :
- Pré-WASDE (dans les 5 jours avant WASDE) ?
- COT en position extrême (percentile > 85 ou < 15) ?
- Saison météo critique (juillet US = pollinisation) ?
- Année de crise (2012, 2020, 2022) ?
- Régime marché (tendance vs range) ?

**T3 — Produire la liste de circonstances "ne pas signaler"** :
```json
{
  "silence_conditions": [
    {"condition": "pre_wasde_5d", "frequency_in_worst_100": 0.34, "action": "UNCERTAIN_NEAR_WASDE"},
    {"condition": "cot_extreme_flag", "frequency_in_worst_100": 0.28, "action": "UNCERTAIN_COT_EXTREME"},
    {"condition": "crisis_year", "frequency_in_worst_100": 0.21, "action": "UNCERTAIN_EXOGENOUS"},
    {"condition": "pollination_stress", "frequency_in_worst_100": 0.17, "action": "UNCERTAIN_WEATHER"}
  ]
}
```

**T4 — Vérifier que ces circonstances s'appliquent aussi au signal EMA** :
Comparer : quand le modèle se trompe sur CBOT, se trompe-t-il aussi sur EMA ?

### Objectifs mesurables

- 100 pires erreurs identifiées et datées
- Tableau : circonstance × fréquence dans les 100 pires erreurs × fréquence dans l'ensemble
- Liste finale de 3–5 circonstances de silence documentée dans JSON
- Règles de silence intégrées dans le système d'incertitude typée

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/error_archaeology.py` | **CRÉER** |
| `artefacts/diagnostics/error_archaeology.json` | Produit |
| `artefacts/diagnostics/worst_100_errors.parquet` | Produit |

---

## EXP-DIAG-02 — Replay événements historiques Euronext

**Priorité** : HAUTE  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : EXP-EU-00 (données EMA requises)  

### Contexte

Valider que le modèle aurait réagi (ou aurait dû rester silencieux) sur les grands chocs historiques EMA. C'est le test de réalité de l'indicateur.

### Événements à tester

| Événement | Période | Mouvement EMA | Question |
|---|---|---|---|
| Sécheresse EU | Été 2018 | +25–30% | Signal anticipait avant août ? |
| Choc Covid | Mars-Août 2020 | -15% puis +50% | Transition gérée ? |
| Ukraine invasion | Fév-Mai 2022 | +40–60% | Délai de réaction ? |
| Récolte France record | Automne 2021 | -20% | Signal baissier activé ? |
| MARS révision baissière | Août 2022 | +12% en 2 semaines | Anticipé ou réactif ? |

### Tâches

**T1 — Fenêtres événementielles** :
```python
def replay_event(event_date: str, window_before=30, window_after=60):
    """Calculer le score du modèle dans la fenêtre autour de l'événement."""
    t = pd.Timestamp(event_date)
    window = slice(t - pd.Timedelta(days=window_before), t + pd.Timedelta(days=window_after))
    return {
        "signal_before": model_scores[window].mean(),
        "ema_return_after": ema_close[t:t + pd.Timedelta(days=window_after)].pct_change().iloc[-1],
        "signal_direction_correct": ...
    }
```

**T2 — Pour chaque événement** : calculer si le signal était haussier / baissier / UNCERTAIN dans les 30 jours précédents.

**T3 — Documenter les limites honnêtes** :
- "Le modèle n'anticipait pas l'invasion Ukraine (choc exogène imprévisible)"
- "La sécheresse 2018 : signal haussier activé 3 semaines avant le pic"
- Ces limitations vont directement dans le rapport final

### Objectifs mesurables

- 5 événements analysés dans des fenêtres J-30/J+60
- Verdict par événement : ANTICIPÉ / RÉACTIF / MANQUÉ / EXOGÈNE_IMPRÉVISIBLE
- Rapport `docs/REPLAY_EVENTS_EMA.md`

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/research/replay_analysis.py` | **CRÉER** |
| `docs/REPLAY_EVENTS_EMA.md` | Produit — rapport événements |
| `artefacts/diagnostics/replay_results.json` | Produit |

---

## EXP-DIAG-03 — SHAP × mois — drivers saisonniers

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : EXP-EU-00B (modèle OOF requis)  

### Contexte

Toutes les features n'ont pas la même importance selon la saison. En juillet (pollinisation US), la météo domine. En août-septembre (récolte européenne), les données Agreste dominent. Cette matrice SHAP × mois guide la spécialisation des experts du Module A.

### Tâches

**T1 — Calcul SHAP sur les prédictions OOF** :
```python
import shap
explainer = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(X_oof)
```

**T2 — Agréger par mois calendaire** :
```python
shap_by_month = pd.DataFrame(shap_values, columns=features.columns)
shap_by_month["month"] = X_oof.index.month
shap_matrix = shap_by_month.groupby("month").agg(lambda x: np.abs(x).mean())
# Résultat : matrice (12 mois) × (N features)
```

**T3 — Identifier les top-5 features par mois** :
```python
for month in range(1, 13):
    top5 = shap_matrix.loc[month].nlargest(5)
    print(f"Mois {month}: {top5.index.tolist()}")
```

**T4 — Visualisation heatmap** :
Heatmap features × mois, colorée par importance SHAP absolue normalisée.

### Objectifs mesurables

- Matrice SHAP × mois produite (top-50 features × 12 mois)
- 3 insights clés documentés : "quand chaque famille de features domine"
- Guide pour le Module A : "en juillet → pondérer météo × 1.5, dépouiller COT"

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `artefacts/diagnostics/shap_by_month.parquet` | Produit |
| `artefacts/diagnostics/shap_by_month_heatmap.png` | Produit |
| `docs/SEASONAL_DRIVERS.md` | Produit — guide drivers saisonniers |

---

## EXP-MOD-A-01 — Construction des 12 signaux fondamentaux

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : TODO  
**Dépendances** : EXP-EU-02  

### Contexte

Implémenter les 12 signaux fondamentaux du Module A, scorés entre -1 (baissier) et +1 (haussier). Chaque signal doit être calculable de manière indépendante, avec une interprétation économique claire en une phrase.

### Les 12 signaux et leur implémentation

**Bloc Offre mondiale (poids total = 35%)**

```python
# Signal 1 : Bilan mondial WASDE
def score_bilan_mondial(world_stocks_use_ratio: float) -> float:
    # Ratio stocks/usage mondial : faible = tendu = haussier
    # Seuils historiques 2010-2022 : mean=0.24, std=0.04
    z = -(world_stocks_use_ratio - 0.24) / 0.04  # inversé
    return np.tanh(z / 2)  # [-1, +1]
    # Source : WASDE "World Corn : Ending Stocks / Total Use"

# Signal 2 : Bilan stocks EU
def score_bilan_stocks_eu(eu_stocks_use_ratio: float) -> float:
    # Analogie Signal 1 mais pour l'Europe (source : EC MARS ou IGC)
    z = -(eu_stocks_use_ratio - 0.15) / 0.04  # EU ratio plus faible que monde
    return np.tanh(z / 2)

# Signal 3 : Crop condition EU
def score_crop_condition_eu(france_ge_pct: float, eu_soil_moisture_anomaly: float) -> float:
    # Conditions dégradées = offre future réduite = haussier
    # france_ge_pct : normal = 70-75%, stress = < 60%
    z_crop = -(france_ge_pct - 0.72) / 0.08  # sous 72% = stress
    z_moisture = -eu_soil_moisture_anomaly     # négatif = sec = stress
    return np.tanh((0.7 * z_crop + 0.3 * z_moisture) / 2)
```

**Bloc Offre compétiteurs (poids total = 25%)**

```python
# Signal 4 : Compétition Brésil
def score_brazil_competition(brazil_us_fob_spread: float) -> float:
    # Spread en USD/t. Positif = US moins cher = US gagne les marchés = bullish
    # Mean ~ 0, std ~ 15 $/t
    z = brazil_us_fob_spread / 15.0
    return np.tanh(z / 2)

# Signal 5 : Pression d'offre safrinha
def score_brazil_supply_pressure(brazil_safrinha_progress_pct: float, month: int) -> float:
    # En juin-août : safrinha récoltée = afflux offre = baissier
    if month not in [6, 7, 8]:
        return 0.0  # hors saison = signal neutre
    if brazil_safrinha_progress_pct >= 85:
        return -0.6  # récolte complète = offre abondante = baissier
    elif brazil_safrinha_progress_pct < 50:
        return +0.6  # récolte en retard = offre tendue = haussier
    return 0.0  # récolte normale = neutre

# Signal 6 : Offre Ukraine
def score_ukraine_supply(ukraine_corridor_status: int, ukraine_export_pace_mt: float,
                          ukraine_export_pace_5y_avg: float) -> float:
    if ukraine_corridor_status == 0:
        return +0.8  # corridor bloqué = offre réduite = haussier pour EMA
    pace_z = (ukraine_export_pace_mt - ukraine_export_pace_5y_avg) / max(ukraine_export_pace_5y_avg * 0.2, 0.1)
    return np.tanh(-pace_z / 2)  # pace élevée = offre abondante = baissier
```

**Bloc Demande mondiale (poids total = 25%)**

```python
# Signal 7 : Demande Chine
def score_china_demand(china_import_incentive_usd_t: float) -> float:
    # Positif = DCE > import parity = Chine a incentive à importer = haussier
    # Seuils : > +10 $/t = forte incitation ; < -10 $/t = pas d'incitation
    return np.tanh(china_import_incentive_usd_t / 20.0)

# Signal 8 : Surprise WASDE mondial
def score_wasde_surprise_mondial(world_ending_stocks_surprise_mt: float) -> float:
    # Révision à la baisse des stocks = haussier
    # Magnitude typique : ±5 Mt pour une surprise modérée, ±15 Mt pour surprise forte
    return np.tanh(-world_ending_stocks_surprise_mt / 8.0)  # inversé

# Signal 9 : Export pace EU
def score_export_pace_eu(eu_export_pace_vs_forecast: float) -> float:
    # pace_vs_forecast en ratio : 1.10 = +10% vs prévisions
    z = (eu_export_pace_vs_forecast - 1.0) / 0.10
    return np.tanh(z / 2)
```

**Bloc Positionnement marché (poids total = 15%)**

```python
# Signal 10 : COT positionnement (CONTRARIAN)
def score_cot_positioning(ema_cot_percentile: float, cbot_cot_percentile: float) -> float:
    # CONTRARIAN : fonds très longs = risque retournement = baissier
    # Utiliser percentile expanding de la position nette des fonds spéculatifs
    combined_pct = 0.6 * ema_cot_percentile + 0.4 * cbot_cot_percentile
    z = -(combined_pct - 50) / 25  # percentile 80 → z = -1.2 → score = -0.83
    return np.tanh(z / 2)

# Signal 11 : Structure futures EMA
def score_futures_structure(ema_backwardation_flag: int, ema_contango_flag: int) -> float:
    if ema_backwardation_flag:
        return +0.7   # backwardation = tension physique = haussier
    elif ema_contango_flag:
        return -0.4   # contango = offre confortable = baissier
    return 0.0

# Signal 12 : Basis CBOT-EMA
def score_cbot_ema_basis(cbot_ema_basis_zscore: float) -> float:
    # EMA prime vs CBOT (basis négatif) = tension EU spécifique = haussier pour EMA
    return np.tanh(-cbot_ema_basis_zscore / 2)  # basis négatif → score positif

# Signal bonus : EUR/USD compétitivité (si données disponibles)
def score_eurusd(eurusd_zscore_52w: float) -> float:
    # EUR faible (z négatif) = exports EU compétitifs = haussier pour EMA
    return np.tanh(-eurusd_zscore_52w / 2)  # inversé
```

### Agrégation

```python
# Poids calibrés (à optimiser en OOF mais valeurs initiales ci-dessous)
WEIGHTS = {
    "bilan_mondial":          0.15,
    "bilan_stocks_eu":        0.12,
    "crop_condition_eu":      0.08,
    "brazil_competition":     0.10,
    "brazil_supply_pressure": 0.08,
    "ukraine_supply":         0.07,
    "china_demand":           0.10,
    "wasde_surprise_mondial": 0.10,
    "export_pace_eu":         0.05,
    "cot_positioning":        0.06,
    "futures_structure":      0.05,
    "cbot_ema_basis":         0.04,
}

context_score = sum(signals[k] * WEIGHTS[k] for k in WEIGHTS)
dominant_signal = max(signals, key=lambda k: abs(signals[k]))
```

### Objectifs mesurables

- 12 fonctions de scoring implémentées avec documentation économique
- Tests unitaires sur chaque scoring (cas limites : NaN, extremes, valeurs normales)
- `data_availability_score` calculé pour chaque signal
- Cohérence vérifiée : quand tous les signaux manquent → `UNCERTAIN_DATA_MISSING`

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/modules/module_a.py` | **CRÉER** — 12 fonctions de scoring + agrégateur |
| `src/mais/modules/__init__.py` | **CRÉER** |
| `tests/test_module_a.py` | **CRÉER** — tests unitaires scores |

---

## EXP-MOD-A-02 — Calibration et validation Module A

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : TODO  
**Dépendances** : EXP-MOD-A-01  

### Contexte

Les poids initiaux du Module A sont des hypothèses. Ce ticket les calibre sur les données historiques (OOF 2010–2020, validation 2020–2024) et valide la cohérence du dashboard.

### Tâches

**T1 — Calibration des poids en OOF** :
```python
from scipy.optimize import minimize

def objective(weights, signals_matrix, y_true):
    """Minimiser l'erreur de classification avec poids contraints."""
    weights = softmax(weights)  # contrainte: somme = 1, positifs
    context_score = signals_matrix @ weights
    predictions = (context_score > 0).astype(int)
    return -directional_accuracy(predictions, y_true)  # maximiser DA

result = minimize(objective, x0=initial_weights, method="SLSQP",
                  constraints={"type": "eq", "fun": lambda w: softmax(w).sum() - 1})
optimal_weights = softmax(result.x)
```

**T2 — Validation cohérence** :
```python
# Test de cohérence : quand score > 0.30, retour 40j positif en moyenne ?
strong_bullish_mask = context_score_oof > 0.30
mean_return_when_bullish = ema_return_40d[strong_bullish_mask].mean()
# Objectif : mean_return_when_bullish > 0 (signe positif)

# DA hebdomadaire du score (validation agricole)
weekly_da = compute_weekly_da(context_score_oof, y_up_h40_ema_oof)
# Objectif : weekly_da > 0.55
```

**T3 — Validation stabilité semaine → semaine** :
```python
# Le score ne doit pas changer de signe sans catalyseur identifiable
score_changes = context_score.diff().abs()
# Score change de >0.6 en une semaine → vérifier si événement explicatif
sudden_changes = score_changes[score_changes > 0.6]
```

**T4 — Stress test données manquantes** :
- Retirer chaque signal un par un → mesurer dégradation DA
- Si suppression d'un signal → DA < 0.50 → signal critique (documenter)
- Dégradation gracieuse : avec 50% des signaux manquants, DA doit rester > 0.52

**T5 — IC95% sur DA du Module A** :
```python
da_module_a = compute_weekly_da(context_score, y_up_h40_ema)
ci95 = bootstrap_ci(da_module_a, n=1000)
print(f"Module A weekly DA = {da_module_a:.4f} [{ci95[0]:.4f}, {ci95[1]:.4f}]")
```

### Objectifs mesurables

- DA hebdomadaire Module A > 0.55 sur validation OOF 2020–2024
- IC95% da_module_a entièrement > 0.50 (signal au-dessus du bruit)
- Cohérence : mean_return_when_bullish > 0, mean_return_when_bearish < 0
- Stabilité : < 10% des semaines avec changement de signe inexpliqué
- Stress test : dégradation gracieuse documentée

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/modules/module_a.py` | **MODIFIER** — ajouter `calibrate_weights()`, `validate_coherence()` |
| `artefacts/module_a/calibrated_weights.json` | Produit |
| `artefacts/module_a/module_a_backtest.parquet` | Produit — score × date × da × retour |
| `docs/MODULE_A_VALIDATION.md` | Produit — rapport validation |

---

## EXP-MOD-B-01 — Étude événementielle — grandes variations

**Priorité** : MOYENNE  
**Type** : complexe  
**Statut** : TODO  
**Dépendances** : EXP-EU-02  

### Contexte

Étudier ce qui précède les mouvements de ±5% sur l'EMA. Pas de prédiction continue — une étude de marché produisant des règles lisibles et économiquement motivées.

### Définition des grands mouvements

```python
# Seuil principal : ±5% dans 40 jours
THRESHOLD = 0.05
HORIZON = 40

big_up_flag   = (ema_return_h40 > +THRESHOLD).astype(int)
big_down_flag = (ema_return_h40 < -THRESHOLD).astype(int)

# Fréquence historique attendue (base rate)
base_rate_up   = big_up_flag.mean()   # attendu ~25-35%
base_rate_down = big_down_flag.mean() # attendu ~25-35%
```

### Étude événementielle

```python
def event_window_analysis(event_dates, ema_prices, window_before=10, window_after=40):
    """Mesurer la proportion de grands mouvements après les publications."""
    results = []
    for date in event_dates:
        window_future = slice(date, date + pd.Timedelta(days=window_after))
        future_return = ema_prices[window_future].pct_change(window_after).iloc[-1]
        results.append({
            "event_date": date,
            "big_up": future_return > 0.05,
            "big_down": future_return < -0.05,
            "return": future_return,
        })
    freq_big_move = pd.DataFrame(results)["big_up"].mean() + pd.DataFrame(results)["big_down"].mean()
    return freq_big_move
```

Publications à analyser :
- EC MARS bulletin (n ≈ 100 publications 2010–2024)
- WASDE US (n ≈ 170 publications)
- Agreste crop progress France (n ≈ 400 hebdomadaires saison)
- Révisions CONAB Brésil (n ≈ 80 publications)

Test statistique : Fisher exact test — `proportion_grands_mouvements_post_event vs base_rate`.

### Objectifs mesurables

- Fréquences de grands mouvements mesurées pour chaque type de publication
- Test statistique (Fisher) : p-value < 0.05 après BH pour les publications significatives
- 2 publications identifiées comme "amplificateurs de volatilité" → alertes dans le Module B

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/modules/module_b.py` | **CRÉER** — `event_window_analysis()` |
| `artefacts/module_b/event_study_results.json` | Produit |
| `artefacts/module_b/volatility_calendar.parquet` | Produit |

---

## EXP-MOD-B-02 — Extraction de règles lisibles

**Priorité** : MOYENNE  
**Type** : complexe  
**Statut** : TODO  
**Dépendances** : EXP-MOD-B-01  

### Contexte

Extraire des règles du type "quand A ET B ET C → forte hausse probable avec X% de probabilité". Ces règles doivent être économiquement motivées, rares, et testables sur le futur.

### Méthode

**Option 1 — Decision tree (max_depth=3)** :
```python
from sklearn.tree import DecisionTreeClassifier, export_text

clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=15, class_weight="balanced")
clf.fit(X_train, big_up_flag_train)
rules_text = export_text(clf, feature_names=X_train.columns.tolist())
print(rules_text)
```

**Option 2 — Règles manuelles + validation statistique** :
Écrire les règles depuis la connaissance économique puis tester chacune sur OOF.

### Critères de validation pour chaque règle

```python
def validate_rule(rule_mask, y_true, n_bootstrap=1000):
    support = rule_mask.sum()
    precision = y_true[rule_mask].mean()
    ci = bootstrap_ci(y_true[rule_mask].values, n=n_bootstrap)

    return {
        "support": support,            # >= 15 requis
        "precision": precision,        # >= 0.60 requis (IC95% entièrement > 0.50)
        "ci95_lo": ci[0],
        "ci95_hi": ci[1],
        "valid": support >= 15 and ci[0] > 0.50,
    }
```

### Format des règles produites

```json
{
  "rule_id": "RULE_01",
  "direction": "FORTE_HAUSSE",
  "conditions": [
    {"feature": "eu_stocks_use_ratio", "operator": "<", "threshold": 0.18},
    {"feature": "wasde_world_ending_stocks_surprise", "operator": "<", "threshold": -5.0},
    {"feature": "france_ge_pct", "operator": "<", "threshold": 0.65}
  ],
  "support": 23,
  "precision": 0.78,
  "ci95": [0.62, 0.91],
  "economic_rationale": "Stocks EU tendus + révision baissière WASDE + mauvaise récolte France = tensions cumulées",
  "alert_message": "Trois conditions de tension cumulées — forte hausse probable dans 40 jours"
}
```

### Objectifs mesurables

- ≥ 3 règles validées (support ≥ 15, IC95% > 0.50)
- Chaque règle a une justification économique documentée en une phrase
- Précision moyenne des règles validées > 0.65

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/modules/module_b.py` | **MODIFIER** — `extract_rules()`, `validate_rule()` |
| `artefacts/module_b/validated_rules.json` | Produit — règles validées |
| `docs/MARKET_RULES.md` | Produit — documentation des règles en langage agriculteur |

---

## EXP-MOD-B-03 — Carte de risque hebdomadaire

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : EXP-MOD-B-02  

### Contexte

Chaque lundi, calculer le score de risque baissier et l'opportunité haussière en fonction des règles actives.

### Implémentation

```python
def compute_risk_card(current_features: pd.Series, rules: list[dict]) -> dict:
    active_rules_up = []
    active_rules_down = []

    for rule in rules:
        if evaluate_rule(rule, current_features):
            if rule["direction"] == "FORTE_HAUSSE":
                active_rules_up.append(rule)
            else:
                active_rules_down.append(rule)

    # Score (0 à 1)
    upside_score = sum(r["precision"] for r in active_rules_up) / len(rules) if rules else 0.0
    downside_score = sum(r["precision"] for r in active_rules_down) / len(rules) if rules else 0.0

    return {
        "upside_score": upside_score,
        "downside_score": downside_score,
        "active_rules_up": [r["rule_id"] for r in active_rules_up],
        "active_rules_down": [r["rule_id"] for r in active_rules_down],
        "alert_messages": [r["alert_message"] for r in active_rules_up + active_rules_down],
    }
```

### Objectifs mesurables

- Carte de risque générée pour la semaine courante
- Format intégrable dans le rapport hebdomadaire (Markdown)
- Backtest : scores de risque corrèlent avec fréquence de grands mouvements observés

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/modules/module_b.py` | **MODIFIER** — `compute_risk_card()` |
| `artefacts/module_b/weekly_risk_card_YYYYMMDD.json` | Produit hebdomadaire |

---

## EXP-MOD-C-01 — Régression prix EMA avec baselines

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : TODO  
**Dépendances** : EXP-EU-02  

### Contexte

Prédire le prix absolu de l'EMA (EUR/tonne) dans H jours, avec des baselines honnêtes à battre. Ce n'est pas de la direction — c'est un niveau de prix pour construire l'intervalle de confiance.

### Baselines obligatoires à implémenter et battre

```python
baselines = {
    "naive": lambda y, h: y.shift(h),         # prix t = prix t+H
    "seasonal_naive": lambda y, h, year: ..., # même semaine années précédentes
    "linear_trend": LinearRegression(),        # tendance linéaire sur 252 jours
    "arima_11": ARIMA(order=(1,1,1)),         # ARIMA simple sans features
}
```

### Modèles de régression

```python
models_regression = {
    "ridge":    Ridge(alpha=10.0),
    "histgb":   HistGradientBoostingRegressor(max_iter=200, max_depth=4),
    "quantile_10": GradientBoostingRegressor(loss="quantile", alpha=0.10, n_estimators=200),
    "quantile_50": GradientBoostingRegressor(loss="quantile", alpha=0.50, n_estimators=200),
    "quantile_90": GradientBoostingRegressor(loss="quantile", alpha=0.90, n_estimators=200),
}
```

### Protocole walk-forward

- Train : expanding, min_train = 3 ans (≥ 756 jours)
- Horizons : J+20, J+60, J+120
- Cible : `y_price_ema_t_plus_H` (prix absolu EMA en EUR/t)

### Métriques

```python
metrics_regression = {
    "rmse":  root_mean_squared_error(y_true, y_pred),    # EUR/t
    "mae":   mean_absolute_error(y_true, y_pred),        # EUR/t
    "mape":  mean_absolute_percentage_error(y_true, y_pred),  # %
    "r2":    r2_score(y_true, y_pred),
}
```

Objectif absolu : RMSE < RMSE(seasonal_naive) sur J+60.

### Objectifs mesurables

- 5 modèles × 3 horizons × métriques complètes avec IC95%
- RMSE ridge < RMSE seasonal_naive sur J+60
- Quantile models produisent intervalles bruts (non calibrés)
- Artefact comparaison baselines vs modèles

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/modules/module_c.py` | **CRÉER** |
| `artefacts/module_c/regression_results.json` | Produit |
| `artefacts/module_c/baseline_comparison.parquet` | Produit |

---

## EXP-MOD-C-02 — CQR calibration sur Euronext

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : TODO  
**Dépendances** : EXP-MOD-C-01  

### Contexte

Adapter le CQR (Conformal Quantile Regression) existant dans `mais.meta.cqr` pour la cible prix absolu EMA. Garantir une couverture IC90% ≥ 90% sur la validation OOF.

### Implémentation

```python
from mais.meta.cqr import walk_forward_cqr

# Adapter walk_forward_cqr() pour target EMA prix absolu
results_cqr = walk_forward_cqr(
    X=features_eu,
    y=y_price_ema_60d,     # prix absolu EMA dans 60j
    quantile_model_lo=quantile_10_model,
    quantile_model_hi=quantile_90_model,
    calibration_size=252,  # 1 an de calibration conformal
    target_coverage=0.90,
)

# Validation
coverage_90 = results_cqr["coverage"]   # objectif >= 0.90
sharpness   = results_cqr["mean_width"] # intervalle moyen en EUR/t
```

### Adaptive intervals

```python
def adaptive_ci_multiplier(days_to_mars: int, days_to_wasde: int,
                            cot_extreme: bool, ukraine_flag: bool) -> float:
    mult = 1.0
    if days_to_mars <= 7:    mult *= 1.15
    if days_to_wasde <= 5:   mult *= 1.10
    if cot_extreme:          mult *= 1.20
    if ukraine_flag:         mult *= 1.30
    return mult

ci_lo_adj = ci_lo / adaptive_mult
ci_hi_adj = ci_hi * adaptive_mult
```

### Objectifs mesurables

- Couverture IC90% ≥ 90% sur validation OOF 2015–2022
- Couverture par année : aucune année < 85%
- Sharpness < Sharpness(IC constant width)
- Adaptive intervals plus larges avant publications (vérifiable)
- `walk_forward_cqr()` adapté pour target prix absolu EMA

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/meta/cqr.py` | **MODIFIER** — ajouter support target prix absolu |
| `src/mais/modules/module_c.py` | **MODIFIER** — intégrer CQR + adaptive intervals |
| `artefacts/module_c/cqr_calibration_results.json` | Produit |

---

## EXP-MOD-C-03 — Winkler loss + adaptive intervals

**Priorité** : MOYENNE  
**Type** : moyen  
**Statut** : TODO  
**Dépendances** : EXP-MOD-C-02  

### Contexte

Optimiser le trade-off couverture/sharpness via le Winkler score. Comparer IC fixe vs IC adaptatif (proximité événements).

### Tâches

```python
def winkler_score(y_true, lower, upper, alpha=0.10):
    """Winkler interval score : pénalise largeur + pénalise non-couverture."""
    width = upper - lower
    penalty = np.where(
        y_true < lower, 2 / alpha * (lower - y_true),
        np.where(y_true > upper, 2 / alpha * (y_true - upper), 0)
    )
    return np.mean(width + penalty)

# Comparer les trois variantes :
ws_fixed    = winkler_score(y_true, lower_fixed, upper_fixed)
ws_adaptive = winkler_score(y_true, lower_adaptive, upper_adaptive)
ws_cqr      = winkler_score(y_true, lower_cqr, upper_cqr)
```

### Objectifs mesurables

- Winkler score CQR adaptatif < Winkler score IC fixe (sur validation OOF)
- Couverture maintenue ≥ 90% malgré l'optimisation
- Graphique : couverture vs largeur IC pour les 3 variantes

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/modules/module_c.py` | **MODIFIER** — `winkler_score()` + comparaison variantes |
| `artefacts/module_c/winkler_comparison.json` | Produit |

---

## EXP-INT-01 — Stacking augmenté cross-fitted EMA

**Priorité** : MOYENNE  
**Type** : critique  
**Statut** : TODO  
**Dépendances** : EXP-MOD-A-02, EXP-MOD-C-02  

### Contexte

Stacker les prédictions OOF des Modules A, B, C pour obtenir un signal final plus robuste. **Nested walk-forward obligatoire** pour éviter le double leakage sur les méta-features.

### Architecture

```python
# Features de niveau 1 : prédictions OOF des modules
X_meta = {
    "module_a_score":       context_score_oof,          # [-1, +1]
    "module_c_proba_up":    module_c_proba_oof,         # [0, 1]
    "module_b_upside":      risk_card_upside_score_oof,  # [0, 1]
    "module_b_downside":    risk_card_downside_score_oof,# [0, 1]
    "cqr_ci_width":         cqr_ci_width_oof,           # largeur IC (€/t)
    "cbot_ridge_proba":     cbot_ridge_proba_oof,        # proba CBOT (référence)
}

# Méta-modèle
meta_model = LogisticRegression(C=0.1, class_weight="balanced")

# Validation : nested walk-forward
# Train méta-modèle sur prédictions OOF fold_k → tester sur fold_k+1
# JAMAIS entraîner méta-modèle sur les mêmes données que les modèles niveau 0
```

### Objectifs mesurables

- DA stacking > max(DA_module_A, DA_module_C) sur validation OOF
- IC95% da_stacking entièrement > IC95% meilleur module seul
- Nested walk-forward correctement implémenté (0 leakage)

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/modules/stacking_ema.py` | **CRÉER** |
| `artefacts/stacking/stacking_ema_results.json` | Produit |

---

## EXP-INT-02 — Rapport hebdomadaire intégré Euronext

**Priorité** : MOYENNE  
**Type** : complexe  
**Statut** : TODO  
**Dépendances** : EXP-MOD-A-02, EXP-MOD-B-03, EXP-MOD-C-02  

### Contexte

Pipeline automatique du lundi matin : collecter, calculer les 3 modules, générer le rapport Markdown pour l'agriculteur. Remplace et améliore `ops/weekly_report.py` pour la cible Euronext.

### Format du rapport

```markdown
# Maïs Euronext — Semaine du {date}
**Prix actuel** : {ema_close:.2f} €/t | **Variation hebdo** : {pct_change:+.1f}%

## Contexte marché (Module A)
Score : {context_score:+.2f} → **{orientation}**
Driver dominant : {dominant_signal_desc}

| Signal | Score | Niveau actuel |
|---|---|---|
| Bilan mondial | {s1:+.2f} | stocks/usage = {world_su:.2f} |
...

## Carte de risque (Module B)
**Risque baissier** : {downside_score:.0%} | **Opportunité haussière** : {upside_score:.0%}
Règles actives : {active_rules}

## Prévision prix (Module C)
| Horizon | Estimation | IC90% |
|---|---|---|
| 1 mois (+20j) | {price_20:.0f} €/t | [{lo_20:.0f} – {hi_20:.0f} €/t] |
| 3 mois (+60j) | {price_60:.0f} €/t | [{lo_60:.0f} – {hi_60:.0f} €/t] |

## Incertitudes
{uncertainty_codes}

---
*Indicateur Maïs Euronext — couverture IC90% historique : {coverage:.1%}*
*Signal valide si DA hebdomadaire OOF > 0.55. Résultats non garantis.*
```

### Objectifs mesurables

- Pipeline `make weekly-ema` génère le rapport en < 5 minutes
- Rapport cohérent : quand Module A haussier, Module C prédit hausse avec proba > 0.55
- Typed uncertainty automatique (UNCERTAIN_NEAR_MARS, _COT_EXTREME, etc.)
- `pytest tests/test_weekly_report_ema.py` → PASS

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/ops/weekly_report_ema.py` | **CRÉER** |
| `ops/weekly_report_ema.sh` | **CRÉER** |
| `tests/test_weekly_report_ema.py` | **CRÉER** — 8 tests format et contenu |

---

## EXP-INT-03 — Backtest économique Euronext

**Priorité** : HAUTE  
**Type** : complexe  
**Statut** : TODO  
**Dépendances** : EXP-INT-02  

### Contexte

Le seul vrai test de valeur agricole de l'indicateur : combien gagne un agriculteur qui utilise le signal vs un agriculteur qui vend à la récolte (baseline SELL_HARVEST_EU) ?

### Stratégies à comparer

| Stratégie | Description |
|---|---|
| `SELL_HARVEST_EU` | Vendre 100% à la récolte (octobre) |
| `HOLD_MAX_EU` | Vendre au maximum de campagne (oracle, borne supérieure) |
| `MODULE_A_SIGNAL` | Vendre quand Module A > seuil haussier |
| `MODULE_C_PRICE_TARGET` | Vendre quand prix > cible Module C |
| `STACKING_SIGNAL` | Vendre selon signal stacking intégré |
| `MONTHLY_SELL_EU` | Vendre 1/6 par mois oct-mars |

### Protocole

- Période : 8 crop years EU = 2015–2022 (récolte octobre année N → octobre N+1)
- Agriculteur référence : 100 tonnes à stocker après récolte
- Coût stockage : 1.5 €/t/mois (en silo fermier)
- Gain mesuré : prix de vente moyen de la stratégie vs SELL_HARVEST_EU (€/t)
- IC95% (bootstrap sur les 8 années) sur le gain annuel moyen

```python
def simulate_strategy(prices_ema, signal, strategy_name, crop_year_start, crop_year_end):
    """Simuler une stratégie de vente sur une campagne."""
    # Prix de vente selon le signal
    sell_price = select_sell_date(prices_ema, signal, crop_year_start, crop_year_end)
    # Déduire coûts stockage
    storage_months = (sell_date - crop_year_start).days / 30
    net_price = sell_price - storage_months * 1.5
    return net_price

# Baseline
baseline = prices_ema[crop_year_start]  # prix à la récolte
gain_vs_harvest = net_price_strategy - baseline
```

### Objectifs mesurables

- 6 stratégies × 8 crop years EU = tableau 6×8 gains nets (€/t)
- Critère principal : gain moyen > 0 €/t/an pour la meilleure stratégie vs SELL_HARVEST_EU
- IC95% gain moyen entièrement positif → signal économiquement viable
- Proportion d'années gagnantes > 5/8 pour la meilleure stratégie

### Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `src/mais/decision/farmer_backtest_eu.py` | **CRÉER** |
| `artefacts/backtest_eu/farmer_backtest_eu_results.json` | Produit |
| `artefacts/backtest_eu/strategy_comparison_eu.parquet` | Produit |
| `docs/BACKTEST_ECONOMIQUE_EU.md` | Produit — rapport final critère de vérité |

### Vérifications

- [ ] 8 crop years EU couverts (2015–2022)
- [ ] Coûts de stockage déduits
- [ ] IC95% sur gain annuel moyen calculé
- [ ] Comparaison vs HOLD_MAX (mesure de l'alpha accessible)
- [ ] Résultats écrits honnêtement même si gain négatif

---

## Résumé — critères de validation globaux

| Module | Critère principal | Seuil |
|---|---|---|
| EXP-EU-00B | DA EMA h40 (OOF, IC95%) | > 0.55 + pivot décidé |
| EXP-MOD-A | DA hebdomadaire Module A | > 0.55 (IC95% > 0.50) |
| EXP-MOD-A | Cohérence : score haussier → retour 40j positif | > 60% des cas |
| EXP-MOD-B | Support règles validées | ≥ 15 occurrences, IC95% > 0.60 |
| EXP-MOD-C | Couverture IC90% | ≥ 90% sur OOF 2015–2022 |
| EXP-MOD-C | RMSE vs seasonal_naive | RMSE modèle < RMSE baseline |
| EXP-INT | Backtest économique | Gain > 0 €/t/an sur ≥ 5/8 crop years EU |
| Global | IC95% gain moyen backtest | Entièrement > 0 |

> **L'indicateur est fiable quand les trois modules satisfont leurs critères simultanément.**
> Un seul module excellent ne suffit pas.
> UNCERTAIN est une sortie valide — ne jamais forcer un signal quand les données sont insuffisantes.
