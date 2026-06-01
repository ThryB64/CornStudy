# Réflexion — Sélection des contrats EMA et construction des séries

> Créé le 2026-05-19. Corrigé le 2026-05-20 (statuts tickets, mois historiques, dépendances source).
> Document de conception, pas un ticket.
> Objectif : formaliser la logique de sélection des contrats Euronext EMA avant implémentation.

---

## 1. Le problème fondamental

La question centrale n'est pas "quels 6 mois calendaires prochains ?" mais :

> **Quelles sont les prochaines échéances EMA réellement cotées et liquides sur le marché ?**

Euronext Matif maïs (EMA) ne cote pas un contrat par mois. Les **mois de livraison officiels actuels** du contrat Corn Futures EMA sont :

| Code mois | Lettre | Signification agronomique |
|---|---|---|
| Mars | H | fin campagne mondiale, stocks vieux |
| Juin | M | nouvelle récolte US en vue |
| Août | Q | pic tension pré-récolte EU |
| Novembre | X | contrat récolte EU principal |

**Correction C1 : le pipeline courant ne doit jamais générer Janvier (F).**  
Les seules lettres valides pour les contrats EMA actifs récupérés aujourd'hui sont **H, M, Q, X**. En revanche, certaines sources historiques tierces (notamment Barchart) affichent des symboles `XBF..`. Ces contrats doivent être classés `legacy_or_ambiguous` tant qu'une table de référence officielle ne confirme pas qu'ils étaient réellement cotés pour l'année concernée. Ils ne doivent pas entrer dans les séries finales par défaut.

Euronext indique que jusqu'à **dix mois de livraison** peuvent être disponibles au trading simultanément. En pratique, selon la source de données utilisée, on récupérera un nombre variable de contrats (souvent 4 à 8). L'algorithme doit accepter moins de 6 contrats et remplir avec NaN — il ne faut jamais forcer artificiellement 6 rangs.

---

## 2. Table de référence des contrats (prérequis absolu)

**Avant de construire les séries, il faut une table de référence :**

```
data/processed/euronext/ema_contract_reference.parquet
```

| Colonne | Type | Description |
|---|---|---|
| `contract_code` | str | ex. `EMA_H2026` |
| `month_code` | str | H / M / Q / X |
| `delivery_month` | int | 3=mars, 6=juin, 8=août, 11=novembre |
| `delivery_year` | int | ex. 2026 |
| `expiry_date` | date | date exacte d'expiration (source Euronext officielle) |
| `last_trade_date` | date | dernier jour de négociation |
| `first_trade_date` | date | premier jour de négociation (si disponible) |
| `isin` | str | identifiant ISIN (si disponible) |
| `amr_code` | str | code Euronext AMR (si disponible) |
| `source` | str | euronext_web / barchart / manual |
| `source_symbol` | str | symbole brut fournisseur, ex. `XBQ10` |
| `import_verdict` | str | usable / legacy_or_ambiguous / do_not_import |
| `active_month_status` | str | current_official / historical_confirmed / legacy_or_ambiguous |

**Sans cette table, les dates d'expiration sont des estimations. Il ne faut pas deviner.**  
C'est la fondation de toute la logique de sélection des contrats.

---

## 3. Règle de sélection : jusqu'à 6 contrats (courbe quotidienne)

**Chaque jour, l'algorithme :**

1. Récupère tous les contrats EMA cotés ce jour-là (depuis `ema_contract_daily`)
2. Exclut les contrats avec `days_to_expiry <= 15` (spreads erratiques, liquidation proche)
3. Exclut les contrats avec `month_code` non valide pour le pipeline courant (`H`, `M`, `Q`, `X`), sauf si `active_month_status = historical_confirmed`
4. Trie les contrats restants par `expiry_date` croissante
5. Garde **jusqu'à 6** premières échéances (front, next1…next5)
6. Remplit avec `NaN` si moins de 6 contrats disponibles

**Exemple concret (février 2026) :**

```
Contrats EMA cotés : Mar-H26, Jun-M26, Aug-Q26, Nov-X26, Mar-H27, Jun-M27, Aug-Q27

Mar-H26 : 42 jours → OK
Jun-M26 : 133 jours → OK
...

Résultat courbe du jour :
  front = Mar-H26 (42j)
  next1 = Jun-M26 (133j)
  next2 = Aug-Q26 (195j)
  next3 = Nov-X26 (287j)
  next4 = Mar-H27 (377j)
  next5 = Jun-M27 (468j)
```

**Exemple : glissement de mars (fin février / début mars 2026)**

```
Mar-H26 : 12 jours → EXCLUS (<=15j)

front = Jun-M26 (126j)
next1 = Aug-Q26 (188j)
next2 = Nov-X26 (280j)
next3 = Mar-H27 (370j)
next4 = Jun-M27 (461j)
next5 = Aug-Q27 (523j)   ← seulement si ce contrat est disponible, sinon NaN
```

Le glissement (roll) se fait naturellement par le DTE, pas à une date fixée.

---

## 4. Données à collecter par contrat

Pour **chaque** contrat dans `ema_contract_daily.parquet` (table longue : 1 ligne par date × contrat) :

| Colonne | Type | Description |
|---|---|---|
| `date` | date | date de négociation |
| `contract_code` | str | ex. `EMA_H2026` |
| `expiry_date` | date | date d'expiration (jointure sur `ema_contract_reference`) |
| `days_to_expiry` | int | jours jusqu'à expiration |
| `open` | float | prix d'ouverture (EUR/t) |
| `high` | float | prix max séance |
| `low` | float | prix min séance |
| `settlement` | float | prix de règlement officiel Euronext |
| `last` | float | dernier prix traité (fallback si settlement absent) |
| `price` | float | = settlement si disponible, sinon last |
| `volume` | int | nombre de lots traités |
| `open_interest` | int | positions ouvertes (OI) |
| `bid` | float | meilleure offre d'achat (optionnel) |
| `ask` | float | meilleure offre de vente (optionnel) |
| `bid_ask_spread` | float | ask - bid (proxy liquidité intraday) |
| `quality_flag` | str | ok / settlement_missing / low_liquidity / proxy_cbot |
| `is_proxy` | bool | True si dérivé CBOT (jamais vrai Euronext) |
| `source` | str | euronext_scraper / barchart / proxy_cbot |
| `source_symbol` | str | symbole fournisseur brut |
| `canonical_contract_code` | str | code canonique projet |
| `import_verdict` | str | usable / legacy_or_ambiguous / do_not_import |
| `active_month_status` | str | current_official / historical_confirmed / legacy_or_ambiguous |

**Données dérivées dans la table courbe (`ema_curve_daily.parquet`, table large) :**

| Colonne | Calcul |
|---|---|
| `rank` | 0=front, 1=next1, …, 5=next5 |
| `dte_category` | short (≤90j) / medium (91-180j) / long (>180j) |
| `liquidity_score` | score composite volume + OI (normalisé 0-1 sur 52 semaines glissantes) |

---

## 5. Séries continues

### 5.1 Architecture : 4 séries + harvest_nov

| Fichier | Usage |
|---|---|
| `ema_front_continuous_raw` | rapport agriculteur, cibles y_price, cibles direction |
| `ema_front_continuous_adjusted` | features de rendement uniquement (returns, momentum, RSI, volatilité) |
| `ema_liquid_continuous_raw` | alternative plus représentative du contrat réellement travaillé |
| `ema_liquid_continuous_adjusted` | features de rendement version contrat liquide |
| `ema_harvest_nov` | cible agriculteur récolte EU — jamais ajusté |

**Règle d'usage raw vs adjusted :**
- `raw` = prix réel de marché. Utilisé pour : rapports, y_up_hH_ema, y_price_h60_ema, y_storage_profit_3m
- `adjusted` = prix corrigé des roll_gaps. Utilisé pour : ema_return_20d, ema_momentum, ema_rsi, ema_volatility_20d

Ne jamais utiliser `adjusted` comme cible d'un modèle ou dans un rapport.

---

### 5.2 `ema_front_continuous_raw`

**Règle de sélection :** chaque jour, prendre la **première échéance** disponible avec `days_to_expiry > 15`.

Colonnes :
```
date, selected_contract, selected_expiry, days_to_expiry,
open, high, low, settlement, last, price,
volume, open_interest,
roll_flag, roll_reason, roll_gap_eur_t,
quality_flag, is_proxy, source
```

`roll_reason` : `expiry_roll` (contrat trop proche) | `manual_override`

---

### 5.3 `ema_liquid_continuous_raw`

**Règle de sélection :** chaque jour, sélectionner le contrat avec le **plus grand open_interest** parmi les candidats éligibles.

**Candidats éligibles :**
```
- days_to_expiry > 15
- days_to_expiry < 370     ← contrainte ajoutée : éviter de sauter sur une échéance très lointaine
- is_proxy = False         ← jamais de proxy dans la série liquid
- volume > 0 OU open_interest > seuil minimal (configurable, ex. 100 lots)
```

**Règle de stabilité (évite les allers-retours) :**
```
Garder le contrat courant si :
  - il reste éligible (DTE > 15 AND DTE < 370)
  - il reste dans le top 2 des OI parmi les éligibles

Changer si :
  - le contrat courant n'est plus éligible (DTE <= 15)
  - OU il sort du top 2 OI (OI < 70% du OI du leader)
→ Changer vers le contrat éligible avec le plus grand OI
```

`roll_reason` : `expiry_roll` | `liquidity_roll` (sortie top 2 OI) | `manual_override`

---

### 5.4 `ema_harvest_nov`

**Ce que c'est :** le contrat Novembre de la campagne agricole EU en cours. Référence pour l'agriculteur qui veut savoir à quel prix vendre sa prochaine récolte.

**Règle de sélection :**
```python
# Campagne EU = août N → juillet N+1
# Le contrat récolte = EMA_X de l'année de la récolte

if date < expiry(EMA_X{année(date)}) - 15j:
    harvest_nov = EMA_X{année(date)}      # Novembre de l'année en cours
else:
    harvest_nov = EMA_X{année(date) + 1}  # Novembre de l'année suivante
```

**Deux colonnes optionnelles pour l'étude :**
- `harvest_nov_current` : contrat Novembre de la prochaine récolte (règle ci-dessus)
- `harvest_nov_next` : contrat Novembre de la récolte suivante (N+1)

**Jamais back-adjusted.** Le prix brut est toujours utilisé.

Colonnes supplémentaires :
```
campaign_year    # ex. "2026/2027" = récolte août 2026 → juillet 2027
days_to_harvest  # estimation : expiry_nov - date (approximation)
```

---

### 5.5 `ema_front_continuous_adjusted` et `ema_liquid_continuous_adjusted`

Construction : `price_adjusted = price_raw - cumsum(roll_gaps)` appliqué rétroactivement à chaque roll.

Colonnes supplémentaires :
```
price_adjusted        # prix brut corrigé des gaps de roll
cumulative_adjustment # debug : total des ajustements depuis le début
```

**Usage exclusif :** features de rendement pour modèles ML.
- ema_return_1d = price_adjusted.pct_change(1)
- ema_return_20d = price_adjusted.pct_change(20)
- ema_volatility_20d = ema_return_1d.rolling(20).std()
- ema_rsi = ...

---

## 6. Features de courbe dérivées des 6 contrats

Calculées quotidiennement à partir des prix des rangs front…next5 dans `ema_curve_daily`.

### 6.1 Spreads (structure de la courbe)

```
ema_spread_f0_f1   = next1_price - front_price          (spread immédiat)
ema_spread_f1_f2   = next2_price - next1_price
ema_spread_f0_f2   = next2_price - front_price
ema_spread_nov_mar = prix_EMA_X_rangK - prix_EMA_H_rangL (spread campagne EU, chercher les rangs X et H)
ema_curve_slope_6  = next5_price - front_price          (pente totale, NaN si next5 absent)
```

Note : `ema_spread_nov_mar` n'est pas calculé sur des codes mois fixes (EMA_X2026 - EMA_H2027), mais en identifiant parmi les 6 rangs disponibles les rangs correspondant aux mois X et H.

### 6.2 Structure de marché

```
ema_contango_flag      = 1 si next1_price > front_price + 0.5 €/t
ema_backwardation_flag = 1 si next1_price < front_price - 0.5 €/t
ema_curve_shape        = (next5_price - front_price) / front_price  (pente normalisée, NaN si next5 absent)
```

### 6.3 Carry et roll yield

```
ema_carry_30d      = (next1_price - front_price) / front_price * (30 / dte_spread_days)
ema_roll_yield_ann = ema_carry_30d * 12
```

### 6.4 Liquidité et concentration

```
ema_oi_front_pct   = oi_front / oi_total    (concentration sur le front)
ema_oi_total       = sum(oi pour tous les rangs non-NaN)
ema_volume_total   = sum(volume pour tous les rangs non-NaN)
ema_liquid_shift   = oi_next1 / oi_front    (> 1 = le marché anticipe déjà le suivant)
```

### 6.5 Cross-market CBOT-EMA

```
cbot_eur_t           = cbot_cents_bu / 100 / eurusd_rate * 39.3679
ema_cbot_basis       = ema_front_price - cbot_eur_t
ema_cbot_basis_z52w  = expanding_zscore(ema_cbot_basis, window=52w)
ema_cbot_rel_20d     = (ema / ema_sma20) - (cbot_eur_t / cbot_eur_t_sma20)
```

**Anti-leakage :** toutes ces features utilisent `shift(1)` (settlement J → feature disponible J+1).

---

## 7. Audit des rolls (obligatoire avant modèles)

Avant d'utiliser les séries continues dans les modèles, vérifier :

| Contrôle | Valeur attendue | Alerte si |
|---|---|---|
| Nombre de rolls/an | 3-4 (4 échéances/an) | < 2 ou > 6 |
| Roll_gap moyen (EUR/t) | < 5 €/t | > 10 €/t |
| Roll_gap max | < 15 €/t | > 20 €/t (possible erreur données) |
| Invariant raw - adjusted | = sum(roll_gaps) à chaque date | écart > 0.01 |
| Cibles traversant un roll | identifiées (nécessitent adjusted) | non documentées |

**Rapport de roll audit :** `artefacts/roll_audit/roll_audit_report.txt`

```
ROLL AUDIT REPORT

Front continuous RAW vs ADJUSTED
  Total rolls detected: 42
  Rolls per year (avg): 3.5
  Average roll gap: 2.3 €/t
  Max roll gap: 8.7 €/t (2022-06-08, EMA_M2022 → EMA_Q2022)
  
  ⚠ Cibles h20 traversant un roll : 127 fenêtres
  → Ces fenêtres doivent utiliser la série adjusted.

Verdict: OK / ALERTE (selon seuils ci-dessus)
```

---

## 8. Études à mener : quel contrat a le plus de signal ?

**Question ouverte :** parmi les rangs de courbe, lequel donne le meilleur signal prédictif ?

Hypothèses :
- **H1 :** front (rang 0) : incorpore l'information immédiate
- **H2 :** next2 (~6 mois) : filtre le bruit court terme
- **H3 :** harvest_nov : le plus adapté aux cibles de stockage agriculteur
- **H4 :** la structure courbe (spreads, slope) > n'importe quel contrat individuel

**Méthode :**
1. Construire `y_up_h20_rank{k}` à partir de chacun des rangs (front, next1, …, next5)
2. Run walk_forward_da (8 folds crop year) + IC95% bootstrap pour chaque rang
3. Comparer avec correction Benjamini-Hochberg
4. Documenter classement dans `artefacts/ema_contract_signal_study.json`

---

## 9. Règles anti-leakage

| Source | Disponibilité réelle |
|---|---|
| settlement J | J+1 matin (publication Euronext J soir après 18h CET) |
| open_interest J | J+1 (calculé fin de séance) |
| volume J | J+1 |
| bid/ask intraday | temps réel (non utilisé pour ML) |

Règle : `shift(1)` sur settlement, OI et volume pour toutes les features ML.  
Rapport agriculteur : prix J affiché en temps réel (pas de shift).

---

## 10. Blocage historique et stratégie de backfill

**Point critique (Correction C4) :**

L'API publique visible sur euronext.com ne donne probablement pas l'historique des contrats expirés avant 2024-2025. Pour reconstruire l'historique 2014-2024, il faut une source qui donne les anciens contrats.

**Sources par ordre de priorité (corrigé) :**

| Priorité | Source | Accès | Contrats expirés ? | Coût | Statut |
|---|---|---|---|---|---|
| 1 | **Barchart historical expired** | Web / API OnDemand | Pages/métadonnées confirmées, lignes OHLC non visibles en HTML public | API/Premier ou CSV manuel requis | **VALIDÉ PARTIEL → DATA-EMA-09** |
| 2 | Euronext Web Services officiel | API REST officielle | Oui | Commercial / licence | Propre mais plus long |
| 3 | CSV manuel unique | Téléchargement | Oui si export complet | Temps ou abonnement | Fallback fiable |
| 4 | Proxy CBOT | Calcul | Oui, mais faux prix | Gratuit | **Interdit pour résultats finaux** |

**Ce qu'on sait sur Barchart :**  
Le probe DATA-EMA-09 a testé 79 symboles : H/M/Q/X de 2010 à 2026 et F de 2010 à 2020. Toutes les pages répondent HTTP 200 et identifient Euronext Corn, mais aucune ligne historique n'est visible dans le HTML public (`n_rows_visible=0`). Barchart indique une capacité de téléchargement côté interface, mais l'accès exploitable nécessite probablement Barchart Premier/OnDemand ou un CSV manuel autorisé.  
⚠ Attention : XBF14 (Corn Jan 2014) apparaît chez Barchart, alors que Janvier n'est pas un mois officiel EMA actuel. Il faut valider proprement les mois disponibles.

**Conséquence sur DATA-EMA-02 :**  
DATA-EMA-02 reste **BLOCKED par validation source externe** tant qu'une source OHLC historique exploitable n'est pas validée. Le statut `PENDING_VALIDATION` n'est pas autorisé par les règles projet et ne doit pas être utilisé dans `TICKETS_RD.md`.  
→ **DATA-EMA-09** a confirmé les pages Barchart, mais pas l'accès public aux lignes OHLC.  
→ **DATA-EMA-10** reste bloqué tant qu'une source historique OHLC ou un CSV manuel validé n'existe pas.  
→ Prochain vrai déblocage : Barchart OnDemand/Premier/API, Euronext Web Services, LSEG/Bloomberg ou CSV manuel.

**Stratégie recommandée en 11 étapes :**
1. Automatiser la collecte quotidienne réelle dès maintenant (DATA-EMA-01) ← DONE
2. Séparer flux actif et legacy fournisseur (DATA-EMA-11) ← DONE
3. Valider Barchart pour les contrats expirés (DATA-EMA-09) ← DONE partiel : pages OK, OHLC public KO
4. Préparer le validateur CSV/API externe (DATA-EMA-12) ← DONE
5. Tester série continue fournisseur (`XB*0`, `EMA1!`, `EMA=F`) ← DONE, aucune OHLC publique
6. Tester contrats Barchart unitaires (`XBM26`, `XBQ26`, `XBX26`, `XBM14`) ← DONE, aucune OHLC publique
7. Obtenir une source OHLC exploitable ou un CSV manuel autorisé
8. Valider cette source avec DATA-EMA-12
9. Figer la référence contrats (DATA-EMA-10)
10. Si validé → importer l'historique 2010-2026 (DATA-EMA-02)
11. Reconstruire séries continues puis lancer benchmarks

---

## 11. Tests obligatoires (à implémenter dans DATA-EMA-03 et DATA-EMA-09)

```python
# Test C1 — aucun contrat Janvier généré automatiquement dans le pipeline courant
def test_no_generated_january_contracts():
    current = contracts[contracts["active_month_status"] == "current_official"]
    assert all(c.split("_")[1][0] in "HMQX" for c in current["contract_code"])

# Test C3 — seuls les mois H/M/Q/X sont valides par défaut
def test_current_valid_month_codes_only():
    valid = {"H", "M", "Q", "X"}
    current = contracts[contracts["active_month_status"] == "current_official"]
    assert set(current["month_code"]).issubset(valid)

# Test — DTE > 15 pour tout contrat sélectionné
def test_no_near_expiry_selected():
    assert (curve_daily["front_dte"] > 15).all()
    assert (continuous["days_to_expiry"] > 15).all()

# Test — NaN si moins de 6 rangs disponibles
def test_missing_ranks_are_nan():
    if n_available < 6:
        assert pd.isna(curve_daily["next5_price"]).all()

# Test — harvest_nov jamais adjusted
def test_harvest_nov_no_adjustment():
    assert "price_adjusted" not in harvest_nov.columns
    assert "cumulative_adjustment" not in harvest_nov.columns

# Test — liquid_continuous DTE < 370
def test_liquid_dte_bound():
    assert (liquid_continuous["days_to_expiry"] < 370).all()

# Test — invariant raw vs adjusted
def test_adjusted_invariant():
    assert abs(
        (front_raw["price"] - front_adjusted["price_adjusted"])
        - front_adjusted["cumulative_adjustment"]
    ).max() < 0.01

# Test — shift(1) appliqué sur les features ML
def test_ml_features_shifted():
    assert features["ema_settlement"].iloc[0] is np.nan  # NaN en ligne 0

# Test — roll_flag=True exactement aux dates de changement de contrat
def test_roll_flag_on_contract_change():
    changes = continuous["selected_contract"].ne(continuous["selected_contract"].shift(1))
    assert (changes == continuous["roll_flag"]).all()

# Test — roll_gap documenté quand roll_flag=True
def test_roll_gap_when_roll():
    rolls = continuous[continuous["roll_flag"]]
    assert (rolls["roll_gap_eur_t"].notna()).all()
```

---

## 12. Structure finale des fichiers

```
data/raw/euronext_ema_contracts/
  YYYY-MM-DD.json                   ← snapshot quotidien brut

data/processed/euronext/
  ema_contract_reference.parquet    ← TABLE DE RÉFÉRENCE (prérequis absolu)
  ema_contract_daily.parquet        ← table longue : 1 ligne par date × contrat
  ema_curve_daily.parquet           ← table large : 1 ligne par date, rangs front..next5
  ema_front_continuous_raw.parquet
  ema_front_continuous_adjusted.parquet
  ema_liquid_continuous_raw.parquet
  ema_liquid_continuous_adjusted.parquet
  ema_harvest_nov.parquet           ← jamais adjusté, jamais de proxy CBOT
  ema_curve_features.parquet        ← features dérivées (spreads, carry, basis, OI)
```

---

## 13. Ce qu'on sait vs ce qu'on ne sait pas encore

| Question | Réponse actuelle | À confirmer |
|---|---|---|
| Mois valides EMA courants | H, M, Q, X uniquement par défaut | ✅ Officiel Euronext courant |
| DTE minimum pour exclure | 15 jours | À ajuster si données montrent comportement différent |
| DTE maximum pour ema_liquid | 370 jours | À valider sur historique |
| Le front ou le liquid a plus de signal ? | **Inconnu** → étude §8 | EXP-BENCH-02 |
| back-adjust améliore les features ML ? | Attendu oui pour rendements | À vérifier par ablation |
| Mois F/Janvier historique | Source tierce possible (`XBF..`) | À confirmer via référence officielle/source |
| OI disponible dans le backfill historique ? | Incertain — dépend de la source | À confirmer lors de DATA-EMA-09/DATA-EMA-02 |
| L'API Euronext donne les contrats expirés ? | Non observé sur version publique testée | DATA-EMA-02 public partiel |
| Le spread nov-mar est prédictif ? | Hypothèse forte (campagne EU) | EXP-BENCH-03 |
| Nb de rolls par an | 3-4 (4 échéances/an) | Roll audit DATA-EMA-08 |

---

## 14. État des corrections dans TICKETS_RD.md

| Correction | Statut | Ticket |
|---|---|---|
| Ne jamais générer Jan/F dans le pipeline courant | Ticket correctif ajouté | DATA-EMA-11 |
| `parse_contract_label("Jan 2027")` → ValueError pour flux actif courant | Ticket correctif ajouté | DATA-EMA-11 |
| `VALID_EMA_MONTH_CODES = {"H","M","Q","X"}` défini pour contrats actifs | Ticket correctif ajouté | DATA-EMA-11 |
| `source_symbol` + `canonical_contract_code` + `import_verdict` dans JSON | ✅ FAIT | DATA-EMA-01 |
| Validation import : `legacy_or_ambiguous` si month_code non courant | Ticket correctif ajouté | DATA-EMA-11 / DATA-EMA-10 |
| DATA-EMA-02 = `BLOCKED` tant que DATA-EMA-09 + DATA-EMA-10 ne sont pas `DONE` | ✅ FAIT | TICKETS_RD.md index |
| DATA-EMA-09 créé (validation Barchart expired) | ✅ FAIT | TICKETS_RD.md |
| DATA-EMA-10 créé (référence contrats EMA) | ✅ FAIT | TICKETS_RD.md |
| DATA-EMA-12 créé (validation CSV OHLC externe) | ✅ FAIT | TICKETS_RD.md |
| DATA-EMA-13 créé (série continue longue) | ✅ FAIT | TICKETS_RD.md |
| DATA-EMA-14 créé (contrats Barchart unitaires) | ✅ FAIT | TICKETS_RD.md |
| Ordre exécution : DATA-EMA-11 → DATA-EMA-09 → DATA-EMA-12/13/14 → source OHLC → DATA-EMA-10 → DATA-EMA-02 | ✅ FAIT | TICKETS_RD.md Phase 0/0b |

## 15. Pré-conditions pour débloquer les benchmarks EMA

Ces 5 conditions doivent être TOUTES satisfaites avant EXP-BENCH-02 :

1. `ema_contract_reference.parquet` existe (dates d'expiration exactes)
2. `ema_contract_daily.parquet` couvre ≥ 2014-2026 (ou min 8 crop years)
3. Séries continues `ema_front_continuous_raw`, `ema_liquid_continuous_raw`, `ema_harvest_nov` construites
4. Roll audit (DATA-EMA-08) : verdict OK
5. VAL-EMA-01 : proxy vs réel comparé, exclusion proxy formalisée
