# Architecture professionnelle — Indicateur maïs Euronext (EMA)
> Créé le 2026-05-19. Base : vision utilisateur + codebase existante.
> Ce document est la **référence unique** pour la génération des tickets de la Phase EXP.
> Il remplace et complète `.ai/TICKETS_EMA.md` qui reste valide pour les tickets déjà créés.

---

## 0. Problème central résolu

**Avant** : le pipeline dépend d'un téléchargement CSV manuel quotidien sur euronext.com.
→ Fragile, pas scalable, bloque la production.

**Après** : pipeline entièrement automatisé en deux étages :
1. **Backfill historique** (une seule fois) — récupérer le maximum d'historique par contrat.
2. **Collecte quotidienne** — chaque jour après clôture, sans intervention humaine.

---

## 1. Vision et objectif

Ce n'est pas un bot de prédiction. C'est un **système d'intelligence de marché agricole** qui répond à :

| Question | Module |
|---|---|
| Le marché Euronext est-il haussier ou baissier ? | A — Contexte |
| Sur quel horizon ? Avec quelle confiance ? | C — Prédiction |
| Quels facteurs dominent (CBOT, EU, météo, stocks) ? | A + SHAP |
| Le marché rémunère-t-il le stockage 1/3/6 mois ? | B — Stockage |
| Quelle fourchette de prix à H jours ? | C — CQR |
| Quand ne rien faire (incertitude) ? | A — Typed uncertainty |

---

## 2. Architecture globale (flux de données)

```
┌─────────────────────────────────────────────────────────────────────┐
│  SOURCES BRUTES                                                      │
│                                                                      │
│  Euronext EMA (contrats)   CBOT/CME    USDA WASDE/FAS/NASS         │
│  EUR/USD, TTF, BDI         CFTC COT    Météo US + EU               │
│  CONAB Brésil, Ukraine     DCE Dalian  EC MARS, Agreste             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │  collect/ (un module par source)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  RAW LAYER  data/raw/<source>/                                       │
│  Format : JSON (contrats EMA) + CSV/Parquet (tout le reste)         │
│  Règle : jamais écraser, toujours append                             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │  features/euronext_continuous.py
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PROCESSED LAYER  data/processed/euronext/                           │
│  ema_contract_daily.parquet   (tous contrats par jour)               │
│  ema_front_continuous.parquet                                        │
│  ema_most_liquid_continuous.parquet                                  │
│  ema_harvest_nov.parquet                                             │
│  ema_constant_maturity.parquet                                       │
│  ema_curve_features.parquet                                          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │  features/master_dataset.py
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MASTER DATASET  data/processed/features.parquet (étendu)            │
│  EMA curve features + CBOT features + EU fundamentals               │
│  + macro + météo + COT + WASDE + FAS + NASS                         │
│  Anti-leakage : chaque feature date-validée par source_lag          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │  targets.py (étendu)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TARGETS data/processed/targets.parquet (étendu)                     │
│  y_up_h{20,40,60}_ema_most_liquid                                   │
│  y_up_h{40,60}_ema_harvest_nov                                      │
│  y_price_h{20,40,60}_ema (pour CQR)                                 │
│  y_storage_value_{1m,3m,6m}_ema                                     │
│  y_strong_move_h40_ema (>±3%, >±5%)                                 │
└─────────────────────────────┬───────────────────────────────────────┘
                              │  models/ + meta/cqr.py
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PREDICTIONS  data/predictions/                                      │
│  daily/YYYY-MM-DD_ema_signal.json                                   │
│  weekly/YYYY-WXX_ema_report.md + .json                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Accès aux données Euronext — Stratégie réelle

### 3.1 Problème réel

`EMA=F` n'existe pas sur Yahoo Finance. Euronext ne propose pas d'API publique gratuite documentée.

### 3.2 Stratégie en 3 niveaux (implémentation par ordre de priorité)

#### Niveau 1 — Scraping Euronext (quotidien, gratuit)

Euronext publie les prix de settlement dans ses pages web. Son frontend JavaScript effectue des appels API JSON dont les endpoints doivent être **validés via les Network Requests du navigateur** (onglet Réseau / DevTools) avant d'être intégrés dans le collecteur — ils ne doivent pas être considérés comme garantis sans vérification.

```
Endpoint candidat à valider (Network Requests sur euronext.com) :
  URL pattern observé : /en/pd_ajax/fixings?d=DEBA-DEBA&p=0
  ou : /en/pd/data/quote?d=DEBA-DEBA&t=commodity-futures

Paramètres à vérifier :
  d : code produit maïs Matif (à confirmer = DEBA-DEBA ou autre)
  p : page (0 = plus récent, incrémenter pour l'historique)

Validation obligatoire (ticket DATA-EMA-07) :
  1. Comparer 10 lignes récupérées automatiquement vs page Euronext
  2. Vérifier settlement, open, high, low, volume, open_interest existent
  3. Vérifier que le produit récupéré est bien EMA (pas un autre produit DEBA)
  4. Produire euronext_endpoint_validation_report.txt

Output JSON attendu (structure cible, à adapter selon endpoint réel) :
  [{"contract": "EMA Jun26", "expiry": "2026-06-05",
    "settlement": "210.50", "open": "211.00", "high": "211.25",
    "low": "209.75", "volume": "2221", "open_interest": "4448"}]

Backfill :
  Boucler sur pages successives jusqu'à épuisement
  Throttle : 2 secondes minimum entre appels (robots.txt à respecter)
```

**Fallback si l'endpoint principal change ou bloque** : repérer un endpoint alternatif via DevTools avant chaque mise à jour du collecteur. Le collecteur doit inclure un mécanisme de détection d'échec + alerte explicite.

#### Niveau 2 — Barchart API (payant, tier gratuit limité)

```
API endpoint : https://ondemand.websol.barchart.com/getHistory.json
Ticker EMA Matif : CWHZ26 (Nov 2026), CWHU26 (Sep 2026), etc.
Paramètres : apikey, symbol, type=daily, startDate, endDate
Tier gratuit : 60 requêtes/jour, max 1 an historique
```

**Utilisation** : backfill des 12 derniers mois si le scraping Euronext échoue.

#### Niveau 3 — Fichier manuel unique (backfill historique profond)

```
Chemin : data/raw/euronext_ema/manual_backfill/ema_historical_contracts.csv
Format : date,contract_code,expiry_month,expiry_year,open,high,low,settlement,volume,open_interest
Source : 
  - euronext.com > Market Data > Derivatives > Agricultural > Historical Data
  - ou Quandl/NASDAQ Data Link dataset EURONEXT/EMA (si souscrit)
  - ou fichier Barchart CSV téléchargé manuellement une seule fois
Période cible : 2010-01-01 à aujourd'hui
```

**Ce fichier ne se télécharge qu'une fois**. Ensuite, la collecte quotidienne prend le relais.

### 3.3 Contrats EMA (Euronext Matif Corn)

| Code mois | Mois livraison | Liquidité relative |
|---|---|---|
| F | Janvier | ★★ |
| H | Mars | ★★★ |
| M | Juin | ★★★★ |
| Q | Août | ★★★ |
| X | Novembre | ★★★★★ (récolte EU) |

Contrats actifs simultanément : 5 à 8 selon la période de l'année.
Horizon maximum visible : 2 ans environ.

**Test de mapping obligatoire** — à implémenter dans `tests/test_ema_contracts.py` :
```python
def test_contract_month_code_mapping():
    """Si ce test casse, tout le pipeline contrats est faux."""
    assert parse_contract_label("Jun 2026") == "EMA_M2026"
    assert parse_contract_label("Aug 2026") == "EMA_Q2026"
    assert parse_contract_label("Nov 2026") == "EMA_X2026"
    assert parse_contract_label("Mar 2027") == "EMA_H2027"
    assert parse_contract_label("Jan 2027") == "EMA_F2027"
```
Ce test est P0 : il doit passer avant toute autre opération sur les contrats.

---

## 4. Schéma des tables de données

### 4.1 `data/raw/euronext_ema_contracts/YYYY-MM-DD.json`

Snapshot quotidien brut — un fichier JSON par jour.

```json
{
  "date": "2026-05-19",
  "source": "euronext_scraper",
  "collected_at": "2026-05-19T18:05:43Z",
  "contracts": [
    {
      "contract_code": "EMA_M2026",
      "product_code": "EMA",
      "contract_month": 6,
      "contract_year": 2026,
      "expiry_date": "2026-06-05",
      "days_to_expiry": 17,
      "open": 211.00,
      "high": 211.25,
      "low": 209.75,
      "settlement": 210.50,
      "last": 210.50,
      "bid": null,
      "ask": null,
      "volume": 2221,
      "open_interest": 4448,
      "currency": "EUR",
      "unit": "EUR/t",
      "lot_size": 50,
      "quality_flag": "ok"
    }
  ]
}
```

### 4.2 `data/processed/euronext/ema_contract_daily.parquet`

Table maître de tous les contrats, toutes les dates.

| Colonne | Type | Description |
|---|---|---|
| `date` | date | Date du prix |
| `contract_code` | str | `EMA_M2026` |
| `product` | str | `EMA` |
| `contract_month` | int | 1-12 |
| `contract_year` | int | 2024-2028 |
| `expiry_date` | date | Date d'échéance |
| `days_to_expiry` | int | Jours jusqu'à échéance |
| `open` | float | EUR/t |
| `high` | float | EUR/t |
| `low` | float | EUR/t |
| `close` | float | Dernier prix ou settlement |
| `settlement` | float | Prix settlement officiel |
| `volume` | int | Nombre de lots échangés |
| `open_interest` | int | Positions ouvertes |
| `source` | str | `euronext_scraper`, `barchart`, `manual_backfill` |
| `is_proxy` | bool | True si données dérivées CBOT |
| `quality_flag` | str | `ok`, `low_liquidity`, `settlement_missing`, `interpolated` |

**Règle** : on n'écrase jamais une ligne existante avec `is_proxy=False` si `source=euronext_scraper`.
En cas de conflit source réelle > proxy > interpolation.

### 4.3 Séries continues — schéma commun

```
data/processed/euronext/
  ema_front_continuous_raw.parquet       ← prix réels non ajustés (reporting agriculteur)
  ema_front_continuous_adjusted.parquet  ← prix ajustés pour gaps de roll (modèles direction)
  ema_most_liquid_continuous.parquet     ← contrat le plus liquide (OI max)
  ema_harvest_nov.parquet                ← contrat Novembre (jamais back-adjusted)
  ema_constant_maturity_30d.parquet
  ema_constant_maturity_60d.parquet
  ema_constant_maturity_120d.parquet
```

**Règle raw vs adjusted** :
- `raw` = prix affiché sur Euronext, utilisé pour le reporting prix réel à l'agriculteur
- `adjusted` = prix corrigé des gaps de roll (par soustraction du roll_adjustment), utilisé pour les features de rendement et les modèles de direction — évite les faux signaux de hausse/baisse au roll
- `harvest_nov` = **jamais back-adjusted** : on suit le contrat Novembre réel d'une récolte, le prix affiché est le prix réel de marché

| Colonne | Description |
|---|---|
| `date` | Date |
| `price` | Prix EUR/t |
| `contract_code` | Contrat sélectionné ce jour-là |
| `days_to_expiry` | DTE du contrat sélectionné |
| `volume` | Volume du contrat sélectionné |
| `open_interest` | OI du contrat sélectionné |
| `roll_event` | 1 si changement de contrat ce jour |
| `roll_adjustment` | Différence de prix lors du roll |
| `source` | Origine de la donnée |

### 4.4 `data/processed/euronext/ema_curve_features.parquet`

Features de courbe calculées quotidiennement.

| Feature | Formule | Interprétation |
|---|---|---|
| `ema_front_price` | Prix contrat front | Niveau marché immédiat |
| `ema_second_price` | Prix 2e contrat actif | |
| `ema_harvest_nov_price` | Prix contrat Nov (récolte) | Signal récolte |
| `ema_next_march_price` | Prix contrat Mar suivant | Signal stockage hiver |
| `ema_front_second_spread` | front - second | Backwardation front |
| `ema_nov_mar_spread` | Nov - Mar suivant | Structure saisonnière |
| `ema_aug_nov_spread` | Août - Nov | Prime livraison récolte |
| `ema_curve_slope_3m` | (price_90d - price_0d) / 90 | Pente courbe |
| `ema_curve_slope_6m` | (price_180d - price_0d) / 180 | Pente moyen terme |
| `ema_contango_flag` | 1 si slope > 0 | Marché en contango |
| `ema_backwardation_flag` | 1 si slope < 0 | Marché en backwardation |
| `ema_carry_1m` | (price_30d - price_0d) / price_0d | Portage 1 mois |
| `ema_roll_yield_ann` | carry_1m × 12 | Roll yield annualisé |
| `ema_oi_total` | Somme OI tous contrats | Engagement total marché |
| `ema_volume_total` | Somme volumes | Activité totale |
| `ema_oi_concentration` | OI(front) / OI(total) | Concentration positions |
| `ema_liquidity_shift` | ΔOI(front) 5j | Migration positions |
| `cbot_eur_t` | CBOT_cents/100 / EURUSD × 39.3679 | Prix CBOT en EUR/t |
| `ema_cbot_basis` | ema_front - cbot_eur_t | Prime européenne |
| `ema_cbot_basis_zscore_52w` | z-score expanding(basis, 52w) | Basis normalisé |
| `ema_cbot_rel_strength_20d` | (ema/ema_20d) - (cbot/cbot_20d) | Force relative |

### 4.5 Cibles agricoles — extensions de `targets.parquet`

| Cible | Formule | Question métier |
|---|---|---|
| `y_up_h20_ema` | close_t+20 > close_t | EMA monte en 1 mois ? |
| `y_up_h40_ema` | close_t+40 > close_t | EMA monte en 2 mois ? |
| `y_up_h60_ema` | close_t+60 > close_t | EMA monte en 3 mois ? |
| `y_up_h20_ema_harvest` | nov_t+20 > nov_t | Prix récolte monte ? |
| `y_up_h40_ema_harvest` | nov_t+40 > nov_t | Prix récolte monte (2m) ? |
| `y_up_gt3pct_h40_ema` | log(t+40/t) > 0.03 | Forte hausse probable ? |
| `y_down_gt3pct_h40_ema` | log(t+40/t) < -0.03 | Forte baisse probable ? |
| `y_price_h20_ema` | close_t+20 (absolu, pour CQR) | Prix dans 1 mois |
| `y_price_h60_ema` | close_t+60 (absolu, pour CQR) | Prix dans 3 mois |
| `y_storage_value_1m` | price_t+20 - price_t - cost_1m | Stocker 1m rentable ? |
| `y_storage_value_3m` | price_t+60 - price_t - cost_3m | Stocker 3m rentable ? |
| `y_storage_value_6m` | price_t+120 - price_t - cost_6m | Stocker 6m rentable ? |
| `y_storage_profit_3m` | y_storage_value_3m > 0 (binaire) | Décision stockage |

**Coûts de stockage de référence** (EUR/tonne/mois) :
```
cost_1m  ≈ 1.5 €/t/mois  (stockage à la ferme)
cost_3m  ≈ 4.5 €/t       (3 mois, frais fixes inclus)
cost_6m  ≈ 9.0 €/t       (6 mois, risque qualité)
Paramétrisables dans config/decision.yaml
```

---

## 5. Anti-leakage — Matrice de disponibilité par source

Chaque source a une date de disponibilité réelle. Le pipeline doit implémenter `feature_available_date(source, publish_date)` — pas seulement `shift(1)` partout.

| Source | Fréquence | Jour publication | Disponible le | Décalage réel |
|---|---|---|---|---|
| `euronext_settlement` | Quotidien | J, après 18h | J+1 matin | +1 jour |
| `cbot_corn` | Quotidien | J, après 15h CT | J+1 matin | +1 jour |
| `eurusd_rate` | Quotidien | J, intraday | J même soir | +0 (si après clôture) |
| `ttf_natgas` | Quotidien | J, après clôture | J+1 matin | +1 jour |
| `cftc_cot` | Hebdomadaire | Vendredi 15h30 ET | Lundi | +3 jours calendaires |
| `usda_wasde` | Mensuel | ~12 du mois 12h ET | Même jour après 18h | +0 (post-publication) |
| `usda_fas_export_sales` | Hebdomadaire | Jeudi 8h30 ET | Jeudi même | +0 (post-publication) |
| `usda_nass_crop_progress` | Hebdomadaire (mai-oct) | Lundi 16h ET | Lundi soir | +0 (post-publication) |
| `openmeteo_states` | Quotidien | J, temps réel | J même | +0 |
| `us_drought_monitor` | Hebdomadaire | Jeudi | Jeudi | +0 |
| `enso_oni` | Mensuel | ~15 du mois | ~15 du mois | +0 |
| `ec_mars_bulletin` | Mensuel | ~15 du mois | ~15 du mois | +1 mois shift sécurité |
| `agreste_france` | Hebdomadaire | Lundi | Lundi | +1 semaine shift |
| `franceagrimer` | Mensuel | ~10 du mois | ~10 du mois | +1 mois shift |
| `conab_brazil` | Mensuel | ~8 du mois | ~8 du mois | +1 mois shift |
| `dce_dalian` | Quotidien | J, après clôture | J+1 matin | +1 jour |

**Implémentation** :
```python
# src/mais/leakage/availability.py (nouveau fichier)
SOURCE_AVAILABILITY: dict[str, dict] = {
    "euronext_settlement": {"lag_days": 1, "same_day_after": "18:00 CET"},
    "cbot_corn":           {"lag_days": 1, "same_day_after": "15:00 CT"},
    "cftc_cot":            {"lag_days": 3, "publication_day": "friday"},
    "usda_wasde":          {"lag_days": 0, "same_day_after": "18:00 ET", "frequency": "monthly"},
    # etc.
}
```

**Règle** : pour toute feature fondamentale (WASDE, COT, MARS, Agreste), on applique
`shift(1)` minimum + vérification calendrier de publication.

---

## 6. Modules Python à créer/modifier

### 6.1 Nouveaux collecteurs

```
src/mais/collect/
  euronext_contracts_daily.py   ← NOUVEAU — scraping contrats EMA (remplace euronext_ema_collector.py)
  euronext_backfill.py          ← NOUVEAU — backfill historique par contrat
  data_quality.py               ← NOUVEAU — rapport qualité quotidien
```

#### `euronext_contracts_daily.py` — interface minimale

```python
def download_active_contracts(date: datetime.date) -> list[dict]:
    """Récupère tous les contrats EMA actifs pour une date donnée.
    Sources par priorité : scraping euronext > barchart > proxy CBOT.
    Retourne une liste de dicts conformes au schéma §4.1."""

def download_settlement_history(contract_code: str, from_date: date, to_date: date) -> pd.DataFrame:
    """Historique settlement pour un contrat donné."""

def save_daily_snapshot(date: datetime.date, contracts: list[dict]) -> Path:
    """Sauvegarde JSON dans data/raw/euronext_ema_contracts/YYYY-MM-DD.json."""
```

#### `euronext_backfill.py` — interface minimale

```python
def backfill_from_manual(csv_path: Path) -> int:
    """Charge le CSV manuel et alimente ema_contract_daily.parquet."""

def backfill_from_scraper(from_date: date, to_date: date, throttle_sec: float = 2.0) -> int:
    """Boucle de backfill via scraping Euronext. Respecte throttle."""

def load_manual_backfill_if_exists() -> pd.DataFrame | None:
    """Cherche data/raw/euronext_ema/manual_backfill/ema_historical_contracts.csv."""
```

### 6.2 Nouveaux modules features

```
src/mais/features/
  euronext_continuous.py   ← NOUVEAU — séries continues EMA
  euronext_curve.py        ← NOUVEAU — features de courbe EMA
  ema_targets.py           ← NOUVEAU — cibles agricoles EMA
  storage_features.py      ← NOUVEAU — features de décision stockage
  leakage_calendar.py      ← NOUVEAU — validateur date disponibilité
```

#### `euronext_continuous.py` — fonctions clés

```python
def build_front_continuous(contracts: pd.DataFrame, min_dte: int = 5, min_volume: int = 0) -> pd.DataFrame:
    """Série front continue avec gestion des rolls."""

def build_most_liquid(contracts: pd.DataFrame) -> pd.DataFrame:
    """Série contrat le plus liquide (max OI ou volume)."""

def build_harvest_november(contracts: pd.DataFrame) -> pd.DataFrame:
    """Série suivi contrat Novembre (récolte EU) campagne par campagne."""

def build_constant_maturity(contracts: pd.DataFrame, target_dte: int) -> pd.DataFrame:
    """Interpolation entre deux contrats pour une maturité constante."""

def detect_rolls(series: pd.DataFrame) -> pd.DataFrame:
    """Identifie les dates de roll et le gap de prix."""
```

#### `euronext_curve.py` — fonctions clés

```python
def build_curve_features(contracts: pd.DataFrame, cbot: pd.DataFrame, eurusd: pd.DataFrame) -> pd.DataFrame:
    """Calcule les 18 features de courbe du §4.4.
    Anti-leakage : toutes les features sont shift(1) (settlement J-1 disponible J).
    """

def compute_basis(ema_price: float, cbot_cents_bu: float, eurusd: float) -> float:
    """basis = ema - (cbot/100/eurusd*39.3679)."""
```

### 6.3 Modifications modules existants

| Fichier | Modification |
|---|---|
| `src/mais/paths.py` | Ajouter `EMA_CONTRACTS_RAW_DIR`, `EMA_PROCESSED_DIR`, `PREDICTIONS_DIR` |
| `src/mais/collect/__init__.py` | Remplacer `euronext_ema_collector` par `euronext_contracts_daily` |
| `src/mais/targets.py` | Ajouter les 13 cibles EMA du §4.5 |
| `src/mais/features/__init__.py` | Brancher `euronext_continuous` + `euronext_curve` dans `build_features()` |
| `src/mais/ops/daily.py` | Ajouter step `build_ema_dataset` dans le pipeline quotidien |
| `src/mais/cli.py` | Ajouter commandes `backfill`, `build-ema-dataset`, `predict-ema`, `report-weekly` |
| `config/sources.yaml` | Remplacer `euronext_ema` par `euronext_ema_daily` + `euronext_ema_backfill` |
| `config/decision.yaml` | Ajouter paramètres storage_costs, confidence_thresholds |

---

## 7. Pipeline quotidien — Orchestration exacte

### 7.1 Commandes CLI cibles

```bash
# Collecte (après clôture Euronext, ~18h CET)
python -m mais.cli collect source euronext_ema_daily   # contrats actifs
python -m mais.cli collect source eu_cross_assets      # EUR/USD, TTF
python -m mais.cli collect source cbot_corn            # CBOT
python -m mais.cli collect all                         # toutes sources actives

# Dataset (après collecte)
python -m mais.cli build-ema-dataset                   # continuous + curve + master

# Prédictions
python -m mais.cli predict-ema                         # signal + prix + stockage

# Rapport (quotidien léger ou hebdomadaire complet)
python -m mais.cli report daily
python -m mais.cli report weekly   # seulement le lundi

# Backfill (une seule fois ou si manque)
python -m mais.cli backfill euronext --from 2014-01-01
```

### 7.2 Ordre d'exécution quotidien

```
18:05 CET  collect euronext_ema_daily      # settlement J disponible
18:10 CET  collect eu_cross_assets         # EUR/USD, TTF
18:15 CET  collect cbot_corn               # CBOT close
18:20 CET  collect [macro, cot si J=vendr, wasde si J=pub]
18:30 CET  build-ema-dataset               # continuous + curve + features
18:45 CET  predict-ema                     # signal JSON
19:00 CET  report daily                    # rapport léger (si lundi: rapport complet)
```

### 7.3 Cron entries

```cron
# Quotidien (lun-ven), après clôture Euronext
5 18 * * 1-5  cd /home/cytech/Desktop/Etude\ Mais && venv/bin/python -m mais.cli daily-run --collect >> logs/cron_daily.log 2>&1

# Rapport hebdomadaire (lundi 6h, avant ouverture)
0 6 * * 1  cd /home/cytech/Desktop/Etude\ Mais && venv/bin/python -m mais.cli report weekly >> logs/cron_weekly.log 2>&1
```

---

## 8. Rapport qualité quotidien (Data Quality Check)

Chaque exécution quotidienne doit produire `data/reports/YYYY-MM-DD_quality.json`.

```json
{
  "date": "2026-05-19",
  "euronext": {
    "contracts_found": 7,
    "front_contract": "EMA_Q2026",
    "most_liquid_contract": "EMA_Q2026",
    "harvest_contract": "EMA_X2026",
    "missing_settlement": 0,
    "missing_open_interest": 1,
    "abnormal_move_pct": null,
    "source": "euronext_scraper",
    "is_proxy": false
  },
  "cbot": {"updated": true, "last_date": "2026-05-19"},
  "eurusd": {"updated": true, "last_date": "2026-05-19"},
  "wasde": {"latest": "2026-05-12", "days_since": 7},
  "cot": {"latest": "2026-05-15", "days_since": 4},
  "fas": {"latest": "2026-05-15", "days_since": 4},
  "data_availability_score": 0.91,
  "signal_status": "ok",
  "uncertainty_flags": []
}
```

Si `data_availability_score < 0.70` → signal = `UNCERTAIN_DATA_MISSING`.
Si `is_proxy = true` → avertissement dans rapport, modèle EMA non lancé.

---

## 9. Typed uncertainty — Codes complets

| Code | Condition | Comportement |
|---|---|---|
| `NEAR_WASDE` | Publication WASDE dans ≤ 5 jours | Signal affiché + avertissement |
| `NEAR_MARS` | Publication MARS dans ≤ 5 jours | Signal affiché + avertissement |
| `COT_EXTREME` | COT percentile > 90 ou < 10 | Avertissement retournement |
| `UKRAINE_RISK` | Indicateur corridor Ukraine modifié | Avertissement géopolitique |
| `DISAGREEMENT` | Désaccord modèles horizons > seuil | UNCERTAIN |
| `DATA_MISSING` | data_availability_score < 0.70 | UNCERTAIN, pas de signal |
| `LOW_LIQUIDITY` | OI contrat front < 500 | Avertissement technique |
| `PROXY_DATA` | EMA est un proxy CBOT | Avertissement, pas de signal EMA |

---

## 10. Séries continues — Règles de construction

### 10.1 Front continuous

```
Sélection chaque jour :
  contract = argmin(days_to_expiry, where days_to_expiry > 5 AND volume > 0)
  
  Si days_to_expiry <= 5 :
    → roll vers contrat suivant
    → enregistrer roll_event = True, roll_adjustment = new_price - old_price
  
  Qualité :
    Si volume == 0 ET open_interest < 100 → flag low_liquidity
    Si settlement manquant → utiliser last, flag settlement_missing
```

### 10.2 Most liquid

```
Sélection chaque jour :
  contract = argmax(open_interest)  # ou volume si OI non disponible
  
  Ce contrat peut changer d'une semaine à l'autre sans roll forcé.
  On garde track de la migration via ema_liquidity_shift.
```

### 10.3 Harvest November

```
Sélection du contrat Novembre pour une date t :

  expiry_nov_current = expiry du contrat EMA_X{année(t)}

  if t < expiry_nov_current - 5j :
    harvest_contract = EMA_X{année(t)}       # Nov de l'année en cours
  else :
    harvest_contract = EMA_X{année(t) + 1}   # Nov de l'année suivante

Exemples :
  Mai 2026      → EMA_X2026   (Nov 2026 pas encore expiré)
  Décembre 2026 → EMA_X2027   (Nov 2026 expiré début nov)
  Août 2026     → EMA_X2026   (récolte EU en cours)

Règles supplémentaires :
  - Jamais back-adjusted (prix réel de marché)
  - Si EMA_X de l'année en cours n'existe pas encore (> 18 mois avant) :
    utiliser EMA_X de l'année suivante avec flag future_contract = True
  - Enregistrer la date de transition campagne dans roll_log

Importance :
  - Principal contrat de couverture agriculteurs EU
  - Reflète le consensus marché sur la récolte future
  - Spread Nov-Mar = signal stockage hiver
  - Cible agricole principale : y_up_h40_ema_harvest_nov
```

### 10.4 Constant maturity (60d exemple)

```
Chaque jour, identifier les deux contrats encadrant 60 jours :
  contract_A : DTE = 45j (exemple)
  contract_B : DTE = 75j (exemple)
  
  weight_A = (75 - 60) / (75 - 45) = 0.50
  weight_B = (60 - 45) / (75 - 45) = 0.50
  
  price_60d = weight_A × price_A + weight_B × price_B
```

---

## 11. Modèles — Stratégie

### 11.1 Familles de modèles par cible

| Famille cible | Modèles | Métrique principale |
|---|---|---|
| Direction (classification) | RidgeClassifier, HistGBT, LightGBM, LogisticReg | DA OOF + AUC + IC95% bootstrap |
| Prix absolu (régression) | Ridge, ElasticNet, HistGBT, LightGBM | RMSE €/t + coverage IC90% |
| Intervalle prix (CQR) | LightGBM + conformal quantile | Winkler loss + coverage |
| Stockage (binaire) | LogisticReg, HistGBT | DA + gain net €/t |
| Confiance P(correct) | LogisticReg calibrée Platt | ECE + Brier |

### 11.2 Protocole walk-forward

```
Min train      : 3 ans (756 jours)
Step           : ~6 mois (126 jours)
Min n_splits   : 8
Référence      : 2014-01-01 → 2025-12-31 si données disponibles

NB : le backtest modèle ne démarre qu'à la date de disponibilité
réelle des vraies données EMA (pas du proxy CBOT).
```

### 11.3 Feature selection obligatoire

**Ne pas utiliser toutes les 289 features sans sélection** (résultat DA=0.46 observé).

```
Pipeline sélection :
  1. Correlation > 0.95 → drop une des deux (à conserver : celle avec moins de NaN)
  2. NaN rate > 60% sur la période train → drop
  3. Importance SHAP ← HistGBT first pass
  4. Garder top-50 features SHAP dans un premier temps
  5. Ablation par famille (CBOT, EMA curve, EU, COT, météo, macro)
```

---

## 12. Métriques finales

### 12.1 Direction

```
DA OOF              = accuracy directionnelle hors-échantillon
AUC OOF             = discrimination
DA IC95% bootstrap  = intervalle de confiance (1000 draws)
DA top-20%          = DA sur les 20% de signaux les plus confiants
DA hebdomadaire     = 1 point par lundi (référence agricole)
DA par année        = stabilité inter-années (cible : stable 2015-2025)
Benjamini-Hochberg  = correction tests multiples (comparaisons inter-features)
```

### 12.2 Prix / CQR

```
MAE €/t             = erreur absolue moyenne
RMSE €/t            = erreur quadratique moyenne
Coverage IC90%      ≥ 90% (objectif calibration)
Largeur IC90% €/t   = sharpness
Winkler loss        = métrique unifiée coverage + sharpness
Baseline            = random_walk (prix_t+H = prix_t)
```

### 12.3 Stockage

```
Gain net €/t/an     = (signal positif AND stock profitable) - coût décision
% années gagnantes  = sur les 8+ backtest folds
Regret moyen €/t    = gain manqué vs oracle
Pire année €/t      = risque maximal
Drawdown décisionnel = perte max sur une période continue
```

### 12.4 Production système

```
Nombre signaux/an   = activité (objectif : ≥ 40/an)
% UNCERTAIN         = indisponibilité (objectif : < 30%)
data_availability   = score qualité données (objectif : > 0.85)
Latence collecte    = temps entre clôture EMA et signal disponible (objectif : < 2h)
Taux échec coll.    = % de jours avec collecte en erreur (objectif : < 5%)
```

---

## 13. Structure des rapports

### 13.1 Signal quotidien JSON

```
data/predictions/daily/YYYY-MM-DD_ema_signal.json

{
  "date": "2026-05-19",
  "ema_front_price": 210.50,
  "ema_harvest_nov_price": 205.25,
  
  "direction_h20": {"signal": "HAUSSIER", "prob_up": 0.61, "confidence": 0.72},
  "direction_h40": {"signal": "NEUTRE",   "prob_up": 0.53, "confidence": 0.48},
  
  "price_forecast_h60": {
    "point_estimate": 218.5,
    "ci90_low": 198.0,
    "ci90_high": 242.0,
    "winkler_score": null
  },
  
  "storage": {
    "store_1m_expected_gain": 2.4,
    "store_3m_expected_gain": -1.2,
    "store_3m_signal": "VENDRE",
    "store_3m_confidence": 0.65
  },
  
  "top_factors_bullish":  ["wasde_stocks_surprise_neg", "cot_managed_low", "eur_weak"],
  "top_factors_bearish":  ["brazil_record_harvest", "eu_crop_good"],
  
  "uncertainty_flags": [],
  "data_quality_score": 0.91,
  "is_proxy_data": false,
  "generated_at": "2026-05-19T18:52:00Z"
}
```

### 13.2 Rapport hebdomadaire Markdown (lundi)

```
data/reports/weekly/YYYY-WXX_mais_euronext.md

# Rapport hebdomadaire maïs Euronext — Semaine XX/YYYY

## Prix Euronext (EMA)
- Contrat front (Jun 2026) : 210.50 €/t  (+1.2% vs semaine précédente)
- Contrat récolte (Nov 2026) : 205.25 €/t
- Structure courbe : CONTANGO (Nov < Mar = stockage rémunéré)
- Basis vs CBOT : -5.2 €/t (dans la norme)

## Orientation marché
NEUTRE → légèrement HAUSSIER sur 40 jours
Score contexte : +0.21

Facteurs haussiers :
  ↑ Révision WASDE : stocks mondiaux révisés à la baisse (-3.5 Mt)
  ↑ Brésil : safrinha en retard (GE% 68%, -5pts vs moyenne)
  ↑ COT : fonds managed-money à position neutre (percentile 38%)

Facteurs baissiers :
  ↓ Récolte EU : conditions bonnes (MARS +2pts)
  ↓ Brésil : record export en cours

## Prévision de prix
Horizon 60 jours : 218 €/t [IC90% : 198-242]

## Décision stockage
Stocker 1 mois : NEUTRE (gain attendu +2.4 €/t vs coût 1.5 €/t)
Stocker 3 mois : VENDRE (gain attendu -1.2 €/t < coût 4.5 €/t)

## Alertes
⚠ WASDE publication dans 7 jours (2026-05-26 12h ET)
→ Prévoir volatilité accrue

## Données disponibles
Euronext : OK (7 contrats actifs, source: euronext_scraper)
Data quality score : 0.91
```

---

## 14. Index des tickets à créer

Les tickets seront créés dans `.ai/TICKETS_EMA.md` (section nouvelle) en remplaçant les stubs existants.

### Sprint INFRA (avant tout modèle)

| ID | Titre | Type | Bloqué par |
|---|---|---|---|
| `DATA-PATHS-01` | Extension paths.py + dirs EMA (EMA_CONTRACTS_RAW_DIR, etc.) | simple | — |
| `DATA-EMA-07` | Validation endpoint Euronext (avant scraping en masse) | moyen | — |
| `DATA-EMA-01` | Collecteur quotidien Euronext (scraping contrats actifs) | critique | DATA-EMA-07 |
| `DATA-EMA-02` | Backfill historique EMA par contrat | complexe | DATA-EMA-01 |
| `DATA-EMA-03` | Séries continues (front_raw, front_adj, most_liquid, harvest_nov, constant_maturity) | complexe | DATA-EMA-02 |
| `DATA-EMA-08` | Roll audit (dates roll, gaps prix, anti-leakage targets) | moyen | DATA-EMA-03 |
| `DATA-EMA-04` | Features courbe Euronext (18 features §4.4) | complexe | DATA-EMA-03 |
| `DATA-EMA-05` | Rapport qualité quotidien (data_quality.py + JSON) | moyen | DATA-EMA-01 |
| `DATA-EMA-06` | Anti-leakage calendrier (leakage_calendar.py) | moyen | — |
| `DATA-MASTER-01` | Dataset master EMA+CBOT (build_features étendu) | complexe | DATA-EMA-04 |
| `DATA-TARGETS-01` | Cibles agricoles EMA (13 cibles §4.5) | moyen | DATA-EMA-03 |

### Sprint BENCHMARK

| ID | Titre | Type | Bloqué par |
|---|---|---|---|
| `EXP-BENCH-01` | Feature selection (drop NaN >60%, correlation, SHAP top-50) | moyen | DATA-MASTER-01 |
| `VAL-EMA-01` | Proxy vs vraie EMA (corrélation, spread, périodes inutilisables) | moyen | DATA-EMA-02 |
| `EXP-BENCH-02` | Benchmark EMA vs CBOT (vrais prix) — EXP-EU-00B complet | critique | VAL-EMA-01, EXP-BENCH-01 |
| `VAL-EMA-02` | Benchmark hebdomadaire DA/AUC/stockage (1 point/semaine) | moyen | EXP-BENCH-02 |
| `EXP-BENCH-03` | Ablation features EMA curve (delta DA par famille) | moyen | EXP-BENCH-02 |
| `EXP-BENCH-04` | Benchmark cible stockage (y_storage_profit_3m) | moyen | DATA-TARGETS-01, EXP-BENCH-01 |

### Sprint MODÈLES

| ID | Titre | Type | Bloqué par |
|---|---|---|---|
| `MODEL-DIR-01` | Modèle direction EMA (walk-forward multi-modèles) | complexe | EXP-BENCH-02 |
| `MODEL-CQR-01` | CQR prix absolu EMA (adaptation mais.meta.cqr) | complexe | EXP-BENCH-02 |
| `MODEL-STOR-01` | Modèle décision stockage (P(storage profitable)) | complexe | DATA-TARGETS-01 |
| `MODEL-CONF-01` | Confiance P(correct) adapté EMA | moyen | MODEL-DIR-01 |
| `MODEL-STACK-01` | Stacking augmenté cross-fitted EMA | critique | MODEL-DIR-01, MODEL-CQR-01 |

### Sprint MODULES A/B/C

| ID | Titre | Type | Bloqué par |
|---|---|---|---|
| `MOD-A-01` | Module A: 12 signaux contexte scorés (§6 REFLEXION) | complexe | DATA-MASTER-01 |
| `MOD-A-02` | Module A: calibration OOF + poids | complexe | MOD-A-01 |
| `MOD-B-01` | Module B: étude événementielle grandes variations EMA | complexe | EXP-BENCH-02 |
| `MOD-B-02` | Module B: règles lisibles + carte risque | moyen | MOD-B-01 |
| `MOD-C-01` | Module C: prédiction prix EMA avec IC90% CQR | critique | MODEL-CQR-01 |

### Sprint OPS/RAPPORT

| ID | Titre | Type | Bloqué par |
|---|---|---|---|
| `OPS-DAILY-01` | Pipeline quotidien EMA (daily.py étendu) | complexe | MODEL-DIR-01, MODEL-CQR-01 |
| `OPS-REPORT-01` | Rapport hebdomadaire agriculteur EMA (§13.2) | complexe | OPS-DAILY-01 |
| `OPS-CRON-01` | Automatisation cron/systemd (2 jobs §7.3) | simple | OPS-DAILY-01 |
| `OPS-CLI-01` | Extension CLI (backfill, build-ema-dataset, predict-ema, report) | moyen | DATA-MASTER-01 |

### Sprint VALIDATION FINALE

| ID | Titre | Type | Bloqué par |
|---|---|---|---|
| `VAL-BACKTEST-01` | Backtest économique complet EMA (2014-2024) | critique | OPS-DAILY-01 |
| `VAL-REPORT-01` | Rapport étude final Euronext (mise à jour PROFESSIONAL_STUDY_REPORT) | moyen | VAL-BACKTEST-01 |

---

## 15. Ordre d'exécution recommandé

```
Phase 0 — Infrastructure (1-2 jours)
  DATA-PATHS-01 → DATA-EMA-07 → DATA-EMA-01 → DATA-EMA-05 → DATA-EMA-06

Phase 1 — Données historiques (2-3 jours)
  DATA-EMA-02 → DATA-EMA-03 → DATA-EMA-08 → DATA-EMA-04 → DATA-TARGETS-01 → DATA-MASTER-01

Phase 2 — Benchmark (1-2 jours)
  EXP-BENCH-01 → VAL-EMA-01 → EXP-BENCH-02 → VAL-EMA-02 → EXP-BENCH-03 → EXP-BENCH-04
  DÉCISION GO/NO-GO sur la base de EXP-BENCH-02 (critères §16 go/no-go minimal)

Phase 3 — Modèles (3-5 jours)
  MODEL-DIR-01 → MODEL-CQR-01 → MODEL-STOR-01 → MODEL-CONF-01 → MODEL-STACK-01

Phase 4 — Modules A/B/C (3-4 jours)
  MOD-A-01 → MOD-A-02 (parallèle avec MOD-B-01 → MOD-B-02)
  MOD-C-01

Phase 5 — Ops + Rapport (2-3 jours)
  OPS-CLI-01 → OPS-DAILY-01 → OPS-REPORT-01 → OPS-CRON-01

Phase 6 — Validation (1-2 jours)
  VAL-BACKTEST-01 → VAL-REPORT-01
```

---

## 16. Critères de succès globaux

### Go/no-go minimal (Phase 2 → Phase 3)

| Critère | Seuil | Bloquant |
|---|---|---|
| DA OOF EMA h20 moyenne > 0.55 | > 0.55 | OUI |
| AUC OOF EMA h20 > 0.55 | > 0.55 | OUI |
| IC95% bootstrap non catastrophique (lo > 0.50) | > 0.50 | OUI |
| DA top-20% > 0.62 | > 0.62 | OUI |
| Stabilité inter-annuelle (std split DAs < 0.10) | < 0.10 | OUI |
| EMA proxy remplacé par données réelles | 100% | OUI (avant Phase 3) |

_Rationnel_ : DA=0.58 avec IC95=[0.545;0.615] est un vrai signal malgré IC95_lo < 0.55. Ne pas tuer une piste prometteuse avec un critère trop strict.

### Critère professionnel (validation finale)

| Critère | Seuil | Bloquant |
|---|---|---|
| DA OOF EMA h40 IC95% lo > 0.55 | > 0.55 | OUI (validation finale) |
| DA top-20% > 0.68 | > 0.68 | OUI |
| Coverage IC90% CQR ≥ 88% | ≥ 88% | OUI |
| Gain stockage €/t/an > 0 sur ≥ 6/8 années | > 0 | OUI |
| Latence collecte → signal < 2h | < 2h | NON |
| data_availability_score > 0.85 | > 0.85 | NON |
| Signal UNCERTAIN < 30% des jours | < 30% | NON |

---

## 17. Dépendance critique : obtenir les vrais prix EMA

**Avant de lancer Phase 2 (benchmark), il faut des vrais prix EMA.**

Options par ordre de praticité :

1. **Téléchargement manuel une seule fois** (urgent, avant tickets Phase 1) :
   - euronext.com > Products > Derivatives > Agricultural > Corn (Maïs Rendu Rouen)
   - Télécharger l'historique disponible (format CSV ou Excel)
   - Sauvegarder dans `data/raw/euronext_ema/manual_backfill/ema_historical_contracts.csv`
   - **Estimation** : 30 minutes, débloque tout le reste

2. **Scraping automatique `DATA-EMA-01`** (premier ticket INFRA) :
   - Implémente le collecteur qui le fait quotidiennement
   - Mais aussi le backfill depuis 2014

3. **Barchart API** (si scraping Euronext bloqué) :
   - Clé API gratuite sur barchart.com
   - Tickers EMA : `CWHZ26` (Nov), `CWHU26` (Aug), `CWHM26` (Jun), etc.

> **Recommandation** : Télécharger le fichier historique manuellement **maintenant** (30 min)
> pour débloquer EXP-BENCH-02 sans attendre DATA-EMA-01/02.
> Ensuite, DATA-EMA-01 assure la collecte quotidienne automatique.
