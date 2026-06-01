# Reference contrats EMA

Date : 2026-05-20  
Ticket : DATA-EMA-10

## Objectif

La table `EMA_CONTRACT_REFERENCE` fixe la correspondance entre les symboles fournisseur et les contrats canoniques du projet.

Elle evite de melanger :

- les symboles Barchart, par exemple `XBM14` ;
- les codes projet, par exemple `EMA_M2014` ;
- les mois legacy ou ambigus, notamment `XBF..`.

## Source retenue

La source candidate technique issue de DATA-EMA-15 est Barchart, racine `XB`.

La liste des contrats est exposee par la page Barchart via :

```text
list=futures.historical.byRoot(XB)
```

Le test DATA-EMA-15 a confirme :

- 120 contrats `XB` disponibles ;
- 81 contrats dans la fenetre 2010-2026 ;
- mois `F/H/M/Q/X` disponibles de 2010 a 2022 ;
- mois `H/M/Q/X` disponibles de 2023 a 2026.

## Schema canonique

Colonnes obligatoires :

| Colonne | Sens |
|---|---|
| `source` | fournisseur, actuellement `barchart` |
| `source_symbol` | symbole fournisseur brut, par exemple `XBM14` |
| `canonical_contract_code` | code projet, par exemple `EMA_M2014`, ou `None` si non importable |
| `month_code` | code mois futures (`F`, `H`, `M`, `Q`, `X`) |
| `delivery_month` | mois numerique |
| `delivery_year` | annee de livraison |
| `expiry_date` | date d'expiration si connue |
| `last_trade_date` | derniere date de cotation si connue |
| `active_month_status` | statut du mois dans l'architecture EMA |
| `import_verdict` | verdict d'import par defaut |

Colonnes complementaires :

- `contract_name` ;
- `source_root` ;
- `source_confirmed`.

## Regles de mapping

Mois officiels courants EMA :

```python
CURRENT_OFFICIAL_EMA_MONTHS = {"H": 3, "M": 6, "Q": 8, "X": 11}
```

Regle :

```text
XB{month_code}{yy} -> EMA_{month_code}{yyyy}
```

Exemples :

| Barchart | Projet | Statut | Verdict |
|---|---|---|---|
| `XBH14` | `EMA_H2014` | `historical_confirmed` | `usable` |
| `XBM14` | `EMA_M2014` | `historical_confirmed` | `usable` |
| `XBQ14` | `EMA_Q2014` | `historical_confirmed` | `usable` |
| `XBX14` | `EMA_X2014` | `historical_confirmed` | `usable` |
| `XBM26` | `EMA_M2026` | `current_official` | `usable` |

## Cas janvier / F

Barchart expose des contrats `XBF..` historiques, mais DATA-EMA-11 a separe le flux actif officiel des mois legacy fournisseur.

Regle par defaut :

| Barchart | Projet | Statut | Verdict |
|---|---|---|---|
| `XBF14` | `None` | `legacy_or_ambiguous` | `legacy_or_ambiguous` |

Une ligne `legacy_or_ambiguous` ne doit pas alimenter les series finales par defaut.

Ces contrats peuvent rester utiles pour une experience exploratoire de couverture calendaires, mais il faut une confirmation officielle ou une decision methodologique explicite avant de les integrer dans une serie finale.

## Limites restantes

- Les dates `expiry_date` / `last_trade_date` issues de Barchart doivent etre auditees contre Euronext ou une source contractuelle.
- `lastPrice` du proxy Barchart ne doit pas etre renomme `settlement` sans validation externe.
- La source Barchart proxy web est rate-limitee et non officielle ; le collecteur d'historique devra garder un throttle strict.
- Les contrats `F` ameliorent probablement la couverture 2010-2022, mais restent exclus par defaut pour eviter une contamination des resultats finaux.

## Module

Le module `src/mais/collect/ema_contract_reference.py` fournit :

- `map_provider_symbol()` ;
- `build_reference_from_barchart_rows()` ;
- `build_contract_reference()` ;
- `validate_contract_reference()` ;
- `write_contract_reference()`.

Le CLI permet de generer la table :

```bash
venv/bin/python -m mais.collect.ema_contract_reference
```

Par defaut, la sortie est :

```text
data/processed/euronext/ema_contract_reference.parquet
```

