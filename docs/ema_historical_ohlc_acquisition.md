# Acquisition Historique EMA OHLC

## Pourquoi ce document existe

Le probe Barchart public a confirmé les pages Euronext Corn expirées, mais pas l'accès aux lignes OHLC historiques. Avant de relancer `DATA-EMA-10` ou `DATA-EMA-02`, il faut donc obtenir un export CSV/API externe puis le valider.

## Sources acceptables

Une source est acceptable si elle fournit les contrats EMA historiques avec, au minimum :

- date ;
- contrat ou livraison ;
- settlement, close ou last ;
- idéalement open, high, low ;
- volume ;
- open interest si disponible ;
- symbole fournisseur brut.

Sources possibles :

- Barchart OnDemand/Premier ou export CSV autorisé ;
- Euronext Web Services ;
- LSEG / Refinitiv ;
- Bloomberg ;
- CSV manuel provenant d'une source documentée.

## Format CSV minimal

Colonnes minimales :

```text
date, contract_code, settlement
```

ou :

```text
date, delivery, settlement
```

Exemples :

```text
date,delivery,settlement,volume,open_interest,source_symbol,canonical_contract_code
2024-01-02,Nov 2024,210.5,100,1200,XBX24,EMA_X2024
```

Colonnes recommandées :

```text
date
source
source_symbol
canonical_contract_code
contract_code
delivery
contract_month
contract_year
expiry_date
open
high
low
last
settlement
volume
open_interest
import_verdict
active_month_status
```

Valeurs autorisées :

```text
import_verdict: usable | legacy_or_ambiguous | do_not_import
active_month_status: current_official | historical_confirmed | legacy_or_ambiguous
```

## Règle Janvier/F

Les mois actifs courants EMA sont H, M, Q, X.

Un contrat F/Janvier, par exemple `EMA_F2024`, est refusé par défaut. Il ne peut être accepté que si :

- `active_month_status = historical_confirmed` ;
- `import_verdict = usable` ;
- la source officielle ou fournisseur documente clairement que ce contrat était réellement coté.

## Validation avant import

Commande :

```bash
venv/bin/python -m mais.collect.ema_manual_backfill_validator path/to/ema_historical_contracts.csv --from-year 2014 --to-year 2025
```

La commande :

- affiche un rapport JSON ;
- retourne `0` si le fichier est importable ;
- retourne `1` si le fichier doit être corrigé.

Critères bloquants :

- colonne `date` absente ;
- aucune colonne prix (`settlement`, `settle`, `close`, `last`) ;
- contrat illisible ;
- prix non numérique ;
- historique qui ne couvre pas la période demandée ;
- année entièrement absente ;
- ligne legacy/F non confirmée.

Warnings non bloquants :

- `source_symbol` absent ;
- `canonical_contract_code` absent ;
- contrat novembre manquant pour une année.

## Étape suivante

Quand le CSV passe ce validateur :

1. créer ou compléter `EMA_CONTRACT_REFERENCE` dans `DATA-EMA-10` ;
2. importer le CSV via `DATA-EMA-02` ;
3. construire les séries continues dans `DATA-EMA-03`.
